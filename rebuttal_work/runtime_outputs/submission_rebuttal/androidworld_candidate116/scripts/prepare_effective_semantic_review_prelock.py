#!/usr/bin/env python3
"""Build a content-bound semantic-review prelock for the effective 116-case wave.

The produced prelock is intentionally compatible with the existing snapshotted
six-worker ``run_semantic_review_batch.py``.  It binds the repair-aware effective
manifest, strict effective QC, every original full packet, every effective
checklist/origin record, optional repair provenance, the frozen checklist
schema, the review prompt/schema/toolchain, and the exact Codex-login settings.
It does not call a model and does not authorize promotion.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from repair_pipeline_common import (
    REPO_ROOT,
    EFFECTIVE_MANIFEST_SCHEMA,
    EXPECTED_CASE_COUNT,
    EXPECTED_PARALLELISM,
    WORK_ROOT,
    RepairPipelineError,
    add_self_hash,
    canonical_runtime_tree,
    file_binding,
    load_audit_selection,
    load_json,
    load_yaml_mapping,
    object_sha256,
    python_runtime_binding,
    repo_relative,
    resolve_repo_path,
    sha256_file,
    utc_now,
    verify_file_binding,
    verify_internal_hash,
    verify_repair_concurrency_evidence,
)
from semantic_review_common import (
    CONFIG_SCHEMA_VERSION,
    EXACT_CODEX_LOGIN_STATUS,
    EXPECTED_MODEL,
    EXPECTED_REASONING_EFFORT,
    ISSUE_HISTORY_SCHEMA_VERSION,
    PRELOCK_SCHEMA_VERSION,
    SemanticReviewError,
    model_body_schema,
    parse_case_packet,
    schema_errors,
    sha256_bytes,
    verify_issue_history,
    verify_self_hash,
    write_json_atomic,
)


SCRIPT = Path(__file__).resolve()
SOURCE_PROMPT = (
    WORK_ROOT / "prompts" / "androidworld_effective_checklist_semantic_review_v2.prompt.md"
)
SOURCE_PROPOSAL_SCHEMA = (
    WORK_ROOT / "schemas" / "androidworld_checklist_semantic_review_proposal.schema.json"
)
SOURCE_DRAFT_PRELOCK = (
    WORK_ROOT
    / "draft_generation"
    / "freeze"
    / "androidworld_candidate116_codex_cli_draft_prelock_v3.json"
)
REVIEW_TOOLS = {
    "bootstrap": WORK_ROOT / "scripts" / "semantic_review_bootstrap.py",
    "common": WORK_ROOT / "scripts" / "semantic_review_common.py",
    "prelock_dependency_repair_common": WORK_ROOT / "scripts" / "repair_pipeline_common.py",
    "prelock_builder": SCRIPT,
    "batch_runner": WORK_ROOT / "scripts" / "run_semantic_review_batch.py",
    "independent_validator": WORK_ROOT / "scripts" / "validate_semantic_review_batch.py",
}
BOOTSTRAP_LAUNCHER = (
    "import hashlib,sys;"
    "p=sys.argv[1];h=sys.argv[2];d=open(p,'rb').read();"
    "(_ for _ in ()).throw(SystemExit('SEMANTIC_REVIEW_BOOTSTRAP_HASH_MISMATCH'))"
    " if hashlib.sha256(d).hexdigest()!=h else None;"
    "sys.argv=[p]+sys.argv[3:];g={'__name__':'__main__','__file__':p};"
    "exec(compile(d,p,'exec'),g,g)"
)
REQUIRED_PROMPT_POLICIES = (
    "exception/NaN/no numeric raw -> undecided",
    "metadata/code difference",
    "parameter-schema/generator difference",
    "strictly `> 0.5`",
    "issue_history.json.issues",
    "never a human review",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--effective-manifest", type=Path)
    parser.add_argument("--effective-qc-root", type=Path)
    parser.add_argument("--source-draft-prelock", type=Path, default=SOURCE_DRAFT_PRELOCK)
    parser.add_argument("--review-id")
    parser.add_argument("--model", default=EXPECTED_MODEL)
    parser.add_argument(
        "--reasoning-effort",
        default=EXPECTED_REASONING_EFFORT,
        choices=("minimal", "low", "medium", "high", "xhigh"),
    )
    parser.add_argument("--codex-timeout-seconds", type=int, default=1800)
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument("--max-parallel", type=int, default=EXPECTED_PARALLELISM)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument(
        "--bootstrap-self-test",
        action="store_true",
        help="Run a no-model isolated-runtime positive/tamper test in a temporary candidate tree.",
    )
    return parser.parse_args()


def safe_id(value: str) -> bool:
    return bool(value) and all(character.isalnum() or character in "_.-" for character in value)


def assert_prompt_policy(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [policy for policy in REQUIRED_PROMPT_POLICIES if policy not in text]
    if missing:
        raise RepairPipelineError(f"effective semantic-review prompt lacks hard policies: {missing}")


def codex_binding() -> dict[str, Any]:
    binary_raw = shutil.which("codex")
    if not binary_raw:
        raise RepairPipelineError("codex is not on PATH")
    invocation = Path(os.path.abspath(binary_raw))
    binary = invocation.resolve(strict=True)
    version = subprocess.run(
        [str(binary), "--version"], capture_output=True, text=True, timeout=30, check=False
    )
    login = subprocess.run(
        [str(binary), "login", "status"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    detail = "\n".join(part.strip() for part in (login.stdout, login.stderr) if part.strip())
    if version.returncode != 0:
        raise RepairPipelineError("cannot obtain Codex CLI version")
    if login.returncode != 0 or detail != EXACT_CODEX_LOGIN_STATUS:
        raise RepairPipelineError(f"Codex CLI login is not active: {detail}")
    return {
        "invocation_path": str(invocation),
        "binary_path": str(binary),
        "binary_sha256": sha256_file(binary),
        "version": (version.stdout or version.stderr).strip(),
        "login_status_at_prelock": detail,
        "login_success_format": EXACT_CODEX_LOGIN_STATUS,
        "auth_mode": "codex_login",
    }


def source_context(path: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]], Path]:
    prelock = load_json(path.resolve(), "source draft prelock")
    verify_self_hash(prelock, "prelock_sha256", "source draft prelock")
    if prelock.get("case_count") != EXPECTED_CASE_COUNT:
        raise RepairPipelineError("source draft prelock is not exactly 116 cases")
    order = list(prelock.get("case_order") or [])
    rows = list(prelock.get("packet_inputs") or [])
    if (
        len(order) != EXPECTED_CASE_COUNT
        or len(set(order)) != EXPECTED_CASE_COUNT
        or prelock.get("case_order_sha256") != object_sha256(order)
        or len(rows) != EXPECTED_CASE_COUNT
        or prelock.get("packet_inputs_sha256") != object_sha256(rows)
    ):
        raise RepairPipelineError("source draft prelock case/packet index is invalid")
    by_case: dict[str, dict[str, Any]] = {}
    for rank, row in enumerate(rows):
        case_id = str(row.get("case_unit_id") or "")
        if (
            case_id != order[rank]
            or row.get("selection_rank") != rank
            or row.get("task_id") != case_id
            or row.get("input_kind") != "full_case_packet"
        ):
            raise RepairPipelineError(f"source full-packet identity/order fails at rank {rank}")
        packet_path = resolve_repo_path(row.get("path"), inside_candidate=True)
        binding = file_binding(packet_path)
        if packet_path.name != "case_packet.md" or any(
            binding[key] != row.get(key) for key in ("sha256", "size_bytes")
        ):
            raise RepairPipelineError(f"{case_id} original full-packet binding differs")
        parsed = parse_case_packet(packet_path.read_text(encoding="utf-8"))
        if parsed["kind"] != "full" or parsed["identity"].get("case_unit_id") != case_id:
            raise RepairPipelineError(f"{case_id} is not a valid original full packet")
        by_case[case_id] = dict(row)
    tools = prelock.get("tool_bindings") or {}
    schema_path = verify_file_binding(
        tools.get("checklist_schema"), "frozen checklist schema", inside_candidate=True
    )
    return prelock, by_case, schema_path


def effective_context(
    manifest_path: Path,
    qc_root: Path,
    source: Mapping[str, Any],
    packet_by_case: Mapping[str, Mapping[str, Any]],
    checklist_schema_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    manifest = load_json(manifest_path, "effective manifest")
    if manifest.get("schema_version") != EFFECTIVE_MANIFEST_SCHEMA:
        raise RepairPipelineError("effective manifest schema is invalid")
    if manifest.get("status") != "composed_not_qc_or_independent_codex_root_agent_accepted":
        raise RepairPipelineError("effective manifest status is not the pre-QC/pre-review state")
    verify_internal_hash(manifest, ("effective_manifest_sha256",), "effective manifest")
    order = list(manifest.get("case_order") or [])
    cases = list(manifest.get("cases") or [])
    if (
        manifest.get("case_count") != EXPECTED_CASE_COUNT
        or order != list(source.get("case_order") or [])
        or manifest.get("case_order_sha256") != object_sha256(order)
        or len(cases) != EXPECTED_CASE_COUNT
        or manifest.get("cases_sha256") != object_sha256(cases)
    ):
        raise RepairPipelineError("effective manifest does not bind the original candidate116 order")

    repair_prelock_path = verify_file_binding(
        manifest.get("repair_prelock"), "repair prelock", inside_candidate=True
    )
    repair_prelock = load_json(repair_prelock_path, "repair prelock")
    verify_internal_hash(repair_prelock, ("prelock_sha256",), "repair prelock")
    selection_path = verify_file_binding(
        repair_prelock.get("audit_selection"), "repair audit selection", inside_candidate=True
    )
    automatic_qc_summary_path = verify_file_binding(
        (repair_prelock.get("automatic_qc") or {}).get("summary"),
        "repair source automatic-QC summary",
        inside_candidate=True,
    )
    selection, audit_rows = load_audit_selection(
        selection_path,
        case_order=order,
        automatic_qc_root=automatic_qc_summary_path.parent,
    )
    if (
        (repair_prelock.get("audit_selection") or {}).get("selection_sha256")
        != selection.get("selection_sha256")
        or repair_prelock.get("audit_rows_sha256") != object_sha256(audit_rows)
    ):
        raise RepairPipelineError("repair prelock does not bind the reconstructed issue history")
    audit_by_case = {str(row["case_unit_id"]): row for row in audit_rows}
    if set(audit_by_case) != set(order):
        raise RepairPipelineError("reconstructed issue history is not exact candidate116")
    repair_receipt_path = verify_file_binding(
        manifest.get("repair_batch_receipt"), "repair batch receipt", inside_candidate=True
    )
    repair_receipt = load_json(repair_receipt_path, "repair batch receipt")
    verify_internal_hash(repair_receipt, ("receipt_sha256",), "repair batch receipt")
    concurrency_evidence = verify_repair_concurrency_evidence(
        repair_prelock,
        repair_receipt,
        repair_root=repair_receipt_path.parent,
    )
    if (
        manifest.get("repair_concurrency_evidence") != concurrency_evidence
        or manifest.get("repair_concurrency_audit")
        != concurrency_evidence.get("summary")
        or manifest.get("repair_concurrency_samples")
        != concurrency_evidence.get("samples")
    ):
        raise RepairPipelineError(
            "effective manifest repair concurrency evidence/audit/samples differ from raw revalidation"
        )

    qc_summary_path = qc_root / "summary.json"
    qc_summary = load_json(qc_summary_path, "effective QC summary")
    verify_internal_hash(qc_summary, ("summary_sha256",), "effective QC summary")
    if (
        qc_summary.get("schema_version")
        != "androidworld_effective_checklist_automatic_qc_summary/v1"
        or qc_summary.get("status") != "pass"
        or qc_summary.get("case_count") != EXPECTED_CASE_COUNT
        or qc_summary.get("passed_count") != EXPECTED_CASE_COUNT
        or qc_summary.get("failed_count") != 0
        or qc_summary.get("failed_cases") not in (None, [])
        or (qc_summary.get("effective_manifest") or {}).get("effective_manifest_sha256")
        != manifest.get("effective_manifest_sha256")
        or qc_summary.get("repair_concurrency_evidence") != concurrency_evidence
        or qc_summary.get("repair_concurrency_audit")
        != concurrency_evidence.get("summary")
        or qc_summary.get("repair_concurrency_samples")
        != concurrency_evidence.get("samples")
    ):
        raise RepairPipelineError("effective automatic QC is not a bound 116/116 pass")
    report_index = {
        str(row.get("case_unit_id")): row
        for row in qc_summary.get("case_report_index") or []
        if isinstance(row, Mapping)
    }
    if set(report_index) != set(order):
        raise RepairPipelineError("effective QC report index is not exact candidate116")

    checklist_schema = load_json(checklist_schema_path, "frozen checklist schema")
    validator = Draft202012Validator(checklist_schema)
    case_inputs: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for rank, (case_id, row) in enumerate(zip(order, cases, strict=True)):
        if (
            not isinstance(row, Mapping)
            or row.get("selection_rank") != rank
            or row.get("case_unit_id") != case_id
            or row.get("task_id") != case_id
        ):
            raise RepairPipelineError(f"effective case order/identity differs at {case_id}")
        origin = str(row.get("origin") or "")
        if origin not in {"wave_003", "repair"}:
            raise RepairPipelineError(f"{case_id} has invalid effective origin {origin!r}")
        counts[origin] += 1
        audit = audit_by_case[case_id]
        expected_disposition = "repair" if origin == "repair" else "retain"
        if (
            audit.get("selection_rank") != rank
            or audit.get("task_id") != case_id
            or audit.get("disposition") != expected_disposition
            or audit.get("audit_case_sha256") != row.get("audit_case_sha256")
        ):
            raise RepairPipelineError(f"{case_id} effective origin differs from issue history")

        packet_record = packet_by_case[case_id]
        packet_path = resolve_repo_path(packet_record["path"], inside_candidate=True)
        checklist_path = verify_file_binding(
            row.get("effective_checklist"), f"{case_id} effective checklist", inside_candidate=True
        )
        checklist_json_path = checklist_path.with_suffix(".json")
        checklist = load_yaml_mapping(checklist_path, f"{case_id} effective checklist YAML")
        checklist_json = load_json(checklist_json_path, f"{case_id} effective checklist JSON")
        if checklist != checklist_json:
            raise RepairPipelineError(f"{case_id} effective checklist YAML/JSON differ")
        errors = sorted(validator.iter_errors(checklist), key=lambda item: list(item.absolute_path))
        if errors:
            raise RepairPipelineError(f"{case_id} effective checklist schema fails: {errors[0].message}")
        if (
            checklist.get("case_unit_id") != case_id
            or checklist.get("task_id") != case_id
            or checklist.get("domain") != "androidworld"
        ):
            raise RepairPipelineError(f"{case_id} effective checklist identity differs")

        origin_path = verify_file_binding(
            row.get("effective_origin"), f"{case_id} effective origin", inside_candidate=True
        )
        origin_value = load_json(origin_path, f"{case_id} effective origin")
        verify_internal_hash(origin_value, ("origin_sha256",), f"{case_id} effective origin")
        if (
            origin_value.get("case_unit_id") != case_id
            or origin_value.get("origin") != origin
            or origin_value.get("origin_sha256")
            != (row.get("effective_origin") or {}).get("origin_sha256")
        ):
            raise RepairPipelineError(f"{case_id} effective-origin provenance differs")

        qc_path = qc_root / case_id / "qc.json"
        qc = load_json(qc_path, f"{case_id} effective QC")
        indexed_path = verify_file_binding(
            (report_index[case_id] or {}).get("report"),
            f"{case_id} indexed effective QC",
            inside_candidate=True,
        )
        if indexed_path != qc_path.resolve():
            raise RepairPipelineError(f"{case_id} effective QC index points elsewhere")
        if (
            qc.get("case_unit_id") != case_id
            or qc.get("task_id") != case_id
            or qc.get("status") != "passed"
            or qc.get("issues") != []
            or qc.get("effective_manifest_sha256") != manifest["effective_manifest_sha256"]
            or qc.get("effective_origin") != origin
            or resolve_repo_path(qc.get("checklist_path"), inside_candidate=True)
            != checklist_path
            or qc.get("checklist_sha256") != sha256_file(checklist_path)
            or not isinstance(qc.get("checks"), Mapping)
            or not all(value is True for value in qc["checks"].values())
        ):
            raise RepairPipelineError(f"{case_id} effective QC identity/provenance is invalid")

        bindings: dict[str, Any] = {
            "packet": file_binding(packet_path),
            "raw_checklist_yaml": file_binding(checklist_path),
            "raw_checklist_json": file_binding(checklist_json_path),
            "automatic_qc": file_binding(qc_path),
            "effective_origin": file_binding(origin_path),
            "effective_manifest": file_binding(manifest_path),
        }
        issue_source_bindings: dict[str, Any] = {
            "repair_selection": file_binding(selection_path),
            "repair_prelock": file_binding(repair_prelock_path),
            "automatic_qc": copy.deepcopy(audit["automatic_qc"]),
        }
        for source_index, source_binding in enumerate(audit.get("audit_sources") or []):
            verify_file_binding(
                source_binding,
                f"{case_id} issue-history manual source {source_index}",
                inside_candidate=True,
            )
            issue_source_bindings[f"manual_audit_{source_index:02d}"] = copy.deepcopy(
                source_binding
            )
        repair_provenance = row.get("repair_provenance")
        if origin == "repair":
            provenance_path = verify_file_binding(
                repair_provenance, f"{case_id} repair provenance", inside_candidate=True
            )
            provenance = load_json(provenance_path, f"{case_id} repair provenance")
            verify_internal_hash(provenance, ("provenance_sha256",), f"{case_id} repair provenance")
            if provenance.get("provenance_sha256") != repair_provenance.get("provenance_sha256"):
                raise RepairPipelineError(f"{case_id} repair provenance internal hash differs")
            bindings["repair_provenance"] = file_binding(provenance_path)
            issue_source_bindings["repair_provenance"] = file_binding(provenance_path)
        elif repair_provenance is not None:
            raise RepairPipelineError(f"{case_id} retained origin unexpectedly has repair provenance")

        issue_history = {
            "schema_version": ISSUE_HISTORY_SCHEMA_VERSION,
            "case_unit_id": case_id,
            "task_id": case_id,
            "selection_rank": rank,
            "disposition": expected_disposition,
            "audit_case_sha256": audit["audit_case_sha256"],
            "issue_count": len(audit["issues"]),
            "issues": copy.deepcopy(audit["issues"]),
            "issues_sha256": object_sha256(audit["issues"]),
            "source_bindings": issue_source_bindings,
        }
        issue_history = add_self_hash(issue_history, "issue_history_sha256")
        verify_issue_history(issue_history, case_id=case_id, rank=rank)
        case_input = {
            "case_unit_id": case_id,
            "task_id": case_id,
            "selection_rank": rank,
            "packet_kind": "full",
            "effective_origin_kind": origin,
            "effective_origin_sha256": origin_value["origin_sha256"],
            "audit_case_sha256": audit["audit_case_sha256"],
            "input_bindings": bindings,
            "_issue_history_payload": issue_history,
        }
        case_inputs.append(case_input)
    if dict(counts) != manifest.get("origin_counts"):
        raise RepairPipelineError("effective origin counts differ from the manifest")
    return manifest, qc_summary, case_inputs


def semantic_python_runtime(snapshot_script_directory: Path, codex: Mapping[str, Any]) -> dict[str, Any]:
    """Freeze Python while excluding the mutable live repository ``src`` path."""
    runtime = python_runtime_binding(
        expected_runner_script_directory=snapshot_script_directory,
        codex_invocation_path=Path(str(codex["invocation_path"])),
        execution_requires_isolated_bootstrap=True,
    )
    live_source = str((REPO_ROOT / "src").resolve())
    original_expected = list(runtime["expected_runner_sys_path"])
    filtered_expected = [
        path
        for index, path in enumerate(original_expected)
        if index == 0 or os.path.abspath(str(path)) != live_source
    ]
    if live_source not in [os.path.abspath(str(path)) for path in original_expected]:
        raise RepairPipelineError("capture sys.path does not contain the expected live repository src")
    old_extra_by_path = {
        os.path.abspath(str(row["path"])): dict(row)
        for row in runtime["extra_sys_path_entries"]
    }
    extras: list[dict[str, Any]] = []
    for index, path in enumerate(filtered_expected[1:], 1):
        row = old_extra_by_path.get(os.path.abspath(str(path)))
        if row is None:
            raise RepairPipelineError(f"cannot remap frozen sys.path entry: {path}")
        row["index"] = index
        extras.append(row)
    runtime["expected_runner_sys_path"] = filtered_expected
    runtime["expected_runner_script_directory"] = filtered_expected[0]
    runtime["sys_path_tail_sha256"] = object_sha256(filtered_expected[1:])
    runtime["extra_sys_path_entries"] = extras
    runtime["extra_sys_path_entries_sha256"] = object_sha256(extras)
    runtime["live_repository_source_path"] = live_source
    runtime["live_repository_source_excluded"] = True
    runtime["runtime_scope"] = "frozen_stdlib_site_packages_and_snapshot_scripts_only"
    ps_invocation = Path("/bin/ps")
    ps_binary = ps_invocation.resolve(strict=True)
    runtime["process_observer"] = {
        "invocation_path": str(ps_invocation),
        "resolved_path": str(ps_binary),
        "sha256": sha256_file(ps_binary),
    }
    return add_self_hash(runtime, "runtime_sha256")


def materialize_issue_histories(
    review_id: str, case_inputs: list[dict[str, Any]]
) -> tuple[Path, list[dict[str, Any]]]:
    root = WORK_ROOT / "review_generation" / "effective_issue_history" / review_id
    if root.exists():
        raise RepairPipelineError(f"issue-history snapshot already exists: {root}")
    root.mkdir(parents=True)
    finalized: list[dict[str, Any]] = []
    try:
        for row in case_inputs:
            item = copy.deepcopy(row)
            payload = item.pop("_issue_history_payload", None)
            case_id = str(item["case_unit_id"])
            if not isinstance(payload, Mapping):
                raise RepairPipelineError(f"{case_id} has no normalized issue-history payload")
            verify_issue_history(payload, case_id=case_id, rank=int(item["selection_rank"]))
            path = root / case_id / "issue_history.json"
            write_json_atomic(path, payload)
            path.chmod(0o444)
            item["input_bindings"]["issue_history"] = file_binding(path)
            item["issue_history_sha256"] = payload["issue_history_sha256"]
            item["case_input_sha256"] = object_sha256(item)
            finalized.append(item)
        for directory in sorted(
            (path for path in root.rglob("*") if path.is_dir()), reverse=True
        ):
            directory.chmod(0o555)
        root.chmod(0o555)
    except BaseException:
        for path in root.rglob("*"):
            if path.is_dir():
                path.chmod(0o755)
            else:
                path.chmod(0o644)
        shutil.rmtree(root, ignore_errors=True)
        raise
    return root, finalized


def copy_snapshot(
    review_id: str, checklist_schema_path: Path, codex: Mapping[str, Any]
) -> tuple[Path, dict[str, Any], dict[str, Any], dict[str, Any]]:
    root = WORK_ROOT / "review_generation" / "effective_toolchain_snapshot" / review_id
    if root.exists():
        raise RepairPipelineError(f"review snapshot already exists: {root}")
    scripts = root / "scripts"
    prompts = root / "prompts"
    schemas = root / "schemas"
    scripts.mkdir(parents=True)
    prompts.mkdir()
    schemas.mkdir()
    paths: dict[str, Path] = {}
    for role, source in REVIEW_TOOLS.items():
        if not source.is_file():
            raise RepairPipelineError(f"review tool is missing: {source}")
        destination = scripts / source.name
        shutil.copy2(source, destination)
        paths[role] = destination
    assert_prompt_policy(SOURCE_PROMPT)
    prompt_path = prompts / SOURCE_PROMPT.name
    proposal_path = schemas / SOURCE_PROPOSAL_SCHEMA.name
    checklist_path = schemas / "case_checklist.schema.json"
    shutil.copy2(SOURCE_PROMPT, prompt_path)
    shutil.copy2(SOURCE_PROPOSAL_SCHEMA, proposal_path)
    shutil.copy2(checklist_schema_path, checklist_path)
    proposal_schema = load_json(proposal_path, "semantic proposal schema")
    body_schema = model_body_schema(proposal_schema)
    body_path = schemas / "androidworld_checklist_semantic_review_body.schema.json"
    write_json_atomic(body_path, body_schema)
    paths.update(
        {
            "review_prompt": prompt_path,
            "proposal_schema": proposal_path,
            "model_output_schema": body_path,
            "checklist_schema": checklist_path,
        }
    )
    runtime = semantic_python_runtime(scripts, codex)
    runtime_path = root / "python_runtime.json"
    write_json_atomic(runtime_path, runtime)
    paths["python_runtime"] = runtime_path
    roles = {role: file_binding(path) for role, path in sorted(paths.items())}
    snapshot = {
        "schema_version": "androidworld_effective_semantic_review_toolchain_snapshot/v1",
        "review_id": review_id,
        "created_at": utc_now(),
        "roles": roles,
        "hard_prompt_policies": list(REQUIRED_PROMPT_POLICIES),
    }
    snapshot = add_self_hash(snapshot, "snapshot_sha256")
    snapshot_path = root / "snapshot_manifest.json"
    write_json_atomic(snapshot_path, snapshot)
    # Model tools are immutable after their hashes enter the prelock.  Directories
    # remain traversable but not writable; the proposal wave is elsewhere.
    for path in sorted((item for item in root.rglob("*") if item.is_file())):
        path.chmod(0o444)
    for path in sorted((item for item in root.rglob("*") if item.is_dir()), reverse=True):
        path.chmod(0o555)
    root.chmod(0o555)
    return root, snapshot, roles, runtime


def bootstrap_command(
    *,
    runtime: Mapping[str, Any],
    roles: Mapping[str, Mapping[str, Any]],
    prelock_path: Path,
    prelock_sha256: str,
    snapshot_tree_sha256: str,
    target_role: str,
    target_args: list[str] | None = None,
) -> list[str]:
    bootstrap_path = resolve_repo_path(roles["bootstrap"]["path"], inside_candidate=True)
    return [
        str(runtime["invocation_path"]),
        "-I",
        "-S",
        "-B",
        "-c",
        BOOTSTRAP_LAUNCHER,
        str(bootstrap_path),
        str(roles["bootstrap"]["sha256"]),
        "--prelock",
        str(prelock_path),
        "--prelock-file-sha256",
        sha256_file(prelock_path),
        "--prelock-internal-sha256",
        prelock_sha256,
        "--snapshot-tree-sha256",
        snapshot_tree_sha256,
        "--target-role",
        target_role,
        "--",
        *(target_args or []),
    ]


def run_bootstrap_self_test() -> int:
    with tempfile.TemporaryDirectory(
        prefix="semantic_bootstrap_selftest_", dir=WORK_ROOT
    ) as temporary:
        root = Path(temporary)
        snapshot_root = root / "snapshot"
        scripts = snapshot_root / "scripts"
        scripts.mkdir(parents=True)
        bootstrap_path = scripts / "semantic_review_bootstrap.py"
        target_path = scripts / "dummy_batch_runner.py"
        shutil.copy2(REVIEW_TOOLS["bootstrap"], bootstrap_path)
        target_bytes = (
            b"import json,sys\n"
            b"assert sys.flags.isolated == 1 and sys.flags.no_site == 1\n"
            b"assert sys.dont_write_bytecode\n"
            b"print(json.dumps({'status':'bootstrap_dummy_pass'}))\n"
        )
        target_path.write_bytes(target_bytes)
        codex_raw = shutil.which("codex")
        if not codex_raw:
            raise RepairPipelineError("bootstrap self-test requires the frozen Codex invocation")
        codex_stub = Path(os.path.abspath(codex_raw))
        runtime = semantic_python_runtime(
            scripts,
            {
                "invocation_path": str(codex_stub),
            },
        )
        runtime_path = snapshot_root / "python_runtime.json"
        write_json_atomic(runtime_path, runtime)
        roles = {
            "bootstrap": file_binding(bootstrap_path),
            "batch_runner": file_binding(target_path),
            "python_runtime": file_binding(runtime_path),
        }
        snapshot = add_self_hash(
            {
                "schema_version": "androidworld_effective_semantic_review_toolchain_snapshot/v1",
                "review_id": "bootstrap_selftest",
                "created_at": utc_now(),
                "roles": roles,
                "hard_prompt_policies": [],
            },
            "snapshot_sha256",
        )
        snapshot_path = snapshot_root / "snapshot_manifest.json"
        write_json_atomic(snapshot_path, snapshot)
        exact_tree = canonical_runtime_tree(snapshot_root)
        config = add_self_hash(
            {"schema_version": CONFIG_SCHEMA_VERSION, "status": "prelocked"},
            "config_sha256",
        )
        config_path = root / "config.json"
        write_json_atomic(config_path, config)
        bootstrap_record = {
            "schema_version": "androidworld_semantic_review_isolated_bootstrap/v1",
            "launcher_source": BOOTSTRAP_LAUNCHER,
            "launcher_sha256": sha256_bytes(BOOTSTRAP_LAUNCHER.encode("utf-8")),
            "entrypoint": roles["bootstrap"],
            "entrypoint_sha256": roles["bootstrap"]["sha256"],
            "required_python_flags": ["-I", "-S", "-B"],
            "target_roles": ["batch_runner", "independent_validator"],
        }
        security_payload = {"self_test": True}
        execution_payload = {
            "security_content_address": object_sha256(security_payload),
            "case_inputs_sha256": object_sha256([]),
            "config_sha256": config["config_sha256"],
            "python_runtime_sha256": runtime["runtime_sha256"],
            "toolchain_snapshot_sha256": snapshot["snapshot_sha256"],
            "toolchain_exact_tree_sha256": exact_tree["tree_sha256"],
            "bootstrap_launcher_sha256": bootstrap_record["launcher_sha256"],
            "bootstrap_entrypoint_sha256": bootstrap_record["entrypoint_sha256"],
        }
        prelock = {
            "repository_root": str(REPO_ROOT.resolve()),
            "toolchain_snapshot_root_absolute": str(snapshot_root.resolve()),
            "toolchain_exact_tree": exact_tree,
            "toolchain_snapshot": file_binding(snapshot_path)
            | {"snapshot_sha256": snapshot["snapshot_sha256"]},
            "tool_bindings": roles,
            "python_runtime": file_binding(runtime_path)
            | {"runtime_sha256": runtime["runtime_sha256"]},
            "isolated_bootstrap": bootstrap_record,
            "review_config": file_binding(config_path)
            | {"config_sha256": config["config_sha256"]},
            "case_inputs_sha256": object_sha256([]),
            "security_content_payload": security_payload,
            "security_content_address": object_sha256(security_payload),
            "execution_security_payload": execution_payload,
            "execution_security_address": object_sha256(execution_payload),
        }
        prelock = add_self_hash(prelock, "prelock_sha256")
        prelock_path = root / "prelock.json"
        write_json_atomic(prelock_path, prelock)
        command = bootstrap_command(
            runtime=runtime,
            roles=roles,
            prelock_path=prelock_path,
            prelock_sha256=prelock["prelock_sha256"],
            snapshot_tree_sha256=exact_tree["tree_sha256"],
            target_role="batch_runner",
        )
        environment = os.environ.copy()
        for variable in runtime["forbidden_child_python_environment"]:
            environment.pop(variable, None)
        environment.update(runtime["required_environment"])
        positive = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
            env=environment,
        )
        if positive.returncode != 0 or "bootstrap_dummy_pass" not in positive.stdout:
            raise RepairPipelineError(
                f"isolated bootstrap positive self-test failed: {positive.stderr}"
            )
        target_path.write_bytes(target_bytes + b"# tamper\n")
        negative = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
            env=environment,
        )
        target_path.write_bytes(target_bytes)
        if negative.returncode == 0:
            raise RepairPipelineError("isolated bootstrap accepted a tampered toolchain tree")
    print(
        json.dumps(
            {
                "status": "self_test_pass",
                "isolated_flags": ["-I", "-S", "-B"],
                "positive_bootstrap": True,
                "tampered_toolchain_rejected": True,
                "model_invoked": False,
            },
            indent=2,
        )
    )
    return 0


def main() -> int:
    args = parse_args()
    assert_prompt_policy(SOURCE_PROMPT)
    if args.bootstrap_self_test:
        return run_bootstrap_self_test()
    if args.self_test:
        source, packets, schema_path = source_context(args.source_draft_prelock)
        proposal = load_json(SOURCE_PROPOSAL_SCHEMA, "proposal schema")
        body = model_body_schema(proposal)
        if not schema_errors({}, body):
            raise RepairPipelineError("derived review body schema unexpectedly accepts empty input")
        print(
            json.dumps(
                {
                    "status": "self_test_pass",
                    "case_count": len(packets),
                    "case_order_sha256": source["case_order_sha256"],
                    "frozen_checklist_schema": file_binding(schema_path),
                    "prompt_hard_policy_count": len(REQUIRED_PROMPT_POLICIES),
                    "negative_empty_body_rejected": True,
                    "model_invoked": False,
                },
                indent=2,
            )
        )
        return 0
    if args.effective_manifest is None or args.effective_qc_root is None:
        raise RepairPipelineError("--effective-manifest and --effective-qc-root are required")
    if args.max_parallel != EXPECTED_PARALLELISM:
        raise RepairPipelineError("effective semantic review requires exactly six workers")
    if args.model != EXPECTED_MODEL or args.reasoning_effort != EXPECTED_REASONING_EFFORT:
        raise RepairPipelineError(
            f"effective semantic review requires {EXPECTED_MODEL}/{EXPECTED_REASONING_EFFORT}"
        )
    if args.codex_timeout_seconds <= 0 or args.max_attempts <= 0:
        raise RepairPipelineError("review timeout and max attempts must be positive")

    manifest_path = args.effective_manifest.resolve()
    qc_root = args.effective_qc_root.resolve()
    for label, path in (("effective manifest", manifest_path), ("effective QC", qc_root)):
        try:
            path.relative_to(WORK_ROOT.resolve())
        except ValueError as exc:
            raise RepairPipelineError(f"{label} must stay inside candidate116") from exc
    source_prelock_path = args.source_draft_prelock.resolve()
    source, packet_by_case, checklist_schema_path = source_context(source_prelock_path)
    manifest, qc_summary, case_inputs = effective_context(
        manifest_path, qc_root, source, packet_by_case, checklist_schema_path
    )
    qc_summary_path = qc_root / "summary.json"
    codex = codex_binding()
    compatibility_content_payload = {
            "effective_manifest_sha256": manifest["effective_manifest_sha256"],
            "effective_qc_summary_sha256": qc_summary["summary_sha256"],
            "repair_concurrency_evidence_sha256": manifest[
                "repair_concurrency_evidence"
            ]["evidence_sha256"],
            "source_prelock_sha256": source["prelock_sha256"],
            "prompt_sha256": sha256_file(SOURCE_PROMPT),
            "proposal_schema_sha256": sha256_file(SOURCE_PROPOSAL_SCHEMA),
            "checklist_schema_sha256": sha256_file(checklist_schema_path),
            "review_tools_sha256": {
                role: sha256_file(REVIEW_TOOLS[role])
                for role in (
                    "batch_runner",
                    "common",
                    "independent_validator",
                    "prelock_builder",
                )
            },
            "codex_binary_sha256": codex["binary_sha256"],
            "codex_version": codex["version"],
            "model": args.model,
            "reasoning_effort": args.reasoning_effort,
            "max_parallel": args.max_parallel,
    }
    compatibility_content_id = object_sha256(compatibility_content_payload)
    security_content_payload = {
            **compatibility_content_payload,
            "all_review_tools_sha256": {
                role: sha256_file(path) for role, path in sorted(REVIEW_TOOLS.items())
            },
            "issue_history_payloads_sha256": object_sha256(
                [
                    {
                        "case_unit_id": row["case_unit_id"],
                        "issue_history_sha256": row["_issue_history_payload"][
                            "issue_history_sha256"
                        ],
                    }
                    for row in case_inputs
                ]
            ),
            "bootstrap_launcher_sha256": sha256_bytes(BOOTSTRAP_LAUNCHER.encode("utf-8")),
    }
    security_content_id = object_sha256(security_content_payload)
    review_id = args.review_id or f"effective_semantic_review_{security_content_id[:16]}"
    if not safe_id(review_id):
        raise RepairPipelineError("review id may contain only letters, digits, dots, dashes, underscores")
    output_root = WORK_ROOT / "review_generation" / "effective_waves" / review_id
    config_path = WORK_ROOT / "review_generation" / "effective_config" / f"{review_id}.json"
    prelock_path = WORK_ROOT / "review_generation" / "effective_freeze" / f"{review_id}.json"
    snapshot_root = WORK_ROOT / "review_generation" / "effective_toolchain_snapshot" / review_id
    issue_history_root = (
        WORK_ROOT / "review_generation" / "effective_issue_history" / review_id
    )
    for target in (output_root, config_path, prelock_path, snapshot_root, issue_history_root):
        if target.exists():
            raise RepairPipelineError(f"refusing to overwrite review artifact: {target}")
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry_run_pass",
                    "review_id": review_id,
                    "case_count": len(case_inputs),
                    "origin_counts": manifest["origin_counts"],
                    "max_parallel": args.max_parallel,
                    "content_id": compatibility_content_id,
                    "security_content_address": security_content_id,
                    "codex": codex,
                    "model_invoked": False,
                },
                indent=2,
            )
        )
        return 0

    issue_history_root, case_inputs = materialize_issue_histories(review_id, case_inputs)
    snapshot_root, snapshot, roles, runtime = copy_snapshot(
        review_id, checklist_schema_path, codex
    )
    snapshot_path = snapshot_root / "snapshot_manifest.json"
    snapshot_exact_tree = canonical_runtime_tree(snapshot_root)
    runtime_path = resolve_repo_path(roles["python_runtime"]["path"], inside_candidate=True)
    bootstrap_record = {
        "schema_version": "androidworld_semantic_review_isolated_bootstrap/v1",
        "launcher_source": BOOTSTRAP_LAUNCHER,
        "launcher_sha256": sha256_bytes(BOOTSTRAP_LAUNCHER.encode("utf-8")),
        "entrypoint": copy.deepcopy(roles["bootstrap"]),
        "entrypoint_sha256": roles["bootstrap"]["sha256"],
        "required_python_flags": ["-I", "-S", "-B"],
        "target_roles": ["batch_runner", "independent_validator"],
    }
    config = {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "status": "prelocked",
        "review_id": review_id,
        "source_generation_id": manifest["effective_wave_id"],
        "provider": "codex_cli",
        "auth_mode": "codex_login",
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "sandbox": "read-only",
        "ephemeral": True,
        "ignore_user_config": True,
        "max_parallel": args.max_parallel,
        "codex_timeout_seconds": args.codex_timeout_seconds,
        "max_attempts": args.max_attempts,
        "case_count": EXPECTED_CASE_COUNT,
        "output_root": repo_relative(output_root),
        "entrypoint": roles["batch_runner"],
        "isolated_bootstrap": bootstrap_record,
        "python_runtime": file_binding(runtime_path)
        | {"runtime_sha256": runtime["runtime_sha256"]},
        "toolchain_exact_tree_sha256": snapshot_exact_tree["tree_sha256"],
        "prompt": roles["review_prompt"],
        "proposal_schema": roles["proposal_schema"],
        "model_output_schema": roles["model_output_schema"],
        "created_at": utc_now(),
    }
    config = add_self_hash(config, "config_sha256")
    write_json_atomic(config_path, config)
    execution_security_payload = {
        "security_content_address": security_content_id,
        "case_inputs_sha256": object_sha256(case_inputs),
        "config_sha256": config["config_sha256"],
        "python_runtime_sha256": runtime["runtime_sha256"],
        "toolchain_snapshot_sha256": snapshot["snapshot_sha256"],
        "toolchain_exact_tree_sha256": snapshot_exact_tree["tree_sha256"],
        "bootstrap_launcher_sha256": bootstrap_record["launcher_sha256"],
        "bootstrap_entrypoint_sha256": bootstrap_record["entrypoint_sha256"],
    }
    prelock = {
        "schema_version": PRELOCK_SCHEMA_VERSION,
        "status": "frozen_before_first_review_model_call",
        "review_id": review_id,
        "source_generation_id": manifest["effective_wave_id"],
        "created_at": utc_now(),
        "case_count": EXPECTED_CASE_COUNT,
        "case_order": list(manifest["case_order"]),
        "case_order_sha256": manifest["case_order_sha256"],
        "case_inputs": case_inputs,
        "case_inputs_sha256": object_sha256(case_inputs),
        "repository_root": str(REPO_ROOT.resolve()),
        "toolchain_snapshot_root_absolute": str(snapshot_root.resolve()),
        "toolchain_exact_tree": snapshot_exact_tree,
        "python_runtime": file_binding(runtime_path)
        | {"runtime_sha256": runtime["runtime_sha256"]},
        "isolated_bootstrap": bootstrap_record,
        "issue_history_root": repo_relative(issue_history_root),
        "effective_generation": {
            "effective_manifest": file_binding(manifest_path)
            | {"effective_manifest_sha256": manifest["effective_manifest_sha256"]},
            "effective_wave": repo_relative(manifest_path.parent),
            "source_draft_prelock": file_binding(source_prelock_path)
            | {"prelock_sha256": source["prelock_sha256"]},
            "repair_concurrency_evidence": copy.deepcopy(
                manifest["repair_concurrency_evidence"]
            ),
            "repair_concurrency_audit": copy.deepcopy(
                manifest["repair_concurrency_audit"]
            ),
            "repair_concurrency_samples": copy.deepcopy(
                manifest["repair_concurrency_samples"]
            ),
        },
        "automatic_qc_summary": file_binding(qc_summary_path)
        | {"summary_sha256": qc_summary["summary_sha256"]},
        "review_config": file_binding(config_path) | {"config_sha256": config["config_sha256"]},
        "toolchain_snapshot": file_binding(snapshot_path)
        | {"snapshot_sha256": snapshot["snapshot_sha256"]},
        "tool_bindings": roles,
        "codex_cli": codex,
        "content_address": compatibility_content_id,
        "security_content_payload": security_content_payload,
        "security_content_address": security_content_id,
        "execution_security_payload": execution_security_payload,
        "execution_security_address": object_sha256(execution_security_payload),
        "hard_semantic_policies": {
            "exception_nan_or_no_numeric_raw_is_undecided": True,
            "metadata_code_differences_explicit": True,
            "parameter_schema_generator_differences_explicit": True,
        },
        "canonical_output_gate": {
            "proposal_wave": repo_relative(output_root),
            "final_root_agent_review_root": repo_relative(
                WORK_ROOT / "review_generation" / "finalized_reviews" / review_id
            ),
            "model_proposals_are_not_human_reviews": True,
            "all_116_proposals_must_be_accepted": True,
            "independent_validation_must_pass": True,
            "promotion_authorized": False,
            "exact_six_process_lifecycle_evidence_required": True,
        },
    }
    prelock = add_self_hash(prelock, "prelock_sha256")
    write_json_atomic(prelock_path, prelock)
    print(
        json.dumps(
            {
                "status": "prelocked",
                "review_id": review_id,
                "case_count": EXPECTED_CASE_COUNT,
                "origin_counts": manifest["origin_counts"],
                "content_address": compatibility_content_id,
                "security_content_address": security_content_id,
                "prelock": file_binding(prelock_path)
                | {"prelock_sha256": prelock["prelock_sha256"]},
                "snapshot": file_binding(snapshot_path)
                | {"snapshot_sha256": snapshot["snapshot_sha256"]},
                "run_command": bootstrap_command(
                    runtime=runtime,
                    roles=roles,
                    prelock_path=prelock_path,
                    prelock_sha256=prelock["prelock_sha256"],
                    snapshot_tree_sha256=snapshot_exact_tree["tree_sha256"],
                    target_role="batch_runner",
                    target_args=["--prelock", str(prelock_path)],
                ),
                "validation_command": bootstrap_command(
                    runtime=runtime,
                    roles=roles,
                    prelock_path=prelock_path,
                    prelock_sha256=prelock["prelock_sha256"],
                    snapshot_tree_sha256=snapshot_exact_tree["tree_sha256"],
                    target_role="independent_validator",
                    target_args=["--prelock", str(prelock_path)],
                ),
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
