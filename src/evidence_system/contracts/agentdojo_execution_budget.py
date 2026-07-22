"""Content-free historical cost projection for AgentDojo full execution.

The plan deliberately reads only the already-redacted LLM-call accounting
fields needed for capacity planning.  It never copies response metadata,
prompts, trajectories, evaluator labels, or native scores into provenance.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

from evidence_system.contracts.common import ContractLifecycleError, load_mapping
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import repo_root, resolve_repo_path
from evidence_system.core.schemas import validate_object


BUDGET_PLAN_SCHEMA_VERSION = "agentdojo_execution_budget_plan/v1"
BUDGET_PLAN_ID = "agentdojo_full_v1.2.2_direct_execution_budget"
DEFAULT_HISTORICAL_ROOT = Path("results/full/agentdojo")
DEFAULT_BUDGET_PLAN = Path(
    "experiments/agentdojo_full_v1.2.2_direct/provenance/execution_budget_plan.json"
)
EXPECTED_HISTORICAL_CASES = 100
EXPECTED_HISTORICAL_RECORD_SLOTS = 300
EXPECTED_TARGET_CASES = 949
EXPECTED_TARGET_RECORD_SLOTS = 2_847
EXPECTED_AGENTS = ("Agent A", "Agent B", "Agent C")
EXPECTED_PROJECTED_COST_USD = Decimal("527.18")
EXPECTED_CREDIT_FLOOR_USD = Decimal("650.00")
EXPECTED_MAXIMUM_COST_CAP_USD = Decimal("650.00")
EXPECTED_PREFLIGHT_PER_MODEL_RAMP_SLOTS_PER_AGENT_PER_ROUND = 60
EXPECTED_PREFLIGHT_MIXED_SLOTS_PER_AGENT_PER_ROUND = 4
EXPECTED_PREFLIGHT_SLOTS_PER_AGENT_PER_ROUND = 64
EXPECTED_PREFLIGHT_RECORD_SLOTS_PER_ROUND = 192
EXPECTED_PREFLIGHT_STAGE_RECEIPTS_PER_ROUND = 13
EXPECTED_PREFLIGHT_ROUNDS = 2
EXPECTED_PREFLIGHT_ROUND_COST_USD = Decimal("35.553")
EXPECTED_PREFLIGHT_TWO_ROUND_COST_USD = Decimal("71.106")
EXPECTED_PREFLIGHT_RESERVE_USD = Decimal("150.00")
EXPECTED_PREFLIGHT_MARGIN_USD = Decimal("78.894")
EXPECTED_RECOMMENDED_INITIAL_CREDIT_USD = Decimal("800.00")


def build_budget_definition(
    *, historical_root: str | Path = DEFAULT_HISTORICAL_ROOT
) -> dict[str, Any]:
    """Aggregate accounting metadata and extrapolate 100 cases to 949."""

    root = resolve_repo_path(historical_root)
    if root.is_symlink() or not root.is_dir():
        raise ContractLifecycleError(
            f"historical AgentDojo result root is missing, not a directory, or symlinked: {root}"
        )
    logs = sorted(root.glob("*/adapter/llm_calls/calls.jsonl"))
    if len(logs) != EXPECTED_HISTORICAL_RECORD_SLOTS:
        raise ContractLifecycleError(
            "historical accounting source must contain exactly "
            f"{EXPECTED_HISTORICAL_RECORD_SLOTS} calls.jsonl files; found {len(logs)}"
        )
    if any(path.is_symlink() or not path.is_file() for path in logs):
        raise ContractLifecycleError("historical accounting source contains a symlink or non-file")

    totals: dict[str, dict[str, Any]] = {
        agent: {
            "record_slots": set(),
            "case_unit_ids": set(),
            "calls": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cost_usd": Decimal("0"),
        }
        for agent in EXPECTED_AGENTS
    }
    all_slots: set[str] = set()
    all_cases: set[str] = set()
    source_entries: list[dict[str, str]] = []

    for log_path in logs:
        relative = log_path.relative_to(root).as_posix()
        source_entries.append({"path": relative, "sha256": sha256_file(log_path)})
        expected_identity: tuple[str, str, str] | None = None
        line_count = 0
        for line_number, line in enumerate(
            log_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            line_count += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ContractLifecycleError(
                    f"invalid historical accounting JSON at {relative}:{line_number}"
                ) from exc
            if not isinstance(record, Mapping):
                raise ContractLifecycleError(
                    f"historical accounting row is not an object at {relative}:{line_number}"
                )
            agent = str(record.get("agent_id_or_role") or "")
            slot = str(record.get("record_slot_id") or "")
            case_id = str(record.get("case_unit_id") or "")
            if agent not in totals or not slot or not case_id:
                raise ContractLifecycleError(
                    f"historical accounting identity is invalid at {relative}:{line_number}"
                )
            identity = (agent, slot, case_id)
            if expected_identity is None:
                expected_identity = identity
            elif identity != expected_identity:
                raise ContractLifecycleError(
                    f"historical calls log mixes record-slot identities: {relative}"
                )

            usage = record.get("token_usage")
            cost = record.get("cost")
            if not isinstance(usage, Mapping) or not isinstance(cost, Mapping):
                raise ContractLifecycleError(
                    f"historical accounting metadata is missing at {relative}:{line_number}"
                )
            prompt = _nonnegative_int(usage, "prompt_tokens", relative, line_number)
            completion = _nonnegative_int(
                usage, "completion_tokens", relative, line_number
            )
            total = _nonnegative_int(usage, "total_tokens", relative, line_number)
            if total != prompt + completion:
                raise ContractLifecycleError(
                    f"historical total_tokens mismatch at {relative}:{line_number}"
                )
            raw_cost = cost.get("total_cost_usd")
            if isinstance(raw_cost, bool) or not isinstance(raw_cost, (int, float)):
                raise ContractLifecycleError(
                    f"historical provider cost is missing at {relative}:{line_number}"
                )
            decimal_cost = Decimal(str(raw_cost))
            if decimal_cost < 0:
                raise ContractLifecycleError(
                    f"historical provider cost is negative at {relative}:{line_number}"
                )
            bucket = totals[agent]
            bucket["calls"] += 1
            bucket["prompt_tokens"] += prompt
            bucket["completion_tokens"] += completion
            bucket["total_tokens"] += total
            bucket["cost_usd"] += decimal_cost

        if line_count == 0 or expected_identity is None:
            raise ContractLifecycleError(f"historical calls log is empty: {relative}")
        agent, slot, case_id = expected_identity
        if slot in all_slots:
            raise ContractLifecycleError(f"duplicate historical record slot: {slot}")
        all_slots.add(slot)
        all_cases.add(case_id)
        totals[agent]["record_slots"].add(slot)
        totals[agent]["case_unit_ids"].add(case_id)

    if len(all_slots) != EXPECTED_HISTORICAL_RECORD_SLOTS:
        raise ContractLifecycleError("historical record-slot denominator mismatch")
    if len(all_cases) != EXPECTED_HISTORICAL_CASES:
        raise ContractLifecycleError(
            f"historical case denominator must be {EXPECTED_HISTORICAL_CASES}; found {len(all_cases)}"
        )
    for agent in EXPECTED_AGENTS:
        if len(totals[agent]["record_slots"]) != EXPECTED_HISTORICAL_CASES:
            raise ContractLifecycleError(f"{agent} does not cover all historical cases")
        if totals[agent]["case_unit_ids"] != all_cases:
            raise ContractLifecycleError(f"{agent} historical case set differs")

    factor = Decimal(EXPECTED_TARGET_CASES) / Decimal(EXPECTED_HISTORICAL_CASES)
    observed_agents: dict[str, Any] = {}
    projected_agents: dict[str, Any] = {}
    observed_total = defaultdict(int)
    observed_cost = Decimal("0")
    projected_cost_unrounded = Decimal("0")
    for agent in EXPECTED_AGENTS:
        bucket = totals[agent]
        observed = {
            "record_slots": len(bucket["record_slots"]),
            "calls": int(bucket["calls"]),
            "prompt_tokens": int(bucket["prompt_tokens"]),
            "completion_tokens": int(bucket["completion_tokens"]),
            "total_tokens": int(bucket["total_tokens"]),
            "cost_usd": _decimal_number(bucket["cost_usd"], places=6),
        }
        observed_agents[agent] = observed
        for key in ("calls", "prompt_tokens", "completion_tokens", "total_tokens"):
            observed_total[key] += observed[key]
        observed_cost += bucket["cost_usd"]
        agent_projected_cost = bucket["cost_usd"] * factor
        projected_cost_unrounded += agent_projected_cost
        projected_agents[agent] = {
            "record_slots": EXPECTED_TARGET_CASES,
            "calls": _ceiling_int(Decimal(observed["calls"]) * factor),
            "prompt_tokens": _ceiling_int(Decimal(observed["prompt_tokens"]) * factor),
            "completion_tokens": _ceiling_int(
                Decimal(observed["completion_tokens"]) * factor
            ),
            "total_tokens": _ceiling_int(
                Decimal(observed["total_tokens"]) * factor
            ),
            "cost_usd_unrounded": _decimal_number(agent_projected_cost, places=6),
        }

    projected_cost = projected_cost_unrounded.quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    if projected_cost != EXPECTED_PROJECTED_COST_USD:
        raise ContractLifecycleError(
            "historical accounting projection drifted from the reviewed $527.18 total: "
            f"observed={projected_cost}"
        )
    projected_totals = {
        key: sum(int(projected_agents[agent][key]) for agent in EXPECTED_AGENTS)
        for key in ("calls", "prompt_tokens", "completion_tokens", "total_tokens")
    }
    preflight_agent_costs: dict[str, float] = {}
    preflight_round_cost_unrounded = Decimal("0")
    for agent in EXPECTED_AGENTS:
        observed_agent_cost = Decimal(str(observed_agents[agent]["cost_usd"]))
        agent_cost = (
            observed_agent_cost
            * Decimal(EXPECTED_PREFLIGHT_SLOTS_PER_AGENT_PER_ROUND)
            / Decimal(EXPECTED_HISTORICAL_CASES)
        )
        preflight_round_cost_unrounded += agent_cost
        preflight_agent_costs[agent] = _decimal_number(agent_cost, places=3)
    preflight_round_cost = preflight_round_cost_unrounded.quantize(
        Decimal("0.001"), rounding=ROUND_HALF_UP
    )
    preflight_two_round_cost = (
        preflight_round_cost_unrounded * Decimal(EXPECTED_PREFLIGHT_ROUNDS)
    ).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    if preflight_round_cost != EXPECTED_PREFLIGHT_ROUND_COST_USD:
        raise ContractLifecycleError(
            "historical accounting preflight projection drifted from $35.553 per round: "
            f"observed={preflight_round_cost}"
        )
    if preflight_two_round_cost != EXPECTED_PREFLIGHT_TWO_ROUND_COST_USD:
        raise ContractLifecycleError(
            "historical accounting preflight projection drifted from $71.106 for two rounds: "
            f"observed={preflight_two_round_cost}"
        )

    return {
        "historical_observation": {
            "case_units": EXPECTED_HISTORICAL_CASES,
            "record_slots": EXPECTED_HISTORICAL_RECORD_SLOTS,
            "agents": observed_agents,
            "total": {
                **{key: int(value) for key, value in observed_total.items()},
                "cost_usd": _decimal_number(observed_cost, places=6),
            },
        },
        "full_projection": {
            "case_units": EXPECTED_TARGET_CASES,
            "record_slots": EXPECTED_TARGET_RECORD_SLOTS,
            "agents": projected_agents,
            "total": {
                **projected_totals,
                "cost_usd_unrounded": _decimal_number(
                    projected_cost_unrounded, places=6
                ),
                "cost_usd": float(projected_cost),
            },
        },
        "budget_guard": {
            "projected_cost_usd": float(EXPECTED_PROJECTED_COST_USD),
            "credit_floor_usd": float(EXPECTED_CREDIT_FLOOR_USD),
            "maximum_run_cost_usd": float(EXPECTED_MAXIMUM_COST_CAP_USD),
            "headroom_usd": float(
                EXPECTED_MAXIMUM_COST_CAP_USD - EXPECTED_PROJECTED_COST_USD
            ),
            "cost_cap_action": "block_new_requests",
        },
        "preflight_projection": {
            "concurrency_stages_per_agent": [4, 8, 16, 32],
            "model_concurrency_substage_count_per_round": 12,
            "stage_receipt_count_per_round": (
                EXPECTED_PREFLIGHT_STAGE_RECEIPTS_PER_ROUND
            ),
            "per_model_ramp_slots_per_agent_per_round": (
                EXPECTED_PREFLIGHT_PER_MODEL_RAMP_SLOTS_PER_AGENT_PER_ROUND
            ),
            "independent_mixed_canary_slots_per_agent_per_round": (
                EXPECTED_PREFLIGHT_MIXED_SLOTS_PER_AGENT_PER_ROUND
            ),
            "independent_mixed_canary_record_slots_per_round": 12,
            "slots_per_agent_per_round": EXPECTED_PREFLIGHT_SLOTS_PER_AGENT_PER_ROUND,
            "record_slots_per_round": EXPECTED_PREFLIGHT_RECORD_SLOTS_PER_ROUND,
            "rounds": [
                "measurement",
                "final_hash_validation",
            ],
            "round_count": EXPECTED_PREFLIGHT_ROUNDS,
            "agent_cost_usd_per_round": preflight_agent_costs,
            "cost_usd_per_round": float(preflight_round_cost),
            "two_round_cost_usd": float(preflight_two_round_cost),
            "credential_and_mixed_canary_margin_usd": float(
                EXPECTED_PREFLIGHT_MARGIN_USD
            ),
            "preflight_reserve_usd": float(EXPECTED_PREFLIGHT_RESERVE_USD),
            "recommended_initial_credit_usd": float(
                EXPECTED_RECOMMENDED_INITIAL_CREDIT_USD
            ),
            "required_post_ramp_credit_usd": float(EXPECTED_CREDIT_FLOOR_USD),
            "formal_maximum_run_cost_usd": float(EXPECTED_MAXIMUM_COST_CAP_USD),
            "credit_gate": (
                "require_initial_credit_at_least_800_and_after_disposable_ramp_"
                "require_remaining_credit_at_least_650"
            ),
        },
        "methodology": {
            "method": "case_linear_extrapolation_from_existing_100_case_run",
            "factor_numerator": EXPECTED_TARGET_CASES,
            "factor_denominator": EXPECTED_HISTORICAL_CASES,
            "factor": float(factor),
            "calls_and_tokens_rounding": "ceiling_per_agent",
            "cost_rounding": "provider_reported_cost_scaled_then_half_up_to_usd_cent",
            "assumption": (
                "The prior stratified 100-case run is used only as an empirical "
                "per-agent accounting-rate estimate; formal evidence labels and "
                "response content are excluded."
            ),
        },
        "source": {
            "path": _repo_relative(root),
            "scope": "*/adapter/llm_calls/calls.jsonl accounting fields only",
            "calls_log_file_count": len(logs),
            "calls_log_set_sha256": sha256_object(source_entries),
            "source_tree_sha256": sha256_object(source_entries),
            "response_content_included": False,
            "prompt_content_included": False,
            "trajectory_content_included": False,
            "evaluator_labels_included": False,
            "secret_material_included": False,
        },
    }


def publish_budget_plan(
    *,
    historical_root: str | Path = DEFAULT_HISTORICAL_ROOT,
    output_path: str | Path = DEFAULT_BUDGET_PLAN,
    created_at: str | None = None,
) -> Path:
    definition = build_budget_definition(historical_root=historical_root)
    timestamp = created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    _require_aware_timestamp(timestamp)
    payload = {
        "schema_version": BUDGET_PLAN_SCHEMA_VERSION,
        "plan_id": BUDGET_PLAN_ID,
        "status": "locked",
        "created_at": timestamp,
        "definition": definition,
        "definition_sha256": sha256_object(definition),
    }
    validate_budget_plan_payload(payload)
    output = resolve_repo_path(output_path)
    if output.exists():
        existing = load_mapping(output)
        validate_budget_plan_payload(existing)
        if existing.get("definition") != definition:
            raise ContractLifecycleError(
                "execution budget plan already exists and its accounting source drifted"
            )
        return output
    _atomic_write_json(output, payload)
    return output


def verify_budget_plan(
    path: str | Path = DEFAULT_BUDGET_PLAN,
) -> dict[str, Any]:
    plan_path = resolve_repo_path(path)
    if plan_path.is_symlink() or not plan_path.is_file():
        raise ContractLifecycleError(f"execution budget plan is missing or symlinked: {plan_path}")
    payload = load_mapping(plan_path)
    validate_budget_plan_payload(payload)
    definition = dict(payload["definition"])
    source = dict(definition["source"])
    recomputed = build_budget_definition(historical_root=str(source["path"]))
    if recomputed != definition:
        raise ContractLifecycleError("execution budget plan currentness verification failed")
    return payload


def validate_budget_plan_payload(payload: Mapping[str, Any]) -> None:
    report = validate_object(
        "agentdojo_execution_budget_plan", dict(payload), raise_on_error=False
    )
    if not report.ok:
        raise ContractLifecycleError(
            f"execution budget plan schema validation failed: {report.to_dict()}"
        )
    definition = payload.get("definition")
    if not isinstance(definition, Mapping):
        raise ContractLifecycleError("execution budget plan definition is missing")
    if payload.get("definition_sha256") != sha256_object(definition):
        raise ContractLifecycleError("execution budget plan definition hash mismatch")
    _require_aware_timestamp(str(payload.get("created_at") or ""))
    guard = dict(definition.get("budget_guard") or {})
    if Decimal(str(guard.get("projected_cost_usd"))) != EXPECTED_PROJECTED_COST_USD:
        raise ContractLifecycleError("execution budget projected total must be $527.18")
    if Decimal(str(guard.get("credit_floor_usd"))) != EXPECTED_CREDIT_FLOOR_USD:
        raise ContractLifecycleError("execution budget credit floor must be $650")
    if Decimal(str(guard.get("maximum_run_cost_usd"))) != EXPECTED_MAXIMUM_COST_CAP_USD:
        raise ContractLifecycleError("execution budget maximum cost cap must be $650")
    preflight = dict(definition.get("preflight_projection") or {})
    if Decimal(str(preflight.get("cost_usd_per_round"))) != EXPECTED_PREFLIGHT_ROUND_COST_USD:
        raise ContractLifecycleError("execution budget preflight round cost must be $35.553")
    if Decimal(str(preflight.get("two_round_cost_usd"))) != EXPECTED_PREFLIGHT_TWO_ROUND_COST_USD:
        raise ContractLifecycleError("execution budget two-round preflight cost must be $71.106")
    if int(preflight.get("record_slots_per_round") or 0) != EXPECTED_PREFLIGHT_RECORD_SLOTS_PER_ROUND:
        raise ContractLifecycleError("execution budget must machine-count 192 slots per round")
    if int(preflight.get("stage_receipt_count_per_round") or 0) != EXPECTED_PREFLIGHT_STAGE_RECEIPTS_PER_ROUND:
        raise ContractLifecycleError("execution budget must bind thirteen receipts per round")
    if Decimal(str(preflight.get("preflight_reserve_usd"))) != EXPECTED_PREFLIGHT_RESERVE_USD:
        raise ContractLifecycleError("execution budget preflight reserve must be $150")
    if Decimal(str(preflight.get("recommended_initial_credit_usd"))) != EXPECTED_RECOMMENDED_INITIAL_CREDIT_USD:
        raise ContractLifecycleError("execution budget recommended initial credit must be $800")
    if Decimal(str(preflight.get("required_post_ramp_credit_usd"))) != EXPECTED_CREDIT_FLOOR_USD:
        raise ContractLifecycleError("execution budget post-ramp credit floor must be $650")
    source = dict(definition.get("source") or {})
    for forbidden in (
        "response_content_included",
        "prompt_content_included",
        "trajectory_content_included",
        "evaluator_labels_included",
        "secret_material_included",
    ):
        if source.get(forbidden) is not False:
            raise ContractLifecycleError(
                f"execution budget metadata-only assertion failed: {forbidden}"
            )


def _nonnegative_int(
    value: Mapping[str, Any], field: str, relative: str, line_number: int
) -> int:
    raw = value.get(field)
    if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
        raise ContractLifecycleError(
            f"historical {field} is invalid at {relative}:{line_number}"
        )
    return raw


def _ceiling_int(value: Decimal) -> int:
    return int(value.to_integral_value(rounding=ROUND_CEILING))


def _decimal_number(value: Decimal, *, places: int) -> float:
    quantum = Decimal(1).scaleb(-places)
    return float(value.quantize(quantum, rounding=ROUND_HALF_UP))


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root().resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _require_aware_timestamp(value: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractLifecycleError("budget plan created_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ContractLifecycleError("budget plan created_at must include a timezone")


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=True, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
