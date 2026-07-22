#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ModuleNotFoundError:
    # See the runner for the full operational checks.  Codex enforces the same
    # JSON schema at generation time; this fallback lets the offline audit run
    # its pointer, hash, and binding validation on a desktop Python install.
    class _SchemaError:
        def __init__(self, message: str) -> None:
            self.message = message

    class Draft202012Validator:  # type: ignore[no-redef]
        def __init__(self, _schema: dict[str, Any]) -> None:
            pass

        def iter_errors(self, payload: Any) -> list[_SchemaError]:
            if not isinstance(payload, dict):
                return [_SchemaError("top-level value must be an object")]
            if set(payload) != {"case_unit_id", "case_analysis", "records"}:
                return [_SchemaError("invalid top-level keys")]
            if not isinstance(payload.get("case_analysis"), dict) or not isinstance(payload.get("records"), list) or len(payload["records"]) != 3:
                return [_SchemaError("invalid case_analysis or records collection")]
            return []


POINTER_RE = re.compile(r"^(?P<path>[^:]+)::(?P<location>.+)$")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--contract-root", type=Path, required=True)
    return parser.parse_args()


def pointer_file(workspace: Path, pointer: str) -> Path | None:
    match = POINTER_RE.match(pointer)
    if match is None:
        return None
    path = (workspace / match.group("path")).resolve()
    try:
        path.relative_to(workspace.resolve())
    except ValueError:
        # Packet symlinks intentionally resolve to locked shared sources/evidence.
        pass
    return path if path.is_file() else None


def pointer_location_valid(path: Path, pointer: str) -> bool:
    match = POINTER_RE.match(pointer)
    if match is None:
        return False
    location = match.group("location").strip()
    line_match = re.fullmatch(r"lines?\s+(\d+)(?:-(\d+))?", location)
    if line_match:
        start = int(line_match.group(1))
        end = int(line_match.group(2) or start)
        line_count = sum(1 for _ in path.open("r", encoding="utf-8", errors="replace"))
        return 1 <= start <= end <= line_count
    if path.suffix == ".json":
        try:
            value: Any = load_json(path)
            expression = location[2:] if location.startswith("$.") else location
            tokens = re.findall(r"(?:^|\.)([^.\[\]]+)|\[(\d+)\]", expression)
            if not tokens:
                return False
            for key, index in tokens:
                if key:
                    if not isinstance(value, dict) or key not in value:
                        return False
                    value = value[key]
                else:
                    idx = int(index)
                    if not isinstance(value, list) or idx >= len(value):
                        return False
                    value = value[idx]
            return True
        except Exception:
            return False
    return location in path.read_text(encoding="utf-8", errors="replace")


def pointer_valid(workspace: Path, pointer: str) -> bool:
    path = pointer_file(workspace, pointer)
    return path is not None and pointer_location_valid(path, pointer)


def main() -> int:
    args = parse_args()
    audit_root = args.audit_root.resolve()
    contract_root = args.contract_root.resolve()
    index = load_json(audit_root / "index.json")
    audit_lock = load_json(audit_root / "conflict_review_lock.json")
    validator = Draft202012Validator(load_json(contract_root / "conflict_review.schema.json"))
    findings: list[dict[str, Any]] = []
    flattened: list[dict[str, Any]] = []
    status_counts: collections.Counter[str] = collections.Counter()
    agent_counts: collections.Counter[str] = collections.Counter()
    case_status_counts: collections.Counter[str] = collections.Counter()
    for item in index:
        output = Path(item["output"])
        manifest_path = output.with_suffix(".manifest.json")
        workspace = Path(item["workspace"])
        if not output.is_file() or not manifest_path.is_file():
            findings.append({"case_unit_id": item["case_unit_id"], "code": "missing_output"})
            continue
        payload = load_json(output)
        manifest = load_json(manifest_path)
        for error in validator.iter_errors(payload):
            findings.append({"case_unit_id": item["case_unit_id"], "code": "schema", "detail": error.message})
        if payload.get("case_unit_id") != item["case_unit_id"]:
            findings.append({"case_unit_id": item["case_unit_id"], "code": "case_binding"})
        expected = {(r["run_dir_name"], r["agent_id"], r["released_evaluator_label"]) for r in item["expected_records"]}
        actual = {(r.get("run_dir_name"), r.get("agent_id"), r.get("released_evaluator_label")) for r in payload.get("records", [])}
        if actual != expected or len(payload.get("records", [])) != 3:
            findings.append({"case_unit_id": item["case_unit_id"], "code": "record_binding"})
        if manifest.get("model") != "gpt-5.4" or manifest.get("reasoning_effort") != "high" or manifest.get("service_tier") != "default" or manifest.get("fast_mode") is not False:
            findings.append({"case_unit_id": item["case_unit_id"], "code": "model_config", "detail": manifest})
        if manifest.get("prompt_sha256") != audit_lock.get("prompt_sha256") or manifest.get("schema_sha256") != audit_lock.get("schema_sha256"):
            findings.append({"case_unit_id": item["case_unit_id"], "code": "contract_binding"})
        if manifest.get("output_sha256") != sha256_file(output):
            findings.append({"case_unit_id": item["case_unit_id"], "code": "output_hash"})

        all_case_pointers = list((payload.get("case_analysis") or {}).get("source_pointers", []))
        for pointer in all_case_pointers:
            if not pointer_valid(workspace, str(pointer)):
                findings.append({"case_unit_id": item["case_unit_id"], "code": "case_pointer", "detail": pointer})
        required_case_fragments = [
            "sources/case/official/case_definition.json::user_goal",
            "sources/case/official/case_definition.json::injection_goal",
            "sources/case/official/evaluator_oracle_excerpts.json::",
            "runtime_wiring/official_agentdojo/baseline_attacks.py::",
            "runtime_wiring/official_agentdojo/benchmark.py::",
            "runtime_wiring/agentdojo_worker.py::",
            "runtime_wiring/agentdojo_formal_postprocessor.py::",
            "runtime_wiring/score_evidence_with_codex.py::",
        ]
        for fragment in required_case_fragments:
            if not any(str(pointer).startswith(fragment) for pointer in all_case_pointers):
                findings.append({"case_unit_id": item["case_unit_id"], "code": "missing_case_basis", "detail": fragment})
        if any("score.json::" in str(pointer) or "score_manifest.json::" in str(pointer) for pointer in all_case_pointers):
            findings.append({"case_unit_id": item["case_unit_id"], "code": "score_context_used_as_case_evidence"})
        exact_case_definition = load_json(workspace / "sources/case/official/case_definition.json")
        if exact_case_definition.get("case_unit_id") != item["case_unit_id"]:
            findings.append({"case_unit_id": item["case_unit_id"], "code": "exact_case_source_binding"})
        per_case_status = []
        for record in payload.get("records", []):
            status = str(record.get("audit_status"))
            confirmed_value = record.get("confirmed_benchmark_conflict")
            difference_value = record.get("different_outcome_description")
            if status == "confirmed_conflict" and not (
                confirmed_value is True
                and isinstance(difference_value, str)
                and difference_value.strip()
            ):
                findings.append({"case_unit_id": item["case_unit_id"], "run_dir_name": record.get("run_dir_name"), "code": "status_binding"})
            elif status == "not_confirmed" and not (
                confirmed_value is False and difference_value is None
            ):
                findings.append({"case_unit_id": item["case_unit_id"], "run_dir_name": record.get("run_dir_name"), "code": "status_binding"})
            elif status == "insufficient" and confirmed_value is not None:
                findings.append({"case_unit_id": item["case_unit_id"], "run_dir_name": record.get("run_dir_name"), "code": "status_binding"})
            status_counts[status] += 1
            agent_counts[str(record.get("agent_id"))] += 1
            per_case_status.append(status)
            pointers = [str(pointer) for pointer in record.get("source_pointers", [])]
            unresolved = [pointer for pointer in pointers if not pointer_valid(workspace, pointer)]
            for pointer in unresolved:
                findings.append({"case_unit_id": item["case_unit_id"], "run_dir_name": record.get("run_dir_name"), "code": "record_pointer", "detail": pointer})
            agent_slug = str(record.get("agent_id", "")).lower().replace(" ", "_")
            evidence_prefix = f"records/{agent_slug}/evidence/"
            _, suite, user_task, injection_task = item["case_unit_id"].split(":")
            required_record_fragments = [
                f"{evidence_prefix}artifact_manifest.json::",
                f"{evidence_prefix}native_run/native_evaluator_input.json::",
                f"{evidence_prefix}native_run/native_evaluator_output.json::",
                f"{evidence_prefix}native_run/trace_logs/local/{suite}/{user_task}/none/none.json::",
                f"{evidence_prefix}native_run/trace_logs/local/{suite}/{user_task}/direct/{injection_task}.json::",
            ]
            for fragment in required_record_fragments:
                if not any(pointer.startswith(fragment) for pointer in pointers):
                    findings.append({"case_unit_id": item["case_unit_id"], "run_dir_name": record.get("run_dir_name"), "code": "missing_record_basis", "detail": fragment})
            if any("score.json::" in pointer or "score_manifest.json::" in pointer for pointer in pointers):
                findings.append({"case_unit_id": item["case_unit_id"], "run_dir_name": record.get("run_dir_name"), "code": "score_context_used_as_record_evidence"})
            has_native_output = any(p.startswith(evidence_prefix) and "native_evaluator_output.json::" in p for p in pointers)
            has_trace = any(p.startswith(evidence_prefix) and "/trace_logs/" in p for p in pointers)
            if not has_native_output:
                findings.append({"case_unit_id": item["case_unit_id"], "run_dir_name": record.get("run_dir_name"), "code": "missing_native_evaluator_output_pointer"})
            if not has_trace:
                findings.append({"case_unit_id": item["case_unit_id"], "run_dir_name": record.get("run_dir_name"), "code": "missing_trace_pointer"})
            checks = record.get("non_dispositive_checks")
            if not isinstance(checks, dict) or any(value is not False for value in checks.values()):
                findings.append({"case_unit_id": item["case_unit_id"], "run_dir_name": record.get("run_dir_name"), "code": "non_dispositive_signal_used"})
            relation = ((record.get("semantic_comparison") or {}).get("relation"))
            expected_relations = {
                "confirmed_conflict": {"different_outcome"},
                "not_confirmed": {"same_exact", "same_outcome_weaker_or_under_specified"},
                "insufficient": {"indeterminate"},
            }
            if relation not in expected_relations.get(status, set()):
                findings.append({"case_unit_id": item["case_unit_id"], "run_dir_name": record.get("run_dir_name"), "code": "semantic_relation_binding", "detail": relation})
            if status == "confirmed_conflict":
                has_task = any("sources/" in p and "case_definition.json::" in p for p in pointers + all_case_pointers)
                has_checker = any(("evaluator_oracle_excerpts.json::" in p or p.startswith("runtime_wiring/")) for p in pointers + all_case_pointers)
                has_record = any(p.startswith(f"records/{agent_slug}/evidence/") for p in pointers)
                if not (has_task and has_checker and has_record):
                    findings.append({"case_unit_id": item["case_unit_id"], "run_dir_name": record.get("run_dir_name"), "code": "confirmed_basis", "detail": {"task": has_task, "checker": has_checker, "record": has_record}})
            flattened.append({
                "case_unit_id": item["case_unit_id"],
                "run_dir_name": record.get("run_dir_name"),
                "agent_id": record.get("agent_id"),
                "released_evaluator_label": record.get("released_evaluator_label"),
                "audit_status": status,
                "confirmed_benchmark_conflict": record.get("confirmed_benchmark_conflict"),
                "different_outcome_description": record.get("different_outcome_description"),
                "reason": record.get("reason"),
                "source_pointers": pointers,
                "review_output": str(output),
            })
        case_status_counts["confirmed_conflict" if "confirmed_conflict" in per_case_status else ("insufficient" if "insufficient" in per_case_status else "not_confirmed")] += 1

    output_dir = audit_root / "audit"
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "record_level_conflict_reviews.jsonl").open("w", encoding="utf-8") as handle:
        for row in flattened:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with (output_dir / "confirmed_conflicts.jsonl").open("w", encoding="utf-8") as handle:
        for row in flattened:
            if row["confirmed_benchmark_conflict"] is True:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with (output_dir / "audit_findings.jsonl").open("w", encoding="utf-8") as handle:
        for finding in findings:
            handle.write(json.dumps(finding, ensure_ascii=False) + "\n")
    fieldnames = ["case_unit_id", "run_dir_name", "agent_id", "released_evaluator_label", "audit_status", "confirmed_benchmark_conflict", "different_outcome_description", "reason", "review_output"]
    with (output_dir / "record_level_conflict_reviews.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: row.get(key) for key in fieldnames} for row in flattened)
    summary = {
        "schema_version": "agentdojo_full_record_level_conflict_audit/v1",
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not findings and len(flattened) == 2547 else "fail",
        "case_count": len(index),
        "record_count": len(flattened),
        "record_status_counts": dict(sorted(status_counts.items())),
        "case_status_counts": dict(sorted(case_status_counts.items())),
        "agent_counts": dict(sorted(agent_counts.items())),
        "confirmed_benchmark_conflict_count": sum(row["confirmed_benchmark_conflict"] is True for row in flattened),
        "not_confirmed_count": sum(row["confirmed_benchmark_conflict"] is False for row in flattened),
        "insufficient_count": sum(row["confirmed_benchmark_conflict"] is None for row in flattened),
        "finding_count": len(findings),
        "scores_modified": False,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
