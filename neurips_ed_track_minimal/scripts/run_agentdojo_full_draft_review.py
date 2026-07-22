#!/usr/bin/env python3
"""Run the locked 949-case AgentDojo draft/review/revision lifecycle.

Initial checklists are produced by ``run_draft_batch.py`` with exactly six Codex
CLI workers.  Every final checklist then passes schema, packet-aware guardrails,
deterministic semantic review, and an independent structured Codex review.  A
model-proposed revision is always validated and reviewed again in a fresh session.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml
from jsonschema import Draft202012Validator


SCRIPT_DIR = Path(__file__).resolve().parent
MINIMAL_ROOT = SCRIPT_DIR.parent
PACKAGE_ROOT = MINIMAL_ROOT.parent
EXPERIMENT_ROOT = PACKAGE_ROOT / "experiments" / "agentdojo_full_v1.2.2_direct"
MANIFEST_PATH = EXPERIMENT_ROOT / "experiment_manifest.yaml"
SOURCE_BUNDLE_PATH = EXPERIMENT_ROOT / "source_bundles" / "case_packet_source_bundle.json"
PACKET_ROOT = EXPERIMENT_ROOT / "case_packets" / "agentdojo"
DRAFT_ROOT = EXPERIMENT_ROOT / "drafts" / "agentdojo"
BASE_DRAFT_PROMPT = MINIMAL_ROOT / "prompts" / "draft_case_checklist.prompt.md"
COMPOSED_DRAFT_PROMPT = EXPERIMENT_ROOT / "lock" / "agentdojo_full_draft_prompt.md"
CHECKLIST_SCHEMA = MINIMAL_ROOT / "schemas" / "case_checklist.schema.json"
TEMPLATE_PATH = MINIMAL_ROOT / "templates" / "case_checklist.template.yaml"
REVIEW_PROMPT = MINIMAL_ROOT / "prompts" / "review_agentdojo_full_checklist.prompt.md"
REVIEW_SCHEMA = MINIMAL_ROOT / "schemas" / "case_checklist_review.schema.json"
SCORE_PROMPT = MINIMAL_ROOT / "prompts" / "score_evidence_with_codex.prompt.md"
SCORE_SCHEMA = MINIMAL_ROOT / "schemas" / "evidence_score.schema.json"
DRAFT_BATCH_SCRIPT = SCRIPT_DIR / "run_draft_batch.py"
DRAFT_SCRIPT = SCRIPT_DIR / "draft_case_checklist.py"
VALIDATOR_SCRIPT = SCRIPT_DIR / "checklist_validator.py"
REVIEW_SCRIPT = SCRIPT_DIR / "review_case_checklist_with_codex.py"
UPDATE_CASE_LOCK_SCRIPT = SCRIPT_DIR / "update_case_locks.py"
BATCH_LOCK_SCRIPT = SCRIPT_DIR / "update_case_locks_batch.py"
GUARDRAILS_PATH = MINIMAL_ROOT / "checklist_guardrails.py"
DETERMINISTIC_REVIEW_PATH = SCRIPT_DIR / "case_checklist_review.py"
RESOLVED_CONFIG_PATH = EXPERIMENT_ROOT / "lock" / "draft_review_config.json"
INPUT_LOCK_PATH = EXPERIMENT_ROOT / "lock" / "draft_input_lock.json"
BUDGET_PLAN_PATH = EXPERIMENT_ROOT / "provenance" / "draft_budget_plan.json"
LIFECYCLE_REPORT_PATH = EXPERIMENT_ROOT / "provenance" / "draft_review_report.json"
LIFECYCLE_INDEX_PATH = EXPERIMENT_ROOT / "lock" / "draft_review_index.json"
CASE_LOCK_PATH = EXPERIMENT_ROOT / "lock" / "case_checklist_locks.jsonl"
LOCK_ACCEPTANCE_PATH = EXPERIMENT_ROOT / "provenance" / "case_checklist_lock_acceptance.json"

EXPECTED_CASES = 949
EXPECTED_SUITES = ("workspace", "travel", "banking", "slack")
TOKEN_BUDGETS = (12000, 16000, 20000, 24000)

if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from neurips_ed_track_minimal.checklist_guardrails import (  # noqa: E402
    ChecklistGuardrailError,
    case_packet_support_paths,
    validate_checklist_guardrails,
)
from neurips_ed_track_minimal.scripts.case_checklist_review import (  # noqa: E402
    review_agentdojo_checklist,
    validate_model_review_body,
)
from neurips_ed_track_minimal.scripts.draft_case_checklist import (  # noqa: E402
    compose_prompt,
    extract_case_metadata,
)


class DraftReviewLifecycleError(RuntimeError):
    """Raised when an input or case fails a strict lifecycle gate."""


@dataclass(frozen=True)
class CaseInput:
    case_unit_id: str
    task_id: str
    suite: str
    directory_name: str
    case_packet_path: Path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--canary", action="store_true", help="Run one case from each of four suites")
    parser.add_argument("--skip-generation", action="store_true")
    parser.add_argument("--force-generation", action="store_true")
    parser.add_argument("--max-parallel", type=int, default=6)
    parser.add_argument("--max-review-rounds", type=int, default=5)
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--reasoning-effort", default="xhigh", choices=["minimal", "low", "medium", "high", "xhigh"])
    parser.add_argument("--codex-timeout-seconds", type=int, default=1800)
    parser.add_argument("--codex-sandbox", default="read-only", choices=["read-only"])
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--source-bundle", type=Path, default=SOURCE_BUNDLE_PATH)
    parser.add_argument("--case-packet-root", type=Path, default=PACKET_ROOT)
    parser.add_argument("--output-root", type=Path, default=DRAFT_ROOT)
    parser.add_argument("--base-draft-prompt", type=Path, default=BASE_DRAFT_PROMPT)
    parser.add_argument("--composed-draft-prompt", type=Path, default=COMPOSED_DRAFT_PROMPT)
    parser.add_argument("--checklist-schema", type=Path, default=CHECKLIST_SCHEMA)
    parser.add_argument("--review-prompt", type=Path, default=REVIEW_PROMPT)
    parser.add_argument("--review-schema", type=Path, default=REVIEW_SCHEMA)
    parser.add_argument("--score-prompt", type=Path, default=SCORE_PROMPT)
    parser.add_argument("--score-schema", type=Path, default=SCORE_SCHEMA)
    parser.add_argument("--resolved-config", type=Path, default=RESOLVED_CONFIG_PATH)
    parser.add_argument("--input-lock", type=Path, default=INPUT_LOCK_PATH)
    parser.add_argument("--budget-plan", type=Path, default=BUDGET_PLAN_PATH)
    parser.add_argument("--report", type=Path, default=LIFECYCLE_REPORT_PATH)
    parser.add_argument("--index", type=Path, default=LIFECYCLE_INDEX_PATH)
    parser.add_argument("--case-lock-file", type=Path, default=CASE_LOCK_PATH)
    parser.add_argument("--lock-acceptance", type=Path, default=LOCK_ACCEPTANCE_PATH)
    return parser.parse_args(argv)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _sha256_object(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value).rstrip(b"\n")).hexdigest()


def _display(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(PACKAGE_ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def _write_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
        staged = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def _write_json(path: Path, value: Any) -> None:
    _write_atomic(path, _canonical_bytes(value))


def _write_text(path: Path, value: str) -> None:
    _write_atomic(path, value.encode("utf-8"))


def _load_mapping(path: Path) -> dict[str, Any]:
    if path.suffix.lower() in {".yaml", ".yml"}:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DraftReviewLifecycleError(f"expected mapping: {path}")
    return value


def _safe_case_dir(case_unit_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", case_unit_id)


def _manifest_cases(manifest_path: Path, packet_root: Path) -> list[CaseInput]:
    manifest = _load_mapping(manifest_path)
    domains = manifest.get("domains")
    if not isinstance(domains, list):
        raise DraftReviewLifecycleError("manifest domains must be a list")
    matches = [item for item in domains if isinstance(item, Mapping) and item.get("domain") == "agentdojo"]
    if len(matches) != 1:
        raise DraftReviewLifecycleError(f"expected one agentdojo domain block, found {len(matches)}")
    raw_cases = matches[0].get("case_units")
    if not isinstance(raw_cases, list) or len(raw_cases) != EXPECTED_CASES:
        raise DraftReviewLifecycleError(
            f"manifest case count must be {EXPECTED_CASES}, found {len(raw_cases) if isinstance(raw_cases, list) else 'invalid'}"
        )
    cases: list[CaseInput] = []
    for index, item in enumerate(raw_cases):
        if not isinstance(item, Mapping):
            raise DraftReviewLifecycleError(f"manifest case_units[{index}] is not a mapping")
        case_unit_id = str(item.get("case_unit_id") or "")
        task_id = str(item.get("task_id") or "")
        parts = case_unit_id.split(":")
        if len(parts) != 4 or parts[0] != "v1.2.2":
            raise DraftReviewLifecycleError(f"invalid AgentDojo case ID: {case_unit_id}")
        directory_name = _safe_case_dir(case_unit_id)
        packet_path = packet_root / directory_name / "case_packet.md"
        if not packet_path.is_file():
            raise DraftReviewLifecycleError(f"case packet missing for {case_unit_id}: {packet_path}")
        metadata = extract_case_metadata(packet_path.read_text(encoding="utf-8"))
        if metadata != {"domain": "agentdojo", "case_unit_id": case_unit_id, "task_id": task_id}:
            raise DraftReviewLifecycleError(f"case packet metadata mismatch: {case_unit_id}")
        cases.append(CaseInput(case_unit_id, task_id, parts[1], directory_name, packet_path.resolve()))
    ids = [case.case_unit_id for case in cases]
    if len(set(ids)) != EXPECTED_CASES:
        raise DraftReviewLifecycleError("manifest contains duplicate case IDs")
    packet_dirs = {path.parent.name for path in packet_root.glob("*/case_packet.md")}
    expected_dirs = {case.directory_name for case in cases}
    if packet_dirs != expected_dirs:
        raise DraftReviewLifecycleError(
            f"packet directory set mismatch: missing={sorted(expected_dirs-packet_dirs)[:5]}, extra={sorted(packet_dirs-expected_dirs)[:5]}"
        )
    return cases


def _validate_source_bundle(bundle_path: Path, cases: Sequence[CaseInput]) -> None:
    bundle = _load_mapping(bundle_path)
    sources = bundle.get("sources")
    if not isinstance(sources, list) or len(sources) != EXPECTED_CASES or bundle.get("source_count") != EXPECTED_CASES:
        raise DraftReviewLifecycleError("source bundle must contain exactly 949 entries")
    actual = [str(item.get("case_unit_id") or "") for item in sources if isinstance(item, Mapping)]
    expected = [case.case_unit_id for case in cases]
    if actual != expected:
        raise DraftReviewLifecycleError("source bundle case ID order does not exactly match manifest")
    for case, source in zip(cases, sources, strict=True):
        assert isinstance(source, Mapping)
        draft_input = source.get("draft_input")
        if not isinstance(draft_input, Mapping):
            raise DraftReviewLifecycleError(f"missing source draft_input: {case.case_unit_id}")
        if draft_input.get("case_packet_sha256") != _sha256_file(case.case_packet_path):
            raise DraftReviewLifecycleError(f"stale source bundle packet hash: {case.case_unit_id}")


def _codex_preflight() -> tuple[str, str]:
    if shutil.which("codex") is None:
        raise DraftReviewLifecycleError("codex is not on PATH")
    version = subprocess.run(["codex", "--version"], capture_output=True, text=True, check=False)
    status = subprocess.run(["codex", "login", "status"], capture_output=True, text=True, check=False)
    version_text = (version.stdout or version.stderr).strip()
    status_text = (status.stdout or status.stderr).strip()
    if version.returncode != 0 or not version_text:
        raise DraftReviewLifecycleError("could not resolve Codex CLI version")
    if status.returncode != 0 or "logged in" not in status_text.lower():
        raise DraftReviewLifecycleError(f"Codex CLI login is not active: {status_text}")
    return version_text, status_text


def _path_lock(path: Path) -> dict[str, str]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise DraftReviewLifecycleError(f"locked input missing: {resolved}")
    return {"path": _display(resolved), "sha256": _sha256_file(resolved)}


def _build_config(args: argparse.Namespace, codex_version: str) -> dict[str, Any]:
    composed = compose_prompt(
        args.base_draft_prompt.read_text(encoding="utf-8"),
        None,
    )
    _write_text(args.composed_draft_prompt, composed)
    code_inputs = (
        DRAFT_BATCH_SCRIPT,
        DRAFT_SCRIPT,
        VALIDATOR_SCRIPT,
        REVIEW_SCRIPT,
        UPDATE_CASE_LOCK_SCRIPT,
        BATCH_LOCK_SCRIPT,
        GUARDRAILS_PATH,
        DETERMINISTIC_REVIEW_PATH,
        Path(__file__),
    )
    return {
        "schema_version": "agentdojo_draft_review_config/v1",
        "benchmark_version": "v1.2.2",
        "attack": "direct",
        "defense": None,
        "expected_cases": EXPECTED_CASES,
        "generation": {
            "provider": "codex_cli",
            "auth_mode": "codex_login",
            "model": args.model,
            "reasoning_effort": args.reasoning_effort,
            "sandbox": args.codex_sandbox,
            "ephemeral": True,
            "ignore_user_config": True,
            "model_verbosity": "low",
            "timeout_seconds": args.codex_timeout_seconds,
            "max_parallel": args.max_parallel,
            "token_budgets": list(TOKEN_BUDGETS),
            "token_budgets_are_retry_labels_not_codex_output_caps": True,
            "base_prompt": _path_lock(args.base_draft_prompt),
            "prompt_supplement": None,
            "composed_prompt": _path_lock(args.composed_draft_prompt),
            "checklist_schema": _path_lock(args.checklist_schema),
            "template": _path_lock(TEMPLATE_PATH),
        },
        "review": {
            "provider": "codex_cli",
            "auth_mode": "codex_login",
            "model": args.model,
            "reasoning_effort": args.reasoning_effort,
            "sandbox": args.codex_sandbox,
            "ephemeral": True,
            "ignore_user_config": True,
            "model_verbosity": "low",
            "timeout_seconds": args.codex_timeout_seconds,
            "max_parallel": args.max_parallel,
            "max_rounds": args.max_review_rounds,
            "prompt": _path_lock(args.review_prompt),
            "schema": _path_lock(args.review_schema),
        },
        "locking": {
            "batch_runner": _path_lock(BATCH_LOCK_SCRIPT),
            "single_case_runner": _path_lock(UPDATE_CASE_LOCK_SCRIPT),
            "score_prompt": _path_lock(args.score_prompt),
            "score_schema": _path_lock(args.score_schema),
            "case_lock_file": _display(args.case_lock_file),
            "lock_acceptance": _display(args.lock_acceptance),
        },
        "codex_cli_version": codex_version,
        "lifecycle_code": [_path_lock(path) for path in code_inputs],
    }


def _publish_or_verify_config(path: Path, config: Mapping[str, Any]) -> str:
    payload = _canonical_bytes(config)
    if path.exists() and path.read_bytes() != payload:
        raise DraftReviewLifecycleError(f"resolved config drifted after lock: {path}")
    if not path.exists():
        _write_atomic(path, payload)
    return _sha256_file(path)


def _packet_index(cases: Sequence[CaseInput]) -> list[dict[str, str]]:
    return [
        {
            "case_unit_id": case.case_unit_id,
            "task_id": case.task_id,
            "suite": case.suite,
            "case_packet_path": _display(case.case_packet_path),
            "case_packet_sha256": _sha256_file(case.case_packet_path),
            "raw_case_manifest_sha256": _sha256_file(case.case_packet_path.parent / "raw_case_manifest.json"),
            "selected_task_source_sha256": _sha256_file(
                case.case_packet_path.parent / "raw_case" / "selected_task_source.json"
            ),
        }
        for case in cases
    ]


def _input_lock_definition(
    args: argparse.Namespace,
    cases: Sequence[CaseInput],
    *,
    config_sha256: str,
) -> dict[str, Any]:
    packet_index = _packet_index(cases)
    ids = [case.case_unit_id for case in cases]
    return {
        "schema_version": "agentdojo_draft_input_lock/v1",
        "manifest": _path_lock(args.manifest),
        "source_bundle": _path_lock(args.source_bundle),
        "case_packet_root": _display(args.case_packet_root),
        "case_count": len(cases),
        "case_id_order_sha256": _sha256_object(ids),
        "case_id_set_sha256": _sha256_object(sorted(ids)),
        "packet_index_sha256": _sha256_object(packet_index),
        "packet_index": packet_index,
        "resolved_config": {"path": _display(args.resolved_config), "sha256": config_sha256},
        "reuse_audit": {
            "strict_match_fields": [
                "case_packet_sha256",
                "draft_prompt_sha256",
                "checklist_schema_sha256",
                "checklist_sha256",
            ],
            "legacy_candidates": 100,
            "strictly_reusable": 0,
            "planned_new_drafts": EXPECTED_CASES,
        },
    }


def _publish_or_verify_input_lock(path: Path, definition: Mapping[str, Any]) -> str:
    if path.exists():
        existing = _load_mapping(path)
        existing_definition = dict(existing)
        existing_definition.pop("locked_at", None)
        if existing_definition != dict(definition):
            raise DraftReviewLifecycleError(f"draft input lock drift detected: {path}")
    else:
        _write_json(path, {**definition, "locked_at": _now()})
    return _sha256_file(path)


def _budget_plan(args: argparse.Namespace, *, input_lock_sha256: str) -> dict[str, Any]:
    max_generation_calls = EXPECTED_CASES * len(TOKEN_BUDGETS)
    max_review_calls = EXPECTED_CASES * args.max_review_rounds
    return {
        "schema_version": "agentdojo_draft_budget/v1",
        "status": "planned",
        "planned_at": _now(),
        "denominator": EXPECTED_CASES,
        "strictly_reusable_legacy_drafts": 0,
        "new_drafts_required": EXPECTED_CASES,
        "max_parallel": args.max_parallel,
        "minimum_generation_codex_exec_calls": EXPECTED_CASES,
        "maximum_generation_codex_exec_calls": max_generation_calls,
        "minimum_review_codex_exec_calls": EXPECTED_CASES,
        "maximum_review_codex_exec_calls": max_review_calls,
        "minimum_total_codex_exec_calls": EXPECTED_CASES * 2,
        "maximum_total_codex_exec_calls": max_generation_calls + max_review_calls,
        "generation_retry_labels": list(TOKEN_BUDGETS),
        "codex_cli_output_token_cap_available": False,
        "max_review_rounds_per_case": args.max_review_rounds,
        "input_lock_sha256": input_lock_sha256,
        "acceptance_targets": {
            "case_packets": EXPECTED_CASES,
            "source_entries": EXPECTED_CASES,
            "valid_drafts": EXPECTED_CASES,
            "reviewed_locked": EXPECTED_CASES,
            "unresolved_drafts": 0,
        },
    }


def _selected_cases(cases: Sequence[CaseInput], canary: bool) -> list[CaseInput]:
    if not canary:
        return list(cases)
    selected: list[CaseInput] = []
    for suite in EXPECTED_SUITES:
        match = next((case for case in cases if case.suite == suite), None)
        if match is None:
            raise DraftReviewLifecycleError(f"canary suite missing: {suite}")
        selected.append(match)
    return selected


def _canary_packet_root(args: argparse.Namespace, cases: Sequence[CaseInput]) -> Path:
    root = args.output_root.parent / "_canary_packets"
    root.mkdir(parents=True, exist_ok=True)
    expected_names = {case.directory_name for case in cases}
    for child in root.iterdir():
        if child.name not in expected_names:
            raise DraftReviewLifecycleError(f"unexpected canary packet entry: {child}")
    for case in cases:
        link = root / case.directory_name
        if link.exists() or link.is_symlink():
            if not link.is_symlink() or link.resolve() != case.case_packet_path.parent:
                raise DraftReviewLifecycleError(f"stale canary packet link: {link}")
        else:
            link.symlink_to(case.case_packet_path.parent, target_is_directory=True)
    return root


def _active_output_root(args: argparse.Namespace) -> Path:
    return args.output_root.parent / "_canary_drafts" if args.canary else args.output_root


def _run_generation(args: argparse.Namespace, selected: Sequence[CaseInput]) -> None:
    packet_root = args.case_packet_root
    output_root = _active_output_root(args)
    if args.canary:
        packet_root = _canary_packet_root(args, selected)
    command = [
        sys.executable,
        str(DRAFT_BATCH_SCRIPT),
        "--case-packet-root",
        str(packet_root),
        "--output-root",
        str(output_root),
        "--provider",
        "codex",
        "--model",
        args.model,
        "--reasoning-effort",
        args.reasoning_effort,
        "--max-parallel",
        str(args.max_parallel),
        "--large-max-parallel",
        str(args.max_parallel),
        "--large-case-threshold-bytes",
        "100000",
        "--codex-timeout-seconds",
        str(args.codex_timeout_seconds),
        "--large-codex-timeout-seconds",
        str(args.codex_timeout_seconds),
        "--codex-sandbox",
        args.codex_sandbox,
        "--token-budgets",
        ",".join(str(value) for value in TOKEN_BUDGETS),
        "--quality-check",
        "agentdojo",
        "--sort-by",
        "name",
    ]
    if args.force_generation:
        command.append("--force")
    completed = subprocess.run(command, cwd=PACKAGE_ROOT, check=False)
    if completed.returncode != 0:
        raise DraftReviewLifecycleError(f"draft batch exited with status {completed.returncode}")


def _validate_checklist(
    path: Path,
    *,
    case: CaseInput,
    schema: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    checklist = _load_mapping(path)
    errors = sorted(Draft202012Validator(schema).iter_errors(checklist), key=lambda item: list(item.absolute_path))
    if errors:
        detail = "; ".join(
            f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors
        )
        raise DraftReviewLifecycleError(f"checklist schema failed for {case.case_unit_id}: {detail}")
    expected = {"case_unit_id": case.case_unit_id, "domain": "agentdojo", "task_id": case.task_id}
    for field, value in expected.items():
        if checklist.get(field) != value:
            raise DraftReviewLifecycleError(
                f"checklist metadata mismatch for {case.case_unit_id}: {field}={checklist.get(field)!r}"
            )
    try:
        validate_checklist_guardrails(
            checklist,
            allowed_source_paths=case_packet_support_paths(case.case_packet_path.read_text(encoding="utf-8")),
        )
    except ChecklistGuardrailError as exc:
        raise DraftReviewLifecycleError(f"checklist guardrails failed for {case.case_unit_id}: {exc}") from exc
    deterministic = review_agentdojo_checklist(checklist, case_packet_path=case.case_packet_path)
    return checklist, deterministic


def _canonical_checklist_bytes(checklist: Mapping[str, Any]) -> bytes:
    return yaml.safe_dump(
        dict(checklist),
        sort_keys=False,
        allow_unicode=True,
        width=1000,
    ).encode("utf-8")


def _generation_receipt(
    args: argparse.Namespace,
    *,
    case: CaseInput,
    case_dir: Path,
    config_sha256: str,
    input_lock_sha256: str,
    checklist: Mapping[str, Any],
) -> dict[str, Any]:
    required = {
        "checklist": case_dir / "checklist.yaml",
        "checklist_json": case_dir / "checklist.json",
        "api_response": case_dir / "api_response.json",
        "llm_call": case_dir / "llm_call.json",
        "reasoning_summary": case_dir / "reasoning_summary.txt",
    }
    for label, path in required.items():
        if not path.is_file():
            raise DraftReviewLifecycleError(f"generation sidecar missing ({label}): {case.case_unit_id}")
    generated_yaml = case_dir / "generated_checklist.yaml"
    generated_json = case_dir / "generated_checklist.json"
    if args.force_generation or not generated_yaml.exists():
        shutil.copy2(required["checklist"], generated_yaml)
    if args.force_generation or not generated_json.exists():
        shutil.copy2(required["checklist_json"], generated_json)
    llm_call = _load_mapping(required["llm_call"])
    if llm_call.get("provider") != "codex_cli" or llm_call.get("model") != args.model:
        raise DraftReviewLifecycleError(f"generation provider/model drift: {case.case_unit_id}")
    response = llm_call.get("response_metadata")
    if not isinstance(response, Mapping) or response.get("reasoning_effort") != args.reasoning_effort:
        raise DraftReviewLifecycleError(f"generation reasoning effort drift: {case.case_unit_id}")
    canonical_json = json.loads(required["checklist_json"].read_text(encoding="utf-8"))
    if canonical_json != checklist:
        raise DraftReviewLifecycleError(f"checklist YAML/JSON semantic mismatch: {case.case_unit_id}")
    receipt = {
        "schema_version": "case_checklist_generation/v1",
        "case_unit_id": case.case_unit_id,
        "case_packet_path": _display(case.case_packet_path),
        "case_packet_sha256": _sha256_file(case.case_packet_path),
        "checklist_path": _display(generated_yaml),
        "checklist_sha256": _sha256_file(generated_yaml),
        "checklist_json_path": _display(generated_json),
        "checklist_json_sha256": _sha256_file(generated_json),
        "llm_call_path": _display(required["llm_call"]),
        "llm_call_sha256": _sha256_file(required["llm_call"]),
        "api_response_path": _display(required["api_response"]),
        "api_response_sha256": _sha256_file(required["api_response"]),
        "reasoning_summary_path": _display(required["reasoning_summary"]),
        "reasoning_summary_sha256": _sha256_file(required["reasoning_summary"]),
        "composed_draft_prompt_path": _display(args.composed_draft_prompt),
        "composed_draft_prompt_sha256": _sha256_file(args.composed_draft_prompt),
        "checklist_schema_path": _display(args.checklist_schema),
        "checklist_schema_sha256": _sha256_file(args.checklist_schema),
        "resolved_config_sha256": config_sha256,
        "input_lock_sha256": input_lock_sha256,
        "provider": "codex_cli",
        "auth_mode": "codex_login",
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
    }
    _write_json(case_dir / "generation.json", receipt)
    return receipt


def _validate_generated_cases(
    args: argparse.Namespace,
    cases: Sequence[CaseInput],
    *,
    config_sha256: str,
    input_lock_sha256: str,
) -> dict[str, dict[str, Any]]:
    schema = _load_mapping(args.checklist_schema)
    output_root = _active_output_root(args)
    receipts: dict[str, dict[str, Any]] = {}
    for case in cases:
        case_dir = output_root / case.directory_name
        checklist_path = case_dir / "checklist.yaml"
        if not checklist_path.is_file():
            raise DraftReviewLifecycleError(f"generated checklist missing: {case.case_unit_id}")
        checklist, _ = _validate_checklist(checklist_path, case=case, schema=schema)
        receipts[case.case_unit_id] = _generation_receipt(
            args,
            case=case,
            case_dir=case_dir,
            config_sha256=config_sha256,
            input_lock_sha256=input_lock_sha256,
            checklist=checklist,
        )
    return receipts


def _reviewer_config(args: argparse.Namespace, codex_version: str) -> dict[str, Any]:
    return {
        "provider": "codex_cli",
        "auth_mode": "codex_login",
        "codex_cli_version": codex_version,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "sandbox": args.codex_sandbox,
        "ephemeral": True,
        "ignore_user_config": True,
        "model_verbosity": "low",
        "timeout_seconds": args.codex_timeout_seconds,
    }


def _receipt_bindings(args: argparse.Namespace, case: CaseInput, checklist_path: Path) -> dict[str, str]:
    return {
        "case_packet_path": _display(case.case_packet_path),
        "case_packet_sha256": _sha256_file(case.case_packet_path),
        "checklist_path": _display(checklist_path),
        "checklist_sha256": _sha256_file(checklist_path),
        "draft_prompt_path": _display(args.composed_draft_prompt),
        "draft_prompt_sha256": _sha256_file(args.composed_draft_prompt),
        "checklist_schema_path": _display(args.checklist_schema),
        "checklist_schema_sha256": _sha256_file(args.checklist_schema),
        "review_prompt_path": _display(args.review_prompt),
        "review_prompt_sha256": _sha256_file(args.review_prompt),
        "review_schema_path": _display(args.review_schema),
        "review_schema_sha256": _sha256_file(args.review_schema),
    }


def _validate_review_receipt_schema(receipt: Mapping[str, Any], schema: Mapping[str, Any]) -> None:
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda item: list(item.absolute_path))
    if errors:
        detail = "; ".join(
            f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors
        )
        raise DraftReviewLifecycleError(f"review receipt schema failed: {detail}")


def _reusable_review(
    args: argparse.Namespace,
    *,
    case: CaseInput,
    case_dir: Path,
    checklist_schema: Mapping[str, Any],
    review_schema: Mapping[str, Any],
    reviewer_config: Mapping[str, Any],
) -> bool:
    review_path = case_dir / "review.json"
    checklist_path = case_dir / "checklist.yaml"
    if not review_path.is_file() or not checklist_path.is_file():
        return False
    try:
        receipt = _load_mapping(review_path)
        _validate_review_receipt_schema(receipt, review_schema)
        _, deterministic = _validate_checklist(checklist_path, case=case, schema=checklist_schema)
    except Exception:
        return False
    if receipt.get("schema_version") != "case_checklist_model_review/v1":
        return False
    if receipt.get("case_unit_id") != case.case_unit_id:
        return False
    if receipt.get("decision") != "accept" or receipt.get("unresolved_findings") != []:
        return False
    if deterministic != {"status": "pass", "findings": []}:
        return False
    if receipt.get("deterministic_review") != deterministic:
        return False
    model_review = receipt.get("model_review")
    if not isinstance(model_review, Mapping) or validate_model_review_body(model_review):
        return False
    if model_review.get("decision") != "accept":
        return False
    if receipt.get("reviewer_config") != dict(reviewer_config):
        return False
    for field, expected in _receipt_bindings(args, case, checklist_path).items():
        if receipt.get(field) != expected:
            return False
    return True


def _run_model_review(
    args: argparse.Namespace,
    *,
    case: CaseInput,
    checklist_path: Path,
    attempt_dir: Path,
    round_index: int,
    deterministic: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    attempt_dir.mkdir(parents=True, exist_ok=True)
    prefix = attempt_dir / f"round_{round_index:02d}"
    body_path = prefix.with_suffix(".model_review.json")
    prompt_path = args.review_prompt
    if deterministic.get("status") != "pass":
        prompt_path = prefix.with_suffix(".review_prompt.md")
        prompt_text = args.review_prompt.read_text(encoding="utf-8").rstrip()
        prompt_text += (
            "\n\n## Deterministic blocking findings\n\n"
            "Treat every item below as blocking. Return `revise` and a complete corrected checklist.\n\n"
            "```json\n"
            + json.dumps(deterministic.get("findings", []), indent=2, ensure_ascii=False)
            + "\n```\n"
        )
        _write_text(prompt_path, prompt_text)
    command = [
        sys.executable,
        str(REVIEW_SCRIPT),
        str(case.case_packet_path),
        str(checklist_path),
        "-o",
        str(body_path),
        "--model",
        args.model,
        "--reasoning-effort",
        args.reasoning_effort,
        "--codex-timeout-seconds",
        str(args.codex_timeout_seconds),
        "--codex-sandbox",
        args.codex_sandbox,
        "--review-prompt",
        str(prompt_path),
        "--review-schema",
        str(args.review_schema),
    ]
    started = _now()
    completed = subprocess.run(command, cwd=PACKAGE_ROOT, capture_output=True, text=True, check=False)
    _write_text(prefix.with_suffix(".stdout.log"), completed.stdout or "")
    _write_text(prefix.with_suffix(".stderr.log"), completed.stderr or "")
    record: dict[str, Any] = {
        "round": round_index,
        "started_at": started,
        "finished_at": _now(),
        "returncode": completed.returncode,
        "input_checklist_path": _display(checklist_path),
        "input_checklist_sha256": _sha256_file(checklist_path),
        "review_prompt_path": _display(prompt_path),
        "review_prompt_sha256": _sha256_file(prompt_path),
        "deterministic_review": dict(deterministic),
    }
    if completed.returncode != 0 or not body_path.is_file():
        record["error"] = (completed.stderr or completed.stdout or "reviewer produced no output").strip()[-4000:]
        return None, record
    body = _load_mapping(body_path)
    body_errors = validate_model_review_body(body)
    if body_errors:
        record["error"] = "; ".join(body_errors)
        return None, record
    record.update(
        {
            "model_review_path": _display(body_path),
            "model_review_sha256": _sha256_file(body_path),
            "decision": body.get("decision"),
        }
    )
    return body, record


def _materialize_revision(body: Mapping[str, Any], case: CaseInput) -> dict[str, Any]:
    revision = body.get("revised_checklist")
    if not isinstance(revision, Mapping):
        raise DraftReviewLifecycleError("revise decision did not include revised_checklist")
    if "schema_version" in revision:
        full = dict(revision)
    else:
        full = {
            "schema_version": "case_checklist_v1",
            "case_unit_id": case.case_unit_id,
            "domain": "agentdojo",
            "task_id": case.task_id,
            **dict(revision),
        }
    full["schema_version"] = "case_checklist_v1"
    full["case_unit_id"] = case.case_unit_id
    full["domain"] = "agentdojo"
    full["task_id"] = case.task_id
    return full


def _publish_final_checklist(case_dir: Path, checklist: Mapping[str, Any]) -> Path:
    checklist_path = case_dir / "checklist.yaml"
    checklist_json_path = case_dir / "checklist.json"
    _write_atomic(checklist_path, _canonical_checklist_bytes(checklist))
    _write_json(checklist_json_path, checklist)
    return checklist_path


def _review_one_case(
    args: argparse.Namespace,
    *,
    case: CaseInput,
    checklist_schema: Mapping[str, Any],
    review_schema: Mapping[str, Any],
    reviewer_config: Mapping[str, Any],
    run_id: str,
) -> dict[str, Any]:
    case_dir = _active_output_root(args) / case.directory_name
    canonical_checklist = case_dir / "checklist.yaml"
    if _reusable_review(
        args,
        case=case,
        case_dir=case_dir,
        checklist_schema=checklist_schema,
        review_schema=review_schema,
        reviewer_config=reviewer_config,
    ):
        return {
            "case_unit_id": case.case_unit_id,
            "status": "reused_review",
            "review_rounds": 0,
            "revised": False,
        }

    current_path = canonical_checklist
    attempt_dir = case_dir / "review_attempts" / run_id
    attempts: list[dict[str, Any]] = []
    revised = False
    for round_index in range(1, args.max_review_rounds + 1):
        try:
            checklist, deterministic = _validate_checklist(
                current_path,
                case=case,
                schema=checklist_schema,
            )
        except DraftReviewLifecycleError as exc:
            return {
                "case_unit_id": case.case_unit_id,
                "status": "unresolved",
                "review_rounds": round_index - 1,
                "revised": revised,
                "error": str(exc),
                "attempts": attempts,
            }

        model_review, attempt_record = _run_model_review(
            args,
            case=case,
            checklist_path=current_path,
            attempt_dir=attempt_dir,
            round_index=round_index,
            deterministic=deterministic,
        )
        attempts.append(attempt_record)
        if model_review is None:
            continue
        if model_review.get("decision") == "accept":
            if deterministic != {"status": "pass", "findings": []}:
                attempt_record["error"] = "model accepted despite deterministic blocking findings"
                continue
            final_path = _publish_final_checklist(case_dir, checklist)
            receipt = {
                "schema_version": "case_checklist_model_review/v1",
                "case_unit_id": case.case_unit_id,
                "decision": "accept",
                "unresolved_findings": [],
                **_receipt_bindings(args, case, final_path),
                "deterministic_review": deterministic,
                "model_review": model_review,
                "reviewer_config": dict(reviewer_config),
                "reviewed_at": _now(),
            }
            _validate_review_receipt_schema(receipt, review_schema)
            _write_json(case_dir / "review.json", receipt)
            lifecycle = {
                "schema_version": "case_checklist_review_lifecycle/v1",
                "case_unit_id": case.case_unit_id,
                "status": "accepted",
                "revised": revised,
                "review_rounds": round_index,
                "final_checklist_sha256": _sha256_file(final_path),
                "final_review_sha256": _sha256_file(case_dir / "review.json"),
                "attempts": attempts,
            }
            _write_json(case_dir / "review_lifecycle.json", lifecycle)
            return {
                "case_unit_id": case.case_unit_id,
                "status": "accepted",
                "review_rounds": round_index,
                "revised": revised,
            }

        revision = _materialize_revision(model_review, case)
        revision_path = attempt_dir / f"round_{round_index:02d}.revised_checklist.yaml"
        _write_atomic(revision_path, _canonical_checklist_bytes(revision))
        try:
            _validate_checklist(revision_path, case=case, schema=checklist_schema)
        except DraftReviewLifecycleError as exc:
            attempt_record["revision_validation_error"] = str(exc)
            continue
        current_path = revision_path
        revised = True

    lifecycle = {
        "schema_version": "case_checklist_review_lifecycle/v1",
        "case_unit_id": case.case_unit_id,
        "status": "unresolved",
        "revised": revised,
        "review_rounds": args.max_review_rounds,
        "attempts": attempts,
    }
    _write_json(case_dir / "review_lifecycle.json", lifecycle)
    return {
        "case_unit_id": case.case_unit_id,
        "status": "unresolved",
        "review_rounds": args.max_review_rounds,
        "revised": revised,
        "attempts": attempts,
    }


def _review_cases(
    args: argparse.Namespace,
    cases: Sequence[CaseInput],
    *,
    codex_version: str,
    run_id: str,
) -> list[dict[str, Any]]:
    checklist_schema = _load_mapping(args.checklist_schema)
    review_schema = _load_mapping(args.review_schema)
    Draft202012Validator.check_schema(review_schema)
    reviewer_config = _reviewer_config(args, codex_version)
    results: list[dict[str, Any]] = []
    completed_count = 0
    print(
        f"Starting independent checklist review: cases={len(cases)} max_parallel={args.max_parallel} "
        f"model={args.model} reasoning_effort={args.reasoning_effort}",
        flush=True,
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_parallel) as executor:
        futures = {
            executor.submit(
                _review_one_case,
                args,
                case=case,
                checklist_schema=checklist_schema,
                review_schema=review_schema,
                reviewer_config=reviewer_config,
                run_id=run_id,
            ): case
            for case in cases
        }
        for future in concurrent.futures.as_completed(futures):
            case = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "case_unit_id": case.case_unit_id,
                    "status": "unresolved",
                    "review_rounds": 0,
                    "revised": False,
                    "error": f"review_worker_exception: {exc}",
                }
            results.append(result)
            completed_count += 1
            print(
                f"[{completed_count}/{len(cases)}] review {result['status']} {case.directory_name} "
                f"rounds={result.get('review_rounds', 0)} revised={result.get('revised', False)}",
                flush=True,
            )
    by_id = {str(result["case_unit_id"]): result for result in results}
    return [by_id[case.case_unit_id] for case in cases]


def _resolve_declared_path(value: Any, *, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise DraftReviewLifecycleError(f"{field} must be a non-empty path")
    path = Path(value)
    return (path if path.is_absolute() else PACKAGE_ROOT / path).resolve()


def _require_current_binding(
    receipt: Mapping[str, Any],
    *,
    path_field: str,
    hash_field: str,
    expected_path: Path,
    context: str,
) -> None:
    declared = _resolve_declared_path(receipt.get(path_field), field=f"{context}.{path_field}")
    expected = expected_path.resolve()
    if declared != expected:
        raise DraftReviewLifecycleError(
            f"{context} {path_field} is stale: expected={_display(expected)}, actual={_display(declared)}"
        )
    if receipt.get(hash_field) != _sha256_file(expected):
        raise DraftReviewLifecycleError(f"{context} {hash_field} is stale")


def _validate_generation_receipt(
    args: argparse.Namespace,
    *,
    case: CaseInput,
    case_dir: Path,
    config_sha256: str,
    input_lock_sha256: str,
) -> dict[str, Any]:
    receipt_path = case_dir / "generation.json"
    receipt = _load_mapping(receipt_path)
    required_values = {
        "schema_version": "case_checklist_generation/v1",
        "case_unit_id": case.case_unit_id,
        "case_packet_sha256": _sha256_file(case.case_packet_path),
        "composed_draft_prompt_sha256": _sha256_file(args.composed_draft_prompt),
        "checklist_schema_sha256": _sha256_file(args.checklist_schema),
        "resolved_config_sha256": config_sha256,
        "input_lock_sha256": input_lock_sha256,
        "provider": "codex_cli",
        "auth_mode": "codex_login",
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
    }
    for field, expected in required_values.items():
        if receipt.get(field) != expected:
            raise DraftReviewLifecycleError(
                f"generation receipt field drift for {case.case_unit_id}: {field}"
            )
    for path_field, hash_field, expected_path in (
        ("case_packet_path", "case_packet_sha256", case.case_packet_path),
        ("checklist_path", "checklist_sha256", case_dir / "generated_checklist.yaml"),
        ("checklist_json_path", "checklist_json_sha256", case_dir / "generated_checklist.json"),
        ("llm_call_path", "llm_call_sha256", case_dir / "llm_call.json"),
        ("api_response_path", "api_response_sha256", case_dir / "api_response.json"),
        ("reasoning_summary_path", "reasoning_summary_sha256", case_dir / "reasoning_summary.txt"),
        ("composed_draft_prompt_path", "composed_draft_prompt_sha256", args.composed_draft_prompt),
        ("checklist_schema_path", "checklist_schema_sha256", args.checklist_schema),
    ):
        _require_current_binding(
            receipt,
            path_field=path_field,
            hash_field=hash_field,
            expected_path=expected_path,
            context=f"generation receipt for {case.case_unit_id}",
        )
    llm_call = _load_mapping(case_dir / "llm_call.json")
    if (
        llm_call.get("schema_version") != "llm_call/v1"
        or llm_call.get("provider") != "codex_cli"
        or llm_call.get("case_unit_id") != case.case_unit_id
        or llm_call.get("model") != args.model
    ):
        raise DraftReviewLifecycleError(f"generation llm_call binding failed: {case.case_unit_id}")
    response_metadata = llm_call.get("response_metadata")
    if not isinstance(response_metadata, Mapping):
        raise DraftReviewLifecycleError(f"generation response metadata missing: {case.case_unit_id}")
    if (
        response_metadata.get("auth_mode") != "codex_login"
        or response_metadata.get("reasoning_effort") != args.reasoning_effort
        or response_metadata.get("max_output_tokens_enforced") is not False
    ):
        raise DraftReviewLifecycleError(f"generation Codex configuration drift: {case.case_unit_id}")
    return receipt


def _validate_final_outputs(
    args: argparse.Namespace,
    cases: Sequence[CaseInput],
    *,
    config_sha256: str,
    input_lock_sha256: str,
    codex_version: str,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    output_root = _active_output_root(args)
    expected_dirs = {case.directory_name for case in cases}
    actual_dirs = {path.name for path in output_root.iterdir() if path.is_dir()}
    if actual_dirs != expected_dirs:
        raise DraftReviewLifecycleError(
            "draft directory set mismatch: "
            f"missing={sorted(expected_dirs - actual_dirs)[:10]}, "
            f"extra={sorted(actual_dirs - expected_dirs)[:10]}"
        )

    checklist_schema = _load_mapping(args.checklist_schema)
    review_schema = _load_mapping(args.review_schema)
    reviewer_config = _reviewer_config(args, codex_version)
    entries: list[dict[str, Any]] = []
    unresolved: list[dict[str, str]] = []
    for case in cases:
        case_dir = output_root / case.directory_name
        try:
            checklist_path = case_dir / "checklist.yaml"
            checklist_json_path = case_dir / "checklist.json"
            checklist, deterministic = _validate_checklist(
                checklist_path,
                case=case,
                schema=checklist_schema,
            )
            if deterministic != {"status": "pass", "findings": []}:
                raise DraftReviewLifecycleError(
                    f"deterministic review is not clean for {case.case_unit_id}"
                )
            checklist_json = _load_mapping(checklist_json_path)
            if checklist_json != checklist:
                raise DraftReviewLifecycleError(
                    f"final checklist YAML/JSON semantic mismatch: {case.case_unit_id}"
                )
            generation = _validate_generation_receipt(
                args,
                case=case,
                case_dir=case_dir,
                config_sha256=config_sha256,
                input_lock_sha256=input_lock_sha256,
            )
            if not _reusable_review(
                args,
                case=case,
                case_dir=case_dir,
                checklist_schema=checklist_schema,
                review_schema=review_schema,
                reviewer_config=reviewer_config,
            ):
                raise DraftReviewLifecycleError(
                    f"accepted current review receipt missing: {case.case_unit_id}"
                )
            lifecycle_path = case_dir / "review_lifecycle.json"
            lifecycle = _load_mapping(lifecycle_path)
            review_path = case_dir / "review.json"
            if (
                lifecycle.get("schema_version") != "case_checklist_review_lifecycle/v1"
                or lifecycle.get("case_unit_id") != case.case_unit_id
                or lifecycle.get("status") != "accepted"
                or lifecycle.get("final_checklist_sha256") != _sha256_file(checklist_path)
                or lifecycle.get("final_review_sha256") != _sha256_file(review_path)
            ):
                raise DraftReviewLifecycleError(
                    f"review lifecycle receipt is stale: {case.case_unit_id}"
                )
            entries.append(
                {
                    "case_unit_id": case.case_unit_id,
                    "task_id": case.task_id,
                    "suite": case.suite,
                    "case_packet_path": _display(case.case_packet_path),
                    "case_packet_sha256": _sha256_file(case.case_packet_path),
                    "generated_checklist_path": generation["checklist_path"],
                    "generated_checklist_sha256": generation["checklist_sha256"],
                    "generation_receipt_path": _display(case_dir / "generation.json"),
                    "generation_receipt_sha256": _sha256_file(case_dir / "generation.json"),
                    "checklist_path": _display(checklist_path),
                    "checklist_sha256": _sha256_file(checklist_path),
                    "checklist_json_path": _display(checklist_json_path),
                    "checklist_json_sha256": _sha256_file(checklist_json_path),
                    "review_path": _display(review_path),
                    "review_sha256": _sha256_file(review_path),
                    "review_lifecycle_path": _display(lifecycle_path),
                    "review_lifecycle_sha256": _sha256_file(lifecycle_path),
                    "revised": bool(lifecycle.get("revised")),
                    "review_rounds": int(lifecycle.get("review_rounds") or 0),
                }
            )
        except Exception as exc:
            unresolved.append({"case_unit_id": case.case_unit_id, "error": str(exc)})
    return entries, unresolved


def _run_batch_lock(args: argparse.Namespace) -> dict[str, Any]:
    command = [
        sys.executable,
        str(BATCH_LOCK_SCRIPT),
        "--manifest",
        str(args.manifest),
        "--source-bundle",
        str(args.source_bundle),
        "--case-packet-root",
        str(args.case_packet_root),
        "--draft-root",
        str(args.output_root),
        "--lock-file",
        str(args.case_lock_file),
        "--acceptance-output",
        str(args.lock_acceptance),
        "--expected-count",
        str(EXPECTED_CASES),
        "--draft-prompt",
        str(args.composed_draft_prompt),
        "--score-prompt",
        str(args.score_prompt),
        "--review-prompt",
        str(args.review_prompt),
        "--checklist-schema",
        str(args.checklist_schema),
        "--score-schema",
        str(args.score_schema),
        "--review-schema",
        str(args.review_schema),
        "--json",
    ]
    completed = subprocess.run(
        command,
        cwd=PACKAGE_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "batch lock failed").strip()
        raise DraftReviewLifecycleError(
            f"batch case lock exited with status {completed.returncode}: {detail[-4000:]}"
        )
    acceptance = _load_mapping(args.lock_acceptance)
    expected_counts = {
        "manifest_cases": EXPECTED_CASES,
        "source_entries": EXPECTED_CASES,
        "case_packets": EXPECTED_CASES,
        "valid_drafts": EXPECTED_CASES,
        "reviewed": EXPECTED_CASES,
        "locked": EXPECTED_CASES,
        "unresolved_drafts": 0,
    }
    if (
        acceptance.get("schema_version") != "agentdojo_case_checklist_lock_acceptance/v1"
        or acceptance.get("status") != "accepted"
        or acceptance.get("expected_count") != EXPECTED_CASES
        or acceptance.get("counts") != expected_counts
        or acceptance.get("lock_file_sha256") != _sha256_file(args.case_lock_file)
        or acceptance.get("unresolved_drafts") != []
    ):
        raise DraftReviewLifecycleError("batch case lock acceptance failed strict readback")
    return acceptance


def _publish_timestamped_definition(
    path: Path,
    definition: Mapping[str, Any],
    *,
    timestamp_field: str,
) -> str:
    if path.exists():
        existing = _load_mapping(path)
        comparable = dict(existing)
        comparable.pop(timestamp_field, None)
        if comparable != dict(definition):
            raise DraftReviewLifecycleError(f"frozen definition drift detected: {path}")
    else:
        _write_json(path, {**definition, timestamp_field: _now()})
    return _sha256_file(path)


def _prepare_paths(args: argparse.Namespace) -> None:
    for field in (
        "manifest",
        "source_bundle",
        "case_packet_root",
        "output_root",
        "base_draft_prompt",
        "composed_draft_prompt",
        "checklist_schema",
        "review_prompt",
        "review_schema",
        "score_prompt",
        "score_schema",
        "resolved_config",
        "input_lock",
        "budget_plan",
        "report",
        "index",
        "case_lock_file",
        "lock_acceptance",
    ):
        setattr(args, field, getattr(args, field).expanduser().resolve())
    if args.canary:
        root = args.output_root.parent / "_canary_provenance"
        args.composed_draft_prompt = root / "agentdojo_full_draft_prompt.md"
        args.resolved_config = root / "draft_review_config.json"
        args.input_lock = root / "draft_input_lock.json"
        args.budget_plan = root / "draft_budget_plan.json"
        args.report = root / "draft_review_report.json"
        args.index = root / "draft_review_index.json"
        args.case_lock_file = root / "case_checklist_locks.jsonl"
        args.lock_acceptance = root / "case_checklist_lock_acceptance.json"


def _validate_args(args: argparse.Namespace) -> None:
    if args.max_parallel != 6:
        raise DraftReviewLifecycleError(
            f"strict full lifecycle requires exactly 6 workers, got {args.max_parallel}"
        )
    if args.max_review_rounds < 2:
        raise DraftReviewLifecycleError(
            "max-review-rounds must be at least 2 so every revision can receive a fresh review"
        )
    if args.codex_timeout_seconds <= 0:
        raise DraftReviewLifecycleError("codex-timeout-seconds must be positive")
    if args.force_generation and args.skip_generation:
        raise DraftReviewLifecycleError("--force-generation and --skip-generation are mutually exclusive")
    if args.model != "gpt-5.6-sol":
        raise DraftReviewLifecycleError("the frozen full experiment model is gpt-5.6-sol")
    if args.reasoning_effort != "xhigh" or args.codex_sandbox != "read-only":
        raise DraftReviewLifecycleError(
            "the frozen full experiment requires reasoning_effort=xhigh and sandbox=read-only"
        )
    for path in (
        args.manifest,
        args.source_bundle,
        args.base_draft_prompt,
        args.checklist_schema,
        args.review_prompt,
        args.review_schema,
        args.score_prompt,
        args.score_schema,
    ):
        if not path.is_file():
            raise DraftReviewLifecycleError(f"required lifecycle input missing: {path}")
    if not args.case_packet_root.is_dir():
        raise DraftReviewLifecycleError(f"case packet root missing: {args.case_packet_root}")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        _prepare_paths(args)
        _validate_args(args)
        cases = _manifest_cases(args.manifest, args.case_packet_root)
        _validate_source_bundle(args.source_bundle, cases)
        selected = _selected_cases(cases, args.canary)
        codex_version, login_status = _codex_preflight()
        config = _build_config(args, codex_version)
        config_sha256 = _publish_or_verify_config(args.resolved_config, config)
        input_definition = _input_lock_definition(
            args,
            cases,
            config_sha256=config_sha256,
        )
        input_lock_sha256 = _publish_or_verify_input_lock(args.input_lock, input_definition)
        budget_definition = _budget_plan(args, input_lock_sha256=input_lock_sha256)
        budget_definition.pop("planned_at", None)
        budget_sha256 = _publish_timestamped_definition(
            args.budget_plan,
            budget_definition,
            timestamp_field="planned_at",
        )
        plan = {
            "mode": "canary" if args.canary else "full",
            "selected_cases": len(selected),
            "full_denominator": EXPECTED_CASES,
            "max_parallel": args.max_parallel,
            "model": args.model,
            "reasoning_effort": args.reasoning_effort,
            "codex_cli_version": codex_version,
            "codex_login_status": login_status,
            "resolved_config_sha256": config_sha256,
            "input_lock_sha256": input_lock_sha256,
            "budget_plan_sha256": budget_sha256,
            "output_root": _display(_active_output_root(args)),
        }
        print(json.dumps(plan, ensure_ascii=False, sort_keys=True), flush=True)
        if args.plan_only:
            return 0

        run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        started_at = _now()
        if not args.skip_generation:
            _run_generation(args, selected)
        _validate_generated_cases(
            args,
            selected,
            config_sha256=config_sha256,
            input_lock_sha256=input_lock_sha256,
        )
        review_results = _review_cases(
            args,
            selected,
            codex_version=codex_version,
            run_id=run_id,
        )
        entries, unresolved = _validate_final_outputs(
            args,
            selected,
            config_sha256=config_sha256,
            input_lock_sha256=input_lock_sha256,
            codex_version=codex_version,
        )
        counts = {
            "case_packets": len(selected),
            "source_entries": len(selected),
            "valid_drafts": len(entries),
            "reviewed": len(entries),
            "lock_eligible": len(entries),
            "locked": 0,
            "unresolved_drafts": len(unresolved),
        }
        report = {
            "schema_version": "agentdojo_draft_review_report/v1",
            "mode": "canary" if args.canary else "full",
            "run_id": run_id,
            "started_at": started_at,
            "finished_at": _now(),
            "full_denominator": EXPECTED_CASES,
            "selected_case_count": len(selected),
            "max_parallel": args.max_parallel,
            "resolved_config_sha256": config_sha256,
            "input_lock_sha256": input_lock_sha256,
            "budget_plan_sha256": budget_sha256,
            "counts": counts,
            "review_results": review_results,
            "unresolved_drafts": unresolved,
        }
        _write_json(args.report, report)
        if unresolved or len(entries) != len(selected):
            print(
                f"strict lifecycle incomplete: accepted={len(entries)}/{len(selected)} "
                f"unresolved={len(unresolved)}; see {_display(args.report)}",
                file=sys.stderr,
            )
            return 2

        index_definition = {
            "schema_version": "agentdojo_draft_review_index/v1",
            "mode": "canary" if args.canary else "full",
            "case_count": len(entries),
            "full_denominator": EXPECTED_CASES,
            "case_id_order_sha256": _sha256_object([entry["case_unit_id"] for entry in entries]),
            "case_id_set_sha256": _sha256_object(sorted(entry["case_unit_id"] for entry in entries)),
            "entries_sha256": _sha256_object(entries),
            "resolved_config_sha256": config_sha256,
            "input_lock_sha256": input_lock_sha256,
            "entries": entries,
        }
        index_sha256 = _publish_timestamped_definition(
            args.index,
            index_definition,
            timestamp_field="frozen_at",
        )
        if not args.canary:
            _run_batch_lock(args)
            counts["locked"] = EXPECTED_CASES
            report["lock_file_path"] = _display(args.case_lock_file)
            report["lock_file_sha256"] = _sha256_file(args.case_lock_file)
            report["lock_acceptance_path"] = _display(args.lock_acceptance)
            report["lock_acceptance_sha256"] = _sha256_file(args.lock_acceptance)
            report["status"] = "accepted_and_locked"
        else:
            report["status"] = "canary_accepted"
        report["index_path"] = _display(args.index)
        report["index_sha256"] = index_sha256
        report["counts"] = counts
        _write_json(args.report, report)
        print(
            f"strict lifecycle accepted: valid={len(entries)} reviewed={len(entries)} "
            f"locked={counts['locked']} unresolved=0 index={_display(args.index)}",
            flush=True,
        )
        return 0
    except DraftReviewLifecycleError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
