#!/usr/bin/env python3
"""Run the AppWorld-68 strict record-level audit with isolated Codex homes."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator


PRINT_LOCK = threading.Lock()
SUMMARY_LOCK = threading.Lock()
AGENT_NAMES = {"agent_a": "Agent A", "agent_b": "Agent B", "agent_c": "Agent C"}
RELATIONS_SAME = {"same_exact", "same_outcome_weaker_or_under_specified"}
LINE_RE = re.compile(r"^(?:lines?\s+|L)(\d+)(?:-(?:L)?(\d+))?$", re.IGNORECASE)


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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def public_readability_errors(workspace: Path) -> list[str]:
    """Reject packets whose modes would hide sources from the review sandbox."""
    errors: list[str] = []
    paths = [workspace, *workspace.rglob("*")]
    for path in paths:
        if path.is_symlink():
            errors.append(f"symlink forbidden: {path}")
            continue
        mode = path.stat().st_mode & 0o777
        required = 0o555 if path.is_dir() else 0o444
        if mode & required != required:
            errors.append(f"not sandbox-readable: {path} mode={mode:04o}")
            if len(errors) >= 20:
                break
    return errors


def pointer_error(pointer: str, workspace: Path) -> str | None:
    if "::" not in pointer:
        return f"pointer lacks selector: {pointer}"
    relative, selector = pointer.split("::", 1)
    posix = PurePosixPath(relative)
    if not relative or posix.is_absolute() or ".." in posix.parts or not selector.strip():
        return f"unsafe or empty pointer: {pointer}"
    if len(relative) > 4096 or any(len(part) > 255 for part in posix.parts):
        preview = relative[:160] + ("..." if len(relative) > 160 else "")
        return f"pointer path too long: {preview}"
    path = workspace / Path(*posix.parts)
    try:
        if path.is_symlink() or not path.is_file():
            return f"pointer target missing: {pointer}"
    except OSError as exc:
        preview = relative[:160] + ("..." if len(relative) > 160 else "")
        return f"pointer target unreadable ({exc.errno}): {preview}"
    line_match = LINE_RE.fullmatch(selector.strip())
    if line_match:
        start = int(line_match.group(1))
        end = int(line_match.group(2) or start)
        line_count = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
        if start < 1 or end < start or end > line_count:
            return f"pointer line range invalid: {pointer}"
    return None


def output_errors(
    payload: dict[str, Any], item: dict[str, Any], validator: Draft202012Validator, audit_root: Path
) -> list[str]:
    errors = [error.message for error in validator.iter_errors(payload)]
    case_id = str(item["case_unit_id"])
    workspace_value = Path(str(item["workspace"]))
    workspace = workspace_value if workspace_value.is_absolute() else audit_root / workspace_value
    if payload.get("case_unit_id") != case_id:
        errors.append("case_unit_id mismatch")
    records = payload.get("records") if isinstance(payload.get("records"), list) else []
    expected = {
        (row["task_id"], row["agent_id"], row["released_evaluator_label"])
        for row in item["expected_records"]
    }
    actual = {
        (row.get("task_id"), row.get("agent_id"), row.get("released_evaluator_label"))
        for row in records
        if isinstance(row, dict)
    }
    if len(records) != 3 or actual != expected:
        errors.append("record identity/label set mismatch")

    case_analysis = payload.get("case_analysis") if isinstance(payload.get("case_analysis"), dict) else {}
    case_pointers = [str(value) for value in case_analysis.get("source_pointers", [])]
    required_case_prefixes = (
        "official/specs.json::$.instruction",
        "official/ground_truth/evaluation.py::evaluate",
        "official/ground_truth/test_data.json::$",
        "runtime_wiring/official_appworld/task.py::Task.load",
        "runtime_wiring/official_appworld/ground_truth.py::GroundTruth.load",
        "runtime_wiring/official_appworld/evaluator.py::TestTracker.success",
        "runtime_wiring/official_appworld/evaluator.py::evaluate_task",
        "runtime_wiring/our_system/appworld_official_worker.py::run_official_job",
        "runtime_wiring/our_system/run_campaign.py::run_slot",
        "runtime_wiring/our_system/audit_join_appworld68_blind_scores.py::main",
    )
    for prefix in required_case_prefixes:
        if not any(pointer.startswith(prefix) for pointer in case_pointers):
            errors.append(f"case analysis missing required source: {prefix}")
    if any("/score/" in pointer or "joined_record.json::" in pointer for pointer in case_pointers):
        errors.append("case conflict analysis cites scorer/join conclusion")
    official_assessment = case_analysis.get("official_benchmark_assessment") or {}
    if official_assessment.get("status") == "no_issue_found" and official_assessment.get("category") != "none":
        errors.append("no official issue must use category none")
    if official_assessment.get("status") != "no_issue_found" and official_assessment.get("category") == "none":
        errors.append("official issue/limitation cannot use category none")

    all_pointer_groups: list[list[str]] = [case_pointers]
    for record in records:
        if not isinstance(record, dict):
            continue
        status = record.get("audit_status")
        confirmed = record.get("confirmed_benchmark_conflict")
        difference = record.get("different_outcome_description")
        semantic = record.get("semantic_comparison") if isinstance(record.get("semantic_comparison"), dict) else {}
        relation = semantic.get("relation")
        if status == "confirmed_conflict":
            if confirmed is not True or relation != "different_outcome" or not isinstance(difference, str) or not difference.strip():
                errors.append("confirmed_conflict relation/value contract violated")
        elif status == "not_confirmed":
            if confirmed is not False or relation not in RELATIONS_SAME or difference is not None:
                errors.append("not_confirmed relation/value contract violated")
        elif status == "insufficient":
            if confirmed is not None or relation != "indeterminate" or difference is not None:
                errors.append("insufficient relation/value contract violated")

        agent_slug = str(record.get("agent_id", "")).lower().replace(" ", "_")
        prefix = f"records/{agent_slug}/retained_record/"
        pointers = [str(value) for value in record.get("source_pointers", [])]
        required_record_prefixes = (
            f"{prefix}artifact_manifest.json::",
            f"{prefix}native_evaluator_input.json::",
            f"{prefix}native_evaluator_output.json::",
            f"{prefix}run_summary.json::",
            f"{prefix}job.json::",
        )
        for required in required_record_prefixes:
            if not any(pointer.startswith(required) for pointer in pointers):
                errors.append(f"{agent_slug}: missing retained binding source: {required}")
        trace_prefix = f"{prefix}appworld_task_output/"
        if not any(
            pointer.startswith(trace_prefix)
            and any(part in pointer for part in ("/logs/api_calls.jsonl::", "/logs/environment_io.md::", "/dbs/"))
            for pointer in pointers
        ):
            errors.append(f"{agent_slug}: missing retained action/environment/DB source")
        if any("/score/" in pointer or "joined_record.json::" in pointer for pointer in pointers):
            errors.append(f"{agent_slug}: conflict pointers cite scorer/join conclusion")
        checks = record.get("non_dispositive_checks")
        if not isinstance(checks, dict) or any(value is not False for value in checks.values()):
            errors.append(f"{agent_slug}: non-dispositive signal used as conflict proof")
        system = record.get("our_system_review") if isinstance(record.get("our_system_review"), dict) else {}
        issues = system.get("issues") if isinstance(system.get("issues"), list) else []
        if system.get("overall_status") == "confirmed_issue" and not issues:
            errors.append(f"{agent_slug}: confirmed system issue has empty issues")
        if system.get("overall_status") == "no_issue_found" and issues:
            errors.append(f"{agent_slug}: no_issue_found has nonempty issues")
        all_pointer_groups.extend(
            [
                pointers,
                [str(value) for value in system.get("source_pointers", [])],
                *[
                    [str(value) for value in issue.get("source_pointers", [])]
                    for issue in issues
                    if isinstance(issue, dict)
                ],
            ]
        )
    checklist_assessment = case_analysis.get("checklist_and_case_packet_assessment") or {}
    all_pointer_groups.append([str(value) for value in checklist_assessment.get("source_pointers", [])])
    all_pointer_groups.append([str(value) for value in official_assessment.get("source_pointers", [])])
    for pointers in all_pointer_groups:
        for pointer in pointers:
            problem = pointer_error(pointer, workspace)
            if problem:
                errors.append(problem)
    return errors


def valid_output(
    path: Path, item: dict[str, Any], validator: Draft202012Validator, audit_root: Path
) -> bool:
    try:
        payload = load_json(path)
    except Exception:
        return False
    return isinstance(payload, dict) and not output_errors(payload, item, validator, audit_root)


def review_one(
    item: dict[str, Any], *, audit_root: Path, model: str, reasoning_effort: str,
    service_tier: str, timeout_seconds: int, max_attempts: int,
    validator: Draft202012Validator, prompt: str, schema_path: Path, prompt_sha: str,
    schema_sha: str, codex_home_template: Path, codex_homes_root: Path,
    launch_index: int, max_parallel: int, launch_stagger_seconds: float,
) -> dict[str, Any]:
    workspace_value = Path(str(item["workspace"]))
    output_value = Path(str(item["output"]))
    log_value = Path(str(item["log_prefix"]))
    workspace = (workspace_value if workspace_value.is_absolute() else audit_root / workspace_value).resolve()
    output = (output_value if output_value.is_absolute() else audit_root / output_value).resolve()
    log_prefix = (log_value if log_value.is_absolute() else audit_root / log_value).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    log_prefix.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = output.with_suffix(".manifest.json")
    if valid_output(output, item, validator, audit_root) and manifest_path.is_file():
        return {"status": "reused", "case_unit_id": item["case_unit_id"], "attempt": 0}

    codex_home = codex_homes_root / str(item["case_unit_id"])
    codex_home.mkdir(parents=True, exist_ok=True)
    for name in ("auth.json", "models_cache.json", "installation_id"):
        source = codex_home_template / name
        if source.is_file():
            shutil.copy2(source, codex_home / name)
    (codex_home / "shell_snapshots").mkdir(exist_ok=True)
    command = [
        "codex", "exec", "--cd", str(workspace), "--skip-git-repo-check", "--ephemeral",
        "--ignore-user-config", "--sandbox", "read-only", "--model", model,
        "-c", f'model_reasoning_effort="{reasoning_effort}"',
        "-c", 'model_verbosity="low"', "-c", f'service_tier="{service_tier}"',
        "--color", "never", "--json", "--output-schema", str(schema_path),
        "-o", str(output), prompt,
    ]
    started = time.monotonic()
    errors: list[str] = []
    delay = (launch_index % max_parallel) * max(0.0, launch_stagger_seconds)
    if delay:
        time.sleep(delay)
    for attempt in range(1, max_attempts + 1):
        output.unlink(missing_ok=True)
        events_path = Path(f"{log_prefix}.attempt_{attempt:02d}.events.jsonl")
        stderr_path = Path(f"{log_prefix}.attempt_{attempt:02d}.stderr.log")
        try:
            with events_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
                result = subprocess.run(
                    command,
                    stdout=stdout,
                    stderr=stderr,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                    env={**os.environ, "CODEX_HOME": str(codex_home)},
                )
        except subprocess.TimeoutExpired:
            errors.append(f"attempt {attempt}: timeout after {timeout_seconds}s")
            continue
        if result.returncode != 0:
            tail = stderr_path.read_text(encoding="utf-8", errors="replace")[-1800:]
            errors.append(f"attempt {attempt}: codex exit {result.returncode}: {tail}")
        elif valid_output(output, item, validator, audit_root):
            write_json(
                manifest_path,
                {
                    "schema_version": "appworld68_record_level_conflict_review_manifest/v1",
                    "case_unit_id": item["case_unit_id"],
                    "model": model,
                    "reasoning_effort": reasoning_effort,
                    "service_tier": service_tier,
                    "fast_mode": False,
                    "sandbox": "read-only",
                    "auth_mode": "codex_login",
                    "prompt_sha256": prompt_sha,
                    "schema_sha256": schema_sha,
                    "workspace": str(workspace),
                    "output": str(output),
                    "output_sha256": sha256_file(output),
                    "attempt": attempt,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "duration_seconds": round(time.monotonic() - started, 3),
                },
            )
            return {"status": "success", "case_unit_id": item["case_unit_id"], "attempt": attempt}
        else:
            try:
                detail = output_errors(load_json(output), item, validator, audit_root)
            except Exception as exc:
                detail = [f"unreadable output: {exc}"]
            errors.append(f"attempt {attempt}: {'; '.join(detail[:12])}")
        if attempt < max_attempts:
            time.sleep(15 * attempt)
    return {
        "status": "failed",
        "case_unit_id": item["case_unit_id"],
        "errors": errors,
        "duration_seconds": round(time.monotonic() - started, 3),
    }


def main() -> int:
    args = parse_args()
    if args.service_tier.lower() == "fast":
        raise SystemExit("fast service tier is forbidden")
    if args.max_parallel < 1 or args.max_attempts < 1:
        raise SystemExit("parallelism and attempts must be positive")
    audit_root = args.audit_root.resolve()
    contract_root = args.contract_root.resolve()
    schema_path = contract_root / "review.schema.json"
    prompt_path = contract_root / "review.prompt.md"
    validator = Draft202012Validator(load_json(schema_path))
    prompt = prompt_path.read_text(encoding="utf-8")
    index = load_json(audit_root / "index.json")
    if not isinstance(index, list) or len(index) != 68:
        raise SystemExit(f"expected 68 indexed cases, found {len(index) if isinstance(index, list) else 'invalid'}")
    requested = set(args.case_id)
    if requested:
        known = {str(item["case_unit_id"]) for item in index}
        if not requested <= known:
            raise SystemExit(f"unknown case ids: {sorted(requested - known)}")
        index = [item for item in index if item["case_unit_id"] in requested]
    for item in index:
        workspace_value = Path(str(item["workspace"]))
        workspace = workspace_value if workspace_value.is_absolute() else audit_root / workspace_value
        readability = public_readability_errors(workspace)
        if readability:
            raise SystemExit(
                "audit packet is not readable by the Codex sandbox:\n" + "\n".join(readability)
            )
    codex_home_template = args.codex_home_template.resolve()
    if not (codex_home_template / "auth.json").is_file():
        raise SystemExit(f"missing Codex auth: {codex_home_template / 'auth.json'}")
    codex_homes_root = audit_root / "codex_homes"
    codex_homes_root.mkdir(parents=True, exist_ok=True)
    summary_path = audit_root / ("run_summary.json" if not requested else "canary_run_summary.json")
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
        futures = {
            executor.submit(
                review_one,
                item,
                audit_root=audit_root,
                model=args.model,
                reasoning_effort=args.reasoning_effort,
                service_tier=args.service_tier,
                timeout_seconds=args.timeout_seconds,
                max_attempts=args.max_attempts,
                validator=validator,
                prompt=prompt,
                schema_path=schema_path,
                prompt_sha=sha256_file(prompt_path),
                schema_sha=sha256_file(schema_path),
                codex_home_template=codex_home_template,
                codex_homes_root=codex_homes_root,
                launch_index=index_number,
                max_parallel=args.max_parallel,
                launch_stagger_seconds=args.launch_stagger_seconds,
            ): item
            for index_number, item in enumerate(index)
        }
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            with SUMMARY_LOCK:
                summary["completed"] += 1
                summary[result["status"]] += 1
                summary["updated_at"] = datetime.now(timezone.utc).isoformat()
                write_json(summary_path, summary)
            with PRINT_LOCK:
                print(f"[{summary['completed']}/{len(index)}] {result['status']} {result['case_unit_id']}", flush=True)
    results.sort(key=lambda value: value["case_unit_id"])
    write_json(audit_root / ("run_results.json" if not requested else "canary_run_results.json"), results)
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
