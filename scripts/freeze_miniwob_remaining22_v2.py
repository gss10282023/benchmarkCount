#!/usr/bin/env python3
"""Freeze the source-only MiniWoB remaining-22 v2 checklists before scoring."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
for import_root in (ROOT, ROOT / "src"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from evidence_system.core.hashing import canonical_json_bytes, sha256_file, sha256_object, sha256_path  # noqa: E402
from neurips_ed_track_minimal.checklist_guardrails import (  # noqa: E402
    case_packet_support_paths,
    validate_checklist_guardrails,
)
from neurips_ed_track_minimal.scripts.checklist_validator import (  # noqa: E402
    validate_packet_required_stronger_conditions,
    validate_support_pointers,
)


EXPECTED_COUNT = 22
FORBIDDEN_OUTCOME_MARKERS = (
    "Agent A",
    "Agent B",
    "Agent C",
    '"native_score":',
    '"native_label":',
    '"outcome_label":',
    '"evidence_label":',
    '"response_id":',
    '"api_response":',
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed-root", type=Path, required=True)
    parser.add_argument("--case-packet-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    reviewed_root = args.reviewed_root.resolve()
    packet_root = args.case_packet_root.resolve()
    output_root = args.output_root.resolve()
    if output_root.exists():
        raise ValueError(f"freeze output already exists: {output_root}")
    case_ids = sorted(path.name for path in reviewed_root.iterdir() if path.is_dir())
    packet_ids = sorted(path.name for path in packet_root.iterdir() if path.is_dir())
    if len(case_ids) != EXPECTED_COUNT or packet_ids != case_ids:
        raise ValueError("freeze requires the same exact 22-case reviewed and packet sets")

    schema_path = ROOT / "neurips_ed_track_minimal/schemas/case_checklist.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    prompt_path = ROOT / "neurips_ed_track_minimal/prompts/score_evidence_with_codex.prompt.md"
    score_schema_path = ROOT / "neurips_ed_track_minimal/schemas/evidence_score.schema.json"
    frozen_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    output_root.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.stage-", dir=output_root.parent))
    cases: list[dict[str, Any]] = []
    try:
        for case_id in case_ids:
            yaml_path = reviewed_root / case_id / "checklist.yaml"
            json_path = reviewed_root / case_id / "checklist.json"
            packet_path = packet_root / case_id / "case_packet.md"
            checklist = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            if checklist != json.loads(json_path.read_text(encoding="utf-8")):
                raise ValueError(f"reviewed YAML/JSON mismatch: {case_id}")
            errors = list(validator.iter_errors(checklist))
            if errors:
                raise ValueError(f"schema failure for {case_id}: {errors[0].message}")
            allowed = case_packet_support_paths(packet_path.read_text(encoding="utf-8"))
            validate_checklist_guardrails(checklist, allowed_source_paths=allowed)
            validate_support_pointers(checklist, packet_path)
            validate_packet_required_stronger_conditions(checklist, packet_path)
            serialized = json.dumps(checklist, ensure_ascii=False, sort_keys=True)
            leaked = [marker for marker in FORBIDDEN_OUTCOME_MARKERS if marker in serialized]
            if leaked:
                raise ValueError(f"outcome marker leaked into {case_id}: {leaked}")

            target = stage / "checklists" / case_id
            target.mkdir(parents=True)
            shutil.copyfile(yaml_path, target / "checklist.yaml")
            canonical = canonical_json_bytes(checklist)
            (target / "checklist.canonical.json").write_bytes(canonical)
            cases.append(
                {
                    "case_unit_id": case_id,
                    "contract_version": "2.0.0",
                    "contract_hash": sha256_object(checklist),
                    "checklist_yaml_sha256": sha256_file(target / "checklist.yaml"),
                    "checklist_canonical_sha256": sha256_file(
                        target / "checklist.canonical.json"
                    ),
                    "case_packet_sha256": sha256_file(packet_path),
                    "stronger_condition_count": len(
                        checklist["stronger"]["additional_conditions"]
                    ),
                }
            )

        receipt = {
            "schema_version": "miniwob_remaining22_system_design_freeze/v2",
            "status": "frozen",
            "frozen_at": frozen_at,
            "case_count": len(cases),
            "phase_boundary": {
                "locked_before_evidence_scoring": True,
                "locked_before_specific_outcome_or_released_label_inspection": True,
                "contains_agent_outcomes": False,
                "reads_result_namespaces": False,
                "applies_prospectively_to_new_score_outputs_only": True,
                "does_not_rewrite_existing_v1_results": True,
            },
            "system_design": {
                "native_verdicts": ["S", "F", "U"],
                "released_evaluator_label_is_not_decisive_evidence": True,
                "stronger_reported_separately": True,
                "stronger_failure_implies_benchmark_conflict": False,
                "native_s_plus_stronger_f_implies_benchmark_conflict": False,
                "benchmark_conflict_requires_separate_record_level_audit": True,
            },
            "inputs": {
                "reviewed_root": reviewed_root.relative_to(ROOT).as_posix(),
                "reviewed_tree_sha256": sha256_path(reviewed_root),
                "case_packet_root": packet_root.relative_to(ROOT).as_posix(),
                "case_packet_tree_sha256": sha256_path(packet_root),
                "score_prompt_path": prompt_path.relative_to(ROOT).as_posix(),
                "score_prompt_sha256": sha256_file(prompt_path),
                "checklist_schema_path": schema_path.relative_to(ROOT).as_posix(),
                "checklist_schema_sha256": sha256_file(schema_path),
                "score_schema_path": score_schema_path.relative_to(ROOT).as_posix(),
                "score_schema_sha256": sha256_file(score_schema_path),
            },
            "planned_scorer": {
                "provider": "codex_cli",
                "auth_mode": "codex_login",
                "model": "gpt-5.4",
                "reasoning_effort": "high",
                "service_tier": "default",
                "fast_mode": False,
                "concurrency": 11,
            },
            "cases": cases,
            "cases_sha256": sha256_object(cases),
        }
        provenance = stage / "provenance"
        provenance.mkdir()
        (provenance / "freeze_receipt.json").write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        os.replace(stage, output_root)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise

    print(
        json.dumps(
            {
                "status": "frozen",
                "case_count": len(cases),
                "output_root": output_root.relative_to(ROOT).as_posix(),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
