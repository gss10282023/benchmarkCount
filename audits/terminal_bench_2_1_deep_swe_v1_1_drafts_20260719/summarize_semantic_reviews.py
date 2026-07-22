#!/usr/bin/env python3
"""Validate and summarize the independent semantic-review receipts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

import yaml
from jsonschema import Draft202012Validator


AUDIT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = AUDIT_ROOT.parents[1]
MINIMAL_ROOT = REPO_ROOT / "neurips_ed_track_minimal"
DEFAULT_DRAFT_ROOT = (
    REPO_ROOT
    / "results/drafts/terminal_bench_2_1_deep_swe_v1_1_gpt54_high_c32_20260719"
)
DEFAULT_REVIEW_ROOT = AUDIT_ROOT / "semantic_reviews"
PACKET_ROOTS = {
    "terminal_bench_2_1": REPO_ROOT / "experiments/case_packets/terminal_bench_2_1",
    "deep_swe_v1_1": REPO_ROOT / "experiments/case_packets/deep_swe_v1_1",
}
SCHEMA_PATH = MINIMAL_ROOT / "schemas/case_checklist.schema.json"
REVIEW_SCHEMA_PATH = MINIMAL_ROOT / "schemas/case_checklist_review.schema.json"
BASE_REVIEW_PROMPT_PATH = AUDIT_ROOT / "semantic_review.prompt.md"
SCHEMA_REPAIR_PROMPT_PATH = AUDIT_ROOT / "semantic_review_schema_repair.prompt.md"
SCHEMA_REPAIR_ARCHIVE_DIR = (
    AUDIT_ROOT / "semantic_review_invalid_attempt_archive" / "v3"
)
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

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from audits.terminal_bench_2_1_deep_swe_v1_1_drafts_20260719.audit_drafts import (  # noqa: E402
    final_label_leaks,
)
from neurips_ed_track_minimal.checklist_guardrails import (  # noqa: E402
    case_packet_support_paths,
    collect_checklist_guardrail_violations,
)
from neurips_ed_track_minimal.scripts import (  # noqa: E402
    review_case_checklist_with_codex as reviewer,
)
from neurips_ed_track_minimal.scripts.checklist_validator import (  # noqa: E402
    validate_packet_required_stronger_conditions,
    validate_support_pointers,
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected YAML mapping: {path}")
    return value


def packet_map() -> dict[str, tuple[str, Path]]:
    result: dict[str, tuple[str, Path]] = {}
    for benchmark, root in PACKET_ROOTS.items():
        for path in root.glob("*/case_packet.md"):
            if path.parent.name in result:
                raise RuntimeError(f"duplicate case id: {path.parent.name}")
            result[path.parent.name] = (benchmark, path)
    return result


def schema_errors(value: Mapping[str, Any], schema: Mapping[str, Any]) -> list[str]:
    validator = Draft202012Validator(dict(schema))
    return [
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(
            validator.iter_errors(dict(value)), key=lambda item: list(item.absolute_path)
        )
    ]


def revised_checklist_validation(
    original: Mapping[str, Any],
    review: Mapping[str, Any],
    packet_path: Path,
    schema: Mapping[str, Any],
) -> dict[str, Any] | None:
    if review.get("decision") != "revise":
        return None
    body = review.get("revised_checklist")
    if not isinstance(body, Mapping):
        return {"valid": False, "errors": ["missing revised_checklist body"]}
    candidate = {
        "schema_version": original.get("schema_version"),
        "case_unit_id": original.get("case_unit_id"),
        "domain": original.get("domain"),
        "task_id": original.get("task_id"),
        "native": body.get("native"),
        "stronger": body.get("stronger"),
    }
    errors = schema_errors(candidate, schema)
    packet_text = packet_path.read_text(encoding="utf-8")
    guardrails = collect_checklist_guardrail_violations(
        candidate,
        allowed_source_paths=case_packet_support_paths(packet_text),
    )
    pointer_errors: list[str] = []
    try:
        validate_support_pointers(candidate, packet_path)
        validate_packet_required_stronger_conditions(candidate, packet_path)
    except Exception as exc:
        pointer_errors.append(f"{type(exc).__name__}: {exc}")
    label_leaks = final_label_leaks(candidate)
    all_errors = [
        *errors,
        *(f"guardrail: {item}" for item in guardrails),
        *(f"pointer: {item}" for item in pointer_errors),
        *(f"label leak: {item}" for item in label_leaks),
    ]
    return {
        "valid": not all_errors,
        "errors": all_errors,
        "candidate": candidate,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft-root", type=Path, default=DEFAULT_DRAFT_ROOT)
    parser.add_argument("--review-root", type=Path, default=DEFAULT_REVIEW_ROOT)
    args = parser.parse_args()
    draft_root = args.draft_root.resolve()
    review_root = args.review_root.resolve()
    packets = packet_map()
    if len(packets) != 202:
        raise RuntimeError(f"expected 202 packet cases, found {len(packets)}")
    review_schema = load_json(REVIEW_SCHEMA_PATH)
    checklist_schema = load_json(SCHEMA_PATH)
    repair_case_ids = (
        {path.name for path in SCHEMA_REPAIR_ARCHIVE_DIR.iterdir() if path.is_dir()}
        if SCHEMA_REPAIR_ARCHIVE_DIR.is_dir()
        else set()
    )
    unknown_repair_ids = sorted(repair_case_ids - set(packets))
    if unknown_repair_ids:
        raise RuntimeError(f"unknown schema-repair case ids: {unknown_repair_ids}")

    records: list[dict[str, Any]] = []
    for case_id in sorted(packets):
        benchmark, packet_path = packets[case_id]
        checklist_path = draft_root / case_id / "checklist.yaml"
        review_path = review_root / case_id / "review.json"
        llm_call_path = review_root / case_id / "review.llm_call.json"
        infra_errors: list[str] = []
        if not checklist_path.is_file():
            infra_errors.append("missing original checklist")
        if not review_path.is_file():
            infra_errors.append("missing review.json")
        if not llm_call_path.is_file():
            infra_errors.append("missing review.llm_call.json")
        if infra_errors:
            records.append(
                {
                    "benchmark": benchmark,
                    "case_unit_id": case_id,
                    "status": "failed",
                    "decision": None,
                    "infra_errors": infra_errors,
                    "failed_item_ids": [],
                    "finding_count": 0,
                    "findings": [],
                    "revision_validation": None,
                }
            )
            continue

        original = load_yaml(checklist_path)
        review = load_json(review_path)
        try:
            review = reviewer.validate_model_review_body(
                review,
                review_schema,
                review_item_ids=REVIEW_ITEM_IDS,
            )
        except reviewer.ChecklistModelReviewError as exc:
            infra_errors.append(f"invalid review body: {exc}")
        llm_call = load_json(llm_call_path)
        response = llm_call.get("response_metadata")
        response = response if isinstance(response, Mapping) else {}
        expected_llm = {
            "provider": "codex_cli",
            "model": "gpt-5.6-sol",
            "phase": "checklist_model_review",
            "case_unit_id": case_id,
            "reasoning_effort": "high",
        }
        actual_llm = {
            "provider": llm_call.get("provider"),
            "model": llm_call.get("model"),
            "phase": llm_call.get("phase"),
            "case_unit_id": llm_call.get("case_unit_id"),
            "reasoning_effort": response.get("reasoning_effort"),
        }
        mismatches = {
            key: {"expected": value, "actual": actual_llm.get(key)}
            for key, value in expected_llm.items()
            if actual_llm.get(key) != value
        }
        if mismatches:
            infra_errors.append(f"review LLM config mismatch: {mismatches}")

        items = review.get("checklist_items")
        items = items if isinstance(items, list) else []
        failed_item_ids = [
            str(item.get("id"))
            for item in items
            if isinstance(item, Mapping) and item.get("status") == "fail"
        ]
        findings = review.get("blocking_findings")
        findings = findings if isinstance(findings, list) else []
        revision_validation = revised_checklist_validation(
            original,
            review,
            packet_path,
            checklist_schema,
        )
        records.append(
            {
                "benchmark": benchmark,
                "case_unit_id": case_id,
                "status": "failed" if infra_errors else "completed",
                "decision": review.get("decision"),
                "infra_errors": infra_errors,
                "failed_item_ids": failed_item_ids,
                "finding_count": len(findings),
                "findings": findings,
                "revision_validation": revision_validation,
                "review_llm_config": actual_llm,
            }
        )

    with (AUDIT_ROOT / "semantic_review_records.jsonl").open(
        "w", encoding="utf-8"
    ) as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    columns = [
        "benchmark",
        "case_unit_id",
        "status",
        "decision",
        "failed_item_ids",
        "finding_count",
        "revision_valid",
        "infra_errors",
    ]
    with (AUDIT_ROOT / "semantic_review_report.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for record in records:
            revision = record.get("revision_validation")
            writer.writerow(
                {
                    "benchmark": record["benchmark"],
                    "case_unit_id": record["case_unit_id"],
                    "status": record["status"],
                    "decision": record["decision"],
                    "failed_item_ids": ";".join(record["failed_item_ids"]),
                    "finding_count": record["finding_count"],
                    "revision_valid": (
                        revision.get("valid") if isinstance(revision, Mapping) else ""
                    ),
                    "infra_errors": " | ".join(record["infra_errors"]),
                }
            )

    decisions = Counter(str(record["decision"]) for record in records)
    failed_items = Counter(
        item for record in records for item in record["failed_item_ids"]
    )
    infra_failed = [record for record in records if record["status"] != "completed"]
    invalid_revisions = [
        record
        for record in records
        if isinstance(record.get("revision_validation"), Mapping)
        and not record["revision_validation"]["valid"]
    ]
    benchmarks: dict[str, dict[str, int]] = {}
    for benchmark in PACKET_ROOTS:
        rows = [record for record in records if record["benchmark"] == benchmark]
        benchmarks[benchmark] = {
            "case_count": len(rows),
            "accept_count": sum(record["decision"] == "accept" for record in rows),
            "revise_count": sum(record["decision"] == "revise" for record in rows),
            "infra_failed_count": sum(record["status"] != "completed" for record in rows),
        }
    summary = {
        "schema_version": "tb21_deepswe11_semantic_review_summary/v1",
        "status": (
            "pass"
            if not infra_failed and decisions.get("revise", 0) == 0
            else "review_required"
        ),
        "audit_boundary": (
            "one matching case_packet.md and checklist.yaml plus pinned review prompt(s); "
            "no run outcomes, released labels, or evidence scores"
        ),
        "case_count": len(records),
        "decision_counts": dict(sorted(decisions.items())),
        "infra_failed_count": len(infra_failed),
        "invalid_proposed_revision_count": len(invalid_revisions),
        "review_prompt_variants": {
            "base_semantic_review": {
                "case_count": len(records) - len(repair_case_ids),
                "prompt": str(BASE_REVIEW_PROMPT_PATH.relative_to(REPO_ROOT)),
                "prompt_sha256": sha256_file(BASE_REVIEW_PROMPT_PATH),
            },
            "schema_repair_retry": {
                "case_count": len(repair_case_ids),
                "case_ids": sorted(repair_case_ids),
                "prompt": str(SCHEMA_REPAIR_PROMPT_PATH.relative_to(REPO_ROOT)),
                "prompt_sha256": sha256_file(SCHEMA_REPAIR_PROMPT_PATH),
            },
        },
        "failed_review_item_counts": dict(sorted(failed_items.items())),
        "benchmarks": benchmarks,
    }
    (AUDIT_ROOT / "semantic_review_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report_lines = [
        "# Terminal-Bench 2.1 / DeepSWE v1.1 draft 语义审核",
        "",
        "## 审核边界",
        "",
        "- 每个 case 只读取匹配的 `case_packet.md`、`checklist.yaml` 和冻结审核 prompt。",
        "- 未读取 agent outcome、per-record reward/released label 或 evidence score。",
        "- `accept` 表示九项系统设计检查全部通过；`revise` 表示至少一项阻断问题。",
        "- `revise` 的 proposed revision 只作审计建议；本次未覆盖或修改原始 draft。",
        "",
        "## 汇总",
        "",
        f"- 总 case：{len(records)}",
        f"- accept：{decisions.get('accept', 0)}",
        f"- revise：{decisions.get('revise', 0)}",
        f"- 审核运行失败：{len(infra_failed)}",
        f"- 无效修订建议：{len(invalid_revisions)}",
        f"- 使用 schema 加固 retry prompt 的 case：{len(repair_case_ids)}",
        "",
        "## 分 benchmark",
        "",
    ]
    for benchmark, counts in benchmarks.items():
        report_lines.append(
            f"- `{benchmark}`：{counts['case_count']} cases，"
            f"accept {counts['accept_count']}，revise {counts['revise_count']}，"
            f"审核失败 {counts['infra_failed_count']}。"
        )
    report_lines.extend(["", "## 阻断项计数", ""])
    if failed_items:
        for item, count in sorted(failed_items.items()):
            report_lines.append(f"- `{item}`：{count}")
    else:
        report_lines.append("- 无。")
    report_lines.extend(
        [
            "",
            "逐 case 结论和 finding 见 `semantic_review_records.jsonl` 与 "
            "`semantic_review_report.csv`。",
            "",
        ]
    )
    (AUDIT_ROOT / "AUDIT_REPORT_ZH.md").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not infra_failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
