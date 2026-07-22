"""Build and verify the isolated AgentDojo v1.2.2 full-coverage experiment."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from evidence_system.contracts.case_packets import (
    load_selected_case_units,
    validate_case_packet_source,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.contracts.agentdojo_packet_extraction import (
    SHARED_SOURCE_BUNDLE_DIRECTORY,
    validate_official_source_bundle,
)
from evidence_system.core.hashing import sha256_file, sha256_object, sha256_path
from evidence_system.core.paths import repo_root, resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml, validate_object


EXPERIMENT_ROOT = Path("experiments/agentdojo_full_v1.2.2_direct")
RESULT_NAMESPACE = "agentdojo_full_v1.2.2_direct"
AGENTDOJO_PACKAGE_VERSION = "0.1.35"
AGENTDOJO_TAG = "v0.1.35"
AGENTDOJO_COMMIT = "a75aba7631d3ca5fb7ab938965c97ead2f9ff84b"
AGENTDOJO_TREE = "3c74b60f2bad4ff321d864e0c0483f256cc8f8d2"
AGENTDOJO_WHEEL = "agentdojo-0.1.35-py3-none-any.whl"
AGENTDOJO_WHEEL_SHA256 = (
    "364bea4219716b716bf639f504d195943f7f6a5535d312ca41d7098704a2affd"
)
BENCHMARK_VERSION = "v1.2.2"
ATTACK = "direct"
DEFENSE: None = None
TOOL_DELIMITER = "tool"
TOOL_OUTPUT_FORMAT = "yaml"
SYSTEM_MESSAGE_NAME: None = None
SYSTEM_MESSAGE_SHA256 = (
    "a021a92b114c523250d0e52b18adc0aa7b41db7c7628b579b2b8db1df9361837"
)
EXPECTED_CASE_COUNT = 949
EXPECTED_AGENTS = ("Agent A", "Agent B", "Agent C")
EXPECTED_RECORD_SLOT_COUNT = EXPECTED_CASE_COUNT * len(EXPECTED_AGENTS)
EXPECTED_SUITE_COUNTS = {
    "banking": 144,
    "slack": 105,
    "travel": 140,
    "workspace": 560,
}
CASE_ID_RE = re.compile(
    r"^v1\.2\.2:(workspace|travel|banking|slack):user_task_\d+:injection_task_\d+$"
)
ZERO_SHA256 = "0" * 64

DEFAULT_CANDIDATES = Path(
    "experiments/official_splits/agentdojo_v1.2.2_paired_candidates.json"
)
DEFAULT_CATALOG = (
    EXPERIMENT_ROOT / "official_splits/agentdojo_selected_task_sources.json"
)
DEFAULT_MANIFEST = EXPERIMENT_ROOT / "experiment_manifest.yaml"
DEFAULT_CASE_PACKETS = EXPERIMENT_ROOT / "case_packets"
DEFAULT_SOURCE_BUNDLE = (
    EXPERIMENT_ROOT / "source_bundles/case_packet_source_bundle.json"
)
DEFAULT_OFFICIAL_SOURCE_BUNDLE = (
    EXPERIMENT_ROOT / "source_bundles" / SHARED_SOURCE_BUNDLE_DIRECTORY
)
DEFAULT_JOBS_ROOT = EXPERIMENT_ROOT / "jobs/full"
DEFAULT_LOCK = EXPERIMENT_ROOT / "lock/experiment_lock.json"
DEFAULT_ACCEPTANCE = EXPERIMENT_ROOT / "provenance/acceptance_report.json"
DEFAULT_RESULT_NAMESPACE_LOCK = (
    Path("results/namespaces") / RESULT_NAMESPACE / "NAMESPACE_LOCK.json"
)
DEFAULT_DRAFT_ROOT = EXPERIMENT_ROOT / "drafts/agentdojo"
DEFAULT_DRAFT_REVIEW_CONFIG = EXPERIMENT_ROOT / "lock/draft_review_config.json"
DEFAULT_DRAFT_INPUT_LOCK = EXPERIMENT_ROOT / "lock/draft_input_lock.json"
DEFAULT_DRAFT_BUDGET_PLAN = EXPERIMENT_ROOT / "provenance/draft_budget_plan.json"
DEFAULT_DRAFT_REVIEW_REPORT = EXPERIMENT_ROOT / "provenance/draft_review_report.json"
DEFAULT_DRAFT_REVIEW_INDEX = EXPERIMENT_ROOT / "lock/draft_review_index.json"
DEFAULT_CASE_CHECKLIST_LOCK = EXPERIMENT_ROOT / "lock/case_checklist_locks.jsonl"
DEFAULT_CASE_CHECKLIST_LOCK_ACCEPTANCE = (
    EXPERIMENT_ROOT / "provenance/case_checklist_lock_acceptance.json"
)
DEFAULT_SCORE_PROMPT = Path(
    "neurips_ed_track_minimal/prompts/score_evidence_with_codex.prompt.md"
)
DEFAULT_SCORE_SCHEMA = Path(
    "neurips_ed_track_minimal/schemas/evidence_score.schema.json"
)
DEFAULT_SCORE_NAMESPACE_ROOTS = (
    Path("results/scores/namespaces") / RESULT_NAMESPACE,
    Path("results/scores_openrouter/namespaces") / RESULT_NAMESPACE,
)
DEFAULT_AGENTS_CONFIG = Path("configs/agents.yaml")
DEFAULT_INFRA_CONFIG = Path("configs/infra.yaml")

LOCKED_RUNTIME_PATHS = (
    "src/evidence_system/adapters/agentdojo.py",
    "src/evidence_system/adapters/agentdojo_worker.py",
    "src/evidence_system/adapters/runtime.py",
    "src/evidence_system/orchestrator/jobs.py",
    "src/evidence_system/contracts/agentdojo_full_catalog.py",
    "src/evidence_system/contracts/agentdojo_full_experiment.py",
    "src/evidence_system/contracts/agentdojo_packet_extraction.py",
    "src/evidence_system/contracts/case_packets.py",
    "src/evidence_system/core/hashing.py",
    "src/evidence_system/core/paths.py",
    "src/evidence_system/core/schemas.py",
    "schemas/experiment_manifest.schema.json",
    "src/evidence_system/cli/build_agentdojo_full_catalog.py",
    "src/evidence_system/cli/build_case_packets.py",
    "src/evidence_system/cli/build_case_packet_source_bundle.py",
    "src/evidence_system/cli/prepare_agentdojo_full_experiment.py",
    "src/evidence_system/cli/freeze_agentdojo_full_checklists.py",
    "src/evidence_system/cli/verify_agentdojo_full_experiment.py",
    "src/evidence_system/cli/run_full.py",
    "neurips_ed_track_minimal/checklist_guardrails.py",
    "neurips_ed_track_minimal/scripts/case_checklist_review.py",
    "neurips_ed_track_minimal/scripts/checklist_validator.py",
    "neurips_ed_track_minimal/scripts/draft_case_checklist.py",
    "neurips_ed_track_minimal/scripts/review_case_checklist_with_codex.py",
    "neurips_ed_track_minimal/scripts/run_agentdojo_full_draft_review.py",
    "neurips_ed_track_minimal/scripts/run_draft_batch.py",
    "neurips_ed_track_minimal/scripts/run_agentdojo_score_batch.py",
    "neurips_ed_track_minimal/scripts/score_evidence_with_codex.py",
    "neurips_ed_track_minimal/scripts/update_case_locks.py",
    "neurips_ed_track_minimal/scripts/update_case_locks_batch.py",
    "neurips_ed_track_minimal/scripts/export_agentdojo_scores_csv.py",
)

CHECKLIST_FREEZE_SCHEMA_VERSION = "agentdojo_full_checklist_freeze/v1"
CHECKLIST_FREEZE_LOCK_SCHEMA_VERSION = "agentdojo_full_experiment_lock/v2"
CHECKLIST_LOCK_ACCEPTANCE_SCHEMA_VERSION = "agentdojo_case_checklist_lock_acceptance/v1"


@dataclass(frozen=True)
class ChecklistFreezeResult:
    """Published checklist-freeze lock and its deterministic snapshot."""

    lock_path: Path
    lock_sha256: str
    replaced: bool
    snapshot: dict[str, Any]


def build_full_manifest(
    *,
    catalog_path: str | Path = DEFAULT_CATALOG,
    source_bundle_path: str | Path = DEFAULT_SOURCE_BUNDLE,
    output_path: str | Path = DEFAULT_MANIFEST,
    agents_config_path: str | Path = DEFAULT_AGENTS_CONFIG,
    infra_config_path: str | Path = DEFAULT_INFRA_CONFIG,
    created_at: str | None = None,
) -> Path:
    """Build the standalone 949-case appendix manifest.

    The manifest may be built before the source bundle exists so case packets
    have a manifest input. In that preparatory state ``source_bundle_hash`` is
    all zeroes. The verifier rejects that state; rerun this function after the
    bundle is created to finalize the hash closure.
    """

    catalog_file = resolve_repo_path(catalog_path)
    agents_file = resolve_repo_path(agents_config_path)
    infra_file = resolve_repo_path(infra_config_path)
    output_file = resolve_repo_path(output_path)
    source_bundle_file = resolve_repo_path(source_bundle_path)

    catalog, case_refs = _load_catalog(catalog_file)
    _validate_case_refs(case_refs, label="catalog")
    agents_config = _load_mapping(agents_file, "agents config")
    infra_config = _load_mapping(infra_file, "infra config")
    agent_entries = _manifest_agent_entries(agents_config)
    _agentdojo_infra_snapshot(infra_config)

    if created_at is None and output_file.exists():
        existing = load_json_or_yaml(output_file)
        if isinstance(existing, Mapping) and isinstance(
            existing.get("created_at"), str
        ):
            created_at = str(existing["created_at"])
    created_at = (
        created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    )

    case_units = [
        {
            "case_unit_id": row["case_unit_id"],
            "task_id": row["task_id"],
            "contract_lock_status": "draft_required",
        }
        for row in case_refs
    ]
    case_ids = [row["case_unit_id"] for row in case_refs]
    slot_ids = _planned_record_slot_ids(case_ids)
    source_bundle_hash = (
        sha256_file(source_bundle_file) if source_bundle_file.exists() else ZERO_SHA256
    )
    payload: dict[str, Any] = {
        "schema_version": "experiment_manifest/v1",
        "manifest_id": "agentdojo_full_v1.2.2_direct_manifest",
        "manifest_version": "1.0.0-prelock",
        "created_at": created_at,
        "status": "draft",
        "result_namespace": RESULT_NAMESPACE,
        "experiment_lock_path": _repo_relative(resolve_repo_path(DEFAULT_LOCK)),
        "paper_mapping_path": "experiments/paper_mapping.md",
        "paper_mapping_sha256": sha256_file(
            resolve_repo_path("experiments/paper_mapping.md")
        ),
        "source_bundle_hash": source_bundle_hash,
        "agents_config_hash": sha256_file(agents_file),
        "infra_config_hash": sha256_file(infra_file),
        "deterministic_selection": {
            "hash_function": "sha256",
            "hash_salt_hash": sha256_object("agentdojo-full-v1.2.2-direct-v1"),
            "eligible_case_unit_set_hash": sha256_object(sorted(case_ids)),
            "excluded_smoke_case_units": [],
            "smoke_exclusion_hash": sha256_object([]),
            "case_selection_order_hash": sha256_object(case_refs),
            "bootstrap_seed": 123,
            "bootstrap_resample_count": 1000,
            "audit_sample_seed": 456,
            "rerun_subset_selection_rule": "predeclared catalog order over all 949 AgentDojo v1.2.2 direct-attack case units",
        },
        "domains": [
            {
                "domain": "agentdojo",
                "domain_display_name": "AgentDojo",
                "experiment_type": "appendix",
                "priority": "P1",
                "case_unit_target": EXPECTED_CASE_COUNT,
                "case_unit_count": EXPECTED_CASE_COUNT,
                "record_slot_count": EXPECTED_RECORD_SLOT_COUNT,
                "planned_record_slot_ids_hash": sha256_object(slot_ids),
                "official_split_eligible_case_units": EXPECTED_CASE_COUNT,
                "official_split_hash": sha256_file(catalog_file),
                "official_split_exception_id": None,
                "contract_lock_status": "draft_required",
                "claim_scope": "native_aligned",
                "stronger_measurement_mapping": None,
                "case_units": case_units,
            }
        ],
        "agents": agent_entries,
        "official_split_exceptions": [],
        "declared_appendix_diagnostics": [],
        "required_paper_labels": [],
        "contract_locks": [],
    }
    report = validate_object("experiment_manifest", payload, raise_on_error=False)
    if not report.ok:
        raise ContractLifecycleError(
            f"generated manifest failed schema validation: {report.to_dict()}"
        )
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=120),
        encoding="utf-8",
    )
    return output_file


def _build_experiment_definition(
    *,
    candidates_path: str | Path,
    catalog_path: str | Path,
    manifest_path: str | Path,
    source_bundle_path: str | Path,
    case_packets_root: str | Path,
    agents_config_path: str | Path,
    infra_config_path: str | Path,
) -> dict[str, Any]:
    """Recompute the execution definition from current authoritative files."""

    candidates_file = resolve_repo_path(candidates_path)
    catalog_file = resolve_repo_path(catalog_path)
    agents_file = resolve_repo_path(agents_config_path)
    infra_file = resolve_repo_path(infra_config_path)
    _candidates, candidate_refs = _load_candidates(candidates_file)
    catalog, catalog_refs = _load_catalog(catalog_file)
    _validate_case_refs(candidate_refs, label="paired candidates")
    _validate_case_refs(catalog_refs, label="catalog")
    if candidate_refs != catalog_refs:
        raise ContractLifecycleError(
            "catalog ID/task order differs from paired candidates"
        )

    agents_config = _load_mapping(agents_file, "agents config")
    infra_config = _load_mapping(infra_file, "infra config")
    model_snapshot = _model_snapshot(agents_config)
    missing_runtime_paths = [
        path for path in LOCKED_RUNTIME_PATHS if not resolve_repo_path(path).is_file()
    ]
    if missing_runtime_paths:
        raise ContractLifecycleError(
            f"required locked runtime files are missing: {missing_runtime_paths}"
        )
    runtime_hashes = {
        path: sha256_file(resolve_repo_path(path)) for path in LOCKED_RUNTIME_PATHS
    }
    legacy_paths = (
        "results/full/agentdojo",
        "experiments/case_packets/agentdojo",
        "experiments/official_splits/agentdojo_selected_task_sources.json",
        "neurips_ed_track_minimal/locks/cases.jsonl",
    )
    legacy_snapshot = {
        path: sha256_path(resolve_repo_path(path))
        for path in legacy_paths
        if resolve_repo_path(path).exists()
    }
    catalog_provenance = dict(catalog.get("provenance") or {})
    official_source_bundle = validate_official_source_bundle(
        DEFAULT_OFFICIAL_SOURCE_BUNDLE
    )
    return {
        "result_namespace": RESULT_NAMESPACE,
        "benchmark": {
            "package_name": "agentdojo",
            "package_version": AGENTDOJO_PACKAGE_VERSION,
            "distribution_filename": AGENTDOJO_WHEEL,
            "distribution_sha256": AGENTDOJO_WHEEL_SHA256,
            "pypi_project": f"https://pypi.org/project/agentdojo/{AGENTDOJO_PACKAGE_VERSION}/",
            "source_repository": "https://github.com/ethz-spylab/agentdojo",
            "official_tag": AGENTDOJO_TAG,
            "git_commit": AGENTDOJO_COMMIT,
            "git_tree": AGENTDOJO_TREE,
            "benchmark_version": BENCHMARK_VERSION,
            "dependency_extra": "agentdojo-full",
            "dependency_spec_path": "pyproject.toml",
            "dependency_spec_sha256": sha256_file(resolve_repo_path("pyproject.toml")),
            "dependency_lock_path": "uv.lock",
            "dependency_lock_sha256": sha256_file(resolve_repo_path("uv.lock")),
        },
        "execution": {
            "attack": ATTACK,
            "defense": DEFENSE,
            "pipeline_llm": "LOCAL",
            "provider_route": "OpenRouter through local OpenAI-compatible proxy",
            "tool_delimiter": TOOL_DELIMITER,
            "tool_output_format": TOOL_OUTPUT_FORMAT,
            "system_message_name": SYSTEM_MESSAGE_NAME,
            "system_message_sha256": SYSTEM_MESSAGE_SHA256,
            "phase": "full",
            "experiment_type": "appendix",
            "case_unit_target": EXPECTED_CASE_COUNT,
            "score_slot_count": len(EXPECTED_AGENTS),
            "score_tasks_per_slot": EXPECTED_CASE_COUNT,
            "force_rerun": True,
            "paired_arms": ["benign", "injected"],
            "auxiliary_trajectory": "injection_task_as_user_task",
        },
        "models": {
            "agents_config_path": _repo_relative(agents_file),
            "agents_config_sha256": sha256_file(agents_file),
            "ordered_agent_ids": list(EXPECTED_AGENTS),
            "agent_configs": model_snapshot,
        },
        "infrastructure": {
            "infra_config_path": _repo_relative(infra_file),
            "infra_config_sha256": sha256_file(infra_file),
            "agentdojo_target": _agentdojo_infra_snapshot(infra_config),
        },
        "catalog": {
            "paired_candidates_path": _repo_relative(candidates_file),
            "paired_candidates_sha256": sha256_file(candidates_file),
            "source_metadata_path": _repo_relative(catalog_file),
            "source_metadata_sha256": sha256_file(catalog_file),
            "case_count": EXPECTED_CASE_COUNT,
            "case_id_order_sha256": sha256_object(
                [row["case_unit_id"] for row in candidate_refs]
            ),
            "case_id_set_sha256": sha256_object(
                sorted(row["case_unit_id"] for row in candidate_refs)
            ),
            "suite_case_counts": dict(EXPECTED_SUITE_COUNTS),
            "source_metadata_provenance": catalog_provenance,
        },
        "artifacts": {
            "manifest_path": _repo_relative(resolve_repo_path(manifest_path)),
            "manifest_sha256": sha256_file(resolve_repo_path(manifest_path)),
            "case_packets_root": _repo_relative(resolve_repo_path(case_packets_root)),
            "case_packets_tree_sha256": sha256_path(
                resolve_repo_path(case_packets_root)
            ),
            "source_bundle_path": _repo_relative(resolve_repo_path(source_bundle_path)),
            "source_bundle_sha256": sha256_file(resolve_repo_path(source_bundle_path)),
            "official_source_bundle_path": _repo_relative(
                resolve_repo_path(DEFAULT_OFFICIAL_SOURCE_BUNDLE)
            ),
            "official_source_manifest_path": str(
                official_source_bundle["manifest_path"]
            ),
            "official_source_manifest_sha256": str(
                official_source_bundle["manifest_sha256"]
            ),
            "official_source_tree_sha256": str(
                official_source_bundle["source_tree_sha256"]
            ),
            "official_source_file_count": int(official_source_bundle["file_count"]),
            "jobs_root": _repo_relative(resolve_repo_path(DEFAULT_JOBS_ROOT)),
            "result_namespace_lock_path": _repo_relative(
                resolve_repo_path(DEFAULT_RESULT_NAMESPACE_LOCK)
            ),
            "expected_case_packets": EXPECTED_CASE_COUNT,
            "expected_source_bundle_entries": EXPECTED_CASE_COUNT,
            "expected_record_slots": EXPECTED_RECORD_SLOT_COUNT,
            "expected_scores_per_case": len(EXPECTED_AGENTS),
        },
        "runtime_code_sha256": runtime_hashes,
        "legacy_artifact_snapshot_sha256": legacy_snapshot,
    }


def build_experiment_lock(
    *,
    candidates_path: str | Path = DEFAULT_CANDIDATES,
    catalog_path: str | Path = DEFAULT_CATALOG,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    source_bundle_path: str | Path = DEFAULT_SOURCE_BUNDLE,
    case_packets_root: str | Path = DEFAULT_CASE_PACKETS,
    output_path: str | Path = DEFAULT_LOCK,
    agents_config_path: str | Path = DEFAULT_AGENTS_CONFIG,
    infra_config_path: str | Path = DEFAULT_INFRA_CONFIG,
    locked_at: str | None = None,
    replace_existing_lock_sha256: str | None = None,
) -> Path:
    """Write the immutable definition lock, with digest-gated protocol revision."""

    output_file = resolve_repo_path(output_path)
    output_existing = load_json_or_yaml(output_file) if output_file.exists() else None
    if locked_at is None and isinstance(output_existing, Mapping):
        locked_at = str(output_existing.get("locked_at") or "") or None
    locked_at = (
        locked_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    )
    definition = _build_experiment_definition(
        candidates_path=candidates_path,
        catalog_path=catalog_path,
        manifest_path=manifest_path,
        source_bundle_path=source_bundle_path,
        case_packets_root=case_packets_root,
        agents_config_path=agents_config_path,
        infra_config_path=infra_config_path,
    )
    payload = {
        "schema_version": "agentdojo_full_experiment_lock/v1",
        "lock_id": "agentdojo_full_v1.2.2_direct",
        "lock_status": "locked",
        "locked_at": locked_at,
        **definition,
        "definition_sha256": sha256_object(definition),
    }
    if isinstance(output_existing, Mapping):
        previous = dict(output_existing)
        if previous != payload:
            if replace_existing_lock_sha256 is None:
                raise ContractLifecycleError(
                    "experiment lock already exists and differs; provide the exact existing "
                    "lock SHA-256 only for an explicit protocol revision"
                )
            expected_existing_sha256 = replace_existing_lock_sha256.removeprefix(
                "sha256:"
            )
            actual_existing_sha256 = sha256_file(output_file)
            if expected_existing_sha256 != actual_existing_sha256:
                raise ContractLifecycleError(
                    "experiment lock protocol-revision digest mismatch: "
                    f"expected_existing={expected_existing_sha256}, "
                    f"actual_existing={actual_existing_sha256}"
                )
            _atomic_write_json(output_file, payload)
        return output_file
    _atomic_write_json(output_file, payload)
    return output_file


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Durably replace one JSON file without exposing a partial lock."""

    if path.is_symlink():
        raise ContractLifecycleError(
            f"refusing to replace symlinked lock output: {path}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (
        json.dumps(dict(payload), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    staged: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as handle:
            staged = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(staged, path)
        staged = None
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError as exc:
        raise ContractLifecycleError(
            f"failed to atomically publish {path}: {exc}"
        ) from exc
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


def _require_regular_file(path: str | Path, label: str) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_symlink():
        raise ContractLifecycleError(f"{label} must not be a symlink: {candidate}")
    resolved = candidate.resolve()
    if not resolved.is_file():
        raise ContractLifecycleError(
            f"{label} is missing or not a regular file: {candidate}"
        )
    return resolved


def _require_regular_directory(path: str | Path, label: str) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_symlink():
        raise ContractLifecycleError(f"{label} must not be a symlink: {candidate}")
    resolved = candidate.resolve()
    if not resolved.is_dir():
        raise ContractLifecycleError(
            f"{label} is missing or not a directory: {candidate}"
        )
    return resolved


def _reject_tree_symlinks(root: Path, label: str) -> None:
    symlinks = [path for path in root.rglob("*") if path.is_symlink()]
    if symlinks:
        raise ContractLifecycleError(f"{label} contains symlinks: {symlinks[:3]}")


def _resolve_declared_artifact_path(value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ContractLifecycleError(f"{field} must be a non-empty path string")
    path = Path(value).expanduser()
    return (path if path.is_absolute() else repo_root() / path).resolve()


def _require_file_binding(
    mapping: Mapping[str, Any],
    *,
    path_field: str,
    hash_field: str,
    expected_path: Path,
    context: str,
) -> None:
    declared = _resolve_declared_artifact_path(
        mapping.get(path_field), f"{context}.{path_field}"
    )
    expected = _require_regular_file(expected_path, f"{context} input")
    if declared != expected:
        raise ContractLifecycleError(
            f"{context}.{path_field} is non-canonical: expected={expected}, actual={declared}"
        )
    actual_hash = sha256_file(expected)
    if mapping.get(hash_field) != actual_hash:
        raise ContractLifecycleError(
            f"{context}.{hash_field} is stale: expected={actual_hash}, "
            f"actual={mapping.get(hash_field)!r}"
        )


def _validate_path_lock(value: Any, label: str) -> Path:
    if not isinstance(value, Mapping):
        raise ContractLifecycleError(f"{label} must be a path/hash mapping")
    path = _resolve_declared_artifact_path(value.get("path"), f"{label}.path")
    path = _require_regular_file(path, label)
    if value.get("sha256") != sha256_file(path):
        raise ContractLifecycleError(f"{label}.sha256 is stale")
    return path


def _load_jsonl_mappings(path: Path, label: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            raise ContractLifecycleError(
                f"{label} contains a blank line at {line_number}"
            )
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ContractLifecycleError(
                f"{label} contains invalid JSON at line {line_number}: {exc}"
            ) from exc
        if not isinstance(value, Mapping):
            raise ContractLifecycleError(f"{label} line {line_number} is not an object")
        entries.append(dict(value))
    return entries


def _format_schema_errors(errors: Sequence[Any]) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in errors
    )


def _assert_exact(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ContractLifecycleError(
            f"{label} differs: expected={expected!r}, actual={actual!r}"
        )


def _require_aware_timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractLifecycleError(f"{label} must be a non-empty timestamp")
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ContractLifecycleError(
            f"{label} is not an ISO-8601 timestamp: {value!r}"
        ) from exc
    if parsed.tzinfo is None:
        raise ContractLifecycleError(f"{label} must include a timezone: {value!r}")
    return value.strip()


def _empty_output_snapshot(
    root: str | Path,
    *,
    label: str,
    allowed_files: Sequence[str] = (),
) -> dict[str, Any]:
    """Reject formal output before freeze while allowing declared namespace markers."""

    candidate = Path(root).expanduser()
    display = _repo_relative(candidate.resolve())
    if candidate.is_symlink():
        raise ContractLifecycleError(f"{label} must not be a symlink: {candidate}")
    if not candidate.exists():
        return {
            "path": display,
            "exists": False,
            "allowed_marker_hashes": {},
            "formal_output_file_count": 0,
        }
    resolved = _require_regular_directory(candidate, label)
    symlinks = [path for path in resolved.rglob("*") if path.is_symlink()]
    if symlinks:
        raise ContractLifecycleError(f"{label} contains symlinks: {symlinks[:3]}")
    relative_files = {
        path.relative_to(resolved).as_posix(): path
        for path in resolved.rglob("*")
        if path.is_file()
    }
    allowed = set(allowed_files)
    unexpected = sorted(set(relative_files) - allowed)
    missing_allowed = sorted(name for name in allowed if name not in relative_files)
    if unexpected:
        raise ContractLifecycleError(
            f"{label} is not empty before freeze; unexpected files={unexpected[:10]}"
        )
    if missing_allowed:
        raise ContractLifecycleError(
            f"{label} is missing required namespace marker files={missing_allowed}"
        )
    return {
        "path": _repo_relative(resolved),
        "exists": True,
        "allowed_marker_hashes": {
            name: sha256_file(relative_files[name]) for name in sorted(allowed)
        },
        "formal_output_file_count": 0,
    }


def _parse_aware_timestamp(value: Any, label: str) -> datetime:
    normalized = _require_aware_timestamp(value, label).replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _deduplicated_resolved_paths(paths: Sequence[str | Path]) -> tuple[Path, ...]:
    result: list[Path] = []
    seen: set[Path] = set()
    for value in paths:
        candidate = Path(value).expanduser()
        path = (
            candidate if candidate.is_absolute() else repo_root() / candidate
        ).resolve()
        if path not in seen:
            result.append(path)
            seen.add(path)
    return tuple(result)


def _production_snapshot_overrides(
    overrides: Mapping[str, Any],
) -> dict[str, Any]:
    """Pin production-only namespace and denominator inputs.

    ``build_checklist_freeze_snapshot`` remains parameterized for its small fixture
    tests.  The public production freeze/verify entry points, however, must never
    permit a caller to replace the reserved result namespace or reduce the 949-case
    denominator.  Caller-supplied score roots are additional audit roots, not
    replacements for the two canonical scorer namespaces.
    """

    normalized = dict(overrides)
    default_result_root = (repo_root() / DEFAULT_RESULT_NAMESPACE_LOCK.parent).resolve()
    supplied_candidate = Path(
        normalized.get("result_namespace_root", default_result_root)
    ).expanduser()
    supplied_result_root = (
        supplied_candidate
        if supplied_candidate.is_absolute()
        else repo_root() / supplied_candidate
    ).resolve()
    if supplied_result_root != default_result_root:
        raise ContractLifecycleError(
            "the production result namespace root is fixed and cannot be overridden: "
            f"expected={default_result_root}, actual={supplied_result_root}"
        )
    normalized["result_namespace_root"] = default_result_root

    supplied_count = normalized.get("expected_count", EXPECTED_CASE_COUNT)
    if supplied_count != EXPECTED_CASE_COUNT:
        raise ContractLifecycleError(
            "the production checklist freeze denominator is fixed at "
            f"{EXPECTED_CASE_COUNT}; actual={supplied_count!r}"
        )
    normalized["expected_count"] = EXPECTED_CASE_COUNT
    supplied_namespace = normalized.get("expected_result_namespace", RESULT_NAMESPACE)
    if supplied_namespace != RESULT_NAMESPACE:
        raise ContractLifecycleError(
            "the production result namespace identity cannot be overridden"
        )
    normalized["expected_result_namespace"] = RESULT_NAMESPACE

    extra_score_roots = tuple(normalized.get("score_result_roots", ()))
    normalized["score_result_roots"] = _deduplicated_resolved_paths(
        (*DEFAULT_SCORE_NAMESPACE_ROOTS, *extra_score_roots)
    )
    return normalized


def _recheck_empty_formal_outputs(precondition: Mapping[str, Any]) -> None:
    """Re-run the empty-output audit immediately before lock publication."""

    if precondition.get("formal_results_and_scores_are_empty") is not True:
        raise ContractLifecycleError(
            "formal output precondition is not an accepted empty-output snapshot"
        )
    result = precondition.get("result_namespace")
    scores = precondition.get("score_namespaces")
    if not isinstance(result, Mapping) or not isinstance(scores, list):
        raise ContractLifecycleError("formal output precondition is malformed")

    def recompute(value: Mapping[str, Any], label: str) -> dict[str, Any]:
        path = _resolve_declared_artifact_path(value.get("path"), f"{label}.path")
        marker_hashes = value.get("allowed_marker_hashes")
        if not isinstance(marker_hashes, Mapping):
            raise ContractLifecycleError(f"{label}.allowed_marker_hashes is malformed")
        return _empty_output_snapshot(
            path,
            label=label,
            allowed_files=tuple(sorted(str(name) for name in marker_hashes)),
        )

    _assert_exact(
        recompute(result, "formal result namespace"),
        dict(result),
        "pre-publication formal result namespace recheck",
    )
    for index, score in enumerate(scores):
        if not isinstance(score, Mapping):
            raise ContractLifecycleError(
                f"formal scoring namespace[{index}] snapshot is malformed"
            )
        _assert_exact(
            recompute(score, f"formal scoring namespace[{index}]"),
            dict(score),
            f"pre-publication formal scoring namespace[{index}] recheck",
        )


def _validate_frozen_formal_output_precondition(
    precondition: Mapping[str, Any],
    *,
    result_namespace_root: Path,
    score_result_roots: Sequence[str | Path],
) -> dict[str, Any]:
    """Validate the immutable *freeze-time* namespace assertion after publication.

    Formal outputs are expected to appear after a lock is published.  Currentness
    verification therefore checks the stored namespace identities and immutable
    marker hashes, while deliberately not re-imposing the one-time emptiness gate.
    """

    if precondition.get("formal_results_and_scores_are_empty") is not True:
        raise ContractLifecycleError("frozen formal output precondition is invalid")
    result = precondition.get("result_namespace")
    scores = precondition.get("score_namespaces")
    if not isinstance(result, Mapping) or not isinstance(scores, list):
        raise ContractLifecycleError("frozen formal output precondition is malformed")
    _assert_exact(
        _resolve_declared_artifact_path(result.get("path"), "frozen result path"),
        result_namespace_root,
        "frozen result namespace path",
    )
    result_markers = result.get("allowed_marker_hashes")
    if not isinstance(result_markers, Mapping):
        raise ContractLifecycleError("frozen result marker hashes are malformed")
    _assert_exact(
        set(result_markers), {"NAMESPACE_LOCK.json"}, "frozen result marker set"
    )
    marker = _require_regular_file(
        result_namespace_root / "NAMESPACE_LOCK.json", "result namespace marker"
    )
    _assert_exact(
        result_markers.get("NAMESPACE_LOCK.json"),
        sha256_file(marker),
        "frozen result namespace marker hash",
    )
    _assert_exact(result.get("formal_output_file_count"), 0, "frozen result file count")

    expected_score_roots = _deduplicated_resolved_paths(score_result_roots)
    if len(scores) != len(expected_score_roots):
        raise ContractLifecycleError("frozen score namespace count differs")
    for index, (score, expected_root) in enumerate(
        zip(scores, expected_score_roots, strict=True)
    ):
        if not isinstance(score, Mapping):
            raise ContractLifecycleError(
                f"frozen scoring namespace[{index}] is malformed"
            )
        _assert_exact(
            _resolve_declared_artifact_path(
                score.get("path"), f"frozen score namespace[{index}].path"
            ),
            expected_root,
            f"frozen score namespace[{index}] path",
        )
        _assert_exact(
            score.get("allowed_marker_hashes"),
            {},
            f"frozen score namespace[{index}] marker set",
        )
        _assert_exact(
            score.get("formal_output_file_count"),
            0,
            f"frozen score namespace[{index}] file count",
        )
    return dict(precondition)


def _expected_llm_token_usage(api_response: Mapping[str, Any]) -> dict[str, int]:
    usage = api_response.get("usage")
    usage = usage if isinstance(usage, Mapping) else {}
    input_details = usage.get("input_tokens_details")
    input_details = input_details if isinstance(input_details, Mapping) else {}
    output_details = usage.get("output_tokens_details")
    output_details = output_details if isinstance(output_details, Mapping) else {}
    return {
        "prompt_tokens": int(usage.get("input_tokens", 0) or 0),
        "completion_tokens": int(usage.get("output_tokens", 0) or 0),
        "cached_prompt_tokens": int(input_details.get("cached_tokens", 0) or 0),
        "reasoning_tokens": int(output_details.get("reasoning_tokens", 0) or 0),
        "total_tokens": int(usage.get("total_tokens", 0) or 0),
    }


def _assert_locked_codex_command(
    command: Any,
    *,
    model: str,
    reasoning_effort: str,
    output_name: str,
    context: str,
) -> None:
    if not isinstance(command, list) or not all(
        isinstance(part, str) for part in command
    ):
        raise ContractLifecycleError(f"{context} command is malformed")
    if len(command) != 23:
        raise ContractLifecycleError(f"{context} command length differs")
    workspace = Path(command[3])
    schema_path = Path(command[19])
    output_path = Path(command[21])
    expected = [
        "codex",
        "exec",
        "--cd",
        command[3],
        "--skip-git-repo-check",
        "--ephemeral",
        "--ignore-user-config",
        "--sandbox",
        "read-only",
        "--model",
        model,
        "-c",
        f'model_reasoning_effort="{reasoning_effort}"',
        "-c",
        'model_verbosity="low"',
        "--color",
        "never",
        "--json",
        "--output-schema",
        command[19],
        "-o",
        command[21],
        "-",
    ]
    _assert_exact(command, expected, f"{context} locked Codex command")
    _assert_exact(schema_path.parent, workspace, f"{context} schema workspace")
    _assert_exact(schema_path.name, "output_schema.json", f"{context} schema name")
    _assert_exact(output_path.parent, workspace, f"{context} output workspace")
    _assert_exact(output_path.name, output_name, f"{context} output name")


def _validate_codex_call_provenance(
    *,
    api_response_path: Path,
    llm_call_path: Path,
    reasoning_summary_path: Path,
    case_unit_id: str,
    task_id: str,
    phase: str,
    model: str,
    reasoning_effort: str,
    timeout_seconds: int,
    input_lock_time: datetime,
    response_ids: set[str],
    codex_cli_version: str | None = None,
    attempt_started: datetime | None = None,
    attempt_finished: datetime | None = None,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Validate one raw Codex call and return its API/LLM records and thread id."""

    api_file = _require_regular_file(api_response_path, f"{phase} API response")
    llm_file = _require_regular_file(llm_call_path, f"{phase} LLM call")
    reasoning_file = _require_regular_file(
        reasoning_summary_path, f"{phase} reasoning summary"
    )
    api_response = _load_mapping(api_file, f"{phase} API response")
    llm_call = _load_mapping(llm_file, f"{phase} LLM call")
    context = f"{phase} Codex call for {case_unit_id}"

    if phase == "draft":
        expected_phase_fields = {
            "phase": "draft",
            "experiment_type": "minimal_package",
            "agent_id_or_role": "case_checklist_drafter",
            "temperature": 0.0,
            "max_tokens": 12000,
        }
        output_name = "draft_body.json"
    elif phase == "checklist_model_review":
        expected_phase_fields = {
            "phase": "checklist_model_review",
            "experiment_type": "agentdojo_full_extension",
            "agent_id_or_role": "case_checklist_model_reviewer",
            "temperature": None,
            "max_tokens": None,
        }
        output_name = "model_review.json"
    else:  # pragma: no cover - internal API owns this enum
        raise ContractLifecycleError(f"unsupported Codex provenance phase: {phase}")

    expected_llm_fields = {
        "schema_version": "llm_call/v1",
        "provider": "codex_cli",
        "model": model,
        "model_version": model,
        "api_key_env": "CODEX_HOME",
        "domain": "agentdojo",
        "case_unit_id": case_unit_id,
        "task_id": task_id,
        "timeout_seconds": timeout_seconds,
        "retry_index": 0,
        **expected_phase_fields,
    }
    for field, expected in expected_llm_fields.items():
        _assert_exact(llm_call.get(field), expected, f"{context} llm_call.{field}")

    request_time = _parse_aware_timestamp(
        llm_call.get("request_timestamp"), f"{context} request_timestamp"
    )
    response_time = _parse_aware_timestamp(
        llm_call.get("response_timestamp"), f"{context} response_timestamp"
    )
    if request_time <= input_lock_time:
        raise ContractLifecycleError(
            f"{context} predates or equals the frozen draft input lock"
        )
    if response_time < request_time:
        raise ContractLifecycleError(f"{context} response predates its request")
    if attempt_started is not None and request_time < attempt_started:
        raise ContractLifecycleError(f"{context} request predates the attempt")
    if attempt_finished is not None and response_time > attempt_finished:
        raise ContractLifecycleError(f"{context} response postdates the attempt")

    for field, expected in (
        ("status", "completed"),
        ("model", model),
        ("provider", "codex_cli"),
    ):
        _assert_exact(api_response.get(field), expected, f"{context} API.{field}")
    response_id = api_response.get("id")
    if not isinstance(response_id, str) or not response_id.strip():
        raise ContractLifecycleError(f"{context} response/thread id is missing")
    response_id = response_id.strip()
    if response_id in response_ids:
        raise ContractLifecycleError(
            f"duplicate generation/review response id: {response_id}"
        )
    response_ids.add(response_id)

    response_metadata = llm_call.get("response_metadata")
    if not isinstance(response_metadata, Mapping):
        raise ContractLifecycleError(f"{context} response metadata is missing")
    for field, expected in (
        ("response_id", response_id),
        ("response_status", "completed"),
        ("provider_model", model),
        ("reasoning_effort", reasoning_effort),
        ("auth_mode", "codex_login"),
    ):
        _assert_exact(
            response_metadata.get(field), expected, f"{context} metadata.{field}"
        )
    _assert_exact(
        _resolve_declared_artifact_path(
            response_metadata.get("raw_api_response_path"),
            f"{context} metadata.raw_api_response_path",
        ),
        api_file,
        f"{context} raw API path",
    )
    _assert_exact(
        _resolve_declared_artifact_path(
            response_metadata.get("reasoning_summary_path"),
            f"{context} metadata.reasoning_summary_path",
        ),
        reasoning_file,
        f"{context} reasoning path",
    )
    if phase == "draft":
        _assert_exact(
            response_metadata.get("max_output_tokens_enforced"),
            False,
            f"{context} output cap disclosure",
        )
    else:
        for field, expected in (
            ("sandbox", "read-only"),
            ("codex_cli_version", codex_cli_version),
            ("ephemeral", True),
            ("ignore_user_config", True),
            ("model_verbosity", "low"),
        ):
            _assert_exact(
                response_metadata.get(field),
                expected,
                f"{context} metadata.{field}",
            )

    _assert_exact(
        llm_call.get("token_usage"),
        _expected_llm_token_usage(api_response),
        f"{context} token usage",
    )
    codex = api_response.get("codex_cli")
    if not isinstance(codex, Mapping):
        raise ContractLifecycleError(f"{context} Codex CLI record is missing")
    for field, expected in (
        ("auth_mode", "codex_login"),
        ("returncode", 0),
        ("timeout_seconds", timeout_seconds),
        ("sandbox", "read-only"),
        ("malformed_event_lines", []),
    ):
        _assert_exact(codex.get(field), expected, f"{context} codex_cli.{field}")
    if phase == "checklist_model_review":
        for field, expected in (
            ("ephemeral", True),
            ("ignore_user_config", True),
            ("model_verbosity", "low"),
            (
                "input_files",
                ["case_packet.md", "checklist.yaml", "review_prompt.md"],
            ),
        ):
            _assert_exact(codex.get(field), expected, f"{context} codex_cli.{field}")
    _assert_locked_codex_command(
        codex.get("command"),
        model=model,
        reasoning_effort=reasoning_effort,
        output_name=output_name,
        context=context,
    )
    events = codex.get("events")
    if not isinstance(events, list) or not all(
        isinstance(event, Mapping) for event in events
    ):
        raise ContractLifecycleError(f"{context} event stream is malformed")
    thread_ids = [
        event.get("thread_id")
        for event in events
        if event.get("type") == "thread.started"
    ]
    _assert_exact(thread_ids, [response_id], f"{context} thread-start binding")

    try:
        if phase == "draft":
            from neurips_ed_track_minimal.scripts.draft_case_checklist import (
                extract_reasoning_summary_text,
            )

            reasoning = extract_reasoning_summary_text(dict(api_response))
        else:
            from neurips_ed_track_minimal.scripts.review_case_checklist_with_codex import (
                extract_reasoning_summary,
            )

            reasoning = extract_reasoning_summary(api_response)
    except Exception as exc:  # pragma: no cover - locked extractor failure
        raise ContractLifecycleError(
            f"{context} reasoning could not be independently reconstructed: {exc}"
        ) from exc
    expected_reasoning = reasoning + ("\n" if reasoning else "")
    _assert_exact(
        reasoning_file.read_text(encoding="utf-8"),
        expected_reasoning,
        f"{context} reasoning summary",
    )
    return dict(api_response), dict(llm_call), response_id


def _validate_generation_batch_provenance(
    *,
    drafts: Path,
    cases: Sequence[Any],
    packets: Mapping[str, Any],
    config: Mapping[str, Any],
    config_paths: Mapping[str, Path],
    input_lock_time: datetime,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Require a completed, non-skipped 949-case generation batch."""

    summary_path = _require_regular_file(
        drafts / "_batch_summary.json", "draft generation batch summary"
    )
    results_path = _require_regular_file(
        drafts / "_batch_results.jsonl", "draft generation batch results"
    )
    summary = _load_mapping(summary_path, "draft generation batch summary")
    results = _load_jsonl_mappings(results_path, "draft generation batch results")
    expected_count = len(cases)
    generation_config = config["generation"]
    assert isinstance(generation_config, Mapping)
    packet_sizes = [
        packets[case.case_unit_id].case_packet_path.stat().st_size for case in cases
    ]
    regular_sizes = [size for size in packet_sizes if size < 100000]
    oversized_sizes = [size for size in packet_sizes if size >= 100000]

    def lane_stats(sizes: Sequence[int]) -> dict[str, int]:
        return {
            "count": len(sizes),
            "min_bytes": min(sizes) if sizes else 0,
            "max_bytes": max(sizes) if sizes else 0,
        }

    for field, expected in (
        ("total_cases", expected_count),
        ("completed_cases", expected_count),
        ("success_cases", expected_count),
        ("skipped_cases", 0),
        ("failed_cases", 0),
        ("provider", "codex"),
        ("model", generation_config["model"]),
        ("reasoning_effort", generation_config["reasoning_effort"]),
        ("codex_sandbox", generation_config["sandbox"]),
        ("token_budgets", generation_config["token_budgets"]),
        ("sort_by", "name"),
        ("quality_check", "agentdojo"),
        ("large_case_threshold_bytes", 100000),
        (
            "lane_stats",
            {
                "regular": lane_stats(regular_sizes),
                "oversized": lane_stats(oversized_sizes),
            },
        ),
    ):
        _assert_exact(summary.get(field), expected, f"generation batch summary.{field}")
    _assert_exact(
        summary.get("prompt_supplement"),
        None,
        "generation batch prompt supplement must be disabled",
    )
    _assert_exact(
        _resolve_declared_artifact_path(
            summary.get("output_root"), "generation batch summary.output_root"
        ),
        drafts,
        "generation batch output root",
    )
    started = _parse_aware_timestamp(
        summary.get("started_at"), "generation batch summary.started_at"
    )
    updated = _parse_aware_timestamp(
        summary.get("updated_at"), "generation batch summary.updated_at"
    )
    if started <= input_lock_time:
        raise ContractLifecycleError(
            "generation batch started before or at the frozen draft input lock"
        )
    if updated < started:
        raise ContractLifecycleError("generation batch update predates its start")
    warning_count = summary.get("warning_count")
    if not isinstance(warning_count, int) or warning_count < 0:
        raise ContractLifecycleError("generation batch warning_count is invalid")

    if len(results) != expected_count:
        raise ContractLifecycleError(
            "generation batch result count differs: "
            f"expected={expected_count}, actual={len(results)}"
        )
    result_by_dir: dict[str, dict[str, Any]] = {}
    for index, result in enumerate(results):
        directory = result.get("case_unit_dir")
        if not isinstance(directory, str) or not directory:
            raise ContractLifecycleError(
                f"generation batch result[{index}] has no case directory"
            )
        if directory in result_by_dir:
            raise ContractLifecycleError(
                f"generation batch contains duplicate case directory: {directory}"
            )
        if result.get("status") != "success":
            raise ContractLifecycleError(
                "generation batch contains a skipped/failed/preseeded case: "
                f"{directory} status={result.get('status')!r}"
            )
        result_by_dir[directory] = result
    expected_directories = {
        packets[case.case_unit_id].case_packet_path.parent.name for case in cases
    }
    _assert_exact(
        set(result_by_dir), expected_directories, "generation batch case directory set"
    )
    return result_by_dir, {
        "summary_path": _repo_relative(summary_path),
        "summary_sha256": sha256_file(summary_path),
        "results_path": _repo_relative(results_path),
        "results_sha256": sha256_file(results_path),
    }


def _validate_generation_case_provenance(
    *,
    case: Any,
    packet: Any,
    case_dir: Path,
    paths: Mapping[str, Path],
    batch_result: Mapping[str, Any],
    config: Mapping[str, Any],
    config_paths: Mapping[str, Path],
    input_lock_time: datetime,
    response_ids: set[str],
) -> dict[str, Any]:
    """Bind one generated checklist to a fresh attempt-01 Codex call."""

    generation_config = config["generation"]
    assert isinstance(generation_config, Mapping)
    attempt_records = batch_result.get("attempts")
    if not isinstance(attempt_records, list) or len(attempt_records) != 1:
        raise ContractLifecycleError(
            f"generation must have exactly one fresh attempt: {case.case_unit_id}"
        )
    attempt_record = attempt_records[0]
    if not isinstance(attempt_record, Mapping):
        raise ContractLifecycleError(
            f"generation attempt record is malformed: {case.case_unit_id}"
        )
    for field, expected in (
        ("attempt_index", 1),
        ("max_output_tokens", generation_config["token_budgets"][0]),
        ("codex_timeout_seconds", generation_config["timeout_seconds"]),
        ("returncode", 0),
    ):
        _assert_exact(
            attempt_record.get(field),
            expected,
            f"generation batch {case.case_unit_id}.{field}",
        )
    validator = attempt_record.get("validator")
    if not isinstance(validator, str) or not validator.strip():
        raise ContractLifecycleError(
            f"generation attempt lacks validator evidence: {case.case_unit_id}"
        )
    _assert_exact(
        batch_result.get("case_unit_dir"),
        case_dir.name,
        f"generation batch case directory {case.case_unit_id}",
    )
    _assert_exact(
        _resolve_declared_artifact_path(
            batch_result.get("case_packet"),
            f"generation batch {case.case_unit_id}.case_packet",
        ),
        packet.case_packet_path,
        f"generation batch packet {case.case_unit_id}",
    )
    _assert_exact(
        batch_result.get("case_packet_size_bytes"),
        packet.case_packet_path.stat().st_size,
        f"generation packet size {case.case_unit_id}",
    )
    _assert_exact(
        _resolve_declared_artifact_path(
            batch_result.get("checklist_path"),
            f"generation batch {case.case_unit_id}.checklist_path",
        ),
        case_dir / "checklist.yaml",
        f"generation promoted checklist path {case.case_unit_id}",
    )

    prefix = case_dir / "attempt_01"
    attempt_paths = {
        "checklist": prefix.with_suffix(".checklist.yaml"),
        "checklist_json": prefix.with_suffix(".checklist.json"),
        "api_response": prefix.with_suffix(".api_response.json"),
        "llm_call": prefix.with_suffix(".llm_call.json"),
        "reasoning_summary": prefix.with_suffix(".reasoning_summary.txt"),
    }
    for label, path in tuple(attempt_paths.items()):
        attempt_paths[label] = _require_regular_file(
            path, f"generation attempt-01 {label} for {case.case_unit_id}"
        )
    extra_attempts = sorted(
        path.name
        for path in case_dir.glob("attempt_[0-9][0-9].checklist.yaml")
        if path != attempt_paths["checklist"]
    )
    if extra_attempts:
        raise ContractLifecycleError(
            f"generation contains unbound retry artifacts for {case.case_unit_id}: "
            f"{extra_attempts}"
        )
    if not validator.rstrip().endswith(str(attempt_paths["checklist"])):
        raise ContractLifecycleError(
            f"generation validator does not bind attempt-01 for {case.case_unit_id}"
        )

    for canonical_key, attempt_key in (
        ("generated_checklist", "checklist"),
        ("generated_checklist_json", "checklist_json"),
        ("api_response", "api_response"),
        ("llm_call", "llm_call"),
        ("reasoning_summary", "reasoning_summary"),
    ):
        _assert_exact(
            paths[canonical_key].read_bytes(),
            attempt_paths[attempt_key].read_bytes(),
            f"promoted generation {canonical_key} for {case.case_unit_id}",
        )

    attempt_checklist = _load_mapping(
        attempt_paths["checklist"], "generation attempt checklist"
    )
    attempt_json = _load_mapping(
        attempt_paths["checklist_json"], "generation attempt checklist JSON"
    )
    _assert_exact(
        attempt_json,
        attempt_checklist,
        f"generation attempt YAML/JSON semantics {case.case_unit_id}",
    )
    api_response, _, response_id = _validate_codex_call_provenance(
        api_response_path=attempt_paths["api_response"],
        llm_call_path=attempt_paths["llm_call"],
        reasoning_summary_path=attempt_paths["reasoning_summary"],
        case_unit_id=case.case_unit_id,
        task_id=case.task_id,
        phase="draft",
        model=str(generation_config["model"]),
        reasoning_effort=str(generation_config["reasoning_effort"]),
        timeout_seconds=int(generation_config["timeout_seconds"]),
        input_lock_time=input_lock_time,
        response_ids=response_ids,
    )
    try:
        from neurips_ed_track_minimal.scripts.draft_case_checklist import (
            extract_json_text,
            strip_null_fields,
        )

        generated_body = strip_null_fields(extract_json_text(api_response))
    except Exception as exc:
        raise ContractLifecycleError(
            f"generation body reconstruction failed for {case.case_unit_id}: {exc}"
        ) from exc
    expected_body = {
        key: value
        for key, value in attempt_checklist.items()
        if key not in {"schema_version", "case_unit_id", "domain", "task_id"}
    }
    _assert_exact(
        generated_body,
        expected_body,
        f"generation API body/checklist binding {case.case_unit_id}",
    )
    for field, expected in (
        ("schema_version", "case_checklist_v1"),
        ("case_unit_id", case.case_unit_id),
        ("domain", "agentdojo"),
        ("task_id", case.task_id),
    ):
        _assert_exact(
            attempt_checklist.get(field),
            expected,
            f"generation attempt identity {case.case_unit_id}.{field}",
        )

    return {
        "case_unit_id": case.case_unit_id,
        "response_id": response_id,
        "attempt_checklist_sha256": sha256_file(attempt_paths["checklist"]),
        "attempt_checklist_json_sha256": sha256_file(attempt_paths["checklist_json"]),
        "attempt_api_response_sha256": sha256_file(attempt_paths["api_response"]),
        "attempt_llm_call_sha256": sha256_file(attempt_paths["llm_call"]),
        "attempt_reasoning_summary_sha256": sha256_file(
            attempt_paths["reasoning_summary"]
        ),
        "case_packet_sha256": sha256_file(packet.case_packet_path),
        "composed_draft_prompt_sha256": sha256_file(
            config_paths["composed_draft_prompt"]
        ),
        "checklist_schema_sha256": sha256_file(config_paths["checklist_schema"]),
    }


def _materialize_review_revision(
    model_review: Mapping[str, Any], *, case_unit_id: str, task_id: str
) -> dict[str, Any]:
    revision = model_review.get("revised_checklist")
    if not isinstance(revision, Mapping):
        raise ContractLifecycleError("revise decision has no checklist body")
    if "schema_version" in revision:
        materialized = dict(revision)
    else:
        materialized = {
            "schema_version": "case_checklist_v1",
            "case_unit_id": case_unit_id,
            "domain": "agentdojo",
            "task_id": task_id,
            **dict(revision),
        }
    materialized["schema_version"] = "case_checklist_v1"
    materialized["case_unit_id"] = case_unit_id
    materialized["domain"] = "agentdojo"
    materialized["task_id"] = task_id
    return materialized


def _validate_review_case_provenance(
    *,
    case: Any,
    packet: Any,
    case_dir: Path,
    generated_checklist_path: Path,
    final_checklist_path: Path,
    review_receipt: Mapping[str, Any],
    lifecycle: Mapping[str, Any],
    report_run_id: str,
    config: Mapping[str, Any],
    config_paths: Mapping[str, Path],
    review_schema: Mapping[str, Any],
    checklist_validator: Draft202012Validator,
    input_lock_time: datetime,
    response_ids: set[str],
) -> dict[str, Any]:
    """Validate the complete independent-review and revision decision chain."""

    from neurips_ed_track_minimal.scripts import update_case_locks_batch as batch
    from neurips_ed_track_minimal.scripts.case_checklist_review import (
        review_agentdojo_checklist,
    )
    from neurips_ed_track_minimal.scripts.review_case_checklist_with_codex import (
        extract_json_text,
        normalize_provider_model_review,
        strip_null_fields,
        validate_model_review_body,
    )

    review_config = config["review"]
    assert isinstance(review_config, Mapping)
    attempts = lifecycle.get("attempts")
    rounds = lifecycle.get("review_rounds")
    if not isinstance(rounds, int) or rounds < 1:
        raise ContractLifecycleError(
            f"accepted review has no rounds: {case.case_unit_id}"
        )
    if not isinstance(attempts, list) or len(attempts) != rounds:
        raise ContractLifecycleError(
            f"review attempt denominator differs: {case.case_unit_id}"
        )

    review_root = case_dir / "review_attempts"
    active_root = _require_regular_directory(
        review_root / report_run_id, f"active review run for {case.case_unit_id}"
    )
    stale_runs: list[dict[str, str]] = []
    for run_dir in sorted(path for path in review_root.iterdir() if path.is_dir()):
        if run_dir != active_root:
            stale_runs.append(
                {"run_id": run_dir.name, "tree_sha256": sha256_path(run_dir)}
            )

    generated_hash = sha256_file(generated_checklist_path)
    final_hash = sha256_file(final_checklist_path)
    current_input_path = generated_checklist_path
    current_input_hash = generated_hash
    previous_finished: datetime | None = None
    decisions: list[str] = []
    active_expected_files: set[Path] = set()
    attempt_components: list[dict[str, Any]] = []

    for round_index, raw_attempt in enumerate(attempts, start=1):
        if not isinstance(raw_attempt, Mapping):
            raise ContractLifecycleError(
                f"review attempt {round_index} is malformed: {case.case_unit_id}"
            )
        attempt = dict(raw_attempt)
        context = f"review {case.case_unit_id} round {round_index}"
        _assert_exact(attempt.get("round"), round_index, f"{context} number")
        _assert_exact(attempt.get("returncode"), 0, f"{context} returncode")
        if "error" in attempt or "revision_validation_error" in attempt:
            raise ContractLifecycleError(f"{context} contains an unresolved error")
        started = _parse_aware_timestamp(
            attempt.get("started_at"), f"{context}.started_at"
        )
        finished = _parse_aware_timestamp(
            attempt.get("finished_at"), f"{context}.finished_at"
        )
        if finished < started:
            raise ContractLifecycleError(f"{context} finishes before it starts")
        if previous_finished is not None and started <= previous_finished:
            raise ContractLifecycleError(
                f"{context} is not a fresh call after the previous round"
            )
        previous_finished = finished

        declared_input = _resolve_declared_artifact_path(
            attempt.get("input_checklist_path"), f"{context}.input_checklist_path"
        )
        expected_declared_input = (
            case_dir / "checklist.yaml" if round_index == 1 else current_input_path
        ).resolve()
        _assert_exact(
            declared_input, expected_declared_input, f"{context} input checklist path"
        )
        _assert_exact(
            attempt.get("input_checklist_sha256"),
            current_input_hash,
            f"{context} input checklist hash",
        )
        current_checklist = _load_mapping(
            current_input_path, f"{context} immutable input checklist"
        )
        deterministic = review_agentdojo_checklist(
            current_checklist, case_packet_path=packet.case_packet_path
        )
        _assert_exact(
            attempt.get("deterministic_review"),
            deterministic,
            f"{context} deterministic review",
        )

        prefix = active_root / f"round_{round_index:02d}"
        model_review_path = prefix.with_suffix(".model_review.json")
        _assert_exact(
            _resolve_declared_artifact_path(
                attempt.get("model_review_path"), f"{context}.model_review_path"
            ),
            model_review_path,
            f"{context} model review path",
        )
        model_review_path = _require_regular_file(
            model_review_path, f"{context} model review"
        )
        _assert_exact(
            attempt.get("model_review_sha256"),
            sha256_file(model_review_path),
            f"{context} model review hash",
        )
        model_review = _load_mapping(model_review_path, f"{context} model review")
        try:
            validated_model_review = validate_model_review_body(
                model_review, review_schema
            )
        except Exception as exc:
            raise ContractLifecycleError(
                f"{context} model-review body is invalid: {exc}"
            ) from exc
        _assert_exact(
            validated_model_review,
            model_review,
            f"{context} model-review materialization",
        )
        decision = str(model_review.get("decision") or "")
        _assert_exact(attempt.get("decision"), decision, f"{context} decision")
        expected_decision = "accept" if round_index == rounds else "revise"
        _assert_exact(decision, expected_decision, f"{context} decision chain")
        if deterministic.get("status") != "pass" and decision != "revise":
            raise ContractLifecycleError(
                f"{context} accepted despite deterministic blocking findings"
            )
        decisions.append(decision)

        if deterministic == {"status": "pass", "findings": []}:
            prompt_path = config_paths["review_prompt"]
        else:
            prompt_path = prefix.with_suffix(".review_prompt.md")
            prompt_path = _require_regular_file(prompt_path, f"{context} review prompt")
            expected_prompt = (
                config_paths["review_prompt"].read_text(encoding="utf-8").rstrip()
            )
            expected_prompt += (
                "\n\n## Deterministic blocking findings\n\n"
                "Treat every item below as blocking. Return `revise` and a complete "
                "corrected checklist.\n\n"
                "```json\n"
                + json.dumps(
                    deterministic.get("findings", []), indent=2, ensure_ascii=False
                )
                + "\n```\n"
            )
            _assert_exact(
                prompt_path.read_text(encoding="utf-8"),
                expected_prompt,
                f"{context} deterministic review prompt",
            )
            active_expected_files.add(prompt_path)
        _assert_exact(
            _resolve_declared_artifact_path(
                attempt.get("review_prompt_path"), f"{context}.review_prompt_path"
            ),
            prompt_path,
            f"{context} review prompt path",
        )
        _assert_exact(
            attempt.get("review_prompt_sha256"),
            sha256_file(prompt_path),
            f"{context} review prompt hash",
        )

        api_path = prefix.with_suffix(".model_review.api_response.json")
        llm_path = prefix.with_suffix(".model_review.llm_call.json")
        reasoning_path = prefix.with_suffix(".model_review.reasoning_summary.txt")
        api_response, _, response_id = _validate_codex_call_provenance(
            api_response_path=api_path,
            llm_call_path=llm_path,
            reasoning_summary_path=reasoning_path,
            case_unit_id=case.case_unit_id,
            task_id=case.task_id,
            phase="checklist_model_review",
            model=str(review_config["model"]),
            reasoning_effort=str(review_config["reasoning_effort"]),
            timeout_seconds=int(review_config["timeout_seconds"]),
            input_lock_time=input_lock_time,
            response_ids=response_ids,
            codex_cli_version=str(config["codex_cli_version"]),
            attempt_started=started,
            attempt_finished=finished,
        )
        try:
            api_model_review = strip_null_fields(
                normalize_provider_model_review(extract_json_text(api_response))
            )
        except Exception as exc:
            raise ContractLifecycleError(
                f"{context} raw model review reconstruction failed: {exc}"
            ) from exc
        _assert_exact(
            api_model_review,
            model_review,
            f"{context} API/model-review body binding",
        )
        for artifact in (
            model_review_path,
            api_path,
            llm_path,
            reasoning_path,
            prefix.with_suffix(".stdout.log"),
            prefix.with_suffix(".stderr.log"),
        ):
            active_expected_files.add(
                _require_regular_file(artifact, f"{context} sidecar")
            )

        component = {
            "round": round_index,
            "decision": decision,
            "input_checklist_sha256": current_input_hash,
            "review_prompt_sha256": sha256_file(prompt_path),
            "model_review_sha256": sha256_file(model_review_path),
            "api_response_sha256": sha256_file(api_path),
            "llm_call_sha256": sha256_file(llm_path),
            "reasoning_summary_sha256": sha256_file(reasoning_path),
            "response_id": response_id,
        }

        if decision == "revise":
            revision_path = prefix.with_suffix(".revised_checklist.yaml")
            revision_path = _require_regular_file(
                revision_path, f"{context} revised checklist"
            )
            expected_revision = _materialize_review_revision(
                model_review,
                case_unit_id=case.case_unit_id,
                task_id=case.task_id,
            )
            _assert_exact(
                _load_mapping(revision_path, f"{context} revised checklist"),
                expected_revision,
                f"{context} revised checklist body",
            )
            expected_revision_bytes = yaml.safe_dump(
                expected_revision,
                sort_keys=False,
                allow_unicode=True,
                width=1000,
            ).encode("utf-8")
            _assert_exact(
                revision_path.read_bytes(),
                expected_revision_bytes,
                f"{context} canonical revised checklist bytes",
            )
            try:
                batch._validate_checklist(
                    revision_path,
                    packet=packet,
                    checklist_validator=checklist_validator,
                )
            except batch.BatchCaseLockError as exc:
                raise ContractLifecycleError(str(exc)) from exc
            revision_hash = sha256_file(revision_path)
            if revision_hash == current_input_hash:
                raise ContractLifecycleError(
                    f"{context} revise decision did not change the checklist"
                )
            current_input_path = revision_path
            current_input_hash = revision_hash
            component["revised_checklist_sha256"] = revision_hash
            active_expected_files.add(revision_path)
        attempt_components.append(component)

    _assert_exact(
        current_input_hash,
        final_hash,
        f"final accepted review input {case.case_unit_id}",
    )
    expected_revised = generated_hash != final_hash
    _assert_exact(
        lifecycle.get("revised"),
        expected_revised,
        f"review revised flag {case.case_unit_id}",
    )
    _assert_exact(
        any(decision == "revise" for decision in decisions),
        expected_revised,
        f"review decision/checklist revision equivalence {case.case_unit_id}",
    )
    _assert_exact(
        review_receipt.get("model_review"),
        _load_mapping(
            active_root / f"round_{rounds:02d}.model_review.json",
            "final model review",
        ),
        f"final review receipt/model sidecar {case.case_unit_id}",
    )
    _assert_exact(
        review_receipt.get("deterministic_review"),
        {"status": "pass", "findings": []},
        f"final review deterministic result {case.case_unit_id}",
    )
    _assert_exact(
        review_receipt.get("decision"),
        "accept",
        f"final review decision {case.case_unit_id}",
    )
    _assert_exact(
        review_receipt.get("unresolved_findings"),
        [],
        f"final review unresolved findings {case.case_unit_id}",
    )

    actual_active_files = {
        path.resolve() for path in active_root.iterdir() if path.is_file()
    }
    _assert_exact(
        actual_active_files,
        {path.resolve() for path in active_expected_files},
        f"active review artifact set {case.case_unit_id}",
    )
    return {
        "case_unit_id": case.case_unit_id,
        "run_id": report_run_id,
        "generated_checklist_sha256": generated_hash,
        "final_checklist_sha256": final_hash,
        "revised": expected_revised,
        "review_rounds": rounds,
        "attempts_sha256": sha256_object(attempt_components),
        "active_review_tree_sha256": sha256_path(active_root),
        "excluded_stale_review_runs": stale_runs,
    }


def _validate_draft_review_config(
    config: Mapping[str, Any],
    *,
    expected_count: int,
    config_path: Path,
    case_lock_path: Path,
    lock_acceptance_path: Path,
    score_prompt_path: Path,
    score_schema_path: Path,
) -> dict[str, Path]:
    required_top = {
        "schema_version": "agentdojo_draft_review_config/v1",
        "benchmark_version": BENCHMARK_VERSION,
        "attack": ATTACK,
        "defense": DEFENSE,
        "expected_cases": expected_count,
    }
    for field, expected in required_top.items():
        _assert_exact(config.get(field), expected, f"draft review config.{field}")

    generation = config.get("generation")
    review = config.get("review")
    locking = config.get("locking")
    if not isinstance(generation, Mapping) or not isinstance(review, Mapping):
        raise ContractLifecycleError(
            "draft review config requires generation and review mappings"
        )
    if not isinstance(locking, Mapping):
        raise ContractLifecycleError("draft review config requires a locking mapping")
    common = {
        "provider": "codex_cli",
        "auth_mode": "codex_login",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "xhigh",
        "sandbox": "read-only",
        "ephemeral": True,
        "ignore_user_config": True,
        "model_verbosity": "low",
        "max_parallel": 6,
    }
    for section_name, section in (("generation", generation), ("review", review)):
        for field, expected in common.items():
            _assert_exact(
                section.get(field),
                expected,
                f"draft review config.{section_name}.{field}",
            )
        timeout = section.get("timeout_seconds")
        if not isinstance(timeout, int) or timeout <= 0:
            raise ContractLifecycleError(
                f"draft review config.{section_name}.timeout_seconds must be positive"
            )
    _assert_exact(
        generation.get("token_budgets"),
        [12000, 16000, 20000, 24000],
        "draft review config.generation.token_budgets",
    )
    _assert_exact(
        generation.get("token_budgets_are_retry_labels_not_codex_output_caps"),
        True,
        "draft review config.generation retry-label disclosure",
    )
    if not isinstance(review.get("max_rounds"), int) or int(review["max_rounds"]) < 2:
        raise ContractLifecycleError(
            "draft review config.review.max_rounds must be at least 2"
        )
    if (
        not isinstance(config.get("codex_cli_version"), str)
        or not str(config.get("codex_cli_version")).strip()
    ):
        raise ContractLifecycleError(
            "draft review config must lock a Codex CLI version"
        )

    _assert_exact(
        generation.get("prompt_supplement"),
        None,
        "draft review config.generation.prompt_supplement must be disabled",
    )
    paths = {
        "base_draft_prompt": _validate_path_lock(
            generation.get("base_prompt"), "draft review config.generation.base_prompt"
        ),
        "composed_draft_prompt": _validate_path_lock(
            generation.get("composed_prompt"),
            "draft review config.generation.composed_prompt",
        ),
        "checklist_schema": _validate_path_lock(
            generation.get("checklist_schema"),
            "draft review config.generation.checklist_schema",
        ),
        "checklist_template": _validate_path_lock(
            generation.get("template"), "draft review config.generation.template"
        ),
        "review_prompt": _validate_path_lock(
            review.get("prompt"), "draft review config.review.prompt"
        ),
        "review_schema": _validate_path_lock(
            review.get("schema"), "draft review config.review.schema"
        ),
        "batch_lock_runner": _validate_path_lock(
            locking.get("batch_runner"), "draft review config.locking.batch_runner"
        ),
        "single_case_lock_runner": _validate_path_lock(
            locking.get("single_case_runner"),
            "draft review config.locking.single_case_runner",
        ),
        "score_prompt": _validate_path_lock(
            locking.get("score_prompt"), "draft review config.locking.score_prompt"
        ),
        "score_schema": _validate_path_lock(
            locking.get("score_schema"), "draft review config.locking.score_schema"
        ),
    }
    _assert_exact(paths["score_prompt"], score_prompt_path, "locked score prompt path")
    _assert_exact(paths["score_schema"], score_schema_path, "locked score schema path")
    _assert_exact(
        _resolve_declared_artifact_path(
            locking.get("case_lock_file"), "locking.case_lock_file"
        ),
        case_lock_path,
        "locked case checklist lock path",
    )
    _assert_exact(
        _resolve_declared_artifact_path(
            locking.get("lock_acceptance"), "locking.lock_acceptance"
        ),
        lock_acceptance_path,
        "locked checklist acceptance path",
    )

    code_locks = config.get("lifecycle_code")
    if not isinstance(code_locks, list) or not code_locks:
        raise ContractLifecycleError(
            "draft review config.lifecycle_code must be a non-empty list"
        )
    code_paths = [
        _validate_path_lock(item, f"draft review config.lifecycle_code[{index}]")
        for index, item in enumerate(code_locks)
    ]
    if len(set(code_paths)) != len(code_paths):
        raise ContractLifecycleError(
            "draft review config.lifecycle_code contains duplicates"
        )
    if expected_count == EXPECTED_CASE_COUNT:
        required_names = {
            "run_agentdojo_full_draft_review.py",
            "run_draft_batch.py",
            "draft_case_checklist.py",
            "checklist_validator.py",
            "review_case_checklist_with_codex.py",
            "update_case_locks.py",
            "update_case_locks_batch.py",
            "checklist_guardrails.py",
            "case_checklist_review.py",
        }
        observed_names = {path.name for path in code_paths}
        if observed_names != required_names:
            raise ContractLifecycleError(
                "draft lifecycle code set differs: "
                f"missing={sorted(required_names - observed_names)}, "
                f"extra={sorted(observed_names - required_names)}"
            )
    paths["config"] = config_path
    return paths


def build_checklist_freeze_snapshot(
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    source_bundle_path: str | Path = DEFAULT_SOURCE_BUNDLE,
    case_packet_root: str | Path = DEFAULT_CASE_PACKETS / "agentdojo",
    draft_root: str | Path = DEFAULT_DRAFT_ROOT,
    resolved_config_path: str | Path = DEFAULT_DRAFT_REVIEW_CONFIG,
    input_lock_path: str | Path = DEFAULT_DRAFT_INPUT_LOCK,
    budget_plan_path: str | Path = DEFAULT_DRAFT_BUDGET_PLAN,
    lifecycle_report_path: str | Path = DEFAULT_DRAFT_REVIEW_REPORT,
    lifecycle_index_path: str | Path = DEFAULT_DRAFT_REVIEW_INDEX,
    case_lock_path: str | Path = DEFAULT_CASE_CHECKLIST_LOCK,
    lock_acceptance_path: str | Path = DEFAULT_CASE_CHECKLIST_LOCK_ACCEPTANCE,
    score_prompt_path: str | Path = DEFAULT_SCORE_PROMPT,
    score_schema_path: str | Path = DEFAULT_SCORE_SCHEMA,
    agents_config_path: str | Path = DEFAULT_AGENTS_CONFIG,
    infra_config_path: str | Path = DEFAULT_INFRA_CONFIG,
    result_namespace_root: str | Path = DEFAULT_RESULT_NAMESPACE_LOCK.parent,
    score_result_roots: Sequence[str | Path] = DEFAULT_SCORE_NAMESPACE_ROOTS,
    expected_count: int = EXPECTED_CASE_COUNT,
    expected_suite_counts: Mapping[str, int] | None = EXPECTED_SUITE_COUNTS,
    expected_result_namespace: str = RESULT_NAMESPACE,
    require_empty_formal_outputs: bool = True,
    frozen_formal_output_precondition: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Recompute the complete checklist lifecycle and return its frozen digest graph.

    This function is intentionally read-only.  It verifies the same source,
    packet, checklist, review, and lock objects through independent paths and
    refuses to freeze after any formal result or score has appeared.
    """

    if expected_count <= 0:
        raise ContractLifecycleError("checklist freeze expected_count must be positive")
    if require_empty_formal_outputs and frozen_formal_output_precondition is not None:
        raise ContractLifecycleError(
            "a freeze-time output snapshot cannot be supplied to the empty-output gate"
        )
    if not require_empty_formal_outputs and frozen_formal_output_precondition is None:
        raise ContractLifecycleError(
            "post-freeze verification requires the frozen formal-output precondition"
        )
    strict_provenance = expected_count == EXPECTED_CASE_COUNT

    from neurips_ed_track_minimal.scripts import update_case_locks_batch as batch
    from neurips_ed_track_minimal.scripts.case_checklist_review import (
        review_agentdojo_checklist,
    )

    manifest_file = _require_regular_file(manifest_path, "checklist-freeze manifest")
    source_bundle_file = _require_regular_file(
        source_bundle_path, "checklist-freeze source bundle"
    )
    packet_root = _require_regular_directory(
        case_packet_root, "checklist-freeze packet root"
    )
    drafts = _require_regular_directory(draft_root, "checklist-freeze draft root")
    _reject_tree_symlinks(packet_root, "checklist-freeze packet root")
    _reject_tree_symlinks(drafts, "checklist-freeze draft root")
    config_file = _require_regular_file(resolved_config_path, "draft review config")
    input_lock_file = _require_regular_file(input_lock_path, "draft input lock")
    budget_file = _require_regular_file(budget_plan_path, "draft budget plan")
    report_file = _require_regular_file(lifecycle_report_path, "draft lifecycle report")
    index_file = _require_regular_file(lifecycle_index_path, "draft lifecycle index")
    case_lock_file = _require_regular_file(case_lock_path, "case checklist lock")
    lock_acceptance_file = _require_regular_file(
        lock_acceptance_path, "case checklist lock acceptance"
    )
    score_prompt_file = _require_regular_file(score_prompt_path, "score prompt")
    score_schema_file = _require_regular_file(score_schema_path, "score schema")
    agents_file = _require_regular_file(agents_config_path, "agents config")
    infra_file = _require_regular_file(infra_config_path, "infra config")
    report = _load_mapping(report_file, "draft lifecycle report")
    report_run_id = report.get("run_id")
    if not isinstance(report_run_id, str) or not report_run_id.strip():
        raise ContractLifecycleError("draft lifecycle report.run_id is missing")
    report_run_id = report_run_id.strip()

    try:
        manifest, cases = batch._load_manifest_cases(
            manifest_file,
            domain="agentdojo",
            expected_count=expected_count,
        )
        packets = batch._discover_packets(packet_root, expected_count)
    except batch.BatchCaseLockError as exc:
        raise ContractLifecycleError(str(exc)) from exc

    case_ids = [case.case_unit_id for case in cases]
    task_ids = [case.task_id for case in cases]
    if len(set(case_ids)) != expected_count:
        raise ContractLifecycleError("manifest case IDs are not unique")
    expected_packet_ids = set(case_ids)
    if set(packets) != expected_packet_ids:
        raise ContractLifecycleError("packet ID set does not exactly match manifest")
    for case in cases:
        if packets[case.case_unit_id].metadata != case:
            raise ContractLifecycleError(
                f"packet metadata differs from manifest for {case.case_unit_id}"
            )
    if expected_suite_counts is not None:
        observed_suite_counts = Counter(
            case.case_unit_id.split(":")[1] for case in cases
        )
        if dict(observed_suite_counts) != dict(expected_suite_counts):
            raise ContractLifecycleError(
                "manifest suite counts differ: "
                f"expected={dict(expected_suite_counts)}, actual={dict(observed_suite_counts)}"
            )

    if manifest.get("result_namespace") != expected_result_namespace:
        raise ContractLifecycleError(
            "manifest result namespace differs: "
            f"expected={expected_result_namespace!r}, actual={manifest.get('result_namespace')!r}"
        )
    if expected_count == EXPECTED_CASE_COUNT:
        manifest_schema_report = validate_object(
            "experiment_manifest", manifest, raise_on_error=False
        )
        if not manifest_schema_report.ok:
            raise ContractLifecycleError(
                "full manifest failed schema validation: "
                f"{manifest_schema_report.to_dict()}"
            )
    _assert_exact(
        manifest.get("source_bundle_hash"),
        sha256_file(source_bundle_file),
        "manifest source_bundle_hash",
    )
    _assert_exact(
        manifest.get("agents_config_hash"),
        sha256_file(agents_file),
        "manifest agents_config_hash",
    )
    _assert_exact(
        manifest.get("infra_config_hash"),
        sha256_file(infra_file),
        "manifest infra_config_hash",
    )
    try:
        source_bundle = batch._validate_source_bundle(
            source_bundle_file,
            manifest_path=manifest_file,
            manifest=manifest,
            cases=cases,
            packets=packets,
        )
    except batch.BatchCaseLockError as exc:
        raise ContractLifecycleError(str(exc)) from exc
    if expected_count == EXPECTED_CASE_COUNT:
        from evidence_system.cli.build_case_packet_source_bundle import (
            validate_source_bundle_strict,
        )

        deep_bundle_audit = validate_source_bundle_strict(
            source_bundle_path=source_bundle_file,
            manifest_path=manifest_file,
            case_packets_root=packet_root.parent,
            expected_cases=load_selected_case_units(manifest_file),
            expected_count=EXPECTED_CASE_COUNT,
            expected_domains=["agentdojo"],
        )
        expected_raw_case_file_hash_count = sum(
            len(
                _load_mapping(packet.raw_case_manifest_path, "raw case manifest").get(
                    "sha256_per_file"
                )
                or {}
            )
            for packet in packets.values()
        )
        if (
            deep_bundle_audit.get("verified_file_hash_count") != EXPECTED_CASE_COUNT * 2
            or deep_bundle_audit.get("verified_raw_case_file_hash_count")
            != expected_raw_case_file_hash_count
        ):
            raise ContractLifecycleError(
                f"source bundle deep audit is incomplete: {deep_bundle_audit}"
            )

    config = _load_mapping(config_file, "draft review config")
    config_paths = _validate_draft_review_config(
        config,
        expected_count=expected_count,
        config_path=config_file,
        case_lock_path=case_lock_file,
        lock_acceptance_path=lock_acceptance_file,
        score_prompt_path=score_prompt_file,
        score_schema_path=score_schema_file,
    )
    config_hash = sha256_file(config_file)
    lifecycle_hash = batch._sha256_object

    packet_index: list[dict[str, str]] = []
    packet_component_index: list[dict[str, str]] = []
    for case in cases:
        packet = packets[case.case_unit_id]
        raw_manifest_path = packet.raw_case_manifest_path
        raw_manifest = _load_mapping(raw_manifest_path, "raw case manifest")
        for field, expected in (
            ("case_unit_id", case.case_unit_id),
            ("task_id", case.task_id),
            ("domain", "agentdojo"),
        ):
            _assert_exact(
                raw_manifest.get(field), expected, f"raw case manifest {field}"
            )
        packet_files = {str(item) for item in raw_manifest.get("packet_files") or []}
        selected_relative = (
            "official/case_definition.json"
            if "official/case_definition.json" in packet_files
            else "derived/selected_task_source.json"
            if "derived/selected_task_source.json" in packet_files
            else "selected_task_source.json"
        )
        selected_source_path = (
            packet.case_packet_path.parent / "raw_case" / selected_relative
        )
        selected_source_path = _require_regular_file(
            selected_source_path, f"selected task source for {case.case_unit_id}"
        )
        suite = case.case_unit_id.split(":")[1]
        packet_index.append(
            {
                "case_unit_id": case.case_unit_id,
                "task_id": case.task_id,
                "suite": suite,
                "case_packet_path": _repo_relative(packet.case_packet_path),
                "case_packet_sha256": sha256_file(packet.case_packet_path),
                "raw_case_manifest_sha256": sha256_file(raw_manifest_path),
                "selected_task_source_sha256": sha256_file(selected_source_path),
            }
        )
        packet_component_index.append(
            {
                "case_unit_id": case.case_unit_id,
                "case_directory": _repo_relative(packet.case_packet_path.parent),
                "case_directory_tree_sha256": sha256_path(
                    packet.case_packet_path.parent
                ),
            }
        )

    input_lock = _load_mapping(input_lock_file, "draft input lock")
    _assert_exact(
        input_lock.get("schema_version"),
        "agentdojo_draft_input_lock/v1",
        "draft input lock schema_version",
    )
    manifest_binding = input_lock.get("manifest")
    source_binding = input_lock.get("source_bundle")
    if not isinstance(manifest_binding, Mapping) or not isinstance(
        source_binding, Mapping
    ):
        raise ContractLifecycleError(
            "draft input lock manifest/source bindings are missing"
        )
    _require_file_binding(
        manifest_binding,
        path_field="path",
        hash_field="sha256",
        expected_path=manifest_file,
        context="draft input lock.manifest",
    )
    _require_file_binding(
        source_binding,
        path_field="path",
        hash_field="sha256",
        expected_path=source_bundle_file,
        context="draft input lock.source_bundle",
    )
    _assert_exact(
        _resolve_declared_artifact_path(
            input_lock.get("case_packet_root"), "draft input lock.case_packet_root"
        ),
        packet_root,
        "draft input lock packet root",
    )
    _assert_exact(
        input_lock.get("case_count"), expected_count, "draft input lock case_count"
    )
    _assert_exact(
        input_lock.get("case_id_order_sha256"),
        lifecycle_hash(case_ids),
        "draft input lock case order hash",
    )
    _assert_exact(
        input_lock.get("case_id_set_sha256"),
        lifecycle_hash(sorted(case_ids)),
        "draft input lock case set hash",
    )
    _assert_exact(
        input_lock.get("packet_index"), packet_index, "draft input lock packet index"
    )
    _assert_exact(
        input_lock.get("packet_index_sha256"),
        lifecycle_hash(packet_index),
        "draft input lock packet index hash",
    )
    resolved_config_binding = input_lock.get("resolved_config")
    if not isinstance(resolved_config_binding, Mapping):
        raise ContractLifecycleError(
            "draft input lock resolved_config binding is missing"
        )
    _require_file_binding(
        resolved_config_binding,
        path_field="path",
        hash_field="sha256",
        expected_path=config_file,
        context="draft input lock.resolved_config",
    )
    _assert_exact(
        input_lock.get("reuse_audit"),
        {
            "strict_match_fields": [
                "case_packet_sha256",
                "draft_prompt_sha256",
                "checklist_schema_sha256",
                "checklist_sha256",
            ],
            "legacy_candidates": 100,
            "strictly_reusable": 0,
            "planned_new_drafts": expected_count,
        },
        "draft input lock reuse audit",
    )
    input_lock_time = _parse_aware_timestamp(
        input_lock.get("locked_at"), "draft input lock.locked_at"
    )
    input_lock_hash = sha256_file(input_lock_file)

    generation_batch_results: dict[str, dict[str, Any]] = {}
    generation_batch_component: dict[str, Any] = {}
    if strict_provenance:
        generation_batch_results, generation_batch_component = (
            _validate_generation_batch_provenance(
                drafts=drafts,
                cases=cases,
                packets=packets,
                config=config,
                config_paths=config_paths,
                input_lock_time=input_lock_time,
            )
        )

    budget = _load_mapping(budget_file, "draft budget plan")
    max_review_rounds = int(dict(config["review"])["max_rounds"])
    expected_budget = {
        "schema_version": "agentdojo_draft_budget/v1",
        "status": "planned",
        "denominator": expected_count,
        "strictly_reusable_legacy_drafts": 0,
        "new_drafts_required": expected_count,
        "max_parallel": 6,
        "minimum_generation_codex_exec_calls": expected_count,
        "maximum_generation_codex_exec_calls": expected_count * 4,
        "minimum_review_codex_exec_calls": expected_count,
        "maximum_review_codex_exec_calls": expected_count * max_review_rounds,
        "minimum_total_codex_exec_calls": expected_count * 2,
        "maximum_total_codex_exec_calls": expected_count * (4 + max_review_rounds),
        "generation_retry_labels": [12000, 16000, 20000, 24000],
        "codex_cli_output_token_cap_available": False,
        "max_review_rounds_per_case": max_review_rounds,
        "input_lock_sha256": input_lock_hash,
        "acceptance_targets": {
            "case_packets": expected_count,
            "source_entries": expected_count,
            "valid_drafts": expected_count,
            "reviewed_locked": expected_count,
            "unresolved_drafts": 0,
        },
    }
    comparable_budget = dict(budget)
    planned_at = comparable_budget.pop("planned_at", None)
    _require_aware_timestamp(planned_at, "draft budget plan.planned_at")
    _assert_exact(comparable_budget, expected_budget, "draft budget plan")
    budget_hash = sha256_file(budget_file)

    acceptance = _load_mapping(lock_acceptance_file, "case checklist lock acceptance")
    required_counts = {
        "manifest_cases": expected_count,
        "source_entries": expected_count,
        "case_packets": expected_count,
        "valid_drafts": expected_count,
        "reviewed": expected_count,
        "locked": expected_count,
        "unresolved_drafts": 0,
    }
    for field, expected in (
        ("schema_version", CHECKLIST_LOCK_ACCEPTANCE_SCHEMA_VERSION),
        ("status", "accepted"),
        ("domain", "agentdojo"),
        ("expected_count", expected_count),
        ("counts", required_counts),
        ("case_id_order_sha256", lifecycle_hash(case_ids)),
        ("case_id_set_sha256", lifecycle_hash(sorted(case_ids))),
        ("unresolved_drafts", []),
    ):
        _assert_exact(acceptance.get(field), expected, f"checklist acceptance {field}")
    for path_field, expected_path in (
        ("manifest_path", manifest_file),
        ("source_bundle_path", source_bundle_file),
        ("case_packet_root", packet_root),
        ("draft_root", drafts),
        ("lock_file_path", case_lock_file),
    ):
        _assert_exact(
            _resolve_declared_artifact_path(
                acceptance.get(path_field), f"acceptance.{path_field}"
            ),
            expected_path,
            f"checklist acceptance {path_field}",
        )
    _assert_exact(
        acceptance.get("manifest_sha256"),
        sha256_file(manifest_file),
        "acceptance manifest hash",
    )
    _assert_exact(
        acceptance.get("source_bundle_sha256"),
        sha256_file(source_bundle_file),
        "acceptance source bundle hash",
    )
    _assert_exact(
        acceptance.get("lock_file_sha256"),
        sha256_file(case_lock_file),
        "acceptance case lock hash",
    )
    writer_lock_path = _resolve_declared_artifact_path(
        acceptance.get("writer_lock_path"), "acceptance.writer_lock_path"
    )
    writer_lock_path = _require_regular_file(
        writer_lock_path, "case checklist writer lock"
    )
    _assert_exact(
        acceptance.get("writer_lock_sha256"),
        sha256_file(writer_lock_path),
        "acceptance writer lock hash",
    )

    acceptance_inputs = acceptance.get("inputs")
    if not isinstance(acceptance_inputs, Mapping):
        raise ContractLifecycleError("checklist acceptance inputs are missing")
    acceptance_input_paths = {
        "draft_prompt": config_paths["composed_draft_prompt"],
        "score_prompt": score_prompt_file,
        "review_prompt": config_paths["review_prompt"],
        "checklist_schema": config_paths["checklist_schema"],
        "score_schema": score_schema_file,
        "review_schema": config_paths["review_schema"],
    }
    for prefix, expected_path in acceptance_input_paths.items():
        _require_file_binding(
            acceptance_inputs,
            path_field=f"{prefix}_path",
            hash_field=f"{prefix}_sha256",
            expected_path=expected_path,
            context="checklist acceptance.inputs",
        )

    generation_config = dict(config["generation"])
    review_config = dict(config["review"])
    expected_reviewer_config = {
        "provider": "codex_cli",
        "auth_mode": "codex_login",
        "codex_cli_version": config["codex_cli_version"],
        "model": generation_config["model"],
        "reasoning_effort": generation_config["reasoning_effort"],
        "sandbox": review_config["sandbox"],
        "ephemeral": True,
        "ignore_user_config": True,
        "model_verbosity": "low",
        "timeout_seconds": review_config["timeout_seconds"],
    }
    _assert_exact(
        acceptance.get("reviewer_config"),
        expected_reviewer_config,
        "checklist acceptance reviewer config",
    )
    _assert_exact(
        acceptance.get("reviewer_config_sha256"),
        lifecycle_hash(expected_reviewer_config),
        "checklist acceptance reviewer config hash",
    )

    checklist_schema = _load_mapping(
        config_paths["checklist_schema"], "checklist schema"
    )
    review_schema = _load_mapping(config_paths["review_schema"], "review schema")
    score_schema = _load_mapping(score_schema_file, "score schema")
    try:
        Draft202012Validator.check_schema(checklist_schema)
        Draft202012Validator.check_schema(review_schema)
        Draft202012Validator.check_schema(score_schema)
    except Exception as exc:
        raise ContractLifecycleError(
            f"checklist/review/score JSON schema is invalid: {exc}"
        ) from exc
    checklist_validator = Draft202012Validator(checklist_schema)
    review_validator = Draft202012Validator(
        review_schema, format_checker=FormatChecker()
    )

    direct_draft_dirs = [path for path in drafts.iterdir() if path.is_dir()]
    if any(path.is_symlink() for path in direct_draft_dirs):
        raise ContractLifecycleError("draft root contains symlinked case directories")
    expected_draft_names = {
        packets[case_id].case_packet_path.parent.name for case_id in case_ids
    }
    actual_draft_names = {path.name for path in direct_draft_dirs}
    if actual_draft_names != expected_draft_names:
        raise ContractLifecycleError(
            "draft directory set differs: "
            f"missing={sorted(expected_draft_names - actual_draft_names)[:10]}, "
            f"extra={sorted(actual_draft_names - expected_draft_names)[:10]}"
        )

    case_lock_entries = _load_jsonl_mappings(case_lock_file, "case checklist lock")
    if len(case_lock_entries) != expected_count:
        raise ContractLifecycleError(
            f"case checklist lock count differs: expected={expected_count}, "
            f"actual={len(case_lock_entries)}"
        )
    _assert_exact(
        [entry.get("case_unit_id") for entry in case_lock_entries],
        case_ids,
        "case checklist lock order",
    )
    accepted_cases = acceptance.get("accepted_cases")
    if not isinstance(accepted_cases, list) or len(accepted_cases) != expected_count:
        raise ContractLifecycleError(
            "checklist acceptance accepted_cases has the wrong count"
        )

    index_entries: list[dict[str, Any]] = []
    checklist_component_index: list[dict[str, str]] = []
    generation_component_index: list[dict[str, Any]] = []
    review_component_index: list[dict[str, Any]] = []
    final_checklist_paths: set[Path] = set()
    final_review_paths: set[Path] = set()
    response_ids: set[str] = set()
    generation_response_ids: set[str] = set()
    for position, case in enumerate(cases):
        packet = packets[case.case_unit_id]
        case_dir = drafts / packet.case_packet_path.parent.name
        if case_dir.is_symlink():
            raise ContractLifecycleError(
                f"draft directory is a symlink: {case.case_unit_id}"
            )
        paths = {
            "checklist": case_dir / "checklist.yaml",
            "checklist_json": case_dir / "checklist.json",
            "generated_checklist": case_dir / "generated_checklist.yaml",
            "generated_checklist_json": case_dir / "generated_checklist.json",
            "generation": case_dir / "generation.json",
            "llm_call": case_dir / "llm_call.json",
            "api_response": case_dir / "api_response.json",
            "reasoning_summary": case_dir / "reasoning_summary.txt",
            "review": case_dir / "review.json",
            "review_lifecycle": case_dir / "review_lifecycle.json",
        }
        for label, path in paths.items():
            paths[label] = _require_regular_file(
                path, f"{label} for {case.case_unit_id}"
            )
        final_checklist_paths.add(paths["checklist"])
        final_review_paths.add(paths["review"])

        try:
            final_checklist = batch._validate_checklist(
                paths["checklist"],
                packet=packet,
                checklist_validator=checklist_validator,
            )
            generated_checklist = batch._validate_checklist(
                paths["generated_checklist"],
                packet=packet,
                checklist_validator=checklist_validator,
            )
        except batch.BatchCaseLockError as exc:
            raise ContractLifecycleError(str(exc)) from exc
        final_json = _load_mapping(paths["checklist_json"], "final checklist JSON")
        generated_json = _load_mapping(
            paths["generated_checklist_json"], "generated checklist JSON"
        )
        _assert_exact(
            final_json, final_checklist, "final checklist YAML/JSON semantics"
        )
        _assert_exact(
            generated_json,
            generated_checklist,
            "generated checklist YAML/JSON semantics",
        )
        deterministic_review = review_agentdojo_checklist(
            final_checklist,
            case_packet_path=packet.case_packet_path,
        )
        _assert_exact(
            deterministic_review,
            {"status": "pass", "findings": []},
            f"independently recomputed deterministic review {case.case_unit_id}",
        )

        generation = _load_mapping(paths["generation"], "generation receipt")
        generation_required = {
            "schema_version": "case_checklist_generation/v1",
            "case_unit_id": case.case_unit_id,
            "case_packet_sha256": sha256_file(packet.case_packet_path),
            "composed_draft_prompt_sha256": sha256_file(
                config_paths["composed_draft_prompt"]
            ),
            "checklist_schema_sha256": sha256_file(config_paths["checklist_schema"]),
            "resolved_config_sha256": config_hash,
            "input_lock_sha256": input_lock_hash,
            "provider": "codex_cli",
            "auth_mode": "codex_login",
            "model": "gpt-5.6-sol",
            "reasoning_effort": "xhigh",
        }
        for field, expected in generation_required.items():
            _assert_exact(
                generation.get(field),
                expected,
                f"generation {case.case_unit_id}.{field}",
            )
        for path_field, hash_field, expected_path in (
            ("case_packet_path", "case_packet_sha256", packet.case_packet_path),
            ("checklist_path", "checklist_sha256", paths["generated_checklist"]),
            (
                "checklist_json_path",
                "checklist_json_sha256",
                paths["generated_checklist_json"],
            ),
            ("llm_call_path", "llm_call_sha256", paths["llm_call"]),
            ("api_response_path", "api_response_sha256", paths["api_response"]),
            (
                "reasoning_summary_path",
                "reasoning_summary_sha256",
                paths["reasoning_summary"],
            ),
            (
                "composed_draft_prompt_path",
                "composed_draft_prompt_sha256",
                config_paths["composed_draft_prompt"],
            ),
            (
                "checklist_schema_path",
                "checklist_schema_sha256",
                config_paths["checklist_schema"],
            ),
        ):
            _require_file_binding(
                generation,
                path_field=path_field,
                hash_field=hash_field,
                expected_path=expected_path,
                context=f"generation receipt {case.case_unit_id}",
            )
        llm_call = _load_mapping(paths["llm_call"], "generation llm call")
        for field, expected in (
            ("schema_version", "llm_call/v1"),
            ("provider", "codex_cli"),
            ("case_unit_id", case.case_unit_id),
            ("model", "gpt-5.6-sol"),
        ):
            _assert_exact(llm_call.get(field), expected, f"generation llm_call.{field}")
        response_metadata = llm_call.get("response_metadata")
        if not isinstance(response_metadata, Mapping):
            raise ContractLifecycleError(
                f"generation response metadata is missing: {case.case_unit_id}"
            )
        for field, expected in (
            ("auth_mode", "codex_login"),
            ("reasoning_effort", "xhigh"),
            ("max_output_tokens_enforced", False),
        ):
            _assert_exact(
                response_metadata.get(field),
                expected,
                f"generation response metadata.{field}",
            )

        strict_generation_component: dict[str, Any] = {}
        if strict_provenance:
            strict_generation_component = _validate_generation_case_provenance(
                case=case,
                packet=packet,
                case_dir=case_dir,
                paths=paths,
                batch_result=generation_batch_results[case_dir.name],
                config=config,
                config_paths=config_paths,
                input_lock_time=input_lock_time,
                response_ids=response_ids,
            )
            response_id = str(strict_generation_component["response_id"])
            if response_id in generation_response_ids:
                raise ContractLifecycleError(
                    f"duplicate generation response id: {response_id}"
                )
            generation_response_ids.add(response_id)

        try:
            review = batch._validate_review(
                paths["review"],
                case_unit_id=case.case_unit_id,
                packet_path=packet.case_packet_path,
                checklist_path=paths["checklist"],
                draft_prompt_path=config_paths["composed_draft_prompt"],
                checklist_schema_path=config_paths["checklist_schema"],
                review_prompt_path=config_paths["review_prompt"],
                review_schema_path=config_paths["review_schema"],
                review_validator=review_validator,
            )
        except batch.BatchCaseLockError as exc:
            raise ContractLifecycleError(str(exc)) from exc
        _assert_exact(
            review.get("reviewer_config"),
            expected_reviewer_config,
            f"reviewer config for {case.case_unit_id}",
        )
        _assert_exact(
            review.get("deterministic_review"),
            deterministic_review,
            f"review deterministic binding for {case.case_unit_id}",
        )
        lifecycle = _load_mapping(paths["review_lifecycle"], "review lifecycle receipt")
        for field, expected in (
            ("schema_version", "case_checklist_review_lifecycle/v1"),
            ("case_unit_id", case.case_unit_id),
            ("status", "accepted"),
            ("final_checklist_sha256", sha256_file(paths["checklist"])),
            ("final_review_sha256", sha256_file(paths["review"])),
        ):
            _assert_exact(lifecycle.get(field), expected, f"review lifecycle.{field}")
        if not isinstance(lifecycle.get("revised"), bool):
            raise ContractLifecycleError(
                f"review lifecycle revised flag invalid: {case.case_unit_id}"
            )
        if (
            not isinstance(lifecycle.get("review_rounds"), int)
            or int(lifecycle["review_rounds"]) < 0
        ):
            raise ContractLifecycleError(
                f"review lifecycle rounds invalid: {case.case_unit_id}"
            )
        if not isinstance(lifecycle.get("attempts"), list):
            raise ContractLifecycleError(
                f"review lifecycle attempts invalid: {case.case_unit_id}"
            )
        if len(lifecycle["attempts"]) != lifecycle["review_rounds"]:
            raise ContractLifecycleError(
                f"review lifecycle attempt count differs from rounds: {case.case_unit_id}"
            )
        if lifecycle["revised"] is True and lifecycle["review_rounds"] < 2:
            raise ContractLifecycleError(
                f"revised checklist lacks a fresh review round: {case.case_unit_id}"
            )
        expected_revised = sha256_file(paths["generated_checklist"]) != sha256_file(
            paths["checklist"]
        )
        _assert_exact(
            lifecycle["revised"],
            expected_revised,
            f"review lifecycle revised/hash equivalence {case.case_unit_id}",
        )
        strict_review_component: dict[str, Any] = {}
        if strict_provenance:
            strict_review_component = _validate_review_case_provenance(
                case=case,
                packet=packet,
                case_dir=case_dir,
                generated_checklist_path=paths["generated_checklist"],
                final_checklist_path=paths["checklist"],
                review_receipt=review,
                lifecycle=lifecycle,
                report_run_id=report_run_id,
                config=config,
                config_paths=config_paths,
                review_schema=review_schema,
                checklist_validator=checklist_validator,
                input_lock_time=input_lock_time,
                response_ids=response_ids,
            )

        expected_accepted_case = {
            "case_unit_id": case.case_unit_id,
            "case_packet_sha256": sha256_file(packet.case_packet_path),
            "raw_case_manifest_sha256": sha256_file(packet.raw_case_manifest_path),
            "checklist_sha256": sha256_file(paths["checklist"]),
            "review_sha256": sha256_file(paths["review"]),
        }
        _assert_exact(
            accepted_cases[position],
            expected_accepted_case,
            f"accepted case {case.case_unit_id}",
        )
        try:
            recomputed_lock_entry = batch.case_locks.build_lock_entry(
                case_packet_path=packet.case_packet_path,
                checklist_path=paths["checklist"],
                draft_prompt_path=config_paths["composed_draft_prompt"],
                score_prompt_path=score_prompt_file,
                checklist_schema_path=config_paths["checklist_schema"],
                score_schema_path=score_schema_file,
            )
        except batch.case_locks.CaseLockError as exc:
            raise ContractLifecycleError(str(exc)) from exc
        _assert_exact(
            case_lock_entries[position],
            recomputed_lock_entry,
            f"recomputed case checklist lock {case.case_unit_id}",
        )

        entry = {
            "case_unit_id": case.case_unit_id,
            "task_id": case.task_id,
            "suite": case.case_unit_id.split(":")[1],
            "case_packet_path": _repo_relative(packet.case_packet_path),
            "case_packet_sha256": sha256_file(packet.case_packet_path),
            "generated_checklist_path": _repo_relative(paths["generated_checklist"]),
            "generated_checklist_sha256": sha256_file(paths["generated_checklist"]),
            "generation_receipt_path": _repo_relative(paths["generation"]),
            "generation_receipt_sha256": sha256_file(paths["generation"]),
            "checklist_path": _repo_relative(paths["checklist"]),
            "checklist_sha256": sha256_file(paths["checklist"]),
            "checklist_json_path": _repo_relative(paths["checklist_json"]),
            "checklist_json_sha256": sha256_file(paths["checklist_json"]),
            "review_path": _repo_relative(paths["review"]),
            "review_sha256": sha256_file(paths["review"]),
            "review_lifecycle_path": _repo_relative(paths["review_lifecycle"]),
            "review_lifecycle_sha256": sha256_file(paths["review_lifecycle"]),
            "revised": lifecycle["revised"],
            "review_rounds": lifecycle["review_rounds"],
        }
        index_entries.append(entry)
        checklist_component_index.append(
            {
                "case_unit_id": case.case_unit_id,
                "generated_yaml_sha256": sha256_file(paths["generated_checklist"]),
                "generated_json_sha256": sha256_file(paths["generated_checklist_json"]),
                "final_yaml_sha256": sha256_file(paths["checklist"]),
                "final_json_sha256": sha256_file(paths["checklist_json"]),
            }
        )
        generation_component_index.append(
            {
                "case_unit_id": case.case_unit_id,
                "generation_sha256": sha256_file(paths["generation"]),
                "llm_call_sha256": sha256_file(paths["llm_call"]),
                "api_response_sha256": sha256_file(paths["api_response"]),
                "reasoning_summary_sha256": sha256_file(paths["reasoning_summary"]),
                **strict_generation_component,
            }
        )
        review_component_index.append(
            {
                "case_unit_id": case.case_unit_id,
                "review_sha256": sha256_file(paths["review"]),
                "review_lifecycle_sha256": sha256_file(paths["review_lifecycle"]),
                **strict_review_component,
            }
        )

    if strict_provenance:
        _assert_exact(
            len(generation_response_ids),
            expected_count,
            "unique fresh generation response-id denominator",
        )

    discovered_checklists = {path.resolve() for path in drafts.glob("*/checklist.yaml")}
    discovered_reviews = {path.resolve() for path in drafts.glob("*/review.json")}
    _assert_exact(
        discovered_checklists, final_checklist_paths, "final checklist file set"
    )
    _assert_exact(discovered_reviews, final_review_paths, "final review file set")
    _assert_exact(
        acceptance.get("accepted_cases_sha256"),
        lifecycle_hash(accepted_cases),
        "checklist acceptance accepted cases hash",
    )

    lifecycle_index = _load_mapping(index_file, "draft lifecycle index")
    expected_index = {
        "schema_version": "agentdojo_draft_review_index/v1",
        "mode": "full",
        "case_count": expected_count,
        "full_denominator": expected_count,
        "case_id_order_sha256": lifecycle_hash(case_ids),
        "case_id_set_sha256": lifecycle_hash(sorted(case_ids)),
        "entries_sha256": lifecycle_hash(index_entries),
        "resolved_config_sha256": config_hash,
        "input_lock_sha256": input_lock_hash,
        "entries": index_entries,
    }
    comparable_index = dict(lifecycle_index)
    frozen_at = comparable_index.pop("frozen_at", None)
    _require_aware_timestamp(frozen_at, "draft lifecycle index.frozen_at")
    _assert_exact(comparable_index, expected_index, "draft lifecycle index")
    index_hash = sha256_file(index_file)

    expected_report_counts = {
        "case_packets": expected_count,
        "source_entries": expected_count,
        "valid_drafts": expected_count,
        "reviewed": expected_count,
        "lock_eligible": expected_count,
        "locked": expected_count,
        "unresolved_drafts": 0,
    }
    for field, expected in (
        ("schema_version", "agentdojo_draft_review_report/v1"),
        ("mode", "full"),
        ("status", "accepted_and_locked"),
        ("full_denominator", expected_count),
        ("selected_case_count", expected_count),
        ("max_parallel", 6),
        ("resolved_config_sha256", config_hash),
        ("input_lock_sha256", input_lock_hash),
        ("budget_plan_sha256", budget_hash),
        ("counts", expected_report_counts),
        ("unresolved_drafts", []),
        ("lock_file_sha256", sha256_file(case_lock_file)),
        ("lock_acceptance_sha256", sha256_file(lock_acceptance_file)),
        ("index_sha256", index_hash),
    ):
        _assert_exact(report.get(field), expected, f"draft lifecycle report.{field}")
    _assert_exact(report.get("run_id"), report_run_id, "draft lifecycle report.run_id")
    for field in ("started_at", "finished_at"):
        _require_aware_timestamp(report.get(field), f"draft lifecycle report.{field}")
    for field, expected_path in (
        ("lock_file_path", case_lock_file),
        ("lock_acceptance_path", lock_acceptance_file),
        ("index_path", index_file),
    ):
        _assert_exact(
            _resolve_declared_artifact_path(report.get(field), f"draft report.{field}"),
            expected_path,
            f"draft lifecycle report.{field}",
        )
    review_results = report.get("review_results")
    if not isinstance(review_results, list) or len(review_results) != expected_count:
        raise ContractLifecycleError(
            "draft lifecycle review_results has the wrong count"
        )
    _assert_exact(
        [
            str(item.get("case_unit_id") or "")
            for item in review_results
            if isinstance(item, Mapping)
        ],
        case_ids,
        "draft lifecycle review result order",
    )
    for position, item in enumerate(review_results):
        if not isinstance(item, Mapping) or item.get("status") not in {
            "accepted",
            "reused_review",
        }:
            raise ContractLifecycleError(
                "draft lifecycle contains a non-accepted review result"
            )
        if item.get("status") == "accepted":
            _assert_exact(
                item.get("review_rounds"),
                index_entries[position]["review_rounds"],
                f"review result rounds for {case_ids[position]}",
            )
            _assert_exact(
                item.get("revised"),
                index_entries[position]["revised"],
                f"review result revised flag for {case_ids[position]}",
            )
        else:
            if strict_provenance:
                raise ContractLifecycleError(
                    "production freeze forbids reused reviews; every accepted review "
                    "must bind the active report run"
                )
            _assert_exact(
                item.get("review_rounds"),
                0,
                f"reused review rounds for {case_ids[position]}",
            )
            _assert_exact(
                item.get("revised"),
                False,
                f"reused review revised flag for {case_ids[position]}",
            )

    contract_locks = manifest.get("contract_locks")
    if not isinstance(contract_locks, list):
        raise ContractLifecycleError("manifest contract_locks must remain a list")
    _assert_exact(
        contract_locks,
        [],
        "manifest evidence-contract locks at checklist freeze boundary",
    )
    domain = next(
        block
        for block in manifest["domains"]
        if isinstance(block, Mapping) and block.get("domain") == "agentdojo"
    )
    case_status_counts = Counter(
        str(item.get("contract_lock_status") or "missing")
        for item in domain.get("case_units") or []
        if isinstance(item, Mapping)
    )
    _assert_exact(
        case_status_counts,
        Counter({"draft_required": expected_count}),
        "manifest case evidence-contract status boundary",
    )

    namespace_root = Path(result_namespace_root).expanduser().resolve()
    namespace_marker = _load_mapping(
        namespace_root / "NAMESPACE_LOCK.json", "result namespace marker"
    )
    _assert_exact(
        namespace_marker.get("result_namespace"),
        expected_result_namespace,
        "result namespace marker identity",
    )
    _assert_exact(
        namespace_marker.get("legacy_result_root_must_not_be_modified"),
        True,
        "result namespace legacy isolation flag",
    )
    if require_empty_formal_outputs:
        result_snapshot = _empty_output_snapshot(
            namespace_root,
            label="formal result namespace",
            allowed_files=("NAMESPACE_LOCK.json",),
        )
        score_snapshots = [
            _empty_output_snapshot(path, label=f"formal scoring namespace[{index}]")
            for index, path in enumerate(score_result_roots)
        ]
        formal_output_precondition = {
            "result_namespace": result_snapshot,
            "score_namespaces": score_snapshots,
            "formal_results_and_scores_are_empty": True,
        }
    else:
        assert frozen_formal_output_precondition is not None
        formal_output_precondition = _validate_frozen_formal_output_precondition(
            frozen_formal_output_precondition,
            result_namespace_root=namespace_root,
            score_result_roots=score_result_roots,
        )

    missing_runtime_paths = [
        path for path in LOCKED_RUNTIME_PATHS if not resolve_repo_path(path).is_file()
    ]
    if missing_runtime_paths:
        raise ContractLifecycleError(
            f"required locked runtime files are missing: {missing_runtime_paths}"
        )
    runtime_hashes = {
        path: sha256_file(resolve_repo_path(path)) for path in LOCKED_RUNTIME_PATHS
    }
    snapshot = {
        "schema_version": CHECKLIST_FREEZE_SCHEMA_VERSION,
        "status": "accepted_for_final_freeze",
        "expected_count": expected_count,
        "counts": {
            "case_packets": expected_count,
            "source_entries": len(source_bundle["sources"]),
            "valid_drafts": len(index_entries),
            "reviewed": len(review_component_index),
            "locked": len(case_lock_entries),
            "unresolved_drafts": 0,
        },
        "case_identity": {
            "case_id_order_sha256": lifecycle_hash(case_ids),
            "case_id_set_sha256": lifecycle_hash(sorted(case_ids)),
            "task_id_order_sha256": lifecycle_hash(task_ids),
            "suite_case_counts": dict(
                expected_suite_counts
                or Counter(case_id.split(":")[1] for case_id in case_ids)
            ),
        },
        "inputs": {
            "manifest": {
                "path": _repo_relative(manifest_file),
                "sha256": sha256_file(manifest_file),
            },
            "source_bundle": {
                "path": _repo_relative(source_bundle_file),
                "sha256": sha256_file(source_bundle_file),
            },
            "case_packet_root": {
                "path": _repo_relative(packet_root),
                "tree_sha256": sha256_path(packet_root),
            },
            "draft_root": {
                "path": _repo_relative(drafts),
                "tree_sha256": sha256_path(drafts),
            },
            "resolved_config": {
                "path": _repo_relative(config_file),
                "sha256": config_hash,
            },
            "draft_input_lock": {
                "path": _repo_relative(input_lock_file),
                "sha256": input_lock_hash,
            },
            "draft_budget_plan": {
                "path": _repo_relative(budget_file),
                "sha256": budget_hash,
            },
            "draft_review_report": {
                "path": _repo_relative(report_file),
                "sha256": sha256_file(report_file),
            },
            "draft_review_index": {
                "path": _repo_relative(index_file),
                "sha256": index_hash,
            },
            "case_checklist_lock": {
                "path": _repo_relative(case_lock_file),
                "sha256": sha256_file(case_lock_file),
            },
            "case_checklist_lock_acceptance": {
                "path": _repo_relative(lock_acceptance_file),
                "sha256": sha256_file(lock_acceptance_file),
            },
            "score_prompt": {
                "path": _repo_relative(score_prompt_file),
                "sha256": sha256_file(score_prompt_file),
            },
            "score_schema": {
                "path": _repo_relative(score_schema_file),
                "sha256": sha256_file(score_schema_file),
            },
            "agents_config": {
                "path": _repo_relative(agents_file),
                "sha256": sha256_file(agents_file),
            },
            "infra_config": {
                "path": _repo_relative(infra_file),
                "sha256": sha256_file(infra_file),
            },
            "generation_batch": generation_batch_component,
        },
        "component_index_sha256": {
            "case_packets": lifecycle_hash(packet_component_index),
            "checklists": lifecycle_hash(checklist_component_index),
            "generation": lifecycle_hash(generation_component_index),
            "reviews": lifecycle_hash(review_component_index),
            "draft_review_index_entries": lifecycle_hash(index_entries),
            "case_checklist_lock_entries": lifecycle_hash(case_lock_entries),
        },
        "drafting_configuration": {
            "provider": "codex_cli",
            "auth_mode": "codex_login",
            "model": "gpt-5.6-sol",
            "reasoning_effort": "xhigh",
            "sandbox": "read-only",
            "max_parallel": 6,
            "codex_cli_version": config["codex_cli_version"],
            "reviewer_config_sha256": lifecycle_hash(expected_reviewer_config),
        },
        "evidence_contract_boundary": {
            "checklist_lock_kind": "case_checklist_lock",
            "checklist_locks_are_evidence_contract_locks": False,
            "manifest_evidence_contract_lock_count": len(contract_locks),
            "manifest_evidence_contract_locks_sha256": lifecycle_hash(contract_locks),
            "manifest_case_contract_status_counts": dict(
                sorted(case_status_counts.items())
            ),
        },
        "formal_output_precondition": formal_output_precondition,
        "runtime_code_sha256": runtime_hashes,
    }
    _assert_exact(
        snapshot["counts"],
        {
            "case_packets": expected_count,
            "source_entries": expected_count,
            "valid_drafts": expected_count,
            "reviewed": expected_count,
            "locked": expected_count,
            "unresolved_drafts": 0,
        },
        "final checklist freeze denominator",
    )
    if "acceptance_report" in json.dumps(snapshot, sort_keys=True):
        raise ContractLifecycleError(
            "the final acceptance_report must not be included in its own checklist-freeze inputs"
        )
    return snapshot


def publish_checklist_freeze_lock(
    *,
    snapshot: Mapping[str, Any],
    base_definition: Mapping[str, Any],
    output_path: str | Path,
    replace_stale_lock: bool = False,
    expected_previous_lock_sha256: str | None = None,
    locked_at: str | None = None,
) -> ChecklistFreezeResult:
    """Atomically publish a v2 lock, requiring an exact CAS token for replacement."""

    if snapshot.get("schema_version") != CHECKLIST_FREEZE_SCHEMA_VERSION:
        raise ContractLifecycleError("invalid checklist-freeze snapshot schema")
    expected_count = snapshot.get("expected_count")
    if not isinstance(expected_count, int) or expected_count <= 0:
        raise ContractLifecycleError("invalid checklist-freeze expected_count")
    _assert_exact(
        snapshot.get("counts"),
        {
            "case_packets": expected_count,
            "source_entries": expected_count,
            "valid_drafts": expected_count,
            "reviewed": expected_count,
            "locked": expected_count,
            "unresolved_drafts": 0,
        },
        "publishable checklist-freeze denominator",
    )
    formal_output = snapshot.get("formal_output_precondition")
    if (
        not isinstance(formal_output, Mapping)
        or formal_output.get("formal_results_and_scores_are_empty") is not True
    ):
        raise ContractLifecycleError(
            "checklist freeze cannot publish after formal output exists"
        )
    _recheck_empty_formal_outputs(formal_output)
    output_file = Path(output_path).expanduser().resolve()
    desired_definition = {
        **dict(base_definition),
        "lock_revision": "checklist-freeze-v1",
        "checklist_freeze": dict(snapshot),
    }
    replaced = False
    compare_and_swap_hash: str | None = None
    if output_file.exists():
        if output_file.is_symlink():
            raise ContractLifecycleError(
                f"experiment lock output is a symlink: {output_file}"
            )
        existing = _load_mapping(output_file, "existing experiment lock")
        current_hash = sha256_file(output_file)
        existing_definition = {
            key: value
            for key, value in existing.items()
            if key
            not in {
                "schema_version",
                "lock_id",
                "lock_status",
                "locked_at",
                "definition_sha256",
            }
        }
        comparable_existing = dict(existing_definition)
        comparable_existing.pop("supersedes_lock_sha256", None)
        if (
            existing.get("schema_version") == CHECKLIST_FREEZE_LOCK_SCHEMA_VERSION
            and existing.get("lock_id") == "agentdojo_full_v1.2.2_direct"
            and existing.get("lock_status") == "locked"
            and _require_aware_timestamp(
                existing.get("locked_at"), "existing lock.locked_at"
            )
            and sha256_object(existing_definition) == existing.get("definition_sha256")
            and comparable_existing == desired_definition
        ):
            return ChecklistFreezeResult(
                lock_path=output_file,
                lock_sha256=current_hash,
                replaced=False,
                snapshot=dict(snapshot),
            )
        if not replace_stale_lock:
            raise ContractLifecycleError(
                "experiment lock is stale; replacement requires --replace-stale-lock and the "
                "exact previous SHA-256"
            )
        if not expected_previous_lock_sha256:
            raise ContractLifecycleError(
                "expected_previous_lock_sha256 is required when replacing a stale lock"
            )
        if expected_previous_lock_sha256 != current_hash:
            raise ContractLifecycleError(
                "stale-lock compare-and-swap failed: "
                f"expected={expected_previous_lock_sha256}, actual={current_hash}"
            )
        desired_definition["supersedes_lock_sha256"] = current_hash
        replaced = True
        compare_and_swap_hash = current_hash
    elif replace_stale_lock or expected_previous_lock_sha256 is not None:
        raise ContractLifecycleError(
            "stale-lock replacement was requested but no prior lock exists"
        )

    timestamp = _require_aware_timestamp(
        locked_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "experiment lock.locked_at",
    )
    payload = {
        "schema_version": CHECKLIST_FREEZE_LOCK_SCHEMA_VERSION,
        "lock_id": "agentdojo_full_v1.2.2_direct",
        "lock_status": "locked",
        "locked_at": timestamp,
        **desired_definition,
        "definition_sha256": sha256_object(desired_definition),
    }
    if compare_and_swap_hash is not None:
        current_hash = sha256_file(output_file) if output_file.is_file() else None
        if current_hash != compare_and_swap_hash:
            raise ContractLifecycleError(
                "stale-lock compare-and-swap changed before atomic publication: "
                f"expected={compare_and_swap_hash}, actual={current_hash}"
            )
    elif output_file.exists():
        raise ContractLifecycleError(
            "experiment lock appeared before atomic creation; rerun with explicit replacement"
        )
    _recheck_empty_formal_outputs(formal_output)
    _atomic_write_json(output_file, payload)
    readback = _load_mapping(output_file, "published experiment lock")
    if readback != payload:
        raise ContractLifecycleError(
            "atomic experiment-lock readback differs from staged payload"
        )
    return ChecklistFreezeResult(
        lock_path=output_file,
        lock_sha256=sha256_file(output_file),
        replaced=replaced,
        snapshot=dict(snapshot),
    )


def freeze_agentdojo_full_checklists(
    *,
    output_path: str | Path = DEFAULT_LOCK,
    replace_stale_lock: bool = False,
    expected_previous_lock_sha256: str | None = None,
    locked_at: str | None = None,
    **snapshot_overrides: Any,
) -> ChecklistFreezeResult:
    """Validate twice, then atomically publish the production 949-case final lock."""

    normalized_overrides = _production_snapshot_overrides(snapshot_overrides)
    normalized_overrides["require_empty_formal_outputs"] = True
    snapshot = build_checklist_freeze_snapshot(**normalized_overrides)
    packet_direct_root = Path(
        normalized_overrides.get("case_packet_root", DEFAULT_CASE_PACKETS / "agentdojo")
    ).expanduser()
    definition = _build_experiment_definition(
        candidates_path=DEFAULT_CANDIDATES,
        catalog_path=DEFAULT_CATALOG,
        manifest_path=normalized_overrides.get("manifest_path", DEFAULT_MANIFEST),
        source_bundle_path=normalized_overrides.get(
            "source_bundle_path", DEFAULT_SOURCE_BUNDLE
        ),
        case_packets_root=packet_direct_root.parent,
        agents_config_path=normalized_overrides.get(
            "agents_config_path", DEFAULT_AGENTS_CONFIG
        ),
        infra_config_path=normalized_overrides.get(
            "infra_config_path", DEFAULT_INFRA_CONFIG
        ),
    )
    second_snapshot = build_checklist_freeze_snapshot(**normalized_overrides)
    second_definition = _build_experiment_definition(
        candidates_path=DEFAULT_CANDIDATES,
        catalog_path=DEFAULT_CATALOG,
        manifest_path=normalized_overrides.get("manifest_path", DEFAULT_MANIFEST),
        source_bundle_path=normalized_overrides.get(
            "source_bundle_path", DEFAULT_SOURCE_BUNDLE
        ),
        case_packets_root=packet_direct_root.parent,
        agents_config_path=normalized_overrides.get(
            "agents_config_path", DEFAULT_AGENTS_CONFIG
        ),
        infra_config_path=normalized_overrides.get(
            "infra_config_path", DEFAULT_INFRA_CONFIG
        ),
    )
    if snapshot != second_snapshot or definition != second_definition:
        raise ContractLifecycleError("freeze inputs changed between validation passes")
    return publish_checklist_freeze_lock(
        snapshot=snapshot,
        base_definition=definition,
        output_path=output_path,
        replace_stale_lock=replace_stale_lock,
        expected_previous_lock_sha256=expected_previous_lock_sha256,
        locked_at=locked_at,
    )


def verify_checklist_freeze_lock(
    *,
    lock_path: str | Path = DEFAULT_LOCK,
    **snapshot_overrides: Any,
) -> ChecklistFreezeResult:
    """Recompute every final-freeze input and compare it with an existing v2 lock."""

    lock_file = _require_regular_file(
        lock_path, "final checklist-freeze experiment lock"
    )
    lock = _load_mapping(lock_file, "final checklist-freeze experiment lock")
    if lock.get("schema_version") != CHECKLIST_FREEZE_LOCK_SCHEMA_VERSION:
        raise ContractLifecycleError(
            f"final experiment lock must use {CHECKLIST_FREEZE_LOCK_SCHEMA_VERSION}"
        )
    if lock.get("lock_status") != "locked":
        raise ContractLifecycleError("final experiment lock is not locked")
    if lock.get("lock_id") != "agentdojo_full_v1.2.2_direct":
        raise ContractLifecycleError("final experiment lock_id is invalid")
    _require_aware_timestamp(lock.get("locked_at"), "final experiment lock.locked_at")
    definition = {
        key: value
        for key, value in lock.items()
        if key
        not in {
            "schema_version",
            "lock_id",
            "lock_status",
            "locked_at",
            "definition_sha256",
        }
    }
    if sha256_object(definition) != lock.get("definition_sha256"):
        raise ContractLifecycleError("final experiment lock definition hash is stale")
    locked_snapshot = definition.get("checklist_freeze")
    if not isinstance(locked_snapshot, Mapping):
        raise ContractLifecycleError("final experiment lock has no checklist snapshot")
    locked_formal_precondition = locked_snapshot.get("formal_output_precondition")
    if not isinstance(locked_formal_precondition, Mapping):
        raise ContractLifecycleError(
            "final experiment lock has no formal-output precondition"
        )
    normalized_overrides = _production_snapshot_overrides(snapshot_overrides)
    normalized_overrides.update(
        {
            "require_empty_formal_outputs": False,
            "frozen_formal_output_precondition": locked_formal_precondition,
        }
    )
    snapshot = build_checklist_freeze_snapshot(**normalized_overrides)
    _assert_exact(
        definition.get("lock_revision"), "checklist-freeze-v1", "lock revision"
    )
    _assert_exact(
        definition.get("checklist_freeze"), snapshot, "checklist-freeze snapshot"
    )
    supersedes = definition.get("supersedes_lock_sha256")
    if supersedes is not None and (
        not isinstance(supersedes, str)
        or re.fullmatch(r"[0-9a-f]{64}", supersedes) is None
    ):
        raise ContractLifecycleError("supersedes_lock_sha256 is invalid")
    comparable_definition = dict(definition)
    comparable_definition.pop("lock_revision", None)
    comparable_definition.pop("checklist_freeze", None)
    comparable_definition.pop("supersedes_lock_sha256", None)
    packet_direct_root = Path(
        normalized_overrides.get("case_packet_root", DEFAULT_CASE_PACKETS / "agentdojo")
    ).expanduser()
    expected_definition = _build_experiment_definition(
        candidates_path=DEFAULT_CANDIDATES,
        catalog_path=DEFAULT_CATALOG,
        manifest_path=normalized_overrides.get("manifest_path", DEFAULT_MANIFEST),
        source_bundle_path=normalized_overrides.get(
            "source_bundle_path", DEFAULT_SOURCE_BUNDLE
        ),
        case_packets_root=packet_direct_root.parent,
        agents_config_path=normalized_overrides.get(
            "agents_config_path", DEFAULT_AGENTS_CONFIG
        ),
        infra_config_path=normalized_overrides.get(
            "infra_config_path", DEFAULT_INFRA_CONFIG
        ),
    )
    _assert_exact(
        comparable_definition, expected_definition, "base experiment definition"
    )
    return ChecklistFreezeResult(
        lock_path=lock_file,
        lock_sha256=sha256_file(lock_file),
        replaced=False,
        snapshot=snapshot,
    )


def verify_full_experiment(
    *,
    lock_path: str | Path = DEFAULT_LOCK,
    acceptance_output_path: str | Path = DEFAULT_ACCEPTANCE,
) -> Path:
    """Fail closed unless the complete 949-case artifact graph matches its lock."""

    lock_file = resolve_repo_path(lock_path)
    lock = _load_mapping(lock_file, "experiment lock")
    checks: list[dict[str, Any]] = []

    def require(condition: bool, check: str, detail: Any) -> None:
        if not condition:
            raise ContractLifecycleError(f"acceptance check failed [{check}]: {detail}")
        checks.append({"check": check, "status": "pass", "detail": detail})

    require(lock.get("lock_status") == "locked", "lock_status", lock.get("lock_status"))
    definition = {
        key: value
        for key, value in lock.items()
        if key
        not in {
            "schema_version",
            "lock_id",
            "lock_status",
            "locked_at",
            "definition_sha256",
        }
    }
    require(
        sha256_object(definition) == lock.get("definition_sha256"),
        "lock_definition_hash",
        lock.get("definition_sha256"),
    )
    require(
        lock.get("schema_version") == CHECKLIST_FREEZE_LOCK_SCHEMA_VERSION,
        "final_checklist_freeze_lock_schema",
        lock.get("schema_version"),
    )
    checklist_freeze = verify_checklist_freeze_lock(lock_path=lock_file)
    require(
        checklist_freeze.snapshot.get("counts")
        == {
            "case_packets": EXPECTED_CASE_COUNT,
            "source_entries": EXPECTED_CASE_COUNT,
            "valid_drafts": EXPECTED_CASE_COUNT,
            "reviewed": EXPECTED_CASE_COUNT,
            "locked": EXPECTED_CASE_COUNT,
            "unresolved_drafts": 0,
        },
        "final_checklist_freeze_denominator",
        checklist_freeze.snapshot.get("counts"),
    )
    benchmark = dict(lock.get("benchmark") or {})
    required_benchmark = {
        "package_version": AGENTDOJO_PACKAGE_VERSION,
        "official_tag": AGENTDOJO_TAG,
        "git_commit": AGENTDOJO_COMMIT,
        "git_tree": AGENTDOJO_TREE,
        "benchmark_version": BENCHMARK_VERSION,
        "distribution_sha256": AGENTDOJO_WHEEL_SHA256,
    }
    require(
        all(benchmark.get(key) == value for key, value in required_benchmark.items()),
        "upstream_version_pin",
        required_benchmark,
    )
    require(
        benchmark.get("dependency_extra") == "agentdojo-full"
        and sha256_file(
            resolve_repo_path(str(benchmark.get("dependency_spec_path") or ""))
        )
        == benchmark.get("dependency_spec_sha256")
        and sha256_file(
            resolve_repo_path(str(benchmark.get("dependency_lock_path") or ""))
        )
        == benchmark.get("dependency_lock_sha256"),
        "dependency_lock_hashes",
        "agentdojo-full / pyproject.toml / uv.lock",
    )
    execution = dict(lock.get("execution") or {})
    required_execution = {
        "attack": ATTACK,
        "defense": DEFENSE,
        "tool_delimiter": TOOL_DELIMITER,
        "tool_output_format": TOOL_OUTPUT_FORMAT,
        "system_message_sha256": SYSTEM_MESSAGE_SHA256,
        "phase": "full",
        "experiment_type": "appendix",
        "case_unit_target": EXPECTED_CASE_COUNT,
        "score_slot_count": len(EXPECTED_AGENTS),
        "score_tasks_per_slot": EXPECTED_CASE_COUNT,
    }
    require(
        all(execution.get(key) == value for key, value in required_execution.items()),
        "execution_definition_pin",
        required_execution,
    )

    for path_text, expected_hash in dict(lock.get("runtime_code_sha256") or {}).items():
        path = resolve_repo_path(path_text)
        require(
            path.exists() and sha256_file(path) == expected_hash,
            "runtime_code_hash",
            path_text,
        )
    for path_text, expected_hash in dict(
        lock.get("legacy_artifact_snapshot_sha256") or {}
    ).items():
        path = resolve_repo_path(path_text)
        require(
            path.exists() and sha256_path(path) == expected_hash,
            "legacy_artifact_unchanged",
            path_text,
        )

    catalog_lock = dict(lock.get("catalog") or {})
    candidates_file = resolve_repo_path(
        str(catalog_lock.get("paired_candidates_path") or "")
    )
    catalog_file = resolve_repo_path(
        str(catalog_lock.get("source_metadata_path") or "")
    )
    require(
        sha256_file(candidates_file) == catalog_lock.get("paired_candidates_sha256"),
        "candidate_hash",
        _repo_relative(candidates_file),
    )
    require(
        sha256_file(catalog_file) == catalog_lock.get("source_metadata_sha256"),
        "catalog_hash",
        _repo_relative(catalog_file),
    )
    _candidates, candidate_refs = _load_candidates(candidates_file)
    catalog, catalog_refs = _load_catalog(catalog_file)
    require(
        candidate_refs == catalog_refs,
        "catalog_exact_id_and_task_order",
        EXPECTED_CASE_COUNT,
    )
    require(
        _suite_counts(catalog_refs) == EXPECTED_SUITE_COUNTS,
        "suite_case_counts",
        EXPECTED_SUITE_COUNTS,
    )
    require(
        all(
            item.get("agentdojo_package_version") == AGENTDOJO_PACKAGE_VERSION
            for item in catalog.get("items") or []
        ),
        "catalog_package_version_non_null",
        AGENTDOJO_PACKAGE_VERSION,
    )

    artifacts = dict(lock.get("artifacts") or {})
    manifest_file = resolve_repo_path(str(artifacts.get("manifest_path") or ""))
    packets_root = resolve_repo_path(str(artifacts.get("case_packets_root") or ""))
    source_bundle_file = resolve_repo_path(
        str(artifacts.get("source_bundle_path") or "")
    )
    official_source_root = resolve_repo_path(
        str(artifacts.get("official_source_bundle_path") or "")
    )
    official_source = validate_official_source_bundle(official_source_root)
    require(
        sha256_file(manifest_file) == artifacts.get("manifest_sha256")
        and sha256_path(packets_root) == artifacts.get("case_packets_tree_sha256")
        and sha256_file(source_bundle_file) == artifacts.get("source_bundle_sha256")
        and official_source.get("manifest_sha256")
        == artifacts.get("official_source_manifest_sha256")
        and official_source.get("source_tree_sha256")
        == artifacts.get("official_source_tree_sha256")
        and official_source.get("file_count")
        == artifacts.get("official_source_file_count"),
        "locked_artifact_hashes",
        {
            "manifest": _repo_relative(manifest_file),
            "case_packets": _repo_relative(packets_root),
            "source_bundle": _repo_relative(source_bundle_file),
            "official_source_bundle": _repo_relative(official_source_root),
        },
    )
    manifest = _load_mapping(manifest_file, "full manifest")
    schema_report = validate_object(
        "experiment_manifest", manifest, raise_on_error=False
    )
    require(schema_report.ok, "manifest_schema", schema_report.to_dict())
    require(
        manifest.get("result_namespace") == RESULT_NAMESPACE,
        "result_namespace",
        RESULT_NAMESPACE,
    )
    selected = load_selected_case_units(manifest_file)
    selected_refs = [
        {"case_unit_id": item.case_unit_id, "task_id": item.task_id}
        for item in selected
    ]
    require(
        selected_refs == catalog_refs,
        "manifest_exact_catalog_order",
        EXPECTED_CASE_COUNT,
    )
    domain = dict((manifest.get("domains") or [None])[0] or {})
    require(
        domain.get("case_unit_target") == EXPECTED_CASE_COUNT
        and domain.get("case_unit_count") == EXPECTED_CASE_COUNT,
        "manifest_case_target_and_count",
        EXPECTED_CASE_COUNT,
    )
    require(
        domain.get("record_slot_count") == EXPECTED_RECORD_SLOT_COUNT,
        "manifest_record_slots",
        EXPECTED_RECORD_SLOT_COUNT,
    )
    require(
        domain.get("official_split_hash") == sha256_file(catalog_file),
        "manifest_catalog_hash",
        domain.get("official_split_hash"),
    )
    require(
        manifest.get("source_bundle_hash") != ZERO_SHA256,
        "manifest_finalized",
        manifest.get("source_bundle_hash"),
    )
    require(
        manifest.get("source_bundle_hash") == sha256_file(source_bundle_file),
        "manifest_source_bundle_hash",
        _repo_relative(source_bundle_file),
    )
    models = dict(lock.get("models") or {})
    infra = dict(lock.get("infrastructure") or {})
    require(
        sha256_file(resolve_repo_path(models["agents_config_path"]))
        == manifest.get("agents_config_hash"),
        "manifest_agents_hash",
        models["agents_config_path"],
    )
    require(
        sha256_file(resolve_repo_path(infra["infra_config_path"]))
        == manifest.get("infra_config_hash"),
        "manifest_infra_hash",
        infra["infra_config_path"],
    )

    jobs_root = resolve_repo_path(str(artifacts.get("jobs_root") or ""))
    job_files = sorted(jobs_root.glob("*.json")) if jobs_root.is_dir() else []
    require(
        len(job_files) == EXPECTED_RECORD_SLOT_COUNT,
        "planned_job_count",
        EXPECTED_RECORD_SLOT_COUNT,
    )
    expected_combinations = {
        (row["case_unit_id"], agent_id)
        for row in catalog_refs
        for agent_id in EXPECTED_AGENTS
    }
    observed_combinations: set[tuple[str, str]] = set()
    observed_slots: set[str] = set()
    manifest_sha256 = sha256_file(manifest_file)
    for job_file in job_files:
        job = _load_mapping(job_file, "planned job")
        combination = (
            str(job.get("case_unit_id") or ""),
            str(job.get("agent_id") or ""),
        )
        observed_combinations.add(combination)
        observed_slots.add(str(job.get("record_slot_id") or ""))
        require(
            job.get("result_namespace") == RESULT_NAMESPACE
            and job.get("domain") == "agentdojo"
            and job.get("phase") == "full"
            and job.get("experiment_type") == "appendix"
            and job.get("manifest_hash") == manifest_sha256,
            "planned_job_identity",
            job_file.name,
        )
    require(
        observed_combinations == expected_combinations,
        "planned_case_agent_product",
        EXPECTED_RECORD_SLOT_COUNT,
    )
    require(
        observed_slots
        == set(_planned_record_slot_ids([row["case_unit_id"] for row in catalog_refs])),
        "planned_record_slot_ids",
        EXPECTED_RECORD_SLOT_COUNT,
    )
    namespace_lock_file = resolve_repo_path(
        str(artifacts.get("result_namespace_lock_path") or "")
    )
    namespace_lock = _load_mapping(namespace_lock_file, "result namespace lock")
    require(
        namespace_lock.get("result_namespace") == RESULT_NAMESPACE
        and namespace_lock.get("legacy_result_root_must_not_be_modified") is True,
        "result_namespace_reservation",
        _repo_relative(namespace_lock_file),
    )

    expected_dirs = {_safe_case_dir_name(row["case_unit_id"]) for row in catalog_refs}
    agentdojo_packets = packets_root / "agentdojo"
    actual_dirs = (
        {path.name for path in agentdojo_packets.iterdir() if path.is_dir()}
        if agentdojo_packets.exists()
        else set()
    )
    require(
        actual_dirs == expected_dirs,
        "case_packet_directory_set",
        {"expected": len(expected_dirs), "actual": len(actual_dirs)},
    )
    expected_raw_case_file_hash_count = 0
    for row in catalog_refs:
        case_dir = agentdojo_packets / _safe_case_dir_name(row["case_unit_id"])
        packet_file = case_dir / "case_packet.md"
        raw_manifest_file = case_dir / "raw_case_manifest.json"
        raw_dir = case_dir / "raw_case"
        require(
            packet_file.is_file() and raw_manifest_file.is_file() and raw_dir.is_dir(),
            "case_packet_files",
            row["case_unit_id"],
        )
        raw_manifest = _load_mapping(raw_manifest_file, "raw case manifest")
        expected_raw_case_file_hash_count += len(
            raw_manifest.get("sha256_per_file") or {}
        )
        require(
            raw_manifest.get("case_unit_id") == row["case_unit_id"]
            and raw_manifest.get("task_id") == row["task_id"]
            and raw_manifest.get("domain") == "agentdojo",
            "raw_case_identity",
            row["case_unit_id"],
        )

    bundle = _load_mapping(source_bundle_file, "case packet source bundle")
    from evidence_system.cli.build_case_packet_source_bundle import (
        validate_source_bundle_strict,
    )

    bundle_audit = validate_source_bundle_strict(
        source_bundle_path=source_bundle_file,
        manifest_path=manifest_file,
        case_packets_root=packets_root,
        expected_cases=selected,
        expected_count=EXPECTED_CASE_COUNT,
        expected_domains=["agentdojo"],
    )
    require(
        bundle_audit.get("verified_file_hash_count") == EXPECTED_CASE_COUNT * 2
        and bundle_audit.get("verified_raw_case_file_hash_count")
        == expected_raw_case_file_hash_count,
        "source_bundle_deep_hash_audit",
        bundle_audit,
    )
    sources = list(bundle.get("sources") or [])
    require(
        bundle.get("source_count") == EXPECTED_CASE_COUNT
        and len(sources) == EXPECTED_CASE_COUNT,
        "source_bundle_count",
        EXPECTED_CASE_COUNT,
    )
    source_refs = [
        {
            "case_unit_id": str(item.get("case_unit_id") or ""),
            "task_id": str(item.get("task_id") or ""),
        }
        for item in sources
        if isinstance(item, Mapping)
    ]
    require(
        source_refs == catalog_refs,
        "source_bundle_exact_manifest_order",
        EXPECTED_CASE_COUNT,
    )
    for index, source in enumerate(sources):
        if not isinstance(source, Mapping):
            raise ContractLifecycleError(
                f"source bundle entry {index} is not a mapping"
            )
        issues = validate_case_packet_source(source, base=f"$.sources[{index}]")
        require(not issues, "source_bundle_entry_hashes", source.get("case_unit_id"))

    acceptance = {
        "schema_version": "agentdojo_full_acceptance_report/v1",
        "status": "accepted",
        "lock_path": _repo_relative(lock_file),
        "lock_sha256": sha256_file(lock_file),
        "manifest_path": _repo_relative(manifest_file),
        "manifest_sha256": sha256_file(manifest_file),
        "catalog_path": _repo_relative(catalog_file),
        "catalog_sha256": sha256_file(catalog_file),
        "case_packets_root": _repo_relative(packets_root),
        "case_packets_tree_sha256": sha256_path(packets_root),
        "jobs_root": _repo_relative(jobs_root),
        "jobs_tree_sha256": sha256_path(jobs_root),
        "result_namespace_lock_path": _repo_relative(namespace_lock_file),
        "result_namespace_lock_sha256": sha256_file(namespace_lock_file),
        "source_bundle_path": _repo_relative(source_bundle_file),
        "source_bundle_sha256": sha256_file(source_bundle_file),
        "counts": {
            "case_units": EXPECTED_CASE_COUNT,
            "case_packets": len(actual_dirs),
            "source_bundle_entries": len(sources),
            "valid_checklist_drafts": EXPECTED_CASE_COUNT,
            "reviewed_checklists": EXPECTED_CASE_COUNT,
            "locked_checklists": EXPECTED_CASE_COUNT,
            "unresolved_checklist_drafts": 0,
            "record_slots": EXPECTED_RECORD_SLOT_COUNT,
            "planned_jobs": len(job_files),
            "formal_paired_episodes": EXPECTED_RECORD_SLOT_COUNT * 2,
            "native_trajectories_without_cache": EXPECTED_RECORD_SLOT_COUNT * 3,
        },
        "suite_case_counts": _suite_counts(catalog_refs),
        "checks": checks,
    }
    acceptance_file = resolve_repo_path(acceptance_output_path)
    acceptance_file.parent.mkdir(parents=True, exist_ok=True)
    acceptance_file.write_text(
        json.dumps(acceptance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return acceptance_file


def _load_candidates(path: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    payload = _load_mapping(path, "paired candidates")
    if payload.get("benchmark_version") != BENCHMARK_VERSION:
        raise ContractLifecycleError(
            f"paired candidates benchmark_version must be {BENCHMARK_VERSION}"
        )
    items = payload.get("items")
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        raise ContractLifecycleError("paired candidates items must be a list")
    refs = [_case_ref(item, label="paired candidate") for item in items]
    return payload, refs


def _load_catalog(path: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    payload = _load_mapping(path, "AgentDojo source catalog")
    if payload.get("benchmark_version") != BENCHMARK_VERSION:
        raise ContractLifecycleError(
            f"source catalog benchmark_version must be {BENCHMARK_VERSION}"
        )
    items = payload.get("items")
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        raise ContractLifecycleError("source catalog items must be a list")
    refs = [_case_ref(item, label="source catalog item") for item in items]
    return payload, refs


def _case_ref(value: Any, *, label: str) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ContractLifecycleError(f"{label} must be a mapping")
    return {
        "case_unit_id": str(value.get("case_unit_id") or ""),
        "task_id": str(value.get("task_id") or ""),
    }


def _validate_case_refs(refs: Sequence[Mapping[str, str]], *, label: str) -> None:
    if len(refs) != EXPECTED_CASE_COUNT:
        raise ContractLifecycleError(
            f"{label} must contain exactly {EXPECTED_CASE_COUNT} cases; found {len(refs)}"
        )
    ids = [row["case_unit_id"] for row in refs]
    if len(set(ids)) != len(ids):
        raise ContractLifecycleError(f"{label} contains duplicate case_unit_id values")
    for row in refs:
        case_id = row["case_unit_id"]
        if not CASE_ID_RE.fullmatch(case_id):
            raise ContractLifecycleError(
                f"invalid full-coverage case ID in {label}: {case_id}"
            )
        expected_task = case_id.removeprefix(f"{BENCHMARK_VERSION}:")
        if row["task_id"] != expected_task:
            raise ContractLifecycleError(
                f"task_id mismatch for {case_id}: {row['task_id']}"
            )
    observed = _suite_counts(refs)
    if observed != EXPECTED_SUITE_COUNTS:
        raise ContractLifecycleError(
            f"{label} suite counts differ: expected={EXPECTED_SUITE_COUNTS} actual={observed}"
        )


def _suite_counts(refs: Sequence[Mapping[str, str]]) -> dict[str, int]:
    counts = Counter(str(row["case_unit_id"]).split(":")[1] for row in refs)
    return {suite: counts[suite] for suite in sorted(counts)}


def _manifest_agent_entries(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    roles = config.get("experimental_agents")
    if not isinstance(roles, Mapping):
        raise ContractLifecycleError("agents config missing experimental_agents")
    entries: list[dict[str, Any]] = []
    for agent_id in EXPECTED_AGENTS:
        role = roles.get(agent_id)
        if not isinstance(role, Mapping):
            raise ContractLifecycleError(f"agents config missing {agent_id}")
        original_rationale = role.get("agent_probe_rationale")
        if not isinstance(original_rationale, Mapping):
            raise ContractLifecycleError(
                f"agents config {agent_id} missing agent_probe_rationale"
            )
        rationale = dict(original_rationale)
        rationale["spans_tool_use_style"] = (
            "AgentDojo native tool calls via LOCAL OpenAI-compatible proxy; delimiter=tool"
        )
        entries.append(
            {
                "agent_id": agent_id,
                "config_hash": sha256_object(dict(role)),
                "agent_probe_rationale": rationale,
            }
        )
    return entries


def _model_snapshot(config: Mapping[str, Any]) -> dict[str, Any]:
    roles = config.get("experimental_agents")
    if not isinstance(roles, Mapping):
        raise ContractLifecycleError("agents config missing experimental_agents")
    fields = (
        "provider",
        "model",
        "model_display_name",
        "model_version",
        "api_key_env",
        "temperature",
        "max_tokens",
        "timeout_seconds",
        "retry",
        "rate_limit",
        "save_response_metadata",
        "cost_tracking",
    )
    result: dict[str, Any] = {}
    for agent_id in EXPECTED_AGENTS:
        role = roles.get(agent_id)
        if not isinstance(role, Mapping):
            raise ContractLifecycleError(f"agents config missing {agent_id}")
        snapshot = {field: role.get(field) for field in fields}
        if any(
            snapshot.get(field) in {None, ""}
            for field in ("provider", "model", "model_version", "api_key_env")
        ):
            raise ContractLifecycleError(
                f"agents config {agent_id} has incomplete model identity"
            )
        snapshot["config_sha256"] = sha256_object(dict(role))
        result[agent_id] = snapshot
    return result


def _agentdojo_infra_snapshot(config: Mapping[str, Any]) -> dict[str, Any]:
    for machine in config.get("machines") or []:
        if not isinstance(machine, Mapping) or machine.get("enabled") is False:
            continue
        benchmarks = machine.get("benchmarks")
        if not isinstance(benchmarks, Mapping):
            continue
        for name, benchmark in benchmarks.items():
            if str(name).lower() != "agentdojo" or not isinstance(benchmark, Mapping):
                continue
            return {
                "machine_id": str(machine.get("machine_id") or ""),
                "machine_role": str(machine.get("role") or ""),
                "remote_workdir": str(machine.get("remote_workdir") or ""),
                "machine_concurrency": int(machine.get("concurrency") or 1),
                "install_dir": str(benchmark.get("install_dir") or ""),
                "runner_command": str(benchmark.get("runner_command") or ""),
            }
    raise ContractLifecycleError("enabled AgentDojo infra target is missing")


def _planned_record_slot_ids(case_ids: Sequence[str]) -> list[str]:
    return [
        f"slot-agentdojo-{_safe_job_id(case_id)}-{_safe_job_id(agent.lower().replace(' ', '_'))}"
        for case_id in case_ids
        for agent in EXPECTED_AGENTS
    ]


def _safe_job_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "x"


def _safe_case_dir_name(case_unit_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", case_unit_id).strip("_") or "case"


def _load_mapping(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise ContractLifecycleError(f"{label} is missing: {path}")
    payload = load_json_or_yaml(path)
    if not isinstance(payload, Mapping):
        raise ContractLifecycleError(f"{label} must be a mapping: {path}")
    return dict(payload)


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root().resolve()).as_posix()
    except ValueError:
        return str(path.resolve())
