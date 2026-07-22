#!/usr/bin/env python3
"""Package the 75 non-paper AndroidWorld drafts for outcome-blind evidence scoring.

The package has one task per (case, agent) record.  It preserves the released
label as a task sidecar for post-model joining, but the Codex scorer receives
only the allowlisted evidence view under ``evidence/``.  In particular, the
raw record and result-bearing evaluator artifacts are never copied into that
model-visible tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEWED_ROOT = (
    REPO_ROOT
    / "transfer/androidworld_remaining75_draft_gpt54_high_c11_v3_20260719"
    / "final_reviewed75_results"
)
DEFAULT_CANONICAL_DRAFT_ROOT = REPO_ROOT / "results/drafts/androidworld_full100"
DEFAULT_RUN_ROOT = REPO_ROOT / "results/full/androidworld"
DEFAULT_SELECTION = (
    REPO_ROOT
    / "transfer/androidworld_remaining75_draft_gpt54_high_c11_v3_20260719"
    / "FINAL_SELECTION.json"
)
DEFAULT_EXECUTION_LOCK = REPO_ROOT / "androidworld_gold_execution/execution_provenance.lock.json"
DEFAULT_OUTPUT_ROOT = (
    REPO_ROOT
    / "transfer/androidworld_remaining75_score_gpt54_high_c32_v2_blind_20260720"
    / "score_job"
)

AGENTS = ("agent_a", "agent_b", "agent_c")
AGENT_LABELS = {"agent_a": "Agent A", "agent_b": "Agent B", "agent_c": "Agent C"}
EXCLUDED_NATIVE_RUN_NAMES = {
    "episode_metadata.json",
    "native_evaluator_output.json",
    "run_summary.json",
    "raw_run.json",
    "worker_config.json",
}
EXCLUDED_NATIVE_RUN_PARTS = {"checkpoint_dir", "evaluator_artifacts"}
FORBIDDEN_MODEL_VISIBLE_SUFFIXES = {".gz", ".pickle", ".pkl"}
FORBIDDEN_RESULT_KEYS = {
    "native_label",
    "native_score",
    "released_evaluator_label",
    "released_evaluator_score",
}


class PackageError(RuntimeError):
    """Raised when an AndroidWorld record cannot be safely packaged."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed-root", type=Path, default=DEFAULT_REVIEWED_ROOT)
    parser.add_argument("--canonical-draft-root", type=Path, default=DEFAULT_CANONICAL_DRAFT_ROOT)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--execution-lock", type=Path, default=DEFAULT_EXECUTION_LOCK)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PackageError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PackageError(f"expected a JSON object: {path}")
    return payload


def load_json_value(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PackageError(f"cannot read JSON {path}: {exc}") from exc


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_tree(root: Path) -> str:
    entries = [
        {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    ]
    return hashlib.sha256(
        json.dumps(entries, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require_real_directory(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_dir():
        raise PackageError(f"{label} must be a real directory: {path}")


def require_real_file(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise PackageError(f"{label} must be a regular file: {path}")


def copy_regular_file(source: Path, target: Path) -> None:
    require_real_file(source, "source file")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_visible_native_run(source: Path, target: Path) -> list[str]:
    require_real_directory(source, "native run directory")
    copied: list[str] = []
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if path.is_symlink():
            raise PackageError(f"native run contains a symlink: {path}")
        if any(part.lower() in EXCLUDED_NATIVE_RUN_PARTS for part in relative.parts):
            continue
        if path.is_dir():
            continue
        if not path.is_file():
            raise PackageError(f"native run contains a non-regular file: {path}")
        if path.name.lower() in EXCLUDED_NATIVE_RUN_NAMES:
            continue
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        copied.append(relative.as_posix())
    if not copied:
        raise PackageError(f"no scorer-visible artifacts copied from {source}")
    return copied


def find_result_leaks(value: Any, pointer: str = "$") -> list[str]:
    leaks: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_pointer = f"{pointer}.{key}"
            normalized = str(key).strip().lower()
            if normalized in FORBIDDEN_RESULT_KEYS:
                leaks.append(child_pointer)
            if normalized == "is_successful" and not isinstance(child, (dict, list, str)):
                leaks.append(child_pointer)
            leaks.extend(find_result_leaks(child, child_pointer))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            leaks.extend(find_result_leaks(child, f"{pointer}[{index}]"))
    return leaks


def validate_model_visible_evidence(root: Path) -> dict[str, int]:
    file_count = 0
    json_count = 0
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        file_count += 1
        if path.suffix.lower() in FORBIDDEN_MODEL_VISIBLE_SUFFIXES:
            raise PackageError(f"compressed/pickle artifact is not allowed in model evidence: {path}")
        if path.suffix.lower() != ".json":
            continue
        json_count += 1
        payload = load_json_value(path)
        leaks = find_result_leaks(payload)
        if leaks:
            raise PackageError(f"result-bearing JSON fields in model evidence {path}: {leaks}")
    return {"file_count": file_count, "json_count": json_count}


def read_case_ids(reviewed_root: Path) -> list[str]:
    cases = sorted(path.name for path in reviewed_root.iterdir() if path.is_dir())
    if len(cases) != 75 or len(set(cases)) != 75:
        raise PackageError(f"expected exactly 75 reviewed case directories, found {len(cases)}")
    return cases


def validate_checklist_identity(path: Path, case_id: str) -> None:
    require_real_file(path, "checklist")
    expected = f"case_unit_id: {case_id}"
    lines = path.read_text(encoding="utf-8").splitlines()
    if expected not in lines:
        raise PackageError(f"checklist case identity mismatch for {case_id}: {path}")


def main() -> int:
    args = parse_args()
    reviewed_root = args.reviewed_root.resolve()
    canonical_root = args.canonical_draft_root.resolve()
    run_root = args.run_root.resolve()
    selection_path = args.selection.resolve()
    execution_lock_path = args.execution_lock.resolve()
    output_root = args.output_root.resolve()

    for path, label in (
        (reviewed_root, "reviewed draft root"),
        (canonical_root, "canonical draft root"),
        (run_root, "run root"),
    ):
        require_real_directory(path, label)
    require_real_file(selection_path, "final draft selection")
    require_real_file(execution_lock_path, "execution provenance lock")
    if output_root.exists():
        raise PackageError(f"refusing to overwrite existing output root: {output_root}")

    selection = load_json(selection_path)
    execution_lock = load_json(execution_lock_path)
    if selection.get("case_count") != 75:
        raise PackageError("final selection does not claim exactly 75 cases")
    if execution_lock.get("completion", {}).get("status") != "complete":
        raise PackageError("AndroidWorld execution provenance is not complete")
    if execution_lock.get("completion", {}).get("neurips_ed_track_minimal_score_invoked") is not False:
        raise PackageError("AndroidWorld provenance no longer represents a pre-score source")

    case_ids = read_case_ids(reviewed_root)
    canonical_case_ids = sorted(path.name for path in canonical_root.iterdir() if path.is_dir())
    if len(canonical_case_ids) != 116:
        raise PackageError(f"expected 116 canonical AndroidWorld drafts, found {len(canonical_case_ids)}")
    excluded_paper_cases = sorted(set(canonical_case_ids) - set(case_ids))
    if len(excluded_paper_cases) != 41:
        raise PackageError(
            f"expected 41 paper-draft cases excluded from score input, found {len(excluded_paper_cases)}"
        )

    drafts_root = output_root / "drafts_75"
    tasks_root = output_root / "tasks"
    drafts_root.mkdir(parents=True)
    tasks_root.mkdir()
    task_records: list[dict[str, Any]] = []
    source_run_records: list[dict[str, Any]] = []

    for case_id in case_ids:
        reviewed_case = reviewed_root / case_id
        canonical_case = canonical_root / case_id
        reviewed_checklist = reviewed_case / "checklist.yaml"
        canonical_checklist = canonical_case / "checklist.yaml"
        validate_checklist_identity(reviewed_checklist, case_id)
        validate_checklist_identity(canonical_checklist, case_id)
        if sha256_file(reviewed_checklist) != sha256_file(canonical_checklist):
            raise PackageError(f"reviewed/canonical checklist drift for {case_id}")
        shutil.copytree(canonical_case, drafts_root / case_id)

        for agent_slug in AGENTS:
            task_id = f"full-androidworld-{case_id}-{agent_slug}"
            source_adapter = run_root / task_id / "adapter"
            raw_run_path = source_adapter / "raw_run.json"
            native_run = source_adapter / "native_run"
            require_real_directory(source_adapter, f"source adapter for {task_id}")
            require_real_file(raw_run_path, f"raw run for {task_id}")
            raw_run = load_json(raw_run_path)
            if raw_run.get("case_unit_id") != case_id:
                raise PackageError(f"source run case mismatch for {task_id}")
            if raw_run.get("agent_id") != AGENT_LABELS[agent_slug]:
                raise PackageError(f"source run agent mismatch for {task_id}")
            if raw_run.get("status") != "COMPLETED":
                raise PackageError(f"source run is not completed for {task_id}")
            released_label = str(raw_run.get("native_label") or "").strip().lower()
            if released_label not in {"success", "fail"}:
                raise PackageError(f"source run has invalid released label for {task_id}")

            task_dir = tasks_root / task_id
            evidence_dir = task_dir / "evidence"
            task_dir.mkdir()
            copy_regular_file(canonical_checklist, task_dir / "checklist.yaml")
            visible_files = copy_visible_native_run(native_run, evidence_dir / "native_run")
            evidence_index = {
                "schema_version": "androidworld_score_view_index/v1",
                "case_unit_id": case_id,
                "agent": agent_slug,
                "source_adapter_tree_sha256": sha256_tree(source_adapter),
                "source_native_run_tree_sha256": sha256_tree(native_run),
                "model_visible_files": visible_files,
                "excluded_result_bearing_paths": [
                    "raw_run.json",
                    "native_run/raw_run.json",
                    "native_run/run_summary.json",
                    "native_run/native_evaluator_output.json",
                    "native_run/evaluator_artifacts/**",
                    "native_run/checkpoint_dir/**",
                    "native_run/post_run_artifacts/episode_metadata.json",
                    "native_run/worker_config.json",
                ],
                "released_evaluator_label_visible_to_model": False,
                "released_evaluator_score_visible_to_model": False,
                "purpose": "Navigation and visibility receipt only; not decisive evidence.",
            }
            write_json(evidence_dir / "index.json", evidence_index)
            visibility_audit = validate_model_visible_evidence(evidence_dir)
            native_label = {
                "value": released_label,
                "source": "source_adapter/raw_run.json::native_label",
                "source_file_sha256": sha256_file(raw_run_path),
                "model_visible": False,
                "join_policy": "The batch scorer stages only checklist.yaml and evidence/ before invoking Codex; this sidecar is joined only after native/stronger model output is produced and validated.",
            }
            write_json(task_dir / "native_label.json", native_label)

            evidence_hash = sha256_tree(evidence_dir)
            record = {
                "task_id": task_id,
                "case_unit_id": case_id,
                "agent": agent_slug,
                "checklist_sha256": sha256_file(task_dir / "checklist.yaml"),
                "evidence_tree_sha256": evidence_hash,
                "native_label_sha256": sha256_file(task_dir / "native_label.json"),
                "source_adapter_tree_sha256": sha256_tree(source_adapter),
                "source_native_run_tree_sha256": sha256_tree(native_run),
                "model_visible_released_label": False,
                "model_visible_visibility_audit": visibility_audit,
            }
            task_records.append(record)
            source_run_records.append(
                {
                    "task_id": task_id,
                    "source_adapter": str(source_adapter),
                    "source_adapter_tree_sha256": record["source_adapter_tree_sha256"],
                    "raw_run_sha256": sha256_file(raw_run_path),
                }
            )

    if len(task_records) != 225:
        raise PackageError(f"expected 225 score tasks, built {len(task_records)}")
    if len({record["task_id"] for record in task_records}) != 225:
        raise PackageError("duplicate score task ID")

    receipt = {
        "schema_version": "androidworld_remaining75_outcome_blind_score_package/v1",
        "status": "ready",
        "case_count": 75,
        "record_count": 225,
        "agents": list(AGENTS),
        "excluded_paper_case_count": 41,
        "excluded_paper_case_ids": excluded_paper_cases,
        "source_locks": {
            "final_selection": {"path": str(selection_path), "sha256": sha256_file(selection_path)},
            "execution_provenance": {"path": str(execution_lock_path), "sha256": sha256_file(execution_lock_path)},
            "canonical_draft_tree_sha256": sha256_tree(canonical_root),
            "reviewed75_tree_sha256": sha256_tree(reviewed_root),
            "source_run_tree_sha256": sha256_tree(run_root),
        },
        "scoring_lock": {
            "provider": "neurips_ed_track_minimal",
            "model": "gpt-5.4",
            "reasoning_effort": "high",
            "service_tier": "default",
            "fast_mode": False,
            "auth_mode": "codex_login",
            "sandbox": "read-only",
            "max_parallel": 32,
        },
        "system_design": {
            "checklists_locked_before_evidence_scoring": True,
            "draft_selection_outcome_blind": selection.get("selection_policy", {}).get("outcome_blind") is True,
            "model_visible_released_evaluator_labels": False,
            "model_visible_released_evaluator_scores": False,
            "native_scored_as_S_F_U_from_locked_checklist_and_retained_evidence": True,
            "stronger_reported_separately": True,
            "benchmark_conflict_not_inferred_from_native_and_stronger_scores": True,
            "released_label_joined_after_model_output": True,
            "checkpoint_and_episode_result_artifacts_excluded": True,
            "model_visible_evidence_fail_closed_scanned": True,
        },
        "drafts_tree_sha256": sha256_tree(drafts_root),
        "tasks_tree_sha256": sha256_tree(tasks_root),
        "tasks": task_records,
        "source_runs": source_run_records,
    }
    write_json(output_root / "transfer_receipt.json", receipt)
    print(json.dumps({"status": "ready", "case_count": 75, "record_count": 225, "output_root": str(output_root)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
