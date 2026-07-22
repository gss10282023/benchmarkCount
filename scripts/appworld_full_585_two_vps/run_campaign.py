#!/usr/bin/env python3
"""Run one deterministic AppWorld full-test shard with the standard worker.

The launcher keeps all benchmark artifacts on the VPS, runs the three paper
agents in the same A -> B -> C batch order as ``run_full``, and uses rolling
submission so a single slot failure never aborts the campaign.  A run is
halted only after the configured number of consecutive terminal
infrastructure errors; native evaluator failures are valid benchmark outcomes
and never count toward that threshold.
"""

from __future__ import annotations

import argparse
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Iterable
import urllib.error
import urllib.request


AGENTS = (
    ("Agent A", "agent_a", "openai/gpt-5.4"),
    ("Agent B", "agent_b", "anthropic/claude-opus-4.7"),
    ("Agent C", "agent_c", "deepseek/deepseek-v4-pro"),
)
REQUIRED_ARTIFACTS = (
    "run_summary.json",
    "native_evaluator_input.json",
    "native_evaluator_output.json",
    "official_runner_config.json",
    "artifact_manifest.json",
)
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
EXPECTED_DATA_VERSION = "0.2.0"
ADAPTIVE_WORKER_LEVELS = (6, 12, 24, 36, 48, 60, 72)
MINIMUM_AVAILABLE_MEMORY_AFTER_RAMP_GIB = 4.0
MEMORY_RESERVE_PER_ADDED_WORKER_GIB = 1.0
MAXIMUM_ONE_MINUTE_LOAD_PER_CPU_BEFORE_RAMP = 2.0


@dataclass(frozen=True)
class Case:
    task_id: str
    dataset_name: str
    global_index: int


@dataclass(frozen=True)
class Slot:
    case: Case
    agent_id: str
    agent_slug: str
    model: str

    @property
    def slot_id(self) -> str:
        return f"{self.agent_slug}__{self.case.task_id}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(payload) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def ramp_health_snapshot(current_workers: int, target_workers: int) -> dict[str, Any]:
    available_memory_gib: float | None = None
    meminfo_path = Path("/proc/meminfo")
    if meminfo_path.is_file():
        values: dict[str, int] = {}
        for line in meminfo_path.read_text(encoding="utf-8").splitlines():
            name, separator, raw_value = line.partition(":")
            if separator and raw_value.strip().endswith(" kB"):
                values[name] = int(raw_value.strip().split()[0])
        if "MemAvailable" in values:
            available_memory_gib = values["MemAvailable"] / (1024 * 1024)
    cpu_count = max(1, int(os.cpu_count() or 1))
    one_minute_load = float(os.getloadavg()[0])
    load_per_cpu = one_minute_load / cpu_count
    additional_workers = max(0, target_workers - current_workers)
    required_available_memory_gib = (
        MINIMUM_AVAILABLE_MEMORY_AFTER_RAMP_GIB
        + additional_workers * MEMORY_RESERVE_PER_ADDED_WORKER_GIB
    )
    memory_ok = (
        available_memory_gib is None
        or available_memory_gib >= required_available_memory_gib
    )
    load_ok = load_per_cpu <= MAXIMUM_ONE_MINUTE_LOAD_PER_CPU_BEFORE_RAMP
    return {
        "allowed": memory_ok and load_ok,
        "available_memory_gib": available_memory_gib,
        "required_available_memory_gib": required_available_memory_gib,
        "one_minute_load": one_minute_load,
        "cpu_count": cpu_count,
        "load_per_cpu": load_per_cpu,
        "maximum_load_per_cpu": MAXIMUM_ONE_MINUTE_LOAD_PER_CPU_BEFORE_RAMP,
        "memory_ok": memory_ok,
        "load_ok": load_ok,
    }


def acquire_campaign_lock(path: Path) -> Any:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        handle.close()
        raise RuntimeError("another launcher already holds the campaign lock") from exc
    handle.seek(0)
    handle.truncate()
    handle.write(canonical_json({"pid": os.getpid(), "acquired_at": utc_now()}) + "\n")
    handle.flush()
    os.fsync(handle.fileno())
    return handle


def load_cases(path: Path) -> list[Case]:
    cases: list[Case] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        case = Case(
            task_id=str(payload["task_id"]),
            dataset_name=str(payload["dataset_name"]),
            global_index=int(payload["global_index"]),
        )
        if not SAFE_ID.fullmatch(case.task_id):
            raise ValueError(f"unsafe task_id at line {line_number}: {case.task_id!r}")
        if case.dataset_name not in {"test_normal", "test_challenge"}:
            raise ValueError(f"invalid dataset_name at line {line_number}: {case.dataset_name!r}")
        cases.append(case)
    if not cases:
        raise ValueError("shard file is empty")
    if len({case.task_id for case in cases}) != len(cases):
        raise ValueError("shard contains duplicate task IDs")
    if len({case.global_index for case in cases}) != len(cases):
        raise ValueError("shard contains duplicate global indices")
    return cases


def completed_summary(output_dir: Path) -> dict[str, Any] | None:
    summary_path = output_dir / "run_summary.json"
    if not summary_path.is_file():
        return None
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if summary.get("status") != "completed":
        return None
    if any(not (output_dir / relative).is_file() for relative in REQUIRED_ARTIFACTS):
        return None
    data_version_path = output_dir / "appworld_task_output" / "version" / "data.txt"
    if not data_version_path.is_file():
        return None
    if data_version_path.read_text(encoding="utf-8").strip() != EXPECTED_DATA_VERSION:
        return None
    return summary


def billed_cost_usd(output_dir: Path) -> float:
    path = output_dir / "appworld_task_output" / "logs" / "lm_calls.jsonl"
    if not path.is_file():
        return 0.0
    total = 0.0
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw_line.strip():
            continue
        try:
            payload = json.loads(raw_line)
            total += float(((payload.get("output") or {}).get("usage") or {}).get("cost") or 0.0)
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
    return total


def existing_shard_cost_usd(output_root: Path, cases: list[Case]) -> float:
    return sum(
        billed_cost_usd(output_root / agent_slug / case.task_id)
        for _, agent_slug, _ in AGENTS
        for case in cases
    )


def prior_campaign_cost_usd(state_path: Path, *, run_id: str, vps_id: str) -> float:
    if not state_path.is_file():
        return 0.0
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("run_id") != run_id or state.get("vps_id") != vps_id:
            return 0.0
        return max(0.0, float(state.get("billed_cost_usd") or 0.0))
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        raise RuntimeError("existing campaign state is unreadable; refusing to reset its cost ledger")


def fatal_error_reason(error_type: str, error_message: str) -> str | None:
    combined = f"{error_type}: {error_message}".lower()
    fatal_markers = {
        "openrouter_402": ("insufficient credits", 'code":402', "status code: 402"),
        "openrouter_auth": ("status code: 401", "authenticationerror", "invalid api key"),
        "runtime_compatibility": ("unsupported appworld runtime", "not officially compatible"),
        "missing_runtime_artifact": ("api_docs.json", "filenotfounderror"),
    }
    for label, markers in fatal_markers.items():
        if any(marker in combined for marker in markers):
            return label
    return None


def validate_openrouter_key(api_key: str) -> dict[str, Any]:
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/key",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"OpenRouter key preflight failed with HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenRouter key preflight failed: {type(exc.reason).__name__}") from exc
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        raise RuntimeError("OpenRouter key preflight returned an unexpected response")
    return {
        "limit_remaining": data.get("limit_remaining"),
        "usage": data.get("usage"),
        "usage_daily": data.get("usage_daily"),
        "is_free_tier": data.get("is_free_tier"),
    }


def validate_openrouter_credits(api_key: str) -> dict[str, float]:
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/credits",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"OpenRouter credits preflight failed with HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenRouter credits preflight failed: {type(exc.reason).__name__}") from exc
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        raise RuntimeError("OpenRouter credits preflight returned an unexpected response")
    try:
        total_credits = float(data["total_credits"])
        total_usage = float(data["total_usage"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("OpenRouter credits preflight omitted required totals") from exc
    return {
        "total_credits_usd": total_credits,
        "total_usage_usd": total_usage,
        "available_balance_usd": max(0.0, total_credits - total_usage),
    }


def run_zero_lm_preflight(
    *, python_bin: Path, repo_root: Path, appworld_root: Path, shard_file: Path, control_root: Path
) -> dict[str, Any]:
    command = [
        str(python_bin),
        str(repo_root / "scripts" / "appworld_full_585_two_vps" / "preflight_runtime.py"),
        "--appworld-root",
        str(appworld_root),
        "--shard-file",
        str(shard_file),
    ]
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(repo_root / "src")
    environment["APPWORLD_ROOT"] = str(appworld_root)
    completed = subprocess.run(
        command,
        cwd=repo_root,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "zero-LM AppWorld preflight failed; no paid request was made: "
            + (completed.stderr or completed.stdout)[-4000:]
        )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    payload = json.loads(lines[-1])
    write_json(control_root / "preflight.json", payload)
    return payload


def lock_assignment(path: Path, *, run_id: str, vps_id: str, shard_file: Path, cases: list[Case]) -> None:
    payload = {
        "schema_version": "appworld_assignment_lock/v1",
        "run_id": run_id,
        "vps_id": vps_id,
        "shard_file_sha256": sha256_file(shard_file),
        "task_ids": [case.task_id for case in cases],
        "agents": [agent_slug for _, agent_slug, _ in AGENTS],
    }
    if path.is_file():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != payload:
            raise RuntimeError("immutable task assignment changed; refusing to make any LM request")
        return
    write_json(path, payload)


def validate_fixed_campaign_policy(
    path: Path,
    *,
    run_id: str,
    vps_id: str,
    shard_file: Path,
    cases: list[Case],
    initial_workers: int,
    max_workers: int,
    normal_completions_per_ramp: int,
    max_attempts: int,
    consecutive_error_limit: int,
    campaign_cost_cap_usd: float,
    confirmed_credit_balance_usd: float,
    per_slot_reserve_usd: float,
    allow_low_balance: bool,
    allow_retired_key: bool,
) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError("fixed assignment manifest is missing; refusing to make any LM request")
    payload = json.loads(path.read_text(encoding="utf-8"))
    shard = (payload.get("shards") or {}).get(vps_id) or {}
    budget = payload.get("budget_policy") or {}
    resources = payload.get("resource_ramp_policy") or {}
    expected = {
        "run_id": str(payload.get("run_id")),
        "shard_sha256": str(shard.get("sha256")),
        "task_count": int(shard.get("task_count") or 0),
        "initial_workers": int(payload.get("initial_workers_per_vps") or 0),
        "max_workers": int(payload.get("max_workers_per_vps") or 0),
        "normal_completions_per_ramp": int(payload.get("normal_completions_per_ramp") or 0),
        "worker_levels": tuple(int(value) for value in payload.get("worker_levels") or ()),
        "max_attempts": int(payload.get("automatic_task_attempts") or 0),
        "consecutive_error_limit": int(payload.get("consecutive_error_limit") or 0),
        "campaign_cost_cap_usd": float(budget.get(f"{vps_id}_campaign_cost_cap_usd") or 0.0),
        "per_slot_reserve_usd": float(budget.get("per_slot_reserve_usd") or 0.0),
        "minimum_confirmed_shared_balance_usd": float(
            budget.get("minimum_confirmed_shared_balance_usd") or 0.0
        ),
        "minimum_available_memory_after_ramp_gib": float(
            resources.get("minimum_available_memory_after_ramp_gib") or 0.0
        ),
        "memory_reserve_per_added_worker_gib": float(
            resources.get("memory_reserve_per_added_worker_gib") or 0.0
        ),
        "maximum_one_minute_load_per_cpu_before_ramp": float(
            resources.get("maximum_one_minute_load_per_cpu_before_ramp") or 0.0
        ),
        "allow_low_balance": bool(payload.get("operator_authorized_low_balance_start")),
        "allow_retired_key": bool(payload.get("operator_authorized_retired_key_start")),
    }
    actual = {
        "run_id": run_id,
        "shard_sha256": sha256_file(shard_file),
        "task_count": len(cases),
        "initial_workers": initial_workers,
        "max_workers": max_workers,
        "normal_completions_per_ramp": normal_completions_per_ramp,
        "worker_levels": ADAPTIVE_WORKER_LEVELS,
        "max_attempts": max_attempts,
        "consecutive_error_limit": consecutive_error_limit,
        "campaign_cost_cap_usd": campaign_cost_cap_usd,
        "per_slot_reserve_usd": per_slot_reserve_usd,
        "minimum_available_memory_after_ramp_gib": MINIMUM_AVAILABLE_MEMORY_AFTER_RAMP_GIB,
        "memory_reserve_per_added_worker_gib": MEMORY_RESERVE_PER_ADDED_WORKER_GIB,
        "maximum_one_minute_load_per_cpu_before_ramp": (
            MAXIMUM_ONE_MINUTE_LOAD_PER_CPU_BEFORE_RAMP
        ),
        "allow_low_balance": allow_low_balance,
        "allow_retired_key": allow_retired_key,
    }
    for key in (
        "run_id",
        "shard_sha256",
        "task_count",
        "initial_workers",
        "max_workers",
        "normal_completions_per_ramp",
        "worker_levels",
        "max_attempts",
        "consecutive_error_limit",
        "campaign_cost_cap_usd",
        "per_slot_reserve_usd",
        "minimum_available_memory_after_ramp_gib",
        "memory_reserve_per_added_worker_gib",
        "maximum_one_minute_load_per_cpu_before_ramp",
        "allow_low_balance",
        "allow_retired_key",
    ):
        if actual[key] != expected[key]:
            raise RuntimeError(f"fixed campaign policy changed at {key}; refusing any LM request")
    if (
        not allow_low_balance
        and confirmed_credit_balance_usd < expected["minimum_confirmed_shared_balance_usd"]
    ):
        raise RuntimeError("confirmed shared balance is below the immutable two-VPS minimum")
    return expected


def slot_payload(slot: Slot, *, seed_base: int) -> tuple[dict[str, Any], dict[str, Any]]:
    # Match the paper runs: every AppWorld record uses the same frozen seed.
    seed = seed_base
    job = {
        "schema_version": "job/v1",
        "job_id": f"full-appworld-{slot.case.task_id}-{slot.agent_slug}",
        "domain": "appworld",
        "case_unit_id": slot.case.task_id,
        "task_id": slot.case.task_id,
        "record_slot_id": f"slot-appworld-{slot.case.task_id}-{slot.agent_slug}",
        "agent_id": slot.agent_id,
        "provider": "openrouter",
        "model": slot.model,
        "phase": "full",
        "seed": seed,
        "global_case_index": slot.case.global_index,
        "dataset_name": slot.case.dataset_name,
    }
    source_entry = {
        "domain": "appworld",
        "task_id": slot.case.task_id,
        "dataset_name": slot.case.dataset_name,
        "source_ref": f"appworld://{slot.case.dataset_name}/{slot.case.task_id}",
    }
    return job, source_entry


def run_slot(
    slot: Slot,
    *,
    run_id: str,
    output_root: Path,
    logs_root: Path,
    appworld_root: Path,
    python_bin: Path,
    repo_root: Path,
    seed_base: int,
    max_attempts: int,
) -> dict[str, Any]:
    output_dir = output_root / slot.agent_slug / slot.case.task_id
    existing = completed_summary(output_dir)
    if existing is not None:
        return {
            "event": "slot_terminal",
            "status": "completed",
            "resume_reused": True,
            "slot_id": slot.slot_id,
            "task_id": slot.case.task_id,
            "global_index": slot.case.global_index,
            "dataset_name": slot.case.dataset_name,
            "agent_id": slot.agent_id,
            "model": slot.model,
            "native_success": existing.get("success"),
            "billed_cost_usd": 0.0,
            "attempt_count": 0,
            "ended_at": utc_now(),
        }

    job, source_entry = slot_payload(slot, seed_base=seed_base)
    experiment_name = f"{run_id}_{slot.agent_slug}_{slot.case.task_id}"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(repo_root / "src")
    environment["APPWORLD_ROOT"] = str(appworld_root)
    environment.setdefault("OPENAI_API_KEY", "unused-for-litellm")

    last_error: dict[str, Any] = {}
    for attempt in range(1, max_attempts + 1):
        stdout_path = logs_root / "workers" / slot.agent_slug / f"{slot.case.task_id}.attempt_{attempt:02d}.stdout.log"
        stderr_path = logs_root / "workers" / slot.agent_slug / f"{slot.case.task_id}.attempt_{attempt:02d}.stderr.log"
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        command = [
            str(python_bin),
            "-m",
            "evidence_system.adapters.appworld_official_worker",
            "--job-json",
            canonical_json(job),
            "--source-entry-json",
            canonical_json(source_entry),
            "--output-dir",
            str(output_dir),
            "--experiment-name",
            experiment_name,
            "--provider",
            "openrouter",
            "--model",
            slot.model,
            "--temperature",
            "0",
            "--max-tokens",
            "4096",
            "--openrouter-api-key-env",
            "OPENROUTER_API_KEY",
            "--max-steps",
            "50",
            "--lm-retry-after-seconds",
            "60",
            "--lm-max-retries",
            "1",
        ]
        started_at = utc_now()
        with stdout_path.open("w", encoding="utf-8") as stdout_handle, stderr_path.open(
            "w", encoding="utf-8"
        ) as stderr_handle:
            completed = subprocess.run(
                command,
                cwd=repo_root,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout_handle,
                stderr=stderr_handle,
                check=False,
            )
        summary = completed_summary(output_dir)
        if completed.returncode == 0 and summary is not None:
            return {
                "event": "slot_terminal",
                "status": "completed",
                "resume_reused": False,
                "slot_id": slot.slot_id,
                "task_id": slot.case.task_id,
                "global_index": slot.case.global_index,
                "dataset_name": slot.case.dataset_name,
                "agent_id": slot.agent_id,
                "model": slot.model,
                "native_success": summary.get("success"),
                "billed_cost_usd": billed_cost_usd(output_dir),
                "evaluation_pass_count": summary.get("evaluation_pass_count"),
                "attempt_count": attempt,
                "started_at": started_at,
                "ended_at": utc_now(),
                "output_dir": str(output_dir),
            }

        error_type = "WorkerProcessError"
        error_message = f"worker exit={completed.returncode} or required artifacts missing"
        summary_path = output_dir / "run_summary.json"
        if summary_path.is_file():
            try:
                raw_summary = json.loads(summary_path.read_text(encoding="utf-8"))
                error_type = str(raw_summary.get("error_type") or error_type)
                error_message = str(raw_summary.get("error_message") or error_message)
            except (OSError, json.JSONDecodeError):
                pass
        last_error = {
            "returncode": completed.returncode,
            "error_type": error_type,
            "error_message": error_message,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
        }
        # Automatic whole-task retries are disabled. A later explicit resume
        # keeps the fixed assignment, reuses completed slots, and runs only
        # the failed slot after its cause has been corrected.

    return {
        "event": "slot_terminal",
        "status": "error",
        "resume_reused": False,
        "slot_id": slot.slot_id,
        "task_id": slot.case.task_id,
        "global_index": slot.case.global_index,
        "dataset_name": slot.case.dataset_name,
        "agent_id": slot.agent_id,
        "model": slot.model,
        "attempt_count": max_attempts,
        "ended_at": utc_now(),
        "output_dir": str(output_dir),
        "billed_cost_usd": billed_cost_usd(output_dir),
        "fatal_error_reason": fatal_error_reason(
            str(last_error.get("error_type") or ""), str(last_error.get("error_message") or "")
        ),
        **last_error,
    }


def run_agent_batch(
    slots: list[Slot],
    *,
    initial_worker_limit: int,
    maximum_worker_limit: int,
    normal_completions_per_ramp: int,
    consecutive_error_limit: int,
    event_path: Path,
    issue_path: Path,
    state_path: Path,
    state: dict[str, Any],
    slot_kwargs: dict[str, Any],
    campaign_cost_cap_usd: float,
    per_slot_reserve_usd: float,
) -> bool:
    pending: Iterable[Slot] = iter(slots)
    futures: dict[Future[dict[str, Any]], Slot] = {}
    halted = False
    worker_levels = tuple(level for level in ADAPTIVE_WORKER_LEVELS if level <= maximum_worker_limit)
    if not worker_levels or worker_levels[0] != initial_worker_limit or worker_levels[-1] != maximum_worker_limit:
        raise RuntimeError("invalid adaptive worker levels")
    agent_id = slots[0].agent_id if slots else ""
    previously_validated_limit = initial_worker_limit
    if event_path.is_file():
        for raw_line in event_path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                prior_event = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            if prior_event.get("event") != "concurrency_ramp" or prior_event.get("agent_id") != agent_id:
                continue
            candidate = int(prior_event.get("to_workers") or 0)
            if candidate in worker_levels:
                previously_validated_limit = max(previously_validated_limit, candidate)
    worker_level_index = worker_levels.index(previously_validated_limit)
    successful_normal_since_ramp = 0
    deferred_targets: set[int] = set()
    state["current_worker_limit"] = previously_validated_limit
    state["peak_worker_limit"] = max(
        int(state.get("peak_worker_limit") or 0), previously_validated_limit
    )
    state["successful_normal_since_ramp"] = 0
    if previously_validated_limit > initial_worker_limit:
        append_jsonl(
            event_path,
            {
                "event": "concurrency_resume",
                "agent_id": agent_id,
                "workers": previously_validated_limit,
                "basis": "previously completed live concurrency ramp",
                "at": utc_now(),
            },
        )

    with ThreadPoolExecutor(max_workers=maximum_worker_limit, thread_name_prefix="appworld-slot") as pool:
        def submit_next() -> bool:
            nonlocal halted
            if halted:
                return False
            reserved = len(futures) * per_slot_reserve_usd
            if float(state["billed_cost_usd"]) + reserved + per_slot_reserve_usd > campaign_cost_cap_usd:
                halted = True
                state["halt_reason"] = "campaign cost cap reached before scheduling another fixed slot"
                return False
            try:
                slot = next(pending)
            except StopIteration:
                return False
            futures[pool.submit(run_slot, slot, **slot_kwargs)] = slot
            return True

        for _ in range(min(previously_validated_limit, len(slots))):
            submit_next()

        while futures:
            done, _ = wait(futures, return_when=FIRST_COMPLETED)
            for future in done:
                slot = futures.pop(future)
                try:
                    result = future.result()
                except BaseException as exc:  # Keep the rest of the shard alive.
                    result = {
                        "event": "slot_terminal",
                        "status": "error",
                        "slot_id": slot.slot_id,
                        "task_id": slot.case.task_id,
                        "global_index": slot.case.global_index,
                        "dataset_name": slot.case.dataset_name,
                        "agent_id": slot.agent_id,
                        "model": slot.model,
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                        "attempt_count": 0,
                        "ended_at": utc_now(),
                    }
                append_jsonl(event_path, result)
                state["terminal_count"] += 1
                state["last_event"] = result
                state["billed_cost_usd"] = round(
                    float(state["billed_cost_usd"]) + float(result.get("billed_cost_usd") or 0.0), 12
                )
                if result["status"] == "completed":
                    state["completed_count"] += 1
                    state["consecutive_errors"] = 0
                    if result.get("native_success") is True:
                        state["native_success_count"] += 1
                    elif result.get("native_success") is False:
                        state["native_fail_count"] += 1
                    if (
                        result.get("dataset_name") == "test_normal"
                        and not result.get("resume_reused")
                    ):
                        successful_normal_since_ramp += 1
                        state["successful_normal_since_ramp"] = successful_normal_since_ramp
                        if (
                            successful_normal_since_ramp >= normal_completions_per_ramp
                            and worker_level_index + 1 < len(worker_levels)
                        ):
                            previous_limit = worker_levels[worker_level_index]
                            new_limit = worker_levels[worker_level_index + 1]
                            health = ramp_health_snapshot(previous_limit, new_limit)
                            if health["allowed"]:
                                worker_level_index += 1
                                successful_normal_since_ramp = 0
                                deferred_targets.discard(new_limit)
                                state["current_worker_limit"] = new_limit
                                state["peak_worker_limit"] = max(
                                    int(state.get("peak_worker_limit") or 0), new_limit
                                )
                                state["successful_normal_since_ramp"] = 0
                                state["last_ramp_health"] = health
                                append_jsonl(
                                    event_path,
                                    {
                                        "event": "concurrency_ramp",
                                        "agent_id": slot.agent_id,
                                        "from_workers": previous_limit,
                                        "to_workers": new_limit,
                                        "trigger": (
                                            f"{normal_completions_per_ramp} completed test_normal slots "
                                            "with no terminal infrastructure error"
                                        ),
                                        "health": health,
                                        "at": utc_now(),
                                    },
                                )
                            elif new_limit not in deferred_targets:
                                deferred_targets.add(new_limit)
                                state["last_ramp_health"] = health
                                append_jsonl(
                                    event_path,
                                    {
                                        "event": "concurrency_ramp_deferred",
                                        "agent_id": slot.agent_id,
                                        "from_workers": previous_limit,
                                        "to_workers": new_limit,
                                        "reason": "resource health gate",
                                        "health": health,
                                        "at": utc_now(),
                                    },
                                )
                else:
                    state["error_count"] += 1
                    state["consecutive_errors"] += 1
                    append_jsonl(issue_path, result)
                    if result.get("fatal_error_reason"):
                        halted = True
                        state["halt_reason"] = f"fatal worker error: {result['fatal_error_reason']}"
                    elif state["consecutive_errors"] >= consecutive_error_limit:
                        halted = True
                        state["halt_reason"] = (
                            f"{state['consecutive_errors']} consecutive terminal infrastructure errors"
                        )
                state["updated_at"] = utc_now()
                if not halted:
                    while len(futures) < int(state["current_worker_limit"]):
                        if not submit_next():
                            break
                state["active_count"] = len(futures)
                write_json(state_path, state)

    return halted


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--vps-id", required=True, choices=("vps1", "vps2"))
    parser.add_argument("--shard-file", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--appworld-root", type=Path, required=True)
    parser.add_argument("--python-bin", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--initial-workers", type=int, default=6)
    parser.add_argument("--max-workers", type=int, default=72)
    parser.add_argument("--normal-completions-per-ramp", type=int, default=12)
    parser.add_argument("--seed-base", type=int, default=7)
    parser.add_argument("--max-attempts", type=int, default=1)
    parser.add_argument("--consecutive-error-limit", type=int, default=1)
    parser.add_argument("--campaign-cost-cap-usd", type=float, required=True)
    parser.add_argument("--confirmed-credit-balance-usd", type=float, required=True)
    parser.add_argument("--per-slot-reserve-usd", type=float, default=3.0)
    parser.add_argument("--allow-low-balance", action="store_true")
    parser.add_argument("--allow-retired-key", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not SAFE_ID.fullmatch(args.run_id):
        raise ValueError("run-id contains unsafe characters")
    if args.initial_workers < 1 or args.max_workers < 1 or args.consecutive_error_limit < 1:
        raise ValueError("worker, attempt, and error limits must be positive")
    if args.max_attempts != 1:
        raise ValueError("max-attempts must be 1; automatic whole-task retries are disabled")
    if args.normal_completions_per_ramp < 1:
        raise ValueError("normal-completions-per-ramp must be positive")
    if args.initial_workers != ADAPTIVE_WORKER_LEVELS[0] or args.max_workers != ADAPTIVE_WORKER_LEVELS[-1]:
        raise ValueError("adaptive concurrency must start at 6 and end at 72")
    if args.max_workers > 72:
        raise ValueError("max-workers above 72 is disabled")
    if args.campaign_cost_cap_usd <= 0 or args.per_slot_reserve_usd <= 0:
        raise ValueError("campaign cost cap and per-slot reserve must be positive")
    if (
        not args.allow_low_balance
        and args.confirmed_credit_balance_usd < args.campaign_cost_cap_usd + args.per_slot_reserve_usd
    ):
        raise ValueError("confirmed credit balance must cover the campaign cap plus one slot reserve")
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise RuntimeError("OPENROUTER_API_KEY is missing")
    if not args.python_bin.is_file() or not args.appworld_root.is_dir():
        raise RuntimeError("AppWorld runtime is not ready")

    cases = load_cases(args.shard_file)
    root = args.output_root
    outputs_root = root / "outputs"
    logs_root = root / "logs"
    control_root = root / "control"
    event_path = control_root / "events.jsonl"
    issue_path = control_root / "issues.jsonl"
    state_path = control_root / "state.json"
    # Keep the handle alive for the whole process. This prevents two launchers
    # from issuing duplicate paid requests against the same fixed shard.
    campaign_lock_handle = acquire_campaign_lock(control_root / "launcher.lock")
    api_key = str(os.environ["OPENROUTER_API_KEY"])
    retired_key_path = control_root / "retired_openrouter_key.sha256"
    if retired_key_path.is_file():
        retired_fingerprints = {
            line.strip() for line in retired_key_path.read_text(encoding="utf-8").splitlines() if line.strip()
        }
        if sha256_text(api_key) in retired_fingerprints and not args.allow_retired_key:
            raise RuntimeError("refusing the retired API key exposed by the earlier run")
    fixed_policy = validate_fixed_campaign_policy(
        control_root / "fixed_assignment_manifest.json",
        run_id=args.run_id,
        vps_id=args.vps_id,
        shard_file=args.shard_file,
        cases=cases,
        initial_workers=args.initial_workers,
        max_workers=args.max_workers,
        normal_completions_per_ramp=args.normal_completions_per_ramp,
        max_attempts=args.max_attempts,
        consecutive_error_limit=args.consecutive_error_limit,
        campaign_cost_cap_usd=args.campaign_cost_cap_usd,
        confirmed_credit_balance_usd=args.confirmed_credit_balance_usd,
        per_slot_reserve_usd=args.per_slot_reserve_usd,
        allow_low_balance=args.allow_low_balance,
        allow_retired_key=args.allow_retired_key,
    )
    lock_assignment(
        control_root / "assignment_lock.json",
        run_id=args.run_id,
        vps_id=args.vps_id,
        shard_file=args.shard_file,
        cases=cases,
    )
    key_preflight = validate_openrouter_key(api_key)
    limit_remaining = key_preflight.get("limit_remaining")
    if limit_remaining is not None and float(limit_remaining) < args.campaign_cost_cap_usd:
        raise RuntimeError("OpenRouter key limit remaining is below the requested campaign cost cap")
    write_json(control_root / "openrouter_key_preflight.json", key_preflight)
    credits_preflight = validate_openrouter_credits(api_key)
    required_shared_balance = float(fixed_policy["minimum_confirmed_shared_balance_usd"])
    if (
        credits_preflight["available_balance_usd"] < required_shared_balance
        and not args.allow_low_balance
    ):
        raise RuntimeError(
            "OpenRouter account balance is below the immutable two-VPS minimum; "
            "no LM request was made"
        )
    write_json(control_root / "openrouter_credits_preflight.json", credits_preflight)
    preflight = run_zero_lm_preflight(
        python_bin=args.python_bin,
        repo_root=args.repo_root,
        appworld_root=args.appworld_root,
        shard_file=args.shard_file,
        control_root=control_root,
    )
    campaign_manifest = {
        "schema_version": "appworld_full_585_campaign/v1",
        "run_id": args.run_id,
        "vps_id": args.vps_id,
        "created_at": utc_now(),
        "case_count": len(cases),
        "record_slot_count": len(cases) * len(AGENTS),
        "first_global_index": cases[0].global_index,
        "last_global_index": cases[-1].global_index,
        "first_task_id": cases[0].task_id,
        "last_task_id": cases[-1].task_id,
        "shard_file": str(args.shard_file),
        "shard_file_sha256": sha256_file(args.shard_file),
        "agents": [
            {"agent_id": agent_id, "agent_slug": agent_slug, "provider": "openrouter", "model": model}
            for agent_id, agent_slug, model in AGENTS
        ],
        "official_agent": "simplified_react_code_agent",
        "official_commit": "a072b7a86e7c1d5b1d7175659d750ebb9b79f10a",
        "max_steps": 50,
        "max_tokens": 4096,
        "temperature": 0,
        "seed_base": args.seed_base,
        "max_workers": args.max_workers,
        "initial_workers": args.initial_workers,
        "worker_levels": list(ADAPTIVE_WORKER_LEVELS),
        "normal_completions_per_ramp": args.normal_completions_per_ramp,
        "max_attempts": args.max_attempts,
        "consecutive_error_limit": args.consecutive_error_limit,
        "campaign_cost_cap_usd": args.campaign_cost_cap_usd,
        "confirmed_credit_balance_usd": args.confirmed_credit_balance_usd,
        "per_slot_reserve_usd": args.per_slot_reserve_usd,
        "operator_authorized_low_balance_start": args.allow_low_balance,
        "operator_authorized_retired_key_start": args.allow_retired_key,
        "resource_ramp_policy": {
            "minimum_available_memory_after_ramp_gib": (
                MINIMUM_AVAILABLE_MEMORY_AFTER_RAMP_GIB
            ),
            "memory_reserve_per_added_worker_gib": MEMORY_RESERVE_PER_ADDED_WORKER_GIB,
            "maximum_one_minute_load_per_cpu_before_ramp": (
                MAXIMUM_ONE_MINUTE_LOAD_PER_CPU_BEFORE_RAMP
            ),
        },
        "automatic_lm_attempts": 1,
        "automatic_task_attempts": 1,
        "runtime_preflight": preflight,
        "openrouter_key_preflight": key_preflight,
        "openrouter_credits_preflight": credits_preflight,
        "fixed_campaign_policy": fixed_policy,
        "launcher_path": str(Path(__file__).resolve()),
        "launcher_sha256": sha256_file(Path(__file__).resolve()),
    }
    write_json(control_root / "campaign_manifest.json", campaign_manifest)
    append_jsonl(event_path, {"event": "campaign_start", **campaign_manifest})

    prior_billed_cost_usd = max(
        existing_shard_cost_usd(outputs_root, cases),
        prior_campaign_cost_usd(state_path, run_id=args.run_id, vps_id=args.vps_id),
    )
    if prior_billed_cost_usd + args.per_slot_reserve_usd > args.campaign_cost_cap_usd:
        raise RuntimeError("existing shard cost leaves less than one slot reserve under the campaign cap")
    state: dict[str, Any] = {
        "schema_version": "appworld_full_585_campaign_state/v1",
        "run_id": args.run_id,
        "vps_id": args.vps_id,
        "status": "running",
        "started_at": utc_now(),
        "updated_at": utc_now(),
        "case_count": len(cases),
        "record_slot_count": len(cases) * len(AGENTS),
        "initial_workers": args.initial_workers,
        "maximum_workers": args.max_workers,
        "current_worker_limit": args.initial_workers,
        "peak_worker_limit": args.initial_workers,
        "successful_normal_since_ramp": 0,
        "last_ramp_health": None,
        "active_agent_id": None,
        "active_count": 0,
        "terminal_count": 0,
        "completed_count": 0,
        "error_count": 0,
        "native_success_count": 0,
        "native_fail_count": 0,
        "consecutive_errors": 0,
        "billed_cost_usd": round(prior_billed_cost_usd, 12),
        "prior_billed_cost_usd": round(prior_billed_cost_usd, 12),
        "halt_reason": None,
        "last_event": None,
    }
    write_json(state_path, state)

    common = {
        "run_id": args.run_id,
        "output_root": outputs_root,
        "logs_root": logs_root,
        "appworld_root": args.appworld_root,
        "python_bin": args.python_bin,
        "repo_root": args.repo_root,
        "seed_base": args.seed_base,
        "max_attempts": args.max_attempts,
    }
    halted = False
    for agent_id, agent_slug, model in AGENTS:
        state["active_agent_id"] = agent_id
        state["updated_at"] = utc_now()
        write_json(state_path, state)
        slots = [Slot(case=case, agent_id=agent_id, agent_slug=agent_slug, model=model) for case in cases]
        halted = run_agent_batch(
            slots,
            initial_worker_limit=args.initial_workers,
            maximum_worker_limit=args.max_workers,
            normal_completions_per_ramp=args.normal_completions_per_ramp,
            consecutive_error_limit=args.consecutive_error_limit,
            event_path=event_path,
            issue_path=issue_path,
            state_path=state_path,
            state=state,
            slot_kwargs=common,
            campaign_cost_cap_usd=args.campaign_cost_cap_usd,
            per_slot_reserve_usd=args.per_slot_reserve_usd,
        )
        if halted:
            break

    state["active_agent_id"] = None
    state["active_count"] = 0
    state["updated_at"] = utc_now()
    state["ended_at"] = utc_now()
    state["status"] = "halted" if halted else "completed"
    write_json(state_path, state)
    append_jsonl(
        event_path,
        {
            "event": "campaign_terminal",
            "status": state["status"],
            "terminal_count": state["terminal_count"],
            "completed_count": state["completed_count"],
            "error_count": state["error_count"],
            "native_success_count": state["native_success_count"],
            "native_fail_count": state["native_fail_count"],
            "billed_cost_usd": state["billed_cost_usd"],
            "halt_reason": state["halt_reason"],
            "ended_at": state["ended_at"],
        },
    )
    return 2 if halted else 0


if __name__ == "__main__":
    raise SystemExit(main())
