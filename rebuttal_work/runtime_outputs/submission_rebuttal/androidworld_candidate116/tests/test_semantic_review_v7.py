#!/usr/bin/env python3
"""Hermetic positive and fault-injection tests for semantic review v7."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from typing import Any, Mapping

CANDIDATE = Path(__file__).resolve().parents[1]
REPOSITORY = CANDIDATE.parents[3]
sys.path.insert(0, str(CANDIDATE / "scripts"))

import semantic_review_v7_staging as review_staging  # noqa: E402
import wave004_v6_clean2_hardened_staging as source_staging  # noqa: E402
from semantic_review_v7_common import (  # noqa: E402
    DIMENSION_IDS,
    SemanticReviewV7Error,
    canonical_sha256,
    checklist_semantic_inventory,
    covered_line_spans_from_requirements,
    is_exact_int,
    sha256_text,
    validate_review_body,
)

sys.dont_write_bytecode = True


def make_checklist(source_pointer: str) -> dict[str, Any]:
    support = [source_pointer]
    return {
        "schema_version": "case_checklist_v1",
        "case_unit_id": "SystemCopyToClipboard",
        "domain": "androidworld",
        "task_id": "SystemCopyToClipboard",
        "native": {
            "user_goal": {
                "text": "Copy the generated value to the Android clipboard.",
                "support": support,
            },
            "benchmark_success": {
                "text": "The released evaluator returns a successful native result.",
                "support": support,
            },
            "checked_by": {
                "text": "The runtime evaluator checks the retained Android state.",
                "support": support,
            },
            "decisive_artifacts": [
                {
                    "artifact": "Retained evaluator input and Android clipboard state",
                    "question": "Does the retained state equal the generated expected clipboard value?",
                    "support": support,
                }
            ],
            "success_if": [
                {
                    "text": "The evaluator and runner jointly establish native success.",
                    "support": support,
                }
            ],
            "fail_if": [
                {
                    "text": "The retained state establishes that the native evaluator rejects the run.",
                    "support": support,
                }
            ],
            "undecided_if": [
                {
                    "text": "Required retained evidence is absent or contradictory, so outcome is unestablished.",
                    "support": support,
                }
            ],
        },
        "stronger": {
            "additional_conditions": [
                {
                    "id": "retained_clipboard_trace",
                    "text": "Retained trace evidence directly records the clipboard-changing action.",
                    "rationale": "This measures a source-defined goal detail beyond the native end-state check.",
                    "decisive_artifacts": [
                        {
                            "artifact": "Retained action and observation trace",
                            "question": "Does the trace show the source-defined clipboard-changing action?",
                            "support": support,
                        }
                    ],
                    "support": support,
                }
            ]
        },
    }


def event_pair(
    index: int, operation: Mapping[str, Any], output: str
) -> list[dict[str, Any]]:
    item_id = f"cmd-{index:04d}"
    common = {
        "id": item_id,
        "type": "command_execution",
        "command": operation["exact_command"],
    }
    return [
        {
            "type": "item.started",
            "item": {
                **common,
                "status": "in_progress",
                "exit_code": None,
                "aggregated_output": "",
            },
        },
        {
            "type": "item.completed",
            "item": {
                **common,
                "status": "completed",
                "exit_code": 0,
                "aggregated_output": output,
            },
        },
    ]


class SemanticReviewV7Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        index = json.loads(
            (
                CANDIDATE / "indexes" / "androidworld_candidate116_packet_index.json"
            ).read_text(encoding="utf-8")
        )
        row = next(
            item
            for item in index["items"]
            if item["case_unit_id"] == "SystemCopyToClipboard"
        )
        cls.packet_path = REPOSITORY / row["case_packet_path"]
        cls.packet_text = cls.packet_path.read_text(encoding="utf-8")
        cls.parsed = source_staging.parse_packet_sources(cls.packet_text)
        tokenizer_root = (
            CANDIDATE / "draft_generation" / "tokenizer" / "tiktoken_0_12_0_py312"
        )
        token_counter, cls.tokenizer_binding = (
            source_staging.load_frozen_o200k_token_counter(
                tokenizer_root=tokenizer_root,
                merge_table_path=tokenizer_root
                / "encoding_cache"
                / "fb374d419588a4632f3f557e76b4b70aebbca790",
            )
        )
        cls.token_counter = staticmethod(token_counter)
        cls.requirements = source_staging.build_coverage_requirements(
            cls.parsed,
            token_counter=cls.token_counter,
            tokenizer_binding=cls.tokenizer_binding,
        )
        cls.requirements["case_packet_sha256"] = sha256_text(cls.packet_text)
        cls.requirements["source_inventory"] = [
            {
                key: cls.parsed["sources"][path][key]
                for key in ("path", "sha256", "size_bytes", "line_count")
            }
            for path in cls.parsed["inventory"]
        ]
        cls.requirements.pop("requirements_sha256", None)
        cls.requirements["requirements_sha256"] = canonical_sha256(cls.requirements)
        cls.packet_expectations = source_staging.build_reader_operation_expectations(
            case_packet_text=cls.packet_text,
            parsed=cls.parsed,
            requirements=cls.requirements,
            token_counter=cls.token_counter,
        )
        source_staging.verify_reader_operation_expectations_binding(
            cls.requirements, cls.packet_expectations
        )
        source_path = next(
            path for path in cls.parsed["inventory"] if path.startswith("official/")
        )
        cls.checklist = make_checklist(f"{source_path}::L1")
        cls.checklist_text = (
            json.dumps(cls.checklist, ensure_ascii=False, indent=2) + "\n"
        )
        cls.inventory = checklist_semantic_inventory(cls.checklist)
        cls.review_expectations = review_staging.build_review_operation_expectations(
            packet_operation_expectations=cls.packet_expectations,
            requirements=cls.requirements,
            checklist_text=cls.checklist_text,
            inventory=cls.inventory,
            token_counter=cls.token_counter,
        )
        cls.output_schema = json.loads(
            (
                CANDIDATE
                / "schemas"
                / "androidworld_candidate116_semantic_review_v7.schema.json"
            ).read_text(encoding="utf-8")
        )
        cls.raw_sources = {
            path: {
                "sha256": cls.parsed["sources"][path]["sha256"],
                "line_count": cls.parsed["sources"][path]["line_count"],
            }
            for path in cls.parsed["inventory"]
        }
        cls.evidence_path = source_path
        cls.covered = covered_line_spans_from_requirements(cls.requirements)
        cls.events = cls.build_events()

    @classmethod
    def packet_output(cls, operation: Mapping[str, Any]) -> str:
        kind = operation["kind"]
        identity = operation["semantic_identity"]
        if kind == "overview":
            return source_staging.render_overview_output_for_audit(cls.requirements)
        if kind == "header":
            marker = "## Packet Source Files\n"
            header = cls.packet_text.split(marker, 1)[0]
            return source_staging.render_header_output_for_audit(
                header_text=header,
                case_packet_sha256=cls.requirements["case_packet_sha256"],
                requirements_sha256=cls.requirements["requirements_sha256"],
            )
        if kind == "plan-page":
            return source_staging.render_plan_page_output_for_audit(
                page_index=identity["page_index"], requirements=cls.requirements
            )
        if kind == "read":
            row = cls.requirements["required_ranges"][identity["range_index"]]
            return source_staging.render_read_output_for_audit(
                row=row,
                source_text=cls.parsed["sources"][row["path"]]["text"],
                requirements_sha256=cls.requirements["requirements_sha256"],
            )
        raise AssertionError(kind)

    @classmethod
    def build_events(cls) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = [
            {"type": "thread.started", "thread_id": "test-thread"},
            {"type": "turn.started"},
        ]
        for index, operation in enumerate(cls.packet_expectations["operations"]):
            events.extend(event_pair(index, operation, cls.packet_output(operation)))
        checklist_operation = cls.review_expectations["checklist_operation"]
        checklist_output = review_staging.render_checklist_output_for_audit(
            checklist_text=cls.checklist_text,
            inventory=cls.inventory,
            requirements_sha256=cls.requirements["requirements_sha256"],
        )
        events.extend(
            event_pair(
                len(cls.packet_expectations["operations"]),
                checklist_operation,
                checklist_output,
            )
        )
        events.append(
            {
                "type": "item.completed",
                "item": {
                    "id": "agent-final",
                    "type": "agent_message",
                    "text": json.dumps(
                        cls.accept_body(),
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                },
            }
        )
        events.append(
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 120_000,
                    "cached_input_tokens": 0,
                    "output_tokens": 12_000,
                    "reasoning_output_tokens": 8_000,
                },
            }
        )
        return events

    @classmethod
    def accept_body(cls) -> dict[str, Any]:
        evidence = [
            {
                "path": cls.evidence_path,
                "line_start": 1,
                "line_end": 1,
                "evidence_role": "This exact raw line anchors the case-specific source assessment.",
            }
        ]
        dimensions = [
            {
                "dimension_id": dimension,
                "status": "pass",
                "assessment": f"SystemCopyToClipboard case-specific source analysis passes {dimension} without broadening semantics.",
                "checklist_pointers": ["/native/user_goal/text"],
                "source_evidence": copy.deepcopy(evidence),
                "finding_ids": [],
            }
            for dimension in DIMENSION_IDS
        ]
        claims = [
            {
                "checklist_pointer": row["checklist_pointer"],
                "text_sha256": row["text_sha256"],
                "status": "pass",
                "assessment": "The complete case-specific claim is materially and narrowly entailed by the cited runtime source.",
                "source_evidence": copy.deepcopy(evidence),
                "finding_ids": [],
            }
            for row in cls.inventory["claims"]
        ]
        supports = [
            {
                "support_pointer": row["support_pointer"],
                "source_pointer": row["source_pointer"],
                "target_claim_pointers": row["target_claim_pointers"],
                "status": "pass",
                "entailment": "This support occurrence materially entails every listed target clause through the cited runtime behavior.",
                "source_evidence": copy.deepcopy(evidence),
                "finding_ids": [],
            }
            for row in cls.inventory["support_occurrences"]
        ]
        return {
            "verdict": "accept",
            "dimension_audits": dimensions,
            "claim_audits": claims,
            "support_audits": supports,
            "blocking_findings": [],
        }

    def validate_body(
        self, body: Mapping[str, Any], *, covered: Any = None
    ) -> dict[str, Any]:
        return validate_review_body(
            body,
            schema=self.output_schema,
            checklist=self.checklist,
            inventory=self.inventory,
            raw_sources=self.raw_sources,
            require_accept=False,
            covered_line_spans=self.covered if covered is None else covered,
        )

    def receipt(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        return review_staging.combined_coverage_receipt_from_events(
            events=events,
            requirements=self.requirements,
            packet_operation_expectations=self.packet_expectations,
            review_operation_expectations=self.review_expectations,
            checklist_text=self.checklist_text,
            inventory=self.inventory,
            expected_final_body=self.accept_body(),
            token_counter=self.token_counter,
        )

    def assert_positive_receipt_baseline(self) -> None:
        receipt = self.receipt(copy.deepcopy(self.events))
        self.assertEqual(receipt["additional_command_count"], 0)
        self.assertEqual(
            receipt["source_coverage_receipt"]["status"],
            "all_required_reader_operations_completed",
        )

    def assert_positive_accept_body_baseline(self) -> None:
        self.assertEqual(self.validate_body(self.accept_body())["verdict"], "accept")

    def closed_reject_body(self) -> dict[str, Any]:
        body = self.accept_body()
        body["verdict"] = "reject"
        body["claim_audits"][0]["status"] = "fail"
        body["claim_audits"][0]["finding_ids"] = ["F001"]
        body["blocking_findings"] = [self.finding("F001")]
        return body

    def assert_positive_closed_reject_baseline(self) -> None:
        self.assertEqual(
            self.validate_body(self.closed_reject_body())["verdict"], "reject"
        )

    def test_positive_complete_receipt(self) -> None:
        receipt = self.receipt(copy.deepcopy(self.events))
        self.assertEqual(receipt["additional_command_count"], 0)
        self.assertEqual(
            receipt["source_coverage_receipt"]["status"],
            "all_required_reader_operations_completed",
        )
        checklist_operation = self.review_expectations["checklist_operation"]
        self.assertEqual(
            checklist_operation["exact_command"],
            source_staging.render_codex_event_command(checklist_operation["argv"]),
        )
        self.assertEqual(
            self.review_expectations["event_trust_policy"],
            source_staging.exact_event_trust_policy(),
        )

    def test_bool_is_never_an_exact_persisted_integer(self) -> None:
        self.assertTrue(is_exact_int(0, expected=0))
        self.assertTrue(is_exact_int(116, expected=116))
        self.assertFalse(is_exact_int(False, expected=0))
        self.assertFalse(is_exact_int(True, expected=1))

    def test_positive_accept_body_exact_inventory(self) -> None:
        result = self.validate_body(self.accept_body())
        self.assertEqual(result["verdict"], "accept")
        self.assertEqual(result["claim_count"], self.inventory["claim_count"])
        self.assertEqual(
            result["support_occurrence_count"],
            self.inventory["support_occurrence_count"],
        )

    def test_schema_closes_every_object_shape(self) -> None:
        object_shapes: list[tuple[str, Mapping[str, Any]]] = []

        def collect(value: Any, pointer: str) -> None:
            if isinstance(value, Mapping):
                if value.get("type") == "object":
                    object_shapes.append((pointer, value))
                for key, child in value.items():
                    collect(child, f"{pointer}/{key}")
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    collect(child, f"{pointer}/{index}")

        collect(self.output_schema, "")
        self.assertGreaterEqual(len(object_shapes), 6)
        for pointer, shape in object_shapes:
            with self.subTest(pointer=pointer):
                self.assertIs(shape.get("additionalProperties"), False)

    def test_body_rejects_extra_field_at_every_nested_object_level(self) -> None:
        accept_mutations = (
            ("top", lambda body: body.__setitem__("unexpected", True)),
            (
                "dimension",
                lambda body: body["dimension_audits"][0].__setitem__(
                    "unexpected", True
                ),
            ),
            (
                "dimension_evidence",
                lambda body: body["dimension_audits"][0]["source_evidence"][
                    0
                ].__setitem__("unexpected", True),
            ),
            (
                "claim",
                lambda body: body["claim_audits"][0].__setitem__(
                    "unexpected", True
                ),
            ),
            (
                "support",
                lambda body: body["support_audits"][0].__setitem__(
                    "unexpected", True
                ),
            ),
        )
        for label, mutate in accept_mutations:
            with self.subTest(level=label):
                self.assert_positive_accept_body_baseline()
                body = self.accept_body()
                mutate(body)
                with self.assertRaises(SemanticReviewV7Error):
                    self.validate_body(body)

        with self.subTest(level="blocking_finding"):
            self.assert_positive_closed_reject_baseline()
            body = self.closed_reject_body()
            body["blocking_findings"][0]["unexpected"] = True
            with self.assertRaises(SemanticReviewV7Error):
                self.validate_body(body)

    def test_receipt_rejects_reordered_commands(self) -> None:
        self.assert_positive_receipt_baseline()
        events = copy.deepcopy(self.events)
        first = events[2:4]
        second = events[4:6]
        events[2:6] = second + first
        with self.assertRaises(SemanticReviewV7Error):
            self.receipt(events)

    def test_receipt_rejects_shell_chain(self) -> None:
        for suffix in (
            " && true",
            " | /usr/bin/tee /dev/null",
            " $(/usr/bin/true)",
            " `/usr/bin/true`",
        ):
            with self.subTest(suffix=suffix):
                self.assert_positive_receipt_baseline()
                events = copy.deepcopy(self.events)
                events[2]["item"]["command"] += suffix
                events[3]["item"]["command"] += suffix
                with self.assertRaises(SemanticReviewV7Error):
                    self.receipt(events)

    def test_receipt_rejects_bare_checklist_event_command(self) -> None:
        self.assert_positive_receipt_baseline()
        events = copy.deepcopy(self.events)
        semantic = self.review_expectations["checklist_operation"]["semantic_command"]
        events[-4]["item"]["command"] = semantic
        events[-3]["item"]["command"] = semantic
        with self.assertRaises(SemanticReviewV7Error):
            self.receipt(events)

    def test_receipt_rejects_double_wrapped_checklist_event_command(self) -> None:
        self.assert_positive_receipt_baseline()
        events = copy.deepcopy(self.events)
        exact = self.review_expectations["checklist_operation"]["exact_command"]
        doubled = f'/bin/zsh -lc "{exact}"'
        events[-4]["item"]["command"] = doubled
        events[-3]["item"]["command"] = doubled
        with self.assertRaises(SemanticReviewV7Error):
            self.receipt(events)

    def test_receipt_rejects_boolean_exit_code(self) -> None:
        self.assert_positive_receipt_baseline()
        events = copy.deepcopy(self.events)
        events[3]["item"]["exit_code"] = False
        with self.assertRaises(SemanticReviewV7Error):
            self.receipt(events)

    def test_receipt_rejects_cross_id_started_completed_pair(self) -> None:
        self.assert_positive_receipt_baseline()
        events = copy.deepcopy(self.events)
        events[3]["item"]["id"] = "cross-id-completion"
        with self.assertRaises(SemanticReviewV7Error):
            self.receipt(events)

    def test_receipt_rejects_missing_started_event(self) -> None:
        self.assert_positive_receipt_baseline()
        events = copy.deepcopy(self.events)
        del events[2]
        with self.assertRaises(SemanticReviewV7Error):
            self.receipt(events)

    def test_receipt_rejects_duplicate_event_id(self) -> None:
        self.assert_positive_receipt_baseline()
        events = copy.deepcopy(self.events)
        events[4]["item"]["id"] = events[2]["item"]["id"]
        events[5]["item"]["id"] = events[2]["item"]["id"]
        with self.assertRaises(SemanticReviewV7Error):
            self.receipt(events)

    def test_receipt_rejects_failed_command(self) -> None:
        self.assert_positive_receipt_baseline()
        events = copy.deepcopy(self.events)
        events[3]["item"]["status"] = "failed"
        events[3]["item"]["exit_code"] = 1
        with self.assertRaises(SemanticReviewV7Error):
            self.receipt(events)

    def test_receipt_rejects_truncated_output(self) -> None:
        self.assert_positive_receipt_baseline()
        events = copy.deepcopy(self.events)
        events[3]["item"]["aggregated_output"] = events[3]["item"]["aggregated_output"][
            :-20
        ]
        with self.assertRaises(SemanticReviewV7Error):
            self.receipt(events)

    def test_agent_message_marker_cannot_substitute_for_reader(self) -> None:
        self.assert_positive_receipt_baseline()
        events = copy.deepcopy(self.events)
        del events[2:4]
        events.insert(
            2,
            {
                "type": "item.completed",
                "item": {
                    "id": "spoof-agent",
                    "type": "agent_message",
                    "text": "WAVE004_READER_COMPLETE {} SEMANTIC_REVIEW_V7_READER_COMPLETE {}",
                },
            },
        )
        with self.assertRaises(SemanticReviewV7Error):
            self.receipt(events)

    def test_receipt_rejects_extra_command(self) -> None:
        self.assert_positive_receipt_baseline()
        events = copy.deepcopy(self.events)
        operation = self.review_expectations["checklist_operation"]
        output = review_staging.render_checklist_output_for_audit(
            checklist_text=self.checklist_text,
            inventory=self.inventory,
            requirements_sha256=self.requirements["requirements_sha256"],
        )
        events[-2:-2] = event_pair(9999, operation, output)
        with self.assertRaises(SemanticReviewV7Error):
            self.receipt(events)

    def test_receipt_rejects_checklist_body_tamper(self) -> None:
        self.assert_positive_receipt_baseline()
        events = copy.deepcopy(self.events)
        checklist_completed = events[-3]
        checklist_completed["item"]["aggregated_output"] = checklist_completed["item"][
            "aggregated_output"
        ].replace("generated value", "tampered value", 1)
        with self.assertRaises(SemanticReviewV7Error):
            self.receipt(events)

    def test_receipt_rejects_packet_B_tamper(self) -> None:
        self.assert_positive_receipt_baseline()
        expectations = copy.deepcopy(self.packet_expectations)
        expectations["operations"][0]["exact_command"] += " --bad"
        with self.assertRaises(SemanticReviewV7Error):
            review_staging.combined_coverage_receipt_from_events(
                events=copy.deepcopy(self.events),
                requirements=self.requirements,
                packet_operation_expectations=expectations,
                review_operation_expectations=self.review_expectations,
                checklist_text=self.checklist_text,
                inventory=self.inventory,
                expected_final_body=self.accept_body(),
                token_counter=self.token_counter,
            )

    def test_receipt_rejects_resigned_boolean_packet_operation_index(self) -> None:
        self.assert_positive_receipt_baseline()
        expectations = copy.deepcopy(self.packet_expectations)
        expectations["operations"][0]["operation_index"] = False
        operation = expectations["operations"][0]
        operation_core = dict(operation)
        operation_core.pop("operation_sha256", None)
        operation["operation_sha256"] = canonical_sha256(operation_core)
        expectations["operations_sha256"] = canonical_sha256(expectations["operations"])
        expectations_core = dict(expectations)
        expectations_core.pop("reader_operation_expectations_sha256", None)
        expectations["reader_operation_expectations_sha256"] = canonical_sha256(
            expectations_core
        )
        with self.assertRaises(SemanticReviewV7Error):
            review_staging.combined_coverage_receipt_from_events(
                events=copy.deepcopy(self.events),
                requirements=self.requirements,
                packet_operation_expectations=expectations,
                review_operation_expectations=self.review_expectations,
                checklist_text=self.checklist_text,
                inventory=self.inventory,
                expected_final_body=self.accept_body(),
                token_counter=self.token_counter,
            )

    def test_receipt_rejects_resigned_extra_review_expectation_key(self) -> None:
        self.assert_positive_receipt_baseline()
        expectations = copy.deepcopy(self.review_expectations)
        expectations["legacy_policy"] = True
        expectations.pop("review_operation_expectations_sha256", None)
        expectations["review_operation_expectations_sha256"] = canonical_sha256(
            expectations
        )
        with self.assertRaises(SemanticReviewV7Error):
            review_staging.combined_coverage_receipt_from_events(
                events=copy.deepcopy(self.events),
                requirements=self.requirements,
                packet_operation_expectations=self.packet_expectations,
                review_operation_expectations=expectations,
                checklist_text=self.checklist_text,
                inventory=self.inventory,
                expected_final_body=self.accept_body(),
                token_counter=self.token_counter,
            )

    def test_receipt_rejects_packet_A_tamper(self) -> None:
        self.assert_positive_receipt_baseline()
        requirements = copy.deepcopy(self.requirements)
        requirements["required_range_count"] += 1
        with self.assertRaises(SemanticReviewV7Error):
            review_staging.combined_coverage_receipt_from_events(
                events=copy.deepcopy(self.events),
                requirements=requirements,
                packet_operation_expectations=self.packet_expectations,
                review_operation_expectations=self.review_expectations,
                checklist_text=self.checklist_text,
                inventory=self.inventory,
                expected_final_body=self.accept_body(),
                token_counter=self.token_counter,
            )

    def test_body_rejects_dimension_reorder(self) -> None:
        self.assert_positive_accept_body_baseline()
        body = self.accept_body()
        body["dimension_audits"][0], body["dimension_audits"][1] = (
            body["dimension_audits"][1],
            body["dimension_audits"][0],
        )
        with self.assertRaises(SemanticReviewV7Error):
            self.validate_body(body)

    def test_body_rejects_duplicate_dimension(self) -> None:
        self.assert_positive_accept_body_baseline()
        body = self.accept_body()
        body["dimension_audits"][1]["dimension_id"] = body["dimension_audits"][0][
            "dimension_id"
        ]
        with self.assertRaises(SemanticReviewV7Error):
            self.validate_body(body)

    def test_body_rejects_missing_claim(self) -> None:
        self.assert_positive_accept_body_baseline()
        body = self.accept_body()
        body["claim_audits"].pop()
        with self.assertRaises(SemanticReviewV7Error):
            self.validate_body(body)

    def test_body_rejects_reordered_support_occurrences(self) -> None:
        self.assert_positive_accept_body_baseline()
        body = self.accept_body()
        body["support_audits"][0], body["support_audits"][1] = (
            body["support_audits"][1],
            body["support_audits"][0],
        )
        with self.assertRaises(SemanticReviewV7Error):
            self.validate_body(body)

    def test_body_rejects_accept_with_failed_audit(self) -> None:
        self.assert_positive_accept_body_baseline()
        body = self.accept_body()
        body["claim_audits"][0]["status"] = "fail"
        with self.assertRaises(SemanticReviewV7Error):
            self.validate_body(body)

    def test_body_rejects_accept_with_finding(self) -> None:
        self.assert_positive_accept_body_baseline()
        body = self.accept_body()
        body["blocking_findings"] = [self.finding("F001")]
        with self.assertRaises(SemanticReviewV7Error):
            self.validate_body(body)

    def finding(self, finding_id: str) -> dict[str, Any]:
        return {
            "finding_id": finding_id,
            "category": "native_misstatement_or_omission",
            "checklist_pointers": ["/native/user_goal/text"],
            "source_evidence": [
                {
                    "path": self.evidence_path,
                    "line_start": 1,
                    "line_end": 1,
                    "evidence_role": "The raw runtime line establishes this blocking semantic mismatch.",
                }
            ],
            "blocking_explanation": "The case-specific checklist statement materially conflicts with the released runtime source.",
        }

    def test_body_accepts_closed_reject(self) -> None:
        body = self.accept_body()
        body["verdict"] = "reject"
        body["claim_audits"][0]["status"] = "fail"
        body["claim_audits"][0]["finding_ids"] = ["F001"]
        body["blocking_findings"] = [self.finding("F001")]
        self.assertEqual(self.validate_body(body)["verdict"], "reject")

    def test_body_rejects_orphan_finding(self) -> None:
        self.assert_positive_closed_reject_baseline()
        body = self.accept_body()
        body["verdict"] = "reject"
        body["claim_audits"][0]["status"] = "fail"
        body["claim_audits"][0]["finding_ids"] = ["F001"]
        body["blocking_findings"] = [self.finding("F001"), self.finding("F002")]
        with self.assertRaises(SemanticReviewV7Error):
            self.validate_body(body)

    def test_body_rejects_noncontinuous_finding_ids(self) -> None:
        self.assert_positive_closed_reject_baseline()
        body = self.accept_body()
        body["verdict"] = "reject"
        body["claim_audits"][0]["status"] = "fail"
        body["claim_audits"][0]["finding_ids"] = ["F002"]
        body["blocking_findings"] = [self.finding("F002")]
        with self.assertRaises(SemanticReviewV7Error):
            self.validate_body(body)

    def test_body_rejects_noninventory_evidence_path(self) -> None:
        self.assert_positive_accept_body_baseline()
        body = self.accept_body()
        body["dimension_audits"][0]["source_evidence"][0]["path"] = (
            "official/not/in/inventory.py"
        )
        with self.assertRaises(SemanticReviewV7Error):
            self.validate_body(body)

    def test_body_rejects_empty_evidence(self) -> None:
        self.assert_positive_accept_body_baseline()
        body = self.accept_body()
        body["support_audits"][0]["source_evidence"] = []
        with self.assertRaises(SemanticReviewV7Error):
            self.validate_body(body)

    def test_body_rejects_blank_evidence_role(self) -> None:
        self.assert_positive_accept_body_baseline()
        body = self.accept_body()
        body["dimension_audits"][0]["source_evidence"][0]["evidence_role"] = "   "
        with self.assertRaises(SemanticReviewV7Error):
            self.validate_body(body)

    def test_body_rejects_out_of_range_evidence(self) -> None:
        self.assert_positive_accept_body_baseline()
        body = self.accept_body()
        body["claim_audits"][0]["source_evidence"][0]["line_end"] = 99999999
        with self.assertRaises(SemanticReviewV7Error):
            self.validate_body(body)

    def test_body_rejects_span_not_fully_frozen_read(self) -> None:
        self.assert_positive_accept_body_baseline()
        body = self.accept_body()
        incomplete = copy.deepcopy(self.covered)
        incomplete[self.evidence_path] = []
        with self.assertRaises(SemanticReviewV7Error):
            self.validate_body(body, covered=incomplete)


if __name__ == "__main__":
    unittest.main()
