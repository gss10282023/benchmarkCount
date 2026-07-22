"""Read-only case monitoring and resumable control for WebArena-Verified.

The monitor deliberately treats benchmark result trees as immutable inputs.  It
may write only two controller-owned files at the top of a result namespace:
``case_issue_ledger.jsonl`` and ``progress_receipt.json`` (plus SHA sidecars).
It never acquires a WebArena site lock, changes a score, requests a rerun, or
stops a worker.  The paid wrapper uses the monitor's canonical-slot decision to
resume three sequential agent lanes and trips only between slots.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
from functools import wraps
import hashlib
from importlib import import_module
import json
import os
from pathlib import Path
import re
import shlex
import tempfile
import threading
from typing import Any
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

from evidence_system.adapters.runtime import (
    job_result_relative_dir,
    run_remote_blind_command,
)
from evidence_system.adapters.webarena_remote_retention import RETENTION_MODE
from evidence_system.adapters.webarena_remote_retention import PERSISTENT_RESULTS_ROOT
from evidence_system.adapters.webarena_har_sanitization import (
    HarSanitizationError,
    load_and_validate_network_sanitization_receipt,
)
from evidence_system.core.hashing import sha256_file, sha256_object, sha256_path
from evidence_system.core.paths import repo_root, resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml
from evidence_system.orchestrator import jobs as jobs_module
from evidence_system.orchestrator.jobs import InfraBenchmarkTarget
from evidence_system.orchestrator.webarena_verified_full import (
    DEFAULT_REMOTE_WORKDIR,
    DEFAULT_AGENTS_CONFIG,
    DEFAULT_JOBS_ROOT,
    DEFAULT_MANIFEST,
    DEFAULT_SITE_LOCK,
    DEFAULT_SOURCE_BUNDLE,
    EXPECTED_AGENT_IDS,
    EXPECTED_RECORD_SLOT_COUNT,
    EXPECTED_ROUTES,
    EXPECTED_SOURCE_SHA256,
    FullSchedulePlan,
    RESULT_NAMESPACE,
    SCHEDULE_INDEX_SCHEMA_VERSION,
)
from evidence_system.orchestrator.webarena_verified_full_execution import (
    execute_full_schedule,
    execution_input_hash,
)
from evidence_system.orchestrator.webarena_verified_pilot_execution import (
    PILOT_RESULT_NAMESPACE,
    build_pilot_schedule,
)
from evidence_system.orchestrator.webarena_verified_pilot import (
    DEFAULT_PILOT_MANIFEST,
)
from evidence_system.webarena_sites import (
    RESET_RECEIPT_SCHEMA,
    load_site_lock,
    pinned_image_reference,
)


PAID_FULL_CONFIRMATION = "RUN-2436-PAID-FULL"
DEFAULT_JOBS_INDEX = DEFAULT_JOBS_ROOT / "index.json"
DEFAULT_CONTROL_ACCEPTANCE = Path(
    "experiments/step20/webarena_verified/full_run_control_acceptance.json"
)
DEFAULT_PILOT_ACCEPTANCE = Path(
    "experiments/step20/webarena_verified/pilot_acceptance.json"
)
DEFAULT_STORAGE_ACCEPTANCE = Path(
    "experiments/step20/webarena_verified/storage_readiness_acceptance.json"
)
DEFAULT_CREDENTIAL_ACCEPTANCE = Path(
    "experiments/step20/webarena_verified/openrouter_credential_acceptance.json"
)
DEFAULT_PILOT_BUDGET_CAPACITY_ACCEPTANCE = Path(
    "experiments/step20/webarena_verified/"
    "pilot_cost_runtime_storage_acceptance.json"
)
DEFAULT_REMOTE_RETENTION_CANARY_ACCEPTANCE = Path(
    "experiments/step20/webarena_verified/remote_retention_canary_acceptance.json"
)
DEFAULT_CIRCUIT_RECOVERY_RECEIPT = Path(
    "results/namespaces/webarena_verified_v1_2_3_full_812/"
    "circuit_recovery_receipt.json"
)
CIRCUIT_RECOVERY_SCHEMA = "webarena_verified_circuit_recovery_receipt/v1"
CIRCUIT_RECOVERY_ISSUE_CONFIRMATION = "ISSUE-WV-FULL-CIRCUIT-RECOVERY"
CIRCUIT_RECOVERY_CONFIRMATION_PREFIX = "CLEAR-WV-FULL-"
RETRY_EXHAUSTION_SCHEMA = "webarena_verified_retry_exhaustion_receipt/v1"
RECOVERY_CRITICAL_CODE_PATHS = (
    "src/evidence_system/adapters/webarena_har_sanitization.py",
    "src/evidence_system/adapters/webarena_official_worker.py",
    "src/evidence_system/adapters/webarena_remote_retention.py",
    "src/evidence_system/adapters/webarena_verified.py",
    "src/evidence_system/cli/webarena_full_control.py",
    "src/evidence_system/orchestrator/webarena_verified_full_execution.py",
    "src/evidence_system/orchestrator/webarena_verified_pilot_execution.py",
    "src/evidence_system/orchestrator/webarena_verified_run_control.py",
    "scripts/build_webarena_verified_circuit_recovery.py",
    "scripts/build_webarena_verified_step20_acceptance.py",
    "scripts/run_webarena_verified_task0_canary.py",
)
REQUIRED_RECOVERY_TEST_CASES = frozenset(
    {
        "test_trace_member_larger_than_legacy_50mb_cap_is_sanitized",
        "test_opaque_secret_crossing_stream_chunk_boundary_is_redacted",
        "test_v5_receipt_remains_valid_after_v6_deployment",
        "test_empty_json_response_resource_is_preserved_as_opaque",
        "test_empty_core_structured_trace_member_still_fails_closed",
        "test_json_response_resource_uses_opaque_exact_redaction",
        "test_full_execution_runs_recovery_prelude_before_any_lane_resume",
        "test_recovered_lane_retries_exact_failure_tail_as_prelude",
    }
)
TASK_PACKET_ROOT = Path("experiments/case_packets/webarena_verified")

ISSUE_SCHEMA = "webarena_verified_case_issue/v1"
PROGRESS_SCHEMA = "webarena_verified_case_monitor_progress/v1"
CONTROL_SCHEMA = "webarena_verified_full_run_control_acceptance/v1"
ALLOWED_CLASSIFICATIONS = {
    "potential_case_issue",
    "agent",
    "infra",
    "systemic",
}
ALLOWED_CIRCUIT_CLASSES = {
    "none",
    "credential",
    "storage",
    "reset",
    "infra",
    "systemic",
}
IMMEDIATE_CIRCUIT_CLASSES = {"credential", "storage", "systemic"}
FULL_SWEEP_RECORD_ONLY_INFRA_ISSUES = False
CONSECUTIVE_CONTROLLER_FAILURE_THRESHOLD = 3
# Isolated runtime/post-run audit failures remain record-only.  Four
# consecutive failures in one ordered lane open the shared circuit between
# slots; any canonical slot resets that lane's streak.  A single transient
# reset/SSH failure therefore cannot stop the run.  Credential, storage, and
# systemic failures remain immediate fail-closed circuit classes.
CONSECUTIVE_LANE_FAILURE_THRESHOLD = 4
EXPECTED_PILOT_JOBS_SHA256 = (
    "010c67c5fbf9762c0f937385b0bbadb2c28ee0eb5d7cebb6e629b667bd80a29a"
)
DEFAULT_PILOT_MONITOR_SCHEDULE = Path(
    "experiments/step20/webarena_verified/pilot_monitor_schedule.json"
)
DEFAULT_CANONICAL_PILOT_JOBS_INDEX = Path(
    "experiments/step20/webarena_verified/jobs/pilot/index.json"
)
DEFAULT_CANONICAL_PILOT_ACCEPTANCE = Path(
    "experiments/step20/webarena_verified/pilot_schedule_acceptance.json"
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_PLACEHOLDER_RE = re.compile(
    r"\{\{[^{}]+\}\}|\$\{[^{}]+\}|<PLACEHOLDER>|__PLACEHOLDER__",
    re.IGNORECASE,
)


class WebArenaRunControlError(RuntimeError):
    """Raised before a paid call when run-control evidence is invalid."""


def _single_full_controller(function: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
    """Prevent overlapping local controllers from resetting the same VPS lane."""

    @wraps(function)
    def guarded(*args: Any, **kwargs: Any) -> dict[str, Any]:
        repository_id = hashlib.sha256(str(repo_root()).encode("utf-8")).hexdigest()[:16]
        lock_path = Path(tempfile.gettempdir()) / (
            f"webarena-verified-full-controller-{repository_id}.lock"
        )
        descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise WebArenaRunControlError(
                    "another WebArena full controller is already active"
                ) from exc
            os.ftruncate(descriptor, 0)
            os.write(
                descriptor,
                (
                    json.dumps(
                        {
                            "pid": os.getpid(),
                            "started_at": datetime.now(timezone.utc)
                            .isoformat()
                            .replace("+00:00", "Z"),
                        }
                    )
                    + "\n"
                ).encode("ascii"),
            )
            os.fsync(descriptor)
            return function(*args, **kwargs)
        finally:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)

    return guarded


@dataclass(frozen=True)
class SlotAudit:
    record_slot_id: str
    state: str
    reusable: bool
    issues: tuple[dict[str, Any], ...]
    artifact_root: str
    semantic_review: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class MonitorSnapshot:
    jobs: tuple[dict[str, Any], ...]
    audits: tuple[SlotAudit, ...]
    issues: tuple[dict[str, Any], ...]
    progress: dict[str, Any]

    @property
    def reusable_slot_ids(self) -> frozenset[str]:
        return frozenset(item.record_slot_id for item in self.audits if item.reusable)


def load_full_jobs(
    index_path: str | Path = DEFAULT_JOBS_INDEX,
) -> tuple[tuple[dict[str, Any], ...], dict[str, Any], Path]:
    """Load and hash-check the exact materialized 2,436-job index."""

    index_file = resolve_repo_path(index_path)
    if not index_file.is_file() or index_file.is_symlink():
        raise WebArenaRunControlError(f"jobs index is missing or unsafe: {index_file}")
    if not _sidecar_valid(index_file):
        raise WebArenaRunControlError("jobs index SHA sidecar is missing or stale")
    index = _load_object(index_file, "jobs index")
    if (
        index.get("schema_version") != SCHEDULE_INDEX_SCHEMA_VERSION
        or index.get("result_namespace") != RESULT_NAMESPACE
        or index.get("job_count") != EXPECTED_RECORD_SLOT_COUNT
    ):
        raise WebArenaRunControlError("jobs index identity/count is not the frozen full run")
    entries = index.get("entries")
    if not isinstance(entries, list) or len(entries) != EXPECTED_RECORD_SLOT_COUNT:
        raise WebArenaRunControlError("jobs index entries are incomplete")

    jobs: list[dict[str, Any]] = []
    for position, entry in enumerate(entries):
        if not isinstance(entry, Mapping) or entry.get("position") != position:
            raise WebArenaRunControlError(f"jobs index position changed at {position}")
        relative = entry.get("path")
        if not isinstance(relative, str) or Path(relative).name != relative:
            raise WebArenaRunControlError(f"unsafe job path at position {position}")
        job_file = index_file.parent / relative
        if not job_file.is_file() or job_file.is_symlink():
            raise WebArenaRunControlError(f"job file is missing or unsafe: {relative}")
        if entry.get("sha256") != sha256_file(job_file):
            raise WebArenaRunControlError(f"job hash changed: {relative}")
        job = _load_object(job_file, f"job {position}")
        if (
            job.get("record_slot_id") != entry.get("record_slot_id")
            or job.get("job_id") != entry.get("job_id")
        ):
            raise WebArenaRunControlError(f"job/index identity mismatch: {relative}")
        jobs.append(job)
    if index.get("jobs_sha256") != sha256_object(jobs):
        raise WebArenaRunControlError("jobs aggregate hash changed")
    synthetic = FullSchedulePlan(
        jobs=tuple(jobs),
        acceptance={"status": "pass", "formal_launch_eligible": True},
    )
    # This is the production executor's exact route/order/seed/reset validator.
    jobs_module_plan_validator = import_module(
        "evidence_system.orchestrator.webarena_verified_full_execution"
    )
    jobs_module_plan_validator._validate_executable_plan(synthetic)
    _validate_launch_authorization(index, index_file=index_file)
    return tuple(jobs), index, index_file


def load_materialized_full_plan(
    index_path: str | Path = DEFAULT_JOBS_INDEX,
) -> FullSchedulePlan:
    """Load the formal plan exclusively from the hash-checked job index.

    The legacy native-claim compiler package is historical planning lineage,
    not a runtime input and not a formal score draft.  Every value retained
    from that package is read from the already materialized jobs; this loader
    never opens the legacy ``native_claims`` tree.
    """

    jobs, index, index_file = load_full_jobs(index_path)
    lineage_fields = (
        "native_claim_index_sha256",
        "native_claim_acceptance_sha256",
        "source_bundle_sha256",
        "step19_manifest_sha256",
        "operator_waiver_sha256",
    )
    lineage: dict[str, str] = {}
    for field in lineage_fields:
        values = {
            str(dict(job.get("formal_policy_lock") or {}).get(field) or "")
            for job in jobs
        }
        if len(values) != 1:
            raise WebArenaRunControlError(
                f"materialized jobs disagree on historical lineage: {field}"
            )
        value = next(iter(values))
        if _SHA256_RE.fullmatch(value) is None:
            raise WebArenaRunControlError(
                f"materialized jobs have an invalid historical lineage hash: {field}"
            )
        lineage[field] = value

    authorization = dict(index.get("launch_authorization") or {})
    if authorization.get("operator_waiver_sha256") != lineage["operator_waiver_sha256"]:
        raise WebArenaRunControlError(
            "materialized jobs and index disagree on the operator waiver hash"
        )
    return FullSchedulePlan(
        jobs=jobs,
        acceptance={
            "schema_version": "webarena_verified_materialized_full_plan/v1",
            "status": "pass",
            "formal_launch_eligible": True,
            "plan_source": "hash_checked_materialized_full_jobs_index",
            "legacy_native_claim_compiler_runtime_dependency": False,
            "legacy_native_claim_hashes_are_lineage_only": True,
            "formal_score_draft_provider": "neurips_ed_track_minimal",
            "jobs_index": {
                "path": _display_path(index_file),
                "sha256": sha256_file(index_file),
                "job_count": len(jobs),
                "jobs_sha256": str(index["jobs_sha256"]),
            },
            "inputs": lineage,
            "launch_authorization": authorization,
        },
    )


def jobs_for_monitor_mode(
    *,
    mode: str,
    index_path: str | Path = DEFAULT_JOBS_INDEX,
) -> tuple[
    tuple[dict[str, Any], ...],
    dict[str, Any],
    Path,
    str,
    dict[str, Any],
]:
    full_jobs, index, index_file = load_full_jobs(index_path)
    if mode == "full":
        binding = {
            "kind": "materialized_full_jobs_index",
            "path": _display_path(index_file),
            "sha256": sha256_file(index_file),
            "job_count": len(full_jobs),
            "jobs_sha256": str(index["jobs_sha256"]),
        }
        return full_jobs, index, index_file, RESULT_NAMESPACE, binding
    if mode != "pilot":
        raise WebArenaRunControlError("monitor mode must be pilot or full")
    first_lock = dict(full_jobs[0].get("formal_policy_lock") or {})
    full = FullSchedulePlan(
        jobs=full_jobs,
        acceptance={
            "status": "pass",
            "formal_launch_eligible": True,
            "inputs": {
                "native_claim_index_sha256": first_lock.get(
                    "native_claim_index_sha256"
                )
            },
        },
    )
    pilot = build_pilot_schedule(full)
    pilot_jobs = tuple(dict(job) for job in pilot.jobs)
    pilot_jobs_hash = sha256_object(pilot_jobs)
    if len(pilot_jobs) != 24 or pilot_jobs_hash != EXPECTED_PILOT_JOBS_SHA256:
        raise WebArenaRunControlError(
            "derived pilot schedule is not the exact locked 24-slot schedule"
        )
    pilot_manifest = resolve_repo_path(DEFAULT_PILOT_MANIFEST)
    if not pilot_manifest.is_file() or not _sidecar_valid(pilot_manifest):
        raise WebArenaRunControlError("pilot manifest hash sidecar is missing or stale")
    schedule_payload = {
        "schema_version": "webarena_verified_pilot_monitor_schedule/v1",
        "status": "frozen_derived",
        "result_namespace": PILOT_RESULT_NAMESPACE,
        "job_count": 24,
        "jobs_sha256": pilot_jobs_hash,
        "pilot_manifest": {
            "path": _display_path(pilot_manifest),
            "sha256": sha256_file(pilot_manifest),
        },
        "source_full_jobs_index": {
            "path": _display_path(index_file),
            "sha256": sha256_file(index_file),
            "job_count": int(index["job_count"]),
            "jobs_sha256": str(index["jobs_sha256"]),
        },
        "derivation": "build_pilot_schedule_from_hash_checked_full_jobs_v1",
        "entries": [
            {
                "position": position,
                "record_slot_id": job["record_slot_id"],
                "task_id": int(job["task_id"]),
                "task_revision": int(job["task_revision"]),
                "agent_id": job["agent_id"],
                "seed": int(job["seed"]),
                "route": job["execution_target"],
                "job_object_sha256": sha256_object(job),
            }
            for position, job in enumerate(pilot_jobs)
        ],
    }
    schedule_path = resolve_repo_path(DEFAULT_PILOT_MONITOR_SCHEDULE)
    binding = {
        "kind": "materialized_derived_pilot_schedule",
        "path": _display_path(schedule_path),
        "sha256": hashlib.sha256(_json_bytes(schedule_payload)).hexdigest(),
        "job_count": 24,
        "jobs_sha256": pilot_jobs_hash,
        "pilot_manifest_path": _display_path(pilot_manifest),
        "pilot_manifest_sha256": sha256_file(pilot_manifest),
        "source_full_jobs_index_path": _display_path(index_file),
        "source_full_jobs_index_sha256": sha256_file(index_file),
    }
    schedule_payload["monitor_binding"] = {
        "job_count": 24,
        "jobs_sha256": pilot_jobs_hash,
        "result_namespace": PILOT_RESULT_NAMESPACE,
    }
    binding["sha256"] = hashlib.sha256(_json_bytes(schedule_payload)).hexdigest()
    canonical_binding = _canonical_pilot_schedule_binding(
        pilot_jobs=pilot_jobs,
        full_index=index,
        full_index_file=index_file,
        pilot_manifest=pilot_manifest,
    )
    if canonical_binding is not None:
        return (
            pilot_jobs,
            index,
            index_file,
            PILOT_RESULT_NAMESPACE,
            canonical_binding,
        )
    return pilot_jobs, index, index_file, PILOT_RESULT_NAMESPACE, {
        **binding,
        "payload": schedule_payload,
    }


def monitor_namespace(
    *,
    mode: str = "full",
    index_path: str | Path = DEFAULT_JOBS_INDEX,
    result_namespace: str | None = None,
    site_lock_path: str | Path = DEFAULT_SITE_LOCK,
    ssh_key_path: str | Path | None = None,
    remote_verify_files: bool = True,
    write_outputs: bool = True,
) -> MonitorSnapshot:
    """Audit slots without mutating any remote result directory."""

    jobs, _index, index_file, expected_namespace, schedule_binding = jobs_for_monitor_mode(
        mode=mode, index_path=index_path
    )
    namespace = result_namespace or expected_namespace
    if namespace != expected_namespace:
        raise WebArenaRunControlError(
            f"{mode} monitor namespace must be exactly {expected_namespace}"
        )
    namespace_root = resolve_repo_path(Path("results/namespaces") / namespace)
    site_lock_file = resolve_repo_path(site_lock_path)
    site_lock = load_site_lock(site_lock_file)
    if mode == "pilot" and write_outputs and "payload" in schedule_binding:
        payload = dict(schedule_binding.pop("payload"))
        schedule_path = resolve_repo_path(schedule_binding["path"])
        _atomic_write_json(schedule_path, payload, mode=0o644)
        _write_sidecar(schedule_path)
        if sha256_file(schedule_path) != schedule_binding["sha256"]:
            raise WebArenaRunControlError("materialized pilot monitor schedule hash changed")
    else:
        schedule_binding.pop("payload", None)
    remote_retention = any(
        job.get("artifact_retention_mode") == RETENTION_MODE for job in jobs
    )
    if remote_retention:
        if mode != "full":
            raise WebArenaRunControlError(
                "VPS persistent retention is allowed only for the full monitor"
            )
        if ssh_key_path is None:
            raise WebArenaRunControlError(
                "full remote-retention monitor requires an SSH private key"
            )
        key = resolve_repo_path(ssh_key_path)
        if not key.is_file() or key.is_symlink():
            raise WebArenaRunControlError("full monitor SSH private key is missing or unsafe")
        audits = audit_remote_schedule(
            jobs,
            jobs_index_path=index_file,
            ssh_key_path=key,
            site_lock=site_lock,
            verify_files=remote_verify_files,
        )
    else:
        audits = tuple(audit_slot(job, site_lock=site_lock) for job in jobs)

    ledger_path = namespace_root / "case_issue_ledger.jsonl"
    old_issues = _load_ledger(ledger_path)
    merged: dict[str, dict[str, Any]] = {item["issue_id"]: item for item in old_issues}
    observed_issue_keys = {
        (
            str(item["record_slot_id"]),
            str(item["circuit_class"]),
            str(item["signature"]),
        )
        for item in old_issues
    }
    for audit in audits:
        for issue in audit.issues:
            key = (
                str(issue["record_slot_id"]),
                str(issue["circuit_class"]),
                str(issue["signature"]),
            )
            if key in observed_issue_keys:
                continue
            merged.setdefault(str(issue["issue_id"]), issue)
            observed_issue_keys.add(key)
    issues = tuple(merged[key] for key in sorted(merged))
    ledger_bytes = _ledger_bytes(issues)
    ledger_sha256 = hashlib.sha256(ledger_bytes).hexdigest()
    controller_retryable = _controller_retryable_issue_receipt(
        namespace=namespace,
        audits=audits,
        issues=issues,
        ledger_path=ledger_path,
        ledger_sha256=ledger_sha256,
    )
    controller_retryable_path = (
        namespace_root / "controller_induced_retryable_issues.json"
    )
    controller_retryable_bytes = _json_bytes(controller_retryable)
    controller_retryable_sha256 = hashlib.sha256(
        controller_retryable_bytes
    ).hexdigest()
    progress = _progress_payload(
        mode=mode,
        namespace=namespace,
        jobs=jobs,
        audits=audits,
        issues=issues,
        schedule_binding=schedule_binding,
        source_jobs_index_path=index_file,
        source_jobs_index_sha256=sha256_file(index_file),
        ledger_path=ledger_path,
        ledger_sha256=ledger_sha256,
        controller_retryable_receipt={
            "path": _display_path(controller_retryable_path),
            "sha256": controller_retryable_sha256,
            "issue_count": controller_retryable["issue_count"],
            "record_slot_count": controller_retryable["record_slot_count"],
            "raw_issue_ledger_preserved": True,
        },
    )
    if write_outputs:
        namespace_root.mkdir(parents=True, exist_ok=True)
        _atomic_write_bytes(ledger_path, ledger_bytes, mode=0o600)
        _write_sidecar(ledger_path)
        _atomic_write_bytes(
            controller_retryable_path,
            controller_retryable_bytes,
            mode=0o600,
        )
        _write_sidecar(controller_retryable_path)
        progress_path = namespace_root / "progress_receipt.json"
        _atomic_write_json(progress_path, progress, mode=0o600)
        _write_sidecar(progress_path)
    return MonitorSnapshot(jobs=jobs, audits=audits, issues=issues, progress=progress)


def _remote_terminal_failure_issue(
    job: Mapping[str, Any], verification: Mapping[str, Any]
) -> dict[str, Any] | None:
    observed = verification.get("terminal_failure_observed")
    if observed is None:
        return None
    code = str(verification.get("terminal_failure_code") or "")
    summary_sha256 = str(verification.get("run_summary_sha256") or "")
    if (
        observed is not True
        or re.fullmatch(r"[a-z0-9_]{3,96}", code) is None
        or _SHA256_RE.fullmatch(summary_sha256) is None
    ):
        return _issue(
            job,
            classification="systemic",
            circuit_class="systemic",
            signature="remote_terminal_failure_envelope_invalid",
            summary="VPS terminal worker failure envelope is malformed",
            evidence_paths=(),
        )
    if code == "credential_or_billing_failure":
        return _issue(
            job,
            classification="systemic",
            circuit_class="credential",
            signature="credential_or_billing_failure",
            summary="model credential or billing authorization failed",
            evidence_paths=(),
            details={
                "remote_terminal_failure_code": code,
                "remote_run_summary_sha256": summary_sha256,
            },
        )
    return _issue(
        job,
        classification="infra",
        circuit_class="infra",
        signature="unclassified_runtime_failure",
        summary="isolated runtime failure requires review and later resume",
        evidence_paths=(),
        details={
            "remote_terminal_failure_code": code,
            "remote_run_summary_sha256": summary_sha256,
        },
    )


def _remote_completed_unsealed_issue(
    job: Mapping[str, Any], verification: Mapping[str, Any]
) -> dict[str, Any] | None:
    observed = verification.get("runtime_completed_unsealed")
    if observed is None:
        return None
    summary_sha256 = str(verification.get("run_summary_sha256") or "")
    if observed is not True or _SHA256_RE.fullmatch(summary_sha256) is None:
        return _issue(
            job,
            classification="systemic",
            circuit_class="systemic",
            signature="remote_completed_unsealed_envelope_invalid",
            summary="VPS completed-unsealed control envelope is malformed",
            evidence_paths=(),
        )
    return _issue(
        job,
        classification="infra",
        circuit_class="none",
        signature="post_run_audit_deferred_for_full_sweep",
        summary="paid runtime completed; final sealing is deferred to batch reconciliation",
        evidence_paths=(),
        details={"remote_run_summary_sha256": summary_sha256},
    )


def audit_remote_slot(
    job: Mapping[str, Any],
    *,
    ssh_key_path: str | Path,
    site_lock: Mapping[str, Any],
) -> SlotAudit:
    """Verify a VPS-resident slot and its artifact hashes over pinned SSH."""

    copied = dict(job)
    slot_id = str(copied["record_slot_id"])
    target_spec = dict(copied.get("execution_target") or {})
    agent_id = str(copied.get("agent_id") or "")
    if (
        copied.get("artifact_retention_mode") != RETENTION_MODE
        or target_spec != EXPECTED_ROUTES.get(agent_id)
    ):
        issue = _issue(
            copied,
            classification="systemic",
            circuit_class="systemic",
            signature="remote_retention_route_or_policy_mismatch",
            summary="formal slot is not bound to the locked VPS retention route",
            evidence_paths=(),
        )
        return SlotAudit(slot_id, "settled_invalid", False, (issue,), "remote:invalid")
    runner_root = str(site_lock.get("runner_root") or "")
    if not runner_root.startswith("/opt/"):
        raise WebArenaRunControlError("site lock has no safe remote runner root")
    target = InfraBenchmarkTarget(
        machine_id=str(target_spec["server_id"]),
        machine_role="webarena_vps",
        ssh_host=str(target_spec["ssh_host"]),
        ssh_user=str(target_spec["ssh_user"]),
        ssh_port=22,
        ssh_key_path=str(resolve_repo_path(ssh_key_path)),
        remote_workdir=DEFAULT_REMOTE_WORKDIR,
        runner_workdir=runner_root,
        benchmark_name="WebArena-Verified",
        benchmark_config={},
        benchmark_config_hash=str(copied.get("benchmark_config_hash") or ""),
        runner_command=f"{runner_root}/.venv/bin/python",
        machine_concurrency=1,
        ssh_host_ed25519_fingerprint=str(
            target_spec["ssh_host_ed25519_fingerprint"]
        ),
        ssh_public_key_fingerprint=str(
            target_spec["controller_ssh_public_key_fingerprint"]
        ),
    )
    relative = job_result_relative_dir(copied)
    adapter_root = str(
        PERSISTENT_RESULTS_ROOT.joinpath(*relative.parts[1:], "adapter")
    )
    command = (
        f"cd {shlex.quote(DEFAULT_REMOTE_WORKDIR)} && "
        f"PYTHONPATH={shlex.quote(f'{DEFAULT_REMOTE_WORKDIR}/src')} "
        f"{shlex.quote(target.runner_command)} -m "
        "evidence_system.adapters.webarena_remote_retention verify "
        f"--job-json {shlex.quote(json.dumps(copied, ensure_ascii=True, sort_keys=True))} "
        f"--adapter-root {shlex.quote(adapter_root)}"
    )
    observed = run_remote_blind_command(
        target,
        command,
        timeout_seconds=900,
        maximum_stdout_bytes=131_072,
        maximum_stderr_bytes=4096,
    )
    display_root = f"ssh://{target.ssh_user}@{target.ssh_host}{adapter_root}"
    if observed.returncode != 0 or observed.stderr:
        issue = _issue(
            copied,
            classification="systemic",
            circuit_class="systemic",
            signature="remote_artifact_ssh_verification_failed",
            summary="VPS-resident artifacts or their hashes failed SSH verification",
            evidence_paths=(),
        )
        return SlotAudit(slot_id, "settled_invalid", False, (issue,), display_root)
    try:
        verification = json.loads(observed.stdout or "{}")
    except json.JSONDecodeError:
        verification = {}
    if (
        not isinstance(verification, Mapping)
        or verification.get("status") != "pass"
        or verification.get("record_slot_id") != slot_id
        or verification.get("verified_over_ssh") is not True
    ):
        issue = _issue(
            copied,
            classification="systemic",
            circuit_class="systemic",
            signature="remote_artifact_control_envelope_invalid",
            summary="VPS artifact verifier returned an invalid control envelope",
            evidence_paths=(),
        )
        return SlotAudit(slot_id, "settled_invalid", False, (issue,), display_root)
    state = str(verification.get("state") or "")
    if state in {"pending", "in_progress"}:
        observed_issues = tuple(
            issue
            for issue in (
                _remote_terminal_failure_issue(copied, verification),
                _remote_completed_unsealed_issue(copied, verification),
            )
            if issue is not None
        )
        return SlotAudit(
            slot_id,
            state,
            False,
            observed_issues,
            display_root,
        )
    if state != "canonical_reusable":
        issue = _issue(
            copied,
            classification="systemic",
            circuit_class="systemic",
            signature="remote_artifact_noncanonical_state",
            summary="VPS artifact verifier did not return a canonical slot",
            evidence_paths=(),
        )
        return SlotAudit(slot_id, "settled_invalid", False, (issue,), display_root)
    return SlotAudit(
        slot_id,
        "canonical_reusable",
        True,
        (),
        display_root,
        {
            "task_id": int(copied["task_id"]),
            "agent_id": agent_id,
            "verification_mode": "ssh_remote_file_and_hash_validation",
            "remote_slot_acceptance_sha256": verification.get(
                "remote_slot_acceptance_sha256"
            ),
            "remote_artifact_manifest_sha256": verification.get(
                "remote_artifact_manifest_sha256"
            ),
            "remote_security_acceptance_sha256": verification.get(
                "remote_security_acceptance_sha256"
            ),
            "remote_evaluator_receipt_sha256": verification.get(
                "remote_evaluator_receipt_sha256"
            ),
            "score": verification.get("score"),
            "paid_model_call_count": verification.get("paid_model_call_count"),
            "observed_model_cost_usd": verification.get(
                "observed_model_cost_usd"
            ),
            "artifact_file_count": verification.get("artifact_file_count"),
            "artifact_total_size_bytes": verification.get(
                "artifact_total_size_bytes"
            ),
            "security_finding_count": verification.get("security_finding_count"),
            "gold_finding_count": verification.get("gold_finding_count"),
        },
    )


def audit_remote_schedule(
    jobs: Sequence[Mapping[str, Any]],
    *,
    jobs_index_path: str | Path,
    ssh_key_path: str | Path,
    site_lock: Mapping[str, Any],
    verify_files: bool = True,
) -> tuple[SlotAudit, ...]:
    """Verify all three formal lanes with one pinned SSH call per VPS."""

    by_slot = {str(job["record_slot_id"]): dict(job) for job in jobs}
    if len(by_slot) != len(jobs):
        raise WebArenaRunControlError("remote schedule contains duplicate slot IDs")
    index_file = resolve_repo_path(jobs_index_path)
    audits: dict[str, SlotAudit] = {}
    for agent_id in EXPECTED_AGENT_IDS:
        lane = [job for job in jobs if job.get("agent_id") == agent_id]
        if len(lane) != 812:
            raise WebArenaRunControlError(f"remote {agent_id} lane is incomplete")
        target = _remote_audit_target(
            lane[0], ssh_key_path=ssh_key_path, site_lock=site_lock
        )
        remote_index = (
            f"{DEFAULT_REMOTE_WORKDIR}/experiments/step20/"
            "webarena_verified/jobs/full/index.json"
        )
        command = (
            f"cd {shlex.quote(DEFAULT_REMOTE_WORKDIR)} && "
            f"PYTHONPATH={shlex.quote(f'{DEFAULT_REMOTE_WORKDIR}/src')} "
            f"{shlex.quote(target.runner_command)} -m "
            "evidence_system.adapters.webarena_remote_retention verify-schedule "
            f"--jobs-index {shlex.quote(remote_index)} "
            f"--server-id {shlex.quote(target.machine_id)}"
            + ("" if verify_files else " --receipt-only")
        )
        observed = run_remote_blind_command(
            target,
            command,
            timeout_seconds=3600,
            maximum_stdout_bytes=4_194_304,
            maximum_stderr_bytes=4096,
        )
        if observed.returncode != 0 or observed.stderr:
            raise WebArenaRunControlError(
                f"remote schedule SSH verification failed for {agent_id}"
            )
        try:
            payload = json.loads(observed.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise WebArenaRunControlError(
                f"remote schedule verifier returned invalid JSON for {agent_id}"
            ) from exc
        remote_items = payload.get("audits") if isinstance(payload, Mapping) else None
        if (
            not isinstance(remote_items, list)
            or payload.get("status") != "pass"
            or payload.get("server_id") != target.machine_id
            or payload.get("slot_count") != 812
            or payload.get("jobs_index_sha256") != sha256_file(index_file)
            or payload.get("verified_over_ssh") is not True
            or payload.get("artifact_files_rehashed") is not verify_files
        ):
            raise WebArenaRunControlError(
                f"remote schedule verifier binding changed for {agent_id}"
            )
        for verification in remote_items:
            if not isinstance(verification, Mapping):
                raise WebArenaRunControlError("remote schedule audit item is invalid")
            slot_id = str(verification.get("record_slot_id") or "")
            job = by_slot.get(slot_id)
            if job is None or job.get("agent_id") != agent_id:
                raise WebArenaRunControlError(
                    "remote schedule audit contains an unknown slot"
                )
            display_root = str(verification.get("persistent_adapter_root") or "")
            display_root = f"ssh://{target.ssh_user}@{target.ssh_host}{display_root}"
            state = str(verification.get("state") or "")
            if (
                verification.get("status") != "pass"
                or verification.get("verified_over_ssh") is not True
            ):
                issue = _issue(
                    job,
                    classification="systemic",
                    circuit_class="systemic",
                    signature="remote_artifact_control_envelope_invalid",
                    summary="VPS artifact verifier returned an invalid control envelope",
                    evidence_paths=(),
                )
                audits[slot_id] = SlotAudit(
                    slot_id, "settled_invalid", False, (issue,), display_root
                )
            elif state in {"pending", "in_progress"}:
                observed_issues = tuple(
                    issue
                    for issue in (
                        _remote_terminal_failure_issue(job, verification),
                        _remote_completed_unsealed_issue(job, verification),
                    )
                    if issue is not None
                )
                audits[slot_id] = SlotAudit(
                    slot_id,
                    state,
                    False,
                    observed_issues,
                    display_root,
                )
            elif state == "canonical_reusable":
                audits[slot_id] = SlotAudit(
                    slot_id,
                    state,
                    True,
                    (),
                    display_root,
                    {
                        "task_id": int(job["task_id"]),
                        "agent_id": str(job["agent_id"]),
                        "verification_mode": "ssh_remote_file_and_hash_validation",
                        "remote_slot_acceptance_sha256": verification.get(
                            "remote_slot_acceptance_sha256"
                        ),
                        "remote_artifact_manifest_sha256": verification.get(
                            "remote_artifact_manifest_sha256"
                        ),
                        "remote_security_acceptance_sha256": verification.get(
                            "remote_security_acceptance_sha256"
                        ),
                        "remote_evaluator_receipt_sha256": verification.get(
                            "remote_evaluator_receipt_sha256"
                        ),
                        "score": verification.get("score"),
                    },
                )
            else:
                issue = _issue(
                    job,
                    classification="systemic",
                    circuit_class="systemic",
                    signature="remote_artifact_noncanonical_state",
                    summary="VPS artifact verifier returned an unknown slot state",
                    evidence_paths=(),
                )
                audits[slot_id] = SlotAudit(
                    slot_id, "settled_invalid", False, (issue,), display_root
                )
    if set(audits) != set(by_slot):
        raise WebArenaRunControlError("remote schedule audit is incomplete")
    return tuple(audits[str(job["record_slot_id"])] for job in jobs)


def _remote_audit_target(
    job: Mapping[str, Any],
    *,
    ssh_key_path: str | Path,
    site_lock: Mapping[str, Any],
) -> InfraBenchmarkTarget:
    target_spec = dict(job.get("execution_target") or {})
    runner_root = str(site_lock.get("runner_root") or "")
    return InfraBenchmarkTarget(
        machine_id=str(target_spec["server_id"]),
        machine_role="webarena_vps",
        ssh_host=str(target_spec["ssh_host"]),
        ssh_user=str(target_spec["ssh_user"]),
        ssh_port=22,
        ssh_key_path=str(resolve_repo_path(ssh_key_path)),
        remote_workdir=DEFAULT_REMOTE_WORKDIR,
        runner_workdir=runner_root,
        benchmark_name="WebArena-Verified",
        benchmark_config={},
        benchmark_config_hash=str(job.get("benchmark_config_hash") or ""),
        runner_command=f"{runner_root}/.venv/bin/python",
        machine_concurrency=1,
        ssh_host_ed25519_fingerprint=str(
            target_spec["ssh_host_ed25519_fingerprint"]
        ),
        ssh_public_key_fingerprint=str(
            target_spec["controller_ssh_public_key_fingerprint"]
        ),
    )


def audit_slot(job: Mapping[str, Any], *, site_lock: Mapping[str, Any]) -> SlotAudit:
    """Return a granular, read-only audit of one result slot."""

    copied = dict(job)
    slot_id = str(copied["record_slot_id"])
    root = resolve_repo_path(job_result_relative_dir(copied) / "adapter")
    display_root = _display_path(root)
    if not root.exists():
        return SlotAudit(slot_id, "pending", False, (), display_root)
    if root.is_symlink() or not root.is_dir():
        issue = _issue(
            copied,
            classification="systemic",
            circuit_class="systemic",
            signature="unsafe_slot_root",
            summary="slot result root is not a regular directory",
            evidence_paths=(),
        )
        return SlotAudit(slot_id, "settled_invalid", False, (issue,), display_root)

    raw_path = root / "raw_run.json"
    failure_path = root / "failure_record.json"
    if not raw_path.is_file():
        if failure_path.is_file():
            issue = _classify_failure_record(copied, failure_path)
            return SlotAudit(slot_id, "settled_invalid", False, (issue,), display_root)
        if _is_empty_prelaunch_scaffold(root):
            # build_job_paths creates empty controller directories before the
            # first remote preflight.  A failure before environment/reset/
            # worker evidence exists is not a benchmark attempt and remains
            # canonically pending for the same locked slot.
            return SlotAudit(slot_id, "pending", False, (), display_root)
        return SlotAudit(slot_id, "in_progress", False, (), display_root)

    issues: list[dict[str, Any]] = []
    manifest_path = root / "artifact_manifest.json"
    environment_path = root / "environment.json"
    native_root = root / "native_run"
    task_id = int(copied["task_id"])
    task_dir = native_root / str(task_id)
    required = {
        "artifact_manifest": manifest_path,
        "environment": environment_path,
        "reset_receipt": native_root / "reset_receipt.json",
        "run_summary": native_root / "run_summary.json",
        "official_task": task_dir / "official_task_config.json",
        "solver_trace": task_dir / "solver_trace.json",
        "network_har": task_dir / "network.har",
        "network_har_sanitization": task_dir
        / "network_har_sanitization.json",
        "playwright_trace": native_root / "traces" / f"{task_id}.zip",
        "eval_result": task_dir / "eval_result.json",
        "eval_summary": task_dir / "eval_summary.json",
        "agent_response": task_dir / "agent_response.json",
    }
    missing = [label for label, path in required.items() if not path.is_file()]
    if missing:
        run_summary_path = required["run_summary"]
        run_summary = _load_optional_object(run_summary_path)
        if run_summary is not None and run_summary.get("status") == "error":
            error_text = " ".join(
                str(run_summary.get(key) or "")
                for key in ("error_type", "error_message", "status")
            )
            issues.append(
                _classify_runtime_text(
                    copied,
                    error_text,
                    evidence_paths=(raw_path, run_summary_path),
                )
            )
            return SlotAudit(
                slot_id, "settled_invalid", False, tuple(issues), display_root
            )
        issues.append(
            _issue(
                copied,
                classification="infra",
                circuit_class="infra",
                signature="settled_slot_missing_required_artifacts",
                summary="settled slot is missing required canonical artifacts",
                evidence_paths=(raw_path,),
                details={"missing_artifact_labels": sorted(missing)},
            )
        )
        return SlotAudit(slot_id, "settled_invalid", False, tuple(issues), display_root)

    raw = _load_optional_object(raw_path)
    manifest = _load_optional_object(manifest_path)
    environment = _load_optional_object(environment_path)
    if raw is None or manifest is None or environment is None:
        issues.append(
            _issue(
                copied,
                classification="systemic",
                circuit_class="systemic",
                signature="invalid_controller_json",
                summary="controller result metadata is not valid JSON object data",
                evidence_paths=(raw_path, manifest_path, environment_path),
            )
        )
        return SlotAudit(slot_id, "settled_invalid", False, tuple(issues), display_root)

    source_bundle_hash = str(
        dict(copied.get("formal_policy_lock") or {}).get("source_bundle_sha256") or ""
    )
    controller_checks = (
        raw.get("status") == "COMPLETED",
        str(raw.get("diagnostic_status") or "completed").lower() == "completed",
        jobs_module._raw_run_matches_job(raw, copied),
        jobs_module._artifact_manifest_matches_job(
            manifest,
            copied,
            source_bundle_hash=source_bundle_hash,
            official_split_hash=EXPECTED_SOURCE_SHA256,
        ),
        jobs_module._environment_matches_job(environment, copied),
        raw.get("artifact_manifest_sha256") == sha256_file(manifest_path),
    )
    if not all(controller_checks):
        issues.append(
            _issue(
                copied,
                classification="systemic",
                circuit_class="systemic",
                signature="controller_job_binding_mismatch",
                summary="raw run, environment, or artifact manifest is not bound to the frozen job",
                evidence_paths=(raw_path, manifest_path, environment_path),
            )
        )

    artifact_failure = _artifact_integrity_failure(manifest, root=root)
    if artifact_failure is not None:
        issues.append(
            _issue(
                copied,
                classification="systemic",
                circuit_class="systemic",
                signature="artifact_hash_or_path_mismatch",
                summary="one or more artifact manifest entries failed path/hash/size validation",
                evidence_paths=(manifest_path,),
                details={"integrity_failure": artifact_failure},
            )
        )

    reset_failure = _reset_integrity_failure(
        _load_optional_object(required["reset_receipt"]),
        job=copied,
        site_lock=site_lock,
    )
    if reset_failure is not None:
        issues.append(
            _issue(
                copied,
                classification="infra",
                circuit_class="reset",
                signature="slot_reset_integrity_failure",
                summary="pre-slot reset receipt failed identity, scope, pin, or replacement validation",
                evidence_paths=(required["reset_receipt"],),
                details={"reset_failure": reset_failure},
            )
        )

    try:
        load_and_validate_network_sanitization_receipt(
            required["network_har_sanitization"],
            har_path=required["network_har"],
            trace_path=required["playwright_trace"],
        )
    except (HarSanitizationError, OSError, ValueError) as exc:
        issues.append(
            _issue(
                copied,
                classification="systemic",
                circuit_class="systemic",
                signature="network_sanitization_receipt_failure",
                summary=(
                    "HAR/trace sanitization receipt failed artifact hash, size, "
                    "or redaction validation"
                ),
                evidence_paths=(
                    required["network_har_sanitization"],
                    required["network_har"],
                    required["playwright_trace"],
                ),
                details={"error_type": type(exc).__name__},
            )
        )

    native_ok = jobs_module._webarena_native_run_is_auditable(root)
    if not native_ok:
        issues.append(
            _issue(
                copied,
                classification="systemic",
                circuit_class="systemic",
                signature="official_native_audit_failed",
                summary="official task, revision, sites, HAR, trace, or evaluator binding is invalid",
                evidence_paths=tuple(required.values()),
            )
        )

    binding_failure = _source_and_trajectory_binding_failure(copied, required)
    if binding_failure is not None:
        issues.append(
            _issue(
                copied,
                classification="systemic",
                circuit_class="systemic",
                signature="task_source_or_trajectory_binding_failure",
                summary="official task/source packet/trajectory disagrees with the frozen task definition",
                evidence_paths=(
                    required["official_task"],
                    required["solver_trace"],
                    TASK_PACKET_ROOT / str(task_id) / "case_packet.json",
                    TASK_PACKET_ROOT / str(task_id) / "agent_input.json",
                ),
                details={"binding_failure": binding_failure},
            )
        )

    integrity_ok = not any(
        issue["circuit_class"] in {"systemic", "reset"} for issue in issues
    )
    semantic_review: Mapping[str, Any] | None = None
    if integrity_ok and native_ok:
        semantic_review, quality_issues = _semantic_case_review(copied, required)
        issues.extend(quality_issues)
    reusable = bool(integrity_ok and native_ok and artifact_failure is None)
    return SlotAudit(
        slot_id,
        "canonical_reusable" if reusable else "settled_invalid",
        reusable,
        tuple(_deduplicate_issues(issues)),
        display_root,
        semantic_review,
    )


def _is_empty_prelaunch_scaffold(root: Path) -> bool:
    try:
        for current, directories, filenames in os.walk(root, followlinks=False):
            current_path = Path(current)
            if filenames:
                return False
            for name in directories:
                child = current_path / name
                if child.is_symlink() or not child.is_dir():
                    return False
    except OSError:
        return False
    return True


def build_full_run_control_acceptance(
    *,
    plan: FullSchedulePlan,
    jobs_index_path: str | Path = DEFAULT_JOBS_INDEX,
    snapshot: MonitorSnapshot | None = None,
    pilot_acceptance_path: str | Path = DEFAULT_PILOT_ACCEPTANCE,
    storage_acceptance_path: str | Path = DEFAULT_STORAGE_ACCEPTANCE,
    credential_acceptance_path: str | Path = DEFAULT_CREDENTIAL_ACCEPTANCE,
    pilot_budget_capacity_acceptance_path: str | Path = (
        DEFAULT_PILOT_BUDGET_CAPACITY_ACCEPTANCE
    ),
    remote_retention_canary_acceptance_path: str | Path = (
        DEFAULT_REMOTE_RETENTION_CANARY_ACCEPTANCE
    ),
    circuit_recovery_receipt_path: str | Path = (
        DEFAULT_CIRCUIT_RECOVERY_RECEIPT
    ),
    dry_run: bool = True,
) -> dict[str, Any]:
    jobs, index, index_file = load_full_jobs(jobs_index_path)
    if tuple(plan.jobs) != jobs or execution_input_hash(plan) != index.get("jobs_sha256"):
        raise WebArenaRunControlError("planner jobs differ from the materialized jobs index")
    if snapshot is None:
        snapshot = monitor_namespace(
            mode="full", index_path=index_file, write_outputs=True
        )
    authorization = dict(index.get("launch_authorization") or {})
    pilot_gate = _future_gate(pilot_acceptance_path, require_all_gates=True)
    storage_gate = _storage_gate(storage_acceptance_path)
    credential_gate = _future_gate(credential_acceptance_path, require_all_gates=False)
    pilot_budget_capacity_gate = _future_gate(
        pilot_budget_capacity_acceptance_path,
        require_all_gates=True,
    )
    remote_retention_canary_gate = _remote_retention_canary_gate(
        remote_retention_canary_acceptance_path
    )
    recovery_gate = _circuit_recovery_gate(
        path_value=circuit_recovery_receipt_path,
        snapshot=snapshot,
        jobs_index_path=index_file,
    )
    raw_circuit_clear = snapshot.progress["circuit_breaker"]["tripped"] is False
    effective_circuit_clear = raw_circuit_clear or recovery_gate["status"] == "pass"
    effective_remote_canary = (
        remote_retention_canary_gate["status"] == "pass"
        or recovery_gate["status"] == "pass"
    )
    formal_ready = bool(
        pilot_gate["status"] == "pass"
        and storage_gate["status"] == "pass"
        and credential_gate["status"] == "pass"
        and pilot_budget_capacity_gate["status"] == "pass"
        and effective_remote_canary
        and all(job.get("artifact_retention_mode") == RETENTION_MODE for job in jobs)
        and effective_circuit_clear
    )
    lanes = []
    for agent_id in EXPECTED_AGENT_IDS:
        lane_jobs = [job for job in jobs if job["agent_id"] == agent_id]
        lanes.append(
            {
                "agent_id": agent_id,
                "job_count": len(lane_jobs),
                "sequential": True,
                "concurrency": 1,
                "task_order": "0..811",
                "route": EXPECTED_ROUTES[agent_id],
                "reset_before_every_slot": all(
                    job.get("reset_policy") == "recreate_task_sites_from_digest_v1"
                    and job.get("reset_receipt_relative_path") == "reset_receipt.json"
                    for job in lane_jobs
                ),
            }
        )
    progress_path = resolve_repo_path(
        Path("results/namespaces") / RESULT_NAMESPACE / "progress_receipt.json"
    )
    return {
        "schema_version": CONTROL_SCHEMA,
        "status": "pass",
        "dry_run": bool(dry_run),
        "result_namespace": RESULT_NAMESPACE,
        "fresh_namespace_policy": "formal_namespace_only_never_pilot_namespace",
        "jobs_index": {
            "path": _display_path(index_file),
            "sha256": sha256_file(index_file),
            "count": len(jobs),
            "jobs_sha256": str(index["jobs_sha256"]),
        },
        "operator_waiver_sha256": authorization.get("operator_waiver_sha256"),
        "human_signed_count": authorization.get("human_signed_count"),
        "human_signoff_claimed": authorization.get("human_signoff_claimed"),
        "human_review_requirement_waived": authorization.get(
            "human_review_requirement_waived"
        ),
        "lanes": lanes,
        "cross_lane_parallelism": 3,
        "reuse_policy": "canonical_fully_validated_slots_only",
        "issue_policy": "record_needs_review_do_not_interrupt_or_change_score",
        "circuit_breaker_policy": {
            "immediate": sorted(IMMEDIATE_CIRCUIT_CLASSES),
            "consecutive_failure_scope": "per_agent_lane_ordered_slots",
            "consecutive_lane_failure_threshold": (
                CONSECUTIVE_LANE_FAILURE_THRESHOLD
            ),
            "consecutive_controller_failure_threshold": (
                CONSECUTIVE_CONTROLLER_FAILURE_THRESHOLD
            ),
            "controller_failure_scope": (
                "per_agent_reset_or_pre_slot_controller_failures"
            ),
            "isolated_infra_issues_block_full_sweep": False,
            "post_run_audit_failures_reconciled_after_full_sweep": True,
            "full_sweep_record_only_infra_issues": (
                FULL_SWEEP_RECORD_ONLY_INFRA_ISSUES
            ),
            "canonical_slot_resets_lane_streak": True,
            "different_lanes_never_combine": True,
            "different_failure_signatures_in_one_lane_do_combine": True,
            "checked_between_slots_only": True,
            "in_flight_worker_interrupted": False,
        },
        "paid_confirmation_required": PAID_FULL_CONFIRMATION,
        "formal_paid_launch_ready": formal_ready,
        "launch_gates": {
            "pilot": pilot_gate,
            "storage": storage_gate,
            "credential": credential_gate,
            "pilot_budget_and_openrouter_capacity": pilot_budget_capacity_gate,
            "remote_retention_three_host_canary": remote_retention_canary_gate,
            "circuit_recovery_authorization": recovery_gate,
            "effective_remote_retention_canary_clear": effective_remote_canary,
            "formal_jobs_vps_persistent_retention_locked": all(
                job.get("artifact_retention_mode") == RETENTION_MODE for job in jobs
            ),
            "raw_monitor_circuit_clear": raw_circuit_clear,
            "monitor_circuit_clear": effective_circuit_clear,
            "effective_execution_circuit_clear": effective_circuit_clear,
        },
        "progress_receipt": {
            "path": _display_path(progress_path),
            "sha256": sha256_file(progress_path) if progress_path.is_file() else None,
            "expected_slots": len(jobs),
            "canonical_reusable_slots": snapshot.progress["counts"][
                "canonical_reusable"
            ],
        },
        "paid_calls_made_by_dry_run": 0,
        "dotenv_read_by_dry_run": False,
        "secret_material_recorded": False,
    }


def write_control_acceptance(
    payload: Mapping[str, Any],
    *,
    output_path: str | Path = DEFAULT_CONTROL_ACCEPTANCE,
) -> Path:
    path = resolve_repo_path(output_path)
    _atomic_write_json(path, dict(payload), mode=0o644)
    _write_sidecar(path)
    return path


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _recovery_code_bindings() -> dict[str, str]:
    return {
        path: sha256_file(resolve_repo_path(path))
        for path in RECOVERY_CRITICAL_CODE_PATHS
    }


def _junit_gate(path_value: str | Path) -> dict[str, Any]:
    path = resolve_repo_path(path_value)
    if not path.is_file() or path.is_symlink():
        return {"status": "fail", "path": _display_path(path), "sha256": None}
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        return {
            "status": "fail",
            "path": _display_path(path),
            "sha256": sha256_file(path),
        }
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    try:
        tests = sum(int(item.attrib.get("tests", "0")) for item in suites)
        failures = sum(int(item.attrib.get("failures", "0")) for item in suites)
        errors = sum(int(item.attrib.get("errors", "0")) for item in suites)
    except ValueError:
        tests, failures, errors = 0, 1, 1
    observed_test_cases = {
        str(item.attrib.get("name") or "") for item in root.iter("testcase")
    }
    required_test_cases_present = REQUIRED_RECOVERY_TEST_CASES.issubset(
        observed_test_cases
    )
    return {
        "status": (
            "pass"
            if tests > 0
            and failures == 0
            and errors == 0
            and required_test_cases_present
            else "fail"
        ),
        "path": _display_path(path),
        "sha256": sha256_file(path),
        "tests": tests,
        "failures": failures,
        "errors": errors,
        "required_test_cases": sorted(REQUIRED_RECOVERY_TEST_CASES),
        "required_test_cases_present": required_test_cases_present,
    }


def _vps_host_finalization_receipts_ok(
    host_receipts: Any,
    *,
    expected_agent_ids: set[str],
) -> bool:
    """Validate VPS-resident host finalization summaries without fetching them."""

    if not isinstance(host_receipts, list) or len(host_receipts) != len(
        expected_agent_ids
    ):
        return False
    if {
        str(item.get("agent_id"))
        for item in host_receipts
        if isinstance(item, Mapping)
    } != expected_agent_ids:
        return False
    for item in host_receipts:
        if not isinstance(item, Mapping):
            return False
        if item.get("path") not in (None, ""):
            # Legacy receipts were copied before the VPS-only policy. Keep
            # validation compatible without allowing new code to retrieve one.
            receipt_path = resolve_repo_path(str(item.get("path") or ""))
            if (
                not receipt_path.is_file()
                or receipt_path.is_symlink()
                or sha256_file(receipt_path) != item.get("sha256")
            ):
                return False
            receipt = _load_optional_object(receipt_path)
            if (
                receipt is None
                or receipt.get("status") != "pass"
                or receipt.get("server_id") != item.get("server_id")
                or receipt.get("slot_count") != 1
                or receipt.get("security_finding_count") != 0
                or receipt.get("gold_finding_count") != 0
                or receipt.get("remote_directory_cleanup_performed") is not False
                or receipt.get("full_evidence_synced_to_controller") is not False
            ):
                return False
            continue
        namespace_prefix = str(PERSISTENT_RESULTS_ROOT / "namespaces") + "/"
        if (
            item.get("status") != "pass"
            or not isinstance(item.get("server_id"), str)
            or not item.get("server_id")
            or not isinstance(item.get("persistent_namespace_root"), str)
            or not str(item.get("persistent_namespace_root")).startswith(
                namespace_prefix
            )
            or item.get("slot_count") != 1
            or item.get("security_scan_executed_on_vps") is not True
            or item.get("security_finding_count") != 0
            or item.get("gold_finding_count") != 0
            or item.get("remote_directory_cleanup_performed") is not False
            or item.get("full_evidence_synced_to_controller") is not False
            or item.get("vps_resident") is not True
            or item.get("receipt_hash_algorithm") != "sha256_canonical_json_v1"
            or _SHA256_RE.fullmatch(str(item.get("receipt_sha256") or "")) is None
        ):
            return False
    return True


def _trace_heavy_recovery_canary_gate(path_value: str | Path) -> dict[str, Any]:
    path = resolve_repo_path(path_value)
    if not path.is_file() or path.is_symlink() or not _sidecar_valid(path):
        return {
            "status": "fail",
            "path": _display_path(path),
            "sha256": sha256_file(path) if path.is_file() else None,
        }
    payload = _load_optional_object(path)
    if payload is None:
        return {"status": "fail", "path": _display_path(path), "sha256": sha256_file(path)}
    results = payload.get("results")
    host_receipts = payload.get("remote_host_finalization_receipts")
    bindings = dict(payload.get("control_bindings") or {})
    critical = dict(bindings.get("critical_code_sha256") or {})
    current_index = resolve_repo_path(DEFAULT_JOBS_INDEX)
    results_ok = (
        isinstance(results, list)
        and len(results) == 1
        and isinstance(results[0], Mapping)
        and results[0].get("agent_id") == "Agent A"
        and results[0].get("audit_state") == "canonical_reusable"
        and results[0].get("security_finding_count") == 0
        and results[0].get("gold_finding_count") == 0
    )
    host_ok = _vps_host_finalization_receipts_ok(
        host_receipts,
        expected_agent_ids={"Agent A"},
    )
    bindings_ok = bool(
        bindings.get("schema_version")
        == "webarena_verified_canary_control_bindings/v1"
        and bindings.get("materialized_full_jobs_index_path")
        == _display_path(current_index)
        and bindings.get("materialized_full_jobs_index_sha256")
        == sha256_file(current_index)
        and bindings.get("materialized_full_jobs_sha256")
        == "5c613b729e96ac020b9e2a8d5cdba667371f086be7c5cad4e46292d9a349e704"
        and bindings.get("materialized_full_job_count") == EXPECTED_RECORD_SLOT_COUNT
        and bindings.get("legacy_native_claim_compiler_runtime_dependency") is False
        and bindings.get("formal_score_draft_provider") == "neurips_ed_track_minimal"
        and set(critical) == set(RECOVERY_CRITICAL_CODE_PATHS)
        and critical == _recovery_code_bindings()
    )
    ok = bool(
        payload.get("schema_version")
        == "webarena_verified_three_host_task0_canary_acceptance/v1"
        and payload.get("status") == "pass"
        and payload.get("task_id") == 64
        and payload.get("result_namespace") != RESULT_NAMESPACE
        and payload.get("paid_slot_count") == 1
        and payload.get("required_artifact_audit_pass_count") == 1
        and payload.get("artifact_retention_mode") == RETENTION_MODE
        and payload.get("remote_file_and_hash_verification_over_ssh") is True
        and payload.get("security_scan_and_finalization_executed_on_each_vps") is True
        and payload.get("full_evidence_synced_to_controller") is False
        and payload.get("remote_directory_cleanup_performed") is False
        and results_ok
        and host_ok
        and bindings_ok
    )
    return {
        "status": "pass" if ok else "fail",
        "path": _display_path(path),
        "sha256": sha256_file(path),
        "task_id": payload.get("task_id"),
        "result_namespace": payload.get("result_namespace"),
    }


def _live_quiescence(
    *,
    jobs: Sequence[Mapping[str, Any]],
    ssh_key_path: str | Path,
    site_lock_path: str | Path,
) -> dict[str, Any]:
    site_lock = load_site_lock(resolve_repo_path(site_lock_path))
    runtime_paths = {
        "webarena_har_sanitization.py": (
            "src/evidence_system/adapters/webarena_har_sanitization.py"
        ),
        "webarena_remote_retention.py": (
            "src/evidence_system/adapters/webarena_remote_retention.py"
        ),
    }
    expected_runtime_hashes = {
        name: sha256_file(resolve_repo_path(relative))
        for name, relative in runtime_paths.items()
    }
    observations: list[dict[str, Any]] = []
    for agent_id in EXPECTED_AGENT_IDS:
        lane = [dict(job) for job in jobs if job.get("agent_id") == agent_id]
        target = _remote_audit_target(
            lane[0], ssh_key_path=ssh_key_path, site_lock=site_lock
        )
        sanitizer_path = (
            f"{target.remote_workdir.rstrip('/')}/src/evidence_system/adapters/"
            "webarena_har_sanitization.py"
        )
        retention_path = (
            f"{target.remote_workdir.rstrip('/')}/src/evidence_system/adapters/"
            "webarena_remote_retention.py"
        )
        command = (
            "count=$({ pgrep -f '[w]ebarena_official_worker' || true; } | wc -l); "
            f"sanitizer=$(sha256sum {shlex.quote(sanitizer_path)} | cut -d' ' -f1); "
            f"retention=$(sha256sum {shlex.quote(retention_path)} | cut -d' ' -f1); "
            "printf '{\"active_worker_count\":%s,"
            "\"webarena_har_sanitization.py\":\"%s\","
            "\"webarena_remote_retention.py\":\"%s\"}\\n' "
            '"$count" "$sanitizer" "$retention"'
        )
        observed = run_remote_blind_command(
            target,
            command,
            timeout_seconds=60,
            maximum_stdout_bytes=1024,
            maximum_stderr_bytes=1024,
        )
        try:
            payload = json.loads(observed.stdout or "{}")
        except json.JSONDecodeError:
            payload = {}
        count = payload.get("active_worker_count")
        runtime_hashes = {
            name: payload.get(name) for name in sorted(runtime_paths)
        }
        if (
            observed.returncode != 0
            or observed.stderr
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count < 0
            or runtime_hashes != expected_runtime_hashes
        ):
            raise WebArenaRunControlError(
                f"cannot prove worker quiescence for {agent_id}"
            )
        observations.append(
            {
                "agent_id": agent_id,
                "server_id": target.machine_id,
                "active_worker_count": count,
                "runtime_code_sha256": runtime_hashes,
                "verified_over_ssh": True,
            }
        )
    total = sum(item["active_worker_count"] for item in observations)
    return {
        "status": "pass" if total == 0 else "fail",
        "active_worker_count": total,
        "hosts": observations,
        "expected_runtime_code_sha256": expected_runtime_hashes,
        "workers_stopped_or_killed_by_check": 0,
    }


def build_circuit_recovery_receipt(
    *,
    snapshot: MonitorSnapshot,
    jobs_index_path: str | Path,
    trace_heavy_canary_acceptance_path: str | Path,
    junit_report_path: str | Path,
    ssh_key_path: str | Path,
    credential_recovery_canary_acceptance_path: str | Path = (
        DEFAULT_REMOTE_RETENTION_CANARY_ACCEPTANCE
    ),
    site_lock_path: str | Path = DEFAULT_SITE_LOCK,
    confirmation: str,
    output_path: str | Path = DEFAULT_CIRCUIT_RECOVERY_RECEIPT,
) -> dict[str, Any]:
    if confirmation != CIRCUIT_RECOVERY_ISSUE_CONFIRMATION:
        raise WebArenaRunControlError("exact circuit-recovery issuance confirmation is required")
    circuit = dict(snapshot.progress.get("circuit_breaker") or {})
    immediate_classes = set(circuit.get("immediate_classes_observed") or [])
    credential_recovery = immediate_classes == {"credential"}
    if (
        circuit.get("tripped") is not True
        or immediate_classes - {"credential"}
        or (not immediate_classes and not circuit.get("tripped_lanes"))
    ):
        raise WebArenaRunControlError(
            "circuit recovery is allowed only for an infra lane-streak trip or "
            "a credential-only trip"
        )
    canary = _trace_heavy_recovery_canary_gate(trace_heavy_canary_acceptance_path)
    credential_canary = _remote_retention_canary_gate(
        credential_recovery_canary_acceptance_path
    )
    junit = _junit_gate(junit_report_path)
    if (
        canary["status"] != "pass"
        or junit["status"] != "pass"
        or (credential_recovery and credential_canary["status"] != "pass")
    ):
        raise WebArenaRunControlError("recovery canary and targeted tests must pass")
    terminal_slots = sorted(
        audit.record_slot_id for audit in snapshot.audits if audit.state == "in_progress"
    )
    issues_by_slot: dict[str, list[Mapping[str, Any]]] = {}
    for issue in snapshot.issues:
        issues_by_slot.setdefault(str(issue["record_slot_id"]), []).append(issue)
    if not terminal_slots or any(slot not in issues_by_slot for slot in terminal_slots):
        raise WebArenaRunControlError(
            "every partial slot must have a terminal issue before recovery"
        )
    jobs, index, index_path = load_full_jobs(jobs_index_path)
    quiescence = _live_quiescence(
        jobs=jobs,
        ssh_key_path=ssh_key_path,
        site_lock_path=site_lock_path,
    )
    if quiescence["status"] != "pass":
        raise WebArenaRunControlError("all three VPS workers must be quiescent")
    authorized_issues = sorted(
        str(issue["issue_id"])
        for slot in terminal_slots
        for issue in issues_by_slot[slot]
    )
    recovered_agents = (
        sorted(
            {
                str(issue["agent_id"])
                for issue in snapshot.issues
                if issue.get("circuit_class") == "credential"
            }
        )
        if credential_recovery
        else list(circuit["tripped_lanes"])
    )
    if credential_recovery and not recovered_agents:
        raise WebArenaRunControlError(
            "credential recovery requires at least one affected agent lane"
        )
    core = {
        "schema_version": CIRCUIT_RECOVERY_SCHEMA,
        "status": "pass",
        "result_namespace": RESULT_NAMESPACE,
        "created_at_utc": _utc_now_iso(),
        "trigger": {
            "progress_payload_sha256": sha256_object(snapshot.progress),
            "issue_ledger_sha256": snapshot.progress["ledger"]["sha256"],
            "issue_ledger_entry_count": snapshot.progress["ledger"]["entry_count"],
            "circuit_fingerprint_sha256": sha256_object(circuit),
            "raw_circuit_breaker": circuit,
            "triggering_issue_ids": authorized_issues,
            "terminal_partial_slot_ids": terminal_slots,
        },
        "immutable_inputs": {
            "jobs_index_path": _display_path(index_path),
            "jobs_index_sha256": sha256_file(index_path),
            "jobs_sha256": index["jobs_sha256"],
            "job_count": len(jobs),
            "critical_code_sha256": _recovery_code_bindings(),
        },
        "diagnosis_and_remediation": {
            "diagnosis": (
                "historical_openrouter_credential_failure_revalidated_by_"
                "current_three_host_paid_canary"
                if credential_recovery
                else "playwright_trace_empty_json_resource_misclassified_as_structured"
            ),
            "recovery_mode": (
                "credential_only_current_paid_canary"
                if credential_recovery
                else "infra_lane_streak"
            ),
            "sanitizer_algorithm_version": (
                "webarena_verified_har_trace_credential_value_redaction_v7"
            ),
            "structured_member_limit_bytes": 50_000_000,
            "opaque_member_limit_bytes": 256_000_000,
            "archive_total_limit_bytes": 512_000_000,
            "opaque_stream_chunk_bytes": 1_048_576,
            "jobs_changed": False,
            "ledger_rewritten": False,
            "partial_evidence_deleted": False,
        },
        "quiescence": quiescence,
        "validation": {
            "trace_heavy_canary": canary,
            "credential_recovery_canary": credential_canary,
            "targeted_tests": junit,
            "security_finding_count": 0,
            "gold_finding_count": 0,
        },
        "authorization": {
            "decision": "clear_for_exact_resume",
            "issuance_confirmation": CIRCUIT_RECOVERY_ISSUE_CONFIRMATION,
            "authorized_issue_ids": authorized_issues,
            "new_failure_streak_epoch_agent_ids": recovered_agents,
        },
        "policy": {
            "raw_circuit_history_preserved": True,
            "issue_ledger_preserved": True,
            "noncredential_immediate_circuit_classes_not_overridable": True,
            "credential_recovery_requires_current_three_host_paid_canary": True,
            "consecutive_lane_failure_threshold": CONSECUTIVE_LANE_FAILURE_THRESHOLD,
            "consecutive_controller_failure_threshold": (
                CONSECUTIVE_CONTROLLER_FAILURE_THRESHOLD
            ),
            "in_flight_worker_interrupted": False,
            "remote_evidence_deleted": False,
            "one_time_exact_resume_authorization": True,
        },
        "secret_material_recorded": False,
    }
    payload = {"recovery_id": sha256_object(core), **core}
    destination = resolve_repo_path(output_path)
    _atomic_write_json(destination, payload, mode=0o600)
    _write_sidecar(destination)
    return payload


def _circuit_recovery_gate(
    *,
    path_value: str | Path,
    snapshot: MonitorSnapshot,
    jobs_index_path: str | Path,
) -> dict[str, Any]:
    path = resolve_repo_path(path_value)
    if not path.is_file():
        return {"status": "missing", "path": _display_path(path), "sha256": None}
    if path.is_symlink() or not _sidecar_valid(path):
        return {"status": "fail", "path": _display_path(path), "sha256": sha256_file(path)}
    payload = _load_optional_object(path)
    if payload is None:
        return {"status": "fail", "path": _display_path(path), "sha256": sha256_file(path)}
    core = dict(payload)
    recovery_id = str(core.pop("recovery_id", ""))
    trigger = dict(payload.get("trigger") or {})
    immutable = dict(payload.get("immutable_inputs") or {})
    validation = dict(payload.get("validation") or {})
    authorization = dict(payload.get("authorization") or {})
    policy = dict(payload.get("policy") or {})
    circuit = dict(snapshot.progress.get("circuit_breaker") or {})
    jobs, index, index_path = load_full_jobs(jobs_index_path)
    terminal_slots = sorted(
        audit.record_slot_id for audit in snapshot.audits if audit.state == "in_progress"
    )
    issues_by_slot = {
        str(issue["record_slot_id"]): True for issue in snapshot.issues
    }
    canary_path = str(dict(validation.get("trace_heavy_canary") or {}).get("path") or "")
    credential_canary_path = str(
        dict(validation.get("credential_recovery_canary") or {}).get("path") or ""
    )
    junit_path = str(dict(validation.get("targeted_tests") or {}).get("path") or "")
    canary = _trace_heavy_recovery_canary_gate(canary_path) if canary_path else {"status": "fail"}
    credential_canary = (
        _remote_retention_canary_gate(credential_canary_path)
        if credential_canary_path
        else {"status": "fail"}
    )
    junit = _junit_gate(junit_path) if junit_path else {"status": "fail"}
    authorized_issue_ids = sorted(
        str(issue["issue_id"])
        for issue in snapshot.issues
        if str(issue["record_slot_id"]) in terminal_slots
    )
    quiescence = dict(payload.get("quiescence") or {})
    immediate_classes = set(circuit.get("immediate_classes_observed") or [])
    credential_recovery = immediate_classes == {"credential"}
    expected_recovered_agents = (
        sorted(
            {
                str(issue["agent_id"])
                for issue in snapshot.issues
                if issue.get("circuit_class") == "credential"
            }
        )
        if credential_recovery
        else list(circuit.get("tripped_lanes") or [])
    )
    circuit_recoverable = bool(
        (not immediate_classes and circuit.get("tripped_lanes"))
        or (
            credential_recovery
            and expected_recovered_agents
            and credential_canary.get("status") == "pass"
        )
    )
    expected_runtime_hashes = {
        "webarena_har_sanitization.py": sha256_file(
            resolve_repo_path(
                "src/evidence_system/adapters/webarena_har_sanitization.py"
            )
        ),
        "webarena_remote_retention.py": sha256_file(
            resolve_repo_path(
                "src/evidence_system/adapters/webarena_remote_retention.py"
            )
        ),
    }
    quiescent_hosts = list(quiescence.get("hosts") or [])
    ok = bool(
        recovery_id
        and recovery_id == sha256_object(core)
        and payload.get("schema_version") == CIRCUIT_RECOVERY_SCHEMA
        and payload.get("status") == "pass"
        and payload.get("result_namespace") == RESULT_NAMESPACE
        and payload.get("secret_material_recorded") is False
        and circuit.get("tripped") is True
        and circuit_recoverable
        and trigger.get("progress_payload_sha256") == sha256_object(snapshot.progress)
        and trigger.get("issue_ledger_sha256") == snapshot.progress["ledger"]["sha256"]
        and trigger.get("issue_ledger_entry_count") == snapshot.progress["ledger"]["entry_count"]
        and trigger.get("circuit_fingerprint_sha256") == sha256_object(circuit)
        and trigger.get("raw_circuit_breaker") == circuit
        and trigger.get("terminal_partial_slot_ids") == terminal_slots
        and terminal_slots
        and all(slot in issues_by_slot for slot in terminal_slots)
        and immutable.get("jobs_index_path") == _display_path(index_path)
        and immutable.get("jobs_index_sha256") == sha256_file(index_path)
        and immutable.get("jobs_sha256") == index["jobs_sha256"]
        and immutable.get("job_count") == len(jobs) == EXPECTED_RECORD_SLOT_COUNT
        and immutable.get("critical_code_sha256") == _recovery_code_bindings()
        and canary.get("status") == "pass"
        and (
            not credential_recovery
            or validation.get("credential_recovery_canary") == credential_canary
        )
        and junit.get("status") == "pass"
        and validation.get("security_finding_count") == 0
        and validation.get("gold_finding_count") == 0
        and authorization.get("decision") == "clear_for_exact_resume"
        and authorization.get("issuance_confirmation")
        == CIRCUIT_RECOVERY_ISSUE_CONFIRMATION
        and authorization.get("authorized_issue_ids") == authorized_issue_ids
        and authorization.get("new_failure_streak_epoch_agent_ids")
        == expected_recovered_agents
        and quiescence.get("status") == "pass"
        and quiescence.get("active_worker_count") == 0
        and quiescence.get("expected_runtime_code_sha256")
        == expected_runtime_hashes
        and len(quiescent_hosts) == 3
        and all(
            isinstance(host, Mapping)
            and host.get("active_worker_count") == 0
            and host.get("verified_over_ssh") is True
            and host.get("runtime_code_sha256") == expected_runtime_hashes
            for host in quiescent_hosts
        )
        and policy.get("raw_circuit_history_preserved") is True
        and policy.get("issue_ledger_preserved") is True
        and policy.get("noncredential_immediate_circuit_classes_not_overridable")
        is True
        and policy.get("credential_recovery_requires_current_three_host_paid_canary")
        is True
        and policy.get("one_time_exact_resume_authorization") is True
    )
    return {
        "status": "pass" if ok else "fail",
        "path": _display_path(path),
        "sha256": sha256_file(path),
        "recovery_id": recovery_id,
        "authorized_agent_ids": list(
            authorization.get("new_failure_streak_epoch_agent_ids") or []
        ),
        "raw_circuit_history_preserved": True,
    }


def _retry_exhausted_slots_gate(
    *,
    path_value: str | Path | None,
    plan: FullSchedulePlan,
    snapshot: MonitorSnapshot,
    recovery_gate: Mapping[str, Any],
    jobs_index_path: str | Path,
) -> dict[str, Any]:
    """Validate a one-time disposition for terminal slots that must not replay.

    A recovery receipt authorizes a new lane-streak epoch, but it must not turn
    a documented, already-consumed retry (or a credential record-only outcome)
    into an implicit second paid attempt.  This signed controller receipt binds
    every excluded slot to the live terminal audit, immutable job, and exact
    circuit-recovery receipt used for the following normal resume.
    """

    if path_value in (None, ""):
        return {"status": "not_supplied", "slot_ids": []}
    path = resolve_repo_path(path_value)
    if not path.is_file() or path.is_symlink() or not _sidecar_valid(path):
        raise WebArenaRunControlError("retry-exhaustion receipt is missing or unsafe")
    payload = _load_optional_object(path)
    if payload is None:
        raise WebArenaRunControlError("retry-exhaustion receipt is invalid JSON")
    rows = payload.get("slots")
    if not isinstance(rows, list) or not rows:
        raise WebArenaRunControlError("retry-exhaustion receipt has no slot dispositions")
    index_path = resolve_repo_path(jobs_index_path)
    by_slot = {str(job["record_slot_id"]): dict(job) for job in plan.jobs}
    audits_by_slot = {audit.record_slot_id: audit for audit in snapshot.audits}
    issue_slots = {
        str(issue.get("record_slot_id") or "") for issue in snapshot.issues
    }
    allowed_dispositions = {
        "retry_exhausted_benchmark",
        "record_only_credential",
        "record_only_unrecoverable_infra",
    }
    slot_ids: list[str] = []
    rows_valid = True
    for row in rows:
        if not isinstance(row, Mapping):
            rows_valid = False
            break
        slot_id = str(row.get("record_slot_id") or "")
        job = by_slot.get(slot_id)
        audit = audits_by_slot.get(slot_id)
        if (
            job is None
            or audit is None
            or audit.reusable
            or audit.state != "in_progress"
            or slot_id not in issue_slots
            or row.get("agent_id") != job.get("agent_id")
            or row.get("task_id") != job.get("task_id")
            or row.get("job_sha256") != sha256_object(job)
            or row.get("disposition") not in allowed_dispositions
            or not isinstance(row.get("evidence"), Mapping)
        ):
            rows_valid = False
            break
        slot_ids.append(slot_id)
    recovery_id = str(recovery_gate.get("recovery_id") or "")
    ok = bool(
        payload.get("schema_version") == RETRY_EXHAUSTION_SCHEMA
        and payload.get("status") == "pass"
        and payload.get("result_namespace") == RESULT_NAMESPACE
        and payload.get("jobs_index_sha256") == sha256_file(index_path)
        and payload.get("circuit_recovery_id") == recovery_id
        and payload.get("circuit_recovery_receipt_sha256")
        == recovery_gate.get("sha256")
        and payload.get("secret_material_recorded") is False
        and rows_valid
        and slot_ids == sorted(slot_ids)
        and len(slot_ids) == len(set(slot_ids))
    )
    if not ok:
        raise WebArenaRunControlError("retry-exhaustion receipt does not match live terminal slots")
    return {
        "status": "pass",
        "path": _display_path(path),
        "sha256": sha256_file(path),
        "slot_ids": slot_ids,
    }


@_single_full_controller
def execute_resumable_full_schedule(
    plan: FullSchedulePlan,
    *,
    ssh_key_path: str | Path,
    confirm_paid_full: str,
    jobs_index_path: str | Path = DEFAULT_JOBS_INDEX,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    source_bundle_path: str | Path = DEFAULT_SOURCE_BUNDLE,
    agents_config_path: str | Path = DEFAULT_AGENTS_CONFIG,
    dotenv_path: str | Path = ".env",
    site_lock_path: str | Path = DEFAULT_SITE_LOCK,
    circuit_recovery_receipt_path: str | Path = DEFAULT_CIRCUIT_RECOVERY_RECEIPT,
    confirm_circuit_recovery: str = "",
    retry_exhausted_receipt_path: str | Path | None = None,
    adapter_planner: Callable[..., dict[str, Any]] | None = None,
    adapter_executor: Callable[..., dict[str, Any]] | None = None,
    adapter_reconciler: Callable[..., dict[str, Any]] | None = None,
    progress_callback: Callable[[Mapping[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Execute/resume three sequential lanes after an exact paid confirmation.

    Existing slots are reused only when :func:`audit_slot` verifies all frozen
    job bindings, reset semantics, HAR/trace/evaluator artifacts, and manifest
    hashes.  Isolated infrastructure failures are recorded and the affected
    lane continues.  Four consecutive infra or post-run audit failures in one
    lane open the shared circuit between slots.  Credential/storage/systemic
    issues remain immediate fail-closed classes, while controller/reset
    failures trip after three consecutive slots.  A canonical slot resets that
    lane's observed failure streak.  In-flight calls are never killed by this
    controller.
    """

    if confirm_paid_full != PAID_FULL_CONFIRMATION:
        raise WebArenaRunControlError(
            f"paid full execution requires exact confirmation {PAID_FULL_CONFIRMATION}"
        )
    initial = monitor_namespace(
        mode="full",
        index_path=jobs_index_path,
        site_lock_path=site_lock_path,
        ssh_key_path=ssh_key_path,
    )
    acceptance = build_full_run_control_acceptance(
        plan=plan,
        jobs_index_path=jobs_index_path,
        snapshot=initial,
        circuit_recovery_receipt_path=circuit_recovery_receipt_path,
        dry_run=False,
    )
    if acceptance["formal_paid_launch_ready"] is not True:
        raise WebArenaRunControlError(
            "paid full launch gates are not all pass; pilot/storage/credential/"
            "pilot-budget-and-capacity/circuit must be clear"
        )
    raw_circuit_open = initial.progress["circuit_breaker"]["tripped"] is True
    recovery_gate = _circuit_recovery_gate(
        path_value=circuit_recovery_receipt_path,
        snapshot=initial,
        jobs_index_path=jobs_index_path,
    )
    recovered_agents: set[str] = set()
    retry_exhausted_slots: set[str] = set()
    if raw_circuit_open:
        if recovery_gate["status"] != "pass":
            raise WebArenaRunControlError("existing monitor evidence has an open circuit")
        expected_recovery_confirmation = (
            CIRCUIT_RECOVERY_CONFIRMATION_PREFIX + str(recovery_gate["recovery_id"])
        )
        if confirm_circuit_recovery != expected_recovery_confirmation:
            raise WebArenaRunControlError(
                "exact circuit-recovery execution confirmation is required"
            )
        live_quiescence = _live_quiescence(
            jobs=plan.jobs,
            ssh_key_path=ssh_key_path,
            site_lock_path=site_lock_path,
        )
        if live_quiescence["status"] != "pass":
            raise WebArenaRunControlError(
                "circuit recovery cannot start while a VPS worker is active"
            )
        recovered_agents = set(recovery_gate["authorized_agent_ids"])
        retry_exhausted = _retry_exhausted_slots_gate(
            path_value=retry_exhausted_receipt_path,
            plan=plan,
            snapshot=initial,
            recovery_gate=recovery_gate,
            jobs_index_path=jobs_index_path,
        )
        retry_exhausted_slots = set(retry_exhausted["slot_ids"])
    elif retry_exhausted_receipt_path not in (None, ""):
        raise WebArenaRunControlError(
            "retry-exhaustion receipt is valid only with an open recovered circuit"
        )

    real_adapter = import_module("evidence_system.adapters.webarena_verified")
    real_planner = adapter_planner or getattr(real_adapter, "plan_smoke_execution")
    real_executor = adapter_executor or getattr(real_adapter, "execute_smoke_job")
    real_reconciler = adapter_reconciler or getattr(
        real_adapter, "reconcile_completed_remote_slot"
    )
    reusable = set(initial.reusable_slot_ids)
    deferred_post_run_slots = {
        audit.record_slot_id
        for audit in initial.audits
        if not audit.reusable
        and any(
            issue.get("signature") == "post_run_audit_deferred_for_full_sweep"
            for issue in audit.issues
        )
    }
    # A restart must not turn immutable issue-ledger entries into outcome-based
    # paid reruns.  Skip every previously attempted slot that already has a
    # terminal issue.  The only exception is the exact tail named by a valid
    # circuit-recovery receipt; those slots form a fail-closed recovery prelude
    # before any lane can resume new work.
    record_only_issue_slots = {
        audit.record_slot_id
        for audit in initial.audits
        if not audit.reusable and bool(audit.issues)
    }
    record_only_issue_slots.update(
        str(issue["record_slot_id"])
        for issue in initial.issues
        if str(issue.get("record_slot_id") or "")
    )
    record_only_issue_slots.difference_update(deferred_post_run_slots)
    retryable_controller_issue_ids = _retryable_controller_issue_ids(
        audits=initial.audits,
        issues=initial.issues,
    )
    retryable_controller_slots = {
        str(issue["record_slot_id"])
        for issue in initial.issues
        if str(issue["issue_id"]) in retryable_controller_issue_ids
    }
    # These ledger entries describe controller failures before any remote slot
    # evidence or paid runtime existed.  Preserve the entries, but do not let
    # their presence make resume skip the case that was never run.
    record_only_issue_slots.difference_update(retryable_controller_slots)
    state_lock = threading.Lock()
    task_id_by_slot = {
        str(job["record_slot_id"]): int(job["task_id"]) for job in plan.jobs
    }
    agent_id_by_slot = {
        str(job["record_slot_id"]): str(job["agent_id"]) for job in plan.jobs
    }
    initial_streaks = {agent_id: [] for agent_id in EXPECTED_AGENT_IDS}
    for item in initial.progress["circuit_breaker"].get(
        "consecutive_lane_failure_streaks", []
    ):
        initial_streaks[str(item["agent_id"])] = list(
            item.get("record_slot_ids") or []
        )
    recovery_prelude_slot_ids = tuple(
        slot_id
        for agent_id in EXPECTED_AGENT_IDS
        if agent_id in recovered_agents
        for slot_id in initial_streaks[agent_id]
        if agent_id_by_slot.get(slot_id) == agent_id
        and slot_id not in retry_exhausted_slots
    )
    record_only_issue_slots.update(retry_exhausted_slots)
    record_only_issue_slots.difference_update(recovery_prelude_slot_ids)
    lane_failure_slots: dict[str, list[str]] = {
        agent_id: (
            [] if agent_id in recovered_agents else list(initial_streaks[agent_id])
        )
        for agent_id in EXPECTED_AGENT_IDS
    }
    initial_controller_streaks = {
        agent_id: [] for agent_id in EXPECTED_AGENT_IDS
    }
    for item in initial.progress["circuit_breaker"].get(
        "consecutive_controller_failure_streaks", []
    ):
        initial_controller_streaks[str(item["agent_id"])] = list(
            item.get("record_slot_ids") or []
        )
    controller_failure_slots: dict[str, list[str]] = {
        agent_id: (
            []
            if agent_id in recovered_agents
            else list(initial_controller_streaks[agent_id])
        )
        for agent_id in EXPECTED_AGENT_IDS
    }
    runtime_issues: dict[str, dict[str, Any]] = {
        str(issue["issue_id"]): dict(issue) for issue in initial.issues
    }
    circuit = threading.Event()
    execution_counts: Counter[str] = Counter()
    publish_lock = threading.Lock()

    def publish() -> MonitorSnapshot:
        # Three lanes can seal at nearly the same time.  Serialize controller
        # receipt publication so concurrent SSH audits and atomic sidecars do
        # not race one another.  This lock never covers paid runtime work.
        with publish_lock:
            snapshot = monitor_namespace(
                mode="full",
                index_path=jobs_index_path,
                site_lock_path=site_lock_path,
                ssh_key_path=ssh_key_path,
                remote_verify_files=False,
            )
            if progress_callback is not None:
                progress_callback(snapshot.progress)
            return snapshot

    def record_issue(issue: dict[str, Any]) -> None:
        with state_lock:
            runtime_issues.setdefault(str(issue["issue_id"]), issue)
            _merge_runtime_issue_into_ledger(
                issue,
                namespace=RESULT_NAMESPACE,
                jobs_index_path=jobs_index_path,
                site_lock_path=site_lock_path,
            )
            circuit_class = str(issue["circuit_class"])
            agent_id = str(issue["agent_id"])
            slot_id = str(issue["record_slot_id"])
            if _is_controller_failure_issue(issue):
                if slot_id not in controller_failure_slots[agent_id]:
                    controller_failure_slots[agent_id].append(slot_id)
                if (
                    len(controller_failure_slots[agent_id])
                    >= CONSECUTIVE_CONTROLLER_FAILURE_THRESHOLD
                ):
                    circuit.set()
            elif circuit_class == "infra":
                # A paid/runtime case issue proves the controller reached the
                # worker, so it also breaks any controller-preflight streak.
                controller_failure_slots[agent_id] = []
                if slot_id not in lane_failure_slots[agent_id]:
                    lane_failure_slots[agent_id].append(slot_id)
                if (
                    len(lane_failure_slots[agent_id])
                    >= CONSECUTIVE_LANE_FAILURE_THRESHOLD
                ):
                    circuit.set()
            elif circuit_class in IMMEDIATE_CIRCUIT_CLASSES:
                circuit.set()

    def record_canonical_slot(job: Mapping[str, Any]) -> None:
        with state_lock:
            agent_id = str(job["agent_id"])
            canonical_task_id = int(job["task_id"])
            controller_failure_slots[agent_id] = []
            lane_failure_slots[agent_id] = [
                slot_id
                for slot_id in lane_failure_slots[agent_id]
                if task_id_by_slot[slot_id] > canonical_task_id
            ]

    def publish_best_effort(job: Mapping[str, Any]) -> MonitorSnapshot | None:
        """Do not terminate paid lanes for an isolated progress-audit outage."""

        try:
            return publish()
        except Exception as exc:
            issue = _issue(
                job,
                classification="infra",
                circuit_class="none",
                signature="controller_progress_publish_deferred",
                summary="controller progress publication is deferred until the next slot",
                evidence_paths=(),
                details={"exception_type": type(exc).__name__},
            )
            record_issue(issue)
            with state_lock:
                execution_counts["progress_publish_deferred"] += 1
            return None

    def wrapped_planner(job: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        slot_id = str(job["record_slot_id"])
        if circuit.is_set():
            raise WebArenaRunControlError("run-control circuit is open")
        if slot_id in reusable:
            return {
                "status": "runnable",
                "runner_command": "controller-canonical-reuse-no-command",
                "run_control_reuse": True,
            }
        if slot_id in deferred_post_run_slots:
            # Build the normal immutable plan so reconciliation retains the
            # exact route, remote root, and secret-name bindings.  The worker
            # command is never invoked by the reconciliation executor.
            planned = dict(real_planner(job, **kwargs))
            if planned.get("status") != "runnable":
                raise WebArenaRunControlError(
                    f"completed slot {slot_id} cannot build its seal-only plan"
                )
            planned["run_control_deferred_post_run_audit"] = True
            return planned
        if slot_id in record_only_issue_slots:
            return {
                "status": "runnable",
                "runner_command": "controller-record-only-issue-no-command",
                "run_control_record_only_issue": True,
            }
        try:
            planned = dict(real_planner(job, **kwargs))
        except Exception as exc:
            issue = _classify_runtime_exception(
                job,
                exc,
                failure_stage="planner",
            )
            record_issue(issue)
            if circuit.is_set():
                raise WebArenaRunControlError(
                    f"run-control circuit opened at {slot_id}"
                ) from exc
            return {
                "status": "runnable",
                "runner_command": "controller-isolated-planner-issue-no-command",
                "run_control_isolated_issue": issue["issue_id"],
            }
        if planned.get("status") != "runnable":
            issue = _classify_runtime_text(
                job,
                str(planned.get("blocking_reason") or "planner not runnable"),
                evidence_paths=(),
                details={"failure_stage": "planner"},
            )
            record_issue(issue)
            if circuit.is_set():
                raise WebArenaRunControlError(
                    f"run-control circuit opened at {slot_id}"
                )
            return {
                "status": "runnable",
                "runner_command": "controller-isolated-planner-issue-no-command",
                "run_control_isolated_issue": issue["issue_id"],
            }
        return planned

    def wrapped_executor(
        job: dict[str, Any],
        *,
        execution_plan: Mapping[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        slot_id = str(job["record_slot_id"])
        if execution_plan.get("run_control_reuse") is True:
            with state_lock:
                execution_counts["reused"] += 1
            record_canonical_slot(job)
            return {
                "status": "completed",
                "skipped_existing": True,
                "record_slot_id": slot_id,
            }
        if execution_plan.get("run_control_deferred_post_run_audit") is True:
            try:
                result = dict(
                    real_reconciler(
                        job,
                        execution_plan=dict(execution_plan),
                        **kwargs,
                    )
                )
            except Exception as exc:
                issue = _classify_runtime_exception(
                    job,
                    exc,
                    failure_stage="post_run_seal_reconciliation",
                )
                record_issue(issue)
                with state_lock:
                    execution_counts["post_run_reconciliation_issue"] += 1
                return {
                    "status": "completed",
                    "post_run_reconciliation_issue": issue["issue_id"],
                    "record_slot_id": slot_id,
                }
            if result.get("status") != "completed":
                raise WebArenaRunControlError(
                    f"post-run reconciliation did not complete for {slot_id}"
                )
            reusable.add(slot_id)
            record_canonical_slot(job)
            with state_lock:
                execution_counts["post_run_reconciled"] += 1
            publish_best_effort(job)
            return result
        if execution_plan.get("run_control_record_only_issue") is True:
            with state_lock:
                execution_counts["record_only_issue_skipped"] += 1
            return {
                "status": "completed",
                "record_only_issue_preserved": True,
                "record_slot_id": slot_id,
            }
        isolated = execution_plan.get("run_control_isolated_issue")
        if isolated:
            with state_lock:
                execution_counts["isolated_issue_skipped"] += 1
            return {
                "status": "completed",
                "run_control_issue_id": isolated,
                "record_slot_id": slot_id,
            }
        try:
            result = dict(
                real_executor(job, execution_plan=dict(execution_plan), **kwargs)
            )
        except Exception as exc:
            evidence_paths = _existing_slot_evidence_paths(job)
            failure_stage = (
                "adapter_execution_after_slot_evidence"
                if evidence_paths or getattr(exc, "remote_runtime_observed", False)
                else "adapter_execution_before_slot_evidence"
            )
            issue = _classify_runtime_exception(
                job,
                exc,
                failure_stage=failure_stage,
            )
            record_issue(issue)
            with state_lock:
                execution_counts["runtime_issue"] += 1
            if circuit.is_set():
                raise WebArenaRunControlError(
                    f"run-control circuit opened at {slot_id}"
                ) from exc
            return {
                "status": "completed",
                "run_control_issue_id": issue["issue_id"],
                "record_slot_id": slot_id,
            }
        if result.get("status") != "completed":
            evidence_paths = _existing_slot_evidence_paths(job)
            issue = _classify_runtime_text(
                job,
                str(result.get("status") or "non-completed adapter result"),
                evidence_paths=evidence_paths,
                details={
                    "failure_stage": (
                        "adapter_execution_after_slot_evidence"
                        if evidence_paths
                        else "adapter_execution_before_slot_evidence"
                    )
                },
            )
            record_issue(issue)
            with state_lock:
                execution_counts["runtime_issue"] += 1
            if circuit.is_set():
                raise WebArenaRunControlError(
                    f"run-control circuit opened at {slot_id}"
                )
            return {
                "status": "completed",
                "run_control_issue_id": issue["issue_id"],
                "record_slot_id": slot_id,
            }

        try:
            site_lock = load_site_lock(resolve_repo_path(site_lock_path))
            audited = audit_remote_slot(
                job, ssh_key_path=ssh_key_path, site_lock=site_lock
            )
        except Exception as exc:
            # The paid runtime returned completed.  A controller-side SSH or
            # verifier exception is therefore deferred post-run work; it must
            # not repeat the case or terminate the other two lanes.
            issue = _issue(
                job,
                classification="infra",
                circuit_class="none",
                signature="post_run_remote_audit_deferred_for_full_sweep",
                summary="paid runtime completed; remote audit is deferred to batch reconciliation",
                evidence_paths=(),
                details={"exception_type": type(exc).__name__},
            )
            record_issue(issue)
            with state_lock:
                execution_counts["post_run_remote_audit_deferred"] += 1
            publish_best_effort(job)
            return result
        for issue in audited.issues:
            record_issue(dict(issue))
        if not audited.reusable:
            if not audited.issues:
                record_issue(
                    _issue(
                        job,
                        classification="infra",
                        circuit_class="infra",
                        signature="post_run_slot_not_canonical",
                        summary="completed adapter result is not a reusable canonical slot",
                        evidence_paths=_existing_slot_evidence_paths(job),
                    )
                )
            if circuit.is_set():
                raise WebArenaRunControlError(
                    f"run-control circuit opened after {slot_id}"
                )
        else:
            reusable.add(slot_id)
            with state_lock:
                execution_counts["executed_canonical"] += 1
            record_canonical_slot(job)
        publish_best_effort(job)
        return result

    try:
        execute_full_schedule(
            plan,
            ssh_key_path=ssh_key_path,
            manifest_path=manifest_path,
            source_bundle_path=source_bundle_path,
            agents_config_path=agents_config_path,
            dotenv_path=dotenv_path,
            site_lock_path=site_lock_path,
            adapter_planner=wrapped_planner,
            adapter_executor=wrapped_executor,
            recovery_prelude_slot_ids=recovery_prelude_slot_ids,
        )
    except Exception:
        try:
            publish()
        except Exception:
            pass
        raise
    final_snapshot = publish()
    counts = dict(final_snapshot.progress["counts"])
    return {
        "schema_version": "webarena_verified_resumable_full_execution/v1",
        "status": (
            "completed"
            if counts["canonical_reusable"] == EXPECTED_RECORD_SLOT_COUNT
            else "partial_resumable"
        ),
        "result_namespace": RESULT_NAMESPACE,
        "expected_slots": EXPECTED_RECORD_SLOT_COUNT,
        "canonical_reusable_slots": counts["canonical_reusable"],
        "execution_counts": dict(sorted(execution_counts.items())),
        "circuit_breaker": final_snapshot.progress["circuit_breaker"],
        "case_issue_ledger_sha256": final_snapshot.progress["ledger"]["sha256"],
        "circuit_recovery_used": raw_circuit_open,
        "circuit_recovery_id": (
            recovery_gate.get("recovery_id") if raw_circuit_open else None
        ),
        "recovery_prelude_slot_ids": list(recovery_prelude_slot_ids),
        "retry_exhausted_slot_ids": sorted(retry_exhausted_slots),
        "raw_circuit_history_preserved": True,
        "rerun_triggered_by_monitor": False,
        "in_flight_worker_interrupted": False,
        "score_mutation_performed": False,
    }


def _is_retryable_controller_issue(
    issue: Mapping[str, Any], audit: SlotAudit | None
) -> bool:
    """Identify a controller-only failure that never reached slot evidence.

    The raw issue remains immutable.  A pending remote slot, empty evidence,
    and an infra-only controller/runtime signature jointly prove that the case
    itself was never executed and is eligible for the exact full sweep.
    """

    return bool(
        audit is not None
        and audit.state == "pending"
        and issue.get("classification") == "infra"
        and issue.get("circuit_class") == "infra"
        and not list(issue.get("evidence") or [])
        and issue.get("signature")
        in {
            "controller_preflight_failure",
            "transient_transport_or_worker_failure",
            "unclassified_runtime_failure",
        }
    )


def _is_controller_failure_issue(issue: Mapping[str, Any]) -> bool:
    """Return whether a new issue belongs to the short controller circuit."""

    details = issue.get("details")
    failure_stage = (
        str(details.get("failure_stage") or "")
        if isinstance(details, Mapping)
        else ""
    )
    return bool(
        issue.get("circuit_class") in {"infra", "reset"}
        and (
            issue.get("circuit_class") == "reset"
            or issue.get("signature") == "controller_preflight_failure"
            # An adapter-execution exception can follow a remote launch even
            # where the controller cannot yet read slot evidence.  Count it
            # against the paid lane threshold, not the shorter preflight
            # threshold, so it cannot be mistaken for a no-runtime controller
            # failure.
            or failure_stage == "planner"
        )
    )


def _retryable_controller_issue_ids(
    *,
    audits: Sequence[SlotAudit],
    issues: Sequence[Mapping[str, Any]],
) -> set[str]:
    audits_by_slot = {audit.record_slot_id: audit for audit in audits}
    return {
        str(issue["issue_id"])
        for issue in issues
        if _is_retryable_controller_issue(
            issue, audits_by_slot.get(str(issue["record_slot_id"]))
        )
    }


def _ordered_task_ranges(values: Sequence[int]) -> list[dict[str, int]]:
    ranges: list[list[int]] = []
    for value in sorted(set(values)):
        if not ranges or value > ranges[-1][1] + 1:
            ranges.append([value, value])
        else:
            ranges[-1][1] = value
    return [
        {"first_task_id": first, "last_task_id": last, "count": last - first + 1}
        for first, last in ranges
    ]


def _controller_retryable_issue_receipt(
    *,
    namespace: str,
    audits: Sequence[SlotAudit],
    issues: Sequence[Mapping[str, Any]],
    ledger_path: Path,
    ledger_sha256: str,
) -> dict[str, Any]:
    retryable_ids = _retryable_controller_issue_ids(audits=audits, issues=issues)
    rows = [
        issue for issue in issues if str(issue["issue_id"]) in retryable_ids
    ]
    slot_ids = sorted({str(issue["record_slot_id"]) for issue in rows})
    per_lane = []
    for agent_id in EXPECTED_AGENT_IDS:
        lane_rows = [issue for issue in rows if issue.get("agent_id") == agent_id]
        task_ids = [int(issue["task_id"]) for issue in lane_rows]
        per_lane.append(
            {
                "agent_id": agent_id,
                "issue_count": len(lane_rows),
                "record_slot_count": len(
                    {str(issue["record_slot_id"]) for issue in lane_rows}
                ),
                "task_ranges": _ordered_task_ranges(task_ids),
            }
        )
    return {
        "schema_version": "webarena_verified_controller_retryable_issues/v1",
        "status": "pass",
        "result_namespace": namespace,
        "source_issue_ledger": {
            "path": _display_path(ledger_path),
            "sha256": ledger_sha256,
            "entry_count": len(issues),
            "raw_ledger_preserved": True,
        },
        "classification_policy": {
            "remote_audit_state": "pending",
            "classification": "infra",
            "circuit_class": "infra",
            "evidence_count": 0,
            "allowed_signatures": [
                "controller_preflight_failure",
                "transient_transport_or_worker_failure",
                "unclassified_runtime_failure",
            ],
            "meaning": "controller_failed_before_slot_evidence_or_paid_runtime",
        },
        "issue_count": len(rows),
        "record_slot_count": len(slot_ids),
        "issue_ids": sorted(retryable_ids),
        "record_slot_ids": slot_ids,
        "per_lane": per_lane,
        "resume_policy": {
            "eligible_for_exact_full_sweep": True,
            "paid_rerun": False,
            "raw_issue_deleted": False,
            "score_changed": False,
            "remote_evidence_deleted": False,
        },
        "secret_material_recorded": False,
    }


def _progress_payload(
    *,
    mode: str,
    namespace: str,
    jobs: Sequence[Mapping[str, Any]],
    audits: Sequence[SlotAudit],
    issues: Sequence[Mapping[str, Any]],
    schedule_binding: Mapping[str, Any],
    source_jobs_index_path: Path,
    source_jobs_index_sha256: str,
    ledger_path: Path,
    ledger_sha256: str,
    controller_retryable_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    state_counts = Counter(audit.state for audit in audits)
    classification_counts = Counter(str(issue["classification"]) for issue in issues)
    circuit_counts = Counter(str(issue["circuit_class"]) for issue in issues)
    immediate = sorted(
        circuit_class
        for circuit_class in IMMEDIATE_CIRCUIT_CLASSES
        if circuit_counts[circuit_class] > 0
    )
    lane_failure_streaks = _consecutive_lane_failure_streaks(
        jobs=jobs,
        audits=audits,
        issues=issues,
    )
    controller_failure_streaks = _consecutive_controller_failure_streaks(
        jobs=jobs,
        audits=audits,
        issues=issues,
    )
    tripped_runtime_lanes = [
        streak
        for streak in lane_failure_streaks
        if streak["count"] >= CONSECUTIVE_LANE_FAILURE_THRESHOLD
    ]
    tripped_controller_lanes = [
        streak
        for streak in controller_failure_streaks
        if streak["count"] >= CONSECUTIVE_CONTROLLER_FAILURE_THRESHOLD
    ]
    tripped_lane_ids = sorted(
        {
            str(item["agent_id"])
            for item in (*tripped_runtime_lanes, *tripped_controller_lanes)
        }
    )
    semantic_case_review = _semantic_review_progress(audits, issues)
    per_lane: list[dict[str, Any]] = []
    for agent_id in EXPECTED_AGENT_IDS:
        lane = [
            audit
            for job, audit in zip(jobs, audits, strict=True)
            if job["agent_id"] == agent_id
        ]
        completed_tasks = [
            int(job["task_id"])
            for job, audit in zip(jobs, audits, strict=True)
            if job["agent_id"] == agent_id and audit.reusable
        ]
        per_lane.append(
            {
                "agent_id": agent_id,
                "expected": len(lane),
                "canonical_reusable": sum(item.reusable for item in lane),
                "pending": sum(item.state == "pending" for item in lane),
                "in_progress": sum(item.state == "in_progress" for item in lane),
                "settled_invalid": sum(
                    item.state == "settled_invalid" for item in lane
                ),
                "highest_canonical_task_id": max(completed_tasks)
                if completed_tasks
                else None,
                "sequential_lane": True,
            }
        )
    return {
        "schema_version": PROGRESS_SCHEMA,
        "status": "pass",
        "monitor_mode": mode,
        "result_namespace": namespace,
        "schedule_binding": dict(schedule_binding),
        "source_full_jobs_index": {
            "path": _display_path(source_jobs_index_path),
            "sha256": source_jobs_index_sha256,
            "not_the_monitored_schedule_when_mode_is_pilot": mode == "pilot",
        },
        "counts": {
            "expected": len(jobs),
            "canonical_reusable": state_counts["canonical_reusable"],
            "pending": state_counts["pending"],
            "in_progress": state_counts["in_progress"],
            "settled_invalid": state_counts["settled_invalid"],
            "issues": len(issues),
        },
        "lanes": per_lane,
        "issue_classification_counts": dict(sorted(classification_counts.items())),
        "ledger": {
            "path": _display_path(ledger_path),
            "sha256": ledger_sha256,
            "entry_count": len(issues),
            "idempotent_issue_id": True,
        },
        "controller_induced_retryable_issues": dict(
            controller_retryable_receipt
        ),
        "circuit_breaker": {
            "tripped": bool(
                immediate or tripped_runtime_lanes or tripped_controller_lanes
            ),
            "immediate_classes_observed": immediate,
            "consecutive_lane_failure_streaks": lane_failure_streaks,
            "consecutive_controller_failure_streaks": (
                controller_failure_streaks
            ),
            "tripped_lanes": tripped_lane_ids,
            "consecutive_lane_failure_threshold": (
                CONSECUTIVE_LANE_FAILURE_THRESHOLD
            ),
            "consecutive_controller_failure_threshold": (
                CONSECUTIVE_CONTROLLER_FAILURE_THRESHOLD
            ),
            "advisory_to_executor_only": True,
            "monitor_stopped_or_killed_worker": False,
        },
        "semantic_case_review": semantic_case_review,
        "monitor_guarantees": {
            "slot_result_trees_read_only": True,
            "slot_locks_acquired": 0,
            "workers_stopped_or_killed": 0,
            "scores_changed": 0,
            "reruns_triggered": 0,
            "issues_are_needs_review_only": True,
            "credential_values_or_hashes_recorded": False,
            "dotenv_read": False,
        },
    }


def _consecutive_lane_failure_streaks(
    *,
    jobs: Sequence[Mapping[str, Any]],
    audits: Sequence[SlotAudit],
    issues: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Return the current ordered infra-failure tail for each agent lane.

    Ledger entries are immutable historical evidence.  A slot that later
    becomes canonical therefore wins over its historical issue and resets the
    lane.  Pending or currently-running future slots neither increment nor
    clear the observed tail.
    """

    audits_by_slot = {audit.record_slot_id: audit for audit in audits}
    infra_by_slot: dict[str, list[Mapping[str, Any]]] = {}
    for issue in issues:
        if issue.get("circuit_class") != "infra":
            continue
        audit = audits_by_slot.get(str(issue["record_slot_id"]))
        if _is_retryable_controller_issue(issue, audit):
            continue
        if _is_controller_failure_issue(issue):
            continue
        infra_by_slot.setdefault(str(issue["record_slot_id"]), []).append(issue)

    streaks: list[dict[str, Any]] = []
    for agent_id in EXPECTED_AGENT_IDS:
        count = 0
        slot_ids: list[str] = []
        signatures: list[str] = []
        for job, audit in zip(jobs, audits, strict=True):
            if job.get("agent_id") != agent_id:
                continue
            slot_id = str(job["record_slot_id"])
            if audit.reusable:
                count = 0
                slot_ids = []
                signatures = []
                continue
            slot_issues = infra_by_slot.get(slot_id, [])
            if slot_issues:
                count += 1
                slot_ids.append(slot_id)
                signatures.extend(
                    sorted({str(issue["signature"]) for issue in slot_issues})
                )
                continue
            # Pending holes do not hide a later observed terminal failure.
            continue
        streaks.append(
            {
                "agent_id": agent_id,
                "count": count,
                "record_slot_ids": slot_ids,
                "signatures": sorted(set(signatures)),
            }
        )
    return streaks


def _consecutive_controller_failure_streaks(
    *,
    jobs: Sequence[Mapping[str, Any]],
    audits: Sequence[SlotAudit],
    issues: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Return each lane's current reset/controller-preflight failure tail."""

    controller_by_slot: dict[str, list[Mapping[str, Any]]] = {}
    for issue in issues:
        if _is_controller_failure_issue(issue):
            controller_by_slot.setdefault(
                str(issue["record_slot_id"]), []
            ).append(issue)

    streaks: list[dict[str, Any]] = []
    for agent_id in EXPECTED_AGENT_IDS:
        slot_ids: list[str] = []
        signatures: list[str] = []
        for job, audit in zip(jobs, audits, strict=True):
            if job.get("agent_id") != agent_id:
                continue
            slot_id = str(job["record_slot_id"])
            if audit.reusable:
                slot_ids = []
                signatures = []
                continue
            slot_issues = controller_by_slot.get(slot_id, [])
            if slot_issues:
                slot_ids.append(slot_id)
                signatures.extend(
                    sorted({str(issue["signature"]) for issue in slot_issues})
                )
                continue
            # A different terminal issue means this is not a consecutive
            # controller failure chain.  A merely pending slot is neutral.
            if audit.issues:
                slot_ids = []
                signatures = []
        streaks.append(
            {
                "agent_id": agent_id,
                "count": len(slot_ids),
                "record_slot_ids": slot_ids,
                "signatures": sorted(set(signatures)),
            }
        )
    return streaks


def _semantic_review_progress(
    audits: Sequence[SlotAudit], issues: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    receipts = [
        dict(audit.semantic_review)
        for audit in audits
        if audit.semantic_review is not None
    ]
    reviewed_by_task: dict[int, set[str]] = {}
    for receipt in receipts:
        reviewed_by_task.setdefault(int(receipt["task_id"]), set()).add(
            str(receipt["agent_id"])
        )

    semantic_issues = [
        issue
        for issue in issues
        if dict(issue.get("details") or {}).get("semantic_category")
    ]
    grouped: dict[tuple[int, str], list[Mapping[str, Any]]] = {}
    for issue in semantic_issues:
        grouped.setdefault(
            (int(issue["task_id"]), str(issue["signature"])), []
        ).append(issue)
    clusters: list[dict[str, Any]] = []
    for (task_id, signature), rows in sorted(grouped.items()):
        agent_ids = sorted({str(row["agent_id"]) for row in rows})
        if len(agent_ids) < 2:
            continue
        evidence_by_path: dict[str, dict[str, Any]] = {}
        for row in rows:
            for evidence in list(row.get("evidence") or []):
                if isinstance(evidence, Mapping) and isinstance(
                    evidence.get("path"), str
                ):
                    evidence_by_path[str(evidence["path"])] = dict(evidence)
        categories = sorted(
            {
                str(
                    dict(row.get("details") or {}).get("semantic_category") or ""
                )
                for row in rows
            }
        )
        cluster_core = {
            "schema_version": "webarena_verified_cross_agent_case_anomaly/v1",
            "task_id": task_id,
            "signature": signature,
            "semantic_categories": categories,
            "classifications": sorted(
                {str(row["classification"]) for row in rows}
            ),
            "agent_ids": agent_ids,
            "record_slot_ids": sorted({str(row["record_slot_id"]) for row in rows}),
            "issue_ids": sorted({str(row["issue_id"]) for row in rows}),
            "evidence": [evidence_by_path[key] for key in sorted(evidence_by_path)],
            "observed_in_all_three_agents": set(agent_ids) == set(EXPECTED_AGENT_IDS),
            "needs_review": True,
            "case_defect_concluded": False,
            "interrupt_requested": False,
            "score_mutation_requested": False,
            "rerun_requested": False,
        }
        clusters.append(
            {"cluster_id": sha256_object(cluster_core), **cluster_core}
        )

    category_counts = Counter(
        str(dict(issue.get("details") or {}).get("semantic_category") or "")
        for issue in semantic_issues
    )
    return {
        "schema_version": "webarena_verified_semantic_case_review_progress/v1",
        "reviewed_slot_count": len(receipts),
        "reviewed_task_count": len(reviewed_by_task),
        "tasks_reviewed_for_all_three_agents": sorted(
            task_id
            for task_id, agent_ids in reviewed_by_task.items()
            if agent_ids == set(EXPECTED_AGENT_IDS)
        ),
        "finding_count": len(semantic_issues),
        "finding_category_counts": dict(sorted(category_counts.items())),
        "cross_agent_common_anomaly_clusters": clusters,
        "review_receipts": receipts,
        "private_evaluator_payload_recorded": False,
        "semantic_findings_trip_executor_circuit": False,
        "case_defect_concluded_by_monitor": False,
        "monitor_interruption_requested": False,
        "score_mutation_requested": False,
        "rerun_requested": False,
    }


def _artifact_integrity_failure(
    manifest: Mapping[str, Any], *, root: Path
) -> str | None:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return "artifact list missing"
    root_resolved = root.resolve()
    for position, item in enumerate(artifacts):
        if not isinstance(item, Mapping):
            return f"artifact {position} is not an object"
        raw_path = item.get("path")
        if not isinstance(raw_path, str) or not raw_path:
            return f"artifact {position} path missing"
        try:
            path = resolve_repo_path(raw_path)
            path.resolve().relative_to(root_resolved)
        except (OSError, RuntimeError, ValueError):
            return f"artifact {position} path escapes slot root"
        if path.is_symlink() or (not path.is_file() and not path.is_dir()):
            return f"artifact {position} path missing or symlinked"
        try:
            actual_hash = sha256_path(path)
            actual_size = (
                path.stat().st_size
                if path.is_file()
                else sum(
                    candidate.stat().st_size
                    for candidate in path.rglob("*")
                    if candidate.is_file()
                )
            )
        except OSError:
            return f"artifact {position} could not be read"
        if item.get("sha256") != actual_hash:
            return f"artifact {position} hash mismatch"
        if item.get("size_bytes") != actual_size:
            return f"artifact {position} size mismatch"
    return None


def _reset_integrity_failure(
    receipt: Mapping[str, Any] | None,
    *,
    job: Mapping[str, Any],
    site_lock: Mapping[str, Any],
) -> str | None:
    if receipt is None:
        return "receipt is not a JSON object"
    if receipt.get("schema_version") != RESET_RECEIPT_SCHEMA:
        return "schema mismatch"
    if receipt.get("status") != "pass":
        return "status is not pass"
    expected_slot = {
        "slot_id": str(job["record_slot_id"]),
        "task_id": int(job["task_id"]),
        "agent_id": str(job["agent_id"]),
        "attempt_id": str(job["attempt_id"]),
        "seed": int(job["seed"]),
    }
    if dict(receipt.get("slot") or {}) != expected_slot:
        return "slot identity mismatch"
    expected_sites = list(job.get("task_sites") or [])
    observed_scope = list(receipt.get("reset_scope") or [])
    if (
        len(observed_scope) != len(expected_sites)
        or len(set(observed_scope)) != len(observed_scope)
        or set(observed_scope) != set(expected_sites)
    ):
        return "reset scope mismatch"
    if receipt.get("site_lock_sha256") != sha256_object(site_lock):
        return "site lock hash mismatch"
    route = dict(job.get("execution_target") or {})
    machine = dict(receipt.get("machine") or {})
    if (
        machine.get("machine_id") != route.get("server_id")
        or machine.get("ssh_host") != route.get("ssh_host")
        or machine.get("ssh_host_fingerprint")
        != route.get("ssh_host_ed25519_fingerprint")
    ):
        return "machine route mismatch"
    exclusive = dict(receipt.get("exclusive_lock") or {})
    if not exclusive.get("acquired_at") or not exclusive.get("released_at"):
        return "exclusive reset lock timestamps missing"
    if receipt.get("error") is not None or receipt.get("fail_closed") is not None:
        return "failure marker present"
    rows = receipt.get("sites")
    if not isinstance(rows, list):
        return "site rows missing or invalid"
    observed_row_sites = [
        row.get("site") for row in rows if isinstance(row, Mapping)
    ]
    if (
        len(observed_row_sites) != len(expected_sites)
        or len(set(observed_row_sites)) != len(observed_row_sites)
        or set(observed_row_sites) != set(expected_sites)
    ):
        return "site rows missing, duplicate, or outside reset scope"
    for row in rows:
        if not isinstance(row, Mapping) or row.get("ok") is not True:
            return "site row is not successful"
        site = str(row["site"])
        if row.get("image_reference") != pinned_image_reference(site_lock, site):
            return f"unpinned image for {site}"
        before = row.get("before")
        after = row.get("after")
        if not isinstance(after, Mapping):
            return f"replacement metadata missing for {site}"
        if not after.get("container_id") or after.get("running") is not True:
            return f"replacement container is not running for {site}"
        if isinstance(before, Mapping) and before.get("container_id") == after.get(
            "container_id"
        ):
            return f"container was not replaced for {site}"
        if after.get("image_id") != row.get("expected_image_id"):
            return f"replacement image ID mismatch for {site}"
        sentinels = row.get("sentinels")
        if not isinstance(sentinels, list) or not sentinels or any(
            not isinstance(check, Mapping) or check.get("ok") is not True
            for check in sentinels
        ):
            return f"sentinel failure for {site}"
    return None


def _source_and_trajectory_binding_failure(
    job: Mapping[str, Any], required: Mapping[str, Path]
) -> str | None:
    task_id = int(job["task_id"])
    packet_path = resolve_repo_path(TASK_PACKET_ROOT / str(task_id) / "case_packet.json")
    agent_input_path = resolve_repo_path(TASK_PACKET_ROOT / str(task_id) / "agent_input.json")
    packet = _load_optional_object(packet_path)
    agent_input = _load_optional_object(agent_input_path)
    official = _load_optional_object(required["official_task"])
    solver = _load_optional_object(required["solver_trace"])
    if any(value is None for value in (packet, agent_input, official, solver)):
        return "source/task/trajectory JSON missing"
    assert packet is not None
    assert agent_input is not None
    assert official is not None
    assert solver is not None
    task = packet.get("task")
    if not isinstance(task, Mapping):
        return "case packet task block missing"
    if (
        task.get("task_id") != task_id
        or task.get("revision") != int(job["task_revision"])
        or task.get("sites") != list(job.get("task_sites") or [])
        or agent_input.get("task_id") != task_id
        or official.get("task_id") != task_id
        or official.get("revision") != int(job["task_revision"])
        or official.get("sites") != list(job.get("task_sites") or [])
        or official.get("intent") != agent_input.get("intent")
        or official.get("start_url")
        != " |AND| ".join(list(agent_input.get("start_urls") or []))
        or solver.get("task_id") != task_id
        or solver.get("task_revision") != int(job["task_revision"])
    ):
        return "task/revision/sites/instruction/start URL mismatch"
    steps = solver.get("steps")
    if not isinstance(steps, list) or not steps:
        return "solver trajectory has no steps"
    for position, step in enumerate(steps):
        if not isinstance(step, Mapping) or step.get("step") != position:
            return "solver trajectory step order is invalid"
        if not isinstance(step.get("page_url_before"), str):
            return "solver trajectory page URL is missing"
        if not isinstance(step.get("action"), Mapping):
            return "solver trajectory action is missing"
    return None


def _semantic_case_review(
    job: Mapping[str, Any], required: Mapping[str, Path]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Review one settled slot without exposing evaluator-private values.

    These observations are deliberately advisory.  Even an infrastructure-like
    semantic observation uses ``circuit_class=none``: structural/runtime checks
    own the executor circuit, while this layer only records material for human
    review and cross-agent clustering.
    """

    task_id = int(job["task_id"])
    packet_root = resolve_repo_path(TASK_PACKET_ROOT / str(task_id))
    packet_path = packet_root / "case_packet.json"
    packet_md_path = packet_root / "case_packet.md"
    agent_input_path = packet_root / "agent_input.json"
    raw_task_path = packet_root / "raw_case" / "derived" / "task.json"
    tag_task_path = packet_root / "raw_case" / "derived" / "tag_task.json"
    native_root = required["solver_trace"].parent.parent
    llm_attempts_path = native_root / "llm_attempts"

    packet = _load_optional_object(packet_path) or {}
    agent_input = _load_optional_object(agent_input_path) or {}
    raw_task = _load_optional_object(raw_task_path) or {}
    official = _load_optional_object(required["official_task"]) or {}
    solver = _load_optional_object(required["solver_trace"]) or {}
    eval_result = _load_optional_object(required["eval_result"]) or {}
    agent_response = _load_optional_object(required["agent_response"]) or {}
    har = _load_optional_object(required["network_har"]) or {}
    issues: list[dict[str, Any]] = []

    def add(
        *,
        category: str,
        classification: str,
        signature: str,
        summary: str,
        evidence_paths: Sequence[Path],
        details: Mapping[str, Any] | None = None,
    ) -> None:
        issues.append(
            _issue(
                job,
                classification=classification,
                circuit_class="none",
                signature=signature,
                summary=summary,
                evidence_paths=evidence_paths,
                details={"semantic_category": category, **dict(details or {})},
            )
        )

    intent = str(agent_input.get("intent") or "")
    if not intent.strip() or len(intent.strip()) < 8:
        add(
            category="instruction_ambiguity",
            classification="potential_case_issue",
            signature="empty_or_too_short_instruction",
            summary="official instruction is empty or too short to identify a task",
            evidence_paths=(packet_md_path, packet_path, agent_input_path),
        )
    if _PLACEHOLDER_RE.search(intent):
        add(
            category="instruction_ambiguity",
            classification="potential_case_issue",
            signature="unresolved_instruction_placeholder",
            summary="locked official instruction appears to contain an unresolved placeholder",
            evidence_paths=(
                packet_md_path,
                packet_path,
                agent_input_path,
                required["official_task"],
            ),
        )

    task_block = dict(packet.get("task") or {})
    evaluator_ref = dict(packet.get("evaluator_reference") or {})
    task_type = str(task_block.get("task_type") or "")
    packet_evaluators = [
        str(value) for value in list(evaluator_ref.get("evaluator_names") or [])
    ]
    raw_evaluators = [
        row
        for row in list(raw_task.get("eval") or [])
        if isinstance(row, Mapping)
    ]
    raw_evaluator_names = [str(row.get("evaluator") or "") for row in raw_evaluators]
    result_evaluator_names = [
        str(row.get("evaluator_name") or "")
        for row in list(eval_result.get("evaluators_results") or [])
        if isinstance(row, Mapping)
    ]
    if (
        raw_evaluator_names != packet_evaluators
        or result_evaluator_names != packet_evaluators
    ):
        add(
            category="evaluator_instruction_alignment",
            classification="potential_case_issue",
            signature="official_evaluator_sequence_disagrees_with_packet",
            summary="official task, packet, and evaluator output name different evaluator sequences",
            evidence_paths=(
                packet_md_path,
                packet_path,
                raw_task_path,
                required["eval_result"],
            ),
            details={
                "packet_evaluator_count": len(packet_evaluators),
                "raw_evaluator_count": len(raw_evaluator_names),
                "result_evaluator_count": len(result_evaluator_names),
            },
        )

    response_evaluators = [
        row for row in raw_evaluators if row.get("evaluator") == "AgentResponseEvaluator"
    ]
    response_task_types = {
        str(dict(row.get("expected") or {}).get("task_type") or "").upper()
        for row in response_evaluators
    }
    if len(response_evaluators) != 1 or response_task_types != {task_type}:
        add(
            category="evaluator_instruction_alignment",
            classification="potential_case_issue",
            signature="official_response_task_type_disagrees_with_packet",
            summary="official response evaluator task type disagrees with the public task type",
            evidence_paths=(packet_md_path, packet_path, raw_task_path),
            details={
                "response_evaluator_count": len(response_evaluators),
                "distinct_expected_task_type_count": len(response_task_types),
            },
        )
    elif not _response_schema_matches_task_type(response_evaluators[0], task_type):
        add(
            category="evaluator_instruction_alignment",
            classification="potential_case_issue",
            signature="official_response_schema_disagrees_with_task_type",
            summary="official result schema does not match retrieve versus action semantics",
            evidence_paths=(packet_md_path, packet_path, raw_task_path),
        )

    allowed_agent_fields = {
        "intent",
        "intent_template_id",
        "sites",
        "start_urls",
        "task_id",
    }
    leakage = dict(packet.get("leakage_control") or {})
    prompt_leakage_markers = _prompt_private_marker_hits(llm_attempts_path)
    private_official_fields = sorted(
        key
        for key in official
        if str(key).lower()
        in {"eval", "expected", "gold", "reference_answer", "private_dataset_ref"}
    )
    if (
        set(agent_input) != allowed_agent_fields
        or leakage.get("answer_payload_embedded") is not False
        or leakage.get("evaluator_payload_embedded") is not False
        or leakage.get("model_receives_only_agent_input_json") is not True
        or private_official_fields
        or prompt_leakage_markers
    ):
        add(
            category="answer_or_evaluator_leakage",
            classification="systemic",
            signature="model_visible_boundary_may_include_private_evaluator_material",
            summary="a model-visible boundary contains or references evaluator-private material",
            evidence_paths=(
                packet_path,
                agent_input_path,
                required["official_task"],
                llm_attempts_path,
            ),
            details={
                "agent_input_field_count": len(agent_input),
                "unexpected_agent_input_field_count": len(
                    set(agent_input) - allowed_agent_fields
                ),
                "private_official_field_count": len(private_official_fields),
                "prompt_private_marker_count": len(prompt_leakage_markers),
            },
        )

    start_urls = [str(value) for value in list(agent_input.get("start_urls") or [])]
    har_summary = _har_review_summary(har, start_urls=start_urls)
    for row in har_summary["start_url_observations"]:
        statuses = list(row["response_statuses"])
        if row["matching_request_count"] == 0:
            add(
                category="start_page_reachability",
                classification="potential_case_issue",
                signature="locked_start_url_not_observed_in_har",
                summary="a locked start URL was never observed in the canonical network trace",
                evidence_paths=(agent_input_path, required["network_har"]),
            )
        if any(status in {404, 410} for status in statuses):
            add(
                category="start_page_reachability",
                classification="potential_case_issue",
                signature="locked_start_url_not_found",
                summary="a locked task start URL returned HTTP 404/410",
                evidence_paths=(agent_input_path, required["network_har"]),
            )
        if any(status in {401, 403} for status in statuses):
            add(
                category="initial_state_or_session_conflict",
                classification="infra",
                signature="locked_start_url_access_denied",
                summary="a locked start page returned an authentication or authorization denial",
                evidence_paths=(
                    agent_input_path,
                    required["reset_receipt"],
                    required["network_har"],
                ),
            )
        if any(status <= 0 or status >= 500 for status in statuses):
            add(
                category="site_dependency_anomaly",
                classification="infra",
                signature="task_start_url_transport_or_server_failure",
                summary="a locked start page had a transport failure or HTTP 5xx response",
                evidence_paths=(
                    agent_input_path,
                    required["reset_receipt"],
                    required["network_har"],
                ),
            )

    steps = [
        step for step in list(solver.get("steps") or []) if isinstance(step, Mapping)
    ]
    trace_summary = _solver_trace_review_summary(steps, start_urls=start_urls)
    if trace_summary["first_page_class"] == "unexpected_login_page":
        add(
            category="initial_state_or_session_conflict",
            classification="infra",
            signature="unexpected_login_page_after_verified_reset",
            summary="the first browser state was an unexpected login page after reset",
            evidence_paths=(
                agent_input_path,
                required["reset_receipt"],
                required["solver_trace"],
                required["network_har"],
            ),
        )
    if trace_summary["first_page_class"] in {"blank", "missing"}:
        add(
            category="start_page_reachability",
            classification="infra",
            signature="browser_did_not_reach_a_start_page",
            summary="the first browser state did not contain a reachable task page",
            evidence_paths=(
                agent_input_path,
                required["solver_trace"],
                required["playwright_trace"],
            ),
        )
    if trace_summary["network_failure_step_count"] > 0:
        add(
            category="site_dependency_anomaly",
            classification="infra",
            signature="browser_reported_site_dependency_failure",
            summary="browser steps reported a transport, DNS, or connection failure",
            evidence_paths=(
                required["solver_trace"],
                required["network_har"],
                required["playwright_trace"],
            ),
            details={
                "network_failure_step_count": trace_summary[
                    "network_failure_step_count"
                ]
            },
        )
    elif trace_summary["failed_step_count"] >= 2:
        add(
            category="site_dependency_anomaly",
            classification="infra",
            signature="repeated_browser_step_failure",
            summary="multiple browser steps reported environment execution failures",
            evidence_paths=(required["solver_trace"], required["playwright_trace"]),
            details={"failed_step_count": trace_summary["failed_step_count"]},
        )
    if (
        har_summary["transport_or_server_failure_count"] >= 2
        and har_summary["transport_or_server_failure_ratio"] >= 0.1
    ):
        add(
            category="site_dependency_anomaly",
            classification="infra",
            signature="repeated_har_transport_or_server_failure",
            summary="network trace contains repeated transport or server failures",
            evidence_paths=(required["network_har"], required["playwright_trace"]),
            details={
                "failure_count": har_summary[
                    "transport_or_server_failure_count"
                ],
                "failure_ratio": har_summary[
                    "transport_or_server_failure_ratio"
                ],
            },
        )

    if eval_result.get("status") == "error" or any(
        isinstance(row, Mapping) and row.get("status") == "error"
        for row in list(eval_result.get("evaluators_results") or [])
    ):
        add(
            category="evaluator_instruction_alignment",
            classification="potential_case_issue",
            signature="official_evaluator_returned_error",
            summary="integrity-verified official evaluator returned an error outcome",
            evidence_paths=(required["eval_result"], required["eval_summary"]),
        )

    protocol = str(solver.get("response_protocol_source") or "")
    final_source = str(solver.get("final_response_source") or "")
    if protocol in {
        "invalid_structured_json",
        "invalid_structured_schema",
        "missing_stop_action",
    } or final_source != "official_stop_action":
        add(
            category="agent_execution_outcome",
            classification="agent",
            signature="agent_final_response_protocol_failure",
            summary="agent did not finish through the required structured official stop protocol",
            evidence_paths=(required["solver_trace"], required["agent_response"]),
        )
    elif agent_response.get("status") != "SUCCESS" and eval_result.get(
        "status"
    ) == "failure":
        # Ordinary scored agent failures are not recorded as case anomalies.
        pass

    deduplicated = _deduplicate_issues(issues)
    category_signatures: dict[str, list[str]] = {}
    for issue in deduplicated:
        category = str(dict(issue.get("details") or {}).get("semantic_category") or "")
        category_signatures.setdefault(category, []).append(str(issue["signature"]))
    review_categories = (
        "instruction_ambiguity",
        "start_page_reachability",
        "evaluator_instruction_alignment",
        "initial_state_or_session_conflict",
        "answer_or_evaluator_leakage",
        "site_dependency_anomaly",
    )
    receipt_core = {
        "schema_version": "webarena_verified_semantic_case_review/v1",
        "record_slot_id": str(job["record_slot_id"]),
        "task_id": task_id,
        "task_revision": int(job["task_revision"]),
        "agent_id": str(job["agent_id"]),
        "source_evidence": _evidence_records(
            (
                packet_md_path,
                packet_path,
                agent_input_path,
                raw_task_path,
                tag_task_path,
                required["official_task"],
                required["reset_receipt"],
                required["solver_trace"],
                required["network_har"],
                required["network_har_sanitization"],
                required["playwright_trace"],
                required["eval_result"],
                llm_attempts_path,
            )
        ),
        "official_evaluator_semantics": {
            "task_type": task_type,
            "evaluator_names": packet_evaluators,
            "evaluator_count": len(packet_evaluators),
            "private_expected_values_recorded": False,
        },
        "solver_trace_summary": trace_summary,
        "har_summary": har_summary,
        "category_status": {
            category: (
                "needs_review"
                if category_signatures.get(category)
                else "reviewed_no_deterministic_indicator"
            )
            for category in review_categories
        },
        "finding_signatures": sorted(
            str(issue["signature"]) for issue in deduplicated
        ),
        "needs_review": bool(deduplicated),
        "case_defect_concluded": False,
        "interrupt_requested": False,
        "score_mutation_requested": False,
        "rerun_requested": False,
        "private_evaluator_payload_recorded": False,
    }
    return {
        "review_receipt_sha256": sha256_object(receipt_core),
        **receipt_core,
    }, deduplicated


def _response_schema_matches_task_type(
    evaluator: Mapping[str, Any], task_type: str
) -> bool:
    expected = evaluator.get("expected")
    schema = evaluator.get("results_schema")
    if not isinstance(expected, Mapping) or not isinstance(schema, Mapping):
        return False
    if task_type == "RETRIEVE":
        return (
            schema.get("type") == "array"
            and isinstance(expected.get("retrieved_data"), list)
        )
    if task_type in {"NAVIGATE", "MUTATE"}:
        return schema.get("type") == "null" and expected.get("retrieved_data") is None
    return False


def _prompt_private_marker_hits(path: Path) -> list[str]:
    if not path.is_dir() or path.is_symlink():
        return ["llm_attempts_directory_missing"]
    markers = {
        "private_config_sha256",
        "private_dataset_ref",
        "evaluator_reference",
        "answer_payload_embedded",
        "case_packet.md",
        "raw_case/derived/task.json",
    }
    hits: set[str] = set()
    prompt_paths = sorted(path.glob("*_prompt.json"))
    if not prompt_paths:
        return ["model_prompt_artifact_missing"]
    for prompt_path in prompt_paths:
        try:
            text = prompt_path.read_text(encoding="utf-8").lower()
        except OSError:
            hits.add("model_prompt_artifact_unreadable")
            continue
        for marker in markers:
            if marker in text:
                hits.add(marker)
    return sorted(hits)


def _har_review_summary(
    har: Mapping[str, Any], *, start_urls: Sequence[str]
) -> dict[str, Any]:
    entries = [
        entry
        for entry in list(dict(har.get("log") or {}).get("entries") or [])
        if isinstance(entry, Mapping)
    ]
    statuses: list[int] = []
    request_urls: list[str] = []
    for entry in entries:
        request_urls.append(str(dict(entry.get("request") or {}).get("url") or ""))
        status = dict(entry.get("response") or {}).get("status")
        if isinstance(status, int) and not isinstance(status, bool):
            statuses.append(status)
    observations: list[dict[str, Any]] = []
    for start_url in start_urls:
        matching = [
            (url, status)
            for entry, url in zip(entries, request_urls, strict=True)
            if _url_matches_start(url, start_url)
            for status in [dict(entry.get("response") or {}).get("status")]
        ]
        observations.append(
            {
                "matching_request_count": len(matching),
                "response_statuses": sorted(
                    {
                        int(status)
                        for _, status in matching
                        if isinstance(status, int) and not isinstance(status, bool)
                    }
                ),
            }
        )
    failure_count = sum(status <= 0 or status >= 500 for status in statuses)
    entry_count = len(entries)
    return {
        "entry_count": entry_count,
        "response_status_buckets": {
            "transport_or_zero": sum(status <= 0 for status in statuses),
            "2xx": sum(200 <= status < 300 for status in statuses),
            "3xx": sum(300 <= status < 400 for status in statuses),
            "4xx": sum(400 <= status < 500 for status in statuses),
            "5xx": sum(status >= 500 for status in statuses),
        },
        "distinct_request_origin_count": len(
            {
                _url_origin(url)
                for url in request_urls
                if _url_origin(url) is not None
            }
        ),
        "start_url_count": len(start_urls),
        "start_url_observations": observations,
        "transport_or_server_failure_count": failure_count,
        "transport_or_server_failure_ratio": (
            round(failure_count / entry_count, 6) if entry_count else 0.0
        ),
        "raw_urls_recorded": False,
        "response_bodies_recorded": False,
    }


def _solver_trace_review_summary(
    steps: Sequence[Mapping[str, Any]], *, start_urls: Sequence[str]
) -> dict[str, Any]:
    failures = [str(step.get("fail_error") or "") for step in steps]
    network_tokens = (
        "err_name_not_resolved",
        "err_connection",
        "econnrefused",
        "dns",
        "networkerror",
        "timed out",
        "timeout",
    )
    first_url = str(steps[0].get("page_url_before") or "") if steps else ""
    first_lower = first_url.lower()
    if not first_url:
        first_page_class = "missing"
    elif first_lower in {"about:blank", "data:,"}:
        first_page_class = "blank"
    elif any(token in urlsplit(first_url).path.lower() for token in ("login", "sign_in")):
        expected_login = any(
            any(token in urlsplit(url).path.lower() for token in ("login", "sign_in"))
            for url in start_urls
        )
        first_page_class = "expected_start_page" if expected_login else "unexpected_login_page"
    elif any(_url_origin(first_url) == _url_origin(url) for url in start_urls):
        first_page_class = "expected_start_origin"
    else:
        first_page_class = "other_origin"
    page_urls = [
        str(step.get(key) or "")
        for step in steps
        for key in ("page_url_before", "page_url_after")
        if str(step.get(key) or "")
    ]
    return {
        "step_count": len(steps),
        "failed_step_count": sum(bool(value.strip()) for value in failures),
        "network_failure_step_count": sum(
            any(token in value.lower() for token in network_tokens)
            for value in failures
            if value.strip()
        ),
        "first_page_class": first_page_class,
        "distinct_page_origin_count": len(
            {_url_origin(url) for url in page_urls if _url_origin(url) is not None}
        ),
        "raw_page_urls_recorded": False,
        "raw_actions_recorded": False,
        "raw_errors_recorded": False,
    }


def _url_origin(value: str) -> tuple[str, str, int | None] | None:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    if not parsed.scheme or not parsed.hostname:
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    return parsed.scheme.lower(), parsed.hostname.lower(), port


def _url_matches_start(candidate: str, start: str) -> bool:
    normalized_candidate = candidate.split("#", 1)[0].rstrip("/")
    normalized_start = start.split("#", 1)[0].rstrip("/")
    return bool(
        normalized_candidate == normalized_start
        or normalized_candidate.startswith(normalized_start + "?")
        or normalized_candidate.startswith(normalized_start + "/")
    )


def _classify_failure_record(job: Mapping[str, Any], path: Path) -> dict[str, Any]:
    payload = _load_optional_object(path) or {}
    text = " ".join(
        str(payload.get(key) or "")
        for key in ("error_type", "error_message", "message", "status")
    )
    return _classify_runtime_text(job, text, evidence_paths=(path,))


def _classify_runtime_exception(
    job: Mapping[str, Any],
    exc: Exception,
    *,
    failure_stage: str | None = None,
) -> dict[str, Any]:
    return _classify_runtime_text(
        job,
        f"{type(exc).__name__} {exc}",
        evidence_paths=_existing_slot_evidence_paths(job),
        details={
            "exception_type": type(exc).__name__,
            **({"failure_stage": failure_stage} if failure_stage else {}),
        },
    )


def _classify_runtime_text(
    job: Mapping[str, Any],
    text: str,
    *,
    evidence_paths: Sequence[Path],
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = text.lower()
    if "runtime_completed_unsealed" in normalized:
        return _issue(
            job,
            classification="infra",
            circuit_class="none",
            signature="post_run_audit_deferred_for_full_sweep",
            summary="paid runtime completed; final sealing requires reconciliation",
            evidence_paths=evidence_paths,
            details=details,
        )
    if any(
        token in normalized
        for token in (
            "credential_or_billing_failure",
            "openrouter http 401",
            "openrouter http 402",
            "api key",
            "unauthorized",
            "authentication failed",
            "insufficient credit",
        )
    ):
        return _issue(
            job,
            classification="systemic",
            circuit_class="credential",
            signature="credential_or_billing_failure",
            summary="model credential or billing authorization failed",
            evidence_paths=evidence_paths,
            details=details,
        )
    if any(
        token in normalized
        for token in (
            "openrouter_rate_limited",
            "openrouter_empty_response",
            "official_auto_login_failed",
            "official_evaluator_infrastructure_failure",
            "playwright_page_client_incompatible",
        )
    ):
        return _issue(
            job,
            classification="infra",
            circuit_class="infra",
            signature="transient_transport_or_worker_failure",
            summary="bounded model or official-runtime infrastructure failure",
            evidence_paths=evidence_paths,
            details=details,
        )
    if any(
        token in normalized
        for token in ("no space left", "enospc", "disk full", "free-space", "free space")
    ):
        return _issue(
            job,
            classification="infra",
            circuit_class="storage",
            signature="storage_capacity_failure",
            summary="results storage failed its capacity/write requirement",
            evidence_paths=evidence_paths,
            details=details,
        )
    if any(
        token in normalized
        for token in ("slot reset", "reset receipt", "reset scope", "site reset")
    ):
        return _issue(
            job,
            classification="infra",
            circuit_class="reset",
            signature="slot_reset_failure",
            summary="mandatory pre-slot environment reset failed",
            evidence_paths=evidence_paths,
            details=details,
        )
    if any(
        token in normalized
        for token in (
            "hash mismatch",
            "checksum mismatch",
            "contract mismatch",
            "source bundle",
            "task revision",
            "evaluator integrity",
            "runtime config",
            "route changed",
        )
    ):
        return _issue(
            job,
            classification="systemic",
            circuit_class="systemic",
            signature="frozen_input_or_evaluator_integrity_failure",
            summary="frozen input, route, runtime, or evaluator integrity failed",
            evidence_paths=evidence_paths,
            details=details,
        )
    failure_stage = str(dict(details or {}).get("failure_stage") or "")
    if failure_stage == "planner" or (
        failure_stage == "adapter_execution_before_slot_evidence"
        and any(token in normalized for token in ("controller", "preflight"))
    ):
        signature = "controller_preflight_failure"
        summary = "controller preflight failed before slot planning completed"
    elif any(
        token in normalized
        for token in (
            "timeout",
            "timed out",
            "connection",
            "ssh",
            "browser closed",
            "target closed",
            "docker",
            "infra_excluded",
        )
    ):
        signature = "transient_transport_or_worker_failure"
        summary = "isolated runtime failure requires review and later resume"
    else:
        signature = "unclassified_runtime_failure"
        summary = "isolated runtime failure requires review and later resume"
    return _issue(
        job,
        classification="infra",
        circuit_class="infra",
        signature=signature,
        summary=summary,
        evidence_paths=evidence_paths,
        details=details,
    )


def _issue(
    job: Mapping[str, Any],
    *,
    classification: str,
    circuit_class: str,
    signature: str,
    summary: str,
    evidence_paths: Sequence[Path],
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if classification not in ALLOWED_CLASSIFICATIONS:
        raise WebArenaRunControlError(f"invalid issue classification: {classification}")
    if circuit_class not in ALLOWED_CIRCUIT_CLASSES:
        raise WebArenaRunControlError(f"invalid circuit class: {circuit_class}")
    evidence = _evidence_records(evidence_paths)
    task_id = int(job["task_id"])
    packet = resolve_repo_path(TASK_PACKET_ROOT / str(task_id) / "case_packet.json")
    agent_input = resolve_repo_path(TASK_PACKET_ROOT / str(task_id) / "agent_input.json")
    core = {
        "schema_version": ISSUE_SCHEMA,
        "classification": classification,
        "circuit_class": circuit_class,
        "signature": signature,
        "summary": summary,
        "record_slot_id": str(job["record_slot_id"]),
        "task_id": task_id,
        "task_revision": int(job["task_revision"]),
        "agent_id": str(job["agent_id"]),
        "job_object_sha256": sha256_object(dict(job)),
        "source_binding": {
            "case_packet_sha256": sha256_file(packet) if packet.is_file() else None,
            "agent_input_sha256": sha256_file(agent_input)
            if agent_input.is_file()
            else None,
        },
        "evidence": evidence,
        "details": dict(details or {}),
        "needs_review": True,
        "case_defect_concluded": False,
        "interrupt_requested": False,
        "score_mutation_requested": False,
        "rerun_requested": False,
    }
    return {"issue_id": sha256_object(core), **core}


def _evidence_records(paths: Sequence[Path]) -> list[dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for candidate in paths:
        try:
            path = resolve_repo_path(candidate)
        except (RuntimeError, ValueError):
            continue
        if path.is_symlink() or (not path.is_file() and not path.is_dir()):
            continue
        display = _display_path(path)
        records[display] = {
            "path": display,
            "sha256": sha256_path(path),
            "kind": "directory_tree" if path.is_dir() else "file",
        }
    return [records[key] for key in sorted(records)]


def _existing_slot_evidence_paths(job: Mapping[str, Any]) -> tuple[Path, ...]:
    root = resolve_repo_path(job_result_relative_dir(job) / "adapter")
    candidates = (
        root / "failure_record.json",
        root / "raw_run.json",
        root / "artifact_manifest.json",
        root / "native_run" / "run_summary.json",
        root / "native_run" / "reset_receipt.json",
    )
    return tuple(path for path in candidates if path.is_file())


def _deduplicate_issues(
    issues: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        dict(item)
        for _, item in sorted(
            {str(item["issue_id"]): item for item in issues}.items()
        )
    ]


def _load_ledger(path: Path) -> tuple[dict[str, Any], ...]:
    if not path.exists():
        return ()
    if not path.is_file() or path.is_symlink():
        raise WebArenaRunControlError("case issue ledger is not a regular file")
    issues: dict[str, dict[str, Any]] = {}
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise WebArenaRunControlError(
                f"case issue ledger line {line_number} is invalid JSON"
            ) from exc
        if not isinstance(payload, dict):
            raise WebArenaRunControlError(
                f"case issue ledger line {line_number} is not an object"
            )
        issue_id = str(payload.get("issue_id") or "")
        core = dict(payload)
        core.pop("issue_id", None)
        if (
            _SHA256_RE.fullmatch(issue_id) is None
            or sha256_object(core) != issue_id
            or payload.get("schema_version") != ISSUE_SCHEMA
            or payload.get("classification") not in ALLOWED_CLASSIFICATIONS
            or payload.get("circuit_class") not in ALLOWED_CIRCUIT_CLASSES
            or payload.get("needs_review") is not True
            or payload.get("case_defect_concluded") is not False
            or payload.get("interrupt_requested") is not False
            or payload.get("score_mutation_requested") is not False
            or payload.get("rerun_requested") is not False
        ):
            raise WebArenaRunControlError(
                f"case issue ledger line {line_number} failed semantic hash validation"
            )
        existing = issues.get(issue_id)
        if existing is not None and existing != payload:
            raise WebArenaRunControlError("duplicate issue ID has different content")
        issues[issue_id] = payload
    return tuple(issues[key] for key in sorted(issues))


def _ledger_bytes(issues: Sequence[Mapping[str, Any]]) -> bytes:
    if not issues:
        return b""
    return (
        "\n".join(
            json.dumps(dict(issue), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
            for issue in issues
        )
        + "\n"
    ).encode("utf-8")


def _merge_runtime_issue_into_ledger(
    issue: Mapping[str, Any],
    *,
    namespace: str,
    jobs_index_path: str | Path,
    site_lock_path: str | Path,
) -> None:
    del jobs_index_path, site_lock_path
    ledger = resolve_repo_path(
        Path("results/namespaces") / namespace / "case_issue_ledger.jsonl"
    )
    existing = {item["issue_id"]: item for item in _load_ledger(ledger)}
    existing.setdefault(str(issue["issue_id"]), dict(issue))
    payload = tuple(existing[key] for key in sorted(existing))
    _atomic_write_bytes(ledger, _ledger_bytes(payload), mode=0o600)
    _write_sidecar(ledger)


def _canonical_pilot_schedule_binding(
    *,
    pilot_jobs: Sequence[Mapping[str, Any]],
    full_index: Mapping[str, Any],
    full_index_file: Path,
    pilot_manifest: Path,
) -> dict[str, Any] | None:
    index_file = resolve_repo_path(DEFAULT_CANONICAL_PILOT_JOBS_INDEX)
    if not index_file.exists():
        return None
    if not index_file.is_file() or index_file.is_symlink() or not _sidecar_valid(index_file):
        raise WebArenaRunControlError("canonical pilot jobs index is unsafe or has a stale sidecar")
    index = _load_object(index_file, "canonical pilot jobs index")
    expected_source = {
        "path": _display_path(full_index_file),
        "index_sha256": sha256_file(full_index_file),
        "job_count": int(full_index["job_count"]),
        "jobs_sha256": str(full_index["jobs_sha256"]),
    }
    expected_manifest = {
        "path": _display_path(pilot_manifest),
        "sha256": sha256_file(pilot_manifest),
    }
    if (
        index.get("schema_version") != "webarena_verified_pilot_schedule_index/v1"
        or index.get("result_namespace") != PILOT_RESULT_NAMESPACE
        or index.get("job_count") != 24
        or index.get("jobs_sha256") != EXPECTED_PILOT_JOBS_SHA256
        or index.get("source_full_schedule") != expected_source
        or index.get("pilot_manifest") != expected_manifest
    ):
        raise WebArenaRunControlError("canonical pilot jobs index metadata changed")
    entries = index.get("entries")
    if not isinstance(entries, list) or len(entries) != 24:
        raise WebArenaRunControlError("canonical pilot jobs index must contain 24 entries")
    loaded_jobs: list[dict[str, Any]] = []
    for position, (entry, expected_job) in enumerate(
        zip(entries, pilot_jobs, strict=True)
    ):
        if not isinstance(entry, Mapping) or entry.get("position") != position:
            raise WebArenaRunControlError(
                f"canonical pilot index position changed at {position}"
            )
        relative = entry.get("path")
        if not isinstance(relative, str) or Path(relative).name != relative:
            raise WebArenaRunControlError("canonical pilot job path is unsafe")
        job_file = index_file.parent / relative
        if not job_file.is_file() or job_file.is_symlink():
            raise WebArenaRunControlError(f"canonical pilot job is missing: {relative}")
        file_sha = sha256_file(job_file)
        job = _load_object(job_file, f"canonical pilot job {position}")
        if (
            entry.get("sha256") != file_sha
            or entry.get("job_object_sha256") != sha256_object(job)
            or entry.get("record_slot_id") != expected_job["record_slot_id"]
            or entry.get("job_id") != expected_job["job_id"]
            or entry.get("task_id") != int(expected_job["task_id"])
            or entry.get("agent_id") != expected_job["agent_id"]
            or job != dict(expected_job)
        ):
            raise WebArenaRunControlError(
                f"canonical pilot job differs from strict derivation at {position}"
            )
        loaded_jobs.append(job)
    if sha256_object(loaded_jobs) != EXPECTED_PILOT_JOBS_SHA256:
        raise WebArenaRunControlError("canonical pilot aggregate jobs hash changed")

    acceptance_file = resolve_repo_path(DEFAULT_CANONICAL_PILOT_ACCEPTANCE)
    if (
        not acceptance_file.is_file()
        or acceptance_file.is_symlink()
        or not _sidecar_valid(acceptance_file)
    ):
        raise WebArenaRunControlError(
            "canonical pilot schedule acceptance is missing or has a stale sidecar"
        )
    acceptance = _load_object(acceptance_file, "canonical pilot schedule acceptance")
    canonical = dict(acceptance.get("canonical_schedule") or {})
    if (
        acceptance.get("schema_version")
        != "webarena_verified_pilot_schedule_acceptance/v1"
        or acceptance.get("status") != "pass"
        or acceptance.get("pilot_launch_eligible") is not True
        or canonical
        != {
            "index_path": _display_path(index_file),
            "index_sha256": sha256_file(index_file),
            "job_count": 24,
            "jobs_sha256": EXPECTED_PILOT_JOBS_SHA256,
        }
        or dict(acceptance.get("source_full_schedule") or {}) != expected_source
    ):
        raise WebArenaRunControlError("canonical pilot schedule acceptance changed")
    return {
        "kind": "canonical_pilot_schedule_index",
        "path": _display_path(index_file),
        "sha256": sha256_file(index_file),
        "job_count": 24,
        "jobs_sha256": EXPECTED_PILOT_JOBS_SHA256,
        "acceptance_path": _display_path(acceptance_file),
        "acceptance_sha256": sha256_file(acceptance_file),
        "pilot_manifest_path": _display_path(pilot_manifest),
        "pilot_manifest_sha256": sha256_file(pilot_manifest),
        "source_full_jobs_index_path": _display_path(full_index_file),
        "source_full_jobs_index_sha256": sha256_file(full_index_file),
    }


def _validate_launch_authorization(
    index: Mapping[str, Any], *, index_file: Path
) -> None:
    authorization = index.get("launch_authorization")
    if not isinstance(authorization, Mapping):
        raise WebArenaRunControlError("jobs index launch authorization is missing")
    if (
        authorization.get("basis") != "operator_machine_only_waiver"
        or authorization.get("status")
        != "authorized_machine_only_not_human_signoff"
        or authorization.get("human_review_requirement_waived") is not True
        or authorization.get("human_signed_count") != 0
        or authorization.get("human_signoff_claimed") is not False
    ):
        raise WebArenaRunControlError("jobs index waiver semantics changed")
    waiver_raw = authorization.get("operator_waiver_path")
    waiver_sha = authorization.get("operator_waiver_sha256")
    if not isinstance(waiver_raw, str) or _SHA256_RE.fullmatch(str(waiver_sha or "")) is None:
        raise WebArenaRunControlError("jobs index operator waiver pointer is invalid")
    waiver = resolve_repo_path(waiver_raw)
    if (
        not waiver.is_file()
        or waiver.is_symlink()
        or sha256_file(waiver) != waiver_sha
        or not _sidecar_valid(waiver)
    ):
        raise WebArenaRunControlError("operator waiver hash/sidecar is stale")
    if index_file.parent != resolve_repo_path(DEFAULT_JOBS_ROOT):
        # Custom copies are permitted for tests, but production acceptance must
        # still bind their exact index path/hash.
        return


def _future_gate(path_value: str | Path, *, require_all_gates: bool) -> dict[str, Any]:
    path = resolve_repo_path(path_value)
    if not path.is_file():
        return {"status": "pending", "path": _display_path(path), "sha256": None}
    payload = _load_optional_object(path)
    if payload is None or not _sidecar_valid(path):
        return {"status": "fail", "path": _display_path(path), "sha256": sha256_file(path)}
    gates = payload.get("gates")
    gates_ok = True
    if require_all_gates:
        gates_ok = isinstance(gates, Mapping) and bool(gates) and all(
            value is True for value in gates.values()
        )
    status = "pass" if payload.get("status") == "pass" and gates_ok else "pending"
    return {"status": status, "path": _display_path(path), "sha256": sha256_file(path)}


def _storage_gate(path_value: str | Path) -> dict[str, Any]:
    path = resolve_repo_path(path_value)
    if not path.is_file():
        return {"status": "pending", "path": _display_path(path), "sha256": None}
    payload = _load_optional_object(path)
    if payload is None or not _sidecar_valid(path):
        return {"status": "fail", "path": _display_path(path), "sha256": sha256_file(path)}
    ok = (
        payload.get("status") == "pass"
        and payload.get("all_three_capacity_thresholds_satisfied") is True
        and payload.get("pilot_storage_projection_complete") is True
        and payload.get("full_run_storage_projection_complete") is True
    )
    return {
        "status": "pass" if ok else "pending",
        "path": _display_path(path),
        "sha256": sha256_file(path),
    }


def _remote_retention_canary_gate(path_value: str | Path) -> dict[str, Any]:
    path = resolve_repo_path(path_value)
    if not path.is_file():
        return {"status": "pending", "path": _display_path(path), "sha256": None}
    payload = _load_optional_object(path)
    if payload is None or not _sidecar_valid(path):
        return {"status": "fail", "path": _display_path(path), "sha256": sha256_file(path)}
    results = payload.get("results")
    host_receipts = payload.get("remote_host_finalization_receipts")
    referenced_receipts_ok = _vps_host_finalization_receipts_ok(
        host_receipts,
        expected_agent_ids=set(EXPECTED_AGENT_IDS),
    )
    results_ok = (
        isinstance(results, list)
        and len(results) == 3
        and {str(item.get("agent_id")) for item in results if isinstance(item, Mapping)}
        == set(EXPECTED_AGENT_IDS)
        and all(
            isinstance(item, Mapping)
            and item.get("audit_state") == "canonical_reusable"
            and item.get("security_finding_count") == 0
            and item.get("gold_finding_count") == 0
            for item in results
        )
    )
    bindings = dict(payload.get("control_bindings") or {})
    critical_code = dict(bindings.get("critical_code_sha256") or {})
    required_code_paths = (
        "src/evidence_system/adapters/webarena_har_sanitization.py",
        "src/evidence_system/adapters/webarena_official_worker.py",
        "src/evidence_system/adapters/webarena_remote_retention.py",
        "src/evidence_system/adapters/webarena_verified.py",
        "src/evidence_system/cli/webarena_full_control.py",
        "src/evidence_system/orchestrator/webarena_verified_full_execution.py",
        "src/evidence_system/orchestrator/webarena_verified_pilot_execution.py",
        "src/evidence_system/orchestrator/webarena_verified_run_control.py",
        "scripts/build_webarena_verified_circuit_recovery.py",
        "scripts/build_webarena_verified_step20_acceptance.py",
        "scripts/run_webarena_verified_task0_canary.py",
    )
    current_index = resolve_repo_path(DEFAULT_JOBS_INDEX)
    bindings_ok = bool(
        bindings.get("schema_version")
        == "webarena_verified_canary_control_bindings/v1"
        and bindings.get("materialized_full_jobs_index_path")
        == _display_path(current_index)
        and bindings.get("materialized_full_jobs_index_sha256")
        == sha256_file(current_index)
        and bindings.get("materialized_full_jobs_sha256")
        == "5c613b729e96ac020b9e2a8d5cdba667371f086be7c5cad4e46292d9a349e704"
        and bindings.get("materialized_full_job_count") == 2436
        and bindings.get("legacy_native_claim_compiler_runtime_dependency")
        is False
        and bindings.get("formal_score_draft_provider")
        == "neurips_ed_track_minimal"
        and set(critical_code) == set(required_code_paths)
        and all(
            critical_code.get(code_path)
            == sha256_file(resolve_repo_path(code_path))
            for code_path in required_code_paths
        )
    )
    ok = (
        payload.get("schema_version")
        == "webarena_verified_three_host_task0_canary_acceptance/v1"
        and payload.get("status") == "pass"
        and payload.get("artifact_retention_mode") == RETENTION_MODE
        and payload.get("paid_slot_count") == 3
        and payload.get("required_artifact_audit_pass_count") == 3
        and payload.get("remote_file_and_hash_verification_over_ssh") is True
        and payload.get("security_scan_and_finalization_executed_on_each_vps") is True
        and payload.get("full_evidence_synced_to_controller") is False
        and payload.get("remote_directory_cleanup_performed") is False
        and results_ok
        and referenced_receipts_ok
        and bindings_ok
    )
    return {
        "status": "pass" if ok else "pending",
        "path": _display_path(path),
        "sha256": sha256_file(path),
    }


def _load_object(path: Path, label: str) -> dict[str, Any]:
    payload = _load_optional_object(path)
    if payload is None:
        raise WebArenaRunControlError(f"{label} is not a JSON object: {path}")
    return payload


def _load_optional_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = load_json_or_yaml(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _sidecar_valid(path: Path) -> bool:
    sidecar = path.with_name(path.name + ".sha256")
    if not sidecar.is_file() or sidecar.is_symlink():
        return False
    lines = [line.strip() for line in sidecar.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 1:
        return False
    parts = lines[0].split()
    return len(parts) == 2 and parts[0] == sha256_file(path) and parts[1] == path.name


def _atomic_write_json(path: Path, payload: Mapping[str, Any], *, mode: int) -> None:
    _atomic_write_bytes(path, _json_bytes(payload), mode=mode)


def _json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(dict(payload), ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _atomic_write_bytes(path: Path, data: bytes, *, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.read_bytes() == data:
        os.chmod(path, mode)
        return
    descriptor, temporary_raw = tempfile.mkstemp(
        prefix=f".{path.name}.tmp-", dir=str(path.parent)
    )
    temporary = Path(temporary_raw)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_sidecar(path: Path) -> None:
    content = f"{sha256_file(path)}  {path.name}\n".encode("ascii")
    _atomic_write_bytes(path.with_name(path.name + ".sha256"), content, mode=0o600)


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root()).as_posix()
    except ValueError:
        return str(path.resolve())
