#!/usr/bin/env python3
"""Audit candidate116 coverage and run only missing AndroidWorld agent slots.

The planner is always built from the frozen candidate116 manifest.  Existing
legacy results are accepted only when they contain a completed native
AndroidWorld episode and evaluator output; their older source-bundle binding is
not used as a reason to rerun or overwrite them.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable, Mapping

from evidence_system.orchestrator.jobs import execute_planned_jobs, plan_smoke_jobs


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/manifests/androidworld_candidate116_manifest.json"
SOURCE_BUNDLE = REPO_ROOT / "rebuttal_work/runtime_outputs/submission_rebuttal/androidworld_candidate116/source_bundles/androidworld_candidate116_source_bundle.json"
CONTRACTS_DIR = REPO_ROOT / "experiments/evidence_contracts/locked"
INFRA_CONFIG = REPO_ROOT / "configs/infra.androidworld_gold.yaml"
AGENTS_CONFIG = REPO_ROOT / "configs/agents.yaml"
JOBS_DIR = REPO_ROOT / "androidworld_gold_execution/jobs"
RESULTS_ROOT = REPO_ROOT / "results/full/androidworld"
ADB = Path.home() / "Library/Android/sdk/platform-tools/adb"
EXPECTED_FINGERPRINT = "google/sdk_gphone64_arm64/emu64a:13/TE1A.240213.009/12342917:userdebug/dev-keys"
EXPECTED_MODELS = {
    "Agent A": "openai/gpt-5.4",
    "Agent B": "anthropic/claude-opus-4.7",
    "Agent C": "deepseek/deepseek-v4-pro",
}


@dataclass(frozen=True)
class SlotAudit:
    state: str
    reasons: tuple[str, ...]
    warnings: tuple[str, ...] = ()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _suffix(agent_id: str) -> str:
    return agent_id.lower().replace(" ", "_")


def _result_root(task_id: str, agent_id: str) -> Path:
    return RESULTS_ROOT / f"full-androidworld-{task_id}-{_suffix(agent_id)}"


def _summary(root: Path) -> dict[str, Any] | None:
    for path in (
        root / "adapter/native_run/run_summary.json",
        root / "worker_output/run_summary.json",
    ):
        payload = _load_json(path)
        if payload is not None:
            return payload
    return None


def audit_result(task_id: str, agent_id: str) -> SlotAudit:
    root = _result_root(task_id, agent_id)
    if not root.exists():
        return SlotAudit("missing", ())

    reasons: list[str] = []
    warnings: list[str] = []
    raw = _load_json(root / "adapter/raw_run.json")
    manifest = _load_json(root / "adapter/artifact_manifest.json")
    environment = _load_json(root / "adapter/environment.json")
    summary = _summary(root)
    native_eval = _load_json(root / "adapter/native_run/native_evaluator_output.json")
    if native_eval is None:
        native_eval = _load_json(root / "worker_output/native_evaluator_output.json")

    if raw is None:
        reasons.append("missing_or_invalid_adapter_raw_run")
    else:
        expected_raw = {
            "schema_version": "raw_run/v1",
            "case_unit_id": task_id,
            "task_id": task_id,
            "agent_id": agent_id,
            "phase": "full",
            "diagnostic_status": "completed",
            "appendix_failure_class": "none",
        }
        for key, expected in expected_raw.items():
            if raw.get(key) != expected:
                reasons.append(f"raw_run_{key}_mismatch")
        if str(raw.get("status") or "").upper() != "COMPLETED":
            reasons.append("raw_run_not_completed")
        if raw.get("native_label") not in {"success", "fail"}:
            reasons.append("raw_run_native_label_invalid")
        raw_score = raw.get("native_score")
        if (
            not isinstance(raw_score, (int, float))
            or isinstance(raw_score, bool)
            or not 0.0 <= float(raw_score) <= 1.0
        ):
            reasons.append("raw_run_native_score_invalid")
        if not list(raw.get("episode_ids") or []):
            reasons.append("raw_run_episode_ids_empty")

    if manifest is None:
        reasons.append("missing_or_invalid_adapter_artifact_manifest")
    else:
        if manifest.get("schema_version") != "artifact_manifest/v1":
            reasons.append("artifact_manifest_schema_invalid")
        for key, expected in (
            ("case_unit_id", task_id),
            ("task_id", task_id),
            ("agent_id", agent_id),
            ("phase", "full"),
        ):
            if manifest.get(key) != expected:
                reasons.append(f"artifact_manifest_{key}_mismatch")
        artifact_types = {
            str(row.get("artifact_type"))
            for row in list(manifest.get("artifacts") or [])
            if isinstance(row, Mapping)
        }
        for required in ("native_evaluator_input", "native_evaluator_output", "trace", "tool_log"):
            if required not in artifact_types:
                reasons.append(f"artifact_type_missing_{required}")

    if environment is None:
        reasons.append("missing_or_invalid_environment")
    elif environment.get("job_id") != f"full-androidworld-{task_id}-{_suffix(agent_id)}":
        reasons.append("environment_job_id_mismatch")

    if summary is None:
        reasons.append("missing_or_invalid_run_summary")
    else:
        if summary.get("status") != "completed":
            reasons.append("run_summary_not_completed")
        if summary.get("task_name") != task_id:
            reasons.append("run_summary_task_name_mismatch")
        if not isinstance(summary.get("success"), bool):
            reasons.append("run_summary_success_not_boolean")
        if summary.get("exception_info") is not None:
            reasons.append("run_summary_has_exception")

    if native_eval is None:
        reasons.append("missing_or_invalid_native_evaluator_output")
    else:
        if native_eval.get("schema_version") != "androidworld_native_evaluator_output/v1":
            reasons.append("native_evaluator_schema_invalid")
        if native_eval.get("task_name") != task_id:
            reasons.append("native_evaluator_task_name_mismatch")
        evaluator_score = native_eval.get("success")
        if (
            not isinstance(evaluator_score, (int, float))
            or isinstance(evaluator_score, bool)
            or not 0.0 <= float(evaluator_score) <= 1.0
        ):
            reasons.append("native_evaluator_success_invalid")
        if native_eval.get("exception_info") is not None:
            reasons.append("native_evaluator_has_exception")

    llm_dir = root / "adapter/llm_calls"
    llm_calls = sorted(llm_dir.glob("*.json")) if llm_dir.is_dir() else []
    if not llm_calls:
        reasons.append("llm_call_logs_empty")
    for path in llm_calls:
        call = _load_json(path)
        if call is None:
            reasons.append(f"invalid_llm_call_{path.name}")
            continue
        if call.get("provider") != "openrouter":
            reasons.append(f"llm_provider_mismatch_{path.name}")
        if call.get("model") != EXPECTED_MODELS[agent_id]:
            reasons.append(f"llm_model_mismatch_{path.name}")
        metadata = call.get("response_metadata")
        if not isinstance(metadata, Mapping):
            reasons.append(f"llm_response_metadata_invalid_{path.name}")
        elif metadata.get("status") != "success":
            warnings.append(f"llm_retry_attempt_failed_{path.name}")

    return SlotAudit(
        "valid" if not reasons else "invalid",
        tuple(sorted(set(reasons))),
        tuple(sorted(set(warnings))),
    )


def _device_value(*args: str) -> str:
    completed = subprocess.run(
        [str(ADB), "-s", "emulator-5554", *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout.strip()


def verify_gold_device() -> None:
    checks = {
        "state": (_device_value("get-state"), "device"),
        "sdk": (_device_value("shell", "getprop", "ro.build.version.sdk"), "33"),
        "fingerprint": (
            _device_value("shell", "getprop", "ro.build.fingerprint"),
            EXPECTED_FINGERPRINT,
        ),
        "size": (_device_value("shell", "wm", "size"), "Physical size: 1080x2400"),
        "density": (_device_value("shell", "wm", "density"), "Physical density: 420"),
    }
    failures = [f"{key}: actual={actual!r} expected={expected!r}" for key, (actual, expected) in checks.items() if actual != expected]
    if failures:
        raise RuntimeError("gold AVD preflight failed: " + "; ".join(failures))
    snapshot_count = int(_device_value("shell", "sh", "-c", "find /data/data/android_world/snapshots -mindepth 1 -maxdepth 1 -type d | wc -l"))
    if snapshot_count < 24:
        raise RuntimeError(f"gold AVD has only {snapshot_count} app snapshots; expected at least 24")


def _planned_jobs(agent_ids: Iterable[str]):
    planned = []
    for agent_id in agent_ids:
        planned.extend(
            plan_smoke_jobs(
                domain="androidworld",
                phase="full",
                experiment_type="appendix",
                case_count=None,
                agent_ids=[agent_id],
                seed=7,
                manifest_path=MANIFEST,
                source_bundle_path=SOURCE_BUNDLE,
                contracts_dir=CONTRACTS_DIR,
                infra_config_path=INFRA_CONFIG,
                agents_config_path=AGENTS_CONFIG,
                jobs_dir=JOBS_DIR,
            )
        )
    return planned


def _coverage(planned) -> tuple[Counter[str], list[Any], list[tuple[Any, SlotAudit]], list[tuple[Any, SlotAudit]]]:
    counts: Counter[str] = Counter()
    missing = []
    invalid = []
    warnings = []
    for item in planned:
        audit = audit_result(str(item.job["task_id"]), str(item.job["agent_id"]))
        counts[audit.state] += 1
        if audit.state == "missing":
            missing.append(item)
        elif audit.state == "invalid":
            invalid.append((item, audit))
        if audit.warnings:
            warnings.append((item, audit))
    return counts, missing, invalid, warnings


def _print_audit(counts: Counter[str], missing, invalid, warnings) -> None:
    print(
        json.dumps(
            {
                "slot_count": sum(counts.values()),
                "counts": dict(sorted(counts.items())),
                "missing": [
                    {"task_id": item.job["task_id"], "agent_id": item.job["agent_id"]}
                    for item in missing
                ],
                "invalid": [
                    {
                        "task_id": item.job["task_id"],
                        "agent_id": item.job["agent_id"],
                        "reasons": list(audit.reasons),
                    }
                    for item, audit in invalid
                ],
                "warnings": [
                    {
                        "task_id": item.job["task_id"],
                        "agent_id": item.job["agent_id"],
                        "warnings": list(audit.warnings),
                    }
                    for item, audit in warnings
                ],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        flush=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Run missing slots after the audit.")
    parser.add_argument("--agent-id", action="append", choices=tuple(EXPECTED_MODELS), default=[])
    parser.add_argument("--max-jobs", type=int, default=None)
    args = parser.parse_args(argv)

    agent_ids = args.agent_id or list(EXPECTED_MODELS)
    verify_gold_device()
    planned = _planned_jobs(agent_ids)
    counts, missing, invalid, warnings = _coverage(planned)
    _print_audit(counts, missing, invalid, warnings)
    if invalid:
        print("Refusing to overwrite invalid/non-final result directories.", file=sys.stderr)
        return 2
    if not args.execute:
        return 0
    if args.max_jobs is not None:
        if args.max_jobs < 1:
            parser.error("--max-jobs must be positive")
        missing = missing[: args.max_jobs]

    total = len(missing)
    for index, item in enumerate(missing, start=1):
        print(
            f"RUN {index}/{total} agent={item.job['agent_id']} task={item.job['task_id']}",
            flush=True,
        )

        def progress_callback(planned_item, execution_result, done_count, total_count):
            print(
                f"EXECUTOR status={execution_result.get('status')} job={planned_item.job['job_id']} {done_count}/{total_count}",
                flush=True,
            )

        execute_planned_jobs(
            [item],
            manifest_path=MANIFEST,
            source_bundle_path=SOURCE_BUNDLE,
            infra_config_path=INFRA_CONFIG,
            agents_config_path=AGENTS_CONFIG,
            max_workers=1,
            progress_callback=progress_callback,
            fail_fast_on_noncompleted=True,
            skip_completed=False,
            retry_no_response_attempts=2,
            continue_on_error=False,
        )
        audit = audit_result(str(item.job["task_id"]), str(item.job["agent_id"]))
        if audit.state != "valid":
            raise RuntimeError(
                f"post-run audit failed for {item.job['job_id']}: {list(audit.reasons)}"
            )
        print(
            f"VALID {index}/{total} agent={item.job['agent_id']} task={item.job['task_id']}",
            flush=True,
        )

    final_counts, final_missing, final_invalid, final_warnings = _coverage(planned)
    _print_audit(final_counts, final_missing, final_invalid, final_warnings)
    return 0 if not final_missing and not final_invalid else 3


if __name__ == "__main__":
    raise SystemExit(main())
