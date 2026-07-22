"""Build the reviewed 485-case AppWorld stronger-gap registry."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from evidence_system.contracts.appworld_checklist_semantics import (
    APPWORLD_ALL_TESTS_MARKER,
    APPWORLD_UNDECIDED_RATIONALE,
    APPWORLD_UNDECIDED_TEXT,
    appworld_benchmark_success_text,
    appworld_registered_test_fail_text,
    appworld_registered_test_marker,
    appworld_registered_test_success_text,
    appworld_required_native_surface,
    derive_appworld_evaluator_semantics,
)
from evidence_system.contracts.appworld_stronger_gaps import (
    APPWORLD_DATA_VERSION,
    APPWORLD_GIT_COMMIT,
    EXPECTED_CASE_COUNT,
    REGISTRY_PATH,
    REGISTRY_SCHEMA,
    appworld_gap_basis,
    appworld_stronger_gap_marker,
    validate_condition_without_marker,
    validate_review_basis,
    validate_review_receipt_inputs,
    validate_registry_case_entry,
)
from evidence_system.contracts.appworld_support_pointers import (
    canonical_archive_path,
    official_pointer_resolves,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import repo_root, resolve_repo_path


DEFAULT_MANIFEST = Path(
    "experiments/appworld_full_test_extension_v1/experiment_manifest.json"
)
DEFAULT_CATALOG = Path(
    "experiments/appworld_full_test_extension_v1/official_splits/"
    "appworld_selected_task_sources.json"
)
DEFAULT_POLICY = Path(
    "experiments/appworld_full_test_extension_v1/official_splits/"
    "appworld_stronger_gap_review_policy.gpt56.v1.json"
)
POLICY_SCHEMA = "appworld_stronger_gap_review_policy.v1"


def _load(path: Path, label: str) -> Mapping[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise ContractLifecycleError(f"{label} is missing or symlinked: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractLifecycleError(f"{label} is malformed: {path}") from exc
    if not isinstance(value, Mapping):
        raise ContractLifecycleError(f"{label} must be a mapping")
    return value


def _manifest_cases(manifest: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    domains = manifest.get("domains")
    if not isinstance(domains, list) or len(domains) != 1:
        raise ContractLifecycleError("extension manifest must contain one domain")
    block = domains[0]
    if not isinstance(block, Mapping) or block.get("domain") != "appworld":
        raise ContractLifecycleError("extension manifest domain must be appworld")
    cases = block.get("case_units")
    if not isinstance(cases, list) or len(cases) != EXPECTED_CASE_COUNT:
        raise ContractLifecycleError("extension manifest must contain exactly 485 cases")
    if not all(isinstance(item, Mapping) for item in cases):
        raise ContractLifecycleError("extension manifest contains a non-mapping case")
    expected_case_fields = {
        "case_unit_id",
        "contract_lock_status",
        "dataset_name",
        "source_ref",
        "split",
        "task_id",
    }
    if any(
        set(item) != expected_case_fields
        or item.get("contract_lock_status") != "draft_required"
        for item in cases
    ):
        raise ContractLifecycleError("extension manifest case schema/lock status drifted")
    case_ids = [str(item.get("case_unit_id") or "") for item in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ContractLifecycleError("extension manifest contains duplicate case IDs")
    return list(cases)


def _source_inventory(item: Mapping[str, Any]) -> dict[str, str]:
    files = item.get("files")
    if not isinstance(files, Mapping) or not files:
        raise ContractLifecycleError(f"{item.get('task_id')}: catalog files are missing")
    result: dict[str, str] = {}
    for raw in files.values():
        if not isinstance(raw, Mapping):
            raise ContractLifecycleError("catalog file descriptor must be a mapping")
        archive = str(raw.get("archive_path") or "")
        digest = str(raw.get("sha256") or "").removeprefix("sha256:")
        if (
            canonical_archive_path(archive) != archive
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        ):
            raise ContractLifecycleError("catalog file descriptor identity/hash is invalid")
        if archive in result:
            raise ContractLifecycleError("catalog contains duplicate archive paths")
        result[archive] = digest
    required = {
        "official/specs.json",
        "official/ground_truth/evaluation.py",
        "official/ground_truth/test_data.json",
    }
    if len(result) != 19 or not required <= set(result):
        raise ContractLifecycleError(
            "catalog source inventory is not the canonical 19-file AppWorld set"
        )
    return dict(sorted(result.items()))


def _evaluator_registries(item: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    task_dir = resolve_repo_path(str(item.get("task_dir") or ""))
    test_data_path = task_dir / "ground_truth/test_data.json"
    evaluation_path = task_dir / "ground_truth/evaluation.py"
    if not test_data_path.is_file() or test_data_path.is_symlink():
        raise ContractLifecycleError(f"{item.get('task_id')}: test_data is missing or symlinked")
    test_data = json.loads(test_data_path.read_text(encoding="utf-8"))
    if not isinstance(test_data, list) or not test_data:
        raise ContractLifecycleError(f"{item.get('task_id')}: test_data must be non-empty")
    records: list[dict[str, Any]] = []
    for index, raw in enumerate(test_data, start=1):
        if (
            not isinstance(raw, Mapping)
            or not isinstance(raw.get("requirement"), str)
            or not raw["requirement"].strip()
            or not isinstance(raw.get("label"), str)
            or not raw["label"].strip()
        ):
            raise ContractLifecycleError(f"{item.get('task_id')}: invalid test_data record")
        requirement = str(raw["requirement"])
        normalized = " ".join(requirement.split())
        marker = appworld_registered_test_marker(index, requirement)
        records.append(
            {
                "index": index,
                "marker": marker,
                "requirement": requirement,
                "requirement_sha256": hashlib.sha256(
                    normalized.encode("utf-8")
                ).hexdigest(),
                "required_success_if_text": appworld_registered_test_success_text(
                    marker, requirement
                ),
                "required_fail_if_text": appworld_registered_test_fail_text(
                    marker, requirement
                ),
            }
        )
    registered = {
        "all_tests_marker": APPWORLD_ALL_TESTS_MARKER,
        "required_benchmark_success_text": appworld_benchmark_success_text(
            [record["marker"] for record in records]
        ),
        "required_undecided_if_text": APPWORLD_UNDECIDED_TEXT,
        "required_undecided_if_rationale": APPWORLD_UNDECIDED_RATIONALE,
        "registered_tests": records,
    }
    specs_path = task_dir / "specs.json"
    if not specs_path.is_file() or specs_path.is_symlink():
        raise ContractLifecycleError(f"{item.get('task_id')}: specs.json is missing or symlinked")
    try:
        specs = json.loads(specs_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractLifecycleError(f"{item.get('task_id')}: specs.json is malformed") from exc
    if not isinstance(specs, Mapping) or not isinstance(specs.get("instruction"), str):
        raise ContractLifecycleError(f"{item.get('task_id')}: specs instruction is invalid")
    registered["required_native"] = appworld_required_native_surface(
        instruction=specs["instruction"],
        registered_tests=records,
    )
    if not evaluation_path.is_file() or evaluation_path.is_symlink():
        raise ContractLifecycleError(f"{item.get('task_id')}: evaluation.py is missing or symlinked")
    semantics = derive_appworld_evaluator_semantics(
        evaluation_path.read_text(encoding="utf-8"), test_data
    )
    if semantics["registered_test_registry"] != records:
        raise ContractLifecycleError(
            f"{item.get('task_id')}: registered-test derivation drift"
        )
    non_scoring = semantics["non_scoring_test_assignments"]
    if not isinstance(non_scoring, list):
        raise ContractLifecycleError(
            f"{item.get('task_id')}: non-scoring assignment registry is invalid"
        )
    return registered, non_scoring


def _condition(
    case_id: str,
    task_dir: Path,
    inventory_paths: set[str],
    registered_test_registry_sha256: str,
    non_scoring_assignment_registry_sha256: str,
    raw: Any,
    index: int,
) -> dict[str, Any]:
    if not isinstance(raw, Mapping) or set(raw) != {
        "id",
        "text",
        "rationale",
        "decisive_artifacts",
        "support",
    }:
        raise ContractLifecycleError(f"{case_id}: policy condition has invalid fields")
    condition_without_marker = validate_condition_without_marker(
        json.loads(json.dumps(raw)), index=index
    )
    support = condition_without_marker["support"]
    if not isinstance(support, list) or len(support) != len(set(support)):
        raise ContractLifecycleError(f"{case_id}: condition support contains duplicates")
    pointers = list(support)
    for artifact in condition_without_marker["decisive_artifacts"]:
        if not isinstance(artifact, Mapping):
            raise ContractLifecycleError(f"{case_id}: policy artifact must be a mapping")
        artifact_support = artifact.get("support")
        if not isinstance(artifact_support, list) or len(artifact_support) != len(
            set(artifact_support)
        ):
            raise ContractLifecycleError(
                f"{case_id}: artifact support contains duplicates"
            )
        pointers.extend(artifact_support)
    if not all(
        isinstance(pointer, str)
        and official_pointer_resolves(
            task_dir=task_dir,
            pointer=pointer,
            inventory_paths=inventory_paths,
        )
        for pointer in pointers
    ):
        raise ContractLifecycleError(f"{case_id}: policy condition contains an invalid support pointer")
    required_support = {
        "official/specs.json::$.instruction",
        "official/ground_truth/evaluation.py::evaluate",
    }
    if not required_support <= set(condition_without_marker["support"]):
        raise ContractLifecycleError(f"{case_id}: condition lacks task/evaluator support")
    marker = appworld_stronger_gap_marker(index, condition_without_marker)
    condition = dict(condition_without_marker)
    condition["text"] = f"{marker} {condition_without_marker['text']}"
    return {
        "index": index,
        "marker": marker,
        "condition_sha256": sha256_object(condition_without_marker),
        "required_condition": condition,
        "gap_basis": appworld_gap_basis(
            condition_without_marker,
            registered_test_registry_sha256=registered_test_registry_sha256,
            non_scoring_assignment_registry_sha256=(
                non_scoring_assignment_registry_sha256
            ),
        ),
    }


def build_registry(
    *, manifest_path: Path, catalog_path: Path, policy_path: Path
) -> dict[str, Any]:
    manifest = _load(manifest_path, "extension manifest")
    catalog = _load(catalog_path, "extension source catalog")
    policy = _load(policy_path, "stronger-gap review policy")
    if set(policy) != {
        "schema_version",
        "review_basis",
        "reviewed_no_gap_case_ids",
        "groups",
    } or policy.get("schema_version") != POLICY_SCHEMA:
        raise ContractLifecycleError("stronger-gap review policy schema mismatch")
    validate_review_basis(policy.get("review_basis"))
    validate_review_receipt_inputs(
        manifest_path=manifest_path,
        catalog_path=catalog_path,
        policy=policy,
    )
    cases = _manifest_cases(manifest)
    items = catalog.get("items")
    if not isinstance(items, list) or len(items) != EXPECTED_CASE_COUNT:
        raise ContractLifecycleError("source catalog must contain exactly 485 items")
    if not all(isinstance(item, Mapping) for item in items):
        raise ContractLifecycleError("source catalog contains a non-mapping item")
    catalog_ids = [str(item.get("case_unit_id") or "") for item in items]
    if len(catalog_ids) != len(set(catalog_ids)):
        raise ContractLifecycleError("source catalog contains duplicate case IDs")
    manifest_ids = [str(case["case_unit_id"]) for case in cases]
    if catalog_ids != manifest_ids:
        raise ContractLifecycleError(
            "source catalog case IDs/order differ from the extension manifest"
        )
    catalog_by_id = {str(item["case_unit_id"]): item for item in items}
    groups = policy.get("groups")
    if not isinstance(groups, list):
        raise ContractLifecycleError("review policy groups must be an array")
    conditions_by_case: dict[str, list[Any]] = {}
    for group in groups:
        if not isinstance(group, Mapping) or set(group) != {"case_ids", "conditions"}:
            raise ContractLifecycleError("review policy group has invalid fields")
        group_cases = group.get("case_ids")
        group_conditions = group.get("conditions")
        if not isinstance(group_cases, list) or not group_cases or not isinstance(group_conditions, list) or not group_conditions:
            raise ContractLifecycleError("review policy group must contain cases and conditions")
        for case_id in group_cases:
            if case_id in conditions_by_case:
                raise ContractLifecycleError(f"{case_id}: appears in more than one policy group")
            conditions_by_case[str(case_id)] = group_conditions
    if not set(conditions_by_case) <= set(manifest_ids):
        raise ContractLifecycleError("review policy contains an off-scope case")
    explicit_no_gap = policy.get("reviewed_no_gap_case_ids")
    if not isinstance(explicit_no_gap, list) or len(explicit_no_gap) != len(
        set(explicit_no_gap)
    ):
        raise ContractLifecycleError(
            "review policy must contain an explicit unique no-gap case list"
        )
    expected_no_gap = [case_id for case_id in manifest_ids if case_id not in conditions_by_case]
    if explicit_no_gap != expected_no_gap:
        raise ContractLifecycleError(
            "explicit no-gap case list must exactly equal the ordered manifest complement"
        )

    records: list[dict[str, Any]] = []
    for case in cases:
        case_id = str(case["case_unit_id"])
        item = catalog_by_id.get(case_id)
        if not isinstance(item, Mapping):
            raise ContractLifecycleError(f"{case_id}: missing source catalog item")
        split = str(case.get("dataset_name") or "")
        source_ref = str(case.get("source_ref") or "")
        if (
            str(case.get("task_id") or "") != case_id
            or case.get("split") != split
            or split not in {"test_normal", "test_challenge"}
            or source_ref != f"appworld://{split}/{case_id}"
        ):
            raise ContractLifecycleError(f"{case_id}: manifest source identity is invalid")
        if (
            item.get("case_unit_id") != case_id
            or item.get("task_id") != case_id
            or item.get("dataset_name") != split
            or item.get("split") != split
            or item.get("source_ref") != source_ref
        ):
            raise ContractLifecycleError(f"{case_id}: manifest/catalog source identity mismatch")
        task_dir = resolve_repo_path(str(item.get("task_dir") or ""))
        if not task_dir.is_dir() or task_dir.is_symlink():
            raise ContractLifecycleError(f"{case_id}: task directory is missing or symlinked")
        task_root = task_dir.resolve()
        inventory = _source_inventory(item)
        for archive, digest in inventory.items():
            relative = Path(archive.removeprefix("official/"))
            cursor = task_root
            symlinked = False
            for part in relative.parts:
                cursor = cursor / part
                if cursor.is_symlink():
                    symlinked = True
                    break
            source = (task_root / relative).resolve()
            try:
                source.relative_to(task_root)
            except ValueError as exc:
                raise ContractLifecycleError(
                    f"{case_id}: source path escapes task root: {archive}"
                ) from exc
            if symlinked or not source.is_file() or sha256_file(source) != digest:
                raise ContractLifecycleError(f"{case_id}: source catalog bytes drifted: {archive}")
        registered, non_scoring = _evaluator_registries(item)
        registered_sha256 = sha256_object(registered)
        non_scoring_sha256 = sha256_object(non_scoring)
        condition_ids = [
            str(raw.get("id") or "")
            for raw in conditions_by_case.get(case_id, [])
            if isinstance(raw, Mapping)
        ]
        if len(condition_ids) != len(set(condition_ids)):
            raise ContractLifecycleError(
                f"{case_id}: duplicate stronger-gap condition IDs"
            )
        gaps = [
            _condition(
                case_id,
                task_dir,
                set(inventory),
                registered_sha256,
                non_scoring_sha256,
                raw,
                index,
            )
            for index, raw in enumerate(conditions_by_case.get(case_id, []), start=1)
        ]
        record: dict[str, Any] = {
            "case_unit_id": case_id,
            "split": split,
            "source_ref": source_ref,
            "source_basis_sha256": sha256_object(inventory),
            "registered_test_registry_sha256": registered_sha256,
            "non_scoring_assignment_registry": non_scoring,
            "non_scoring_assignment_registry_sha256": non_scoring_sha256,
            "non_scoring_assignment_exclusion_status": (
                "excluded_from_native_and_stronger_scoring"
            ),
            "review_status": "reviewed_gap" if gaps else "reviewed_no_gap",
            "gaps": gaps,
        }
        record["entry_semantic_sha256"] = sha256_object(record)
        records.append(record)
    registry: dict[str, Any] = {
        "schema_version": REGISTRY_SCHEMA,
        "appworld_commit": APPWORLD_GIT_COMMIT,
        "data_version": APPWORLD_DATA_VERSION,
        "case_count": EXPECTED_CASE_COUNT,
        "case_ids_semantic_sha256": sha256_object(manifest_ids),
        "review_policy": {
            "path": policy_path.resolve().relative_to(repo_root().resolve()).as_posix(),
            "sha256": sha256_file(policy_path),
            "schema_version": POLICY_SCHEMA,
            "review_basis": policy.get("review_basis"),
            "reviewed_gap_case_count": len(conditions_by_case),
            "reviewed_no_gap_case_count": EXPECTED_CASE_COUNT - len(conditions_by_case),
            "reviewed_no_gap_case_ids_sha256": sha256_object(explicit_no_gap),
            "required_condition_count": sum(len(record["gaps"]) for record in records),
        },
        "cases": records,
    }
    registry["registry_semantic_sha256"] = sha256_object(registry)
    validated_records = [validate_registry_case_entry(record) for record in records]
    if validated_records != records:
        raise ContractLifecycleError("generated stronger-gap registry entry validation drift")
    if [record["case_unit_id"] for record in validated_records] != manifest_ids:
        raise ContractLifecycleError("generated stronger-gap registry case order drift")
    return registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--output", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        output = resolve_repo_path(args.output)
        if output.exists():
            raise ContractLifecycleError(f"registry output already exists: {output}")
        registry = build_registry(
            manifest_path=resolve_repo_path(args.manifest),
            catalog_path=resolve_repo_path(args.catalog),
            policy_path=resolve_repo_path(args.policy),
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as handle:
            json.dump(registry, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
    except (ContractLifecycleError, OSError, ValueError) as exc:
        payload = {"status": "blocked", "reason": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        return 2
    payload = {
        "status": "ok",
        "path": str(args.output),
        "sha256": sha256_file(output),
        "case_count": registry["case_count"],
        "gap_case_count": registry["review_policy"]["reviewed_gap_case_count"],
        "condition_count": registry["review_policy"]["required_condition_count"],
    }
    print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
