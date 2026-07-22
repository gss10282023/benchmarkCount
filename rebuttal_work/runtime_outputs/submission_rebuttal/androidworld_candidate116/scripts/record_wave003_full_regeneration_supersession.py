#!/usr/bin/env python3
"""Bind and supersede the old 116-draft wave before user-authorized deletion."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).resolve()
WORK_ROOT = SCRIPT.parents[1]
REPO_ROOT = WORK_ROOT.parents[3]
GEN_ROOT = WORK_ROOT / "draft_generation"
WAVE_ROOT = GEN_ROOT / "waves" / "wave_003"
PRELOCK = GEN_ROOT / "freeze" / "androidworld_candidate116_codex_cli_draft_prelock_v3.json"
CONFIG = GEN_ROOT / "config" / "androidworld_candidate116_codex_cli_draft_config_v3.json"
OUTPUT = GEN_ROOT / "incidents" / "wave_003_superseded_full_regeneration.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def repo_path(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def binding(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"required regular file is missing: {path}")
    return {
        "path": repo_path(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON object required: {path}")
    return value


def verify_self_hash(value: dict[str, Any], field: str, label: str) -> None:
    claimed = value.get(field)
    core = dict(value)
    core.pop(field, None)
    if claimed != canonical_sha256(core):
        raise RuntimeError(f"{label} self-hash mismatch")


def main() -> int:
    if OUTPUT.exists():
        raise RuntimeError(f"supersession incident already exists: {OUTPUT}")
    if WAVE_ROOT.is_symlink() or not WAVE_ROOT.is_dir():
        raise RuntimeError("wave_003 root is missing or is a symlink")

    prelock = load_json(PRELOCK)
    config = load_json(CONFIG)
    verify_self_hash(prelock, "prelock_sha256", "wave_003 prelock")
    verify_self_hash(config, "config_sha256", "wave_003 config")
    if (
        prelock.get("generation_id") != "wave_003"
        or prelock.get("case_count") != 116
        or config.get("generation_id") != "wave_003"
        or config.get("max_parallel") != 6
    ):
        raise RuntimeError("wave_003 prelock/config identity is invalid")

    case_dirs = sorted(
        path for path in WAVE_ROOT.iterdir() if path.is_dir() and not path.name.startswith(".")
    )
    checklist_paths = [path / "checklist.yaml" for path in case_dirs]
    if len(case_dirs) != 116 or any(not path.is_file() for path in checklist_paths):
        raise RuntimeError("wave_003 is not exactly 116 case directories/checklists")

    summary_path = WAVE_ROOT / "_batch_summary.json"
    summary = load_json(summary_path)
    if (
        summary.get("total_cases") != 116
        or summary.get("completed_cases") != 116
        or summary.get("success_cases") != 116
        or summary.get("failed_cases") != 0
        or summary.get("skipped_cases") != 0
    ):
        raise RuntimeError("wave_003 batch summary is not a complete 116/116 success record")

    files = []
    for path in sorted(candidate for candidate in WAVE_ROOT.rglob("*") if candidate.is_file()):
        if path.is_symlink():
            raise RuntimeError(f"symlink in wave_003: {path}")
        files.append(binding(path))

    evidence_paths = [
        GEN_ROOT / "automatic_qc_v3" / "summary.json",
        GEN_ROOT / "integrity_audits" / "wave_003_generation_integrity.json",
        GEN_ROOT / "manual_audits" / "wave_003_batch_a.json",
        GEN_ROOT / "manual_audits" / "wave_003_batch_b.json",
        GEN_ROOT / "manual_audits" / "wave_003_batch_c1.json",
        GEN_ROOT / "manual_audits" / "wave_003_batch_c2.json",
    ]
    payload = {
        "schema_version": "androidworld_candidate116_draft_wave_supersession/v1",
        "status": "superseded_user_requested_full_regeneration",
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_generation_id": "wave_003",
        "replacement_generation_id": "wave_004",
        "reason": (
            "The user explicitly required deletion of all 116 old raw drafts and a fresh "
            "116-case Codex CLI generation; no old draft may be retained or promoted."
        ),
        "promotion_forbidden": True,
        "old_draft_reuse_forbidden": True,
        "old_prelock": binding(PRELOCK)
        | {"prelock_sha256": prelock["prelock_sha256"]},
        "old_config": binding(CONFIG) | {"config_sha256": config["config_sha256"]},
        "old_wave_root": repo_path(WAVE_ROOT),
        "old_wave_file_count": len(files),
        "old_wave_files": files,
        "old_wave_files_sha256": canonical_sha256(files),
        "old_case_count": len(case_dirs),
        "old_case_order": [path.name for path in case_dirs],
        "old_case_order_sha256": canonical_sha256([path.name for path in case_dirs]),
        "old_batch_summary": binding(summary_path),
        "old_batch_results": binding(WAVE_ROOT / "_batch_results.jsonl"),
        "old_review_evidence": [binding(path) for path in evidence_paths],
        "deletion_authorization_scope": {
            "authorized_by": "user",
            "exact_root": repo_path(WAVE_ROOT),
            "delete_only_old_wave_root": True,
            "preserve_old_prelock_config_and_review_evidence": True,
            "preserve_packets_results_official100_and_paper_baseline": True,
        },
        "replacement_requirements": {
            "new_prelock_required": True,
            "new_config_required": True,
            "new_toolchain_snapshot_required": True,
            "all_116_model_calls_required": True,
            "exact_concurrency": 6,
            "freeze_requires_116_of_116_acceptance": True,
        },
    }
    payload["incident_sha256"] = canonical_sha256(payload)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    print(
        json.dumps(
            {
                "status": "recorded",
                "incident": binding(OUTPUT),
                "incident_sha256": payload["incident_sha256"],
                "old_wave_file_count": len(files),
                "old_case_count": len(case_dirs),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
