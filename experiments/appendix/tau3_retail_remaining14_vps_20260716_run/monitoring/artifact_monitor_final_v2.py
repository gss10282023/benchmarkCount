#!/usr/bin/env python3
"""Independent post-repair strict acceptance audit for all 42 canonical runs."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import artifact_monitor as base


ROOT = base.ROOT
ROWS_PATH = ROOT / "monitoring" / "monitor_artifact_final_v2.jsonl"
ANOMALIES_PATH = ROOT / "monitoring" / "monitor_artifact_final_v2_anomalies.jsonl"
FINAL_PATH = ROOT / "monitoring" / "monitor_artifact_resume_final_v2.json"
REPAIR_PATH = ROOT / "monitoring" / "internal_retry_manifest_repair.json"
ARCHIVE_ROOT = ROOT / "monitoring" / "pre_retry_manifest_repair"
DIAGNOSTIC_ROOT = ROOT / "monitoring" / "internal_retry_diagnostics"
REPAIRED = {
    "full-tau3_retail-104-agent_c",
    "full-tau3_retail-55-agent_c",
}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"not an object: {path}")
    return value


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    text = "".join(
        json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n"
        for value in values
    )
    path.write_text(text, encoding="utf-8")


def artifact_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(entry["path"]): entry
        for entry in manifest.get("artifacts", [])
        if isinstance(entry, dict) and entry.get("path")
    }


def repair_audit(
    job: dict[str, Any],
    adapter: Path,
    repair: dict[str, Any],
    base_anomalies: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    job_id = str(job["job_id"])
    case_id = str(job["case_unit_id"])
    errors: list[dict[str, Any]] = []
    checks: dict[str, Any] = {}

    def issue(code: str, source: Path | str, expected: Any, observed: Any) -> None:
        errors.append({
            "signal": code,
            "source_path": rel(source) if isinstance(source, Path) else str(source),
            "expected": expected,
            "observed": observed,
        })

    def expect(code: str, source: Path | str, observed: Any, expected: Any) -> None:
        if observed != expected:
            issue(code, source, expected, observed)

    rows = [row for row in repair.get("rows", []) if row.get("job_id") == job_id]
    if len(rows) != 1:
        issue("repair_row_count", REPAIR_PATH, 1, len(rows))
        return errors, checks
    repair_row = rows[0]
    diagnostic_path = ROOT / str(repair_row["diagnostic_path"])
    archive = ARCHIVE_ROOT / job_id
    manifest_path = adapter / "artifact_manifest.json"
    raw_path = adapter / "raw_run.json"
    results_path = adapter / "native_run" / "results.json"
    manifest = load(manifest_path)
    raw = load(raw_path)
    results = load(results_path)
    diagnostic = load(diagnostic_path)
    old_manifest = load(archive / "artifact_manifest.json")
    old_raw = load(archive / "raw_run.json")
    old_map = artifact_map(old_manifest)
    new_map = artifact_map(manifest)
    diagnostic_entries = {
        str(entry["path"]): entry
        for entry in diagnostic.get("failed_retry_files", [])
    }
    diagnostic_paths = set(diagnostic_entries)

    expect("repair_status", REPAIR_PATH, repair.get("status"), "PASS")
    expect("repair_native_modified_flag", REPAIR_PATH, repair.get("native_files_modified"), False)
    expect("repair_benchmark_modified_flag", REPAIR_PATH, repair.get("benchmark_runs_modified"), False)
    expect("repair_case_identity", REPAIR_PATH, str(repair_row.get("case_unit_id")), case_id)
    expect("repair_new_manifest_hash", manifest_path, sha256(manifest_path), repair_row.get("new_artifact_manifest_sha256"))
    expect("repair_new_raw_hash", raw_path, sha256(raw_path), repair_row.get("new_raw_run_sha256"))
    expect("repair_old_manifest_hash", archive / "artifact_manifest.json", sha256(archive / "artifact_manifest.json"), repair_row.get("old_artifact_manifest_sha256"))
    expect("repair_old_raw_hash", archive / "raw_run.json", sha256(archive / "raw_run.json"), repair_row.get("old_raw_run_sha256"))
    expect("repair_new_artifact_count", manifest_path, len(manifest.get("artifacts", [])), repair_row.get("new_artifact_count"))
    expect("repair_old_artifact_count", archive / "artifact_manifest.json", len(old_manifest.get("artifacts", [])), repair_row.get("old_artifact_count"))

    raw_diffs = {
        key for key in set(old_raw) | set(raw)
        if old_raw.get(key) != raw.get(key)
    }
    expect("repair_raw_diff_scope", raw_path, sorted(raw_diffs), ["artifact_manifest_sha256"])
    expect("repair_raw_manifest_hash_pointer", raw_path, raw.get("artifact_manifest_sha256"), sha256(manifest_path))
    old_top = {key: value for key, value in old_manifest.items() if key != "artifacts"}
    new_top = {key: value for key, value in manifest.items() if key != "artifacts"}
    expect("repair_manifest_top_level_changed", manifest_path, new_top, old_top)

    new_entries = list(manifest.get("artifacts", []))
    new_ids = [str(entry.get("artifact_id")) for entry in new_entries]
    duplicate_ids = sorted(key for key, count in Counter(new_ids).items() if count > 1)
    expect("repair_artifact_ids_not_unique", manifest_path, duplicate_ids, [])
    expect("repair_artifact_path_uniqueness", manifest_path, len(new_map), len(new_entries))
    retained_changed = [
        path for path, entry in new_map.items()
        if path not in old_map or entry != old_map[path]
    ]
    expect("repair_retained_artifacts_changed", manifest_path, retained_changed, [])
    removed_paths = set(old_map) - set(new_map)
    expect("repair_removed_paths_not_diagnostics", diagnostic_path, sorted(removed_paths), sorted(diagnostic_paths))
    expect("repair_failed_simulation_count", diagnostic_path, diagnostic.get("failed_simulation_count"), repair_row.get("failed_internal_simulations"))
    expect("repair_diagnostic_identity", diagnostic_path, diagnostic.get("job_id"), job_id)

    for path_text, entry in diagnostic_entries.items():
        path = ROOT / path_text
        if not path.is_file():
            issue("repair_diagnostic_file_missing", diagnostic_path, "existing file", path_text)
            continue
        expect("repair_diagnostic_sha_mismatch", path, sha256(path), entry.get("sha256"))
        expect("repair_diagnostic_size_mismatch", path, path.stat().st_size, entry.get("size_bytes"))
        old_entry = old_map.get(path_text)
        if old_entry is None:
            issue("repair_diagnostic_not_in_old_manifest", diagnostic_path, "old manifest entry", path_text)
        else:
            expect("repair_diagnostic_old_sha_mismatch", path, entry.get("sha256"), old_entry.get("sha256"))
            expect("repair_diagnostic_old_size_mismatch", path, entry.get("size_bytes"), old_entry.get("size_bytes"))

    native_files = {
        rel(path): path
        for path in (adapter / "native_run").rglob("*")
        if path.is_file()
    }
    old_native = {
        path: entry for path, entry in old_map.items()
        if f"/{job_id}/adapter/native_run/" in f"/{path}"
    }
    expect("repair_native_file_set_changed", adapter / "native_run", sorted(native_files), sorted(old_native))
    for path_text, path in native_files.items():
        entry = old_native.get(path_text)
        if entry is None:
            continue
        expect("repair_native_sha_changed", path, sha256(path), entry.get("sha256"))
        expect("repair_native_size_changed", path, path.stat().st_size, entry.get("size_bytes"))

    used_dir_text = str(diagnostic.get("used_simulation_dir") or "")
    used_dir = ROOT / used_dir_text
    selected_task = [path for path in new_map if path.endswith("/task.log")]
    selected_status = [path for path in new_map if path.endswith("/sim_status.json")]
    selected_debug = [path for path in new_map if "/llm_debug/" in path]
    expect("repair_selected_task_count", manifest_path, len(selected_task), 1)
    expect("repair_selected_status_count", manifest_path, len(selected_status), 1)
    expect("repair_report_selected_task_count", REPAIR_PATH, repair_row.get("selected_task_log_count"), 1)
    expect("repair_report_selected_status_count", REPAIR_PATH, repair_row.get("selected_sim_status_count"), 1)
    for path_text in selected_task + selected_status + selected_debug:
        try:
            (ROOT / path_text).resolve().relative_to(used_dir.resolve())
        except ValueError:
            issue("repair_selected_artifact_outside_used_sim", manifest_path, used_dir_text, path_text)
    if len(selected_status) == 1:
        selected_status_value = load(ROOT / selected_status[0]).get("status")
        expect("repair_selected_status_not_used", ROOT / selected_status[0], selected_status_value, "used")
    if diagnostic_paths & set(new_map):
        issue("repair_failed_diagnostic_still_decisive", manifest_path, [], sorted(diagnostic_paths & set(new_map)))

    simulations = results.get("simulations") if isinstance(results.get("simulations"), list) else []
    expect("repair_results_simulation_count", results_path, len(simulations), 1)
    if len(simulations) == 1 and isinstance(simulations[0], dict):
        simulation = simulations[0]
        expect("repair_results_used_sim_id", results_path, str(simulation.get("id")), used_dir.name.removeprefix("sim_"))
        expect("repair_results_task_id", results_path, str(simulation.get("task_id")), case_id)
        expect("repair_results_termination", results_path, simulation.get("termination_reason"), "user_stop")
        reward_info = simulation.get("reward_info") if isinstance(simulation.get("reward_info"), dict) else {}
        reward = reward_info.get("reward")
        if isinstance(reward, bool) or not isinstance(reward, (int, float)) or not math.isfinite(float(reward)):
            issue("repair_results_reward_invalid", results_path, "finite numeric reward", reward)
        else:
            expect("repair_results_reward_report", results_path, float(reward), float(repair_row.get("native_reward")))

    stdout_entries = [entry for entry in new_entries if entry.get("artifact_id") == "stdout:stdout"]
    stderr_entries = [entry for entry in new_entries if entry.get("artifact_id") == "stderr:stderr"]
    expect("repair_stdout_entry_count", manifest_path, len(stdout_entries), 1)
    expect("repair_stderr_entry_count", manifest_path, len(stderr_entries), 1)
    for name, entries in (("stdout", stdout_entries), ("stderr", stderr_entries)):
        if len(entries) != 1:
            continue
        path = ROOT / str(entries[0]["path"])
        expect(f"repair_{name}_path", manifest_path, path.resolve(), (adapter / "logs" / f"{name}.log").resolve())
        if not path.is_file():
            issue(f"repair_{name}_missing", manifest_path, "existing file", rel(path))
        elif path.stat().st_size == 0:
            issue(f"repair_{name}_empty", path, ">0 bytes", 0)

    allowed_base: list[dict[str, Any]] = []
    for anomaly in base_anomalies:
        signal = str(anomaly.get("signal"))
        expected_path = str(anomaly.get("expected") or "")
        allowed = signal in {"task_log_count_mismatch", "sim_status_count_mismatch"}
        if signal == "native_artifact_not_manifested" and expected_path in diagnostic_paths:
            allowed = True
        if allowed:
            allowed_base.append(anomaly)
        else:
            errors.append({
                "signal": f"base:{signal}",
                "source_path": anomaly.get("source_path"),
                "expected": anomaly.get("expected"),
                "observed": anomaly.get("observed"),
            })
    expected_allowed = 2 + len(diagnostic_paths)
    expect("repair_base_exclusion_count", manifest_path, len(allowed_base), expected_allowed)

    checks.update({
        "repair_manifest_sha256": sha256(manifest_path),
        "repair_raw_run_sha256": sha256(raw_path),
        "old_manifest_sha256": sha256(archive / "artifact_manifest.json"),
        "old_raw_run_sha256": sha256(archive / "raw_run.json"),
        "artifact_ids_unique": not duplicate_ids,
        "selected_task_log_count": len(selected_task),
        "selected_sim_status_count": len(selected_status),
        "selected_llm_debug_count": len(selected_debug),
        "failed_diagnostic_file_count": len(diagnostic_paths),
        "native_file_count_verified_unchanged": len(native_files),
        "accepted_base_diagnostic_exclusions": len(allowed_base),
        "repair_semantics": "one decisive used simulation; failed internal retry retained and hash-indexed as diagnostic",
    })
    return errors, checks


def main() -> int:
    jobs = base.load_expected_jobs()
    expected_ids = base.expected_job_ids()
    repair = load(REPAIR_PATH)
    rows: list[dict[str, Any]] = []
    anomalies: list[dict[str, Any]] = []
    global_errors: list[dict[str, Any]] = []

    if set(jobs) != expected_ids or len(jobs) != 42:
        global_errors.append({
            "signal": "job_denominator_mismatch",
            "expected": sorted(expected_ids),
            "observed": sorted(jobs),
        })
    result_dirs = {
        path.name for path in base.RESULT_ROOT.iterdir() if path.is_dir()
    } if base.RESULT_ROOT.exists() else set()
    if result_dirs != expected_ids:
        global_errors.append({
            "signal": "result_denominator_mismatch",
            "expected": sorted(expected_ids),
            "observed": sorted(result_dirs),
        })

    for job_id in sorted(jobs):
        job = jobs[job_id]
        adapter = base.RESULT_ROOT / job_id / "adapter"
        sample, base_anomalies = base.audit_job(job, adapter)
        repair_checks: dict[str, Any] = {}
        if job_id in REPAIRED:
            errors, repair_checks = repair_audit(job, adapter, repair, base_anomalies)
            semantics = "selected_used_plus_hash_indexed_internal_retry_diagnostics"
        else:
            errors = [{
                "signal": anomaly.get("signal"),
                "source_path": anomaly.get("source_path"),
                "expected": anomaly.get("expected"),
                "observed": anomaly.get("observed"),
            } for anomaly in base_anomalies]
            semantics = "single_native_simulation"
        row = {
            **sample,
            "schema_version": "tau3_remaining14_artifact_final_v2/v1",
            "audit_revision": 3,
            "timestamp": now(),
            "status": "PASS" if not errors else "FAIL",
            "error_count": len(errors),
            "error_codes": sorted({str(error["signal"]) for error in errors}),
            "acceptance_semantics": semantics,
            "repair_checks": repair_checks,
        }
        rows.append(row)
        for error in errors:
            anomalies.append({
                "schema_version": "tau3_remaining14_artifact_final_v2_anomaly/v1",
                "timestamp": now(),
                "job_id": job_id,
                "case_unit_id": job.get("case_unit_id"),
                "agent_id": job.get("agent_id"),
                "signal": error.get("signal"),
                "source_path": error.get("source_path"),
                "expected": error.get("expected"),
                "observed": error.get("observed"),
                "action_taken": "recorded_only_post_run_audit",
            })

    slots = [str(job.get("record_slot_id")) for job in jobs.values()]
    if len(set(slots)) != 42:
        global_errors.append({"signal": "record_slot_uniqueness", "expected": 42, "observed": len(set(slots))})
    passed = sum(row["status"] == "PASS" for row in rows)
    failed = sum(row["status"] == "FAIL" for row in rows)
    by_agent: dict[str, dict[str, int]] = {}
    rewards: Counter[str] = Counter()
    for agent in base.AGENTS:
        selected = [row for row in rows if row.get("agent_id") == agent]
        by_agent[agent] = {
            "passed": sum(row["status"] == "PASS" for row in selected),
            "failed": sum(row["status"] == "FAIL" for row in selected),
        }
    for row in rows:
        rewards[str(float(row["native_reward"]))] += 1

    write_jsonl(ROWS_PATH, rows)
    write_jsonl(ANOMALIES_PATH, anomalies)
    final = {
        "schema_version": "tau3_remaining14_artifact_final_v2_summary/v1",
        "created_at": now(),
        "namespace": base.NAMESPACE,
        "status": "PASS" if passed == 42 and not global_errors else "FAIL",
        "planned_slots": 42,
        "audited_slots": len(rows),
        "passed": passed,
        "failed": failed,
        "global_errors": global_errors,
        "job_json_count": len(jobs),
        "result_directory_count": len(result_dirs),
        "unique_record_slots": len(set(slots)),
        "by_agent": by_agent,
        "native_reward_distribution": dict(sorted(rewards.items())),
        "repaired_jobs": sorted(REPAIRED),
        "repair_report_sha256": sha256(REPAIR_PATH),
        "repair_semantics": "decisive manifest selects exactly one used simulation; failed internal retry files remain immutable and hash-indexed diagnostics",
        "rows_path": rel(ROWS_PATH),
        "rows_sha256": sha256(ROWS_PATH),
        "row_count": len(rows),
        "anomalies_path": rel(ANOMALIES_PATH),
        "anomalies_sha256": sha256(ANOMALIES_PATH),
        "anomaly_count": len(anomalies),
        "run_results_modified_by_v2_monitor": False,
    }
    write_json(FINAL_PATH, final)
    print(json.dumps(final, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if final["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
