from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from evidence_system.cli.finalize_agentdojo_full_evidence import main as evidence_main
from evidence_system.contracts.agentdojo_full_evidence import (
    EVIDENCE_INDEX_SCHEMA_VERSION,
    EXECUTION_STAGING_NAMESPACE,
    PRESCORE_JOIN_SCHEMA_VERSION,
    _assert_inventory_equal,
    _atomic_promote_tree,
    _blind_top_level_projection,
    _score_empty_snapshot,
    _tree_inventory,
    _validate_evidence_index_payload,
    _validate_join_payload,
    _validate_promotion_payload,
    _verify_formal_execution_receipts,
    verify_prescore_join_inputs_current,
    _require_reserved_formal_namespace,
    LockedArtifactResult,
    _assert_tree_read_only,
    _seal_tree_read_only,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_file, sha256_object, sha256_path
from evidence_system.core.schemas import (
    REQUIRED_SCHEMA_FILES,
    check_schema_files,
    load_schema,
)
from neurips_ed_track_minimal.scripts import run_agentdojo_score_batch as score_batch
from neurips_ed_track_minimal.scripts import score_evidence_with_codex as score_child
from neurips_ed_track_minimal.scripts import (
    score_evidence_with_openrouter as openrouter_child,
)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def test_blind_raw_projection_does_not_materialize_outcomes_or_trajectories(
    tmp_path: Path,
) -> None:
    raw = tmp_path / "raw_run.json"
    _write_json(
        raw,
        {
            "case_unit_id": "v1.2.2:slack:user_task_1:injection_task_2",
            "status": "COMPLETED",
            "native_label": "sentinel-secret-label",
            "native_score": 1.0,
            "episode_ids": ["sentinel-secret-trajectory"],
            "native_decisive_support": {
                "deeply": {"nested": ["sentinel-secret-evidence"]}
            },
        },
    )

    projected, keys = _blind_top_level_projection(
        raw, frozenset({"case_unit_id", "status"})
    )

    assert projected == {
        "case_unit_id": "v1.2.2:slack:user_task_1:injection_task_2",
        "status": "COMPLETED",
    }
    assert keys == {
        "case_unit_id",
        "status",
        "native_label",
        "native_score",
        "episode_ids",
        "native_decisive_support",
    }
    assert "sentinel" not in json.dumps(projected)


def test_blind_raw_projection_rejects_duplicate_metadata_keys(tmp_path: Path) -> None:
    raw = tmp_path / "raw_run.json"
    raw.write_text('{"status":"COMPLETED","status":"COMPLETED"}\n', encoding="utf-8")
    with pytest.raises(ContractLifecycleError, match="duplicate raw metadata key"):
        _blind_top_level_projection(raw, frozenset({"status"}))


def test_blind_raw_projection_accepts_only_string_episode_id_list(
    tmp_path: Path,
) -> None:
    raw = tmp_path / "raw_run.json"
    _write_json(raw, {"episode_ids": ["benign", "injection-as-user", "injected"]})
    projected, _ = _blind_top_level_projection(raw, frozenset({"episode_ids"}))
    assert projected["episode_ids"] == ["benign", "injection-as-user", "injected"]
    _write_json(raw, {"episode_ids": [{"trajectory": "forbidden"}]})
    with pytest.raises(ContractLifecycleError, match="exact episode_ids"):
        _blind_top_level_projection(raw, frozenset({"episode_ids"}))


@pytest.mark.parametrize("kind", ["fifo", "hardlink", "symlink"])
def test_acceptance_tree_inventory_rejects_nonregular_or_linked_nodes(
    tmp_path: Path, kind: str
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    regular = root / "regular.bin"
    regular.write_bytes(b"opaque\n")
    if kind == "fifo":
        os.mkfifo(root / "forbidden.fifo")
        match = "special filesystem node"
    elif kind == "hardlink":
        os.link(regular, root / "forbidden-hardlink.bin")
        match = "hardlinked"
    else:
        (root / "forbidden-symlink").symlink_to(regular)
        match = "symlink"
    with pytest.raises(ContractLifecycleError, match=match):
        _tree_inventory(root)


def test_evidence_acceptance_schema_and_semantics_require_2847_unique_slots() -> None:
    entries: list[dict[str, Any]] = []
    for case_index in range(949):
        case_id = f"v1.2.2:workspace:user_task_{case_index}:injection_task_0"
        for agent_index, agent_id in enumerate(("Agent A", "Agent B", "Agent C")):
            suffix = f"{case_index}-{agent_index}"
            entries.append(
                {
                    "job_id": f"job-{suffix}",
                    "case_unit_id": case_id,
                    "task_id": f"workspace:user_task_{case_index}:injection_task_0",
                    "record_slot_id": f"slot-{suffix}",
                    "run_id": f"run-{suffix}",
                    "attempt_id": f"attempt-{suffix}",
                    "seed": case_index,
                    "agent_id": agent_id,
                    "execution_lock_sha256": "1" * 64,
                    "execution_policy_sha256": "2" * 64,
                    "evidence_directory": f"staging/job-{suffix}/adapter",
                    "raw_run_path": f"staging/job-{suffix}/adapter/raw_run.json",
                    "raw_run_sha256": "3" * 64,
                    "artifact_manifest_path": f"staging/job-{suffix}/adapter/artifact_manifest.json",
                    "artifact_manifest_sha256": "4" * 64,
                    "environment_path": f"staging/job-{suffix}/adapter/environment.json",
                    "environment_sha256": "5" * 64,
                    "native_job_path": f"staging/job-{suffix}/adapter/native_run/job.json",
                    "native_job_sha256": "6" * 64,
                    "job_binding_sha256": "c" * 64,
                    "job_identity_sha256": f"{case_index * 3 + agent_index:064x}",
                    "formal_completion_marker_path": (
                        f"staging/job-{suffix}/adapter/formal_job_completion.json"
                    ),
                    "formal_completion_marker_sha256": "d" * 64,
                    "formal_completion_marker_semantic_sha256": "e" * 64,
                    "artifact_count": 8,
                    "artifact_set_sha256": "7" * 64,
                    "job_tree_sha256": "8" * 64,
                    "native_trajectory_file_count": 3,
                    "metadata_status": "completed",
                }
            )
    definition = {
        "execution_lock": {"path": "lock/execution_lock.json", "sha256": "1" * 64},
        "checklist_freeze_lock": {
            "path": "lock/checklist_freeze_v2.json",
            "sha256": "c" * 64,
        },
        "review_quiescence_receipt": {
            "path": "lock/acceptance_quiescence.json",
            "sha256": "a" * 64,
        },
        "sealed_retrieval_receipt": {
            "path": "provenance/sealed_retrieval.json",
            "sha256": "b" * 64,
        },
        "execution_policy_sha256": "2" * 64,
        "formal_execution_receipts": {
            "completion": {"path": "provenance/completion.json", "sha256": "d" * 64},
            "anomaly": {"path": "provenance/anomaly.json", "sha256": "e" * 64},
            "remote_completion_index": {
                "path": "provenance/remote-index.json",
                "sha256": "f" * 64,
            },
        },
        "staging_evidence_root": {
            "path": "results/staging",
            "tree_sha256": "9" * 64,
            "file_count": 1,
        },
        "counts": {
            "cases": 949,
            "agents_per_case": 3,
            "record_slots": 2847,
            "native_trajectories": 8541,
            "completed": 2847,
            "missing": 0,
            "duplicate": 0,
            "unexpected": 0,
            "unresolved": 0,
        },
        "case_identity": {
            "case_id_order_sha256": "a" * 64,
            "case_id_set_sha256": "b" * 64,
            "suite_case_counts": {
                "banking": 144,
                "slack": 105,
                "travel": 140,
                "workspace": 560,
            },
        },
        "entry_order": "execution_lock_job_plan",
        "entries_sha256": sha256_object(entries),
        "entries": entries,
        "blind_audit": {
            "raw_run_projection": "top_level_integrity_metadata_only",
            "artifact_bytes": "hashed_not_deserialized",
            "trajectory_contents_materialized": False,
            "native_labels_materialized": False,
            "native_labels_emitted": False,
        },
    }
    payload = {
        "schema_version": EVIDENCE_INDEX_SCHEMA_VERSION,
        "index_id": "agentdojo_full_v1.2.2_direct_evidence_acceptance",
        "status": "accepted",
        "locked_at": "2026-07-16T10:00:00+00:00",
        "result_namespace": EXECUTION_STAGING_NAMESPACE,
        "definition": definition,
        "definition_sha256": sha256_object(definition),
    }

    _validate_evidence_index_payload(payload)
    entries[-1]["agent_id"] = "Agent B"
    definition["entries_sha256"] = sha256_object(entries)
    payload["definition_sha256"] = sha256_object(definition)
    with pytest.raises(ContractLifecycleError, match="bijection"):
        _validate_evidence_index_payload(payload)


def test_atomic_promotion_is_byte_identical_and_recovery_is_idempotent(
    tmp_path: Path,
) -> None:
    source = tmp_path / "staging"
    destination = tmp_path / "formal"
    (source / "job-a/adapter").mkdir(parents=True)
    (source / "job-a/adapter/raw_run.json").write_bytes(b"raw-bytes\n")
    (source / "job-a/adapter/environment.json").write_bytes(b"environment-bytes\n")

    source_inventory = _tree_inventory(source)
    methods = _atomic_promote_tree(
        source_inventory=source_inventory, destination=destination
    )
    destination_inventory = _tree_inventory(destination)
    _assert_inventory_equal(source_inventory, destination_inventory)
    assert set(methods.values()) == {"copy"}

    recovered = _atomic_promote_tree(
        source_inventory=source_inventory, destination=destination
    )
    assert set(recovered.values()) == {"existing_verified"}
    for promoted in destination.rglob("*"):
        if promoted.is_file():
            assert promoted.stat().st_nlink == 1

    promoted_raw = destination / "job-a/adapter/raw_run.json"
    promoted_raw.write_bytes(b"tampered\n")
    assert (source / "job-a/adapter/raw_run.json").read_bytes() == b"raw-bytes\n"
    with pytest.raises(ContractLifecycleError, match="not byte-identical"):
        _assert_inventory_equal(source_inventory, _tree_inventory(destination))
    promoted_raw.write_bytes(b"raw-bytes\n")

    _seal_tree_read_only(destination)
    _assert_tree_read_only(destination)
    assert not (destination.stat().st_mode & 0o222)
    assert not ((destination / "job-a/adapter/raw_run.json").stat().st_mode & 0o222)
    for path in (destination, *destination.rglob("*")):
        path.chmod(path.stat().st_mode | 0o700)


def test_atomic_promotion_never_replaces_an_existing_empty_destination(
    tmp_path: Path,
) -> None:
    source = tmp_path / "staging"
    destination = tmp_path / "formal"
    source.mkdir()
    (source / "opaque.bin").write_bytes(b"opaque\n")
    destination.mkdir()

    with pytest.raises(ContractLifecycleError, match="not byte-identical"):
        _atomic_promote_tree(
            source_inventory=_tree_inventory(source), destination=destination
        )
    assert list(destination.iterdir()) == []


def test_postpromotion_envelope_is_used_only_after_exact_namespace_proof(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from evidence_system.contracts import agentdojo_full_evidence as contract

    namespace = tmp_path / "formal-namespace"
    destination = namespace / "full/agentdojo"
    source = tmp_path / "staging"
    destination.mkdir(parents=True)
    source.mkdir()
    (source / "opaque.bin").write_bytes(b"opaque-evidence\n")
    (destination / "opaque.bin").write_bytes(b"opaque-evidence\n")

    execution_path = tmp_path / "execution.json"
    checklist_path = tmp_path / "checklist.json"
    quiescence_path = tmp_path / "promotion-quiescence.json"
    evidence_path = tmp_path / "evidence-index.json"
    retrieval_path = tmp_path / "sealed-retrieval.json"
    receipt_path = tmp_path / "promotion.json"
    for path in (
        execution_path,
        checklist_path,
        quiescence_path,
        evidence_path,
        retrieval_path,
    ):
        _write_json(path, {})
    marker_path = namespace / "NAMESPACE_LOCK.json"
    _write_json(
        marker_path,
        {
            "schema_version": "result_namespace_lock/v1",
            "result_namespace": "agentdojo_full_v1.2.2_direct",
            "experiment_manifest_path": (
                "experiments/agentdojo_full_v1.2.2_direct/experiment_manifest.yaml"
            ),
            "formal_result_root": str(destination.resolve()),
            "legacy_result_root": "results/full/agentdojo",
            "legacy_result_root_must_not_be_modified": True,
            "status": "reserved_no_formal_runs_yet",
        },
    )
    score_a = tmp_path / "scores-a"
    score_b = tmp_path / "scores-b"
    score_a.mkdir()
    score_b.mkdir()

    source_inventory = contract._tree_inventory(source)
    destination_inventory = contract._tree_inventory(destination)
    files = [
        {
            "relative_path": str(item["relative_path"]),
            "size_bytes": int(item["size_bytes"]),
            "source_sha256": str(item["sha256"]),
            "destination_sha256": str(item["sha256"]),
            "transfer_method": "copy",
        }
        for item in source_inventory.files
    ]
    definition = {
        "execution_lock": contract._path_lock(execution_path),
        "checklist_freeze_lock": contract._path_lock(checklist_path),
        "review_quiescence_receipt": contract._path_lock(quiescence_path),
        "sealed_retrieval_receipt": contract._path_lock(retrieval_path),
        "evidence_acceptance_index": contract._path_lock(evidence_path),
        "namespace_reservation": contract._path_lock(marker_path),
        "source": {
            "path": str(source.resolve()),
            "tree_sha256": source_inventory.tree_sha256,
            "file_count": source_inventory.file_count,
        },
        "destination": {
            "path": str(destination.resolve()),
            "tree_sha256": destination_inventory.tree_sha256,
            "file_count": destination_inventory.file_count,
        },
        "counts": {
            "cases": 949,
            "record_slots": 2847,
            "files": source_inventory.file_count,
            "hash_mismatches": 0,
        },
        "inventory_sha256": sha256_object(files),
        "files": files,
        "byte_preserving": True,
        "formal_tree_read_only": True,
        "formal_tree_hardlink_count": 0,
        "score_output_precondition": contract._score_empty_snapshot(
            (score_a, score_b)
        ),
        "publication": "atomic_directory_rename_after_full_hash_verification",
        "publication_guarantees": {
            "copy_only": True,
            "same_filesystem": True,
            "fsync_completed_before_publication": True,
            "atomic_rename_noreplace": True,
            "destination_overwrite_permitted": False,
        },
    }
    _write_json(
        receipt_path,
        {
            "schema_version": "agentdojo_full_evidence_promotion_receipt/v1",
            "promotion_id": (
                "agentdojo_full_v1.2.2_direct_staging_to_formal"
            ),
            "status": "promoted_and_verified",
            "locked_at": "2026-07-16T10:00:00+00:00",
            "result_namespace": "agentdojo_full_v1.2.2_direct",
            "definition": definition,
            "definition_sha256": sha256_object(definition),
        },
    )
    monkeypatch.setattr(
        contract, "DEFAULT_RESULT_NAMESPACE_LOCK", marker_path
    )
    monkeypatch.setattr(
        contract,
        "_verify_checklist_v2_quiescence_gate",
        lambda **_: (SimpleNamespace(freeze_path=checklist_path), {}),
    )
    events: list[str] = []
    real_namespace_proof = contract._verify_promoted_namespace_layout

    def namespace_proof(**kwargs: Any) -> dict[str, str]:
        events.append("namespace-proof")
        return real_namespace_proof(**kwargs)

    def execution_envelope(**_: Any) -> SimpleNamespace:
        events.append("execution-envelope")
        return SimpleNamespace(
            lock_path=execution_path,
            definition={
                "output_precondition": {
                    "staging_raw_result_root": str(source.resolve()),
                    "formal_raw_result_root": str(destination.resolve()),
                }
            },
        )

    def evidence_envelope(**kwargs: Any) -> LockedArtifactResult:
        assert kwargs["_execution_envelope_only"] is True
        events.append("evidence-envelope")
        return LockedArtifactResult(
            path=evidence_path,
            sha256=sha256_file(evidence_path),
            definition={
                "sealed_retrieval_receipt": contract._path_lock(retrieval_path)
            },
            created=False,
        )

    monkeypatch.setattr(contract, "_verify_promoted_namespace_layout", namespace_proof)
    monkeypatch.setattr(contract, "verify_execution_lock_envelope", execution_envelope)
    monkeypatch.setattr(
        contract, "verify_evidence_acceptance_index", evidence_envelope
    )
    contract._seal_tree_read_only(destination)
    try:
        verified = contract.verify_evidence_promotion_receipt(
            receipt_path=receipt_path,
            execution_lock_path=execution_path,
            checklist_freeze_lock_path=checklist_path,
            evidence_index_path=evidence_path,
            score_result_roots=(score_a, score_b),
        )
        assert verified.path == receipt_path.resolve()
        assert events == [
            "namespace-proof",
            "execution-envelope",
            "evidence-envelope",
        ]

        events.clear()
        (namespace / "unbound.bin").write_bytes(b"not-in-promotion-receipt\n")
        with pytest.raises(ContractLifecycleError, match="unbound file"):
            contract.verify_evidence_promotion_receipt(
                receipt_path=receipt_path,
                execution_lock_path=execution_path,
                checklist_freeze_lock_path=checklist_path,
                evidence_index_path=evidence_path,
                score_result_roots=(score_a, score_b),
            )
        assert events == ["namespace-proof"]

        (namespace / "unbound.bin").unlink()
        events.clear()
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        marker["status"] = "stale"
        _write_json(marker_path, marker)
        with pytest.raises(
            ContractLifecycleError, match="namespace reservation metadata"
        ):
            contract.verify_evidence_promotion_receipt(
                receipt_path=receipt_path,
                execution_lock_path=execution_path,
                checklist_freeze_lock_path=checklist_path,
                evidence_index_path=evidence_path,
                score_result_roots=(score_a, score_b),
            )
        assert events == ["namespace-proof"]
    finally:
        for path in (destination, *destination.rglob("*")):
            path.chmod(path.stat().st_mode | 0o700)


def test_raw_acceptance_fails_before_any_retrieved_tree_access_without_v2_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from evidence_system.contracts import agentdojo_full_evidence as contract

    monkeypatch.setattr(
        contract,
        "_verify_checklist_v2_quiescence_gate",
        lambda **_: (_ for _ in ()).throw(
            ContractLifecycleError("v2 freeze/quiescence absent")
        ),
    )
    monkeypatch.setattr(
        contract,
        "verify_sealed_evidence_retrieval_receipt",
        lambda **_: pytest.fail("retrieval must not be inspected before the v2 gate"),
    )
    monkeypatch.setattr(
        contract,
        "verify_execution_lock",
        lambda **_: pytest.fail("execution/raw resolution must not start before gate"),
    )

    with pytest.raises(ContractLifecycleError, match="v2 freeze/quiescence absent"):
        contract.build_evidence_acceptance_definition()


def test_sealed_retrieval_verifier_gates_before_receipt_or_raw_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from evidence_system.contracts import agentdojo_full_evidence as contract

    monkeypatch.setattr(
        contract,
        "_verify_checklist_v2_quiescence_gate",
        lambda **_: (_ for _ in ()).throw(
            ContractLifecycleError("review quiescence is stale")
        ),
    )
    monkeypatch.setattr(
        contract,
        "_regular_file",
        lambda *_args, **_kwargs: pytest.fail(
            "retrieval receipt/raw must not be touched before quiescence"
        ),
    )

    with pytest.raises(ContractLifecycleError, match="quiescence is stale"):
        contract.verify_sealed_evidence_retrieval_receipt()


def test_join_hash_graph_rejects_any_cross_lock_hash_substitution() -> None:
    def binding(name: str, digest: str) -> dict[str, str]:
        return {"path": f"locks/{name}.json", "sha256": digest}

    graph = {
        "execution_lock_sha256": "1" * 64,
        "checklist_freeze_sha256": "2" * 64,
        "review_quiescence_receipt_sha256": "3" * 64,
        "sealed_retrieval_receipt_sha256": "4" * 64,
        "evidence_acceptance_index_sha256": "5" * 64,
        "promotion_receipt_sha256": "6" * 64,
        "score_prompt_sha256": "7" * 64,
        "score_schema_sha256": "8" * 64,
        "formal_evidence_tree_sha256": "9" * 64,
    }
    definition = {
        "execution_lock": binding("execution", graph["execution_lock_sha256"]),
        "checklist_freeze_lock": binding(
            "checklist", graph["checklist_freeze_sha256"]
        ),
        "review_quiescence_receipt": binding(
            "quiescence", graph["review_quiescence_receipt_sha256"]
        ),
        "sealed_retrieval_receipt": binding(
            "retrieval", graph["sealed_retrieval_receipt_sha256"]
        ),
        "evidence_acceptance_index": binding(
            "evidence", graph["evidence_acceptance_index_sha256"]
        ),
        "promotion_receipt": binding(
            "promotion", graph["promotion_receipt_sha256"]
        ),
        "score_prompt": binding("prompt", graph["score_prompt_sha256"]),
        "score_schema": binding("schema", graph["score_schema_sha256"]),
        "formal_evidence": {
            "path": "results/formal",
            "tree_sha256": graph["formal_evidence_tree_sha256"],
            "file_count": 1,
        },
        "hash_graph": graph,
        "join_inputs_sha256": sha256_object(graph),
        "score_output_precondition": {
            "roots": [
                {"path": "scores/codex", "file_count": 0},
                {"path": "scores/openrouter", "file_count": 0},
            ],
            "all_empty": True,
        },
        "authorization": {
            "case_count": 949,
            "agents_per_case": 3,
            "score_task_count": 2847,
            "tasks_per_key": 949,
            "slot_count": 3,
            "unresolved_evidence": 0,
            "unresolved_checklists": 0,
        },
    }
    payload = {
        "schema_version": PRESCORE_JOIN_SCHEMA_VERSION,
        "join_id": "agentdojo_full_v1.2.2_direct_prescore_join",
        "lock_status": "locked",
        "locked_at": "2026-07-16T10:00:00+00:00",
        "result_namespace": "agentdojo_full_v1.2.2_direct",
        "definition": definition,
        "definition_sha256": sha256_object(definition),
    }
    _validate_join_payload(payload)

    definition["hash_graph"]["score_schema_sha256"] = "f" * 64
    definition["join_inputs_sha256"] = sha256_object(definition["hash_graph"])
    payload["definition_sha256"] = sha256_object(definition)
    with pytest.raises(ContractLifecycleError, match="score_schema_sha256"):
        _validate_join_payload(payload)


def test_score_namespace_gate_fails_closed(tmp_path: Path) -> None:
    first = tmp_path / "codex"
    second = tmp_path / "openrouter"
    first.mkdir()
    second.mkdir()
    assert _score_empty_snapshot((first, second))["all_empty"] is True
    (second / "partial-score.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ContractLifecycleError, match="not empty"):
        _score_empty_snapshot((first, second))


def test_evidence_acceptance_binds_blind_completion_and_anomaly_receipt_hashes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from evidence_system.adapters.agentdojo_runtime_control import (
        job_identity_sha256,
    )
    from evidence_system.adapters.runtime import formal_job_binding_sha256
    from evidence_system.contracts import agentdojo_full_evidence as contract

    execution_lock = tmp_path / "execution_lock.json"
    anomaly_path = tmp_path / "formal_execution_anomaly_receipt.json"
    completion_path = tmp_path / "formal_execution_completion_receipt.json"
    remote_index_path = tmp_path / "formal_remote_completion_index.json"
    journal_path = tmp_path / "formal-completion-journal.v2.jsonl"
    failed_journal_path = tmp_path / "formal-failed-attempt-journal.v2.jsonl"
    namespace_init_path = tmp_path / "formal_execution_namespace_init_receipt.json"
    execution_lock.write_text("{}\n", encoding="utf-8")
    namespace_init_path.write_text("{}\n", encoding="utf-8")
    failed_journal_path.write_bytes(b"")
    execution_sha = "1" * 64
    policy_sha = "2" * 64
    experiment_root = tmp_path / "experiment"
    monkeypatch.setattr(contract, "EXPERIMENT_ROOT", experiment_root)
    monkeypatch.setattr(
        contract, "DEFAULT_FORMAL_NAMESPACE_INIT_RECEIPT", namespace_init_path
    )
    plan_root = experiment_root / "execution_plan" / execution_sha
    jobs_root = plan_root / "jobs"
    jobs_root.mkdir(parents=True)

    stage_order = [
        "canary",
        "ramp-a-8",
        "ramp-a-16",
        "ramp-a-32",
        "remaining-a",
        "ramp-b-8",
        "ramp-b-16",
        "ramp-b-32",
        "remaining-b",
        "ramp-c-8",
        "ramp-c-16",
        "ramp-c-32",
        "remaining-c",
        "recovery-a",
        "recovery-b",
        "recovery-c",
    ]
    execution_definition = {
        "concurrency_policy": {"promotion_policy": {"formal_stage_order": stage_order}}
    }
    plan_entries: list[dict[str, Any]] = []
    remote_entries: list[dict[str, Any]] = []
    journal_entries: list[dict[str, Any]] = []
    for index in range(2847):
        job = {
            "job_id": f"job-{index}",
            "case_unit_id": f"case-{index // 3}",
            "record_slot_id": f"slot-{index}",
            "agent_id": ("Agent A", "Agent B", "Agent C")[index % 3],
            "execution_lock_sha256": execution_sha,
            "execution_policy_sha256": policy_sha,
        }
        job_path = jobs_root / f"job-{index}.json"
        _write_json(job_path, job)
        plan_entries.append(
            {
                "job_id": job["job_id"],
                "record_slot_id": job["record_slot_id"],
                "agent_id": job["agent_id"],
                "path": str(job_path.resolve()),
                "sha256": sha256_file(job_path),
                "execution_lock_sha256": execution_sha,
            }
        )
        binding = formal_job_binding_sha256(job)
        entry = {
            "schema_version": "agentdojo_formal_remote_completion_index_entry/v2",
            "execution_lock_sha256": execution_sha,
            "execution_policy_sha256": policy_sha,
            "job_binding_sha256": binding,
            "job_identity_sha256": job_identity_sha256(job),
            "stage_authorization_sha256": "3" * 64,
            "formal_stage_id": "recovery-a",
            "formal_stage_session_id": f"session-{index}",
            "formal_execution_context_sha256": "4" * 64,
            "canonical_job_relative_path": binding,
            "completion_marker_relative_path": (
                f"{binding}/adapter/formal_job_completion.json"
            ),
            "completion_marker_file_sha256": "5" * 64,
            "completion_marker_semantic_sha256": "6" * 64,
            "artifact_file_count": 8,
            "artifact_tree_sha256": "7" * 64,
            "artifact_total_bytes": 1024,
            "native_episode_count": 3,
            "attempt_tree_sha256": "8" * 64,
            "attempt_file_count": 7,
            "attempt_total_bytes": 2048,
            "supervisor_exit_receipt_sha256": "9" * 64,
            "blind_only": True,
            "contains_case_agent_prompt_response_trajectory_evaluator_or_label": False,
        }
        remote_entries.append(entry)
        journal_entries.append(
            {
                **entry,
                "schema_version": (
                    "agentdojo_formal_remote_completion_journal_entry/v2"
                ),
                "recorded_at": "2026-07-16T09:00:00+00:00",
            }
        )
    plan_index = plan_root / "plan_index.json"
    plan = {
        "schema_version": "agentdojo_locked_job_plan_index/v2",
        "execution_lock_sha256": execution_sha,
        "execution_policy_sha256": policy_sha,
        "job_count": 2847,
        "record_slot_count": 2847,
        "entries_sha256": sha256_object(plan_entries),
        "entries": plan_entries,
    }
    _write_json(plan_index, plan)
    journal_path.write_text(
        "".join(
            json.dumps(entry, separators=(",", ":"), sort_keys=True) + "\n"
            for entry in journal_entries
        ),
        encoding="utf-8",
    )
    journal_set_sha = sha256_object(
        sorted(remote_entries, key=lambda item: item["job_binding_sha256"])
    )
    remote_index = {
        "schema_version": "agentdojo_formal_remote_completion_index/v2",
        "status": "frozen",
        "frozen_at": "2026-07-16T10:00:00+00:00",
        "execution_lock_sha256": execution_sha,
        "execution_policy_sha256": policy_sha,
        "plan_index_sha256": sha256_file(plan_index),
        "entry_order": "execution_lock_job_plan",
        "entry_count": 2847,
        "native_trajectory_count": 8541,
        "completion_journal_relative_path": journal_path.name,
        "completion_journal_file_sha256": sha256_file(journal_path),
        "completion_journal_entry_count": 2847,
        "completion_journal_entry_set_sha256": journal_set_sha,
        "entries_sha256": sha256_object(remote_entries),
        "entries": remote_entries,
        "blind_only": True,
        "contains_case_agent_prompt_response_trajectory_evaluator_or_label": False,
    }
    _write_json(remote_index_path, remote_index)
    anomaly = {
        "schema_version": "agentdojo_formal_execution_anomaly_receipt/v1",
        "execution_lock_sha256": execution_sha,
        "execution_policy_sha256": policy_sha,
        "plan_index_sha256": sha256_file(plan_index),
        "blind_only": True,
        "contains_case_prompt_response_trajectory_evaluator_or_label": False,
    }
    _write_json(anomaly_path, anomaly)
    completion = {
        "schema_version": "agentdojo_formal_execution_completion_receipt/v2",
        "status": "frozen",
        "frozen_at": "2026-07-16T10:01:00+00:00",
        "execution_lock_sha256": execution_sha,
        "execution_policy_sha256": policy_sha,
        "plan_index_sha256": sha256_file(plan_index),
        "namespace_init_receipt_sha256": sha256_file(namespace_init_path),
        "completion_journal_relative_path": journal_path.name,
        "completion_journal_file_sha256": sha256_file(journal_path),
        "completion_journal_entry_count": 2847,
        "completion_journal_entry_set_sha256": journal_set_sha,
        "completion_index_relative_path": remote_index_path.name,
        "completion_index_file_sha256": sha256_file(remote_index_path),
        "completion_index_semantic_sha256": sha256_object(remote_index),
        "completion_index_entries_sha256": sha256_object(remote_entries),
        "failed_attempt_journal_relative_path": failed_journal_path.name,
        "failed_attempt_journal_file_sha256": sha256_file(failed_journal_path),
        "failed_attempt_journal_entry_count": 0,
        "failed_attempt_journal_entry_set_sha256": sha256_object([]),
        "canonical_job_count": 2847,
        "native_trajectory_count": 8541,
        "unresolved_failure_count": 0,
        "lifecycle_lock_relative_path": ".canonical-lifecycle.lock",
        "blind_only": True,
        "contains_case_agent_prompt_response_trajectory_evaluator_or_label": False,
    }
    _write_json(completion_path, completion)
    bindings = _verify_formal_execution_receipts(
        completion_path=completion_path,
        anomaly_path=anomaly_path,
        execution_lock_path=execution_lock,
        execution_lock_sha256=execution_sha,
        execution_policy_sha256=policy_sha,
        execution_definition=execution_definition,
        remote_completion_index_path=remote_index_path,
    )
    assert bindings["completion"]["sha256"] == sha256_file(completion_path)
    assert bindings["anomaly"]["sha256"] == sha256_file(anomaly_path)

    original_anomaly_sha = bindings["anomaly"]["sha256"]
    anomaly["anomaly_record_count"] = 1
    _write_json(anomaly_path, anomaly)
    assert sha256_file(anomaly_path) != original_anomaly_sha


def test_verify_only_missing_index_fails_closed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = evidence_main(["--verify-only", "--output", str(tmp_path / "missing.json")])
    assert rc == 2
    assert "not a regular file" in capsys.readouterr().out


def test_new_strict_schemas_are_registered() -> None:
    assert check_schema_files().ok
    assert {
        "agentdojo_full_evidence_acceptance_index.schema.json",
        "agentdojo_full_evidence_promotion_receipt.schema.json",
        "agentdojo_full_prescore_join_lock.schema.json",
        "agentdojo_sealed_evidence_retrieval_receipt.schema.json",
    } <= set(REQUIRED_SCHEMA_FILES)
    entries = load_schema("agentdojo_full_evidence_acceptance_index")["properties"][
        "definition"
    ]["properties"]["entries"]
    assert entries["minItems"] == entries["maxItems"] == 2847


def test_copy_only_promotion_fixture_is_schema_and_semantically_valid() -> None:
    fixture = (
        Path(__file__).parents[1]
        / "fixtures/valid_agentdojo_full_evidence_promotion_receipt.json"
    )
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    _validate_promotion_payload(payload)
    assert payload["definition"]["files"][0]["transfer_method"] == "copy"


def _formal_score_args(tmp_path: Path) -> SimpleNamespace:
    return SimpleNamespace(
        evidence_root=score_batch.FULL_EVIDENCE_ROOT,
        draft_root=score_batch.FULL_DRAFT_ROOT,
        score_output_root=score_batch.FORMAL_SCORE_ROOTS[0],
        batch_root=score_batch.FORMAL_SCORE_ROOTS[0] / "_batch_runs",
        slot_count=3,
        tasks_per_key=949,
        agents=None,
        ignore_extra_evidence_cases=False,
        dry_run=False,
        score_prompt=score_batch.score_module.PROMPT_PATH,
        score_schema=score_batch.score_module.SCHEMA_PATH,
        prescore_join_lock=tmp_path / "prescore_join_lock.json",
        nonformal_disposable=False,
        resume_formal_session=None,
        force=False,
    )


def _fake_join(tmp_path: Path) -> LockedArtifactResult:
    join_path = tmp_path / "prescore_join_lock.json"
    join_path.write_text("{}\n", encoding="utf-8")
    authorization = {
        "case_count": 949,
        "agents_per_case": 3,
        "score_task_count": 2847,
        "tasks_per_key": 949,
        "slot_count": 3,
        "unresolved_evidence": 0,
        "unresolved_checklists": 0,
    }
    return LockedArtifactResult(
        path=join_path,
        sha256="1" * 64,
        definition={
            "authorization": authorization,
            "formal_evidence": {
                "path": str(score_batch.FULL_EVIDENCE_ROOT),
                "tree_sha256": "2" * 64,
                "file_count": 1,
            },
        },
        created=False,
    )


def test_formal_score_gate_accepts_only_exact_join_authorization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _formal_score_args(tmp_path)
    fake = _fake_join(tmp_path)
    monkeypatch.setattr(
        score_batch, "verify_prescore_join_inputs_current", lambda **_: fake
    )
    accepted = score_batch.enforce_formal_score_entry_gate(args)
    assert accepted is not None
    assert accepted.join.sha256 == fake.sha256


def test_formal_resume_revalidates_join_without_requiring_empty_score_roots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _formal_score_args(tmp_path)
    args.resume_formal_session = tmp_path / "formal_score_session.json"
    fake = _fake_join(tmp_path)
    observed: dict[str, Any] = {}

    def verify(**kwargs: Any) -> LockedArtifactResult:
        observed.update(kwargs)
        return fake

    monkeypatch.setattr(score_batch, "verify_prescore_join_inputs_current", verify)
    accepted = score_batch.enforce_formal_score_entry_gate(args)
    assert accepted is not None
    assert accepted.resume_session_path == args.resume_formal_session.resolve()
    assert observed["require_score_roots_empty"] is False


def test_formal_score_gate_forbids_force_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _formal_score_args(tmp_path)
    args.force = True
    monkeypatch.setattr(
        score_batch,
        "verify_prescore_join_inputs_current",
        lambda **_: pytest.fail("force must fail before join verification"),
    )
    with pytest.raises(score_batch.AgentDojoBatchScoreError, match="forbids --force"):
        score_batch.enforce_formal_score_entry_gate(args)


def test_prescore_currentness_relaxes_only_score_root_emptiness_on_resume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from evidence_system.contracts import agentdojo_full_evidence as evidence_contract

    execution_path = tmp_path / "execution.json"
    checklist_path = tmp_path / "checklist_freeze.json"
    evidence_path = tmp_path / "evidence_index.json"
    promotion_path = tmp_path / "promotion.json"
    quiescence_path = tmp_path / "join_quiescence.json"
    retrieval_path = tmp_path / "sealed_retrieval.json"
    join_path = tmp_path / "join.json"
    prompt_path = tmp_path / "prompt.md"
    schema_path = tmp_path / "schema.json"
    formal_evidence = tmp_path / "formal-evidence"
    score_a = tmp_path / "score-a"
    score_b = tmp_path / "score-b"
    for path in (
        execution_path,
        checklist_path,
        evidence_path,
        promotion_path,
        quiescence_path,
        retrieval_path,
        join_path,
        prompt_path,
        schema_path,
    ):
        path.write_text("{}\n", encoding="utf-8")
    formal_evidence.mkdir()
    score_a.mkdir()
    score_b.mkdir()

    def lock(path: Path) -> dict[str, str]:
        return {"path": str(path.resolve()), "sha256": sha256_file(path)}

    authorization = {
        "case_count": 949,
        "agents_per_case": 3,
        "score_task_count": 2847,
        "tasks_per_key": 949,
        "slot_count": 3,
        "unresolved_evidence": 0,
        "unresolved_checklists": 0,
    }
    destination = {
        "path": str(formal_evidence.resolve()),
        "tree_sha256": "7" * 64,
        "file_count": 1,
    }
    hash_graph = {
        "execution_lock_sha256": lock(execution_path)["sha256"],
        "checklist_freeze_sha256": lock(checklist_path)["sha256"],
        "review_quiescence_receipt_sha256": lock(quiescence_path)["sha256"],
        "sealed_retrieval_receipt_sha256": lock(retrieval_path)["sha256"],
        "evidence_acceptance_index_sha256": lock(evidence_path)["sha256"],
        "promotion_receipt_sha256": lock(promotion_path)["sha256"],
        "score_prompt_sha256": lock(prompt_path)["sha256"],
        "score_schema_sha256": lock(schema_path)["sha256"],
        "formal_evidence_tree_sha256": destination["tree_sha256"],
    }
    definition = {
        "execution_lock": lock(execution_path),
        "checklist_freeze_lock": lock(checklist_path),
        "review_quiescence_receipt": lock(quiescence_path),
        "sealed_retrieval_receipt": lock(retrieval_path),
        "evidence_acceptance_index": lock(evidence_path),
        "promotion_receipt": lock(promotion_path),
        "score_prompt": lock(prompt_path),
        "score_schema": lock(schema_path),
        "formal_evidence": destination,
        "hash_graph": hash_graph,
        "join_inputs_sha256": sha256_object(hash_graph),
        "score_output_precondition": {
            "roots": [
                {"path": str(score_a.resolve()), "file_count": 0},
                {"path": str(score_b.resolve()), "file_count": 0},
            ],
            "all_empty": True,
        },
        "authorization": authorization,
    }
    fake_join = LockedArtifactResult(
        join_path, sha256_file(join_path), definition, False
    )
    monkeypatch.setattr(
        evidence_contract,
        "load_prescore_join_lock_envelope",
        lambda _: fake_join,
    )
    monkeypatch.setattr(
        evidence_contract,
        "verify_execution_lock_envelope",
        lambda **_: SimpleNamespace(lock_path=execution_path),
    )
    monkeypatch.setattr(
        evidence_contract,
        "_verify_checklist_v2_quiescence_gate",
        lambda **_: (SimpleNamespace(freeze_path=checklist_path), {}),
    )
    monkeypatch.setattr(
        evidence_contract,
        "verify_evidence_acceptance_index",
        lambda **_: LockedArtifactResult(
            evidence_path,
            sha256_file(evidence_path),
            {"sealed_retrieval_receipt": lock(retrieval_path)},
            False,
        ),
    )
    monkeypatch.setattr(
        evidence_contract,
        "verify_evidence_promotion_receipt",
        lambda **_: LockedArtifactResult(
            promotion_path,
            sha256_file(promotion_path),
            {"destination": destination},
            False,
        ),
    )

    verified = verify_prescore_join_inputs_current(
        lock_path=join_path,
        execution_lock_path=execution_path,
        checklist_freeze_lock_path=checklist_path,
        evidence_index_path=evidence_path,
        promotion_receipt_path=promotion_path,
        score_prompt_path=prompt_path,
        score_schema_path=schema_path,
        score_result_roots=(score_a, score_b),
        require_score_roots_empty=False,
    )
    assert verified.sha256 == fake_join.sha256
    (score_a / "valid-partial-score.json").write_text("{}\n", encoding="utf-8")
    verify_prescore_join_inputs_current(
        lock_path=join_path,
        execution_lock_path=execution_path,
        checklist_freeze_lock_path=checklist_path,
        evidence_index_path=evidence_path,
        promotion_receipt_path=promotion_path,
        score_prompt_path=prompt_path,
        score_schema_path=schema_path,
        score_result_roots=(score_a, score_b),
        require_score_roots_empty=False,
    )
    with pytest.raises(ContractLifecycleError, match="not empty"):
        verify_prescore_join_inputs_current(
            lock_path=join_path,
            execution_lock_path=execution_path,
            checklist_freeze_lock_path=checklist_path,
            evidence_index_path=evidence_path,
            promotion_receipt_path=promotion_path,
            score_prompt_path=prompt_path,
            score_schema_path=schema_path,
            score_result_roots=(score_a, score_b),
            require_score_roots_empty=True,
        )


@pytest.mark.parametrize(
    ("message", "mutate"),
    [
        ("requires --slot-count 3", lambda args, tmp: setattr(args, "slot_count", 2)),
        (
            "requires --tasks-per-key 949",
            lambda args, tmp: setattr(args, "tasks_per_key", 948),
        ),
        (
            "score prompt path differs",
            lambda args, tmp: setattr(args, "score_prompt", tmp / "changed.prompt.md"),
        ),
        (
            "score schema path differs",
            lambda args, tmp: setattr(
                args, "score_schema", tmp / "changed.schema.json"
            ),
        ),
    ],
)
def test_formal_score_gate_rejects_denominator_and_score_input_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    message: str,
    mutate: Any,
) -> None:
    args = _formal_score_args(tmp_path)
    mutate(args, tmp_path)
    monkeypatch.setattr(
        score_batch,
        "verify_prescore_join_inputs_current",
        lambda **_: pytest.fail(
            "join verification must not run after an early gate failure"
        ),
    )
    with pytest.raises(score_batch.AgentDojoBatchScoreError, match=message):
        score_batch.enforce_formal_score_entry_gate(args)


@pytest.mark.parametrize(
    "reason",
    ["join lock is missing", "join lock is stale", "score namespace is not empty"],
)
def test_formal_score_gate_propagates_missing_stale_and_nonempty_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reason: str,
) -> None:
    args = _formal_score_args(tmp_path)

    def fail(**_: Any) -> Any:
        raise ContractLifecycleError(reason)

    monkeypatch.setattr(score_batch, "verify_prescore_join_inputs_current", fail)
    with pytest.raises(score_batch.AgentDojoBatchScoreError, match=reason):
        score_batch.enforce_formal_score_entry_gate(args)


def test_legacy_100_case_score_paths_do_not_require_full_join(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _formal_score_args(tmp_path)
    args.evidence_root = tmp_path / "legacy/evidence"
    args.draft_root = tmp_path / "legacy/drafts"
    args.score_output_root = tmp_path / "legacy/scores"
    args.batch_root = tmp_path / "legacy/scores/_batch_runs"
    args.slot_count = 3
    args.tasks_per_key = 100
    monkeypatch.setattr(
        score_batch,
        "verify_prescore_join_inputs_current",
        lambda **_: pytest.fail("legacy scoring must not consult the 949-case join"),
    )
    assert score_batch.enforce_formal_score_entry_gate(args) is None


def test_direct_formal_score_writer_requires_batch_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(score_child.FORMAL_SCORE_SESSION_ENV, raising=False)
    monkeypatch.delenv(score_child.FORMAL_SCORE_SESSION_SHA_ENV, raising=False)
    with pytest.raises(score_child.CodexScoreError, match="batch-issued score session"):
        score_child.enforce_formal_score_write_gate(
            out_prefix=score_batch.FORMAL_SCORE_ROOTS[0] / "case/score",
            checklist_path=score_batch.FULL_DRAFT_ROOT / "case/checklist.yaml",
            evidence_dir=score_batch.FULL_EVIDENCE_ROOT / "job/adapter",
        )


def test_direct_openrouter_scorer_cannot_write_formal_namespace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = SimpleNamespace(
        out_prefix=tmp_path / "score",
        checklist=tmp_path / "checklist.yaml",
        evidence_dir=tmp_path / "evidence",
    )
    monkeypatch.setattr(openrouter_child, "parse_args", lambda: args)
    monkeypatch.setattr(
        openrouter_child.shared,
        "enforce_formal_score_write_gate",
        lambda **_: True,
    )
    with pytest.raises(
        openrouter_child.OpenRouterScoreError,
        match="cannot write the formal AgentDojo namespace",
    ):
        openrouter_child.main()


def test_direct_formal_score_writer_rejects_stale_session_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = tmp_path / "session.json"
    session.write_text("{}\n", encoding="utf-8")
    monkeypatch.setenv(score_child.FORMAL_SCORE_SESSION_ENV, str(session))
    monkeypatch.setenv(score_child.FORMAL_SCORE_SESSION_SHA_ENV, "0" * 64)
    with pytest.raises(score_child.CodexScoreError, match="session SHA-256 mismatch"):
        score_child.enforce_formal_score_write_gate(
            out_prefix=score_batch.FORMAL_SCORE_ROOTS[0] / "case/score",
            checklist_path=score_batch.FULL_DRAFT_ROOT / "case/checklist.yaml",
            evidence_dir=score_batch.FULL_EVIDENCE_ROOT / "job/adapter",
        )


def test_direct_formal_writer_rechecks_per_task_checklist_and_evidence_hashes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from evidence_system.contracts import agentdojo_full_evidence as evidence_contract
    from evidence_system.contracts import (
        agentdojo_full_experiment as experiment_contract,
    )

    draft_root = tmp_path / "drafts"
    namespace_root = tmp_path / "formal_namespace"
    evidence_root = namespace_root / "full/agentdojo"
    score_root_a = tmp_path / "scores-a"
    score_root_b = tmp_path / "scores-b"
    checklist = draft_root / "case/checklist.yaml"
    evidence = evidence_root / "job/adapter"
    out_prefix = score_root_a / "case/score"
    checklist.parent.mkdir(parents=True)
    evidence.mkdir(parents=True)
    checklist.write_text("case_unit_id: case\n", encoding="utf-8")
    (evidence / "raw_run.json").write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(experiment_contract, "DEFAULT_DRAFT_ROOT", draft_root)
    monkeypatch.setattr(
        experiment_contract,
        "DEFAULT_RESULT_NAMESPACE_LOCK",
        namespace_root / "NAMESPACE_LOCK.json",
    )
    monkeypatch.setattr(
        experiment_contract,
        "DEFAULT_SCORE_NAMESPACE_ROOTS",
        (score_root_a, score_root_b),
    )
    prompt_binding = {
        "path": str(score_child.PROMPT_PATH.resolve()),
        "sha256": sha256_file(score_child.PROMPT_PATH),
    }
    schema_binding = {
        "path": str(score_child.SCHEMA_PATH.resolve()),
        "sha256": sha256_file(score_child.SCHEMA_PATH),
    }
    authorization = {
        "case_count": 949,
        "agents_per_case": 3,
        "score_task_count": 2847,
        "tasks_per_key": 949,
        "slot_count": 3,
        "unresolved_evidence": 0,
        "unresolved_checklists": 0,
    }
    task = {
        "task_index": 0,
        "out_prefix": str(out_prefix.resolve()),
        "checklist_path": str(checklist.resolve()),
        "checklist_sha256": sha256_file(checklist),
        "evidence_dir": str(evidence.resolve()),
        "evidence_tree_sha256": sha256_path(evidence),
    }
    plan_path = tmp_path / "task_plan.json"
    plan = {
        "task_count": 2847,
        "tasks_per_key": 949,
        "selected_agents": ["agent_a", "agent_b", "agent_c"],
        "tasks": [task],
    }
    _write_json(plan_path, plan)
    join_path = tmp_path / "prescore_join_lock.json"
    join_path.write_text("{}\n", encoding="utf-8")
    join = LockedArtifactResult(
        path=join_path,
        sha256=sha256_file(join_path),
        definition={
            "score_prompt": prompt_binding,
            "score_schema": schema_binding,
            "authorization": authorization,
        },
        created=False,
    )
    monkeypatch.setattr(
        evidence_contract, "load_prescore_join_lock_envelope", lambda _: join
    )
    session_path = tmp_path / "formal_score_session.json"
    session = {
        "schema_version": "agentdojo_full_score_session/v1",
        "join_lock": {"path": str(join_path), "sha256": join.sha256},
        "task_plan": {"path": str(plan_path), "sha256": sha256_file(plan_path)},
        "tasks_sha256": sha256_object(plan["tasks"]),
        "score_prompt": prompt_binding,
        "score_schema": schema_binding,
        "score_output_root": str(score_root_a.resolve()),
        "formal_evidence_root": str(evidence_root.resolve()),
        "authorization": authorization,
    }
    _write_json(session_path, session)
    monkeypatch.setenv(score_child.FORMAL_SCORE_SESSION_ENV, str(session_path))
    monkeypatch.setenv(
        score_child.FORMAL_SCORE_SESSION_SHA_ENV, sha256_file(session_path)
    )

    score_child.enforce_formal_score_write_gate(
        out_prefix=out_prefix,
        checklist_path=checklist,
        evidence_dir=evidence,
    )
    (evidence / "raw_run.json").write_text('{"drift": true}\n', encoding="utf-8")
    with pytest.raises(score_child.CodexScoreError, match="evidence tree drifted"):
        score_child.enforce_formal_score_write_gate(
            out_prefix=out_prefix,
            checklist_path=checklist,
            evidence_dir=evidence,
        )


def test_formal_resume_reuses_only_valid_same_session_scores_and_rejects_extras(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    score_root = tmp_path / "scores"
    other_root = tmp_path / "scores-other"
    batch_dir = score_root / "_batch_runs/batch"
    batch_dir.mkdir(parents=True)
    (batch_dir / "task_plan.json").write_text("{}\n", encoding="utf-8")
    (batch_dir / "formal_score_session.json").write_text("{}\n", encoding="utf-8")
    checklist = tmp_path / "drafts/case/checklist.yaml"
    evidence = tmp_path / "evidence/job/adapter"
    checklist.parent.mkdir(parents=True)
    evidence.mkdir(parents=True)
    checklist.write_text("case_unit_id: case\n", encoding="utf-8")
    (evidence / "raw_run.json").write_text("{}\n", encoding="utf-8")
    out_prefix = score_root / "full/agentdojo/run/case/model/score"
    out_prefix.parent.mkdir(parents=True)
    score_file = out_prefix.with_suffix(".json")
    score_file.write_text("{}\n", encoding="utf-8")
    task = score_batch.ScoreTask(
        task_index=0,
        key_slot=1,
        case_unit_id="case",
        checklist_path=checklist,
        evidence_dir=evidence,
        run_dir_name="run-agent_a",
        run_id="run",
        agent_id="Agent A",
        out_prefix=out_prefix,
    )
    authorization = score_batch.FormalScoreAuthorization(
        join=_fake_join(tmp_path),
        score_output_root=score_root.resolve(),
        evidence_root=evidence.parent.parent.resolve(),
        draft_root=checklist.parent.parent.resolve(),
        score_prompt=score_child.PROMPT_PATH.resolve(),
        score_schema=score_child.SCHEMA_PATH.resolve(),
        resume_session_path=batch_dir / "formal_score_session.json",
    )
    monkeypatch.setattr(score_batch, "FORMAL_SCORE_ROOTS", (score_root, other_root))
    monkeypatch.setattr(score_batch, "existing_score_is_valid", lambda *_, **__: True)
    monkeypatch.setattr(
        score_batch, "_manifest_declared_output_files", lambda _: {score_file.resolve()}
    )
    completed = score_batch.audit_formal_score_resume_outputs(
        authorization=authorization,
        tasks=[task],
        batch_dir=batch_dir,
        model="model",
        reasoning_effort="high",
        session_path=batch_dir / "formal_score_session.json",
        session_sha256="1" * 64,
    )
    assert completed == {0}

    (score_root / "unbound.txt").write_text("unexpected\n", encoding="utf-8")
    with pytest.raises(score_batch.AgentDojoBatchScoreError, match="unbound files"):
        score_batch.audit_formal_score_resume_outputs(
            authorization=authorization,
            tasks=[task],
            batch_dir=batch_dir,
            model="model",
            reasoning_effort="high",
            session_path=batch_dir / "formal_score_session.json",
            session_sha256="1" * 64,
        )


def test_formal_resume_rejects_session_from_an_old_join(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    score_root = tmp_path / "scores"
    batch_root = score_root / "_batch_runs"
    batch_dir = batch_root / "batch"
    batch_dir.mkdir(parents=True)
    join = _fake_join(tmp_path)
    authorization = score_batch.FormalScoreAuthorization(
        join=join,
        score_output_root=score_root.resolve(),
        evidence_root=(tmp_path / "evidence").resolve(),
        draft_root=(tmp_path / "drafts").resolve(),
        score_prompt=score_child.PROMPT_PATH.resolve(),
        score_schema=score_child.SCHEMA_PATH.resolve(),
        resume_session_path=batch_dir / "formal_score_session.json",
    )
    expected_join = {
        "path": score_batch.repo_relative_or_absolute(join.path),
        "sha256": join.sha256,
    }
    plan_path = batch_dir / "task_plan.json"
    plan = {
        "tasks": [],
        "task_count": 2847,
        "tasks_per_key": 949,
        "selected_agents": ["agent_a", "agent_b", "agent_c"],
        "model": "model",
        "reasoning_effort": "high",
        "batch_root": str(batch_dir.resolve()),
        "draft_root": str(authorization.draft_root),
        "evidence_root": str(authorization.evidence_root),
        "score_output_root": str(score_root.resolve()),
        "formal_prescore_join": expected_join,
    }
    _write_json(plan_path, plan)
    session_path = batch_dir / "formal_score_session.json"
    session = {
        "schema_version": "agentdojo_full_score_session/v1",
        "join_lock": {**expected_join, "sha256": "0" * 64},
        "task_plan": {"path": str(plan_path), "sha256": sha256_file(plan_path)},
        "tasks_sha256": sha256_object([]),
        "score_prompt": {
            "path": score_batch.repo_relative_or_absolute(authorization.score_prompt),
            "sha256": sha256_file(authorization.score_prompt),
        },
        "score_schema": {
            "path": score_batch.repo_relative_or_absolute(authorization.score_schema),
            "sha256": sha256_file(authorization.score_schema),
        },
        "score_output_root": str(score_root.resolve()),
        "formal_evidence_root": str(authorization.evidence_root),
        "formal_draft_root": str(authorization.draft_root),
        "model": "model",
        "reasoning_effort": "high",
        "authorization": join.definition["authorization"],
    }
    _write_json(session_path, session)
    plan_path.chmod(0o444)
    session_path.chmod(0o444)
    monkeypatch.setattr(
        score_batch, "audit_formal_score_resume_outputs", lambda **_: set()
    )
    args = SimpleNamespace(batch_root=batch_root)
    with pytest.raises(score_batch.AgentDojoBatchScoreError, match="stale join lock"):
        score_batch.load_formal_resume_session(
            args=args,
            authorization=authorization,
            tasks=[],
            model="model",
            reasoning_effort="high",
        )
    session_path.chmod(0o644)
    plan_path.chmod(0o644)


def test_promotion_reservation_gate_allows_only_exact_namespace_marker(
    tmp_path: Path,
) -> None:
    namespace = tmp_path / "results/namespaces/agentdojo_full_v1.2.2_direct"
    evidence_root = namespace / "full/agentdojo"
    evidence_root.mkdir(parents=True)
    marker = {
        "schema_version": "result_namespace_lock/v1",
        "result_namespace": "agentdojo_full_v1.2.2_direct",
        "experiment_manifest_path": "experiments/agentdojo_full_v1.2.2_direct/experiment_manifest.yaml",
        "formal_result_root": str(evidence_root.resolve()),
        "legacy_result_root": "results/full/agentdojo",
        "legacy_result_root_must_not_be_modified": True,
        "status": "reserved_no_formal_runs_yet",
    }
    _write_json(namespace / "NAMESPACE_LOCK.json", marker)
    accepted = _require_reserved_formal_namespace(
        namespace_root=namespace,
        formal_evidence_root=evidence_root,
    )
    assert accepted["path"].endswith("NAMESPACE_LOCK.json")

    (namespace / "unexpected.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ContractLifecycleError, match="must contain only"):
        _require_reserved_formal_namespace(
            namespace_root=namespace,
            formal_evidence_root=evidence_root,
        )
