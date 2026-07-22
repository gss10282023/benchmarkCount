#!/usr/bin/env python3
"""Package 66 MiniWoB records for blinded v2 evidence scoring on the score VPS."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from evidence_system.core.hashing import sha256_file, sha256_path  # noqa: E402


EXPECTED_CASES = 22
EXPECTED_AGENTS = ("agent_a", "agent_b", "agent_c")
EXPECTED_TASKS = EXPECTED_CASES * len(EXPECTED_AGENTS)
BLINDED_FIELDS = {
    "native_run/run_summary.json": ("success",),
    "native_run/native_evaluator_output.json": ("success",),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen-root", type=Path, required=True)
    parser.add_argument("--case-packet-root", type=Path, required=True)
    parser.add_argument("--reviewed-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _task_identity(run_dir: Path, raw_run: dict[str, Any]) -> tuple[str, str]:
    case_id = str(raw_run.get("case_unit_id") or "")
    agent_id = str(raw_run.get("agent_id") or "")
    agent_slug = agent_id.strip().lower().replace(" ", "_")
    if not case_id.startswith("miniwob.") or agent_slug not in EXPECTED_AGENTS:
        raise ValueError(f"invalid case/agent identity in {run_dir}")
    expected_suffix = f"-{agent_slug}"
    if not run_dir.name.endswith(expected_suffix):
        raise ValueError(f"run directory/agent mismatch: {run_dir}")
    return case_id, agent_slug


def main() -> int:
    args = parse_args()
    frozen_root = args.frozen_root.resolve()
    packet_root = args.case_packet_root.resolve()
    reviewed_root = args.reviewed_root.resolve()
    run_root = args.run_root.resolve()
    output_root = args.output_root.resolve()
    if output_root.exists():
        raise ValueError(f"output already exists: {output_root}")

    freeze_receipt = _load_json(frozen_root / "provenance/freeze_receipt.json")
    if freeze_receipt.get("status") != "frozen" or freeze_receipt.get("case_count") != EXPECTED_CASES:
        raise ValueError("v2 checklist freeze receipt is not valid")
    boundary = freeze_receipt.get("phase_boundary") or {}
    if not (
        boundary.get("locked_before_evidence_scoring") is True
        and boundary.get("locked_before_specific_outcome_or_released_label_inspection") is True
        and boundary.get("contains_agent_outcomes") is False
    ):
        raise ValueError("v2 freeze does not establish the required outcome-isolation boundary")

    locked_cases = {
        str(item["case_unit_id"]): item for item in freeze_receipt.get("cases") or []
    }
    if len(locked_cases) != EXPECTED_CASES:
        raise ValueError("freeze receipt does not bind exactly 22 cases")
    run_dirs = sorted(path for path in run_root.iterdir() if path.is_dir())
    if len(run_dirs) != EXPECTED_TASKS:
        raise ValueError(f"expected 66 run directories, observed {len(run_dirs)}")

    output_root.mkdir(parents=True)
    tasks_root = output_root / "tasks"
    tasks_root.mkdir()
    contracts = output_root / "contracts"
    contracts.mkdir()
    shutil.copytree(frozen_root, contracts / "frozen_v2")
    shutil.copytree(packet_root, contracts / "case_packets_v2")
    shutil.copytree(reviewed_root, contracts / "reviewed_v2")

    task_records: list[dict[str, Any]] = []
    observed_pairs: set[tuple[str, str]] = set()
    for run_dir in run_dirs:
        adapter = run_dir / "adapter"
        raw_run_path = adapter / "raw_run.json"
        raw_run = _load_json(raw_run_path)
        case_id, agent_slug = _task_identity(run_dir, raw_run)
        pair = (case_id, agent_slug)
        if pair in observed_pairs:
            raise ValueError(f"duplicate case/agent record: {pair}")
        observed_pairs.add(pair)
        if case_id not in locked_cases:
            raise ValueError(f"run case is absent from frozen v2: {case_id}")
        if raw_run.get("status") != "COMPLETED":
            raise ValueError(f"non-completed record cannot enter this score batch: {run_dir.name}")
        released_label = str(raw_run.get("native_label") or "").strip().lower()
        if released_label not in {"success", "fail"}:
            raise ValueError(f"missing released evaluator label: {run_dir.name}")

        task_dir = tasks_root / run_dir.name
        evidence_dir = task_dir / "evidence"
        task_dir.mkdir()
        frozen_checklist = frozen_root / "checklists" / case_id / "checklist.yaml"
        shutil.copyfile(frozen_checklist, task_dir / "checklist.yaml")
        if sha256_file(task_dir / "checklist.yaml") != locked_cases[case_id]["checklist_yaml_sha256"]:
            raise ValueError(f"frozen checklist hash drift: {case_id}")

        shutil.copytree(adapter, evidence_dir)
        label_source = task_dir / "released_label_source"
        label_source.mkdir()
        shutil.copyfile(raw_run_path, label_source / "raw_run.json")
        (evidence_dir / "raw_run.json").unlink()

        blinding: list[dict[str, Any]] = []
        for relative, fields in BLINDED_FIELDS.items():
            source = adapter / relative
            target = evidence_dir / relative
            original = _load_json(source)
            shutil.copyfile(source, label_source / source.name)
            removed = []
            for field in fields:
                if field in original:
                    original.pop(field)
                    removed.append(field)
            if removed != list(fields):
                raise ValueError(f"expected summary-only fields missing in {source}")
            target.write_text(
                json.dumps(original, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            blinding.append(
                {
                    "evidence_path": relative,
                    "removed_summary_only_fields": removed,
                    "original_path": f"released_label_source/{source.name}",
                    "original_sha256": sha256_file(source),
                    "blinded_sha256": sha256_file(target),
                }
            )

        native_label = {
            "value": released_label,
            "source": "released_label_source/raw_run.json::native_label",
            "source_file_sha256": sha256_file(raw_run_path),
        }
        (task_dir / "native_label.json").write_text(
            json.dumps(native_label, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        blinded_receipt = {
            "schema_version": "miniwob_released_label_blinding/v1",
            "purpose": (
                "Keep the saved released evaluator label and summary-only success fields outside the model-visible "
                "evidence directory while retaining exact originals for post-score comparison."
            ),
            "released_label_value_exposed_to_model": False,
            "raw_run_in_model_evidence": False,
            "modifications": blinding,
        }
        (evidence_dir / "released_label_blinding_receipt.json").write_text(
            json.dumps(blinded_receipt, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        task_records.append(
            {
                "task_id": run_dir.name,
                "case_unit_id": case_id,
                "agent": agent_slug,
                "checklist_sha256": sha256_file(task_dir / "checklist.yaml"),
                "evidence_tree_sha256": sha256_path(evidence_dir),
                "native_label_sha256": sha256_file(task_dir / "native_label.json"),
                "original_adapter_tree_sha256": sha256_path(adapter),
                "released_label_source_tree_sha256": sha256_path(label_source),
            }
        )

    expected_pairs = {
        (case_id, agent) for case_id in locked_cases for agent in EXPECTED_AGENTS
    }
    if observed_pairs != expected_pairs or len(task_records) != EXPECTED_TASKS:
        raise ValueError("score task denominator is not the exact 22 x 3 product")
    receipt = {
        "schema_version": "miniwob_remaining22_v2_score_transfer/v1",
        "status": "ready",
        "task_count": len(task_records),
        "case_count": EXPECTED_CASES,
        "agents": list(EXPECTED_AGENTS),
        "system_design": {
            "checklists_frozen_before_outcome_inspection": True,
            "model_visible_released_evaluator_labels": False,
            "released_labels_preserved_separately": True,
            "native_scored_as_S_F_U_from_retained_evidence": True,
            "stronger_reported_separately": True,
            "benchmark_conflict_not_inferred_by_scorer": True,
        },
        "frozen_contract_tree_sha256": sha256_path(frozen_root),
        "case_packet_tree_sha256": sha256_path(packet_root),
        "source_run_tree_sha256": sha256_path(run_root),
        "tasks_tree_sha256": sha256_path(tasks_root),
        "tasks": task_records,
    }
    (output_root / "transfer_receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "ready",
                "task_count": len(task_records),
                "output_root": output_root.relative_to(ROOT).as_posix(),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
