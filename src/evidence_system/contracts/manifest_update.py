"""Update experiment manifests with locked contract metadata."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, MutableMapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evidence_system.contracts.common import (
    ContractLifecycleError,
    case_unit_lock_complete,
    contract_lock_entry,
    display_path,
    iter_json_files,
    iter_manifest_case_units,
    load_mapping,
    normalize_domain_or_none,
    stamp_contract_hash,
    write_json,
)
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml, validate_object


@dataclass(frozen=True)
class ManifestUpdateResult:
    manifest_path: str
    manifest_hash: str
    contract_locks_hash: str
    locked_contract_count: int
    synced_contract_paths: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_path": self.manifest_path,
            "manifest_hash": self.manifest_hash,
            "contract_locks_hash": self.contract_locks_hash,
            "locked_contract_count": self.locked_contract_count,
            "synced_contract_paths": list(self.synced_contract_paths),
        }


def update_manifest_contract_locks(
    *,
    manifest_path: str | Path,
    locked_contracts: Iterable[str | Path],
    output_path: str | Path | None = None,
    sync_contract_manifest_hash: bool = True,
) -> ManifestUpdateResult:
    manifest = load_json_or_yaml(manifest_path)
    if not isinstance(manifest, dict):
        raise ContractLifecycleError("manifest must be a mapping")
    contracts = _load_locked_contracts(locked_contracts)
    entries = sorted(
        [contract_lock_entry(contract) for _, contract in contracts],
        key=lambda item: (item["contract_id"], item["contract_version"]),
    )
    updated = dict(manifest)
    updated["contract_locks"] = entries
    updated["contract_locks_hash"] = sha256_object(entries)
    _update_case_unit_contract_refs(updated, contracts)
    _update_domain_lock_status(updated, contracts)

    destination = resolve_repo_path(output_path or manifest_path)
    _write_manifest(destination, updated)
    manifest_hash = sha256_file(destination)
    synced_paths: list[str] = []
    if sync_contract_manifest_hash:
        for contract_path, contract in contracts:
            synced = dict(contract)
            synced["manifest_hash"] = manifest_hash
            stamp_contract_hash(synced)
            # contract_hash intentionally remains stable because manifest_hash
            # is not part of the canonical contract hash payload.
            write_json(contract_path, synced)
            synced_paths.append(display_path(contract_path))
    return ManifestUpdateResult(
        manifest_path=display_path(destination),
        manifest_hash=manifest_hash,
        contract_locks_hash=updated["contract_locks_hash"],
        locked_contract_count=len(entries),
        synced_contract_paths=tuple(synced_paths),
    )


def _load_locked_contracts(paths: Iterable[str | Path]) -> list[tuple[Path, dict[str, Any]]]:
    contracts: list[tuple[Path, dict[str, Any]]] = []
    for path in iter_json_files(paths):
        contract = load_mapping(path)
        if contract.get("schema_version") != "evidence_contract/v1":
            continue
        if contract.get("contract_status") != "locked":
            raise ContractLifecycleError(f"{path} is not a locked evidence contract")
        if contract.get("main_result_eligible") is not True:
            raise ContractLifecycleError(f"{path} is not eligible for main manifest lock update")
        contracts.append((path, contract))
    if not contracts:
        raise ContractLifecycleError("no locked evidence_contract/v1 files were found")
    return contracts


def _update_domain_lock_status(manifest: MutableMapping[str, Any], contracts: list[tuple[Path, Mapping[str, Any]]]) -> None:
    locked_by_domain: dict[str, set[str]] = {}
    for _, contract in contracts:
        domain = str(contract.get("domain"))
        locked_by_domain.setdefault(domain, set()).add(str(contract.get("case_unit_id")))
    expected_from_cases: dict[str, set[str]] = {}
    for ref in iter_manifest_case_units(manifest):
        if ref.domain is not None:
            expected_from_cases.setdefault(ref.domain, set()).add(str(ref.case_unit.get("case_unit_id")))
    domains = manifest.get("domains")
    if not isinstance(domains, list):
        domains = []
    for domain in domains:
        if not isinstance(domain, MutableMapping):
            continue
        domain_id = normalize_domain_or_none(domain.get("domain"))
        if domain_id is None or domain.get("contract_lock_status") == "not_applicable":
            continue
        expected = expected_from_cases.get(domain_id)
        locked = locked_by_domain.get(domain_id, set())
        complete = False
        if expected:
            complete = expected.issubset(locked)
        else:
            expected_count = int(domain.get("case_unit_count") or 0)
            complete = expected_count > 0 and len(locked) >= expected_count
        domain["contract_lock_status"] = "locked" if complete else "locked_required_before_scoring"

    experiments = manifest.get("experiments")
    if not isinstance(experiments, list):
        return
    for experiment in experiments:
        if not isinstance(experiment, MutableMapping):
            continue
        domain_id = normalize_domain_or_none(experiment.get("domain"))
        if domain_id is None or experiment.get("contract_lock_status") == "not_applicable":
            continue
        case_units = experiment.get("case_units")
        if isinstance(case_units, list) and case_units:
            complete = all(isinstance(case, Mapping) and case_unit_lock_complete(case) for case in case_units)
        else:
            expected_count = int(experiment.get("case_unit_count") or 0)
            complete = expected_count > 0 and len(locked_by_domain.get(domain_id, set())) >= expected_count
        if "contract_lock_status" in experiment:
            experiment["contract_lock_status"] = "locked" if complete else "locked_required_before_scoring"


def _update_case_unit_contract_refs(manifest: MutableMapping[str, Any], contracts: list[tuple[Path, Mapping[str, Any]]]) -> None:
    by_domain_case = {
        (str(contract["domain"]), str(contract["case_unit_id"])): contract
        for _, contract in contracts
    }
    by_case = {str(contract["case_unit_id"]): contract for _, contract in contracts}
    for ref in iter_manifest_case_units(manifest):
        case_unit = ref.case_unit
        contract = None
        if ref.domain is not None:
            contract = by_domain_case.get((ref.domain, str(case_unit.get("case_unit_id"))))
        if contract is None:
            contract = by_case.get(str(case_unit.get("case_unit_id")))
        if contract is None:
            continue
        case_unit["evidence_contract_id"] = contract["contract_id"]
        case_unit["evidence_contract_version"] = contract["contract_version"]
        case_unit["evidence_contract_hash"] = contract["contract_hash"]
        case_unit["contract_lock_status"] = "locked"
        case_unit["contract_lock_time"] = contract["locked_at"]
        case_unit["taxonomy_version"] = contract["taxonomy_version"]


def _write_manifest(path: Path, manifest: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore[import-not-found]
        except ModuleNotFoundError as exc:
            raise ContractLifecycleError("PyYAML is required to write YAML manifests") from exc
        path.write_text(yaml.safe_dump(dict(manifest), sort_keys=False, allow_unicode=True), encoding="utf-8")
        return
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
