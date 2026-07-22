#!/usr/bin/env python3
"""Deterministically rebuild paper Tables 2/3/6/9/13.

The calculation universe is Step 1's 1,282-row artifact manifest.  The
paper-source companion commit supplies the frozen final-label ledger and the
printed table contract.  Printed macros and prose are comparison inputs only;
numeric outputs are aggregated from record/review-item rows.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import itertools
import json
import re
import subprocess
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable


PAPER_TEX = "revised_agent_benchmark_paper.tex"
PAPER_MACROS = "outputs/latex/results_macros.tex"
TABLE13_TEX = "outputs/latex/audit_case_insights_agentdojo.tex"
AUDIT_SUMMARY = "reviews/evidence_adjudication/audit_summary.csv"
LEDGER_PATHS = {
    "agentdojo": "reviews/evidence_adjudication/audit_items_agentdojo.csv",
    "androidworld": "reviews/evidence_adjudication/audit_items_androidworld.csv",
    "appworld": "reviews/evidence_adjudication/audit_items_appworld.csv",
    "miniwob": "reviews/evidence_adjudication/audit_items_miniwob.csv",
    "tau3_retail": "reviews/evidence_adjudication/audit_items_tau3_retail.csv",
}
AGENT_ALIAS = {"Agent A": "agent_a", "Agent B": "agent_b", "Agent C": "agent_c"}
NATIVE_LABEL = {"success": "S", "fail": "F"}
HARD_LABELS = {"S", "F"}
BENCHMARK_ISSUE = "BENCHMARK_OR_EVALUATOR_FALSE_SUCCESS"
TAU_PRINTED_CORRECTION_LABELS = {"SCORER_TOO_STRICT_NATIVE", "SCORER_TOO_LENIENT_NATIVE"}
ONE_DECIMAL = Decimal("0.1")
GENERATED_FILES = [
    "audit_review_items.csv",
    "cell_lineage.jsonl",
    "discrepancies.csv",
    "frozen_input_manifest.json",
    "paper_source_contract_validation.json",
    "printed_vs_rebuilt.csv",
    "table13_rebuilt.csv",
    "table13_rebuilt.json",
    "table13_rebuilt.tex",
    "table2_rebuilt.csv",
    "table2_rebuilt.json",
    "table2_rebuilt.tex",
    "table3_pairwise_details.csv",
    "table3_rebuilt.csv",
    "table3_rebuilt.json",
    "table3_rebuilt.tex",
    "table6_rebuilt.csv",
    "table6_rebuilt.json",
    "table6_rebuilt.tex",
    "table9_rebuilt.csv",
    "table9_rebuilt.json",
    "table9_rebuilt.tex",
    "table_reconstruction_manifest.csv",
    "table_reconstruction_manifest_summary.json",
    "tau3_scope_note.md",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def read_csv_file(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_csv_bytes(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline="")))


def git_bytes(repo_root: Path, commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=repo_root)


def git_blob_oid(repo_root: Path, commit: str, path: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", f"{commit}:{path}"], cwd=repo_root, text=True
    ).strip()


def format_ratio(numerator: int, denominator: int) -> str:
    if denominator <= 0 or numerator < 0 or numerator > denominator:
        raise ValueError(f"invalid ratio {numerator}/{denominator}")
    value = (Decimal(numerator) * Decimal(100) / Decimal(denominator)).quantize(
        ONE_DECIMAL, rounding=ROUND_HALF_UP
    )
    return f"{value:.1f}%"


def canonicalize_tex(value: str) -> str:
    """Canonical display form used for frozen-source comparisons."""

    text = value.strip()
    text = text.replace("Figure~\\ref{fig:recipe-motivation}", "Figure 2")
    text = text.replace("\\(", "").replace("\\)", "")
    text = text.replace("\\succ", ">")
    text = text.replace("\\%", "%").replace("\\$", "$")
    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"\\texttt\{([^{}]*)\}", r"\1", text)
    text = text.replace("~", " ").replace("{}", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_macros(data: bytes) -> dict[str, str]:
    macros: dict[str, str] = {}
    pattern = re.compile(r"^\\newcommand\{\\([A-Za-z0-9]+)\}\{(.*)\}\s*$")
    for line in data.decode("utf-8").splitlines():
        match = pattern.match(line)
        if match:
            macros[match.group(1)] = canonicalize_tex(match.group(2))
    return macros


def tex_escape(value: Any) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    return "".join(replacements.get(character, character) for character in text)


def write_tex_fragment(path: Path, table_id: str, columns: list[tuple[str, str]], rows: list[dict[str, Any]]) -> None:
    lines = [
        f"% Deterministically generated {table_id} body; presentation wrapper remains in the paper source.",
        " & ".join(tex_escape(header) for _, header in columns) + r" \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(tex_escape(row[column]) for column, _ in columns) + r" \\")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def stable_review_item_id(benchmark: str, row: dict[str, str]) -> str:
    identity = {
        "benchmark": benchmark,
        "case_unit_id": row["case_unit_id"],
        "agent_id": row["agent_id"],
        "layer": row["layer"],
        "trigger": row["trigger"],
    }
    return f"{benchmark}:{sha256_bytes(canonical_bytes(identity))[:20]}"


def expand_agents(raw: str) -> list[str]:
    agents: list[str] = []
    for token in raw.split(";"):
        name = token.strip()
        if name not in AGENT_ALIAS:
            raise ValueError(f"unknown ledger agent {name!r}")
        agents.append(AGENT_ALIAS[name])
    return agents


def extract_table13_rows(data: bytes) -> list[list[str]]:
    text = data.decode("utf-8")
    marker = r"\label{tab:agentdojo-case-insights}"
    if marker not in text:
        raise ValueError("Table 13 label is absent from frozen source")
    span = text.split(marker, 1)[1].split(r"\end{longtable}", 1)[0]
    span = span.split(r"\endhead", 1)[1]
    rows: list[list[str]] = []
    for raw_line in span.splitlines():
        line = raw_line.strip()
        if line == r"\bottomrule":
            break
        if not line.endswith(r"\\"):
            continue
        body = line[:-2].rstrip()
        cells = [canonicalize_tex(cell) for cell in body.split(" & ")]
        if len(cells) != 5:
            raise ValueError(f"Table 13 row does not have five cells: {line}")
        rows.append(cells)
    return rows


def order_from_scores(scores: dict[str, Fraction], symbols: dict[str, str]) -> str:
    tie_order = {"agent_a": 0, "agent_b": 1, "agent_c": 2}
    ordered = sorted(scores, key=lambda agent: (-scores[agent], tie_order[agent]))
    groups: list[list[str]] = []
    for agent in ordered:
        if not groups or scores[groups[-1][0]] != scores[agent]:
            groups.append([agent])
        else:
            groups[-1].append(agent)
    return " > ".join(" = ".join(symbols[agent] for agent in group) for group in groups)


def source_ref(commit: str, path: str, sha256: str, suffix: str = "") -> str:
    fragment = f"#{suffix}" if suffix else ""
    return f"git:{commit}:{path}{fragment}@sha256:{sha256}"


def build(repo_root: Path, output_dir: Path, specs_dir: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if specs_dir is None:
        specs_dir = Path(__file__).resolve().parents[1] / "specs"
    specs_dir = specs_dir.resolve()

    contracts_path = specs_dir / "table_contracts.json"
    table13_spec_path = specs_dir / "table13_row_spec.json"
    contracts = json.loads(contracts_path.read_text(encoding="utf-8"))
    table13_spec = json.loads(table13_spec_path.read_text(encoding="utf-8"))
    contract_sha = sha256_file(contracts_path)
    table13_spec_sha = sha256_file(table13_spec_path)

    lock_path = repo_root / "rebuttal_work/00_submission_repo_lock/submission_repo_lock.json"
    baseline_path = repo_root / "rebuttal_work/01_submission_baseline/submitted_baseline_manifest.csv"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    artifact_commit = lock["selection_basis"]["artifact_execution_commit"]["commit"]
    paper_commit = lock["selection_basis"]["paper_source_commit"]["commit"]
    if artifact_commit != contracts["artifact_commit"] or paper_commit != contracts["paper_source_commit"]:
        raise ValueError("table contract commits do not match the Step 1 repository lock")

    source_paths = [PAPER_TEX, PAPER_MACROS, TABLE13_TEX, AUDIT_SUMMARY, *LEDGER_PATHS.values()]
    source_data = {path: git_bytes(repo_root, paper_commit, path) for path in source_paths}
    source_hashes = {path: sha256_bytes(data) for path, data in source_data.items()}
    source_blobs = {path: git_blob_oid(repo_root, paper_commit, path) for path in source_paths}
    macros = parse_macros(source_data[PAPER_MACROS])
    paper_canonical = canonicalize_tex(source_data[PAPER_TEX].decode("utf-8"))

    baseline_rows = read_csv_file(baseline_path)
    baseline_sha = sha256_file(baseline_path)
    baseline_by_key = {row["record_key"]: row for row in baseline_rows}
    if len(baseline_rows) != 1282 or len(baseline_by_key) != 1282:
        raise ValueError("Step 1 baseline must contain 1,282 unique record keys")
    if any(row["table2_denominator"].lower() != "true" for row in baseline_rows):
        raise ValueError("all Step 1 baseline rows must belong to the Table 2 denominator")

    ledgers: dict[str, list[dict[str, Any]]] = {}
    item_by_id: dict[str, dict[str, Any]] = {}
    refs_by_record: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for benchmark, ledger_path in LEDGER_PATHS.items():
        items: list[dict[str, Any]] = []
        for data_row, raw in enumerate(read_csv_bytes(source_data[ledger_path]), start=1):
            item_id = stable_review_item_id(benchmark, raw)
            agents = expand_agents(raw["agent_id"])
            record_keys = [f"{benchmark}::{raw['case_unit_id']}::{agent}" for agent in agents]
            if any(key not in baseline_by_key for key in record_keys):
                missing = [key for key in record_keys if key not in baseline_by_key]
                raise ValueError(f"ledger item {item_id} has missing Step 1 keys: {missing}")
            item = {
                "review_item_id": item_id,
                "benchmark": benchmark,
                "source_data_row": data_row,
                "source_path": ledger_path,
                "source_sha256": source_hashes[ledger_path],
                "agents": agents,
                "record_keys": record_keys,
                "row": raw,
                "review_item_sha256": sha256_bytes(canonical_bytes(raw)),
            }
            if item_id in item_by_id:
                raise ValueError(f"duplicate stable review item id {item_id}")
            item_by_id[item_id] = item
            items.append(item)
            for key in record_keys:
                refs_by_record[key].append(item)
        ledgers[benchmark] = items

    physical_review_items = sum(len(items) for items in ledgers.values())
    expanded_review_links = sum(len(item["record_keys"]) for items in ledgers.values() for item in items)
    expanded_review_keys = {key for item in item_by_id.values() for key in item["record_keys"]}
    if (physical_review_items, expanded_review_links, len(expanded_review_keys)) != (126, 133, 133):
        raise ValueError("unexpected audit-ledger physical/expanded counts")

    reconstruction_rows: list[dict[str, Any]] = []
    record_hashes: dict[str, str] = {}
    final_override_links = 0
    changed_labels = 0
    for base in sorted(baseline_rows, key=lambda row: row["record_key"]):
        key = base["record_key"]
        refs = refs_by_record.get(key, [])
        final_items = [item for item in refs if item["row"]["final_native_verdict"].strip()]
        final_values = {item["row"]["final_native_verdict"].strip() for item in final_items}
        if len(final_values) > 1:
            raise ValueError(f"conflicting final labels for {key}: {sorted(final_values)}")
        raw_label = base["evidence_label_raw"]
        final_label = next(iter(final_values), raw_label)
        if final_label not in {"S", "F", "U"}:
            raise ValueError(f"invalid final label {final_label!r} for {key}")
        if final_items:
            final_override_links += 1
        changed = final_label != raw_label
        changed_labels += int(changed)

        benchmark = base["benchmark"]
        released_hard = NATIVE_LABEL[base["released_label"]]
        if benchmark == "tau3_retail":
            conflict = final_label in HARD_LABELS and final_label != released_hard
            conflict_items = [item for item in refs if item["row"]["trigger"] == "released_native_conflict"]
            if conflict and not conflict_items:
                raise ValueError(f"tau3 hard disagreement lacks ledger row: {key}")
            conflict_rule = "released/evidence hard-label disagreement; Unknown excluded"
        else:
            conflict_items = [item for item in refs if item["row"]["human_audit_label"] == BENCHMARK_ISSUE]
            conflict = bool(conflict_items)
            conflict_rule = "expanded ledger item labelled BENCHMARK_OR_EVALUATOR_FALSE_SUCCESS"

        all_item_ids = sorted(item["review_item_id"] for item in refs)
        final_item_ids = sorted(item["review_item_id"] for item in final_items)
        conflict_item_ids = sorted(item["review_item_id"] for item in conflict_items)
        ledger_paths = sorted({item["source_path"] for item in refs})
        ledger_hashes = sorted({item["source_sha256"] for item in refs})
        manifest_row = {
            "record_key": key,
            "benchmark": benchmark,
            "case_unit_id": base["case_unit_id"],
            "agent_id": base["agent_id"],
            "included": "true",
            "released_label": base["released_label"],
            "evidence_label_raw": raw_label,
            "evidence_label_submitted_as_printed": final_label,
            "final_label_source": "paper-source final_native_verdict" if final_items else "Step 1 evidence_label_raw",
            "correction_applied_for_reconstruction": str(changed).lower(),
            "conflict_flag_submitted_as_printed": str(conflict).lower(),
            "conflict_rule": conflict_rule,
            "review_item_ids": ";".join(all_item_ids),
            "final_label_review_item_ids": ";".join(final_item_ids),
            "conflict_review_item_ids": ";".join(conflict_item_ids),
            "selection_source_path": base["selection_source_path"],
            "selection_source_row": base["selection_source_row"],
            "raw_run_path": base["raw_run_path"],
            "raw_run_sha256": base["raw_run_sha256"],
            "native_evaluator_path": base["native_evaluator_path"],
            "native_evaluator_sha256": base["native_evaluator_sha256"],
            "score_path": base["score_path"],
            "score_sha256": base["score_sha256"],
            "step1_manifest_sha256": baseline_sha,
            "paper_ledger_paths": ";".join(ledger_paths),
            "paper_ledger_sha256s": ";".join(ledger_hashes),
            "scope_note": "paper printed-value reconstruction; no post-submission re-audit labels used",
        }
        record_hash = sha256_bytes(canonical_bytes(manifest_row))
        manifest_row["reconstruction_record_sha256"] = record_hash
        record_hashes[key] = record_hash
        reconstruction_rows.append(manifest_row)

    if final_override_links != 63 or changed_labels != 38:
        raise ValueError(f"unexpected final-label coverage: {final_override_links=} {changed_labels=}")

    reconstruction_fields = [
        "record_key", "benchmark", "case_unit_id", "agent_id", "included", "released_label",
        "evidence_label_raw", "evidence_label_submitted_as_printed", "final_label_source",
        "correction_applied_for_reconstruction", "conflict_flag_submitted_as_printed", "conflict_rule",
        "review_item_ids", "final_label_review_item_ids", "conflict_review_item_ids",
        "selection_source_path", "selection_source_row", "raw_run_path", "raw_run_sha256",
        "native_evaluator_path", "native_evaluator_sha256", "score_path", "score_sha256",
        "step1_manifest_sha256", "paper_ledger_paths", "paper_ledger_sha256s", "scope_note",
        "reconstruction_record_sha256",
    ]
    write_csv(output_dir / "table_reconstruction_manifest.csv", reconstruction_fields, reconstruction_rows)

    audit_output_rows: list[dict[str, Any]] = []
    corrected_item_ids_by_benchmark: dict[str, set[str]] = defaultdict(set)
    for benchmark in sorted(ledgers):
        for item in ledgers[benchmark]:
            raw = item["row"]
            if benchmark == "tau3_retail":
                corrected = raw["human_audit_label"] in TAU_PRINTED_CORRECTION_LABELS
                corrected_rule = "legacy printed candidate: native strict/lenient scorer label"
            else:
                corrected = raw["adjudication_status"] == "corrected" and raw["human_audit_label"] != BENCHMARK_ISSUE
                corrected_rule = "status=corrected excluding benchmark-facing false success"
            if corrected:
                corrected_item_ids_by_benchmark[benchmark].add(item["review_item_id"])
            audit_output_rows.append({
                "review_item_id": item["review_item_id"],
                "benchmark": benchmark,
                "source_data_row": item["source_data_row"],
                "case_unit_id": raw["case_unit_id"],
                "agent_id_raw": raw["agent_id"],
                "expanded_record_keys": ";".join(item["record_keys"]),
                "layer": raw["layer"],
                "trigger": raw["trigger"],
                "adjudication_status": raw["adjudication_status"],
                "human_audit_label": raw["human_audit_label"],
                "final_native_verdict": raw["final_native_verdict"],
                "legacy_table9_corrected_flag": str(corrected).lower(),
                "legacy_table9_corrected_rule": corrected_rule,
                "source_path": item["source_path"],
                "source_sha256": item["source_sha256"],
                "review_item_sha256": item["review_item_sha256"],
            })
    write_csv(
        output_dir / "audit_review_items.csv",
        [
            "review_item_id", "benchmark", "source_data_row", "case_unit_id", "agent_id_raw",
            "expanded_record_keys", "layer", "trigger", "adjudication_status", "human_audit_label",
            "final_native_verdict", "legacy_table9_corrected_flag", "legacy_table9_corrected_rule",
            "source_path", "source_sha256", "review_item_sha256",
        ],
        audit_output_rows,
    )

    by_benchmark: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in reconstruction_rows:
        by_benchmark[row["benchmark"]].append(row)

    lineage: list[dict[str, Any]] = []
    reconciliation: list[dict[str, str]] = []

    local_contract_ref = f"rebuttal_work/02_table_reconstruction/specs/table_contracts.json@sha256:{contract_sha}"
    local_table13_ref = f"rebuttal_work/02_table_reconstruction/specs/table13_row_spec.json@sha256:{table13_spec_sha}"
    paper_ref = source_ref(paper_commit, PAPER_TEX, source_hashes[PAPER_TEX])
    macros_ref = source_ref(paper_commit, PAPER_MACROS, source_hashes[PAPER_MACROS])

    def add_cell(
        *,
        table_id: str,
        paper_label: str,
        row_id: str,
        column_id: str,
        value: Any,
        expected: Any,
        record_keys: Iterable[str],
        formula: str,
        filter_predicate: str,
        source_references: list[str],
        review_item_ids: Iterable[str] = (),
        aggregation_unit: str = "record_key",
        expected_source: str = "frozen paper source",
    ) -> None:
        output_value = str(value)
        expected_value = str(expected)
        keys = sorted(set(record_keys))
        item_ids = sorted(set(review_item_ids))
        payload = {
            "record_keys": keys,
            "record_hashes": [record_hashes[key] for key in keys],
            "review_item_ids": item_ids,
            "review_item_hashes": [item_by_id[item_id]["review_item_sha256"] for item_id in item_ids],
            "formula": formula,
            "filter_predicate": filter_predicate,
            "source_references": source_references,
        }
        cell_id = f"{table_id}:{row_id}:{column_id}"
        lineage.append({
            "cell_id": cell_id,
            "table_id": table_id,
            "paper_label": paper_label,
            "row_id": row_id,
            "column_id": column_id,
            "output_value": output_value,
            "aggregation_unit": aggregation_unit,
            "input_record_keys": keys,
            "input_review_item_ids": item_ids,
            "filter_predicate": filter_predicate,
            "formula": formula,
            "source_references": source_references,
            "input_sha256": sha256_bytes(canonical_bytes(payload)),
        })
        status = "EXACT_MATCH" if output_value == expected_value else "DOCUMENTED_DISCREPANCY"
        reconciliation.append({
            "cell_id": cell_id,
            "table_id": table_id,
            "paper_label": paper_label,
            "row_id": row_id,
            "column_id": column_id,
            "expected_value": expected_value,
            "rebuilt_value": output_value,
            "status": status,
            "expected_source": expected_source,
            "normalization_rule": contracts["normalization"],
        })

    def add_headers(table_id: str, contract: dict[str, Any]) -> list[tuple[str, str]]:
        columns = [(str(column), str(header)) for column, header in contract["columns"]]
        for column, header in columns:
            add_cell(
                table_id=table_id,
                paper_label=contract["paper_label"],
                row_id="__header__",
                column_id=column,
                value=header,
                expected=header,
                record_keys=[],
                formula="fixed machine-readable column schema",
                filter_predicate="not applicable",
                source_references=[local_contract_ref, paper_ref],
                aggregation_unit="schema",
                expected_source="frozen table contract checked against paper source",
            )
        return columns

    # Table 2 -----------------------------------------------------------------
    t2_contract = contracts["tables"]["table2"]
    t2_columns = add_headers("table2", t2_contract)
    t2_rows: list[dict[str, Any]] = []
    t2_internal: dict[tuple[str, str | None], dict[str, Any]] = {}
    t2_expected: dict[str, dict[str, str]] = {}
    for benchmark_spec in t2_contract["benchmarks"]:
        benchmark = benchmark_spec["benchmark"]
        row_specs: list[tuple[str | None, str]] = [(None, benchmark_spec["macro_prefix"])] + [
            (agent, prefix) for agent, prefix in benchmark_spec["agents"]
        ]
        for agent, prefix in row_specs:
            selected = [row for row in by_benchmark[benchmark] if agent is None or row["agent_id"] == agent]
            keys = sorted(row["record_key"] for row in selected)
            n = len(selected)
            native_successes = sum(row["released_label"] == "success" for row in selected)
            label_counts = Counter(row["evidence_label_submitted_as_printed"] for row in selected)
            p_count, f_count, u_count = label_counts["S"], label_counts["F"], label_counts["U"]
            conflict_count = sum(row["conflict_flag_submitted_as_printed"] == "true" for row in selected)
            row_id = f"{benchmark}::{'all' if agent is None else agent}"
            benchmark_cell = benchmark_spec["display"] if agent is None else contracts["agent_display"][agent]
            meaning = benchmark_spec["meaning"] if agent is None else ""
            visible = {
                "benchmark": benchmark_cell,
                "n": str(n),
                "native_score": format_ratio(native_successes, n),
                "evidence_counts": f"{p_count}/{f_count}/{u_count}",
                "bound": f"[{format_ratio(p_count, n)}, {format_ratio(p_count + u_count, n)}]",
                "unknown_share": format_ratio(u_count, n),
                "benchmark_conflicts": str(conflict_count),
                "meaning": meaning,
            }
            expected = {
                "benchmark": benchmark_cell,
                "n": macros[f"{prefix}Total"],
                "native_score": macros[f"{prefix}NativeScore"],
                "evidence_counts": "/".join(macros[f"{prefix}{suffix}"] for suffix in ("Success", "Fail", "Unresolve")),
                "bound": f"[{macros[f'{prefix}Lower']}, {macros[f'{prefix}Upper']}]",
                "unknown_share": macros[f"{prefix}Width"],
                "benchmark_conflicts": macros[f"{prefix}LabelConflicts"],
                "meaning": meaning,
            }
            t2_expected[row_id] = expected
            table_row = {
                "row_id": row_id,
                "benchmark_key": benchmark,
                "agent_id": agent or "all",
                **visible,
                "p_count": p_count,
                "f_count": f_count,
                "u_count": u_count,
                "native_success_count": native_successes,
            }
            t2_rows.append(table_row)
            t2_internal[(benchmark, agent)] = {
                **table_row,
                "keys": keys,
                "lower": Fraction(p_count, n),
                "upper": Fraction(p_count + u_count, n),
                "native": Fraction(native_successes, n),
            }
            review_ids = {
                item_id
                for row in selected
                for item_id in row["review_item_ids"].split(";")
                if item_id
            }
            formulas = {
                "benchmark": "row label from frozen table contract",
                "n": "count(included records)",
                "native_score": "count(released_label == success) / N; round half-up to one decimal percent",
                "evidence_counts": "count(final label == S) / count(final label == F) / count(final label == U)",
                "bound": "[P/N, (P+U)/N]; round half-up to one decimal percent",
                "unknown_share": "U/N; round half-up to one decimal percent",
                "benchmark_conflicts": "count(conflict_flag_submitted_as_printed == true)",
                "meaning": "authored prose from frozen paper row contract",
            }
            filters = {
                "benchmark": f"benchmark == {benchmark}" + (f" and agent_id == {agent}" if agent else ""),
                "n": f"benchmark == {benchmark}" + (f" and agent_id == {agent}" if agent else ""),
                "native_score": "selected row records; numerator released_label == success",
                "evidence_counts": "selected row records grouped by submitted-as-printed final label",
                "bound": "selected row records grouped by submitted-as-printed final label",
                "unknown_share": "selected row records with submitted-as-printed final label U",
                "benchmark_conflicts": "selected row records with submitted-as-printed conflict flag true",
                "meaning": f"benchmark == {benchmark}; total row only" if agent is None else "agent row has intentionally blank merged prose cell",
            }
            for column, _ in t2_columns:
                add_cell(
                    table_id="table2",
                    paper_label=t2_contract["paper_label"],
                    row_id=row_id,
                    column_id=column,
                    value=visible[column],
                    expected=expected[column],
                    record_keys=keys,
                    formula=formulas[column],
                    filter_predicate=filters[column],
                    source_references=[local_contract_ref, macros_ref, paper_ref],
                    review_item_ids=review_ids,
                )

    t2_fields = ["row_id", "benchmark_key", "agent_id", *[column for column, _ in t2_columns], "p_count", "f_count", "u_count", "native_success_count"]
    write_csv(output_dir / "table2_rebuilt.csv", t2_fields, t2_rows)
    write_json(output_dir / "table2_rebuilt.json", {
        "schema_version": "step2_machine_table/v1", "table_id": "table2",
        "paper_label": t2_contract["paper_label"], "scope": contracts["scope"], "rows": t2_rows,
    })
    write_tex_fragment(output_dir / "table2_rebuilt.tex", "Table 2", t2_columns, t2_rows)

    # Table 3 -----------------------------------------------------------------
    t3_contract = contracts["tables"]["table3"]
    t3_columns = add_headers("table3", t3_contract)
    t3_rows: list[dict[str, Any]] = []
    pairwise_rows: list[dict[str, Any]] = []
    for benchmark_spec in t3_contract["benchmarks"]:
        benchmark = benchmark_spec["benchmark"]
        agents = ["agent_a", "agent_b", "agent_c"]
        native_scores = {agent: t2_internal[(benchmark, agent)]["native"] for agent in agents}
        lower = {agent: t2_internal[(benchmark, agent)]["lower"] for agent in agents}
        upper = {agent: t2_internal[(benchmark, agent)]["upper"] for agent in agents}
        native_order = order_from_scores(native_scores, contracts["agent_symbol"])
        separated = 0
        for left, right in itertools.combinations(agents, 2):
            if lower[left] > upper[right]:
                relation = f"{contracts['agent_symbol'][left]} > {contracts['agent_symbol'][right]}"
                identified = True
            elif lower[right] > upper[left]:
                relation = f"{contracts['agent_symbol'][right]} > {contracts['agent_symbol'][left]}"
                identified = True
            else:
                relation = "overlap"
                identified = False
            separated += int(identified)
            pair_keys = sorted(t2_internal[(benchmark, left)]["keys"] + t2_internal[(benchmark, right)]["keys"])
            pairwise_rows.append({
                "benchmark": benchmark,
                "left_agent": left,
                "right_agent": right,
                "left_interval": t2_internal[(benchmark, left)]["bound"],
                "right_interval": t2_internal[(benchmark, right)]["bound"],
                "identified": str(identified).lower(),
                "relation": relation,
                "record_keys_sha256": sha256_bytes(canonical_bytes(pair_keys)),
            })
        evidence_scores = {agent: lower[agent] for agent in agents}
        evidence_order = order_from_scores(evidence_scores, contracts["agent_symbol"])
        style = benchmark_spec["claim_style"]
        if style == "tau_all_separated":
            if separated != 3:
                raise ValueError("tau Table 3 claim template requires all pairs separated")
            claim = f"{evidence_order}; all pairs are separated in the current sample."
        elif style == "all_separated_matches_native":
            if separated != 3 or evidence_order != native_order:
                raise ValueError(f"{benchmark} no longer satisfies its frozen Table 3 claim template")
            claim = f"All pairs separate after audit; the supported order {evidence_order} matches the released point-score order."
        elif style == "none_separated":
            if separated != 0:
                raise ValueError(f"{benchmark} no longer satisfies zero-separated claim template")
            claim = "No strict leaderboard is identified; all three native pairwise orderings overlap under the evidence-supported bounds."
        elif style == "all_separated_changes_native":
            if separated != 3 or evidence_order == native_order:
                raise ValueError(f"{benchmark} no longer satisfies changed-order claim template")
            claim = f"All pairs separate after audit; the supported order is {evidence_order}, not the released {native_order}."
        else:
            raise ValueError(f"unknown Table 3 claim style {style}")
        row_id = benchmark
        visible = {
            "benchmark": benchmark_spec["display"],
            "native_point_order": native_order,
            "separated_pairs": f"{separated}/3",
            "evidence_supported_claim": claim,
        }
        expected_claim = benchmark_spec.get("expected_claim")
        if expected_claim is None:
            expected_claim = macros[benchmark_spec["expected_claim_macro"]]
        expected = {
            "benchmark": benchmark_spec["display"],
            "native_point_order": benchmark_spec["expected_native_order"],
            "separated_pairs": f"{macros[benchmark_spec['expected_pairs_macro']]}/3",
            "evidence_supported_claim": expected_claim,
        }
        table_row = {"row_id": row_id, "benchmark_key": benchmark, **visible}
        t3_rows.append(table_row)
        keys = sorted(row["record_key"] for row in by_benchmark[benchmark])
        formulas = {
            "benchmark": "row label from frozen table contract",
            "native_point_order": "rank agents by exact released-success fraction; equal fractions are ties",
            "separated_pairs": "for each of 3 pairs, identified iff LB_i > UB_j or LB_j > UB_i using exact fractions",
            "evidence_supported_claim": "fixed prose template filled from computed native/evidence order and separated-pair count",
        }
        for column, _ in t3_columns:
            add_cell(
                table_id="table3", paper_label=t3_contract["paper_label"], row_id=row_id, column_id=column,
                value=visible[column], expected=expected[column], record_keys=keys, formula=formulas[column],
                filter_predicate=f"benchmark == {benchmark}; AndroidWorld excluded because only two agents",
                source_references=[local_contract_ref, macros_ref, paper_ref],
            )
    write_csv(output_dir / "table3_rebuilt.csv", ["row_id", "benchmark_key", *[column for column, _ in t3_columns]], t3_rows)
    write_csv(
        output_dir / "table3_pairwise_details.csv",
        ["benchmark", "left_agent", "right_agent", "left_interval", "right_interval", "identified", "relation", "record_keys_sha256"],
        pairwise_rows,
    )
    write_json(output_dir / "table3_rebuilt.json", {
        "schema_version": "step2_machine_table/v1", "table_id": "table3",
        "paper_label": t3_contract["paper_label"], "scope": contracts["scope"], "rows": t3_rows,
    })
    write_tex_fragment(output_dir / "table3_rebuilt.tex", "Table 3", t3_columns, t3_rows)

    # Table 6 -----------------------------------------------------------------
    t6_contract = contracts["tables"]["table6"]
    t6_columns = add_headers("table6", t6_contract)
    t6_rows: list[dict[str, Any]] = []
    for row_spec in t6_contract["rows"]:
        benchmark = row_spec["benchmark"]
        selected = by_benchmark[benchmark]
        keys = sorted(row["record_key"] for row in selected)
        conflict_keys = sorted(row["record_key"] for row in selected if row["conflict_flag_submitted_as_printed"] == "true")
        conflict_item_ids = {
            item_id
            for row in selected
            for item_id in row["conflict_review_item_ids"].split(";")
            if item_id
        }
        visible = {
            "benchmark": row_spec["display"],
            "benchmark_conflicts": str(len(conflict_keys)),
            "conflict_type": row_spec["conflict_type"],
            "representative_evidence": row_spec["representative_evidence"],
        }
        expected_count = row_spec.get("expected_count")
        if expected_count is None:
            expected_count = macros[row_spec["expected_count_macro"]]
        expected = {**visible, "benchmark_conflicts": expected_count}
        table_row = {"row_id": benchmark, "benchmark_key": benchmark, **visible}
        t6_rows.append(table_row)
        formulas = {
            "benchmark": "row label from frozen table contract",
            "benchmark_conflicts": "count submitted-as-printed conflict record keys",
            "conflict_type": "authored taxonomy code from frozen paper row contract",
            "representative_evidence": "authored representative evidence from frozen paper row contract",
        }
        for column, _ in t6_columns:
            is_count = column == "benchmark_conflicts"
            add_cell(
                table_id="table6", paper_label=t6_contract["paper_label"], row_id=benchmark, column_id=column,
                value=visible[column], expected=expected[column], record_keys=keys if is_count else conflict_keys,
                formula=formulas[column],
                filter_predicate=(
                    f"benchmark == {benchmark}; conflict_flag_submitted_as_printed == true"
                    if is_count else f"benchmark == {benchmark}; supporting conflict records"
                ),
                source_references=[local_contract_ref, macros_ref, paper_ref],
                review_item_ids=conflict_item_ids,
            )
    write_csv(output_dir / "table6_rebuilt.csv", ["row_id", "benchmark_key", *[column for column, _ in t6_columns]], t6_rows)
    write_json(output_dir / "table6_rebuilt.json", {
        "schema_version": "step2_machine_table/v1", "table_id": "table6",
        "paper_label": t6_contract["paper_label"], "scope": contracts["scope"], "rows": t6_rows,
    })
    write_tex_fragment(output_dir / "table6_rebuilt.tex", "Table 6", t6_columns, t6_rows)

    # Table 9 -----------------------------------------------------------------
    t9_contract = contracts["tables"]["table9"]
    t9_columns = add_headers("table9", t9_contract)
    t9_rows: list[dict[str, Any]] = []
    for row_spec in t9_contract["rows"]:
        benchmark = row_spec["benchmark"]
        items = ledgers[benchmark]
        reviewed_ids = sorted(item["review_item_id"] for item in items)
        corrected_ids = sorted(corrected_item_ids_by_benchmark[benchmark])
        keys = sorted({key for item in items for key in item["record_keys"]})
        visible = {
            "benchmark": row_spec["display"],
            "reviewed": str(len(reviewed_ids)),
            "corrected": str(len(corrected_ids)),
            "main_findings": row_spec["main_findings"],
        }
        expected_reviewed = row_spec.get("expected_reviewed")
        if expected_reviewed is None:
            expected_reviewed = macros[row_spec["expected_reviewed_macro"]]
        expected_corrected = row_spec.get("expected_corrected")
        if expected_corrected is None:
            expected_corrected = macros[row_spec["expected_corrected_macro"]]
        expected = {**visible, "reviewed": expected_reviewed, "corrected": expected_corrected}
        table_row = {"row_id": benchmark, "benchmark_key": benchmark, **visible}
        t9_rows.append(table_row)
        formulas = {
            "benchmark": "row label from frozen table contract",
            "reviewed": "count physical audit-item CSV rows; grouped agents are not expanded for this count",
            "corrected": (
                "count items labelled SCORER_TOO_STRICT_NATIVE or SCORER_TOO_LENIENT_NATIVE under legacy printed candidate rule"
                if benchmark == "tau3_retail"
                else "count status=corrected items excluding BENCHMARK_OR_EVALUATOR_FALSE_SUCCESS"
            ),
            "main_findings": "authored findings prose from frozen paper row contract",
        }
        for column, _ in t9_columns:
            item_ids = corrected_ids if column == "corrected" else reviewed_ids
            add_cell(
                table_id="table9", paper_label=t9_contract["paper_label"], row_id=benchmark, column_id=column,
                value=visible[column], expected=expected[column], record_keys=keys, formula=formulas[column],
                filter_predicate=f"physical audit rows where benchmark == {benchmark}",
                source_references=[local_contract_ref, macros_ref, paper_ref, source_ref(paper_commit, LEDGER_PATHS[benchmark], source_hashes[LEDGER_PATHS[benchmark]])],
                review_item_ids=item_ids,
                aggregation_unit="review_item_row" if column in {"reviewed", "corrected"} else "record_key",
            )
    write_csv(output_dir / "table9_rebuilt.csv", ["row_id", "benchmark_key", *[column for column, _ in t9_columns]], t9_rows)
    write_json(output_dir / "table9_rebuilt.json", {
        "schema_version": "step2_machine_table/v1", "table_id": "table9",
        "paper_label": t9_contract["paper_label"], "scope": contracts["scope"], "rows": t9_rows,
    })
    write_tex_fragment(output_dir / "table9_rebuilt.tex", "Table 9", t9_columns, t9_rows)

    # Table 13 ----------------------------------------------------------------
    t13_contract = contracts["tables"]["table13"]
    t13_columns = add_headers("table13", t13_contract)
    frozen_table13_rows = extract_table13_rows(source_data[TABLE13_TEX])
    if len(frozen_table13_rows) != 6:
        raise ValueError("frozen Table 13 must have six body rows")
    t13_rows: list[dict[str, Any]] = []
    agentdojo_items = ledgers["agentdojo"]
    for index, row_spec in enumerate(table13_spec["rows"]):
        if row_spec["cells"] != frozen_table13_rows[index]:
            raise ValueError(f"Table 13 structured row spec differs from frozen TeX at row {index + 1}")
        keys: list[str] = []
        item_ids: list[str] = []
        for ref in row_spec["ledger_refs"]:
            item = agentdojo_items[int(ref["ledger_row"]) - 1]
            if item["row"]["case_unit_id"] != ref["case_unit_id"]:
                raise ValueError(f"Table 13 ledger row reference has wrong case: {ref}")
            if item["agents"] != ref["agents"]:
                raise ValueError(f"Table 13 ledger row reference has wrong expanded agents: {ref}")
            keys.extend(item["record_keys"])
            item_ids.append(item["review_item_id"])
        keys = sorted(set(keys))
        if len(keys) != sum(len(ref["agents"]) for ref in row_spec["ledger_refs"]):
            raise ValueError(f"Table 13 row {row_spec['row_id']} has duplicate record-key mappings")
        visible = dict(zip((column for column, _ in t13_columns), row_spec["cells"], strict=True))
        table_row = {"row_id": row_spec["row_id"], **visible, "record_keys": ";".join(keys)}
        t13_rows.append(table_row)
        for column, _ in t13_columns:
            add_cell(
                table_id="table13", paper_label=t13_contract["paper_label"], row_id=row_spec["row_id"], column_id=column,
                value=visible[column], expected=frozen_table13_rows[index][[name for name, _ in t13_columns].index(column)],
                record_keys=keys,
                formula="structured narrative row spec validated cell-by-cell against frozen TeX and mapped to ledger records",
                filter_predicate="record keys listed by this Table 13 row's ledger_refs",
                source_references=[local_table13_ref, source_ref(paper_commit, TABLE13_TEX, source_hashes[TABLE13_TEX]), source_ref(paper_commit, LEDGER_PATHS["agentdojo"], source_hashes[LEDGER_PATHS["agentdojo"]])],
                review_item_ids=item_ids,
            )
    write_csv(output_dir / "table13_rebuilt.csv", ["row_id", *[column for column, _ in t13_columns], "record_keys"], t13_rows)
    write_json(output_dir / "table13_rebuilt.json", {
        "schema_version": "step2_machine_table/v1", "table_id": "table13",
        "paper_label": t13_contract["paper_label"], "scope": contracts["scope"], "rows": t13_rows,
    })
    write_tex_fragment(output_dir / "table13_rebuilt.tex", "Table 13", t13_columns, t13_rows)

    # Validate authored contracts against the frozen source, independently of
    # the record-level aggregations.
    contract_checks: list[dict[str, str]] = []
    for table_id in ("table2", "table6", "table9"):
        contract = contracts["tables"][table_id]
        row_specs = contract.get("benchmarks", contract.get("rows", []))
        prose_fields = {
            "table2": ["meaning"],
            "table6": ["conflict_type", "representative_evidence"],
            "table9": ["main_findings"],
        }[table_id]
        for row_spec in row_specs:
            for field in prose_fields:
                value = row_spec[field]
                status = "EXACT_MATCH" if canonicalize_tex(value) in paper_canonical else "DOCUMENTED_DISCREPANCY"
                contract_checks.append({
                    "check_id": f"{table_id}:{row_spec['benchmark']}:{field}",
                    "expected": canonicalize_tex(value),
                    "status": status,
                    "source": paper_ref,
                })
    for row_spec in contracts["tables"]["table3"]["benchmarks"]:
        native_order = row_spec["expected_native_order"]
        contract_checks.append({
            "check_id": f"table3:{row_spec['benchmark']}:native_point_order",
            "expected": native_order,
            "status": "EXACT_MATCH" if native_order in paper_canonical else "DOCUMENTED_DISCREPANCY",
            "source": paper_ref,
        })
        if "expected_claim_macro" in row_spec:
            macro_name = row_spec["expected_claim_macro"]
            claim = macros[macro_name]
            source_ok = f"\\{macro_name}" in source_data[PAPER_TEX].decode("utf-8")
            claim_source = f"{paper_ref}; {source_ref(paper_commit, PAPER_MACROS, source_hashes[PAPER_MACROS], macro_name)}"
        else:
            claim = row_spec["expected_claim"]
            source_ok = claim in paper_canonical
            claim_source = paper_ref
        contract_checks.append({
            "check_id": f"table3:{row_spec['benchmark']}:evidence_supported_claim",
            "expected": claim,
            "status": "EXACT_MATCH" if source_ok else "DOCUMENTED_DISCREPANCY",
            "source": claim_source,
        })
    for index, cells in enumerate(frozen_table13_rows):
        for column_index, value in enumerate(cells):
            contract_checks.append({
                "check_id": f"table13:row{index + 1}:cell{column_index + 1}",
                "expected": value,
                "status": "EXACT_MATCH" if table13_spec["rows"][index]["cells"][column_index] == value else "DOCUMENTED_DISCREPANCY",
                "source": source_ref(paper_commit, TABLE13_TEX, source_hashes[TABLE13_TEX]),
            })
    write_json(output_dir / "paper_source_contract_validation.json", {
        "schema_version": "step2_paper_contract_validation/v1",
        "checks": contract_checks,
        "exact_matches": sum(check["status"] == "EXACT_MATCH" for check in contract_checks),
        "discrepancies": sum(check["status"] != "EXACT_MATCH" for check in contract_checks),
    })

    lineage.sort(key=lambda row: (row["table_id"], row["row_id"], row["column_id"]))
    with (output_dir / "cell_lineage.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for row in lineage:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    reconciliation.sort(key=lambda row: (row["table_id"], row["row_id"], row["column_id"]))
    reconciliation_fields = [
        "cell_id", "table_id", "paper_label", "row_id", "column_id", "expected_value",
        "rebuilt_value", "status", "expected_source", "normalization_rule",
    ]
    write_csv(output_dir / "printed_vs_rebuilt.csv", reconciliation_fields, reconciliation)
    discrepancies = [row for row in reconciliation if row["status"] != "EXACT_MATCH"]
    write_csv(output_dir / "discrepancies.csv", reconciliation_fields, discrepancies)

    frozen_inputs: list[dict[str, Any]] = [
        {
            "input_id": "step1_baseline_manifest", "kind": "local_frozen_output",
            "path": "rebuttal_work/01_submission_baseline/submitted_baseline_manifest.csv",
            "sha256": baseline_sha, "role": "1,282-record calculation universe",
        },
        {
            "input_id": "submission_repo_lock", "kind": "local_frozen_output",
            "path": "rebuttal_work/00_submission_repo_lock/submission_repo_lock.json",
            "sha256": sha256_file(lock_path), "role": "artifact and paper-source commit lock",
        },
        {
            "input_id": "table_contracts", "kind": "local_structured_spec",
            "path": "rebuttal_work/02_table_reconstruction/specs/table_contracts.json",
            "sha256": contract_sha, "role": "row order, headings, macro references, and authored prose contract",
        },
        {
            "input_id": "table13_row_spec", "kind": "local_structured_spec",
            "path": "rebuttal_work/02_table_reconstruction/specs/table13_row_spec.json",
            "sha256": table13_spec_sha, "role": "Table 13 row-to-ledger mapping",
        },
    ]
    for path in source_paths:
        frozen_inputs.append({
            "input_id": path.replace("/", "_"), "kind": "git_blob", "commit": paper_commit,
            "path": path, "git_blob_oid": source_blobs[path], "sha256": source_hashes[path],
            "role": (
                "printed-value/prose comparison source" if path in {PAPER_TEX, PAPER_MACROS, TABLE13_TEX}
                else "paper-source audit ledger" if path in LEDGER_PATHS.values()
                else "cross-check only; not used as an aggregation shortcut"
            ),
        })
    write_json(output_dir / "frozen_input_manifest.json", {
        "schema_version": "step2_frozen_inputs/v1",
        "scope": contracts["scope"],
        "artifact_commit": artifact_commit,
        "paper_source_companion_commit": paper_commit,
        "strict_submission_only_note": "The anonymous artifact branch does not contain the paper audit ledgers; this exact printed-value reconstruction transparently uses the separately locked paper-source companion commit.",
        "inputs": frozen_inputs,
    })

    final_counts = Counter(row["evidence_label_submitted_as_printed"] for row in reconstruction_rows)
    conflict_counts = Counter(
        row["benchmark"] for row in reconstruction_rows if row["conflict_flag_submitted_as_printed"] == "true"
    )
    summary = {
        "schema_version": "step2_reconstruction_summary/v1",
        "scope": contracts["scope"],
        "record_count": len(reconstruction_rows),
        "unique_record_keys": len({row["record_key"] for row in reconstruction_rows}),
        "physical_review_items": physical_review_items,
        "expanded_review_links": expanded_review_links,
        "unique_reviewed_record_keys": len(expanded_review_keys),
        "nonblank_final_label_links": final_override_links,
        "changed_final_labels": changed_labels,
        "final_label_counts": dict(sorted(final_counts.items())),
        "conflict_counts": dict(sorted(conflict_counts.items())),
        "table_row_counts": {"table2": len(t2_rows), "table3": len(t3_rows), "table6": len(t6_rows), "table9": len(t9_rows), "table13": len(t13_rows)},
        "reconciled_cells_including_headers": len(reconciliation),
        "exact_match_cells": sum(row["status"] == "EXACT_MATCH" for row in reconciliation),
        "documented_discrepancy_cells": len(discrepancies),
    }
    write_json(output_dir / "table_reconstruction_manifest_summary.json", summary)

    tau_items = ledgers["tau3_retail"]
    tau_strict = sum(item["row"]["human_audit_label"] == "SCORER_TOO_STRICT_NATIVE" for item in tau_items)
    tau_lenient = sum(item["row"]["human_audit_label"] == "SCORER_TOO_LENIENT_NATIVE" for item in tau_items)
    tau_note = f"""# τ³ 投稿打印口径说明

本目录只重建论文投稿时打印的五张表，不裁决候选修正后来是否真正应用。

- 表2的 τ³ 记录来自步骤1冻结的300条记录。审核台账的 `final_native_verdict` 全为空，因此生成器保留记录标签，得到 `212/87/1`。
- 表6的 `24` 是 released 标签与 evidence 标签之间的硬 S/F 分歧；唯一 Unknown 分歧被排除。它是投稿时的冲突计数规则，不等同于24条后续严格确认的基准错误。
- 表9的 `10` 按投稿打印规则计数：`SCORER_TOO_STRICT_NATIVE` {tau_strict} 条，加 `SCORER_TOO_LENIENT_NATIVE` {tau_lenient} 条。这些条目在台账中仍是 preliminary，生成器只恢复表9的历史打印数字，不把它们写回表2。

因此，`212/87/1`、`24`、`10` 可以同时由固定脚本重建；三者回答的是不同问题。
"""
    (output_dir / "tau3_scope_note.md").write_text(tau_note, encoding="utf-8", newline="\n")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    default_repo_root = Path(__file__).resolve().parents[3]
    parser.add_argument("--repo-root", type=Path, default=default_repo_root)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--specs-dir", type=Path)
    args = parser.parse_args()
    summary = build(args.repo_root, args.output_dir, args.specs_dir)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
