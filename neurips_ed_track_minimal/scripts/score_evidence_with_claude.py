#!/usr/bin/env python3
"""Score stored evidence with Claude Code using its existing login state.

This is an opt-in secondary scorer.  It shares the locked prompt, schema,
released-label resolution, and deterministic guardrails with the canonical
Codex scorer, while keeping the Claude Code invocation read-only and isolated
from user/project customizations.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from neurips_ed_track_minimal.scripts import score_evidence_with_codex as common


DEFAULT_SCORE_MODEL = "sonnet"
DEFAULT_SCORE_REASONING_EFFORT = "high"
DEFAULT_CLAUDE_TIMEOUT_SECONDS = 1800
SCORER_NAME = "claude-code"
AUTH_MODE = "claude-code-login-state"
READ_ONLY_TOOLS = "Read,Glob,Grep"
API_AUTH_ENV_VARS = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_USE_FOUNDRY",
)


class ClaudeScoreError(RuntimeError):
    """Raised when the opt-in Claude Code scorer cannot produce a valid score."""


@dataclass(frozen=True)
class ClaudeRunResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    timeout_seconds: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checklist", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--native-label-path", type=Path, default=None)
    parser.add_argument("--out-prefix", type=Path, default=None)
    parser.add_argument("--model", default=DEFAULT_SCORE_MODEL)
    parser.add_argument(
        "--reasoning-effort",
        default=DEFAULT_SCORE_REASONING_EFFORT,
        choices=["low", "medium", "high", "xhigh", "max"],
    )
    parser.add_argument("--keep-workspace", type=Path, default=None)
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument(
        "--claude-timeout-seconds",
        type=int,
        default=DEFAULT_CLAUDE_TIMEOUT_SECONDS,
    )
    return parser.parse_args()


def claude_attempt_output_paths(out_prefix: Path, attempt: int) -> dict[str, Path]:
    attempt_prefix = out_prefix.parent / f"{out_prefix.name}.attempt_{attempt:02d}"
    return {
        "stdout": attempt_prefix.with_name(
            f"{attempt_prefix.name}.claude.stdout.log"
        ),
        "stderr": attempt_prefix.with_name(
            f"{attempt_prefix.name}.claude.stderr.log"
        ),
        "telemetry": attempt_prefix.with_name(
            f"{attempt_prefix.name}.claude.telemetry.json"
        ),
        "model_output": attempt_prefix.with_name(
            f"{attempt_prefix.name}.model_output.json"
        ),
    }


def build_claude_command(
    *,
    model_schema: dict[str, Any],
    prompt: str,
    model: str,
    reasoning_effort: str,
) -> list[str]:
    """Build a non-interactive, read-only Claude Code command.

    ``--safe-mode`` disables CLAUDE.md, hooks, plugins, MCP, skills, and other
    customizations while retaining the normal Claude Code authentication state.
    The tool allowlist prevents shell execution and workspace mutation.
    """

    return [
        "claude",
        "--print",
        "--model",
        model,
        "--effort",
        reasoning_effort,
        "--safe-mode",
        "--no-session-persistence",
        "--permission-mode",
        "dontAsk",
        "--tools",
        READ_ONLY_TOOLS,
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(model_schema, ensure_ascii=True, separators=(",", ":")),
        prompt,
    ]


def _subprocess_output_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def run_claude(
    *,
    workspace_root: Path,
    model_schema: dict[str, Any],
    prompt: str,
    model: str,
    reasoning_effort: str,
    claude_timeout_seconds: int,
) -> ClaudeRunResult:
    if shutil.which("claude") is None:
        raise ClaudeScoreError(
            "Could not find `claude` on PATH. Install Claude Code and run "
            "`claude login` before explicitly selecting the Claude scorer."
        )

    command = build_claude_command(
        model_schema=model_schema,
        prompt=prompt,
        model=model,
        reasoning_effort=reasoning_effort,
    )
    env = dict(os.environ)
    for name in API_AUTH_ENV_VARS:
        env.pop(name, None)
    try:
        completed = subprocess.run(
            command,
            cwd=str(workspace_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=claude_timeout_seconds,
        )
        return ClaudeRunResult(
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            timed_out=False,
            timeout_seconds=claude_timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return ClaudeRunResult(
            returncode=124,
            stdout=_subprocess_output_text(exc.stdout),
            stderr=_subprocess_output_text(exc.stderr),
            timed_out=True,
            timeout_seconds=claude_timeout_seconds,
        )
    except OSError as exc:
        raise ClaudeScoreError(f"Failed to launch Claude Code CLI: {exc}") from exc


def parse_claude_json_output(raw_stdout: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the schema-bound score and the Claude JSON result envelope."""

    try:
        envelope = json.loads(raw_stdout)
    except json.JSONDecodeError as exc:
        raise ClaudeScoreError(f"Claude Code did not return JSON output: {exc}") from exc
    if not isinstance(envelope, dict):
        raise ClaudeScoreError("Claude Code JSON output must be an object")
    if envelope.get("is_error") is True:
        raise ClaudeScoreError(
            f"Claude Code reported an error: {envelope.get('result') or 'unknown error'}"
        )

    structured = envelope.get("structured_output")
    if isinstance(structured, dict):
        return structured, envelope

    result = envelope.get("result")
    if isinstance(result, dict):
        return result, envelope
    if isinstance(result, str):
        candidate = result.strip()
        if candidate.startswith("```json") and candidate.endswith("```"):
            candidate = candidate[7:-3].strip()
        elif candidate.startswith("```") and candidate.endswith("```"):
            candidate = candidate[3:-3].strip()
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise ClaudeScoreError(
                "Claude Code result did not contain schema-bound JSON"
            ) from exc
        if isinstance(parsed, dict):
            return parsed, envelope

    raise ClaudeScoreError("Claude Code response has no structured_output object")


def build_claude_telemetry(
    *,
    envelope: dict[str, Any] | None,
    result: ClaudeRunResult,
    attempt: int,
) -> dict[str, Any]:
    envelope = envelope or {}
    return {
        "schema_version": "claude_code_score_telemetry_v1",
        "attempt": attempt,
        "provider": SCORER_NAME,
        "auth_mode": AUTH_MODE,
        "session_id": envelope.get("session_id"),
        "subtype": envelope.get("subtype"),
        "is_error": envelope.get("is_error"),
        "duration_ms": envelope.get("duration_ms"),
        "duration_api_ms": envelope.get("duration_api_ms"),
        "num_turns": envelope.get("num_turns"),
        "usage": envelope.get("usage"),
        "total_cost_usd": envelope.get("total_cost_usd"),
        "claude_exit": {
            "returncode": result.returncode,
            "timed_out": result.timed_out,
            "timeout_seconds": result.timeout_seconds,
        },
        "reasoning": {
            "available": False,
            "note": "Claude Code JSON mode does not expose hidden reasoning.",
        },
    }


def build_manifest(
    *,
    out_prefix: Path,
    checklist_path: Path,
    checklist: dict[str, Any],
    evidence_dir: Path,
    raw_run: dict[str, Any] | None,
    model: str,
    reasoning_effort: str,
    stdout_log_path: Path,
    stderr_log_path: Path,
    telemetry_path: Path,
) -> dict[str, Any]:
    manifest = common.build_score_manifest(
        out_prefix=out_prefix,
        checklist_path=checklist_path,
        checklist=checklist,
        evidence_dir=evidence_dir,
        raw_run=raw_run,
        model=model,
        reasoning_effort=reasoning_effort,
        service_tier="not-applicable",
        stdout_log_path=stdout_log_path,
        stderr_log_path=stderr_log_path,
        events_log_path=stdout_log_path,
        telemetry_path=telemetry_path,
        reasoning_path=telemetry_path,
    )
    manifest["scorer"] = SCORER_NAME
    manifest["auth_mode"] = AUTH_MODE
    manifest["outputs"] = {
        "json": str(out_prefix.with_suffix(".json").resolve()),
        "yaml": str(out_prefix.with_suffix(".yaml").resolve()),
        "manifest": str(common.manifest_output_path(out_prefix).resolve()),
        "claude_stdout_log": str(stdout_log_path.resolve()),
        "claude_stderr_log": str(stderr_log_path.resolve()),
        "claude_telemetry_json": str(telemetry_path.resolve()),
        "claude_attempt_files": [
            str(path.resolve())
            for path in sorted(out_prefix.parent.glob(f"{out_prefix.name}.attempt_*"))
            if path.is_file()
        ],
    }
    return manifest


def main() -> int:
    args = parse_args()
    if args.max_attempts < 1:
        raise ClaudeScoreError("--max-attempts must be at least 1")
    if args.claude_timeout_seconds < 1:
        raise ClaudeScoreError("--claude-timeout-seconds must be at least 1")

    common.enforce_formal_score_write_gate(
        out_prefix=args.out_prefix,
        checklist_path=args.checklist,
        evidence_dir=args.evidence_dir,
    )
    common.ensure_exists(args.checklist, "Checklist")
    common.ensure_exists(args.evidence_dir, "Evidence directory")
    if not args.evidence_dir.is_dir():
        raise ClaudeScoreError(f"Evidence path is not a directory: {args.evidence_dir}")
    if args.native_label_path is not None:
        common.ensure_exists(args.native_label_path, "Native label file")

    prompt_text = common.load_text(common.PROMPT_PATH)
    checklist = common.load_yaml(args.checklist)
    schema = common.load_json(common.SCHEMA_PATH)
    model_schema = common.build_model_output_schema(schema)
    raw_run = common.load_optional_raw_run(args.evidence_dir.resolve())
    released_evaluator_label = common.resolve_released_evaluator_label(
        evidence_dir=args.evidence_dir.resolve(),
        native_label_path=(
            args.native_label_path.resolve() if args.native_label_path else None
        ),
    )

    out_prefix = common.resolve_out_prefix(
        requested_out_prefix=args.out_prefix,
        score_output_root=None,
        checklist_path=args.checklist.resolve(),
        checklist=checklist,
        evidence_dir=args.evidence_dir.resolve(),
        raw_run=raw_run,
        model=args.model,
        reasoning_effort=args.reasoning_effort,
        scorer_name=SCORER_NAME,
    )
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    json_output_path = out_prefix.with_suffix(".json")
    yaml_output_path = out_prefix.with_suffix(".yaml")
    manifest_path = common.manifest_output_path(out_prefix)
    stdout_log_path = out_prefix.with_suffix(".claude.stdout.log")
    stderr_log_path = out_prefix.with_suffix(".claude.stderr.log")
    telemetry_path = out_prefix.with_suffix(".claude.telemetry.json")

    if args.keep_workspace is not None:
        workspace_root = args.keep_workspace.resolve()
        if workspace_root.exists():
            shutil.rmtree(workspace_root)
        common.stage_workspace(
            checklist_path=args.checklist.resolve(),
            evidence_dir=args.evidence_dir.resolve(),
            workspace_root=workspace_root,
        )
        temp_context = None
    else:
        temp_context = tempfile.TemporaryDirectory(prefix="claude_evidence_score_")
        workspace_root = Path(temp_context.name)
        common.stage_workspace(
            checklist_path=args.checklist.resolve(),
            evidence_dir=args.evidence_dir.resolve(),
            workspace_root=workspace_root,
        )

    prompt = common.build_prompt(prompt_text)
    validator = Draft202012Validator(schema)
    score: dict[str, Any] | None = None
    retry_note = ""
    common.clear_codex_attempt_outputs(out_prefix)

    try:
        for attempt in range(1, args.max_attempts + 1):
            if json_output_path.exists():
                json_output_path.unlink()

            attempt_prompt = prompt
            if retry_note:
                attempt_prompt = (
                    prompt.rstrip()
                    + "\n\nRetry correction:\n"
                    + retry_note.rstrip()
                    + "\nReturn a fully corrected JSON object.\n"
                )

            result = run_claude(
                workspace_root=workspace_root,
                model_schema=model_schema,
                prompt=attempt_prompt,
                model=args.model,
                reasoning_effort=args.reasoning_effort,
                claude_timeout_seconds=args.claude_timeout_seconds,
            )
            attempt_paths = claude_attempt_output_paths(out_prefix, attempt)
            common.write_text(stdout_log_path, result.stdout)
            common.write_text(stderr_log_path, result.stderr)
            common.write_text(attempt_paths["stdout"], result.stdout)
            common.write_text(attempt_paths["stderr"], result.stderr)

            envelope: dict[str, Any] | None = None
            model_score: dict[str, Any] | None = None
            parse_error: str | None = None
            if not result.timed_out and result.returncode == 0:
                try:
                    model_score, envelope = parse_claude_json_output(result.stdout)
                except ClaudeScoreError as exc:
                    parse_error = str(exc)

            telemetry = build_claude_telemetry(
                envelope=envelope,
                result=result,
                attempt=attempt,
            )
            if parse_error:
                telemetry["parse_error"] = parse_error
            common.write_json(telemetry_path, telemetry)
            common.write_json(attempt_paths["telemetry"], telemetry)

            if result.timed_out:
                retry_note = (
                    "Previous Claude Code attempt timed out. Read only the decisive "
                    "evidence and return the required JSON object directly."
                )
            elif result.returncode != 0:
                retry_note = (
                    f"Previous Claude Code attempt exited with status {result.returncode}. "
                    "Return one complete valid JSON result."
                )
            elif model_score is None:
                retry_note = parse_error or "Claude Code returned no structured JSON result."
            else:
                common.write_json(attempt_paths["model_output"], model_score)
                candidate = {
                    "schema_version": "evidence_score_v1",
                    "case_unit_id": checklist["case_unit_id"],
                    "released_evaluator_label": released_evaluator_label,
                    **model_score,
                }
                errors = sorted(
                    validator.iter_errors(candidate),
                    key=lambda error: list(error.absolute_path),
                )
                if errors:
                    lines = ["Claude Code output failed schema validation:"]
                    for error in errors:
                        path = ".".join(
                            str(part) for part in error.absolute_path
                        ) or "<root>"
                        lines.append(f"- {path}: {error.message}")
                    retry_note = "\n".join(lines)
                else:
                    try:
                        common.validate_score_guardrails(
                            candidate,
                            checklist,
                            workspace_root=workspace_root,
                        )
                    except common.CodexScoreError as exc:
                        retry_note = common.build_guardrail_retry_note(str(exc))
                    else:
                        score = candidate
                        break

            if attempt == args.max_attempts:
                raise ClaudeScoreError(retry_note)

        if score is None:
            raise ClaudeScoreError("Claude Code scoring did not produce a valid output")

        common.write_json(json_output_path, score)
        common.write_yaml(yaml_output_path, score)
        common.write_json(
            manifest_path,
            build_manifest(
                out_prefix=out_prefix,
                checklist_path=args.checklist.resolve(),
                checklist=checklist,
                evidence_dir=args.evidence_dir.resolve(),
                raw_run=raw_run,
                model=args.model,
                reasoning_effort=args.reasoning_effort,
                stdout_log_path=stdout_log_path,
                stderr_log_path=stderr_log_path,
                telemetry_path=telemetry_path,
            ),
        )
        return 0
    finally:
        if temp_context is not None:
            temp_context.cleanup()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ClaudeScoreError, common.CodexScoreError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
