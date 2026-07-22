#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ModuleNotFoundError:
    # The Codex output schema is enforced by the CLI.  This small local fallback
    # preserves the additional pre/post-run structural validation when the
    # desktop Python lacks the optional jsonschema package.
    class _SchemaError:
        def __init__(self, message: str) -> None:
            self.message = message

    class Draft202012Validator:  # type: ignore[no-redef]
        def __init__(self, _schema: dict[str, Any]) -> None:
            pass

        def iter_errors(self, payload: Any) -> list[_SchemaError]:
            errors: list[_SchemaError] = []
            if not isinstance(payload, dict):
                return [_SchemaError("top-level value must be an object")]
            required_top = {"case_unit_id", "case_analysis", "records"}
            if set(payload) != required_top:
                errors.append(_SchemaError("top-level keys must be case_unit_id, case_analysis, records"))
            analysis = payload.get("case_analysis")
            required_analysis = {"apparent_benchmark_claim", "actual_checked_outcome", "record_binding_and_aggregation", "source_pointers"}
            if not isinstance(analysis, dict) or set(analysis) != required_analysis:
                errors.append(_SchemaError("invalid case_analysis structure"))
            elif not all(isinstance(analysis.get(key), str) and analysis[key] for key in required_analysis - {"source_pointers"}):
                errors.append(_SchemaError("case_analysis text fields must be nonempty strings"))
            elif not isinstance(analysis.get("source_pointers"), list) or len(analysis["source_pointers"]) < 3 or not all(isinstance(item, str) and item for item in analysis["source_pointers"]):
                errors.append(_SchemaError("case_analysis source_pointers must contain at least three strings"))
            records = payload.get("records")
            required_record = {"run_dir_name", "agent_id", "released_evaluator_label", "audit_status", "confirmed_benchmark_conflict", "different_outcome_description", "reason", "semantic_comparison", "source_pointers", "non_dispositive_checks"}
            required_comparison = {"apparent_claim", "actual_checker", "aggregation", "record_binding", "relation"}
            required_checks = {"label_agreement_used_as_proof", "label_disagreement_used_as_proof", "stronger_result_used_as_proof"}
            if not isinstance(records, list) or len(records) != 3:
                return errors + [_SchemaError("records must contain exactly three objects")]
            for index, record in enumerate(records):
                if not isinstance(record, dict) or set(record) != required_record:
                    errors.append(_SchemaError(f"record {index} has invalid keys")); continue
                if record.get("agent_id") not in {"Agent A", "Agent B", "Agent C"} or record.get("released_evaluator_label") not in {"success", "fail"} or record.get("audit_status") not in {"confirmed_conflict", "not_confirmed", "insufficient"}:
                    errors.append(_SchemaError(f"record {index} has invalid identity/status enum"))
                comparison = record.get("semantic_comparison")
                if not isinstance(comparison, dict) or set(comparison) != required_comparison or comparison.get("relation") not in {"same_exact", "same_outcome_weaker_or_under_specified", "different_outcome", "indeterminate"} or not all(isinstance(comparison.get(key), str) and comparison[key] for key in required_comparison - {"relation"}):
                    errors.append(_SchemaError(f"record {index} has invalid semantic_comparison"))
                pointers = record.get("source_pointers")
                if not isinstance(pointers, list) or len(pointers) < 7 or not all(isinstance(item, str) and item for item in pointers):
                    errors.append(_SchemaError(f"record {index} has invalid source_pointers"))
                checks = record.get("non_dispositive_checks")
                if not isinstance(checks, dict) or set(checks) != required_checks or any(value is not False for value in checks.values()):
                    errors.append(_SchemaError(f"record {index} has invalid non_dispositive_checks"))
            return errors


PRINT_LOCK = threading.Lock()
SUMMARY_LOCK = threading.Lock()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--contract-root", type=Path, required=True)
    parser.add_argument("--max-parallel", type=int, default=130)
    parser.add_argument("--model", default="gpt-5.4")
    parser.add_argument("--reasoning-effort", default="high")
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--codex-home-template", type=Path, required=True)
    parser.add_argument("--launch-stagger-seconds", type=float, default=0.5)
    return parser.parse_args()


def output_errors(payload: dict[str, Any], item: dict[str, Any], validator: Draft202012Validator) -> list[str]:
    errors = [error.message for error in validator.iter_errors(payload)]
    if payload.get("case_unit_id") != item["case_unit_id"]:
        errors.append("case_unit_id mismatch")
    records = payload.get("records") if isinstance(payload.get("records"), list) else []
    expected = {(r["run_dir_name"], r["agent_id"], r["released_evaluator_label"]) for r in item["expected_records"]}
    actual = {
        (r.get("run_dir_name"), r.get("agent_id"), r.get("released_evaluator_label"))
        for r in records if isinstance(r, dict)
    }
    if actual != expected or len(records) != 3:
        errors.append("record identity/label set mismatch")
    case_pointers = [str(pointer) for pointer in (payload.get("case_analysis") or {}).get("source_pointers", [])]
    required_case_pointer_fragments = [
        "sources/case/official/case_definition.json::user_goal",
        "sources/case/official/case_definition.json::injection_goal",
        "sources/case/official/evaluator_oracle_excerpts.json::",
        "runtime_wiring/official_agentdojo/baseline_attacks.py::",
        "runtime_wiring/official_agentdojo/benchmark.py::",
        "runtime_wiring/agentdojo_worker.py::",
        "runtime_wiring/agentdojo_formal_postprocessor.py::",
        "runtime_wiring/score_evidence_with_codex.py::",
    ]
    for fragment in required_case_pointer_fragments:
        if not any(pointer.startswith(fragment) for pointer in case_pointers):
            errors.append(f"case analysis missing required current-pair source: {fragment}")
    if any("score.json::" in pointer or "score_manifest.json::" in pointer for pointer in case_pointers):
        errors.append("case analysis cites prior score context as evidence")
    _, suite, user_task, injection_task = str(item["case_unit_id"]).split(":")
    for record in records:
        if not isinstance(record, dict):
            continue
        status = record.get("audit_status")
        comparison = record.get("semantic_comparison") if isinstance(record.get("semantic_comparison"), dict) else {}
        relation = comparison.get("relation")
        confirmed = record.get("confirmed_benchmark_conflict")
        difference = record.get("different_outcome_description")
        if status == "confirmed_conflict" and not (
            confirmed is True and isinstance(difference, str) and difference.strip()
        ):
            errors.append("confirmed_conflict must bind true and a nonempty different outcome")
        elif status == "not_confirmed" and not (
            confirmed is False and difference is None
        ):
            errors.append("not_confirmed must bind false and null different outcome")
        elif status == "insufficient" and confirmed is not None:
            errors.append("insufficient must bind null confirmed value")
        if status == "confirmed_conflict" and relation != "different_outcome":
            errors.append("confirmed_conflict requires different_outcome semantic relation")
        elif status == "insufficient" and relation != "indeterminate":
            errors.append("insufficient requires indeterminate semantic relation")
        elif status == "not_confirmed" and relation not in {"same_exact", "same_outcome_weaker_or_under_specified"}:
            errors.append("not_confirmed requires a same-outcome semantic relation")
        pointers = record.get("source_pointers") if isinstance(record.get("source_pointers"), list) else []
        pointers = [str(pointer) for pointer in pointers]
        agent_slug = str(record.get("agent_id", "")).lower().replace(" ", "_")
        evidence_prefix = f"records/{agent_slug}/evidence/"
        required_record_fragments = [
            f"{evidence_prefix}artifact_manifest.json::",
            f"{evidence_prefix}native_run/native_evaluator_input.json::",
            f"{evidence_prefix}native_run/native_evaluator_output.json::",
            f"{evidence_prefix}native_run/trace_logs/local/{suite}/{user_task}/none/none.json::",
            f"{evidence_prefix}native_run/trace_logs/local/{suite}/{user_task}/direct/{injection_task}.json::",
        ]
        for fragment in required_record_fragments:
            if not any(pointer.startswith(fragment) for pointer in pointers):
                errors.append(f"{agent_slug}: missing required retained source: {fragment}")
        if any("score.json::" in pointer or "score_manifest.json::" in pointer for pointer in pointers):
            errors.append(f"{agent_slug}: cites prior score context as evidence")
        if not any(str(pointer).startswith(evidence_prefix) and "native_evaluator_output.json::" in str(pointer) for pointer in pointers):
            errors.append(f"{agent_slug}: missing original native_evaluator_output pointer")
        if not any(str(pointer).startswith(evidence_prefix) and "/trace_logs/" in str(pointer) for pointer in pointers):
            errors.append(f"{agent_slug}: missing original trace/action pointer")
        checks = record.get("non_dispositive_checks")
        if not isinstance(checks, dict) or any(value is not False for value in checks.values()):
            errors.append(f"{agent_slug}: non-dispositive score/label/stronger signal was used")
    return errors


def valid_output(path: Path, item: dict[str, Any], validator: Draft202012Validator) -> bool:
    try:
        payload = load_json(path)
    except Exception:
        return False
    return isinstance(payload, dict) and not output_errors(payload, item, validator)


def review_one(
    item: dict[str, Any], *, model: str, reasoning_effort: str, timeout_seconds: int,
    max_attempts: int, validator: Draft202012Validator, prompt: str, schema_path: Path,
    prompt_sha: str, schema_sha: str, codex_home_template: Path,
    codex_homes_root: Path, launch_index: int, launch_slots: int,
    launch_stagger_seconds: float,
) -> dict[str, Any]:
    workspace = Path(item["workspace"]).resolve()
    output = Path(item["output"]).resolve()
    log_prefix = Path(item["log_prefix"]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    log_prefix.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = output.with_suffix(".manifest.json")
    if valid_output(output, item, validator) and manifest_path.is_file():
        return {"status": "reused", "case_unit_id": item["case_unit_id"], "attempt": 0}

    # A ThreadPoolExecutor worker performs only one review at a time.  Reusing one
    # Codex home per worker avoids concurrent SQLite/shell-snapshot writes while
    # keeping hundreds of completed-case homes from consuming the local disk.
    agent_home = codex_homes_root / f"worker_{threading.get_ident()}"
    agent_home.mkdir(parents=True, exist_ok=True)
    for name in ("auth.json", "models_cache.json", "installation_id"):
        source = codex_home_template / name
        if source.is_file():
            shutil.copy2(source, agent_home / name)
    (agent_home / "shell_snapshots").mkdir(exist_ok=True)
    command = [
        "codex", "exec", "--cd", str(workspace), "--skip-git-repo-check", "--ephemeral",
        "--ignore-user-config", "--sandbox", "read-only", "--model", model,
        "-c", f'model_reasoning_effort="{reasoning_effort}"',
        "-c", 'model_verbosity="low"', "-c", 'service_tier="default"',
        "--color", "never", "--json", "--output-schema", str(schema_path),
        "-o", str(output), prompt,
    ]
    started = time.monotonic()
    errors: list[str] = []
    initial_delay = (launch_index % max(1, launch_slots)) * max(0.0, launch_stagger_seconds)
    if initial_delay:
        time.sleep(initial_delay)
    for attempt in range(1, max_attempts + 1):
        if output.exists():
            output.unlink()
        stdout_path = Path(f"{log_prefix}.attempt_{attempt:02d}.events.jsonl")
        stderr_path = Path(f"{log_prefix}.attempt_{attempt:02d}.stderr.log")
        try:
            with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
                result = subprocess.run(
                    command, stdout=stdout, stderr=stderr, text=True,
                    timeout=timeout_seconds, check=False,
                    env={**os.environ, "CODEX_HOME": str(agent_home)},
                )
        except subprocess.TimeoutExpired:
            errors.append(f"attempt {attempt}: timeout after {timeout_seconds}s")
            continue
        if result.returncode != 0:
            tail = stderr_path.read_text(encoding="utf-8", errors="replace")[-1600:]
            errors.append(f"attempt {attempt}: codex exit {result.returncode}: {tail}")
            if attempt < max_attempts:
                time.sleep(30 * attempt)
            continue
        if not valid_output(output, item, validator):
            try:
                payload = load_json(output)
                detail = output_errors(payload, item, validator)
            except Exception as exc:
                detail = [f"unreadable output: {exc}"]
            errors.append(f"attempt {attempt}: {'; '.join(detail[:8])}")
            if attempt < max_attempts:
                time.sleep(15 * attempt)
            continue
        manifest = {
            "schema_version": "agentdojo_record_level_conflict_review_manifest/v1",
            "case_unit_id": item["case_unit_id"],
            "model": model,
            "reasoning_effort": reasoning_effort,
            "service_tier": "default",
            "fast_mode": False,
            "prompt_sha256": prompt_sha,
            "schema_sha256": schema_sha,
            "workspace": str(workspace),
            "output": str(output),
            "output_sha256": sha256_file(output),
            "attempt": attempt,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(time.monotonic() - started, 3),
        }
        write_json(manifest_path, manifest)
        return {"status": "success", "case_unit_id": item["case_unit_id"], "attempt": attempt}
    return {"status": "failed", "case_unit_id": item["case_unit_id"], "errors": errors, "duration_seconds": round(time.monotonic() - started, 3)}


def main() -> int:
    args = parse_args()
    audit_root = args.audit_root.resolve()
    contract_root = args.contract_root.resolve()
    index = load_json(audit_root / "index.json")
    schema_path = contract_root / "conflict_review.schema.json"
    prompt_path = contract_root / "conflict_review.prompt.md"
    validator = Draft202012Validator(load_json(schema_path))
    prompt = prompt_path.read_text(encoding="utf-8")
    prompt_sha = sha256_file(prompt_path)
    schema_sha = sha256_file(schema_path)
    codex_home_template = args.codex_home_template.resolve()
    if not (codex_home_template / "auth.json").is_file():
        raise SystemExit(f"missing Codex auth template: {codex_home_template / 'auth.json'}")
    codex_homes_root = audit_root / "codex_homes"
    codex_homes_root.mkdir(parents=True, exist_ok=True)
    if len(index) != 849:
        raise SystemExit(f"expected 849 cases, found {len(index)}")
    summary_path = audit_root / "run_summary.json"
    summary = {
        "started_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat(),
        "model": args.model, "reasoning_effort": args.reasoning_effort, "service_tier": "default",
        "fast_mode": False, "max_parallel": args.max_parallel,
        "isolated_codex_homes": True, "launch_stagger_seconds": args.launch_stagger_seconds,
        "case_count": 849, "record_count": 2547,
        "completed": 0, "success": 0, "reused": 0, "failed": 0,
    }
    write_json(summary_path, summary)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_parallel) as executor:
        futures = {
            executor.submit(
                review_one, item, model=args.model, reasoning_effort=args.reasoning_effort,
                timeout_seconds=args.timeout_seconds, max_attempts=args.max_attempts,
                validator=validator, prompt=prompt, schema_path=schema_path,
                prompt_sha=prompt_sha, schema_sha=schema_sha,
                codex_home_template=codex_home_template, codex_homes_root=codex_homes_root,
                launch_index=launch_index, launch_slots=args.max_parallel,
                launch_stagger_seconds=args.launch_stagger_seconds,
            ): item for launch_index, item in enumerate(index)
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
                print(f"[{summary['completed']}/849] {result['status']} {result['case_unit_id']}", flush=True)
    results.sort(key=lambda item: item["case_unit_id"])
    write_json(audit_root / "run_results.json", results)
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
