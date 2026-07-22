"""Immutable refreeze ledger for the AppWorld GPT-5.6 draft definition.

The ledger is deliberately separate from the draft-run lock.  It binds a new,
clean 485-case materialization namespace after a real stability observation
window and before any canary or formal model call.  Both publication and
verification fail closed on path aliases, symlinks, unlisted materialization
files, stale packet acceptance, evaluator-composition drift, or runtime-config
drift.
"""

from __future__ import annotations

import json
import os
import re
import time
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evidence_system.contracts import appworld_draft_acceptance_v56 as draft_acceptance
from evidence_system.contracts.appworld_checklist_semantics import (
    validate_appworld_packet_evaluator_semantics,
)
from evidence_system.contracts.appworld_extension import (
    ACCEPTANCE_SCHEMA as PACKET_ACCEPTANCE_SCHEMA,
    AGENT_IDS,
    APPWORLD_DATA_VERSION,
    APPWORLD_GIT_COMMIT,
    DEFAULT_AGENTS_CONFIG,
    DEFAULT_BASE_DBS_ROOT,
    DEFAULT_CHALLENGE_SPLIT,
    DEFAULT_CURRENT_CATALOG,
    DEFAULT_DATA_VERSION_PATH,
    DEFAULT_EXISTING_MANIFEST,
    DEFAULT_EXISTING_PACKETS,
    DEFAULT_EXISTING_SCORE_ROOT,
    DEFAULT_EXISTING_SOURCE_BUNDLE,
    DEFAULT_INSTALL_LOG,
    DEFAULT_NORMAL_SPLIT,
    DEFAULT_SCORE_PROMPT,
    DEFAULT_SCORE_SCHEMA,
    DEFAULT_SNAPSHOT_README,
    DEFAULT_TASKS_ROOT,
    EXPECTED_CHALLENGE_COUNT,
    EXPECTED_EXTENSION_COUNT,
    EXPECTED_FILES_PER_TASK,
    EXPECTED_NORMAL_EXTENSION_COUNT,
    EXPERIMENT_ID,
    REQUIRED_TASK_FILES,
    validate_extension_definition,
    validate_extension_packets,
    validate_extension_source_bundle,
)
from evidence_system.contracts.case_packets import APPWORLD_EVALUATOR_SEMANTICS_PATH
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import repo_root


LEDGER_SCHEMA = "appworld_definition_refreeze_gpt56_strict_v3.v1"
SNAPSHOT_SCHEMA = "appworld_definition_refreeze_snapshot.v1"
PACKET_AUDIT_SCHEMA = "appworld_packet_evaluator_batch.v1"
MINIMUM_STABILITY_WINDOW_SECONDS = 60
STABILITY_SAMPLE_INTERVAL_SECONDS = 10
MINIMUM_STABILITY_SAMPLE_COUNT = 7
EXPECTED_REGISTERED_TEST_COUNT = 3_817
EXPECTED_NON_SCORING_TASK_COMPLETED_COUNT = EXPECTED_EXTENSION_COUNT
EXPECTED_LARGE_CASE_THRESHOLD_BYTES = 100_000

LEGACY_MATERIALIZATION_ROOT = Path("experiments/appworld_full_test_extension_v1")
DEFAULT_MATERIALIZATION_ROOT = Path(
    "experiments/appworld_full_test_extension_v1_gpt56_strict_v3_lockfix_v6"
)
LEDGER_BASENAME = "definition_refreeze_gpt56_strict_v3.json"
DEFAULT_LEDGER_PATH = DEFAULT_MATERIALIZATION_ROOT / "provenance" / LEDGER_BASENAME

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_NEW_NAMESPACE_RE = re.compile(
    r"appworld_full_test_extension_[a-z0-9_.-]*gpt56[a-z0-9_.-]*"
)
_MATERIALIZATION_FIXED_FILES = frozenset(
    {
        "experiment_manifest.json",
        "frozen_scope.json",
        "official_splits/appworld_extension_all.txt",
        "official_splits/appworld_selected_task_sources.json",
        "official_splits/appworld_test_challenge.txt",
        "official_splits/appworld_test_normal_extension.txt",
        "provenance/acceptance_report.json",
        "source_bundles/case_packet_source_bundle.json",
    }
)

_UPSTREAM_FILES = {
    "normal_split": DEFAULT_NORMAL_SPLIT,
    "challenge_split": DEFAULT_CHALLENGE_SPLIT,
    "selected_100_catalog": DEFAULT_CURRENT_CATALOG,
    "data_version": DEFAULT_DATA_VERSION_PATH,
    "snapshot_readme": DEFAULT_SNAPSHOT_README,
    "install_log": DEFAULT_INSTALL_LOG,
    "selected_100_source_bundle": DEFAULT_EXISTING_SOURCE_BUNDLE,
    "selected_100_manifest": DEFAULT_EXISTING_MANIFEST,
}
_UPSTREAM_TREES = {
    "appworld_tasks": DEFAULT_TASKS_ROOT,
    "appworld_base_dbs": DEFAULT_BASE_DBS_ROOT,
    "selected_100_score_and_draft_package": DEFAULT_EXISTING_SCORE_ROOT,
    "selected_100_case_packets": DEFAULT_EXISTING_PACKETS,
}
_PROTOCOL_FILES = {
    "agents_config": DEFAULT_AGENTS_CONFIG,
    "score_prompt": DEFAULT_SCORE_PROMPT,
    "score_schema": DEFAULT_SCORE_SCHEMA,
    "draft_prompt": Path(
        "neurips_ed_track_minimal/prompts/draft_case_checklist.prompt.md"
    ),
    "draft_prompt_supplement": Path(
        "neurips_ed_track_minimal/prompts/appworld_gpt56_draft_strict_v3.supplement.md"
    ),
    "draft_schema": Path("neurips_ed_track_minimal/schemas/case_checklist.schema.json"),
    "draft_template": Path(
        "neurips_ed_track_minimal/templates/case_checklist.template.yaml"
    ),
    "frozen_evaluator_semantics": APPWORLD_EVALUATOR_SEMANTICS_PATH,
    "stronger_gap_registry": Path(
        "experiments/appworld_full_test_extension_v1/official_splits/"
        "appworld_stronger_gap_registry.gpt56.v2.json"
    ),
    "stronger_gap_review_policy": Path(
        "experiments/appworld_full_test_extension_v1/official_splits/"
        "appworld_stronger_gap_review_policy.gpt56.v1.json"
    ),
    "stronger_gap_review_receipt": Path(
        "experiments/appworld_full_test_extension_v1/official_splits/"
        "appworld_stronger_gap_review_receipt.gpt56.v1.json"
    ),
}
_MATERIALIZATION_CODE_FILES = {
    "build_appworld_extension_cli": Path(
        "src/evidence_system/cli/build_appworld_extension.py"
    ),
    "build_case_packets_cli": Path("src/evidence_system/cli/build_case_packets.py"),
    "build_source_bundle_cli": Path(
        "src/evidence_system/cli/build_case_packet_source_bundle.py"
    ),
    "validate_appworld_extension_cli": Path(
        "src/evidence_system/cli/validate_appworld_extension.py"
    ),
    "refreeze_contract": Path("src/evidence_system/contracts/appworld_refreeze_v56.py"),
    "refreeze_cli": Path("src/evidence_system/cli/refreeze_appworld_drafts_v56.py"),
    "stronger_gap_registry_builder": Path(
        "src/evidence_system/cli/build_appworld_stronger_gap_registry.py"
    ),
    "stronger_gap_contract": Path(
        "src/evidence_system/contracts/appworld_stronger_gaps.py"
    ),
    "support_pointer_contract": Path(
        "src/evidence_system/contracts/appworld_support_pointers.py"
    ),
    "appworld_checklist_semantics": Path(
        "src/evidence_system/contracts/appworld_checklist_semantics.py"
    ),
}


def freeze_appworld_definition_v56(
    *,
    materialization_root: str | Path = DEFAULT_MATERIALIZATION_ROOT,
    output_path: str | Path | None = None,
    stability_window_seconds: int = MINIMUM_STABILITY_WINDOW_SECONDS,
    _minimum_stability_seconds: int = MINIMUM_STABILITY_WINDOW_SECONDS,
    _sleep: Callable[[float], None] = time.sleep,
    _monotonic: Callable[[], float] = time.monotonic,
    _now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> dict[str, Any]:
    """Observe stability, then publish the canonical ledger with ``O_EXCL``."""

    root_relative, ledger_relative = _validate_namespace(
        materialization_root, output_path, require_ledger=False
    )
    _require(
        isinstance(stability_window_seconds, int)
        and stability_window_seconds >= _minimum_stability_seconds,
        f"stability window must be at least {_minimum_stability_seconds} seconds",
    )
    first_snapshot = _build_snapshot(root_relative, ledger_relative)
    first_sha256 = sha256_object(first_snapshot)
    started_at = _utc_text(_now())
    started_monotonic = _monotonic()
    sample_targets = list(
        range(0, stability_window_seconds + 1, STABILITY_SAMPLE_INTERVAL_SECONDS)
    )
    if sample_targets[-1] != stability_window_seconds:
        sample_targets.append(stability_window_seconds)
    _require(
        len(sample_targets) >= MINIMUM_STABILITY_SAMPLE_COUNT,
        "stability schedule must contain at least seven samples",
    )
    samples: list[dict[str, Any]] = []
    initial_probe_sha256: str | None = None
    for index, target_offset in enumerate(sample_targets):
        elapsed = _monotonic() - started_monotonic
        if elapsed < target_offset:
            _sleep(target_offset - elapsed)
        observed = _monotonic() - started_monotonic
        probe_sha256 = sha256_object(_shared_code_probe())
        if initial_probe_sha256 is None:
            initial_probe_sha256 = probe_sha256
        _require(
            probe_sha256 == initial_probe_sha256,
            "shared implementation/protocol graph changed during stability window",
        )
        samples.append(
            {
                "sample_index": index,
                "target_offset_seconds": target_offset,
                "observed_elapsed_seconds": round(observed, 6),
                "sampled_at": _utc_text(_now()),
                "shared_code_probe_sha256": probe_sha256,
            }
        )
    second_snapshot = _build_snapshot(root_relative, ledger_relative)
    ended_at = _utc_text(_now())
    observed_seconds = _monotonic() - started_monotonic
    second_sha256 = sha256_object(second_snapshot)
    _require(
        first_snapshot == second_snapshot,
        "refreeze dependency graph changed during stability window",
    )
    _require(
        first_sha256 == second_sha256,
        "refreeze snapshot hash changed during stability window",
    )
    _require(
        observed_seconds >= stability_window_seconds,
        "observed stability interval was shorter than requested",
    )

    payload = {
        "schema_version": LEDGER_SCHEMA,
        "status": "frozen_pre_canary",
        "frozen_at": ended_at,
        "materialization_root": root_relative.as_posix(),
        "ledger_path": ledger_relative.as_posix(),
        "stability_window": {
            "required_seconds": stability_window_seconds,
            "started_at": started_at,
            "ended_at": ended_at,
            "observed_seconds": round(observed_seconds, 6),
            "sample_interval_seconds": STABILITY_SAMPLE_INTERVAL_SECONDS,
            "samples": samples,
            "initial_snapshot_sha256": first_sha256,
            "final_snapshot_sha256": second_sha256,
            "unchanged": True,
        },
        "snapshot": second_snapshot,
        "snapshot_sha256": second_sha256,
    }
    _write_json_exclusive(_absolute(ledger_relative), payload)
    post_write_snapshot = _build_snapshot(root_relative, ledger_relative)
    _require(
        post_write_snapshot == second_snapshot,
        "dependency graph drifted during exclusive ledger publication; namespace is consumed",
    )
    return _freeze_result(payload, _absolute(ledger_relative), action="frozen")


def verify_appworld_definition_refreeze_v56(
    *,
    materialization_root: str | Path = DEFAULT_MATERIALIZATION_ROOT,
    ledger_path: str | Path | None = None,
) -> dict[str, Any]:
    """Recompute the complete graph and verify canonical ledger bytes."""

    root_relative, ledger_relative = _validate_namespace(
        materialization_root, ledger_path, require_ledger=True
    )
    ledger_file = _absolute(ledger_relative)
    payload = _load_mapping(ledger_file, "definition refreeze ledger")
    _require(
        ledger_file.read_bytes() == _json_bytes(payload),
        "definition refreeze ledger is not canonical JSON",
    )
    _validate_ledger_shape(payload, root_relative, ledger_relative)
    live_snapshot = _build_snapshot(root_relative, ledger_relative)
    live_sha256 = sha256_object(live_snapshot)
    _require(payload["snapshot"] == live_snapshot, "definition refreeze snapshot drift")
    _require(
        payload["snapshot_sha256"] == live_sha256,
        "definition refreeze snapshot hash drift",
    )
    window = _mapping(payload["stability_window"], "stability_window")
    _require(
        window["initial_snapshot_sha256"]
        == window["final_snapshot_sha256"]
        == live_sha256,
        "stability-window snapshot binding drift",
    )
    return _freeze_result(payload, ledger_file, action="verified")


def _build_snapshot(root_relative: Path, ledger_relative: Path) -> dict[str, Any]:
    root = _absolute(root_relative)
    manifest_path = root / "experiment_manifest.json"
    scope_path = root / "frozen_scope.json"
    acceptance_path = root / "provenance/acceptance_report.json"
    packet_root = root / "case_packets/appworld"
    source_bundle = root / "source_bundles/case_packet_source_bundle.json"
    manifest = _load_mapping(manifest_path, "extension manifest")
    scope = _load_mapping(scope_path, "extension scope")
    cases = _manifest_cases(manifest)
    materialization_tree = _validate_materialization_closure(
        root_relative=root_relative,
        ledger_relative=ledger_relative,
        case_ids=[case["case_unit_id"] for case in cases],
    )

    definition_audit = validate_extension_definition(output_root=root_relative)
    packet_acceptance_audit = validate_extension_packets(
        output_root=root_relative,
        case_packets_root=root_relative / "case_packets",
    )
    source_bundle_audit = validate_extension_source_bundle(
        output_root=root_relative,
        case_packets_root=root_relative / "case_packets",
        source_bundle_path=root_relative
        / "source_bundles/case_packet_source_bundle.json",
    )
    acceptance = _validate_packet_acceptance_report(
        acceptance_path=acceptance_path,
        scope_path=scope_path,
        manifest_path=manifest_path,
        catalog_path=root / "official_splits/appworld_selected_task_sources.json",
        definition_audit=definition_audit,
        packet_audit=packet_acceptance_audit,
        source_bundle_audit=source_bundle_audit,
    )
    packet_audit = _audit_packet_evaluator_composition(packet_root, cases)
    benchmark, appworld, scorer = _validate_scope_and_manifest(scope, manifest)
    drafter = _validate_draft_acceptance_binding(
        root_relative=root_relative,
        ledger_relative=ledger_relative,
        packet_audit=packet_audit,
        scope_path=scope_path,
        manifest_path=manifest_path,
        acceptance_path=acceptance_path,
    )
    drafter["legacy_scope_contract_drafter_authoritative"] = False
    drafter["legacy_scope_contract_drafter_semantic_sha256"] = sha256_object(
        _mapping(scope.get("contract_drafter"), "legacy scope contract drafter")
    )

    upstream_files = {
        key: _file_descriptor(path) for key, path in sorted(_UPSTREAM_FILES.items())
    }
    upstream_trees = {
        key: _tree_descriptor(path) for key, path in sorted(_UPSTREAM_TREES.items())
    }
    protocol_files = {
        key: _file_descriptor(path) for key, path in sorted(_PROTOCOL_FILES.items())
    }
    implementation_files = _implementation_descriptors()
    _require_descriptor_paths_unique(
        upstream_files, upstream_trees, protocol_files, implementation_files
    )
    graph = {
        "materialization_tree_sha256": materialization_tree["tree_sha256"],
        "upstream_files": upstream_files,
        "upstream_trees": upstream_trees,
        "protocol_files": protocol_files,
        "implementation_files": implementation_files,
    }
    snapshot: dict[str, Any] = {
        "schema_version": SNAPSHOT_SCHEMA,
        "scope": {
            "experiment_id": EXPERIMENT_ID,
            "completed_test_normal_case_count": 100,
            "extension_case_count": EXPECTED_EXTENSION_COUNT,
            "extension_case_count_by_dataset": {
                "test_normal": EXPECTED_NORMAL_EXTENSION_COUNT,
                "test_challenge": EXPECTED_CHALLENGE_COUNT,
            },
            "full_test_case_count": 585,
            "record_slot_count": 1_455,
            "case_ids_semantic_sha256": sha256_object(
                [case["case_unit_id"] for case in cases]
            ),
            "case_records_semantic_sha256": sha256_object(cases),
        },
        "appworld": appworld,
        "benchmark_agents": benchmark,
        "drafter": drafter,
        "scorer": scorer,
        "materialization": materialization_tree,
        "packet_audit": packet_audit,
        "packet_acceptance": acceptance,
        "source_bundle": {
            **source_bundle_audit,
            "path": _relative_existing_file(source_bundle).as_posix(),
        },
        "input_graph": graph,
    }
    snapshot["dependency_graph_sha256"] = sha256_object(graph)
    return snapshot


def _validate_materialization_closure(
    *, root_relative: Path, ledger_relative: Path, case_ids: Sequence[str]
) -> dict[str, Any]:
    expected_files = set(_MATERIALIZATION_FIXED_FILES)
    for case_id in case_ids:
        prefix = f"case_packets/appworld/{case_id}"
        expected_files.add(f"{prefix}/case_packet.md")
        expected_files.add(f"{prefix}/raw_case_manifest.json")
        expected_files.update(
            f"{prefix}/raw_case/official/{relative}" for relative in REQUIRED_TASK_FILES
        )
    expected_directories = {
        parent.as_posix()
        for value in expected_files
        for parent in Path(value).parents
        if parent != Path(".")
    }
    ledger_inside = ledger_relative.relative_to(root_relative).as_posix()
    entries = _tree_entries(root_relative, exclude_files={ledger_inside})
    actual_files = {entry["path"] for entry in entries if entry["type"] == "file"}
    actual_directories = {
        entry["path"] for entry in entries if entry["type"] == "directory"
    }
    _require(
        actual_files == expected_files,
        "materialization file closure mismatch: "
        f"missing={sorted(expected_files - actual_files)[:8]}, "
        f"extra={sorted(actual_files - expected_files)[:8]}",
    )
    _require(
        actual_directories == expected_directories,
        "materialization directory closure mismatch: "
        f"missing={sorted(expected_directories - actual_directories)[:8]}, "
        f"extra={sorted(actual_directories - expected_directories)[:8]}",
    )
    descriptor = _tree_descriptor(root_relative, exclude_files={ledger_inside})
    _require(
        descriptor["file_count"]
        == len(_MATERIALIZATION_FIXED_FILES)
        + EXPECTED_EXTENSION_COUNT * (2 + EXPECTED_FILES_PER_TASK),
        "materialization closure file count mismatch",
    )
    return descriptor


def _validate_packet_acceptance_report(
    *,
    acceptance_path: Path,
    scope_path: Path,
    manifest_path: Path,
    catalog_path: Path,
    definition_audit: Mapping[str, Any],
    packet_audit: Mapping[str, Any],
    source_bundle_audit: Mapping[str, Any],
) -> dict[str, Any]:
    report = _load_mapping(acceptance_path, "packet acceptance report")
    expected = {
        "schema_version": PACKET_ACCEPTANCE_SCHEMA,
        "status": "accepted",
        "experiment_id": EXPERIMENT_ID,
        "protected_data_notice": (
            "AppWorld protected source and derived packets must remain access-controlled "
            "or be redistributed only encrypted."
        ),
        "definition": dict(definition_audit),
        "packets": dict(packet_audit),
        "source_bundle": dict(source_bundle_audit),
        "artifact_hashes": {
            "catalog_sha256": sha256_file(catalog_path),
            "scope_lock_sha256": sha256_file(scope_path),
            "manifest_sha256": sha256_file(manifest_path),
        },
        "all_hard_gates_passed": True,
    }
    _require(report == expected, "packet acceptance report is stale or non-canonical")
    return {
        "path": _relative_existing_file(acceptance_path).as_posix(),
        "sha256": sha256_file(acceptance_path),
        "schema_version": report["schema_version"],
        "status": report["status"],
        "all_hard_gates_passed": True,
        "semantic_sha256": sha256_object(report),
    }


def _audit_packet_evaluator_composition(
    packet_root: Path, cases: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    lane_counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()
    registered_test_count = 0
    scoring_block_count = 0
    non_scoring_count = 0
    audit_hashes: dict[str, str] = {}
    size_index: list[dict[str, Any]] = []
    lane_sizes: dict[str, list[int]] = {"regular": [], "oversized": []}
    for case in cases:
        case_id = str(case["case_unit_id"])
        split = str(case["dataset_name"])
        case_root = packet_root / case_id
        audit = validate_appworld_packet_evaluator_semantics(case_packet_root=case_root)
        _require(
            audit.get("status") == "passed" and audit.get("case_id") == case_id,
            f"packet evaluator audit identity/status mismatch: {case_id}",
        )
        assignments = audit.get("non_scoring_test_assignments")
        _require(
            isinstance(assignments, list)
            and len(assignments) == 1
            and assignments[0].get("attribute") == "task_completed",
            f"packet evaluator non-scoring assignment mismatch: {case_id}",
        )
        registered_test_count += int(audit["test_data_requirement_count"])
        scoring_block_count += int(audit["scoring_block_count"])
        non_scoring_count += len(assignments)
        audit_hash = str(audit["audit_semantic_sha256"])
        _require(
            _SHA256_RE.fullmatch(audit_hash) is not None, "invalid packet audit hash"
        )
        audit_hashes[case_id] = audit_hash
        size = (case_root / "case_packet.md").stat().st_size
        lane = "oversized" if size > EXPECTED_LARGE_CASE_THRESHOLD_BYTES else "regular"
        lane_counts[lane] += 1
        split_counts[split] += 1
        lane_sizes[lane].append(size)
        size_index.append({"case_id": case_id, "size_bytes": size, "lane": lane})
    _require(
        dict(split_counts)
        == {
            "test_normal": EXPECTED_NORMAL_EXTENSION_COUNT,
            "test_challenge": EXPECTED_CHALLENGE_COUNT,
        },
        "packet evaluator audit split counts mismatch",
    )
    _require(
        registered_test_count == scoring_block_count == EXPECTED_REGISTERED_TEST_COUNT,
        "packet evaluator registered/scoring test totals mismatch",
    )
    _require(
        non_scoring_count == EXPECTED_NON_SCORING_TASK_COMPLETED_COUNT,
        "packet evaluator non-scoring task_completed total mismatch",
    )
    return {
        "schema_version": PACKET_AUDIT_SCHEMA,
        "status": "passed",
        "case_count": len(cases),
        "case_count_by_dataset": dict(sorted(split_counts.items())),
        "registered_test_count": registered_test_count,
        "scoring_block_count": scoring_block_count,
        "non_scoring_task_completed_assignment_count": non_scoring_count,
        "large_case_threshold_bytes": EXPECTED_LARGE_CASE_THRESHOLD_BYTES,
        "lane_counts": {
            key: lane_counts.get(key, 0) for key in ("regular", "oversized")
        },
        "lane_size_ranges": {
            key: {
                "min_bytes": min(values) if values else 0,
                "max_bytes": max(values) if values else 0,
            }
            for key, values in lane_sizes.items()
        },
        "case_packet_size_index_sha256": sha256_object(size_index),
        "audit_semantic_sha256_by_case": audit_hashes,
        "aggregate_semantic_sha256": sha256_object(audit_hashes),
    }


def _validate_scope_and_manifest(
    scope: Mapping[str, Any], manifest: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    scope_counts = _mapping(scope.get("scope"), "scope counts")
    _require(
        scope_counts.get("completed_case_count") == 100
        and scope_counts.get("extension_case_count") == EXPECTED_EXTENSION_COUNT
        and scope_counts.get("extension_case_count_by_dataset")
        == {
            "test_normal": EXPECTED_NORMAL_EXTENSION_COUNT,
            "test_challenge": EXPECTED_CHALLENGE_COUNT,
        }
        and scope_counts.get("extension_record_slot_count") == 1_455,
        "frozen scope counts mismatch",
    )
    appworld = dict(_mapping(scope.get("appworld"), "scope AppWorld provenance"))
    _require(
        appworld.get("git_commit") == APPWORLD_GIT_COMMIT
        and appworld.get("data_version") == APPWORLD_DATA_VERSION,
        "AppWorld commit/data version drift",
    )
    agents = manifest.get("agents")
    _require(
        isinstance(agents, list) and len(agents) == len(AGENT_IDS),
        "manifest agent count mismatch",
    )
    _require(
        [item.get("agent_id") for item in agents] == list(AGENT_IDS),
        "manifest agent order mismatch",
    )
    scope_agents = _mapping(scope.get("agents"), "scope agents")
    _require(
        scope_agents.get("agent_ids") == list(AGENT_IDS), "scope agent IDs mismatch"
    )
    config_path = _canonical_repo_relative(
        str(manifest.get("agents_config_path") or ""), require_exists=True
    )
    config_sha = str(manifest.get("agents_config_sha256") or "").removeprefix("sha256:")
    _require(
        config_sha == sha256_file(_absolute(config_path)), "agents config hash mismatch"
    )
    benchmark = {
        "agent_count": len(agents),
        "agent_ids": list(AGENT_IDS),
        "agents": agents,
        "agents_semantic_sha256": sha256_object(agents),
        "agents_config_path": config_path.as_posix(),
        "agents_config_sha256": config_sha,
    }
    scorer = dict(_mapping(scope.get("scorer"), "scope scorer"))
    _require(
        scorer.get("executor") == "codex"
        and scorer.get("model") == "gpt-5.4"
        and scorer.get("reasoning_effort") == "high",
        "scorer executor/model/reasoning drift",
    )
    for path_field, hash_field in (
        ("score_prompt_path", "score_prompt_sha256"),
        ("score_schema_path", "score_schema_sha256"),
    ):
        relative = _canonical_repo_relative(
            str(scorer.get(path_field) or ""), require_exists=True
        )
        _require(
            str(scorer.get(hash_field) or "").removeprefix("sha256:")
            == sha256_file(_absolute(relative)),
            f"scorer {hash_field} drift",
        )
    scorer["semantic_sha256"] = sha256_object(scorer)
    return benchmark, appworld, scorer


def _validate_draft_acceptance_binding(
    *,
    root_relative: Path,
    ledger_relative: Path,
    packet_audit: Mapping[str, Any],
    scope_path: Path,
    manifest_path: Path,
    acceptance_path: Path,
) -> dict[str, Any]:
    root = root_relative.as_posix()
    expected_inputs = {
        "manifest": f"{root}/experiment_manifest.json",
        "source_bundle": f"{root}/source_bundles/case_packet_source_bundle.json",
        "packet_acceptance_report": f"{root}/provenance/acceptance_report.json",
        "frozen_scope": f"{root}/frozen_scope.json",
        "source_catalog": f"{root}/official_splits/appworld_selected_task_sources.json",
        "all_extension_ids": f"{root}/official_splits/appworld_extension_all.txt",
        "normal_extension_ids": f"{root}/official_splits/appworld_test_normal_extension.txt",
        "challenge_ids": f"{root}/official_splits/appworld_test_challenge.txt",
        "definition_refreeze": ledger_relative.as_posix(),
        "stronger_gap_registry": (
            "experiments/appworld_full_test_extension_v1/official_splits/"
            "appworld_stronger_gap_registry.gpt56.v2.json"
        ),
        "stronger_gap_review_policy": (
            "experiments/appworld_full_test_extension_v1/official_splits/"
            "appworld_stronger_gap_review_policy.gpt56.v1.json"
        ),
        "stronger_gap_review_receipt": (
            "experiments/appworld_full_test_extension_v1/official_splits/"
            "appworld_stronger_gap_review_receipt.gpt56.v1.json"
        ),
    }
    actual_inputs = {
        key: _canonical_repo_relative(
            value, require_exists=(key != "definition_refreeze")
        ).as_posix()
        for key, value in draft_acceptance._INPUT_PATHS.items()
    }
    _require(
        actual_inputs == expected_inputs,
        "draft acceptance input paths do not target the new namespace",
    )
    packet_root = _canonical_repo_relative(
        draft_acceptance._PACKET_ROOT, require_exists=True
    )
    _require(
        packet_root.as_posix() == f"{root}/case_packets/appworld",
        "draft acceptance packet root drift",
    )
    draft_root = _canonical_repo_relative(
        draft_acceptance.DEFAULT_DRAFT_ROOT, require_exists=False
    )
    preflight_root = _canonical_repo_relative(
        draft_acceptance.DEFAULT_PREFLIGHT_ROOT, require_exists=False
    )
    _require(
        root_relative in draft_root.parents,
        "formal draft root is outside the new materialization namespace",
    )
    _require(
        root_relative in preflight_root.parents,
        "preflight root is outside the new materialization namespace",
    )
    _require(
        not _absolute(draft_root).exists(),
        "formal draft namespace must not exist at refreeze",
    )
    _require(
        not _absolute(preflight_root).exists(),
        "preflight namespace must not exist at refreeze",
    )
    _require(
        draft_acceptance.EXPECTED_EXPERIMENT_ID == EXPERIMENT_ID
        and draft_acceptance.EXPECTED_MODEL == "gpt-5.6-sol"
        and draft_acceptance.EXPECTED_REASONING_EFFORT == "xhigh"
        and draft_acceptance.EXPECTED_MODEL_VERBOSITY == "low"
        and draft_acceptance.EXPECTED_CODEX_SANDBOX == "danger-full-access"
        and draft_acceptance.EXPECTED_MAX_PARALLEL == 8
        and draft_acceptance.EXPECTED_LARGE_THRESHOLD_BYTES
        == EXPECTED_LARGE_CASE_THRESHOLD_BYTES,
        "draft runtime model/reasoning/sandbox/concurrency binding drift",
    )
    _require(
        tuple(draft_acceptance.EXPECTED_TOKEN_BUDGETS) == (12_000, 16_000, 20_000),
        "draft token budget binding drift",
    )
    _require(
        draft_acceptance.EXPECTED_LANE_COUNTS == packet_audit["lane_counts"],
        "draft acceptance lane counts differ from materialized packets",
    )
    _require(
        draft_acceptance.EXPECTED_REGISTERED_TEST_COUNT
        == packet_audit["registered_test_count"],
        "draft acceptance registered-test count drift",
    )
    _require(
        draft_acceptance.EXPECTED_FROZEN_SCOPE_SHA256 == sha256_file(scope_path)
        and draft_acceptance.EXPECTED_EXTENSION_MANIFEST_SHA256
        == sha256_file(manifest_path)
        and draft_acceptance.EXPECTED_PACKET_ACCEPTANCE_SHA256
        == sha256_file(acceptance_path),
        "draft acceptance materialization hash constants are stale",
    )
    return {
        "agent_role": "case_checklist_drafter",
        "executor": "codex_cli",
        "authentication": (
            "ChatGPT login required and reverified at canary and formal phase start"
        ),
        "provider": "codex",
        "run_id": draft_acceptance.EXPECTED_DRAFT_RUN_ID,
        "model": draft_acceptance.EXPECTED_MODEL,
        "reasoning_effort": draft_acceptance.EXPECTED_REASONING_EFFORT,
        "model_verbosity": draft_acceptance.EXPECTED_MODEL_VERBOSITY,
        "sandbox": draft_acceptance.EXPECTED_CODEX_SANDBOX,
        "regular_max_parallel": draft_acceptance.EXPECTED_MAX_PARALLEL,
        "oversized_max_parallel": draft_acceptance.EXPECTED_MAX_PARALLEL,
        "large_case_threshold_bytes": draft_acceptance.EXPECTED_LARGE_THRESHOLD_BYTES,
        "token_budgets": list(draft_acceptance.EXPECTED_TOKEN_BUDGETS),
        "draft_root": draft_root.as_posix(),
        "preflight_root": preflight_root.as_posix(),
        "environment_policy": draft_acceptance.ENVIRONMENT_POLICY,
        "event_command_policy": draft_acceptance.EVENT_COMMAND_POLICY,
        "retry_policy": "audited_allowlisted_codex_infrastructure_failures_only",
        "infra_retry_schema": draft_acceptance.INFRA_RETRY_SCHEMA,
    }


def _implementation_descriptors() -> dict[str, dict[str, Any]]:
    paths = dict(_MATERIALIZATION_CODE_FILES)
    for key, value in draft_acceptance._IMPLEMENTATION_PATHS.items():
        path = Path(value)
        if path.suffix == ".py":
            paths[f"draft_{key}"] = path
    by_path: dict[str, tuple[str, Path]] = {}
    for key, path in sorted(paths.items()):
        canonical = _canonical_repo_relative(path, require_exists=True)
        by_path.setdefault(canonical.as_posix(), (key, canonical))
    return {key: _file_descriptor(path) for _, (key, path) in sorted(by_path.items())}


def _shared_code_probe() -> dict[str, Any]:
    """Hash the change-prone shared code/protocol graph at ten-second cadence."""

    return {
        "protocol_files": {
            key: _file_descriptor(path) for key, path in sorted(_PROTOCOL_FILES.items())
        },
        "implementation_files": _implementation_descriptors(),
    }


def _manifest_cases(manifest: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    domains = manifest.get("domains")
    _require(
        isinstance(domains, list)
        and len(domains) == 1
        and isinstance(domains[0], Mapping),
        "extension manifest must contain exactly one domain",
    )
    domain = domains[0]
    cases = domain.get("case_units")
    _require(
        domain.get("domain") == "appworld"
        and isinstance(cases, list)
        and len(cases) == EXPECTED_EXTENSION_COUNT
        and all(isinstance(case, Mapping) for case in cases),
        "extension manifest case inventory mismatch",
    )
    ids = [str(case.get("case_unit_id") or "") for case in cases]
    _require(
        len(ids) == len(set(ids)), "extension manifest contains duplicate case IDs"
    )
    splits = Counter(str(case.get("dataset_name") or "") for case in cases)
    _require(
        dict(splits)
        == {
            "test_normal": EXPECTED_NORMAL_EXTENSION_COUNT,
            "test_challenge": EXPECTED_CHALLENGE_COUNT,
        },
        "extension manifest split inventory mismatch",
    )
    for case in cases:
        case_id = str(case["case_unit_id"])
        split = str(case["dataset_name"])
        _require(
            case.get("task_id") == case_id
            and case.get("split") == split
            and case.get("source_ref") == f"appworld://{split}/{case_id}",
            f"extension manifest identity mismatch: {case_id}",
        )
    return cases


def _validate_namespace(
    materialization_root: str | Path,
    output_path: str | Path | None,
    *,
    require_ledger: bool,
) -> tuple[Path, Path]:
    root_relative = _canonical_repo_relative(materialization_root, require_exists=True)
    _require(
        _absolute(root_relative).is_dir(), "materialization root must be a directory"
    )
    _require(
        root_relative != LEGACY_MATERIALIZATION_ROOT,
        "legacy materialization root cannot be refrozen",
    )
    _require(
        len(root_relative.parts) == 2
        and root_relative.parts[0] == "experiments"
        and _NEW_NAMESPACE_RE.fullmatch(root_relative.name) is not None,
        "materialization root must be a new experiments/...gpt56... namespace",
    )
    expected_ledger = root_relative / "provenance" / LEDGER_BASENAME
    ledger_relative = _canonical_repo_relative(
        output_path or expected_ledger,
        require_exists=require_ledger,
        allow_missing_leaf=not require_ledger,
    )
    _require(
        ledger_relative == expected_ledger,
        "refreeze ledger path is not canonical for the namespace",
    )
    if require_ledger:
        _require(_absolute(ledger_relative).is_file(), "refreeze ledger is missing")
    else:
        _require(
            not _absolute(ledger_relative).exists(),
            "refreeze ledger already exists; namespace cannot be reused",
        )
    return root_relative, ledger_relative


def _validate_ledger_shape(
    payload: Mapping[str, Any], root_relative: Path, ledger_relative: Path
) -> None:
    _require(
        set(payload)
        == {
            "schema_version",
            "status",
            "frozen_at",
            "materialization_root",
            "ledger_path",
            "stability_window",
            "snapshot",
            "snapshot_sha256",
        },
        "definition refreeze ledger field set mismatch",
    )
    _require(
        payload.get("schema_version") == LEDGER_SCHEMA
        and payload.get("status") == "frozen_pre_canary"
        and payload.get("materialization_root") == root_relative.as_posix()
        and payload.get("ledger_path") == ledger_relative.as_posix(),
        "definition refreeze ledger identity/status mismatch",
    )
    snapshot = _mapping(payload.get("snapshot"), "snapshot")
    snapshot_sha = str(payload.get("snapshot_sha256") or "")
    _require(
        _SHA256_RE.fullmatch(snapshot_sha) is not None
        and snapshot_sha == sha256_object(snapshot),
        "definition refreeze snapshot hash invalid",
    )
    window = _mapping(payload.get("stability_window"), "stability_window")
    _require(
        set(window)
        == {
            "required_seconds",
            "started_at",
            "ended_at",
            "observed_seconds",
            "sample_interval_seconds",
            "samples",
            "initial_snapshot_sha256",
            "final_snapshot_sha256",
            "unchanged",
        },
        "stability_window field set mismatch",
    )
    required = window.get("required_seconds")
    observed = window.get("observed_seconds")
    _require(
        isinstance(required, int)
        and required >= MINIMUM_STABILITY_WINDOW_SECONDS
        and isinstance(observed, (int, float))
        and not isinstance(observed, bool)
        and observed >= required
        and window.get("unchanged") is True,
        "stability_window duration/status invalid",
    )
    _require(
        window.get("sample_interval_seconds") == STABILITY_SAMPLE_INTERVAL_SECONDS,
        "stability_window sample interval drift",
    )
    started = _parse_utc(str(window.get("started_at") or ""))
    ended = _parse_utc(str(window.get("ended_at") or ""))
    _require(
        (ended - started).total_seconds() >= required,
        "stability_window wall-clock interval too short",
    )
    _parse_utc(str(payload.get("frozen_at") or ""))
    samples = window.get("samples")
    _require(
        isinstance(samples, list) and len(samples) >= MINIMUM_STABILITY_SAMPLE_COUNT,
        "stability_window requires at least seven samples",
    )
    input_graph = _mapping(snapshot.get("input_graph"), "snapshot input_graph")
    expected_probe_sha256 = sha256_object(
        {
            "protocol_files": input_graph.get("protocol_files"),
            "implementation_files": input_graph.get("implementation_files"),
        }
    )
    previous_target: int | None = None
    previous_sampled_at: datetime | None = None
    for index, raw_sample in enumerate(samples):
        sample = _mapping(raw_sample, f"stability sample {index}")
        _require(
            set(sample)
            == {
                "sample_index",
                "target_offset_seconds",
                "observed_elapsed_seconds",
                "sampled_at",
                "shared_code_probe_sha256",
            }
            and sample.get("sample_index") == index,
            f"stability sample {index} field set/index mismatch",
        )
        target = sample.get("target_offset_seconds")
        sample_observed = sample.get("observed_elapsed_seconds")
        _require(
            isinstance(target, int)
            and isinstance(sample_observed, (int, float))
            and not isinstance(sample_observed, bool)
            and sample_observed >= target
            and sample.get("shared_code_probe_sha256") == expected_probe_sha256,
            f"stability sample {index} offset/hash mismatch",
        )
        if previous_target is None:
            _require(target == 0, "first stability sample must target zero seconds")
        else:
            _require(
                0 < target - previous_target <= STABILITY_SAMPLE_INTERVAL_SECONDS,
                f"stability sample {index} cadence exceeds ten seconds",
            )
        sampled_at = _parse_utc(str(sample.get("sampled_at") or ""))
        _require(
            started <= sampled_at <= ended
            and (previous_sampled_at is None or sampled_at >= previous_sampled_at),
            f"stability sample {index} timestamp order mismatch",
        )
        previous_target = target
        previous_sampled_at = sampled_at
    _require(
        previous_target == required,
        "final stability sample must target the full window",
    )


def _file_descriptor(path: str | Path) -> dict[str, Any]:
    relative = _canonical_repo_relative(path, require_exists=True)
    absolute = _absolute(relative)
    _require(absolute.is_file(), f"expected file input: {relative}")
    return {
        "path": relative.as_posix(),
        "kind": "file",
        "sha256": sha256_file(absolute),
        "size_bytes": absolute.stat().st_size,
    }


def _tree_descriptor(
    path: str | Path, *, exclude_files: set[str] | frozenset[str] = frozenset()
) -> dict[str, Any]:
    relative = _canonical_repo_relative(path, require_exists=True)
    absolute = _absolute(relative)
    _require(absolute.is_dir(), f"expected tree input: {relative}")
    entries = _tree_entries(relative, exclude_files=set(exclude_files))
    file_entries = [entry for entry in entries if entry["type"] == "file"]
    directory_entries = [entry for entry in entries if entry["type"] == "directory"]
    return {
        "path": relative.as_posix(),
        "kind": "tree",
        "tree_sha256": sha256_object(entries),
        "inventory_sha256": sha256_object(
            [{"path": entry["path"], "type": entry["type"]} for entry in entries]
        ),
        "file_count": len(file_entries),
        "directory_count": len(directory_entries),
        "byte_count": sum(int(entry["size_bytes"]) for entry in file_entries),
    }


def _tree_entries(relative: Path, *, exclude_files: set[str]) -> list[dict[str, Any]]:
    absolute = _absolute(relative)
    entries: list[dict[str, Any]] = []
    for path in sorted(absolute.rglob("*")):
        item_relative = path.relative_to(absolute).as_posix()
        if path.is_symlink():
            raise ContractLifecycleError(
                f"tree contains symlink: {relative / item_relative}"
            )
        if path.is_dir():
            entries.append({"path": item_relative, "type": "directory"})
        elif path.is_file():
            if item_relative in exclude_files:
                continue
            entries.append(
                {
                    "path": item_relative,
                    "type": "file",
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
        else:
            raise ContractLifecycleError(
                f"tree contains non-file/non-directory entry: {path}"
            )
    if exclude_files:
        existing_files = {entry["path"] for entry in entries if entry["type"] == "file"}
        # The excluded file is absent from ``entries``; inspect only its exact
        # candidate instead of traversing large protected trees a second time.
        unknown_exclusions = {
            value
            for value in exclude_files
            if not (_absolute(relative) / value).is_file()
        }
        # A not-yet-created canonical ledger is the only accepted absent exclusion.
        unknown_exclusions.discard(f"provenance/{LEDGER_BASENAME}")
        _require(
            not unknown_exclusions,
            f"tree exclusions do not exist: {sorted(unknown_exclusions)}",
        )
        _require(
            not (exclude_files & existing_files),
            "excluded files unexpectedly remained in tree entries",
        )
    return entries


def _require_descriptor_paths_unique(*groups: Mapping[str, Mapping[str, Any]]) -> None:
    paths = [str(item["path"]) for group in groups for item in group.values()]
    _require(
        len(paths) == len(set(paths)), "refreeze input graph contains duplicate paths"
    )


def _canonical_repo_relative(
    value: str | Path,
    *,
    require_exists: bool,
    allow_missing_leaf: bool = False,
) -> Path:
    raw = str(value)
    _require(
        raw and "\\" not in raw and not raw.startswith("/"),
        f"path must be canonical repo-relative: {raw}",
    )
    _require("//" not in raw, f"path contains an empty component: {raw}")
    candidate = Path(raw)
    _require(
        not candidate.is_absolute()
        and all(part not in {"", ".", ".."} for part in candidate.parts)
        and candidate.as_posix() == raw,
        f"path is not canonical repo-relative: {raw}",
    )
    absolute = _absolute(candidate)
    current = repo_root()
    for index, part in enumerate(candidate.parts):
        current = current / part
        if current.exists() or current.is_symlink():
            _require(
                not current.is_symlink(), f"path component is a symlink: {candidate}"
            )
        elif not (allow_missing_leaf and index == len(candidate.parts) - 1):
            _require(not require_exists, f"path does not exist: {candidate}")
            break
    if require_exists:
        _require(absolute.exists(), f"path does not exist: {candidate}")
    return candidate


def _relative_existing_file(path: Path) -> Path:
    try:
        relative = path.relative_to(repo_root())
    except ValueError as exc:
        raise ContractLifecycleError(f"path is outside repository: {path}") from exc
    return _canonical_repo_relative(relative, require_exists=True)


def _absolute(relative: Path) -> Path:
    return repo_root() / relative


def _write_json_exclusive(path: Path, payload: Mapping[str, Any]) -> None:
    data = _json_bytes(payload)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    except FileExistsError as exc:
        raise ContractLifecycleError(
            f"refusing to overwrite immutable refreeze ledger: {path}"
        ) from exc
    try:
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short write while publishing refreeze ledger")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    ).encode("utf-8")


def _load_mapping(path: Path, label: str) -> dict[str, Any]:
    _require(
        path.is_file() and not path.is_symlink(),
        f"{label} is missing or symlinked: {path}",
    )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractLifecycleError(f"invalid {label}: {path}: {exc}") from exc
    _require(isinstance(payload, Mapping), f"{label} must be a JSON object")
    return dict(payload)


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), f"{label} must be a mapping")
    return value


def _utc_text(value: datetime) -> str:
    _require(value.tzinfo is not None, "freeze clock must be timezone-aware")
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _parse_utc(value: str) -> datetime:
    _require(value.endswith("Z"), f"timestamp must use UTC Z form: {value}")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ContractLifecycleError(f"invalid UTC timestamp: {value}") from exc
    _require(parsed.tzinfo is not None, f"timestamp lacks timezone: {value}")
    return parsed.astimezone(timezone.utc)


def _freeze_result(
    payload: Mapping[str, Any], ledger_file: Path, *, action: str
) -> dict[str, Any]:
    snapshot = _mapping(payload["snapshot"], "snapshot")
    return {
        "action": action,
        "status": "ok",
        "ledger_path": str(ledger_file.relative_to(repo_root())),
        "ledger_sha256": sha256_file(ledger_file),
        "snapshot_sha256": payload["snapshot_sha256"],
        "case_count": snapshot["scope"]["extension_case_count"],
        "case_count_by_dataset": snapshot["scope"]["extension_case_count_by_dataset"],
        "lane_counts": snapshot["packet_audit"]["lane_counts"],
        "registered_test_count": snapshot["packet_audit"]["registered_test_count"],
    }


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ContractLifecycleError(message)
