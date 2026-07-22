"""Immutable, content-free plans for the two OpenRouter rate-validation rounds.

The first plan is bound only to the provisional policy and its frozen inputs.
The second is bound to the finalized policy plus the immutable measurement and
finalization receipts.  This directionality prevents circular policy/receipt
claims and makes the exact 13-receipt, 192-slot workload machine-verifiable.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any, Mapping, Sequence

from evidence_system.adapters.agentdojo_runtime_control import (
    REQUIRED_MODELS,
    RuntimePolicy,
    RuntimePolicyError,
    build_ramp_stage_workload_from_sources,
    execution_runtime_snapshot,
    load_policy_finalization_receipt,
    load_rate_measurement_receipt,
    load_runtime_policy,
    materialize_disposable_stage_jobs,
    validate_ramp_stage_workload,
)
from evidence_system.contracts.agentdojo_execution_budget import (
    DEFAULT_BUDGET_PLAN,
    EXPECTED_PREFLIGHT_RECORD_SLOTS_PER_ROUND,
    EXPECTED_PREFLIGHT_ROUND_COST_USD,
    EXPECTED_PREFLIGHT_STAGE_RECEIPTS_PER_ROUND,
    verify_budget_plan,
)
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import repo_root, resolve_repo_path
from evidence_system.core.schemas import validate_object


ROUND_PLAN_SCHEMA_VERSION = "agentdojo_openrouter_disposable_round_plan/v1"
ROUND_KINDS = ("exploratory_measurement", "finalized_validation")


def build_disposable_round_plan(
    policy: RuntimePolicy,
    *,
    policy_path: str | Path,
    runtime_infra_path: str | Path,
    agents_config_path: str | Path,
    manifest_path: str | Path,
    source_bundle_path: str | Path,
    result_namespace: str,
    round_kind: str,
    execution_budget_plan_path: str | Path = DEFAULT_BUDGET_PLAN,
    measurement_receipt_path: str | Path | None = None,
    policy_finalization_receipt_path: str | Path | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    if round_kind not in ROUND_KINDS:
        raise RuntimePolicyError("disposable round kind is invalid")
    expected_lifecycle = (
        "provisional" if round_kind == "exploratory_measurement" else "finalized"
    )
    if policy.lifecycle_status != expected_lifecycle:
        raise RuntimePolicyError("round kind and runtime-policy lifecycle differ")
    if round_kind == "exploratory_measurement":
        if policy.runtime_mode != "exploratory_measurement" or policy.formal_execution_allowed:
            raise RuntimePolicyError("measurement plan requires exploratory-only policy")
        expected_suffix = "_measurement_disposable_preflight"
        receipt_scope = "exploratory_measurement"
        if measurement_receipt_path is not None or policy_finalization_receipt_path is not None:
            raise RuntimePolicyError("measurement plan cannot point to future receipts")
    else:
        if policy.runtime_mode != "finalized_validation" or not policy.formal_execution_allowed:
            raise RuntimePolicyError("validation plan requires finalized formal-eligible policy")
        expected_suffix = "_validation_disposable_preflight"
        receipt_scope = "disposable_preflight"
        if measurement_receipt_path is None or policy_finalization_receipt_path is None:
            raise RuntimePolicyError("validation plan requires both bridge receipts")
    if not result_namespace.endswith(expected_suffix) or len(result_namespace) > 128:
        raise RuntimePolicyError("disposable round result namespace is not isolated")

    policy_file = _regular_file(policy_path, "round runtime policy")
    loaded_policy = load_runtime_policy(json.loads(policy_file.read_text(encoding="utf-8")))
    if loaded_policy.raw != policy.raw:
        raise RuntimePolicyError("round policy file differs from supplied policy")
    infra_file = _regular_file(runtime_infra_path, "round runtime infra")
    agents_file = _regular_file(agents_config_path, "round agents config")
    manifest_file = _regular_file(manifest_path, "round manifest")
    source_file = _regular_file(source_bundle_path, "round source bundle")
    budget_file = _regular_file(execution_budget_plan_path, "execution budget plan")
    budget = verify_budget_plan(budget_file)

    bridge: dict[str, Any]
    if round_kind == "exploratory_measurement":
        bridge = {"measurement_receipt": None, "policy_finalization_receipt": None}
    else:
        measurement_file = _regular_file(
            measurement_receipt_path, "measurement aggregate receipt"
        )
        finalization_file = _regular_file(
            policy_finalization_receipt_path, "policy finalization receipt"
        )
        measurement_raw = json.loads(measurement_file.read_text(encoding="utf-8"))
        if not isinstance(measurement_raw, Mapping):
            raise RuntimePolicyError("measurement aggregate is not an object")
        measurement = load_rate_measurement_receipt(
            measurement_file,
            expected_candidate_operational_definition_sha256=str(
                measurement_raw["candidate_runtime_policy"][
                    "operational_definition_sha256"
                ]
            ),
            expected_runtime_infra_file_sha256=sha256_file(infra_file),
            expected_agents_config_file_sha256=sha256_file(agents_file),
        )
        finalization = load_policy_finalization_receipt(finalization_file)
        if (
            finalization["measurement_receipt"]["sha256"]
            != sha256_file(measurement_file)
            or finalization["finalized_runtime_policy"]["semantic_sha256"]
            != policy.semantic_sha256
            or policy.measurement_receipt_sha256 != sha256_file(measurement_file)
            or measurement["candidate_runtime_policy"]["semantic_sha256"]
            == policy.semantic_sha256
        ):
            raise RuntimePolicyError("validation plan bridge is cross-policy or circular")
        bridge = {
            "measurement_receipt": _file_ref(measurement_file),
            "policy_finalization_receipt": _file_ref(finalization_file),
        }

    stage_specs: list[dict[str, Any]] = []
    mixed = build_ramp_stage_workload_from_sources(
        worker_concurrency=4,
        model_ordinal=None,
        manifest_path=manifest_file,
        agents_config_path=agents_file,
        source_bundle_path=source_file,
        result_namespace=result_namespace,
    )
    stage_specs.append(
        _stage_spec(
            ordinal=0,
            workload=mixed,
            receipt_scope=receipt_scope,
            effective_workers=4,
            effective_workers_rule="locked_mixed_canary/v1",
        )
    )
    ordinal = 1
    for locked_workers in policy.ramp_stages:
        for model_ordinal in range(len(REQUIRED_MODELS)):
            workload = build_ramp_stage_workload_from_sources(
                worker_concurrency=locked_workers,
                model_ordinal=model_ordinal,
                manifest_path=manifest_file,
                agents_config_path=agents_file,
                source_bundle_path=source_file,
                result_namespace=result_namespace,
            )
            stage_specs.append(
                _stage_spec(
                    ordinal=ordinal,
                    workload=workload,
                    receipt_scope=receipt_scope,
                    effective_workers=(
                        None
                        if round_kind == "exploratory_measurement"
                        else min(
                            locked_workers,
                            int(
                                policy.per_model_safe_limits[
                                    REQUIRED_MODELS[model_ordinal]
                                ]["concurrent_requests"]
                            ),
                        )
                    ),
                    effective_workers_rule=(
                        "prior_safe_adaptive_hold/v1"
                        if round_kind == "exploratory_measurement"
                        else "min_locked_and_finalized_per_model_safe/v1"
                    ),
                )
            )
            ordinal += 1
    if len(stage_specs) != EXPECTED_PREFLIGHT_STAGE_RECEIPTS_PER_ROUND:
        raise RuntimePolicyError("round plan must contain exactly thirteen stages")
    total_jobs = sum(int(row["planned_jobs"]) for row in stage_specs)
    if total_jobs != EXPECTED_PREFLIGHT_RECORD_SLOTS_PER_ROUND:
        raise RuntimePolicyError("round plan must machine-count exactly 192 slots")
    agent_job_counts = {agent_id: 0 for agent_id in ("Agent A", "Agent B", "Agent C")}
    for stage_spec in stage_specs:
        for materialized in materialize_disposable_stage_jobs(stage_spec["workload"]):
            agent_id = str(materialized["job"].get("agent_id") or "")
            if agent_id not in agent_job_counts:
                raise RuntimePolicyError("round plan materialized an unexpected agent")
            agent_job_counts[agent_id] += 1
    model_job_counts = [
        agent_job_counts[agent_id] for agent_id in ("Agent A", "Agent B", "Agent C")
    ]
    if model_job_counts != [64, 64, 64]:
        raise RuntimePolicyError("round plan model job counts are not exactly 64 each")
    projected = dict(budget["definition"]["preflight_projection"])
    if (
        int(projected["record_slots_per_round"]) != total_jobs
        or float(projected["cost_usd_per_round"])
        != float(EXPECTED_PREFLIGHT_ROUND_COST_USD)
    ):
        raise RuntimePolicyError("round plan execution-budget projection is stale")

    definition = {
        "round_kind": round_kind,
        "receipt_scope": receipt_scope,
        "runtime_policy": {
            **_file_ref(policy_file),
            "semantic_sha256": policy.semantic_sha256,
            "operational_definition_sha256": policy.operational_definition_sha256,
        },
        "runtime_infra": _file_ref(infra_file),
        "agents_config": _file_ref(agents_file),
        "manifest": _file_ref(manifest_file),
        "source_bundle": _file_ref(source_file),
        "execution_budget_plan": _file_ref(budget_file),
        "bridge": bridge,
        "result_namespace": result_namespace,
        "stage_order_algorithm": "mixed_then_stage_major_models_v1",
        "stages": stage_specs,
        "exact_workload": {
            "stage_receipt_count": len(stage_specs),
            "independent_mixed_canary_jobs": int(stage_specs[0]["planned_jobs"]),
            "per_model_ramp_jobs": total_jobs - int(stage_specs[0]["planned_jobs"]),
            "total_record_slots": total_jobs,
            "record_slots_per_model": model_job_counts,
            "projected_cost_usd": float(projected["cost_usd_per_round"]),
            "projection_method": (
                "historical_per_agent_cost_times_machine_counted_64_slots_over_100"
            ),
        },
        "runtime_snapshot": execution_runtime_snapshot(),
        "blind_only": True,
        "contains_evidence_or_labels": False,
    }
    definition_sha256 = sha256_object(definition)
    payload = {
        "schema_version": ROUND_PLAN_SCHEMA_VERSION,
        "status": "locked",
        "created_at": _timestamp(created_at),
        "definition": definition,
        "definition_sha256": definition_sha256,
        # Runtime state must never fall back to the legacy generic
        # runtime/preflight ledgers.  The immutable definition digest derives a
        # destination-absent namespace for this round's DB, locks, ledgers and
        # receipts; aggregate builders subsequently require these exact paths.
        "artifact_namespace": _artifact_namespace(
            definition_sha256=definition_sha256,
            round_kind=round_kind,
            stages=stage_specs,
        ),
    }
    validate_object("agentdojo_openrouter_disposable_round_plan", payload)
    validate_disposable_round_plan_payload(payload)
    return payload


def load_disposable_round_plan(path: str | Path) -> dict[str, Any]:
    plan_file = _regular_file(path, "disposable round plan")
    raw = json.loads(plan_file.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise RuntimePolicyError("disposable round plan is not an object")
    payload = dict(raw)
    validate_object("agentdojo_openrouter_disposable_round_plan", payload)
    validate_disposable_round_plan_payload(payload, plan_path=plan_file)
    definition = dict(payload["definition"])
    policy_ref = dict(definition["runtime_policy"])
    policy_file = _regular_file(policy_ref["path"], "round policy")
    policy = load_runtime_policy(
        json.loads(policy_file.read_text(encoding="utf-8")),
        expected_semantic_sha256=str(policy_ref["semantic_sha256"]),
    )
    bridge = dict(definition["bridge"])
    rebuilt = build_disposable_round_plan(
        policy,
        policy_path=policy_file,
        runtime_infra_path=definition["runtime_infra"]["path"],
        agents_config_path=definition["agents_config"]["path"],
        manifest_path=definition["manifest"]["path"],
        source_bundle_path=definition["source_bundle"]["path"],
        result_namespace=str(definition["result_namespace"]),
        round_kind=str(definition["round_kind"]),
        execution_budget_plan_path=definition["execution_budget_plan"]["path"],
        measurement_receipt_path=(
            None
            if bridge["measurement_receipt"] is None
            else bridge["measurement_receipt"]["path"]
        ),
        policy_finalization_receipt_path=(
            None
            if bridge["policy_finalization_receipt"] is None
            else bridge["policy_finalization_receipt"]["path"]
        ),
        created_at=str(payload["created_at"]),
    )
    if payload != rebuilt:
        raise RuntimePolicyError("disposable round plan differs from current sources")
    return payload


def validate_disposable_round_plan_payload(
    payload: Mapping[str, Any], *, plan_path: Path | None = None
) -> None:
    definition = payload.get("definition")
    if not isinstance(definition, Mapping) or payload.get(
        "definition_sha256"
    ) != sha256_object(definition):
        raise RuntimePolicyError("disposable round definition hash mismatch")
    if definition.get("stage_order_algorithm") != "mixed_then_stage_major_models_v1":
        raise RuntimePolicyError("disposable round stage-order algorithm differs")
    stages = definition.get("stages")
    if not isinstance(stages, list) or len(stages) != 13:
        raise RuntimePolicyError("disposable round requires thirteen ordered stages")
    expected_order = [("global_mixed_canary", 4, None)] + [
        ("per_model_ramp", stage, model)
        for stage in (4, 8, 16, 32)
        for model in range(3)
    ]
    total = 0
    for ordinal, (row, expected) in enumerate(zip(stages, expected_order, strict=True)):
        if not isinstance(row, Mapping) or int(row.get("ordinal", -1)) != ordinal:
            raise RuntimePolicyError("disposable round stage order is invalid")
        workload = validate_ramp_stage_workload(dict(row.get("workload") or {}))
        generation = workload["generation"]
        observed = (
            generation["workload_kind"],
            int(workload["worker_concurrency"]),
            generation["model_ordinal"],
        )
        if observed != expected or row.get("workload_sha256") != sha256_object(workload):
            raise RuntimePolicyError("disposable round stage identity/hash differs")
        if int(row.get("planned_jobs", 0)) != int(workload["planned_job_count"]):
            raise RuntimePolicyError("disposable round planned-job count differs")
        expected_effective = row.get("effective_workers")
        rule = row.get("effective_workers_rule")
        if ordinal == 0:
            if expected_effective != 4 or rule != "locked_mixed_canary/v1":
                raise RuntimePolicyError("mixed canary effective-worker rule differs")
        elif definition.get("round_kind") == "exploratory_measurement":
            if expected_effective is not None or rule != "prior_safe_adaptive_hold/v1":
                raise RuntimePolicyError("measurement adaptive hold rule differs")
        else:
            if (
                not isinstance(expected_effective, int)
                or expected_effective not in (4, 8, 16, 32)
                or expected_effective > int(row["locked_workers"])
                or rule != "min_locked_and_finalized_per_model_safe/v1"
            ):
                raise RuntimePolicyError("validation effective-worker rule differs")
        materialize_disposable_stage_jobs(workload)
        total += int(workload["planned_job_count"])
    if total != 192 or dict(definition.get("exact_workload") or {}).get(
        "total_record_slots"
    ) != 192:
        raise RuntimePolicyError("disposable round exact workload is not 192")
    expected_artifacts = _artifact_namespace(
        definition_sha256=str(payload["definition_sha256"]),
        round_kind=str(definition.get("round_kind") or ""),
        stages=stages,
    )
    if payload.get("artifact_namespace") != expected_artifacts:
        raise RuntimePolicyError("disposable round artifact namespace is not SHA-derived")
    bridge = dict(definition.get("bridge") or {})
    if definition.get("round_kind") == "exploratory_measurement":
        if any(bridge.get(key) is not None for key in bridge):
            raise RuntimePolicyError("measurement plan contains a future/circular bridge")
    else:
        if any(bridge.get(key) is None for key in bridge):
            raise RuntimePolicyError("validation plan bridge is incomplete")
    for field in (
        "runtime_policy",
        "runtime_infra",
        "agents_config",
        "manifest",
        "source_bundle",
        "execution_budget_plan",
    ):
        ref = dict(definition[field])
        current = _regular_file(ref["path"], field)
        if ref["sha256"] != sha256_file(current):
            raise RuntimePolicyError(f"disposable round {field} is stale")
        if plan_path is not None and current == plan_path:
            raise RuntimePolicyError("disposable round plan contains a self-reference")


def write_disposable_round_plan_once(
    path: str | Path, payload: Mapping[str, Any]
) -> Path:
    validate_object("agentdojo_openrouter_disposable_round_plan", dict(payload))
    validate_disposable_round_plan_payload(payload)
    output = resolve_repo_path(path)
    encoded = json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    if output.exists() or output.is_symlink():
        existing = _regular_file(output, "existing round plan")
        if existing.read_text(encoding="utf-8") != encoded:
            raise RuntimePolicyError("round plan already exists and differs")
        # Identical bytes are accepted only after all source/currentness
        # checks have been rerun; byte equality alone is not a lock gate.
        if load_disposable_round_plan(existing) != dict(payload):
            raise RuntimePolicyError("existing round plan failed currentness validation")
        return output
    artifact_root = resolve_repo_path(payload["artifact_namespace"]["root"])
    if artifact_root.exists() or artifact_root.is_symlink():
        raise RuntimePolicyError(
            "round artifact namespace must be absent at initial plan publication"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    _assert_directory_chain_no_symlinks(output.parent)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, output)
        except FileExistsError:
            existing = _regular_file(output, "racing round plan")
            if existing.read_text(encoding="utf-8") != encoded:
                raise RuntimePolicyError("round plan won a publication race and differs")
            if load_disposable_round_plan(existing) != dict(payload):
                raise RuntimePolicyError("racing round plan failed currentness validation")
        directory_descriptor = os.open(
            output.parent,
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return output


def _stage_spec(
    *,
    ordinal: int,
    workload: Mapping[str, Any],
    receipt_scope: str,
    effective_workers: int | None,
    effective_workers_rule: str,
) -> dict[str, Any]:
    normalized = validate_ramp_stage_workload(dict(workload))
    materialize_disposable_stage_jobs(normalized)
    generation = normalized["generation"]
    return {
        "ordinal": ordinal,
        "workload_kind": generation["workload_kind"],
        "locked_workers": int(normalized["worker_concurrency"]),
        "effective_workers": effective_workers,
        "effective_workers_rule": effective_workers_rule,
        "model_ordinal": generation["model_ordinal"],
        "receipt_scope": receipt_scope,
        "planned_jobs": int(normalized["planned_job_count"]),
        "workload": normalized,
        "workload_sha256": sha256_object(normalized),
    }


def _artifact_namespace(
    *,
    definition_sha256: str,
    round_kind: str,
    stages: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if round_kind not in ROUND_KINDS:
        raise RuntimePolicyError("round artifact namespace kind is invalid")
    digest = str(definition_sha256)
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise RuntimePolicyError("round artifact namespace digest is invalid")
    root = Path(
        "experiments/agentdojo_full_v1.2.2_direct/runtime/preflight/rounds"
    ) / digest
    stage_rows: list[dict[str, Any]] = []
    for row in stages:
        ordinal = int(row["ordinal"])
        stage_root = root / f"stage-{ordinal:02d}"
        stage_rows.append(
            {
                "ordinal": ordinal,
                "root": stage_root.as_posix(),
                "blind_health_ledger": (stage_root / "blind_health.jsonl").as_posix(),
                "resource_ledger": (stage_root / "resource_health.jsonl").as_posix(),
                "stage_receipt": (stage_root / "stage_receipt.json").as_posix(),
            }
        )
    return {
        "derivation": "definition_sha256_full_hex/v1",
        "root": root.as_posix(),
        "must_be_absent_at_initial_publication": True,
        "limiter_database": (root / "limiter.sqlite3").as_posix(),
        "controller_lifecycle_lock": (
            root / "controller_lifecycle.lock"
        ).as_posix(),
        "pre_credential_receipt": (root / "credential_pre.json").as_posix(),
        "pre_credential_health_ledger": (
            root / "credential_pre_health.jsonl"
        ).as_posix(),
        "post_credential_receipt": (
            None
            if round_kind == "exploratory_measurement"
            else (root / "credential_post.json").as_posix()
        ),
        "post_credential_health_ledger": (
            None
            if round_kind == "exploratory_measurement"
            else (root / "credential_post_health.jsonl").as_posix()
        ),
        "aggregate_receipt": (
            root
            / (
                "measurement_aggregate.json"
                if round_kind == "exploratory_measurement"
                else "validation_aggregate.json"
            )
        ).as_posix(),
        "stages": stage_rows,
    }


def _regular_file(path: str | Path | None, label: str) -> Path:
    if path is None:
        raise RuntimePolicyError(f"{label} is missing")
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = resolve_repo_path(candidate)
    candidate = candidate.absolute()
    try:
        file_stat = os.lstat(candidate)
    except FileNotFoundError as exc:
        raise RuntimePolicyError(f"{label} is missing") from exc
    if (
        stat.S_ISLNK(file_stat.st_mode)
        or not stat.S_ISREG(file_stat.st_mode)
        or file_stat.st_nlink != 1
    ):
        raise RuntimePolicyError(f"{label} must be a regular non-symlink file")
    try:
        relative_parent = candidate.parent.relative_to(repo_root().absolute())
    except ValueError:
        chain = [candidate.parent]
    else:
        chain = [repo_root().absolute()]
        current = repo_root().absolute()
        for part in relative_parent.parts:
            current = current / part
            chain.append(current)
    for directory in chain:
        directory_stat = os.lstat(directory)
        if stat.S_ISLNK(directory_stat.st_mode) or not stat.S_ISDIR(
            directory_stat.st_mode
        ):
            raise RuntimePolicyError(f"{label} ancestor contains a symlink")
    return candidate


def _assert_directory_chain_no_symlinks(directory: Path) -> None:
    root = repo_root().absolute()
    candidate = directory.absolute()
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise RuntimePolicyError("round-plan output must remain under repository root") from exc
    current = root
    for part in relative.parts:
        current = current / part
        info = os.lstat(current)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise RuntimePolicyError("round-plan output ancestor contains a symlink")


def _file_ref(path: Path) -> dict[str, str]:
    try:
        portable = path.relative_to(repo_root().resolve()).as_posix()
    except ValueError:
        portable = str(path)
    return {"path": portable, "sha256": sha256_file(path)}


def _timestamp(value: str | None) -> str:
    text = value or datetime.now(timezone.utc).isoformat()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimePolicyError("round plan created_at is invalid") from exc
    if parsed.tzinfo is None:
        raise RuntimePolicyError("round plan created_at must have a timezone")
    return text
