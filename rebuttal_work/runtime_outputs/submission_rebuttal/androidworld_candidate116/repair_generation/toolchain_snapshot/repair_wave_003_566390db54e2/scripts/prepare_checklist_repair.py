#!/usr/bin/env python3
"""Prepare content-addressed, prelocked wave_003 checklist repairs.

This command performs no model calls.  It refuses incomplete wave/QC evidence,
snapshots the repair toolchain, materializes immutable repair packets, and
freezes the exact Codex CLI/read-only/xhigh/six-worker execution contract.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from semantic_review_common import SemanticReviewError

from repair_pipeline_common import (
    EXPECTED_CASE_COUNT,
    EXPECTED_PARALLELISM,
    REPAIR_CONFIG_SCHEMA,
    REPAIR_PRELOCK_SCHEMA,
    WORK_ROOT,
    RepairPipelineError,
    add_self_hash,
    file_binding,
    load_audit_selection,
    load_json,
    load_source_prelock,
    object_sha256,
    repo_relative,
    resolve_repo_path,
    safe_id,
    sha256_file,
    source_wave,
    tool_binding,
    utc_now,
    verify_binding_tree,
    verify_case_identity,
    verify_checklist_pair,
    verify_file_binding,
    verify_internal_hash,
    verify_source_wave_complete,
    write_json_atomic,
)


SOURCE_SCRIPTS = Path(__file__).resolve().parent
SOURCE_PROMPT = WORK_ROOT / "prompts" / "androidworld_checklist_repair_v1.supplement.md"
SNAPSHOT_SCRIPT_NAMES = (
    "semantic_review_common.py",
    "repair_pipeline_common.py",
    "build_scope_aware_wave3_guard.py",
    "build_repair_selection.py",
    "prepare_checklist_repair.py",
    "run_checklist_repair_batch.py",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-prelock", type=Path, required=True)
    parser.add_argument("--automatic-qc-root", type=Path, required=True)
    parser.add_argument("--audit-selection", type=Path, required=True)
    parser.add_argument("--original-generation-guard", type=Path, required=True)
    parser.add_argument("--changed-path-incident", type=Path, required=True)
    parser.add_argument("--scope-aware-guard", type=Path, required=True)
    parser.add_argument("--repair-id")
    parser.add_argument("--model", default="gpt-5.6-sol", choices=("gpt-5.6-sol",))
    parser.add_argument("--reasoning-effort", default="xhigh", choices=("xhigh",))
    parser.add_argument("--max-parallel", type=int, default=6)
    parser.add_argument("--codex-timeout-seconds", type=int, default=1800)
    parser.add_argument("--large-codex-timeout-seconds", type=int, default=3600)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def check_codex() -> dict[str, Any]:
    raw = shutil.which("codex")
    if not raw:
        raise RepairPipelineError("codex is not on PATH")
    binary = Path(raw).resolve()
    version = subprocess.run(
        [str(binary), "--version"], capture_output=True, text=True, check=False, timeout=30
    )
    login = subprocess.run(
        [str(binary), "login", "status"], capture_output=True, text=True, check=False, timeout=30
    )
    detail = "\n".join(part.strip() for part in (login.stdout, login.stderr) if part.strip())
    if version.returncode != 0 or login.returncode != 0 or "logged in" not in detail.casefold():
        raise RepairPipelineError(f"Codex CLI/login prelock failed: {detail}")
    return {
        "binary_path": str(binary),
        "binary_sha256": sha256_file(binary),
        "version": (version.stdout or version.stderr).strip(),
        "login_status_at_prelock": detail,
        "auth_mode": "codex_login",
    }


def verify_automatic_qc(root: Path, order: list[str]) -> dict[str, Any]:
    try:
        root.resolve().relative_to(WORK_ROOT.resolve())
    except ValueError as exc:
        raise RepairPipelineError("automatic QC root must be inside candidate116") from exc
    summary_path = root / "summary.json"
    summary = load_json(summary_path, "wave3 automatic QC summary")
    if summary.get("case_count") != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("automatic QC summary is not a 116-case audit")
    reports = []
    for rank, case_id in enumerate(order):
        path = root / case_id / "qc.json"
        report = load_json(path, f"{case_id} automatic QC")
        if (
            report.get("case_unit_id") != case_id
            or report.get("task_id") != case_id
            or report.get("selection_rank") != rank
        ):
            raise RepairPipelineError(f"{case_id} automatic QC identity/rank differs")
        reports.append(file_binding(path))
    if len(reports) != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("automatic QC does not contain exactly 116 case reports")
    return {"summary": file_binding(summary_path), "reports_sha256": object_sha256(reports)}


def verify_drift_evidence(
    original_path: Path,
    incident_path: Path,
    scope_path: Path,
) -> dict[str, Any]:
    original = load_json(original_path, "original generation guard")
    incident = load_json(incident_path, "changed-path incident")
    scope = load_json(scope_path, "scope-aware guard")
    verify_internal_hash(original, ("guard_sha256",), "original generation guard")
    verify_internal_hash(incident, ("incident_sha256",), "changed-path incident")
    verify_internal_hash(scope, ("scope_guard_sha256",), "scope-aware guard")
    if original.get("generation_id") != "wave_003":
        raise RepairPipelineError("original generation guard is not wave_003")
    if incident.get("generation_id") != "wave_003" or scope.get("generation_id") != "wave_003":
        raise RepairPipelineError("drift evidence is not wave_003")
    if scope.get("status") != "pass":
        raise RepairPipelineError("scope-aware guard did not pass")
    if scope.get("packet_inputs_unchanged") is not True:
        raise RepairPipelineError("scope-aware guard did not prove packet inputs unchanged")
    if scope.get("v3_snapshot_files_unchanged") is not True:
        raise RepairPipelineError("scope-aware guard did not prove v3 snapshot bytes unchanged")
    if scope.get("v3_bound_live_origins_unchanged") is not True:
        raise RepairPipelineError("scope-aware guard did not prove v3 live origins unchanged")
    protected = scope.get("protected_root_equality") or {}
    if not protected or not all(value is True for value in protected.values()):
        raise RepairPipelineError("scope-aware guard did not prove protected root equality")
    if scope.get("official100_equal") is not True:
        raise RepairPipelineError("scope-aware guard did not prove official100 unchanged")
    bound_original = scope.get("original_guard") or {}
    if bound_original.get("sha256") != sha256_file(original_path):
        raise RepairPipelineError("scope-aware guard does not bind the original guard file")
    if scope.get("live_drift_incident_sha256") != incident.get("incident_sha256"):
        raise RepairPipelineError("scope-aware guard and changed-path incident disagree")
    bound_incident = scope.get("live_drift_incident")
    if isinstance(bound_incident, Mapping):
        verify_file_binding(bound_incident, "scope guard incident", inside_candidate=True)
    return {
        "original_guard": file_binding(original_path)
        | {"guard_sha256": original["guard_sha256"], "status": original.get("status")},
        "changed_path_incident": file_binding(incident_path)
        | {"incident_sha256": incident["incident_sha256"]},
        "scope_aware_guard": file_binding(scope_path)
        | {"scope_guard_sha256": scope["scope_guard_sha256"]},
        "policy": "original guard is preserved even when failed; scope-aware pass is additive",
    }


def packet_text(
    *,
    case_id: str,
    rank: int,
    original_yaml: str,
    issues: list[dict[str, Any]],
    full_packet: str,
) -> str:
    issue_json = json.dumps(issues, ensure_ascii=False, sort_keys=True, indent=2)
    return (
        "# AndroidWorld Checklist Repair Packet\n\n"
        "## Case Metadata\n\n"
        "- domain: `androidworld`\n"
        f"- case_unit_id: `{case_id}`\n"
        f"- task_id: `{case_id}`\n"
        f"- selection_rank: `{rank}`\n\n"
        "## Repair Control (untrusted leads; never semantic evidence)\n\n"
        "The old checklist and issue statements below identify what must be checked. "
        "They are not source facts, runtime evidence, or valid support targets. The "
        "verbatim full packet later in this file is the sole semantic authority.\n\n"
        "### Bound issues\n\n```json\n"
        f"{issue_json}\n```\n\n"
        "### Original checklist to repair\n\n```yaml\n"
        f"{original_yaml.rstrip()}\n```\n\n"
        "## Authoritative Full Case Packet (verbatim; sole semantic authority)\n\n"
        f"{full_packet.rstrip()}\n"
    )


def materialize_packets(
    *,
    repair_id: str,
    prelock: Mapping[str, Any],
    audit_rows: list[dict[str, Any]],
    wave: Path,
) -> tuple[Path, list[dict[str, Any]]]:
    packet_set_root = WORK_ROOT / "repair_generation" / "packet_sets" / repair_id
    if packet_set_root.exists():
        raise RepairPipelineError(f"repair packet set already exists: {packet_set_root}")
    content_root = WORK_ROOT / "repair_generation" / "content_addressed_packets"
    row_by_case = {row["case_unit_id"]: row for row in audit_rows}
    packet_by_case = {row["case_unit_id"]: row for row in prelock.get("packet_inputs") or []}
    repair_inputs: list[dict[str, Any]] = []
    created_content: list[Path] = []
    try:
        for rank, case_id in enumerate(prelock["case_order"]):
            audit = row_by_case[case_id]
            if audit["disposition"] != "repair":
                continue
            packet_record = packet_by_case[case_id]
            full_path = verify_file_binding(packet_record, f"{case_id} full packet", inside_candidate=True)
            original_dir = wave / case_id
            original = verify_checklist_pair(original_dir, case_id)
            original_yaml_path = original_dir / "checklist.yaml"
            original_json_path = original_dir / "checklist.json"
            text = packet_text(
                case_id=case_id,
                rank=rank,
                original_yaml=original_yaml_path.read_text(encoding="utf-8"),
                issues=audit["issues"],
                full_packet=full_path.read_text(encoding="utf-8"),
            )
            payload = text.encode("utf-8")
            packet_sha = __import__("hashlib").sha256(payload).hexdigest()
            addressed = content_root / packet_sha / "case_packet.md"
            if addressed.exists():
                if addressed.read_bytes() != payload:
                    raise RepairPipelineError(f"content-address collision for {case_id}")
            else:
                addressed.parent.mkdir(parents=True, exist_ok=False)
                addressed.write_bytes(payload)
                created_content.append(addressed.parent)
            case_dir = packet_set_root / case_id
            case_dir.mkdir(parents=True)
            packet_path = case_dir / "case_packet.md"
            packet_path.write_bytes(payload)
            bindings = {
                "authoritative_full_packet": file_binding(full_path),
                "original_checklist_yaml": file_binding(original_yaml_path),
                "original_checklist_json": file_binding(original_json_path),
                "automatic_qc": audit["automatic_qc"],
                "audit_sources": audit["audit_sources"],
                "content_addressed_packet": file_binding(addressed),
                "batch_packet": file_binding(packet_path),
            }
            descriptor = {
                "schema_version": "androidworld_checklist_repair_packet/v1",
                "repair_id": repair_id,
                "case_unit_id": case_id,
                "task_id": case_id,
                "selection_rank": rank,
                "audit_case_sha256": audit["audit_case_sha256"],
                "issues": audit["issues"],
                "packet_sha256": packet_sha,
                "semantic_authority": "authoritative_full_packet_only",
                "bindings": bindings,
            }
            descriptor = add_self_hash(descriptor, "descriptor_sha256")
            descriptor_path = case_dir / "repair_packet_descriptor.json"
            write_json_atomic(descriptor_path, descriptor)
            repair_inputs.append(
                {
                    "selection_rank": rank,
                    "case_unit_id": case_id,
                    "task_id": case_id,
                    "audit_case_sha256": audit["audit_case_sha256"],
                    "issues_sha256": object_sha256(audit["issues"]),
                    "repair_packet_sha256": packet_sha,
                    "descriptor": file_binding(descriptor_path)
                    | {"descriptor_sha256": descriptor["descriptor_sha256"]},
                    "bindings": bindings,
                }
            )
    except BaseException:
        shutil.rmtree(packet_set_root, ignore_errors=True)
        for directory in reversed(created_content):
            shutil.rmtree(directory, ignore_errors=True)
        raise
    return packet_set_root, repair_inputs


def copy_toolchain(repair_id: str) -> tuple[Path, dict[str, Any]]:
    root = WORK_ROOT / "repair_generation" / "toolchain_snapshot" / repair_id
    if root.exists():
        raise RepairPipelineError(f"repair snapshot already exists: {root}")
    scripts = root / "scripts"
    prompts = root / "prompts"
    scripts.mkdir(parents=True)
    prompts.mkdir(parents=True)
    for name in SNAPSHOT_SCRIPT_NAMES:
        source = SOURCE_SCRIPTS / name
        if not source.is_file():
            raise RepairPipelineError(f"repair tool source is missing: {source}")
        shutil.copy2(source, scripts / name)
    shutil.copy2(SOURCE_PROMPT, prompts / SOURCE_PROMPT.name)
    roles = {
        "semantic_review_primitives": scripts / "semantic_review_common.py",
        "common": scripts / "repair_pipeline_common.py",
        "selection_builder": scripts / "build_repair_selection.py",
        "prelock_builder": scripts / "prepare_checklist_repair.py",
        "repair_runner": scripts / "run_checklist_repair_batch.py",
        "scope_aware_guard_builder": scripts / "build_scope_aware_wave3_guard.py",
        "repair_prompt": prompts / SOURCE_PROMPT.name,
    }
    files = [
        file_binding(path)
        for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file())
    ]
    manifest = {
        "schema_version": "androidworld_checklist_repair_toolchain_snapshot/v1",
        "repair_id": repair_id,
        "created_at": utc_now(),
        "roles": {name: file_binding(path) for name, path in sorted(roles.items())},
        "files": files,
        "file_count": len(files),
        "files_sha256": object_sha256(files),
    }
    manifest = add_self_hash(manifest, "snapshot_sha256")
    path = root / "snapshot_manifest.json"
    write_json_atomic(path, manifest)
    for file in root.rglob("*"):
        if file.is_file():
            file.chmod(0o444)
    for directory in sorted((path for path in root.rglob("*") if path.is_dir()), reverse=True):
        directory.chmod(0o555)
    root.chmod(0o555)
    return path, manifest


def main() -> int:
    args = parse_args()
    if args.max_parallel != EXPECTED_PARALLELISM:
        raise RepairPipelineError("repair protocol requires exactly 6 concurrent workers")
    if args.codex_timeout_seconds <= 0 or args.large_codex_timeout_seconds <= 0:
        raise RepairPipelineError("Codex timeouts must be positive")
    source_prelock_path = args.source_prelock.resolve()
    source_prelock = load_source_prelock(source_prelock_path)
    wave, _ = verify_source_wave_complete(source_prelock)
    order = list(source_prelock["case_order"])
    automatic_qc_root = args.automatic_qc_root.resolve()
    automatic_qc = verify_automatic_qc(automatic_qc_root, order)
    selection_path = args.audit_selection.resolve()
    selection, audit_rows = load_audit_selection(
        selection_path,
        case_order=order,
        automatic_qc_root=automatic_qc_root,
    )
    repair_rows = [row for row in audit_rows if row["disposition"] == "repair"]
    if not repair_rows:
        raise RepairPipelineError("selection has zero repairs; no repair wave is necessary")
    drift = verify_drift_evidence(
        args.original_generation_guard.resolve(),
        args.changed_path_incident.resolve(),
        args.scope_aware_guard.resolve(),
    )
    codex = check_codex()
    selection_sha = selection["selection_sha256"]
    repair_id = args.repair_id or f"repair_wave_003_{selection_sha[:12]}"
    if not safe_id(repair_id):
        raise RepairPipelineError("repair id contains unsupported characters")

    output_root = WORK_ROOT / "repair_generation" / "waves" / repair_id
    effective_root = WORK_ROOT / "repair_generation" / "effective_waves" / f"effective_{repair_id}"
    config_path = WORK_ROOT / "repair_generation" / "config" / f"{repair_id}.config.json"
    prelock_path = WORK_ROOT / "repair_generation" / "freeze" / f"{repair_id}.prelock.json"
    packet_set_root = WORK_ROOT / "repair_generation" / "packet_sets" / repair_id
    snapshot_root = WORK_ROOT / "repair_generation" / "toolchain_snapshot" / repair_id
    for target in (output_root, effective_root, config_path, prelock_path, packet_set_root, snapshot_root):
        if target.exists():
            raise RepairPipelineError(f"refusing to overwrite repair artifact: {target}")

    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry_run_pass",
                    "repair_id": repair_id,
                    "case_count": EXPECTED_CASE_COUNT,
                    "repair_count": len(repair_rows),
                    "retain_count": EXPECTED_CASE_COUNT - len(repair_rows),
                    "issue_severities": dict(
                        Counter(issue["severity"] for row in repair_rows for issue in row["issues"])
                    ),
                    "source_wave": repo_relative(wave),
                    "scope_aware_guard": drift["scope_aware_guard"],
                    "codex": codex,
                },
                indent=2,
            )
        )
        return 0

    packet_set_root, repair_inputs = materialize_packets(
        repair_id=repair_id,
        prelock=source_prelock,
        audit_rows=audit_rows,
        wave=wave,
    )
    try:
        snapshot_path, snapshot = copy_toolchain(repair_id)
        roles = snapshot["roles"]
        _, original_batch_runner, _ = tool_binding(source_prelock, "batch_runner")
        original_tools = {
            name: dict(binding)
            for name, binding in (source_prelock.get("tool_bindings") or {}).items()
        }
        for name, binding in original_tools.items():
            verify_file_binding(binding, f"original frozen tool {name}", inside_candidate=True)
        config = {
            "schema_version": REPAIR_CONFIG_SCHEMA,
            "status": "prelocked",
            "repair_id": repair_id,
            "source_generation_id": "wave_003",
            "provider": "codex_cli",
            "auth_mode": "codex_login",
            "model": args.model,
            "reasoning_effort": args.reasoning_effort,
            "sandbox": "read-only",
            "ephemeral": True,
            "ignore_user_config": True,
            "max_parallel": EXPECTED_PARALLELISM,
            "large_max_parallel": EXPECTED_PARALLELISM,
            "codex_timeout_seconds": args.codex_timeout_seconds,
            "large_codex_timeout_seconds": args.large_codex_timeout_seconds,
            "token_budgets": [12000, 16000, 20000],
            "quality_check": "none",
            "case_count": EXPECTED_CASE_COUNT,
            "repair_count": len(repair_inputs),
            "packet_set_root": repo_relative(packet_set_root),
            "output_root": repo_relative(output_root),
            "effective_root": repo_relative(effective_root),
            "repair_runner": roles["repair_runner"],
            "frozen_batch_runner": original_batch_runner,
            "repair_prompt": roles["repair_prompt"],
            "codex_cli": codex,
            "created_at": utc_now(),
        }
        config = add_self_hash(config, "config_sha256")
        write_json_atomic(config_path, config)
        source_binding = file_binding(source_prelock_path) | {
            "prelock_sha256": source_prelock["prelock_sha256"]
        }
        retain_rows = [
            {
                "selection_rank": row["selection_rank"],
                "case_unit_id": row["case_unit_id"],
                "task_id": row["task_id"],
                "audit_case_sha256": row["audit_case_sha256"],
                "automatic_qc": row["automatic_qc"],
                "audit_sources": row["audit_sources"],
            }
            for row in audit_rows
            if row["disposition"] == "retain"
        ]
        prelock = {
            "schema_version": REPAIR_PRELOCK_SCHEMA,
            "status": "frozen_before_first_repair_model_call",
            "repair_id": repair_id,
            "source_generation_id": "wave_003",
            "created_at": utc_now(),
            "case_count": EXPECTED_CASE_COUNT,
            "case_order": order,
            "case_order_sha256": object_sha256(order),
            "repair_count": len(repair_inputs),
            "retain_count": len(retain_rows),
            "repair_inputs": repair_inputs,
            "repair_inputs_sha256": object_sha256(repair_inputs),
            "retain_inputs": retain_rows,
            "retain_inputs_sha256": object_sha256(retain_rows),
            "audit_selection": file_binding(selection_path)
            | {"selection_sha256": selection["selection_sha256"]},
            "audit_rows_sha256": object_sha256(audit_rows),
            "automatic_qc": automatic_qc,
            "source_draft": {
                "prelock": source_binding,
                "raw_wave": repo_relative(wave),
                "batch_summary": file_binding(wave / "_batch_summary.json"),
                "batch_results": file_binding(wave / "_batch_results.jsonl"),
            },
            "drift_evidence": drift,
            "repair_config": file_binding(config_path) | {"config_sha256": config["config_sha256"]},
            "repair_toolchain_snapshot": file_binding(snapshot_path)
            | {"snapshot_sha256": snapshot["snapshot_sha256"]},
            "repair_tool_bindings": roles,
            "original_v3_tool_bindings": original_tools,
            "codex_cli": codex,
            "canonical_output_gate": {
                "repair_wave": repo_relative(output_root),
                "effective_wave": repo_relative(effective_root),
                "effective_qc_required": True,
                "new_independent_human_reviews_required": True,
                "legacy_direct_promotion_forbidden": True,
                "separate_content_addressed_downstream_prelock_required": True,
                "downstream_tools_not_part_of_repair_generation_snapshot": True,
            },
        }
        prelock = add_self_hash(prelock, "prelock_sha256")
        write_json_atomic(prelock_path, prelock)
    except BaseException:
        shutil.rmtree(packet_set_root, ignore_errors=True)
        if snapshot_root.exists():
            for path in snapshot_root.rglob("*"):
                try:
                    path.chmod(0o755 if path.is_dir() else 0o644)
                except OSError:
                    pass
            try:
                snapshot_root.chmod(0o755)
            except OSError:
                pass
            shutil.rmtree(snapshot_root, ignore_errors=True)
        config_path.unlink(missing_ok=True)
        prelock_path.unlink(missing_ok=True)
        raise
    print(
        json.dumps(
            {
                "status": "prelocked",
                "repair_id": repair_id,
                "case_count": EXPECTED_CASE_COUNT,
                "repair_count": len(repair_inputs),
                "retain_count": len(retain_rows),
                "prelock": file_binding(prelock_path) | {"prelock_sha256": prelock["prelock_sha256"]},
                "run_command": [
                    sys.executable,
                    str(resolve_repo_path(roles["repair_runner"]["path"], inside_candidate=True)),
                    "--prelock",
                    str(prelock_path),
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SemanticReviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
