#!/usr/bin/env python3
"""Assemble hash-bound semantic acceptance receipts for the final 849 drafts."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_CASES = 849
EXPECTED_REPAIRS = 460


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-final-audit", type=Path, required=True)
    parser.add_argument("--draft-root", type=Path, required=True)
    parser.add_argument("--review-root", type=Path, action="append", default=[])
    parser.add_argument("--adjudication-root", type=Path, action="append", default=[])
    parser.add_argument("--output-root", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    original_rows: dict[str, dict[str, Any]] = {}
    with args.original_final_audit.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                original_rows[row["directory_name"]] = row
    if len(original_rows) != EXPECTED_CASES:
        raise ValueError(f"expected {EXPECTED_CASES} original audit rows")

    receipt_index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for root in args.review_root:
        for path in root.glob("cases/*/review.json"):
            receipt = read_json(path)
            if receipt.get("decision") != "pass":
                continue
            key = (str(receipt["directory_name"]), str(receipt["checklist_sha256"]))
            receipt_index.setdefault(key, []).append(
                {
                    "kind": "first_review_pass",
                    "path": str(path),
                    "model": receipt.get("model"),
                    "reasoning_effort": receipt.get("reasoning_effort"),
                    "finished_at": receipt.get("finished_at"),
                    "receipt_sha256": sha256(path),
                }
            )
    for root in args.adjudication_root:
        for path in root.glob("cases/*/adjudication.json"):
            receipt = read_json(path)
            if receipt.get("final_decision") != "pass":
                continue
            key = (str(receipt["directory_name"]), str(receipt["checklist_sha256"]))
            receipt_index.setdefault(key, []).append(
                {
                    "kind": "adjudication_pass",
                    "path": str(path),
                    "model": receipt.get("model"),
                    "reasoning_effort": receipt.get("reasoning_effort"),
                    "finished_at": receipt.get("finished_at"),
                    "receipt_sha256": sha256(path),
                }
            )

    rows: list[dict[str, Any]] = []
    repaired_count = 0
    for name in sorted(original_rows):
        original = original_rows[name]
        current_hash = sha256(args.draft_root / name / "checklist.yaml")
        if original.get("final_status") == "compliant":
            status = "pass" if current_hash == original["checklist_sha256"] else "fail"
            evidence = {
                "kind": "original_locked_audit_pass",
                "path": str(args.original_final_audit),
                "original_checklist_sha256": original["checklist_sha256"],
            }
        else:
            repaired_count += 1
            matches = receipt_index.get((name, current_hash), [])
            status = "pass" if matches else "fail"
            evidence = matches[-1] if matches else {"kind": "missing_hash_bound_pass_receipt"}
        rows.append(
            {
                "case_unit_id": original["case_unit_id"],
                "directory_name": name,
                "current_checklist_sha256": current_hash,
                "original_final_status": original["final_status"],
                "acceptance_status": status,
                "acceptance_evidence": evidence,
                "agent_outcomes_read": False,
            }
        )

    if repaired_count != EXPECTED_REPAIRS:
        raise ValueError(f"expected {EXPECTED_REPAIRS} repaired cases, found {repaired_count}")
    args.output_root.mkdir(parents=True, exist_ok=True)
    detail_path = args.output_root / "FINAL_SEMANTIC_ACCEPTANCE_849.jsonl"
    detail_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    counts = Counter(row["acceptance_status"] for row in rows)
    summary = {
        "schema_version": "agentdojo849_hash_bound_semantic_acceptance/v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "case_count": len(rows),
        "repaired_case_count": repaired_count,
        "status_counts": dict(sorted(counts.items())),
        "agent_outcomes_read": False,
        "score_artifacts_read": False,
        "detail_path": str(detail_path),
    }
    write_json(args.output_root / "SEMANTIC_ACCEPTANCE_SUMMARY.json", summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if counts == {"pass": EXPECTED_CASES} else 2


if __name__ == "__main__":
    raise SystemExit(main())
