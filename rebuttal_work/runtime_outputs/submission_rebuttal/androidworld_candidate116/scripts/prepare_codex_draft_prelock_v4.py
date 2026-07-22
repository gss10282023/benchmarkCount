#!/usr/bin/env python3
"""Create the canonical-only wave_004 tool snapshot, config, and prelock."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).resolve()
WORK_ROOT = SCRIPT.parents[1]
REPO_ROOT = WORK_ROOT.parents[3]
GEN_ROOT = WORK_ROOT / "draft_generation"
REJECTED_GATE = GEN_ROOT / "validation" / "wave_004_v6_prelock_independent_go.json"
INDEPENDENT_GO = GEN_ROOT / "validation" / "wave_004_v6_clean_independent_go.json"
INDEPENDENT_AUDIT = WORK_ROOT / "scripts" / "audit_wave004_v6_prelock.py"
PACKET_INDEX = WORK_ROOT / "indexes" / "androidworld_candidate116_packet_index.json"
INPUT_FREEZE = WORK_ROOT / "freeze" / "androidworld_candidate116_draft_input_freeze.json"
PACKET_ROOT = WORK_ROOT / "case_packets" / "androidworld"
SUPERSESSION = GEN_ROOT / "incidents" / "wave_003_superseded_full_regeneration.json"
OUTPUT_ROOT = GEN_ROOT / "waves" / "wave_004_v6_clean"
CONFIG_PATH = GEN_ROOT / "config" / "androidworld_candidate116_codex_cli_draft_config_v6_clean.json"
AGENTS_CONFIG = GEN_ROOT / "config" / "androidworld_candidate116_codex_cli_agents_config_v6_clean.json"
PRELOCK_PATH = GEN_ROOT / "freeze" / "androidworld_candidate116_codex_cli_draft_prelock_v6_clean.json"
READONLY_BEFORE = (
    GEN_ROOT / "validation" / "pre_generation_wave_004_v6_clean_readonly_snapshot.json"
)
SNAPSHOT_ROOT = GEN_ROOT / "toolchain_snapshot" / "v6_clean"
SNAPSHOT_PACKAGE = SNAPSHOT_ROOT / "neurips_ed_track_minimal"
SNAPSHOT_MANIFEST = SNAPSHOT_ROOT / "snapshot_manifest.json"
LIVE_NEURIPS = REPO_ROOT / "neurips_ed_track_minimal"
LIVE_PROMPT = GEN_ROOT / "prompts" / "androidworld_fresh_canonical_v6.supplement.md"
LIVE_POINTER_PROMPT = (
    GEN_ROOT / "prompts" / "androidworld_source_pointer_strict_v3.supplement.md"
)
LIVE_STRICT_GUARDRAILS = WORK_ROOT / "scripts" / "strict_checklist_guardrails_v6_clean.py"
LIVE_WRAPPER = WORK_ROOT / "scripts" / "run_fresh_draft_wave_v4.py"
LIVE_READONLY_HELPER = WORK_ROOT / "scripts" / "readonly_snapshot_helper.py"
CANONICAL_DRAFTS = WORK_ROOT / "drafts"
CANONICAL_CONTRACTS = WORK_ROOT / "contracts" / "drafts"
ALLOWED_CODEX_WARNING = (
    "WARNING: proceeding, even though we could not create PATH aliases: "
    "Operation not permitted (os error 1)"
)


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON object required: {path}")
    return value


def verify_self_hash(value: dict[str, Any], field: str, label: str) -> None:
    claimed = value.get(field)
    core = dict(value)
    core.pop(field, None)
    if claimed != canonical_sha256(core):
        raise RuntimeError(f"{label} self-hash mismatch")


def binding(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if path.is_symlink() or not resolved.is_file():
        raise RuntimeError(f"regular file required: {path}")
    return {
        "path": str(resolved),
        "sha256": sha256_file(resolved),
        "size_bytes": resolved.stat().st_size,
    }


def python_runtime_binding(invocation: Path) -> dict[str, Any]:
    invocation = invocation.absolute()
    if not invocation.is_symlink():
        raise RuntimeError(f"expected venv Python invocation symlink: {invocation}")
    chain: list[dict[str, str]] = []
    current = invocation
    seen: set[Path] = set()
    while current.is_symlink():
        if current in seen:
            raise RuntimeError("cycle in venv Python symlink chain")
        seen.add(current)
        target = current.readlink()
        chain.append({"path": str(current), "target": str(target)})
        current = target if target.is_absolute() else current.parent / target
        current = current.absolute()
    resolved = current.resolve(strict=True)
    pyvenv_cfg = invocation.parent.parent / "pyvenv.cfg"
    return {
        "invocation_path": str(invocation),
        "symlink_chain": chain,
        "resolved_binary": binding(resolved),
        "pyvenv_cfg": binding(pyvenv_cfg),
    }


def write_json_create_once(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-5.6-sol", choices=("gpt-5.6-sol",))
    parser.add_argument("--reasoning-effort", default="xhigh", choices=("xhigh",))
    parser.add_argument("--max-parallel", type=int, default=6, choices=(6,))
    parser.add_argument("--codex-timeout-seconds", type=int, default=1800)
    parser.add_argument("--large-codex-timeout-seconds", type=int, default=3600)
    parser.add_argument("--token-budgets", default="12000,16000,20000")
    parser.add_argument("--large-case-threshold-bytes", type=int, default=900000)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def exact_environment(codex_home: Path) -> dict[str, str]:
    home = Path.home().resolve(strict=True)
    if not codex_home.is_dir() or codex_home.is_symlink():
        raise RuntimeError(f"Codex home is missing or symlinked: {codex_home}")
    return {
        "PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(home),
        "CODEX_HOME": str(codex_home.resolve(strict=True)),
        "TMPDIR": "/private/tmp",
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
    }


def codex_preflight(environment: dict[str, str]) -> dict[str, Any]:
    invocation = Path("/opt/homebrew/bin/codex")
    if not invocation.is_file():
        raise RuntimeError("required Codex invocation is missing")
    binary = invocation.resolve(strict=True)
    version = subprocess.run(
        [str(binary), "--version"],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if version.returncode != 0 or version.stdout.strip() != "codex-cli 0.144.4":
        raise RuntimeError("Codex version is not exactly codex-cli 0.144.4")
    login = subprocess.run(
        [str(binary), "login", "status"],
        env=environment,
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
    warning = bool(lines and lines[0] == ALLOWED_CODEX_WARNING)
    if warning:
        lines = lines[1:]
    if login.returncode != 0 or lines != ["Logged in using ChatGPT"]:
        raise RuntimeError(f"Codex login is not exact: rc={login.returncode}, lines={lines}")
    return binding(binary) | {
        "version": "codex-cli 0.144.4",
        "login_status_at_prelock": "Logged in using ChatGPT",
        "allowed_path_alias_warning_observed": warning,
        "auth_mode": "codex_login",
    }


def copy_toolchain(root: Path) -> tuple[dict[str, Any], dict[str, Path]]:
    if root.exists():
        raise RuntimeError(f"wave_004 toolchain snapshot already exists: {root}")
    paths = {
        "base_checklist_guardrails": LIVE_NEURIPS / "checklist_guardrails.py",
        "checklist_guardrails": LIVE_STRICT_GUARDRAILS,
        "draft_prompt": LIVE_NEURIPS / "prompts" / "draft_case_checklist.prompt.md",
        "source_pointer_prompt": LIVE_POINTER_PROMPT,
        "fresh_prompt_supplement": LIVE_PROMPT,
        "draft_template": LIVE_NEURIPS / "templates" / "case_checklist.template.yaml",
        "checklist_schema": LIVE_NEURIPS / "schemas" / "case_checklist.schema.json",
        "validator": LIVE_NEURIPS / "scripts" / "checklist_validator.py",
        "drafter": LIVE_NEURIPS / "scripts" / "draft_case_checklist.py",
        "batch_runner": LIVE_NEURIPS / "scripts" / "run_draft_batch.py",
        "wrapper": LIVE_WRAPPER,
        "readonly_helper": LIVE_READONLY_HELPER,
    }
    destinations = {
        "base_checklist_guardrails": SNAPSHOT_PACKAGE / "_base_checklist_guardrails.py",
        "checklist_guardrails": SNAPSHOT_PACKAGE / "checklist_guardrails.py",
        "draft_prompt": SNAPSHOT_PACKAGE / "prompts" / "draft_case_checklist.prompt.md",
        "source_pointer_prompt": SNAPSHOT_PACKAGE
        / "prompts"
        / "androidworld_source_pointer_strict_v3.supplement.md",
        "fresh_prompt_supplement": SNAPSHOT_PACKAGE
        / "prompts"
        / "androidworld_fresh_canonical_v6.supplement.md",
        "draft_template": SNAPSHOT_PACKAGE / "templates" / "case_checklist.template.yaml",
        "checklist_schema": SNAPSHOT_PACKAGE / "schemas" / "case_checklist.schema.json",
        "validator": SNAPSHOT_PACKAGE / "scripts" / "checklist_validator.py",
        "drafter": SNAPSHOT_PACKAGE / "scripts" / "draft_case_checklist.py",
        "batch_runner": SNAPSHOT_PACKAGE / "scripts" / "run_draft_batch.py",
        "wrapper": root / "run_fresh_draft_wave_v4.py",
        "readonly_helper": root / "readonly_snapshot_helper.py",
    }
    for name, source in paths.items():
        if source.is_symlink() or not source.is_file():
            raise RuntimeError(f"missing snapshot source {name}: {source}")
        destination = destinations[name]
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Copy bytes only.  The protected live NeurIPS tree carries macOS uchg
        # flags, which must not leak into the newly created snapshot before its
        # own permissions are applied and recorded.
        shutil.copyfile(source, destination)
    files = [
        binding(path)
        for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file())
    ]
    manifest = {
        "schema_version": "androidworld_candidate116_draft_toolchain_snapshot/v4_clean",
        "status": "frozen_before_first_model_call",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "snapshot_root_absolute": str(root.resolve()),
        "file_count": len(files),
        "files": files,
        "files_sha256": canonical_sha256(files),
        "roles": {name: binding(path) for name, path in sorted(destinations.items())},
        "live_origins": {name: binding(path) for name, path in sorted(paths.items())},
        "old_draft_content_in_snapshot": False,
    }
    manifest["snapshot_sha256"] = canonical_sha256(manifest)
    write_json_create_once(SNAPSHOT_MANIFEST, manifest)
    for path in sorted((candidate for candidate in root.rglob("*") if candidate.is_file())):
        path.chmod(0o444)
    for path in sorted((candidate for candidate in root.rglob("*") if candidate.is_dir()), reverse=True):
        path.chmod(0o555)
    root.chmod(0o555)
    return manifest, destinations


def load_readonly_helper(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("wave004_prepare_readonly_helper", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load read-only helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_independent_go() -> dict[str, Any]:
    go = load_json(INDEPENDENT_GO)
    verify_self_hash(go, "audit_sha256", "wave_004 v6 independent GO")
    required_gates = {
        "canonical_prompt_gate",
        "source_pointer_gate",
        "runtime_isolation_gate",
        "signal_cleanup_gate",
        "argv_detection_gate",
        "exact_six_concurrency_gate",
        "native_batch_discovery_gate",
    }
    gates = go.get("gates")
    expected_artifacts = {
        "audit_script": binding(INDEPENDENT_AUDIT),
        "preparer": binding(SCRIPT),
        "wrapper": binding(LIVE_WRAPPER),
        "canonical_prompt": binding(LIVE_PROMPT),
        "base_prompt": binding(LIVE_NEURIPS / "prompts" / "draft_case_checklist.prompt.md"),
        "source_pointer_prompt": binding(LIVE_POINTER_PROMPT),
        "base_guardrails": binding(LIVE_NEURIPS / "checklist_guardrails.py"),
        "strict_guardrails": binding(LIVE_STRICT_GUARDRAILS),
        "drafter": binding(LIVE_NEURIPS / "scripts" / "draft_case_checklist.py"),
        "batch_runner": binding(LIVE_NEURIPS / "scripts" / "run_draft_batch.py"),
        "validator": binding(LIVE_NEURIPS / "scripts" / "checklist_validator.py"),
        "schema": binding(LIVE_NEURIPS / "schemas" / "case_checklist.schema.json"),
        "template": binding(LIVE_NEURIPS / "templates" / "case_checklist.template.yaml"),
        "packet_index": binding(PACKET_INDEX),
        "canonical_input_freeze": binding(INPUT_FREEZE),
    }
    if (
        go.get("schema_version")
        != "androidworld_candidate116_wave004_v6_clean_independent_go/v1"
        or go.get("status") != "go"
        or go.get("model_calls_made") != 0
        or go.get("draft_outputs_created") != 0
        or not isinstance(gates, dict)
        or set(gates) != required_gates
        or any(value != "pass" for value in gates.values())
        or go.get("artifacts") != expected_artifacts
    ):
        raise RuntimeError("wave_004 canonical/v6 independent GO record is invalid or stale")
    return go


def main() -> int:
    args = parse_args()
    if not args.dry_run and not INDEPENDENT_GO.is_file():
        raise RuntimeError(
            "NO-GO: canonical/v6 prelock requires a create-once independent GO record "
            "after prompt, pointer, runtime-isolation, signal, argv, and concurrency gates pass"
        )
    independent_go = verify_independent_go() if not args.dry_run else None
    rejected_gate = load_json(REJECTED_GATE)
    if (
        rejected_gate.get("schema_version")
        != "androidworld_candidate116_wave004_rejected_gate/v1"
        or rejected_gate.get("status") != "REJECTED_DO_NOT_USE_AS_GO"
        or rejected_gate.get("replacement_namespace") != "wave_004_v6_clean"
        or rejected_gate.get("effects", {}).get("model_calls_authorized") is not False
    ):
        raise RuntimeError("required rejected predecessor gate record is invalid")
    persistent_targets = (
        CONFIG_PATH,
        AGENTS_CONFIG,
        PRELOCK_PATH,
        READONLY_BEFORE,
        SNAPSHOT_ROOT,
        OUTPUT_ROOT,
    )
    if any(path.exists() or path.is_symlink() for path in persistent_targets):
        raise RuntimeError("wave_004 prelock/output target already exists")
    if any(CANONICAL_DRAFTS.rglob("*")) or (
        CANONICAL_CONTRACTS.exists() and any(CANONICAL_CONTRACTS.rglob("*"))
    ):
        raise RuntimeError("canonical drafts/contracts must be empty before wave_004")
    packet_index = load_json(PACKET_INDEX)
    input_freeze = load_json(INPUT_FREEZE)
    supersession = load_json(SUPERSESSION)
    verify_self_hash(input_freeze, "freeze_sha256", "canonical draft input freeze")
    verify_self_hash(supersession, "incident_sha256", "wave_003 supersession")
    index_items = list(packet_index.get("items") or [])
    freeze_records = list(input_freeze.get("records") or [])
    if (
        packet_index.get("candidate_count") != 116
        or len(index_items) != 116
        or len(freeze_records) != 116
        or input_freeze.get("status") != "frozen"
        or input_freeze.get("case_order", {}).get("case_count") != 116
    ):
        raise RuntimeError("canonical packet index/input freeze is invalid")
    if input_freeze.get("artifacts", {}).get("packet_index", {}).get("sha256") != sha256_file(
        PACKET_INDEX
    ):
        raise RuntimeError("canonical input freeze does not bind the packet index")
    freeze_by_case = {row.get("case_unit_id"): row for row in freeze_records}
    cases: list[dict[str, Any]] = []
    for item in index_items:
        case_id = str(item.get("case_unit_id") or "")
        relative = Path(str(item.get("case_packet_path") or ""))
        packet = REPO_ROOT / relative
        frozen = freeze_by_case.get(case_id) or {}
        if (
            not case_id
            or item.get("task_id") != case_id
            or packet.parent.name != case_id
            or item.get("case_packet_sha256") != sha256_file(packet)
            or frozen.get("full_case_packet_path") != relative.as_posix()
            or frozen.get("full_case_packet_sha256") != sha256_file(packet)
        ):
            raise RuntimeError(f"canonical packet binding mismatch: {case_id}")
        packet_text = packet.read_text(encoding="utf-8")
        forbidden_markers = (
            "# AndroidWorld Fresh Draft Packet",
            "## Fresh Generation Control",
            "prior_rejected_draft_issue",
            "## Authoritative Full Case Packet",
        )
        if any(marker in packet_text for marker in forbidden_markers):
            raise RuntimeError(f"old-draft-derived wrapper content in canonical packet: {case_id}")
        cases.append(
            {
                "case_unit_id": case_id,
                "task_id": case_id,
                "selection_rank": item.get("selection_rank"),
                "group": item.get("group"),
                "packet": binding(packet),
            }
        )
    case_order = [row["case_unit_id"] for row in cases]
    if (
        len(set(case_order)) != 116
        or case_order != input_freeze.get("case_order", {}).get("case_unit_ids")
    ):
        raise RuntimeError("canonical packet order differs from the frozen candidate116 order")

    environment = exact_environment(Path.home() / ".codex")
    codex = codex_preflight(environment)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry_run_pass",
                    "case_count": len(cases),
                    "model_input": "116 complete canonical case packets only",
                    "old_draft_content_or_issue_warnings_visible": False,
                    "codex": codex,
                    "environment_key_count": len(environment),
                    "max_parallel": args.max_parallel,
                },
                indent=2,
            )
        )
        return 0

    snapshot, roles = copy_toolchain(SNAPSHOT_ROOT)
    independent_go_after_copy = verify_independent_go()
    if independent_go_after_copy["audit_sha256"] != independent_go["audit_sha256"]:
        raise RuntimeError("independent GO record changed while copying the toolchain")
    origin_to_go = {
        "draft_prompt": "base_prompt",
        "source_pointer_prompt": "source_pointer_prompt",
        "base_checklist_guardrails": "base_guardrails",
        "checklist_guardrails": "strict_guardrails",
        "fresh_prompt_supplement": "canonical_prompt",
        "drafter": "drafter",
        "batch_runner": "batch_runner",
        "validator": "validator",
        "draft_template": "template",
        "checklist_schema": "schema",
        "wrapper": "wrapper",
    }
    if any(
        snapshot["live_origins"].get(origin) != independent_go["artifacts"].get(go_name)
        for origin, go_name in origin_to_go.items()
    ):
        raise RuntimeError("frozen toolchain origins differ from independently audited artifacts")
    readonly_helper = load_readonly_helper(roles["readonly_helper"])
    readonly_before = readonly_helper.readonly_operation_snapshot(
        phase="before_candidate116_wave004_v6_clean",
        repo_root=REPO_ROOT,
        work_root=WORK_ROOT,
    )
    readonly_before["snapshot_sha256"] = canonical_sha256(readonly_before)
    write_json_create_once(READONLY_BEFORE, readonly_before)

    python = (REPO_ROOT / ".venv" / "bin" / "python").absolute()
    runtime = python_runtime_binding(python)
    packet_root = PACKET_ROOT.resolve(strict=True)
    batch_command = [
        str(python),
        str(roles["batch_runner"].resolve()),
        "--case-packet-root",
        str(packet_root),
        "--output-root",
        str(OUTPUT_ROOT.resolve()),
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
        "--prompt-supplement",
        str(roles["fresh_prompt_supplement"].resolve()),
        "--quality-check",
        "none",
        "--sort-by",
        "name",
    ]
    if "--appworld-v56-runtime-gate" in batch_command:
        raise RuntimeError("AppWorld-specific runtime gate must not be used for AndroidWorld")
    llm_roles = {
        "checklist_drafter": {
            "provider": "codex_cli",
            "auth_mode": "codex_login",
            "model": args.model,
            "reasoning_effort": args.reasoning_effort,
            "model_verbosity": "low",
            "sandbox": "read-only",
            "ephemeral": True,
            "ignore_user_config": True,
            "max_parallel": args.max_parallel,
            "token_budgets": [int(value) for value in args.token_budgets.split(",")],
        }
    }
    agents_config = {
        "schema_version": "agents/v1",
        "status": "frozen_before_first_model_call",
        "generation_id": "wave_004_v6_clean",
        "input_policy": {
            "visible_inputs": [
                "complete canonical case_packet.md",
                "frozen NeurIPS base prompt and source-pointer supplement",
                "androidworld_fresh_canonical_v6 supplement",
                "frozen checklist schema and template",
            ],
            "forbidden_inputs": [
                "any earlier checklist or draft",
                "any earlier draft review, score, issue list, or repair note",
                "agent run identity, trace, outcome, or score",
            ],
        },
        "llm_roles": llm_roles,
        "llm_roles_sha256": canonical_sha256(llm_roles),
    }
    agents_config["config_sha256"] = canonical_sha256(agents_config)
    write_json_create_once(AGENTS_CONFIG, agents_config)
    config = {
        "schema_version": "androidworld_candidate116_codex_draft_config/v6_clean",
        "status": "prelocked",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "generation_id": "wave_004_v6_clean",
        "repository_root_absolute": str(REPO_ROOT.resolve()),
        "work_root_absolute": str(WORK_ROOT.resolve()),
        "output_root_absolute": str(OUTPUT_ROOT.resolve()),
        "canonical_drafts_absolute": str(CANONICAL_DRAFTS.resolve()),
        "canonical_contracts_absolute": str(CANONICAL_CONTRACTS.resolve()),
        "concurrency_samples_absolute": str((OUTPUT_ROOT / "_concurrency_samples.jsonl").resolve()),
        "provider": "codex_cli",
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "sandbox": "read-only",
        "max_parallel": args.max_parallel,
        "large_max_parallel": args.max_parallel,
        "large_case_threshold_bytes": args.large_case_threshold_bytes,
        "token_budgets": [int(value) for value in args.token_budgets.split(",")],
        "codex_timeout_seconds": args.codex_timeout_seconds,
        "large_codex_timeout_seconds": args.large_codex_timeout_seconds,
        "child_environment": environment,
        "child_environment_sha256": canonical_sha256(environment),
        "codex_cli": codex,
        "python_runtime": runtime,
        "native_batch_command": batch_command,
        "native_batch_command_sha256": canonical_sha256(batch_command),
        "toolchain_snapshot": binding(SNAPSHOT_MANIFEST)
        | {"snapshot_sha256": snapshot["snapshot_sha256"]},
        "frozen_wrapper": binding(roles["wrapper"]),
        "frozen_drafter": binding(roles["drafter"]),
        "frozen_batch_runner": binding(roles["batch_runner"]),
        "frozen_prompt_supplement": binding(roles["fresh_prompt_supplement"]),
        "frozen_readonly_helper": binding(roles["readonly_helper"]),
        "agents_config": binding(AGENTS_CONFIG),
        "llm_roles": llm_roles,
        "llm_roles_sha256": canonical_sha256(llm_roles),
        "case_count": 116,
        "case_order": [row["case_unit_id"] for row in cases],
        "case_order_sha256": canonical_sha256([row["case_unit_id"] for row in cases]),
        "old_draft_reuse_forbidden": True,
        "model_input_policy": "complete canonical packets only; no prior draft-derived content",
        "old_draft_content_or_issue_warnings_visible": False,
    }
    config["config_sha256"] = canonical_sha256(config)
    write_json_create_once(CONFIG_PATH, config)
    prelock = {
        "schema_version": "androidworld_candidate116_codex_draft_prelock/v6_clean",
        "status": "frozen_before_first_model_call",
        "frozen_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "generation_id": "wave_004_v6_clean",
        "repository_root_absolute": str(REPO_ROOT.resolve()),
        "case_count": 116,
        "case_order": config["case_order"],
        "case_order_sha256": config["case_order_sha256"],
        "packet_cases": cases,
        "packet_cases_sha256": canonical_sha256(cases),
        "packet_index": binding(PACKET_INDEX),
        "canonical_input_freeze": binding(INPUT_FREEZE)
        | {"freeze_sha256": input_freeze["freeze_sha256"]},
        "superseded_wave_003": binding(SUPERSESSION)
        | {"incident_sha256": supersession["incident_sha256"]},
        "rejected_predecessor_gate": binding(REJECTED_GATE),
        "independent_go": binding(INDEPENDENT_GO)
        | {"audit_sha256": independent_go["audit_sha256"]},
        "draft_config": binding(CONFIG_PATH) | {"config_sha256": config["config_sha256"]},
        "toolchain_snapshot": config["toolchain_snapshot"],
        "readonly_before_snapshot": binding(READONLY_BEFORE)
        | {"snapshot_sha256": readonly_before["snapshot_sha256"]},
        "agents_config": config["agents_config"],
        "llm_roles": llm_roles,
        "llm_roles_sha256": config["llm_roles_sha256"],
        "prompt_supplement": config["frozen_prompt_supplement"],
        "child_environment_sha256": config["child_environment_sha256"],
        "native_batch_command_sha256": config["native_batch_command_sha256"],
        "old_draft_reuse_forbidden": True,
        "model_input_policy": "complete canonical packets only; no prior draft-derived content",
        "old_draft_content_or_issue_warnings_visible": False,
        "canonical_output_gate": {
            "raw_wave": str(OUTPUT_ROOT.resolve()),
            "canonical_drafts": str(CANONICAL_DRAFTS.resolve()),
            "canonical_contracts": str(CANONICAL_CONTRACTS.resolve()),
            "freeze_requires_116_of_116_acceptance": True,
        },
    }
    prelock["prelock_sha256"] = canonical_sha256(prelock)
    write_json_create_once(PRELOCK_PATH, prelock)
    wrapper_command = [
        str(python),
        str(roles["wrapper"].resolve()),
        "--prelock",
        str(PRELOCK_PATH.resolve()),
    ]
    print(
        json.dumps(
            {
                "status": "prelocked",
                "prelock": binding(PRELOCK_PATH) | {"prelock_sha256": prelock["prelock_sha256"]},
                "config": binding(CONFIG_PATH) | {"config_sha256": config["config_sha256"]},
                "case_count": 116,
                "max_parallel": 6,
                "run_command": wrapper_command,
                "run_command_sha256": canonical_sha256(wrapper_command),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
