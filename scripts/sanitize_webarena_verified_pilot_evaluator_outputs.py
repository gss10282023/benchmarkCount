#!/usr/bin/env python3
"""Redact controller-only evaluator credentials and reseal pilot metadata."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evidence_system.adapters.runtime import job_result_relative_dir  # noqa: E402
from evidence_system.adapters.webarena_har_sanitization import (  # noqa: E402
    sanitize_structured_credential_values,
)
from evidence_system.contracts.common import write_json  # noqa: E402
from evidence_system.core.hashing import (  # noqa: E402
    sha256_file,
    sha256_object,
)
from evidence_system.core.paths import resolve_repo_path  # noqa: E402
from evidence_system.orchestrator.webarena_verified_full import (  # noqa: E402
    DEFAULT_SITE_LOCK,
)
from evidence_system.orchestrator.webarena_verified_pilot_execution import (  # noqa: E402
    build_pilot_schedule,
)
from evidence_system.orchestrator.webarena_verified_run_control import (  # noqa: E402
    audit_slot,
    load_materialized_full_plan,
)
from evidence_system.webarena_sites import load_site_lock  # noqa: E402


OUTPUT_PATH = Path(
    "experiments/step20/webarena_verified/"
    "pilot_evaluator_output_sanitization.json"
)


def _load_object(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return loaded


def _reseal_slot(job: Mapping[str, Any]) -> dict[str, Any] | None:
    root = resolve_repo_path(job_result_relative_dir(dict(job)) / "adapter")
    task_id = int(job["task_id"])
    eval_result_path = root / "native_run" / str(task_id) / "eval_result.json"
    payload = _load_object(eval_result_path)
    redacted_count = sanitize_structured_credential_values(payload)
    if not redacted_count:
        return None
    write_json(eval_result_path, payload)
    sanitized_eval_sha256 = sha256_file(eval_result_path)
    redaction = {
        "status": "pass",
        "redacted_value_count": redacted_count,
        "original_sensitive_values_retained": False,
        "original_sensitive_value_hashes_retained": False,
    }

    eval_summary_path = eval_result_path.with_name("eval_summary.json")
    eval_summary = _load_object(eval_summary_path)
    eval_summary["official_eval_result_sha256"] = sanitized_eval_sha256
    eval_summary["controller_output_credential_redaction"] = redaction
    write_json(eval_summary_path, eval_summary)

    native_output_path = root / "native_run" / "native_evaluator_output.json"
    native_output = _load_object(native_output_path)
    native_output["official_eval_result_sha256"] = sanitized_eval_sha256
    native_output["controller_output_credential_redaction"] = redaction
    write_json(native_output_path, native_output)

    manifest_path = root / "artifact_manifest.json"
    manifest = _load_object(manifest_path)
    entries = manifest.get("artifacts")
    if not isinstance(entries, list):
        raise RuntimeError(f"artifact list missing: {manifest_path}")
    target_redaction_statuses = {
        eval_result_path.resolve(): "redacted",
        eval_summary_path.resolve(): "not_needed",
        native_output_path.resolve(): "not_needed",
    }
    matched: set[Path] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        declared = entry.get("path")
        if not isinstance(declared, str):
            continue
        artifact_path = resolve_repo_path(declared).resolve()
        if artifact_path not in target_redaction_statuses:
            continue
        artifact_payload = _load_object(artifact_path)
        entry["sha256"] = sha256_file(artifact_path)
        entry["size_bytes"] = artifact_path.stat().st_size
        entry["verified_evaluator_output_object_hash"] = sha256_object(
            artifact_payload
        )
        entry["redaction_status"] = target_redaction_statuses[artifact_path]
        matched.add(artifact_path)
    if matched != set(target_redaction_statuses):
        raise RuntimeError(
            "expected evaluator result, summary, and native-output artifact "
            f"entries for {job['record_slot_id']}"
        )
    write_json(manifest_path, manifest)

    raw_path = root / "raw_run.json"
    raw = _load_object(raw_path)
    raw["artifact_manifest_sha256"] = sha256_file(manifest_path)
    write_json(raw_path, raw)
    return {
        "record_slot_id": str(job["record_slot_id"]),
        "task_id": task_id,
        "agent_id": str(job["agent_id"]),
        "redacted_value_count": redacted_count,
        "sanitized_eval_result_path": str(eval_result_path.relative_to(ROOT)),
        "sanitized_eval_result_sha256": sanitized_eval_sha256,
        "artifact_manifest_sha256": sha256_file(manifest_path),
    }


def main() -> int:
    pilot = build_pilot_schedule(load_materialized_full_plan())
    site_lock = load_site_lock(resolve_repo_path(DEFAULT_SITE_LOCK))
    rows = [row for job in pilot.jobs if (row := _reseal_slot(job)) is not None]
    audits = [audit_slot(job, site_lock=site_lock) for job in pilot.jobs]
    states = Counter(audit.state for audit in audits)
    if states != {"canonical_reusable": 24}:
        raise RuntimeError(f"post-sanitization pilot audit failed: {dict(states)}")
    receipt = {
        "schema_version": "webarena_verified_pilot_evaluator_output_sanitization/v1",
        "status": "pass",
        "sanitization_scope": "controller_only_official_evaluator_json",
        "sanitized_slot_count": len(rows),
        "redacted_value_count": sum(row["redacted_value_count"] for row in rows),
        "slots": rows,
        "post_sanitization_canonical_reusable_count": 24,
        "original_sensitive_values_retained": False,
        "original_sensitive_value_hashes_retained": False,
        "secret_material_recorded": False,
    }
    output = write_json(OUTPUT_PATH, receipt)
    output.with_suffix(f"{output.suffix}.sha256").write_text(
        f"{sha256_file(output)}  {output.name}\n",
        encoding="ascii",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
