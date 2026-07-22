"""Fail-closed acceptance for the six extended, two-site WebArena resets."""

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
    sites_for_agent_input,
    WebArenaSiteError,
)


EXTENDED_RESET_ACCEPTANCE_SCHEMA = (
    "webarena_verified_extended_real_reset_acceptance/v1"
)
EXTENDED_TASKS: dict[int, dict[str, list[str]]] = {
    97: {
        "official_sites": ["map", "wikipedia"],
        "reset_scope": ["wikipedia", "map"],
    },
    759: {
        "official_sites": ["map", "shopping_admin"],
        "reset_scope": ["shopping_admin", "map"],
    },
}
EXPECTED_SENTINELS: dict[str, list[str]] = {
    "wikipedia": ["env_ctrl_status", "homepage"],
    "shopping_admin": [
        "env_ctrl_status",
        "homepage",
        "shopping_admin_reviews",
    ],
    "map": [
        "homepage",
        "map_env_ctrl_process",
        "map_postgres_ports",
        "map_rails",
        "map_osrm_profiles",
        "map_tile_png",
        "map_nominatim",
        "map_route_distance",
    ],
}
MAP_ROUTE_DISTANCE_METERS = 10289.9
MAP_ROUTE_DISTANCE_TOLERANCE = 5.0


def build_extended_reset_acceptance(
    *,
    receipts_root: str | Path,
    site_lock_path: str | Path,
    infra_config_path: str | Path,
    agent_inputs_path: str | Path,
) -> dict[str, Any]:
    """Validate exactly three machines by two locked, two-site reset tasks."""

    root = Path(receipts_root)
    site_lock = load_site_lock(site_lock_path)
    infra = json.loads(Path(infra_config_path).read_text(encoding="utf-8"))
    machines = _expected_machines(infra)
    lock_hash = _sha256_json(site_lock)
    source_reasons, source_tasks = _validate_source_tasks(agent_inputs_path)

    expected_paths = {
        f"{machine_id}/{task_id}/reset_receipt.json"
        for machine_id in machines
        for task_id in EXTENDED_TASKS
    }
    observed_paths = (
        {
            path.relative_to(root).as_posix()
            for path in root.rglob("reset_receipt.json")
            if path.is_file()
        }
        if root.is_dir()
        else set()
    )
    blockers = list(source_reasons)
    missing = sorted(expected_paths - observed_paths)
    extras = sorted(observed_paths - expected_paths)
    if missing:
        blockers.append(f"missing extended reset receipts: {', '.join(missing)}")
    if extras:
        blockers.append(f"unexpected extended reset receipts: {', '.join(extras)}")

    entries: list[dict[str, Any]] = []
    completion_times: list[str] = []
    validation_flags: dict[str, list[bool]] = {
        "clean_pass": [],
        "schema_identity_lock": [],
        "scope_order": [],
        "exclusive_lock": [],
        "digest_loopback": [],
        "sentinels": [],
        "fresh": [],
    }
    cross_host_rows: dict[tuple[int, str], list[dict[str, Any]]] = {
        (task_id, site): []
        for task_id, task in EXTENDED_TASKS.items()
        for site in task["reset_scope"]
    }
    all_after_ids: list[str] = []

    for machine_id, machine in machines.items():
        for task_id, task in EXTENDED_TASKS.items():
            relative = f"{machine_id}/{task_id}/reset_receipt.json"
            path = root / relative
            if not path.is_file():
                continue
            try:
                receipt = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                blockers.append(f"invalid JSON {relative}: {exc}")
                continue
            result = _validate_receipt(
                receipt,
                machine=machine,
                task_id=task_id,
                reset_scope=task["reset_scope"],
                expected_lock_hash=lock_hash,
                site_lock=site_lock,
            )
            blockers.extend(f"{relative}: {reason}" for reason in result["reasons"])
            for flag in validation_flags:
                validation_flags[flag].append(bool(result["flags"][flag]))
            completed_at = receipt.get("completed_at")
            if isinstance(completed_at, str) and completed_at:
                completion_times.append(completed_at)

            row_summaries: list[dict[str, Any]] = []
            for row in result["rows"]:
                task_site_key = (task_id, row["site"])
                cross_host_rows[task_site_key].append(
                    {
                        "machine_id": machine_id,
                        "signature_sha256": row["signature_sha256"],
                        "after_container_id": row["after_container_id"],
                    }
                )
                if row["after_container_id"]:
                    all_after_ids.append(row["after_container_id"])
                row_summaries.append(
                    {
                        key: value
                        for key, value in row.items()
                        if key != "signature_sha256"
                    }
                )
            entries.append(
                {
                    "machine_id": machine_id,
                    "agent_id": machine["agent_id"],
                    "ssh_host": machine["ssh_host"],
                    "task_id": task_id,
                    "expected_reset_scope": list(task["reset_scope"]),
                    "receipt_path": relative,
                    "receipt_sha256": _sha256_file(path),
                    "status": receipt.get("status"),
                    "flags": result["flags"],
                    "sites": row_summaries,
                }
            )

    cross_host_consistency: list[dict[str, Any]] = []
    for (task_id, site), rows in cross_host_rows.items():
        signatures = {str(row["signature_sha256"]) for row in rows}
        container_ids = {
            str(row["after_container_id"])
            for row in rows
            if row["after_container_id"]
        }
        signature_ok = len(rows) == len(machines) and len(signatures) == 1
        containers_unique = (
            len(rows) == len(machines) and len(container_ids) == len(machines)
        )
        if not signature_ok:
            blockers.append(
                f"task {task_id} site {site}: cross-host digest/sentinel signatures differ or are incomplete"
            )
        if not containers_unique:
            blockers.append(
                f"task {task_id} site {site}: fresh container IDs are not unique across all hosts"
            )
        cross_host_consistency.append(
            {
                "task_id": task_id,
                "site": site,
                "host_count": len(rows),
                "signature_sha256": (
                    next(iter(signatures)) if len(signatures) == 1 else None
                ),
                "digest_and_sentinels_identical": signature_ok,
                "fresh_container_ids_unique_across_hosts": containers_unique,
            }
        )

    expected_receipts = len(machines) * len(EXTENDED_TASKS)
    expected_site_rows = sum(
        len(task["reset_scope"]) for task in EXTENDED_TASKS.values()
    ) * len(machines)
    global_container_ids_unique = (
        len(all_after_ids) == expected_site_rows
        and len(set(all_after_ids)) == expected_site_rows
    )
    if not global_container_ids_unique:
        blockers.append(
            "extended reset after-container IDs are missing or reused across task/site slots"
        )

    def all_receipts(flag: str) -> bool:
        values = validation_flags[flag]
        return len(values) == expected_receipts and all(values)

    gates = {
        "locked_task_sources_and_scopes_exact": not source_reasons,
        "receipt_set_exact_6": observed_paths == expected_paths,
        "all_receipts_clean_pass": all_receipts("clean_pass"),
        "all_receipts_schema_identity_and_lock_valid": all_receipts(
            "schema_identity_lock"
        ),
        "all_two_site_scope_and_row_order_exact": all_receipts("scope_order"),
        "all_exclusive_locks_complete": all_receipts("exclusive_lock"),
        "all_digest_and_loopback_bindings_valid": all_receipts(
            "digest_loopback"
        ),
        "all_map_wiki_admin_sentinels_pass": all_receipts("sentinels"),
        "all_container_transitions_fresh": all_receipts("fresh"),
        "cross_host_digest_and_sentinels_identical": len(
            cross_host_consistency
        ) == expected_site_rows // len(machines)
        and all(
            row["digest_and_sentinels_identical"]
            for row in cross_host_consistency
        ),
        "cross_host_container_ids_unique": len(cross_host_consistency)
        == expected_site_rows // len(machines)
        and all(
            row["fresh_container_ids_unique_across_hosts"]
            for row in cross_host_consistency
        ),
        "all_12_after_container_ids_globally_unique": global_container_ids_unique,
    }
    if not all(gates.values()) and not blockers:
        blockers.append("one or more extended reset acceptance gates failed")
    return {
        "schema_version": EXTENDED_RESET_ACCEPTANCE_SCHEMA,
        "status": "pass" if all(gates.values()) and not blockers else "blocked",
        "generated_at": (
            max(completion_times) if completion_times else "1970-01-01T00:00:00Z"
        ),
        "inputs": {
            "receipts_root": str(root),
            "site_lock_path": str(site_lock_path),
            "site_lock_sha256": lock_hash,
            "infra_config_path": str(infra_config_path),
            "infra_config_sha256": _sha256_file(Path(infra_config_path)),
            "agent_inputs_path": str(agent_inputs_path),
            "agent_inputs_sha256": _sha256_file(Path(agent_inputs_path)),
        },
        "expected": {
            "machine_ids": list(machines),
            "receipt_count": expected_receipts,
            "site_row_count": expected_site_rows,
            "tasks": source_tasks,
            "slots": [
                _expected_slot_identity(
                    machine_id=machine_id,
                    agent_id=machine["agent_id"],
                    task_id=task_id,
                )
                for machine_id, machine in machines.items()
                for task_id in EXTENDED_TASKS
            ],
        },
        "counts": {
            "expected_receipts": expected_receipts,
            "observed_receipts": len(observed_paths),
            "validated_receipts": len(entries),
            "expected_site_rows": expected_site_rows,
            "observed_validated_site_rows": sum(
                len(entry["sites"]) for entry in entries
            ),
            "blocking_reasons": len(blockers),
        },
        "gates": gates,
        "cross_host_consistency": cross_host_consistency,
        "entries": entries,
        "blocking_reasons": blockers,
    }


def write_extended_reset_acceptance(
    path: str | Path, payload: Mapping[str, Any]
) -> None:
    destination = Path(path)
    atomic_write_json(destination, payload)
    digest = _sha256_file(destination)
    _atomic_write_text(
        destination.with_suffix(destination.suffix + ".sha256"),
        f"{digest}  {destination.name}\n",
    )


def _validate_source_tasks(
    agent_inputs_path: str | Path,
) -> tuple[list[str], list[dict[str, Any]]]:
    payload = json.loads(Path(agent_inputs_path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        return ["official agent-input source is not a list"], []
    by_id = {
        int(item["task_id"]): item
        for item in payload
        if isinstance(item, Mapping) and "task_id" in item
    }
    reasons: list[str] = []
    tasks: list[dict[str, Any]] = []
    for task_id, expected in EXTENDED_TASKS.items():
        item = by_id.get(task_id)
        if not isinstance(item, Mapping):
            reasons.append(f"official task {task_id} is missing")
            continue
        official_sites = list(item.get("sites") or [])
        if official_sites != expected["official_sites"]:
            reasons.append(f"official task {task_id} site list changed")
        try:
            reset_scope = sites_for_agent_input(item, expected_task_id=task_id)
        except (TypeError, ValueError, WebArenaSiteError) as exc:
            reasons.append(f"official task {task_id} is invalid: {exc}")
            reset_scope = []
        if reset_scope != expected["reset_scope"]:
            reasons.append(f"official task {task_id} canonical reset scope changed")
        tasks.append(
            {
                "task_id": task_id,
                "official_sites": official_sites,
                "reset_scope": reset_scope,
                "agent_input_sha256": _sha256_json(item),
            }
        )
    return reasons, tasks


def _validate_receipt(
    receipt: Any,
    *,
    machine: Mapping[str, str],
    task_id: int,
    reset_scope: list[str],
    expected_lock_hash: str,
    site_lock: Mapping[str, Any],
) -> dict[str, Any]:
    reasons: list[str] = []
    flags = {
        "clean_pass": True,
        "schema_identity_lock": True,
        "scope_order": True,
        "exclusive_lock": True,
        "digest_loopback": True,
        "sentinels": True,
        "fresh": True,
    }

    def fail(flag: str, reason: str) -> None:
        flags[flag] = False
        reasons.append(reason)

    if not isinstance(receipt, Mapping):
        for flag in flags:
            flags[flag] = False
        return {"reasons": ["receipt is not an object"], "flags": flags, "rows": []}
    if (
        receipt.get("status") != "pass"
        or receipt.get("error") is not None
        or receipt.get("fail_closed") is not None
    ):
        fail("clean_pass", "receipt is not a clean pass")
    if receipt.get("schema_version") != RESET_RECEIPT_SCHEMA:
        fail("schema_identity_lock", "schema mismatch")
    if receipt.get("site_lock_sha256") != expected_lock_hash:
        fail("schema_identity_lock", "site-lock hash mismatch")
    expected_machine = {
        "machine_id": machine["machine_id"],
        "ssh_host": machine["ssh_host"],
        "ssh_host_fingerprint": machine["ssh_host_fingerprint"],
    }
    if not isinstance(receipt.get("machine"), Mapping) or dict(
        receipt["machine"]
    ) != expected_machine:
        fail("schema_identity_lock", "machine identity mismatch")
    expected_slot = _expected_slot_identity(
        machine_id=machine["machine_id"],
        agent_id=machine["agent_id"],
        task_id=task_id,
    )
    expected_slot_receipt = {
        key: value for key, value in expected_slot.items() if key != "machine_id"
    }
    if not isinstance(receipt.get("slot"), Mapping) or dict(
        receipt["slot"]
    ) != expected_slot_receipt:
        fail("schema_identity_lock", "slot identity mismatch")

    if list(receipt.get("reset_scope") or []) != reset_scope:
        fail("scope_order", "two-site reset scope/order mismatch")
    rows = receipt.get("sites")
    if not isinstance(rows, list) or len(rows) != 2 or any(
        not isinstance(row, Mapping) for row in rows
    ):
        fail("scope_order", "site row set is not exactly two objects")
        rows = []
    elif [row.get("site") for row in rows] != reset_scope:
        fail("scope_order", "two site rows are missing, duplicated, or reordered")

    exclusive = receipt.get("exclusive_lock")
    if not isinstance(exclusive, Mapping):
        fail("exclusive_lock", "exclusive lock evidence missing")
    else:
        if exclusive.get("path") != site_lock["slot_lock_file"]:
            fail("exclusive_lock", "exclusive lock path mismatch")
        acquired = str(exclusive.get("acquired_at") or "")
        released = str(exclusive.get("released_at") or "")
        if not acquired or not released or acquired > released:
            fail("exclusive_lock", "exclusive lock timestamps are absent or reversed")
        started = str(receipt.get("started_at") or "")
        completed = str(receipt.get("completed_at") or "")
        if not started or not completed or not (started <= acquired <= released <= completed):
            fail("exclusive_lock", "exclusive lock timestamps fall outside receipt lifetime")

    summaries: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        site = reset_scope[index]
        if row.get("site") != site or row.get("ok") is not True:
            fail("scope_order", f"{site} row identity/status mismatch")
        expected_image = str(site_lock["images"][site]["digest"])
        image_reference = pinned_image_reference(site_lock, site)
        if (
            row.get("image_reference") != image_reference
            or row.get("expected_image_id") != expected_image
        ):
            fail("digest_loopback", f"{site} pinned image evidence mismatch")
        before = row.get("before")
        after = row.get("after")
        after_id: str | None = None
        before_id: str | None = None
        if isinstance(before, Mapping):
            before_id = str(before.get("container_id") or "") or None
        if not isinstance(after, Mapping):
            fail("digest_loopback", f"{site} replacement container evidence missing")
            fail("fresh", f"{site} replacement container ID missing")
            after = {}
        else:
            after_id = str(after.get("container_id") or "") or None
            if after.get("running") is not True or after.get("image_id") != expected_image:
                fail("digest_loopback", f"{site} replacement image/running state mismatch")
            if not after_id:
                fail("fresh", f"{site} replacement container ID missing")
            if before_id and before_id == after_id:
                fail("fresh", f"{site} container was not replaced")
            bindings = list(after.get("port_bindings") or [])
            expected_bindings = _expected_port_bindings(site_lock, site)
            if set(str(binding) for binding in bindings) != expected_bindings:
                fail("digest_loopback", f"{site} loopback port binding set mismatch")
            if any(
                "127.0.0.1:" not in str(binding)
                or "0.0.0.0:" in str(binding)
                or "[::]" in str(binding)
                for binding in bindings
            ):
                fail("digest_loopback", f"{site} exposes a non-loopback binding")

        sentinels = row.get("sentinels")
        if not isinstance(sentinels, list):
            fail("sentinels", f"{site} sentinels missing")
            sentinels = []
        names = [
            item.get("name") for item in sentinels if isinstance(item, Mapping)
        ]
        if names != EXPECTED_SENTINELS[site] or len(names) != len(sentinels):
            fail("sentinels", f"{site} sentinel set/order mismatch")
        if any(
            not isinstance(item, Mapping) or item.get("ok") is not True
            for item in sentinels
        ):
            fail("sentinels", f"{site} has a failed sentinel")
        if site == "map":
            map_rows = [
                item
                for item in sentinels
                if isinstance(item, Mapping)
                and item.get("name") == "map_route_distance"
            ]
            distance = map_rows[0].get("actual_distance_meters") if len(map_rows) == 1 else None
            if not isinstance(distance, (int, float)) or abs(
                float(distance) - MAP_ROUTE_DISTANCE_METERS
            ) > MAP_ROUTE_DISTANCE_TOLERANCE:
                fail("sentinels", "map route distance sentinel value mismatch")

        signature = {
            "site": site,
            "image_reference": row.get("image_reference"),
            "expected_image_id": row.get("expected_image_id"),
            "port_bindings": list(after.get("port_bindings") or []),
            "sentinels": sentinels,
        }
        summaries.append(
            {
                "site": site,
                "before_container_id": before_id,
                "after_container_id": after_id,
                "fresh_container_transition": bool(after_id)
                and (not before_id or before_id != after_id),
                "image_id": after.get("image_id"),
                "port_bindings": list(after.get("port_bindings") or []),
                "sentinel_names": names,
                "signature_sha256": _sha256_json(signature),
            }
        )
    return {"reasons": reasons, "flags": flags, "rows": summaries}


def _expected_machines(infra: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for raw in list(infra.get("machines") or []):
        if raw.get("enabled") is False or raw.get("role") != "webarena_vps":
            continue
        benchmark = dict(
            raw.get("benchmarks", {}).get("WebArena-Verified") or {}
        )
        if not benchmark:
            continue
        machine_id = str(raw.get("machine_id") or "")
        machine = {
            "machine_id": machine_id,
            "agent_id": str(raw.get("assigned_agent_id") or ""),
            "ssh_host": str(raw.get("ssh", {}).get("host") or ""),
            "ssh_host_fingerprint": str(
                benchmark.get("site_controller", {}).get(
                    "ssh_host_fingerprint"
                )
                or ""
            ),
        }
        if not all(machine.values()) or machine_id in result:
            raise ValueError(
                f"invalid or duplicate WebArena machine identity: {machine_id!r}"
            )
        result[machine_id] = machine
    if len(result) != 3 or {
        machine["agent_id"] for machine in result.values()
    } != {"Agent A", "Agent B", "Agent C"}:
        raise ValueError(
            "infra config must define exactly the three locked WebArena agent machines"
        )
    return result


def _expected_slot_identity(
    *, machine_id: str, agent_id: str, task_id: int
) -> dict[str, Any]:
    return {
        "machine_id": machine_id,
        "slot_id": f"reset-extended-{machine_id}-task-{task_id}",
        "task_id": int(task_id),
        "agent_id": agent_id,
        "attempt_id": 1,
        "seed": 123000 + int(task_id),
    }


def _expected_port_bindings(
    site_lock: Mapping[str, Any], site: str
) -> set[str]:
    spec = site_lock["sites"][site]
    return {
        f"{int(spec['container_port'])}/tcp -> 127.0.0.1:{int(spec['host_port'])}",
        (
            f"{int(spec['env_ctrl_container_port'])}/tcp -> "
            f"127.0.0.1:{int(spec['env_ctrl_host_port'])}"
        ),
    }


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_json(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
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
    "EXPECTED_SENTINELS",
    "EXTENDED_RESET_ACCEPTANCE_SCHEMA",
    "EXTENDED_TASKS",
    "build_extended_reset_acceptance",
    "write_extended_reset_acceptance",
]
