"""Formal schema loading and fail-closed validation for Step 3.

The repository keeps JSON Schema files as first-class artifacts under
``schemas/``.  This module validates those structures with a small stdlib
validator that covers the subset used by the checked-in schemas, then applies
experiment-specific semantic gates that JSON Schema alone cannot express
cleanly.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from evidence_system.core.errors import EvidenceSystemError
from evidence_system.core.hashing import sha256_bytes
from evidence_system.core.paths import repo_root, resolve_repo_path


REQUIRED_SCHEMA_FILES = (
    "experiment_manifest.schema.json",
    "paper_mapping.schema.json",
    "job.schema.json",
    "agent_config.schema.json",
    "infra_config.schema.json",
    "raw_run.schema.json",
    "scored_record.schema.json",
    "infra_exclusion_record.schema.json",
    "failure_record.schema.json",
    "artifact_manifest.schema.json",
    "evidence_contract.schema.json",
    "contract_review.schema.json",
    "llm_call.schema.json",
    "human_review.schema.json",
    "human_time.schema.json",
    "audit_item.schema.json",
    "audit_label.schema.json",
    "rerun_record.schema.json",
    "stats_plan.schema.json",
    "bootstrap_plan.schema.json",
    "audit_sampling_plan.schema.json",
    "rerun_subset.schema.json",
    "aggregate_metrics.schema.json",
    "prediction_outcome.schema.json",
    "pairwise_matrix.schema.json",
    "denominator_audit.schema.json",
    "paper_output.schema.json",
    "freeze_manifest.schema.json",
    "deployment_manifest.schema.json",
    "release_artifact.schema.json",
)

CANONICAL_DOMAIN_IDS = frozenset(
    {
        "agentdojo",
        "appworld",
        "miniwob",
        "webarena_verified",
        "tau3_retail",
        "androidworld",
        "workarena",
        "toolsandbox",
        "osworld_verified",
        "judge_only",
        "maintenance_update",
        "matched_budget_controls",
    }
)
PHASES = frozenset({"smoke", "dry_run", "preflight", "full", "rerun"})
FORMAL_PHASES = frozenset({"preflight", "full", "rerun"})
EXPERIMENT_TYPES = frozenset(
    {"main", "appendix", "diagnostic", "audit", "maintenance_update", "matched_budget_control"}
)
PRIORITIES = frozenset({"P0", "P1", "P2", "P3"})
AGENT_IDS = ("Agent A", "Agent B", "Agent C")
LLM_ROLE_IDS = AGENT_IDS + ("contract_drafter", "judge_only")
LLM_PROMPT_ROLE_IDS = frozenset({"contract_drafter", "judge_only"})
P0_MAIN_DOMAIN_IDS = frozenset({"agentdojo", "appworld", "webarena_verified", "tau3_retail"})
P0_DEFAULT_CASE_UNITS_PER_DOMAIN = 100
P0_DEFAULT_PLANNED_RECORD_SLOTS = len(P0_MAIN_DOMAIN_IDS) * P0_DEFAULT_CASE_UNITS_PER_DOMAIN * len(AGENT_IDS)
UNRESOLVE_REASONS = frozenset({"R1", "R2", "R3", "R4", "R5", "R6", "R7"})
UNRESOLVE_LEVELS = frozenset({"trace_level", "instrument_level"})
HASH_RE = re.compile(r"^(sha256:)?[a-f0-9]{64}$")
PAPER_LABEL_RE = re.compile(r"\b(?:tab|fig|app):[A-Za-z0-9:-]+")

REQUIRED_PAPER_LABELS = frozenset(
    {
        "tab:views",
        "tab:unresolve-taxonomy",
        "tab:domains",
        "tab:main-results-A",
        "tab:denominator-audit",
        "tab:main-results-B",
        "tab:prediction-outcomes",
        "tab:main-results-C",
        "tab:pairwise-margins",
        "tab:top-unresolve-reasons",
        "tab:audit-rerun",
        "tab:per-agent",
        "tab:cost",
        "tab:contract-drafting-metadata",
        "tab:update",
        "fig:hero",
        "fig:evidence-counting",
        "fig:case-cards",
        "app:per-agent",
        "app:cost",
        "app:contract-drafting-details",
        "app:aux-domains",
        "app:osworld",
        "app:judge",
        "app:update",
        "app:release",
        "Formal Definitions",
        "app:macro-contract",
    }
)

PLACEHOLDER_MARKERS = (
    "需要从 locked manifest 确认",
    "需要从 scored manifest 填充",
    "需要从论文确认",
    "需要从 benchmark 官方 split 确认",
    "\\fillfromdata",
    "fillfromdata",
    "placeholder",
    "TBD",
    "TODO",
    "not_implemented",
    "mock" + "_result",
)

UNSUPPORTED_JSON_SCHEMA_KEYWORDS = frozenset(
    {
        "if",
        "then",
        "else",
        "allOf",
        "oneOf",
        "not",
        "dependentRequired",
        "dependentSchemas",
        "patternProperties",
        "unevaluatedProperties",
        "contains",
    }
)

NATIVE_ALIGNED_MAIN_OUTPUT_LABELS = frozenset(
    {
        "tab:main-results-A",
        "tab:main-results-B",
        "tab:main-results-C",
        "tab:per-agent",
        "tab:pairwise-margins",
        "fig:hero",
    }
)

PAPER_OUTPUT_SOURCE_SCHEMA_VERSIONS: dict[str, frozenset[str]] = {
    "aggregate_metrics": frozenset({"aggregate_metrics/v1"}),
    "scored_record": frozenset({"scored_record/v1"}),
    "human_time": frozenset({"human_time/v1"}),
    "llm_call": frozenset({"llm_call/v1"}),
    "release_artifact": frozenset({"release_artifact/v1"}),
    "manifest": frozenset({"experiment_manifest/v1"}),
    "pairwise_matrix": frozenset({"pairwise_matrix/v1"}),
    "prediction_outcome": frozenset({"prediction_outcome/v1"}),
    "denominator_audit": frozenset({"denominator_audit/v1"}),
}

PAPER_MAPPING_PROVENANCE_ALIASES = {
    "scored_record": "scored_records",
    "llm_call": "llm_calls",
    "release_artifact": "release_metadata",
}

COST_TABLE_ACTIVITY_TYPES = frozenset(
    {
        "contract_draft_review",
        "contract_lock",
        "evidence_scoring_review",
        "unresolve_tagging",
        "setup",
    }
)

DEPLOY_COLLECT_RESUME_WORKFLOW_STAGES = frozenset(
    {
        "deploy_all",
        "deploy_webarena",
        "deploy_osworld",
        "deploy_other_vps",
        "deploy_local_androidworld",
        "collect_results",
        "resume_failed",
    }
)

TIMESTAMP_FIELD_NAMES = frozenset(
    {
        "created_at",
        "created_at_utc",
        "started_at",
        "ended_at",
        "failed_at",
        "finished_at",
        "locked_at",
        "frozen_at",
        "draft_created_at",
        "review_started_at",
        "review_finished_at",
        "first_scoring_started_at",
        "request_timestamp",
        "response_timestamp",
        "artifact_created_at",
        "clarification_requested_at",
        "clarification_locked_at",
    }
)


@dataclass(frozen=True)
class SchemaRegistryStatus:
    schema_dir: str
    missing: list[str]

    @property
    def ok(self) -> bool:
        return not self.missing


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationReport:
    schema_name: str
    status: str
    issues: tuple[ValidationIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": self.schema_name,
            "status": self.status,
            "issues": [issue.to_dict() for issue in self.issues],
        }


class SchemaValidationError(EvidenceSystemError):
    """Raised when an object fails structural or semantic schema validation."""

    def __init__(self, report: ValidationReport):
        self.report = report
        joined = "; ".join(f"{i.path}: {i.message}" for i in report.issues[:5])
        if len(report.issues) > 5:
            joined += f"; ... {len(report.issues) - 5} more"
        super().__init__(joined or f"{report.schema_name} validation failed")


def schema_dir() -> Path:
    return resolve_repo_path("schemas")


def check_schema_files() -> SchemaRegistryStatus:
    base = schema_dir()
    missing = [name for name in REQUIRED_SCHEMA_FILES if not (base / name).exists()]
    return SchemaRegistryStatus(schema_dir=str(base), missing=missing)


def schema_filename(schema_name: str) -> str:
    normalized = schema_name[:-12] if schema_name.endswith(".schema.json") else schema_name
    filename = f"{normalized}.schema.json"
    if filename not in REQUIRED_SCHEMA_FILES:
        raise SchemaValidationError(
            ValidationReport(
                schema_name=normalized,
                status="invalid",
                issues=(ValidationIssue("$schema", f"unknown schema: {schema_name}"),),
            )
        )
    return filename


def load_schema(schema_name: str) -> dict[str, Any]:
    path = schema_dir() / schema_filename(schema_name)
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SchemaValidationError(
            ValidationReport(
                schema_name=schema_name,
                status="invalid",
                issues=(ValidationIssue("$schema", f"missing schema file: {path}"),),
            )
        ) from exc
    except json.JSONDecodeError as exc:
        raise SchemaValidationError(
            ValidationReport(
                schema_name=schema_name,
                status="invalid",
                issues=(ValidationIssue("$schema", f"invalid JSON schema: {exc}"),),
            )
        ) from exc
    if not isinstance(loaded, dict):
        raise SchemaValidationError(
            ValidationReport(
                schema_name=schema_name,
                status="invalid",
                issues=(ValidationIssue("$schema", "schema root must be an object"),),
            )
        )
    return loaded


def load_json_or_yaml(path: str | Path) -> Any:
    resolved = resolve_repo_path(path)
    text = resolved.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as json_error:
        try:
            import yaml  # type: ignore[import-not-found]
        except ModuleNotFoundError as exc:
            raise SchemaValidationError(
                ValidationReport(
                    schema_name=str(path),
                    status="invalid",
                    issues=(
                        ValidationIssue(
                            "$",
                            "file is not JSON and PyYAML is not installed for YAML parsing",
                        ),
                    ),
                )
            ) from exc
        try:
            return yaml.safe_load(text)
        except Exception as yaml_error:  # pragma: no cover - optional dependency path
            raise SchemaValidationError(
                ValidationReport(
                    schema_name=str(path),
                    status="invalid",
                    issues=(ValidationIssue("$", f"could not parse YAML: {yaml_error}"),),
                )
            ) from json_error


def validate_file(
    schema_name: str,
    path: str | Path,
    *,
    formal: bool = False,
    paper_mapping_labels: set[str] | None = None,
    locked_contracts: Mapping[str, Any] | None = None,
    raise_on_error: bool = True,
) -> ValidationReport:
    payload = load_json_or_yaml(path)
    return validate_object(
        schema_name,
        payload,
        formal=formal,
        paper_mapping_labels=paper_mapping_labels,
        locked_contracts=locked_contracts,
        raise_on_error=raise_on_error,
    )


def validate_object(
    schema_name: str,
    payload: Any,
    *,
    formal: bool = False,
    paper_mapping_labels: set[str] | None = None,
    locked_contracts: Mapping[str, Any] | None = None,
    raise_on_error: bool = True,
) -> ValidationReport:
    normalized = schema_name[:-12] if schema_name.endswith(".schema.json") else schema_name
    schema = load_schema(normalized)
    issues = list(_unsupported_schema_keyword_issues(schema, "$schema"))
    issues.extend(_validate_against_schema(payload, schema, schema, "$"))
    issues.extend(_timestamp_parseability_issues(payload, "$"))
    issues.extend(
        _semantic_issues(
            normalized,
            payload,
            formal=formal,
            paper_mapping_labels=paper_mapping_labels,
            locked_contracts=locked_contracts,
        )
    )
    if formal:
        issues.extend(_placeholder_issues(payload, "$"))
    report = ValidationReport(
        schema_name=normalized,
        status="ok" if not issues else "invalid",
        issues=tuple(issues),
    )
    if issues and raise_on_error:
        raise SchemaValidationError(report)
    return report


def validate_cross_object_consistency(
    objects: Iterable[tuple[str, Mapping[str, Any]]],
    *,
    raise_on_error: bool = True,
) -> ValidationReport:
    """Validate cross-object hashes that cannot be checked inside one file.

    This is a Step 3 validation primitive, not Step 4 contract lifecycle logic.
    It requires already-materialized objects and verifies that shared contract
    and deterministic-selection commitments agree across them.
    """

    items = list(objects)
    issues: list[ValidationIssue] = []
    contract_locks, registry_report = collect_locked_contracts(items, raise_on_error=False)
    issues.extend(registry_report.issues)
    freeze_manifest: Mapping[str, Any] | None = None
    manifest: Mapping[str, Any] | None = None
    paper_mappings: list[Mapping[str, Any]] = []
    deterministic_reference: tuple[str, Mapping[str, Any]] | None = None
    deterministic_fields = {
        "hash_function",
        "hash_salt_hash",
        "eligible_case_unit_set_hash",
        "smoke_exclusion_hash",
        "case_selection_order_hash",
        "bootstrap_seed",
        "bootstrap_resample_count",
        "audit_sample_seed",
        "rerun_subset_selection_rule",
    }

    for name, payload in items:
        if payload.get("schema_version") == "experiment_manifest/v1":
            manifest = payload
        if payload.get("schema_version") == "freeze_manifest/v1":
            freeze_manifest = payload
        if payload.get("schema_version") == "paper_mapping/v1":
            paper_mappings.append(payload)
        selection = _deterministic_selection_view(payload)
        if selection is not None:
            selection_base = f"${name}.deterministic_selection" if isinstance(payload.get("deterministic_selection"), Mapping) else f"${name}"
            issues.extend(_deterministic_selection_hash_issues(selection, selection_base))
            if deterministic_reference is None:
                deterministic_reference = (name, selection)
            else:
                ref_name, ref = deterministic_reference
                for field in deterministic_fields:
                    if selection.get(field) != ref.get(field):
                        issues.append(
                            _issue(
                                f"${name}.deterministic_selection.{field}",
                                f"deterministic selection drift from {ref_name}",
                            )
                        )

    issues.extend(_formal_context_hash_issues(manifest, freeze_manifest, paper_mappings, items))
    for name, payload in items:
        issues.extend(_validate_contract_reference(payload, f"${name}", contract_locks or None))
        if freeze_manifest is not None:
            issues.extend(_freeze_drift_issues(payload, freeze_manifest, f"${name}"))
        if manifest is not None and payload.get("schema_version") == "denominator_audit/v1":
            issues.extend(_denominator_manifest_slot_issues(payload, manifest, f"${name}"))
        if payload.get("schema_version") == "aggregate_metrics/v1":
            issues.extend(_validate_aggregate_metrics_semantics(payload))
            issues.extend(_aggregate_denominator_consistency_issues(payload, items, f"${name}"))
        if payload.get("schema_version") == "paper_output/v1":
            issues.extend(_paper_output_source_mapping_issues(payload, items, paper_mappings, f"${name}"))
        if payload.get("schema_version") == "failure_record/v1":
            issues.extend(_failure_record_deployment_manifest_issues(payload, items, f"${name}"))
        issues.extend(_native_decisive_artifact_manifest_issues(payload, items, f"${name}"))
        issues.extend(_native_decisive_locked_artifact_mapping_issues(payload, items, f"${name}"))
    if manifest is not None:
        issues.extend(_p0_denominator_audit_global_issues(manifest, items))
        issues.extend(_formal_result_denominator_audit_issues(manifest, items))

    report = ValidationReport(
        schema_name="cross_object_consistency",
        status="ok" if not issues else "invalid",
        issues=tuple(issues),
    )
    if issues and raise_on_error:
        raise SchemaValidationError(report)
    return report


def collect_locked_contracts(
    objects: Iterable[tuple[str, Mapping[str, Any]]],
    *,
    raise_on_error: bool = True,
) -> tuple[dict[str, Mapping[str, Any]], ValidationReport]:
    items = list(objects)
    registry: dict[str, Mapping[str, Any]] = {}
    issues: list[ValidationIssue] = []
    manifest: Mapping[str, Any] | None = None
    for name, payload in items:
        if payload.get("schema_version") == "experiment_manifest/v1":
            manifest = payload
        locks = payload.get("contract_locks")
        if not isinstance(locks, list):
            continue
        for index, lock in enumerate(locks):
            if not isinstance(lock, Mapping):
                continue
            base = f"${name}.contract_locks[{index}]"
            entry_issues = _contract_registry_entry_issues(lock, base)
            issues.extend(entry_issues)
            if entry_issues:
                continue
            key = _contract_key(lock)
            if key is None:
                issues.append(_issue(base, "locked contract registry entry requires contract_id and contract_version"))
                continue
            existing = registry.get(key)
            if existing is not None and _registry_contract_hash(existing) != _registry_contract_hash(lock):
                issues.append(_issue(base, "duplicate locked contract registry entries disagree on canonical hash"))
                continue
            registry[key] = lock

    for name, payload in items:
        if payload.get("schema_version") != "evidence_contract/v1":
            continue
        base = f"${name}"
        entry_issues = _contract_registry_entry_issues(payload, base)
        issues.extend(entry_issues)
        if entry_issues:
            continue
        issues.extend(_evidence_contract_manifest_lock_issues(payload, registry, manifest, base))
    report = ValidationReport(
        schema_name="locked_contract_registry",
        status="ok" if not issues else "invalid",
        issues=tuple(issues),
    )
    if issues and raise_on_error:
        raise SchemaValidationError(report)
    return registry, report


def extract_paper_mapping_labels(path: str | Path) -> set[str]:
    resolved = resolve_repo_path(path)
    text = resolved.read_text(encoding="utf-8")
    labels = set(PAPER_LABEL_RE.findall(text))
    if "Formal Definitions" in text:
        labels.add("Formal Definitions")
    return labels


def paper_mapping_labels_from_object(payload: Mapping[str, Any]) -> set[str]:
    labels: set[str] = set()
    labels_obj = payload.get("labels")
    if isinstance(labels_obj, Mapping):
        for value in labels_obj.values():
            if isinstance(value, list):
                labels.update(str(item) for item in value)
    mappings = payload.get("mappings")
    if isinstance(mappings, list):
        for item in mappings:
            if isinstance(item, Mapping) and isinstance(item.get("label"), str):
                labels.add(item["label"])
    return labels


def paper_mapping_declared_labels_from_object(payload: Mapping[str, Any]) -> set[str]:
    labels: set[str] = set()
    labels_obj = payload.get("labels")
    if isinstance(labels_obj, Mapping):
        for value in labels_obj.values():
            if isinstance(value, list):
                labels.update(str(item) for item in value)
    return labels


def paper_mapping_mapped_labels_from_object(payload: Mapping[str, Any]) -> set[str]:
    labels: set[str] = set()
    mappings = payload.get("mappings")
    if isinstance(mappings, list):
        for item in mappings:
            if isinstance(item, Mapping) and isinstance(item.get("label"), str):
                labels.add(item["label"])
    return labels


def validate_paper_mapping_coverage(
    mapping: Mapping[str, Any] | str | Path,
    *,
    required_labels: Iterable[str] = REQUIRED_PAPER_LABELS,
    raise_on_error: bool = True,
) -> ValidationReport:
    if isinstance(mapping, Mapping):
        declared_labels = paper_mapping_declared_labels_from_object(mapping)
        mapped_labels = paper_mapping_mapped_labels_from_object(mapping)
        schema_name = "paper_mapping"
    else:
        declared_labels = extract_paper_mapping_labels(mapping)
        mapped_labels = declared_labels
        schema_name = "paper_mapping"
    required = set(required_labels)
    issues: list[ValidationIssue] = []
    for label in sorted(required - declared_labels):
        issues.append(ValidationIssue("labels", f"missing required paper label declaration: {label}"))
    for label in sorted(required - mapped_labels):
        issues.append(ValidationIssue("mappings", f"missing required paper label mapping: {label}"))
    if isinstance(mapping, Mapping):
        mappings = mapping.get("mappings")
        if isinstance(mappings, list):
            mapped_label_list: list[str] = [
                str(item.get("label"))
                for item in mappings
                if isinstance(item, Mapping) and isinstance(item.get("label"), str)
            ]
            mapped_counts = Counter(mapped_label_list)
            for label in sorted(declared_labels - set(mapped_label_list)):
                issues.append(ValidationIssue("mappings", f"declared paper label has no mapping: {label}"))
            for label in sorted(set(mapped_label_list) - declared_labels):
                issues.append(ValidationIssue("mappings", f"mapping label is not declared: {label}"))
            for label, count in sorted(mapped_counts.items()):
                if count != 1:
                    issues.append(ValidationIssue("mappings", f"duplicate paper label mapping: {label}"))
            for index, item in enumerate(mappings):
                if not isinstance(item, Mapping):
                    continue
                label = item.get("label")
                sources = item.get("provenance_sources")
                if not item.get("source_path"):
                    issues.append(ValidationIssue(f"mappings[{index}].source_path", "paper mapping source_path is required"))
                if not _is_hash(item.get("source_sha256")):
                    issues.append(ValidationIssue(f"mappings[{index}].source_sha256", "paper mapping source_sha256 is required"))
                if not sources:
                    issues.append(ValidationIssue(f"mappings[{index}].provenance_sources", "paper mapping provenance_sources are required"))
                if label in {"tab:cost", "app:cost"}:
                    if not isinstance(sources, list) or {str(source) for source in sources} != {"human_time"}:
                        issues.append(ValidationIssue(f"mappings[{index}].provenance_sources", f"{label} mapping must use only human_time provenance"))
                if label in NATIVE_ALIGNED_MAIN_OUTPUT_LABELS and isinstance(sources, list):
                    if any(str(source) in {"stronger_measurement", "smoke", "dry_run", "manual_fallback"} for source in sources):
                        issues.append(ValidationIssue(f"mappings[{index}].provenance_sources", "native-aligned main mapping cannot use stronger_measurement or fallback provenance"))
    report = ValidationReport(schema_name=schema_name, status="ok" if not issues else "invalid", issues=issues)
    if issues and raise_on_error:
        raise SchemaValidationError(report)
    return report


def _validate_against_schema(value: Any, schema: Mapping[str, Any], root: Mapping[str, Any], path: str) -> list[ValidationIssue]:
    if "$ref" in schema:
        return _validate_against_schema(value, _resolve_ref(schema["$ref"], root), root, path)

    if "anyOf" in schema:
        branch_issues = [
            _validate_against_schema(value, branch, root, path)
            for branch in _as_sequence(schema["anyOf"])
        ]
        if any(not issues for issues in branch_issues):
            return []
        return [ValidationIssue(path, "does not match any allowed schema branch")]

    issues: list[ValidationIssue] = []
    if "const" in schema and value != schema["const"]:
        issues.append(ValidationIssue(path, f"expected constant {schema['const']!r}"))
        return issues
    if "enum" in schema and value not in schema["enum"]:
        issues.append(ValidationIssue(path, f"value {value!r} is not in enum {schema['enum']!r}"))
        return issues

    expected_type = schema.get("type")
    if expected_type is not None and not _matches_type(value, expected_type):
        issues.append(ValidationIssue(path, f"expected type {expected_type!r}, got {type(value).__name__}"))
        return issues

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                issues.append(ValidationIssue(_join_path(path, key), "missing required property"))
        properties = schema.get("properties", {})
        if isinstance(properties, Mapping):
            for key, child_schema in properties.items():
                if key in value:
                    issues.extend(_validate_against_schema(value[key], child_schema, root, _join_path(path, key)))
            if schema.get("additionalProperties") is False:
                allowed = set(properties)
                for key in sorted(set(value) - allowed):
                    issues.append(_issue(_join_path(path, key), "additional property is not allowed"))

    if isinstance(value, list):
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            issues.append(ValidationIssue(path, f"expected at least {min_items} items"))
        max_items = schema.get("maxItems")
        if isinstance(max_items, int) and len(value) > max_items:
            issues.append(ValidationIssue(path, f"expected at most {max_items} items"))
        items_schema = schema.get("items")
        if isinstance(items_schema, Mapping):
            for index, item in enumerate(value):
                issues.extend(_validate_against_schema(item, items_schema, root, f"{path}[{index}]"))

    if isinstance(value, str):
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            issues.append(ValidationIssue(path, f"expected string length >= {min_length}"))
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and not re.match(pattern, value):
            issues.append(ValidationIssue(path, f"does not match pattern {pattern!r}"))

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if isinstance(minimum, (int, float)) and value < minimum:
            issues.append(ValidationIssue(path, f"expected value >= {minimum}"))
        if isinstance(maximum, (int, float)) and value > maximum:
            issues.append(ValidationIssue(path, f"expected value <= {maximum}"))

    return issues


def _semantic_issues(
    schema_name: str,
    payload: Any,
    *,
    formal: bool,
    paper_mapping_labels: set[str] | None,
    locked_contracts: Mapping[str, Any] | None,
) -> list[ValidationIssue]:
    if not isinstance(payload, dict):
        return []
    deterministic_selection = _deterministic_selection_view(payload)
    deterministic_base = "$.deterministic_selection" if isinstance(payload.get("deterministic_selection"), Mapping) else "$"
    issues = _deterministic_selection_hash_issues(deterministic_selection, deterministic_base)
    validators = {
        "scored_record": _validate_scored_record_semantics,
        "infra_exclusion_record": _validate_infra_exclusion_semantics,
        "raw_run": _validate_raw_run_semantics,
        "artifact_manifest": _validate_artifact_manifest_semantics,
        "aggregate_metrics": _validate_aggregate_metrics_semantics,
        "experiment_manifest": _validate_experiment_manifest_semantics,
        "agent_config": _validate_agent_config_semantics,
        "infra_config": _validate_infra_config_semantics,
        "llm_call": _validate_llm_call_semantics,
        "human_review": _validate_human_review_semantics,
        "contract_review": _validate_contract_review_semantics,
        "human_time": _validate_human_time_semantics,
        "audit_label": _validate_audit_label_semantics,
        "evidence_contract": _validate_evidence_contract_semantics,
        "denominator_audit": _validate_denominator_audit_semantics,
        "paper_output": _validate_paper_output_semantics,
        "stats_plan": _validate_stats_plan_semantics,
        "job": _validate_job_semantics,
        "freeze_manifest": _validate_freeze_manifest_semantics,
        "failure_record": _validate_failure_record_semantics,
        "deployment_manifest": _validate_deployment_manifest_semantics,
        "prediction_outcome": _validate_prediction_outcome_semantics,
        "pairwise_matrix": _validate_pairwise_matrix_semantics,
        "release_artifact": _validate_release_artifact_semantics,
        "rerun_record": _validate_rerun_record_semantics,
        "rerun_subset": _validate_rerun_subset_semantics,
        "audit_item": _validate_audit_item_semantics,
        "audit_sampling_plan": _validate_audit_sampling_plan_semantics,
        "bootstrap_plan": _validate_bootstrap_plan_semantics,
    }
    validator = validators.get(schema_name)
    if validator is None:
        return issues
    issues.extend(validator(
        payload,
        formal=formal,
        paper_mapping_labels=paper_mapping_labels,
        locked_contracts=locked_contracts,
    ))
    return issues


def _validate_scored_record_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    status = payload.get("status")
    label = payload.get("evidence_label")
    reason = payload.get("unresolve_reason")
    level = payload.get("unresolve_level")

    if status == "COMPLETED":
        if label not in {"SUCCESS", "FAIL", "UNRESOLVE"}:
            issues.append(_issue("$.evidence_label", "COMPLETED records require SUCCESS, FAIL, or UNRESOLVE"))
        if payload.get("completed_record") is not True or payload.get("infra_exclusion_record") is not False:
            issues.append(_issue("$", "COMPLETED must set completed_record=true and infra_exclusion_record=false"))
        if payload.get("entered_evidence_denominator") is not True or payload.get("entered_denominator_audit") is not True:
            issues.append(_issue("$", "COMPLETED records enter both evidence denominator and denominator audit"))
        issues.extend(_final_attempt_issues(payload, "$"))
    if status == "INFRA_EXCLUDED":
        issues.extend(_infra_label_issues(payload, "$"))
        if payload.get("completed_record") is not False or payload.get("infra_exclusion_record") is not True:
            issues.append(_issue("$", "INFRA_EXCLUDED must set completed_record=false and infra_exclusion_record=true"))
        issues.extend(_final_attempt_issues(payload, "$"))

    issues.extend(_evidence_label_semantic_issues(label, reason, level, "$"))
    issues.extend(_stronger_measurement_issues(payload, "$"))
    issues.extend(_native_decisive_support_issues(payload, "$"))
    issues.extend(_contract_reference_issues(payload, "$", _.get("locked_contracts")))
    issues.extend(_diagnostic_status_issues(payload, "$"))

    if payload.get("phase") in {"smoke", "dry_run"}:
        issues.append(_issue("$.phase", "formal scored_record artifacts cannot use smoke or dry_run phase"))
    if payload.get("phase") in {"smoke", "dry_run"} and payload.get("entered_evidence_denominator") is True:
        issues.append(_issue("$.phase", "smoke/dry_run records cannot enter the formal evidence denominator"))
    if _is_placeholder_string(payload.get("scorer_version")):
        issues.append(_issue("$.scorer_version", "scorer_version must be non-placeholder"))
    return issues


def _validate_infra_exclusion_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues = _infra_label_issues(payload, "$")
    issues.extend(_final_attempt_issues(payload, "$"))
    return issues


def _validate_raw_run_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues = _native_decisive_support_issues(payload, "$")
    issues.extend(_contract_reference_issues(payload, "$", _.get("locked_contracts")))
    issues.extend(_diagnostic_status_issues(payload, "$"))
    if "evidence_label" in payload:
        issues.append(_issue("$.evidence_label", "raw_run cannot carry final evidence labels"))
    return issues


def _validate_artifact_manifest_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues = _contract_reference_issues(payload, "$", _.get("locked_contracts"))
    for index, artifact in enumerate(payload.get("artifacts", [])):
        if not isinstance(artifact, Mapping):
            continue
        base = f"$.artifacts[{index}]"
        native_eval = artifact.get("artifact_type") == "native_evaluator_output" or artifact.get("official_evaluator") is True
        if native_eval:
            if artifact.get("official_runner") is not True:
                issues.append(_issue(f"{base}.official_runner", "native evaluator output requires official_runner=true"))
            if artifact.get("official_evaluator") is not True:
                issues.append(_issue(f"{base}.official_evaluator", "native evaluator output requires official_evaluator=true"))
            if artifact.get("producer_role") != "official_evaluator":
                issues.append(_issue(f"{base}.producer_role", "native evaluator output must be produced by official_evaluator"))
            for field in ("evaluator_name", "evaluator_version", "verified_evaluator_output_object_hash"):
                if not artifact.get(field):
                    issues.append(_issue(f"{base}.{field}", "official evaluator provenance field is required"))
            if artifact.get("artifact_created_after_run_start") is not True:
                issues.append(_issue(f"{base}.artifact_created_after_run_start", "artifact must be created after run start"))
            if not artifact.get("artifact_contract_requirement_ids"):
                issues.append(_issue(f"{base}.artifact_contract_requirement_ids", "official evidence must map to contract requirement ids"))
    return issues


def _validate_aggregate_metrics_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    success = _int(payload.get("SUCCESS"))
    fail = _int(payload.get("FAIL"))
    unresolve = _int(payload.get("UNRESOLVE"))
    n = _int(payload.get("N_completed_scored_records"))
    if None not in (success, fail, unresolve, n) and n != success + fail + unresolve:
        issues.append(_issue("$.N_completed_scored_records", "must equal SUCCESS + FAIL + UNRESOLVE"))
    counted = (success or 0) + (fail or 0)
    if n == 0:
        if counted != 0 or (unresolve or 0) != 0:
            issues.append(_issue("$.N_completed_scored_records", "N=0 aggregates cannot have SUCCESS, FAIL, or UNRESOLVE counts"))
        for field in ("coverage", "lower", "upper", "width"):
            issues.extend(_metric_value_issues(payload, field, 0.0, "$"))
    if counted == 0:
        if payload.get("counted_only_score") is not None:
            issues.append(_issue("$.counted_only_score", "must be null when SUCCESS + FAIL == 0"))
        if payload.get("counted_only_score_undefined_reason") != "no_counted_records":
            issues.append(
                _issue(
                    "$.counted_only_score_undefined_reason",
                    "must be no_counted_records when SUCCESS + FAIL == 0",
                )
            )
    else:
        if payload.get("counted_only_score") is None:
            issues.append(_issue("$.counted_only_score", "must be defined when counted records exist"))
        else:
            issues.extend(_metric_value_issues(payload, "counted_only_score", (success or 0) / counted, "$"))
        if payload.get("counted_only_score_undefined_reason") is not None:
            issues.append(_issue("$.counted_only_score_undefined_reason", "must be null when counted score is defined"))
    if n is not None and n > 0 and None not in (success, fail, unresolve):
        expected_coverage = counted / n
        expected_lower = success / n
        expected_upper = (success + unresolve) / n
        expected_width = unresolve / n
        issues.extend(_metric_value_issues(payload, "coverage", expected_coverage, "$"))
        issues.extend(_metric_value_issues(payload, "lower", expected_lower, "$"))
        issues.extend(_metric_value_issues(payload, "upper", expected_upper, "$"))
        issues.extend(_metric_value_issues(payload, "width", expected_width, "$"))
        observed_upper = payload.get("upper")
        observed_lower = payload.get("lower")
        observed_width = payload.get("width")
        if _is_number(observed_upper) and _is_number(observed_lower) and _is_number(observed_width):
            if not _float_close(float(observed_width), float(observed_upper) - float(observed_lower)):
                issues.append(_issue("$.width", "width must equal upper - lower"))
    if payload.get("claim_scope") == "stronger_measurement" and payload.get("experiment_type") == "main":
        issues.append(_issue("$.claim_scope", "stronger_measurement cannot enter native-aligned main aggregate envelope"))
    return issues


def _validate_experiment_manifest_semantics(
    payload: Mapping[str, Any],
    *,
    formal: bool,
    paper_mapping_labels: set[str] | None,
    **_: Any,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    domains = [d for d in payload.get("domains", []) if isinstance(d, Mapping)]
    exceptions = [e for e in payload.get("official_split_exceptions", []) if isinstance(e, Mapping)]
    exceptions_by_id = {
        e.get("exception_id"): e
        for e in exceptions
        if isinstance(e.get("exception_id"), str) and e.get("exception_recorded_before_scoring") is True
    }
    for index, domain in enumerate(domains):
        base = f"$.domains[{index}]"
        if domain.get("domain") not in CANONICAL_DOMAIN_IDS:
            issues.append(_issue(f"{base}.domain", "domain must use canonical identifier"))
        exception = None
        short_split = (
            domain.get("experiment_type") == "main"
            and domain.get("priority") == "P0"
            and _int(domain.get("official_split_eligible_case_units")) is not None
            and int(domain["official_split_eligible_case_units"]) < 100
        )
        if short_split:
            exception_id = domain.get("official_split_exception_id")
            exception = exceptions_by_id.get(exception_id)
            if not exception:
                issues.append(
                    _issue(
                        f"{base}.official_split_exception_id",
                        "official split has fewer than 100 eligible case units without a referenced recorded exception",
                    )
                )
            else:
                if exception.get("domain") != domain.get("domain"):
                    issues.append(_issue(f"{base}.official_split_exception_id", "official split exception domain mismatch"))
                if exception.get("eligible_case_units") != domain.get("official_split_eligible_case_units"):
                    issues.append(_issue(f"{base}.official_split_exception_id", "official split exception eligible count mismatch"))
                if exception.get("official_split_hash") != domain.get("official_split_hash"):
                    issues.append(_issue(f"{base}.official_split_exception_id", "official split exception hash mismatch"))
        issues.extend(_stronger_measurement_issues(domain, base))
        if formal:
            issues.extend(_p0_main_domain_issues(domain, exception, base))

    if formal:
        issues.extend(_p0_main_manifest_issues(domains, "$.domains"))
        issues.extend(_llm_roles_issues(payload))

    for index, lock in enumerate(payload.get("contract_locks", [])):
        if not isinstance(lock, Mapping):
            continue
        base = f"$.contract_locks[{index}]"
        if lock.get("lock_status") != "locked":
            issues.append(_issue(f"{base}.lock_status", "manifest contract lock entries must be locked"))
        for field in ("contract_id", "contract_version", "contract_hash", "locked_at", "review_record_id", "contract_drafting_llm_call_id", "contract_draft_id"):
            if not lock.get(field):
                issues.append(_issue(f"{base}.{field}", "manifest contract lock linkage field is required"))

    agents = [a for a in payload.get("agents", []) if isinstance(a, Mapping)]
    agent_ids = [a.get("agent_id") for a in agents]
    present_agents = set(agent_ids)
    if len(agents) != len(AGENT_IDS) or present_agents != set(AGENT_IDS) or len(agent_ids) != len(present_agents):
        issues.append(_issue("$.agents", "manifest agents must be exactly one each of Agent A-C"))
    for agent in AGENT_IDS:
        if agent not in present_agents:
            issues.append(_issue("$.agents", f"missing required {agent} entry"))
    for index, agent in enumerate(agents):
        rationale = agent.get("agent_probe_rationale")
        if not isinstance(rationale, Mapping):
            issues.append(_issue(f"$.agents[{index}].agent_probe_rationale", "agent_probe_rationale is required"))
            continue
        if rationale.get("leaderboard_interpretation") is not False:
            issues.append(_issue(f"$.agents[{index}].agent_probe_rationale.leaderboard_interpretation", "must be false"))
    if paper_mapping_labels is not None:
        required = set(str(label) for label in payload.get("required_paper_labels", [])) or REQUIRED_PAPER_LABELS
        for label in sorted(required - paper_mapping_labels):
            issues.append(_issue("$.required_paper_labels", f"missing paper mapping coverage for {label}"))
    return issues


def _validate_agent_config_semantics(payload: Mapping[str, Any], *, formal: bool, **_: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    agents = payload.get("experimental_agents")
    if isinstance(agents, Mapping):
        observed_agents = set(str(agent) for agent in agents)
        if observed_agents != set(AGENT_IDS):
            issues.append(_issue("$.experimental_agents", "experimental_agents must contain exactly Agent A-C and no extra execution agents"))
        for agent in AGENT_IDS:
            agent_config = agents.get(agent)
            if not isinstance(agent_config, Mapping):
                issues.append(_issue(f"$.experimental_agents.{agent}", "missing required fixed probe agent config"))
                continue
            rationale = agent_config.get("agent_probe_rationale")
            if not isinstance(rationale, Mapping):
                issues.append(_issue(f"$.experimental_agents.{agent}.agent_probe_rationale", "agent_probe_rationale is required"))
            elif rationale.get("leaderboard_interpretation") is not False:
                issues.append(
                    _issue(
                        f"$.experimental_agents.{agent}.agent_probe_rationale.leaderboard_interpretation",
                        "must be false",
                    )
                )
    if formal:
        for key in _domain_keys_from_config(payload):
            if key not in CANONICAL_DOMAIN_IDS:
                issues.append(_issue("$.domain_ids", f"non-canonical domain id in formal config: {key}"))
        domain_map = payload.get("main_domain_agent_map")
        if isinstance(domain_map, Mapping):
            missing_domains = P0_MAIN_DOMAIN_IDS - {str(domain_id) for domain_id in domain_map}
            for domain_id in sorted(missing_domains):
                issues.append(_issue("$.main_domain_agent_map", f"missing P0 main domain agent map for {domain_id}"))
            for domain_id, mapped_agents in domain_map.items():
                if domain_id in P0_MAIN_DOMAIN_IDS:
                    if not isinstance(mapped_agents, list) or set(str(agent) for agent in mapped_agents) != set(AGENT_IDS) or len(mapped_agents) != len(AGENT_IDS):
                        issues.append(_issue(f"$.main_domain_agent_map.{domain_id}", "P0 main domains must map to exactly Agent A-C"))
    return issues


def _validate_infra_config_semantics(payload: Mapping[str, Any], *, formal: bool, **_: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not formal:
        return issues

    domain_constraints = payload.get("domain_machine_constraints")
    if isinstance(domain_constraints, Mapping):
        for domain_id in domain_constraints:
            if str(domain_id) not in CANONICAL_DOMAIN_IDS:
                issues.append(_issue(f"$.domain_machine_constraints.{domain_id}", "infra_config domain keys must use canonical identifiers"))

    machines = payload.get("machines")
    if isinstance(machines, list):
        for machine_index, machine in enumerate(machines):
            if not isinstance(machine, Mapping):
                continue
            allowed_domains = machine.get("allowed_domains")
            if isinstance(allowed_domains, list):
                for domain_index, domain_id in enumerate(allowed_domains):
                    if str(domain_id) not in CANONICAL_DOMAIN_IDS:
                        issues.append(
                            _issue(
                                f"$.machines[{machine_index}].allowed_domains[{domain_index}]",
                                "infra_config allowed_domains must use canonical identifiers",
                            )
                        )
            benchmarks = machine.get("benchmarks")
            if isinstance(benchmarks, Mapping):
                for domain_id in benchmarks:
                    if str(domain_id) not in CANONICAL_DOMAIN_IDS:
                        issues.append(
                            _issue(
                                f"$.machines[{machine_index}].benchmarks.{domain_id}",
                                "infra_config benchmark keys must use canonical identifiers",
                            )
                        )
    return issues


def _p0_main_domain_issues(
    domain: Mapping[str, Any],
    exception: Mapping[str, Any] | None,
    base: str,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if domain.get("experiment_type") != "main" or domain.get("priority") != "P0":
        return issues
    domain_id = domain.get("domain")
    if domain_id not in P0_MAIN_DOMAIN_IDS:
        issues.append(_issue(f"{base}.domain", "unexpected P0 main domain; formal P0 uses the four fixed main domains"))
        return issues
    case_units = _int(domain.get("case_unit_count"))
    eligible_units = _int(domain.get("official_split_eligible_case_units"))
    record_slots = _int(domain.get("record_slot_count"))
    expected_case_units = exception.get("eligible_case_units") if exception is not None else P0_DEFAULT_CASE_UNITS_PER_DOMAIN
    if exception is None and domain.get("official_split_exception_id") is not None:
        issues.append(_issue(f"{base}.official_split_exception_id", "official_split_exception_id must reference a recorded exception"))
    if exception is None:
        if eligible_units is None:
            issues.append(_issue(f"{base}.official_split_eligible_case_units", "P0 main domains require official_split_eligible_case_units"))
        elif eligible_units < P0_DEFAULT_CASE_UNITS_PER_DOMAIN:
            issues.append(
                _issue(
                    f"{base}.official_split_eligible_case_units",
                    "P0 main domains with fewer than 100 eligible case units require a recorded split exception",
                )
            )
    if case_units != expected_case_units:
        issues.append(_issue(f"{base}.case_unit_count", "P0 main case_unit_count must match planned eligible case units"))
    if record_slots is not None and case_units is not None and record_slots != case_units * len(AGENT_IDS):
        issues.append(_issue(f"{base}.record_slot_count", "P0 main record_slot_count must equal case_unit_count x 3 fixed agents"))
    if not _is_hash(domain.get("planned_record_slot_ids_hash")):
        issues.append(_issue(f"{base}.planned_record_slot_ids_hash", "P0 main domains require planned_record_slot_ids_hash"))
    return issues


def _p0_main_manifest_issues(domains: Sequence[Mapping[str, Any]], base: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    p0_main_domains = [
        domain
        for domain in domains
        if domain.get("experiment_type") == "main" and domain.get("priority") == "P0"
    ]
    observed = {str(domain.get("domain")) for domain in p0_main_domains}
    missing = P0_MAIN_DOMAIN_IDS - observed
    extra = observed - P0_MAIN_DOMAIN_IDS
    for domain_id in sorted(missing):
        issues.append(_issue(base, f"missing required P0 main domain: {domain_id}"))
    for domain_id in sorted(extra):
        issues.append(_issue(base, f"unexpected P0 main domain: {domain_id}"))
    if len(p0_main_domains) != len(observed):
        issues.append(_issue(base, "duplicate P0 main domain entries are not allowed"))
    total = sum((_int(domain.get("record_slot_count")) or 0) for domain in p0_main_domains)
    expected_total = sum(((_int(domain.get("case_unit_count")) or 0) * len(AGENT_IDS)) for domain in p0_main_domains)
    has_exception = any(domain.get("official_split_exception_id") is not None for domain in p0_main_domains)
    if not has_exception and not missing and not extra and total != P0_DEFAULT_PLANNED_RECORD_SLOTS:
        issues.append(_issue(base, "formal P0 main manifest must plan 1200 record slots without split exceptions"))
    if total != expected_total:
        issues.append(_issue(base, "formal P0 main total record_slot_count must equal planned case units x 3 agents"))
    return issues


def _llm_roles_issues(payload: Mapping[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    roles = payload.get("llm_roles")
    if not isinstance(roles, Mapping):
        return [_issue("$.llm_roles", "formal manifest requires locked llm_roles for Agent A-C, contract_drafter, and judge_only")]

    observed = set(str(role) for role in roles)
    missing = set(LLM_ROLE_IDS) - observed
    extra = observed - set(LLM_ROLE_IDS)
    for role in LLM_ROLE_IDS:
        role_payload = roles.get(role)
        base = f"$.llm_roles.{role}"
        if role in missing:
            issues.append(_issue(base, "formal manifest missing locked LLM role config"))
            continue
        if not isinstance(role_payload, Mapping):
            issues.append(_issue(base, "formal manifest LLM role config must be an object"))
            continue
        required = {
            "provider",
            "model",
            "model_version",
            "api_key_env",
            "temperature",
            "max_tokens",
            "timeout_seconds",
            "retry",
            "rate_limit",
            "save_response_metadata",
            "cost_tracking",
        }
        if role in LLM_PROMPT_ROLE_IDS:
            required.update({"prompt_version", "prompt_hash", "prompt_hash_method"})
        for field in sorted(required):
            value = role_payload.get(field)
            if field not in role_payload or value is None or (isinstance(value, str) and not value):
                issues.append(_issue(f"{base}.{field}", "formal manifest LLM role config field is required"))
            if field == "rate_limit" and not isinstance(value, Mapping):
                issues.append(_issue(f"{base}.{field}", "formal manifest LLM role rate_limit must be an object"))
            if field == "prompt_hash" and not _is_hash(value):
                issues.append(_issue(f"{base}.{field}", "formal manifest prompt_hash must be sha256"))
            if field == "prompt_hash_method" and value != "sha256":
                issues.append(_issue(f"{base}.{field}", "formal manifest prompt_hash_method must be sha256"))
    for role in sorted(extra):
        issues.append(_issue(f"$.llm_roles.{role}", "formal manifest contains undeclared LLM role"))
    return issues


def _validate_llm_call_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    issues.extend(_time_order_issues(payload, "request_timestamp", "response_timestamp", "$"))
    cost = payload.get("cost")
    if isinstance(cost, Mapping):
        amount = cost.get("amount")
        total_cost = cost.get("total_cost_usd")
        reason = cost.get("missing_cost_reason")
        if amount is None and not reason:
            issues.append(_issue("$.cost.missing_cost_reason", "missing cost amount requires missing_cost_reason"))
        if amount is not None and reason is not None:
            issues.append(_issue("$.cost.missing_cost_reason", "must be null when cost amount is present"))
        if amount != total_cost:
            issues.append(_issue("$.cost.total_cost_usd", "total_cost_usd must be the canonical equivalent of amount"))
        pricing_source = cost.get("pricing_source")
        pricing_fields = ("pricing_table_id", "pricing_table_version", "pricing_source_hash")
        method = cost.get("cost_calculation_method")
        if pricing_source == "provider_response":
            if amount is None or total_cost is None:
                issues.append(_issue("$.cost.amount", "provider_response cost requires amount and total_cost_usd"))
            if reason is not None:
                issues.append(_issue("$.cost.missing_cost_reason", "provider_response cost must not carry missing_cost_reason"))
            if method != "provider_reported":
                issues.append(_issue("$.cost.cost_calculation_method", "provider_response requires provider_reported calculation method"))
            if not _is_hash(cost.get("pricing_source_hash")):
                issues.append(_issue("$.cost.pricing_source_hash", "provider_response cost requires provider response/source hash"))
        if pricing_source == "config_estimate":
            for field in pricing_fields:
                if not cost.get(field):
                    issues.append(_issue(f"$.cost.{field}", "config_estimate cost requires pricing table metadata"))
            if method != "tokens_times_config_rate":
                issues.append(_issue("$.cost.cost_calculation_method", "config_estimate requires tokens_times_config_rate"))
            if amount is None or total_cost is None:
                issues.append(_issue("$.cost.amount", "config_estimate must produce amount and total_cost_usd"))
            if reason is not None:
                issues.append(_issue("$.cost.missing_cost_reason", "config_estimate cost must not carry missing_cost_reason"))
        if pricing_source == "unavailable":
            for field in pricing_fields:
                if cost.get(field) is not None:
                    issues.append(_issue(f"$.cost.{field}", "unavailable cost requires pricing table metadata to be null"))
            if method != "unavailable":
                issues.append(_issue("$.cost.cost_calculation_method", "unavailable cost requires unavailable calculation method"))
            if reason is None:
                issues.append(_issue("$.cost.missing_cost_reason", "unavailable cost requires missing_cost_reason"))
            if amount is not None or total_cost is not None:
                issues.append(_issue("$.cost.amount", "unavailable cost requires amount and total_cost_usd to be null"))
    usage = payload.get("token_usage")
    if isinstance(usage, Mapping):
        prompt = _int(usage.get("prompt_tokens")) or 0
        completion = _int(usage.get("completion_tokens")) or 0
        total = _int(usage.get("total_tokens"))
        if total is not None and total < prompt + completion:
            issues.append(_issue("$.token_usage.total_tokens", "must be at least prompt_tokens + completion_tokens"))
    role = payload.get("agent_id_or_role")
    if role in AGENT_IDS:
        for field in ("run_id", "record_slot_id", "attempt_id", "case_unit_id", "task_id"):
            if not payload.get(field):
                issues.append(_issue(f"$.{field}", "Agent A-C execution calls require run/case linkage"))
    if role == "contract_drafter":
        required = (
            "contract_draft_id",
            "case_unit_id",
            "contract_template_version",
            "contract_template_hash",
            "visible_input_hash",
            "hidden_input_assertion_hash",
            "source_bundle_hash",
        )
        for field in required:
            if not payload.get(field):
                issues.append(_issue(f"$.{field}", "contract_drafter calls require draft/source linkage"))
    if role == "judge_only" and not payload.get("forbidden_input_assertion_hash"):
        issues.append(_issue("$.forbidden_input_assertion_hash", "judge_only calls require forbidden-input assertion hash"))
    return issues


def _validate_human_review_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues = _time_order_issues(payload, "review_started_at", "review_finished_at", "$")
    issues.extend(
        _duration_consistency_issues(
            payload,
            "review_started_at",
            "review_finished_at",
            "duration_seconds",
            "seconds",
            "$",
        )
    )
    return issues


def _validate_contract_review_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if payload.get("final_lock_decision") == "lock" and (not payload.get("locked_at") or not payload.get("locked_by")):
        issues.append(_issue("$.locked_at", "lock decision requires locked_at and locked_by"))
    ordering = (
        ("draft_created_at", "review_started_at", True),
        ("review_started_at", "review_finished_at", False),
        ("review_finished_at", "locked_at", True),
        ("locked_at", "first_scoring_started_at", False),
    )
    for start_field, finish_field, allow_equal in ordering:
        issues.extend(_time_pair_issues(payload, start_field, finish_field, "$", allow_equal=allow_equal))
    issues.extend(
        _duration_consistency_issues(
            payload,
            "review_started_at",
            "review_finished_at",
            "duration_minutes",
            "minutes",
            "$",
        )
    )
    return issues


def _validate_human_time_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues = _time_order_issues(payload, "started_at", "finished_at", "$")
    issues.extend(
        _duration_consistency_issues(
            payload,
            "started_at",
            "finished_at",
            "duration_minutes",
            "minutes",
            "$",
        )
    )
    excluded_flags = (
        "no_llm_cost_included",
        "no_vps_cost_included",
        "no_cloud_bill_included",
        "no_benchmark_execution_compute_included",
        "no_local_machine_runtime_included",
    )
    for field in excluded_flags:
        if payload.get(field) is not True:
            issues.append(_issue(f"$.{field}", "human-time logs must explicitly exclude non-human costs"))
    if payload.get("counts_for_cost_table") is True:
        activity_type = payload.get("activity_type")
        if activity_type not in COST_TABLE_ACTIVITY_TYPES:
            issues.append(_issue("$.activity_type", "activity_type is not allowed in tab:cost human-time inputs"))
        if activity_type != "setup" and not payload.get("source_artifacts"):
            issues.append(_issue("$.source_artifacts", "cost-table human-time entries require source artifacts except setup"))
    return issues


def _validate_audit_label_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues = _time_order_issues(payload, "started_at", "finished_at", "$")
    issues.extend(
        _evidence_label_semantic_issues(
            payload.get("evidence_label"),
            payload.get("unresolve_reason"),
            payload.get("unresolve_level"),
            "$",
        )
    )
    return issues


def _validate_evidence_contract_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues = _stronger_measurement_issues(payload, "$")
    support = payload.get("source_support")
    if isinstance(support, Mapping):
        for field in ("evaluator", "task_or_policy", "schema"):
            if not isinstance(support.get(field), str) or not support.get(field).strip():
                issues.append(_issue(f"$.source_support.{field}", "source_support must include evaluator, task_or_policy, and schema support strings"))
    else:
        issues.append(_issue("$.source_support", "source_support must be a mapping with evaluator, task_or_policy, and schema"))
    issues.extend(_repo_local_absolute_path_issues(payload, "$"))
    status = payload.get("contract_status")
    if status == "locked" and (not payload.get("locked_at") or not payload.get("locked_by")):
        issues.append(_issue("$.locked_at", "locked contracts require locked_at and locked_by"))
    if status == "locked" and payload.get("main_result_eligible") is True:
        for field in ("canonicalization_method", "canonical_hash_source", "canonical_hash", "manifest_contract_lock_ref"):
            if not payload.get(field):
                issues.append(_issue(f"$.{field}", "locked main-result contracts require canonical hash and manifest lock linkage"))
        if payload.get("canonical_hash") and payload.get("canonical_hash") != payload.get("contract_hash"):
            issues.append(_issue("$.canonical_hash", "canonical_hash must equal contract_hash"))
    if status in {"clarification", "superseded"}:
        if payload.get("main_result_eligible") is not False:
            issues.append(_issue("$.main_result_eligible", "clarification/superseded contracts cannot enter main results"))
        for field in ("supersedes_contract_id", "supersedes_contract_version", "supersedes_contract_hash", "sensitivity_report_id"):
            if not payload.get(field):
                issues.append(_issue(f"$.{field}", "post-lock clarification requires supersession and sensitivity mapping"))
    for index, artifact in enumerate(payload.get("required_artifacts", [])):
        if not isinstance(artifact, Mapping):
            continue
        if artifact.get("native_aligned_source_support") is True and not artifact.get("contract_requirement_id"):
            issues.append(
                _issue(
                    f"$.required_artifacts[{index}].contract_requirement_id",
                    "native-aligned required artifacts must declare contract_requirement_id",
                )
            )
    return issues


def _repo_local_absolute_path_issues(value: Any, path: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    root = str(repo_root())
    if isinstance(value, Mapping):
        for key, child in value.items():
            issues.extend(_repo_local_absolute_path_issues(child, f"{path}.{key}"))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            issues.extend(_repo_local_absolute_path_issues(child, f"{path}[{index}]"))
    elif isinstance(value, str) and root in value:
        issues.append(_issue(path, "repo-local absolute paths must be recorded as repo-relative source refs"))
    return issues


def _validate_denominator_audit_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    completed = _int(payload.get("completed_records"))
    infra = _int(payload.get("infra_excluded"))
    blocked = _int(payload.get("formally_documented_missing_or_blocked"))
    attempted = _int(payload.get("attempted_record_slots"))
    agent_caused = _int(payload.get("agent_caused_failures"))
    if attempted is not None and None not in (completed, infra, blocked) and attempted != completed + infra + blocked:
        issues.append(_issue("$.attempted_record_slots", "attempted slots must be exactly partitioned into completed, infra exclusions, and blocked slots"))
    if agent_caused is not None:
        if completed is not None and agent_caused > completed:
            issues.append(_issue("$.agent_caused_failures", "agent_caused_failures cannot exceed completed_records"))
        if attempted is not None and agent_caused > attempted:
            issues.append(_issue("$.agent_caused_failures", "agent_caused_failures cannot exceed attempted_record_slots"))

    attempted_ids = payload.get("attempted_record_slot_ids")
    completed_ids = payload.get("completed_record_ids", [])
    infra_ids = payload.get("infra_exclusion_record_ids", [])
    blocked_ids = payload.get("formally_blocked_record_slot_ids", [])

    if completed is not None and len(completed_ids) != completed:
        issues.append(_issue("$.completed_record_ids", "length must match completed_records"))
    if infra is not None and len(infra_ids) != infra:
        issues.append(_issue("$.infra_exclusion_record_ids", "length must match infra_excluded"))
    if blocked is not None and isinstance(blocked_ids, list) and len(blocked_ids) != blocked:
        issues.append(_issue("$.formally_blocked_record_slot_ids", "length must match formally_documented_missing_or_blocked"))
    if attempted is not None and isinstance(attempted_ids, list) and len(attempted_ids) != attempted:
        issues.append(_issue("$.attempted_record_slot_ids", "length must match attempted_record_slots"))
    if isinstance(attempted_ids, list) and all(isinstance(ids, list) for ids in (completed_ids, infra_ids, blocked_ids)):
        attempted_set = set(attempted_ids)
        final_ids = list(completed_ids) + list(infra_ids) + list(blocked_ids)
        final_set = set(final_ids)
        if len(final_ids) != len(final_set):
            issues.append(_issue("$", "denominator final-state partition contains duplicate record slots"))
        missing = attempted_set - final_set
        extra = final_set - attempted_set
        if missing:
            issues.append(_issue("$.attempted_record_slot_ids", "attempted record slots missing final state classification"))
        if extra:
            issues.append(_issue("$", "final-state record slot ids include slots outside attempted set"))
    attempted_hash = payload.get("attempted_record_slot_ids_hash")
    if isinstance(attempted_ids, list):
        computed_attempted_hash = _canonical_string_list_hash(attempted_ids)
        if attempted_hash != computed_attempted_hash:
            issues.append(
                _issue(
                    "$.attempted_record_slot_ids_hash",
                    "attempted_record_slot_ids_hash must equal the canonical hash of attempted_record_slot_ids",
                )
            )
    blocked_hash = payload.get("formally_blocked_record_slot_ids_hash")
    if isinstance(blocked_ids, list):
        computed_blocked_hash = _canonical_string_list_hash(blocked_ids)
        if blocked_hash != computed_blocked_hash:
            issues.append(
                _issue(
                    "$.formally_blocked_record_slot_ids_hash",
                    "formally_blocked_record_slot_ids_hash must equal the canonical hash of formally_blocked_record_slot_ids",
                )
            )
    infra_hash = payload.get("infra_exclusion_records_hash")
    if isinstance(infra_ids, list):
        computed_infra_hash = _canonical_string_list_hash(infra_ids)
        if infra_hash != computed_infra_hash:
            issues.append(
                _issue(
                    "$.infra_exclusion_records_hash",
                    "infra_exclusion_records_hash must equal the canonical hash of infra_exclusion_record_ids",
                )
            )
    return issues


def _validate_paper_output_semantics(
    payload: Mapping[str, Any],
    *,
    paper_mapping_labels: set[str] | None,
    **_: Any,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    label = payload.get("label")
    mapping_label = payload.get("paper_mapping_label")
    if label != mapping_label:
        issues.append(_issue("$.paper_mapping_label", "paper_output.label must exactly equal paper_mapping_label"))
    if paper_mapping_labels is not None and label not in paper_mapping_labels:
        issues.append(_issue("$.paper_mapping_label", f"label is not covered by paper mapping: {label}"))
    source_mapping = [item for item in payload.get("source_mapping", []) if isinstance(item, Mapping)]
    if label in {"tab:cost", "app:cost"}:
        for index, item in enumerate(source_mapping):
            if item.get("source_type") != "human_time":
                issues.append(_issue(f"$.source_mapping[{index}].source_type", f"{label} may only use human_time provenance"))
    if label in NATIVE_ALIGNED_MAIN_OUTPUT_LABELS:
        for index, item in enumerate(source_mapping):
            if item.get("claim_scope") == "stronger_measurement":
                issues.append(
                    _issue(
                        f"$.source_mapping[{index}].claim_scope",
                        "native-aligned main paper outputs cannot use stronger_measurement sources",
                    )
                )
            if item.get("source_type") in {"scored_record", "aggregate_metrics"} and item.get("claim_scope") != "native_aligned":
                issues.append(
                    _issue(
                        f"$.source_mapping[{index}].claim_scope",
                        "native-aligned main scored/aggregate sources must declare claim_scope=native_aligned",
                    )
                )
    return issues


def _aggregate_denominator_consistency_issues(
    payload: Mapping[str, Any],
    objects: Iterable[tuple[str, Mapping[str, Any]]],
    base: str,
) -> list[ValidationIssue]:
    audit = _resolve_aggregate_denominator_audit(payload, objects)
    if audit is None:
        return []
    issues: list[ValidationIssue] = []
    completed = _int(audit.get("completed_records"))
    n = _int(payload.get("N_completed_scored_records"))
    if completed is not None and n is not None and n != completed:
        issues.append(_issue(f"{base}.N_completed_scored_records", "aggregate N_completed_scored_records must match denominator_audit completed_records"))
    source_ids = payload.get("source_scored_record_ids", [])
    if isinstance(source_ids, list) and n is not None and len(source_ids) != n:
        issues.append(_issue(f"{base}.source_scored_record_ids", "aggregate source_scored_record_ids length must match N_completed_scored_records"))
    normalized_source_ids = [str(record_id) for record_id in source_ids if record_id is not None] if isinstance(source_ids, list) else []
    if len(normalized_source_ids) != len(set(normalized_source_ids)):
        issues.append(_issue(f"{base}.source_scored_record_ids", "aggregate source_scored_record_ids must be unique"))
    requires_loaded_scored_records = (
        payload.get("experiment_type") == "main"
        and payload.get("priority") == "P0"
        and ((n or 0) > 0 or bool(normalized_source_ids))
    )
    source_set_hash = payload.get("source_scored_record_set_hash")
    if not normalized_source_ids and (n or 0) == 0:
        empty_hash = _aggregate_source_record_set_hash([])
        if source_set_hash != empty_hash:
            issues.append(
                _issue(
                    f"{base}.source_scored_record_set_hash",
                    "aggregate source_scored_record_set_hash must match the canonical empty source-record set hash",
                )
            )

    scored_records = [
        candidate
        for _, candidate in objects
        if candidate.get("schema_version") == "scored_record/v1"
    ]
    if not scored_records:
        if requires_loaded_scored_records:
            issues.append(
                _issue(
                    f"{base}.source_scored_record_ids",
                    "formal P0 aggregate_metrics with source scored records require loaded scored_record/v1 artifacts",
                )
            )
        return issues
    scored_by_id: dict[str, list[Mapping[str, Any]]] = {}
    for candidate in scored_records:
        record_id = candidate.get("record_id")
        if record_id is None:
            continue
        scored_by_id.setdefault(str(record_id), []).append(candidate)
    duplicate_record_ids = sorted(record_id for record_id, records in scored_by_id.items() if len(records) > 1)
    if duplicate_record_ids:
        issues.append(_issue(f"{base}.source_scored_record_ids", "loaded scored_record artifacts must not duplicate record_id"))
    relevant_completed_slot_counts: Counter[str] = Counter()
    for candidate in scored_records:
        if candidate.get("status") != "COMPLETED":
            continue
        if candidate.get("completed_record") is not True or candidate.get("final_attempt") is not True:
            continue
        if candidate.get("entered_evidence_denominator") is not True:
            continue
        if candidate.get("domain") != payload.get("domain") or candidate.get("claim_scope") != payload.get("claim_scope"):
            continue
        slot_id = candidate.get("record_slot_id")
        if slot_id is not None:
            relevant_completed_slot_counts[str(slot_id)] += 1
    duplicate_completed_slots = sorted(slot_id for slot_id, count in relevant_completed_slot_counts.items() if count > 1)
    if duplicate_completed_slots:
        issues.append(
            _issue(
                f"{base}.source_scored_record_ids",
                "loaded scored_record artifacts must not include multiple final completed scored records for the same record_slot_id",
            )
        )
    resolved: list[Mapping[str, Any]] = []
    for record_id in source_ids:
        matches = scored_by_id.get(str(record_id), [])
        if not matches:
            issues.append(_issue(f"{base}.source_scored_record_ids", "aggregate source_scored_record_ids must resolve to loaded scored_record artifacts"))
            continue
        if len(matches) != 1:
            issues.append(_issue(f"{base}.source_scored_record_ids", "aggregate source_scored_record_ids must resolve uniquely to loaded scored_record artifacts"))
            continue
        resolved.append(matches[0])
    if len(resolved) != len(source_ids):
        return issues
    resolved_record_ids = [str(record.get("record_id")) for record in resolved if record.get("record_id") is not None]
    if len(resolved_record_ids) != len(set(resolved_record_ids)):
        issues.append(_issue(f"{base}.source_scored_record_ids", "aggregate resolved scored_record record_id values must be unique"))
    completed_slots = {
        str(slot_id)
        for slot_id in audit.get("completed_record_ids", [])
        if slot_id is not None
    }
    resolved_slot_ids = [str(record.get("record_slot_id")) for record in resolved if record.get("record_slot_id") is not None]
    if len(resolved_slot_ids) != len(set(resolved_slot_ids)):
        issues.append(_issue(f"{base}.source_scored_record_ids", "aggregate resolved scored_record record_slot_id values must be unique"))
    if completed is not None and len(resolved_slot_ids) != completed:
        issues.append(_issue(f"{base}.source_scored_record_ids", "aggregate resolved scored_record slot count must match denominator_audit completed_records"))
    if set(resolved_slot_ids) != completed_slots:
        issues.append(_issue(f"{base}.source_scored_record_ids", "aggregate resolved scored_record slot set must exactly match denominator_audit completed_record_ids"))
    computed_source_set_hash = _aggregate_source_record_set_hash(resolved)
    if computed_source_set_hash is None:
        issues.append(
            _issue(
                f"{base}.source_scored_record_set_hash",
                "aggregate source scored records must carry source_path and source_sha256 provenance via loaded scored_record artifacts",
            )
        )
    elif source_set_hash != computed_source_set_hash:
        issues.append(
            _issue(
                f"{base}.source_scored_record_set_hash",
                "aggregate source_scored_record_set_hash must match loaded scored_record artifacts",
            )
        )
    label_counts = {"SUCCESS": 0, "FAIL": 0, "UNRESOLVE": 0}
    for index, record in enumerate(resolved):
        if record.get("final_attempt") is not True:
            issues.append(_issue(f"{base}.source_scored_record_ids[{index}]", "aggregate source scored records must be final_attempt=true"))
        if record.get("completed_record") is not True:
            issues.append(_issue(f"{base}.source_scored_record_ids[{index}]", "aggregate source scored records must be completed_record=true"))
        if record.get("entered_evidence_denominator") is not True:
            issues.append(_issue(f"{base}.source_scored_record_ids[{index}]", "aggregate source scored records must enter the evidence denominator"))
        if record.get("claim_scope") != payload.get("claim_scope"):
            issues.append(_issue(f"{base}.source_scored_record_ids[{index}]", "aggregate source scored records must match aggregate claim_scope"))
        if record.get("domain") != payload.get("domain"):
            issues.append(_issue(f"{base}.source_scored_record_ids[{index}]", "aggregate source scored records must match aggregate domain"))
        if record.get("record_slot_id") not in completed_slots:
            issues.append(_issue(f"{base}.source_scored_record_ids[{index}]", "aggregate source scored record slot must appear in denominator_audit completed_record_ids"))
        label = record.get("evidence_label")
        if label in label_counts:
            label_counts[label] += 1
    for label, count in label_counts.items():
        observed = _int(payload.get(label))
        if observed is not None and observed != count:
            issues.append(_issue(f"{base}.{label}", f"aggregate {label} count must match loaded scored_record evidence labels"))
    return issues


def _aggregate_source_record_set_hash(records: Sequence[Mapping[str, Any]]) -> str | None:
    entries: list[dict[str, str]] = []
    for record in records:
        record_id = record.get("record_id")
        record_slot_id = record.get("record_slot_id")
        source_path = record.get("__path") or record.get("__abs_path")
        source_sha = record.get("__sha256")
        if not record_id or not record_slot_id or not source_path or not _is_hash(source_sha):
            return None
        entries.append(
            {
                "record_id": str(record_id),
                "record_slot_id": str(record_slot_id),
                "source_path": str(source_path),
                "source_sha256": str(source_sha),
            }
        )
    canonical = json.dumps(sorted(entries, key=lambda item: item["record_id"]), ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return sha256_bytes(canonical.encode("utf-8"))


def _canonical_string_list_hash(values: Sequence[Any]) -> str:
    normalized = [str(value) for value in values]
    canonical = json.dumps(normalized, ensure_ascii=True, separators=(",", ":"))
    return sha256_bytes(canonical.encode("utf-8"))


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _float_close(observed: float, expected: float) -> bool:
    return abs(observed - expected) <= 1e-9


def _metric_value_issues(payload: Mapping[str, Any], field: str, expected: float, base: str) -> list[ValidationIssue]:
    observed = payload.get(field)
    if not _is_number(observed):
        return [_issue(f"{base}.{field}", f"{field} must be numeric")]
    if not _float_close(float(observed), expected):
        return [_issue(f"{base}.{field}", f"{field} must equal derived aggregate value")]
    return []


def _deterministic_selection_hash_issues(selection: Mapping[str, Any] | None, base: str) -> list[ValidationIssue]:
    if selection is None:
        return []
    excluded = selection.get("excluded_smoke_case_units")
    smoke_hash = selection.get("smoke_exclusion_hash")
    if isinstance(excluded, list):
        expected = _canonical_string_list_hash(excluded)
        if smoke_hash != expected:
            return [
                _issue(
                    f"{base}.smoke_exclusion_hash",
                    "smoke_exclusion_hash must equal the canonical hash of excluded_smoke_case_units",
                )
            ]
    return []


def _validate_stats_plan_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if (
        payload.get("threshold_boundary_rule") == "strict_interval"
        and payload.get("interval_touching_threshold") != "inconclusive"
    ):
        issues.append(_issue("$.interval_touching_threshold", "strict interval rule requires touching threshold to be inconclusive"))
    return issues


def _validate_job_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if payload.get("domain") not in CANONICAL_DOMAIN_IDS:
        issues.append(_issue("$.domain", "domain must use canonical identifier before job hashing or execution"))
    issues.extend(_contract_reference_issues(payload, "$", _.get("locked_contracts")))
    return issues


def _validate_freeze_manifest_semantics(payload: Mapping[str, Any], *, formal: bool, **_: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if _is_placeholder_string(payload.get("scorer_version")):
        issues.append(_issue("$.scorer_version", "freeze manifest scorer_version must be non-placeholder"))
    return issues


def _validate_failure_record_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    provenance = payload.get("provenance")
    workflow_stage = payload.get("workflow_stage")
    required = (
        "command_hash",
        "config_hash",
        "manifest_hash",
        "environment_hash",
        "machine_id",
        "workflow_stage",
        "source_path",
        "source_sha256",
        "failure_linkage",
    )
    if not isinstance(provenance, Mapping):
        return [_issue("$.provenance", "failure_record provenance must be a structured object")]
    for field in required:
        if not provenance.get(field):
            issues.append(_issue(f"$.provenance.{field}", "failure provenance field is required"))
    for hash_field in ("command_hash", "config_hash", "manifest_hash", "environment_hash", "source_sha256"):
        if provenance.get(hash_field) and not _is_hash(provenance.get(hash_field)):
            issues.append(_issue(f"$.provenance.{hash_field}", "failure provenance hash field must be sha256"))
    for field in ("command_hash", "workflow_stage", "machine_id"):
        if payload.get(field) and provenance.get(field) and payload.get(field) != provenance.get(field):
            issues.append(_issue(f"$.provenance.{field}", "failure provenance must match top-level failure field"))
    failure_linkage = provenance.get("failure_linkage")
    if isinstance(failure_linkage, Mapping) and workflow_stage in DEPLOY_COLLECT_RESUME_WORKFLOW_STAGES:
        top_deployment_path = payload.get("deployment_manifest_path")
        linked_deployment_path = failure_linkage.get("deployment_manifest_path")
        if not _is_nonempty_string(top_deployment_path):
            issues.append(
                _issue(
                    "$.deployment_manifest_path",
                    "deploy/collect/resume failure records require deployment manifest provenance",
                )
            )
        if not _is_nonempty_string(linked_deployment_path):
            issues.append(
                _issue(
                    "$.provenance.failure_linkage.deployment_manifest_path",
                    "deploy/collect/resume failure records require deployment manifest provenance",
                )
            )
        elif _is_nonempty_string(top_deployment_path) and linked_deployment_path != top_deployment_path:
            issues.append(
                _issue(
                    "$.provenance.failure_linkage.deployment_manifest_path",
                    "failure linkage deployment_manifest_path must match top-level deployment_manifest_path",
                )
            )
    if workflow_stage == "collect_results" and not _is_nonempty_string(payload.get("collect_results_manifest_path")):
        issues.append(
            _issue(
                "$.collect_results_manifest_path",
                "collect_results failure records require collect_results_manifest_path",
            )
        )
    if workflow_stage == "resume_failed" and not _is_nonempty_string(payload.get("resume_manifest_path")):
        issues.append(
            _issue(
                "$.resume_manifest_path",
                "resume_failed failure records require resume_manifest_path",
            )
        )
    return issues


def _validate_deployment_manifest_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues = _time_order_issues(payload, "started_at", "finished_at", "$")
    workflow_stage = payload.get("workflow_stage")
    if workflow_stage == "collect_results" and not payload.get("artifacts"):
        issues.append(_issue("$.artifacts", "collect_results deployment manifests require collected artifact provenance"))
    if workflow_stage == "resume_failed" and not payload.get("failure_record_paths"):
        issues.append(_issue("$.failure_record_paths", "resume_failed manifests require failure record linkage"))
    return issues


def _failure_record_deployment_manifest_issues(
    payload: Mapping[str, Any],
    objects: Iterable[tuple[str, Mapping[str, Any]]],
    base: str,
) -> list[ValidationIssue]:
    workflow_stage = payload.get("workflow_stage")
    if workflow_stage not in DEPLOY_COLLECT_RESUME_WORKFLOW_STAGES:
        return []

    issues: list[ValidationIssue] = []
    linkage = payload.get("provenance", {}).get("failure_linkage") if isinstance(payload.get("provenance"), Mapping) else None
    expected_paths = {
        str(path)
        for path in (
            payload.get("deployment_manifest_path"),
            linkage.get("deployment_manifest_path") if isinstance(linkage, Mapping) else None,
        )
        if _is_nonempty_string(path)
    }
    deployment_manifests = [
        candidate
        for _, candidate in objects
        if candidate.get("schema_version") == "deployment_manifest/v1"
    ]
    if not deployment_manifests:
        return [
            _issue(
                f"{base}.deployment_manifest_path",
                "deploy/collect/resume failure records require loaded deployment_manifest artifact",
            )
        ]
    matching_manifests: list[Mapping[str, Any]] = []
    for manifest in deployment_manifests:
        actual_paths = {
            str(path)
            for path in (manifest.get("__path"), manifest.get("__abs_path"))
            if _is_nonempty_string(path)
        }
        if expected_paths and expected_paths.isdisjoint(actual_paths):
            continue
        matching_manifests.append(manifest)
    if not matching_manifests:
        return [
            _issue(
                f"{base}.deployment_manifest_path",
                "failure_record deployment_manifest_path must resolve to a loaded deployment_manifest/v1 artifact",
            )
        ]

    provenance = payload.get("provenance")
    provenance_map = provenance if isinstance(provenance, Mapping) else {}
    for manifest in matching_manifests:
        for field in ("workflow_stage", "machine_id", "command_hash", "domain", "phase", "experiment_type", "priority"):
            observed = payload.get(field)
            expected = manifest.get(field)
            if observed is not None and expected is not None and observed != expected:
                issues.append(_issue(f"{base}.{field}", "failure_record deployment manifest linkage field mismatch"))
        for field in ("config_hash", "manifest_hash", "environment_hash"):
            observed = provenance_map.get(field)
            expected = manifest.get(field)
            if observed is not None and expected is not None and observed != expected:
                issues.append(_issue(f"{base}.provenance.{field}", "failure_record deployment manifest provenance hash mismatch"))
    return issues


def _validate_prediction_outcome_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if (
        payload.get("threshold_boundary_rule") == "strict_interval"
        and payload.get("interval_touching_threshold") != "inconclusive"
    ):
        issues.append(_issue("$.interval_touching_threshold", "strict interval rule requires touching threshold to be inconclusive"))
    lower = payload.get("ci_lower")
    upper = payload.get("ci_upper")
    if isinstance(lower, (int, float)) and isinstance(upper, (int, float)) and lower > upper:
        issues.append(_issue("$.ci_lower", "ci_lower must be <= ci_upper"))
    threshold = payload.get("threshold")
    if (
        payload.get("threshold_boundary_rule") == "strict_interval"
        and isinstance(threshold, (int, float))
        and (lower == threshold or upper == threshold)
        and payload.get("outcome") != "inconclusive"
    ):
        issues.append(_issue("$.outcome", "interval touching threshold must be inconclusive under strict_interval"))
    return issues


def _validate_pairwise_matrix_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    agents = [agent for agent in payload.get("agents", []) if isinstance(agent, str)]
    if payload.get("experiment_type") == "main" and payload.get("priority") == "P0":
        if set(agents) != set(AGENT_IDS) or len(agents) != len(AGENT_IDS):
            issues.append(_issue("$.agents", "P0 main pairwise_matrix must contain exactly one each of Agent A-C"))
    expected_pairs = {tuple(sorted((a, b))) for i, a in enumerate(agents) for b in agents[i + 1 :]}
    seen_pairs: set[tuple[str, str]] = set()
    for index, cell in enumerate(payload.get("cells", [])):
        if not isinstance(cell, Mapping):
            continue
        pair = tuple(sorted((str(cell.get("agent_i")), str(cell.get("agent_j")))))
        if pair in seen_pairs:
            issues.append(_issue(f"$.cells[{index}]", "duplicate pairwise matrix cell"))
        seen_pairs.add(pair)
        if cell.get("relation") in {">", "<"} and cell.get("margin") is None:
            issues.append(_issue(f"$.cells[{index}].margin", "separated pairwise relations require margin"))
        if cell.get("relation") == "=" and cell.get("margin") not in {0, 0.0, None}:
            issues.append(_issue(f"$.cells[{index}].margin", "equality relation must not carry non-zero margin"))
    missing = expected_pairs - seen_pairs
    for pair in sorted(missing):
        issues.append(_issue("$.cells", f"missing pairwise matrix cell for {pair[0]} vs {pair[1]}"))
    return issues


def _validate_release_artifact_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if payload.get("visibility") != payload.get("release_status"):
        issues.append(_issue("$.release_status", "release_status must match visibility"))
    if payload.get("visibility") == "public" and payload.get("redaction_status") not in {"not_needed", "redacted"}:
        issues.append(_issue("$.redaction_status", "public release artifacts must be redacted or not need redaction"))
    if payload.get("visibility") == "not_released" and payload.get("redaction_status") != "blocked":
        issues.append(_issue("$.redaction_status", "not_released artifacts require blocked redaction status"))
    return issues


def _validate_rerun_record_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if payload.get("original_evidence_label") != "UNRESOLVE" and payload.get("original_unresolve_reason") is not None:
        issues.append(_issue("$.original_unresolve_reason", "counted original rerun labels cannot carry UNRESOLVE reason"))
    if payload.get("rerun_evidence_label") != "UNRESOLVE" and payload.get("rerun_unresolve_reason") is not None:
        issues.append(_issue("$.rerun_unresolve_reason", "counted rerun labels cannot carry UNRESOLVE reason"))
    return issues


def _validate_rerun_subset_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    if payload.get("agent_id") != "Agent A":
        return [_issue("$.agent_id", "paper rerun subset must use Agent A")]
    return []


def _validate_audit_item_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    if not payload.get("forbidden_input_assertion_hash"):
        return [_issue("$.forbidden_input_assertion_hash", "audit items require forbidden-input assertion hash")]
    return []


def _validate_audit_sampling_plan_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    required_strata = {"counted_records", "unresolve_records", "native_evidence_disagreement"}
    observed = set(payload.get("strata", []))
    missing = required_strata - observed
    for stratum in sorted(missing):
        issues.append(_issue("$.strata", f"missing required audit stratum: {stratum}"))
    return issues


def _validate_bootstrap_plan_semantics(payload: Mapping[str, Any], **_: Any) -> list[ValidationIssue]:
    if payload.get("cluster_unit") != "case_unit" or payload.get("preserve_agent_records") is not True:
        return [_issue("$", "bootstrap plan must resample case_unit clusters and preserve agent records")]
    return []


def _evidence_label_semantic_issues(label: Any, reason: Any, level: Any, base: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if label == "UNRESOLVE":
        if reason not in UNRESOLVE_REASONS:
            issues.append(_issue(f"{base}.unresolve_reason", "UNRESOLVE requires exactly one R1-R7 reason code"))
        if level not in UNRESOLVE_LEVELS:
            issues.append(_issue(f"{base}.unresolve_level", "UNRESOLVE requires trace_level or instrument_level"))
    if label in {"SUCCESS", "FAIL"}:
        if reason is not None:
            issues.append(_issue(f"{base}.unresolve_reason", "SUCCESS/FAIL cannot carry unresolve_reason"))
        if level is not None:
            issues.append(_issue(f"{base}.unresolve_level", "SUCCESS/FAIL cannot carry unresolve_level"))
    return issues


def _contract_reference_issues(
    payload: Mapping[str, Any],
    base: str,
    locked_contracts: Mapping[str, Any] | None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    issues.extend(_validate_contract_reference(payload, base, locked_contracts))
    return issues


def _validate_contract_reference(
    payload: Mapping[str, Any],
    base: str,
    locked_contracts: Mapping[str, Any] | None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    contract_id = payload.get("contract_id")
    evidence_contract_id = payload.get("evidence_contract_id")
    contract_version = payload.get("contract_version")
    evidence_contract_version = payload.get("evidence_contract_version")
    contract_hash = payload.get("contract_hash")
    evidence_contract_hash = payload.get("evidence_contract_hash")

    if not any((contract_id, evidence_contract_id, contract_version, evidence_contract_version, contract_hash, evidence_contract_hash)):
        return issues

    if contract_id and evidence_contract_id and contract_id != evidence_contract_id:
        issues.append(_issue(f"{base}.contract_id", "contract_id must equal evidence_contract_id"))
    if contract_version and evidence_contract_version and contract_version != evidence_contract_version:
        issues.append(_issue(f"{base}.contract_version", "contract_version must equal evidence_contract_version"))
    if contract_hash and evidence_contract_hash and contract_hash != evidence_contract_hash:
        issues.append(_issue(f"{base}.contract_hash", "contract_hash must equal evidence_contract_hash"))
    if locked_contracts is None:
        return issues

    key = _contract_key(
        {
            "contract_id": contract_id or evidence_contract_id,
            "contract_version": contract_version or evidence_contract_version,
        }
    )
    lock = locked_contracts.get(key) or locked_contracts.get(str(contract_id or evidence_contract_id))
    if not lock:
        issues.append(_issue(f"{base}.contract_id", "contract reference is absent from locked contract registry"))
        return issues
    expected_hash = _registry_contract_hash(lock)
    observed_hash = contract_hash or evidence_contract_hash
    if expected_hash and observed_hash and observed_hash != expected_hash:
        issues.append(_issue(f"{base}.contract_hash", "contract_hash does not match locked contract canonical hash"))
    if expected_hash and observed_hash is None and _requires_locked_contract_hash(payload):
        issues.append(_issue(f"{base}.contract_hash", "contract reference requires contract_hash or evidence_contract_hash"))
    if lock.get("schema_version") == "evidence_contract/v1":
        if lock.get("contract_status") != "locked":
            issues.append(_issue(f"{base}.contract_id", "locked contract registry entry is not locked"))
        if lock.get("main_result_eligible") is not True:
            issues.append(_issue(f"{base}.contract_id", "locked contract registry entry is not main_result_eligible"))
    elif lock.get("lock_status") != "locked":
        issues.append(_issue(f"{base}.contract_id", "locked contract registry entry is not locked"))
    if not lock.get("locked_at"):
        issues.append(_issue(f"{base}.contract_id", "locked contract registry entry is missing locked_at"))
    return issues


def _diagnostic_status_issues(payload: Mapping[str, Any], base: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    diagnostic_status = payload.get("diagnostic_status")
    failure_class = payload.get("appendix_failure_class")
    label = payload.get("evidence_label")
    domain = payload.get("domain")
    record_status = payload.get("status")

    if diagnostic_status in {"evaluator_failure", "evaluator_unstable"}:
        if label in {"SUCCESS", "FAIL", "UNRESOLVE"}:
            issues.append(
                _issue(
                    f"{base}.diagnostic_status",
                    "evaluator failure/unstable is diagnostic and must not carry evidence SUCCESS/FAIL/UNRESOLVE",
                )
            )
    diagnostic_status_to_class = {
        "not_applicable": "none",
        "infra_excluded": "infra_pre_run",
        "evaluator_failure": "evaluator_failure",
        "evaluator_unstable": "evaluator_unstable",
    }
    expected_diagnostic_class = diagnostic_status_to_class.get(diagnostic_status)
    if expected_diagnostic_class is not None and failure_class != expected_diagnostic_class:
        issues.append(_issue(f"{base}.appendix_failure_class", "diagnostic_status and appendix_failure_class mismatch"))

    expected_by_record_status = {
        "INFRA_EXCLUDED": ("infra_excluded", "infra_pre_run"),
        "EVALUATOR_FAILURE": ("evaluator_failure", "evaluator_failure"),
        "EVALUATOR_UNSTABLE": ("evaluator_unstable", "evaluator_unstable"),
    }
    if record_status in expected_by_record_status:
        expected_status, expected_class = expected_by_record_status[record_status]
        if diagnostic_status != expected_status:
            issues.append(_issue(f"{base}.diagnostic_status", f"{record_status} requires diagnostic_status={expected_status}"))
        if failure_class != expected_class:
            issues.append(_issue(f"{base}.appendix_failure_class", "diagnostic_status and appendix_failure_class mismatch"))
        if record_status in {"EVALUATOR_FAILURE", "EVALUATOR_UNSTABLE"} and label in {"SUCCESS", "FAIL", "UNRESOLVE"}:
            issues.append(_issue(f"{base}.evidence_label", f"{record_status} must not carry evidence SUCCESS/FAIL/UNRESOLVE"))

    if record_status == "COMPLETED":
        if diagnostic_status != "completed":
            issues.append(_issue(f"{base}.diagnostic_status", "COMPLETED requires diagnostic_status=completed"))
        if failure_class not in {"none", "evidence_unresolve"}:
            issues.append(_issue(f"{base}.appendix_failure_class", "COMPLETED diagnostic records may only use none or evidence_unresolve"))
        if label in {"SUCCESS", "FAIL"} and failure_class != "none":
            issues.append(_issue(f"{base}.appendix_failure_class", "COMPLETED SUCCESS/FAIL records require appendix_failure_class=none"))

    if domain == "osworld_verified" and diagnostic_status == "completed" and label == "UNRESOLVE" and failure_class != "evidence_unresolve":
        issues.append(
            _issue(
                f"{base}.appendix_failure_class",
                "OSWorld completed evidence UNRESOLVE must use appendix_failure_class=evidence_unresolve",
            )
        )
    return issues


def _infra_label_issues(payload: Mapping[str, Any], base: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if payload.get("evidence_label") not in {None, "NOT_APPLICABLE"}:
        issues.append(_issue(f"{base}.evidence_label", "INFRA_EXCLUDED must not carry SUCCESS/FAIL/UNRESOLVE evidence labels"))
    if payload.get("unresolve_reason") is not None or payload.get("unresolve_level") is not None:
        issues.append(_issue(base, "INFRA_EXCLUDED cannot carry UNRESOLVE reason or level"))
    if payload.get("entered_evidence_denominator") is not False:
        issues.append(_issue(f"{base}.entered_evidence_denominator", "INFRA_EXCLUDED is excluded from evidence denominator"))
    if payload.get("entered_denominator_audit") is not True:
        issues.append(_issue(f"{base}.entered_denominator_audit", "INFRA_EXCLUDED must remain in denominator audit"))
    return issues


def _final_attempt_issues(payload: Mapping[str, Any], base: str) -> list[ValidationIssue]:
    if (
        payload.get("entered_evidence_denominator") is True
        or payload.get("entered_denominator_audit") is True
        or payload.get("completed_record") is True
        or payload.get("infra_exclusion_record") is True
    ) and payload.get("final_attempt") is not True:
        return [_issue(f"{base}.final_attempt", "denominator final-state records must be final_attempt=true")]
    return []


def _stronger_measurement_issues(payload: Mapping[str, Any], base: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    claim_scope = payload.get("claim_scope")
    mapping = payload.get("stronger_measurement_mapping")
    if claim_scope == "stronger_measurement":
        if not isinstance(mapping, Mapping):
            issues.append(_issue(f"{base}.stronger_measurement_mapping", "stronger_measurement requires sidecar/appendix/manifest mapping"))
        elif mapping.get("enters_native_aligned_main_envelope") is not False:
            issues.append(
                _issue(
                    f"{base}.stronger_measurement_mapping.enters_native_aligned_main_envelope",
                    "stronger_measurement must not enter native-aligned main envelope",
                )
            )
        if payload.get("experiment_type") == "main" and payload.get("entered_evidence_denominator") is True:
            issues.append(_issue(f"{base}.claim_scope", "stronger_measurement cannot enter native-aligned main envelope"))
    elif claim_scope == "native_aligned" and isinstance(mapping, Mapping):
        if mapping.get("enters_native_aligned_main_envelope") is not False:
            issues.append(
                _issue(
                    f"{base}.stronger_measurement_mapping.enters_native_aligned_main_envelope",
                    "native_aligned stronger-measurement sidecar mapping must not enter native-aligned main envelope",
                )
            )
    return issues


def _native_decisive_support_issues(payload: Mapping[str, Any], base: str) -> list[ValidationIssue]:
    if payload.get("native_label_used_as_decisive_evidence") is not True:
        return []
    support = payload.get("native_decisive_support")
    issues: list[ValidationIssue] = []
    if not isinstance(support, Mapping):
        return [_issue(f"{base}.native_decisive_support", "decisive native evidence requires locked artifact support")]
    required_true = ("locked_artifact_mapping", "official_provenance", "verified_object_or_direct_artifact_read")
    for field in required_true:
        if support.get(field) is not True:
            issues.append(_issue(f"{base}.native_decisive_support.{field}", "must be true for decisive native evidence"))
    for field in ("artifact_id", "contract_requirement_id"):
        if not support.get(field):
            issues.append(_issue(f"{base}.native_decisive_support.{field}", "is required for decisive native evidence"))
    if not support.get("artifact_manifest_path"):
        issues.append(_issue(f"{base}.native_decisive_support.artifact_manifest_path", "artifact manifest path is required"))
    if not _is_hash(support.get("artifact_manifest_sha256")):
        issues.append(_issue(f"{base}.native_decisive_support.artifact_manifest_sha256", "artifact manifest sha256 is required"))
    if not _is_hash(support.get("artifact_sha256")):
        issues.append(_issue(f"{base}.native_decisive_support.artifact_sha256", "artifact sha256 is required"))
    if not _is_hash(support.get("verified_evaluator_output_object_hash")):
        issues.append(
            _issue(
                f"{base}.native_decisive_support.verified_evaluator_output_object_hash",
                "verified evaluator output object hash is required",
            )
        )
    return issues


def _time_order_issues(payload: Mapping[str, Any], start_field: str, finish_field: str, base: str) -> list[ValidationIssue]:
    return _time_pair_issues(payload, start_field, finish_field, base, allow_equal=False)


def _time_pair_issues(
    payload: Mapping[str, Any],
    start_field: str,
    finish_field: str,
    base: str,
    *,
    allow_equal: bool,
) -> list[ValidationIssue]:
    start = _parse_time(payload.get(start_field))
    finish = _parse_time(payload.get(finish_field))
    if start is None or finish is None:
        return []
    if allow_equal:
        if start > finish:
            return [_issue(f"{base}.{finish_field}", f"{start_field} must be <= {finish_field}")]
    elif start >= finish:
        return [_issue(f"{base}.{finish_field}", f"{finish_field} must be after {start_field}")]
    return []


def _duration_consistency_issues(
    payload: Mapping[str, Any],
    start_field: str,
    finish_field: str,
    duration_field: str,
    unit: str,
    base: str,
) -> list[ValidationIssue]:
    start = _parse_time(payload.get(start_field))
    finish = _parse_time(payload.get(finish_field))
    observed = payload.get(duration_field)
    if start is None or finish is None or not isinstance(observed, (int, float)) or isinstance(observed, bool):
        return []
    elapsed_seconds = (finish - start).total_seconds()
    expected = elapsed_seconds if unit == "seconds" else elapsed_seconds / 60.0
    tolerance = 1e-6
    if abs(float(observed) - expected) > tolerance:
        return [_issue(f"{base}.{duration_field}", f"{duration_field} must match {start_field} to {finish_field}")]
    return []


def _timestamp_parseability_issues(value: Any, path: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = _join_path(path, str(key))
            key_text = str(key)
            is_timestamp_field = (
                key_text in TIMESTAMP_FIELD_NAMES
                or key_text.endswith("_at")
                or key_text.endswith("_timestamp")
            )
            if is_timestamp_field and child is not None:
                if not isinstance(child, str) or _parse_time(child) is None:
                    issues.append(_issue(child_path, "timestamp field must be parseable ISO-8601"))
            issues.extend(_timestamp_parseability_issues(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(_timestamp_parseability_issues(child, f"{path}[{index}]"))
    return issues


def _placeholder_issues(value: Any, path: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker.lower() in lowered for marker in PLACEHOLDER_MARKERS):
            issues.append(_issue(path, "formal validation cannot contain unresolved placeholder values"))
    elif isinstance(value, Mapping):
        for key, child in value.items():
            issues.extend(_placeholder_issues(child, _join_path(path, str(key))))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(_placeholder_issues(child, f"{path}[{index}]"))
    return issues


def _is_placeholder_string(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return True
    lowered = value.lower()
    return any(marker.lower() in lowered for marker in PLACEHOLDER_MARKERS)


def _iter_contract_locks(payload: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    locks = payload.get("contract_locks")
    if isinstance(locks, list):
        for lock in locks:
            if isinstance(lock, Mapping):
                yield lock
    if payload.get("schema_version") == "evidence_contract/v1":
        yield payload


def _contract_registry_entry_issues(lock: Mapping[str, Any], base: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    is_evidence_contract = lock.get("schema_version") == "evidence_contract/v1"
    if is_evidence_contract:
        if lock.get("contract_status") != "locked":
            issues.append(_issue(f"{base}.contract_status", "evidence_contract registry sources must be locked"))
        if lock.get("main_result_eligible") is not True:
            issues.append(_issue(f"{base}.main_result_eligible", "locked evidence_contract registry sources must be main_result_eligible=true"))
        if lock.get("claim_scope") == "stronger_measurement":
            issues.append(_issue(f"{base}.claim_scope", "stronger_measurement contracts cannot be main-result lock sources"))
        required_fields = (
            "contract_id",
            "contract_version",
            "contract_hash",
            "locked_at",
            "locked_by",
            "review_record_id",
            "contract_drafting_llm_call_id",
            "contract_draft_id",
            "canonicalization_method",
            "canonical_hash_source",
            "canonical_hash",
            "manifest_contract_lock_ref",
        )
    else:
        if lock.get("lock_status") != "locked":
            issues.append(_issue(f"{base}.lock_status", "manifest contract lock registry entries must be locked"))
        if lock.get("main_result_eligible") is not True:
            issues.append(_issue(f"{base}.main_result_eligible", "manifest lock registry entries must be main_result_eligible=true"))
        required_fields = (
            "contract_id",
            "contract_version",
            "contract_hash",
            "locked_at",
            "review_record_id",
            "contract_drafting_llm_call_id",
            "contract_draft_id",
            "canonicalization_method",
            "main_result_eligible",
        )
    for field in required_fields:
        if not lock.get(field):
            issues.append(_issue(f"{base}.{field}", "locked contract registry linkage field is required"))
    canonical_hash = lock.get("canonical_hash")
    contract_hash = lock.get("contract_hash")
    if canonical_hash is not None and contract_hash is not None and canonical_hash != contract_hash:
        issues.append(_issue(f"{base}.canonical_hash", "canonical_hash must equal contract_hash"))
    return issues


def _registry_contract_hash(lock: Mapping[str, Any]) -> Any:
    return lock.get("contract_hash") or lock.get("canonical_hash")


def _requires_locked_contract_hash(payload: Mapping[str, Any]) -> bool:
    schema_version = payload.get("schema_version")
    return schema_version in {
        "job/v1",
        "raw_run/v1",
        "scored_record/v1",
        "artifact_manifest/v1",
        "evidence_contract/v1",
    }


def _contract_key(payload: Mapping[str, Any]) -> str | None:
    contract_id = payload.get("contract_id") or payload.get("evidence_contract_id")
    contract_version = payload.get("contract_version") or payload.get("evidence_contract_version")
    if not contract_id:
        return None
    if contract_version:
        return f"{contract_id}:{contract_version}"
    return str(contract_id)


def _deterministic_selection_view(payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
    selection = payload.get("deterministic_selection")
    if isinstance(selection, Mapping):
        return selection
    required = {
        "hash_function",
        "hash_salt_hash",
        "eligible_case_unit_set_hash",
        "smoke_exclusion_hash",
        "case_selection_order_hash",
        "bootstrap_seed",
        "bootstrap_resample_count",
        "audit_sample_seed",
        "rerun_subset_selection_rule",
    }
    if required.issubset(payload.keys()):
        return payload
    return None


def _freeze_drift_issues(payload: Mapping[str, Any], freeze_manifest: Mapping[str, Any], base: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if payload is freeze_manifest or payload.get("schema_version") == "freeze_manifest/v1":
        return issues

    schema_version = payload.get("schema_version")
    if schema_version == "scored_record/v1":
        comparisons = (
            ("scorer_version", "scorer_version"),
            ("scorer_code_hash", "scorer_code_hash"),
            ("result_schema_hash", "result_schema_hash"),
            ("taxonomy_version", "taxonomy_version"),
        )
        for payload_field, freeze_field in comparisons:
            expected = freeze_manifest.get(freeze_field)
            observed = payload.get(payload_field)
            if expected is not None and observed is not None and observed != expected:
                issues.append(_issue(f"{base}.{payload_field}", f"{payload_field} drift from freeze manifest"))
        actual_freeze_hash = freeze_manifest.get("__sha256")
        observed_freeze_hash = payload.get("freeze_manifest_hash")
        if actual_freeze_hash is not None and observed_freeze_hash != actual_freeze_hash:
            issues.append(_issue(f"{base}.freeze_manifest_hash", "freeze_manifest_hash does not match freeze manifest artifact sha256"))
        frozen_at = _parse_time(freeze_manifest.get("frozen_at"))
        scoring_started_at = _parse_time(payload.get("started_at"))
        if frozen_at is not None and scoring_started_at is not None and frozen_at > scoring_started_at:
            issues.append(_issue(f"{base}.started_at", "freeze time must be at or before scoring start"))
    elif schema_version == "aggregate_metrics/v1":
        actual_freeze_hash = freeze_manifest.get("__sha256")
        observed_freeze_hash = payload.get("freeze_manifest_hash")
        if actual_freeze_hash is not None and observed_freeze_hash != actual_freeze_hash:
            issues.append(_issue(f"{base}.freeze_manifest_hash", "aggregate freeze_manifest_hash does not match freeze manifest artifact sha256"))

    if payload.get("manifest_hash") is not None and freeze_manifest.get("manifest_hash") is not None:
        if payload.get("manifest_hash") != freeze_manifest.get("manifest_hash"):
            issues.append(_issue(f"{base}.manifest_hash", "manifest_hash drift from freeze manifest"))
    if payload.get("agent_config_hash") is not None and freeze_manifest.get("agents_config_hash") is not None:
        if payload.get("agent_config_hash") != freeze_manifest.get("agents_config_hash"):
            issues.append(_issue(f"{base}.agent_config_hash", "agent_config_hash drift from freeze manifest"))
    if payload.get("taxonomy_version") is not None and freeze_manifest.get("taxonomy_version") is not None:
        if payload.get("taxonomy_version") != freeze_manifest.get("taxonomy_version"):
            issues.append(_issue(f"{base}.taxonomy_version", "taxonomy_version drift from freeze manifest"))
    return issues


def _formal_context_hash_issues(
    manifest: Mapping[str, Any] | None,
    freeze_manifest: Mapping[str, Any] | None,
    paper_mappings: Sequence[Mapping[str, Any]],
    objects: Iterable[tuple[str, Mapping[str, Any]]],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    manifest_sha = manifest.get("__sha256") if manifest is not None else None
    if manifest is not None and freeze_manifest is not None:
        if manifest_sha is not None and freeze_manifest.get("manifest_hash") != manifest_sha:
            issues.append(_issue("$.freeze_manifest.manifest_hash", "freeze manifest manifest_hash must match loaded experiment_manifest sha256"))
        if manifest.get("contract_locks_hash") != freeze_manifest.get("locked_contracts_hash"):
            issues.append(_issue("$.freeze_manifest.locked_contracts_hash", "freeze locked_contracts_hash must match manifest contract_locks_hash"))
        if manifest.get("agents_config_hash") != freeze_manifest.get("agents_config_hash"):
            issues.append(_issue("$.freeze_manifest.agents_config_hash", "freeze agents_config_hash must match manifest agents_config_hash"))
        if manifest.get("infra_config_hash") != freeze_manifest.get("infra_config_hash"):
            issues.append(_issue("$.freeze_manifest.infra_config_hash", "freeze infra_config_hash must match manifest infra_config_hash"))
        if manifest.get("source_bundle_hash") != freeze_manifest.get("source_bundle_hash"):
            issues.append(_issue("$.freeze_manifest.source_bundle_hash", "freeze source_bundle_hash must match manifest source_bundle_hash"))
        deterministic = manifest.get("deterministic_selection")
        if isinstance(deterministic, Mapping):
            for field in (
                "hash_function",
                "hash_salt_hash",
                "eligible_case_unit_set_hash",
                "excluded_smoke_case_units",
                "smoke_exclusion_hash",
                "case_selection_order_hash",
                "bootstrap_seed",
                "bootstrap_resample_count",
                "audit_sample_seed",
                "rerun_subset_selection_rule",
            ):
                if deterministic.get(field) != freeze_manifest.get(field):
                    issues.append(_issue(f"$.freeze_manifest.{field}", f"freeze {field} must match manifest deterministic_selection"))
    for index, paper_mapping in enumerate(paper_mappings):
        paper_sha = paper_mapping.get("__sha256")
        if paper_sha is None:
            continue
        if manifest is not None and manifest.get("paper_mapping_sha256") != paper_sha:
            issues.append(_issue(f"$paper_mapping[{index}].__sha256", "loaded paper_mapping sha256 must match manifest paper_mapping_sha256"))
        if freeze_manifest is not None and freeze_manifest.get("paper_mapping_hash") != paper_sha:
            issues.append(_issue(f"$paper_mapping[{index}].__sha256", "loaded paper_mapping sha256 must match freeze paper_mapping_hash"))
    if manifest_sha is not None:
        for name, payload in objects:
            if payload.get("schema_version") == "evidence_contract/v1" and payload.get("manifest_hash") != manifest_sha:
                issues.append(_issue(f"${name}.manifest_hash", "evidence_contract manifest_hash must match loaded experiment_manifest sha256"))
    return issues


def _evidence_contract_manifest_lock_issues(
    contract: Mapping[str, Any],
    manifest_locks: Mapping[str, Mapping[str, Any]],
    manifest: Mapping[str, Any] | None,
    base: str,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    key = _contract_key(contract)
    lock = manifest_locks.get(key or "")
    if key is None or lock is None:
        return [_issue(f"{base}.contract_id", "evidence_contract must match a loaded manifest contract_locks entry")]
    if lock.get("contract_hash") != contract.get("contract_hash"):
        issues.append(_issue(f"{base}.contract_hash", "evidence_contract hash must match loaded manifest contract_locks entry"))
    expected_ref = None
    if manifest is not None:
        expected_ref = f"{manifest.get('manifest_id')}:{contract.get('contract_id')}:{contract.get('contract_version')}"
    if expected_ref is not None and contract.get("manifest_contract_lock_ref") != expected_ref:
        issues.append(_issue(f"{base}.manifest_contract_lock_ref", "manifest_contract_lock_ref must point to loaded manifest contract lock"))
    return issues


def _denominator_manifest_slot_issues(
    audit: Mapping[str, Any],
    manifest: Mapping[str, Any],
    base: str,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    domain = audit.get("domain")
    experiment_type = audit.get("experiment_type")
    priority = audit.get("priority")
    matching_domains = [
        item
        for item in manifest.get("domains", [])
        if isinstance(item, Mapping)
        and item.get("domain") == domain
        and item.get("experiment_type") == experiment_type
        and item.get("priority") == priority
    ]
    if not matching_domains:
        issues.append(_issue(f"{base}.domain", "denominator audit has no matching manifest planned domain"))
        return issues
    expected_exception_ids = {
        item.get("official_split_exception_id")
        for item in matching_domains
        if item.get("official_split_exception_id") is not None
    }
    audit_exception_id = audit.get("official_split_exception_id")
    audit_exception_case_units = _int(audit.get("official_split_exception_case_units"))
    if expected_exception_ids:
        if audit_exception_id not in expected_exception_ids:
            issues.append(
                _issue(
                    f"{base}.official_split_exception_id",
                    "denominator audit must report manifest official split exception",
                )
            )
        expected_case_units = {
            _int(item.get("case_unit_count"))
            for item in matching_domains
            if item.get("official_split_exception_id") == audit_exception_id
        }
        if audit_exception_case_units not in expected_case_units:
            issues.append(
                _issue(
                    f"{base}.official_split_exception_case_units",
                    "denominator audit official split exception case units must match manifest",
                )
            )
    elif audit_exception_id is not None or audit.get("official_split_exception_case_units") is not None:
        issues.append(
            _issue(
                f"{base}.official_split_exception_id",
                "denominator audit reports unmanifested official split exception",
            )
        )
    expected = sum((_int(item.get("record_slot_count")) or 0) for item in matching_domains)
    attempted = _int(audit.get("attempted_record_slots"))
    if attempted is not None and expected != attempted:
        issues.append(
            _issue(
                f"{base}.attempted_record_slots",
                "denominator audit attempted_record_slots must equal manifest planned record_slot_count",
            )
        )
    attempted_ids = audit.get("attempted_record_slot_ids")
    if isinstance(attempted_ids, list) and len(attempted_ids) != expected:
        issues.append(
            _issue(
                f"{base}.attempted_record_slot_ids",
                "denominator audit attempted_record_slot_ids must cover manifest planned slots",
            )
        )
    expected_hashes = {
        item.get("planned_record_slot_ids_hash")
        for item in matching_domains
        if item.get("planned_record_slot_ids_hash") is not None
    }
    attempted_hash = audit.get("attempted_record_slot_ids_hash")
    if expected_hashes and attempted_hash not in expected_hashes:
        issues.append(
            _issue(
                f"{base}.attempted_record_slot_ids_hash",
                "denominator audit attempted_record_slot_ids_hash must match manifest planned_record_slot_ids_hash",
            )
        )
    return issues


def _p0_denominator_audit_global_issues(
    manifest: Mapping[str, Any],
    objects: Iterable[tuple[str, Mapping[str, Any]]],
) -> list[ValidationIssue]:
    audits = [
        payload
        for _, payload in objects
        if payload.get("schema_version") == "denominator_audit/v1"
        and payload.get("experiment_type") == "main"
        and payload.get("priority") == "P0"
    ]
    if not audits:
        return []
    issues: list[ValidationIssue] = []
    p0_domains = [
        domain
        for domain in manifest.get("domains", [])
        if isinstance(domain, Mapping)
        and domain.get("experiment_type") == "main"
        and domain.get("priority") == "P0"
        and domain.get("domain") in P0_MAIN_DOMAIN_IDS
    ]
    expected_by_domain = {
        str(domain.get("domain")): _int(domain.get("record_slot_count")) or 0
        for domain in p0_domains
    }
    audit_by_domain = {str(audit.get("domain")): audit for audit in audits}
    for domain_id in sorted(P0_MAIN_DOMAIN_IDS):
        if domain_id not in audit_by_domain:
            issues.append(_issue("$denominator_audit", f"missing P0 denominator audit for {domain_id}"))
    unexpected = set(audit_by_domain) - P0_MAIN_DOMAIN_IDS
    for domain_id in sorted(unexpected):
        issues.append(_issue("$denominator_audit", f"unexpected P0 denominator audit domain: {domain_id}"))
    total_attempted = sum((_int(audit.get("attempted_record_slots")) or 0) for audit in audits)
    expected_total = sum(expected_by_domain.values())
    if expected_total and total_attempted != expected_total:
        issues.append(_issue("$denominator_audit.attempted_record_slots", "P0 denominator audits must cover complete manifest planned slot universe"))
    return issues


def _formal_result_denominator_audit_issues(
    manifest: Mapping[str, Any],
    objects: Iterable[tuple[str, Mapping[str, Any]]],
) -> list[ValidationIssue]:
    items = list(objects)
    result_artifacts = [
        (name, payload)
        for name, payload in items
        if _requires_formal_denominator_audit(payload)
    ]
    if not result_artifacts:
        return []
    issues: list[ValidationIssue] = []
    audits = [
        payload
        for _, payload in items
        if payload.get("schema_version") == "denominator_audit/v1"
        and payload.get("experiment_type") == "main"
        and payload.get("priority") == "P0"
    ]
    if not audits:
        return [_issue("$denominator_audit", "formal P0 result validation requires loaded denominator_audit artifacts")]
    issues.extend(_p0_denominator_audit_global_issues(manifest, items))
    for name, payload in result_artifacts:
        if payload.get("schema_version") == "aggregate_metrics/v1":
            if _resolve_aggregate_denominator_audit(payload, items) is None:
                issues.append(
                    _issue(
                        f"${name}.denominator_audit_ref",
                        "aggregate_metrics.denominator_audit_ref and denominator_audit_sha256 must resolve to a loaded denominator_audit/v1 artifact",
                    )
                )
        if payload.get("schema_version") == "paper_output/v1":
            for index, source in enumerate(payload.get("source_mapping", [])):
                if not isinstance(source, Mapping) or source.get("source_type") != "denominator_audit":
                    continue
                source_path = source.get("source_path")
                source_sha = source.get("source_sha256")
                if not _paper_output_denominator_source_matches(source_path, source_sha, audits):
                    issues.append(
                        _issue(
                            f"${name}.source_mapping[{index}]",
                            "paper_output denominator_audit source must resolve to a loaded denominator_audit/v1 artifact",
                        )
                    )
    return issues


def _paper_output_denominator_source_matches(
    source_path: Any,
    source_sha: Any,
    audits: Sequence[Mapping[str, Any]],
) -> bool:
    for audit in audits:
        actual_paths = {audit.get("__path"), audit.get("__abs_path")}
        path_candidates = {str(path) for path in actual_paths if path}
        sha_matches = source_sha is None or audit.get("__sha256") == source_sha
        path_matches = source_path is None or str(source_path) in path_candidates
        if sha_matches and path_matches:
            return True
    return False


def _requires_formal_denominator_audit(payload: Mapping[str, Any]) -> bool:
    schema_version = payload.get("schema_version")
    if schema_version == "aggregate_metrics/v1":
        return payload.get("experiment_type") == "main" and payload.get("priority") == "P0"
    if schema_version == "paper_output/v1":
        return True
    return False


def _paper_output_source_mapping_issues(
    payload: Mapping[str, Any],
    objects: Iterable[tuple[str, Mapping[str, Any]]],
    paper_mappings: Sequence[Mapping[str, Any]],
    base: str,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    paper_hashes = {
        mapping.get("__sha256")
        for mapping in paper_mappings
        if mapping.get("__sha256") is not None
    }
    if paper_hashes and payload.get("paper_mapping_hash") not in paper_hashes:
        issues.append(_issue(f"{base}.paper_mapping_hash", "paper_output.paper_mapping_hash must match a loaded paper_mapping sha256"))
    label = payload.get("label")
    mapping_label = payload.get("paper_mapping_label")
    if label != mapping_label:
        issues.append(_issue(f"{base}.paper_mapping_label", "paper_output.label must exactly equal paper_mapping_label"))
    mapping_entries = _paper_mapping_entries_for_label(label, paper_mappings)
    mapping_entry: Mapping[str, Any] | None = None
    if paper_mappings:
        if len(mapping_entries) != 1:
            issues.append(
                _issue(
                    f"{base}.paper_mapping_label",
                    "paper_output label must resolve to exactly one loaded paper_mapping entry",
                )
            )
        else:
            mapping_entry = mapping_entries[0]
    for index, source in enumerate(payload.get("source_mapping", [])):
        if not isinstance(source, Mapping):
            continue
        source_type = source.get("source_type")
        if source_type == "static_text":
            if not _static_text_source_allowed(source, mapping_entry):
                issues.append(
                    _issue(
                        f"{base}.source_mapping[{index}]",
                        "static_text paper_output sources must match the loaded paper_mapping static source declaration",
                    )
                )
            continue
        if not _paper_mapping_allows_source_type(mapping_entry, source_type):
            issues.append(
                _issue(
                    f"{base}.source_mapping[{index}].source_type",
                    "paper_output source_type must be declared in the loaded paper_mapping provenance sources",
                )
            )
        matches = _resolve_loaded_source_objects(source_type, source.get("source_path"), source.get("source_sha256"), objects)
        if not matches:
            issues.append(
                _issue(
                    f"{base}.source_mapping[{index}]",
                    f"paper_output {source_type} source must resolve to a loaded artifact by source_path and source_sha256",
                )
            )
            continue
        if source_type == "human_time":
            for matched in matches:
                if matched.get("counts_for_cost_table") is not True:
                    issues.append(
                        _issue(
                            f"{base}.source_mapping[{index}]",
                            "paper_output human_time sources must have counts_for_cost_table=true",
                        )
                    )
                for flag in (
                    "no_llm_cost_included",
                    "no_vps_cost_included",
                    "no_cloud_bill_included",
                    "no_benchmark_execution_compute_included",
                    "no_local_machine_runtime_included",
                ):
                    if matched.get(flag) is not True:
                        issues.append(
                            _issue(
                                f"{base}.source_mapping[{index}]",
                                "paper_output human_time sources must exclude all non-human costs",
                            )
                        )
                        break
    return issues


def _paper_mapping_entries_for_label(
    label: Any,
    paper_mappings: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    entries: list[Mapping[str, Any]] = []
    for mapping in paper_mappings:
        for entry in mapping.get("mappings", []):
            if isinstance(entry, Mapping) and entry.get("label") == label:
                entries.append(entry)
    return entries


def _paper_mapping_allows_source_type(mapping_entry: Mapping[str, Any] | None, source_type: Any) -> bool:
    if mapping_entry is None:
        return False
    declared = {
        str(item)
        for item in mapping_entry.get("provenance_sources", [])
        if item is not None
    }
    expected = PAPER_MAPPING_PROVENANCE_ALIASES.get(str(source_type), str(source_type))
    return expected in declared


def _static_text_source_allowed(source: Mapping[str, Any], mapping_entry: Mapping[str, Any] | None) -> bool:
    if mapping_entry is None:
        return False
    if not _paper_mapping_allows_source_type(mapping_entry, "static_text"):
        return False
    return (
        source.get("source_path") == mapping_entry.get("source_path")
        and source.get("source_sha256") == mapping_entry.get("source_sha256")
    )


def _resolve_loaded_source_objects(
    source_type: Any,
    source_path: Any,
    source_sha: Any,
    objects: Iterable[tuple[str, Mapping[str, Any]]],
) -> list[Mapping[str, Any]]:
    schema_versions = PAPER_OUTPUT_SOURCE_SCHEMA_VERSIONS.get(str(source_type))
    if schema_versions is None:
        return []
    matches: list[Mapping[str, Any]] = []
    for _, candidate in objects:
        if candidate.get("schema_version") not in schema_versions:
            continue
        if _matches_loaded_source(candidate, source_path, source_sha):
            matches.append(candidate)
    return matches


def _matches_loaded_source(candidate: Mapping[str, Any], source_path: Any, source_sha: Any) -> bool:
    paths = {candidate.get("__path"), candidate.get("__abs_path")}
    return source_path in paths and source_sha is not None and candidate.get("__sha256") == source_sha


def _resolve_aggregate_denominator_audit(
    payload: Mapping[str, Any],
    objects: Iterable[tuple[str, Mapping[str, Any]]],
) -> Mapping[str, Any] | None:
    ref = payload.get("denominator_audit_ref")
    expected_sha = payload.get("denominator_audit_sha256")
    domain = payload.get("domain")
    experiment_type = payload.get("experiment_type")
    priority = payload.get("priority")
    for _, candidate in objects:
        if candidate.get("schema_version") != "denominator_audit/v1":
            continue
        if candidate.get("domain") != domain or candidate.get("experiment_type") != experiment_type or candidate.get("priority") != priority:
            continue
        if ref in {candidate.get("__path"), candidate.get("__abs_path")} and expected_sha == candidate.get("__sha256"):
            return candidate
    return None


def _native_decisive_artifact_manifest_issues(
    payload: Mapping[str, Any],
    objects: Iterable[tuple[str, Mapping[str, Any]]],
    base: str,
) -> list[ValidationIssue]:
    schema_version = payload.get("schema_version")
    if schema_version not in {"raw_run/v1", "scored_record/v1"}:
        return []
    support = payload.get("native_decisive_support")
    decisive = payload.get("native_label_used_as_decisive_evidence") is True
    formal_artifact_reference = payload.get("__sha256") is not None and (
        payload.get("artifact_manifest_path") is not None or payload.get("artifact_manifest_sha256") is not None
    )
    if not decisive and not formal_artifact_reference:
        return []
    expected_sha = payload.get("artifact_manifest_sha256")
    expected_path = payload.get("artifact_manifest_path")
    if decisive and isinstance(support, Mapping):
        expected_sha = support.get("artifact_manifest_sha256") or expected_sha
        expected_path = support.get("artifact_manifest_path") or expected_path
    artifact_manifests = [
        candidate
        for _, candidate in objects
        if candidate.get("schema_version") == "artifact_manifest/v1"
    ]
    if not artifact_manifests:
        return [_issue(f"{base}.artifact_manifest_path", "formal raw/scored evidence requires matching artifact_manifest input")]
    for manifest in artifact_manifests:
        actual_sha = manifest.get("__sha256")
        actual_paths = {manifest.get("__path"), manifest.get("__abs_path")}
        path_candidates = {str(path) for path in actual_paths if path}
        sha_matches = expected_sha is None or actual_sha == expected_sha
        path_matches = expected_path is None or str(expected_path) in path_candidates
        if sha_matches and path_matches:
            return []
    return [_issue(f"{base}.artifact_manifest_sha256", "artifact_manifest path and sha256 must match loaded artifact_manifest")]


def _native_decisive_locked_artifact_mapping_issues(
    payload: Mapping[str, Any],
    objects: Iterable[tuple[str, Mapping[str, Any]]],
    base: str,
) -> list[ValidationIssue]:
    schema_version = payload.get("schema_version")
    if schema_version not in {"raw_run/v1", "scored_record/v1"}:
        return []
    if payload.get("native_label_used_as_decisive_evidence") is not True:
        return []
    matching_artifact_manifests = _matching_artifact_manifests_for_payload(payload, objects)
    if not matching_artifact_manifests:
        return []
    contract = _matching_evidence_contract_for_payload(payload, objects)
    if contract is None:
        return [_issue(f"{base}.native_decisive_support.locked_artifact_mapping", "native decisive evidence requires loaded locked evidence_contract required_artifacts")]
    issues: list[ValidationIssue] = []
    issues.extend(_native_decisive_required_artifact_issues(contract, f"{base}.native_decisive_support"))
    if issues:
        return issues
    support = payload.get("native_decisive_support")
    if not isinstance(support, Mapping):
        return [_issue(f"{base}.native_decisive_support", "decisive native evidence requires locked artifact support")]
    required_artifact = _matching_contract_required_artifact(contract, support)
    if required_artifact is None:
        return [
            _issue(
                f"{base}.native_decisive_support.contract_requirement_id",
                "native decisive support must match a loaded evidence_contract required_artifact binding",
            )
        ]
    for manifest in matching_artifact_manifests:
        for field in ("evidence_contract_id", "evidence_contract_version", "evidence_contract_hash"):
            expected = payload.get(field) or payload.get(field.removeprefix("evidence_"))
            observed = manifest.get(field)
            if expected is not None and observed is not None and observed != expected:
                issues.append(_issue(f"{base}.{field}", "native decisive artifact manifest contract linkage must match record contract"))
        if manifest.get("evidence_contract_id") != contract.get("contract_id"):
                issues.append(_issue(f"{base}.artifact_manifest_path", "artifact_manifest evidence_contract_id must match loaded evidence_contract"))
        if manifest.get("evidence_contract_version") != contract.get("contract_version"):
            issues.append(_issue(f"{base}.artifact_manifest_path", "artifact_manifest evidence_contract_version must match loaded evidence_contract"))
        if manifest.get("evidence_contract_hash") != contract.get("contract_hash"):
            issues.append(_issue(f"{base}.artifact_manifest_path", "artifact_manifest evidence_contract_hash must match loaded evidence_contract"))
        if _artifact_manifest_satisfies_contract_required_artifact(manifest, required_artifact, support):
            return issues
    issues.append(
        _issue(
            f"{base}.native_decisive_support.artifact_id",
            "native decisive support must match the loaded artifact_manifest artifact binding for the locked evidence_contract requirement",
        )
    )
    return issues


def _matching_artifact_manifests_for_payload(
    payload: Mapping[str, Any],
    objects: Iterable[tuple[str, Mapping[str, Any]]],
) -> list[Mapping[str, Any]]:
    support = payload.get("native_decisive_support")
    expected_sha = payload.get("artifact_manifest_sha256")
    expected_path = payload.get("artifact_manifest_path")
    if isinstance(support, Mapping):
        expected_sha = support.get("artifact_manifest_sha256") or expected_sha
        expected_path = support.get("artifact_manifest_path") or expected_path
    matches: list[Mapping[str, Any]] = []
    for _, candidate in objects:
        if candidate.get("schema_version") != "artifact_manifest/v1":
            continue
        actual_paths = {candidate.get("__path"), candidate.get("__abs_path")}
        path_candidates = {str(path) for path in actual_paths if path}
        sha_matches = expected_sha is None or candidate.get("__sha256") == expected_sha
        path_matches = expected_path is None or str(expected_path) in path_candidates
        if sha_matches and path_matches:
            matches.append(candidate)
    return matches


def _matching_evidence_contract_for_payload(
    payload: Mapping[str, Any],
    objects: Iterable[tuple[str, Mapping[str, Any]]],
) -> Mapping[str, Any] | None:
    key = _contract_key(payload)
    expected_hash = payload.get("contract_hash") or payload.get("evidence_contract_hash")
    for _, candidate in objects:
        if candidate.get("schema_version") != "evidence_contract/v1":
            continue
        if _contract_key(candidate) != key:
            continue
        if expected_hash is not None and candidate.get("contract_hash") != expected_hash:
            continue
        if candidate.get("contract_status") != "locked" or candidate.get("main_result_eligible") is not True:
            continue
        return candidate
    return None


def _matching_contract_required_artifact(
    contract: Mapping[str, Any],
    support: Mapping[str, Any],
) -> Mapping[str, Any] | None:
    support_artifact_id = support.get("artifact_id")
    support_requirement_id = support.get("contract_requirement_id")
    for required in contract.get("required_artifacts", []):
        if not isinstance(required, Mapping):
            continue
        if required.get("native_aligned_source_support") is not True:
            continue
        if required.get("artifact_id") != support_artifact_id:
            continue
        if required.get("contract_requirement_id") != support_requirement_id:
            continue
        return required
    return None


def _artifact_manifest_satisfies_contract_required_artifact(
    manifest: Mapping[str, Any],
    required_artifact: Mapping[str, Any],
    support: Mapping[str, Any],
) -> bool:
    artifacts = [item for item in manifest.get("artifacts", []) if isinstance(item, Mapping)]
    requirement_id = required_artifact.get("contract_requirement_id")
    artifact_id = support.get("artifact_id")
    artifact_sha256 = support.get("artifact_sha256")
    verified_output_hash = support.get("verified_evaluator_output_object_hash")
    if not isinstance(requirement_id, str) or not requirement_id:
        return False
    for artifact in artifacts:
        if artifact.get("artifact_id") != artifact_id:
            continue
        if requirement_id not in artifact.get("artifact_contract_requirement_ids", []):
            continue
        if artifact_sha256 is not None and artifact.get("sha256") != artifact_sha256:
            continue
        if verified_output_hash is not None and artifact.get("verified_evaluator_output_object_hash") != verified_output_hash:
            continue
        if required_artifact.get("artifact_type") and artifact.get("artifact_type") != required_artifact.get("artifact_type"):
            continue
        if not _artifact_source_matches_producer(required_artifact.get("artifact_source"), artifact.get("producer_role")):
            continue
        return True
    return False


def _native_decisive_required_artifact_issues(
    contract: Mapping[str, Any],
    base: str,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    required_artifacts = [item for item in contract.get("required_artifacts", []) if isinstance(item, Mapping)]
    for index, required in enumerate(required_artifacts):
        if required.get("native_aligned_source_support") is not True:
            continue
        requirement_id = required.get("contract_requirement_id")
        if not isinstance(requirement_id, str) or not requirement_id:
            issues.append(
                _issue(
                    f"{base}.required_artifacts[{index}].contract_requirement_id",
                    "native decisive required artifacts must declare contract_requirement_id",
                )
            )
    return issues


def _artifact_source_matches_producer(required_source: Any, producer_role: Any) -> bool:
    if required_source is None:
        return True
    if required_source == producer_role:
        return True
    aliases = {
        "official_evaluator": {"official_evaluator"},
        "official_runner": {"official_runner", "benchmark"},
    }
    return producer_role in aliases.get(str(required_source), set())


def _unsupported_schema_keyword_issues(schema: Any, path: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if isinstance(schema, Mapping):
        for key, value in schema.items():
            if key in UNSUPPORTED_JSON_SCHEMA_KEYWORDS:
                issues.append(_issue(f"{path}.{key}", f"unsupported JSON Schema keyword: {key}"))
            issues.extend(_unsupported_schema_keyword_issues(value, _join_path(path, str(key))))
    elif isinstance(schema, list):
        for index, item in enumerate(schema):
            issues.extend(_unsupported_schema_keyword_issues(item, f"{path}[{index}]"))
    return issues


def _domain_keys_from_config(payload: Mapping[str, Any]) -> set[str]:
    keys: set[str] = set()
    domain_map = payload.get("main_domain_agent_map")
    if isinstance(domain_map, Mapping):
        keys.update(str(key) for key in domain_map)
    return keys


def _resolve_ref(ref: str, root: Mapping[str, Any]) -> Mapping[str, Any]:
    if not ref.startswith("#/$defs/"):
        raise SchemaValidationError(
            ValidationReport(
                schema_name="schema",
                status="invalid",
                issues=(ValidationIssue("$ref", f"unsupported ref: {ref}"),),
            )
        )
    key = ref.removeprefix("#/$defs/")
    defs = root.get("$defs", {})
    if not isinstance(defs, Mapping) or key not in defs:
        raise SchemaValidationError(
            ValidationReport(
                schema_name="schema",
                status="invalid",
                issues=(ValidationIssue("$ref", f"missing ref target: {ref}"),),
            )
        )
    target = defs[key]
    if not isinstance(target, Mapping):
        raise SchemaValidationError(
            ValidationReport(
                schema_name="schema",
                status="invalid",
                issues=(ValidationIssue("$ref", f"ref target is not a schema object: {ref}"),),
            )
        )
    return target


def _matches_type(value: Any, expected: Any) -> bool:
    if isinstance(expected, list):
        return any(_matches_type(value, item) for item in expected)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _as_sequence(value: Any) -> Sequence[Any]:
    return value if isinstance(value, list) else []


def _join_path(path: str, key: str) -> str:
    return f"{path}.{key}" if path != "$" else f"$.{key}"


def _issue(path: str, message: str) -> ValidationIssue:
    return ValidationIssue(path=path, message=message)


def _int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _is_hash(value: Any) -> bool:
    return isinstance(value, str) and bool(HASH_RE.match(value))


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
