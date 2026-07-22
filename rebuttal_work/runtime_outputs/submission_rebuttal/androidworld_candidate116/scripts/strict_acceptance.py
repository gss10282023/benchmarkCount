#!/usr/bin/env python3
"""Read-only acceptance gate for the AndroidWorld candidate-116 inputs.

This module deliberately does not create, rewrite, or repair artifacts.  It is
intended to be run after ``build_and_validate.py`` has materialised a candidate
workspace, and it can also be imported by that builder as its final gate.

The accepted artifact contract is intentionally stricter than the repository's
generic JSON schemas.  In particular, it binds the compact LLM-visible packet,
the effective AndroidWorld task semantics, the 348 execution slots, and the
pre-run freeze without trusting a checksum file generated beside those inputs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


EXPECTED_CASE_COUNT = 116
EXPECTED_EXTRA_COUNT = 16
EXPECTED_OFFICIAL_COUNT = 100
EXPECTED_GOAL_CATEGORY_COUNTS = {
    "format_template": 57,
    "computed_goal": 33,
    "branch_template": 1,
    "ir_proto_prompt": 25,
}
EXPECTED_AGENT_IDS = ("agent_a", "agent_b", "agent_c")
EXPECTED_SLOT_COUNTS = {
    "candidate116": 348,
    "official100": 300,
    "extra16": 48,
}
EXPECTED_OFFICIAL100_SELECTOR_SHA256 = (
    "6aa7d2b447742c2333192424941198ca8c8226c29141badfcae09b644a12c320"
)

HASH_RE = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
HOST_ABSOLUTE_PATTERNS = (
    re.compile(rb"/Users/[A-Za-z0-9_.-]+/"),
    re.compile(rb"/home/[A-Za-z0-9_.-]+/"),
    re.compile(rb"[A-Za-z]:\\\\Users\\\\[A-Za-z0-9_.-]+\\\\"),
)
RESULT_FIELD_NAMES = frozenset(
    {
        "agent_identity",
        "agent_trace",
        "trace_with_agent_identity",
        "native_score",
        "native_label",
        "native_pass_fail",
        "native_pass_fail_scalar",
        "native_evaluator_score",
        "native_evaluator_label",
        "native_evaluator_verdict",
        "native_evaluator_pass_fail",
        "native_evaluator_pass_fail_scalar",
        "native_evaluator_pass_fail_label",
        "evaluator_pass_fail",
        "evaluator_pass_fail_scalar",
        "pass_fail_scalar",
        "outcome_label",
        "prior_outcome_verdict",
        "alternate_view_verdict",
        "alternate_view_verdicts",
        "evidence_label",
        "final_evidence_label",
        "unresolve_reason",
        "counting_decision",
        "scored_record",
        "scored_records",
        "scored_label",
        "scored_verdict",
        "scored_value",
        "scored_values",
        "paper_output",
        "paper_outputs",
        "paper_output_value",
        "paper_output_values",
        "final_verdict",
        "judge_only_label",
        "judge_only_labels",
        "adapter_summary_verdict",
        "runner_summary_verdict",
    }
)
RESULT_TEXT_TOKENS = tuple(
    token.encode("utf-8")
    for token in sorted(
        {
            "native_score",
            "outcome_label",
            "evidence_label",
            "final_evidence_label",
            "unresolve_reason",
            "scored_record",
            "paper_output_value",
            "native_pass_fail_scalar",
        }
    )
)


class AcceptanceFailure(RuntimeError):
    """Raised when one or more strict acceptance checks fail."""

    def __init__(self, issues: Sequence[str]):
        self.issues = tuple(issues)
        super().__init__("strict acceptance failed: " + "; ".join(self.issues[:8]))


def _canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _sha256_object(payload: Any) -> str:
    return _sha256_bytes(_canonical_json_bytes(payload))


def _as_mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _first(mapping: Mapping[str, Any], names: Iterable[str]) -> Any:
    for name in names:
        if name in mapping:
            return mapping[name]
    return None


def _case_id(record: Mapping[str, Any]) -> str:
    return str(record.get("case_unit_id") or record.get("task_id") or record.get("task_name") or "")


def _normal_agent_id(value: Any) -> str:
    text = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {"a": "agent_a", "b": "agent_b", "c": "agent_c"}
    return aliases.get(text, text)


@dataclass(frozen=True)
class AcceptancePaths:
    repo_root: Path
    work_root: Path
    semantic_index: Path
    source_bundle: Path
    candidate_manifest: Path
    extra16_manifest: Path
    slot_manifest: Path
    draft_input_freeze: Path
    old_snapshot_before: Path
    old_snapshot_after: Path
    official100_selector: Path
    conflict_ledger: Path | None = None
    extra16_source_bundle: Path | None = None
    agents_config: Path | None = None


class StrictAcceptance:
    """Accumulates independent, read-only acceptance checks."""

    def __init__(self, paths: AcceptancePaths, *, max_compact_bytes: int = 180_000):
        self.paths = paths
        self.max_compact_bytes = max_compact_bytes
        self.issues: list[str] = []
        self.checks: dict[str, Any] = {}
        self.semantic_payload: Mapping[str, Any] = {}
        self.semantic_records: list[Mapping[str, Any]] = []
        self.semantic_by_id: dict[str, Mapping[str, Any]] = {}
        self.bundle: Mapping[str, Any] = {}
        self.bundle_sources: list[Mapping[str, Any]] = []
        self.freeze: Mapping[str, Any] = {}
        self.freeze_by_id: dict[str, Mapping[str, Any]] = {}
        self.slot_payload: Mapping[str, Any] = {}
        self.slot_records: list[Mapping[str, Any]] = []
        self.prompt_hashes: dict[str, str] = {}

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.issues.append(message)

    def load_json(self, path: Path, label: str) -> Mapping[str, Any]:
        if not path.is_file():
            self.issues.append(f"{label} is missing: {path}")
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            self.issues.append(f"{label} is not readable JSON: {path}: {exc}")
            return {}
        if not isinstance(payload, Mapping):
            self.issues.append(f"{label} must be a JSON object: {path}")
            return {}
        return payload

    def resolve_declared_path(self, value: Any, label: str) -> Path | None:
        text = str(value or "")
        if not text:
            self.issues.append(f"{label} path is missing")
            return None
        posix = PurePosixPath(text.replace("\\", "/"))
        if posix.is_absolute() or ".." in posix.parts or text.startswith("./"):
            self.issues.append(f"{label} is not a safe relative path: {text!r}")
            return None
        repo_candidate = (self.paths.repo_root / posix).resolve()
        work_candidate = (self.paths.work_root / posix).resolve()
        matches = [path for path in (repo_candidate, work_candidate) if path.exists()]
        unique = list(dict.fromkeys(matches))
        if len(unique) > 1:
            self.issues.append(f"{label} is ambiguous between repo/work roots: {text!r}")
            return None
        resolved = unique[0] if unique else repo_candidate
        try:
            resolved.relative_to(self.paths.repo_root)
        except ValueError:
            self.issues.append(f"{label} escapes the repository: {text!r}")
            return None
        return resolved

    def run(self) -> dict[str, Any]:
        self._load_primary_inputs()
        self._validate_semantic_records()
        self._validate_metadata_conflicts()
        self._validate_effective_sources()
        self._validate_markor_edit_note()
        self._validate_ir_proto_bindings()
        self._validate_source_bundle_and_prompts()
        self._validate_slots()
        self._validate_manifests_and_freeze()
        self._validate_old_root_snapshots()
        self._validate_official100()
        self._scan_forbidden_inputs_and_paths()
        report = {
            "schema_version": "androidworld_candidate116_strict_acceptance/v1",
            "status": "fail" if self.issues else "pass",
            "case_count": len(self.semantic_records),
            "prompt_hash_count": len(self.prompt_hashes),
            "slot_count": len(self.slot_records),
            "checks": self.checks,
            "issues": self.issues,
        }
        if self.issues:
            raise AcceptanceFailure(self.issues)
        return report

    def _load_primary_inputs(self) -> None:
        self.semantic_payload = self.load_json(self.paths.semantic_index, "semantic index")
        raw_records = _first(self.semantic_payload, ("records", "items", "cases"))
        self.semantic_records = [row for row in _as_list(raw_records) if isinstance(row, Mapping)]
        for record in self.semantic_records:
            case_id = _case_id(record)
            if case_id and case_id not in self.semantic_by_id:
                self.semantic_by_id[case_id] = record

        self.bundle = self.load_json(self.paths.source_bundle, "candidate116 compact source bundle")
        self.bundle_sources = [row for row in _as_list(self.bundle.get("sources")) if isinstance(row, Mapping)]

        self.freeze = self.load_json(self.paths.draft_input_freeze, "draft-input freeze")
        raw_freeze_records = _first(self.freeze, ("records", "items", "cases", "draft_inputs"))
        if isinstance(raw_freeze_records, Mapping):
            freeze_rows = [dict(value, case_unit_id=key) if isinstance(value, Mapping) else {} for key, value in raw_freeze_records.items()]
        else:
            freeze_rows = [row for row in _as_list(raw_freeze_records) if isinstance(row, Mapping)]
        for record in freeze_rows:
            case_id = _case_id(record)
            if case_id and case_id not in self.freeze_by_id:
                self.freeze_by_id[case_id] = record

        self.slot_payload = self._load_slot_manifest(self.paths.slot_manifest)
        raw_slots = _first(self.slot_payload, ("slots", "records", "items"))
        self.slot_records = [row for row in _as_list(raw_slots) if isinstance(row, Mapping)]

    def _load_slot_manifest(self, path: Path) -> Mapping[str, Any]:
        if path.suffix.lower() != ".csv":
            return self.load_json(path, "348-slot manifest")
        if not path.is_file():
            self.issues.append(f"348-slot manifest is missing: {path}")
            return {}
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        companion = path.with_name(path.stem + "_hashes.json")
        hashes = self.load_json(companion, "slot-hash companion")
        return {"slots": rows, "slot_sets": hashes.get("slot_sets") or hashes}

    def _validate_semantic_records(self) -> None:
        self.require(len(self.semantic_records) == EXPECTED_CASE_COUNT, "semantic index must contain exactly 116 records")
        ids = [_case_id(row) for row in self.semantic_records]
        self.require(all(SAFE_ID_RE.fullmatch(case_id or "") for case_id in ids), "semantic records contain an empty or unsafe case id")
        self.require(len(set(ids)) == EXPECTED_CASE_COUNT, "semantic record case ids must be 116 unique values")
        ranks = [row.get("selection_rank") for row in self.semantic_records]
        try:
            rank_values = [int(value) for value in ranks]
        except (TypeError, ValueError):
            rank_values = []
        self.require(sorted(rank_values) == list(range(EXPECTED_CASE_COUNT)), "semantic selection ranks must be exactly 0..115")

        kinds: list[str] = []
        for record in self.semantic_records:
            goal = _as_mapping(record.get("goal")) or {}
            kinds.append(str(goal.get("representation_kind") or ""))
        actual = dict(sorted(Counter(kinds).items()))
        declared_expected = self.semantic_payload.get("expected_category_counts")
        declared_actual = self.semantic_payload.get("category_counts")
        self.require(declared_expected == EXPECTED_GOAL_CATEGORY_COUNTS, f"expected_category_counts must equal {EXPECTED_GOAL_CATEGORY_COUNTS}")
        self.require(declared_actual == EXPECTED_GOAL_CATEGORY_COUNTS, f"category_counts must equal {EXPECTED_GOAL_CATEGORY_COUNTS}")
        self.require(actual == EXPECTED_GOAL_CATEGORY_COUNTS, f"goal representation counts are wrong: {actual}")
        self.checks["goal_category_counts"] = actual

        for record in self.semantic_records:
            self._reject_canonical_abc(record, f"semantics[{_case_id(record)}]")
        self.checks["canonical_abc_provenance_absent"] = not any("abc provenance" in issue for issue in self.issues)

    def _reject_canonical_abc(
        self,
        value: Any,
        base: str,
        key: str = "",
        diagnostic_context: bool = False,
    ) -> None:
        diagnostic = diagnostic_context or key.startswith("runtime_reported_") or key.startswith("diagnostic_") or key in {
            "observed_module",
            "observed_source_file",
            "runtime_observation",
            "observed_provenance",
        }
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                self._reject_canonical_abc(
                    child,
                    f"{base}.{child_key}",
                    str(child_key),
                    diagnostic,
                )
        elif isinstance(value, list):
            for index, child in enumerate(value):
                self._reject_canonical_abc(
                    child,
                    f"{base}[{index}]",
                    key,
                    diagnostic,
                )
        elif not diagnostic and isinstance(value, str):
            canonical_key = key in {
                "module",
                "source_module",
                "definition_module",
                "canonical_module",
                "source_file",
                "source_path",
                "definition_source_file",
                "canonical_source_file",
                "artifact_path",
            }
            if canonical_key and (value == "abc" or PurePosixPath(value.replace("\\", "/")).name == "abc.py"):
                self.issues.append(f"canonical abc provenance is forbidden at {base}: {value!r}")

    def _combined_conflicts(self, record: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        conflicts = [row for row in _as_list(_first(record, ("metadata_conflicts", "conflicts"))) if isinstance(row, Mapping)]
        if self.paths.conflict_ledger is not None:
            ledger = self.load_json(self.paths.conflict_ledger, "metadata-conflict ledger")
            raw = _first(ledger, ("records", "items", "conflicts"))
            if isinstance(raw, Mapping):
                entry = raw.get(_case_id(record))
                if isinstance(entry, Mapping):
                    conflicts.extend([row for row in _as_list(entry.get("conflicts")) if isinstance(row, Mapping)])
                elif isinstance(entry, list):
                    conflicts.extend([row for row in entry if isinstance(row, Mapping)])
            else:
                for row in _as_list(raw):
                    if not isinstance(row, Mapping) or _case_id(row) != _case_id(record):
                        continue
                    nested = [
                        child
                        for child in _as_list(row.get("conflicts"))
                        if isinstance(child, Mapping)
                    ]
                    if "conflicts" in row:
                        conflicts.extend(nested)
                    else:
                        conflicts.append(row)
        deduplicated: list[Mapping[str, Any]] = []
        seen: set[bytes] = set()
        for conflict in conflicts:
            key = _canonical_json_bytes(conflict)
            if key not in seen:
                seen.add(key)
                deduplicated.append(conflict)
        return deduplicated

    def _metadata_differences(self, record: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        comparison = _as_mapping(record.get("metadata_comparison")) or {}
        raw = _first(comparison, ("differences", "diffs", "items"))
        if raw is None:
            raw = _first(record, ("metadata_differences", "differences"))
        return [row for row in _as_list(raw) if isinstance(row, Mapping)]

    def _validate_metadata_conflicts(self) -> None:
        difference_count = 0
        conflict_count = 0
        for record in self.semantic_records:
            case_id = _case_id(record)
            differences = self._metadata_differences(record)
            conflicts = self._combined_conflicts(record)
            difference_count += len(differences)
            conflict_count += len(conflicts)
            comparison = _as_mapping(record.get("metadata_comparison")) or {}
            declares_difference = bool(differences) or comparison.get("matches_runtime") is False or bool(comparison.get("has_difference"))
            if declares_difference:
                self.require(bool(conflicts), f"{case_id}: metadata difference has no conflict record")
            conflict_keys = {
                str(_first(conflict, ("difference_id", "field", "path", "conflict_id")) or "")
                for conflict in conflicts
            }
            for difference in differences:
                diff_key = str(_first(difference, ("difference_id", "field", "path", "id")) or "")
                covered = bool(diff_key) and any(diff_key == key or diff_key in key or key in diff_key for key in conflict_keys if key)
                self.require(covered, f"{case_id}: metadata difference {diff_key!r} is not covered by a conflict record")
            for conflict in conflicts:
                status = str(conflict.get("status") or "")
                resolution = _first(conflict, ("resolution", "precedence", "native_envelope_decision", "handling"))
                self.require(status in {"recorded", "acknowledged", "resolved", "requires_contract_review"}, f"{case_id}: invalid metadata conflict status {status!r}")
                self.require(bool(resolution), f"{case_id}: metadata conflict lacks an explicit resolution/precedence")
        self.checks["metadata_difference_count"] = difference_count
        self.checks["metadata_conflict_record_count"] = conflict_count

    def _source_bindings(self, block: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        raw = _first(block, ("source_bindings", "sources", "bindings", "source"))
        if isinstance(raw, Mapping):
            return [raw]
        return [row for row in _as_list(raw) if isinstance(row, Mapping)]

    def _validate_binding(self, binding: Mapping[str, Any], label: str) -> None:
        declared_path = _first(binding, ("artifact_path", "snapshot_path", "packet_path", "source_path", "path"))
        declared_hash = str(_first(binding, ("sha256", "source_sha256", "artifact_sha256")) or "")
        self.require(HASH_RE.fullmatch(declared_hash) is not None, f"{label}: source binding lacks a valid sha256")
        path = self.resolve_declared_path(declared_path, f"{label}.source")
        if path is not None:
            self.require(path.is_file(), f"{label}: source artifact does not exist: {path}")
            if path.is_file() and HASH_RE.fullmatch(declared_hash):
                self.require(_sha256_file(path) == declared_hash, f"{label}: source artifact sha256 mismatch: {path}")
        owner = _first(binding, ("owner_qualname", "qualname", "symbol", "owner_class"))
        module = _first(binding, ("owner_module", "module", "source_module"))
        self.require(bool(owner), f"{label}: source binding lacks owner/symbol provenance")
        self.require(bool(module), f"{label}: source binding lacks module provenance")
        self._reject_canonical_abc(binding, label)

    def _semantic_block(self, record: Mapping[str, Any], names: Sequence[str]) -> Mapping[str, Any]:
        for name in names:
            value = record.get(name)
            if isinstance(value, Mapping):
                return value
        semantics = _as_mapping(record.get("semantics")) or {}
        for name in names:
            value = semantics.get(name)
            if isinstance(value, Mapping):
                return value
        return {}

    def _validate_effective_sources(self) -> None:
        required = {
            "goal": ("goal",),
            "schema": ("schema",),
            "initialize_task": ("initialize_task", "init"),
            "is_successful": ("is_successful", "success"),
            "evaluator": ("evaluator", "evaluation"),
        }
        for record in self.semantic_records:
            case_id = _case_id(record)
            for label, aliases in required.items():
                block = self._semantic_block(record, aliases)
                self.require(bool(block), f"{case_id}: effective {label} block is missing")
                bindings = self._source_bindings(block)
                self.require(bool(bindings), f"{case_id}: effective {label} has no source bindings")
                for index, binding in enumerate(bindings):
                    self._validate_binding(binding, f"{case_id}.{label}.source_bindings[{index}]")
            goal = self._semantic_block(record, ("goal",))
            self.require(bool(goal.get("representation_kind")), f"{case_id}: goal representation_kind is missing")
            self.require(bool(_first(goal, ("generation_semantics", "template", "computed_expression", "prompt", "branches"))), f"{case_id}: goal-generation semantics are missing")
            schema = self._semantic_block(record, ("schema",))
            self.require("value" in schema or "effective_schema" in schema, f"{case_id}: effective schema value is missing (empty dict is valid but must be explicit)")
            init = self._semantic_block(record, ("initialize_task", "init"))
            success = self._semantic_block(record, ("is_successful", "success"))
            self.require(bool(_first(init, ("method_chain", "source_bindings", "bindings", "source"))), f"{case_id}: initialize_task method chain is missing")
            self.require(bool(_first(success, ("method_chain", "source_bindings", "bindings", "source"))), f"{case_id}: is_successful method chain is missing")
        self.checks["goal_schema_init_evaluator_sources_complete"] = True

    def _branch_ids(self, block: Mapping[str, Any]) -> set[str]:
        values = _as_list(block.get("branches"))
        return {
            str(_first(row, ("branch_id", "name", "value")) or "")
            for row in values
            if isinstance(row, Mapping)
        }

    def _validate_markor_edit_note(self) -> None:
        record = self.semantic_by_id.get("MarkorEditNote")
        self.require(record is not None, "MarkorEditNote semantic record is missing")
        if record is None:
            return
        goal = self._semantic_block(record, ("goal",))
        evaluator = self._semantic_block(record, ("evaluator", "evaluation"))
        expected = {"header", "footer", "replace"}
        self.require(goal.get("representation_kind") == "branch_template", "MarkorEditNote must be the sole branch_template goal")
        self.require(self._branch_ids(goal) == expected, "MarkorEditNote goal must preserve exactly header/footer/replace branches")
        self.require(self._branch_ids(evaluator) == expected, "MarkorEditNote evaluator must preserve exactly header/footer/replace branches")
        for label, block in (("goal", goal), ("evaluator", evaluator)):
            for branch in _as_list(block.get("branches")):
                if not isinstance(branch, Mapping):
                    continue
                branch_id = str(_first(branch, ("branch_id", "name", "value")) or "")
                self.require(bool(_first(branch, ("predicate", "condition"))), f"MarkorEditNote {label} branch {branch_id} lacks predicate")
                self.require(bool(_first(branch, ("template", "semantics", "expected_content"))), f"MarkorEditNote {label} branch {branch_id} lacks semantics")
        schema = self._semantic_block(record, ("schema",))
        schema_value = schema.get("value", schema.get("effective_schema"))
        enum: Any = None
        if isinstance(schema_value, Mapping):
            properties = _as_mapping(schema_value.get("properties")) or {}
            edit_type = _as_mapping(properties.get("edit_type")) or {}
            enum = edit_type.get("enum")
        self.require(set(_as_list(enum)) == expected, "MarkorEditNote schema must enumerate header/footer/replace")
        self.checks["markor_edit_note_three_branches"] = True

    def _validate_ir_proto_bindings(self) -> None:
        ir_records = [
            record
            for record in self.semantic_records
            if (_as_mapping(record.get("goal")) or {}).get("representation_kind") == "ir_proto_prompt"
        ]
        self.require(len(ir_records) == 25, "exactly 25 records must use ir_proto_prompt")
        definition_hashes: list[str] = []
        for record in ir_records:
            case_id = _case_id(record)
            goal = _as_mapping(record.get("goal")) or {}
            binding = _as_mapping(_first(goal, ("proto_binding", "task_proto_binding"))) or {}
            self.require(bool(binding), f"{case_id}: IR goal lacks task proto binding")
            self.require(str(_first(binding, ("task_name", "case_unit_id")) or "") == case_id, f"{case_id}: IR proto task name mismatch")
            source_path = str(_first(binding, ("artifact_path", "source_path", "path")) or "")
            self.require(PurePosixPath(source_path.replace("\\", "/")).name == "tasks.textproto", f"{case_id}: IR proto must bind tasks.textproto")
            source_hash = str(_first(binding, ("source_sha256", "sha256")) or "")
            self.require(HASH_RE.fullmatch(source_hash) is not None, f"{case_id}: IR tasks.textproto hash is missing")
            task_definition = _first(binding, ("task_definition", "task_proto", "message"))
            task_hash = str(_first(binding, ("task_definition_sha256", "task_proto_sha256", "message_sha256")) or "")
            self.require(isinstance(task_definition, Mapping), f"{case_id}: IR binding lacks canonical task definition")
            self.require(HASH_RE.fullmatch(task_hash) is not None, f"{case_id}: IR task-definition hash is missing")
            if isinstance(task_definition, Mapping) and HASH_RE.fullmatch(task_hash):
                self.require(_sha256_object(task_definition) == task_hash, f"{case_id}: IR task-definition hash mismatch")
                self.require(str(task_definition.get("name") or task_definition.get("task_name") or "") == case_id, f"{case_id}: canonical task definition name mismatch")
                definition_hashes.append(task_hash)
            definition_module = str(_first(record, ("definition_module", "canonical_module")) or "")
            definition_source = str(_first(record, ("definition_source_file", "canonical_source_file")) or "")
            provenance_text = json.dumps(record, sort_keys=True)
            self.require("information_retrieval_registry" in (definition_module + definition_source + provenance_text), f"{case_id}: dynamic IR registry provenance is missing")
            self.require("information_retrieval.py" in provenance_text, f"{case_id}: InformationRetrieval base provenance is missing")
        self.require(len(set(definition_hashes)) == 25, "IR task-definition hashes must be 25 unique values")
        self.checks["ir_proto_bindings"] = len(definition_hashes)

    def _prompt_hash_from_freeze(self, case_id: str) -> str:
        record = self.freeze_by_id.get(case_id, {})
        return str(_first(record, ("prompt_hash", "prompt_sha256", "drafter_prompt_hash")) or "")

    def _import_prompt_builder(self):
        source_root = self.paths.repo_root / "src"
        if str(source_root) not in sys.path:
            sys.path.insert(0, str(source_root))
        try:
            from evidence_system.contracts.draft import (  # type: ignore
                DEFAULT_PROMPT_VERSION,
                build_drafter_prompt,
            )
        except Exception as exc:  # pragma: no cover - error is reported to caller
            self.issues.append(f"cannot import the real contract drafter prompt builder: {exc}")
            return None, None
        return build_drafter_prompt, DEFAULT_PROMPT_VERSION

    def _validate_source_bundle_and_prompts(self) -> None:
        self.require(self.bundle.get("source_count") == EXPECTED_CASE_COUNT, "candidate source bundle source_count must be 116")
        self.require(len(self.bundle_sources) == EXPECTED_CASE_COUNT, "candidate source bundle must contain 116 sources")
        ids = [_case_id(row) for row in self.bundle_sources]
        self.require(len(set(ids)) == EXPECTED_CASE_COUNT, "candidate source-bundle case ids must be unique")
        self.require(set(ids) == set(self.semantic_by_id), "source-bundle and semantic-index case sets differ")
        ranked_ids = [
            _case_id(record)
            for record in sorted(self.semantic_records, key=lambda row: int(row.get("selection_rank", -1)))
        ]
        self.require(ids == ranked_ids, "candidate source-bundle order must follow semantic selection ranks 0..115")
        prompt_builder, default_version = self._import_prompt_builder()
        prompt_version = str(self.freeze.get("prompt_version") or self.bundle.get("prompt_version") or default_version or "")
        self.require(bool(prompt_version), "draft-input freeze must pin prompt_version")
        lowered_prompt_version = prompt_version.lower()
        self.require(
            not any(marker in lowered_prompt_version for marker in ("placeholder", "todo", "tbd", "需要", "待定")),
            "draft-input freeze prompt_version contains an unresolved placeholder",
        )
        for source in self.bundle_sources:
            case_id = _case_id(source)
            draft_input = _as_mapping(source.get("draft_input")) or {}
            frozen_input = self.freeze_by_id.get(case_id, {})
            view_kind = str(draft_input.get("view_kind") or source.get("view_kind") or "")
            path_text = str(draft_input.get("case_packet_path") or "")
            packet_path = self.resolve_declared_path(path_text, f"{case_id}.compact_packet")
            self.require(view_kind == "compact", f"{case_id}: source bundle must declare draft_input.view_kind=compact")
            basename = PurePosixPath(path_text.replace("\\", "/")).name.lower()
            self.require("compact" in basename and basename != "case_packet.md", f"{case_id}: drafter path is not an explicitly named compact packet")
            expected_packet_hash = str(draft_input.get("case_packet_sha256") or "")
            self.require(HASH_RE.fullmatch(expected_packet_hash) is not None, f"{case_id}: compact packet hash is missing")
            self.require(
                str(_first(frozen_input, ("case_packet_path", "compact_packet_path")) or "") == path_text,
                f"{case_id}: frozen compact packet path differs from source bundle",
            )
            self.require(
                str(_first(frozen_input, ("case_packet_sha256", "compact_packet_sha256")) or "")
                == expected_packet_hash,
                f"{case_id}: frozen compact packet hash differs from source bundle",
            )
            semantic_hash = str(_first(frozen_input, ("semantic_record_sha256", "semantics_sha256")) or "")
            semantic_record = self.semantic_by_id.get(case_id, {})
            expected_semantic_hash = str(semantic_record.get("record_sha256") or "")
            semantic_hash_input = dict(semantic_record)
            semantic_hash_input.pop("record_sha256", None)
            self.require(
                expected_semantic_hash == _sha256_object(semantic_hash_input),
                f"{case_id}: semantic record self-hash mismatch",
            )
            self.require(
                semantic_hash == expected_semantic_hash,
                f"{case_id}: frozen semantic-record hash mismatch",
            )
            if packet_path is not None and packet_path.is_file():
                size = packet_path.stat().st_size
                self.require(size <= self.max_compact_bytes, f"{case_id}: compact packet is {size} bytes, over {self.max_compact_bytes}")
                self.require(_sha256_file(packet_path) == expected_packet_hash, f"{case_id}: compact packet hash mismatch")
            audit = _as_mapping(source.get("audit_input")) or _as_mapping(draft_input.get("audit_input")) or {}
            full_path_text = str(_first(audit, ("full_case_packet_path", "case_packet_path")) or "")
            full_hash = str(_first(audit, ("full_case_packet_sha256", "case_packet_sha256")) or "")
            self.require(bool(full_path_text) and HASH_RE.fullmatch(full_hash) is not None, f"{case_id}: full audit packet path/hash is missing")
            self.require(
                str(_first(frozen_input, ("full_case_packet_path", "audit_packet_path")) or "") == full_path_text,
                f"{case_id}: frozen full audit packet path mismatch",
            )
            self.require(
                str(_first(frozen_input, ("full_case_packet_sha256", "audit_packet_sha256")) or "") == full_hash,
                f"{case_id}: frozen full audit packet hash mismatch",
            )
            full_path = self.resolve_declared_path(full_path_text, f"{case_id}.full_audit_packet") if full_path_text else None
            if full_path is not None and full_path.is_file():
                self.require(_sha256_file(full_path) == full_hash, f"{case_id}: full audit packet hash mismatch")
                if packet_path is not None and packet_path.is_file():
                    self.require(packet_path.stat().st_size < full_path.stat().st_size, f"{case_id}: compact packet is not smaller than full audit packet")
            if prompt_builder is None:
                continue
            try:
                prompt = prompt_builder(source, prompt_version=prompt_version)
            except Exception as exc:
                self.issues.append(f"{case_id}: real drafter cannot build prompt from compact source: {exc}")
                continue
            actual_prompt_hash = _sha256_object({"prompt": prompt})
            frozen_prompt_hash = self._prompt_hash_from_freeze(case_id)
            source_prompt_hash = str(_first(draft_input, ("prompt_hash", "prompt_sha256", "drafter_prompt_hash")) or "")
            self.require(HASH_RE.fullmatch(frozen_prompt_hash) is not None, f"{case_id}: frozen prompt hash is missing")
            self.require(actual_prompt_hash == frozen_prompt_hash, f"{case_id}: frozen prompt hash does not match real drafter prompt")
            if source_prompt_hash:
                self.require(actual_prompt_hash == source_prompt_hash, f"{case_id}: source-bundle prompt hash mismatch")
            self.prompt_hashes[case_id] = actual_prompt_hash
        self.require(len(self.prompt_hashes) == EXPECTED_CASE_COUNT, "exactly 116 prompt hashes must be verified")
        self.require(len(set(self.prompt_hashes.values())) == EXPECTED_CASE_COUNT, "all 116 real drafter prompt hashes must be unique")
        declared_prompt_set_hash = str(_first(self.freeze, ("prompt_hashes_hash", "prompt_set_hash")) or "")
        ordered_prompt_hashes = [
            self.prompt_hashes[_case_id(record)]
            for record in sorted(self.semantic_records, key=lambda row: int(row.get("selection_rank", -1)))
            if _case_id(record) in self.prompt_hashes
        ]
        self.require(declared_prompt_set_hash == _sha256_object(ordered_prompt_hashes), "freeze prompt_hashes_hash does not match rank-ordered prompt hashes")
        self.checks["unique_real_prompt_hashes"] = len(set(self.prompt_hashes.values()))

    def _slot_id(self, row: Mapping[str, Any]) -> str:
        return str(row.get("record_slot_id") or row.get("slot_id") or "")

    def _slot_sets(self) -> dict[str, list[Mapping[str, Any]]]:
        rank_by_case = {
            _case_id(record): int(record.get("selection_rank", -1))
            for record in self.semantic_records
        }
        all_rows = list(self.slot_records)
        official = [row for row in all_rows if rank_by_case.get(_case_id(row), -1) < 100]
        extra = [row for row in all_rows if rank_by_case.get(_case_id(row), -1) >= 100]
        return {"candidate116": all_rows, "official100": official, "extra16": extra}

    def _declared_slot_set(self, name: str) -> Mapping[str, Any]:
        sets = _as_mapping(self.slot_payload.get("slot_sets")) or {}
        aliases = {
            "candidate116": ("candidate116", "all348", "candidate116_348"),
            "official100": ("official100", "official300", "official100_300"),
            "extra16": ("extra16", "extra48", "extra16_48"),
        }
        for alias in aliases[name]:
            value = sets.get(alias)
            if isinstance(value, Mapping):
                return value
        return {}

    def _validate_slots(self) -> None:
        self.require(len(self.slot_records) == 348, "slot manifest must contain exactly 348 rows")
        ids = [self._slot_id(row) for row in self.slot_records]
        self.require(all(ids), "every slot row must have slot_id/record_slot_id")
        self.require(len(set(ids)) == 348, "slot ids must be 348 unique values")
        triples: list[tuple[str, str]] = []
        for row in self.slot_records:
            case_id = _case_id(row)
            agent_id = _normal_agent_id(row.get("agent_id"))
            triples.append((case_id, agent_id))
            self.require(case_id in self.semantic_by_id, f"slot references unknown case {case_id!r}")
            self.require(agent_id in EXPECTED_AGENT_IDS, f"slot has invalid agent id {agent_id!r}")
            expected_id = f"slot-androidworld-{case_id}-{agent_id}"
            self.require(self._slot_id(row) == expected_id, f"slot id is not canonical: {self._slot_id(row)!r} != {expected_id!r}")
        self.require(len(set(triples)) == 348, "each case/agent pair must occur exactly once")
        expected_triples = {
            (case_id, agent_id)
            for case_id in self.semantic_by_id
            for agent_id in EXPECTED_AGENT_IDS
        }
        self.require(set(triples) == expected_triples, "slot manifest is not the complete 116 x A/B/C Cartesian product")
        rank_by_case = {
            _case_id(record): int(record.get("selection_rank", -1))
            for record in self.semantic_records
        }
        agent_order = {agent_id: index for index, agent_id in enumerate(EXPECTED_AGENT_IDS)}
        expected_order = sorted(
            triples,
            key=lambda pair: (rank_by_case.get(pair[0], -1), agent_order.get(pair[1], -1)),
        )
        self.require(triples == expected_order, "348 slots must be ordered by selection rank, then agent_a/agent_b/agent_c")

        computed_sets = self._slot_sets()
        for name, expected_count in EXPECTED_SLOT_COUNTS.items():
            rows = computed_sets[name]
            slot_ids = [self._slot_id(row) for row in rows]
            declared = self._declared_slot_set(name)
            self.require(len(rows) == expected_count, f"{name} slot set must contain {expected_count} rows")
            self.require(declared.get("count") == expected_count, f"{name} declared slot count must be {expected_count}")
            declared_hash = str(_first(declared, ("slot_ids_hash", "sha256", "hash")) or "")
            self.require(declared_hash == _sha256_object(slot_ids), f"{name} slot_ids_hash mismatch")
            declared_ids = declared.get("slot_ids")
            if declared_ids is not None:
                self.require(declared_ids == slot_ids, f"{name} declared slot id list/order mismatch")
        self.checks["slot_counts"] = dict(EXPECTED_SLOT_COUNTS)

    def _manifest_cases(self, manifest: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        domains = [row for row in _as_list(manifest.get("domains")) if isinstance(row, Mapping)]
        android = next((row for row in domains if str(row.get("domain")) == "androidworld"), {})
        return [row for row in _as_list(android.get("case_units")) if isinstance(row, Mapping)]

    def _manifest_domain(self, manifest: Mapping[str, Any]) -> Mapping[str, Any]:
        return next(
            (row for row in _as_list(manifest.get("domains")) if isinstance(row, Mapping) and str(row.get("domain")) == "androidworld"),
            {},
        )

    def _binding_from_freeze(self, names: Sequence[str]) -> Mapping[str, Any]:
        bindings = _as_mapping(self.freeze.get("artifact_bindings")) or _as_mapping(self.freeze.get("bindings")) or {}
        for name in names:
            value = bindings.get(name)
            if isinstance(value, Mapping):
                return value
        return {}

    def _validate_frozen_artifact_binding(self, names: Sequence[str], actual_path: Path, label: str) -> None:
        binding = self._binding_from_freeze(names)
        self.require(bool(binding), f"draft-input freeze lacks {label} artifact binding")
        declared_path = str(_first(binding, ("path", "artifact_path")) or "")
        declared_hash = str(_first(binding, ("sha256", "artifact_sha256")) or "")
        try:
            expected_rel = actual_path.resolve().relative_to(self.paths.repo_root).as_posix()
        except ValueError:
            expected_rel = ""
        self.require(declared_path == expected_rel, f"draft-input freeze {label} path mismatch")
        self.require(HASH_RE.fullmatch(declared_hash) is not None, f"draft-input freeze {label} hash is invalid")
        if actual_path.is_file():
            self.require(declared_hash == _sha256_file(actual_path), f"draft-input freeze {label} hash mismatch")

    def _validate_manifests_and_freeze(self) -> None:
        candidate = self.load_json(self.paths.candidate_manifest, "candidate116 prelock manifest")
        extra = self.load_json(self.paths.extra16_manifest, "extra16 prelock manifest")
        self.require(str(candidate.get("status")) in {"draft", "prelock"}, "candidate manifest status must be draft/prelock")
        self.require(str(extra.get("status")) in {"draft", "prelock"}, "extra16 manifest status must be draft/prelock")
        candidate_cases = self._manifest_cases(candidate)
        extra_cases = self._manifest_cases(extra)
        candidate_ids = [_case_id(row) for row in candidate_cases]
        extra_ids = [_case_id(row) for row in extra_cases]
        ranked_ids = [
            _case_id(record)
            for record in sorted(self.semantic_records, key=lambda row: int(row.get("selection_rank", -1)))
        ]
        self.require(candidate_ids == ranked_ids, "candidate manifest case order/set differs from semantic rank order")
        self.require(extra_ids == ranked_ids[100:], "extra16 manifest must be the exact semantic tail ranks 100..115")
        candidate_domain = self._manifest_domain(candidate)
        extra_domain = self._manifest_domain(extra)
        self.require(candidate_domain.get("case_unit_count") == 116, "candidate manifest case_unit_count must be 116")
        self.require(candidate_domain.get("record_slot_count") == 348, "candidate manifest record_slot_count must be 348")
        self.require(extra_domain.get("case_unit_count") == 16, "extra16 manifest case_unit_count must be 16")
        self.require(extra_domain.get("record_slot_count") == 48, "extra16 manifest record_slot_count must be 48")
        candidate_slot_hash = str(_first(self._declared_slot_set("candidate116"), ("slot_ids_hash", "sha256", "hash")) or "")
        extra_slot_hash = str(_first(self._declared_slot_set("extra16"), ("slot_ids_hash", "sha256", "hash")) or "")
        self.require(candidate_domain.get("planned_record_slot_ids_hash") == candidate_slot_hash, "candidate manifest planned slot hash differs from 348-slot manifest")
        self.require(extra_domain.get("planned_record_slot_ids_hash") == extra_slot_hash, "extra16 manifest planned slot hash differs from 48-slot manifest")
        if self.paths.source_bundle.is_file():
            self.require(candidate.get("source_bundle_hash") == _sha256_file(self.paths.source_bundle), "candidate manifest source_bundle_hash mismatch")
        if self.paths.extra16_source_bundle is not None and self.paths.extra16_source_bundle.is_file():
            extra_bundle = self.load_json(self.paths.extra16_source_bundle, "extra16 compact source bundle")
            extra_sources = [row for row in _as_list(extra_bundle.get("sources")) if isinstance(row, Mapping)]
            self.require(extra_bundle.get("source_count") == 16 and len(extra_sources) == 16, "extra16 source bundle must contain exactly 16 sources")
            self.require([_case_id(row) for row in extra_sources] == ranked_ids[100:], "extra16 source bundle must be the exact rank-100..115 tail")
            candidate_by_id = {_case_id(row): row for row in self.bundle_sources}
            for row in extra_sources:
                case_id = _case_id(row)
                candidate_source = candidate_by_id.get(case_id, {})
                self.require(row == candidate_source, f"{case_id}: extra16 source entry differs from candidate116 compact entry")
            self.require(extra.get("source_bundle_hash") == _sha256_file(self.paths.extra16_source_bundle), "extra16 manifest source_bundle_hash mismatch")

        self.require(str(self.freeze.get("status")) == "frozen", "draft_input_freeze status must be frozen")
        self.require(self.freeze.get("source_count") == 116, "draft_input_freeze source_count must be 116")
        self.require(self.freeze.get("frozen_before_runs") is True, "draft_input_freeze must assert frozen_before_runs=true")
        self.require(self.freeze.get("expected_category_counts") == EXPECTED_GOAL_CATEGORY_COUNTS, "freeze expected category counts mismatch")
        self.require(self.freeze.get("category_counts") == EXPECTED_GOAL_CATEGORY_COUNTS, "freeze actual category counts mismatch")
        freeze_slot_sets = _as_mapping(self.freeze.get("slot_sets")) or {}
        for name, expected_count in EXPECTED_SLOT_COUNTS.items():
            frozen_set = _as_mapping(freeze_slot_sets.get(name)) or {}
            declared_set = self._declared_slot_set(name)
            self.require(
                frozen_set.get("count") == expected_count,
                f"draft_input_freeze {name} slot count mismatch",
            )
            self.require(
                _first(frozen_set, ("slot_ids_hash", "sha256", "hash"))
                == _first(declared_set, ("slot_ids_hash", "sha256", "hash")),
                f"draft_input_freeze {name} slot hash differs from slot manifest",
            )
        self.require(len(self.freeze_by_id) == 116, "draft_input_freeze must bind 116 per-case records")
        self.require(set(self.freeze_by_id) == set(self.semantic_by_id), "draft_input_freeze and semantics case sets differ")
        freeze_content_hash = str(
            self.freeze.get("freeze_sha256") or self.freeze.get("freeze_content_hash") or ""
        )
        freeze_hash_payload = dict(self.freeze)
        freeze_hash_payload.pop("freeze_sha256", None)
        freeze_hash_payload.pop("freeze_content_hash", None)
        self.require(
            freeze_content_hash == _sha256_object(freeze_hash_payload),
            "draft_input_freeze canonical content hash mismatch",
        )

        self._validate_frozen_artifact_binding(("semantic_index", "candidate116_semantic_index"), self.paths.semantic_index, "semantic index")
        self._validate_frozen_artifact_binding(("source_bundle", "candidate116_source_bundle"), self.paths.source_bundle, "candidate source bundle")
        if self.paths.extra16_source_bundle is not None:
            self._validate_frozen_artifact_binding(
                ("extra16_source_bundle",),
                self.paths.extra16_source_bundle,
                "extra16 source bundle",
            )
        self._validate_frozen_artifact_binding(("candidate_manifest", "candidate116_manifest"), self.paths.candidate_manifest, "candidate manifest")
        self._validate_frozen_artifact_binding(("extra16_manifest",), self.paths.extra16_manifest, "extra16 manifest")
        self._validate_frozen_artifact_binding(("slot_manifest", "candidate116_slot_manifest"), self.paths.slot_manifest, "slot manifest")
        if self.paths.conflict_ledger is not None:
            self._validate_frozen_artifact_binding(("metadata_conflicts", "conflict_ledger"), self.paths.conflict_ledger, "metadata conflicts")

        self.require(bool(self.freeze.get("freeze_id")), "draft-input freeze id is missing")

        if self.paths.agents_config is not None and self.paths.agents_config.is_file():
            actual_agents_hash = _sha256_file(self.paths.agents_config)
            self.require(candidate.get("agents_config_hash") == actual_agents_hash, "candidate manifest agents_config_hash differs from actual config")
            self.require(extra.get("agents_config_hash") == actual_agents_hash, "extra16 manifest agents_config_hash differs from actual config")
            self.require(self.freeze.get("agents_config_hash") == actual_agents_hash, "draft_input_freeze agents_config_hash differs from actual config")
        self.checks["draft_prelock_freeze_consistent"] = True

    def _snapshot_roots(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        roots = _first(payload, ("roots", "legacy_roots", "snapshots"))
        return roots if isinstance(roots, Mapping) else {}

    def _normal_snapshot_state(self, value: Any) -> Any:
        if isinstance(value, Mapping):
            ignored = {"captured_at", "capture_timestamp", "phase", "status", "label"}
            return {
                str(key): self._normal_snapshot_state(child)
                for key, child in sorted(value.items(), key=lambda item: str(item[0]))
                if str(key) not in ignored
            }
        if isinstance(value, list):
            return [self._normal_snapshot_state(child) for child in value]
        return value

    def _validate_old_root_snapshots(self) -> None:
        before = self.load_json(self.paths.old_snapshot_before, "old-root before snapshot")
        after = self.load_json(self.paths.old_snapshot_after, "old-root after snapshot")
        before_roots = self._snapshot_roots(before)
        after_roots = self._snapshot_roots(after)
        required_roots = {"results", "paper_result_packages", "neurips_ed_track_minimal"}
        self.require(required_roots.issubset(set(before_roots)), "old-root before snapshot does not cover all three immutable roots")
        self.require(required_roots.issubset(set(after_roots)), "old-root after snapshot does not cover all three immutable roots")
        for root_name in required_roots:
            before_state = _as_mapping(before_roots.get(root_name)) or {}
            after_state = _as_mapping(after_roots.get(root_name)) or {}
            for label, state in (("before", before_state), ("after", after_state)):
                tree_hash = str(_first(state, ("tree_sha256", "content_tree_sha256", "sha256")) or "")
                entry_count = _first(state, ("entry_count", "recursive_entry_count", "file_count"))
                self.require(HASH_RE.fullmatch(tree_hash) is not None, f"{root_name} {label} snapshot lacks content tree sha256")
                self.require(isinstance(entry_count, int) and entry_count >= 0, f"{root_name} {label} snapshot lacks integer entry count")
            self.require(self._normal_snapshot_state(before_state) == self._normal_snapshot_state(after_state), f"old root changed between snapshots: {root_name}")
        self.checks["old_root_pre_post_snapshots_equal"] = True

    def _validate_official100(self) -> None:
        path = self.paths.official100_selector
        self.require(path.is_file(), f"official100 selector is missing: {path}")
        if path.is_file():
            actual = _sha256_file(path)
            self.require(actual == EXPECTED_OFFICIAL100_SELECTOR_SHA256, "official100 selector changed from the frozen submitted hash")
            self.require(self.freeze.get("official100_selector_sha256") == actual, "draft_input_freeze official100 selector hash mismatch")
        self.checks["official100_selector_unchanged"] = True

    def _walk_forbidden_keys(self, value: Any, base: str) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                key_text = str(key)
                if key_text in RESULT_FIELD_NAMES:
                    self.issues.append(f"drafter-visible result field is forbidden at {base}.{key_text}")
                self._walk_forbidden_keys(child, f"{base}.{key_text}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                self._walk_forbidden_keys(child, f"{base}[{index}]")

    def _scan_bytes(self, path: Path, *, result_tokens: bool) -> None:
        if not path.is_file():
            return
        data = path.read_bytes()
        for pattern in HOST_ABSOLUTE_PATTERNS:
            if pattern.search(data):
                self.issues.append(f"host absolute path leaked into artifact: {path}")
                break
        if result_tokens:
            lowered = data.lower()
            for token in RESULT_TEXT_TOKENS:
                if token in lowered:
                    self.issues.append(f"result token {token.decode()} leaked into drafter-visible artifact: {path}")
                    break

    def _validate_structured_paths(self, value: Any, base: str) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                self._validate_structured_paths(child, f"{base}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                self._validate_structured_paths(child, f"{base}[{index}]")
        elif isinstance(value, str):
            encoded = value.encode("utf-8", errors="ignore")
            if any(pattern.search(encoded) for pattern in HOST_ABSOLUTE_PATTERNS):
                self.issues.append(f"host absolute path leaked at {base}")

    def _scan_forbidden_inputs_and_paths(self) -> None:
        # Only inputs visible to the contract drafter are checked for result
        # vocabulary.  Slot/manifests legitimately contain agent identifiers.
        self._walk_forbidden_keys(self.bundle, "$.source_bundle")
        self._walk_forbidden_keys(self.semantic_payload, "$.semantic_index")
        self._walk_forbidden_keys(self.freeze, "$.draft_input_freeze")
        self._validate_structured_paths(self.bundle, "$.source_bundle")
        self._validate_structured_paths(self.semantic_payload, "$.semantic_index")
        self._validate_structured_paths(self.freeze, "$.draft_input_freeze")
        self._validate_structured_paths(self.slot_payload, "$.slot_manifest")
        self._validate_structured_paths(self.load_json(self.paths.candidate_manifest, "candidate manifest path scan"), "$.candidate_manifest")
        self._validate_structured_paths(self.load_json(self.paths.extra16_manifest, "extra16 manifest path scan"), "$.extra16_manifest")
        if self.paths.conflict_ledger is not None:
            conflict_payload = self.load_json(self.paths.conflict_ledger, "conflict ledger path scan")
            self._walk_forbidden_keys(conflict_payload, "$.conflict_ledger")
            self._validate_structured_paths(conflict_payload, "$.conflict_ledger")

        scanned: set[Path] = set()
        for source in self.bundle_sources:
            draft_input = _as_mapping(source.get("draft_input")) or {}
            path = self.resolve_declared_path(draft_input.get("case_packet_path"), f"{_case_id(source)}.compact scan")
            if path is not None and path not in scanned:
                scanned.add(path)
                self._scan_bytes(path, result_tokens=True)
        for path in (
            self.paths.semantic_index,
            self.paths.source_bundle,
            self.paths.draft_input_freeze,
            self.paths.slot_manifest,
            self.paths.candidate_manifest,
            self.paths.extra16_manifest,
            self.paths.old_snapshot_before,
            self.paths.old_snapshot_after,
        ):
            self._scan_bytes(path, result_tokens=False)
        if self.paths.conflict_ledger is not None:
            self._scan_bytes(self.paths.conflict_ledger, result_tokens=False)
        self.checks["result_fields_and_host_paths_absent"] = True


def _discover_one(work_root: Path, explicit: Path | None, candidates: Sequence[str], label: str) -> Path:
    if explicit is not None:
        return explicit.resolve()
    matches = [(work_root / candidate).resolve() for candidate in candidates if (work_root / candidate).is_file()]
    unique = list(dict.fromkeys(matches))
    if len(unique) != 1:
        rendered = ", ".join(str(path) for path in unique) or "none"
        raise AcceptanceFailure([f"could not uniquely discover {label}; matches: {rendered}"])
    return unique[0]


def _discover_optional(
    work_root: Path,
    explicit: Path | None,
    candidates: Sequence[str],
    label: str,
) -> Path | None:
    if explicit is not None:
        return explicit.resolve()
    matches = [(work_root / candidate).resolve() for candidate in candidates if (work_root / candidate).is_file()]
    unique = list(dict.fromkeys(matches))
    if len(unique) > 1:
        raise AcceptanceFailure(
            [f"could not uniquely discover optional {label}; matches: {', '.join(str(path) for path in unique)}"]
        )
    return unique[0] if unique else None


def default_paths(
    *,
    repo_root: Path,
    work_root: Path,
    semantic_index: Path | None = None,
    source_bundle: Path | None = None,
    candidate_manifest: Path | None = None,
    extra16_manifest: Path | None = None,
    slot_manifest: Path | None = None,
    draft_input_freeze: Path | None = None,
    old_snapshot_before: Path | None = None,
    old_snapshot_after: Path | None = None,
    conflict_ledger: Path | None = None,
    extra16_source_bundle: Path | None = None,
    agents_config: Path | None = None,
) -> AcceptancePaths:
    work_root = work_root.resolve()
    repo_root = repo_root.resolve()
    semantic_index = _discover_one(
        work_root,
        semantic_index,
        (
            "indexes/androidworld_candidate116_semantic_index.json",
            "indexes/androidworld_candidate116_semantics.json",
            "semantics/androidworld_candidate116_semantic_index.json",
        ),
        "semantic index",
    )
    source_bundle = _discover_one(
        work_root,
        source_bundle,
        (
            "source_bundles/androidworld_candidate116_compact_source_bundle.json",
            "source_bundles/androidworld_candidate116_source_bundle.json",
        ),
        "candidate source bundle",
    )
    candidate_manifest = _discover_one(
        work_root,
        candidate_manifest,
        ("manifests/androidworld_candidate116_manifest.json",),
        "candidate manifest",
    )
    extra16_manifest = _discover_one(
        work_root,
        extra16_manifest,
        ("manifests/androidworld_extra16_manifest.json",),
        "extra16 manifest",
    )
    slot_manifest = _discover_one(
        work_root,
        slot_manifest,
        (
            "manifests/androidworld_candidate116_slot_manifest.json",
            "slots/androidworld_candidate116_slots.json",
            "manifests/androidworld_candidate116_slots.json",
            "manifests/androidworld_candidate116_slot_manifest.csv",
        ),
        "348-slot manifest",
    )
    draft_input_freeze = _discover_one(
        work_root,
        draft_input_freeze,
        (
            "freezes/androidworld_candidate116_draft_input_freeze.json",
            "manifests/androidworld_candidate116_draft_input_freeze.json",
            "draft_input_freeze.json",
        ),
        "draft-input freeze",
    )
    old_snapshot_before = _discover_one(
        work_root,
        old_snapshot_before,
        (
            "validation/old_roots_before.json",
            "validation/legacy_roots_before.json",
            "validation/old_root_snapshot_before.json",
        ),
        "old-root before snapshot",
    )
    old_snapshot_after = _discover_one(
        work_root,
        old_snapshot_after,
        (
            "validation/old_roots_after.json",
            "validation/legacy_roots_after.json",
            "validation/old_root_snapshot_after.json",
        ),
        "old-root after snapshot",
    )
    conflict_ledger = _discover_optional(
        work_root,
        conflict_ledger,
        (
            "indexes/androidworld_candidate116_metadata_conflicts.json",
            "validation/androidworld_candidate116_semantic_conflicts.json",
            "semantics/androidworld_candidate116_metadata_conflicts.json",
        ),
        "metadata-conflict ledger",
    )
    extra16_source_bundle = _discover_optional(
        work_root,
        extra16_source_bundle,
        (
            "source_bundles/androidworld_extra16_compact_source_bundle.json",
            "source_bundles/androidworld_extra16_source_bundle.json",
        ),
        "extra16 source bundle",
    )
    official100 = (
        repo_root
        / "experiments/official_splits/androidworld_full100/androidworld_selected_task_sources.json"
    ).resolve()
    return AcceptancePaths(
        repo_root=repo_root,
        work_root=work_root,
        semantic_index=semantic_index,
        source_bundle=source_bundle,
        candidate_manifest=candidate_manifest,
        extra16_manifest=extra16_manifest,
        slot_manifest=slot_manifest,
        draft_input_freeze=draft_input_freeze,
        old_snapshot_before=old_snapshot_before,
        old_snapshot_after=old_snapshot_after,
        official100_selector=official100,
        conflict_ledger=conflict_ledger,
        extra16_source_bundle=extra16_source_bundle,
        agents_config=(agents_config or (repo_root / "configs/agents.yaml")).resolve(),
    )


def validate_strict_acceptance(
    paths: AcceptancePaths,
    *,
    max_compact_bytes: int = 180_000,
) -> dict[str, Any]:
    """Run all acceptance checks and return a report without writing it."""

    return StrictAcceptance(paths, max_compact_bytes=max_compact_bytes).run()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    script = Path(__file__).resolve()
    default_work_root = script.parents[1]
    default_repo_root = script.parents[5]
    parser.add_argument("--repo-root", type=Path, default=default_repo_root)
    parser.add_argument("--work-root", type=Path, default=default_work_root)
    parser.add_argument("--semantic-index", type=Path)
    parser.add_argument("--source-bundle", type=Path)
    parser.add_argument("--candidate-manifest", type=Path)
    parser.add_argument("--extra16-manifest", type=Path)
    parser.add_argument("--slot-manifest", type=Path)
    parser.add_argument("--draft-input-freeze", type=Path)
    parser.add_argument("--old-snapshot-before", type=Path)
    parser.add_argument("--old-snapshot-after", type=Path)
    parser.add_argument("--conflict-ledger", type=Path)
    parser.add_argument("--extra16-source-bundle", type=Path)
    parser.add_argument("--agents-config", type=Path)
    parser.add_argument("--max-compact-bytes", type=int, default=180_000)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        paths = default_paths(
            repo_root=args.repo_root,
            work_root=args.work_root,
            semantic_index=args.semantic_index,
            source_bundle=args.source_bundle,
            candidate_manifest=args.candidate_manifest,
            extra16_manifest=args.extra16_manifest,
            slot_manifest=args.slot_manifest,
            draft_input_freeze=args.draft_input_freeze,
            old_snapshot_before=args.old_snapshot_before,
            old_snapshot_after=args.old_snapshot_after,
            conflict_ledger=args.conflict_ledger,
            extra16_source_bundle=args.extra16_source_bundle,
            agents_config=args.agents_config,
        )
        report = validate_strict_acceptance(paths, max_compact_bytes=args.max_compact_bytes)
    except AcceptanceFailure as exc:
        print(
            json.dumps(
                {
                    "schema_version": "androidworld_candidate116_strict_acceptance/v1",
                    "status": "fail",
                    "issues": list(exc.issues),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
