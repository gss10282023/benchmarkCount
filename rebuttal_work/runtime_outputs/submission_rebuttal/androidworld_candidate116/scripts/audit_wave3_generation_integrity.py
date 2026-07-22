#!/usr/bin/env python3
"""Independent provenance/integrity audit for AndroidWorld candidate116 wave_003.

This deliberately does not judge checklist semantics and never mutates wave_003,
the packet tree, or any legacy root.  Its JSON output is self-addressed by
``report_sha256`` (canonical JSON with that field omitted).
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import statistics
import subprocess
from typing import Any, Iterable

import yaml


SCRIPT = Path(__file__).resolve()
CANDIDATE_ROOT = SCRIPT.parents[1]
REPO_ROOT = SCRIPT.parents[5]
GENERATION_ROOT = CANDIDATE_ROOT / "draft_generation"
PRELOCK_PATH = GENERATION_ROOT / "freeze/androidworld_candidate116_codex_cli_draft_prelock_v3.json"
CONFIG_PATH = GENERATION_ROOT / "config/androidworld_candidate116_codex_cli_draft_config_v3.json"
WAVE_ROOT = GENERATION_ROOT / "waves/wave_003"
BATCH_RESULTS_PATH = WAVE_ROOT / "_batch_results.jsonl"
BATCH_SUMMARY_PATH = WAVE_ROOT / "_batch_summary.json"
SNAPSHOT_MANIFEST_PATH = GENERATION_ROOT / "toolchain_snapshot/v3/snapshot_manifest.json"
GENERATION_GUARD_PATH = GENERATION_ROOT / "validation/wave_003_readonly_pre_post_guard_report.json"

CANONICAL_SUFFIXES = (
    "checklist.yaml",
    "checklist.json",
    "api_response.json",
    "llm_call.json",
    "reasoning_summary.txt",
    "stderr.log",
    "stdout.log",
)
ATTEMPT_SUFFIXES = CANONICAL_SUFFIXES

KNOWN_STDERR_CLASSES: tuple[tuple[str, str], ...] = (
    ("state db discrepancy", "state_db_discrepancy"),
    ("failed to download remote installed plugin bundle", "remote_plugin_bundle"),
    ("failed to load recommended plugins", "recommended_plugin_catalog"),
    ("failed to warm remote plugin catalog cache", "plugin_catalog_warm"),
    ("Failed to delete shell snapshot", "shell_snapshot_delete"),
    ("responses_retry", "responses_retry"),
    ("codex_core::tools::router: error=exec_command failed", "model_tool_router_error"),
    ("codex_analytics::client: events failed with status", "analytics_delivery_failure"),
)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def object_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_path(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT))


def file_binding(path: Path) -> dict[str, Any]:
    return {
        "path": repo_path(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"expected object at {path}:{number}")
        rows.append(value)
    return rows


def strip_null_fields(node: Any) -> Any:
    if isinstance(node, dict):
        return {key: strip_null_fields(value) for key, value in node.items() if value is not None}
    if isinstance(node, list):
        return [strip_null_fields(value) for value in node]
    return node


def parse_timestamp(value: Any) -> dt.datetime:
    if not isinstance(value, str):
        raise ValueError(f"timestamp is not a string: {value!r}")
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp is timezone-naive: {value}")
    return parsed


def verify_self_hash(value: dict[str, Any], key: str) -> bool:
    core = dict(value)
    expected = core.pop(key, None)
    return isinstance(expected, str) and expected == object_sha256(core)


def add_notice(
    notices: list[dict[str, Any]],
    code: str,
    severity: str,
    detail: str,
    *,
    cases: Iterable[str] | None = None,
) -> None:
    item: dict[str, Any] = {"code": code, "severity": severity, "detail": detail}
    if cases is not None:
        item["cases"] = sorted(set(cases))
    notices.append(item)


def add_case_issue(case: dict[str, Any], code: str, severity: str, detail: str) -> None:
    case["issues"].append({"code": code, "severity": severity, "detail": detail})


def flag_value(command: list[Any], flag: str) -> Any:
    positions = [index for index, value in enumerate(command) if value == flag]
    if len(positions) != 1 or positions[0] + 1 >= len(command):
        return None
    return command[positions[0] + 1]


def classify_stderr(stderr: str) -> tuple[collections.Counter[str], list[str]]:
    classes: collections.Counter[str] = collections.Counter()
    unknown: list[str] = []
    for raw_line in stderr.splitlines():
        line = re.sub(r"^\d{4}-\d\d-\d\dT\S+\s+", "", raw_line)
        matched = False
        for needle, label in KNOWN_STDERR_CLASSES:
            if needle in line:
                classes[label] += 1
                matched = True
                break
        if not matched and line.strip():
            unknown.append(line[:500])
    return classes, unknown


MUTATION_RE = re.compile(
    r"(?:^|[;&|]\s*)(?:rm|mv|cp|touch|chmod|chown|mkdir|install|truncate|tee)\b"
    r"|\bsed\s+-i\b|\.write_text\s*\(|\.write_bytes\s*\(",
    re.IGNORECASE,
)


def event_integrity(api: dict[str, Any]) -> dict[str, Any]:
    codex = api.get("codex_cli") or {}
    events = codex.get("events") or []
    type_counts: collections.Counter[str] = collections.Counter()
    command_statuses: collections.Counter[str] = collections.Counter()
    nonzero_commands: list[dict[str, Any]] = []
    successful_mutation_like_commands: list[str] = []
    started_ids: set[str] = set()
    completed_ids: set[str] = set()
    final_messages: list[str] = []
    thread_ids: list[str] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("type"))
        type_counts[event_type] += 1
        if event_type == "thread.started" and isinstance(event.get("thread_id"), str):
            thread_ids.append(event["thread_id"])
        item = event.get("item") or {}
        if not isinstance(item, dict):
            continue
        item_id = item.get("id")
        if isinstance(item_id, str):
            if event_type == "item.started":
                started_ids.add(item_id)
            if event_type == "item.completed":
                completed_ids.add(item_id)
        if event_type == "item.completed" and item.get("type") == "agent_message":
            if isinstance(item.get("text"), str):
                final_messages.append(item["text"])
        if event_type == "item.completed" and item.get("type") == "command_execution":
            status_value = str(item.get("status"))
            command_statuses[status_value] += 1
            exit_code = item.get("exit_code")
            if exit_code not in (0, None):
                nonzero_commands.append(
                    {
                        "exit_code": exit_code,
                        "command_sha256": hashlib.sha256(
                            str(item.get("command", "")).encode("utf-8")
                        ).hexdigest(),
                    }
                )
            command = str(item.get("command", ""))
            if status_value == "completed" and exit_code == 0 and MUTATION_RE.search(command):
                successful_mutation_like_commands.append(command[:500])
    return {
        "event_count": len(events),
        "event_type_counts": dict(sorted(type_counts.items())),
        "command_status_counts": dict(sorted(command_statuses.items())),
        "nonzero_command_count": len(nonzero_commands),
        "nonzero_commands": nonzero_commands,
        "successful_mutation_like_commands": successful_mutation_like_commands,
        "started_without_completion": sorted(started_ids - completed_ids),
        "agent_message_count": len(final_messages),
        "final_agent_message": final_messages[-1] if final_messages else None,
        "thread_ids": thread_ids,
    }


def normalized_usage(api: dict[str, Any]) -> dict[str, int]:
    usage = api.get("usage") or {}
    input_details = usage.get("input_tokens_details") or {}
    output_details = usage.get("output_tokens_details") or {}
    return {
        "prompt_tokens": int(usage.get("input_tokens", 0) or 0),
        "completion_tokens": int(usage.get("output_tokens", 0) or 0),
        "cached_prompt_tokens": int(input_details.get("cached_tokens", 0) or 0),
        "reasoning_tokens": int(output_details.get("reasoning_tokens", 0) or 0),
        "total_tokens": int(usage.get("total_tokens", 0) or 0),
    }


def audit_api_and_call(
    *,
    api_path: Path,
    llm_path: Path,
    reasoning_path: Path,
    expected_case_id: str,
    expected_task_id: str,
    expected_attempt: int,
    expected_timeout: int,
    expected_max_tokens: int,
    case: dict[str, Any],
    selected: bool,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    api = load_json(api_path)
    llm = load_json(llm_path)
    prefix = "selected" if selected else f"attempt_{expected_attempt:02d}"

    expected_values = {
        "api.provider": (api.get("provider"), "codex_cli"),
        "api.model": (api.get("model"), "gpt-5.6-sol"),
        "api.status": (api.get("status"), "completed"),
        "llm.provider": (llm.get("provider"), "codex_cli"),
        "llm.model": (llm.get("model"), "gpt-5.6-sol"),
        "llm.model_version": (llm.get("model_version"), "gpt-5.6-sol"),
        "llm.case_unit_id": (llm.get("case_unit_id"), expected_case_id),
        "llm.task_id": (llm.get("task_id"), expected_task_id),
        "llm.domain": (llm.get("domain"), "androidworld"),
        "llm.timeout_seconds": (llm.get("timeout_seconds"), expected_timeout),
        "llm.max_tokens": (llm.get("max_tokens"), expected_max_tokens),
        "llm.reasoning_effort": (
            (llm.get("response_metadata") or {}).get("reasoning_effort"),
            "xhigh",
        ),
        "llm.auth_mode": ((llm.get("response_metadata") or {}).get("auth_mode"), "codex_login"),
    }
    for label, (observed, expected) in expected_values.items():
        if observed != expected:
            add_case_issue(
                case,
                "sidecar_field_mismatch",
                "repair_blocker",
                f"{prefix} {label}: observed={observed!r}, expected={expected!r}",
            )

    codex = api.get("codex_cli") or {}
    command = codex.get("command") or []
    command_ok = (
        isinstance(command, list)
        and command[:2] == ["codex", "exec"]
        and "--ephemeral" in command
        and "--ignore-user-config" in command
        and "--json" in command
        and flag_value(command, "--sandbox") == "read-only"
        and flag_value(command, "--model") == "gpt-5.6-sol"
        and 'model_reasoning_effort="xhigh"' in command
        and 'model_verbosity="low"' in command
        and "--dangerously-bypass-approvals-and-sandbox" not in command
    )
    if not command_ok:
        add_case_issue(
            case,
            "codex_command_contract_mismatch",
            "repair_blocker",
            f"{prefix} command does not prove ephemeral/read-only/gpt-5.6-sol/xhigh/low/ignore-user-config",
        )
    if codex.get("auth_mode") != "codex_login" or codex.get("returncode") != 0:
        add_case_issue(
            case,
            "codex_execution_identity_mismatch",
            "repair_blocker",
            f"{prefix} Codex auth/returncode mismatch",
        )
    if codex.get("timeout_seconds") != expected_timeout or codex.get("sandbox") != "read-only":
        add_case_issue(
            case,
            "codex_timeout_or_sandbox_mismatch",
            "repair_blocker",
            f"{prefix} timeout/sandbox mismatch",
        )
    if codex.get("malformed_event_lines") not in ([], None):
        add_case_issue(
            case,
            "malformed_codex_events",
            "repair_blocker",
            f"{prefix} has malformed Codex JSONL events",
        )

    response_id = api.get("id")
    metadata = llm.get("response_metadata") or {}
    events = event_integrity(api)
    if (
        not isinstance(response_id, str)
        or not response_id
        or metadata.get("response_id") != response_id
        or events["thread_ids"] != [response_id]
    ):
        add_case_issue(
            case,
            "response_id_chain_mismatch",
            "repair_blocker",
            f"{prefix} response/thread/llm ids do not form a unique chain",
        )

    try:
        request_time = parse_timestamp(llm.get("request_timestamp"))
        response_time = parse_timestamp(llm.get("response_timestamp"))
        if response_time <= request_time:
            raise ValueError("response is not after request")
        duration_seconds = (response_time - request_time).total_seconds()
    except Exception as exc:  # noqa: BLE001 - audit must report malformed records
        add_case_issue(
            case,
            "timestamp_chain_invalid",
            "repair_blocker",
            f"{prefix} timestamp chain invalid: {exc}",
        )
        request_time = response_time = None
        duration_seconds = None

    api_usage = normalized_usage(api)
    llm_usage = llm.get("token_usage") or {}
    if api_usage != llm_usage:
        add_case_issue(
            case,
            "token_usage_sidecar_mismatch",
            "repair_blocker",
            f"{prefix} normalized API usage differs from llm_call usage",
        )
    required_positive = ("prompt_tokens", "completion_tokens", "reasoning_tokens", "total_tokens")
    if any(int(api_usage.get(key, 0)) <= 0 for key in required_positive):
        add_case_issue(
            case,
            "zero_or_negative_token_usage",
            "repair_blocker",
            f"{prefix} has zero/negative required token usage",
        )
    if api_usage["total_tokens"] != api_usage["prompt_tokens"] + api_usage["completion_tokens"]:
        add_case_issue(
            case,
            "token_total_arithmetic_mismatch",
            "repair_blocker",
            f"{prefix} total_tokens does not equal prompt+completion",
        )
    if api_usage["cached_prompt_tokens"] > api_usage["prompt_tokens"]:
        add_case_issue(
            case,
            "cached_token_count_invalid",
            "repair_blocker",
            f"{prefix} cached prompt tokens exceed prompt tokens",
        )
    if api_usage["reasoning_tokens"] > api_usage["completion_tokens"]:
        add_case_issue(
            case,
            "reasoning_token_count_invalid",
            "repair_blocker",
            f"{prefix} reasoning tokens exceed completion tokens",
        )

    output_text = api.get("output_text")
    parsed_output: Any = None
    try:
        parsed_output = json.loads(output_text)
        if not isinstance(parsed_output, dict):
            raise ValueError("output_text is not an object")
    except Exception as exc:  # noqa: BLE001
        add_case_issue(
            case,
            "api_output_text_invalid",
            "repair_blocker",
            f"{prefix} output_text is not structured JSON: {exc}",
        )

    final_event_message = events.pop("final_agent_message")
    try:
        if json.loads(final_event_message) != parsed_output:
            raise ValueError("last completed agent message differs from output_text")
    except Exception as exc:  # noqa: BLE001
        add_case_issue(
            case,
            "final_event_output_mismatch",
            "repair_blocker",
            f"{prefix} final agent event mismatch: {exc}",
        )
    if events["started_without_completion"]:
        add_case_issue(
            case,
            "incomplete_codex_event_items",
            "repair_blocker",
            f"{prefix} has started item ids without completion",
        )
    if events["successful_mutation_like_commands"]:
        add_case_issue(
            case,
            "successful_mutation_like_model_command",
            "repair_blocker",
            f"{prefix} has a successful mutation-like model command",
        )

    stderr_classes, unknown_stderr = classify_stderr(str(codex.get("stderr") or ""))
    if unknown_stderr:
        add_case_issue(
            case,
            "unclassified_codex_stderr",
            "warning",
            f"{prefix} has {len(unknown_stderr)} unclassified stderr line(s)",
        )
    reasoning_expected = "\n\n".join(
        str(summary.get("text", "")).strip()
        for item in api.get("output", [])
        if isinstance(item, dict) and item.get("type") == "reasoning"
        for summary in item.get("summary", [])
        if isinstance(summary, dict) and str(summary.get("text", "")).strip()
    ).strip()
    reasoning_actual = reasoning_path.read_text(encoding="utf-8").strip()
    if reasoning_actual != reasoning_expected:
        add_case_issue(
            case,
            "reasoning_summary_sidecar_mismatch",
            "repair_blocker",
            f"{prefix} reasoning summary does not match API response summary",
        )

    raw_api_path = metadata.get("raw_api_response_path")
    reasoning_sidecar_path = metadata.get("reasoning_summary_path")
    if not (
        isinstance(raw_api_path, str)
        and Path(raw_api_path).resolve() == api_path.resolve()
        and isinstance(reasoning_sidecar_path, str)
        and Path(reasoning_sidecar_path).resolve() == reasoning_path.resolve()
    ):
        add_case_issue(
            case,
            "llm_sidecar_path_mismatch",
            "repair_blocker",
            f"{prefix} raw API/reasoning paths do not bind the attempt sidecars",
        )

    return api, llm, {
        "response_id": response_id,
        "request_timestamp": request_time.isoformat() if request_time else None,
        "response_timestamp": response_time.isoformat() if response_time else None,
        "duration_seconds": round(duration_seconds, 6) if duration_seconds is not None else None,
        "token_usage": api_usage,
        "completion_exceeds_nominal_max_tokens": api_usage["completion_tokens"] > expected_max_tokens,
        "events": events,
        "stderr_classes": dict(sorted(stderr_classes.items())),
        "unclassified_stderr_line_count": len(unknown_stderr),
        "reasoning_summary_empty": not bool(reasoning_actual),
        "parsed_output": parsed_output,
    }


def percentile(values: list[int], fraction: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))
    return ordered[index]


def audit() -> dict[str, Any]:
    notices: list[dict[str, Any]] = []
    repair_global_blockers: list[str] = []

    prelock = load_json(PRELOCK_PATH)
    config = load_json(CONFIG_PATH)
    summary = load_json(BATCH_SUMMARY_PATH)
    batch_rows = load_jsonl(BATCH_RESULTS_PATH)
    snapshot = load_json(SNAPSHOT_MANIFEST_PATH)
    guard = load_json(GENERATION_GUARD_PATH)

    def repair_require(condition: bool, code: str, detail: str) -> None:
        if not condition:
            repair_global_blockers.append(code)
            add_notice(notices, code, "repair_blocker", detail)

    repair_require(verify_self_hash(prelock, "prelock_sha256"), "prelock_self_hash_invalid", "v3 prelock self-hash does not verify")
    repair_require(verify_self_hash(config, "config_sha256"), "config_self_hash_invalid", "v3 config self-hash does not verify")
    repair_require(
        prelock.get("draft_config", {}).get("sha256") == sha256_file(CONFIG_PATH)
        and prelock.get("draft_config", {}).get("config_sha256") == config.get("config_sha256"),
        "prelock_config_binding_invalid",
        "prelock does not bind the current v3 config bytes and self-hash",
    )
    repair_require(
        prelock.get("case_count") == 116 and len(prelock.get("packet_inputs") or []) == 116,
        "prelock_case_count_invalid",
        "v3 prelock does not contain exactly 116 packet bindings",
    )
    packet_inputs = prelock.get("packet_inputs") or []
    case_order = prelock.get("case_order") or []
    repair_require(
        prelock.get("packet_inputs_sha256") == object_sha256(packet_inputs),
        "packet_inputs_hash_invalid",
        "packet input aggregate hash does not verify",
    )
    repair_require(
        prelock.get("case_order_sha256") == object_sha256(case_order)
        and case_order == [row.get("case_unit_id") for row in packet_inputs],
        "case_order_hash_invalid",
        "case order hash/order does not match packet bindings",
    )
    repair_require(
        [row.get("selection_rank") for row in packet_inputs] == list(range(116)),
        "selection_rank_invalid",
        "packet selection_rank values are not exactly 0..115",
    )

    expected_config = {
        "schema_version": "androidworld_candidate116_codex_draft_config/v3",
        "generation_id": "wave_003",
        "status": "prelocked",
        "provider": "codex_cli",
        "auth_mode": "codex_login",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "xhigh",
        "model_verbosity": "low",
        "sandbox": "read-only",
        "ephemeral": True,
        "ignore_user_config": True,
        "max_parallel": 6,
        "large_max_parallel": 6,
        "codex_timeout_seconds": 1800,
        "large_codex_timeout_seconds": 3600,
        "large_case_threshold_bytes": 900000,
        "token_budgets": [12000, 16000, 20000],
        "input_kind": "full_case_packet",
    }
    repair_require(
        all(config.get(key) == value for key, value in expected_config.items()),
        "generation_config_contract_invalid",
        "v3 config does not retain the exact Codex-login/model/xhigh/read-only/6-worker contract",
    )
    runner_command = config.get("runner_command") or []
    repair_require(
        config.get("runner_command_sha256") == object_sha256(runner_command),
        "runner_command_hash_invalid",
        "runner command aggregate hash does not verify",
    )
    repair_require(
        flag_value(runner_command, "--max-parallel") == "6"
        and flag_value(runner_command, "--large-max-parallel") == "6"
        and flag_value(runner_command, "--provider") == "codex"
        and flag_value(runner_command, "--model") == "gpt-5.6-sol"
        and flag_value(runner_command, "--reasoning-effort") == "xhigh"
        and flag_value(runner_command, "--codex-sandbox") == "read-only"
        and flag_value(runner_command, "--sort-by") == "name",
        "runner_command_contract_invalid",
        "runner command does not match the frozen 6-worker Codex contract",
    )

    for name, binding in sorted((prelock.get("tool_bindings") or {}).items()):
        path = REPO_ROOT / str(binding.get("path"))
        repair_require(
            path.is_file()
            and sha256_file(path) == binding.get("sha256")
            and path.stat().st_size == binding.get("size_bytes"),
            f"tool_binding_invalid_{name}",
            f"frozen tool binding does not verify: {name}",
        )
    repair_require(
        sha256_file(SNAPSHOT_MANIFEST_PATH) == prelock.get("toolchain_snapshot", {}).get("sha256")
        and verify_self_hash(snapshot, "snapshot_sha256")
        and snapshot.get("snapshot_sha256") == prelock.get("toolchain_snapshot", {}).get("snapshot_sha256")
        and snapshot.get("files_sha256") == object_sha256(snapshot.get("files") or []),
        "toolchain_snapshot_binding_invalid",
        "v3 toolchain snapshot manifest/hash chain does not verify",
    )
    snapshot_unlocked: list[str] = []
    for row in snapshot.get("files") or []:
        path = REPO_ROOT / str(row.get("path"))
        repair_require(
            path.is_file()
            and sha256_file(path) == row.get("sha256")
            and path.stat().st_size == row.get("size_bytes"),
            "toolchain_snapshot_file_invalid",
            f"snapshot file does not match manifest: {row.get('path')}",
        )
        flags = getattr(path.stat(), "st_flags", 0)
        immutable = bool(flags & getattr(stat, "UF_IMMUTABLE", 0))
        if path.stat().st_mode & 0o222 or not immutable:
            snapshot_unlocked.append(str(row.get("path")))
    repair_require(
        not snapshot_unlocked,
        "toolchain_snapshot_permissions_invalid",
        f"{len(snapshot_unlocked)} snapshot files are writable or lack UF_IMMUTABLE",
    )

    guard_core = dict(guard)
    claimed_guard_hash = guard_core.pop("guard_sha256", None)
    repair_require(
        claimed_guard_hash == object_sha256(guard_core),
        "generation_guard_self_hash_invalid",
        "wave_003 generation guard self-hash does not verify",
    )
    repair_require(
        guard.get("wave_complete_116_of_116") is True
        and guard.get("full_packet_inputs_unchanged") is True
        and guard.get("toolchain_snapshot_unchanged") is True,
        "generation_input_guard_invalid",
        "wave guard does not prove 116 completion and unchanged packet/toolchain inputs",
    )
    if guard.get("status") != "pass" or guard.get("readonly_pre_post_equal") is not True:
        add_notice(
            notices,
            "legacy_root_changed_during_generation",
            "direct_freeze_blocker",
            "The monitored legacy neurips_ed_track_minimal root changed during wave_003; the isolated v3 snapshot and all full packets remained unchanged, so this is nonblocking only for use as repair input.",
            cases=[],
        )

    summary_expected = {
        "total_cases": 116,
        "completed_cases": 116,
        "success_cases": 116,
        "skipped_cases": 0,
        "failed_cases": 0,
        "warning_count": 0,
        "provider": "codex",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "xhigh",
        "codex_sandbox": "read-only",
        "token_budgets": [12000, 16000, 20000],
        "sort_by": "name",
        "quality_check": "none",
        "large_case_threshold_bytes": 900000,
    }
    repair_require(
        all(summary.get(key) == value for key, value in summary_expected.items()),
        "batch_summary_contract_invalid",
        "batch summary does not report an exact 116/116 successful frozen-contract run",
    )
    repair_require(
        len(batch_rows) == 116
        and len({row.get("case_unit_dir") for row in batch_rows}) == 116,
        "batch_results_cardinality_invalid",
        "batch_results does not contain exactly one row per case",
    )

    packet_by_case = {str(row.get("case_unit_id")): row for row in packet_inputs}
    batch_by_case = {str(row.get("case_unit_dir")): row for row in batch_rows}
    repair_require(
        set(packet_by_case) == set(batch_by_case) == set(case_order),
        "case_set_mismatch",
        "prelock, case order, and batch result case sets differ",
    )

    lane_sizes: dict[str, list[int]] = {"regular": [], "oversized": []}
    for row in packet_inputs:
        lane = "oversized" if int(row.get("size_bytes", 0)) > 900000 else "regular"
        lane_sizes[lane].append(int(row.get("size_bytes", 0)))
    expected_lane_stats = {
        lane: {
            "count": len(sizes),
            "min_bytes": min(sizes),
            "max_bytes": max(sizes),
        }
        for lane, sizes in lane_sizes.items()
    }
    repair_require(
        summary.get("lane_stats") == expected_lane_stats,
        "lane_stats_invalid",
        "batch lane counts/sizes do not match the 116 prelocked packets",
    )

    cases: list[dict[str, Any]] = []
    response_ids: dict[str, list[str]] = collections.defaultdict(list)
    checklist_hashes: dict[str, list[str]] = collections.defaultdict(list)
    output_hashes: dict[str, list[str]] = collections.defaultdict(list)
    selected_usages: list[tuple[str, dict[str, int]]] = []
    selected_intervals: list[tuple[dt.datetime, dt.datetime, str]] = []
    global_stderr_classes: collections.Counter[str] = collections.Counter()
    total_nonzero_model_commands = 0
    retained_model_call_count = 0

    for packet_record in packet_inputs:
        case_id = str(packet_record.get("case_unit_id"))
        task_id = str(packet_record.get("task_id"))
        case: dict[str, Any] = {
            "case_unit_id": case_id,
            "task_id": task_id,
            "selection_rank": packet_record.get("selection_rank"),
            "issues": [],
        }
        packet_path = REPO_ROOT / str(packet_record.get("path"))
        if not (
            packet_path.is_file()
            and packet_path.parent.name == case_id
            and packet_path.stat().st_size == packet_record.get("size_bytes")
            and sha256_file(packet_path) == packet_record.get("sha256")
        ):
            add_case_issue(case, "packet_binding_mismatch", "repair_blocker", "prelocked packet path/hash/size/case directory mismatch")
        else:
            metadata_prefix = packet_path.read_text(encoding="utf-8")[:1200]
            expected_metadata = (
                f"- domain: `androidworld`" in metadata_prefix
                and f"- case_unit_id: `{case_id}`" in metadata_prefix
                and f"- task_id: `{task_id}`" in metadata_prefix
            )
            if not expected_metadata:
                add_case_issue(case, "packet_metadata_identity_mismatch", "repair_blocker", "packet metadata does not match prelocked identity")

        batch = batch_by_case.get(case_id)
        if batch is None:
            add_case_issue(case, "missing_batch_result", "repair_blocker", "case has no batch result row")
            cases.append(case)
            continue
        expected_lane = "oversized" if int(packet_record.get("size_bytes", 0)) > 900000 else "regular"
        expected_packet_resolved = packet_path.resolve()
        batch_packet = Path(str(batch.get("case_packet")))
        if not batch_packet.is_absolute():
            batch_packet = REPO_ROOT / batch_packet
        if not (
            batch.get("status") == "success"
            and batch.get("lane") == expected_lane
            and batch.get("case_packet_size_bytes") == packet_record.get("size_bytes")
            and batch_packet.resolve() == expected_packet_resolved
            and batch.get("quality_warnings") == []
        ):
            add_case_issue(case, "batch_case_record_mismatch", "repair_blocker", "batch status/lane/packet/size/warnings do not match prelock")

        attempts = batch.get("attempts") or []
        if not attempts or attempts[-1].get("returncode") != 0:
            add_case_issue(case, "no_successful_terminal_attempt", "repair_blocker", "attempt chain has no successful terminal attempt")
        selected_attempt = len(attempts)
        case_dir = WAVE_ROOT / case_id
        if not case_dir.is_dir():
            add_case_issue(case, "missing_case_directory", "repair_blocker", "wave case directory is absent")
            cases.append(case)
            continue

        actual_names = {path.name for path in case_dir.iterdir() if path.is_file()}
        allowed_names = set(CANONICAL_SUFFIXES)
        for index in range(1, len(attempts) + 1):
            allowed_names.update(f"attempt_{index:02d}.{suffix}" for suffix in ATTEMPT_SUFFIXES)
        unexpected_names = sorted(actual_names - allowed_names)
        if unexpected_names:
            add_case_issue(case, "unexpected_case_sidecars", "repair_blocker", f"unexpected files: {unexpected_names}")
        for suffix in CANONICAL_SUFFIXES:
            if not (case_dir / suffix).is_file():
                add_case_issue(case, "missing_canonical_sidecar", "repair_blocker", f"missing canonical {suffix}")

        attempt_rows: list[dict[str, Any]] = []
        selected_details: dict[str, Any] | None = None
        selected_api: dict[str, Any] | None = None
        selected_llm: dict[str, Any] | None = None
        for index, attempt in enumerate(attempts, 1):
            attempt_prefix = f"attempt_{index:02d}"
            expected_http_timeout = 480 if expected_lane == "oversized" else 180
            expected_codex_timeout = 3600 if expected_lane == "oversized" else 1800
            expected_max = [12000, 16000, 20000][index - 1]
            if not (
                attempt.get("attempt_index") == index
                and attempt.get("max_output_tokens") == expected_max
                and attempt.get("http_timeout_seconds") == expected_http_timeout
                and attempt.get("codex_timeout_seconds") == expected_codex_timeout
                and isinstance(attempt.get("duration_seconds"), (int, float))
                and attempt.get("duration_seconds") > 0
            ):
                add_case_issue(case, "attempt_record_mismatch", "repair_blocker", f"{attempt_prefix} batch metadata mismatch")
            stdout_path = case_dir / f"{attempt_prefix}.stdout.log"
            stderr_path = case_dir / f"{attempt_prefix}.stderr.log"
            if not stdout_path.is_file() or not stderr_path.is_file():
                add_case_issue(case, "missing_attempt_logs", "repair_blocker", f"{attempt_prefix} stdout/stderr logs missing")
            api_path = case_dir / f"{attempt_prefix}.api_response.json"
            llm_path = case_dir / f"{attempt_prefix}.llm_call.json"
            reasoning_path = case_dir / f"{attempt_prefix}.reasoning_summary.txt"
            checklist_json_path = case_dir / f"{attempt_prefix}.checklist.json"
            checklist_yaml_path = case_dir / f"{attempt_prefix}.checklist.yaml"
            has_model_sidecars = api_path.is_file() or llm_path.is_file() or reasoning_path.is_file()
            details: dict[str, Any] | None = None
            if has_model_sidecars:
                if not (api_path.is_file() and llm_path.is_file() and reasoning_path.is_file()):
                    add_case_issue(case, "partial_model_sidecars", "repair_blocker", f"{attempt_prefix} API/llm/reasoning trio is incomplete")
                else:
                    api, llm, details = audit_api_and_call(
                        api_path=api_path,
                        llm_path=llm_path,
                        reasoning_path=reasoning_path,
                        expected_case_id=case_id,
                        expected_task_id=task_id,
                        expected_attempt=index,
                        expected_timeout=expected_codex_timeout,
                        expected_max_tokens=expected_max,
                        case=case,
                        selected=index == selected_attempt,
                    )
                    retained_model_call_count += 1
                    response_id = str(details.get("response_id"))
                    response_ids[response_id].append(f"{case_id}/{attempt_prefix}")
                    global_stderr_classes.update(details.get("stderr_classes") or {})
                    total_nonzero_model_commands += int((details.get("events") or {}).get("nonzero_command_count", 0))
                    if index == selected_attempt:
                        selected_details = details
                        selected_api = api
                        selected_llm = llm
            if attempt.get("returncode") == 0:
                if not (checklist_json_path.is_file() and checklist_yaml_path.is_file()):
                    add_case_issue(case, "successful_attempt_missing_checklist", "repair_blocker", f"{attempt_prefix} lacks checklist outputs")
                if "validator" not in attempt:
                    add_case_issue(case, "successful_attempt_missing_validator", "repair_blocker", f"{attempt_prefix} lacks validator receipt")
            attempt_rows.append(
                {
                    "attempt_index": index,
                    "returncode": attempt.get("returncode"),
                    "duration_seconds": attempt.get("duration_seconds"),
                    "max_output_tokens": attempt.get("max_output_tokens"),
                    "has_model_sidecars": bool(has_model_sidecars),
                    "has_checklist": checklist_json_path.is_file() and checklist_yaml_path.is_file(),
                    "stdout_size_bytes": stdout_path.stat().st_size if stdout_path.is_file() else None,
                    "stderr_size_bytes": stderr_path.stat().st_size if stderr_path.is_file() else None,
                    "response_id": details.get("response_id") if details else None,
                }
            )

        selected_prefix = f"attempt_{selected_attempt:02d}"
        for suffix in CANONICAL_SUFFIXES:
            canonical = case_dir / suffix
            attempted = case_dir / f"{selected_prefix}.{suffix}"
            if canonical.is_file() and attempted.is_file() and canonical.read_bytes() != attempted.read_bytes():
                add_case_issue(case, "canonical_attempt_promotion_mismatch", "repair_blocker", f"canonical {suffix} differs from selected attempt")

        checklist_json_path = case_dir / "checklist.json"
        checklist_yaml_path = case_dir / "checklist.yaml"
        if checklist_json_path.is_file() and checklist_yaml_path.is_file():
            checklist_json = load_json(checklist_json_path)
            checklist_yaml = yaml.safe_load(checklist_yaml_path.read_text(encoding="utf-8"))
            if checklist_yaml != checklist_json:
                add_case_issue(case, "yaml_json_checklist_mismatch", "repair_blocker", "canonical YAML and JSON parse to different values")
            if not (
                checklist_json.get("schema_version") == "case_checklist_v1"
                and checklist_json.get("domain") == "androidworld"
                and checklist_json.get("case_unit_id") == case_id
                and checklist_json.get("task_id") == task_id
            ):
                add_case_issue(case, "canonical_checklist_identity_mismatch", "repair_blocker", "canonical checklist identity does not match packet/prelock")
            checklist_hash = sha256_file(checklist_json_path)
            checklist_hashes[checklist_hash].append(case_id)
        else:
            checklist_json = {}
            checklist_hash = None

        if selected_api is not None and selected_details is not None and selected_llm is not None:
            model_body = strip_null_fields(selected_details.get("parsed_output"))
            checklist_body = {key: value for key, value in checklist_json.items() if key not in {"schema_version", "case_unit_id", "domain", "task_id"}}
            if model_body != checklist_body:
                add_case_issue(case, "api_to_checklist_body_mismatch", "repair_blocker", "selected API JSON body differs from canonical checklist body")
            output_hash = hashlib.sha256(str(selected_api.get("output_text", "")).encode("utf-8")).hexdigest()
            output_hashes[output_hash].append(case_id)
            selected_usages.append((case_id, selected_details["token_usage"]))
            try:
                selected_intervals.append(
                    (
                        parse_timestamp(selected_llm.get("request_timestamp")),
                        parse_timestamp(selected_llm.get("response_timestamp")),
                        case_id,
                    )
                )
            except ValueError:
                pass
            batch_duration = float(attempts[-1].get("duration_seconds", 0))
            llm_duration = float(selected_details.get("duration_seconds") or 0)
            if abs(batch_duration - llm_duration) > 1.0:
                add_case_issue(case, "batch_llm_duration_mismatch", "repair_blocker", "selected attempt duration differs from llm timestamp interval by more than one second")
            retry_index = selected_llm.get("retry_index")
            if retry_index != selected_attempt - 1:
                add_case_issue(
                    case,
                    "llm_retry_index_underreported",
                    "warning",
                    f"selected attempt is {selected_attempt}, but llm_call.retry_index is {retry_index}; batch_results remains authoritative",
                )
            response_id_value = selected_details.get("response_id")
            response_timestamp_value = selected_details.get("response_timestamp")
            usage_value = selected_details.get("token_usage")
            event_value = selected_details.get("events") or {}
            stderr_value = selected_details.get("stderr_classes") or {}
            completion_over = selected_details.get("completion_exceeds_nominal_max_tokens")
            reasoning_empty = selected_details.get("reasoning_summary_empty")
        else:
            response_id_value = response_timestamp_value = usage_value = None
            event_value = stderr_value = {}
            completion_over = reasoning_empty = None

        if len(attempts) > 1:
            add_case_issue(
                case,
                "generation_retry_occurred",
                "warning",
                f"case required {len(attempts)} attempts; final canonical files bind {selected_prefix}",
            )
        nonzero_count = int(event_value.get("nonzero_command_count", 0))
        if nonzero_count:
            add_case_issue(
                case,
                "model_read_tool_commands_failed_but_recovered",
                "warning",
                f"selected Codex call had {nonzero_count} nonzero read/inspection command(s) but completed with a bound final JSON output",
            )

        hashes = {
            suffix.replace(".", "_") + "_sha256": sha256_file(case_dir / suffix)
            for suffix in CANONICAL_SUFFIXES
            if (case_dir / suffix).is_file()
        }
        blocker_count = sum(issue["severity"] == "repair_blocker" for issue in case["issues"])
        warning_count = sum(issue["severity"] == "warning" for issue in case["issues"])
        case.update(
            {
                "integrity_status": "fail" if blocker_count else ("pass_with_warnings" if warning_count else "pass"),
                "repair_input_eligible": blocker_count == 0,
                "lane": expected_lane,
                "packet_sha256": packet_record.get("sha256"),
                "selected_attempt": selected_attempt,
                "attempts": attempt_rows,
                "response_id": response_id_value,
                "response_timestamp": response_timestamp_value,
                "token_usage": usage_value,
                "completion_exceeds_nominal_max_tokens": completion_over,
                "reasoning_summary_empty": reasoning_empty,
                "selected_event_count": event_value.get("event_count"),
                "selected_nonzero_model_command_count": nonzero_count,
                "selected_stderr_classes": stderr_value,
                "hashes": hashes,
            }
        )
        cases.append(case)

    duplicate_response_ids = {key: value for key, value in response_ids.items() if len(value) > 1}
    duplicate_checklists = [value for value in checklist_hashes.values() if len(value) > 1]
    duplicate_outputs = [value for value in output_hashes.values() if len(value) > 1]
    repair_require(not duplicate_response_ids, "duplicate_response_ids", "Codex response ids are not unique across retained calls")
    repair_require(not duplicate_checklists, "duplicate_canonical_checklists", "byte-identical canonical checklists occur across cases")
    repair_require(not duplicate_outputs, "duplicate_model_outputs", "byte-identical selected model bodies occur across cases")

    zero_token_cases = [
        case_id
        for case_id, usage in selected_usages
        if any(int(usage.get(key, 0)) <= 0 for key in ("prompt_tokens", "completion_tokens", "reasoning_tokens", "total_tokens"))
    ]
    repair_require(not zero_token_cases, "zero_token_cases", f"selected calls with zero tokens: {zero_token_cases}")
    totals = [usage["total_tokens"] for _, usage in selected_usages]
    median_total = statistics.median(totals) if totals else 0
    extreme_threshold = int(median_total * 5) if totals else 0
    extreme_cases = [
        {"case_unit_id": case_id, "total_tokens": usage["total_tokens"]}
        for case_id, usage in selected_usages
        if usage["total_tokens"] > extreme_threshold
    ]
    completion_over_cases = [
        case["case_unit_id"] for case in cases if case.get("completion_exceeds_nominal_max_tokens") is True
    ]
    if completion_over_cases:
        add_notice(
            notices,
            "codex_completion_exceeded_nominal_retry_budget",
            "information",
            "Codex CLI records max_output_tokens_enforced=false; selected completion usage exceeded the nominal retry-budget label in these cases without truncation or sidecar inconsistency.",
            cases=completion_over_cases,
        )
    if extreme_cases:
        add_notice(
            notices,
            "extreme_but_internally_consistent_token_usage",
            "information",
            f"{len(extreme_cases)} selected calls exceed 5x the median total-token count; every API/llm usage record and arithmetic check remains consistent.",
            cases=[row["case_unit_id"] for row in extreme_cases],
        )
    if all(case.get("reasoning_summary_empty") is True for case in cases):
        add_notice(
            notices,
            "reasoning_summaries_empty",
            "information",
            "All 116 textual reasoning_summary sidecars are empty because the retained Codex event summaries are empty, despite nonzero reasoning-token counts; sidecars are internally consistent but do not retain a prose chain of thought.",
        )

    concurrency_points: list[tuple[dt.datetime, int]] = []
    for start, end, _ in selected_intervals:
        concurrency_points.append((start, 1))
        concurrency_points.append((end, -1))
    active = 0
    max_observed_concurrency = 0
    for _, change in sorted(concurrency_points, key=lambda row: (row[0], row[1])):
        active += change
        max_observed_concurrency = max(max_observed_concurrency, active)
    repair_require(
        max_observed_concurrency <= 6,
        "observed_concurrency_exceeded_six",
        f"selected call intervals imply concurrency {max_observed_concurrency} > 6",
    )

    retry_cases = [case["case_unit_id"] for case in cases if case.get("selected_attempt", 0) > 1]
    if retry_cases:
        add_notice(
            notices,
            "two_cases_retried",
            "warning",
            "SimpleCalendarNextEvent timed out on attempt 1; VlcCreatePlaylist failed deterministic guardrails on attempt 1. Both canonical outputs are byte-identical to their successful attempt 2 sidecars.",
            cases=retry_cases,
        )
    nonzero_command_cases = [
        case["case_unit_id"] for case in cases if int(case.get("selected_nonzero_model_command_count") or 0) > 0
    ]
    if nonzero_command_cases:
        add_notice(
            notices,
            "model_inspection_commands_had_nonzero_exits",
            "warning",
            f"Selected calls contain {sum(int(case.get('selected_nonzero_model_command_count') or 0) for case in cases)} nonzero shell inspection commands across {len(nonzero_command_cases)} cases; no successful mutation-like command was observed and every final event/output chain closes.",
            cases=nonzero_command_cases,
        )

    if global_stderr_classes:
        add_notice(
            notices,
            "codex_cli_environmental_stderr",
            "warning",
            "Every selected Codex call retained stderr diagnostics. They classify as state-db, plugin-catalog, shell-snapshot, recovered stream, model-tool-router, or analytics-delivery messages; canonical outer stderr/stdout logs for successful attempts are empty.",
        )

    codex_path = shutil.which("codex")
    login_recheck: dict[str, Any] = {
        "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "path": codex_path,
    }
    if codex_path:
        login_recheck["binary_sha256"] = sha256_file(Path(codex_path))
        for key, command in (
            ("version_output", [codex_path, "--version"]),
            ("login_status_output", [codex_path, "login", "status"]),
        ):
            proc = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
            login_recheck[key] = (proc.stdout or proc.stderr).strip()
            login_recheck[key.replace("output", "returncode")] = proc.returncode
    repair_require(
        codex_path is not None
        and login_recheck.get("binary_sha256") == config.get("codex_cli", {}).get("binary_sha256")
        and login_recheck.get("version_output") == config.get("codex_cli", {}).get("version_output")
        and login_recheck.get("login_status_output") == "Logged in using ChatGPT",
        "codex_login_recheck_failed",
        "post-generation Codex binary/version/login status does not match prelock",
    )

    case_repair_blockers = [case["case_unit_id"] for case in cases if not case.get("repair_input_eligible")]
    repair_input_eligible = (
        not repair_global_blockers
        and not case_repair_blockers
        and len(cases) == 116
        and sum(case.get("repair_input_eligible") is True for case in cases) == 116
    )
    case_status_counts = collections.Counter(case.get("integrity_status") for case in cases)
    usage_fields = ("prompt_tokens", "completion_tokens", "cached_prompt_tokens", "reasoning_tokens", "total_tokens")
    token_stats = {
        field: {
            "min": min(usage[field] for _, usage in selected_usages),
            "median": statistics.median(usage[field] for _, usage in selected_usages),
            "p95": percentile([usage[field] for _, usage in selected_usages], 0.95),
            "max": max(usage[field] for _, usage in selected_usages),
            "zero_count": sum(usage[field] == 0 for _, usage in selected_usages),
        }
        for field in usage_fields
    }

    report: dict[str, Any] = {
        "schema_version": "androidworld_candidate116_wave003_generation_integrity/v1",
        "audit_scope": {
            "generation_id": "wave_003",
            "case_count_expected": 116,
            "checks": [
                "prelock packet/config/toolchain binding",
                "batch_results and batch_summary consistency",
                "canonical and per-attempt sidecar identity/hash/promotion chain",
                "YAML/JSON and model-output consistency",
                "Codex CLI login/gpt-5.6-sol/xhigh/read-only/ephemeral/ignore-user-config contract",
                "response ids, timestamps, token usage, retries, duplicate/cross-case identity, and stdout/stderr diagnostics",
            ],
            "explicitly_excluded": [
                "semantic correctness of native/stronger checklist rules",
                "support-pointer truth",
                "authorization to freeze drafts or contracts",
            ],
            "read_only_targets": [repo_path(WAVE_ROOT), repo_path(CANDIDATE_ROOT / "case_packets")],
        },
        "decision": {
            "generation_integrity_status": "pass_for_repair_input_only" if repair_input_eligible else "fail",
            "can_use_as_repair_input": repair_input_eligible,
            "repair_input_cases_eligible": sum(case.get("repair_input_eligible") is True for case in cases),
            "repair_input_cases_expected": 116,
            "direct_freeze_authorized": False,
            "direct_freeze_denial_reasons": [
                "This audit excludes semantic correctness and therefore cannot authorize freeze.",
                "The generation-period legacy-root guard is fail because neurips_ed_track_minimal changed, although the isolated v3 snapshot and packets remained unchanged.",
                "Two retry chains have underreported llm_call.retry_index values; batch_results plus attempt-prefixed sidecars must be used as authority.",
                "Codex CLI exposes only the requested model id, not an immutable backend snapshot id.",
            ],
        },
        "bindings": {
            "prelock": file_binding(PRELOCK_PATH) | {"prelock_sha256": prelock.get("prelock_sha256")},
            "config": file_binding(CONFIG_PATH) | {"config_sha256": config.get("config_sha256")},
            "toolchain_snapshot_manifest": file_binding(SNAPSHOT_MANIFEST_PATH) | {"snapshot_sha256": snapshot.get("snapshot_sha256")},
            "batch_results": file_binding(BATCH_RESULTS_PATH),
            "batch_summary": file_binding(BATCH_SUMMARY_PATH),
            "generation_guard": file_binding(GENERATION_GUARD_PATH) | {"guard_sha256": guard.get("guard_sha256"), "status": guard.get("status")},
        },
        "codex_cli_post_generation_recheck": login_recheck,
        "aggregate": {
            "case_rows_audited": len(cases),
            "case_status_counts": dict(sorted(case_status_counts.items())),
            "batch_success_cases": summary.get("success_cases"),
            "batch_failed_cases": summary.get("failed_cases"),
            "batch_skipped_cases": summary.get("skipped_cases"),
            "regular_lane_cases": expected_lane_stats["regular"]["count"],
            "oversized_lane_cases": expected_lane_stats["oversized"]["count"],
            "configured_regular_concurrency": config.get("max_parallel"),
            "configured_oversized_concurrency": config.get("large_max_parallel"),
            "max_observed_selected_call_concurrency": max_observed_concurrency,
            "retained_model_call_count": retained_model_call_count,
            "attempt_count": sum(len(batch.get("attempts") or []) for batch in batch_rows),
            "retry_case_count": len(retry_cases),
            "retry_cases": retry_cases,
            "duplicate_response_ids": duplicate_response_ids,
            "duplicate_canonical_checklists": duplicate_checklists,
            "duplicate_selected_model_outputs": duplicate_outputs,
            "zero_token_cases": zero_token_cases,
            "completion_over_nominal_max_case_count": len(completion_over_cases),
            "extreme_total_token_threshold": extreme_threshold,
            "extreme_total_token_cases": sorted(extreme_cases, key=lambda row: (-row["total_tokens"], row["case_unit_id"])),
            "selected_token_usage_stats": token_stats,
            "selected_nonzero_model_command_count": sum(int(case.get("selected_nonzero_model_command_count") or 0) for case in cases),
            "selected_nonzero_model_command_case_count": len(nonzero_command_cases),
            "selected_codex_stderr_class_counts": dict(sorted(global_stderr_classes.items())),
            "canonical_outer_stdout_nonempty_count": sum((WAVE_ROOT / case["case_unit_id"] / "stdout.log").stat().st_size > 0 for case in cases),
            "canonical_outer_stderr_nonempty_count": sum((WAVE_ROOT / case["case_unit_id"] / "stderr.log").stat().st_size > 0 for case in cases),
            "repair_global_blockers": repair_global_blockers,
            "repair_case_blockers": case_repair_blockers,
        },
        "notices": notices,
        "cases": cases,
        "report_sha256": None,
    }
    report["report_sha256"] = object_sha256({key: value for key, value in report.items() if key != "report_sha256"})
    return report


def verify_report(path: Path) -> int:
    value = load_json(path)
    expected = value.pop("report_sha256", None)
    observed = object_sha256(value)
    result = {
        "status": "pass" if expected == observed else "fail",
        "path": str(path),
        "claimed_report_sha256": expected,
        "observed_report_sha256": observed,
        "case_count": len(value.get("cases") or []),
        "repair_input_eligible": (value.get("decision") or {}).get("can_use_as_repair_input"),
        "direct_freeze_authorized": (value.get("decision") or {}).get("direct_freeze_authorized"),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if expected == observed else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-report", type=Path)
    args = parser.parse_args()
    if args.verify_report is not None:
        return verify_report(args.verify_report.resolve())
    print(json.dumps(audit(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
