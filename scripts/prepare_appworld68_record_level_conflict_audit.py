#!/usr/bin/env python3
"""Build source-locked record-level conflict-audit workspaces for AppWorld-68."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
CASE_BUNDLE = (
    REPO_ROOT
    / "experiments/appworld_test_normal_68_system_design_v4_runtime_semantics_gpt54_high_v1"
)
PUBLIC_JOB = (
    REPO_ROOT
    / "transfer/appworld68_tn_blind_score_system_design_v4_runtime_semantics_20260719_v1/public_score_job"
)
SCORE_RUN = (
    REPO_ROOT
    / "transfer/appworld68_tn_blind_score_gpt54_high_default_c34_20260720_v2_runtime_semantics"
)
RETAINED_ROOT = Path("/Users/gss/Downloads/appworld585_20260719_full_v1_completed")
RUNTIME_ROOT = (
    REPO_ROOT
    / "experiments/appworld_evaluator_runtime_0.2.0.dev0_a072b7a_v2_semantic_closure"
)
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "transfer/appworld68_tn_record_level_conflict_audit_gpt54_high_c34_20260722_v1"
)
OFFICIAL_COMMIT = "a072b7a86e7c1d5b1d7175659d750ebb9b79f10a"
EXPECTED_CASES = 68
AGENTS = ("agent_a", "agent_b", "agent_c")
AGENT_NAMES = {"agent_a": "Agent A", "agent_b": "Agent B", "agent_c": "Agent C"}

OUR_SOURCE_FILES = {
    "src/evidence_system/adapters/appworld_official_worker.py": "appworld_official_worker.py",
    "scripts/appworld_full_585_two_vps/run_campaign.py": "run_campaign.py",
    "scripts/package_appworld68_blind_score_job.py": "package_appworld68_blind_score_job.py",
    "neurips_ed_track_minimal/scripts/score_evidence_blind_with_codex.py": "score_evidence_blind_with_codex.py",
    "scripts/audit_join_appworld68_blind_scores.py": "audit_join_appworld68_blind_scores.py",
    "scripts/build_appworld68_system_design_v4_runtime_semantics.py": "build_appworld68_system_design_v4_runtime_semantics.py",
    "src/evidence_system/contracts/appworld_checklist_semantics.py": "appworld_checklist_semantics.py",
    "src/evidence_system/contracts/appworld_refreeze_v56.py": "appworld_refreeze_v56.py",
    "src/evidence_system/contracts/appworld_draft_acceptance_v56.py": "appworld_draft_acceptance_v56.py",
}
OFFICIAL_CORE_FILES = (
    "src/appworld/task.py",
    "src/appworld/ground_truth.py",
    "src/appworld/environment.py",
)
RETAINED_TOP_FILES = (
    "artifact_manifest.json",
    "job.json",
    "native_evaluator_input.json",
    "native_evaluator_output.json",
    "official_runner_config.json",
    "run_summary.json",
    "source_bundle_entry.json",
    "worker_config.json",
)
RETAINED_SUBTREES = (
    "appworld_task_output/dbs",
    "appworld_task_output/evaluation",
    "appworld_task_output/misc",
    "appworld_task_output/version",
)
RETAINED_LOG_FILES = (
    "appworld_task_output/logs/api_calls.jsonl",
    "appworld_task_output/logs/environment_io.md",
)
SCORE_FILES = (
    "score.json",
    "score.yaml",
    "score_manifest.json",
    "score.blind_lock.json",
    "score.native.model_output.json",
    "score.native.lock.json",
    "score.native.output_schema.json",
    "score.stronger.model_output.json",
    "score.stronger.lock.json",
    "score.stronger.output_schema.json",
)


class AuditBuildError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-repo", type=Path, required=True)
    parser.add_argument("--retained-root", type=Path, default=RETAINED_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha(value: Any) -> str:
    data = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditBuildError(f"cannot load JSON {path}: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require_file(path: Path) -> Path:
    if path.is_symlink() or not path.is_file():
        raise AuditBuildError(f"missing regular file: {path}")
    return path


def require_dir(path: Path) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise AuditBuildError(f"missing real directory: {path}")
    return path


def copy_file(source: Path, destination: Path) -> None:
    require_file(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    # The review process runs Codex in a read-only sandbox under a separate
    # OS identity.  Retained artifacts can be mode 0600 on the collection
    # host, so preserving their source mode would make an otherwise complete
    # audit packet unreadable to the reviewer.
    destination.chmod(0o644)
    if sha256_file(source) != sha256_file(destination):
        raise AuditBuildError(f"copy hash mismatch: {source} -> {destination}")


def copy_tree(source: Path, destination: Path) -> None:
    require_dir(source)
    if destination.exists():
        raise AuditBuildError(f"destination already exists: {destination}")
    shutil.copytree(source, destination, symlinks=False)
    destination.chmod(0o755)
    for path in destination.rglob("*"):
        if path.is_symlink():
            raise AuditBuildError(f"copied audit tree contains symlink: {path}")
        path.chmod(0o755 if path.is_dir() else 0o644)


def git_output(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise AuditBuildError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def build_official_runtime(official_repo: Path, destination: Path) -> dict[str, Any]:
    resolved = official_repo.resolve()
    commit = git_output(resolved, "rev-parse", "HEAD")
    if commit != OFFICIAL_COMMIT:
        raise AuditBuildError(f"official checkout commit differs: {commit}")
    destination.mkdir(parents=True, exist_ok=False)
    entries: list[dict[str, Any]] = []
    for relative in OFFICIAL_CORE_FILES:
        source = resolved / relative
        target = destination / Path(relative).name
        copy_file(source, target)
        entries.append({"path": target.name, "sha256": sha256_file(target), "git_path": relative})
    runtime_source = RUNTIME_ROOT / "src/appworld"
    for source in sorted(path for path in runtime_source.rglob("*") if path.is_file()):
        relative = source.relative_to(runtime_source)
        target = destination / relative
        if target.exists():
            if sha256_file(source) != sha256_file(target):
                raise AuditBuildError(f"official runtime/core collision: {relative}")
            continue
        copy_file(source, target)
        entries.append({"path": relative.as_posix(), "sha256": sha256_file(target)})
    manifest = load_json(RUNTIME_ROOT / "SOURCE_MANIFEST.json")
    if manifest.get("commit") != OFFICIAL_COMMIT:
        raise AuditBuildError("runtime source manifest commit differs")
    return {
        "repository": "https://github.com/StonyBrookNLP/appworld",
        "commit": commit,
        "runtime_source_manifest_sha256": sha256_file(RUNTIME_ROOT / "SOURCE_MANIFEST.json"),
        "files": sorted(entries, key=lambda item: item["path"]),
    }


def build_our_sources(destination: Path) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=False)
    entries: list[dict[str, Any]] = []
    for source_relative, target_name in OUR_SOURCE_FILES.items():
        source = REPO_ROOT / source_relative
        target = destination / target_name
        copy_file(source, target)
        entries.append(
            {"path": target_name, "source_path": source_relative, "sha256": sha256_file(target)}
        )
    head = git_output(REPO_ROOT, "rev-parse", "HEAD")
    dirty = git_output(REPO_ROOT, "status", "--porcelain", "--untracked-files=no", "--", *OUR_SOURCE_FILES)
    if dirty:
        raise AuditBuildError(f"tracked audit/runtime sources are dirty:\n{dirty}")
    return {"repository_commit": head, "tracked_sources_clean": True, "files": entries}


def locate_retained_records(retained_root: Path, case_ids: Iterable[str]) -> dict[tuple[str, str], Path]:
    wanted = set(case_ids)
    found: dict[tuple[str, str], Path] = {}
    for vps in ("vps1", "vps2"):
        for agent in AGENTS:
            base = retained_root / vps / "outputs" / agent
            if not base.is_dir():
                continue
            for case_id in wanted:
                candidate = base / case_id
                if not candidate.is_dir():
                    continue
                key = (case_id, agent)
                if key in found:
                    raise AuditBuildError(f"duplicate retained record: {key}")
                found[key] = candidate
    expected = {(case_id, agent) for case_id in wanted for agent in AGENTS}
    if set(found) != expected:
        missing = sorted(expected - set(found))
        raise AuditBuildError(f"missing retained records: {missing[:10]}")
    return found


def copy_retained_record(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    for relative in RETAINED_TOP_FILES:
        copy_file(source / relative, destination / relative)
    for relative in RETAINED_SUBTREES:
        copy_tree(source / relative, destination / relative)
    for relative in RETAINED_LOG_FILES:
        copy_file(source / relative, destination / relative)
    forbidden = [
        path
        for path in destination.rglob("*")
        if path.is_file() and ("lm_calls" in path.name or "logger" in path.name)
    ]
    if forbidden:
        raise AuditBuildError(f"sensitive/nonessential LM or logger files copied: {forbidden[:3]}")


def copy_blind_evidence(task_root: Path, record_root: Path) -> None:
    evidence = task_root / "evidence"
    blind_package = record_root / "blind_package"
    blind_package.mkdir(parents=True, exist_ok=False)
    copy_file(evidence / "index.json", blind_package / "evidence_index.json")
    copy_tree(evidence / "run", record_root / "blind_evidence" / "run")
    frozen = evidence / "frozen_semantics"
    if frozen.is_dir():
        copy_tree(frozen, record_root / "blind_evidence" / "frozen_semantics")
    forbidden_names = {
        "native_evaluator_output.json",
        "run_summary.json",
        "artifact_manifest.json",
        "report.md",
    }
    leaked = [path for path in (record_root / "blind_evidence").rglob("*") if path.name in forbidden_names]
    if leaked:
        raise AuditBuildError(f"blind evidence contains released/component output: {leaked[:3]}")


def copy_score(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    for relative in SCORE_FILES:
        copy_file(source / relative, destination / relative)


def file_inventory(root: Path) -> list[dict[str, Any]]:
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    ]


def main() -> int:
    args = parse_args()
    output_root = args.output_root.resolve()
    if output_root.exists():
        raise AuditBuildError(f"refusing existing output root: {output_root}")
    require_dir(args.retained_root)
    require_dir(args.official_repo)
    case_root = require_dir(CASE_BUNDLE / "case_packets/appworld")
    case_ids = sorted(path.name for path in case_root.iterdir() if path.is_dir())
    if len(case_ids) != EXPECTED_CASES:
        raise AuditBuildError(f"expected {EXPECTED_CASES} cases, found {len(case_ids)}")
    retained = locate_retained_records(args.retained_root.resolve(), case_ids)
    package = load_json(PUBLIC_JOB / "package_manifest.json")
    package_records = {
        str(item["task_id"]): item for item in package.get("records", []) if isinstance(item, dict)
    }
    if len(package_records) != EXPECTED_CASES * len(AGENTS):
        raise AuditBuildError("public package record denominator differs")

    output_root.mkdir(parents=True, exist_ok=False)
    shared_root = output_root / "shared_sources"
    official_lock = build_official_runtime(args.official_repo, shared_root / "official_appworld")
    our_lock = build_our_sources(shared_root / "our_system")
    copy_file(RUNTIME_ROOT / "SOURCE_MANIFEST.json", shared_root / "official_appworld/SOURCE_MANIFEST.json")

    index: list[dict[str, Any]] = []
    for case_id in case_ids:
        source_case = case_root / case_id
        workspace = output_root / "workspaces" / case_id
        workspace.mkdir(parents=True, exist_ok=False)
        copy_tree(source_case / "raw_case/official", workspace / "official")
        copy_file(source_case / "case_packet.md", workspace / "case_packet.md")
        copy_file(source_case / "raw_case_manifest.json", workspace / "raw_case_manifest.json")
        copy_tree(shared_root / "official_appworld", workspace / "runtime_wiring/official_appworld")
        copy_tree(shared_root / "our_system", workspace / "runtime_wiring/our_system")

        checklist_hashes: set[str] = set()
        expected_records: list[dict[str, Any]] = []
        for agent in AGENTS:
            task_id = f"{case_id}__{agent}"
            task_root = PUBLIC_JOB / "tasks" / task_id
            record_root = workspace / "records" / agent
            record_root.mkdir(parents=True, exist_ok=False)
            checklist_hashes.add(sha256_file(task_root / "checklist.yaml"))
            copy_blind_evidence(task_root, record_root)
            copy_retained_record(retained[(case_id, agent)], record_root / "retained_record")
            copy_score(SCORE_RUN / "blind_outputs" / task_id, record_root / "score")
            joined_path = SCORE_RUN / "postscore_join/joined_records" / f"{task_id}.json"
            copy_file(joined_path, record_root / "joined_record.json")

            joined = load_json(joined_path)
            native_output_path = retained[(case_id, agent)] / "native_evaluator_output.json"
            native_output = load_json(native_output_path)
            success = native_output.get("tracker", {}).get("success")
            if not isinstance(success, bool):
                raise AuditBuildError(f"non-boolean tracker.success: {task_id}")
            label = "success" if success else "fail"
            released = joined.get("released_evaluator_label", {})
            if released.get("value") != label or released.get("source_sha256") != sha256_file(native_output_path):
                raise AuditBuildError(f"joined released label/source differs: {task_id}")
            score = load_json(SCORE_RUN / "blind_outputs" / task_id / "score.json")
            expected_records.append(
                {
                    "task_id": task_id,
                    "agent_slug": agent,
                    "agent_id": AGENT_NAMES[agent],
                    "released_evaluator_label": label,
                    "native_evidence_verdict_navigation_only": score["native"]["verdict"],
                    "stronger_measurement_verdict_navigation_only": score["stronger"]["verdict"],
                    "label_comparison_navigation_only": joined["comparison"]["status"],
                    "source_vps": released["source_vps"],
                }
            )
        if len(checklist_hashes) != 1:
            raise AuditBuildError(f"agent checklist drift: {case_id}")
        copy_file(PUBLIC_JOB / "tasks" / f"{case_id}__agent_a/checklist.yaml", workspace / "checklist.yaml")

        source_lock = {
            "schema_version": "appworld68_record_level_conflict_source_lock/v1",
            "case_unit_id": case_id,
            "official_appworld": official_lock,
            "our_system": our_lock,
            "official_case_manifest_sha256": sha256_file(source_case / "raw_case_manifest.json"),
            "checklist_sha256": next(iter(checklist_hashes)),
            "public_package_manifest_sha256": sha256_file(PUBLIC_JOB / "package_manifest.json"),
            "blind_validation_lock_sha256": sha256_file(SCORE_RUN / "postscore_join/blind_validation_lock.json"),
        }
        write_json(workspace / "SOURCE_LOCK.json", source_lock)
        review_input = {
            "schema_version": "appworld68_record_level_conflict_review_input/v1",
            "audit_standard": (
                "Only a separate record-level review may confirm benchmark conflict, and only when retained "
                "artifacts plus explicit source pointers show that task, target construction, evaluator, oracle, "
                "or reward wiring/aggregation checked a different outcome than the benchmark appeared to claim."
            ),
            "case_unit_id": case_id,
            "dataset_name": "test_normal",
            "records": expected_records,
            "score_and_label_fields_are_navigation_only_for_conflict": True,
            "original_full_lm_and_logger_logs_intentionally_not_recopied": True,
            "action_environment_api_and_db_evidence_retained": True,
        }
        write_json(workspace / "review_input.json", review_input)
        inventory = file_inventory(workspace)
        write_json(
            workspace / "WORKSPACE_MANIFEST.json",
            {
                "schema_version": "appworld68_record_level_conflict_workspace_manifest/v1",
                "case_unit_id": case_id,
                "files": inventory,
                "files_sha256": canonical_sha(inventory),
            },
        )
        index.append(
            {
                "case_unit_id": case_id,
                "workspace": f"workspaces/{case_id}",
                "output": f"outputs/{case_id}.json",
                "log_prefix": f"logs/{case_id}",
                "expected_records": expected_records,
            }
        )
        print(f"prepared {case_id}", flush=True)

    write_json(output_root / "index.json", index)
    global_inventory = file_inventory(output_root)
    write_json(
        output_root / "AUDIT_PACKAGE_MANIFEST.json",
        {
            "schema_version": "appworld68_record_level_conflict_audit_package/v1",
            "created_at": utc_now(),
            "case_count": len(case_ids),
            "record_count": len(case_ids) * len(AGENTS),
            "index_sha256": sha256_file(output_root / "index.json"),
            "file_count_before_manifest": len(global_inventory),
            "files_sha256_before_manifest": canonical_sha(global_inventory),
            "sensitive_full_lm_logs_included": False,
            "official_commit": OFFICIAL_COMMIT,
            "our_repository_commit": our_lock["repository_commit"],
        },
    )
    print(json.dumps({"output_root": str(output_root), "cases": len(case_ids), "records": 204}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
