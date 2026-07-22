#!/usr/bin/env python3
"""Rebuild the submitted master table from one explicit manifest.

This script intentionally performs no directory discovery.  Every included
record must already be named in the manifest passed with --manifest.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from formatting import format_identification_interval, format_ratio


BENCHMARK_ORDER = {
    "agentdojo": 0,
    "androidworld": 1,
    "appworld": 2,
    "miniwob": 3,
    "tau3_retail": 4,
}
AGENT_ORDER = {"agent_a": 0, "agent_b": 1, "agent_c": 2}
REQUIRED_COLUMNS = {
    "record_key",
    "raw_record_id",
    "raw_record_slot_id",
    "raw_run_id",
    "benchmark",
    "case_unit_id",
    "agent_id",
    "evidence_label_raw",
    "stronger_label_raw",
    "released_label",
    "table2_denominator",
    "submission_status",
    "raw_run_path",
    "raw_run_sha256",
    "native_evaluator_path",
    "native_evaluator_sha256",
    "score_path",
    "score_sha256",
    "score_manifest_path",
    "score_manifest_sha256",
    "checklist_path",
    "checklist_sha256",
    "artifact_manifest_path",
    "artifact_manifest_sha256",
}
PATH_COLUMNS = {
    "raw_run_path",
    "native_evaluator_path",
    "score_path",
    "score_manifest_path",
    "checklist_path",
    "artifact_manifest_path",
}


def read_manifest(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - set(fieldnames)
        if missing:
            raise ValueError(f"manifest missing required columns: {sorted(missing)}")
        rows = list(reader)
    keys = [row["record_key"] for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("manifest contains duplicate record_key values")
    for row in rows:
        benchmark = row["benchmark"]
        agent_id = row["agent_id"]
        expected_key = f"{benchmark}::{row['case_unit_id']}::{agent_id}"
        if benchmark not in BENCHMARK_ORDER or agent_id not in AGENT_ORDER:
            raise ValueError(f"invalid benchmark/agent in {row['record_key']}")
        if row["record_key"] != expected_key:
            raise ValueError(f"record_key does not match benchmark/case/agent: {row['record_key']}")
        if row["submission_status"] != "submitted":
            raise ValueError(f"non-submitted row in baseline: {row['record_key']}")
        if row["table2_denominator"] != "true":
            raise ValueError(f"baseline row excluded from Table 2: {row['record_key']}")
        if row["evidence_label_raw"] not in {"S", "F", "U"}:
            raise ValueError(f"invalid evidence label in {row['record_key']}")
        if row["stronger_label_raw"] not in {"S", "F", "U", "NA"}:
            raise ValueError(f"invalid stronger label in {row['record_key']}")
        if row["released_label"] not in {"success", "fail"}:
            raise ValueError(f"invalid released label in {row['record_key']}")
        for column in PATH_COLUMNS:
            value = row[column].replace("\\", "/")
            if value.startswith("/") or ".." in value.split("/"):
                raise ValueError(f"unsafe path in {column}: {value}")
            if not value.startswith("paper_result_packages/"):
                raise ValueError(f"non-submission artifact path in {column}: {value}")
    return fieldnames, rows


def row_sort_key(row: dict[str, str]) -> tuple[int, str, int, str]:
    return (
        BENCHMARK_ORDER[row["benchmark"]],
        row["case_unit_id"],
        AGENT_ORDER[row["agent_id"]],
        row["record_key"],
    )


def write_master(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(rows, key=row_sort_key))


def write_summary(path: Path, rows: list[dict[str, str]]) -> None:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["benchmark"], row["agent_id"])].append(row)

    fieldnames = [
        "benchmark",
        "agent_id",
        "n",
        "evidence_s",
        "evidence_f",
        "evidence_u",
        "evidence_s_percent",
        "evidence_f_percent",
        "evidence_u_percent",
        "identification_interval",
        "released_success",
        "released_fail",
    ]
    output: list[dict[str, str | int]] = []
    for benchmark, agent_id in sorted(
        grouped,
        key=lambda item: (BENCHMARK_ORDER[item[0]], AGENT_ORDER[item[1]]),
    ):
        group = grouped[(benchmark, agent_id)]
        n = len(group)
        counts = {label: sum(row["evidence_label_raw"] == label for row in group) for label in "SFU"}
        output.append(
            {
                "benchmark": benchmark,
                "agent_id": agent_id,
                "n": n,
                "evidence_s": counts["S"],
                "evidence_f": counts["F"],
                "evidence_u": counts["U"],
                "evidence_s_percent": format_ratio(counts["S"], n),
                "evidence_f_percent": format_ratio(counts["F"], n),
                "evidence_u_percent": format_ratio(counts["U"], n),
                "identification_interval": format_identification_interval(counts["S"], counts["U"], n),
                "released_success": sum(row["released_label"].lower() == "success" for row in group),
                "released_fail": sum(row["released_label"].lower() == "fail" for row in group),
            }
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)


def rebuild(manifest: Path, master_out: Path, summary_out: Path, expected_rows: int) -> None:
    fieldnames, rows = read_manifest(manifest)
    if len(rows) != expected_rows:
        raise ValueError(f"expected {expected_rows} manifest rows, found {len(rows)}")
    write_master(master_out, fieldnames, rows)
    write_summary(summary_out, rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--master-out", type=Path, required=True)
    parser.add_argument("--summary-out", type=Path, required=True)
    parser.add_argument("--expected-rows", type=int, default=1282)
    args = parser.parse_args()
    rebuild(args.manifest, args.master_out, args.summary_out, args.expected_rows)


if __name__ == "__main__":
    main()
