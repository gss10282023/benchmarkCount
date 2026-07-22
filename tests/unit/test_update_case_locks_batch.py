from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from neurips_ed_track_minimal.scripts import update_case_locks_batch as batch  # noqa: E402
from neurips_ed_track_minimal.scripts.case_checklist_review import (  # noqa: E402
    EXPECTED_MODEL_REVIEW_ITEM_IDS,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha_object(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _valid_checklist(case_id: str, task_id: str) -> dict[str, Any]:
    support = ["selected_task_source.json::$.user_task"]
    rule = lambda text: {"text": text, "support": support}  # noqa: E731
    return {
        "schema_version": "case_checklist_v1",
        "case_unit_id": case_id,
        "domain": "agentdojo",
        "task_id": task_id,
        "native": {
            "user_goal": rule("The stored user task defines the requested outcome."),
            "benchmark_success": rule("The native utility evaluator determines success."),
            "checked_by": rule("The benchmark evaluates retained post-run state."),
            "decisive_artifacts": [
                {
                    "artifact": "retained post-run state",
                    "question": "Does the retained state satisfy the native evaluator?",
                    "support": support,
                }
            ],
            "success_if": [rule("The native evaluator returns success from retained state.")],
            "fail_if": [rule("The native evaluator returns failure from retained state.")],
            "undecided_if": [rule("The retained state is unavailable or incomplete.")],
        },
        "stronger": {"additional_conditions": []},
    }


def _fixture(tmp_path: Path, count: int = 2) -> dict[str, Any]:
    packet_root = tmp_path / "packets"
    draft_root = tmp_path / "drafts"
    prompt_root = tmp_path / "prompts"
    manifest_path = tmp_path / "manifest.yaml"
    bundle_path = tmp_path / "bundle.json"
    lock_path = tmp_path / "locks" / "cases.jsonl"
    acceptance_path = tmp_path / "locks" / "acceptance.json"

    draft_prompt = prompt_root / "draft.md"
    score_prompt = prompt_root / "score.md"
    review_prompt = prompt_root / "review.md"
    for path, body in (
        (draft_prompt, "draft prompt\n"),
        (score_prompt, "score prompt\n"),
        (review_prompt, "review prompt\n"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    review_schema = ROOT / "neurips_ed_track_minimal/schemas/case_checklist_review.schema.json"
    checklist_schema = ROOT / "neurips_ed_track_minimal/schemas/case_checklist.schema.json"
    score_schema = ROOT / "neurips_ed_track_minimal/schemas/evidence_score.schema.json"

    manifest_cases: list[dict[str, str]] = []
    sources: list[dict[str, Any]] = []
    for index in range(count):
        case_id = f"v1.2.2:test:user_task_{index}:injection_task_0"
        task_id = f"test:user_task_{index}:injection_task_0"
        case_dir_name = f"case_{index}"
        packet_dir = packet_root / case_dir_name
        packet_dir.mkdir(parents=True)
        packet_path = packet_dir / "case_packet.md"
        packet_path.write_text(
            "# Case Packet\n\n"
            "## Case Metadata\n\n"
            "- domain: `agentdojo`\n"
            f"- case_unit_id: `{case_id}`\n"
            f"- task_id: `{task_id}`\n\n"
            "## Source Inventory\n\n"
            "- `selected_task_source.json`\n\n"
            "## Packet Source Files\n",
            encoding="utf-8",
        )
        raw_manifest = packet_dir / "raw_case_manifest.json"
        _write_json(raw_manifest, {"case_unit_id": case_id})

        checklist_path = draft_root / case_dir_name / "checklist.yaml"
        checklist_path.parent.mkdir(parents=True)
        checklist_path.write_text(
            yaml.safe_dump(_valid_checklist(case_id, task_id), sort_keys=False),
            encoding="utf-8",
        )
        review_path = checklist_path.with_name("review.json")
        review = {
            "schema_version": "case_checklist_model_review/v1",
            "case_unit_id": case_id,
            "decision": "accept",
            "unresolved_findings": [],
            "case_packet_path": str(packet_path.resolve()),
            "case_packet_sha256": _sha(packet_path),
            "checklist_path": str(checklist_path.resolve()),
            "checklist_sha256": _sha(checklist_path),
            "draft_prompt_path": str(draft_prompt.resolve()),
            "draft_prompt_sha256": _sha(draft_prompt),
            "checklist_schema_path": str(checklist_schema.resolve()),
            "checklist_schema_sha256": _sha(checklist_schema),
            "review_prompt_path": str(review_prompt.resolve()),
            "review_prompt_sha256": _sha(review_prompt),
            "review_schema_path": str(review_schema.resolve()),
            "review_schema_sha256": _sha(review_schema),
            "deterministic_review": {"status": "pass", "findings": []},
            "model_review": {
                "decision": "accept",
                "blocking_findings": [],
                "checklist_items": [
                    {
                        "id": item_id,
                        "status": "pass",
                        "rationale": "The fixture satisfies this review item.",
                        "evidence": ["checklist.yaml::$.native"],
                    }
                    for item_id in EXPECTED_MODEL_REVIEW_ITEM_IDS
                ],
            },
            "reviewer_config": {
                "provider": "codex_cli",
                "auth_mode": "codex_login",
                "codex_cli_version": "codex-cli 1.0.0-test",
                "model": "test-model",
                "reasoning_effort": "xhigh",
                "sandbox": "read-only",
                "ephemeral": True,
                "ignore_user_config": True,
                "model_verbosity": "low",
                "timeout_seconds": 60,
            },
            "reviewed_at": "2026-07-16T12:00:00+10:00",
        }
        _write_json(review_path, review)
        manifest_cases.append({"case_unit_id": case_id, "task_id": task_id})
        sources.append(
            {
                "case_unit_id": case_id,
                "contract_id": f"contract_{index}",
                "domain": "agentdojo",
                "task_id": task_id,
                "draft_input": {
                    "case_packet_path": str(packet_path.resolve()),
                    "case_packet_sha256": _sha(packet_path),
                    "raw_case_manifest_path": str(raw_manifest.resolve()),
                    "raw_case_manifest_sha256": _sha(raw_manifest),
                },
            }
        )

    manifest: dict[str, Any] = {
        "schema_version": "experiment_manifest/v1",
        "source_bundle_hash": "0" * 64,
        "domains": [
            {
                "domain": "agentdojo",
                "case_unit_target": count,
                "case_unit_count": count,
                "case_units": manifest_cases,
            }
        ],
    }
    definition = dict(manifest)
    definition.pop("source_bundle_hash")
    bundle = {
        "schema_version": "contract_source_bundle.v2",
        "manifest_path": str(manifest_path.resolve()),
        "manifest_definition_sha256": _sha_object(definition),
        "manifest_definition_sha256_scope": "canonical_mapping_without_source_bundle_hash",
        "manifest_definition_excluded_fields": ["source_bundle_hash"],
        "source_count": count,
        "sources": sources,
    }
    _write_json(bundle_path, bundle)
    manifest["source_bundle_hash"] = _sha(bundle_path)
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    argv = [
        "--manifest",
        str(manifest_path),
        "--source-bundle",
        str(bundle_path),
        "--case-packet-root",
        str(packet_root),
        "--draft-root",
        str(draft_root),
        "--lock-file",
        str(lock_path),
        "--acceptance-output",
        str(acceptance_path),
        "--expected-count",
        str(count),
        "--draft-prompt",
        str(draft_prompt),
        "--score-prompt",
        str(score_prompt),
        "--review-prompt",
        str(review_prompt),
        "--checklist-schema",
        str(checklist_schema),
        "--score-schema",
        str(score_schema),
        "--review-schema",
        str(review_schema),
    ]
    return {
        "argv": argv,
        "manifest": manifest_path,
        "bundle": bundle_path,
        "draft_root": draft_root,
        "lock": lock_path,
        "acceptance": acceptance_path,
    }


def test_batch_locks_exact_manifest_order_and_is_idempotent(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    assert batch.main(fixture["argv"]) == 0
    first_lock = fixture["lock"].read_bytes()
    first_acceptance = fixture["acceptance"].read_bytes()

    entries = [json.loads(line) for line in first_lock.decode().splitlines()]
    manifest = yaml.safe_load(fixture["manifest"].read_text(encoding="utf-8"))
    expected_ids = [case["case_unit_id"] for case in manifest["domains"][0]["case_units"]]
    assert [entry["case_unit_id"] for entry in entries] == expected_ids
    receipt = json.loads(first_acceptance)
    assert first_acceptance == batch._canonical_json_bytes(receipt, newline=True)
    writer_lock = fixture["lock"].with_name(f"{fixture['lock'].name}.writer.lock")
    assert receipt["writer_lock_sha256"] == _sha(writer_lock)
    assert receipt["counts"] == {
        "manifest_cases": 2,
        "source_entries": 2,
        "case_packets": 2,
        "valid_drafts": 2,
        "reviewed": 2,
        "locked": 2,
        "unresolved_drafts": 0,
    }
    assert receipt["lock_file_sha256"] == hashlib.sha256(first_lock).hexdigest()

    assert batch.main(fixture["argv"]) == 0
    assert fixture["lock"].read_bytes() == first_lock
    assert fixture["acceptance"].read_bytes() == first_acceptance


def test_lock_entry_paths_keep_minimal_compatibility_and_use_repo_fallback() -> None:
    assert batch.case_locks.display_path(
        ROOT / "neurips_ed_track_minimal/prompts/draft_case_checklist.prompt.md"
    ) == "prompts/draft_case_checklist.prompt.md"
    assert batch.case_locks.display_path(
        ROOT / "experiments/agentdojo_full_v1.2.2_direct/lock/draft_prompt.md"
    ) == "experiments/agentdojo_full_v1.2.2_direct/lock/draft_prompt.md"


def test_guardrail_failure_publishes_nothing(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture["lock"].parent.mkdir(parents=True, exist_ok=True)
    fixture["lock"].write_bytes(b"old lock\n")
    fixture["acceptance"].write_bytes(b"old acceptance\n")
    checklist = next(fixture["draft_root"].glob("*/checklist.yaml"))
    value = yaml.safe_load(checklist.read_text(encoding="utf-8"))
    value["native"]["user_goal"]["support"] = ["outside.json::$.goal"]
    checklist.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")

    assert batch.main(fixture["argv"]) == 2
    assert fixture["lock"].read_bytes() == b"old lock\n"
    assert fixture["acceptance"].read_bytes() == b"old acceptance\n"


def test_stale_review_hash_publishes_nothing(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture["lock"].parent.mkdir(parents=True, exist_ok=True)
    fixture["lock"].write_bytes(b"old lock\n")
    review_path = next(fixture["draft_root"].glob("*/review.json"))
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review["checklist_sha256"] = "0" * 64
    _write_json(review_path, review)

    assert batch.main(fixture["argv"]) == 2
    assert fixture["lock"].read_bytes() == b"old lock\n"
    assert not fixture["acceptance"].exists()


def test_source_order_mismatch_publishes_nothing(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    bundle = json.loads(fixture["bundle"].read_text(encoding="utf-8"))
    bundle["sources"].reverse()
    _write_json(fixture["bundle"], bundle)
    manifest = yaml.safe_load(fixture["manifest"].read_text(encoding="utf-8"))
    manifest["source_bundle_hash"] = _sha(fixture["bundle"])
    fixture["manifest"].write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    assert batch.main(fixture["argv"]) == 2
    assert not fixture["lock"].exists()
    assert not fixture["acceptance"].exists()


def test_mixed_reviewer_configs_publish_nothing(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    review_paths = sorted(fixture["draft_root"].glob("*/review.json"))
    review = json.loads(review_paths[1].read_text(encoding="utf-8"))
    review["reviewer_config"]["model"] = "different-model"
    _write_json(review_paths[1], review)

    assert batch.main(fixture["argv"]) == 2
    assert not fixture["lock"].exists()
    assert not fixture["acceptance"].exists()


def test_missing_review_publishes_nothing(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    next(fixture["draft_root"].glob("*/review.json")).unlink()

    assert batch.main(fixture["argv"]) == 2
    assert not fixture["lock"].exists()
    assert not fixture["acceptance"].exists()


def test_second_replace_failure_rolls_back_both_outputs(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    fixture = _fixture(tmp_path)
    fixture["lock"].parent.mkdir(parents=True, exist_ok=True)
    fixture["lock"].write_bytes(b"old lock\n")
    fixture["acceptance"].write_bytes(b"old acceptance\n")
    original_replace = batch.os.replace
    failed = False

    def fail_acceptance_once(source: Path, destination: Path) -> None:
        nonlocal failed
        if Path(destination) == fixture["acceptance"] and not failed:
            failed = True
            raise OSError("simulated acceptance replace failure")
        original_replace(source, destination)

    monkeypatch.setattr(batch.os, "replace", fail_acceptance_once)
    assert batch.main(fixture["argv"]) == 2
    assert fixture["lock"].read_bytes() == b"old lock\n"
    assert fixture["acceptance"].read_bytes() == b"old acceptance\n"


def test_busy_advisory_writer_lock_is_a_clear_fail_closed_error(
    tmp_path: Path,
    capsys: Any,
) -> None:
    fixture = _fixture(tmp_path)
    lock_path = fixture["lock"]
    acceptance_path = fixture["acceptance"]
    writer_lock_path = lock_path.with_name(f"{lock_path.name}.writer.lock")
    definition = {
        "schema_version": "case_checklist_batch_writer_lock/v1",
        "lock_file_path": batch._display_path(lock_path),
        "acceptance_output_path": batch._display_path(acceptance_path),
    }
    payload = batch._canonical_json_bytes(definition, newline=True)

    with batch._advisory_writer_lock(writer_lock_path, payload):
        assert batch.main(fixture["argv"]) == 2
    assert "Another batch runner holds advisory writer lock" in capsys.readouterr().err
    assert not lock_path.exists()
    assert not acceptance_path.exists()
