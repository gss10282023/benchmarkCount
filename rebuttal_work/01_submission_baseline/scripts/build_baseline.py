#!/usr/bin/env python3
"""Freeze the 1,282-record submitted baseline and Android extension contract.

The four 300-record benchmarks are selected by their frozen flat CSVs.  The
AndroidWorld records are selected by the submitted public-package MANIFEST,
expanded only over Agent A and Agent B.  Working-result directories are never
used for inclusion decisions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


SUBMISSION_COMMIT = "ffd9ff4e706d85ff2d12e60f087cde664dbae433"
EXPECTED_LABEL_COUNTS = {
    "agentdojo": {"S": 195, "F": 55, "U": 50},
    "androidworld": {"S": 19, "F": 26, "U": 37},
    "appworld": {"S": 208, "F": 91, "U": 1},
    "miniwob": {"S": 120, "F": 168, "U": 12},
    "tau3_retail": {"S": 212, "F": 87, "U": 1},
}
AGENTS = ("agent_a", "agent_b", "agent_c")
AGENT_DISPLAY = {"agent_a": "Agent A", "agent_b": "Agent B", "agent_c": "Agent C"}
AGENT_NORMALIZED = {display: normalized for normalized, display in AGENT_DISPLAY.items()}


CONFIG = {
    "agentdojo": {
        "bundle": "paper_result_packages/agentdojo_case_bundle_openrouter_gpt54_high",
        "selector": "global/agentdojo_scores_flat.csv",
        "case_dir": lambda case_id: case_id.replace(":", "_"),
        "checklist": lambda case_dir, row: case_dir / "draft" / "checklist.yaml",
    },
    "appworld": {
        "bundle": "paper_result_packages/appworld_case_bundle_openrouter",
        "selector": "global/appworld_scores_flat.csv",
        "case_dir": lambda case_id: case_id,
        "checklist": lambda case_dir, row: case_dir / "draft" / "checklist.yaml",
    },
    "miniwob": {
        "bundle": "paper_result_packages/miniwob_case_bundle",
        "selector": "global/miniwob_scores_flat.csv",
        "case_dir": lambda case_id: case_id,
        "checklist": lambda case_dir, row: miniwob_checklist_path(case_dir, row),
    },
    "tau3_retail": {
        "bundle": "paper_result_packages/tau3_retail_case_bundle",
        "selector": "global/tau3_retail_scores_flat.csv",
        "case_dir": lambda case_id: case_id,
        "checklist": lambda case_dir, row: case_dir / "draft" / "checklist.yaml",
    },
}

MANIFEST_FIELDS = [
    "record_key",
    "raw_record_id",
    "raw_record_slot_id",
    "raw_run_id",
    "benchmark",
    "case_unit_id",
    "agent_id",
    "raw_run_native_label",
    "evidence_label_raw",
    "stronger_label_raw",
    "released_label",
    "table2_denominator",
    "table2_inclusion_basis",
    "submission_status",
    "selection_source_path",
    "selection_source_row",
    "raw_run_path",
    "raw_run_sha256",
    "raw_run_git_blob_oid",
    "native_evaluator_path",
    "native_evaluator_sha256",
    "native_evaluator_git_blob_oid",
    "score_path",
    "score_sha256",
    "score_git_blob_oid",
    "score_manifest_path",
    "score_manifest_sha256",
    "score_manifest_git_blob_oid",
    "checklist_path",
    "checklist_sha256",
    "checklist_git_blob_oid",
    "artifact_manifest_path",
    "artifact_manifest_sha256",
    "artifact_manifest_git_blob_oid",
    "public_artifact_byte_identical",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha1_git_blob(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def miniwob_checklist_path(case_dir: Path, row: dict[str, str]) -> Path:
    source = placeholder_relative(row["batch.checklist_path"])
    parts = PurePosixPath(source).parts
    try:
        index = parts.index("drafts")
    except ValueError as exc:
        raise ValueError(f"MiniWoB checklist path lacks drafts component: {source}") from exc
    return case_dir / "drafts" / Path(*parts[index + 1 :])


def placeholder_relative(value: str) -> str:
    normalized = value.replace("\\", "/")
    prefix = "<REPO_ROOT>/"
    if normalized.startswith(prefix):
        normalized = normalized[len(prefix) :]
    if normalized.startswith("/") or ".." in PurePosixPath(normalized).parts:
        raise ValueError(f"path is not a repository-relative placeholder path: {value}")
    return normalized


def package_score_path(case_dir: Path, row: dict[str, str]) -> Path:
    source = PurePosixPath(placeholder_relative(row["score.json_path"]))
    run_dir = row["run_dir_name"]
    try:
        index = source.parts.index(run_dir)
    except ValueError as exc:
        raise ValueError(f"score path does not contain run directory {run_dir}: {source}") from exc
    suffix = source.parts[index + 1 :]
    if not suffix or suffix[-1] != "score.json":
        raise ValueError(f"invalid score suffix: {suffix}")
    return case_dir / "score_runs" / run_dir / Path(*suffix)


def evaluator_path(adapter_dir: Path, score: dict[str, Any]) -> Path:
    source = str(score["released_evaluator_label"]["source"]).split("::", 1)[0]
    if not source.startswith("evidence/"):
        raise ValueError(f"released evaluator source is outside evidence root: {source}")
    return adapter_dir / Path(source.removeprefix("evidence/"))


def validate_raw(raw: dict[str, Any], benchmark: str, case_id: str, agent_display: str) -> None:
    expected = {
        "domain": benchmark,
        "case_unit_id": case_id,
        "agent_id": agent_display,
        "status": "COMPLETED",
        "diagnostic_status": "completed",
        "final_attempt": True,
        "phase": "full",
    }
    for field, value in expected.items():
        if str(raw.get(field)) != str(value):
            raise ValueError(f"raw record mismatch for {benchmark}/{case_id}/{agent_display}: {field}")


def base_record(
    root: Path,
    benchmark: str,
    case_id: str,
    agent_id: str,
    selection_source: Path,
    selection_row: int,
    raw_path: Path,
    native_path: Path,
    score_path: Path,
    score_manifest_path: Path,
    checklist_path: Path,
    artifact_manifest_path: Path,
) -> dict[str, str]:
    agent_display = AGENT_DISPLAY[agent_id]
    score = load_json(score_path)
    score_manifest = load_json(score_manifest_path)
    raw = load_json(raw_path)
    validate_raw(raw, benchmark, case_id, agent_display)

    if str(score.get("case_unit_id")) != case_id:
        raise ValueError(f"score case mismatch: {score_path}")
    if str(score_manifest.get("case_unit_id")) != case_id:
        raise ValueError(f"score manifest case mismatch: {score_manifest_path}")
    if score_manifest.get("agent_id") != agent_display:
        raise ValueError(f"score manifest agent mismatch: {score_manifest_path}")
    if sha256_file(checklist_path) != score_manifest.get("checklist_sha256"):
        raise ValueError(f"checklist hash mismatch: {checklist_path}")
    if sha256_file(artifact_manifest_path) != raw.get("artifact_manifest_sha256"):
        raise ValueError(f"artifact manifest hash mismatch: {artifact_manifest_path}")

    evidence_label = str(score["native"]["verdict"])
    stronger_label = str((score.get("stronger") or {}).get("verdict") or "NA").replace("N/A", "NA")
    if evidence_label not in {"S", "F", "U"}:
        raise ValueError(f"invalid evidence label {evidence_label}: {score_path}")
    if stronger_label not in {"S", "F", "U", "NA"}:
        raise ValueError(f"invalid stronger label {stronger_label}: {score_path}")

    paths = {
        "raw_run": raw_path,
        "native_evaluator": native_path,
        "score": score_path,
        "score_manifest": score_manifest_path,
        "checklist": checklist_path,
        "artifact_manifest": artifact_manifest_path,
    }
    row: dict[str, str] = {
        "record_key": f"{benchmark}::{case_id}::{agent_id}",
        "raw_record_id": str(raw["record_id"]),
        "raw_record_slot_id": str(raw["record_slot_id"]),
        "raw_run_id": str(raw["run_id"]),
        "benchmark": benchmark,
        "case_unit_id": case_id,
        "agent_id": agent_id,
        "raw_run_native_label": str(raw.get("native_label", "")),
        "evidence_label_raw": evidence_label,
        "stronger_label_raw": stronger_label,
        "released_label": str(score["released_evaluator_label"]["value"]),
        "table2_denominator": "true",
        "table2_inclusion_basis": "membership_in_frozen_submitted_public_package_selector",
        "submission_status": "submitted",
        "selection_source_path": relative(root, selection_source),
        "selection_source_row": str(selection_row),
        "public_artifact_byte_identical": "pending",
    }
    for name, path in paths.items():
        row[f"{name}_path"] = relative(root, path)
        row[f"{name}_sha256"] = sha256_file(path)
        row[f"{name}_git_blob_oid"] = "pending"
    return row


def records_from_flat_selectors(root: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for benchmark, config in CONFIG.items():
        bundle = root / str(config["bundle"])
        selector = bundle / str(config["selector"])
        rows = read_csv(selector)
        if len(rows) != 300:
            raise ValueError(f"{benchmark} selector must contain 300 records, found {len(rows)}")
        selector_keys = {(row["case_unit_id"], row["agent_id"]) for row in rows}
        if len(selector_keys) != 300:
            raise ValueError(f"{benchmark} selector keys are not unique")

        for row_number, source_row in enumerate(rows, start=1):
            case_id = str(source_row["case_unit_id"])
            agent_id = AGENT_NORMALIZED[source_row["agent_id"]]
            case_dir = bundle / "cases" / config["case_dir"](case_id)
            score_path = package_score_path(case_dir, source_row)
            score_manifest_path = score_path.with_name("score_manifest.json")
            checklist_path = config["checklist"](case_dir, source_row)
            raw_path = case_dir / "full_runs" / source_row["run_dir_name"] / "adapter" / "raw_run.json"
            adapter_dir = raw_path.parent
            native_path = evaluator_path(adapter_dir, load_json(score_path))
            artifact_manifest_path = adapter_dir / "artifact_manifest.json"
            required = [
                case_dir,
                score_path,
                score_manifest_path,
                checklist_path,
                raw_path,
                native_path,
                artifact_manifest_path,
            ]
            missing = [str(path) for path in required if not path.exists()]
            if missing:
                raise FileNotFoundError(f"missing submitted artifacts: {missing}")
            if benchmark == "appworld" and "codex-gpt-5.4-high" not in score_path.as_posix():
                raise ValueError(f"AppWorld selector chose noncanonical scorer: {score_path}")
            records.append(
                base_record(
                    root,
                    benchmark,
                    case_id,
                    agent_id,
                    selector,
                    row_number,
                    raw_path,
                    native_path,
                    score_path,
                    score_manifest_path,
                    checklist_path,
                    artifact_manifest_path,
                )
            )
    return records


def records_from_android_manifest(root: Path) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    bundle = root / "paper_result_packages/androidworld_both_agents_scored_cases_official_full100"
    selector = bundle / "MANIFEST.json"
    manifest = load_json(selector)
    cases = manifest.get("cases")
    if manifest.get("case_count") != 41 or not isinstance(cases, list) or len(cases) != 41:
        raise ValueError("AndroidWorld public manifest must contain exactly 41 cases")
    if len({entry["case"] for entry in cases}) != 41:
        raise ValueError("AndroidWorld public manifest contains duplicate cases")

    records: list[dict[str, str]] = []
    for entry in sorted(cases, key=lambda item: (int(item["selection_rank"]), item["case"])):
        case_id = str(entry["case"])
        case_dir = bundle / "cases" / case_id
        checklist_path = case_dir / "draft" / "checklist.yaml"
        checklist_hash = sha256_file(checklist_path)
        for agent_id in ("agent_a", "agent_b"):
            score_path = (
                case_dir
                / "score"
                / agent_id
                / f"{case_id}__chk_{checklist_hash[:8]}"
                / "codex-gpt-5.4-high"
                / "score.json"
            )
            score_manifest_path = score_path.with_name("score_manifest.json")
            adapter_dir = case_dir / "full" / agent_id / "adapter"
            raw_path = adapter_dir / "raw_run.json"
            native_path = evaluator_path(adapter_dir, load_json(score_path))
            artifact_manifest_path = adapter_dir / "artifact_manifest.json"
            required = [
                score_path,
                score_manifest_path,
                raw_path,
                native_path,
                artifact_manifest_path,
                checklist_path,
            ]
            missing = [str(path) for path in required if not path.exists()]
            if missing:
                raise FileNotFoundError(f"missing submitted Android artifacts: {missing}")
            records.append(
                base_record(
                    root,
                    "androidworld",
                    case_id,
                    agent_id,
                    selector,
                    int(entry["index"]),
                    raw_path,
                    native_path,
                    score_path,
                    score_manifest_path,
                    checklist_path,
                    artifact_manifest_path,
                )
            )
    return records, cases


def git_blob_oids(root: Path, commit: str, paths: list[str]) -> dict[str, str]:
    if len(paths) != len(set(paths)):
        paths = list(dict.fromkeys(paths))
    process = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
        cwd=root,
        input="".join(f"{commit}:{path}\n" for path in paths),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    lines = process.stdout.splitlines()
    if len(lines) != len(paths):
        raise RuntimeError("git cat-file returned an unexpected number of rows")
    result: dict[str, str] = {}
    for path, line in zip(paths, lines):
        parts = line.split()
        if len(parts) != 3 or parts[1] != "blob":
            raise ValueError(f"path is missing from submission commit {commit}: {path} ({line})")
        result[path] = parts[0]
    return result


def attach_public_blob_provenance(root: Path, rows: list[dict[str, str]]) -> None:
    artifact_names = (
        "raw_run",
        "native_evaluator",
        "score",
        "score_manifest",
        "checklist",
        "artifact_manifest",
    )
    paths = [row[f"{name}_path"] for row in rows for name in artifact_names]
    oids = git_blob_oids(root, SUBMISSION_COMMIT, paths)
    for row in rows:
        identical = True
        for name in artifact_names:
            path_string = row[f"{name}_path"]
            oid = oids[path_string]
            row[f"{name}_git_blob_oid"] = oid
            if sha1_git_blob(root / path_string) != oid:
                identical = False
        row["public_artifact_byte_identical"] = "true" if identical else "false"
        if not identical:
            raise ValueError(f"working artifact differs from submission Git blob: {row['record_key']}")


def extension_contract(
    root: Path, submitted_cases: set[str]
) -> tuple[list[dict[str, str]], dict[str, Any], Path]:
    source = root / "experiments/official_splits/androidworld_full100/androidworld_selected_task_sources.json"
    frozen = load_json(source)
    items = frozen.get("items")
    if frozen.get("selected_count") != 100 or not isinstance(items, list) or len(items) != 100:
        raise ValueError("AndroidWorld official full100 source must contain exactly 100 cases")
    official = {str(item["case_unit_id"]): item for item in items}
    if len(official) != 100:
        raise ValueError("AndroidWorld official full100 source contains duplicate cases")
    if not submitted_cases < set(official):
        raise ValueError("submitted Android cases are not a strict subset of official100")
    remaining = set(official) - submitted_cases
    if len(remaining) != 59:
        raise ValueError(f"expected 59 remaining Android cases, found {len(remaining)}")

    ordered = sorted(official.values(), key=lambda item: (int(item["selection_rank"]), item["case_unit_id"]))
    rows: list[dict[str, str]] = []
    slot_order = 1
    for item in ordered:
        case_id = str(item["case_unit_id"])
        if case_id not in remaining:
            continue
        for agent_id in ("agent_a", "agent_b"):
            rows.append(
                {
                    "slot_order": str(slot_order),
                    "slot_id": f"androidworld::{case_id}::{agent_id}",
                    "case_selection_rank": str(item["selection_rank"]),
                    "case_unit_id": case_id,
                    "agent_id": agent_id,
                    "extension_component": "remaining59_ab",
                    "submission_status": "post_submission_target",
                    "expected_artifact_state": "pending",
                    "append_gate": "step4b_slot_acceptance",
                }
            )
            slot_order += 1
    for item in ordered:
        case_id = str(item["case_unit_id"])
        rows.append(
            {
                "slot_order": str(slot_order),
                "slot_id": f"androidworld::{case_id}::agent_c",
                "case_selection_rank": str(item["selection_rank"]),
                "case_unit_id": case_id,
                "agent_id": "agent_c",
                "extension_component": "full100_c",
                "submission_status": "post_submission_target",
                "expected_artifact_state": "pending",
                "append_gate": "step4b_slot_acceptance",
            }
        )
        slot_order += 1
    if len(rows) != 218 or len({row["slot_id"] for row in rows}) != 218:
        raise ValueError("AndroidWorld extension contract is not exactly 218 unique slots")
    return rows, frozen, source


def legacy_path(root: Path, value: str) -> Path | None:
    normalized = value.replace("\\", "/")
    if normalized.startswith("<REPO_ROOT>/"):
        return root / normalized.removeprefix("<REPO_ROOT>/")
    candidate = Path(normalized)
    if not candidate.is_absolute():
        return root / candidate
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def legacy_crosswalk(root: Path, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in rows:
        score_manifest = load_json(root / row["score_manifest_path"])
        score = load_json(root / row["score_path"])
        evidence_root = legacy_path(root, str(score_manifest["evidence_input_path"]))
        evaluator_source = str(score["released_evaluator_label"]["source"]).split("::", 1)[0]
        if not evaluator_source.startswith("evidence/"):
            raise ValueError(f"bad evaluator source in {row['record_key']}")
        candidates = {
            "raw_run": evidence_root / "raw_run.json" if evidence_root else None,
            "native_evaluator": evidence_root / evaluator_source.removeprefix("evidence/") if evidence_root else None,
            "score": legacy_path(root, str(score_manifest["outputs"]["json"])),
            "score_manifest": legacy_path(root, str(score_manifest["outputs"]["manifest"])),
            "checklist": legacy_path(root, str(score_manifest["checklist_path"])),
            "artifact_manifest": evidence_root / "artifact_manifest.json" if evidence_root else None,
        }
        crosswalk: dict[str, str] = {"record_key": row["record_key"]}
        for name, candidate in candidates.items():
            crosswalk[f"legacy_{name}_path"] = relative(root, candidate) if candidate and candidate.exists() else ""
            if candidate is None or not candidate.exists():
                status = "missing"
            elif sha256_file(candidate) == row[f"{name}_sha256"]:
                status = "byte_identical"
            else:
                status = "content_differs_noncanonical_legacy"
            crosswalk[f"{name}_status"] = status
        output.append(crosswalk)
    return output


def exclusion_rows(root: Path) -> list[dict[str, str]]:
    android_flat = root / "results/scores/full/androidworld/androidworld_scores_flat.csv"
    android_flat_rows = len(read_csv(android_flat)) if android_flat.exists() else 0
    return [
        {
            "scope": "results/**",
            "observed_count": "working tree",
            "rule": "exclude_as_source",
            "reason": "README identifies results as working/intermediate output; only frozen public-package selectors may define submitted membership.",
        },
        {
            "scope": "results/full/androidworld/**/*__infra_failed*",
            "observed_count": "9",
            "rule": "exclude_path_class",
            "reason": "Infrastructure-failed attempts are outside the submitted selector even if an inner raw_run says COMPLETED.",
        },
        {
            "scope": "results/full/androidworld/**/*__retry_archived*",
            "observed_count": "7",
            "rule": "exclude_path_class",
            "reason": "Archived retries are superseded attempts and may not enter a denominator.",
        },
        {
            "scope": "results/full/androidworld/**/*__env_failed* or *__interrupted*",
            "observed_count": "2",
            "rule": "exclude_path_class",
            "reason": "Environment-failed and interrupted attempts are noncanonical.",
        },
        {
            "scope": "results/scores/full/androidworld/**/score.json",
            "observed_count": "83",
            "rule": "exclude_directory_discovery",
            "reason": "The score root contains the submitted 82 plus one off-selector ExpenseDeleteSingle Agent A score.",
        },
        {
            "scope": "results/scores/full/androidworld/androidworld_scores_flat.csv",
            "observed_count": str(android_flat_rows),
            "rule": "exclude_stale_selector",
            "reason": "Stale 81-row selector omits both submitted RecipeDeleteMultipleRecipesWithConstraint records and adds off-selector ExpenseDeleteSingle Agent A.",
        },
        {
            "scope": "paper_result_packages/appworld_case_bundle_openrouter/**/codex-gpt-5.4-xhigh/score.json",
            "observed_count": "31",
            "rule": "exclude_alternate_rescore",
            "reason": "The frozen AppWorld flat CSV explicitly selects the high scorer; xhigh is an alternate duplicate version.",
        },
        {
            "scope": "results/{jobs,rerun,backups,smoke,tmp,tables}/** and */_batch_runs/**",
            "observed_count": "policy",
            "rule": "exclude_noncanonical_work_products",
            "reason": "Jobs, retries, backups, smoke runs, temporary packages, and derived tables cannot define submitted membership.",
        },
        {
            "scope": "results/full/webarena_verified/**",
            "observed_count": "out_of_scope",
            "rule": "exclude_benchmark",
            "reason": "WebArena-Verified is auxiliary/table-external and not part of the five-benchmark submitted 1,282-record universe.",
        },
        {
            "scope": "results/tables/** and outputs/latex/results_macros.tex",
            "observed_count": "derived",
            "rule": "exclude_numeric_source",
            "reason": "Old tables/macros are derived outputs; master-table records and hashes are the only numeric source.",
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    rows = records_from_flat_selectors(root)
    android_rows, android_cases = records_from_android_manifest(root)
    rows.extend(android_rows)
    if len(rows) != 1282:
        raise ValueError(f"expected 1,282 submitted records, found {len(rows)}")
    if len({row["record_key"] for row in rows}) != 1282:
        raise ValueError("submitted baseline record keys are not unique")
    if len({row["raw_record_slot_id"] for row in rows}) != 1282:
        raise ValueError("submitted raw record_slot_id values are not unique")
    if len({row["raw_record_id"] for row in rows}) != 1282:
        raise ValueError("submitted raw record_id values are not unique")
    if len({row["raw_run_id"] for row in rows}) != 1282:
        raise ValueError("submitted raw run_id values are not unique")

    benchmark_order = {name: index for index, name in enumerate(EXPECTED_LABEL_COUNTS)}
    agent_order = {name: index for index, name in enumerate(AGENTS)}
    rows.sort(key=lambda row: (benchmark_order[row["benchmark"]], row["case_unit_id"], agent_order[row["agent_id"]]))
    attach_public_blob_provenance(root, rows)

    counts_by_benchmark: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        counts_by_benchmark[row["benchmark"]][row["evidence_label_raw"]] += 1
    for benchmark, expected in EXPECTED_LABEL_COUNTS.items():
        observed = {label: counts_by_benchmark[benchmark][label] for label in "SFU"}
        if observed != expected:
            raise ValueError(f"raw evidence counts for {benchmark} changed: {observed} != {expected}")
    agent_counts = Counter(row["agent_id"] for row in rows)
    if agent_counts != Counter({"agent_a": 441, "agent_b": 441, "agent_c": 400}):
        raise ValueError(f"unexpected agent counts: {agent_counts}")

    baseline_path = output / "submitted_baseline_manifest.csv"
    android_path = output / "androidworld_submitted41_ab_manifest.csv"
    write_csv(baseline_path, MANIFEST_FIELDS, rows)
    write_csv(android_path, MANIFEST_FIELDS, [row for row in rows if row["benchmark"] == "androidworld"])

    submitted_android = {str(entry["case"]) for entry in android_cases}
    extension_rows, official100, official100_path = extension_contract(root, submitted_android)
    extension_fields = [
        "slot_order",
        "slot_id",
        "case_selection_rank",
        "case_unit_id",
        "agent_id",
        "extension_component",
        "submission_status",
        "expected_artifact_state",
        "append_gate",
    ]
    write_csv(output / "androidworld_extension_contract.csv", extension_fields, extension_rows)
    write_csv(output / "post_submission_extension_manifest.csv", extension_fields, [])

    crosswalk = legacy_crosswalk(root, rows)
    crosswalk_fields = ["record_key"]
    for name in (
        "raw_run",
        "native_evaluator",
        "score",
        "score_manifest",
        "checklist",
        "artifact_manifest",
    ):
        crosswalk_fields.extend([f"legacy_{name}_path", f"{name}_status"])
    write_csv(output / "legacy_results_crosswalk.csv", crosswalk_fields, crosswalk)
    write_csv(output / "exclusion_ledger.csv", ["scope", "observed_count", "rule", "reason"], exclusion_rows(root))

    source_paths = [
        root / str(config["bundle"]) / str(config["selector"]) for config in CONFIG.values()
    ] + [
        root / "paper_result_packages/androidworld_both_agents_scored_cases_official_full100/MANIFEST.json",
        official100_path,
    ]
    source_oids = git_blob_oids(root, SUBMISSION_COMMIT, [relative(root, path) for path in source_paths])
    inputs = [
        {
            "path": relative(root, path),
            "sha256": sha256_file(path),
            "submission_git_blob_oid": source_oids[relative(root, path)],
            "working_bytes_match_submission_blob": sha1_git_blob(path) == source_oids[relative(root, path)],
        }
        for path in source_paths
    ]
    write_json(output / "frozen_input_sources.json", inputs)

    total_labels = Counter(row["evidence_label_raw"] for row in rows)
    stronger = Counter(row["stronger_label_raw"] for row in rows)
    released = Counter(row["released_label"].lower() for row in rows)
    if total_labels != Counter({"S": 754, "F": 427, "U": 101}):
        raise ValueError(f"unexpected submitted evidence-label totals: {total_labels}")
    if released != Counter({"success": 863, "fail": 419}):
        raise ValueError(f"unexpected released-label totals: {released}")
    if stronger != Counter({"S": 386, "F": 290, "U": 81, "NA": 525}):
        raise ValueError(f"unexpected stronger-label totals: {stronger}")

    crosswalk_statuses = Counter(
        crosswalk_row[f"{name}_status"]
        for crosswalk_row in crosswalk
        for name in (
            "raw_run",
            "native_evaluator",
            "score",
            "score_manifest",
            "checklist",
            "artifact_manifest",
        )
    )
    summary = {
        "schema_version": "step1_baseline_summary/v1",
        "submission_commit": SUBMISSION_COMMIT,
        "baseline_record_count": len(rows),
        "unique_record_key_count": len({row["record_key"] for row in rows}),
        "unique_raw_record_slot_id_count": len({row["raw_record_slot_id"] for row in rows}),
        "unique_raw_record_id_count": len({row["raw_record_id"] for row in rows}),
        "unique_raw_run_id_count": len({row["raw_run_id"] for row in rows}),
        "benchmark_record_counts": dict(Counter(row["benchmark"] for row in rows)),
        "agent_record_counts": dict(agent_counts),
        "raw_evidence_label_counts": dict(total_labels),
        "stronger_label_counts": dict(stronger),
        "released_label_counts": dict(released),
        "androidworld_submitted_case_count": len(submitted_android),
        "androidworld_submitted_record_count": len(android_rows),
        "androidworld_official100_case_count": len(official100["items"]),
        "androidworld_remaining_case_count": 59,
        "extension_contract_slot_count": len(extension_rows),
        "extension_manifest_active_row_count": 0,
        "all_decisive_files_match_submission_git_blobs": all(
            row["public_artifact_byte_identical"] == "true" for row in rows
        ),
        "legacy_results_crosswalk_artifact_status_counts": dict(crosswalk_statuses),
        "selection_policy": "four frozen 300-row flat CSVs plus Android public-package MANIFEST expanded over A/B",
        "aggregation_policy": "submitted master table may be rebuilt only from submitted_baseline_manifest.csv",
    }
    write_json(output / "baseline_summary.json", summary)


if __name__ == "__main__":
    main()
