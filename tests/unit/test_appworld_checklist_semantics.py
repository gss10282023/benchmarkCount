from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

import pytest
import evidence_system.contracts.appworld_stronger_gaps as stronger_gap_contract
import evidence_system.contracts.appworld_checklist_semantics as checklist_semantics_contract

from evidence_system.contracts.appworld_checklist_semantics import (
    APPWORLD_ALL_TESTS_MARKER,
    APPWORLD_UNDECIDED_RATIONALE,
    APPWORLD_UNDECIDED_TEXT,
    AppWorldChecklistSemanticError,
    TEST_TRACKER_SUCCESS_EXPRESSION,
    appworld_benchmark_success_text,
    appworld_registered_test_fail_text,
    appworld_registered_test_marker,
    appworld_registered_test_success_text,
    appworld_required_native_surface,
    validate_appworld_checklist_semantics,
    validate_appworld_packet_checklist_semantics,
)
from evidence_system.contracts.appworld_stronger_gaps import (
    AppWorldStrongerGapError,
    packet_stronger_gap_payload,
)
from evidence_system.core.hashing import sha256_object


CASE_ID = "0000000_1"
_TEST_GAP_ENTRIES: dict[str, dict[str, Any]] = {}
EVALUATION = '''from appworld.evaluator import TestTracker


def evaluate(test: TestTracker, public_data, private_data, main_user, models, ground_truth_answer):
    active_tasks = models.end.supervisor.Task.all()
    predicted_answer = active_tasks[0].answer
    test.task_completed = active_tasks[0].status == "success"
    with test("""
        assert answers match.
    """):
        test.answer(predicted_answer, ground_truth_answer)
    with test("""
        assert no model changes.
    """):
        changed_model_names = models.changed_model_names()
        test.case(changed_model_names, "==", set())
'''
TEST_DATA = [
    {"requirement": "assert no model changes.", "label": "no_op_pass"},
    {"requirement": "assert answers match.", "label": "no_op_fail"},
]
TEST_MARKERS = [
    appworld_registered_test_marker(index, item["requirement"])
    for index, item in enumerate(TEST_DATA, start=1)
]


@pytest.fixture(autouse=True)
def _bind_synthetic_packet_to_synthetic_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    def frozen_entry(case_unit_id: str) -> dict[str, Any]:
        return json.loads(json.dumps(_TEST_GAP_ENTRIES[case_unit_id]))

    monkeypatch.setattr(
        stronger_gap_contract,
        "frozen_stronger_gap_case_entry",
        frozen_entry,
    )
    _TEST_GAP_ENTRIES.clear()


def _checklist() -> dict[str, Any]:
    checklist = {
        "schema_version": "case_checklist_v1",
        "case_unit_id": CASE_ID,
        "domain": "appworld",
        "task_id": CASE_ID,
        "native": {
            "user_goal": {"text": "Return the requested answer.", "rationale": "fixture"},
            "benchmark_success": {
                "text": appworld_benchmark_success_text(TEST_MARKERS),
                "rationale": "fixture",
            },
            "checked_by": {"text": "The official evaluate function.", "rationale": "fixture"},
            "decisive_artifacts": [
                {
                    "artifact": "Official TestTracker result",
                    "question": "Did every registered official check pass?",
                    "support": ["official/ground_truth/evaluation.py::evaluate"],
                }
            ],
            "success_if": [
                {
                    "text": appworld_registered_test_success_text(
                        TEST_MARKERS[0], TEST_DATA[0]["requirement"]
                    ),
                    "rationale": "fixture",
                },
                {
                    "text": appworld_registered_test_success_text(
                        TEST_MARKERS[1], TEST_DATA[1]["requirement"]
                    ),
                    "rationale": "fixture",
                },
            ],
            "fail_if": [
                {
                    "text": appworld_registered_test_fail_text(
                        TEST_MARKERS[0], TEST_DATA[0]["requirement"]
                    ),
                    "rationale": "fixture",
                },
                {
                    "text": appworld_registered_test_fail_text(
                        TEST_MARKERS[1], TEST_DATA[1]["requirement"]
                    ),
                    "rationale": "fixture",
                },
            ],
            "undecided_if": [
                {
                    "text": APPWORLD_UNDECIDED_TEXT,
                    "rationale": APPWORLD_UNDECIDED_RATIONALE,
                }
            ],
        },
        "stronger": {"additional_conditions": []},
    }
    checklist["native"] = appworld_required_native_surface(
        instruction="Return the requested answer.",
        registered_tests=[
            {
                "marker": TEST_MARKERS[index],
                "required_success_if_text": appworld_registered_test_success_text(
                    TEST_MARKERS[index], item["requirement"]
                ),
                "required_fail_if_text": appworld_registered_test_fail_text(
                    TEST_MARKERS[index], item["requirement"]
                ),
            }
            for index, item in enumerate(TEST_DATA)
        ],
    )
    return checklist


def _packet(
    tmp_path: Path,
    *,
    evaluation: str = EVALUATION,
    test_data: list[dict[str, str]] | None = None,
) -> Path:
    root = tmp_path / CASE_ID
    ground_truth = root / "raw_case/official/ground_truth"
    ground_truth.mkdir(parents=True)
    evaluation_path = ground_truth / "evaluation.py"
    test_data_path = ground_truth / "test_data.json"
    specs_path = root / "raw_case/official/specs.json"
    evaluation_path.write_text(evaluation, encoding="utf-8")
    test_data_source = json.dumps(test_data or TEST_DATA, indent=2) + "\n"
    selected_test_data = test_data or TEST_DATA
    registry = {
        "all_tests_marker": APPWORLD_ALL_TESTS_MARKER,
        "required_benchmark_success_text": appworld_benchmark_success_text(
            [
                appworld_registered_test_marker(index, item["requirement"])
                for index, item in enumerate(selected_test_data, start=1)
            ]
        ),
        "required_undecided_if_text": APPWORLD_UNDECIDED_TEXT,
        "required_undecided_if_rationale": APPWORLD_UNDECIDED_RATIONALE,
        "registered_tests": [
            {
                "index": index,
                "marker": appworld_registered_test_marker(index, item["requirement"]),
                "requirement": item["requirement"],
                "requirement_sha256": hashlib.sha256(
                    " ".join(item["requirement"].split()).encode("utf-8")
                ).hexdigest(),
                "required_success_if_text": appworld_registered_test_success_text(
                    appworld_registered_test_marker(index, item["requirement"]),
                    item["requirement"],
                ),
                "required_fail_if_text": appworld_registered_test_fail_text(
                    appworld_registered_test_marker(index, item["requirement"]),
                    item["requirement"],
                ),
            }
            for index, item in enumerate(selected_test_data, start=1)
        ],
    }
    registry["required_native"] = appworld_required_native_surface(
        instruction="Return the requested answer.",
        registered_tests=registry["registered_tests"],
    )
    gap_entry = {
        "case_unit_id": CASE_ID,
        "split": "test_normal",
        "source_ref": f"appworld://test_normal/{CASE_ID}",
        "source_basis_sha256": "0" * 64,
        "registered_test_registry_sha256": sha256_object(registry),
        "non_scoring_assignment_registry": [
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
        ],
        "non_scoring_assignment_exclusion_status": (
            "excluded_from_native_and_stronger_scoring"
        ),
        "review_status": "reviewed_no_gap",
        "gaps": [],
    }
    gap_entry["non_scoring_assignment_registry_sha256"] = sha256_object(
        gap_entry["non_scoring_assignment_registry"]
    )
    gap_entry["entry_semantic_sha256"] = sha256_object(gap_entry)
    _TEST_GAP_ENTRIES[CASE_ID] = json.loads(json.dumps(gap_entry))
    gap_payload = packet_stronger_gap_payload(gap_entry)
    test_data_path.write_text(test_data_source, encoding="utf-8")
    specs_source = json.dumps({"instruction": "Return the requested answer."}, indent=2) + "\n"
    specs_path.write_text(specs_source, encoding="utf-8")
    packet = (
        "# Case Packet\n\n"
        "## Case Metadata\n\n"
        "- domain: `appworld`\n"
        f"- case_unit_id: `{CASE_ID}`\n"
        f"- task_id: `{CASE_ID}`\n\n"
        "## Source Inventory\n\n"
        "- `official/ground_truth/evaluation.py`\n"
        "- `official/ground_truth/test_data.json`\n\n"
        "- `official/specs.json`\n\n"
        "### Machine-verifiable registered-test registry\n\n"
        f"```json\n{json.dumps(registry, indent=2)}\n```\n\n"
        "### Machine-verifiable stronger-gap registry\n\n"
        f"```json\n{json.dumps(gap_payload, indent=2)}\n```\n\n"
        "## Packet Source Files\n\n"
        "### `official/ground_truth/evaluation.py`\n\n"
        f"Source ref: `appworld://test_normal/{CASE_ID}#ground_truth/evaluation.py`\n\n"
        f"```python\n{evaluation}```\n\n"
        "### `official/ground_truth/test_data.json`\n\n"
        f"Source ref: `appworld://test_normal/{CASE_ID}#ground_truth/test_data.json`\n\n"
        f"```json\n{test_data_source}```\n\n"
        "### `official/specs.json`\n\n"
        f"Source ref: `appworld://test_normal/{CASE_ID}#specs.json`\n\n"
        f"```json\n{specs_source}```\n"
    )
    (root / "case_packet.md").write_text(packet, encoding="utf-8")
    return root


def test_valid_canary_extracts_registered_checks_and_source_expressions(tmp_path: Path) -> None:
    root = _packet(tmp_path)

    report = validate_appworld_packet_checklist_semantics(
        case_packet_root=root,
        checklist=_checklist(),
    )

    assert report["status"] == "passed"
    assert report["test_tracker_success"]["expression"] == TEST_TRACKER_SUCCESS_EXPRESSION
    assert report["scoring_block_count"] == 2
    assert report["scoring_call_count"] == 2
    assert report["scoring_methods"] == ["answer", "case"]
    assert report["non_scoring_test_assignments"] == [
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
    case_call = next(call for call in report["scoring_calls"] if call["method"] == "case")
    assert any(
        source["expression"] == "models.changed_model_names()"
        for source in case_call["source_expressions"]
    )
    assert "changed_model_names" in report["scored_source_attributes"]
    assert "status" not in report["scored_source_attributes"]


# These are the eight distinct bad benchmark-success phrasings in the stopped
# GPT-5.6 diagnostic run.  The ninth promoted draft (afc4005_2) uses the valid
# two-check composition represented by _checklist() above.
@pytest.mark.parametrize(
    "bad_text",
    [
        "The first supervisor task has status `success`; its answer matches; and no "
        "models changed.",
        "The supervisor task is marked successful, the answer matches, and no models changed.",
        "The first active task is marked successful, its answer matches, and no models changed.",
        'The first active task is marked successful, its answer matches "21257.8", and no '
        "models changed.",
        "The first active supervisor task has status success, its answer matches, and no "
        "models changed.",
        "The first active supervisor task is marked successful, its answer matches, and no "
        "models changed.",
        'Native success requires the supervisor task status to be "success", its answer to '
        "match, and no models changed.",
        "All three evaluator components hold: the task status is success, the answer matches, "
        "and no models changed.",
    ],
)
def test_rejects_all_observed_status_as_native_success_phrasings(
    tmp_path: Path,
    bad_text: str,
) -> None:
    root = _packet(tmp_path)
    checklist = _checklist()
    checklist["native"]["benchmark_success"]["text"] = (
        f"{bad_text} {APPWORLD_ALL_TESTS_MARKER}: all {TEST_MARKERS[0]} and "
        f"{TEST_MARKERS[1]} pass."
    )

    with pytest.raises(
        AppWorldChecklistSemanticError,
        match=r"native\.benchmark_success\.text must exactly equal",
    ):
        validate_appworld_packet_checklist_semantics(
            case_packet_root=root,
            checklist=checklist,
        )


@pytest.mark.parametrize(
    "bad_text",
    [
        "Native success requires the supervisor task to be successful and both registered checks to pass.",
        "The task must succeed and both registered checks must pass.",
        "Final supervisor task record shows a successful outcome.",
        "Task status is not scored, but native success still requires the supervisor task status to be success.",
        "Although task_completed is unscored, native success requires task_completed to be true.",
    ],
)
def test_rejects_paraphrase_and_disclaimer_bypasses(
    tmp_path: Path,
    bad_text: str,
) -> None:
    root = _packet(tmp_path)
    checklist = _checklist()
    checklist["native"]["benchmark_success"]["text"] = (
        f"{bad_text} {APPWORLD_ALL_TESTS_MARKER}: all {TEST_MARKERS[0]} and "
        f"{TEST_MARKERS[1]} pass."
    )

    with pytest.raises(
        AppWorldChecklistSemanticError,
        match=r"native\.benchmark_success\.text must exactly equal",
    ):
        validate_appworld_packet_checklist_semantics(
            case_packet_root=root,
            checklist=checklist,
        )


@pytest.mark.parametrize(
    "text",
    [
        "The task asks to complete missing log data, but the evaluator ignores row order.",
    ],
)
def test_non_scoring_heuristic_allows_task_intent_completion_prose(text: str) -> None:
    assignment = {
        "attribute": "task_completed",
        "semantic_atoms": {
            "attributes": ["status"],
            "names": ["active_tasks"],
            "constants": ["0", "success"],
        },
    }

    assert not checklist_semantics_contract._text_requires_non_scoring_assignment(
        text,
        assignment,
        scored_attributes=set(),
    )


@pytest.mark.parametrize(
    "text",
    [
        "The supervisor task must be completed.",
        "Native success requires completing the supervisor task.",
        "The task must succeed.",
    ],
)
def test_non_scoring_heuristic_rejects_task_status_completion_predicates(text: str) -> None:
    assignment = {
        "attribute": "task_completed",
        "semantic_atoms": {
            "attributes": ["status"],
            "names": ["active_tasks"],
            "constants": ["0", "success"],
        },
    }

    assert checklist_semantics_contract._text_requires_non_scoring_assignment(
        text,
        assignment,
        scored_attributes=set(),
    )


def test_rejects_omitted_registered_scoring_block(tmp_path: Path) -> None:
    root = _packet(tmp_path)
    checklist = _checklist()
    checklist["native"]["benchmark_success"]["text"] = (
        f"{APPWORLD_ALL_TESTS_MARKER}: all {TEST_MARKERS[0]} pass."
    )
    checklist["native"]["success_if"] = [
        {"text": f"{TEST_MARKERS[0]} passes.", "rationale": "incomplete"}
    ]
    checklist["native"]["fail_if"] = [
        {"text": f"{TEST_MARKERS[0]} fails.", "rationale": "incomplete"}
    ]

    with pytest.raises(AppWorldChecklistSemanticError, match="must occur exactly once"):
        validate_appworld_packet_checklist_semantics(
            case_packet_root=root,
            checklist=checklist,
        )


@pytest.mark.parametrize(
    ("field", "text"),
    [
        (
            "benchmark_success",
            f"{APPWORLD_ALL_TESTS_MARKER}: all {TEST_MARKERS[0]} and "
            f"{TEST_MARKERS[1]} do not pass.",
        ),
        ("success_if", f"{TEST_MARKERS[0]} does not pass."),
        ("fail_if", f"{TEST_MARKERS[0]} does not fail."),
    ],
)
def test_rejects_inverted_registered_test_polarity(
    tmp_path: Path,
    field: str,
    text: str,
) -> None:
    root = _packet(tmp_path)
    checklist = _checklist()
    if field == "benchmark_success":
        checklist["native"][field]["text"] = text
    else:
        checklist["native"][field][0]["text"] = text

    with pytest.raises(AppWorldChecklistSemanticError):
        validate_appworld_packet_checklist_semantics(
            case_packet_root=root,
            checklist=checklist,
        )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda checklist: checklist["native"]["benchmark_success"].__setitem__(
            "text",
            checklist["native"]["benchmark_success"]["text"]
            + " [appworld_test_999_DEADBEEFDEAD] passes.",
        ),
        lambda checklist: checklist["native"]["fail_if"].append(
            {"text": f"{APPWORLD_ALL_TESTS_MARKER} fails.", "rationale": "bad"}
        ),
        lambda checklist: checklist["native"]["undecided_if"].append(
            {"text": f"{TEST_MARKERS[0]} is unavailable.", "rationale": "bad"}
        ),
    ],
)
def test_rejects_unknown_or_out_of_surface_markers(
    tmp_path: Path,
    mutate: Any,
) -> None:
    root = _packet(tmp_path)
    checklist = _checklist()
    mutate(checklist)

    with pytest.raises(AppWorldChecklistSemanticError):
        validate_appworld_packet_checklist_semantics(
            case_packet_root=root,
            checklist=checklist,
        )


@pytest.mark.parametrize("field", ["success_if", "fail_if"])
def test_requires_polarity_to_be_bound_to_each_marker(
    tmp_path: Path,
    field: str,
) -> None:
    root = _packet(tmp_path)
    checklist = _checklist()
    verb = "passes" if field == "success_if" else "fails"
    checklist["native"][field] = [
        {
            "text": f"{TEST_MARKERS[0]} {verb}; {TEST_MARKERS[1]} is unavailable.",
            "rationale": "bad",
        }
    ]

    with pytest.raises(
        AppWorldChecklistSemanticError,
        match="must contain exactly one item per frozen AppWorld registered test",
    ):
        validate_appworld_packet_checklist_semantics(
            case_packet_root=root,
            checklist=checklist,
        )


def test_rejects_non_scoring_predicate_in_undecided_surface(tmp_path: Path) -> None:
    root = _packet(tmp_path)
    checklist = _checklist()
    checklist["native"]["undecided_if"] = [
        {
            "text": "Undecided unless the supervisor task is completed successfully.",
            "rationale": "bad",
        }
    ]

    with pytest.raises(AppWorldChecklistSemanticError, match=r"native\.undecided_if\[0\]"):
        validate_appworld_packet_checklist_semantics(
            case_packet_root=root,
            checklist=checklist,
        )


@pytest.mark.parametrize(
    ("mutate", "expected_field"),
    [
        (
            lambda checklist: checklist["native"]["decisive_artifacts"].append(
                {
                    "artifact": "Final supervisor task record",
                    "question": "Is its task status success?",
                    "support": ["official/ground_truth/evaluation.py::evaluate"],
                }
            ),
            r"checklist\.native must exactly equal",
        ),
    ],
)
def test_rejects_non_scoring_predicate_in_each_native_condition_surface(
    tmp_path: Path,
    mutate: Any,
    expected_field: str,
) -> None:
    root = _packet(tmp_path)
    checklist = _checklist()
    mutate(checklist)

    with pytest.raises(AppWorldChecklistSemanticError, match=expected_field):
        validate_appworld_packet_checklist_semantics(
            case_packet_root=root,
            checklist=checklist,
        )


def test_rejects_dynamic_task_status_added_to_stronger_without_frozen_gap(
    tmp_path: Path,
) -> None:
    root = _packet(tmp_path)
    checklist = _checklist()
    checklist["stronger"]["additional_conditions"] = [
        {
            "id": "stronger_completion",
            "text": "The supervisor task status is success.",
            "rationale": "This is intentionally stronger than native AppWorld scoring.",
            "decisive_artifacts": [
                {
                    "artifact": "Supervisor task record",
                    "question": "Is status success?",
                    "support": ["official/ground_truth/evaluation.py::evaluate"],
                }
            ],
            "support": ["official/ground_truth/evaluation.py::evaluate"],
        }
    ]

    with pytest.raises(
        AppWorldStrongerGapError,
        match=r"stronger\.additional_conditions must exactly equal",
    ):
        validate_appworld_packet_checklist_semantics(
            case_packet_root=root,
            checklist=checklist,
        )


def test_allows_scored_is_completed_field_without_conflating_task_completed(
    tmp_path: Path,
) -> None:
    requirement = "assert all updated tasks have changed only in is_completed field."
    evaluation = EVALUATION.replace("assert no model changes.", requirement)
    test_data = [
        {"requirement": requirement, "label": "no_op_pass"},
        TEST_DATA[1],
    ]
    root = _packet(tmp_path, evaluation=evaluation, test_data=test_data)
    checklist = _checklist()
    markers = [
        appworld_registered_test_marker(index, item["requirement"])
        for index, item in enumerate(test_data, start=1)
    ]
    checklist["native"]["benchmark_success"]["text"] = (
        appworld_benchmark_success_text(markers)
    )
    checklist["native"]["success_if"][0]["text"] = (
        appworld_registered_test_success_text(markers[0], requirement)
    )
    checklist["native"]["fail_if"][0]["text"] = (
        appworld_registered_test_fail_text(markers[0], requirement)
    )

    report = validate_appworld_packet_checklist_semantics(
        case_packet_root=root,
        checklist=checklist,
    )

    assert report["status"] == "passed"
    assert report["non_scoring_native_requirement_count"] == 0


def test_rejects_scoring_call_outside_with_test(tmp_path: Path) -> None:
    evaluation = EVALUATION.replace(
        '    with test("""\n        assert answers match.\n    """):\n        '
        "test.answer(predicted_answer, ground_truth_answer)\n",
        "    test.answer(predicted_answer, ground_truth_answer)\n",
    )
    root = _packet(tmp_path, evaluation=evaluation)

    with pytest.raises(AppWorldChecklistSemanticError, match="outside with test"):
        validate_appworld_packet_checklist_semantics(
            case_packet_root=root,
            checklist=_checklist(),
        )


def test_rejects_packet_raw_evaluator_mismatch(tmp_path: Path) -> None:
    root = _packet(tmp_path)
    evaluation_path = root / "raw_case/official/ground_truth/evaluation.py"
    evaluation_path.write_text(EVALUATION + "# drift\n", encoding="utf-8")

    with pytest.raises(AppWorldChecklistSemanticError, match="differs from raw official bytes"):
        validate_appworld_checklist_semantics(
            case_packet_path=root / "case_packet.md",
            evaluation_path=evaluation_path,
            test_data_path=root / "raw_case/official/ground_truth/test_data.json",
            checklist=_checklist(),
        )


def test_rejects_test_data_requirement_drift(tmp_path: Path) -> None:
    root = _packet(
        tmp_path,
        test_data=[
            {"requirement": "assert answers match.", "label": "no_op_fail"},
            {"requirement": "different requirement", "label": "no_op_pass"},
        ],
    )

    with pytest.raises(AppWorldChecklistSemanticError, match="do not match test_data.json"):
        validate_appworld_packet_checklist_semantics(
            case_packet_root=root,
            checklist=_checklist(),
        )
