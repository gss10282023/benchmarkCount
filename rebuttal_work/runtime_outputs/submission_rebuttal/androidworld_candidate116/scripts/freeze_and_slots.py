"""Pure builders for the AndroidWorld candidate-116 draft-input freeze.

This module deliberately does no filesystem I/O.  The caller owns loading and
writing JSON/YAML files and supplies the byte-level sha256 values of those
files.  Keeping the builders pure makes it possible for the package builder to
construct an artifact, write it, reload it, and run the same validators before
any contract-drafting call is made.

The freeze produced here freezes *draft inputs only*.  It does not turn the
draft/prelock experiment manifests into locked manifests, and it is explicitly
ineligible for AndroidWorld execution or scoring.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any


DOMAIN = "androidworld"
AGENT_IDS = ("Agent A", "Agent B", "Agent C")
CANDIDATE_CASE_COUNT = 116
OFFICIAL_CASE_COUNT = 100
EXTRA_CASE_COUNT = 16

CANDIDATE_SLOT_COUNT = 348
OFFICIAL_SLOT_COUNT = 300
EXTRA_SLOT_COUNT = 48

# These are hashes of ordered JSON string arrays, not hashes of
# {case_unit_id, agent_id} objects.
EXPECTED_CANDIDATE116_SLOT_HASH = (
    "ee6bf85a39f4caaea1ce687059f3e79452834f6011c1bb93d8cc125cb83971c8"
)
EXPECTED_OFFICIAL100_SLOT_HASH = (
    "7e9a921a15a1c1cfd6b0f492c2b30b02119c8406773c048aebb7a93abe088e6d"
)
EXPECTED_EXTRA16_SLOT_HASH = (
    "57ba693defbf80d5145a15656c9fd2ce3f98cb6a9f61a744381fe74010216c9e"
)
EMPTY_LIST_HASH = "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"

SLOT_LEDGER_SCHEMA_VERSION = "record_slot_ledger/v1"
FREEZE_SCHEMA_VERSION = "contract_draft_input_freeze/v1"

_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9._-]+")
_SHA256_RE = re.compile(r"^(?:sha256:)?[a-f0-9]{64}$")
_ENV_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")

_DRAFTER_ROLE_FIELDS = (
    "provider",
    "model",
    "model_version",
    "api_key_env",
    "temperature",
    "max_tokens",
    "timeout_seconds",
    "retry",
    "rate_limit",
    "save_response_metadata",
    "cost_tracking",
    "prompt_version",
    "prompt_hash",
    "prompt_hash_method",
)

_PLACEHOLDER_PHRASES = (
    "需要从 locked manifest 确认",
    "需要从 scored manifest 填充",
    "需要从论文确认",
    "需要从 benchmark 官方 split 确认",
    "\\fillfromdata",
    "fillfromdata",
    "pending_formal_lock",
)
_PLACEHOLDER_TOKENS = frozenset(
    {
        "placeholder",
        "tbd",
        "todo",
        "not_implemented",
        "not implemented",
    }
)


class FreezeBuildError(ValueError):
    """Raised when an input cannot support a truthful draft-input freeze."""


def canonical_json_bytes(payload: Any) -> bytes:
    """Return the repository's canonical JSON representation."""

    return json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def payload_sha256(payload: Any) -> str:
    """Hash a JSON-compatible payload using repository canonical JSON."""

    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def canonical_string_list_hash(values: Sequence[Any]) -> str:
    """Hash an ordered string list exactly as denominator validation does."""

    normalized = [str(value) for value in values]
    encoded = json.dumps(
        normalized,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def safe_id(value: Any) -> str:
    """Mirror ``evidence_system.orchestrator.jobs._safe_id``."""

    return _SAFE_ID_RE.sub("_", str(value)).strip("_") or "unknown"


def build_candidate116_slot_ledger(
    ordered_cases: Sequence[Mapping[str, Any]],
    *,
    domain: str = DOMAIN,
    agent_ids: Sequence[str] = AGENT_IDS,
    ledger_id: str = "androidworld_candidate116_record_slots",
) -> dict[str, Any]:
    """Build the canonical 348-slot ledger and its two contiguous subsets."""

    cases = _normalize_ordered_cases(ordered_cases)
    agents = [str(value) for value in agent_ids]
    if domain != DOMAIN:
        raise FreezeBuildError(f"candidate116 ledger domain must be {DOMAIN!r}")
    if agents != list(AGENT_IDS):
        raise FreezeBuildError(f"candidate116 agent order must be {list(AGENT_IDS)!r}")
    if not str(ledger_id).strip():
        raise FreezeBuildError("ledger_id must be non-empty")

    rows, slot_ids = _build_slot_rows(cases, domain=domain, agent_ids=agents)
    official_ids = slot_ids[:OFFICIAL_SLOT_COUNT]
    extra_ids = slot_ids[OFFICIAL_SLOT_COUNT:]
    payload: dict[str, Any] = {
        "schema_version": SLOT_LEDGER_SCHEMA_VERSION,
        "ledger_id": str(ledger_id),
        "domain": domain,
        "case_count": len(cases),
        "agent_count": len(agents),
        "agent_ids": agents,
        "record_slot_count": len(slot_ids),
        "ordering": {
            "case_order": "selection_rank ascending, zero based",
            "agent_order": agents,
            "record_slot_id_template": (
                "slot-{domain}-{safe_id(case_unit_id)}-"
                "{safe_id(agent_id.lower().replace(' ', '_'))}"
            ),
            "safe_id_rule": "replace each non-[A-Za-z0-9._-]+ run with '_' and strip '_'",
            "record_slot_ids_hash_method": (
                "sha256(json.dumps(ordered_string_list, ensure_ascii=True, "
                "separators=(',', ':')))"
            ),
        },
        "cases": cases,
        "rows": rows,
        "record_slot_ids": slot_ids,
        "record_slot_ids_hash": canonical_string_list_hash(slot_ids),
        "subsets": {
            "official100": _slot_subset(
                official_ids,
                case_start=0,
                case_end_exclusive=OFFICIAL_CASE_COUNT,
                parent_slot_start=0,
            ),
            "extra16": _slot_subset(
                extra_ids,
                case_start=OFFICIAL_CASE_COUNT,
                case_end_exclusive=CANDIDATE_CASE_COUNT,
                parent_slot_start=OFFICIAL_SLOT_COUNT,
            ),
        },
    }
    payload["ledger_sha256"] = payload_sha256(payload)
    issues = validate_candidate116_slot_ledger(payload)
    if issues:
        raise FreezeBuildError("invalid generated slot ledger: " + "; ".join(issues))
    return payload


def validate_candidate116_slot_ledger(payload: Mapping[str, Any]) -> list[str]:
    """Return all structural, ordering, and known-hash ledger violations."""

    issues: list[str] = []
    if not isinstance(payload, Mapping):
        return ["slot ledger must be a mapping"]
    if payload.get("schema_version") != SLOT_LEDGER_SCHEMA_VERSION:
        issues.append(f"schema_version must be {SLOT_LEDGER_SCHEMA_VERSION}")
    if payload.get("domain") != DOMAIN:
        issues.append(f"domain must be {DOMAIN}")
    if payload.get("agent_ids") != list(AGENT_IDS):
        issues.append("agent_ids must be ordered Agent A, Agent B, Agent C")
    if payload.get("case_count") != CANDIDATE_CASE_COUNT:
        issues.append(f"case_count must be {CANDIDATE_CASE_COUNT}")
    if payload.get("agent_count") != len(AGENT_IDS):
        issues.append(f"agent_count must be {len(AGENT_IDS)}")
    if payload.get("record_slot_count") != CANDIDATE_SLOT_COUNT:
        issues.append(f"record_slot_count must be {CANDIDATE_SLOT_COUNT}")

    try:
        cases = _normalize_ordered_cases(payload.get("cases"))
    except (FreezeBuildError, TypeError) as exc:
        issues.append(f"cases: {exc}")
        cases = []

    if cases:
        expected_rows, expected_ids = _build_slot_rows(
            cases,
            domain=DOMAIN,
            agent_ids=list(AGENT_IDS),
        )
        if payload.get("rows") != expected_rows:
            issues.append("rows do not exactly match canonical case-major/agent-minor order")
        if payload.get("record_slot_ids") != expected_ids:
            issues.append("record_slot_ids do not exactly match canonical rows")
        observed_hash = canonical_string_list_hash(expected_ids)
        if payload.get("record_slot_ids_hash") != observed_hash:
            issues.append("record_slot_ids_hash does not hash record_slot_ids")
        if observed_hash != EXPECTED_CANDIDATE116_SLOT_HASH:
            issues.append("candidate116 record_slot_ids do not match the predeclared candidate order")

        subsets = payload.get("subsets")
        if not isinstance(subsets, Mapping):
            issues.append("subsets must be a mapping")
        else:
            expected_official = _slot_subset(
                expected_ids[:OFFICIAL_SLOT_COUNT],
                case_start=0,
                case_end_exclusive=OFFICIAL_CASE_COUNT,
                parent_slot_start=0,
            )
            expected_extra = _slot_subset(
                expected_ids[OFFICIAL_SLOT_COUNT:],
                case_start=OFFICIAL_CASE_COUNT,
                case_end_exclusive=CANDIDATE_CASE_COUNT,
                parent_slot_start=OFFICIAL_SLOT_COUNT,
            )
            if subsets.get("official100") != expected_official:
                issues.append("subsets.official100 is not the first 300 parent slots")
            if subsets.get("extra16") != expected_extra:
                issues.append("subsets.extra16 is not parent slots 300..347")

    if payload.get("record_slot_ids_hash") != EXPECTED_CANDIDATE116_SLOT_HASH:
        issues.append("candidate116 known slot hash mismatch")
    subsets = payload.get("subsets")
    if isinstance(subsets, Mapping):
        official = subsets.get("official100")
        extra = subsets.get("extra16")
        if not isinstance(official, Mapping) or official.get("record_slot_ids_hash") != EXPECTED_OFFICIAL100_SLOT_HASH:
            issues.append("official100 known slot hash mismatch")
        if not isinstance(extra, Mapping) or extra.get("record_slot_ids_hash") != EXPECTED_EXTRA16_SLOT_HASH:
            issues.append("extra16 known slot hash mismatch")

    ledger_hash = payload.get("ledger_sha256")
    if not _is_sha256(ledger_hash):
        issues.append("ledger_sha256 must be a sha256")
    else:
        hash_input = dict(payload)
        hash_input.pop("ledger_sha256", None)
        if ledger_hash != payload_sha256(hash_input):
            issues.append("ledger_sha256 does not hash the payload excluding ledger_sha256")
    return _dedupe(issues)


def assert_known_slot_hashes(payload: Mapping[str, Any]) -> None:
    """Fail unless the candidate116, official100, and extra16 hashes are exact."""

    subsets = payload.get("subsets")
    observed = {
        "candidate116": payload.get("record_slot_ids_hash"),
        "official100": subsets.get("official100", {}).get("record_slot_ids_hash")
        if isinstance(subsets, Mapping)
        else None,
        "extra16": subsets.get("extra16", {}).get("record_slot_ids_hash")
        if isinstance(subsets, Mapping)
        else None,
    }
    expected = {
        "candidate116": EXPECTED_CANDIDATE116_SLOT_HASH,
        "official100": EXPECTED_OFFICIAL100_SLOT_HASH,
        "extra16": EXPECTED_EXTRA16_SLOT_HASH,
    }
    if observed != expected:
        raise FreezeBuildError(f"known slot hash mismatch: observed={observed!r}, expected={expected!r}")


def build_contract_drafter_config(
    baseline_agents_config: Mapping[str, Any],
    *,
    prompt_version: str,
    prompt_hash: str,
) -> dict[str, Any]:
    """Project a minimal, placeholder-free config for ``contract_drafter``.

    The result intentionally contains only ``schema_version``, optional shared
    ``llm_call_logging``, and ``contract_drafter``.  It is accepted by
    ``load_role_config('contract_drafter', ...)``; it is not represented as a
    complete Agent A-C/judge execution config.
    """

    if not isinstance(baseline_agents_config, Mapping):
        raise FreezeBuildError("baseline agents config must be a mapping")
    baseline_role = baseline_agents_config.get("contract_drafter")
    if not isinstance(baseline_role, Mapping):
        raise FreezeBuildError("baseline agents config requires contract_drafter mapping")
    if not str(prompt_version).strip() or _contains_placeholder(prompt_version):
        raise FreezeBuildError("prompt_version must be a non-placeholder string")
    if not _is_sha256(prompt_hash):
        raise FreezeBuildError("prompt_hash must be a lowercase sha256")

    role = copy.deepcopy(dict(baseline_role))
    role["prompt_version"] = str(prompt_version)
    role["prompt_hash"] = str(prompt_hash)
    role["prompt_hash_method"] = "sha256"
    _validate_contract_drafter_role(role)

    projected: dict[str, Any] = {
        "schema_version": str(baseline_agents_config.get("schema_version") or "agents/v1"),
    }
    logging_config = baseline_agents_config.get("llm_call_logging")
    if isinstance(logging_config, Mapping):
        projected["llm_call_logging"] = copy.deepcopy(dict(logging_config))
    projected["contract_drafter"] = role
    if _contains_placeholder(projected):
        raise FreezeBuildError("projected contract_drafter config contains a placeholder")
    return projected


def project_contract_drafter_llm_role(
    contract_drafter_config: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the exact manifest-compatible LLM role projection."""

    if not isinstance(contract_drafter_config, Mapping):
        raise FreezeBuildError("contract_drafter config must be a mapping")
    role = contract_drafter_config.get("contract_drafter")
    if not isinstance(role, Mapping):
        raise FreezeBuildError("contract_drafter config has no contract_drafter role")
    _validate_contract_drafter_role(role)
    projected = {field: copy.deepcopy(role[field]) for field in _DRAFTER_ROLE_FIELDS}
    if "pricing_table" in role:
        projected["pricing_table"] = copy.deepcopy(role["pricing_table"])
    return projected


def build_prelock_manifest_binding(
    *,
    name: str,
    path: str,
    sha256: str,
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive the non-circular fields frozen for one draft/prelock manifest."""

    _validate_artifact_ref({"path": path, "sha256": sha256}, name)
    if not isinstance(manifest, Mapping):
        raise FreezeBuildError(f"{name} manifest must be a mapping")
    if manifest.get("schema_version") != "experiment_manifest/v1":
        raise FreezeBuildError(f"{name} is not an experiment_manifest/v1")
    if manifest.get("status") != "draft":
        raise FreezeBuildError(f"{name} manifest must remain status=draft at prelock")
    locks = manifest.get("contract_locks")
    if locks != []:
        raise FreezeBuildError(f"{name} prelock manifest must have contract_locks=[]")
    declared_lock_hash = manifest.get("contract_locks_hash")
    if declared_lock_hash not in (None, EMPTY_LIST_HASH):
        raise FreezeBuildError(f"{name} contract_locks_hash must be absent/null or hash([])")
    domains = manifest.get("domains")
    android_domains = [item for item in domains or [] if isinstance(item, Mapping) and item.get("domain") == DOMAIN]
    if len(android_domains) != 1:
        raise FreezeBuildError(f"{name} must contain exactly one AndroidWorld domain block")
    domain_block = android_domains[0]
    case_units = domain_block.get("case_units")
    if not isinstance(case_units, Sequence) or isinstance(case_units, (str, bytes, bytearray)):
        raise FreezeBuildError(f"{name} AndroidWorld case_units must be a sequence")
    case_ids: list[str] = []
    task_ids: list[str] = []
    for index, item in enumerate(case_units):
        if not isinstance(item, Mapping):
            raise FreezeBuildError(f"{name} case_units[{index}] must be a mapping")
        case_ids.append(_required_text(item, "case_unit_id", f"{name}.case_units[{index}]"))
        task_ids.append(_required_text(item, "task_id", f"{name}.case_units[{index}]"))
        if item.get("contract_lock_status") == "locked":
            raise FreezeBuildError(f"{name} case_units[{index}] cannot be locked at prelock")
    if len(case_ids) != len(set(case_ids)):
        raise FreezeBuildError(f"{name} contains duplicate case_unit_id values")
    if len(task_ids) != len(set(task_ids)):
        raise FreezeBuildError(f"{name} contains duplicate task_id values")
    if domain_block.get("contract_lock_status") == "locked":
        raise FreezeBuildError(f"{name} domain cannot be locked at prelock")

    llm_roles = manifest.get("llm_roles")
    binding: dict[str, Any] = {
        "name": str(name),
        "path": str(path),
        "sha256": str(sha256),
        "manifest_id": _required_text(manifest, "manifest_id", name),
        "manifest_version": _required_text(manifest, "manifest_version", name),
        "status": "draft",
        "prelock": True,
        "contract_lock_count": 0,
        "contract_locks_sha256": EMPTY_LIST_HASH,
        "case_unit_count": len(case_ids),
        "case_unit_ids": case_ids,
        "task_ids": task_ids,
        "case_unit_ids_hash": canonical_string_list_hash(case_ids),
        "planned_record_slot_ids_hash": domain_block.get("planned_record_slot_ids_hash"),
        "record_slot_count": domain_block.get("record_slot_count"),
        "agents_config_sha256": manifest.get("agents_config_hash"),
        "source_bundle_sha256": manifest.get("source_bundle_hash"),
        "llm_roles_sha256": payload_sha256(llm_roles) if isinstance(llm_roles, Mapping) else None,
    }
    if not _is_sha256(binding["planned_record_slot_ids_hash"]):
        raise FreezeBuildError(f"{name} planned_record_slot_ids_hash must be a sha256")
    if not isinstance(binding["record_slot_count"], int):
        raise FreezeBuildError(f"{name} record_slot_count must be an integer")
    return binding


def build_per_case_draft_bindings(
    ordered_cases: Sequence[Mapping[str, Any]],
    *,
    source_bundle: Mapping[str, Any],
    semantic_contexts: Mapping[str, Mapping[str, Any]] | Sequence[Mapping[str, Any]],
    rendered_prompts: Mapping[str, str] | Sequence[str],
) -> list[dict[str, Any]]:
    """Bind persisted packet/source rows and actual per-case semantic prompts."""

    cases = _normalize_ordered_cases(ordered_cases)
    if not isinstance(source_bundle, Mapping):
        raise FreezeBuildError("source_bundle must be a mapping")
    sources = source_bundle.get("sources")
    if not isinstance(sources, Sequence) or isinstance(sources, (str, bytes, bytearray)):
        raise FreezeBuildError("source_bundle.sources must be a sequence")
    if len(sources) != CANDIDATE_CASE_COUNT or source_bundle.get("source_count") != CANDIDATE_CASE_COUNT:
        raise FreezeBuildError("candidate source bundle must declare and contain exactly 116 sources")

    rows: list[dict[str, Any]] = []
    for rank, (case, source) in enumerate(zip(cases, sources, strict=True)):
        if not isinstance(source, Mapping):
            raise FreezeBuildError(f"source_bundle.sources[{rank}] must be a mapping")
        case_id = case["case_unit_id"]
        task_id = case["task_id"]
        if source.get("case_unit_id") != case_id or source.get("task_id") != task_id:
            raise FreezeBuildError(f"source bundle order/identity mismatch at rank {rank}")
        draft_input = source.get("draft_input")
        if not isinstance(draft_input, Mapping):
            raise FreezeBuildError(f"source {case_id} requires draft_input mapping")
        semantic = _case_value(semantic_contexts, case_id, rank, "semantic_contexts")
        if not isinstance(semantic, Mapping):
            raise FreezeBuildError(f"semantic context for {case_id} must be a mapping")
        prompt = _case_value(rendered_prompts, case_id, rank, "rendered_prompts")
        if not isinstance(prompt, str) or not prompt:
            raise FreezeBuildError(f"rendered prompt for {case_id} must be a non-empty string")

        persisted_source = {
            str(key): copy.deepcopy(value)
            for key, value in source.items()
            if not str(key).startswith("__")
        }
        row = {
            "selection_rank": rank,
            "group": "official100" if rank < OFFICIAL_CASE_COUNT else "extra16",
            "case_unit_id": case_id,
            "task_id": task_id,
            "contract_id": _required_text(source, "contract_id", f"source[{rank}]"),
            "case_packet_path": _required_text(draft_input, "case_packet_path", f"source[{rank}].draft_input"),
            "case_packet_sha256": _required_hash(draft_input, "case_packet_sha256", f"source[{rank}].draft_input"),
            "raw_case_manifest_path": _required_text(
                draft_input,
                "raw_case_manifest_path",
                f"source[{rank}].draft_input",
            ),
            "raw_case_manifest_sha256": _required_hash(
                draft_input,
                "raw_case_manifest_sha256",
                f"source[{rank}].draft_input",
            ),
            "source_closure_sha256": _required_hash(
                ordered_cases[rank],
                "source_closure_sha256",
                f"ordered_cases[{rank}]",
            ),
            "source_bundle_item_sha256": payload_sha256(persisted_source),
            "semantic_source_context_sha256": payload_sha256(dict(semantic)),
            # This intentionally mirrors draft.py's sha256_object({"prompt": prompt}).
            "rendered_prompt_sha256": payload_sha256({"prompt": prompt}),
        }
        rows.append(row)
    return rows


def build_draft_input_freeze(
    *,
    freeze_id: str,
    frozen_at: str,
    manifest_bindings: Mapping[str, Mapping[str, Any]],
    ordered_cases: Sequence[Mapping[str, Any]],
    packet_index_ref: Mapping[str, Any],
    source_bundle_ref: Mapping[str, Any],
    per_case_inputs: Sequence[Mapping[str, Any]],
    contract_drafter_config: Mapping[str, Any],
    contract_drafter_config_ref: Mapping[str, Any],
    slot_ledger: Mapping[str, Any],
    slot_ledger_ref: Mapping[str, Any],
    llm_roles: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build an immutable sidecar that freezes exactly 116 drafting inputs."""

    if not str(freeze_id).strip():
        raise FreezeBuildError("freeze_id must be non-empty")
    if not str(frozen_at).strip():
        raise FreezeBuildError("frozen_at must be supplied by the caller")
    cases = _normalize_ordered_cases(ordered_cases)
    case_rows = _normalize_per_case_inputs(per_case_inputs, cases)
    _validate_artifact_ref(packet_index_ref, "packet_index")
    _validate_artifact_ref(source_bundle_ref, "source_bundle")
    _validate_artifact_ref(contract_drafter_config_ref, "contract_drafter_config")
    _validate_artifact_ref(slot_ledger_ref, "slot_ledger")

    ledger_issues = validate_candidate116_slot_ledger(slot_ledger)
    if ledger_issues:
        raise FreezeBuildError("slot ledger is invalid: " + "; ".join(ledger_issues))
    assert_known_slot_hashes(slot_ledger)

    drafter_role = project_contract_drafter_llm_role(contract_drafter_config)
    roles: dict[str, Any]
    if llm_roles is None:
        roles = {"contract_drafter": drafter_role}
    else:
        roles = copy.deepcopy(dict(llm_roles))
        if roles.get("contract_drafter") != drafter_role:
            raise FreezeBuildError("llm_roles.contract_drafter disagrees with dedicated config")
        if _contains_placeholder(roles):
            raise FreezeBuildError("llm_roles contains an unresolved placeholder")

    bindings = _normalize_manifest_bindings(manifest_bindings, cases, slot_ledger)
    config_file_hash = str(contract_drafter_config_ref["sha256"])
    for name, binding in bindings.items():
        declared = binding.get("agents_config_sha256")
        if declared is not None and declared != config_file_hash:
            raise FreezeBuildError(f"{name} agents_config_sha256 disagrees with dedicated config file")
        declared_roles_hash = binding.get("llm_roles_sha256")
        if declared_roles_hash is not None and declared_roles_hash != payload_sha256(roles):
            raise FreezeBuildError(f"{name} llm_roles disagree with the frozen llm_roles")

    case_ids = [case["case_unit_id"] for case in cases]
    task_ids = [case["task_id"] for case in cases]
    subsets = slot_ledger["subsets"]
    freeze: dict[str, Any] = {
        "schema_version": FREEZE_SCHEMA_VERSION,
        "freeze_id": str(freeze_id),
        "status": "frozen",
        "scope": "androidworld_contract_draft_inputs_only",
        "frozen_at": str(frozen_at),
        "execution_eligible": False,
        "scoring_eligible": False,
        "prelock_assertions": {
            "manifests_remain_draft": True,
            "contract_locks_expected_empty": True,
            "contracts_expected": CANDIDATE_CASE_COUNT,
            "draft_calls_expected": CANDIDATE_CASE_COUNT,
            "androidworld_execution_requires_later_locked_manifest": True,
        },
        "hash_methods": {
            "artifact_sha256": "sha256(file bytes)",
            "canonical_payload_sha256": (
                "sha256(json.dumps(payload, ensure_ascii=True, separators=(',', ':'), sort_keys=True))"
            ),
            "record_slot_ids_hash": (
                "sha256(json.dumps(ordered_string_list, ensure_ascii=True, separators=(',', ':')))"
            ),
            "rendered_prompt_sha256": "canonical_payload_sha256({'prompt': rendered_prompt})",
            "semantic_source_context_sha256": "canonical_payload_sha256(derive_source_context(source))",
            "source_bundle_item_sha256": "canonical_payload_sha256(persisted source bundle item)",
            "freeze_sha256": "canonical_payload_sha256(payload excluding freeze_sha256)",
        },
        "artifacts": {
            "manifests": bindings,
            "packet_index": _copy_artifact_ref(packet_index_ref),
            "source_bundle": _copy_artifact_ref(source_bundle_ref),
            "contract_drafter_config": {
                **_copy_artifact_ref(contract_drafter_config_ref),
                "canonical_payload_sha256": payload_sha256(contract_drafter_config),
            },
            "slot_ledger": {
                **_copy_artifact_ref(slot_ledger_ref),
                "ledger_sha256": slot_ledger["ledger_sha256"],
            },
        },
        "case_order": {
            "selection_rank_start": 0,
            "selection_rank_end_exclusive": CANDIDATE_CASE_COUNT,
            "case_count": CANDIDATE_CASE_COUNT,
            "official100_count": OFFICIAL_CASE_COUNT,
            "extra16_count": EXTRA_CASE_COUNT,
            "case_unit_ids": case_ids,
            "task_ids": task_ids,
            "case_unit_ids_hash": canonical_string_list_hash(case_ids),
            "task_ids_hash": canonical_string_list_hash(task_ids),
            "case_identity_sha256": payload_sha256(cases),
        },
        "llm": {
            "llm_roles": roles,
            "llm_roles_sha256": payload_sha256(roles),
            "contract_drafter_role_sha256": payload_sha256(drafter_role),
            "contract_drafter_config_sha256": config_file_hash,
            "contract_drafter_config_canonical_payload_sha256": payload_sha256(
                contract_drafter_config
            ),
        },
        "slots": {
            "ledger_id": slot_ledger["ledger_id"],
            "ledger_sha256": slot_ledger["ledger_sha256"],
            "candidate116_record_slot_count": CANDIDATE_SLOT_COUNT,
            "candidate116_record_slot_ids_hash": slot_ledger["record_slot_ids_hash"],
            "official100_record_slot_count": OFFICIAL_SLOT_COUNT,
            "official100_record_slot_ids_hash": subsets["official100"]["record_slot_ids_hash"],
            "extra16_record_slot_count": EXTRA_SLOT_COUNT,
            "extra16_record_slot_ids_hash": subsets["extra16"]["record_slot_ids_hash"],
        },
        "per_case_inputs": case_rows,
        "per_case_inputs_sha256": payload_sha256(case_rows),
    }
    freeze["freeze_sha256"] = payload_sha256(freeze)
    issues = validate_draft_input_freeze(
        freeze,
        expected_contract_drafter_config=contract_drafter_config,
        expected_slot_ledger=slot_ledger,
    )
    if issues:
        raise FreezeBuildError("invalid generated draft-input freeze: " + "; ".join(issues))
    return freeze


def validate_draft_input_freeze(
    payload: Mapping[str, Any],
    *,
    expected_contract_drafter_config: Mapping[str, Any] | None = None,
    expected_slot_ledger: Mapping[str, Any] | None = None,
) -> list[str]:
    """Return all internally detectable draft-input freeze violations."""

    issues: list[str] = []
    if not isinstance(payload, Mapping):
        return ["draft-input freeze must be a mapping"]
    if payload.get("schema_version") != FREEZE_SCHEMA_VERSION:
        issues.append(f"schema_version must be {FREEZE_SCHEMA_VERSION}")
    if payload.get("status") != "frozen":
        issues.append("sidecar status must be frozen")
    if payload.get("scope") != "androidworld_contract_draft_inputs_only":
        issues.append("scope must be androidworld_contract_draft_inputs_only")
    if payload.get("execution_eligible") is not False:
        issues.append("draft-input freeze must not be execution eligible")
    if payload.get("scoring_eligible") is not False:
        issues.append("draft-input freeze must not be scoring eligible")

    observed_freeze_hash = payload.get("freeze_sha256")
    if not _is_sha256(observed_freeze_hash):
        issues.append("freeze_sha256 must be a sha256")
    else:
        hash_input = dict(payload)
        hash_input.pop("freeze_sha256", None)
        if observed_freeze_hash != payload_sha256(hash_input):
            issues.append("freeze_sha256 does not hash the payload excluding freeze_sha256")

    case_order = payload.get("case_order")
    cases: list[dict[str, Any]] = []
    if not isinstance(case_order, Mapping):
        issues.append("case_order must be a mapping")
    else:
        case_ids = case_order.get("case_unit_ids")
        task_ids = case_order.get("task_ids")
        if not _is_nonstring_sequence(case_ids) or len(case_ids) != CANDIDATE_CASE_COUNT:
            issues.append("case_order.case_unit_ids must contain exactly 116 IDs")
        if not _is_nonstring_sequence(task_ids) or len(task_ids) != CANDIDATE_CASE_COUNT:
            issues.append("case_order.task_ids must contain exactly 116 IDs")
        if _is_nonstring_sequence(case_ids) and _is_nonstring_sequence(task_ids):
            if len(set(str(value) for value in case_ids)) != CANDIDATE_CASE_COUNT:
                issues.append("case_order.case_unit_ids must be unique")
            if len(set(str(value) for value in task_ids)) != CANDIDATE_CASE_COUNT:
                issues.append("case_order.task_ids must be unique")
            if case_order.get("case_unit_ids_hash") != canonical_string_list_hash(case_ids):
                issues.append("case_order.case_unit_ids_hash mismatch")
            if case_order.get("task_ids_hash") != canonical_string_list_hash(task_ids):
                issues.append("case_order.task_ids_hash mismatch")
            cases = [
                {
                    "selection_rank": rank,
                    "case_unit_id": str(case_id),
                    "task_id": str(task_id),
                }
                for rank, (case_id, task_id) in enumerate(zip(case_ids, task_ids, strict=False))
            ]
            if case_order.get("case_identity_sha256") != payload_sha256(cases):
                issues.append("case_order.case_identity_sha256 mismatch")
        for field, expected in (
            ("selection_rank_start", 0),
            ("selection_rank_end_exclusive", CANDIDATE_CASE_COUNT),
            ("case_count", CANDIDATE_CASE_COUNT),
            ("official100_count", OFFICIAL_CASE_COUNT),
            ("extra16_count", EXTRA_CASE_COUNT),
        ):
            if case_order.get(field) != expected:
                issues.append(f"case_order.{field} must be {expected}")

    rows = payload.get("per_case_inputs")
    if not _is_nonstring_sequence(rows):
        issues.append("per_case_inputs must be a sequence")
    elif cases:
        try:
            normalized_rows = _normalize_per_case_inputs(rows, cases)
        except FreezeBuildError as exc:
            issues.append(f"per_case_inputs: {exc}")
        else:
            if list(rows) != normalized_rows:
                issues.append("per_case_inputs are not canonically normalized")
            if payload.get("per_case_inputs_sha256") != payload_sha256(normalized_rows):
                issues.append("per_case_inputs_sha256 mismatch")

    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, Mapping):
        issues.append("artifacts must be a mapping")
        artifacts = {}
    for field in ("packet_index", "source_bundle", "contract_drafter_config", "slot_ledger"):
        try:
            _validate_artifact_ref(artifacts.get(field), f"artifacts.{field}")
        except FreezeBuildError as exc:
            issues.append(str(exc))

    manifests = artifacts.get("manifests")
    if not isinstance(manifests, Mapping):
        issues.append("artifacts.manifests must be a mapping")
    elif cases:
        _validate_manifest_binding_relationships(manifests, cases, payload.get("slots"), issues)

    llm = payload.get("llm")
    if not isinstance(llm, Mapping):
        issues.append("llm must be a mapping")
    else:
        roles = llm.get("llm_roles")
        if not isinstance(roles, Mapping) or not isinstance(roles.get("contract_drafter"), Mapping):
            issues.append("llm.llm_roles requires contract_drafter")
        else:
            if _contains_placeholder(roles):
                issues.append("llm.llm_roles contains an unresolved placeholder")
            if llm.get("llm_roles_sha256") != payload_sha256(roles):
                issues.append("llm.llm_roles_sha256 mismatch")
            if llm.get("contract_drafter_role_sha256") != payload_sha256(roles["contract_drafter"]):
                issues.append("llm.contract_drafter_role_sha256 mismatch")
        config_artifact = artifacts.get("contract_drafter_config")
        if isinstance(config_artifact, Mapping):
            if llm.get("contract_drafter_config_sha256") != config_artifact.get("sha256"):
                issues.append("LLM config file hash disagrees with artifacts.contract_drafter_config")
            if (
                llm.get("contract_drafter_config_canonical_payload_sha256")
                != config_artifact.get("canonical_payload_sha256")
            ):
                issues.append("LLM config canonical payload hash disagrees with artifact binding")
        if expected_contract_drafter_config is not None:
            try:
                expected_role = project_contract_drafter_llm_role(expected_contract_drafter_config)
            except FreezeBuildError as exc:
                issues.append(f"expected contract drafter config: {exc}")
            else:
                if not isinstance(roles, Mapping) or roles.get("contract_drafter") != expected_role:
                    issues.append("frozen contract_drafter role disagrees with expected config")
                expected_config_hash = payload_sha256(expected_contract_drafter_config)
                if llm.get("contract_drafter_config_canonical_payload_sha256") != expected_config_hash:
                    issues.append("frozen config canonical hash disagrees with expected config")

    slots = payload.get("slots")
    expected_slot_fields = {
        "candidate116_record_slot_count": CANDIDATE_SLOT_COUNT,
        "candidate116_record_slot_ids_hash": EXPECTED_CANDIDATE116_SLOT_HASH,
        "official100_record_slot_count": OFFICIAL_SLOT_COUNT,
        "official100_record_slot_ids_hash": EXPECTED_OFFICIAL100_SLOT_HASH,
        "extra16_record_slot_count": EXTRA_SLOT_COUNT,
        "extra16_record_slot_ids_hash": EXPECTED_EXTRA16_SLOT_HASH,
    }
    if not isinstance(slots, Mapping):
        issues.append("slots must be a mapping")
    else:
        for field, expected in expected_slot_fields.items():
            if slots.get(field) != expected:
                issues.append(f"slots.{field} mismatch")
        ledger_artifact = artifacts.get("slot_ledger")
        if isinstance(ledger_artifact, Mapping) and slots.get("ledger_sha256") != ledger_artifact.get("ledger_sha256"):
            issues.append("slots.ledger_sha256 disagrees with artifact binding")
    if expected_slot_ledger is not None:
        ledger_issues = validate_candidate116_slot_ledger(expected_slot_ledger)
        issues.extend(f"expected slot ledger: {issue}" for issue in ledger_issues)
        if isinstance(slots, Mapping):
            if slots.get("ledger_sha256") != expected_slot_ledger.get("ledger_sha256"):
                issues.append("frozen ledger_sha256 disagrees with expected ledger")
            if slots.get("ledger_id") != expected_slot_ledger.get("ledger_id"):
                issues.append("frozen ledger_id disagrees with expected ledger")

    assertions = payload.get("prelock_assertions")
    required_assertions = {
        "manifests_remain_draft": True,
        "contract_locks_expected_empty": True,
        "contracts_expected": CANDIDATE_CASE_COUNT,
        "draft_calls_expected": CANDIDATE_CASE_COUNT,
        "androidworld_execution_requires_later_locked_manifest": True,
    }
    if not isinstance(assertions, Mapping):
        issues.append("prelock_assertions must be a mapping")
    else:
        for field, expected in required_assertions.items():
            if assertions.get(field) != expected:
                issues.append(f"prelock_assertions.{field} must be {expected!r}")
    return _dedupe(issues)


def _normalize_ordered_cases(
    ordered_cases: Sequence[Mapping[str, Any]] | Any,
) -> list[dict[str, Any]]:
    if not _is_nonstring_sequence(ordered_cases):
        raise FreezeBuildError("ordered_cases must be a sequence")
    if len(ordered_cases) != CANDIDATE_CASE_COUNT:
        raise FreezeBuildError(f"ordered_cases must contain exactly {CANDIDATE_CASE_COUNT} cases")
    normalized: list[dict[str, Any]] = []
    for rank, item in enumerate(ordered_cases):
        if not isinstance(item, Mapping):
            raise FreezeBuildError(f"ordered_cases[{rank}] must be a mapping")
        declared_rank = item.get("selection_rank")
        if declared_rank != rank:
            raise FreezeBuildError(
                f"ordered_cases[{rank}].selection_rank must be {rank}, observed {declared_rank!r}"
            )
        normalized.append(
            {
                "selection_rank": rank,
                "case_unit_id": _required_text(item, "case_unit_id", f"ordered_cases[{rank}]"),
                "task_id": _required_text(item, "task_id", f"ordered_cases[{rank}]"),
            }
        )
    case_ids = [item["case_unit_id"] for item in normalized]
    task_ids = [item["task_id"] for item in normalized]
    if len(case_ids) != len(set(case_ids)):
        raise FreezeBuildError("ordered_cases case_unit_id values must be unique")
    if len(task_ids) != len(set(task_ids)):
        raise FreezeBuildError("ordered_cases task_id values must be unique")
    return normalized


def _build_slot_rows(
    cases: Sequence[Mapping[str, Any]],
    *,
    domain: str,
    agent_ids: Sequence[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    slot_ids: list[str] = []
    for case in cases:
        rank = int(case["selection_rank"])
        group = "official100" if rank < OFFICIAL_CASE_COUNT else "extra16"
        for agent_index, agent_id in enumerate(agent_ids):
            safe_agent = safe_id(str(agent_id).lower().replace(" ", "_"))
            record_slot_id = f"slot-{domain}-{safe_id(case['case_unit_id'])}-{safe_agent}"
            slot_index = len(rows)
            rows.append(
                {
                    "slot_index": slot_index,
                    "record_slot_id": record_slot_id,
                    "domain": domain,
                    "case_unit_id": case["case_unit_id"],
                    "task_id": case["task_id"],
                    "selection_rank": rank,
                    "agent_id": str(agent_id),
                    "agent_index": agent_index,
                    "group": group,
                    "subset_slot_index": slot_index
                    if group == "official100"
                    else slot_index - OFFICIAL_SLOT_COUNT,
                }
            )
            slot_ids.append(record_slot_id)
    return rows, slot_ids


def _slot_subset(
    slot_ids: Sequence[str],
    *,
    case_start: int,
    case_end_exclusive: int,
    parent_slot_start: int,
) -> dict[str, Any]:
    values = [str(value) for value in slot_ids]
    return {
        "case_rank_start": case_start,
        "case_rank_end_exclusive": case_end_exclusive,
        "case_count": case_end_exclusive - case_start,
        "parent_slot_index_start": parent_slot_start,
        "parent_slot_index_end_exclusive": parent_slot_start + len(values),
        "record_slot_count": len(values),
        "record_slot_ids": values,
        "record_slot_ids_hash": canonical_string_list_hash(values),
    }


def _normalize_per_case_inputs(
    per_case_inputs: Sequence[Mapping[str, Any]] | Any,
    cases: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if not _is_nonstring_sequence(per_case_inputs):
        raise FreezeBuildError("per_case_inputs must be a sequence")
    if len(per_case_inputs) != CANDIDATE_CASE_COUNT:
        raise FreezeBuildError("per_case_inputs must contain exactly 116 rows")
    required_hashes = (
        "case_packet_sha256",
        "raw_case_manifest_sha256",
        "source_closure_sha256",
        "source_bundle_item_sha256",
        "semantic_source_context_sha256",
        "rendered_prompt_sha256",
    )
    normalized: list[dict[str, Any]] = []
    contract_ids: list[str] = []
    for rank, (row, case) in enumerate(zip(per_case_inputs, cases, strict=True)):
        if not isinstance(row, Mapping):
            raise FreezeBuildError(f"per_case_inputs[{rank}] must be a mapping")
        expected_group = "official100" if rank < OFFICIAL_CASE_COUNT else "extra16"
        if row.get("selection_rank") != rank:
            raise FreezeBuildError(f"per_case_inputs[{rank}].selection_rank mismatch")
        if row.get("group") != expected_group:
            raise FreezeBuildError(f"per_case_inputs[{rank}].group must be {expected_group}")
        if row.get("case_unit_id") != case["case_unit_id"] or row.get("task_id") != case["task_id"]:
            raise FreezeBuildError(f"per_case_inputs[{rank}] identity/order mismatch")
        normalized_row = {
            "selection_rank": rank,
            "group": expected_group,
            "case_unit_id": case["case_unit_id"],
            "task_id": case["task_id"],
            "contract_id": _required_text(row, "contract_id", f"per_case_inputs[{rank}]"),
            "case_packet_path": _required_text(row, "case_packet_path", f"per_case_inputs[{rank}]"),
            "case_packet_sha256": _required_hash(row, "case_packet_sha256", f"per_case_inputs[{rank}]"),
            "raw_case_manifest_path": _required_text(
                row,
                "raw_case_manifest_path",
                f"per_case_inputs[{rank}]",
            ),
            "raw_case_manifest_sha256": _required_hash(
                row,
                "raw_case_manifest_sha256",
                f"per_case_inputs[{rank}]",
            ),
            "source_closure_sha256": _required_hash(
                row,
                "source_closure_sha256",
                f"per_case_inputs[{rank}]",
            ),
            "source_bundle_item_sha256": _required_hash(
                row,
                "source_bundle_item_sha256",
                f"per_case_inputs[{rank}]",
            ),
            "semantic_source_context_sha256": _required_hash(
                row,
                "semantic_source_context_sha256",
                f"per_case_inputs[{rank}]",
            ),
            "rendered_prompt_sha256": _required_hash(
                row,
                "rendered_prompt_sha256",
                f"per_case_inputs[{rank}]",
            ),
        }
        for field in required_hashes:
            if not _is_sha256(normalized_row[field]):
                raise FreezeBuildError(f"per_case_inputs[{rank}].{field} must be a sha256")
        normalized.append(normalized_row)
        contract_ids.append(normalized_row["contract_id"])
    if len(contract_ids) != len(set(contract_ids)):
        raise FreezeBuildError("per_case_inputs contract_id values must be unique")
    return normalized


def _normalize_manifest_bindings(
    bindings: Mapping[str, Mapping[str, Any]],
    cases: Sequence[Mapping[str, Any]],
    slot_ledger: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(bindings, Mapping):
        raise FreezeBuildError("manifest_bindings must be a mapping")
    if set(bindings) != {"candidate116", "extra16"}:
        raise FreezeBuildError("manifest_bindings must contain exactly candidate116 and extra16")
    normalized = copy.deepcopy(dict(bindings))
    slots = {
        "candidate116_record_slot_ids_hash": slot_ledger["record_slot_ids_hash"],
        "extra16_record_slot_ids_hash": slot_ledger["subsets"]["extra16"]["record_slot_ids_hash"],
    }
    issues: list[str] = []
    _validate_manifest_binding_relationships(normalized, list(cases), slots, issues)
    if issues:
        raise FreezeBuildError("; ".join(issues))
    return normalized


def _validate_manifest_binding_relationships(
    manifests: Mapping[str, Any],
    cases: Sequence[Mapping[str, Any]],
    slots: Any,
    issues: list[str],
) -> None:
    expected_cases = {
        "candidate116": [case["case_unit_id"] for case in cases],
        "extra16": [case["case_unit_id"] for case in cases[OFFICIAL_CASE_COUNT:]],
    }
    expected_tasks = {
        "candidate116": [case["task_id"] for case in cases],
        "extra16": [case["task_id"] for case in cases[OFFICIAL_CASE_COUNT:]],
    }
    expected_slot_count = {"candidate116": CANDIDATE_SLOT_COUNT, "extra16": EXTRA_SLOT_COUNT}
    expected_slot_hash = {
        "candidate116": EXPECTED_CANDIDATE116_SLOT_HASH,
        "extra16": EXPECTED_EXTRA16_SLOT_HASH,
    }
    for name in ("candidate116", "extra16"):
        binding = manifests.get(name)
        if not isinstance(binding, Mapping):
            issues.append(f"artifacts.manifests.{name} must be a mapping")
            continue
        try:
            _validate_artifact_ref(binding, f"artifacts.manifests.{name}")
        except FreezeBuildError as exc:
            issues.append(str(exc))
        if binding.get("status") != "draft" or binding.get("prelock") is not True:
            issues.append(f"{name} binding must truthfully remain draft/prelock")
        if binding.get("contract_lock_count") != 0:
            issues.append(f"{name} binding must have zero contract locks")
        if binding.get("contract_locks_sha256") != EMPTY_LIST_HASH:
            issues.append(f"{name} contract_locks_sha256 must equal hash([])")
        if binding.get("case_unit_ids") != expected_cases[name]:
            issues.append(f"{name} case order/set mismatch")
        if binding.get("task_ids") != expected_tasks[name]:
            issues.append(f"{name} task order/set mismatch")
        if binding.get("case_unit_count") != len(expected_cases[name]):
            issues.append(f"{name} case_unit_count mismatch")
        if binding.get("case_unit_ids_hash") != canonical_string_list_hash(expected_cases[name]):
            issues.append(f"{name} case_unit_ids_hash mismatch")
        if binding.get("record_slot_count") != expected_slot_count[name]:
            issues.append(f"{name} record_slot_count mismatch")
        if binding.get("planned_record_slot_ids_hash") != expected_slot_hash[name]:
            issues.append(f"{name} planned_record_slot_ids_hash mismatch")
    if isinstance(slots, Mapping):
        if slots.get("candidate116_record_slot_ids_hash") != EXPECTED_CANDIDATE116_SLOT_HASH:
            issues.append("candidate manifest/ledger slot hash relationship mismatch")
        if slots.get("extra16_record_slot_ids_hash") != EXPECTED_EXTRA16_SLOT_HASH:
            issues.append("extra16 manifest/ledger slot hash relationship mismatch")


def _validate_contract_drafter_role(role: Mapping[str, Any]) -> None:
    missing = [field for field in _DRAFTER_ROLE_FIELDS if field not in role]
    if missing:
        raise FreezeBuildError(f"contract_drafter is missing fields: {missing}")
    for field in ("provider", "model", "model_version", "api_key_env", "prompt_version"):
        _required_text(role, field, "contract_drafter")
    if not _ENV_NAME_RE.fullmatch(str(role["api_key_env"])):
        raise FreezeBuildError("contract_drafter.api_key_env must be an environment variable name")
    if not _is_sha256(role["prompt_hash"]):
        raise FreezeBuildError("contract_drafter.prompt_hash must be a sha256")
    if role["prompt_hash_method"] != "sha256":
        raise FreezeBuildError("contract_drafter.prompt_hash_method must be sha256")
    if not isinstance(role["rate_limit"], Mapping):
        raise FreezeBuildError("contract_drafter.rate_limit must be a mapping")
    if _contains_placeholder(role):
        raise FreezeBuildError("contract_drafter role contains an unresolved placeholder")


def _case_value(container: Any, case_id: str, rank: int, label: str) -> Any:
    if isinstance(container, Mapping):
        if case_id not in container:
            raise FreezeBuildError(f"{label} has no value for {case_id}")
        return container[case_id]
    if _is_nonstring_sequence(container):
        if len(container) != CANDIDATE_CASE_COUNT:
            raise FreezeBuildError(f"{label} sequence must contain exactly 116 entries")
        return container[rank]
    raise FreezeBuildError(f"{label} must be keyed mapping or ordered sequence")


def _copy_artifact_ref(ref: Mapping[str, Any]) -> dict[str, str]:
    return {"path": str(ref["path"]), "sha256": str(ref["sha256"])}


def _validate_artifact_ref(ref: Any, label: str) -> None:
    if not isinstance(ref, Mapping):
        raise FreezeBuildError(f"{label} artifact ref must be a mapping")
    if not isinstance(ref.get("path"), str) or not ref.get("path"):
        raise FreezeBuildError(f"{label}.path must be non-empty")
    if not _is_sha256(ref.get("sha256")):
        raise FreezeBuildError(f"{label}.sha256 must be a lowercase sha256")


def _required_text(payload: Mapping[str, Any], field: str, label: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise FreezeBuildError(f"{label}.{field} must be a non-empty string")
    return value


def _required_hash(payload: Mapping[str, Any], field: str, label: str) -> str:
    value = payload.get(field)
    if not _is_sha256(value):
        raise FreezeBuildError(f"{label}.{field} must be a lowercase sha256")
    return str(value)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256_RE.fullmatch(value))


def _is_nonstring_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _contains_placeholder(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_placeholder(item) for item in value.values())
    if _is_nonstring_sequence(value):
        return any(_contains_placeholder(item) for item in value)
    if not isinstance(value, str):
        return False
    normalized = value.strip().casefold()
    if normalized in _PLACEHOLDER_TOKENS:
        return True
    return any(marker.casefold() in normalized for marker in _PLACEHOLDER_PHRASES)


def _dedupe(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(values))


__all__ = [
    "AGENT_IDS",
    "CANDIDATE_CASE_COUNT",
    "CANDIDATE_SLOT_COUNT",
    "DOMAIN",
    "EMPTY_LIST_HASH",
    "EXPECTED_CANDIDATE116_SLOT_HASH",
    "EXPECTED_EXTRA16_SLOT_HASH",
    "EXPECTED_OFFICIAL100_SLOT_HASH",
    "EXTRA_CASE_COUNT",
    "EXTRA_SLOT_COUNT",
    "FreezeBuildError",
    "OFFICIAL_CASE_COUNT",
    "OFFICIAL_SLOT_COUNT",
    "assert_known_slot_hashes",
    "build_candidate116_slot_ledger",
    "build_contract_drafter_config",
    "build_draft_input_freeze",
    "build_per_case_draft_bindings",
    "build_prelock_manifest_binding",
    "canonical_json_bytes",
    "canonical_string_list_hash",
    "payload_sha256",
    "project_contract_drafter_llm_role",
    "safe_id",
    "validate_candidate116_slot_ledger",
    "validate_draft_input_freeze",
]
