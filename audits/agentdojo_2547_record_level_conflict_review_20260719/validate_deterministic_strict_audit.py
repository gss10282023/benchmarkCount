#!/usr/bin/env python3
"""Validate the deterministic strict conflict audit without using score artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


POINTER_RE = re.compile(r"^(?P<path>[^:]+)::(?P<location>.+)$")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def pointer_valid(packet: Path, pointer: str) -> bool:
    match = POINTER_RE.match(pointer)
    if match is None:
        return False
    path = packet / match.group("path")
    if not path.is_file():
        return False
    location = match.group("location").strip()
    line_match = re.fullmatch(r"lines?\s+(\d+)(?:-(\d+))?", location)
    if line_match:
        start = int(line_match.group(1))
        end = int(line_match.group(2) or start)
        count = sum(1 for _ in path.open("r", encoding="utf-8", errors="replace"))
        return 1 <= start <= end <= count
    if path.suffix == ".json":
        try:
            value: Any = load_json(path)
            expression = location[2:] if location.startswith("$.") else location
            for key, index in re.findall(r"(?:^|\.)([^.\[\]]+)|\[(\d+)\]", expression):
                if key:
                    if not isinstance(value, dict) or key not in value:
                        return False
                    value = value[key]
                elif isinstance(value, list) and int(index) < len(value):
                    value = value[int(index)]
                else:
                    return False
            return True
        except Exception:
            return False
    return location in path.read_text(encoding="utf-8", errors="replace")


def candidates_for(registry: dict[str, Any], suite: str, user_task: str, injection_task: str) -> set[str]:
    found: set[str] = set()
    for candidate in registry["candidates"]:
        if candidate["suite"] != suite:
            continue
        user_tasks = set(candidate["user_tasks"])
        injection_tasks = set(candidate["injection_tasks"])
        if user_tasks and user_task not in user_tasks:
            continue
        if injection_tasks and injection_task not in injection_tasks:
            continue
        found.add(str(candidate["id"]))
    return found


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-root", type=Path, required=True)
    parser.add_argument("--audit-root", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    packet_root = args.packet_root.resolve()
    audit_root = args.audit_root.resolve()
    packet_index = {str(row["case_unit_id"]): row for row in load_json(packet_root / "index.json")}
    audit_index = load_json(audit_root / "index.json")
    registry_path = audit_root / "source_semantic_registry.json"
    component_coverage_path = audit_root / "source_component_coverage.json"
    registry = load_json(registry_path)
    summary = load_json(audit_root / "summary.json")
    findings: list[dict[str, Any]] = []
    flattened: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    relation_counts: Counter[str] = Counter()

    def fail(case_unit_id: str, code: str, run_dir_name: str | None = None, detail: Any = None) -> None:
        row: dict[str, Any] = {"case_unit_id": case_unit_id, "code": code}
        if run_dir_name is not None:
            row["run_dir_name"] = run_dir_name
        if detail is not None:
            row["detail"] = detail
        findings.append(row)

    if len(packet_index) != 849 or len(audit_index) != 849:
        fail("__global__", "case_count", detail={"packet": len(packet_index), "audit": len(audit_index)})
    if summary.get("source_registry", {}).get("sha256") != sha256_file(registry_path):
        fail("__global__", "source_registry_hash")
    if (
        not component_coverage_path.is_file()
        or summary.get("source_component_coverage", {}).get("sha256") != sha256_file(component_coverage_path)
        or summary.get("source_component_coverage", {}).get("component_count") != 132
    ):
        fail("__global__", "source_component_coverage")
    elif load_json(component_coverage_path).get("component_count") != 132:
        fail("__global__", "source_component_coverage_count")
    if summary.get("binding_validation", {}).get("status") != "pass":
        fail("__global__", "binding_validation_status")

    for index_row in audit_index:
        case_unit_id = str(index_row["case_unit_id"])
        packet_row = packet_index.get(case_unit_id)
        if packet_row is None:
            fail(case_unit_id, "not_in_packet_index")
            continue
        packet = Path(packet_row["workspace"])
        output = Path(index_row["output"])
        if not output.is_file():
            fail(case_unit_id, "missing_output")
            continue
        payload = load_json(output)
        if payload.get("case_unit_id") != case_unit_id:
            fail(case_unit_id, "case_binding")
        if payload.get("outcome_exclusion", "").find("score") < 0:
            fail(case_unit_id, "missing_outcome_exclusion")
        _, suite, user_task, injection_task = case_unit_id.split(":")
        expected_candidates = candidates_for(registry, suite, user_task, injection_task)
        actual_case_candidates = set((payload.get("case_analysis") or {}).get("source_candidate_ids", []))
        if actual_case_candidates != expected_candidates:
            fail(case_unit_id, "case_candidate_binding", detail={"expected": sorted(expected_candidates), "actual": sorted(actual_case_candidates)})
        case_pointers = [str(pointer) for pointer in (payload.get("case_analysis") or {}).get("source_pointers", [])]
        for pointer in case_pointers:
            if "score.json" in pointer or "score_manifest" in pointer:
                fail(case_unit_id, "score_artifact_cited", detail=pointer)
            elif not pointer_valid(packet, pointer):
                fail(case_unit_id, "invalid_case_pointer", detail=pointer)
        for fragment in (
            "sources/case/official/case_definition.json::user_goal",
            "sources/case/official/case_definition.json::injection_goal",
            "runtime_wiring/official_agentdojo/benchmark.py::",
            "runtime_wiring/agentdojo_worker.py::",
            "runtime_wiring/agentdojo_formal_postprocessor.py::",
        ):
            if not any(pointer.startswith(fragment) for pointer in case_pointers):
                fail(case_unit_id, "missing_case_basis", detail=fragment)
        records = payload.get("records")
        expected_records = {(str(row["run_dir_name"]), str(row["agent_id"]), str(row["released_evaluator_label"])) for row in packet_row["expected_records"]}
        actual_records = {
            (str(row.get("run_dir_name")), str(row.get("agent_id")), str(row.get("released_evaluator_label")))
            for row in records or [] if isinstance(row, dict)
        }
        if actual_records != expected_records or not isinstance(records, list) or len(records) != 3:
            fail(case_unit_id, "record_identity_set")
            continue
        for record in records:
            run_dir_name = str(record.get("run_dir_name"))
            agent_id = str(record.get("agent_id"))
            agent_slug = agent_id.lower().replace(" ", "_")
            actual_candidates = set(record.get("source_candidate_ids", []))
            if actual_candidates != expected_candidates:
                fail(case_unit_id, "record_candidate_binding", run_dir_name, {"expected": sorted(expected_candidates), "actual": sorted(actual_candidates)})
            status = str(record.get("audit_status"))
            comparison = record.get("semantic_comparison") or {}
            relation = str(comparison.get("relation"))
            if record.get("label_used_in_decision") is not False:
                fail(case_unit_id, "released_label_used", run_dir_name)
            checks = record.get("non_dispositive_checks")
            if not isinstance(checks, dict) or any(value is not False for value in checks.values()):
                fail(case_unit_id, "non_dispositive_check", run_dir_name)
            if record.get("observed_label_misclassification_inferred") is not False:
                fail(case_unit_id, "observed_label_overclaim", run_dir_name)
            if expected_candidates:
                benign = packet / f"records/{agent_slug}/evidence/native_run/trace_logs/local/{suite}/{user_task}/none/none.json"
                injected = packet / f"records/{agent_slug}/evidence/native_run/trace_logs/local/{suite}/{user_task}/direct/{injection_task}.json"
                normal = load_json(benign).get("error") is None and load_json(injected).get("error") is None
                expected_status = "confirmed_conflict" if normal else "insufficient"
                expected_relation = "different_outcome" if normal else "indeterminate"
            else:
                expected_status = "not_confirmed"
                expected_relation = relation
            if status != expected_status:
                fail(case_unit_id, "status_binding", run_dir_name, {"expected": expected_status, "actual": status})
            if expected_candidates and relation != expected_relation:
                fail(case_unit_id, "relation_binding", run_dir_name, {"expected": expected_relation, "actual": relation})
            if status == "confirmed_conflict":
                if record.get("confirmed_benchmark_conflict") is not True or not record.get("different_outcome_description"):
                    fail(case_unit_id, "confirmed_fields", run_dir_name)
            elif status == "not_confirmed":
                if record.get("confirmed_benchmark_conflict") is not False or record.get("different_outcome_description") is not None:
                    fail(case_unit_id, "not_confirmed_fields", run_dir_name)
                if relation not in {"same_exact", "same_outcome_weaker_or_under_specified"}:
                    fail(case_unit_id, "not_confirmed_relation", run_dir_name, relation)
            elif status == "insufficient":
                if record.get("confirmed_benchmark_conflict") is not None or relation != "indeterminate":
                    fail(case_unit_id, "insufficient_fields", run_dir_name)
            else:
                fail(case_unit_id, "unknown_status", run_dir_name, status)
            pointers = [str(pointer) for pointer in record.get("source_pointers", [])]
            for pointer in pointers:
                if "score.json" in pointer or "score_manifest" in pointer:
                    fail(case_unit_id, "score_artifact_cited", run_dir_name, pointer)
                elif not pointer_valid(packet, pointer):
                    fail(case_unit_id, "invalid_record_pointer", run_dir_name, pointer)
            for fragment in (
                f"records/{agent_slug}/evidence/artifact_manifest.json::",
                f"records/{agent_slug}/evidence/native_run/native_evaluator_input.json::",
                f"records/{agent_slug}/evidence/native_run/native_evaluator_output.json::",
                f"records/{agent_slug}/evidence/native_run/trace_logs/local/{suite}/{user_task}/none/none.json::",
                f"records/{agent_slug}/evidence/native_run/trace_logs/local/{suite}/{user_task}/direct/{injection_task}.json::",
            ):
                if not any(pointer.startswith(fragment) for pointer in pointers):
                    fail(case_unit_id, "missing_record_basis", run_dir_name, fragment)
            status_counts[status] += 1
            relation_counts[relation] += 1
            flattened.append({"case_unit_id": case_unit_id, "run_dir_name": run_dir_name})

    report = {
        "schema_version": "agentdojo_strict_record_level_conflict_audit_validation/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not findings else "fail",
        "case_count": len(audit_index),
        "record_count": len(flattened),
        "finding_count": len(findings),
        "status_counts": dict(sorted(status_counts.items())),
        "relation_counts": dict(sorted(relation_counts.items())),
        "checks": [
            "849 exact current-pair case bindings and 2,547 three-agent record bindings",
            "all cited primary source pointers resolve in their own packet",
            "no score.json or score_manifest.json used as audit evidence",
            "locked source-candidate selector matches every per-case and per-record decision",
            "released labels retained but not used in the decision",
            "confirmed/insufficient status matches normal trace dispatch for source-qualified candidate cases",
            "all noncandidate records retain only same-outcome relations",
        ],
    }
    write_json(audit_root / "validation.json", report)
    with (audit_root / "validation_findings.jsonl").open("w", encoding="utf-8") as handle:
        for finding in findings:
            handle.write(json.dumps(finding, ensure_ascii=False) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not findings else 2


if __name__ == "__main__":
    raise SystemExit(main())
