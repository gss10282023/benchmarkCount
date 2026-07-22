from __future__ import annotations

import json
import inspect
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from evidence_system.contracts.appworld_generation_draft_acceptance import (
    EXPECTED_CANONICAL_SUFFIXES,
    EXPECTED_CORRECTION_CASE_IDS,
    EXPECTED_EXTENSION_COUNT,
    EXPECTED_REPAIR_CASE_COUNT,
    EXPECTED_DRAFT_RUN_ID,
    REPAIR_LOCK_SCHEMA,
    REPAIR_REPORT_SCHEMA,
    _attempt_tree_sha256,
    _load_mapping,
    _packet_section_span_resolves,
    _tree_inventory,
    _validate_batch_artifacts,
    _validate_case_draft,
    _validate_codex_command,
    _validate_generation_corrections_overlay,
    _validate_lock,
    _validate_locked_inputs,
    _validate_one_correction,
    _support_location_resolves,
    _validate_support_inventory,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_bytes, sha256_file, sha256_object, sha256_path
from neurips_ed_track_minimal.scripts import draft_case_checklist as minimal_drafter
from evidence_system.cli.validate_appworld_drafts import build_parser as build_acceptance_parser
from evidence_system.contracts import appworld_draft_acceptance as overlay_acceptance
from evidence_system.contracts import appworld_draft_overlay


ROOT = Path(__file__).resolve().parents[2]
DRAFT_ROOT = ROOT / "experiments/appworld_full_test_extension_v1/draft_runs/codex-gpt-5.4-high-support-v2"
PACKET_ROOT = ROOT / "experiments/appworld_full_test_extension_v1/case_packets/appworld"


def test_v2_lock_and_every_frozen_input_hash_validate() -> None:
    lock_path = DRAFT_ROOT / "provenance/draft_run_lock.json"
    lock = _load_mapping(lock_path, "draft run lock")

    lock_audit = _validate_lock(
        lock_file=lock_path,
        lock=lock,
        cases_root=(ROOT / lock["execution"]["output_root"]).resolve(),
    )
    input_audit, cases = _validate_locked_inputs(lock)

    assert lock_audit["implementation_hash_count"] == 9
    assert lock_audit["implementation_hashes_verified"] is True
    assert input_audit["case_ids_sha256"] == lock["inputs"]["case_ids_sha256"]
    assert input_audit["packets_recomputed"] is True
    assert len(cases) == EXPECTED_EXTENSION_COUNT


def test_one_known_good_codex_pilot_passes_dedicated_sidecar_protocol() -> None:
    case_id = "dac78d9_3"
    lock = _load_json(DRAFT_ROOT / "provenance/draft_run_lock.json")
    rows = _load_jsonl(DRAFT_ROOT / "pilot/_batch_results.jsonl")
    result = next(row for row in rows if row["case_unit_dir"] == case_id)
    schema = _load_json(ROOT / "neurips_ed_track_minimal/schemas/case_checklist.schema.json")

    entry, usage = _validate_case_draft(
        case={"case_unit_id": case_id, "task_id": case_id, "dataset_name": "test_normal"},
        case_dir=DRAFT_ROOT / "pilot" / case_id,
        packet_path=PACKET_ROOT / case_id / "case_packet.md",
        result_history=[result],
        authoritative_row=result,
        lock=lock,
        validator=Draft202012Validator(schema),
    )

    assert entry["successful_attempt_index"] == 1
    assert len(entry["canonical_files"]) == 7
    assert len(entry["attempt_files"]) == 7
    assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]


def test_packet_aware_guardrail_rejects_temporary_draft_workspace_source() -> None:
    case_id = "dac78d9_3"
    checklist = _load_json(DRAFT_ROOT / "pilot" / case_id / "checklist.json")
    checklist["native"]["user_goal"]["support"] = ["draft_instructions.md::requirements"]

    with pytest.raises(ContractLifecycleError, match="packet-aware checklist guardrails"):
        _validate_support_inventory(
            checklist,
            packet_path=PACKET_ROOT / case_id / "case_packet.md",
            case_id=case_id,
        )


@pytest.mark.parametrize("location", ["$", "root"])
def test_json_root_support_location_resolves_for_json_null(
    tmp_path: Path,
    location: str,
) -> None:
    answer_path = tmp_path / "answer.json"
    answer_path.write_text("null\n", encoding="utf-8")

    assert _support_location_resolves(answer_path, location)


def test_json_scalar_value_support_location_resolves_only_at_root(tmp_path: Path) -> None:
    answer_path = tmp_path / "answer.json"
    answer_path.write_text("null\n", encoding="utf-8")

    assert _support_location_resolves(answer_path, "null")
    assert not _support_location_resolves(answer_path, "false")


@pytest.mark.parametrize(
    "location",
    ["[0].requirement", "$[0].requirement"],
)
def test_json_array_support_location_resolves(
    tmp_path: Path,
    location: str,
) -> None:
    source_path = tmp_path / "requirements.json"
    source_path.write_text(
        json.dumps([{"requirement": "first"}]),
        encoding="utf-8",
    )

    assert _support_location_resolves(source_path, location)


def test_json_object_array_support_location_resolves(tmp_path: Path) -> None:
    source_path = tmp_path / "requirements.json"
    source_path.write_text(
        json.dumps({"foo": [{"requirement": "first"}]}),
        encoding="utf-8",
    )

    assert _support_location_resolves(source_path, "$.foo[0]")
    assert not _support_location_resolves(source_path, "$.foo[1]")


@pytest.mark.parametrize("location", ["L2-L4", "lines 1-3", "1-3"])
def test_line_span_support_location_resolves_within_bounds(
    tmp_path: Path,
    location: str,
) -> None:
    source_path = tmp_path / "source.txt"
    source_path.write_text("one\ntwo\nthree\nfour\n", encoding="utf-8")

    assert _support_location_resolves(source_path, location)


def test_large_l_prefixed_line_span_resolves_at_exact_upper_bound(tmp_path: Path) -> None:
    source_path = tmp_path / "source.txt"
    source_path.write_text(
        "\n".join(f"line {number}" for number in range(1, 156)) + "\n",
        encoding="utf-8",
    )

    assert _support_location_resolves(source_path, "L135-L155")
    assert not _support_location_resolves(source_path, "L135-L156")


def test_official_file_span_cannot_fall_back_to_packet_global_lines(tmp_path: Path) -> None:
    source_path = tmp_path / "evaluation.py"
    source_path.write_text(
        "\n".join(f"line {number}" for number in range(1, 135)) + "\n",
        encoding="utf-8",
    )
    packet_path = tmp_path / "case_packet.md"
    packet_path.write_text(
        "\n".join(f"packet line {number}" for number in range(1, 400)) + "\n",
        encoding="utf-8",
    )

    assert packet_path.read_text(encoding="utf-8").count("\n") >= 371
    assert not _support_location_resolves(source_path, "L266-L371")


def test_packet_rendered_span_resolves_only_inside_exact_source_section(tmp_path: Path) -> None:
    source_path = tmp_path / "evaluation.py"
    source_path.write_text("raw line\n", encoding="utf-8")
    packet_path = tmp_path / "case_packet.md"
    packet_path.write_text(
        "intro\n"
        "### `official/ground_truth/evaluation.py`\n"
        "Source ref: `locked`\n"
        "```python\n"
        "first\n"
        "second\n"
        "```\n"
        "### `official/ground_truth/metadata.json`\n"
        "```json\n{}\n```\n",
        encoding="utf-8",
    )

    assert _support_location_resolves(
        source_path,
        "2-7",
        packet_path=packet_path,
        packet_source_path="official/ground_truth/evaluation.py",
    )
    assert not _support_location_resolves(
        source_path,
        "7-8",
        packet_path=packet_path,
        packet_source_path="official/ground_truth/evaluation.py",
    )
    assert not _support_location_resolves(source_path, "2-7")


def test_packet_rendered_span_rejects_duplicate_source_heading(tmp_path: Path) -> None:
    packet_path = tmp_path / "case_packet.md"
    packet_path.write_text(
        "### `official/specs.json`\n```json\n{}\n```\n"
        "### `official/specs.json`\n```json\n{}\n```\n",
        encoding="utf-8",
    )

    assert not _packet_section_span_resolves(
        packet_path=packet_path,
        packet_source_path="official/specs.json",
        start=1,
        end=4,
    )


def test_tree_inventory_detects_empty_directory_structure(tmp_path: Path) -> None:
    (tmp_path / "case").mkdir()
    before = _tree_inventory(tmp_path)
    (tmp_path / "case" / "empty").mkdir()
    after = _tree_inventory(tmp_path)

    assert before["tree_sha256"] == after["tree_sha256"]
    assert before["directories"] != after["directories"]
    assert before != after


def test_real_two_correction_overlay_is_exact_and_byte_locked() -> None:
    lock_path = DRAFT_ROOT / "provenance/draft_run_lock.json"
    lock = _load_mapping(lock_path, "draft run lock")
    _, cases = _validate_locked_inputs(lock)

    audit, histories, rows = _validate_generation_corrections_overlay(
        corrections_file=DRAFT_ROOT / "provenance/draft_corrections.json",
        lock_file=lock_path,
        formal_cases_root=DRAFT_ROOT / "cases",
        accepted_cases_root=DRAFT_ROOT / "accepted_cases",
        expected_ids=[case["case_unit_id"] for case in cases],
        packet_root=PACKET_ROOT,
        lock=lock,
    )

    assert audit["corrected_case_ids"] == list(EXPECTED_CORRECTION_CASE_IDS)
    assert audit["unchanged_case_count"] == 483
    assert audit["all_483_unchanged_cases_byte_equal"] is True
    assert set(histories) == set(rows) == set(EXPECTED_CORRECTION_CASE_IDS)


def test_correction_rejects_extra_result_normalization_field() -> None:
    manifest = _load_json(DRAFT_ROOT / "provenance/draft_corrections.json")
    correction = json.loads(json.dumps(manifest["corrections"][0]))
    correction["result_normalization"]["unexpected"] = True
    lock = _load_json(DRAFT_ROOT / "provenance/draft_run_lock.json")

    with pytest.raises(ContractLifecycleError, match="normalization field set mismatch"):
        _validate_one_correction(
            correction=correction,
            expected_case_id="9ef034e_2",
            expected_round="round_01",
            draft_root=DRAFT_ROOT,
            formal_cases_root=DRAFT_ROOT / "cases",
            accepted_cases_root=DRAFT_ROOT / "accepted_cases",
            packet_root=PACKET_ROOT,
            expected_ids=list(EXPECTED_CORRECTION_CASE_IDS),
            lock=lock,
        )


@pytest.mark.parametrize("location", ["L4-L5", "lines 3-5", "2-5", "4-2"])
def test_line_span_support_location_rejects_out_of_range_or_reversed(
    tmp_path: Path,
    location: str,
) -> None:
    source_path = tmp_path / "source.txt"
    source_path.write_text("one\ntwo\nthree\nfour\n", encoding="utf-8")

    assert not _support_location_resolves(source_path, location)


def test_codex_command_gate_rejects_writable_sandbox() -> None:
    case_id = "dac78d9_3"
    api_response = _load_json(DRAFT_ROOT / "pilot" / case_id / "api_response.json")
    command = list(api_response["codex_cli"]["command"])
    command[command.index("read-only")] = "workspace-write"

    with pytest.raises(ContractLifecycleError, match="command flags drift"):
        _validate_codex_command(command, case_id=case_id)


def test_batch_results_validation_preserves_original_485_success_rows(tmp_path: Path) -> None:
    case_ids = [f"case_{index:03d}" for index in range(EXPECTED_EXTENSION_COUNT)]
    for case_id in case_ids:
        (tmp_path / case_id).mkdir()
    summary = {
        "total_cases": EXPECTED_EXTENSION_COUNT,
        "completed_cases": EXPECTED_EXTENSION_COUNT,
        "success_cases": EXPECTED_EXTENSION_COUNT,
        "skipped_cases": 0,
        "failed_cases": 0,
        "warning_count": 0,
        "provider": "codex",
        "model": "gpt-5.4",
        "reasoning_effort": "high",
        "codex_sandbox": "read-only",
        "prompt_supplement": "neurips_ed_track_minimal/prompts/draft_source_pointer_strict_v2.supplement.md",
        "token_budgets": [12000, 16000, 20000],
        "sort_by": "size",
        "quality_check": "none",
        "large_case_threshold_bytes": 100000,
        "lane_stats": {
            "regular": {"count": 439, "min_bytes": 15265, "max_bytes": 99789},
            "oversized": {"count": 46, "min_bytes": 100147, "max_bytes": 688300},
        },
        "output_root": str(tmp_path),
    }
    (tmp_path / "_batch_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    original = [
        {"case_unit_dir": case_id, "status": "success"}
        for case_id in reversed(case_ids)
    ]
    (tmp_path / "_batch_results.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in original),
        encoding="utf-8",
    )

    audit, histories, latest = _validate_batch_artifacts(
        cases_root=tmp_path,
        expected_ids=case_ids,
        lock={
            "drafter": {
                "large_case_threshold_bytes": 100000,
                "regular_max_parallel": 8,
                "oversized_max_parallel": 8,
            }
        },
    )

    assert audit["historical_result_row_count"] == EXPECTED_EXTENSION_COUNT
    assert audit["superseded_result_row_count"] == 0
    assert audit["repair_provenance"]["repair_applied"] is False
    assert len(histories) == len(latest) == EXPECTED_EXTENSION_COUNT
    assert all(row["status"] == "success" for row in latest.values())


def test_batch_results_rejects_old_failed_invocation_followed_by_485_tail(tmp_path: Path) -> None:
    case_ids = _write_batch_fixture(tmp_path)
    failed = [{"case_unit_dir": case_id, "status": "failed"} for case_id in case_ids]
    success = [{"case_unit_dir": case_id, "status": "success"} for case_id in case_ids]
    _write_jsonl(tmp_path / "_batch_results.jsonl", failed + success)

    with pytest.raises(ContractLifecycleError, match="immutable formal batch results must contain exactly 485 rows"):
        _validate_batch_artifacts(
            cases_root=tmp_path,
            expected_ids=case_ids,
            lock=_batch_lock_stub(),
        )


def test_formal_batch_rejects_appended_repairs(tmp_path: Path) -> None:
    case_ids = _write_batch_fixture(tmp_path)
    original = [{"case_unit_dir": case_id, "status": "success"} for case_id in case_ids]
    repairs = [{"case_unit_dir": case_id, "status": "success"} for case_id in case_ids[:EXPECTED_REPAIR_CASE_COUNT]]
    _write_jsonl(tmp_path / "_batch_results.jsonl", original + repairs)

    with pytest.raises(ContractLifecycleError, match="immutable formal batch results must contain exactly 485 rows"):
        _validate_batch_artifacts(
            cases_root=tmp_path,
            expected_ids=case_ids,
            lock=_batch_lock_stub(),
        )


def test_formal_batch_rejects_promotion_style_repair_even_with_provenance(tmp_path: Path) -> None:
    cases_root = tmp_path / "cases"
    case_ids = _write_batch_fixture(cases_root)
    original = [{"case_unit_dir": case_id, "status": "success"} for case_id in case_ids]
    repair_ids = case_ids[:EXPECTED_REPAIR_CASE_COUNT]
    repairs = [{"case_unit_dir": case_id, "status": "success"} for case_id in repair_ids]
    rows = original + repairs
    results_path = cases_root / "_batch_results.jsonl"
    _write_jsonl(results_path, rows)

    provenance = tmp_path / "provenance"
    provenance.mkdir()
    formal_lock_path = provenance / "draft_run_lock.json"
    formal_lock_path.write_text('{"formal":true}\n', encoding="utf-8")
    subset_path = tmp_path / "repair_case_ids.json"
    subset_path.write_text(json.dumps(repair_ids) + "\n", encoding="utf-8")
    supplement_path = tmp_path / "repair_supplement.md"
    supplement_path.write_text("Repair only unresolved support locations.\n", encoding="utf-8")
    candidate_root = tmp_path / "candidate"
    candidate_root.mkdir()
    (candidate_root / "candidate.json").write_text('{"ok":true}\n', encoding="utf-8")

    base_prompt = (ROOT / "neurips_ed_track_minimal/prompts/draft_case_checklist.prompt.md").read_text(encoding="utf-8")
    repair_inputs = {
        "case_ids_path": str(subset_path),
        "case_ids_sha256": sha256_file(subset_path),
        "case_ids_semantic_sha256": sha256_object(repair_ids),
        "case_count": EXPECTED_REPAIR_CASE_COUNT,
        "repair_supplement_path": str(supplement_path),
        "repair_supplement_sha256": sha256_file(supplement_path),
        "effective_composed_prompt_sha256": sha256_bytes(
            minimal_drafter.compose_prompt(base_prompt, supplement_path.read_text(encoding="utf-8")).encode("utf-8")
        ),
    }
    original_batch = {
        "batch_summary_path": str(cases_root / "_batch_summary.json"),
        "batch_summary_sha256": sha256_file(cases_root / "_batch_summary.json"),
        "result_row_count": EXPECTED_EXTENSION_COUNT,
        "result_rows_sha256": sha256_object(original),
    }
    configuration = {
        "provider": "codex",
        "llm_call_provider": "codex_cli",
        "model": "gpt-5.4",
        "reasoning_effort": "high",
        "auth_mode": "codex_login",
        "codex_sandbox": "read-only",
        "max_parallel": 8,
    }
    repair_lock = {
        "schema_version": REPAIR_LOCK_SCHEMA,
        "status": "locked_pre_repair",
        "draft_run_id": EXPECTED_DRAFT_RUN_ID,
        "locked_at": "2026-07-16T00:00:00Z",
        "formal_draft_run_lock_path": str(formal_lock_path),
        "formal_draft_run_lock_sha256": sha256_file(formal_lock_path),
        "cases_root": str(cases_root),
        "original_batch": original_batch,
        "repair_inputs": repair_inputs,
        "execution": {
            **configuration,
            "candidate_output_root": str(candidate_root),
            "pre_run_candidate_output_root_exists": False,
        },
        "formal_cases_pre_repair_tree_sha256": sha256_bytes(b"formal cases before repair"),
    }
    repair_lock_path = provenance / "draft_repair_lock.json"

    report_repairs = []
    for offset, case_id in enumerate(repair_ids, start=1):
        backup = tmp_path / "backups" / case_id
        backup.mkdir(parents=True)
        original_hashes = {}
        for suffix in EXPECTED_CANONICAL_SUFFIXES:
            path = backup / suffix
            path.write_text(f"{case_id}:{suffix}:original\n", encoding="utf-8")
            original_hashes[suffix] = sha256_file(path)
        (backup / "attempt_01.stdout.log").write_text("old attempt\n", encoding="utf-8")
        report_repairs.append(
            {
                "case_unit_id": case_id,
                "superseded_row_index": case_ids.index(case_id) + 1,
                "repair_row_index": EXPECTED_EXTENSION_COUNT + offset,
                "superseded_row_sha256": sha256_object(original[case_ids.index(case_id)]),
                "repair_row_sha256": sha256_object(repairs[offset - 1]),
                "reason": "repair unresolved source location",
                "backup_path": str(backup),
                "original_canonical_file_sha256": original_hashes,
                "original_attempt_tree_sha256": _attempt_tree_sha256(backup),
                "canonical_file_sha256": {
                    suffix: sha256_bytes(f"{case_id}:{suffix}:new".encode("utf-8"))
                    for suffix in EXPECTED_CANONICAL_SUFFIXES
                },
            }
        )
    repair_lock["original_cases"] = [
        {
            "case_unit_id": entry["case_unit_id"],
            "canonical_file_sha256": entry["original_canonical_file_sha256"],
            "attempt_tree_sha256": entry["original_attempt_tree_sha256"],
            "backup_path": entry["backup_path"],
        }
        for entry in report_repairs
    ]
    repair_lock_path.write_text(json.dumps(repair_lock, sort_keys=True) + "\n", encoding="utf-8")
    report = {
        "schema_version": REPAIR_REPORT_SCHEMA,
        "status": "locked_post_repair",
        "draft_run_id": EXPECTED_DRAFT_RUN_ID,
        "created_at": "2026-07-16T01:00:00Z",
        "cases_root": str(cases_root),
        "formal_draft_run_lock_path": str(formal_lock_path),
        "formal_draft_run_lock_sha256": sha256_file(formal_lock_path),
        "original_batch": original_batch,
        "repaired_batch": {
            "batch_results_jsonl_path": str(results_path),
            "batch_results_jsonl_sha256": sha256_file(results_path),
            "total_result_row_count": len(rows),
            "appended_success_row_count": len(repairs),
        },
        "repair_lock": {"path": str(repair_lock_path), "sha256": sha256_file(repair_lock_path)},
        "repair_inputs": repair_inputs,
        "candidate": {"output_root": str(candidate_root), "tree_sha256": sha256_path(candidate_root)},
        "formal_cases_tree": {
            "pre_repair_sha256": repair_lock["formal_cases_pre_repair_tree_sha256"],
            "post_repair_sha256": sha256_path(cases_root),
        },
        "repair_configuration": configuration,
        "repairs": report_repairs,
    }
    report_path = provenance / "draft_repair_report.json"
    report_path.write_text(json.dumps(report, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(ContractLifecycleError, match="immutable formal batch results must contain exactly 485 rows"):
        _validate_batch_artifacts(
            cases_root=cases_root,
            expected_ids=case_ids,
            lock=_batch_lock_stub(),
            repair_report_path=report_path,
            formal_lock_path=formal_lock_path,
        )


def _write_batch_fixture(root: Path) -> list[str]:
    root.mkdir(parents=True, exist_ok=True)
    case_ids = [f"case_{index:03d}" for index in range(EXPECTED_EXTENSION_COUNT)]
    for case_id in case_ids:
        (root / case_id).mkdir()
    summary = {
        "total_cases": EXPECTED_EXTENSION_COUNT,
        "completed_cases": EXPECTED_EXTENSION_COUNT,
        "success_cases": EXPECTED_EXTENSION_COUNT,
        "skipped_cases": 0,
        "failed_cases": 0,
        "warning_count": 0,
        "provider": "codex",
        "model": "gpt-5.4",
        "reasoning_effort": "high",
        "codex_sandbox": "read-only",
        "prompt_supplement": "neurips_ed_track_minimal/prompts/draft_source_pointer_strict_v2.supplement.md",
        "token_budgets": [12000, 16000, 20000],
        "sort_by": "size",
        "quality_check": "none",
        "large_case_threshold_bytes": 100000,
        "lane_stats": {
            "regular": {"count": 439, "min_bytes": 15265, "max_bytes": 99789},
            "oversized": {"count": 46, "min_bytes": 100147, "max_bytes": 688300},
        },
        "output_root": str(root),
    }
    (root / "_batch_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    return case_ids


def _batch_lock_stub() -> dict[str, object]:
    return {
        "drafter": {
            "large_case_threshold_bytes": 100000,
            "regular_max_parallel": 8,
            "oversized_max_parallel": 8,
        }
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_location_overlay_defaults_and_schema_are_authoritative() -> None:
    assert overlay_acceptance.DEFAULT_ACCEPTED_CASES_ROOT.name == "accepted_cases_location_v1"
    assert overlay_acceptance.DEFAULT_CORRECTIONS_PATH.name == "draft_corrections_location_v1.json"
    assert overlay_acceptance.CORRECTIONS_SCHEMA == "appworld_draft_corrections_location.v1"
    assert overlay_acceptance.EXPECTED_REPAIR_CASE_IDS == appworld_draft_overlay.EXPECTED_LOCATION_CASE_IDS
    assert overlay_acceptance.EXPECTED_CORRECTED_CASE_SET == appworld_draft_overlay.EXPECTED_CORRECTED_CASE_SET


def test_location_overlay_resolver_has_no_packet_global_fallback(tmp_path: Path) -> None:
    source = tmp_path / "evaluation.py"
    source.write_text("one\ntwo\n", encoding="utf-8")
    packet = tmp_path / "case_packet.md"
    packet.write_text("\n".join(f"packet {index}" for index in range(400)), encoding="utf-8")

    assert not overlay_acceptance._support_location_resolves(source, "L266-L371")
    with pytest.raises(TypeError):
        overlay_acceptance._support_location_resolves(
            source,
            "L266-L371",
            packet_path=packet,
            packet_source_path="official/ground_truth/evaluation.py",
        )


def test_location_overlay_secret_scanner_is_high_confidence_and_value_free(tmp_path: Path) -> None:
    source = tmp_path / "case_deadbee_1.jsonl"
    source.write_text(
        "\n".join(
            [
                '{"OPENAI_API_KEY":"sk-' + "a" * 30 + '"}',
                '{"Authorization":"Bearer ' + "b" * 30 + '"}',
                "ghp_" + "c" * 30,
                "xoxb-" + "d" * 30,
                "AKIA" + "E" * 16,
                "sk_live_" + "f" * 24,
                "-----BEGIN PRIVATE KEY-----",
                "eyJ" + "g" * 12 + "." + "h" * 12 + "." + "i" * 12,
                '{"api_key":"synthetic-fixture"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    findings = overlay_acceptance._secret_scan_paths([source])
    assert {finding["pattern"] for finding in findings} == {
        "quoted_provider_api_key",
        "authorization_bearer",
        "github_token",
        "slack_token",
        "aws_access_key_id",
        "stripe_live_secret",
        "pem_private_key",
        "jwt",
    }
    assert all(set(finding) == {"case_unit_id", "path", "pattern", "count", "line"} for finding in findings)
    assert all("value" not in finding and "sha256" not in finding for finding in findings)


def test_location_overlay_formal_batch_rejects_any_appended_row(tmp_path: Path) -> None:
    case_ids = _write_batch_fixture(tmp_path)
    rows = [{"case_unit_dir": case_id, "status": "success"} for case_id in case_ids]
    rows.append({"case_unit_dir": case_ids[0], "status": "success"})
    _write_jsonl(tmp_path / "_batch_results.jsonl", rows)

    with pytest.raises(ContractLifecycleError, match="exactly 485 rows"):
        overlay_acceptance._validate_batch_artifacts(
            cases_root=tmp_path,
            expected_ids=case_ids,
            lock=_batch_lock_stub(),
        )


def test_location_overlay_cli_exposes_explicit_closure_paths_and_verify_mode() -> None:
    parser = build_acceptance_parser()
    args = parser.parse_args(["--verify-final-lock"])
    assert args.accepted_cases_root == str(overlay_acceptance.DEFAULT_ACCEPTED_CASES_ROOT)
    assert args.corrections == str(overlay_acceptance.DEFAULT_CORRECTIONS_PATH)
    assert args.final_lock == str(overlay_acceptance.DEFAULT_FINAL_LOCK_PATH)
    parameters = inspect.signature(overlay_acceptance.validate_appworld_draft_final_lock).parameters
    assert {"final_lock_path", "lock_path", "accepted_cases_root", "corrections_path"} <= set(parameters)
