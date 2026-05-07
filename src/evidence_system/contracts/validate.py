"""Fail-closed validation for contract lifecycle artifacts."""

from __future__ import annotations

import ast
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evidence_system.contracts.common import (
    ContractLifecycleError,
    LifecycleIssue,
    case_unit_lock_complete,
    contract_content_hash,
    display_path,
    find_forbidden_inputs,
    iter_json_files,
    iter_manifest_case_units,
    load_mapping,
    normalize_domain_or_none,
)
from evidence_system.contracts.case_packets import derive_source_context, validate_case_packet_source
from evidence_system.core.hashing import sha256_file
from evidence_system.core.paths import repo_root, resolve_repo_path
from evidence_system.core.schemas import (
    P0_MAIN_DOMAIN_IDS,
    SchemaValidationError,
    load_json_or_yaml,
    validate_cross_object_consistency,
    validate_object,
)


@dataclass(frozen=True)
class ContractValidationReport:
    status: str
    issues: tuple[LifecycleIssue, ...]
    contract_count: int
    locked_contract_count: int
    review_record_count: int
    llm_call_count: int

    @property
    def ok(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "contract_count": self.contract_count,
            "locked_contract_count": self.locked_contract_count,
            "review_record_count": self.review_record_count,
            "llm_call_count": self.llm_call_count,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def validate_contracts(
    *,
    contracts: Iterable[str | Path],
    manifest_path: str | Path | None = None,
    review_records: Iterable[str | Path] = (),
    llm_calls: Iterable[str | Path] = (),
    source_bundle_path: str | Path | None = None,
    formal: bool = False,
    require_p0_complete: bool = False,
    require_declared_appendix: bool = False,
    allow_empty_before_lock: bool = False,
    raise_on_error: bool = False,
) -> ContractValidationReport:
    issues: list[LifecycleIssue] = []
    contract_objects = _load_contracts(contracts, issues, formal=formal, allow_empty_before_lock=allow_empty_before_lock)
    review_objects = _load_schema_objects(review_records, "contract_review", issues, formal=formal)
    llm_objects = _load_schema_objects(llm_calls, "llm_call", issues, formal=formal)
    manifest: dict[str, Any] | None = None
    manifest_object: tuple[str, Mapping[str, Any]] | None = None
    source_bundle_sources: dict[str, Mapping[str, Any]] = {}
    if manifest_path is not None:
        manifest = _load_manifest(manifest_path, issues, formal=formal)
        if manifest is not None:
            manifest_object = ("manifest", manifest)
    if source_bundle_path is not None:
        issues.extend(_source_bundle_issues(source_bundle_path))
        source_bundle_sources = _source_bundle_sources_by_contract(source_bundle_path)

    for path, contract in contract_objects:
        source = source_bundle_sources.get(str(contract.get("contract_id"))) or source_bundle_sources.get(
            str(contract.get("case_unit_id"))
        )
        issues.extend(_contract_lifecycle_issues(path, contract, formal=formal, source=source))

    issues.extend(_review_linkage_issues(contract_objects, review_objects))
    issues.extend(_llm_call_linkage_issues(contract_objects, llm_objects, formal=formal))
    if manifest_object is not None:
        issues.extend(_manifest_contract_issues(manifest_object[1], contract_objects))
        context: list[tuple[str, Mapping[str, Any]]] = [manifest_object]
        context.extend(
            (f"contract:{path}", contract)
            for path, contract in contract_objects
            if contract.get("contract_status") == "locked" and contract.get("main_result_eligible") is True
        )
        cross_report = validate_cross_object_consistency(context, raise_on_error=False)
        issues.extend(LifecycleIssue(issue.path, issue.message) for issue in cross_report.issues)
    if require_p0_complete and manifest is not None:
        issues.extend(_p0_complete_issues(manifest, contract_objects))
    if require_declared_appendix and manifest is not None:
        issues.extend(_declared_appendix_issues(manifest, contract_objects))

    report = ContractValidationReport(
        status="ok" if not issues else "invalid",
        issues=tuple(issues),
        contract_count=len(contract_objects),
        locked_contract_count=sum(1 for _, c in contract_objects if c.get("contract_status") == "locked"),
        review_record_count=len(review_objects),
        llm_call_count=len(llm_objects),
    )
    if report.issues and raise_on_error:
        raise ContractLifecycleError("; ".join(f"{i.path}: {i.message}" for i in report.issues[:8]))
    return report


def _load_contracts(
    paths: Iterable[str | Path],
    issues: list[LifecycleIssue],
    *,
    formal: bool,
    allow_empty_before_lock: bool,
) -> list[tuple[Path, dict[str, Any]]]:
    contracts: list[tuple[Path, dict[str, Any]]] = []
    for path in iter_json_files(paths):
        payload = load_mapping(path)
        if payload.get("schema_version") != "evidence_contract/v1":
            continue
        report = validate_object("evidence_contract", payload, formal=formal, raise_on_error=False)
        issues.extend(LifecycleIssue(f"{path}:{issue.path}", issue.message) for issue in report.issues)
        contracts.append((path, payload))
    if not contracts and not allow_empty_before_lock:
        issues.append(LifecycleIssue("$.contracts", "at least one evidence_contract/v1 file is required"))
    return contracts


def _load_schema_objects(
    paths: Iterable[str | Path],
    schema_name: str,
    issues: list[LifecycleIssue],
    *,
    formal: bool,
) -> list[tuple[Path, dict[str, Any]]]:
    objects: list[tuple[Path, dict[str, Any]]] = []
    for path in iter_json_files(paths):
        payload = load_mapping(path)
        report = validate_object(schema_name, payload, formal=formal, raise_on_error=False)
        issues.extend(LifecycleIssue(f"{path}:{issue.path}", issue.message) for issue in report.issues)
        objects.append((path, payload))
    return objects


def _load_manifest(path: str | Path, issues: list[LifecycleIssue], *, formal: bool) -> dict[str, Any] | None:
    payload = load_json_or_yaml(path)
    if not isinstance(payload, dict):
        issues.append(LifecycleIssue("$.manifest", "manifest must be a mapping"))
        return None
    if payload.get("schema_version") == "experiment_manifest/v1":
        report = validate_object("experiment_manifest", payload, formal=formal, raise_on_error=False)
        issues.extend(LifecycleIssue(f"{path}:{issue.path}", issue.message) for issue in report.issues)
    resolved = resolve_repo_path(path)
    payload = dict(payload)
    if resolved.exists():
        payload["__path"] = display_path(resolved)
        payload["__abs_path"] = str(resolved)
        payload["__sha256"] = sha256_file(resolved)
    return payload


def _source_bundle_issues(path: str | Path) -> list[LifecycleIssue]:
    issues: list[LifecycleIssue] = []
    payload = load_json_or_yaml(path)
    if not isinstance(payload, Mapping):
        return [LifecycleIssue("$.source_bundle", "source bundle must be a mapping")]
    issues.extend(_repo_local_absolute_path_issues(payload, "$.source_bundle"))
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        return [LifecycleIssue("$.source_bundle.sources", "source bundle requires sources")]
    for index, source in enumerate(sources):
        if not isinstance(source, Mapping):
            issues.append(LifecycleIssue(f"$.source_bundle.sources[{index}]", "source must be a mapping"))
            continue
        issues.extend(validate_case_packet_source(source, f"$.source_bundle.sources[{index}]"))
    return issues


def _source_context(source: Mapping[str, Any]) -> Mapping[str, Any]:
    explicit = source.get("source_context")
    if isinstance(explicit, Mapping):
        return explicit
    if isinstance(source, dict):
        cached = source.get("__case_packet_context")
        if isinstance(cached, Mapping):
            return cached
        derived = derive_source_context(source)
        source["__case_packet_context"] = derived
        return derived
    return derive_source_context(source)


def _contract_lifecycle_issues(
    path: Path,
    contract: Mapping[str, Any],
    *,
    formal: bool,
    source: Mapping[str, Any] | None = None,
) -> list[LifecycleIssue]:
    issues: list[LifecycleIssue] = []
    issues.extend(_review_lint_issues(path, contract))
    if source is not None:
        issues.extend(_compare_args_native_rule_issues(path, contract, source))
        issues.extend(_source_semantic_alignment_issues(path, contract, source))
    observed = contract.get("contract_hash")
    expected = contract_content_hash(contract)
    if observed != expected:
        issues.append(LifecycleIssue(str(path), "contract_hash must equal canonical json_canonical_sha256 content hash"))
    if contract.get("canonical_hash") != observed:
        issues.append(LifecycleIssue(str(path), "canonical_hash must equal contract_hash"))
    if contract.get("contract_status") == "locked":
        issues.extend(find_forbidden_inputs(contract, str(path)))
        if formal and _contract_uses_test_mock_draft(contract):
            issues.append(LifecycleIssue(str(path), "test-only mock contract draft cannot be used in formal contract lifecycle"))
        if contract.get("main_result_eligible") is True and contract.get("claim_scope") != "native_aligned":
            issues.append(LifecycleIssue(str(path), "main-result eligible locked contracts must be native_aligned"))
        for index, artifact in enumerate(contract.get("required_artifacts", [])):
            if isinstance(artifact, Mapping) and contract.get("claim_scope") == "native_aligned":
                if artifact.get("native_aligned_source_support") is not True:
                    issues.append(
                        LifecycleIssue(
                            f"{path}:$.required_artifacts[{index}]",
                            "native-aligned unsupported requirement must be removed or marked stronger_measurement before lock",
                        )
                    )
    if contract.get("contract_status") in {"clarification", "superseded"} and contract.get("main_result_eligible") is not False:
        issues.append(LifecycleIssue(str(path), "post-lock clarification/superseded contracts must set main_result_eligible=false"))
    return issues


def _repo_local_absolute_path_issues(value: Any, base: str) -> list[LifecycleIssue]:
    issues: list[LifecycleIssue] = []
    if base == "$.source_bundle.manifest_path":
        return issues
    root = str(repo_root())
    if isinstance(value, Mapping):
        for key, child in value.items():
            issues.extend(_repo_local_absolute_path_issues(child, f"{base}.{key}"))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            issues.extend(_repo_local_absolute_path_issues(child, f"{base}[{index}]"))
    elif isinstance(value, str) and (
        root in value
        or ("/" + "root/benchmarks/") in value
        or (_looks_like_local_absolute_path(value) and _is_source_path_field(base))
    ):
        issues.append(LifecycleIssue(base, "source bundle must use repo-relative paths or benchmark URI refs, not local absolute paths"))
    return issues


def _looks_like_local_absolute_path(value: str) -> bool:
    text = value.strip()
    return text.startswith(("/Users/", "/root/", "/home/", "/tmp/", "/var/", "/opt/", "/mnt/", "/workspace/"))


def _is_source_path_field(base: str) -> bool:
    key = base.rsplit(".", 1)[-1].split("[", 1)[0]
    return key in {"source_ref", "task_dir", "task_directory", "manifest_path"}


def _source_bundle_sources_by_contract(path: str | Path) -> dict[str, Mapping[str, Any]]:
    payload = load_json_or_yaml(path)
    if not isinstance(payload, Mapping):
        return {}
    sources = payload.get("sources")
    if not isinstance(sources, Sequence) or isinstance(sources, (str, bytes, bytearray)):
        return {}
    indexed: dict[str, Mapping[str, Any]] = {}
    for source in sources:
        if not isinstance(source, Mapping):
            continue
        for key in ("contract_id", "case_unit_id"):
            value = source.get(key)
            if value is not None:
                indexed[str(value)] = source
    return indexed


def _review_lint_issues(path: Path, contract: Mapping[str, Any]) -> list[LifecycleIssue]:
    issues: list[LifecycleIssue] = []
    support = contract.get("source_support")
    support_mapping = support if isinstance(support, Mapping) else {}
    extra = support_mapping.get("drafter_extra_fields")
    extra_mapping = extra if isinstance(extra, Mapping) else {}
    mapping = contract.get("stronger_measurement_mapping")

    stronger_marked = _nonempty_review_items(extra_mapping.get("requirements_marked_stronger_measurement"))
    if stronger_marked and not isinstance(mapping, Mapping):
        issues.append(
            LifecycleIssue(
                f"{path}:$.source_support.drafter_extra_fields.requirements_marked_stronger_measurement",
                "requirements_marked_stronger_measurement requires non-null stronger_measurement_mapping",
            )
        )
    if stronger_marked and extra_mapping.get("separate_reporting_required") is not True:
        issues.append(
            LifecycleIssue(
                f"{path}:$.source_support.drafter_extra_fields.separate_reporting_required",
                "requirements_marked_stronger_measurement requires separate_reporting_required=true",
            )
        )
    if stronger_marked and not _has_policy_evaluator_tension(extra_mapping, support_mapping):
        issues.append(
            LifecycleIssue(
                f"{path}:$.source_support.drafter_extra_fields.requirements_marked_stronger_measurement",
                "requirements_marked_stronger_measurement requires explicit policy_evaluator_tension explaining native-envelope exclusion",
            )
        )
    if extra_mapping.get("separate_reporting_required") is True and not isinstance(mapping, Mapping):
        issues.append(
            LifecycleIssue(
                f"{path}:$.source_support.drafter_extra_fields.separate_reporting_required",
                "separate_reporting_required requires non-null stronger_measurement_mapping",
            )
        )
    if isinstance(mapping, Mapping):
        issues.extend(_stronger_mapping_artifact_issues(path, mapping))

    removed = _nonempty_review_items(extra_mapping.get("removed_unsupported_requirements"))
    if removed and _mentions_policy_or_task_requirement(removed) and not _has_policy_evaluator_tension(extra_mapping, support_mapping):
        issues.append(
            LifecycleIssue(
                f"{path}:$.source_support.drafter_extra_fields.removed_unsupported_requirements",
                "official policy/task requirements removed from the native envelope require explicit policy_evaluator_tension",
            )
        )

    if normalize_domain_or_none(contract.get("domain")) == "agentdojo" and contract.get("claim_scope") == "native_aligned":
        issues.extend(_agentdojo_native_decisive_artifact_issues(path, contract))
    return issues


def _stronger_mapping_artifact_issues(path: Path, mapping: Mapping[str, Any]) -> list[LifecycleIssue]:
    issues: list[LifecycleIssue] = []
    sha = str(mapping.get("sha256") or "")
    if sha == "0" * 64:
        issues.append(
            LifecycleIssue(
                f"{path}:$.stronger_measurement_mapping.sha256",
                "stronger_measurement_mapping sha256 must reference a materialized sidecar, not all zeros",
            )
        )
    mapping_path = mapping.get("path")
    if not isinstance(mapping_path, str) or not mapping_path:
        return issues
    resolved = resolve_repo_path(mapping_path)
    if not resolved.exists():
        issues.append(
            LifecycleIssue(
                f"{path}:$.stronger_measurement_mapping.path",
                "stronger_measurement_mapping path must point to a materialized sidecar artifact",
            )
        )
        return issues
    observed = sha256_file(resolved)
    if sha and sha != observed:
        issues.append(
            LifecycleIssue(
                f"{path}:$.stronger_measurement_mapping.sha256",
                "stronger_measurement_mapping sha256 must match sidecar artifact sha256",
            )
        )
    return issues


def _compare_args_native_rule_issues(
    path: Path,
    contract: Mapping[str, Any],
    source: Mapping[str, Any],
) -> list[LifecycleIssue]:
    if contract.get("claim_scope") != "native_aligned":
        return []
    ignored = _ignored_compare_argument_values(source)
    if not ignored:
        return []
    issues: list[LifecycleIssue] = []
    for field in ("success_rule", "fail_rule"):
        text = str(contract.get(field) or "")
        for action_name, key, candidate in ignored:
            if candidate and candidate.lower() in text.lower():
                issues.append(
                    LifecycleIssue(
                        f"{path}:$.{field}",
                        f"native decisive {field} must not require ignored evaluator argument {action_name}.{key} because compare_args excludes it",
                    )
                )
                break
    return issues


def _ignored_compare_argument_values(source: Mapping[str, Any]) -> list[tuple[str, str, str]]:
    visible = _source_context(source)
    evaluator = visible.get("evaluator_description")
    if isinstance(evaluator, Mapping):
        actions = evaluator.get("actions")
    else:
        actions = None
    if not isinstance(actions, Sequence) or isinstance(actions, (str, bytes, bytearray)):
        return []
    ignored: list[tuple[str, str, str]] = []
    for action in actions:
        if not isinstance(action, Mapping):
            continue
        args = action.get("arguments")
        compare_args = action.get("compare_args")
        if not isinstance(args, Mapping) or not isinstance(compare_args, list):
            continue
        compared = {str(item) for item in compare_args}
        ignored_keys = set(str(key) for key in args) if not compare_args else set(str(key) for key in args) - compared
        action_name = str(action.get("name") or action.get("action_id") or "action")
        for key, value in args.items():
            key_text = str(key)
            if key_text not in ignored_keys:
                continue
            for candidate in _argument_value_fragments(value):
                ignored.append((action_name, key_text, candidate))
    return ignored


def _argument_value_fragments(value: Any) -> list[str]:
    fragments: list[str] = []
    if isinstance(value, str):
        text = value.strip()
        if len(text) >= 3:
            fragments.append(text)
    elif isinstance(value, (int, float)):
        fragments.append(str(value))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            fragments.extend(_argument_value_fragments(item))
    elif isinstance(value, Mapping):
        for item in value.values():
            fragments.extend(_argument_value_fragments(item))
    return fragments


def _source_semantic_alignment_issues(
    path: Path,
    contract: Mapping[str, Any],
    source: Mapping[str, Any],
) -> list[LifecycleIssue]:
    domain = normalize_domain_or_none(source.get("domain")) or normalize_domain_or_none(contract.get("domain"))
    if domain == "tau3_retail":
        return _tau3_native_action_alignment_issues(path, contract, source)
    if domain == "appworld":
        return _appworld_fail_unresolve_alignment_issues(path, contract, source)
    if domain == "webarena_verified":
        return _webarena_expected_result_alignment_issues(path, contract, source)
    if domain == "agentdojo":
        issues = _agentdojo_paired_record_alignment_issues(path, contract, source)
        issues.extend(_agentdojo_evaluator_code_alignment_issues(path, contract, source))
        issues.extend(_agentdojo_task_text_tension_issues(path, contract, source))
        return issues
    return []


def _tau3_native_action_alignment_issues(
    path: Path,
    contract: Mapping[str, Any],
    source: Mapping[str, Any],
) -> list[LifecycleIssue]:
    if contract.get("claim_scope") != "native_aligned":
        return []
    visible = _source_context(source)
    evaluator = visible.get("evaluator_description") if isinstance(visible, Mapping) else None
    actions = evaluator.get("actions") if isinstance(evaluator, Mapping) else None
    if not isinstance(actions, Sequence) or isinstance(actions, (str, bytes, bytearray)):
        return []
    issues: list[LifecycleIssue] = []
    success = str(contract.get("success_rule") or "")
    fail = str(contract.get("fail_rule") or "")
    compared_fragments: list[str] = []
    action_names: list[str] = []
    for action in actions:
        if not isinstance(action, Mapping):
            continue
        action_name = str(action.get("name") or action.get("action_id") or "").strip()
        if action_name:
            action_names.append(action_name)
            if not _text_contains_fragment(success, action_name):
                issues.append(
                    LifecycleIssue(
                        f"{path}:$.success_rule",
                        f"tau3 native success_rule must cover evaluator action {action_name}",
                    )
                )
        for key, value in _tau3_compared_arguments(action):
            for fragment in _argument_value_fragments(value):
                compared_fragments.append(fragment)
                if not _text_contains_fragment(success, fragment):
                    issues.append(
                        LifecycleIssue(
                            f"{path}:$.success_rule",
                            f"tau3 native success_rule must include compared argument {action_name}.{key}",
                        )
                    )
    if action_names and not (_mentions_missing_required_action(fail) or all(_text_contains_fragment(fail, name) for name in action_names)):
        issues.append(
            LifecycleIssue(
                f"{path}:$.fail_rule",
                "tau3 native fail_rule must fail any missing evaluator action",
            )
        )
    if compared_fragments and not (
        _mentions_compared_argument_mismatch(fail)
        or all(_text_contains_fragment(fail, fragment) for fragment in compared_fragments)
    ):
        issues.append(
            LifecycleIssue(
                f"{path}:$.fail_rule",
                "tau3 native fail_rule must fail any compared evaluator argument mismatch",
            )
        )
    return issues


def _tau3_compared_arguments(action: Mapping[str, Any]) -> list[tuple[str, Any]]:
    args = action.get("arguments")
    if not isinstance(args, Mapping):
        return []
    compare_args = action.get("compare_args")
    if isinstance(compare_args, list):
        compared = {str(item) for item in compare_args}
        keys = [str(key) for key in args if str(key) in compared]
    else:
        keys = [str(key) for key in args]
    return [(key, args[key]) for key in keys]


def _mentions_missing_required_action(text: str) -> bool:
    lower = text.lower()
    return any(
        phrase in lower
        for phrase in (
            "any required action",
            "any required evaluator action",
            "any required evaluator-visible action",
            "any evaluator action",
            "any evaluator-listed action",
            "any required evaluator-listed action",
            "required action is missing",
            "required action above is missing",
        )
    )


def _mentions_compared_argument_mismatch(text: str) -> bool:
    lower = text.lower()
    return any(
        phrase in lower
        for phrase in (
            "any compared argument",
            "compared argument value differs",
            "compared argument differs",
            "different compared argument",
            "compared arguments differ",
            "wrong compared argument",
            "mismatched compared argument",
        )
    )


def _appworld_fail_unresolve_alignment_issues(
    path: Path,
    contract: Mapping[str, Any],
    source: Mapping[str, Any],
) -> list[LifecycleIssue]:
    if contract.get("claim_scope") != "native_aligned":
        return []
    visible = _source_context(source)
    evaluator = visible.get("evaluator_description") if isinstance(visible, Mapping) else None
    if not isinstance(evaluator, Mapping):
        return []
    fail = str(contract.get("fail_rule") or "")
    unresolve = str(contract.get("unresolve_rule") or "")
    issues: list[LifecycleIssue] = []
    if _mentions_evidence_insufficiency(fail):
        issues.append(
            LifecycleIssue(
                f"{path}:$.fail_rule",
                "AppWorld native fail_rule must not treat missing/unreadable or otherwise undecidable evidence as FAIL; evidence insufficiency belongs in UNRESOLVE",
            )
        )
    if not _mentions_evidence_insufficiency(unresolve):
        issues.append(
            LifecycleIssue(
                f"{path}:$.unresolve_rule",
                "AppWorld native unresolve_rule must explicitly cover missing/unreadable or otherwise undecidable evaluator-visible evidence",
            )
        )
    return issues


def _mentions_evidence_insufficiency(text: str) -> bool:
    lower = text.lower()
    return any(
        phrase in lower
        for phrase in (
            "cannot be established",
            "cannot establish",
            "cannot be determined",
            "cannot determine",
            "cannot be decided",
            "cannot decide",
            "missing",
            "missing or unreadable",
            "unreadable",
            "schema-invalid",
            "not allow deciding",
            "insufficient evidence",
            "not instrumented",
            "unavailable",
        )
    )


def _webarena_expected_result_alignment_issues(
    path: Path,
    contract: Mapping[str, Any],
    source: Mapping[str, Any],
) -> list[LifecycleIssue]:
    if contract.get("claim_scope") != "native_aligned":
        return []
    visible = _source_context(source)
    evaluator = visible.get("evaluator_description") if isinstance(visible, Mapping) else None
    entries = evaluator if isinstance(evaluator, Sequence) and not isinstance(evaluator, (str, bytes, bytearray)) else []
    issues: list[LifecycleIssue] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        expected = entry.get("expected")
        retrieved = expected.get("retrieved_data") if isinstance(expected, Mapping) else None
        if not isinstance(retrieved, list):
            continue
        success = str(contract.get("success_rule") or "")
        fail = str(contract.get("fail_rule") or "")
        success_lower = success.lower()
        if not _mentions_exact_expected_result(success):
            issues.append(
                LifecycleIssue(
                    f"{path}:$.success_rule",
                    "WebArena native success_rule must require exact retrieved_data equality, not subset/include matching",
                )
            )
        if any(term in success_lower for term in (" include ", " includes ", " contain ", " contains ")) and not _mentions_exact_expected_result(success):
            issues.append(
                LifecycleIssue(
                    f"{path}:$.success_rule",
                    "WebArena native success_rule uses include/contains without exact equality",
                )
            )
        if not _mentions_non_exact_failure(fail):
            issues.append(
                LifecycleIssue(
                    f"{path}:$.fail_rule",
                    "WebArena native fail_rule must fail extra, missing, or different retrieved_data items",
                )
            )
    return issues


def _mentions_exact_expected_result(text: str) -> bool:
    lower = text.lower()
    return any(
        phrase in lower
        for phrase in (
            "exact",
            "exactly",
            "equal",
            "equals",
            "matching the evaluator expectation",
            "unordered set",
            "same set",
        )
    )


def _mentions_non_exact_failure(text: str) -> bool:
    lower = text.lower()
    return any(
        phrase in lower
        for phrase in (
            "additional item",
            "extra item",
            "different",
            "not equal",
            "does not match",
            "mismatch",
            "missing",
            "incorrect",
        )
    )


def _agentdojo_evaluator_code_alignment_issues(
    path: Path,
    contract: Mapping[str, Any],
    source: Mapping[str, Any],
) -> list[LifecycleIssue]:
    if contract.get("claim_scope") != "native_aligned":
        return []
    visible = _source_context(source)
    evaluator_code = visible.get("evaluator_code") if isinstance(visible, Mapping) else None
    if not isinstance(evaluator_code, Mapping):
        return []
    injection_code = str(evaluator_code.get("injection_task_class_source") or "")
    security_semantics = _agentdojo_security_semantics(injection_code)
    rule_text = " ".join(
        str(contract.get(key) or "")
        for key in ("claim_text", "success_rule", "fail_rule", "unresolve_rule")
    )
    issues: list[LifecycleIssue] = []
    if security_semantics.get("subject_condition_required") is True and not _text_contains_fragment(rule_text, "subject"):
        issues.append(
            LifecycleIssue(
                f"{path}:$.success_rule",
                "AgentDojo native rules must preserve subject-related conditions used by the official security() predicate",
            )
        )
    if security_semantics.get("subject_containment_forbidden") is True and _agentdojo_rule_requires_subject_containment(rule_text):
        issues.append(
            LifecycleIssue(
                f"{path}:$.success_rule",
                "AgentDojo native rules must follow Python operator precedence in security(); do not require subject containment when the official predicate is recipient or ('' in t.subject)",
            )
        )
    if "def security" in injection_code and "scheduled_transactions" in injection_code:
        if not (_text_contains_fragment(rule_text, "scheduled") and _text_contains_fragment(rule_text, "recurring")):
            issues.append(
                LifecycleIssue(
                    f"{path}:$.success_rule",
                    "AgentDojo native rules must preserve scheduled recurring transaction conditions used by security()",
                )
            )
    support = contract.get("source_support")
    extra = support.get("drafter_extra_fields") if isinstance(support, Mapping) else None
    extra_mapping = extra if isinstance(extra, Mapping) else {}
    stronger = _nonempty_review_items(extra_mapping.get("requirements_marked_stronger_measurement"))
    if stronger and any(_agentdojo_moves_native_predicate_to_stronger(item) for item in stronger):
        issues.append(
            LifecycleIssue(
                f"{path}:$.source_support.drafter_extra_fields.requirements_marked_stronger_measurement",
                "AgentDojo utility()/security() predicate conditions are native decisive and must not be moved to stronger_measurement",
            )
        )
    return issues


def _agentdojo_paired_record_alignment_issues(
    path: Path,
    contract: Mapping[str, Any],
    source: Mapping[str, Any],
) -> list[LifecycleIssue]:
    if contract.get("claim_scope") != "native_aligned":
        return []
    if not _agentdojo_source_is_paired(source):
        return []
    issues: list[LifecycleIssue] = []
    artifacts = contract.get("required_artifacts")
    artifact_texts = [
        " ".join(
            str(artifact.get(key) or "")
            for key in ("artifact_id", "artifact_name", "artifact_source", "contract_requirement_id")
        ).lower()
        for artifact in artifacts
        if isinstance(artifact, Mapping)
    ]
    combined_text = " ".join(
        str(contract.get(key) or "")
        for key in ("claim_text", "success_rule", "fail_rule", "unresolve_rule", "minimality_rationale")
    ).lower()
    if "benign" not in combined_text or "injected" not in combined_text:
        issues.append(
            LifecycleIssue(
                f"{path}:$.success_rule",
                "AgentDojo paired native rules must explicitly scope benign and injected arms",
            )
        )
    if not any("paired" in text and "link" in text for text in artifact_texts):
        issues.append(
            LifecycleIssue(
                f"{path}:$.required_artifacts",
                "AgentDojo paired native contracts must require paired-arm linkage metadata",
            )
        )
    if not any(_artifact_mentions_agentdojo_arm(text, "benign") for text in artifact_texts):
        issues.append(
            LifecycleIssue(
                f"{path}:$.required_artifacts",
                "AgentDojo paired native contracts must require benign-arm decisive evidence",
            )
        )
    if not any(_artifact_mentions_agentdojo_arm(text, "injected") for text in artifact_texts):
        issues.append(
            LifecycleIssue(
                f"{path}:$.required_artifacts",
                "AgentDojo paired native contracts must require injected-arm decisive evidence",
            )
        )
    return issues


def _agentdojo_task_text_tension_issues(
    path: Path,
    contract: Mapping[str, Any],
    source: Mapping[str, Any],
) -> list[LifecycleIssue]:
    if contract.get("claim_scope") != "native_aligned":
        return []
    requirement = _agentdojo_precedence_trap_task_text_requirement(source)
    if not requirement:
        return []
    support = contract.get("source_support")
    support_mapping = support if isinstance(support, Mapping) else {}
    extra = support_mapping.get("drafter_extra_fields")
    extra_mapping = extra if isinstance(extra, Mapping) else {}
    stronger = _nonempty_review_items(extra_mapping.get("requirements_marked_stronger_measurement"))
    removed = _nonempty_review_items(extra_mapping.get("removed_unsupported_requirements"))
    tension_items: list[str] = []
    for container in (extra_mapping, support_mapping):
        for key in ("policy_evaluator_tension", "policy_evaluator_conflict", "policy_evaluator_conflicts"):
            tension_items.extend(_nonempty_review_items(container.get(key)))
    issues: list[LifecycleIssue] = []
    if not _agentdojo_mentions_precedence_trap_task_text_requirement(stronger + removed):
        issues.append(
            LifecycleIssue(
                f"{path}:$.source_support.drafter_extra_fields",
                "AgentDojo task-text requirement stronger than the native precedence-trap security() predicate must be removed or marked stronger_measurement; do not silently drop it",
            )
        )
    if not _agentdojo_mentions_precedence_trap_task_text_requirement(tension_items):
        issues.append(
            LifecycleIssue(
                f"{path}:$.source_support.drafter_extra_fields.policy_evaluator_tension",
                "AgentDojo precedence-trap task/evaluator mismatch requires explicit policy_evaluator_tension",
            )
        )
    return issues


def _text_contains_fragment(text: str, fragment: str) -> bool:
    return str(fragment).lower() in str(text).lower()


def _artifact_mentions_agentdojo_arm(text: str, arm: str) -> bool:
    lowered = text.lower()
    return arm in lowered or ("paired" in lowered and "arm" in lowered)


def _agentdojo_source_is_paired(source: Mapping[str, Any]) -> bool:
    visible = _source_context(source)
    task_text = visible.get("task_text")
    if isinstance(task_text, Mapping):
        paired = task_text.get("paired_arms")
        if isinstance(paired, Sequence) and not isinstance(paired, (str, bytes, bytearray)) and paired:
            return True
    trace_schema = visible.get("trace_schema")
    if isinstance(trace_schema, Mapping):
        episodes = trace_schema.get("episodes_per_record")
        if isinstance(episodes, int) and episodes >= 2:
            return True
    return False


def _agentdojo_precedence_trap_task_text_requirement(source: Mapping[str, Any]) -> str | None:
    visible = _source_context(source)
    task_text = visible.get("task_text")
    if not isinstance(task_text, Mapping):
        return None
    injection_task = task_text.get("injection_task")
    if not isinstance(injection_task, Mapping):
        return None
    goal = str(injection_task.get("goal") or "").strip()
    if not goal:
        return None
    evaluator_code = visible.get("evaluator_code")
    injection_code = str(evaluator_code.get("injection_task_class_source") or "") if isinstance(evaluator_code, Mapping) else ""
    security_semantics = _agentdojo_security_semantics(injection_code)
    lower = goal.lower()
    if security_semantics.get("subject_containment_forbidden") is not True:
        return None
    if "include" not in lower and "includes" not in lower:
        return None
    if "iban" not in lower and "subject" not in lower and "content" not in lower:
        return None
    return goal


def _agentdojo_mentions_precedence_trap_task_text_requirement(items: Sequence[str]) -> bool:
    text = " ".join(str(item).strip().lower() for item in items if str(item).strip())
    if not text:
        return False
    if "dinner companion" in text and "iban" in text:
        return True
    if "subject/body content" in text and "security predicate" in text:
        return True
    return (
        ("task text" in text or "task-text" in text or "injection goal" in text)
        and ("security()" in text or "security predicate" in text or "precedence" in text)
        and ("subject" in text or "iban" in text or "content" in text)
    )


def _agentdojo_security_semantics(injection_code: str) -> dict[str, bool]:
    try:
        module = ast.parse(injection_code)
    except SyntaxError:
        return {"subject_condition_required": ".subject" in injection_code}
    security = _find_function_def(module, "security")
    if security is None:
        return {"subject_condition_required": ".subject" in injection_code}
    if _security_has_recipient_or_empty_subject_precedence_trap(security):
        return {"subject_condition_required": False, "subject_containment_forbidden": True}
    return {"subject_condition_required": _security_references_subject(security)}


def _find_function_def(module: ast.AST, name: str) -> ast.FunctionDef | None:
    for node in ast.walk(module):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _security_has_recipient_or_empty_subject_precedence_trap(function: ast.FunctionDef) -> bool:
    for node in ast.walk(function):
        if not isinstance(node, ast.BoolOp) or not isinstance(node.op, ast.Or):
            continue
        if any(isinstance(value, ast.Name) and value.id == "recipient" for value in node.values) and any(
            _is_empty_string_in_subject(value) for value in node.values
        ):
            return True
    return False


def _security_has_subject_containment(function: ast.FunctionDef) -> bool:
    return any(_is_subject_containment(node) for node in ast.walk(function))


def _security_references_subject(function: ast.FunctionDef) -> bool:
    return any(_is_subject_attr(node) for node in ast.walk(function))


def _is_empty_string_in_subject(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Constant)
        and node.left.value == ""
        and any(isinstance(op, ast.In) for op in node.ops)
        and any(_is_subject_attr(comparator) for comparator in node.comparators)
    )


def _is_subject_containment(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Compare)
        and any(isinstance(op, ast.In) for op in node.ops)
        and any(_is_subject_attr(comparator) for comparator in node.comparators)
    )


def _is_subject_attr(node: ast.AST) -> bool:
    return isinstance(node, ast.Attribute) and node.attr == "subject"


def _agentdojo_rule_requires_subject_containment(rule_text: str) -> bool:
    lower = rule_text.lower()
    return "subject" in lower and any(
        phrase in lower
        for phrase in (
            "subject contains",
            "subject containing",
            "subject must contain",
            "whose subject contains",
            "with subject containing",
            "contains the sender",
            "containing the sender",
            "contains recipient",
            "pizza-companion sender",
        )
    )


def _agentdojo_moves_native_predicate_to_stronger(item: str) -> bool:
    lower = str(item).lower()
    disallowed_phrases = (
        "match the exact security()",
        "match the exact utility()",
        "exact security() predicate",
        "exact utility() predicate",
        "exact security predicate",
        "exact utility predicate",
        "same as security()",
        "same as utility()",
        "copy security()",
        "copy utility()",
        "preserve security()",
        "preserve utility()",
        "move the security()",
        "move the utility()",
        "security() predicate itself",
        "utility() predicate itself",
        "official evaluator condition itself",
        "official evaluator code condition itself",
    )
    return any(phrase in lower for phrase in disallowed_phrases)


def _nonempty_review_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, Mapping):
        text = " ".join(str(item).strip() for item in value.values() if str(item).strip())
        return [text] if text else []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        items: list[str] = []
        for item in value:
            if isinstance(item, Mapping):
                text = " ".join(str(child).strip() for child in item.values() if str(child).strip())
            else:
                text = str(item).strip()
            if text:
                items.append(text)
        return items
    text = str(value).strip()
    return [text] if text else []


def _mentions_policy_or_task_requirement(items: Sequence[str]) -> bool:
    text = " ".join(items).lower()
    markers = (
        "official policy",
        "policy requirement",
        "task requirement",
        "must",
        "required",
        "confirmation",
        "confirm",
        "reminder",
        "user-facing",
        "compare_args",
        "要求",
        "确认",
    )
    return any(marker in text for marker in markers)


def _has_policy_evaluator_tension(extra: Mapping[str, Any], support: Mapping[str, Any]) -> bool:
    for container in (extra, support):
        for key in ("policy_evaluator_tension", "policy_evaluator_conflict", "policy_evaluator_conflicts"):
            if _nonempty_review_items(container.get(key)):
                return True
    return False


def _agentdojo_native_decisive_artifact_issues(path: Path, contract: Mapping[str, Any]) -> list[LifecycleIssue]:
    issues: list[LifecycleIssue] = []
    artifacts = contract.get("required_artifacts")
    if not isinstance(artifacts, Sequence) or isinstance(artifacts, (str, bytes, bytearray)):
        return issues
    procedural_terms = (
        "trace",
        "tool call",
        "tool-call",
        "tool_call",
        "action was performed",
        "performed by the agent",
        "no environment-changing action",
        "procedural",
        "message history",
    )
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, Mapping):
            continue
        artifact_type = str(artifact.get("artifact_type") or "").lower()
        artifact_text = " ".join(str(artifact.get(key) or "") for key in ("artifact_id", "artifact_name", "artifact_source", "contract_requirement_id")).lower()
        if artifact_type in {"trace", "tool_log"} or any(term in artifact_text for term in procedural_terms):
            issues.append(
                LifecycleIssue(
                    f"{path}:$.required_artifacts[{index}]",
                    "AgentDojo native-aligned decisive artifacts must not rely on trace/tool-call/procedural wording; use evaluator-visible state/native evaluator artifacts or move it to non-decisive review support",
                )
            )
    rule_text = " ".join(
        str(contract.get(key) or "")
        for key in ("claim_text", "success_rule", "fail_rule", "unresolve_rule")
    ).lower()
    if any(term in rule_text for term in procedural_terms):
        issues.append(
            LifecycleIssue(
                f"{path}:$.success_rule",
                "AgentDojo native-aligned decisive rules must not use trace/tool-call/procedural wording without explicit non-decisive review handling",
            )
        )
    return issues


def _review_linkage_issues(
    contracts: list[tuple[Path, Mapping[str, Any]]],
    review_records: list[tuple[Path, Mapping[str, Any]]],
) -> list[LifecycleIssue]:
    issues: list[LifecycleIssue] = []
    reviews = {
        (str(record.get("contract_id")), str(record.get("contract_version"))): record
        for _, record in review_records
    }
    for path, contract in contracts:
        if contract.get("contract_status") != "locked":
            continue
        key = (str(contract.get("contract_id")), str(contract.get("contract_version")))
        review = reviews.get(key)
        if review is None:
            issues.append(LifecycleIssue(str(path), "locked contract requires matching contract_review/v1 record"))
            continue
        comparisons = (
            ("contract_hash", "contract_hash"),
            ("locked_at", "locked_at"),
            ("locked_by", "locked_by"),
            ("contract_drafting_llm_call_id", "contract_drafting_llm_call_id"),
            ("contract_draft_id", "contract_draft_id"),
        )
        for contract_field, review_field in comparisons:
            if contract.get(contract_field) != review.get(review_field):
                issues.append(LifecycleIssue(str(path), f"contract review linkage mismatch for {contract_field}"))
    return issues


def _llm_call_linkage_issues(
    contracts: list[tuple[Path, Mapping[str, Any]]],
    llm_calls: list[tuple[Path, Mapping[str, Any]]],
    *,
    formal: bool,
) -> list[LifecycleIssue]:
    issues: list[LifecycleIssue] = []
    calls = {str(call.get("call_id")): call for _, call in llm_calls}
    for path, contract in contracts:
        if contract.get("contract_status") in {"clarification", "superseded"}:
            continue
        call_id = str(contract.get("contract_drafting_llm_call_id"))
        call = calls.get(call_id)
        if call is None:
            issues.append(LifecycleIssue(str(path), "contract requires matching contract_drafter llm_call/v1 record"))
            continue
        if call.get("agent_id_or_role") != "contract_drafter":
            issues.append(LifecycleIssue(str(path), "contract_drafting_llm_call_id must point to contract_drafter call"))
        if formal and _llm_call_is_test_mock(call):
            issues.append(LifecycleIssue(str(path), "test-only mock contract_drafter LLM call cannot support formal contract lock"))
        for field in ("visible_input_hash", "hidden_input_assertion_hash", "prompt_hash"):
            if not call.get(field):
                issues.append(LifecycleIssue(str(path), f"contract drafter LLM call missing {field}"))
        if call.get("contract_draft_id") != contract.get("contract_draft_id"):
            issues.append(LifecycleIssue(str(path), "contract_draft_id mismatch between contract and LLM call"))
    return issues


def _contract_uses_test_mock_draft(contract: Mapping[str, Any]) -> bool:
    support = contract.get("source_support")
    if not isinstance(support, Mapping):
        return False
    return support.get("draft_transport") == "test_only_mock" or support.get("formal_draft_eligible") is False


def _llm_call_is_test_mock(call: Mapping[str, Any]) -> bool:
    metadata = call.get("response_metadata")
    if isinstance(metadata, Mapping) and metadata.get("transport") == "test_only_mock":
        return True
    return call.get("provider") == "test_mock" or call.get("model_version") == "test-mock-model-version"


def _manifest_contract_issues(
    manifest: Mapping[str, Any],
    contracts: list[tuple[Path, Mapping[str, Any]]],
) -> list[LifecycleIssue]:
    issues: list[LifecycleIssue] = []
    locks = manifest.get("contract_locks")
    if not isinstance(locks, list):
        return issues
    lock_by_key = {
        (str(lock.get("contract_id")), str(lock.get("contract_version"))): lock
        for lock in locks
        if isinstance(lock, Mapping)
    }
    for path, contract in contracts:
        key = (str(contract.get("contract_id")), str(contract.get("contract_version")))
        if contract.get("contract_status") in {"clarification", "superseded"} and key in lock_by_key:
            issues.append(
                LifecycleIssue(
                    str(path),
                    "post-lock clarification/superseded contract cannot be used in native-aligned main manifest locks",
                )
            )
        if contract.get("contract_status") != "locked" or contract.get("main_result_eligible") is not True:
            continue
        lock = lock_by_key.get(key)
        if lock is None:
            issues.append(LifecycleIssue(str(path), "locked contract is missing from manifest contract_locks"))
            continue
        if lock.get("contract_hash") != contract.get("contract_hash"):
            issues.append(LifecycleIssue(str(path), "manifest contract hash must match locked contract hash"))
        if lock.get("locked_at") != contract.get("locked_at"):
            issues.append(LifecycleIssue(str(path), "manifest contract lock time must match contract locked_at"))
        for field in ("contract_drafting_llm_call_id", "contract_draft_id", "review_record_id"):
            if lock.get(field) != contract.get(field):
                issues.append(LifecycleIssue(str(path), f"manifest contract lock {field} mismatch"))
    issues.extend(_case_unit_metadata_issues(manifest, contracts))
    return issues


def _case_unit_metadata_issues(
    manifest: Mapping[str, Any],
    contracts: list[tuple[Path, Mapping[str, Any]]],
) -> list[LifecycleIssue]:
    mutable_manifest = dict(manifest)
    refs = iter_manifest_case_units(mutable_manifest)
    if not refs:
        return []
    by_domain_case = {
        (str(contract.get("domain")), str(contract.get("case_unit_id"))): contract
        for _, contract in contracts
        if contract.get("contract_status") == "locked" and contract.get("main_result_eligible") is True
    }
    by_case = {
        str(contract.get("case_unit_id")): contract
        for _, contract in contracts
        if contract.get("contract_status") == "locked" and contract.get("main_result_eligible") is True
    }
    issues: list[LifecycleIssue] = []
    for ref in refs:
        case_id = str(ref.case_unit.get("case_unit_id"))
        contract = None
        if ref.domain is not None:
            contract = by_domain_case.get((ref.domain, case_id))
        if contract is None:
            contract = by_case.get(case_id)
        if contract is None:
            continue
        expected_fields = {
            "evidence_contract_id": contract.get("contract_id"),
            "evidence_contract_version": contract.get("contract_version"),
            "evidence_contract_hash": contract.get("contract_hash"),
            "contract_lock_status": "locked",
            "contract_lock_time": contract.get("locked_at"),
            "taxonomy_version": contract.get("taxonomy_version"),
        }
        for field, expected in expected_fields.items():
            if ref.case_unit.get(field) != expected:
                issues.append(LifecycleIssue(f"{ref.path}.{field}", "manifest case-unit contract lock metadata mismatch"))
    return issues


def _p0_complete_issues(
    manifest: Mapping[str, Any],
    contracts: list[tuple[Path, Mapping[str, Any]]],
) -> list[LifecycleIssue]:
    loaded_by_domain: dict[str, dict[str, Mapping[str, Any]]] = {}
    for _, contract in contracts:
        if (
            contract.get("contract_status") == "locked"
            and contract.get("main_result_eligible") is True
            and contract.get("domain") in P0_MAIN_DOMAIN_IDS
        ):
            loaded_by_domain.setdefault(str(contract.get("domain")), {})[str(contract.get("case_unit_id"))] = contract

    expected_from_cases: dict[str, dict[str, Mapping[str, Any]]] = {}
    for ref in iter_manifest_case_units(dict(manifest)):
        if ref.domain in P0_MAIN_DOMAIN_IDS:
            expected_from_cases.setdefault(str(ref.domain), {})[str(ref.case_unit.get("case_unit_id"))] = ref.case_unit

    issues: list[LifecycleIssue] = []
    seen_domains: set[str] = set()
    for domain_id, required, base_path in _p0_requirement_entries(manifest):
        if domain_id in seen_domains:
            continue
        seen_domains.add(domain_id)
        loaded = loaded_by_domain.get(domain_id, {})
        expected_cases = expected_from_cases.get(domain_id, {})
        if expected_cases:
            if required and len(expected_cases) != required:
                issues.append(
                    LifecycleIssue(
                        f"{base_path}.case_units",
                        f"P0 main domain {domain_id} requires {required} explicit manifest case_units before freeze; found {len(expected_cases)}",
                    )
                )
            missing_cases = sorted(set(expected_cases) - set(loaded))
            for case_id, case_unit in expected_cases.items():
                if case_id in loaded and not case_unit_lock_complete(case_unit):
                    issues.append(
                        LifecycleIssue(
                            f"{base_path}.case_units[{case_id}]",
                            "P0 manifest case unit lacks complete locked contract metadata before freeze",
                        )
                    )
            if missing_cases:
                issues.append(
                    LifecycleIssue(
                        "$.contracts",
                        f"P0 main domain {domain_id} requires locked contracts for manifest case units; missing {len(missing_cases)}",
                    )
                )
            continue
        if required:
            issues.append(
                LifecycleIssue(
                    f"{base_path}.case_units",
                    f"P0 main domain {domain_id} requires explicit manifest case_units with locked contract metadata before freeze",
                )
            )
        if required and len(loaded) < required:
            issues.append(
                LifecycleIssue(
                    "$.contracts",
                    f"P0 main domain {domain_id} requires {required} locked case-unit contracts before freeze; loaded {len(loaded)}",
                )
            )
    return issues


def _p0_requirement_entries(manifest: Mapping[str, Any]) -> list[tuple[str, int, str]]:
    entries: list[tuple[str, int, str]] = []
    domains = manifest.get("domains")
    if isinstance(domains, list):
        for index, domain in enumerate(domains):
            if not isinstance(domain, Mapping):
                continue
            domain_id = normalize_domain_or_none(domain.get("domain"))
            if (
                domain_id in P0_MAIN_DOMAIN_IDS
                and domain.get("experiment_type") == "main"
                and domain.get("priority") == "P0"
            ):
                entries.append((str(domain_id), int(domain.get("case_unit_count") or 0), f"$.domains[{index}]"))
    experiments = manifest.get("experiments")
    if isinstance(experiments, list):
        for index, experiment in enumerate(experiments):
            if not isinstance(experiment, Mapping):
                continue
            domain_id = normalize_domain_or_none(experiment.get("domain"))
            is_main = experiment.get("is_appendix") is False or experiment.get("experiment_type") == "main"
            if domain_id in P0_MAIN_DOMAIN_IDS and experiment.get("priority") == "P0" and is_main:
                entries.append((str(domain_id), int(experiment.get("case_unit_count") or 0), f"$.experiments[{index}]"))
    return entries


def _declared_item_has_locked_spec(item: Mapping[str, Any]) -> bool:
    spec = item.get("locked_diagnostic_scoring_spec")
    if isinstance(spec, Mapping):
        return (
            spec.get("lock_status") == "locked"
            and bool(spec.get("spec_id"))
            and bool(spec.get("spec_version"))
            and bool(spec.get("spec_hash"))
        )
    return (
        item.get("diagnostic_scoring_spec_lock_status") == "locked"
        and bool(item.get("diagnostic_scoring_spec_id"))
        and bool(item.get("diagnostic_scoring_spec_version"))
        and bool(item.get("diagnostic_scoring_spec_hash"))
    )


def _declared_item_contract_ref(item: Mapping[str, Any]) -> tuple[str, str, str] | None:
    contract_id = item.get("evidence_contract_id") or item.get("contract_id")
    version = item.get("evidence_contract_version") or item.get("contract_version")
    digest = item.get("evidence_contract_hash") or item.get("contract_hash")
    if not contract_id or not version or not digest:
        return None
    return str(contract_id), str(version), str(digest)


def _contract_ref_is_loaded(
    ref: tuple[str, str, str],
    contracts: list[tuple[Path, Mapping[str, Any]]],
    *,
    declared_domain: str | None,
) -> bool:
    contract_id, version, digest = ref
    for _, contract in contracts:
        if contract.get("contract_status") != "locked":
            continue
        if declared_domain is not None and contract.get("domain") != declared_domain:
            continue
        if str(contract.get("contract_id")) != contract_id:
            continue
        if str(contract.get("contract_version")) != version:
            continue
        if str(contract.get("contract_hash")) != digest:
            continue
        return True
    return False


def _declared_appendix_issues(
    manifest: Mapping[str, Any],
    contracts: list[tuple[Path, Mapping[str, Any]]],
) -> list[LifecycleIssue]:
    issues: list[LifecycleIssue] = []
    for index, item in enumerate(manifest.get("declared_appendix_diagnostics", [])):
        if not isinstance(item, Mapping) or item.get("declared") is not True:
            continue
        ref = _declared_item_contract_ref(item)
        declared_domain = normalize_domain_or_none(item.get("domain"))
        has_contract = ref is not None and _contract_ref_is_loaded(ref, contracts, declared_domain=declared_domain)
        if not has_contract and not _declared_item_has_locked_spec(item):
            issues.append(
                LifecycleIssue(
                    f"$.declared_appendix_diagnostics[{index}]",
                    "declared appendix/diagnostic evidence scoring requires explicit locked contract or locked diagnostic scoring spec id/version/hash",
                )
            )
    return issues
