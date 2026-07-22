from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from evidence_system.cli.webarena_extended_reset_acceptance import main as cli_main
from evidence_system.webarena_extended_reset_acceptance import (
    EXPECTED_SENTINELS,
    EXTENDED_TASKS,
    build_extended_reset_acceptance,
    write_extended_reset_acceptance,
)
from evidence_system.webarena_sites import load_site_lock, pinned_image_reference


ROOT = Path(__file__).resolve().parents[2]
SITE_LOCK = ROOT / "configs/webarena_verified_sites.lock.json"
INFRA_CONFIG = ROOT / "configs/infra.yaml"
AGENT_INPUTS = (
    ROOT
    / "experiments/official_splits/webarena_verified_agent_inputs_full_812.json"
)


def _canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def _machines() -> list[dict[str, Any]]:
    infra = json.loads(INFRA_CONFIG.read_text(encoding="utf-8"))
    return [
        machine
        for machine in infra["machines"]
        if machine.get("role") == "webarena_vps"
        and machine.get("enabled") is not False
    ]


def _port_bindings(lock: dict[str, Any], site: str) -> list[str]:
    spec = lock["sites"][site]
    return sorted(
        [
            (
                f"{spec['container_port']}/tcp -> "
                f"127.0.0.1:{spec['host_port']}"
            ),
            (
                f"{spec['env_ctrl_container_port']}/tcp -> "
                f"127.0.0.1:{spec['env_ctrl_host_port']}"
            ),
        ]
    )


def _sentinels(site: str) -> list[dict[str, Any]]:
    rows = [{"name": name, "ok": True} for name in EXPECTED_SENTINELS[site]]
    if site == "map":
        rows[-1]["actual_distance_meters"] = 10289.9
    return rows


def _write_receipts(root: Path) -> None:
    lock = load_site_lock(SITE_LOCK)
    lock_hash = _canonical_sha256(lock)
    for machine_index, machine in enumerate(_machines()):
        benchmark = machine["benchmarks"]["WebArena-Verified"]
        for task_id, task in EXTENDED_TASKS.items():
            sites: list[dict[str, Any]] = []
            for site_index, site in enumerate(task["reset_scope"]):
                digest = lock["images"][site]["digest"]
                sites.append(
                    {
                        "site": site,
                        "image_reference": pinned_image_reference(lock, site),
                        "expected_image_id": digest,
                        "before": {
                            "container_id": (
                                f"before-{machine_index}-{task_id}-{site_index}"
                            )
                        },
                        "after": {
                            "container_id": (
                                f"after-{machine_index}-{task_id}-{site_index}"
                            ),
                            "image_id": digest,
                            "running": True,
                            "port_bindings": _port_bindings(lock, site),
                        },
                        "mutable_volumes_restored": [],
                        "sentinels": _sentinels(site),
                        "started_at": "2026-07-16T00:00:02Z",
                        "completed_at": "2026-07-16T00:00:03Z",
                        "duration_seconds": 1.0,
                        "ok": True,
                    }
                )
            receipt = {
                "schema_version": "webarena_verified_slot_reset_receipt/v1",
                "status": "pass",
                "slot": {
                    "slot_id": (
                        f"reset-extended-{machine['machine_id']}-task-{task_id}"
                    ),
                    "task_id": task_id,
                    "agent_id": machine["assigned_agent_id"],
                    "attempt_id": 1,
                    "seed": 123000 + task_id,
                },
                "machine": {
                    "machine_id": machine["machine_id"],
                    "ssh_host": machine["ssh"]["host"],
                    "ssh_host_fingerprint": benchmark["site_controller"][
                        "ssh_host_fingerprint"
                    ],
                },
                "site_lock_sha256": lock_hash,
                "reset_scope": list(task["reset_scope"]),
                "started_at": "2026-07-16T00:00:00Z",
                "completed_at": "2026-07-16T00:00:05Z",
                "duration_seconds": 5.0,
                "exclusive_lock": {
                    "path": lock["slot_lock_file"],
                    "acquired_at": "2026-07-16T00:00:01Z",
                    "released_at": "2026-07-16T00:00:04Z",
                },
                "sites": sites,
                "fail_closed": None,
                "error": None,
            }
            path = root / machine["machine_id"] / str(task_id) / "reset_receipt.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )


def _build(receipts: Path) -> dict[str, Any]:
    return build_extended_reset_acceptance(
        receipts_root=receipts,
        site_lock_path=SITE_LOCK,
        infra_config_path=INFRA_CONFIG,
        agent_inputs_path=AGENT_INPUTS,
    )


def _receipt_path(receipts: Path, machine_index: int, task_id: int) -> Path:
    return (
        receipts
        / _machines()[machine_index]["machine_id"]
        / str(task_id)
        / "reset_receipt.json"
    )


def _mutate(path: Path, callback: Any) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    callback(payload)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_extended_acceptance_passes_exact_six_two_site_receipts(
    tmp_path: Path,
) -> None:
    receipts = tmp_path / "receipts"
    _write_receipts(receipts)

    acceptance = _build(receipts)

    assert acceptance["status"] == "pass"
    assert acceptance["counts"] == {
        "expected_receipts": 6,
        "observed_receipts": 6,
        "validated_receipts": 6,
        "expected_site_rows": 12,
        "observed_validated_site_rows": 12,
        "blocking_reasons": 0,
    }
    assert all(acceptance["gates"].values())
    assert [task["reset_scope"] for task in acceptance["expected"]["tasks"]] == [
        ["wikipedia", "map"],
        ["shopping_admin", "map"],
    ]
    assert acceptance == _build(receipts)

    output = tmp_path / "acceptance.json"
    write_extended_reset_acceptance(output, acceptance)
    assert output.is_file()
    assert output.with_suffix(".json.sha256").is_file()


@pytest.mark.parametrize(
    ("task_id", "mutator", "failed_gate"),
    [
        (
            97,
            lambda payload: payload.update(
                {
                    "reset_scope": ["map", "wikipedia"],
                    "sites": list(reversed(payload["sites"])),
                }
            ),
            "all_two_site_scope_and_row_order_exact",
        ),
        (
            97,
            lambda payload: payload["exclusive_lock"].update(
                {"released_at": None}
            ),
            "all_exclusive_locks_complete",
        ),
        (
            97,
            lambda payload: payload["sites"][1]["after"].update(
                {"port_bindings": ["8080/tcp -> 0.0.0.0:3030"]}
            ),
            "all_digest_and_loopback_bindings_valid",
        ),
        (
            97,
            lambda payload: payload["sites"][1]["sentinels"][-1].update(
                {"actual_distance_meters": 1.0}
            ),
            "all_map_wiki_admin_sentinels_pass",
        ),
        (
            759,
            lambda payload: payload["sites"][0]["after"].update(
                {
                    "container_id": payload["sites"][0]["before"][
                        "container_id"
                    ]
                }
            ),
            "all_container_transitions_fresh",
        ),
    ],
)
def test_extended_acceptance_fails_closed_for_required_evidence_drift(
    tmp_path: Path,
    task_id: int,
    mutator: Any,
    failed_gate: str,
) -> None:
    receipts = tmp_path / "receipts"
    _write_receipts(receipts)
    _mutate(_receipt_path(receipts, 0, task_id), mutator)

    acceptance = _build(receipts)

    assert acceptance["status"] == "blocked"
    assert acceptance["gates"][failed_gate] is False
    assert acceptance["blocking_reasons"]


def test_extended_acceptance_rejects_cross_host_container_id_reuse(
    tmp_path: Path,
) -> None:
    receipts = tmp_path / "receipts"
    _write_receipts(receipts)
    first = json.loads(_receipt_path(receipts, 0, 97).read_text(encoding="utf-8"))
    reused = first["sites"][1]["after"]["container_id"]
    _mutate(
        _receipt_path(receipts, 1, 97),
        lambda payload: payload["sites"][1]["after"].update(
            {"container_id": reused}
        ),
    )

    acceptance = _build(receipts)

    assert acceptance["status"] == "blocked"
    assert acceptance["gates"]["cross_host_container_ids_unique"] is False
    assert (
        acceptance["gates"]["all_12_after_container_ids_globally_unique"]
        is False
    )


def test_extended_acceptance_rejects_extra_receipt_and_source_scope_drift(
    tmp_path: Path,
) -> None:
    receipts = tmp_path / "receipts"
    _write_receipts(receipts)
    extra = receipts / "unexpected" / "97" / "reset_receipt.json"
    extra.parent.mkdir(parents=True)
    extra.write_text("{}\n", encoding="utf-8")
    source = json.loads(AGENT_INPUTS.read_text(encoding="utf-8"))
    next(item for item in source if item["task_id"] == 759)["sites"] = ["map"]
    source_path = tmp_path / "agent_inputs.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    acceptance = build_extended_reset_acceptance(
        receipts_root=receipts,
        site_lock_path=SITE_LOCK,
        infra_config_path=INFRA_CONFIG,
        agent_inputs_path=source_path,
    )

    assert acceptance["status"] == "blocked"
    assert acceptance["gates"]["receipt_set_exact_6"] is False
    assert acceptance["gates"]["locked_task_sources_and_scopes_exact"] is False


def test_extended_acceptance_cli_writes_report_and_hash(tmp_path: Path) -> None:
    receipts = tmp_path / "receipts"
    _write_receipts(receipts)
    output = tmp_path / "acceptance.json"

    exit_code = cli_main(
        [
            "--receipts-root",
            str(receipts),
            "--site-lock",
            str(SITE_LOCK),
            "--infra-config",
            str(INFRA_CONFIG),
            "--agent-inputs",
            str(AGENT_INPUTS),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "pass"
    assert output.with_suffix(".json.sha256").is_file()


def test_current_extended_receipt_root_is_blocked_until_real_resets_exist() -> None:
    acceptance = build_extended_reset_acceptance(
        receipts_root=(
            ROOT
            / "experiments/step20/webarena_verified/environment_receipts/"
            "extended_real_reset"
        ),
        site_lock_path=SITE_LOCK,
        infra_config_path=INFRA_CONFIG,
        agent_inputs_path=AGENT_INPUTS,
    )
    assert acceptance["status"] in {"pass", "blocked"}
    if acceptance["counts"]["observed_receipts"] != 6:
        assert acceptance["status"] == "blocked"
