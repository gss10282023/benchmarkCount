#!/usr/bin/env python3
"""Production trust-boundary regressions for JSON bool/int confusion.

Every fixture is otherwise valid.  Hash-only seals are recomputed after the
adversarial JSON type substitution, so rejection cannot be attributed merely to
a stale outer digest.
"""

from __future__ import annotations

import hashlib
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import prepare_codex_draft_prelock_v6_clean2_hardened as preparer  # noqa: E402
import run_fresh_draft_wave_v6_clean2_hardened as launcher  # noqa: E402
import wave004_v6_clean2_hardened_common as common  # noqa: E402


def _write_json(path: Path, value: Any, *, mode: int | None = None) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if mode is not None:
        path.chmod(mode)


def _seal_sample_chain(samples: list[dict[str, Any]]) -> None:
    previous: str | None = None
    for sample in samples:
        sample["previous_sample_sha256"] = previous
        sample.pop("sample_sha256", None)
        sample["sample_sha256"] = common.canonical_sha256(sample)
        previous = sample["sample_sha256"]


def _write_samples(path: Path, samples: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(
            json.dumps(sample, ensure_ascii=False, sort_keys=True) + "\n"
            for sample in samples
        ),
        encoding="utf-8",
    )


class ProductionNumericCanonicalTrustTest(unittest.TestCase):
    def test_candidate_approval_false_cannot_impersonate_zero_model_calls(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="production-numeric-candidate-", dir=TESTS_DIR
        ) as temporary:
            path = Path(temporary).resolve() / "candidate_approval.json"
            core = {
                "schema_version": common.CANDIDATE_REVIEW_SCHEMA,
                "status": "approved_for_create_once_candidate_prelock",
                "candidate_generation_id": common.GENERATION_ID,
                "scripts": preparer.live_script_bindings(),
                "owner_nonce_sha256": hashlib.sha256(b"n" * 64).hexdigest(),
                "independent_final_go": False,
                "model_call_count": 0,
            }
            payload = common.add_self_hash(core, "approval_sha256")
            _write_json(path, payload, mode=0o444)
            observed, _binding = preparer.verify_reviewed_candidate_approval(path)
            self.assertEqual(observed["model_call_count"], 0)

            path.chmod(0o600)
            core["model_call_count"] = False
            payload = common.add_self_hash(core, "approval_sha256")
            _write_json(path, payload, mode=0o444)
            with self.assertRaises(common.Wave004V6Clean2HardenedError):
                preparer.verify_reviewed_candidate_approval(path)

    def test_launch_approval_false_cannot_impersonate_zero_model_calls(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="production-numeric-launch-", dir=TESTS_DIR
        ) as temporary:
            root = Path(temporary).resolve()
            prelock = {"prelock_sha256": "a" * 64}
            config = {
                "config_sha256": "b" * 64,
                "toolchain_snapshot": {"snapshot_sha256": "c" * 64},
                "staged_capacity": {"capacity_sha256": "d" * 64},
            }
            review_rows = []
            for index in range(2):
                reviewer_id = f"independent-reviewer-{index}"
                review = {
                    "schema_version": common.INDEPENDENT_PRELOCK_REVIEW_SCHEMA,
                    "status": "pass",
                    "reviewer_id": reviewer_id,
                    "independent": True,
                    "model_call_count": 0,
                    "candidate_generation_id": common.GENERATION_ID,
                    "prelock_sha256": prelock["prelock_sha256"],
                    "config_sha256": config["config_sha256"],
                    "snapshot_sha256": config["toolchain_snapshot"][
                        "snapshot_sha256"
                    ],
                    "capacity_sha256": config["staged_capacity"]["capacity_sha256"],
                }
                review = common.add_self_hash(review, "review_sha256")
                review_path = root / f"review_{index}.json"
                _write_json(review_path, review)
                binding = common.regular_file_binding(review_path)
                review_rows.append(
                    {
                        "reviewer_id": reviewer_id,
                        "status": "pass",
                        "independent": True,
                        "review_sha256": review["review_sha256"],
                        "report": binding,
                    }
                )
            approval_core = {
                "schema_version": common.LAUNCH_APPROVAL_SCHEMA,
                "status": "approved_after_independent_prelock_audit",
                "candidate_generation_id": common.GENERATION_ID,
                "model_call_count": 0,
                "authorize_first_model_call": True,
                "independent_final_go": True,
                "launch_nonce_sha256": hashlib.sha256(b"l" * 64).hexdigest(),
                "prelock_sha256": prelock["prelock_sha256"],
                "config_sha256": config["config_sha256"],
                "snapshot_sha256": config["toolchain_snapshot"]["snapshot_sha256"],
                "capacity_sha256": config["staged_capacity"]["capacity_sha256"],
                "independent_reviews": review_rows,
            }
            approval_path = root / "launch_approval.json"
            approval = common.add_self_hash(approval_core, "approval_sha256")
            _write_json(approval_path, approval, mode=0o444)
            observed = launcher.verify_launch_approval(
                approval_path, prelock=prelock, config=config
            )
            self.assertEqual(observed["model_call_count"], 0)

            approval_path.chmod(0o600)
            approval_core["model_call_count"] = False
            approval = common.add_self_hash(approval_core, "approval_sha256")
            _write_json(approval_path, approval, mode=0o444)
            with self.assertRaises(common.Wave004V6Clean2HardenedError):
                launcher.verify_launch_approval(
                    approval_path, prelock=prelock, config=config
                )

    def test_false_cannot_impersonate_empty_file_size_in_common_bindings(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="production-numeric-binding-", dir=TESTS_DIR
        ) as temporary:
            root = Path(temporary).resolve()
            empty = root / "empty.log"
            empty.write_bytes(b"")
            binding = common.regular_file_binding(empty)
            self.assertEqual(binding["size_bytes"], 0)
            tampered = dict(binding)
            tampered["size_bytes"] = False

            common.read_regular_bytes_bound(
                empty, label="empty fixture", expected_binding=binding
            )
            self.assertEqual(
                common.verify_regular_file_binding(binding, "empty fixture"), empty
            )
            common.verify_exact_directory_files(
                root,
                [
                    {
                        "relative_path": "empty.log",
                        "sha256": common.sha256_file(empty),
                        "size_bytes": 0,
                    }
                ],
                label="empty fixture tree",
            )

            with self.assertRaises(common.Wave004V6Clean2HardenedError):
                common.read_regular_bytes_bound(
                    empty, label="empty fixture", expected_binding=tampered
                )
            with self.assertRaises(common.Wave004V6Clean2HardenedError):
                common.verify_regular_file_binding(tampered, "empty fixture")
            with self.assertRaises(common.Wave004V6Clean2HardenedError):
                common.verify_exact_directory_files(
                    root,
                    [
                        {
                            "relative_path": "empty.log",
                            "sha256": common.sha256_file(empty),
                            "size_bytes": False,
                        }
                    ],
                    label="empty fixture tree",
                )

    def test_concurrency_chain_numeric_and_extra_field_faults_are_paired(self) -> None:
        case_order = [f"Case{index:03d}" for index in range(common.CASE_COUNT)]
        samples: list[dict[str, Any]] = []
        monotonic = 1
        for start in range(0, len(case_order), common.PARALLELISM):
            active_ids = case_order[start : start + common.PARALLELISM]
            active = [
                {
                    "pid": 20_000 + case_order.index(case_id),
                    "case_unit_id": case_id,
                    "argv_sha256": hashlib.sha256(
                        f"drafter:{case_id}".encode("utf-8")
                    ).hexdigest(),
                }
                for case_id in active_ids
            ]
            codex_active = [
                {
                    "pid": 30_000 + case_order.index(row["case_unit_id"]),
                    "drafter_pid": row["pid"],
                    "case_unit_id": row["case_unit_id"],
                    "workspace": f"/private/tmp/{row['case_unit_id']}",
                    "argv_sha256": hashlib.sha256(
                        f"codex:{row['case_unit_id']}".encode("utf-8")
                    ).hexdigest(),
                }
                for row in active
            ]
            samples.append(
                {
                    "schema_version": "androidworld_candidate116_wave004_v6_clean5_hardened_concurrency_sample/v1",
                    "sequence": len(samples),
                    "previous_sample_sha256": None,
                    "captured_at": f"2026-07-16T00:00:{len(samples):02d}+00:00",
                    "monotonic_ns": monotonic,
                    "batch_pid": 12345,
                    "active_case_attempt_count": len(active),
                    "active_case_attempts": active,
                    "active_codex_exec_count": len(codex_active),
                    "active_codex_execs": codex_active,
                    "foreign_drafting_processes": [],
                    "native_argv_validation": "pass",
                }
            )
            monotonic += 1
        # Zero/one-valued valid samples make bool/int substitution meaningful,
        # while the earlier samples still prove an exact peak of six and cover 116.
        for active_ids in (case_order[:1], []):
            active = [
                {
                    "pid": 20_000 + case_order.index(case_id),
                    "case_unit_id": case_id,
                    "argv_sha256": hashlib.sha256(
                        f"drafter:{case_id}".encode("utf-8")
                    ).hexdigest(),
                }
                for case_id in active_ids
            ]
            codex_active = [
                {
                    "pid": 30_000 + case_order.index(row["case_unit_id"]),
                    "drafter_pid": row["pid"],
                    "case_unit_id": row["case_unit_id"],
                    "workspace": f"/private/tmp/{row['case_unit_id']}",
                    "argv_sha256": hashlib.sha256(
                        f"codex:{row['case_unit_id']}".encode("utf-8")
                    ).hexdigest(),
                }
                for row in active
            ]
            samples.append(
                {
                    "schema_version": "androidworld_candidate116_wave004_v6_clean5_hardened_concurrency_sample/v1",
                    "sequence": len(samples),
                    "previous_sample_sha256": None,
                    "captured_at": f"2026-07-16T00:01:{len(samples):02d}+00:00",
                    "monotonic_ns": monotonic,
                    "batch_pid": 12345,
                    "active_case_attempt_count": len(active),
                    "active_case_attempts": active,
                    "active_codex_exec_count": len(codex_active),
                    "active_codex_execs": codex_active,
                    "foreign_drafting_processes": [],
                    "native_argv_validation": "pass",
                }
            )
            monotonic += 1
        _seal_sample_chain(samples)

        with tempfile.TemporaryDirectory(
            prefix="production-numeric-samples-", dir=TESTS_DIR
        ) as temporary:
            path = Path(temporary).resolve() / "samples.jsonl"
            _write_samples(path, samples)
            _observed, drafter_peak, codex_peak, covered = (
                launcher.read_and_verify_samples(path, case_order)
            )
            self.assertEqual((drafter_peak, codex_peak), (6, 6))
            self.assertEqual(covered, sorted(case_order))

            def sequence_false(rows: list[dict[str, Any]]) -> None:
                rows[0]["sequence"] = False

            def monotonic_true(rows: list[dict[str, Any]]) -> None:
                rows[0]["monotonic_ns"] = True

            def one_count_true(rows: list[dict[str, Any]]) -> None:
                rows[-2]["active_case_attempt_count"] = True

            def zero_count_false(rows: list[dict[str, Any]]) -> None:
                rows[-1]["active_codex_exec_count"] = False

            def extra_field(rows: list[dict[str, Any]]) -> None:
                rows[0]["unsealed_hint"] = "ignore"

            def active_row_extra_field(rows: list[dict[str, Any]]) -> None:
                rows[0]["active_case_attempts"][0]["unsealed_hint"] = "ignore"

            def codex_row_extra_field(rows: list[dict[str, Any]]) -> None:
                rows[0]["active_codex_execs"][0]["unsealed_hint"] = "ignore"

            mutations = {
                "sequence_zero_to_false": sequence_false,
                "monotonic_one_to_true": monotonic_true,
                "active_count_one_to_true": one_count_true,
                "codex_count_zero_to_false": zero_count_false,
                "extra_sample_field": extra_field,
                "extra_active_attempt_field": active_row_extra_field,
                "extra_codex_exec_field": codex_row_extra_field,
            }
            for name, mutate in mutations.items():
                with self.subTest(name=name):
                    # Paired positive control immediately before each delta.
                    launcher.read_and_verify_samples(path, case_order)
                    tampered = copy.deepcopy(samples)
                    mutate(tampered)
                    _seal_sample_chain(tampered)
                    _write_samples(path, tampered)
                    with self.assertRaises(common.Wave004V6Clean2HardenedError):
                        launcher.read_and_verify_samples(path, case_order)
                    _write_samples(path, samples)


if __name__ == "__main__":
    unittest.main()
