#!/usr/bin/env python3
"""Resume AgentDojo checklist review while preserving the original review lock.

The full review driver locks generation and review helpers together.  A review-only
resume must not be invalidated when *only* generation helpers (which are not
executed under ``--skip-generation``) have changed.  This wrapper permits exactly
that narrow case, records it, and delegates all review/reuse/lock checks to the
original fail-closed driver.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from neurips_ed_track_minimal.scripts import (
    run_agentdojo_full_draft_review as lifecycle,
)


GENERATION_ONLY_PATHS = {
    "neurips_ed_track_minimal/scripts/run_draft_batch.py",
    "neurips_ed_track_minimal/scripts/draft_case_checklist.py",
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _rows_by_path(config: dict[str, Any]) -> dict[str, dict[str, str]]:
    rows = config.get("lifecycle_code")
    if not isinstance(rows, list):
        raise lifecycle.DraftReviewLifecycleError(
            "resolved review config lifecycle_code is not a list"
        )
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise lifecycle.DraftReviewLifecycleError(
                "resolved review config lifecycle_code row is invalid"
            )
        path = str(row.get("path") or "")
        sha256 = str(row.get("sha256") or "")
        if not path or len(sha256) != 64 or path in result:
            raise lifecycle.DraftReviewLifecycleError(
                "resolved review config lifecycle_code inventory is invalid"
            )
        result[path] = {"path": path, "sha256": sha256}
    return result


def main() -> int:
    args = lifecycle.parse_args()
    if not args.skip_generation or args.force_generation:
        raise lifecycle.DraftReviewLifecycleError(
            "review resume gate requires --skip-generation and forbids --force-generation"
        )
    if not args.run_id:
        raise lifecycle.DraftReviewLifecycleError(
            "review resume gate requires an explicit unique --run-id"
        )
    locked_path = args.resolved_config.resolve()
    locked = lifecycle._load_mapping(locked_path)
    codex_version, _ = lifecycle._codex_preflight()
    current = lifecycle._build_config(args, codex_version)
    locked_rows = _rows_by_path(locked)
    current_rows = _rows_by_path(current)
    if set(locked_rows) != set(current_rows):
        raise lifecycle.DraftReviewLifecycleError(
            "review resume lifecycle-code path inventory drifted"
        )

    normalized = json.loads(json.dumps(current))
    normalized_rows = _rows_by_path(normalized)
    drift: list[dict[str, str]] = []
    for path in sorted(GENERATION_ONLY_PATHS):
        if path not in locked_rows:
            raise lifecycle.DraftReviewLifecycleError(
                f"locked generation-only lifecycle path is missing: {path}"
            )
        if current_rows[path]["sha256"] != locked_rows[path]["sha256"]:
            drift.append(
                {
                    "path": path,
                    "locked_sha256": locked_rows[path]["sha256"],
                    "current_sha256": current_rows[path]["sha256"],
                }
            )
        normalized_rows[path]["sha256"] = locked_rows[path]["sha256"]

    normalized["lifecycle_code"] = [
        normalized_rows[str(row["path"])] for row in normalized["lifecycle_code"]
    ]
    if normalized != locked:
        raise lifecycle.DraftReviewLifecycleError(
            "review resume detected drift outside non-executed generation helpers"
        )

    receipt_path = (
        lifecycle.EXPERIMENT_ROOT
        / "provenance"
        / "draft_review_resume"
        / f"{args.run_id}.json"
    )
    if receipt_path.exists() or receipt_path.is_symlink():
        raise lifecycle.DraftReviewLifecycleError(
            f"review resume receipt already exists: {receipt_path}"
        )
    receipt = {
        "schema_version": "agentdojo_draft_review_resume_gate/v1",
        "run_id": args.run_id,
        "mode": "review_only_skip_generation",
        "locked_review_config_path": lifecycle._display(locked_path),
        "locked_review_config_sha256": _sha256_file(locked_path),
        "current_unadjusted_config_semantic_sha256": _canonical_sha256(current),
        "generation_only_drift": drift,
        "generation_helpers_executed": False,
        "review_semantics_unchanged": True,
        "resume_wrapper": {
            "path": lifecycle._display(Path(__file__).resolve()),
            "sha256": _sha256_file(Path(__file__).resolve()),
        },
    }
    lifecycle._write_json(receipt_path, receipt)

    original_builder = lifecycle._build_config
    lifecycle._build_config = lambda _args, _version: json.loads(json.dumps(locked))
    try:
        return lifecycle.main()
    finally:
        lifecycle._build_config = original_builder


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except lifecycle.DraftReviewLifecycleError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc
