#!/usr/bin/env python3
"""Read-only, record-by-record audit of the two-VPS AppWorld 585 campaign.

The script has a local controller mode and a remote worker mode.  Controller
mode sends this source over SSH, receives only sanitized metadata, and writes
JSON/JSONL/CSV/Markdown audit artifacts locally.  It never copies prompts,
responses, credentials, synthetic account data, or database contents.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Iterable, Mapping


RUN_ID = "appworld585_20260719_full_v1"
OFFICIAL_COMMIT = "a072b7a86e7c1d5b1d7175659d750ebb9b79f10a"
LAUNCHER_SHA256 = "07c891f4f70f3df8ba92a49537fade6b69c027ec4a8ee513753db57f60ddbc61"
AGENTS: dict[str, dict[str, str]] = {
    "agent_a": {"agent_id": "Agent A", "model": "openai/gpt-5.4"},
    "agent_b": {"agent_id": "Agent B", "model": "anthropic/claude-opus-4.7"},
    "agent_c": {"agent_id": "Agent C", "model": "deepseek/deepseek-v4-pro"},
}
TOP_JSON_FILES = (
    "run_summary.json",
    "job.json",
    "source_bundle_entry.json",
    "worker_config.json",
    "official_runner_config.json",
    "native_evaluator_input.json",
    "native_evaluator_output.json",
    "artifact_manifest.json",
)
NESTED_REQUIRED = (
    "appworld_task_output/logs/api_calls.jsonl",
    "appworld_task_output/logs/lm_calls.jsonl",
    "appworld_task_output/logs/logger.jsonl",
    "appworld_task_output/logs/logger.log",
    "appworld_task_output/logs/environment_io.md",
    "appworld_task_output/evaluation/report.md",
    "appworld_task_output/evaluation/version.txt",
    "appworld_task_output/misc/finished",
    "appworld_task_output/misc/usage.json",
    "appworld_task_output/version/code.txt",
    "appworld_task_output/version/data.txt",
    "appworld_task_output/dbs/model_hashes.json",
    "appworld_task_output/dbs/supervisor.jsonl",
)
NONEMPTY_NESTED = tuple(path for path in NESTED_REQUIRED if not path.endswith("/finished"))
MISSING_TABLE_RE = re.compile(r"no such table:\s*([A-Za-z0-9_]+)", re.IGNORECASE)
MISSING_COLUMN_RE = re.compile(r"no such column:\s*([A-Za-z0-9_.]+)", re.IGNORECASE)
INSERT_MISSING_COLUMN_RE = re.compile(
    r"table\s+([A-Za-z0-9_]+)\s+has no column named\s+([A-Za-z0-9_]+)", re.IGNORECASE
)
EXCEPTION_LINE_RE = re.compile(
    r"(?m)^([A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception)):\s*([^\n]*)$"
)
KNOWN_INFRA_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("sqlite_missing_table", re.compile(r"no such table:", re.IGNORECASE)),
    ("sqlite_missing_column", re.compile(r"no such column:", re.IGNORECASE)),
    (
        "sqlite_insert_column_mismatch",
        re.compile(r"table\s+[A-Za-z0-9_]+\s+has no column named\s+[A-Za-z0-9_]+", re.IGNORECASE),
    ),
    ("sqlite_database_locked", re.compile(r"database is locked", re.IGNORECASE)),
    ("sqlite_open_failure", re.compile(r"unable to open database", re.IGNORECASE)),
    ("missing_runtime_file", re.compile(r"FileNotFoundError:.*(?:appworld|api_docs|/data/)", re.IGNORECASE)),
    ("module_import_failure", re.compile(r"(?:ModuleNotFoundError|ImportError):", re.IGNORECASE)),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path, issues: list[str], label: str) -> dict[str, Any]:
    if not path.is_file():
        issues.append(f"missing:{label}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        issues.append(f"invalid_json:{label}:{type(exc).__name__}")
        return {}
    if not isinstance(value, dict):
        issues.append(f"not_object:{label}")
        return {}
    return value


def iter_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any] | None, str | None]]:
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                yield line_number, None, "blank_line"
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                yield line_number, None, "json_decode"
                continue
            if not isinstance(value, dict):
                yield line_number, None, "not_object"
                continue
            yield line_number, value, None


def nested_get(value: Mapping[str, Any], *path: str) -> Any:
    current: Any = value
    for key in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def check_equal(
    issues: list[str], label: str, actual: Any, expected: Any, *, allow_none: bool = False
) -> None:
    if allow_none and actual is None:
        return
    if actual != expected:
        issues.append(f"mismatch:{label}:actual={actual!r}:expected={expected!r}")


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    seen_tasks: set[str] = set()
    seen_indices: set[int] = set()
    for line_number, value, error in iter_jsonl(path):
        if error or value is None:
            raise RuntimeError(f"invalid shard line {line_number}: {error}")
        task_id = str(value.get("task_id") or "")
        dataset_name = str(value.get("dataset_name") or "")
        global_index = int(value.get("global_index") or 0)
        if not task_id or dataset_name not in {"test_normal", "test_challenge"} or global_index < 1:
            raise RuntimeError(f"invalid shard payload at line {line_number}")
        if task_id in seen_tasks or global_index in seen_indices:
            raise RuntimeError(f"duplicate shard task/index at line {line_number}")
        seen_tasks.add(task_id)
        seen_indices.add(global_index)
        cases.append(
            {"task_id": task_id, "dataset_name": dataset_name, "global_index": global_index}
        )
    return cases


def load_event_history(control_root: Path) -> dict[str, list[dict[str, Any]]]:
    histories: dict[str, list[dict[str, Any]]] = defaultdict(list)
    events_path = control_root / "events.jsonl"
    if not events_path.is_file():
        return histories
    for _, value, error in iter_jsonl(events_path):
        if error or value is None or value.get("event") != "slot_terminal":
            continue
        slot_id = str(value.get("slot_id") or "")
        if slot_id:
            histories[slot_id].append(value)
    return histories


def load_attempt_failure_reasons(logs_root: Path) -> dict[str, list[str]]:
    failures: dict[str, list[str]] = defaultdict(list)
    pattern = re.compile(r"^(?P<task>.+)\.attempt_(?P<attempt>\d+)\.stdout\.log$")
    for path in sorted(logs_root.glob("agent_*/*.stdout.log")):
        match = pattern.match(path.name)
        if not match:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if '"status": "error"' not in text:
            continue
        if "Insufficient credits" in text and ("code\":402" in text or "402 Payment Required" in text):
            reason = "openrouter_402_insufficient_credits"
        elif "FileNotFoundError" in text and "api_docs/standard/api_docs.json" in text:
            reason = "missing_generated_api_docs_file"
        elif '"error_type": "APIError"' in text:
            reason = "other_model_api_error"
        elif '"error_type": "FileNotFoundError"' in text:
            reason = "other_missing_file"
        else:
            error_match = re.search(r'"error_type"\s*:\s*"([^"]+)"', text)
            reason = f"other:{error_match.group(1) if error_match else 'unknown'}"
        agent_slug = path.parent.name
        slot_id = f"{agent_slug}__{match.group('task')}"
        failures[slot_id].append(reason)
    return failures


def parse_lm_log(path: Path, expected_model: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "line_count": 0,
        "invalid_line_count": 0,
        "response_count": 0,
        "response_with_content_count": 0,
        "credential_field_count": 0,
        "input_models": Counter(),
        "output_models": Counter(),
        "providers": Counter(),
        "finish_reasons": Counter(),
        "first_response_start": None,
        "last_response_end": None,
    }
    if not path.is_file():
        return result
    for _, value, error in iter_jsonl(path):
        result["line_count"] += 1
        if error or value is None:
            result["invalid_line_count"] += 1
            continue
        request = value.get("input")
        response = value.get("output")
        if isinstance(request, Mapping):
            input_model = str(request.get("model") or "")
            if input_model:
                result["input_models"][input_model] += 1
            # Record only presence.  Never return, hash, or print credential values.
            if "api_key" in request and bool(request.get("api_key")):
                result["credential_field_count"] += 1
        if isinstance(response, Mapping):
            result["response_count"] += 1
            output_model = str(response.get("model") or "")
            if output_model:
                result["output_models"][output_model] += 1
            provider = str(response.get("provider") or "")
            if provider:
                result["providers"][provider] += 1
            choices = response.get("choices")
            if isinstance(choices, list):
                for choice in choices:
                    if not isinstance(choice, Mapping):
                        continue
                    finish_reason = str(choice.get("finish_reason") or "")
                    if finish_reason:
                        result["finish_reasons"][finish_reason] += 1
                    message = choice.get("message")
                    content = message.get("content") if isinstance(message, Mapping) else None
                    if isinstance(content, str) and content.strip():
                        result["response_with_content_count"] += 1
                        break
            timestamps = response.get("timestamps")
            if isinstance(timestamps, Mapping):
                start = timestamps.get("start")
                end = timestamps.get("end")
                if start is not None and result["first_response_start"] is None:
                    result["first_response_start"] = str(start)
                if end is not None:
                    result["last_response_end"] = str(end)
    result["input_models"] = dict(sorted(result["input_models"].items()))
    result["output_models"] = dict(sorted(result["output_models"].items()))
    result["providers"] = dict(sorted(result["providers"].items()))
    result["finish_reasons"] = dict(sorted(result["finish_reasons"].items()))
    expected = f"openrouter/{expected_model}"
    result["all_input_models_expected"] = set(result["input_models"]) == ({expected} if result["line_count"] else set())
    result["all_output_models_expected"] = all(
        model == expected_model or model.endswith("/" + expected_model)
        for model in result["output_models"]
    ) and bool(result["output_models"])
    return result


def parse_api_log(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "line_count": 0,
        "invalid_line_count": 0,
        "supervisor_completion_count": 0,
        "action_call_count": 0,
        "last_url": None,
        "apps": Counter(),
    }
    if not path.is_file():
        return result
    for _, value, error in iter_jsonl(path):
        result["line_count"] += 1
        if error or value is None:
            result["invalid_line_count"] += 1
            continue
        url = str(value.get("url") or "")
        result["last_url"] = url or result["last_url"]
        segments = [segment for segment in url.split("/") if segment]
        app = segments[0] if segments else ""
        if app:
            result["apps"][app] += 1
        if url == "/supervisor/message" and str(value.get("method") or "").lower() == "post":
            result["supervisor_completion_count"] += 1
        if app and app not in {"api_docs", "supervisor"}:
            result["action_call_count"] += 1
    result["apps"] = dict(sorted(result["apps"].items()))
    return result


def audit_record(
    *,
    campaign_root: Path,
    vps_id: str,
    case: Mapping[str, Any],
    agent_slug: str,
    event_history: list[dict[str, Any]],
    attempt_failure_reasons: list[str],
) -> dict[str, Any]:
    task_id = str(case["task_id"])
    dataset_name = str(case["dataset_name"])
    global_index = int(case["global_index"])
    agent = AGENTS[agent_slug]
    expected_model = agent["model"]
    output_dir = campaign_root / "outputs" / agent_slug / task_id
    issues: list[str] = []
    warnings: list[str] = []

    if not output_dir.is_dir():
        issues.append("missing:output_dir")

    payloads = {
        filename: read_json(output_dir / filename, issues, filename)
        for filename in TOP_JSON_FILES
    }
    for relative in NESTED_REQUIRED:
        if not (output_dir / relative).is_file():
            issues.append(f"missing:{relative}")
    for relative in NONEMPTY_NESTED:
        path = output_dir / relative
        if path.is_file() and path.stat().st_size == 0:
            issues.append(f"empty:{relative}")
    db_dir = output_dir / "appworld_task_output" / "dbs"
    if not db_dir.is_dir():
        issues.append("missing:appworld_task_output/dbs")

    summary = payloads["run_summary.json"]
    job = payloads["job.json"]
    source = payloads["source_bundle_entry.json"]
    worker = payloads["worker_config.json"]
    runner = payloads["official_runner_config.json"]
    native_input = payloads["native_evaluator_input.json"]
    native_output = payloads["native_evaluator_output.json"]
    artifact_manifest = payloads["artifact_manifest.json"]

    expected_experiment = f"{RUN_ID}_{agent_slug}_{task_id}"
    expected_job_id = f"full-appworld-{task_id}-{agent_slug}"
    expected_source_ref = f"appworld://{dataset_name}/{task_id}"
    expected_model_id = f"openrouter/{expected_model}"

    check_equal(issues, "summary.status", summary.get("status"), "completed")
    check_equal(issues, "summary.task_id", summary.get("task_id"), task_id)
    check_equal(issues, "summary.dataset_name", summary.get("dataset_name"), dataset_name)
    check_equal(issues, "summary.job_id", summary.get("job_id"), expected_job_id)
    check_equal(issues, "summary.experiment_name", summary.get("experiment_name"), expected_experiment)
    check_equal(issues, "summary.provider", summary.get("provider"), "openrouter")
    check_equal(issues, "summary.model", summary.get("model"), expected_model)
    check_equal(issues, "summary.official_agent_name", summary.get("official_agent_name"), "simplified_react_code_agent")
    check_equal(issues, "summary.official_prompt_path", summary.get("official_prompt_path"), "react_code_agent/instructions.txt")
    check_equal(issues, "summary.max_steps", summary.get("max_steps"), 50)
    check_equal(issues, "summary.compatibility_mode", summary.get("compatibility_mode"), "locked_data_runtime_patch")
    check_equal(issues, "summary.data_version", summary.get("data_version"), "0.1.0")

    check_equal(issues, "job.agent_id", job.get("agent_id"), agent["agent_id"])
    check_equal(issues, "job.task_id", job.get("task_id"), task_id)
    check_equal(issues, "job.case_unit_id", job.get("case_unit_id"), task_id)
    check_equal(issues, "job.dataset_name", job.get("dataset_name"), dataset_name)
    check_equal(issues, "job.global_case_index", job.get("global_case_index"), global_index)
    check_equal(issues, "job.job_id", job.get("job_id"), expected_job_id)
    check_equal(issues, "job.model", job.get("model"), expected_model)
    check_equal(issues, "job.provider", job.get("provider"), "openrouter")
    check_equal(issues, "job.phase", job.get("phase"), "full")
    check_equal(issues, "job.seed", job.get("seed"), 7)

    check_equal(issues, "source.task_id", source.get("task_id"), task_id)
    check_equal(issues, "source.dataset_name", source.get("dataset_name"), dataset_name)
    check_equal(issues, "source.source_ref", source.get("source_ref"), expected_source_ref)
    check_equal(issues, "source.domain", source.get("domain"), "appworld")

    check_equal(issues, "worker.experiment_name", worker.get("experiment_name"), expected_experiment)
    check_equal(issues, "worker.model", worker.get("model"), expected_model)
    check_equal(issues, "worker.provider", worker.get("provider"), "openrouter")
    check_equal(issues, "worker.temperature", worker.get("temperature"), 0.0)
    check_equal(issues, "worker.max_tokens", worker.get("max_tokens"), 4096)
    check_equal(issues, "worker.max_steps", worker.get("max_steps"), 50)

    check_equal(issues, "runner.dataset", runner.get("dataset"), dataset_name)
    check_equal(issues, "runner.agent.type", nested_get(runner, "agent", "type"), "simplified_react_code_agent")
    check_equal(issues, "runner.agent.max_steps", nested_get(runner, "agent", "max_steps"), 50)
    check_equal(issues, "runner.model.name", nested_get(runner, "agent", "model_config", "name"), expected_model_id)
    check_equal(issues, "runner.model.client_name", nested_get(runner, "agent", "model_config", "client_name"), "litellm")
    check_equal(issues, "runner.model.api_type", nested_get(runner, "agent", "model_config", "api_type"), "chat_completions")
    check_equal(issues, "runner.model.temperature", nested_get(runner, "agent", "model_config", "temperature"), 0.0)
    check_equal(issues, "runner.model.max_tokens", nested_get(runner, "agent", "model_config", "max_tokens"), 4096)
    check_equal(issues, "runner.model.seed", nested_get(runner, "agent", "model_config", "seed"), 7)
    check_equal(issues, "runner.model.use_cache", nested_get(runner, "agent", "model_config", "use_cache"), False)
    check_equal(issues, "runner.agent.log_lm_calls", nested_get(runner, "agent", "log_lm_calls"), True)

    check_equal(issues, "native_input.task_id", native_input.get("task_id"), task_id)
    check_equal(issues, "native_input.dataset_name", native_input.get("dataset_name"), dataset_name)
    check_equal(issues, "native_input.experiment_name", native_input.get("experiment_name"), expected_experiment)
    check_equal(issues, "native_input.source_ref", native_input.get("source_ref"), expected_source_ref)
    check_equal(issues, "native_input.model_id", native_input.get("model_id"), expected_model_id)
    check_equal(issues, "native_input.official_agent_name", native_input.get("official_agent_name"), "simplified_react_code_agent")

    check_equal(issues, "native_output.task_id", native_output.get("task_id"), task_id)
    check_equal(issues, "native_output.dataset_name", native_output.get("dataset_name"), dataset_name)
    check_equal(issues, "native_output.experiment_name", native_output.get("experiment_name"), expected_experiment)
    tracker = native_output.get("tracker") if isinstance(native_output.get("tracker"), Mapping) else {}
    passes = tracker.get("passes") if isinstance(tracker.get("passes"), list) else []
    failures = tracker.get("failures") if isinstance(tracker.get("failures"), list) else []
    check_equal(issues, "tracker.num_tests", tracker.get("num_tests"), len(passes) + len(failures))
    check_equal(issues, "summary.evaluation_pass_count", summary.get("evaluation_pass_count"), len(passes))
    check_equal(issues, "summary.success", summary.get("success"), tracker.get("success"))
    check_equal(issues, "manifest.task_id", artifact_manifest.get("task_id"), task_id)
    check_equal(issues, "manifest.dataset_name", artifact_manifest.get("dataset_name"), dataset_name)
    check_equal(issues, "manifest.experiment_name", artifact_manifest.get("experiment_name"), expected_experiment)
    check_equal(issues, "manifest.evaluation_success", artifact_manifest.get("evaluation_success"), tracker.get("success"))

    evaluation_version_path = output_dir / "appworld_task_output" / "evaluation" / "version.txt"
    code_version_path = output_dir / "appworld_task_output" / "version" / "code.txt"
    data_version_path = output_dir / "appworld_task_output" / "version" / "data.txt"
    evaluation_version = evaluation_version_path.read_text(encoding="utf-8", errors="replace").strip() if evaluation_version_path.is_file() else ""
    code_version = code_version_path.read_text(encoding="utf-8", errors="replace").strip() if code_version_path.is_file() else ""
    data_version = data_version_path.read_text(encoding="utf-8", errors="replace").strip() if data_version_path.is_file() else ""
    check_equal(issues, "output.data_version", data_version, "0.1.0")
    if not code_version.startswith("0.2.0"):
        issues.append(f"mismatch:output.code_version:actual={code_version!r}:expected_prefix='0.2.0'")

    lm_path = output_dir / "appworld_task_output" / "logs" / "lm_calls.jsonl"
    api_path = output_dir / "appworld_task_output" / "logs" / "api_calls.jsonl"
    environment_path = output_dir / "appworld_task_output" / "logs" / "environment_io.md"
    lm = parse_lm_log(lm_path, expected_model)
    api = parse_api_log(api_path)
    environment_text = environment_path.read_text(encoding="utf-8", errors="replace") if environment_path.is_file() else ""
    environment_interaction_count = len(re.findall(r"(?m)^### Environment Interaction \d+\s*$", environment_text))
    missing_tables = sorted(set(MISSING_TABLE_RE.findall(environment_text)))
    missing_columns = sorted(set(MISSING_COLUMN_RE.findall(environment_text)))
    insert_missing_columns = sorted(
        {f"{table}.{column}" for table, column in INSERT_MISSING_COLUMN_RE.findall(environment_text)}
    )
    exception_lines = EXCEPTION_LINE_RE.findall(environment_text)
    exception_types = dict(sorted(Counter(kind for kind, _ in exception_lines).items()))
    infra_signatures = {
        label: len(pattern.findall(environment_text))
        for label, pattern in KNOWN_INFRA_PATTERNS
        if pattern.search(environment_text)
    }

    if lm["line_count"] < 1:
        issues.append("no_lm_calls")
    if lm["invalid_line_count"]:
        issues.append(f"invalid_lm_jsonl_lines:{lm['invalid_line_count']}")
    if lm["response_count"] != lm["line_count"]:
        issues.append(f"lm_response_count_mismatch:{lm['response_count']}/{lm['line_count']}")
    empty_assistant_content_count = lm["line_count"] - lm["response_with_content_count"]
    if empty_assistant_content_count:
        # DeepSeek sometimes returns a reasoning-only message with content=null.
        # The official runner records and executes this as an empty/no-op turn.
        # That is model behavior, not a malformed run record.
        warnings.append("reasoning_only_or_empty_assistant_turn")
    if not lm["all_input_models_expected"]:
        issues.append("lm_input_model_mismatch")
    if not lm["all_output_models_expected"]:
        issues.append("lm_output_model_mismatch")
    if lm["credential_field_count"]:
        warnings.append("plaintext_api_key_in_lm_log")
    if api["line_count"] < 1:
        issues.append("no_api_calls")
    if api["invalid_line_count"]:
        issues.append(f"invalid_api_jsonl_lines:{api['invalid_line_count']}")
    if environment_interaction_count < 1:
        issues.append("no_environment_interactions")
    if api["supervisor_completion_count"] < 1:
        warnings.append("agent_did_not_call_supervisor_complete_task")
    if infra_signatures:
        warnings.extend(f"runtime_infra:{label}" for label in sorted(infra_signatures))
    if attempt_failure_reasons:
        warnings.append("recovered_worker_attempt_failure")

    db_files = sorted(db_dir.glob("*.jsonl")) if db_dir.is_dir() else []
    db_nonempty_files = [path.name for path in db_files if path.stat().st_size > 0]
    db_total_bytes = sum(path.stat().st_size for path in db_files)
    actual_run = bool(
        not any(item.startswith("missing:") for item in issues)
        and summary.get("status") == "completed"
        and lm["line_count"] > 0
        and lm["response_count"] > 0
        and api["line_count"] > 0
        and environment_interaction_count > 0
        and isinstance(tracker, Mapping)
        and tracker.get("num_tests") is not None
    )
    if not actual_run:
        issues.append("not_proven_actual_appworld_run")

    unsupported_code_data_combination = bool(
        data_version == "0.1.0" and code_version.startswith("0.2.0")
    )
    if unsupported_code_data_combination:
        warnings.append("unsupported_code_0.2_data_0.1_compatibility_bypass")

    if issues:
        verdict = "INVALID_RECORD"
    elif infra_signatures:
        verdict = "DIRECT_RUNTIME_SCHEMA_ERROR"
    elif unsupported_code_data_combination:
        verdict = "UNSUPPORTED_RUNTIME_NO_OBSERVED_SCHEMA_ERROR"
    elif warnings:
        verdict = "NORMAL_RUN_WITH_WARNINGS"
    else:
        verdict = "NORMAL_RUN"

    terminal_statuses = Counter(str(item.get("status") or "") for item in event_history)
    total_attempts = sum(int(item.get("attempt_count") or 0) for item in event_history if not item.get("resume_reused"))
    resume_reuse_count = sum(1 for item in event_history if item.get("resume_reused"))
    error_event_count = terminal_statuses.get("error", 0)

    return {
        "vps_id": vps_id,
        "run_id": RUN_ID,
        "task_id": task_id,
        "dataset_name": dataset_name,
        "global_index": global_index,
        "agent_slug": agent_slug,
        "agent_id": agent["agent_id"],
        "expected_model": expected_model,
        "verdict": verdict,
        "actually_ran_appworld": actual_run,
        "structural_issue_count": len(issues),
        "issues": issues,
        "warnings": sorted(set(warnings)),
        "native_success": summary.get("success"),
        "evaluation_pass_count": len(passes),
        "evaluation_failure_count": len(failures),
        "evaluation_num_tests": tracker.get("num_tests"),
        "evaluation_difficulty": tracker.get("difficulty"),
        "data_version": data_version,
        "code_version": code_version,
        "evaluation_version": evaluation_version,
        "lm_call_count": lm["line_count"],
        "lm_response_count": lm["response_count"],
        "empty_assistant_content_count": empty_assistant_content_count,
        "lm_input_models": lm["input_models"],
        "lm_output_models": lm["output_models"],
        "lm_providers": lm["providers"],
        "lm_finish_reasons": lm["finish_reasons"],
        "first_response_start": lm["first_response_start"],
        "last_response_end": lm["last_response_end"],
        "credential_exposed": bool(lm["credential_field_count"]),
        "credential_field_count": lm["credential_field_count"],
        "api_call_count": api["line_count"],
        "api_action_call_count": api["action_call_count"],
        "api_apps": api["apps"],
        "supervisor_completion_count": api["supervisor_completion_count"],
        "environment_interaction_count": environment_interaction_count,
        "environment_exception_count": len(exception_lines),
        "environment_exception_types": exception_types,
        "infra_signatures": infra_signatures,
        "missing_sqlite_tables": missing_tables,
        "missing_sqlite_columns": missing_columns,
        "sqlite_insert_missing_columns": insert_missing_columns,
        "unsupported_code_data_combination": unsupported_code_data_combination,
        "db_jsonl_file_count": len(db_files),
        "db_nonempty_files": db_nonempty_files,
        "db_total_bytes": db_total_bytes,
        "event_history_count": len(event_history),
        "event_terminal_statuses": dict(sorted(terminal_statuses.items())),
        "event_error_count": error_event_count,
        "event_total_attempts": total_attempts,
        "event_resume_reuse_count": resume_reuse_count,
        "failed_attempt_reason_counts": dict(sorted(Counter(attempt_failure_reasons).items())),
        "output_dir": str(output_dir),
    }


def remote_audit(args: argparse.Namespace) -> int:
    campaign_root = Path(args.campaign_root)
    shard_file = Path(args.shard_file)
    control_root = campaign_root / "control"
    cases = load_cases(shard_file)
    histories = load_event_history(control_root)
    attempt_failures = load_attempt_failure_reasons(campaign_root / "logs" / "workers")
    control_issues: list[str] = []
    state = read_json(control_root / "state.json", control_issues, "control/state.json")
    campaign_manifest = read_json(
        control_root / "campaign_manifest.json", control_issues, "control/campaign_manifest.json"
    )
    shard_manifest_path = control_root / "shard_manifest.json"
    if not shard_manifest_path.is_file():
        shard_manifest_path = control_root / "shard_manifest.prelaunch.json"
    shard_manifest = read_json(shard_manifest_path, control_issues, f"control/{shard_manifest_path.name}")

    records: list[dict[str, Any]] = []
    for agent_slug in AGENTS:
        for case in cases:
            slot_id = f"{agent_slug}__{case['task_id']}"
            records.append(
                audit_record(
                    campaign_root=campaign_root,
                    vps_id=args.vps_id,
                    case=case,
                    agent_slug=agent_slug,
                    event_history=histories.get(slot_id, []),
                    attempt_failure_reasons=attempt_failures.get(slot_id, []),
                )
            )
    payload = {
        "schema_version": "appworld_full_585_remote_record_audit/v1",
        "generated_at": utc_now(),
        "vps_id": args.vps_id,
        "campaign_root": str(campaign_root),
        "shard_file": str(shard_file),
        "shard_file_sha256": sha256_file(shard_file),
        "case_count": len(cases),
        "record_count": len(records),
        "cases": cases,
        "control_issues": control_issues,
        "state": state,
        "campaign_manifest": campaign_manifest,
        "shard_manifest": shard_manifest,
        "records": records,
    }
    sys.stdout.write(canonical_json(payload) + "\n")
    return 0


def ssh_remote_audit(
    *, host: str, known_hosts: Path, vps_id: str, campaign_root: str, shard_file: str
) -> dict[str, Any]:
    source = Path(__file__).read_bytes()
    command = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=15",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        f"UserKnownHostsFile={known_hosts}",
        f"root@{host}",
        "python3",
        "-",
        "--remote",
        "--vps-id",
        vps_id,
        "--campaign-root",
        campaign_root,
        "--shard-file",
        shard_file,
    ]
    completed = subprocess.run(command, input=source, capture_output=True, check=False)
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace")[-4000:]
        raise RuntimeError(f"remote audit failed for {vps_id} exit={completed.returncode}: {stderr}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        preview = completed.stdout[:1000].decode("utf-8", errors="replace")
        raise RuntimeError(f"remote audit returned invalid JSON for {vps_id}: {preview}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"remote audit returned non-object for {vps_id}")
    return payload


def load_task_ids_from_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    verdicts = Counter(str(record["verdict"]) for record in records)
    by_agent: dict[str, dict[str, Any]] = {}
    by_dataset: dict[str, dict[str, Any]] = {}
    for dimension, target in (("agent_slug", by_agent), ("dataset_name", by_dataset)):
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            grouped[str(record[dimension])].append(record)
        for key, group in sorted(grouped.items()):
            target[key] = {
                "record_count": len(group),
                "actual_appworld_count": sum(bool(item["actually_ran_appworld"]) for item in group),
                "native_success_count": sum(item["native_success"] is True for item in group),
                "native_fail_count": sum(item["native_success"] is False for item in group),
                "runtime_contaminated_count": sum(bool(item["infra_signatures"]) for item in group),
                "invalid_count": sum(bool(item["structural_issue_count"]) for item in group),
                "credential_exposed_count": sum(bool(item["credential_exposed"]) for item in group),
                "lm_call_count": sum(int(item["lm_call_count"]) for item in group),
                "api_call_count": sum(int(item["api_call_count"]) for item in group),
            }
    missing_tables = Counter()
    missing_columns = Counter()
    insert_missing_columns = Counter()
    infra_signatures = Counter()
    exception_types = Counter()
    warning_counts = Counter()
    issue_counts = Counter()
    attempt_failure_reasons = Counter()
    for record in records:
        missing_tables.update(record["missing_sqlite_tables"])
        missing_columns.update(record["missing_sqlite_columns"])
        insert_missing_columns.update(record["sqlite_insert_missing_columns"])
        infra_signatures.update(record["infra_signatures"].keys())
        exception_types.update(record["environment_exception_types"])
        warning_counts.update(record["warnings"])
        issue_counts.update(record["issues"])
        attempt_failure_reasons.update(record["failed_attempt_reason_counts"])
    return {
        "record_count": len(records),
        "verdict_counts": dict(sorted(verdicts.items())),
        "actual_appworld_count": sum(bool(record["actually_ran_appworld"]) for record in records),
        "native_success_count": sum(record["native_success"] is True for record in records),
        "native_fail_count": sum(record["native_success"] is False for record in records),
        "runtime_contaminated_count": sum(bool(record["infra_signatures"]) for record in records),
        "unsupported_code_data_combination_count": sum(
            bool(record["unsupported_code_data_combination"]) for record in records
        ),
        "invalid_count": sum(bool(record["structural_issue_count"]) for record in records),
        "credential_exposed_count": sum(bool(record["credential_exposed"]) for record in records),
        "credential_field_count": sum(int(record["credential_field_count"]) for record in records),
        "lm_call_count": sum(int(record["lm_call_count"]) for record in records),
        "lm_response_count": sum(int(record["lm_response_count"]) for record in records),
        "api_call_count": sum(int(record["api_call_count"]) for record in records),
        "environment_interaction_count": sum(int(record["environment_interaction_count"]) for record in records),
        "environment_exception_count": sum(int(record["environment_exception_count"]) for record in records),
        "missing_sqlite_table_record_counts": dict(sorted(missing_tables.items())),
        "missing_sqlite_column_record_counts": dict(sorted(missing_columns.items())),
        "sqlite_insert_missing_column_record_counts": dict(sorted(insert_missing_columns.items())),
        "infra_signature_record_counts": dict(sorted(infra_signatures.items())),
        "environment_exception_type_counts": dict(sorted(exception_types.items())),
        "warning_counts": dict(sorted(warning_counts.items())),
        "issue_counts": dict(sorted(issue_counts.items())),
        "failed_attempt_reason_counts": dict(sorted(attempt_failure_reasons.items())),
        "by_agent": by_agent,
        "by_dataset": by_dataset,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(canonical_json(record) + "\n")


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    fields = (
        "global_index",
        "task_id",
        "dataset_name",
        "vps_id",
        "agent_id",
        "agent_slug",
        "expected_model",
        "verdict",
        "actually_ran_appworld",
        "native_success",
        "evaluation_pass_count",
        "evaluation_failure_count",
        "lm_call_count",
        "lm_response_count",
        "api_call_count",
        "api_action_call_count",
        "supervisor_completion_count",
        "environment_interaction_count",
        "environment_exception_count",
        "empty_assistant_content_count",
        "credential_exposed",
        "event_error_count",
        "event_total_attempts",
        "event_resume_reuse_count",
        "failed_attempt_reason_counts",
        "missing_sqlite_tables",
        "missing_sqlite_columns",
        "sqlite_insert_missing_columns",
        "infra_signatures",
        "issues",
        "warnings",
        "output_dir",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = {key: record.get(key) for key in fields}
            for key in (
                "missing_sqlite_tables",
                "missing_sqlite_columns",
                "sqlite_insert_missing_columns",
                "failed_attempt_reason_counts",
                "infra_signatures",
                "issues",
                "warnings",
            ):
                value = row[key]
                if isinstance(value, Mapping):
                    row[key] = ";".join(f"{name}={count}" for name, count in sorted(value.items()))
                elif isinstance(value, list):
                    row[key] = ";".join(str(item) for item in value)
            writer.writerow(row)


def markdown_report(report: Mapping[str, Any]) -> str:
    summary = report["summary"]
    coverage = report["coverage"]
    lines = [
        "# AppWorld 585 two-VPS record-by-record audit",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Verdict",
        "",
        (
            f"All `{summary['record_count']}` expected records contain evidence of a real AppWorld run: "
            f"official simplified ReAct runner configuration, `{summary['lm_call_count']}` model calls, "
            f"`{summary['api_call_count']}` AppWorld API calls, environment traces, database snapshots, "
            "and official evaluator output."
        ),
        "",
        (
            f"However, all `{summary['unsupported_code_data_combination_count']}` records used AppWorld "
            "code 0.2.0.dev0 with data 0.1.0 through a compatibility-check bypass. "
            f"`{summary['runtime_contaminated_count']}` records directly exhibit the resulting SQLite schema "
            f"errors; `{summary['invalid_count']}` records have additional structural failures."
        ),
        "",
        (
            f"Credential exposure: `{summary['credential_exposed_count']}` records store a plaintext API-key "
            "field in the official LM-call log. Rotate the key and sanitize retained/released artifacts."
        ),
        "",
        "## Coverage",
        "",
        f"- Remote union: `{coverage['remote_unique_task_count']}` unique tasks and `{summary['record_count']}` agent-task records.",
        f"- VPS overlap: `{coverage['vps_task_overlap_count']}` tasks.",
        f"- Missing from selected-100 + extension-485 union: `{coverage['missing_from_expected_union_count']}` tasks.",
        f"- Unexpected remote tasks: `{coverage['unexpected_remote_task_count']}` tasks.",
        f"- The remote full run includes `{coverage['selected_100_remote_overlap_count']}` of the locally selected 100 tasks and all `{coverage['extension_485_remote_overlap_count']}` extension tasks.",
        "",
        "## Aggregate counts",
        "",
        "| Dimension | Records | Native success | Native fail | Runtime contaminated | Invalid |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, item in summary["by_agent"].items():
        lines.append(
            f"| {name} | {item['record_count']} | {item['native_success_count']} | {item['native_fail_count']} | "
            f"{item['runtime_contaminated_count']} | {item['invalid_count']} |"
        )
    for name, item in summary["by_dataset"].items():
        lines.append(
            f"| {name} | {item['record_count']} | {item['native_success_count']} | {item['native_fail_count']} | "
            f"{item['runtime_contaminated_count']} | {item['invalid_count']} |"
        )
    lines.extend(
        [
            "",
            "## Runtime contamination",
            "",
            f"Recognized signatures by affected record: `{canonical_json(summary['infra_signature_record_counts'])}`",
            "",
        f"Missing SQLite tables by affected record: `{canonical_json(summary['missing_sqlite_table_record_counts'])}`",
        "",
        f"Missing SQLite columns by affected record: `{canonical_json(summary['missing_sqlite_column_record_counts'])}`",
        "",
        f"INSERT column mismatches by affected record: `{canonical_json(summary['sqlite_insert_missing_column_record_counts'])}`",
        "",
        f"Recovered failed worker attempts: `{canonical_json(summary['failed_attempt_reason_counts'])}`",
        "",
            "## Files",
            "",
            "- `records.csv`: one row per agent-task record.",
            "- `records.jsonl`: full sanitized per-record audit metadata.",
            "- `audit_report.json`: complete aggregate report and remote control metadata.",
            "",
        ]
    )
    return "\n".join(lines)


def controller(args: argparse.Namespace) -> int:
    specs = (
        {
            "vps_id": "vps1",
            "host": args.vps1_host,
            "known_hosts": Path(args.vps1_known_hosts),
            "campaign_root": f"/srv/appworld-full-585/{RUN_ID}/vps1",
            "shard_file": f"/srv/appworld-full-585/{RUN_ID}/vps1/control/vps1_cases.jsonl",
        },
        {
            "vps_id": "vps2",
            "host": args.vps2_host,
            "known_hosts": Path(args.vps2_known_hosts),
            "campaign_root": f"/srv/appworld-full-585/{RUN_ID}/vps2",
            "shard_file": f"/srv/appworld-full-585/{RUN_ID}/vps2/control/shard.v1.jsonl",
        },
    )
    remote_payloads = []
    for spec in specs:
        remote_payloads.append(ssh_remote_audit(**spec))

    records = [record for payload in remote_payloads for record in payload["records"]]
    records.sort(key=lambda item: (int(item["global_index"]), str(item["agent_slug"])))
    selected_payload = json.loads(Path(args.selected_100_json).read_text(encoding="utf-8"))
    selected_100 = {
        str(item["task_id"])
        for item in list(selected_payload.get("items") or [])
        if isinstance(item, Mapping) and item.get("task_id")
    }
    extension_485 = set(load_task_ids_from_lines(Path(args.extension_485_txt)))
    expected_union = selected_100 | extension_485
    vps_tasks = {
        payload["vps_id"]: {str(case["task_id"]) for case in payload["cases"]}
        for payload in remote_payloads
    }
    remote_union = set().union(*vps_tasks.values())
    coverage = {
        "selected_100_count": len(selected_100),
        "extension_485_count": len(extension_485),
        "selected_extension_overlap_count": len(selected_100 & extension_485),
        "expected_union_count": len(expected_union),
        "remote_unique_task_count": len(remote_union),
        "vps1_task_count": len(vps_tasks.get("vps1", set())),
        "vps2_task_count": len(vps_tasks.get("vps2", set())),
        "vps_task_overlap_count": len(vps_tasks.get("vps1", set()) & vps_tasks.get("vps2", set())),
        "missing_from_expected_union_count": len(expected_union - remote_union),
        "missing_from_expected_union": sorted(expected_union - remote_union),
        "unexpected_remote_task_count": len(remote_union - expected_union),
        "unexpected_remote_tasks": sorted(remote_union - expected_union),
        "selected_100_remote_overlap_count": len(selected_100 & remote_union),
        "extension_485_remote_overlap_count": len(extension_485 & remote_union),
        "remote_global_index_count": len({int(record["global_index"]) for record in records}),
    }
    summary = summarize_records(records)
    control_validation: dict[str, Any] = {}
    for payload in remote_payloads:
        vps_id = str(payload["vps_id"])
        state = payload["state"]
        manifest = payload["campaign_manifest"]
        control_validation[vps_id] = {
            "control_issues": payload["control_issues"],
            "state_status": state.get("status"),
            "state_case_count": state.get("case_count"),
            "state_record_slot_count": state.get("record_slot_count"),
            "state_completed_count": state.get("completed_count"),
            "state_error_count": state.get("error_count"),
            "state_terminal_count": state.get("terminal_count"),
            "state_native_success_count": state.get("native_success_count"),
            "state_native_fail_count": state.get("native_fail_count"),
            "manifest_run_id": manifest.get("run_id"),
            "manifest_official_commit": manifest.get("official_commit"),
            "manifest_launcher_sha256": manifest.get("launcher_sha256"),
            "manifest_valid": (
                manifest.get("run_id") == RUN_ID
                and manifest.get("official_commit") == OFFICIAL_COMMIT
                and manifest.get("launcher_sha256") == LAUNCHER_SHA256
            ),
            "shard_file_sha256": payload["shard_file_sha256"],
        }
    report = {
        "schema_version": "appworld_full_585_two_vps_audit/v1",
        "generated_at": utc_now(),
        "run_id": RUN_ID,
        "campaign_validity": {
            "verdict": "FAIL_NOT_VALID_FOR_SCORING",
            "actually_executed_appworld": summary["actual_appworld_count"] == summary["record_count"],
            "reasons": [
                "official AppWorld code 0.2.0.dev0 was run against data 0.1.0 after bypassing the official compatibility guard",
                f"{summary['runtime_contaminated_count']} records directly contain SQLite schema mismatch errors",
                f"{summary['credential_exposed_count']} records retain a plaintext API-key field in LM logs",
            ],
        },
        "hosts": {
            "vps1": {"address": args.vps1_host, "host_key_fingerprint": args.vps1_fingerprint},
            "vps2": {"address": args.vps2_host, "host_key_fingerprint": args.vps2_fingerprint},
        },
        "coverage": coverage,
        "control_validation": control_validation,
        "summary": summary,
        "remote_meta": [
            {key: value for key, value in payload.items() if key not in {"records", "cases"}}
            for payload in remote_payloads
        ],
    }
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "audit_report.json", report)
    write_jsonl(output_dir / "records.jsonl", records)
    write_csv(output_dir / "records.csv", records)
    (output_dir / "README.md").write_text(markdown_report(report), encoding="utf-8")
    sys.stdout.write(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote", action="store_true")
    parser.add_argument("--vps-id", choices=("vps1", "vps2"))
    parser.add_argument("--campaign-root")
    parser.add_argument("--shard-file")
    parser.add_argument("--vps1-host", default="45.76.116.86")
    parser.add_argument("--vps2-host", default="207.148.81.191")
    parser.add_argument("--vps1-known-hosts", default="/tmp/appworld_vps1_hostkeys")
    parser.add_argument("--vps2-known-hosts", default="/tmp/appworld_vps2_hostkeys")
    parser.add_argument("--vps1-fingerprint", default="SHA256:UrMhNI+Jqo8oFJ+wwCMVxjZM3xOZzUft4eISOVpT8HI")
    parser.add_argument("--vps2-fingerprint", default="SHA256:olcxZYCxN4pGGBdk/o6c6mKGCvJx1byndAzd1nXxVUM")
    parser.add_argument(
        "--selected-100-json", default="experiments/official_splits/appworld_selected_task_sources.json"
    )
    parser.add_argument(
        "--extension-485-txt",
        default=(
            "experiments/appworld_full_test_extension_v1_gpt56_strict_v3_lockfix_v6/"
            "official_splits/appworld_extension_all.txt"
        ),
    )
    parser.add_argument(
        "--output-dir", default="results/audits/appworld585_20260719_two_vps_record_audit"
    )
    args = parser.parse_args(argv)
    if args.remote and not (args.vps_id and args.campaign_root and args.shard_file):
        parser.error("--remote requires --vps-id, --campaign-root, and --shard-file")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return remote_audit(args) if args.remote else controller(args)


if __name__ == "__main__":
    raise SystemExit(main())
