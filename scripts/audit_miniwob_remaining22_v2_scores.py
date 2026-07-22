#!/usr/bin/env python3
"""Audit the 66 MiniWoB v2 evidence scores against the locked system design."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from neurips_ed_track_minimal.scripts.score_evidence_with_codex import (  # noqa: E402
    CodexScoreError,
    validate_score_guardrails,
)


EXPECTED_TASKS = 66
EXPECTED_CASES = 22
EXPECTED_MODEL = "gpt-5.4"
EXPECTED_REASONING = "high"
EXPECTED_SERVICE_TIER = "default"
EXPECTED_SANDBOX = "read-only"
EXPECTED_PARALLEL = 11
MODEL_OUTPUT_RE = re.compile(r"score\.attempt_(\d+)\.model_output\.json$")
ATTEMPT_TELEMETRY_RE = re.compile(r"score\.attempt_(\d+)\.codex\.telemetry\.json$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--score-root", type=Path, required=True)
    parser.add_argument("--transfer-receipt", type=Path, required=True)
    parser.add_argument("--freeze-receipt", type=Path, required=True)
    parser.add_argument("--task-plan", type=Path, required=True)
    parser.add_argument("--batch-summary", type=Path, required=True)
    parser.add_argument("--conflict-audit", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def verdict_agrees(label: str, verdict: str) -> bool:
    return (label == "success" and verdict == "S") or (
        label == "fail" and verdict == "F"
    )


def expected_stronger_verdict(
    native_verdict: str,
    checks: list[dict[str, Any]],
) -> str:
    statuses = [str(item.get("status")) for item in checks]
    if not statuses:
        return "NA"
    if native_verdict == "F":
        return "F"
    if native_verdict == "U":
        return "U"
    if "contradicted" in statuses:
        return "F"
    if all(status == "supported" for status in statuses):
        return "S"
    return "U"


def counter_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def load_conflict_records(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    payload = load_json(path)
    if payload.get("schema_version") != "miniwob_record_level_conflict_audit/v1":
        raise ValueError("unexpected conflict-audit schema_version")
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("conflict audit records must be a list")
    by_task: dict[str, dict[str, Any]] = {}
    for record in records:
        task_id = str(record.get("task_id") or "")
        if not task_id or task_id in by_task:
            raise ValueError(f"invalid or duplicate conflict audit task_id: {task_id}")
        by_task[task_id] = record
    return by_task


def model_outputs(score_dir: Path) -> list[tuple[int, Path]]:
    candidates: list[tuple[int, Path]] = []
    for path in score_dir.glob("score.attempt_*.model_output.json"):
        match = MODEL_OUTPUT_RE.search(path.name)
        if match:
            candidates.append((int(match.group(1)), path))
    return sorted(candidates)


def latest_model_output(score_dir: Path) -> tuple[Path | None, dict[str, Any] | None]:
    candidates = model_outputs(score_dir)
    if not candidates:
        return None, None
    path = max(candidates)[1]
    return path, load_json(path)


def attempt_telemetry(score_dir: Path) -> list[tuple[int, Path]]:
    candidates: list[tuple[int, Path]] = []
    for path in score_dir.glob("score.attempt_*.codex.telemetry.json"):
        match = ATTEMPT_TELEMETRY_RE.search(path.name)
        if match:
            candidates.append((int(match.group(1)), path))
    return sorted(candidates)


def validate_conflict_record(
    task_id: str,
    record: dict[str, Any] | None,
) -> tuple[str, list[str]]:
    errors: list[str] = []
    if record is None:
        return "pending_record_level_audit", ["missing record-level conflict audit"]
    status = str(record.get("status") or "")
    allowed = {"confirmed_benchmark_conflict", "not_confirmed_benchmark_conflict"}
    if status not in allowed:
        errors.append(f"invalid conflict audit status: {status}")
    if not str(record.get("rationale") or "").strip():
        errors.append("record-level audit lacks rationale")
    for key in ("retained_artifact_pointers", "source_pointers"):
        pointers = record.get(key)
        if not isinstance(pointers, list) or not pointers or not all(
            isinstance(pointer, str) and pointer.strip() for pointer in pointers
        ):
            errors.append(f"record-level audit requires nonempty {key}")
    if str(record.get("task_id") or "") != task_id:
        errors.append("record-level audit task_id mismatch")
    return status or "invalid_record_level_audit", errors


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "task_id",
        "case_unit_id",
        "agent",
        "released_label",
        "native_verdict",
        "native_reason",
        "stronger_verdict",
        "stronger_reason",
        "label_agreement",
        "native_S_stronger_F",
        "record_level_conflict_status",
        "structural_valid",
        "error_count",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in rows:
            writer.writerow({key: record.get(key) for key in fields})


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    summary = report["summary"]
    lines = [
        "# MiniWoB remaining-22 v2 score audit",
        "",
        f"- Audit status: `{report['audit_status']}`",
        f"- Records: {summary['record_count']} (cases: {summary['case_count']})",
        f"- Structurally valid: {summary['structurally_valid_count']}/{summary['record_count']}",
        f"- Native verdicts: `{json.dumps(summary['native_verdicts'], sort_keys=True)}`",
        f"- Released labels: `{json.dumps(summary['released_labels'], sort_keys=True)}`",
        f"- Native/released agreement: {summary['agreement_count']}; disagreements: {summary['disagreement_count']}",
        f"- Stronger verdicts: `{json.dumps(summary['stronger_verdicts'], sort_keys=True)}`",
        f"- Native S + stronger F (reported only, not a conflict inference): {summary['native_S_stronger_F_count']}",
        f"- Confirmed benchmark conflicts after separate record-level review: {summary['confirmed_benchmark_conflict_count']}",
        "",
        "## System-design checks",
        "",
    ]
    for key, value in report["system_design_checks"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Disagreement records", ""])
    mismatches = [record for record in report["records"] if not record["label_agreement"]]
    if not mismatches:
        lines.append("No native/released-label disagreements.")
    else:
        lines.extend(
            [
                "| task | label | native | stronger | conflict review |",
                "|---|---:|---:|---:|---|",
            ]
        )
        for record in mismatches:
            lines.append(
                "| {task_id} | {released_label} | {native_verdict} | {stronger_verdict} | {record_level_conflict_status} |".format(
                    **record
                )
            )
    lines.extend(["", "## Validation errors", ""])
    invalid = [record for record in report["records"] if record["errors"]]
    if not invalid:
        lines.append("No structural, provenance, blinding, schema, or decisive-pointer errors.")
    else:
        for record in invalid:
            lines.append(f"- `{record['task_id']}`: {'; '.join(record['errors'])}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    task_root = args.task_root.resolve()
    score_root = args.score_root.resolve()
    transfer = load_json(args.transfer_receipt.resolve())
    freeze = load_json(args.freeze_receipt.resolve())
    plan = load_json(args.task_plan.resolve())
    batch = load_json(args.batch_summary.resolve())
    schema_path = ROOT / "neurips_ed_track_minimal/schemas/evidence_score.schema.json"
    schema = load_json(schema_path)
    schema_validator = Draft202012Validator(schema)
    prompt_path = ROOT / "neurips_ed_track_minimal/prompts/score_evidence_with_codex.prompt.md"
    expected_prompt_sha = sha256_file(prompt_path)
    expected_schema_sha = sha256_file(schema_path)
    conflict_records = load_conflict_records(args.conflict_audit.resolve() if args.conflict_audit else None)
    transfer_manifest_path = score_root / "_transfer_manifest.json"
    transfer_manifest = load_json(transfer_manifest_path)

    receipt_tasks = transfer.get("tasks") or []
    global_errors: list[str] = []
    if len(receipt_tasks) != EXPECTED_TASKS or transfer.get("task_count") != EXPECTED_TASKS:
        global_errors.append("transfer receipt does not contain exactly 66 tasks")
    if transfer.get("case_count") != EXPECTED_CASES:
        global_errors.append("transfer receipt does not contain exactly 22 cases")
    if transfer_manifest.get("schema_version") != "neurips_score_transfer_manifest_v1":
        global_errors.append("downloaded score transfer manifest has an unexpected schema")
    for key, expected in {
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING,
        "score_prompt_sha256": expected_prompt_sha,
        "score_schema_sha256": expected_schema_sha,
    }.items():
        if transfer_manifest.get(key) != expected:
            global_errors.append(f"score transfer manifest {key} mismatch")
    manifest_outputs = transfer_manifest.get("outputs") or []
    manifest_output_paths = {str(item.get("path") or "") for item in manifest_outputs}
    observed_output_paths = {
        path.relative_to(score_root).as_posix()
        for path in score_root.rglob("*")
        if path.is_file() and path != transfer_manifest_path
    }
    if manifest_output_paths != observed_output_paths:
        global_errors.append(
            "downloaded output inventory differs from the sealed transfer manifest"
        )
    for item in manifest_outputs:
        relative = str(item.get("path") or "")
        path = score_root / relative
        if not path.is_file() or sha256_file(path) != item.get("sha256"):
            global_errors.append(f"downloaded output hash mismatch: {relative}")
    manifest_task_ids = {
        str(item.get("task_id") or "") for item in transfer_manifest.get("tasks") or []
    }
    if freeze.get("status") != "frozen" or freeze.get("case_count") != EXPECTED_CASES:
        global_errors.append("freeze receipt is not the expected frozen 22-case receipt")
    boundary = freeze.get("phase_boundary") or {}
    for key, expected in {
        "locked_before_evidence_scoring": True,
        "locked_before_specific_outcome_or_released_label_inspection": True,
        "contains_agent_outcomes": False,
        "reads_result_namespaces": False,
    }.items():
        if boundary.get(key) is not expected:
            global_errors.append(f"freeze boundary failed: {key}")
    plan_expected = {
        "task_count": EXPECTED_TASKS,
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING,
        "service_tier": EXPECTED_SERVICE_TIER,
        "sandbox": EXPECTED_SANDBOX,
        "max_parallel": EXPECTED_PARALLEL,
        "score_prompt_sha256": expected_prompt_sha,
        "score_schema_sha256": expected_schema_sha,
    }
    for key, expected in plan_expected.items():
        if plan.get(key) != expected:
            global_errors.append(f"task plan {key} mismatch: {plan.get(key)!r} != {expected!r}")
    for key, expected in {
        "task_count": EXPECTED_TASKS,
        "completed": EXPECTED_TASKS,
        "success": EXPECTED_TASKS,
        "failed": 0,
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING,
        "max_parallel": EXPECTED_PARALLEL,
    }.items():
        if batch.get(key) != expected:
            global_errors.append(f"batch summary {key} mismatch: {batch.get(key)!r} != {expected!r}")

    plan_by_task = {str(item["task_id"]): item for item in plan.get("tasks") or []}
    receipt_by_task = {str(item["task_id"]): item for item in receipt_tasks}
    expected_task_ids = set(receipt_by_task)
    if manifest_task_ids != expected_task_ids:
        global_errors.append("score transfer manifest task set differs from transfer receipt")
    observed_task_ids = {path.name for path in score_root.iterdir() if path.is_dir()}
    if observed_task_ids != expected_task_ids:
        global_errors.append(
            f"score task set mismatch: missing={sorted(expected_task_ids - observed_task_ids)}, extra={sorted(observed_task_ids - expected_task_ids)}"
        )

    records: list[dict[str, Any]] = []
    freeze_time = parse_time(str(freeze["frozen_at"]))
    for task_id in sorted(expected_task_ids):
        receipt_task = receipt_by_task[task_id]
        task_dir = task_root / task_id
        score_dir = score_root / task_id
        score_path = score_dir / "score.json"
        manifest_path = score_dir / "score_manifest.json"
        checklist_path = task_dir / "checklist.yaml"
        errors: list[str] = []
        try:
            score = load_json(score_path)
            manifest = load_json(manifest_path)
            checklist = load_yaml(checklist_path)
        except Exception as exc:  # continue auditing the rest of the denominator
            records.append(
                {
                    "task_id": task_id,
                    "case_unit_id": receipt_task.get("case_unit_id"),
                    "agent": receipt_task.get("agent"),
                    "released_label": "",
                    "native_verdict": "",
                    "native_reason": "",
                    "stronger_verdict": "",
                    "stronger_reason": "",
                    "label_agreement": False,
                    "native_S_stronger_F": False,
                    "record_level_conflict_status": "not_auditable",
                    "structural_valid": False,
                    "errors": [f"failed to load task result: {exc}"],
                    "error_count": 1,
                }
            )
            continue

        for schema_error in sorted(
            schema_validator.iter_errors(score), key=lambda item: list(item.absolute_path)
        ):
            location = ".".join(str(part) for part in schema_error.absolute_path) or "<root>"
            errors.append(f"score schema: {location}: {schema_error.message}")
        try:
            validate_score_guardrails(score, checklist, workspace_root=task_dir)
        except CodexScoreError as exc:
            errors.append(str(exc))

        checklist_sha = sha256_file(checklist_path)
        if checklist_sha != receipt_task.get("checklist_sha256"):
            errors.append("checklist hash differs from transfer receipt")
        plan_task = plan_by_task.get(task_id)
        if plan_task is None:
            errors.append("task missing from remote task plan")
        elif checklist_sha != plan_task.get("checklist_sha256"):
            errors.append("checklist hash differs from remote task plan")
        if score.get("case_unit_id") != receipt_task.get("case_unit_id"):
            errors.append("score case_unit_id differs from transfer receipt")

        expected_manifest = {
            "model": EXPECTED_MODEL,
            "reasoning_effort": EXPECTED_REASONING,
            "service_tier": EXPECTED_SERVICE_TIER,
            "checklist_sha256": checklist_sha,
            "score_prompt_sha256": expected_prompt_sha,
            "score_schema_sha256": expected_schema_sha,
        }
        for key, expected in expected_manifest.items():
            if manifest.get(key) != expected:
                errors.append(f"manifest {key} mismatch")
        try:
            if parse_time(str(manifest["scored_at"])) <= freeze_time:
                errors.append("score timestamp is not after checklist freeze")
        except Exception:
            errors.append("manifest scored_at is missing or invalid")

        native_label = load_json(task_dir / "native_label.json")
        exact_raw_run = load_json(task_dir / "released_label_source/raw_run.json")
        native_output = load_json(task_dir / "evidence/native_run/native_evaluator_output.json")
        score_label = str((score.get("released_evaluator_label") or {}).get("value") or "")
        expected_label = str(native_label.get("value") or "")
        if expected_label not in {"success", "fail"}:
            errors.append("saved released evaluator label is not success/fail")
        if score_label != expected_label or exact_raw_run.get("native_label") != expected_label:
            errors.append("released evaluator label does not match exact retained source")
        if (score.get("released_evaluator_label") or {}).get("source") != native_label.get("source"):
            errors.append("released evaluator label source pointer drift")

        if (task_dir / "evidence/raw_run.json").exists():
            errors.append("model-visible evidence unexpectedly contains raw_run.json")
        for relative in (
            "evidence/native_run/run_summary.json",
            "evidence/native_run/native_evaluator_output.json",
        ):
            payload = load_json(task_dir / relative)
            if "success" in payload:
                errors.append(f"model-visible {relative} retains summary-only success")

        model_path, model_output = latest_model_output(score_dir)
        attempt_outputs = model_outputs(score_dir)
        telemetry_attempts = attempt_telemetry(score_dir)
        if model_path is None or model_output is None:
            errors.append("missing final model_output.json")
        else:
            if set(model_output) != {"native", "stronger"}:
                errors.append("model output contains fields outside native/stronger")
            if model_output.get("native") != score.get("native") or model_output.get("stronger") != score.get("stronger"):
                errors.append("final score native/stronger differs from final model output")
            serialized_model_output = json.dumps(model_output, sort_keys=True).lower()
            if "released_evaluator_label" in serialized_model_output or "native_label" in serialized_model_output:
                errors.append("model output contains a released-label field")
        if not telemetry_attempts:
            errors.append("missing attempt-level Codex telemetry")
        else:
            final_telemetry = load_json(telemetry_attempts[-1][1])
            if (final_telemetry.get("codex_exit") or {}).get("returncode") != 0:
                errors.append("final Codex attempt did not exit successfully")

        expected_condition_ids = [
            str(item["id"])
            for item in ((checklist.get("stronger") or {}).get("additional_conditions") or [])
        ]
        checks = (score.get("stronger") or {}).get("condition_checks") or []
        actual_condition_ids = [str(item.get("id")) for item in checks]
        if actual_condition_ids != expected_condition_ids:
            errors.append("stronger condition ID/order mismatch")
        native_verdict = str((score.get("native") or {}).get("verdict") or "")
        evaluator_info = native_output.get("info") or {}
        raw_reward = evaluator_info.get("RAW_REWARD_GLOBAL")
        evaluator_reward = native_output.get("reward")
        evaluator_done = native_output.get("done")
        native_crosscheck = "S" if (
            evaluator_done is True
            and isinstance(evaluator_reward, (int, float))
            and float(evaluator_reward) >= 1.0
            and isinstance(raw_reward, (int, float))
            and float(raw_reward) > 0.0
        ) else "F"
        if native_verdict != native_crosscheck:
            errors.append(
                f"native verdict differs from concrete validator cross-check: {native_verdict} != {native_crosscheck}"
            )
        expected_stronger = expected_stronger_verdict(native_verdict, checks)
        stronger_verdict = str((score.get("stronger") or {}).get("verdict") or "")
        if stronger_verdict != expected_stronger:
            errors.append(
                f"stronger verdict does not aggregate condition checks: {stronger_verdict} != {expected_stronger}"
            )

        agreement = verdict_agrees(score_label, native_verdict)
        conflict_status = "not_applicable_agreement"
        conflict_errors: list[str] = []
        if not agreement:
            conflict_status, conflict_errors = validate_conflict_record(
                task_id, conflict_records.get(task_id)
            )
            errors.extend(conflict_errors)
        elif task_id in conflict_records:
            errors.append("record-level conflict audit supplied for an agreement record")

        records.append(
            {
                "task_id": task_id,
                "case_unit_id": str(receipt_task.get("case_unit_id") or ""),
                "agent": str(receipt_task.get("agent") or ""),
                "released_label": score_label,
                "native_verdict": native_verdict,
                "native_reason": str((score.get("native") or {}).get("reason") or ""),
                "native_pointers": (score.get("native") or {}).get("pointers") or [],
                "native_evaluator_crosscheck": {
                    "expected_verdict": native_crosscheck,
                    "done": evaluator_done,
                    "reward": evaluator_reward,
                    "raw_reward_global": raw_reward,
                },
                "stronger_verdict": stronger_verdict,
                "stronger_reason": str((score.get("stronger") or {}).get("reason") or ""),
                "stronger_condition_checks": checks,
                "label_agreement": agreement,
                "native_S_stronger_F": native_verdict == "S" and stronger_verdict == "F",
                "record_level_conflict_status": conflict_status,
                "record_level_conflict_audit": conflict_records.get(task_id),
                "structural_valid": not errors,
                "errors": errors,
                "error_count": len(errors),
                "score_json": str(score_path),
                "score_manifest": str(manifest_path),
                "final_model_output": str(model_path) if model_path else None,
                "model_attempt_count": len(telemetry_attempts),
                "model_output_count": len(attempt_outputs),
            }
        )

    unexpected_conflict_records = sorted(set(conflict_records) - expected_task_ids)
    if unexpected_conflict_records:
        global_errors.append(f"conflict audit contains unknown tasks: {unexpected_conflict_records}")

    native_counts = Counter(record["native_verdict"] for record in records)
    label_counts = Counter(record["released_label"] for record in records)
    stronger_counts = Counter(record["stronger_verdict"] for record in records)
    agent_summary: dict[str, dict[str, dict[str, int]]] = {}
    case_summary: dict[str, dict[str, dict[str, int]]] = {}
    for grouping_key, target in (("agent", agent_summary), ("case_unit_id", case_summary)):
        grouped: dict[str, dict[str, Counter[str]]] = defaultdict(
            lambda: {"native": Counter(), "released": Counter(), "stronger": Counter()}
        )
        for record in records:
            group = grouped[record[grouping_key]]
            group["native"][record["native_verdict"]] += 1
            group["released"][record["released_label"]] += 1
            group["stronger"][record["stronger_verdict"]] += 1
        for key in sorted(grouped):
            target[key] = {
                dimension: counter_dict(counter)
                for dimension, counter in grouped[key].items()
            }

    mismatches = [record for record in records if not record["label_agreement"]]
    confirmed_conflicts = [
        record
        for record in mismatches
        if record["record_level_conflict_status"] == "confirmed_benchmark_conflict"
    ]
    pending_conflicts = [
        record
        for record in mismatches
        if record["record_level_conflict_status"] == "pending_record_level_audit"
    ]
    structurally_valid = [record for record in records if record["structural_valid"]]
    system_design_checks = {
        "checklist_freeze_precedes_scores": not any(
            "timestamp is not after" in error for record in records for error in record["errors"]
        ),
        "released_label_blinded_from_model_workspace": not any(
            "model-visible" in error for record in records for error in record["errors"]
        ),
        "model_outputs_contain_only_native_and_stronger": not any(
            "model output" in error for record in records for error in record["errors"]
        ),
        "native_scored_as_S_F_U": set(native_counts) <= {"S", "F", "U"},
        "stronger_reported_separately": set(stronger_counts) <= {"NA", "S", "F", "U"},
        "stronger_not_used_as_conflict_inference": True,
        "disagreements_receive_separate_record_level_audit": not pending_conflicts,
        "benchmark_conflict_requires_retained_and_source_pointers": not any(
            "requires nonempty" in error for record in mismatches for error in record["errors"]
        ),
        "scorer_configuration_gpt54_high_default_nonfast_c11": not any(
            error.startswith("task plan") or error.startswith("batch summary") for error in global_errors
        ),
    }
    audit_complete = (
        len(records) == EXPECTED_TASKS
        and not global_errors
        and len(structurally_valid) == EXPECTED_TASKS
        and not pending_conflicts
    )
    report = {
        "schema_version": "miniwob_remaining22_v2_score_audit/v1",
        "audit_status": "complete" if audit_complete else "incomplete_or_flagged",
        "system_design_checks": system_design_checks,
        "global_errors": global_errors,
        "summary": {
            "record_count": len(records),
            "case_count": len({record["case_unit_id"] for record in records}),
            "structurally_valid_count": len(structurally_valid),
            "native_verdicts": counter_dict(native_counts),
            "released_labels": counter_dict(label_counts),
            "stronger_verdicts": counter_dict(stronger_counts),
            "agreement_count": sum(record["label_agreement"] for record in records),
            "disagreement_count": len(mismatches),
            "native_S_stronger_F_count": sum(record["native_S_stronger_F"] for record in records),
            "retry_record_count": sum(record.get("model_attempt_count", 0) > 1 for record in records),
            "model_attempt_count": sum(record.get("model_attempt_count", 0) for record in records),
            "record_level_audit_pending_count": len(pending_conflicts),
            "confirmed_benchmark_conflict_count": len(confirmed_conflicts),
        },
        "by_agent": agent_summary,
        "by_case": case_summary,
        "records": records,
    }

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "audit_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_markdown(output_dir / "audit_report.md", report)
    write_csv(output_dir / "records.csv", records)
    print(
        json.dumps(
            {
                "audit_status": report["audit_status"],
                **report["summary"],
                "global_error_count": len(global_errors),
                "output_dir": str(output_dir),
            },
            ensure_ascii=False,
        )
    )
    return 0 if audit_complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
