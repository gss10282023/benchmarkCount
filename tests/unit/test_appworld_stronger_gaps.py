from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import evidence_system.contracts.appworld_stronger_gaps as contract
from evidence_system.contracts.appworld_stronger_gaps import (
    AppWorldStrongerGapError,
    appworld_stronger_gap_marker,
    appworld_gap_basis,
    packet_stronger_gap_payload,
    parse_packet_stronger_gap_registry,
    validate_condition_without_marker,
)
from evidence_system.core.hashing import sha256_object


def _condition(text: str = "The selected task completion must be retained.") -> dict[str, Any]:
    return {
        "id": "task_intent_gap",
        "text": text,
        "rationale": "The explicit user instruction is stricter than the native evaluator.",
        "decisive_artifacts": [
            {
                "artifact": "Retained final record",
                "question": "Does the retained record satisfy the explicit instruction?",
                "support": [
                    "official/specs.json::$.instruction",
                    "official/ground_truth/evaluation.py::evaluate",
                ],
            }
        ],
        "support": [
            "official/specs.json::$.instruction",
            "official/ground_truth/evaluation.py::evaluate",
        ],
    }


@pytest.mark.parametrize(
    "text",
    [
        "test.task_completed must be true.",
        "test task\tcompleted must be true.",
        "test task\ncompleted must be true.",
        "test task\u200bcompleted must be true.",
        "active‐tasks[0].status must be success.",
        "The task status must be success.",
    ],
)
def test_policy_condition_rejects_non_scoring_dynamic_aliases(text: str) -> None:
    with pytest.raises(AppWorldStrongerGapError, match="non-scoring"):
        validate_condition_without_marker(_condition(text), index=1)


def test_policy_condition_does_not_reject_task_intent_completion_word() -> None:
    assert validate_condition_without_marker(_condition(), index=1) == _condition()


@pytest.mark.parametrize("support", [[], [123], ["x", "x"]])
def test_policy_condition_support_must_be_nonempty_unique_strings(
    support: list[Any],
) -> None:
    condition = _condition()
    condition["support"] = support
    with pytest.raises(AppWorldStrongerGapError, match="non-empty unique string array"):
        validate_condition_without_marker(condition, index=1)


def _entry(text: str) -> dict[str, Any]:
    condition = _condition(text)
    marker = appworld_stronger_gap_marker(1, condition)
    marked = dict(condition)
    marked["text"] = f"{marker} {condition['text']}"
    non_scoring = [
        {
            "attribute": "task_completed",
            "line": 7,
            "source_expression": "active_tasks[0].status == 'success'",
            "semantic_atoms": {
                "attributes": ["status"],
                "names": ["active_tasks"],
                "constants": ["0", "success"],
            },
        }
    ]
    non_scoring_sha256 = sha256_object(non_scoring)
    registered_sha256 = "1" * 64
    entry: dict[str, Any] = {
        "case_unit_id": "0000000_1",
        "split": "test_normal",
        "source_ref": "appworld://test_normal/0000000_1",
        "source_basis_sha256": "0" * 64,
        "registered_test_registry_sha256": registered_sha256,
        "non_scoring_assignment_registry": non_scoring,
        "non_scoring_assignment_registry_sha256": non_scoring_sha256,
        "non_scoring_assignment_exclusion_status": (
            "excluded_from_native_and_stronger_scoring"
        ),
        "review_status": "reviewed_gap",
        "gaps": [
            {
                "index": 1,
                "marker": marker,
                "condition_sha256": sha256_object(condition),
                "required_condition": marked,
                "gap_basis": appworld_gap_basis(
                    condition,
                    registered_test_registry_sha256=registered_sha256,
                    non_scoring_assignment_registry_sha256=non_scoring_sha256,
                ),
            }
        ],
    }
    entry["entry_semantic_sha256"] = sha256_object(entry)
    return entry


def _packet(entry: dict[str, Any]) -> str:
    payload = packet_stronger_gap_payload(entry)
    return (
        "### Machine-verifiable stronger-gap registry\n\n"
        f"```json\n{json.dumps(payload)}\n```\n"
    )


def test_packet_rejects_self_consistent_forgery_against_global_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical = _entry("The canonical task obligation must hold.")
    forged = _entry("The forged task obligation must hold.")
    monkeypatch.setattr(
        contract,
        "frozen_stronger_gap_case_entry",
        lambda _case_id: canonical,
    )

    with pytest.raises(AppWorldStrongerGapError, match="differs from the frozen global"):
        parse_packet_stronger_gap_registry(_packet(forged))


def test_packet_rejects_duplicate_machine_registry_sections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry = _entry("The canonical task obligation must hold.")
    monkeypatch.setattr(
        contract,
        "frozen_stronger_gap_case_entry",
        lambda _case_id: entry,
    )
    packet = _packet(entry)

    with pytest.raises(AppWorldStrongerGapError, match="one exact, unambiguous"):
        parse_packet_stronger_gap_registry(packet + "\n" + packet)


def test_current_policy_has_exact_explicit_485_case_disposition() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads(
        (root / "experiments/appworld_full_test_extension_v1/experiment_manifest.json").read_text()
    )
    policy = json.loads(
        (
            root
            / "experiments/appworld_full_test_extension_v1/official_splits/"
            "appworld_stronger_gap_review_policy.gpt56.v1.json"
        ).read_text()
    )
    manifest_ids = [item["case_unit_id"] for item in manifest["domains"][0]["case_units"]]
    gap_ids = [case_id for group in policy["groups"] for case_id in group["case_ids"]]
    no_gap_ids = policy["reviewed_no_gap_case_ids"]

    assert len(manifest_ids) == 485
    assert len(gap_ids) == len(set(gap_ids)) == 135
    assert len(no_gap_ids) == len(set(no_gap_ids)) == 350
    assert no_gap_ids == [case_id for case_id in manifest_ids if case_id not in gap_ids]
