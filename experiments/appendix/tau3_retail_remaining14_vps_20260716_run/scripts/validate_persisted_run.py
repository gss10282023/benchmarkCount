#!/usr/bin/env python3
"""Strict, read-only acceptance audit for the persisted remaining-14 run."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

import yaml


SCRIPT_PATH = Path(__file__).resolve()
EVIDENCE_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[4]
sys.path.insert(0, str(REPO_ROOT / "src"))

from evidence_system.core.schemas import validate_object  # noqa: E402


NAMESPACE = "tau3-retail-remaining14-vps-20260716"
CASES = ("104", "85", "88", "42", "44", "55", "63", "43", "96", "4", "48", "110", "9", "24")
AGENT_SUFFIX = {"Agent A": "a", "Agent B": "b", "Agent C": "c"}
EXPECTED_MODELS = {
    "Agent A": "openrouter/openai/gpt-5.4",
    "Agent B": "openrouter/anthropic/claude-opus-4.7",
    "Agent C": "openrouter/deepseek/deepseek-v4-pro",
}
REPAIRED_JOBS = {
    "full-tau3_retail-104-agent_c",
    "full-tau3_retail-55-agent_c",
}
EXPECTED_HASHES = {
    "original_manifest": "539c5962aba0fa982202db9351e86342363aef8b3dc20a4d9b12b238b6bcd448",
    "run_manifest": "deb8ccb22b5f4c754bcb0f7d2ffe953690969fccc969b209101e7d607e39b18f",
    "agents": "be27141079f93e207586c649743a1671040b606a705f3ef48459f7c3f9381be8",
    "infra": "20b6174d3a8ba28bb69269d17fd9045dc3751da98c20739fe8f6dcd6daaac305",
    "source_bundle": "2fdd836898e16b47f2a5626b47cf3cbbe91ee53ffc7ce139ea2fd6cf2cc1e36a",
    "official_split": "8e03ebce7901bd6218e7a7dc3105faa9324091a68058f7fe61c65262868812e8",
    "artifact_final_v2": "c8bdfa6ab70fb1a8450336e190882413b3ae2b81d24e988abd6bd0be2dc9f894",
    "artifact_rows_v2": "e62af9d30d0713eb2a72dfe7c0dbbb3fbec82b5a142cf21722cf886e4a929421",
    "empty_anomaly_ledger": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "strict_drafts": "8c9a342b6aee7390668f128364d89829a6dca42289368b032b0642b429632532",
    "checked_in_adapter": "641277ad334b21b151921f0dfd21e669ea89bc27a340e9209dd1ac506cd85676",
    "runtime_adapter": "ee4e72912f224585899cf65e1077fa0d4ccfb90bfc1ad4b92c6340feffa9b44a",
}

RESULT_ROOT = REPO_ROOT / "results" / "namespaces" / NAMESPACE / "full" / "tau3_retail"
JOBS_ROOT = EVIDENCE_ROOT / "jobs"
MONITORING_ROOT = EVIDENCE_ROOT / "monitoring"
INPUTS_ROOT = EVIDENCE_ROOT / "inputs"
FINAL_PATH = EVIDENCE_ROOT / "final_acceptance.json"
INVENTORY_PATH = EVIDENCE_ROOT / "bundle_inventory.json"
RELEASE_CHECKSUMS_PATH = EVIDENCE_ROOT / "release_checksums.sha256"
RUNTIME_ROOT = Path("/tmp/tau3_remaining14_controller_20260716.7yPH40")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_object_hash(value: Any) -> str:
    data = json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    if path.is_file():
        return sha256_file(path)
    if not path.is_dir():
        raise FileNotFoundError(path)
    entries = []
    for file_path in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        if "__pycache__" in file_path.parts or file_path.suffix == ".pyc":
            continue
        entries.append({
            "path": file_path.relative_to(path).as_posix(),
            "sha256": sha256_file(file_path),
        })
    return canonical_object_hash(entries)


def path_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(
        candidate.stat().st_size
        for candidate in path.rglob("*")
        if candidate.is_file() and "__pycache__" not in candidate.parts and candidate.suffix != ".pyc"
    )


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"expected object at {path}:{line_number}")
        rows.append(value)
    return rows


def yaml_object(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected YAML object: {path}")
    return value


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def safe_value(value: Any) -> Any:
    if isinstance(value, Path):
        return relative(value)
    if isinstance(value, list) and len(value) > 20:
        return {"count": len(value), "sample": value[:10]}
    if isinstance(value, dict) and len(value) > 20:
        keys = sorted(str(key) for key in value)[:20]
        return {"key_count": len(value), "sample_keys": keys}
    text = str(value)
    if len(text) > 1000:
        return text[:1000] + "..."
    return value


class Audit:
    def __init__(self) -> None:
        self.errors: list[dict[str, Any]] = []
        self.check_count = 0

    def expect(self, code: str, source: Path | str, observed: Any, expected: Any) -> None:
        self.check_count += 1
        if observed == expected:
            return
        self.errors.append({
            "code": code,
            "source": relative(source) if isinstance(source, Path) else source,
            "expected": safe_value(expected),
            "observed": safe_value(observed),
        })

    def require(self, code: str, source: Path | str, condition: bool, detail: str) -> None:
        self.check_count += 1
        if condition:
            return
        self.errors.append({
            "code": code,
            "source": relative(source) if isinstance(source, Path) else source,
            "expected": detail,
            "observed": "condition_not_met",
        })


def expected_job_ids() -> set[str]:
    return {
        f"full-tau3_retail-{case}-agent_{suffix}"
        for case in CASES
        for suffix in AGENT_SUFFIX.values()
    }


def artifact_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(entry["path"]): entry
        for entry in manifest.get("artifacts", [])
        if isinstance(entry, dict) and entry.get("path")
    }


def validate_schema(audit: Audit, schema_name: str, payload: dict[str, Any], source: Path) -> None:
    try:
        report = validate_object(schema_name, payload, raise_on_error=False)
    except Exception as exc:  # pragma: no cover - captured in the report
        audit.expect(f"{schema_name}_schema_exception", source, type(exc).__name__, "no exception")
        return
    audit.expect(f"{schema_name}_schema_status", source, report.status, "ok")


def audit_repaired_job(
    audit: Audit,
    job_id: str,
    adapter: Path,
    manifest: dict[str, Any],
    raw: dict[str, Any],
    repair_report: dict[str, Any],
) -> None:
    rows = [row for row in repair_report.get("rows", []) if row.get("job_id") == job_id]
    audit.expect("repair_row_count", MONITORING_ROOT / "internal_retry_manifest_repair.json", len(rows), 1)
    if len(rows) != 1:
        return
    row = rows[0]
    diagnostic_path = EVIDENCE_ROOT / str(row["diagnostic_path"])
    archive = MONITORING_ROOT / "pre_retry_manifest_repair" / job_id
    current_manifest_path = adapter / "artifact_manifest.json"
    current_raw_path = adapter / "raw_run.json"
    old_manifest_path = archive / "artifact_manifest.json"
    old_raw_path = archive / "raw_run.json"
    diagnostic = load_json(diagnostic_path)
    old_manifest = load_json(old_manifest_path)
    old_raw = load_json(old_raw_path)
    old_map = artifact_map(old_manifest)
    new_map = artifact_map(manifest)
    diagnostic_map = {
        str(entry["path"]): entry
        for entry in diagnostic.get("failed_retry_files", [])
        if isinstance(entry, dict) and entry.get("path")
    }

    audit.expect("repair_new_manifest_hash", current_manifest_path, sha256_file(current_manifest_path), row.get("new_artifact_manifest_sha256"))
    audit.expect("repair_new_raw_hash", current_raw_path, sha256_file(current_raw_path), row.get("new_raw_run_sha256"))
    audit.expect("repair_old_manifest_hash", old_manifest_path, sha256_file(old_manifest_path), row.get("old_artifact_manifest_sha256"))
    audit.expect("repair_old_raw_hash", old_raw_path, sha256_file(old_raw_path), row.get("old_raw_run_sha256"))
    audit.expect("repair_current_manifest_count", current_manifest_path, len(manifest.get("artifacts", [])), row.get("new_artifact_count"))
    audit.expect("repair_old_manifest_count", old_manifest_path, len(old_manifest.get("artifacts", [])), row.get("old_artifact_count"))
    raw_differences = sorted(key for key in set(old_raw) | set(raw) if old_raw.get(key) != raw.get(key))
    audit.expect("repair_raw_change_scope", current_raw_path, raw_differences, ["artifact_manifest_sha256"])
    audit.expect("repair_raw_manifest_pointer", current_raw_path, raw.get("artifact_manifest_sha256"), sha256_file(current_manifest_path))
    audit.expect(
        "repair_manifest_top_level_unchanged",
        current_manifest_path,
        {key: value for key, value in manifest.items() if key != "artifacts"},
        {key: value for key, value in old_manifest.items() if key != "artifacts"},
    )

    removed = set(old_map) - set(new_map)
    audit.expect("repair_removed_set_is_diagnostic", diagnostic_path, sorted(removed), sorted(diagnostic_map))
    audit.expect("repair_failed_simulation_count", diagnostic_path, diagnostic.get("failed_simulation_count"), 1)
    audit.expect("repair_diagnostic_identity", diagnostic_path, diagnostic.get("job_id"), job_id)
    audit.require("repair_failed_files_excluded", current_manifest_path, not (set(new_map) & set(diagnostic_map)), "failed retry files excluded from decisive manifest")

    for path_text, entry in sorted(diagnostic_map.items()):
        path = REPO_ROOT / path_text
        audit.require("repair_diagnostic_file_exists", path, path.is_file(), "diagnostic file exists")
        if not path.is_file():
            continue
        audit.expect("repair_diagnostic_hash", path, sha256_file(path), entry.get("sha256"))
        audit.expect("repair_diagnostic_size", path, path.stat().st_size, entry.get("size_bytes"))
        audit.require("repair_diagnostic_in_old_manifest", old_manifest_path, path_text in old_map, "diagnostic file was present in original manifest")
        if path_text in old_map:
            audit.expect("repair_diagnostic_old_hash", path, entry.get("sha256"), old_map[path_text].get("sha256"))
            audit.expect("repair_diagnostic_old_size", path, entry.get("size_bytes"), old_map[path_text].get("size_bytes"))

    native_files = {
        relative(path): path
        for path in (adapter / "native_run").rglob("*")
        if path.is_file()
    }
    old_native = {
        path_text: entry
        for path_text, entry in old_map.items()
        if f"/{job_id}/adapter/native_run/" in f"/{path_text}"
    }
    audit.expect("repair_native_file_set_unchanged", adapter / "native_run", sorted(native_files), sorted(old_native))
    for path_text, path in sorted(native_files.items()):
        entry = old_native.get(path_text)
        if entry is None:
            continue
        audit.expect("repair_native_hash_unchanged", path, sha256_file(path), entry.get("sha256"))
        audit.expect("repair_native_size_unchanged", path, path.stat().st_size, entry.get("size_bytes"))


def tree_inventory(root: Path, *, relative_to: Path) -> dict[str, str]:
    return {
        path.relative_to(relative_to).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }


def verify_runtime_copy(audit: Audit) -> dict[str, Any]:
    if not RUNTIME_ROOT.is_dir():
        return {"available": False, "verified": False, "reason": "ephemeral controller directory no longer present"}
    comparisons = []
    pairs = (
        (
            RUNTIME_ROOT / "results" / "namespaces" / NAMESPACE,
            REPO_ROOT / "results" / "namespaces" / NAMESPACE,
            "canonical_results",
        ),
        (
            RUNTIME_ROOT / "results" / "jobs" / "full" / "namespaces" / NAMESPACE,
            JOBS_ROOT,
            "job_specs",
        ),
        (RUNTIME_ROOT / "monitoring", MONITORING_ROOT, "monitoring_evidence"),
    )
    for source, destination, name in pairs:
        source_map = tree_inventory(source, relative_to=source)
        destination_map = tree_inventory(destination, relative_to=destination)
        equal = source_map == destination_map
        audit.expect(f"runtime_copy_{name}", destination, equal, True)
        comparisons.append({
            "name": name,
            "source_files": len(source_map),
            "destination_files": len(destination_map),
            "sha256_maps_equal": equal,
        })
    return {"available": True, "verified": all(row["sha256_maps_equal"] for row in comparisons), "comparisons": comparisons}


def remote_quiescence(audit: Audit, infra: dict[str, Any]) -> dict[str, Any]:
    machine = infra["machines"][0]
    ssh_config = machine["ssh"]
    remote_result_root = f"{machine['remote_workdir']}/results/namespaces/{NAMESPACE}/full/tau3_retail"
    command = "\n".join((
        "set -eu",
        f"test \"$(find {remote_result_root} -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')\" = 42",
        "! pgrep -af '[t]au2[[:space:]]+run'",
    ))
    args = [
        "ssh",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=10",
        "-o", "StrictHostKeyChecking=accept-new",
        "-i", str(ssh_config["key_path"]),
        "-p", str(ssh_config.get("port", 22)),
        f"{ssh_config['user']}@{ssh_config['host']}",
        command,
    ]
    try:
        completed = subprocess.run(args, capture_output=True, text=True, timeout=20, check=False)
    except Exception as exc:  # pragma: no cover - network state is reported
        audit.expect("remote_quiescence_exception", ssh_config["host"], type(exc).__name__, "no exception")
        return {"checked": False, "live_tau2_processes": None, "remote_result_directories": None}
    audit.expect("remote_quiescence_exit", ssh_config["host"], completed.returncode, 0)
    return {
        "checked": True,
        "ssh_exit_code": completed.returncode,
        "live_tau2_processes": 0 if completed.returncode == 0 else None,
        "remote_result_directories": 42 if completed.returncode == 0 else None,
    }


def secret_scan(audit: Audit, roots: list[Path]) -> dict[str, Any]:
    patterns = {
        "openrouter_key": re.compile(rb"sk-or-v1-[A-Za-z0-9_-]{20,}"),
        "bearer_token": re.compile(rb"Authorization:[ \t]*Bearer[ \t]+[A-Za-z0-9._-]{20,}", re.IGNORECASE),
        "openrouter_assignment": re.compile(rb"OPENROUTER_API_KEY[ \t]*=[ \t]*[^\r\n \t]{10,}"),
    }
    matched_files: dict[str, set[str]] = defaultdict(set)
    scanned = 0
    env_files = []
    seen: set[Path] = set()
    for root in roots:
        candidates = [root] if root.is_file() else sorted(path for path in root.rglob("*") if path.is_file())
        for path in candidates:
            resolved = path.resolve()
            if resolved in seen or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            seen.add(resolved)
            if path.name == ".env":
                env_files.append(relative(path))
            data = path.read_bytes()
            scanned += 1
            for name, pattern in patterns.items():
                if pattern.search(data):
                    matched_files[name].add(relative(path))
    total_matches = sum(len(paths) for paths in matched_files.values())
    audit.expect("secret_pattern_matches", "persisted run trees", total_matches, 0)
    audit.expect("persisted_env_files", "persisted run trees", env_files, [])
    return {
        "files_scanned": scanned,
        "matched_file_count": total_matches,
        "env_files": env_files,
        "patterns": {name: len(paths) for name, paths in sorted(matched_files.items())},
    }


def resource_summary() -> dict[str, Any]:
    rows = []
    for name in ("monitor_resource.jsonl", "monitor_resource_resume.jsonl"):
        path = MONITORING_ROOT / name
        if path.exists():
            rows.extend(load_jsonl(path))
    remote_rows = [row["remote"] for row in rows if isinstance(row.get("remote"), dict)]
    return {
        "samples": len(rows),
        "successful_remote_samples": len(remote_rows),
        "probe_failures": sum(1 for row in rows if not row.get("ssh", {}).get("ok")),
        "minimum_memory_available_pct": min((row["mem_available_pct"] for row in remote_rows), default=None),
        "maximum_load_1": max((row["load_1"] for row in remote_rows), default=None),
        "minimum_disk_available_gib": round(min((row["disk_available_bytes"] for row in remote_rows), default=0) / (1024 ** 3), 2),
        "maximum_oom_kill_count": max((row["oom_kill_count"] for row in remote_rows), default=None),
    }


def write_inventory() -> dict[str, Any]:
    paths: set[Path] = set()
    for root in (RESULT_ROOT.parent.parent, JOBS_ROOT, EVIDENCE_ROOT):
        for path in root.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            if path in {FINAL_PATH, INVENTORY_PATH, RELEASE_CHECKSUMS_PATH}:
                continue
            paths.add(path)
    paths.add(REPO_ROOT / "configs" / "tau3_remaining14_vultr.json")
    paths.add(REPO_ROOT / "experiments" / "appendix" / "tau3_retail_remaining14_vultr_run_manifest.yaml")
    entries = [
        {"path": relative(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
        for path in sorted(paths)
    ]
    payload = {
        "schema_version": "tau3_remaining14_persisted_inventory/v1",
        "created_at": utc_now(),
        "namespace": NAMESPACE,
        "file_count": len(entries),
        "files": entries,
    }
    INVENTORY_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"path": relative(INVENTORY_PATH), "sha256": sha256_file(INVENTORY_PATH), "file_count": len(entries)}


def main() -> int:
    audit = Audit()

    original_manifest_path = INPUTS_ROOT / "original_manifest.yaml"
    run_manifest_path = INPUTS_ROOT / "run_manifest.yaml"
    agents_path = INPUTS_ROOT / "agents.yaml"
    infra_path = INPUTS_ROOT / "infra.json"
    source_bundle_path = INPUTS_ROOT / "source_bundle.json"
    strict_drafts_path = REPO_ROOT / "experiments" / "appendix" / "tau3_retail_remaining14_drafts" / "_strict_acceptance.json"
    input_acceptance_path = MONITORING_ROOT / "input_acceptance.json"
    plan_acceptance_path = MONITORING_ROOT / "plan_acceptance.json"
    supervisor_path = MONITORING_ROOT / "supervisor_summary.json"
    remote_final_path = MONITORING_ROOT / "remote_final_acceptance.json"
    artifact_final_path = MONITORING_ROOT / "monitor_artifact_resume_final_v2.json"
    artifact_rows_path = MONITORING_ROOT / "monitor_artifact_final_v2.jsonl"
    artifact_anomalies_path = MONITORING_ROOT / "monitor_artifact_final_v2_anomalies.jsonl"
    repair_path = MONITORING_ROOT / "internal_retry_manifest_repair.json"
    pre_run_path = MONITORING_ROOT / "pre_run_deviations.json"
    anomaly_ledger_path = MONITORING_ROOT / "anomalies.jsonl"

    fixed_files = {
        "original_manifest": original_manifest_path,
        "run_manifest": run_manifest_path,
        "agents": agents_path,
        "infra": infra_path,
        "source_bundle": source_bundle_path,
        "artifact_final_v2": artifact_final_path,
        "artifact_rows_v2": artifact_rows_path,
        "empty_anomaly_ledger": artifact_anomalies_path,
        "strict_drafts": strict_drafts_path,
        "checked_in_adapter": EVIDENCE_ROOT / "provenance" / "checked_in_adapter" / "tau3_retail.py",
        "runtime_adapter": EVIDENCE_ROOT / "provenance" / "runtime_adapter" / "tau3_retail.py",
    }
    for name, path in fixed_files.items():
        audit.require(f"{name}_exists", path, path.is_file(), "file exists")
        if path.is_file():
            audit.expect(f"{name}_sha256", path, sha256_file(path), EXPECTED_HASHES[name])

    audit.expect("original_manifest_workspace_copy", original_manifest_path, sha256_file(original_manifest_path), sha256_file(REPO_ROOT / "experiments" / "appendix" / "tau3_retail_remaining14_manifest.yaml"))
    audit.expect("run_manifest_workspace_copy", run_manifest_path, sha256_file(run_manifest_path), sha256_file(REPO_ROOT / "experiments" / "appendix" / "tau3_retail_remaining14_vultr_run_manifest.yaml"))
    audit.expect("agents_workspace_copy", agents_path, sha256_file(agents_path), sha256_file(REPO_ROOT / "configs" / "agents.yaml"))
    audit.expect("infra_workspace_copy", infra_path, sha256_file(infra_path), sha256_file(REPO_ROOT / "configs" / "tau3_remaining14_vultr.json"))
    audit.expect("source_bundle_workspace_copy", source_bundle_path, sha256_file(source_bundle_path), sha256_file(REPO_ROOT / "experiments" / "evidence_contracts" / "source_bundles" / "tau3_retail_remaining14_source_bundle.json"))

    original_manifest = yaml_object(original_manifest_path)
    run_manifest = yaml_object(run_manifest_path)
    infra = load_json(infra_path)
    input_acceptance = load_json(input_acceptance_path)
    plan_acceptance = load_json(plan_acceptance_path)
    supervisor = load_json(supervisor_path)
    remote_final = load_json(remote_final_path)
    artifact_final = load_json(artifact_final_path)
    repair_report = load_json(repair_path)
    pre_run = load_json(pre_run_path)
    operational_anomalies = load_jsonl(anomaly_ledger_path)

    run_domain = run_manifest["domains"][0]
    run_cases = [str(row["case_unit_id"]) for row in run_domain["case_units"]]
    run_agents = [str(row["agent_id"]) for row in run_manifest["agents"]]
    audit.expect("original_manifest_status", original_manifest_path, original_manifest.get("status"), "draft")
    audit.expect("run_manifest_status", run_manifest_path, run_manifest.get("status"), "draft")
    audit.expect("run_manifest_namespace", run_manifest_path, run_manifest.get("result_namespace"), NAMESPACE)
    audit.expect("run_manifest_case_order", run_manifest_path, run_cases, list(CASES))
    audit.expect("run_manifest_agent_order", run_manifest_path, run_agents, list(AGENT_SUFFIX))
    audit.expect("run_manifest_case_count", run_manifest_path, run_domain.get("case_unit_count"), 14)
    audit.expect("run_manifest_slot_count", run_manifest_path, run_domain.get("record_slot_count"), 42)
    audit.expect("run_manifest_source_hash", run_manifest_path, run_manifest.get("source_bundle_hash"), EXPECTED_HASHES["source_bundle"])
    audit.expect("run_manifest_agents_hash", run_manifest_path, run_manifest.get("agents_config_hash"), EXPECTED_HASHES["agents"])
    audit.expect("run_manifest_infra_hash", run_manifest_path, run_manifest.get("infra_config_hash"), EXPECTED_HASHES["infra"])
    audit.expect("run_manifest_contract_locks", run_manifest_path, run_manifest.get("contract_locks"), [])
    audit.expect("run_manifest_contract_gate", run_manifest_path, run_domain.get("contract_lock_status"), "locked_required_before_scoring")
    audit.expect("case_contract_gates", run_manifest_path, {row.get("contract_lock_status") for row in run_domain["case_units"]}, {"locked_required_before_scoring"})

    audit.expect("input_acceptance_status", input_acceptance_path, input_acceptance.get("status"), "PASS")
    audit.expect("input_packet_count", input_acceptance_path, input_acceptance.get("case_packets_verified"), 14)
    audit.expect("input_raw_manifest_count", input_acceptance_path, input_acceptance.get("raw_case_manifests_verified"), 14)
    audit.expect("input_draft_count", input_acceptance_path, input_acceptance.get("draft_checklists_verified"), 14)
    audit.expect("input_draft_guardrail_count", input_acceptance_path, input_acceptance.get("draft_schema_guardrail_valid"), 14)
    audit.expect("input_source_hash", input_acceptance_path, input_acceptance.get("source_bundle_sha256"), EXPECTED_HASHES["source_bundle"])
    audit.expect("input_strict_draft_hash", input_acceptance_path, input_acceptance.get("strict_draft_acceptance_sha256"), EXPECTED_HASHES["strict_drafts"])

    audit.expect("plan_status", plan_acceptance_path, plan_acceptance.get("status"), "PASS")
    audit.expect("plan_jobs", plan_acceptance_path, plan_acceptance.get("planned_jobs"), 42)
    audit.expect("plan_slots", plan_acceptance_path, plan_acceptance.get("unique_record_slots"), 42)
    audit.expect("plan_cases", plan_acceptance_path, plan_acceptance.get("case_order"), list(CASES))
    audit.expect("plan_agents", plan_acceptance_path, plan_acceptance.get("agents"), list(AGENT_SUFFIX))
    audit.expect("plan_workers", plan_acceptance_path, plan_acceptance.get("max_workers"), 2)
    audit.expect("plan_seed_range", plan_acceptance_path, plan_acceptance.get("seed_range"), [107, 120])
    audit.expect("plan_contract_mode", plan_acceptance_path, plan_acceptance.get("contract_mode"), "generated_fallback_prelock")
    audit.expect("plan_formal_eligibility", plan_acceptance_path, plan_acceptance.get("formal_scoring_eligible"), False)

    audit.expect("supervisor_status", supervisor_path, supervisor.get("status"), "complete")
    audit.expect("supervisor_planned", supervisor_path, supervisor.get("planned_slots"), 42)
    audit.expect("supervisor_attempted", supervisor_path, supervisor.get("attempted_unique_slots"), 42)
    audit.expect("supervisor_completed", supervisor_path, supervisor.get("completed_unique_slots"), 42)
    audit.expect("supervisor_active", supervisor_path, supervisor.get("currently_active"), 0)
    audit.expect("supervisor_unresolved", supervisor_path, supervisor.get("unresolved_job_ids"), [])
    audit.expect("supervisor_max_active", supervisor_path, supervisor.get("max_active_observed"), 2)

    audit.expect("remote_verdict", remote_final_path, remote_final.get("verdict"), "accepted_with_documented_nonblocking_anomalies")
    remote_results = remote_final["remote_result_acceptance"]
    audit.expect("remote_slots", remote_final_path, remote_results.get("slot_count"), 42)
    audit.expect("remote_numeric_rewards", remote_final_path, remote_results.get("numeric_reward_records"), 42)
    audit.expect("remote_used_status", remote_final_path, remote_results.get("used_sim_status_records"), 42)
    audit.expect("remote_failed_internal_status", remote_final_path, remote_results.get("failed_internal_sim_status_records"), 2)
    audit.expect("remote_reward_sum", remote_final_path, remote_results.get("reward_sum"), 35.0)
    fatal_signal_fields = (
        "http_401_402_403_or_billing_files", "http_429_or_rate_limit_files", "http_5xx_files",
        "timeout_files", "traceback_files", "no_response_files",
    )
    for field in fatal_signal_fields:
        audit.expect(f"remote_{field}", remote_final_path, remote_final["full_remote_signal_scan"].get(field), 0)

    audit.expect("artifact_final_status", artifact_final_path, artifact_final.get("status"), "PASS")
    audit.expect("artifact_final_passed", artifact_final_path, artifact_final.get("passed"), 42)
    audit.expect("artifact_final_failed", artifact_final_path, artifact_final.get("failed"), 0)
    audit.expect("artifact_final_anomalies", artifact_final_path, artifact_final.get("anomaly_count"), 0)
    audit.expect("artifact_final_errors", artifact_final_path, artifact_final.get("global_errors"), [])
    audit.expect("artifact_final_jobs", artifact_final_path, artifact_final.get("job_json_count"), 42)
    audit.expect("artifact_final_result_dirs", artifact_final_path, artifact_final.get("result_directory_count"), 42)
    audit.expect("artifact_final_slots", artifact_final_path, artifact_final.get("unique_record_slots"), 42)
    audit.expect("artifact_final_rewards", artifact_final_path, artifact_final.get("native_reward_distribution"), {"0.0": 7, "1.0": 35})
    audit.expect("artifact_rows_hash", artifact_rows_path, sha256_file(artifact_rows_path), artifact_final.get("rows_sha256"))
    audit.expect("artifact_anomaly_hash", artifact_anomalies_path, sha256_file(artifact_anomalies_path), artifact_final.get("anomalies_sha256"))
    audit.expect("artifact_repaired_jobs", artifact_final_path, set(artifact_final.get("repaired_jobs", [])), REPAIRED_JOBS)
    for agent in AGENT_SUFFIX:
        audit.expect(f"artifact_{agent}_pass", artifact_final_path, artifact_final["by_agent"].get(agent), {"failed": 0, "passed": 14})

    audit.expect("repair_report_status", repair_path, repair_report.get("status"), "PASS")
    audit.expect("repair_native_files_modified", repair_path, repair_report.get("native_files_modified"), False)
    audit.expect("repair_benchmark_runs_modified", repair_path, repair_report.get("benchmark_runs_modified"), False)
    audit.expect("repair_job_set", repair_path, {row.get("job_id") for row in repair_report.get("rows", [])}, REPAIRED_JOBS)
    audit.expect("pre_run_status", pre_run_path, pre_run.get("status"), "accepted_for_raw_collection_only")
    audit.expect("pre_run_formal_eligibility", pre_run_path, pre_run.get("formal_scoring_eligible"), False)
    audit.expect("operational_anomaly_rows", anomaly_ledger_path, len(operational_anomalies), 3)
    audit.expect(
        "operational_anomaly_categories",
        anomaly_ledger_path,
        {row.get("category") for row in operational_anomalies},
        {"controller_transport", "controller_persistence", "api_runner"},
    )
    orphan_native_jobs = sorted(
        path.name for path in (MONITORING_ROOT / "orphan_native_attempts").iterdir() if path.is_dir()
    )
    orphan_controller_jobs = sorted(
        path.name for path in (MONITORING_ROOT / "orphan_controller_attempts").iterdir() if path.is_dir()
    )
    audit.expect("orphan_native_jobs", MONITORING_ROOT / "orphan_native_attempts", orphan_native_jobs, ["full-tau3_retail-104-agent_c", "full-tau3_retail-85-agent_c"])
    audit.expect("orphan_controller_jobs", MONITORING_ROOT / "orphan_controller_attempts", orphan_controller_jobs, ["full-tau3_retail-104-agent_c", "full-tau3_retail-85-agent_c"])

    expected_ids = expected_job_ids()
    job_files = sorted(JOBS_ROOT.glob("*.json"))
    result_dirs = {path.name for path in RESULT_ROOT.iterdir() if path.is_dir()} if RESULT_ROOT.is_dir() else set()
    jobs = {load_json(path)["job_id"]: load_json(path) for path in job_files}
    audit.expect("job_file_count", JOBS_ROOT, len(job_files), 42)
    audit.expect("job_id_set", JOBS_ROOT, set(jobs), expected_ids)
    audit.expect("result_directory_count", RESULT_ROOT, len(result_dirs), 42)
    audit.expect("result_directory_set", RESULT_ROOT, result_dirs, expected_ids)

    slots: set[str] = set()
    reward_by_agent: dict[str, Counter[float]] = defaultdict(Counter)
    reward_distribution: Counter[float] = Counter()
    llm_call_count = 0
    artifact_pointer_count = 0
    artifact_file_count = 0
    artifact_directory_count = 0
    schema_counts: Counter[str] = Counter()

    for job_id in sorted(jobs):
        job = jobs[job_id]
        job_file = JOBS_ROOT / f"{job_id}.json"
        validate_schema(audit, "job", job, job_file)
        schema_counts["job"] += 1
        case_id = str(job["case_unit_id"])
        agent_id = str(job["agent_id"])
        expected_seed = 107 + CASES.index(case_id)
        expected_id = f"full-tau3_retail-{case_id}-agent_{AGENT_SUFFIX[agent_id]}"
        audit.expect("job_identity", job_file, job_id, expected_id)
        audit.expect("job_namespace", job_file, job.get("result_namespace"), NAMESPACE)
        audit.expect("job_seed", job_file, job.get("seed"), expected_seed)
        audit.expect("job_manifest_hash", job_file, job.get("manifest_hash"), EXPECTED_HASHES["run_manifest"])
        audit.expect("job_agent_config_hash", job_file, job.get("agent_config_hash"), EXPECTED_HASHES["agents"])
        audit.expect("job_prelock_required_artifacts", job_file, job.get("artifact_contract", {}).get("required_artifacts"), [])
        slot = str(job["record_slot_id"])
        audit.require("job_slot_unique", job_file, slot not in slots, "record_slot_id is unique")
        slots.add(slot)

        adapter = RESULT_ROOT / job_id / "adapter"
        raw_path = adapter / "raw_run.json"
        manifest_path = adapter / "artifact_manifest.json"
        environment_path = adapter / "environment.json"
        results_path = adapter / "native_run" / "results.json"
        calls_path = adapter / "llm_calls" / "calls.jsonl"
        for path in (raw_path, manifest_path, environment_path, results_path, calls_path):
            audit.require("required_job_file_exists", path, path.is_file(), "required terminal file exists")
        if not all(path.is_file() for path in (raw_path, manifest_path, environment_path, results_path, calls_path)):
            continue

        raw = load_json(raw_path)
        manifest = load_json(manifest_path)
        environment = load_json(environment_path)
        results = load_json(results_path)
        validate_schema(audit, "raw_run", raw, raw_path)
        validate_schema(audit, "artifact_manifest", manifest, manifest_path)
        schema_counts["raw_run"] += 1
        schema_counts["artifact_manifest"] += 1
        identity_fields = (
            "domain", "case_unit_id", "task_id", "record_slot_id", "run_id", "attempt_id", "seed",
            "agent_id", "phase", "experiment_type", "priority", "evidence_contract_id",
            "evidence_contract_version", "evidence_contract_hash",
        )
        for field in identity_fields:
            audit.expect(f"raw_job_{field}", raw_path, raw.get(field), job.get(field))
            audit.expect(f"manifest_job_{field}", manifest_path, manifest.get(field), job.get(field))
        audit.expect("raw_status", raw_path, str(raw.get("status", "")).lower(), "completed")
        audit.expect("raw_diagnostic_status", raw_path, str(raw.get("diagnostic_status", "")).lower(), "completed")
        audit.expect("raw_manifest_hash", raw_path, raw.get("manifest_hash"), EXPECTED_HASHES["run_manifest"])
        audit.expect("raw_artifact_manifest_hash", raw_path, raw.get("artifact_manifest_sha256"), sha256_file(manifest_path))
        audit.expect("environment_job", environment_path, environment.get("job_id"), job_id)
        audit.expect("environment_machine", environment_path, environment.get("machine_id"), "tau3-vultr-45-76-20-117")
        environment_hash = sha256_file(environment_path)
        audit.expect("manifest_source_hash", manifest_path, manifest.get("source_bundle_hash"), EXPECTED_HASHES["source_bundle"])
        audit.expect("manifest_split_hash", manifest_path, manifest.get("official_splits_hash"), EXPECTED_HASHES["official_split"])
        audit.expect("manifest_environment_hash", manifest_path, manifest.get("environment_hash"), environment_hash)

        pointer_expectations = {
            "artifact_manifest_path": manifest_path,
            "raw_source_path": raw_path,
            "llm_calls_log_path": calls_path,
        }
        for field, expected_path in pointer_expectations.items():
            observed_path = (REPO_ROOT / str(raw.get(field, ""))).resolve()
            audit.expect(f"raw_{field}_pointer", raw_path, observed_path, expected_path.resolve())

        artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), list) else []
        artifact_ids = [str(entry.get("artifact_id")) for entry in artifacts if isinstance(entry, dict)]
        artifact_paths = [str(entry.get("path")) for entry in artifacts if isinstance(entry, dict)]
        audit.expect("artifact_id_uniqueness", manifest_path, len(set(artifact_ids)), len(artifact_ids))
        audit.expect("artifact_path_uniqueness", manifest_path, len(set(artifact_paths)), len(artifact_paths))
        required_ids = {
            "native_evaluator_output:results", "tool_log:task", "post_state:sim_status",
            "file:environment", "stdout:stdout", "stderr:stderr", "file:llm_calls",
        }
        audit.require("required_artifact_ids", manifest_path, required_ids <= set(artifact_ids), "required result, decisive, environment, stream, and call artifacts present")
        resolved_artifact_paths: set[Path] = set()
        for entry in artifacts:
            if not isinstance(entry, dict):
                audit.require("artifact_entry_object", manifest_path, False, "artifact entry is an object")
                continue
            path = (REPO_ROOT / str(entry.get("path", ""))).resolve()
            resolved_artifact_paths.add(path)
            artifact_pointer_count += 1
            audit.require("artifact_inside_job", manifest_path, path.is_relative_to(adapter.resolve()), "artifact path is inside its job directory")
            audit.require("artifact_exists", path, path.exists(), "artifact path exists")
            if not path.exists():
                continue
            if path.is_file():
                artifact_file_count += 1
            elif path.is_dir():
                artifact_directory_count += 1
            audit.expect("artifact_hash", path, sha256_path(path), entry.get("sha256"))
            audit.expect("artifact_size", path, path_size(path), entry.get("size_bytes"))
            audit.expect("artifact_source_hash", path, entry.get("source_bundle_hash"), EXPECTED_HASHES["source_bundle"])
            audit.expect("artifact_split_hash", path, entry.get("official_splits_hash"), EXPECTED_HASHES["official_split"])
            audit.expect("artifact_environment_hash", path, entry.get("environment_hash"), environment_hash)

        stdout_path = adapter / "logs" / "stdout.log"
        stderr_path = adapter / "logs" / "stderr.log"
        audit.require("stdout_nonempty", stdout_path, stdout_path.is_file() and stdout_path.stat().st_size > 0, "stdout exists and is non-empty")
        audit.require("stderr_nonempty", stderr_path, stderr_path.is_file() and stderr_path.stat().st_size > 0, "stderr exists and is non-empty")

        simulations = results.get("simulations") if isinstance(results.get("simulations"), list) else []
        audit.expect("native_simulation_count", results_path, len(simulations), 1)
        if len(simulations) != 1 or not isinstance(simulations[0], dict):
            continue
        simulation = simulations[0]
        audit.expect("native_task_id", results_path, str(simulation.get("task_id")), case_id)
        audit.expect("native_termination", results_path, simulation.get("termination_reason"), "user_stop")
        reward = simulation.get("reward_info", {}).get("reward")
        numeric_reward = isinstance(reward, (int, float)) and not isinstance(reward, bool) and math.isfinite(float(reward))
        audit.require("native_reward_numeric", results_path, numeric_reward, "finite numeric native reward")
        if not numeric_reward:
            continue
        reward_value = float(reward)
        audit.require("native_reward_binary", results_path, reward_value in {0.0, 1.0}, "native reward is 0.0 or 1.0")
        reward_distribution[reward_value] += 1
        reward_by_agent[agent_id][reward_value] += 1
        audit.expect("raw_native_score", raw_path, float(raw.get("native_score")), reward_value)
        audit.expect("raw_episode_id", raw_path, raw.get("episode_ids"), [simulation.get("id")])

        status_paths = sorted((adapter / "native_run" / "artifacts").rglob("sim_status.json"))
        status_values = {path: load_json(path).get("status") for path in status_paths}
        used_paths = [path for path, status in status_values.items() if status == "used"]
        failed_paths = [path for path, status in status_values.items() if status == "failed"]
        audit.expect("used_simulation_count", adapter, len(used_paths), 1)
        audit.expect("failed_simulation_count", adapter, len(failed_paths), 1 if job_id in REPAIRED_JOBS else 0)
        if len(used_paths) == 1:
            used_dir = used_paths[0].parent
            audit.expect("used_simulation_id", results_path, used_dir.name.removeprefix("sim_"), str(simulation.get("id")))
            selected_status = [path for path in resolved_artifact_paths if path.name == "sim_status.json"]
            selected_task = [path for path in resolved_artifact_paths if path.name == "task.log"]
            selected_debug = [path for path in resolved_artifact_paths if "llm_debug" in path.parts]
            audit.expect("selected_status_count", manifest_path, len(selected_status), 1)
            audit.expect("selected_task_count", manifest_path, len(selected_task), 1)
            audit.expect("selected_status_is_used", manifest_path, selected_status, [used_paths[0].resolve()])
            audit.expect("selected_task_is_used", manifest_path, selected_task, [(used_dir / "task.log").resolve()])
            audit.require("selected_debug_is_used", manifest_path, all(path.is_relative_to(used_dir.resolve()) for path in selected_debug), "decisive debug traces are from the used simulation")

        call_files = sorted((adapter / "llm_calls").glob("*.json"))
        call_rows = load_jsonl(calls_path)
        call_objects = [load_json(path) for path in call_files]
        by_id_files = {str(row.get("call_id")): row for row in call_objects}
        by_id_rows = {str(row.get("call_id")): row for row in call_rows}
        audit.expect("llm_call_file_row_count", calls_path, len(call_files), len(call_rows))
        audit.expect("llm_call_id_set", calls_path, set(by_id_files), set(by_id_rows))
        audit.expect("llm_call_payloads", calls_path, by_id_files, by_id_rows)
        debug_files = sorted((adapter / "native_run" / "artifacts").rglob("llm_debug/*.json"))
        debug_call_ids = {path.stem.rsplit("_", 1)[-1] for path in debug_files}
        audit.expect("llm_debug_call_ids", adapter, debug_call_ids, set(by_id_files))
        for path, call in zip(call_files, call_objects, strict=True):
            validate_schema(audit, "llm_call", call, path)
            schema_counts["llm_call"] += 1
            audit.expect("llm_call_agent", path, call.get("agent_id_or_role"), agent_id)
            audit.expect("llm_call_case", path, str(call.get("case_unit_id")), case_id)
            audit.expect("llm_call_slot", path, call.get("record_slot_id"), slot)
            call_name = str(call.get("response_metadata", {}).get("call_name") or "")
            if call_name in {"agent_response", "user_simulator_response"}:
                expected_call_model = EXPECTED_MODELS[agent_id]
            elif call_name == "nl_assertions_eval":
                expected_call_model = "gpt-4.1-2025-04-14"
            else:
                expected_call_model = None
                audit.require("llm_call_name_known", path, False, "known agent, user-simulator, or native-evaluator call name")
            if expected_call_model is not None:
                audit.expect("llm_call_model", path, call.get("model"), expected_call_model)
            audit.expect("llm_call_provider", path, call.get("provider"), "openrouter")
            audit.expect("llm_call_transport_status", path, call.get("response_metadata", {}).get("status"), "success")
            audit.expect("llm_call_redaction", path, call.get("redaction_status"), "no_secret_logged")
            audit.expect("llm_call_source_hash", path, call.get("source_bundle_hash"), EXPECTED_HASHES["source_bundle"])
        llm_call_count += len(call_files)

        if job_id in REPAIRED_JOBS:
            audit_repaired_job(audit, job_id, adapter, manifest, raw, repair_report)

    audit.expect("unique_record_slots", JOBS_ROOT, len(slots), 42)
    audit.expect("native_reward_distribution", RESULT_ROOT, reward_distribution, Counter({1.0: 35, 0.0: 7}))
    expected_agent_rewards = {
        "Agent A": Counter({1.0: 10, 0.0: 4}),
        "Agent B": Counter({1.0: 13, 0.0: 1}),
        "Agent C": Counter({1.0: 12, 0.0: 2}),
    }
    for agent, expected in expected_agent_rewards.items():
        audit.expect(f"native_reward_{AGENT_SUFFIX[agent]}", RESULT_ROOT, reward_by_agent[agent], expected)

    runtime_copy = verify_runtime_copy(audit)
    quiescence = remote_quiescence(audit, infra)
    secrets = secret_scan(audit, [
        REPO_ROOT / "results" / "namespaces" / NAMESPACE,
        EVIDENCE_ROOT,
        REPO_ROOT / "configs" / "tau3_remaining14_vultr.json",
        REPO_ROOT / "experiments" / "appendix" / "tau3_retail_remaining14_vultr_run_manifest.yaml",
    ])
    resources = resource_summary()
    audit.expect("resource_oom", MONITORING_ROOT, resources.get("maximum_oom_kill_count"), 0)

    inventory = write_inventory()
    status = "PASS" if not audit.errors else "FAIL"
    report = {
        "schema_version": "tau3_remaining14_persisted_final_acceptance/v1",
        "created_at": utc_now(),
        "namespace": NAMESPACE,
        "status": status,
        "acceptance_scope": "raw benchmark collection and artifact integrity",
        "collection_disposition": "accepted_for_raw_collection_only" if status == "PASS" else "rejected",
        "formal_scoring_eligible": False,
        "paper_ready": False,
        "methodology_gate": {
            "status": "BLOCKED_PENDING_REVIEW_AND_LOCK",
            "reason": "14 checklists are schema/guardrail-valid drafts, not formally reviewed and locked contracts",
            "required_before_formal_scoring": "complete checklist review/lock and reconcile contract provenance before scorer execution",
        },
        "denominator": {
            "cases": 14,
            "agents": 3,
            "planned_slots": 42,
            "completed_slots": 42,
            "unique_record_slots": len(slots),
            "per_agent": {agent: 14 for agent in AGENT_SUFFIX},
        },
        "execution": {
            "vps": "45.76.20.117",
            "tau2_commit": "2be691669909439cf88dedc13decf94b7664d262",
            "configured_concurrency": 2,
            "observed_max_concurrency": supervisor.get("max_active_observed"),
            "unresolved_jobs": supervisor.get("unresolved_job_ids"),
            "remote_quiescence": quiescence,
        },
        "native_rewards": {
            "total": {"1.0": reward_distribution[1.0], "0.0": reward_distribution[0.0], "sum": float(sum(value * count for value, count in reward_distribution.items()))},
            "by_agent": {
                agent: {"1.0": reward_by_agent[agent][1.0], "0.0": reward_by_agent[agent][0.0]}
                for agent in AGENT_SUFFIX
            },
            "interpretation": "native Tau2 benchmark reward only; not checklist/scorer output",
        },
        "strict_artifact_audit": {
            "status": artifact_final.get("status"),
            "passed": artifact_final.get("passed"),
            "failed": artifact_final.get("failed"),
            "independent_report_sha256": sha256_file(artifact_final_path),
            "artifact_pointer_count_reverified": artifact_pointer_count,
            "artifact_file_count_reverified": artifact_file_count,
            "artifact_directory_count_reverified": artifact_directory_count,
            "llm_call_count_reverified": llm_call_count,
            "schema_validation_counts": dict(schema_counts),
            "second_crosscheck": "C104 and C55 independently cross-checked with zero failures",
        },
        "internal_retries": {
            "count": 2,
            "jobs": sorted(REPAIRED_JOBS),
            "native_files_modified": repair_report.get("native_files_modified"),
            "benchmark_runs_modified": repair_report.get("benchmark_runs_modified"),
            "disposition": "failed simulations retained as hash-indexed diagnostics; exactly one used simulation remains decisive per job",
        },
        "documented_operational_anomalies": {
            "controller_ledger": {
                "path": relative(anomaly_ledger_path),
                "sha256": sha256_file(anomaly_ledger_path),
                "rows": len(operational_anomalies),
                "categories": dict(Counter(str(row.get("category")) for row in operational_anomalies)),
            },
            "orphan_native_attempt_jobs": orphan_native_jobs,
            "orphan_controller_attempt_jobs": orphan_controller_jobs,
            "canonical_internal_retry_jobs": sorted(REPAIRED_JOBS),
            "cost_telemetry_warning_files": remote_final.get("full_remote_signal_scan", {}).get("model_cost_unmapped_files"),
            "resource_monitor_probe_failures": resources.get("probe_failures"),
            "impact": "recorded and resolved without dropping a canonical slot; cost telemetry remains incomplete",
        },
        "remote_signal_scan": remote_final.get("full_remote_signal_scan"),
        "resource_monitoring": resources,
        "secret_scan": secrets,
        "runtime_copy_verification": runtime_copy,
        "persisted_paths": {
            "results": relative(REPO_ROOT / "results" / "namespaces" / NAMESPACE),
            "jobs": relative(JOBS_ROOT),
            "evidence": relative(EVIDENCE_ROOT),
            "run_manifest": relative(REPO_ROOT / "experiments" / "appendix" / "tau3_retail_remaining14_vultr_run_manifest.yaml"),
            "infra": relative(REPO_ROOT / "configs" / "tau3_remaining14_vultr.json"),
        },
        "inventory": inventory,
        "checks_performed": audit.check_count,
        "error_count": len(audit.errors),
        "errors": audit.errors,
    }
    FINAL_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RELEASE_CHECKSUMS_PATH.write_text(
        f"{sha256_file(FINAL_PATH)}  {relative(FINAL_PATH)}\n"
        f"{sha256_file(INVENTORY_PATH)}  {relative(INVENTORY_PATH)}\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": status,
        "checks_performed": audit.check_count,
        "errors": len(audit.errors),
        "final_acceptance": relative(FINAL_PATH),
        "inventory": inventory,
        "release_checksums": relative(RELEASE_CHECKSUMS_PATH),
    }, ensure_ascii=False, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
