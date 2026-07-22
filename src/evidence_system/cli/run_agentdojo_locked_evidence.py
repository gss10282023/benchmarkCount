"""Plan and run the staged, execution-locked AgentDojo full evidence branch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from evidence_system.contracts.agentdojo_full_execution import (
    DEFAULT_RUNTIME_INFRA_OVERLAY,
)
from evidence_system.contracts.agentdojo_execution_namespace import (
    DEFAULT_NAMESPACE_INIT_RECEIPT,
)
from evidence_system.contracts.agentdojo_full_experiment import (
    DEFAULT_AGENTS_CONFIG,
    DEFAULT_MANIFEST,
    DEFAULT_SOURCE_BUNDLE,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.orchestrator.agentdojo_locked_runner import (
    DEFAULT_ANOMALY_RECEIPT,
    DEFAULT_COMPLETION_RECEIPT,
    DEFAULT_JOB_PLAN_INDEX,
    DEFAULT_LOCKED_JOBS_DIR,
    DEFAULT_STAGE_EXECUTION_ROOT,
    DEFAULT_STAGE_AUTHORIZATION_ROOT,
    DEFAULT_CONTROLLER_LIFECYCLE_LOCK,
    DEFAULT_MACHINE_HEALTH_ROOT,
    DEFAULT_STAGE_INTENT_ROOT,
    DEFAULT_STAGE_WORKLOAD_ROOT,
    DEFAULT_STAGE_RECEIPT_ROOT,
    STAGE_ORDER,
    build_and_verify_locked_plan,
    finalize_formal_execution_receipts,
    run_locked_stage,
    run_all_locked_stages,
    seal_locked_stage,
    select_locked_stage,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execution-lock",
        type=Path,
        required=True,
        help="A real, current execution_lock.json is mandatory; no unlocked mode exists.",
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source-bundle", type=Path, default=DEFAULT_SOURCE_BUNDLE)
    parser.add_argument("--runtime-infra", type=Path, default=DEFAULT_RUNTIME_INFRA_OVERLAY)
    parser.add_argument("--agents-config", type=Path, default=DEFAULT_AGENTS_CONFIG)
    parser.add_argument("--jobs-dir", type=Path, default=DEFAULT_LOCKED_JOBS_DIR)
    parser.add_argument("--plan-index", type=Path, default=DEFAULT_JOB_PLAN_INDEX)
    parser.add_argument(
        "--namespace-init-receipt",
        type=Path,
        default=DEFAULT_NAMESPACE_INIT_RECEIPT,
        help="Mandatory post-lock remote namespace-init receipt for run/seal/finalize.",
    )
    parser.add_argument("--stage-receipt-root", type=Path, default=DEFAULT_STAGE_RECEIPT_ROOT)
    parser.add_argument(
        "--stage-authorization-root",
        type=Path,
        default=DEFAULT_STAGE_AUTHORIZATION_ROOT,
    )
    parser.add_argument(
        "--stage-execution-root", type=Path, default=DEFAULT_STAGE_EXECUTION_ROOT
    )
    parser.add_argument("--stage-intent-root", type=Path, default=DEFAULT_STAGE_INTENT_ROOT)
    parser.add_argument("--machine-health-root", type=Path, default=DEFAULT_MACHINE_HEALTH_ROOT)
    parser.add_argument("--stage-workload-root", type=Path, default=DEFAULT_STAGE_WORKLOAD_ROOT)
    parser.add_argument(
        "--controller-lifecycle-lock",
        type=Path,
        default=DEFAULT_CONTROLLER_LIFECYCLE_LOCK,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "plan-verify", help="Materialize and verify all 2,847 execution-bound job files."
    )
    run = subparsers.add_parser(
        "run-stage",
        help="Run one locked stage; failures are sealed and do not stop the batch.",
    )
    run.add_argument("--stage", required=True, choices=STAGE_ORDER)
    run_all = subparsers.add_parser(
        "run-all",
        help="Crash-resumably execute, sample, health-seal, and advance all stages.",
    )
    run_all.add_argument("--stop-after-stage", choices=STAGE_ORDER)
    seal = subparsers.add_parser(
        "seal-stage",
        help="Bind the stage execution observation to its machine blind-health receipt.",
    )
    seal.add_argument("--stage", required=True, choices=STAGE_ORDER)
    seal.add_argument("--post-stage-health-receipt", type=Path, required=True)
    finalize = subparsers.add_parser(
        "finalize",
        help="Freeze blind completion/anomaly receipts after all recovery stages.",
    )
    finalize.add_argument("--completion-receipt", type=Path, default=DEFAULT_COMPLETION_RECEIPT)
    finalize.add_argument("--anomaly-receipt", type=Path, default=DEFAULT_ANOMALY_RECEIPT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        plan = build_and_verify_locked_plan(
            execution_lock_path=args.execution_lock,
            manifest_path=args.manifest,
            source_bundle_path=args.source_bundle,
            infra_config_path=args.runtime_infra,
            agents_config_path=args.agents_config,
            jobs_dir=args.jobs_dir,
            plan_index_path=args.plan_index,
        )
        if args.command == "plan-verify":
            result: dict[str, Any] = {
                "status": "verified",
                "execution_lock_sha256": plan.execution.lock_sha256,
                "execution_policy_sha256": plan.execution.definition[
                    "execution_policy_sha256"
                ],
                "job_count": len(plan.planned),
                "record_slot_count": len(plan.by_slot),
                "plan_index_path": str(plan.plan_index_path),
                "plan_index_sha256": plan.plan_index_sha256,
                "agent_batch_order": ["Agent A", "Agent B", "Agent C"],
                "blind_only": True,
            }
        elif args.command == "run-stage":
            stage = select_locked_stage(plan, args.stage)
            result = run_locked_stage(
                plan,
                stage,
                manifest_path=args.manifest,
                source_bundle_path=args.source_bundle,
                infra_config_path=args.runtime_infra,
                agents_config_path=args.agents_config,
                receipt_root=args.stage_receipt_root,
                execution_observation_root=args.stage_execution_root,
                namespace_init_receipt_path=args.namespace_init_receipt,
                stage_authorization_root=args.stage_authorization_root,
                stage_intent_root=args.stage_intent_root,
                controller_lifecycle_lock_path=args.controller_lifecycle_lock,
            )
        elif args.command == "run-all":
            result = run_all_locked_stages(
                plan,
                manifest_path=args.manifest,
                source_bundle_path=args.source_bundle,
                infra_config_path=args.runtime_infra,
                agents_config_path=args.agents_config,
                receipt_root=args.stage_receipt_root,
                execution_observation_root=args.stage_execution_root,
                stage_authorization_root=args.stage_authorization_root,
                stage_intent_root=args.stage_intent_root,
                machine_health_root=args.machine_health_root,
                stage_workload_root=args.stage_workload_root,
                namespace_init_receipt_path=args.namespace_init_receipt,
                controller_lifecycle_lock_path=args.controller_lifecycle_lock,
                stop_after_stage=args.stop_after_stage,
            )
        elif args.command == "seal-stage":
            stage = select_locked_stage(plan, args.stage)
            result = seal_locked_stage(
                plan,
                stage,
                post_stage_health_receipt_path=args.post_stage_health_receipt,
                receipt_root=args.stage_receipt_root,
                execution_observation_root=args.stage_execution_root,
                namespace_init_receipt_path=args.namespace_init_receipt,
                controller_lifecycle_lock_path=args.controller_lifecycle_lock,
            )
        else:
            completion, anomaly = finalize_formal_execution_receipts(
                plan,
                receipt_root=args.stage_receipt_root,
                completion_path=args.completion_receipt,
                anomaly_path=args.anomaly_receipt,
                namespace_init_receipt_path=args.namespace_init_receipt,
            )
            result = {
                "status": completion["status"],
                "execution_lock_sha256": plan.execution.lock_sha256,
                "completion_receipt_path": completion["receipt_path"],
                "completion_receipt_sha256": completion["receipt_sha256"],
                "anomaly_receipt_path": anomaly["receipt_path"],
                "anomaly_receipt_sha256": anomaly["receipt_sha256"],
                "unresolved_failure_count": completion["unresolved_failure_count"],
                "blind_only": True,
            }
    except (ContractLifecycleError, OSError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "formal_episode_started": False,
                },
                ensure_ascii=True,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
