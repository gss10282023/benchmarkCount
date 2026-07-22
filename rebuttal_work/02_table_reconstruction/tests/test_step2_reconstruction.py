from __future__ import annotations

import csv
import hashlib
import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path


STEP2 = Path(__file__).resolve().parents[1]
REPO_ROOT = STEP2.parents[1]
sys.path.insert(0, str(STEP2 / "scripts"))

from build_reconstruction import GENERATED_FILES, build  # noqa: E402


def read_csv(name: str) -> list[dict[str, str]]:
    with (STEP2 / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Step2ReconstructionTests(unittest.TestCase):
    def test_manifest_universe_and_final_labels(self) -> None:
        rows = read_csv("table_reconstruction_manifest.csv")
        self.assertEqual(len(rows), 1282)
        self.assertEqual(len({row["record_key"] for row in rows}), 1282)
        self.assertEqual(Counter(row["benchmark"] for row in rows), {
            "agentdojo": 300, "androidworld": 82, "appworld": 300, "miniwob": 300, "tau3_retail": 300,
        })
        self.assertEqual(Counter(row["evidence_label_submitted_as_printed"] for row in rows), {"S": 754, "F": 436, "U": 92})
        self.assertEqual(sum(row["final_label_source"] == "paper-source final_native_verdict" for row in rows), 63)
        self.assertEqual(sum(row["correction_applied_for_reconstruction"] == "true" for row in rows), 38)

    def test_table2_exact_values_and_invariants(self) -> None:
        rows = read_csv("table2_rebuilt.csv")
        self.assertEqual(len(rows), 19)
        totals = {row["benchmark_key"]: row for row in rows if row["agent_id"] == "all"}
        expected = {
            "androidworld": ("82", "61.0%", "13/28/41", "[15.9%, 65.9%]", "50.0%", "2"),
            "tau3_retail": ("300", "77.0%", "212/87/1", "[70.7%, 71.0%]", "0.3%", "24"),
            "appworld": ("300", "73.3%", "220/80/0", "[73.3%, 73.3%]", "0.0%", "0"),
            "agentdojo": ("300", "80.7%", "191/59/50", "[63.7%, 80.3%]", "16.7%", "4"),
            "miniwob": ("300", "40.0%", "118/182/0", "[39.3%, 39.3%]", "0.0%", "2"),
        }
        for benchmark, values in expected.items():
            row = totals[benchmark]
            self.assertEqual(tuple(row[field] for field in ("n", "native_score", "evidence_counts", "bound", "unknown_share", "benchmark_conflicts")), values)
        for row in rows:
            p_count, f_count, u_count = (int(row[field]) for field in ("p_count", "f_count", "u_count"))
            self.assertEqual(int(row["n"]), p_count + f_count + u_count)
        for benchmark, total in totals.items():
            agent_rows = [row for row in rows if row["benchmark_key"] == benchmark and row["agent_id"] != "all"]
            self.assertEqual(sum(int(row["n"]) for row in agent_rows), int(total["n"]))
            for field in ("p_count", "f_count", "u_count", "native_success_count", "benchmark_conflicts"):
                self.assertEqual(sum(int(row[field]) for row in agent_rows), int(total[field]))

    def test_table3_pairwise_rule(self) -> None:
        rows = {row["benchmark_key"]: row for row in read_csv("table3_rebuilt.csv")}
        self.assertEqual({key: (row["native_point_order"], row["separated_pairs"]) for key, row in rows.items()}, {
            "tau3_retail": ("C > G > D", "3/3"),
            "appworld": ("C > D > G", "3/3"),
            "agentdojo": ("C > D > G", "0/3"),
            "miniwob": ("C > G = D", "3/3"),
        })
        pairs = read_csv("table3_pairwise_details.csv")
        self.assertEqual(len(pairs), 12)
        self.assertEqual(sum(row["identified"] == "true" for row in pairs), 9)
        self.assertTrue(all(row["relation"] == "overlap" for row in pairs if row["benchmark"] == "agentdojo"))

    def test_table6_conflicts_are_record_derived(self) -> None:
        table6 = {row["benchmark_key"]: int(row["benchmark_conflicts"]) for row in read_csv("table6_rebuilt.csv")}
        self.assertEqual(table6, {"androidworld": 2, "tau3_retail": 24, "appworld": 0, "agentdojo": 4, "miniwob": 2})
        self.assertEqual(sum(table6.values()), 32)
        table2 = {row["benchmark_key"]: int(row["benchmark_conflicts"]) for row in read_csv("table2_rebuilt.csv") if row["agent_id"] == "all"}
        self.assertEqual(table6, table2)

    def test_table9_physical_row_and_legacy_candidate_rules(self) -> None:
        rows = {row["benchmark_key"]: (int(row["reviewed"]), int(row["corrected"])) for row in read_csv("table9_rebuilt.csv")}
        self.assertEqual(rows, {
            "androidworld": (8, 6), "tau3_retail": (53, 10), "appworld": (15, 12),
            "agentdojo": (14, 0), "miniwob": (36, 20),
        })
        self.assertEqual(sum(value[0] for value in rows.values()), 126)
        self.assertEqual(sum(value[1] for value in rows.values()), 48)
        items = read_csv("audit_review_items.csv")
        self.assertEqual(len(items), 126)
        mini_corrected = [row for row in items if row["benchmark"] == "miniwob" and row["adjudication_status"] == "corrected"]
        self.assertEqual(len(mini_corrected), 22)
        self.assertEqual(sum(row["legacy_table9_corrected_flag"] == "true" for row in mini_corrected), 20)
        agentdojo_corrected = [row for row in items if row["benchmark"] == "agentdojo" and row["adjudication_status"] == "corrected"]
        self.assertEqual(len(agentdojo_corrected), 3)
        self.assertTrue(all(row["legacy_table9_corrected_flag"] == "false" for row in agentdojo_corrected))
        tau_candidates = [row for row in items if row["benchmark"] == "tau3_retail" and row["legacy_table9_corrected_flag"] == "true"]
        self.assertEqual(Counter(row["human_audit_label"] for row in tau_candidates), {"SCORER_TOO_STRICT_NATIVE": 9, "SCORER_TOO_LENIENT_NATIVE": 1})
        self.assertTrue(all(row["adjudication_status"] == "preliminary" and not row["final_native_verdict"] for row in tau_candidates))

    def test_table13_structured_mapping(self) -> None:
        rows = read_csv("table13_rebuilt.csv")
        self.assertEqual(len(rows), 6)
        keys = [key for row in rows for key in row["record_keys"].split(";")]
        self.assertEqual(len(keys), 11)
        self.assertEqual(len(set(keys)), 11)
        manifest_keys = {row["record_key"] for row in read_csv("table_reconstruction_manifest.csv")}
        self.assertTrue(set(keys).issubset(manifest_keys))
        self.assertEqual([row["case_models"] for row in rows], [
            "B5/I5 / G", "W34/I4 / C+D; W34/I11 / D", "S12/I5 / all",
            "B11/I1 / C+D", "B13/I5 / C", "T7/I3 / G",
        ])

    def test_every_cell_has_exact_reconciliation_and_lineage(self) -> None:
        reconciliation = read_csv("printed_vs_rebuilt.csv")
        self.assertEqual(len(reconciliation), 263)
        self.assertTrue(all(row["status"] == "EXACT_MATCH" for row in reconciliation))
        self.assertEqual(read_csv("discrepancies.csv"), [])
        lineage = [json.loads(line) for line in (STEP2 / "cell_lineage.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(lineage), 263)
        self.assertEqual({row["cell_id"] for row in lineage}, {row["cell_id"] for row in reconciliation})
        self.assertTrue(all(len(row["input_sha256"]) == 64 and row["formula"] for row in lineage))

    def test_isolated_rebuild_is_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory(prefix="step2-test-") as temporary:
            isolated = Path(temporary)
            build(REPO_ROOT, isolated, STEP2 / "specs")
            self.assertEqual(
                {name: file_hash(STEP2 / name) for name in GENERATED_FILES},
                {name: file_hash(isolated / name) for name in GENERATED_FILES},
            )


if __name__ == "__main__":
    unittest.main()
