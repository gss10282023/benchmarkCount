#!/usr/bin/env python3
"""Outcome-blind fidelity audit for Terminal-Bench 2.1 and DeepSWE v1.1 packets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import tomllib
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts import build_deep_swe_v1_1_case_packets as deep  # noqa: E402
from scripts import build_terminal_bench_2_1_case_packets as terminal  # noqa: E402


AUDIT_ROOT = Path(__file__).resolve().parent
TERMINAL_ROOT = REPO_ROOT / "experiments/case_packets/terminal_bench_2_1"
DEEP_ROOT = REPO_ROOT / "experiments/case_packets/deep_swe_v1_1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def source_inventory(markdown: str) -> list[str]:
    paths: list[str] = []
    active = False
    for line in markdown.splitlines():
        if line == "## Source Inventory":
            active = True
            continue
        if active and line.startswith("## "):
            break
        if active and line.startswith("- `") and line.endswith("`"):
            paths.append(line[3:-1])
    return paths


def audit_terminal(source_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    validator = terminal.validate_output(TERMINAL_ROOT)
    snapshot = terminal.load_source_directory(source_dir)
    source_by_slug = {
        slug: {
            source.relative_path: source
            for source in terminal._files_for_task(snapshot, slug)
        }
        for slug in snapshot.task_digests
    }
    index = load_json(TERMINAL_ROOT / "index.json")
    rows: list[dict[str, Any]] = []
    for entry in index["entries"]:
        slug = entry["case_unit_id"]
        case_dir = TERMINAL_ROOT / slug
        packet = load_json(case_dir / "case_packet.json")
        manifest = load_json(case_dir / "raw_case_manifest.json")
        agent = load_json(case_dir / "agent_input.json")
        markdown = (case_dir / "case_packet.md").read_text(encoding="utf-8")
        raw = case_dir / "raw_case"
        instruction = (raw / "official/instruction.md").read_text(encoding="utf-8")
        task_config = tomllib.loads(
            (raw / "official/task.toml").read_text(encoding="utf-8")
        )
        actual_raw = sorted(
            path.relative_to(raw).as_posix()
            for path in raw.rglob("*")
            if path.is_file()
        )
        refs = [str(value) for value in manifest["file_sources"].values()]
        required_sources = {
            "instruction.md",
            "task.toml",
            "README.md",
            "environment/Dockerfile",
            "tests/test.sh",
            "solution/solve.sh",
        }
        canonical_paths = {item["source_path"] for item in manifest["source_files"]}
        manifest_items = {
            item["source_path"]: item for item in manifest["source_files"]
        }
        external_source_exact = canonical_paths == set(source_by_slug[slug])
        if external_source_exact:
            for relative, source in source_by_slug[slug].items():
                item = manifest_items[relative]
                if (
                    item["sha256"] != source.sha256
                    or item["size_bytes"] != source.size_bytes
                ):
                    external_source_exact = False
                    break
                materialized = item["materialized_path"]
                if materialized is None:
                    if (raw / "official" / relative).exists():
                        external_source_exact = False
                        break
                elif source.text is None or (
                    raw / materialized
                ).read_bytes() != source.text.encode("utf-8"):
                    external_source_exact = False
                    break
        checks = {
            "instruction_exact": packet["task"]["instruction"]
            == instruction
            == agent["instruction"],
            "task_config_exact": packet["task"]["task_config"] == task_config,
            "task_identity_exact": (
                packet["task"]["task_name"] == f"terminal-bench/{slug}"
                and agent["task_name"] == f"terminal-bench/{slug}"
            ),
            "source_membership_complete": required_sources <= canonical_paths,
            "external_harbor_source_exact": external_source_exact,
            "markdown_inventory_exact": source_inventory(markdown) == actual_raw,
            "raw_inventory_exact": actual_raw == sorted(manifest["official_files"]),
            "verifier_entrypoint_present": (
                case_dir / packet["evaluator_reference"]["verifier_entrypoint"]
            ).is_file(),
            "solution_bytes_excluded": (
                not any(path.startswith("official/solution/") for path in actual_raw)
                and all(
                    item["materialized_path"] is None
                    for item in manifest["controller_metadata_only_files"]
                )
            ),
            "harbor_source_refs_bound": (
                bool(refs)
                and all(
                    ref.startswith(f"harbor://terminal-bench/{slug}@sha256:")
                    for ref in refs
                )
                and all("/jobs/" not in ref and "/trials/" not in ref for ref in refs)
            ),
            "outcome_blind_checklist_contract": (
                packet["checklist_design_contract"][
                    "released_label_visibility_during_drafting"
                ]
                == "forbidden"
                and packet["checklist_design_contract"][
                    "released_label_visibility_during_evidence_scoring"
                ]
                == "forbidden"
                and packet["checklist_design_contract"]["released_label_use"]
                == "post-score comparison only"
                and packet["leakage_control"][
                    "prior_run_records_excluded_from_packet_generation"
                ]
            ),
            "artifact_inventory_types_only": (
                packet["artifact_inventory"]["inventory_known_pre_lock"]
                and not packet["artifact_inventory"][
                    "per_record_contents_or_values_in_packet"
                ]
                and not packet["artifact_inventory"][
                    "released_evaluator_value_available_to_packet_or_scorer"
                ]
                and packet["artifact_inventory"]["retained_execution_artifact_types"]
                == terminal.RETAINED_EXECUTION_ARTIFACT_TYPES
            ),
            "source_lock_join": manifest["source_tree_sha256"]
            == entry["source_tree_sha256"],
        }
        rows.append(
            {
                "benchmark": "terminal_bench_2_1",
                "case_unit_id": slug,
                "status": "pass" if all(checks.values()) else "fail",
                "checks": checks,
                "canonical_source_file_count": manifest["source_file_count"],
                "materialized_official_file_count": manifest["raw_case_file_count"],
                "external_binary_hash_only_count": len(
                    manifest["external_binary_files"]
                ),
                "metadata_only_text_count": len(
                    manifest.get("metadata_only_text_files", [])
                ),
                "protected_solution_count": len(
                    manifest["controller_metadata_only_files"]
                ),
                "content_fidelity": (
                    "official task/evaluator text is byte-exact; protected solutions and "
                    "binary/allowlisted oversized fixtures use source-bound metadata"
                ),
            }
        )
    return validator, rows


def audit_deep(source_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    validator = deep.validate_output(DEEP_ROOT)
    snapshot = deep.load_source_directory(source_dir)
    source_by_slug = {
        slug: {
            source.relative_path: source
            for source in deep._files_for_task(snapshot, slug)
        }
        for slug in snapshot.manifest_task_digests
    }
    index = load_json(DEEP_ROOT / "index.json")
    rows: list[dict[str, Any]] = []
    for entry in index["entries"]:
        slug = entry["case_unit_id"]
        case_dir = DEEP_ROOT / slug
        packet = load_json(case_dir / "case_packet.json")
        manifest = load_json(case_dir / "raw_case_manifest.json")
        agent = load_json(case_dir / "agent_input.json")
        markdown = (case_dir / "case_packet.md").read_text(encoding="utf-8")
        raw = case_dir / "raw_case"
        official_source = source_by_slug[slug]
        config = tomllib.loads((raw / "official/task.toml").read_text(encoding="utf-8"))
        grader = load_json(raw / "official/tests/config.json")
        projection = load_json(raw / "derived/evaluator_projection.json")
        base_commit = config["metadata"]["base_commit_hash"]
        repository_url = config["metadata"]["repository_url"]
        environment = (raw / "official/environment/Dockerfile").read_text(
            encoding="utf-8"
        )
        pre_artifacts = (raw / "official/pre_artifacts.sh").read_text(encoding="utf-8")
        actual_raw = sorted(
            path.relative_to(raw).as_posix()
            for path in raw.rglob("*")
            if path.is_file()
        )
        byte_exact = True
        for relative, source in official_source.items():
            if relative.startswith("solution/"):
                continue
            candidate = raw / "official" / relative
            if not candidate.is_file() or candidate.read_bytes() != source.data:
                byte_exact = False
                break
        solution_metadata_exact = True
        solution_items = {
            item["source_path"]: item
            for item in manifest["controller_metadata_only_files"]
        }
        for relative in ("solution/solve.sh", "solution/solution.patch"):
            source = official_source[relative]
            item = solution_items.get(relative)
            if (
                item is None
                or item["sha256"] != source.sha256
                or item["size_bytes"] != source.size_bytes
                or item["materialized_path"] is not None
            ):
                solution_metadata_exact = False
        checks = {
            "instruction_exact": (
                packet["task"]["instruction"]
                == agent["instruction"]
                == official_source["instruction.md"].text
            ),
            "task_config_exact": packet["task"]["task_config"] == config,
            "task_identity_exact": (
                packet["task"]["task_name"] == f"datacurve/{slug}"
                and agent["task_name"] == f"datacurve/{slug}"
                and config["metadata"]["task_id"] == slug
            ),
            "all_non_solution_sources_byte_exact": byte_exact,
            "solution_metadata_exact_no_bytes": solution_metadata_exact,
            "markdown_inventory_exact": source_inventory(markdown) == actual_raw,
            "base_commit_consistent": (
                grader["base_commit"] == base_commit
                and base_commit in environment
                and base_commit in pre_artifacts
            ),
            "repository_consistent": (
                repository_url in environment
                or repository_url.removesuffix(".git") in environment
            ),
            "evaluator_projection_exact": (
                projection == packet["evaluator_reference"]["projection"]
                and projection["native_test_sets"]["fail_to_pass"]["node_ids"]
                == grader["f2p_node_ids"]
                and projection["native_test_sets"]["pass_to_pass"]["count"]
                == len(grader["p2p_node_ids"])
                and projection["native_test_sets"]["pass_to_pass"]["node_ids_sha256"]
                == deep._node_list_sha256(grader["p2p_node_ids"])
            ),
            "test_patch_present": (raw / "official/tests/test.patch").stat().st_size
            > 0,
            "separate_verifier_and_model_patch_contract": (
                config["verifier"]["environment_mode"] == "separate"
                and config["artifacts"] == ["/logs/artifacts/model.patch"]
            ),
            "outcome_blind_contract": (
                packet["leakage_control"][
                    "prior_run_records_excluded_from_packet_generation"
                ]
                and not packet["artifact_inventory"][
                    "per_record_contents_or_values_in_packet"
                ]
                and not packet["artifact_inventory"][
                    "released_evaluator_value_available_to_packet_or_scorer"
                ]
            ),
            "source_lock_join": manifest["source_tree_sha256"]
            == entry["source_tree_sha256"],
        }
        rows.append(
            {
                "benchmark": "deep_swe_v1_1",
                "case_unit_id": slug,
                "status": "pass" if all(checks.values()) else "fail",
                "checks": checks,
                "canonical_source_file_count": manifest["source_file_count"],
                "materialized_official_file_count": len(manifest["official_files"]),
                "protected_solution_count": len(
                    manifest["controller_metadata_only_files"]
                ),
                "f2p_node_id_count": len(grader["f2p_node_ids"]),
                "p2p_node_id_count": len(grader["p2p_node_ids"]),
                "base_commit_length": len(base_commit),
                "content_fidelity": (
                    "all non-solution official task bytes match the pinned Git tree; reference "
                    "solution bytes are excluded but their exact hashes and sizes match"
                ),
            }
        )
    return validator, rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terminal-source-dir", type=Path, required=True)
    parser.add_argument("--deep-source-dir", type=Path, required=True)
    args = parser.parse_args()
    terminal_validator, terminal_rows = audit_terminal(
        args.terminal_source_dir.resolve()
    )
    deep_validator, deep_rows = audit_deep(args.deep_source_dir.resolve())
    rows = terminal_rows + deep_rows
    failures = [row for row in rows if row["status"] != "pass"]
    base_lengths = Counter(
        row["base_commit_length"] for row in deep_rows if "base_commit_length" in row
    )
    summary = {
        "schema_version": "two_benchmark_case_packet_fidelity_audit/v1",
        "status": "pass" if not failures else "fail",
        "audit_scope": (
            "official case/task/evaluator source fidelity and outcome-blind packet boundary; "
            "no agent outcomes or released per-record evaluator results were used"
        ),
        "benchmarks": {
            "terminal_bench_2_1": {
                "case_count": len(terminal_rows),
                "passed": sum(row["status"] == "pass" for row in terminal_rows),
                "failed": sum(row["status"] != "pass" for row in terminal_rows),
                "builder_validation": terminal_validator,
                "canonical_source_binding": (
                    "fresh official Harbor terminal-bench/terminal-bench-2-1@6 export; "
                    "every materialized source byte and every metadata-only source hash/size "
                    "were compared, with all 89 package digests and the 946-file corpus tree "
                    "independently verified"
                ),
            },
            "deep_swe_v1_1": {
                "case_count": len(deep_rows),
                "passed": sum(row["status"] == "pass" for row in deep_rows),
                "failed": sum(row["status"] != "pass" for row in deep_rows),
                "builder_validation": deep_validator,
                "canonical_source_binding": (
                    "official Git task tree 891e2975cd842071f62e567c3b11cae7362bf065; "
                    "every retained official source compared byte-for-byte"
                ),
                "official_base_commit_length_counts": dict(
                    sorted(base_lengths.items())
                ),
            },
        },
        "total_case_count": len(rows),
        "total_passed": sum(row["status"] == "pass" for row in rows),
        "total_failed": len(failures),
        "review_findings": [
            {
                "severity": "informational",
                "benchmark": "deep_swe_v1_1",
                "finding": (
                    "the official corpus contains two 7-character base commit values and one "
                    "39-character value; task.toml, grader config, environment Dockerfile, and "
                    "pre_artifacts.sh agree exactly for every affected case"
                ),
            },
            {
                "severity": "informational",
                "benchmark": "deep_swe_v1_1",
                "finding": (
                    "tests/config.json is retained byte-for-byte for all cases; Markdown renders "
                    "all f2p IDs and a count/hash binding for very large p2p inventories"
                ),
            },
            {
                "severity": "informational",
                "benchmark": "terminal_bench_2_1",
                "finding": (
                    "binary assets, one allowlisted oversized fixture manifest, and reference "
                    "solutions are source-bound metadata rather than duplicated packet bytes"
                ),
            },
        ],
    }
    AUDIT_ROOT.mkdir(parents=True, exist_ok=True)
    jsonl(AUDIT_ROOT / "audit_records.jsonl", rows)
    with (AUDIT_ROOT / "audit_report.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "benchmark",
                "case_unit_id",
                "status",
                "canonical_source_file_count",
                "materialized_official_file_count",
                "protected_solution_count",
                "f2p_node_id_count",
                "p2p_node_id_count",
                "content_fidelity",
            ],
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)
    (AUDIT_ROOT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
