#!/usr/bin/env python3
"""Independently review one AgentDojo checklist with an authenticated Codex CLI.

The CLI emits a validated model-review body plus raw Codex sidecars. A separate
orchestrator is responsible for deterministic checks, revisions, and the canonical
``case_checklist_model_review/v1`` receipt.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml
from jsonschema import Draft202012Validator


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
DEFAULT_REVIEW_PROMPT = ROOT_DIR / "prompts" / "review_agentdojo_full_checklist.prompt.md"
DEFAULT_REVIEW_SCHEMA = ROOT_DIR / "schemas" / "case_checklist_review.schema.json"
DEFAULT_MODEL = "gpt-5.6-sol"
DEFAULT_REASONING_EFFORT = "xhigh"
DEFAULT_TIMEOUT_SECONDS = 1800
REVIEW_ITEM_IDS = (
    "identity_and_scope",
    "native_user_goal",
    "native_evaluator_semantics",
    "paired_arm_composition",
    "decisive_post_run_evidence",
    "source_support_pointers",
    "stronger_conditions",
    "schema_guardrail_minimality",
)


class ChecklistModelReviewError(RuntimeError):
    """Raised when a model review cannot be produced or fails validation."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_packet", type=Path, help="Path to case_packet.md")
    parser.add_argument("checklist", type=Path, help="Path to checklist.yaml")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Model-review body JSON")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Codex model (default: {DEFAULT_MODEL})")
    parser.add_argument(
        "--reasoning-effort",
        default=DEFAULT_REASONING_EFFORT,
        choices=["minimal", "low", "medium", "high", "xhigh"],
        help=f"Codex reasoning effort (default: {DEFAULT_REASONING_EFFORT})",
    )
    parser.add_argument(
        "--codex-timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Hard Codex subprocess timeout (default: {DEFAULT_TIMEOUT_SECONDS})",
    )
    parser.add_argument(
        "--codex-sandbox",
        default="read-only",
        choices=["read-only"],
        help="Codex sandbox; model review is always read-only",
    )
    parser.add_argument(
        "--review-prompt",
        type=Path,
        default=DEFAULT_REVIEW_PROMPT,
        help=f"Pinned review prompt (default: {DEFAULT_REVIEW_PROMPT})",
    )
    parser.add_argument(
        "--review-schema",
        type=Path,
        default=DEFAULT_REVIEW_SCHEMA,
        help=f"Canonical review schema (default: {DEFAULT_REVIEW_SCHEMA})",
    )
    parser.add_argument(
        "--review-item-ids",
        default=",".join(REVIEW_ITEM_IDS),
        help=(
            "Comma-separated review item ids in the exact order required from the model. "
            "Defaults to the canonical AgentDojo review profile."
        ),
    )
    parser.add_argument(
        "--experiment-type",
        default="agentdojo_full_extension",
        help="Experiment type recorded in the LLM sidecar.",
    )
    parser.add_argument(
        "--reviewer-role",
        default="case_checklist_model_reviewer",
        help="Reviewer role recorded in the LLM sidecar.",
    )
    return parser.parse_args()


def parse_review_item_ids(raw: str) -> tuple[str, ...]:
    item_ids = tuple(item.strip() for item in raw.split(",") if item.strip())
    if not item_ids:
        raise ChecklistModelReviewError("--review-item-ids must contain at least one id")
    if len(item_ids) != len(set(item_ids)):
        raise ChecklistModelReviewError("--review-item-ids must be unique")
    invalid = [item for item in item_ids if re.fullmatch(r"[a-z][a-z0-9_]*", item) is None]
    if invalid:
        raise ChecklistModelReviewError(
            "--review-item-ids must use lowercase snake_case: " + ", ".join(invalid)
        )
    return item_ids


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ChecklistModelReviewError(f"Failed to read {path}: {exc}") from exc


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(load_text(path))
    except json.JSONDecodeError as exc:
        raise ChecklistModelReviewError(f"Failed to parse JSON from {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ChecklistModelReviewError(f"Expected a JSON object in {path}")
    return payload


def load_checklist(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(load_text(path))
    except yaml.YAMLError as exc:
        raise ChecklistModelReviewError(f"Failed to parse checklist YAML {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ChecklistModelReviewError(f"Checklist must parse to an object: {path}")
    return payload


def extract_case_packet_metadata(case_packet_text: str) -> dict[str, str]:
    patterns = {
        "domain": r"-\s*domain:\s*`([^`]+)`",
        "case_unit_id": r"-\s*case_unit_id:\s*`([^`]+)`",
        "task_id": r"-\s*task_id:\s*`([^`]+)`",
    }
    metadata: dict[str, str] = {}
    for field, pattern in patterns.items():
        match = re.search(pattern, case_packet_text)
        if not match:
            raise ChecklistModelReviewError(f"Could not extract {field} from case packet")
        metadata[field] = match.group(1).strip()
    return metadata


def validate_input_identity(case_packet_text: str, checklist: Mapping[str, Any]) -> dict[str, str]:
    metadata = extract_case_packet_metadata(case_packet_text)
    for field in ("domain", "case_unit_id", "task_id"):
        actual = str(checklist.get(field) or "").strip()
        if actual != metadata[field]:
            raise ChecklistModelReviewError(
                f"Checklist {field} does not match case packet: {actual!r} != {metadata[field]!r}"
            )
    return metadata


def build_model_output_schema(
    full_schema: Mapping[str, Any],
    *,
    review_item_ids: tuple[str, ...] = REVIEW_ITEM_IDS,
) -> dict[str, Any]:
    """Build a provider-safe schema; revisions cross the boundary as JSON text."""
    definitions = full_schema.get("$defs")
    if not isinstance(definitions, dict) or not isinstance(definitions.get("ModelReviewBody"), dict):
        raise ChecklistModelReviewError("Review schema is missing $defs.ModelReviewBody")
    non_empty_string = {"type": "string", "minLength": 1}
    evidence = {
        "type": "array",
        "minItems": 1,
        "items": dict(non_empty_string),
    }
    review_item = {
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "status", "rationale", "evidence"],
        "properties": {
            "id": {"type": "string", "enum": list(review_item_ids)},
            "status": {"type": "string", "enum": ["pass", "fail"]},
            "rationale": dict(non_empty_string),
            "evidence": evidence,
        },
    }
    blocking_finding = {
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "checklist_item_id", "message", "required_change", "evidence"],
        "properties": {
            "id": dict(non_empty_string),
            "checklist_item_id": {"type": "string", "enum": list(review_item_ids)},
            "message": dict(non_empty_string),
            "required_change": dict(non_empty_string),
            "evidence": evidence,
        },
    }
    return {
        "$schema": full_schema.get("$schema", "https://json-schema.org/draft/2020-12/schema"),
        "type": "object",
        "additionalProperties": False,
        "required": [
            "decision",
            "checklist_items",
            "blocking_findings",
            "revised_checklist_json",
        ],
        "properties": {
            "decision": {"type": "string", "enum": ["accept", "revise"]},
            "checklist_items": {
                "type": "array",
                "minItems": len(review_item_ids),
                "maxItems": len(review_item_ids),
                "items": review_item,
            },
            "blocking_findings": {"type": "array", "items": blocking_finding},
            "revised_checklist_json": {"type": ["string", "null"]},
        },
    }


def normalize_provider_model_review(body: Mapping[str, Any]) -> dict[str, Any]:
    """Decode the transport-only revision JSON into the canonical review body."""
    materialized = dict(body)
    if "revised_checklist_json" not in materialized:
        raise ChecklistModelReviewError("Provider review body is missing revised_checklist_json")
    raw_revision = materialized.pop("revised_checklist_json")
    if raw_revision is not None:
        if not isinstance(raw_revision, str) or not raw_revision.strip():
            raise ChecklistModelReviewError("revised_checklist_json must be JSON text or null")
        try:
            revision = json.loads(raw_revision)
        except json.JSONDecodeError as exc:
            raise ChecklistModelReviewError(
                f"revised_checklist_json is not valid JSON: {exc}"
            ) from exc
        if not isinstance(revision, dict):
            raise ChecklistModelReviewError("revised_checklist_json must decode to an object")
        materialized["revised_checklist"] = revision
    return materialized


def _model_body_validation_schema(
    full_schema: Mapping[str, Any],
    *,
    review_item_ids: tuple[str, ...] = REVIEW_ITEM_IDS,
) -> dict[str, Any]:
    definitions = full_schema.get("$defs")
    if not isinstance(definitions, dict) or not isinstance(definitions.get("ModelReviewBody"), dict):
        raise ChecklistModelReviewError("Review schema is missing $defs.ModelReviewBody")
    schema = copy.deepcopy(definitions["ModelReviewBody"])
    schema["$schema"] = full_schema.get(
        "$schema", "https://json-schema.org/draft/2020-12/schema"
    )
    schema["$defs"] = copy.deepcopy(definitions)
    schema["properties"]["checklist_items"]["minItems"] = len(review_item_ids)
    schema["properties"]["checklist_items"]["maxItems"] = len(review_item_ids)
    schema["$defs"]["ReviewItemId"]["enum"] = list(review_item_ids)
    return schema


def validate_model_review_body(
    body: Mapping[str, Any],
    review_schema: Mapping[str, Any] | Path | str | None = None,
    *,
    review_item_ids: tuple[str, ...] = REVIEW_ITEM_IDS,
) -> dict[str, Any]:
    """Validate schema plus fail-closed decision, item, and revision invariants."""
    if not isinstance(body, Mapping):
        raise ChecklistModelReviewError("Model review body must be an object")
    if review_schema is None:
        full_schema = load_json(DEFAULT_REVIEW_SCHEMA)
    elif isinstance(review_schema, Mapping):
        full_schema = dict(review_schema)
    else:
        full_schema = load_json(Path(review_schema))

    materialized = dict(body)
    validator = Draft202012Validator(
        _model_body_validation_schema(full_schema, review_item_ids=review_item_ids)
    )
    errors = sorted(validator.iter_errors(materialized), key=lambda error: list(error.absolute_path))
    if errors:
        lines = ["Model review body failed schema validation:"]
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path) or "<root>"
            lines.append(f"- {location}: {error.message}")
        raise ChecklistModelReviewError("\n".join(lines))

    items = materialized.get("checklist_items")
    assert isinstance(items, list)  # schema-validated above
    item_ids = tuple(str(item.get("id") or "") for item in items if isinstance(item, dict))
    if item_ids != review_item_ids:
        raise ChecklistModelReviewError(
            "checklist_items must contain the exact review ids in canonical order: "
            + ", ".join(review_item_ids)
        )

    decision = materialized.get("decision")
    findings = materialized.get("blocking_findings")
    assert isinstance(findings, list)  # schema-validated above
    failed_ids = {
        str(item["id"])
        for item in items
        if isinstance(item, dict) and item.get("status") == "fail"
    }
    finding_item_ids = {
        str(finding["checklist_item_id"])
        for finding in findings
        if isinstance(finding, dict)
    }
    finding_ids = [str(finding["id"]) for finding in findings if isinstance(finding, dict)]
    if len(finding_ids) != len(set(finding_ids)):
        raise ChecklistModelReviewError("blocking_findings ids must be unique")

    has_revision = "revised_checklist" in materialized
    if decision == "accept":
        if failed_ids:
            raise ChecklistModelReviewError("accept requires all eight checklist items to pass")
        if findings:
            raise ChecklistModelReviewError("accept forbids blocking_findings")
        if has_revision:
            raise ChecklistModelReviewError("accept forbids revised_checklist")
    elif decision == "revise":
        if not failed_ids:
            raise ChecklistModelReviewError("revise requires at least one failed checklist item")
        if not findings:
            raise ChecklistModelReviewError("revise requires blocking_findings")
        if finding_item_ids != failed_ids:
            raise ChecklistModelReviewError(
                "revise requires blocking findings for exactly every failed checklist item"
            )
        if not has_revision:
            raise ChecklistModelReviewError("revise requires revised_checklist")
    else:  # pragma: no cover - schema owns the decision enum
        raise ChecklistModelReviewError(f"Unsupported review decision: {decision!r}")

    return materialized


def strip_null_fields(node: Any) -> Any:
    if isinstance(node, dict):
        return {
            key: strip_null_fields(value)
            for key, value in node.items()
            if value is not None
        }
    if isinstance(node, list):
        return [strip_null_fields(item) for item in node]
    return node


def build_codex_command(
    *,
    workspace_root: Path,
    schema_path: Path,
    output_path: Path,
    model: str,
    reasoning_effort: str,
    sandbox: str,
) -> list[str]:
    if sandbox != "read-only":
        raise ChecklistModelReviewError("Checklist model review requires sandbox=read-only")
    return [
        "codex",
        "exec",
        "--strict-config",
        "--disable",
        "shell_tool",
        "--disable",
        "unified_exec",
        "--cd",
        str(workspace_root),
        "--skip-git-repo-check",
        "--ephemeral",
        "--ignore-user-config",
        "--sandbox",
        "read-only",
        "--model",
        model,
        "-c",
        f'model_reasoning_effort="{reasoning_effort}"',
        "-c",
        'model_verbosity="low"',
        "--color",
        "never",
        "--json",
        "--output-schema",
        str(schema_path),
        "-o",
        str(output_path),
        "-",
    ]


def load_jsonl_objects(raw_text: str) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    malformed: list[str] = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            malformed.append(stripped)
            continue
        if isinstance(parsed, dict):
            events.append(parsed)
        else:
            malformed.append(stripped)
    return events, malformed


def recover_json_output_from_events(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for event in reversed(events):
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") != "agent_message":
            continue
        text = item.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def extract_reasoning_fragments(events: list[dict[str, Any]]) -> list[str]:
    fragments: list[str] = []
    for event in events:
        item = event.get("item")
        if not isinstance(item, dict) or str(item.get("type") or "").lower() != "reasoning":
            continue
        for key in ("text", "summary", "content"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                fragments.append(value.strip())
    return fragments


def normalize_codex_usage(events: list[dict[str, Any]]) -> dict[str, Any]:
    completed = next(
        (event for event in reversed(events) if event.get("type") == "turn.completed"),
        {},
    )
    usage = completed.get("usage") if isinstance(completed.get("usage"), dict) else {}
    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": int(usage.get("total_tokens", input_tokens + output_tokens) or 0),
        "input_tokens_details": {
            "cached_tokens": int(usage.get("cached_input_tokens", 0) or 0),
        },
        "output_tokens_details": {
            "reasoning_tokens": int(usage.get("reasoning_output_tokens", 0) or 0),
        },
    }


def call_codex_cli(
    *,
    case_packet_text: str,
    checklist_text: str,
    review_prompt_text: str,
    model_output_schema: Mapping[str, Any],
    model: str,
    reasoning_effort: str,
    codex_timeout_seconds: int,
    sandbox: str,
) -> dict[str, Any]:
    if shutil.which("codex") is None:
        raise ChecklistModelReviewError(
            "Could not find `codex` on PATH. Install Codex CLI and run `codex login` first."
        )
    if codex_timeout_seconds <= 0:
        raise ChecklistModelReviewError("--codex-timeout-seconds must be positive")

    with tempfile.TemporaryDirectory(prefix="case-checklist-review-codex-") as temp_dir:
        workspace_root = Path(temp_dir)
        (workspace_root / "case_packet.md").write_text(case_packet_text, encoding="utf-8")
        (workspace_root / "checklist.yaml").write_text(checklist_text, encoding="utf-8")
        (workspace_root / "review_prompt.md").write_text(review_prompt_text, encoding="utf-8")
        schema_path = workspace_root / "output_schema.json"
        output_path = workspace_root / "model_review.json"
        schema_path.write_text(
            json.dumps(model_output_schema, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        command = build_codex_command(
            workspace_root=workspace_root,
            schema_path=schema_path,
            output_path=output_path,
            model=model,
            reasoning_effort=reasoning_effort,
            sandbox=sandbox,
        )
        components = []
        for name, text in (
            ("review_prompt.md", review_prompt_text),
            ("case_packet.md", case_packet_text),
            ("checklist.yaml", checklist_text),
        ):
            encoded = text.encode("utf-8")
            components.append(
                {
                    "name": name,
                    "sha256": hashlib.sha256(encoded).hexdigest(),
                    "size_bytes": len(encoded),
                    "text": text,
                }
            )
        launch_prompt = json.dumps(
            {
                "schema_version": "case_checklist_model_review_stdin/v1",
                "policy": (
                    "The components below are the complete review boundary. "
                    "Read no other review inputs. Do not use tools."
                ),
                "instruction": (
                    "Read review_prompt.md completely, then case_packet.md and "
                    "checklist.yaml. Perform the independent semantic review and "
                    "return JSON only."
                ),
                "components": components,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ) + "\n"
        try:
            completed = subprocess.run(
                command,
                input=launch_prompt,
                capture_output=True,
                text=True,
                check=False,
                timeout=codex_timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            stderr = _subprocess_text(exc.stderr)
            raise ChecklistModelReviewError(
                f"Codex CLI timed out after {codex_timeout_seconds} seconds.\n{stderr.strip()}"
            ) from exc
        except OSError as exc:
            raise ChecklistModelReviewError(f"Failed to launch Codex CLI: {exc}") from exc

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        events, malformed_lines = load_jsonl_objects(stdout)
        if completed.returncode != 0:
            diagnostic_parts = []
            if stdout.strip():
                diagnostic_parts.append(f"stdout:\n{stdout.strip()}")
            if stderr.strip():
                diagnostic_parts.append(f"stderr:\n{stderr.strip()}")
            detail = "\n\n".join(diagnostic_parts) or "no diagnostic output"
            raise ChecklistModelReviewError(
                "Codex CLI model review failed. Confirm `codex login` and model access "
                f"(exit {completed.returncode}).\n{detail}"
            )

        parsed: dict[str, Any] | None = None
        if output_path.exists():
            try:
                candidate = json.loads(output_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ChecklistModelReviewError(
                    f"Codex CLI wrote invalid JSON to {output_path}: {exc}"
                ) from exc
            if isinstance(candidate, dict):
                parsed = candidate
        if parsed is None:
            parsed = recover_json_output_from_events(events)
        if parsed is None:
            raise ChecklistModelReviewError(
                "Codex CLI completed but produced no structured model-review object"
            )

        reasoning = extract_reasoning_fragments(events)
        thread_started = next(
            (event for event in events if event.get("type") == "thread.started"),
            {},
        )
        output_text = json.dumps(parsed, ensure_ascii=False)
        return {
            "id": thread_started.get("thread_id"),
            "status": "completed",
            "model": model,
            "provider": "codex_cli",
            "output_text": output_text,
            "output": [
                {
                    "type": "reasoning",
                    "summary": [{"type": "summary_text", "text": text} for text in reasoning],
                },
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": output_text}],
                },
            ],
            "usage": normalize_codex_usage(events),
            "codex_cli": {
                "auth_mode": "codex_login",
                "returncode": completed.returncode,
                "timeout_seconds": codex_timeout_seconds,
                "sandbox": sandbox,
                "ephemeral": True,
                "ignore_user_config": True,
                "model_verbosity": "low",
                "input_files": ["case_packet.md", "checklist.yaml", "review_prompt.md"],
                "command": command,
                "events": events,
                "malformed_event_lines": malformed_lines,
                "stderr": stderr,
            },
        }


def _subprocess_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def extract_json_text(api_response: Mapping[str, Any]) -> dict[str, Any]:
    output_text = api_response.get("output_text")
    if isinstance(output_text, str):
        try:
            parsed = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ChecklistModelReviewError(f"Codex model-review output is invalid JSON: {exc}") from exc
        if isinstance(parsed, dict):
            return parsed
    raise ChecklistModelReviewError("Codex response has no structured model-review object")


def extract_reasoning_summary(api_response: Mapping[str, Any]) -> str:
    chunks: list[str] = []
    output = api_response.get("output")
    if not isinstance(output, list):
        return ""
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "reasoning":
            continue
        summary = item.get("summary")
        if not isinstance(summary, list):
            continue
        for summary_item in summary:
            if isinstance(summary_item, dict):
                text = summary_item.get("text")
                if isinstance(text, str) and text.strip():
                    chunks.append(text.strip())
    return "\n\n".join(chunks)


def sidecar_paths_for_output(output_path: Path) -> dict[str, Path]:
    prefix = f"{output_path.stem}."
    return {
        "api_response": output_path.with_name(f"{prefix}api_response.json"),
        "llm_call": output_path.with_name(f"{prefix}llm_call.json"),
        "reasoning_summary": output_path.with_name(f"{prefix}reasoning_summary.txt"),
    }


def codex_cli_version() -> str:
    try:
        completed = subprocess.run(
            ["codex", "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ChecklistModelReviewError(f"Could not resolve Codex CLI version: {exc}") from exc
    version = (completed.stdout or completed.stderr or "").strip()
    if completed.returncode != 0 or not version:
        raise ChecklistModelReviewError("Could not resolve Codex CLI version")
    return version


def _token_usage(api_response: Mapping[str, Any]) -> dict[str, int]:
    usage = api_response.get("usage")
    usage = usage if isinstance(usage, dict) else {}
    input_details = usage.get("input_tokens_details")
    input_details = input_details if isinstance(input_details, dict) else {}
    output_details = usage.get("output_tokens_details")
    output_details = output_details if isinstance(output_details, dict) else {}
    return {
        "prompt_tokens": int(usage.get("input_tokens", 0) or 0),
        "completion_tokens": int(usage.get("output_tokens", 0) or 0),
        "cached_prompt_tokens": int(input_details.get("cached_tokens", 0) or 0),
        "reasoning_tokens": int(output_details.get("reasoning_tokens", 0) or 0),
        "total_tokens": int(usage.get("total_tokens", 0) or 0),
    }


def build_llm_call_record(
    *,
    api_response: Mapping[str, Any],
    metadata: Mapping[str, str],
    model: str,
    reasoning_effort: str,
    sandbox: str,
    timeout_seconds: int,
    request_timestamp: str,
    response_timestamp: str,
    raw_api_response_path: Path,
    reasoning_summary_path: Path,
    cli_version: str,
    experiment_type: str,
    reviewer_role: str,
) -> dict[str, Any]:
    return {
        "schema_version": "llm_call/v1",
        "provider": "codex_cli",
        "model": model,
        "model_version": model,
        "api_key_env": "CODEX_HOME",
        "domain": metadata["domain"],
        "case_unit_id": metadata["case_unit_id"],
        "task_id": metadata["task_id"],
        "phase": "checklist_model_review",
        "experiment_type": experiment_type,
        "agent_id_or_role": reviewer_role,
        "request_timestamp": request_timestamp,
        "response_timestamp": response_timestamp,
        "temperature": None,
        "max_tokens": None,
        "timeout_seconds": timeout_seconds,
        "retry_index": 0,
        "token_usage": _token_usage(api_response),
        "cost": {
            "amount": None,
            "currency": "USD",
            "cost_calculation_method": "unavailable",
            "missing_cost_reason": "codex_login_cost_unavailable",
            "total_cost_usd": None,
        },
        "response_metadata": {
            "response_id": api_response.get("id"),
            "response_status": api_response.get("status"),
            "provider_model": model,
            "reasoning_effort": reasoning_effort,
            "sandbox": sandbox,
            "auth_mode": "codex_login",
            "codex_cli_version": cli_version,
            "ephemeral": True,
            "ignore_user_config": True,
            "model_verbosity": "low",
            "raw_api_response_path": str(raw_api_response_path),
            "reasoning_summary_path": str(reasoning_summary_path),
        },
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    if args.codex_timeout_seconds <= 0:
        raise ChecklistModelReviewError("--codex-timeout-seconds must be positive")
    if args.codex_sandbox != "read-only":
        raise ChecklistModelReviewError("Checklist model review requires --codex-sandbox read-only")

    case_packet_text = load_text(args.case_packet)
    checklist_text = load_text(args.checklist)
    checklist = load_checklist(args.checklist)
    metadata = validate_input_identity(case_packet_text, checklist)
    review_prompt_text = load_text(args.review_prompt)
    full_schema = load_json(args.review_schema)
    review_item_ids = parse_review_item_ids(
        getattr(args, "review_item_ids", ",".join(REVIEW_ITEM_IDS))
    )
    model_output_schema = build_model_output_schema(
        full_schema,
        review_item_ids=review_item_ids,
    )
    sidecars = sidecar_paths_for_output(args.output)

    request_timestamp = utc_now_iso()
    api_response = call_codex_cli(
        case_packet_text=case_packet_text,
        checklist_text=checklist_text,
        review_prompt_text=review_prompt_text,
        model_output_schema=model_output_schema,
        model=args.model,
        reasoning_effort=args.reasoning_effort,
        codex_timeout_seconds=args.codex_timeout_seconds,
        sandbox=args.codex_sandbox,
    )
    response_timestamp = utc_now_iso()
    reasoning_summary = extract_reasoning_summary(api_response)
    cli_version = codex_cli_version()

    write_json(sidecars["api_response"], api_response)
    write_text(
        sidecars["reasoning_summary"],
        reasoning_summary + ("\n" if reasoning_summary else ""),
    )
    write_json(
        sidecars["llm_call"],
        build_llm_call_record(
            api_response=api_response,
            metadata=metadata,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            sandbox=args.codex_sandbox,
            timeout_seconds=args.codex_timeout_seconds,
            request_timestamp=request_timestamp,
            response_timestamp=response_timestamp,
            raw_api_response_path=sidecars["api_response"],
            reasoning_summary_path=sidecars["reasoning_summary"],
            cli_version=cli_version,
            experiment_type=getattr(args, "experiment_type", "agentdojo_full_extension"),
            reviewer_role=getattr(args, "reviewer_role", "case_checklist_model_reviewer"),
        ),
    )

    body = strip_null_fields(
        normalize_provider_model_review(extract_json_text(api_response))
    )
    validated = validate_model_review_body(
        body,
        full_schema,
        review_item_ids=review_item_ids,
    )
    write_json(args.output, validated)
    print(f"model review valid: {args.output} [{validated['decision']}]")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ChecklistModelReviewError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
