"""Lock reviewed evidence contracts before scoring."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evidence_system.contracts.common import (
    ContractLifecycleError,
    contract_output_name,
    display_path,
    iter_json_files,
    load_mapping,
    stamp_contract_hash,
    write_json,
)
from evidence_system.contracts.review_time import review_timing
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import validate_object


@dataclass(frozen=True)
class LockResult:
    locked_contract_path: str
    contract_review_path: str
    contract_id: str
    contract_version: str
    contract_hash: str
    locked_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "locked_contract_path": self.locked_contract_path,
            "contract_review_path": self.contract_review_path,
            "contract_id": self.contract_id,
            "contract_version": self.contract_version,
            "contract_hash": self.contract_hash,
            "locked_at": self.locked_at,
        }


def lock_contracts(
    *,
    reviewed: Iterable[str | Path],
    review_logs: Iterable[str | Path],
    locked_dir: str | Path = "experiments/evidence_contracts/locked",
    contract_review_dir: str | Path = "results/reviews/contracts/locked",
    manifest_id: str,
    manifest_hash: str,
    locked_at: str,
    locked_by: str,
    first_scoring_started_at: str,
    allow_test_mock: bool = False,
) -> list[LockResult]:
    if not locked_by:
        raise ContractLifecycleError("locked_by is required")
    workflow_by_key = _workflow_index(review_logs)
    results: list[LockResult] = []
    for reviewed_path in iter_json_files(reviewed):
        contract = load_mapping(reviewed_path)
        if contract.get("schema_version") != "evidence_contract/v1":
            raise ContractLifecycleError(f"{reviewed_path} is not an evidence_contract/v1 contract")
        if contract.get("contract_status") != "reviewed":
            raise ContractLifecycleError(f"{reviewed_path} must be reviewed before lock")
        key = (str(contract["contract_id"]), str(contract["contract_version"]))
        workflow = workflow_by_key.get(key)
        if workflow is None:
            raise ContractLifecycleError(f"missing review workflow for {key[0]}:{key[1]}")
        _check_native_aligned_support(contract)
        timing = review_timing(
            review_started_at=str(workflow["review_started_at"]),
            review_finished_at=str(workflow["review_finished_at"]),
            locked_at=locked_at,
            first_scoring_started_at=first_scoring_started_at,
        )
        if not allow_test_mock:
            _check_formal_draft_source(contract)
        locked = dict(contract)
        locked["contract_status"] = "locked"
        locked["locked_at"] = locked_at
        locked["locked_by"] = locked_by
        locked["manifest_hash"] = manifest_hash
        locked["main_result_eligible"] = locked.get("claim_scope") == "native_aligned"
        locked["manifest_contract_lock_ref"] = f"{manifest_id}:{locked['contract_id']}:{locked['contract_version']}"
        out_path = resolve_repo_path(locked_dir) / contract_output_name(locked)
        locked["canonical_hash_source"] = display_path(out_path)
        stamp_contract_hash(locked)
        validate_object("evidence_contract", locked, raise_on_error=True)
        write_json(out_path, locked)

        review_record = _contract_review_record(
            locked,
            workflow,
            locked_at=locked_at,
            locked_by=locked_by,
            first_scoring_started_at=first_scoring_started_at,
            duration=timing.duration_minutes,
        )
        validate_object("contract_review", review_record, raise_on_error=True)
        review_path = resolve_repo_path(contract_review_dir) / f"{review_record['review_id']}.json"
        write_json(review_path, review_record)

        results.append(
            LockResult(
                locked_contract_path=display_path(out_path),
                contract_review_path=display_path(review_path),
                contract_id=locked["contract_id"],
                contract_version=locked["contract_version"],
                contract_hash=locked["contract_hash"],
                locked_at=locked_at,
            )
        )
    return results


def _workflow_index(paths: Iterable[str | Path]) -> dict[tuple[str, str], Mapping[str, Any]]:
    index: dict[tuple[str, str], Mapping[str, Any]] = {}
    for path in iter_json_files(paths):
        workflow = load_mapping(path)
        if workflow.get("schema_version") != "contract_review_workflow/v1":
            continue
        key = (str(workflow.get("contract_id")), str(workflow.get("contract_version")))
        index[key] = workflow
    return index


def _check_native_aligned_support(contract: Mapping[str, Any]) -> None:
    if contract.get("claim_scope") != "native_aligned":
        if contract.get("stronger_measurement_mapping") is None:
            raise ContractLifecycleError("non-native-aligned contracts require stronger_measurement mapping before lock")
        return
    unsupported = [
        artifact.get("artifact_id")
        for artifact in contract.get("required_artifacts", [])
        if isinstance(artifact, Mapping) and artifact.get("native_aligned_source_support") is not True
    ]
    if unsupported:
        raise ContractLifecycleError(
            "native-aligned unsupported requirements must be removed or marked stronger_measurement before lock: "
            + ", ".join(str(item) for item in unsupported)
        )


def _check_formal_draft_source(contract: Mapping[str, Any]) -> None:
    support = contract.get("source_support")
    if not isinstance(support, Mapping):
        return
    if support.get("draft_transport") == "test_only_mock" or support.get("formal_draft_eligible") is False:
        raise ContractLifecycleError(
            "test-only mock contract drafts cannot be locked for formal use; "
            "use allow_test_mock only for lifecycle tests"
        )


def _contract_review_record(
    locked: Mapping[str, Any],
    workflow: Mapping[str, Any],
    *,
    locked_at: str,
    locked_by: str,
    first_scoring_started_at: str,
    duration: float,
) -> dict[str, Any]:
    return {
        "schema_version": "contract_review/v1",
        "review_id": workflow["review_id"],
        "contract_id": locked["contract_id"],
        "contract_version": locked["contract_version"],
        "domain": locked["domain"],
        "case_unit_id": locked["case_unit_id"],
        "review_started_at": workflow["review_started_at"],
        "review_finished_at": workflow["review_finished_at"],
        "duration_minutes": duration,
        "reviewer_id": workflow["reviewer_id"],
        "source_bundle_hash": workflow["source_bundle_hash"],
        "visible_input_hash": workflow["visible_input_hash"],
        "review_actions": workflow["review_actions"],
        "source_hierarchy_applied": workflow["source_hierarchy_applied"],
        "unsupported_requirements_removed": workflow["unsupported_requirements_removed"],
        "requirements_marked_stronger_measurement": workflow["requirements_marked_stronger_measurement"],
        "final_lock_decision": "lock",
        "contract_hash": locked["contract_hash"],
        "manifest_hash": locked["manifest_hash"],
        "contract_drafting_llm_call_id": locked["contract_drafting_llm_call_id"],
        "contract_draft_id": locked["contract_draft_id"],
        "draft_created_at": workflow["draft_created_at"],
        "locked_at": locked_at,
        "locked_by": locked_by,
        "first_scoring_started_at": first_scoring_started_at,
    }
