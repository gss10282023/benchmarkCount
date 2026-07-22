from __future__ import annotations

import copy
from pathlib import Path

import pytest

from evidence_system.orchestrator.webarena_verified_full import WebArenaFullScheduleError
from evidence_system.orchestrator.webarena_verified_pilot import (
    PILOT_AGENT_ORDERS,
    PILOT_TASK_IDS,
    build_pilot_manifest,
    validate_pilot_manifest,
)


def test_pilot_manifest_freezes_8x3_coverage_and_counterbalance() -> None:
    payload = build_pilot_manifest()

    assert [case["task_id"] for case in payload["cases"]] == list(PILOT_TASK_IDS)
    assert [case["agent_order"] for case in payload["cases"]] == [
        list(order) for order in PILOT_AGENT_ORDERS
    ]
    assert payload["counts"] == {
        "cases": 8,
        "record_slots": 24,
        "per_agent": {"Agent A": 8, "Agent B": 8, "Agent C": 8},
        "fallback_contracts": 0,
    }
    assert payload["coverage"]["sites"] == [
        "gitlab",
        "map",
        "reddit",
        "shopping",
        "shopping_admin",
        "wikipedia",
    ]
    assert payload["coverage"]["task_types"] == ["MUTATE", "NAVIGATE", "RETRIEVE"]
    assert payload["coverage"]["special_auth_task_ids"] == [759]
    validate_pilot_manifest(payload)


def test_pilot_manifest_rejects_route_mutation() -> None:
    payload = build_pilot_manifest()
    mutated = copy.deepcopy(payload)
    mutated["record_slots"][0]["server_id"] = "wrong-vps"
    core = dict(mutated)
    core.pop("integrity")
    from evidence_system.core.hashing import sha256_object

    mutated["record_slots_sha256"] = sha256_object(mutated["record_slots"])
    core = dict(mutated)
    core.pop("integrity")
    mutated["integrity"]["core_sha256"] = sha256_object(core)

    with pytest.raises(WebArenaFullScheduleError, match="route changed"):
        validate_pilot_manifest(mutated)
