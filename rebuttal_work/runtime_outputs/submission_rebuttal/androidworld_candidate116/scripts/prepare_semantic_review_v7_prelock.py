#!/usr/bin/env python3
"""Prepare the create-once, no-model prelock for candidate116 semantic review v7."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

import semantic_review_v7_staging as review_staging
import wave004_v6_clean2_hardened_common as source_common
import wave004_v6_clean2_hardened_staging as source_staging
from semantic_review_v7_common import (
    CANDIDATE_ROOT,
    CASE_COUNT,
    CODEX_BINARY_SHA256,
    CODEX_LOGIN_STATUS,
    CODEX_VERSION,
    CONFIG_SCHEMA,
    MODEL,
    PARALLELISM,
    PRELOCK_SCHEMA,
    REASONING_EFFORT,
    REPOSITORY_ROOT,
    SemanticReviewV7Error,
    add_self_hash,
    canonical_sha256,
    checklist_semantic_inventory,
    exact_tree,
    is_exact_int,
    load_json,
    load_yaml,
    regular_file_binding,
    require_case_id,
    sha256_file,
    sha256_text,
    validate_json_schema,
    verify_self_hash,
    write_json_create_once,
)

sys.dont_write_bytecode = True


SCRIPT = Path(__file__).resolve()
PROMPT = (
    CANDIDATE_ROOT
    / "prompts"
    / "androidworld_candidate116_semantic_review_v7.prompt.md"
)
OUTPUT_SCHEMA = (
    CANDIDATE_ROOT
    / "schemas"
    / "androidworld_candidate116_semantic_review_v7.schema.json"
)
PACKET_INDEX = (
    CANDIDATE_ROOT / "indexes" / "androidworld_candidate116_packet_index.json"
)
TOKENIZER_ROOT = (
    CANDIDATE_ROOT / "draft_generation" / "tokenizer" / "tiktoken_0_12_0_py312"
)
TOKENIZER_CACHE = (
    TOKENIZER_ROOT / "encoding_cache" / "fb374d419588a4632f3f557e76b4b70aebbca790"
)
REVIEW_BASE = CANDIDATE_ROOT / "review_generation" / "semantic_review_v7"
QC_SCHEMA = "androidworld_candidate116_fresh_draft_deterministic_qc/v1"
GENERATION_RECEIPT_SCHEMA = (
    "androidworld_candidate116_fresh_draft_generation_receipt/v6_clean5_hardened"
)
GENERATION_QC_SCHEMA = (
    "androidworld_candidate116_wave004_v6_clean5_hardened_generation_qc/v1"
)
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$")
PROTOCOL_RESERVE_TOKENS = 8_000
GENERATION_OUTPUT_NAMES = (
    "checklist.yaml",
    "checklist.json",
    "api_response.json",
    "llm_call.json",
    "reasoning_summary.txt",
    "stderr.log",
    "stdout.log",
)
SOURCE_REGULAR_BINDING_FIELDS = frozenset(
    {"path", "kind", "sha256", "size_bytes", "mode"}
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-id", required=True)
    parser.add_argument("--raw-draft-root", type=Path, required=True)
    parser.add_argument("--draft-generation-prelock", type=Path, required=True)
    parser.add_argument("--draft-generation-receipt", type=Path, required=True)
    parser.add_argument("--draft-qc-report", type=Path, required=True)
    parser.add_argument("--checklist-schema", type=Path, required=True)
    parser.add_argument("--tokenizer-root", type=Path, default=TOKENIZER_ROOT)
    parser.add_argument("--tokenizer-cache", type=Path, default=TOKENIZER_CACHE)
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--reasoning-effort", default=REASONING_EFFORT)
    parser.add_argument("--max-parallel", type=int, default=PARALLELISM)
    parser.add_argument("--timeout-seconds", type=int, default=2400)
    parser.add_argument("--snapshot-root", type=Path)
    parser.add_argument("--capacity-out", type=Path)
    parser.add_argument("--config-out", type=Path)
    parser.add_argument("--prelock-out", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def require_safe_review_id(value: str) -> str:
    if not SAFE_ID_RE.fullmatch(value):
        raise SemanticReviewV7Error(f"unsafe review ID: {value!r}")
    return value


def load_hashed_document_bound(
    path: Path, field: str, label: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read one high-trust JSON document from one no-follow, identity-stable fd."""

    try:
        payload, binding = source_common.read_regular_bytes_bound(path, label=label)
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SemanticReviewV7Error(f"cannot decode {label}: {exc}") from exc
    except BaseException as exc:
        raise SemanticReviewV7Error(f"cannot bind {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise SemanticReviewV7Error(f"{label} is not a JSON object")
    verify_self_hash(value, field, label)
    return value, binding


def verify_hashed_document(path: Path, field: str, label: str) -> dict[str, Any]:
    value, _binding = load_hashed_document_bound(path, field, label)
    return value


def verify_qc_report(
    path: Path, expected_order: list[str]
) -> tuple[dict[str, Any], dict[str, Any]]:
    report, binding = load_hashed_document_bound(
        path, "report_sha256", "fresh draft deterministic QC"
    )
    if (
        report.get("schema_version") != QC_SCHEMA
        or report.get("status") != "pass_116_of_116"
        or not is_exact_int(
            report.get("production_case_count_required"), expected=CASE_COUNT
        )
        or not is_exact_int(report.get("audited_case_count"), expected=CASE_COUNT)
        or not is_exact_int(report.get("passed_case_count"), expected=CASE_COUNT)
        or report.get("case_order") != expected_order
        or report.get("case_order_sha256") != canonical_sha256(expected_order)
        or report.get("errors") != []
        or report.get("warnings") != []
        or report.get("deterministic_gate_passed") is not True
        or report.get("freeze_authorized") is not False
        or len(report.get("cases") or []) != CASE_COUNT
        or [row.get("case_unit_id") for row in report.get("cases") or []]
        != expected_order
        or any(row.get("status") != "pass" for row in report.get("cases") or [])
    ):
        raise SemanticReviewV7Error(
            "fresh draft QC is not a warning-free exact 116/116 pass"
        )
    return report, binding


def load_packet_index() -> tuple[dict[str, Any], list[str], list[dict[str, Any]]]:
    index = load_json(PACKET_INDEX, "candidate116 packet index")
    items = list(index.get("items") or [])
    order = [require_case_id(row.get("case_unit_id")) for row in items]
    if (
        index.get("schema_version") != "androidworld_candidate116_packet_index/v1"
        or not is_exact_int(index.get("candidate_count"), expected=CASE_COUNT)
        or len(items) != CASE_COUNT
        or len(set(order)) != CASE_COUNT
        or any(
            not is_exact_int(row.get("selection_rank"), expected=rank)
            for rank, row in enumerate(items)
        )
        or any(row.get("task_id") != row.get("case_unit_id") for row in items)
    ):
        raise SemanticReviewV7Error(
            "candidate116 packet index identity/order is invalid"
        )
    return index, order, items


def _source_binding_core(
    binding: Mapping[str, Any], *, label: str, extra_fields: tuple[str, ...] = ()
) -> dict[str, Any]:
    if not isinstance(binding, Mapping) or set(binding) != (
        SOURCE_REGULAR_BINDING_FIELDS | set(extra_fields)
    ):
        raise SemanticReviewV7Error(f"{label} source binding schema is not exact")
    core = {field: binding[field] for field in SOURCE_REGULAR_BINDING_FIELDS}
    try:
        source_common.read_regular_bytes_bound(
            Path(str(core["path"])), label=label, expected_binding=core
        )
    except BaseException as exc:
        raise SemanticReviewV7Error(f"{label} source binding differs: {exc}") from exc
    return core


def _load_source_bound_json(
    binding: Mapping[str, Any],
    *,
    label: str,
    self_hash_field: str,
    extra_fields: tuple[str, ...] = (),
) -> tuple[dict[str, Any], dict[str, Any]]:
    core = _source_binding_core(binding, label=label, extra_fields=extra_fields)
    try:
        payload, _observed = source_common.read_regular_bytes_bound(
            Path(core["path"]), label=label, expected_binding=core
        )
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SemanticReviewV7Error(f"cannot decode {label}: {exc}") from exc
    except BaseException as exc:
        raise SemanticReviewV7Error(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise SemanticReviewV7Error(f"{label} is not a JSON object")
    verify_self_hash(value, self_hash_field, label)
    for field in extra_fields:
        if binding.get(field) != value.get(field):
            raise SemanticReviewV7Error(
                f"{label} outer {field} differs from the bound document"
            )
    return value, core


def _automatic_generation_receipt_rows(
    automatic_qc: Mapping[str, Any], expected_order: list[str]
) -> dict[str, Mapping[str, Any]]:
    rows = list(automatic_qc.get("case_receipts") or [])
    observed = [row.get("case_unit_id") for row in rows if isinstance(row, Mapping)]
    if (
        not is_exact_int(automatic_qc.get("case_count"), expected=CASE_COUNT)
        or len(rows) != CASE_COUNT
        or len(observed) != CASE_COUNT
        or observed != expected_order
        or len(set(observed)) != CASE_COUNT
        or automatic_qc.get("case_receipts_sha256") != canonical_sha256(rows)
    ):
        raise SemanticReviewV7Error(
            "automatic generation QC lacks the exact ordered 116 case receipts"
        )
    return {require_case_id(row["case_unit_id"]): row for row in rows}


def _qc_output_hash(outputs: Mapping[str, Any]) -> str:
    minimal: dict[str, dict[str, Any]] = {}
    for name in GENERATION_OUTPUT_NAMES:
        binding = outputs.get(name)
        if not isinstance(binding, Mapping):
            raise SemanticReviewV7Error(f"generation output binding missing: {name}")
        minimal[name] = {
            "sha256": binding.get("sha256"),
            "size_bytes": binding.get("size_bytes"),
        }
    return canonical_sha256(minimal)


def verify_generation_document_chain(
    *,
    generation_prelock_path: Path,
    generation_prelock: Mapping[str, Any],
    generation_receipt_path: Path,
    generation_receipt: Mapping[str, Any],
    raw_draft_root: Path,
    expected_order: list[str],
    deterministic_qc: Mapping[str, Any],
) -> tuple[dict[str, Mapping[str, Any]], dict[str, Any]]:
    """Bind prelock -> config -> receipt -> automatic QC -> exact case outputs.

    The top-level generation receipt intentionally contains only a binding to
    ``_automatic_generation_qc.json``.  Treating it as if it directly contained
    ``case_receipts`` would silently accept an empty/nonexistent chain, so the
    nested document is loaded and independently re-bound here.
    """

    generation_id = source_common.GENERATION_ID
    packet_inputs = list(generation_prelock.get("packet_inputs") or [])
    if (
        generation_prelock.get("schema_version") != source_common.PRELOCK_SCHEMA
        or generation_prelock.get("status") != "frozen_before_first_model_call"
        or generation_prelock.get("generation_id") != generation_id
        or not is_exact_int(
            generation_prelock.get("case_count"), expected=CASE_COUNT
        )
        or generation_prelock.get("case_order") != expected_order
        or generation_prelock.get("case_order_sha256")
        != canonical_sha256(expected_order)
        or len(packet_inputs) != CASE_COUNT
        or [row.get("case_unit_id") for row in packet_inputs] != expected_order
        or any(
            not is_exact_int(row.get("selection_rank"), expected=rank)
            or row.get("task_id") != case_id
            for rank, (case_id, row) in enumerate(
                zip(expected_order, packet_inputs, strict=True)
            )
        )
        or generation_prelock.get("packet_inputs_sha256")
        != canonical_sha256(packet_inputs)
        or generation_prelock.get("freeze_authorized") is not False
    ):
        raise SemanticReviewV7Error("fresh generation prelock identity is not exact")
    packet_by_case = {str(row["case_unit_id"]): row for row in packet_inputs}

    config, config_binding = _load_source_bound_json(
        generation_prelock.get("draft_config") or {},
        label="fresh generation config",
        self_hash_field="config_sha256",
        extra_fields=("config_sha256",),
    )
    raw_root = raw_draft_root.absolute()
    if raw_root.resolve(strict=True) != raw_root:
        raise SemanticReviewV7Error("raw draft root is not a lexical canonical path")
    if (
        config.get("schema_version") != source_common.CONFIG_SCHEMA
        or config.get("status") != "prelocked_before_first_model_call"
        or config.get("generation_id") != generation_id
        or config.get("model") != MODEL
        or config.get("reasoning_effort") != REASONING_EFFORT
        or not is_exact_int(config.get("max_parallel"), expected=PARALLELISM)
        or not is_exact_int(config.get("large_max_parallel"), expected=PARALLELISM)
        or config.get("token_budgets") != [32_000]
        or Path(str(config.get("output_root_absolute") or "")) != raw_root
    ):
        raise SemanticReviewV7Error("fresh generation config identity is not exact")

    receipt_path = generation_receipt_path.absolute()
    expected_receipt_path = raw_root / "_generation_receipt.json"
    if receipt_path != expected_receipt_path:
        raise SemanticReviewV7Error(
            "generation receipt is not the exact receipt inside raw draft root"
        )
    if (
        generation_receipt.get("schema_version") != GENERATION_RECEIPT_SCHEMA
        or generation_receipt.get("status")
        != "generation_complete_unfrozen_automatic_qc_pass_116_of_116"
        or generation_receipt.get("generation_id") != generation_id
        or generation_receipt.get("prelock_sha256")
        != generation_prelock.get("prelock_sha256")
        or generation_receipt.get("config_sha256") != config.get("config_sha256")
        or not is_exact_int(generation_receipt.get("case_count"), expected=CASE_COUNT)
        or generation_receipt.get("freeze_authorized") is not False
    ):
        raise SemanticReviewV7Error("fresh generation receipt identity is not exact")

    automatic_qc_binding = generation_receipt.get("automatic_generation_qc") or {}
    automatic_qc, automatic_qc_core = _load_source_bound_json(
        automatic_qc_binding,
        label="automatic generation QC",
        self_hash_field="audit_sha256",
        extra_fields=("audit_sha256",),
    )
    if Path(automatic_qc_core["path"]) != raw_root / "_automatic_generation_qc.json":
        raise SemanticReviewV7Error(
            "generation receipt automatic-QC path escapes the raw draft root"
        )
    if (
        automatic_qc.get("schema_version") != GENERATION_QC_SCHEMA
        or automatic_qc.get("status")
        != "automatic_generation_qc_pass_116_of_116"
        or automatic_qc.get("freeze_authorized") is not False
    ):
        raise SemanticReviewV7Error("automatic generation QC status is not exact")
    receipt_by_case = _automatic_generation_receipt_rows(
        automatic_qc, expected_order
    )

    deterministic_rows = list(deterministic_qc.get("cases") or [])
    if [row.get("case_unit_id") for row in deterministic_rows] != expected_order:
        raise SemanticReviewV7Error(
            "deterministic QC order differs from automatic generation receipts"
        )
    deterministic_by_case = {
        str(row["case_unit_id"]): row for row in deterministic_rows
    }
    exact_receipt_row_fields = {
        "case_unit_id",
        "task_id",
        "packet",
        "outputs",
        "deterministic_schema_guardrail_qc",
        "codex_provenance_qc",
        "staged_source_coverage_qc",
        "coverage_receipt_sha256",
        "requirements_sha256",
        "reader_operation_expectations_sha256",
    }
    for case_id in expected_order:
        row = receipt_by_case[case_id]
        if set(row) != exact_receipt_row_fields:
            raise SemanticReviewV7Error(
                f"{case_id} automatic generation receipt row schema is not exact"
            )
        packet_binding = row.get("packet") or {}
        _source_binding_core(packet_binding, label=f"{case_id} generation packet")
        if canonical_sha256(packet_binding) != canonical_sha256(
            packet_by_case[case_id].get("packet") or {}
        ):
            raise SemanticReviewV7Error(
                f"{case_id} generation receipt packet differs from prelock"
            )
        outputs = row.get("outputs") or {}
        if not isinstance(outputs, Mapping) or set(outputs) != set(
            GENERATION_OUTPUT_NAMES
        ):
            raise SemanticReviewV7Error(
                f"{case_id} generation output namespace is not exact"
            )
        for name in GENERATION_OUTPUT_NAMES:
            output_binding = outputs[name]
            core = _source_binding_core(
                output_binding, label=f"{case_id}/{name} generation output"
            )
            if Path(core["path"]) != raw_root / case_id / name:
                raise SemanticReviewV7Error(
                    f"{case_id}/{name} generation output path is not root-bound"
                )
        deterministic_row = deterministic_by_case[case_id]
        if (
            row.get("task_id") != case_id
            or row.get("deterministic_schema_guardrail_qc") != "pass"
            or row.get("codex_provenance_qc") != "pass"
            or row.get("staged_source_coverage_qc") != "pass"
            or deterministic_row.get("status") != "pass"
            or deterministic_row.get("task_id") != case_id
            or deterministic_row.get("packet_sha256")
            != packet_binding.get("sha256")
            or deterministic_row.get("coverage_requirements_sha256")
            != row.get("requirements_sha256")
            or deterministic_row.get("checklist_sha256")
            != outputs["checklist.json"].get("sha256")
            or deterministic_row.get("outputs_sha256") != _qc_output_hash(outputs)
        ):
            raise SemanticReviewV7Error(
                f"{case_id} independent deterministic QC is not bound to exact outputs"
            )

    for name in ("native_batch_summary", "native_batch_results"):
        _source_binding_core(
            automatic_qc.get(name) or {}, label=f"automatic generation QC {name}"
        )

    cleanup_path = raw_root / "_runtime_cleanup_receipt.json"
    cleanup, cleanup_binding = load_hashed_document_bound(
        cleanup_path,
        "cleanup_receipt_sha256",
        "fresh generation runtime cleanup receipt",
    )
    cleanup_generation_binding = cleanup.get("generation_receipt") or {}
    _source_binding_core(
        cleanup_generation_binding, label="cleanup-bound generation receipt"
    )
    if (
        cleanup.get("schema_version")
        != "androidworld_candidate116_authorized_runtime_cleanup/v6_clean5_hardened"
        or cleanup.get("status") != "pass"
        or cleanup.get("auth_content_or_hash_recorded") is not False
        or cleanup.get("all_paths_absent") is not True
        or cleanup.get("generation_returned_success") is not True
        or cleanup.get("abort_incident") is not None
        or Path(str(cleanup_generation_binding.get("path") or "")) != receipt_path
        or cleanup_generation_binding.get("sha256")
        != generation_receipt.get("receipt_sha256")
        or len(cleanup.get("paths") or []) != 3
        or any(row.get("path_absent") is not True for row in cleanup.get("paths") or [])
    ):
        raise SemanticReviewV7Error(
            "fresh generation runtime cleanup is not a terminal exact success"
        )

    audit = add_self_hash(
        {
            "schema_version": "androidworld_candidate116_semantic_review_v7_generation_chain/v1",
            "status": "exact_prelock_config_receipt_automatic_qc_outputs_and_cleanup_bound",
            "generation_id": generation_id,
            "case_count": CASE_COUNT,
            "case_order": expected_order,
            "case_order_sha256": canonical_sha256(expected_order),
            "generation_prelock": regular_file_binding(generation_prelock_path),
            "generation_prelock_sha256": generation_prelock["prelock_sha256"],
            "generation_config_source_binding": config_binding,
            "generation_config_sha256": config["config_sha256"],
            "generation_receipt": regular_file_binding(receipt_path),
            "generation_receipt_sha256": generation_receipt["receipt_sha256"],
            "automatic_generation_qc_source_binding": automatic_qc_core,
            "automatic_generation_qc_sha256": automatic_qc["audit_sha256"],
            "case_receipts_sha256": automatic_qc["case_receipts_sha256"],
            "runtime_cleanup_receipt": cleanup_binding,
            "runtime_cleanup_receipt_sha256": cleanup["cleanup_receipt_sha256"],
            "freeze_authorized": False,
        },
        "generation_chain_sha256",
    )
    return receipt_by_case, audit


def _verify_receipt_checklist_binding(
    *, case_id: str, row: Mapping[str, Any], checklist_path: Path
) -> None:
    outputs = row.get("outputs") or {}
    binding = outputs.get("checklist.yaml") or outputs.get("checklist_yaml")
    if not isinstance(binding, Mapping):
        raise SemanticReviewV7Error(
            f"{case_id} generation receipt lacks checklist.yaml binding"
        )
    core = _source_binding_core(binding, label=f"{case_id} checklist.yaml")
    bound_path = Path(core["path"])
    if bound_path != checklist_path.resolve(strict=True):
        raise SemanticReviewV7Error(
            f"{case_id} generation receipt checklist binding differs"
        )


def codex_binding() -> dict[str, Any]:
    invocation_raw = shutil.which("codex")
    if not invocation_raw:
        raise SemanticReviewV7Error("codex is not on PATH")
    invocation = Path(os.path.abspath(invocation_raw))
    resolved = invocation.resolve(strict=True)
    if sha256_file(resolved) != CODEX_BINARY_SHA256:
        raise SemanticReviewV7Error(
            "Codex CLI binary hash differs from the reviewed toolchain"
        )
    version = subprocess.run(
        [str(resolved), "--version"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    login = subprocess.run(
        [str(resolved), "login", "status"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    version_text = (version.stdout or version.stderr).strip()
    login_text = "\n".join(
        part.strip() for part in (login.stdout, login.stderr) if part.strip()
    )
    if version.returncode != 0 or version_text != CODEX_VERSION:
        raise SemanticReviewV7Error(f"unexpected Codex version: {version_text!r}")
    if login.returncode != 0 or login_text != CODEX_LOGIN_STATUS:
        raise SemanticReviewV7Error(f"Codex login state is not exact: {login_text!r}")
    return {
        "invocation_path": str(invocation),
        "resolved_path": str(resolved),
        "sha256": CODEX_BINARY_SHA256,
        "size_bytes": resolved.stat().st_size,
        "version": version_text,
        "login_status_at_prelock": login_text,
        "auth_mode": "codex_login",
        "auth_content_or_hash_persisted": False,
    }


def create_snapshot(snapshot_root: Path) -> dict[str, Any]:
    if snapshot_root.is_symlink() or snapshot_root.exists():
        raise SemanticReviewV7Error(f"snapshot root must be absent: {snapshot_root}")
    files = {
        "scripts/semantic_review_v7_common.py": CANDIDATE_ROOT
        / "scripts"
        / "semantic_review_v7_common.py",
        "scripts/semantic_review_v7_staging.py": CANDIDATE_ROOT
        / "scripts"
        / "semantic_review_v7_staging.py",
        "scripts/wave004_v6_clean2_hardened_staging.py": CANDIDATE_ROOT
        / "scripts"
        / "wave004_v6_clean2_hardened_staging.py",
        "scripts/prepare_semantic_review_v7_prelock.py": SCRIPT,
        "scripts/run_semantic_review_v7_batch.py": CANDIDATE_ROOT
        / "scripts"
        / "run_semantic_review_v7_batch.py",
        "scripts/validate_semantic_review_v7_batch.py": CANDIDATE_ROOT
        / "scripts"
        / "validate_semantic_review_v7_batch.py",
        "prompts/androidworld_candidate116_semantic_review_v7.prompt.md": PROMPT,
        "schemas/androidworld_candidate116_semantic_review_v7.schema.json": OUTPUT_SCHEMA,
    }
    missing = [str(path) for path in files.values() if not path.is_file()]
    if missing:
        raise SemanticReviewV7Error(
            f"review toolchain snapshot sources are missing: {missing}"
        )
    snapshot_root.mkdir(parents=True, mode=0o700)
    rows: list[dict[str, Any]] = []
    try:
        for relative, source in sorted(files.items()):
            target = snapshot_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open("rb") as reader, target.open("xb") as writer:
                shutil.copyfileobj(reader, writer)
                writer.flush()
                os.fsync(writer.fileno())
            os.chmod(target, 0o444)
            row = regular_file_binding(target)
            row["relative_path"] = relative
            row["source_sha256"] = sha256_file(source)
            rows.append(row)
        manifest = add_self_hash(
            {
                "schema_version": "androidworld_candidate116_semantic_review_v7_toolchain_snapshot/v1",
                "status": "create_once_byte_frozen",
                "snapshot_root": str(snapshot_root.resolve(strict=True)),
                "file_count": len(rows),
                "files": rows,
                "files_sha256": canonical_sha256(rows),
            },
            "snapshot_sha256",
        )
        write_json_create_once(snapshot_root / "snapshot_manifest.json", manifest)
        for directory in sorted(
            (path for path in snapshot_root.rglob("*") if path.is_dir()),
            key=lambda path: len(path.parts),
            reverse=True,
        ):
            os.chmod(directory, 0o555)
        os.chmod(snapshot_root, 0o555)
        return manifest
    except BaseException:
        if snapshot_root.exists() and not snapshot_root.is_symlink():
            for path in [snapshot_root, *snapshot_root.rglob("*")]:
                try:
                    if path.is_dir():
                        os.chmod(path, 0o700)
                    elif path.is_file():
                        os.chmod(path, 0o600)
                except OSError:
                    pass
            shutil.rmtree(snapshot_root)
        raise


def _packet_operation_token_count(operation_expectations: Mapping[str, Any]) -> int:
    operations = list(operation_expectations.get("operations") or [])
    if not operations:
        raise SemanticReviewV7Error("packet reader B lacks ordered operations")
    total = 0
    for index, row in enumerate(operations):
        value = row.get("expected_full_output_o200k_tokens")
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise SemanticReviewV7Error(
                f"packet reader B operation {index} lacks exact output token count"
            )
        total += value
    return total


def build_capacity_and_inputs(
    *,
    items: list[dict[str, Any]],
    order: list[str],
    raw_draft_root: Path,
    checklist_schema: Mapping[str, Any],
    generation_receipt_rows: Mapping[str, Mapping[str, Any]],
    token_counter: Any,
    tokenizer_binding: Mapping[str, Any],
    base_prompt: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    receipt_by_case = dict(generation_receipt_rows)
    if list(receipt_by_case) != order:
        raise SemanticReviewV7Error(
            "generation receipt row order differs from candidate116 order"
        )
    case_inputs: list[dict[str, Any]] = []
    capacity_rows: list[dict[str, Any]] = []
    for rank, (case_id, item) in enumerate(zip(order, items, strict=True)):
        packet_path = (
            REPOSITORY_ROOT / str(item.get("case_packet_path") or "")
        ).resolve(strict=True)
        if (
            packet_path.is_symlink()
            or sha256_file(packet_path) != item.get("case_packet_sha256")
            or item.get("task_id") != case_id
        ):
            raise SemanticReviewV7Error(f"{case_id} canonical packet binding differs")
        case_dir = raw_draft_root / case_id
        checklist_yaml_path = case_dir / "checklist.yaml"
        checklist_json_path = case_dir / "checklist.json"
        if (
            case_dir.is_symlink()
            or not case_dir.is_dir()
            or checklist_yaml_path.is_symlink()
            or checklist_json_path.is_symlink()
            or not checklist_yaml_path.is_file()
            or not checklist_json_path.is_file()
        ):
            raise SemanticReviewV7Error(
                f"{case_id} fresh draft checklist files are missing"
            )
        checklist = load_yaml(checklist_yaml_path, f"{case_id} checklist YAML")
        checklist_json = load_json(checklist_json_path, f"{case_id} checklist JSON")
        if checklist != checklist_json:
            raise SemanticReviewV7Error(f"{case_id} checklist YAML/JSON bodies differ")
        validate_json_schema(checklist, checklist_schema, f"{case_id} checklist")
        if (
            checklist.get("schema_version") != "case_checklist_v1"
            or checklist.get("case_unit_id") != case_id
            or checklist.get("task_id") != case_id
            or checklist.get("domain") != "androidworld"
        ):
            raise SemanticReviewV7Error(f"{case_id} checklist identity differs")
        _verify_receipt_checklist_binding(
            case_id=case_id,
            row=receipt_by_case[case_id],
            checklist_path=checklist_yaml_path,
        )
        packet_text = packet_path.read_text(encoding="utf-8")
        parsed = source_staging.parse_packet_sources(packet_text)
        requirements = source_staging.build_coverage_requirements(
            parsed, token_counter=token_counter, tokenizer_binding=tokenizer_binding
        )
        requirements["case_packet_sha256"] = sha256_text(packet_text)
        requirements["source_inventory"] = [
            {
                key: parsed["sources"][path][key]
                for key in ("path", "sha256", "size_bytes", "line_count")
            }
            for path in parsed["inventory"]
        ]
        requirements.pop("requirements_sha256", None)
        requirements["requirements_sha256"] = canonical_sha256(requirements)
        requirements_core = dict(requirements)
        claimed_requirements_sha = requirements_core.pop("requirements_sha256", None)
        if claimed_requirements_sha != canonical_sha256(requirements_core):
            raise SemanticReviewV7Error(
                f"{case_id} packet coverage A self-hash differs"
            )
        builder = getattr(source_staging, "build_reader_operation_expectations", None)
        if not callable(builder):
            raise SemanticReviewV7Error(
                "finalized packet reader A+B interface is unavailable"
            )
        packet_expectations = builder(
            case_packet_text=packet_text,
            parsed=parsed,
            requirements=requirements,
            token_counter=token_counter,
        )
        source_staging.verify_reader_operation_expectations_binding(
            requirements, packet_expectations
        )
        inventory = checklist_semantic_inventory(checklist)
        checklist_text = checklist_yaml_path.read_text(encoding="utf-8")
        review_expectations = review_staging.build_review_operation_expectations(
            packet_operation_expectations=packet_expectations,
            requirements=requirements,
            checklist_text=checklist_text,
            inventory=inventory,
            token_counter=token_counter,
        )
        manifest_stub = {
            "case_unit_id": case_id,
            "task_id": case_id,
            "checklist_sha256": sha256_text(checklist_text),
            "inventory_sha256": inventory["inventory_sha256"],
            "coverage_requirements": requirements,
            "packet_reader_operation_expectations": packet_expectations,
            "packet_reader_operation_expectations_sha256": review_staging._packet_expectations_hash(
                packet_expectations
            ),
            "review_operation_expectations_sha256": review_expectations[
                "review_operation_expectations_sha256"
            ],
        }
        prompt_text = review_staging.staged_review_prompt(
            base_prompt=base_prompt, manifest=manifest_stub
        )
        prompt_tokens = token_counter(prompt_text)
        packet_tokens = _packet_operation_token_count(packet_expectations)
        exact_checklist_reader_output = review_staging.render_checklist_output_for_audit(
            checklist_text=checklist_text,
            inventory=inventory,
            requirements_sha256=requirements["requirements_sha256"],
        )
        checklist_tokens = review_expectations["checklist_operation"][
            "expected_output_o200k_tokens"
        ]
        checklist_bytes = review_expectations["checklist_operation"][
            "expected_output_size_bytes"
        ]
        exact_checklist_reader_tokens = token_counter(exact_checklist_reader_output)
        exact_checklist_reader_bytes = len(
            exact_checklist_reader_output.encode("utf-8")
        )
        if (
            not is_exact_int(checklist_tokens, minimum=1)
            or not is_exact_int(checklist_bytes, minimum=1)
            or checklist_tokens != exact_checklist_reader_tokens
            or checklist_bytes != exact_checklist_reader_bytes
            or review_expectations["checklist_operation"].get(
                "expected_output_sha256"
            )
            != sha256_text(exact_checklist_reader_output)
        ):
            raise SemanticReviewV7Error(
                f"{case_id} checklist reader envelope is not an exact recomputation"
            )
        base_without_checklist_tokens = (
            prompt_tokens + packet_tokens + PROTOCOL_RESERVE_TOKENS
        )
        max_checklist_tokens_by_input_gate = (
            review_staging.MAX_STAGED_INPUT_TOKENS - base_without_checklist_tokens
        )
        max_checklist_tokens_by_total_gate = (
            review_staging.EFFECTIVE_CONTEXT_LIMIT
            - review_staging.MAX_OUTPUT_RESERVE_TOKENS
            - base_without_checklist_tokens
        )
        effective_max_checklist_tokens = min(
            review_staging.MAX_CHECKLIST_READER_TOKENS,
            max_checklist_tokens_by_input_gate,
            max_checklist_tokens_by_total_gate,
        )
        staged_input_tokens = base_without_checklist_tokens + checklist_tokens
        effective_total_tokens = (
            staged_input_tokens + review_staging.MAX_OUTPUT_RESERVE_TOKENS
        )
        input_gate_headroom = (
            review_staging.MAX_STAGED_INPUT_TOKENS - staged_input_tokens
        )
        total_gate_headroom = (
            review_staging.EFFECTIVE_CONTEXT_LIMIT - effective_total_tokens
        )
        if (
            effective_max_checklist_tokens < 0
            or checklist_tokens > effective_max_checklist_tokens
            or checklist_bytes > review_staging.MAX_CHECKLIST_READER_BYTES
            or staged_input_tokens > review_staging.MAX_STAGED_INPUT_TOKENS
            or effective_total_tokens > review_staging.EFFECTIVE_CONTEXT_LIMIT
            or input_gate_headroom < 0
            or total_gate_headroom < 0
        ):
            raise SemanticReviewV7Error(
                f"{case_id} review context capacity is unsafe: {staged_input_tokens}"
            )
        case_input = add_self_hash(
            {
                "selection_rank": rank,
                "case_unit_id": case_id,
                "task_id": case_id,
                "packet": regular_file_binding(packet_path),
                "checklist_yaml": regular_file_binding(checklist_yaml_path),
                "checklist_json": regular_file_binding(checklist_json_path),
                "checklist_semantic_sha256": canonical_sha256(checklist),
                "semantic_inventory_sha256": inventory["inventory_sha256"],
                "coverage_requirements_sha256": requirements["requirements_sha256"],
                "packet_reader_operation_expectations_sha256": review_staging._packet_expectations_hash(
                    packet_expectations
                ),
                "review_operation_expectations_sha256": review_expectations[
                    "review_operation_expectations_sha256"
                ],
                "generation_receipt_row_sha256": canonical_sha256(
                    receipt_by_case[case_id]
                ),
            },
            "case_input_sha256",
        )
        capacity_row = {
            "selection_rank": rank,
            "case_unit_id": case_id,
            "requirements": requirements,
            "packet_reader_operation_expectations": packet_expectations,
            "semantic_inventory": inventory,
            "review_operation_expectations": review_expectations,
            "prompt_sha256": sha256_text(prompt_text),
            "actual_frozen_draft": regular_file_binding(checklist_yaml_path),
            "actual_frozen_draft_sha256": sha256_text(checklist_text),
            "actual_frozen_draft_size_bytes": len(checklist_text.encode("utf-8")),
            "actual_frozen_draft_o200k_tokens": token_counter(checklist_text),
            "actual_frozen_draft_reader_output_sha256": sha256_text(
                exact_checklist_reader_output
            ),
            "frozen_checklist_yaml_size_bytes": checklist_yaml_path.stat().st_size,
            "frozen_checklist_yaml_o200k_tokens": token_counter(checklist_text),
            "prompt_o200k_tokens": prompt_tokens,
            "packet_reader_output_o200k_tokens": packet_tokens,
            "checklist_reader_output_o200k_tokens": checklist_tokens,
            "checklist_reader_output_size_bytes": checklist_bytes,
            "max_checklist_reader_output_size_bytes": review_staging.MAX_CHECKLIST_READER_BYTES,
            "max_checklist_reader_output_o200k_tokens_hard": review_staging.MAX_CHECKLIST_READER_TOKENS,
            "base_without_checklist_o200k_tokens": base_without_checklist_tokens,
            "max_checklist_o200k_tokens_by_210000_input_gate": max_checklist_tokens_by_input_gate,
            "max_checklist_o200k_tokens_by_258400_total_gate": max_checklist_tokens_by_total_gate,
            "effective_max_checklist_reader_output_o200k_tokens": effective_max_checklist_tokens,
            "capacity_basis": "actual_frozen_checklist_and_inventory_reader_output_exact_o200k_count",
            "protocol_reserve_o200k_tokens": PROTOCOL_RESERVE_TOKENS,
            "staged_input_o200k_tokens": staged_input_tokens,
            "max_staged_input_o200k_tokens_gate": review_staging.MAX_STAGED_INPUT_TOKENS,
            "staged_input_gate_headroom_o200k_tokens": input_gate_headroom,
            "staged_input_gate_passed": True,
            "reserved_output_o200k_tokens": review_staging.MAX_OUTPUT_RESERVE_TOKENS,
            "effective_total_with_output_reserve_o200k_tokens": effective_total_tokens,
            "effective_context_limit_o200k_tokens": review_staging.EFFECTIVE_CONTEXT_LIMIT,
            "remaining_context_margin_o200k_tokens": total_gate_headroom,
            "effective_total_gate_passed": True,
            "actual_frozen_draft_capacity_gate_passed": True,
        }
        capacity_row["capacity_row_sha256"] = canonical_sha256(capacity_row)
        case_inputs.append(case_input)
        capacity_rows.append(capacity_row)
    capacity = add_self_hash(
        {
            "schema_version": "androidworld_candidate116_semantic_review_v7_capacity/v1",
            "status": "all_116_fit_frozen_o200k_context_with_output_reserve",
            "case_count": CASE_COUNT,
            "case_order": order,
            "case_order_sha256": canonical_sha256(order),
            "tokenizer_binding": dict(tokenizer_binding),
            "cases": capacity_rows,
            "cases_sha256": canonical_sha256(capacity_rows),
            "actual_frozen_draft_case_count": len(capacity_rows),
            "actual_frozen_draft_capacity_pass_count": sum(
                row["actual_frozen_draft_capacity_gate_passed"] is True
                for row in capacity_rows
            ),
            "all_actual_frozen_drafts_pass_both_exact_gates": all(
                row["staged_input_gate_passed"] is True
                and row["effective_total_gate_passed"] is True
                and row["actual_frozen_draft_capacity_gate_passed"] is True
                for row in capacity_rows
            ),
            "max_staged_input_o200k_tokens": max(
                row["staged_input_o200k_tokens"] for row in capacity_rows
            ),
            "max_effective_total_with_output_reserve_o200k_tokens": max(
                row["effective_total_with_output_reserve_o200k_tokens"]
                for row in capacity_rows
            ),
            "minimum_remaining_context_margin_o200k_tokens": min(
                row["remaining_context_margin_o200k_tokens"] for row in capacity_rows
            ),
            "minimum_max_checklist_o200k_tokens_by_210000_input_gate": min(
                row["max_checklist_o200k_tokens_by_210000_input_gate"]
                for row in capacity_rows
            ),
            "minimum_max_checklist_o200k_tokens_by_258400_total_gate": min(
                row["max_checklist_o200k_tokens_by_258400_total_gate"]
                for row in capacity_rows
            ),
            "minimum_effective_max_checklist_reader_output_o200k_tokens": min(
                row["effective_max_checklist_reader_output_o200k_tokens"]
                for row in capacity_rows
            ),
            "capacity_basis": "actual_frozen_checklist_and_inventory_reader_output_exact_o200k_count",
            "output_reserve_o200k_tokens": review_staging.MAX_OUTPUT_RESERVE_TOKENS,
            "effective_context_limit_o200k_tokens": review_staging.EFFECTIVE_CONTEXT_LIMIT,
        },
        "capacity_sha256",
    )
    if (
        not is_exact_int(
            capacity.get("actual_frozen_draft_case_count"), expected=CASE_COUNT
        )
        or not is_exact_int(
            capacity.get("actual_frozen_draft_capacity_pass_count"),
            expected=CASE_COUNT,
        )
        or capacity.get("all_actual_frozen_drafts_pass_both_exact_gates") is not True
    ):
        raise SemanticReviewV7Error(
            "actual frozen draft capacity is not an exact 116/116 two-gate pass"
        )
    return case_inputs, capacity


def planned_paths(args: argparse.Namespace, review_id: str) -> dict[str, Path]:
    return {
        "snapshot": (
            args.snapshot_root or REVIEW_BASE / "toolchain" / review_id
        ).resolve(),
        "capacity": (
            args.capacity_out or REVIEW_BASE / "capacity" / f"{review_id}.json"
        ).resolve(),
        "config": (
            args.config_out or REVIEW_BASE / "config" / f"{review_id}.json"
        ).resolve(),
        "prelock": (
            args.prelock_out or REVIEW_BASE / "freeze" / f"{review_id}.prelock.json"
        ).resolve(),
        "output": (args.output_root or REVIEW_BASE / "waves" / review_id).resolve(),
    }


def main() -> int:
    args = parse_args()
    review_id = require_safe_review_id(args.review_id)
    if (
        args.model != MODEL
        or args.reasoning_effort != REASONING_EFFORT
        or args.max_parallel != PARALLELISM
        or args.timeout_seconds < 600
    ):
        raise SemanticReviewV7Error(
            "review model/reasoning/exact-six/timeout settings differ"
        )
    if sys.version_info[:2] != (3, 12):
        raise SemanticReviewV7Error(
            "prelock must run under the bound Python 3.12 environment"
        )
    paths = planned_paths(args, review_id)
    for label, path in paths.items():
        if path.is_symlink() or path.exists():
            raise SemanticReviewV7Error(
                f"planned {label} namespace must be absent: {path}"
            )
    raw_root = args.raw_draft_root.resolve(strict=True)
    if raw_root.is_symlink() or not raw_root.is_dir():
        raise SemanticReviewV7Error("raw draft root is missing/symlinked")
    index, order, items = load_packet_index()
    generation_prelock_path = args.draft_generation_prelock.absolute()
    generation_prelock, generation_prelock_file_binding = load_hashed_document_bound(
        generation_prelock_path,
        "prelock_sha256",
        "fresh draft generation prelock",
    )
    generation_receipt_path = args.draft_generation_receipt.absolute()
    generation_receipt, generation_receipt_file_binding = load_hashed_document_bound(
        generation_receipt_path,
        "receipt_sha256",
        "fresh draft generation receipt",
    )
    qc_report_path = args.draft_qc_report.absolute()
    qc_report, qc_report_file_binding = verify_qc_report(qc_report_path, order)
    generation_receipt_rows, generation_chain = verify_generation_document_chain(
        generation_prelock_path=generation_prelock_path,
        generation_prelock=generation_prelock,
        generation_receipt_path=generation_receipt_path,
        generation_receipt=generation_receipt,
        raw_draft_root=raw_root,
        expected_order=order,
        deterministic_qc=qc_report,
    )
    checklist_schema_path = args.checklist_schema.resolve(strict=True)
    checklist_schema = load_json(checklist_schema_path, "adapted checklist schema")
    Draft202012Validator.check_schema(checklist_schema)
    output_schema = load_json(OUTPUT_SCHEMA, "semantic review v7 output schema")
    Draft202012Validator.check_schema(output_schema)
    prompt_text = PROMPT.read_text(encoding="utf-8")
    if (
        "Never emit a revised" not in prompt_text
        or "every expected support occurrence" not in prompt_text
    ):
        raise SemanticReviewV7Error(
            "semantic review v7 prompt hard policies are missing"
        )
    tokenizer_root = args.tokenizer_root.resolve(strict=True)
    tokenizer_cache = args.tokenizer_cache.resolve(strict=True)
    token_counter, tokenizer_binding = source_staging.load_frozen_o200k_token_counter(
        tokenizer_root=tokenizer_root, merge_table_path=tokenizer_cache
    )
    case_inputs, capacity = build_capacity_and_inputs(
        items=items,
        order=order,
        raw_draft_root=raw_root,
        checklist_schema=checklist_schema,
        generation_receipt_rows=generation_receipt_rows,
        token_counter=token_counter,
        tokenizer_binding=tokenizer_binding,
        base_prompt=prompt_text,
    )
    raw_draft_tree = exact_tree(raw_root)

    source_authority_bindings = {
        "generation prelock": generation_prelock_file_binding,
        "generation receipt": generation_receipt_file_binding,
        "deterministic draft QC": qc_report_file_binding,
        "generation config": generation_chain["generation_config_source_binding"],
        "automatic generation QC": generation_chain[
            "automatic_generation_qc_source_binding"
        ],
        "generation runtime cleanup": generation_chain[
            "runtime_cleanup_receipt"
        ],
    }

    def revalidate_generation_authorities() -> None:
        for label, binding in source_authority_bindings.items():
            try:
                source_common.read_regular_bytes_bound(
                    Path(str(binding["path"])),
                    label=label,
                    expected_binding=binding,
                )
            except BaseException as exc:
                raise SemanticReviewV7Error(
                    f"{label} changed after capacity binding: {exc}"
                ) from exc
        if canonical_sha256(exact_tree(raw_root)) != canonical_sha256(raw_draft_tree):
            raise SemanticReviewV7Error(
                "raw fresh-draft tree changed after exact capacity binding"
            )

    revalidate_generation_authorities()
    codex = codex_binding()
    real_home = Path.home().resolve(strict=True)
    original_codex_home = Path(
        os.environ.get("CODEX_HOME") or real_home / ".codex"
    ).resolve(strict=True)
    auth_json = original_codex_home / "auth.json"
    if auth_json.is_symlink() or not auth_json.is_file():
        raise SemanticReviewV7Error("Codex login auth.json is missing/symlinked")
    temp_base = Path(tempfile.gettempdir()).resolve(strict=True)
    runtime_stem = f"androidworld-semantic-review-v7-{review_id}"
    runtime_paths = {
        "auth_home": temp_base / f"{runtime_stem}-auth",
        "isolated_home": temp_base / f"{runtime_stem}-home",
        "review_tmp_root": temp_base / f"{runtime_stem}-tmp",
    }
    if len(set(runtime_paths.values())) != 3 or any(
        path.exists() or path.is_symlink() for path in runtime_paths.values()
    ):
        raise SemanticReviewV7Error(
            "planned isolated auth/HOME/TMP roots are not fresh/distinct"
        )

    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry_run_pass_no_files_written_no_model_calls",
                    "case_count": len(case_inputs),
                    "max_staged_input_o200k_tokens": capacity[
                        "max_staged_input_o200k_tokens"
                    ],
                    "minimum_remaining_context_margin_o200k_tokens": capacity[
                        "minimum_remaining_context_margin_o200k_tokens"
                    ],
                    "minimum_effective_max_checklist_reader_output_o200k_tokens": capacity[
                        "minimum_effective_max_checklist_reader_output_o200k_tokens"
                    ],
                    "freeze_authorized": False,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    revalidate_generation_authorities()
    snapshot = create_snapshot(paths["snapshot"])
    revalidate_generation_authorities()
    write_json_create_once(paths["capacity"], capacity)
    python_binary = Path(sys.executable).resolve(strict=True)
    child_environment = {
        "CODEX_HOME": str(runtime_paths["auth_home"]),
        "HOME": str(runtime_paths["isolated_home"]),
        "TMPDIR": str(runtime_paths["review_tmp_root"]),
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TZ": "UTC",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
    }
    config = add_self_hash(
        {
            "schema_version": CONFIG_SCHEMA,
            "status": "prelocked_no_model_calls",
            "review_id": review_id,
            "provider": "codex_cli",
            "auth_mode": "codex_login",
            "model": MODEL,
            "model_version": MODEL,
            "reasoning_effort": REASONING_EFFORT,
            "model_verbosity": "low",
            "max_parallel": PARALLELISM,
            "required_peak_parallel": PARALLELISM,
            "case_count": CASE_COUNT,
            "timeout_seconds": args.timeout_seconds,
            "repository_root": str(REPOSITORY_ROOT.resolve(strict=True)),
            "candidate_root": str(CANDIDATE_ROOT.resolve(strict=True)),
            "raw_draft_root": str(raw_root),
            "raw_draft_tree": raw_draft_tree,
            "generation_chain": generation_chain,
            "output_root": str(paths["output"]),
            "snapshot_root": str(paths["snapshot"]),
            "snapshot_manifest": regular_file_binding(
                paths["snapshot"] / "snapshot_manifest.json"
            ),
            "snapshot_sha256": snapshot["snapshot_sha256"],
            "capacity": regular_file_binding(paths["capacity"]),
            "capacity_sha256": capacity["capacity_sha256"],
            "codex_cli": codex,
            "python_runtime": regular_file_binding(python_binary),
            "tokenizer_root": exact_tree(tokenizer_root),
            "tokenizer_cache": regular_file_binding(tokenizer_cache),
            "original_codex_home": str(original_codex_home),
            "real_home": str(real_home),
            "isolated_runtime_roots": {
                key: str(path) for key, path in runtime_paths.items()
            },
            "child_environment": child_environment,
            "permission_profile": {
                "name": review_staging.PROFILE_NAME,
                "workspace_access": "read",
                "repository_access": "deny",
                "auth_home_access": "deny_inside_model_sandbox",
                "network_enabled": False,
            },
            "disabled_codex_features": list(review_staging.DISABLED_CODEX_FEATURES),
            "codex_exec_contract": {
                "global_prefix": ["-a", "never", "--strict-config", "exec"],
                "working_directory_flag": "--cd",
                "ephemeral": True,
                "ignore_user_config": True,
                "ignore_rules": True,
                "approval_policy": "never",
                "model": MODEL,
                "reasoning_effort": REASONING_EFFORT,
                "model_verbosity": "low",
                "web_search": "disabled",
                "mcp_servers": {},
                "shell_environment_inherit": "none",
                "permission_profile": review_staging.PROFILE_NAME,
                "permission_workspace_access": "read",
                "permission_network_enabled": False,
                "disabled_features": list(review_staging.DISABLED_CODEX_FEATURES),
                "forbidden_flags": [
                    "--sandbox",
                    "-s",
                    "--add-dir",
                    "--search",
                    "--dangerously-bypass-approvals-and-sandbox",
                ],
                "json_events": True,
                "structured_output": True,
                "prompt_transport": "stdin",
                "output_filename": "review_body.json",
            },
            "external_codex_exec_required_at_launch": 0,
            "auth_copy_policy": {
                "copy_only_after_launch_approval_and_zero_foreign_codex": True,
                "namespace": ["auth.json"],
                "directory_mode": 0o700,
                "file_mode": 0o600,
                "content_or_hash_must_never_be_persisted": True,
                "terminal_cleanup_required": True,
            },
            "freeze_authorized": False,
        },
        "config_sha256",
    )
    revalidate_generation_authorities()
    write_json_create_once(paths["config"], config)
    prelock = add_self_hash(
        {
            "schema_version": PRELOCK_SCHEMA,
            "status": "prelocked_waiting_independent_launch_approval",
            "review_id": review_id,
            "case_count": CASE_COUNT,
            "case_order": order,
            "case_order_sha256": canonical_sha256(order),
            "case_inputs": case_inputs,
            "case_inputs_sha256": canonical_sha256(case_inputs),
            "packet_index": regular_file_binding(PACKET_INDEX),
            "packet_index_semantic_sha256": canonical_sha256(index),
            "raw_draft_tree": raw_draft_tree,
            "generation_chain": generation_chain,
            "draft_generation_prelock": regular_file_binding(
                generation_prelock_path
            ),
            "draft_generation_prelock_sha256": generation_prelock["prelock_sha256"],
            "draft_generation_receipt": regular_file_binding(
                generation_receipt_path
            ),
            "draft_generation_receipt_sha256": generation_receipt["receipt_sha256"],
            "draft_qc_report": regular_file_binding(
                qc_report_path
            ),
            "draft_qc_report_sha256": qc_report["report_sha256"],
            "adapted_checklist_schema": regular_file_binding(checklist_schema_path),
            "review_config": regular_file_binding(paths["config"]),
            "review_config_sha256": config["config_sha256"],
            "review_capacity": regular_file_binding(paths["capacity"]),
            "review_capacity_sha256": capacity["capacity_sha256"],
            "review_toolchain_snapshot": regular_file_binding(
                paths["snapshot"] / "snapshot_manifest.json"
            ),
            "review_toolchain_snapshot_sha256": snapshot["snapshot_sha256"],
            "model_call_count": 0,
            "review_output_count": 0,
            "canonical_draft_write_count": 0,
            "canonical_contract_write_count": 0,
            "freeze_authorized": False,
            "launch_requires": [
                "independent post-prelock root audit",
                "create-once launch approval bound to this prelock/config/snapshot/capacity",
                "fresh external codex exec process count exactly zero",
            ],
        },
        "prelock_sha256",
    )
    revalidate_generation_authorities()
    write_json_create_once(paths["prelock"], prelock)
    print(
        json.dumps(
            {
                "status": prelock["status"],
                "case_count": CASE_COUNT,
                "prelock": str(paths["prelock"]),
                "prelock_sha256": prelock["prelock_sha256"],
                "config_sha256": config["config_sha256"],
                "capacity_sha256": capacity["capacity_sha256"],
                "snapshot_sha256": snapshot["snapshot_sha256"],
                "model_call_count": 0,
                "freeze_authorized": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SemanticReviewV7Error as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
