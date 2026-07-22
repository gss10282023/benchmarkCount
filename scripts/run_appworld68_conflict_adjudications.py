#!/usr/bin/env python3
"""Run source-corrected AppWorld conflict adjudications against official data 0.2.0."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from run_appworld68_record_level_conflict_reviews import (
    load_json,
    pointer_error,
    public_readability_errors,
    sha256_file,
    write_json,
)


PRINT_LOCK = threading.Lock()
SUMMARY_LOCK = threading.Lock()
AGENTS = {"agent_a": "Agent A", "agent_b": "Agent B", "agent_c": "Agent C"}
SAME_RELATIONS = {"same_exact", "same_outcome_weaker_or_under_specified"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--contract-root", type=Path, required=True)
    parser.add_argument("--codex-home-template", type=Path, required=True)
    parser.add_argument("--max-parallel", type=int, default=34)
    parser.add_argument("--model", default="gpt-5.4")
    parser.add_argument("--reasoning-effort", default="high")
    parser.add_argument("--service-tier", default="default")
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--launch-stagger-seconds", type=float, default=0.5)
    parser.add_argument("--case-id", action="append", default=[])
    return parser.parse_args()


def adjudication_errors(
    payload: dict[str, Any],
    item: dict[str, Any],
    validator: Draft202012Validator,
    workspace: Path,
) -> list[str]:
    errors = [error.message for error in validator.iter_errors(payload)]
    case_id = str(item["case_unit_id"])
    if payload.get("case_unit_id") != case_id:
        errors.append("case_unit_id mismatch")
    expected = {
        (row["task_id"], row["agent_id"], row["released_evaluator_label"])
        for row in item["expected_records"]
    }
    records = payload.get("records") if isinstance(payload.get("records"), list) else []
    actual = {
        (row.get("task_id"), row.get("agent_id"), row.get("released_evaluator_label"))
        for row in records
        if isinstance(row, dict)
    }
    if len(records) != 3 or actual != expected:
        errors.append("record identity/label set mismatch")

    case_status = payload.get("case_conflict_status")
    difference = payload.get("different_outcome_description")
    for record in records:
        if not isinstance(record, dict):
            continue
        status = record.get("audit_status")
        relation = record.get("relation")
        confirmed = record.get("confirmed_benchmark_conflict")
        if case_status == "confirmed_conflict":
            if not isinstance(difference, str) or not difference.strip():
                errors.append("confirmed case lacks different-outcome description")
            if status != "confirmed_conflict" or relation != "different_outcome" or confirmed is not True:
                errors.append(f"{record.get('task_id')}: confirmed case contract violated")
        elif case_status == "not_confirmed":
            if difference is not None:
                errors.append("not-confirmed case has different-outcome description")
            if status != "not_confirmed" or relation not in SAME_RELATIONS or confirmed is not False:
                errors.append(f"{record.get('task_id')}: not-confirmed case contract violated")
        elif case_status == "insufficient":
            if difference is not None:
                errors.append("insufficient case has different-outcome description")
            if status != "insufficient" or relation != "indeterminate" or confirmed is not None:
                errors.append(f"{record.get('task_id')}: insufficient case contract violated")

    top_pointers = [str(value) for value in payload.get("source_pointers", [])]
    for required in (
        "task_source_lock.json::",
        "actual_run_receipt.json::",
        "official/specs.json::",
        "official/ground_truth/evaluation.py::",
    ):
        if not any(value.startswith(required) for value in top_pointers):
            errors.append(f"case analysis lacks authoritative binding pointer {required}")
    for agent in AGENTS:
        required = f"records/{agent}/retained_record/native_evaluator_output.json::"
        if not any(value.startswith(required) for value in top_pointers):
            errors.append(f"case analysis lacks actual native output for {agent}")

    conflict_pointer_groups = [top_pointers]
    all_pointer_groups: list[list[str]] = [top_pointers]
    for record in records:
        if not isinstance(record, dict):
            continue
        agent = str(record.get("agent_id", "")).lower().replace(" ", "_")
        pointers = [str(value) for value in record.get("source_pointers", [])]
        conflict_pointer_groups.append(pointers)
        all_pointer_groups.append(pointers)
        required = (
            "actual_run_receipt.json::",
            "official/specs.json::",
            "official/ground_truth/evaluation.py::",
            f"records/{agent}/retained_record/native_evaluator_output.json::",
            f"records/{agent}/retained_record/run_summary.json::",
        )
        for prefix in required:
            if not any(value.startswith(prefix) for value in pointers):
                errors.append(f"{agent}: missing actual-run binding pointer {prefix}")
        trace_prefix = f"records/{agent}/retained_record/appworld_task_output/"
        if not any(
            value.startswith(trace_prefix)
            and any(piece in value for piece in ("/logs/api_calls.jsonl::", "/logs/environment_io.md::", "/dbs/"))
            for value in pointers
        ):
            errors.append(f"{agent}: missing actual API/environment/DB pointer")

    for pointers in conflict_pointer_groups:
        if any(
            value.startswith(
                (
                    "HISTORICAL_V4_SOURCE_LOCK.json::",
                    "source_hotfix_record.json::",
                    "first_pass_review.json::",
                    "checklist.yaml::",
                    "case_packet.md::",
                )
            )
            or "/score/" in value
            or "joined_record.json::" in value
            for value in pointers
        ):
            errors.append("historical/scorer/join source used in official conflict proof")

    provenance = payload.get("source_provenance") or {}
    provenance_pointers = [str(value) for value in provenance.get("source_pointers", [])]
    all_pointer_groups.append(provenance_pointers)
    for required in (
        "task_source_lock.json::",
        "actual_run_receipt.json::",
        "HISTORICAL_V4_SOURCE_LOCK.json::",
        "source_hotfix_record.json::",
    ):
        if not any(value.startswith(required) for value in provenance_pointers):
            errors.append(f"provenance review lacks pointer {required}")

    official = payload.get("official_case_assessment") or {}
    all_pointer_groups.append([str(value) for value in official.get("source_pointers", [])])
    system = payload.get("our_system_assessment") or {}
    system_pointers = [str(value) for value in system.get("source_pointers", [])]
    all_pointer_groups.append(system_pointers)
    for required in (
        "checklist.yaml::",
        "HISTORICAL_V4_SOURCE_LOCK.json::",
        "source_hotfix_record.json::",
    ):
        if not any(value.startswith(required) for value in system_pointers):
            errors.append(f"system review lacks pointer {required}")
    valid_task_ids = {row[0] for row in expected}
    for issue in system.get("additional_issues", []):
        if not isinstance(issue, dict):
            continue
        if not set(issue.get("record_ids", [])) <= valid_task_ids:
            errors.append("system issue references foreign record id")
        all_pointer_groups.append([str(value) for value in issue.get("source_pointers", [])])

    for pointers in all_pointer_groups:
        for pointer in pointers:
            problem = pointer_error(pointer, workspace)
            if problem:
                errors.append(problem)
    return errors


def valid_output(
    path: Path,
    item: dict[str, Any],
    validator: Draft202012Validator,
    workspace: Path,
) -> bool:
    try:
        payload = load_json(path)
        return isinstance(payload, dict) and not adjudication_errors(
            payload, item, validator, workspace
        )
    except Exception:
        return False


def run_one(
    item: dict[str, Any],
    *,
    audit_root: Path,
    contract_root: Path,
    auth_template: Path,
    validator: Draft202012Validator,
    prompt: str,
    model: str,
    reasoning: str,
    service_tier: str,
    timeout: int,
    max_attempts: int,
    launch_delay: float,
    index_number: int,
    max_parallel: int,
) -> dict[str, Any]:
    case_id = str(item["case_unit_id"])
    workspace_value = Path(str(item["workspace"]))
    workspace = (workspace_value if workspace_value.is_absolute() else audit_root / workspace_value).resolve()
    output = audit_root / "adjudication_outputs" / f"{case_id}.json"
    manifest = output.with_suffix(".manifest.json")
    log_prefix = audit_root / "adjudication_logs" / case_id
    output.parent.mkdir(parents=True, exist_ok=True)
    log_prefix.parent.mkdir(parents=True, exist_ok=True)
    if valid_output(output, item, validator, workspace) and manifest.is_file():
        return {"case_unit_id": case_id, "status": "reused", "attempt": 0}
    codex_home = audit_root / "adjudication_codex_homes" / case_id
    codex_home.mkdir(parents=True, exist_ok=True)
    for name in ("auth.json", "models_cache.json", "installation_id"):
        source = auth_template / name
        if source.is_file():
            shutil.copy2(source, codex_home / name)
    (codex_home / "shell_snapshots").mkdir(exist_ok=True)
    command = [
        "codex",
        "exec",
        "--cd",
        str(workspace),
        "--skip-git-repo-check",
        "--ephemeral",
        "--ignore-user-config",
        "--sandbox",
        "read-only",
        "--model",
        model,
        "-c",
        f'model_reasoning_effort="{reasoning}"',
        "-c",
        'model_verbosity="low"',
        "-c",
        f'service_tier="{service_tier}"',
        "--color",
        "never",
        "--json",
        "--output-schema",
        str(contract_root / "adjudication.schema.json"),
        "-o",
        str(output),
        prompt,
    ]
    if launch_delay:
        time.sleep((index_number % max_parallel) * launch_delay)
    started = time.monotonic()
    errors: list[str] = []
    for attempt in range(1, max_attempts + 1):
        output.unlink(missing_ok=True)
        events = Path(f"{log_prefix}.attempt_{attempt:02d}.events.jsonl")
        stderr_path = Path(f"{log_prefix}.attempt_{attempt:02d}.stderr.log")
        try:
            with events.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
                result = subprocess.run(
                    command,
                    stdout=stdout,
                    stderr=stderr,
                    text=True,
                    check=False,
                    timeout=timeout,
                    env={**os.environ, "CODEX_HOME": str(codex_home)},
                )
        except subprocess.TimeoutExpired:
            errors.append(f"attempt {attempt}: timeout")
            continue
        if result.returncode == 0 and valid_output(output, item, validator, workspace):
            write_json(
                manifest,
                {
                    "schema_version": "appworld68_conflict_adjudication_manifest/v1",
                    "case_unit_id": case_id,
                    "model": model,
                    "reasoning_effort": reasoning,
                    "service_tier": service_tier,
                    "fast_mode": False,
                    "sandbox": "read-only",
                    "auth_mode": "codex_login",
                    "prompt_sha256": sha256_file(contract_root / "adjudication.prompt.md"),
                    "schema_sha256": sha256_file(contract_root / "adjudication.schema.json"),
                    "output_sha256": sha256_file(output),
                    "attempt": attempt,
                    "duration_seconds": round(time.monotonic() - started, 3),
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            return {"case_unit_id": case_id, "status": "success", "attempt": attempt}
        if result.returncode != 0:
            errors.append(f"attempt {attempt}: codex exit {result.returncode}")
        else:
            try:
                detail = adjudication_errors(load_json(output), item, validator, workspace)
            except Exception as exc:
                detail = [f"unreadable output: {exc}"]
            errors.append(f"attempt {attempt}: {'; '.join(detail[:12])}")
        if attempt < max_attempts:
            time.sleep(15 * attempt)
    return {
        "case_unit_id": case_id,
        "status": "failed",
        "errors": errors,
        "duration_seconds": round(time.monotonic() - started, 3),
    }


def main() -> int:
    args = parse_args()
    if args.service_tier.lower() == "fast" or args.max_parallel < 1:
        raise SystemExit("fast is forbidden and parallelism must be positive")
    audit_root = args.audit_root.resolve()
    contract_root = args.contract_root.resolve()
    auth_template = args.codex_home_template.resolve()
    index = load_json(audit_root / "index.json")
    requested = set(args.case_id)
    if requested:
        index = [item for item in index if item["case_unit_id"] in requested]
    if len(index) != (len(requested) if requested else 68):
        raise SystemExit("case selection/denominator differs")
    validator = Draft202012Validator(load_json(contract_root / "adjudication.schema.json"))
    prompt = (contract_root / "adjudication.prompt.md").read_text(encoding="utf-8")
    for item in index:
        workspace_value = Path(str(item["workspace"]))
        workspace = workspace_value if workspace_value.is_absolute() else audit_root / workspace_value
        for required in (
            "actual_run_receipt.json",
            "first_pass_review.json",
            "task_source_lock.json",
            "source_hotfix_record.json",
            "HISTORICAL_V4_SOURCE_LOCK.json",
            "official/specs.json",
            "official/ground_truth/evaluation.py",
        ):
            if not (workspace / required).is_file():
                raise SystemExit(f"missing {required} for {item['case_unit_id']}")
        readability = public_readability_errors(workspace)
        if readability:
            raise SystemExit("workspace not sandbox-readable:\n" + "\n".join(readability))
    summary_path = audit_root / (
        "adjudication_run_summary.json" if not requested else "adjudication_canary_summary.json"
    )
    summary: dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "service_tier": args.service_tier,
        "fast_mode": False,
        "sandbox": "read-only",
        "auth_mode": "codex_login",
        "max_parallel": args.max_parallel,
        "case_count": len(index),
        "record_count": len(index) * 3,
        "completed": 0,
        "success": 0,
        "reused": 0,
        "failed": 0,
    }
    write_json(summary_path, summary)
    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_parallel) as executor:
        futures = [
            executor.submit(
                run_one,
                item,
                audit_root=audit_root,
                contract_root=contract_root,
                auth_template=auth_template,
                validator=validator,
                prompt=prompt,
                model=args.model,
                reasoning=args.reasoning_effort,
                service_tier=args.service_tier,
                timeout=args.timeout_seconds,
                max_attempts=args.max_attempts,
                launch_delay=args.launch_stagger_seconds,
                index_number=index_number,
                max_parallel=args.max_parallel,
            )
            for index_number, item in enumerate(index)
        ]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            with SUMMARY_LOCK:
                summary["completed"] += 1
                summary[result["status"]] += 1
                summary["updated_at"] = datetime.now(timezone.utc).isoformat()
                write_json(summary_path, summary)
            with PRINT_LOCK:
                print(
                    f"[{summary['completed']}/{len(index)}] {result['status']} {result['case_unit_id']}",
                    flush=True,
                )
    results.sort(key=lambda row: row["case_unit_id"])
    write_json(
        audit_root
        / ("adjudication_run_results.json" if not requested else "adjudication_canary_results.json"),
        results,
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
