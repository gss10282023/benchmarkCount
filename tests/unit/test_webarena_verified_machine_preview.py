from __future__ import annotations

import copy

import pytest

from evidence_system.core.hashing import sha256_object
from evidence_system.orchestrator.webarena_verified_full import WebArenaFullScheduleError
from evidence_system.orchestrator.webarena_verified_machine_preview import (
    PREVIEW_MODE,
    build_machine_preview,
    validate_machine_preview_index,
)


def test_machine_preview_proves_product_but_never_authorizes_launch() -> None:
    index, acceptance = build_machine_preview()

    assert index["mode"] == PREVIEW_MODE
    assert index["formal_launch_eligible"] is False
    assert index["executable"] is False
    assert len(index["record_slots"]) == 2436
    assert index["counts"]["per_agent"] == {
        "Agent A": 812,
        "Agent B": 812,
        "Agent C": 812,
    }
    assert index["counts"]["formally_executable_record_slots"] == 0
    assert index["counts"]["fallback_contracts"] == 0
    assert acceptance["gates"]["human_signoff_complete"] is False
    validate_machine_preview_index(index)


def test_machine_preview_rejects_executable_mutation() -> None:
    index, _ = build_machine_preview()
    mutated = copy.deepcopy(index)
    mutated["counts"]["formally_executable_record_slots"] = 1
    core = dict(mutated)
    core.pop("integrity")
    mutated["integrity"]["core_sha256"] = sha256_object(core)

    with pytest.raises(WebArenaFullScheduleError, match="executable/fallback"):
        validate_machine_preview_index(mutated)
