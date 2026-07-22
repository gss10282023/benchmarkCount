#!/usr/bin/env python3
"""Add original case, benchmark measurement, and original draft context to the Chinese revision report."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
from pathlib import Path
from typing import Any

import yaml


SECTION_ZH = {
    "identity_and_scope": "case 身份与范围",
    "native_user_goal": "native.user_goal",
    "official_evaluator_semantics": "native.benchmark_success / 官方 evaluator 语义",
    "evaluator_composition": "native.checked_by 及 evaluator 组合规则",
    "decisive_post_run_evidence": "native.decisive_artifacts",
    "decision_rules": "native.success_if / fail_if / undecided_if",
    "source_support_pointers": "support 来源指针",
    "stronger_conditions": "stronger.additional_conditions",
    "minimality_and_no_run_leakage": "native 整体最小性、内部一致性及无运行结果泄漏",
}

PROMPT = """你是 WebArena-Verified 技术报告编辑。根据输入中固定的 case packet 摘要、官方 task evaluator 配置、
原始 draft 和已经完成的源码口径 review，为每个 case 写三段简体中文说明。

硬性要求：
1. case_id、case 数量和顺序必须原样保留。
2. original_case_zh：说明原始用户任务是什么、站点和 task type；不得加入 packet 外事实。
3. benchmark_measurement_zh：准确说明配置了哪些 evaluator、每个 evaluator 测什么、关键 expected/filter/normalization/last-event 语义，以及 task score 如何组合。只写输入能支持的内容。
4. original_draft_zh：忠实概括原始 draft 实际写了什么，包括它声明的 benchmark success、决定性 artifacts、success/failure/undecided 和非空 stronger conditions。这里不要静默修正 draft，也不要把 review 的修改建议冒充原 draft。
5. 每段应完整但紧凑，通常 2 至 6 句。精确保留字段名、类名、artifact 名、URL、数字、枚举和字符串字面量。
6. 禁止推断或提及实际 benchmark 运行结果；不要读取文件、不要调用工具、不要输出额外说明。

输入 JSON：
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-packet-root", type=Path, required=True)
    parser.add_argument("--draft-root", type=Path, required=True)
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--revision-details-json", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--case-ids", nargs="*")
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--max-parallel", type=int, default=16)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--reasoning-effort", default="medium")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def strip_support(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: strip_support(item) for key, item in value.items() if key != "support"}
    if isinstance(value, list):
        return [strip_support(item) for item in value]
    return value


def packet_summary(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return text.split("## Visibility Boundary", 1)[0].strip()


def collect_sources(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    details = load_json(args.revision_details_json)
    selected_ids = set(args.case_ids or [])
    detail_cases = [
        case for case in details["cases"]
        if not selected_ids or str(case["case_id"]) in selected_ids
    ]
    if selected_ids != set() and {str(case["case_id"]) for case in detail_cases} != selected_ids:
        raise ValueError("Requested case IDs do not exactly match revision details")

    sources: list[dict[str, Any]] = []
    for detail_case in detail_cases:
        case_id = str(detail_case["case_id"])
        packet_dir = args.case_packet_root / case_id
        draft = yaml.safe_load((args.draft_root / case_id / "checklist.yaml").read_text(encoding="utf-8"))
        review = load_json(args.review_root / case_id / "review.json")
        sources.append(
            {
                "case_id": case_id,
                "case_packet_summary": packet_summary(packet_dir / "case_packet.md"),
                "sparse_official_task_config": load_json(packet_dir / "raw_case/derived/tag_task.json"),
                "materialized_task_config": load_json(packet_dir / "raw_case/derived/task.json"),
                "original_draft": strip_support(draft),
                "source_review": {
                    "checklist_items": [
                        {"id": item["id"], "status": item["status"], "rationale": item["rationale"]}
                        for item in review["checklist_items"]
                    ],
                    "revised_checklist": strip_support(review.get("revised_checklist")),
                },
            }
        )
    selected_details = {
        **details,
        "case_count": len(detail_cases),
        "finding_count": sum(len(case["findings"]) for case in detail_cases),
        "cases": detail_cases,
    }
    return sources, selected_details


def validate(source_batch: list[dict[str, Any]], output: Any) -> dict[str, Any]:
    if not isinstance(output, dict) or set(output) != {"contexts"}:
        raise ValueError("Output must contain only contexts")
    contexts = output["contexts"]
    if not isinstance(contexts, list) or len(contexts) != len(source_batch):
        raise ValueError("Context case count mismatch")
    for source, context in zip(source_batch, contexts, strict=True):
        if context.get("case_id") != source["case_id"]:
            raise ValueError("Context case ID/order mismatch")
        minimum_lengths = {
            "original_case_zh": 50,
            "benchmark_measurement_zh": 120,
            "original_draft_zh": 250,
        }
        for key in ("original_case_zh", "benchmark_measurement_zh", "original_draft_zh"):
            value = context.get(key)
            if not isinstance(value, str) or len(value.strip()) < minimum_lengths[key]:
                raise ValueError(f"Case {source['case_id']} has incomplete {key}")
            if not re.search(r"[\u3400-\u9fff]", value):
                raise ValueError(f"Case {source['case_id']} {key} is not Chinese")
        for site in source["sparse_official_task_config"].get("sites", []):
            if site not in context["original_case_zh"]:
                raise ValueError(f"Case {source['case_id']} original_case_zh omits site ID {site}")
        for evaluator in source["sparse_official_task_config"].get("eval", []):
            evaluator_name = evaluator.get("evaluator")
            if evaluator_name and evaluator_name not in context["benchmark_measurement_zh"]:
                raise ValueError(
                    f"Case {source['case_id']} benchmark_measurement_zh omits {evaluator_name}"
                )
        for artifact in source["original_draft"]["native"]["decisive_artifacts"]:
            technical_tokens = re.findall(
                r"[A-Za-z0-9_.-]+\.(?:json|har)|TaskEvalResult|EvaluatorResult",
                artifact["artifact"],
            )
            if any(token not in context["original_draft_zh"] for token in technical_tokens):
                raise ValueError(
                    f"Case {source['case_id']} original_draft_zh omits an artifact token"
                )
        for condition in source["original_draft"].get("stronger", {}).get(
            "additional_conditions", []
        ):
            condition_id = condition.get("id") if isinstance(condition, dict) else None
            if condition_id and condition_id not in context["original_draft_zh"]:
                raise ValueError(
                    f"Case {source['case_id']} original_draft_zh omits stronger ID {condition_id}"
                )
    return output


def command(args: argparse.Namespace, output_path: Path) -> list[str]:
    return [
        "codex", "exec", "--strict-config",
        "--disable", "shell_tool", "--disable", "unified_exec",
        "--cd", str(args.workspace_root.resolve()), "--skip-git-repo-check",
        "--ephemeral", "--ignore-user-config", "--sandbox", "read-only",
        "--model", args.model,
        "-c", f'model_reasoning_effort="{args.reasoning_effort}"',
        "-c", 'model_verbosity="low"',
        "--color", "never", "--json",
        "--output-schema", str(args.schema.resolve()),
        "-o", str(output_path.resolve()), "-",
    ]


async def run_batch(
    args: argparse.Namespace,
    semaphore: asyncio.Semaphore,
    index: int,
    source_batch: list[dict[str, Any]],
) -> dict[str, Any]:
    batch_dir = args.output_root / "context_batches" / f"batch_{index:04d}"
    final = batch_dir / "context.json"
    if final.exists():
        return validate(source_batch, load_json(final))
    batch_dir.mkdir(parents=True, exist_ok=True)
    write_json(batch_dir / "source.json", {"cases": source_batch})
    prompt = PROMPT + json.dumps({"cases": source_batch}, ensure_ascii=False, separators=(",", ":"))

    async with semaphore:
        errors: list[str] = []
        for attempt in range(1, args.max_attempts + 1):
            output_path = batch_dir / f"attempt_{attempt:02d}.output.json"
            process = await asyncio.create_subprocess_exec(
                *command(args, output_path), stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy(),
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(prompt.encode("utf-8")), timeout=args.timeout_seconds
                )
            except TimeoutError:
                process.kill()
                await process.wait()
                errors.append(f"attempt {attempt}: timeout")
                continue
            (batch_dir / f"attempt_{attempt:02d}.stdout.jsonl").write_bytes(stdout)
            (batch_dir / f"attempt_{attempt:02d}.stderr.log").write_bytes(stderr)
            if process.returncode != 0:
                errors.append(f"attempt {attempt}: exit {process.returncode}")
                continue
            try:
                result = validate(source_batch, load_json(output_path))
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                errors.append(f"attempt {attempt}: {exc}")
                continue
            write_json(final, result)
            return result
        raise RuntimeError(f"Context batch {index} failed: {'; '.join(errors)}")


def render(args: argparse.Namespace, details: dict[str, Any], batches: list[dict[str, Any]]) -> None:
    contexts = [context for batch in batches for context in batch["contexts"]]
    context_by_id = {context["case_id"]: context for context in contexts}
    if len(context_by_id) != len(details["cases"]):
        raise ValueError("Combined context count mismatch")

    enriched_cases = []
    for case in details["cases"]:
        case_id = str(case["case_id"])
        enriched_cases.append({**case, **context_by_id[case_id]})
    finding_count = sum(len(case["findings"]) for case in enriched_cases)
    enriched = {
        "schema_version": "webarena_verified_revision_details_enriched_zh/v1",
        "case_count": len(enriched_cases),
        "finding_count": finding_count,
        "cases": enriched_cases,
    }
    write_json(args.output_root / "draft_revision_details_enriched_zh.json", enriched)

    with (args.output_root / "draft_revision_context_zh.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["case_id", "original_case_zh", "benchmark_measurement_zh", "original_draft_zh"],
        )
        writer.writeheader()
        for case in enriched_cases:
            writer.writerow({key: case[key] for key in writer.fieldnames})

    markdown = [
        f"# WebArena-Verified：{len(enriched_cases)} 个需修改 draft 的逐 case 修改说明", "",
        f"- 需修改 case 数：{len(enriched_cases)}",
        f"- 具体 blocking finding 数：{finding_count}",
        "- 每个 case 均依次说明：原始 case、benchmark 如何测、原始 draft、修改位置、修改原因和具体改法。",
        "- 原始 case 和 benchmark 摘要仅来自 case packet、官方 task 配置及已完成的源码口径 review，不读取实际运行结果。",
        "- 本报告是修改要求，不表示原始 draft 已经被改写。", "",
    ]
    for case in enriched_cases:
        markdown.extend(
            [
                f"## Case {case['case_id']}", "",
                "### 原本 case 是什么", "", case["original_case_zh"], "",
                "### Benchmark 怎么测", "", case["benchmark_measurement_zh"], "",
                "### 原本 draft 是什么", "", case["original_draft_zh"], "",
                "### 需要修改的部分", "",
            ]
        )
        for index, finding in enumerate(case["findings"], start=1):
            markdown.extend(
                [
                    f"#### 修改项 {index}：{SECTION_ZH[finding['section_id']]}", "",
                    f"- Finding ID：`{finding['finding_id']}`",
                    f"- 为什么修改：{finding['problem_zh']}",
                    f"- 应如何修改：{finding['required_change_zh']}", "",
                ]
            )
    (args.output_root / "DRAFT_REVISION_DETAILS_ZH.md").write_text("\n".join(markdown), encoding="utf-8")


async def async_main(args: argparse.Namespace) -> None:
    sources, details = collect_sources(args)
    batches = [sources[index:index + args.batch_size] for index in range(0, len(sources), args.batch_size)]
    semaphore = asyncio.Semaphore(args.max_parallel)
    results = await asyncio.gather(
        *(run_batch(args, semaphore, index, batch) for index, batch in enumerate(batches, start=1))
    )
    render(args, details, results)
    print(json.dumps(
        {"case_count": len(sources), "finding_count": details["finding_count"], "batch_count": len(batches)},
        ensure_ascii=False,
    ))


def main() -> int:
    args = parse_args()
    asyncio.run(async_main(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
