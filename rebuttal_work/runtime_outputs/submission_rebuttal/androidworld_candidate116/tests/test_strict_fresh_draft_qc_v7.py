#!/usr/bin/env python3
"""Hermetic positive and tamper tests for fresh candidate116 deterministic QC."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import strict_fresh_draft_postgen_qc as qc  # noqa: E402


CASE_ID = "CaseAlpha"
TASK_ID = "CaseAlpha"
SOURCE_PATH = "official/install/android_world/task_evals/single/case_alpha.py"
METADATA_PATH = "official/install/android_world/task_metadata.json"


SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "case_unit_id", "domain", "task_id", "native", "stronger"],
    "properties": {
        "schema_version": {"const": "case_checklist_v1"},
        "case_unit_id": {"type": "string", "minLength": 1},
        "domain": {"const": "androidworld"},
        "task_id": {"type": "string", "minLength": 1},
        "native": {
            "type": "object",
            "additionalProperties": False,
            "required": list(qc.REQUIRED_NATIVE_FIELDS),
            "properties": {
                "user_goal": {"$ref": "#/$defs/Justified"},
                "benchmark_success": {"$ref": "#/$defs/Justified"},
                "checked_by": {"$ref": "#/$defs/Justified"},
                "decisive_artifacts": {
                    "type": "array", "minItems": 1, "items": {"$ref": "#/$defs/Artifact"}
                },
                "success_if": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/Justified"}},
                "fail_if": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/Justified"}},
                "undecided_if": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/Justified"}},
            },
        },
        "stronger": {
            "type": "object", "additionalProperties": False,
            "required": ["additional_conditions"],
            "properties": {
                "additional_conditions": {
                    "type": "array", "items": {"$ref": "#/$defs/Condition"}
                }
            },
        },
    },
    "$defs": {
        "Support": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}},
        "Justified": {
            "type": "object", "additionalProperties": False,
            "required": ["text", "support"],
            "properties": {
                "text": {"type": "string", "minLength": 1},
                "support": {"$ref": "#/$defs/Support"},
                "rationale": {"type": "string", "minLength": 1},
            },
        },
        "Artifact": {
            "type": "object", "additionalProperties": False,
            "required": ["artifact", "question", "support"],
            "properties": {
                "artifact": {"type": "string", "minLength": 1},
                "question": {"type": "string", "minLength": 1},
                "support": {"$ref": "#/$defs/Support"},
            },
        },
        "Condition": {
            "type": "object", "additionalProperties": False,
            "required": ["id", "text", "rationale", "decisive_artifacts", "support"],
            "properties": {
                "id": {"type": "string", "minLength": 1},
                "text": {"type": "string", "minLength": 1},
                "rationale": {"type": "string", "minLength": 1},
                "decisive_artifacts": {
                    "type": "array", "minItems": 1, "items": {"$ref": "#/$defs/Artifact"}
                },
                "support": {"$ref": "#/$defs/Support"},
            },
        },
    },
}


SOURCE_TEXT = """class CaseAlpha:
    goal = "create a retained value"
    schema = {"type": "object"}

    def initialize_task(self, env):
        self.before = 0

    def is_successful(self, env):
        return 1.0 if env.value == 1 else 0.0
"""
METADATA_TEXT = '[{"task_name":"CaseAlpha","task_template":"Create the retained value."}]\n'


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _self_hash(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = dict(value)
    result.pop(field, None)
    result[field] = qc.canonical_sha256(result)
    return result


def _checklist(pointer: str | None = None) -> dict[str, Any]:
    pointer = pointer or f"{SOURCE_PATH}::CaseAlpha.is_successful"

    def justified(text: str) -> dict[str, Any]:
        return {"text": text, "support": [pointer]}

    def artifact(name: str) -> dict[str, Any]:
        return {
            "artifact": name,
            "question": "Does the retained evaluator record show the required value?",
            "support": [pointer],
        }

    return {
        "schema_version": "case_checklist_v1",
        "case_unit_id": CASE_ID,
        "domain": "androidworld",
        "task_id": TASK_ID,
        "native": {
            "user_goal": justified("Create the retained value."),
            "benchmark_success": justified("The raw evaluator returns one and the run is done."),
            "checked_by": justified("CaseAlpha.is_successful checks the retained value."),
            "decisive_artifacts": [artifact("Retained evaluator input and output")],
            "success_if": [justified("The retained evaluator output is one.")],
            "fail_if": [justified("The retained evaluator output is zero.")],
            "undecided_if": [justified("The required retained evaluator record is absent or corrupt.")],
        },
        "stronger": {
            "additional_conditions": [
                {
                    "id": "trace_method",
                    "text": "The retained trace shows the requested value was created.",
                    "rationale": "The native state check does not establish the interaction method.",
                    "decisive_artifacts": [artifact("Retained trace")],
                    "support": [pointer],
                }
            ]
        },
    }


def _command_event(item_id: str, command: str, output: str) -> list[dict[str, Any]]:
    base = {"id": item_id, "type": "command_execution", "command": command}
    return [
        {
            "type": "item.started",
            "item": dict(base)
            | {
                "status": "in_progress",
                "exit_code": None,
                "aggregated_output": "",
            },
        },
        {
            "type": "item.completed",
            "item": dict(base) | {
                "status": "completed", "exit_code": 0, "aggregated_output": output
            },
        },
    ]


class Fixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.raw = root / "raw"
        self.packets = root / "packets"
        self.toolchain = root / "toolchain"
        self.coverage = root / "coverage"
        self.order_path = root / "case_order.json"
        self.expectations_path = root / "expectations.json"
        self.case_dir = self.raw / CASE_ID
        self.packet_path = self.packets / CASE_ID / "case_packet.md"
        self.coverage_path = self.coverage / CASE_ID / "model_input_coverage.json"
        self.operation_expectations_path = (
            self.coverage / CASE_ID / "reader_operation_expectations.json"
        )
        for directory in (self.raw, self.packets, self.toolchain, self.coverage, self.case_dir):
            directory.mkdir(parents=True, exist_ok=True)
        self._build()

    def _build(self) -> None:
        self._build_packet()
        requirements = self._build_coverage()
        operation_expectations = self._build_operation_expectations(requirements)
        control = self._build_toolchain()
        self._build_outputs(
            requirements, operation_expectations, control["codex_cli_path"]
        )
        self._build_batch()
        self._build_expectations(control)
        _write_json(self.order_path, [CASE_ID])

    def _build_packet(self) -> None:
        raw_root = self.packets / CASE_ID / "raw_case"
        source_file = raw_root / SOURCE_PATH
        metadata_file = raw_root / METADATA_PATH
        source_file.parent.mkdir(parents=True, exist_ok=True)
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text(SOURCE_TEXT, encoding="utf-8")
        metadata_file.write_text(METADATA_TEXT, encoding="utf-8")
        source_sha = qc.sha256_file(source_file)
        metadata_sha = qc.sha256_file(metadata_file)
        packet = (
            "# Case Packet\n\n"
            "## Case Metadata\n\n"
            "- domain: `androidworld`\n"
            f"- case_unit_id: `{CASE_ID}`\n"
            f"- task_id: `{TASK_ID}`\n\n"
            "## Source Inventory\n\n"
            f"- `{METADATA_PATH}`\n"
            f"- `{SOURCE_PATH}`\n\n"
            "## Packet Source Files\n\n"
            f"### `{METADATA_PATH}`\n\n"
            "Source ref: `<FIXTURE>/task_metadata.json`\n\n"
            "```json\n"
            f"{METADATA_TEXT}```\n\n"
            f"### `{SOURCE_PATH}`\n\n"
            "Source ref: `<FIXTURE>/case_alpha.py`\n\n"
            "```python\n"
            f"{SOURCE_TEXT}```\n"
        )
        self.packet_path.parent.mkdir(parents=True, exist_ok=True)
        self.packet_path.write_text(packet, encoding="utf-8")
        _write_json(
            self.packets / CASE_ID / "raw_case_manifest.json",
            {
                "case_unit_id": CASE_ID,
                "task_id": TASK_ID,
                "packet_files": [METADATA_PATH, SOURCE_PATH],
                "sha256_per_file": {METADATA_PATH: metadata_sha, SOURCE_PATH: source_sha},
            },
        )

    def _build_coverage(self) -> dict[str, Any]:
        raw_root = self.packets / CASE_ID / "raw_case"
        source = raw_root / SOURCE_PATH
        metadata = raw_root / METADATA_PATH
        source_bytes = source.read_bytes()
        metadata_bytes = metadata.read_bytes()
        line_count = len(source_bytes.splitlines(keepends=True))
        metadata_line_count = len(metadata_bytes.splitlines(keepends=True))
        source_sha = qc.sha256_bytes(source_bytes)
        metadata_sha = qc.sha256_bytes(metadata_bytes)
        common = {
            "raw_authority": "official_source",
            "path": SOURCE_PATH,
            "start_line": 1,
            "end_line": line_count,
            "file_sha256": source_sha,
            "snippet_sha256": source_sha,
            "owner_module": "android_world.task_evals.single.case_alpha",
            "owner_qualname": "CaseAlpha",
        }
        metadata_common = {
            "anchor": "metadata_task_description",
            "raw_authority": "official_source",
            "path": METADATA_PATH,
            "start_line": 1,
            "end_line": metadata_line_count,
            "file_sha256": metadata_sha,
            "snippet_sha256": metadata_sha,
            "owner_module": None,
            "owner_qualname": TASK_ID,
        }
        anchors = [
            {"anchor": anchor, "required_raw_official_ranges": [
                metadata_common if anchor == "metadata_task_description" else dict(common) | {"anchor": anchor}
            ]}
            for anchor in qc.REQUIRED_COVERAGE_ANCHORS
        ]
        flat = sorted(
            [row for anchor in anchors for row in anchor["required_raw_official_ranges"]],
            key=lambda row: (row["anchor"], row["path"], row["start_line"], row["end_line"]),
        )
        source_specs = [
            (METADATA_PATH, metadata_bytes, metadata_line_count, metadata_sha),
            (SOURCE_PATH, source_bytes, line_count, source_sha),
        ]
        closure = []
        required_ranges = []
        for path, content, lines, digest in source_specs:
            chunk = {
                "start_line": 1, "end_line": lines, "size_bytes": len(content),
                "snippet_sha256": digest,
                "snippet_ends_with_newline": content.endswith(b"\n"),
                "planned_reader_envelope_max_bytes": len(content) + 100,
                "planned_reader_envelope_max_o200k_tokens": 100,
                "chunk_index": 0, "chunk_count": 1,
            }
            closure.append({
                "path": path, "physical_read_path": path, "file_sha256": digest,
                "size_bytes": len(content), "line_count": lines,
                "logical_aliases": [path], "logical_alias_count": 1,
                "logical_alias_bindings": [{
                    "path": path, "file_sha256": digest, "size_bytes": len(content),
                    "line_count": lines, "source_ref": f"<FIXTURE>/{Path(path).name}",
                }],
                "chunks": [chunk], "navigation_reasons": [],
            })
            required_ranges.append({
                "anchor": "raw_source_closure_chunk", "raw_authority": "official_source",
                "path": path, "logical_aliases": [path], "start_line": 1, "end_line": lines,
                "file_sha256": digest, "snippet_sha256": digest,
                "chunk_index": 0, "chunk_count": 1, "chunk_size_bytes": len(content),
                "snippet_ends_with_newline": content.endswith(b"\n"),
                "owner_module": None, "owner_qualname": "complete_file_chunk",
            })
        tokenizer_binding = {
            "encoding": "o200k_base",
            "tiktoken_version": "0.12.0",
            "merge_table_sha256": "1" * 64,
        }
        tokenizer_binding["binding_sha256"] = qc.canonical_sha256(
            tokenizer_binding
        )
        source_inventory = [
            {
                "path": path,
                "sha256": digest,
                "size_bytes": len(content),
                "line_count": lines,
            }
            for path, content, lines, digest in source_specs
        ]
        payload = {
            "schema_version": "androidworld_candidate116_staged_source_coverage_requirements/v1",
            "production_namespace": qc.PRODUCTION_NAMESPACE,
            "case_unit_id": CASE_ID,
            "task_id": TASK_ID,
            "policy": {
                "runtime_semantics_authority": "raw_official_source_ranges",
                "derived_role": "navigation_identity_closure_and_conflict_only",
                "required_anchors": list(qc.REQUIRED_COVERAGE_ANCHORS),
                "max_coverage_chunk_bytes": qc.MAX_COVERAGE_CHUNK_BYTES,
                "max_reader_envelope_bytes": qc.MAX_READER_ENVELOPE_BYTES,
                "max_reader_envelope_o200k_tokens": qc.MAX_READER_ENVELOPE_TOKENS,
                "max_plan_row_serialized_bytes": qc.MAX_COVERAGE_PLAN_ROW_BYTES,
                "max_plan_page_output_bytes": qc.MAX_COVERAGE_PLAN_PAGE_OUTPUT_BYTES,
                "max_plan_page_o200k_tokens": qc.MAX_COVERAGE_PLAN_PAGE_TOKENS,
                "recursive_source_ref_mapping_missing_count": 0,
                "source_binding_mapping_missing_count": 0,
                "every_distinct_raw_official_inventory_payload_must_be_read_completely": True,
                "raw_inventory_members_may_never_be_excluded_by_navigation_or_ast": True,
                "byte_identical_aliases_share_one_physical_read_only_when_hash_bound": True,
                "chunks_must_be_read_separately_in_listed_order": True,
                "case_packet_one_shot_read_forbidden": True,
            },
            "tokenizer_binding": tokenizer_binding,
            "derived_navigation": {
                "canonical_module": "android_world.task_evals.single.case_alpha",
                "canonical_source_file": SOURCE_PATH,
                "runtime_reported_class": TASK_ID,
                "runtime_reported_module": "android_world.task_evals.single.case_alpha",
                "readiness": "ready",
                "metadata_conflicts": [],
                "metadata_comparison_status": "checked",
                "record_sha256": "2" * 64,
            },
            "anchors": anchors,
            "anchor_raw_official_ranges": flat,
            "raw_official_source_closure": closure,
            "raw_official_source_closure_count": 2,
            "raw_official_inventory_member_count": 2,
            "raw_official_distinct_sha_count": 2,
            "raw_official_omitted_count": 0,
            "raw_official_inventory_aliases_sha256": qc.canonical_sha256([METADATA_PATH, SOURCE_PATH]),
            "source_inventory": source_inventory,
            "source_closure_audit": {
                "method": "all_raw_official_inventory_members_exhaustively_bound_before_ast_audit",
                "unresolved_internal_imports": [],
                "unresolved_internal_import_count": 0,
                "plan_member_count": 2,
                "plan_distinct_content_count": 2,
            },
            "decisive_call_closure": {
                "algorithm": "packet_local_ast_fixed_point_v1",
                "fixed_point_reached": True,
                "packet_local_unresolved_count": 0,
                "resolved_edges": [],
                "resolved_edges_sha256": qc.canonical_sha256([]),
                "selected_definition_count": 0,
                "unresolved_external_semantic_direct_calls": [],
            },
            "required_ranges": required_ranges,
            "required_range_count": 2,
            "coverage_pagination": "serialized_byte_and_o200k_token_envelope_v1",
            "coverage_pages": [
                {
                    "page_index": 0,
                    "start_range_index": 0,
                    "end_range_index_exclusive": 2,
                    "row_count": 2,
                    "max_row_serialized_bytes": max(len(qc.canonical_bytes(row)) for row in required_ranges),
                    "planned_output_size_bytes": 500,
                    "planned_output_o200k_tokens": 100,
                }
            ],
            "coverage_page_count": 1,
            "case_packet_sha256": qc.sha256_file(self.packet_path),
        }
        payload = _self_hash(payload, "requirements_sha256")
        _write_json(self.coverage_path, payload)
        return payload

    def _build_operation_expectations(
        self, requirements: dict[str, Any]
    ) -> dict[str, Any]:
        packet = qc.parse_packet(
            self.packet_path,
            self.packets / CASE_ID,
            CASE_ID,
            TASK_ID,
        )
        specs = qc._expected_reader_operations(requirements, packet)
        operations = []
        for spec in specs:
            kind = spec["kind"]
            record = {
                "operation_index": spec["operation_index"],
                "kind": kind,
                "argv": spec["argv"],
                "argv_sha256": qc.canonical_sha256(spec["argv"]),
                "semantic_command": spec["semantic_command"],
                "exact_command": spec["exact_command"],
                "event_command_sha256": qc._sha256_text(spec["exact_command"]),
                "semantic_identity": spec["semantic_identity"],
                "body_sha256": qc._sha256_text(spec["body"]),
                "body_size_bytes": len(spec["body"].encode("utf-8")),
                "body_line_count": spec["body"].count("\n"),
                "body_ends_with_newline": True,
                "terminal_completion": spec["completion"],
                "expected_full_output_sha256": qc._sha256_text(spec["output"]),
                "expected_full_output_size_bytes": len(spec["output"].encode("utf-8")),
                "expected_full_output_o200k_tokens": 100,
                "max_full_output_size_bytes": (
                    qc.MAX_COVERAGE_PLAN_PAGE_OUTPUT_BYTES
                    if kind == "plan-page"
                    else qc.MAX_READER_ENVELOPE_BYTES
                ),
                "max_full_output_o200k_tokens": (
                    qc.MAX_COVERAGE_PLAN_PAGE_TOKENS
                    if kind == "plan-page"
                    else qc.MAX_READER_ENVELOPE_TOKENS
                ),
                "aggregated_output_must_equal_exact_bytes": True,
            }
            record["operation_sha256"] = qc.canonical_sha256(record)
            operations.append(record)
        payload = {
            "schema_version": qc.READER_OPERATION_EXPECTATIONS_SCHEMA,
            "production_namespace": qc.PRODUCTION_NAMESPACE,
            "case_unit_id": CASE_ID,
            "task_id": TASK_ID,
            "coverage_requirements_sha256": requirements["requirements_sha256"],
            "case_packet_sha256": qc.sha256_file(self.packet_path),
            "tokenizer_binding": requirements["tokenizer_binding"],
            "event_trust_policy": {
                "accepted_event_type": "item.completed",
                "accepted_output_field": "aggregated_output",
                "same_id_started_completed_pair_required": True,
                "completed_status_required": "completed",
                "completed_exit_code_required": 0,
                "model_supplied_shell_wrapper_pipeline_or_chain_allowed": False,
                "additional_command_count_allowed": 0,
                "terminal_completion_must_be_unique_and_last": True,
                "full_body_and_output_identity_required": True,
                "agent_message_before_or_between_commands_allowed": False,
                "terminal_agent_message_count_required": 1,
                "reasoning_items_allowed_before_terminal_agent_message": True,
                "exact_outer_framing_required": (
                    "thread.started_then_turn.started_then_items_then_turn.completed"
                ),
            },
            "event_shell_carrier": qc._codex_event_shell_carrier_binding(),
            "global_order": "overview_then_header_then_all_pages_then_all_ranges",
            "operation_count": len(operations),
            "overview_operation_count": 1,
            "header_operation_count": 1,
            "plan_page_operation_count": requirements["coverage_page_count"],
            "read_operation_count": requirements["required_range_count"],
            "operations": operations,
            "operations_sha256": qc.canonical_sha256(operations),
        }
        payload["reader_operation_expectations_sha256"] = qc.canonical_sha256(payload)
        _write_json(self.operation_expectations_path, payload)
        return payload

    def _build_toolchain(self) -> dict[str, Any]:
        paths = {
            "codex_cli": self.toolchain / "bin" / "codex",
            "prompt": self.toolchain / "prompts" / "draft.prompt.md",
            "schema": self.toolchain / "schemas" / "case_checklist.schema.json",
            "template": self.toolchain / "templates" / "case_checklist.template.yaml",
            "config": self.toolchain / "config" / "draft_config.json",
        }
        for path in paths.values():
            path.parent.mkdir(parents=True, exist_ok=True)
        paths["codex_cli"].write_bytes(b"fixture-codex-cli\n")
        paths["codex_cli"].chmod(0o755)
        paths["prompt"].write_text("fresh v7 prompt\n", encoding="utf-8")
        _write_json(paths["schema"], SCHEMA)
        paths["template"].write_text("schema_version: case_checklist_v1\n", encoding="utf-8")
        carried = {
            name: qc.sha256_file(paths[name])
            for name in ("codex_cli", "prompt", "schema", "template")
        }
        _write_json(paths["config"], {"model": "gpt-5.6-sol", "frozen_binding_hashes": carried})
        return {"paths": paths, "codex_cli_path": paths["codex_cli"]}

    def _build_outputs(
        self,
        requirements: dict[str, Any],
        operation_expectations: dict[str, Any],
        cli_path: Path,
    ) -> None:
        checklist = _checklist()
        body = {"native": checklist["native"], "stronger": checklist["stronger"]}
        output_text = json.dumps(body, ensure_ascii=False)
        req_sha = requirements["requirements_sha256"]
        workspace = Path("/private/tmp/fresh_qc_fixture") / CASE_ID
        disabled = ["apps", "plugins"]
        configs = [
            'default_permissions="candidate_draft_isolated"',
            'model_reasoning_effort="xhigh"',
        ]
        command = [
            str(cli_path.resolve()), "-a", "never", "--strict-config", "exec",
            "--cd", str(workspace), "--skip-git-repo-check", "--ephemeral",
            "--ignore-user-config", "--ignore-rules", "--model", "gpt-5.6-sol",
        ]
        for value in configs:
            command.extend(("-c", value))
        for feature in disabled:
            command.extend(("--disable", feature))
        command.extend((
            "--color", "never", "--json", "--output-schema", str(workspace / "output_schema.json"),
            "-o", str(workspace / "draft_body.json"), "-",
        ))
        self.codex_argv_sha256 = qc.canonical_sha256(command)
        packet = qc.parse_packet(
            self.packet_path,
            self.packets / CASE_ID,
            CASE_ID,
            TASK_ID,
        )
        specs = qc._expected_reader_operations(requirements, packet)
        events: list[dict[str, Any]] = [
            {"type": "thread.started", "thread_id": "fixture-thread"},
            {"type": "turn.started"},
        ]
        for index, (operation, spec) in enumerate(
            zip(operation_expectations["operations"], specs, strict=True)
        ):
            events.extend(
                _command_event(
                    f"cmd-{index:03d}",
                    operation["exact_command"],
                    spec["output"],
                )
            )
        events.append({
            "type": "item.completed",
            "item": {"id": "agent", "type": "agent_message", "text": output_text},
        })
        events.append({
            "type": "turn.completed",
            "usage": {
                "input_tokens": 1000,
                "cached_input_tokens": 100,
                "output_tokens": 200,
                "reasoning_output_tokens": 50,
            },
        })
        completed_operations = []
        covered_ranges = []
        command_ids = []
        for index, (operation, spec) in enumerate(
            zip(operation_expectations["operations"], specs, strict=True)
        ):
            command_id = f"cmd-{index:03d}"
            command_ids.append(command_id)
            output_sha = qc._sha256_text(spec["output"])
            completed_operations.append(
                {
                    "operation_index": index,
                    "kind": operation["kind"],
                    "operation_sha256": operation["operation_sha256"],
                    "completed_event_id": command_id,
                    "argv_sha256": operation["argv_sha256"],
                    "event_command_sha256": operation["event_command_sha256"],
                    "expected_output_sha256": operation[
                        "expected_full_output_sha256"
                    ],
                    "observed_output_sha256": output_sha,
                    "observed_output_size_bytes": len(
                        spec["output"].encode("utf-8")
                    ),
                    "completion_proof": spec["completion"],
                }
            )
            if operation["kind"] == "read":
                range_index = operation["semantic_identity"]["range_index"]
                row = requirements["required_ranges"][range_index]
                covered_ranges.append(
                    {
                        "range_index": range_index,
                        "anchor": row["anchor"],
                        "path": row["path"],
                        "logical_aliases": row["logical_aliases"],
                        "start_line": row["start_line"],
                        "end_line": row["end_line"],
                        "file_sha256": row["file_sha256"],
                        "snippet_sha256": row["snippet_sha256"],
                        "reader_argv_sha256": operation["argv_sha256"],
                        "completed_event_id": command_id,
                        "completed_output_sha256": output_sha,
                        "completion_proof": spec["completion"],
                    }
                )
        receipt = {
            "schema_version": qc.COVERAGE_RECEIPT_SCHEMA,
            "production_namespace": qc.PRODUCTION_NAMESPACE,
            "status": "all_required_reader_operations_completed",
            "case_unit_id": CASE_ID,
            "requirements_sha256": req_sha,
            "reader_operation_expectations_sha256": operation_expectations[
                "reader_operation_expectations_sha256"
            ],
            "operations_sha256": operation_expectations["operations_sha256"],
            "required_operation_count": len(completed_operations),
            "completed_operation_count": len(completed_operations),
            "completed_operations": completed_operations,
            "completed_operations_sha256": qc.canonical_sha256(completed_operations),
            "completed_command_event_ids": command_ids,
            "completed_command_event_ids_sha256": qc.canonical_sha256(command_ids),
            "required_range_count": len(requirements["required_ranges"]),
            "covered_range_count": len(covered_ranges),
            "covered_ranges": covered_ranges,
            "coverage_page_count": requirements["coverage_page_count"],
            "coverage_pages_read": list(range(requirements["coverage_page_count"])),
            "additional_command_count": 0,
            "global_order": "overview_then_header_then_all_pages_then_all_ranges",
        }
        receipt["coverage_receipt_sha256"] = qc.canonical_sha256(receipt)
        usage = qc._normalized_usage(events)
        api = {
            "id": "fixture-thread",
            "status": "completed",
            "model": "gpt-5.6-sol",
            "provider": "codex_cli",
            "output_text": output_text,
            "output": [
                {"type": "reasoning", "summary": []},
                {"type": "message", "content": [{"type": "output_text", "text": output_text}]},
            ],
            "usage": usage,
            "codex_cli": {
                "auth_mode": "codex_login",
                "returncode": 0,
                "timeout_seconds": 1800,
                "sandbox": None,
                "permission_profile": "candidate_draft_isolated",
                "permission_profile_workspace_access": "read",
                "permission_profile_network_enabled": False,
                "full_canonical_packet_in_readonly_workspace": True,
                "full_canonical_packet_in_stdin": False,
                "command": command,
                "events": events,
                "malformed_event_lines": [],
                "stderr": "",
                "coverage_receipt": receipt,
            },
        }
        attempt_prefix = self.case_dir / "attempt_01"
        api_path = attempt_prefix.with_suffix(".api_response.json")
        reasoning_path = attempt_prefix.with_suffix(".reasoning_summary.txt")
        llm = {
            "schema_version": "llm_call/v1",
            "provider": "codex_cli",
            "model": "gpt-5.6-sol",
            "model_version": "gpt-5.6-sol",
            "api_key_env": "CODEX_HOME",
            "domain": "androidworld",
            "case_unit_id": CASE_ID,
            "task_id": TASK_ID,
            "phase": "draft",
            "experiment_type": "minimal_package",
            "agent_id_or_role": "case_checklist_drafter",
            "request_timestamp": "2026-07-16T00:00:00+00:00",
            "response_timestamp": "2026-07-16T00:01:00+00:00",
            "temperature": 0.0,
            "max_tokens": 20000,
            "timeout_seconds": 1800,
            "retry_index": 0,
            "token_usage": qc._token_usage(usage),
            "cost": {"amount": None},
            "response_metadata": {
                "response_id": "fixture-thread",
                "response_status": "completed",
                "provider_model": "gpt-5.6-sol",
                "reasoning_effort": "xhigh",
                "raw_api_response_path": str(api_path),
                "reasoning_summary_path": str(reasoning_path),
                "auth_mode": "codex_login",
                "max_output_tokens_enforced": False,
            },
        }
        payloads = {
            "checklist.json": qc.canonical_checklist_json(checklist),
            "checklist.yaml": qc.canonical_checklist_yaml(checklist),
            "api_response.json": (json.dumps(api, ensure_ascii=False, indent=2) + "\n").encode(),
            "llm_call.json": (json.dumps(llm, ensure_ascii=False, indent=2) + "\n").encode(),
            "reasoning_summary.txt": b"",
            "stderr.log": b"",
            "stdout.log": b"",
        }
        for name, content in payloads.items():
            (self.case_dir / name).write_bytes(content)
            (self.case_dir / f"attempt_01.{name}").write_bytes(content)

    def _build_batch(self) -> None:
        _write_json(
            self.raw / "_batch_summary.json",
            {
                "total_cases": 1, "completed_cases": 1, "success_cases": 1,
                "failed_cases": 0, "skipped_cases": 0, "provider": "codex",
                "model": "gpt-5.6-sol", "reasoning_effort": "xhigh",
                "codex_sandbox": "read-only",
            },
        )
        row = {
            "case_unit_dir": CASE_ID,
            "case_packet": str(self.packet_path),
            "status": "success",
            "attempts": [{
                "attempt_index": 1, "max_output_tokens": 20000,
                "codex_timeout_seconds": 1800, "returncode": 0,
                "stderr_tail": "",
            }],
            "quality_warnings": [],
            "checklist_path": str(self.case_dir / "checklist.yaml"),
        }
        (self.raw / "_batch_results.jsonl").write_text(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
        )

    def _build_expectations(self, control: dict[str, Any]) -> None:
        paths = control["paths"]
        bindings = {
            name: {
                **(
                    {"path": str(paths[name].resolve())}
                    if name in {"codex_cli", "config"}
                    else {
                        "relative_path": paths[name]
                        .relative_to(self.toolchain)
                        .as_posix()
                    }
                ),
                "sha256": qc.sha256_file(paths[name]),
                "size_bytes": paths[name].stat().st_size,
            }
            for name in qc.REQUIRED_CONTROL_BINDINGS
        }
        tree = qc.tree_binding(self.toolchain)
        case_files = sorted(
            [name for name in (
                "checklist.yaml", "checklist.json", "api_response.json", "llm_call.json",
                "reasoning_summary.txt", "stderr.log", "stdout.log",
            ) for name in (name, f"attempt_01.{name}")]
        )
        value = {
            "schema_version": qc.EXPECTATIONS_SCHEMA,
            "expected_case_count": 1,
            "domain": "androidworld",
            "case_order_sha256": qc.canonical_sha256([CASE_ID]),
            "expected_attempt_index": 1,
            "expected_global_files": ["_batch_results.jsonl", "_batch_summary.json"],
            "expected_case_files": case_files,
            "coverage_global_files": [],
            "control_bindings": bindings,
            "toolchain_tree": {"file_count": tree["file_count"], "files_sha256": tree["files_sha256"]},
            "config_must_carry_binding_hashes": ["codex_cli", "prompt", "schema", "template"],
            "runtime": {
                "model": "gpt-5.6-sol",
                "reasoning_effort": "xhigh",
                "auth_mode": "codex_login",
                "permission_profile": "candidate_draft_isolated",
                "timeout_seconds": 1800,
                "max_output_tokens": 20000,
                "native_runner_sandbox_label": "read-only",
                "disabled_features": ["apps", "plugins"],
                "config_overrides": [
                    'default_permissions="candidate_draft_isolated"',
                    'model_reasoning_effort="xhigh"',
                ],
                "required_flags": [
                    "--skip-git-repo-check", "--ephemeral", "--ignore-user-config",
                    "--ignore-rules", "--color", "--json",
                ],
            },
            "cases": [{
                "case_unit_id": CASE_ID,
                "task_id": TASK_ID,
                "packet_relative_path": f"{CASE_ID}/case_packet.md",
                "packet_sha256": qc.sha256_file(self.packet_path),
                "coverage_relative_path": f"{CASE_ID}/model_input_coverage.json",
                "coverage_sha256": qc.sha256_file(self.coverage_path),
                "reader_operation_expectations_relative_path": (
                    f"{CASE_ID}/reader_operation_expectations.json"
                ),
                "reader_operation_expectations_file_sha256": qc.sha256_file(
                    self.operation_expectations_path
                ),
                "reader_operation_expectations_sha256": json.loads(
                    self.operation_expectations_path.read_text(encoding="utf-8")
                )["reader_operation_expectations_sha256"],
                "recorded_packet_path": str(self.packet_path),
                "codex_argv_sha256": self.codex_argv_sha256,
            }],
        }
        _write_json(self.expectations_path, _self_hash(value, "expectations_sha256"))

    def resign_expectations(self, update_tree: bool = False) -> None:
        value = json.loads(self.expectations_path.read_text(encoding="utf-8"))
        value.pop("expectations_sha256", None)
        if update_tree:
            tree = qc.tree_binding(self.toolchain)
            value["toolchain_tree"] = {
                "file_count": tree["file_count"], "files_sha256": tree["files_sha256"]
            }
            for name, binding in value["control_bindings"].items():
                path = self.toolchain / binding["relative_path"]
                binding["sha256"] = qc.sha256_file(path)
                binding["size_bytes"] = path.stat().st_size
        value["cases"][0]["coverage_sha256"] = qc.sha256_file(self.coverage_path)
        value["cases"][0]["reader_operation_expectations_file_sha256"] = (
            qc.sha256_file(self.operation_expectations_path)
        )
        value["cases"][0]["reader_operation_expectations_sha256"] = json.loads(
            self.operation_expectations_path.read_text(encoding="utf-8")
        )["reader_operation_expectations_sha256"]
        _write_json(self.expectations_path, _self_hash(value, "expectations_sha256"))

    def audit(self) -> dict[str, Any]:
        return qc.run_audit(
            raw_output_root=self.raw,
            packet_root=self.packets,
            toolchain_root=self.toolchain,
            schema_path=self.toolchain / "schemas" / "case_checklist.schema.json",
            coverage_root=self.coverage,
            case_order_path=self.order_path,
            expectations_path=self.expectations_path,
            expected_count=1,
        )


class FreshDraftQCTest(unittest.TestCase):
    def with_fixture(self, mutation: Callable[[Fixture], None] | None = None) -> dict[str, Any]:
        with tempfile.TemporaryDirectory(prefix="fresh-draft-qc-") as directory:
            fixture = Fixture(Path(directory))
            if mutation is not None:
                mutation(fixture)
            return fixture.audit()

    def test_positive_fixture_passes_without_authorizing_freeze(self) -> None:
        report = self.with_fixture()
        self.assertTrue(report["deterministic_gate_passed"], report["errors"])
        self.assertEqual(report["passed_case_count"], 1)
        self.assertEqual(report["warnings"], [])
        self.assertFalse(report["freeze_authorized"])
        self.assertEqual(len(report["semantic_boundaries_not_claimed"]), 4)

    def assert_tamper_fails(self, mutation: Callable[[Fixture], None]) -> None:
        with tempfile.TemporaryDirectory(prefix="fresh-draft-qc-paired-") as directory:
            fixture = Fixture(Path(directory))
            positive = fixture.audit()
            self.assertTrue(
                positive["deterministic_gate_passed"], positive["errors"]
            )
            mutation(fixture)
            report = fixture.audit()
            self.assertFalse(report["deterministic_gate_passed"])
            self.assertTrue(report["errors"])
            self.assertFalse(report["freeze_authorized"])

    def test_missing_native_decisive_support_fails(self) -> None:
        def mutate(fixture: Fixture) -> None:
            value = json.loads((fixture.case_dir / "checklist.json").read_text())
            value["native"]["decisive_artifacts"][0]["support"] = []
            content = qc.canonical_checklist_json(value)
            (fixture.case_dir / "checklist.json").write_bytes(content)
            (fixture.case_dir / "attempt_01.checklist.json").write_bytes(content)

        self.assert_tamper_fails(mutate)

    def test_forbidden_packet_alias_support_fails(self) -> None:
        def mutate(fixture: Fixture) -> None:
            value = json.loads((fixture.case_dir / "checklist.json").read_text())
            value["native"]["user_goal"]["support"] = ["case_packet.md::L1"]
            content = qc.canonical_checklist_json(value)
            (fixture.case_dir / "checklist.json").write_bytes(content)
            (fixture.case_dir / "attempt_01.checklist.json").write_bytes(content)

        self.assert_tamper_fails(mutate)

    def test_invented_python_symbol_fails(self) -> None:
        def mutate(fixture: Fixture) -> None:
            value = json.loads((fixture.case_dir / "checklist.json").read_text())
            value["native"]["checked_by"]["support"] = [f"{SOURCE_PATH}::CaseAlpha.not_real"]
            content = qc.canonical_checklist_json(value)
            (fixture.case_dir / "checklist.json").write_bytes(content)
            (fixture.case_dir / "attempt_01.checklist.json").write_bytes(content)

        self.assert_tamper_fails(mutate)

    def test_semantically_equal_but_noncanonical_yaml_bytes_fail(self) -> None:
        def mutate(fixture: Fixture) -> None:
            for name in ("checklist.yaml", "attempt_01.checklist.yaml"):
                path = fixture.case_dir / name
                path.write_text(path.read_text(encoding="utf-8") + "# byte tamper\n", encoding="utf-8")

        self.assert_tamper_fails(mutate)

    def test_missing_coverage_chunk_fails_after_valid_resigning(self) -> None:
        def mutate(fixture: Fixture) -> None:
            value = json.loads(fixture.coverage_path.read_text())
            value["raw_official_source_closure"][0]["chunks"] = []
            value.pop("requirements_sha256", None)
            _write_json(fixture.coverage_path, _self_hash(value, "requirements_sha256"))
            fixture.resign_expectations()

        self.assert_tamper_fails(mutate)

    def test_semantic_anchor_may_span_two_contiguous_frozen_chunks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fresh-draft-anchor-span-") as directory:
            fixture = Fixture(Path(directory))
            requirements = json.loads(fixture.coverage_path.read_text(encoding="utf-8"))
            packet = qc.parse_packet(
                fixture.packet_path,
                fixture.packets / CASE_ID,
                CASE_ID,
                TASK_ID,
            )
            source = packet.sources[SOURCE_PATH]
            lines = source.read_bytes().splitlines(keepends=True)
            split = max(1, len(lines) // 2)
            spans = [(1, split), (split + 1, len(lines))]
            closure_row = next(
                row
                for row in requirements["raw_official_source_closure"]
                if row["path"] == SOURCE_PATH
            )
            chunks = []
            replacement_ranges = []
            template_range = next(
                row
                for row in requirements["required_ranges"]
                if row["path"] == SOURCE_PATH
            )
            for index, (start, end) in enumerate(spans):
                snippet = b"".join(lines[start - 1 : end])
                chunks.append(
                    {
                        "start_line": start,
                        "end_line": end,
                        "size_bytes": len(snippet),
                        "snippet_sha256": qc.sha256_bytes(snippet),
                        "snippet_ends_with_newline": snippet.endswith(b"\n"),
                        "planned_reader_envelope_max_bytes": len(snippet) + 100,
                        "planned_reader_envelope_max_o200k_tokens": 100,
                        "chunk_index": index,
                        "chunk_count": 2,
                    }
                )
                replacement_ranges.append(
                    dict(template_range)
                    | {
                        "start_line": start,
                        "end_line": end,
                        "snippet_sha256": qc.sha256_bytes(snippet),
                        "snippet_ends_with_newline": snippet.endswith(b"\n"),
                        "chunk_size_bytes": len(snippet),
                        "chunk_index": index,
                        "chunk_count": 2,
                    }
                )
            closure_row["chunks"] = chunks
            requirements["required_ranges"] = [
                row
                for row in requirements["required_ranges"]
                if row["path"] != SOURCE_PATH
            ] + replacement_ranges
            requirements["required_range_count"] = len(requirements["required_ranges"])
            page = requirements["coverage_pages"][0]
            page["end_range_index_exclusive"] = len(requirements["required_ranges"])
            page["row_count"] = len(requirements["required_ranges"])
            page["max_row_serialized_bytes"] = max(
                len(qc.canonical_bytes(row)) for row in requirements["required_ranges"]
            )
            requirements.pop("requirements_sha256", None)
            requirements["requirements_sha256"] = qc.canonical_sha256(requirements)
            report = qc.validate_coverage(requirements, packet)
            self.assertEqual(report["required_range_count"], 3)

    def test_event_ledger_truncated_read_envelope_fails(self) -> None:
        def mutate(fixture: Fixture) -> None:
            api_path = fixture.case_dir / "api_response.json"
            value = json.loads(api_path.read_text())
            for event in value["codex_cli"]["events"]:
                item = event.get("item") or {}
                if item.get("type") == "command_execution" and item.get("id") == "cmd-003" \
                        and event.get("type") == "item.completed":
                    item["aggregated_output"] = "000001: class CaseAlpha:\n"
            content = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
            api_path.write_bytes(content)
            (fixture.case_dir / "attempt_01.api_response.json").write_bytes(content)

        self.assert_tamper_fails(mutate)

    def test_toolchain_prompt_drift_fails(self) -> None:
        def mutate(fixture: Fixture) -> None:
            (fixture.toolchain / "prompts" / "draft.prompt.md").write_text("tampered prompt\n", encoding="utf-8")

        self.assert_tamper_fails(mutate)

    def test_model_provenance_mismatch_fails(self) -> None:
        def mutate(fixture: Fixture) -> None:
            api_path = fixture.case_dir / "api_response.json"
            value = json.loads(api_path.read_text())
            value["model"] = "wrong-model"
            content = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
            api_path.write_bytes(content)
            (fixture.case_dir / "attempt_01.api_response.json").write_bytes(content)

        self.assert_tamper_fails(mutate)

    def test_unprelocked_codex_privilege_flag_fails(self) -> None:
        def mutate(fixture: Fixture) -> None:
            for name in ("api_response.json", "attempt_01.api_response.json"):
                path = fixture.case_dir / name
                value = json.loads(path.read_text(encoding="utf-8"))
                value["codex_cli"]["command"].insert(
                    -1, "--dangerously-bypass-approvals-and-sandbox"
                )
                path.write_text(
                    json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )

        self.assert_tamper_fails(mutate)

    def test_nonempty_attempt_stderr_fails(self) -> None:
        def mutate(fixture: Fixture) -> None:
            for name in ("stderr.log", "attempt_01.stderr.log"):
                (fixture.case_dir / name).write_text("WARN unexpected\n", encoding="utf-8")

        self.assert_tamper_fails(mutate)

    def test_persisted_numeric_boolean_confusion_fails_closed(self) -> None:
        """Every persisted integer gate preserves the JSON number type."""

        def api_false_returncode(fixture: Fixture) -> None:
            for name in ("api_response.json", "attempt_01.api_response.json"):
                path = fixture.case_dir / name
                value = json.loads(path.read_text(encoding="utf-8"))
                value["codex_cli"]["returncode"] = False
                _write_json(path, value)

        def llm_false_retry_and_temperature(fixture: Fixture) -> None:
            for name in ("llm_call.json", "attempt_01.llm_call.json"):
                path = fixture.case_dir / name
                value = json.loads(path.read_text(encoding="utf-8"))
                value["retry_index"] = False
                value["temperature"] = False
                _write_json(path, value)

        def false_batch_zero_counts(fixture: Fixture) -> None:
            path = fixture.raw / "_batch_summary.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            value["failed_cases"] = False
            value["skipped_cases"] = False
            _write_json(path, value)

        def bool_batch_attempt_fields(fixture: Fixture) -> None:
            path = fixture.raw / "_batch_results.jsonl"
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            rows[0]["attempts"][0]["attempt_index"] = True
            rows[0]["attempts"][0]["returncode"] = False
            path.write_text(
                "".join(
                    json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
                    for row in rows
                ),
                encoding="utf-8",
            )

        def bool_expectation_counts(fixture: Fixture) -> None:
            value = json.loads(
                fixture.expectations_path.read_text(encoding="utf-8")
            )
            value["expected_case_count"] = True
            value["expected_attempt_index"] = True
            value.pop("expectations_sha256", None)
            _write_json(
                fixture.expectations_path,
                _self_hash(value, "expectations_sha256"),
            )

        mutations = {
            "api_returncode_false": api_false_returncode,
            "llm_retry_temperature_false": llm_false_retry_and_temperature,
            "batch_zero_counts_false": false_batch_zero_counts,
            "batch_attempt_bool_fields": bool_batch_attempt_fields,
            "expectation_counts_bool": bool_expectation_counts,
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name):
                self.assert_tamper_fails(mutation)

    def test_real_codex_usage_shape_and_capacity_have_paired_controls(self) -> None:
        with tempfile.TemporaryDirectory(prefix="usage-shape-qc-") as directory:
            fixture = Fixture(Path(directory))
            api = json.loads(
                (fixture.case_dir / "api_response.json").read_text(encoding="utf-8")
            )
            clean_events = api["codex_cli"]["events"]
            expected = {
                "input_tokens": 1000,
                "output_tokens": 200,
                "total_tokens": 1200,
                "input_tokens_details": {"cached_tokens": 100},
                "output_tokens_details": {"reasoning_tokens": 50},
            }
            self.assertEqual(
                qc._validated_actual_usage(
                    clean_events, max_output_tokens=32_000
                ),
                expected,
            )

            def output_over_limit(events: list[dict[str, Any]]) -> None:
                events[-1]["usage"]["output_tokens"] = 32_001

            def boolean_raw_usage(events: list[dict[str, Any]]) -> None:
                events[-1]["usage"]["output_tokens"] = False

            def raw_total_is_not_a_cli_field(events: list[dict[str, Any]]) -> None:
                events[-1]["usage"]["total_tokens"] = 1200

            def total_over_effective_capacity(events: list[dict[str, Any]]) -> None:
                events[-1]["usage"]["input_tokens"] = qc.MAX_CODEX_TOTAL_TOKENS
                events[-1]["usage"]["cached_input_tokens"] = 0
                events[-1]["usage"]["output_tokens"] = 1
                events[-1]["usage"]["reasoning_output_tokens"] = 0

            for name, mutation in {
                "output_32001": output_over_limit,
                "output_false": boolean_raw_usage,
                "raw_total_extra": raw_total_is_not_a_cli_field,
                "derived_total_over_limit": total_over_effective_capacity,
            }.items():
                with self.subTest(name=name):
                    # Paired positive on the same real-CLI-shaped fixture.
                    qc._validated_actual_usage(
                        clean_events, max_output_tokens=32_000
                    )
                    events = copy.deepcopy(clean_events)
                    mutation(events)
                    with self.assertRaises(qc.QCFailure):
                        qc._validated_actual_usage(
                            events, max_output_tokens=32_000
                        )

    def test_consistently_resigned_over_budget_usage_still_fails_full_audit(
        self,
    ) -> None:
        def mutate(fixture: Fixture) -> None:
            normalized: dict[str, Any] | None = None
            for name in ("api_response.json", "attempt_01.api_response.json"):
                path = fixture.case_dir / name
                value = json.loads(path.read_text(encoding="utf-8"))
                events = value["codex_cli"]["events"]
                events[-1]["usage"]["output_tokens"] = 20_001
                normalized = qc._normalized_usage(events)
                value["usage"] = normalized
                _write_json(path, value)
            assert normalized is not None
            for name in ("llm_call.json", "attempt_01.llm_call.json"):
                path = fixture.case_dir / name
                value = json.loads(path.read_text(encoding="utf-8"))
                value["token_usage"] = qc._token_usage(normalized)
                _write_json(path, value)

        self.assert_tamper_fails(mutate)

    def test_json_yaml_selectors_and_line_spans_are_exact(self) -> None:
        with tempfile.TemporaryDirectory(prefix="selector-qc-") as directory:
            root = Path(directory)
            json_path = root / "value.json"
            yaml_path = root / "value.yaml"
            text_path = root / "value.txt"
            _write_json(json_path, {"items": [{"name": "kept"}]})
            yaml_path.write_text("items:\n  - name: kept\n", encoding="utf-8")
            text_path.write_text("meaningful line\n", encoding="utf-8")
            self.assertEqual(
                qc.resolve_selector("official/value.json", json_path, "/items/0/name")["kind"],
                "json_yaml_selector",
            )
            self.assertEqual(
                qc.resolve_selector("official/value.yaml", yaml_path, "$.items[0].name")["kind"],
                "json_yaml_selector",
            )
            self.assertEqual(
                qc.resolve_selector("official/value.txt", text_path, "L1")["kind"],
                "line_span",
            )
            with self.assertRaises(qc.QCFailure):
                qc.resolve_selector("official/value.json", json_path, "$.items[2].name")
            with self.assertRaises(qc.QCFailure):
                qc.resolve_selector("official/value.txt", text_path, "L2")


if __name__ == "__main__":
    unittest.main()
