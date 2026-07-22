from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evidence_system.webarena_reset_acceptance import (
    DEFAULT_TASK_SITES,
    EXPECTED_SENTINELS,
    build_reset_smoke_acceptance,
    write_reset_smoke_acceptance,
)
from evidence_system.webarena_sites import load_site_lock, pinned_image_reference


ROOT = Path(__file__).resolve().parents[2]


def _write_fixture_receipts(root: Path) -> None:
    infra = json.loads((ROOT / "configs/infra.yaml").read_text(encoding="utf-8"))
    lock = load_site_lock(ROOT / "configs/webarena_verified_sites.lock.json")
    lock_hash = hashlib.sha256(
        json.dumps(lock, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    machines = [machine for machine in infra["machines"] if machine.get("role") == "webarena_vps"]
    for machine_index, machine in enumerate(machines):
        benchmark = machine["benchmarks"]["WebArena-Verified"]
        for task_id, site in DEFAULT_TASK_SITES.items():
            image_id = lock["images"][site]["digest"]
            path = root / machine["machine_id"] / str(task_id) / "reset_receipt.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "webarena_verified_slot_reset_receipt/v1",
                        "status": "pass",
                        "error": None,
                        "fail_closed": None,
                        "site_lock_sha256": lock_hash,
                        "machine": {
                            "machine_id": machine["machine_id"],
                            "ssh_host": machine["ssh"]["host"],
                            "ssh_host_fingerprint": benchmark["site_controller"]["ssh_host_fingerprint"],
                        },
                        "slot": {
                            "slot_id": (
                                f"reset-smoke-{machine['machine_id']}-"
                                f"{'admin' if site == 'shopping_admin' else site}"
                            ),
                            "task_id": task_id,
                            "agent_id": machine["assigned_agent_id"],
                            "attempt_id": 1,
                            "seed": 123000 + task_id,
                        },
                        "exclusive_lock": {"acquired_at": "start", "released_at": "end"},
                        "reset_scope": [site],
                        "sites": [
                            {
                                "site": site,
                                "ok": True,
                                "image_reference": pinned_image_reference(lock, site),
                                "expected_image_id": image_id,
                                "before": None,
                                "after": {
                                    "container_id": f"container-{machine_index}-{task_id}",
                                    "image_id": image_id,
                                    "running": True,
                                    "port_bindings": ["80/tcp -> 127.0.0.1:7770"],
                                },
                                "sentinels": [
                                    {"name": name, "ok": True}
                                    for name in EXPECTED_SENTINELS[site]
                                ],
                            }
                        ],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )


def test_real_reset_smoke_acceptance_requires_exact_consistent_twelve(tmp_path: Path) -> None:
    receipts = tmp_path / "receipts"
    _write_fixture_receipts(receipts)

    acceptance = build_reset_smoke_acceptance(
        receipts_root=receipts,
        site_lock_path=ROOT / "configs/webarena_verified_sites.lock.json",
        infra_config_path=ROOT / "configs/infra.yaml",
    )
    assert acceptance["status"] == "pass"
    assert acceptance["counts"]["observed_receipts"] == 12
    assert all(acceptance["gates"].values())
    assert len(acceptance["cross_host_consistency"]) == 4
    assert acceptance == build_reset_smoke_acceptance(
        receipts_root=receipts,
        site_lock_path=ROOT / "configs/webarena_verified_sites.lock.json",
        infra_config_path=ROOT / "configs/infra.yaml",
    )

    output = tmp_path / "acceptance.json"
    write_reset_smoke_acceptance(output, acceptance)
    assert output.is_file()
    assert output.with_suffix(".json.sha256").is_file()


def test_real_reset_smoke_acceptance_blocks_sentinel_or_cross_host_container_drift(
    tmp_path: Path,
) -> None:
    receipts = tmp_path / "receipts"
    _write_fixture_receipts(receipts)
    path = receipts / "webarena-claude47-ord" / "0" / "reset_receipt.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["sites"][0]["sentinels"][-1]["ok"] = False
    payload["sites"][0]["after"]["container_id"] = "container-0-0"
    path.write_text(json.dumps(payload), encoding="utf-8")

    acceptance = build_reset_smoke_acceptance(
        receipts_root=receipts,
        site_lock_path=ROOT / "configs/webarena_verified_sites.lock.json",
        infra_config_path=ROOT / "configs/infra.yaml",
    )
    assert acceptance["status"] == "blocked"
    assert acceptance["gates"]["all_receipts_schema_identity_and_lock_valid"] is False
    assert acceptance["gates"]["cross_host_sentinels_and_images_identical"] is False
    assert acceptance["gates"]["container_ids_unique_across_hosts"] is False


def test_current_real_reset_smoke_remains_blocked_until_all_twelve_exist() -> None:
    acceptance = build_reset_smoke_acceptance(
        receipts_root=(
            ROOT
            / "experiments/step20/webarena_verified/environment_receipts/real_reset_smoke"
        ),
        site_lock_path=ROOT / "configs/webarena_verified_sites.lock.json",
        infra_config_path=ROOT / "configs/infra.yaml",
    )
    assert acceptance["status"] in {"pass", "blocked"}
    if acceptance["counts"]["observed_receipts"] != 12:
        assert acceptance["status"] == "blocked"
