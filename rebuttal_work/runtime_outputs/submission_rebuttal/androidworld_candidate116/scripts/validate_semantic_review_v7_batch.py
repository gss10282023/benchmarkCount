#!/usr/bin/env python3
"""Independently validate all 116 semantic review v7 results; never freeze."""

from __future__ import annotations

import argparse
import json
import stat
import sys
from pathlib import Path
from typing import Any, Mapping

import semantic_review_v7_staging as review_staging
import wave004_v6_clean2_hardened_staging as source_staging
from semantic_review_v7_common import (
    CASE_COUNT,
    CONFIG_SCHEMA,
    DIMENSION_IDS,
    MODEL,
    PARALLELISM,
    PRELOCK_SCHEMA,
    REASONING_EFFORT,
    RECEIPT_SCHEMA,
    VALIDATION_SCHEMA,
    SemanticReviewV7Error,
    add_self_hash,
    canonical_bytes,
    canonical_sha256,
    checklist_semantic_inventory,
    covered_line_spans_from_requirements,
    ensure_no_sensitive_hash_fields,
    is_exact_int,
    load_json,
    load_yaml,
    parse_jsonl,
    regular_file_binding,
    sha256_text,
    validate_review_body,
    verify_actual_frozen_draft_capacity_row,
    verify_exact_tree,
    verify_regular_file_binding,
    verify_self_hash,
    write_json_create_once,
)

sys.dont_write_bytecode = True


class IndependentValidationError(SemanticReviewV7Error):
    """Raised when review outputs do not prove a strict 116/116 acceptance."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prelock", type=Path, required=True)
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args()


def verify_prelock_context(
    prelock_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], str]:
    if (
        prelock_path.is_symlink()
        or not prelock_path.is_file()
        or stat.S_IMODE(prelock_path.stat().st_mode) != 0o444
    ):
        raise IndependentValidationError("prelock is not a sealed 0444 regular file")
    prelock = load_json(prelock_path.resolve(strict=True), "semantic review v7 prelock")
    verify_self_hash(prelock, "prelock_sha256", "semantic review v7 prelock")
    order = list(prelock.get("case_order") or [])
    inputs = list(prelock.get("case_inputs") or [])
    if (
        prelock.get("schema_version") != PRELOCK_SCHEMA
        or not is_exact_int(prelock.get("case_count"), expected=CASE_COUNT)
        or len(order) != CASE_COUNT
        or len(set(order)) != CASE_COUNT
        or prelock.get("case_order_sha256") != canonical_sha256(order)
        or len(inputs) != CASE_COUNT
        or prelock.get("case_inputs_sha256") != canonical_sha256(inputs)
        or prelock.get("freeze_authorized") is not False
    ):
        raise IndependentValidationError("prelock case identity/order is invalid")
    config_path = verify_regular_file_binding(
        prelock.get("review_config") or {}, "semantic review config"
    )
    config = load_json(config_path, "semantic review config")
    verify_self_hash(config, "config_sha256", "semantic review config")
    if (
        config.get("schema_version") != CONFIG_SCHEMA
        or config.get("config_sha256") != prelock.get("review_config_sha256")
        or config.get("model") != MODEL
        or config.get("reasoning_effort") != REASONING_EFFORT
        or not is_exact_int(config.get("max_parallel"), expected=PARALLELISM)
        or not is_exact_int(config.get("case_count"), expected=CASE_COUNT)
        or config.get("freeze_authorized") is not False
    ):
        raise IndependentValidationError("semantic review config differs")
    python_path = verify_regular_file_binding(
        config.get("python_runtime") or {}, "semantic review Python runtime"
    )
    if python_path != Path(sys.executable).resolve(strict=True):
        raise IndependentValidationError(
            "validator Python runtime differs from prelock"
        )
    capacity_path = verify_regular_file_binding(
        prelock.get("review_capacity") or {}, "semantic review capacity"
    )
    capacity = load_json(capacity_path, "semantic review capacity")
    verify_self_hash(capacity, "capacity_sha256", "semantic review capacity")
    if (
        capacity.get("capacity_sha256") != prelock.get("review_capacity_sha256")
        or not is_exact_int(capacity.get("case_count"), expected=CASE_COUNT)
        or capacity.get("case_order") != order
        or len(capacity.get("cases") or []) != CASE_COUNT
        or capacity.get("cases_sha256") != canonical_sha256(capacity.get("cases") or [])
        or not is_exact_int(
            capacity.get("actual_frozen_draft_case_count"), expected=CASE_COUNT
        )
        or not is_exact_int(
            capacity.get("actual_frozen_draft_capacity_pass_count"),
            expected=CASE_COUNT,
        )
        or capacity.get("all_actual_frozen_drafts_pass_both_exact_gates") is not True
    ):
        raise IndependentValidationError("semantic review capacity differs")
    for case_id, input_row, capacity_row in zip(
        order, inputs, capacity.get("cases") or [], strict=True
    ):
        verify_actual_frozen_draft_capacity_row(
            capacity_row,
            label=f"{case_id} actual frozen draft capacity",
            max_staged_input_tokens=review_staging.MAX_STAGED_INPUT_TOKENS,
            max_output_reserve_tokens=review_staging.MAX_OUTPUT_RESERVE_TOKENS,
            effective_context_limit=review_staging.EFFECTIVE_CONTEXT_LIMIT,
            max_checklist_reader_tokens=review_staging.MAX_CHECKLIST_READER_TOKENS,
            max_checklist_reader_bytes=review_staging.MAX_CHECKLIST_READER_BYTES,
            protocol_reserve_tokens=8_000,
        )
        if (
            capacity_row.get("case_unit_id") != case_id
            or capacity_row.get("actual_frozen_draft")
            != input_row.get("checklist_yaml")
        ):
            raise IndependentValidationError(
                f"{case_id} actual frozen draft capacity binding differs"
            )
    verify_exact_tree(prelock.get("raw_draft_tree") or {}, "raw draft tree")
    verify_exact_tree(config.get("tokenizer_root") or {}, "frozen tokenizer root")
    verify_regular_file_binding(
        config.get("tokenizer_cache") or {}, "frozen tokenizer cache"
    )
    for label in (
        "packet_index",
        "draft_generation_prelock",
        "draft_generation_receipt",
        "draft_qc_report",
        "adapted_checklist_schema",
        "review_toolchain_snapshot",
    ):
        verify_regular_file_binding(prelock.get(label) or {}, label.replace("_", " "))
    snapshot_manifest_path = verify_regular_file_binding(
        prelock.get("review_toolchain_snapshot") or {}, "review toolchain snapshot"
    )
    snapshot = load_json(snapshot_manifest_path, "review toolchain snapshot")
    verify_self_hash(snapshot, "snapshot_sha256", "review toolchain snapshot")
    if snapshot.get("snapshot_sha256") != prelock.get(
        "review_toolchain_snapshot_sha256"
    ):
        raise IndependentValidationError("snapshot internal hash differs from prelock")
    snapshot_root = Path(str(snapshot.get("snapshot_root") or ""))
    snapshot_rows = list(snapshot.get("files") or [])
    if not is_exact_int(
        snapshot.get("file_count"), expected=len(snapshot_rows)
    ) or snapshot.get("files_sha256") != canonical_sha256(snapshot_rows):
        raise IndependentValidationError("snapshot exact file index is invalid")
    expected_relatives: set[str] = set()
    for row in snapshot_rows:
        relative = row.get("relative_path")
        if not isinstance(relative, str) or relative in expected_relatives:
            raise IndependentValidationError(
                "snapshot relative path is malformed/duplicated"
            )
        expected_relatives.add(relative)
        observed = regular_file_binding(snapshot_root / relative)
        for field in (
            "path",
            "repository_relative_path",
            "sha256",
            "size_bytes",
            "mode",
        ):
            if observed[field] != row.get(field):
                raise IndependentValidationError(
                    f"snapshot file changed: {relative}/{field}"
                )
    actual_relatives = {
        path.relative_to(snapshot_root).as_posix()
        for path in snapshot_root.rglob("*")
        if path.is_file() and path.name != "snapshot_manifest.json"
    }
    if actual_relatives != expected_relatives:
        raise IndependentValidationError("snapshot exact file namespace changed")
    if (
        Path(__file__).resolve(strict=True)
        != snapshot_root / "scripts" / "validate_semantic_review_v7_batch.py"
    ):
        raise IndependentValidationError(
            "independent validator must execute from the frozen review snapshot"
        )
    output_schema = load_json(
        snapshot_root
        / "schemas"
        / "androidworld_candidate116_semantic_review_v7.schema.json",
        "frozen semantic review output schema",
    )
    base_prompt = (
        snapshot_root
        / "prompts"
        / "androidworld_candidate116_semantic_review_v7.prompt.md"
    ).read_text(encoding="utf-8")
    ensure_no_sensitive_hash_fields(prelock)
    ensure_no_sensitive_hash_fields(config)
    return prelock, config, capacity, output_schema, base_prompt


def verify_concurrency_samples(
    path: Path, *, expected_order: list[str]
) -> dict[str, Any]:
    previous: str | None = None
    sequence = 0
    peak_live = 0
    peak_registered = 0
    covered: set[str] = set()
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise IndependentValidationError("concurrency sample chain is empty")
    for line in lines:
        try:
            sample = json.loads(line)
        except json.JSONDecodeError as exc:
            raise IndependentValidationError(
                f"malformed concurrency sample {sequence}"
            ) from exc
        if not isinstance(sample, dict):
            raise IndependentValidationError(
                f"concurrency sample {sequence} is not an object"
            )
        verify_self_hash(sample, "sample_sha256", f"concurrency sample {sequence}")
        active = list(sample.get("active_case_ids") or [])
        if (
            not is_exact_int(sample.get("sequence"), expected=sequence)
            or sample.get("previous_sample_sha256") != previous
            or sample.get("foreign_codex_exec_pids") != []
            or not is_exact_int(
                sample.get("active_registered_count"),
                expected=len(active),
                maximum=PARALLELISM,
            )
            or not is_exact_int(
                sample.get("active_live_codex_exec_count"),
                minimum=0,
                maximum=PARALLELISM,
            )
            or len(active) != len(set(active))
            or not set(active).issubset(set(expected_order))
        ):
            raise IndependentValidationError(
                f"concurrency sample invariant fails at {sequence}"
            )
        peak_registered = max(peak_registered, sample["active_registered_count"])
        peak_live = max(peak_live, sample["active_live_codex_exec_count"])
        covered.update(active)
        previous = sample["sample_sha256"]
        sequence += 1
    if (
        peak_registered != PARALLELISM
        or peak_live != PARALLELISM
        or covered != set(expected_order)
    ):
        raise IndependentValidationError(
            f"concurrency proof is not exact peak-six/all-116: {peak_registered}/{peak_live}/{len(covered)}"
        )
    return {
        "sample_count": sequence,
        "peak_registered": peak_registered,
        "peak_live_codex_exec": peak_live,
        "covered_case_count": len(covered),
        "tail_sample_sha256": previous,
    }


def validate_case(
    *,
    rank: int,
    case_id: str,
    input_row: Mapping[str, Any],
    capacity_row: Mapping[str, Any],
    result_row: Mapping[str, Any],
    review_root: Path,
    prelock: Mapping[str, Any],
    config: Mapping[str, Any],
    output_schema: Mapping[str, Any],
    base_prompt: str,
    token_counter: Any,
) -> dict[str, Any]:
    verify_self_hash(input_row, "case_input_sha256", f"{case_id} input")
    if (
        not is_exact_int(input_row.get("selection_rank"), expected=rank)
        or input_row.get("case_unit_id") != case_id
        or not is_exact_int(capacity_row.get("selection_rank"), expected=rank)
        or capacity_row.get("case_unit_id") != case_id
        or not is_exact_int(result_row.get("selection_rank"), expected=rank)
        or result_row.get("case_unit_id") != case_id
        or result_row.get("task_id") != case_id
        or result_row.get("verdict") != "accept"
        or not is_exact_int(result_row.get("warning_count"), expected=0)
        or not is_exact_int(result_row.get("error_count"), expected=0)
    ):
        raise IndependentValidationError(
            f"{case_id} cross-stage identity/order differs"
        )
    case_dir = review_root / case_id
    if case_dir.is_symlink() or not case_dir.is_dir():
        raise IndependentValidationError(
            f"{case_id} review case directory is missing/symlinked"
        )
    expected_names = {"codex_events.jsonl", "codex_stderr.log", "review.json"}
    actual_names = {path.name for path in case_dir.iterdir() if path.is_file()}
    if actual_names != expected_names or any(
        path.is_dir() or path.is_symlink() for path in case_dir.iterdir()
    ):
        raise IndependentValidationError(
            f"{case_id} review output namespace is not exact"
        )
    review_path = verify_regular_file_binding(
        result_row.get("review") or {}, f"{case_id} review"
    )
    if review_path != case_dir / "review.json":
        raise IndependentValidationError(
            f"{case_id} result points outside exact case directory"
        )
    review = load_json(review_path, f"{case_id} review")
    verify_self_hash(review, "review_sha256", f"{case_id} review")
    if (
        review.get("schema_version")
        != "androidworld_candidate116_semantic_review_v7_case_result/v1"
        or review.get("status") != "structurally_valid_independent_semantic_review"
        or not is_exact_int(review.get("selection_rank"), expected=rank)
        or review.get("case_unit_id") != case_id
        or review.get("task_id") != case_id
        or review.get("review_sha256") != result_row.get("review_sha256")
        or not is_exact_int(review.get("warning_count"), expected=0)
        or not is_exact_int(review.get("error_count"), expected=0)
        or review.get("reviewer_modified_checklist") is not False
        or review.get("human_review_claimed") is not False
        or review.get("freeze_authorized") is not False
    ):
        raise IndependentValidationError(
            f"{case_id} review wrapper identity/status differs"
        )
    for field in ("packet", "checklist_yaml", "checklist_json"):
        if review.get(field) != input_row.get(field):
            raise IndependentValidationError(
                f"{case_id} review {field} binding differs"
            )
    packet_path = verify_regular_file_binding(input_row["packet"], f"{case_id} packet")
    checklist_path = verify_regular_file_binding(
        input_row["checklist_yaml"], f"{case_id} checklist YAML"
    )
    checklist_json_path = verify_regular_file_binding(
        input_row["checklist_json"], f"{case_id} checklist JSON"
    )
    checklist = load_yaml(checklist_path, f"{case_id} checklist")
    if checklist != load_json(checklist_json_path, f"{case_id} checklist JSON"):
        raise IndependentValidationError(f"{case_id} checklist YAML/JSON differs")
    inventory = checklist_semantic_inventory(checklist)
    if (
        inventory != capacity_row.get("semantic_inventory")
        or inventory.get("inventory_sha256") != review.get("semantic_inventory_sha256")
        or inventory.get("inventory_sha256")
        != input_row.get("semantic_inventory_sha256")
    ):
        raise IndependentValidationError(f"{case_id} semantic inventory differs")
    packet_text = packet_path.read_text(encoding="utf-8")
    parsed = source_staging.parse_packet_sources(packet_text)
    raw_sources = {
        path: {
            "sha256": parsed["sources"][path]["sha256"],
            "line_count": parsed["sources"][path]["line_count"],
        }
        for path in parsed["inventory"]
    }
    requirements = capacity_row.get("requirements") or {}
    if requirements.get("requirements_sha256") != input_row.get(
        "coverage_requirements_sha256"
    ) or requirements.get("requirements_sha256") != review.get(
        "coverage_requirements_sha256"
    ):
        raise IndependentValidationError(
            f"{case_id} coverage requirements binding differs"
        )
    packet_expectations = capacity_row["packet_reader_operation_expectations"]
    review_expectations = capacity_row["review_operation_expectations"]
    checklist_text = checklist_path.read_text(encoding="utf-8")
    exact_checklist_output = review_staging.render_checklist_output_for_audit(
        checklist_text=checklist_text,
        inventory=inventory,
        requirements_sha256=requirements["requirements_sha256"],
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
    exact_prompt = review_staging.staged_review_prompt(
        base_prompt=base_prompt, manifest=manifest_stub
    )
    packet_tokens = sum(
        operation["expected_full_output_o200k_tokens"]
        for operation in packet_expectations["operations"]
    )
    if (
        token_counter(checklist_text)
        != capacity_row.get("actual_frozen_draft_o200k_tokens")
        or sha256_text(exact_checklist_output)
        != capacity_row.get("actual_frozen_draft_reader_output_sha256")
        or len(exact_checklist_output.encode("utf-8"))
        != capacity_row.get("checklist_reader_output_size_bytes")
        or token_counter(exact_checklist_output)
        != capacity_row.get("checklist_reader_output_o200k_tokens")
        or sha256_text(exact_prompt) != capacity_row.get("prompt_sha256")
        or token_counter(exact_prompt) != capacity_row.get("prompt_o200k_tokens")
        or packet_tokens != capacity_row.get("packet_reader_output_o200k_tokens")
    ):
        raise IndependentValidationError(
            f"{case_id} exact actual-draft capacity recomputation differs"
        )
    body = review.get("review_body")
    if not isinstance(body, Mapping):
        raise IndependentValidationError(f"{case_id} review body is not an object")
    body_qc = validate_review_body(
        body,
        schema=output_schema,
        checklist=checklist,
        inventory=inventory,
        raw_sources=raw_sources,
        require_accept=True,
        covered_line_spans=covered_line_spans_from_requirements(requirements),
    )
    if body_qc != review.get("review_body_qc") or review.get("verdict") != "accept":
        raise IndependentValidationError(f"{case_id} review body QC/verdict differs")
    if [row.get("dimension_id") for row in body.get("dimension_audits") or []] != list(
        DIMENSION_IDS
    ):
        raise IndependentValidationError(f"{case_id} 14-dimension order is not exact")
    events_path = verify_regular_file_binding(
        review.get("codex_events") or {}, f"{case_id} Codex events"
    )
    stderr_path = verify_regular_file_binding(
        review.get("codex_stderr") or {}, f"{case_id} Codex stderr"
    )
    if (
        events_path != case_dir / "codex_events.jsonl"
        or stderr_path != case_dir / "codex_stderr.log"
    ):
        raise IndependentValidationError(
            f"{case_id} event/stderr path escapes case directory"
        )
    stderr = stderr_path.read_text(encoding="utf-8").strip()
    if stderr not in {
        "",
        "WARNING: proceeding, even though we could not create PATH aliases: Operation not permitted (os error 1)",
    }:
        raise IndependentValidationError(
            f"{case_id} stderr contains a non-allowlisted warning/error"
        )
    reconstructed = review_staging.combined_coverage_receipt_from_events(
        events=parse_jsonl(events_path),
        requirements=requirements,
        packet_operation_expectations=capacity_row[
            "packet_reader_operation_expectations"
        ],
        review_operation_expectations=capacity_row["review_operation_expectations"],
        checklist_text=checklist_path.read_text(encoding="utf-8"),
        inventory=inventory,
        expected_final_body=body,
        token_counter=token_counter,
    )
    if reconstructed != review.get("combined_coverage_receipt"):
        raise IndependentValidationError(
            f"{case_id} saved reader receipt cannot be reconstructed"
        )
    coverage = reconstructed
    if (
        coverage.get("status")
        != "all_raw_official_then_immutable_checklist_read_with_paired_terminal_envelopes"
        or not is_exact_int(coverage.get("additional_command_count"), expected=0)
        or not is_exact_int(coverage.get("forbidden_tool_event_count"), expected=0)
        or coverage.get("global_order")
        != "overview_header_all_pages_all_raw_ranges_then_checklist"
        or coverage.get("coverage_receipt_sha256")
        != result_row.get("coverage_receipt_sha256")
        or (coverage.get("codex_0144_event_framing") or {}).get(
            "terminal_agent_message_body_sha256"
        )
        != canonical_sha256(body)
    ):
        raise IndependentValidationError(
            f"{case_id} combined reader coverage is not exact"
        )
    provenance = review.get("codex_provenance") or {}
    expected_workspace = (
        Path(config["isolated_runtime_roots"]["review_tmp_root"])
        / f"semantic-review-v7-{rank:03d}-{case_id}"
    )
    expected_argv = review_staging.build_codex_exec_argv_from_bound_paths(
        codex_executable=Path(config["codex_cli"]["resolved_path"]),
        workspace_root=expected_workspace,
        model=MODEL,
        reasoning_effort=REASONING_EFFORT,
        repository_root=Path(config["repository_root"]),
        review_tmp_root=Path(config["isolated_runtime_roots"]["review_tmp_root"]),
        auth_home=Path(config["isolated_runtime_roots"]["auth_home"]),
        original_codex_home=Path(config["original_codex_home"]),
        isolated_home=Path(config["isolated_runtime_roots"]["isolated_home"]),
        real_home=Path(config["real_home"]),
        require_existing=False,
    )
    if (
        provenance.get("provider") != "codex_cli"
        or provenance.get("auth_mode") != "codex_login"
        or provenance.get("model") != MODEL
        or provenance.get("model_version") != MODEL
        or provenance.get("reasoning_effort") != REASONING_EFFORT
        or provenance.get("fresh_context") is not True
        or provenance.get("ephemeral") is not True
        or provenance.get("permission_profile") != review_staging.PROFILE_NAME
        or provenance.get("permission_workspace_access") != "read"
        or provenance.get("permission_network_enabled") is not False
        or provenance.get("argv") != expected_argv
        or provenance.get("argv_sha256") != canonical_sha256(expected_argv)
        or provenance.get("prelock_sha256") != prelock.get("prelock_sha256")
        or provenance.get("config_sha256") != config.get("config_sha256")
        or provenance.get("snapshot_sha256") != config.get("snapshot_sha256")
        or provenance.get("capacity_sha256") != config.get("capacity_sha256")
    ):
        raise IndependentValidationError(f"{case_id} Codex provenance differs")
    ensure_no_sensitive_hash_fields(review)
    return {
        "selection_rank": rank,
        "case_unit_id": case_id,
        "status": "accept",
        "dimension_count": len(DIMENSION_IDS),
        "claim_count": body_qc["claim_count"],
        "support_occurrence_count": body_qc["support_occurrence_count"],
        "blocking_finding_count": 0,
        "review_sha256": review["review_sha256"],
        "coverage_receipt_sha256": coverage["coverage_receipt_sha256"],
    }


def run_validation(*, prelock_path: Path, review_root: Path) -> dict[str, Any]:
    prelock, config, capacity, output_schema, base_prompt = verify_prelock_context(
        prelock_path
    )
    token_counter, tokenizer_binding = source_staging.load_frozen_o200k_token_counter(
        tokenizer_root=Path(config["tokenizer_root"]["root"]),
        merge_table_path=Path(config["tokenizer_cache"]["path"]),
    )
    if canonical_bytes(tokenizer_binding) != canonical_bytes(
        capacity.get("tokenizer_binding")
    ):
        raise IndependentValidationError(
            "frozen tokenizer binding differs from review capacity"
        )
    if (
        review_root.is_symlink()
        or not review_root.is_dir()
        or review_root != Path(config["output_root"]).resolve(strict=True)
    ):
        raise IndependentValidationError(
            "review root is missing/symlinked or differs from config"
        )
    receipt_path = review_root / "_review_receipt.json"
    receipt = load_json(receipt_path, "semantic review v7 receipt")
    verify_self_hash(receipt, "receipt_sha256", "semantic review v7 receipt")
    order = list(prelock["case_order"])
    results = list(receipt.get("results") or [])
    if (
        receipt.get("schema_version") != RECEIPT_SCHEMA
        or receipt.get("status")
        != "complete_116_structurally_valid_independent_reviews"
        or not is_exact_int(receipt.get("case_count"), expected=CASE_COUNT)
        or receipt.get("case_order") != order
        or receipt.get("case_order_sha256") != prelock.get("case_order_sha256")
        or len(results) != CASE_COUNT
        or [row.get("case_unit_id") for row in results] != order
        or receipt.get("results_sha256") != canonical_sha256(results)
        or not is_exact_int(receipt.get("accept_count"), expected=CASE_COUNT)
        or not is_exact_int(receipt.get("reject_count"), expected=0)
        or not is_exact_int(receipt.get("warning_count"), expected=0)
        or not is_exact_int(receipt.get("error_count"), expected=0)
        or not is_exact_int(receipt.get("max_parallel"), expected=PARALLELISM)
        or not is_exact_int(
            receipt.get("observed_peak_registered"), expected=PARALLELISM
        )
        or not is_exact_int(
            receipt.get("observed_peak_live_codex_exec"), expected=PARALLELISM
        )
        or not is_exact_int(receipt.get("covered_case_count"), expected=CASE_COUNT)
        or not is_exact_int(receipt.get("external_codex_exec_count_before"), expected=0)
        or not is_exact_int(receipt.get("external_codex_exec_count_after"), expected=0)
        or receipt.get("prelock_sha256") != prelock.get("prelock_sha256")
        or receipt.get("config_sha256") != config.get("config_sha256")
        or receipt.get("snapshot_sha256") != config.get("snapshot_sha256")
        or receipt.get("capacity_sha256") != config.get("capacity_sha256")
        or receipt.get("human_review_claimed") is not False
        or receipt.get("freeze_authorized") is not False
        or (receipt.get("isolated_runtime_cleanup") or {}).get("all_paths_absent")
        is not True
        or (receipt.get("isolated_runtime_cleanup") or {}).get(
            "auth_content_or_hash_persisted"
        )
        is not False
    ):
        raise IndependentValidationError(
            "batch receipt is not exact accept 116/116, peak-six, clean"
        )
    expected_global = {
        "_namespace_claim.json",
        "_concurrency_samples.jsonl",
        "_review_receipt.json",
    }
    observed_dirs = {path.name for path in review_root.iterdir() if path.is_dir()}
    observed_files = {path.name for path in review_root.iterdir() if path.is_file()}
    if (
        observed_dirs != set(order)
        or observed_files != expected_global
        or any(path.is_symlink() for path in review_root.iterdir())
    ):
        raise IndependentValidationError("review root exact output namespace differs")
    concurrency_path = verify_regular_file_binding(
        receipt.get("concurrency_samples") or {}, "concurrency samples"
    )
    if concurrency_path != review_root / "_concurrency_samples.jsonl":
        raise IndependentValidationError(
            "concurrency sample binding points outside review root"
        )
    concurrency = verify_concurrency_samples(concurrency_path, expected_order=order)
    input_by_case = {row["case_unit_id"]: row for row in prelock["case_inputs"]}
    capacity_by_case = {row["case_unit_id"]: row for row in capacity["cases"]}
    accepted: list[dict[str, Any]] = []
    for rank, (case_id, result) in enumerate(zip(order, results, strict=True)):
        accepted.append(
            validate_case(
                rank=rank,
                case_id=case_id,
                input_row=input_by_case[case_id],
                capacity_row=capacity_by_case[case_id],
                result_row=result,
                review_root=review_root,
                prelock=prelock,
                config=config,
                output_schema=output_schema,
                base_prompt=base_prompt,
                token_counter=token_counter,
            )
        )
    report = add_self_hash(
        {
            "schema_version": VALIDATION_SCHEMA,
            "status": "pass_accept_116_of_116_zero_warnings_errors",
            "case_count": CASE_COUNT,
            "accepted_case_count": len(accepted),
            "rejected_case_count": 0,
            "case_order": order,
            "case_order_sha256": prelock["case_order_sha256"],
            "cases": accepted,
            "cases_sha256": canonical_sha256(accepted),
            "warning_count": 0,
            "error_count": 0,
            "warnings": [],
            "errors": [],
            "concurrency": concurrency,
            "prelock": regular_file_binding(prelock_path),
            "prelock_sha256": prelock["prelock_sha256"],
            "review_receipt": regular_file_binding(receipt_path),
            "review_receipt_sha256": receipt["receipt_sha256"],
            "deterministic_and_semantic_structure_gate_passed": True,
            "human_review_claimed": False,
            "freeze_authorized": False,
            "freeze_requires": [
                "root agent reads and accepts every case-specific semantic assessment 116/116",
                "root agent records explicit per-case acceptance without human-review claim",
            ],
        },
        "validation_sha256",
    )
    ensure_no_sensitive_hash_fields(report)
    return report


def main() -> int:
    args = parse_args()
    report_path = args.report.resolve()
    if report_path.exists() or report_path.is_symlink():
        raise IndependentValidationError(
            f"create-once validation report exists: {report_path}"
        )
    report = run_validation(
        prelock_path=args.prelock.resolve(strict=True),
        review_root=args.review_root.resolve(strict=True),
    )
    write_json_create_once(report_path, report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "accepted_case_count": report["accepted_case_count"],
                "warning_count": report["warning_count"],
                "error_count": report["error_count"],
                "validation_sha256": report["validation_sha256"],
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
