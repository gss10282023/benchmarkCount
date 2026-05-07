from __future__ import annotations

import pytest

from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.contracts.miniwob_case_selection import _default_manifest_id, _select_cases


def _candidate_pool(task_ids: list[str]) -> dict[str, object]:
    return {
        "items": [
            {
                "case_unit_id": task_id,
                "task_id": task_id,
                "selection_order_key": f"key-{index:03d}",
            }
            for index, task_id in enumerate(task_ids)
        ]
    }


def test_select_cases_supports_offset_window() -> None:
    candidate_pool = _candidate_pool(
        [
            "miniwob.task-3",
            "miniwob.task-1",
            "miniwob.task-4",
            "miniwob.task-2",
        ]
    )
    # The helper sorts by selection_order_key, not input order.
    first_window = _select_cases(candidate_pool, selected_count=2, selection_offset=0)
    second_window = _select_cases(candidate_pool, selected_count=2, selection_offset=2)

    assert [item.task_id for item in first_window] == ["miniwob.task-3", "miniwob.task-1"]
    assert [item.task_id for item in second_window] == ["miniwob.task-4", "miniwob.task-2"]
    assert {item.task_id for item in first_window}.isdisjoint({item.task_id for item in second_window})


def test_select_cases_rejects_invalid_windows() -> None:
    candidate_pool = _candidate_pool(["miniwob.task-1", "miniwob.task-2"])

    with pytest.raises(ContractLifecycleError, match="selected_count must be positive"):
        _select_cases(candidate_pool, selected_count=0, selection_offset=0)
    with pytest.raises(ContractLifecycleError, match="selection_offset must be non-negative"):
        _select_cases(candidate_pool, selected_count=1, selection_offset=-1)
    with pytest.raises(ContractLifecycleError, match="candidate pool too small"):
        _select_cases(candidate_pool, selected_count=2, selection_offset=1)


def test_default_manifest_id_uses_window_when_nondefault() -> None:
    assert _default_manifest_id(selected_count=50, selection_offset=0) == "miniwob-diagnostic-50-manifest"
    assert _default_manifest_id(selected_count=50, selection_offset=50) == "miniwob-diagnostic-window-051-100-manifest"
