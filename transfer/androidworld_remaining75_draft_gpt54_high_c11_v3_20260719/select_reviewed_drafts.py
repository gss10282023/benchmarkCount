#!/usr/bin/env python3
"""Materialize the reviewed per-case V2/V3/V4 draft selection without edits."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_rows(root: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for line in (root / "_batch_results.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        case_id = str(row.get("case_unit_dir"))
        if case_id in rows:
            raise ValueError(f"duplicate batch row for {case_id} in {root}")
        rows[case_id] = row
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--case-ids", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    case_ids = [line.strip() for line in args.case_ids.read_text(encoding="utf-8").splitlines() if line.strip()]
    if case_ids != sorted(set(case_ids)):
        raise ValueError("case ids must be unique and sorted")
    selection = json.loads(args.selection.read_text(encoding="utf-8"))
    if selection.get("case_count") != len(case_ids):
        raise ValueError("selection case_count mismatch")
    if args.destination.exists() or args.receipt.exists():
        raise FileExistsError("destination or receipt already exists; refusing to overwrite")

    source_roots = {
        label: args.workspace_root / relative
        for label, relative in selection["sources"].items()
    }
    source_rows = {label: read_rows(root) for label, root in source_roots.items()}
    default = selection["default_source"]
    overrides = selection.get("overrides") or {}
    chosen = {case_id: (overrides.get(case_id) or {}).get("source", default) for case_id in case_ids}
    observed_counts = Counter(chosen.values())
    if dict(observed_counts) != selection["source_selection_counts"]:
        raise ValueError(f"source selection counts mismatch: {dict(observed_counts)!r}")

    args.destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{args.destination.name}.", dir=args.destination.parent))
    combined_rows: list[dict] = []
    receipt_cases: list[dict] = []
    try:
        for case_id in case_ids:
            label = chosen[case_id]
            root = source_roots[label]
            source_dir = root / case_id
            row = source_rows[label].get(case_id)
            if not source_dir.is_dir() or not row or row.get("status") != "success":
                raise ValueError(f"selected source is not a successful generated case: {case_id} from {label}")
            shutil.copytree(source_dir, temporary / case_id, copy_function=shutil.copy2)
            copied_hash = sha256(temporary / case_id / "checklist.yaml")
            source_hash = sha256(source_dir / "checklist.yaml")
            if copied_hash != source_hash:
                raise ValueError(f"copy hash mismatch: {case_id}")
            enriched = dict(row)
            enriched["reviewed_selected_source"] = label
            combined_rows.append(enriched)
            receipt_cases.append(
                {
                    "case_id": case_id,
                    "source": label,
                    "reason": (overrides.get(case_id) or {}).get("reason", "V3 passed manual semantic review."),
                    "checklist_sha256": source_hash,
                    "llm_call_sha256": sha256(source_dir / "llm_call.json"),
                }
            )

        combined_rows.sort(key=lambda row: str(row["case_unit_dir"]))
        (temporary / "_batch_results.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in combined_rows),
            encoding="utf-8",
        )
        (temporary / "_batch_summary.json").write_text(
            json.dumps(
                {
                    "schema_version": "androidworld_reviewed_draft_selection_batch/v1",
                    "total_cases": len(case_ids),
                    "completed_cases": len(case_ids),
                    "success_cases": len(case_ids),
                    "skipped_cases": 0,
                    "failed_cases": 0,
                    "not_run_case_count": 0,
                    "not_run_case_ids": [],
                    "warning_count": 0,
                    "provider": "codex",
                    "model": "gpt-5.4",
                    "reasoning_effort": "high",
                    "codex_sandbox": "read-only",
                    "max_parallel_per_source_job": 11,
                    "selection_counts": dict(observed_counts),
                    "output_root": str(args.destination.resolve()),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary.rename(args.destination)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    args.receipt.write_text(
        json.dumps(
            {
                "schema_version": "androidworld_reviewed_draft_selection_receipt/v1",
                "case_count": len(case_ids),
                "selection_sha256": sha256(args.selection),
                "source_selection_counts": dict(observed_counts),
                "manual_checklist_editing": False,
                "cases": receipt_cases,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"case_count": len(case_ids), "source_selection_counts": dict(observed_counts)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
