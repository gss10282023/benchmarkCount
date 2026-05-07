"""Plan provisional Step 8 smoke-domain jobs."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from evidence_system.cli._common import BootstrapCommand, bootstrap_main
from evidence_system.orchestrator.jobs import execute_smoke_jobs, plan_smoke_jobs


COMMAND = BootstrapCommand(
    name="run_domain",
    responsibility="Plan provisional Step 8 smoke jobs and adapter commands for one canonical domain.",
    owner_module="evidence_system.orchestrator.jobs",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_system.cli.run_domain",
        description=COMMAND.responsibility,
    )
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--execute", action="store_true", help="Run the planned smoke jobs instead of only emitting plans.")
    parser.add_argument("--domain", required=False, help="Canonical domain id such as appworld or tau3_retail.")
    parser.add_argument("--phase", default="smoke")
    parser.add_argument("--experiment-type", default="main")
    parser.add_argument("--case-count", type=int, default=1)
    parser.add_argument("--agent-count", type=int, default=1)
    parser.add_argument("--agent-id", action="append", default=[], help="Explicit agent id(s) to use instead of manifest order.")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--manifest", default="experiments/smoke/experiment_manifest_3_per_domain.yaml")
    parser.add_argument("--source-bundle", default="experiments/smoke/source_bundle_3_per_domain.json")
    parser.add_argument("--contracts-dir", default="experiments/smoke/evidence_contracts/drafts")
    parser.add_argument("--infra-config", default="configs/infra.yaml")
    parser.add_argument("--agents-config", default="experiments/smoke/agents_smoke_gpt54mini.yaml")
    parser.add_argument("--jobs-dir", default="results/jobs/smoke")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.bootstrap_check:
        return bootstrap_main(COMMAND, ["--bootstrap-check", *(["--json"] if args.json else [])])
    if not args.domain:
        parser.error("--domain is required unless --bootstrap-check is used")
    agent_ids = list(args.agent_id) if args.agent_id else [f"Agent {letter}" for letter in "ABC"][: args.agent_count]
    try:
        if args.execute:
            executed = execute_smoke_jobs(
                domain=args.domain,
                phase=args.phase,
                experiment_type=args.experiment_type,
                case_count=args.case_count,
                agent_ids=agent_ids,
                seed=args.seed,
                manifest_path=args.manifest,
                source_bundle_path=args.source_bundle,
                contracts_dir=args.contracts_dir,
                infra_config_path=args.infra_config,
                agents_config_path=args.agents_config,
                jobs_dir=args.jobs_dir,
            )
            payload = {
                "status": "executed",
                "domain": args.domain,
                "phase": args.phase,
                "experiment_type": args.experiment_type,
                "executed_jobs": [
                    {
                        "job_id": item.planned.job["job_id"],
                        "job_path": str(item.planned.job_path),
                        "execution_plan": item.planned.execution_plan,
                        "execution_result": item.execution_result,
                    }
                    for item in executed
                ],
            }
        else:
            planned = plan_smoke_jobs(
                domain=args.domain,
                phase=args.phase,
                experiment_type=args.experiment_type,
                case_count=args.case_count,
                agent_ids=agent_ids,
                seed=args.seed,
                manifest_path=args.manifest,
                source_bundle_path=args.source_bundle,
                contracts_dir=args.contracts_dir,
                infra_config_path=args.infra_config,
                agents_config_path=args.agents_config,
                jobs_dir=args.jobs_dir,
            )
            blocked = [item for item in planned if item.execution_plan.get("status") == "blocked"]
            payload = {
                "status": "planned_with_blockers" if blocked else "planned",
                "domain": args.domain,
                "phase": args.phase,
                "experiment_type": args.experiment_type,
                "planned_jobs": [
                    {
                        "job_id": item.job["job_id"],
                        "job_path": str(item.job_path),
                        "agent_id": item.job["agent_id"],
                        "case_unit_id": item.job["case_unit_id"],
                        "task_id": item.job["task_id"],
                        "execution_plan": item.execution_plan,
                    }
                    for item in planned
                ],
            }
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "error", "message": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"status: {payload['status']}")
        items = payload.get("executed_jobs") or payload.get("planned_jobs") or []
        for item in items:
            print(f"{item['job_id']}: {item['execution_plan']['status']} -> {item['job_path']}")
            if item["execution_plan"].get("runner_command"):
                print(f"  command: {item['execution_plan']['runner_command']}")
            if item["execution_plan"].get("blocking_reason"):
                print(f"  blocked: {item['execution_plan']['blocking_reason']}")
            if item.get("execution_result"):
                print(f"  result: {item['execution_result'].get('status')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
