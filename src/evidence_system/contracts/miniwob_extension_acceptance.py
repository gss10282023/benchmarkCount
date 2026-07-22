"""Fail-closed acceptance gates for the MiniWoB++ remaining-22 extension.

The validator is intentionally read-only.  It verifies the three deterministic
selection windows, the generated manifest/source bundle, and every byte copied
into the 22 case packets.  A receipt may be written by the CLI only after all
gates have passed.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

from evidence_system.contracts.case_packets import (
    MINIWOB_COMPACT_DERIVED_FILES,
    MINIWOB_DRAFTING_CONTEXT_SCHEMA,
    MINIWOB_POST_RUN_ARTIFACT_TYPES,
    MINIWOB_RUNTIME_WIRING_SCHEMA,
    MINIWOB_SOURCE_EXCERPTS_SCHEMA,
    MINIWOB_STRONGER_CONDITION_SPECS_V1,
)
from evidence_system.contracts.common import ContractLifecycleError, write_json
from evidence_system.core.hashing import sha256_file, sha256_object, sha256_path
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml


EXPECTED_CATALOG_COUNT = 125
EXPECTED_ELIGIBLE_COUNT = 122
EXPECTED_REMAINING_COUNT = 22
EXPECTED_RECORD_SLOT_COUNT = 66
EXPECTED_AGENTS = ("Agent A", "Agent B", "Agent C")
EXPECTED_RESULT_NAMESPACE = "miniwob_remaining22_bg0143_v1"
EXPECTED_SMOKE_CASES = (
    "miniwob.click-button",
    "miniwob.click-test",
    "miniwob.enter-text",
)
EXPECTED_SELECTION_SALT_HASH = "04d7178a6462c2a8156a264183713d7e7a13456ac60c9ab7abc13c46ceac9585"
EXPECTED_ELIGIBLE_SET_HASH = "850e2ecab0bef8f17677513f3f239328b8389c8663d4f7d1065247a639da493e"
EXPECTED_SELECTION_ORDER_HASH = "36c5bdeb86fafe82bfbf4bc8c6d8978ef9a46107183d8bda6b4d6ae4ebd64195"
EXPECTED_SMOKE_EXCLUSION_HASH = "fc56679d48440e0cbe74bf6ff33e66d66ba0097c601c25d58478ede9148aac32"

DEFAULT_FIRST50_SELECTED = Path("experiments/official_splits/miniwob_selected_task_sources.json")
DEFAULT_SECOND50_SELECTED = Path("experiments/official_splits/miniwob_second50/miniwob_selected_task_sources.json")
DEFAULT_REMAINING22_SELECTED = Path("experiments/official_splits/miniwob_remaining22/miniwob_selected_task_sources.json")
DEFAULT_REMAINING_CATALOG = Path("experiments/official_splits/miniwob_remaining22/miniwob_official_task_catalog_122.json")
DEFAULT_MANIFEST = Path("experiments/appendix/miniwob_remaining22_manifest.yaml")
DEFAULT_SOURCE_BUNDLE = Path(
    "experiments/evidence_contracts/source_bundles/miniwob_remaining22_case_units_source_bundle.json"
)
DEFAULT_CASE_PACKETS_ROOT = Path("experiments/case_packets_extensions/miniwob_remaining22")
DEFAULT_EXECUTION_INFRA = Path("configs/miniwob_browsergym_0_14_3_execution.locked.yaml")
DEFAULT_AGENTS_CONFIG = Path("configs/miniwob_browsergym_0_14_3_agents.locked.yaml")

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_FORBIDDEN_PUBLIC_MARKERS = ("/Users/", "tmp/miniwob-browsergym", "materialization_path")
_FORBIDDEN_PACKET_OUTCOME_MARKERS = (
    "Agent A",
    "Agent B",
    "Agent C",
    '"native_score":',
    '"outcome_label":',
    '"evidence_label":',
    '"response_id":',
    '"api_response":',
)
MAX_COMPACT_PACKET_BYTES = 120_000


def validate_miniwob_extension(
    *,
    first50_selected_path: str | Path = DEFAULT_FIRST50_SELECTED,
    second50_selected_path: str | Path = DEFAULT_SECOND50_SELECTED,
    remaining22_selected_path: str | Path = DEFAULT_REMAINING22_SELECTED,
    remaining_catalog_path: str | Path = DEFAULT_REMAINING_CATALOG,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    source_bundle_path: str | Path = DEFAULT_SOURCE_BUNDLE,
    case_packets_root: str | Path = DEFAULT_CASE_PACKETS_ROOT,
    execution_infra_path: str | Path = DEFAULT_EXECUTION_INFRA,
    agents_config_path: str | Path = DEFAULT_AGENTS_CONFIG,
    expected_result_namespace: str = EXPECTED_RESULT_NAMESPACE,
) -> dict[str, Any]:
    """Validate the complete remaining-22 definition and return a receipt.

    No input is modified.  The first failed invariant raises
    :class:`ContractLifecycleError` so callers cannot accidentally treat a
    partial audit as acceptance.
    """

    paths = {
        "first50_selected": _input_file(first50_selected_path, "first50 selected source"),
        "second50_selected": _input_file(second50_selected_path, "second50 selected source"),
        "remaining22_selected": _input_file(remaining22_selected_path, "remaining22 selected source"),
        "remaining_catalog": _input_file(remaining_catalog_path, "remaining22 catalog"),
        "manifest": _input_file(manifest_path, "remaining22 manifest"),
        "source_bundle": _input_file(source_bundle_path, "remaining22 source bundle"),
        "execution_infra": _input_file(execution_infra_path, "execution infra"),
        "agents_config": _input_file(agents_config_path, "agents config"),
    }
    unresolved_packet_root = resolve_repo_path(case_packets_root)
    _require(unresolved_packet_root.is_dir(), "case_packets_root", f"directory is missing: {unresolved_packet_root}")
    _require(not unresolved_packet_root.is_symlink(), "case_packets_root", "symlink roots are not accepted")
    packet_root = unresolved_packet_root.resolve()

    catalog = _load_mapping(paths["remaining_catalog"], "remaining22 catalog")
    canonical_catalog = _validate_catalog(catalog, label="remaining22 catalog")

    cohort_specs = (
        ("first50", paths["first50_selected"], range(0, 50)),
        ("second50", paths["second50_selected"], range(50, 100)),
        ("remaining22", paths["remaining22_selected"], range(100, 122)),
    )
    cohorts: dict[str, dict[str, Any]] = {}
    selected_payloads: dict[str, dict[str, Any]] = {}
    public_files: set[Path] = {paths[key] for key in paths if key not in {"execution_infra", "agents_config"}}
    selected_id_sets: list[set[str]] = []
    for name, selected_path, expected_ranks in cohort_specs:
        selected = _load_mapping(selected_path, f"{name} selected source")
        selected_payloads[name] = selected
        audit, referenced_catalog_path = _validate_cohort(
            name=name,
            selected=selected,
            expected_ranks=list(expected_ranks),
            canonical_catalog=canonical_catalog,
        )
        referenced_catalog = _load_mapping(referenced_catalog_path, f"{name} referenced catalog")
        referenced = _validate_catalog(referenced_catalog, label=f"{name} referenced catalog")
        _require(
            referenced["identity_records"] == canonical_catalog["identity_records"],
            f"{name}.candidate_catalog",
            "catalog identity/order differs from the remaining22 catalog",
        )
        if name == "remaining22":
            _require(
                referenced_catalog_path == paths["remaining_catalog"],
                "remaining22.candidate_pool_path",
                "must resolve to the supplied remaining22 catalog",
            )
        public_files.add(referenced_catalog_path)
        selected_id_sets.append(set(audit.pop("case_unit_ids")))
        cohorts[name] = {
            **audit,
            "path": _display_path(selected_path),
            "sha256": sha256_file(selected_path),
            "candidate_catalog_path": _display_path(referenced_catalog_path),
            "candidate_catalog_sha256": sha256_file(referenced_catalog_path),
        }

    _require(
        all(selected_id_sets[left].isdisjoint(selected_id_sets[right]) for left in range(3) for right in range(left + 1, 3)),
        "cohort_disjointness",
        "first50, second50, and remaining22 overlap",
    )
    union_ids = set().union(*selected_id_sets)
    _require(
        union_ids == set(canonical_catalog["case_unit_ids"]),
        "cohort_union",
        f"three windows must equal the complete 122-case eligible catalog; observed={len(union_ids)}",
    )

    infra = _load_mapping(paths["execution_infra"], "execution infra")
    agents_config = _load_mapping(paths["agents_config"], "agents config")
    _validate_execution_inputs(infra=infra, agents_config=agents_config)
    manifest = _load_mapping(paths["manifest"], "remaining22 manifest")
    bundle = _load_mapping(paths["source_bundle"], "remaining22 source bundle")
    remaining_items = _mapping_items(selected_payloads["remaining22"], "remaining22 selected source")

    manifest_audit = _validate_manifest(
        manifest=manifest,
        manifest_path=paths["manifest"],
        catalog_path=paths["remaining_catalog"],
        bundle_path=paths["source_bundle"],
        infra_path=paths["execution_infra"],
        agents_path=paths["agents_config"],
        agents_config=agents_config,
        remaining_items=remaining_items,
        expected_result_namespace=expected_result_namespace,
    )
    packet_audit = _validate_bundle_and_packets(
        bundle=bundle,
        bundle_path=paths["source_bundle"],
        manifest=manifest,
        manifest_path=paths["manifest"],
        packet_root=packet_root,
        remaining_items=remaining_items,
    )
    public_files.update(packet_audit.pop("public_files"))
    privacy_audit = _scan_public_artifacts(public_files)

    artifact_receipt = {
        key: {"path": _display_path(path), "sha256": sha256_file(path)}
        for key, path in paths.items()
    }
    return {
        "schema_version": "miniwob_extension_acceptance_receipt/v1",
        "status": "ok",
        "all_hard_gates_passed": True,
        "artifacts": artifact_receipt,
        "catalog": {
            "catalog_count": EXPECTED_CATALOG_COUNT,
            "eligible_count": EXPECTED_ELIGIBLE_COUNT,
            "smoke_count": len(EXPECTED_SMOKE_CASES),
            "excluded_smoke_case_units": list(EXPECTED_SMOKE_CASES),
            "selection_salt_hash": EXPECTED_SELECTION_SALT_HASH,
            "eligible_case_unit_set_hash": EXPECTED_ELIGIBLE_SET_HASH,
            "case_selection_order_hash": EXPECTED_SELECTION_ORDER_HASH,
            "smoke_exclusion_hash": EXPECTED_SMOKE_EXCLUSION_HASH,
            "eligible_case_ids_sha256": sha256_object(canonical_catalog["case_unit_ids"]),
        },
        "cohorts": cohorts,
        "cohort_union_count": len(union_ids),
        "cohorts_pairwise_disjoint": True,
        "manifest": manifest_audit,
        "packets": packet_audit,
        "privacy": privacy_audit,
        "checks": {
            "registry_125_minus_3_equals_122": True,
            "fixed_selection_hashes_recomputed": True,
            "cohort_rank_windows_exact": True,
            "cohorts_disjoint_and_union_122": True,
            "manifest_hash_bindings_exact": True,
            "manifest_case_agent_product_22x3": True,
            "bundle_selected_packet_identity_exact": True,
            "packet_and_raw_manifest_hashes_exact": True,
            "all_raw_files_present_and_hashed": True,
            "compact_pre_run_drafting_context_complete": True,
            "packet_outcome_isolation_enforced": True,
            "public_artifacts_path_anonymized": True,
        },
    }


def write_acceptance_receipt(receipt: Mapping[str, Any], output_path: str | Path) -> Path:
    """Write a receipt that was produced by a successful full validation."""

    _require(receipt.get("status") == "ok", "receipt.status", "only successful receipts may be written")
    _require(receipt.get("all_hard_gates_passed") is True, "receipt.gates", "all hard gates must pass")
    return write_json(output_path, receipt)


def _validate_catalog(catalog: Mapping[str, Any], *, label: str) -> dict[str, Any]:
    items = _mapping_items(catalog, label)
    _require(catalog.get("benchmark") == "MiniWoB++", f"{label}.benchmark", catalog.get("benchmark"))
    _require(catalog.get("catalog_count") == EXPECTED_CATALOG_COUNT, f"{label}.catalog_count", catalog.get("catalog_count"))
    _require(catalog.get("candidate_count") == EXPECTED_ELIGIBLE_COUNT, f"{label}.candidate_count", catalog.get("candidate_count"))
    _require(len(items) == EXPECTED_ELIGIBLE_COUNT, f"{label}.items", f"expected 122, observed {len(items)}")
    smoke = tuple(catalog.get("excluded_smoke_case_units") or ())
    _require(smoke == EXPECTED_SMOKE_CASES, f"{label}.excluded_smoke_case_units", smoke)
    _require(catalog.get("selection_salt_hash") == EXPECTED_SELECTION_SALT_HASH, f"{label}.selection_salt_hash", catalog.get("selection_salt_hash"))

    identity_records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_tasks: set[str] = set()
    seen_ranks: set[int] = set()
    seen_keys: set[str] = set()
    for index, item in enumerate(items):
        case_id = _nonempty_string(item.get("case_unit_id"), f"{label}.items[{index}].case_unit_id")
        task_id = _nonempty_string(item.get("task_id"), f"{label}.items[{index}].task_id")
        _require(case_id == task_id, f"{label}.items[{index}].identity", f"{case_id!r} != {task_id!r}")
        rank = item.get("selection_rank")
        _require(isinstance(rank, int) and not isinstance(rank, bool), f"{label}.items[{index}].selection_rank", rank)
        order_key = _nonempty_string(item.get("selection_order_key"), f"{label}.items[{index}].selection_order_key")
        expected_key = sha256_object(
            {
                "salt": "miniwob-deterministic-selection-v1",
                "domain": "miniwob",
                "case_unit_id": case_id,
                "task_id": task_id,
            }
        )
        _require(order_key == expected_key, f"{label}.items[{index}].selection_order_key", "does not recompute")
        _require(case_id not in seen_ids and task_id not in seen_tasks, f"{label}.items[{index}].identity", "duplicate case/task")
        _require(rank not in seen_ranks and order_key not in seen_keys, f"{label}.items[{index}].selection", "duplicate rank/order key")
        seen_ids.add(case_id)
        seen_tasks.add(task_id)
        seen_ranks.add(rank)
        seen_keys.add(order_key)
        identity_records.append(
            {"case_unit_id": case_id, "task_id": task_id, "selection_order_key": order_key, "selection_rank": rank}
        )
    _require(seen_ranks == set(range(EXPECTED_ELIGIBLE_COUNT)), f"{label}.selection_ranks", "must be exactly 0..121")
    ordered = sorted(identity_records, key=lambda row: (str(row["selection_order_key"]), str(row["case_unit_id"])))
    _require([row["selection_rank"] for row in ordered] == list(range(EXPECTED_ELIGIBLE_COUNT)), f"{label}.selection_order", "rank is not hash-key order")

    case_records = [
        {"case_unit_id": row["case_unit_id"], "task_id": row["task_id"]}
        for row in sorted(identity_records, key=lambda row: str(row["case_unit_id"]))
    ]
    order_records = sorted(identity_records, key=lambda row: int(row["selection_rank"]))
    recomputed = {
        "eligible_case_unit_set_hash": sha256_object(case_records),
        "case_selection_order_hash": sha256_object(order_records),
        "smoke_exclusion_hash": sha256_object(list(smoke)),
    }
    expected = {
        "eligible_case_unit_set_hash": EXPECTED_ELIGIBLE_SET_HASH,
        "case_selection_order_hash": EXPECTED_SELECTION_ORDER_HASH,
        "smoke_exclusion_hash": EXPECTED_SMOKE_EXCLUSION_HASH,
    }
    for field, expected_digest in expected.items():
        _require(recomputed[field] == expected_digest, f"{label}.{field}.recomputed", recomputed[field])
        _require(catalog.get(field) == expected_digest, f"{label}.{field}", catalog.get(field))
    by_id = {str(row["case_unit_id"]): row for row in identity_records}
    by_rank = {int(row["selection_rank"]): row for row in identity_records}
    return {
        "identity_records": sorted(identity_records, key=lambda row: int(row["selection_rank"])),
        "case_unit_ids": [str(by_rank[rank]["case_unit_id"]) for rank in range(EXPECTED_ELIGIBLE_COUNT)],
        "by_id": by_id,
        "by_rank": by_rank,
    }


def _validate_cohort(
    *,
    name: str,
    selected: Mapping[str, Any],
    expected_ranks: list[int],
    canonical_catalog: Mapping[str, Any],
) -> tuple[dict[str, Any], Path]:
    items = _mapping_items(selected, f"{name} selected source")
    _require(selected.get("benchmark") == "MiniWoB++", f"{name}.benchmark", selected.get("benchmark"))
    _require(selected.get("selected_count") == len(expected_ranks), f"{name}.selected_count", selected.get("selected_count"))
    _require(len(items) == len(expected_ranks), f"{name}.items", f"expected {len(expected_ranks)}, observed {len(items)}")
    _require(selected.get("selection_salt_hash") == EXPECTED_SELECTION_SALT_HASH, f"{name}.selection_salt_hash", selected.get("selection_salt_hash"))
    observed_ranks = [item.get("selection_rank") for item in items]
    _require(observed_ranks == expected_ranks, f"{name}.selection_ranks", observed_ranks)
    case_ids: list[str] = []
    by_rank = canonical_catalog["by_rank"]
    for index, (item, rank) in enumerate(zip(items, expected_ranks, strict=True)):
        case_id = _nonempty_string(item.get("case_unit_id"), f"{name}.items[{index}].case_unit_id")
        task_id = _nonempty_string(item.get("task_id"), f"{name}.items[{index}].task_id")
        expected = by_rank[rank]
        _require(case_id == task_id == expected["case_unit_id"], f"{name}.items[{index}].identity", f"rank {rank} identity mismatch")
        _require(item.get("selection_order_key") == expected["selection_order_key"], f"{name}.items[{index}].selection_order_key", "catalog mismatch")
        case_ids.append(case_id)
    _require(len(set(case_ids)) == len(case_ids), f"{name}.case_unit_ids", "duplicates observed")
    candidate_path_value = _nonempty_string(selected.get("candidate_pool_path"), f"{name}.candidate_pool_path")
    candidate_path = _input_file(candidate_path_value, f"{name} referenced catalog")
    return (
        {
            "count": len(items),
            "rank_start": expected_ranks[0],
            "rank_end": expected_ranks[-1],
            "case_unit_ids_sha256": sha256_object(case_ids),
            "case_unit_ids": case_ids,
        },
        candidate_path,
    )


def _validate_execution_inputs(*, infra: Mapping[str, Any], agents_config: Mapping[str, Any]) -> None:
    _require(isinstance(infra.get("machines"), list) and bool(infra.get("machines")), "execution_infra.machines", "missing/non-list")
    roles = agents_config.get("experimental_agents")
    _require(isinstance(roles, Mapping), "agents_config.experimental_agents", "missing/non-mapping")
    _require(tuple(roles) == EXPECTED_AGENTS, "agents_config.experimental_agents", f"must be exactly {EXPECTED_AGENTS}")
    domain_map = agents_config.get("main_domain_agent_map")
    _require(isinstance(domain_map, Mapping), "agents_config.main_domain_agent_map", "missing/non-mapping")
    _require(tuple(domain_map.get("miniwob") or ()) == EXPECTED_AGENTS, "agents_config.main_domain_agent_map.miniwob", f"must be exactly {EXPECTED_AGENTS}")


def _validate_manifest(
    *,
    manifest: Mapping[str, Any],
    manifest_path: Path,
    catalog_path: Path,
    bundle_path: Path,
    infra_path: Path,
    agents_path: Path,
    agents_config: Mapping[str, Any],
    remaining_items: Sequence[Mapping[str, Any]],
    expected_result_namespace: str,
) -> dict[str, Any]:
    _require(manifest.get("schema_version") == "experiment_manifest/v1", "manifest.schema_version", manifest.get("schema_version"))
    _require(manifest.get("result_namespace") == expected_result_namespace, "manifest.result_namespace", manifest.get("result_namespace"))
    _require(manifest.get("infra_config_hash") == sha256_file(infra_path), "manifest.infra_config_hash", "execution infra hash mismatch")
    _require(manifest.get("agents_config_hash") == sha256_file(agents_path), "manifest.agents_config_hash", "agents config hash mismatch")
    _require(manifest.get("source_bundle_hash") == sha256_file(bundle_path), "manifest.source_bundle_hash", "source bundle hash mismatch")

    agent_entries = manifest.get("agents")
    _require(isinstance(agent_entries, list), "manifest.agents", "missing/non-list")
    _require(tuple(entry.get("agent_id") for entry in agent_entries if isinstance(entry, Mapping)) == EXPECTED_AGENTS, "manifest.agents", f"must be exactly {EXPECTED_AGENTS}")
    roles = agents_config["experimental_agents"]
    for index, (entry, agent_id) in enumerate(zip(agent_entries, EXPECTED_AGENTS, strict=True)):
        _require(isinstance(entry, Mapping), f"manifest.agents[{index}]", "must be mapping")
        _require(entry.get("config_hash") == sha256_object(roles[agent_id]), f"manifest.agents[{index}].config_hash", "agent role hash mismatch")

    domains = manifest.get("domains")
    _require(isinstance(domains, list) and len(domains) == 1 and isinstance(domains[0], Mapping), "manifest.domains", "must contain exactly one mapping")
    domain = domains[0]
    _require(domain.get("domain") == "miniwob", "manifest.domains[0].domain", domain.get("domain"))
    _require(domain.get("case_unit_count") == EXPECTED_REMAINING_COUNT, "manifest.domains[0].case_unit_count", domain.get("case_unit_count"))
    _require(domain.get("record_slot_count") == EXPECTED_RECORD_SLOT_COUNT, "manifest.domains[0].record_slot_count", domain.get("record_slot_count"))
    _require(domain.get("official_split_eligible_case_units") == EXPECTED_ELIGIBLE_COUNT, "manifest.domains[0].official_split_eligible_case_units", domain.get("official_split_eligible_case_units"))
    _require(domain.get("official_split_hash") == sha256_file(catalog_path), "manifest.domains[0].official_split_hash", "remaining catalog hash mismatch")
    cases = domain.get("case_units")
    _require(isinstance(cases, list) and len(cases) == EXPECTED_REMAINING_COUNT, "manifest.domains[0].case_units", "must contain 22 cases")
    expected_refs = [(str(item["case_unit_id"]), str(item["task_id"])) for item in remaining_items]
    observed_refs = [
        (str(case.get("case_unit_id") or ""), str(case.get("task_id") or ""))
        for case in cases
        if isinstance(case, Mapping)
    ]
    _require(observed_refs == expected_refs, "manifest.domains[0].case_units", "must exactly match remaining22 selection order")
    expected_slot_hash = sha256_object(
        [{"case_unit_id": case_id, "agent_id": agent_id} for case_id, _task_id in expected_refs for agent_id in EXPECTED_AGENTS]
    )
    _require(domain.get("planned_record_slot_ids_hash") == expected_slot_hash, "manifest.domains[0].planned_record_slot_ids_hash", "22x3 slot hash mismatch")

    deterministic = manifest.get("deterministic_selection")
    _require(isinstance(deterministic, Mapping), "manifest.deterministic_selection", "missing/non-mapping")
    expected_fields: dict[str, Any] = {
        "hash_salt_hash": EXPECTED_SELECTION_SALT_HASH,
        "eligible_case_unit_set_hash": EXPECTED_ELIGIBLE_SET_HASH,
        "case_selection_order_hash": EXPECTED_SELECTION_ORDER_HASH,
        "smoke_exclusion_hash": EXPECTED_SMOKE_EXCLUSION_HASH,
        "excluded_smoke_case_units": list(EXPECTED_SMOKE_CASES),
    }
    for field, expected in expected_fields.items():
        _require(deterministic.get(field) == expected, f"manifest.deterministic_selection.{field}", deterministic.get(field))
    return {
        "path": _display_path(manifest_path),
        "sha256": sha256_file(manifest_path),
        "case_unit_count": EXPECTED_REMAINING_COUNT,
        "record_slot_count": EXPECTED_RECORD_SLOT_COUNT,
        "agents": list(EXPECTED_AGENTS),
        "result_namespace": expected_result_namespace,
        "infra_config_sha256": sha256_file(infra_path),
        "agents_config_sha256": sha256_file(agents_path),
        "official_split_sha256": sha256_file(catalog_path),
        "source_bundle_sha256": sha256_file(bundle_path),
    }


def _validate_bundle_and_packets(
    *,
    bundle: Mapping[str, Any],
    bundle_path: Path,
    manifest: Mapping[str, Any],
    manifest_path: Path,
    packet_root: Path,
    remaining_items: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    _require(bundle.get("schema_version") == "contract_source_bundle.v2", "source_bundle.schema_version", bundle.get("schema_version"))
    _require(bundle.get("source_count") == EXPECTED_REMAINING_COUNT, "source_bundle.source_count", bundle.get("source_count"))
    sources = bundle.get("sources")
    _require(isinstance(sources, list) and len(sources) == EXPECTED_REMAINING_COUNT, "source_bundle.sources", "must contain 22 sources")
    declared_manifest = _input_file(_nonempty_string(bundle.get("manifest_path"), "source_bundle.manifest_path"), "source bundle manifest")
    _require(declared_manifest == manifest_path, "source_bundle.manifest_path", "must resolve to supplied manifest")
    definition = dict(manifest)
    definition.pop("source_bundle_hash", None)
    _require(bundle.get("manifest_definition_sha256") == sha256_object(definition), "source_bundle.manifest_definition_sha256", "manifest definition hash mismatch")
    _require(bundle.get("manifest_definition_sha256_scope") == "canonical_mapping_without_source_bundle_hash", "source_bundle.manifest_definition_sha256_scope", bundle.get("manifest_definition_sha256_scope"))
    _require(bundle.get("manifest_definition_excluded_fields") == ["source_bundle_hash"], "source_bundle.manifest_definition_excluded_fields", bundle.get("manifest_definition_excluded_fields"))

    domain_root = packet_root / "miniwob" if (packet_root / "miniwob").is_dir() else packet_root
    _require(not domain_root.is_symlink(), "case_packets.domain_root", "symlink roots are not accepted")
    expected_ids = [str(item["case_unit_id"]) for item in remaining_items]
    domain_entries = list(domain_root.iterdir())
    actual_case_dirs = sorted(path.name for path in domain_entries if path.is_dir() and not path.is_symlink())
    _require(
        len(domain_entries) == EXPECTED_REMAINING_COUNT
        and set(actual_case_dirs) == set(expected_ids)
        and len(actual_case_dirs) == EXPECTED_REMAINING_COUNT,
        "case_packets.case_directories",
        "must contain only the 22 remaining case directories",
    )
    _require(all(not path.is_symlink() for path in domain_root.rglob("*")), "case_packets.symlinks", "symlinks are forbidden")

    verified_raw_files = 0
    verified_raw_bytes = 0
    compact_packet_bytes: list[int] = []
    stronger_condition_case_count = 0
    stronger_condition_count = 0
    public_files: set[Path] = {bundle_path, manifest_path}
    contract_ids: set[str] = set()
    observed_refs: list[tuple[str, str]] = []
    for index, (source, selected_item) in enumerate(zip(sources, remaining_items, strict=True)):
        _require(isinstance(source, Mapping), f"source_bundle.sources[{index}]", "must be mapping")
        case_id = str(selected_item["case_unit_id"])
        task_id = str(selected_item["task_id"])
        observed_refs.append((str(source.get("case_unit_id") or ""), str(source.get("task_id") or "")))
        _require(source.get("domain") == "miniwob", f"source_bundle.sources[{index}].domain", source.get("domain"))
        _require(source.get("case_unit_id") == case_id and source.get("task_id") == task_id, f"source_bundle.sources[{index}].identity", "selected source mismatch")
        contract_id = _nonempty_string(source.get("contract_id"), f"source_bundle.sources[{index}].contract_id")
        _require(contract_id not in contract_ids, f"source_bundle.sources[{index}].contract_id", "duplicate")
        contract_ids.add(contract_id)
        draft = source.get("draft_input")
        _require(isinstance(draft, Mapping), f"source_bundle.sources[{index}].draft_input", "missing/non-mapping")
        _require(
            set(draft) == {"case_packet_path", "case_packet_sha256", "raw_case_manifest_path", "raw_case_manifest_sha256"},
            f"source_bundle.sources[{index}].draft_input",
            "unexpected/missing fields",
        )
        case_dir = (domain_root / case_id).resolve()
        _require(case_dir.parent == domain_root.resolve(), f"case_packets.{case_id}", "unsafe case ID/path")
        case_entries = {entry.name: entry for entry in case_dir.iterdir()}
        _require(
            set(case_entries) == {"case_packet.md", "raw_case_manifest.json", "raw_case"}
            and case_entries["case_packet.md"].is_file()
            and case_entries["raw_case_manifest.json"].is_file()
            and case_entries["raw_case"].is_dir(),
            f"case_packets.{case_id}.layout",
            "must contain exactly case_packet.md, raw_case_manifest.json, and raw_case/",
        )
        expected_paths = {
            "case_packet_path": case_dir / "case_packet.md",
            "raw_case_manifest_path": case_dir / "raw_case_manifest.json",
        }
        for path_field, expected_path in expected_paths.items():
            declared = _input_file(_nonempty_string(draft.get(path_field), f"source_bundle.sources[{index}].{path_field}"), path_field)
            _require(declared == expected_path, f"source_bundle.sources[{index}].{path_field}", "does not route to expected case directory")
            hash_field = path_field.replace("_path", "_sha256")
            digest = draft.get(hash_field)
            _require(isinstance(digest, str) and _SHA256_RE.fullmatch(digest) is not None, f"source_bundle.sources[{index}].{hash_field}", digest)
            _require(digest == sha256_file(declared), f"source_bundle.sources[{index}].{hash_field}", "file hash mismatch")
            public_files.add(declared)

        raw_manifest_path = expected_paths["raw_case_manifest_path"]
        raw_manifest = _load_mapping(raw_manifest_path, f"raw manifest {case_id}")
        _require(raw_manifest.get("domain") == "miniwob", f"raw_manifest.{case_id}.domain", raw_manifest.get("domain"))
        _require(raw_manifest.get("case_unit_id") == case_id and raw_manifest.get("task_id") == task_id, f"raw_manifest.{case_id}.identity", "selected source mismatch")
        raw_root = case_dir / "raw_case"
        _require(raw_root.is_dir() and not raw_root.is_symlink(), f"raw_manifest.{case_id}.raw_case", "directory missing or symlink")
        hashes = raw_manifest.get("sha256_per_file")
        copied = raw_manifest.get("copied_files")
        _require(isinstance(hashes, Mapping) and isinstance(copied, list), f"raw_manifest.{case_id}.files", "missing copied_files/sha256_per_file")
        _require(len(copied) == len(set(copied)) and set(copied) == set(hashes), f"raw_manifest.{case_id}.copied_files", "must uniquely equal sha256_per_file keys")
        actual_files = sorted(path.relative_to(raw_root).as_posix() for path in raw_root.rglob("*") if path.is_file())
        _require(actual_files == sorted(copied), f"raw_manifest.{case_id}.raw_tree", "extra or missing raw files")
        for relative in copied:
            _require(_safe_relative_path(relative), f"raw_manifest.{case_id}.copied_files", f"unsafe path: {relative!r}")
            file_path = raw_root / relative
            _require(file_path.is_file() and not file_path.is_symlink(), f"raw_manifest.{case_id}.{relative}", "missing/non-regular/symlink")
            digest = hashes.get(relative)
            _require(isinstance(digest, str) and _SHA256_RE.fullmatch(digest) is not None, f"raw_manifest.{case_id}.sha256_per_file.{relative}", digest)
            _require(digest == sha256_file(file_path), f"raw_manifest.{case_id}.sha256_per_file.{relative}", "raw file hash mismatch")
            verified_raw_files += 1
            verified_raw_bytes += file_path.stat().st_size
            public_files.add(file_path)
        for field in ("official_files", "derived_files", "packet_files"):
            values = raw_manifest.get(field)
            _require(isinstance(values, list) and len(values) == len(set(values)), f"raw_manifest.{case_id}.{field}", "missing/non-list/duplicates")
            _require(set(values).issubset(set(copied)), f"raw_manifest.{case_id}.{field}", "references uncopied file")
        file_sources = raw_manifest.get("file_sources")
        _require(isinstance(file_sources, Mapping) and set(file_sources) == set(copied), f"raw_manifest.{case_id}.file_sources", "must cover every copied file")

        derived_path = raw_root / "derived/selected_task_source.json"
        _require(derived_path.is_file(), f"raw_manifest.{case_id}.derived_source", "missing")
        _require(_load_mapping(derived_path, f"derived selected source {case_id}") == dict(selected_item), f"raw_manifest.{case_id}.derived_source", "does not exactly equal selected item")
        descriptors = selected_item.get("official_files")
        _require(isinstance(descriptors, list) and bool(descriptors), f"selected.{case_id}.official_files", "missing/non-list")
        expected_official: dict[str, Mapping[str, Any]] = {}
        for descriptor in descriptors:
            _require(isinstance(descriptor, Mapping), f"selected.{case_id}.official_files", "descriptor must be mapping")
            archive_path = _nonempty_string(descriptor.get("archive_path"), f"selected.{case_id}.official_files.archive_path")
            _require(archive_path not in expected_official, f"selected.{case_id}.official_files", "duplicate archive_path")
            expected_official[archive_path] = descriptor
        _require(set(raw_manifest.get("official_files") or ()) == set(expected_official), f"raw_manifest.{case_id}.official_files", "selected descriptor mismatch")
        _require(raw_manifest.get("packet_files") == selected_item.get("packet_files"), f"raw_manifest.{case_id}.packet_files", "selected packet_files mismatch")
        packet_semantics = _validate_compact_packet_semantics(
            case_id=case_id,
            task_id=task_id,
            case_packet_path=expected_paths["case_packet_path"],
            raw_root=raw_root,
            raw_manifest=raw_manifest,
        )
        compact_packet_bytes.append(int(packet_semantics["packet_bytes"]))
        condition_count = int(packet_semantics["stronger_condition_count"])
        stronger_condition_count += condition_count
        stronger_condition_case_count += int(condition_count > 0)
        for archive_path, descriptor in expected_official.items():
            _require(hashes.get(archive_path) == descriptor.get("sha256"), f"raw_manifest.{case_id}.{archive_path}", "selected official hash mismatch")
            _require(file_sources.get(archive_path) == descriptor.get("source_path"), f"raw_manifest.{case_id}.{archive_path}.source", "selected official source path mismatch")

    expected_refs = [(str(item["case_unit_id"]), str(item["task_id"])) for item in remaining_items]
    _require(observed_refs == expected_refs, "source_bundle.sources", "source ordering/identity does not match remaining22 selection")
    expected_stronger_counts = [
        len(MINIWOB_STRONGER_CONDITION_SPECS_V1.get(case_id, ()))
        for case_id, _task_id in expected_refs
    ]
    _require(
        stronger_condition_case_count == sum(count > 0 for count in expected_stronger_counts)
        and stronger_condition_count == sum(expected_stronger_counts),
        "compact_packets.stronger_measurement",
        "source-supported stronger condition coverage differs from the frozen 22-case basis",
    )
    return {
        "source_bundle_path": _display_path(bundle_path),
        "source_bundle_sha256": sha256_file(bundle_path),
        "case_packets_root": _display_path(domain_root),
        "case_packets_tree_sha256": sha256_path(domain_root),
        "source_count": EXPECTED_REMAINING_COUNT,
        "packet_count": EXPECTED_REMAINING_COUNT,
        "raw_manifest_count": EXPECTED_REMAINING_COUNT,
        "verified_raw_file_count": verified_raw_files,
        "verified_raw_byte_count": verified_raw_bytes,
        "max_compact_packet_bytes": max(compact_packet_bytes),
        "total_compact_packet_bytes": sum(compact_packet_bytes),
        "stronger_condition_case_count": stronger_condition_case_count,
        "stronger_condition_count": stronger_condition_count,
        "contract_id_count": len(contract_ids),
        "public_files": public_files,
    }


def _validate_compact_packet_semantics(
    *,
    case_id: str,
    task_id: str,
    case_packet_path: Path,
    raw_root: Path,
    raw_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    packet_files = list(raw_manifest.get("packet_files") or [])
    task_html = [
        value
        for value in packet_files
        if isinstance(value, str)
        and value.startswith("official/install/miniwob/html/miniwob/")
        and value.endswith(".html")
    ]
    _require(len(task_html) == 1, f"compact_packet.{case_id}.task_html", task_html)
    expected_packet_files = [*MINIWOB_COMPACT_DERIVED_FILES, task_html[0]]
    _require(
        packet_files == expected_packet_files,
        f"compact_packet.{case_id}.packet_files",
        f"expected {expected_packet_files}, observed {packet_files}",
    )
    _require(
        not any(
            value.endswith(("all.py", "base.py", ".min.js", ".min.css"))
            for value in packet_files
        ),
        f"compact_packet.{case_id}.minimality",
        "full registry/base or minified dependency leaked into drafting view",
    )

    packet_bytes = case_packet_path.stat().st_size
    _require(
        packet_bytes <= MAX_COMPACT_PACKET_BYTES,
        f"compact_packet.{case_id}.size",
        f"{packet_bytes} > {MAX_COMPACT_PACKET_BYTES}",
    )
    packet_text = case_packet_path.read_text(encoding="utf-8")
    for marker in _FORBIDDEN_PACKET_OUTCOME_MARKERS:
        _require(
            marker not in packet_text,
            f"compact_packet.{case_id}.outcome_isolation",
            f"forbidden marker {marker!r}",
        )
    for relative in packet_files:
        _require(
            f"### `{relative}`" in packet_text,
            f"compact_packet.{case_id}.rendered_source",
            f"missing heading for {relative}",
        )
    for relative in raw_manifest.get("official_files") or []:
        if relative in packet_files:
            continue
        _require(
            f"### `{relative}`" not in packet_text,
            f"compact_packet.{case_id}.minimality",
            f"non-packet official source was rendered: {relative}",
        )

    context_path = raw_root / "derived/drafting_context.json"
    context = _load_mapping(context_path, f"drafting context {case_id}")
    _require(
        context.get("schema_version") == MINIWOB_DRAFTING_CONTEXT_SCHEMA,
        f"drafting_context.{case_id}.schema_version",
        context.get("schema_version"),
    )
    _require(
        context.get("case_unit_id") == case_id and context.get("task_id") == task_id,
        f"drafting_context.{case_id}.identity",
        "case/task mismatch",
    )
    _require(
        context.get("phase") == "pre_run_checklist_drafting"
        and context.get("locked_before_outcomes") is True
        and context.get("contains_agent_outcomes") is False,
        f"drafting_context.{case_id}.pre_run_isolation",
        "pre-run flags are incomplete",
    )
    source_priority = context.get("source_priority")
    _require(
        isinstance(source_priority, list)
        and bool(source_priority)
        and str(source_priority[0]).startswith("released evaluator/oracle"),
        f"drafting_context.{case_id}.source_priority",
        source_priority,
    )
    if "derived/runtime_decision_wiring.json" in packet_files:
        runtime_wiring = _load_mapping(
            raw_root / "derived/runtime_decision_wiring.json",
            f"runtime decision wiring {case_id}",
        )
        _require(
            runtime_wiring.get("schema_version") == MINIWOB_RUNTIME_WIRING_SCHEMA
            and runtime_wiring.get("case_unit_id") == case_id
            and runtime_wiring.get("task_id") == task_id,
            f"runtime_decision_wiring.{case_id}.identity",
            "schema/case/task mismatch",
        )
        runtime_excerpts = runtime_wiring.get("excerpts")
        _require(
            isinstance(runtime_excerpts, Mapping)
            and isinstance(runtime_excerpts.get("worker_run_smoke_job"), Mapping)
            and bool(runtime_excerpts["worker_run_smoke_job"].get("content"))
            and isinstance(runtime_excerpts.get("adapter_execute_smoke_job"), Mapping)
            and bool(runtime_excerpts["adapter_execute_smoke_job"].get("content")),
            f"runtime_decision_wiring.{case_id}.excerpts",
            "worker/adapter exact excerpts are missing",
        )
    policy = context.get("official_policy")
    _require(
        isinstance(policy, Mapping)
        and policy.get("applicability") == "N/A"
        and bool(policy.get("support")),
        f"drafting_context.{case_id}.official_policy",
        policy,
    )
    released = context.get("released_evaluator")
    _require(
        isinstance(released, Mapping)
        and released.get("entrypoint") == "env.unwrapped.task.validate(page, chat_messages)"
        and "RAW_REWARD_GLOBAL > 0" in str(released.get("native_semantics") or "")
        and bool(released.get("support")),
        f"drafting_context.{case_id}.released_evaluator",
        "formal native semantics are incomplete",
    )
    state_schema = context.get("evaluator_visible_state_schema")
    expected_state_fields = [
        "REWARD_GLOBAL",
        "RAW_REWARD_GLOBAL",
        "REWARD_REASON",
        "DONE_GLOBAL",
        "EPISODE_ID",
        "TASK_READY",
    ]
    _require(
        isinstance(state_schema, Mapping)
        and state_schema.get("fields") == expected_state_fields
        and bool(state_schema.get("support")),
        f"drafting_context.{case_id}.state_schema",
        state_schema,
    )
    artifact_inventory = context.get("artifact_inventory")
    _require(
        isinstance(artifact_inventory, Mapping)
        and artifact_inventory.get("known_before_run") is True
        and artifact_inventory.get("artifact_types") == list(MINIWOB_POST_RUN_ARTIFACT_TYPES)
        and len(artifact_inventory.get("retained_artifacts") or []) >= 8,
        f"drafting_context.{case_id}.artifact_inventory",
        "missing or incomplete retained-artifact contract",
    )
    reporting = context.get("post_run_reporting")
    _require(
        isinstance(reporting, Mapping)
        and reporting.get("native_evidence_labels")
        == {"S": "Evidence Pass", "F": "Evidence Fail", "U": "Unknown"}
        and reporting.get("paper_counts") == {"S": "P", "F": "F", "U": "U"}
        and "Never predeclare conflict" in str(reporting.get("benchmark_conflict_rule") or ""),
        f"drafting_context.{case_id}.post_run_reporting",
        "S/F/U, stronger, or benchmark-conflict boundary is incomplete",
    )
    stronger = context.get("stronger_measurement")
    candidates = (
        list(stronger.get("required_additional_conditions") or [])
        if isinstance(stronger, Mapping)
        else []
    )
    _require(
        isinstance(stronger, Mapping)
        and "Copy every required_additional_conditions item" in str(stronger.get("drafting_instruction") or "")
        and stronger.get("empty_when_no_required_condition") is True,
        f"drafting_context.{case_id}.stronger.drafting_rule",
        "required stronger-condition copying/empty-list rule is missing",
    )
    expected_specs = list(MINIWOB_STRONGER_CONDITION_SPECS_V1.get(case_id, ()))
    _require(
        [candidate.get("id") for candidate in candidates if isinstance(candidate, Mapping)]
        == [spec["id"] for spec in expected_specs],
        f"drafting_context.{case_id}.stronger.ids",
        candidates,
    )
    for candidate, spec in zip(candidates, expected_specs, strict=True):
        _require(isinstance(candidate, Mapping), f"drafting_context.{case_id}.stronger", candidate)
        for field in ("text", "rationale", "native_gap"):
            _require(
                candidate.get(field) == spec[field],
                f"drafting_context.{case_id}.stronger.{candidate.get('id')}.{field}",
                "does not match frozen source-supported specification",
            )
        _require(
            bool(candidate.get("support")) and bool(candidate.get("decisive_post_run_artifacts")),
            f"drafting_context.{case_id}.stronger.{candidate.get('id')}.evidence",
            "support/artifacts missing",
        )

    excerpts_path = raw_root / "derived/official_source_excerpts.json"
    excerpts = _load_mapping(excerpts_path, f"source excerpts {case_id}")
    _require(
        excerpts.get("schema_version") == MINIWOB_SOURCE_EXCERPTS_SCHEMA,
        f"source_excerpts.{case_id}.schema_version",
        excerpts.get("schema_version"),
    )
    _require(
        excerpts.get("case_unit_id") == case_id and excerpts.get("task_id") == task_id,
        f"source_excerpts.{case_id}.identity",
        "case/task mismatch",
    )
    source_inventory = excerpts.get("source_inventory")
    _require(
        isinstance(source_inventory, Mapping)
        and set(source_inventory)
        == {"task_class", "base_validator", "core_reward_wiring", "task_html"},
        f"source_excerpts.{case_id}.source_inventory",
        source_inventory,
    )
    raw_hashes = raw_manifest.get("sha256_per_file") or {}
    for label, descriptor in source_inventory.items():
        _require(isinstance(descriptor, Mapping), f"source_excerpts.{case_id}.{label}", descriptor)
        source_path = descriptor.get("path")
        _require(
            isinstance(source_path, str)
            and descriptor.get("sha256") == raw_hashes.get(source_path),
            f"source_excerpts.{case_id}.{label}.source_identity",
            "path/hash does not bind to raw manifest",
        )
    excerpt_items = excerpts.get("excerpts") or {}
    base_methods = ((excerpt_items.get("base_validator") or {}).get("methods") or {})
    _require(
        set(base_methods) == {"_get_goal", "_get_info", "validate"}
        and all(not item.get("fallback") for item in base_methods.values()),
        f"source_excerpts.{case_id}.base_validator",
        "exact evaluator method extraction failed",
    )
    _require(
        not (excerpt_items.get("task_class") or {}).get("fallback")
        and not (excerpt_items.get("core_reward_wiring") or {}).get("fallback"),
        f"source_excerpts.{case_id}.exact_extraction",
        "task class or core reward extraction fell back to full source",
    )
    return {
        "packet_bytes": packet_bytes,
        "stronger_condition_count": len(candidates),
    }


def _scan_public_artifacts(paths: set[Path]) -> dict[str, Any]:
    files: set[Path] = set()
    for path in paths:
        if path.is_dir():
            files.update(item for item in path.rglob("*") if item.is_file())
        elif path.is_file():
            files.add(path)
        else:
            raise ContractLifecycleError(f"public_artifact_scan: missing path {path}")
    for file_path in sorted(files):
        content = file_path.read_bytes().decode("utf-8", errors="ignore")
        for marker in _FORBIDDEN_PUBLIC_MARKERS:
            _require(marker not in content, "public_artifact_path_anonymization", f"{marker!r} found in {_display_path(file_path)}")
    return {
        "scanned_file_count": len(files),
        "path_leakage_policy": "miniwob_public_path_anonymization/v1",
        "forbidden_marker_count": len(_FORBIDDEN_PUBLIC_MARKERS),
        "forbidden_markers_sha256": sha256_object(list(_FORBIDDEN_PUBLIC_MARKERS)),
        "allowed_root_tokens": ["<MINIWOB_INSTALL_ROOT>", "<MINIWOB_VENV_ROOT>"],
        "violations": 0,
    }


def _mapping_items(payload: Mapping[str, Any], label: str) -> list[Mapping[str, Any]]:
    items = payload.get("items")
    _require(isinstance(items, list), f"{label}.items", "missing/non-list")
    _require(all(isinstance(item, Mapping) for item in items), f"{label}.items", "every item must be a mapping")
    return list(items)


def _input_file(path: str | Path, label: str) -> Path:
    unresolved = resolve_repo_path(path)
    _require(unresolved.is_file(), label, f"file is missing: {unresolved}")
    _require(not unresolved.is_symlink(), label, "symlink inputs are not accepted")
    return unresolved.resolve()


def _load_mapping(path: Path, label: str) -> dict[str, Any]:
    payload = load_json_or_yaml(path)
    _require(isinstance(payload, Mapping), label, "must be a mapping")
    return dict(payload)


def _safe_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return (
        value == path.as_posix()
        and not path.is_absolute()
        and all(part not in {"", ".", ".."} for part in path.parts)
    )


def _nonempty_string(value: Any, gate: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), gate, "must be a non-empty string")
    return value.strip()


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(resolve_repo_path(".").resolve()).as_posix()
    except ValueError:
        return str(path)


def _require(condition: bool, gate: str, detail: Any) -> None:
    if not condition:
        raise ContractLifecycleError(f"{gate}: {detail}")
