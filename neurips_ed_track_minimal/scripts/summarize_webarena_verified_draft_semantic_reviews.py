#!/usr/bin/env python3
"""Validate and summarize per-case WebArena-Verified semantic review artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from neurips_ed_track_minimal.scripts import (  # noqa: E402
    review_case_checklist_with_codex as reviewer,
)
from neurips_ed_track_minimal.scripts.run_webarena_verified_draft_semantic_reviews import (  # noqa: E402
    REVIEW_ITEM_IDS,
    REVIEW_SCHEMA,
    numeric_case_key,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--case-packet-root", type=Path, required=True)
    parser.add_argument("--draft-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, default=812)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected object in {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def audit_case(
    case_id: str,
    review_path: Path,
    case_packet_path: Path,
    checklist_path: Path,
) -> dict[str, Any]:
    body = reviewer.validate_model_review_body(
        load_json(review_path),
        REVIEW_SCHEMA,
        review_item_ids=REVIEW_ITEM_IDS,
    )
    sidecars = reviewer.sidecar_paths_for_output(review_path)
    missing_sidecars = [name for name, path in sidecars.items() if not path.is_file()]
    if missing_sidecars:
        raise ValueError(f"{case_id}: missing sidecars: {', '.join(missing_sidecars)}")
    llm_call = load_json(sidecars["llm_call"])
    expected_llm_fields = {
        "case_unit_id": case_id,
        "domain": "webarena_verified",
        "phase": "checklist_model_review",
        "experiment_type": "webarena_verified_full_812",
        "agent_id_or_role": "case_checklist_semantic_reviewer",
        "provider": "codex_cli",
        "model": "gpt-5.6-sol",
    }
    mismatches = {
        field: {"expected": expected, "actual": llm_call.get(field)}
        for field, expected in expected_llm_fields.items()
        if llm_call.get(field) != expected
    }
    if mismatches:
        raise ValueError(f"{case_id}: LLM sidecar mismatch: {mismatches}")
    failed_items = [
        item["id"] for item in body["checklist_items"] if item["status"] == "fail"
    ]
    findings = body["blocking_findings"]
    return {
        "case_id": case_id,
        "decision": body["decision"],
        "failed_item_ids": failed_items,
        "finding_ids": [finding["id"] for finding in findings],
        "finding_item_ids": [finding["checklist_item_id"] for finding in findings],
        "finding_messages": [finding["message"] for finding in findings],
        "required_changes": [finding["required_change"] for finding in findings],
        "review_sha256": sha256_file(review_path),
        "case_packet_sha256": sha256_file(case_packet_path),
        "checklist_sha256": sha256_file(checklist_path),
        "model": llm_call["model"],
        "reasoning_effort": llm_call["response_metadata"]["reasoning_effort"],
        "sandbox": llm_call["response_metadata"]["sandbox"],
        "review_path": str(review_path),
    }


def main() -> int:
    args = parse_args()
    review_paths = {
        path.parent.name: path for path in args.review_root.glob("*/review.json")
    }
    packet_paths = {
        path.parent.name: path for path in args.case_packet_root.glob("*/case_packet.md")
    }
    checklist_paths = {
        path.parent.name: path for path in args.draft_root.glob("*/checklist.yaml")
    }
    ids = set(review_paths)
    if len(ids) != args.expected_count:
        raise SystemExit(
            f"Expected {args.expected_count} promoted reviews, found {len(ids)}"
        )
    if ids != set(packet_paths) or ids != set(checklist_paths):
        raise SystemExit("Review, packet, and draft case-id sets do not match")

    cases = [
        audit_case(
            case_id,
            review_paths[case_id],
            packet_paths[case_id],
            checklist_paths[case_id],
        )
        for case_id in sorted(ids, key=numeric_case_key)
    ]
    decision_counts = Counter(case["decision"] for case in cases)
    failed_item_counts = Counter(
        item_id for case in cases for item_id in case["failed_item_ids"]
    )
    report = {
        "schema_version": "webarena_verified_draft_semantic_review_index/v1",
        "case_count": len(cases),
        "decision_counts": dict(sorted(decision_counts.items())),
        "failed_item_counts": {
            item_id: failed_item_counts[item_id] for item_id in REVIEW_ITEM_IDS
        },
        "review_item_ids": list(REVIEW_ITEM_IDS),
        "cases": cases,
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    write_json(args.output_root / "semantic_review_index.json", report)

    csv_path = args.output_root / "semantic_review_index.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "case_id",
            "decision",
            "failed_item_ids",
            "finding_ids",
            "finding_item_ids",
            "finding_messages",
            "required_changes",
            "review_sha256",
            "case_packet_sha256",
            "checklist_sha256",
            "model",
            "reasoning_effort",
            "sandbox",
            "review_path",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for case in cases:
            writer.writerow(
                {
                    **case,
                    "failed_item_ids": " | ".join(case["failed_item_ids"]),
                    "finding_ids": " | ".join(case["finding_ids"]),
                    "finding_item_ids": " | ".join(case["finding_item_ids"]),
                    "finding_messages": " | ".join(case["finding_messages"]),
                    "required_changes": " | ".join(case["required_changes"]),
                }
            )

    markdown = [
        "# WebArena-Verified draft semantic review index",
        "",
        f"- Cases reviewed: {len(cases)}",
        f"- Accept: {decision_counts.get('accept', 0)}",
        f"- Revise: {decision_counts.get('revise', 0)}",
        "- Review boundary per case: `case_packet.md`, `checklist.yaml`, pinned review prompt only",
        "- Benchmark run outputs and checklist score were not read",
        "",
        "## Failed-item counts",
        "",
        "| Review item | Cases failed |",
        "|---|---:|",
    ]
    markdown.extend(
        f"| `{item_id}` | {failed_item_counts[item_id]} |"
        for item_id in REVIEW_ITEM_IDS
    )
    markdown.extend(
        [
            "",
            "## Per-case verdicts",
            "",
            "| Case | Verdict | Failed items | Findings |",
            "|---:|---|---|---|",
        ]
    )
    for case in cases:
        findings = "; ".join(case["finding_messages"]).replace("|", "\\|")
        failed = ", ".join(case["failed_item_ids"]).replace("|", "\\|")
        markdown.append(
            f"| {case['case_id']} | {case['decision']} | {failed} | {findings} |"
        )
    (args.output_root / "SEMANTIC_REVIEW.md").write_text(
        "\n".join(markdown) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["decision_counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
