from __future__ import annotations

import json
import hashlib
from collections import Counter
from pathlib import Path

import pytest

import evidence_system.contracts.case_packets as case_packets
from evidence_system.contracts.appworld_checklist_semantics import (
    APPWORLD_ALL_TESTS_MARKER,
    APPWORLD_UNDECIDED_RATIONALE,
    APPWORLD_UNDECIDED_TEXT,
    appworld_benchmark_success_text,
    appworld_packet_registered_test_registry,
    appworld_registered_test_fail_text,
    appworld_registered_test_marker,
    appworld_registered_test_success_text,
    appworld_required_native_surface,
    validate_appworld_packet_evaluator_semantics,
)
from evidence_system.contracts.case_packets import (
    APPWORLD_EVALUATOR_GIT_COMMIT,
    APPWORLD_EVALUATOR_SEMANTICS_PATH,
    APPWORLD_EVALUATOR_SEMANTICS_SHA256,
    APPWORLD_EVALUATOR_SOURCE_SHA256,
    load_frozen_appworld_evaluator_semantics,
    render_case_packet,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path


ROOT = Path(__file__).resolve().parents[2]
EXTENSION_ROOT = (
    ROOT / "experiments/appworld_full_test_extension_v1_gpt56_strict_v3_lockfix_v6"
)


def test_frozen_appworld_evaluator_semantics_is_source_and_hash_bound() -> None:
    path = resolve_repo_path(APPWORLD_EVALUATOR_SEMANTICS_PATH)
    payload = load_frozen_appworld_evaluator_semantics()

    assert sha256_file(path) == APPWORLD_EVALUATOR_SEMANTICS_SHA256
    assert payload["evaluator_source"] == {
        "git_commit": APPWORLD_EVALUATOR_GIT_COMMIT,
        "path": "src/appworld/evaluator.py",
        "repository_url": "https://github.com/StonyBrookNLP/appworld",
        "sha256": f"sha256:{APPWORLD_EVALUATOR_SOURCE_SHA256}",
        "url": (
            "https://github.com/StonyBrookNLP/appworld/blob/"
            f"{APPWORLD_EVALUATOR_GIT_COMMIT}/src/appworld/evaluator.py"
        ),
    }
    assert payload["test_tracker"]["success"] == "self.pass_count == self.num_tests"
    assert payload["test_tracker"]["to_dict_stats_only_false_fields"] == [
        "success",
        "difficulty",
        "num_tests",
        "passes",
        "failures",
    ]
    assert (
        "task_completed"
        not in payload["test_tracker"]["to_dict_stats_only_false_fields"]
    )


def test_appworld_packet_renders_mandatory_native_scoring_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw_case_dir = tmp_path / "raw_case"
    evaluation_path = raw_case_dir / "official" / "ground_truth" / "evaluation.py"
    evaluation_path.parent.mkdir(parents=True)
    evaluation_path.write_text(
        'test.task_completed = True\nwith test("answer"):\n    test.case(1, "==", 1)\n',
        encoding="utf-8",
    )
    test_data_path = evaluation_path.parent / "test_data.json"
    test_data_path.write_text(
        json.dumps([{"requirement": "answer", "label": "answer"}], indent=2) + "\n",
        encoding="utf-8",
    )
    specs_path = raw_case_dir / "official" / "specs.json"
    specs_path.write_text(
        json.dumps({"instruction": "Return the requested answer."}, indent=2) + "\n",
        encoding="utf-8",
    )
    case_id = "0000000_1"
    relative = "official/ground_truth/evaluation.py"
    test_data_relative = "official/ground_truth/test_data.json"
    specs_relative = "official/specs.json"
    manifest = {
        "case_unit_id": case_id,
        "dataset_name": "test_normal",
        "source_ref": f"appworld://test_normal/{case_id}",
        "packet_files": [relative, test_data_relative, specs_relative],
        "file_sources": {
            relative: f"appworld://test_normal/{case_id}#ground_truth/evaluation.py",
            test_data_relative: (
                f"appworld://test_normal/{case_id}#ground_truth/test_data.json"
            ),
            specs_relative: f"appworld://test_normal/{case_id}#specs.json",
        },
        "sha256_per_file": {
            relative: sha256_file(evaluation_path),
            test_data_relative: sha256_file(test_data_path),
            specs_relative: sha256_file(specs_path),
        },
    }

    def fake_gap_entry(**kwargs: str) -> dict[str, object]:
        non_scoring = [
            {
                "attribute": "task_completed",
                "line": 1,
                "source_expression": "True",
                "semantic_atoms": {
                    "attributes": [],
                    "names": [],
                    "constants": ["true"],
                },
            }
        ]
        entry: dict[str, object] = {
            **kwargs,
            "non_scoring_assignment_registry": non_scoring,
            "non_scoring_assignment_registry_sha256": sha256_object(non_scoring),
            "non_scoring_assignment_exclusion_status": (
                "excluded_from_native_and_stronger_scoring"
            ),
            "review_status": "reviewed_no_gap",
            "gaps": [],
        }
        entry["entry_semantic_sha256"] = sha256_object(entry)
        return entry

    monkeypatch.setattr(case_packets, "stronger_gap_case_entry", fake_gap_entry)

    packet = render_case_packet(
        domain="appworld",
        case_unit_id=case_id,
        task_id=case_id,
        raw_case_dir=raw_case_dir,
        raw_case_manifest=manifest,
    )

    assert "## Frozen AppWorld Native Scoring Semantics (Mandatory)" in packet
    assert APPWORLD_EVALUATOR_GIT_COMMIT in packet
    assert APPWORLD_EVALUATOR_SOURCE_SHA256 in packet
    assert APPWORLD_EVALUATOR_SEMANTICS_SHA256 in packet
    assert "`success` is exactly `self.pass_count == self.num_tests`" in packet
    assert (
        "Only a registered `with test(requirement):` context appends a pass or failure"
        in packet
    )
    assert "`to_dict(stats_only=False)` contains exactly these fields" in packet
    assert (
        '`test.task_completed = active_tasks[0].status == "success"` is a dynamic assignment only'
        in packet
    )
    assert (
        "do **not** add task status or `task_completed` as a separate native success condition"
        in packet
    )
    assert "### Machine-verifiable registered-test registry" in packet
    assert "### Machine-verifiable stronger-gap registry" in packet
    assert APPWORLD_ALL_TESTS_MARKER in packet
    assert appworld_registered_test_marker(1, "answer") in packet


def test_non_appworld_packet_does_not_receive_appworld_scoring_lock(
    tmp_path: Path,
) -> None:
    raw_case_dir = tmp_path / "raw_case"
    raw_case_dir.mkdir()

    packet = render_case_packet(
        domain="miniwob",
        case_unit_id="miniwob.example",
        task_id="miniwob.example",
        raw_case_dir=raw_case_dir,
        raw_case_manifest={"packet_files": [], "file_sources": {}},
    )

    assert "Frozen AppWorld Native Scoring Semantics" not in packet


def test_appworld_semantics_loader_fails_closed_on_file_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = load_frozen_appworld_evaluator_semantics()
    payload["test_tracker"]["success"] = (
        "self.task_completed and self.pass_count == self.num_tests"
    )
    drifted = tmp_path / "appworld_evaluator_semantics.json"
    drifted.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    monkeypatch.setattr(case_packets, "APPWORLD_EVALUATOR_SEMANTICS_PATH", drifted)

    with pytest.raises(ContractLifecycleError, match="semantics hash mismatch"):
        load_frozen_appworld_evaluator_semantics()


def test_all_485_extension_packets_carry_exact_semantics_lock() -> None:
    manifest = json.loads(
        (EXTENSION_ROOT / "experiment_manifest.json").read_text(encoding="utf-8")
    )
    bundle = json.loads(
        (EXTENSION_ROOT / "source_bundles/case_packet_source_bundle.json").read_text(
            encoding="utf-8"
        )
    )
    cases = manifest["domains"][0]["case_units"]
    sources = {source["case_unit_id"]: source for source in bundle["sources"]}
    markers = (
        "## Frozen AppWorld Native Scoring Semantics (Mandatory)",
        APPWORLD_EVALUATOR_GIT_COMMIT,
        APPWORLD_EVALUATOR_SOURCE_SHA256,
        APPWORLD_EVALUATOR_SEMANTICS_SHA256,
        "`success` is exactly `self.pass_count == self.num_tests`",
        "Only a registered `with test(requirement):` context appends a pass or failure",
        "`to_dict(stats_only=False)` contains exactly these fields",
        '`test.task_completed = active_tasks[0].status == "success"` is a dynamic assignment only',
        "do **not** add task status or `task_completed` as a separate native success condition",
    )

    assert len(cases) == len(sources) == 485
    assert Counter(case["dataset_name"] for case in cases) == {
        "test_normal": 68,
        "test_challenge": 417,
    }
    registered_test_count = 0
    non_scoring_task_completed_count = 0
    for case in cases:
        task_id = case["task_id"]
        case_dir = EXTENSION_ROOT / "case_packets/appworld" / task_id
        packet_path = case_dir / "case_packet.md"
        packet = packet_path.read_text(encoding="utf-8")
        raw_manifest = json.loads(
            (case_dir / "raw_case_manifest.json").read_text(encoding="utf-8")
        )
        assert all(packet.count(marker) == 1 for marker in markers), task_id
        test_data = json.loads(
            (
                case_dir
                / "raw_case/official/ground_truth/test_data.json"
            ).read_text(encoding="utf-8")
        )
        registered_tests = []
        for index, item in enumerate(test_data, start=1):
            requirement = item["requirement"]
            normalized = " ".join(requirement.split())
            marker = appworld_registered_test_marker(index, requirement)
            registered_tests.append(
                {
                    "index": index,
                    "marker": marker,
                    "requirement": requirement,
                    "requirement_sha256": hashlib.sha256(
                        normalized.encode("utf-8")
                    ).hexdigest(),
                    "required_success_if_text": appworld_registered_test_success_text(
                        marker, requirement
                    ),
                    "required_fail_if_text": appworld_registered_test_fail_text(
                        marker, requirement
                    ),
                }
            )
        specs = json.loads(
            (case_dir / "raw_case/official/specs.json").read_text(encoding="utf-8")
        )
        assert appworld_packet_registered_test_registry(packet) == {
            "all_tests_marker": APPWORLD_ALL_TESTS_MARKER,
            "required_benchmark_success_text": appworld_benchmark_success_text(
                [item["marker"] for item in registered_tests]
            ),
            "required_undecided_if_text": APPWORLD_UNDECIDED_TEXT,
            "required_undecided_if_rationale": APPWORLD_UNDECIDED_RATIONALE,
            "registered_tests": registered_tests,
            "required_native": appworld_required_native_surface(
                instruction=specs["instruction"],
                registered_tests=registered_tests,
            ),
        }, task_id
        evaluator_audit = validate_appworld_packet_evaluator_semantics(
            case_packet_root=case_dir
        )
        assert evaluator_audit["scoring_block_count"] == len(registered_tests), task_id
        assert evaluator_audit["test_data_requirement_count"] == len(
            registered_tests
        ), task_id
        assert [
            item["attribute"]
            for item in evaluator_audit["non_scoring_test_assignments"]
        ] == ["task_completed"], task_id
        registered_test_count += len(registered_tests)
        non_scoring_task_completed_count += len(
            evaluator_audit["non_scoring_test_assignments"]
        )
        assert (
            len(raw_manifest["official_files"])
            == len(raw_manifest["copied_files"])
            == 19
        )
        assert sources[task_id]["draft_input"]["case_packet_sha256"] == sha256_file(
            packet_path
        )
    assert registered_test_count == 3817
    assert non_scoring_task_completed_count == 485
