#!/usr/bin/env python3
"""Fail-closed audit and post-score label join for the AppWorld-68 blind batch.

The released evaluator artifacts are not opened until every blind score, lock,
pointer, denominator, and execution setting has passed validation.  The join is
written to a new directory; the blind score tree is never modified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

import yaml
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PUBLIC_JOB_ROOT = (
    REPO_ROOT
    / "transfer"
    / "appworld68_tn_blind_score_system_design_v3_20260719_v1"
    / "public_score_job"
)
DEFAULT_RUN_ROOT = Path("/Users/gss/Downloads/appworld585_20260719_full_v1_completed")
DEFAULT_JOIN_ROOT = (
    REPO_ROOT / "results" / "appworld68_tn_blind_score_system_design_v3_joined_v1"
)

EXPECTED_CASES = 68
EXPECTED_AGENTS = ("agent_a", "agent_b", "agent_c")
EXPECTED_RECORDS = EXPECTED_CASES * len(EXPECTED_AGENTS)
EXPECTED_NATIVE_CHECKS = 1_407
EXPECTED_STRONGER_CHECKS = 132
EXPECTED_MODEL = "gpt-5.4"
EXPECTED_REASONING = "high"
EXPECTED_SERVICE_TIER = "default"
EXPECTED_PARALLELISM = 34
EXPECTED_SANDBOX = "read-only"
EXPECTED_AUTH_MODE = "codex_login"

TEST_MARKER_RE = re.compile(r"\[(appworld_test_[A-Za-z0-9._-]+)\]")
HEX_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
LINE_SPAN_RE = re.compile(
    r"^(?:L(?P<ls>\d+)(?:-L?(?P<le>\d+))?"
    r"|lines?\s+(?P<ws>\d+)(?:-(?P<we>\d+))?"
    r"|line_span:(?P<ss>\d+)-(?P<se>\d+)"
    r"|(?P<ns>\d+)-(?P<ne>\d+))$",
    re.IGNORECASE,
)
STRUCTURED_TOKEN_RE = re.compile(r"([^.\[\]]+)|\[(\d+)\]")
SYMBOL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")

FORBIDDEN_POINTER_BASENAMES = frozenset(
    {
        "released_evaluator_label.json",
        "native_label.json",
        "native_evaluator_output.json",
        "evaluator_output.json",
        "evaluator_results.json",
        "component_evaluator_outputs.json",
        "testtracker.json",
        "test_tracker.json",
        "test_tracker_output.json",
        "test_tracker_results.json",
        "run_summary.json",
        "raw_run.json",
        "artifact_manifest.json",
        "report.md",
        "evidence_index.txt",
        "index.json",
    }
)
FORBIDDEN_POINTER_PARTS = frozenset(
    {
        "evaluation",
        "released_label_source",
        "released_evaluator_results",
        "component_evaluator_outputs",
    }
)
FORBIDDEN_INPUT_BASENAMES = frozenset(
    {
        "released_evaluator_label.json",
        "native_label.json",
        "native_evaluator_output.json",
        "evaluator_output.json",
        "evaluator_results.json",
        "component_evaluator_outputs.json",
        "testtracker.json",
        "test_tracker.json",
        "test_tracker_output.json",
        "test_tracker_results.json",
        "run_summary.json",
        "raw_run.json",
        "artifact_manifest.json",
        "report.md",
    }
)
FORBIDDEN_BLIND_KEYS = frozenset(
    {
        "released_evaluator_label",
        "released_label",
        "native_label",
        "component_evaluator_outputs",
        "benchmark_conflict",
    }
)


class AuditError(RuntimeError):
    """A fail-closed audit precondition was not satisfied."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-job-root", type=Path, default=DEFAULT_PUBLIC_JOB_ROOT)
    parser.add_argument("--blind-output-root", type=Path, required=True)
    parser.add_argument("--batch-state-root", type=Path, required=True)
    parser.add_argument("--retained-run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_JOIN_ROOT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Revalidate an existing joined output without modifying it.",
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, label: str) -> dict[str, Any]:
    require_regular_file(path, label)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"cannot parse {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AuditError(f"{label} must be a JSON object: {path}")
    return value


def load_yaml(path: Path, label: str) -> dict[str, Any]:
    require_regular_file(path, label)
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise AuditError(f"cannot parse {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AuditError(f"{label} must be a YAML object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def require_regular_file(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise AuditError(f"{label} is missing or not a regular file: {path}")


def require_regular_tree(root: Path, label: str) -> None:
    if root.is_symlink() or not root.is_dir():
        raise AuditError(f"{label} is missing or not a real directory: {root}")
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        parent = Path(dirpath)
        for name in [*dirnames, *filenames]:
            path = parent / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise AuditError(f"{label} contains a symlink: {path}")
            if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise AuditError(f"{label} contains a special file: {path}")


def file_entries(root: Path) -> list[dict[str, Any]]:
    require_regular_tree(root, "tree")
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    ]


def tree_sha256(root: Path) -> str:
    """Hash compatible with the blind scorer/batch task evidence-tree lock."""

    entries = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    ]
    return sha256_bytes(canonical_json_bytes(entries))


def package_entries_sha256(entries: Sequence[Mapping[str, Any]]) -> str:
    return sha256_bytes(canonical_json_bytes(list(entries)))


def safe_relative(value: Any, label: str) -> str:
    raw = str(value or "")
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise AuditError(f"unsafe {label}: {raw!r}")
    return path.as_posix()


def require_sha(value: Any, label: str) -> str:
    text = str(value or "")
    if not HEX_SHA256_RE.fullmatch(text):
        raise AuditError(f"{label} is not a lowercase SHA-256: {text!r}")
    return text


def binding_sha(binding: Any, label: str) -> str:
    if not isinstance(binding, dict):
        raise AuditError(f"{label} binding is missing")
    return require_sha(binding.get("sha256"), f"{label}.sha256")


def binding_matches_file(binding: Any, path: Path, label: str) -> None:
    expected = binding_sha(binding, label)
    bound_name = Path(str(binding.get("path") or "")).name
    if bound_name != path.name:
        raise AuditError(
            f"{label} path basename differs: {bound_name!r} != {path.name!r}"
        )
    if sha256_file(path) != expected:
        raise AuditError(f"{label} SHA-256 differs: {path}")


def expected_task_ids(package: dict[str, Any]) -> tuple[list[str], dict[str, dict[str, Any]]]:
    scope = package.get("scope")
    records = package.get("records")
    if not isinstance(scope, dict) or not isinstance(records, list):
        raise AuditError("public package scope/records is malformed")
    if (
        scope.get("case_count") != EXPECTED_CASES
        or scope.get("record_count") != EXPECTED_RECORDS
        or len(records) != EXPECTED_RECORDS
    ):
        raise AuditError("public package denominator differs from 68 cases / 204 records")
    if package.get("records_sha256") != sha256_bytes(canonical_json_bytes(records)):
        raise AuditError("public package records aggregate SHA-256 differs")
    case_ids = scope.get("case_ids")
    if (
        not isinstance(case_ids, list)
        or len(case_ids) != EXPECTED_CASES
        or len(set(case_ids)) != EXPECTED_CASES
        or not all(isinstance(value, str) and value for value in case_ids)
    ):
        raise AuditError("public package case-id denominator differs")
    if scope.get("case_ids_sha256") != sha256_bytes(canonical_json_bytes(case_ids)):
        raise AuditError("public package case-id SHA-256 differs")
    result: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise AuditError("public package record is not an object")
        task_id = str(record.get("task_id") or "")
        case_id = str(record.get("case_unit_id") or "")
        agent_id = str(record.get("agent_id") or "")
        if task_id != f"{case_id}__{agent_id}" or agent_id not in EXPECTED_AGENTS:
            raise AuditError(f"invalid public task identity: {task_id!r}")
        if task_id in result:
            raise AuditError(f"duplicate public task id: {task_id}")
        result[task_id] = record
    by_case = {
        case_id: {
            str(record.get("agent_id") or "")
            for record in records
            if isinstance(record, dict) and record.get("case_unit_id") == case_id
        }
        for case_id in case_ids
    }
    if set(by_case) != set(case_ids) or any(
        agents != set(EXPECTED_AGENTS) for agents in by_case.values()
    ):
        raise AuditError("public package does not contain all three agents for every case")
    return sorted(result), result


def validate_scoring_config(value: Mapping[str, Any], label: str) -> None:
    expected = {
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING,
        "service_tier": EXPECTED_SERVICE_TIER,
        "fast_mode": False,
        "sandbox": EXPECTED_SANDBOX,
    }
    for key, wanted in expected.items():
        if value.get(key) != wanted:
            raise AuditError(f"{label}.{key} differs: {value.get(key)!r} != {wanted!r}")
    parallel = value.get("max_parallel", value.get("requested_parallelism"))
    if parallel != EXPECTED_PARALLELISM:
        raise AuditError(
            f"{label} parallelism differs: {parallel!r} != {EXPECTED_PARALLELISM}"
        )
    if value.get("auth_mode") != EXPECTED_AUTH_MODE:
        raise AuditError(
            f"{label}.auth_mode differs: {value.get('auth_mode')!r} != {EXPECTED_AUTH_MODE!r}"
        )


def validate_restricted_identity(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AuditError(f"{label} restricted model identity is missing")
    username = str(value.get("username") or "")
    if (
        not username
        or username in {"root", "draftsvc"}
        or not isinstance(value.get("uid"), int)
        or value.get("uid") == 0
        or not str(value.get("groupname") or "")
        or not isinstance(value.get("gid"), int)
        or value.get("orchestrator_uid") != 0
    ):
        raise AuditError(f"{label} restricted model identity is invalid")
    return {
        "username": username,
        "uid": value["uid"],
        "groupname": value["groupname"],
        "gid": value["gid"],
        "orchestrator_uid": value["orchestrator_uid"],
    }


def validate_public_package(public_root: Path) -> tuple[dict[str, Any], list[str], dict[str, dict[str, Any]]]:
    require_regular_tree(public_root, "public blind score job")
    package_path = public_root / "package_manifest.json"
    package = load_json(package_path, "public package manifest")
    if package.get("schema_version") != "appworld68_blind_score_input_package.v3":
        raise AuditError("public package schema version differs")
    scoring_lock = package.get("scoring_lock")
    if not isinstance(scoring_lock, dict):
        raise AuditError("public package scoring_lock is missing")
    validate_scoring_config(scoring_lock, "public package scoring_lock")
    if scoring_lock.get("released_result_join") != "local_only_after_blind_score_sha256_lock":
        raise AuditError("public package post-score join boundary differs")
    outcome_blind = package.get("outcome_blind")
    if not isinstance(outcome_blind, dict) or any(
        outcome_blind.get(key) is not False
        for key in (
            "released_labels_present",
            "component_evaluator_outputs_present",
            "evaluator_reports_present",
        )
    ):
        raise AuditError("public package is not declared outcome-blind")
    task_ids, records = expected_task_ids(package)
    actual_dirs = sorted(
        path.name for path in (public_root / "tasks").iterdir() if path.is_dir()
    )
    if actual_dirs != task_ids:
        raise AuditError("public task-directory set differs from the 204-record manifest")
    for task_id in task_ids:
        record = records[task_id]
        task_dir = public_root / "tasks" / task_id
        checklist = task_dir / "checklist.yaml"
        evidence = task_dir / "evidence"
        if sha256_file(checklist) != record.get("checklist_sha256"):
            raise AuditError(f"public checklist SHA-256 differs: {task_id}")
        entries = file_entries(evidence)
        for entry in entries:
            relative = PurePosixPath(str(entry["path"]))
            if relative.name.lower() in FORBIDDEN_INPUT_BASENAMES or any(
                part.lower() in FORBIDDEN_POINTER_PARTS for part in relative.parts
            ):
                raise AuditError(
                    f"public scorer input contains a result-bearing artifact: "
                    f"{task_id}/evidence/{relative.as_posix()}"
                )
        index_path = evidence / "index.json"
        if sha256_file(index_path) != record.get("evidence_index_sha256"):
            raise AuditError(f"public evidence index SHA-256 differs: {task_id}")
        index = load_json(index_path, "public blind evidence index")
        if (
            index.get("case_unit_id") != record.get("case_unit_id")
            or index.get("agent_id") != record.get("agent_id")
            or index.get("source_vps") != record.get("source_vps")
            or index.get("released_result_artifacts_present") is not False
            or index.get("component_evaluator_outputs_present") is not False
            or index.get("evaluator_reports_present") is not False
        ):
            raise AuditError(f"public evidence index blind contract differs: {task_id}")
        before_index = [entry for entry in entries if entry["path"] != "index.json"]
        if index.get("files") != before_index or index.get(
            "files_sha256"
        ) != package_entries_sha256(before_index):
            raise AuditError(f"public evidence index inventory differs: {task_id}")
        if len(entries) != record.get("evidence_file_count"):
            raise AuditError(f"public evidence file count differs: {task_id}")
        if package_entries_sha256(entries) != record.get("evidence_files_sha256"):
            raise AuditError(f"public evidence aggregate SHA-256 differs: {task_id}")
    return package, task_ids, records


def load_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    require_regular_file(path, label)
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AuditError(f"invalid {label} at line {line_no}: {exc}") from exc
        if not isinstance(value, dict):
            raise AuditError(f"{label} line {line_no} is not an object")
        rows.append(value)
    return rows


def validate_batch_state(
    state_root: Path, task_ids: Sequence[str]
) -> dict[str, Any]:
    require_regular_tree(state_root, "blind batch state")
    plan_path = state_root / "_task_plan.json"
    summary_path = state_root / "_batch_summary.json"
    results_path = state_root / "_task_results.jsonl"
    plan = load_json(plan_path, "blind batch task plan")
    summary = load_json(summary_path, "blind batch summary")
    rows = load_jsonl(results_path, "blind batch task results")
    validate_scoring_config(
        {
            **plan,
            "auth_mode": plan.get("auth_mode", EXPECTED_AUTH_MODE),
            "fast_mode": plan.get(
                "fast_mode", str(plan.get("service_tier", "")).lower() == "fast"
            ),
        },
        "batch task plan",
    )
    if plan.get("blind_mode") is not True or plan.get("task_count") != EXPECTED_RECORDS:
        raise AuditError("batch task plan is not a 204-record blind plan")
    planned = plan.get("tasks")
    if not isinstance(planned, list) or sorted(
        str(row.get("task_id") or "") for row in planned if isinstance(row, dict)
    ) != list(task_ids):
        raise AuditError("batch task-plan task set differs")
    for row in planned:
        if not isinstance(row, dict) or row.get("blind_mode") is not True:
            raise AuditError("batch task-plan contains a non-blind task")
        if any(key in row for key in ("native_label", "native_label_path", "native_label_sha256")):
            raise AuditError("batch task-plan contains a released-label binding")
    if (
        summary.get("task_count") != EXPECTED_RECORDS
        or summary.get("completed") != EXPECTED_RECORDS
        or summary.get("success") != EXPECTED_RECORDS
        or summary.get("failed") != 0
    ):
        raise AuditError("batch summary does not establish 204/204 successful scores")
    if len(rows) != EXPECTED_RECORDS:
        raise AuditError("batch task-result row count differs from 204")
    row_ids = [str(row.get("task_id") or "") for row in rows]
    if sorted(row_ids) != list(task_ids) or len(set(row_ids)) != EXPECTED_RECORDS:
        raise AuditError("batch result task set differs")
    if any(row.get("status") != "success" for row in rows):
        raise AuditError("batch results include a failed record")
    restricted_identity = validate_restricted_identity(
        plan.get("restricted_model_identity"), "batch task plan"
    )
    return {
        "task_plan": {"path": "_task_plan.json", "sha256": sha256_file(plan_path)},
        "batch_summary": {
            "path": "_batch_summary.json",
            "sha256": sha256_file(summary_path),
        },
        "task_results": {
            "path": "_task_results.jsonl",
            "sha256": sha256_file(results_path),
        },
        "restricted_model_identity": restricted_identity,
    }


def validate_transfer_manifest(
    blind_root: Path,
    task_ids: Sequence[str],
    records: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, str]]:
    require_regular_tree(blind_root, "blind score output")
    transfer_path = blind_root / "_transfer_manifest.json"
    transfer = load_json(transfer_path, "blind transfer manifest")
    if transfer.get("schema_version") != "neurips_blind_score_transfer_manifest_v1":
        raise AuditError("blind transfer manifest schema differs")
    validate_scoring_config(transfer, "blind transfer manifest")
    if transfer.get("blind_mode") is not True or transfer.get("task_count") != EXPECTED_RECORDS:
        raise AuditError("transfer manifest is not a 204-record blind manifest")
    validate_restricted_identity(
        transfer.get("restricted_model_identity"), "blind transfer manifest"
    )
    isolation = transfer.get("model_stage_isolation")
    if not isinstance(isolation, dict) or (
        isolation.get("invocation_order") != ["stronger", "native"]
        or isolation.get("separate_os_restricted_workspaces") is not True
        or isolation.get("stage_outputs_published_after_all_model_invocations") is not True
        or isolation.get("cross_stage_output_visibility") is not False
    ):
        raise AuditError("transfer manifest does not establish independent model stages")
    handling = transfer.get("released_label_handling")
    if not isinstance(handling, dict) or (
        handling.get("required_by_scorer") is not False
        or handling.get("resolved_before_or_during_scoring") is not False
        or handling.get("comparison_stage") != "external_after_blind_score_lock"
    ):
        raise AuditError("transfer manifest released-label boundary differs")
    local_contract_files = {
        "native": REPO_ROOT
        / "neurips_ed_track_minimal"
        / "prompts"
        / "score_evidence_native_blind.prompt.md",
        "stronger": REPO_ROOT
        / "neurips_ed_track_minimal"
        / "prompts"
        / "score_evidence_stronger_blind.prompt.md",
    }
    transfer_prompts = transfer.get("score_prompts")
    if not isinstance(transfer_prompts, dict):
        raise AuditError("transfer blind prompt bindings are missing")
    for stage, local_path in local_contract_files.items():
        require_regular_file(local_path, f"local frozen {stage} prompt")
        if binding_sha(transfer_prompts.get(stage), f"transfer {stage} prompt") != sha256_file(
            local_path
        ):
            raise AuditError(f"transfer {stage} prompt differs from local frozen scorer")
    local_schema = (
        REPO_ROOT
        / "neurips_ed_track_minimal"
        / "scripts"
        / "blind_evidence_score.schema.json"
    )
    require_regular_file(local_schema, "local frozen blind score schema")
    if binding_sha(transfer.get("score_schema"), "transfer final schema") != sha256_file(
        local_schema
    ):
        raise AuditError("transfer final schema differs from local frozen scorer")
    tasks = transfer.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != EXPECTED_RECORDS:
        raise AuditError("transfer task denominator differs")
    transfer_task_ids: list[str] = []
    for task in tasks:
        if not isinstance(task, dict):
            raise AuditError("transfer task is not an object")
        task_id = str(task.get("task_id") or "")
        transfer_task_ids.append(task_id)
        if task.get("blind_mode") is not True:
            raise AuditError(f"transfer task is not blind: {task_id}")
        if task.get("released_label_required") is not False or task.get("released_label_resolved") is not False:
            raise AuditError(f"transfer task touched released label: {task_id}")
        if any(key in task for key in ("native_label", "native_label_sha256")):
            raise AuditError(f"transfer task has native-label fields: {task_id}")
        record = records.get(task_id)
        if record is None:
            raise AuditError(f"unregistered transfer task: {task_id}")
        if task.get("case_unit_id") != record.get("case_unit_id"):
            raise AuditError(f"transfer case identity differs: {task_id}")
        if task.get("checklist") != f"{task_id}/checklist.yaml" or task.get(
            "evidence"
        ) != f"{task_id}/evidence":
            raise AuditError(f"transfer task paths differ: {task_id}")
        if task.get("checklist_sha256") != record.get("checklist_sha256"):
            raise AuditError(f"transfer checklist SHA-256 differs: {task_id}")
    if sorted(transfer_task_ids) != list(task_ids):
        raise AuditError("transfer task set differs")

    outputs = transfer.get("outputs")
    if not isinstance(outputs, list):
        raise AuditError("transfer output inventory is missing")
    inventory: dict[str, str] = {}
    for entry in outputs:
        if not isinstance(entry, dict):
            raise AuditError("transfer output entry is not an object")
        relative = safe_relative(entry.get("path"), "transfer output path")
        if relative in inventory:
            raise AuditError(f"duplicate transfer output path: {relative}")
        expected_sha = require_sha(entry.get("sha256"), f"transfer output {relative}")
        actual_path = blind_root / relative
        require_regular_file(actual_path, "transferred blind output")
        if sha256_file(actual_path) != expected_sha:
            raise AuditError(f"transferred blind output SHA-256 differs: {relative}")
        inventory[relative] = expected_sha
    actual_files = {
        path.relative_to(blind_root).as_posix()
        for path in blind_root.rglob("*")
        if path.is_file() and path != transfer_path
    }
    if actual_files != set(inventory):
        missing = sorted(set(inventory) - actual_files)
        extra = sorted(actual_files - set(inventory))
        raise AuditError(f"transfer output inventory differs; missing={missing}, extra={extra}")
    return transfer, inventory


def parse_structured_location(payload: Any, location: str) -> Any:
    raw = location[1:] if location.startswith("$") else location
    if raw.startswith("."):
        raw = raw[1:]
    if not raw:
        return payload
    tokens: list[str | int] = []
    cursor = 0
    for match in STRUCTURED_TOKEN_RE.finditer(raw):
        if match.start() != cursor and raw[cursor : match.start()] != ".":
            raise AuditError(f"unsupported structured pointer syntax: {location}")
        tokens.append(match.group(1) if match.group(1) is not None else int(match.group(2)))
        cursor = match.end()
        if cursor < len(raw) and raw[cursor] == ".":
            cursor += 1
    if cursor != len(raw):
        raise AuditError(f"unsupported structured pointer syntax: {location}")
    current = payload
    for token in tokens:
        if isinstance(token, int):
            if not isinstance(current, list) or token >= len(current):
                raise AuditError(f"structured pointer index is unresolved: {location}")
            current = current[token]
        else:
            if not isinstance(current, dict) or token not in current:
                raise AuditError(f"structured pointer key is unresolved: {location}")
            current = current[token]
    return current


def validate_line_span(path: Path, location: str) -> None:
    match = LINE_SPAN_RE.fullmatch(location)
    if match is None:
        raise AuditError(f"invalid line-span pointer: {location}")
    groups = match.groupdict()
    start = int(next(groups[key] for key in ("ls", "ws", "ss", "ns") if groups[key]))
    end_value = next(
        (groups[key] for key in ("le", "we", "se", "ne") if groups[key]), None
    )
    end = int(end_value or start)
    line_count = sum(1 for _ in path.open("r", encoding="utf-8", errors="replace"))
    if start < 1 or end < start or end > line_count:
        raise AuditError(
            f"line-span pointer is out of bounds: {path.name}::{location} (lines={line_count})"
        )


def validate_symbol(path: Path, location: str) -> None:
    if not SYMBOL_RE.fullmatch(location):
        raise AuditError(f"invalid source-symbol pointer: {location}")
    symbol = location.split(".")[-1]
    text = path.read_text(encoding="utf-8", errors="replace")
    pattern = re.compile(
        rf"(?:^|\n)\s*(?:async\s+def|def|class)\s+{re.escape(symbol)}\b|\b{re.escape(symbol)}\b"
    )
    if not pattern.search(text):
        raise AuditError(f"source-symbol pointer is unresolved: {path}::{location}")


def validate_pointer(task_dir: Path, pointer: Any, label: str) -> str:
    if not isinstance(pointer, str):
        raise AuditError(f"{label} pointer is not a string")
    relative, separator, location = pointer.strip().replace("\\", "/").partition("::")
    if separator != "::" or not relative or not location:
        raise AuditError(f"{label} has an invalid pointer: {pointer!r}")
    if relative != "checklist.yaml" and not relative.startswith("evidence/"):
        raise AuditError(f"{label} pointer escaped scorer inputs: {pointer}")
    relative = safe_relative(relative, f"{label} pointer path")
    parts = PurePosixPath(relative).parts
    if parts[-1].lower() in FORBIDDEN_POINTER_BASENAMES or any(
        part.lower() in FORBIDDEN_POINTER_PARTS for part in parts
    ):
        raise AuditError(f"{label} points to a forbidden result/helper artifact: {pointer}")
    path = task_dir / relative
    require_regular_file(path, f"{label} pointer target")
    if LINE_SPAN_RE.fullmatch(location):
        validate_line_span(path, location)
    elif path.suffix.lower() in {".json", ".yaml", ".yml"}:
        payload: Any
        if path.suffix.lower() == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
        else:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        parse_structured_location(payload, location)
    elif path.suffix.lower() == ".py":
        validate_symbol(path, location)
    else:
        raise AuditError(
            f"{label} must use a real line span for non-structured evidence: {pointer}"
        )
    return relative


def all_score_pointers(score: Mapping[str, Any]) -> Iterable[tuple[str, Any]]:
    native = score.get("native")
    stronger = score.get("stronger")
    if not isinstance(native, dict) or not isinstance(stronger, dict):
        raise AuditError("blind score native/stronger object is missing")
    for pointer in native.get("pointers", []):
        yield "native.pointers", pointer
    for index, check in enumerate(native.get("test_checks", [])):
        if isinstance(check, dict):
            for pointer in check.get("pointers", []):
                yield f"native.test_checks[{index}].pointers", pointer
    for pointer in stronger.get("pointers", []):
        yield "stronger.pointers", pointer
    for index, check in enumerate(stronger.get("condition_checks", [])):
        if isinstance(check, dict):
            for pointer in check.get("pointers", []):
                yield f"stronger.condition_checks[{index}].pointers", pointer


def assert_no_forbidden_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in FORBIDDEN_BLIND_KEYS:
                raise AuditError(f"blind score contains forbidden key {path}.{key}")
            assert_no_forbidden_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_no_forbidden_keys(child, f"{path}[{index}]")


def registered_test_ids(checklist: Mapping[str, Any]) -> list[str]:
    native = checklist.get("native")
    success = native.get("success_if") if isinstance(native, dict) else None
    failure = native.get("fail_if") if isinstance(native, dict) else None
    if not isinstance(success, list) or not isinstance(failure, list):
        raise AuditError("checklist native test rules are missing")
    success_ids: list[str] = []
    failure_ids: list[str] = []
    for rules, output in ((success, success_ids), (failure, failure_ids)):
        for rule in rules:
            matches = TEST_MARKER_RE.findall(str(rule.get("text") if isinstance(rule, dict) else ""))
            if len(matches) != 1:
                raise AuditError("checklist native rule does not contain exactly one test id")
            output.append(matches[0])
    if success_ids != failure_ids or len(set(success_ids)) != len(success_ids):
        raise AuditError("checklist native success/failure test ids differ")
    return success_ids


def validate_checks(
    *,
    checks: Any,
    expected_ids: Sequence[str],
    task_dir: Path,
    kind: str,
) -> None:
    if not isinstance(checks, list) or [
        str(check.get("id") or "") for check in checks if isinstance(check, dict)
    ] != list(expected_ids):
        raise AuditError(f"{kind} check ids/order differ from the frozen checklist")
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            raise AuditError(f"{kind} check {index} is not an object")
        status = check.get("status")
        if status not in {"supported", "contradicted", "undecided"}:
            raise AuditError(f"{kind} check {index} has invalid status")
        if not str(check.get("reason") or "").strip():
            raise AuditError(f"{kind} check {index} has no reason")
        pointers = check.get("pointers")
        if not isinstance(pointers, list) or not pointers:
            raise AuditError(f"{kind} check {index} has no pointers")
        resolved = [validate_pointer(task_dir, value, f"{kind} check {index}") for value in pointers]
        if "checklist.yaml" not in resolved or not any(path.startswith("evidence/") for path in resolved):
            raise AuditError(f"{kind} check {index} lacks checklist or decisive evidence pointer")
        if not any(path.startswith("evidence/run/") for path in resolved):
            raise AuditError(
                f"{kind} check {index} lacks post-run execution evidence under evidence/run/"
            )
        if kind == "native":
            wanted = (
                f"checklist.yaml::native.success_if[{index}]"
                if status == "supported"
                else f"checklist.yaml::native.fail_if[{index}]"
                if status == "contradicted"
                else "checklist.yaml::native.undecided_if["
            )
            normalized = []
            for value in pointers:
                item = str(value).replace("\\", "/").lstrip("./")
                if item.startswith("checklist.yaml::$."):
                    item = "checklist.yaml::" + item.removeprefix("checklist.yaml::$.")
                elif item.startswith("checklist.yaml::$["):
                    item = "checklist.yaml::[" + item.removeprefix("checklist.yaml::$[")
                normalized.append(item)
            if status == "undecided":
                if not any(value.startswith(wanted) for value in normalized):
                    raise AuditError(f"native check {index} lacks its verdict-matching rule")
            elif wanted not in normalized:
                raise AuditError(f"native check {index} lacks its verdict-matching rule")
        else:
            wanted = f"checklist.yaml::stronger.additional_conditions[{index}]"
            normalized = []
            for value in pointers:
                item = str(value).replace("\\", "/").lstrip("./")
                if item.startswith("checklist.yaml::$."):
                    item = "checklist.yaml::" + item.removeprefix("checklist.yaml::$.")
                elif item.startswith("checklist.yaml::$["):
                    item = "checklist.yaml::[" + item.removeprefix("checklist.yaml::$[")
                normalized.append(item)
            if wanted not in normalized:
                raise AuditError(f"stronger check {index} lacks its exact frozen condition pointer")


def aggregate(statuses: Sequence[str], *, no_items: str) -> str:
    if not statuses:
        return no_items
    if "contradicted" in statuses:
        return "F"
    if all(status == "supported" for status in statuses):
        return "S"
    return "U"


def validate_stage_lock(
    *,
    task_dir: Path,
    stage: str,
    expected_score: Path,
    expected_stage_payload: Mapping[str, Any],
    checklist_path: Path,
    evidence_sha: str,
    transfer: Mapping[str, Any],
) -> None:
    lock_path = task_dir / f"score.{stage}.lock.json"
    lock = load_json(lock_path, f"{stage} stage lock")
    if (
        lock.get("schema_version") != "blind_score_stage_lock_v1"
        or lock.get("stage") != stage
        or lock.get("outcome_blind") is not True
        or lock.get("released_evaluator_label_resolved") is not False
        or lock.get("component_evaluator_outputs_allowed") is not False
    ):
        raise AuditError(f"{stage} stage lock violates blind contract")
    binding_matches_file(lock.get("stage_score"), expected_score, f"{stage} stage score")
    binding_matches_file(lock.get("checklist"), checklist_path, f"{stage} checklist")
    evidence = lock.get("evidence")
    if not isinstance(evidence, dict) or evidence.get("tree_sha256") != evidence_sha:
        raise AuditError(f"{stage} stage evidence SHA-256 differs")
    if lock.get("auth_mode") != EXPECTED_AUTH_MODE:
        raise AuditError(f"{stage} stage lock does not establish Codex-login auth")
    restricted_user = str(lock.get("restricted_os_user") or "")
    if (
        not restricted_user
        or restricted_user in {"root", "draftsvc"}
        or not isinstance(lock.get("restricted_uid"), int)
        or lock.get("restricted_uid") == 0
        or not isinstance(lock.get("restricted_gid"), int)
    ):
        raise AuditError(f"{stage} stage lock does not establish a restricted OS identity")
    validate_scoring_config(
        {
            **lock,
            "auth_mode": transfer.get("auth_mode"),
            "max_parallel": transfer.get("max_parallel"),
            "sandbox": transfer.get("sandbox"),
        },
        f"{stage} stage lock",
    )
    prompt = transfer.get("score_prompts", {}).get(stage)
    if binding_sha(lock.get("prompt"), f"{stage} prompt") != binding_sha(
        prompt, f"transfer {stage} prompt"
    ):
        raise AuditError(f"{stage} prompt hash differs from transfer lock")
    stage_schema = task_dir / f"score.{stage}.output_schema.json"
    binding_matches_file(lock.get("model_output_schema"), stage_schema, f"{stage} model schema")
    payload = load_json(expected_score, f"{stage} stage score")
    if payload != dict(expected_stage_payload):
        raise AuditError(f"{stage} stage score differs from final blind score")


def validate_record_score(
    *,
    task_id: str,
    task_dir: Path,
    input_task_dir: Path,
    record: Mapping[str, Any],
    transfer: Mapping[str, Any],
    expected_evidence_sha: str,
) -> tuple[dict[str, Any], int, int]:
    score_path = task_dir / "score.json"
    yaml_path = task_dir / "score.yaml"
    manifest_path = task_dir / "score_manifest.json"
    blind_lock_path = task_dir / "score.blind_lock.json"
    score = load_json(score_path, "blind score")
    final_schema_path = (
        REPO_ROOT
        / "neurips_ed_track_minimal"
        / "scripts"
        / "blind_evidence_score.schema.json"
    )
    final_schema = load_json(final_schema_path, "local blind score schema")
    schema_errors = sorted(
        Draft202012Validator(final_schema).iter_errors(score),
        key=lambda error: list(error.absolute_path),
    )
    if schema_errors:
        first = schema_errors[0]
        location = ".".join(str(value) for value in first.absolute_path) or "$"
        raise AuditError(
            f"blind score schema validation failed at {task_id}/{location}: {first.message}"
        )
    if score.get("schema_version") != "blind_evidence_score_v1" or score.get("blind_mode") is not True:
        raise AuditError(f"score is not blind_evidence_score_v1: {task_id}")
    if score.get("case_unit_id") != record.get("case_unit_id"):
        raise AuditError(f"score case id differs: {task_id}")
    assert_no_forbidden_keys(score)
    yaml_score = load_yaml(yaml_path, "blind score YAML")
    if yaml_score != score:
        raise AuditError(f"blind score JSON/YAML differ: {task_id}")
    checklist = load_yaml(input_task_dir / "checklist.yaml", "frozen checklist")
    if (
        checklist.get("case_unit_id") != record.get("case_unit_id")
        or checklist.get("task_id") != record.get("case_unit_id")
        or str(checklist.get("domain") or "").lower() != "appworld"
    ):
        raise AuditError(f"frozen checklist identity differs: {task_id}")
    test_ids = registered_test_ids(checklist)
    stronger = checklist.get("stronger")
    conditions = stronger.get("additional_conditions") if isinstance(stronger, dict) else None
    if not isinstance(conditions, list):
        raise AuditError(f"checklist stronger conditions are missing: {task_id}")
    condition_ids = [str(value.get("id") or "") for value in conditions if isinstance(value, dict)]
    if len(condition_ids) != len(conditions) or len(set(condition_ids)) != len(condition_ids):
        raise AuditError(f"checklist stronger ids are invalid: {task_id}")
    native = score.get("native")
    stronger_score = score.get("stronger")
    if not isinstance(native, dict) or not isinstance(stronger_score, dict):
        raise AuditError(f"score native/stronger shape differs: {task_id}")
    for name, value, allowed in (
        ("native", native, {"S", "F", "U"}),
        ("stronger", stronger_score, {"NA", "S", "F", "U"}),
    ):
        if value.get("verdict") not in allowed or not str(value.get("reason") or "").strip():
            raise AuditError(f"score {name} verdict/reason differs: {task_id}")
        if not isinstance(value.get("pointers"), list) or not value["pointers"]:
            raise AuditError(f"score {name} aggregate pointers are empty: {task_id}")
    validate_checks(
        checks=native.get("test_checks"),
        expected_ids=test_ids,
        task_dir=input_task_dir,
        kind="native",
    )
    validate_checks(
        checks=stronger_score.get("condition_checks"),
        expected_ids=condition_ids,
        task_dir=input_task_dir,
        kind="stronger",
    )
    native_statuses = [str(check["status"]) for check in native["test_checks"]]
    stronger_statuses = [str(check["status"]) for check in stronger_score["condition_checks"]]
    if native.get("verdict") != aggregate(native_statuses, no_items="U"):
        raise AuditError(f"native aggregate is not derived from test checks: {task_id}")
    if stronger_score.get("verdict") != aggregate(stronger_statuses, no_items="NA"):
        raise AuditError(f"stronger aggregate is not independently derived: {task_id}")
    for label, pointer in all_score_pointers(score):
        validate_pointer(input_task_dir, pointer, f"{task_id} {label}")

    lock = load_json(blind_lock_path, "final blind score lock")
    if (
        lock.get("schema_version") != "blind_score_lock_v1"
        or lock.get("blind_mode") is not True
        or lock.get("released_evaluator_label_resolved") is not False
        or lock.get("case_unit_id") != record.get("case_unit_id")
    ):
        raise AuditError(f"final blind lock differs: {task_id}")
    validate_scoring_config(
        {
            **lock,
            "max_parallel": transfer.get("max_parallel"),
        },
        "final blind lock",
    )
    isolation = lock.get("model_stage_isolation")
    if not isinstance(isolation, dict) or (
        isolation.get("stage_outputs_published_after_all_model_invocations") is not True
        or isolation.get("cross_stage_output_visibility") is not False
    ):
        raise AuditError(f"final blind lock does not establish stage isolation: {task_id}")
    binding_matches_file(lock.get("score"), score_path, "final blind score")
    binding_matches_file(lock.get("score_yaml"), yaml_path, "final blind score YAML")
    binding_matches_file(lock.get("checklist"), input_task_dir / "checklist.yaml", "final checklist")
    if lock.get("evidence_tree_sha256") != expected_evidence_sha:
        raise AuditError(f"final evidence tree SHA-256 differs: {task_id}")
    final_schema = transfer.get("score_schema")
    if binding_sha(lock.get("final_schema"), "final score schema") != binding_sha(
        final_schema, "transfer final score schema"
    ):
        raise AuditError(f"final schema SHA-256 differs: {task_id}")
    binding_matches_file(
        lock.get("native_stage_lock"), task_dir / "score.native.lock.json", "native stage lock"
    )
    binding_matches_file(
        lock.get("stronger_stage_lock"), task_dir / "score.stronger.lock.json", "stronger stage lock"
    )
    validate_stage_lock(
        task_dir=task_dir,
        stage="native",
        expected_score=task_dir / "score.native.blind.json",
        expected_stage_payload={"native": native},
        checklist_path=input_task_dir / "checklist.yaml",
        evidence_sha=expected_evidence_sha,
        transfer=transfer,
    )
    validate_stage_lock(
        task_dir=task_dir,
        stage="stronger",
        expected_score=task_dir / "score.stronger.blind.json",
        expected_stage_payload={"stronger": stronger_score},
        checklist_path=input_task_dir / "checklist.yaml",
        evidence_sha=expected_evidence_sha,
        transfer=transfer,
    )
    manifest = load_json(manifest_path, "blind score manifest")
    if (
        manifest.get("schema_version") != "blind_score_manifest_v1"
        or manifest.get("blind_mode") is not True
        or manifest.get("case_unit_id") != record.get("case_unit_id")
        or manifest.get("score_task_id") != task_id
        or manifest.get("agent_id") != record.get("agent_id")
        or manifest.get("task_id") != checklist.get("task_id")
    ):
        raise AuditError(f"blind score manifest differs: {task_id}")
    validate_scoring_config(
        {
            **manifest,
            "auth_mode": transfer.get("auth_mode"),
            "max_parallel": transfer.get("max_parallel"),
            "sandbox": transfer.get("sandbox"),
        },
        "blind score manifest",
    )
    handling = manifest.get("released_label_handling")
    if not isinstance(handling, dict) or any(
        handling.get(key) is not False
        for key in (
            "required_by_scorer",
            "resolved_before_or_during_scoring",
            "included_in_model_workspaces",
            "included_in_score",
        )
    ):
        raise AuditError(f"blind score manifest label handling differs: {task_id}")
    auth = manifest.get("auth")
    if not isinstance(auth, dict) or (
        auth.get("mode") != EXPECTED_AUTH_MODE
        or auth.get("isolated_codex_home") is not True
        or auth.get("auth_json_present") is not True
        or auth.get("api_credential_environment_present") is not False
        or auth.get("batch_login_marker_verified") is not True
        or not str(auth.get("restricted_os_user") or "")
        or auth.get("restricted_os_user") in {"root", "draftsvc"}
        or not isinstance(auth.get("restricted_uid"), int)
        or auth.get("restricted_uid") == 0
        or not isinstance(auth.get("restricted_gid"), int)
        or not isinstance(auth.get("forbidden_root_canary_count"), int)
        or auth.get("forbidden_root_canary_count") < 1
        or auth.get("forbidden_root_canary_passed") is not True
    ):
        raise AuditError(f"blind score manifest does not establish Codex-login auth: {task_id}")
    transfer_identity = validate_restricted_identity(
        transfer.get("restricted_model_identity"), "blind transfer manifest"
    )
    if (
        auth.get("restricted_os_user") != transfer_identity["username"]
        or auth.get("restricted_uid") != transfer_identity["uid"]
        or auth.get("restricted_group") != transfer_identity["groupname"]
        or auth.get("restricted_gid") != transfer_identity["gid"]
    ):
        raise AuditError(f"record auth receipt differs from transfer identity: {task_id}")
    for stage in ("native", "stronger"):
        stage_lock = load_json(task_dir / f"score.{stage}.lock.json", f"{stage} stage lock")
        if any(
            stage_lock.get(lock_key) != auth.get(auth_key)
            for lock_key, auth_key in (
                ("restricted_os_user", "restricted_os_user"),
                ("restricted_uid", "restricted_uid"),
                ("restricted_gid", "restricted_gid"),
            )
        ):
            raise AuditError(f"{stage} restricted identity differs from auth receipt: {task_id}")
    manifest_isolation = manifest.get("model_stage_isolation")
    if not isinstance(manifest_isolation, dict) or (
        manifest_isolation.get("separate_temporary_workspaces") is not True
        or manifest_isolation.get("temporary_stage_outputs_deleted_before_next_invocation") is not True
        or manifest_isolation.get("final_score_directory_empty_during_model_invocations") is not True
        or manifest_isolation.get("all_stage_artifacts_published_after_all_model_invocations") is not True
        or manifest_isolation.get("stronger_received_native_output") is not False
        or manifest_isolation.get("native_received_stronger_output") is not False
    ):
        raise AuditError(f"blind score manifest does not establish stage isolation: {task_id}")
    binding_matches_file(
        manifest.get("checklist"), input_task_dir / "checklist.yaml", "manifest checklist"
    )
    manifest_evidence = manifest.get("evidence")
    if not isinstance(manifest_evidence, dict) or manifest_evidence.get("tree_sha256") != expected_evidence_sha:
        raise AuditError(f"manifest evidence tree SHA-256 differs: {task_id}")
    prompts = manifest.get("prompts")
    schemas = manifest.get("schemas")
    stages = manifest.get("stages")
    outputs = manifest.get("outputs")
    if not all(isinstance(value, dict) for value in (prompts, schemas, stages, outputs)):
        raise AuditError(f"manifest artifact bindings are malformed: {task_id}")
    for stage in ("native", "stronger"):
        if binding_sha(prompts.get(stage), f"manifest {stage} prompt") != binding_sha(
            transfer.get("score_prompts", {}).get(stage), f"transfer {stage} prompt"
        ):
            raise AuditError(f"manifest {stage} prompt SHA-256 differs: {task_id}")
        stage_value = stages.get(stage)
        if not isinstance(stage_value, dict):
            raise AuditError(f"manifest {stage} stage binding is missing: {task_id}")
        binding_matches_file(
            stage_value.get("score"), task_dir / f"score.{stage}.blind.json", f"manifest {stage} score"
        )
        binding_matches_file(
            stage_value.get("lock"), task_dir / f"score.{stage}.lock.json", f"manifest {stage} lock"
        )
        binding_matches_file(
            schemas.get(f"{stage}_model_output"),
            task_dir / f"score.{stage}.output_schema.json",
            f"manifest {stage} schema",
        )
    if binding_sha(schemas.get("final_blind_score"), "manifest final schema") != binding_sha(
        transfer.get("score_schema"), "transfer final schema"
    ):
        raise AuditError(f"manifest final schema SHA-256 differs: {task_id}")
    binding_matches_file(outputs.get("json"), score_path, "manifest score JSON")
    binding_matches_file(outputs.get("yaml"), yaml_path, "manifest score YAML")
    binding_matches_file(outputs.get("blind_lock"), blind_lock_path, "manifest blind lock")
    return score, len(test_ids), len(condition_ids)


def validate_blind_batch(
    public_root: Path, blind_root: Path, state_root: Path
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, Any]]:
    package, task_ids, records = validate_public_package(public_root)
    state_bindings = validate_batch_state(state_root, task_ids)
    transfer, _ = validate_transfer_manifest(blind_root, task_ids, records)
    if state_bindings["restricted_model_identity"] != validate_restricted_identity(
        transfer.get("restricted_model_identity"), "blind transfer manifest"
    ):
        raise AuditError("batch-plan and transfer restricted identities differ")
    transfer_tasks = {
        str(value["task_id"]): value
        for value in transfer["tasks"]
        if isinstance(value, dict)
    }
    scores: dict[str, dict[str, Any]] = {}
    native_count = 0
    stronger_count = 0
    score_hashes: list[dict[str, str]] = []
    for task_id in task_ids:
        input_task = public_root / "tasks" / task_id
        expected_evidence_sha = tree_sha256(input_task / "evidence")
        if transfer_tasks[task_id].get("evidence_tree_sha256") != expected_evidence_sha:
            raise AuditError(f"transfer evidence tree SHA-256 differs: {task_id}")
        score, native_items, stronger_items = validate_record_score(
            task_id=task_id,
            task_dir=blind_root / task_id,
            input_task_dir=input_task,
            record=records[task_id],
            transfer=transfer,
            expected_evidence_sha=expected_evidence_sha,
        )
        scores[task_id] = score
        native_count += native_items
        stronger_count += stronger_items
        score_hashes.append(
            {
                "task_id": task_id,
                "score_sha256": sha256_file(blind_root / task_id / "score.json"),
                "blind_lock_sha256": sha256_file(
                    blind_root / task_id / "score.blind_lock.json"
                ),
            }
        )
    if native_count != EXPECTED_NATIVE_CHECKS:
        raise AuditError(
            f"native test-check denominator differs: {native_count} != {EXPECTED_NATIVE_CHECKS}"
        )
    if stronger_count != EXPECTED_STRONGER_CHECKS:
        raise AuditError(
            f"stronger condition-check denominator differs: {stronger_count} != {EXPECTED_STRONGER_CHECKS}"
        )
    blind_entries = file_entries(blind_root)
    lock = {
        "schema_version": "appworld68_verified_blind_prescore_join_lock.v1",
        "locked_at": utc_now(),
        "released_labels_read": False,
        "benchmark": "AppWorld",
        "dataset_name": "test_normal",
        "case_count": EXPECTED_CASES,
        "record_count": EXPECTED_RECORDS,
        "native_test_check_count": native_count,
        "stronger_condition_check_count": stronger_count,
        "public_package_manifest": {
            "path": "package_manifest.json",
            "sha256": sha256_file(public_root / "package_manifest.json"),
        },
        "blind_transfer_manifest": {
            "path": "_transfer_manifest.json",
            "sha256": sha256_file(blind_root / "_transfer_manifest.json"),
        },
        "blind_output_file_count": len(blind_entries),
        "blind_output_size_bytes": sum(int(value["size_bytes"]) for value in blind_entries),
        "blind_output_files_sha256": package_entries_sha256(blind_entries),
        "batch_state": state_bindings,
        "scoring_config": {
            "model": EXPECTED_MODEL,
            "reasoning_effort": EXPECTED_REASONING,
            "service_tier": EXPECTED_SERVICE_TIER,
            "fast_mode": False,
            "sandbox": EXPECTED_SANDBOX,
            "max_parallel": EXPECTED_PARALLELISM,
            "auth_mode": EXPECTED_AUTH_MODE,
        },
        "records": score_hashes,
        "records_sha256": sha256_bytes(canonical_json_bytes(score_hashes)),
        "post_lock_rule": (
            "Only after this lock is written may released labels be read. A mismatch "
            "routes a record to review and never establishes benchmark conflict."
        ),
    }
    return lock, scores, records


def locate_retained_record(run_root: Path, case_id: str, agent: str) -> tuple[str, Path]:
    matches: list[tuple[str, Path]] = []
    for vps in ("vps1", "vps2"):
        candidate = run_root / vps / "outputs" / agent / case_id
        if candidate.is_dir() and not candidate.is_symlink():
            matches.append((vps, candidate))
    if len(matches) != 1:
        raise AuditError(
            f"expected one retained record for {case_id}/{agent}, found {len(matches)}"
        )
    return matches[0]


def read_released_labels(
    run_root: Path,
    records: Mapping[str, Mapping[str, Any]],
    public_root: Path,
) -> dict[str, dict[str, Any]]:
    """This is the sole released-result read boundary in the build path."""

    require_regular_tree(run_root, "retained AppWorld run root")
    labels: dict[str, dict[str, Any]] = {}
    for task_id in sorted(records):
        record = records[task_id]
        case_id = str(record["case_unit_id"])
        agent = str(record["agent_id"])
        vps, record_root = locate_retained_record(run_root, case_id, agent)
        if vps != record.get("source_vps"):
            raise AuditError(f"retained record VPS binding differs: {task_id}")
        input_run_root = public_root / "tasks" / task_id / "evidence" / "run"
        for relative in (
            "job.json",
            "source_bundle_entry.json",
            "native_evaluator_input.json",
            "official_runner_config.json",
            "appworld_task_output/version/code.txt",
            "appworld_task_output/version/data.txt",
        ):
            retained_identity_file = record_root / relative
            public_identity_file = input_run_root / relative
            require_regular_file(retained_identity_file, "retained record identity file")
            require_regular_file(public_identity_file, "blind input identity file")
            if sha256_file(retained_identity_file) != sha256_file(public_identity_file):
                raise AuditError(
                    f"released-label source is not the record bound to the blind input: "
                    f"{task_id}/{relative}"
                )
        source_path = record_root / "native_evaluator_output.json"
        source = load_json(source_path, "released AppWorld evaluator output")
        if source.get("schema_version") != "appworld_native_evaluator_output/v1":
            raise AuditError(f"released evaluator schema differs: {task_id}")
        if source.get("task_id") != case_id or source.get("dataset_name") != "test_normal":
            raise AuditError(f"released evaluator identity differs: {task_id}")
        tracker = source.get("tracker")
        if not isinstance(tracker, dict) or type(tracker.get("success")) is not bool:
            raise AuditError(f"released evaluator success flag is missing: {task_id}")
        labels[task_id] = {
            "value": "success" if tracker["success"] else "fail",
            "source_vps": vps,
            "source_relative_path": (
                f"{vps}/outputs/{agent}/{case_id}/native_evaluator_output.json"
            ),
            "source_pointer": "native_evaluator_output.json::tracker.success",
            "source_sha256": sha256_file(source_path),
        }
    if len(labels) != EXPECTED_RECORDS:
        raise AuditError("released-label join denominator differs")
    return labels


def comparison_status(released: str, native: str) -> str:
    expected_native = "S" if released == "success" else "F"
    return "match" if native == expected_native else "mismatch"


def joined_record(
    *, task_id: str, record: Mapping[str, Any], score: Mapping[str, Any], label: Mapping[str, Any], score_sha: str
) -> dict[str, Any]:
    native_verdict = str(score["native"]["verdict"])
    released = str(label["value"])
    status = comparison_status(released, native_verdict)
    return {
        "schema_version": "appworld68_postscore_joined_record.v1",
        "task_id": task_id,
        "case_unit_id": record["case_unit_id"],
        "agent_id": record["agent_id"],
        "blind_score": {
            "source_relative_path": f"{task_id}/score.json",
            "source_sha256": score_sha,
            "native": score["native"],
            "stronger": score["stronger"],
        },
        "released_evaluator_label": dict(label),
        "comparison": {
            "status": status,
            "released_success_maps_to": "S",
            "released_fail_maps_to": "F",
            "native_evidence_verdict": native_verdict,
            "routing_rule": "mismatch enters independent record-level review",
        },
        "benchmark_conflict_review": {
            "status": "not_assessed",
            "automatic_inference_prohibited": True,
            "note": (
                "Neither this comparison nor any stronger result establishes benchmark "
                "conflict; confirmation requires a separate source-pointer-based audit."
            ),
        },
    }


def build_join(
    public_root: Path,
    blind_root: Path,
    state_root: Path,
    run_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    for source, label in (
        (public_root, "public job"),
        (blind_root, "blind output"),
        (state_root, "batch state"),
        (run_root, "retained run"),
    ):
        if output_root == source or output_root in source.parents or source in output_root.parents:
            raise AuditError(f"output root overlaps {label} root")
    if output_root.exists():
        raise AuditError(f"refusing to overwrite joined output: {output_root}")

    # Phase 1: no released-result artifact is opened.
    lock, scores, records = validate_blind_batch(public_root, blind_root, state_root)
    output_root.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{output_root.name}.tmp-", dir=output_root.parent)
    )
    try:
        lock_path = temporary / "blind_validation_lock.json"
        write_json(lock_path, lock)
        lock_sha = sha256_file(lock_path)

        # Phase 2 begins only after the blind score bytes and validation lock exist.
        labels = read_released_labels(run_root, records, public_root)
        joined_files: list[dict[str, str]] = []
        mismatch_items: list[dict[str, Any]] = []
        released_counts = {"success": 0, "fail": 0}
        native_counts = {"S": 0, "F": 0, "U": 0}
        stronger_counts = {"NA": 0, "S": 0, "F": 0, "U": 0}
        for task_id in sorted(records):
            score = scores[task_id]
            label = labels[task_id]
            score_sha = sha256_file(blind_root / task_id / "score.json")
            value = joined_record(
                task_id=task_id,
                record=records[task_id],
                score=score,
                label=label,
                score_sha=score_sha,
            )
            path = temporary / "joined_records" / f"{task_id}.json"
            write_json(path, value)
            joined_files.append(
                {
                    "path": path.relative_to(temporary).as_posix(),
                    "sha256": sha256_file(path),
                }
            )
            released_counts[str(label["value"])] += 1
            native_counts[str(score["native"]["verdict"])] += 1
            stronger_counts[str(score["stronger"]["verdict"])] += 1
            if value["comparison"]["status"] == "mismatch":
                mismatch_items.append(
                    {
                        "task_id": task_id,
                        "case_unit_id": records[task_id]["case_unit_id"],
                        "agent_id": records[task_id]["agent_id"],
                        "released_evaluator_label": label["value"],
                        "native_evidence_verdict": score["native"]["verdict"],
                        "stronger_measurement_verdict": score["stronger"]["verdict"],
                        "joined_record": f"joined_records/{task_id}.json",
                        "review_status": "pending_independent_record_level_review",
                        "benchmark_conflict_status": "not_assessed",
                    }
                )
        mismatch_queue = {
            "schema_version": "appworld68_native_label_mismatch_review_queue.v1",
            "blind_validation_lock_sha256": lock_sha,
            "queue_role": (
                "Routing only. Mismatch is neither necessary nor sufficient for "
                "confirmed benchmark conflict."
            ),
            "item_count": len(mismatch_items),
            "items": mismatch_items,
            "items_sha256": sha256_bytes(canonical_json_bytes(mismatch_items)),
        }
        write_json(temporary / "mismatch_review_queue.json", mismatch_queue)
        manifest = {
            "schema_version": "appworld68_postscore_join_manifest.v1",
            "created_at": utc_now(),
            "blind_validation_lock": {
                "path": "blind_validation_lock.json",
                "sha256": lock_sha,
            },
            "record_count": EXPECTED_RECORDS,
            "joined_records": joined_files,
            "joined_records_sha256": sha256_bytes(canonical_json_bytes(joined_files)),
            "mismatch_review_queue": {
                "path": "mismatch_review_queue.json",
                "sha256": sha256_file(temporary / "mismatch_review_queue.json"),
                "item_count": len(mismatch_items),
            },
            "counts": {
                "released_evaluator_label": released_counts,
                "native_evidence": native_counts,
                "stronger_measurement": stronger_counts,
                "comparison": {
                    "match": EXPECTED_RECORDS - len(mismatch_items),
                    "mismatch": len(mismatch_items),
                },
            },
            "benchmark_conflict": {
                "confirmed_count": None,
                "status": "not_assessed_by_this_join",
                "separate_record_level_audit_required": True,
            },
            "blind_outputs_modified": False,
        }
        write_json(temporary / "join_manifest.json", manifest)
        temporary.replace(output_root)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return validate_join(public_root, blind_root, state_root, run_root, output_root)


def validate_join(
    public_root: Path,
    blind_root: Path,
    state_root: Path,
    run_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    require_regular_tree(output_root, "joined score output")
    # Re-establish the blind gate before reading released labels in check mode.
    expected_lock, scores, records = validate_blind_batch(public_root, blind_root, state_root)
    lock_path = output_root / "blind_validation_lock.json"
    saved_lock = load_json(lock_path, "saved blind validation lock")
    expected_without_time = {key: value for key, value in expected_lock.items() if key != "locked_at"}
    saved_without_time = {key: value for key, value in saved_lock.items() if key != "locked_at"}
    if saved_without_time != expected_without_time or saved_lock.get("released_labels_read") is not False:
        raise AuditError("saved blind validation lock differs from current blind bytes")
    labels = read_released_labels(run_root, records, public_root)
    manifest = load_json(output_root / "join_manifest.json", "post-score join manifest")
    if manifest.get("schema_version") != "appworld68_postscore_join_manifest.v1":
        raise AuditError("join manifest schema differs")
    if manifest.get("record_count") != EXPECTED_RECORDS or manifest.get("blind_outputs_modified") is not False:
        raise AuditError("join manifest denominator or immutability declaration differs")
    conflict = manifest.get("benchmark_conflict")
    if not isinstance(conflict, dict) or (
        conflict.get("confirmed_count") is not None
        or conflict.get("status") != "not_assessed_by_this_join"
        or conflict.get("separate_record_level_audit_required") is not True
    ):
        raise AuditError("join manifest contains an automatic benchmark-conflict judgment")
    lock_binding = manifest.get("blind_validation_lock")
    binding_matches_file(lock_binding, lock_path, "joined blind validation lock")
    files = manifest.get("joined_records")
    if not isinstance(files, list) or len(files) != EXPECTED_RECORDS:
        raise AuditError("joined-record inventory differs from 204")
    if manifest.get("joined_records_sha256") != sha256_bytes(canonical_json_bytes(files)):
        raise AuditError("joined-record aggregate SHA-256 differs")
    seen: set[str] = set()
    mismatch_ids: list[str] = []
    for entry in files:
        if not isinstance(entry, dict):
            raise AuditError("joined-record inventory entry is malformed")
        relative = safe_relative(entry.get("path"), "joined record path")
        path = output_root / relative
        expected_sha = require_sha(entry.get("sha256"), f"joined record {relative}")
        if sha256_file(path) != expected_sha:
            raise AuditError(f"joined record SHA-256 differs: {relative}")
        value = load_json(path, "joined record")
        task_id = str(value.get("task_id") or "")
        if task_id in seen or task_id not in records:
            raise AuditError(f"joined record task identity differs: {task_id}")
        seen.add(task_id)
        expected = joined_record(
            task_id=task_id,
            record=records[task_id],
            score=scores[task_id],
            label=labels[task_id],
            score_sha=sha256_file(blind_root / task_id / "score.json"),
        )
        if value != expected:
            raise AuditError(f"joined record content differs: {task_id}")
        if value["comparison"]["status"] == "mismatch":
            mismatch_ids.append(task_id)
    if seen != set(records):
        raise AuditError("joined record task set differs")
    queue_path = output_root / "mismatch_review_queue.json"
    queue = load_json(queue_path, "mismatch review queue")
    queue_binding = manifest.get("mismatch_review_queue")
    binding_matches_file(queue_binding, queue_path, "mismatch review queue")
    items = queue.get("items")
    if not isinstance(items, list) or queue.get("item_count") != len(items):
        raise AuditError("mismatch queue denominator differs")
    if queue.get("items_sha256") != sha256_bytes(canonical_json_bytes(items)):
        raise AuditError("mismatch queue aggregate SHA-256 differs")
    if [str(item.get("task_id") or "") for item in items if isinstance(item, dict)] != mismatch_ids:
        raise AuditError("mismatch queue task set differs")
    if any(item.get("benchmark_conflict_status") != "not_assessed" for item in items):
        raise AuditError("mismatch queue contains an automatic conflict judgment")
    return {
        "status": "valid",
        "record_count": EXPECTED_RECORDS,
        "native_test_check_count": EXPECTED_NATIVE_CHECKS,
        "stronger_condition_check_count": EXPECTED_STRONGER_CHECKS,
        "mismatch_count": len(items),
        "blind_validation_lock_sha256": sha256_file(lock_path),
        "join_manifest_sha256": sha256_file(output_root / "join_manifest.json"),
    }


def main() -> int:
    args = parse_args()
    public_root = args.public_job_root.resolve()
    blind_root = args.blind_output_root.resolve()
    state_root = args.batch_state_root.resolve()
    run_root = args.retained_run_root.resolve()
    output_root = args.output_root.resolve()
    try:
        result = (
            validate_join(public_root, blind_root, state_root, run_root, output_root)
            if args.check
            else build_join(public_root, blind_root, state_root, run_root, output_root)
        )
    except (AuditError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
