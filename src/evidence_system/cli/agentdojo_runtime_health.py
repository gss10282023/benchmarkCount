"""Record or summarize AgentDojo's evidence-blind OpenRouter health ledger."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Sequence

from evidence_system.adapters.agentdojo_runtime_control import (
    BlindHealthLedger,
    GlobalRateLimiter,
    RampResourceLedger,
    RuntimePolicyError,
    build_formal_stage_health_receipt,
    load_formal_stage_health_receipt,
    load_runtime_policy,
    linux_host_boot_id,
    summarize_blind_health,
    sample_linux_host_resources,
)
from evidence_system.core.hashing import sha256_file, sha256_object


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    record = subparsers.add_parser("record")
    record.add_argument("--policy", required=True)
    record.add_argument("--ledger", required=True)
    record.add_argument(
        "--event-type",
        required=True,
        choices=("credential_probe", "budget_probe", "ramp_health", "incident"),
    )
    record.add_argument(
        "--outcome",
        required=True,
        choices=("success", "passed", "retryable_error", "fatal_error", "blocked", "warning"),
    )
    record.add_argument("--http-status", type=int)
    record.add_argument("--latency-seconds", type=float)
    record.add_argument("--credit-balance-usd", type=float)
    record.add_argument("--credit-floor-usd", type=float)
    record.add_argument("--active-requests", type=int)
    record.add_argument("--requests-in-window", type=int)
    record.add_argument("--tokens-in-window", type=int)
    record.add_argument("--cumulative-cost-usd", type=float)

    summary = subparsers.add_parser("summarize")
    summary.add_argument("--ledger", required=True)
    resource = subparsers.add_parser("sample-resource")
    resource.add_argument("--ledger", required=True)
    resource.add_argument("--worker-concurrency", type=int, required=True)
    resource.add_argument("--sample-seconds", type=float, default=0.25)
    resource.add_argument("--policy", required=True)
    resource.add_argument("--runtime-state-dir", required=True)
    resource.add_argument(
        "--budget-scope",
        required=True,
        choices=("formal_execution", "disposable_preflight"),
    )
    resource.add_argument("--expected-database-path", required=True)
    resource.add_argument("--session-id", required=True)
    resource.add_argument("--host-boot-id", required=True)
    resource.add_argument("--stage-binding-sha256", required=True)
    resource.add_argument("--worker-process-binding-sha256", required=True)
    resource.add_argument("--expected-worker-uid", type=int, required=True)
    resource.add_argument(
        "--minimum-worker-starttime-ticks", type=int, required=True
    )
    resource.add_argument("--shared-group")
    formal = subparsers.add_parser("formal-stage-receipt")
    formal.add_argument("--policy", required=True)
    formal.add_argument("--runtime-infra", required=True)
    formal.add_argument("--stage-workload", required=True)
    formal.add_argument("--blind-health-ledger", required=True)
    formal.add_argument("--resource-ledger", required=True)
    formal.add_argument("--session-id", required=True)
    formal.add_argument("--host-boot-id")
    formal.add_argument("--session-started-at", required=True)
    formal.add_argument("--session-ended-at", required=True)
    formal.add_argument("--prior-safe-workers", type=int, required=True)
    formal.add_argument("--output", required=True)
    verify = subparsers.add_parser("verify-formal-stage-receipt")
    verify.add_argument("--receipt", required=True)
    verify.add_argument("--execution-lock-sha256", required=True)
    verify.add_argument("--execution-policy-sha256", required=True)
    verify.add_argument("--plan-index-sha256", required=True)
    verify.add_argument("--stage-id", required=True)
    verify.add_argument("--workers", type=int, required=True)
    verify.add_argument("--record-slot-count", type=int, required=True)
    verify.add_argument("--record-slot-ids-sha256", required=True)
    verify.add_argument("--stage-workload-sha256", required=True)
    verify.add_argument("--runtime-infra-sha256", required=True)
    verify.add_argument("--session-id", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "summarize":
            result = summarize_blind_health(args.ledger)
        elif args.command == "sample-resource":
            live_boot_id = linux_host_boot_id()
            if args.host_boot_id != live_boot_id:
                raise RuntimePolicyError(
                    "resource sampler host boot differs from the live Linux boot"
                )
            policy = load_runtime_policy(
                json.loads(Path(args.policy).read_text(encoding="utf-8"))
            )
            limiter = GlobalRateLimiter(
                policy,
                state_dir=args.runtime_state_dir,
                budget_scope=args.budget_scope,
                host_boot_id=args.host_boot_id,
            )
            expected_database_path = Path(args.expected_database_path)
            if (
                not expected_database_path.is_absolute()
                or expected_database_path.resolve()
                != limiter.database_path.resolve()
                or limiter.database_path.is_symlink()
                or not limiter.database_path.is_file()
                or limiter.database_path.stat().st_nlink != 1
            ):
                raise RuntimePolicyError(
                    "resource sampler limiter database path/identity differs"
                )
            observed = sample_linux_host_resources(
                sample_seconds=args.sample_seconds,
                worker_process_binding_sha256=(
                    args.worker_process_binding_sha256
                ),
                expected_worker_uid=args.expected_worker_uid,
                minimum_worker_starttime_ticks=(
                    args.minimum_worker_starttime_ticks
                ),
            )
            observed["active_openrouter_leases"] = limiter.snapshot().active_requests
            result = RampResourceLedger(
                args.ledger, shared_group=args.shared_group
            ).record(
                worker_concurrency=args.worker_concurrency,
                session_id=args.session_id,
                host_boot_id=args.host_boot_id,
                budget_scope=args.budget_scope,
                runtime_database_path_sha256=sha256_object(
                    {"absolute_path": str(limiter.database_path.resolve())}
                ),
                stage_binding_sha256=args.stage_binding_sha256,
                **observed,
            )
        elif args.command == "formal-stage-receipt":
            policy = load_runtime_policy(
                json.loads(Path(args.policy).read_text(encoding="utf-8"))
            )
            workload = json.loads(
                Path(args.stage_workload).read_text(encoding="utf-8")
            )
            if not isinstance(workload, dict):
                raise RuntimePolicyError("formal stage workload must be an object")
            result = build_formal_stage_health_receipt(
                policy,
                stage_workload=workload,
                runtime_infra_file_sha256=sha256_file(args.runtime_infra),
                blind_health_ledger_path=args.blind_health_ledger,
                resource_ledger_path=args.resource_ledger,
                session_id=args.session_id,
                host_boot_id=args.host_boot_id or linux_host_boot_id(),
                session_started_at=args.session_started_at,
                session_ended_at=args.session_ended_at,
                prior_safe_workers=args.prior_safe_workers,
            )
            _write_once(Path(args.output), result)
        elif args.command == "verify-formal-stage-receipt":
            result = load_formal_stage_health_receipt(
                args.receipt,
                expected_execution_lock_sha256=args.execution_lock_sha256,
                expected_execution_policy_sha256=args.execution_policy_sha256,
                expected_plan_index_sha256=args.plan_index_sha256,
                expected_stage_id=args.stage_id,
                expected_workers=args.workers,
                expected_record_slot_count=args.record_slot_count,
                expected_record_slot_ids_sha256=args.record_slot_ids_sha256,
                expected_workload_sha256=args.stage_workload_sha256,
                expected_runtime_infra_file_sha256=args.runtime_infra_sha256,
                expected_session_id=args.session_id,
            )
        else:
            policy_path = Path(args.policy)
            policy = load_runtime_policy(json.loads(policy_path.read_text(encoding="utf-8")))
            fields: dict[str, Any] = {}
            for argument, field in (
                ("http_status", "http_status"),
                ("latency_seconds", "latency_seconds"),
                ("credit_balance_usd", "credit_balance_usd"),
                ("credit_floor_usd", "credit_floor_usd"),
                ("active_requests", "active_requests"),
                ("requests_in_window", "requests_in_window"),
                ("tokens_in_window", "tokens_in_window"),
                ("cumulative_cost_usd", "cumulative_cost_usd"),
            ):
                value = getattr(args, argument)
                if value is not None:
                    fields[field] = value
            result = BlindHealthLedger(
                (args.ledger,), policy_sha256=policy.semantic_sha256
            ).record(event_type=args.event_type, outcome=args.outcome, **fields)
    except (OSError, ValueError, RuntimePolicyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error_type": type(exc).__name__, "error_message": str(exc)}))
        return 1
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


def _write_once(path: Path, payload: dict[str, Any]) -> None:
    if path.is_symlink() or path.exists():
        raise RuntimePolicyError("formal health receipt output must not already exist")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        path,
        os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        os.fchmod(descriptor, 0o600)
        encoded = (
            json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        os.write(descriptor, encoded)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
