#!/usr/bin/env python3
"""Independent acceptance checks for the Step 2 reconstruction."""

from __future__ import annotations

import argparse
import csv
import json
import tempfile
from pathlib import Path
from typing import Any

from build_reconstruction import GENERATED_FILES, build, git_bytes, sha256_bytes, sha256_file


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--status", type=Path, required=True)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()

    checks: list[dict[str, Any]] = []

    def check(check_id: str, condition: bool, observed: Any, expected: Any) -> None:
        checks.append({
            "check_id": check_id,
            "status": "PASS" if condition else "FAIL",
            "observed": observed,
            "expected": expected,
        })

    summary = json.loads((output_dir / "table_reconstruction_manifest_summary.json").read_text(encoding="utf-8"))
    check("record_count", summary["record_count"] == 1282, summary["record_count"], 1282)
    check("unique_record_keys", summary["unique_record_keys"] == 1282, summary["unique_record_keys"], 1282)
    check("review_item_counts", (summary["physical_review_items"], summary["expanded_review_links"]) == (126, 133), [summary["physical_review_items"], summary["expanded_review_links"]], [126, 133])
    check("final_label_coverage", (summary["nonblank_final_label_links"], summary["changed_final_labels"]) == (63, 38), [summary["nonblank_final_label_links"], summary["changed_final_labels"]], [63, 38])
    check("final_label_counts", summary["final_label_counts"] == {"F": 436, "S": 754, "U": 92}, summary["final_label_counts"], {"F": 436, "S": 754, "U": 92})
    check("table_row_counts", summary["table_row_counts"] == {"table2": 19, "table3": 4, "table6": 5, "table9": 5, "table13": 6}, summary["table_row_counts"], {"table2": 19, "table3": 4, "table6": 5, "table9": 5, "table13": 6})

    reconciliation = read_csv(output_dir / "printed_vs_rebuilt.csv")
    discrepancy_rows = read_csv(output_dir / "discrepancies.csv")
    check("all_cells_reconciled", len(reconciliation) == 263, len(reconciliation), 263)
    check("all_cells_exact", all(row["status"] == "EXACT_MATCH" for row in reconciliation), sum(row["status"] == "EXACT_MATCH" for row in reconciliation), 263)
    check("zero_discrepancies", not discrepancy_rows, len(discrepancy_rows), 0)

    lineage = [json.loads(line) for line in (output_dir / "cell_lineage.jsonl").read_text(encoding="utf-8").splitlines() if line]
    reconciliation_ids = {row["cell_id"] for row in reconciliation}
    lineage_ids = {row["cell_id"] for row in lineage}
    check("lineage_complete", len(lineage) == 263 and lineage_ids == reconciliation_ids, len(lineage), 263)
    check("lineage_unique", len(lineage_ids) == len(lineage), len(lineage_ids), len(lineage))
    check("lineage_hashes_present", all(len(row["input_sha256"]) == 64 for row in lineage), sum(len(row["input_sha256"]) == 64 for row in lineage), 263)

    paper_contract = json.loads((output_dir / "paper_source_contract_validation.json").read_text(encoding="utf-8"))
    check("paper_contract_exact", paper_contract["discrepancies"] == 0, paper_contract["discrepancies"], 0)

    frozen = json.loads((output_dir / "frozen_input_manifest.json").read_text(encoding="utf-8"))
    source_mismatches: list[str] = []
    for item in frozen["inputs"]:
        if item["kind"] == "git_blob":
            actual = sha256_bytes(git_bytes(repo_root, item["commit"], item["path"]))
        else:
            actual = sha256_file(repo_root / item["path"])
        if actual != item["sha256"]:
            source_mismatches.append(item["input_id"])
    check("frozen_input_hashes", not source_mismatches, source_mismatches, [])

    with tempfile.TemporaryDirectory(prefix="step2-isolated-") as temporary:
        isolated = Path(temporary)
        build(repo_root, isolated, output_dir / "specs")
        mismatches = [
            filename
            for filename in GENERATED_FILES
            if sha256_file(output_dir / filename) != sha256_file(isolated / filename)
        ]
    check("isolated_rerun_byte_identity", not mismatches, mismatches, [])

    passed = all(item["status"] == "PASS" for item in checks)
    report = {
        "schema_version": "step2_verification_report/v1",
        "scope": "submitted_as_printed_dual_commit_reconstruction",
        "status": "PASS" if passed else "FAIL",
        "checks": checks,
        "passed_checks": sum(item["status"] == "PASS" for item in checks),
        "failed_checks": sum(item["status"] == "FAIL" for item in checks),
        "five_tables_exact": passed,
        "two_frozen_submission_sources": {
            "artifact_commit": frozen["artifact_commit"],
            "paper_source_commit": frozen["paper_source_companion_commit"],
        },
        "author_signoff_required_for_g2": True,
        "qualification": "Exact printed-value reconstruction uses the locked artifact submission plus the locked paper-source submission.",
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    status = {
        "schema_version": "rebuttal_work_status/v1",
        "step": "Step 2 table reconstruction",
        "status": "technical_complete_pending_author_signoff" if passed else "verification_failed",
        "g2_status": "PENDING_AUTHOR_SIGNOFF" if passed else "FAILED",
        "blocked": not passed,
        "five_tables": [2, 3, 6, 9, 13],
        "exact_cells_including_headers": 263 if passed else summary["exact_match_cells"],
        "documented_discrepancies": 0 if passed else summary["documented_discrepancy_cells"],
        "source_scope": "two_frozen_submission_sources",
        "artifact_commit": frozen["artifact_commit"],
        "paper_source_commit": frozen["paper_source_companion_commit"],
        "acceptance_report": "verification_report.json",
    }
    args.status.write_text(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
