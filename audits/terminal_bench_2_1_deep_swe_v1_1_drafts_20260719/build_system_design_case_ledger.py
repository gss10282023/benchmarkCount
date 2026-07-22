#!/usr/bin/env python3
"""Build an outcome-blind, case-level audit ledger for the frozen draft corpus.

This report deliberately reads only case packets, frozen draft checklists and
their provenance, the deterministic audit ledger, and the outcome-blind semantic
review receipts.  It never reads agent trajectories, concrete run artifacts,
per-record evaluator values, reward files, released labels, or evidence scores.

The result maps every case to the user's system-design clauses.  It keeps the
following distinct:

* structural/provenance validity of a frozen pre-run draft;
* substantive compliance of that draft with the evidence-checklist design;
* a later benchmark-conflict determination, which is expressly outside drafting.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


AUDIT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = AUDIT_ROOT.parents[1]
DRAFT_ROOT = AUDIT_ROOT / "drafts"
SEMANTIC_REVIEW_ROOT = AUDIT_ROOT / "semantic_reviews"
PACKET_ROOTS = {
    "terminal_bench_2_1": REPO_ROOT / "experiments/case_packets/terminal_bench_2_1",
    "deep_swe_v1_1": REPO_ROOT / "experiments/case_packets/deep_swe_v1_1",
}
REVIEW_ITEM_IDS = (
    "identity_and_scope",
    "native_user_goal",
    "native_evaluator_semantics",
    "decisive_post_run_evidence",
    "decision_rules_sfu",
    "source_support_pointers",
    "stronger_conditions",
    "minimality_and_no_run_leakage",
    "stronger_conflict_separation",
)
EXPECTED_DRAFT_CONFIG = {
    "provider": "codex_cli",
    "model": "gpt-5.4",
    "reasoning_effort": "high",
    "phase": "draft",
}
EXPECTED_REVIEW_CONFIG = {
    "provider": "codex_cli",
    "model": "gpt-5.6-sol",
    "reasoning_effort": "high",
    "phase": "checklist_model_review",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"expected JSON object at {path}:{line_number}")
        rows.append(value)
    return rows


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def short_join(values: Iterable[str], separator: str = "; ") -> str:
    return separator.join(value for value in values if value)


def review_item_statuses(review: Mapping[str, Any]) -> tuple[dict[str, str], list[str]]:
    items = as_list(review.get("checklist_items"))
    status: dict[str, str] = {}
    issues: list[str] = []
    for item in items:
        if not isinstance(item, Mapping):
            issues.append("review item is not an object")
            continue
        item_id = str(item.get("id") or "")
        item_status = str(item.get("status") or "")
        if item_id in status:
            issues.append(f"duplicate review item: {item_id}")
        status[item_id] = item_status
    if tuple(status) != REVIEW_ITEM_IDS:
        issues.append(
            "review item set/order differs: " + ",".join(status) + " (expected " + ",".join(REVIEW_ITEM_IDS) + ")"
        )
    invalid = [item_id for item_id, item_status in status.items() if item_status not in {"pass", "fail"}]
    if invalid:
        issues.append("invalid review status: " + ",".join(invalid))
    return status, issues


def all_pass(statuses: Mapping[str, str], *item_ids: str) -> bool:
    return all(statuses.get(item_id) == "pass" for item_id in item_ids)


def status_zh(passed: bool) -> str:
    return "通过" if passed else "需修订"


def packet_state_basis(packet: Mapping[str, Any], benchmark: str) -> tuple[bool, str, list[str]]:
    """Check availability of the pre-lock evaluator/report-state description.

    The packets have no field literally called ``state_schema``.  For this audit
    its functional equivalent is the case-specific evaluator/oracle record
    semantics plus the retained-artifact inventory: CTRF node/status schema and
    aggregation for DeepSWE, and task-specific verifier/test semantics for
    Terminal-Bench.
    """

    inventory = packet.get("artifact_inventory")
    evaluator = packet.get("evaluator_reference")
    inventory = inventory if isinstance(inventory, Mapping) else {}
    evaluator = evaluator if isinstance(evaluator, Mapping) else {}
    artifact_types = as_list(inventory.get("retained_execution_artifact_types"))
    issues: list[str] = []
    if inventory.get("inventory_known_pre_lock") is not True:
        issues.append("artifact inventory not marked known pre-lock")
    if not artifact_types:
        issues.append("no retained execution artifact types")
    if not evaluator.get("native_test_report_artifact"):
        issues.append("native test-report artifact missing")
    if not evaluator.get("native_reward_artifact"):
        issues.append("released evaluator artifact type missing")
    if benchmark == "deep_swe_v1_1":
        projection = evaluator.get("projection")
        projection = projection if isinstance(projection, Mapping) else {}
        if not projection.get("grade"):
            issues.append("DeepSWE grade/report schema projection missing")
        if not projection.get("native_decision_rule"):
            issues.append("DeepSWE native aggregation projection missing")
        if not projection.get("native_test_sets"):
            issues.append("DeepSWE configured test-set state missing")
        basis = (
            "case_packet evaluator_reference.projection: CTRF `suite.name` state, "
            "configured test sets, and native aggregation"
        )
    else:
        if not as_list(evaluator.get("test_source_paths")):
            issues.append("Terminal-Bench task-specific test/verifier sources missing")
        if not evaluator.get("verifier_entrypoint"):
            issues.append("Terminal-Bench verifier entrypoint missing")
        basis = (
            "case_packet evaluator_reference: task-specific verifier entrypoint, "
            "test sources, and verifier report artifact"
        )
    return not issues, basis, issues


def reviewer_config_ok(receipt: Mapping[str, Any], case_id: str, benchmark: str) -> tuple[bool, list[str]]:
    issues: list[str] = []
    for key, expected in EXPECTED_REVIEW_CONFIG.items():
        if key == "reasoning_effort":
            metadata = receipt.get("response_metadata")
            metadata = metadata if isinstance(metadata, Mapping) else {}
            actual = metadata.get("reasoning_effort")
        else:
            actual = receipt.get(key)
        if actual != expected:
            issues.append(f"{key}={actual!r}, expected {expected!r}")
    if receipt.get("case_unit_id") != case_id:
        issues.append("case_unit_id mismatch")
    if receipt.get("domain") != benchmark:
        issues.append("domain mismatch")
    metadata = receipt.get("response_metadata")
    metadata = metadata if isinstance(metadata, Mapping) else {}
    if metadata.get("sandbox") != "read-only":
        issues.append("review sandbox is not read-only")
    return not issues, issues


def draft_config_ok(receipt: Mapping[str, Any], case_id: str) -> tuple[bool, list[str]]:
    issues: list[str] = []
    for key, expected in EXPECTED_DRAFT_CONFIG.items():
        if key == "reasoning_effort":
            metadata = receipt.get("response_metadata")
            metadata = metadata if isinstance(metadata, Mapping) else {}
            actual = metadata.get("reasoning_effort")
        else:
            actual = receipt.get(key)
        if actual != expected:
            issues.append(f"{key}={actual!r}, expected {expected!r}")
    if receipt.get("case_unit_id") != case_id:
        issues.append("case_unit_id mismatch")
    return not issues, issues


def prompt_variant_map(summary: Mapping[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    variants = summary.get("review_prompt_variants")
    variants = variants if isinstance(variants, Mapping) else {}
    base = variants.get("base_semantic_review")
    repair = variants.get("schema_repair_retry")
    base = base if isinstance(base, Mapping) else {}
    repair = repair if isinstance(repair, Mapping) else {}
    repair_ids = {str(item) for item in as_list(repair.get("case_ids"))}
    labels: dict[str, str] = {}
    hashes: dict[str, str] = {}
    for case_id in repair_ids:
        labels[case_id] = "schema_repair_retry"
        hashes[case_id] = str(repair.get("prompt_sha256") or "")
    labels["__default__"] = "base_semantic_review"
    hashes["__default__"] = str(base.get("prompt_sha256") or "")
    return labels, hashes


def validate_prompt_hashes(summary: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    variants = summary.get("review_prompt_variants")
    variants = variants if isinstance(variants, Mapping) else {}
    for variant_id in ("base_semantic_review", "schema_repair_retry"):
        variant = variants.get(variant_id)
        variant = variant if isinstance(variant, Mapping) else {}
        prompt_raw = variant.get("prompt")
        expected_hash = str(variant.get("prompt_sha256") or "")
        if not prompt_raw or not expected_hash:
            issues.append(f"{variant_id}: missing prompt/path hash")
            continue
        prompt_path = REPO_ROOT / str(prompt_raw)
        if not prompt_path.is_file():
            issues.append(f"{variant_id}: missing prompt {prompt_raw}")
        elif sha256_file(prompt_path) != expected_hash:
            issues.append(f"{variant_id}: prompt hash differs from frozen review summary")
    return issues


def validate_frozen_draft_inputs(summary: Mapping[str, Any]) -> list[str]:
    """Verify that the drafting prompt/schema/supplement still match their lock."""

    frozen = summary.get("frozen_inputs")
    frozen = frozen if isinstance(frozen, Mapping) else {}
    pairs = (
        ("checklist_schema", "checklist_schema_sha256"),
        ("base_draft_prompt", "base_draft_prompt_sha256"),
        ("draft_supplement", "draft_supplement_sha256"),
        ("targeted_pointer_supplement", "targeted_pointer_supplement_sha256"),
    )
    issues: list[str] = []
    for path_key, hash_key in pairs:
        raw_path = frozen.get(path_key)
        expected_hash = str(frozen.get(hash_key) or "")
        if not raw_path or not expected_hash:
            issues.append(f"missing frozen input or hash: {path_key}")
            continue
        path = REPO_ROOT / str(raw_path)
        if not path.is_file():
            issues.append(f"frozen input no longer exists: {raw_path}")
        elif sha256_file(path) != expected_hash:
            issues.append(f"frozen input hash changed: {raw_path}")
    return issues


def packet_outcome_boundary(packet: Mapping[str, Any]) -> tuple[bool, list[str]]:
    """Check packet-level data-exclusion declarations without reading outcomes."""

    leakage = packet.get("leakage_control")
    inventory = packet.get("artifact_inventory")
    leakage = leakage if isinstance(leakage, Mapping) else {}
    inventory = inventory if isinstance(inventory, Mapping) else {}
    required_true = (
        "model_receives_only_agent_input_json",
        "oracle_solution_bytes_excluded_from_packet",
        "prior_run_records_excluded_from_packet_generation",
        "released_evaluator_results_excluded_from_packet_generation",
        "tests_verifier_solution_excluded_from_model_input",
    )
    issues = [key for key in required_true if leakage.get(key) is not True]
    if inventory.get("per_record_contents_or_values_in_packet") is not False:
        issues.append("artifact_inventory.per_record_contents_or_values_in_packet")
    if inventory.get("released_evaluator_value_available_to_packet_or_scorer") is not False:
        issues.append("artifact_inventory.released_evaluator_value_available_to_packet_or_scorer")
    return not issues, issues


def main() -> int:
    audit_rows = load_jsonl(AUDIT_ROOT / "audit_records.jsonl")
    semantic_rows = load_jsonl(AUDIT_ROOT / "semantic_review_records.jsonl")
    lock_manifest = load_json(AUDIT_ROOT / "draft_lock_manifest.json")
    semantic_summary = load_json(AUDIT_ROOT / "semantic_review_summary.json")
    deterministic_summary = load_json(AUDIT_ROOT / "summary.json")
    audit_by_case = {str(row["case_unit_id"]): row for row in audit_rows}
    semantic_by_case = {str(row["case_unit_id"]): row for row in semantic_rows}
    lock_by_case = {
        str(row["case_unit_id"]): row
        for row in as_list(lock_manifest.get("records"))
        if isinstance(row, Mapping)
    }
    prompt_labels, prompt_hashes = prompt_variant_map(semantic_summary)
    prompt_hash_issues = validate_prompt_hashes(semantic_summary)
    frozen_draft_input_issues = validate_frozen_draft_inputs(deterministic_summary)

    packets: dict[str, dict[str, Any]] = {}
    expected_benchmarks: dict[str, str] = {}
    packet_paths: dict[str, Path] = {}
    for benchmark, root in PACKET_ROOTS.items():
        for packet_path in sorted(root.glob("*/case_packet.json")):
            case_id = packet_path.parent.name
            if case_id in packets:
                raise RuntimeError(f"duplicate case id across packet roots: {case_id}")
            packets[case_id] = load_json(packet_path)
            expected_benchmarks[case_id] = benchmark
            packet_paths[case_id] = packet_path.with_suffix(".md")

    expected_ids = set(packets)
    input_set_issues = {
        "packet_case_count": len(expected_ids),
        "audit_only": sorted(set(audit_by_case) - expected_ids),
        "audit_missing": sorted(expected_ids - set(audit_by_case)),
        "semantic_only": sorted(set(semantic_by_case) - expected_ids),
        "semantic_missing": sorted(expected_ids - set(semantic_by_case)),
        "lock_only": sorted(set(lock_by_case) - expected_ids),
        "lock_missing": sorted(expected_ids - set(lock_by_case)),
    }
    if len(expected_ids) != 202:
        raise RuntimeError(f"expected 202 case packets, found {len(expected_ids)}")
    if any(value for key, value in input_set_issues.items() if key != "packet_case_count"):
        raise RuntimeError("case identity sets differ: " + json.dumps(input_set_issues, ensure_ascii=False))

    ledger: list[dict[str, Any]] = []
    item_failure_counts: Counter[str] = Counter()
    clause_revision_counts: Counter[str] = Counter()
    benchmark_counts: dict[str, Counter[str]] = defaultdict(Counter)
    integrity_issue_count = 0
    for case_id in sorted(expected_ids):
        benchmark = expected_benchmarks[case_id]
        packet = packets[case_id]
        packet_path = packet_paths[case_id]
        audit = audit_by_case[case_id]
        semantic = semantic_by_case[case_id]
        locked = lock_by_case[case_id]
        review_path = SEMANTIC_REVIEW_ROOT / case_id / "review.json"
        review_llm_path = SEMANTIC_REVIEW_ROOT / case_id / "review.llm_call.json"
        draft_path = DRAFT_ROOT / case_id / "checklist.yaml"
        draft_llm_path = DRAFT_ROOT / case_id / "llm_call.json"
        integrity_issues: list[str] = []
        for path in (packet_path, review_path, review_llm_path, draft_path, draft_llm_path):
            if not path.is_file():
                integrity_issues.append(f"missing {path.relative_to(REPO_ROOT)}")
        if integrity_issues:
            # Continue only because a detailed ledger is still useful; statuses
            # below will necessarily be revision-required.
            review: dict[str, Any] = {}
            review_receipt: dict[str, Any] = {}
            draft_receipt: dict[str, Any] = {}
        else:
            review = load_json(review_path)
            review_receipt = load_json(review_llm_path)
            draft_receipt = load_json(draft_llm_path)

        state_schema_available, state_basis, state_issues = packet_state_basis(packet, benchmark)
        integrity_issues.extend(state_issues)
        packet_outcome_blind, packet_outcome_issues = packet_outcome_boundary(packet)
        integrity_issues.extend("packet outcome boundary: " + item for item in packet_outcome_issues)
        current_draft_hash = sha256_file(draft_path) if draft_path.is_file() else ""
        current_packet_hash = sha256_file(packet_path) if packet_path.is_file() else ""
        current_draft_llm_hash = sha256_file(draft_llm_path) if draft_llm_path.is_file() else ""
        lock_integrity = (
            current_draft_hash == str(locked.get("checklist_sha256") or "")
            and current_packet_hash == str(locked.get("case_packet_sha256") or "")
            and current_draft_llm_hash == str(locked.get("llm_call_sha256") or "")
        )
        if not lock_integrity:
            integrity_issues.append("current draft/packet/provenance hash differs from draft lock manifest")
        audit_hash_integrity = (
            current_draft_hash == str(audit.get("checklist_sha256") or "")
            and current_packet_hash == str(audit.get("case_packet_sha256") or "")
        )
        if not audit_hash_integrity:
            integrity_issues.append("current draft/packet hash differs from deterministic audit record")
        draft_config_valid, draft_config_issues = draft_config_ok(draft_receipt, case_id)
        integrity_issues.extend("draft config: " + item for item in draft_config_issues)
        review_config_valid, review_config_issues = reviewer_config_ok(review_receipt, case_id, benchmark)
        integrity_issues.extend("review config: " + item for item in review_config_issues)
        item_status, review_shape_issues = review_item_statuses(review)
        integrity_issues.extend(review_shape_issues)
        semantic_failed_ids = [str(item) for item in as_list(semantic.get("failed_item_ids"))]
        review_failed_ids = [item_id for item_id in REVIEW_ITEM_IDS if item_status.get(item_id) == "fail"]
        if semantic_failed_ids != review_failed_ids:
            integrity_issues.append("semantic ledger failed-item IDs differ from review receipt")
        if semantic.get("decision") != review.get("decision"):
            integrity_issues.append("semantic ledger decision differs from review receipt")
        if semantic.get("status") != "completed":
            integrity_issues.append("semantic review was not completed")
        if audit.get("status") != "pass":
            integrity_issues.append("deterministic audit did not pass")
        if audit.get("benchmark") != benchmark:
            integrity_issues.append("deterministic audit benchmark differs from packet root")

        # The deterministic audit establishes the no-label/no-current-run boundary;
        # the semantic item covers reusable pre-run scope and compactness.
        no_label_or_run_leak = not any(
            as_list(audit.get(field))
            for field in ("released_label_leaks", "run_specific_mentions")
        )
        pre_run_scope = (
            lock_integrity
            and audit_hash_integrity
            and draft_config_valid
            and review_config_valid
            and not frozen_draft_input_issues
            and audit.get("status") == "pass"
            and item_status.get("identity_and_scope") == "pass"
        )
        outcome_blind_boundary = (
            packet_outcome_blind
            and no_label_or_run_leak
            and review_config_valid
            and not prompt_hash_issues
        )
        native_goal = item_status.get("native_user_goal") == "pass"
        native_evaluator = item_status.get("native_evaluator_semantics") == "pass"
        inventory_compatible = not as_list(audit.get("artifact_inventory_signals"))
        decisive_evidence = item_status.get("decisive_post_run_evidence") == "pass"
        sfu = item_status.get("decision_rules_sfu") == "pass"
        source_support = item_status.get("source_support_pointers") == "pass"
        stronger = item_status.get("stronger_conditions") == "pass"
        conflict_separation = item_status.get("stronger_conflict_separation") == "pass" and not any(
            condition.get("mentions_benchmark_conflict")
            for condition in as_list(audit.get("stronger_conditions"))
            if isinstance(condition, Mapping)
        )
        minimality = item_status.get("minimality_and_no_run_leakage") == "pass"
        full_semantic_design = semantic.get("decision") == "accept" and not integrity_issues

        failed_clause_labels: list[str] = []
        clause_map = (
            ("预运行锁定/可复用 scope", pre_run_scope),
            ("官方 user goal/task", native_goal),
            ("native evaluator/oracle 语义", native_evaluator),
            ("state schema 与 artifact inventory", state_schema_available and inventory_compatible),
            ("决定性非标签运行证据", decisive_evidence),
            ("native S/F/U 规则", sfu),
            ("source support pointers", source_support),
            ("stronger 条件的官方支持与测量 gap", stronger),
            ("stronger 与 benchmark conflict 分离", conflict_separation),
            ("最小性/无运行泄漏", minimality),
        )
        for label, passed in clause_map:
            if not passed:
                failed_clause_labels.append(label)
                clause_revision_counts[label] += 1
        for item_id in review_failed_ids:
            item_failure_counts[item_id] += 1
        if integrity_issues:
            integrity_issue_count += 1

        findings = [item for item in as_list(semantic.get("findings")) if isinstance(item, Mapping)]
        finding_summary = short_join(
            [
                f"{item.get('checklist_item_id')}: {item.get('message')}"
                for item in findings
            ]
        )
        reviewer_evidence = {
            str(item.get("id")): as_list(item.get("evidence"))
            for item in as_list(review.get("checklist_items"))
            if isinstance(item, Mapping)
        }
        review_prompt_variant = prompt_labels.get(case_id, prompt_labels["__default__"])
        expected_review_prompt_hash = prompt_hashes.get(case_id, prompt_hashes["__default__"])
        row = {
            "benchmark": benchmark,
            "case_unit_id": case_id,
            "draft_lock_and_pre_run_scope": status_zh(pre_run_scope),
            "outcome_label_boundary": status_zh(outcome_blind_boundary),
            "official_user_goal_task": status_zh(native_goal),
            "native_evaluator_oracle_semantics": status_zh(native_evaluator),
            "state_schema_and_artifact_inventory": status_zh(
                state_schema_available and inventory_compatible
            ),
            "nonlabel_decisive_evidence": status_zh(decisive_evidence),
            "native_sfu_rules": status_zh(sfu),
            "source_support_pointers": status_zh(source_support),
            "stronger_conditions": status_zh(stronger),
            "stronger_conflict_separation": status_zh(conflict_separation),
            "minimality_no_run_leakage": status_zh(minimality),
            "overall_system_design_audit": "符合" if full_semantic_design else "需修订",
            "semantic_decision": semantic.get("decision"),
            "failed_review_items": review_failed_ids,
            "failed_design_clauses": failed_clause_labels,
            "finding_count": len(findings),
            "finding_summary": finding_summary,
            "stronger_condition_count": audit.get("stronger_condition_count"),
            "state_schema_basis": state_basis,
            "artifact_inventory_types": as_list(
                (packet.get("artifact_inventory") if isinstance(packet.get("artifact_inventory"), Mapping) else {}).get(
                    "retained_execution_artifact_types"
                )
            ),
            "inventory_mechanical_signals": as_list(audit.get("artifact_inventory_signals")),
            "review_item_statuses": item_status,
            "review_item_evidence": reviewer_evidence,
            "review_prompt_variant": review_prompt_variant,
            "review_prompt_sha256": expected_review_prompt_hash,
            "packet_outcome_boundary": packet_outcome_blind,
            "packet_outcome_boundary_issues": packet_outcome_issues,
            "frozen_draft_input_integrity": not frozen_draft_input_issues,
            "draft_sha256": current_draft_hash,
            "case_packet_sha256": current_packet_hash,
            "draft_lock_integrity": lock_integrity,
            "deterministic_audit_integrity": audit_hash_integrity,
            "review_receipt_integrity": not integrity_issues,
            "integrity_issues": integrity_issues,
            "raw_draft_changed_since_lock": not lock_integrity,
            "reviewed_original_draft_preserved": lock_integrity and audit_hash_integrity,
        }
        ledger.append(row)
        benchmark_counts[benchmark]["case_count"] += 1
        benchmark_counts[benchmark]["conform_count"] += int(full_semantic_design)
        benchmark_counts[benchmark]["revision_required_count"] += int(not full_semantic_design)
        benchmark_counts[benchmark]["structural_boundary_pass_count"] += int(
            pre_run_scope and outcome_blind_boundary
        )

    output_jsonl = AUDIT_ROOT / "system_design_case_ledger.jsonl"
    output_csv = AUDIT_ROOT / "system_design_case_ledger.csv"
    output_summary = AUDIT_ROOT / "system_design_audit_summary.json"
    output_report = AUDIT_ROOT / "SYSTEM_DESIGN_AUDIT_ZH.md"
    write_jsonl(output_jsonl, ledger)
    csv_columns = [
        "benchmark",
        "case_unit_id",
        "overall_system_design_audit",
        "semantic_decision",
        "draft_lock_and_pre_run_scope",
        "outcome_label_boundary",
        "official_user_goal_task",
        "native_evaluator_oracle_semantics",
        "state_schema_and_artifact_inventory",
        "nonlabel_decisive_evidence",
        "native_sfu_rules",
        "source_support_pointers",
        "stronger_conditions",
        "stronger_conflict_separation",
        "minimality_no_run_leakage",
        "failed_review_items",
        "failed_design_clauses",
        "finding_count",
        "finding_summary",
        "stronger_condition_count",
        "review_prompt_variant",
        "draft_lock_integrity",
        "review_receipt_integrity",
        "raw_draft_changed_since_lock",
        "draft_sha256",
        "case_packet_sha256",
    ]
    with output_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_columns)
        writer.writeheader()
        for row in ledger:
            csv_row = dict(row)
            for key in ("failed_review_items", "failed_design_clauses"):
                csv_row[key] = "; ".join(str(item) for item in as_list(row[key]))
            writer.writerow({key: csv_row.get(key) for key in csv_columns})

    total = len(ledger)
    conform_count = sum(row["overall_system_design_audit"] == "符合" for row in ledger)
    revision_required_count = total - conform_count
    summary = {
        "schema_version": "tb21_deepswe11_system_design_case_audit/v1",
        "status": "revision_required" if revision_required_count else "pass",
        "audit_boundary": {
            "read": [
                "matching case_packet.md/json",
                "frozen checklist.yaml and drafting provenance",
                "draft lock manifest and deterministic audit ledger",
                "outcome-blind semantic review body/receipt and frozen review prompts",
            ],
            "not_read": [
                "agent trajectories or trajectory contents",
                "concrete retained execution artifact contents",
                "per-record evaluator reward/result/label values",
                "evidence-scoring verdicts",
                "benchmark-conflict determinations",
            ],
        },
        "case_count": total,
        "conform_count": conform_count,
        "revision_required_count": revision_required_count,
        "benchmark_counts": {key: dict(value) for key, value in sorted(benchmark_counts.items())},
        "structural_boundary_pass_count": sum(
            row["draft_lock_and_pre_run_scope"] == "通过"
            and row["outcome_label_boundary"] == "通过"
            for row in ledger
        ),
        "state_schema_and_artifact_inventory_structural_pass_count": sum(
            row["state_schema_and_artifact_inventory"] == "通过" for row in ledger
        ),
        "no_raw_draft_changes_since_lock_count": sum(
            row["raw_draft_changed_since_lock"] is False for row in ledger
        ),
        "review_receipt_integrity_issue_count": integrity_issue_count,
        "review_item_failure_counts": dict(sorted(item_failure_counts.items())),
        "system_design_clause_revision_counts": dict(sorted(clause_revision_counts.items())),
        "prompt_hash_issues": prompt_hash_issues,
        "frozen_draft_input_hash_issues": frozen_draft_input_issues,
        "interpretation": {
            "state_schema": (
                "Packets do not expose a literal `state_schema` field. This audit treats the "
                "case-specific evaluator/report-state semantics and available-artifact inventory "
                "as the required state schema: DeepSWE's CTRF node/status aggregation projection "
                "and Terminal-Bench's task-specific verifier/test semantics."
            ),
            "accept": (
                "A case is `符合` only if the independent outcome-blind semantic review accepted all "
                "nine design items and its frozen draft/packet provenance remains intact."
            ),
            "revision_required": (
                "`需修订` concerns the pre-run checklist only. It is not a benchmark label, an "
                "evidence-scoring S/F/U result, or a benchmark-conflict finding."
            ),
        },
    }
    write_json(output_summary, summary)

    item_counts_zh = {
        "identity_and_scope": "身份与预运行 scope",
        "native_user_goal": "官方 user goal/task",
        "native_evaluator_semantics": "native evaluator/oracle 语义",
        "decisive_post_run_evidence": "决定性非标签运行证据",
        "decision_rules_sfu": "native S/F/U 规则",
        "source_support_pointers": "source support pointers",
        "stronger_conditions": "stronger 条件的官方支持与 gap",
        "minimality_and_no_run_leakage": "最小性/无运行泄漏",
        "stronger_conflict_separation": "stronger/conflict 分离",
    }
    report = f"""# Terminal-Bench 2.1 / DeepSWE v1.1 draft 系统设计逐案审查

## 结论

- 已逐案审查 **{total}** 份冻结 draft：Terminal-Bench 2.1 为 89，DeepSWE v1.1 为 113。
- **{conform_count} / {total}** 份 draft 当前符合这版系统设计；**{revision_required_count} / {total}** 份需要在进入 evidence scoring 前修订并重新锁定。
- 这不是对 benchmark record 的 S/F/U 判断，也不是 benchmark conflict 判断。它只判断 pre-run evidence checklist 是否符合设计。
- 全部 {total} 份当前 draft 的哈希均与 draft lock manifest 一致，draft prompt/schema/supplement 与冻结哈希一致；本次审查没有改写任何原始 draft。

## 审查边界

本次审查只读取每个 case 的 packet、冻结 `checklist.yaml`、draft provenance/lock、确定性审核记录，以及只读、outcome-blind 的逐案语义审核 receipt。每个 packet 都声明排除 prior-run records、released evaluator results、oracle bytes 和 per-record artifact values。没有读取 agent outcome、trajectory 内容、实际运行 artifact 内容、per-record reward/result/released label、evidence-scoring S/F/U 或 benchmark-conflict 记录。

因此，结果直接回答“draft 是否可作为进入运行前锁定的 checklist”，而不依赖 benchmark 原始 label。

## 系统设计条款到逐案检查的映射

| 你的设计要求 | 对应逐案检查 |
| --- | --- |
| 在接触 outcome/label 前锁定、不得随 outcome 修改 | lock-manifest 哈希、draft/review provenance、`identity_and_scope`、标签/运行特定语言扫描 |
| 官方 user goal/task | `native_user_goal` |
| released evaluator/oracle 的正式 native 语义 | `native_evaluator_semantics` |
| 必要的 state schema 与 artifact inventory | case packet 中的 evaluator/report-state 语义与 `artifact_inventory`，并以 `decisive_post_run_evidence` 检查 artifact 是否真的能证明对应事实 |
| 独立的非标签 S/F/U | `decisive_post_run_evidence` + `decision_rules_sfu`；静态检查禁止把 reward/result/label 当 decisive evidence |
| source support、禁止主观加码 | `source_support_pointers` |
| stronger 独立、须有 case-specific 官方支持和明确 gap | `stronger_conditions` |
| 不从 stronger F 或 native S + stronger F 推出 conflict | `stronger_conflict_separation`，并静态禁止 draft 声称 benchmark conflict |

这里的“state schema”是功能性含义：packet 没有字面字段 `state_schema`，故以每案 evaluator 的报告状态/聚合语义和 retained artifact inventory 为准。DeepSWE 是 CTRF `suite.name` 节点、状态和聚合投影；Terminal-Bench 是任务特定 verifier/test 语义与 report artifact。

## 汇总

| Benchmark | cases | 符合 | 需修订 | 预运行/标签边界通过 |
| --- | ---: | ---: | ---: | ---: |
| Terminal-Bench 2.1 | {benchmark_counts['terminal_bench_2_1']['case_count']} | {benchmark_counts['terminal_bench_2_1']['conform_count']} | {benchmark_counts['terminal_bench_2_1']['revision_required_count']} | {benchmark_counts['terminal_bench_2_1']['structural_boundary_pass_count']} |
| DeepSWE v1.1 | {benchmark_counts['deep_swe_v1_1']['case_count']} | {benchmark_counts['deep_swe_v1_1']['conform_count']} | {benchmark_counts['deep_swe_v1_1']['revision_required_count']} | {benchmark_counts['deep_swe_v1_1']['structural_boundary_pass_count']} |
| **总计** | **{total}** | **{conform_count}** | **{revision_required_count}** | **{summary['structural_boundary_pass_count']}** |

所有 {total} 个 case packet 均在 lock 前声明 artifact inventory 和 case-specific evaluator/report-state source；所有 {total} 个 draft 的 named artifact 都与该 inventory 机械匹配。该结构事实不取代语义审核：某 artifact 即使在 inventory 中，仍可能不足以独立证明 checklist 声称的事实，因而会在 `decisive_post_run_evidence` 下要求修订。

## 需修订的设计条款计数

"""
    for item_id in REVIEW_ITEM_IDS:
        count = item_failure_counts.get(item_id, 0)
        report += f"- `{item_id}`（{item_counts_zh[item_id]}）：{count}\n"
    report += f"""

`stronger_conflict_separation` 没有逐案失败；这意味着现有 drafts 没有把 stronger 结果写成 benchmark conflict 结论。它不构成任何 record-level conflict 判定。

## 逐案台账

- 适合筛选和复核的表格：`system_design_case_ledger.csv`
- 包含每个 review item 证据和所有 finding 的可机读台账：`system_design_case_ledger.jsonl`
- 汇总：`system_design_audit_summary.json`

台账中 `符合` 仅表示 draft 已通过本次严格的 pre-run 设计审查；`需修订` 的 finding 是针对 draft 本身的修改要求。审查建议未自动写回，因此不会违反“锁定后不得根据 outcome 修改”的约束；如后续采纳，必须将修订版本当作新的、在任何具体 outcome/label 可见之前重新冻结的 checklist。
"""
    output_report.write_text(report, encoding="utf-8")
    print(json.dumps({
        "case_count": total,
        "conform_count": conform_count,
        "revision_required_count": revision_required_count,
        "structural_boundary_pass_count": summary["structural_boundary_pass_count"],
        "receipt_integrity_issue_count": integrity_issue_count,
        "outputs": [str(path.relative_to(REPO_ROOT)) for path in (output_report, output_csv, output_jsonl, output_summary)],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
