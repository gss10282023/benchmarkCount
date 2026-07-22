#!/usr/bin/env python3
"""Record the zero-call v6-clean prelock as superseded by task-scoped isolation."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).resolve()
WORK_ROOT = SCRIPT.parents[1]
GEN_ROOT = WORK_ROOT / "draft_generation"
OUTPUT = GEN_ROOT / "incidents" / "wave_004_v6_clean_prelock_superseded.json"
ARTIFACTS = {
    "independent_go": GEN_ROOT / "validation" / "wave_004_v6_clean_independent_go.json",
    "prelock": GEN_ROOT
    / "freeze"
    / "androidworld_candidate116_codex_cli_draft_prelock_v6_clean.json",
    "config": GEN_ROOT
    / "config"
    / "androidworld_candidate116_codex_cli_draft_config_v6_clean.json",
    "agents_config": GEN_ROOT
    / "config"
    / "androidworld_candidate116_codex_cli_agents_config_v6_clean.json",
    "snapshot_manifest": GEN_ROOT / "toolchain_snapshot" / "v6_clean" / "snapshot_manifest.json",
    "readonly_before": GEN_ROOT
    / "validation"
    / "pre_generation_wave_004_v6_clean_readonly_snapshot.json",
}
OLD_OUTPUT = GEN_ROOT / "waves" / "wave_004_v6_clean"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def binding(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if path.is_symlink() or not resolved.is_file():
        raise RuntimeError(f"regular non-symlink file required: {path}")
    return {
        "path": str(resolved),
        "sha256": sha256_file(resolved),
        "size_bytes": resolved.stat().st_size,
    }


def main() -> int:
    if OUTPUT.exists() or OUTPUT.is_symlink():
        raise RuntimeError("supersession incident already exists")
    if OLD_OUTPUT.is_symlink() or not OLD_OUTPUT.is_dir():
        raise RuntimeError("expected revoked v6-clean namespace directory")
    children = list(OLD_OUTPUT.iterdir())
    if len(children) != 1 or children[0].name != "REVOKED_DO_NOT_RUN.json":
        raise RuntimeError("v6-clean namespace contains more than the revocation sentinel")
    revocation = json.loads(children[0].read_text(encoding="utf-8"))
    if (
        revocation.get("status") != "REVOKED_BEFORE_FIRST_MODEL_CALL"
        or revocation.get("model_call_count") != 0
        or revocation.get("replacement_namespace") != "wave_004_v6_clean2"
    ):
        raise RuntimeError("v6-clean revocation sentinel is invalid")
    bound = {name: binding(path) for name, path in ARTIFACTS.items()}
    prelock = json.loads(ARTIFACTS["prelock"].read_text(encoding="utf-8"))
    if prelock.get("generation_id") != "wave_004_v6_clean":
        raise RuntimeError("unexpected prelock generation identity")
    record = {
        "schema_version": "androidworld_candidate116_wave004_prelock_supersession/v1",
        "status": "superseded_before_first_model_call",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "superseded_generation_id": "wave_004_v6_clean",
        "replacement_generation_id": "wave_004_v6_clean2",
        "reason": (
            "The full canonical packet token-capacity audit and staged reading-plan "
            "gate were incomplete, and the frozen foreign-process predicate also "
            "classified unrelated checklist-review work as draft generation. The "
            "replacement binds source-addressed staged reads plus exact task-scoped "
            "argv/PGID isolation while preserving peak-six and 116-case coverage."
        ),
        "superseded_artifacts": bound,
        "old_output_root": str(OLD_OUTPUT.resolve()),
        "revocation_sentinel": binding(children[0]),
        "old_output_contains_only_revocation_sentinel": True,
        "model_calls_made_under_superseded_prelock": 0,
        "drafts_created_under_superseded_prelock": 0,
        "canonical_drafts_or_contracts_promoted": 0,
        "reuse_forbidden": True,
    }
    record["incident_sha256"] = canonical_sha256(record)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps({"status": record["status"], "incident_sha256": record["incident_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
