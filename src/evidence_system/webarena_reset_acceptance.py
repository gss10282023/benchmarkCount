"""Fail-closed aggregation for the three-host real WebArena reset smoke."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from evidence_system.webarena_sites import (
    RESET_RECEIPT_SCHEMA,
    atomic_write_json,
    load_site_lock,
    pinned_image_reference,
)


RESET_SMOKE_ACCEPTANCE_SCHEMA = "webarena_verified_real_reset_smoke_acceptance/v1"
DEFAULT_TASK_SITES = {
    0: "shopping_admin",
    21: "shopping",
    389: "gitlab",
    399: "reddit",
}
EXPECTED_SENTINELS = {
    "shopping": ["env_ctrl_status", "homepage"],
    "shopping_admin": ["env_ctrl_status", "homepage", "shopping_admin_reviews"],
    "reddit": ["env_ctrl_status", "homepage"],
    "gitlab": ["env_ctrl_status", "homepage"],
}


def build_reset_smoke_acceptance(
    *,
    receipts_root: str | Path,
    site_lock_path: str | Path,
    infra_config_path: str | Path,
    task_sites: Mapping[int, str] = DEFAULT_TASK_SITES,
) -> dict[str, Any]:
    root = Path(receipts_root)
    site_lock = load_site_lock(site_lock_path)
    infra = json.loads(Path(infra_config_path).read_text(encoding="utf-8"))
    expected_machines = _expected_machines(infra)
    expected_lock_hash = _sha256_json(site_lock)
    expected_relative_paths = {
        f"{machine_id}/{task_id}/reset_receipt.json"
        for machine_id in expected_machines
        for task_id in task_sites
    }
    observed_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob("reset_receipt.json")
        if path.is_file()
    } if root.is_dir() else set()
    expected_slots = [
        _expected_slot_identity(
            machine_id=machine_id,
            agent_id=machine["agent_id"],
            task_id=int(task_id),
            site=str(site),
        )
        for machine_id, machine in expected_machines.items()
        for task_id, site in task_sites.items()
    ]

    blockers: list[str] = []
    missing = sorted(expected_relative_paths - observed_paths)
    extras = sorted(observed_paths - expected_relative_paths)
    if missing:
        blockers.append(f"missing reset receipts: {', '.join(missing)}")
    if extras:
        blockers.append(f"unexpected reset receipts: {', '.join(extras)}")

    entries: list[dict[str, Any]] = []
    receipt_completion_times: list[str] = []
    cross_host: dict[int, list[dict[str, Any]]] = {int(task_id): [] for task_id in task_sites}
    invalid_receipts = 0
    for machine_id, machine in expected_machines.items():
        for task_id, site in task_sites.items():
            relative = f"{machine_id}/{int(task_id)}/reset_receipt.json"
            path = root / relative
            if not path.is_file():
                continue
            try:
                receipt = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                blockers.append(f"invalid JSON {relative}: {exc}")
                invalid_receipts += 1
                continue
            reasons = _validate_receipt(
                receipt,
                machine=machine,
                task_id=int(task_id),
                site=str(site),
                expected_lock_hash=expected_lock_hash,
                site_lock=site_lock,
            )
            if reasons:
                invalid_receipts += 1
                blockers.extend(f"{relative}: {reason}" for reason in reasons)
            completed_at = receipt.get("completed_at")
            if isinstance(completed_at, str) and completed_at:
                receipt_completion_times.append(completed_at)
            row = receipt.get("sites", [{}])[0] if isinstance(receipt.get("sites"), list) else {}
            after = row.get("after") if isinstance(row, Mapping) else {}
            before = row.get("before") if isinstance(row, Mapping) else None
            sentinels = row.get("sentinels") if isinstance(row, Mapping) else []
            signature = {
                "site": site,
                "image_reference": row.get("image_reference") if isinstance(row, Mapping) else None,
                "expected_image_id": row.get("expected_image_id") if isinstance(row, Mapping) else None,
                "sentinels": sentinels,
            }
            cross_host[int(task_id)].append(
                {
                    "machine_id": machine_id,
                    "signature_sha256": _sha256_json(signature),
                    "container_id": after.get("container_id") if isinstance(after, Mapping) else None,
                }
            )
            entries.append(
                {
                    "machine_id": machine_id,
                    "agent_id": machine["agent_id"],
                    "ssh_host": machine["ssh_host"],
                    "task_id": int(task_id),
                    "site": site,
                    "receipt_path": relative,
                    "receipt_sha256": _sha256_file(path),
                    "status": receipt.get("status"),
                    "fresh_container_transition": (
                        isinstance(after, Mapping)
                        and bool(after.get("container_id"))
                        and (
                            before is None
                            or (
                                isinstance(before, Mapping)
                                and before.get("container_id") != after.get("container_id")
                            )
                        )
                    ),
                    "before_container_id": before.get("container_id") if isinstance(before, Mapping) else None,
                    "after_container_id": after.get("container_id") if isinstance(after, Mapping) else None,
                    "image_id": after.get("image_id") if isinstance(after, Mapping) else None,
                    "sentinel_names": [
                        item.get("name") for item in sentinels if isinstance(item, Mapping)
                    ] if isinstance(sentinels, list) else [],
                }
            )

    consistency: list[dict[str, Any]] = []
    for task_id, rows in cross_host.items():
        signatures = {row["signature_sha256"] for row in rows}
        container_ids = {row["container_id"] for row in rows if row.get("container_id")}
        signature_ok = len(rows) == len(expected_machines) and len(signatures) == 1
        isolated_ok = len(rows) == len(expected_machines) and len(container_ids) == len(expected_machines)
        if not signature_ok:
            blockers.append(f"task {task_id}: cross-host image/sentinel signatures differ or are incomplete")
        if not isolated_ok:
            blockers.append(f"task {task_id}: after-container IDs are not unique across all three hosts")
        consistency.append(
            {
                "task_id": task_id,
                "site": task_sites[task_id],
                "host_count": len(rows),
                "signature_sha256": next(iter(signatures)) if len(signatures) == 1 else None,
                "image_and_sentinels_identical": signature_ok,
                "container_ids_unique_across_hosts": isolated_ok,
            }
        )

    gates = {
        "receipt_set_exact_12": observed_paths == expected_relative_paths,
        "all_receipts_schema_identity_and_lock_valid": len(entries) == 12
        and invalid_receipts == 0,
        "all_receipts_pass": len(entries) == 12 and all(entry["status"] == "pass" for entry in entries),
        "all_container_transitions_fresh": len(entries) == 12
        and all(entry["fresh_container_transition"] for entry in entries),
        "cross_host_sentinels_and_images_identical": len(consistency) == len(task_sites)
        and all(row["image_and_sentinels_identical"] for row in consistency),
        "container_ids_unique_across_hosts": len(consistency) == len(task_sites)
        and all(row["container_ids_unique_across_hosts"] for row in consistency),
    }
    if not all(gates.values()) and not blockers:
        blockers.append("one or more reset-smoke acceptance gates failed")
    return {
        "schema_version": RESET_SMOKE_ACCEPTANCE_SCHEMA,
        "status": "pass" if all(gates.values()) and not blockers else "blocked",
        # Derive this from the immutable source receipts so rebuilding the same
        # acceptance produces the same bytes and therefore the same lock hash.
        "generated_at": (
            max(receipt_completion_times)
            if receipt_completion_times
            else "1970-01-01T00:00:00Z"
        ),
        "inputs": {
            "receipts_root": str(root),
            "site_lock_path": str(site_lock_path),
            "site_lock_sha256": expected_lock_hash,
            "infra_config_path": str(infra_config_path),
            "infra_config_sha256": _sha256_file(Path(infra_config_path)),
        },
        "expected": {
            "machine_ids": list(expected_machines),
            "task_sites": {str(key): value for key, value in task_sites.items()},
            "receipt_count": 12,
            "slots": expected_slots,
        },
        "counts": {
            "expected_receipts": 12,
            "observed_receipts": len(observed_paths),
            "validated_entries": len(entries),
            "blocking_reasons": len(blockers),
        },
        "gates": gates,
        "cross_host_consistency": consistency,
        "entries": entries,
        "blocking_reasons": blockers,
    }


def write_reset_smoke_acceptance(path: str | Path, payload: Mapping[str, Any]) -> None:
    destination = Path(path)
    atomic_write_json(destination, payload)
    digest = _sha256_file(destination)
    _atomic_write_text(destination.with_suffix(destination.suffix + ".sha256"), f"{digest}  {destination.name}\n")


def _validate_receipt(
    receipt: Any,
    *,
    machine: Mapping[str, str],
    task_id: int,
    site: str,
    expected_lock_hash: str,
    site_lock: Mapping[str, Any],
) -> list[str]:
    reasons: list[str] = []
    if not isinstance(receipt, Mapping):
        return ["receipt is not an object"]
    if receipt.get("schema_version") != RESET_RECEIPT_SCHEMA:
        reasons.append("schema mismatch")
    if receipt.get("status") != "pass" or receipt.get("error") is not None or receipt.get("fail_closed") is not None:
        reasons.append("receipt is not a clean pass")
    if receipt.get("site_lock_sha256") != expected_lock_hash:
        reasons.append("site-lock hash mismatch")
    observed_machine = receipt.get("machine")
    expected_machine = {
        "machine_id": machine["machine_id"],
        "ssh_host": machine["ssh_host"],
        "ssh_host_fingerprint": machine["ssh_host_fingerprint"],
    }
    if not isinstance(observed_machine, Mapping) or dict(observed_machine) != expected_machine:
        reasons.append("machine identity mismatch")
    slot = receipt.get("slot")
    if not isinstance(slot, Mapping):
        reasons.append("slot identity missing")
    else:
        if int(slot.get("task_id", -1)) != task_id:
            reasons.append("slot task_id mismatch")
        if slot.get("agent_id") != machine["agent_id"]:
            reasons.append("slot agent_id mismatch")
        expected_slot = _expected_slot_identity(
            machine_id=machine["machine_id"],
            agent_id=machine["agent_id"],
            task_id=task_id,
            site=site,
        )
        if int(slot.get("seed", -1)) != expected_slot["seed"]:
            reasons.append("slot seed mismatch")
        if (
            int(slot.get("attempt_id", -1)) != expected_slot["attempt_id"]
            or slot.get("slot_id") != expected_slot["slot_id"]
        ):
            reasons.append("slot attempt/slot ID mismatch")
    if list(receipt.get("reset_scope") or []) != [site]:
        reasons.append("reset scope mismatch")
    exclusive = receipt.get("exclusive_lock")
    if not isinstance(exclusive, Mapping) or not exclusive.get("acquired_at") or not exclusive.get("released_at"):
        reasons.append("exclusive reset lock evidence missing")
    rows = receipt.get("sites")
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], Mapping):
        reasons.append("site row set is not exact")
        return reasons
    row = rows[0]
    if row.get("site") != site or row.get("ok") is not True:
        reasons.append("site row identity/status mismatch")
    if row.get("image_reference") != pinned_image_reference(site_lock, site):
        reasons.append("pinned image reference mismatch")
    expected_image_id = str(site_lock["images"][site]["digest"])
    if row.get("expected_image_id") != expected_image_id:
        reasons.append("expected image ID mismatch")
    before = row.get("before")
    after = row.get("after")
    if not isinstance(after, Mapping) or after.get("running") is not True:
        reasons.append("replacement container is absent or stopped")
    else:
        if after.get("image_id") != expected_image_id:
            reasons.append("replacement container image mismatch")
        if not str(after.get("container_id") or ""):
            reasons.append("replacement container ID missing")
        if isinstance(before, Mapping) and before.get("container_id") == after.get("container_id"):
            reasons.append("container was not replaced")
        bindings = list(after.get("port_bindings") or [])
        if not bindings or any("127.0.0.1:" not in str(binding) for binding in bindings):
            reasons.append("port binding is absent or not loopback-only")
    sentinels = row.get("sentinels")
    if not isinstance(sentinels, list):
        reasons.append("sentinels missing")
    else:
        names = [item.get("name") for item in sentinels if isinstance(item, Mapping)]
        if names != EXPECTED_SENTINELS[site]:
            reasons.append("sentinel set/order mismatch")
        if len(names) != len(sentinels) or any(item.get("ok") is not True for item in sentinels):
            reasons.append("one or more sentinels failed")
    return reasons


def _expected_machines(infra: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    machines: dict[str, dict[str, str]] = {}
    for raw in list(infra.get("machines") or []):
        if raw.get("enabled") is False or raw.get("role") != "webarena_vps":
            continue
        benchmark = dict(raw.get("benchmarks", {}).get("WebArena-Verified") or {})
        if not benchmark:
            continue
        machine_id = str(raw.get("machine_id") or "")
        machine = {
            "machine_id": machine_id,
            "agent_id": str(raw.get("assigned_agent_id") or ""),
            "ssh_host": str(raw.get("ssh", {}).get("host") or ""),
            "ssh_host_fingerprint": str(
                benchmark.get("site_controller", {}).get("ssh_host_fingerprint") or ""
            ),
        }
        if not all(machine.values()):
            raise ValueError(f"incomplete WebArena machine identity in infra config: {machine_id!r}")
        machines[machine_id] = machine
    if len(machines) != 3 or set(machine["agent_id"] for machine in machines.values()) != {
        "Agent A",
        "Agent B",
        "Agent C",
    }:
        raise ValueError("infra config must define exactly the three locked WebArena agent machines")
    return machines


def _expected_slot_identity(
    *,
    machine_id: str,
    agent_id: str,
    task_id: int,
    site: str,
) -> dict[str, Any]:
    label = "admin" if site == "shopping_admin" else site
    return {
        "machine_id": machine_id,
        "agent_id": agent_id,
        "task_id": int(task_id),
        "site": site,
        "seed": 123000 + int(task_id),
        "attempt_id": 1,
        "slot_id": f"reset-smoke-{machine_id}-{label}",
    }


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_json(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


__all__ = [
    "DEFAULT_TASK_SITES",
    "RESET_SMOKE_ACCEPTANCE_SCHEMA",
    "build_reset_smoke_acceptance",
    "write_reset_smoke_acceptance",
]
