"""Create fail-closed OpenRouter credential and disposable-ramp receipts."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import stat
import tempfile
from typing import Any, Callable, Mapping, Sequence
import urllib.error
import urllib.parse
import urllib.request

from evidence_system.adapters.agentdojo_runtime_control import (
    BlindHealthLedger,
    OpenRouterAuthLifecycleLock,
    REQUIRED_MODELS,
    RuntimePolicyError,
    build_credential_probe_receipt,
    build_disposable_ramp_receipt,
    build_policy_finalization_receipt,
    build_rate_measurement_receipt,
    build_ramp_stage_receipt,
    derive_finalized_runtime_policy,
    load_credential_probe_receipt,
    load_disposable_ramp_receipt,
    load_policy_finalization_receipt,
    load_rate_measurement_receipt,
    load_ramp_stage_receipt,
    load_runtime_policy,
    openrouter_key_fingerprint,
    required_credit_floor,
)
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import repo_root, resolve_repo_path
from evidence_system.contracts.agentdojo_execution_budget import DEFAULT_BUDGET_PLAN
from evidence_system.contracts.agentdojo_rate_lifecycle import (
    build_disposable_round_plan,
    load_disposable_round_plan,
    write_disposable_round_plan_once,
)


EXPERIMENT_RUNTIME = Path("experiments/agentdojo_full_v1.2.2_direct/runtime")
DEFAULT_POLICY = EXPERIMENT_RUNTIME / "openrouter_runtime_policy.json"
DEFAULT_INFRA = EXPERIMENT_RUNTIME / "infra.vultr.yaml"
DEFAULT_CREDENTIAL_RECEIPT = (
    EXPERIMENT_RUNTIME / "preflight/credential_probe_receipt.json"
)
DEFAULT_RAMP_RECEIPT = EXPERIMENT_RUNTIME / "preflight/disposable_ramp_receipt.json"
DEFAULT_BLIND_HEALTH = EXPERIMENT_RUNTIME / "preflight/blind_health.jsonl"
KEY_URL = "https://openrouter.ai/api/v1/key"
MODELS_URL = "https://openrouter.ai/api/v1/models"
CREDITS_URL = "https://openrouter.ai/api/v1/credits"
KEYS_URL = "https://openrouter.ai/api/v1/keys"
KEYS_PAGE_SIZE = 100
KEYS_MAX_PAGES = 100


class ProbeHTTPError(RuntimeError):
    def __init__(self, status: int) -> None:
        self.status = int(status)
        super().__init__(f"OpenRouter credential probe returned HTTP {status}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    credential = subparsers.add_parser("credential-probe")
    _common_paths(credential)
    credential.add_argument("--round-plan", required=True)
    credential.add_argument("--output")
    credential.add_argument("--blind-health-ledger")
    credential.add_argument("--api-key-env", default="OPENROUTER_API_KEY")
    credential.add_argument("--timeout-seconds", type=int, default=30)
    credential.add_argument(
        "--probe-phase",
        choices=("pre_ramp", "pre_final_validation", "post_ramp"),
        default="pre_ramp",
    )

    stage = subparsers.add_parser("ramp-stage-receipt")
    _common_paths(stage)
    stage.add_argument("--output", required=True)
    stage.add_argument(
        "--scope",
        required=True,
        choices=("exploratory_measurement", "disposable_preflight", "formal_execution"),
    )
    stage.add_argument("--round-plan", required=True)
    stage.add_argument("--stage-ordinal", type=int, required=True)
    stage.add_argument("--worker-concurrency", type=int, required=True)
    stage.add_argument("--effective-worker-concurrency", type=int, required=True)
    stage.add_argument("--prior-safe-workers", type=int, required=True)
    stage.add_argument("--blind-health-ledger", required=True)
    stage.add_argument("--resource-ledger", required=True)
    stage.add_argument("--stage-workload", required=True)

    ramp = subparsers.add_parser("disposable-ramp-receipt")
    _common_paths(ramp)
    ramp.add_argument("--output", default=str(DEFAULT_RAMP_RECEIPT))
    ramp.add_argument("--stage-receipt", action="append", required=True)
    ramp.add_argument("--global-mixed-canary-receipt", required=True)
    ramp.add_argument("--pre-ramp-credential-receipt", required=True)
    ramp.add_argument("--post-ramp-credential-receipt", required=True)
    ramp.add_argument("--validation-round-plan", required=True)
    ramp.add_argument("--measurement-receipt", required=True)
    ramp.add_argument("--policy-finalization-receipt", required=True)

    round_plan = subparsers.add_parser("round-plan")
    _common_paths(round_plan)
    round_plan.add_argument("--output", required=True)
    round_plan.add_argument(
        "--round-kind",
        required=True,
        choices=("exploratory_measurement", "finalized_validation"),
    )
    round_plan.add_argument("--agents-config", default="configs/agents.yaml")
    round_plan.add_argument(
        "--manifest",
        default="experiments/agentdojo_full_v1.2.2_direct/experiment_manifest.yaml",
    )
    round_plan.add_argument(
        "--source-bundle",
        default=(
            "experiments/agentdojo_full_v1.2.2_direct/"
            "source_bundles/case_packet_source_bundle.json"
        ),
    )
    round_plan.add_argument("--result-namespace", required=True)
    round_plan.add_argument("--execution-budget-plan", default=str(DEFAULT_BUDGET_PLAN))
    round_plan.add_argument("--measurement-receipt")
    round_plan.add_argument("--policy-finalization-receipt")

    measurement = subparsers.add_parser("measurement-receipt")
    _common_paths(measurement)
    measurement.add_argument("--agents-config", default="configs/agents.yaml")
    measurement.add_argument("--output", required=True)
    measurement.add_argument("--round-plan", required=True)
    measurement.add_argument("--global-mixed-canary-receipt", required=True)
    measurement.add_argument("--stage-receipt", action="append", required=True)
    measurement.add_argument("--pre-ramp-credential-receipt", required=True)

    finalize = subparsers.add_parser("finalize-policy")
    finalize.add_argument("--policy", default=str(DEFAULT_POLICY))
    finalize.add_argument("--measurement-receipt", required=True)
    finalize.add_argument("--output", required=True)

    finalization = subparsers.add_parser("policy-finalization-receipt")
    finalization.add_argument("--candidate-policy", default=str(DEFAULT_POLICY))
    finalization.add_argument("--measurement-receipt", required=True)
    finalization.add_argument("--finalized-policy", required=True)
    finalization.add_argument("--output", required=True)

    verify = subparsers.add_parser("verify")
    _common_paths(verify)
    verify.add_argument("--credential-receipt", default=str(DEFAULT_CREDENTIAL_RECEIPT))
    verify.add_argument("--ramp-receipt", default=str(DEFAULT_RAMP_RECEIPT))
    return parser.parse_args(argv)


def _common_paths(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--policy", default=str(DEFAULT_POLICY))
    parser.add_argument("--runtime-infra", default=str(DEFAULT_INFRA))


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "finalize-policy":
            candidate_path = Path(args.policy)
            candidate = load_runtime_policy(
                json.loads(candidate_path.read_text(encoding="utf-8"))
            )
            finalized_payload = derive_finalized_runtime_policy(
                candidate, measurement_receipt_path=args.measurement_receipt
            )
            _write_once(
                args.output,
                finalized_payload,
                currentness_check=lambda path: dict(
                    load_runtime_policy(json.loads(path.read_text(encoding="utf-8"))).raw
                ),
            )
            result: Mapping[str, Any] = finalized_payload
            print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
            return 0
        if args.command == "policy-finalization-receipt":
            receipt = build_policy_finalization_receipt(
                candidate_policy_path=args.candidate_policy,
                measurement_receipt_path=args.measurement_receipt,
                finalized_policy_path=args.finalized_policy,
            )
            _write_once(
                args.output,
                receipt,
                currentness_check=lambda path: load_policy_finalization_receipt(path),
            )
            print(json.dumps(receipt, ensure_ascii=True, indent=2, sort_keys=True))
            return 0
        policy_path = Path(args.policy)
        infra_path = Path(args.runtime_infra)
        policy = load_runtime_policy(json.loads(policy_path.read_text(encoding="utf-8")))
        infra_sha = sha256_file(infra_path)
        if args.command == "round-plan":
            round_payload = build_disposable_round_plan(
                policy,
                policy_path=policy_path,
                runtime_infra_path=infra_path,
                agents_config_path=args.agents_config,
                manifest_path=args.manifest,
                source_bundle_path=args.source_bundle,
                result_namespace=args.result_namespace,
                round_kind=args.round_kind,
                execution_budget_plan_path=args.execution_budget_plan,
                measurement_receipt_path=args.measurement_receipt,
                policy_finalization_receipt_path=args.policy_finalization_receipt,
            )
            write_disposable_round_plan_once(args.output, round_payload)
            result = round_payload
        elif args.command == "credential-probe":
            round_plan = load_disposable_round_plan(args.round_plan)
            round_artifacts = dict(round_plan["artifact_namespace"])
            expected_output = (
                round_artifacts["post_credential_receipt"]
                if args.probe_phase == "post_ramp"
                else round_artifacts["pre_credential_receipt"]
            )
            expected_health = (
                round_artifacts["post_credential_health_ledger"]
                if args.probe_phase == "post_ramp"
                else round_artifacts["pre_credential_health_ledger"]
            )
            actual_output = args.output or expected_output
            actual_health = args.blind_health_ledger or expected_health
            _require_exact_portable_path(actual_output, expected_output, "credential output")
            _require_exact_portable_path(
                actual_health,
                expected_health,
                "credential blind-health ledger",
            )
            ledger = BlindHealthLedger(
                (actual_health,), policy_sha256=policy.semantic_sha256
            )
            key = os.environ.get(args.api_key_env)
            if not key:
                ledger.record(
                    event_type="credential_probe",
                    outcome="fatal_error",
                    credit_floor_usd=required_credit_floor(
                        policy, probe_phase=args.probe_phase
                    ),
                )
                raise RuntimePolicyError(
                    f"missing environment variable {args.api_key_env}"
                )
            status: int | None = None
            try:
                auth_lock_path = round_artifacts["controller_lifecycle_lock"]
                auth_lock = OpenRouterAuthLifecycleLock(auth_lock_path)
                with auth_lock.hold(exclusive=True):
                    status, key_payload = _get_json(
                        KEY_URL, api_key=key, timeout=args.timeout_seconds
                    )
                    _, models_payload = _get_json(
                        MODELS_URL, api_key=key, timeout=args.timeout_seconds
                    )
                    key_funding = _key_funding(key_payload)
                    key_metadata = _key_metadata(key_payload)
                    model_catalog = _required_model_catalog(models_payload)
                    receipt = build_credential_probe_receipt(
                        policy,
                        runtime_infra_file_sha256=infra_sha,
                        http_status=status,
                        key_limit_usd=key_funding["limit"],
                        key_limit_remaining_usd=key_funding["limit_remaining"],
                        key_usage_usd=key_funding["usage"],
                        provider_limit_mode=str(
                            key_funding["provider_limit_mode"]
                        ),
                        key_is_free_tier=key_metadata["is_free_tier"],
                        key_is_management=key_metadata["is_management_key"],
                        key_is_provisioning=key_metadata["is_provisioning_key"],
                        key_disabled=key_metadata["disabled"],
                        key_disabled_field_present=key_metadata[
                            "disabled_field_present"
                        ],
                        key_limit_reset_policy=key_metadata["limit_reset"],
                        key_expires_at=key_metadata["expires_at"],
                        model_catalog_entries=model_catalog,
                        credential_fingerprint_sha256=openrouter_key_fingerprint(key),
                        management_audit_status="waived_by_user",
                        round_plan_path=args.round_plan,
                        probe_phase=args.probe_phase,
                    )
            except ProbeHTTPError as exc:
                ledger.record(
                    event_type="credential_probe",
                    outcome="fatal_error",
                    http_status=exc.status,
                    credit_floor_usd=required_credit_floor(
                        policy, probe_phase=args.probe_phase
                    ),
                )
                raise
            except RuntimePolicyError:
                ledger.record(
                    event_type="credential_probe",
                    outcome="fatal_error",
                    http_status=status,
                    credit_floor_usd=required_credit_floor(
                        policy, probe_phase=args.probe_phase
                    ),
                )
                raise
            health_fields: dict[str, Any] = {
                "credit_floor_usd": required_credit_floor(
                    policy, probe_phase=args.probe_phase
                )
            }
            if key_funding["limit_remaining"] is not None:
                health_fields["credit_balance_usd"] = key_funding[
                    "limit_remaining"
                ]
            ledger.record(
                event_type="credential_probe",
                outcome="passed",
                http_status=200,
                **health_fields,
            )
            _write_once(
                actual_output,
                receipt,
                currentness_check=lambda path: load_credential_probe_receipt(
                    path,
                    expected_policy_sha256=policy.semantic_sha256,
                    expected_runtime_infra_file_sha256=infra_sha,
                    expected_probe_phase=args.probe_phase,
                ),
            )
            result: Mapping[str, Any] = receipt
        elif args.command == "ramp-stage-receipt":
            round_plan = load_disposable_round_plan(args.round_plan)
            try:
                stage_artifact = round_plan["artifact_namespace"]["stages"][
                    args.stage_ordinal
                ]
                planned_stage = round_plan["definition"]["stages"][args.stage_ordinal]
            except (IndexError, KeyError, TypeError) as exc:
                raise RuntimePolicyError("stage ordinal is outside the round plan") from exc
            _require_exact_portable_path(
                args.output, stage_artifact["stage_receipt"], "stage receipt"
            )
            _require_exact_portable_path(
                args.blind_health_ledger,
                stage_artifact["blind_health_ledger"],
                "stage blind-health ledger",
            )
            _require_exact_portable_path(
                args.resource_ledger,
                stage_artifact["resource_ledger"],
                "stage resource ledger",
            )
            workload = json.loads(Path(args.stage_workload).read_text(encoding="utf-8"))
            if not isinstance(workload, Mapping):
                raise RuntimePolicyError("stage workload must be a JSON object")
            if sha256_object(dict(workload)) != planned_stage["workload_sha256"]:
                raise RuntimePolicyError("stage workload differs from its round plan")
            receipt = build_ramp_stage_receipt(
                policy,
                scope=args.scope,
                worker_concurrency=args.worker_concurrency,
                effective_worker_concurrency=args.effective_worker_concurrency,
                prior_safe_workers=args.prior_safe_workers,
                runtime_infra_file_sha256=infra_sha,
                blind_health_ledger_path=args.blind_health_ledger,
                resource_ledger_path=args.resource_ledger,
                stage_workload=workload,
            )
            _write_once(
                args.output,
                receipt,
                currentness_check=lambda path: load_ramp_stage_receipt(
                    path,
                    expected_policy_sha256=policy.semantic_sha256,
                    expected_runtime_infra_file_sha256=infra_sha,
                    expected_scope=args.scope,
                ),
            )
            result = receipt
        elif args.command == "disposable-ramp-receipt":
            receipt = build_disposable_ramp_receipt(
                policy,
                runtime_infra_file_sha256=infra_sha,
                stage_receipt_paths=args.stage_receipt,
                global_mixed_canary_receipt_path=args.global_mixed_canary_receipt,
                pre_ramp_credential_receipt_path=args.pre_ramp_credential_receipt,
                post_ramp_credential_receipt_path=args.post_ramp_credential_receipt,
                validation_round_plan_path=args.validation_round_plan,
                measurement_receipt_path=args.measurement_receipt,
                policy_finalization_receipt_path=args.policy_finalization_receipt,
            )
            round_plan = load_disposable_round_plan(args.validation_round_plan)
            _require_exact_portable_path(
                args.output,
                round_plan["artifact_namespace"]["aggregate_receipt"],
                "validation aggregate receipt",
            )
            _write_once(
                args.output,
                receipt,
                currentness_check=lambda path: load_disposable_ramp_receipt(
                    path,
                    expected_policy_sha256=policy.semantic_sha256,
                    expected_stages=policy.ramp_stages,
                    expected_runtime_infra_file_sha256=infra_sha,
                ),
            )
            result = receipt
        elif args.command == "measurement-receipt":
            receipt = build_rate_measurement_receipt(
                policy,
                candidate_policy_path=policy_path,
                runtime_infra_path=infra_path,
                agents_config_path=args.agents_config,
                global_mixed_canary_receipt_path=args.global_mixed_canary_receipt,
                stage_receipt_paths=args.stage_receipt,
                pre_ramp_credential_receipt_path=args.pre_ramp_credential_receipt,
                measurement_round_plan_path=args.round_plan,
            )
            round_plan = load_disposable_round_plan(args.round_plan)
            _require_exact_portable_path(
                args.output,
                round_plan["artifact_namespace"]["aggregate_receipt"],
                "measurement aggregate receipt",
            )
            _write_once(
                args.output,
                receipt,
                currentness_check=lambda path: load_rate_measurement_receipt(
                    path,
                    expected_candidate_operational_definition_sha256=(
                        policy.operational_definition_sha256
                    ),
                    expected_runtime_infra_file_sha256=infra_sha,
                    expected_agents_config_file_sha256=sha256_file(
                        args.agents_config
                    ),
                ),
            )
            result = receipt
        else:
            credential = load_credential_probe_receipt(
                args.credential_receipt,
                expected_policy_sha256=policy.semantic_sha256,
                expected_runtime_infra_file_sha256=infra_sha,
            )
            ramp = load_disposable_ramp_receipt(
                args.ramp_receipt,
                expected_policy_sha256=policy.semantic_sha256,
                expected_stages=policy.ramp_stages,
                expected_runtime_infra_file_sha256=infra_sha,
            )
            result = {
                "status": "passed",
                "credential_receipt_sha256": sha256_file(args.credential_receipt),
                "ramp_receipt_sha256": sha256_file(args.ramp_receipt),
                "runtime_policy_semantic_sha256": policy.semantic_sha256,
                "credential_status": credential["status"],
                "ramp_status": ramp["status"],
            }
    except (OSError, ValueError, RuntimePolicyError, ProbeHTTPError) as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "secret_material_recorded": False,
                    "response_body_recorded": False,
                },
                ensure_ascii=True,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


def _get_json(url: str, *, api_key: str, timeout: int) -> tuple[int, Mapping[str, Any]]:
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = int(response.status)
            loaded = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ProbeHTTPError(int(exc.code)) from None
    except urllib.error.URLError as exc:
        raise RuntimePolicyError(
            f"OpenRouter credential probe transport failure: {type(exc.reason).__name__}"
        ) from None
    if status != 200 or not isinstance(loaded, Mapping):
        raise ProbeHTTPError(status)
    return status, loaded


def _key_account_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    if not isinstance(data, Mapping):
        raise RuntimePolicyError("OpenRouter key response has no data object")
    fields = (
        "creator_user_id",
        "label",
        "limit",
        "limit_remaining",
        "limit_reset",
        "usage",
        "expires_at",
    )
    missing = [field for field in fields if field not in data]
    if missing:
        raise RuntimePolicyError(
            f"OpenRouter key response lacks same-account match fields: {missing!r}"
        )
    return {field: data[field] for field in fields}


def _management_key_inventory(
    *, management_api_key: str, timeout: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Walk the default-workspace management inventory without persisting rows."""

    projections: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    seen_page_digests: set[str] = set()
    offset = 0
    for _ in range(KEYS_MAX_PAGES):
        query = urllib.parse.urlencode(
            {"offset": offset, "include_disabled": "true"}
        )
        _, payload = _get_json(
            f"{KEYS_URL}?{query}",
            api_key=management_api_key,
            timeout=timeout,
        )
        rows = payload.get("data")
        if not isinstance(rows, list):
            raise RuntimePolicyError(
                "OpenRouter management /keys response has no data list"
            )
        if len(rows) > KEYS_PAGE_SIZE:
            raise RuntimePolicyError(
                "OpenRouter management /keys response exceeded the documented 100-row page"
            )
        page_digest = sha256_object(dict(payload))
        if page_digest in seen_page_digests:
            raise RuntimePolicyError(
                "OpenRouter management /keys repeated a canonical response page"
            )
        seen_page_digests.add(page_digest)
        pages.append(
            {
                "offset": offset,
                "count": len(rows),
                "canonical_response_sha256": page_digest,
            }
        )
        for row in rows:
            if not isinstance(row, Mapping):
                raise RuntimePolicyError(
                    "OpenRouter management /keys inventory contains a non-object row"
                )
            # Wrap the row to reuse the exact /key field extractor, then drop
            # it immediately after the in-memory projection is built.
            projections.append(_key_account_projection({"data": row}))
        if len(rows) < KEYS_PAGE_SIZE:
            return projections, pages
        offset += len(rows)
    raise RuntimePolicyError(
        "OpenRouter management /keys inventory exceeded the 100-page safety limit "
        "without a terminating short page"
    )


def _key_funding(payload: Mapping[str, Any]) -> dict[str, float | str | None]:
    data = payload.get("data")
    if not isinstance(data, Mapping):
        raise RuntimePolicyError("OpenRouter key response has no data object")
    try:
        raw_limit = data["limit"]
        raw_remaining = data["limit_remaining"]
        usage_value = float(data["usage"])
    except (TypeError, ValueError) as exc:
        raise RuntimePolicyError(
            "OpenRouter dedicated key requires numeric usage"
        ) from exc
    except KeyError as exc:
        raise RuntimePolicyError(
            "OpenRouter dedicated key is missing limit, limit_remaining, or usage"
        ) from exc
    if raw_limit is None and raw_remaining is None:
        limit_value = None
        remaining_value = None
        provider_limit_mode = "unlimited_no_provider_cap"
    elif raw_limit is not None and raw_remaining is not None:
        try:
            limit_value = float(raw_limit)
            remaining_value = float(raw_remaining)
        except (TypeError, ValueError) as exc:
            raise RuntimePolicyError(
                "OpenRouter explicit key limit fields must be numeric"
            ) from exc
        provider_limit_mode = "explicit_cap"
    else:
        raise RuntimePolicyError(
            "OpenRouter key limit and limit_remaining must both be numeric or both null"
        )
    if not math.isfinite(usage_value) or usage_value < 0:
        raise RuntimePolicyError("OpenRouter key usage must be finite and non-negative")
    return {
        "limit": limit_value,
        "limit_remaining": remaining_value,
        "usage": usage_value,
        "provider_limit_mode": provider_limit_mode,
    }


def _key_metadata(payload: Mapping[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    if not isinstance(data, Mapping):
        raise RuntimePolicyError("OpenRouter key response has no data object")
    is_free_tier = data.get("is_free_tier")
    if not isinstance(is_free_tier, bool):
        raise RuntimePolicyError("OpenRouter key response has no boolean is_free_tier")
    is_management = data.get("is_management_key")
    is_provisioning = data.get("is_provisioning_key")
    if not isinstance(is_management, bool) or not isinstance(is_provisioning, bool):
        raise RuntimePolicyError(
            "OpenRouter key response must expose management/provisioning booleans"
        )
    limit_reset = data.get("limit_reset")
    if limit_reset not in {None, "daily", "weekly", "monthly"}:
        raise RuntimePolicyError(
            "OpenRouter key limit_reset must be daily, weekly, monthly, or null"
        )
    disabled_present = "disabled" in data
    disabled = data.get("disabled")
    if disabled_present and not isinstance(disabled, bool):
        raise RuntimePolicyError("OpenRouter key disabled field is not boolean")
    return {
        "is_free_tier": is_free_tier,
        "is_management_key": is_management,
        "is_provisioning_key": is_provisioning,
        "disabled": disabled if disabled_present else None,
        "disabled_field_present": disabled_present,
        "limit_reset": limit_reset,
        "expires_at": _nullable_timestamp(data.get("expires_at"), "expires_at"),
    }


def _account_credits(payload: Mapping[str, Any]) -> dict[str, float]:
    data = payload.get("data")
    if not isinstance(data, Mapping):
        raise RuntimePolicyError("OpenRouter credits response has no data object")
    try:
        total_credits = float(data["total_credits"])
        total_usage = float(data["total_usage"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimePolicyError(
            "OpenRouter credits response requires numeric total_credits and total_usage"
        ) from exc
    if (
        not math.isfinite(total_credits)
        or not math.isfinite(total_usage)
        or total_credits < 0
        or total_usage < 0
        or total_usage > total_credits
    ):
        raise RuntimePolicyError("OpenRouter account credits are invalid")
    return {"total_credits": total_credits, "total_usage": total_usage}


def _nullable_timestamp(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise RuntimePolicyError(f"OpenRouter key {field} is not null or a timestamp")
    return value.strip()


def _required_model_catalog(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise RuntimePolicyError("OpenRouter model response has no data list")
    by_id = {
        str(row.get("id")): row
        for row in rows
        if isinstance(row, Mapping) and row.get("id")
    }
    missing = [model for model in REQUIRED_MODELS if model not in by_id]
    if missing:
        raise RuntimePolicyError(f"frozen OpenRouter model(s) unavailable: {missing}")
    return tuple(by_id[model] for model in REQUIRED_MODELS)


def _write_once(
    path: str | Path,
    payload: Mapping[str, Any],
    *,
    currentness_check: Callable[[Path], Mapping[str, Any]],
) -> None:
    output = resolve_repo_path(path)
    encoded = json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    if output.exists() or output.is_symlink():
        _assert_single_link_regular_file(output, "existing receipt")
        if output.read_text(encoding="utf-8") != encoded:
            raise RuntimePolicyError(f"receipt already exists and differs: {output}")
        if dict(currentness_check(output)) != dict(payload):
            raise RuntimePolicyError("existing identical receipt failed currentness check")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    _assert_output_directory_chain(output.parent)
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
            _assert_single_link_regular_file(output, "racing receipt")
            if output.read_text(encoding="utf-8") != encoded:
                raise RuntimePolicyError("receipt publication race produced different bytes")
            if dict(currentness_check(output)) != dict(payload):
                raise RuntimePolicyError("racing identical receipt failed currentness check")
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


def _assert_single_link_regular_file(path: Path, label: str) -> None:
    info = os.lstat(path)
    if path.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise RuntimePolicyError(f"{label} must be a single-link regular file")


def _assert_output_directory_chain(directory: Path) -> None:
    root = repo_root().absolute()
    candidate = directory.absolute()
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise RuntimePolicyError("receipt output must remain under repository root") from exc
    current = root
    for part in relative.parts:
        current = current / part
        info = os.lstat(current)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise RuntimePolicyError("receipt output ancestor contains a symlink")


def _require_exact_portable_path(
    actual: str | Path, expected: str | None, label: str
) -> None:
    if expected is None:
        raise RuntimePolicyError(f"{label} is not valid for this round")
    actual_path = resolve_repo_path(actual)
    expected_path = resolve_repo_path(expected)
    if actual_path.absolute() != expected_path.absolute():
        raise RuntimePolicyError(f"{label} is outside the SHA-derived round namespace")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
