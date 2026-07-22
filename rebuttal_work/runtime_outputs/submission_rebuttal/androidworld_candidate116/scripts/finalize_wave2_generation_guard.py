#!/usr/bin/env python3
"""Close the wave_002 generation window and verify every prelocked byte."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).resolve()
WORK_ROOT = SCRIPT.parents[1]
REPO_ROOT = WORK_ROOT.parents[3]
GEN_ROOT = WORK_ROOT / "draft_generation"
PRELOCK = GEN_ROOT / "freeze" / "androidworld_candidate116_codex_cli_draft_prelock_v2.json"
CONFIG = GEN_ROOT / "config" / "androidworld_candidate116_codex_cli_draft_config_v2.json"
WAVE_ROOT = GEN_ROOT / "waves" / "wave_002"
PRE_SNAPSHOT = GEN_ROOT / "validation" / "pre_generation_wave_002_readonly_snapshot.json"
POST_SNAPSHOT = GEN_ROOT / "validation" / "post_generation_wave_002_readonly_snapshot.json"
GUARD_REPORT = GEN_ROOT / "validation" / "wave_002_readonly_pre_post_guard_report.json"


class GuardError(RuntimeError):
    """A fail-closed generation-window validation error."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GuardError(f"cannot load {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def resolve_repo_path(raw: str) -> Path:
    candidate = (REPO_ROOT / raw).resolve()
    try:
        candidate.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise GuardError(f"bound path escapes repository: {raw}") from exc
    return candidate


def verify_binding(binding: dict[str, Any], label: str) -> Path:
    path = resolve_repo_path(str(binding.get("path") or ""))
    if not path.is_file():
        raise GuardError(f"missing {label}: {path}")
    actual = sha256_file(path)
    if actual != binding.get("sha256"):
        raise GuardError(f"{label} hash mismatch: {actual} != {binding.get('sha256')}")
    return path


def require_self_hash(value: dict[str, Any], key: str, label: str) -> None:
    expected = value.get(key)
    core = dict(value)
    core.pop(key, None)
    if expected != canonical_sha256(core):
        raise GuardError(f"{label} self hash mismatch")


def load_builder() -> Any:
    path = SCRIPT.with_name("build_and_validate.py")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate116_builder_wave2_guard", path)
    if spec is None or spec.loader is None:
        raise GuardError(f"cannot import snapshot helper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_snapshot(prelock: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    binding = prelock.get("toolchain_snapshot") or {}
    try:
        manifest_path = verify_binding(binding, "toolchain snapshot manifest")
        manifest = load_json(manifest_path)
        require_self_hash(manifest, "snapshot_sha256", "toolchain snapshot manifest")
        if manifest.get("snapshot_sha256") != binding.get("snapshot_sha256"):
            raise GuardError("prelock snapshot canonical hash mismatch")
        files = list(manifest.get("files") or [])
        if len(files) != manifest.get("file_count") or canonical_sha256(files) != manifest.get("files_sha256"):
            raise GuardError("toolchain snapshot file index mismatch")
        for item in files:
            verify_binding(item, f"snapshot file {item.get('path')}")
        return manifest, issues
    except GuardError as exc:
        issues.append(str(exc))
        return {}, issues


def verify_wave(prelock: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    summary_path = WAVE_ROOT / "_batch_summary.json"
    summary: dict[str, Any] = {}
    try:
        summary = load_json(summary_path)
    except GuardError as exc:
        issues.append(str(exc))
        return summary, issues

    expected = {
        "total_cases": 116,
        "completed_cases": 116,
        "success_cases": 116,
        "failed_cases": 0,
        "warning_count": 0,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            issues.append(f"batch summary {key}={summary.get(key)!r}, expected {value!r}")

    case_ids = list(prelock.get("case_order") or [])
    actual_dirs = sorted(path.name for path in WAVE_ROOT.iterdir() if path.is_dir()) if WAVE_ROOT.is_dir() else []
    if sorted(case_ids) != actual_dirs:
        issues.append("wave case directories are not exactly the 116 prelocked ids")
    required = (
        "checklist.yaml",
        "checklist.json",
        "api_response.json",
        "llm_call.json",
        "reasoning_summary.txt",
        "stdout.log",
        "stderr.log",
    )
    for case_id in case_ids:
        case_dir = WAVE_ROOT / case_id
        missing = [name for name in required if not (case_dir / name).is_file()]
        if missing:
            issues.append(f"{case_id} missing canonical sidecars: {', '.join(missing)}")
    return summary, issues


def main() -> int:
    if POST_SNAPSHOT.exists() or GUARD_REPORT.exists():
        raise GuardError("post snapshot/guard already exists; refusing to rewrite the closed generation window")
    prelock = load_json(PRELOCK)
    require_self_hash(prelock, "prelock_sha256", "wave_002 prelock")
    if prelock.get("schema_version") != "androidworld_candidate116_codex_draft_prelock/v2":
        raise GuardError("unexpected prelock schema")
    if prelock.get("generation_id") != "wave_002":
        raise GuardError("prelock does not identify wave_002")
    if resolve_repo_path(str((prelock.get("canonical_output_gate") or {}).get("raw_wave"))) != WAVE_ROOT.resolve():
        raise GuardError("prelock raw_wave does not resolve to wave_002")

    verify_binding(prelock.get("draft_config") or {}, "draft config")
    config = load_json(CONFIG)
    require_self_hash(config, "config_sha256", "draft config")
    if config.get("runner_command_sha256") != canonical_sha256(config.get("runner_command")):
        raise GuardError("runner command canonical hash mismatch")

    input_issues: list[str] = []
    compact_inputs = list(prelock.get("compact_packet_inputs") or [])
    if len(compact_inputs) != 116 or canonical_sha256(compact_inputs) != prelock.get("compact_packet_inputs_sha256"):
        input_issues.append("compact input index is not the exact prelocked 116-case index")
    for item in compact_inputs:
        try:
            verify_binding(item, f"compact packet {item.get('case_unit_id')}")
        except GuardError as exc:
            input_issues.append(str(exc))

    _, snapshot_issues = verify_snapshot(prelock)
    summary, wave_issues = verify_wave(prelock)

    builder = load_builder()
    pre_snapshot = load_json(PRE_SNAPSHOT)
    post_snapshot = builder.readonly_operation_snapshot(phase="after_candidate116_codex_draft_generation_wave_002")
    write_json(POST_SNAPSHOT, post_snapshot)
    pre_core = builder.readonly_snapshot_core(pre_snapshot)
    post_core = builder.readonly_snapshot_core(post_snapshot)
    readonly_equal = pre_core == post_core
    changed_roots = []
    for name, before in (pre_core.get("roots") or {}).items():
        after = (post_core.get("roots") or {}).get(name)
        if before != after:
            changed_roots.append(name)
    if pre_core.get("official100") != post_core.get("official100"):
        changed_roots.append("official100")

    issues = input_issues + snapshot_issues + wave_issues
    if not readonly_equal:
        issues.append("legacy read-only roots changed during wave_002: " + ", ".join(changed_roots))
    report = {
        "schema_version": "androidworld_candidate116_wave2_generation_guard/v1",
        "status": "pass" if not issues else "fail",
        "generation_id": "wave_002",
        "case_count": 116,
        "batch_summary": summary,
        "prelock": {"path": str(PRELOCK.relative_to(REPO_ROOT)), "sha256": sha256_file(PRELOCK), "prelock_sha256": prelock["prelock_sha256"]},
        "draft_config": {"path": str(CONFIG.relative_to(REPO_ROOT)), "sha256": sha256_file(CONFIG), "config_sha256": config["config_sha256"]},
        "pre_snapshot": {"path": str(PRE_SNAPSHOT.relative_to(REPO_ROOT)), "sha256": sha256_file(PRE_SNAPSHOT)},
        "post_snapshot": {"path": str(POST_SNAPSHOT.relative_to(REPO_ROOT)), "sha256": sha256_file(POST_SNAPSHOT)},
        "readonly_pre_post_equal": readonly_equal,
        "changed_roots": changed_roots,
        "compact_inputs_unchanged": not input_issues,
        "toolchain_snapshot_unchanged": not snapshot_issues,
        "wave_complete_116_of_116": not wave_issues,
        "issues": issues,
    }
    report["guard_sha256"] = canonical_sha256(report)
    write_json(GUARD_REPORT, report)
    print(json.dumps({"status": report["status"], "guard": str(GUARD_REPORT), "issues": issues}, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GuardError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
