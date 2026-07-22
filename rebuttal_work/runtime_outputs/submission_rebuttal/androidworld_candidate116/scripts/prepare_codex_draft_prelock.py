#!/usr/bin/env python3
"""Create the honest pre-generation lock for the candidate116 Codex draft wave."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).resolve()
WORK_ROOT = SCRIPT.parents[1]
REPO_ROOT = WORK_ROOT.parents[3]
PACKET_ROOT = WORK_ROOT / "case_packets" / "androidworld"
DRAFT_ROOT = WORK_ROOT / "drafts"
DRAFT_LOG_ROOT = WORK_ROOT / "draft_logs"
GEN_ROOT = WORK_ROOT / "draft_generation"
CONFIG_DIR = GEN_ROOT / "config"
FREEZE_DIR = GEN_ROOT / "freeze"
VALIDATION_DIR = GEN_ROOT / "validation"
WAVE_ROOT = GEN_ROOT / "waves" / "wave_001"
OLD_INPUT_FREEZE = WORK_ROOT / "freeze" / "androidworld_candidate116_draft_input_freeze.json"
STATIC_REPORT = WORK_ROOT / "validation" / "strict_acceptance_report.json"
CASE_ORDER_SOURCE = WORK_ROOT / "freeze" / "androidworld_candidate116_draft_input_freeze.json"
CONFIG_PATH = CONFIG_DIR / "androidworld_candidate116_codex_cli_draft_config.json"
PRELOCK_PATH = FREEZE_DIR / "androidworld_candidate116_codex_cli_draft_prelock.json"
READONLY_BEFORE = VALIDATION_DIR / "pre_generation_readonly_snapshot.json"

NEURIPS = REPO_ROOT / "neurips_ed_track_minimal"
TOOL_PATHS = {
    "draft_prompt": NEURIPS / "prompts" / "draft_case_checklist.prompt.md",
    "draft_template": NEURIPS / "templates" / "case_checklist.template.yaml",
    "checklist_schema": NEURIPS / "schemas" / "case_checklist.schema.json",
    "checklist_guardrails": NEURIPS / "checklist_guardrails.py",
    "drafter": NEURIPS / "scripts" / "draft_case_checklist.py",
    "batch_runner": NEURIPS / "scripts" / "run_draft_batch.py",
    "validator": NEURIPS / "scripts" / "checklist_validator.py",
    "score_prompt": NEURIPS / "prompts" / "score_evidence_with_codex.prompt.md",
    "score_schema": NEURIPS / "schemas" / "evidence_score.schema.json",
    "compact_adapter": SCRIPT.with_name("draft_case_checklist_compact_adapter.py"),
    "compact_batch_runner": SCRIPT.with_name("run_compact_draft_batch.py"),
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def repo_path(path: Path) -> str:
    absolute = path if path.is_absolute() else (REPO_ROOT / path)
    try:
        return absolute.absolute().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return absolute.resolve().relative_to(REPO_ROOT).as_posix()


def command_output(command: list[str]) -> str:
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        fail(f"command failed ({result.returncode}): {' '.join(command)}\n{result.stderr}")
    return "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())


def load_builder_module() -> Any:
    module_path = SCRIPT.with_name("build_and_validate.py")
    sys.path.insert(0, str(module_path.parent))
    spec = importlib.util.spec_from_file_location("candidate116_builder_for_snapshot", module_path)
    if spec is None or spec.loader is None:
        fail(f"could not load builder module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--reasoning-effort", default="xhigh")
    parser.add_argument("--max-parallel", type=int, default=6)
    parser.add_argument("--codex-timeout-seconds", type=int, default=1800)
    parser.add_argument("--large-codex-timeout-seconds", type=int, default=3600)
    parser.add_argument("--token-budgets", default="12000,16000,20000")
    parser.add_argument("--large-case-threshold-bytes", type=int, default=180000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_parallel != 6:
        fail("candidate116 drafting policy requires exactly 6 concurrent workers")
    if PRELOCK_PATH.exists() or CONFIG_PATH.exists():
        fail("prelock/config already exists; refusing to rewrite a pre-generation declaration")
    if WAVE_ROOT.exists() and any(WAVE_ROOT.iterdir()):
        fail("wave_001 is not empty")
    if any(DRAFT_ROOT.rglob("*")) or any(DRAFT_LOG_ROOT.rglob("*")):
        fail("canonical drafts/draft_logs must remain empty before review and promotion")
    if load_json(STATIC_REPORT).get("status") != "pass":
        fail("static candidate116 strict acceptance is not pass")
    old_freeze = load_json(OLD_INPUT_FREEZE)
    if old_freeze.get("freeze_sha256") != "fe2018595bf1ef44de803fffe82c81dd55f5368b8fde47d1a10a7958bdd8a9e4":
        fail("unexpected packet/source input freeze")

    case_ids = list(old_freeze["case_order"]["case_unit_ids"])
    compact_inputs: list[dict[str, Any]] = []
    for rank, case_id in enumerate(case_ids):
        path = PACKET_ROOT / case_id / "compact_case_packet.md"
        if not path.is_file():
            fail(f"missing compact packet: {path}")
        compact_inputs.append(
            {
                "selection_rank": rank,
                "case_unit_id": case_id,
                "path": repo_path(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    if len(compact_inputs) != 116 or len({item["case_unit_id"] for item in compact_inputs}) != 116:
        fail("compact packet universe is not exactly 116 unique cases")

    codex_path_raw = shutil.which("codex")
    if not codex_path_raw:
        fail("codex CLI not found")
    codex_path = Path(codex_path_raw).resolve()
    login_status = command_output([codex_path_raw, "login", "status"])
    if "logged in" not in login_status.lower():
        fail(f"codex login is not active: {login_status}")
    codex_version = command_output([codex_path_raw, "--version"])

    for name, path in TOOL_PATHS.items():
        if not path.is_file():
            fail(f"missing tool binding {name}: {path}")
    tool_bindings = {
        name: {"path": repo_path(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
        for name, path in sorted(TOOL_PATHS.items())
    }

    runner_command = [
        repo_path(REPO_ROOT / ".venv" / "bin" / "python"),
        repo_path(TOOL_PATHS["compact_batch_runner"]),
        "--case-packet-root",
        repo_path(PACKET_ROOT),
        "--output-root",
        repo_path(WAVE_ROOT),
        "--provider",
        "codex",
        "--model",
        args.model,
        "--reasoning-effort",
        args.reasoning_effort,
        "--token-budgets",
        args.token_budgets,
        "--max-parallel",
        str(args.max_parallel),
        "--large-max-parallel",
        str(args.max_parallel),
        "--large-case-threshold-bytes",
        str(args.large_case_threshold_bytes),
        "--codex-timeout-seconds",
        str(args.codex_timeout_seconds),
        "--large-codex-timeout-seconds",
        str(args.large_codex_timeout_seconds),
        "--codex-sandbox",
        "read-only",
        "--quality-check",
        "none",
        "--sort-by",
        "name",
    ]
    config = {
        "schema_version": "androidworld_candidate116_codex_draft_config/v1",
        "status": "prelocked",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "provider": "codex_cli",
        "auth_mode": "codex_login",
        "codex_cli": {
            "path": str(codex_path),
            "binary_sha256": sha256_file(codex_path),
            "version_output": codex_version,
            "login_status_at_prelock": login_status,
        },
        "model": args.model,
        "model_version_claim": None,
        "model_version_note": "Codex CLI exposes the requested model id but no immutable backend snapshot id.",
        "reasoning_effort": args.reasoning_effort,
        "model_verbosity": "low",
        "sandbox": "read-only",
        "ephemeral": True,
        "ignore_user_config": True,
        "max_parallel": args.max_parallel,
        "large_max_parallel": args.max_parallel,
        "large_case_threshold_bytes": args.large_case_threshold_bytes,
        "token_budgets": [int(value) for value in args.token_budgets.split(",")],
        "codex_timeout_seconds": args.codex_timeout_seconds,
        "large_codex_timeout_seconds": args.large_codex_timeout_seconds,
        "quality_check": "none",
        "case_order_policy": "frozen candidate116 selection order; scheduling by name does not alter identity/order lock",
        "runner_command": runner_command,
        "runner_command_sha256": canonical_sha256(runner_command),
        "tool_bindings": tool_bindings,
    }
    config["config_sha256"] = canonical_sha256(config)
    write_json(CONFIG_PATH, config)

    builder = load_builder_module()
    readonly_snapshot = builder.readonly_operation_snapshot(phase="before_candidate116_codex_draft_generation")
    write_json(READONLY_BEFORE, readonly_snapshot)

    prelock = {
        "schema_version": "androidworld_candidate116_codex_draft_prelock/v1",
        "status": "frozen_before_first_model_call",
        "frozen_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "old_packet_source_freeze": {
            "path": repo_path(OLD_INPUT_FREEZE),
            "file_sha256": sha256_file(OLD_INPUT_FREEZE),
            "freeze_sha256": old_freeze["freeze_sha256"],
        },
        "static_acceptance": {"path": repo_path(STATIC_REPORT), "sha256": sha256_file(STATIC_REPORT)},
        "draft_config": {"path": repo_path(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH), "config_sha256": config["config_sha256"]},
        "readonly_before_snapshot": {"path": repo_path(READONLY_BEFORE), "sha256": sha256_file(READONLY_BEFORE)},
        "case_count": 116,
        "case_order": case_ids,
        "case_order_sha256": canonical_sha256(case_ids),
        "compact_packet_inputs": compact_inputs,
        "compact_packet_inputs_sha256": canonical_sha256(compact_inputs),
        "tool_bindings": tool_bindings,
        "canonical_output_gate": {
            "raw_wave": repo_path(WAVE_ROOT),
            "canonical_drafts": repo_path(DRAFT_ROOT),
            "canonical_draft_logs": repo_path(DRAFT_LOG_ROOT),
            "promotion_requires": "116/116 schema, guardrail, provenance, semantic, and independent per-case reviews accepted",
        },
    }
    prelock["prelock_sha256"] = canonical_sha256(prelock)
    write_json(PRELOCK_PATH, prelock)
    print(json.dumps({"status": "pass", "config": repo_path(CONFIG_PATH), "prelock": repo_path(PRELOCK_PATH), "prelock_sha256": prelock["prelock_sha256"], "case_count": 116}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
