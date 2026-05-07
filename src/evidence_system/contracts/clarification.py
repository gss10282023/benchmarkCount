"""Post-lock contract clarification records.

Clarifications never edit the main locked contract in place. They create a new
non-main-result contract version under ``superseded/`` for sensitivity reporting.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evidence_system.contracts.common import (
    ContractLifecycleError,
    contract_output_name,
    display_path,
    load_mapping,
    stamp_contract_hash,
    write_json,
)
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import validate_object


@dataclass(frozen=True)
class ClarificationResult:
    clarification_path: str
    contract_id: str
    contract_version: str
    contract_hash: str
    supersedes_contract_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "clarification_path": self.clarification_path,
            "contract_id": self.contract_id,
            "contract_version": self.contract_version,
            "contract_hash": self.contract_hash,
            "supersedes_contract_hash": self.supersedes_contract_hash,
        }


def record_contract_clarification(
    *,
    locked_contract_path: str | Path,
    output_dir: str | Path = "experiments/evidence_contracts/superseded",
    new_version: str,
    sensitivity_report_id: str,
    clarification_note: str,
    locked_by: str,
    locked_at: str,
) -> ClarificationResult:
    if not new_version:
        raise ContractLifecycleError("new_version is required")
    if not sensitivity_report_id:
        raise ContractLifecycleError("sensitivity_report_id is required")
    source = load_mapping(locked_contract_path)
    if source.get("schema_version") != "evidence_contract/v1" or source.get("contract_status") != "locked":
        raise ContractLifecycleError("post-lock clarification source must be a locked evidence_contract/v1")
    if str(new_version) == str(source.get("contract_version")):
        raise ContractLifecycleError("post-lock clarification must use a new contract_version")
    clarification = dict(source)
    clarification["contract_version"] = new_version
    clarification["contract_status"] = "clarification"
    clarification["main_result_eligible"] = False
    clarification["supersedes_contract_id"] = source["contract_id"]
    clarification["supersedes_contract_version"] = source["contract_version"]
    clarification["supersedes_contract_hash"] = source["contract_hash"]
    clarification["sensitivity_report_id"] = sensitivity_report_id
    clarification["locked_by"] = locked_by
    clarification["locked_at"] = locked_at
    support = dict(clarification.get("source_support") or {})
    support["post_lock_clarification_note"] = clarification_note
    clarification["source_support"] = support
    out_path = resolve_repo_path(output_dir) / contract_output_name(clarification)
    clarification["canonical_hash_source"] = display_path(out_path)
    clarification["manifest_contract_lock_ref"] = f"clarification-only:{clarification['contract_id']}:{new_version}"
    stamp_contract_hash(clarification)
    validate_object("evidence_contract", clarification, raise_on_error=True)
    write_json(out_path, clarification)
    return ClarificationResult(
        clarification_path=display_path(out_path),
        contract_id=clarification["contract_id"],
        contract_version=clarification["contract_version"],
        contract_hash=clarification["contract_hash"],
        supersedes_contract_hash=source["contract_hash"],
    )
