#!/usr/bin/env python3
"""Read-only terminal artifact monitor for the remaining-14 tau3 campaign."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import time
from typing import Any

from evidence_system.core.hashing import sha256_file, sha256_object, sha256_path
from evidence_system.core.schemas import validate_object


ROOT = Path(__file__).resolve().parents[1]
NAMESPACE = "tau3-retail-remaining14-vps-20260716"
RESULT_ROOT = ROOT / "results" / "namespaces" / NAMESPACE / "full" / "tau3_retail"
JOBS_ROOT = ROOT / "results" / "jobs" / "full" / "namespaces" / NAMESPACE
SAMPLES_PATH = ROOT / "monitoring" / "monitor_artifact.jsonl"
ANOMALIES_PATH = ROOT / "monitoring" / "monitor_artifact_anomalies.jsonl"
STATE_PATH = ROOT / "monitoring" / "monitor_artifact_state.json"
SOURCE_BUNDLE_PATH = ROOT / "experiments" / "evidence_contracts" / "source_bundles" / "tau3_retail_remaining14_source_bundle.json"
MANIFEST_PATH = ROOT / "experiments" / "appendix" / "tau3_retail_remaining14_vultr_run_manifest.yaml"
INFRA_PATH = ROOT / "configs" / "tau3_remaining14_vultr.json"
AGENTS_PATH = ROOT / "configs" / "agents.yaml"

CASES = ("104", "85", "88", "42", "44", "55", "63", "43", "96", "4", "48", "110", "9", "24")
AGENTS = ("Agent A", "Agent B", "Agent C")
EXPECTED_MODELS = {
    "Agent A": "openrouter/openai/gpt-5.4",
    "Agent B": "openrouter/anthropic/claude-opus-4.7",
    "Agent C": "openrouter/deepseek/deepseek-v4-pro",
}
EXPECTED_SPLIT_HASH = "8e03ebce7901bd6218e7a7dc3105faa9324091a68058f7fe61c65262868812e8"
EXPECTED_TAU2_COMMIT = "2be691669909439cf88dedc13decf94b7664d262"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def prior_keys(path: Path, field: str) -> set[str]:
    values: set[str] = set()
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line).get(field)
        except (json.JSONDecodeError, AttributeError):
            continue
        if value:
            values.add(str(value))
    return values


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def resolve_pointer(value: Any) -> Path:
    path = Path(str(value or ""))
    return path if path.is_absolute() else ROOT / path


def tree_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(
        candidate.stat().st_size
        for candidate in path.rglob("*")
        if candidate.is_file() and "__pycache__" not in candidate.parts and candidate.suffix != ".pyc"
    )


def load_expected_jobs() -> dict[str, dict[str, Any]]:
    jobs: dict[str, dict[str, Any]] = {}
    for path in sorted(JOBS_ROOT.glob("*.json")):
        job = load_json(path)
        jobs[str(job.get("job_id"))] = job
    return jobs


def expected_job_ids() -> set[str]:
    return {
        f"full-tau3_retail-{case}-agent_{agent[-1].lower()}"
        for agent in AGENTS
        for case in CASES
    }


def audit_job(job: dict[str, Any], adapter: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []

    def issue(code: str, source: Path, expected: Any, observed: Any) -> None:
        errors.append({
            "code": code,
            "source_path": relative(source),
            "expected": expected,
            "observed": observed,
        })

    def expect(code: str, source: Path, observed: Any, expected: Any) -> None:
        if observed != expected:
            issue(code, source, expected, observed)

    job_id = str(job["job_id"])
    case_id = str(job["case_unit_id"])
    agent_id = str(job["agent_id"])
    expected_seed = 107 + CASES.index(case_id)
    expected_model = EXPECTED_MODELS[agent_id]
    raw_path = adapter / "raw_run.json"
    manifest_path = adapter / "artifact_manifest.json"
    environment_path = adapter / "environment.json"
    results_path = adapter / "native_run" / "results.json"
    calls_path = adapter / "llm_calls" / "calls.jsonl"

    try:
        raw = load_json(raw_path)
        artifact_manifest = load_json(manifest_path)
        environment = load_json(environment_path)
        results = load_json(results_path)
    except Exception as exc:
        issue("terminal_json_unreadable", adapter, "four readable JSON objects", f"{type(exc).__name__}: {exc}")
        raw, artifact_manifest, environment, results = {}, {}, {}, {}

    for schema_name, payload, path in (
        ("raw_run", raw, raw_path),
        ("artifact_manifest", artifact_manifest, manifest_path),
    ):
        if payload:
            try:
                report = validate_object(schema_name, payload, raise_on_error=False)
                if report.status != "ok":
                    issue(
                        f"{schema_name}_schema_invalid",
                        path,
                        "ok",
                        [f"{entry.path}: {entry.message}" for entry in report.issues[:10]],
                    )
            except Exception as exc:
                issue(f"{schema_name}_schema_exception", path, "schema validation succeeds", f"{type(exc).__name__}: {exc}")

    identity_fields = (
        "domain", "case_unit_id", "task_id", "record_slot_id", "run_id", "attempt_id",
        "seed", "agent_id", "phase", "experiment_type", "priority", "evidence_contract_id",
        "evidence_contract_version", "evidence_contract_hash",
    )
    for field in identity_fields:
        expect(f"raw_job_{field}_mismatch", raw_path, raw.get(field), job.get(field))
        expect(f"artifact_job_{field}_mismatch", manifest_path, artifact_manifest.get(field), job.get(field))
    expect("environment_job_id_mismatch", environment_path, environment.get("job_id"), job_id)
    expect("environment_run_id_mismatch", environment_path, environment.get("run_id"), job.get("run_id"))
    expect("environment_machine_id_mismatch", environment_path, environment.get("machine_id"), "tau3-vultr-45-76-20-117")
    expect("environment_benchmark_hash_mismatch", environment_path, environment.get("benchmark_config_hash"), job.get("benchmark_config_hash"))
    expect("job_seed_mismatch", raw_path, raw.get("seed"), expected_seed)
    expect("raw_status_not_completed", raw_path, str(raw.get("status") or "").lower(), "completed")
    expect("raw_diagnostic_not_completed", raw_path, str(raw.get("diagnostic_status") or "").lower(), "completed")
    expect("raw_manifest_hash_mismatch", raw_path, raw.get("manifest_hash"), job.get("manifest_hash"))
    expect("raw_namespace_path_mismatch", raw_path, adapter.parent.name, job_id)

    expected_source_hash = sha256_file(SOURCE_BUNDLE_PATH)
    expected_environment_hash = sha256_file(environment_path) if environment_path.exists() else None
    expect("artifact_source_bundle_hash_mismatch", manifest_path, artifact_manifest.get("source_bundle_hash"), expected_source_hash)
    expect("artifact_split_hash_mismatch", manifest_path, artifact_manifest.get("official_splits_hash"), EXPECTED_SPLIT_HASH)
    expect("artifact_environment_hash_mismatch", manifest_path, artifact_manifest.get("environment_hash"), expected_environment_hash)
    expect("raw_artifact_manifest_hash_mismatch", raw_path, raw.get("artifact_manifest_sha256"), sha256_file(manifest_path) if manifest_path.exists() else None)
    expect("raw_artifact_pointer_mismatch", raw_path, resolve_pointer(raw.get("artifact_manifest_path")).resolve(), manifest_path.resolve())
    expect("raw_source_pointer_mismatch", raw_path, resolve_pointer(raw.get("raw_source_path")).resolve(), raw_path.resolve())
    expect("raw_llm_pointer_mismatch", raw_path, resolve_pointer(raw.get("llm_calls_log_path")).resolve(), calls_path.resolve())

    artifacts = artifact_manifest.get("artifacts") if isinstance(artifact_manifest.get("artifacts"), list) else []
    artifact_paths: set[Path] = set()
    artifact_ids: set[str] = set()
    for index, entry in enumerate(artifacts):
        if not isinstance(entry, dict):
            issue("artifact_entry_not_object", manifest_path, "object", type(entry).__name__)
            continue
        artifact_id = str(entry.get("artifact_id") or "")
        if artifact_id in artifact_ids:
            issue("duplicate_artifact_id", manifest_path, "unique", artifact_id)
        artifact_ids.add(artifact_id)
        path = resolve_pointer(entry.get("path")).resolve()
        try:
            path.relative_to(adapter.resolve())
        except ValueError:
            issue("artifact_pointer_outside_job", manifest_path, relative(adapter), relative(path))
        if path in artifact_paths:
            issue("duplicate_artifact_path", manifest_path, "unique", relative(path))
        artifact_paths.add(path)
        if not path.exists():
            issue("artifact_missing", manifest_path, "existing path", relative(path))
            continue
        expect("artifact_sha256_mismatch", path, sha256_path(path), entry.get("sha256"))
        expect("artifact_size_mismatch", path, tree_size(path), entry.get("size_bytes"))
        expect("artifact_source_hash_mismatch", manifest_path, entry.get("source_bundle_hash"), expected_source_hash)
        expect("artifact_split_hash_entry_mismatch", manifest_path, entry.get("official_splits_hash"), EXPECTED_SPLIT_HASH)
        expect("artifact_environment_hash_entry_mismatch", manifest_path, entry.get("environment_hash"), expected_environment_hash)
        object_hash = entry.get("verified_evaluator_output_object_hash")
        if object_hash and path.is_file() and path.suffix == ".json":
            try:
                expect("artifact_object_hash_mismatch", path, sha256_object(json.loads(path.read_text(encoding="utf-8"))), object_hash)
            except Exception as exc:
                issue("artifact_object_hash_unreadable", path, "valid JSON", f"{type(exc).__name__}: {exc}")

    task_logs = sorted((adapter / "native_run").rglob("task.log"))
    sim_statuses = sorted((adapter / "native_run").rglob("sim_status.json"))
    debug_paths = sorted((adapter / "native_run").rglob("llm_debug/*.json"))
    for required in (results_path, environment_path, adapter / "logs" / "stdout.log", adapter / "logs" / "stderr.log", calls_path):
        if required.resolve() not in artifact_paths:
            issue("required_artifact_not_manifested", manifest_path, relative(required), "absent")
    if len(task_logs) != 1:
        issue("task_log_count_mismatch", adapter / "native_run", 1, len(task_logs))
    if len(sim_statuses) != 1:
        issue("sim_status_count_mismatch", adapter / "native_run", 1, len(sim_statuses))
    if not debug_paths:
        issue("llm_debug_missing", adapter / "native_run", ">=1", 0)
    for required in task_logs + sim_statuses + debug_paths:
        if required.resolve() not in artifact_paths:
            issue("native_artifact_not_manifested", manifest_path, relative(required), "absent")

    tasks = results.get("tasks") if isinstance(results.get("tasks"), list) else []
    simulations = results.get("simulations") if isinstance(results.get("simulations"), list) else []
    expect("native_tau2_commit_mismatch", results_path, (results.get("info") or {}).get("git_commit") if isinstance(results.get("info"), dict) else None, EXPECTED_TAU2_COMMIT)
    expect("native_num_trials_mismatch", results_path, (results.get("info") or {}).get("num_trials") if isinstance(results.get("info"), dict) else None, 1)
    expect("native_task_count_mismatch", results_path, len(tasks), 1)
    if tasks:
        expect("native_task_id_mismatch", results_path, str((tasks[0] or {}).get("id")), case_id)
    expect("native_simulation_count_mismatch", results_path, len(simulations), 1)
    reward: Any = None
    termination_reason: Any = None
    if simulations:
        simulation = simulations[0] if isinstance(simulations[0], dict) else {}
        expect("native_simulation_task_id_mismatch", results_path, str(simulation.get("task_id")), case_id)
        # tau2 deterministically derives a per-trial simulation seed from the
        # requested run seed. The requested seed is retained at info.seed and
        # in raw_run/job; simulation.seed is not expected to equal it.
        termination_reason = simulation.get("termination_reason")
        if termination_reason == "infrastructure_error":
            issue("native_infrastructure_error", results_path, "non-infrastructure termination", termination_reason)
        reward_info = simulation.get("reward_info") if isinstance(simulation.get("reward_info"), dict) else {}
        reward = reward_info.get("reward")
    if isinstance(reward, bool) or not isinstance(reward, (int, float)) or not math.isfinite(float(reward)):
        issue("native_reward_not_numeric", results_path, "finite number", reward)
    else:
        expect("raw_native_score_mismatch", raw_path, raw.get("native_score"), float(reward))
        expect("raw_native_label_mismatch", raw_path, raw.get("native_label"), "success" if float(reward) > 0 else "fail")

    info = results.get("info") if isinstance(results.get("info"), dict) else {}
    expect("native_requested_seed_mismatch", results_path, info.get("seed"), expected_seed)
    agent_model = ((info.get("agent_info") or {}).get("llm") if isinstance(info.get("agent_info"), dict) else None)
    user_model = ((info.get("user_info") or {}).get("llm") if isinstance(info.get("user_info"), dict) else None)
    expect("native_agent_model_mismatch", results_path, agent_model, expected_model)
    expect("native_user_model_mismatch", results_path, user_model, expected_model)

    call_count = 0
    if not calls_path.exists() or calls_path.stat().st_size == 0:
        issue("calls_jsonl_missing_or_empty", calls_path, "non-empty", "missing or empty")
    else:
        for line_number, line in enumerate(calls_path.read_text(encoding="utf-8").splitlines(), start=1):
            try:
                call = json.loads(line)
            except json.JSONDecodeError as exc:
                issue("calls_jsonl_invalid_json", calls_path, "valid JSON", f"line {line_number}: {exc}")
                continue
            call_count += 1
            try:
                report = validate_object("llm_call", call, raise_on_error=False)
                if report.status != "ok":
                    issue("llm_call_schema_invalid", calls_path, "ok", f"line {line_number}: {len(report.issues)} issues")
            except Exception as exc:
                issue("llm_call_schema_exception", calls_path, "schema validation succeeds", f"line {line_number}: {type(exc).__name__}: {exc}")
            for field in ("domain", "case_unit_id", "task_id", "run_id", "record_slot_id", "attempt_id", "manifest_hash", "source_bundle_hash", "evidence_contract_id", "contract_version"):
                expected = job.get(field)
                if field == "source_bundle_hash":
                    expected = expected_source_hash
                if call.get(field) != expected:
                    issue(f"llm_call_{field}_mismatch", calls_path, expected, f"line {line_number}: {call.get(field)!r}")
            expect("llm_call_agent_role_mismatch", calls_path, call.get("agent_id_or_role"), agent_id)
            metadata = call.get("response_metadata") if isinstance(call.get("response_metadata"), dict) else {}
            call_name = str(metadata.get("call_name") or "")
            # Native evaluator calls (for example nl_assertions_eval) use the
            # benchmark's evaluator model. Only agent/user-simulator calls are
            # required to use the selected experimental model.
            if call_name in {"agent_response", "user_simulator_response"}:
                expect("llm_call_model_mismatch", calls_path, call.get("model"), expected_model)
            if str(metadata.get("status") or "success").lower() != "success":
                issue("llm_call_non_success", calls_path, "success", f"line {line_number}: {metadata.get('status')!r}")
    if call_count != len(debug_paths):
        issue("llm_call_debug_count_mismatch", calls_path, len(debug_paths), call_count)

    sample = {
        "schema_version": "tau3_remaining14_artifact_monitor/v1",
        "audit_revision": 2,
        "timestamp": now(),
        "event": "terminal_artifact_audit",
        "namespace": NAMESPACE,
        "job_id": job_id,
        "record_slot_id": job.get("record_slot_id"),
        "case_unit_id": case_id,
        "task_id": job.get("task_id"),
        "agent_id": agent_id,
        "seed": job.get("seed"),
        "native_reward": reward,
        "native_termination_reason": termination_reason,
        "artifact_count": len(artifacts),
        "task_log_count": len(task_logs),
        "sim_status_count": len(sim_statuses),
        "llm_debug_count": len(debug_paths),
        "llm_call_count": call_count,
        "raw_run_sha256": sha256_file(raw_path) if raw_path.exists() else None,
        "artifact_manifest_sha256": sha256_file(manifest_path) if manifest_path.exists() else None,
        "results_sha256": sha256_file(results_path) if results_path.exists() else None,
        "status": "PASS" if not errors else "FAIL",
        "error_count": len(errors),
        "error_codes": sorted({entry["code"] for entry in errors}),
    }
    anomalies = [
        {
            "schema_version": "tau3_remaining14_artifact_monitor_anomaly/v1",
            "timestamp": now(),
            "monitor_role": "artifact_monitor",
            "namespace": NAMESPACE,
            "job_id": job_id,
            "record_slot_id": job.get("record_slot_id"),
            "case_unit_id": case_id,
            "agent_id": agent_id,
            "severity": "error",
            "category": "artifact_acceptance",
            "dedupe_key": f"{job_id}:{entry['code']}",
            "signal": entry["code"],
            "source_path": entry["source_path"],
            "expected": entry["expected"],
            "observed": entry["observed"],
            "action_taken": "recorded_only_run_not_interrupted",
        }
        for entry in errors
    ]
    return sample, anomalies


def main() -> int:
    audited: set[str] = set()
    if SAMPLES_PATH.exists():
        for line in SAMPLES_PATH.read_text(encoding="utf-8").splitlines():
            try:
                prior = json.loads(line)
            except json.JSONDecodeError:
                continue
            if int(prior.get("audit_revision") or 1) >= 2 and prior.get("job_id"):
                audited.add(str(prior["job_id"]))
    anomaly_keys = prior_keys(ANOMALIES_PATH, "dedupe_key")
    resolved_anomaly_keys = prior_keys(ANOMALIES_PATH, "resolves_dedupe_key")
    # Revision 1 incorrectly compared tau2's derived per-trial seed to the
    # requested seed and treated native evaluator-model calls as agent calls.
    # Preserve append-only history and explicitly resolve those monitor-only
    # false positives before revision-2 re-audits.
    if ANOMALIES_PATH.exists():
        prior_anomalies = []
        for line in ANOMALIES_PATH.read_text(encoding="utf-8").splitlines():
            try:
                prior_anomalies.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        for prior in prior_anomalies:
            if prior.get("signal") not in {"native_simulation_seed_mismatch", "llm_call_model_mismatch"}:
                continue
            target_key = str(prior.get("dedupe_key") or "")
            if not target_key or target_key in resolved_anomaly_keys:
                continue
            resolution_key = f"resolution:{target_key}:monitor-revision-2"
            append_jsonl(ANOMALIES_PATH, {
                "schema_version": "tau3_remaining14_artifact_monitor_anomaly_resolution/v1",
                "timestamp": now(), "monitor_role": "artifact_monitor", "namespace": NAMESPACE,
                "job_id": prior.get("job_id"), "record_slot_id": prior.get("record_slot_id"),
                "case_unit_id": prior.get("case_unit_id"), "agent_id": prior.get("agent_id"),
                "severity": "info", "category": "monitor_method_correction",
                "dedupe_key": resolution_key, "resolves_dedupe_key": target_key,
                "signal": "monitor_false_positive_retracted",
                "source_path": prior.get("source_path"),
                "expected": "revision-2 tau2 seed/evaluator-model semantics",
                "observed": prior.get("signal"),
                "action_taken": "append_only_correction_run_artifacts_unchanged",
            })
            anomaly_keys.add(resolution_key)
            resolved_anomaly_keys.add(target_key)
    expected = load_expected_jobs()
    structural_errors: list[tuple[str, Any, Any]] = []
    if set(expected) != expected_job_ids():
        structural_errors.append(("expected_job_set_mismatch", sorted(expected_job_ids()), sorted(expected)))
    if len(expected) != 42:
        structural_errors.append(("expected_job_count_mismatch", 42, len(expected)))
    slots = [str(job.get("record_slot_id")) for job in expected.values()]
    if len(set(slots)) != 42:
        structural_errors.append(("expected_slot_uniqueness_failure", 42, len(set(slots))))
    for signal, wanted, observed in structural_errors:
        key = f"global:{signal}"
        if key not in anomaly_keys:
            append_jsonl(ANOMALIES_PATH, {
                "schema_version": "tau3_remaining14_artifact_monitor_anomaly/v1",
                "timestamp": now(), "monitor_role": "artifact_monitor", "namespace": NAMESPACE,
                "job_id": None, "record_slot_id": None, "case_unit_id": None, "agent_id": None,
                "severity": "error", "category": "denominator", "dedupe_key": key,
                "signal": signal, "source_path": relative(JOBS_ROOT), "expected": wanted,
                "observed": observed, "action_taken": "recorded_only_run_not_interrupted",
            })
            anomaly_keys.add(key)

    last_report = 0.0
    while len(audited & set(expected)) < 42:
        actual_dirs = {path.name for path in RESULT_ROOT.iterdir() if path.is_dir()} if RESULT_ROOT.exists() else set()
        for extra in sorted(actual_dirs - set(expected)):
            key = f"global:unexpected_result_job:{extra}"
            if key not in anomaly_keys:
                append_jsonl(ANOMALIES_PATH, {
                    "schema_version": "tau3_remaining14_artifact_monitor_anomaly/v1",
                    "timestamp": now(), "monitor_role": "artifact_monitor", "namespace": NAMESPACE,
                    "job_id": extra, "record_slot_id": None, "case_unit_id": None, "agent_id": None,
                    "severity": "error", "category": "denominator", "dedupe_key": key,
                    "signal": "unexpected_result_job", "source_path": relative(RESULT_ROOT / extra),
                    "expected": "one of the fixed 42 jobs", "observed": extra,
                    "action_taken": "recorded_only_run_not_interrupted",
                })
                anomaly_keys.add(key)

        new_count = 0
        for job_id, job in sorted(expected.items()):
            if job_id in audited:
                continue
            adapter = RESULT_ROOT / job_id / "adapter"
            required = (
                adapter / "raw_run.json", adapter / "artifact_manifest.json",
                adapter / "environment.json", adapter / "native_run" / "results.json",
            )
            if not all(path.exists() for path in required):
                continue
            sample, anomalies = audit_job(job, adapter)
            append_jsonl(SAMPLES_PATH, sample)
            for anomaly in anomalies:
                key = str(anomaly["dedupe_key"])
                if key not in anomaly_keys:
                    append_jsonl(ANOMALIES_PATH, anomaly)
                    anomaly_keys.add(key)
            audited.add(job_id)
            new_count += 1
            print(
                f"{now()} artifact_audit job={job_id} status={sample['status']} "
                f"reward={sample['native_reward']} errors={sample['error_count']}",
                flush=True,
            )

        passed = 0
        failed = 0
        latest_samples: dict[str, dict[str, Any]] = {}
        if SAMPLES_PATH.exists():
            for line in SAMPLES_PATH.read_text(encoding="utf-8").splitlines():
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if payload.get("job_id") not in expected:
                    continue
                latest_samples[str(payload["job_id"])] = payload
            for payload in latest_samples.values():
                if payload.get("status") == "PASS":
                    passed += 1
                elif payload.get("status") == "FAIL":
                    failed += 1
        state = {
            "schema_version": "tau3_remaining14_artifact_monitor_state/v1",
            "updated_at": now(), "namespace": NAMESPACE, "expected_slots": 42,
            "audited_terminal_slots": len(audited & set(expected)), "passed": passed,
            "failed": failed, "unseen": sorted(set(expected) - audited),
            "unexpected_result_jobs": sorted(actual_dirs - set(expected)),
            "anomaly_record_count": len(anomaly_keys),
            "resolved_monitor_false_positive_count": len(resolved_anomaly_keys),
            "unresolved_anomaly_count": len({key for key in anomaly_keys if not key.startswith("resolution:") and key not in resolved_anomaly_keys}),
        }
        write_json_atomic(STATE_PATH, state)
        monotonic = time.monotonic()
        if new_count or monotonic - last_report >= 120:
            print(
                f"{now()} artifact_monitor audited={state['audited_terminal_slots']}/42 "
                f"pass={passed} fail={failed} active_result_dirs={len(actual_dirs)} "
                f"extra={len(state['unexpected_result_jobs'])}",
                flush=True,
            )
            last_report = monotonic
        if len(audited & set(expected)) >= 42:
            break
        time.sleep(30)

    print(f"{now()} artifact_monitor complete audited=42 pass={passed} fail={failed}", flush=True)
    return 0 if failed == 0 and not structural_errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
