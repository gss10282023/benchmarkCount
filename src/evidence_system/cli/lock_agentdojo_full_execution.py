"""Publish or verify the pre-run AgentDojo full execution lock."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from evidence_system.contracts.agentdojo_execution_budget import DEFAULT_BUDGET_PLAN
from evidence_system.contracts.agentdojo_execution_namespace import (
    DEFAULT_FINAL_RUNTIME_DEPLOYMENT_RECEIPT,
    DEFAULT_REMOTE_OUTPUT_PRECONDITION_RECEIPT,
)
from evidence_system.contracts.agentdojo_full_execution import (
    DEFAULT_CREDIT_FLOOR_USD,
    DEFAULT_CREDENTIAL_PROBE_RECEIPT,
    DEFAULT_DISPOSABLE_RAMP_RECEIPT,
    DEFAULT_EXECUTION_LOCK,
    DEFAULT_RAMP_WORKERS,
    DEFAULT_RUNTIME_INFRA_OVERLAY,
    DEFAULT_RUNTIME_POLICY,
    DEFAULT_VPS_PROVISION_RECEIPT,
    publish_execution_lock,
    verify_execution_lock,
)
from evidence_system.contracts.agentdojo_full_experiment import (
    DEFAULT_AGENTS_CONFIG,
    DEFAULT_CASE_PACKETS,
    DEFAULT_CATALOG,
    DEFAULT_MANIFEST,
    DEFAULT_SOURCE_BUNDLE,
)
from evidence_system.contracts.common import ContractLifecycleError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--source-bundle", type=Path, default=DEFAULT_SOURCE_BUNDLE)
    parser.add_argument(
        "--case-packets-root", type=Path, default=DEFAULT_CASE_PACKETS / "agentdojo"
    )
    parser.add_argument("--agents-config", type=Path, default=DEFAULT_AGENTS_CONFIG)
    parser.add_argument(
        "--runtime-infra",
        type=Path,
        default=DEFAULT_RUNTIME_INFRA_OVERLAY,
        help="AgentDojo-only runtime overlay; configs/infra.yaml is rejected.",
    )
    parser.add_argument("--runtime-policy", type=Path, default=DEFAULT_RUNTIME_POLICY)
    parser.add_argument(
        "--credential-probe-receipt",
        type=Path,
        default=DEFAULT_CREDENTIAL_PROBE_RECEIPT,
    )
    parser.add_argument(
        "--disposable-ramp-receipt",
        type=Path,
        default=DEFAULT_DISPOSABLE_RAMP_RECEIPT,
    )
    parser.add_argument(
        "--vps-provision-receipt", type=Path, default=DEFAULT_VPS_PROVISION_RECEIPT
    )
    parser.add_argument(
        "--remote-output-precondition-receipt",
        type=Path,
        default=DEFAULT_REMOTE_OUTPUT_PRECONDITION_RECEIPT,
    )
    parser.add_argument(
        "--final-runtime-deployment-receipt",
        type=Path,
        default=DEFAULT_FINAL_RUNTIME_DEPLOYMENT_RECEIPT,
    )
    parser.add_argument("--base-seed", type=int, default=7)
    parser.add_argument(
        "--ramp-worker",
        action="append",
        type=int,
        default=None,
        help="Concurrency ramp value; repeat in increasing order (default 4,8,16,32).",
    )
    parser.add_argument(
        "--maximum-workers",
        type=int,
        default=None,
        help=(
            "Assert the finalized active worker ceiling; by default it is "
            "derived from the finalized OpenRouter runtime policy."
        ),
    )
    parser.add_argument("--retry-transient-model", type=int, default=2)
    failure = parser.add_mutually_exclusive_group()
    failure.add_argument(
        "--continue-on-error",
        dest="continue_on_job_error",
        action="store_true",
        help="Record blind job-health failures and finish the batch.",
    )
    failure.add_argument(
        "--fail-fast",
        dest="continue_on_job_error",
        action="store_false",
        help="Stop the batch at the first job failure.",
    )
    parser.set_defaults(continue_on_job_error=True)
    parser.add_argument("--budget-plan", type=Path, default=DEFAULT_BUDGET_PLAN)
    parser.add_argument("--credit-preflight-receipt", type=Path)
    parser.add_argument(
        "--credit-floor-usd", type=float, default=DEFAULT_CREDIT_FLOOR_USD
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_EXECUTION_LOCK)
    parser.add_argument("--locked-at")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Recompute immutable inputs without requiring output directories to remain empty.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.verify_only and args.locked_at:
        print("--verify-only cannot be combined with --locked-at")
        return 2
    ramp_workers = tuple(args.ramp_worker or DEFAULT_RAMP_WORKERS)
    try:
        if args.verify_only:
            result = verify_execution_lock(
                lock_path=args.output,
                manifest_path=args.manifest,
                source_bundle_path=args.source_bundle,
                agents_config_path=args.agents_config,
                runtime_infra_path=args.runtime_infra,
            )
            action = "verified"
        else:
            result = publish_execution_lock(
                output_path=args.output,
                locked_at=args.locked_at,
                manifest_path=args.manifest,
                catalog_path=args.catalog,
                source_bundle_path=args.source_bundle,
                case_packets_root=args.case_packets_root,
                agents_config_path=args.agents_config,
                runtime_infra_path=args.runtime_infra,
                runtime_policy_path=args.runtime_policy,
                credential_probe_receipt_path=args.credential_probe_receipt,
                disposable_ramp_receipt_path=args.disposable_ramp_receipt,
                vps_provision_receipt_path=args.vps_provision_receipt,
                remote_output_precondition_receipt_path=(
                    args.remote_output_precondition_receipt
                ),
                final_runtime_deployment_receipt_path=(
                    args.final_runtime_deployment_receipt
                ),
                base_seed=args.base_seed,
                ramp_workers=ramp_workers,
                maximum_workers=args.maximum_workers,
                retry_transient_model_attempts=args.retry_transient_model,
                continue_on_job_error=args.continue_on_job_error,
                budget_plan_path=args.budget_plan,
                credit_preflight_receipt_path=args.credit_preflight_receipt,
                credit_floor_usd=args.credit_floor_usd,
            )
            action = "published" if result.created else "already_identical"
    except (ContractLifecycleError, OSError, ValueError) as exc:
        print(str(exc))
        return 2

    definition = result.definition
    print(
        json.dumps(
            {
                "action": action,
                "lock_path": str(result.lock_path),
                "lock_sha256": result.lock_sha256,
                "case_count": definition["case_set"]["case_count"],
                "job_count": definition["job_plan"]["job_count"],
                "execution_policy_sha256": definition["execution_policy_sha256"],
                "runtime_infra_sha256": definition["runtime_infra_overlay"]["sha256"],
                "runtime_policy_sha256": definition["runtime_policy"]["sha256"],
                "vps_provision_receipt_sha256": definition[
                    "vps_provision_receipt"
                ]["sha256"],
                "budget_plan_sha256": definition["budget_control"]["budget_plan"][
                    "sha256"
                ],
                "staging_result_namespace": definition["staging_result_namespace"],
                "staging_raw_result_file_count_at_publish": definition[
                    "output_precondition"
                ]["staging_raw_result_file_count"],
                "formal_raw_result_file_count_at_publish": definition[
                    "output_precondition"
                ]["formal_raw_result_file_count"],
                "score_result_file_count_at_publish": definition[
                    "output_precondition"
                ]["score_result_file_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
