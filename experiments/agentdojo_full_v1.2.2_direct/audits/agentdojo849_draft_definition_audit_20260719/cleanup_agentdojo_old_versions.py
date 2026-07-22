#!/usr/bin/env python3
"""Delete superseded AgentDojo repair versions while retaining final audit evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_AUDIT_NAMES = {
    "local": "agentdojo849_draft_definition_audit_20260719",
    "vps": "audit_draft_definition_20260719",
}
EXPECTED_CASES = 849
EXPECTED_REPAIRS = 460


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("local", "vps"), required=True)
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_bytes(path: Path) -> int:
    if path.is_file() or path.is_symlink():
        return path.lstat().st_size
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def validate_canonical(root: Path) -> None:
    yaml_files = list(root.glob("*/checklist.yaml"))
    json_files = list(root.glob("*/checklist.json"))
    if len(yaml_files) != EXPECTED_CASES or len(json_files) != EXPECTED_CASES:
        raise ValueError(
            f"canonical set mismatch: yaml={len(yaml_files)} json={len(json_files)}"
        )


def remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def main() -> int:
    args = parse_args()
    audit_root = args.audit_root.resolve()
    canonical_root = args.canonical_root.resolve()
    if audit_root.name != EXPECTED_AUDIT_NAMES[args.mode]:
        raise ValueError(f"refusing unexpected audit root: {audit_root}")
    if audit_root == canonical_root or audit_root in canonical_root.parents:
        raise ValueError("canonical root must be outside the audit root")
    validate_canonical(canonical_root)

    final_dir = audit_root / "final"
    acceptance_dir = audit_root / "final_repaired_849_acceptance_v7"
    deterministic_dir = audit_root / "final_promoted_849_deterministic_v7"
    manifest_path = audit_root / "FINAL_PROMOTION_MANIFEST_V7.json"
    if args.mode == "local":
        manifest_path = audit_root / "FINAL_PROMOTION_MANIFEST_V7_VPS.json"
    required = [
        final_dir / "AGENTDOJO_460_DRAFT_REPAIR_REPORT_ZH.md",
        final_dir / "FINAL_REPAIR_SUMMARY_V7.json",
        acceptance_dir / "SEMANTIC_ACCEPTANCE_SUMMARY.json",
        deterministic_dir / "deterministic_summary.json",
        manifest_path,
    ]
    for path in required:
        if not path.is_file():
            raise ValueError(f"required final artifact missing: {path}")
    if json.loads((acceptance_dir / "SEMANTIC_ACCEPTANCE_SUMMARY.json").read_text())["status_counts"] != {"pass": EXPECTED_CASES}:
        raise ValueError("final semantic acceptance is not 849 pass")
    if json.loads((deterministic_dir / "deterministic_summary.json").read_text())["status_counts"] != {"pass": EXPECTED_CASES}:
        raise ValueError("final deterministic validation is not 849 pass")

    keep_top = {
        "final",
        "final_repaired_849_acceptance_v7",
        "final_promoted_849_deterministic_v7",
        manifest_path.name,
    }
    if args.mode == "vps":
        keep_top.add("final_local_sync_v7")
    else:
        keep_top.update(
            {
                "final_repaired_849_hash_verification_v7",
                "LOCAL_PROMOTION_RECEIPT_V7.json",
                "POINTER_NORMALIZATION_MANIFEST_V6.json",
            }
        )
    keep_top.update(path.name for path in audit_root.glob("*.py"))

    receipt_paths: set[Path] = set()
    receipt_roots: set[Path] = set()
    if args.mode == "vps":
        acceptance_path = acceptance_dir / "FINAL_SEMANTIC_ACCEPTANCE_849.jsonl"
        repaired_rows = 0
        for line in acceptance_path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("original_final_status") != "noncompliant":
                continue
            repaired_rows += 1
            evidence = row["acceptance_evidence"]
            receipt = Path(evidence["path"]).resolve()
            if audit_root not in receipt.parents or not receipt.is_file():
                raise ValueError(f"invalid acceptance receipt path: {receipt}")
            if sha256(receipt) != evidence["receipt_sha256"]:
                raise ValueError(f"acceptance receipt hash mismatch: {receipt}")
            receipt_paths.add(receipt)
            receipt_roots.add(next(parent for parent in receipt.parents if parent.parent == audit_root))
        if repaired_rows != EXPECTED_REPAIRS or len(receipt_paths) != EXPECTED_REPAIRS:
            raise ValueError(
                f"expected {EXPECTED_REPAIRS} unique repaired receipts, found {len(receipt_paths)}"
            )
        keep_top.update(path.name for path in receipt_roots)

    delete_targets = [
        path
        for path in sorted(audit_root.iterdir(), key=lambda item: item.name)
        if path.name not in keep_top
    ]
    receipt_prune_files: list[Path] = []
    for root in receipt_roots:
        receipt_prune_files.extend(
            path for path in root.rglob("*") if path.is_file() and path.resolve() not in receipt_paths
        )

    cleanup_manifest_path = final_dir / f"OLD_VERSION_CLEANUP_MANIFEST_{args.mode.upper()}.json"
    cleanup = {
        "schema_version": "agentdojo849_old_version_cleanup/v1",
        "mode": args.mode,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "validated_before_delete",
        "canonical_root": str(canonical_root),
        "canonical_case_count": EXPECTED_CASES,
        "deleted_top_level_targets": [
            {"name": path.name, "bytes": tree_bytes(path)} for path in delete_targets
        ],
        "deleted_receipt_sibling_files": len(receipt_prune_files),
        "preserved_hash_bound_receipts": len(receipt_paths),
        "bytes_scheduled": sum(tree_bytes(path) for path in delete_targets)
        + sum(path.stat().st_size for path in receipt_prune_files),
        "recoverable": False,
    }
    if args.dry_run:
        print(json.dumps(cleanup, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    write_json(cleanup_manifest_path, cleanup)

    for path in receipt_prune_files:
        path.unlink()
    for root in receipt_roots:
        for directory in sorted(
            (path for path in root.rglob("*") if path.is_dir()),
            key=lambda item: len(item.parts),
            reverse=True,
        ):
            try:
                directory.rmdir()
            except OSError:
                pass
    for path in delete_targets:
        remove_path(path)

    validate_canonical(canonical_root)
    for receipt in receipt_paths:
        if not receipt.is_file():
            raise ValueError(f"preserved receipt missing after cleanup: {receipt}")
    for path in required:
        if not path.is_file():
            raise ValueError(f"required final artifact lost during cleanup: {path}")

    cleanup["status"] = "complete"
    cleanup["completed_at"] = datetime.now(timezone.utc).isoformat()
    cleanup["deleted_top_level_count"] = len(delete_targets)
    write_json(cleanup_manifest_path, cleanup)
    print(
        json.dumps(
            {
                "mode": args.mode,
                "status": "complete",
                "deleted_top_level_count": len(delete_targets),
                "bytes_deleted": cleanup["bytes_scheduled"],
                "preserved_hash_bound_receipts": len(receipt_paths),
                "cleanup_manifest": str(cleanup_manifest_path),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
