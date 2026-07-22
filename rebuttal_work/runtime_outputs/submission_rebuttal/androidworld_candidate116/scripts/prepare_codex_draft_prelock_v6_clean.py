#!/usr/bin/env python3
"""Create the fail-closed v6_clean prelock for a fresh canonical-only wave_004.

This command performs no model call.  It is intentionally create-once: a partial
or complete prior claim requires a human audit rather than an automatic rewrite.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

from wave004_v6_clean_common import (
    CASE_COUNT,
    CONFIG_SCHEMA,
    EXPECTED_CODEX_VERSION,
    EXPECTED_FREEZE_SHA256,
    EXPECTED_MODEL,
    EXPECTED_REASONING,
    EXPECTED_SANDBOX,
    GENERATION_ID,
    PARALLELISM,
    PRELOCK_SCHEMA,
    SNAPSHOT_SCHEMA,
    Wave004V6CleanError,
    add_self_hash,
    canonical_sha256,
    executable_binding,
    load_json,
    regular_file_binding,
    require_empty_or_absent,
    require_safe_case_id,
    sha256_file,
    verify_self_hash,
    write_json_create_once,
)


SCRIPT = Path(__file__).resolve()
WORK_ROOT = SCRIPT.parents[1]
REPO_ROOT = WORK_ROOT.parents[3]
GEN_ROOT = WORK_ROOT / "draft_generation"
PACKET_ROOT = WORK_ROOT / "case_packets" / "androidworld"
OLD_FREEZE = WORK_ROOT / "freeze" / "androidworld_candidate116_draft_input_freeze.json"
PACKET_INDEX = WORK_ROOT / "indexes" / "androidworld_candidate116_packet_index.json"
STATIC_ACCEPTANCE = WORK_ROOT / "validation" / "strict_acceptance_report.json"
AGENTS_CONFIG = WORK_ROOT / "draft_config" / "androidworld_candidate116_drafter_config.json"
SOURCE_BUNDLE = WORK_ROOT / "source_bundles" / "androidworld_candidate116_source_bundle.json"
READONLY_HELPER = WORK_ROOT / "scripts" / "readonly_snapshot_helper.py"
LIVE_COMMON = WORK_ROOT / "scripts" / "wave004_v6_clean_common.py"
LIVE_LAUNCHER = WORK_ROOT / "scripts" / "run_fresh_draft_wave_v6_clean.py"
LIVE_NEURIPS = REPO_ROOT / "neurips_ed_track_minimal"
CLEAN_SUPPLEMENT = (
    GEN_ROOT / "prompts" / "androidworld_fresh_canonical_v6.supplement.md"
)
SUPERSESSION_INCIDENT = GEN_ROOT / "incidents" / "wave_003_superseded_full_regeneration.json"
WAVE003_ROOT = GEN_ROOT / "waves" / "wave_003"
WAVE004_ROOT = GEN_ROOT / "waves" / GENERATION_ID
CANONICAL_DRAFTS = WORK_ROOT / "drafts"
CANONICAL_CONTRACTS = WORK_ROOT / "contracts" / "drafts"

CLAIM_ROOT = GEN_ROOT / "prelock_claims" / "wave_004_v6_clean"
SNAPSHOT_ROOT = GEN_ROOT / "toolchain_snapshot" / "v6_clean"
SNAPSHOT_MANIFEST = SNAPSHOT_ROOT / "snapshot_manifest.json"
CONFIG_PATH = (
    GEN_ROOT / "config" / "androidworld_candidate116_codex_cli_draft_config_v6_clean.json"
)
PRELOCK_PATH = (
    GEN_ROOT / "freeze" / "androidworld_candidate116_codex_cli_draft_prelock_v6_clean.json"
)
READONLY_BEFORE = (
    GEN_ROOT / "validation" / "pre_generation_wave_004_v6_clean_readonly_snapshot.json"
)

EXPECTED_ENV_KEYS = (
    "CODEX_HOME",
    "HOME",
    "LANG",
    "LC_ALL",
    "PATH",
    "PYTHONDONTWRITEBYTECODE",
    "PYTHONHASHSEED",
    "PYTHONNOUSERSITE",
    "TMPDIR",
    "TZ",
)
RUNTIME_DISTRIBUTIONS = (
    "PyYAML",
    "attrs",
    "certifi",
    "charset-normalizer",
    "idna",
    "jsonschema",
    "jsonschema-specifications",
    "referencing",
    "requests",
    "rpds-py",
    "urllib3",
)
ALLOWED_LOGIN_WARNING = (
    "WARNING: proceeding, even though we could not create PATH aliases: "
    "Operation not permitted (os error 1)"
)

NEURIPS_COPY_MAP = {
    "package_init": (LIVE_NEURIPS / "__init__.py", "neurips_ed_track_minimal/__init__.py"),
    "checklist_guardrails": (
        LIVE_NEURIPS / "checklist_guardrails.py",
        "neurips_ed_track_minimal/checklist_guardrails.py",
    ),
    "scripts_init": (
        LIVE_NEURIPS / "scripts" / "__init__.py",
        "neurips_ed_track_minimal/scripts/__init__.py",
    ),
    "drafter": (
        LIVE_NEURIPS / "scripts" / "draft_case_checklist.py",
        "neurips_ed_track_minimal/scripts/draft_case_checklist.py",
    ),
    "batch_runner": (
        LIVE_NEURIPS / "scripts" / "run_draft_batch.py",
        "neurips_ed_track_minimal/scripts/run_draft_batch.py",
    ),
    "validator": (
        LIVE_NEURIPS / "scripts" / "checklist_validator.py",
        "neurips_ed_track_minimal/scripts/checklist_validator.py",
    ),
    "draft_prompt": (
        LIVE_NEURIPS / "prompts" / "draft_case_checklist.prompt.md",
        "neurips_ed_track_minimal/prompts/draft_case_checklist.prompt.md",
    ),
    "draft_template": (
        LIVE_NEURIPS / "templates" / "case_checklist.template.yaml",
        "neurips_ed_track_minimal/templates/case_checklist.template.yaml",
    ),
    "checklist_schema": (
        LIVE_NEURIPS / "schemas" / "case_checklist.schema.json",
        "neurips_ed_track_minimal/schemas/case_checklist.schema.json",
    ),
    "requirements": (
        LIVE_NEURIPS / "requirements.txt",
        "neurips_ed_track_minimal/requirements.txt",
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=EXPECTED_MODEL)
    parser.add_argument("--reasoning-effort", default=EXPECTED_REASONING)
    parser.add_argument("--max-parallel", type=int, default=PARALLELISM)
    parser.add_argument("--token-budgets", default="20000,24000,32000")
    parser.add_argument("--codex-timeout-seconds", type=int, default=3600)
    parser.add_argument("--large-codex-timeout-seconds", type=int, default=5400)
    return parser.parse_args()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise Wave004V6CleanError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exact_closed_environment() -> dict[str, str]:
    home = Path.home().resolve()
    tmpdir = Path(os.environ.get("TMPDIR") or tempfile.gettempdir()).resolve()
    environment = {
        "CODEX_HOME": str((home / ".codex").resolve()),
        "HOME": str(home),
        "LANG": "en_US.UTF-8",
        "LC_ALL": "en_US.UTF-8",
        "PATH": "/opt/homebrew/bin:/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
        "TMPDIR": str(tmpdir),
        "TZ": "UTC",
    }
    if tuple(sorted(environment)) != tuple(sorted(EXPECTED_ENV_KEYS)):
        raise Wave004V6CleanError("internal closed-environment key set changed")
    if not Path(environment["CODEX_HOME"]).is_dir():
        raise Wave004V6CleanError("CODEX_HOME does not exist")
    if not tmpdir.is_dir():
        raise Wave004V6CleanError("TMPDIR does not exist")
    return environment


def exact_codex_status(
    executable: Path, environment: Mapping[str, str]
) -> tuple[str, bool]:
    version = subprocess.run(
        [str(executable), "--version"],
        env=dict(environment),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if (
        version.returncode != 0
        or version.stdout.strip() != EXPECTED_CODEX_VERSION
        or version.stderr.strip()
    ):
        raise Wave004V6CleanError(
            f"Codex version is not exact: rc={version.returncode}, "
            f"stdout={version.stdout!r}, stderr={version.stderr!r}"
        )
    login = subprocess.run(
        [str(executable), "login", "status"],
        env=dict(environment),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    lines = [
        line.strip()
        for part in (login.stdout, login.stderr)
        for line in (part or "").splitlines()
        if line.strip()
    ]
    warning = bool(lines and lines[0] == ALLOWED_LOGIN_WARNING)
    if warning:
        lines = lines[1:]
    if login.returncode != 0 or lines != ["Logged in using ChatGPT"]:
        raise Wave004V6CleanError(
            f"Codex login is not exact ChatGPT login: rc={login.returncode}, lines={lines}"
        )
    return version.stdout.strip(), warning


def verify_frozen_inputs() -> tuple[
    dict[str, Any], dict[str, Any], list[dict[str, Any]], list[str]
]:
    freeze = load_json(OLD_FREEZE, "fe2018 packet/source freeze")
    verify_self_hash(freeze, "freeze_sha256", "fe2018 packet/source freeze")
    if (
        freeze.get("schema_version") != "contract_draft_input_freeze/v1"
        or freeze.get("status") != "frozen"
        or freeze.get("freeze_sha256") != EXPECTED_FREEZE_SHA256
        or freeze.get("source_count") != CASE_COUNT
    ):
        raise Wave004V6CleanError("fe2018 packet/source freeze identity is invalid")

    case_order = list((freeze.get("case_order") or {}).get("case_unit_ids") or [])
    if (
        len(case_order) != CASE_COUNT
        or len(set(case_order)) != CASE_COUNT
        or any(require_safe_case_id(case_id) != case_id for case_id in case_order)
        or (freeze.get("case_order") or {}).get("case_unit_ids_hash")
        != canonical_sha256(case_order)
    ):
        raise Wave004V6CleanError("frozen case order is not exactly 116 unique safe cases")

    index = load_json(PACKET_INDEX, "packet index")
    rows = list(index.get("items") or [])
    if index.get("candidate_count") != CASE_COUNT or len(rows) != CASE_COUNT:
        raise Wave004V6CleanError("packet index does not contain exactly 116 rows")
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        case_id = require_safe_case_id(row.get("case_unit_id"))
        if case_id in by_id:
            raise Wave004V6CleanError(f"duplicate packet-index case: {case_id}")
        by_id[case_id] = row

    discovered = sorted(PACKET_ROOT.glob("*/case_packet.md"))
    discovered_ids = [path.parent.name for path in discovered]
    if len(discovered) != CASE_COUNT or set(discovered_ids) != set(case_order):
        raise Wave004V6CleanError("canonical packet root is not the exact frozen 116-case set")

    packet_inputs: list[dict[str, Any]] = []
    metadata_patterns = {
        "domain": re.compile(r"-\s*domain:\s*`([^`]+)`"),
        "case_unit_id": re.compile(r"-\s*case_unit_id:\s*`([^`]+)`"),
        "task_id": re.compile(r"-\s*task_id:\s*`([^`]+)`"),
    }
    for rank, case_id in enumerate(case_order):
        row = by_id.get(case_id)
        if row is None or row.get("selection_rank") != rank:
            raise Wave004V6CleanError(f"packet index rank mismatch for {case_id}")
        packet = PACKET_ROOT / case_id / "case_packet.md"
        expected_relative = packet.relative_to(REPO_ROOT).as_posix()
        if row.get("case_packet_path") != expected_relative:
            raise Wave004V6CleanError(f"packet index path mismatch for {case_id}")
        binding = regular_file_binding(packet)
        if row.get("case_packet_sha256") != binding["sha256"]:
            raise Wave004V6CleanError(f"packet index byte hash mismatch for {case_id}")
        text = packet.read_text(encoding="utf-8")
        metadata: dict[str, str] = {}
        for name, pattern in metadata_patterns.items():
            match = pattern.search(text)
            if match is None:
                raise Wave004V6CleanError(f"canonical packet lacks {name}: {case_id}")
            metadata[name] = match.group(1).strip()
        if (
            metadata["domain"] != "androidworld"
            or metadata["case_unit_id"] != case_id
            or metadata["task_id"] != str(row.get("task_id"))
        ):
            raise Wave004V6CleanError(f"canonical packet metadata mismatch for {case_id}")
        packet_inputs.append(
            {
                "selection_rank": rank,
                "case_unit_id": case_id,
                "task_id": metadata["task_id"],
                "group": row.get("group"),
                "input_kind": "canonical_full_case_packet",
                "packet": binding,
                "source_closure_sha256": row.get("source_closure_sha256"),
                "semantic_source_context_sha256": row.get(
                    "semantic_source_context_sha256"
                ),
            }
        )

    agents_binding = regular_file_binding(AGENTS_CONFIG)
    if (
        agents_binding["sha256"] != freeze.get("agents_config_hash")
        or agents_binding["sha256"]
        != ((freeze.get("artifact_bindings") or {}).get("agents_config") or {}).get(
            "sha256"
        )
    ):
        raise Wave004V6CleanError("frozen agents config binding is inconsistent")
    llm = freeze.get("llm") or {}
    llm_roles = llm.get("llm_roles")
    if (
        not isinstance(llm_roles, dict)
        or "contract_drafter" not in llm_roles
        or llm.get("llm_roles_sha256") != canonical_sha256(llm_roles)
    ):
        raise Wave004V6CleanError("frozen llm_roles binding is invalid")
    static = load_json(STATIC_ACCEPTANCE, "strict static acceptance")
    if static.get("status") != "pass" or static.get("case_count") != CASE_COUNT:
        raise Wave004V6CleanError("strict packet acceptance is not 116/116 pass")
    return freeze, index, packet_inputs, case_order


STRICT_SUPPORT_INSERT = '''    native = checklist.get("native", {})
    for singleton_name in ("user_goal", "benchmark_success", "checked_by"):
        singleton = native.get(singleton_name)
        support = singleton.get("support") if isinstance(singleton, dict) else None
        if not isinstance(support, list) or not support or any(
            not isinstance(pointer, str) or not pointer.strip() for pointer in support
        ):
            violations.append(f"native.{singleton_name}.support must be a non-empty source-pointer list")
    for list_name in ("success_if", "fail_if", "undecided_if", "decisive_artifacts"):
        values = native.get(list_name)
        if not isinstance(values, list) or not values:
            violations.append(f"native.{list_name} must be a non-empty list")
            continue
        for index, item in enumerate(values):
            support = item.get("support") if isinstance(item, dict) else None
            if not isinstance(support, list) or not support or any(
                not isinstance(pointer, str) or not pointer.strip() for pointer in support
            ):
                violations.append(
                    f"native.{list_name}[{index}].support must be a non-empty source-pointer list"
                )
    stronger_items = checklist.get("stronger", {}).get("additional_conditions", [])
    for index, item in enumerate(stronger_items):
        support = item.get("support") if isinstance(item, dict) else None
        if not isinstance(support, list) or not support or any(
            not isinstance(pointer, str) or not pointer.strip() for pointer in support
        ):
            violations.append(
                f"stronger.additional_conditions[{index}].support must be a non-empty source-pointer list"
            )

'''


def adapt_guardrail_text(origin: str) -> str:
    replacements = (
        ('    allowed = {"case_packet.md"}\n', '    allowed: set[str] = set()\n'),
        (
            '    if len(allowed) == 1:\n',
            '    if not allowed:\n',
        ),
        (
            'f"{field_name} must cite case_packet.md or an exact Source Inventory path: {pointer}"',
            'f"{field_name} must cite an exact Source Inventory path: {pointer}"',
        ),
        (
            '    violations: list[str] = []\n\n    for field_name, pointers in _iter_support_pointer_lists(checklist):',
            '    violations: list[str] = []\n\n'
            + STRICT_SUPPORT_INSERT
            + '    for field_name, pointers in _iter_support_pointer_lists(checklist):',
        ),
    )
    adapted = origin
    for old, new in replacements:
        if adapted.count(old) != 1:
            raise Wave004V6CleanError(
                f"guardrail controlled-adaptation anchor count is {adapted.count(old)}, expected 1"
            )
        adapted = adapted.replace(old, new, 1)
    return adapted


def adapt_validator_text(origin: str) -> str:
    old = (
        '"restricted to case_packet.md and its exact Source Inventory paths."\n'
    )
    new = '"restricted to exact Source Inventory paths; case_packet.md is forbidden."\n'
    if origin.count(old) != 1:
        raise Wave004V6CleanError("validator controlled-adaptation anchor is not exact")
    return origin.replace(old, new, 1)


def adapt_drafter_text(origin: str) -> str:
    """Isolate every model tool runtime while retaining the live drafter API."""

    old_command = '''    return [
        codex_executable,
        "exec",
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
'''
    permission_profile = (
        'permissions.candidate_draft_isolated={description="Canonical packet temp '
        'workspace read only",filesystem={":minimal"="read",":workspace_roots"='
        '{"."="read"},"'
        + str(REPO_ROOT)
        + '"="deny","'
        + str(Path.home().resolve() / ".codex")
        + '"="deny"},network={enabled=false}}'
    )
    new_command = '''    if sandbox != "read-only":
        raise DraftChecklistError("v6_clean requires the isolated read-only permission profile")
    permission_profile = ''' + repr(permission_profile) + '''
    return [
        codex_executable,
        "-a",
        "never",
        "exec",
        "--cd",
        str(workspace_root),
        "--skip-git-repo-check",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--strict-config",
        "--model",
        model,
        "-c",
        'default_permissions="candidate_draft_isolated"',
        "-c",
        permission_profile,
        "-c",
        f'model_reasoning_effort="{reasoning_effort}"',
        "-c",
        'model_verbosity="low"',
        "-c",
        'web_search="disabled"',
        "-c",
        "mcp_servers={}",
        "-c",
        'shell_environment_policy.inherit="none"',
        "--disable",
        "apps",
        "--disable",
        "plugins",
        "--disable",
        "remote_plugin",
        "--disable",
        "enable_mcp_apps",
        "--disable",
        "skill_mcp_dependency_install",
        "--disable",
        "browser_use",
        "--disable",
        "browser_use_external",
        "--disable",
        "browser_use_full_cdp_access",
        "--disable",
        "computer_use",
        "--disable",
        "in_app_browser",
        "--color",
        "never",
        "--json",
        "--output-schema",
        str(schema_path),
        "-o",
        str(output_path),
        "-",
    ]
'''
    old_workspace = '''        instructions_path = workspace_root / "draft_instructions.md"
        template_path = workspace_root / "template.yaml"
        case_packet_path = workspace_root / "case_packet.md"
        schema_path = workspace_root / "output_schema.json"
        output_path = workspace_root / "draft_body.json"
        instructions_path.write_text(instructions, encoding="utf-8")
        template_path.write_text(template_text, encoding="utf-8")
        case_packet_path.write_text(case_packet_text, encoding="utf-8")
        schema_path.write_text(
            json.dumps(model_output_schema, indent=2, ensure_ascii=False) + "\\n",
            encoding="utf-8",
        )

        prompt = (
            "Draft one case-checklist body. Read draft_instructions.md completely, then read "
            "template.yaml and case_packet.md from the current workspace. Follow the instructions "
            "and the enforced output schema exactly. Return JSON only. Do not modify any files."
        )
'''
    new_workspace = '''        schema_path = workspace_root / "output_schema.json"
        output_path = workspace_root / "draft_body.json"
        schema_text = json.dumps(model_output_schema, indent=2, ensure_ascii=False) + "\\n"
        schema_path.write_text(schema_text, encoding="utf-8")

        prompt = (
            "Draft exactly one case-checklist body from the four immutable inputs below. "
            "They are supplied through stdin; do not inspect any filesystem source other than "
            "the enforced output schema in this isolated workspace. Return JSON only.\\n\\n"
            "<<<BEGIN FROZEN BASE PLUS CANONICAL-V6 INSTRUCTIONS>>>\\n"
            + instructions.rstrip()
            + "\\n<<<END FROZEN BASE PLUS CANONICAL-V6 INSTRUCTIONS>>>\\n\\n"
            "<<<BEGIN FROZEN TEMPLATE>>>\\n"
            + template_text.rstrip()
            + "\\n<<<END FROZEN TEMPLATE>>>\\n\\n"
            "<<<BEGIN CANONICAL CASE PACKET>>>\\n"
            + case_packet_text.rstrip()
            + "\\n<<<END CANONICAL CASE PACKET>>>\\n"
        )
'''
    old_after = '''        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        events, malformed_lines = load_jsonl_objects(stdout)
'''
    new_after = '''        workspace_entries = sorted(path.name for path in workspace_root.iterdir())
        if any(name not in {"output_schema.json", "draft_body.json"} for name in workspace_entries):
            raise DraftChecklistError(
                f"isolated Codex workspace gained an undeclared entry: {workspace_entries}"
            )
        if schema_path.read_text(encoding="utf-8") != schema_text:
            raise DraftChecklistError("isolated Codex workspace schema bytes changed")

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        events, malformed_lines = load_jsonl_objects(stdout)
'''
    old_receipt = '''                "sandbox": sandbox,
                "command": command,
'''
    new_receipt = '''                "sandbox": None,
                "permission_profile": "candidate_draft_isolated",
                "permission_profile_workspace_access": "read",
                "permission_profile_network_enabled": False,
                "model_inputs_via_stdin": True,
                "command": command,
'''
    adapted = origin
    for old, new, label in (
        (old_command, new_command, "Codex command"),
        (old_workspace, new_workspace, "stdin-only workspace"),
        (old_after, new_after, "workspace namespace readback"),
        (old_receipt, new_receipt, "permission receipt"),
    ):
        if adapted.count(old) != 1:
            raise Wave004V6CleanError(
                f"drafter controlled-adaptation anchor {label} count is {adapted.count(old)}, expected 1"
            )
        adapted = adapted.replace(old, new, 1)
    return adapted


def runtime_environment_payload(python_path: Path) -> dict[str, Any]:
    probe = r'''
import importlib.metadata as metadata
import json
import pathlib
import sys
names = json.loads(sys.argv[1])
rows = []
for name in names:
    dist = metadata.distribution(name)
    files = []
    for item in sorted(dist.files or [], key=lambda value: str(value)):
        path = pathlib.Path(dist.locate_file(item))
        if path.suffix == ".pyc" or "__pycache__" in path.parts or not path.exists():
            continue
        if path.is_file() or path.is_symlink():
            files.append(str(path.absolute()))
    rows.append({"name": name, "version": dist.version, "files": files})
print(json.dumps({"sys_executable": sys.executable, "version": sys.version, "distributions": rows}))
'''
    completed = subprocess.run(
        [str(python_path), "-I", "-c", probe, json.dumps(RUNTIME_DISTRIBUTIONS)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if completed.returncode != 0 or completed.stderr.strip():
        raise Wave004V6CleanError(
            f"runtime closure probe failed: rc={completed.returncode}, stderr={completed.stderr}"
        )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise Wave004V6CleanError("runtime closure probe emitted invalid JSON") from exc
    distributions = []
    for row in result.get("distributions") or []:
        files = []
        for raw in row.get("files") or []:
            path = Path(raw)
            files.append(
                executable_binding(path) if path.is_symlink() else regular_file_binding(path)
            )
        if not files:
            raise Wave004V6CleanError(f"runtime distribution has no bound files: {row}")
        distributions.append(
            {"name": row["name"], "version": row["version"], "files": files}
        )
    if tuple(row["name"] for row in distributions) != RUNTIME_DISTRIBUTIONS:
        raise Wave004V6CleanError("runtime distribution closure order/set changed")
    payload = {
        "schema_version": "androidworld_candidate116_python_runtime_closure/v1",
        "status": "fully_byte_bound",
        "python_invocation": executable_binding(python_path),
        "python_version": result.get("version"),
        "pyvenv_cfg": regular_file_binding(REPO_ROOT / ".venv" / "pyvenv.cfg"),
        "distributions": distributions,
        "distribution_count": len(distributions),
        "policy": (
            "all non-stdlib distributions imported by the frozen drafter, validator, "
            "and batch runner are versioned and every installed non-pyc file is byte-bound"
        ),
    }
    return add_self_hash(payload, "runtime_closure_sha256")


def build_snapshot(stage: Path, python_path: Path) -> dict[str, Any]:
    stage.mkdir(mode=0o700)
    origins: list[dict[str, Any]] = []
    adaptations: list[dict[str, Any]] = []
    for name, (origin, relative) in NEURIPS_COPY_MAP.items():
        if origin.is_symlink() or not origin.is_file():
            raise Wave004V6CleanError(f"missing live tool origin: {origin}")
        destination = stage / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        origin_text: str | None = None
        adapted_text: str | None = None
        if name == "checklist_guardrails":
            origin_text = origin.read_text(encoding="utf-8")
            adapted_text = adapt_guardrail_text(origin_text)
        elif name == "validator":
            origin_text = origin.read_text(encoding="utf-8")
            adapted_text = adapt_validator_text(origin_text)
        elif name == "drafter":
            origin_text = origin.read_text(encoding="utf-8")
            adapted_text = adapt_drafter_text(origin_text)
        if adapted_text is None:
            shutil.copyfile(origin, destination)
        else:
            destination.write_text(adapted_text, encoding="utf-8")
            diff = "".join(
                difflib.unified_diff(
                    origin_text.splitlines(keepends=True),
                    adapted_text.splitlines(keepends=True),
                    fromfile=f"live/{origin.name}",
                    tofile=f"snapshot/{origin.name}",
                )
            )
            diff_path = stage / "controlled_adaptations" / f"{name}.diff"
            diff_path.parent.mkdir(parents=True, exist_ok=True)
            diff_path.write_text(diff, encoding="utf-8")
            adaptations.append(
                {
                    "name": name,
                    "policy": (
                        "minimum fail-closed adaptation: guardrail/validator forbid the "
                        "case_packet.md alias and require exact non-empty Source Inventory "
                        "support; drafter uses stdin-only canonical inputs and a custom "
                        "read-only, network-disabled permission profile with no repo access"
                    ),
                    "origin_sha256": sha256_file(origin),
                    "adapted_sha256": sha256_file(destination),
                    "diff_relative_path": diff_path.relative_to(stage).as_posix(),
                    "diff_sha256": sha256_file(diff_path),
                }
            )
        origins.append(
            {
                "name": name,
                "live_origin": regular_file_binding(origin),
                "snapshot_relative_path": relative,
                "snapshot_sha256": sha256_file(destination),
                "byte_identical": sha256_file(origin) == sha256_file(destination),
            }
        )

    supplement_destination = (
        stage
        / "neurips_ed_track_minimal"
        / "prompts"
        / "androidworld_fresh_canonical_v6.supplement.md"
    )
    shutil.copyfile(CLEAN_SUPPLEMENT, supplement_destination)
    origins.append(
        {
            "name": "prompt_supplement",
            "live_origin": regular_file_binding(CLEAN_SUPPLEMENT),
            "snapshot_relative_path": supplement_destination.relative_to(stage).as_posix(),
            "snapshot_sha256": sha256_file(supplement_destination),
            "byte_identical": True,
        }
    )

    wrapper_dir = stage / "wave004_v6_clean"
    wrapper_dir.mkdir(parents=True, exist_ok=True)
    for name, origin in (
        ("frozen_wrapper", LIVE_LAUNCHER),
        ("wave004_v6_clean_common", LIVE_COMMON),
        ("readonly_snapshot_helper", READONLY_HELPER),
    ):
        destination = wrapper_dir / origin.name
        shutil.copyfile(origin, destination)
        origins.append(
            {
                "name": name,
                "live_origin": regular_file_binding(origin),
                "snapshot_relative_path": destination.relative_to(stage).as_posix(),
                "snapshot_sha256": sha256_file(destination),
                "byte_identical": True,
            }
        )

    runtime_payload = runtime_environment_payload(python_path)
    runtime_path = stage / "runtime_environment_manifest.json"
    write_json_create_once(runtime_path, runtime_payload)

    forbidden_names = {
        "draft_source_pointer_strict_v2.supplement.md",
        "androidworld_full_regeneration_v5.supplement.md",
    }
    if any(path.name in forbidden_names for path in stage.rglob("*")):
        raise Wave004V6CleanError("snapshot contains a forbidden legacy/wrapper supplement")

    files = []
    for path in sorted(stage.rglob("*"), key=lambda item: item.relative_to(stage).as_posix()):
        if path.is_symlink():
            raise Wave004V6CleanError(f"snapshot contains symlink: {path}")
        if path.is_file() and path.name != "snapshot_manifest.json":
            files.append(
                {
                    "relative_path": path.relative_to(stage).as_posix(),
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    manifest = {
        "schema_version": SNAPSHOT_SCHEMA,
        "status": "frozen_create_once",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "snapshot_root_absolute": str(SNAPSHOT_ROOT),
        "file_count": len(files),
        "files": files,
        "files_sha256": canonical_sha256(files),
        "live_origins": origins,
        "controlled_adaptations": adaptations,
        "runtime_environment_manifest_relative": runtime_path.relative_to(stage).as_posix(),
        "runtime_environment_manifest_sha256": sha256_file(runtime_path),
        "effective_prompt_policy": (
            "exactly frozen live base draft prompt plus clean canonical v6 supplement; "
            "no legacy pointer supplement and no historical draft/warning packet"
        ),
        "permission_policy": "all files 0444 and all directories 0555 after finalization",
    }
    manifest = add_self_hash(manifest, "snapshot_sha256")
    write_json_create_once(stage / "snapshot_manifest.json", manifest)
    return manifest


def make_snapshot_read_only(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_file():
            path.chmod(0o444)
    for path in sorted((item for item in root.rglob("*") if item.is_dir()), reverse=True):
        path.chmod(0o555)
    root.chmod(0o555)


def native_batch_command(
    *,
    python_path: Path,
    tool_bindings: Mapping[str, Mapping[str, Any]],
    packet_inputs: list[Mapping[str, Any]],
    case_order: list[str],
    token_budgets: str,
    codex_timeout: int,
    large_codex_timeout: int,
) -> list[str]:
    max_packet_size = max(int(row["packet"]["size_bytes"]) for row in packet_inputs)
    return [
        str(python_path.absolute()),
        str(tool_bindings["batch_runner"]["path"]),
        "--case-packet-root",
        str(PACKET_ROOT.resolve()),
        "--output-root",
        str(WAVE004_ROOT),
        "--provider",
        "codex",
        "--model",
        EXPECTED_MODEL,
        "--reasoning-effort",
        EXPECTED_REASONING,
        "--token-budgets",
        token_budgets,
        "--max-parallel",
        str(PARALLELISM),
        "--large-max-parallel",
        str(PARALLELISM),
        "--large-case-threshold-bytes",
        str(max_packet_size + 1),
        "--http-timeout-seconds",
        "180",
        "--large-http-timeout-seconds",
        "480",
        "--codex-timeout-seconds",
        str(codex_timeout),
        "--large-codex-timeout-seconds",
        str(large_codex_timeout),
        "--codex-sandbox",
        EXPECTED_SANDBOX,
        "--prompt-supplement",
        str(tool_bindings["prompt_supplement"]["path"]),
        "--sort-by",
        "name",
        "--sleep-seconds",
        "2.0",
        "--quality-check",
        "none",
        "--case-ids",
        ",".join(case_order),
    ]


def main() -> int:
    args = parse_args()
    if (
        args.model != EXPECTED_MODEL
        or args.reasoning_effort != EXPECTED_REASONING
        or args.max_parallel != PARALLELISM
        or args.codex_timeout_seconds < 1800
        or args.large_codex_timeout_seconds < args.codex_timeout_seconds
    ):
        raise Wave004V6CleanError("v6_clean model/reasoning/concurrency/timeout policy is immutable")
    try:
        budgets = [int(value) for value in args.token_budgets.split(",")]
    except ValueError as exc:
        raise Wave004V6CleanError("token budgets are not integers") from exc
    if len(budgets) < 1 or any(value < 12000 for value in budgets):
        raise Wave004V6CleanError("token budgets are below strict generation policy")

    for path, label in (
        (SNAPSHOT_ROOT, "v6_clean toolchain snapshot"),
        (CONFIG_PATH, "v6_clean draft config"),
        (PRELOCK_PATH, "v6_clean prelock"),
        (READONLY_BEFORE, "v6_clean read-only snapshot"),
        (CLAIM_ROOT, "v6_clean prelock claim"),
        (WAVE004_ROOT, "wave_004 raw output"),
    ):
        if path.exists() or path.is_symlink():
            raise Wave004V6CleanError(f"{label} already exists; refusing rewrite: {path}")
    require_empty_or_absent(CANONICAL_DRAFTS, "canonical drafts")
    require_empty_or_absent(CANONICAL_CONTRACTS, "canonical contracts/drafts")
    if WAVE003_ROOT.exists() or WAVE003_ROOT.is_symlink():
        raise Wave004V6CleanError("superseded wave_003 bytes still exist")

    incident = load_json(SUPERSESSION_INCIDENT, "wave_003 supersession incident")
    verify_self_hash(incident, "incident_sha256", "wave_003 supersession incident")
    if (
        incident.get("promotion_forbidden") is not True
        or incident.get("old_draft_reuse_forbidden") is not True
        or incident.get("replacement_generation_id") != GENERATION_ID
    ):
        raise Wave004V6CleanError("wave_003 supersession incident does not forbid reuse")

    freeze, packet_index, packet_inputs, case_order = verify_frozen_inputs()
    environment = exact_closed_environment()
    codex_path_raw = shutil.which("codex", path=environment["PATH"])
    if codex_path_raw != "/opt/homebrew/bin/codex":
        raise Wave004V6CleanError(f"Codex CLI did not resolve exactly: {codex_path_raw}")
    codex_path = Path(codex_path_raw)
    version, login_warning = exact_codex_status(codex_path, environment)
    codex_binding = executable_binding(codex_path)
    python_path = REPO_ROOT / ".venv" / "bin" / "python"
    python_binding = executable_binding(python_path)

    CLAIM_ROOT.parent.mkdir(parents=True, exist_ok=True)
    os.mkdir(CLAIM_ROOT, 0o700)
    stage_snapshot = CLAIM_ROOT / "toolchain_snapshot.stage"
    manifest = build_snapshot(stage_snapshot, python_path)
    make_snapshot_read_only(stage_snapshot)
    SNAPSHOT_ROOT.parent.mkdir(parents=True, exist_ok=True)
    os.replace(stage_snapshot, SNAPSHOT_ROOT)

    snapshot_package = SNAPSHOT_ROOT / "neurips_ed_track_minimal"
    tool_paths = {
        "draft_prompt": snapshot_package / "prompts" / "draft_case_checklist.prompt.md",
        "prompt_supplement": snapshot_package
        / "prompts"
        / "androidworld_fresh_canonical_v6.supplement.md",
        "draft_template": snapshot_package / "templates" / "case_checklist.template.yaml",
        "checklist_schema": snapshot_package / "schemas" / "case_checklist.schema.json",
        "checklist_guardrails": snapshot_package / "checklist_guardrails.py",
        "drafter": snapshot_package / "scripts" / "draft_case_checklist.py",
        "batch_runner": snapshot_package / "scripts" / "run_draft_batch.py",
        "validator": snapshot_package / "scripts" / "checklist_validator.py",
    }
    tool_bindings = {
        name: regular_file_binding(path) for name, path in sorted(tool_paths.items())
    }
    effective_prompt = (
        tool_paths["draft_prompt"].read_text(encoding="utf-8").rstrip()
        + "\n\n"
        + tool_paths["prompt_supplement"].read_text(encoding="utf-8").strip()
        + "\n"
    )
    prompt_composition = {
        "ordered_components": [
            tool_bindings["draft_prompt"],
            tool_bindings["prompt_supplement"],
        ],
        "separator": "base.rstrip() + two newlines + supplement.strip() + newline",
        "effective_prompt_sha256": canonical_sha256({"prompt": effective_prompt}),
        "legacy_supplements_included": [],
        "historical_draft_or_warning_input_included": False,
    }
    prompt_composition["composition_sha256"] = canonical_sha256(prompt_composition)

    readonly_helper = load_module(READONLY_HELPER, "wave004_v6_clean_readonly_preparer")
    readonly = readonly_helper.readonly_operation_snapshot(
        phase="before_candidate116_wave004_v6_clean",
        repo_root=REPO_ROOT,
        work_root=WORK_ROOT,
    )
    readonly["snapshot_sha256"] = canonical_sha256(readonly)
    write_json_create_once(READONLY_BEFORE, readonly)

    snapshot_binding = regular_file_binding(SNAPSHOT_MANIFEST)
    snapshot_binding["snapshot_sha256"] = manifest["snapshot_sha256"]
    command = native_batch_command(
        python_path=python_path,
        tool_bindings=tool_bindings,
        packet_inputs=packet_inputs,
        case_order=case_order,
        token_budgets=args.token_budgets,
        codex_timeout=args.codex_timeout_seconds,
        large_codex_timeout=args.large_codex_timeout_seconds,
    )
    frozen_wrapper = regular_file_binding(
        SNAPSHOT_ROOT / "wave004_v6_clean" / LIVE_LAUNCHER.name
    )
    frozen_common = regular_file_binding(
        SNAPSHOT_ROOT / "wave004_v6_clean" / LIVE_COMMON.name
    )
    frozen_readonly_helper = regular_file_binding(
        SNAPSHOT_ROOT / "wave004_v6_clean" / READONLY_HELPER.name
    )
    auth_receipt = {
        "schema_version": "androidworld_candidate116_codex_auth_prelock/v1",
        "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "version": version,
        "login_status": "Logged in using ChatGPT",
        "allowed_path_alias_warning_observed": login_warning,
        "closed_environment_sha256": canonical_sha256(environment),
    }
    auth_receipt["auth_receipt_sha256"] = canonical_sha256(auth_receipt)

    frozen_llm_roles = dict((freeze.get("llm") or {}).get("llm_roles") or {})
    config = {
        "schema_version": CONFIG_SCHEMA,
        "status": "prelocked_before_first_model_call",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "generation_id": GENERATION_ID,
        "provider": "codex_cli",
        "auth_mode": "codex_login_chatgpt",
        "model": EXPECTED_MODEL,
        "reasoning_effort": EXPECTED_REASONING,
        "model_verbosity": "low",
        "sandbox": EXPECTED_SANDBOX,
        "ephemeral": True,
        "ignore_user_config": True,
        "max_parallel": PARALLELISM,
        "large_max_parallel": PARALLELISM,
        "sample_interval_seconds": 0.1,
        "token_budgets": budgets,
        "codex_timeout_seconds": args.codex_timeout_seconds,
        "large_codex_timeout_seconds": args.large_codex_timeout_seconds,
        "codex_cli": codex_binding,
        "python_runtime": python_binding,
        "child_environment": environment,
        "child_environment_sha256": canonical_sha256(environment),
        "toolchain_snapshot": snapshot_binding,
        "tool_bindings": tool_bindings,
        "frozen_wrapper": frozen_wrapper,
        "frozen_common": frozen_common,
        "frozen_readonly_helper": frozen_readonly_helper,
        "prompt_composition": prompt_composition,
        "native_batch_command": command,
        "native_batch_command_sha256": canonical_sha256(command),
        "repository_root_absolute": str(REPO_ROOT),
        "work_root_absolute": str(WORK_ROOT),
        "snapshot_root_absolute": str(SNAPSHOT_ROOT),
        "canonical_packet_root_absolute": str(PACKET_ROOT.resolve()),
        "output_root_absolute": str(WAVE004_ROOT),
        "concurrency_samples_absolute": str(WAVE004_ROOT / "_concurrency_samples.jsonl"),
        "canonical_drafts_absolute": str(CANONICAL_DRAFTS),
        "canonical_contracts_absolute": str(CANONICAL_CONTRACTS),
        "model_input_policy": {
            "packet_kind": "canonical_full_case_packet",
            "packet_count": CASE_COUNT,
            "packet_wrapper_used": False,
            "historical_draft_bytes_used": False,
            "historical_qc_or_warning_text_used": False,
            "effective_prompt_components": ["frozen_base_prompt", "clean_canonical_v6"],
        },
        "frozen_context_agents_config": regular_file_binding(AGENTS_CONFIG),
        "frozen_context_llm_roles": frozen_llm_roles,
        "frozen_context_llm_roles_sha256": canonical_sha256(frozen_llm_roles),
        "context_role_note": (
            "the fe2018 agents config/llm_roles are bound provenance context; the "
            "actual fresh drafter is independently and explicitly locked above to Codex CLI"
        ),
        "codex_auth_at_prelock": auth_receipt,
    }
    config = add_self_hash(config, "config_sha256")
    write_json_create_once(CONFIG_PATH, config)

    prelock = {
        "schema_version": PRELOCK_SCHEMA,
        "status": "frozen_before_first_model_call",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "generation_id": GENERATION_ID,
        "case_count": CASE_COUNT,
        "case_order": case_order,
        "case_order_sha256": canonical_sha256(case_order),
        "packet_inputs": packet_inputs,
        "packet_inputs_sha256": canonical_sha256(packet_inputs),
        "packet_index": regular_file_binding(PACKET_INDEX),
        "packet_index_payload_sha256": canonical_sha256(packet_index),
        "old_packet_source_freeze": regular_file_binding(OLD_FREEZE)
        | {"freeze_sha256": freeze["freeze_sha256"]},
        "static_acceptance": regular_file_binding(STATIC_ACCEPTANCE),
        "source_bundle": regular_file_binding(SOURCE_BUNDLE),
        "agents_config": regular_file_binding(AGENTS_CONFIG),
        "llm_roles": frozen_llm_roles,
        "llm_roles_sha256": canonical_sha256(frozen_llm_roles),
        "tool_bindings": tool_bindings,
        "toolchain_snapshot": snapshot_binding,
        "draft_config": regular_file_binding(CONFIG_PATH)
        | {"config_sha256": config["config_sha256"]},
        "readonly_before_snapshot": regular_file_binding(READONLY_BEFORE)
        | {"snapshot_sha256": readonly["snapshot_sha256"]},
        "wave003_supersession": regular_file_binding(SUPERSESSION_INCIDENT)
        | {"incident_sha256": incident["incident_sha256"]},
        "canonical_output_gate": {
            "raw_wave": str(WAVE004_ROOT),
            "canonical_drafts": str(CANONICAL_DRAFTS),
            "canonical_contracts": str(CANONICAL_CONTRACTS),
            "raw_wave_create_once": True,
            "canonical_outputs_must_remain_empty_until_qc_semantic_root_116_of_116": True,
        },
        "first_model_call_authorized": True,
        "freeze_authorized": False,
        "freeze_requires": (
            "deterministic QC, independent semantic review, and explicit root acceptance 116/116"
        ),
    }
    prelock = add_self_hash(prelock, "prelock_sha256")
    write_json_create_once(PRELOCK_PATH, prelock)

    claim_receipt = add_self_hash(
        {
            "schema_version": "androidworld_candidate116_wave004_v6_clean_prelock_claim/v1",
            "status": "complete_no_model_call",
            "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "prelock": regular_file_binding(PRELOCK_PATH)
            | {"prelock_sha256": prelock["prelock_sha256"]},
            "config": regular_file_binding(CONFIG_PATH)
            | {"config_sha256": config["config_sha256"]},
            "toolchain_snapshot": snapshot_binding,
            "readonly_before": regular_file_binding(READONLY_BEFORE)
            | {"snapshot_sha256": readonly["snapshot_sha256"]},
            "model_call_count": 0,
        },
        "claim_receipt_sha256",
    )
    write_json_create_once(CLAIM_ROOT / "claim_receipt.json", claim_receipt)
    os.chmod(CLAIM_ROOT / "claim_receipt.json", 0o444)
    print(
        json.dumps(
            {
                "status": "prelocked_no_model_call",
                "prelock": str(PRELOCK_PATH),
                "prelock_sha256": prelock["prelock_sha256"],
                "frozen_launcher": frozen_wrapper["path"],
                "launch_command": [
                    str(python_path.absolute()),
                    frozen_wrapper["path"],
                    "--prelock",
                    str(PRELOCK_PATH),
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Wave004V6CleanError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
