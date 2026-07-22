from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from evidence_system.contracts import appworld_draft_candidate_repair as repair
from evidence_system.contracts.appworld_draft_candidate_repair import (
    EXPECTED_MAX_PARALLEL,
    EXPECTED_REPAIR_CASE_IDS,
    EXPECTED_REPAIR_SUPPLEMENT_SHA256,
    EXPECTED_TOKEN_BUDGETS,
    prepare_candidate_repair_lock,
    load_repair_case_ids,
    run_candidate_repairs,
    validate_candidate_repair_lock,
    validate_candidate_support,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.contracts.appworld_draft_acceptance import _validate_repair_lock as validate_promotion_repair_lock


ROOT = Path(__file__).resolve().parents[2]
FORMAL_ROOT = ROOT / "experiments/appworld_full_test_extension_v1/draft_runs/codex-gpt-5.4-high-support-v2"
PACKET_ROOT = ROOT / "experiments/appworld_full_test_extension_v1/case_packets/appworld"


def _write_ids(path: Path, ids: tuple[str, ...] = EXPECTED_REPAIR_CASE_IDS) -> None:
    path.write_text("\n".join(ids) + "\n", encoding="utf-8")


def test_subset_loader_requires_exact_frozen_12_without_duplicates(tmp_path: Path) -> None:
    valid = tmp_path / "valid.txt"
    _write_ids(valid)
    assert load_repair_case_ids(valid) == EXPECTED_REPAIR_CASE_IDS

    reordered = tmp_path / "reordered.txt"
    _write_ids(reordered, tuple(reversed(EXPECTED_REPAIR_CASE_IDS)))
    with pytest.raises(ContractLifecycleError, match="deterministic order"):
        load_repair_case_ids(reordered)

    missing = tmp_path / "missing.json"
    missing.write_text(json.dumps(list(EXPECTED_REPAIR_CASE_IDS[:-1])), encoding="utf-8")
    with pytest.raises(ContractLifecycleError, match="exact frozen 12"):
        load_repair_case_ids(missing)

    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text(
        json.dumps([*EXPECTED_REPAIR_CASE_IDS[:-1], EXPECTED_REPAIR_CASE_IDS[0]]),
        encoding="utf-8",
    )
    with pytest.raises(ContractLifecycleError, match="duplicates"):
        load_repair_case_ids(duplicate)


def test_prepare_lock_rejects_existing_candidate_namespace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(repair, "_require_repair_lock_location", lambda *_: None)
    ids_path = tmp_path / "repair_ids.txt"
    _write_ids(ids_path)
    candidate_root = tmp_path / "candidates"
    candidate_root.mkdir()
    (candidate_root / "leftover.txt").write_text("not clean", encoding="utf-8")

    with pytest.raises(ContractLifecycleError, match="must be absent"):
        prepare_candidate_repair_lock(
            subset_ids_path=ids_path,
            repair_lock_path=tmp_path / "draft_repair_lock.json",
            candidate_output_root=candidate_root,
        )


def test_prepare_and_validate_lock_freezes_formal_tree_and_repair_prompt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(repair, "_require_repair_lock_location", lambda *_: None)
    ids_path = tmp_path / "repair_ids.txt"
    _write_ids(ids_path)
    repair_lock = tmp_path / "provenance" / "draft_repair_lock.json"
    candidate_root = tmp_path / "candidates"

    result = prepare_candidate_repair_lock(
        subset_ids_path=ids_path,
        repair_lock_path=repair_lock,
        candidate_output_root=candidate_root,
    )
    context = validate_candidate_repair_lock(repair_lock)
    lock = json.loads(repair_lock.read_text(encoding="utf-8"))

    assert result["case_count"] == 12
    assert context.formal_cases_root == FORMAL_ROOT / "cases"
    assert context.candidate_output_root == candidate_root
    assert [case["case_unit_id"] for case in context.cases] == list(EXPECTED_REPAIR_CASE_IDS)
    assert lock["prompt_deviation"]["repair_supplement_sha256"] == EXPECTED_REPAIR_SUPPLEMENT_SHA256
    assert lock["execution"]["max_parallel"] == lock["execution"]["large_max_parallel"] == 8
    assert lock["status"] == "locked_pre_repair"
    assert lock["schema_version"] == "appworld_draft_repair_lock.v1"
    assert lock["formal_cases_pre_repair_tree_sha256"] == result["formal_cases_tree_sha256"]
    assert len(lock["original_cases"]) == 12
    assert all(set(item["canonical_file_sha256"]) == {
        "api_response.json",
        "checklist.json",
        "checklist.yaml",
        "llm_call.json",
        "reasoning_summary.txt",
        "stderr.log",
        "stdout.log",
    } for item in lock["original_cases"])
    assert lock["lifecycle"] == {
        "automatic_promotion_supported": False,
        "formal_namespace_write_allowed": False,
        "output_status": "candidate_generated/review_required",
        "promotion_performed": False,
    }
    promotion_lock_view = validate_promotion_repair_lock(
        lock=lock,
        formal_lock_file=FORMAL_ROOT / "provenance/draft_run_lock.json",
        cases_root=FORMAL_ROOT / "cases",
        original_batch=lock["original_batch"],
        repair_inputs=lock["repair_inputs"],
        candidate_root=candidate_root,
        configuration={
            "provider": "codex",
            "llm_call_provider": "codex_cli",
            "model": "gpt-5.4",
            "reasoning_effort": "high",
            "auth_mode": "codex_login",
            "codex_sandbox": "read-only",
            "max_parallel": 8,
        },
    )
    assert set(promotion_lock_view) == set(EXPECTED_REPAIR_CASE_IDS)


def test_candidate_orchestrator_calls_frozen_process_case_with_size_aware_lanes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(repair, "_require_repair_lock_location", lambda *_: None)
    ids_path = tmp_path / "repair_ids.txt"
    _write_ids(ids_path)
    repair_lock = tmp_path / "provenance" / "draft_repair_lock.json"
    candidate_root = tmp_path / "candidates"
    prepare_candidate_repair_lock(
        subset_ids_path=ids_path,
        repair_lock_path=repair_lock,
        candidate_output_root=candidate_root,
    )

    calls: list[dict[str, Any]] = []
    active = 0
    max_active = 0
    call_lock = threading.Lock()

    def fake_process_case(**kwargs: Any) -> dict[str, Any]:
        nonlocal active, max_active
        with call_lock:
            active += 1
            max_active = max(max_active, active)
            calls.append(kwargs)
        time.sleep(0.01)
        with call_lock:
            active -= 1
        case_info = kwargs["case_info"]
        return {
            "case_unit_dir": case_info.path.parent.name,
            "case_packet": str(case_info.path),
            "case_packet_size_bytes": case_info.size_bytes,
            "lane": kwargs["lane"],
            "status": "failed",
            "attempts": [],
            "quality_warnings": [],
        }

    summary = run_candidate_repairs(
        repair_lock,
        process_case_fn=fake_process_case,
        codex_status_fn=lambda: "Logged in using ChatGPT",
    )

    assert len(calls) == 12
    assert 1 < max_active <= EXPECTED_MAX_PARALLEL
    assert {call["case_info"].path for call in calls} == {
        PACKET_ROOT / case_id / "case_packet.md" for case_id in EXPECTED_REPAIR_CASE_IDS
    }
    assert all(call["provider"] == "codex" for call in calls)
    assert all(call["model"] == "gpt-5.4" for call in calls)
    assert all(call["reasoning_effort"] == "high" for call in calls)
    assert all(call["codex_sandbox"] == "read-only" for call in calls)
    assert all(call["token_budgets"] == list(EXPECTED_TOKEN_BUDGETS) for call in calls)
    assert all(call["output_root"] == candidate_root for call in calls)
    assert all(call["force"] is False for call in calls)
    oversized = [call for call in calls if call["lane"] == "oversized"]
    regular = [call for call in calls if call["lane"] == "regular"]
    assert [call["case_info"].path.parent.name for call in oversized] == ["d8e490b_3"]
    assert len(regular) == 11
    assert all(call["codex_timeout_seconds"] == 1800 for call in regular)
    assert oversized[0]["codex_timeout_seconds"] == 3600
    assert summary["regular_case_count"] == 11
    assert summary["oversized_case_count"] == 1
    assert summary["promotion_performed"] is False
    assert summary["status"] == "candidate_generation_failed_validation"
    assert not (FORMAL_ROOT / "cases" / "_candidate_summary.json").exists()


def test_authoritative_support_gate_rejects_source_local_out_of_range_location() -> None:
    case_id = "652485c_2"
    with pytest.raises(ContractLifecycleError, match="support location does not resolve"):
        validate_candidate_support(
            checklist_path=FORMAL_ROOT / "cases" / case_id / "checklist.json",
            packet_path=PACKET_ROOT / case_id / "case_packet.md",
            case_id=case_id,
        )


def test_candidate_root_inventory_requires_exact_flat_12_plus_metadata(tmp_path: Path) -> None:
    root = tmp_path / "candidates"
    root.mkdir()
    for case_id in EXPECTED_REPAIR_CASE_IDS:
        case_dir = root / case_id
        case_dir.mkdir()
        (case_dir / "artifact.txt").write_text("safe\n", encoding="utf-8")
    for name in repair._ROOT_METADATA_NAMES:
        (root / name).write_text("{}\n", encoding="utf-8")

    inventory = repair._candidate_cases_inventory(root, require_metadata=True)
    assert inventory["exact_layout"] is True
    repair._validate_candidate_root_exact(root)

    (root / "unexpected_empty_dir").mkdir()
    with pytest.raises(ContractLifecycleError, match="exactly 12"):
        repair._validate_candidate_root_exact(root)


def test_formal_snapshot_detects_directory_only_and_symlink_mutation(tmp_path: Path) -> None:
    formal = tmp_path / "formal"
    formal.mkdir()
    (formal / "case").mkdir()
    (formal / "case" / "draft.json").write_text("{}\n", encoding="utf-8")
    strict = repair._strict_tree_inventory(formal, label="formal")
    context = repair.CandidateRepairContext(
        repair_lock_path=tmp_path / "lock.json",
        repair_lock_sha256="0" * 64,
        formal_lock_path=tmp_path / "formal-lock.json",
        formal_cases_root=formal,
        formal_cases_tree_sha256=repair.sha256_path(formal),
        formal_cases_strict_tree_sha256=strict["tree_sha256"],
        formal_cases_file_count=strict["file_count"],
        formal_cases_directory_count=strict["directory_count"],
        formal_cases_size_bytes=strict["size_bytes"],
        case_packet_root=tmp_path / "packets",
        candidate_output_root=tmp_path / "candidates",
        prompt_supplement=tmp_path / "supplement.md",
        cases=(),
    )
    repair._validate_formal_snapshot(context, label="baseline")
    (formal / "empty").mkdir()
    with pytest.raises(ContractLifecycleError, match="strict tree"):
        repair._validate_formal_snapshot(context, label="after empty directory")
    (formal / "empty").rmdir()
    (formal / "broken-link").symlink_to(formal / "missing")
    with pytest.raises(ContractLifecycleError, match="symlink"):
        repair._validate_formal_snapshot(context, label="after symlink")


def test_codex_event_command_gate_rejects_external_workspace_reads() -> None:
    workspace = "/tmp/case-checklist-codex-test"
    safe = {
        "codex_cli": {
            "command": ["codex", "exec", "--cd", workspace],
            "events": [
                {"item": {"type": "command_execution", "command": "/bin/zsh -lc 'cat case_packet.md'"}},
            ],
        }
    }
    assert repair._validate_codex_event_commands(api_response=safe, case_id="case") == 1

    unsafe = json.loads(json.dumps(safe))
    unsafe["codex_cli"]["events"][0]["item"]["command"] = "/bin/zsh -lc 'rg needle /Users/example/results'"
    with pytest.raises(ContractLifecycleError, match="outside the isolated workspace"):
        repair._validate_codex_event_commands(api_response=unsafe, case_id="case")


def test_minimal_subprocess_environment_removes_secret_variables_and_restores(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sensitive-test-value-not-a-real-key")
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    monkeypatch.setenv("HOME", "/tmp/test-home")
    with repair._minimal_subprocess_environment():
        assert "OPENAI_API_KEY" not in repair.os.environ
        assert set(repair.os.environ) <= set(repair._MINIMAL_ENV_ALLOWLIST)
    assert repair.os.environ["OPENAI_API_KEY"] == "sensitive-test-value-not-a-real-key"


def test_repair_lock_anchor_uses_fixed_path_bytes_when_keyword_is_omitted(tmp_path: Path) -> None:
    repair_lock = tmp_path / "draft_repair_lock.json"
    repair_lock.write_text('{"schema_version":"test"}\n', encoding="utf-8")

    assert repair._resolve_repair_lock_anchor(repair_lock, None) == repair.sha256_file(repair_lock)


def test_validate_existing_candidates_accepts_legacy_single_argument_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repair_lock = tmp_path / "draft_repair_lock.json"
    repair_lock.write_text('{"schema_version":"test"}\n', encoding="utf-8")
    entered: list[tuple[Path, bool]] = []

    def stop_after_anchor(path: str | Path, *, require_clean_candidate_root: bool = False) -> Any:
        entered.append((Path(path), require_clean_candidate_root))
        raise ContractLifecycleError("entered candidate lock validation")

    monkeypatch.setattr(repair, "validate_candidate_repair_lock", stop_after_anchor)
    with pytest.raises(ContractLifecycleError, match="entered candidate lock validation"):
        repair.validate_existing_candidates(repair_lock)
    assert entered == [(repair_lock, False)]


def test_explicit_repair_lock_anchor_rejects_mismatch_before_lock_parse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repair_lock = tmp_path / "draft_repair_lock.json"
    repair_lock.write_text('{"schema_version":"test"}\n', encoding="utf-8")
    entered = False

    def unexpected_parse(*_args: Any, **_kwargs: Any) -> Any:
        nonlocal entered
        entered = True
        raise AssertionError("lock parser must not run after an explicit anchor mismatch")

    monkeypatch.setattr(repair, "validate_candidate_repair_lock", unexpected_parse)
    with pytest.raises(ContractLifecycleError, match="caller-anchored pre-lock hash"):
        repair.validate_existing_candidates(
            repair_lock,
            expected_repair_lock_sha256="0" * 64,
        )
    assert entered is False
