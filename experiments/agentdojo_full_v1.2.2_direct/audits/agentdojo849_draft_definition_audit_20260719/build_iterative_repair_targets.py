#!/usr/bin/env python3
"""Build normalized repair targets from review plus finding adjudication receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-root", type=Path, required=True)
    parser.add_argument("--draft-root", type=Path, required=True)
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--adjudication-root", type=Path, required=True)
    parser.add_argument("--output-jsonl", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def main() -> int:
    args = parse_args()
    rows: list[dict[str, Any]] = []
    for adjudication_path in sorted(
        (args.adjudication_root / "cases").glob("*/adjudication.json")
    ):
        adjudication = json.loads(adjudication_path.read_text(encoding="utf-8"))
        if adjudication["final_decision"] != "fail":
            continue
        name = adjudication["directory_name"]
        review_path = args.review_root / "cases" / name / "review.json"
        review = json.loads(review_path.read_text(encoding="utf-8"))
        first_findings = [
            {"finding_id": f"F{index}", **finding}
            for index, finding in enumerate(
                review["model_review"]["blocking_findings"], start=1
            )
        ]
        by_id = {item["finding_id"]: item for item in first_findings}
        sustained: list[dict[str, Any]] = []
        for item in adjudication["adjudication"]["finding_adjudications"]:
            if item["verdict"] != "sustain":
                continue
            allegation = by_id[item["finding_id"]]
            if item["original_code"] != allegation["code"]:
                raise ValueError(f"finding code mismatch: {name} {item['finding_id']}")
            sustained.append({
                "finding_id": item["finding_id"],
                "code": item["original_code"],
                "checklist_path": allegation["checklist_path"],
                "first_pass_explanation": allegation["explanation"],
                "first_pass_source_pointers": allegation["source_pointers"],
                "adjudication_rationale": item["rationale"],
                "adjudication_source_pointers": item["source_pointers"],
            })
        if not sustained:
            raise ValueError(f"failed adjudication has no sustained finding: {name}")
        packet_path = args.packet_root / name / "case_packet.md"
        checklist_path = args.draft_root / name / "checklist.yaml"
        if sha256(packet_path) != adjudication["packet_sha256"]:
            raise ValueError(f"packet hash mismatch: {name}")
        if sha256(checklist_path) != adjudication["checklist_sha256"]:
            raise ValueError(f"checklist hash mismatch: {name}")
        rows.append({
            "schema_version": "agentdojo_iterative_repair_target/v1",
            "directory_name": name,
            "case_unit_id": review["case_unit_id"],
            "packet_sha256": adjudication["packet_sha256"],
            "checklist_sha256": adjudication["checklist_sha256"],
            "final_status": "noncompliant",
            "deterministic_blocking_findings": [],
            "sustained_findings": sustained,
            "agent_outcomes_read": False,
        })
    if not rows:
        raise SystemExit("no failed adjudications")
    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    args.output_jsonl.write_bytes(b"".join(canonical(row) for row in rows))
    print(json.dumps({
        "case_count": len(rows),
        "sustained_finding_count": sum(len(row["sustained_findings"]) for row in rows),
        "agent_outcomes_read": False,
        "output": str(args.output_jsonl),
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
