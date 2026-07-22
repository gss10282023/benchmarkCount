"""Shared primitives for the evidence-contract lifecycle."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, MutableMapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evidence_system.core.errors import EvidenceSystemError
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml


class ContractLifecycleError(EvidenceSystemError):
    """Raised when a contract lifecycle gate must fail closed."""


@dataclass(frozen=True)
class LifecycleIssue:
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "message": self.message}


@dataclass(frozen=True)
class ManifestCaseUnitRef:
    domain: str | None
    case_unit: MutableMapping[str, Any]
    parent: MutableMapping[str, Any] | None
    path: str


DOMAIN_ALIASES = {
    "AgentDojo": "agentdojo",
    "agentdojo": "agentdojo",
    "AppWorld": "appworld",
    "appworld": "appworld",
    "MiniWoB++": "miniwob",
    "MiniWoB": "miniwob",
    "miniwob": "miniwob",
    "miniwob++": "miniwob",
    "WebArena-Verified": "webarena_verified",
    "webarena_verified": "webarena_verified",
    "tau3-bench retail": "tau3_retail",
    "τ³-bench retail": "tau3_retail",
    "tau3_retail": "tau3_retail",
    "tau3 retail": "tau3_retail",
    "AndroidWorld": "androidworld",
    "androidworld": "androidworld",
    "WorkArena": "workarena",
    "workarena": "workarena",
    "ToolSandbox": "toolsandbox",
    "toolsandbox": "toolsandbox",
    "tool_sandbox": "toolsandbox",
    "OSWorld-Verified": "osworld_verified",
    "osworld_verified": "osworld_verified",
    "judge_only": "judge_only",
    "maintenance_update": "maintenance_update",
    "matched_budget_controls": "matched_budget_controls",
}

DRAFTER_FORBIDDEN_FIELDS = frozenset(
    {
        "agent_identity",
        "agent_id",
        "agent",
        "agent_trace",
        "trace_with_agent_identity",
        "native_score",
        "native_label",
        "native_pass_fail",
        "native_pass_fail_scalar",
        "native_evaluator_score",
        "native_evaluator_label",
        "native_evaluator_verdict",
        "native_evaluator_pass_fail",
        "native_evaluator_pass_fail_scalar",
        "native_evaluator_pass_fail_label",
        "evaluator_pass_fail",
        "evaluator_pass_fail_scalar",
        "pass_fail_scalar",
        "outcome_label",
        "prior_outcome_verdict",
        "alternate_view_verdict",
        "alternate_view_verdicts",
        "evidence_label",
        "final_evidence_label",
        "unresolve_reason",
        "counting_decision",
        "scored_record",
        "scored_records",
        "scored_label",
        "scored_verdict",
        "scored_value",
        "scored_values",
        "paper_output",
        "paper_outputs",
        "paper_output_value",
        "paper_output_values",
        "final_verdict",
        "judge_only_label",
        "judge_only_labels",
        "adapter_summary_verdict",
        "runner_summary_verdict",
    }
)

SELF_HASH_FIELDS = frozenset({"contract_hash", "canonical_hash"})


def normalize_domain(domain: Any) -> str:
    value = str(domain)
    normalized = DOMAIN_ALIASES.get(value)
    if normalized is None:
        normalized = DOMAIN_ALIASES.get(value.strip())
    if normalized is None:
        raise ContractLifecycleError(f"unknown or non-canonical contract domain: {domain!r}")
    return normalized


def normalize_domain_or_none(domain: Any) -> str | None:
    try:
        return normalize_domain(domain)
    except ContractLifecycleError:
        return None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_timestamp(value: str, field_name: str) -> datetime:
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ContractLifecycleError(f"{field_name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ContractLifecycleError(f"{field_name} must include a timezone offset")
    return parsed


def duration_minutes(start: str, finish: str) -> float:
    started = parse_timestamp(start, "started_at")
    finished = parse_timestamp(finish, "finished_at")
    if finished <= started:
        raise ContractLifecycleError("review_finished_at must be after review_started_at")
    return round((finished - started).total_seconds() / 60.0, 6)


def load_mapping(path: str | Path) -> dict[str, Any]:
    loaded = load_json_or_yaml(path)
    if not isinstance(loaded, dict):
        raise ContractLifecycleError(f"expected mapping file: {path}")
    return dict(loaded)


def load_sequence_or_mapping(path: str | Path) -> Any:
    return load_json_or_yaml(path)


def write_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    resolved = resolve_repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return resolved


def display_path(path: str | Path) -> str:
    resolved = resolve_repo_path(path)
    try:
        return str(resolved.relative_to(resolve_repo_path(".")))
    except ValueError:
        return str(resolved)


def hash_path_if_exists(path: str | Path | None) -> str:
    if path is None:
        return "0" * 64
    resolved = resolve_repo_path(path)
    if not resolved.exists():
        return "0" * 64
    return sha256_file(resolved)


def contract_hash_payload(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Return the canonical contract hash payload.

    ``manifest_hash`` is excluded to avoid a circular dependency between the
    manifest artifact hash and the locked contract artifact. The contract hash
    still binds contract identity, version, status, rules, artifacts, reviewer
    linkage, and canonical path metadata.
    """

    return {
        key: value
        for key, value in contract.items()
        if key not in SELF_HASH_FIELDS and key != "manifest_hash" and not key.startswith("__")
    }


def contract_content_hash(contract: Mapping[str, Any]) -> str:
    return sha256_object(contract_hash_payload(contract))


def stamp_contract_hash(contract: MutableMapping[str, Any]) -> None:
    digest = contract_content_hash(contract)
    contract["contract_hash"] = digest
    contract["canonical_hash"] = digest


def contract_output_name(contract: Mapping[str, Any]) -> str:
    contract_id = str(contract.get("contract_id") or "contract")
    version = str(contract.get("contract_version") or "version").replace("/", "_")
    return f"{contract_id}__{version}.json"


def iter_json_files(paths: Iterable[str | Path]) -> list[Path]:
    files: list[Path] = []
    for item in paths:
        path = resolve_repo_path(item)
        if path.is_dir():
            files.extend(sorted(p for p in path.rglob("*.json") if p.is_file()))
        elif path.is_file():
            files.append(path)
        else:
            raise ContractLifecycleError(f"missing contract lifecycle path: {path}")
    return files


def find_forbidden_inputs(payload: Any, base: str = "$") -> list[LifecycleIssue]:
    issues: list[LifecycleIssue] = []
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            key_text = str(key)
            if key_text in DRAFTER_FORBIDDEN_FIELDS:
                issues.append(LifecycleIssue(f"{base}.{key_text}", "drafter-forbidden input field is present"))
            issues.extend(find_forbidden_inputs(value, f"{base}.{key_text}"))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            issues.extend(find_forbidden_inputs(value, f"{base}[{index}]"))
    return issues

def contract_lock_entry(contract: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "contract_id": contract["contract_id"],
        "contract_version": contract["contract_version"],
        "contract_hash": contract["contract_hash"],
        "lock_status": "locked",
        "locked_at": contract["locked_at"],
        "review_record_id": contract["review_record_id"],
        "contract_drafting_llm_call_id": contract["contract_drafting_llm_call_id"],
        "contract_draft_id": contract["contract_draft_id"],
        "canonicalization_method": "json_canonical_sha256",
        "canonical_hash_source": contract.get("canonical_hash_source"),
        "main_result_eligible": True,
    }


def iter_manifest_case_units(manifest: MutableMapping[str, Any]) -> list[ManifestCaseUnitRef]:
    refs: list[ManifestCaseUnitRef] = []
    top_level = manifest.get("case_units")
    if isinstance(top_level, list):
        for index, case_unit in enumerate(top_level):
            if isinstance(case_unit, MutableMapping):
                refs.append(
                    ManifestCaseUnitRef(
                        domain=normalize_domain_or_none(case_unit.get("domain")),
                        case_unit=case_unit,
                        parent=None,
                        path=f"$.case_units[{index}]",
                    )
                )
    domains = manifest.get("domains")
    if isinstance(domains, list):
        for domain_index, domain_entry in enumerate(domains):
            if not isinstance(domain_entry, MutableMapping):
                continue
            domain_id = normalize_domain_or_none(domain_entry.get("domain"))
            case_units = domain_entry.get("case_units")
            if not isinstance(case_units, list):
                continue
            for case_index, case_unit in enumerate(case_units):
                if isinstance(case_unit, MutableMapping):
                    refs.append(
                        ManifestCaseUnitRef(
                            domain=normalize_domain_or_none(case_unit.get("domain")) or domain_id,
                            case_unit=case_unit,
                            parent=domain_entry,
                            path=f"$.domains[{domain_index}].case_units[{case_index}]",
                        )
                    )
    experiments = manifest.get("experiments")
    if isinstance(experiments, list):
        for experiment_index, experiment in enumerate(experiments):
            if not isinstance(experiment, MutableMapping):
                continue
            domain_id = normalize_domain_or_none(experiment.get("domain"))
            case_units = experiment.get("case_units")
            if not isinstance(case_units, list):
                continue
            for case_index, case_unit in enumerate(case_units):
                if isinstance(case_unit, MutableMapping):
                    refs.append(
                        ManifestCaseUnitRef(
                            domain=normalize_domain_or_none(case_unit.get("domain")) or domain_id,
                            case_unit=case_unit,
                            parent=experiment,
                            path=f"$.experiments[{experiment_index}].case_units[{case_index}]",
                        )
                    )
    return refs


def case_unit_lock_complete(case_unit: Mapping[str, Any]) -> bool:
    required = (
        "evidence_contract_id",
        "evidence_contract_version",
        "evidence_contract_hash",
        "contract_lock_status",
        "contract_lock_time",
        "taxonomy_version",
    )
    return all(case_unit.get(field) for field in required) and case_unit.get("contract_lock_status") == "locked"
