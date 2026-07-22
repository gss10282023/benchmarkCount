"""Frozen 8-task/24-slot WebArena-Verified pilot manifest builder."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml
from evidence_system.orchestrator.webarena_verified_full import (
    DEFAULT_MANIFEST,
    DEFAULT_TASK_CONTRACT_INDEX,
    EXPECTED_AGENT_IDS,
    EXPECTED_MANIFEST_SHA256,
    EXPECTED_ROUTES,
    EXPECTED_TASK_CONTRACT_INDEX_SHA256,
    WebArenaFullScheduleError,
)


PILOT_SCHEMA_VERSION = "webarena_verified_pilot_8x3_manifest/v1"
PILOT_TASK_IDS = (0, 21, 389, 399, 369, 97, 759, 681)
PILOT_AGENT_ORDERS = (
    ("Agent A", "Agent B", "Agent C"),
    ("Agent B", "Agent C", "Agent A"),
    ("Agent C", "Agent A", "Agent B"),
    ("Agent A", "Agent C", "Agent B"),
    ("Agent B", "Agent A", "Agent C"),
    ("Agent C", "Agent B", "Agent A"),
    ("Agent A", "Agent B", "Agent C"),
    ("Agent B", "Agent C", "Agent A"),
)
DEFAULT_PILOT_MANIFEST = Path(
    "experiments/step20/webarena_verified/pilot_manifest.json"
)


def build_pilot_manifest(
    *,
    full_manifest_path: str | Path = DEFAULT_MANIFEST,
    task_contract_index_path: str | Path = DEFAULT_TASK_CONTRACT_INDEX,
) -> dict[str, Any]:
    full_path = resolve_repo_path(full_manifest_path)
    contract_path = resolve_repo_path(task_contract_index_path)
    if sha256_file(full_path) != EXPECTED_MANIFEST_SHA256:
        raise WebArenaFullScheduleError("pilot input Step 19 manifest hash mismatch")
    if sha256_file(contract_path) != EXPECTED_TASK_CONTRACT_INDEX_SHA256:
        raise WebArenaFullScheduleError("pilot input task contract index hash mismatch")
    full = load_json_or_yaml(full_path)
    task_index = load_json_or_yaml(contract_path)
    if not isinstance(full, Mapping) or not isinstance(task_index, Mapping):
        raise WebArenaFullScheduleError("pilot inputs must be JSON objects")
    full_cases = {
        int(case["task_id"]): dict(case)
        for case in list(full.get("cases") or [])
        if isinstance(case, Mapping)
    }
    contracts = {
        int(entry["task_id"]): dict(entry)
        for entry in list(task_index.get("entries") or [])
        if isinstance(entry, Mapping)
    }
    if set(PILOT_TASK_IDS) - set(full_cases) or set(PILOT_TASK_IDS) - set(contracts):
        raise WebArenaFullScheduleError("one or more frozen pilot tasks are missing")

    cases: list[dict[str, Any]] = []
    slots: list[dict[str, Any]] = []
    for ordinal, (task_id, agent_order) in enumerate(
        zip(PILOT_TASK_IDS, PILOT_AGENT_ORDERS, strict=True), start=1
    ):
        case = full_cases[task_id]
        contract = contracts[task_id]
        if int(case["revision"]) != int(contract["task_revision"]):
            raise WebArenaFullScheduleError(f"pilot task {task_id} revision mismatch")
        if list(case["sites"]) != list(contract["sites"]):
            raise WebArenaFullScheduleError(f"pilot task {task_id} site mismatch")
        seed = 123000 + task_id
        cases.append(
            {
                "pilot_ordinal": ordinal,
                "task_id": task_id,
                "revision": int(case["revision"]),
                "task_type": str(contract["task_type"]),
                "sites": list(case["sites"]),
                "source_task_sha256": case["source_task_sha256"],
                "evaluator_names_in_order": list(contract["evaluator_names_in_order"]),
                "agent_order": list(agent_order),
                "paired_seed": seed,
                "special_auth_coverage": task_id == 759,
            }
        )
        for within_task_order, agent_id in enumerate(agent_order, start=1):
            route = EXPECTED_ROUTES[agent_id]
            slots.append(
                {
                    "pilot_slot_ordinal": len(slots) + 1,
                    "within_task_order": within_task_order,
                    "record_slot_id": (
                        f"wv123-pilot-task-{task_id:03d}-agent-{agent_id[-1].lower()}"
                    ),
                    "task_id": task_id,
                    "revision": int(case["revision"]),
                    "agent_id": agent_id,
                    "model": route["model"],
                    "server_id": route["server_id"],
                    "seed": seed,
                }
            )

    payload: dict[str, Any] = {
        "schema_version": PILOT_SCHEMA_VERSION,
        "status": "frozen",
        "benchmark": {
            "name": "WebArena-Verified",
            "version": "v1.2.3",
            "split": "pilot_preflight",
        },
        "inputs": {
            "full_manifest_path": _display(full_path),
            "full_manifest_sha256": sha256_file(full_path),
            "task_contract_index_path": _display(contract_path),
            "task_contract_index_sha256": sha256_file(contract_path),
        },
        "selection": {
            "task_ids": list(PILOT_TASK_IDS),
            "selection_rule": (
                "predeclared coverage of six sites, RETRIEVE/MUTATE/NAVIGATE, "
                "single-site, multi-site, network evaluators, and task 759 auth"
            ),
            "outcome_blind": True,
            "agent_order_policy": (
                "all six permutations once, then two predeclared balanced repeats"
            ),
            "formal_run_slots_reused": False,
        },
        "run_policy": {
            "case_order": "exact selection.task_ids order",
            "paired_seed": True,
            "concurrency_per_server": 1,
            "cross_server_parallelism": 3,
            "reset_before_every_slot": True,
            "reset_policy": "recreate_task_sites_from_digest_v1",
            "fallback_contracts": 0,
            "advance_to_full_only_after_pilot_acceptance": True,
        },
        "counts": {
            "cases": len(cases),
            "record_slots": len(slots),
            "per_agent": dict(Counter(slot["agent_id"] for slot in slots)),
            "fallback_contracts": 0,
        },
        "coverage": {
            "sites": sorted({site for case in cases for site in case["sites"]}),
            "task_types": sorted({case["task_type"] for case in cases}),
            "multi_site_task_ids": [
                case["task_id"] for case in cases if len(case["sites"]) > 1
            ],
            "network_evaluator_task_ids": [
                case["task_id"]
                for case in cases
                if "NetworkEventEvaluator" in case["evaluator_names_in_order"]
            ],
            "special_auth_task_ids": [759],
        },
        "cases": cases,
        "record_slots": slots,
        "cases_sha256": sha256_object(cases),
        "record_slots_sha256": sha256_object(slots),
    }
    core = dict(payload)
    payload["integrity"] = {"core_sha256": sha256_object(core)}
    validate_pilot_manifest(payload)
    return payload


def validate_pilot_manifest(payload: Mapping[str, Any]) -> None:
    if payload.get("schema_version") != PILOT_SCHEMA_VERSION:
        raise WebArenaFullScheduleError("pilot manifest schema mismatch")
    if payload.get("status") != "frozen":
        raise WebArenaFullScheduleError("pilot manifest is not frozen")
    integrity = payload.get("integrity")
    if not isinstance(integrity, Mapping):
        raise WebArenaFullScheduleError("pilot manifest integrity block is missing")
    core = dict(payload)
    core.pop("integrity", None)
    if integrity.get("core_sha256") != sha256_object(core):
        raise WebArenaFullScheduleError("pilot manifest core hash mismatch")
    cases = payload.get("cases")
    slots = payload.get("record_slots")
    if not isinstance(cases, list) or len(cases) != 8:
        raise WebArenaFullScheduleError("pilot manifest must contain exactly eight cases")
    if not isinstance(slots, list) or len(slots) != 24:
        raise WebArenaFullScheduleError("pilot manifest must contain exactly 24 slots")
    if [case.get("task_id") for case in cases] != list(PILOT_TASK_IDS):
        raise WebArenaFullScheduleError("pilot task order changed")
    if [case.get("agent_order") for case in cases] != [
        list(order) for order in PILOT_AGENT_ORDERS
    ]:
        raise WebArenaFullScheduleError("pilot agent counterbalance order changed")
    if payload.get("cases_sha256") != sha256_object(cases):
        raise WebArenaFullScheduleError("pilot cases hash mismatch")
    if payload.get("record_slots_sha256") != sha256_object(slots):
        raise WebArenaFullScheduleError("pilot slots hash mismatch")
    expected_slots: list[tuple[int, str, int]] = []
    for task_id, order in zip(PILOT_TASK_IDS, PILOT_AGENT_ORDERS, strict=True):
        expected_slots.extend((task_id, agent, 123000 + task_id) for agent in order)
    observed = [
        (int(slot.get("task_id", -1)), str(slot.get("agent_id")), int(slot.get("seed", -1)))
        for slot in slots
    ]
    if observed != expected_slots:
        raise WebArenaFullScheduleError("pilot task/agent/paired-seed schedule changed")
    if len({slot.get("record_slot_id") for slot in slots}) != 24:
        raise WebArenaFullScheduleError("pilot record-slot IDs are not unique")
    for slot in slots:
        agent_id = str(slot["agent_id"])
        route = EXPECTED_ROUTES[agent_id]
        if slot.get("server_id") != route["server_id"] or slot.get("model") != route["model"]:
            raise WebArenaFullScheduleError("pilot agent/model/server route changed")
    counts = payload.get("counts")
    if not isinstance(counts, Mapping):
        raise WebArenaFullScheduleError("pilot counts are missing")
    if counts.get("cases") != 8 or counts.get("record_slots") != 24:
        raise WebArenaFullScheduleError("pilot counts changed")
    if counts.get("per_agent") != {agent: 8 for agent in EXPECTED_AGENT_IDS}:
        raise WebArenaFullScheduleError("pilot per-agent counts changed")
    if counts.get("fallback_contracts") != 0:
        raise WebArenaFullScheduleError("pilot fallback contracts are forbidden")


def write_pilot_manifest(
    payload: Mapping[str, Any], *, output_path: str | Path = DEFAULT_PILOT_MANIFEST
) -> Path:
    destination = resolve_repo_path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    fd, temporary = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=str(destination.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    sidecar = destination.with_name(destination.name + ".sha256")
    sidecar.write_text(
        f"{sha256_file(destination)}  {destination.name}\n", encoding="utf-8"
    )
    return destination


def _display(path: Path) -> str:
    root = resolve_repo_path(".").resolve()
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path.resolve())
