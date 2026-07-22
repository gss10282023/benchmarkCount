"""Run controlled Step 8 full-phase raw collection batches."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from evidence_system.cli._common import BootstrapCommand
from evidence_system.cli import webarena_runtime
from evidence_system.contracts.common import load_mapping, normalize_domain, utc_now_iso
from evidence_system.orchestrator.jobs import (
    execute_planned_jobs,
    plan_smoke_jobs,
    resolve_result_namespace,
)


COMMAND = BootstrapCommand(
    name="run_full",
    responsibility="Run controlled full-phase raw collection batches for selected domains and agents.",
    owner_module="evidence_system.orchestrator.jobs",
)

DEFAULT_FULL_MANIFEST = "experiments/experiment_manifest.yaml"
DEFAULT_FULL_SOURCE_BUNDLE = "experiments/evidence_contracts/source_bundles/main_case_units_source_bundle.json"
DEFAULT_FULL_CONTRACTS_DIR = "experiments/evidence_contracts/drafts"
DEFAULT_FULL_AGENTS_CONFIG = "configs/agents.yaml"
DEFAULT_FULL_JOBS_DIR = "results/jobs/full"
WEBARENA_PREFLIGHT_DOMAIN = "webarena_verified"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_system.cli.run_full",
        description=COMMAND.responsibility,
    )
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--domain",
        action="append",
        default=[],
        help="Canonical domain id(s) in the desired execution order. May be repeated.",
    )
    parser.add_argument("--phase", default="full")
    parser.add_argument(
        "--experiment-type",
        default=None,
        help="Experiment type. Omit to infer it from the selected manifest domains; an explicit value must match.",
    )
    parser.add_argument(
        "--case-count",
        type=int,
        default=None,
        help="Number of manifest cases to run per domain. Omit to run every case in the manifest.",
    )
    parser.add_argument(
        "--agent-id",
        action="append",
        default=[],
        help="Explicit agent id(s) to use for every selected domain. Defaults to main_domain_agent_map[domain].",
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--manifest", default=DEFAULT_FULL_MANIFEST)
    parser.add_argument("--source-bundle", default=DEFAULT_FULL_SOURCE_BUNDLE)
    parser.add_argument("--contracts-dir", default=DEFAULT_FULL_CONTRACTS_DIR)
    parser.add_argument("--infra-config", default="configs/infra.yaml")
    parser.add_argument(
        "--execution-lock",
        default=None,
        help=(
            "Pre-run AgentDojo full execution lock. When supplied, raw evidence "
            "is forced into the lock's sealed staging namespace."
        ),
    )
    parser.add_argument("--agents-config", default=DEFAULT_FULL_AGENTS_CONFIG)
    parser.add_argument(
        "--jobs-dir",
        default=None,
        help="Job-plan directory. Defaults to the legacy directory, or an isolated namespace directory when configured.",
    )
    parser.add_argument(
        "--result-namespace",
        "--run-set",
        dest="result_namespace",
        default=None,
        help=(
            "Isolated result run-set. Must match manifest.result_namespace when the manifest declares one. "
            "Results are written below results/namespaces/<value>/ instead of the legacy results/<phase>/ tree."
        ),
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        help="Optional per-batch concurrency cap. The effective value never exceeds infra machine concurrency.",
    )
    parser.add_argument(
        "--rerun-completed",
        action="store_true",
        help="Rerun jobs even when a completed result already passes reuse checks.",
    )
    parser.add_argument(
        "--retry-no-response",
        type=int,
        default=2,
        help="Retry transient model failures such as AgentDojo `No response from model` and AppWorld TimeoutError this many times before stopping.",
    )
    failure_mode = parser.add_mutually_exclusive_group()
    failure_mode.add_argument(
        "--continue-on-error",
        dest="continue_on_error",
        action="store_true",
        help="Record blind job failures and finish all remaining jobs in the batch.",
    )
    failure_mode.add_argument(
        "--fail-fast",
        dest="continue_on_error",
        action="store_false",
        help="Stop at the first job failure.",
    )
    parser.set_defaults(continue_on_error=None)
    parser.add_argument("--plan-only", action="store_true", help="Plan batches and emit the execution order without running them.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.bootstrap_check:
        payload = {
            "name": COMMAND.name,
            "responsibility": COMMAND.responsibility,
            "owner_module": COMMAND.owner_module,
            "status": "ok",
            "formal_logic": "implemented_step_8_controlled_raw_collection",
            "side_effects": "job plans, raw results, logs, and benchmark evidence",
        }
        _emit(payload, as_json=args.json)
        return 0

    if not args.domain:
        parser.error("--domain must be provided at least once")
    if args.execution_lock and not args.plan_only:
        _emit_error(
            "execution-locked AgentDojo plans are permanently non-executable from "
            "run_full; use run_agentdojo_locked_evidence with namespace-init and "
            "immutable stage authorization",
            as_json=args.json,
        )
        return 1

    try:
        manifest = load_mapping(args.manifest)
        result_namespace = resolve_result_namespace(
            manifest=manifest,
            requested=args.result_namespace,
            execution_lock_path=args.execution_lock,
        )
        jobs_dir = args.jobs_dir or _default_jobs_dir(result_namespace)
        domain_batches = _domain_batches(args.domain, explicit_agents=args.agent_id, agents_config_path=args.agents_config)
        experiment_type = _resolve_experiment_type(
            manifest,
            domains=[domain for domain, _ in domain_batches],
            requested=args.experiment_type,
        )
    except Exception as exc:
        _emit_error(str(exc), as_json=args.json)
        return 1

    batch_total = sum(len(agent_ids) for _, agent_ids in domain_batches)
    summaries: list[dict[str, Any]] = []
    preflight_summaries: list[dict[str, Any]] = []
    completed_batches = 0
    preflight_completed: set[str] = set()

    try:
        for domain, agent_ids in domain_batches:
            for agent_id in agent_ids:
                planned = plan_smoke_jobs(
                    domain=domain,
                    phase=args.phase,
                    experiment_type=experiment_type,
                    case_count=args.case_count,
                    agent_ids=[agent_id],
                    seed=args.seed,
                    manifest_path=args.manifest,
                    source_bundle_path=args.source_bundle,
                    contracts_dir=args.contracts_dir,
                    infra_config_path=args.infra_config,
                    agents_config_path=args.agents_config,
                    jobs_dir=jobs_dir,
                    result_namespace=result_namespace,
                    execution_lock_path=args.execution_lock,
                )
                if not planned:
                    raise ValueError(f"{domain}/{agent_id}: manifest selection produced zero case jobs")
                if args.case_count is not None and len(planned) != args.case_count:
                    raise ValueError(
                        f"{domain}/{agent_id}: expected {args.case_count} case jobs, planned {len(planned)}"
                    )
                completed_batches += 1
                batch_summary = {
                    "batch_index": completed_batches,
                    "batch_total": batch_total,
                    "domain": domain,
                    "agent_id": agent_id,
                    "phase": args.phase,
                    "experiment_type": experiment_type,
                    "result_namespace": result_namespace,
                    "jobs_dir": str(jobs_dir),
                    "planned_job_count": len(planned),
                    "first_job_id": planned[0].job["job_id"],
                    "last_job_id": planned[-1].job["job_id"],
                }
                summaries.append(batch_summary)
                if args.plan_only:
                    continue

                if _needs_webarena_preflight(domain, phase=args.phase) and domain not in preflight_completed:
                    preflight_payload = _run_webarena_preflight(args.infra_config, as_json=args.json)
                    preflight_summaries.append(_summarize_webarena_preflight(domain, preflight_payload))
                    if preflight_payload.get("status") != "ok":
                        raise RuntimeError(_webarena_preflight_failure_message(preflight_payload))
                    preflight_completed.add(domain)

                _progress(
                    f"{utc_now_iso()} batch {completed_batches}/{batch_total} start "
                    f"domain={domain} agent={agent_id} jobs={len(planned)} max_workers={args.max_workers or 'infra-default'}",
                    as_json=args.json,
                )

                def _on_progress(item, execution_result, done_count, total_count) -> None:
                    status = execution_result.get("status") or "unknown"
                    _progress(
                        f"{utc_now_iso()} batch {completed_batches}/{batch_total} "
                        f"domain={domain} agent={agent_id} {done_count}/{total_count} "
                        f"job={item.job['job_id']} status={status}",
                        as_json=args.json,
                    )

                executed = execute_planned_jobs(
                    planned,
                    manifest_path=args.manifest,
                    source_bundle_path=args.source_bundle,
                    infra_config_path=args.infra_config,
                    agents_config_path=args.agents_config,
                    max_workers=args.max_workers,
                    progress_callback=_on_progress,
                    fail_fast_on_noncompleted=True,
                    skip_completed=not args.rerun_completed,
                    retry_no_response_attempts=args.retry_no_response,
                    continue_on_error=args.continue_on_error,
                )
                status_counts = Counter(str(item.execution_result.get("status") or "unknown") for item in executed)
                batch_summary["status_counts"] = dict(sorted(status_counts.items()))
                batch_summary["executed_job_count"] = len(executed)
                _progress(
                    f"{utc_now_iso()} batch {completed_batches}/{batch_total} done "
                    f"domain={domain} agent={agent_id} statuses={dict(sorted(status_counts.items()))}",
                    as_json=args.json,
                )
    except Exception as exc:
        payload = {
            "status": "error",
            "message": str(exc),
            "completed_batches": summaries,
            "preflights": preflight_summaries,
        }
        _emit(payload, as_json=args.json)
        return 1

    payload = {
        "status": "planned" if args.plan_only else "executed",
        "phase": args.phase,
        "experiment_type": experiment_type,
        "result_namespace": result_namespace,
        "jobs_dir": str(jobs_dir),
        "domains": [domain for domain, _ in domain_batches],
        "batches": summaries,
        "preflights": preflight_summaries,
    }
    _emit(payload, as_json=args.json)
    return 0


def _default_jobs_dir(result_namespace: str | None) -> str:
    if result_namespace is None:
        return DEFAULT_FULL_JOBS_DIR
    return str(Path(DEFAULT_FULL_JOBS_DIR) / "namespaces" / result_namespace)


def _resolve_experiment_type(
    manifest: dict[str, Any],
    *,
    domains: Sequence[str],
    requested: str | None,
) -> str:
    selected = {normalize_domain(domain) for domain in domains}
    declared_by_domain = {
        normalize_domain(block.get("domain")): str(block.get("experiment_type") or "")
        for block in manifest.get("domains") or []
        if isinstance(block, dict) and normalize_domain(block.get("domain")) in selected
    }
    missing = selected - set(declared_by_domain)
    if missing:
        raise ValueError(f"manifest is missing selected domain(s): {sorted(missing)}")
    declared = set(declared_by_domain.values())
    if "" in declared or len(declared) != 1:
        raise ValueError(
            "selected manifest domains must declare one common experiment_type: "
            f"{declared_by_domain}"
        )
    resolved = next(iter(declared))
    if requested is not None and requested != resolved:
        raise ValueError(
            "requested experiment_type does not match manifest: "
            f"requested={requested!r}, manifest={resolved!r}"
        )
    return resolved


def _domain_batches(
    domains: Sequence[str],
    *,
    explicit_agents: Sequence[str],
    agents_config_path: str,
) -> list[tuple[str, list[str]]]:
    normalized_domains = [normalize_domain(domain) for domain in domains]
    if explicit_agents:
        return [(domain, list(explicit_agents)) for domain in normalized_domains]
    config = load_mapping(agents_config_path)
    agent_map = dict(config.get("main_domain_agent_map") or {})
    batches: list[tuple[str, list[str]]] = []
    for domain in normalized_domains:
        agents = list(agent_map.get(domain) or [])
        if not agents:
            raise ValueError(f"{agents_config_path} has no main_domain_agent_map entry for {domain}")
        batches.append((domain, [str(agent_id) for agent_id in agents]))
    return batches


def _needs_webarena_preflight(domain: str, *, phase: str) -> bool:
    return normalize_domain(domain) == WEBARENA_PREFLIGHT_DOMAIN and phase == "full"


def _run_webarena_preflight(infra_config_path: str, *, as_json: bool) -> dict[str, Any]:
    _progress(
        f"{utc_now_iso()} preflight start domain={WEBARENA_PREFLIGHT_DOMAIN} mode=reset+baseline-check",
        as_json=as_json,
    )
    target = webarena_runtime._load_webarena_target(infra_config_path)
    resolved_sites = webarena_runtime._resolve_sites(target)
    payload = webarena_runtime._baseline_check(
        target,
        [resolved_sites[site] for site in webarena_runtime.DEFAULT_SITES],
        timeout_seconds=webarena_runtime.DEFAULT_TIMEOUT_SECONDS,
        map_timeout_seconds=webarena_runtime.MAP_TIMEOUT_SECONDS,
        with_reset=True,
    )
    failing_sites = [site["site"] for site in payload.get("sites") or [] if not site.get("ok")]
    _progress(
        f"{utc_now_iso()} preflight done domain={WEBARENA_PREFLIGHT_DOMAIN} "
        f"status={payload.get('status') or 'unknown'} failing_sites={','.join(failing_sites) or 'none'}",
        as_json=as_json,
    )
    return payload


def _summarize_webarena_preflight(domain: str, payload: dict[str, Any]) -> dict[str, Any]:
    failing_sites = [str(site.get("site") or "") for site in payload.get("sites") or [] if not site.get("ok")]
    return {
        "domain": domain,
        "status": str(payload.get("status") or "unknown"),
        "with_reset": bool(payload.get("with_reset")),
        "machine_id": payload.get("machine_id"),
        "site_count": len(payload.get("sites") or []),
        "failing_sites": failing_sites,
    }


def _webarena_preflight_failure_message(payload: dict[str, Any]) -> str:
    failures: list[str] = []
    for site in payload.get("sites") or []:
        if site.get("ok"):
            continue
        site_name = str(site.get("site") or "unknown")
        site_failures: list[str] = []
        container = dict(site.get("container") or {})
        homepage = dict(site.get("homepage") or {})
        if not container.get("ok"):
            site_failures.append("container")
        if not homepage.get("ok"):
            detail = str(homepage.get("stderr") or homepage.get("returncode") or "homepage check failed")
            site_failures.append(f"homepage={detail}")
        for sentinel in site.get("sentinels") or []:
            if not sentinel.get("ok"):
                site_failures.append(str(sentinel.get("name") or "sentinel"))
        failures.append(f"{site_name}[{', '.join(site_failures) or 'unknown'}]")
    suffix = "; ".join(failures) if failures else "unknown"
    return f"WebArena preflight failed after reset+baseline-check: {suffix}"


def _emit(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if payload.get("status") == "error":
        print(f"status: {payload['status']}", file=sys.stderr)
        print(f"message: {payload['message']}", file=sys.stderr)
        for batch in payload.get("completed_batches") or []:
            print(
                f"completed_batch: {batch['batch_index']}/{batch['batch_total']} "
                f"{batch['domain']} {batch['agent_id']}",
                file=sys.stderr,
            )
        return
    print(f"status: {payload['status']}")
    print(f"phase: {payload['phase']}")
    print(f"experiment_type: {payload['experiment_type']}")
    print(f"domains: {', '.join(payload['domains'])}")
    for preflight in payload.get("preflights") or []:
        print(
            f"preflight: {preflight['domain']} / {preflight['status']} / "
            f"failing_sites={','.join(preflight['failing_sites']) or 'none'}"
        )
    for batch in payload.get("batches") or []:
        suffix = ""
        if batch.get("status_counts"):
            suffix = f" statuses={batch['status_counts']}"
        print(
            f"batch {batch['batch_index']}/{batch['batch_total']}: "
            f"{batch['domain']} / {batch['agent_id']} / jobs={batch['planned_job_count']}{suffix}"
        )


def _emit_error(message: str, *, as_json: bool) -> None:
    payload = {"status": "error", "message": message}
    _emit(payload, as_json=as_json)


def _progress(message: str, *, as_json: bool) -> None:
    print(message, file=sys.stderr if as_json else sys.stdout, flush=True)


if __name__ == "__main__":
    sys.exit(main())
