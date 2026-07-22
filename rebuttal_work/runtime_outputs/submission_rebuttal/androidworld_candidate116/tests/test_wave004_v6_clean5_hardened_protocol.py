#!/usr/bin/env python3
"""Hermetic positive/negative tests for the clean5 A/B reader protocol."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path
from typing import Any


TEST_FILE = Path(__file__).resolve()
WORK_ROOT = TEST_FILE.parents[1]
SCRIPTS_ROOT = WORK_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT))

import wave004_v6_clean2_hardened_common as common  # noqa: E402
import wave004_v6_clean2_hardened_staging as staging  # noqa: E402
import prepare_codex_draft_prelock_v6_clean2_hardened as preparer  # noqa: E402
import run_fresh_draft_wave_v6_clean2_hardened as launcher  # noqa: E402


class Clean5ReaderProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        packets = sorted(
            (WORK_ROOT / "case_packets" / "androidworld").glob("*/case_packet.md")
        )
        if len(packets) != 116:
            raise AssertionError(
                f"expected 116 canonical packets, found {len(packets)}"
            )
        cls.packet_path = packets[0]
        cls.packet_text = cls.packet_path.read_text(encoding="utf-8")
        cls.parsed = staging.parse_packet_sources(cls.packet_text)
        tokenizer_root = (
            WORK_ROOT / "draft_generation" / "tokenizer" / "tiktoken_0_12_0_py312"
        )
        token_counter, cls.tokenizer_binding = staging.load_frozen_o200k_token_counter(
            tokenizer_root=tokenizer_root,
            merge_table_path=tokenizer_root
            / "encoding_cache"
            / "fb374d419588a4632f3f557e76b4b70aebbca790",
        )
        cls.token_counter = staticmethod(token_counter)
        requirements = staging.build_coverage_requirements(
            cls.parsed,
            token_counter=cls.token_counter,
            tokenizer_binding=cls.tokenizer_binding,
        )
        requirements["case_packet_sha256"] = staging.sha256_text(cls.packet_text)
        requirements["source_inventory"] = [
            {
                key: cls.parsed["sources"][path][key]
                for key in ("path", "sha256", "size_bytes", "line_count")
            }
            for path in cls.parsed["inventory"]
        ]
        requirements.pop("requirements_sha256", None)
        requirements["requirements_sha256"] = staging.canonical_sha256(requirements)
        cls.requirements = requirements
        cls.operation_expectations = staging.build_reader_operation_expectations(
            case_packet_text=cls.packet_text,
            parsed=cls.parsed,
            requirements=cls.requirements,
            token_counter=cls.token_counter,
        )
        cls.outputs = cls._render_outputs()
        cls.events = cls._events_for_outputs(cls.outputs)

    @classmethod
    def _render_outputs(cls) -> list[str]:
        requirements = cls.requirements
        header = cls.packet_text.split("## Packet Source Files\n", 1)[0]
        outputs = [
            staging.render_overview_output_for_audit(requirements),
            staging.render_header_output_for_audit(
                header_text=header,
                case_packet_sha256=requirements["case_packet_sha256"],
                requirements_sha256=requirements["requirements_sha256"],
            ),
        ]
        outputs.extend(
            staging.render_plan_page_output_for_audit(
                page_index=index, requirements=requirements
            )
            for index in range(requirements["coverage_page_count"])
        )
        outputs.extend(
            staging.render_read_output_for_audit(
                row=row,
                source_text=cls.parsed["sources"][row["path"]]["text"],
                requirements_sha256=requirements["requirements_sha256"],
            )
            for row in requirements["required_ranges"]
        )
        return outputs

    @classmethod
    def _events_for_outputs(cls, outputs: list[str]) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = [
            {"type": "thread.started", "thread_id": "thread-0"},
            {"type": "turn.started"},
        ]
        operations = cls.operation_expectations["operations"]
        if len(outputs) != len(operations):
            raise AssertionError("fixture output/operation counts differ")
        for index, (operation, output) in enumerate(
            zip(operations, outputs, strict=True)
        ):
            item = {
                "type": "command_execution",
                "id": f"command-{index:03d}",
                "command": operation["exact_command"],
                "status": "in_progress",
                "exit_code": None,
                "aggregated_output": "",
            }
            events.append({"type": "item.started", "item": dict(item)})
            events.append(
                {
                    "type": "item.completed",
                    "item": {
                        **item,
                        "status": "completed",
                        "exit_code": 0,
                        "aggregated_output": output,
                    },
                }
            )
        events.append(
            {
                "type": "item.completed",
                "item": {
                    "type": "agent_message",
                    "id": "terminal-agent-message",
                    "text": '{"native":{},"stronger":{}}',
                },
            }
        )
        events.append(
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 1,
                    "cached_input_tokens": 0,
                    "output_tokens": 1,
                    "reasoning_output_tokens": 0,
                },
            }
        )
        return events

    @staticmethod
    def _resign_operation_expectations(value: dict[str, Any]) -> None:
        for operation in value["operations"]:
            core = dict(operation)
            core.pop("operation_sha256", None)
            operation["operation_sha256"] = staging.canonical_sha256(core)
        value["operations_sha256"] = staging.canonical_sha256(value["operations"])
        core = dict(value)
        core.pop("reader_operation_expectations_sha256", None)
        value["reader_operation_expectations_sha256"] = staging.canonical_sha256(core)

    @staticmethod
    def _resign_receipt(value: dict[str, Any]) -> None:
        core = dict(value)
        core.pop("coverage_receipt_sha256", None)
        value["coverage_receipt_sha256"] = staging.canonical_sha256(core)

    def assert_protocol_rejects(self, events: list[dict[str, Any]]) -> None:
        staging.coverage_receipt_from_events(
            self.events, self.requirements, self.operation_expectations
        )
        with self.assertRaises(staging.StagingError):
            staging.coverage_receipt_from_events(
                events, self.requirements, self.operation_expectations
            )

    @staticmethod
    def _write_candidate_approval_fixture(
        path: Path, *, include_nonce: bool = True, mode: int = 0o444
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": common.CANDIDATE_REVIEW_SCHEMA,
            "status": "approved_for_create_once_candidate_prelock",
            "candidate_generation_id": common.GENERATION_ID,
            "scripts": preparer.live_script_bindings(),
            "independent_final_go": False,
            "model_call_count": 0,
        }
        if include_nonce:
            payload["owner_nonce_sha256"] = hashlib.sha256(b"o" * 64).hexdigest()
        payload = common.add_self_hash(payload, "approval_sha256")
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        path.chmod(mode)
        return payload

    def test_candidate_approval_seal_nonce_and_toctou_gates(self) -> None:
        with tempfile.TemporaryDirectory(prefix="clean5-approval-gate-") as temp_dir:
            root = Path(temp_dir).resolve()
            valid_path = root / "valid.json"
            expected = self._write_candidate_approval_fixture(valid_path)
            observed, binding = preparer.verify_reviewed_candidate_approval(valid_path)
            self.assertEqual(observed, expected)
            self.assertEqual(binding["mode"], 0o444)

            mode_path = root / "mode-0644.json"
            self._write_candidate_approval_fixture(mode_path, mode=0o644)
            with self.assertRaises(common.Wave004V6Clean2HardenedError):
                preparer.verify_reviewed_candidate_approval(mode_path)

            target_path = root / "symlink-target.json"
            self._write_candidate_approval_fixture(target_path)
            symlink_path = root / "approval-symlink.json"
            symlink_path.symlink_to(target_path)
            with self.assertRaises(common.Wave004V6Clean2HardenedError):
                preparer.verify_reviewed_candidate_approval(symlink_path)

            missing_nonce_path = root / "missing-nonce.json"
            self._write_candidate_approval_fixture(
                missing_nonce_path, include_nonce=False
            )
            with self.assertRaises(common.Wave004V6Clean2HardenedError):
                preparer.verify_reviewed_candidate_approval(missing_nonce_path)

            valid_path.chmod(0o600)
            changed = dict(expected)
            changed["review_note"] = "post-capture mutation"
            changed = common.add_self_hash(changed, "approval_sha256")
            valid_path.write_text(
                json.dumps(changed, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
            valid_path.chmod(0o444)
            with self.assertRaises(common.Wave004V6Clean2HardenedError):
                preparer.verify_candidate_gate_unchanged(
                    valid_path,
                    expected_approval=expected,
                    expected_approval_file_binding=binding,
                    expected_script_bindings=expected["scripts"],
                )

            stable_path = root / "stable.json"
            stable = self._write_candidate_approval_fixture(stable_path)
            _stable, stable_binding = preparer.verify_reviewed_candidate_approval(
                stable_path
            )
            drifted_scripts = copy.deepcopy(stable["scripts"])
            drifted_scripts["staging"]["sha256"] = "0" * 64
            with mock.patch.object(
                preparer, "live_script_bindings", return_value=drifted_scripts
            ):
                with self.assertRaises(common.Wave004V6Clean2HardenedError):
                    preparer.verify_candidate_gate_unchanged(
                        stable_path,
                        expected_approval=stable,
                        expected_approval_file_binding=stable_binding,
                        expected_script_bindings=stable["scripts"],
                    )

            expected_core = {"prompt": common.regular_file_binding(stable_path)}
            drifted_core = copy.deepcopy(expected_core)
            drifted_core["prompt"]["sha256"] = "f" * 64
            with mock.patch.object(
                preparer,
                "capture_core_input_bindings",
                return_value=drifted_core,
            ):
                with self.assertRaises(common.Wave004V6Clean2HardenedError):
                    preparer.verify_core_input_bindings_unchanged(expected_core)

    def test_one_shot_owner_and_launch_nonce_gates(self) -> None:
        for field, environment_variable in (
            ("owner_nonce_sha256", common.OWNER_NONCE_ENV),
            ("launch_nonce_sha256", common.LAUNCH_NONCE_ENV),
        ):
            with self.subTest(field=field, state="missing"):
                with mock.patch.dict(os.environ, {}, clear=False):
                    os.environ.pop(environment_variable, None)
                    with self.assertRaises(common.Wave004V6Clean2HardenedError):
                        common.consume_and_verify_nonce(
                            {field: hashlib.sha256(b"x" * 32).hexdigest()},
                            hash_field=field,
                            environment_variable=environment_variable,
                            label="dry gate",
                        )
            with self.subTest(field=field, state="wrong"):
                with mock.patch.dict(
                    os.environ, {environment_variable: "w" * 32}, clear=False
                ):
                    with self.assertRaises(common.Wave004V6Clean2HardenedError):
                        common.consume_and_verify_nonce(
                            {field: hashlib.sha256(b"r" * 32).hexdigest()},
                            hash_field=field,
                            environment_variable=environment_variable,
                            label="dry gate",
                        )
                    self.assertNotIn(environment_variable, os.environ)
            with self.subTest(field=field, state="correct"):
                nonce = "n" * 64
                expected_hash = hashlib.sha256(nonce.encode("utf-8")).hexdigest()
                with mock.patch.dict(
                    os.environ, {environment_variable: nonce}, clear=False
                ):
                    receipt = common.consume_and_verify_nonce(
                        {field: expected_hash},
                        hash_field=field,
                        environment_variable=environment_variable,
                        label="dry gate",
                    )
                    self.assertNotIn(environment_variable, os.environ)
                self.assertEqual(receipt["nonce_sha256"], expected_hash)
                self.assertFalse(receipt["raw_nonce_persisted"])
                self.assertNotIn(nonce, json.dumps(receipt, sort_keys=True))

    def test_actual_codex_usage_has_exact_32k_and_context_limits(self) -> None:
        valid = {
            "input_tokens": 100_000,
            "output_tokens": 32_000,
            "total_tokens": 132_000,
            "input_tokens_details": {"cached_tokens": 50_000},
            "output_tokens_details": {"reasoning_tokens": 20_000},
        }
        launcher.verify_actual_codex_usage(valid)
        for label, mutate in (
            (
                "output-over-32k",
                lambda value: value.update(
                    {"output_tokens": 32_001, "total_tokens": 132_001}
                ),
            ),
            (
                "false-as-zero",
                lambda value: value.__setitem__("output_tokens", False),
            ),
            (
                "total-mismatch",
                lambda value: value.__setitem__("total_tokens", 131_999),
            ),
        ):
            with self.subTest(label=label):
                tampered = copy.deepcopy(valid)
                mutate(tampered)
                with self.assertRaises(launcher.GenerationError):
                    launcher.verify_actual_codex_usage(tampered)

    def test_positive_A_B_and_exact_receipt(self) -> None:
        self.assertEqual(staging.PRODUCTION_NAMESPACE, "wave_004_v6_clean5_hardened")
        staging.verify_reader_operation_expectations_binding(
            self.requirements, self.operation_expectations
        )
        self.assertEqual(
            len(staging.ordered_completed_command_records(self.events)),
            self.operation_expectations["operation_count"],
        )
        self.assertFalse(
            self.operation_expectations["event_trust_policy"][
                "model_supplied_shell_wrapper_pipeline_or_chain_allowed"
            ]
        )
        self.assertEqual(
            self.operation_expectations["event_shell_carrier"],
            staging.codex_event_shell_carrier_binding(),
        )
        for operation, output in zip(
            self.operation_expectations["operations"], self.outputs, strict=True
        ):
            self.assertEqual(
                operation["expected_full_output_sha256"], staging.sha256_text(output)
            )
            self.assertEqual(
                operation["expected_full_output_size_bytes"],
                len(output.encode("utf-8")),
            )
        receipt = staging.coverage_receipt_from_events(
            self.events, self.requirements, self.operation_expectations
        )
        self.assertEqual(receipt["status"], "all_required_reader_operations_completed")
        self.assertEqual(
            receipt["completed_operation_count"],
            self.operation_expectations["operation_count"],
        )
        staging.verify_coverage_receipt_against_events(
            receipt, self.events, self.requirements, self.operation_expectations
        )

    def test_existing_codex_events_calibrate_exact_host_shell_carrier(self) -> None:
        wave_root = WORK_ROOT / "draft_generation" / "waves"
        matched = 0
        for path in wave_root.rglob("api_response.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                continue
            for event in (payload.get("codex_cli") or {}).get("events") or []:
                item = event.get("item") or {}
                command = item.get("command")
                if item.get("type") != "command_execution" or not isinstance(
                    command, str
                ):
                    continue
                try:
                    carrier = shlex.split(command)
                except ValueError:
                    continue
                if (
                    len(carrier) != 3
                    or carrier[:2] != ["/bin/zsh", "-lc"]
                    or not staging.SAFE_READER_INNER_COMMAND_RE.fullmatch(carrier[2])
                ):
                    continue
                semantic_argv = shlex.split(carrier[2])
                self.assertEqual(
                    command, staging.render_codex_event_command(semantic_argv)
                )
                matched += 1
        self.assertGreaterEqual(matched, 10)

    def test_bare_event_command_is_rejected_but_exact_carrier_passes(self) -> None:
        staging.coverage_receipt_from_events(
            self.events, self.requirements, self.operation_expectations
        )
        bare = copy.deepcopy(self.events)
        semantic_command = self.operation_expectations["operations"][0][
            "semantic_command"
        ]
        for event in bare[2:4]:
            event["item"]["command"] = semantic_command
        self.assert_protocol_rejects(bare)

    def test_double_shell_wrapper_is_rejected(self) -> None:
        events = copy.deepcopy(self.events)
        exact = events[2]["item"]["command"]
        double = f'/bin/zsh -lc "{exact}"'
        for event in events[2:4]:
            event["item"]["command"] = double
        self.assert_protocol_rejects(events)

    def test_materialized_reader_matches_all_frozen_outputs(self) -> None:
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        with tempfile.TemporaryDirectory(prefix="clean5-reader-protocol-") as temp_dir:
            workspace = Path(temp_dir)
            materialization = staging.materialize_case_workspace(
                workspace,
                case_packet_text=self.packet_text,
                model_output_schema={},
                token_counter=self.token_counter,
                tokenizer_binding=self.tokenizer_binding,
            )
            try:
                operations = materialization["reader_operation_expectations"][
                    "operations"
                ]
                for operation in operations:
                    completed = subprocess.run(
                        operation["argv"],
                        cwd=workspace,
                        env=environment,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(completed.returncode, 0)
                    self.assertEqual(completed.stderr, "")
                    self.assertEqual(
                        staging.sha256_text(completed.stdout),
                        operation["expected_full_output_sha256"],
                    )
            finally:
                staging.unseal_case_workspace_for_cleanup(workspace)

    def test_runtime_A_or_B_drift_from_frozen_pair_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="clean5-frozen-ab-") as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir(mode=0o700)
            materialization = staging.materialize_case_workspace(
                workspace,
                case_packet_text=self.packet_text,
                model_output_schema={},
                token_counter=self.token_counter,
                tokenizer_binding=self.tokenizer_binding,
            )
            frozen_case = root / materialization["case_unit_id"]
            frozen_case.mkdir(mode=0o700)
            names = (
                "model_input_coverage.json",
                "reader_operation_expectations.json",
            )
            for name in names:
                target = frozen_case / name
                target.write_bytes((workspace / name).read_bytes())
                target.chmod(0o444)
            frozen_case.chmod(0o555)
            try:
                staging.verify_workspace_against_frozen_reader_coverage(
                    workspace, frozen_case, materialization
                )
                for name in names:
                    with self.subTest(name=name):
                        target = frozen_case / name
                        original = target.read_bytes()
                        target.chmod(0o600)
                        target.write_bytes(original + b"\n")
                        target.chmod(0o444)
                        with self.assertRaises(staging.StagingError):
                            staging.verify_workspace_against_frozen_reader_coverage(
                                workspace, frozen_case, materialization
                            )
                        target.chmod(0o600)
                        target.write_bytes(original)
                        target.chmod(0o444)
            finally:
                staging.unseal_case_workspace_for_cleanup(workspace)
                frozen_case.chmod(0o700)
                for name in names:
                    (frozen_case / name).chmod(0o600)

    def test_resigned_argv_sha256_tamper_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.operation_expectations)
        tampered["operations"][0]["argv_sha256"] = "0" * 64
        self._resign_operation_expectations(tampered)
        with self.assertRaises(staging.StagingError):
            staging.verify_reader_operation_expectations_binding(
                self.requirements, tampered
            )

    def test_resigned_old_event_trust_policy_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.operation_expectations)
        policy = tampered["event_trust_policy"]
        policy["shell_wrapper_pipeline_or_chain_allowed"] = policy.pop(
            "model_supplied_shell_wrapper_pipeline_or_chain_allowed"
        )
        self._resign_operation_expectations(tampered)
        with self.assertRaises(staging.StagingError):
            staging.verify_reader_operation_expectations_binding(
                self.requirements, tampered
            )

    def test_resigned_bool_int_nested_contract_matrix_is_rejected(self) -> None:
        mutations = (
            (
                "event-policy-false-to-zero",
                lambda value: value["event_trust_policy"].__setitem__(
                    "model_supplied_shell_wrapper_pipeline_or_chain_allowed", 0
                ),
            ),
            (
                "carrier-false-to-zero-with-stale-nested-hash",
                lambda value: value["event_shell_carrier"].__setitem__(
                    "bare_semantic_argv_event_allowed", 0
                ),
            ),
            (
                "overview-count-one-to-true",
                lambda value: value["operations"][0]["semantic_identity"].__setitem__(
                    "coverage_page_count", True
                ),
            ),
            (
                "plan-page-index-zero-to-false",
                lambda value: value["operations"][2]["semantic_identity"].__setitem__(
                    "page_index", False
                ),
            ),
            (
                "read-range-index-zero-to-false",
                lambda value: value["operations"][
                    2 + self.requirements["coverage_page_count"]
                ]["semantic_identity"].__setitem__("range_index", False),
            ),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                tampered = copy.deepcopy(self.operation_expectations)
                mutate(tampered)
                self._resign_operation_expectations(tampered)
                with self.assertRaises(staging.StagingError):
                    staging.verify_reader_operation_expectations_binding(
                        self.requirements, tampered
                    )

        tampered_a = copy.deepcopy(self.requirements)
        tampered_a["policy"]["recursive_source_ref_mapping_missing_count"] = False
        tampered_a.pop("requirements_sha256", None)
        tampered_a["requirements_sha256"] = staging.canonical_sha256(tampered_a)
        rebuilt_b = staging.build_reader_operation_expectations(
            case_packet_text=self.packet_text,
            parsed=self.parsed,
            requirements=tampered_a,
            token_counter=self.token_counter,
        )
        with self.assertRaises(staging.StagingError):
            staging.verify_reader_operation_expectations_binding(tampered_a, rebuilt_b)

    def test_resigned_expected_output_tamper_is_rejected_by_replay(self) -> None:
        tampered = copy.deepcopy(self.operation_expectations)
        tampered["operations"][0]["expected_full_output_sha256"] = "f" * 64
        self._resign_operation_expectations(tampered)
        staging.verify_reader_operation_expectations_binding(
            self.requirements, tampered
        )
        with self.assertRaises(staging.StagingError):
            staging.coverage_receipt_from_events(
                self.events, self.requirements, tampered
            )

    def test_agent_message_fake_marker_cannot_rescue_truncation(self) -> None:
        events = copy.deepcopy(self.events)
        events[3]["item"]["aggregated_output"] = events[3]["item"]["aggregated_output"][
            :-20
        ]
        events[-2]["item"]["text"] = self.outputs[0]
        self.assert_protocol_rejects(events)

    def test_cross_id_completion_is_rejected(self) -> None:
        events = copy.deepcopy(self.events)
        events[3]["item"]["id"] = "cross-id"
        self.assert_protocol_rejects(events)

    def test_only_one_final_agent_message_is_allowed(self) -> None:
        staging.coverage_receipt_from_events(
            self.events, self.requirements, self.operation_expectations
        )
        middle = copy.deepcopy(self.events)
        terminal = middle.pop(-2)
        middle.insert(4, terminal)
        self.assert_protocol_rejects(middle)

        early = copy.deepcopy(self.events)
        terminal = early.pop(-2)
        early.insert(2, terminal)
        self.assert_protocol_rejects(early)

        reasoning = copy.deepcopy(self.events)
        reasoning.insert(
            4,
            {
                "type": "item.completed",
                "item": {
                    "type": "reasoning",
                    "id": "reasoning-0",
                    "text": "bounded reader plan",
                },
            },
        )
        staging.coverage_receipt_from_events(
            reasoning, self.requirements, self.operation_expectations
        )

    def test_boolean_false_is_not_integer_zero_and_resigned_json_ints_reject(
        self,
    ) -> None:
        events = copy.deepcopy(self.events)
        events[3]["item"]["exit_code"] = False
        self.assert_protocol_rejects(events)

        tampered_b = copy.deepcopy(self.operation_expectations)
        tampered_b["operations"][0]["operation_index"] = False
        self._resign_operation_expectations(tampered_b)
        with self.assertRaises(staging.StagingError):
            staging.verify_reader_operation_expectations_binding(
                self.requirements, tampered_b
            )

        tampered_a = copy.deepcopy(self.requirements)
        tampered_a["required_ranges"][0]["start_line"] = True
        tampered_a.pop("requirements_sha256", None)
        tampered_a["requirements_sha256"] = staging.canonical_sha256(tampered_a)
        rebuilt_b = staging.build_reader_operation_expectations(
            case_packet_text=self.packet_text,
            parsed=self.parsed,
            requirements=tampered_a,
            token_counter=self.token_counter,
        )
        with self.assertRaises(staging.StagingError):
            staging.verify_reader_operation_expectations_binding(tampered_a, rebuilt_b)

    def test_resigned_legacy_receipt_status_is_rejected(self) -> None:
        receipt = staging.coverage_receipt_from_events(
            self.events, self.requirements, self.operation_expectations
        )
        receipt["status"] = (
            "all_distinct_raw_official_payloads_read_with_terminal_envelopes"
        )
        receipt["additional_inspection_count"] = 0
        self._resign_receipt(receipt)
        with self.assertRaises(staging.StagingError):
            staging.verify_coverage_receipt_against_events(
                receipt, self.events, self.requirements, self.operation_expectations
            )

    def test_truncated_output_is_rejected(self) -> None:
        events = copy.deepcopy(self.events)
        events[3]["item"]["aggregated_output"] = events[3]["item"]["aggregated_output"][
            :-1
        ]
        self.assert_protocol_rejects(events)

    def test_missing_repeated_and_reordered_operations_are_rejected(self) -> None:
        missing = copy.deepcopy(self.events[:2] + self.events[4:])
        self.assert_protocol_rejects(missing)

        repeated = copy.deepcopy(self.events)
        extra_pair = copy.deepcopy(repeated[-4:-2])
        extra_pair[0]["item"]["id"] = "repeated-extra"
        extra_pair[1]["item"]["id"] = "repeated-extra"
        repeated.extend(extra_pair)
        self.assert_protocol_rejects(repeated)

        reordered = copy.deepcopy(self.events)
        reordered[2:6] = reordered[4:6] + reordered[2:4]
        self.assert_protocol_rejects(reordered)

    def test_extra_and_inspect_commands_are_rejected(self) -> None:
        extra = copy.deepcopy(self.events)
        item = {
            "type": "command_execution",
            "id": "extra-command",
            "command": "/usr/bin/python3 packet_reader.py overview",
        }
        extra.extend(
            [
                {"type": "item.started", "item": dict(item)},
                {
                    "type": "item.completed",
                    "item": {
                        **item,
                        "status": "completed",
                        "exit_code": 0,
                        "aggregated_output": self.outputs[0],
                    },
                },
            ]
        )
        self.assert_protocol_rejects(extra)

        inspect = copy.deepcopy(self.events)
        inspect_command = staging.render_codex_event_command(
            [
                "/usr/bin/python3",
                "packet_reader.py",
                "inspect",
                "--path",
                "official/x.py",
                "--start",
                "1",
                "--end",
                "1",
                "--manifest-sha256",
                self.requirements["requirements_sha256"],
            ]
        )
        for event in inspect[2:4]:
            event["item"]["command"] = inspect_command
        self.assert_protocol_rejects(inspect)

    def test_shell_metacharacter_commands_are_rejected(self) -> None:
        for suffix in (" ; true", " && true", " | true", " $(true)", " `true`"):
            with self.subTest(suffix=suffix):
                events = copy.deepcopy(self.events)
                for event in events[2:4]:
                    event["item"]["command"] += suffix
                self.assert_protocol_rejects(events)

    def test_overlapping_commands_are_rejected(self) -> None:
        events = copy.deepcopy(self.events)
        overlapped = [
            events[0],
            events[1],
            events[2],
            events[4],
            events[3],
            events[5],
            *events[6:],
        ]
        self.assert_protocol_rejects(overlapped)


if __name__ == "__main__":
    unittest.main()
