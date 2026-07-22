#!/usr/bin/env python3
"""Natively validate the repair-aware canonical draft/contract/run freeze.

The validator recomputes every file/self/tree hash, origin and repair-provenance
relationship, root-agent/semantic-review handoff, 116 case locks, 348 slots,
and runtime/config eligibility relationship.  It neither patches the manifest
nor accepts fields added after a weaker legacy promotion.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from repair_pipeline_common import (
    EXPECTED_CASE_COUNT,
    REPO_ROOT,
    WORK_ROOT,
    RepairPipelineError,
    load_json,
    object_sha256,
    resolve_repo_path,
    sha256_file,
    verify_file_binding,
    verify_internal_hash,
)
from semantic_review_common import SemanticReviewError, verify_self_hash
from repair_aware_final_common import (
    AGENTS,
    AGENTS_CONFIG,
    CANDIDATE_MANIFEST,
    INFRA_CONFIG,
    INPUT_FREEZE,
    PACKET_INDEX,
    RUNTIME_PREFLIGHT,
    SLOT_COUNT,
    SLOT_LEDGER,
    STATIC_ACCEPTANCE,
    STATIC_VALIDATION,
    load_packet_index,
    load_slot_ledger,
    publication_commit_contract,
    read_jsonl,
    resolved_agent_configuration_bindings,
    runtime_state,
    tree_descriptor,
    verify_handoff,
    verify_legacy_self_hash,
    verify_self_hashed_row,
    verify_static_acceptance_inputs,
)


SCRIPT = Path(__file__).resolve()
PROMOTER = WORK_ROOT / "scripts" / "promote_repair_aware_final_run.py"
DEFAULT_MANIFEST = WORK_ROOT / "manifests" / "androidworld_candidate116_final_run_manifest.json"
DEFAULT_FREEZE = WORK_ROOT / "freeze" / "androidworld_candidate116_contracts_drafts_freeze.json"
DEFAULT_LOCKS = WORK_ROOT / "locks" / "androidworld_candidate116_cases.jsonl"
DEFAULT_REPORT = WORK_ROOT / "validation" / "androidworld_candidate116_promotion_report.json"
CANONICAL_DRAFTS = WORK_ROOT / "drafts"
CANONICAL_CONTRACTS = WORK_ROOT / "contracts" / "drafts"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--freeze", type=Path, default=DEFAULT_FREEZE)
    parser.add_argument("--case-locks", type=Path, default=DEFAULT_LOCKS)
    parser.add_argument("--promotion-report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def require_binding_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise RepairPipelineError(f"{label} binding differs")


def verify_tree(root: Path, declared: Mapping[str, Any], label: str) -> None:
    observed = tree_descriptor(root, root)
    expected_path = root.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    if (
        declared.get("path") != expected_path
        or declared.get("file_count") != observed["file_count"]
        or declared.get("tree_sha256") != observed["tree_sha256"]
        or declared.get("files") != observed["files"]
    ):
        raise RepairPipelineError(f"{label} tree hash/count/files differ")


def verify_case_bundle(
    case: Mapping[str, Any],
    handoff_row: Mapping[str, Any],
    lock: Mapping[str, Any],
) -> None:
    case_id = str(case["case_unit_id"])
    verify_self_hashed_row(case, "case_binding_sha256", f"{case_id} case binding")
    verify_self_hash(lock, "case_lock_sha256", f"{case_id} case lock")
    expected_identity = {
        "case_unit_id": case_id,
        "task_id": handoff_row["task_id"],
        "selection_rank": handoff_row["selection_rank"],
        "group": handoff_row["group"],
        "origin": handoff_row["origin"],
    }
    for key, expected in expected_identity.items():
        if case.get(key) != expected or lock.get(key) != expected:
            raise RepairPipelineError(f"{case_id} {key} differs across handoff/case/lock")
    if (
        case.get("case_handoff_sha256") != handoff_row.get("case_handoff_sha256")
        or lock.get("case_binding_sha256") != case.get("case_binding_sha256")
        or lock.get("packet") != case.get("packet")
        or lock.get("effective_origin") != case.get("effective_origin")
        or lock.get("repair_provenance") != case.get("repair_provenance")
        or lock.get("source_review_chain") != case.get("source_review_chain")
        or lock.get("canonical_draft") != case.get("canonical_draft")
        or lock.get("canonical_contract_draft") != case.get("canonical_contract_draft")
    ):
        raise RepairPipelineError(f"{case_id} case lock does not lock the complete case binding")

    draft = case.get("canonical_draft") or {}
    contract = case.get("canonical_contract_draft") or {}
    if not draft or set(draft) != set(contract):
        raise RepairPipelineError(f"{case_id} canonical draft/contract file sets differ")
    draft_dir = CANONICAL_DRAFTS / case_id
    contract_dir = CANONICAL_CONTRACTS / case_id
    observed_draft_names = {path.name for path in draft_dir.iterdir() if path.is_file()}
    observed_contract_names = {path.name for path in contract_dir.iterdir() if path.is_file()}
    bound_draft_names: set[str] = set()
    bound_contract_names: set[str] = set()
    for key in sorted(draft):
        draft_path = verify_file_binding(draft[key], f"{case_id} canonical draft {key}")
        contract_path = verify_file_binding(contract[key], f"{case_id} canonical contract {key}")
        if draft_path.parent != draft_dir.resolve() or contract_path.parent != contract_dir.resolve():
            raise RepairPipelineError(f"{case_id} canonical bundle binding escapes its case directory")
        bound_draft_names.add(draft_path.name)
        bound_contract_names.add(contract_path.name)
        if sha256_file(draft_path) != sha256_file(contract_path) or draft_path.stat().st_size != contract_path.stat().st_size:
            raise RepairPipelineError(f"{case_id} canonical draft/contract bytes differ for {key}")
    if observed_draft_names != bound_draft_names or observed_contract_names != bound_contract_names:
        raise RepairPipelineError(f"{case_id} canonical bundle has unbound/missing files")

    checklist_draft = verify_file_binding(draft["checklist_yaml"], f"{case_id} checklist")
    checklist_contract = verify_file_binding(contract["checklist_yaml"], f"{case_id} contract checklist")
    if (
        sha256_file(checklist_draft) != handoff_row["effective_checklist_yaml"]["sha256"]
        or sha256_file(checklist_contract) != handoff_row["effective_checklist_yaml"]["sha256"]
    ):
        raise RepairPipelineError(f"{case_id} canonical checklist differs from effective handoff")
    source_mapping = {
        "llm_call_json": "llm_call_json",
        "api_response_json": "api_response_json",
        "reasoning_summary_txt": "reasoning_summary_txt",
        "stdout_log": "stdout_log",
        "stderr_log": "stderr_log",
    }
    for canonical_key, source_key in source_mapping.items():
        if draft[canonical_key]["sha256"] != handoff_row["draft_sidecars"][source_key]["sha256"]:
            raise RepairPipelineError(f"{case_id} canonical {canonical_key} differs from effective source")
    expected_source_bindings = {
        "effective_qc": handoff_row["effective_qc"],
        "semantic_proposal": handoff_row["semantic_proposal"],
        "semantic_result": handoff_row["semantic_result"],
        "semantic_receipt": handoff_row["semantic_receipt"],
        "root_agent_verdict": handoff_row["root_agent_verdict"],
        "root_agent_review": handoff_row["root_agent_review"],
    }
    if case.get("source_review_chain") != expected_source_bindings:
        raise RepairPipelineError(f"{case_id} source-review chain differs from handoff")
    for canonical_key, source_key in (
        ("automatic_qc_report_json", "effective_qc"),
        ("semantic_proposal_json", "semantic_proposal"),
        ("semantic_result_json", "semantic_result"),
        ("semantic_receipt_json", "semantic_receipt"),
        ("root_agent_verdict_json", "root_agent_verdict"),
        ("review_json", "root_agent_review"),
        ("effective_origin_json", "effective_origin"),
    ):
        if draft[canonical_key]["sha256"] != handoff_row[source_key]["sha256"]:
            raise RepairPipelineError(f"{case_id} canonical {canonical_key} differs from handoff")
    if handoff_row["origin"] == "repair":
        if (
            "repair_provenance_json" not in draft
            or draft["repair_provenance_json"]["sha256"]
            != handoff_row["repair_provenance"]["sha256"]
        ):
            raise RepairPipelineError(f"{case_id} repair provenance is not canonically bound")
    elif "repair_provenance_json" in draft or handoff_row["repair_provenance"] is not None:
        raise RepairPipelineError(f"{case_id} retained case has canonical repair provenance")

    provenance_path = verify_file_binding(draft["provenance_json"], f"{case_id} provenance")
    provenance = load_json(provenance_path, f"{case_id} canonical provenance")
    verify_self_hash(provenance, "provenance_sha256", f"{case_id} canonical provenance")
    if (
        provenance.get("provenance_sha256") != case.get("provenance_sha256")
        or provenance.get("case_handoff_sha256") != handoff_row.get("case_handoff_sha256")
        or provenance.get("origin") != handoff_row.get("origin")
        or (provenance.get("source_bindings") or {}).get("full_packet")
        != handoff_row.get("full_packet")
        or (provenance.get("source_bindings") or {}).get("repair_provenance")
        != handoff_row.get("repair_provenance")
        or provenance.get("handoff") != lock.get("handoff")
    ):
        raise RepairPipelineError(f"{case_id} canonical provenance differs from handoff")
    contract_provenance = load_json(
        verify_file_binding(contract["provenance_json"], f"{case_id} contract provenance")
    )
    if contract_provenance != provenance:
        raise RepairPipelineError(f"{case_id} draft/contract provenance differs")


def validate(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = args.manifest.resolve()
    freeze_path = args.freeze.resolve()
    locks_path = args.case_locks.resolve()
    report_path = args.promotion_report.resolve()
    if (
        manifest_path != DEFAULT_MANIFEST.resolve()
        or freeze_path != DEFAULT_FREEZE.resolve()
        or locks_path != DEFAULT_LOCKS.resolve()
        or report_path != DEFAULT_REPORT.resolve()
    ):
        raise RepairPipelineError("native final validation only accepts canonical publication paths")
    manifest = load_json(manifest_path, "repair-aware final run manifest")
    if manifest.get("schema_version") != "androidworld_candidate116_repair_aware_final_run_manifest/v1":
        raise RepairPipelineError("final manifest is not the native repair-aware schema")
    verify_self_hash(manifest, "manifest_sha256", "repair-aware final run manifest")
    if (
        manifest.get("case_count") != EXPECTED_CASE_COUNT
        or manifest.get("agent_count") != len(AGENTS)
        or manifest.get("record_slot_count") != SLOT_COUNT
        or manifest.get("scoring_eligible") is not False
    ):
        raise RepairPipelineError("final manifest counts/scoring gate are invalid")
    if manifest.get("publication") != publication_commit_contract(commit_marker=True):
        raise RepairPipelineError("final manifest is not the create-once publication commit marker")
    handoff_path = verify_file_binding(
        manifest.get("promotion_handoff"), "manifest promotion handoff", inside_candidate=True
    )
    context = verify_handoff(handoff_path)
    verify_static_acceptance_inputs()
    if manifest["promotion_handoff"].get("handoff_sha256") != context["handoff"].get(
        "handoff_sha256"
    ):
        raise RepairPipelineError("manifest handoff internal hash differs")
    concurrency_evidence = context["repair_concurrency_evidence"]
    concurrency_audit = concurrency_evidence["summary"]
    concurrency_samples = concurrency_evidence["samples"]
    if (
        manifest.get("repair_concurrency_evidence") != concurrency_evidence
        or manifest.get("repair_concurrency_audit") != concurrency_audit
        or manifest.get("repair_concurrency_samples") != concurrency_samples
    ):
        raise RepairPipelineError(
            "final manifest repair concurrency evidence/aliases differ from raw revalidation"
        )
    order = context["order"]
    packet_index, packet_by_case = load_packet_index(order)
    input_freeze = load_json(INPUT_FREEZE, "candidate116 packet/source input freeze")
    verify_legacy_self_hash(input_freeze, "freeze_sha256", "candidate116 input freeze")
    ledger, base_slots = load_slot_ledger(order)

    freeze_bound = verify_file_binding(
        manifest.get("contracts_drafts_freeze"), "contracts/drafts freeze", inside_candidate=True
    )
    if freeze_bound != freeze_path:
        raise RepairPipelineError("manifest points to a different contracts/drafts freeze")
    freeze = load_json(freeze_path, "repair-aware contracts/drafts freeze")
    if freeze.get("schema_version") != "androidworld_repair_aware_contracts_drafts_freeze/v1":
        raise RepairPipelineError("contracts/drafts freeze is not repair aware")
    verify_self_hash(freeze, "freeze_sha256", "repair-aware contracts/drafts freeze")
    if (
        freeze.get("freeze_sha256") != manifest["contracts_drafts_freeze"].get("freeze_sha256")
        or freeze.get("case_count") != EXPECTED_CASE_COUNT
        or freeze.get("case_order") != order
        or freeze.get("case_order_sha256") != context["handoff"]["case_order_sha256"]
        or freeze.get("cases_sha256") != object_sha256(freeze.get("cases") or [])
        or freeze.get("repair_concurrency_evidence") != concurrency_evidence
        or freeze.get("repair_concurrency_audit") != concurrency_audit
        or freeze.get("repair_concurrency_samples") != concurrency_samples
        or freeze.get("publication") != publication_commit_contract(commit_marker=False)
    ):
        raise RepairPipelineError("contracts/drafts freeze identity/case index is invalid")

    locks = read_jsonl(locks_path)
    if len(locks) != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("case-lock JSONL does not contain exactly 116 locks")
    external = freeze.get("external_case_locks") or {}
    if (
        manifest.get("external_case_locks") != external
        or external.get("path") != locks_path.relative_to(REPO_ROOT.resolve()).as_posix()
        or external.get("sha256") != sha256_file(locks_path)
        or external.get("size_bytes") != locks_path.stat().st_size
        or external.get("count") != EXPECTED_CASE_COUNT
        or external.get("ordered_case_lock_hashes_sha256")
        != object_sha256([row.get("case_lock_sha256") for row in locks])
    ):
        raise RepairPipelineError("external case-lock binding/count/hash is invalid")

    cases = list(manifest.get("cases") or [])
    freeze_cases = list(freeze.get("cases") or [])
    if (
        len(cases) != EXPECTED_CASE_COUNT
        or manifest.get("cases_sha256") != object_sha256(cases)
        or freeze_cases != cases
        or freeze.get("cases_sha256") != manifest.get("cases_sha256")
    ):
        raise RepairPipelineError("manifest/freeze canonical case indexes differ")
    for rank, (case_id, case, handoff_row, lock) in enumerate(
        zip(order, cases, context["rows"], locks, strict=True)
    ):
        if case.get("selection_rank") != rank or case.get("case_unit_id") != case_id:
            raise RepairPipelineError(f"canonical case order differs at {case_id}")
        packet = packet_by_case[case_id]
        if (
            case.get("packet") != handoff_row.get("full_packet")
            or case["packet"].get("path") != packet.get("case_packet_path")
            or case["packet"].get("sha256") != packet.get("case_packet_sha256")
        ):
            raise RepairPipelineError(f"{case_id} canonical packet differs from packet index/handoff")
        verify_case_bundle(case, handoff_row, lock)

    verify_tree(CANONICAL_DRAFTS, freeze["canonical_drafts_tree"], "canonical drafts")
    verify_tree(
        CANONICAL_CONTRACTS,
        freeze["canonical_contracts_drafts_tree"],
        "canonical contract drafts",
    )
    if freeze["canonical_drafts_tree"]["files"] != freeze[
        "canonical_contracts_drafts_tree"
    ]["files"]:
        raise RepairPipelineError("canonical draft/contract tree file bindings differ")

    slots = list(manifest.get("slots") or [])
    if len(slots) != SLOT_COUNT or manifest.get("slots_sha256") != object_sha256(slots):
        raise RepairPipelineError("manifest slot index/hash is invalid")
    lock_by_case = {row["case_unit_id"]: row for row in locks}
    case_by_id = {row["case_unit_id"]: row for row in cases}
    agent_configurations = resolved_agent_configuration_bindings()
    for base, slot in zip(base_slots, slots, strict=True):
        for key, value in base.items():
            if slot.get(key) != value:
                raise RepairPipelineError(f"slot {base['record_slot_id']} base field {key} differs")
        case = case_by_id[base["case_unit_id"]]
        lock = lock_by_case[base["case_unit_id"]]
        agent_id = base["agent_id"]
        expected_agent_configuration = agent_configurations[agent_id]
        expected_runtime_configuration = {
            "runtime_bindings_sha256": (manifest.get("runtime") or {}).get(
                "runtime_bindings_sha256"
            ),
            "configuration_bindings_sha256": object_sha256(
                (manifest.get("runtime") or {}).get("configuration_bindings") or {}
            ),
            "execution_eligible": (manifest.get("runtime") or {}).get(
                "execution_eligible"
            ),
            "scoring_eligible": (manifest.get("runtime") or {}).get("scoring_eligible"),
        }
        if (
            slot.get("case_lock_sha256") != lock.get("case_lock_sha256")
            or slot.get("packet") != case["packet"]
            or slot.get("packet_sha256") != case["packet"]["sha256"]
            or slot.get("draft") != case["canonical_draft"]["checklist_yaml"]
            or slot.get("draft_sha256") != case["canonical_draft"]["checklist_yaml"]["sha256"]
            or slot.get("contract_draft")
            != case["canonical_contract_draft"]["checklist_yaml"]
            or slot.get("contract_draft_sha256")
            != case["canonical_contract_draft"]["checklist_yaml"]["sha256"]
            or slot.get("agent_configuration") != expected_agent_configuration
            or slot.get("infra_config_sha256") != sha256_file(INFRA_CONFIG)
            or slot.get("runtime_bindings_sha256")
            != (manifest.get("runtime") or {}).get("runtime_bindings_sha256")
            or slot.get("runtime_configuration") != expected_runtime_configuration
        ):
            raise RepairPipelineError(f"slot {base['record_slot_id']} frozen bindings differ")
    slot_binding_path = verify_file_binding(manifest.get("slot_ledger"), "slot ledger", inside_candidate=True)
    if (
        slot_binding_path != SLOT_LEDGER.resolve()
        or manifest["slot_ledger"].get("record_slot_ids_hash")
        != ledger.get("record_slot_ids_hash")
    ):
        raise RepairPipelineError("manifest slot-ledger binding differs")

    runtime = manifest.get("runtime") or {}
    custom_binding = (runtime.get("configuration_bindings") or {}).get("custom_execution")
    custom_path = (
        resolve_repo_path(custom_binding.get("path"), inside_candidate=False)
        if isinstance(custom_binding, Mapping)
        else None
    )
    expected_runtime, eligible = runtime_state(custom_path)
    if runtime != expected_runtime:
        raise RepairPipelineError("manifest runtime/config binding differs from current bound bytes/state")
    expected_status = "locked_ready_for_execution" if eligible else "locked_inputs_runtime_preflight_pending"
    if (
        manifest.get("execution_eligible") is not eligible
        or manifest.get("scoring_eligible") is not False
        or manifest.get("status") != expected_status
        or freeze.get("runtime") != runtime
    ):
        raise RepairPipelineError("runtime preflight/config eligibility propagation is invalid")
    if load_json(RUNTIME_PREFLIGHT).get("status") == "blocked" and (
        manifest.get("execution_eligible") is not False
        or manifest.get("scoring_eligible") is not False
    ):
        raise RepairPipelineError("blocked runtime preflight was promoted as eligible")

    exact_bindings = (
        ("packet_source_input_freeze", INPUT_FREEZE),
        ("packet_index", PACKET_INDEX),
        ("effective_manifest", context["manifest_path"]),
        ("repair_prelock", context["repair_prelock_path"]),
        ("effective_qc_summary", context["qc_summary_path"]),
        ("semantic_review_prelock", context["semantic_prelock_path"]),
        ("independent_semantic_validation", context["validation_path"]),
        ("external_root_agent_verdict_index", context["verdict_index_path"]),
        ("root_agent_review_summary", context["review_summary_path"]),
        ("strict_static_acceptance", STATIC_ACCEPTANCE),
        ("semantic_static_validation", STATIC_VALIDATION),
    )
    for key, expected_path in exact_bindings:
        path = verify_file_binding(manifest.get(key), f"manifest {key}", inside_candidate=True)
        if path != expected_path.resolve() or freeze.get(key) != manifest.get(key):
            raise RepairPipelineError(f"manifest/freeze {key} binding differs")
    experiment = verify_file_binding(
        manifest.get("experiment_scope_manifest"), "experiment scope manifest", inside_candidate=True
    )
    if experiment != CANDIDATE_MANIFEST.resolve():
        raise RepairPipelineError("experiment scope manifest differs")
    tools = manifest.get("tool_bindings") or {}
    if (
        verify_file_binding(
            tools.get("repair_aware_promotion_builder"), "repair-aware promoter", inside_candidate=True
        )
        != PROMOTER.resolve()
        or verify_file_binding(
            tools.get("repair_aware_independent_validator"),
            "repair-aware validator",
            inside_candidate=True,
        )
        != SCRIPT
        or verify_file_binding(
            tools.get("repair_aware_final_common"),
            "repair-aware final common",
            inside_candidate=True,
        )
        != (WORK_ROOT / "scripts" / "repair_aware_final_common.py").resolve()
        or verify_file_binding(
            tools.get("repair_concurrency_verifier"),
            "repair concurrency verifier",
            inside_candidate=True,
        )
        != (WORK_ROOT / "scripts" / "repair_pipeline_common.py").resolve()
    ):
        raise RepairPipelineError("manifest tool bindings do not bind native promoter/validator")

    report = load_json(report_path, "repair-aware promotion report")
    verify_self_hash(report, "report_sha256", "repair-aware promotion report")
    report_manifest_path = verify_file_binding(
        report.get("final_run_manifest"), "promotion report final manifest", inside_candidate=True
    )
    report_freeze_path = verify_file_binding(
        report.get("contracts_drafts_freeze"),
        "promotion report contracts/drafts freeze",
        inside_candidate=True,
    )
    if (
        report.get("status") != "pass"
        or report.get("case_count") != EXPECTED_CASE_COUNT
        or report.get("slot_count") != SLOT_COUNT
        or report.get("human_review_claimed") is not False
        or report.get("execution_eligible") is not eligible
        or report.get("scoring_eligible") is not False
        or report_manifest_path != manifest_path
        or report_freeze_path != freeze_path
        or (report.get("final_run_manifest") or {}).get("sha256") != sha256_file(manifest_path)
        or (report.get("final_run_manifest") or {}).get("manifest_sha256")
        != manifest.get("manifest_sha256")
        or (report.get("contracts_drafts_freeze") or {}).get("sha256") != sha256_file(freeze_path)
        or report.get("repair_concurrency_evidence") != concurrency_evidence
        or report.get("repair_concurrency_audit") != concurrency_audit
        or report.get("repair_concurrency_samples") != concurrency_samples
        or report.get("publication") != publication_commit_contract(commit_marker=False)
    ):
        raise RepairPipelineError("promotion report does not bind final manifest/freeze")
    return {
        "schema_version": "androidworld_candidate116_repair_aware_final_validation/v1",
        "status": "pass",
        "case_count": EXPECTED_CASE_COUNT,
        "slot_count": SLOT_COUNT,
        "repair_count": context["handoff"]["repair_count"],
        "retain_count": context["handoff"]["retain_count"],
        "execution_eligible": eligible,
        "scoring_eligible": False,
        "manifest_status": manifest["status"],
        "manifest_sha256": manifest["manifest_sha256"],
        "freeze_sha256": freeze["freeze_sha256"],
        "handoff_sha256": context["handoff"]["handoff_sha256"],
        "repair_concurrency_evidence_sha256": concurrency_evidence["evidence_sha256"],
        "reviewer": "Codex/root_agent",
        "human_reviewed": False,
        "issues": [],
    }


def main() -> int:
    args = parse_args()
    if args.self_test:
        sample = {"a": 1}
        sample["row_sha256"] = object_sha256(sample)
        verify_self_hashed_row(sample, "row_sha256", "self-test row")
        tampered = dict(sample)
        tampered["a"] = 2
        rejected = False
        try:
            verify_self_hashed_row(tampered, "row_sha256", "tampered self-test row")
        except RepairPipelineError:
            rejected = True
        runtime, eligible = runtime_state(None)
        if not rejected or runtime.get("scoring_eligible") is not False:
            raise RepairPipelineError("validator negative self-test failed")
        print(
            json.dumps(
                {
                    "status": "self_test_pass",
                    "negative_tampered_hash_rejected": rejected,
                    "runtime_status": runtime["status"],
                    "execution_eligible": eligible,
                    "scoring_eligible": False,
                    "files_written": False,
                },
                indent=2,
            )
        )
        return 0
    result = validate(args)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SemanticReviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
