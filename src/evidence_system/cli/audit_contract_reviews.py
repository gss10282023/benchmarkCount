"""Interactive, auditable human review for evidence-contract drafts."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from evidence_system.contracts.common import (
    ContractLifecycleError,
    contract_content_hash,
    display_path,
    iter_json_files,
    load_mapping,
    normalize_domain,
    parse_timestamp,
    write_json,
)
from evidence_system.contracts.review import review_contracts
from evidence_system.core.hashing import sha256_object
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml, validate_object


CHECKLIST = (
    (
        "source_visibility",
        "Drafter visible inputs are restricted to task, policy, evaluator, schema, trace schema, available artifact types, contract template, and native source references; they do not expose agent identity, agent trace, native score, outcome label, evidence label, or UNRESOLVE reason.",
    ),
    (
        "required_artifacts_source_support",
        "Every required artifact is supported by official evaluator semantics, official task text or policy, or schema constraints, and native_aligned_source_support is true for native-aligned requirements.",
    ),
    (
        "success_rule_native_alignment",
        "The success_rule matches the native benchmark evaluator claim and does not add unsupported task, policy, procedural, or annotator-intuition requirements.",
    ),
    (
        "fail_rule_native_alignment",
        "The fail_rule marks FAIL only when evaluator-visible evidence shows the native claim is false or the native security/failure predicate is satisfied; undecidable or missing evidence is not treated as FAIL.",
    ),
    (
        "unresolve_rule_checkable",
        "The unresolve_rule is explicit, checkable, and covers missing, unreadable, schema-invalid, ambiguous, or insufficient evidence needed to decide SUCCESS versus FAIL.",
    ),
    (
        "source_hierarchy_applied",
        "The source hierarchy was applied correctly: official evaluator semantics > official task text or policy > schema constraints needed to interpret evaluator-visible state.",
    ),
    (
        "no_annotator_intuition",
        "The contract does not add requirements based on reviewer or annotator intuition beyond the visible official sources.",
    ),
    (
        "stronger_measurement_handling",
        "Unsupported or stronger task/policy requirements are removed from the native-aligned envelope or marked as stronger_measurement, and stronger_measurement claims are not folded into the native-aligned main result.",
    ),
    (
        "stronger_sidecar_mapping",
        "Every stronger_measurement claim that remains reportable has a sidecar, appendix, or manifest-view mapping with enters_native_aligned_main_envelope=false.",
    ),
    (
        "provenance_and_hashes",
        "The draft has contract_drafting_llm_call_id, contract_draft_id, source_bundle_hash, visible_input_hash, hidden or forbidden input assertion provenance, and stable contract hash metadata.",
    ),
)

FINAL_DECISIONS = ("approve", "needs_changes", "reject")
AUDIT_MODES = ("smoke", "formal")
OFFICIAL_SPLITS_DIR = Path("experiments/official_splits")
VISIBLE_INPUT_SOURCE_LABELS = {
    "task_text": "Original benchmark",
    "official_policy": "Original policy/source note",
    "evaluator_description": "Derived note",
    "evaluator_code": "Original benchmark code",
    "schema": "Structured extraction",
    "trace_schema": "Our schema",
    "available_post_run_artifact_types": "Our taxonomy",
    "native_sources": "Structured provenance",
}


@dataclass(frozen=True)
class AuditPaths:
    drafts: Path
    source_bundle: Path
    llm_log_dir: Path
    human_review_dir: Path
    notes_dir: Path
    reviewed_dir: Path
    review_log_dir: Path
    human_time_dir: Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m evidence_system.cli.audit_contract_reviews")
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--audit-mode", choices=AUDIT_MODES)
    parser.add_argument("--draft", dest="drafts")
    parser.add_argument("--source-bundle")
    parser.add_argument("--llm-log-dir")
    parser.add_argument("--human-review-dir")
    parser.add_argument("--notes-dir")
    parser.add_argument("--reviewed-dir")
    parser.add_argument("--review-log-dir")
    parser.add_argument("--human-time-dir")
    parser.add_argument("--reviewer-name")
    parser.add_argument("--reviewer-id")
    parser.add_argument("--display-limit", type=int, default=12000, help="Characters to display per source/draft section; 0 means no limit.")
    parser.add_argument(
        "--raw-display-limit",
        type=int,
        default=0,
        help="Characters to display per raw benchmark source section; default 0 means no limit.",
    )
    parser.add_argument("--non-interactive", action="store_true", help="Review one contract using command-line decisions.")
    parser.add_argument("--contract-id", help="Required with --non-interactive.")
    parser.add_argument("--decision", choices=FINAL_DECISIONS, help="Required with --non-interactive.")
    parser.add_argument("--all-pass", action="store_true", help="Mark all checklist items pass in --non-interactive mode.")
    parser.add_argument("--note", action="append", default=[], help="Additional note for --non-interactive review.")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.bootstrap_check:
        payload = {
            "name": "audit_contract_reviews",
            "status": "ok",
            "formal_logic": "interactive_contract_human_review",
            "side_effects": "none",
        }
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
        return 0
    try:
        session_started_at = utc_now_iso()
        if args.non_interactive:
            result = _run_non_interactive(args, session_started_at=session_started_at)
            print(json.dumps(result, indent=2, sort_keys=True) if args.json else result)
            return 0
        _run_interactive(args, session_started_at=session_started_at)
        return 0
    except (ContractLifecycleError, KeyboardInterrupt) as exc:
        payload = {"status": "blocked", "reason": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload, file=sys.stderr)
        return 2


def _run_interactive(args: argparse.Namespace, *, session_started_at: str) -> None:
    print("Evidence Contract Human Review CLI")
    print(f"Session started at: {session_started_at}")
    reviewer_name = args.reviewer_name or _prompt_nonempty("Reviewer name")
    reviewer_id = args.reviewer_id or _prompt_nonempty("Reviewer id")
    audit_mode = args.audit_mode or _prompt_choice("Audit mode", AUDIT_MODES)
    paths = _audit_paths(args, audit_mode)

    while True:
        drafts = _load_drafts(paths.drafts)
        audits = _latest_audits(paths.human_review_dir)
        choice = _prompt_choice("Select view", ("unaudited", "audited", "exit"))
        if choice == "exit":
            print("Exiting review CLI.")
            return
        if choice == "audited":
            _show_audited(drafts, audits)
            continue
        unaudited = [draft for draft in drafts if str(draft.get("contract_id")) not in audits]
        if not unaudited:
            print("No unaudited contracts remain.")
            continue
        selected_domain = _select_domain(unaudited)
        if selected_domain is None:
            continue
        selected = _select_contract([draft for draft in unaudited if draft.get("domain") == selected_domain])
        if selected is None:
            continue
        result = _review_one_contract(
            selected,
            paths=paths,
            reviewer_name=reviewer_name,
            reviewer_id=reviewer_id,
            audit_mode=audit_mode,
            session_started_at=session_started_at,
            display_limit=args.display_limit,
            raw_display_limit=args.raw_display_limit,
            interactive=True,
            final_decision=None,
            all_pass=False,
            extra_notes=[],
        )
        print(json.dumps(result, indent=2, sort_keys=True))


def _run_non_interactive(args: argparse.Namespace, *, session_started_at: str) -> dict[str, Any]:
    missing = [
        name
        for name in ("audit_mode", "reviewer_name", "reviewer_id", "contract_id", "decision")
        if not getattr(args, name)
    ]
    if missing:
        raise ContractLifecycleError("--non-interactive missing required arguments: " + ", ".join(missing))
    if not args.all_pass and args.decision == "approve":
        raise ContractLifecycleError("--decision approve requires --all-pass in non-interactive mode")
    paths = _audit_paths(args, str(args.audit_mode))
    drafts = _load_drafts(paths.drafts)
    selected = next((draft for draft in drafts if draft.get("contract_id") == args.contract_id), None)
    if selected is None:
        raise ContractLifecycleError(f"contract_id not found: {args.contract_id}")
    return _review_one_contract(
        selected,
        paths=paths,
        reviewer_name=str(args.reviewer_name),
        reviewer_id=str(args.reviewer_id),
        audit_mode=str(args.audit_mode),
        session_started_at=session_started_at,
        display_limit=args.display_limit,
        raw_display_limit=args.raw_display_limit,
        interactive=False,
        final_decision=str(args.decision),
        all_pass=bool(args.all_pass),
        extra_notes=list(args.note),
    )


def _audit_paths(args: argparse.Namespace, audit_mode: str) -> AuditPaths:
    if audit_mode == "smoke":
        defaults = {
            "drafts": "experiments/smoke/evidence_contracts/drafts",
            "source_bundle": "experiments/smoke/source_bundle_3_per_domain.json",
            "llm_log_dir": "experiments/smoke/logs/llm_calls/contract_drafts",
            "human_review_dir": "experiments/smoke/evidence_contracts/human_reviews",
            "notes_dir": "experiments/smoke/evidence_contracts/review_notes",
            "reviewed_dir": "experiments/smoke/evidence_contracts/reviewed",
            "review_log_dir": "experiments/smoke/evidence_contracts/review_workflows",
            "human_time_dir": "experiments/smoke/human_time/contract_reviews",
        }
    else:
        defaults = {
            "drafts": "experiments/evidence_contracts/drafts",
            "source_bundle": "experiments/evidence_contracts/source_bundles/main_case_units_source_bundle.json",
            "llm_log_dir": "results/logs/llm_calls/contract_drafts",
            "human_review_dir": "results/reviews/contracts/human_reviews",
            "notes_dir": "results/reviews/contracts/review_notes",
            "reviewed_dir": "experiments/evidence_contracts/reviewed",
            "review_log_dir": "results/reviews/contracts/workflows",
            "human_time_dir": "results/human_time/contracts",
        }
    return AuditPaths(
        drafts=resolve_repo_path(args.drafts or defaults["drafts"]),
        source_bundle=resolve_repo_path(args.source_bundle or defaults["source_bundle"]),
        llm_log_dir=resolve_repo_path(args.llm_log_dir or defaults["llm_log_dir"]),
        human_review_dir=resolve_repo_path(args.human_review_dir or defaults["human_review_dir"]),
        notes_dir=resolve_repo_path(args.notes_dir or defaults["notes_dir"]),
        reviewed_dir=resolve_repo_path(args.reviewed_dir or defaults["reviewed_dir"]),
        review_log_dir=resolve_repo_path(args.review_log_dir or defaults["review_log_dir"]),
        human_time_dir=resolve_repo_path(args.human_time_dir or defaults["human_time_dir"]),
    )


def _load_drafts(path: Path) -> list[dict[str, Any]]:
    drafts: list[dict[str, Any]] = []
    for draft_path in iter_json_files([path]):
        draft = load_mapping(draft_path)
        if draft.get("schema_version") != "evidence_contract/v1":
            continue
        draft["__path"] = display_path(draft_path)
        drafts.append(draft)
    return sorted(drafts, key=lambda item: (str(item.get("domain")), str(item.get("case_unit_id"))))


def _latest_audits(path: Path) -> dict[str, Mapping[str, Any]]:
    audits: dict[str, Mapping[str, Any]] = {}
    if not path.exists():
        return audits
    for audit_path in sorted(path.glob("*.json")):
        payload = load_mapping(audit_path)
        if payload.get("schema_version") != "human_review/v1":
            continue
        contract_id = str(payload.get("contract_id") or "")
        if not contract_id:
            continue
        existing = audits.get(contract_id)
        if existing is None or str(payload.get("review_finished_at")) >= str(existing.get("review_finished_at")):
            payload["__path"] = display_path(audit_path)
            audits[contract_id] = payload
    return audits


def _show_audited(drafts: Sequence[Mapping[str, Any]], audits: Mapping[str, Mapping[str, Any]]) -> None:
    if not audits:
        print("No audited contracts yet.")
        return
    by_domain: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    draft_by_id = {str(draft.get("contract_id")): draft for draft in drafts}
    for contract_id, audit in audits.items():
        draft = draft_by_id.get(contract_id, {})
        by_domain[str(draft.get("domain") or audit.get("domain"))].append(audit)
    for domain, items in sorted(by_domain.items()):
        print(f"\n{domain}: {len(items)} audited")
        for item in sorted(items, key=lambda audit: str(audit.get("case_unit_id"))):
            print(
                f"  - {item.get('case_unit_id')} | {item.get('final_decision')} | "
                f"{item.get('reviewer_id')} | {item.get('__path')}"
            )


def _select_domain(drafts: Sequence[Mapping[str, Any]]) -> str | None:
    counts: dict[str, int] = defaultdict(int)
    for draft in drafts:
        counts[str(draft.get("domain"))] += 1
    options = [domain for domain, _ in sorted(counts.items())]
    print("\nUnaudited contracts by benchmark:")
    for index, domain in enumerate(options, 1):
        print(f"  {index}. {domain}: {counts[domain]}")
    print("  0. Back")
    selected = _prompt_index("Select benchmark", len(options), allow_zero=True)
    if selected == 0:
        return None
    return options[selected - 1]


def _select_contract(drafts: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    print("\nUnaudited cases:")
    for index, draft in enumerate(drafts, 1):
        print(f"  {index}. {draft.get('case_unit_id')} | {draft.get('contract_id')}")
    print("  0. Back")
    selected = _prompt_index("Select case", len(drafts), allow_zero=True)
    if selected == 0:
        return None
    return drafts[selected - 1]


def _review_one_contract(
    draft: Mapping[str, Any],
    *,
    paths: AuditPaths,
    reviewer_name: str,
    reviewer_id: str,
    audit_mode: str,
    session_started_at: str,
    display_limit: int,
    raw_display_limit: int,
    interactive: bool,
    final_decision: str | None,
    all_pass: bool,
    extra_notes: Sequence[str],
) -> dict[str, Any]:
    review_started_at = utc_now_iso()
    source = _source_for_contract(paths.source_bundle, str(draft["contract_id"]))
    raw_sources = _raw_benchmark_sources(source, draft)
    llm_call = _llm_call_for_contract(paths.llm_log_dir, str(draft.get("contract_drafting_llm_call_id") or ""))
    if interactive:
        _display_review_material(
            draft,
            source,
            raw_sources,
            llm_call,
            display_limit=display_limit,
            raw_display_limit=raw_display_limit,
        )
    checklist = _collect_checklist(interactive=interactive, all_pass=all_pass)
    if final_decision is None:
        final_decision = _prompt_choice("Final decision", FINAL_DECISIONS)
    if final_decision == "approve" and any(item["result"] != "pass" for item in checklist):
        raise ContractLifecycleError("approve requires every checklist item to pass")
    review_finished_at = finish_after(review_started_at)
    review_id = f"human-review-{_safe_id(draft['contract_id'])}-{_timestamp_id(review_finished_at)}"
    notes_payload = _notes_payload(
        draft,
        source,
        llm_call,
        review_id=review_id,
        reviewer_name=reviewer_name,
        reviewer_id=reviewer_id,
        audit_mode=audit_mode,
        session_started_at=session_started_at,
        review_started_at=review_started_at,
        review_finished_at=review_finished_at,
        checklist=checklist,
        final_decision=final_decision,
        extra_notes=extra_notes,
        raw_sources=raw_sources,
        raw_sources_displayed=interactive,
    )
    notes_path = write_json(paths.notes_dir / f"{review_id}.checklist.json", notes_payload)

    reviewed_contract_path: str | None = None
    review_workflow_path: str | None = None
    output_contract_hash = str(draft.get("contract_hash") or contract_content_hash(draft))
    human_time_path: str | None = None
    if final_decision == "approve":
        review_result = review_contracts(
            drafts=[str(resolve_repo_path(draft["__path"]))],
            reviewed_dir=paths.reviewed_dir,
            review_log_dir=paths.review_log_dir,
            human_time_dir=paths.human_time_dir,
            reviewer_id=reviewer_id,
            review_started_at=review_started_at,
            review_finished_at=review_finished_at,
            review_actions=_review_actions(checklist, final_decision),
            source_bundle_hash=_source_support_hash(draft, "source_bundle_hash"),
            visible_input_hash=_source_support_hash(draft, "visible_input_hash"),
            source_hierarchy_applied=[
                "official evaluator semantics",
                "official task text / policy",
                "schema constraints needed to interpret evaluator-visible state",
            ],
            unsupported_requirements_removed=bool(_extra_items(draft, "removed_unsupported_requirements")),
            requirements_marked_stronger_measurement=_extra_items(draft, "requirements_marked_stronger_measurement"),
            draft_created_at=str(llm_call.get("request_timestamp") or review_started_at),
            phase="smoke" if audit_mode == "smoke" else "preflight",
            counts_for_cost_table=audit_mode == "formal",
        )[0]
        reviewed_contract_path = review_result.reviewed_contract_path
        review_workflow_path = review_result.review_workflow_path
        human_time_path = review_result.human_time_path
        output_contract_hash = load_mapping(reviewed_contract_path)["contract_hash"]
    else:
        human_time_path = display_path(
            _write_human_time(
                draft,
                paths=paths,
                review_id=review_id,
                reviewer_id=reviewer_id,
                review_started_at=review_started_at,
                review_finished_at=review_finished_at,
                action="; ".join(_review_actions(checklist, final_decision)),
                source_artifacts=[str(draft["__path"]), display_path(notes_path)],
                audit_mode=audit_mode,
            )
        )

    human_review = _human_review_record(
        draft,
        llm_call,
        review_id=review_id,
        reviewer_name=reviewer_name,
        reviewer_id=reviewer_id,
        audit_mode=audit_mode,
        session_started_at=session_started_at,
        review_started_at=review_started_at,
        review_finished_at=review_finished_at,
        checklist=checklist,
        final_decision=final_decision,
        notes_path=display_path(notes_path),
        output_contract_hash=output_contract_hash,
        reviewed_contract_path=reviewed_contract_path,
        review_workflow_path=review_workflow_path,
        human_time_path=human_time_path,
    )
    validate_object("human_review", human_review, raise_on_error=True)
    human_review_path = write_json(paths.human_review_dir / f"{review_id}.json", human_review)
    return {
        "status": "ok",
        "review_id": review_id,
        "contract_id": draft.get("contract_id"),
        "case_unit_id": draft.get("case_unit_id"),
        "final_decision": final_decision,
        "human_review_path": display_path(human_review_path),
        "notes_path": display_path(notes_path),
        "reviewed_contract_path": reviewed_contract_path,
        "review_workflow_path": review_workflow_path,
        "human_time_path": human_time_path,
    }


def _display_review_material(
    draft: Mapping[str, Any],
    source: Mapping[str, Any],
    raw_sources: Sequence[Mapping[str, Any]],
    llm_call: Mapping[str, Any],
    *,
    display_limit: int,
    raw_display_limit: int,
) -> None:
    print("\n" + "=" * 80)
    print(f"Contract: {draft.get('contract_id')}")
    print(f"Domain: {draft.get('domain')} | Case: {draft.get('case_unit_id')} | Task: {draft.get('task_id')}")
    print("=" * 80)
    for raw_source in raw_sources:
        _print_section(str(raw_source["title"]), raw_source, raw_display_limit)
    visible = source.get("visible_inputs") if isinstance(source.get("visible_inputs"), Mapping) else {}
    for key in (
        "task_text",
        "official_policy",
        "evaluator_description",
        "evaluator_code",
        "schema",
        "trace_schema",
        "available_post_run_artifact_types",
        "native_sources",
    ):
        if key in visible:
            _print_section(_visible_input_title(key, source), visible[key], display_limit)
    _print_section(
        "LLM-generated: draft evidence contract",
        {
            "claim_text": draft.get("claim_text"),
            "required_artifacts": draft.get("required_artifacts"),
            "success_rule": draft.get("success_rule"),
            "fail_rule": draft.get("fail_rule"),
            "unresolve_rule": draft.get("unresolve_rule"),
            "claim_scope": draft.get("claim_scope"),
            "stronger_measurement_mapping": draft.get("stronger_measurement_mapping"),
            "source_support": draft.get("source_support"),
        },
        display_limit,
    )
    _print_section(
        "LLM provenance: drafting provenance",
        {
            "provider": llm_call.get("provider"),
            "model": llm_call.get("model"),
            "model_version": llm_call.get("model_version"),
            "prompt_version": llm_call.get("prompt_version"),
            "prompt_hash": llm_call.get("prompt_hash"),
            "visible_input_hash": llm_call.get("visible_input_hash"),
            "forbidden_input_assertion_hash": llm_call.get("forbidden_input_assertion_hash"),
        },
        display_limit,
    )


def _visible_input_title(key: str, source: Mapping[str, Any]) -> str:
    label = VISIBLE_INPUT_SOURCE_LABELS.get(key, "Structured input")
    if key == "official_policy" and str(source.get("domain")).lower() == "agentdojo":
        label = "Our source note"
    return f"{label}: {key}"


def _print_section(title: str, value: Any, display_limit: int) -> None:
    text = json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)
    truncated = False
    if display_limit > 0 and len(text) > display_limit:
        text = text[:display_limit] + "\n... [truncated; rerun with --display-limit 0 to show full section]"
        truncated = True
    print(f"\n--- {title}{' (truncated)' if truncated else ''} ---")
    print(text)


def _collect_checklist(*, interactive: bool, all_pass: bool) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    if interactive:
        print("\nReview checklist standards:")
    for key, standard in CHECKLIST:
        if interactive:
            print(f"\n[{key}]\nStandard: {standard}")
            result = _prompt_choice("Result", ("pass", "fail"))
            notes = input("Notes (optional): ").strip()
        else:
            result = "pass" if all_pass else "fail"
            notes = ""
        results.append({"check_id": key, "standard": standard, "result": result, "notes": notes})
    return results


def _source_for_contract(source_bundle_path: Path, contract_id: str) -> Mapping[str, Any]:
    payload = load_json_or_yaml(source_bundle_path)
    if not isinstance(payload, Mapping):
        raise ContractLifecycleError(f"source bundle must be a mapping: {source_bundle_path}")
    for source in payload.get("sources", []):
        if isinstance(source, Mapping) and source.get("contract_id") == contract_id:
            with_path = dict(source)
            with_path["__path"] = display_path(source_bundle_path)
            return with_path
    raise ContractLifecycleError(f"source bundle has no source for contract_id: {contract_id}")


def _raw_benchmark_sources(source: Mapping[str, Any], draft: Mapping[str, Any]) -> list[dict[str, Any]]:
    domain = normalize_domain(str(source.get("domain") or draft.get("domain") or ""))
    if domain == "agentdojo":
        sources = [_raw_agentdojo_source(source, draft)]
    elif domain == "appworld":
        sources = [_raw_appworld_source(source, draft)]
    elif domain == "webarena_verified":
        sources = [_raw_webarena_source(source, draft)]
    elif domain == "tau3_retail":
        sources = _raw_tau3_retail_sources(source, draft)
    else:
        raise ContractLifecycleError(f"raw benchmark source resolver is not implemented for domain: {domain}")
    if not sources:
        raise ContractLifecycleError(f"no raw benchmark source resolved for contract_id: {draft.get('contract_id')}")
    return [_stamp_raw_source(item) for item in sources]


def _raw_agentdojo_source(source: Mapping[str, Any], draft: Mapping[str, Any]) -> dict[str, Any]:
    path = resolve_repo_path(OFFICIAL_SPLITS_DIR / "agentdojo_selected_task_sources.json")
    payload = _load_mapping_file(path)
    case_unit_id = str(source.get("case_unit_id") or draft.get("case_unit_id") or "")
    source_ref = _first_native_source_ref(source)
    item = _find_mapping(payload.get("items"), lambda candidate: (
        str(candidate.get("case_unit_id") or "") == case_unit_id
        or (source_ref and str(candidate.get("source_ref") or "") == source_ref)
    ))
    if item is None:
        raise ContractLifecycleError(f"AgentDojo raw selected task source not found: {case_unit_id}")
    return {
        "title": "Raw benchmark source: AgentDojo selected task source",
        "source_path": display_path(path),
        "source_ref": item.get("source_ref") or source_ref,
        "completeness_scope": "Complete selected AgentDojo case-unit source exported from the installed AgentDojo package: user task, injection task, class source, suite tools, evaluator semantics, and source hash.",
        "source_file_metadata": _metadata_without_items(payload),
        "content": item,
    }


def _raw_appworld_source(source: Mapping[str, Any], draft: Mapping[str, Any]) -> dict[str, Any]:
    path = resolve_repo_path(OFFICIAL_SPLITS_DIR / "appworld_selected_task_sources.json")
    payload = _load_mapping_file(path)
    task_id = str(source.get("task_id") or draft.get("task_id") or draft.get("case_unit_id") or "")
    source_ref = _first_native_source_ref(source)
    item = _find_mapping(payload.get("items"), lambda candidate: (
        str(candidate.get("task_id") or "") == task_id
        or (source_ref and str(candidate.get("source_ref") or "") == source_ref)
    ))
    if item is None:
        raise ContractLifecycleError(f"AppWorld raw selected task source not found: {task_id}")
    return {
        "title": "Raw benchmark source: AppWorld task directory export",
        "source_path": display_path(path),
        "source_ref": item.get("source_ref") or source_ref,
        "completeness_scope": "Complete selected AppWorld task source export available in this repository: specs.json plus ground_truth files with original file hashes.",
        "source_file_metadata": _metadata_without_items(payload),
        "content": item,
    }


def _raw_webarena_source(source: Mapping[str, Any], draft: Mapping[str, Any]) -> dict[str, Any]:
    path = resolve_repo_path(OFFICIAL_SPLITS_DIR / "webarena_verified_official_812.json")
    payload = load_json_or_yaml(path)
    if not isinstance(payload, Sequence) or isinstance(payload, (str, bytes, bytearray)):
        raise ContractLifecycleError(f"WebArena raw source must be a list: {path}")
    task_id = str(source.get("task_id") or draft.get("task_id") or draft.get("case_unit_id") or "")
    item = _find_mapping(payload, lambda candidate: str(candidate.get("task_id") or "") == task_id)
    if item is None:
        raise ContractLifecycleError(f"WebArena raw task entry not found: {task_id}")
    return {
        "title": "Raw benchmark source: WebArena-Verified official task entry",
        "source_path": display_path(path),
        "source_ref": display_path(path),
        "completeness_scope": "Complete task object for this task_id from the official WebArena-Verified 812-task JSON file copied into experiments/official_splits.",
        "source_file_metadata": {"task_count": len(payload)},
        "content": item,
    }


def _raw_tau3_retail_sources(source: Mapping[str, Any], draft: Mapping[str, Any]) -> list[dict[str, Any]]:
    task_path = resolve_repo_path(OFFICIAL_SPLITS_DIR / "tau3_retail_tasks.json")
    policy_path = resolve_repo_path(OFFICIAL_SPLITS_DIR / "tau3_retail_policy.md")
    tasks = load_json_or_yaml(task_path)
    if not isinstance(tasks, Sequence) or isinstance(tasks, (str, bytes, bytearray)):
        raise ContractLifecycleError(f"tau3 retail task source must be a list: {task_path}")
    task_id = str(source.get("task_id") or draft.get("task_id") or draft.get("case_unit_id") or "")
    task = _find_mapping(tasks, lambda candidate: str(candidate.get("id") or "") == task_id)
    if task is None:
        raise ContractLifecycleError(f"tau3 retail raw task not found: {task_id}")
    return [
        {
            "title": "Raw benchmark source: tau3 retail task entry",
            "source_path": display_path(task_path),
            "source_ref": display_path(task_path),
            "completeness_scope": "Complete tau3-bench retail task object for this task id from the official task source copied into experiments/official_splits.",
            "source_file_metadata": {"task_count": len(tasks)},
            "content": task,
        },
        {
            "title": "Raw benchmark source: tau3 retail policy",
            "source_path": display_path(policy_path),
            "source_ref": display_path(policy_path),
            "completeness_scope": "Complete official tau3-bench retail policy source copied into experiments/official_splits.",
            "content": policy_path.read_text(encoding="utf-8"),
        },
    ]


def _stamp_raw_source(raw_source: Mapping[str, Any]) -> dict[str, Any]:
    stamped = dict(raw_source)
    stamped["content_sha256"] = sha256_object(stamped.get("content"))
    return stamped


def _raw_source_records(raw_sources: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for source in raw_sources:
        records.append(
            {
                "title": source.get("title"),
                "source_path": source.get("source_path"),
                "source_ref": source.get("source_ref"),
                "content_sha256": source.get("content_sha256"),
                "completeness_scope": source.get("completeness_scope"),
            }
        )
    return records


def _load_mapping_file(path: Path) -> Mapping[str, Any]:
    payload = load_json_or_yaml(path)
    if not isinstance(payload, Mapping):
        raise ContractLifecycleError(f"raw benchmark source must be a mapping: {path}")
    return payload


def _metadata_without_items(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in payload.items() if key != "items"}


def _find_mapping(items: Any, predicate: Any) -> Mapping[str, Any] | None:
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes, bytearray)):
        return None
    for item in items:
        if isinstance(item, Mapping) and predicate(item):
            return item
    return None


def _first_native_source_ref(source: Mapping[str, Any]) -> str:
    visible = source.get("visible_inputs")
    native_sources = visible.get("native_sources") if isinstance(visible, Mapping) else None
    if not isinstance(native_sources, Sequence) or isinstance(native_sources, (str, bytes, bytearray)):
        return ""
    for item in native_sources:
        if isinstance(item, Mapping):
            value = item.get("source_ref") or item.get("task_dir")
            if value:
                return str(value)
    return ""


def _llm_call_for_contract(llm_log_dir: Path, call_id: str) -> Mapping[str, Any]:
    for path in iter_json_files([llm_log_dir]):
        payload = load_mapping(path)
        if payload.get("schema_version") == "llm_call/v1" and payload.get("call_id") == call_id:
            return payload
    raise ContractLifecycleError(f"missing llm_call log for call_id: {call_id}")


def _human_review_record(
    draft: Mapping[str, Any],
    llm_call: Mapping[str, Any],
    *,
    review_id: str,
    reviewer_name: str,
    reviewer_id: str,
    audit_mode: str,
    session_started_at: str,
    review_started_at: str,
    review_finished_at: str,
    checklist: Sequence[Mapping[str, str]],
    final_decision: str,
    notes_path: str,
    output_contract_hash: str,
    reviewed_contract_path: str | None,
    review_workflow_path: str | None,
    human_time_path: str | None,
) -> dict[str, Any]:
    started = parse_timestamp(review_started_at, "review_started_at")
    finished = parse_timestamp(review_finished_at, "review_finished_at")
    actions = _human_review_actions(checklist, final_decision)
    return {
        "schema_version": "human_review/v1",
        "review_id": review_id,
        "contract_id": draft["contract_id"],
        "case_unit_id": draft["case_unit_id"],
        "domain": normalize_domain(draft["domain"]),
        "reviewer_id": reviewer_id,
        "reviewer_name": reviewer_name,
        "audit_mode": audit_mode,
        "session_started_at": session_started_at,
        "review_started_at": review_started_at,
        "review_finished_at": review_finished_at,
        "duration_seconds": round((finished - started).total_seconds(), 6),
        "actions": actions,
        "final_decision": final_decision,
        "checklist_results": [dict(item) for item in checklist],
        "source_bundle_hash": _source_support_hash(draft, "source_bundle_hash"),
        "visible_input_hash": _source_support_hash(draft, "visible_input_hash"),
        "input_contract_hash": str(draft.get("contract_hash") or contract_content_hash(draft)),
        "output_contract_hash": output_contract_hash,
        "forbidden_input_assertion_hash": str(
            llm_call.get("forbidden_input_assertion_hash")
            or llm_call.get("hidden_input_assertion_hash")
            or "0" * 64
        ),
        "contract_version": draft["contract_version"],
        "manifest_hash": draft["manifest_hash"],
        "contract_drafting_llm_call_id": draft["contract_drafting_llm_call_id"],
        "contract_draft_id": draft["contract_draft_id"],
        "locked_at": None,
        "locked_by": None,
        "notes_path": notes_path,
        "reviewed_contract_path": reviewed_contract_path,
        "review_workflow_path": review_workflow_path,
        "human_time_path": human_time_path,
    }


def _notes_payload(
    draft: Mapping[str, Any],
    source: Mapping[str, Any],
    llm_call: Mapping[str, Any],
    *,
    review_id: str,
    reviewer_name: str,
    reviewer_id: str,
    audit_mode: str,
    session_started_at: str,
    review_started_at: str,
    review_finished_at: str,
    checklist: Sequence[Mapping[str, str]],
    final_decision: str,
    extra_notes: Sequence[str],
    raw_sources: Sequence[Mapping[str, Any]],
    raw_sources_displayed: bool,
) -> dict[str, Any]:
    return {
        "schema_version": "contract_review_checklist/v1",
        "review_id": review_id,
        "reviewer_name": reviewer_name,
        "reviewer_id": reviewer_id,
        "audit_mode": audit_mode,
        "session_started_at": session_started_at,
        "review_started_at": review_started_at,
        "review_finished_at": review_finished_at,
        "contract_id": draft.get("contract_id"),
        "case_unit_id": draft.get("case_unit_id"),
        "domain": draft.get("domain"),
        "source_path": source.get("__path"),
        "draft_path": draft.get("__path"),
        "llm_call_id": llm_call.get("call_id"),
        "raw_benchmark_sources": _raw_source_records(raw_sources),
        "checklist_results": [dict(item) for item in checklist],
        "final_decision": final_decision,
        "extra_notes": list(extra_notes),
        "reviewed_against": {
            "raw_benchmark_sources": raw_sources_displayed,
            "source_visible_inputs": True,
            "draft_contract": True,
            "stronger_measurement_mapping": True,
            "llm_call_provenance": True,
        },
    }


def _write_human_time(
    draft: Mapping[str, Any],
    *,
    paths: AuditPaths,
    review_id: str,
    reviewer_id: str,
    review_started_at: str,
    review_finished_at: str,
    action: str,
    source_artifacts: Sequence[str],
    audit_mode: str,
) -> Path:
    started = parse_timestamp(review_started_at, "review_started_at")
    finished = parse_timestamp(review_finished_at, "review_finished_at")
    payload = {
        "schema_version": "human_time/v1",
        "activity_id": f"human-time-{review_id}",
        "reviewer_or_worker_id": reviewer_id,
        "role": "adapter_author",
        "activity_type": "contract_draft_review",
        "started_at": review_started_at,
        "finished_at": review_finished_at,
        "duration_minutes": round((finished - started).total_seconds() / 60.0, 6),
        "action": action,
        "source_artifacts": list(source_artifacts),
        "phase": "smoke" if audit_mode == "smoke" else "preflight",
        "experiment_type": "main",
        "priority": "P0",
        "manifest_hash": str(draft.get("manifest_hash") or "0" * 64),
        "counts_for_cost_table": audit_mode == "formal",
        "no_llm_cost_included": True,
        "no_vps_cost_included": True,
        "no_cloud_bill_included": True,
        "no_benchmark_execution_compute_included": True,
        "no_local_machine_runtime_included": True,
        "domain": draft.get("domain"),
        "case_unit_id": draft.get("case_unit_id"),
        "record_id": None,
        "contract_hash": str(draft.get("contract_hash") or contract_content_hash(draft)),
        "notes": "Interactive evidence-contract human review time; no LLM/VPS/cloud/benchmark compute included.",
    }
    validate_object("human_time", payload, raise_on_error=True)
    return write_json(paths.human_time_dir / f"human-time-{review_id}.json", payload)


def _review_actions(checklist: Sequence[Mapping[str, str]], final_decision: str) -> list[str]:
    return [f"{item['check_id']}={item['result']}" for item in checklist] + [f"final_decision={final_decision}"]


def _human_review_actions(checklist: Sequence[Mapping[str, str]], final_decision: str) -> list[str]:
    actions: list[str] = []
    if final_decision == "approve":
        actions.append("accept")
    elif final_decision == "needs_changes":
        actions.append("edit")
    else:
        actions.append("reject")
    if any(item["check_id"] == "stronger_measurement_handling" and item["result"] == "pass" for item in checklist):
        actions.append("mark_stronger_measurement")
    return actions


def _extra_items(draft: Mapping[str, Any], key: str) -> list[str]:
    support = draft.get("source_support")
    extra = support.get("drafter_extra_fields") if isinstance(support, Mapping) else None
    value = extra.get(key) if isinstance(extra, Mapping) else None
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [str(item) for item in value if str(item).strip()]


def _source_support_hash(draft: Mapping[str, Any], key: str) -> str:
    support = draft.get("source_support")
    value = support.get(key) if isinstance(support, Mapping) else None
    return str(value) if isinstance(value, str) and value else "0" * 64


def _prompt_nonempty(label: str) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("Value is required.")


def _prompt_choice(label: str, options: Sequence[str]) -> str:
    while True:
        print(f"\n{label}:")
        for index, option in enumerate(options, 1):
            print(f"  {index}. {option}")
        raw = input("Select: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        if raw in options:
            return raw
        print("Invalid selection.")


def _prompt_index(label: str, count: int, *, allow_zero: bool = False) -> int:
    while True:
        raw = input(f"{label}: ").strip()
        if raw.isdigit():
            value = int(raw)
            if (allow_zero and value == 0) or 1 <= value <= count:
                return value
        print("Invalid selection.")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def finish_after(start_iso: str) -> str:
    start = parse_timestamp(start_iso, "review_started_at")
    finish = datetime.now(timezone.utc).replace(microsecond=0)
    if finish <= start:
        finish = start + timedelta(seconds=1)
    return finish.isoformat()


def _timestamp_id(value: str) -> str:
    return value.replace(":", "").replace("-", "").replace("+", "p")


def _safe_id(value: Any) -> str:
    text = str(value)
    safe = "".join(char.lower() if char.isalnum() else "-" for char in text)
    return "-".join(part for part in safe.split("-") if part)


if __name__ == "__main__":
    raise SystemExit(main())
