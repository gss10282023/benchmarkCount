#!/usr/bin/env python3
"""Materialize source-reviewed adjudication of WebArena-Verified draft reviews.

The independent model review remains immutable. This layer records the main reviewer's
case-by-case disposition, including a narrow, source-checked override for inert
non-RETRIEVE ``retrieved_data: null`` omissions.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


NULL_OMISSION_OVERRIDE_IDS = {
    "156",
    "162",
    "326",
    "356",
    "401",
    "405",
    "429",
    "612",
    "630",
    "649",
    "653",
    "654",
    "672",
    "693",
    "697",
    "719",
    "722",
    "734",
    "744",
}


DECISION_ZH = {
    "accept": "可接受",
    "revise": "需修改",
}

DISPOSITION_ZH = {
    "model_accept_validated": "模型通过、复核确认",
    "model_revise_confirmed": "模型要求修改、复核确认",
    "model_revise_overruled": "模型要求修改、复核推翻",
}

CATEGORY_ZH = {
    "artifact_completeness_or_provenance": "产物完整性或来源证明",
    "decision_partition": "成功/失败/无法判定规则",
    "evaluator_composition": "评估器组合逻辑",
    "inert_null_field_omission_overruled": "无影响空字段省略（已推翻误报）",
    "minimality_or_internal_coherence": "最小性或内部一致性",
    "network_evaluator_semantics": "网络评估器语义",
    "nondecisive_or_substitute_artifact": "非决定性或替代产物",
    "response_normalization_or_expected_value": "响应归一化或期望值",
    "response_parser_or_sparse_field_semantics": "响应解析或稀疏字段语义",
    "stronger_condition": "更强条件",
    "unsupported_or_out_of_scope_claim": "无依据或超范围主张",
    "user_goal_scope_or_format": "用户目标范围或格式",
    "other_source_supported_revision": "其他有源码依据的修改项",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--case-packet-root", type=Path, required=True)
    parser.add_argument("--draft-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, default=812)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected object in {path}")
    return value


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected object in {path}")
    return value


def numeric_key(case_id: str) -> int:
    return int(case_id)


def finding_categories(
    findings: list[dict[str, Any]],
    *,
    response_only: bool,
) -> list[str]:
    categories: set[str] = set()
    for finding in findings:
        item_id = str(finding["checklist_item_id"])
        text = f"{finding['message']} {finding['required_change']}".lower()
        if item_id == "identity_and_scope":
            categories.add("unsupported_or_out_of_scope_claim")
        if item_id == "native_user_goal":
            categories.add("user_goal_scope_or_format")
        if item_id == "stronger_conditions":
            categories.add("stronger_condition")
        if item_id == "evaluator_composition":
            categories.add("evaluator_composition")
        if item_id == "decision_rules":
            categories.add("decision_partition")
        if item_id == "minimality_and_no_run_leakage":
            categories.add("minimality_or_internal_coherence")
        if "performed_operation" in text or "error_details" in text:
            categories.add("response_parser_or_sparse_field_semantics")
        if "retrieved_data" in text or "schema" in text or "normalized" in text:
            categories.add("response_normalization_or_expected_value")
        if response_only and any(
            token in text
            for token in ("network.har", " har", "trace", "taskevalresult", "evaluation record")
        ):
            categories.add("nondecisive_or_substitute_artifact")
        if not response_only and item_id == "decisive_post_run_evidence":
            categories.add("artifact_completeness_or_provenance")
        if any(
            token in text
            for token in (
                "networkeventevaluator",
                "last_event_only",
                "last matching",
                "last navigation",
                "full normalized url",
                "query parameter",
                "post_data",
                "response status",
                "should_not_exist",
                "decode_base64_query",
                "referer",
            )
        ):
            categories.add("network_evaluator_semantics")
    return sorted(categories or {"other_source_supported_revision"})


def validate_null_omission_override(
    *,
    case_id: str,
    review: dict[str, Any],
    raw_task: dict[str, Any],
    checklist: dict[str, Any],
) -> None:
    if review.get("decision") != "revise":
        raise ValueError(f"Override case {case_id} is not model-revise")
    evaluators = raw_task.get("eval")
    if not isinstance(evaluators, list):
        raise ValueError(f"Override case {case_id} has no evaluator list")
    response_cfg = next(
        (
            evaluator
            for evaluator in evaluators
            if isinstance(evaluator, dict)
            and evaluator.get("evaluator") == "AgentResponseEvaluator"
        ),
        None,
    )
    if not isinstance(response_cfg, dict):
        raise ValueError(f"Override case {case_id} has no AgentResponseEvaluator")
    expected = response_cfg.get("expected")
    if not isinstance(expected, dict) or "retrieved_data" not in expected:
        raise ValueError(f"Override case {case_id} lacks explicit retrieved_data")
    if expected["retrieved_data"] is not None:
        raise ValueError(f"Override case {case_id} retrieved_data is not null")
    task_type = str(expected.get("task_type") or "").upper()
    if task_type not in {"MUTATE", "NAVIGATE"}:
        raise ValueError(f"Override case {case_id} is not non-RETRIEVE")
    findings = review.get("blocking_findings")
    if not isinstance(findings, list) or not findings:
        raise ValueError(f"Override case {case_id} has no findings")
    allowed_items = {
        "official_evaluator_semantics",
        "decision_rules",
        "minimality_and_no_run_leakage",
    }
    if not any("retrieved_data" in str(finding.get("message") or "").lower() for finding in findings):
        raise ValueError(f"Override case {case_id} has no retrieved_data omission finding")
    for finding in findings:
        if finding.get("checklist_item_id") not in allowed_items:
            raise ValueError(f"Override case {case_id} has an unrelated failed item")
        message = str(finding.get("message") or "").lower()
        if "retrieved_data" not in message and not any(
            token in message
            for token in (
                "omitted response-field",
                "all explicitly configured response semantics",
                "omits part of the configured agentresponseevaluator semantics",
                "does not fully specify the configured agentresponseevaluator comparison",
            )
        ):
            raise ValueError(f"Override case {case_id} has an unrelated finding: {message}")
        if not any(
            token in message
            for token in (
                "omit",
                "does not state",
                "do not state",
                "never states",
                "reduces",
                "abbreviates",
                "names only",
                "does not enumerate",
                "does not provide the omitted",
                "does not fully specify",
            )
        ):
            raise ValueError(f"Override case {case_id} finding is not omission-only")
    native_text = json.dumps(checklist.get("native"), ensure_ascii=False).upper()
    if task_type not in native_text or "SUCCESS" not in native_text:
        raise ValueError(f"Override case {case_id} omits decisive task/status values")
    if not any(token in native_text for token in ("NORMALIZ", "PARS", "EVALUATOR")):
        raise ValueError(f"Override case {case_id} lacks released-evaluator qualification")


def main() -> int:
    args = parse_args()
    review_paths = {
        path.parent.name: path for path in args.review_root.glob("*/review.json")
    }
    if len(review_paths) != args.expected_count:
        raise SystemExit(f"Expected {args.expected_count} reviews, found {len(review_paths)}")
    if not NULL_OMISSION_OVERRIDE_IDS <= set(review_paths):
        raise SystemExit("An adjudication override case is absent from the review root")

    cases: list[dict[str, Any]] = []
    for case_id in sorted(review_paths, key=numeric_key):
        review = load_json(review_paths[case_id])
        raw_task = load_json(
            args.case_packet_root / case_id / "raw_case" / "derived" / "tag_task.json"
        )
        checklist = load_yaml(args.draft_root / case_id / "checklist.yaml")
        evaluator_kinds = [
            str(item.get("evaluator") or "")
            for item in raw_task.get("eval", [])
            if isinstance(item, dict)
        ]
        response_only = evaluator_kinds == ["AgentResponseEvaluator"]
        findings = review.get("blocking_findings")
        if not isinstance(findings, list):
            raise ValueError(f"{case_id}: blocking_findings is not a list")

        if review.get("decision") == "accept":
            adjudicated_decision = "accept"
            disposition = "model_accept_validated"
            note = "All nine independent semantic-review items passed."
            categories: list[str] = []
        elif case_id in NULL_OMISSION_OVERRIDE_IDS:
            validate_null_omission_override(
                case_id=case_id,
                review=review,
                raw_task=raw_task,
                checklist=checklist,
            )
            adjudicated_decision = "accept"
            disposition = "model_revise_overruled"
            note = (
                "The only findings demand explicit repetition of retrieved_data:null. "
                "For this MUTATE/NAVIGATE case the released non-RETRIEVE normalizer maps "
                "missing or supplied retrieved_data to null, so the draft's released "
                "parsing/normalization plus task_type/status rule is already sufficient."
            )
            categories = ["inert_null_field_omission_overruled"]
        else:
            if review.get("decision") != "revise" or not findings:
                raise ValueError(f"{case_id}: invalid revise disposition")
            adjudicated_decision = "revise"
            disposition = "model_revise_confirmed"
            note = (
                "At least one blocking finding remains source-supported after comparing "
                "the draft with the case packet and released evaluator semantics."
            )
            categories = finding_categories(findings, response_only=response_only)

        cases.append(
            {
                "case_id": case_id,
                "model_decision": review["decision"],
                "adjudicated_decision": adjudicated_decision,
                "disposition": disposition,
                "categories": categories,
                "failed_item_ids": [
                    item["id"]
                    for item in review["checklist_items"]
                    if item["status"] == "fail"
                ],
                "finding_ids": [finding["id"] for finding in findings],
                "finding_messages": [finding["message"] for finding in findings],
                "required_changes": [finding["required_change"] for finding in findings],
                "note": note,
            }
        )

    adjudicated_counts = Counter(case["adjudicated_decision"] for case in cases)
    disposition_counts = Counter(case["disposition"] for case in cases)
    category_case_counts = Counter(
        category for case in cases for category in case["categories"]
    )
    report = {
        "schema_version": "webarena_verified_draft_semantic_adjudication/v1",
        "case_count": len(cases),
        "adjudicated_decision_counts": dict(sorted(adjudicated_counts.items())),
        "disposition_counts": dict(sorted(disposition_counts.items())),
        "category_case_counts": dict(sorted(category_case_counts.items())),
        "override_policy": {
            "name": "inert_nonretrieve_retrieved_data_null_omission",
            "case_ids": sorted(NULL_OMISSION_OVERRIDE_IDS, key=numeric_key),
            "count": len(NULL_OMISSION_OVERRIDE_IDS),
        },
        "cases": cases,
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    json_path = args.output_root / "semantic_review_adjudication.json"
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    csv_path = args.output_root / "semantic_review_adjudication.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "case_id",
            "model_decision",
            "adjudicated_decision",
            "disposition",
            "categories",
            "failed_item_ids",
            "finding_ids",
            "finding_messages",
            "required_changes",
            "note",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for case in cases:
            writer.writerow(
                {
                    **case,
                    "categories": " | ".join(case["categories"]),
                    "failed_item_ids": " | ".join(case["failed_item_ids"]),
                    "finding_ids": " | ".join(case["finding_ids"]),
                    "finding_messages": " | ".join(case["finding_messages"]),
                    "required_changes": " | ".join(case["required_changes"]),
                }
            )

    markdown = [
        "# WebArena-Verified draft 逐案语义复核报告",
        "",
        f"- Case 总数：{len(cases)}",
        f"- 最终可接受：{adjudicated_counts['accept']}",
        f"- 最终需修改：{adjudicated_counts['revise']}",
        f"- 模型判定可接受且复核确认：{disposition_counts['model_accept_validated']}",
        f"- 模型判定需修改且复核确认：{disposition_counts['model_revise_confirmed']}",
        f"- 模型判定需修改但复核推翻：{disposition_counts['model_revise_overruled']}",
        "",
        "复核推翻仅限一种狭窄情形：非 RETRIEVE 任务省略了不影响结果、且显式为 null 的",
        "`retrieved_data` 字段。报告生成前，每个推翻项都已对照稀疏原始任务配置和 draft 重新验证。",
        "各问题类别会重叠，同一个 case 可能同时计入多个类别。",
        "",
        "## 已确认需修改的问题类别",
        "",
        "| 问题类别 | Case 数 |",
        "|---|---:|",
    ]
    markdown.extend(
        f"| {CATEGORY_ZH[category]} | {count} |"
        for category, count in sorted(category_case_counts.items())
        if category != "inert_null_field_omission_overruled"
    )
    markdown.extend(
        [
            "",
            "## 逐 case 最终裁决",
            "",
            "| Case 编号 | 模型初判 | 最终裁决 | 复核处理 | 问题类别 |",
            "|---:|---|---|---|---|",
        ]
    )
    for case in cases:
        markdown.append(
            f"| {case['case_id']} | {DECISION_ZH[case['model_decision']]} | "
            f"{DECISION_ZH[case['adjudicated_decision']]} | "
            f"{DISPOSITION_ZH[case['disposition']]} | "
            f"{'、'.join(CATEGORY_ZH[category] for category in case['categories'])} |"
        )
    (args.output_root / "SEMANTIC_ADJUDICATION.md").write_text(
        "\n".join(markdown) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["adjudicated_decision_counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
