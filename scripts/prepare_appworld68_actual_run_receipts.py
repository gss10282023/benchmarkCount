#!/usr/bin/env python3
"""Extract narrow, hashed AppWorld run receipts without copying full LM logs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterator


AGENTS = ("agent_a", "agent_b", "agent_c")
TASK_RE = re.compile(r"(?:^|\n)Task:\s*(.+?)(?:\n\n|\Z)", re.DOTALL)


class ReceiptError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retained-root", type=Path, required=True)
    parser.add_argument("--case-source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


def extract_instruction(path: Path) -> tuple[str, str]:
    matches: set[tuple[str, str]] = set()
    with path.open("r", encoding="utf-8", errors="strict") as handle:
        for line in handle:
            payload = json.loads(line)
            for value in strings(payload):
                if "generate code to solve the actual task" not in value or "Task:" not in value:
                    continue
                match = TASK_RE.search(value)
                if match:
                    instruction = " ".join(match.group(1).strip().split())
                    matches.add((instruction, sha256_text(value)))
    instructions = {instruction for instruction, _ in matches}
    if len(instructions) != 1:
        raise ReceiptError(f"expected one actual task instruction in {path}, found {sorted(instructions)}")
    instruction = next(iter(instructions))
    message_hashes = sorted(message_hash for text, message_hash in matches if text == instruction)
    return instruction, message_hashes[0]


def locate_records(retained_root: Path, case_ids: list[str]) -> dict[tuple[str, str], tuple[str, Path]]:
    found: dict[tuple[str, str], tuple[str, Path]] = {}
    for vps in ("vps1", "vps2"):
        for agent in AGENTS:
            base = retained_root / vps / "outputs" / agent
            if not base.is_dir():
                continue
            for case_id in case_ids:
                candidate = base / case_id
                if candidate.is_dir():
                    key = (case_id, agent)
                    if key in found:
                        raise ReceiptError(f"duplicate record {key}")
                    found[key] = (vps, candidate)
    expected = {(case_id, agent) for case_id in case_ids for agent in AGENTS}
    if set(found) != expected:
        raise ReceiptError(f"retained set differs; missing={sorted(expected-set(found))[:5]}")
    return found


def main() -> int:
    args = parse_args()
    retained_root = args.retained_root.resolve()
    case_source_root = args.case_source_root.resolve()
    output_root = args.output_root.resolve()
    if output_root.exists():
        raise ReceiptError(f"refusing existing output root: {output_root}")
    output_root.mkdir(parents=True, exist_ok=False)
    case_ids = sorted(path.name for path in case_source_root.iterdir() if path.is_dir())
    if len(case_ids) != 68:
        raise ReceiptError(f"expected 68 cases, found {len(case_ids)}")
    records = locate_records(retained_root, case_ids)
    manifest_rows: list[dict[str, Any]] = []
    for case_id in case_ids:
        packet_specs_path = case_source_root / case_id / "raw_case/official/specs.json"
        packet_specs = load_json(packet_specs_path)
        agents: list[dict[str, Any]] = []
        instructions: set[str] = set()
        for agent in AGENTS:
            vps, record = records[(case_id, agent)]
            lm_log = record / "appworld_task_output/logs/lm_calls.jsonl"
            instruction, prompt_message_sha = extract_instruction(lm_log)
            instructions.add(instruction)
            run_summary = load_json(record / "run_summary.json")
            native_output = load_json(record / "native_evaluator_output.json")
            artifact_manifest = load_json(record / "artifact_manifest.json")
            artifact_text = json.dumps(artifact_manifest, sort_keys=True)
            exact_task_directory_retained = any(
                marker in artifact_text
                for marker in ("data/tasks/", "ground_truth/evaluation.py", "ground_truth/test_data.json")
            )
            task_output_data_version = (
                record / "appworld_task_output/version/data.txt"
            ).read_text(encoding="utf-8").strip()
            agents.append(
                {
                    "agent_slug": agent,
                    "task_id": f"{case_id}__{agent}",
                    "source_vps": vps,
                    "actual_task_instruction": instruction,
                    "actual_prompt_message_sha256": prompt_message_sha,
                    "full_lm_log_sha256": sha256_file(lm_log),
                    "actual_run_versions": {
                        "code_data_version": run_summary.get("code_data_version"),
                        "data_version": run_summary.get("data_version"),
                        "db_version": run_summary.get("db_version"),
                        "task_output_data_version": task_output_data_version,
                    },
                    "released_tracker_success": native_output.get("tracker", {}).get("success"),
                    "released_registered_requirements": [
                        row.get("requirement")
                        for group in ("passes", "failures")
                        for row in native_output.get("tracker", {}).get(group, [])
                    ],
                    "native_evaluator_output_sha256": sha256_file(
                        record / "native_evaluator_output.json"
                    ),
                    "evaluation_report_sha256": sha256_file(
                        record / "appworld_task_output/evaluation/report.md"
                    ),
                    "exact_runtime_task_directory_retained": exact_task_directory_retained,
                    "source_pointer": (
                        f"{vps}/outputs/{agent}/{case_id}/appworld_task_output/logs/lm_calls.jsonl"
                    ),
                }
            )
        if len(instructions) != 1:
            raise ReceiptError(f"actual instruction differs across agents for {case_id}: {instructions}")
        actual_versions = {
            tuple(sorted(row["actual_run_versions"].items())) for row in agents
        }
        if len(actual_versions) != 1:
            raise ReceiptError(f"run versions differ across agents for {case_id}")
        payload = {
            "schema_version": "appworld_actual_run_receipt/v1",
            "case_unit_id": case_id,
            "dataset": "test_normal",
            "actual_task_instruction": next(iter(instructions)),
            "packet_source": {
                "path": "official/specs.json",
                "db_version": packet_specs.get("db_version"),
                "instruction": packet_specs.get("instruction"),
                "specs_sha256": sha256_file(packet_specs_path),
            },
            "agents": agents,
            "provenance_facts": {
                "packet_db_version": packet_specs.get("db_version"),
                "actual_run_db_versions": sorted(
                    {row["actual_run_versions"]["db_version"] for row in agents}
                ),
                "instruction_matches_packet_copy": packet_specs.get("instruction")
                == next(iter(instructions)),
                "exact_runtime_task_directory_retained_for_all_records": all(
                    row["exact_runtime_task_directory_retained"] for row in agents
                ),
            },
        }
        target = output_root / f"{case_id}.json"
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest_rows.append(
            {"case_unit_id": case_id, "receipt": target.name, "sha256": sha256_file(target)}
        )
    (output_root / "MANIFEST.json").write_text(
        json.dumps(
            {
                "schema_version": "appworld_actual_run_receipt_manifest/v1",
                "case_count": 68,
                "record_count": 204,
                "rows": manifest_rows,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"case_count": 68, "record_count": 204, "output_root": str(output_root)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
