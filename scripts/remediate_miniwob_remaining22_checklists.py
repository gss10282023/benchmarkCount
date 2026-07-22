#!/usr/bin/env python3
"""Create the reviewed v2 MiniWoB remaining-22 checklists and retire reviewed v1.

This is a source-only remediation.  It never reads result namespaces and the
output is prospective: it must not be substituted into an already executed v1
record.  The script validates every checklist against its v2 case packet before
removing the explicitly supplied reviewed-v1 directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
for import_root in (ROOT, ROOT / "src"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from evidence_system.core.hashing import sha256_file, sha256_object, sha256_path  # noqa: E402
from evidence_system.contracts.case_packets import (  # noqa: E402
    _materialize_miniwob_drafting_sources,
    _raw_case_manifest,
    render_case_packet,
)
from neurips_ed_track_minimal.checklist_guardrails import (  # noqa: E402
    case_packet_support_paths,
    validate_checklist_guardrails,
)
from neurips_ed_track_minimal.scripts.checklist_validator import (  # noqa: E402
    validate_packet_required_stronger_conditions,
    validate_support_pointers,
)


EXPECTED_COUNT = 22
OLD_REVIEWED_BASENAME = "reviewed_system_design_v1"
NEW_REVIEWED_BASENAME = "reviewed_system_design_v2"
RUNTIME_SUPPORT = [
    "derived/drafting_context.json::released_evaluator.failure_evidence_rule",
    "derived/drafting_context.json::released_evaluator.record_scope_rule",
    "derived/runtime_decision_wiring.json::excerpts.worker_run_smoke_job.content",
    "derived/runtime_decision_wiring.json::excerpts.adapter_execute_smoke_job.content",
]
COMPLETED_FAILURE_TEXT = (
    "For a benchmark-counted completed record, retained final validation after the locked action budget "
    "establishes that native success was not reached: the page and URL are valid but `done` is false or "
    "binary `reward` is `0.0`."
)
SCOPE_ARTIFACT_QUESTION = (
    "Do the concrete final validation and step records establish a benchmark-counted completed record whose "
    "locked action budget ended without native success? A non-completed `INFRA_EXCLUDED` record is outside "
    "S/F/U evidence scoring."
)
UNDECIDED_TEXT = (
    "The record is within evidence-scoring scope, but the retained artifacts establish neither the native "
    "success condition nor a decisive final completed-record failure condition."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--source-case-packet-root", type=Path, required=True)
    parser.add_argument("--case-packet-root", type=Path, required=True)
    parser.add_argument("--delete-source", action="store_true", required=True)
    return parser.parse_args()


def _load_mapping(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected mapping: {path}")
    return value


def _is_broad_run_failure(text: str) -> bool:
    lowered = text.lower()
    return "benchmark-counted" in lowered or any(
        marker in lowered
        for marker in ("invalid action", "tool misuse", "exhausted run budget")
    )


def _required_condition(packet_path: Path) -> dict[str, Any]:
    context_path = packet_path.parent / "raw_case/derived/drafting_context.json"
    context = json.loads(context_path.read_text(encoding="utf-8"))
    items = context["stronger_measurement"]["required_additional_conditions"]
    if len(items) != 1:
        raise ValueError(f"expected one required stronger condition: {packet_path}")
    return dict(items[0])


def _remediate_native(checklist: dict[str, Any], *, case_id: str) -> list[str]:
    native = checklist["native"]
    changes: list[str] = []

    retained_failures = [
        item for item in native["fail_if"] if not _is_broad_run_failure(str(item.get("text") or ""))
    ]
    if len(retained_failures) != len(native["fail_if"]):
        changes.append("removed_subjective_or_infra_conflating_failure_rule")
    retained_failures.append({"text": COMPLETED_FAILURE_TEXT, "support": list(RUNTIME_SUPPORT)})
    native["fail_if"] = retained_failures
    changes.append("bound_native_failure_to_completed_record_wiring")

    for artifact in native["decisive_artifacts"]:
        if _is_broad_run_failure(str(artifact.get("question") or "")):
            artifact["question"] = SCOPE_ARTIFACT_QUESTION
            artifact["support"] = list(dict.fromkeys([*artifact["support"], *RUNTIME_SUPPORT]))
            changes.append("repaired_run_status_artifact_scope")

    for item in native["undecided_if"]:
        if _is_broad_run_failure(str(item.get("text") or "")):
            item["text"] = UNDECIDED_TEXT
            item["support"] = [
                "derived/drafting_context.json::released_evaluator.summary_field_guard",
                "derived/drafting_context.json::released_evaluator.record_scope_rule",
                "derived/drafting_context.json::artifact_inventory.retained_artifacts[2].path",
            ]
            changes.append("repaired_native_undecided_scope")

    if case_id == "miniwob.draw-circle":
        native["user_goal"]["support"] = [
            "derived/drafting_context.json::task_text.static_query_text",
            "official/install/miniwob/html/miniwob/draw-circle.html::lines 181-184",
        ]
        changes.append("repaired_direct_user_goal_support")
    elif case_id == "miniwob.terminal":
        native["user_goal"]["support"] = [
            "derived/drafting_context.json::task_text.static_query_text",
            "official/install/miniwob/html/miniwob/terminal.html::lines 196-200",
        ]
        changes.append("repaired_direct_user_goal_support")
    return changes


def _circle_condition(condition: Mapping[str, Any]) -> dict[str, Any]:
    basis_pointer = (
        "derived/drafting_context.json::stronger_measurement."
        "required_additional_conditions[0].decisive_post_run_artifacts"
    )
    return {
        "id": condition["id"],
        "text": condition["text"],
        "rationale": condition["rationale"],
        "decisive_artifacts": [
            {
                "artifact": "browser_artifacts/screenshots/ and BrowserGym video recordings",
                "question": (
                    "Do the retained visuals establish a complete circular path centered around the marker, "
                    "rather than only a partial arc or radial segment, and show that it was submitted?"
                ),
                "support": [
                    basis_pointer,
                    "official/install/miniwob/html/miniwob/draw-circle.html::lines 181-184",
                    "official/install/miniwob/html/miniwob/draw-circle.html::genProblem",
                ],
            },
            {
                "artifact": "trajectory/steps.json and trajectory/observations/",
                "question": (
                    "Does the retained stroke/action sequence corroborate full angular coverage around the "
                    "marked center and the submit action?"
                ),
                "support": [
                    basis_pointer,
                    "official/install/miniwob/html/miniwob/draw-circle.html::findStandardDev",
                ],
            },
            {
                "artifact": "native_evaluator_output.json",
                "question": (
                    "Does the final validator corroborate submission and native success? Raw reward alone is "
                    "not decisive for circle completeness."
                ),
                "support": [
                    basis_pointer,
                    "official/install/miniwob/html/miniwob/draw-circle.html::determineReward",
                    "official/install/miniwob/html/miniwob/draw-circle.html::properlySized",
                ],
            },
        ],
        "support": list(condition["support"]),
    }


def _terminal_condition(condition: Mapping[str, Any]) -> dict[str, Any]:
    basis_pointer = (
        "derived/drafting_context.json::stronger_measurement."
        "required_additional_conditions[0].decisive_post_run_artifacts"
    )
    return {
        "id": condition["id"],
        "text": condition["text"],
        "rationale": condition["rationale"],
        "decisive_artifacts": [
            {
                "artifact": "trajectory/steps.json and trajectory/observations/",
                "question": (
                    "Which exact filename was passed to `rm`, and does it have the requested dot-delimited "
                    "suffix (or no dot for the no-extension query)?"
                ),
                "support": [
                    basis_pointer,
                    "official/install/miniwob/html/miniwob/terminal.html::removeContents",
                    "official/install/miniwob/html/miniwob/terminal.html::lines 196-200",
                ],
            },
            {
                "artifact": "browser_artifacts/page_html/ and browser_artifacts/screenshots/",
                "question": (
                    "Do the retained terminal listing and runtime query corroborate the exact deleted "
                    "filename and literal extension requirement?"
                ),
                "support": [
                    basis_pointer,
                    "official/install/miniwob/html/miniwob/terminal.html::lines 52-53",
                    "official/install/miniwob/html/miniwob/terminal.html::lines 196-200",
                ],
            },
        ],
        "support": list(condition["support"]),
    }


def _remediate_stronger(
    checklist: dict[str, Any], *, case_id: str, packet_path: Path
) -> list[str]:
    if case_id not in {"miniwob.draw-circle", "miniwob.terminal"}:
        return []
    condition = _required_condition(packet_path)
    checklist["stronger"]["additional_conditions"] = [
        _circle_condition(condition)
        if case_id == "miniwob.draw-circle"
        else _terminal_condition(condition)
    ]
    return [
        "replaced_reward_proxy_with_goal_faithful_circle_condition"
        if case_id == "miniwob.draw-circle"
        else "added_literal_extension_requirement"
    ]


def _validate(checklist: dict[str, Any], *, packet_path: Path, schema: Mapping[str, Any]) -> None:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(checklist),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if errors:
        raise ValueError("; ".join(error.message for error in errors))
    allowed = case_packet_support_paths(packet_path.read_text(encoding="utf-8"))
    validate_checklist_guardrails(checklist, allowed_source_paths=allowed)
    validate_support_pointers(checklist, packet_path)
    validate_packet_required_stronger_conditions(checklist, packet_path)


def _rebuild_case_packets(*, source_root: Path, output_root: Path) -> list[str]:
    if output_root.exists():
        raise ValueError(f"v2 packet root already exists: {output_root}")
    case_ids = sorted(path.name for path in source_root.iterdir() if path.is_dir())
    if len(case_ids) != EXPECTED_COUNT:
        raise ValueError(f"expected 22 source packet cases, observed {len(case_ids)}")

    stage_parent = output_root.parent
    stage_parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.stage-", dir=stage_parent))
    try:
        for case_id in case_ids:
            source_case_dir = source_root / case_id
            source_manifest = json.loads(
                (source_case_dir / "raw_case_manifest.json").read_text(encoding="utf-8")
            )
            source_raw = source_case_dir / "raw_case"
            for relative, expected in source_manifest["sha256_per_file"].items():
                actual = sha256_file(source_raw / relative)
                if actual != expected:
                    raise ValueError(f"source packet hash mismatch: {case_id}/{relative}")

            target_case_dir = stage / case_id
            target_raw = target_case_dir / "raw_case"
            shutil.copytree(source_raw, target_raw)
            payload = json.loads(
                (target_raw / "derived/selected_task_source.json").read_text(encoding="utf-8")
            )
            file_sources = dict(source_manifest["file_sources"])
            source_refs = list(source_manifest["source_refs"])
            official_files = list(source_manifest["official_files"])
            derived_files = list(source_manifest["derived_files"])
            packet_files = list(source_manifest["packet_files"])
            _materialize_miniwob_drafting_sources(
                target_raw,
                payload=payload,
                file_sources=file_sources,
                source_refs=source_refs,
                official_files=official_files,
                derived_files=derived_files,
                packet_files=packet_files,
            )
            manifest = _raw_case_manifest(
                domain="miniwob",
                case_unit_id=case_id,
                task_id=case_id,
                raw_case_dir=target_raw,
                source_refs=[value for value in source_refs if value],
                file_sources=file_sources,
                official_files=official_files,
                derived_files=derived_files,
                packet_files=packet_files,
                source_metadata={},
            )
            (target_case_dir / "raw_case_manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (target_case_dir / "case_packet.md").write_text(
                render_case_packet(
                    domain="miniwob",
                    case_unit_id=case_id,
                    task_id=case_id,
                    raw_case_dir=target_raw,
                    raw_case_manifest=manifest,
                ),
                encoding="utf-8",
            )
        os.replace(stage, output_root)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return case_ids


def main() -> int:
    args = parse_args()
    source_root = args.source_root.resolve()
    output_root = args.output_root.resolve()
    source_packet_root = args.source_case_packet_root.resolve()
    packet_root = args.case_packet_root.resolve()
    if source_root.name != OLD_REVIEWED_BASENAME:
        raise ValueError(f"refusing to delete unexpected source root: {source_root}")
    if output_root.name != NEW_REVIEWED_BASENAME or output_root.parent != source_root.parent:
        raise ValueError("output must be the reviewed_system_design_v2 sibling of reviewed v1")
    if not source_root.is_dir() or source_root.is_symlink():
        raise ValueError(f"source root is missing or unsafe: {source_root}")
    if output_root.exists():
        raise ValueError(f"output root already exists: {output_root}")

    case_ids = sorted(path.name for path in source_root.iterdir() if path.is_dir())
    if len(case_ids) != EXPECTED_COUNT or any(not case_id.startswith("miniwob.") for case_id in case_ids):
        raise ValueError(f"expected exactly 22 MiniWoB case directories, observed {len(case_ids)}")
    rebuilt_packet_ids = _rebuild_case_packets(
        source_root=source_packet_root,
        output_root=packet_root,
    )
    packet_ids = sorted(path.name for path in packet_root.iterdir() if path.is_dir())
    if packet_ids != case_ids:
        raise ValueError("source checklist and v2 packet case sets differ")
    if rebuilt_packet_ids != case_ids:
        raise ValueError("rebuilt v2 packet set differs from reviewed checklist set")

    schema = json.loads(
        (ROOT / "neurips_ed_track_minimal/schemas/case_checklist.schema.json").read_text(
            encoding="utf-8"
        )
    )
    source_tree_sha256 = sha256_path(source_root)
    stage = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.stage-", dir=output_root.parent))
    cases: list[dict[str, Any]] = []
    try:
        for case_id in case_ids:
            source_yaml = source_root / case_id / "checklist.yaml"
            packet_path = packet_root / case_id / "case_packet.md"
            checklist = _load_mapping(source_yaml)
            changes = _remediate_native(checklist, case_id=case_id)
            changes.extend(_remediate_stronger(checklist, case_id=case_id, packet_path=packet_path))
            _validate(checklist, packet_path=packet_path, schema=schema)

            case_dir = stage / case_id
            case_dir.mkdir()
            yaml_path = case_dir / "checklist.yaml"
            json_path = case_dir / "checklist.json"
            yaml_path.write_text(
                yaml.safe_dump(checklist, sort_keys=False, allow_unicode=True, width=110),
                encoding="utf-8",
            )
            json_path.write_text(
                json.dumps(checklist, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            cases.append(
                {
                    "case_unit_id": case_id,
                    "changes": sorted(set(changes)),
                    "source_checklist_sha256": sha256_file(source_yaml),
                    "v2_contract_sha256": sha256_object(checklist),
                    "v2_yaml_sha256": sha256_file(yaml_path),
                    "v2_json_sha256": sha256_file(json_path),
                }
            )

        receipt = {
            "schema_version": "miniwob_remaining22_checklist_remediation/v1",
            "status": "reviewed_v2",
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "case_count": len(cases),
            "scope": {
                "phase": "prospective_pre_run_contract_revision",
                "reads_result_namespaces": False,
                "applies_to_existing_v1_results": False,
                "source_packet_basis": packet_root.relative_to(ROOT).as_posix(),
            },
            "retired_source": {
                "path": source_root.relative_to(ROOT).as_posix(),
                "tree_sha256_before_deletion": source_tree_sha256,
                "deleted_after_v2_validation": True,
            },
            "cases": cases,
        }
        (stage / "remediation_receipt.json").write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        os.replace(stage, output_root)
        shutil.rmtree(source_root)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        if output_root.exists() and not source_root.exists():
            raise
        raise

    print(
        json.dumps(
            {
                "status": "ok",
                "created": output_root.relative_to(ROOT).as_posix(),
                "deleted": source_root.relative_to(ROOT).as_posix(),
                "case_count": len(cases),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
