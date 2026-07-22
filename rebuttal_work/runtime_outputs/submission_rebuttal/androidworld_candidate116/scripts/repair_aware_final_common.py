#!/usr/bin/env python3
"""Native shared validation primitives for repair-aware final promotion."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from repair_pipeline_common import (
    EXPECTED_CASE_COUNT,
    REPO_ROOT,
    WORK_ROOT,
    RepairPipelineError,
    file_binding,
    load_json,
    load_yaml_mapping,
    object_sha256,
    repo_relative,
    resolve_repo_path,
    sha256_file,
    verify_file_binding,
    verify_internal_hash,
    verify_repair_concurrency_evidence,
)
from semantic_review_common import verify_self_hash


HANDOFF_SCHEMA = "androidworld_repair_aware_promotion_handoff/v2"
SLOT_COUNT = 348
AGENTS = ("Agent A", "Agent B", "Agent C")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
PACKET_INDEX = WORK_ROOT / "indexes" / "androidworld_candidate116_packet_index.json"
SLOT_LEDGER = WORK_ROOT / "ledgers" / "androidworld_candidate116_348_slot_ledger.json"
CANDIDATE_MANIFEST = WORK_ROOT / "manifests" / "androidworld_candidate116_manifest.json"
INPUT_FREEZE = WORK_ROOT / "freeze" / "androidworld_candidate116_draft_input_freeze.json"
STATIC_ACCEPTANCE = WORK_ROOT / "validation" / "strict_acceptance_report.json"
STATIC_VALIDATION = WORK_ROOT / "validation" / "static_validation_report.json"
RUNTIME_PREFLIGHT = WORK_ROOT / "validation" / "runtime_preflight_report.json"
FINAL_MANIFEST_COMMIT_MARKER = (
    WORK_ROOT / "manifests" / "androidworld_candidate116_final_run_manifest.json"
)
AGENTS_CONFIG = REPO_ROOT / "configs" / "agents.yaml"
INFRA_CONFIG = REPO_ROOT / "configs" / "infra.yaml"
PLACEHOLDERS = (
    "需要从 locked manifest 确认",
    "需要从 scored manifest 填充",
    "需要从论文确认",
    "需要从 benchmark 官方 split 确认",
    "<ANDROIDWORLD_INSTALL_ROOT>",
    "<REPO_ROOT>",
    "pending_formal_lock",
    "placeholder",
    "tbd",
    "todo",
)
REVIEW_CHECKS = (
    "identity",
    "schema_guardrails",
    "llm_provenance",
    "support_pointers",
    "user_goal",
    "evaluator_success",
    "fail",
    "undecided",
    "decisive_artifacts",
    "stronger_conditions",
    "metadata_conflict_disposition",
)
SIDECAR_KEYS = {
    "checklist_yaml": "checklist.yaml",
    "checklist_json": "checklist.json",
    "llm_call_json": "llm_call.json",
    "api_response_json": "api_response.json",
    "reasoning_summary_txt": "reasoning_summary.txt",
    "stdout_log": "stdout.log",
    "stderr_log": "stderr.log",
}
ROOT_VERDICT_SCHEMA = "androidworld_root_agent_case_verdict/v1"
ROOT_VERDICT_INDEX_SCHEMA = "androidworld_root_agent_verdict_index/v1"
CUSTOM_RUNTIME_SCHEMA = "androidworld_candidate116_execution_config/v1"
ROOT_VERDICT_EVIDENCE_SOURCES = {
    "packet",
    "effective_checklist_yaml",
    "effective_checklist_json",
    "automatic_qc",
    "effective_origin",
    "repair_provenance",
    "semantic_proposal",
    "semantic_result",
    "semantic_receipt",
    "semantic_review_prelock",
    "independent_validation",
}


def publication_commit_contract(*, commit_marker: bool) -> dict[str, Any]:
    """Describe the logical atomicity rule embedded in every final artifact."""

    contract = {
        "schema_version": "androidworld_candidate116_create_once_publication/v1",
        "commit_marker_path": repo_relative(FINAL_MANIFEST_COMMIT_MARKER),
        "create_once_required": True,
        "final_manifest_is_only_commit_marker": True,
    }
    if commit_marker:
        contract.update(
            {
                "role": "commit_marker",
                "all_precommit_artifact_bindings_required": True,
            }
        )
    else:
        contract.update(
            {
                "role": "precommit_artifact",
                "commit_marker_required_for_validity": True,
                "standalone_artifact_is_uncommitted": True,
            }
        )
    return contract


def verify_binding_tree(value: Any, label: str, *, inside_candidate: bool = True) -> None:
    if isinstance(value, Mapping) and {"path", "sha256", "size_bytes"}.issubset(value):
        verify_file_binding(value, label, inside_candidate=inside_candidate)
        return
    if isinstance(value, Mapping):
        for key, nested in value.items():
            verify_binding_tree(nested, f"{label}.{key}", inside_candidate=inside_candidate)
        return
    if isinstance(value, list):
        for index, nested in enumerate(value):
            verify_binding_tree(nested, f"{label}[{index}]", inside_candidate=inside_candidate)
        return
    raise RepairPipelineError(f"{label} is not a binding tree")


def verify_self_hashed_row(row: Mapping[str, Any], field: str, label: str) -> None:
    claimed = row.get(field)
    core = copy.deepcopy(dict(row))
    core.pop(field, None)
    if not isinstance(claimed, str) or not HASH_RE.fullmatch(claimed) or object_sha256(core) != claimed:
        raise RepairPipelineError(f"{label} {field} differs")


def verify_legacy_self_hash(value: Mapping[str, Any], field: str, label: str) -> None:
    """Verify artifacts built with freeze_and_slots' ensure_ascii=True convention."""
    core = copy.deepcopy(dict(value))
    claimed = core.pop(field, None)
    observed = hashlib.sha256(
        json.dumps(core, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    if not isinstance(claimed, str) or not HASH_RE.fullmatch(claimed) or claimed != observed:
        raise RepairPipelineError(f"{label} {field} differs")


def require_zoned_time(value: Any, label: str) -> str:
    text = str(value or "").strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RepairPipelineError(f"{label} is not ISO-8601") from exc
    if parsed.tzinfo is None:
        raise RepairPipelineError(f"{label} must include a time zone")
    return text


def verify_root_agent_verdict(
    path: Path,
    *,
    case_id: str,
    selection_rank: int,
    expected_bindings: Mapping[str, Any],
) -> dict[str, Any]:
    """Verify one pre-existing evidence-bearing root-agent verdict.

    This function never creates or upgrades a verdict.  In particular, a model
    proposal being accepted is not evidence that the root agent accepted it.
    """
    path = path.resolve()
    try:
        path.relative_to(WORK_ROOT.resolve())
    except ValueError as exc:
        raise RepairPipelineError("root-agent verdict must stay inside candidate116") from exc
    verdict = load_json(path, f"{case_id} external root-agent verdict")
    verify_self_hash(verdict, "verdict_sha256", f"{case_id} external root-agent verdict")
    expected_keys = {
        "schema_version",
        "case_unit_id",
        "task_id",
        "selection_rank",
        "verdict",
        "reviewer",
        "review_authority",
        "human_reviewed",
        "reviewed_at",
        "review_method",
        "authority_attestation",
        "notes",
        "issues",
        "checks",
        "input_bindings",
        "promotion_authorized_by_model_proposal",
        "verdict_sha256",
    }
    if set(verdict) != expected_keys:
        raise RepairPipelineError(f"{case_id} root-agent verdict field set is not exact")
    if (
        verdict.get("schema_version") != ROOT_VERDICT_SCHEMA
        or verdict.get("case_unit_id") != case_id
        or verdict.get("task_id") != case_id
        or verdict.get("selection_rank") != selection_rank
        or verdict.get("verdict") not in {"accepted", "rejected"}
        or verdict.get("reviewer") != "Codex/root_agent"
        or verdict.get("review_authority") != "external_root_agent_case_verdict"
        or verdict.get("human_reviewed") is not False
        or verdict.get("review_method") != "independent_case_by_case_evidence_review"
        or verdict.get("authority_attestation")
        != "I independently inspected this case and take root-agent responsibility for this verdict."
        or verdict.get("promotion_authorized_by_model_proposal") is not False
    ):
        raise RepairPipelineError(f"{case_id} root-agent verdict identity/authority is invalid")
    require_zoned_time(verdict.get("reviewed_at"), f"{case_id} verdict reviewed_at")
    if len(str(verdict.get("notes") or "").strip()) < 20:
        raise RepairPipelineError(f"{case_id} root-agent verdict needs concrete review notes")
    if verdict.get("input_bindings") != dict(expected_bindings):
        raise RepairPipelineError(f"{case_id} root-agent verdict binds different review inputs")
    verify_binding_tree(verdict["input_bindings"], f"{case_id} verdict input")
    checks = verdict.get("checks")
    if not isinstance(checks, Mapping) or set(checks) != set(REVIEW_CHECKS):
        raise RepairPipelineError(f"{case_id} root-agent verdict check set is not exact")
    statuses: list[str] = []
    for name in REVIEW_CHECKS:
        check = checks[name]
        if not isinstance(check, Mapping) or set(check) != {"status", "notes", "evidence"}:
            raise RepairPipelineError(f"{case_id} root-agent check {name} shape is invalid")
        status = check.get("status")
        if status not in {"pass", "fail"}:
            raise RepairPipelineError(f"{case_id} root-agent check {name} has invalid status")
        statuses.append(str(status))
        if len(str(check.get("notes") or "").strip()) < 8:
            raise RepairPipelineError(f"{case_id} root-agent check {name} needs concrete notes")
        evidence = check.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise RepairPipelineError(f"{case_id} root-agent check {name} has no evidence")
        for item in evidence:
            if not isinstance(item, Mapping) or set(item) != {"source", "pointer", "finding"}:
                raise RepairPipelineError(
                    f"{case_id} root-agent check {name} evidence shape is invalid"
                )
            source = str(item.get("source") or "")
            pointer = str(item.get("pointer") or "").strip()
            finding = str(item.get("finding") or "").strip()
            if (
                source not in ROOT_VERDICT_EVIDENCE_SOURCES
                or source not in expected_bindings
                or not re.match(r"^(?:/|line:|section:)", pointer)
                or len(finding) < 8
            ):
                raise RepairPipelineError(
                    f"{case_id} root-agent check {name} has unusable evidence"
                )
    issues = verdict.get("issues")
    if not isinstance(issues, list) or any(not str(item).strip() for item in issues):
        raise RepairPipelineError(f"{case_id} root-agent verdict issues are invalid")
    if verdict["verdict"] == "accepted":
        if any(status != "pass" for status in statuses) or issues:
            raise RepairPipelineError(f"{case_id} accepted root-agent verdict is internally inconsistent")
    elif "fail" not in statuses or not issues:
        raise RepairPipelineError(f"{case_id} rejected root-agent verdict lacks a failed check/issue")
    return verdict


def verify_effective_review_content_address(prelock: Mapping[str, Any]) -> str:
    """Recompute the effective semantic-review input/tool/model content address."""
    effective = prelock.get("effective_generation") or {}
    manifest_path = verify_file_binding(
        effective.get("effective_manifest"), "content-address effective manifest", inside_candidate=True
    )
    manifest = load_json(manifest_path, "content-address effective manifest")
    verify_self_hash(manifest, "effective_manifest_sha256", "content-address effective manifest")
    qc_path = verify_file_binding(
        prelock.get("automatic_qc_summary"), "content-address effective QC", inside_candidate=True
    )
    qc = load_json(qc_path, "content-address effective QC")
    verify_self_hash(qc, "summary_sha256", "content-address effective QC")
    source_path = verify_file_binding(
        effective.get("source_draft_prelock"),
        "content-address source draft prelock",
        inside_candidate=True,
    )
    source = load_json(source_path, "content-address source draft prelock")
    verify_self_hash(source, "prelock_sha256", "content-address source draft prelock")
    concurrency_evidence = effective.get("repair_concurrency_evidence")
    if not isinstance(concurrency_evidence, Mapping):
        raise RepairPipelineError("semantic-review prelock lacks repair concurrency evidence")
    verify_self_hash(
        concurrency_evidence,
        "evidence_sha256",
        "content-address repair concurrency evidence",
    )
    if (
        concurrency_evidence != manifest.get("repair_concurrency_evidence")
        or concurrency_evidence != qc.get("repair_concurrency_evidence")
    ):
        raise RepairPipelineError(
            "repair concurrency evidence differs across semantic prelock/manifest/QC"
        )
    config_path = verify_file_binding(
        prelock.get("review_config"), "content-address review config", inside_candidate=True
    )
    config = load_json(config_path, "content-address review config")
    verify_self_hash(config, "config_sha256", "content-address review config")
    tools = prelock.get("tool_bindings") or {}
    required = (
        "common",
        "prelock_builder",
        "batch_runner",
        "independent_validator",
        "review_prompt",
        "proposal_schema",
        "checklist_schema",
    )
    if any(name not in tools for name in required):
        raise RepairPipelineError("semantic-review prelock lacks a content-address tool role")
    for name in required:
        verify_file_binding(tools[name], f"content-address tool {name}", inside_candidate=True)
    codex = prelock.get("codex_cli") or {}
    payload = {
        "effective_manifest_sha256": manifest["effective_manifest_sha256"],
        "effective_qc_summary_sha256": qc["summary_sha256"],
        "repair_concurrency_evidence_sha256": (
            effective.get("repair_concurrency_evidence") or {}
        ).get("evidence_sha256"),
        "source_prelock_sha256": source["prelock_sha256"],
        "prompt_sha256": tools["review_prompt"]["sha256"],
        "proposal_schema_sha256": tools["proposal_schema"]["sha256"],
        "checklist_schema_sha256": tools["checklist_schema"]["sha256"],
        "review_tools_sha256": {
            role: tools[role]["sha256"]
            for role in ("batch_runner", "common", "independent_validator", "prelock_builder")
        },
        "codex_binary_sha256": codex.get("binary_sha256"),
        "codex_version": codex.get("version"),
        "model": config.get("model"),
        "reasoning_effort": config.get("reasoning_effort"),
        "max_parallel": config.get("max_parallel"),
    }
    observed = object_sha256(payload)
    if prelock.get("content_address") != observed:
        raise RepairPipelineError("semantic-review prelock content address differs")
    return observed


def verify_handoff(path: Path) -> dict[str, Any]:
    path = path.resolve()
    try:
        path.relative_to(WORK_ROOT.resolve())
    except ValueError as exc:
        raise RepairPipelineError("repair-aware handoff must stay inside candidate116") from exc
    handoff = load_json(path, "repair-aware promotion handoff")
    if (
        handoff.get("schema_version") != HANDOFF_SCHEMA
        or handoff.get("status") != "eligible_input_for_repair_aware_promotion"
    ):
        raise RepairPipelineError("repair-aware handoff schema/status is invalid")
    verify_self_hash(handoff, "handoff_sha256", "repair-aware promotion handoff")
    order = list(handoff.get("case_order") or [])
    rows = list(handoff.get("cases") or [])
    if (
        handoff.get("case_count") != EXPECTED_CASE_COUNT
        or len(order) != EXPECTED_CASE_COUNT
        or len(set(order)) != EXPECTED_CASE_COUNT
        or handoff.get("case_order_sha256") != object_sha256(order)
        or len(rows) != EXPECTED_CASE_COUNT
        or handoff.get("cases_sha256") != object_sha256(rows)
        or handoff.get("repair_count", 0) + handoff.get("retain_count", 0)
        != EXPECTED_CASE_COUNT
    ):
        raise RepairPipelineError("repair-aware handoff case universe is invalid")
    authority = handoff.get("review_authority") or {}
    if (
        authority.get("reviewer") != "Codex/root_agent"
        or authority.get("human_reviewed") is not False
        or authority.get("model_proposals_are_non_authorizing") is not True
        or authority.get("external_case_verdicts_are_authorizing_source") is not True
        or authority.get("root_agent_review_accepted_116_of_116") is not True
    ):
        raise RepairPipelineError("handoff review authority is missing or falsely claims human review")
    policy = handoff.get("promotion_policy") or {}
    required_policy = (
        "legacy_wave3_direct_promotion_forbidden",
        "repair_aware_origin_required",
        "all_116_effective_qc_pass_required",
        "all_116_semantic_proposals_accepted_required",
        "independent_semantic_validation_pass_required",
        "all_116_root_agent_reviews_accepted_required",
        "repair_concurrency_raw_samples_revalidated_required",
        "human_review_claim_forbidden",
    )
    if any(policy.get(key) is not True for key in required_policy) or policy.get(
        "canonical_promotion_completed"
    ) is not False:
        raise RepairPipelineError("handoff promotion policy is not fail closed")

    manifest_path = verify_file_binding(
        handoff.get("effective_manifest"), "effective manifest", inside_candidate=True
    )
    manifest = load_json(manifest_path, "effective manifest")
    verify_internal_hash(manifest, ("effective_manifest_sha256",), "effective manifest")
    if (
        manifest.get("effective_manifest_sha256")
        != handoff["effective_manifest"].get("effective_manifest_sha256")
        or manifest.get("schema_version") != "androidworld_effective_checklist_wave/v1"
        or manifest.get("status")
        != "composed_not_qc_or_independent_codex_root_agent_accepted"
        or manifest.get("case_order") != order
        or manifest.get("case_order_sha256") != handoff.get("case_order_sha256")
        or manifest.get("case_count") != EXPECTED_CASE_COUNT
    ):
        raise RepairPipelineError("handoff/effective-manifest identity differs")
    effective_rows = list(manifest.get("cases") or [])
    if len(effective_rows) != EXPECTED_CASE_COUNT or manifest.get("cases_sha256") != object_sha256(
        effective_rows
    ):
        raise RepairPipelineError("effective manifest case index is invalid")

    repair_prelock_path = verify_file_binding(
        handoff.get("repair_prelock"), "repair prelock", inside_candidate=True
    )
    repair_prelock = load_json(repair_prelock_path, "repair prelock")
    verify_internal_hash(repair_prelock, ("prelock_sha256",), "repair prelock")
    if repair_prelock.get("prelock_sha256") != handoff["repair_prelock"].get("prelock_sha256"):
        raise RepairPipelineError("handoff repair-prelock internal hash differs")

    repair_receipt_path = verify_file_binding(
        manifest.get("repair_batch_receipt"), "repair batch receipt", inside_candidate=True
    )
    repair_receipt = load_json(repair_receipt_path, "repair batch receipt")
    verify_internal_hash(repair_receipt, ("receipt_sha256",), "repair batch receipt")
    concurrency_evidence = verify_repair_concurrency_evidence(
        repair_prelock,
        repair_receipt,
        repair_root=repair_receipt_path.parent,
    )
    if (
        concurrency_evidence != manifest.get("repair_concurrency_evidence")
        or concurrency_evidence != handoff.get("repair_concurrency_evidence")
    ):
        raise RepairPipelineError(
            "repair concurrency evidence differs across raw samples/manifest/handoff"
        )
    concurrency_audit = concurrency_evidence.get("summary")
    concurrency_samples = concurrency_evidence.get("samples")
    if (
        not isinstance(concurrency_audit, Mapping)
        or not isinstance(concurrency_samples, Mapping)
        or manifest.get("repair_concurrency_audit") != concurrency_audit
        or manifest.get("repair_concurrency_samples") != concurrency_samples
        or handoff.get("repair_concurrency_audit") != concurrency_audit
        or handoff.get("repair_concurrency_samples") != concurrency_samples
    ):
        raise RepairPipelineError(
            "repair concurrency summary/sample aliases differ from raw-revalidated evidence"
        )

    qc_summary_path = verify_file_binding(
        handoff.get("effective_qc_summary"), "effective QC summary", inside_candidate=True
    )
    qc_summary = load_json(qc_summary_path, "effective QC summary")
    verify_internal_hash(qc_summary, ("summary_sha256",), "effective QC summary")
    if (
        qc_summary.get("summary_sha256") != handoff["effective_qc_summary"].get("summary_sha256")
        or qc_summary.get("status") != "pass"
        or qc_summary.get("case_count") != EXPECTED_CASE_COUNT
        or qc_summary.get("passed_count") != EXPECTED_CASE_COUNT
        or qc_summary.get("failed_count") != 0
        or (qc_summary.get("effective_manifest") or {}).get("effective_manifest_sha256")
        != manifest.get("effective_manifest_sha256")
        or qc_summary.get("repair_concurrency_evidence") != concurrency_evidence
        or qc_summary.get("repair_concurrency_audit") != concurrency_audit
        or qc_summary.get("repair_concurrency_samples") != concurrency_samples
    ):
        raise RepairPipelineError("handoff effective QC is not a bound 116/116 pass")

    semantic_prelock_path = verify_file_binding(
        handoff.get("semantic_review_prelock"), "semantic-review prelock", inside_candidate=True
    )
    semantic_prelock = load_json(semantic_prelock_path, "semantic-review prelock")
    verify_self_hash(semantic_prelock, "prelock_sha256", "semantic-review prelock")
    verify_effective_review_content_address(semantic_prelock)
    semantic_rows = list(semantic_prelock.get("case_inputs") or [])
    if (
        semantic_prelock.get("prelock_sha256")
        != handoff["semantic_review_prelock"].get("prelock_sha256")
        or semantic_prelock.get("case_order") != order
        or semantic_prelock.get("case_count") != EXPECTED_CASE_COUNT
        or len(semantic_rows) != EXPECTED_CASE_COUNT
        or semantic_prelock.get("case_inputs_sha256") != object_sha256(semantic_rows)
        or (semantic_prelock.get("effective_generation") or {}).get(
            "repair_concurrency_evidence"
        )
        != concurrency_evidence
        or (semantic_prelock.get("effective_generation") or {}).get(
            "repair_concurrency_audit"
        )
        != concurrency_audit
        or (semantic_prelock.get("effective_generation") or {}).get(
            "repair_concurrency_samples"
        )
        != concurrency_samples
    ):
        raise RepairPipelineError("handoff semantic-review prelock differs")
    for rank, (case_id, row) in enumerate(zip(order, semantic_rows, strict=True)):
        verify_self_hashed_row(row, "case_input_sha256", f"{case_id} semantic input")
        if row.get("selection_rank") != rank or row.get("case_unit_id") != case_id:
            raise RepairPipelineError(f"{case_id} semantic-review prelock order differs")
    semantic_config_path = verify_file_binding(
        handoff.get("semantic_review_config"), "semantic-review config", inside_candidate=True
    )
    semantic_config = load_json(semantic_config_path, "semantic-review config")
    verify_self_hash(semantic_config, "config_sha256", "semantic-review config")
    if (
        semantic_config.get("config_sha256")
        != handoff["semantic_review_config"].get("config_sha256")
        or semantic_config.get("provider") != "codex_cli"
        or semantic_config.get("auth_mode") != "codex_login"
        or semantic_config.get("sandbox") != "read-only"
        or semantic_config.get("ephemeral") is not True
        or semantic_config.get("ignore_user_config") is not True
        or semantic_config.get("max_parallel") != 6
        or semantic_config.get("case_count") != EXPECTED_CASE_COUNT
    ):
        raise RepairPipelineError("semantic-review config does not prove exact six-worker Codex mode")
    semantic_snapshot_path = verify_file_binding(
        handoff.get("semantic_review_toolchain"), "semantic-review toolchain", inside_candidate=True
    )
    semantic_snapshot = load_json(semantic_snapshot_path, "semantic-review toolchain")
    verify_self_hash(semantic_snapshot, "snapshot_sha256", "semantic-review toolchain")
    if semantic_snapshot.get("snapshot_sha256") != handoff["semantic_review_toolchain"].get(
        "snapshot_sha256"
    ):
        raise RepairPipelineError("semantic-review toolchain internal hash differs")
    snapshot_roles = semantic_snapshot.get("roles") or {}
    if snapshot_roles != semantic_prelock.get("tool_bindings"):
        raise RepairPipelineError("semantic-review toolchain roles differ from semantic prelock")
    for role, binding in snapshot_roles.items():
        verify_file_binding(binding, f"semantic-review tool {role}", inside_candidate=True)

    validation_path = verify_file_binding(
        handoff.get("independent_semantic_validation"),
        "independent semantic validation",
        inside_candidate=True,
    )
    validation = load_json(validation_path, "independent semantic validation")
    verify_internal_hash(validation, ("validation_report_sha256",), "independent validation")
    if (
        validation.get("validation_report_sha256")
        != handoff["independent_semantic_validation"].get("validation_report_sha256")
        or validation.get("status") != "pass"
        or validation.get("passed_count") != EXPECTED_CASE_COUNT
        or validation.get("proposed_accepted_count") != EXPECTED_CASE_COUNT
        or validation.get("proposed_rejected_count") != 0
    ):
        raise RepairPipelineError("independent semantic validation is not 116 accepted")
    validation_rows = list(validation.get("cases") or [])
    if len(validation_rows) != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("independent semantic validation case index is not 116")
    for rank, (case_id, row) in enumerate(zip(order, validation_rows, strict=True)):
        if (
            row.get("selection_rank") != rank
            or row.get("case_unit_id") != case_id
            or row.get("status") != "pass"
            or row.get("proposal_status") != "accepted"
            or row.get("issues") != []
            or row.get("promotion_authorized") is not False
        ):
            raise RepairPipelineError(f"independent semantic validation row fails at {case_id}")

    verdict_index_path = verify_file_binding(
        handoff.get("external_root_agent_verdict_index"),
        "external root-agent verdict index",
        inside_candidate=True,
    )
    verdict_index = load_json(verdict_index_path, "external root-agent verdict index")
    verify_self_hash(verdict_index, "index_sha256", "external root-agent verdict index")
    verdict_rows = list(verdict_index.get("cases") or [])
    if (
        verdict_index.get("index_sha256")
        != handoff["external_root_agent_verdict_index"].get("index_sha256")
        or verdict_index.get("schema_version") != ROOT_VERDICT_INDEX_SCHEMA
        or verdict_index.get("status") != "complete"
        or verdict_index.get("review_id") != handoff.get("review_id")
        or verdict_index.get("reviewer") != "Codex/root_agent"
        or verdict_index.get("human_reviewed") is not False
        or verdict_index.get("case_count") != EXPECTED_CASE_COUNT
        or verdict_index.get("accepted_count") != EXPECTED_CASE_COUNT
        or verdict_index.get("rejected_count") != 0
        or verdict_index.get("case_order") != order
        or verdict_index.get("case_order_sha256") != handoff.get("case_order_sha256")
        or len(verdict_rows) != EXPECTED_CASE_COUNT
        or verdict_index.get("cases_sha256") != object_sha256(verdict_rows)
        or verdict_index.get("semantic_review_prelock") != handoff.get("semantic_review_prelock")
        or verdict_index.get("independent_validation")
        != handoff.get("independent_semantic_validation")
    ):
        raise RepairPipelineError("external root-agent verdict index is not an exact 116/116 acceptance")
    require_zoned_time(verdict_index.get("created_at"), "root-verdict index created_at")
    for rank, (case_id, row) in enumerate(zip(order, verdict_rows, strict=True)):
        if not isinstance(row, Mapping):
            raise RepairPipelineError(f"{case_id} root-verdict index row is not an object")
        verify_self_hashed_row(row, "row_sha256", f"{case_id} root-verdict index row")
        if (
            set(row)
            != {
                "selection_rank",
                "case_unit_id",
                "task_id",
                "verdict",
                "reviewed_at",
                "verdict_file",
                "verdict_sha256",
                "row_sha256",
            }
            or row.get("selection_rank") != rank
            or row.get("case_unit_id") != case_id
            or row.get("task_id") != case_id
            or row.get("verdict") != "accepted"
        ):
            raise RepairPipelineError(f"{case_id} root-verdict index order/status differs")

    review_summary_path = verify_file_binding(
        handoff.get("root_agent_review_summary"), "root-agent review summary", inside_candidate=True
    )
    review_summary = load_json(review_summary_path, "root-agent review summary")
    verify_internal_hash(review_summary, ("review_summary_sha256",), "root-agent review summary")
    review_rows = list(review_summary.get("reviews") or [])
    if (
        review_summary.get("review_summary_sha256")
        != handoff["root_agent_review_summary"].get("review_summary_sha256")
        or review_summary.get("status") != "accepted_116_of_116"
        or review_summary.get("reviewer") != "Codex/root_agent"
        or review_summary.get("human_reviewed") is not False
        or review_summary.get("accepted_count") != EXPECTED_CASE_COUNT
        or review_summary.get("rejected_count") != 0
        or len(review_rows) != EXPECTED_CASE_COUNT
        or review_summary.get("reviews_sha256") != object_sha256(review_rows)
        or review_summary.get("external_root_agent_verdict_index")
        != handoff.get("external_root_agent_verdict_index")
        or review_summary.get("repair_concurrency_evidence") != concurrency_evidence
        or review_summary.get("repair_concurrency_audit") != concurrency_audit
        or review_summary.get("repair_concurrency_samples") != concurrency_samples
    ):
        raise RepairPipelineError("root-agent review summary is invalid")
    for rank, (case_id, row) in enumerate(zip(order, review_rows, strict=True)):
        if row.get("selection_rank") != rank or row.get("case_unit_id") != case_id:
            raise RepairPipelineError(f"root-agent review summary order differs at {case_id}")

    effective_by_case = {row["case_unit_id"]: row for row in effective_rows}
    semantic_by_case = {row["case_unit_id"]: row for row in semantic_rows}
    review_by_case = {row["case_unit_id"]: row for row in review_rows}
    verdict_by_case = {row["case_unit_id"]: row for row in verdict_rows}
    if set(effective_by_case) != set(order) or set(semantic_by_case) != set(order) or set(
        review_by_case
    ) != set(order) or set(verdict_by_case) != set(order):
        raise RepairPipelineError("effective/semantic/verdict/review case sets differ")

    origin_counts = {"wave_003": 0, "repair": 0}
    for rank, (case_id, row) in enumerate(zip(order, rows, strict=True)):
        if (
            not isinstance(row, Mapping)
            or row.get("selection_rank") != rank
            or row.get("case_unit_id") != case_id
            or row.get("task_id") != case_id
            or row.get("group") != ("official100" if rank < 100 else "extra16")
        ):
            raise RepairPipelineError(f"handoff case identity/order fails at {case_id}")
        verify_self_hashed_row(row, "case_handoff_sha256", f"{case_id} handoff row")
        effective = effective_by_case[case_id]
        semantic = semantic_by_case[case_id]
        origin = row.get("origin")
        if origin not in origin_counts or effective.get("origin") != origin:
            raise RepairPipelineError(f"{case_id} effective origin differs")
        origin_counts[str(origin)] += 1
        packet_path = verify_file_binding(row.get("full_packet"), f"{case_id} packet", inside_candidate=True)
        if row.get("full_packet") != (semantic.get("input_bindings") or {}).get("packet"):
            raise RepairPipelineError(f"{case_id} handoff packet differs from semantic prelock")
        if packet_path.name != "case_packet.md":
            raise RepairPipelineError(f"{case_id} packet is not the original full case_packet.md")
        checklist_path = verify_file_binding(
            row.get("effective_checklist_yaml"), f"{case_id} checklist YAML", inside_candidate=True
        )
        checklist_json_path = verify_file_binding(
            row.get("effective_checklist_json"), f"{case_id} checklist JSON", inside_candidate=True
        )
        if load_yaml_mapping(checklist_path) != load_json(checklist_json_path):
            raise RepairPipelineError(f"{case_id} effective checklist YAML/JSON differ")
        if row.get("effective_checklist_yaml") != effective.get("effective_checklist"):
            raise RepairPipelineError(f"{case_id} handoff checklist differs from effective manifest")
        origin_path = verify_file_binding(
            row.get("effective_origin"), f"{case_id} origin record", inside_candidate=True
        )
        origin_value = load_json(origin_path, f"{case_id} origin record")
        verify_internal_hash(origin_value, ("origin_sha256",), f"{case_id} origin record")
        if (
            origin_value.get("origin") != origin
            or origin_value.get("origin_sha256") != row["effective_origin"].get("origin_sha256")
            or row.get("effective_origin") != effective.get("effective_origin")
        ):
            raise RepairPipelineError(f"{case_id} origin record differs")
        provenance = row.get("repair_provenance")
        if origin == "repair":
            provenance_path = verify_file_binding(
                provenance, f"{case_id} repair provenance", inside_candidate=True
            )
            provenance_value = load_json(provenance_path, f"{case_id} repair provenance")
            verify_internal_hash(
                provenance_value, ("provenance_sha256",), f"{case_id} repair provenance"
            )
            if provenance != effective.get("repair_provenance"):
                raise RepairPipelineError(f"{case_id} repair provenance differs from effective manifest")
        elif provenance is not None or effective.get("repair_provenance") is not None:
            raise RepairPipelineError(f"{case_id} retained case has repair provenance")
        sidecars = row.get("draft_sidecars") or {}
        if set(sidecars) != set(SIDECAR_KEYS):
            raise RepairPipelineError(f"{case_id} draft sidecar set is incomplete")
        for name, binding in sidecars.items():
            path_value = verify_file_binding(binding, f"{case_id} draft sidecar {name}", inside_candidate=True)
            if path_value.parent != checklist_path.parent or path_value.name != SIDECAR_KEYS[name]:
                raise RepairPipelineError(f"{case_id} draft sidecar {name} is from another case")
        llm = load_json(
            resolve_repo_path(sidecars["llm_call_json"]["path"], inside_candidate=True),
            f"{case_id} draft llm_call",
        )
        api = load_json(
            resolve_repo_path(sidecars["api_response_json"]["path"], inside_candidate=True),
            f"{case_id} draft api_response",
        )
        metadata = llm.get("response_metadata") or {}
        if (
            llm.get("case_unit_id") != case_id
            or llm.get("provider") != "codex_cli"
            or metadata.get("auth_mode") != "codex_login"
            or metadata.get("response_status") != "completed"
            or api.get("status") != "completed"
            or api.get("provider") != "codex_cli"
            or int((api.get("usage") or {}).get("total_tokens") or 0) <= 0
        ):
            raise RepairPipelineError(f"{case_id} effective draft Codex provenance is invalid")
        qc_path = verify_file_binding(row.get("effective_qc"), f"{case_id} effective QC", inside_candidate=True)
        qc = load_json(qc_path, f"{case_id} effective QC")
        if (
            qc.get("status") != "passed"
            or qc.get("issues") != []
            or qc.get("checklist_sha256") != sha256_file(checklist_path)
            or qc.get("effective_origin") != origin
            or qc.get("effective_manifest_sha256") != manifest.get("effective_manifest_sha256")
            or not isinstance(qc.get("checks"), Mapping)
            or not all(value is True for value in qc["checks"].values())
        ):
            raise RepairPipelineError(f"{case_id} effective QC is invalid")
        proposal_path = verify_file_binding(
            row.get("semantic_proposal"), f"{case_id} semantic proposal", inside_candidate=True
        )
        proposal = load_json(proposal_path, f"{case_id} semantic proposal")
        verify_self_hash(proposal, "proposal_sha256", f"{case_id} semantic proposal")
        if (
            proposal.get("case_unit_id") != case_id
            or proposal.get("review_authority") != "independent_model_proposal_only"
            or proposal.get("promotion_authorized") is not False
            or (proposal.get("review") or {}).get("proposal_status") != "accepted"
            or (proposal.get("review") or {}).get("issues") != []
            or proposal.get("input_bindings") != semantic.get("input_bindings")
        ):
            raise RepairPipelineError(f"{case_id} semantic proposal is not accepted/non-authorizing")
        proposal_review = proposal.get("review") or {}
        proposal_checks = proposal_review.get("checks") or {}
        matrix = proposal_review.get("goal_evaluator_matrix") or {}
        pointer_audit = proposal_review.get("support_pointer_audit") or {}
        if (
            not proposal_checks
            or any(
                not isinstance(finding, Mapping) or finding.get("status") != "pass"
                for finding in proposal_checks.values()
            )
            or matrix.get("status") != "pass"
            or matrix.get("uncovered_requirement_ids") != []
            or pointer_audit.get("status") != "pass"
            or pointer_audit.get("missing_checklist_support_paths") != []
            or pointer_audit.get("invalid_pointer_values") != []
            or pointer_audit.get("unsupported_pointer_values") != []
            or proposal_review.get("corrected_checklist") is not None
            or proposal_review.get("correction_summary") != []
        ):
            raise RepairPipelineError(f"{case_id} accepted semantic proposal has an incomplete gate")
        result_path = verify_file_binding(
            row.get("semantic_result"), f"{case_id} semantic result", inside_candidate=True
        )
        result = load_json(result_path, f"{case_id} semantic result")
        verify_self_hash(result, "result_sha256", f"{case_id} semantic result")
        receipt_path = verify_file_binding(
            row.get("semantic_receipt"), f"{case_id} semantic receipt", inside_candidate=True
        )
        receipt = load_json(receipt_path, f"{case_id} semantic receipt")
        verify_self_hash(receipt, "receipt_sha256", f"{case_id} semantic receipt")
        if (
            result.get("case_unit_id") != case_id
            or result.get("status") != "completed"
            or result.get("proposal_status") != "accepted"
            or result.get("promotion_authorized") is not False
            or result.get("prelock_sha256") != semantic_prelock.get("prelock_sha256")
            or receipt.get("case_unit_id") != case_id
            or receipt.get("status") != "completed_valid_proposal"
            or receipt.get("proposal_status") != "accepted"
            or receipt.get("promotion_authorized") is not False
            or result.get("receipt_sha256") != receipt.get("receipt_sha256")
            or any(
                (result.get("selected_receipt") or {}).get(key)
                != row["semantic_receipt"].get(key)
                for key in ("path", "sha256", "size_bytes")
            )
            or any(
                ((receipt.get("files") or {}).get("proposal") or {}).get(key)
                != row["semantic_proposal"].get(key)
                for key in ("path", "sha256", "size_bytes")
            )
        ):
            raise RepairPipelineError(f"{case_id} semantic result/receipt chain is invalid")
        indexed_verdict = verdict_by_case[case_id]
        verdict_path = verify_file_binding(
            row.get("root_agent_verdict"),
            f"{case_id} external root-agent verdict",
            inside_candidate=True,
        )
        expected_verdict_bindings = copy.deepcopy(dict(semantic.get("input_bindings") or {}))
        expected_verdict_bindings.update(
            {
                "semantic_proposal": copy.deepcopy(row["semantic_proposal"]),
                "semantic_result": copy.deepcopy(row["semantic_result"]),
                "semantic_receipt": copy.deepcopy(row["semantic_receipt"]),
                "semantic_review_prelock": copy.deepcopy(handoff["semantic_review_prelock"]),
                "independent_validation": copy.deepcopy(
                    handoff["independent_semantic_validation"]
                ),
            }
        )
        verdict = verify_root_agent_verdict(
            verdict_path,
            case_id=case_id,
            selection_rank=rank,
            expected_bindings=expected_verdict_bindings,
        )
        if (
            verdict.get("verdict") != "accepted"
            or verdict.get("verdict_sha256") != row["root_agent_verdict"].get("verdict_sha256")
            or indexed_verdict.get("verdict_sha256") != verdict.get("verdict_sha256")
            or indexed_verdict.get("reviewed_at") != verdict.get("reviewed_at")
            or indexed_verdict.get("verdict_file") != row.get("root_agent_verdict")
        ):
            raise RepairPipelineError(f"{case_id} external root-agent verdict/index differs")
        review_path = verify_file_binding(
            row.get("root_agent_review"), f"{case_id} root-agent review", inside_candidate=True
        )
        review = load_json(review_path, f"{case_id} root-agent review")
        verify_self_hash(review, "review_sha256", f"{case_id} root-agent review")
        if (
            review.get("case_unit_id") != case_id
            or review.get("status") != "accepted"
            or review.get("reviewer") != "Codex/root_agent"
            or review.get("human_reviewed") is not False
            or review.get("issues") != []
            or any((review.get("checks") or {}).get(name) is not True for name in REVIEW_CHECKS)
            or review.get("review_authority")
            != "mechanical_finalization_of_external_root_agent_case_verdict"
            or review.get("reviewed_at") != verdict.get("reviewed_at")
            or review.get("notes") != verdict.get("notes")
            or review.get("review_evidence") != verdict.get("checks")
            or review.get("promotion_authorized_by_model_proposal") is not False
            or review.get("promotion_authorized_by_root_agent_review") is not True
            or review.get("review_sha256") != row["root_agent_review"].get("review_sha256")
            or review.get("raw_checklist_path") != row["effective_checklist_yaml"].get("path")
            or review.get("raw_checklist_sha256") != row["effective_checklist_yaml"].get("sha256")
            or review.get("accepted_checklist_path")
            != row["effective_checklist_yaml"].get("path")
            or review.get("accepted_checklist_sha256")
            != row["effective_checklist_yaml"].get("sha256")
            or review.get("automatic_qc_report_path") != row["effective_qc"].get("path")
            or review.get("automatic_qc_report_sha256") != row["effective_qc"].get("sha256")
            or review.get("semantic_proposal") != row.get("semantic_proposal")
            or review.get("semantic_result") != row.get("semantic_result")
            or review.get("semantic_receipt") != row.get("semantic_receipt")
            or (review.get("semantic_review_prelock") or {}).get("prelock_sha256")
            != semantic_prelock.get("prelock_sha256")
            or (review.get("independent_validation") or {}).get("validation_report_sha256")
            != validation.get("validation_report_sha256")
            or review.get("external_root_agent_verdict") != row.get("root_agent_verdict")
            or review.get("external_root_agent_verdict_index")
            != handoff.get("external_root_agent_verdict_index")
        ):
            raise RepairPipelineError(f"{case_id} root-agent review is invalid")
        if (
            review_by_case[case_id].get("review") != row.get("root_agent_review")
            or review_by_case[case_id].get("root_agent_verdict")
            != row.get("root_agent_verdict")
        ):
            raise RepairPipelineError(f"{case_id} review summary differs from handoff")
    if origin_counts != {"wave_003": handoff["retain_count"], "repair": handoff["repair_count"]}:
        raise RepairPipelineError("handoff origin counts differ from case rows")
    return {
        "path": path,
        "handoff": handoff,
        "order": order,
        "rows": rows,
        "manifest_path": manifest_path,
        "manifest": manifest,
        "repair_prelock_path": repair_prelock_path,
        "repair_prelock": repair_prelock,
        "repair_receipt_path": repair_receipt_path,
        "repair_receipt": repair_receipt,
        "repair_concurrency_evidence": concurrency_evidence,
        "qc_summary_path": qc_summary_path,
        "qc_summary": qc_summary,
        "semantic_prelock_path": semantic_prelock_path,
        "semantic_prelock": semantic_prelock,
        "validation_path": validation_path,
        "validation": validation,
        "verdict_index_path": verdict_index_path,
        "verdict_index": verdict_index,
        "review_summary_path": review_summary_path,
        "review_summary": review_summary,
    }


def load_packet_index(order: list[str]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    index = load_json(PACKET_INDEX, "candidate116 packet index")
    rows = list(index.get("items") or [])
    if (
        index.get("candidate_count") != EXPECTED_CASE_COUNT
        or len(rows) != EXPECTED_CASE_COUNT
        or [str(row.get("case_unit_id")) for row in rows] != order
    ):
        raise RepairPipelineError("packet index does not match handoff order")
    by_case = {str(row["case_unit_id"]): row for row in rows}
    for rank, row in enumerate(rows):
        packet = resolve_repo_path(row.get("case_packet_path"), inside_candidate=True)
        if (
            row.get("selection_rank") != rank
            or packet.name != "case_packet.md"
            or sha256_file(packet) != row.get("case_packet_sha256")
        ):
            raise RepairPipelineError(f"packet index differs at {row.get('case_unit_id')}")
    return index, by_case


def load_slot_ledger(order: list[str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    ledger = load_json(SLOT_LEDGER, "348-slot ledger")
    verify_self_hash(ledger, "ledger_sha256", "348-slot ledger")
    cases = list(ledger.get("cases") or [])
    slots = list(ledger.get("slots") or [])
    if (
        ledger.get("case_count") != EXPECTED_CASE_COUNT
        or ledger.get("agent_count") != len(AGENTS)
        or ledger.get("agent_ids") != list(AGENTS)
        or ledger.get("record_slot_count") != SLOT_COUNT
        or len(slots) != SLOT_COUNT
        or [row.get("case_unit_id") for row in cases] != order
        or [row.get("slot_index") for row in slots] != list(range(SLOT_COUNT))
        or [row.get("record_slot_id") for row in slots] != ledger.get("record_slot_ids")
        or object_sha256(ledger.get("record_slot_ids")) != ledger.get("record_slot_ids_hash")
    ):
        raise RepairPipelineError("slot ledger is not the exact candidate116 x A/B/C order")
    for slot in slots:
        rank = int(slot["selection_rank"])
        agent = str(slot["agent_id"])
        if (
            slot.get("case_unit_id") != order[rank]
            or slot.get("agent_index") != AGENTS.index(agent)
            or slot.get("slot_index") != rank * len(AGENTS) + AGENTS.index(agent)
        ):
            raise RepairPipelineError(f"slot ordering differs at {slot.get('record_slot_id')}")
    return ledger, slots


def verify_static_acceptance_inputs() -> None:
    """Require the frozen packet/source acceptance reports to be clean passes."""

    strict = load_json(STATIC_ACCEPTANCE, "strict packet/source acceptance")
    strict_checks = strict.get("checks") or {}
    required_strict_checks = (
        "canonical_abc_provenance_absent",
        "draft_prelock_freeze_consistent",
        "goal_schema_init_evaluator_sources_complete",
        "markor_edit_note_three_branches",
        "official100_selector_unchanged",
        "old_root_pre_post_snapshots_equal",
        "result_fields_and_host_paths_absent",
    )
    if (
        strict.get("schema_version") != "androidworld_candidate116_strict_acceptance/v1"
        or strict.get("status") != "pass"
        or strict.get("case_count") != EXPECTED_CASE_COUNT
        or strict.get("slot_count") != SLOT_COUNT
        or strict.get("prompt_hash_count") != EXPECTED_CASE_COUNT
        or strict.get("issues") != []
        or not isinstance(strict_checks, Mapping)
        or any(strict_checks.get(key) is not True for key in required_strict_checks)
        or strict_checks.get("unique_real_prompt_hashes") != EXPECTED_CASE_COUNT
        or strict_checks.get("slot_counts")
        != {"candidate116": SLOT_COUNT, "extra16": 48, "official100": 300}
    ):
        raise RepairPipelineError("strict packet/source acceptance report is not a clean 116/348 pass")

    static = load_json(STATIC_VALIDATION, "semantic/static packet validation")
    static_checks = static.get("checks") or {}
    input_guard = static.get("input_guard") or {}
    required_static_checks = (
        "all_116_real_prompt_hashes_frozen",
        "all_116_semantic_records_complete",
        "all_compact_packets_byte_exact",
        "all_core_descriptor_sources_match",
        "all_declared_file_hashes_match",
        "all_internal_source_closures_resolved",
        "all_raw_inventories_exact",
        "all_rendered_packets_byte_exact",
        "all_source_contexts_derive",
        "deterministic_second_build_byte_exact",
        "draft_input_freeze_valid",
        "independent_strict_acceptance",
        "legacy_immutable_roots_pre_post_equal",
        "manifests_draft_prelock",
        "official100_pre_post_hash_equal",
        "official100_untouched",
        "old_roots_content_tree_pre_post_equal",
        "post_run_fields_absent",
        "semantic_consistency_checks_pass",
        "shared_frozen_source_snapshot_complete",
        "slot_ledger_348_predeclared",
    )
    if (
        static.get("schema_version") != "androidworld_candidate116_static_validation/v2"
        or static.get("status") != "pass"
        or not isinstance(static_checks, Mapping)
        or any(static_checks.get(key) is not True for key in required_static_checks)
        or static_checks.get("candidate_packet_count") != EXPECTED_CASE_COUNT
        or static_checks.get("candidate_pool_count") != EXPECTED_CASE_COUNT
        or static_checks.get("official100_prefix_count") != 100
        or static_checks.get("extra16_count") != 16
        or len(static.get("per_case") or []) != EXPECTED_CASE_COUNT
        or input_guard.get("live_registry_exact_match") is not True
        or input_guard.get("official100_membership_and_order_match_candidate_prefix") is not True
        or input_guard.get("official100_selector_remains_unmodified_input") is not True
        or input_guard.get("source_tree_clean") is not True
    ):
        raise RepairPipelineError("semantic/static packet validation is not a clean 116-case pass")


def resolved_agent_configuration_bindings() -> dict[str, dict[str, Any]]:
    """Recompute the exact per-agent slot binding from current bound inputs."""

    experiment = load_json(CANDIDATE_MANIFEST, "candidate116 experiment manifest")
    agent_rows = list(experiment.get("agents") or [])
    declared = {
        str(row.get("agent_id")): str(row.get("config_hash"))
        for row in agent_rows
        if isinstance(row, Mapping)
    }
    configured = load_yaml_mapping(AGENTS_CONFIG, "runtime agents config").get(
        "experimental_agents"
    )
    if (
        len(agent_rows) != len(AGENTS)
        or set(declared) != set(AGENTS)
        or any(not HASH_RE.fullmatch(value) for value in declared.values())
        or not isinstance(configured, Mapping)
        or set(configured) != set(AGENTS)
        or any(not isinstance(configured[agent_id], Mapping) for agent_id in AGENTS)
    ):
        raise RepairPipelineError("Agent A/B/C configuration universe/hash set is not exact")
    config_binding = file_binding(AGENTS_CONFIG)
    return {
        agent_id: {
            "path": config_binding["path"],
            "file_sha256": config_binding["sha256"],
            "size_bytes": config_binding["size_bytes"],
            "agent_id": agent_id,
            "resolved_agent_config_sha256": object_sha256(configured[agent_id]),
            "declared_agent_config_sha256": declared[agent_id],
        }
        for agent_id in AGENTS
    }


def tree_descriptor(root: Path, declared_path: Path | None = None) -> dict[str, Any]:
    files = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    ]
    return {
        "path": str((declared_path or root).resolve().relative_to(REPO_ROOT.resolve())),
        "file_count": len(files),
        "tree_sha256": object_sha256(files),
        "files": files,
    }


def _placeholder_markers(text: str) -> list[str]:
    return sorted({marker for marker in PLACEHOLDERS if marker.casefold() in text.casefold()})


def _require_repo_path(value: Any, label: str, *, kind: str) -> Path:
    path = Path(str(value or "")).expanduser()
    if not path.is_absolute():
        raise RepairPipelineError(f"{label} must be an absolute path")
    path = path.resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise RepairPipelineError(f"{label} must stay inside the repository") from exc
    if kind == "directory" and not path.is_dir():
        raise RepairPipelineError(f"{label} directory does not exist")
    if kind == "file" and not path.is_file():
        raise RepairPipelineError(f"{label} file does not exist")
    return path


def validate_custom_execution_payload(
    custom: Mapping[str, Any],
    *,
    preflight: Mapping[str, Any],
    base_bindings: Mapping[str, Any],
) -> None:
    """Validate the complete locked AndroidWorld execution configuration.

    A two-field ``status/execution_eligible`` assertion is intentionally
    insufficient.  Every agent, source scope, launcher, reset implementation,
    device, and output location is content-bound here.
    """
    expected_top = {
        "schema_version",
        "status",
        "execution_eligible",
        "case_count",
        "record_slot_count",
        "agent_ids",
        "base_configuration_bindings",
        "scope_bindings",
        "agents",
        "androidworld",
        "launcher",
        "results",
        "config_sha256",
    }
    if set(custom) != expected_top:
        raise RepairPipelineError("custom runtime config field set is not exact")
    verify_self_hash(custom, "config_sha256", "custom runtime config")
    if (
        custom.get("schema_version") != CUSTOM_RUNTIME_SCHEMA
        or custom.get("status") != "locked"
        or custom.get("execution_eligible") is not True
        or custom.get("case_count") != EXPECTED_CASE_COUNT
        or custom.get("record_slot_count") != SLOT_COUNT
        or custom.get("agent_ids") != list(AGENTS)
        or custom.get("base_configuration_bindings") != dict(base_bindings)
    ):
        raise RepairPipelineError("custom runtime config scope/status is invalid")
    verify_binding_tree(custom["base_configuration_bindings"], "custom base config", inside_candidate=False)

    scope = custom.get("scope_bindings")
    expected_scope = {
        "packet_index": file_binding(PACKET_INDEX),
        "slot_ledger": file_binding(SLOT_LEDGER),
        "experiment_scope_manifest": file_binding(CANDIDATE_MANIFEST),
    }
    if scope != expected_scope:
        raise RepairPipelineError("custom runtime config binds a different case/slot scope")
    verify_binding_tree(scope, "custom execution scope", inside_candidate=True)

    agents_config = load_yaml_mapping(AGENTS_CONFIG, "agents config")
    experiment = load_json(CANDIDATE_MANIFEST, "candidate116 experiment manifest")
    declared_hashes = {
        str(row.get("agent_id")): str(row.get("config_hash"))
        for row in experiment.get("agents") or []
    }
    configured_agents = agents_config.get("experimental_agents") or {}
    custom_agents = custom.get("agents")
    if (
        not isinstance(custom_agents, Mapping)
        or set(custom_agents) != set(AGENTS)
        or set(declared_hashes) != set(AGENTS)
    ):
        raise RepairPipelineError("custom runtime config does not bind Agent A/B/C exactly")
    agent_fields = {
        "agent_id",
        "provider",
        "model",
        "model_version",
        "api_key_env",
        "temperature",
        "max_tokens",
        "timeout_seconds",
        "retry",
        "rate_limit",
        "resolved_agent_config_sha256",
        "declared_agent_config_sha256",
    }
    for agent_id in AGENTS:
        source = configured_agents.get(agent_id)
        declared = custom_agents.get(agent_id)
        if not isinstance(source, Mapping) or not isinstance(declared, Mapping) or set(declared) != agent_fields:
            raise RepairPipelineError(f"custom runtime config has incomplete {agent_id} binding")
        expected = {
            "agent_id": agent_id,
            **{
                key: copy.deepcopy(source.get(key))
                for key in (
                    "provider",
                    "model",
                    "model_version",
                    "api_key_env",
                    "temperature",
                    "max_tokens",
                    "timeout_seconds",
                    "retry",
                    "rate_limit",
                )
            },
            "resolved_agent_config_sha256": object_sha256(source),
            "declared_agent_config_sha256": declared_hashes[agent_id],
        }
        if dict(declared) != expected or _placeholder_markers(
            json.dumps(declared, ensure_ascii=False, sort_keys=True)
        ):
            raise RepairPipelineError(f"custom runtime config {agent_id} differs/has placeholders")

    infra_config = load_yaml_mapping(INFRA_CONFIG, "infra config")
    android_machines = [
        row
        for row in infra_config.get("machines") or []
        if isinstance(row, Mapping) and row.get("role") == "local_androidworld"
    ]
    if len(android_machines) != 1:
        raise RepairPipelineError("infra config does not have exactly one local AndroidWorld machine")
    machine = android_machines[0]
    android = custom.get("androidworld")
    android_fields = {
        "install_root",
        "assets_path",
        "python_bin",
        "runner_entrypoint",
        "runner_argv",
        "adb_path",
        "emulator_path",
        "avd_name",
        "device_serial",
        "grpc_port",
        "reset_strategy",
        "concurrency",
        "source_commit",
    }
    if not isinstance(android, Mapping) or set(android) != android_fields:
        raise RepairPipelineError("custom AndroidWorld runtime block is incomplete")
    install = Path(str(android.get("install_root") or "")).expanduser().resolve()
    assets = Path(str(android.get("assets_path") or "")).expanduser().resolve()
    python_bin = Path(str(android.get("python_bin") or "")).expanduser().resolve()
    runner = Path(str(android.get("runner_entrypoint") or "")).expanduser().resolve()
    adb = Path(str(android.get("adb_path") or "")).expanduser().resolve()
    emulator = Path(str(android.get("emulator_path") or "")).expanduser().resolve()
    for label, path, mode in (
        ("AndroidWorld install root", install, "dir"),
        ("AndroidWorld assets", assets, "dir"),
        ("AndroidWorld Python", python_bin, "executable"),
        ("AndroidWorld runner", runner, "file"),
        ("adb", adb, "executable"),
        ("emulator", emulator, "executable"),
    ):
        if (mode == "dir" and not path.is_dir()) or (mode != "dir" and not path.is_file()):
            raise RepairPipelineError(f"custom runtime {label} does not exist")
        if mode == "executable" and not os.access(path, os.X_OK):
            raise RepairPipelineError(f"custom runtime {label} is not executable")
    try:
        assets.relative_to(install)
        python_bin.relative_to(install)
        runner.relative_to(install)
    except ValueError as exc:
        raise RepairPipelineError("AndroidWorld assets/Python/runner must live under install_root") from exc
    argv = android.get("runner_argv")
    if (
        not isinstance(argv, list)
        or len(argv) < 3
        or argv[0] != str(python_bin)
        or argv[1] != str(runner)
        or "--suite_family=android_world" not in argv
        or any(not isinstance(item, str) or not item for item in argv)
        or android.get("grpc_port") != 8554
        or android.get("reset_strategy")
        != "initialize_task_per_case_and_fresh_device_state"
        or android.get("concurrency") != machine.get("concurrency")
        or android.get("source_commit") != preflight.get("source_commit")
    ):
        raise RepairPipelineError("custom AndroidWorld launcher/device contract is invalid")
    observed_devices = json.dumps(preflight.get("adb_devices") or [], ensure_ascii=False)
    observed_avds = json.dumps(preflight.get("registered_avds") or [], ensure_ascii=False)
    if (
        not str(android.get("device_serial") or "").strip()
        or str(android["device_serial"]) not in observed_devices
        or not str(android.get("avd_name") or "").strip()
        or str(android["avd_name"]) not in observed_avds
    ):
        raise RepairPipelineError("custom runtime device/AVD is not present in bound preflight")

    launcher = custom.get("launcher")
    if not isinstance(launcher, Mapping) or set(launcher) != {
        "binding",
        "reset_implementation",
        "working_directory",
        "invocation_contract",
    }:
        raise RepairPipelineError("custom runtime launcher binding is incomplete")
    launcher_path = verify_file_binding(
        launcher["binding"], "custom AndroidWorld launcher", inside_candidate=False
    )
    reset_path = verify_file_binding(
        launcher["reset_implementation"], "custom AndroidWorld reset", inside_candidate=False
    )
    if launcher_path.stat().st_size == 0 or reset_path.stat().st_size == 0:
        raise RepairPipelineError("custom runtime launcher/reset implementation is empty")
    working = _require_repo_path(launcher.get("working_directory"), "launcher working directory", kind="directory")
    if launcher.get("invocation_contract") != [
        "case_unit_id",
        "agent_id",
        "contract_draft_path",
        "result_output_path",
        "device_serial",
        "avd_name",
    ] or working != REPO_ROOT.resolve():
        raise RepairPipelineError("custom runtime launcher invocation contract is invalid")

    results = custom.get("results")
    if not isinstance(results, Mapping) or set(results) != {
        "output_root",
        "logs_root",
        "artifacts_root",
    }:
        raise RepairPipelineError("custom runtime results block is incomplete")
    result_paths = [
        _require_repo_path(results[key], f"custom runtime {key}", kind="directory")
        for key in ("output_root", "logs_root", "artifacts_root")
    ]
    if len(set(result_paths)) != len(result_paths):
        raise RepairPipelineError("custom runtime result roots must be distinct")


def runtime_state(custom_config: Path | None = None) -> tuple[dict[str, Any], bool]:
    agents = file_binding(AGENTS_CONFIG)
    infra = file_binding(INFRA_CONFIG)
    preflight = load_json(RUNTIME_PREFLIGHT, "runtime preflight")
    blocked_reasons = list(preflight.get("blocked_reasons") or [])
    config_text = AGENTS_CONFIG.read_text(encoding="utf-8") + "\n" + INFRA_CONFIG.read_text(
        encoding="utf-8"
    )
    placeholders = _placeholder_markers(config_text)
    bindings: dict[str, Any] = {"agents": agents, "infra": infra}
    custom_ready = False
    if custom_config is not None:
        custom_config = custom_config.resolve()
        try:
            custom_config.relative_to(REPO_ROOT.resolve())
        except ValueError as exc:
            raise RepairPipelineError("custom runtime config must stay inside the repository") from exc
        custom = load_json(custom_config, "custom runtime config")
        custom_text = custom_config.read_text(encoding="utf-8")
        custom_markers = _placeholder_markers(custom_text)
        if custom_markers:
            raise RepairPipelineError("custom runtime config contains placeholder markers")
        validate_custom_execution_payload(
            custom,
            preflight=preflight,
            base_bindings={"agents": agents, "infra": infra},
        )
        custom_ready = True
        bindings["custom_execution"] = file_binding(custom_config) | {
            "config_sha256": custom.get("config_sha256"),
            "schema_version": custom.get("schema_version"),
            "declared_status": custom.get("status"),
            "declared_execution_eligible": custom.get("execution_eligible"),
            "placeholder_markers": custom_markers,
        }
    preflight_ready = (
        preflight.get("schema_version") == "androidworld_runtime_preflight/v1"
        and preflight.get("status") == "pass"
        and not blocked_reasons
        and isinstance(preflight.get("source_commit"), str)
        and bool(re.fullmatch(r"[0-9a-f]{40}", preflight["source_commit"]))
        and preflight.get("pip_check_returncode") == 0
        and preflight.get("runtime_checkout_tracked_changes") == []
        and preflight.get("runtime_checkout_untracked_top_level") == []
        and bool(preflight.get("registered_avds"))
        and bool(preflight.get("adb_devices"))
    )
    base_placeholder_free = not placeholders
    eligible = preflight_ready and custom_ready and base_placeholder_free
    runtime = {
        "status": "ready" if eligible else "runtime_preflight_pending",
        "configuration_bindings": bindings,
        "configuration_placeholder_markers": placeholders,
        "base_configuration_placeholder_free": base_placeholder_free,
        "custom_execution_config_required": True,
        "custom_execution_config_validated": custom_ready,
        "runtime_preflight": file_binding(RUNTIME_PREFLIGHT)
        | {
            "schema_version": preflight.get("schema_version"),
            "declared_status": preflight.get("status"),
            "blocked_reasons": blocked_reasons,
            "strict_readiness_passed": preflight_ready,
        },
        "execution_eligible": eligible,
        "scoring_eligible": False,
    }
    runtime["runtime_bindings_sha256"] = object_sha256(runtime)
    return runtime, eligible


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RepairPipelineError(f"invalid JSONL {path}:{number}") from exc
        if not isinstance(value, dict):
            raise RepairPipelineError(f"JSONL row {path}:{number} is not an object")
        rows.append(value)
    return rows
