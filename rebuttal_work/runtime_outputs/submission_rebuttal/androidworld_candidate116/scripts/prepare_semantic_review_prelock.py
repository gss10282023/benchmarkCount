#!/usr/bin/env python3
"""Prelock one independent 116-case semantic-review wave.

This command must run only after the selected draft wave and its deterministic
automatic QC are complete.  The draft prelock is supplied explicitly; its
packet-input index and raw-wave path are authoritative, so this tool does not
hard-code a packet flavor or a draft generation id.
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from semantic_review_common import (
    CONFIG_SCHEMA_VERSION,
    EXPECTED_CASE_COUNT,
    EXPECTED_PARALLELISM,
    PRELOCK_SCHEMA_VERSION,
    REPO_ROOT,
    WORK_ROOT,
    SemanticReviewError,
    add_self_hash,
    file_binding,
    load_json,
    load_yaml_mapping,
    model_body_schema,
    object_sha256,
    parse_case_packet,
    repo_relative,
    resolve_repo_path,
    schema_errors,
    sha256_file,
    utc_now,
    verify_file_binding,
    verify_self_hash,
    write_json_atomic,
)


SCRIPT = Path(__file__).resolve()
SOURCE_SCRIPTS = WORK_ROOT / "scripts"
SOURCE_PROMPT = WORK_ROOT / "prompts" / "androidworld_checklist_semantic_review_v1.prompt.md"
SOURCE_PROPOSAL_SCHEMA = (
    WORK_ROOT / "schemas" / "androidworld_checklist_semantic_review_proposal.schema.json"
)
REQUIRED_REVIEW_TOOLS = (
    "semantic_review_common.py",
    "prepare_semantic_review_prelock.py",
    "run_semantic_review_batch.py",
    "validate_semantic_review_batch.py",
)
REQUIRED_DRAFT_SIDECARS = (
    "checklist.json",
    "llm_call.json",
    "api_response.json",
    "reasoning_summary.txt",
    "stdout.log",
    "stderr.log",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--draft-prelock",
        type=Path,
        required=True,
        help="Exact new draft-wave prelock; compact/wave_002 prelocks are not assumed.",
    )
    parser.add_argument(
        "--automatic-qc-root",
        type=Path,
        required=True,
        help="Root containing summary.json and <case>/qc.json for the same draft wave.",
    )
    parser.add_argument(
        "--wave-root",
        type=Path,
        help="Optional assertion; otherwise derived from draft prelock canonical_output_gate.",
    )
    parser.add_argument("--review-id", help="Defaults to semantic_review_<draft generation id>.")
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument(
        "--reasoning-effort",
        default="xhigh",
        choices=("minimal", "low", "medium", "high", "xhigh"),
    )
    parser.add_argument("--codex-timeout-seconds", type=int, default=1800)
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=EXPECTED_PARALLELISM,
        help="Strict protocol requires exactly six.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate all completed inputs and login, but write no snapshot/prelock.",
    )
    return parser.parse_args()


def packet_rows(prelock: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Accept the selected prelock's declared packet index without flavor assumptions."""
    for key in ("packet_inputs", "case_packet_inputs", "compact_packet_inputs"):
        value = prelock.get(key)
        if isinstance(value, list):
            rows = []
            for raw in value:
                if not isinstance(raw, Mapping):
                    raise SemanticReviewError(f"draft prelock {key} contains a non-object")
                item = dict(raw)
                if "path" not in item:
                    item["path"] = item.get("packet_path") or item.get("case_packet_path")
                rows.append(item)
            return rows
    raise SemanticReviewError(
        "draft prelock has none of packet_inputs/case_packet_inputs/compact_packet_inputs"
    )


def raw_wave_from_prelock(prelock: Mapping[str, Any]) -> Path:
    gate = prelock.get("canonical_output_gate")
    if not isinstance(gate, Mapping):
        raise SemanticReviewError("draft prelock has no canonical_output_gate")
    for key in ("raw_wave", "wave_root", "output_root"):
        if gate.get(key):
            return resolve_repo_path(gate[key], inside_candidate=True)
    raise SemanticReviewError("draft prelock does not bind a raw wave path")


def frozen_checklist_schema(prelock: Mapping[str, Any]) -> Path:
    tools = prelock.get("tool_bindings")
    if not isinstance(tools, Mapping):
        raise SemanticReviewError("draft prelock has no tool_bindings")
    for name, binding in tools.items():
        normalized = str(name).casefold().replace("-", "_")
        if "checklist" in normalized and "schema" in normalized and isinstance(binding, Mapping):
            return verify_file_binding(binding, f"draft tool {name}", inside_candidate=True)
    raise SemanticReviewError("draft prelock does not bind its checklist schema")


def verify_draft_prelock(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    try:
        resolved.relative_to(WORK_ROOT.resolve())
    except ValueError as exc:
        raise SemanticReviewError("draft prelock must be inside candidate116") from exc
    prelock = load_json(resolved, "draft prelock")
    hash_fields = [key for key in prelock if key.endswith("prelock_sha256")]
    if "prelock_sha256" in prelock:
        verify_self_hash(prelock, "prelock_sha256", "draft prelock")
    elif hash_fields:
        verify_self_hash(prelock, hash_fields[0], "draft prelock")
    else:
        raise SemanticReviewError("draft prelock has no canonical self hash")
    if int(prelock.get("case_count", -1)) != EXPECTED_CASE_COUNT:
        raise SemanticReviewError("draft prelock is not a 116-case lock")
    return prelock


def check_codex() -> dict[str, Any]:
    binary_raw = shutil.which("codex")
    if not binary_raw:
        raise SemanticReviewError("codex is not on PATH")
    binary = Path(binary_raw).resolve()
    version = subprocess.run(
        [str(binary), "--version"], capture_output=True, text=True, check=False, timeout=30
    )
    login = subprocess.run(
        [str(binary), "login", "status"], capture_output=True, text=True, check=False, timeout=30
    )
    login_detail = "\n".join(
        part.strip() for part in (login.stdout, login.stderr) if part.strip()
    )
    if login.returncode != 0 or "logged in" not in login_detail.casefold():
        raise SemanticReviewError(f"Codex CLI login is not active: {login_detail}")
    if version.returncode != 0:
        raise SemanticReviewError("cannot obtain Codex CLI version")
    return {
        "binary_path": str(binary),
        "binary_sha256": sha256_file(binary),
        "version": (version.stdout or version.stderr).strip(),
        "login_status_at_prelock": login_detail,
        "auth_mode": "codex_login",
    }


def copy_snapshot(review_id: str, checklist_schema: Path) -> tuple[Path, dict[str, Any]]:
    snapshot_root = WORK_ROOT / "review_generation" / "toolchain_snapshot" / review_id
    if snapshot_root.exists():
        raise SemanticReviewError(f"review snapshot already exists: {snapshot_root}")
    scripts_dir = snapshot_root / "scripts"
    prompts_dir = snapshot_root / "prompts"
    schemas_dir = snapshot_root / "schemas"
    scripts_dir.mkdir(parents=True)
    prompts_dir.mkdir(parents=True)
    schemas_dir.mkdir(parents=True)

    for name in REQUIRED_REVIEW_TOOLS:
        source = SOURCE_SCRIPTS / name
        if not source.is_file():
            raise SemanticReviewError(f"review tool source is missing: {source}")
        shutil.copy2(source, scripts_dir / name)
    shutil.copy2(SOURCE_PROMPT, prompts_dir / SOURCE_PROMPT.name)
    shutil.copy2(SOURCE_PROPOSAL_SCHEMA, schemas_dir / SOURCE_PROPOSAL_SCHEMA.name)
    shutil.copy2(checklist_schema, schemas_dir / "case_checklist.schema.json")

    proposal_schema = load_json(SOURCE_PROPOSAL_SCHEMA, "proposal schema")
    body_schema = model_body_schema(proposal_schema)
    body_path = schemas_dir / "androidworld_checklist_semantic_review_body.schema.json"
    write_json_atomic(body_path, body_schema)

    roles = {
        "common": scripts_dir / "semantic_review_common.py",
        "prelock_builder": scripts_dir / "prepare_semantic_review_prelock.py",
        "batch_runner": scripts_dir / "run_semantic_review_batch.py",
        "independent_validator": scripts_dir / "validate_semantic_review_batch.py",
        "review_prompt": prompts_dir / SOURCE_PROMPT.name,
        "proposal_schema": schemas_dir / SOURCE_PROPOSAL_SCHEMA.name,
        "model_output_schema": body_path,
        "checklist_schema": schemas_dir / "case_checklist.schema.json",
    }
    manifest = {
        "schema_version": "androidworld_semantic_review_toolchain_snapshot/v1",
        "review_id": review_id,
        "created_at": utc_now(),
        "roles": {name: file_binding(path) for name, path in sorted(roles.items())},
    }
    manifest = add_self_hash(manifest, "snapshot_sha256")
    manifest_path = snapshot_root / "snapshot_manifest.json"
    write_json_atomic(manifest_path, manifest)
    return snapshot_root, manifest


def build_case_inputs(
    *,
    draft_prelock: Mapping[str, Any],
    wave_root: Path,
    qc_root: Path,
    checklist_schema: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    rows = packet_rows(draft_prelock)
    order = list(draft_prelock.get("case_order") or [])
    if len(rows) != EXPECTED_CASE_COUNT or len(order) != EXPECTED_CASE_COUNT:
        raise SemanticReviewError("draft prelock packet rows/case order are not both 116")
    by_case = {str(row.get("case_unit_id") or ""): row for row in rows}
    if set(by_case) != set(order) or len(by_case) != EXPECTED_CASE_COUNT:
        raise SemanticReviewError("draft prelock packet index differs from its case order")

    case_inputs: list[dict[str, Any]] = []
    for rank, case_id in enumerate(order):
        packet_record = by_case[case_id]
        if packet_record.get("selection_rank") not in (None, rank):
            raise SemanticReviewError(f"{case_id} packet selection rank mismatch")
        packet_path = resolve_repo_path(packet_record.get("path"), inside_candidate=True)
        packet_binding = file_binding(packet_path)
        if packet_record.get("sha256") and packet_record.get("sha256") != packet_binding["sha256"]:
            raise SemanticReviewError(f"{case_id} packet hash differs from draft prelock")
        if packet_record.get("size_bytes") not in (None, packet_binding["size_bytes"]):
            raise SemanticReviewError(f"{case_id} packet size differs from draft prelock")
        parsed_packet = parse_case_packet(packet_path.read_text(encoding="utf-8"))
        identity = parsed_packet["identity"]
        task_id = str(identity.get("task_id") or "")
        if identity.get("case_unit_id") != case_id or not task_id:
            raise SemanticReviewError(f"{case_id} packet identity is invalid")

        case_dir = wave_root / case_id
        checklist_yaml = case_dir / "checklist.yaml"
        checklist_json = case_dir / "checklist.json"
        yaml_payload = load_yaml_mapping(checklist_yaml, f"{case_id} raw checklist YAML")
        json_payload = load_json(checklist_json, f"{case_id} raw checklist JSON")
        if yaml_payload != json_payload:
            raise SemanticReviewError(f"{case_id} raw checklist YAML/JSON differ")
        checklist_errors = schema_errors(yaml_payload, checklist_schema)
        if checklist_errors:
            raise SemanticReviewError(f"{case_id} raw checklist schema fails: {checklist_errors}")
        if (
            yaml_payload.get("case_unit_id") != case_id
            or yaml_payload.get("task_id") != task_id
            or yaml_payload.get("domain") != "androidworld"
        ):
            raise SemanticReviewError(f"{case_id} raw checklist identity differs from packet")

        sidecars = {
            name.rsplit(".", 1)[0]: file_binding(case_dir / name)
            for name in REQUIRED_DRAFT_SIDECARS
        }
        qc_path = qc_root / case_id / "qc.json"
        qc = load_json(qc_path, f"{case_id} automatic QC")
        if (
            qc.get("case_unit_id") != case_id
            or qc.get("task_id") != task_id
            or qc.get("status") != "passed"
            or qc.get("issues") != []
        ):
            raise SemanticReviewError(f"{case_id} automatic QC is not a clean pass")
        qc_checklist = resolve_repo_path(qc.get("checklist_path"), inside_candidate=True)
        if qc_checklist.resolve() != checklist_yaml.resolve():
            raise SemanticReviewError(f"{case_id} QC inspected a different checklist path")
        if qc.get("checklist_sha256") != sha256_file(checklist_yaml):
            raise SemanticReviewError(f"{case_id} QC checklist hash differs")

        bindings = {
            "packet": packet_binding,
            "raw_checklist_yaml": file_binding(checklist_yaml),
            "raw_checklist_json": file_binding(checklist_json),
            "automatic_qc": file_binding(qc_path),
            "draft_sidecars": sidecars,
        }
        row = {
            "case_unit_id": case_id,
            "task_id": task_id,
            "selection_rank": rank,
            "packet_kind": parsed_packet["kind"],
            "input_bindings": bindings,
        }
        row["case_input_sha256"] = object_sha256(row)
        case_inputs.append(row)
    return case_inputs, order


def main() -> int:
    args = parse_args()
    if args.max_parallel != EXPECTED_PARALLELISM:
        raise SemanticReviewError("semantic review protocol requires exactly 6 concurrent workers")
    if args.codex_timeout_seconds <= 0 or args.max_attempts <= 0:
        raise SemanticReviewError("timeouts and attempt count must be positive")
    draft_prelock_path = args.draft_prelock.resolve()
    draft_prelock = verify_draft_prelock(draft_prelock_path)
    generation_id = str(draft_prelock.get("generation_id") or "").strip()
    if not generation_id:
        raise SemanticReviewError("draft prelock has no generation_id")
    review_id = args.review_id or f"semantic_review_{generation_id}"
    if not re_safe_id(review_id):
        raise SemanticReviewError("review id must contain only letters, digits, underscores, dots, or hyphens")

    declared_wave = raw_wave_from_prelock(draft_prelock)
    wave_root = args.wave_root.resolve() if args.wave_root else declared_wave
    if wave_root != declared_wave:
        raise SemanticReviewError("--wave-root differs from the draft-prelocked raw wave")
    if not wave_root.is_dir():
        raise SemanticReviewError(f"draft raw wave is missing: {wave_root}")
    qc_root = args.automatic_qc_root.resolve()
    try:
        qc_root.relative_to(WORK_ROOT.resolve())
    except ValueError as exc:
        raise SemanticReviewError("automatic QC root must be inside candidate116") from exc
    qc_summary_path = qc_root / "summary.json"
    qc_summary = load_json(qc_summary_path, "automatic QC summary")
    expected_summary = {
        "status": "pass",
        "case_count": EXPECTED_CASE_COUNT,
        "passed_count": EXPECTED_CASE_COUNT,
        "failed_count": 0,
        "issues": [],
    }
    for key, expected in expected_summary.items():
        if qc_summary.get(key) != expected:
            raise SemanticReviewError(
                f"automatic QC summary {key}={qc_summary.get(key)!r}, expected {expected!r}"
            )

    checklist_schema_path = frozen_checklist_schema(draft_prelock)
    checklist_schema = load_json(checklist_schema_path, "frozen checklist schema")
    case_inputs, case_order = build_case_inputs(
        draft_prelock=draft_prelock,
        wave_root=wave_root,
        qc_root=qc_root,
        checklist_schema=checklist_schema,
    )
    batch_summary_path = wave_root / "_batch_summary.json"
    if not batch_summary_path.is_file():
        raise SemanticReviewError("draft wave has no _batch_summary.json")
    codex = check_codex()

    output_root = WORK_ROOT / "review_generation" / "waves" / review_id
    config_path = WORK_ROOT / "review_generation" / "config" / f"{review_id}.config.json"
    prelock_path = WORK_ROOT / "review_generation" / "freeze" / f"{review_id}.prelock.json"
    for target in (output_root, config_path, prelock_path):
        if target.exists():
            raise SemanticReviewError(f"refusing to overwrite review artifact: {target}")

    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry_run_pass",
                    "review_id": review_id,
                    "generation_id": generation_id,
                    "case_count": len(case_inputs),
                    "packet_kinds": dict(Counter(row["packet_kind"] for row in case_inputs)),
                    "raw_wave": repo_relative(wave_root),
                    "automatic_qc": repo_relative(qc_summary_path),
                    "max_parallel": args.max_parallel,
                    "codex": codex,
                },
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
        )
        return 0

    snapshot_root, snapshot_manifest = copy_snapshot(review_id, checklist_schema_path)
    snapshot_manifest_path = snapshot_root / "snapshot_manifest.json"
    roles = snapshot_manifest["roles"]
    config = {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "status": "prelocked",
        "review_id": review_id,
        "source_generation_id": generation_id,
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
        "prompt": roles["review_prompt"],
        "proposal_schema": roles["proposal_schema"],
        "model_output_schema": roles["model_output_schema"],
        "created_at": utc_now(),
    }
    config = add_self_hash(config, "config_sha256")
    write_json_atomic(config_path, config)

    draft_binding = file_binding(draft_prelock_path)
    if draft_prelock.get("prelock_sha256"):
        draft_binding["prelock_sha256"] = draft_prelock["prelock_sha256"]
    prelock = {
        "schema_version": PRELOCK_SCHEMA_VERSION,
        "status": "frozen_before_first_review_model_call",
        "review_id": review_id,
        "source_generation_id": generation_id,
        "created_at": utc_now(),
        "case_count": EXPECTED_CASE_COUNT,
        "case_order": case_order,
        "case_order_sha256": object_sha256(case_order),
        "case_inputs": case_inputs,
        "case_inputs_sha256": object_sha256(case_inputs),
        "draft_generation": {
            "prelock": draft_binding,
            "raw_wave": {
                "path": repo_relative(wave_root),
                "batch_summary": file_binding(batch_summary_path),
            },
        },
        "automatic_qc_summary": file_binding(qc_summary_path),
        "review_config": file_binding(config_path) | {"config_sha256": config["config_sha256"]},
        "toolchain_snapshot": file_binding(snapshot_manifest_path)
        | {"snapshot_sha256": snapshot_manifest["snapshot_sha256"]},
        "tool_bindings": roles,
        "codex_cli": codex,
        "canonical_output_gate": {
            "proposal_wave": repo_relative(output_root),
            "final_human_review_root": repo_relative(WORK_ROOT / "draft_generation" / "reviews"),
            "model_proposals_must_not_be_copied_to_final_review": True,
            "promotion_authorized": False,
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
                "config": file_binding(config_path),
                "prelock": file_binding(prelock_path) | {"prelock_sha256": prelock["prelock_sha256"]},
                "snapshot": file_binding(snapshot_manifest_path)
                | {"snapshot_sha256": snapshot_manifest["snapshot_sha256"]},
                "run_command": [
                    sys.executable,
                    str(resolve_repo_path(roles["batch_runner"]["path"], inside_candidate=True)),
                    "--prelock",
                    str(prelock_path),
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    )
    return 0


def re_safe_id(value: str) -> bool:
    return bool(value) and all(character.isalnum() or character in "_.-" for character in value)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SemanticReviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
