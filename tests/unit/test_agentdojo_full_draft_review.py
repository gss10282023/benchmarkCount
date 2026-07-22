from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from neurips_ed_track_minimal.scripts import run_agentdojo_full_draft_review as lifecycle  # noqa: E402


FROZEN_MODEL = "gpt-5.6-sol"
FROZEN_REASONING_EFFORT = "xhigh"
FROZEN_MAX_PARALLEL = 6


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _write_json(path: Path, value: Any) -> Path:
    return _write(path, json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def _prepared_args(argv: list[str] | None = None) -> Namespace:
    args = lifecycle.parse_args(argv or [])
    lifecycle._prepare_paths(args)
    return args


def _case(tmp_path: Path) -> lifecycle.CaseInput:
    case_unit_id = "v1.2.2:banking:user_task_0:injection_task_2"
    packet = _write(tmp_path / "packet" / "case_packet.md", "# packet\n")
    return lifecycle.CaseInput(
        case_unit_id=case_unit_id,
        task_id="banking:user_task_0:injection_task_2",
        suite="banking",
        directory_name=lifecycle._safe_case_dir(case_unit_id),
        case_packet_path=packet,
    )


def _case_args(tmp_path: Path, *, max_review_rounds: int = 3) -> Namespace:
    return Namespace(
        canary=False,
        output_root=tmp_path / "drafts",
        max_review_rounds=max_review_rounds,
        composed_draft_prompt=_write(tmp_path / "inputs" / "draft.prompt.md", "draft prompt\n"),
        checklist_schema=_write_json(tmp_path / "inputs" / "checklist.schema.json", {}),
        review_prompt=_write(tmp_path / "inputs" / "review.prompt.md", "review prompt\n"),
        review_schema=_write_json(tmp_path / "inputs" / "review.schema.json", {}),
        model=FROZEN_MODEL,
        reasoning_effort=FROZEN_REASONING_EFFORT,
        codex_sandbox="read-only",
        codex_timeout_seconds=1800,
    )


def _initial_checklist(case: lifecycle.CaseInput) -> dict[str, Any]:
    return {
        "schema_version": "case_checklist_v1",
        "case_unit_id": case.case_unit_id,
        "domain": "agentdojo",
        "task_id": case.task_id,
        "native": {"marker": "initial"},
        "stronger": {"additional_conditions": []},
    }


def _install_state_machine_fakes(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[int, Path, dict[str, Any]]]:
    review_calls: list[tuple[int, Path, dict[str, Any]]] = []

    def validate_checklist(
        path: Path,
        *,
        case: lifecycle.CaseInput,
        schema: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        del case, schema
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(value, dict)
        return value, {"status": "pass", "findings": []}

    monkeypatch.setattr(lifecycle, "_reusable_review", lambda *args, **kwargs: False)
    monkeypatch.setattr(lifecycle, "_validate_checklist", validate_checklist)
    monkeypatch.setattr(lifecycle, "_validate_review_receipt_schema", lambda *args, **kwargs: None)
    return review_calls


def test_frozen_execution_defaults_are_strict_and_valid() -> None:
    args = _prepared_args()

    assert (args.max_parallel, args.model, args.reasoning_effort) == (
        FROZEN_MAX_PARALLEL,
        FROZEN_MODEL,
        FROZEN_REASONING_EFFORT,
    )
    assert args.codex_sandbox == "read-only"
    lifecycle._validate_args(args)


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["--max-parallel", "5"], "exactly 6 workers"),
        (["--model", "gpt-5.6"], "model is gpt-5.6-sol"),
        (["--reasoning-effort", "high"], "reasoning_effort=xhigh"),
    ],
)
def test_frozen_execution_configuration_rejects_drift(argv: list[str], message: str) -> None:
    with pytest.raises(lifecycle.DraftReviewLifecycleError, match=message):
        lifecycle._validate_args(_prepared_args(argv))


def test_full_and_four_suite_canary_selection_have_exact_denominators(tmp_path: Path) -> None:
    cases = [
        lifecycle.CaseInput(
            case_unit_id=f"v1.2.2:{suite}:user_task_{index}:injection_task_0",
            task_id=f"{suite}:user_task_{index}:injection_task_0",
            suite=suite,
            directory_name=f"case_{index:04d}",
            case_packet_path=tmp_path / f"case_{index:04d}" / "case_packet.md",
        )
        for index in range(lifecycle.EXPECTED_CASES)
        for suite in (lifecycle.EXPECTED_SUITES[index % len(lifecycle.EXPECTED_SUITES)],)
    ]

    full = lifecycle._selected_cases(cases, canary=False)
    canary = lifecycle._selected_cases(cases, canary=True)

    assert lifecycle.EXPECTED_CASES == 949
    assert len(full) == 949
    assert [case.case_unit_id for case in full] == [case.case_unit_id for case in cases]
    assert len(canary) == 4
    assert tuple(case.suite for case in canary) == ("workspace", "travel", "banking", "slack")
    assert canary == cases[:4]


def test_canary_selection_fails_closed_when_a_suite_is_missing(tmp_path: Path) -> None:
    cases = [
        lifecycle.CaseInput(
            case_unit_id=f"v1.2.2:{suite}:user_task_0:injection_task_0",
            task_id=f"{suite}:user_task_0:injection_task_0",
            suite=suite,
            directory_name=suite,
            case_packet_path=tmp_path / suite / "case_packet.md",
        )
        for suite in lifecycle.EXPECTED_SUITES[:-1]
    ]

    with pytest.raises(lifecycle.DraftReviewLifecycleError, match="canary suite missing: slack"):
        lifecycle._selected_cases(cases, canary=True)


def test_budget_is_planned_against_all_949_cases() -> None:
    args = Namespace(max_parallel=FROZEN_MAX_PARALLEL, max_review_rounds=3)

    plan = lifecycle._budget_plan(args, input_lock_sha256="input-lock-sha256")

    assert plan["denominator"] == 949
    assert plan["strictly_reusable_legacy_drafts"] == 0
    assert plan["new_drafts_required"] == 949
    assert plan["minimum_generation_codex_exec_calls"] == 949
    assert plan["minimum_review_codex_exec_calls"] == 949
    assert plan["minimum_total_codex_exec_calls"] == 1898
    assert plan["max_parallel"] == 6
    assert plan["acceptance_targets"] == {
        "case_packets": 949,
        "source_entries": 949,
        "valid_drafts": 949,
        "reviewed_locked": 949,
        "unresolved_drafts": 0,
    }


def test_direct_acceptance_finishes_in_one_fresh_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = _case_args(tmp_path)
    case = _case(tmp_path)
    case_dir = args.output_root / case.directory_name
    checklist_path = _write(
        case_dir / "checklist.yaml",
        yaml.safe_dump(_initial_checklist(case), sort_keys=False),
    )
    review_calls = _install_state_machine_fakes(monkeypatch)

    def accept_review(_args: Namespace, **kwargs: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        path = kwargs["checklist_path"]
        body = yaml.safe_load(path.read_text(encoding="utf-8"))
        review_calls.append((kwargs["round_index"], path, body))
        return {"decision": "accept"}, {"round": kwargs["round_index"], "decision": "accept"}

    monkeypatch.setattr(lifecycle, "_run_model_review", accept_review)

    result = lifecycle._review_one_case(
        args,
        case=case,
        checklist_schema={},
        review_schema={},
        reviewer_config={"provider": "codex_cli"},
        run_id="test-run",
    )

    assert result == {
        "case_unit_id": case.case_unit_id,
        "status": "accepted",
        "review_rounds": 1,
        "revised": False,
    }
    assert [(round_index, path) for round_index, path, _ in review_calls] == [(1, checklist_path)]


def test_revision_is_never_accepted_without_a_fresh_second_model_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = _case_args(tmp_path)
    case = _case(tmp_path)
    case_dir = args.output_root / case.directory_name
    original_path = _write(
        case_dir / "checklist.yaml",
        yaml.safe_dump(_initial_checklist(case), sort_keys=False),
    )
    review_calls = _install_state_machine_fakes(monkeypatch)
    revision = {
        "native": {"marker": "model-revised"},
        "stronger": {"additional_conditions": []},
    }

    def revise_then_accept(_args: Namespace, **kwargs: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        path = kwargs["checklist_path"]
        body = yaml.safe_load(path.read_text(encoding="utf-8"))
        review_calls.append((kwargs["round_index"], path, body))
        if kwargs["round_index"] == 1:
            return (
                {"decision": "revise", "revised_checklist": revision},
                {"round": 1, "decision": "revise"},
            )
        return {"decision": "accept"}, {"round": 2, "decision": "accept"}

    monkeypatch.setattr(lifecycle, "_run_model_review", revise_then_accept)

    result = lifecycle._review_one_case(
        args,
        case=case,
        checklist_schema={},
        review_schema={},
        reviewer_config={"provider": "codex_cli"},
        run_id="test-run",
    )

    assert result == {
        "case_unit_id": case.case_unit_id,
        "status": "accepted",
        "review_rounds": 2,
        "revised": True,
    }
    assert [round_index for round_index, _, _ in review_calls] == [1, 2]
    assert review_calls[0][1] == original_path
    assert review_calls[1][1] != original_path
    assert review_calls[1][1].name == "round_01.revised_checklist.yaml"
    assert review_calls[1][2]["native"] == {"marker": "model-revised"}
    final = yaml.safe_load(original_path.read_text(encoding="utf-8"))
    assert final["native"] == {"marker": "model-revised"}
    lifecycle_receipt = lifecycle._load_mapping(case_dir / "review_lifecycle.json")
    assert lifecycle_receipt["review_rounds"] == 2
    assert lifecycle_receipt["revised"] is True


def test_generation_receipt_stale_hash_fails_closed(tmp_path: Path) -> None:
    args = _case_args(tmp_path)
    case = _case(tmp_path)
    case_dir = args.output_root / case.directory_name
    generated_yaml = _write(case_dir / "generated_checklist.yaml", "generated: true\n")
    generated_json = _write_json(case_dir / "generated_checklist.json", {"generated": True})
    llm_call = _write_json(
        case_dir / "llm_call.json",
        {
            "schema_version": "llm_call/v1",
            "provider": "codex_cli",
            "case_unit_id": case.case_unit_id,
            "model": FROZEN_MODEL,
            "response_metadata": {
                "auth_mode": "codex_login",
                "reasoning_effort": FROZEN_REASONING_EFFORT,
                "max_output_tokens_enforced": False,
            },
        },
    )
    api_response = _write_json(case_dir / "api_response.json", {"ok": True})
    reasoning_summary = _write(case_dir / "reasoning_summary.txt", "summary\n")
    config_hash = "config-hash"
    input_lock_hash = "input-lock-hash"

    receipt = {
        "schema_version": "case_checklist_generation/v1",
        "case_unit_id": case.case_unit_id,
        "case_packet_path": lifecycle._display(case.case_packet_path),
        "case_packet_sha256": lifecycle._sha256_file(case.case_packet_path),
        "checklist_path": lifecycle._display(generated_yaml),
        "checklist_sha256": lifecycle._sha256_file(generated_yaml),
        "checklist_json_path": lifecycle._display(generated_json),
        "checklist_json_sha256": lifecycle._sha256_file(generated_json),
        "llm_call_path": lifecycle._display(llm_call),
        "llm_call_sha256": lifecycle._sha256_file(llm_call),
        "api_response_path": lifecycle._display(api_response),
        "api_response_sha256": lifecycle._sha256_file(api_response),
        "reasoning_summary_path": lifecycle._display(reasoning_summary),
        "reasoning_summary_sha256": lifecycle._sha256_file(reasoning_summary),
        "composed_draft_prompt_path": lifecycle._display(args.composed_draft_prompt),
        "composed_draft_prompt_sha256": lifecycle._sha256_file(args.composed_draft_prompt),
        "checklist_schema_path": lifecycle._display(args.checklist_schema),
        "checklist_schema_sha256": lifecycle._sha256_file(args.checklist_schema),
        "resolved_config_sha256": config_hash,
        "input_lock_sha256": input_lock_hash,
        "provider": "codex_cli",
        "auth_mode": "codex_login",
        "model": FROZEN_MODEL,
        "reasoning_effort": FROZEN_REASONING_EFFORT,
    }
    _write_json(case_dir / "generation.json", receipt)

    assert lifecycle._validate_generation_receipt(
        args,
        case=case,
        case_dir=case_dir,
        config_sha256=config_hash,
        input_lock_sha256=input_lock_hash,
    ) == receipt

    _write_json(api_response, {"ok": False})
    with pytest.raises(lifecycle.DraftReviewLifecycleError, match="api_response_sha256 is stale"):
        lifecycle._validate_generation_receipt(
            args,
            case=case,
            case_dir=case_dir,
            config_sha256=config_hash,
            input_lock_sha256=input_lock_hash,
        )


def test_review_receipt_stale_checklist_hash_is_not_reused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = _case_args(tmp_path)
    case = _case(tmp_path)
    case_dir = args.output_root / case.directory_name
    checklist_path = _write(
        case_dir / "checklist.yaml",
        yaml.safe_dump(_initial_checklist(case), sort_keys=False),
    )
    reviewer_config = {"provider": "codex_cli", "model": FROZEN_MODEL}
    deterministic = {"status": "pass", "findings": []}
    receipt = {
        "schema_version": "case_checklist_model_review/v1",
        "case_unit_id": case.case_unit_id,
        "decision": "accept",
        "unresolved_findings": [],
        **lifecycle._receipt_bindings(args, case, checklist_path),
        "deterministic_review": deterministic,
        "model_review": {"decision": "accept"},
        "reviewer_config": reviewer_config,
        "reviewed_at": "2026-07-16T00:00:00+00:00",
    }
    _write_json(case_dir / "review.json", receipt)

    monkeypatch.setattr(lifecycle, "_validate_review_receipt_schema", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        lifecycle,
        "_validate_checklist",
        lambda *args, **kwargs: (_initial_checklist(case), deterministic),
    )
    monkeypatch.setattr(lifecycle, "validate_model_review_body", lambda body: [])

    assert lifecycle._reusable_review(
        args,
        case=case,
        case_dir=case_dir,
        checklist_schema={},
        review_schema={},
        reviewer_config=reviewer_config,
    )

    _write(checklist_path, checklist_path.read_text(encoding="utf-8") + "# stale\n")
    assert not lifecycle._reusable_review(
        args,
        case=case,
        case_dir=case_dir,
        checklist_schema={},
        review_schema={},
        reviewer_config=reviewer_config,
    )
