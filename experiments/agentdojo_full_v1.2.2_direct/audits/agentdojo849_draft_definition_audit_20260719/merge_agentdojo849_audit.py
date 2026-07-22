#!/usr/bin/env python3
"""Merge deterministic, first-pass, and adjudicated AgentDojo draft audits."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_CASES = 849


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-root", type=Path, required=True)
    parser.add_argument("--draft-root", type=Path, required=True)
    parser.add_argument("--deterministic-root", type=Path, required=True)
    parser.add_argument("--first-review-root", type=Path, required=True)
    parser.add_argument("--adjudication-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser.parse_args()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def suite_of(name: str) -> str:
    for suite in ("banking", "slack", "travel", "workspace"):
        if f"_{suite}_" in name:
            return suite
    raise ValueError(f"cannot identify suite: {name}")


def sustained_category(checklist_path: str) -> str:
    if checklist_path.startswith("stronger"):
        return "stronger_measurement_conditions"
    if checklist_path.startswith("native.user_goal"):
        return "native_user_goal"
    if checklist_path.startswith("native.decisive_artifacts"):
        return "decisive_evidence_and_inventory"
    if checklist_path.startswith(
        (
            "native.checked_by",
            "native.success_if",
            "native.fail_if",
            "native.undecided_if",
            "native.benchmark_success",
        )
    ):
        return "native_evaluator_and_sfu_rules"
    return "other"


def pointer_file_status(
    packet_dir: Path, checklist_path: Path, pointer: str
) -> dict[str, Any]:
    source = pointer.split("::", 1)[0]
    if source in {"checklist.yaml", "checklist_yaml"} or source.startswith(
        ("native.", "stronger.", "checklist.")
    ):
        return {
            "pointer": pointer,
            "source_file_exists": checklist_path.is_file(),
            "resolved_source_file": "draft/checklist.yaml",
        }
    candidates = [packet_dir / source, packet_dir / "raw_case" / source]
    resolved = None
    for candidate in candidates:
        try:
            candidate.resolve().relative_to(packet_dir.resolve())
        except ValueError:
            continue
        if candidate.is_file():
            resolved = candidate
            break
    return {
        "pointer": pointer,
        "source_file_exists": resolved is not None,
        "resolved_source_file": (
            str(resolved.relative_to(packet_dir)) if resolved is not None else None
        ),
    }


def load_deterministic(root: Path) -> dict[str, dict[str, Any]]:
    path = root / "deterministic_audit.jsonl"
    rows: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        name = row["directory_name"]
        if name in rows:
            raise ValueError(f"duplicate deterministic case: {name}")
        rows[name] = row
    return rows


def load_first_reviews(root: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "cases").glob("*/review.json")):
        row = read_json(path)
        name = row["directory_name"]
        if name in rows:
            raise ValueError(f"duplicate first review: {name}")
        rows[name] = row
    return rows


def load_adjudications(root: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "cases").glob("*/adjudication.json")):
        row = read_json(path)
        name = row["directory_name"]
        if name in rows:
            raise ValueError(f"duplicate adjudication: {name}")
        rows[name] = row
    unresolved = [
        path
        for path in (root / "cases").glob("*/unresolved.json")
        if not (path.parent / "adjudication.json").is_file()
    ]
    if unresolved:
        raise ValueError(f"formal adjudication root contains {len(unresolved)} unresolved cases")
    return rows


def merge_case(
    name: str,
    deterministic: dict[str, Any],
    first: dict[str, Any],
    adjudication: dict[str, Any] | None,
    packet_root: Path,
    draft_root: Path,
) -> dict[str, Any]:
    packet_dir = packet_root / name
    packet_path = packet_dir / "case_packet.md"
    checklist_path = draft_root / name / "checklist.yaml"
    if sha256_file(packet_path) != deterministic["packet_sha256"]:
        raise ValueError(f"deterministic packet hash mismatch: {name}")
    if sha256_file(checklist_path) != deterministic["checklist_sha256"]:
        raise ValueError(f"deterministic checklist hash mismatch: {name}")
    if first["packet_sha256"] != deterministic["packet_sha256"]:
        raise ValueError(f"first-review packet hash mismatch: {name}")
    if first["checklist_sha256"] != deterministic["checklist_sha256"]:
        raise ValueError(f"first-review checklist hash mismatch: {name}")

    first_body = first["model_review"]
    allegations = [
        {"finding_id": f"F{index}", **finding}
        for index, finding in enumerate(first_body["blocking_findings"], start=1)
    ]
    allegation_by_id = {item["finding_id"]: item for item in allegations}
    first_decision = first_body["decision"]
    if (first_decision == "fail") != bool(allegations):
        raise ValueError(f"inconsistent first review: {name}")

    sustained: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    adjudication_decision = "not_required"
    if first_decision == "fail":
        if adjudication is None:
            raise ValueError(f"missing adjudication: {name}")
        if adjudication["packet_sha256"] != deterministic["packet_sha256"]:
            raise ValueError(f"adjudication packet hash mismatch: {name}")
        if adjudication["checklist_sha256"] != deterministic["checklist_sha256"]:
            raise ValueError(f"adjudication checklist hash mismatch: {name}")
        adjudication_decision = adjudication["final_decision"]
        adj_items = adjudication["adjudication"]["finding_adjudications"]
        if [item["finding_id"] for item in adj_items] != list(allegation_by_id):
            raise ValueError(f"adjudication finding ID mismatch: {name}")
        for item in adj_items:
            allegation = allegation_by_id[item["finding_id"]]
            if item["original_code"] != allegation["code"]:
                raise ValueError(f"adjudication finding code mismatch: {name}")
            combined = {
                "finding_id": item["finding_id"],
                "code": item["original_code"],
                "checklist_path": allegation["checklist_path"],
                "first_pass_explanation": allegation["explanation"],
                "first_pass_source_pointers": allegation["source_pointers"],
                "adjudication_rationale": item["rationale"],
                "adjudication_source_pointers": item["source_pointers"],
                "source_pointer_file_checks": [
                    pointer_file_status(packet_dir, checklist_path, pointer)
                    for pointer in dict.fromkeys(
                        allegation["source_pointers"] + item["source_pointers"]
                    )
                ],
            }
            (sustained if item["verdict"] == "sustain" else rejected).append(combined)
        expected = "fail" if sustained else "pass"
        if adjudication_decision != expected:
            raise ValueError(f"adjudication decision/verdict mismatch: {name}")
    elif adjudication is not None:
        raise ValueError(f"unexpected adjudication for first-pass case: {name}")

    blocking_codes = set(deterministic["blocking_finding_codes"])
    deterministic_blocking = [
        finding for finding in deterministic["findings"] if finding["code"] in blocking_codes
    ]
    if deterministic["status"] == "fail" and not deterministic_blocking:
        raise ValueError(f"deterministic failure lacks blocking finding: {name}")

    final_status = "noncompliant" if deterministic_blocking or sustained else "compliant"
    final_reasons: list[str] = []
    if deterministic_blocking:
        final_reasons.append("deterministic_blocking_finding")
    if sustained:
        final_reasons.append("semantically_sustained_finding")
    if not final_reasons:
        final_reasons.append("no_sustained_or_deterministic_blocking_finding")

    failed_items = [
        item["id"] for item in first_body["checklist_items"] if item["status"] == "fail"
    ]
    return {
        "schema_version": "agentdojo_draft_definition_final_audit/v1",
        "directory_name": name,
        "case_unit_id": deterministic["case_unit_id"],
        "suite": suite_of(name),
        "final_status": final_status,
        "final_reasons": final_reasons,
        "deterministic_status": deterministic["status"],
        "deterministic_blocking_findings": deterministic_blocking,
        "deterministic_review_flags": deterministic["findings"],
        "first_review_decision": first_decision,
        "first_review_failed_items": failed_items,
        "first_review_checklist_items": first_body["checklist_items"],
        "adjudication_decision": adjudication_decision,
        "sustained_findings": sustained,
        "rejected_findings": rejected,
        "stronger_condition_count": deterministic["stronger_condition_count"],
        "packet_sha256": deterministic["packet_sha256"],
        "checklist_sha256": deterministic["checklist_sha256"],
        "outcome_blind": True,
        "draft_modified": False,
    }


def markdown_report(summary: dict[str, Any]) -> str:
    final = summary["final_status_counts"]
    lines = [
        "# AgentDojo 新增 849 个 draft 定义符合性审核报告",
        "",
        f"生成时间（UTC）：`{summary['generated_at']}`",
        "",
        "## 结论",
        "",
        f"共审核 **{summary['case_count']}** 个 draft：**{final.get('compliant', 0)} 个符合**系统对 draft 的定义，**{final.get('noncompliant', 0)} 个不符合**，未留下 unresolved 项。",
        "",
        "本结论只审核预运行、结果盲的 checklist/draft 定义，不读取任何 agent outcome、benchmark label、score 或运行产物，不推断实际 S/F/U，也不判定 benchmark conflict。审核过程没有修改任何 draft。",
        "",
        "逐 case 结论见 `FINAL_AUDIT_849.csv`；包含两轮理由、来源指针和 hash 的机器可读记录见 `FINAL_AUDIT_849.jsonl`；所有不符合项的中文索引见 `NONCOMPLIANT_CASES_ZH.md`。",
        "",
        "## 审核方法",
        "",
        "1. 对 849 个 packet/checklist 做确定性结构与来源约束检查，包括 case 身份、结果盲、artifact inventory 精确值、来源文件和 SHA256 一致性。",
        "2. 对每个 case 独立检查八项设计要求：锁定与结果盲、native user goal、released evaluator 权威性、S/F/U 优先级、证据与 inventory、stronger 条件、来源最小性、conflict/reporting 分离。",
        "3. 第一轮指出的问题不直接定案；每个 allegation 再以同一 packet 的官方 goal/task/policy、released evaluator/oracle、schema 和 inventory 逐条裁决。只有能被精确来源证明的 substantive finding 才保留。",
        "4. 最终不符合 = 存在确定性 blocking finding，或第二轮维持至少一个语义 finding。仅有措辞差异、主观偏好、重复要求或无官方依据的更强要求均不构成失败。",
        "",
        "## 审核完整性",
        "",
        f"- packet 数：{summary['case_count']}；packet hash 全部与确定性审核输入一致。",
        f"- 第一轮逐 case 审核：{summary['first_review_decision_counts'].get('pass', 0)} pass，{summary['first_review_decision_counts'].get('fail', 0)} 个进入第二轮。",
        f"- 第二轮：{summary['adjudication_decision_counts'].get('pass', 0)} 个 allegation set 全部驳回，{summary['adjudication_decision_counts'].get('fail', 0)} 个至少保留一项。",
        f"- 第一轮 finding：共 {summary['first_finding_count']} 项；第二轮维持 {summary['sustained_finding_count']} 项，驳回 {summary['rejected_finding_count']} 项。",
        f"- 被维持 finding 的来源指针文件检查：{summary['sustained_pointer_file_checks']['present']} 个存在，{summary['sustained_pointer_file_checks']['missing']} 个缺失。",
        "- 实际 agent outcomes 读取：否；draft 修改：否；未决项：0。",
        "",
        "## 按 suite 的最终结果",
        "",
        "| Suite | 符合 | 不符合 | 合计 |",
        "|---|---:|---:|---:|",
    ]
    for suite in ("banking", "slack", "travel", "workspace"):
        counts = summary["suite_status_counts"].get(suite, {})
        compliant = counts.get("compliant", 0)
        noncompliant = counts.get("noncompliant", 0)
        lines.append(f"| {suite} | {compliant} | {noncompliant} | {compliant + noncompliant} |")

    lines.extend([
        "",
        "## 按系统设计维度统计被维持问题",
        "",
        "以下是 finding 数量，不是 case 数量；同一 case 可以有多项问题。",
        "",
        "| 设计维度 | Finding 数量 |",
        "|---|---:|",
    ])
    category_labels = {
        "stronger_measurement_conditions": "stronger 条件的官方依据、语义 gap、完整性或独立性",
        "native_evaluator_and_sfu_rules": "released evaluator/oracle 语义及 native S/F/U 规则",
        "decisive_evidence_and_inventory": "decisive evidence、artifact inventory 与可判定性",
        "native_user_goal": "native user goal 的官方任务忠实度与角色分离",
        "other": "其他",
    }
    for category, count in summary["sustained_finding_category_counts"].items():
        lines.append(f"| {category_labels.get(category, category)} | {count} |")

    lines.extend([
        "",
        "## 被维持问题的主要类型",
        "",
        "下表按精确 finding code 聚合。code 是逐 case 审核记录的稳定索引；具体语义、官方来源与裁决理由必须以 JSONL 和不符合项明细为准。",
        "",
        "| Finding code | 数量 |",
        "|---|---:|",
    ])
    top_codes = summary["sustained_finding_code_counts"][:20]
    for code, count in top_codes:
        lines.append(f"| `{code}` | {count} |")
    if not top_codes:
        lines.append("| （无） | 0 |")
    remaining_code_count = len(summary["sustained_finding_code_counts"]) - len(top_codes)
    if remaining_code_count:
        lines.extend([
            "",
            f"这里只展示数量最高的 20 个 code；其余 {remaining_code_count} 个低频 code 的完整计数保存在 `AUDIT_SUMMARY.json`。",
        ])

    lines.extend([
        "",
        "## 重要解释",
        "",
        "- 不符合表示 checklist/draft 本身没有忠实、完整地锁定该 case 的证据规则；不表示对应 benchmark run 一定失败。",
        "- stronger 条件的不符合独立于 native label，不自动构成 benchmark conflict。",
        "- 本审核不会用运行结果反向修订 checklist，因此满足 outcome-blind 锁定要求。",
        "- 确定性审核中的非 blocking 语义正则 flag 仅用于把内容送入逐项语义审核，不单独计为失败。",
        "",
        "## 产物",
        "",
        "- `FINAL_AUDIT_849.csv`：每个 case 一行的最终结论。",
        "- `FINAL_AUDIT_849.jsonl`：每个 case 的完整审核收据。",
        "- `NONCOMPLIANT_CASES_ZH.md`：所有不符合 case 及其被维持 finding。",
        "- `AUDIT_SUMMARY.json`：聚合统计、模型配置和不可变性声明。",
        "",
    ])
    return "\n".join(lines)


def noncompliant_markdown(rows: list[dict[str, Any]]) -> str:
    bad = [row for row in rows if row["final_status"] == "noncompliant"]
    lines = [
        "# AgentDojo draft 不符合项逐 case 明细",
        "",
        f"共 {len(bad)} 个不符合 case。这里仅列出最终被维持的问题；第一轮后被驳回的问题不作为缺陷。",
        "",
    ]
    for index, row in enumerate(bad, start=1):
        lines.extend([
            f"## {index}. `{row['directory_name']}`",
            "",
            f"- Case unit：`{row['case_unit_id']}`",
            f"- Suite：`{row['suite']}`",
            f"- Packet SHA256：`{row['packet_sha256']}`",
            f"- Checklist SHA256：`{row['checklist_sha256']}`",
        ])
        for finding in row["deterministic_blocking_findings"]:
            lines.extend([
                "",
                f"### 确定性问题：`{finding['code']}`",
                "",
                f"- 位置：`{finding['path']}`",
                f"- 问题：{finding['detail']}",
            ])
        for finding in row["sustained_findings"]:
            lines.extend([
                "",
                f"### 被维持问题：`{finding['code']}`（{finding['finding_id']}）",
                "",
                f"- Checklist 位置：`{finding['checklist_path']}`",
                f"- 第一轮问题说明：{finding['first_pass_explanation']}",
                f"- 第二轮裁决理由：{finding['adjudication_rationale']}",
                "- 裁决来源：",
            ])
            for pointer in finding["adjudication_source_pointers"]:
                lines.append(f"  - `{pointer}`")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    deterministic = load_deterministic(args.deterministic_root)
    first_reviews = load_first_reviews(args.first_review_root)
    adjudications = load_adjudications(args.adjudication_root)
    names = sorted(deterministic)
    if len(names) != EXPECTED_CASES:
        raise ValueError(f"expected {EXPECTED_CASES} cases, found {len(names)}")
    if set(first_reviews) != set(names):
        raise ValueError("first-review case set differs from deterministic case set")
    failed_names = {
        name
        for name, row in first_reviews.items()
        if row["model_review"]["decision"] == "fail"
    }
    if set(adjudications) != failed_names:
        missing = sorted(failed_names - set(adjudications))
        extra = sorted(set(adjudications) - failed_names)
        raise ValueError(f"adjudication case set mismatch; missing={len(missing)} extra={len(extra)}")

    rows = [
        merge_case(
            name,
            deterministic[name],
            first_reviews[name],
            adjudications.get(name),
            args.packet_root,
            args.draft_root,
        )
        for name in names
    ]
    args.output_root.mkdir(parents=True, exist_ok=True)
    jsonl_path = args.output_root / "FINAL_AUDIT_849.jsonl"
    jsonl_path.write_bytes(b"".join(canonical(row) for row in rows))

    csv_path = args.output_root / "FINAL_AUDIT_849.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "directory_name",
            "case_unit_id",
            "suite",
            "final_status",
            "deterministic_status",
            "first_review_decision",
            "adjudication_decision",
            "sustained_finding_count",
            "sustained_finding_codes",
            "rejected_finding_count",
            "first_review_failed_items",
            "stronger_condition_count",
            "packet_sha256",
            "checklist_sha256",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "directory_name": row["directory_name"],
                "case_unit_id": row["case_unit_id"],
                "suite": row["suite"],
                "final_status": row["final_status"],
                "deterministic_status": row["deterministic_status"],
                "first_review_decision": row["first_review_decision"],
                "adjudication_decision": row["adjudication_decision"],
                "sustained_finding_count": len(row["sustained_findings"]),
                "sustained_finding_codes": ";".join(
                    item["code"] for item in row["sustained_findings"]
                ),
                "rejected_finding_count": len(row["rejected_findings"]),
                "first_review_failed_items": ";".join(row["first_review_failed_items"]),
                "stronger_condition_count": row["stronger_condition_count"],
                "packet_sha256": row["packet_sha256"],
                "checklist_sha256": row["checklist_sha256"],
            })

    final_status_counts = Counter(row["final_status"] for row in rows)
    first_decisions = Counter(row["first_review_decision"] for row in rows)
    adjudication_decisions = Counter(
        row["adjudication_decision"]
        for row in rows
        if row["adjudication_decision"] != "not_required"
    )
    suite_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        suite_counts[row["suite"]][row["final_status"]] += 1
    sustained_codes = Counter(
        finding["code"] for row in rows for finding in row["sustained_findings"]
    )
    sustained_categories = Counter(
        sustained_category(finding["checklist_path"])
        for row in rows
        for finding in row["sustained_findings"]
    )
    pointer_checks = [
        check
        for row in rows
        for finding in row["sustained_findings"]
        for check in finding["source_pointer_file_checks"]
    ]
    first_finding_count = sum(
        len(row["sustained_findings"]) + len(row["rejected_findings"]) for row in rows
    )
    summary = {
        "schema_version": "agentdojo_draft_definition_final_audit_summary/v1",
        "generated_at": now(),
        "case_count": len(rows),
        "final_status_counts": dict(sorted(final_status_counts.items())),
        "first_review_decision_counts": dict(sorted(first_decisions.items())),
        "adjudication_decision_counts": dict(sorted(adjudication_decisions.items())),
        "suite_status_counts": {
            suite: dict(sorted(counts.items())) for suite, counts in sorted(suite_counts.items())
        },
        "first_finding_count": first_finding_count,
        "sustained_finding_count": sum(sustained_codes.values()),
        "rejected_finding_count": first_finding_count - sum(sustained_codes.values()),
        "sustained_finding_category_counts": dict(
            sorted(sustained_categories.items(), key=lambda item: (-item[1], item[0]))
        ),
        "sustained_finding_code_counts": sustained_codes.most_common(),
        "deterministic_blocking_case_count": sum(
            bool(row["deterministic_blocking_findings"]) for row in rows
        ),
        "sustained_pointer_file_checks": {
            "present": sum(check["source_file_exists"] for check in pointer_checks),
            "missing": sum(not check["source_file_exists"] for check in pointer_checks),
        },
        "unresolved_count": 0,
        "agent_outcomes_read": False,
        "drafts_modified": False,
        "review_models": {
            "first_pass": {"model": "gpt-5.6-sol", "reasoning_effort": "high"},
            "adjudication": {"model": "gpt-5.6-sol", "reasoning_effort": "xhigh"},
        },
        "artifact_sha256": {
            "FINAL_AUDIT_849.jsonl": sha256_file(jsonl_path),
            "FINAL_AUDIT_849.csv": sha256_file(csv_path),
        },
    }
    write_json(args.output_root / "AUDIT_SUMMARY.json", summary)
    (args.output_root / "DRAFT_DEFINITION_AUDIT_REPORT_ZH.md").write_text(
        markdown_report(summary), encoding="utf-8"
    )
    (args.output_root / "NONCOMPLIANT_CASES_ZH.md").write_text(
        noncompliant_markdown(rows), encoding="utf-8"
    )
    summary["artifact_sha256"].update({
        "DRAFT_DEFINITION_AUDIT_REPORT_ZH.md": sha256_file(
            args.output_root / "DRAFT_DEFINITION_AUDIT_REPORT_ZH.md"
        ),
        "NONCOMPLIANT_CASES_ZH.md": sha256_file(
            args.output_root / "NONCOMPLIANT_CASES_ZH.md"
        ),
    })
    write_json(args.output_root / "AUDIT_SUMMARY.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
