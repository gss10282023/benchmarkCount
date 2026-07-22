#!/usr/bin/env python3
"""Merge the two clean AndroidWorld V2 draft jobs without overwriting a case."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path


def read_ids(path: Path) -> list[str]:
    values = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if values != sorted(set(values)):
        raise ValueError(f"case ids must be unique and sorted: {path}")
    return values


def case_dirs(root: Path) -> set[str]:
    return {path.name for path in root.iterdir() if path.is_dir() and not path.name.startswith("_")}


def load_rows(root: Path) -> list[dict]:
    rows = []
    for line in (root / "_batch_results.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all-case-ids", type=Path, required=True)
    parser.add_argument("--source", nargs=3, action="append", metavar=("LABEL", "CASE_IDS", "RESULT_ROOT"), required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--provenance-destination", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    expected = read_ids(args.all_case_ids)
    expected_set = set(expected)
    if args.destination.exists() or args.provenance_destination.exists():
        raise FileExistsError("destination already exists; refusing to overwrite")

    sources: list[tuple[str, list[str], Path, dict, list[dict]]] = []
    accumulated: set[str] = set()
    for label, ids_arg, root_arg in args.source:
        ids_path = Path(ids_arg)
        root = Path(root_arg)
        ids = read_ids(ids_path)
        ids_set = set(ids)
        observed = case_dirs(root)
        if observed != ids_set:
            raise ValueError(f"{label}: result case set mismatch: missing={sorted(ids_set-observed)!r}, extra={sorted(observed-ids_set)!r}")
        overlap = accumulated & ids_set
        if overlap:
            raise ValueError(f"{label}: duplicate cases across clean jobs: {sorted(overlap)!r}")
        accumulated |= ids_set
        summary = json.loads((root / "_batch_summary.json").read_text(encoding="utf-8"))
        rows = load_rows(root)
        row_ids = {str(row.get("case_unit_dir")) for row in rows}
        if row_ids != ids_set or any(row.get("status") != "success" for row in rows):
            raise ValueError(f"{label}: batch rows are not an exact all-success case set")
        if summary.get("success_cases") != len(ids) or summary.get("failed_cases") != 0:
            raise ValueError(f"{label}: source batch summary is not clean: {summary!r}")
        sources.append((label, ids, root, summary, rows))

    if accumulated != expected_set:
        raise ValueError(f"combined case set mismatch: missing={sorted(expected_set-accumulated)!r}, extra={sorted(accumulated-expected_set)!r}")

    args.destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{args.destination.name}.", dir=args.destination.parent))
    provenance_temporary = Path(tempfile.mkdtemp(prefix=f".{args.provenance_destination.name}.", dir=args.provenance_destination.parent))
    try:
        combined_rows: list[dict] = []
        summaries: dict[str, dict] = {}
        for label, ids, root, summary, rows in sources:
            for case_id in ids:
                shutil.copytree(root / case_id, temporary / case_id, copy_function=shutil.copy2)
            for row in rows:
                enriched = dict(row)
                enriched["source_clean_job"] = label
                combined_rows.append(enriched)
            summaries[label] = summary

            provenance_root = provenance_temporary / label
            provenance_root.mkdir(parents=True)
            for name in ("_batch_results.jsonl", "_batch_summary.json"):
                shutil.copy2(root / name, provenance_root / name)

        combined_rows.sort(key=lambda row: str(row["case_unit_dir"]))
        (temporary / "_batch_results.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in combined_rows),
            encoding="utf-8",
        )
        combined_summary = {
            "schema_version": "androidworld_clean_v2_combined_batch/v1",
            "total_cases": len(expected),
            "completed_cases": len(expected),
            "success_cases": len(expected),
            "skipped_cases": 0,
            "failed_cases": 0,
            "not_run_case_count": 0,
            "not_run_case_ids": [],
            "warning_count": sum(int(summary.get("warning_count", 0)) for summary in summaries.values()),
            "provider": "codex",
            "model": "gpt-5.4",
            "reasoning_effort": "high",
            "codex_sandbox": "read-only",
            "max_parallel_per_source_job": 11,
            "source_jobs": list(summaries),
            "source_summaries": summaries,
            "output_root": str(args.destination.resolve()),
        }
        (temporary / "_batch_summary.json").write_text(
            json.dumps(combined_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (provenance_temporary / "MERGE_RECEIPT.json").write_text(
            json.dumps(
                {
                    "schema_version": "androidworld_clean_v2_merge_receipt/v1",
                    "case_count": len(expected),
                    "case_ids": expected,
                    "sources": {label: str(root.resolve()) for label, _, root, _, _ in sources},
                    "destination": str(args.destination.resolve()),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary.rename(args.destination)
        provenance_temporary.rename(args.provenance_destination)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        shutil.rmtree(provenance_temporary, ignore_errors=True)
        raise

    print(json.dumps({"case_count": len(expected), "destination": str(args.destination)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
