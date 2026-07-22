"""Fail-closed BrowserGym/MiniWoB++ runtime locking and compatibility audit.

The lock has two deliberately separate decisions:

* ``lock_gate_passed`` means that the *current* BrowserGym runtime is complete,
  internally consistent, and matches the official sources captured for the old
  selected-100 cohort.
* ``direct_merge_eligible`` additionally means that every old-run compatibility
  claim (browser/runtime code, seeds, agents, and scorer protocol) is proven.

An unrecorded baseline is never treated as a match.  This lets a new cohort be
locked and generated while still preventing an unsupported union with old runs.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable, Mapping, Sequence

from evidence_system.contracts.common import (
    ContractLifecycleError,
    load_mapping,
    normalize_domain_or_none,
    write_json,
)
from evidence_system.contracts.miniwob_case_selection import MINIWOB_SELECTION_SALT
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path


SCHEMA_VERSION = "miniwob_browsergym_runtime_lock/v1"
EXPECTED_SMOKE_TASKS = (
    "miniwob.click-button",
    "miniwob.click-test",
    "miniwob.enter-text",
)
EXPECTED_AGENT_ROLES: dict[str, dict[str, Any]] = {
    "Agent A": {"provider": "openrouter", "model": "openai/gpt-5.4"},
    "Agent B": {"provider": "openrouter", "model": "anthropic/claude-opus-4.7"},
    "Agent C": {"provider": "openrouter", "model": "deepseek/deepseek-v4-pro"},
}
EXPECTED_AGENT_SHARED = {
    "temperature": 0,
    "max_tokens": 4096,
    "timeout_seconds": 120,
    "retry": 2,
}
EXPECTED_EXECUTION_PROTOCOL: dict[str, Any] = {
    "adapter_module": "evidence_system.adapters.miniwob",
    "worker_module": "evidence_system.adapters.miniwob_worker",
    "driver": "openrouter_chat",
    "action_set": {"class": "HighLevelActionSet", "multiaction": False, "strict": False},
    "native_evaluator": "env.unwrapped.task.validate(page, chat_messages)",
}
DEFAULT_CATALOGS = (
    "experiments/official_splits/miniwob_official_task_catalog_122.json",
    "experiments/official_splits/miniwob_second50/miniwob_official_task_catalog_122.json",
)
DEFAULT_SELECTED_SOURCES = (
    "experiments/official_splits/miniwob_selected_task_sources.json",
    "experiments/official_splits/miniwob_second50/miniwob_selected_task_sources.json",
)
DEFAULT_CODE_COMPONENTS = (
    "src/evidence_system/adapters/miniwob.py",
    "src/evidence_system/adapters/miniwob_worker.py",
    "src/evidence_system/adapters/runtime.py",
    "src/evidence_system/orchestrator/jobs.py",
)
DEFAULT_SCORE_PROMPT = "neurips_ed_track_minimal/prompts/score_evidence_with_codex.prompt.md"
DEFAULT_SCORE_SCHEMA = "neurips_ed_track_minimal/schemas/evidence_score.schema.json"
DEFAULT_SCORE_SCRIPT = "neurips_ed_track_minimal/scripts/score_evidence_with_codex.py"


class MiniWoBRuntimeLockError(ContractLifecycleError):
    """Raised when the runtime cannot be inspected at all."""


@dataclass(frozen=True)
class RuntimeCheck:
    check_id: str
    scope: str
    status: str
    message: str
    evidence: dict[str, Any]

    def __post_init__(self) -> None:
        if self.scope not in {"lock", "direct_merge"}:
            raise ValueError(f"invalid runtime-check scope: {self.scope}")
        if self.status not in {"passed", "failed", "unproven"}:
            raise ValueError(f"invalid runtime-check status: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "scope": self.scope,
            "status": self.status,
            "message": self.message,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class MiniWoBLocalRuntime:
    python_bin: Path
    install_dir: Path
    html_root: Path
    benchmark_config: dict[str, Any]
    machine_id: str
    machine_config: dict[str, Any]
    infra_config: dict[str, Any]


@dataclass(frozen=True)
class MiniWoBExecutionInfra:
    benchmark_config: dict[str, Any]
    machine_id: str
    machine_config: dict[str, Any]
    infra_config: dict[str, Any]
    result_namespace: str | None


def registry_fingerprint(
    task_ids: Sequence[str],
    *,
    smoke_task_ids: Sequence[str] = EXPECTED_SMOKE_TASKS,
) -> dict[str, Any]:
    """Reproduce the selector's deterministic 125-minus-3 fingerprint."""

    registry = [str(task_id).strip() for task_id in task_ids]
    if any(not task_id for task_id in registry):
        raise MiniWoBRuntimeLockError("BrowserGym registry contains an empty task id")
    if len(set(registry)) != len(registry):
        duplicates = sorted(task_id for task_id, count in Counter(registry).items() if count > 1)
        raise MiniWoBRuntimeLockError(f"BrowserGym registry contains duplicate task ids: {duplicates}")
    smoke = sorted({str(task_id).strip() for task_id in smoke_task_ids if str(task_id).strip()})
    eligible = sorted(set(registry) - set(smoke))
    records: list[dict[str, Any]] = []
    for task_id in eligible:
        order_key = sha256_object(
            {
                "salt": MINIWOB_SELECTION_SALT,
                "domain": "miniwob",
                "case_unit_id": task_id,
                "task_id": task_id,
            }
        )
        records.append(
            {
                "case_unit_id": task_id,
                "task_id": task_id,
                "selection_order_key": order_key,
            }
        )
    records.sort(key=lambda item: (item["selection_order_key"], item["case_unit_id"]))
    for selection_rank, item in enumerate(records):
        item["selection_rank"] = selection_rank
    case_unit_records = [
        {"case_unit_id": task_id, "task_id": task_id}
        for task_id in sorted(eligible)
    ]
    return {
        "catalog_count": len(registry),
        "candidate_count": len(eligible),
        "registry_task_ids": sorted(registry),
        "excluded_smoke_case_units": smoke,
        "smoke_exclusion_hash": sha256_object(smoke),
        "selection_salt_hash": sha256_object(MINIWOB_SELECTION_SALT),
        "eligible_case_unit_set_hash": sha256_object(case_unit_records),
        "case_selection_order_hash": sha256_object(records),
        "selection_records": records,
    }


def load_local_runtime(infra_config_path: str | Path) -> MiniWoBLocalRuntime:
    """Resolve a concrete local MiniWoB runtime from a locked infra file."""

    infra = load_mapping(infra_config_path)
    for machine in list(infra.get("machines") or []):
        if not isinstance(machine, Mapping) or machine.get("enabled") is False:
            continue
        benchmark = _miniwob_benchmark_config(machine)
        if not benchmark:
            continue
        raw_values = {
            "python_bin": str(benchmark.get("python_bin") or "").strip(),
            "install_dir": str(benchmark.get("install_dir") or "").strip(),
            "html_root": str(benchmark.get("assets_path") or "").strip(),
        }
        missing = [key for key, value in raw_values.items() if not value]
        if missing:
            raise MiniWoBRuntimeLockError(
                "MiniWoB++ locked infra is missing: " + ", ".join(missing)
            )
        placeholders = [key for key, value in raw_values.items() if re.search(r"<[^>]+>", value)]
        if placeholders:
            raise MiniWoBRuntimeLockError(
                "MiniWoB++ locked infra still contains placeholders: " + ", ".join(placeholders)
            )
        python_bin = _absolute_path(raw_values["python_bin"])
        install_dir = _absolute_path(raw_values["install_dir"]).resolve()
        html_root = _absolute_path(raw_values["html_root"]).resolve()
        if not python_bin.is_file() or not os.access(python_bin, os.X_OK):
            raise MiniWoBRuntimeLockError(f"locked MiniWoB python is not executable: {python_bin}")
        if not install_dir.is_dir():
            raise MiniWoBRuntimeLockError(f"locked MiniWoB install directory is missing: {install_dir}")
        if not html_root.is_dir():
            raise MiniWoBRuntimeLockError(f"locked MiniWoB HTML assets directory is missing: {html_root}")
        return MiniWoBLocalRuntime(
            python_bin=python_bin,
            install_dir=install_dir,
            html_root=html_root,
            benchmark_config=benchmark,
            machine_id=str(machine.get("machine_id") or ""),
            machine_config=dict(machine),
            infra_config=infra,
        )
    raise MiniWoBRuntimeLockError("locked infra has no enabled MiniWoB++ benchmark")


def load_execution_infra(infra_config_path: str | Path) -> MiniWoBExecutionInfra:
    """Load formal execution metadata without requiring remote paths locally."""

    infra = load_mapping(infra_config_path)
    for machine in list(infra.get("machines") or []):
        if not isinstance(machine, Mapping) or machine.get("enabled") is False:
            continue
        benchmark = _miniwob_benchmark_config(machine)
        if not benchmark:
            continue
        return MiniWoBExecutionInfra(
            benchmark_config=benchmark,
            machine_id=str(machine.get("machine_id") or ""),
            machine_config=dict(machine),
            infra_config=infra,
            result_namespace=_result_namespace_from_infra(infra),
        )
    raise MiniWoBRuntimeLockError("execution infra has no enabled MiniWoB++ benchmark")


def probe_browsergym_runtime(
    python_bin: str | Path,
    *,
    playwright_browsers_path: str | Path | None = None,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    """Inspect BrowserGym and launch its configured Playwright Chromium once."""

    try:
        probe_env = os.environ.copy()
        if playwright_browsers_path is not None:
            probe_env["PLAYWRIGHT_BROWSERS_PATH"] = str(playwright_browsers_path)
        completed = subprocess.run(
            [str(python_bin), "-c", _RUNTIME_PROBE_SOURCE],
            cwd=resolve_repo_path("."),
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
            env=probe_env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MiniWoBRuntimeLockError(f"BrowserGym runtime probe could not run: {exc}") from exc
    if completed.returncode != 0:
        raise MiniWoBRuntimeLockError(
            "BrowserGym runtime probe failed with exit code "
            f"{completed.returncode}: {completed.stderr.strip()}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise MiniWoBRuntimeLockError("BrowserGym runtime probe returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise MiniWoBRuntimeLockError("BrowserGym runtime probe payload must be a mapping")
    return dict(payload)


def build_miniwob_runtime_lock(
    *,
    infra_config_path: str | Path,
    execution_infra_config_path: str | Path | None = None,
    agents_config_path: str | Path = "configs/agents.yaml",
    catalog_paths: Sequence[str | Path] = DEFAULT_CATALOGS,
    selected_sources_paths: Sequence[str | Path] = DEFAULT_SELECTED_SOURCES,
    old_runs_root: str | Path = "results/full/miniwob",
    old_scores_root: str | Path = "results/scores/full/miniwob",
    score_prompt_path: str | Path = DEFAULT_SCORE_PROMPT,
    score_schema_path: str | Path = DEFAULT_SCORE_SCHEMA,
    score_script_path: str | Path = DEFAULT_SCORE_SCRIPT,
    expected_release_component_hashes: Mapping[str, str] | None = None,
    expected_release_chromium_sha256: str | None = None,
    expected_release_chromium_version: str | None = None,
    expected_release_html_inventory_sha256: str | None = None,
    base_seed: int = 7,
    runtime_probe: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a strict lock receipt without claiming unproven compatibility."""

    if len(catalog_paths) != 2 or len(selected_sources_paths) != 2:
        raise MiniWoBRuntimeLockError("exactly two old catalogs and two selected-source files are required")
    runtime = load_local_runtime(infra_config_path)
    execution_infra_explicit = execution_infra_config_path is not None
    resolved_execution_infra_path = execution_infra_config_path or infra_config_path
    execution = load_execution_infra(resolved_execution_infra_path)
    local_playwright_browsers_path = _local_playwright_browsers_path(runtime)
    probe = dict(
        runtime_probe
        or probe_browsergym_runtime(
            runtime.python_bin,
            playwright_browsers_path=local_playwright_browsers_path,
        )
    )
    checks: list[RuntimeCheck] = []

    checks.append(
        _check(
            "locked_infra_paths",
            "lock",
            True,
            "locked MiniWoB Python, install root, and HTML root are concrete local paths",
            {
                "python_bin": str(runtime.python_bin),
                "install_dir": str(runtime.install_dir),
                "html_root": str(runtime.html_root),
                "playwright_browsers_path": str(local_playwright_browsers_path),
            },
        )
    )

    if execution_infra_explicit:
        formal_execution_audit = _audit_formal_execution_infra(execution)
        checks.append(
            _check(
                "formal_execution_infra",
                "lock",
                formal_execution_audit["ok"],
                "formal execution infra is non-dry-run and isolated in one result namespace"
                if formal_execution_audit["ok"]
                else "formal execution infra is dry-run, non-namespaced, or internally inconsistent",
                formal_execution_audit,
            )
        )
    else:
        formal_execution_audit = {
            "ok": False,
            "execution_infra_explicit": False,
            "result_namespace": execution.result_namespace,
        }
        checks.append(
            RuntimeCheck(
                "formal_execution_infra_supplied",
                "direct_merge",
                "unproven",
                "no separate formal execution infra was supplied; source/runtime infra fallback was used",
                formal_execution_audit,
            )
        )

    distribution_versions = dict(probe.get("distributions") or {})
    dependency_versions_ok = bool(probe.get("python", {}).get("version")) and all(
        distribution_versions.get(name)
        for name in ("browsergym-miniwob", "browsergym-core", "gymnasium", "playwright")
    )
    checks.append(
        _check(
            "browsergym_dependency_versions_locked",
            "lock",
            dependency_versions_ok,
            "Python, BrowserGym MiniWoB/core, Gymnasium, and Playwright versions were resolved"
            if dependency_versions_ok
            else "one or more BrowserGym runtime dependency versions could not be resolved",
            {
                "python": dict(probe.get("python") or {}),
                "distributions": distribution_versions,
            },
        )
    )

    execution_settings = _audit_execution_settings(runtime)
    checks.append(
        _check(
            "miniwob_execution_settings_locked",
            "lock",
            execution_settings["ok"],
            "MiniWoB base URL, HTTP asset root, port, and 30-step full-run budget are locked"
            if execution_settings["ok"]
            else "MiniWoB execution settings are incomplete, placeholders, or differ from the 30-step protocol",
            execution_settings,
        )
    )

    chromium_probe = dict(probe.get("chromium") or {})
    browser_ok = (
        bool(chromium_probe.get("launch_ok"))
        and bool(chromium_probe.get("browser_version"))
        and bool(chromium_probe.get("executable_sha256"))
        and bool(chromium_probe.get("browsers_json_sha256"))
        and bool(chromium_probe.get("browsers_json_chromium"))
    )
    checks.append(
        _check(
            "playwright_chromium_launch",
            "lock",
            browser_ok,
            "the locked Playwright Chromium launched and its executable was hashed"
            if browser_ok
            else "the locked Playwright Chromium did not launch or has no executable hash",
            chromium_probe,
        )
    )

    source_execution_protocol = _audit_source_execution_protocol(
        runtime=runtime,
        execution=execution,
        probe=probe,
        cli_base_seed=base_seed,
    )
    checks.append(
        _check(
            "source_runtime_matches_execution_protocol",
            "lock",
            source_execution_protocol["ok"],
            "local source runtime and formal execution infra have identical execution settings and runtime pins"
            if source_execution_protocol["ok"]
            else "local source runtime and execution infra differ in execution settings or runtime pins",
            source_execution_protocol,
        )
    )

    task_ids = list(probe.get("registry_task_ids") or [])
    fingerprint = registry_fingerprint(task_ids)
    cardinality_ok = (
        fingerprint["catalog_count"] == 125
        and fingerprint["candidate_count"] == 122
        and fingerprint["excluded_smoke_case_units"] == list(EXPECTED_SMOKE_TASKS)
        and set(EXPECTED_SMOKE_TASKS).issubset(set(task_ids))
    )
    checks.append(
        _check(
            "registry_125_minus_3_equals_122",
            "lock",
            cardinality_ok,
            "BrowserGym registry is exactly 125 tasks with the three declared smoke tasks excluded"
            if cardinality_ok
            else "BrowserGym registry is not the required 125 minus three smoke tasks",
            {
                key: fingerprint[key]
                for key in (
                    "catalog_count",
                    "candidate_count",
                    "excluded_smoke_case_units",
                    "smoke_exclusion_hash",
                )
            },
        )
    )

    catalogs = [_load_json_mapping(path) for path in catalog_paths]
    catalog_receipts = [
        {
            "path": _display_path(path),
            "sha256": sha256_file(resolve_repo_path(path)),
            "identity": _catalog_identity(payload),
        }
        for path, payload in zip(catalog_paths, catalogs)
    ]
    catalog_identity_match = catalog_receipts[0]["identity"] == catalog_receipts[1]["identity"]
    current_catalog_match = all(
        _catalog_matches_fingerprint(payload, fingerprint) for payload in catalogs
    )
    checks.append(
        _check(
            "old_catalogs_match_current_registry",
            "lock",
            catalog_identity_match and current_catalog_match,
            "both old catalogs and the current BrowserGym registry have identical selection identities"
            if catalog_identity_match and current_catalog_match
            else "old catalog identity differs from the current BrowserGym registry",
            {"catalogs": catalog_receipts, "current_fingerprint": _fingerprint_identity(fingerprint)},
        )
    )

    selected_payloads = [_load_json_mapping(path) for path in selected_sources_paths]
    selection_audit = _audit_old_selection_windows(selected_payloads, fingerprint)
    checks.append(
        _check(
            "old_selection_windows_are_first50_second50",
            "lock",
            selection_audit["ok"],
            "old selected sources are disjoint ranks 0-49 and 50-99"
            if selection_audit["ok"]
            else "old selected sources are not the exact first50/second50 selection windows",
            selection_audit,
        )
    )

    source_audit = _audit_official_files(
        selected_payloads,
        install_dir=runtime.install_dir,
        package_root=Path(str(probe.get("package_root") or "")),
    )
    checks.append(
        _check(
            "old_selected_official_files_match_current_runtime",
            "lock",
            source_audit["ok"],
            "every old selected official file maps to and matches the locked runtime"
            if source_audit["ok"]
            else "one or more old selected official files are unmapped, missing, conflicting, or changed",
            source_audit,
        )
    )

    core_audit = _audit_browsergym_core_files(probe, source_audit)
    checks.append(
        _check(
            "browsergym_miniwob_core_hashes_match_old100",
            "lock",
            core_audit["ok"],
            "BrowserGym MiniWoB __init__.py, all.py, and base.py match old selected-100 sources"
            if core_audit["ok"]
            else "BrowserGym MiniWoB core source hashes differ from old selected-100 sources",
            core_audit,
        )
    )

    html_inventory = _html_inventory(runtime.install_dir, runtime.html_root)
    html_ok = html_inventory["file_count"] > 0
    checks.append(
        _check(
            "html_assets_inventory_locked",
            "lock",
            html_ok,
            "MiniWoB HTML assets were inventoried and hashed"
            if html_ok
            else "MiniWoB HTML asset inventory is empty",
            {
                "root": html_inventory["root"],
                "file_count": html_inventory["file_count"],
                "inventory_sha256": html_inventory["inventory_sha256"],
            },
        )
    )

    agents = load_mapping(agents_config_path)
    agent_audit = _audit_agents(agents)
    checks.append(
        _check(
            "three_agents_exact",
            "lock",
            agent_audit["ok"],
            "Agent A/B/C exactly match the frozen provider, model, and execution settings"
            if agent_audit["ok"]
            else "the experimental agent roles differ from the required three-agent protocol",
            agent_audit,
        )
    )

    current_code = _code_inventory(DEFAULT_CODE_COMPONENTS)
    release_component_check = _audit_release_component_hashes(
        current_code,
        expected_release_component_hashes or {},
    )
    checks.append(
        _compatibility_check(
            "adapter_worker_runtime_release_baseline",
            release_component_check,
            pass_message="adapter, worker, runtime, and job planner match the supplied old-release hashes",
            fail_message="adapter/runtime code differs from the supplied old-release hashes",
            unproven_message="old-release hashes were not supplied for every adapter/runtime component",
        )
    )

    run_audit = _audit_old_runs(
        old_runs_root,
        selected_payloads=selected_payloads,
        agents_config_sha256=sha256_file(resolve_repo_path(agents_config_path)),
        expected_agent_roles=EXPECTED_AGENT_ROLES,
        base_seed=base_seed,
        fingerprint=fingerprint,
    )
    checks.append(
        _check(
            "old300_run_seed_agent_protocol",
            "direct_merge",
            run_audit["ok"],
            "old 100 cases contain exactly three agents with cohort-local seeds base+position"
            if run_audit["ok"]
            else "old 300 runs do not exactly match the frozen case/agent/seed/config protocol",
            run_audit,
        )
    )

    old_runtime_audit = _audit_old_runtime_claims(old_runs_root, probe)
    checks.append(
        _check(
            "old100_browsergym_version_and_action_space",
            "direct_merge",
            old_runtime_audit["ok"],
            "old artifacts' BrowserGym version and action-space hash match the current runtime"
            if old_runtime_audit["ok"]
            else "old artifacts' BrowserGym version or action space differs from the current runtime",
            old_runtime_audit,
        )
    )

    source_benchmark_hash = sha256_object(runtime.benchmark_config)
    execution_benchmark_hash = sha256_object(execution.benchmark_config)
    old_benchmark_hashes = sorted(run_audit.get("benchmark_config_hashes") or [])
    infra_compatible = old_benchmark_hashes == [execution_benchmark_hash]
    checks.append(
        _check(
            "old100_benchmark_config_hash",
            "direct_merge",
            infra_compatible,
            "current MiniWoB benchmark config hash matches all old runs"
            if infra_compatible
            else "current MiniWoB benchmark config hash does not match the old-run hash",
            {
                "execution_benchmark_config_hash": execution_benchmark_hash,
                "old_benchmark_config_hashes": old_benchmark_hashes,
            },
        )
    )

    chromium_baseline = _audit_optional_baseline(
        actual={
            "sha256": str(probe.get("chromium", {}).get("executable_sha256") or ""),
            "version": str(probe.get("chromium", {}).get("browser_version") or ""),
        },
        expected={
            "sha256": expected_release_chromium_sha256,
            "version": expected_release_chromium_version,
        },
    )
    checks.append(
        _compatibility_check(
            "old100_chromium_release_baseline",
            chromium_baseline,
            pass_message="Chromium executable and version match the supplied old-release baseline",
            fail_message="Chromium differs from the supplied old-release baseline",
            unproven_message="the old Chromium executable hash/version baseline was not supplied",
        )
    )

    html_baseline = _audit_optional_baseline(
        actual={"sha256": html_inventory["inventory_sha256"]},
        expected={"sha256": expected_release_html_inventory_sha256},
    )
    checks.append(
        _compatibility_check(
            "old100_full_html_inventory_baseline",
            html_baseline,
            pass_message="full HTML inventory matches the supplied old-release baseline",
            fail_message="full HTML inventory differs from the supplied old-release baseline",
            unproven_message="the old full HTML inventory hash was not supplied",
        )
    )

    scorer = _current_scorer(
        prompt_path=score_prompt_path,
        schema_path=score_schema_path,
        script_path=score_script_path,
    )
    checks.append(
        _check(
            "current_scorer_protocol_locked",
            "lock",
            all(
                re.fullmatch(r"[0-9a-f]{64}", str((scorer.get(field) or {}).get("sha256") or ""))
                for field in ("prompt", "schema", "script")
            ),
            "current gpt-5.4/high/fast scorer prompt, schema, and script are hashed",
            scorer,
        )
    )
    score_audit = _audit_old_scores(old_scores_root, selected_payloads, scorer)
    checks.append(
        _check(
            "old300_scorer_protocol",
            "direct_merge",
            score_audit["ok"],
            "old 300 score manifests all match gpt-5.4/high/fast and current prompt/schema hashes"
            if score_audit["ok"]
            else "old score manifests do not use one identical current scorer protocol",
            score_audit,
        )
    )

    lock_gate_passed = all(check.status == "passed" for check in checks if check.scope == "lock")
    direct_merge_eligible = lock_gate_passed and all(
        check.status == "passed" for check in checks if check.scope == "direct_merge"
    )
    reasons = [
        f"{check.scope}:{check.check_id}: {check.message}"
        for check in checks
        if check.status != "passed"
    ]

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "locked" if lock_gate_passed else "rejected",
        "lock_gate_passed": lock_gate_passed,
        "compatibility": "compatible" if direct_merge_eligible else "not_proven_or_incompatible",
        "direct_merge_eligible": direct_merge_eligible,
        "reasons": reasons,
        "policy": {
            "benchmark_full_case_count": 122,
            "registry_case_count": 125,
            "excluded_smoke_case_units": list(EXPECTED_SMOKE_TASKS),
            "extension_window": {"selection_offset": 100, "selected_count": 22},
            "formal_execution_infra_required": True,
            "execution_result_namespace": execution.result_namespace,
            "seed_rule": {
                "base_seed": base_seed,
                "rule": "seed = base_seed + zero_based_position_within_each_cohort",
                "same_seed_for_all_three_agents": True,
                "cohorts": ["first50", "second50", "remaining22"],
            },
            "merge_rule": "old100 may be unioned only when direct_merge_eligible is true",
        },
        "inputs": {
            "infra_config": _file_receipt(infra_config_path),
            "runtime_source_infra": _file_receipt(infra_config_path),
            "execution_infra": _file_receipt(resolved_execution_infra_path),
            "execution_infra_explicit": execution_infra_explicit,
            "agents_config": _file_receipt(agents_config_path),
            "catalogs": [_file_receipt(path) for path in catalog_paths],
            "selected_sources": [_file_receipt(path) for path in selected_sources_paths],
            "old_runs_root": _display_path(old_runs_root),
            "old_scores_root": _display_path(old_scores_root),
        },
        "runtime": {
            "machine_id": runtime.machine_id,
            "python_bin": str(runtime.python_bin),
            "install_dir": str(runtime.install_dir),
            "html_root": str(runtime.html_root),
            "playwright_browsers_path": str(local_playwright_browsers_path),
            "benchmark_config_hash": source_benchmark_hash,
            "benchmark_config": runtime.benchmark_config,
            "source_benchmark_config_hash": source_benchmark_hash,
            "source_benchmark_config": runtime.benchmark_config,
            "execution_machine_id": execution.machine_id,
            "execution_result_namespace": execution.result_namespace,
            "execution_benchmark_config_hash": execution_benchmark_hash,
            "execution_benchmark_config": execution.benchmark_config,
            "probe": probe,
            "registry": fingerprint,
            "html_assets": html_inventory,
            "install_git_commit": _git_commit(runtime.install_dir),
        },
        "agents": agent_audit,
        "code_components": current_code,
        "scorer": scorer,
        "old100_audit": {
            "selection": selection_audit,
            "official_files": source_audit,
            "runs": run_audit,
            "runtime_claims": old_runtime_audit,
            "scores": score_audit,
        },
        "checks": [check.to_dict() for check in checks],
    }
    payload = _sanitize_local_paths(payload)
    payload["runtime_lock_sha256"] = sha256_object(payload)
    return payload


def write_miniwob_runtime_lock(path: str | Path, payload: Mapping[str, Any]) -> Path:
    return write_json(path, payload)


def _audit_old_selection_windows(
    selected_payloads: Sequence[Mapping[str, Any]],
    fingerprint: Mapping[str, Any],
) -> dict[str, Any]:
    expected_by_rank = {
        int(item["selection_rank"]): str(item["case_unit_id"])
        for item in list(fingerprint.get("selection_records") or [])
    }
    windows: list[dict[str, Any]] = []
    ids_by_window: list[list[str]] = []
    mismatch: list[dict[str, Any]] = []
    for window_index, payload in enumerate(selected_payloads):
        items = [dict(item) for item in list(payload.get("items") or []) if isinstance(item, Mapping)]
        ids = [str(item.get("case_unit_id") or "") for item in items]
        ids_by_window.append(ids)
        expected_start = window_index * 50
        expected_ids = [expected_by_rank.get(rank) for rank in range(expected_start, expected_start + 50)]
        if ids != expected_ids:
            mismatch.append(
                {
                    "window_index": window_index,
                    "expected_ids": expected_ids,
                    "actual_ids": ids,
                }
            )
        actual_ranks = [int(item.get("selection_rank", -1)) for item in items]
        expected_ranks = list(range(expected_start, expected_start + 50))
        if actual_ranks != expected_ranks:
            mismatch.append(
                {
                    "window_index": window_index,
                    "expected_ranks": expected_ranks,
                    "actual_ranks": actual_ranks,
                }
            )
        windows.append(
            {
                "window_index": window_index,
                "selected_count": len(items),
                "rank_start": min(actual_ranks) if actual_ranks else None,
                "rank_end": max(actual_ranks) if actual_ranks else None,
                "case_ids_sha256": sha256_object(ids),
            }
        )
    overlap = sorted(set(ids_by_window[0]) & set(ids_by_window[1]))
    union = set(ids_by_window[0]) | set(ids_by_window[1])
    return {
        "ok": not mismatch and not overlap and len(union) == 100,
        "windows": windows,
        "overlap": overlap,
        "union_count": len(union),
        "mismatches": mismatch,
    }


def _audit_official_files(
    selected_payloads: Sequence[Mapping[str, Any]],
    *,
    install_dir: Path,
    package_root: Path,
) -> dict[str, Any]:
    expected: dict[str, str] = {}
    conflicts: list[dict[str, str]] = []
    references: defaultdict[str, set[str]] = defaultdict(set)
    for payload in selected_payloads:
        for item in list(payload.get("items") or []):
            if not isinstance(item, Mapping):
                continue
            case_id = str(item.get("case_unit_id") or "")
            for source in list(item.get("official_files") or []):
                if not isinstance(source, Mapping):
                    continue
                archive = str(source.get("archive_path") or "")
                digest = str(source.get("sha256") or "")
                references[archive].add(case_id)
                if archive in expected and expected[archive] != digest:
                    conflicts.append(
                        {"archive_path": archive, "first_sha256": expected[archive], "second_sha256": digest}
                    )
                expected[archive] = digest
    rows: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    for archive, expected_digest in sorted(expected.items()):
        mapped = _map_archive_path(archive, install_dir=install_dir, package_root=package_root)
        actual_digest = sha256_file(mapped) if mapped is not None and mapped.is_file() else None
        row = {
            "archive_path": archive,
            "mapped_path": str(mapped) if mapped is not None else None,
            "expected_sha256": expected_digest,
            "actual_sha256": actual_digest,
            "case_reference_count": len(references[archive]),
        }
        rows.append(row)
        if actual_digest != expected_digest:
            mismatches.append(row)
    return {
        "ok": bool(expected) and not conflicts and not mismatches,
        "unique_official_file_count": len(expected),
        "matched_file_count": len(expected) - len(mismatches),
        "conflicts": conflicts,
        "mismatches": mismatches,
        "files": rows,
    }


def _map_archive_path(archive_path: str, *, install_dir: Path, package_root: Path) -> Path | None:
    install_prefix = "official/install/"
    python_prefix = "official/python/browsergym/miniwob/"
    if archive_path.startswith(install_prefix):
        relative = Path(archive_path[len(install_prefix) :])
        target = (install_dir / relative).resolve()
        return target if _is_relative_to(target, install_dir.resolve()) else None
    if archive_path.startswith(python_prefix) and package_root.is_dir():
        relative = Path(archive_path[len(python_prefix) :])
        target = (package_root / relative).resolve()
        return target if _is_relative_to(target, package_root.resolve()) else None
    return None


def _audit_browsergym_core_files(
    probe: Mapping[str, Any],
    source_audit: Mapping[str, Any],
) -> dict[str, Any]:
    expected = {
        str(row.get("archive_path")): str(row.get("expected_sha256"))
        for row in list(source_audit.get("files") or [])
        if str(row.get("archive_path") or "").startswith("official/python/browsergym/miniwob/")
    }
    module_files = dict(probe.get("module_files") or {})
    rows: list[dict[str, Any]] = []
    for filename in ("__init__.py", "all.py", "base.py"):
        archive = f"official/python/browsergym/miniwob/{filename}"
        probed = dict(module_files.get(filename) or {})
        rows.append(
            {
                "filename": filename,
                "expected_sha256": expected.get(archive),
                "actual_sha256": probed.get("sha256"),
                "path": probed.get("path"),
                "matches": bool(expected.get(archive)) and expected.get(archive) == probed.get("sha256"),
            }
        )
    return {"ok": all(row["matches"] for row in rows), "files": rows}


def _audit_agents(agents_config: Mapping[str, Any]) -> dict[str, Any]:
    roles = dict(agents_config.get("experimental_agents") or {})
    errors: list[str] = []
    if set(roles) != set(EXPECTED_AGENT_ROLES):
        errors.append(f"experimental agent IDs are {sorted(roles)}, expected {sorted(EXPECTED_AGENT_ROLES)}")
    receipts: dict[str, Any] = {}
    for agent_id, expected_identity in EXPECTED_AGENT_ROLES.items():
        role = dict(roles.get(agent_id) or {})
        for field, expected in {**expected_identity, **EXPECTED_AGENT_SHARED}.items():
            if role.get(field) != expected:
                errors.append(f"{agent_id}.{field}={role.get(field)!r}, expected {expected!r}")
        receipts[agent_id] = {
            "provider": role.get("provider"),
            "model": role.get("model"),
            "model_version": role.get("model_version"),
            **{field: role.get(field) for field in EXPECTED_AGENT_SHARED},
            "api_key_env": role.get("api_key_env"),
            "role_config_sha256": sha256_object(role),
        }
    return {"ok": not errors, "roles": receipts, "errors": errors}


def _audit_formal_execution_infra(execution: MiniWoBExecutionInfra) -> dict[str, Any]:
    infra = execution.infra_config
    machine = execution.machine_config
    paths = dict(infra.get("paths") or {})
    errors: list[str] = []
    if infra.get("dry_run") is not False:
        errors.append("dry_run must be exactly false")
    namespace = execution.result_namespace
    if not namespace:
        errors.append("all execution result/log roots must declare one results/namespaces/<namespace> namespace")
    namespace_paths = {
        "paths.results_root": paths.get("results_root"),
        "paths.dry_run_results_root": paths.get("dry_run_results_root"),
        "paths.full_results_root": paths.get("full_results_root"),
        "paths.logs_dir": paths.get("logs_dir"),
        "machine.results_dir": machine.get("results_dir"),
        "machine.logs_dir": machine.get("logs_dir"),
    }
    if namespace:
        for field, value in namespace_paths.items():
            if _namespace_from_path(value) != namespace:
                errors.append(f"{field} is not inside results/namespaces/{namespace}")
    for field in (
        "runner_command",
        "python_bin",
        "install_dir",
        "assets_path",
        "base_url",
        "http_server_dir",
        "playwright_browsers_path",
        "adapter_module",
        "worker_module",
        "driver",
        "native_evaluator",
    ):
        value = str(execution.benchmark_config.get(field) or "").strip()
        if not value:
            errors.append(f"execution benchmark {field} is empty")
        elif re.search(r"<[^>]+>", value):
            errors.append(f"execution benchmark {field} contains a placeholder")
    return {
        "ok": not errors,
        "execution_infra_explicit": True,
        "dry_run": infra.get("dry_run"),
        "result_namespace": namespace,
        "namespace_paths": namespace_paths,
        "errors": errors,
    }


def _audit_source_execution_protocol(
    *,
    runtime: MiniWoBLocalRuntime,
    execution: MiniWoBExecutionInfra,
    probe: Mapping[str, Any],
    cli_base_seed: int,
) -> dict[str, Any]:
    protocol_fields = (
        "base_url",
        "http_server_port",
        "full_max_steps",
        "headless",
        "record_video",
        "timeout_seconds",
        "retry",
        "base_seed",
        "adapter_module",
        "worker_module",
        "driver",
        "action_set",
        "native_evaluator",
    )
    source_protocol = {field: runtime.benchmark_config.get(field) for field in protocol_fields}
    execution_protocol = {field: execution.benchmark_config.get(field) for field in protocol_fields}
    protocol_mismatches = [
        {"field": field, "source": source_protocol[field], "execution": execution_protocol[field]}
        for field in protocol_fields
        if source_protocol[field] != execution_protocol[field]
    ]
    expected_protocol = {**EXPECTED_EXECUTION_PROTOCOL, "base_seed": cli_base_seed}
    expected_protocol_mismatches = [
        {"side": side, "field": field, "expected": expected, "actual": protocol.get(field)}
        for side, protocol in (("source", source_protocol), ("execution", execution_protocol))
        for field, expected in expected_protocol.items()
        if protocol.get(field) != expected
    ]
    probed_action_set = dict(probe.get("action_set") or {})
    if probed_action_set != EXPECTED_EXECUTION_PROTOCOL["action_set"]:
        expected_protocol_mismatches.append(
            {
                "side": "actual_source_runtime",
                "field": "action_set",
                "expected": EXPECTED_EXECUTION_PROTOCOL["action_set"],
                "actual": probed_action_set,
            }
        )
    source_browser_path = str(runtime.benchmark_config.get("playwright_browsers_path") or "").strip()
    execution_browser_path = str(execution.benchmark_config.get("playwright_browsers_path") or "").strip()
    source_browser_path_identity = _runtime_path_identity(source_browser_path)
    execution_browser_path_identity = _runtime_path_identity(execution_browser_path)
    expected_local_browser_path = str(_absolute_path(source_browser_path).resolve()) if source_browser_path else None
    probed_browser_path = str(probe.get("playwright_browsers_path") or "").strip() or None
    if (
        not source_browser_path_identity
        or not execution_browser_path_identity
        or source_browser_path_identity != execution_browser_path_identity
    ):
        protocol_mismatches.append(
            {
                "field": "playwright_browsers_path",
                "source": source_browser_path,
                "source_identity": source_browser_path_identity,
                "execution": execution_browser_path,
                "execution_identity": execution_browser_path_identity,
            }
        )
    if probed_browser_path != expected_local_browser_path:
        protocol_mismatches.append(
            {
                "field": "PLAYWRIGHT_BROWSERS_PATH",
                "expected_probe_path": expected_local_browser_path,
                "actual_probe_path": probed_browser_path,
            }
        )

    source_declared_pins = _declared_runtime_pins(runtime.benchmark_config, runtime.machine_config)
    execution_declared_pins = _declared_runtime_pins(execution.benchmark_config, execution.machine_config)
    actual_pins = _actual_runtime_pins(runtime, probe)
    pin_fields = (
        "browsergym_version",
        "miniwob_git_commit",
        "playwright_version",
        "chromium_revision",
        "chromium_version",
    )
    missing_pins = [
        {"source": source, "field": field}
        for source, pins in (
            ("actual_source_runtime", actual_pins),
            ("source_infra", source_declared_pins),
            ("execution_infra", execution_declared_pins),
        )
        for field in pin_fields
        if not pins.get(field)
    ]
    pin_mismatches: list[dict[str, Any]] = []
    for field in pin_fields:
        actual = actual_pins.get(field)
        source_declared = source_declared_pins.get(field)
        execution_declared = execution_declared_pins.get(field)
        if actual and source_declared and actual != source_declared:
            pin_mismatches.append(
                {"field": field, "left": "actual_source_runtime", "left_value": actual, "right": "source_infra", "right_value": source_declared}
            )
        if actual and execution_declared and actual != execution_declared:
            pin_mismatches.append(
                {"field": field, "left": "actual_source_runtime", "left_value": actual, "right": "execution_infra", "right_value": execution_declared}
            )
    return {
        "ok": (
            not protocol_mismatches
            and not expected_protocol_mismatches
            and not missing_pins
            and not pin_mismatches
        ),
        "cli_base_seed": cli_base_seed,
        "expected_protocol": expected_protocol,
        "source_protocol": source_protocol,
        "execution_protocol": execution_protocol,
        "playwright_browsers_path": {
            "source": source_browser_path,
            "source_identity": source_browser_path_identity,
            "execution": execution_browser_path,
            "execution_identity": execution_browser_path_identity,
            "expected_local_probe_path": expected_local_browser_path,
            "actual_probe_path": probed_browser_path,
        },
        "protocol_mismatches": protocol_mismatches,
        "expected_protocol_mismatches": expected_protocol_mismatches,
        "actual_source_runtime_pins": actual_pins,
        "source_infra_declared_pins": source_declared_pins,
        "execution_infra_declared_pins": execution_declared_pins,
        "missing_pins": missing_pins,
        "pin_mismatches": pin_mismatches,
    }


def _declared_runtime_pins(
    benchmark: Mapping[str, Any],
    machine: Mapping[str, Any],
) -> dict[str, str | None]:
    assets = dict(machine.get("benchmark_assets") or {})
    return {
        "browsergym_version": _distribution_pin_version(
            benchmark.get("browsergym_version") or assets.get("browsergym_distribution")
        ),
        "miniwob_git_commit": _optional_text(
            benchmark.get("miniwob_git_commit") or assets.get("miniwob_git_commit")
        ),
        "playwright_version": _distribution_pin_version(
            benchmark.get("playwright_version") or assets.get("playwright_distribution")
        ),
        "chromium_revision": _optional_text(
            benchmark.get("chromium_revision") or assets.get("chromium_revision")
        ),
        "chromium_version": _optional_text(
            benchmark.get("chromium_version") or assets.get("chromium_version")
        ),
    }


def _actual_runtime_pins(
    runtime: MiniWoBLocalRuntime,
    probe: Mapping[str, Any],
) -> dict[str, str | None]:
    distributions = dict(probe.get("distributions") or {})
    chromium = dict(probe.get("chromium") or {})
    chromium_rows = [
        row for row in list(chromium.get("browsers_json_chromium") or []) if isinstance(row, Mapping)
    ]
    preferred = next((row for row in chromium_rows if row.get("name") == "chromium"), None)
    chromium_row = preferred or (chromium_rows[0] if chromium_rows else {})
    return {
        "browsergym_version": _optional_text(distributions.get("browsergym-miniwob")),
        "miniwob_git_commit": _git_commit(runtime.install_dir),
        "playwright_version": _optional_text(distributions.get("playwright")),
        "chromium_revision": _optional_text(chromium_row.get("revision")),
        "chromium_version": _optional_text(chromium.get("browser_version")),
    }


def _audit_execution_settings(runtime: MiniWoBLocalRuntime) -> dict[str, Any]:
    config = runtime.benchmark_config
    raw_server_dir = str(config.get("http_server_dir") or "").strip()
    server_dir = _absolute_path(raw_server_dir).resolve() if raw_server_dir else None
    settings = {
        "runner_command": str(config.get("runner_command") or "").strip(),
        "python_bin": str(config.get("python_bin") or "").strip(),
        "install_dir": str(config.get("install_dir") or "").strip(),
        "assets_path": str(config.get("assets_path") or "").strip(),
        "base_url": str(config.get("base_url") or "").strip(),
        "http_server_dir": raw_server_dir,
        "playwright_browsers_path": str(config.get("playwright_browsers_path") or "").strip(),
        "http_server_port": config.get("http_server_port"),
        "full_max_steps": config.get("full_max_steps"),
        "base_seed": config.get("base_seed"),
        **{field: config.get(field) for field in EXPECTED_EXECUTION_PROTOCOL},
    }
    errors: list[str] = []
    for field in (
        "runner_command",
        "python_bin",
        "install_dir",
        "assets_path",
        "base_url",
        "http_server_dir",
        "playwright_browsers_path",
    ):
        value = str(settings.get(field) or "")
        if not value:
            errors.append(f"{field} is empty")
        elif re.search(r"<[^>]+>", value):
            errors.append(f"{field} contains a placeholder")
    if not settings["base_url"].startswith(("http://", "https://")):
        errors.append("base_url is not HTTP(S)")
    if settings["full_max_steps"] != 30:
        errors.append(f"full_max_steps={settings['full_max_steps']!r}, expected 30")
    if settings["base_seed"] != 7:
        errors.append(f"base_seed={settings['base_seed']!r}, expected 7")
    for field, expected in EXPECTED_EXECUTION_PROTOCOL.items():
        if settings.get(field) != expected:
            errors.append(f"{field}={settings.get(field)!r}, expected {expected!r}")
    try:
        port = int(settings["http_server_port"])
    except (TypeError, ValueError):
        port = 0
    if not 1 <= port <= 65535:
        errors.append("http_server_port is invalid")
    if server_dir is None or not server_dir.is_dir():
        errors.append(f"http_server_dir is missing: {server_dir}")
    raw_browsers_path = str(settings["playwright_browsers_path"] or "")
    browsers_path = _absolute_path(raw_browsers_path).resolve() if raw_browsers_path else None
    if browsers_path is None or not browsers_path.is_dir():
        errors.append(f"playwright_browsers_path is missing: {browsers_path}")
    return {
        "ok": not errors,
        "settings": settings,
        "resolved_http_server_dir": str(server_dir) if server_dir else None,
        "resolved_playwright_browsers_path": str(browsers_path) if browsers_path else None,
        "errors": errors,
    }


def _audit_old_runs(
    root: str | Path,
    *,
    selected_payloads: Sequence[Mapping[str, Any]],
    agents_config_sha256: str,
    expected_agent_roles: Mapping[str, Mapping[str, Any]],
    base_seed: int,
    fingerprint: Mapping[str, Any],
) -> dict[str, Any]:
    root_path = resolve_repo_path(root)
    job_paths = sorted(root_path.glob("*/adapter/native_run/job.json")) if root_path.is_dir() else []
    expected_seed: dict[str, int] = {}
    for payload in selected_payloads:
        items = [item for item in list(payload.get("items") or []) if isinstance(item, Mapping)]
        for position, item in enumerate(items):
            expected_seed[str(item.get("case_unit_id") or "")] = base_seed + position
    expected_slots = {(case_id, agent_id) for case_id in expected_seed for agent_id in expected_agent_roles}
    actual_slots: Counter[tuple[str, str]] = Counter()
    errors: list[dict[str, Any]] = []
    benchmark_hashes: set[str] = set()
    action_description_hashes: set[str] = set()
    for path in job_paths:
        job = _load_json_mapping(path)
        case_id = str(job.get("case_unit_id") or "")
        agent_id = str(job.get("agent_id") or "")
        actual_slots[(case_id, agent_id)] += 1
        benchmark_hashes.add(str(job.get("benchmark_config_hash") or ""))
        expected = expected_seed.get(case_id)
        if expected is None or agent_id not in expected_agent_roles:
            errors.append({"path": _display_path(path), "error": "off-list case or agent"})
        if job.get("seed") != expected:
            errors.append(
                {"path": _display_path(path), "error": "seed mismatch", "expected": expected, "actual": job.get("seed")}
            )
        if job.get("agent_config_hash") != agents_config_sha256:
            errors.append({"path": _display_path(path), "error": "agents config hash mismatch"})
        selection = dict(job.get("deterministic_selection") or {})
        for field in ("eligible_case_unit_set_hash", "case_selection_order_hash", "smoke_exclusion_hash"):
            if selection.get(field) != fingerprint.get(field):
                errors.append({"path": _display_path(path), "error": f"{field} mismatch"})
        worker_path = path.with_name("worker_config.json")
        if not worker_path.is_file():
            errors.append({"path": _display_path(worker_path), "error": "worker config missing"})
            continue
        worker = _load_json_mapping(worker_path)
        expected_model = expected_agent_roles.get(agent_id, {}).get("model")
        expected_worker = {
            "driver": "openrouter_chat",
            "model": expected_model,
            "temperature": 0.0,
            "max_tokens": 4096,
            "timeout_seconds": 120,
            "retry": 2,
            "max_steps": 30,
            "headless": True,
            "record_video": True,
        }
        for field, value in expected_worker.items():
            if worker.get(field) != value:
                errors.append(
                    {"path": _display_path(worker_path), "error": f"{field} mismatch", "expected": value, "actual": worker.get(field)}
                )
        context_path = path.with_name("task_context.json")
        if context_path.is_file():
            context = _load_json_mapping(context_path)
            description = str(context.get("action_space_description") or "")
            if description:
                action_description_hashes.add(hashlib.sha256(description.encode("utf-8")).hexdigest())
    duplicate_slots = [list(slot) + [count] for slot, count in sorted(actual_slots.items()) if count != 1]
    missing_slots = [list(slot) for slot in sorted(expected_slots - set(actual_slots))]
    off_list_slots = [list(slot) for slot in sorted(set(actual_slots) - expected_slots)]
    ok = (
        len(job_paths) == 300
        and len(expected_seed) == 100
        and not errors
        and not duplicate_slots
        and not missing_slots
        and not off_list_slots
    )
    return {
        "ok": ok,
        "job_count": len(job_paths),
        "case_count": len({slot[0] for slot in actual_slots}),
        "slot_count": len(actual_slots),
        "expected_slot_count": len(expected_slots),
        "seed_rule": "base_seed + zero_based_position_within_each_50-case_cohort",
        "base_seed": base_seed,
        "three_agents_same_case_seed": True,
        "benchmark_config_hashes": sorted(value for value in benchmark_hashes if value),
        "action_space_description_hashes": sorted(action_description_hashes),
        "missing_slots": missing_slots,
        "off_list_slots": off_list_slots,
        "duplicate_slots": duplicate_slots,
        "errors": errors,
    }


def _audit_old_runtime_claims(root: str | Path, probe: Mapping[str, Any]) -> dict[str, Any]:
    root_path = resolve_repo_path(root)
    manifests = sorted(root_path.glob("*/adapter/artifact_manifest.json")) if root_path.is_dir() else []
    versions: set[str] = set()
    for path in manifests:
        payload = _load_json_mapping(path)
        for artifact in list(payload.get("artifacts") or []):
            if not isinstance(artifact, Mapping):
                continue
            if artifact.get("producer_name") == "browsergym-miniwob":
                versions.add(str(artifact.get("producer_version") or ""))
    contexts = sorted(root_path.glob("*/adapter/native_run/task_context.json")) if root_path.is_dir() else []
    action_hashes = {
        hashlib.sha256(str(_load_json_mapping(path).get("action_space_description") or "").encode("utf-8")).hexdigest()
        for path in contexts
    }
    current_version = str((probe.get("distributions") or {}).get("browsergym-miniwob") or "")
    current_action_hash = str(probe.get("action_space_description_sha256") or "")
    version_ok = bool(current_version) and versions == {current_version}
    action_ok = bool(current_action_hash) and action_hashes == {current_action_hash}
    return {
        "ok": len(manifests) == 300 and len(contexts) == 300 and version_ok and action_ok,
        "artifact_manifest_count": len(manifests),
        "task_context_count": len(contexts),
        "old_declared_browsergym_miniwob_versions": sorted(versions),
        "current_browsergym_miniwob_version": current_version,
        "version_matches": version_ok,
        "old_action_space_description_sha256": sorted(action_hashes),
        "current_action_space_description_sha256": current_action_hash,
        "action_space_matches": action_ok,
    }


def _current_scorer(*, prompt_path: str | Path, schema_path: str | Path, script_path: str | Path) -> dict[str, Any]:
    for label, path in (("prompt", prompt_path), ("schema", schema_path), ("script", script_path)):
        if not resolve_repo_path(path).is_file():
            raise MiniWoBRuntimeLockError(f"current score {label} is missing: {resolve_repo_path(path)}")
    return {
        "model": "gpt-5.4",
        "reasoning_effort": "high",
        "service_tier": "fast",
        "prompt": _file_receipt(prompt_path),
        "schema": _file_receipt(schema_path),
        "script": _file_receipt(script_path),
    }


def _audit_old_scores(
    root: str | Path,
    selected_payloads: Sequence[Mapping[str, Any]],
    scorer: Mapping[str, Any],
) -> dict[str, Any]:
    root_path = resolve_repo_path(root)
    paths = sorted(root_path.glob("*/*/*/score_manifest.json")) if root_path.is_dir() else []
    cases = {
        str(item.get("case_unit_id") or "")
        for payload in selected_payloads
        for item in list(payload.get("items") or [])
        if isinstance(item, Mapping)
    }
    expected_slots = {(case_id, agent_id) for case_id in cases for agent_id in EXPECTED_AGENT_ROLES}
    slots: Counter[tuple[str, str]] = Counter()
    variants: Counter[tuple[str, str, str, str, str]] = Counter()
    prompt_sha = str((scorer.get("prompt") or {}).get("sha256") or "")
    schema_sha = str((scorer.get("schema") or {}).get("sha256") or "")
    errors: list[dict[str, Any]] = []
    for path in paths:
        manifest = _load_json_mapping(path)
        slot = (str(manifest.get("case_unit_id") or ""), str(manifest.get("agent_id") or ""))
        slots[slot] += 1
        variant = (
            str(manifest.get("model") or ""),
            str(manifest.get("reasoning_effort") or ""),
            str(manifest.get("service_tier") or ""),
            str(manifest.get("score_prompt_sha256") or ""),
            str(manifest.get("score_schema_sha256") or ""),
        )
        variants[variant] += 1
        expected = ("gpt-5.4", "high", "fast", prompt_sha, schema_sha)
        if variant != expected:
            errors.append(
                {
                    "path": _display_path(path),
                    "actual": {
                        "model": variant[0],
                        "reasoning_effort": variant[1],
                        "service_tier": variant[2],
                        "score_prompt_sha256": variant[3],
                        "score_schema_sha256": variant[4],
                    },
                }
            )
    missing = [list(slot) for slot in sorted(expected_slots - set(slots))]
    off_list = [list(slot) for slot in sorted(set(slots) - expected_slots)]
    duplicates = [list(slot) + [count] for slot, count in sorted(slots.items()) if count != 1]
    variant_rows = [
        {
            "model": variant[0],
            "reasoning_effort": variant[1],
            "service_tier": variant[2],
            "score_prompt_sha256": variant[3],
            "score_schema_sha256": variant[4],
            "count": count,
        }
        for variant, count in sorted(variants.items())
    ]
    ok = len(paths) == 300 and not missing and not off_list and not duplicates and not errors
    return {
        "ok": ok,
        "score_manifest_count": len(paths),
        "slot_count": len(slots),
        "expected_slot_count": len(expected_slots),
        "variants": variant_rows,
        "missing_slots": missing,
        "off_list_slots": off_list,
        "duplicate_slots": duplicates,
        "protocol_mismatch_count": len(errors),
        "protocol_mismatches": errors,
    }


def _html_inventory(install_dir: Path, configured_html_root: Path) -> dict[str, Any]:
    conventional = install_dir / "miniwob" / "html"
    if conventional.is_dir():
        root = conventional.resolve()
    elif configured_html_root.name == "miniwob" and configured_html_root.parent.is_dir():
        root = configured_html_root.parent.resolve()
    else:
        root = configured_html_root.resolve()
    files = [path for path in sorted(root.rglob("*")) if path.is_file()]
    entries = [
        {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
        for path in files
    ]
    return {
        "root": str(root),
        "file_count": len(entries),
        "inventory_sha256": sha256_object(entries),
        "files": entries,
    }


def _code_inventory(paths: Iterable[str | Path]) -> dict[str, Any]:
    receipts: dict[str, Any] = {}
    for path in paths:
        resolved = resolve_repo_path(path)
        if not resolved.is_file():
            raise MiniWoBRuntimeLockError(f"runtime code component is missing: {resolved}")
        receipts[_display_path(path)] = {"path": _display_path(path), "sha256": sha256_file(resolved)}
    return receipts


def _audit_release_component_hashes(
    current: Mapping[str, Any],
    expected: Mapping[str, str],
) -> dict[str, Any]:
    normalized_expected = {_display_path(path): str(digest) for path, digest in expected.items()}
    missing = sorted(set(current) - set(normalized_expected))
    mismatches = [
        {
            "path": path,
            "expected_sha256": normalized_expected.get(path),
            "actual_sha256": receipt.get("sha256"),
        }
        for path, receipt in current.items()
        if path in normalized_expected and normalized_expected[path] != receipt.get("sha256")
    ]
    status = "unproven" if missing else ("failed" if mismatches else "passed")
    return {"status": status, "missing_baselines": missing, "mismatches": mismatches}


def _audit_optional_baseline(*, actual: Mapping[str, str], expected: Mapping[str, str | None]) -> dict[str, Any]:
    missing = sorted(key for key, value in expected.items() if not value)
    mismatches = [
        {"field": key, "expected": expected.get(key), "actual": actual.get(key)}
        for key in expected
        if expected.get(key) and expected.get(key) != actual.get(key)
    ]
    status = "unproven" if missing else ("failed" if mismatches else "passed")
    return {"status": status, "actual": dict(actual), "expected": dict(expected), "missing_baselines": missing, "mismatches": mismatches}


def _compatibility_check(
    check_id: str,
    audit: Mapping[str, Any],
    *,
    pass_message: str,
    fail_message: str,
    unproven_message: str,
) -> RuntimeCheck:
    status = str(audit.get("status") or "failed")
    message = pass_message if status == "passed" else (unproven_message if status == "unproven" else fail_message)
    return RuntimeCheck(check_id, "direct_merge", status, message, dict(audit))


def _check(
    check_id: str,
    scope: str,
    condition: bool,
    message: str,
    evidence: Mapping[str, Any],
) -> RuntimeCheck:
    return RuntimeCheck(check_id, scope, "passed" if condition else "failed", message, dict(evidence))


def _catalog_identity(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: payload.get(key)
        for key in (
            "catalog_count",
            "candidate_count",
            "excluded_smoke_case_units",
            "smoke_exclusion_hash",
            "selection_salt_hash",
            "eligible_case_unit_set_hash",
            "case_selection_order_hash",
        )
    }


def _fingerprint_identity(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: payload.get(key)
        for key in (
            "catalog_count",
            "candidate_count",
            "excluded_smoke_case_units",
            "smoke_exclusion_hash",
            "selection_salt_hash",
            "eligible_case_unit_set_hash",
            "case_selection_order_hash",
        )
    }


def _catalog_matches_fingerprint(catalog: Mapping[str, Any], fingerprint: Mapping[str, Any]) -> bool:
    identity = _catalog_identity(catalog)
    expected = _fingerprint_identity(fingerprint)
    if identity != expected:
        return False
    actual_records = sorted(
        (
            str(item.get("case_unit_id") or ""),
            str(item.get("task_id") or ""),
            str(item.get("selection_order_key") or ""),
            int(item.get("selection_rank", -1)),
        )
        for item in list(catalog.get("items") or [])
        if isinstance(item, Mapping)
    )
    expected_records = sorted(
        (
            str(item.get("case_unit_id") or ""),
            str(item.get("task_id") or ""),
            str(item.get("selection_order_key") or ""),
            int(item.get("selection_rank", -1)),
        )
        for item in list(fingerprint.get("selection_records") or [])
    )
    return actual_records == expected_records


def _load_json_mapping(path: str | Path) -> dict[str, Any]:
    resolved = resolve_repo_path(path)
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MiniWoBRuntimeLockError(f"cannot read JSON mapping {resolved}: {exc}") from exc
    if not isinstance(payload, dict):
        raise MiniWoBRuntimeLockError(f"expected JSON mapping: {resolved}")
    return dict(payload)


def _file_receipt(path: str | Path) -> dict[str, str]:
    resolved = resolve_repo_path(path)
    if not resolved.is_file():
        raise MiniWoBRuntimeLockError(f"lock input file is missing: {resolved}")
    return {"path": _display_path(path), "sha256": sha256_file(resolved)}


def _git_commit(path: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    value = completed.stdout.strip()
    return value if completed.returncode == 0 and re.fullmatch(r"[0-9a-fA-F]{40}", value) else None


def _miniwob_benchmark_config(machine: Mapping[str, Any]) -> dict[str, Any]:
    for benchmark_name, benchmark_config in dict(machine.get("benchmarks") or {}).items():
        if normalize_domain_or_none(benchmark_name) == "miniwob":
            return dict(benchmark_config or {})
    return {}


def _local_playwright_browsers_path(runtime: MiniWoBLocalRuntime) -> Path:
    raw = str(runtime.benchmark_config.get("playwright_browsers_path") or "").strip()
    if not raw:
        raise MiniWoBRuntimeLockError("locked source/runtime infra is missing playwright_browsers_path")
    if re.search(r"<[^>]+>", raw):
        raise MiniWoBRuntimeLockError("locked source/runtime playwright_browsers_path contains a placeholder")
    path = _absolute_path(raw).resolve()
    if not path.is_dir():
        raise MiniWoBRuntimeLockError(f"locked Playwright browsers directory is missing: {path}")
    return path


def _result_namespace_from_infra(infra: Mapping[str, Any]) -> str | None:
    paths = dict(infra.get("paths") or {})
    candidates = {
        namespace
        for value in paths.values()
        if (namespace := _namespace_from_path(value)) is not None
    }
    for machine in list(infra.get("machines") or []):
        if not isinstance(machine, Mapping) or machine.get("enabled") is False:
            continue
        for field in ("results_dir", "logs_dir"):
            namespace = _namespace_from_path(machine.get(field))
            if namespace:
                candidates.add(namespace)
    return next(iter(candidates)) if len(candidates) == 1 else None


def _namespace_from_path(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    parts = Path(text).parts
    for index in range(len(parts) - 2):
        if parts[index] == "results" and parts[index + 1] == "namespaces":
            namespace = parts[index + 2]
            if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", namespace):
                return namespace
    return None


def _runtime_path_identity(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text or re.search(r"<[^>]+>", text):
        return None
    parts = Path(text).parts
    for index, part in enumerate(parts):
        if part == "tmp" and index + 1 < len(parts):
            return Path(*parts[index:]).as_posix()
    return Path(text).as_posix()


def _distribution_pin_version(value: Any) -> str | None:
    text = _optional_text(value)
    if text is None:
        return None
    return text.rsplit("==", 1)[1] if "==" in text else text


def _optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _sanitize_local_paths(value: Any) -> Any:
    """Remove workstation-specific absolute prefixes from persisted receipts."""

    if isinstance(value, dict):
        return {key: _sanitize_local_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_local_paths(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_local_paths(item) for item in value]
    if not isinstance(value, str):
        return value
    repo_prefix = str(resolve_repo_path(".").resolve())
    home_prefix = str(Path.home().resolve())
    sanitized = value.replace(repo_prefix, "<REPO_ROOT>")
    if home_prefix and home_prefix != repo_prefix:
        sanitized = sanitized.replace(home_prefix, "<LOCAL_HOME>")
    return sanitized


def _absolute_path(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    return candidate.absolute() if candidate.is_absolute() else resolve_repo_path(candidate).absolute()


def _display_path(path: str | Path) -> str:
    resolved = resolve_repo_path(path)
    try:
        return resolved.relative_to(resolve_repo_path(".")).as_posix()
    except ValueError:
        return str(resolved)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


_RUNTIME_PROBE_SOURCE = r'''
import hashlib
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys

import browsergym.miniwob as miniwob
import browsergym.miniwob.all as miniwob_all
import browsergym.miniwob.base as miniwob_base
from browsergym.core.action.highlevel import HighLevelActionSet


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def distribution_version(name):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


module_file = Path(inspect.getfile(miniwob)).resolve()
package_root = module_file.parent
module_files = {}
for filename, module in (("__init__.py", miniwob), ("all.py", miniwob_all), ("base.py", miniwob_base)):
    path = Path(inspect.getfile(module)).resolve()
    module_files[filename] = {"path": str(path), "sha256": sha256_file(path)}

action_description = HighLevelActionSet(multiaction=False, strict=False).describe(
    with_long_description=False,
    with_examples=True,
)

chromium = {
    "launch_ok": False,
    "launch_error": None,
    "browser_version": None,
    "executable_path": None,
    "executable_sha256": None,
    "browsers_json_path": None,
    "browsers_json_sha256": None,
    "browsers_json_chromium": [],
}
try:
    import playwright
    playwright_root = Path(inspect.getfile(playwright)).resolve().parent
    browsers_json = playwright_root / "driver" / "package" / "browsers.json"
    if browsers_json.is_file():
        chromium["browsers_json_path"] = str(browsers_json)
        chromium["browsers_json_sha256"] = sha256_file(browsers_json)
        browser_payload = json.loads(browsers_json.read_text(encoding="utf-8"))
        chromium["browsers_json_chromium"] = [
            item for item in browser_payload.get("browsers", [])
            if str(item.get("name") or "").startswith("chromium")
        ]
    from playwright.sync_api import sync_playwright
    with sync_playwright() as manager:
        executable = Path(manager.chromium.executable_path).resolve()
        chromium["executable_path"] = str(executable)
        if executable.is_file():
            chromium["executable_sha256"] = sha256_file(executable)
        browser = manager.chromium.launch(headless=True)
        try:
            chromium["browser_version"] = browser.version
            chromium["launch_ok"] = True
        finally:
            browser.close()
except Exception as exc:
    chromium["launch_error"] = f"{type(exc).__name__}: {exc}"

print(json.dumps({
    "python": {
        "executable": sys.executable,
        "version": sys.version,
        "version_info": list(sys.version_info[:5]),
    },
    "distributions": {
        name: distribution_version(name)
        for name in ("browsergym-miniwob", "browsergym-core", "gymnasium", "playwright")
    },
    "package_root": str(package_root),
    "playwright_browsers_path": os.environ.get("PLAYWRIGHT_BROWSERS_PATH"),
    "module_files": module_files,
    "registry_task_ids": sorted(task_cls.get_task_id() for task_cls in miniwob.ALL_MINIWOB_TASKS),
    "action_set": {"class": "HighLevelActionSet", "multiaction": False, "strict": False},
    "action_space_description_sha256": hashlib.sha256(action_description.encode("utf-8")).hexdigest(),
    "chromium": chromium,
}, indent=2, sort_keys=True))
'''
