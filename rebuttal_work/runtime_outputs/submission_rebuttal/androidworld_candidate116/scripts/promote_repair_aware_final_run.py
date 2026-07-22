#!/usr/bin/env python3
"""Atomically promote one validated repair-aware handoff to canonical final inputs.

No legacy promoter is called.  All handoff, effective-origin, repair provenance,
semantic-review, packet, checklist, contract, slot, and runtime-configuration
relationships are validated before canonical writes.  A blocked runtime
preflight always yields ``execution_eligible=false`` and
``scoring_eligible=false`` while preserving a truthful locked-input manifest.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from repair_pipeline_common import (
    EXPECTED_CASE_COUNT,
    REPO_ROOT,
    WORK_ROOT,
    RepairPipelineError,
    add_self_hash,
    file_binding,
    load_json,
    object_sha256,
    repo_relative,
    sha256_file,
    utc_now,
)
from repair_aware_final_common import (
    AGENTS,
    AGENTS_CONFIG,
    CANDIDATE_MANIFEST,
    INFRA_CONFIG,
    INPUT_FREEZE,
    PACKET_INDEX,
    RUNTIME_PREFLIGHT,
    SIDECAR_KEYS,
    SLOT_COUNT,
    SLOT_LEDGER,
    STATIC_ACCEPTANCE,
    STATIC_VALIDATION,
    load_packet_index,
    load_slot_ledger,
    publication_commit_contract,
    runtime_state,
    resolved_agent_configuration_bindings,
    tree_descriptor,
    validate_custom_execution_payload,
    verify_handoff,
    verify_legacy_self_hash,
    verify_static_acceptance_inputs,
)
from semantic_review_common import SemanticReviewError, write_json_atomic


SCRIPT = Path(__file__).resolve()
VALIDATOR = WORK_ROOT / "scripts" / "validate_repair_aware_final_run.py"
CANONICAL_DRAFTS = WORK_ROOT / "drafts"
CANONICAL_CONTRACTS = WORK_ROOT / "contracts" / "drafts"
CASE_LOCK_FILE = WORK_ROOT / "locks" / "androidworld_candidate116_cases.jsonl"
FREEZE_FILE = WORK_ROOT / "freeze" / "androidworld_candidate116_contracts_drafts_freeze.json"
MANIFEST_FILE = WORK_ROOT / "manifests" / "androidworld_candidate116_final_run_manifest.json"
REPORT_FILE = WORK_ROOT / "validation" / "androidworld_candidate116_promotion_report.json"
PROMOTION_LOCK = WORK_ROOT / "locks" / ".androidworld_candidate116_promotion.lock"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--runtime-config", type=Path)
    parser.add_argument("--frozen-at")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def require_time(value: Any) -> str:
    text = str(value or "").strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RepairPipelineError("frozen-at is not ISO-8601") from exc
    if parsed.tzinfo is None:
        raise RepairPipelineError("frozen-at must include a time zone")
    return text


def staged_binding(staged: Path, final: Path) -> dict[str, Any]:
    return {
        "path": repo_relative(final),
        "sha256": sha256_file(staged),
        "size_bytes": staged.stat().st_size,
    }


def source_path(binding: Mapping[str, Any]) -> Path:
    path = Path(str(binding["path"]))
    return (path if path.is_absolute() else REPO_ROOT / path).resolve()


def ensure_pristine() -> None:
    for path in (
        CANONICAL_DRAFTS,
        CANONICAL_CONTRACTS,
        CASE_LOCK_FILE,
        FREEZE_FILE,
        MANIFEST_FILE,
        REPORT_FILE,
    ):
        _require_real_candidate_destination(path)
    conflicts: list[str] = []
    if CANONICAL_DRAFTS.exists() and any(CANONICAL_DRAFTS.iterdir()):
        conflicts.append(repo_relative(CANONICAL_DRAFTS))
    if CANONICAL_CONTRACTS.exists() and any(CANONICAL_CONTRACTS.iterdir()):
        conflicts.append(repo_relative(CANONICAL_CONTRACTS))
    for path in (CASE_LOCK_FILE, FREEZE_FILE, MANIFEST_FILE, REPORT_FILE):
        if path.exists():
            conflicts.append(repo_relative(path))
    if conflicts:
        raise RepairPipelineError(
            "refusing to overwrite existing canonical/frozen outputs: " + ", ".join(conflicts)
        )


def _require_real_candidate_destination(path: Path) -> None:
    """Reject lexical escapes and every pre-existing symlink ancestor."""

    lexical = Path(os.path.abspath(path))
    lexical_root = Path(os.path.abspath(WORK_ROOT))
    try:
        relative = lexical.relative_to(lexical_root)
    except ValueError as exc:
        raise RepairPipelineError(f"canonical destination escapes candidate116: {path}") from exc
    cursor = lexical_root
    if cursor.is_symlink():
        raise RepairPipelineError(f"candidate116 root cannot be a symlink: {cursor}")
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise RepairPipelineError(f"canonical destination has a symlink ancestor: {cursor}")


def copy_case(
    row: Mapping[str, Any],
    handoff_binding: Mapping[str, Any],
    stage_draft: Path,
    stage_contract: Path,
) -> dict[str, Any]:
    case_id = str(row["case_unit_id"])
    final_draft = CANONICAL_DRAFTS / case_id
    final_contract = CANONICAL_CONTRACTS / case_id
    sidecars = row["draft_sidecars"]
    sources: dict[str, Path] = {
        "checklist.yaml": source_path(row["effective_checklist_yaml"]),
        "checklist.json": source_path(row["effective_checklist_json"]),
        "raw_generated_checklist.yaml": source_path(row["effective_checklist_yaml"]),
        "llm_call.json": source_path(sidecars["llm_call_json"]),
        "api_response.json": source_path(sidecars["api_response_json"]),
        "reasoning_summary.txt": source_path(sidecars["reasoning_summary_txt"]),
        "stdout.log": source_path(sidecars["stdout_log"]),
        "stderr.log": source_path(sidecars["stderr_log"]),
        "effective_origin.json": source_path(row["effective_origin"]),
        "automatic_qc_report.json": source_path(row["effective_qc"]),
        "semantic_proposal.json": source_path(row["semantic_proposal"]),
        "semantic_result.json": source_path(row["semantic_result"]),
        "semantic_receipt.json": source_path(row["semantic_receipt"]),
        "root_agent_verdict.json": source_path(row["root_agent_verdict"]),
        "review.json": source_path(row["root_agent_review"]),
    }
    if row["origin"] == "repair":
        sources["repair_provenance.json"] = source_path(row["repair_provenance"])
    for root in (stage_draft, stage_contract):
        root.mkdir(parents=True, exist_ok=False)
        for name, source in sources.items():
            shutil.copy2(source, root / name)
    provenance = {
        "schema_version": "androidworld_repair_aware_promoted_checklist_provenance/v1",
        "case_unit_id": case_id,
        "task_id": row["task_id"],
        "selection_rank": row["selection_rank"],
        "group": row["group"],
        "origin": row["origin"],
        "handoff": copy.deepcopy(dict(handoff_binding)),
        "case_handoff_sha256": row["case_handoff_sha256"],
        "source_bindings": {
            "full_packet": copy.deepcopy(row["full_packet"]),
            "effective_checklist_yaml": copy.deepcopy(row["effective_checklist_yaml"]),
            "effective_checklist_json": copy.deepcopy(row["effective_checklist_json"]),
            "effective_origin": copy.deepcopy(row["effective_origin"]),
            "repair_provenance": copy.deepcopy(row["repair_provenance"]),
            "draft_sidecars": copy.deepcopy(row["draft_sidecars"]),
            "effective_qc": copy.deepcopy(row["effective_qc"]),
            "semantic_proposal": copy.deepcopy(row["semantic_proposal"]),
            "semantic_result": copy.deepcopy(row["semantic_result"]),
            "semantic_receipt": copy.deepcopy(row["semantic_receipt"]),
            "root_agent_verdict": copy.deepcopy(row["root_agent_verdict"]),
            "root_agent_review": copy.deepcopy(row["root_agent_review"]),
        },
        "canonical_paths": {
            "draft": repo_relative(final_draft / "checklist.yaml"),
            "contract_draft": repo_relative(final_contract / "checklist.yaml"),
        },
    }
    provenance = add_self_hash(provenance, "provenance_sha256")
    for root in (stage_draft, stage_contract):
        write_json_atomic(root / "provenance.json", provenance)

    draft_bindings = {
        name.replace(".", "_"): staged_binding(stage_draft / name, final_draft / name)
        for name in sorted([*sources, "provenance.json"])
    }
    contract_bindings = {
        name.replace(".", "_"): staged_binding(stage_contract / name, final_contract / name)
        for name in sorted([*sources, "provenance.json"])
    }
    if draft_bindings != contract_bindings:
        # Paths intentionally differ, bytes and sizes must not.
        for name in draft_bindings:
            if {
                key: draft_bindings[name][key] for key in ("sha256", "size_bytes")
            } != {key: contract_bindings[name][key] for key in ("sha256", "size_bytes")}:
                raise RepairPipelineError(f"{case_id} staged draft/contract bytes differ")
    case = {
        "schema_version": "androidworld_repair_aware_promoted_case_binding/v1",
        "case_unit_id": case_id,
        "task_id": row["task_id"],
        "selection_rank": row["selection_rank"],
        "group": row["group"],
        "origin": row["origin"],
        "case_handoff_sha256": row["case_handoff_sha256"],
        "packet": copy.deepcopy(row["full_packet"]),
        "effective_origin": copy.deepcopy(row["effective_origin"]),
        "repair_provenance": copy.deepcopy(row["repair_provenance"]),
        "source_review_chain": {
            "effective_qc": copy.deepcopy(row["effective_qc"]),
            "semantic_proposal": copy.deepcopy(row["semantic_proposal"]),
            "semantic_result": copy.deepcopy(row["semantic_result"]),
            "semantic_receipt": copy.deepcopy(row["semantic_receipt"]),
            "root_agent_verdict": copy.deepcopy(row["root_agent_verdict"]),
            "root_agent_review": copy.deepcopy(row["root_agent_review"]),
        },
        "canonical_draft": draft_bindings,
        "canonical_contract_draft": contract_bindings,
        "provenance_sha256": provenance["provenance_sha256"],
    }
    case["case_binding_sha256"] = object_sha256(case)
    return case


def build_stage(
    context: Mapping[str, Any],
    slots: list[dict[str, Any]],
    runtime: Mapping[str, Any],
    eligible: bool,
    frozen_at: str,
) -> tuple[Path, dict[str, Any]]:
    stage = Path(tempfile.mkdtemp(prefix=".repair_aware_promotion.", dir=WORK_ROOT))
    stage_drafts = stage / "drafts"
    stage_contracts = stage / "contracts" / "drafts"
    handoff = context["handoff"]
    handoff_binding = file_binding(context["path"]) | {
        "handoff_sha256": handoff["handoff_sha256"]
    }
    case_bindings: list[dict[str, Any]] = []
    try:
        for row in context["rows"]:
            case_bindings.append(
                copy_case(
                    row,
                    handoff_binding,
                    stage_drafts / row["case_unit_id"],
                    stage_contracts / row["case_unit_id"],
                )
            )
        case_by_id = {row["case_unit_id"]: row for row in case_bindings}
        locks: list[dict[str, Any]] = []
        for row in case_bindings:
            lock = {
                "schema_version": "androidworld_repair_aware_external_case_lock/v1",
                "case_unit_id": row["case_unit_id"],
                "task_id": row["task_id"],
                "selection_rank": row["selection_rank"],
                "group": row["group"],
                "origin": row["origin"],
                "handoff": handoff_binding,
                "packet": row["packet"],
                "effective_origin": row["effective_origin"],
                "repair_provenance": row["repair_provenance"],
                "source_review_chain": row["source_review_chain"],
                "canonical_draft": row["canonical_draft"],
                "canonical_contract_draft": row["canonical_contract_draft"],
                "case_binding_sha256": row["case_binding_sha256"],
            }
            locks.append(add_self_hash(lock, "case_lock_sha256"))
        lock_by_id = {row["case_unit_id"]: row for row in locks}
        lock_stage = stage / "locks" / CASE_LOCK_FILE.name
        lock_stage.parent.mkdir(parents=True)
        lock_stage.write_text(
            "".join(
                json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
                for row in locks
            ),
            encoding="utf-8",
        )
        draft_tree = tree_descriptor(stage_drafts, CANONICAL_DRAFTS)
        contract_tree = tree_descriptor(stage_contracts, CANONICAL_CONTRACTS)
        if draft_tree["files"] != contract_tree["files"]:
            raise RepairPipelineError("canonical draft/contract staged trees differ")

        external_locks = {
            "path": repo_relative(CASE_LOCK_FILE),
            "sha256": sha256_file(lock_stage),
            "size_bytes": lock_stage.stat().st_size,
            "count": len(locks),
            "ordered_case_lock_hashes_sha256": object_sha256(
                [row["case_lock_sha256"] for row in locks]
            ),
        }
        freeze = {
            "schema_version": "androidworld_repair_aware_contracts_drafts_freeze/v1",
            "freeze_id": "androidworld_candidate116_repair_aware_contracts_drafts_v1",
            "status": "frozen",
            "publication": publication_commit_contract(commit_marker=False),
            "frozen_at": frozen_at,
            "case_count": EXPECTED_CASE_COUNT,
            "case_order": context["order"],
            "case_order_sha256": handoff["case_order_sha256"],
            "promotion_handoff": handoff_binding,
            "packet_source_input_freeze": file_binding(INPUT_FREEZE)
            | {"freeze_sha256": load_json(INPUT_FREEZE).get("freeze_sha256")},
            "packet_index": file_binding(PACKET_INDEX),
            "effective_manifest": copy.deepcopy(handoff["effective_manifest"]),
            "repair_prelock": copy.deepcopy(handoff["repair_prelock"]),
            "repair_concurrency_evidence": copy.deepcopy(
                handoff["repair_concurrency_evidence"]
            ),
            "repair_concurrency_audit": copy.deepcopy(
                handoff["repair_concurrency_audit"]
            ),
            "repair_concurrency_samples": copy.deepcopy(
                handoff["repair_concurrency_samples"]
            ),
            "effective_qc_summary": copy.deepcopy(handoff["effective_qc_summary"]),
            "semantic_review_prelock": copy.deepcopy(handoff["semantic_review_prelock"]),
            "independent_semantic_validation": copy.deepcopy(
                handoff["independent_semantic_validation"]
            ),
            "external_root_agent_verdict_index": copy.deepcopy(
                handoff["external_root_agent_verdict_index"]
            ),
            "root_agent_review_summary": copy.deepcopy(handoff["root_agent_review_summary"]),
            "runtime": copy.deepcopy(runtime),
            "slot_ledger": file_binding(SLOT_LEDGER),
            "strict_static_acceptance": file_binding(STATIC_ACCEPTANCE),
            "semantic_static_validation": file_binding(STATIC_VALIDATION),
            "canonical_drafts_tree": draft_tree,
            "canonical_contracts_drafts_tree": contract_tree,
            "external_case_locks": external_locks,
            "cases": case_bindings,
            "cases_sha256": object_sha256(case_bindings),
        }
        freeze = add_self_hash(freeze, "freeze_sha256")
        freeze_stage = stage / "freeze" / FREEZE_FILE.name
        write_json_atomic(freeze_stage, freeze)

        agent_configurations = resolved_agent_configuration_bindings()
        slot_rows: list[dict[str, Any]] = []
        for slot in slots:
            case = case_by_id[slot["case_unit_id"]]
            slot_rows.append(
                copy.deepcopy(slot)
                | {
                    "case_lock_sha256": lock_by_id[slot["case_unit_id"]]["case_lock_sha256"],
                    "packet": copy.deepcopy(case["packet"]),
                    "packet_sha256": case["packet"]["sha256"],
                    "contract_draft": copy.deepcopy(
                        case["canonical_contract_draft"]["checklist_yaml"]
                    ),
                    "contract_draft_sha256": case["canonical_contract_draft"][
                        "checklist_yaml"
                    ]["sha256"],
                    "draft": copy.deepcopy(case["canonical_draft"]["checklist_yaml"]),
                    "draft_sha256": case["canonical_draft"]["checklist_yaml"]["sha256"],
                    "agent_configuration": copy.deepcopy(
                        agent_configurations[slot["agent_id"]]
                    ),
                    "infra_config_sha256": sha256_file(INFRA_CONFIG),
                    "runtime_bindings_sha256": runtime["runtime_bindings_sha256"],
                    "runtime_configuration": {
                        "runtime_bindings_sha256": runtime["runtime_bindings_sha256"],
                        "configuration_bindings_sha256": object_sha256(
                            runtime["configuration_bindings"]
                        ),
                        "execution_eligible": runtime["execution_eligible"],
                        "scoring_eligible": runtime["scoring_eligible"],
                    },
                }
            )
        status = "locked_ready_for_execution" if eligible else "locked_inputs_runtime_preflight_pending"
        manifest = {
            "schema_version": "androidworld_candidate116_repair_aware_final_run_manifest/v1",
            "manifest_id": "androidworld_candidate116_repair_aware_final_run_v1",
            "status": status,
            "publication": publication_commit_contract(commit_marker=True),
            "created_at": frozen_at,
            "domain": "androidworld",
            "case_count": EXPECTED_CASE_COUNT,
            "agent_count": len(AGENTS),
            "record_slot_count": SLOT_COUNT,
            "execution_eligible": eligible,
            "scoring_eligible": False,
            "eligibility_note": (
                "All packet/draft/contract/config inputs are frozen; execution and scoring remain "
                "disabled until runtime preflight and a placeholder-free execution config pass."
                if not eligible
                else "Inputs and runtime are execution-ready; scoring stays disabled until runs finish."
            ),
            "promotion_handoff": handoff_binding,
            "contracts_drafts_freeze": staged_binding(freeze_stage, FREEZE_FILE)
            | {"freeze_sha256": freeze["freeze_sha256"]},
            "external_case_locks": external_locks,
            "packet_source_input_freeze": freeze["packet_source_input_freeze"],
            "packet_index": freeze["packet_index"],
            "effective_manifest": freeze["effective_manifest"],
            "repair_prelock": freeze["repair_prelock"],
            "repair_concurrency_evidence": freeze["repair_concurrency_evidence"],
            "repair_concurrency_audit": freeze["repair_concurrency_audit"],
            "repair_concurrency_samples": freeze["repair_concurrency_samples"],
            "effective_qc_summary": freeze["effective_qc_summary"],
            "semantic_review_prelock": freeze["semantic_review_prelock"],
            "independent_semantic_validation": freeze["independent_semantic_validation"],
            "external_root_agent_verdict_index": freeze[
                "external_root_agent_verdict_index"
            ],
            "root_agent_review_summary": freeze["root_agent_review_summary"],
            "strict_static_acceptance": freeze["strict_static_acceptance"],
            "semantic_static_validation": freeze["semantic_static_validation"],
            "experiment_scope_manifest": file_binding(CANDIDATE_MANIFEST),
            "runtime": copy.deepcopy(runtime),
            "slot_ledger": file_binding(SLOT_LEDGER)
            | {"record_slot_ids_hash": load_json(SLOT_LEDGER)["record_slot_ids_hash"]},
            "cases": case_bindings,
            "cases_sha256": object_sha256(case_bindings),
            "slots": slot_rows,
            "slots_sha256": object_sha256(slot_rows),
            "tool_bindings": {
                "repair_aware_promotion_builder": file_binding(SCRIPT),
                "repair_aware_independent_validator": file_binding(VALIDATOR),
                "repair_aware_final_common": file_binding(
                    WORK_ROOT / "scripts" / "repair_aware_final_common.py"
                ),
                "repair_concurrency_verifier": file_binding(
                    WORK_ROOT / "scripts" / "repair_pipeline_common.py"
                ),
            },
        }
        manifest = add_self_hash(manifest, "manifest_sha256")
        manifest_stage = stage / "manifests" / MANIFEST_FILE.name
        write_json_atomic(manifest_stage, manifest)
        report = {
            "schema_version": "androidworld_candidate116_repair_aware_promotion_report/v1",
            "status": "pass",
            "publication": publication_commit_contract(commit_marker=False),
            "created_at": frozen_at,
            "case_count": EXPECTED_CASE_COUNT,
            "slot_count": SLOT_COUNT,
            "repair_count": handoff["repair_count"],
            "retain_count": handoff["retain_count"],
            "root_agent_reviewer": "Codex/root_agent",
            "human_review_claimed": False,
            "execution_eligible": eligible,
            "scoring_eligible": False,
            "manifest_status": status,
            "promotion_handoff": handoff_binding,
            "repair_concurrency_evidence": copy.deepcopy(
                handoff["repair_concurrency_evidence"]
            ),
            "repair_concurrency_audit": copy.deepcopy(
                handoff["repair_concurrency_audit"]
            ),
            "repair_concurrency_samples": copy.deepcopy(
                handoff["repair_concurrency_samples"]
            ),
            "contracts_drafts_freeze": staged_binding(freeze_stage, FREEZE_FILE)
            | {"freeze_sha256": freeze["freeze_sha256"]},
            "final_run_manifest": staged_binding(manifest_stage, MANIFEST_FILE)
            | {"manifest_sha256": manifest["manifest_sha256"]},
            "issues": [],
        }
        report = add_self_hash(report, "report_sha256")
        report_stage = stage / "validation" / REPORT_FILE.name
        write_json_atomic(report_stage, report)
        return stage, {
            "manifest": manifest,
            "freeze": freeze,
            "report": report,
            "paths": {
                "drafts": stage_drafts,
                "contracts": stage_contracts,
                "locks": lock_stage,
                "freeze": freeze_stage,
                "manifest": manifest_stage,
                "report": report_stage,
            },
        }
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def _publish_file_create_once(
    source: Path,
    destination: Path,
    created: list[tuple[str, Path, tuple[int, int, str | None]]],
) -> None:
    """Copy one staged file without any overwrite window."""

    _require_real_candidate_destination(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected_sha256 = sha256_file(source)
    expected_size = source.stat().st_size
    try:
        fd = os.open(
            destination,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
    except FileExistsError as exc:
        raise RepairPipelineError(f"target appeared during promotion: {destination}") from exc
    try:
        with os.fdopen(fd, "wb") as output, source.open("rb") as input_file:
            shutil.copyfileobj(input_file, output, length=1024 * 1024)
            output.flush()
            os.fsync(output.fileno())
        if destination.stat().st_size != expected_size or sha256_file(destination) != expected_sha256:
            raise RepairPipelineError(f"create-once publication bytes differ: {destination}")
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    published = os.lstat(destination)
    created.append(
        ("file", destination, (published.st_dev, published.st_ino, expected_sha256))
    )


def _publish_tree_create_once(
    source: Path,
    destination: Path,
    created: list[tuple[str, Path, tuple[int, int, str | None]]],
) -> None:
    _require_real_candidate_destination(destination)
    if destination.exists():
        if not destination.is_dir() or any(destination.iterdir()):
            raise RepairPipelineError(f"canonical tree is not pristine: {destination}")
    else:
        destination.mkdir(parents=True, exist_ok=False)
        published = os.lstat(destination)
        created.append(("directory", destination, (published.st_dev, published.st_ino, None)))
    for item in sorted(source.rglob("*"), key=lambda value: value.relative_to(source).as_posix()):
        relative = item.relative_to(source)
        target = destination / relative
        if item.is_symlink():
            raise RepairPipelineError(f"staged canonical tree contains a symlink: {item}")
        if item.is_dir():
            target.mkdir(exist_ok=False)
            published = os.lstat(target)
            created.append(("directory", target, (published.st_dev, published.st_ino, None)))
        elif item.is_file():
            _publish_file_create_once(item, target, created)
        else:
            raise RepairPipelineError(f"staged canonical tree contains a special file: {item}")


def _rollback_created(
    created: list[tuple[str, Path, tuple[int, int, str | None]]],
) -> None:
    """Remove only bytes this invocation created and never delete foreign edits."""

    for kind, path, identity in reversed(created):
        try:
            observed = os.lstat(path)
            if (observed.st_dev, observed.st_ino) != identity[:2]:
                continue
            if kind == "file":
                if path.is_file() and sha256_file(path) == identity[2]:
                    path.unlink()
            elif path.is_dir():
                path.rmdir()
        except (FileNotFoundError, OSError):
            # A changed file or non-empty directory is foreign state.  Leave it
            # in place; absence of the final manifest still fails closed.
            pass


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def commit(stage: Path, outputs: Mapping[str, Any]) -> None:
    """Publish create-once, with the final manifest as the sole commit marker."""

    paths = outputs["paths"]
    created: list[tuple[str, Path, tuple[int, int, str | None]]] = []
    committed = False
    try:
        _publish_tree_create_once(paths["drafts"], CANONICAL_DRAFTS, created)
        _publish_tree_create_once(paths["contracts"], CANONICAL_CONTRACTS, created)
        for key, destination in (
            ("locks", CASE_LOCK_FILE),
            ("freeze", FREEZE_FILE),
            ("report", REPORT_FILE),
        ):
            _publish_file_create_once(paths[key], destination, created)

        # Recompute the two complete canonical trees before exposing the commit
        # marker.  Readers must ignore any state without the final manifest.
        if tree_descriptor(CANONICAL_DRAFTS) != outputs["freeze"]["canonical_drafts_tree"]:
            raise RepairPipelineError("published canonical draft tree differs before commit")
        if tree_descriptor(CANONICAL_CONTRACTS) != outputs["freeze"][
            "canonical_contracts_drafts_tree"
        ]:
            raise RepairPipelineError("published canonical contract tree differs before commit")
        for directory in {
            CANONICAL_DRAFTS,
            CANONICAL_CONTRACTS,
            CASE_LOCK_FILE.parent,
            FREEZE_FILE.parent,
            REPORT_FILE.parent,
        }:
            _fsync_directory(directory)

        # This create-once file is the logical atomic commit marker and is
        # intentionally the final state-changing publication operation.
        _publish_file_create_once(paths["manifest"], MANIFEST_FILE, created)
        _fsync_directory(MANIFEST_FILE.parent)
        committed = True
    except BaseException:
        _rollback_created(created)
        CANONICAL_DRAFTS.mkdir(parents=True, exist_ok=True)
        raise
    finally:
        if not committed:
            _rollback_created(created)
        shutil.rmtree(stage, ignore_errors=True)


def main() -> int:
    args = parse_args()
    if args.self_test:
        ledger, slots = load_slot_ledger(
            [row["case_unit_id"] for row in load_json(SLOT_LEDGER)["cases"]]
        )
        runtime, eligible = runtime_state(None)
        fake_runtime_rejected = False
        try:
            validate_custom_execution_payload(
                {"status": "locked", "execution_eligible": True},
                preflight=load_json(RUNTIME_PREFLIGHT),
                base_bindings={
                    "agents": file_binding(AGENTS_CONFIG),
                    "infra": file_binding(INFRA_CONFIG),
                },
            )
        except RepairPipelineError:
            fake_runtime_rejected = True
        if (
            len(slots) != SLOT_COUNT
            or runtime["scoring_eligible"] is not False
            or not fake_runtime_rejected
        ):
            raise RepairPipelineError("repair-aware promoter self-test failed")
        print(
            json.dumps(
                {
                    "status": "self_test_pass",
                    "slot_count": len(slots),
                    "slot_hash": ledger["record_slot_ids_hash"],
                    "runtime_status": runtime["status"],
                    "execution_eligible": eligible,
                    "negative_two_field_runtime_config_rejected": fake_runtime_rejected,
                    "negative_scoring_without_runs_rejected": True,
                    "canonical_outputs_written": False,
                },
                indent=2,
            )
        )
        return 0
    if args.handoff is None:
        raise RepairPipelineError("--handoff is required")
    context = verify_handoff(args.handoff)
    verify_static_acceptance_inputs()
    input_freeze = load_json(INPUT_FREEZE, "candidate116 packet/source input freeze")
    verify_legacy_self_hash(input_freeze, "freeze_sha256", "candidate116 input freeze")
    packet_index, packet_by_case = load_packet_index(context["order"])
    for row in context["rows"]:
        packet = packet_by_case[row["case_unit_id"]]
        if (
            row["full_packet"]["path"] != packet["case_packet_path"]
            or row["full_packet"]["sha256"] != packet["case_packet_sha256"]
        ):
            raise RepairPipelineError(f"{row['case_unit_id']} handoff packet differs from packet index")
    ledger, slots = load_slot_ledger(context["order"])
    runtime, eligible = runtime_state(args.runtime_config)
    if load_json(RUNTIME_PREFLIGHT).get("status") == "blocked" and eligible:
        raise RepairPipelineError("blocked runtime preflight cannot be execution eligible")
    if args.check_only:
        print(
            json.dumps(
                {
                    "status": "check_only_pass",
                    "case_count": EXPECTED_CASE_COUNT,
                    "slot_count": len(slots),
                    "repair_count": context["handoff"]["repair_count"],
                    "retain_count": context["handoff"]["retain_count"],
                    "execution_eligible": eligible,
                    "scoring_eligible": False,
                    "canonical_outputs_written": False,
                },
                indent=2,
            )
        )
        return 0
    _require_real_candidate_destination(PROMOTION_LOCK)
    PROMOTION_LOCK.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock_fd = os.open(
            PROMOTION_LOCK,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
    except FileExistsError as exc:
        raise RepairPipelineError("another candidate116 canonical promotion is active") from exc
    lock_identity = os.fstat(lock_fd)
    try:
        os.write(lock_fd, f"pid={os.getpid()}\n".encode("utf-8"))
        os.fsync(lock_fd)
        ensure_pristine()
        frozen_at = require_time(args.frozen_at or datetime.now(timezone.utc).isoformat())
        stage, outputs = build_stage(context, slots, runtime, eligible, frozen_at)
        commit(stage, outputs)
    finally:
        os.close(lock_fd)
        try:
            current_lock = os.lstat(PROMOTION_LOCK)
        except FileNotFoundError:
            pass
        else:
            if (
                current_lock.st_dev == lock_identity.st_dev
                and current_lock.st_ino == lock_identity.st_ino
            ):
                PROMOTION_LOCK.unlink()
    print(
        json.dumps(
            {
                "status": "pass",
                "promoted_cases": EXPECTED_CASE_COUNT,
                "slot_count": SLOT_COUNT,
                "execution_eligible": outputs["manifest"]["execution_eligible"],
                "scoring_eligible": outputs["manifest"]["scoring_eligible"],
                "manifest_status": outputs["manifest"]["status"],
                "freeze": repo_relative(FREEZE_FILE),
                "manifest": repo_relative(MANIFEST_FILE),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SemanticReviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
