#!/usr/bin/env python3
"""Cross-check frozen staging and independent QC against A+B/v2 tampering.

The production QC implementation never imports the staging module.  This test
imports both only to submit the same adversarial ledgers to each verifier and
to require two independent rejections.
"""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from typing import Any, Callable

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
for directory in (SCRIPTS_DIR, TESTS_DIR):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import strict_fresh_draft_postgen_qc as qc  # noqa: E402
import wave004_v6_clean2_hardened_staging as staging  # noqa: E402


FINAL_JSON_TEXT = json.dumps(
    {"native": {}, "stronger": {}},
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
)
THREAD_STARTED_EVENT = {"type": "thread.started", "thread_id": "thread-fixture"}
TURN_STARTED_EVENT = {"type": "turn.started"}
FINAL_AGENT_EVENT = {
    "type": "item.completed",
    "item": {
        "id": "agent-final",
        "type": "agent_message",
        "text": FINAL_JSON_TEXT,
    },
}
TURN_COMPLETED_EVENT = {
    "type": "turn.completed",
    "usage": {
        "input_tokens": 1,
        "cached_input_tokens": 0,
        "output_tokens": 1,
        "reasoning_output_tokens": 0,
    },
}
REASONING_EVENT = {
    "type": "item.completed",
    "item": {
        "id": "reasoning-fixture",
        "type": "reasoning",
        "text": "bounded reader plan",
    },
}


def _command_pairs(events: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    commands = [
        copy.deepcopy(event)
        for event in events
        if isinstance(event.get("item"), dict)
        and event["item"].get("type") == "command_execution"
    ]
    if len(commands) % 2:
        raise AssertionError("fixture command event count is not paired")
    return [commands[index : index + 2] for index in range(0, len(commands), 2)]


def _flatten(pairs: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        copy.deepcopy(THREAD_STARTED_EVENT),
        copy.deepcopy(TURN_STARTED_EVENT),
        *(event for pair in pairs for event in pair),
        copy.deepcopy(FINAL_AGENT_EVENT),
        copy.deepcopy(TURN_COMPLETED_EVENT),
    ]


def _resign_receipt(receipt: dict[str, Any]) -> None:
    receipt.pop("coverage_receipt_sha256", None)
    receipt["coverage_receipt_sha256"] = qc.canonical_sha256(receipt)


def _resign_operations(
    expectations: dict[str, Any], operation_indexes: list[int] | tuple[int, ...] = ()
) -> None:
    """Re-sign a deliberately altered Layer-B document from the leaves out."""

    for index in operation_indexes:
        operation = expectations["operations"][index]
        operation.pop("operation_sha256", None)
        operation["operation_sha256"] = qc.canonical_sha256(operation)
    expectations["operations_sha256"] = qc.canonical_sha256(
        expectations["operations"]
    )
    expectations.pop("reader_operation_expectations_sha256", None)
    expectations["reader_operation_expectations_sha256"] = qc.canonical_sha256(
        expectations
    )


def _terminal_parts(output: str) -> tuple[str, dict[str, Any]]:
    marker = "\n" + qc.READER_COMPLETION_PREFIX
    start = output.rfind(marker)
    if start < 0:
        raise AssertionError("fixture output lacks completion marker")
    body = output[: start + 1]
    completion = json.loads(output[start + len(marker) : -1])
    return body, completion


def _replace_terminal(output: str, completion: dict[str, Any]) -> str:
    body, _ = _terminal_parts(output)
    return body + qc.READER_COMPLETION_PREFIX + json.dumps(
        completion, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ) + "\n"


class ABV2ReaderProtocolFaultTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        candidate_root = TESTS_DIR.parent
        packet_paths = sorted(
            (candidate_root / "case_packets" / "androidworld").glob(
                "*/case_packet.md"
            )
        )
        if len(packet_paths) != 116:
            raise AssertionError(
                f"expected 116 canonical packets, found {len(packet_paths)}"
            )
        cls.packet_path = packet_paths[0]
        cls.packet_text = cls.packet_path.read_text(encoding="utf-8")
        cls.parsed = staging.parse_packet_sources(cls.packet_text)
        tokenizer_root = (
            candidate_root
            / "draft_generation"
            / "tokenizer"
            / "tiktoken_0_12_0_py312"
        )
        token_counter, tokenizer_binding = staging.load_frozen_o200k_token_counter(
            tokenizer_root=tokenizer_root,
            merge_table_path=(
                tokenizer_root
                / "encoding_cache"
                / "fb374d419588a4632f3f557e76b4b70aebbca790"
            ),
        )
        cls.token_counter = staticmethod(token_counter)
        cls.requirements = staging.build_coverage_requirements(
            cls.parsed,
            token_counter=cls.token_counter,
            tokenizer_binding=tokenizer_binding,
        )
        cls.requirements["case_packet_sha256"] = staging.sha256_text(
            cls.packet_text
        )
        cls.requirements["source_inventory"] = [
            {
                key: cls.parsed["sources"][path][key]
                for key in ("path", "sha256", "size_bytes", "line_count")
            }
            for path in cls.parsed["inventory"]
        ]
        cls.requirements.pop("requirements_sha256", None)
        cls.requirements["requirements_sha256"] = staging.canonical_sha256(
            cls.requirements
        )
        cls.operations = staging.build_reader_operation_expectations(
            case_packet_text=cls.packet_text,
            parsed=cls.parsed,
            requirements=cls.requirements,
            token_counter=cls.token_counter,
        )
        header = cls.packet_text.split("## Packet Source Files\n", 1)[0]
        outputs = [
            staging.render_overview_output_for_audit(cls.requirements),
            staging.render_header_output_for_audit(
                header_text=header,
                case_packet_sha256=cls.requirements["case_packet_sha256"],
                requirements_sha256=cls.requirements["requirements_sha256"],
            ),
        ]
        outputs.extend(
            staging.render_plan_page_output_for_audit(
                page_index=index, requirements=cls.requirements
            )
            for index in range(cls.requirements["coverage_page_count"])
        )
        outputs.extend(
            staging.render_read_output_for_audit(
                row=row,
                source_text=cls.parsed["sources"][row["path"]]["text"],
                requirements_sha256=cls.requirements["requirements_sha256"],
            )
            for row in cls.requirements["required_ranges"]
        )
        command_pairs: list[list[dict[str, Any]]] = []
        for index, (operation, output) in enumerate(
            zip(cls.operations["operations"], outputs, strict=True)
        ):
            item = {
                "id": f"cmd-{index:04d}",
                "type": "command_execution",
                "command": operation["exact_command"],
            }
            command_pairs.append(
                [
                    {
                        "type": "item.started",
                        "item": {
                            **item,
                            "status": "in_progress",
                            "exit_code": None,
                            "aggregated_output": "",
                        },
                    },
                    {
                        "type": "item.completed",
                        "item": {
                            **item,
                            "status": "completed",
                            "exit_code": 0,
                            "aggregated_output": output,
                        },
                    },
                ]
            )
        cls.events = _flatten(command_pairs)
        cls.receipt = staging.coverage_receipt_from_events(
            cls.events, cls.requirements, cls.operations
        )
        case_id = str(cls.requirements["case_unit_id"])
        task_id = str(cls.requirements["task_id"])
        packet_root = candidate_root / "case_packets" / "androidworld"
        cls.packet = qc.parse_packet(
            cls.packet_path,
            packet_root / case_id,
            case_id,
            task_id,
        )

    def _assert_both_accept(
        self,
        events: list[dict[str, Any]],
        receipt: dict[str, Any],
        operations: dict[str, Any] | None = None,
    ) -> None:
        operations = operations or self.operations
        staging.verify_coverage_receipt_against_events(
            receipt, events, self.requirements, operations
        )
        qc.verify_event_ledger(
            events,
            self.requirements,
            operations,
            receipt,
            self.packet,
        )

    def _assert_both_reject(
        self,
        *,
        events: list[dict[str, Any]] | None = None,
        receipt: dict[str, Any] | None = None,
        operations: dict[str, Any] | None = None,
    ) -> None:
        # Paired positive control: every negative fixture starts from this exact
        # production-built A/B/event/receipt tuple, and that tuple must pass both
        # gates before the single adversarial delta is evaluated.
        self._assert_both_accept(self.events, self.receipt, self.operations)
        events = copy.deepcopy(events if events is not None else self.events)
        receipt = copy.deepcopy(receipt if receipt is not None else self.receipt)
        operations = copy.deepcopy(
            operations if operations is not None else self.operations
        )
        with self.assertRaises(staging.StagingError):
            staging.verify_coverage_receipt_against_events(
                receipt, events, self.requirements, operations
            )
        with self.assertRaises(qc.QCFailure):
            qc.verify_event_ledger(
                events,
                self.requirements,
                operations,
                receipt,
                self.packet,
            )

    def test_positive_same_fixture_is_accepted_independently(self) -> None:
        for operation in self.operations["operations"]:
            self.assertEqual(
                qc._parse_codex_event_command(operation["exact_command"]),
                operation["argv"],
            )
        self._assert_both_accept(self.events, self.receipt)

    def test_reasoning_before_terminal_agent_is_a_paired_positive(self) -> None:
        """The frozen policy explicitly permits exact reasoning items."""

        for event_type in ("item.started", "item.completed"):
            with self.subTest(event_type=event_type):
                events = copy.deepcopy(self.events)
                reasoning = copy.deepcopy(REASONING_EVENT)
                reasoning["type"] = event_type
                # Place it between two completed command pairs, never inside an
                # active started/completed pair.
                events.insert(4, reasoning)
                self._assert_both_accept(events, self.receipt)

    def test_staged_prompt_explicitly_binds_native_event_sequence(self) -> None:
        prompt = staging.staged_prompt(
            instructions="frozen instructions",
            template_text="frozen template",
            manifest={
                "coverage_requirements": self.requirements,
                "reader_operation_expectations": self.operations,
            },
        )
        required_clauses = (
            "Do not emit any agent message before or between the required reader commands.",
            "After the final required reader command, emit exactly one terminal agent message;",
            "no command or other item may follow it.",
            "That terminal agent message must contain only the raw JSON object",
        )

        def has_exact_contract(value: str) -> bool:
            return all(value.count(clause) == 1 for clause in required_clauses)

        # Paired positive: the exact production-generated prompt must carry all
        # four native CLI event obligations before any deletion is tested.
        self.assertTrue(has_exact_contract(prompt))
        for clause in required_clauses:
            with self.subTest(omitted_clause=clause):
                self.assertFalse(has_exact_contract(prompt.replace(clause, "", 1)))

    def test_exact_outer_framing_and_terminal_message_faults_reject_by_both(
        self,
    ) -> None:
        """One valid real-CLI-shaped ledger precedes each single-delta fault."""

        def changed(mutator: Callable[[list[dict[str, Any]]], None]) -> list[dict[str, Any]]:
            events = copy.deepcopy(self.events)
            mutator(events)
            return events

        faults: dict[str, list[dict[str, Any]]] = {
            "missing_thread_started": self.events[1:],
            "duplicate_thread_started": [
                copy.deepcopy(self.events[0]),
                *copy.deepcopy(self.events),
            ],
            "thread_started_after_turn_started": [
                copy.deepcopy(self.events[1]),
                copy.deepcopy(self.events[0]),
                *copy.deepcopy(self.events[2:]),
            ],
            "missing_turn_started": [
                copy.deepcopy(self.events[0]),
                *copy.deepcopy(self.events[2:]),
            ],
            "duplicate_turn_started": [
                *copy.deepcopy(self.events[:2]),
                copy.deepcopy(self.events[1]),
                *copy.deepcopy(self.events[2:]),
            ],
            "missing_final_agent": [
                *copy.deepcopy(self.events[:-2]),
                copy.deepcopy(self.events[-1]),
            ],
            "duplicate_final_agent": [
                *copy.deepcopy(self.events[:-1]),
                copy.deepcopy(self.events[-2]),
                copy.deepcopy(self.events[-1]),
            ],
            "missing_turn_completed": copy.deepcopy(self.events[:-1]),
            "duplicate_turn_completed": [
                *copy.deepcopy(self.events),
                copy.deepcopy(self.events[-1]),
            ],
            "turn_completed_before_agent": [
                *copy.deepcopy(self.events[:-2]),
                copy.deepcopy(self.events[-1]),
                copy.deepcopy(self.events[-2]),
            ],
        }

        early_agent = copy.deepcopy(self.events)
        terminal = early_agent.pop(-2)
        early_agent.insert(2, terminal)
        faults["agent_before_commands"] = early_agent

        after_agent_reasoning = copy.deepcopy(self.events)
        after_agent_reasoning.insert(-1, copy.deepcopy(REASONING_EVENT))
        faults["reasoning_after_terminal_agent"] = after_agent_reasoning

        active_reasoning = copy.deepcopy(self.events)
        active_reasoning.insert(3, copy.deepcopy(REASONING_EVENT))
        faults["reasoning_inside_active_command_pair"] = active_reasoning

        faults["empty_thread_id"] = changed(
            lambda events: events[0].__setitem__("thread_id", "")
        )
        faults["thread_event_extra_field"] = changed(
            lambda events: events[0].__setitem__("extra", 0)
        )
        faults["turn_started_extra_field"] = changed(
            lambda events: events[1].__setitem__("extra", 0)
        )
        faults["turn_completed_extra_field"] = changed(
            lambda events: events[-1].__setitem__("extra", 0)
        )
        faults["raw_usage_total_tokens_is_forbidden"] = changed(
            lambda events: events[-1]["usage"].__setitem__("total_tokens", 2)
        )
        faults["raw_usage_boolean_is_not_integer"] = changed(
            lambda events: events[-1]["usage"].__setitem__("cached_input_tokens", False)
        )
        faults["cached_usage_exceeds_input"] = changed(
            lambda events: events[-1]["usage"].__setitem__("cached_input_tokens", 2)
        )
        faults["final_agent_extra_field"] = changed(
            lambda events: events[-2]["item"].__setitem__("extra", 0)
        )
        faults["final_agent_non_json"] = changed(
            lambda events: events[-2]["item"].__setitem__("text", "not-json")
        )
        faults["final_agent_json_plus_prose"] = changed(
            lambda events: events[-2]["item"].__setitem__(
                "text", FINAL_JSON_TEXT + "\nfinished"
            )
        )
        faults["final_agent_wrong_json_keys"] = changed(
            lambda events: events[-2]["item"].__setitem__("text", '{"native":{}}')
        )
        faults["reasoning_extra_field"] = changed(
            lambda events: events.insert(
                4,
                {
                    **copy.deepcopy(REASONING_EVENT),
                    "item": {
                        **copy.deepcopy(REASONING_EVENT["item"]),
                        "extra": 0,
                    },
                },
            )
        )
        faults["command_started_extra_field"] = changed(
            lambda events: events[2]["item"].__setitem__("extra", 0)
        )

        for name, events in faults.items():
            with self.subTest(name=name):
                self._assert_both_reject(events=events)

    def test_physical_clean4_layer_a_b_is_rejected_as_old_namespace(self) -> None:
        candidate_root = TESTS_DIR.parent
        clean4_root = (
            candidate_root
            / "draft_generation"
            / "prelock_claims"
            / "wave_004_v6_clean4_hardened"
            / "frozen_reader_coverage"
        )
        case_id = "SystemCopyToClipboard"
        requirements_path = clean4_root / case_id / "model_input_coverage.json"
        operations_path = clean4_root / case_id / "reader_operation_expectations.json"
        self.assertTrue(requirements_path.is_file(), "clean4 negative fixture is missing")
        self.assertTrue(operations_path.is_file(), "clean4 negative fixture is missing")
        requirements = json.loads(requirements_path.read_text(encoding="utf-8"))
        operations = json.loads(operations_path.read_text(encoding="utf-8"))
        packet_root = candidate_root / "case_packets" / "androidworld"
        packet = qc.parse_packet(
            packet_root / case_id / "case_packet.md",
            packet_root / case_id,
            case_id,
            str(requirements["task_id"]),
        )
        self.assertEqual(
            requirements.get("production_namespace"),
            "wave_004_v6_clean4_hardened",
        )
        with self.assertRaises(staging.StagingError):
            staging.verify_reader_operation_expectations_binding(
                requirements, operations
            )
        with self.assertRaises(qc.QCFailure):
            qc.verify_reader_operation_expectations(
                requirements, operations, packet
            )

    def test_bare_and_double_wrapped_event_carriers_are_rejected_by_both(self) -> None:
        base_pairs = _command_pairs(self.events)
        with self.subTest(name="bare_semantic_command"):
            pairs = copy.deepcopy(base_pairs)
            for event in pairs[0]:
                event["item"]["command"] = self.operations["operations"][0][
                    "semantic_command"
                ]
            self._assert_both_reject(events=_flatten(pairs))
        with self.subTest(name="double_host_shell_wrapper"):
            pairs = copy.deepcopy(base_pairs)
            exact = self.operations["operations"][0]["exact_command"]
            nested = f"/bin/zsh -lc '{exact}'"
            for event in pairs[0]:
                event["item"]["command"] = nested
            self._assert_both_reject(events=_flatten(pairs))

    def test_event_fault_matrix_is_rejected_by_both(self) -> None:
        base_pairs = _command_pairs(self.events)

        def reverse_order(pairs: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
            pairs[0], pairs[1] = pairs[1], pairs[0]
            return _flatten(pairs)

        def duplicate_command(pairs: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
            duplicate = copy.deepcopy(pairs[0])
            for event in duplicate:
                event["item"]["id"] = "cmd-extra-duplicate"
            return _flatten(pairs + [duplicate])

        def nonzero_exit(pairs: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
            pairs[0][1]["item"]["exit_code"] = 1
            return _flatten(pairs)

        def boolean_false_exit(pairs: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
            pairs[0][1]["item"]["exit_code"] = False
            return _flatten(pairs)

        def old_status(pairs: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
            pairs[0][1]["item"]["status"] = "success"
            return _flatten(pairs)

        def forged_agent_message(pairs: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
            output = pairs[0][1]["item"]["aggregated_output"]
            pairs[0][1]["item"]["aggregated_output"] = ""
            pairs[0][1]["item"]["stdout"] = output
            framed = _flatten(pairs)
            framed.insert(
                -1,
                {
                    "type": "item.completed",
                    "item": {
                        "id": "forged-agent-marker",
                        "type": "agent_message",
                        "text": output,
                    },
                },
            )
            return framed

        def cross_id_outputs(pairs: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
            left = pairs[0][1]["item"]["aggregated_output"]
            right = pairs[1][1]["item"]["aggregated_output"]
            pairs[0][1]["item"]["aggregated_output"] = right
            pairs[1][1]["item"]["aggregated_output"] = left
            return _flatten(pairs)

        def missing_start(pairs: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
            pairs[0] = [pairs[0][1]]
            return _flatten(pairs)

        def missing_completion(pairs: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
            pairs[0] = [pairs[0][0]]
            return _flatten(pairs)

        def reused_id(pairs: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
            reused = pairs[0][0]["item"]["id"]
            for event in pairs[1]:
                event["item"]["id"] = reused
            return _flatten(pairs)

        def changed_command_under_id(pairs: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
            pairs[0][1]["item"]["command"] += " "
            return _flatten(pairs)

        def missing_completion_marker(pairs: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
            body, _ = _terminal_parts(pairs[0][1]["item"]["aggregated_output"])
            pairs[0][1]["item"]["aggregated_output"] = body
            return _flatten(pairs)

        def duplicate_completion_marker(pairs: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
            output = pairs[0][1]["item"]["aggregated_output"]
            _, completion = _terminal_parts(output)
            pairs[0][1]["item"]["aggregated_output"] = output + (
                qc.READER_COMPLETION_PREFIX
                + json.dumps(completion, sort_keys=True, separators=(",", ":"))
                + "\n"
            )
            return _flatten(pairs)

        def truncated_body(pairs: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
            output = pairs[3][1]["item"]["aggregated_output"]
            body, completion = _terminal_parts(output)
            pairs[3][1]["item"]["aggregated_output"] = (
                body[:-2]
                + "\n"
                + qc.READER_COMPLETION_PREFIX
                + json.dumps(completion, sort_keys=True, separators=(",", ":"))
                + "\n"
            )
            return _flatten(pairs)

        def wrong_completion_field(
            field: str, value: Any
        ) -> Callable[[list[list[dict[str, Any]]]], list[dict[str, Any]]]:
            def mutate(pairs: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
                output = pairs[0][1]["item"]["aggregated_output"]
                _, completion = _terminal_parts(output)
                completion[field] = value
                pairs[0][1]["item"]["aggregated_output"] = _replace_terminal(
                    output, completion
                )
                return _flatten(pairs)

            return mutate

        event_faults: dict[
            str, Callable[[list[list[dict[str, Any]]]], list[dict[str, Any]]]
        ] = {
            "reverse_global_order": reverse_order,
            "duplicate_command": duplicate_command,
            "nonzero_exit": nonzero_exit,
            "boolean_false_is_not_integer_zero_exit": boolean_false_exit,
            "old_completed_status": old_status,
            "agent_message_forged_marker_and_stdout_fallback": forged_agent_message,
            "cross_id_swapped_aggregated_outputs": cross_id_outputs,
            "missing_started": missing_start,
            "missing_completed": missing_completion,
            "reused_command_id": reused_id,
            "changed_command_under_same_id": changed_command_under_id,
            "missing_terminal_marker": missing_completion_marker,
            "duplicate_terminal_marker": duplicate_completion_marker,
            "truncated_body": truncated_body,
            "wrong_body_hash": wrong_completion_field("body_sha256", "0" * 64),
            "wrong_argv_hash": wrong_completion_field("argv_sha256", "1" * 64),
            "wrong_requirements_hash": wrong_completion_field(
                "requirements_sha256", "2" * 64
            ),
        }
        for name, mutate in event_faults.items():
            with self.subTest(name=name):
                self._assert_both_reject(events=mutate(copy.deepcopy(base_pairs)))

        for operator in (";", "&&", "||", "|", "$(true)", "`true`"):
            with self.subTest(name=f"shell_composition_{operator}"):
                pairs = copy.deepcopy(base_pairs)
                for event in pairs[0]:
                    event["item"]["command"] += f" {operator} true"
                self._assert_both_reject(events=_flatten(pairs))

        for name, command in {
            "extra_inspect": (
                "/usr/bin/python3 packet_reader.py inspect --path official/x.py "
                f"--start 1 --end 1 --manifest-sha256 {self.requirements['requirements_sha256']}"
            ),
            "extra_unplanned_read": self.operations["operations"][-1]["exact_command"],
            "unrelated_command": "/bin/pwd",
        }.items():
            with self.subTest(name=name):
                pairs = copy.deepcopy(base_pairs)
                output = pairs[0][1]["item"]["aggregated_output"]
                pairs.append(
                    [
                        {
                            "type": "item.started",
                            "item": {
                                "id": f"{name}-id",
                                "type": "command_execution",
                                "command": command,
                            },
                        },
                        {
                            "type": "item.completed",
                            "item": {
                                "id": f"{name}-id",
                                "type": "command_execution",
                                "command": command,
                                "status": "completed",
                                "exit_code": 0,
                                "aggregated_output": output,
                            },
                        },
                    ]
                )
                self._assert_both_reject(events=_flatten(pairs))

        for name, page_pairs in {
            "missing_plan_page": base_pairs[:2] + base_pairs[3:],
            "duplicated_plan_page": base_pairs[:3] + [copy.deepcopy(base_pairs[2])] + base_pairs[3:],
        }.items():
            with self.subTest(name=name):
                pairs = copy.deepcopy(page_pairs)
                if name == "duplicated_plan_page":
                    for event in pairs[3]:
                        event["item"]["id"] = "duplicate-page-id"
                self._assert_both_reject(events=_flatten(pairs))

        with self.subTest(name="oversized_plan_page_output"):
            pairs = copy.deepcopy(base_pairs)
            output = pairs[2][1]["item"]["aggregated_output"]
            body, completion = _terminal_parts(output)
            oversized_body = body + ("X" * qc.MAX_COVERAGE_PLAN_PAGE_OUTPUT_BYTES) + "\n"
            completion["body_sha256"] = qc._sha256_text(oversized_body)
            completion["body_size_bytes"] = len(oversized_body.encode("utf-8"))
            pairs[2][1]["item"]["aggregated_output"] = (
                oversized_body
                + qc.READER_COMPLETION_PREFIX
                + json.dumps(completion, sort_keys=True, separators=(",", ":"))
                + "\n"
            )
            self._assert_both_reject(events=_flatten(pairs))

    def test_receipt_fault_matrix_is_rejected_by_both(self) -> None:
        def old_schema(receipt: dict[str, Any]) -> None:
            receipt["schema_version"] = (
                "androidworld_candidate116_staged_source_coverage_receipt/v1"
            )

        def old_status(receipt: dict[str, Any]) -> None:
            receipt["status"] = "all_required_raw_official_ranges_read"

        def old_fields(receipt: dict[str, Any]) -> None:
            receipt["additional_inspection_count"] = 0
            receipt["completed_command_count"] = receipt["completed_operation_count"]
            receipt.pop("additional_command_count", None)

        def wrong_namespace(receipt: dict[str, Any]) -> None:
            receipt["production_namespace"] = "wave_004_v6_clean3_hardened"

        def cross_id(receipt: dict[str, Any]) -> None:
            receipt["completed_operations"][0]["completed_event_id"] = (
                receipt["completed_operations"][1]["completed_event_id"]
            )

        def missing_operation(receipt: dict[str, Any]) -> None:
            receipt["completed_operations"].pop()

        def duplicate_page(receipt: dict[str, Any]) -> None:
            receipt["coverage_pages_read"].append(0)

        def extra_field(receipt: dict[str, Any]) -> None:
            receipt["forged_marker_count"] = 0

        receipt_faults: dict[str, Callable[[dict[str, Any]], None]] = {
            "old_v1_receipt_schema": old_schema,
            "old_receipt_status": old_status,
            "old_inspect_and_command_count_fields": old_fields,
            "old_production_namespace": wrong_namespace,
            "cross_id_receipt_binding": cross_id,
            "missing_completed_operation": missing_operation,
            "duplicate_coverage_page": duplicate_page,
            "extra_receipt_field": extra_field,
        }
        for name, mutate in receipt_faults.items():
            with self.subTest(name=name):
                receipt = copy.deepcopy(self.receipt)
                mutate(receipt)
                _resign_receipt(receipt)
                self._assert_both_reject(receipt=receipt)

        with self.subTest(name="wrong_outer_receipt_hash"):
            receipt = copy.deepcopy(self.receipt)
            receipt["coverage_receipt_sha256"] = "f" * 64
            self._assert_both_reject(receipt=receipt)

    def test_layer_b_binding_faults_are_rejected_by_both(self) -> None:
        mutations: dict[str, Callable[[dict[str, Any]], None]] = {
            "wrong_operation_self_hash": lambda value: value["operations"][0].__setitem__(
                "operation_sha256", "0" * 64
            ),
            "wrong_argv_hash": lambda value: value["operations"][0].__setitem__(
                "argv_sha256", "1" * 64
            ),
            "wrong_operations_list_hash": lambda value: value.__setitem__(
                "operations_sha256", "2" * 64
            ),
            "wrong_expectations_self_hash": lambda value: value.__setitem__(
                "reader_operation_expectations_sha256", "3" * 64
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                operations = copy.deepcopy(self.operations)
                mutate(operations)
                self._assert_both_reject(operations=operations)

    def test_resigned_old_event_trust_policy_is_rejected_by_both_binding_gates(
        self,
    ) -> None:
        operations = copy.deepcopy(self.operations)
        policy = operations["event_trust_policy"]
        self.assertIs(
            policy.pop("model_supplied_shell_wrapper_pipeline_or_chain_allowed"),
            False,
        )
        policy["shell_wrapper_pipeline_or_chain_allowed"] = False
        operations.pop("reader_operation_expectations_sha256", None)
        operations["reader_operation_expectations_sha256"] = qc.canonical_sha256(
            operations
        )
        with self.assertRaises(staging.StagingError):
            staging.verify_reader_operation_expectations_binding(
                self.requirements, operations
            )
        with self.assertRaises(qc.QCFailure):
            qc.verify_reader_operation_expectations(
                self.requirements, operations, self.packet
            )

    def test_resigned_json_boolean_integer_confusion_is_rejected_by_both_gates(
        self,
    ) -> None:
        """JSON booleans must never satisfy frozen integer/boolean bindings.

        Python considers ``False == 0`` and ``True == 1``.  Every comparison in
        the two independent binding gates must instead preserve JSON type.
        Each fixture is otherwise valid and is re-signed after mutation.
        """

        first_read_index = 2 + self.requirements["coverage_page_count"]

        def policy_false_to_zero(value: dict[str, Any]) -> tuple[int, ...]:
            value["event_trust_policy"][
                "model_supplied_shell_wrapper_pipeline_or_chain_allowed"
            ] = 0
            return ()

        def carrier_false_to_zero_with_stale_inner_hash(
            value: dict[str, Any],
        ) -> tuple[int, ...]:
            value["event_shell_carrier"]["bare_semantic_argv_event_allowed"] = 0
            # Deliberately retain carrier_binding_sha256: an outer signature
            # must not hide an invalid nested self-hash.
            return ()

        def overview_one_to_true(value: dict[str, Any]) -> tuple[int, ...]:
            value["operations"][0]["semantic_identity"][
                "coverage_page_count"
            ] = True
            return (0,)

        def plan_page_zero_to_false(value: dict[str, Any]) -> tuple[int, ...]:
            value["operations"][2]["semantic_identity"]["page_index"] = False
            return (2,)

        def read_range_zero_to_false(value: dict[str, Any]) -> tuple[int, ...]:
            value["operations"][first_read_index]["semantic_identity"][
                "range_index"
            ] = False
            return (first_read_index,)

        def operation_index_zero_to_false(value: dict[str, Any]) -> tuple[int, ...]:
            value["operations"][0]["operation_index"] = False
            return (0,)

        mutations: dict[
            str, Callable[[dict[str, Any]], tuple[int, ...]]
        ] = {
            "event_policy_false_to_integer_zero": policy_false_to_zero,
            "carrier_false_to_integer_zero_stale_nested_hash": (
                carrier_false_to_zero_with_stale_inner_hash
            ),
            "overview_identity_integer_one_to_true": overview_one_to_true,
            "plan_page_identity_integer_zero_to_false": plan_page_zero_to_false,
            "read_identity_integer_zero_to_false": read_range_zero_to_false,
            "operation_index_integer_zero_to_false": operation_index_zero_to_false,
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                operations = copy.deepcopy(self.operations)
                changed_indexes = mutate(operations)
                _resign_operations(operations, changed_indexes)
                with self.assertRaises(staging.StagingError):
                    staging.verify_reader_operation_expectations_binding(
                        self.requirements, operations
                    )
                with self.assertRaises(qc.QCFailure):
                    qc.verify_reader_operation_expectations(
                        self.requirements, operations, self.packet
                    )

    def test_resigned_layer_a_schema_and_numeric_faults_are_rejected_by_both(
        self,
    ) -> None:
        """Layer A itself has paired-positive exact-schema/type enforcement."""

        def extra_top_level(value: dict[str, Any]) -> None:
            value["forged_complete"] = True

        def unresolved_false(value: dict[str, Any]) -> None:
            value["source_closure_audit"][
                "unresolved_internal_import_count"
            ] = False

        def call_closure_false(value: dict[str, Any]) -> None:
            value["decisive_call_closure"][
                "packet_local_unresolved_count"
            ] = False

        def inventory_size_false(value: dict[str, Any]) -> None:
            value["source_inventory"][0]["size_bytes"] = False

        def page_index_false(value: dict[str, Any]) -> None:
            value["coverage_pages"][0]["page_index"] = False

        def chunk_start_true(value: dict[str, Any]) -> None:
            value["raw_official_source_closure"][0]["chunks"][0][
                "start_line"
            ] = True

        def nested_extra_key(value: dict[str, Any]) -> None:
            value["derived_navigation"]["unsealed_hint"] = "ignore"

        def anchor_extra_key(value: dict[str, Any]) -> None:
            value["anchors"][0]["unsealed_hint"] = "ignore"

        def anchor_range_extra_key(value: dict[str, Any]) -> None:
            value["anchors"][0]["required_raw_official_ranges"][0][
                "unsealed_hint"
            ] = "ignore"

        def flattened_anchor_range_extra_key(value: dict[str, Any]) -> None:
            value["anchor_raw_official_ranges"][0]["unsealed_hint"] = "ignore"

        def required_range_extra_key(value: dict[str, Any]) -> None:
            value["required_ranges"][0]["unsealed_hint"] = "ignore"

        def coverage_page_extra_key(value: dict[str, Any]) -> None:
            value["coverage_pages"][0]["unsealed_hint"] = "ignore"

        def resolved_edge_extra_key(value: dict[str, Any]) -> None:
            value["decisive_call_closure"]["resolved_edges"][0][
                "unsealed_hint"
            ] = "ignore"
            value["decisive_call_closure"]["resolved_edges_sha256"] = (
                qc.canonical_sha256(
                    value["decisive_call_closure"]["resolved_edges"]
                )
            )

        def unresolved_call_extra_key(value: dict[str, Any]) -> None:
            value["decisive_call_closure"][
                "unresolved_external_semantic_direct_calls"
            ][0]["unsealed_hint"] = "ignore"

        mutations: dict[str, Callable[[dict[str, Any]], None]] = {
            "extra_top_level_field": extra_top_level,
            "unresolved_count_false": unresolved_false,
            "call_closure_count_false": call_closure_false,
            "source_inventory_size_false": inventory_size_false,
            "coverage_page_index_false": page_index_false,
            "closure_chunk_start_true": chunk_start_true,
            "derived_navigation_extra_key": nested_extra_key,
            "anchor_extra_key": anchor_extra_key,
            "anchor_range_extra_key": anchor_range_extra_key,
            "flattened_anchor_range_extra_key": flattened_anchor_range_extra_key,
            "required_range_extra_key": required_range_extra_key,
            "coverage_page_extra_key": coverage_page_extra_key,
            "resolved_call_edge_extra_key": resolved_edge_extra_key,
            "unresolved_call_extra_key": unresolved_call_extra_key,
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                # Paired positive control for these exact direct Layer-A gates.
                staging.verify_coverage_requirements_contract(self.requirements)
                qc.validate_coverage(self.requirements, self.packet)

                requirements = copy.deepcopy(self.requirements)
                mutate(requirements)
                requirements.pop("requirements_sha256", None)
                requirements["requirements_sha256"] = qc.canonical_sha256(
                    requirements
                )
                with self.assertRaises(staging.StagingError):
                    staging.verify_coverage_requirements_contract(requirements)
                with self.assertRaises(qc.QCFailure):
                    qc.validate_coverage(requirements, self.packet)


if __name__ == "__main__":
    unittest.main()
