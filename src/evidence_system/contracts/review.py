"""Human review staging for draft evidence contracts."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evidence_system.contracts.common import (
    ContractLifecycleError,
    contract_content_hash,
    contract_output_name,
    display_path,
    hash_path_if_exists,
    iter_json_files,
    load_mapping,
    stamp_contract_hash,
    write_json,
)
from evidence_system.contracts.review_time import review_timing
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import validate_object


@dataclass(frozen=True)
class ReviewResult:
    reviewed_contract_path: str
    review_workflow_path: str
    human_time_path: str
    review_id: str
    contract_id: str
    contract_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "reviewed_contract_path": self.reviewed_contract_path,
            "review_workflow_path": self.review_workflow_path,
            "human_time_path": self.human_time_path,
            "review_id": self.review_id,
            "contract_id": self.contract_id,
            "contract_version": self.contract_version,
        }


def review_contracts(
    *,
    drafts: Iterable[str | Path],
    reviewed_dir: str | Path = "experiments/evidence_contracts/reviewed",
    review_log_dir: str | Path = "results/reviews/contracts",
    human_time_dir: str | Path = "results/human_time/contracts",
    reviewer_id: str,
    review_started_at: str,
    review_finished_at: str,
    review_actions: Sequence[str],
    source_bundle_hash: str | None = None,
    visible_input_hash: str | None = None,
    source_hierarchy_applied: Sequence[str] | None = None,
    unsupported_requirements_removed: bool = False,
    requirements_marked_stronger_measurement: Sequence[str] | None = None,
    draft_created_at: str | None = None,
    phase: str = "dry_run",
    counts_for_cost_table: bool = True,
) -> list[ReviewResult]:
    if not reviewer_id:
        raise ContractLifecycleError("reviewer_id is required")
    if not review_actions:
        raise ContractLifecycleError("at least one review action is required")
    timing = review_timing(
        review_started_at=review_started_at,
        review_finished_at=review_finished_at,
    )
    hierarchy = list(source_hierarchy_applied or [
        "official evaluator semantics",
        "official task text / policy",
        "schema constraints needed to interpret evaluator-visible state",
    ])
    stronger = list(requirements_marked_stronger_measurement or [])
    results: list[ReviewResult] = []
    for draft_path in iter_json_files(drafts):
        draft = load_mapping(draft_path)
        if draft.get("schema_version") != "evidence_contract/v1":
            raise ContractLifecycleError(f"{draft_path} is not an evidence_contract/v1 draft")
        if draft.get("contract_status") not in {"draft", "reviewed"}:
            raise ContractLifecycleError(f"{draft_path} must be draft or reviewed before review staging")
        reviewed = dict(draft)
        review_id = f"review-{reviewed['contract_id']}-{reviewed['contract_version']}"
        reviewed["contract_status"] = "reviewed"
        reviewed["review_record_id"] = review_id
        reviewed["main_result_eligible"] = False
        out_path = resolve_repo_path(reviewed_dir) / contract_output_name(reviewed)
        reviewed["canonical_hash_source"] = display_path(out_path)
        reviewed["manifest_contract_lock_ref"] = f"pending-lock:{reviewed['contract_id']}:{reviewed['contract_version']}"
        stamp_contract_hash(reviewed)
        validate_object("evidence_contract", reviewed, raise_on_error=True)
        write_json(out_path, reviewed)

        workflow = {
            "schema_version": "contract_review_workflow/v1",
            "review_id": review_id,
            "contract_id": reviewed["contract_id"],
            "contract_version": reviewed["contract_version"],
            "domain": reviewed["domain"],
            "case_unit_id": reviewed["case_unit_id"],
            "review_started_at": review_started_at,
            "review_finished_at": review_finished_at,
            "duration_minutes": timing.duration_minutes,
            "reviewer_id": reviewer_id,
            "source_bundle_hash": source_bundle_hash or _source_support_hash(reviewed, "source_bundle_hash"),
            "visible_input_hash": visible_input_hash or _source_support_hash(reviewed, "visible_input_hash"),
            "review_actions": list(review_actions),
            "source_hierarchy_applied": hierarchy,
            "unsupported_requirements_removed": unsupported_requirements_removed,
            "requirements_marked_stronger_measurement": stronger,
            "final_lock_decision": "lock",
            "contract_hash_at_review": reviewed["contract_hash"],
            "contract_drafting_llm_call_id": reviewed["contract_drafting_llm_call_id"],
            "contract_draft_id": reviewed["contract_draft_id"],
            "draft_created_at": draft_created_at or review_started_at,
            "draft_path": display_path(draft_path),
            "reviewed_contract_path": display_path(out_path),
        }
        workflow_path = resolve_repo_path(review_log_dir) / f"{review_id}.workflow.json"
        write_json(workflow_path, workflow)

        human_time = _human_time_record(
            reviewed,
            workflow,
            human_time_dir=human_time_dir,
            reviewer_id=reviewer_id,
            review_started_at=review_started_at,
            review_finished_at=review_finished_at,
            duration=timing.duration_minutes,
            source_artifacts=[display_path(draft_path), display_path(out_path), display_path(workflow_path)],
            phase=phase,
            counts_for_cost_table=counts_for_cost_table,
        )
        validate_object("human_time", human_time, raise_on_error=True)
        human_time_path = resolve_repo_path(human_time_dir) / f"human-time-{review_id}.json"
        write_json(human_time_path, human_time)

        results.append(
            ReviewResult(
                reviewed_contract_path=display_path(out_path),
                review_workflow_path=display_path(workflow_path),
                human_time_path=display_path(human_time_path),
                review_id=review_id,
                contract_id=reviewed["contract_id"],
                contract_version=reviewed["contract_version"],
            )
        )
    return results


def _source_support_hash(contract: Mapping[str, Any], key: str) -> str:
    support = contract.get("source_support")
    if isinstance(support, Mapping):
        value = support.get(key)
        if isinstance(value, str) and value:
            return value
    return "0" * 64


def _human_time_record(
    contract: Mapping[str, Any],
    workflow: Mapping[str, Any],
    *,
    human_time_dir: str | Path,
    reviewer_id: str,
    review_started_at: str,
    review_finished_at: str,
    duration: float,
    source_artifacts: list[str],
    phase: str,
    counts_for_cost_table: bool,
) -> dict[str, Any]:
    return {
        "schema_version": "human_time/v1",
        "activity_id": f"human-time-{workflow['review_id']}",
        "reviewer_or_worker_id": reviewer_id,
        "role": "adapter_author",
        "activity_type": "contract_draft_review",
        "started_at": review_started_at,
        "finished_at": review_finished_at,
        "duration_minutes": duration,
        "action": "; ".join(str(action) for action in workflow.get("review_actions", [])),
        "source_artifacts": source_artifacts,
        "phase": phase,
        "experiment_type": "main",
        "priority": "P0",
        "manifest_hash": str(contract.get("manifest_hash") or "0" * 64),
        "counts_for_cost_table": counts_for_cost_table,
        "no_llm_cost_included": True,
        "no_vps_cost_included": True,
        "no_cloud_bill_included": True,
        "no_benchmark_execution_compute_included": True,
        "no_local_machine_runtime_included": True,
        "domain": contract.get("domain"),
        "case_unit_id": contract.get("case_unit_id"),
        "record_id": None,
        "contract_hash": contract_content_hash(contract),
        "notes": "Contract draft review time; no LLM/VPS/cloud/benchmark compute included.",
    }
