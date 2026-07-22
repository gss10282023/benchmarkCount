#!/usr/bin/env python3
"""Audit the outcome-blind AndroidWorld remaining-75 draft campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml


REQUIRED_PROMOTED_FILES = (
    "checklist.yaml",
    "checklist.json",
    "api_response.json",
    "llm_call.json",
    "reasoning_summary.txt",
    "stderr.log",
    "stdout.log",
)

LABEL_DEPENDENCE_RE = re.compile(
    r"(?ix)("
    r"\b(?:record(?:s|ed)?|stores?|shows?)\b[^.\n]{0,120}\bis_successful\b\s*(?:=|value|field)"
    r"|\bis_successful\s*(?:=|as|value|outcome|score|field)"
    r"|\b(?:retained|stored|recorded|summary)\b[^.\n]{0,80}"
    r"\b(?:native|released[- ]evaluator|evaluator)\s+(?:label|score|scalar|outcome)\b"
    r"[^.\n]{0,80}\b(?:equals?|indicates?|reports?|shows?|is|=)\b"
    r"[^.\n]{0,30}\b(?:success(?:ful)?|fail(?:ure|ed)?|[SF]|1\.0|0\.0)\b"
    r"|\bscalar\s+(?:result|score|outcome)\b"
    r"|\b(?:episode|official|retained|scored)\s+(?:episode\s+)?result\b"
    r"[^.\n]{0,100}\b(?:success(?:ful)?|fail(?:ure|ed)?|1\.0|0\.0|score)\b"
    r")"
)
INSUFFICIENT_RE = re.compile(
    r"(?i)\b(missing|absent|unavailable|no (?:reliable |usable )?retained|no preserved|no reliable|only (?:a stored )?summary|"
    r"not (?:preserved|retained|recorded|available)|"
    r"do(?:es)? not (?:both )?(?:reliably )?(?:show|establish|preserve|provide|let|recover|expose|reveal|identify|include|reconstruct)|"
    r"lacks? (?:the |a usable|either |underlying|usable|reliable|enough|timing|decisive)|"
    r"insufficient|cannot (?:be )?(?:determined|reconstructed|established|recovered|checked|compared)|"
    r"not recoverable|internally inconsistent|stored evidence does not|"
    r"raised before|exception|nan|non[- ]?numeric|conflicting|ambiguous|incomplete)\b"
)
EXCEPTION_OR_MISSING_RE = re.compile(
    r"(?i)\b(exception|nan|failed[- ]result|failure[- ]result)\b"
)
OUTCOME_LEAK_RE = re.compile(
    r"(?ix)("
    r"\bAgent\s*[ABC]\b|\bagent_[abc]\b|\bfull-androidworld-\b|"
    r"results/full/androidworld|adapter/raw_run\.json|native_evaluator_output\.json|"
    r"\bbenchmark[ -]conflict\b|\breleased[- ]evaluator\s+label\s+(?:was|is|=)"
    r")"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def iter_text(node: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(node, dict):
        for key, value in node.items():
            yield from iter_text(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from iter_text(value, f"{path}[{index}]")
    elif isinstance(node, str):
        yield path, node


def add_issue(
    issues: list[dict[str, str]], case_id: str, code: str, location: str, message: str
) -> None:
    issues.append(
        {"case_id": case_id, "code": code, "location": location, "message": message}
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-ids", type=Path, required=True)
    parser.add_argument("--packet-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--validator", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--expected-model", default="gpt-5.4")
    parser.add_argument("--expected-reasoning", default="high")
    parser.add_argument("--expected-count", type=int, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    expected = [line.strip() for line in args.case_ids.read_text().splitlines() if line.strip()]
    expected_set = set(expected)
    issues: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    cases: list[dict[str, Any]] = []

    expected_count = args.expected_count if args.expected_count is not None else len(expected)
    if len(expected) != expected_count or len(expected_set) != expected_count or expected != sorted(expected):
        add_issue(
            issues,
            "_campaign",
            "case_id_set",
            str(args.case_ids),
            f"Expected {expected_count} unique sorted case ids",
        )

    actual_dirs = {
        path.name
        for path in args.result_root.iterdir()
        if path.is_dir() and not path.name.startswith("_")
    }
    if actual_dirs != expected_set:
        add_issue(
            issues,
            "_campaign",
            "result_case_set",
            str(args.result_root),
            f"missing={sorted(expected_set - actual_dirs)!r}; extra={sorted(actual_dirs - expected_set)!r}",
        )

    batch_rows: dict[str, dict[str, Any]] = {}
    batch_path = args.result_root / "_batch_results.jsonl"
    if batch_path.is_file():
        for line in batch_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            batch_rows[str(row.get("case_unit_dir"))] = row
    else:
        add_issue(issues, "_campaign", "missing_batch_results", str(batch_path), "Batch results JSONL is missing")

    stronger_cases: list[str] = []
    attempt_histogram: Counter[int] = Counter()
    for case_id in expected:
        packet = args.packet_root / case_id / "case_packet.md"
        result_dir = args.result_root / case_id
        case_issues_before = len(issues)
        for name in REQUIRED_PROMOTED_FILES:
            if not (result_dir / name).is_file():
                add_issue(issues, case_id, "missing_sidecar", str(result_dir / name), f"Missing promoted file {name}")
        if not packet.is_file() or not (result_dir / "checklist.yaml").is_file():
            continue

        validation = subprocess.run(
            [sys.executable, str(args.validator), str(result_dir / "checklist.yaml"), "--case-packet", str(packet)],
            capture_output=True,
            text=True,
            check=False,
        )
        if validation.returncode != 0:
            add_issue(
                issues,
                case_id,
                "canonical_validator",
                "$.checklist",
                (validation.stderr or validation.stdout).strip(),
            )

        checklist = yaml.safe_load((result_dir / "checklist.yaml").read_text(encoding="utf-8"))
        if (result_dir / "checklist.json").is_file():
            checklist_json = json.loads((result_dir / "checklist.json").read_text(encoding="utf-8"))
            if checklist_json != checklist:
                add_issue(issues, case_id, "yaml_json_mismatch", "$.checklist", "Promoted YAML and JSON differ semantically")

        for field in ("case_unit_id", "task_id"):
            if checklist.get(field) != case_id:
                add_issue(issues, case_id, "identity_mismatch", f"$.{field}", f"Observed {checklist.get(field)!r}")
        if checklist.get("domain") != "androidworld":
            add_issue(issues, case_id, "domain_mismatch", "$.domain", f"Observed {checklist.get('domain')!r}")

        native = checklist.get("native") or {}
        for path, text in iter_text(checklist):
            match = OUTCOME_LEAK_RE.search(text)
            if match:
                add_issue(issues, case_id, "outcome_or_conflict_leakage", path, f"Matched {match.group(0)!r}")

        for field in ("decisive_artifacts", "success_if", "fail_if"):
            for index, item in enumerate(native.get(field) or []):
                text = " ".join(str(value) for key, value in item.items() if key in {"artifact", "question", "text"})
                match = LABEL_DEPENDENCE_RE.search(text)
                explains_done_gate = bool(
                    re.search(r"(?i)\bdone\s*=\s*false\b", text)
                    and re.search(r"(?i)\b(runner|done gate|gates?|forced)\b", text)
                )
                if match and not explains_done_gate:
                    add_issue(
                        issues,
                        case_id,
                        "released_label_as_decisive_evidence",
                        f"$.native.{field}[{index}]",
                        f"Decision rule/artifact appears to depend on released evaluator output: {match.group(0)!r}",
                    )

        for index, item in enumerate(native.get("fail_if") or []):
            text = str(item.get("text") or "")
            match = EXCEPTION_OR_MISSING_RE.search(text)
            if match:
                add_issue(
                    issues,
                    case_id,
                    "insufficient_evidence_misclassified_as_failure",
                    f"$.native.fail_if[{index}]",
                    f"Failure rule contains evidence-insufficiency/exception token {match.group(0)!r}",
                )
        for index, item in enumerate(native.get("undecided_if") or []):
            text = str(item.get("text") or "")
            if not INSUFFICIENT_RE.search(text):
                warnings.append(
                    {
                        "case_id": case_id,
                        "code": "undecided_rule_requires_manual_check",
                        "location": f"$.native.undecided_if[{index}]",
                        "message": text,
                    }
                )

        stronger = (checklist.get("stronger") or {}).get("additional_conditions") or []
        if stronger:
            stronger_cases.append(case_id)
        for index, condition in enumerate(stronger):
            rationale = str(condition.get("rationale") or "")
            text = str(condition.get("text") or "")
            if not re.search(r"(?i)\b(evaluator|native|benchmark|beyond|gap|only checks?)\b", rationale + " " + text):
                warnings.append(
                    {
                        "case_id": case_id,
                        "code": "stronger_gap_requires_manual_check",
                        "location": f"$.stronger.additional_conditions[{index}]",
                        "message": "Condition does not explicitly name the task/evaluator gap",
                    }
                )

        llm_path = result_dir / "llm_call.json"
        if llm_path.is_file():
            llm = json.loads(llm_path.read_text(encoding="utf-8"))
            checks = {
                "provider": (llm.get("provider"), "codex_cli"),
                "model": (llm.get("model"), args.expected_model),
                "phase": (llm.get("phase"), "draft"),
                "domain": (llm.get("domain"), "androidworld"),
                "case_unit_id": (llm.get("case_unit_id"), case_id),
                "reasoning_effort": ((llm.get("response_metadata") or {}).get("reasoning_effort"), args.expected_reasoning),
                "auth_mode": ((llm.get("response_metadata") or {}).get("auth_mode"), "codex_login"),
            }
            for field, (observed, wanted) in checks.items():
                if observed != wanted:
                    add_issue(issues, case_id, "llm_config_mismatch", f"$.llm_call.{field}", f"observed={observed!r}, expected={wanted!r}")

        batch = batch_rows.get(case_id)
        if not batch or batch.get("status") != "success":
            add_issue(issues, case_id, "batch_status", "$._batch_results", f"Observed {batch!r}")
            attempts = 0
        else:
            attempts = len(batch.get("attempts") or [])
            attempt_histogram[attempts] += 1
            promoted_attempt = batch.get("attempts", [])[-1] if attempts else {}
            if not str(promoted_attempt.get("validator") or "").startswith("checklist valid:"):
                add_issue(issues, case_id, "promoted_attempt_not_valid", "$._batch_results", str(promoted_attempt))

        cases.append(
            {
                "case_id": case_id,
                "status": "pass" if len(issues) == case_issues_before else "fail",
                "attempts": attempts,
                "stronger_condition_count": len(stronger),
                "checklist_sha256": sha256_file(result_dir / "checklist.yaml"),
            }
        )

    summary_path = args.result_root / "_batch_summary.json"
    batch_summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.is_file() else None
    if batch_summary is None:
        add_issue(issues, "_campaign", "missing_batch_summary", str(summary_path), "Batch summary is missing")

    report = {
        "schema_version": "androidworld_remaining75_draft_audit/v1",
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "case_count": len(expected),
            "packet_root": str(args.packet_root.resolve()),
            "result_root": str(args.result_root.resolve()),
            "outcome_blind": True,
            "released_evaluator_label_allowed_as_decisive_evidence": False,
            "benchmark_conflict_is_out_of_scope": True,
        },
        "expected_generation_config": {
            "provider": "codex_cli",
            "model": args.expected_model,
            "reasoning_effort": args.expected_reasoning,
            "max_parallel": 11,
            "sandbox": "read-only",
        },
        "decision": "pass" if not issues else "fail",
        "counts": {
            "expected_cases": len(expected),
            "result_case_dirs": len(actual_dirs),
            "batch_success_rows": sum(row.get("status") == "success" for row in batch_rows.values()),
            "case_pass": sum(row["status"] == "pass" for row in cases),
            "case_fail": sum(row["status"] == "fail" for row in cases),
            "blocking_issues": len(issues),
            "manual_review_warnings": len(warnings),
            "stronger_positive_cases": len(stronger_cases),
        },
        "attempt_histogram": {str(key): value for key, value in sorted(attempt_histogram.items())},
        "stronger_positive_cases": stronger_cases,
        "blocking_issues": issues,
        "manual_review_warnings": warnings,
        "cases": cases,
        "batch_summary": batch_summary,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": report["decision"], "counts": report["counts"]}, ensure_ascii=False))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
