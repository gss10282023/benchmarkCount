"""Step 5 pre-scoring freeze check-only gates."""

from __future__ import annotations

import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evidence_system.contracts.validate import validate_contracts
from evidence_system.core.hashing import sha256_object, sha256_path
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml, validate_object


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
)

REQUIRED_DETERMINISTIC_FIELDS = (
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
)

PREDICTION_IDS = ("P1", "P2", "P3", "P4")


@dataclass(frozen=True)
class FreezeIssue:
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "message": self.message}


@dataclass(frozen=True)
class FreezeCheckReport:
    status: str
    issues: tuple[FreezeIssue, ...]
    freeze_manifest: Mapping[str, Any]
    files: Mapping[str, str | None]
    formal: bool
    check_only: bool

    @property
    def ok(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "formal": self.formal,
            "check_only": self.check_only,
            "issues": [issue.to_dict() for issue in self.issues],
            "files": dict(self.files),
            "freeze_manifest": dict(self.freeze_manifest),
        }


def check_freeze_predictions(
    *,
    manifest_path: str | Path,
    contracts: Iterable[str | Path],
    source_bundle_path: str | Path,
    review_records: Iterable[str | Path] = (),
    llm_calls: Iterable[str | Path] = (),
    paper_mapping_path: str | Path | None = None,
    agents_config_path: str | Path = "configs/agents.yaml",
    infra_config_path: str | Path = "configs/infra.yaml",
    prediction_registry_path: str | Path = "experiments/prediction_registry/registry.yaml",
    official_splits_path: str | Path = "experiments/official_splits",
    contract_template_path: str | Path = "experiments/evidence_contracts/contract_template.yaml",
    bootstrap_plan_path: str | Path | None = None,
    audit_sampling_plan_path: str | Path = "experiments/audit_sampling_plan/plan.yaml",
    rerun_subset_path: str | Path | None = None,
    result_schema_path: str | Path = "schemas/scored_record.schema.json",
    artifact_schema_path: str | Path = "schemas/artifact_manifest.schema.json",
    scorer_code_paths: Sequence[str | Path] = ("src/evidence_system/scorer",),
    scorer_version: str | None = None,
    code_git_commit: str | None = None,
    frozen_at: str | None = None,
    evidence_contract_template_version: str = "contract_template/v1",
    contract_drafting_prompt_version: str = "contract_draft_prompt/v1",
    contract_drafting_prompt_hash: str | None = None,
    proposed_freeze_manifest_path: str | Path | None = None,
    formal: bool = False,
) -> FreezeCheckReport:
    issues: list[FreezeIssue] = []
    files: dict[str, str | None] = {}

    manifest = _load_mapping(manifest_path, "$.manifest", issues)
    if manifest is None:
        manifest = {}
    else:
        _extend_schema_issues(issues, "experiment_manifest", manifest, "$.manifest", formal=formal)

    contract_report = validate_contracts(
        contracts=contracts,
        manifest_path=manifest_path,
        review_records=review_records,
        llm_calls=llm_calls,
        source_bundle_path=source_bundle_path,
        formal=formal,
        require_p0_complete=True,
        require_declared_appendix=True,
    )
    issues.extend(FreezeIssue(f"$.contracts{issue.path}", issue.message) for issue in contract_report.issues)

    deterministic = manifest.get("deterministic_selection")
    if not isinstance(deterministic, Mapping):
        issues.append(FreezeIssue("$.manifest.deterministic_selection", "freeze requires deterministic_selection"))
        deterministic = {}
    for field in REQUIRED_DETERMINISTIC_FIELDS:
        if field not in deterministic or deterministic.get(field) in (None, ""):
            issues.append(FreezeIssue(f"$.manifest.deterministic_selection.{field}", "freeze deterministic selection field is required"))

    _check_hash_input(
        issues,
        files,
        path=source_bundle_path,
        expected=manifest.get("source_bundle_hash"),
        path_label="$.source_bundle",
        expected_label="$.manifest.source_bundle_hash",
    )
    if paper_mapping_path is None:
        paper_mapping_path = manifest.get("paper_mapping_path")
    paper_mapping_hash = _check_hash_input(
        issues,
        files,
        path=paper_mapping_path,
        expected=manifest.get("paper_mapping_sha256"),
        path_label="$.paper_mapping",
        expected_label="$.manifest.paper_mapping_sha256",
    )
    agents_config_hash = _check_hash_input(
        issues,
        files,
        path=agents_config_path,
        expected=manifest.get("agents_config_hash"),
        path_label="$.agents_config",
        expected_label="$.manifest.agents_config_hash",
    )
    infra_config_hash = _check_hash_input(
        issues,
        files,
        path=infra_config_path,
        expected=manifest.get("infra_config_hash"),
        path_label="$.infra_config",
        expected_label="$.manifest.infra_config_hash",
    )

    contract_locks = manifest.get("contract_locks")
    if not isinstance(contract_locks, list):
        issues.append(FreezeIssue("$.manifest.contract_locks", "freeze requires manifest contract_locks list"))
        contract_locks = []
    locked_contracts_hash = sha256_object(contract_locks)
    if manifest.get("contract_locks_hash") != locked_contracts_hash:
        issues.append(FreezeIssue("$.manifest.contract_locks_hash", "manifest contract_locks_hash must equal canonical contract_locks hash"))

    prediction_registry = _load_mapping(prediction_registry_path, "$.prediction_registry", issues)
    if prediction_registry is None:
        prediction_registry = {}
    _placeholder_issues(prediction_registry, "$.prediction_registry", issues)
    predictions = _freeze_predictions_payload(prediction_registry, issues)

    official_splits_hash = _hash_path_or_issue(official_splits_path, "$.official_splits", issues, files)
    prediction_registry_hash = _hash_path_or_issue(prediction_registry_path, "$.prediction_registry", issues, files)
    contract_template_hash = _hash_path_or_issue(contract_template_path, "$.contract_template", issues, files)
    result_schema_hash = _hash_path_or_issue(result_schema_path, "$.result_schema", issues, files)
    artifact_schema_hash = _hash_path_or_issue(artifact_schema_path, "$.artifact_schema", issues, files)
    audit_sampling_plan_hash = _hash_path_or_issue(audit_sampling_plan_path, "$.audit_sampling_plan", issues, files)
    bootstrap_plan_hash = _hash_path_or_issue(bootstrap_plan_path, "$.bootstrap_plan", issues, files)
    rerun_subset_hash = _hash_path_or_issue(rerun_subset_path, "$.rerun_subset", issues, files)
    scorer_code_hash = _hash_many_paths(scorer_code_paths, "$.scorer_code", issues, files)

    if scorer_version is None or _is_placeholder_string(scorer_version):
        issues.append(FreezeIssue("$.scorer_version", "freeze requires non-placeholder scorer_version"))
        scorer_version = ""
    if code_git_commit is None:
        code_git_commit = _current_git_commit_hash()
    if code_git_commit is None or _is_placeholder_string(code_git_commit):
        issues.append(FreezeIssue("$.code_git_commit", "freeze requires code_git_commit hash"))
        code_git_commit = ""
    if contract_drafting_prompt_hash is None:
        contract_drafting_prompt_hash = sha256_object(
            {
                "prompt_version": contract_drafting_prompt_version,
                "prompt_policy": "contract_drafter_allowed_inputs_v1",
            }
        )

    freeze_manifest = {
        "schema_version": "freeze_manifest/v1",
        "frozen_at": frozen_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "manifest_hash": _hash_path_or_issue(manifest_path, "$.manifest", issues, files),
        "paper_mapping_hash": paper_mapping_hash or "0" * 64,
        "official_splits_hash": official_splits_hash or "0" * 64,
        "eligible_case_unit_set_hash": deterministic.get("eligible_case_unit_set_hash"),
        "excluded_smoke_case_units": deterministic.get("excluded_smoke_case_units"),
        "smoke_exclusion_hash": deterministic.get("smoke_exclusion_hash"),
        "case_selection_order_hash": deterministic.get("case_selection_order_hash"),
        "hash_function": deterministic.get("hash_function"),
        "hash_salt_hash": deterministic.get("hash_salt_hash"),
        "source_bundle_hash": _hash_path_or_issue(source_bundle_path, "$.source_bundle", issues, files) or "0" * 64,
        "agents_config_hash": agents_config_hash or "0" * 64,
        "infra_config_hash": infra_config_hash or "0" * 64,
        "locked_contracts_hash": locked_contracts_hash,
        "evidence_contract_template_version": evidence_contract_template_version,
        "evidence_contract_template_hash": contract_template_hash or "0" * 64,
        "contract_drafting_prompt_version": contract_drafting_prompt_version,
        "contract_drafting_prompt_hash": contract_drafting_prompt_hash,
        "prediction_registry_hash": prediction_registry_hash or "0" * 64,
        "taxonomy_version": _taxonomy_version(manifest, contract_locks),
        "result_schema_hash": result_schema_hash or "0" * 64,
        "artifact_schema_hash": artifact_schema_hash or "0" * 64,
        "scorer_version": scorer_version,
        "scorer_code_hash": scorer_code_hash or "0" * 64,
        "code_git_commit": code_git_commit,
        "bootstrap_plan_hash": bootstrap_plan_hash or "0" * 64,
        "bootstrap_seed": deterministic.get("bootstrap_seed"),
        "bootstrap_resample_count": deterministic.get("bootstrap_resample_count"),
        "audit_sampling_plan_hash": audit_sampling_plan_hash or "0" * 64,
        "audit_sample_seed": deterministic.get("audit_sample_seed"),
        "rerun_subset_hash": rerun_subset_hash or "0" * 64,
        "rerun_subset_selection_rule": deterministic.get("rerun_subset_selection_rule"),
        "predictions": predictions,
    }
    _extend_schema_issues(issues, "freeze_manifest", freeze_manifest, "$.freeze_manifest", formal=formal)

    if proposed_freeze_manifest_path is not None:
        proposed = _load_mapping(proposed_freeze_manifest_path, "$.proposed_freeze_manifest", issues)
        if proposed is not None:
            _extend_schema_issues(issues, "freeze_manifest", proposed, "$.proposed_freeze_manifest", formal=formal)
            for field, expected in freeze_manifest.items():
                if proposed.get(field) != expected:
                    issues.append(
                        FreezeIssue(
                            f"$.proposed_freeze_manifest.{field}",
                            "proposed freeze manifest field does not match current check-only inputs",
                        )
                    )

    return FreezeCheckReport(
        status="ok" if not issues else "invalid",
        issues=tuple(issues),
        freeze_manifest=freeze_manifest,
        files=files,
        formal=formal,
        check_only=True,
    )


def _load_mapping(path: str | Path | None, base: str, issues: list[FreezeIssue]) -> dict[str, Any] | None:
    if path is None:
        issues.append(FreezeIssue(base, "required freeze input path is missing"))
        return None
    resolved = resolve_repo_path(path)
    if not resolved.exists():
        issues.append(FreezeIssue(base, f"required freeze input path does not exist: {resolved}"))
        return None
    payload = load_json_or_yaml(resolved)
    if not isinstance(payload, dict):
        issues.append(FreezeIssue(base, "required freeze input must be a mapping"))
        return None
    return dict(payload)


def _extend_schema_issues(
    issues: list[FreezeIssue],
    schema_name: str,
    payload: Mapping[str, Any],
    base: str,
    *,
    formal: bool,
) -> None:
    report = validate_object(schema_name, dict(payload), formal=formal, raise_on_error=False)
    for issue in report.issues:
        issues.append(FreezeIssue(f"{base}{issue.path}", issue.message))


def _check_hash_input(
    issues: list[FreezeIssue],
    files: dict[str, str | None],
    *,
    path: str | Path | None,
    expected: Any,
    path_label: str,
    expected_label: str,
) -> str | None:
    observed = _hash_path_or_issue(path, path_label, issues, files)
    if observed is not None and expected is not None and observed != expected:
        issues.append(FreezeIssue(expected_label, "freeze input hash disagrees with manifest"))
    return observed


def _hash_path_or_issue(
    path: str | Path | None,
    base: str,
    issues: list[FreezeIssue],
    files: dict[str, str | None],
) -> str | None:
    if path is None:
        issues.append(FreezeIssue(base, "required freeze hash input path is missing"))
        return None
    resolved = resolve_repo_path(path)
    key = _display_path(resolved)
    if not resolved.exists():
        files[key] = None
        issues.append(FreezeIssue(base, f"required freeze hash input path does not exist: {resolved}"))
        return None
    digest = sha256_path(resolved)
    files[key] = digest
    return digest


def _hash_many_paths(
    paths: Sequence[str | Path],
    base: str,
    issues: list[FreezeIssue],
    files: dict[str, str | None],
) -> str | None:
    if not paths:
        issues.append(FreezeIssue(base, "at least one scorer code path is required"))
        return None
    entries = []
    for path in paths:
        digest = _hash_path_or_issue(path, base, issues, files)
        if digest is not None:
            entries.append({"path": str(path), "sha256": digest})
    if len(entries) != len(paths):
        return None
    return sha256_object(entries)


def _placeholder_issues(value: Any, path: str, issues: list[FreezeIssue]) -> None:
    if isinstance(value, str):
        if _is_placeholder_string(value):
            issues.append(FreezeIssue(path, "freeze input contains unresolved placeholder value"))
    elif isinstance(value, Mapping):
        for key, child in value.items():
            _placeholder_issues(child, f"{path}.{key}", issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _placeholder_issues(child, f"{path}[{index}]", issues)


def _is_placeholder_string(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return True
    lowered = value.lower()
    return any(marker.lower() in lowered for marker in PLACEHOLDER_MARKERS)


def _freeze_predictions_payload(registry: Mapping[str, Any], issues: list[FreezeIssue]) -> dict[str, Any]:
    raw = registry.get("predictions")
    predictions: dict[str, Any] = {}
    if isinstance(raw, Mapping):
        predictions = {str(key): value for key, value in raw.items()}
    elif isinstance(raw, list):
        for item in raw:
            if isinstance(item, Mapping) and item.get("prediction_id"):
                predictions[str(item["prediction_id"])] = dict(item)
    else:
        issues.append(FreezeIssue("$.prediction_registry.predictions", "prediction registry requires P1-P4 predictions"))
    for prediction_id in PREDICTION_IDS:
        if prediction_id not in predictions:
            issues.append(FreezeIssue(f"$.prediction_registry.predictions.{prediction_id}", "prediction registry missing required prediction"))
    return {prediction_id: predictions.get(prediction_id, {}) for prediction_id in PREDICTION_IDS}


def _taxonomy_version(manifest: Mapping[str, Any], contract_locks: Sequence[Any]) -> str:
    for domain in manifest.get("domains", []):
        if not isinstance(domain, Mapping):
            continue
        for case_unit in domain.get("case_units", []):
            if isinstance(case_unit, Mapping) and case_unit.get("taxonomy_version"):
                return str(case_unit["taxonomy_version"])
    for lock in contract_locks:
        if isinstance(lock, Mapping) and lock.get("taxonomy_version"):
            return str(lock["taxonomy_version"])
    return "R1-R7_paper_taxonomy_v0.1.0"


def _current_git_commit_hash() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=resolve_repo_path("."),
            check=True,
            text=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return sha256_object({"git_commit": result.stdout.strip()})


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(resolve_repo_path(".")))
    except ValueError:
        return str(path)
