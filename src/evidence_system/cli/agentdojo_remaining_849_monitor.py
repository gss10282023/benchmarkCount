"""Blind-only live monitors for the two-VPS AgentDojo remaining-849 campaign.

The monitors deliberately read only the campaign plan/control plane, blind
health ledgers, blind completion/failure journals, lifecycle receipts, procfs,
and filesystem counters.  They never open raw evidence, trajectories,
evaluators, worker stdout/stderr, or the sealed incident-to-case ledger.

Ordinary anomalies are appended to a blind issue ledger.  A hard-fatal
condition creates a durable request to pause *new* admissions.  This module
never sends a signal and never kills or otherwise controls a worker process.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import stat
import time
from typing import Any, Iterable, Mapping, Sequence
import uuid

from evidence_system.adapters import agentdojo_formal_supervisor as formal_supervisor
from evidence_system.adapters.agentdojo_runtime_control import (
    validate_blind_health_record,
)
from evidence_system.core.hashing import sha256_file, sha256_object


HEALTH_STATE_SCHEMA = "agentdojo_remaining_849_health_monitor_state/v1"
INTEGRITY_STATE_SCHEMA = "agentdojo_remaining_849_integrity_monitor_state/v1"
HEALTH_SNAPSHOT_SCHEMA = "agentdojo_remaining_849_health_snapshot/v1"
INTEGRITY_SNAPSHOT_SCHEMA = "agentdojo_remaining_849_integrity_snapshot/v1"
ISSUE_SCHEMA = "agentdojo_remaining_849_monitor_issue/v1"
PAUSE_SCHEMA = "agentdojo_remaining_849_pause_request/v1"
CONTROLLER_IDENTITY_SCHEMA = "agentdojo_remaining_849_controller_identity/v1"
COMPLETION_SCHEMA = "agentdojo_formal_remote_completion_journal_entry/v2"
FAILED_SCHEMA = "agentdojo_formal_attempt_failure/v1"

HEALTH_LEDGER = "openrouter_health.jsonl"
COMPLETION_JOURNAL = "formal-completion-journal.v2.jsonl"
FAILED_JOURNAL = "formal-failed-attempt-journal.v1.jsonl"
DEFAULT_ISSUE_LEDGER = "remaining-849-monitor-issues.v1.jsonl"
DEFAULT_PAUSE_REQUEST = "remaining-849-pause-request.v1.json"
DEFAULT_CONTROLLER_IDENTITY = "remaining-849-controller-identity.v1.json"

EXPECTED_AGENTS = ("Agent A", "Agent B", "Agent C")
FAILURE_STREAK_THRESHOLD = 4
DEFAULT_EXIT_RECEIPT_GRACE_SECONDS = 30.0
DEFAULT_MINIMUM_FREE_BYTES = 100 * 1024**3
DEFAULT_MINIMUM_FREE_INODES = 10_000
MAX_INCREMENT_BYTES = 64 << 20
MAX_JSONL_LINE_BYTES = 1 << 20
MAX_ISSUE_LEDGER_BYTES = 64 << 20

_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SESSION_ID = re.compile(r"^session-[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")
_FORBIDDEN_OUTPUT_MARKERS = (
    "prompt",
    "response",
    "trajectory",
    "evaluator",
    "label",
    "stdout",
    "stderr",
    "secret",
)
_FALSE_CONTENT_MARKER = (
    "contains_case_agent_prompt_response_trajectory_evaluator_or_label"
)


class MonitorError(RuntimeError):
    """A monitor input or invariant is invalid."""


class MonitorViolation(MonitorError):
    """A typed operational anomaly whose detail is never emitted verbatim."""

    def __init__(self, reason_code: str, detail: str, *, hard_fatal: bool) -> None:
        super().__init__(detail)
        self.reason_code = _safe_token(reason_code, "reason_code")
        self.detail = detail
        self.hard_fatal = bool(hard_fatal)


@dataclass(frozen=True)
class CampaignPlan:
    path: Path
    sha256: str
    schema_version: str
    execution_lock_sha256: str | None
    execution_policy_sha256: str | None
    vps_id: str
    ordered_by_agent: Mapping[str, tuple[str, ...]]
    agent_by_identity: Mapping[str, str]

    @property
    def identities(self) -> frozenset[str]:
        return frozenset(self.agent_by_identity)

    @property
    def record_slot_count(self) -> int:
        return len(self.agent_by_identity)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_token(value: str, field: str) -> str:
    normalized = str(value)
    if not _SAFE_ID.fullmatch(normalized):
        raise MonitorError(f"{field} is not a safe opaque identifier")
    return normalized


def _digest(value: Any, field: str) -> str:
    normalized = str(value).removeprefix("sha256:")
    if not _DIGEST.fullmatch(normalized):
        raise MonitorError(f"{field} is not a lowercase SHA-256")
    return normalized


def _optional_digest(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _digest(value, field)


def _nonnegative_int(value: Any, field: str, *, minimum: int = 0) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or int(value) < int(minimum)
    ):
        raise MonitorError(f"{field} is not an integer >= {minimum}")
    return int(value)


def _timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise MonitorError(f"{field} is not a timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MonitorError(f"{field} is not an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise MonitorError(f"{field} is not timezone-aware")
    return value


def _error_sha256(exc: BaseException) -> str:
    return sha256_object(
        {"exception_type": type(exc).__name__, "message": str(exc)}
    )


def _assert_blind_output(value: Any, *, location: str = "root") -> None:
    """Reject evidence-bearing output keys and unbounded output value types."""

    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise MonitorError(f"{location} contains a non-string output key")
            lowered = key.lower()
            if key != _FALSE_CONTENT_MARKER and any(
                marker in lowered for marker in _FORBIDDEN_OUTPUT_MARKERS
            ):
                raise MonitorError(f"{location} contains a forbidden output key")
            if key == _FALSE_CONTENT_MARKER and child is not False:
                raise MonitorError("blind content marker must be false")
            _assert_blind_output(child, location=f"{location}.{key}")
        return
    if isinstance(value, list) or isinstance(value, tuple):
        for index, child in enumerate(value):
            _assert_blind_output(child, location=f"{location}[{index}]")
        return
    if value is None or isinstance(value, (str, int, float, bool)):
        return
    raise MonitorError(f"{location} contains a non-JSON output value")


def _regular_file(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise MonitorError(f"{label} is not a regular file")
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise MonitorError(f"{label} is linked or non-regular")
    return path


def _regular_directory(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise MonitorError(f"{label} is not a regular directory")
    return path


def _load_object(path: Path, label: str) -> dict[str, Any]:
    candidate = _regular_file(path, label)
    try:
        loaded = json.loads(candidate.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MonitorError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(loaded, dict):
        raise MonitorError(f"{label} is not a JSON object")
    return loaded


def _resolve_indexed_job_path(plan_path: Path, raw: str) -> Path:
    value = Path(raw)
    if value.is_absolute():
        return value
    from_cwd = value.resolve()
    if from_cwd.exists() or from_cwd.is_symlink():
        return from_cwd
    return (plan_path.parent / value).resolve()


def _job_identity_from_index_entry(
    entry: Mapping[str, Any], *, plan_path: Path
) -> str:
    direct = entry.get("job_identity_sha256")
    if direct is None:
        direct = entry.get("opaque_job_identity_sha256")
    if direct is not None:
        return _digest(direct, "campaign entry job_identity_sha256")
    raw_path = entry.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        raise MonitorError(
            "campaign entry needs an opaque job identity or locked job path"
        )
    job_path = _resolve_indexed_job_path(plan_path, raw_path)
    _regular_file(job_path, "campaign locked job")
    if entry.get("sha256") is not None and _digest(
        entry["sha256"], "campaign locked job sha256"
    ) != sha256_file(job_path):
        raise MonitorError("campaign locked job hash differs")
    job = _load_object(job_path, "campaign locked job")
    identity = {
        key: job.get(key) for key in ("job_id", "case_unit_id", "record_slot_id")
    }
    if any(not isinstance(value, str) or not value for value in identity.values()):
        raise MonitorError("campaign locked job identity is incomplete")
    return sha256_object(identity)


def load_campaign_plan(path: str | Path, *, vps_id: str) -> CampaignPlan:
    plan_path = Path(path).resolve()
    payload = _load_object(plan_path, "campaign plan index")
    schema = payload.get("schema_version")
    if not isinstance(schema, str) or not schema.startswith("agentdojo_"):
        raise MonitorError("campaign plan schema_version is invalid")
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        raise MonitorError("campaign plan has no ordered entries")
    if payload.get("entries_sha256") is not None and _digest(
        payload["entries_sha256"], "campaign entries_sha256"
    ) != sha256_object(entries):
        raise MonitorError("campaign plan entries hash differs")
    for count_field in ("job_count", "record_slot_count"):
        if payload.get(count_field) is not None and _nonnegative_int(
            payload[count_field], f"campaign {count_field}", minimum=1
        ) != len(entries):
            raise MonitorError(f"campaign {count_field} differs from entries")

    normalized_vps = _safe_token(vps_id, "vps_id")
    ordered: dict[str, list[str]] = {agent: [] for agent in EXPECTED_AGENTS}
    agent_by_identity: dict[str, str] = {}
    for ordinal, raw_entry in enumerate(entries):
        if not isinstance(raw_entry, Mapping):
            raise MonitorError("campaign plan contains a non-object entry")
        assigned = next(
            (
                str(raw_entry[field])
                for field in ("vps_id", "machine_id", "shard_id")
                if raw_entry.get(field) is not None
            ),
            None,
        )
        if assigned is not None and assigned != normalized_vps:
            continue
        agent_id = str(raw_entry.get("agent_id") or "")
        if agent_id not in EXPECTED_AGENTS:
            raise MonitorError(f"campaign entry {ordinal} has an invalid agent lane")
        identity = _job_identity_from_index_entry(raw_entry, plan_path=plan_path)
        if identity in agent_by_identity:
            raise MonitorError("campaign plan contains a duplicate opaque job identity")
        agent_by_identity[identity] = agent_id
        ordered[agent_id].append(identity)
    if not agent_by_identity:
        raise MonitorError("campaign plan assigns no entries to this VPS")
    return CampaignPlan(
        path=plan_path,
        sha256=sha256_file(plan_path),
        schema_version=schema,
        execution_lock_sha256=_optional_digest(
            payload.get("execution_lock_sha256"), "campaign execution lock"
        ),
        execution_policy_sha256=_optional_digest(
            payload.get("execution_policy_sha256"), "campaign execution policy"
        ),
        vps_id=normalized_vps,
        ordered_by_agent={key: tuple(value) for key, value in ordered.items()},
        agent_by_identity=dict(agent_by_identity),
    )


def _empty_cursor() -> dict[str, int | None]:
    return {"device": None, "inode": None, "offset": 0}


def _new_health_state(plan: CampaignPlan) -> dict[str, Any]:
    now = _utc_now()
    return {
        "schema_version": HEALTH_STATE_SCHEMA,
        "monitor_mode": "health-watch",
        "campaign_plan_sha256": plan.sha256,
        "vps_id": plan.vps_id,
        "created_at": now,
        "updated_at": now,
        "health_cursor": _empty_cursor(),
        "health_totals": {
            "record_count": 0,
            "event_type_counts": {},
            "outcome_counts": {},
            "http_status_counts": {},
        },
        "runtime_policy_sha256": None,
        "credential_fingerprint_sha256": None,
        "observed_host_boot_id": None,
        "exit_receipt_missing_observations": {},
    }


def _new_integrity_state(plan: CampaignPlan) -> dict[str, Any]:
    now = _utc_now()
    return {
        "schema_version": INTEGRITY_STATE_SCHEMA,
        "monitor_mode": "integrity-watch",
        "campaign_plan_sha256": plan.sha256,
        "vps_id": plan.vps_id,
        "created_at": now,
        "updated_at": now,
        "completion_cursor": _empty_cursor(),
        "failed_cursor": _empty_cursor(),
        "completion_identities": [],
        "failed_attempt_identities": [],
        "failed_job_counts": {},
        "terminal_status": {},
    }


def _load_monitor_state(
    path: Path, *, mode: str, plan: CampaignPlan
) -> dict[str, Any]:
    if not path.exists() and not path.is_symlink():
        return _new_health_state(plan) if mode == "health-watch" else _new_integrity_state(plan)
    state = _load_object(path, "monitor state")
    expected_schema = HEALTH_STATE_SCHEMA if mode == "health-watch" else INTEGRITY_STATE_SCHEMA
    if (
        state.get("schema_version") != expected_schema
        or state.get("monitor_mode") != mode
        or state.get("campaign_plan_sha256") != plan.sha256
        or state.get("vps_id") != plan.vps_id
    ):
        raise MonitorError("monitor state binding differs")
    _assert_blind_output(state)
    return state


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(
        path,
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    _assert_blind_output(payload)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    _regular_directory(path.parent, "state output parent")
    if path.is_symlink():
        raise MonitorError("state output is symlinked")
    temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(temporary, flags, 0o600)
    try:
        encoded = (
            json.dumps(dict(payload), separators=(",", ":"), sort_keys=True) + "\n"
        ).encode("utf-8")
        view = memoryview(encoded)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise MonitorError("state output write made no progress")
            view = view[written:]
        os.fchmod(descriptor, 0o600)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)
    _fsync_directory(path.parent)


def _read_new_jsonl(
    path: Path,
    cursor: Mapping[str, Any],
    *,
    label: str,
    missing_allowed: bool,
) -> tuple[list[tuple[dict[str, Any], int, str]], dict[str, int | None]]:
    prior_device = cursor.get("device")
    prior_inode = cursor.get("inode")
    prior_offset = _nonnegative_int(cursor.get("offset"), f"{label} cursor offset")
    if not path.exists() and not path.is_symlink():
        if prior_device is not None or prior_inode is not None or prior_offset:
            raise MonitorViolation(
                f"{label}_disappeared", f"{label} disappeared after observation", hard_fatal=True
            )
        if missing_allowed:
            return [], _empty_cursor()
        raise MonitorViolation(
            f"{label}_missing", f"{label} is missing", hard_fatal=True
        )
    if path.is_symlink():
        raise MonitorViolation(
            f"{label}_unsafe", f"{label} is symlinked", hard_fatal=True
        )
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise MonitorViolation(
                f"{label}_unsafe", f"{label} is linked or non-regular", hard_fatal=True
            )
        if prior_device is not None and (
            int(prior_device) != int(info.st_dev) or int(prior_inode) != int(info.st_ino)
        ):
            raise MonitorViolation(
                f"{label}_replaced", f"{label} inode changed", hard_fatal=True
            )
        if info.st_size < prior_offset:
            raise MonitorViolation(
                f"{label}_truncated", f"{label} shrank", hard_fatal=True
            )
        fcntl.flock(descriptor, fcntl.LOCK_SH)
        try:
            os.lseek(descriptor, prior_offset, os.SEEK_SET)
            chunk = os.read(descriptor, MAX_INCREMENT_BYTES)
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)
    if len(chunk) == MAX_INCREMENT_BYTES and b"\n" not in chunk:
        raise MonitorViolation(
            f"{label}_line_too_large", f"{label} has an oversized line", hard_fatal=True
        )
    final_newline = chunk.rfind(b"\n")
    complete = b"" if final_newline < 0 else chunk[: final_newline + 1]
    rows: list[tuple[dict[str, Any], int, str]] = []
    relative_offset = 0
    for raw_line in complete.splitlines(keepends=True):
        line_offset = prior_offset + relative_offset
        relative_offset += len(raw_line)
        stripped = raw_line.rstrip(b"\r\n")
        if not stripped:
            continue
        if len(stripped) > MAX_JSONL_LINE_BYTES:
            raise MonitorViolation(
                f"{label}_line_too_large", f"{label} line is oversized", hard_fatal=True
            )
        try:
            decoded = stripped.decode("utf-8")
            loaded = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MonitorViolation(
                f"{label}_invalid_json", f"{label} has invalid JSON", hard_fatal=True
            ) from exc
        if not isinstance(loaded, dict):
            raise MonitorViolation(
                f"{label}_invalid_record", f"{label} has a non-object", hard_fatal=True
            )
        rows.append(
            (
                loaded,
                line_offset,
                hashlib.sha256(stripped).hexdigest(),
            )
        )
    return rows, {
        "device": int(info.st_dev),
        "inode": int(info.st_ino),
        "offset": prior_offset + len(complete),
    }


def _issue_record(
    *,
    plan: CampaignPlan,
    mode: str,
    source: str,
    reason_code: str,
    detail: str,
    hard_fatal: bool,
    event_identity: str,
    job_identity_sha256: str | None = None,
    agent_id: str | None = None,
    consecutive_failure_count: int | None = None,
) -> dict[str, Any]:
    normalized_job = (
        None
        if job_identity_sha256 is None
        else _digest(job_identity_sha256, "issue job identity")
    )
    if agent_id is not None and agent_id not in EXPECTED_AGENTS:
        raise MonitorError("issue agent lane is invalid")
    core = {
        "campaign_plan_sha256": plan.sha256,
        "vps_id": plan.vps_id,
        "monitor_mode": mode,
        "source": _safe_token(source, "issue source"),
        "reason_code": _safe_token(reason_code, "issue reason"),
        "event_identity": _digest(
            hashlib.sha256(event_identity.encode("utf-8")).hexdigest(),
            "issue event identity",
        ),
        "job_identity_sha256": normalized_job,
        "agent_id": agent_id,
    }
    record = {
        "schema_version": ISSUE_SCHEMA,
        "timestamp": _utc_now(),
        "issue_id": sha256_object(core),
        **core,
        "severity": "hard_fatal" if hard_fatal else "needs_review",
        "detail_sha256": hashlib.sha256(detail.encode("utf-8")).hexdigest(),
        "consecutive_failure_count": consecutive_failure_count,
        "action": "pause_requested" if hard_fatal else "continued",
        "blind_only": True,
        _FALSE_CONTENT_MARKER: False,
    }
    _assert_blind_output(record)
    return record


def _validate_issue_record(record: Mapping[str, Any]) -> None:
    expected = {
        "schema_version",
        "timestamp",
        "issue_id",
        "campaign_plan_sha256",
        "vps_id",
        "monitor_mode",
        "source",
        "reason_code",
        "event_identity",
        "job_identity_sha256",
        "agent_id",
        "severity",
        "detail_sha256",
        "consecutive_failure_count",
        "action",
        "blind_only",
        _FALSE_CONTENT_MARKER,
    }
    if set(record) != expected or record.get("schema_version") != ISSUE_SCHEMA:
        raise MonitorError("monitor issue ledger fields differ")
    for field in (
        "issue_id",
        "campaign_plan_sha256",
        "event_identity",
        "detail_sha256",
    ):
        _digest(record.get(field), f"monitor issue {field}")
    if record.get("job_identity_sha256") is not None:
        _digest(record["job_identity_sha256"], "monitor issue job identity")
    if record.get("agent_id") is not None and record["agent_id"] not in EXPECTED_AGENTS:
        raise MonitorError("monitor issue agent lane differs")
    if record.get("severity") not in {"hard_fatal", "needs_review"}:
        raise MonitorError("monitor issue severity differs")
    if record.get("action") not in {"pause_requested", "continued"}:
        raise MonitorError("monitor issue action differs")
    if record.get("blind_only") is not True or record.get(_FALSE_CONTENT_MARKER) is not False:
        raise MonitorError("monitor issue is not blind-only")
    _timestamp(record.get("timestamp"), "monitor issue timestamp")
    _assert_blind_output(record)


def _append_issue(path: Path, record: Mapping[str, Any]) -> bool:
    _validate_issue_record(record)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o750)
    _regular_directory(path.parent, "monitor issue parent")
    if path.is_symlink():
        raise MonitorError("monitor issue ledger is symlinked")
    flags = os.O_RDWR | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o640)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise MonitorError("monitor issue ledger is linked or non-regular")
        if info.st_size > MAX_ISSUE_LEDGER_BYTES:
            raise MonitorError("monitor issue ledger exceeds its safe read envelope")
        os.fchmod(descriptor, 0o640)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        try:
            os.lseek(descriptor, 0, os.SEEK_SET)
            existing = os.read(descriptor, int(info.st_size)).decode("utf-8")
            for line in existing.splitlines():
                if not line.strip():
                    continue
                loaded = json.loads(line)
                if not isinstance(loaded, dict):
                    raise MonitorError("monitor issue ledger has a non-object")
                _validate_issue_record(loaded)
                if loaded["issue_id"] == record["issue_id"]:
                    return False
            encoded = (
                json.dumps(dict(record), separators=(",", ":"), sort_keys=True) + "\n"
            ).encode("utf-8")
            view = memoryview(encoded)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise MonitorError("monitor issue append made no progress")
                view = view[written:]
            os.fsync(descriptor)
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)
    _fsync_directory(path.parent)
    return True


def _validate_pause_request(payload: Mapping[str, Any]) -> None:
    expected = {
        "schema_version",
        "created_at",
        "campaign_plan_sha256",
        "vps_id",
        "monitor_mode",
        "reason_code",
        "detail_sha256",
        "trigger_job_identity_sha256",
        "agent_id",
        "consecutive_failure_threshold",
        "consecutive_failure_count",
        "controller_action",
        "kill_worker_requested",
        "blind_only",
        _FALSE_CONTENT_MARKER,
    }
    if set(payload) != expected or payload.get("schema_version") != PAUSE_SCHEMA:
        raise MonitorError("pause request fields differ")
    for field in ("campaign_plan_sha256", "detail_sha256"):
        _digest(payload.get(field), f"pause request {field}")
    if payload.get("trigger_job_identity_sha256") is not None:
        _digest(payload["trigger_job_identity_sha256"], "pause trigger identity")
    if payload.get("agent_id") is not None and payload["agent_id"] not in EXPECTED_AGENTS:
        raise MonitorError("pause request agent lane differs")
    if payload.get("controller_action") != "pause_new_admissions_only":
        raise MonitorError("pause request action differs")
    if payload.get("kill_worker_requested") is not False:
        raise MonitorError("pause request must not request worker termination")
    if payload.get("blind_only") is not True or payload.get(_FALSE_CONTENT_MARKER) is not False:
        raise MonitorError("pause request is not blind-only")
    _timestamp(payload.get("created_at"), "pause request timestamp")
    _assert_blind_output(payload)


def _request_pause(
    path: Path,
    *,
    plan: CampaignPlan,
    mode: str,
    reason_code: str,
    detail: str,
    job_identity_sha256: str | None,
    agent_id: str | None,
    consecutive_failure_count: int | None,
) -> dict[str, Any]:
    payload = {
        "schema_version": PAUSE_SCHEMA,
        "created_at": _utc_now(),
        "campaign_plan_sha256": plan.sha256,
        "vps_id": plan.vps_id,
        "monitor_mode": mode,
        "reason_code": _safe_token(reason_code, "pause reason"),
        "detail_sha256": hashlib.sha256(detail.encode("utf-8")).hexdigest(),
        "trigger_job_identity_sha256": (
            None
            if job_identity_sha256 is None
            else _digest(job_identity_sha256, "pause trigger identity")
        ),
        "agent_id": agent_id,
        "consecutive_failure_threshold": FAILURE_STREAK_THRESHOLD,
        "consecutive_failure_count": consecutive_failure_count,
        "controller_action": "pause_new_admissions_only",
        "kill_worker_requested": False,
        "blind_only": True,
        _FALSE_CONTENT_MARKER: False,
    }
    _validate_pause_request(payload)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    _regular_directory(path.parent, "pause request parent")
    if path.exists() or path.is_symlink():
        existing = _load_object(path, "pause request")
        _validate_pause_request(existing)
        if (
            existing.get("campaign_plan_sha256") != plan.sha256
            or existing.get("vps_id") != plan.vps_id
        ):
            raise MonitorError("existing pause request binds another campaign or VPS")
        return existing
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError:
        existing = _load_object(path, "pause request")
        _validate_pause_request(existing)
        return existing
    try:
        encoded = (
            json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n"
        ).encode("utf-8")
        os.write(descriptor, encoded)
        os.fchmod(descriptor, 0o600)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _fsync_directory(path.parent)
    return payload


def _record_violation(
    violation: MonitorViolation,
    *,
    plan: CampaignPlan,
    mode: str,
    source: str,
    event_identity: str,
    issue_ledger: Path,
    pause_request: Path,
    job_identity_sha256: str | None = None,
    agent_id: str | None = None,
    consecutive_failure_count: int | None = None,
) -> dict[str, Any]:
    issue = _issue_record(
        plan=plan,
        mode=mode,
        source=source,
        reason_code=violation.reason_code,
        detail=violation.detail,
        hard_fatal=violation.hard_fatal,
        event_identity=event_identity,
        job_identity_sha256=job_identity_sha256,
        agent_id=agent_id,
        consecutive_failure_count=consecutive_failure_count,
    )
    _append_issue(issue_ledger, issue)
    if violation.hard_fatal:
        _request_pause(
            pause_request,
            plan=plan,
            mode=mode,
            reason_code=violation.reason_code,
            detail=violation.detail,
            job_identity_sha256=job_identity_sha256,
            agent_id=agent_id,
            consecutive_failure_count=consecutive_failure_count,
        )
    return issue


def _live_boot_id() -> str:
    value = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", value):
        raise MonitorError("live Linux boot ID is invalid")
    return value


def _boottime_seconds() -> float:
    value = float(Path("/proc/uptime").read_text(encoding="utf-8").split()[0])
    if value < 0:
        raise MonitorError("Linux boottime is invalid")
    return value


def _process_starttime_ticks(pid: int) -> int:
    raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").strip()
    end = raw.rfind(")")
    if end < 2:
        raise MonitorError("controller proc stat is invalid")
    fields = raw[end + 1 :].split()
    if len(fields) <= 19:
        raise MonitorError("controller proc stat lacks starttime")
    value = int(fields[19])
    if value <= 0:
        raise MonitorError("controller starttime is invalid")
    return value


def _controller_snapshot(
    identity_path: Path, *, plan: CampaignPlan, live_boot_id: str
) -> dict[str, Any]:
    payload = _load_object(identity_path, "controller identity")
    allowed = {
        "schema_version",
        "campaign_plan_sha256",
        "vps_id",
        "pid",
        "starttime_ticks",
        "host_boot_id",
        "created_at",
    }
    if set(payload) != allowed or payload.get("schema_version") != CONTROLLER_IDENTITY_SCHEMA:
        raise MonitorViolation(
            "controller_identity_invalid",
            "controller identity fields differ",
            hard_fatal=True,
        )
    if (
        payload.get("campaign_plan_sha256") != plan.sha256
        or payload.get("vps_id") != plan.vps_id
    ):
        raise MonitorViolation(
            "controller_identity_binding_drift",
            "controller identity campaign binding differs",
            hard_fatal=True,
        )
    pid = _nonnegative_int(payload.get("pid"), "controller pid", minimum=1)
    expected_start = _nonnegative_int(
        payload.get("starttime_ticks"), "controller starttime", minimum=1
    )
    boot_matches = payload.get("host_boot_id") == live_boot_id
    try:
        observed_start = _process_starttime_ticks(pid)
        alive = True
    except (FileNotFoundError, ProcessLookupError):
        observed_start = None
        alive = False
    identity_matches = alive and observed_start == expected_start
    snapshot = {
        "present": True,
        "alive": alive,
        "pid": pid,
        "starttime_ticks": expected_start,
        "identity_matches": identity_matches,
        "boot_matches": boot_matches,
    }
    if not alive:
        raise MonitorViolation(
            "controller_not_alive", "controller process is absent", hard_fatal=True
        )
    if not identity_matches:
        raise MonitorViolation(
            "controller_identity_conflict",
            "controller PID starttime differs",
            hard_fatal=True,
        )
    if not boot_matches:
        raise MonitorViolation(
            "controller_boot_changed", "controller boot ID differs", hard_fatal=True
        )
    _timestamp(payload.get("created_at"), "controller identity created_at")
    return snapshot


def _memory_snapshot() -> dict[str, int]:
    values: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        key, separator, raw = line.partition(":")
        if not separator:
            continue
        pieces = raw.strip().split()
        if pieces and pieces[0].isdigit():
            values[key] = int(pieces[0]) * 1024
    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", 0)
    swap_total = values.get("SwapTotal", 0)
    swap_free = values.get("SwapFree", 0)
    if total <= 0 or not 0 <= available <= total or not 0 <= swap_free <= swap_total:
        raise MonitorError("Linux memory counters are invalid")
    return {
        "memory_total_bytes": total,
        "memory_available_bytes": available,
        "memory_used_percent_milli": round(100_000 * (1 - available / total)),
        "swap_total_bytes": swap_total,
        "swap_used_bytes": swap_total - swap_free,
    }


def _filesystem_snapshot(path: Path) -> dict[str, int]:
    values = os.statvfs(path)
    return {
        "total_bytes": int(values.f_blocks * values.f_frsize),
        "free_bytes": int(values.f_bavail * values.f_frsize),
        "total_inodes": int(values.f_files),
        "free_inodes": int(values.f_favail),
    }


def readonly_supervisor_peek(runtime_root: str | Path) -> dict[str, Any]:
    """Inspect supervisor lifecycle files without status(), writes, or signals."""

    root = Path(runtime_root)
    attempts = root / "sealed-attempts"
    if not attempts.exists() and not attempts.is_symlink():
        return {"attempt_count": 0, "status_counts": {}, "attempts": []}
    _regular_directory(attempts, "sealed attempt namespace")
    live_boot = _live_boot_id()
    boottime = _boottime_seconds()
    rows: list[dict[str, Any]] = []
    for binding_root in sorted(attempts.iterdir(), key=lambda path: path.name):
        if binding_root.is_symlink() or not binding_root.is_dir() or not _DIGEST.fullmatch(binding_root.name):
            rows.append(
                {
                    "job_binding_sha256": (
                        binding_root.name if _DIGEST.fullmatch(binding_root.name) else None
                    ),
                    "session_id": None,
                    "status": "invalid_attempt_namespace",
                    "supervisor_alive": False,
                    "exit_code": None,
                    "outcome": None,
                    "timed_out": None,
                    "group_gone": None,
                    "detail_sha256": sha256_object(
                        {"type": "invalid_attempt_namespace"}
                    ),
                }
            )
            continue
        for attempt in sorted(binding_root.iterdir(), key=lambda path: path.name):
            row: dict[str, Any] = {
                "job_binding_sha256": binding_root.name,
                "session_id": attempt.name if _SESSION_ID.fullmatch(attempt.name) else None,
                "status": "invalid_attempt",
                "supervisor_alive": False,
                "exit_code": None,
                "outcome": None,
                "timed_out": None,
                "group_gone": None,
                "detail_sha256": None,
            }
            try:
                if attempt.is_symlink() or not attempt.is_dir() or row["session_id"] is None:
                    raise MonitorError("attempt directory identity is invalid")
                session_id = str(row["session_id"])
                exit_path = attempt / formal_supervisor.EXIT
                state_path = attempt / formal_supervisor.STATE
                claim_path = attempt / formal_supervisor.CLAIM
                spec_path = attempt / formal_supervisor.SPEC
                if exit_path.exists() or exit_path.is_symlink():
                    receipt = formal_supervisor._verify_exit(
                        exit_path, expected_session_id=session_id
                    )
                    row.update(
                        {
                            "status": "exited",
                            "exit_code": int(receipt["exit_code"]),
                            "outcome": str(receipt["outcome"]),
                            "timed_out": bool(receipt["timed_out"]),
                            "group_gone": bool(receipt["group_gone"]),
                        }
                    )
                elif state_path.exists() or state_path.is_symlink():
                    state = formal_supervisor._verify_state(
                        state_path, expected_session_id=session_id
                    )
                    if state["launched_host_boot_id"] != live_boot:
                        row["status"] = "boot_changed"
                    else:
                        try:
                            alive = formal_supervisor._safe_group_alive(state)
                        except formal_supervisor.ProcessIdentityConflict:
                            row["status"] = "identity_conflict"
                        else:
                            row["status"] = "running" if alive else "exit_receipt_missing"
                            row["supervisor_alive"] = bool(alive)
                elif claim_path.exists() or claim_path.is_symlink():
                    claim = formal_supervisor._verify_claim(
                        claim_path,
                        expected_session_id=session_id,
                        spec_path=spec_path,
                    )
                    try:
                        alive = formal_supervisor._claim_supervisor_alive(claim)
                    except formal_supervisor.ProcessIdentityConflict:
                        alive = False
                        row["status"] = "identity_conflict_before_state"
                    else:
                        if claim["host_boot_id"] != live_boot:
                            row["status"] = "boot_changed_before_state"
                        elif boottime < float(claim["bootstrap_deadline_boottime_seconds"]):
                            row["status"] = "bootstrapping"
                        else:
                            row["status"] = "bootstrap_deadline_expired"
                    row["supervisor_alive"] = bool(alive)
                elif spec_path.exists() or spec_path.is_symlink():
                    formal_supervisor._verify_spec(spec_path)
                    row["status"] = "launch_pending"
                else:
                    row["status"] = "launch_intent_only"
            except Exception as exc:
                row["status"] = "invalid_lifecycle_control"
                row["detail_sha256"] = _error_sha256(exc)
            rows.append(row)
    counts = Counter(str(row["status"]) for row in rows)
    result = {
        "attempt_count": len(rows),
        "status_counts": dict(sorted(counts.items())),
        "attempts": rows,
    }
    _assert_blind_output(result)
    return result


def _health_violation_for_row(row: Mapping[str, Any]) -> MonitorViolation | None:
    status = row.get("http_status")
    outcome = str(row.get("outcome") or "")
    if status in {401, 403}:
        return MonitorViolation(
            "provider_authentication_fatal",
            f"provider returned HTTP {status}",
            hard_fatal=True,
        )
    if status == 402 or outcome == "blocked":
        return MonitorViolation(
            "budget_or_credit_fatal",
            "provider credit or runtime budget blocked admission",
            hard_fatal=True,
        )
    if outcome == "retryable_error":
        return MonitorViolation(
            "retryable_provider_or_transport_issue",
            "a request attempt reported a retryable error",
            hard_fatal=False,
        )
    if outcome in {"fatal_error", "warning"}:
        return MonitorViolation(
            "isolated_runtime_issue",
            "a blind health row reported an isolated runtime issue",
            hard_fatal=False,
        )
    return None


_HARD_SUPERVISOR_STATES = {
    "boot_changed",
    "boot_changed_before_state",
    "identity_conflict",
    "identity_conflict_before_state",
    "bootstrap_deadline_expired",
    "invalid_attempt_namespace",
    "invalid_attempt",
    "invalid_lifecycle_control",
}


def _debounce_exit_receipt_missing(
    state: dict[str, Any],
    supervisors: Mapping[str, Any],
    *,
    observed_at: str,
    grace_seconds: float,
) -> set[str]:
    """Persistently debounce the supervisor-exit/receipt publication window.

    The detached supervisor fsyncs its exit receipt immediately before it
    leaves procfs.  A blind poll can therefore observe the process as gone a
    few milliseconds before the receipt becomes visible.  Only the exact
    opaque attempt identity is remembered; no worker output is opened.
    """

    if not 0.25 <= float(grace_seconds) <= 600.0:
        raise MonitorError("exit receipt grace is outside the safe range")
    current_dt = datetime.fromisoformat(
        _timestamp(observed_at, "exit receipt observation time").replace(
            "Z", "+00:00"
        )
    )
    prior_raw = state.get("exit_receipt_missing_observations", {})
    if not isinstance(prior_raw, Mapping):
        raise MonitorError("exit receipt observation state is invalid")
    prior: dict[str, Mapping[str, Any]] = {}
    for key, value in prior_raw.items():
        normalized_key = _digest(key, "exit receipt observation identity")
        if not isinstance(value, Mapping):
            raise MonitorError("exit receipt observation entry is invalid")
        prior[normalized_key] = value

    active: dict[str, dict[str, Any]] = {}
    matured: set[str] = set()
    attempts = supervisors.get("attempts", [])
    if not isinstance(attempts, list):
        raise MonitorError("supervisor attempt snapshot is invalid")
    for row in attempts:
        if not isinstance(row, Mapping) or row.get("status") != (
            "exit_receipt_missing"
        ):
            continue
        binding = _digest(
            row.get("job_binding_sha256"), "missing receipt job binding"
        )
        session = _safe_token(
            str(row.get("session_id") or ""), "missing receipt session"
        )
        identity = sha256_object(
            {
                "job_binding_sha256": binding,
                "session_id": session,
                "status": "exit_receipt_missing",
            }
        )
        existing = prior.get(identity)
        first_observed_at = observed_at
        observation_count = 1
        if existing is not None:
            first_observed_at = _timestamp(
                existing.get("first_observed_at"),
                "exit receipt first observation",
            )
            observation_count = _nonnegative_int(
                existing.get("observation_count"),
                "exit receipt observation count",
                minimum=1,
            ) + 1
        first_dt = datetime.fromisoformat(
            first_observed_at.replace("Z", "+00:00")
        )
        elapsed_seconds = max(0.0, (current_dt - first_dt).total_seconds())
        active[identity] = {
            "first_observed_at": first_observed_at,
            "last_observed_at": observed_at,
            "observation_count": observation_count,
        }
        if elapsed_seconds >= float(grace_seconds):
            matured.add(identity)
    state["exit_receipt_missing_observations"] = active
    return matured


def run_health_cycle(args: argparse.Namespace) -> dict[str, Any]:
    plan = load_campaign_plan(args.campaign_plan_index, vps_id=args.vps_id)
    blind_root = _regular_directory(Path(args.blind_root), "blind root")
    runtime_root = _regular_directory(Path(args.runtime_root), "runtime root")
    state_path = Path(args.state_output)
    issue_path = Path(args.issue_ledger or blind_root / DEFAULT_ISSUE_LEDGER)
    pause_path = Path(args.pause_request or runtime_root / DEFAULT_PAUSE_REQUEST)
    controller_path = Path(
        args.controller_identity or runtime_root / DEFAULT_CONTROLLER_IDENTITY
    )
    state = _load_monitor_state(
        state_path, mode="health-watch", plan=plan
    )
    live_boot = _live_boot_id()
    issues_this_cycle: list[dict[str, Any]] = []

    def record(
        violation: MonitorViolation,
        *,
        source: str,
        event_identity: str,
        job_identity: str | None = None,
        agent_id: str | None = None,
    ) -> None:
        issues_this_cycle.append(
            _record_violation(
                violation,
                plan=plan,
                mode="health-watch",
                source=source,
                event_identity=event_identity,
                issue_ledger=issue_path,
                pause_request=pause_path,
                job_identity_sha256=job_identity,
                agent_id=agent_id,
            )
        )

    try:
        controller = _controller_snapshot(
            controller_path, plan=plan, live_boot_id=live_boot
        )
    except MonitorViolation as violation:
        record(violation, source="controller", event_identity=violation.reason_code)
        controller = {
            "present": controller_path.exists() and not controller_path.is_symlink(),
            "alive": False,
            "pid": None,
            "starttime_ticks": None,
            "identity_matches": False,
            "boot_matches": False,
        }
    except Exception as exc:
        violation = MonitorViolation(
            "controller_identity_invalid", str(exc), hard_fatal=True
        )
        record(violation, source="controller", event_identity=_error_sha256(exc))
        controller = {
            "present": False,
            "alive": False,
            "pid": None,
            "starttime_ticks": None,
            "identity_matches": False,
            "boot_matches": False,
        }

    filesystems = {
        "blind_root": _filesystem_snapshot(blind_root),
        "runtime_root": _filesystem_snapshot(runtime_root),
    }
    for label, values in filesystems.items():
        if values["free_bytes"] < int(args.minimum_free_bytes):
            record(
                MonitorViolation(
                    "filesystem_free_space_fatal",
                    f"{label} free bytes are below the locked minimum",
                    hard_fatal=True,
                ),
                source="host",
                event_identity=f"{label}:free-bytes",
            )
        if values["free_inodes"] < int(args.minimum_free_inodes):
            record(
                MonitorViolation(
                    "filesystem_inode_fatal",
                    f"{label} free inodes are below the locked minimum",
                    hard_fatal=True,
                ),
                source="host",
                event_identity=f"{label}:free-inodes",
            )
    memory = _memory_snapshot()
    if memory["memory_used_percent_milli"] > int(args.maximum_memory_percent * 1000):
        record(
            MonitorViolation(
                "memory_threshold_warning",
                "memory use exceeded the blind health threshold",
                hard_fatal=False,
            ),
            source="host",
            event_identity="memory-threshold",
        )
    if memory["swap_used_bytes"] > 0:
        record(
            MonitorViolation(
                "swap_usage_warning",
                "swap usage is non-zero",
                hard_fatal=False,
            ),
            source="host",
            event_identity="swap-usage",
        )

    ledger_path = blind_root / HEALTH_LEDGER
    try:
        rows, cursor = _read_new_jsonl(
            ledger_path,
            state["health_cursor"],
            label="health_ledger",
            missing_allowed=True,
        )
    except MonitorViolation as violation:
        record(violation, source="health", event_identity=violation.reason_code)
        rows = []
        cursor = dict(state["health_cursor"])

    totals = dict(state["health_totals"])
    event_counts = Counter(
        {str(key): int(value) for key, value in dict(totals["event_type_counts"]).items()}
    )
    outcome_counts = Counter(
        {str(key): int(value) for key, value in dict(totals["outcome_counts"]).items()}
    )
    status_counts = Counter(
        {str(key): int(value) for key, value in dict(totals["http_status_counts"]).items()}
    )
    processed_rows = 0
    for row, offset, line_sha in rows:
        try:
            validate_blind_health_record(row)
        except Exception as exc:
            violation = MonitorViolation(
                "health_ledger_schema_invalid", str(exc), hard_fatal=True
            )
            record(
                violation,
                source="health",
                event_identity=f"{offset}:{line_sha}",
            )
            continue
        processed_rows += 1
        policy_sha = _digest(row["policy_sha256"], "health policy sha256")
        prior_policy = state.get("runtime_policy_sha256")
        if prior_policy is None:
            state["runtime_policy_sha256"] = policy_sha
        elif prior_policy != policy_sha:
            record(
                MonitorViolation(
                    "runtime_policy_binding_drift",
                    "health ledger policy hash changed",
                    hard_fatal=True,
                ),
                source="health",
                event_identity=f"policy:{offset}:{line_sha}",
            )
        fingerprint = row.get("credential_fingerprint_sha256")
        if fingerprint is not None:
            normalized = _digest(fingerprint, "health credential fingerprint")
            prior_fingerprint = state.get("credential_fingerprint_sha256")
            if prior_fingerprint is None:
                state["credential_fingerprint_sha256"] = normalized
            elif prior_fingerprint != normalized:
                record(
                    MonitorViolation(
                        "credential_binding_drift",
                        "health ledger credential fingerprint changed",
                        hard_fatal=True,
                    ),
                    source="health",
                    event_identity=f"credential:{offset}:{line_sha}",
                )
        row_boot = row.get("host_boot_id")
        if row_boot is not None:
            if state.get("observed_host_boot_id") is None:
                state["observed_host_boot_id"] = row_boot
            if row_boot != live_boot:
                record(
                    MonitorViolation(
                        "host_boot_changed",
                        "health row boot ID differs from the live host",
                        hard_fatal=True,
                    ),
                    source="health",
                    event_identity=f"boot:{offset}:{line_sha}",
                )
        event_counts[str(row["event_type"])] += 1
        outcome_counts[str(row["outcome"])] += 1
        if row.get("http_status") is not None:
            status_counts[str(int(row["http_status"]))] += 1
        violation = _health_violation_for_row(row)
        if violation is not None:
            identity = row.get("job_identity_sha256")
            agent_id = plan.agent_by_identity.get(str(identity)) if identity else None
            record(
                violation,
                source="health",
                event_identity=f"{offset}:{line_sha}",
                job_identity=str(identity) if identity else None,
                agent_id=agent_id,
            )
    totals = {
        "record_count": int(totals["record_count"]) + processed_rows,
        "event_type_counts": dict(sorted(event_counts.items())),
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "http_status_counts": dict(sorted(status_counts.items())),
    }
    state["health_cursor"] = cursor
    state["health_totals"] = totals

    supervisors = readonly_supervisor_peek(runtime_root)
    lifecycle_observed_at = _utc_now()
    matured_missing_receipts = _debounce_exit_receipt_missing(
        state,
        supervisors,
        observed_at=lifecycle_observed_at,
        grace_seconds=float(
            getattr(
                args,
                "supervisor_exit_receipt_grace_seconds",
                DEFAULT_EXIT_RECEIPT_GRACE_SECONDS,
            )
        ),
    )
    for row in supervisors["attempts"]:
        status_value = str(row["status"])
        binding = str(row.get("job_binding_sha256") or "none")
        session = str(row.get("session_id") or "none")
        missing_identity = sha256_object(
            {
                "job_binding_sha256": binding,
                "session_id": session,
                "status": "exit_receipt_missing",
            }
        )
        if status_value == "exit_receipt_missing" and (
            missing_identity in matured_missing_receipts
        ):
            record(
                MonitorViolation(
                    "supervisor_exit_receipt_missing",
                    "supervisor exit receipt remained missing beyond grace",
                    hard_fatal=True,
                ),
                source="supervisor",
                event_identity=f"{binding}:{session}:{status_value}",
            )
        elif status_value in _HARD_SUPERVISOR_STATES:
            record(
                MonitorViolation(
                    f"supervisor_{status_value}",
                    f"supervisor entered {status_value}",
                    hard_fatal=True,
                ),
                source="supervisor",
                event_identity=f"{binding}:{session}:{status_value}",
            )
        elif status_value == "exited" and int(row.get("exit_code") or 0) != 0:
            record(
                MonitorViolation(
                    "supervisor_job_exit_nonzero",
                    "a supervisor sealed a non-zero job exit",
                    hard_fatal=False,
                ),
                source="supervisor",
                event_identity=f"{binding}:{session}:nonzero",
            )

    state["updated_at"] = _utc_now()
    _atomic_write_json(state_path, state)
    pause_requested = pause_path.exists() and not pause_path.is_symlink()
    snapshot = {
        "schema_version": HEALTH_SNAPSHOT_SCHEMA,
        "timestamp": _utc_now(),
        "status": "admission_pause_requested" if pause_requested else (
            "issues_recorded" if issues_this_cycle else "healthy"
        ),
        "campaign_plan_sha256": plan.sha256,
        "vps_id": plan.vps_id,
        "monitor_mode": "health-watch",
        "planned_record_slot_count": plan.record_slot_count,
        "new_health_record_count": processed_rows,
        "health_totals": totals,
        "host": {
            "boot_id": live_boot,
            "memory": memory,
            "filesystems": filesystems,
        },
        "controller": controller,
        "supervisors": supervisors,
        "exit_receipt_missing_pending_count": len(
            state["exit_receipt_missing_observations"]
        ),
        "issues_recorded_this_cycle": len(issues_this_cycle),
        "hard_fatal_issues_this_cycle": sum(
            issue["severity"] == "hard_fatal" for issue in issues_this_cycle
        ),
        "pause_requested": pause_requested,
        "worker_signal_count": 0,
        "blind_only": True,
        _FALSE_CONTENT_MARKER: False,
    }
    _assert_blind_output(snapshot)
    return snapshot


_COMPLETION_FIELDS = {
    "schema_version",
    "recorded_at",
    "execution_lock_sha256",
    "execution_policy_sha256",
    "job_binding_sha256",
    "job_identity_sha256",
    "stage_authorization_sha256",
    "formal_stage_id",
    "formal_stage_session_id",
    "formal_execution_context_sha256",
    "artifact_file_count",
    "artifact_tree_sha256",
    "artifact_total_bytes",
    "native_episode_count",
    "attempt_tree_sha256",
    "attempt_file_count",
    "attempt_total_bytes",
    "supervisor_exit_receipt_sha256",
    "canonical_job_relative_path",
    "completion_marker_relative_path",
    "completion_marker_file_sha256",
    "completion_marker_semantic_sha256",
    "blind_only",
    _FALSE_CONTENT_MARKER,
}


def _validate_completion_entry(
    row: Mapping[str, Any], *, plan: CampaignPlan
) -> str:
    if set(row) != _COMPLETION_FIELDS or row.get("schema_version") != COMPLETION_SCHEMA:
        raise MonitorError("completion journal fields differ")
    if row.get("blind_only") is not True or row.get(_FALSE_CONTENT_MARKER) is not False:
        raise MonitorError("completion journal row is not blind-only")
    for field in (
        "execution_lock_sha256",
        "execution_policy_sha256",
        "job_binding_sha256",
        "job_identity_sha256",
        "stage_authorization_sha256",
        "formal_execution_context_sha256",
        "artifact_tree_sha256",
        "attempt_tree_sha256",
        "supervisor_exit_receipt_sha256",
        "completion_marker_file_sha256",
        "completion_marker_semantic_sha256",
    ):
        _digest(row.get(field), f"completion {field}")
    identity = str(row["job_identity_sha256"])
    if identity not in plan.identities:
        raise MonitorError("completion journal identity is outside this VPS plan")
    if plan.execution_lock_sha256 is not None and row.get(
        "execution_lock_sha256"
    ) != plan.execution_lock_sha256:
        raise MonitorError("completion execution lock binding differs")
    if plan.execution_policy_sha256 is not None and row.get(
        "execution_policy_sha256"
    ) != plan.execution_policy_sha256:
        raise MonitorError("completion execution policy binding differs")
    for field in (
        "artifact_file_count",
        "artifact_total_bytes",
        "attempt_file_count",
        "attempt_total_bytes",
    ):
        _nonnegative_int(row.get(field), f"completion {field}")
    if row.get("native_episode_count") != 3:
        raise MonitorError("completion journal does not prove three episodes")
    binding = str(row["job_binding_sha256"])
    if row.get("canonical_job_relative_path") != binding or row.get(
        "completion_marker_relative_path"
    ) != f"{binding}/adapter/formal_job_completion.json":
        raise MonitorError("completion journal relative paths differ")
    _timestamp(row.get("recorded_at"), "completion recorded_at")
    _assert_blind_output(row)
    return identity


_FAILED_FIELDS = {
    "schema_version",
    "sealed_at",
    "execution_lock_sha256",
    "execution_policy_sha256",
    "job_binding_sha256",
    "job_identity_sha256",
    "stage_authorization_sha256",
    "formal_stage_id",
    "formal_stage_session_id",
    "failure_category",
    "worker_exit_code",
    "attempt_tree_sha256",
    "attempt_file_count",
    "attempt_total_bytes",
    "blind_only",
    _FALSE_CONTENT_MARKER,
    "archive_relative_path",
    "attempt_failure_marker_sha256",
    "archive_tree_sha256",
    "archive_file_count",
    "archive_total_bytes",
    "attempt_identity_sha256",
}


def _validate_failed_entry(
    row: Mapping[str, Any], *, plan: CampaignPlan
) -> tuple[str, str]:
    observed = set(row)
    if observed == _FAILED_FIELDS | {"recorded_at"}:
        _timestamp(row.get("recorded_at"), "failed recorded_at")
    elif observed != _FAILED_FIELDS:
        raise MonitorError("failed journal fields differ")
    if row.get("schema_version") != FAILED_SCHEMA:
        raise MonitorError("failed journal schema differs")
    if row.get("blind_only") is not True or row.get(_FALSE_CONTENT_MARKER) is not False:
        raise MonitorError("failed journal row is not blind-only")
    for field in (
        "execution_lock_sha256",
        "execution_policy_sha256",
        "job_binding_sha256",
        "job_identity_sha256",
        "stage_authorization_sha256",
        "attempt_tree_sha256",
        "attempt_failure_marker_sha256",
        "archive_tree_sha256",
        "attempt_identity_sha256",
    ):
        _digest(row.get(field), f"failed {field}")
    identity = str(row["job_identity_sha256"])
    attempt_identity = str(row["attempt_identity_sha256"])
    if identity not in plan.identities:
        raise MonitorError("failed journal identity is outside this VPS plan")
    if plan.execution_lock_sha256 is not None and row.get(
        "execution_lock_sha256"
    ) != plan.execution_lock_sha256:
        raise MonitorError("failed execution lock binding differs")
    if plan.execution_policy_sha256 is not None and row.get(
        "execution_policy_sha256"
    ) != plan.execution_policy_sha256:
        raise MonitorError("failed execution policy binding differs")
    if row.get("failure_category") not in {
        "worker_error",
        "timeout",
        "unknown_outcome",
        "boot_changed",
    }:
        raise MonitorError("failed journal category differs")
    _nonnegative_int(row.get("worker_exit_code"), "failed worker exit code")
    for field in (
        "attempt_file_count",
        "attempt_total_bytes",
        "archive_file_count",
        "archive_total_bytes",
    ):
        _nonnegative_int(row.get(field), f"failed {field}")
    binding = str(row["job_binding_sha256"])
    session = str(row.get("formal_stage_session_id") or "")
    if not _SESSION_ID.fullmatch(session) or row.get(
        "archive_relative_path"
    ) != f"{binding}/{session}":
        raise MonitorError("failed journal archive path differs")
    _timestamp(row.get("sealed_at"), "failed sealed_at")
    _assert_blind_output(row)
    return identity, attempt_identity


def _lane_progress(
    plan: CampaignPlan, terminal: Mapping[str, str]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for agent_id in EXPECTED_AGENTS:
        ordered = plan.ordered_by_agent[agent_id]
        streak = 0
        settled_prefix = 0
        last_failure: str | None = None
        for identity in ordered:
            status_value = terminal.get(identity)
            if status_value is None:
                break
            settled_prefix += 1
            if status_value == "completed":
                streak = 0
                last_failure = None
            elif status_value == "failed":
                streak += 1
                last_failure = identity
            else:
                raise MonitorError("integrity terminal state is invalid")
        rows.append(
            {
                "agent_id": agent_id,
                "expected": len(ordered),
                "settled_prefix": settled_prefix,
                "pending_from_ordered_prefix": len(ordered) - settled_prefix,
                "completed_total": sum(
                    terminal.get(identity) == "completed" for identity in ordered
                ),
                "failed_total": sum(
                    terminal.get(identity) == "failed" for identity in ordered
                ),
                "consecutive_terminal_failure_streak": streak,
                "last_failure_job_identity_sha256": last_failure,
                "threshold": FAILURE_STREAK_THRESHOLD,
                "threshold_reached": streak >= FAILURE_STREAK_THRESHOLD,
            }
        )
    return rows


def run_integrity_cycle(args: argparse.Namespace) -> dict[str, Any]:
    plan = load_campaign_plan(args.campaign_plan_index, vps_id=args.vps_id)
    blind_root = _regular_directory(Path(args.blind_root), "blind root")
    runtime_root = _regular_directory(Path(args.runtime_root), "runtime root")
    state_path = Path(args.state_output)
    issue_path = Path(args.issue_ledger or blind_root / DEFAULT_ISSUE_LEDGER)
    pause_path = Path(args.pause_request or runtime_root / DEFAULT_PAUSE_REQUEST)
    state = _load_monitor_state(
        state_path, mode="integrity-watch", plan=plan
    )
    issues_this_cycle: list[dict[str, Any]] = []

    def record(
        violation: MonitorViolation,
        *,
        source: str,
        event_identity: str,
        job_identity: str | None = None,
        agent_id: str | None = None,
        streak: int | None = None,
    ) -> None:
        issues_this_cycle.append(
            _record_violation(
                violation,
                plan=plan,
                mode="integrity-watch",
                source=source,
                event_identity=event_identity,
                issue_ledger=issue_path,
                pause_request=pause_path,
                job_identity_sha256=job_identity,
                agent_id=agent_id,
                consecutive_failure_count=streak,
            )
        )

    completion_path = blind_root / COMPLETION_JOURNAL
    failed_path = blind_root / FAILED_JOURNAL
    try:
        completion_rows, completion_cursor = _read_new_jsonl(
            completion_path,
            state["completion_cursor"],
            label="completion_journal",
            missing_allowed=True,
        )
    except MonitorViolation as violation:
        record(violation, source="completion", event_identity=violation.reason_code)
        completion_rows = []
        completion_cursor = dict(state["completion_cursor"])
    try:
        failed_rows, failed_cursor = _read_new_jsonl(
            failed_path,
            state["failed_cursor"],
            label="failed_journal",
            missing_allowed=True,
        )
    except MonitorViolation as violation:
        record(violation, source="failed", event_identity=violation.reason_code)
        failed_rows = []
        failed_cursor = dict(state["failed_cursor"])

    completion_identities = set(str(value) for value in state["completion_identities"])
    failed_attempt_identities = set(
        str(value) for value in state["failed_attempt_identities"]
    )
    failed_job_counts = Counter(
        {str(key): int(value) for key, value in dict(state["failed_job_counts"]).items()}
    )
    terminal = {
        str(key): str(value) for key, value in dict(state["terminal_status"]).items()
    }
    new_completed = 0
    new_failed = 0

    for row, offset, line_sha in completion_rows:
        try:
            identity = _validate_completion_entry(row, plan=plan)
        except Exception as exc:
            record(
                MonitorViolation(
                    "completion_journal_schema_or_binding_invalid",
                    str(exc),
                    hard_fatal=True,
                ),
                source="completion",
                event_identity=f"{offset}:{line_sha}",
            )
            continue
        if identity in completion_identities:
            record(
                MonitorViolation(
                    "duplicate_completion_job_identity",
                    "completion journal repeats an opaque job identity",
                    hard_fatal=True,
                ),
                source="completion",
                event_identity=f"duplicate:{identity}:{offset}",
                job_identity=identity,
                agent_id=plan.agent_by_identity[identity],
            )
            continue
        completion_identities.add(identity)
        terminal[identity] = "completed"
        new_completed += 1

    for row, offset, line_sha in failed_rows:
        try:
            identity, attempt_identity = _validate_failed_entry(row, plan=plan)
        except Exception as exc:
            record(
                MonitorViolation(
                    "failed_journal_schema_or_binding_invalid",
                    str(exc),
                    hard_fatal=True,
                ),
                source="failed",
                event_identity=f"{offset}:{line_sha}",
            )
            continue
        if attempt_identity in failed_attempt_identities:
            record(
                MonitorViolation(
                    "duplicate_failed_attempt_identity",
                    "failed journal repeats an opaque attempt identity",
                    hard_fatal=True,
                ),
                source="failed",
                event_identity=f"duplicate:{attempt_identity}:{offset}",
                job_identity=identity,
                agent_id=plan.agent_by_identity[identity],
            )
            continue
        failed_attempt_identities.add(attempt_identity)
        failed_job_counts[identity] += 1
        if identity not in completion_identities:
            terminal[identity] = "failed"
        new_failed += 1
        record(
            MonitorViolation(
                "terminal_job_failure_recorded",
                "a terminal failed attempt was sealed",
                hard_fatal=False,
            ),
            source="failed",
            event_identity=f"{attempt_identity}:{offset}",
            job_identity=identity,
            agent_id=plan.agent_by_identity[identity],
        )
        if failed_job_counts[identity] > 1:
            record(
                MonitorViolation(
                    "multiple_failed_attempts_for_job",
                    "an opaque job has multiple distinct failed attempts",
                    hard_fatal=False,
                ),
                source="failed",
                event_identity=f"multiple:{identity}:{failed_job_counts[identity]}",
                job_identity=identity,
                agent_id=plan.agent_by_identity[identity],
            )

    lane_rows = _lane_progress(plan, terminal)
    for lane in lane_rows:
        streak = int(lane["consecutive_terminal_failure_streak"])
        if streak >= FAILURE_STREAK_THRESHOLD:
            identity = lane["last_failure_job_identity_sha256"]
            record(
                MonitorViolation(
                    "consecutive_terminal_failure_threshold",
                    "four ordered terminal jobs failed consecutively in one agent lane",
                    hard_fatal=True,
                ),
                source="circuit",
                event_identity=f"{lane['agent_id']}:{streak}:{identity}",
                job_identity=str(identity) if identity is not None else None,
                agent_id=str(lane["agent_id"]),
                streak=streak,
            )

    state.update(
        {
            "updated_at": _utc_now(),
            "completion_cursor": completion_cursor,
            "failed_cursor": failed_cursor,
            "completion_identities": sorted(completion_identities),
            "failed_attempt_identities": sorted(failed_attempt_identities),
            "failed_job_counts": dict(sorted(failed_job_counts.items())),
            "terminal_status": dict(sorted(terminal.items())),
        }
    )
    _atomic_write_json(state_path, state)
    completed_total = sum(value == "completed" for value in terminal.values())
    failed_total = sum(value == "failed" for value in terminal.values())
    pause_requested = pause_path.exists() and not pause_path.is_symlink()
    snapshot = {
        "schema_version": INTEGRITY_SNAPSHOT_SCHEMA,
        "timestamp": _utc_now(),
        "status": "admission_pause_requested" if pause_requested else (
            "issues_recorded" if issues_this_cycle else "healthy"
        ),
        "campaign_plan_sha256": plan.sha256,
        "vps_id": plan.vps_id,
        "monitor_mode": "integrity-watch",
        "planned_record_slot_count": plan.record_slot_count,
        "new_completion_count": new_completed,
        "new_failed_attempt_count": new_failed,
        "terminal_counts": {
            "completed": completed_total,
            "failed": failed_total,
            "pending": plan.record_slot_count - completed_total - failed_total,
            "failed_attempts": len(failed_attempt_identities),
        },
        "agent_lanes": lane_rows,
        "issues_recorded_this_cycle": len(issues_this_cycle),
        "hard_fatal_issues_this_cycle": sum(
            issue["severity"] == "hard_fatal" for issue in issues_this_cycle
        ),
        "pause_requested": pause_requested,
        "worker_signal_count": 0,
        "raw_evidence_files_opened": 0,
        "blind_only": True,
        _FALSE_CONTENT_MARKER: False,
    }
    _assert_blind_output(snapshot)
    return snapshot


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--campaign-plan-index", type=Path, required=True)
    parser.add_argument("--blind-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--state-output", type=Path, required=True)
    parser.add_argument("--issue-ledger", type=Path)
    parser.add_argument("--pause-request", type=Path)
    parser.add_argument("--vps-id", default=socket.gethostname())
    parser.add_argument("--poll-interval", type=float, default=5.0)
    parser.add_argument("--once", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    health = commands.add_parser("health-watch")
    _add_common_arguments(health)
    health.add_argument("--controller-identity", type=Path)
    health.add_argument(
        "--minimum-free-bytes", type=int, default=DEFAULT_MINIMUM_FREE_BYTES
    )
    health.add_argument(
        "--minimum-free-inodes", type=int, default=DEFAULT_MINIMUM_FREE_INODES
    )
    health.add_argument("--maximum-memory-percent", type=float, default=85.0)
    health.add_argument(
        "--supervisor-exit-receipt-grace-seconds",
        type=float,
        default=DEFAULT_EXIT_RECEIPT_GRACE_SECONDS,
    )
    integrity = commands.add_parser("integrity-watch")
    _add_common_arguments(integrity)
    return parser


def _safe_error_result(exc: BaseException, *, mode: str | None) -> dict[str, Any]:
    result = {
        "schema_version": "agentdojo_remaining_849_monitor_error/v1",
        "status": "error",
        "monitor_mode": mode,
        "error_type": type(exc).__name__,
        "error_sha256": _error_sha256(exc),
        "worker_signal_count": 0,
        "blind_only": True,
        _FALSE_CONTENT_MARKER: False,
    }
    _assert_blind_output(result)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if (
        not 0.25 <= float(args.poll_interval) <= 3600.0
        or getattr(args, "minimum_free_bytes", 0) < 0
        or getattr(args, "minimum_free_inodes", 0) < 0
        or not 1.0 <= getattr(args, "maximum_memory_percent", 85.0) <= 100.0
        or not 0.25 <= getattr(
            args,
            "supervisor_exit_receipt_grace_seconds",
            DEFAULT_EXIT_RECEIPT_GRACE_SECONDS,
        ) <= 600.0
    ):
        result = _safe_error_result(
            MonitorError("monitor threshold or polling arguments are invalid"),
            mode=args.command,
        )
        print(json.dumps(result, separators=(",", ":"), sort_keys=True))
        return 2
    runner = run_health_cycle if args.command == "health-watch" else run_integrity_cycle
    while True:
        try:
            result = runner(args)
        except Exception as exc:
            result = _safe_error_result(exc, mode=args.command)
            print(json.dumps(result, separators=(",", ":"), sort_keys=True), flush=True)
            return 2
        print(json.dumps(result, separators=(",", ":"), sort_keys=True), flush=True)
        if args.once:
            return 0
        time.sleep(float(args.poll_interval))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
