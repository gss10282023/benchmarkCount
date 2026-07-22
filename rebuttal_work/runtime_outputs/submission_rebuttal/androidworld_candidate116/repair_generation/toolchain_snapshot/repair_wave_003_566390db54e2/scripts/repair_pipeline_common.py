#!/usr/bin/env python3
"""Shared fail-closed primitives for candidate116 checklist repair."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping

from semantic_review_common import (
    EXPECTED_CASE_COUNT,
    EXPECTED_PARALLELISM,
    REPO_ROOT,
    WORK_ROOT,
    SemanticReviewError,
    add_self_hash,
    canonical_bytes,
    file_binding,
    load_json,
    load_yaml_mapping,
    object_sha256,
    repo_relative,
    resolve_repo_path,
    sha256_file,
    utc_now,
    verify_file_binding,
    verify_self_hash,
    write_json_atomic,
)


REPAIR_PRELOCK_SCHEMA = "androidworld_checklist_repair_prelock/v1"
REPAIR_CONFIG_SCHEMA = "androidworld_checklist_repair_config/v1"
REPAIR_SELECTION_SCHEMA = "androidworld_checklist_repair_selection/v1"
EFFECTIVE_MANIFEST_SCHEMA = "androidworld_effective_checklist_wave/v1"
PROMOTION_HANDOFF_SCHEMA = "androidworld_repair_aware_promotion_handoff/v1"
REQUIRED_CASE_SIDECARS = (
    "checklist.yaml",
    "checklist.json",
    "api_response.json",
    "llm_call.json",
    "reasoning_summary.txt",
    "stdout.log",
    "stderr.log",
)
ISSUE_FIELDS = (
    "issue_id",
    "severity",
    "source_kind",
    "check",
    "description",
    "required_fix",
)


class RepairPipelineError(SemanticReviewError):
    """Raised when a repair/effective-wave invariant is not proven."""


def safe_id(value: str) -> bool:
    return bool(value) and bool(re.fullmatch(r"[A-Za-z0-9_.-]+", value))


def verify_binding_tree(value: Any, label: str, *, inside_candidate: bool = True) -> None:
    if isinstance(value, Mapping) and {"path", "sha256", "size_bytes"}.issubset(value):
        verify_file_binding(value, label, inside_candidate=inside_candidate)
        return
    if isinstance(value, Mapping):
        for key, nested in value.items():
            verify_binding_tree(nested, f"{label}.{key}", inside_candidate=inside_candidate)
        return
    if isinstance(value, list):
        for index, nested in enumerate(value):
            verify_binding_tree(nested, f"{label}[{index}]", inside_candidate=inside_candidate)
        return
    raise RepairPipelineError(f"{label} is not a file-binding tree")


def packet_rows(prelock: Mapping[str, Any]) -> list[dict[str, Any]]:
    for key in ("packet_inputs", "case_packet_inputs", "compact_packet_inputs"):
        rows = prelock.get(key)
        if isinstance(rows, list):
            result: list[dict[str, Any]] = []
            for raw in rows:
                if not isinstance(raw, Mapping):
                    raise RepairPipelineError(f"{key} contains a non-object")
                row = dict(raw)
                row.setdefault("path", row.get("packet_path") or row.get("case_packet_path"))
                result.append(row)
            return result
    raise RepairPipelineError("draft prelock has no packet input list")


def load_source_prelock(path: Path) -> dict[str, Any]:
    path = path.resolve()
    try:
        path.relative_to(WORK_ROOT.resolve())
    except ValueError as exc:
        raise RepairPipelineError("source draft prelock must be inside candidate116") from exc
    value = load_json(path, "source draft prelock")
    verify_self_hash(value, "prelock_sha256", "source draft prelock")
    if value.get("generation_id") != "wave_003":
        raise RepairPipelineError("repair source generation must be wave_003")
    if value.get("case_count") != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("source prelock is not exactly 116 cases")
    order = list(value.get("case_order") or [])
    if len(order) != EXPECTED_CASE_COUNT or len(set(order)) != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("source prelock case order is invalid")
    if value.get("case_order_sha256") != object_sha256(order):
        raise RepairPipelineError("source prelock case-order hash fails")
    rows = packet_rows(value)
    if len(rows) != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("source prelock does not bind 116 packets")
    return value


def source_wave(prelock: Mapping[str, Any]) -> Path:
    raw = (prelock.get("canonical_output_gate") or {}).get("raw_wave")
    path = resolve_repo_path(raw, inside_candidate=True)
    expected = WORK_ROOT / "draft_generation" / "waves" / "wave_003"
    if path != expected.resolve():
        raise RepairPipelineError("source prelock raw wave is not wave_003")
    return path


def tool_binding(prelock: Mapping[str, Any], *names: str) -> tuple[str, dict[str, Any], Path]:
    tools = prelock.get("tool_bindings")
    if not isinstance(tools, Mapping):
        raise RepairPipelineError("prelock has no tool_bindings")
    normalized = {
        re.sub(r"[^a-z0-9]+", "_", str(key).casefold()).strip("_"): (str(key), value)
        for key, value in tools.items()
    }
    for requested in names:
        key = re.sub(r"[^a-z0-9]+", "_", requested.casefold()).strip("_")
        if key in normalized:
            original, binding = normalized[key]
            if not isinstance(binding, Mapping):
                raise RepairPipelineError(f"tool binding {original} is not an object")
            path = verify_file_binding(binding, f"tool {original}", inside_candidate=True)
            return original, dict(binding), path
    raise RepairPipelineError(f"missing tool binding alternatives {names}")


def case_file_bindings(case_dir: Path) -> dict[str, Any]:
    bindings = {name: file_binding(case_dir / name) for name in REQUIRED_CASE_SIDECARS}
    return bindings


def tree_record(root: Path) -> dict[str, Any]:
    files = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file())
    ]
    return {
        "path": repo_relative(root),
        "file_count": len(files),
        "tree_sha256": object_sha256(files),
        "files": files,
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RepairPipelineError(f"cannot read JSONL {path}: {exc}") from exc
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RepairPipelineError(f"invalid JSONL {path}:{number}: {exc}") from exc
        if not isinstance(value, dict):
            raise RepairPipelineError(f"JSONL row {path}:{number} is not an object")
        rows.append(value)
    return rows


def normalized_issue(raw: Mapping[str, Any], case_id: str, index: int) -> dict[str, str]:
    description = str(raw.get("description") or raw.get("message") or "").strip()
    check = str(raw.get("check") or raw.get("field") or "semantic").strip()
    result = {
        "issue_id": str(raw.get("issue_id") or raw.get("code") or f"issue_{index:03d}").strip(),
        "severity": str(raw.get("severity") or "error").strip().casefold(),
        "source_kind": str(raw.get("source_kind") or "manual_audit").strip(),
        "check": check,
        "description": description,
        "required_fix": str(
            raw.get("required_fix")
            or raw.get("fix")
            or (f"Resolve the bound {check} failure: {description}" if description else "")
        ).strip(),
    }
    if result["severity"] not in {"error", "warning"}:
        raise RepairPipelineError(f"{case_id} issue {result['issue_id']} has invalid severity")
    if any(not result[field] for field in ISSUE_FIELDS):
        raise RepairPipelineError(f"{case_id} issue {index} is incomplete")
    return result


def load_audit_selection(
    path: Path,
    *,
    case_order: list[str],
    automatic_qc_root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    selection = load_json(path.resolve(), "repair selection")
    if selection.get("schema_version") != REPAIR_SELECTION_SCHEMA:
        raise RepairPipelineError("repair selection schema_version is invalid")
    verify_self_hash(selection, "selection_sha256", "repair selection")
    if selection.get("source_generation_id") != "wave_003" or selection.get("case_count") != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("repair selection source/count is invalid")
    rows = list(selection.get("cases") or [])
    if len(rows) != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("repair selection must contain exactly 116 rows")
    normalized_rows: list[dict[str, Any]] = []
    for rank, (case_id, raw) in enumerate(zip(case_order, rows, strict=True)):
        if not isinstance(raw, Mapping):
            raise RepairPipelineError(f"repair selection row {rank} is not an object")
        if raw.get("selection_rank") != rank or raw.get("case_unit_id") != case_id or raw.get("task_id") != case_id:
            raise RepairPipelineError(f"repair selection identity/order mismatch at {case_id}")
        disposition = str(raw.get("disposition") or "")
        if disposition not in {"retain", "repair"}:
            raise RepairPipelineError(f"{case_id} disposition must be retain or repair")
        manual_issues = [
            normalized_issue(issue, case_id, index)
            for index, issue in enumerate(raw.get("issues") or [], 1)
            if isinstance(issue, Mapping)
        ]
        if len(manual_issues) != len(raw.get("issues") or []):
            raise RepairPipelineError(f"{case_id} contains a non-object manual issue")
        source_bindings: list[dict[str, Any]] = []
        for source_index, binding in enumerate(raw.get("audit_sources") or []):
            if not isinstance(binding, Mapping):
                raise RepairPipelineError(f"{case_id} audit source {source_index} is not a binding")
            verify_file_binding(binding, f"{case_id} audit source {source_index}", inside_candidate=True)
            source_bindings.append(dict(binding))
        qc_path = automatic_qc_root / case_id / "qc.json"
        qc = load_json(qc_path, f"{case_id} automatic QC")
        if qc.get("case_unit_id") != case_id or qc.get("task_id") != case_id:
            raise RepairPipelineError(f"{case_id} automatic QC identity differs")
        automatic_issues = [
            normalized_issue(dict(issue) | {"source_kind": "automatic_qc"}, case_id, index)
            for index, issue in enumerate(qc.get("issues") or [], 1)
            if isinstance(issue, Mapping) and issue.get("severity", "error") in {"error", "warning"}
        ]
        all_issues = automatic_issues + manual_issues
        required_disposition = "repair" if all_issues else "retain"
        if disposition != required_disposition:
            raise RepairPipelineError(
                f"{case_id} disposition={disposition}, but bound issues require {required_disposition}"
            )
        if disposition == "repair" and not any(item["severity"] == "error" for item in all_issues):
            raise RepairPipelineError(f"{case_id} repair requires at least one error-severity issue")
        row = {
            "selection_rank": rank,
            "case_unit_id": case_id,
            "task_id": case_id,
            "disposition": disposition,
            "issues": all_issues,
            "automatic_qc": file_binding(qc_path),
            "audit_sources": source_bindings,
        }
        row["audit_case_sha256"] = object_sha256(row)
        normalized_rows.append(row)
    return selection, normalized_rows


def load_repair_prelock(path: Path) -> dict[str, Any]:
    prelock = load_json(path.resolve(), "repair prelock")
    if prelock.get("schema_version") != REPAIR_PRELOCK_SCHEMA:
        raise RepairPipelineError("repair prelock schema is invalid")
    if prelock.get("status") != "frozen_before_first_repair_model_call":
        raise RepairPipelineError("repair prelock status is invalid")
    verify_self_hash(prelock, "prelock_sha256", "repair prelock")
    if prelock.get("case_count") != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("repair prelock does not cover 116 effective cases")
    repair_inputs = list(prelock.get("repair_inputs") or [])
    if prelock.get("repair_count") != len(repair_inputs) or not repair_inputs:
        raise RepairPipelineError("repair prelock repair input count is invalid")
    if prelock.get("repair_inputs_sha256") != object_sha256(repair_inputs):
        raise RepairPipelineError("repair prelock input hash fails")
    for row in repair_inputs:
        verify_binding_tree(row.get("bindings"), f"{row.get('case_unit_id')} repair bindings")
    return prelock


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def verify_case_identity(checklist: Mapping[str, Any], case_id: str) -> None:
    if checklist.get("domain") != "androidworld":
        raise RepairPipelineError(f"{case_id} checklist domain is not androidworld")
    if checklist.get("case_unit_id") != case_id or checklist.get("task_id") != case_id:
        raise RepairPipelineError(f"{case_id} checklist identity differs")


def verify_checklist_pair(case_dir: Path, case_id: str) -> dict[str, Any]:
    yaml_path = case_dir / "checklist.yaml"
    json_path = case_dir / "checklist.json"
    yaml_value = load_yaml_mapping(yaml_path, f"{case_id} checklist YAML")
    json_value = load_json(json_path, f"{case_id} checklist JSON")
    if yaml_value != json_value:
        raise RepairPipelineError(f"{case_id} checklist YAML and JSON differ")
    verify_case_identity(yaml_value, case_id)
    return yaml_value


def verify_source_wave_complete(prelock: Mapping[str, Any]) -> tuple[Path, dict[str, dict[str, Any]]]:
    wave = source_wave(prelock)
    if not wave.is_dir():
        raise RepairPipelineError(f"source wave is missing: {wave}")
    order = list(prelock.get("case_order") or [])
    observed = {path.name for path in wave.iterdir() if path.is_dir() and not path.name.startswith(".")}
    if observed != set(order):
        raise RepairPipelineError(
            f"source wave case set differs: missing={sorted(set(order)-observed)}, "
            f"extra={sorted(observed-set(order))}"
        )
    summary = load_json(wave / "_batch_summary.json", "source batch summary")
    expected = {
        "total_cases": EXPECTED_CASE_COUNT,
        "completed_cases": EXPECTED_CASE_COUNT,
        "success_cases": EXPECTED_CASE_COUNT,
        "skipped_cases": 0,
        "failed_cases": 0,
        "provider": "codex",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "xhigh",
        "codex_sandbox": "read-only",
        "quality_check": "none",
    }
    for field, wanted in expected.items():
        if summary.get(field) != wanted:
            raise RepairPipelineError(
                f"source batch summary {field}={summary.get(field)!r}, expected {wanted!r}"
            )
    records_list = load_jsonl(wave / "_batch_results.jsonl")
    records: dict[str, dict[str, Any]] = {}
    for record in records_list:
        case_id = str(record.get("case_unit_dir") or "")
        if case_id in records or case_id not in set(order):
            raise RepairPipelineError(f"source batch record identity is invalid: {case_id!r}")
        if record.get("status") != "success":
            raise RepairPipelineError(f"source batch case {case_id} is not successful")
        records[case_id] = record
    if set(records) != set(order):
        raise RepairPipelineError("source batch result set is not exactly 116 cases")
    for case_id in order:
        case_dir = wave / case_id
        verify_checklist_pair(case_dir, case_id)
        for name in REQUIRED_CASE_SIDECARS:
            if not (case_dir / name).is_file():
                raise RepairPipelineError(f"{case_id} source wave is missing {name}")
        attempts = list(records[case_id].get("attempts") or [])
        accepted = [
            item for item in attempts
            if isinstance(item, Mapping)
            and item.get("returncode") == 0
            and str(item.get("validator") or "").startswith("checklist valid:")
        ]
        if not accepted:
            raise RepairPipelineError(f"{case_id} has no accepted generation attempt")
    return wave, records


def canonical_diff(before: Any, after: Any, prefix: str = "$") -> list[dict[str, Any]]:
    """Return deterministic JSON-path changes without omitting deleted values."""
    changes: list[dict[str, Any]] = []
    if type(before) is not type(after):
        return [{"path": prefix, "before": before, "after": after, "change": "replace"}]
    if isinstance(before, Mapping):
        keys = sorted(set(before) | set(after))
        for key in keys:
            child = f"{prefix}.{key}"
            if key not in before:
                changes.append({"path": child, "after": after[key], "change": "add"})
            elif key not in after:
                changes.append({"path": child, "before": before[key], "change": "remove"})
            else:
                changes.extend(canonical_diff(before[key], after[key], child))
        return changes
    if isinstance(before, list):
        limit = max(len(before), len(after))
        for index in range(limit):
            child = f"{prefix}[{index}]"
            if index >= len(before):
                changes.append({"path": child, "after": after[index], "change": "add"})
            elif index >= len(after):
                changes.append({"path": child, "before": before[index], "change": "remove"})
            else:
                changes.extend(canonical_diff(before[index], after[index], child))
        return changes
    if before != after:
        changes.append({"path": prefix, "before": before, "after": after, "change": "replace"})
    return changes


def guarded_output_directory(path: Path) -> Path:
    """Create an adjacent staging directory; caller atomically renames it."""
    if path.exists():
        raise RepairPipelineError(f"refusing to overwrite output directory: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f".{path.name}.staging.", dir=path.parent))


def atomic_promote_directory(staging: Path, destination: Path) -> None:
    if destination.exists():
        raise RepairPipelineError(f"refusing to overwrite output directory: {destination}")
    os.replace(staging, destination)


def verify_internal_hash(value: Mapping[str, Any], fields: Iterable[str], label: str) -> str:
    for field in fields:
        if field in value:
            verify_self_hash(value, field, label)
            return field
    raise RepairPipelineError(f"{label} has no accepted self-hash field")


def binding_with_internal_hash(path: Path, field_names: Iterable[str]) -> dict[str, Any]:
    value = load_json(path, path.name)
    field = verify_internal_hash(value, field_names, path.name)
    return file_binding(path) | {field: value[field]}


def generated_record_base(schema_version: str) -> dict[str, Any]:
    return {"schema_version": schema_version, "created_at": utc_now()}
