from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from evidence_system.contracts import webarena_native as native
from evidence_system.contracts.webarena_human_review import (
    DEFAULT_OUTPUT_ROOT,
    WebArenaHumanReviewError,
    build_review_package,
    compile_review_materials,
    package_hash,
    validate_review_package,
)


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / DEFAULT_OUTPUT_ROOT


def test_committed_queue_is_exact_unsigned_and_current() -> None:
    report = validate_review_package(PACKAGE)
    assert report == {
        "schema_version": "webarena_verified_native_claim_human_review_validation/v1",
        "status": "ok",
        "issue_count": 0,
        "issues": [],
        "counts": {
            "expected_queue_items": 812,
            "human_signed_in_queue": 0,
            "approved_in_queue": 0,
            "completed_signoffs_validated": 0,
        },
        "completed_signoffs_status": "not_supplied",
        "formal_locks_written": 0,
        "scheduler_outputs_written": 0,
    }
    acceptance = json.loads((PACKAGE / "acceptance.json").read_text(encoding="utf-8"))
    assert acceptance["status"] == "ready_for_real_human_review"
    assert acceptance["formal_launch_eligible"] is False
    assert acceptance["authorizes_formal_lock"] is False
    assert acceptance["counts"] == {
        "queue_items": 812,
        "pending_human_review": 812,
        "human_signed": 0,
        "approved": 0,
        "formal_locks": 0,
    }
    assert len(package_hash(PACKAGE)) == 64


def test_queue_items_have_source_pointers_hashes_and_blank_decisions() -> None:
    queue, templates, _ = compile_review_materials()
    assert [item["case_unit_id"] for item in queue] == [str(value) for value in range(812)]
    assert len(templates) == 812
    for position, (item, template) in enumerate(zip(queue, templates, strict=True), start=1):
        assert item["human_signed"] is False
        assert set(item["hash_binding"]) == {
            "input_lock_sha256",
            "native_ir_sha256",
            "draft_contract_sha256",
            "draft_checklist_sha256",
            "machine_review_sha256",
            "evaluator_config_sha256",
        }
        assert len(item["source_pointers"]) >= 8
        assert item["signoff_output"]["template_line_number"] == position
        assert all(value is None for value in item["decision_fields"].values())
        for field in (
            "review_id",
            "reviewer_id",
            "review_started_at",
            "review_finished_at",
            "locked_at",
            "first_scoring_started_at",
            "source_check_complete",
            "evaluator_semantics_complete",
            "artifact_requirements_accepted",
            "decision",
            "notes",
        ):
            assert template[field] is None


def test_pending_template_is_rejected_as_completed_human_signoff() -> None:
    report = validate_review_package(
        PACKAGE,
        completed_signoffs_path=PACKAGE / "human_signoff.pending.template.jsonl",
    )
    assert report["status"] == "blocked"
    assert report["completed_signoffs_status"] == "invalid"
    assert report["counts"]["completed_signoffs_validated"] == 0
    assert any("violates schema" in issue for issue in report["issues"])
    assert report["formal_locks_written"] == 0
    assert report["scheduler_outputs_written"] == 0


def test_schema_rejects_machine_or_prefilled_decision() -> None:
    queue, _, _ = compile_review_materials()
    item = copy.deepcopy(queue[0])
    item["human_signed"] = True
    item["decision_fields"]["decision"] = "approve"
    schema = json.loads(
        (ROOT / "schemas/webarena_verified_native_claim_human_review_queue_item.schema.json").read_text(
            encoding="utf-8"
        )
    )
    import jsonschema

    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(item))
    assert errors


def test_deterministic_temp_build_does_not_mutate_upstream(tmp_path: Path) -> None:
    native_root = ROOT / native.DEFAULT_OUTPUT_ROOT
    machine_lock = native_root / "locks/machine_locks.jsonl"
    scheduler = ROOT / "experiments/step20/webarena_verified/machine_preview_schedule_index.json"
    before = {
        "machine_lock": native.file_sha256(machine_lock),
        "scheduler": native.file_sha256(scheduler),
    }
    output = tmp_path / "review-package"
    result = build_review_package(output_root=output)
    assert result["status"] == "ok"
    after = {
        "machine_lock": native.file_sha256(machine_lock),
        "scheduler": native.file_sha256(scheduler),
    }
    assert after == before
    with pytest.raises(WebArenaHumanReviewError, match="review package differs"):
        (output / "README.md").write_text("tampered\n", encoding="utf-8")
        build_review_package(output_root=output)
