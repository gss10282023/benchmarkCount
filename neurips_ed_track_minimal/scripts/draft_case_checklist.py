#!/usr/bin/env python3
"""Draft a compact case checklist from a case packet using an LLM provider.

The model is constrained with a JSON schema; the script then injects the top-level
case identifiers parsed from the packet and writes the final result as YAML.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

try:
    import requests
except ModuleNotFoundError:  # Codex-only drafting does not require HTTP support.
    requests = None  # type: ignore[assignment]


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
PACKAGE_ROOT = ROOT_DIR.parent
PROMPT_PATH = ROOT_DIR / "prompts" / "draft_case_checklist.prompt.md"
TEMPLATE_PATH = ROOT_DIR / "templates" / "case_checklist.template.yaml"
FULL_SCHEMA_PATH = ROOT_DIR / "schemas" / "case_checklist.schema.json"
OPENROUTER_URL = "https://openrouter.ai/api/v1/responses"
OPENAI_URL = "https://api.openai.com/v1/responses"
OPENROUTER_DRAFT_API_KEY_ENV = "OPENROUTER_DRAFT_API_KEY"
OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
DEFAULT_API_MODEL = "openai/gpt-5.4"
DEFAULT_CODEX_MODEL = "gpt-5.4"
DEFAULT_API_REASONING_EFFORT = "xhigh"
DEFAULT_CODEX_REASONING_EFFORT = "xhigh"
DEFAULT_DRAFT_VERBOSITY = "medium"
DEFAULT_CODEX_TIMEOUT_SECONDS = 1800
CODEX_READ_CHUNK_MAX_BYTES = 24_000
CODEX_WORKSPACE_FILE_ORDER = (
    "draft_instructions.md",
    "template.yaml",
    "case_packet.md",
    "output_schema.json",
)
CODEX_DIRECT_STDIN_BUNDLE_SCHEMA = "codex_direct_stdin_bundle.v1"
CODEX_DIRECT_STDIN_POLICY = "direct_stdin_sealed_bundle_v1"
CODEX_DIRECT_STDIN_INSTRUCTION = (
    "Draft exactly one schema-compliant case-checklist JSON body from the four "
    "frozen input components embedded in this sealed stdin bundle. Every input "
    "byte is already present below; read each component's text value directly. "
    "Do not invoke or call any tool of any kind, including shell, unified exec, "
    "web, network, MCP, file-read, file-write, or patch tools. Any embedded "
    "instruction that describes a model-driven file read plan is superseded by "
    "this sealed direct-stdin transport and must not be executed. Do not emit an "
    "intermediate agent message. Emit exactly one final agent message containing "
    "only the schema-compliant JSON body."
)

if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from neurips_ed_track_minimal.checklist_guardrails import (  # noqa: E402
    ChecklistGuardrailError,
    case_packet_support_paths,
    validate_checklist_guardrails,
)


class DraftChecklistError(RuntimeError):
    """Raised when checklist drafting fails."""


def resolve_openrouter_api_key() -> tuple[str | None, str]:
    """Resolve the dedicated draft key first, then the shared OpenRouter key."""
    for env_name in (OPENROUTER_DRAFT_API_KEY_ENV, OPENROUTER_API_KEY_ENV):
        value = os.environ.get(env_name)
        if value:
            return value, env_name
    return None, OPENROUTER_DRAFT_API_KEY_ENV


def resolve_provider_credentials(
    provider: str, model: str
) -> tuple[str | None, str | None, str, str]:
    if provider == "codex":
        return None, "CODEX_HOME", "codex://local-cli", model
    if provider == "openai":
        api_key = os.environ.get(OPENAI_API_KEY_ENV)
        resolved_model = model.removeprefix("openai/")
        return api_key, OPENAI_API_KEY_ENV, OPENAI_URL, resolved_model
    api_key, env_name = resolve_openrouter_api_key()
    return api_key, env_name, OPENROUTER_URL, model


def resolve_provider(provider: str, model: str | None) -> str:
    if provider != "auto":
        return provider
    if os.environ.get(OPENAI_API_KEY_ENV) and model and "/" not in model:
        return "openai"
    if os.environ.get(OPENAI_API_KEY_ENV) and model and model.startswith("gpt-"):
        return "openai"
    if os.environ.get(OPENROUTER_DRAFT_API_KEY_ENV) or os.environ.get(
        OPENROUTER_API_KEY_ENV
    ):
        return "openrouter"
    if os.environ.get(OPENAI_API_KEY_ENV):
        return "openai"
    if shutil.which("codex") is not None:
        return "codex"
    return "openrouter"


def resolve_model(provider: str, model: str | None) -> str:
    if model:
        return model
    return DEFAULT_CODEX_MODEL if provider == "codex" else DEFAULT_API_MODEL


def resolve_reasoning_effort(provider: str, reasoning_effort: str | None) -> str:
    if reasoning_effort:
        return reasoning_effort
    return (
        DEFAULT_CODEX_REASONING_EFFORT
        if provider == "codex"
        else DEFAULT_API_REASONING_EFFORT
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_packet", type=Path, help="Path to case_packet.md")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Where to write the final checklist YAML",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=(
            "Model id. Defaults to gpt-5.4 for Codex and "
            "openai/gpt-5.4 for API providers"
        ),
    )
    parser.add_argument(
        "--provider",
        default="auto",
        choices=["auto", "codex", "openai", "openrouter"],
        help="LLM provider to use (default: auto)",
    )
    parser.add_argument(
        "--reasoning-effort",
        default=None,
        choices=["minimal", "low", "medium", "high", "xhigh", "max"],
        help="Reasoning effort (default: xhigh for Codex and API providers)",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=12000,
        help="Max output tokens for the drafting response",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature",
    )
    parser.add_argument(
        "--http-timeout-seconds",
        type=int,
        default=180,
        help="HTTP timeout for the OpenRouter request",
    )
    parser.add_argument(
        "--codex-timeout-seconds",
        type=int,
        default=DEFAULT_CODEX_TIMEOUT_SECONDS,
        help=f"Codex CLI subprocess timeout (default: {DEFAULT_CODEX_TIMEOUT_SECONDS})",
    )
    parser.add_argument(
        "--codex-sandbox",
        default="read-only",
        choices=["read-only", "workspace-write", "danger-full-access"],
        help="Sandbox mode for the Codex draft session (default: read-only)",
    )
    parser.add_argument(
        "--prompt-supplement",
        type=Path,
        default=None,
        help="Optional instructions appended to the frozen base drafting prompt",
    )
    parser.add_argument(
        "--raw-json-output",
        type=Path,
        default=None,
        help="Optional path to also save the raw structured JSON output",
    )
    parser.add_argument(
        "--raw-api-response",
        type=Path,
        default=None,
        help="Optional path to save the full raw API response JSON",
    )
    return parser.parse_args()


def load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DraftChecklistError(f"Failed to read {path}: {exc}") from exc


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(load_text(path))
    except json.JSONDecodeError as exc:
        raise DraftChecklistError(f"Failed to parse JSON schema {path}: {exc}") from exc


def iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def extract_case_metadata(case_packet: str) -> dict[str, str]:
    patterns = {
        "domain": r"-\s*domain:\s*`([^`]+)`",
        "case_unit_id": r"-\s*case_unit_id:\s*`([^`]+)`",
        "task_id": r"-\s*task_id:\s*`([^`]+)`",
    }
    metadata: dict[str, str] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, case_packet)
        if not match:
            raise DraftChecklistError(
                f"Could not extract '{key}' from case packet. Expected a metadata line matching: {pattern}"
            )
        metadata[key] = match.group(1).strip()
    return metadata


def build_model_output_schema(full_schema: dict[str, Any]) -> dict[str, Any]:
    """Use only the body fields for model generation; inject top-level ids locally.

    OpenRouter/Azure structured outputs reject some JSON Schema constructs that are
    acceptable in our final local schema validator, notably `anyOf`/`oneOf` in nested
    object definitions. Strip those from the provider-facing schema and rely on the
    final local schema validation plus deterministic guardrails to enforce them.
    """

    def make_nullable(schema: dict[str, Any]) -> dict[str, Any]:
        if "$ref" in schema:
            return schema
        relaxed = copy.deepcopy(schema)
        schema_type = relaxed.get("type")
        if isinstance(schema_type, str):
            relaxed["type"] = [schema_type, "null"]
        elif isinstance(schema_type, list):
            if "null" not in schema_type:
                relaxed["type"] = [*schema_type, "null"]
        return relaxed

    def relax_provider_schema(node: Any) -> Any:
        if isinstance(node, dict):
            relaxed = {
                key: relax_provider_schema(value)
                for key, value in node.items()
                if key not in {"anyOf", "oneOf"}
            }
            if relaxed.get("type") == "object" and isinstance(
                relaxed.get("properties"), dict
            ):
                properties = relaxed["properties"]
                original_required = set(relaxed.get("required", []))
                for property_name, property_schema in list(properties.items()):
                    if property_name not in original_required and isinstance(
                        property_schema, dict
                    ):
                        properties[property_name] = make_nullable(property_schema)
                relaxed["required"] = list(properties.keys())
            return relaxed
        if isinstance(node, list):
            return [relax_provider_schema(item) for item in node]
        return node

    return relax_provider_schema(
        {
            "$schema": full_schema.get(
                "$schema", "https://json-schema.org/draft/2020-12/schema"
            ),
            "type": "object",
            "additionalProperties": False,
            "required": ["native", "stronger"],
            "properties": {
                "native": copy.deepcopy(full_schema["properties"]["native"]),
                "stronger": copy.deepcopy(full_schema["properties"]["stronger"]),
            },
            "$defs": copy.deepcopy(full_schema.get("$defs", {})),
        }
    )


def build_input_payload(
    prompt_text: str, template_text: str, case_packet_text: str
) -> str:
    return (
        "YAML template (naming guide only; ignore placeholder text):\n"
        "```yaml\n"
        f"{template_text.rstrip()}\n"
        "```\n\n"
        "Case packet:\n"
        "```markdown\n"
        f"{case_packet_text.rstrip()}\n"
        "```\n"
    )


def compose_prompt(base_prompt: str, supplement: str | None) -> str:
    if supplement is None or not supplement.strip():
        return base_prompt
    return f"{base_prompt.rstrip()}\n\n{supplement.strip()}\n"


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


def recover_json_output_from_events(
    events: list[dict[str, Any]],
) -> dict[str, Any] | None:
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


def extract_codex_reasoning_fragments(events: list[dict[str, Any]]) -> list[str]:
    fragments: list[str] = []
    for event in events:
        item = event.get("item")
        if (
            not isinstance(item, dict)
            or str(item.get("type") or "").lower() != "reasoning"
        ):
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
        "total_tokens": int(
            usage.get("total_tokens", input_tokens + output_tokens) or 0
        ),
        "input_tokens_details": {
            "cached_tokens": int(usage.get("cached_input_tokens", 0) or 0),
        },
        "output_tokens_details": {
            "reasoning_tokens": int(usage.get("reasoning_output_tokens", 0) or 0),
        },
    }


def build_codex_command(
    *,
    workspace_root: Path,
    schema_path: Path,
    output_path: Path,
    model: str,
    reasoning_effort: str,
    sandbox: str,
) -> list[str]:
    codex_executable = shutil.which("codex")
    if codex_executable is None:
        raise DraftChecklistError("Could not resolve the Codex CLI executable on PATH.")
    codex_executable = str(Path(codex_executable).resolve())
    return [
        codex_executable,
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
        sandbox,
        "--model",
        model,
        "-c",
        f'model_reasoning_effort="{reasoning_effort}"',
        "-c",
        f'model_verbosity="{DEFAULT_DRAFT_VERBOSITY}"',
        "--color",
        "never",
        "--json",
        "--output-schema",
        str(schema_path),
        "-o",
        str(output_path),
        "-",
    ]


def build_codex_workspace_files(
    *,
    instructions: str,
    template_text: str,
    case_packet_text: str,
    model_output_schema: dict[str, Any],
) -> dict[str, str]:
    """Return the exact four immutable files exposed to a Codex draft turn."""

    files = {
        "draft_instructions.md": instructions,
        "template.yaml": template_text,
        "case_packet.md": case_packet_text,
        "output_schema.json": (
            json.dumps(model_output_schema, indent=2, ensure_ascii=False) + "\n"
        ),
    }
    if tuple(files) != CODEX_WORKSPACE_FILE_ORDER:
        raise DraftChecklistError("Codex workspace file order drifted.")
    for name, text in files.items():
        if not text or "\r" in text or "\x00" in text:
            raise DraftChecklistError(
                f"Codex workspace input must be non-empty LF text: {name}"
            )
    return files


def build_codex_read_plan(workspace_files: dict[str, str]) -> list[dict[str, Any]]:
    """Build deterministic, bounded sed reads covering every workspace line."""

    if tuple(workspace_files) != CODEX_WORKSPACE_FILE_ORDER:
        raise DraftChecklistError("Codex read-plan workspace inventory/order drifted.")
    plan: list[dict[str, Any]] = []
    for name in CODEX_WORKSPACE_FILE_ORDER:
        text = workspace_files[name]
        lines = text.splitlines()
        if not lines:
            raise DraftChecklistError(f"Codex read-plan input has no lines: {name}")
        start = 1
        chunk_bytes = 0
        for line_number, line in enumerate(lines, start=1):
            rendered_size = len((line + "\n").encode("utf-8"))
            if (
                line_number > start
                and chunk_bytes + rendered_size > CODEX_READ_CHUNK_MAX_BYTES
            ):
                end = line_number - 1
                output = "".join(value + "\n" for value in lines[start - 1 : end])
                plan.append(
                    {
                        "file": name,
                        "start_line": start,
                        "end_line": end,
                        "command": f"sed -n '{start},{end}p' {name}",
                        "expected_output": output,
                    }
                )
                start = line_number
                chunk_bytes = 0
            chunk_bytes += rendered_size
        end = len(lines)
        output = "".join(value + "\n" for value in lines[start - 1 : end])
        plan.append(
            {
                "file": name,
                "start_line": start,
                "end_line": end,
                "command": f"sed -n '{start},{end}p' {name}",
                "expected_output": output,
            }
        )
    return plan


def build_codex_stdin_bundle(
    workspace_files: dict[str, str],
) -> tuple[str, dict[str, Any]]:
    """Seal all four frozen inputs into canonical stdin plus a text-free manifest."""

    if tuple(workspace_files) != CODEX_WORKSPACE_FILE_ORDER:
        raise DraftChecklistError("Codex stdin-bundle input inventory/order drifted.")
    components: list[dict[str, Any]] = []
    manifest_components: list[dict[str, Any]] = []
    for name in CODEX_WORKSPACE_FILE_ORDER:
        text = workspace_files[name]
        if not text or "\r" in text or "\x00" in text:
            raise DraftChecklistError(
                f"Codex stdin-bundle input must be non-empty LF text: {name}"
            )
        encoded = text.encode("utf-8")
        metadata = {
            "name": name,
            "sha256": hashlib.sha256(encoded).hexdigest(),
            "size_bytes": len(encoded),
            "line_count": len(text.splitlines()),
        }
        manifest_components.append(metadata)
        components.append({**metadata, "text": text})
    payload = {
        "schema_version": CODEX_DIRECT_STDIN_BUNDLE_SCHEMA,
        "policy": CODEX_DIRECT_STDIN_POLICY,
        "instruction": CODEX_DIRECT_STDIN_INSTRUCTION,
        "components": components,
    }
    stdin_text = (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    encoded_stdin = stdin_text.encode("utf-8")
    manifest = {
        "schema_version": CODEX_DIRECT_STDIN_BUNDLE_SCHEMA,
        "policy": CODEX_DIRECT_STDIN_POLICY,
        "total_sha256": hashlib.sha256(encoded_stdin).hexdigest(),
        "total_size_bytes": len(encoded_stdin),
        "components": manifest_components,
    }
    return stdin_text, manifest


def call_codex_cli(
    *,
    model: str,
    reasoning_effort: str,
    codex_timeout_seconds: int,
    sandbox: str,
    instructions: str,
    template_text: str,
    case_packet_text: str,
    model_output_schema: dict[str, Any],
) -> dict[str, Any]:
    if shutil.which("codex") is None:
        raise DraftChecklistError(
            "Could not find `codex` on PATH. Install Codex CLI and run `codex login` first."
        )

    with tempfile.TemporaryDirectory(prefix="case-checklist-codex-") as temp_dir:
        workspace_root = Path(temp_dir)
        schema_path = workspace_root / "output_schema.json"
        output_path = workspace_root / "draft_body.json"
        workspace_files = build_codex_workspace_files(
            instructions=instructions,
            template_text=template_text,
            case_packet_text=case_packet_text,
            model_output_schema=model_output_schema,
        )
        schema_path.write_text(workspace_files["output_schema.json"], encoding="utf-8")

        prompt, stdin_bundle_manifest = build_codex_stdin_bundle(workspace_files)
        command = build_codex_command(
            workspace_root=workspace_root,
            schema_path=schema_path,
            output_path=output_path,
            model=model,
            reasoning_effort=reasoning_effort,
            sandbox=sandbox,
        )
        timed_out = False
        timeout_stderr = ""
        timeout_stdout = ""
        try:
            completed = subprocess.run(
                command,
                input=prompt,
                capture_output=True,
                text=True,
                check=False,
                timeout=codex_timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            timeout_stdout = (
                exc.stdout.decode()
                if isinstance(exc.stdout, bytes)
                else (exc.stdout or "")
            )
            timeout_stderr = (
                exc.stderr.decode()
                if isinstance(exc.stderr, bytes)
                else (exc.stderr or "")
            )
            completed = subprocess.CompletedProcess(
                command,
                124,
                stdout=timeout_stdout,
                stderr=timeout_stderr,
            )
        except OSError as exc:
            raise DraftChecklistError(f"Failed to launch Codex CLI: {exc}") from exc

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        events, malformed_lines = load_jsonl_objects(stdout)

        parsed: dict[str, Any] | None = None
        parse_failed = False
        if completed.returncode == 0 and output_path.exists():
            try:
                candidate = json.loads(output_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                parse_failed = True
                candidate = None
            if isinstance(candidate, dict):
                parsed = candidate
        if completed.returncode == 0 and not parse_failed and parsed is None:
            parsed = recover_json_output_from_events(events)
        structured_output_missing = completed.returncode == 0 and parsed is None
        call_succeeded = (
            completed.returncode == 0
            and not timed_out
            and not parse_failed
            and not structured_output_missing
        )
        if parsed is None:
            parsed = {}

        reasoning_fragments = extract_codex_reasoning_fragments(events)
        thread_started = next(
            (event for event in events if event.get("type") == "thread.started"),
            {},
        )
        output_text = json.dumps(parsed, ensure_ascii=False)
        return {
            "id": thread_started.get("thread_id"),
            "status": "completed" if call_succeeded else "failed",
            "model": model,
            "provider": "codex_cli",
            "output_text": output_text,
            "output": [
                {
                    "type": "reasoning",
                    "summary": [
                        {"type": "summary_text", "text": text}
                        for text in reasoning_fragments
                    ],
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
                "command": command,
                "stdin_bundle": stdin_bundle_manifest,
                "events": events,
                "malformed_event_lines": malformed_lines,
                "stderr": stderr,
            },
        }


def call_responses_api(
    *,
    provider: str,
    api_url: str,
    api_key: str,
    model: str,
    reasoning_effort: str,
    max_output_tokens: int,
    temperature: float,
    http_timeout_seconds: int,
    instructions: str,
    input_text: str,
    model_output_schema: dict[str, Any],
) -> dict[str, Any]:
    if requests is None:
        raise DraftChecklistError(
            "HTTP drafting requires the optional `requests` dependency; "
            "use --provider codex or install requests."
        )
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "instructions": instructions,
        "input": input_text,
        "reasoning": {"effort": reasoning_effort},
        "max_output_tokens": max_output_tokens,
        "store": False,
        "text": {
            "verbosity": DEFAULT_DRAFT_VERBOSITY,
            "format": {
                "type": "json_schema",
                "name": "case_checklist_body",
                "strict": True,
                "schema": model_output_schema,
            },
        },
    }
    if provider != "openai":
        payload["temperature"] = temperature
    try:
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=http_timeout_seconds,
        )
    except requests.RequestException as exc:
        raise DraftChecklistError(f"OpenRouter request failed: {exc}") from exc

    if response.status_code >= 400:
        message = response.text.strip()
        raise DraftChecklistError(
            f"{provider} returned HTTP {response.status_code}. Response body:\n{message}"
        )

    try:
        return response.json()
    except json.JSONDecodeError as exc:
        raise DraftChecklistError(
            f"OpenRouter returned non-JSON content: {exc}"
        ) from exc


def extract_json_text(api_response: dict[str, Any]) -> dict[str, Any]:
    candidates: list[str] = []
    output_text = api_response.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        candidates.append(output_text)

    for item in api_response.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and isinstance(
                content.get("text"), str
            ):
                candidates.append(content["text"])

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed

    raise DraftChecklistError(
        "Could not parse structured JSON from the response. "
        "Inspect --raw-api-response output for debugging."
    )


def extract_reasoning_summary_text(api_response: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in api_response.get("output", []):
        if item.get("type") != "reasoning":
            continue
        for summary_item in item.get("summary", []):
            text = summary_item.get("text")
            if isinstance(text, str) and text.strip():
                chunks.append(text.strip())
    return "\n\n".join(chunks).strip()


def sidecar_paths_for_output(output_path: Path) -> dict[str, Path]:
    name = output_path.name
    if name.endswith("checklist.yaml"):
        prefix = name[: -len("checklist.yaml")]
    else:
        prefix = f"{output_path.stem}."
    return {
        "api_response": output_path.with_name(f"{prefix}api_response.json"),
        "llm_call": output_path.with_name(f"{prefix}llm_call.json"),
        "reasoning_summary": output_path.with_name(f"{prefix}reasoning_summary.txt"),
    }


def extract_token_usage(api_response: dict[str, Any]) -> dict[str, int]:
    usage = dict(api_response.get("usage") or {})
    output_details = dict(usage.get("output_tokens_details") or {})
    input_details = dict(usage.get("input_tokens_details") or {})
    return {
        "prompt_tokens": int(usage.get("input_tokens", 0) or 0),
        "completion_tokens": int(usage.get("output_tokens", 0) or 0),
        "cached_prompt_tokens": int(input_details.get("cached_tokens", 0) or 0),
        "reasoning_tokens": int(output_details.get("reasoning_tokens", 0) or 0),
        "total_tokens": int(usage.get("total_tokens", 0) or 0),
    }


def extract_cost_payload(api_response: dict[str, Any]) -> dict[str, Any]:
    usage = dict(api_response.get("usage") or {})
    total_cost = usage.get("cost")
    cost_details = usage.get("cost_details")
    if total_cost is None:
        return {
            "amount": None,
            "currency": "USD",
            "pricing_source": "provider_usage",
            "pricing_table_id": None,
            "pricing_table_version": None,
            "pricing_source_hash": None,
            "cost_calculation_method": "unavailable",
            "missing_cost_reason": "provider_cost_unavailable",
            "total_cost_usd": None,
            "cost_details": cost_details,
        }
    return {
        "amount": float(total_cost),
        "currency": "USD",
        "pricing_source": "provider_usage",
        "pricing_table_id": None,
        "pricing_table_version": None,
        "pricing_source_hash": None,
        "cost_calculation_method": "provider_reported",
        "missing_cost_reason": None,
        "total_cost_usd": float(total_cost),
        "cost_details": cost_details,
    }


def build_llm_call_record(
    *,
    api_response: dict[str, Any],
    api_key_env: str | None,
    case_metadata: dict[str, str],
    model: str,
    reasoning_effort: str,
    max_output_tokens: int,
    temperature: float,
    timeout_seconds: int,
    request_timestamp: str,
    response_timestamp: str,
    raw_api_response_path: Path,
    reasoning_summary_path: Path,
    provider: str = "openrouter",
) -> dict[str, Any]:
    response_model = str(api_response.get("model") or model)
    return {
        "schema_version": "llm_call/v1",
        "provider": provider,
        "model": model,
        "model_version": response_model,
        "api_key_env": api_key_env,
        "domain": case_metadata["domain"],
        "case_unit_id": case_metadata["case_unit_id"],
        "task_id": case_metadata["task_id"],
        "phase": "draft",
        "experiment_type": "minimal_package",
        "agent_id_or_role": "case_checklist_drafter",
        "request_timestamp": request_timestamp,
        "response_timestamp": response_timestamp,
        "temperature": temperature,
        "max_tokens": max_output_tokens,
        "timeout_seconds": timeout_seconds,
        "retry_index": 0,
        "token_usage": extract_token_usage(api_response),
        "cost": extract_cost_payload(api_response),
        "response_metadata": {
            "response_id": api_response.get("id"),
            "response_status": api_response.get("status"),
            "provider_model": response_model,
            "reasoning_effort": reasoning_effort,
            "model_verbosity": DEFAULT_DRAFT_VERBOSITY,
            "service_tier": api_response.get("service_tier"),
            "provider_created_at": api_response.get("created_at"),
            "provider_completed_at": api_response.get("completed_at"),
            "raw_api_response_path": str(raw_api_response_path),
            "reasoning_summary_path": str(reasoning_summary_path),
            "auth_mode": "codex_login" if provider == "codex_cli" else "api_key",
            "max_output_tokens_enforced": provider != "codex_cli",
        },
    }


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


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=1000)
    except OSError as exc:
        raise DraftChecklistError(f"Failed to write YAML to {path}: {exc}") from exc


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    except OSError as exc:
        raise DraftChecklistError(f"Failed to write JSON to {path}: {exc}") from exc


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise DraftChecklistError(f"Failed to write text to {path}: {exc}") from exc


def main() -> int:
    args = parse_args()
    provider = resolve_provider(args.provider, args.model)
    model = resolve_model(provider, args.model)
    reasoning_effort = resolve_reasoning_effort(provider, args.reasoning_effort)
    if args.codex_timeout_seconds <= 0:
        raise DraftChecklistError("--codex-timeout-seconds must be positive.")
    if args.http_timeout_seconds <= 0:
        raise DraftChecklistError("--http-timeout-seconds must be positive.")

    api_key, api_key_env, api_url, resolved_model = resolve_provider_credentials(
        provider, model
    )
    if provider != "codex" and not api_key:
        if provider == "openai":
            print(f"{OPENAI_API_KEY_ENV} is not set.", file=sys.stderr)
        else:
            print(
                f"Neither {OPENROUTER_DRAFT_API_KEY_ENV} nor {OPENROUTER_API_KEY_ENV} is set.",
                file=sys.stderr,
            )
        return 2

    case_packet_text = load_text(args.case_packet)
    metadata = extract_case_metadata(case_packet_text)
    prompt_supplement = (
        load_text(args.prompt_supplement)
        if args.prompt_supplement is not None
        else None
    )
    prompt_text = compose_prompt(load_text(PROMPT_PATH), prompt_supplement)
    template_text = load_text(TEMPLATE_PATH)
    full_schema = load_json(FULL_SCHEMA_PATH)
    model_schema = build_model_output_schema(full_schema)
    sidecar_paths = sidecar_paths_for_output(args.output)
    request_timestamp = iso_utc_now()

    if provider == "codex":
        api_response = call_codex_cli(
            model=resolved_model,
            reasoning_effort=reasoning_effort,
            codex_timeout_seconds=args.codex_timeout_seconds,
            sandbox=args.codex_sandbox,
            instructions=prompt_text,
            template_text=template_text,
            case_packet_text=case_packet_text,
            model_output_schema=model_schema,
        )
        call_provider = "codex_cli"
        timeout_seconds = args.codex_timeout_seconds
    else:
        assert api_key is not None
        api_response = call_responses_api(
            provider=provider,
            api_url=api_url,
            api_key=api_key,
            model=resolved_model,
            reasoning_effort=reasoning_effort,
            max_output_tokens=args.max_output_tokens,
            temperature=args.temperature,
            http_timeout_seconds=args.http_timeout_seconds,
            instructions=prompt_text,
            input_text=build_input_payload(
                prompt_text, template_text, case_packet_text
            ),
            model_output_schema=model_schema,
        )
        call_provider = provider
        timeout_seconds = args.http_timeout_seconds
    response_timestamp = iso_utc_now()

    auto_api_response_path = sidecar_paths["api_response"]
    write_json(auto_api_response_path, api_response)
    if (
        args.raw_api_response is not None
        and args.raw_api_response != auto_api_response_path
    ):
        write_json(args.raw_api_response, api_response)

    reasoning_summary_text = extract_reasoning_summary_text(api_response)
    write_text(
        sidecar_paths["reasoning_summary"],
        reasoning_summary_text + ("\n" if reasoning_summary_text else ""),
    )
    write_json(
        sidecar_paths["llm_call"],
        build_llm_call_record(
            provider=call_provider,
            api_response=api_response,
            api_key_env=api_key_env,
            case_metadata=metadata,
            model=resolved_model,
            reasoning_effort=reasoning_effort,
            max_output_tokens=args.max_output_tokens,
            temperature=args.temperature,
            timeout_seconds=timeout_seconds,
            request_timestamp=request_timestamp,
            response_timestamp=response_timestamp,
            raw_api_response_path=auto_api_response_path,
            reasoning_summary_path=sidecar_paths["reasoning_summary"],
        ),
    )

    if call_provider == "codex_cli" and api_response.get("status") != "completed":
        codex_record = dict(api_response.get("codex_cli") or {})
        returncode = codex_record.get("returncode")
        detail = str(codex_record.get("stderr") or "").strip() or "no diagnostic output"
        raise DraftChecklistError(
            "Codex CLI draft did not complete with structured JSON; failure events were "
            f"preserved in the attempt sidecars (exit {returncode}).\n{detail}"
        )

    body = strip_null_fields(extract_json_text(api_response))
    checklist = {
        "schema_version": "case_checklist_v1",
        "case_unit_id": metadata["case_unit_id"],
        "domain": metadata["domain"],
        "task_id": metadata["task_id"],
        **body,
    }

    validator = Draft202012Validator(full_schema)
    errors = sorted(
        validator.iter_errors(checklist), key=lambda e: list(e.absolute_path)
    )
    if errors:
        lines = ["Checklist failed schema validation:"]
        for err in errors:
            path = ".".join(str(p) for p in err.absolute_path) or "<root>"
            lines.append(f"- {path}: {err.message}")
        raise DraftChecklistError("\n".join(lines))

    try:
        validate_checklist_guardrails(
            checklist,
            allowed_source_paths=case_packet_support_paths(case_packet_text),
        )
    except ChecklistGuardrailError as exc:
        raise DraftChecklistError(str(exc)) from exc

    write_yaml(args.output, checklist)
    if args.raw_json_output is not None:
        write_json(args.raw_json_output, checklist)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DraftChecklistError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
