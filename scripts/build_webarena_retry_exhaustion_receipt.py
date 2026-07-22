#!/usr/bin/env python3
"""Bind consumed WebArena retries to the exact next circuit-recovery receipt.

The receipt is intentionally controller-only: it records outcome categories and
hashes of bounded controller receipts, never full VPS artifacts.  The normal
resumable controller uses it to preserve a one-retry policy rather than
silently replaying the same terminal slots during its recovery prelude.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evidence_system.core.hashing import sha256_file, sha256_object  # noqa: E402
from evidence_system.orchestrator.webarena_verified_full import (  # noqa: E402
    RESULT_NAMESPACE,
)
from evidence_system.orchestrator.webarena_verified_run_control import (  # noqa: E402
    DEFAULT_CIRCUIT_RECOVERY_RECEIPT,
    DEFAULT_JOBS_INDEX,
    DEFAULT_SITE_LOCK,
    RETRY_EXHAUSTION_SCHEMA,
    _atomic_write_json,
    _circuit_recovery_gate,
    _write_sidecar,
    load_materialized_full_plan,
    monitor_namespace,
)


SELECTION_SCHEMA = "webarena_verified_targeted_retry_selection/v1"
FIRST_RETRY_SCHEMA = "webarena_verified_parallel_targeted_formal_recovery/v1"
PENDING_RELAUNCH_SCHEMA = "webarena_verified_pending_preserved_relaunch/v1"
EXTRA_RETRY_SCHEMA = "webarena_verified_concurrent_terminal_retry/v1"
DEFAULT_OUTPUT = Path(
    "results/namespaces/webarena_verified_v1_2_3_full_812/"
    "retry_exhaustion_receipt.json"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ssh-key", required=True)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--first-retry-receipt", required=True)
    parser.add_argument("--pending-relaunch-receipt", required=True)
    parser.add_argument(
        "--extra-retry-receipt",
        action="append",
        default=[],
        help="Additional one-retry receipts for failures discovered during normal pending work.",
    )
    parser.add_argument("--jobs-index", default=str(DEFAULT_JOBS_INDEX))
    parser.add_argument("--site-lock", default=str(DEFAULT_SITE_LOCK))
    parser.add_argument(
        "--circuit-recovery-receipt",
        default=str(DEFAULT_CIRCUIT_RECOVERY_RECEIPT),
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser


def _repo_file(path_value: str | Path, *, label: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"{label} is missing or unsafe")
    return path


def _sidecar_valid(path: Path) -> bool:
    sidecar = path.with_suffix(f"{path.suffix}.sha256")
    if not sidecar.is_file() or sidecar.is_symlink():
        return False
    try:
        expected = sidecar.read_text(encoding="ascii").split()[0]
    except OSError:
        return False
    return len(expected) == 64 and expected == sha256_file(path)


def _load_json(path_value: str | Path, *, label: str, schema: str) -> tuple[Path, Mapping[str, Any]]:
    path = _repo_file(path_value, label=label)
    if not _sidecar_valid(path):
        raise RuntimeError(f"{label} sidecar is invalid")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} is invalid JSON") from exc
    if not isinstance(payload, Mapping) or payload.get("schema_version") != schema:
        raise RuntimeError(f"{label} has the wrong schema")
    return path, payload


def _load_selection(path_value: str | Path) -> tuple[Path, Mapping[str, Any]]:
    path = _repo_file(path_value, label="targeted retry selection")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("targeted retry selection is invalid JSON") from exc
    if (
        not isinstance(payload, Mapping)
        or payload.get("schema_version") != SELECTION_SCHEMA
        or not isinstance(payload.get("retry_once"), Mapping)
        or not isinstance(payload.get("record_only"), Mapping)
    ):
        raise RuntimeError("targeted retry selection has the wrong schema")
    return path, payload


def _slot_id(agent_id: str, task_id: int) -> str:
    return f"wv123-task-{task_id:03d}-agent-{agent_id[-1].lower()}"


def _validated_rows(receipt: Mapping[str, Any], *, label: str) -> dict[str, Mapping[str, Any]]:
    rows = receipt.get("results")
    if not isinstance(rows, list):
        raise RuntimeError(f"{label} lacks result rows")
    by_slot: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if (
            not isinstance(row, Mapping)
            or not isinstance(row.get("agent_id"), str)
            or not isinstance(row.get("task_id"), int)
            or row.get("record_slot_id") != _slot_id(str(row["agent_id"]), int(row["task_id"]))
        ):
            raise RuntimeError(f"{label} contains an invalid result row")
        slot_id = str(row["record_slot_id"])
        if slot_id in by_slot:
            raise RuntimeError(f"{label} contains duplicate result rows")
        by_slot[slot_id] = row
    return by_slot


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    selection_path, selection = _load_selection(args.selection)
    first_path, first = _load_json(
        args.first_retry_receipt,
        label="first targeted retry receipt",
        schema=FIRST_RETRY_SCHEMA,
    )
    pending_path, pending = _load_json(
        args.pending_relaunch_receipt,
        label="pending relaunch receipt",
        schema=PENDING_RELAUNCH_SCHEMA,
    )
    first_rows = _validated_rows(first, label="first targeted retry receipt")
    pending_rows = _validated_rows(pending, label="pending relaunch receipt")
    extra_receipts: list[tuple[Path, Mapping[str, Any], dict[str, Mapping[str, Any]]]] = []
    for position, path_value in enumerate(args.extra_retry_receipt, start=1):
        path, receipt = _load_json(
            path_value,
            label=f"extra terminal retry receipt {position}",
            schema=EXTRA_RETRY_SCHEMA,
        )
        extra_receipts.append(
            (path, receipt, _validated_rows(receipt, label=f"extra terminal retry receipt {position}"))
        )

    plan = load_materialized_full_plan(index_path=args.jobs_index)
    jobs_by_slot = {str(job["record_slot_id"]): dict(job) for job in plan.jobs}
    retry_slots = {
        _slot_id(agent_id, int(task_id))
        for agent_id, task_ids in dict(selection["retry_once"]).items()
        for task_id in task_ids
    }
    credential_slots = {
        _slot_id(agent_id, int(task_id))
        for agent_id, task_ids in dict(selection["record_only"]).items()
        for task_id in task_ids
    }
    if not retry_slots.isdisjoint(credential_slots) or not retry_slots | credential_slots <= set(jobs_by_slot):
        raise RuntimeError("targeted retry selection does not match the formal plan")

    # An entry marked pending/OSError in the first receipt proves no remote
    # worker started.  Every such slot must instead have an actual replacement
    # row in the pending-relaunch receipt before it can be called exhausted.
    actual_attempts: dict[str, dict[str, Any]] = {}
    for slot_id in retry_slots:
        first_row = first_rows.get(slot_id)
        pending_row = pending_rows.get(slot_id)
        if first_row is None:
            raise RuntimeError(f"first retry receipt omits selected slot: {slot_id}")
        first_unstarted = (
            first_row.get("audit_state") == "pending"
            and first_row.get("executor_error_type") == "OSError"
        )
        if first_unstarted:
            if pending_row is None:
                raise RuntimeError(f"unstarted retry has no replacement row: {slot_id}")
            actual_attempts[slot_id] = {
                "source_kind": "pending_preserved_relaunch",
                "receipt_path": str(pending_path.relative_to(ROOT)),
                "receipt_sha256": sha256_file(pending_path),
                "source_status": pending_row.get("status"),
            }
        else:
            if pending_row is not None:
                raise RuntimeError(f"already-started retry has an unexpected replacement row: {slot_id}")
            actual_attempts[slot_id] = {
                "source_kind": "parallel_targeted_retry",
                "receipt_path": str(first_path.relative_to(ROOT)),
                "receipt_sha256": sha256_file(first_path),
                "source_status": first_row.get("status"),
            }
    for path, _receipt, rows in extra_receipts:
        for slot_id, row in rows.items():
            if slot_id in actual_attempts:
                raise RuntimeError(f"duplicate paid retry evidence: {slot_id}")
            if row.get("paid_runtime_replayed") is not True:
                raise RuntimeError(f"extra retry receipt lacks paid replay proof: {slot_id}")
            actual_attempts[slot_id] = {
                "source_kind": "concurrent_terminal_retry",
                "receipt_path": str(path.relative_to(ROOT)),
                "receipt_sha256": sha256_file(path),
                "source_status": row.get("status"),
            }

    snapshot = monitor_namespace(
        mode="full",
        index_path=args.jobs_index,
        site_lock_path=args.site_lock,
        ssh_key_path=args.ssh_key,
        write_outputs=False,
    )
    recovery = _circuit_recovery_gate(
        path_value=args.circuit_recovery_receipt,
        snapshot=snapshot,
        jobs_index_path=args.jobs_index,
    )
    if recovery.get("status") != "pass":
        raise RuntimeError("current circuit recovery receipt is not valid")
    audits_by_slot = {audit.record_slot_id: audit for audit in snapshot.audits}
    issues_by_slot: dict[str, list[str]] = {}
    for issue in snapshot.issues:
        issues_by_slot.setdefault(str(issue["record_slot_id"]), []).append(
            str(issue["issue_id"])
        )

    rows: list[dict[str, Any]] = []
    for slot_id, audit in sorted(audits_by_slot.items()):
        if audit.state != "in_progress":
            continue
        job = jobs_by_slot.get(slot_id)
        if job is None or slot_id not in issues_by_slot:
            raise RuntimeError(f"live terminal slot lacks a formal job or issue: {slot_id}")
        if slot_id in credential_slots:
            disposition = "record_only_credential"
            evidence: Mapping[str, Any] = {
                "source_kind": "credential_record_only_selection",
                "selection_path": str(selection_path.relative_to(ROOT)),
                "selection_sha256": sha256_file(selection_path),
                "issue_ids": sorted(issues_by_slot[slot_id]),
            }
        elif slot_id in actual_attempts:
            evidence = actual_attempts[slot_id]
            if evidence.get("source_status") == "canonical_reusable":
                raise RuntimeError(f"canonical retry is still terminal in live audit: {slot_id}")
            disposition = "retry_exhausted_benchmark"
        else:
            disposition = "record_only_unrecoverable_infra"
            evidence = {
                "source_kind": "live_terminal_issue_ledger",
                "issue_ids": sorted(issues_by_slot[slot_id]),
                "reason": "outside paid retry selection or completed-unsealed reconciliation",
            }
        rows.append(
            {
                "record_slot_id": slot_id,
                "agent_id": str(job["agent_id"]),
                # The frozen full-plan schema stores task IDs as strings.
                # Keep the exact immutable job representation so the resume
                # gate can bind this disposition without type coercion.
                "task_id": str(job["task_id"]),
                "job_sha256": sha256_object(job),
                "disposition": disposition,
                "evidence": dict(evidence),
            }
        )

    if not rows:
        raise RuntimeError("there are no live terminal slots to disposition")
    payload = {
        "schema_version": RETRY_EXHAUSTION_SCHEMA,
        "status": "pass",
        "result_namespace": RESULT_NAMESPACE,
        "jobs_index_sha256": sha256_file(Path(args.jobs_index)),
        "circuit_recovery_id": recovery["recovery_id"],
        "circuit_recovery_receipt_sha256": recovery["sha256"],
        "slots": rows,
        "source_receipts": {
            "first_targeted_retry": {
                "path": str(first_path.relative_to(ROOT)),
                "sha256": sha256_file(first_path),
            },
            "pending_relaunch": {
                "path": str(pending_path.relative_to(ROOT)),
                "sha256": sha256_file(pending_path),
            },
            "extra_terminal_retries": [
                {"path": str(path.relative_to(ROOT)), "sha256": sha256_file(path)}
                for path, _receipt, _rows in extra_receipts
            ],
        },
        "policy": {
            "paid_retry_limit": 1,
            "unstarted_controller_failures_require_replacement_before_exhaustion": True,
            "full_vps_artifacts_synced_to_controller": False,
        },
        "secret_material_recorded": False,
    }
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    _atomic_write_json(output, payload, mode=0o600)
    _write_sidecar(output)
    print(
        json.dumps(
            {
                "status": "pass",
                "output_path": str(output.relative_to(ROOT)),
                "slot_count": len(rows),
                "retry_exhausted_count": sum(
                    row["disposition"] == "retry_exhausted_benchmark" for row in rows
                ),
                "record_only_count": sum(
                    row["disposition"] != "retry_exhausted_benchmark" for row in rows
                ),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
