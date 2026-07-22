from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path


STEP = Path(__file__).resolve().parents[1]
SCRIPTS = STEP / "scripts"
sys.path.insert(0, str(SCRIPTS))

from rebuild_master_table import rebuild  # noqa: E402


def rows(name: str) -> list[dict[str, str]]:
    with (STEP / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class Step1OutputTests(unittest.TestCase):
    def test_baseline_cardinality(self) -> None:
        baseline = rows("submitted_baseline_manifest.csv")
        self.assertEqual(len(baseline), 1282)
        self.assertEqual(len({row["record_key"] for row in baseline}), 1282)
        self.assertEqual(
            Counter(row["benchmark"] for row in baseline),
            Counter({"agentdojo": 300, "androidworld": 82, "appworld": 300, "miniwob": 300, "tau3_retail": 300}),
        )
        self.assertTrue(all(row["public_artifact_byte_identical"] == "true" for row in baseline))

    def test_android_and_extension_cardinality(self) -> None:
        android = rows("androidworld_submitted41_ab_manifest.csv")
        contract = rows("androidworld_extension_contract.csv")
        active = rows("post_submission_extension_manifest.csv")
        self.assertEqual(len(android), 82)
        self.assertEqual(len({row["case_unit_id"] for row in android}), 41)
        self.assertEqual(len(contract), 218)
        self.assertEqual(len({row["slot_id"] for row in contract}), 218)
        self.assertEqual(Counter(row["extension_component"] for row in contract), Counter({"remaining59_ab": 118, "full100_c": 100}))
        self.assertEqual(active, [])

    def test_manifest_only_rebuild_matches(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            master = Path(directory) / "master.csv"
            summary = Path(directory) / "summary.csv"
            rebuild(STEP / "submitted_baseline_manifest.csv", master, summary, 1282)
            self.assertEqual(master.read_bytes(), (STEP / "submitted_master_table.csv").read_bytes())
            self.assertEqual(summary.read_bytes(), (STEP / "submitted_master_summary.csv").read_bytes())

    def test_summary_is_locked(self) -> None:
        with (STEP / "baseline_summary.json").open("r", encoding="utf-8") as handle:
            summary = json.load(handle)
        self.assertEqual(summary["baseline_record_count"], 1282)
        self.assertEqual(summary["extension_contract_slot_count"], 218)
        self.assertEqual(summary["extension_manifest_active_row_count"], 0)
        self.assertTrue(summary["all_decisive_files_match_submission_git_blobs"])

    def test_aggregator_contains_no_discovery(self) -> None:
        source = (SCRIPTS / "rebuild_master_table.py").read_text(encoding="utf-8")
        for token in (".glob(", ".rglob(", "os.walk(", "results/tables", "results_macros.tex"):
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
