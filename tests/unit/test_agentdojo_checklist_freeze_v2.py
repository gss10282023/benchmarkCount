from __future__ import annotations

from collections.abc import Iterator, Mapping
from concurrent.futures import ThreadPoolExecutor
import copy
import json
from pathlib import Path
import threading
from typing import Any

import pytest

from evidence_system.contracts import agentdojo_checklist_freeze_v2 as freeze
from evidence_system.contracts import agentdojo_full_experiment as freeze_v1
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_file, sha256_object, sha256_path
from evidence_system.cli import freeze_agentdojo_full_checklists_v2 as freeze_cli


ZERO = "0" * 64


def _binding(name: str) -> dict[str, str]:
    return {"path": f"synthetic/{name}", "sha256": ZERO}


def _definition() -> dict[str, Any]:
    prompt_schema = {name: _binding(name) for name in freeze._PROMPT_SCHEMA_PREFIXES}
    case_bindings: list[dict[str, Any]] = []
    position = 0
    for suite, count in freeze_v1.EXPECTED_SUITE_COUNTS.items():
        for suite_position in range(count):
            case_id = (
                f"v1.2.2:{suite}:user_task_{suite_position}:"
                f"injection_task_{suite_position}"
            )
            receipts = {
                "review_receipt_sha256": ZERO,
                "review_lifecycle_receipt_sha256": ZERO,
                "review_lifecycle_object_sha256": ZERO,
                "active_review_tree_sha256": ZERO,
                "review_rounds": [
                    {
                        "round": 1,
                        "decision": "accept",
                        "attempt_receipt_sha256": ZERO,
                        "input_checklist_sha256": ZERO,
                        "review_prompt_sha256": ZERO,
                        "model_review_sha256": ZERO,
                        "revision_checklist_sha256": None,
                        "artifact_hashes": {
                            "round_01.model_review.json": ZERO,
                        },
                        "artifact_hashes_sha256": sha256_object(
                            {"round_01.model_review.json": ZERO}
                        ),
                    }
                ],
                "stale_review_runs": [],
            }
            case_bindings.append(
                {
                    "position": position,
                    "case_unit_id": case_id,
                    "task_id": f"{suite}_task_{suite_position}",
                    "suite": suite,
                    "case_packet": _binding(f"{position}/case_packet.md"),
                    "raw_case_manifest": _binding(f"{position}/raw_case_manifest.json"),
                    "generated_checklist": _binding(
                        f"{position}/generated_checklist.yaml"
                    ),
                    "generation_receipt": _binding(f"{position}/generation.json"),
                    "final_checklist": _binding(f"{position}/checklist.yaml"),
                    "final_checklist_json": _binding(f"{position}/checklist.json"),
                    "review_receipt": _binding(f"{position}/review.json"),
                    "review_lifecycle_receipt": _binding(
                        f"{position}/review_lifecycle.json"
                    ),
                    "prompt_schema_bindings": prompt_schema,
                    "prompt_schema_bindings_sha256": sha256_object(prompt_schema),
                    "review_revision_receipts": receipts,
                    "review_revision_receipts_sha256": sha256_object(receipts),
                    "batch_acceptance_case_sha256": ZERO,
                    "case_lock_entry_sha256": ZERO,
                    "case_lock_line_sha256": ZERO,
                }
            )
            position += 1
    case_ids = [entry["case_unit_id"] for entry in case_bindings]
    base = {
        "schema_version": freeze_v1.CHECKLIST_FREEZE_SCHEMA_VERSION,
        "expected_count": freeze_v1.EXPECTED_CASE_COUNT,
        "counts": {
            "case_packets": 949,
            "source_entries": 949,
            "valid_drafts": 949,
            "reviewed": 949,
            "locked": 949,
            "unresolved_drafts": 0,
        },
        "case_identity": {
            "case_id_order_sha256": sha256_object(case_ids),
            "case_id_set_sha256": sha256_object(sorted(case_ids)),
            "task_id_order_sha256": ZERO,
            "suite_case_counts": dict(freeze_v1.EXPECTED_SUITE_COUNTS),
        },
        "inputs": {"draft_root": {"tree_sha256": ZERO}},
    }
    definition = {
        "schema_version": freeze.CHECKLIST_FREEZE_V2_DEFINITION_SCHEMA_VERSION,
        "freeze_id": freeze.CHECKLIST_FREEZE_V2_ID,
        "status": "accepted_for_immutable_freeze",
        "benchmark_version": "v1.2.2",
        "attack": "direct",
        "defense": None,
        "expected_count": 949,
        "counts": dict(freeze._EXPECTED_COUNTS),
        "case_identity": dict(base["case_identity"]),
        "prompt_schema_bindings": prompt_schema,
        "prompt_schema_bindings_sha256": sha256_object(prompt_schema),
        "batch_lock": {**_binding("case_locks.jsonl"), "entry_count": 949},
        "batch_lock_acceptance": {
            **_binding("acceptance.json"),
            "accepted_case_count": 949,
        },
        "validated_v1_snapshot_sha256": sha256_object(base),
        "validated_v1_snapshot": base,
        "publisher_code_sha256": {path: ZERO for path in freeze._V2_CODE_PATHS},
        "review_quiescence_receipt": {
            "path": "synthetic/review_quiescence.json",
            "sha256": ZERO,
            "created_at": "2026-07-16T12:00:00+10:00",
            "capture_session_id": "0" * 32,
            "host_session": {
                "hostname": "synthetic-host",
                "boot_id": "synthetic-boot",
                "hostname_sha256": sha256_object("synthetic-host"),
                "boot_id_sha256": sha256_object("synthetic-boot"),
            },
            "draft_tree_sha256": ZERO,
        },
        "case_bindings": case_bindings,
        "aggregate_sha256": freeze._aggregate_hashes(case_bindings),
    }
    freeze._validate_definition(definition)
    return definition


@pytest.fixture(scope="module")
def valid_definition() -> dict[str, Any]:
    return _definition()


def _constant_builder(
    monkeypatch: pytest.MonkeyPatch, definition: dict[str, Any]
) -> None:
    monkeypatch.setattr(
        freeze,
        "build_checklist_freeze_v2_definition",
        lambda **_kwargs: copy.deepcopy(definition),
    )
    _stub_quiescence(monkeypatch, definition)


def _stub_quiescence(
    monkeypatch: pytest.MonkeyPatch, definition: dict[str, Any]
) -> None:
    monkeypatch.setattr(
        freeze,
        "verify_review_quiescence_receipt",
        lambda **_kwargs: copy.deepcopy(definition["review_quiescence_receipt"]),
    )


def test_v2_definition_requires_exact_949_and_all_aggregate_hashes(
    valid_definition: dict[str, Any],
) -> None:
    wrong_count = copy.deepcopy(valid_definition)
    wrong_count["counts"]["accepted_drafts"] = 948
    with pytest.raises(ContractLifecycleError, match="v2 freeze counts"):
        freeze._validate_definition(wrong_count)

    missing_case = copy.deepcopy(valid_definition)
    missing_case["case_bindings"].pop()
    missing_case["aggregate_sha256"] = freeze._aggregate_hashes(
        missing_case["case_bindings"]
    )
    with pytest.raises(ContractLifecycleError, match="exactly 949"):
        freeze._validate_definition(missing_case)

    stale_aggregate = copy.deepcopy(valid_definition)
    stale_aggregate["case_bindings"][0]["case_lock_entry_sha256"] = "1" * 64
    with pytest.raises(ContractLifecycleError, match="aggregate hashes"):
        freeze._validate_definition(stale_aggregate)


def test_publish_is_destination_absent_atomic_and_verify_recomputes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    valid_definition: dict[str, Any],
) -> None:
    _constant_builder(monkeypatch, valid_definition)
    output = tmp_path / "checklist_freeze.json"
    result = freeze.freeze_agentdojo_full_checklists_v2(
        output_path=output,
        frozen_at="2026-07-16T12:00:00+10:00",
    )
    assert result.freeze_path == output.resolve()
    assert result.freeze_sha256 == freeze.sha256_file(output)
    assert not freeze.checklist_freeze_v2_invalidation_path(output).exists()
    assert not list(tmp_path.glob(".checklist_freeze.json.*.tmp"))

    verified = freeze.verify_checklist_freeze_v2(freeze_path=output)
    assert verified.freeze_sha256 == result.freeze_sha256
    first_bytes = output.read_bytes()
    with pytest.raises(ContractLifecycleError, match="already exists"):
        freeze.freeze_agentdojo_full_checklists_v2(output_path=output)
    assert output.read_bytes() == first_bytes


def test_existing_destination_is_never_read_as_publishable_or_overwritten(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "checklist_freeze.json"
    output.write_bytes(b"sentinel\n")

    def should_not_build(**_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("builder must not run when destination exists")

    monkeypatch.setattr(
        freeze, "build_checklist_freeze_v2_definition", should_not_build
    )
    with pytest.raises(ContractLifecycleError, match="already exists"):
        freeze.freeze_agentdojo_full_checklists_v2(output_path=output)
    assert output.read_bytes() == b"sentinel\n"


def test_prepublication_drift_leaves_no_destination_or_invalidation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    valid_definition: dict[str, Any],
) -> None:
    changed = copy.deepcopy(valid_definition)
    changed["case_bindings"][0]["case_lock_entry_sha256"] = "1" * 64
    changed["aggregate_sha256"] = freeze._aggregate_hashes(changed["case_bindings"])
    values: Iterator[dict[str, Any]] = iter([valid_definition, changed])
    _stub_quiescence(monkeypatch, valid_definition)
    monkeypatch.setattr(
        freeze,
        "build_checklist_freeze_v2_definition",
        lambda **_kwargs: copy.deepcopy(next(values)),
    )
    output = tmp_path / "checklist_freeze.json"
    with pytest.raises(ContractLifecycleError, match="pre-publication"):
        freeze.freeze_agentdojo_full_checklists_v2(output_path=output)
    assert not output.exists()
    assert not freeze.checklist_freeze_v2_invalidation_path(output).exists()
    assert not list(tmp_path.glob(".*.tmp"))


def test_postpublication_drift_writes_non_sensitive_invalidation_and_gate_rejects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    valid_definition: dict[str, Any],
) -> None:
    changed = copy.deepcopy(valid_definition)
    changed["case_bindings"][0]["case_lock_entry_sha256"] = "1" * 64
    changed["aggregate_sha256"] = freeze._aggregate_hashes(changed["case_bindings"])
    values: Iterator[dict[str, Any]] = iter(
        [valid_definition, valid_definition, changed]
    )
    _stub_quiescence(monkeypatch, valid_definition)
    monkeypatch.setattr(
        freeze,
        "build_checklist_freeze_v2_definition",
        lambda **_kwargs: copy.deepcopy(next(values)),
    )
    output = tmp_path / "checklist_freeze.json"
    with pytest.raises(ContractLifecycleError, match="invalidated"):
        freeze.freeze_agentdojo_full_checklists_v2(
            output_path=output,
            frozen_at="2026-07-16T12:00:00+10:00",
        )
    invalidation = freeze.checklist_freeze_v2_invalidation_path(output)
    assert output.is_file()
    assert invalidation.is_file()
    receipt = json.loads(invalidation.read_text(encoding="utf-8"))
    assert set(receipt) == {
        "schema_version",
        "status",
        "reason_code",
        "detected_at",
        "freeze_path",
        "freeze_sha256",
        "expected_definition_sha256",
        "observed_definition_sha256",
    }
    assert receipt["reason_code"] == "post_publish_input_drift"
    assert "error" not in json.dumps(receipt).lower()
    monkeypatch.setattr(
        freeze,
        "build_checklist_freeze_v2_definition",
        lambda **_kwargs: copy.deepcopy(valid_definition),
    )
    with pytest.raises(ContractLifecycleError, match="invalidated"):
        freeze.verify_checklist_freeze_v2(freeze_path=output)


def test_concurrent_publishers_create_exactly_one_freeze_without_overwrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    valid_definition: dict[str, Any],
) -> None:
    _constant_builder(monkeypatch, valid_definition)
    output = tmp_path / "checklist_freeze.json"
    barrier = threading.Barrier(2)
    original = freeze._exclusive_publish_json

    def synchronized_publish(path: Path, payload: dict[str, Any]) -> str:
        if Path(path).name == output.name:
            barrier.wait(timeout=5)
        return original(path, payload)

    monkeypatch.setattr(freeze, "_exclusive_publish_json", synchronized_publish)

    def publish() -> tuple[str, str]:
        try:
            result = freeze.freeze_agentdojo_full_checklists_v2(
                output_path=output,
                frozen_at="2026-07-16T12:00:00+10:00",
            )
            return "ok", result.freeze_sha256
        except ContractLifecycleError as exc:
            return "error", str(exc)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _index: publish(), range(2)))
    assert [status for status, _ in results].count("ok") == 1
    assert [status for status, _ in results].count("error") == 1
    assert output.is_file()
    assert not freeze.checklist_freeze_v2_invalidation_path(output).exists()


def test_link_failure_has_zero_partial_publication_and_cleans_staging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    valid_definition: dict[str, Any],
) -> None:
    _constant_builder(monkeypatch, valid_definition)
    monkeypatch.setattr(
        freeze.os,
        "link",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("injected")),
    )
    output = tmp_path / "checklist_freeze.json"
    with pytest.raises(ContractLifecycleError, match="failed to publish"):
        freeze.freeze_agentdojo_full_checklists_v2(output_path=output)
    assert not output.exists()
    assert not freeze.checklist_freeze_v2_invalidation_path(output).exists()
    assert not list(tmp_path.glob(".*.tmp"))


def test_review_round_index_binds_revision_and_every_active_sidecar(
    tmp_path: Path,
) -> None:
    case_dir = tmp_path / "case"
    active = case_dir / "review_attempts" / "run-1"
    active.mkdir(parents=True)
    files = {
        "round_01.model_review.json": b"{}\n",
        "round_01.revised_checklist.yaml": b"schema_version: case_checklist_v1\n",
        "round_01.stdout.log": b"\n",
        "round_02.model_review.json": b"{}\n",
        "round_02.stderr.log": b"\n",
    }
    for name, content in files.items():
        (active / name).write_bytes(content)
    lifecycle = {
        "review_rounds": 2,
        "attempts": [
            {
                "round": 1,
                "decision": "revise",
                "input_checklist_sha256": ZERO,
                "review_prompt_sha256": ZERO,
                "model_review_sha256": ZERO,
            },
            {
                "round": 2,
                "decision": "accept",
                "input_checklist_sha256": ZERO,
                "review_prompt_sha256": ZERO,
                "model_review_sha256": ZERO,
            },
        ],
    }
    rounds, tree_hash, stale = freeze._review_round_bindings(
        case_unit_id="v1.2.2:workspace:user_task_0:injection_task_0",
        case_dir=case_dir,
        lifecycle=lifecycle,
        run_id="run-1",
    )
    assert rounds[0]["revision_checklist_sha256"] == freeze.sha256_file(
        active / "round_01.revised_checklist.yaml"
    )
    assert rounds[1]["revision_checklist_sha256"] is None
    assert set(rounds[0]["artifact_hashes"]) == {
        "round_01.model_review.json",
        "round_01.revised_checklist.yaml",
        "round_01.stdout.log",
    }
    assert tree_hash == freeze.sha256_path(active)
    assert stale == []


def test_full_tree_currentness_rejects_any_post_validation_drift(
    tmp_path: Path,
) -> None:
    tree = tmp_path / "drafts"
    tree.mkdir()
    artifact = tree / "checklist.yaml"
    artifact.write_text("locked\n", encoding="utf-8")
    runtime = tmp_path / "runtime.py"
    runtime.write_text("LOCKED = True\n", encoding="utf-8")
    result_root = tmp_path / "formal-results-absent"
    base = {
        "inputs": {
            "draft_root": {
                "path": str(tree),
                "tree_sha256": sha256_path(tree),
            }
        },
        "runtime_code_sha256": {str(runtime): sha256_file(runtime)},
        "formal_output_precondition": {
            "result_namespace": {
                "path": str(result_root),
                "exists": False,
                "allowed_marker_hashes": {},
                "formal_output_file_count": 0,
            },
            "score_namespaces": [],
            "formal_results_and_scores_are_empty": True,
        },
    }
    freeze._recheck_base_currentness(base)
    artifact.write_text("drift\n", encoding="utf-8")
    with pytest.raises(ContractLifecycleError, match="input tree draft_root"):
        freeze._recheck_base_currentness(base)


def test_review_preflight_rejects_model_accept_when_lifecycle_is_unresolved() -> None:
    model_review = {"decision": "accept", "blocking_findings": []}
    assert model_review["decision"] == "accept"
    lifecycle = {
        "schema_version": "case_checklist_review_lifecycle/v1",
        "case_unit_id": "v1.2.2:workspace:user_task_0:injection_task_0",
        "status": "unresolved",
        "revised": False,
        "review_rounds": 1,
        "attempts": [
            {
                "round": 1,
                "decision": "accept",
                "deterministic_review": {
                    "status": "fail",
                    "findings": [{"code": "blocking"}],
                },
            }
        ],
    }
    with pytest.raises(ContractLifecycleError, match="lifecycle.*status"):
        freeze._validate_preflight_lifecycle_acceptance(
            case_unit_id=lifecycle["case_unit_id"],
            lifecycle=lifecycle,
            final_checklist_sha256=ZERO,
            final_review_sha256=ZERO,
        )


def test_review_preflight_requires_revision_then_fresh_deterministic_accept() -> None:
    case_id = "v1.2.2:workspace:user_task_0:injection_task_0"
    lifecycle = {
        "schema_version": "case_checklist_review_lifecycle/v1",
        "case_unit_id": case_id,
        "status": "accepted",
        "revised": True,
        "review_rounds": 2,
        "final_checklist_sha256": ZERO,
        "final_review_sha256": ZERO,
        "attempts": [
            {
                "round": 1,
                "decision": "revise",
                "deterministic_review": {
                    "status": "fail",
                    "findings": [{"code": "blocking"}],
                },
            },
            {
                "round": 2,
                "decision": "accept",
                "deterministic_review": {"status": "pass", "findings": []},
            },
        ],
    }
    freeze._validate_preflight_lifecycle_acceptance(
        case_unit_id=case_id,
        lifecycle=lifecycle,
        final_checklist_sha256=ZERO,
        final_review_sha256=ZERO,
    )
    lifecycle["attempts"][1]["deterministic_review"] = {
        "status": "fail",
        "findings": [{"code": "still-blocking"}],
    }
    with pytest.raises(ContractLifecycleError, match="accepted deterministic"):
        freeze._validate_preflight_lifecycle_acceptance(
            case_unit_id=case_id,
            lifecycle=lifecycle,
            final_checklist_sha256=ZERO,
            final_review_sha256=ZERO,
        )


def test_cli_exposes_no_denominator_reduction_or_replacement_switch() -> None:
    parser = freeze_cli.build_parser()
    destinations = {action.dest for action in parser._actions}
    assert "expected_count" not in destinations
    assert "expected_suite_counts" not in destinations
    assert "replace_stale_lock" not in destinations
    assert "expected_previous_lock_sha256" not in destinations
    assert "post_lock_currentness_seal" in destinations
    assert "lifecycle_code_snapshot_root" in destinations
    assert "derive_per_case_review_run" in destinations
    assert "derive_review_attempt_state_machine" in destinations
    assert "derive_generation_attempt_state_machine" in destinations
    assert (
        freeze_cli.main(["--verify-only", "--frozen-at", "2026-07-16T00:00:00Z"]) == 2
    )
    assert freeze_cli.main(["--post-lock-currentness-seal"]) == 2
    assert (
        freeze_cli.main(["--capture-review-quiescence", "--post-lock-currentness-seal"])
        == 2
    )
    assert (
        freeze_cli.main(
            [
                "--preflight-review-currentness",
                "--lifecycle-code-snapshot-root",
                "/tmp/snapshot",
            ]
        )
        == 2
    )
    assert freeze_cli.main(["--derive-per-case-review-run"]) == 2
    assert freeze_cli.main(["--derive-review-attempt-state-machine"]) == 2
    assert freeze_cli.main(["--derive-generation-attempt-state-machine"]) == 2
    assert (
        freeze_cli.main(
            [
                "--verify-only",
                "--lifecycle-code-snapshot-root",
                "/tmp/snapshot",
                "--derive-per-case-review-run",
            ]
        )
        == 2
    )


def _review_attempt(
    *,
    round_index: int,
    returncode: int,
    decision: str | None = None,
    deterministic_pass: bool = True,
    error: str | None = None,
) -> dict[str, Any]:
    attempt: dict[str, Any] = {
        "round": round_index,
        "started_at": f"2026-07-16T00:0{round_index}:00+00:00",
        "finished_at": f"2026-07-16T00:0{round_index}:30+00:00",
        "returncode": returncode,
        "input_checklist_path": "/tmp/checklist.yaml",
        "input_checklist_sha256": ZERO,
        "review_prompt_path": "/tmp/review.prompt.md",
        "review_prompt_sha256": ZERO,
        "deterministic_review": (
            {"status": "pass", "findings": []}
            if deterministic_pass
            else {"status": "fail", "findings": [{"code": "blocking"}]}
        ),
    }
    if decision is not None:
        attempt.update(
            {
                "decision": decision,
                "model_review_path": "/tmp/model_review.json",
                "model_review_sha256": ZERO,
            }
        )
    if error is not None:
        attempt["error"] = error
    return attempt


def test_review_attempt_classifier_is_explicit_and_fail_closed() -> None:
    failed = _review_attempt(round_index=1, returncode=1, error="timeout")
    assert (
        freeze._classify_review_attempt(failed, context="failed") == "failed_call"
    )
    rejected = _review_attempt(
        round_index=1,
        returncode=0,
        decision="accept",
        deterministic_pass=False,
        error=freeze._DETERMINISTIC_REJECT_ERROR,
    )
    assert (
        freeze._classify_review_attempt(rejected, context="rejected")
        == "deterministically_rejected_accept"
    )
    assert (
        freeze._classify_review_attempt(
            _review_attempt(round_index=1, returncode=0, decision="revise"),
            context="revise",
        )
        == "successful_revise"
    )
    assert (
        freeze._classify_review_attempt(
            _review_attempt(round_index=1, returncode=0, decision="accept"),
            context="accept",
        )
        == "successful_accept"
    )

    failed["decision"] = "accept"
    with pytest.raises(ContractLifecycleError, match="failed-call fields"):
        freeze._classify_review_attempt(failed, context="tampered")
    malformed = _review_attempt(
        round_index=1, returncode=0, error="arbitrary schema failure"
    )
    with pytest.raises(ContractLifecycleError, match="rejected-attempt error"):
        freeze._classify_review_attempt(malformed, context="malformed")
    revision_error = _review_attempt(
        round_index=1, returncode=0, decision="revise"
    )
    revision_error["revision_validation_error"] = "invalid revision"
    with pytest.raises(ContractLifecycleError, match="unresolved revision"):
        freeze._classify_review_attempt(revision_error, context="revision")


def test_attempt_state_machine_compatibility_is_never_implicit() -> None:
    with pytest.raises(ContractLifecycleError, match="requires per-case review runs"):
        freeze._build_v1_snapshot(
            normalized={},
            lifecycle_code_snapshot_root=None,
            derive_review_attempt_state_machine=True,
        )
    with pytest.raises(ContractLifecycleError, match="requires review-attempt"):
        freeze._build_v1_snapshot(
            normalized={},
            lifecycle_code_snapshot_root=None,
            derive_per_case_review_run=True,
            derive_generation_attempt_state_machine=True,
        )


def test_review_attempt_binding_requires_unique_final_accept() -> None:
    attempt = {
        "round": 1,
        "outcome": "failed_call",
        "returncode": 1,
        "started_at": "2026-07-16T00:01:00+00:00",
        "finished_at": "2026-07-16T00:01:30+00:00",
        "attempt_receipt_sha256": ZERO,
        "input_checklist_sha256": ZERO,
        "review_prompt_sha256": ZERO,
        "model_review_sha256": None,
        "revision_checklist_sha256": None,
        "error_sha256": ZERO,
        "artifact_hashes": {"round_01.stderr.log": ZERO},
        "artifact_hashes_sha256": sha256_object(
            {"round_01.stderr.log": ZERO}
        ),
    }
    case_id = "v1.2.2:workspace:user_task_0:injection_task_0"
    entries = [
        freeze._review_attempt_state_machine_entry(
            case_unit_id=case_id, attempts=[attempt]
        )
    ]
    entries.extend(
        {
            **entries[0],
            "case_unit_id": (
                f"v1.2.2:workspace:user_task_{position}:injection_task_{position}"
            ),
        }
        for position in range(1, freeze_v1.EXPECTED_CASE_COUNT)
    )
    binding = freeze._review_attempt_state_machine_binding(entries)
    with pytest.raises(ContractLifecycleError, match="unique final accept"):
        freeze._validate_review_attempt_state_machine_binding(binding)


def test_locked_review_corpus_attempt_state_machine_regression() -> None:
    draft_root = freeze._absolute_path(freeze_v1.DEFAULT_DRAFT_ROOT)
    if not draft_root.is_dir():
        pytest.skip("locked AgentDojo full-review corpus is not present")
    lifecycle_paths = sorted(draft_root.glob("*/review_lifecycle.json"))
    assert len(lifecycle_paths) == freeze_v1.EXPECTED_CASE_COUNT

    entries: list[dict[str, Any]] = []
    failed_calls = 0
    deterministic_rejections = 0
    for lifecycle_path in lifecycle_paths:
        lifecycle = json.loads(lifecycle_path.read_text(encoding="utf-8"))
        case_unit_id = lifecycle["case_unit_id"]
        derived = freeze._derive_case_review_run(
            case_unit_id=case_unit_id,
            case_dir=lifecycle_path.parent,
            lifecycle=lifecycle,
        )
        active_root = lifecycle_path.parent / "review_attempts" / derived["actual_run_id"]
        attempts: list[dict[str, Any]] = []
        for position, raw_attempt in enumerate(lifecycle["attempts"], start=1):
            outcome = freeze._classify_review_attempt(
                raw_attempt,
                context=f"{case_unit_id} review attempt {position}",
            )
            attempts.append(
                freeze._review_attempt_binding(
                    case_unit_id=case_unit_id,
                    active_root=active_root,
                    attempt=raw_attempt,
                    position=position,
                    outcome=outcome,
                )
            )
            failed_calls += outcome == "failed_call"
            deterministic_rejections += (
                outcome == "deterministically_rejected_accept"
            )
        entries.append(
            freeze._review_attempt_state_machine_entry(
                case_unit_id=case_unit_id, attempts=attempts
            )
        )

    binding = freeze._review_attempt_state_machine_binding(entries)
    freeze._validate_review_attempt_state_machine_binding(binding)
    assert binding["accepted_cases"] == 949
    assert binding["rejected_intermediate_cases"] == 16
    assert binding["rejected_intermediate_attempts"] == 17
    assert binding["unresolved_cases"] == 0
    assert binding["total_attempts"] == 1188
    assert failed_calls == 15
    assert deterministic_rejections == 2


def test_locked_generation_corpus_retry_regression() -> None:
    draft_root = freeze._absolute_path(freeze_v1.DEFAULT_DRAFT_ROOT)
    batch_results = draft_root / "_batch_results.jsonl"
    if not batch_results.is_file():
        pytest.skip("locked AgentDojo generation corpus is not present")
    rows = [
        json.loads(line)
        for line in batch_results.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) == 949
    assert all(row.get("status") == "success" for row in rows)
    assert sum(len(row["attempts"]) for row in rows) == 951
    assert sum(len(row["attempts"]) > 1 for row in rows) == 2
    assert sum(
        attempt.get("returncode") != 0
        for row in rows
        for attempt in row["attempts"]
    ) == 2
    assert all(
        row["attempts"][-1].get("returncode") == 0
        and isinstance(row["attempts"][-1].get("validator"), str)
        for row in rows
    )


def test_active_run_revised_semantics_binding_is_explicit() -> None:
    case_id = "v1.2.2:banking:user_task_2:injection_task_3"
    binding = freeze._review_revised_semantics_binding(
        [
            {
                "case_unit_id": case_id,
                "lifecycle_revised": False,
                "generated_to_final_changed": True,
            }
        ]
    )
    assert binding["case_count"] == 1
    assert binding["entries"][0]["case_unit_id"] == case_id
    with pytest.raises(ContractLifecycleError, match="generated/final delta"):
        freeze._review_revised_semantics_binding(
            [
                {
                    "case_unit_id": case_id,
                    "lifecycle_revised": False,
                    "generated_to_final_changed": False,
                }
            ]
        )


def test_process_scanner_counts_only_target_reviewers_not_rg_or_scanner() -> None:
    process_table = "\n".join(
        [
            "101 1 /usr/bin/rg run_agentdojo_full_draft_review.py",
            "102 1 /bin/zsh -c grep review_case_checklist_with_codex.py files",
            "201 1 python run_agentdojo_full_draft_review.py --max-parallel 6",
            "202 201 python review_case_checklist_with_codex.py case_packet.md",
            "203 202 /usr/local/bin/codex exec --output-last-message round_01.model_review.json -",
        ]
    )
    snapshot = freeze._review_process_snapshot_from_text(process_table)
    assert snapshot["matched_by_policy"] == {
        "run_agentdojo_full_draft_review.py": 1,
        "review_case_checklist_with_codex.py": 1,
        "codex_exec_case_checklist_review": 1,
    }
    assert snapshot["matched_process_count"] == 3
    assert snapshot["command_pattern_sha256"] == freeze._REVIEW_COMMAND_PATTERN_SHA256
    sanitized = dict(snapshot)
    sanitized.pop("command_pattern_sha256")
    assert "command" not in json.dumps(sanitized).lower()


def _make_tree_writable(root: Path) -> None:
    for path in sorted([root, *root.rglob("*")], key=lambda item: len(item.parts)):
        path.chmod(path.stat().st_mode | 0o700)


def _minimal_post_lock_snapshot(
    *, drafts: Path, report: Path, index: Path, formal_root: Path
) -> dict[str, Any]:
    return {
        "schema_version": freeze_v1.CHECKLIST_FREEZE_SCHEMA_VERSION,
        "status": "accepted_for_final_freeze",
        "expected_count": 949,
        "counts": {
            "case_packets": 949,
            "source_entries": 949,
            "valid_drafts": 949,
            "reviewed": 949,
            "locked": 949,
            "unresolved_drafts": 0,
        },
        "case_identity": {
            "suite_case_counts": dict(freeze_v1.EXPECTED_SUITE_COUNTS),
        },
        "inputs": {
            "draft_root": {
                "path": str(drafts),
                "tree_sha256": sha256_path(drafts),
            },
            "draft_review_report": {
                "path": str(report),
                "sha256": sha256_file(report),
            },
            "draft_review_index": {
                "path": str(index),
                "sha256": sha256_file(index),
            },
        },
        "runtime_code_sha256": {},
        "formal_output_precondition": {
            "result_namespace": {
                "path": str(formal_root),
                "exists": False,
                "allowed_marker_hashes": {},
                "formal_output_file_count": 0,
            },
            "score_namespaces": [],
            "formal_results_and_scores_are_empty": True,
        },
    }


def test_post_lock_currentness_reuses_full_snapshot_twice_and_rejects_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = {
        "schema_version": freeze_v1.CHECKLIST_FREEZE_SCHEMA_VERSION,
        "expected_count": 949,
        "counts": {
            "case_packets": 949,
            "source_entries": 949,
            "valid_drafts": 949,
            "reviewed": 949,
            "locked": 949,
            "unresolved_drafts": 0,
        },
        "case_identity": {
            "suite_case_counts": dict(freeze_v1.EXPECTED_SUITE_COUNTS),
        },
    }
    calls: list[dict[str, Any]] = []

    def stable_builder(**kwargs: Any) -> dict[str, Any]:
        calls.append(dict(kwargs))
        return copy.deepcopy(base)

    monkeypatch.setattr(freeze_v1, "build_checklist_freeze_snapshot", stable_builder)
    monkeypatch.setattr(freeze, "_recheck_base_currentness", lambda _base: None)
    assert freeze.post_lock_agentdojo_full_review_currentness() == base
    assert len(calls) == 2
    assert all(call["expected_count"] == 949 for call in calls)
    assert all(call["require_empty_formal_outputs"] is True for call in calls)

    changed = copy.deepcopy(base)
    changed["case_identity"]["task_id_order_sha256"] = "1" * 64
    values: Iterator[dict[str, Any]] = iter([base, changed])
    monkeypatch.setattr(
        freeze_v1,
        "build_checklist_freeze_snapshot",
        lambda **_kwargs: copy.deepcopy(next(values)),
    )
    with pytest.raises(ContractLifecycleError, match="post-lock checklist inputs"):
        freeze.post_lock_agentdojo_full_review_currentness()


def test_sparse_lifecycle_snapshot_rewrites_only_in_memory_and_runtime_map(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "repository"
    current_root = repository / "code"
    current_root.mkdir(parents=True)
    snapshot_root = tmp_path / "snapshot"
    (snapshot_root / "code").mkdir(parents=True)
    locked_a = snapshot_root / "code/a.py"
    locked_a.write_text("locked-a\n", encoding="utf-8")
    current_a = current_root / "a.py"
    current_a.write_text("drifted-a\n", encoding="utf-8")
    current_b = current_root / "b.py"
    current_b.write_text("locked-b\n", encoding="utf-8")
    locks = [
        {"path": "code/a.py", "sha256": sha256_file(locked_a)},
        {"path": "code/b.py", "sha256": sha256_file(current_b)},
    ]
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"lifecycle_code": locks}) + "\n", encoding="utf-8")
    original_config_bytes = config.read_bytes()
    monkeypatch.setattr(freeze, "repo_root", lambda: repository)

    observed_paths: list[str] = []

    def original_validator(config_body: Mapping[str, Any], **_kwargs: Any) -> dict:
        raw_locks = config_body["lifecycle_code"]
        assert isinstance(raw_locks, list)
        observed_paths.extend(str(item["path"]) for item in raw_locks)
        return {}

    monkeypatch.setattr(freeze_v1, "_validate_draft_review_config", original_validator)

    def snapshot_builder(**_kwargs: Any) -> dict[str, Any]:
        config_body = json.loads(config.read_text(encoding="utf-8"))
        freeze_v1._validate_draft_review_config(config_body)
        return {
            "runtime_code_sha256": {
                "code/a.py": sha256_file(current_a),
                "code/b.py": sha256_file(current_b),
            }
        }

    monkeypatch.setattr(freeze_v1, "build_checklist_freeze_snapshot", snapshot_builder)
    result = freeze._build_v1_snapshot(
        normalized={"resolved_config_path": config},
        lifecycle_code_snapshot_root=snapshot_root,
    )
    assert config.read_bytes() == original_config_bytes
    assert freeze_v1._validate_draft_review_config is original_validator
    assert observed_paths == [str(locked_a), "code/b.py"]
    assert result["runtime_code_sha256"] == {
        str(locked_a): sha256_file(locked_a),
        "code/b.py": sha256_file(current_b),
    }
    binding = result["lifecycle_code_snapshot"]
    assert binding["root"]["tree_sha256"] == sha256_path(snapshot_root)
    assert [entry["source"] for entry in binding["files"]] == [
        "snapshot",
        "repository",
    ]

    monkeypatch.setattr(
        freeze_v1,
        "build_checklist_freeze_snapshot",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("injected")),
    )
    with pytest.raises(RuntimeError, match="injected"):
        freeze._build_v1_snapshot(
            normalized={"resolved_config_path": config},
            lifecycle_code_snapshot_root=snapshot_root,
        )
    assert freeze_v1._validate_draft_review_config is original_validator

    assert freeze._LIFECYCLE_CODE_CONTEXT_GUARD.acquire(blocking=False)
    try:
        with pytest.raises(ContractLifecycleError, match="already active"):
            with freeze._lifecycle_code_snapshot_validation_context(binding):
                pass
    finally:
        freeze._LIFECYCLE_CODE_CONTEXT_GUARD.release()


def test_derived_review_run_is_per_case_strict_and_guarded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case_id = "v1.2.2:workspace:user_task_33:injection_task_5"
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    (case_dir / "checklist.yaml").write_text("input\n", encoding="utf-8")
    run_id = "20260716T041905253251Z"
    active_root = case_dir / "review_attempts" / run_id
    active_root.mkdir(parents=True)
    round_one = active_root / "round_01.model_review.json"
    round_one.write_text("{}\n", encoding="utf-8")
    revision = active_root / "round_01.revised_checklist.yaml"
    revision.write_text("revised\n", encoding="utf-8")
    round_two = active_root / "round_02.model_review.json"
    round_two.write_text("{}\n", encoding="utf-8")
    lifecycle = {
        "case_unit_id": case_id,
        "status": "accepted",
        "review_rounds": 2,
        "attempts": [
            {
                "round": 1,
                "decision": "revise",
                "input_checklist_path": str(case_dir / "checklist.yaml"),
                "model_review_path": str(round_one),
            },
            {
                "round": 2,
                "decision": "accept",
                "input_checklist_path": str(revision),
                "model_review_path": str(round_two),
            },
        ],
    }
    expected = {
        "case_unit_id": case_id,
        "actual_run_id": run_id,
        "tree_sha256": sha256_path(active_root),
    }
    assert (
        freeze._derive_case_review_run(
            case_unit_id=case_id, case_dir=case_dir, lifecycle=lifecycle
        )
        == expected
    )

    class Case:
        case_unit_id = case_id

    observed_report_ids: list[str] = []

    def original_review_validator(**kwargs: Any) -> dict[str, str]:
        observed_report_ids.append(str(kwargs["report_run_id"]))
        return {
            "case_unit_id": case_id,
            "run_id": str(kwargs["report_run_id"]),
            "active_review_tree_sha256": sha256_path(active_root),
        }

    monkeypatch.setattr(
        freeze_v1, "_validate_review_case_provenance", original_review_validator
    )
    with freeze._lifecycle_code_snapshot_validation_context(
        None, derive_per_case_review_run=True
    ) as entries:
        freeze_v1._validate_review_case_provenance(
            case=Case(),
            case_dir=case_dir,
            lifecycle=lifecycle,
            report_run_id="20260717T025100000000Z",
        )
    assert observed_report_ids == [run_id]
    assert entries == [expected]
    assert freeze_v1._validate_review_case_provenance is original_review_validator

    other_root = case_dir / "review_attempts/20260717T014000000000Z"
    other_root.mkdir()
    conflicting_input = other_root / "round_01.revised_checklist.yaml"
    conflicting_input.write_text("conflict\n", encoding="utf-8")
    conflicting = copy.deepcopy(lifecycle)
    conflicting["attempts"][1]["input_checklist_path"] = str(conflicting_input)
    with pytest.raises(ContractLifecycleError, match="exactly one review run"):
        freeze._derive_case_review_run(
            case_unit_id=case_id,
            case_dir=case_dir,
            lifecycle=conflicting,
        )


def test_attempt_compatibility_context_restores_every_v1_hook() -> None:
    original_assert = freeze_v1._assert_exact
    original_loader = freeze_v1._load_mapping
    original_generation = freeze_v1._validate_generation_case_provenance
    original_review = freeze_v1._validate_review_case_provenance
    with pytest.raises(RuntimeError, match="injected"):
        with freeze._lifecycle_code_snapshot_validation_context(
            None,
            derive_per_case_review_run=True,
            derive_review_attempt_state_machine=True,
            derive_generation_attempt_state_machine=True,
        ):
            assert freeze_v1._assert_exact is not original_assert
            assert freeze_v1._load_mapping is not original_loader
            assert freeze_v1._validate_generation_case_provenance is not original_generation
            assert freeze_v1._validate_review_case_provenance is not original_review
            raise RuntimeError("injected")
    assert freeze_v1._assert_exact is original_assert
    assert freeze_v1._load_mapping is original_loader
    assert freeze_v1._validate_generation_case_provenance is original_generation
    assert freeze_v1._validate_review_case_provenance is original_review


def test_post_lock_seal_binds_and_revalidates_full_snapshot_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    for position in range(949):
        case_dir = drafts / f"case_{position:04d}"
        case_dir.mkdir()
        (case_dir / "checklist.yaml").write_text("locked\n", encoding="utf-8")
        (case_dir / "review.json").write_text("{}\n", encoding="utf-8")
        (case_dir / "review_lifecycle.json").write_text("{}\n", encoding="utf-8")
    report = tmp_path / "report.json"
    report.write_text("{}\n", encoding="utf-8")
    index = tmp_path / "index.json"
    index.write_text(
        json.dumps(
            {"case_count": 949, "entries": [{"position": i} for i in range(949)]}
        )
        + "\n",
        encoding="utf-8",
    )
    snapshot = _minimal_post_lock_snapshot(
        drafts=drafts,
        report=report,
        index=index,
        formal_root=tmp_path / "formal-results-absent",
    )
    lifecycle_root = tmp_path / "lifecycle-snapshot"
    lifecycle_file = lifecycle_root / "code/locked.py"
    lifecycle_file.parent.mkdir(parents=True)
    lifecycle_file.write_text("locked\n", encoding="utf-8")
    lifecycle_config = tmp_path / "lifecycle-config.json"
    lifecycle_config.write_text("{}\n", encoding="utf-8")
    lifecycle_files = [
        {
            "declared_path": "code/locked.py",
            "locked_sha256": sha256_file(lifecycle_file),
            "resolved_path": str(lifecycle_file),
            "source": "snapshot",
        }
    ]
    lifecycle_binding = {
        "root": {
            "path": str(lifecycle_root),
            "tree_sha256": sha256_path(lifecycle_root),
        },
        "resolved_config": {
            "path": str(lifecycle_config),
            "sha256": sha256_file(lifecycle_config),
        },
        "snapshot_file_count": 1,
        "file_count": 1,
        "files_sha256": sha256_object(lifecycle_files),
        "files": lifecycle_files,
    }
    snapshot["lifecycle_code_snapshot"] = lifecycle_binding
    snapshot["runtime_code_sha256"] = {str(lifecycle_file): sha256_file(lifecycle_file)}
    process_snapshot = {
        "policy": list(freeze._REVIEW_PROCESS_POLICY),
        "command_pattern_sha256": freeze._REVIEW_COMMAND_PATTERN_SHA256,
        "scanned_process_count": 0,
        "matched_process_count": 0,
        "matched_by_policy": {name: 0 for name in freeze._REVIEW_PROCESS_POLICY},
    }
    host_session = {
        "hostname": "post-lock-host",
        "boot_id": "post-lock-boot",
        "hostname_sha256": sha256_object("post-lock-host"),
        "boot_id_sha256": sha256_object("post-lock-boot"),
    }
    events: list[str] = []

    def current_snapshot(**kwargs: Any) -> dict[str, Any]:
        assert kwargs == {"sentinel": "locked"}
        events.append("full-snapshot")
        return copy.deepcopy(snapshot)

    original_seal = freeze._seal_tree_read_only

    def seal_after_gate(root: Path) -> None:
        assert events == ["full-snapshot"]
        events.append("seal")
        original_seal(root)

    monkeypatch.setattr(
        freeze, "post_lock_agentdojo_full_review_currentness", current_snapshot
    )
    monkeypatch.setattr(freeze, "_seal_tree_read_only", seal_after_gate)
    monkeypatch.setattr(
        freeze,
        "_assert_review_process_quiescence",
        lambda: copy.deepcopy(process_snapshot),
    )
    monkeypatch.setattr(freeze, "_current_host_session", lambda: dict(host_session))
    receipt_path = tmp_path / "post_lock_quiescence.json"
    try:
        published = freeze.capture_review_quiescence_receipt(
            output_path=receipt_path,
            draft_root=drafts,
            lifecycle_report_path=report,
            lifecycle_index_path=index,
            seal_draft_tree_read_only=True,
            post_lock_currentness_seal=True,
            post_lock_snapshot_overrides={"sentinel": "locked"},
            freeze_output_path=tmp_path / "freeze.json",
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        assert (
            receipt["schema_version"]
            == freeze.CHECKLIST_REVIEW_POST_LOCK_QUIESCENCE_SCHEMA_VERSION
        )
        assert receipt["currentness_gate"] == {
            "mode": freeze.CHECKLIST_REVIEW_POST_LOCK_GATE_MODE,
            "snapshot_schema_version": freeze_v1.CHECKLIST_FREEZE_SCHEMA_VERSION,
            "snapshot_sha256": sha256_object(snapshot),
            "lifecycle_code_snapshot_root": str(lifecycle_root),
            "lifecycle_code_snapshot_tree_sha256": sha256_path(lifecycle_root),
        }
        verified = freeze.verify_review_quiescence_receipt(
            receipt_path=published,
            max_age_seconds=300,
            require_process_quiescence=False,
            post_lock_snapshot_overrides={"sentinel": "locked"},
        )
        assert verified["currentness_gate_sha256"] == sha256_object(snapshot)
        assert verified["currentness_gate_mode"] == (
            freeze.CHECKLIST_REVIEW_POST_LOCK_GATE_MODE
        )
        assert verified["lifecycle_code_snapshot_root"] == str(lifecycle_root)
        assert verified["lifecycle_code_snapshot_tree_sha256"] == sha256_path(
            lifecycle_root
        )

        drifted = copy.deepcopy(snapshot)
        drifted["case_identity"]["case_id_order_sha256"] = "1" * 64
        monkeypatch.setattr(
            freeze,
            "post_lock_agentdojo_full_review_currentness",
            lambda **_kwargs: copy.deepcopy(drifted),
        )
        with pytest.raises(ContractLifecycleError, match="currentness gate digest"):
            freeze.verify_review_quiescence_receipt(
                receipt_path=published,
                max_age_seconds=300,
                require_process_quiescence=False,
                post_lock_snapshot_overrides={"sentinel": "locked"},
            )
    finally:
        _make_tree_writable(drafts)


def test_quiescence_receipt_binds_zero_processes_host_session_and_readonly_949_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    for position in range(949):
        case_dir = drafts / f"case_{position:04d}"
        case_dir.mkdir()
        (case_dir / "checklist.yaml").write_text("locked\n", encoding="utf-8")
        (case_dir / "review.json").write_text("{}\n", encoding="utf-8")
        (case_dir / "review_lifecycle.json").write_text("{}\n", encoding="utf-8")
    report = tmp_path / "report.json"
    report.write_text("{}\n", encoding="utf-8")
    index = tmp_path / "index.json"
    index.write_text(
        json.dumps(
            {"case_count": 949, "entries": [{"position": i} for i in range(949)]}
        )
        + "\n",
        encoding="utf-8",
    )
    packet_root = tmp_path / "packets"
    packet_root.mkdir()
    preflight_files: dict[str, Path] = {}
    for name in ("manifest", "source_bundle", "resolved_config", "input_lock"):
        path = tmp_path / f"{name}.json"
        path.write_text("{}\n", encoding="utf-8")
        preflight_files[name] = path
    case_entries = [{"position": position} for position in range(949)]
    preflight_snapshot = {
        "schema_version": freeze.CHECKLIST_REVIEW_PREFLIGHT_SCHEMA_VERSION,
        "status": "ready_for_batch_lock",
        "expected_count": 949,
        "counts": {
            "case_packets": 949,
            "source_entries": 949,
            "valid_drafts": 949,
            "accepted_reviews": 949,
            "lock_eligible": 949,
            "unresolved_drafts": 0,
        },
        "case_identity": {},
        "inputs": {
            **{f"{name}_path": str(path) for name, path in preflight_files.items()},
            **{
                f"{name}_sha256": sha256_file(path)
                for name, path in preflight_files.items()
            },
            "case_packet_root": str(packet_root),
            "case_packet_tree_sha256": sha256_path(packet_root),
            "draft_root": str(drafts),
            "draft_tree_sha256": sha256_path(drafts),
            "lifecycle_report_path": str(report),
            "lifecycle_report_sha256": sha256_file(report),
            "lifecycle_index_path": str(index),
            "lifecycle_index_sha256": sha256_file(index),
            "generation_batch": {},
        },
        "planned_outputs": {
            "case_lock_path": str(tmp_path / "scratch-lock.jsonl"),
            "case_lock_destination_absent": True,
            "lock_acceptance_path": str(tmp_path / "scratch-acceptance.json"),
            "lock_acceptance_destination_absent": True,
        },
        "case_entries_sha256": sha256_object(case_entries),
        "case_entries": case_entries,
    }
    preflight_receipt = freeze.publish_review_currentness_preflight_receipt(
        snapshot=preflight_snapshot,
        output_path=tmp_path / "review_preflight.json",
    )
    process_snapshot = {
        "policy": list(freeze._REVIEW_PROCESS_POLICY),
        "command_pattern_sha256": freeze._REVIEW_COMMAND_PATTERN_SHA256,
        "scanned_process_count": 10,
        "matched_process_count": 0,
        "matched_by_policy": {name: 0 for name in freeze._REVIEW_PROCESS_POLICY},
    }
    host_session = {
        "hostname": "host-one",
        "boot_id": "boot-one",
        "hostname_sha256": sha256_object("host-one"),
        "boot_id_sha256": sha256_object("boot-one"),
    }
    monkeypatch.setattr(
        freeze,
        "_assert_review_process_quiescence",
        lambda: copy.deepcopy(process_snapshot),
    )
    monkeypatch.setattr(freeze, "_current_host_session", lambda: dict(host_session))
    receipt_path = tmp_path / "quiescence.json"
    try:
        published = freeze.capture_review_quiescence_receipt(
            output_path=receipt_path,
            draft_root=drafts,
            lifecycle_report_path=report,
            lifecycle_index_path=index,
            seal_draft_tree_read_only=True,
            review_preflight_receipt_path=preflight_receipt,
            freeze_output_path=tmp_path / "freeze.json",
        )
        verified = freeze.verify_review_quiescence_receipt(
            receipt_path=published,
            max_age_seconds=300,
            require_process_quiescence=True,
        )
        assert verified["host_session"] == host_session
        assert verified["draft_tree_sha256"] == sha256_path(drafts)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        assert (
            receipt["schema_version"]
            == freeze.CHECKLIST_REVIEW_QUIESCENCE_SCHEMA_VERSION
        )
        assert "currentness_gate" not in receipt
        assert receipt["tree_inventory"]["case_directories"] == 949
        assert receipt["draft_root"]["filesystem_read_only"] is True
        assert "created_at" in receipt

        monkeypatch.setattr(
            freeze,
            "_current_host_session",
            lambda: {
                "hostname": "host-two",
                "boot_id": "boot-two",
                "hostname_sha256": sha256_object("host-two"),
                "boot_id_sha256": sha256_object("boot-two"),
            },
        )
        with pytest.raises(ContractLifecycleError, match="host/boot session"):
            freeze.verify_review_quiescence_receipt(
                receipt_path=receipt_path,
                max_age_seconds=300,
                require_process_quiescence=False,
            )
    finally:
        _make_tree_writable(drafts)


def test_quiescence_sealing_requires_passed_preflight_and_absent_freeze(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    report = tmp_path / "report.json"
    report.write_text("{}\n", encoding="utf-8")
    index = tmp_path / "index.json"
    index.write_text(
        json.dumps({"case_count": 949, "entries": [{} for _ in range(949)]}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        freeze,
        "_assert_review_process_quiescence",
        lambda: {
            "policy": list(freeze._REVIEW_PROCESS_POLICY),
            "command_pattern_sha256": freeze._REVIEW_COMMAND_PATTERN_SHA256,
            "scanned_process_count": 0,
            "matched_process_count": 0,
            "matched_by_policy": {name: 0 for name in freeze._REVIEW_PROCESS_POLICY},
        },
    )
    output = tmp_path / "quiescence.json"
    with pytest.raises(
        ContractLifecycleError, match="requires a passed review preflight"
    ):
        freeze.capture_review_quiescence_receipt(
            output_path=output,
            draft_root=drafts,
            lifecycle_report_path=report,
            lifecycle_index_path=index,
            seal_draft_tree_read_only=True,
        )
    assert not output.exists()
    assert drafts.stat().st_mode & 0o200


def test_freeze_rechecks_fresh_quiescence_immediately_before_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    valid_definition: dict[str, Any],
) -> None:
    monkeypatch.setattr(
        freeze,
        "build_checklist_freeze_v2_definition",
        lambda **_kwargs: copy.deepcopy(valid_definition),
    )
    calls: list[dict[str, Any]] = []

    def verify_quiescence(**kwargs: Any) -> dict[str, Any]:
        calls.append(dict(kwargs))
        return copy.deepcopy(valid_definition["review_quiescence_receipt"])

    monkeypatch.setattr(freeze, "verify_review_quiescence_receipt", verify_quiescence)
    freeze.freeze_agentdojo_full_checklists_v2(
        output_path=tmp_path / "freeze.json",
        quiescence_max_age_seconds=123,
        frozen_at="2026-07-16T12:00:00+10:00",
    )
    assert len(calls) == 2
    assert all(call["max_age_seconds"] == 123 for call in calls)
    assert calls[-1]["expected_draft_tree_sha256"] == ZERO


def test_verifier_recomputes_currentness_even_when_invalidation_marker_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    valid_definition: dict[str, Any],
) -> None:
    _constant_builder(monkeypatch, valid_definition)
    output = tmp_path / "freeze.json"
    freeze.freeze_agentdojo_full_checklists_v2(
        output_path=output,
        frozen_at="2026-07-16T12:00:00+10:00",
    )
    invalidation = freeze.checklist_freeze_v2_invalidation_path(output)
    invalidation.write_text("{}\n", encoding="utf-8")
    calls = 0

    def recompute(**_kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return copy.deepcopy(valid_definition)

    monkeypatch.setattr(freeze, "build_checklist_freeze_v2_definition", recompute)
    with pytest.raises(ContractLifecycleError, match="invalidated"):
        freeze.verify_checklist_freeze_v2(freeze_path=output)
    assert calls == 1


def test_all_input_files_require_single_link_and_no_symlinked_ancestor(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.json"
    source.write_text("{}\n", encoding="utf-8")
    alias = tmp_path / "alias.json"
    alias.hardlink_to(source)
    with pytest.raises(ContractLifecycleError, match="exactly one hard link"):
        freeze._require_regular_file(source, "hard-linked input")

    real = tmp_path / "real"
    real.mkdir()
    regular = real / "regular.json"
    regular.write_text("{}\n", encoding="utf-8")
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real, target_is_directory=True)
    with pytest.raises(ContractLifecycleError, match="symlinked ancestor"):
        freeze._require_regular_file(
            linked_parent / "regular.json", "symlink-ancestor input"
        )
