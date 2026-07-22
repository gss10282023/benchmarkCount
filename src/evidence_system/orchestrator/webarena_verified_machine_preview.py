"""Non-launchable 2,436-slot preview bound to machine-validated claim drafts."""

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
    DEFAULT_NATIVE_CLAIM_ACCEPTANCE,
    DEFAULT_NATIVE_CLAIM_INDEX,
    EXPECTED_AGENT_IDS,
    EXPECTED_CASE_COUNT,
    EXPECTED_MANIFEST_SHA256,
    EXPECTED_RECORD_SLOT_COUNT,
    EXPECTED_ROUTES,
    WebArenaFullScheduleError,
)


PREVIEW_INDEX_SCHEMA = "webarena_verified_machine_preview_schedule_index/v1"
PREVIEW_ACCEPTANCE_SCHEMA = "webarena_verified_machine_preview_acceptance/v1"
PREVIEW_MODE = "machine_preview_non_launchable"
DEFAULT_PREVIEW_INDEX = Path(
    "experiments/step20/webarena_verified/machine_preview_schedule_index.json"
)
DEFAULT_PREVIEW_ACCEPTANCE = Path(
    "experiments/step20/webarena_verified/machine_preview_schedule_acceptance.json"
)


def build_machine_preview(
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    native_claim_index_path: str | Path = DEFAULT_NATIVE_CLAIM_INDEX,
    native_claim_acceptance_path: str | Path = DEFAULT_NATIVE_CLAIM_ACCEPTANCE,
) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest_file = _file(manifest_path, "Step 19 manifest")
    native_index_file = _file(native_claim_index_path, "native claim index")
    native_acceptance_file = _file(
        native_claim_acceptance_path, "native claim acceptance"
    )
    for path in (manifest_file, native_index_file, native_acceptance_file):
        _sidecar(path)
    if sha256_file(manifest_file) != EXPECTED_MANIFEST_SHA256:
        raise WebArenaFullScheduleError("machine preview Step 19 manifest hash mismatch")
    manifest = _mapping(manifest_file)
    native_index = _mapping(native_index_file)
    native_acceptance = _mapping(native_acceptance_file)
    if native_index.get("path_scope") != "repository_relative":
        raise WebArenaFullScheduleError("machine preview index path scope is not repository-relative")
    if native_index.get("expected_count") != EXPECTED_CASE_COUNT:
        raise WebArenaFullScheduleError("machine preview native claim count is not 812")
    gate = native_acceptance.get("machine_contract_gate")
    if not isinstance(gate, Mapping):
        raise WebArenaFullScheduleError("machine preview has no machine contract gate")
    for field, expected in {
        "machine_locked": True,
        "machine_locked_count": EXPECTED_CASE_COUNT,
        "native_contract_count": EXPECTED_CASE_COUNT,
        "fallback_contract_count": 0,
        "formal_human_locked": False,
        "authorizes_formal_launch": False,
    }.items():
        if gate.get(field) != expected:
            raise WebArenaFullScheduleError(
                f"machine preview gate {field} mismatch: {gate.get(field)!r}"
            )
    if native_acceptance.get("formal_launch_eligible") is not False:
        raise WebArenaFullScheduleError("machine preview source incorrectly authorizes formal launch")
    if native_acceptance.get("index_sha256") != sha256_file(native_index_file):
        raise WebArenaFullScheduleError("machine preview acceptance/index hash mismatch")

    claim_cases_raw = native_index.get("cases")
    if not isinstance(claim_cases_raw, list) or len(claim_cases_raw) != EXPECTED_CASE_COUNT:
        raise WebArenaFullScheduleError("machine preview native index must contain 812 cases")
    claim_cases: dict[int, dict[str, Any]] = {}
    for position, raw in enumerate(claim_cases_raw):
        if not isinstance(raw, Mapping) or int(raw.get("task_id", -1)) != position:
            raise WebArenaFullScheduleError("machine preview native claim order changed")
        item = dict(raw)
        if item.get("human_signoff_status") != "pending":
            raise WebArenaFullScheduleError("machine preview contains a non-pending human claim")
        for path_field, hash_field in (
            ("draft_contract_path", "draft_contract_sha256"),
            ("machine_review_path", "machine_review_sha256"),
        ):
            path = _file(item.get(path_field), f"task {position} {path_field}")
            if item.get(hash_field) != sha256_file(path):
                raise WebArenaFullScheduleError(
                    f"machine preview task {position} {hash_field} mismatch"
                )
        for formal_field in (
            "contract_review_path",
            "contract_review_sha256",
            "locked_contract_path",
            "locked_contract_sha256",
            "locked_checklist_path",
            "locked_checklist_sha256",
        ):
            if item.get(formal_field) is not None:
                raise WebArenaFullScheduleError(
                    f"machine preview pending task {position} has formal field {formal_field}"
                )
        claim_cases[position] = item

    cases_raw = manifest.get("cases")
    slots_raw = manifest.get("record_slots")
    if not isinstance(cases_raw, list) or len(cases_raw) != EXPECTED_CASE_COUNT:
        raise WebArenaFullScheduleError("machine preview manifest cases are not 812")
    if not isinstance(slots_raw, list) or len(slots_raw) != EXPECTED_RECORD_SLOT_COUNT:
        raise WebArenaFullScheduleError("machine preview manifest slots are not 2,436")
    cases = {int(case["task_id"]): dict(case) for case in cases_raw}
    slots: list[dict[str, Any]] = []
    for position, raw in enumerate(slots_raw):
        if not isinstance(raw, Mapping):
            raise WebArenaFullScheduleError("machine preview contains a non-object slot")
        frozen = dict(raw)
        task_id = int(frozen["task_id"])
        agent_id = str(frozen["agent_id"])
        route = EXPECTED_ROUTES[agent_id]
        expected_slot = f"wv123-task-{task_id:03d}-agent-{agent_id[-1].lower()}"
        if frozen.get("record_slot_id") != expected_slot:
            raise WebArenaFullScheduleError(f"machine preview slot ID changed at {position}")
        if frozen.get("model") != route["model"] or frozen.get("server_id") != route["server_id"]:
            raise WebArenaFullScheduleError(f"machine preview route changed at {position}")
        claim = claim_cases[task_id]
        if claim.get("task_revision") != cases[task_id]["revision"]:
            raise WebArenaFullScheduleError(f"machine preview task {task_id} revision mismatch")
        if claim.get("manifest_source_task_sha256") != cases[task_id]["source_task_sha256"]:
            raise WebArenaFullScheduleError(f"machine preview task {task_id} source hash mismatch")
        slots.append(
            {
                "preview_ordinal": position + 1,
                **frozen,
                "ssh_host": route["ssh_host"],
                "ssh_user": route["ssh_user"],
                "ssh_host_ed25519_fingerprint": route[
                    "ssh_host_ed25519_fingerprint"
                ],
                "task_sites": list(cases[task_id]["sites"]),
                "reset_policy": "recreate_task_sites_from_digest_v1",
                "reset_receipt_relative_path": "reset_receipt.json",
                "machine_draft_contract_path": claim["draft_contract_path"],
                "machine_draft_contract_sha256": claim["draft_contract_sha256"],
                "machine_review_path": claim["machine_review_path"],
                "machine_review_sha256": claim["machine_review_sha256"],
                "human_signoff_status": "pending",
                "executable": False,
            }
        )

    index: dict[str, Any] = {
        "schema_version": PREVIEW_INDEX_SCHEMA,
        "mode": PREVIEW_MODE,
        "status": "blocked",
        "formal_launch_eligible": False,
        "executable": False,
        "inputs": {
            "step19_manifest_path": _display(manifest_file),
            "step19_manifest_sha256": sha256_file(manifest_file),
            "native_claim_index_path": _display(native_index_file),
            "native_claim_index_sha256": sha256_file(native_index_file),
            "native_claim_acceptance_path": _display(native_acceptance_file),
            "native_claim_acceptance_sha256": sha256_file(native_acceptance_file),
        },
        "counts": {
            "requested_cases": EXPECTED_CASE_COUNT,
            "preview_cases": EXPECTED_CASE_COUNT,
            "requested_record_slots": EXPECTED_RECORD_SLOT_COUNT,
            "preview_record_slots": EXPECTED_RECORD_SLOT_COUNT,
            "formally_executable_record_slots": 0,
            "per_agent": dict(Counter(slot["agent_id"] for slot in slots)),
            "per_server": dict(Counter(slot["server_id"] for slot in slots)),
            "machine_draft_contracts": EXPECTED_CASE_COUNT,
            "human_locked_contracts": 0,
            "fallback_contracts": 0,
        },
        "record_slots": slots,
        "record_slots_sha256": sha256_object(slots),
        "blocking_reasons": list(native_acceptance.get("blockers") or []),
    }
    core = dict(index)
    index["integrity"] = {"core_sha256": sha256_object(core)}
    validate_machine_preview_index(index)
    acceptance = {
        "schema_version": PREVIEW_ACCEPTANCE_SCHEMA,
        "mode": PREVIEW_MODE,
        "status": "blocked",
        "formal_launch_eligible": False,
        "executable": False,
        "counts": dict(index["counts"]),
        "gates": {
            "exact_812_case_product": True,
            "exact_2436_slot_product": True,
            "agent_model_server_routes_exact": True,
            "paired_seed_policy_exact": True,
            "per_slot_reset_declared": True,
            "machine_draft_contracts_exact": True,
            "fallback_contracts_zero": True,
            "human_signoff_complete": False,
            "formal_locks_complete": False,
        },
        "blocking_reasons": list(index["blocking_reasons"]),
    }
    return index, acceptance


def validate_machine_preview_index(payload: Mapping[str, Any]) -> None:
    if payload.get("schema_version") != PREVIEW_INDEX_SCHEMA or payload.get("mode") != PREVIEW_MODE:
        raise WebArenaFullScheduleError("machine preview schema/mode mismatch")
    if payload.get("status") != "blocked" or payload.get("formal_launch_eligible") is not False:
        raise WebArenaFullScheduleError("machine preview must remain non-launchable")
    slots = payload.get("record_slots")
    if not isinstance(slots, list) or len(slots) != EXPECTED_RECORD_SLOT_COUNT:
        raise WebArenaFullScheduleError("machine preview must contain exactly 2,436 slots")
    if payload.get("record_slots_sha256") != sha256_object(slots):
        raise WebArenaFullScheduleError("machine preview slot hash mismatch")
    if len({slot.get("record_slot_id") for slot in slots}) != EXPECTED_RECORD_SLOT_COUNT:
        raise WebArenaFullScheduleError("machine preview slot IDs are not unique")
    counts = payload.get("counts")
    if not isinstance(counts, Mapping):
        raise WebArenaFullScheduleError("machine preview counts are missing")
    if counts.get("per_agent") != {agent: EXPECTED_CASE_COUNT for agent in EXPECTED_AGENT_IDS}:
        raise WebArenaFullScheduleError("machine preview per-agent count mismatch")
    if counts.get("formally_executable_record_slots") != 0 or counts.get("fallback_contracts") != 0:
        raise WebArenaFullScheduleError("machine preview executable/fallback counts are unsafe")
    integrity = payload.get("integrity")
    core = dict(payload)
    core.pop("integrity", None)
    if not isinstance(integrity, Mapping) or integrity.get("core_sha256") != sha256_object(core):
        raise WebArenaFullScheduleError("machine preview integrity hash mismatch")


def write_machine_preview(
    index: Mapping[str, Any],
    acceptance: Mapping[str, Any],
    *,
    index_path: str | Path = DEFAULT_PREVIEW_INDEX,
    acceptance_path: str | Path = DEFAULT_PREVIEW_ACCEPTANCE,
) -> tuple[Path, Path]:
    index_file = _atomic_json(index_path, index)
    acceptance_payload = dict(acceptance)
    acceptance_payload["index_path"] = _display(index_file)
    acceptance_payload["index_sha256"] = sha256_file(index_file)
    acceptance_file = _atomic_json(acceptance_path, acceptance_payload)
    return index_file, acceptance_file


def _atomic_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    destination = resolve_repo_path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    destination.with_name(destination.name + ".sha256").write_text(
        f"{sha256_file(destination)}  {destination.name}\n", encoding="utf-8"
    )
    return destination


def _file(value: Any, label: str) -> Path:
    if not isinstance(value, (str, Path)) or not str(value):
        raise WebArenaFullScheduleError(f"{label} path is missing")
    path = resolve_repo_path(value)
    if not path.is_file() or path.is_symlink():
        raise WebArenaFullScheduleError(f"{label} is missing or unsafe: {path}")
    return path


def _mapping(path: Path) -> dict[str, Any]:
    payload = load_json_or_yaml(path)
    if not isinstance(payload, Mapping):
        raise WebArenaFullScheduleError(f"expected JSON object: {path}")
    return dict(payload)


def _sidecar(path: Path) -> None:
    sidecar = path.with_name(path.name + ".sha256")
    expected = f"{sha256_file(path)}  {path.name}\n"
    if not sidecar.is_file() or sidecar.read_text(encoding="utf-8") != expected:
        raise WebArenaFullScheduleError(f"invalid SHA-256 sidecar: {sidecar}")


def _display(path: Path) -> str:
    root = resolve_repo_path(".").resolve()
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path.resolve())
