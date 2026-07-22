#!/usr/bin/env python3
"""Audit the 225 AndroidWorld remaining-75 evidence scores fail-closed.

This audit treats the released evaluator label as a post-score comparison only.
It never promotes a native/label disagreement, or native S plus stronger F, to
an asserted benchmark conflict.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JOB_ROOT = (
    REPO_ROOT
    / "transfer/androidworld_remaining75_score_gpt54_high_c32_v2_blind_20260720"
    / "score_job"
)
DEFAULT_SCORE_ROOT = (
    REPO_ROOT
    / "transfer/androidworld_remaining75_score_gpt54_high_c32_v2_blind_20260720"
    / "score_results"
)
DEFAULT_STATE_ROOT = (
    REPO_ROOT
    / "transfer/androidworld_remaining75_score_gpt54_high_c32_v2_blind_20260720"
    / "score_state"
)
DEFAULT_OUTPUT_ROOT = (
    REPO_ROOT
    / "transfer/androidworld_remaining75_score_gpt54_high_c32_v2_blind_20260720"
    / "audit"
)
EXPECTED_TASKS = 225
EXPECTED_CASES = 75
EXPECTED_AGENTS = {"agent_a", "agent_b", "agent_c"}
EXPECTED_MODEL = "gpt-5.4"
EXPECTED_REASONING = "high"
EXPECTED_SERVICE_TIER = "default"
EXPECTED_PARALLEL = 32
EXPECTED_PROMPT_SHA256 = "573ed0bc243833db7a575f9becfe517ac0e0fa25f3d3c6f223c074e3d4e5202f"
EXPECTED_SCHEMA_SHA256 = "a73d0c1278cf4d03ac854209e80125c3ae65858856b0490a8a1d2bf1741899e6"
FORBIDDEN_POINTER_NAMES = {
    "raw_run.json",
    "run_summary.json",
    "native_evaluator_output.json",
    "native_label.json",
    "released_evaluator_label.json",
    "artifact_manifest.json",
    "evidence_index.txt",
}
FORBIDDEN_POINTER_PARTS = {"evaluator_artifacts", "released_label_source"}
ATTEMPT_RE = re.compile(r"score\.attempt_(\d+)\.model_output\.json$")
FORBIDDEN_VISIBLE_PATH_PARTS = {"checkpoint_dir", "evaluator_artifacts"}
FORBIDDEN_VISIBLE_NAMES = {
    "episode_metadata.json",
    "native_evaluator_output.json",
    "raw_run.json",
    "released_evaluator_label.json",
    "run_summary.json",
}


class AuditError(RuntimeError):
    """Raised for invalid audit inputs."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-root", type=Path, default=DEFAULT_JOB_ROOT)
    parser.add_argument("--score-root", type=Path, default=DEFAULT_SCORE_ROOT)
    parser.add_argument("--state-root", type=Path, default=DEFAULT_STATE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AuditError(f"expected JSON object: {path}")
    return value


def load_json_value(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"cannot read JSON {path}: {exc}") from exc


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def latest_model_output(score_dir: Path) -> tuple[Path | None, dict[str, Any] | None]:
    found: list[tuple[int, Path]] = []
    for path in score_dir.glob("score.attempt_*.model_output.json"):
        match = ATTEMPT_RE.fullmatch(path.name)
        if match:
            found.append((int(match.group(1)), path))
    if not found:
        return None, None
    path = max(found)[1]
    return path, load_json(path)


def stronger_ids(checklist_path: Path) -> list[str]:
    """Extract exact ids from the final ``stronger.additional_conditions`` list."""

    lines = checklist_path.read_text(encoding="utf-8").splitlines()
    in_stronger = False
    in_conditions = False
    ids: list[str] = []
    for line in lines:
        if line == "stronger:":
            in_stronger = True
            continue
        if in_stronger and line and not line.startswith(" "):
            break
        if in_stronger and line.strip() == "additional_conditions:":
            in_conditions = True
            continue
        if not in_conditions:
            continue
        match = re.fullmatch(r"  - id: ([A-Za-z0-9._-]+)", line)
        if match:
            ids.append(match.group(1))
        elif line and not line.startswith("  "):
            break
    return ids


def pointer_file(pointer: str, task_dir: Path) -> Path | None:
    if "::" not in pointer:
        return None
    relative, _ = pointer.split("::", 1)
    if not relative.startswith("evidence/"):
        return None
    candidate = task_dir / relative
    if not candidate.is_file():
        return None
    parts = set(candidate.relative_to(task_dir).parts)
    if candidate.name in FORBIDDEN_POINTER_NAMES or parts & FORBIDDEN_POINTER_PARTS:
        return None
    return candidate


def expected_stronger(native: str, checks: list[dict[str, Any]]) -> str:
    if not checks:
        return "NA"
    if native == "F":
        return "F"
    if native == "U":
        return "U"
    statuses = [str(check.get("status") or "") for check in checks]
    if "contradicted" in statuses:
        return "F"
    return "S" if statuses and all(item == "supported" for item in statuses) else "U"


def labels_agree(label: str, native: str) -> bool:
    return (label == "success" and native == "S") or (label == "fail" and native == "F")


def audit_model_visible_inputs(task_root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(task_root.glob("*/evidence/**/*")):
        if not path.is_file():
            continue
        relative = path.relative_to(task_root)
        if path.name in FORBIDDEN_VISIBLE_NAMES or set(relative.parts) & FORBIDDEN_VISIBLE_PATH_PARTS:
            errors.append(f"forbidden model-visible result artifact: {relative}")
        if path.suffix.lower() in {".gz", ".pickle", ".pkl"}:
            errors.append(f"unscanned compressed/pickle model artifact: {relative}")
        if path.suffix.lower() == ".json":
            for pointer in find_result_leaks(load_json_value(path)):
                errors.append(f"result-bearing model-visible JSON field: {relative}::{pointer}")
    return errors


def find_result_leaks(value: Any, pointer: str = "$") -> list[str]:
    forbidden = {
        "native_label",
        "native_score",
        "released_evaluator_label",
        "released_evaluator_score",
    }
    leaks: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_pointer = f"{pointer}.{key}"
            normalized = str(key).strip().lower()
            if normalized in forbidden:
                leaks.append(child_pointer)
            if normalized == "is_successful" and not isinstance(child, (dict, list, str)):
                leaks.append(child_pointer)
            leaks.extend(find_result_leaks(child, child_pointer))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            leaks.extend(find_result_leaks(child, f"{pointer}[{index}]"))
    return leaks


def validate_pointers(
    score: dict[str, Any],
    task_dir: Path,
    expected_conditions: list[str],
) -> list[str]:
    errors: list[str] = []
    native = score.get("native") or {}
    native_verdict = str(native.get("verdict") or "")
    native_pointers = native.get("pointers") or []
    if native_verdict not in {"S", "F", "U"}:
        errors.append("native verdict is not S/F/U")
    expected_rule = {
        "S": "checklist.yaml::native.success_if",
        "F": "checklist.yaml::native.fail_if",
        "U": "checklist.yaml::native.undecided_if",
    }.get(native_verdict, "")
    if not any(str(pointer).startswith(expected_rule) for pointer in native_pointers):
        errors.append("native pointers omit matching checklist rule")
    if not any(pointer_file(str(pointer), task_dir) is not None for pointer in native_pointers):
        errors.append("native pointers omit a valid non-verdict evidence file")

    stronger = score.get("stronger") or {}
    checks = stronger.get("condition_checks") or []
    actual_ids = [str(item.get("id") or "") for item in checks if isinstance(item, dict)]
    if actual_ids != expected_conditions:
        errors.append("stronger condition IDs/order differ from locked checklist")
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            errors.append("stronger condition check is not an object")
            continue
        pointers = check.get("pointers") or []
        expected_prefix = f"checklist.yaml::stronger.additional_conditions[{index}]"
        if not any(str(pointer).startswith(expected_prefix) for pointer in pointers):
            errors.append(f"stronger condition {index} omits its checklist pointer")
        if not any(pointer_file(str(pointer), task_dir) is not None for pointer in pointers):
            errors.append(f"stronger condition {index} omits valid non-verdict evidence")
        if str(check.get("status") or "") not in {"supported", "contradicted", "undecided"}:
            errors.append(f"stronger condition {index} has invalid status")
    stronger_pointers = stronger.get("pointers") or []
    if not any(str(pointer).startswith("checklist.yaml::stronger.additional_conditions") for pointer in stronger_pointers):
        errors.append("stronger pointers omit locked stronger source")
    if not any(pointer_file(str(pointer), task_dir) is not None for pointer in stronger_pointers):
        errors.append("stronger pointers omit a valid non-verdict evidence file")
    if str(stronger.get("verdict") or "") != expected_stronger(native_verdict, checks):
        errors.append("stronger aggregate verdict does not follow locked aggregation")
    return errors


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    job_root = args.job_root.resolve()
    task_root = job_root / "tasks"
    receipt = load_json(job_root / "transfer_receipt.json")
    score_root = args.score_root.resolve()
    state_root = args.state_root.resolve()
    plan = load_json(state_root / "_task_plan.json")
    batch = load_json(state_root / "_batch_summary.json")
    transfer_manifest = load_json(score_root / "_transfer_manifest.json")
    expected = {str(item["task_id"]): item for item in receipt.get("tasks") or []}
    global_errors: list[str] = []
    global_errors.extend(audit_model_visible_inputs(task_root))
    if receipt.get("case_count") != EXPECTED_CASES or receipt.get("record_count") != EXPECTED_TASKS:
        global_errors.append("transfer receipt denominator is not 75 x 3")
    if len(expected) != EXPECTED_TASKS:
        global_errors.append("transfer receipt task set is incomplete or duplicated")
    lock = receipt.get("scoring_lock") or {}
    for key, value in {
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING,
        "service_tier": EXPECTED_SERVICE_TIER,
        "fast_mode": False,
        "auth_mode": "codex_login",
        "sandbox": "read-only",
        "max_parallel": EXPECTED_PARALLEL,
    }.items():
        if lock.get(key) != value:
            global_errors.append(f"transfer scoring lock mismatch: {key}")
    if set(score_dir.name for score_dir in score_root.iterdir() if score_dir.is_dir()) != set(expected):
        global_errors.append("score output task set differs from transfer receipt")
    for key, value in {
        "task_count": EXPECTED_TASKS,
        "completed": EXPECTED_TASKS,
        "success": EXPECTED_TASKS,
        "failed": 0,
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING,
        "max_parallel": EXPECTED_PARALLEL,
    }.items():
        if batch.get(key) != value:
            global_errors.append(f"batch summary mismatch: {key}")
    for key, value in {
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING,
        "service_tier": EXPECTED_SERVICE_TIER,
        "sandbox": "read-only",
        "max_parallel": EXPECTED_PARALLEL,
    }.items():
        if plan.get(key) != value:
            global_errors.append(f"sealed task plan mismatch: {key}")
    for document_name, document in (
        ("sealed task plan", plan),
        ("score transfer manifest", transfer_manifest),
    ):
        if document.get("score_prompt_sha256") != EXPECTED_PROMPT_SHA256:
            global_errors.append(f"{document_name} score prompt hash mismatch")
        if document.get("score_schema_sha256") != EXPECTED_SCHEMA_SHA256:
            global_errors.append(f"{document_name} score schema hash mismatch")
    transfer_records = {
        str(item.get("task_id") or ""): item
        for item in transfer_manifest.get("tasks") or []
    }
    if set(transfer_records) != set(expected):
        global_errors.append("score transfer manifest task set mismatch")
    else:
        for task_id, receipt_task in expected.items():
            transfer_task = transfer_records[task_id]
            for key in ("checklist_sha256", "evidence_tree_sha256", "native_label_sha256"):
                if transfer_task.get(key) != receipt_task.get(key):
                    global_errors.append(f"score transfer manifest hash mismatch: {task_id}:{key}")

    plan_records = {str(item.get("task_id") or ""): item for item in plan.get("tasks") or []}
    records: list[dict[str, Any]] = []
    for task_id, receipt_task in sorted(expected.items()):
        errors: list[str] = []
        task_dir = task_root / task_id
        score_dir = score_root / task_id
        score_path = score_dir / "score.json"
        manifest_path = score_dir / "score_manifest.json"
        try:
            score = load_json(score_path)
            manifest = load_json(manifest_path)
            model_path, model = latest_model_output(score_dir)
            saved_label = load_json(task_dir / "native_label.json")
        except Exception as exc:
            records.append({"task_id": task_id, "structural_valid": False, "errors": [str(exc)]})
            continue
        checklist_path = task_dir / "checklist.yaml"
        checklist_sha = sha256_file(checklist_path)
        if checklist_sha != receipt_task.get("checklist_sha256"):
            errors.append("checklist hash differs from transfer receipt")
        if score.get("case_unit_id") != receipt_task.get("case_unit_id"):
            errors.append("score case id differs from transfer receipt")
        plan_record = plan_records.get(task_id)
        if plan_record is None:
            errors.append("task missing from sealed plan")
        else:
            if plan_record.get("checklist_sha256") != checklist_sha:
                errors.append("plan checklist hash differs")
            if plan_record.get("evidence_tree_sha256") != receipt_task.get("evidence_tree_sha256"):
                errors.append("plan evidence hash differs")
        for key, value in {
            "model": EXPECTED_MODEL,
            "reasoning_effort": EXPECTED_REASONING,
            "service_tier": EXPECTED_SERVICE_TIER,
            "checklist_sha256": checklist_sha,
        }.items():
            if manifest.get(key) != value:
                errors.append(f"score manifest mismatch: {key}")
        if model is None or model_path is None:
            errors.append("missing final model output")
        else:
            if set(model) != {"native", "stronger"}:
                errors.append("model output includes fields beyond native/stronger")
            if model.get("native") != score.get("native") or model.get("stronger") != score.get("stronger"):
                errors.append("final score differs from final model output")
            rendered = json.dumps(model, sort_keys=True).lower()
            if any(token in rendered for token in ("released_evaluator_label", "native_label", "benchmark_conflict")):
                errors.append("model output leaks a forbidden result/conflict field")
        telemetry_paths = sorted(score_dir.glob("score.attempt_*.codex.telemetry.json"))
        if not telemetry_paths:
            errors.append("no Codex attempt telemetry")
        else:
            telemetry = load_json(telemetry_paths[-1])
            if (telemetry.get("codex_exit") or {}).get("returncode") != 0:
                errors.append("final Codex attempt has nonzero exit")
        expected_conditions = stronger_ids(checklist_path)
        errors.extend(validate_pointers(score, task_dir, expected_conditions))
        released_label = str((score.get("released_evaluator_label") or {}).get("value") or "")
        saved_value = str(saved_label.get("value") or "")
        if released_label != saved_value:
            errors.append("joined released label differs from preserved sidecar")
        native = str((score.get("native") or {}).get("verdict") or "")
        stronger = str((score.get("stronger") or {}).get("verdict") or "")
        records.append(
            {
                "task_id": task_id,
                "case_unit_id": receipt_task.get("case_unit_id"),
                "agent": receipt_task.get("agent"),
                "released_label": released_label,
                "native_verdict": native,
                "stronger_verdict": stronger,
                "label_agreement": labels_agree(released_label, native),
                "native_S_stronger_F": native == "S" and stronger == "F",
                "record_level_conflict_status": "not_inferred_from_score",
                "structural_valid": not errors,
                "errors": errors,
                "model_attempt_count": len(telemetry_paths),
                "score_json": str(score_path),
                "score_manifest": str(manifest_path),
            }
        )

    native_counts = Counter(str(record.get("native_verdict") or "") for record in records)
    stronger_counts = Counter(str(record.get("stronger_verdict") or "") for record in records)
    label_counts = Counter(str(record.get("released_label") or "") for record in records)
    mismatches = [record for record in records if record.get("label_agreement") is False]
    invalid = [record for record in records if not record.get("structural_valid")]
    report = {
        "schema_version": "androidworld_remaining75_score_audit/v1",
        "audit_status": "complete" if not global_errors and not invalid else "invalid",
        "global_errors": global_errors,
        "system_design_checks": {
            "exact_75_x_3_denominator": len(records) == EXPECTED_TASKS,
            "paper_41_excluded": receipt.get("excluded_paper_case_count") == 41,
            "checklists_locked_and_hash_bound": not any("checklist" in error or "plan" in error for record in records for error in record.get("errors", [])),
            "released_labels_absent_from_model_output": not any("model output leaks" in error for record in records for error in record.get("errors", [])),
            "released_results_absent_from_model_visible_inputs": not any("model-visible" in error or "compressed/pickle" in error for error in global_errors),
            "non_verdict_evidence_pointers_only": not any("pointer" in error for record in records for error in record.get("errors", [])),
            "native_scored_as_S_F_U": set(native_counts) <= {"S", "F", "U"},
            "stronger_reported_separately": set(stronger_counts) <= {"NA", "S", "F", "U"},
            "stronger_not_auto_promoted_to_benchmark_conflict": all(record.get("record_level_conflict_status") == "not_inferred_from_score" for record in records),
            "gpt54_high_default_nonfast_c32": not global_errors and lock.get("fast_mode") is False,
        },
        "summary": {
            "record_count": len(records),
            "case_count": len({record.get("case_unit_id") for record in records if record.get("case_unit_id")}),
            "structurally_valid_count": len(records) - len(invalid),
            "native_verdicts": dict(sorted(native_counts.items())),
            "stronger_verdicts": dict(sorted(stronger_counts.items())),
            "released_labels": dict(sorted(label_counts.items())),
            "agreement_count": len(records) - len(mismatches),
            "disagreement_count": len(mismatches),
            "native_S_stronger_F_count": sum(bool(record.get("native_S_stronger_F")) for record in records),
            "record_level_conflict_confirmed_count": 0,
            "label_disagreement_followup_count": len(mismatches),
            "record_level_conflict_pending_count": 0,
        },
        "records": records,
    }
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    write_json(output_root / "audit_report.json", report)
    with (output_root / "records.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["task_id", "case_unit_id", "agent", "released_label", "native_verdict", "stronger_verdict", "label_agreement", "native_S_stronger_F", "record_level_conflict_status", "structural_valid", "model_attempt_count"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field) for field in fields})
    print(json.dumps({"audit_status": report["audit_status"], **report["summary"], "global_error_count": len(global_errors)}))
    return 0 if not global_errors and not invalid else 1


if __name__ == "__main__":
    raise SystemExit(main())
