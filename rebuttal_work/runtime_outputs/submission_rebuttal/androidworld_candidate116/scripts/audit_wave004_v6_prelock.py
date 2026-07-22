#!/usr/bin/env python3
"""Create-once, zero-model-call GO audit for the canonical wave_004 prelock."""

from __future__ import annotations

import ast
import datetime as dt
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).resolve()
WORK_ROOT = SCRIPT.parents[1]
REPO_ROOT = WORK_ROOT.parents[3]
GEN_ROOT = WORK_ROOT / "draft_generation"
REJECTED_GATE = GEN_ROOT / "validation" / "wave_004_v6_prelock_independent_go.json"
GO_PATH = GEN_ROOT / "validation" / "wave_004_v6_clean_independent_go.json"
PREPARER = WORK_ROOT / "scripts" / "prepare_codex_draft_prelock_v4.py"
WRAPPER = WORK_ROOT / "scripts" / "run_fresh_draft_wave_v4.py"
PROMPT = GEN_ROOT / "prompts" / "androidworld_fresh_canonical_v6.supplement.md"
POINTER_PROMPT = GEN_ROOT / "prompts" / "androidworld_source_pointer_strict_v3.supplement.md"
STRICT_GUARDRAILS = WORK_ROOT / "scripts" / "strict_checklist_guardrails_v6_clean.py"
NEURIPS = REPO_ROOT / "neurips_ed_track_minimal"
PACKET_ROOT = WORK_ROOT / "case_packets" / "androidworld"
PACKET_INDEX = WORK_ROOT / "indexes" / "androidworld_candidate116_packet_index.json"
INPUT_FREEZE = WORK_ROOT / "freeze" / "androidworld_candidate116_draft_input_freeze.json"
OUTPUT_ROOT = GEN_ROOT / "waves" / "wave_004_v6_clean"
CANONICAL_DRAFTS = WORK_ROOT / "drafts"
CANONICAL_CONTRACTS = WORK_ROOT / "contracts" / "drafts"


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


def binding(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if path.is_symlink() or not resolved.is_file():
        raise RuntimeError(f"regular non-symlink file required: {path}")
    return {
        "path": str(resolved),
        "sha256": sha256_file(resolved),
        "size_bytes": resolved.stat().st_size,
    }


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON object required: {path}")
    return value


def import_wrapper() -> Any:
    spec = importlib.util.spec_from_file_location("wave004_v6_audited_wrapper", WRAPPER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import wave_004 wrapper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_clean_namespace() -> None:
    if GO_PATH.exists() or GO_PATH.is_symlink():
        raise RuntimeError("independent GO record already exists")
    if OUTPUT_ROOT.exists() or OUTPUT_ROOT.is_symlink():
        raise RuntimeError("wave_004 output root must be absent")
    if any(CANONICAL_DRAFTS.rglob("*")) or (
        CANONICAL_CONTRACTS.exists() and any(CANONICAL_CONTRACTS.rglob("*"))
    ):
        raise RuntimeError("canonical drafts/contracts must remain empty")
    rejected = load_json(REJECTED_GATE)
    if (
        rejected.get("status") != "REJECTED_DO_NOT_USE_AS_GO"
        or rejected.get("replacement_namespace") != "wave_004_v6_clean"
        or rejected.get("effects", {}).get("model_calls_authorized") is not False
    ):
        raise RuntimeError("rejected predecessor gate is missing or invalid")


def audit_prompt() -> dict[str, Any]:
    text = PROMPT.read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    required = (
        "complete canonical case packet",
        "No earlier checklist, review, score, repair note, or audit finding",
        "metadata-versus-runtime difference",
        "parameter-schema-versus-generator difference",
        "initialize_task",
        "complete `is_successful` implementation",
        "interaction_results.done",
        "agent_successful > 0.5",
        "exceptions; NaN; an absent numeric raw score",
        "one measurable stronger condition",
        "must be copied verbatim from the packet's `## Source Inventory`",
        "Never cite the packet itself",
        "116/116",
    )
    missing = [needle for needle in required if needle not in normalized]
    if missing or "prior_rejected_draft_issue" in text:
        raise RuntimeError(f"canonical v6 prompt gate failed: missing={missing}")
    return {"required_clause_count": len(required), "prompt_sha256": sha256_file(PROMPT)}


def audit_pointers() -> dict[str, Any]:
    pointer_text = POINTER_PROMPT.read_text(encoding="utf-8")
    guardrail_text = STRICT_GUARDRAILS.read_text(encoding="utf-8")
    if not all(
        needle in pointer_text
        for needle in (
            "## Source Inventory",
            "`case_packet.md` is not a source path and is forbidden",
            "rationale text never substitutes for support",
        )
    ):
        raise RuntimeError("clean source-pointer supplement is incomplete")
    if not all(
        needle in guardrail_text
        for needle in (
            "case_packet_support_paths",
            'allowed.discard("case_packet.md")',
            "rationale never substitutes",
        )
    ):
        raise RuntimeError("clean deterministic source-pointer guardrail is incomplete")
    if "Never cite the packet itself" not in PROMPT.read_text(encoding="utf-8"):
        raise RuntimeError("canonical v6 prompt does not close the case_packet.md alias")

    runtime = (REPO_ROOT / ".venv" / "bin" / "python").absolute()
    packet = sorted(PACKET_ROOT.glob("*/case_packet.md"))[0]
    inventory = []
    in_inventory = False
    for line in packet.read_text(encoding="utf-8").splitlines():
        if line == "## Source Inventory":
            in_inventory = True
            continue
        if in_inventory and line.startswith("## "):
            break
        if in_inventory and line.startswith("- `") and line.endswith("`"):
            inventory.append(line[3:-1])
    if not inventory:
        raise RuntimeError("fixture packet has no Source Inventory")
    pointer = f"{inventory[0]}::L1"
    case_id = packet.parent.name
    valid = {
        "schema_version": "case_checklist_v1",
        "case_unit_id": case_id,
        "domain": "androidworld",
        "task_id": case_id,
        "native": {
            "user_goal": {"text": "Complete the runtime-generated task.", "support": [pointer]},
            "benchmark_success": {
                "text": "The raw evaluator and runner gate accept the episode.",
                "support": [pointer],
            },
            "checked_by": {"text": "The retained evaluator result.", "support": [pointer]},
            "decisive_artifacts": [
                {
                    "artifact": "retained evaluator result",
                    "question": "Does the retained result satisfy the evaluator and runner gate?",
                    "support": [pointer],
                }
            ],
            "success_if": [
                {
                    "text": "The raw evaluator accepts, done is true, and score exceeds 0.5.",
                    "support": [pointer],
                }
            ],
            "fail_if": [
                {
                    "text": "The raw evaluator rejects, done is false, or score is at or below 0.5.",
                    "support": [pointer],
                }
            ],
            "undecided_if": [
                {
                    "text": "Required evaluator evidence is missing or corrupt, so the result cannot be reconstructed.",
                    "support": [pointer],
                }
            ],
        },
        "stronger": {"additional_conditions": []},
    }
    missing_support = json.loads(json.dumps(valid))
    missing_support["native"]["user_goal"].pop("support")
    missing_support["native"]["user_goal"]["rationale"] = "Rationale only is forbidden."

    alias = json.loads(json.dumps(valid))

    def replace_support(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "support":
                    value[key] = ["case_packet.md::L1"]
                else:
                    replace_support(child)
        elif isinstance(value, list):
            for child in value:
                replace_support(child)

    replace_support(alias)
    with tempfile.TemporaryDirectory(prefix="wave004-v6-clean-validator-") as temp:
        root = Path(temp)
        package = root / "neurips_ed_track_minimal"
        (package / "scripts").mkdir(parents=True)
        (package / "schemas").mkdir(parents=True)
        shutil.copyfile(NEURIPS / "checklist_guardrails.py", package / "_base_checklist_guardrails.py")
        shutil.copyfile(STRICT_GUARDRAILS, package / "checklist_guardrails.py")
        shutil.copyfile(
            NEURIPS / "scripts" / "checklist_validator.py",
            package / "scripts" / "checklist_validator.py",
        )
        shutil.copyfile(
            NEURIPS / "schemas" / "case_checklist.schema.json",
            package / "schemas" / "case_checklist.schema.json",
        )
        outcomes: dict[str, subprocess.CompletedProcess[str]] = {}
        for name, value in (
            ("valid", valid),
            ("missing_support", missing_support),
            ("case_packet_alias", alias),
        ):
            checklist = root / f"{name}.json"
            checklist.write_text(json.dumps(value), encoding="utf-8")
            outcomes[name] = subprocess.run(
                [
                    str(runtime),
                    str(package / "scripts" / "checklist_validator.py"),
                    str(checklist),
                    "--case-packet",
                    str(packet),
                ],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
        if outcomes["valid"].returncode != 0:
            raise RuntimeError(f"strict validator rejected valid fixture: {outcomes['valid'].stderr}")
        if outcomes["missing_support"].returncode == 0 or "rationale never substitutes" not in outcomes[
            "missing_support"
        ].stderr:
            raise RuntimeError("strict validator accepted rationale-only native support fixture")
        if outcomes["case_packet_alias"].returncode == 0:
            raise RuntimeError("strict validator accepted forbidden case_packet.md alias fixture")
    return {
        "source_pointer_prompt_sha256": sha256_file(POINTER_PROMPT),
        "base_guardrails_sha256": sha256_file(NEURIPS / "checklist_guardrails.py"),
        "strict_guardrails_sha256": sha256_file(STRICT_GUARDRAILS),
        "canonical_v6_forbids_case_packet_alias": True,
        "valid_fixture_accepted": True,
        "rationale_only_fixture_rejected": True,
        "case_packet_alias_fixture_rejected": True,
    }


def audit_runtime_isolation() -> dict[str, Any]:
    drafter = NEURIPS / "scripts" / "draft_case_checklist.py"
    batch = NEURIPS / "scripts" / "run_draft_batch.py"
    preparer_text = PREPARER.read_text(encoding="utf-8")
    wrapper_text = WRAPPER.read_text(encoding="utf-8")
    drafter_text = drafter.read_text(encoding="utf-8")
    batch_text = batch.read_text(encoding="utf-8")
    required_preparer = (
        '"max_parallel": args.max_parallel',
        '"large_max_parallel": args.max_parallel',
        '"sandbox": "read-only"',
        '"model": args.model',
        '"reasoning_effort": args.reasoning_effort',
        '"old_draft_content_or_issue_warnings_visible": False',
    )
    required_drafter = (
        '"--ephemeral"',
        '"--ignore-user-config"',
        '"--sandbox"',
        'model_verbosity="low"',
        'model_reasoning_effort=',
    )
    if any(value not in preparer_text for value in required_preparer):
        raise RuntimeError("preparer runtime-isolation declarations are incomplete")
    if any(value not in drafter_text for value in required_drafter):
        raise RuntimeError("NeurIPS Codex runtime-isolation flags are incomplete")
    if "set(environment) != EXPECTED_ENV_KEYS" not in wrapper_text:
        raise RuntimeError("wrapper does not enforce the exact closed child environment")
    if "verify_python_runtime(config, environment)" not in wrapper_text:
        raise RuntimeError("wrapper does not verify the bound venv invocation and dependencies")
    batch_block = preparer_text.split("batch_command =", 1)[1].split("llm_roles =", 1)[0]
    if (
        batch_block.count('"--appworld-v56-runtime-gate"') != 1
        or 'if "--appworld-v56-runtime-gate" in batch_command:' not in batch_block
    ):
        raise RuntimeError("AndroidWorld AppWorld-only flag exclusion guard is not exact")
    if "ThreadPoolExecutor(max_workers=lane_parallel)" not in batch_text:
        raise RuntimeError("native batch parallel executor is not present")
    return {
        "drafter_sha256": sha256_file(drafter),
        "batch_runner_sha256": sha256_file(batch),
        "closed_child_environment_key_count": 9,
        "codex_ephemeral_ignore_user_config_read_only": True,
    }


def audit_argv(wrapper: Any) -> dict[str, Any]:
    positives = (
        ["/opt/homebrew/bin/codex", "exec"],
        ["/opt/codex-aarch64-apple-darwin", "exec"],
        [sys.executable, "/tmp/run_draft_batch.py"],
        [sys.executable, "/tmp/draft_case_checklist.py"],
    )
    negatives = (
        ["/opt/homebrew/bin/codex", "login", "status"],
        ["python", "-c", "text mentioning /codex exec only inside one argument"],
        ["rg", "run_draft_batch.py"],
    )
    if not all(wrapper.is_drafting_argv(list(argv)) for argv in positives):
        raise RuntimeError("draft-process argv positive detection failed")
    if any(wrapper.is_drafting_argv(list(argv)) for argv in negatives):
        raise RuntimeError("draft-process argv false-positive rejection failed")
    return {"positive_fixture_count": len(positives), "negative_fixture_count": len(negatives)}


def audit_signal_cleanup(wrapper: Any) -> dict[str, Any]:
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        start_new_session=True,
    )
    wrapper.terminate_group(process)
    if process.poll() is None:
        raise RuntimeError("process-group cleanup left the audit process alive")
    return {"process_group_terminated": True, "returncode": process.returncode}


def monitor_fixture(wrapper: Any, count: int, sample_path: Path) -> dict[str, Any]:
    packet_paths = [
        str(path.resolve())
        for path in sorted(PACKET_ROOT.glob("*/case_packet.md"))[:count]
    ]
    drafter = (NEURIPS / "scripts" / "draft_case_checklist.py").resolve()
    child_code = (
        "import json,os,subprocess,sys;"
        "d=os.environ['AUDIT_DRAFTER'];p=json.loads(os.environ['AUDIT_PACKETS']);"
        "c=[subprocess.Popen([sys.executable,'-c','import time;time.sleep(2)',d,x]) for x in p];"
        "[q.wait() for q in c]"
    )
    environment = dict(os.environ)
    environment["AUDIT_DRAFTER"] = str(drafter)
    environment["AUDIT_PACKETS"] = json.dumps(packet_paths)
    process = subprocess.Popen(
        [sys.executable, "-c", child_code],
        env=environment,
        start_new_session=True,
    )
    stop = threading.Event()
    lock = threading.Lock()
    state: dict[str, Any] = {"sample_count": 0, "peak": 0, "covered": set(), "errors": []}
    packet_cases = [
        {"case_unit_id": Path(path).parent.name, "packet": {"path": path}}
        for path in packet_paths
    ]
    thread = threading.Thread(
        target=wrapper.monitor_batch,
        kwargs={
            "process": process,
            "config": {
                "concurrency_samples_absolute": str(sample_path),
                "frozen_drafter": binding(drafter),
            },
            "prelock": {"packet_cases": packet_cases},
            "stop": stop,
            "state": state,
            "state_lock": lock,
        },
        daemon=False,
    )
    thread.start()
    try:
        process.wait(timeout=15)
    finally:
        stop.set()
        thread.join(timeout=10)
        if process.poll() is None:
            wrapper.terminate_group(process)
    if thread.is_alive() or state["errors"]:
        raise RuntimeError(f"exact-six monitor fixture failed: {state['errors']}")
    return {
        "requested_active_count": count,
        "observed_peak": state["peak"],
        "observed_case_count": len(state["covered"]),
        "sample_count": state["sample_count"],
        "samples_sha256": sha256_file(sample_path),
    }


def audit_concurrency(wrapper: Any) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="wave004-v6-concurrency-audit-") as temp:
        result = monitor_fixture(wrapper, 6, Path(temp) / "samples.jsonl")
    if result["observed_peak"] != 6 or result["observed_case_count"] != 6:
        raise RuntimeError(f"exact-six concurrency fixture did not observe six: {result}")
    wrapper_text = WRAPPER.read_text(encoding="utf-8")
    if (
        "if len(active) > EXPECTED_PARALLELISM" not in wrapper_text
        or "if peak != EXPECTED_PARALLELISM" not in wrapper_text
        or "covered != sorted(prelock[\"case_order\"])" not in wrapper_text
    ):
        raise RuntimeError("production exact-six/coverage fail-closed gates are incomplete")
    return result | {"production_never_above_six_gate": True, "production_116_coverage_gate": True}


def audit_native_batch_discovery() -> dict[str, Any]:
    runtime = (REPO_ROOT / ".venv" / "bin" / "python").absolute()
    if not runtime.is_symlink():
        raise RuntimeError("repository venv Python invocation is not a symlink")
    dependency_probe = subprocess.run(
        [runtime, "-c", "import jsonschema,requests,yaml; print('audit-runtime-ok')"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if dependency_probe.returncode != 0 or dependency_probe.stdout.strip() != "audit-runtime-ok":
        raise RuntimeError("repository venv dependency probe failed")
    with tempfile.TemporaryDirectory(prefix="wave004-v6-batch-dryrun-") as temp:
        command = [
            str(runtime),
            str(NEURIPS / "scripts" / "run_draft_batch.py"),
            "--case-packet-root",
            str(PACKET_ROOT),
            "--output-root",
            str(Path(temp) / "never-created-output"),
            "--provider",
            "codex",
            "--model",
            "gpt-5.6-sol",
            "--reasoning-effort",
            "xhigh",
            "--max-parallel",
            "6",
            "--large-max-parallel",
            "6",
            "--large-case-threshold-bytes",
            "900000",
            "--codex-sandbox",
            "read-only",
            "--prompt-supplement",
            str(PROMPT),
            "--quality-check",
            "none",
            "--sort-by",
            "name",
            "--dry-run",
        ]
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        if completed.returncode != 0 or "discovered_case_count=116" not in completed.stdout:
            raise RuntimeError(
                f"native NeurIPS 116-case dry-run failed: rc={completed.returncode} "
                f"stderr={completed.stderr.strip()}"
            )
    return {
        "discovered_case_count": 116,
        "python_invocation_path": str(runtime),
        "python_resolved_binary": binding(runtime.resolve(strict=True)),
        "pyvenv_cfg": binding(runtime.parent.parent / "pyvenv.cfg"),
        "native_batch_command_sha256": canonical_sha256(command),
        "output_root_created": False,
    }


def main() -> int:
    assert_clean_namespace()
    for path in (SCRIPT, PREPARER, WRAPPER):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    packets = sorted(PACKET_ROOT.glob("*/case_packet.md"))
    packet_index = load_json(PACKET_INDEX)
    input_freeze = load_json(INPUT_FREEZE)
    if (
        len(packets) != 116
        or packet_index.get("candidate_count") != 116
        or input_freeze.get("case_order", {}).get("case_count") != 116
    ):
        raise RuntimeError("canonical candidate116 packet namespace is not exact")
    wrapper = import_wrapper()
    details = {
        "canonical_prompt_gate": audit_prompt(),
        "source_pointer_gate": audit_pointers(),
        "runtime_isolation_gate": audit_runtime_isolation(),
        "signal_cleanup_gate": audit_signal_cleanup(wrapper),
        "argv_detection_gate": audit_argv(wrapper),
        "exact_six_concurrency_gate": audit_concurrency(wrapper),
        "native_batch_discovery_gate": audit_native_batch_discovery(),
    }
    gates = {name: "pass" for name in details}
    artifacts = {
        "audit_script": binding(SCRIPT),
        "preparer": binding(PREPARER),
        "wrapper": binding(WRAPPER),
        "canonical_prompt": binding(PROMPT),
        "base_prompt": binding(NEURIPS / "prompts" / "draft_case_checklist.prompt.md"),
        "source_pointer_prompt": binding(POINTER_PROMPT),
        "base_guardrails": binding(NEURIPS / "checklist_guardrails.py"),
        "strict_guardrails": binding(STRICT_GUARDRAILS),
        "drafter": binding(NEURIPS / "scripts" / "draft_case_checklist.py"),
        "batch_runner": binding(NEURIPS / "scripts" / "run_draft_batch.py"),
        "validator": binding(NEURIPS / "scripts" / "checklist_validator.py"),
        "schema": binding(NEURIPS / "schemas" / "case_checklist.schema.json"),
        "template": binding(NEURIPS / "templates" / "case_checklist.template.yaml"),
        "packet_index": binding(PACKET_INDEX),
        "canonical_input_freeze": binding(INPUT_FREEZE),
    }
    record = {
        "schema_version": "androidworld_candidate116_wave004_v6_clean_independent_go/v1",
        "status": "go",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "case_count": 116,
        "model_calls_made": 0,
        "draft_outputs_created": 0,
        "gates": gates,
        "gate_details": details,
        "artifacts": artifacts,
    }
    record["audit_sha256"] = canonical_sha256(record)
    GO_PATH.parent.mkdir(parents=True, exist_ok=True)
    with GO_PATH.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    print(
        json.dumps(
            {
                "status": "go",
                "audit_sha256": record["audit_sha256"],
                "gates": gates,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
