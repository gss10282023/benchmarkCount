#!/usr/bin/env python3
"""Translate every confirmed WebArena-Verified draft revision finding to Chinese."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
from pathlib import Path
from typing import Any


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

TRANSLATION_PROMPT = """你是严谨的技术翻译者。请把输入 JSON 中每条 finding 的 problem_en 和 required_change_en
忠实翻译为简体中文，并输出符合指定 JSON Schema 的对象。

硬性要求：
1. case_id、finding_id、section_id 必须原样保留；case 和 finding 的数量、顺序必须完全一致。
2. problem_zh 只翻译 problem_en；required_change_zh 只翻译 required_change_en。不得增加、删除、合并、裁决或修复任何 finding。
3. 精确保留代码标识符、字段名、文件名、路径、JSON/YAML key、类名、方法名、枚举值、URL、数字和字符串字面量；必要时用反引号包裹。
4. success、failure、undecided、normalization、parser、evaluator、artifact 等术语可以使用中文解释，但必须保持技术含义。
5. 不要读取文件、不要使用工具、不要引用输入之外的信息、不要输出说明文字。

待翻译 JSON：
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--adjudication-json", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--case-ids", nargs="*")
    parser.add_argument("--batch-size", type=int, default=10)
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


def collect_sources(args: argparse.Namespace) -> list[dict[str, Any]]:
    adjudication = load_json(args.adjudication_json)
    selected_ids = set(args.case_ids or [])
    case_ids = [
        str(case["case_id"])
        for case in adjudication["cases"]
        if case["adjudicated_decision"] == "revise"
        and (not selected_ids or str(case["case_id"]) in selected_ids)
    ]
    if selected_ids and set(case_ids) != selected_ids:
        missing = sorted(selected_ids - set(case_ids), key=int)
        raise ValueError(f"Requested IDs are not confirmed revisions: {missing}")

    sources: list[dict[str, Any]] = []
    for case_id in case_ids:
        review = load_json(args.review_root / case_id / "review.json")
        findings = review.get("blocking_findings")
        if not isinstance(findings, list) or not findings:
            raise ValueError(f"Case {case_id} has no blocking findings")
        sources.append(
            {
                "case_id": case_id,
                "findings": [
                    {
                        "finding_id": str(finding["id"]),
                        "section_id": str(finding["checklist_item_id"]),
                        "problem_en": str(finding["message"]),
                        "required_change_en": str(finding["required_change"]),
                    }
                    for finding in findings
                ],
            }
        )
    return sources


def validate_translation(source_batch: list[dict[str, Any]], translated: Any) -> dict[str, Any]:
    if not isinstance(translated, dict) or set(translated) != {"translations"}:
        raise ValueError("Translation output must contain only translations")
    rows = translated["translations"]
    if not isinstance(rows, list) or len(rows) != len(source_batch):
        raise ValueError("Translation case count mismatch")
    for source_case, translated_case in zip(source_batch, rows, strict=True):
        if translated_case.get("case_id") != source_case["case_id"]:
            raise ValueError("Translation case order or ID mismatch")
        source_findings = source_case["findings"]
        translated_findings = translated_case.get("findings")
        if not isinstance(translated_findings, list) or len(translated_findings) != len(source_findings):
            raise ValueError(f"Case {source_case['case_id']} finding count mismatch")
        for source_finding, translated_finding in zip(source_findings, translated_findings, strict=True):
            for key in ("finding_id", "section_id"):
                if translated_finding.get(key) != source_finding[key]:
                    raise ValueError(f"Case {source_case['case_id']} {key} changed during translation")
            for key in ("problem_zh", "required_change_zh"):
                value = translated_finding.get(key)
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"Case {source_case['case_id']} missing {key}")
    return translated


def codex_command(args: argparse.Namespace, output_path: Path) -> list[str]:
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


async def translate_batch(
    args: argparse.Namespace,
    semaphore: asyncio.Semaphore,
    batch_index: int,
    source_batch: list[dict[str, Any]],
) -> dict[str, Any]:
    batch_dir = args.output_root / "batches" / f"batch_{batch_index:04d}"
    final_path = batch_dir / "translation.json"
    if final_path.exists():
        return validate_translation(source_batch, load_json(final_path))

    batch_dir.mkdir(parents=True, exist_ok=True)
    write_json(batch_dir / "source.json", {"cases": source_batch})
    prompt = TRANSLATION_PROMPT + json.dumps({"cases": source_batch}, ensure_ascii=False, separators=(",", ":"))

    async with semaphore:
        errors: list[str] = []
        for attempt in range(1, args.max_attempts + 1):
            output_path = batch_dir / f"attempt_{attempt:02d}.output.json"
            process = await asyncio.create_subprocess_exec(
                *codex_command(args, output_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
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
                errors.append(
                    f"attempt {attempt}: exit {process.returncode}: "
                    f"{stderr.decode('utf-8', errors='replace')[-1000:]}"
                )
                continue
            try:
                translated = validate_translation(source_batch, load_json(output_path))
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                errors.append(f"attempt {attempt}: {exc}")
                continue
            write_json(final_path, translated)
            return translated
        raise RuntimeError(f"Batch {batch_index} failed: {'; '.join(errors)}")


def render_outputs(
    output_root: Path,
    sources: list[dict[str, Any]],
    translations: list[dict[str, Any]],
) -> None:
    source_by_id = {case["case_id"]: case for case in sources}
    translated_cases = [case for batch in translations for case in batch["translations"]]
    if len(translated_cases) != len(sources):
        raise ValueError("Combined translation count mismatch")

    combined_cases: list[dict[str, Any]] = []
    for translated_case in translated_cases:
        case_id = translated_case["case_id"]
        source_case = source_by_id[case_id]
        combined_findings = []
        for source_finding, translated_finding in zip(
            source_case["findings"], translated_case["findings"], strict=True
        ):
            combined_findings.append({**source_finding, **translated_finding})
        combined_cases.append({"case_id": case_id, "findings": combined_findings})

    finding_count = sum(len(case["findings"]) for case in combined_cases)
    combined = {
        "schema_version": "webarena_verified_revision_details_zh/v1",
        "case_count": len(combined_cases),
        "finding_count": finding_count,
        "cases": combined_cases,
    }
    write_json(output_root / "draft_revision_details_zh.json", combined)

    with (output_root / "draft_revision_details_zh.csv").open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "case_id", "finding_id", "section_id", "section_zh",
            "problem_zh", "required_change_zh", "problem_en", "required_change_en",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for case in combined_cases:
            for finding in case["findings"]:
                writer.writerow(
                    {
                        "case_id": case["case_id"],
                        "finding_id": finding["finding_id"],
                        "section_id": finding["section_id"],
                        "section_zh": SECTION_ZH[finding["section_id"]],
                        "problem_zh": finding["problem_zh"],
                        "required_change_zh": finding["required_change_zh"],
                        "problem_en": finding["problem_en"],
                        "required_change_en": finding["required_change_en"],
                    }
                )

    markdown = [
        f"# WebArena-Verified：{len(combined_cases)} 个需修改 draft 的逐 case 修改说明", "",
        f"- 需修改 case 数：{len(combined_cases)}",
        f"- 具体 blocking finding 数：{finding_count}",
        "- 每条均列出：修改位置、为什么修改、应如何修改。",
        "- 中文内容是原始英文 finding/required_change 的忠实翻译；英文原文保留在同目录 JSON/CSV 中。",
        "- 本报告是修改要求，不表示原始 draft 已经被改写。", "",
    ]
    for case in combined_cases:
        markdown.extend(
            [
                f"## Case {case['case_id']}", "",
                f"原始审核记录：`semantic_reviews_gpt56_xhigh_v1/{case['case_id']}/review.json`", "",
            ]
        )
        for index, finding in enumerate(case["findings"], start=1):
            markdown.extend(
                [
                    f"### 修改项 {index}：{SECTION_ZH[finding['section_id']]}", "",
                    f"- Finding ID：`{finding['finding_id']}`",
                    f"- 为什么修改：{finding['problem_zh']}",
                    f"- 应如何修改：{finding['required_change_zh']}", "",
                ]
            )
    (output_root / "DRAFT_REVISION_DETAILS_ZH.md").write_text("\n".join(markdown), encoding="utf-8")


async def async_main(args: argparse.Namespace) -> None:
    sources = collect_sources(args)
    if args.batch_size <= 0 or args.max_parallel <= 0:
        raise ValueError("batch-size and max-parallel must be positive")
    batches = [sources[index : index + args.batch_size] for index in range(0, len(sources), args.batch_size)]
    args.output_root.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(args.max_parallel)
    translations = await asyncio.gather(
        *(translate_batch(args, semaphore, batch_index, source_batch)
          for batch_index, source_batch in enumerate(batches, start=1))
    )
    render_outputs(args.output_root, sources, translations)
    print(json.dumps(
        {
            "case_count": len(sources),
            "finding_count": sum(len(case["findings"]) for case in sources),
            "batch_count": len(batches),
        }, ensure_ascii=False
    ))


def main() -> int:
    args = parse_args()
    asyncio.run(async_main(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
