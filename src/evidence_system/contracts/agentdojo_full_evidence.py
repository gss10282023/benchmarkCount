"""Blind evidence acceptance, promotion, and pre-score join for AgentDojo full.

This module deliberately keeps raw execution independent from checklist review:

* execution writes only to the execution-lock staging namespace;
* acceptance hashes every byte but projects only non-outcome run metadata;
* promotion is allowed only after the final checklist freeze exists;
* scoring is authorized only by a join lock binding all prior immutable objects.

No function in this module deserializes native evaluator outputs, trace files,
proxy calls, or native outcome fields from ``raw_run.json``.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
import base64
import ctypes
from dataclasses import dataclass
from datetime import datetime, timezone
import errno
import json
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
from typing import Any, Callable
import uuid

from evidence_system.adapters.agentdojo_remote_inventory import (
    COMPLETION_INDEX_ENTRY_FIELDS,
    COMPLETION_MARKER_FIELDS,
)
from evidence_system.adapters.agentdojo_runtime_control import job_identity_sha256
from evidence_system.adapters.runtime import formal_job_binding_sha256
from evidence_system.contracts.agentdojo_full_execution import (
    DEFAULT_EXECUTION_LOCK,
    verify_execution_lock,
    verify_execution_lock_envelope,
    verify_job_binding,
)
from evidence_system.contracts.agentdojo_checklist_freeze_v2 import (
    DEFAULT_CHECKLIST_FREEZE_V2,
    DEFAULT_QUIESCENCE_MAX_AGE_SECONDS,
    ChecklistFreezeV2Result,
    verify_checklist_freeze_v2,
    verify_review_quiescence_receipt,
)
from evidence_system.contracts.agentdojo_full_experiment import (
    DEFAULT_SCORE_NAMESPACE_ROOTS,
    DEFAULT_SCORE_PROMPT,
    DEFAULT_SCORE_SCHEMA,
    DEFAULT_RESULT_NAMESPACE_LOCK,
    EXPECTED_AGENTS,
    EXPECTED_CASE_COUNT,
    EXPECTED_RECORD_SLOT_COUNT,
    EXPECTED_SUITE_COUNTS,
    EXPERIMENT_ROOT,
    RESULT_NAMESPACE,
)
from evidence_system.contracts.common import (
    ContractLifecycleError,
    load_mapping,
    parse_timestamp,
)
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import repo_root, resolve_repo_path
from evidence_system.core.schemas import load_schema, validate_object


EVIDENCE_INDEX_SCHEMA_VERSION = "agentdojo_full_evidence_acceptance_index/v1"
PROMOTION_SCHEMA_VERSION = "agentdojo_full_evidence_promotion_receipt/v1"
PRESCORE_JOIN_SCHEMA_VERSION = "agentdojo_full_prescore_join_lock/v1"
SEALED_RETRIEVAL_SCHEMA_VERSION = "agentdojo_sealed_evidence_retrieval_receipt/v1"
EXECUTION_STAGING_NAMESPACE = "agentdojo_full_v1.2.2_direct_execution_staging"

DEFAULT_EVIDENCE_INDEX = EXPERIMENT_ROOT / "provenance/evidence_acceptance_index.json"
DEFAULT_PROMOTION_RECEIPT = (
    EXPERIMENT_ROOT / "provenance/evidence_promotion_receipt.json"
)
DEFAULT_PRESCORE_JOIN_LOCK = EXPERIMENT_ROOT / "lock/prescore_join_lock.json"
_QUIESCENCE_ROOT = EXPERIMENT_ROOT / "checklist_freeze/v2"
DEFAULT_RETRIEVAL_QUIESCENCE_RECEIPT = (
    _QUIESCENCE_ROOT / "retrieval_quiescence.json"
)
DEFAULT_ACCEPTANCE_QUIESCENCE_RECEIPT = (
    _QUIESCENCE_ROOT / "acceptance_quiescence.json"
)
DEFAULT_PROMOTION_QUIESCENCE_RECEIPT = (
    _QUIESCENCE_ROOT / "promotion_quiescence.json"
)
DEFAULT_JOIN_QUIESCENCE_RECEIPT = _QUIESCENCE_ROOT / "join_quiescence.json"
_FORMAL_EXECUTION_PROVENANCE_ROOT = (
    Path("results/namespaces") / EXECUTION_STAGING_NAMESPACE / "provenance"
)
DEFAULT_FORMAL_EXECUTION_COMPLETION_RECEIPT = (
    _FORMAL_EXECUTION_PROVENANCE_ROOT / "formal_execution_completion_receipt.json"
)
DEFAULT_FORMAL_EXECUTION_ANOMALY_RECEIPT = (
    _FORMAL_EXECUTION_PROVENANCE_ROOT / "formal_execution_anomaly_receipt.json"
)
DEFAULT_FORMAL_REMOTE_COMPLETION_INDEX = (
    _FORMAL_EXECUTION_PROVENANCE_ROOT / "formal_remote_completion_index.json"
)
DEFAULT_FORMAL_NAMESPACE_INIT_RECEIPT = (
    _FORMAL_EXECUTION_PROVENANCE_ROOT / "formal_execution_namespace_init_receipt.json"
)
DEFAULT_SEALED_EVIDENCE_RETRIEVAL_RECEIPT = (
    _FORMAL_EXECUTION_PROVENANCE_ROOT / "sealed_evidence_retrieval_receipt.json"
)
DEFAULT_CONTROLLER_REMOTE_SNAPSHOT_RECEIPT = (
    _FORMAL_EXECUTION_PROVENANCE_ROOT
    / "controller_remote_retrieval_snapshot_receipt.json"
)

_RAW_METADATA_FIELDS = frozenset(
    {
        "schema_version",
        "domain",
        "domain_display_name",
        "benchmark_name",
        "case_unit_id",
        "task_id",
        "record_slot_id",
        "record_id",
        "episode_ids",
        "run_id",
        "attempt_id",
        "final_attempt",
        "seed",
        "agent_id",
        "phase",
        "experiment_type",
        "priority",
        "status",
        "diagnostic_status",
        "appendix_failure_class",
        "artifact_manifest_path",
        "artifact_manifest_sha256",
        "raw_source_path",
        "machine_id",
        "git_commit_hash",
        "config_hash",
        "manifest_hash",
        "contract_id",
        "contract_version",
        "contract_hash",
        "taxonomy_version",
        "evidence_contract_id",
        "evidence_contract_version",
        "evidence_contract_hash",
        "execution_lock_sha256",
        "execution_policy_sha256",
        "openrouter_runtime_policy_sha256",
        "openrouter_runtime_policy_file_sha256",
    }
)
_JSON_NUMBER_RE = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")


@dataclass(frozen=True)
class LockedArtifactResult:
    path: Path
    sha256: str
    definition: dict[str, Any]
    created: bool


@dataclass(frozen=True)
class TreeInventory:
    root: Path
    files: tuple[dict[str, Any], ...]
    tree_sha256: str

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def total_bytes(self) -> int:
        return sum(int(item["size_bytes"]) for item in self.files)

    def by_path(self) -> dict[str, dict[str, Any]]:
        return {str(item["relative_path"]): dict(item) for item in self.files}


def _verify_execution_lock_for_evidence_phase(
    lock_path: str | Path, *, envelope_only: bool
) -> Any:
    """Select the execution verifier without weakening its public default.

    ``envelope_only`` is reserved for the post-promotion verifier after it has
    independently proved the immutable promotion receipt, namespace marker,
    and exact source/destination trees.  Retrieval, acceptance publication, and
    first promotion always use the strict reservation-only execution gate.
    """

    verifier = verify_execution_lock_envelope if envelope_only else verify_execution_lock
    return verifier(lock_path=lock_path)


def _verify_checklist_v2_quiescence_gate(
    *,
    checklist_freeze_lock_path: str | Path,
    review_quiescence_receipt_path: str | Path,
    quiescence_max_age_seconds: int | None,
) -> tuple[ChecklistFreezeV2Result, dict[str, Any]]:
    """Verify the immutable v2 freeze and a phase-specific quiescence receipt.

    Publication paths pass a finite maximum age.  Revalidation of an already
    immutable downstream object may pass ``None`` for historical freshness, but
    still recomputes the complete 949-case freeze, the draft-tree hash, host/boot
    identity, and live review-process quiescence.
    """

    checklist = verify_checklist_freeze_v2(freeze_path=checklist_freeze_lock_path)
    counts = _mapping(checklist.definition.get("counts"), "v2 checklist counts")
    _assert_equal(
        counts,
        {
            "case_packets": EXPECTED_CASE_COUNT,
            "source_entries": EXPECTED_CASE_COUNT,
            "valid_drafts": EXPECTED_CASE_COUNT,
            "accepted_drafts": EXPECTED_CASE_COUNT,
            "reviewed": EXPECTED_CASE_COUNT,
            "locked": EXPECTED_CASE_COUNT,
            "unresolved_drafts": 0,
        },
        "complete v2 checklist denominator",
    )
    frozen_quiescence = _mapping(
        checklist.definition.get("review_quiescence_receipt"),
        "v2 checklist quiescence binding",
    )
    current_quiescence = verify_review_quiescence_receipt(
        receipt_path=review_quiescence_receipt_path,
        max_age_seconds=quiescence_max_age_seconds,
        expected_draft_tree_sha256=str(
            frozen_quiescence.get("draft_tree_sha256") or ""
        ),
        require_process_quiescence=True,
    )
    return checklist, current_quiescence


def verify_sealed_evidence_retrieval_receipt(
    *,
    receipt_path: str | Path = DEFAULT_SEALED_EVIDENCE_RETRIEVAL_RECEIPT,
    execution_lock_path: str | Path = DEFAULT_EXECUTION_LOCK,
    checklist_freeze_lock_path: str | Path = DEFAULT_CHECKLIST_FREEZE_V2,
    review_quiescence_receipt_path: str
    | Path = DEFAULT_RETRIEVAL_QUIESCENCE_RECEIPT,
    quiescence_max_age_seconds: int
    | None = DEFAULT_QUIESCENCE_MAX_AGE_SECONDS,
    formal_completion_receipt_path: str
    | Path = DEFAULT_FORMAL_EXECUTION_COMPLETION_RECEIPT,
    remote_completion_index_path: str | Path = DEFAULT_FORMAL_REMOTE_COMPLETION_INDEX,
    _execution_envelope_only: bool = False,
) -> LockedArtifactResult:
    """Verify checklist-gated, atomic retrieval without opening evidence payloads.

    Only immutable control envelopes and byte inventories are materialized here.
    Raw run, trajectory, evaluator, and native-label files remain opaque.
    """

    # This gate intentionally precedes the first access to the retrieved tree.
    checklist, retrieval_quiescence = _verify_checklist_v2_quiescence_gate(
        checklist_freeze_lock_path=checklist_freeze_lock_path,
        review_quiescence_receipt_path=review_quiescence_receipt_path,
        quiescence_max_age_seconds=quiescence_max_age_seconds,
    )
    receipt_file = _regular_file(receipt_path, "sealed evidence retrieval receipt")
    if receipt_file != _regular_file(
        DEFAULT_SEALED_EVIDENCE_RETRIEVAL_RECEIPT,
        "canonical sealed evidence retrieval receipt",
    ):
        raise ContractLifecycleError(
            "sealed evidence retrieval receipt path is not canonical"
        )
    payload = load_mapping(receipt_file)
    _validate_sealed_retrieval_payload(payload)
    definition = _mapping(payload.get("definition"), "sealed retrieval definition")

    execution = _verify_execution_lock_for_evidence_phase(
        execution_lock_path, envelope_only=_execution_envelope_only
    )
    execution_file = _regular_file(execution.lock_path, "execution lock")
    _assert_equal(
        definition.get("execution_lock"),
        _path_lock(execution_file),
        "sealed retrieval execution lock",
    )
    execution_payload = load_mapping(execution_file)
    execution_locked_at = parse_timestamp(
        str(execution_payload.get("locked_at") or ""),
        "execution lock locked_at",
    )

    checklist_file = _regular_file(checklist.freeze_path, "v2 checklist freeze lock")
    _assert_equal(
        definition.get("checklist_freeze_lock"),
        _path_lock(checklist_file),
        "sealed retrieval v2 checklist freeze lock",
    )
    retrieval_quiescence_file = _regular_file(
        review_quiescence_receipt_path, "retrieval quiescence receipt"
    )
    _assert_equal(
        definition.get("review_quiescence_receipt"),
        _path_lock(retrieval_quiescence_file),
        "sealed retrieval quiescence receipt",
    )
    checklist_payload = load_mapping(checklist_file)
    checklist_frozen_at = parse_timestamp(
        str(checklist_payload.get("frozen_at") or ""),
        "v2 checklist freeze frozen_at",
    )
    retrieval_quiescence_at = parse_timestamp(
        str(retrieval_quiescence.get("created_at") or ""),
        "retrieval quiescence created_at",
    )

    completion_file = _regular_file(
        formal_completion_receipt_path, "formal execution completion receipt"
    )
    completion = load_mapping(completion_file)
    anomaly_file = _regular_file(
        completion.get("anomaly_receipt_path"), "formal blind anomaly receipt"
    )
    execution_receipts = _verify_formal_execution_receipts(
        completion_path=completion_file,
        anomaly_path=anomaly_file,
        execution_lock_path=execution_file,
        execution_lock_sha256=execution.lock_sha256,
        execution_policy_sha256=str(
            execution.definition.get("execution_policy_sha256") or ""
        ),
        remote_completion_index_path=remote_completion_index_path,
        execution_definition=execution.definition,
    )
    _assert_equal(
        definition.get("formal_completion_receipt"),
        execution_receipts["completion"],
        "sealed retrieval formal completion receipt",
    )
    completion_at = _formal_completion_timestamp(completion)

    remote_file = _regular_file(
        remote_completion_index_path, "formal remote completion index"
    )
    remote_index = load_mapping(remote_file)
    remote_entries = list(remote_index.get("entries") or [])
    expected_remote_binding = {
        **_path_lock(remote_file),
        "entry_count": EXPECTED_RECORD_SLOT_COUNT,
        "entries_sha256": sha256_object(remote_entries),
    }
    _assert_equal(
        definition.get("remote_completion_index"),
        expected_remote_binding,
        "sealed retrieval remote completion index",
    )
    _assert_equal(
        remote_index.get("entry_count"),
        EXPECTED_RECORD_SLOT_COUNT,
        "remote completion index entry count",
    )
    _assert_equal(
        remote_index.get("entries_sha256"),
        sha256_object(remote_entries),
        "remote completion index entries hash",
    )

    namespace_init = _verify_formal_namespace_init_receipt(
        definition.get("namespace_init_receipt"),
        execution=execution,
        _execution_envelope_only=_execution_envelope_only,
    )
    namespace_initialized_at = parse_timestamp(
        str(namespace_init.get("initialized_at") or ""),
        "formal namespace initialization timestamp",
    )

    snapshot_validation = _verify_controller_remote_snapshot_receipt(
        definition=definition,
        execution=execution,
        checklist=checklist,
        retrieval_quiescence_file=retrieval_quiescence_file,
        completion_file=completion_file,
        completion=completion,
        remote_index_file=remote_file,
        remote_index=remote_index,
    )
    controller_received_at = snapshot_validation["received_at"]

    retrieved_at = parse_timestamp(
        str(payload.get("retrieved_at") or ""), "sealed evidence retrieved_at"
    )
    if not (
        execution_locked_at < namespace_initialized_at
        and namespace_initialized_at <= completion_at
        and completion_at <= retrieval_quiescence_at
        and checklist_frozen_at <= retrieval_quiescence_at
        and retrieval_quiescence_at <= controller_received_at
        and controller_received_at < retrieved_at
    ):
        raise ContractLifecycleError("sealed evidence retrieval chronology is invalid")

    sealed_remote = _mapping(
        execution.definition.get("sealed_remote_evidence"),
        "execution sealed remote evidence",
    )
    remote_raw_root = str(sealed_remote.get("remote_raw_root") or "")
    if not Path(remote_raw_root).is_absolute():
        raise ContractLifecycleError("locked remote raw root must be absolute")
    _assert_equal(
        definition.get("remote_raw_root"),
        remote_raw_root,
        "sealed retrieval remote raw root",
    )
    remote_blind_root = str(sealed_remote.get("blind_aggregate_root") or "")
    if not Path(remote_blind_root).is_absolute():
        raise ContractLifecycleError("locked remote blind root must be absolute")
    _assert_equal(
        definition.get("remote_blind_root"),
        remote_blind_root,
        "sealed retrieval remote blind root",
    )

    output_precondition = _mapping(
        execution.definition.get("output_precondition"),
        "execution output precondition",
    )
    locked_local_root = _resolve_locked_path(
        output_precondition.get("staging_raw_result_root"),
        "execution staging raw result root",
    )
    _assert_declared_path(
        definition.get("local_staging_root"),
        locked_local_root,
        "sealed retrieval local staging root",
    )
    inventory = _tree_inventory(locked_local_root)
    expected_local_files = snapshot_validation["expected_local_files"]
    observed_local_files = [
        {
            "path": item["relative_path"],
            "sha256": item["sha256"],
            "size_bytes": item["size_bytes"],
        }
        for item in inventory.files
    ]
    _assert_equal(
        observed_local_files,
        expected_local_files,
        "sealed retrieval snapshot-to-local byte mapping",
    )
    _assert_equal(
        definition.get("local_inventory"),
        {
            "tree_sha256": inventory.tree_sha256,
            "file_count": inventory.file_count,
            "total_bytes": inventory.total_bytes,
        },
        "sealed retrieval local inventory",
    )
    _assert_equal(
        definition.get("counts"),
        {
            "cases": EXPECTED_CASE_COUNT,
            "record_slots": EXPECTED_RECORD_SLOT_COUNT,
            "native_trajectories": EXPECTED_RECORD_SLOT_COUNT * 3,
            "missing": 0,
            "duplicate": 0,
            "extra": 0,
            "hash_mismatch": 0,
        },
        "sealed retrieval denominator",
    )

    transfer = _mapping(definition.get("transfer"), "sealed retrieval transfer")
    _assert_equal(
        dict(transfer),
        {
            "temporary_root": transfer.get("temporary_root"),
            "atomic_rename": True,
            "destination_previously_absent": True,
            "symlink_count": 0,
            "hardlink_count": 0,
            "path_escape_count": 0,
            "transport": "rsync_single_hash_locked_tar_over_strict_ed25519",
            "rsync_delete_used": False,
            "remote_inventory_verified_before_transfer": True,
            "remote_pre_archive_post_inventory_identical": True,
            "archive_hash_verified_before_extraction": True,
            "regular_file_only_manual_extraction": True,
            "fsync_completed_before_publication": True,
            "rename_noreplace": True,
            "binding_to_job_id_mapping_sha256": snapshot_validation[
                "binding_to_job_id_mapping_sha256"
            ],
            "failed_attempt_archive_included": False,
        },
        "sealed retrieval transfer guarantees",
    )
    temporary_root = _resolve_locked_path(
        transfer.get("temporary_root"), "sealed retrieval temporary root"
    )
    if (
        temporary_root == locked_local_root
        or temporary_root.parent != locked_local_root.parent
    ):
        raise ContractLifecycleError(
            "sealed retrieval temporary root must be a distinct same-filesystem sibling"
        )
    hardlinks = [
        path
        for path in locked_local_root.rglob("*")
        if path.is_file() and path.stat().st_nlink > 1
    ]
    if hardlinks:
        raise ContractLifecycleError(
            f"sealed retrieval local evidence contains hardlinks: {hardlinks[:5]}"
        )

    return LockedArtifactResult(
        path=receipt_file,
        sha256=sha256_file(receipt_file),
        definition=definition,
        created=False,
    )


def _verify_controller_remote_snapshot_receipt(
    *,
    definition: Mapping[str, Any],
    execution: Any,
    checklist: ChecklistFreezeV2Result,
    retrieval_quiescence_file: Path,
    completion_file: Path,
    completion: Mapping[str, Any],
    remote_index_file: Path,
    remote_index: Mapping[str, Any],
) -> dict[str, Any]:
    """Verify the blind metadata and raw-tree hash graph behind one tar."""

    binding = _mapping(
        definition.get("controller_remote_snapshot_receipt"),
        "controller remote snapshot receipt binding",
    )
    controller_file = _regular_file(
        binding.get("path"), "controller remote snapshot receipt"
    )
    canonical_controller = _regular_file(
        DEFAULT_CONTROLLER_REMOTE_SNAPSHOT_RECEIPT,
        "canonical controller remote snapshot receipt",
    )
    _assert_equal(controller_file, canonical_controller, "controller receipt path")
    _assert_equal(binding, _path_lock(controller_file), "controller receipt binding")
    controller = load_mapping(controller_file)
    controller_fields = {
        "schema_version",
        "status",
        "received_at",
        "execution_lock",
        "checklist_freeze_lock",
        "review_quiescence_receipt",
        "formal_completion_receipt",
        "remote_completion_index",
        "known_hosts",
        "remote_inventory_helper",
        "request_sha256",
        "remote_receipt_sha256",
        "remote_receipt",
        "raw_bytes_transferred",
        "blind_only",
    }
    if set(controller) != controller_fields:
        raise ContractLifecycleError("controller remote snapshot fields differ")
    for actual, expected, label in (
        (
            controller.get("schema_version"),
            "agentdojo_controller_remote_retrieval_snapshot_receipt/v1",
            "schema",
        ),
        (
            controller.get("status"),
            "remote_snapshot_verified_before_transfer",
            "status",
        ),
        (controller.get("execution_lock"), _path_lock(execution.lock_path), "lock"),
        (
            controller.get("checklist_freeze_lock"),
            _path_lock(checklist.freeze_path),
            "checklist",
        ),
        (
            controller.get("review_quiescence_receipt"),
            _path_lock(retrieval_quiescence_file),
            "quiescence",
        ),
        (
            controller.get("formal_completion_receipt"),
            _path_lock(completion_file),
            "completion",
        ),
        (
            controller.get("remote_completion_index"),
            _path_lock(remote_index_file),
            "completion index",
        ),
        (controller.get("raw_bytes_transferred"), False, "raw transfer boundary"),
        (controller.get("blind_only"), True, "blind flag"),
    ):
        _assert_equal(actual, expected, f"controller remote snapshot {label}")
    received_at = parse_timestamp(
        str(controller.get("received_at") or ""), "controller snapshot received_at"
    )

    sealed = _mapping(
        execution.definition.get("sealed_remote_evidence"),
        "execution sealed remote evidence",
    )
    known_binding = _mapping(
        sealed.get("ssh_known_hosts_file"), "locked SSH known_hosts"
    )
    known_file = _regular_file(known_binding.get("path"), "locked SSH known_hosts")
    _assert_equal(known_binding, _path_lock(known_file), "current known_hosts binding")
    known_lines = [
        line.strip()
        for line in known_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if len(known_lines) != 1:
        raise ContractLifecycleError("known_hosts must contain exactly one host key")
    known_fields = known_lines[0].split()
    endpoint_token = (
        str(sealed.get("ssh_host"))
        if sealed.get("ssh_port") == 22
        else f"[{sealed.get('ssh_host')}]:{sealed.get('ssh_port')}"
    )
    if (
        len(known_fields) != 3
        or known_fields[0] != endpoint_token
        or known_fields[1] != "ssh-ed25519"
    ):
        raise ContractLifecycleError("known_hosts ED25519 endpoint differs")
    try:
        public_key = base64.b64decode(known_fields[2], validate=True)
    except ValueError as exc:
        raise ContractLifecycleError("known_hosts public key is malformed") from exc
    observed_fingerprint = "SHA256:" + base64.b64encode(
        hashlib.sha256(public_key).digest()
    ).decode("ascii").rstrip("=")
    _assert_equal(
        observed_fingerprint,
        sealed.get("ssh_host_ed25519_fingerprint"),
        "known_hosts fingerprint",
    )
    expected_known = {
        **known_binding,
        "fingerprint": sealed.get("ssh_host_ed25519_fingerprint"),
    }
    _assert_equal(
        controller.get("known_hosts"), expected_known, "controller known_hosts"
    )
    helper = _mapping(
        sealed.get("remote_inventory_helper"), "locked remote inventory helper"
    )
    helper_file = _regular_file(helper.get("path"), "remote inventory helper")
    if set(helper) != {"path", "remote_path", "sha256"}:
        raise ContractLifecycleError("remote inventory helper binding is not exact")
    _assert_equal(helper.get("sha256"), sha256_file(helper_file), "helper hash")
    _assert_equal(controller.get("remote_inventory_helper"), helper, "helper binding")

    blind_entries = _local_blind_metadata_entries(
        completion_file=completion_file,
        completion=completion,
        remote_index_file=remote_index_file,
    )
    entries = [dict(item) for item in list(remote_index.get("entries") or [])]
    request = {
        "schema_version": "agentdojo_remote_retrieval_snapshot_request/v1",
        "execution_lock_sha256": execution.lock_sha256,
        "execution_policy_sha256": execution.definition[
            "execution_policy_sha256"
        ],
        "remote_raw_root": sealed.get("remote_raw_root"),
        "remote_blind_root": sealed.get("blind_aggregate_root"),
        "retrieval_snapshot_root": sealed.get("retrieval_snapshot_root"),
        "retrieval_lifecycle_lock": sealed.get("retrieval_lifecycle_lock"),
        "entry_count": EXPECTED_RECORD_SLOT_COUNT,
        "entries_sha256": sha256_object(entries),
        "entries": entries,
        "blind_metadata_entry_count": 4,
        "blind_metadata_entries_sha256": sha256_object(blind_entries),
        "blind_metadata_entries": blind_entries,
    }
    _assert_equal(
        controller.get("request_sha256"),
        sha256_object(request),
        "controller snapshot request hash",
    )

    remote_receipt = _mapping(
        controller.get("remote_receipt"), "remote snapshot receipt"
    )
    _assert_equal(
        controller.get("remote_receipt_sha256"),
        sha256_object(remote_receipt),
        "controller remote receipt hash",
    )
    receipt_fields = {
        "schema_version",
        "status",
        "snapshot_id",
        "execution_lock_sha256",
        "execution_policy_sha256",
        "entries_sha256",
        "entry_count",
        "remote_raw_root",
        "remote_blind_root",
        "retrieval_lifecycle_lock",
        "archive",
        "source_inventory",
        "pre_post_inventory_identical",
        "lifecycle_flock",
        "fsync_completed",
        "failed_attempt_archive_included",
        "blind_only",
        "contains_case_agent_prompt_response_trajectory_evaluator_or_label",
    }
    if set(remote_receipt) != receipt_fields:
        raise ContractLifecycleError("remote snapshot receipt fields differ")
    for actual, expected, label in (
        (
            remote_receipt.get("schema_version"),
            "agentdojo_remote_retrieval_snapshot_receipt/v1",
            "schema",
        ),
        (
            remote_receipt.get("status"),
            "snapshot_verified_content_blind",
            "status",
        ),
        (remote_receipt.get("execution_lock_sha256"), execution.lock_sha256, "lock"),
        (
            remote_receipt.get("execution_policy_sha256"),
            execution.definition["execution_policy_sha256"],
            "policy",
        ),
        (remote_receipt.get("entries_sha256"), sha256_object(entries), "entries"),
        (remote_receipt.get("entry_count"), EXPECTED_RECORD_SLOT_COUNT, "count"),
        (remote_receipt.get("remote_raw_root"), sealed.get("remote_raw_root"), "raw root"),
        (
            remote_receipt.get("remote_blind_root"),
            sealed.get("blind_aggregate_root"),
            "blind root",
        ),
        (
            remote_receipt.get("retrieval_lifecycle_lock"),
            sealed.get("retrieval_lifecycle_lock"),
            "lifecycle lock",
        ),
        (remote_receipt.get("pre_post_inventory_identical"), True, "pre/post"),
        (remote_receipt.get("lifecycle_flock"), "exclusive", "flock"),
        (remote_receipt.get("fsync_completed"), True, "fsync"),
        (remote_receipt.get("failed_attempt_archive_included"), False, "failed attempts"),
        (remote_receipt.get("blind_only"), True, "blind flag"),
        (
            remote_receipt.get(
                "contains_case_agent_prompt_response_trajectory_evaluator_or_label"
            ),
            False,
            "content boundary",
        ),
    ):
        _assert_equal(actual, expected, f"remote snapshot receipt {label}")

    inventory = _mapping(
        remote_receipt.get("source_inventory"), "remote snapshot source inventory"
    )
    files = list(inventory.get("files") or [])
    if not all(
        isinstance(item, Mapping)
        and set(item) == {"path", "sha256", "size_bytes"}
        for item in files
    ):
        raise ContractLifecycleError("remote snapshot file inventory is malformed")
    normalized_files = [dict(item) for item in files]
    paths = [str(item.get("path") or "") for item in normalized_files]
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ContractLifecycleError("remote snapshot file paths are duplicate/unordered")
    for item in normalized_files:
        _safe_snapshot_relative(item.get("path"))
        if re.fullmatch(r"[a-f0-9]{64}", str(item.get("sha256") or "")) is None:
            raise ContractLifecycleError("remote snapshot file hash is invalid")
        size = item.get("size_bytes")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ContractLifecycleError("remote snapshot file size is invalid")

    blind_expected = {
        f"blind/{item['relative_path']}": {
            "path": f"blind/{item['relative_path']}",
            "sha256": item["sha256"],
            "size_bytes": item["size_bytes"],
        }
        for item in blind_entries
    }
    blind_observed = {
        str(item["path"]): item
        for item in normalized_files
        if str(item["path"]).startswith("blind/")
    }
    _assert_equal(blind_observed, blind_expected, "snapshot blind metadata files")

    raw_files = [
        item for item in normalized_files if str(item["path"]).startswith("raw/")
    ]
    binding_to_job_id = _binding_to_job_id_mapping(
        completion=completion,
        execution_lock_sha256=execution.lock_sha256,
        execution_policy_sha256=execution.definition["execution_policy_sha256"],
    )
    entry_by_binding = {
        str(item["job_binding_sha256"]): item for item in entries
    }
    raw_by_binding: dict[str, list[dict[str, Any]]] = {}
    for item in raw_files:
        parts = PurePosixPath(str(item["path"])).parts
        if len(parts) < 3 or parts[0] != "raw" or parts[1] not in entry_by_binding:
            raise ContractLifecycleError("snapshot raw path has an unknown binding")
        raw_by_binding.setdefault(parts[1], []).append(item)
    _assert_equal(
        set(raw_by_binding), set(entry_by_binding), "snapshot raw job directory set"
    )
    for binding_value, entry in entry_by_binding.items():
        rows = raw_by_binding[binding_value]
        marker_path = f"raw/{entry['completion_marker_relative_path']}"
        marker_rows = [item for item in rows if item["path"] == marker_path]
        if len(marker_rows) != 1:
            raise ContractLifecycleError("snapshot completion marker is missing")
        _assert_equal(
            marker_rows[0]["sha256"],
            entry["completion_marker_file_sha256"],
            "snapshot completion marker file hash",
        )
        artifacts = [item for item in rows if item["path"] != marker_path]
        projection = [
            {
                "path": PurePosixPath(str(item["path"])).relative_to(
                    PurePosixPath("raw", binding_value)
                ).as_posix(),
                "sha256": item["sha256"],
            }
            for item in artifacts
        ]
        _assert_equal(len(artifacts), entry["artifact_file_count"], "artifact count")
        _assert_equal(
            sha256_object(projection), entry["artifact_tree_sha256"], "artifact tree"
        )
        _assert_equal(
            sum(int(item["size_bytes"]) for item in artifacts),
            entry["artifact_total_bytes"],
            "artifact bytes",
        )

    projection = [
        {"path": item["path"], "sha256": item["sha256"]}
        for item in normalized_files
    ]
    expected_inventory = {
        "tree_sha256": sha256_object(projection),
        "file_count": len(normalized_files),
        "total_bytes": sum(int(item["size_bytes"]) for item in normalized_files),
        "files_sha256": sha256_object(normalized_files),
        "raw_file_count": len(raw_files),
        "blind_metadata_file_count": 4,
        "blind_metadata_entries_sha256": sha256_object(blind_entries),
        "files": normalized_files,
    }
    _assert_equal(inventory, expected_inventory, "remote source inventory aggregate")
    snapshot_id = sha256_object(
        {
            "schema_version": "agentdojo_remote_retrieval_snapshot_receipt/v1",
            "execution_lock_sha256": execution.lock_sha256,
            "entries_sha256": sha256_object(entries),
            "source_tree_sha256": inventory["tree_sha256"],
        }
    )
    _assert_equal(remote_receipt.get("snapshot_id"), snapshot_id, "snapshot id")
    archive = _mapping(remote_receipt.get("archive"), "remote snapshot archive")
    if set(archive) != {"path", "sha256", "size_bytes", "format"}:
        raise ContractLifecycleError("remote snapshot archive binding is not exact")
    _assert_equal(
        archive.get("path"),
        f"{sealed.get('retrieval_snapshot_root')}/{snapshot_id}.tar",
        "remote snapshot archive path",
    )
    if re.fullmatch(r"[a-f0-9]{64}", str(archive.get("sha256") or "")) is None:
        raise ContractLifecycleError("remote snapshot archive hash is invalid")
    if not isinstance(archive.get("size_bytes"), int) or archive["size_bytes"] < 1:
        raise ContractLifecycleError("remote snapshot archive size is invalid")
    _assert_equal(
        archive.get("format"),
        "tar_uncompressed_regular_files_only",
        "remote snapshot archive format",
    )

    expected_snapshot_binding = {
        "receipt_sha256": sha256_object(remote_receipt),
        "snapshot_id": snapshot_id,
        "archive_sha256": archive["sha256"],
        "archive_size_bytes": archive["size_bytes"],
        "source_tree_sha256": inventory["tree_sha256"],
        "source_file_count": inventory["file_count"],
        "source_total_bytes": inventory["total_bytes"],
        "source_raw_file_count": inventory["raw_file_count"],
        "source_blind_metadata_file_count": 4,
        "blind_metadata_entries_sha256": sha256_object(blind_entries),
    }
    _assert_equal(
        definition.get("remote_snapshot"),
        expected_snapshot_binding,
        "sealed retrieval remote snapshot binding",
    )
    expected_ssh = {
        "host": sealed.get("ssh_host"),
        "port": sealed.get("ssh_port"),
        "user": sealed.get("execution_user"),
        "host_key_algorithm": "ssh-ed25519",
        "host_fingerprint": sealed.get("ssh_host_ed25519_fingerprint"),
        "known_hosts": known_binding,
        "strict_host_key_checking": True,
        "password_authentication": False,
        "agent_forwarding": False,
    }
    _assert_equal(definition.get("ssh_transport"), expected_ssh, "SSH transport")
    controller_code = _regular_file(
        repo_root()
        / "src/evidence_system/cli/retrieve_agentdojo_full_evidence.py",
        "retrieval controller code",
    )
    _assert_equal(
        definition.get("retrieval_controller"),
        _path_lock(controller_code),
        "retrieval controller code binding",
    )

    expected_local_files: list[dict[str, Any]] = []
    for item in raw_files:
        parts = PurePosixPath(str(item["path"])).parts
        expected_local_files.append(
            {
                "path": PurePosixPath(
                    binding_to_job_id[parts[1]], *parts[2:]
                ).as_posix(),
                "sha256": item["sha256"],
                "size_bytes": item["size_bytes"],
            }
        )
    expected_local_files.sort(key=lambda item: str(item["path"]))
    return {
        "received_at": received_at,
        "expected_local_files": expected_local_files,
        "binding_to_job_id_mapping_sha256": sha256_object(binding_to_job_id),
    }


def _local_blind_metadata_entries(
    *,
    completion_file: Path,
    completion: Mapping[str, Any],
    remote_index_file: Path,
) -> list[dict[str, Any]]:
    root = completion_file.parent
    declared = {
        completion_file.name: completion_file,
        _safe_blind_relative(
            completion.get("completion_index_relative_path"), "completion index"
        ): remote_index_file,
        _safe_blind_relative(
            completion.get("completion_journal_relative_path"), "completion journal"
        ): None,
        _safe_blind_relative(
            completion.get("failed_attempt_journal_relative_path"),
            "failed-attempt journal",
        ): None,
    }
    if len(declared) != 4:
        raise ContractLifecycleError("blind metadata file set is not exactly four")
    entries: list[dict[str, Any]] = []
    for relative, supplied in sorted(declared.items()):
        file = _regular_file(root / relative, "local blind metadata file")
        if supplied is not None:
            _assert_equal(file, supplied, "local blind metadata canonical path")
        entries.append(
            {
                "relative_path": relative,
                "sha256": sha256_file(file),
                "size_bytes": file.stat().st_size,
            }
        )
    return entries


def _binding_to_job_id_mapping(
    *,
    completion: Mapping[str, Any],
    execution_lock_sha256: str,
    execution_policy_sha256: str,
) -> dict[str, str]:
    plan_path = _regular_file(
        EXPERIMENT_ROOT
        / "execution_plan"
        / execution_lock_sha256
        / "plan_index.json",
        "formal plan index",
    )
    _assert_equal(
        completion.get("plan_index_sha256"), sha256_file(plan_path), "plan hash"
    )
    plan = load_mapping(plan_path)
    entries = list(plan.get("entries") or [])
    if len(entries) != EXPECTED_RECORD_SLOT_COUNT:
        raise ContractLifecycleError("formal plan mapping denominator differs")
    result: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ContractLifecycleError("formal plan mapping entry is malformed")
        job_file = _regular_file(entry.get("path"), "formal job file")
        _assert_equal(entry.get("sha256"), sha256_file(job_file), "formal job hash")
        job = load_mapping(job_file)
        _assert_equal(job.get("execution_lock_sha256"), execution_lock_sha256, "job lock")
        _assert_equal(
            job.get("execution_policy_sha256"), execution_policy_sha256, "job policy"
        )
        binding = formal_job_binding_sha256(job)
        job_id = str(job.get("job_id") or "")
        if (
            not job_id
            or job_id in {".", ".."}
            or "/" in job_id
            or "\\" in job_id
            or binding in result
        ):
            raise ContractLifecycleError("formal plan job binding/path is invalid")
        result[binding] = job_id
    if len(result) != EXPECTED_RECORD_SLOT_COUNT:
        raise ContractLifecycleError("formal plan job bindings are not unique")
    return result


def _safe_snapshot_relative(value: Any) -> str:
    text = str(value or "")
    if not text or "\\" in text:
        raise ContractLifecycleError("snapshot path is empty or non-POSIX")
    path = PurePosixPath(text)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ContractLifecycleError("snapshot path escapes its root")
    if path.as_posix() != text:
        raise ContractLifecycleError("snapshot path is not canonical")
    return text


def build_evidence_acceptance_definition(
    *,
    execution_lock_path: str | Path = DEFAULT_EXECUTION_LOCK,
    checklist_freeze_lock_path: str | Path = DEFAULT_CHECKLIST_FREEZE_V2,
    review_quiescence_receipt_path: str
    | Path = DEFAULT_ACCEPTANCE_QUIESCENCE_RECEIPT,
    retrieval_quiescence_receipt_path: str
    | Path = DEFAULT_RETRIEVAL_QUIESCENCE_RECEIPT,
    quiescence_max_age_seconds: int
    | None = DEFAULT_QUIESCENCE_MAX_AGE_SECONDS,
    sealed_retrieval_receipt_path: str
    | Path = DEFAULT_SEALED_EVIDENCE_RETRIEVAL_RECEIPT,
    staging_evidence_root: str | Path | None = None,
    formal_completion_receipt_path: str
    | Path = DEFAULT_FORMAL_EXECUTION_COMPLETION_RECEIPT,
    formal_anomaly_receipt_path: str | Path = DEFAULT_FORMAL_EXECUTION_ANOMALY_RECEIPT,
    _execution_envelope_only: bool = False,
) -> dict[str, Any]:
    """Fail closed unless all 2,847 locked staging slots are complete and intact."""

    # Both gates intentionally run before resolving or inventorying staging raw.
    checklist, acceptance_quiescence = _verify_checklist_v2_quiescence_gate(
        checklist_freeze_lock_path=checklist_freeze_lock_path,
        review_quiescence_receipt_path=review_quiescence_receipt_path,
        quiescence_max_age_seconds=quiescence_max_age_seconds,
    )
    retrieval = verify_sealed_evidence_retrieval_receipt(
        receipt_path=sealed_retrieval_receipt_path,
        execution_lock_path=execution_lock_path,
        checklist_freeze_lock_path=checklist_freeze_lock_path,
        review_quiescence_receipt_path=retrieval_quiescence_receipt_path,
        quiescence_max_age_seconds=None,
        formal_completion_receipt_path=formal_completion_receipt_path,
        _execution_envelope_only=_execution_envelope_only,
    )

    execution = _verify_execution_lock_for_evidence_phase(
        execution_lock_path, envelope_only=_execution_envelope_only
    )
    execution_lock_file = _regular_file(execution.lock_path, "execution lock")
    definition = execution.definition
    output_precondition = _mapping(
        definition.get("output_precondition"), "execution output precondition"
    )
    locked_root = _resolve_locked_path(
        output_precondition.get("staging_raw_result_root"),
        "execution staging raw result root",
    )
    if staging_evidence_root is not None:
        supplied_root = resolve_repo_path(staging_evidence_root).resolve()
        if supplied_root != locked_root:
            raise ContractLifecycleError(
                "staging evidence root differs from the execution lock"
            )
    staging_root = _regular_directory(locked_root, "staging evidence root")
    _reject_tree_symlinks(staging_root, "staging evidence root")

    locked_entries = list(
        _mapping(definition.get("job_plan"), "execution job plan").get("entries") or []
    )
    if len(locked_entries) != EXPECTED_RECORD_SLOT_COUNT or not all(
        isinstance(item, Mapping) for item in locked_entries
    ):
        raise ContractLifecycleError(
            f"execution lock must contain {EXPECTED_RECORD_SLOT_COUNT} job entries"
        )

    expected_job_ids = [str(item["job_id"]) for item in locked_entries]
    actual_children = list(staging_root.iterdir())
    unexpected_files = sorted(
        path.name for path in actual_children if not path.is_dir()
    )
    actual_job_ids = {path.name for path in actual_children if path.is_dir()}
    missing = sorted(set(expected_job_ids) - actual_job_ids)
    unexpected = sorted(actual_job_ids - set(expected_job_ids))
    if missing or unexpected or unexpected_files:
        raise ContractLifecycleError(
            "staging denominator is incomplete or contaminated: "
            f"expected={EXPECTED_RECORD_SLOT_COUNT}, observed={len(actual_job_ids)}, "
            f"missing={len(missing)} sample={missing[:5]}, "
            f"unexpected={len(unexpected)} sample={unexpected[:5]}, "
            f"root_files={unexpected_files[:5]}"
        )

    inventory = _tree_inventory(staging_root)
    inventory_by_path = inventory.by_path()
    inventory_by_job: dict[str, list[dict[str, Any]]] = {}
    for item in inventory.files:
        top_level = str(item["relative_path"]).partition("/")[0]
        inventory_by_job.setdefault(top_level, []).append(dict(item))
    execution_lock_sha = execution.lock_sha256
    execution_policy_sha = str(definition.get("execution_policy_sha256") or "")
    runtime_policy_semantic_sha = str(
        _mapping(
            definition.get("rate_limit_policy"), "execution rate-limit policy"
        ).get("runtime_policy_semantic_sha256")
        or ""
    )
    runtime_policy_file_sha = str(
        _mapping(definition.get("runtime_policy"), "execution runtime policy").get(
            "sha256"
        )
        or ""
    )
    source_bundle_sha = str(
        _mapping(definition.get("source_bundle"), "execution source bundle").get(
            "sha256"
        )
        or ""
    )
    manifest_sha = str(
        _mapping(definition.get("manifest"), "execution manifest").get("sha256") or ""
    )
    staging_namespace = str(definition.get("staging_result_namespace") or "")
    if staging_namespace != EXECUTION_STAGING_NAMESPACE:
        raise ContractLifecycleError("execution staging namespace is not canonical")
    formal_execution_receipts = _verify_formal_execution_receipts(
        completion_path=formal_completion_receipt_path,
        anomaly_path=formal_anomaly_receipt_path,
        execution_lock_path=execution_lock_file,
        execution_lock_sha256=execution_lock_sha,
        execution_policy_sha256=execution_policy_sha,
        execution_definition=definition,
    )
    formal_remote_index = load_mapping(
        _regular_file(
            formal_execution_receipts["remote_completion_index"]["path"],
            "accepted formal remote completion index",
        )
    )
    remote_entries_by_binding = {
        str(item["job_binding_sha256"]): dict(item)
        for item in list(formal_remote_index.get("entries") or [])
        if isinstance(item, Mapping)
    }
    if len(remote_entries_by_binding) != EXPECTED_RECORD_SLOT_COUNT:
        raise ContractLifecycleError(
            "formal remote completion binding denominator differs"
        )

    accepted_entries: list[dict[str, Any]] = []
    identities: list[tuple[str, str]] = []
    execution_lock_payload = load_mapping(execution_lock_file)
    for locked_entry in locked_entries:
        expected = dict(locked_entry)
        accepted = _validate_staging_job(
            staging_root=staging_root,
            inventory=inventory,
            inventory_by_path=inventory_by_path,
            job_inventory_files=tuple(
                inventory_by_job.get(str(expected["job_id"]), ())
            ),
            expected=expected,
            execution_lock_file=execution_lock_file,
            execution_lock_payload=execution_lock_payload,
            execution_lock_sha=execution_lock_sha,
            execution_policy_sha=execution_policy_sha,
            runtime_policy_semantic_sha=runtime_policy_semantic_sha,
            runtime_policy_file_sha=runtime_policy_file_sha,
            source_bundle_sha=source_bundle_sha,
            manifest_sha=manifest_sha,
            staging_namespace=staging_namespace,
            remote_entries_by_binding=remote_entries_by_binding,
        )
        accepted_entries.append(accepted)
        identities.append((accepted["case_unit_id"], accepted["agent_id"]))

    identity_counts = Counter(identities)
    duplicates = sorted(key for key, count in identity_counts.items() if count != 1)
    if duplicates:
        raise ContractLifecycleError(
            f"duplicate or missing case/agent identities: {duplicates[:5]}"
        )
    case_agent_counts = Counter(case_id for case_id, _ in identities)
    if set(case_agent_counts.values()) != {len(EXPECTED_AGENTS)}:
        raise ContractLifecycleError(
            "every accepted case must contain exactly Agent A, Agent B, and Agent C"
        )

    case_ids: list[str] = []
    seen_cases: set[str] = set()
    for item in locked_entries:
        case_id = str(item["case_unit_id"])
        if case_id not in seen_cases:
            seen_cases.add(case_id)
            case_ids.append(case_id)
    if len(case_ids) != EXPECTED_CASE_COUNT:
        raise ContractLifecycleError(
            f"accepted case denominator must be {EXPECTED_CASE_COUNT}"
        )
    suite_counts = dict(Counter(case_id.split(":")[1] for case_id in case_ids))
    if suite_counts != EXPECTED_SUITE_COUNTS:
        raise ContractLifecycleError(f"accepted suite counts differ: {suite_counts}")

    counts = {
        "cases": EXPECTED_CASE_COUNT,
        "agents_per_case": len(EXPECTED_AGENTS),
        "record_slots": EXPECTED_RECORD_SLOT_COUNT,
        "native_trajectories": EXPECTED_RECORD_SLOT_COUNT * 3,
        "completed": EXPECTED_RECORD_SLOT_COUNT,
        "missing": 0,
        "duplicate": 0,
        "unexpected": 0,
        "unresolved": 0,
    }
    accepted_definition = {
        "execution_lock": _path_lock(execution_lock_file),
        "checklist_freeze_lock": _path_lock(checklist.freeze_path),
        "review_quiescence_receipt": _path_lock(
            acceptance_quiescence["path"]
        ),
        "sealed_retrieval_receipt": _path_lock(retrieval.path),
        "execution_policy_sha256": execution_policy_sha,
        "formal_execution_receipts": formal_execution_receipts,
        "staging_evidence_root": {
            "path": _display(staging_root),
            "tree_sha256": inventory.tree_sha256,
            "file_count": inventory.file_count,
        },
        "counts": counts,
        "case_identity": {
            "case_id_order_sha256": sha256_object(case_ids),
            "case_id_set_sha256": sha256_object(sorted(case_ids)),
            "suite_case_counts": suite_counts,
        },
        "entry_order": "execution_lock_job_plan",
        "entries_sha256": sha256_object(accepted_entries),
        "entries": accepted_entries,
        "blind_audit": {
            "raw_run_projection": "top_level_integrity_metadata_only",
            "artifact_bytes": "hashed_not_deserialized",
            "trajectory_contents_materialized": False,
            "native_labels_materialized": False,
            "native_labels_emitted": False,
        },
    }
    return accepted_definition


def publish_evidence_acceptance_index(
    *,
    output_path: str | Path = DEFAULT_EVIDENCE_INDEX,
    locked_at: str | None = None,
    **definition_kwargs: Any,
) -> LockedArtifactResult:
    definition = build_evidence_acceptance_definition(**definition_kwargs)
    payload = {
        "schema_version": EVIDENCE_INDEX_SCHEMA_VERSION,
        "index_id": "agentdojo_full_v1.2.2_direct_evidence_acceptance",
        "status": "accepted",
        "locked_at": _timestamp(locked_at),
        "result_namespace": EXECUTION_STAGING_NAMESPACE,
        "definition": definition,
        "definition_sha256": sha256_object(definition),
    }
    _validate_evidence_index_payload(payload)
    return _publish_once(
        output_path,
        payload,
        schema_name="evidence acceptance index",
        definition=definition,
        validate_payload=_validate_evidence_index_payload,
    )


def verify_evidence_acceptance_index(
    *,
    index_path: str | Path = DEFAULT_EVIDENCE_INDEX,
    execution_lock_path: str | Path = DEFAULT_EXECUTION_LOCK,
    checklist_freeze_lock_path: str | Path | None = None,
    review_quiescence_receipt_path: str | Path | None = None,
    retrieval_quiescence_receipt_path: str | Path | None = None,
    sealed_retrieval_receipt_path: str | Path | None = None,
    staging_evidence_root: str | Path | None = None,
    formal_completion_receipt_path: str
    | Path = DEFAULT_FORMAL_EXECUTION_COMPLETION_RECEIPT,
    formal_anomaly_receipt_path: str | Path = DEFAULT_FORMAL_EXECUTION_ANOMALY_RECEIPT,
    _execution_envelope_only: bool = False,
) -> LockedArtifactResult:
    index_file = _regular_file(index_path, "evidence acceptance index")
    payload = load_mapping(index_file)
    _validate_evidence_index_payload(payload)
    locked_definition = _mapping(payload.get("definition"), "evidence definition")
    checklist_binding = _mapping(
        locked_definition.get("checklist_freeze_lock"),
        "evidence checklist freeze binding",
    )
    acceptance_quiescence_binding = _mapping(
        locked_definition.get("review_quiescence_receipt"),
        "evidence quiescence binding",
    )
    retrieval_binding = _mapping(
        locked_definition.get("sealed_retrieval_receipt"),
        "evidence sealed retrieval binding",
    )
    effective_checklist = checklist_freeze_lock_path or checklist_binding.get("path")
    effective_acceptance_quiescence = (
        review_quiescence_receipt_path
        or acceptance_quiescence_binding.get("path")
    )
    effective_retrieval = (
        sealed_retrieval_receipt_path or retrieval_binding.get("path")
    )
    retrieval_payload = load_mapping(
        _regular_file(effective_retrieval, "sealed retrieval receipt")
    )
    retrieval_definition = _mapping(
        retrieval_payload.get("definition"), "sealed retrieval definition"
    )
    retrieval_quiescence_binding = _mapping(
        retrieval_definition.get("review_quiescence_receipt"),
        "sealed retrieval quiescence binding",
    )
    effective_retrieval_quiescence = (
        retrieval_quiescence_receipt_path
        or retrieval_quiescence_binding.get("path")
    )
    expected = build_evidence_acceptance_definition(
        execution_lock_path=execution_lock_path,
        checklist_freeze_lock_path=effective_checklist,
        review_quiescence_receipt_path=effective_acceptance_quiescence,
        retrieval_quiescence_receipt_path=effective_retrieval_quiescence,
        quiescence_max_age_seconds=None,
        sealed_retrieval_receipt_path=effective_retrieval,
        staging_evidence_root=staging_evidence_root,
        formal_completion_receipt_path=formal_completion_receipt_path,
        formal_anomaly_receipt_path=formal_anomaly_receipt_path,
        _execution_envelope_only=_execution_envelope_only,
    )
    if payload.get("definition") != expected:
        raise ContractLifecycleError(
            "evidence acceptance index currentness verification failed"
        )
    return LockedArtifactResult(
        path=index_file,
        sha256=sha256_file(index_file),
        definition=expected,
        created=False,
    )


def promote_agentdojo_full_evidence(
    *,
    execution_lock_path: str | Path = DEFAULT_EXECUTION_LOCK,
    checklist_freeze_lock_path: str | Path = DEFAULT_CHECKLIST_FREEZE_V2,
    review_quiescence_receipt_path: str
    | Path = DEFAULT_PROMOTION_QUIESCENCE_RECEIPT,
    quiescence_max_age_seconds: int = DEFAULT_QUIESCENCE_MAX_AGE_SECONDS,
    evidence_index_path: str | Path = DEFAULT_EVIDENCE_INDEX,
    destination_root: str | Path | None = None,
    receipt_path: str | Path = DEFAULT_PROMOTION_RECEIPT,
    score_result_roots: Sequence[str | Path] = DEFAULT_SCORE_NAMESPACE_ROOTS,
    locked_at: str | None = None,
) -> LockedArtifactResult:
    """Promote staging bytes by a verified atomic directory publication."""

    # Freeze/quiescence is the first gate; nested evidence verification opens raw.
    checklist, promotion_quiescence = _verify_checklist_v2_quiescence_gate(
        checklist_freeze_lock_path=checklist_freeze_lock_path,
        review_quiescence_receipt_path=review_quiescence_receipt_path,
        quiescence_max_age_seconds=quiescence_max_age_seconds,
    )
    receipt_file = resolve_repo_path(receipt_path).resolve()
    if receipt_file.exists():
        return verify_evidence_promotion_receipt(
            receipt_path=receipt_file,
            execution_lock_path=execution_lock_path,
            checklist_freeze_lock_path=checklist_freeze_lock_path,
            evidence_index_path=evidence_index_path,
            score_result_roots=score_result_roots,
        )

    # First publication remains on the strict reservation-only execution gate.
    execution = verify_execution_lock(lock_path=execution_lock_path)
    evidence = verify_evidence_acceptance_index(
        index_path=evidence_index_path,
        execution_lock_path=execution_lock_path,
        checklist_freeze_lock_path=checklist_freeze_lock_path,
    )
    score_precondition = _score_empty_snapshot(score_result_roots)

    output_precondition = _mapping(
        execution.definition.get("output_precondition"),
        "execution output precondition",
    )
    source_root = _resolve_locked_path(
        output_precondition.get("staging_raw_result_root"), "staging root"
    )
    locked_destination = _resolve_locked_path(
        output_precondition.get("formal_raw_result_root"), "formal root"
    )
    if destination_root is not None and (
        resolve_repo_path(destination_root).resolve() != locked_destination
    ):
        raise ContractLifecycleError("formal destination differs from execution lock")
    if source_root == locked_destination:
        raise ContractLifecycleError("staging and formal evidence roots must differ")

    namespace_reservation = _require_reserved_formal_namespace(
        namespace_root=DEFAULT_RESULT_NAMESPACE_LOCK.parent,
        formal_evidence_root=locked_destination,
    )

    source_inventory = _tree_inventory(_regular_directory(source_root, "staging root"))
    evidence_root_lock = _mapping(
        evidence.definition.get("staging_evidence_root"),
        "accepted staging evidence root",
    )
    _assert_equal(
        source_inventory.tree_sha256,
        evidence_root_lock.get("tree_sha256"),
        "accepted staging tree hash",
    )
    _assert_equal(
        source_inventory.file_count,
        evidence_root_lock.get("file_count"),
        "accepted staging file count",
    )

    methods = _atomic_promote_tree(
        source_inventory=source_inventory,
        destination=locked_destination,
    )
    destination_inventory = _tree_inventory(
        _regular_directory(locked_destination, "formal evidence root")
    )
    _assert_inventory_equal(source_inventory, destination_inventory)

    # Re-read staging after publication so concurrent or late writes fail closed.
    source_readback = _tree_inventory(source_root)
    _assert_inventory_equal(source_inventory, source_readback)
    _seal_tree_read_only(locked_destination)
    _assert_tree_read_only(locked_destination)
    destination_readback = _tree_inventory(locked_destination)
    _assert_inventory_equal(source_readback, destination_readback)
    _assert_no_hardlinks(destination_readback.root, "formal evidence root")
    file_receipts = [
        {
            "relative_path": str(item["relative_path"]),
            "size_bytes": int(item["size_bytes"]),
            "source_sha256": str(item["sha256"]),
            "destination_sha256": str(item["sha256"]),
            "transfer_method": methods[str(item["relative_path"])],
        }
        for item in source_inventory.files
    ]
    promotion_definition = {
        "execution_lock": _path_lock(execution.lock_path),
        "checklist_freeze_lock": _path_lock(checklist.freeze_path),
        "review_quiescence_receipt": _path_lock(
            promotion_quiescence["path"]
        ),
        "sealed_retrieval_receipt": dict(
            _mapping(
                evidence.definition.get("sealed_retrieval_receipt"),
                "accepted sealed retrieval receipt",
            )
        ),
        "evidence_acceptance_index": _path_lock(evidence.path),
        "namespace_reservation": namespace_reservation,
        "source": {
            "path": _display(source_inventory.root),
            "tree_sha256": source_inventory.tree_sha256,
            "file_count": source_inventory.file_count,
        },
        "destination": {
            "path": _display(destination_inventory.root),
            "tree_sha256": destination_inventory.tree_sha256,
            "file_count": destination_inventory.file_count,
        },
        "counts": {
            "cases": EXPECTED_CASE_COUNT,
            "record_slots": EXPECTED_RECORD_SLOT_COUNT,
            "files": source_inventory.file_count,
            "hash_mismatches": 0,
        },
        "inventory_sha256": sha256_object(file_receipts),
        "files": file_receipts,
        "byte_preserving": True,
        "formal_tree_read_only": True,
        "formal_tree_hardlink_count": 0,
        "score_output_precondition": score_precondition,
        "publication": "atomic_directory_rename_after_full_hash_verification",
        "publication_guarantees": {
            "copy_only": True,
            "same_filesystem": True,
            "fsync_completed_before_publication": True,
            "atomic_rename_noreplace": True,
            "destination_overwrite_permitted": False,
        },
    }
    _assert_equal(
        _score_empty_snapshot(score_result_roots),
        score_precondition,
        "post-promotion score namespace emptiness",
    )
    payload = {
        "schema_version": PROMOTION_SCHEMA_VERSION,
        "promotion_id": "agentdojo_full_v1.2.2_direct_staging_to_formal",
        "status": "promoted_and_verified",
        "locked_at": _timestamp(locked_at),
        "result_namespace": RESULT_NAMESPACE,
        "definition": promotion_definition,
        "definition_sha256": sha256_object(promotion_definition),
    }
    _validate_promotion_payload(payload)
    result = _publish_once(
        receipt_file,
        payload,
        schema_name="evidence promotion receipt",
        definition=promotion_definition,
        validate_payload=_validate_promotion_payload,
    )
    _verify_score_output_precondition(
        promotion_definition.get("score_output_precondition"),
        score_result_roots,
        require_empty=True,
    )
    return result


def verify_evidence_promotion_receipt(
    *,
    receipt_path: str | Path = DEFAULT_PROMOTION_RECEIPT,
    execution_lock_path: str | Path = DEFAULT_EXECUTION_LOCK,
    checklist_freeze_lock_path: str | Path = DEFAULT_CHECKLIST_FREEZE_V2,
    review_quiescence_receipt_path: str | Path | None = None,
    quiescence_max_age_seconds: int | None = None,
    evidence_index_path: str | Path = DEFAULT_EVIDENCE_INDEX,
    score_result_roots: Sequence[str | Path] = DEFAULT_SCORE_NAMESPACE_ROOTS,
    require_score_roots_empty: bool = True,
) -> LockedArtifactResult:
    """Verify the post-promotion phase without relaxing execution admission.

    The promotion receipt, reservation marker, exact namespace layout, source
    and destination inventories, copy receipts, read-only seal, hardlink
    prohibition, and score-output precondition are proved *before* the
    execution envelope verifier is used.  Therefore an arbitrary extra file in
    the formal namespace cannot turn the envelope-only API into an execution
    gate bypass.
    """

    receipt_file = _regular_file(receipt_path, "evidence promotion receipt")
    payload = load_mapping(receipt_file)
    _validate_promotion_payload(payload)
    definition = _mapping(payload.get("definition"), "promotion definition")

    promotion_quiescence_binding = _mapping(
        definition.get("review_quiescence_receipt"),
        "promotion quiescence binding",
    )
    effective_quiescence = (
        review_quiescence_receipt_path
        or promotion_quiescence_binding.get("path")
    )
    checklist, _ = _verify_checklist_v2_quiescence_gate(
        checklist_freeze_lock_path=checklist_freeze_lock_path,
        review_quiescence_receipt_path=effective_quiescence,
        quiescence_max_age_seconds=quiescence_max_age_seconds,
    )
    for actual, expected, label in (
        (
            definition.get("checklist_freeze_lock"),
            _path_lock(checklist.freeze_path),
            "v2 checklist freeze lock",
        ),
        (
            definition.get("review_quiescence_receipt"),
            _path_lock(effective_quiescence),
            "review quiescence receipt",
        ),
    ):
        _assert_equal(actual, expected, f"promotion {label} binding")

    source_lock = _mapping(definition.get("source"), "promotion source")
    destination_lock = _mapping(definition.get("destination"), "promotion destination")
    source = _tree_inventory(_resolve_locked_path(source_lock.get("path"), "source"))
    destination = _tree_inventory(
        _resolve_locked_path(destination_lock.get("path"), "destination")
    )
    namespace_reservation = _verify_promoted_namespace_layout(
        namespace_root=DEFAULT_RESULT_NAMESPACE_LOCK.parent,
        destination=destination,
    )
    _assert_equal(
        definition.get("namespace_reservation"),
        namespace_reservation,
        "promotion namespace reservation binding",
    )
    _assert_tree_read_only(destination.root)
    _assert_inventory_equal(source, destination)
    _assert_no_hardlinks(destination.root, "formal evidence root")
    if source.root.stat().st_dev != destination.root.stat().st_dev:
        raise ContractLifecycleError(
            "promoted evidence source and destination are not on one filesystem"
        )
    _assert_equal(
        definition.get("publication_guarantees"),
        {
            "copy_only": True,
            "same_filesystem": True,
            "fsync_completed_before_publication": True,
            "atomic_rename_noreplace": True,
            "destination_overwrite_permitted": False,
        },
        "formal promotion publication guarantees",
    )
    for inventory, locked, label in (
        (source, source_lock, "source"),
        (destination, destination_lock, "destination"),
    ):
        _assert_equal(inventory.tree_sha256, locked.get("tree_sha256"), f"{label} tree")
        _assert_equal(inventory.file_count, locked.get("file_count"), f"{label} count")

    files = list(definition.get("files") or [])
    if len(files) != source.file_count:
        raise ContractLifecycleError("promotion file receipt denominator differs")
    _assert_equal(
        definition.get("counts"),
        {
            "cases": EXPECTED_CASE_COUNT,
            "record_slots": EXPECTED_RECORD_SLOT_COUNT,
            "files": source.file_count,
            "hash_mismatches": 0,
        },
        "promotion exact denominator",
    )
    source_by_path = source.by_path()
    destination_by_path = destination.by_path()
    receipt_paths: list[str] = []
    for item in files:
        if not isinstance(item, Mapping):
            raise ContractLifecycleError("promotion file receipt is malformed")
        relative = str(item.get("relative_path") or "")
        receipt_paths.append(relative)
        source_item = source_by_path.get(relative)
        destination_item = destination_by_path.get(relative)
        if source_item is None or destination_item is None:
            raise ContractLifecycleError(
                f"promotion receipt has unknown file: {relative}"
            )
        _assert_equal(
            item.get("source_sha256"), source_item["sha256"], "source file hash"
        )
        _assert_equal(
            item.get("destination_sha256"),
            source_item["sha256"],
            "destination file hash",
        )
        _assert_equal(
            destination_item["sha256"],
            source_item["sha256"],
            "current destination file hash",
        )
        _assert_equal(
            item.get("size_bytes"), source_item["size_bytes"], "promoted file size"
        )
        if item.get("transfer_method") not in {"copy", "existing_verified"}:
            raise ContractLifecycleError(
                "formal evidence promotion is copy-only; hardlink receipts are forbidden"
            )
    expected_paths = [str(item["relative_path"]) for item in source.files]
    _assert_equal(receipt_paths, expected_paths, "promotion exact file receipt order")
    _assert_equal(
        definition.get("inventory_sha256"),
        sha256_object(files),
        "promotion inventory hash",
    )
    _assert_equal(
        definition.get("formal_tree_hardlink_count"),
        0,
        "formal evidence hardlink count",
    )
    _verify_score_output_precondition(
        definition.get("score_output_precondition"),
        score_result_roots,
        require_empty=require_score_roots_empty,
    )

    # Only the independently verified post-promotion state may use the immutable
    # execution-envelope verifier.  The public execution gate remains strict.
    execution = verify_execution_lock_envelope(lock_path=execution_lock_path)
    output_precondition = _mapping(
        execution.definition.get("output_precondition"),
        "execution output precondition",
    )
    _assert_declared_path(
        source_lock.get("path"),
        _resolve_locked_path(
            output_precondition.get("staging_raw_result_root"),
            "locked staging evidence root",
        ),
        "promotion source",
    )
    _assert_declared_path(
        destination_lock.get("path"),
        _resolve_locked_path(
            output_precondition.get("formal_raw_result_root"),
            "locked formal evidence root",
        ),
        "promotion destination",
    )
    evidence = verify_evidence_acceptance_index(
        index_path=evidence_index_path,
        execution_lock_path=execution_lock_path,
        checklist_freeze_lock_path=checklist_freeze_lock_path,
        _execution_envelope_only=True,
    )
    for actual, expected, label in (
        (
            definition.get("execution_lock"),
            _path_lock(execution.lock_path),
            "execution lock",
        ),
        (
            definition.get("sealed_retrieval_receipt"),
            _mapping(
                evidence.definition.get("sealed_retrieval_receipt"),
                "accepted sealed retrieval receipt",
            ),
            "sealed retrieval receipt",
        ),
        (
            definition.get("evidence_acceptance_index"),
            _path_lock(evidence.path),
            "evidence acceptance index",
        ),
    ):
        _assert_equal(actual, expected, f"promotion {label} binding")
    return LockedArtifactResult(
        path=receipt_file,
        sha256=sha256_file(receipt_file),
        definition=dict(definition),
        created=False,
    )


def build_prescore_join_definition(
    *,
    execution_lock_path: str | Path = DEFAULT_EXECUTION_LOCK,
    checklist_freeze_lock_path: str | Path = DEFAULT_CHECKLIST_FREEZE_V2,
    review_quiescence_receipt_path: str | Path = DEFAULT_JOIN_QUIESCENCE_RECEIPT,
    quiescence_max_age_seconds: int
    | None = DEFAULT_QUIESCENCE_MAX_AGE_SECONDS,
    evidence_index_path: str | Path = DEFAULT_EVIDENCE_INDEX,
    promotion_receipt_path: str | Path = DEFAULT_PROMOTION_RECEIPT,
    score_prompt_path: str | Path = DEFAULT_SCORE_PROMPT,
    score_schema_path: str | Path = DEFAULT_SCORE_SCHEMA,
    score_result_roots: Sequence[str | Path] = DEFAULT_SCORE_NAMESPACE_ROOTS,
) -> dict[str, Any]:
    checklist, join_quiescence = _verify_checklist_v2_quiescence_gate(
        checklist_freeze_lock_path=checklist_freeze_lock_path,
        review_quiescence_receipt_path=review_quiescence_receipt_path,
        quiescence_max_age_seconds=quiescence_max_age_seconds,
    )
    # Promotion verification independently proves the post-reservation formal
    # tree before any envelope-only execution verification is permitted.
    promotion = verify_evidence_promotion_receipt(
        receipt_path=promotion_receipt_path,
        execution_lock_path=execution_lock_path,
        checklist_freeze_lock_path=checklist_freeze_lock_path,
        evidence_index_path=evidence_index_path,
        score_result_roots=score_result_roots,
    )
    execution = verify_execution_lock_envelope(lock_path=execution_lock_path)
    evidence = verify_evidence_acceptance_index(
        index_path=evidence_index_path,
        execution_lock_path=execution_lock_path,
        checklist_freeze_lock_path=checklist_freeze_lock_path,
        _execution_envelope_only=True,
    )
    score_prompt = _regular_file(score_prompt_path, "score prompt")
    score_schema = _regular_file(score_schema_path, "score schema")
    frozen_inputs = _mapping(
        checklist.definition.get("prompt_schema_bindings"),
        "v2 checklist prompt/schema bindings",
    )
    _assert_equal(
        frozen_inputs.get("score_prompt"),
        _path_lock(score_prompt),
        "frozen score prompt",
    )
    _assert_equal(
        frozen_inputs.get("score_schema"),
        _path_lock(score_schema),
        "frozen score schema",
    )
    score_snapshot = _score_empty_snapshot(score_result_roots)
    destination = _mapping(promotion.definition.get("destination"), "formal evidence")
    execution_binding = _path_lock(execution.lock_path)
    checklist_binding = _path_lock(checklist.freeze_path)
    quiescence_binding = _path_lock(join_quiescence["path"])
    retrieval_binding = _mapping(
        evidence.definition.get("sealed_retrieval_receipt"),
        "accepted sealed retrieval receipt",
    )
    evidence_binding = _path_lock(evidence.path)
    promotion_binding = _path_lock(promotion.path)
    prompt_binding = _path_lock(score_prompt)
    schema_binding = _path_lock(score_schema)
    hash_graph = {
        "execution_lock_sha256": execution_binding["sha256"],
        "checklist_freeze_sha256": checklist_binding["sha256"],
        "review_quiescence_receipt_sha256": quiescence_binding["sha256"],
        "sealed_retrieval_receipt_sha256": retrieval_binding["sha256"],
        "evidence_acceptance_index_sha256": evidence_binding["sha256"],
        "promotion_receipt_sha256": promotion_binding["sha256"],
        "score_prompt_sha256": prompt_binding["sha256"],
        "score_schema_sha256": schema_binding["sha256"],
        "formal_evidence_tree_sha256": str(destination.get("tree_sha256") or ""),
    }
    return {
        "execution_lock": execution_binding,
        "checklist_freeze_lock": checklist_binding,
        "review_quiescence_receipt": quiescence_binding,
        "sealed_retrieval_receipt": retrieval_binding,
        "evidence_acceptance_index": evidence_binding,
        "promotion_receipt": promotion_binding,
        "score_prompt": prompt_binding,
        "score_schema": schema_binding,
        "formal_evidence": dict(destination),
        "hash_graph": hash_graph,
        "join_inputs_sha256": sha256_object(hash_graph),
        "score_output_precondition": score_snapshot,
        "authorization": {
            "case_count": EXPECTED_CASE_COUNT,
            "agents_per_case": len(EXPECTED_AGENTS),
            "score_task_count": EXPECTED_RECORD_SLOT_COUNT,
            "tasks_per_key": EXPECTED_CASE_COUNT,
            "slot_count": len(EXPECTED_AGENTS),
            "unresolved_evidence": 0,
            "unresolved_checklists": 0,
        },
    }


def publish_prescore_join_lock(
    *,
    output_path: str | Path = DEFAULT_PRESCORE_JOIN_LOCK,
    locked_at: str | None = None,
    **definition_kwargs: Any,
) -> LockedArtifactResult:
    definition = build_prescore_join_definition(**definition_kwargs)
    score_result_roots = definition_kwargs.get(
        "score_result_roots", DEFAULT_SCORE_NAMESPACE_ROOTS
    )
    _verify_score_output_precondition(
        definition.get("score_output_precondition"),
        score_result_roots,
        require_empty=True,
    )
    payload = {
        "schema_version": PRESCORE_JOIN_SCHEMA_VERSION,
        "join_id": "agentdojo_full_v1.2.2_direct_prescore_join",
        "lock_status": "locked",
        "locked_at": _timestamp(locked_at),
        "result_namespace": RESULT_NAMESPACE,
        "definition": definition,
        "definition_sha256": sha256_object(definition),
    }
    _validate_join_payload(payload)
    result = _publish_once(
        output_path,
        payload,
        schema_name="pre-score join lock",
        definition=definition,
        validate_payload=_validate_join_payload,
    )
    _verify_score_output_precondition(
        definition.get("score_output_precondition"),
        score_result_roots,
        require_empty=True,
    )
    return result


def verify_prescore_join_lock(
    *,
    lock_path: str | Path = DEFAULT_PRESCORE_JOIN_LOCK,
    **definition_kwargs: Any,
) -> LockedArtifactResult:
    lock_file = _regular_file(lock_path, "pre-score join lock")
    payload = load_mapping(lock_file)
    _validate_join_payload(payload)
    locked_definition = _mapping(payload.get("definition"), "pre-score join definition")
    locked_quiescence = _mapping(
        locked_definition.get("review_quiescence_receipt"),
        "pre-score join quiescence binding",
    )
    definition_kwargs.setdefault(
        "review_quiescence_receipt_path", locked_quiescence.get("path")
    )
    definition_kwargs["quiescence_max_age_seconds"] = None
    expected = build_prescore_join_definition(**definition_kwargs)
    if payload.get("definition") != expected:
        raise ContractLifecycleError("pre-score join lock currentness failed")
    return LockedArtifactResult(
        path=lock_file,
        sha256=sha256_file(lock_file),
        definition=expected,
        created=False,
    )


def verify_prescore_join_inputs_current(
    *,
    lock_path: str | Path = DEFAULT_PRESCORE_JOIN_LOCK,
    execution_lock_path: str | Path = DEFAULT_EXECUTION_LOCK,
    checklist_freeze_lock_path: str | Path = DEFAULT_CHECKLIST_FREEZE_V2,
    evidence_index_path: str | Path = DEFAULT_EVIDENCE_INDEX,
    promotion_receipt_path: str | Path = DEFAULT_PROMOTION_RECEIPT,
    score_prompt_path: str | Path = DEFAULT_SCORE_PROMPT,
    score_schema_path: str | Path = DEFAULT_SCORE_SCHEMA,
    score_result_roots: Sequence[str | Path] = DEFAULT_SCORE_NAMESPACE_ROOTS,
    require_score_roots_empty: bool = True,
) -> LockedArtifactResult:
    """Revalidate every join input while optionally permitting same-session scores.

    ``require_score_roots_empty=False`` is exclusively for resuming a previously
    authorized score session.  It relaxes only the original empty-output
    precondition; execution, checklist, evidence, promotion, prompt, schema,
    namespace identity, and denominator bindings are all recomputed.
    """

    join = load_prescore_join_lock_envelope(lock_path)
    definition = join.definition
    join_quiescence_binding = _mapping(
        definition.get("review_quiescence_receipt"),
        "pre-score join quiescence binding",
    )
    checklist, _ = _verify_checklist_v2_quiescence_gate(
        checklist_freeze_lock_path=checklist_freeze_lock_path,
        review_quiescence_receipt_path=join_quiescence_binding.get("path"),
        quiescence_max_age_seconds=None,
    )
    promotion = verify_evidence_promotion_receipt(
        receipt_path=promotion_receipt_path,
        execution_lock_path=execution_lock_path,
        checklist_freeze_lock_path=checklist_freeze_lock_path,
        evidence_index_path=evidence_index_path,
        score_result_roots=score_result_roots,
        require_score_roots_empty=False,
    )
    execution = verify_execution_lock_envelope(lock_path=execution_lock_path)
    evidence = verify_evidence_acceptance_index(
        index_path=evidence_index_path,
        execution_lock_path=execution_lock_path,
        checklist_freeze_lock_path=checklist_freeze_lock_path,
        _execution_envelope_only=True,
    )
    score_prompt = _regular_file(score_prompt_path, "score prompt")
    score_schema = _regular_file(score_schema_path, "score schema")
    sealed_retrieval_binding = _mapping(
        evidence.definition.get("sealed_retrieval_receipt"),
        "accepted sealed retrieval receipt",
    )
    for actual, expected, label in (
        (
            definition.get("execution_lock"),
            _path_lock(execution.lock_path),
            "execution lock",
        ),
        (
            definition.get("checklist_freeze_lock"),
            _path_lock(checklist.freeze_path),
            "v2 checklist freeze lock",
        ),
        (
            definition.get("review_quiescence_receipt"),
            _path_lock(join_quiescence_binding.get("path")),
            "review quiescence receipt",
        ),
        (
            definition.get("sealed_retrieval_receipt"),
            sealed_retrieval_binding,
            "sealed retrieval receipt",
        ),
        (
            definition.get("evidence_acceptance_index"),
            _path_lock(evidence.path),
            "evidence acceptance index",
        ),
        (
            definition.get("promotion_receipt"),
            _path_lock(promotion.path),
            "evidence promotion receipt",
        ),
        (definition.get("score_prompt"), _path_lock(score_prompt), "score prompt"),
        (definition.get("score_schema"), _path_lock(score_schema), "score schema"),
        (
            definition.get("formal_evidence"),
            _mapping(promotion.definition.get("destination"), "formal evidence"),
            "formal evidence",
        ),
    ):
        _assert_equal(actual, expected, f"pre-score join {label} binding")

    formal_evidence = _mapping(
        promotion.definition.get("destination"), "formal evidence"
    )
    expected_hash_graph = {
        "execution_lock_sha256": sha256_file(execution.lock_path),
        "checklist_freeze_sha256": sha256_file(checklist.freeze_path),
        "review_quiescence_receipt_sha256": sha256_file(
            _regular_file(
                join_quiescence_binding.get("path"),
                "pre-score join quiescence receipt",
            )
        ),
        "sealed_retrieval_receipt_sha256": sealed_retrieval_binding["sha256"],
        "evidence_acceptance_index_sha256": sha256_file(evidence.path),
        "promotion_receipt_sha256": sha256_file(promotion.path),
        "score_prompt_sha256": sha256_file(score_prompt),
        "score_schema_sha256": sha256_file(score_schema),
        "formal_evidence_tree_sha256": str(
            formal_evidence.get("tree_sha256") or ""
        ),
    }
    _assert_equal(
        definition.get("hash_graph"),
        expected_hash_graph,
        "pre-score join hash graph",
    )
    _assert_equal(
        definition.get("join_inputs_sha256"),
        sha256_object(expected_hash_graph),
        "pre-score join input aggregate hash",
    )

    expected_authorization = {
        "case_count": EXPECTED_CASE_COUNT,
        "agents_per_case": len(EXPECTED_AGENTS),
        "score_task_count": EXPECTED_RECORD_SLOT_COUNT,
        "tasks_per_key": EXPECTED_CASE_COUNT,
        "slot_count": len(EXPECTED_AGENTS),
        "unresolved_evidence": 0,
        "unresolved_checklists": 0,
    }
    _assert_equal(
        definition.get("authorization"),
        expected_authorization,
        "pre-score join authorization",
    )
    _verify_score_output_precondition(
        definition.get("score_output_precondition"),
        score_result_roots,
        require_empty=require_score_roots_empty,
    )
    return join


def load_prescore_join_lock_envelope(
    lock_path: str | Path = DEFAULT_PRESCORE_JOIN_LOCK,
) -> LockedArtifactResult:
    """Validate the immutable join envelope without re-imposing freeze-time emptiness.

    This is used only by score children belonging to a batch session that already
    passed :func:`verify_prescore_join_lock` before the first score byte was written.
    """

    lock_file = _regular_file(lock_path, "pre-score join lock")
    payload = load_mapping(lock_file)
    _validate_join_payload(payload)
    return LockedArtifactResult(
        path=lock_file,
        sha256=sha256_file(lock_file),
        definition=_mapping(payload.get("definition"), "pre-score join definition"),
        created=False,
    )


def _validate_staging_job(
    *,
    staging_root: Path,
    inventory: TreeInventory,
    inventory_by_path: Mapping[str, Mapping[str, Any]],
    job_inventory_files: Sequence[Mapping[str, Any]],
    expected: Mapping[str, Any],
    execution_lock_file: Path,
    execution_lock_payload: Mapping[str, Any],
    execution_lock_sha: str,
    execution_policy_sha: str,
    runtime_policy_semantic_sha: str,
    runtime_policy_file_sha: str,
    source_bundle_sha: str,
    manifest_sha: str,
    staging_namespace: str,
    remote_entries_by_binding: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    job_id = str(expected["job_id"])
    job_dir = _regular_directory(staging_root / job_id, f"job {job_id}")
    adapter_dir = _regular_directory(job_dir / "adapter", f"adapter {job_id}")
    raw_path = _regular_file(adapter_dir / "raw_run.json", f"raw run {job_id}")
    manifest_path = _regular_file(
        adapter_dir / "artifact_manifest.json", f"artifact manifest {job_id}"
    )
    environment_path = _regular_file(
        adapter_dir / "environment.json", f"environment {job_id}"
    )
    completion_marker_path = _regular_file(
        adapter_dir / "formal_job_completion.json",
        f"formal completion marker {job_id}",
    )
    completion_marker = load_mapping(completion_marker_path)
    if set(completion_marker) != set(COMPLETION_MARKER_FIELDS):
        raise ContractLifecycleError(
            f"formal completion marker fields differ for {job_id}"
        )
    for actual, expected_value, label in (
        (
            completion_marker.get("schema_version"),
            "agentdojo_formal_job_completion/v2",
            "schema",
        ),
        (completion_marker.get("execution_lock_sha256"), execution_lock_sha, "lock"),
        (
            completion_marker.get("execution_policy_sha256"),
            execution_policy_sha,
            "policy",
        ),
        (completion_marker.get("native_episode_count"), 3, "native episode count"),
        (completion_marker.get("worker_status"), "completed", "worker status"),
        (
            completion_marker.get("postprocessor"),
            "agentdojo_formal_postprocessor/v1",
            "postprocessor",
        ),
    ):
        _assert_equal(actual, expected_value, f"completion marker {job_id}.{label}")
    parse_timestamp(
        str(completion_marker.get("completed_at") or ""),
        f"completion marker {job_id}.completed_at",
    )
    for field in (
        "job_binding_sha256",
        "job_identity_sha256",
        "stage_authorization_sha256",
        "formal_execution_context_sha256",
        "artifact_tree_sha256",
        "attempt_tree_sha256",
        "supervisor_exit_receipt_sha256",
    ):
        if re.fullmatch(
            r"[a-f0-9]{64}", str(completion_marker.get(field) or "")
        ) is None:
            raise ContractLifecycleError(
                f"completion marker {job_id}.{field} is invalid"
            )
    for field in (
        "artifact_file_count",
        "artifact_total_bytes",
        "attempt_file_count",
        "attempt_total_bytes",
    ):
        value = completion_marker.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ContractLifecycleError(
                f"completion marker {job_id}.{field} is invalid"
            )
    marker_relative = completion_marker_path.relative_to(job_dir).as_posix()
    formal_artifact_files = [
        item
        for item in job_inventory_files
        if Path(str(item["relative_path"])).relative_to(job_dir.relative_to(staging_root)).as_posix()
        != marker_relative
    ]
    formal_artifact_projection = [
        {
            "path": Path(str(item["relative_path"]))
            .relative_to(job_dir.relative_to(staging_root))
            .as_posix(),
            "sha256": item["sha256"],
        }
        for item in formal_artifact_files
    ]
    _assert_equal(
        completion_marker.get("artifact_file_count"),
        len(formal_artifact_projection),
        f"completion marker {job_id} artifact count",
    )
    _assert_equal(
        completion_marker.get("artifact_tree_sha256"),
        sha256_object(formal_artifact_projection),
        f"completion marker {job_id} artifact tree",
    )
    _assert_equal(
        completion_marker.get("artifact_total_bytes"),
        sum(int(item["size_bytes"]) for item in formal_artifact_files),
        f"completion marker {job_id} artifact bytes",
    )

    raw_meta, raw_keys = _blind_top_level_projection(raw_path, _RAW_METADATA_FIELDS)
    schema_properties = set(
        _mapping(load_schema("raw_run").get("properties"), "raw schema properties")
    )
    if raw_keys != schema_properties:
        raise ContractLifecycleError(
            f"raw run top-level field set differs for {job_id}: "
            f"missing={sorted(schema_properties - raw_keys)}, "
            f"extra={sorted(raw_keys - schema_properties)}"
        )
    for field in (
        "case_unit_id",
        "task_id",
        "record_slot_id",
        "run_id",
        "attempt_id",
        "seed",
        "agent_id",
    ):
        _assert_equal(raw_meta.get(field), expected[field], f"raw run {job_id}.{field}")
    for field, value in (
        ("schema_version", "raw_run/v1"),
        ("domain", "agentdojo"),
        ("benchmark_name", "AgentDojo"),
        ("phase", "full"),
        ("experiment_type", "appendix"),
        ("final_attempt", True),
        ("status", "COMPLETED"),
        ("diagnostic_status", "completed"),
        ("appendix_failure_class", "none"),
        ("execution_lock_sha256", execution_lock_sha),
        ("execution_policy_sha256", execution_policy_sha),
        ("openrouter_runtime_policy_sha256", runtime_policy_semantic_sha),
        ("openrouter_runtime_policy_file_sha256", runtime_policy_file_sha),
        ("manifest_hash", manifest_sha),
    ):
        _assert_equal(raw_meta.get(field), value, f"raw run {job_id}.{field}")
    expected_episode_ids = [
        f"agentdojo:benign:{expected['task_id']}",
        f"agentdojo:injection_task_as_user_task:{expected['task_id']}",
        f"agentdojo:injected:{expected['task_id']}",
    ]
    _assert_equal(
        raw_meta.get("episode_ids"),
        expected_episode_ids,
        f"raw run {job_id}.episode_ids",
    )
    _assert_declared_path(raw_meta.get("raw_source_path"), raw_path, "raw source path")
    _assert_declared_path(
        raw_meta.get("artifact_manifest_path"), manifest_path, "artifact manifest path"
    )

    artifact_manifest = load_mapping(manifest_path)
    artifact_report = validate_object(
        "artifact_manifest", artifact_manifest, raise_on_error=False
    )
    if not artifact_report.ok:
        raise ContractLifecycleError(
            f"artifact manifest schema failed for {job_id}: {artifact_report.to_dict()}"
        )
    for field in (
        "case_unit_id",
        "task_id",
        "record_slot_id",
        "run_id",
        "attempt_id",
        "seed",
        "agent_id",
    ):
        _assert_equal(
            artifact_manifest.get(field), expected[field], f"artifact {job_id}.{field}"
        )
    for field, value in (
        ("domain", "agentdojo"),
        ("benchmark_name", "AgentDojo"),
        ("phase", "full"),
        ("experiment_type", "appendix"),
        ("final_attempt", True),
        ("execution_lock_sha256", execution_lock_sha),
        ("execution_policy_sha256", execution_policy_sha),
        ("openrouter_runtime_policy_sha256", runtime_policy_semantic_sha),
        ("openrouter_runtime_policy_file_sha256", runtime_policy_file_sha),
        ("source_bundle_hash", source_bundle_sha),
    ):
        _assert_equal(
            artifact_manifest.get(field), value, f"artifact manifest {job_id}.{field}"
        )

    manifest_relative = manifest_path.relative_to(staging_root).as_posix()
    raw_relative = raw_path.relative_to(staging_root).as_posix()
    environment_relative = environment_path.relative_to(staging_root).as_posix()
    manifest_sha256 = _inventory_hash(inventory_by_path, manifest_relative)
    raw_sha256 = _inventory_hash(inventory_by_path, raw_relative)
    environment_sha256 = _inventory_hash(inventory_by_path, environment_relative)
    _assert_equal(
        raw_meta.get("artifact_manifest_sha256"),
        manifest_sha256,
        f"raw run {job_id} artifact manifest hash",
    )
    _assert_equal(
        artifact_manifest.get("environment_hash"),
        environment_sha256,
        f"artifact manifest {job_id} environment hash",
    )

    environment = load_mapping(environment_path)
    for field, expected_value in (
        ("job_id", job_id),
        ("run_id", expected["run_id"]),
        ("execution_lock_sha256", execution_lock_sha),
        ("execution_policy_sha256", execution_policy_sha),
        ("openrouter_runtime_policy_sha256", runtime_policy_semantic_sha),
        ("openrouter_runtime_policy_file_sha256", runtime_policy_file_sha),
    ):
        _assert_equal(
            environment.get(field), expected_value, f"environment {job_id}.{field}"
        )

    artifacts = list(artifact_manifest.get("artifacts") or [])
    artifact_index: list[dict[str, Any]] = []
    artifact_paths: set[Path] = set()
    artifact_ids: set[str] = set()
    trace_root: Path | None = None
    native_job_path: Path | None = None
    native_job_sha: str | None = None
    runtime_verification_path: Path | None = None
    for position, artifact in enumerate(artifacts):
        if not isinstance(artifact, Mapping):
            raise ContractLifecycleError(
                f"artifact manifest {job_id}[{position}] is not an object"
            )
        artifact_id = str(artifact.get("artifact_id") or "")
        if not artifact_id or artifact_id in artifact_ids:
            raise ContractLifecycleError(f"duplicate/empty artifact ID for {job_id}")
        artifact_ids.add(artifact_id)
        artifact_path = _resolve_declared_under(
            artifact.get("path"), job_dir, f"artifact {job_id}:{artifact_id}"
        )
        if artifact_path in artifact_paths:
            raise ContractLifecycleError(f"duplicate artifact path for {job_id}")
        artifact_paths.add(artifact_path)
        digest, size = _inventory_digest_for_path(
            artifact_path,
            staging_root=staging_root,
            inventory=inventory,
            inventory_by_path=inventory_by_path,
            candidate_files=job_inventory_files,
        )
        _assert_equal(artifact.get("sha256"), digest, f"artifact hash {artifact_id}")
        _assert_equal(artifact.get("size_bytes"), size, f"artifact size {artifact_id}")
        _assert_equal(
            artifact.get("environment_hash"),
            environment_sha256,
            f"artifact environment hash {artifact_id}",
        )
        _assert_equal(
            artifact.get("source_bundle_hash"),
            source_bundle_sha,
            f"artifact source bundle hash {artifact_id}",
        )
        artifact_index.append(
            {
                "artifact_id": artifact_id,
                "path": _display(artifact_path),
                "sha256": digest,
                "size_bytes": size,
            }
        )
        if artifact_path == environment_path:
            _assert_equal(digest, environment_sha256, "environment artifact hash")
        if (
            artifact_path.name == "job.json"
            and artifact_path.parent.name == "native_run"
        ):
            native_job_path = artifact_path
            native_job_sha = digest
        if artifact_path.name == "runtime_policy_verification.json":
            if runtime_verification_path is not None:
                raise ContractLifecycleError(
                    f"multiple runtime-policy verification artifacts for {job_id}"
                )
            runtime_verification_path = artifact_path
        if artifact.get("artifact_type") == "trace":
            if trace_root is not None:
                raise ContractLifecycleError(f"multiple trace artifacts for {job_id}")
            trace_root = artifact_path

    if environment_path not in artifact_paths:
        raise ContractLifecycleError(
            f"environment.json is not locked by the artifact manifest for {job_id}"
        )
    _verify_artifact_coverage(
        job_dir=job_dir,
        staging_root=staging_root,
        job_inventory_files=job_inventory_files,
        artifact_paths=artifact_paths,
        control_files={
            raw_path,
            manifest_path,
            adapter_dir / "index.json",
            adapter_dir / "logs/prepare.stdout.log",
            adapter_dir / "logs/prepare.stderr.log",
            completion_marker_path,
        },
    )

    if native_job_path is None or native_job_sha is None:
        raise ContractLifecycleError(f"native job.json is not locked for {job_id}")
    if runtime_verification_path is None:
        raise ContractLifecycleError(
            f"runtime_policy_verification.json is missing for {job_id}"
        )
    runtime_verification = load_mapping(runtime_verification_path)
    for field, value in (
        ("execution_lock_sha256", execution_lock_sha),
        ("execution_policy_sha256", execution_policy_sha),
        ("openrouter_runtime_policy_sha256", runtime_policy_semantic_sha),
        ("openrouter_runtime_policy_file_sha256", runtime_policy_file_sha),
    ):
        _assert_equal(
            runtime_verification.get(field),
            value,
            f"runtime policy verification {job_id}.{field}",
        )
    native_job = load_mapping(native_job_path)
    validate_object("job", native_job, raise_on_error=True)
    verify_job_binding(native_job, execution_lock_payload)
    job_binding = formal_job_binding_sha256(native_job)
    job_identity = job_identity_sha256(native_job)
    _assert_equal(
        completion_marker.get("job_binding_sha256"),
        job_binding,
        f"completion marker {job_id} job binding",
    )
    _assert_equal(
        completion_marker.get("job_identity_sha256"),
        job_identity,
        f"completion marker {job_id} job identity",
    )
    remote_entry = remote_entries_by_binding.get(job_binding)
    if remote_entry is None:
        raise ContractLifecycleError(
            f"formal remote completion entry is missing for {job_id}"
        )
    marker_file_sha = sha256_file(completion_marker_path)
    marker_semantic_sha = sha256_object(completion_marker)
    for actual, expected_value, label in (
        (remote_entry.get("job_identity_sha256"), job_identity, "job identity"),
        (
            remote_entry.get("completion_marker_file_sha256"),
            marker_file_sha,
            "marker file hash",
        ),
        (
            remote_entry.get("completion_marker_semantic_sha256"),
            marker_semantic_sha,
            "marker semantic hash",
        ),
    ):
        _assert_equal(actual, expected_value, f"remote completion {job_id}.{label}")
    for field in (
        "execution_lock_sha256",
        "execution_policy_sha256",
        "stage_authorization_sha256",
        "formal_stage_id",
        "formal_stage_session_id",
        "formal_execution_context_sha256",
        "artifact_file_count",
        "artifact_tree_sha256",
        "artifact_total_bytes",
        "native_episode_count",
        "attempt_tree_sha256",
        "attempt_file_count",
        "attempt_total_bytes",
        "supervisor_exit_receipt_sha256",
    ):
        _assert_equal(
            remote_entry.get(field),
            completion_marker.get(field),
            f"remote completion {job_id}.{field}",
        )
    for field, value in (
        ("execution_lock_sha256", execution_lock_sha),
        ("execution_policy_sha256", execution_policy_sha),
        ("result_namespace", staging_namespace),
    ):
        _assert_equal(native_job.get(field), value, f"native job {job_id}.{field}")
    _assert_declared_path(
        native_job.get("execution_lock_path"),
        execution_lock_file,
        "native execution lock",
    )
    if trace_root is None:
        raise ContractLifecycleError(f"trace artifact is missing for {job_id}")
    _verify_three_native_trajectories(trace_root, str(expected["task_id"]))

    job_tree_digest, _ = _inventory_digest_for_path(
        job_dir,
        staging_root=staging_root,
        inventory=inventory,
        inventory_by_path=inventory_by_path,
        candidate_files=job_inventory_files,
    )
    return {
        **{
            field: expected[field]
            for field in (
                "job_id",
                "case_unit_id",
                "task_id",
                "record_slot_id",
                "run_id",
                "attempt_id",
                "seed",
                "agent_id",
            )
        },
        "execution_lock_sha256": execution_lock_sha,
        "execution_policy_sha256": execution_policy_sha,
        "evidence_directory": _display(adapter_dir),
        "raw_run_path": _display(raw_path),
        "raw_run_sha256": raw_sha256,
        "artifact_manifest_path": _display(manifest_path),
        "artifact_manifest_sha256": manifest_sha256,
        "environment_path": _display(environment_path),
        "environment_sha256": environment_sha256,
        "native_job_path": _display(native_job_path),
        "native_job_sha256": native_job_sha,
        "job_binding_sha256": job_binding,
        "job_identity_sha256": job_identity,
        "formal_completion_marker_path": _display(completion_marker_path),
        "formal_completion_marker_sha256": marker_file_sha,
        "formal_completion_marker_semantic_sha256": marker_semantic_sha,
        "artifact_count": len(artifact_index),
        "artifact_set_sha256": sha256_object(artifact_index),
        "job_tree_sha256": job_tree_digest,
        "native_trajectory_file_count": 3,
        "metadata_status": "completed",
    }


def _blind_top_level_projection(
    path: Path, allowed_fields: frozenset[str]
) -> tuple[dict[str, Any], set[str]]:
    """Validate JSON and materialize only allow-listed top-level scalar values."""

    text = path.read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    index = _skip_ws(text, 0)
    if index >= len(text) or text[index] != "{":
        raise ContractLifecycleError(f"raw metadata root is not an object: {path}")
    index += 1
    projected: dict[str, Any] = {}
    keys: set[str] = set()
    while True:
        index = _skip_ws(text, index)
        if index < len(text) and text[index] == "}":
            index += 1
            break
        try:
            key, key_end = decoder.raw_decode(text, index)
        except json.JSONDecodeError as exc:
            raise ContractLifecycleError(
                f"invalid raw metadata key in {path}: {exc}"
            ) from exc
        if not isinstance(key, str):
            raise ContractLifecycleError(f"non-string raw metadata key in {path}")
        if key in keys:
            raise ContractLifecycleError(
                f"duplicate raw metadata key {key!r} in {path}"
            )
        keys.add(key)
        index = _skip_ws(text, key_end)
        if index >= len(text) or text[index] != ":":
            raise ContractLifecycleError(
                f"missing colon after raw metadata key {key!r}"
            )
        value_start = _skip_ws(text, index + 1)
        value_end = _skip_json_value(text, value_start)
        if key in allowed_fields:
            try:
                value, decoded_end = decoder.raw_decode(text, value_start)
            except json.JSONDecodeError as exc:
                raise ContractLifecycleError(
                    f"invalid projected metadata value {key!r} in {path}: {exc}"
                ) from exc
            allowed_list = (
                key == "episode_ids"
                and isinstance(value, list)
                and all(isinstance(item, str) for item in value)
            )
            if decoded_end != value_end or isinstance(value, dict) or (
                isinstance(value, list) and not allowed_list
            ):
                raise ContractLifecycleError(
                    f"projected raw metadata field {key!r} must be scalar "
                    "or the exact episode_ids string list"
                )
            projected[key] = value
        index = _skip_ws(text, value_end)
        if index < len(text) and text[index] == ",":
            index += 1
            continue
        if index < len(text) and text[index] == "}":
            index += 1
            break
        raise ContractLifecycleError(f"invalid raw metadata object delimiter in {path}")
    if _skip_ws(text, index) != len(text):
        raise ContractLifecycleError(f"trailing data after raw metadata object: {path}")
    return projected, keys


def _skip_json_value(text: str, index: int) -> int:
    index = _skip_ws(text, index)
    if index >= len(text):
        raise ContractLifecycleError("unexpected end of JSON value")
    char = text[index]
    if char == '"':
        return _skip_json_string(text, index)
    if char == "{":
        index = _skip_ws(text, index + 1)
        if index < len(text) and text[index] == "}":
            return index + 1
        while True:
            if index >= len(text) or text[index] != '"':
                raise ContractLifecycleError("invalid nested JSON object key")
            index = _skip_ws(text, _skip_json_string(text, index))
            if index >= len(text) or text[index] != ":":
                raise ContractLifecycleError("invalid nested JSON object colon")
            index = _skip_ws(text, _skip_json_value(text, index + 1))
            if index < len(text) and text[index] == ",":
                index = _skip_ws(text, index + 1)
                continue
            if index < len(text) and text[index] == "}":
                return index + 1
            raise ContractLifecycleError("invalid nested JSON object delimiter")
    if char == "[":
        index = _skip_ws(text, index + 1)
        if index < len(text) and text[index] == "]":
            return index + 1
        while True:
            index = _skip_ws(text, _skip_json_value(text, index))
            if index < len(text) and text[index] == ",":
                index = _skip_ws(text, index + 1)
                continue
            if index < len(text) and text[index] == "]":
                return index + 1
            raise ContractLifecycleError("invalid nested JSON array delimiter")
    for literal in ("true", "false", "null"):
        if text.startswith(literal, index):
            return index + len(literal)
    match = _JSON_NUMBER_RE.match(text, index)
    if match is not None:
        return match.end()
    raise ContractLifecycleError("invalid JSON scalar")


def _skip_json_string(text: str, index: int) -> int:
    if text[index] != '"':
        raise ContractLifecycleError("JSON string does not begin with a quote")
    index += 1
    while index < len(text):
        char = text[index]
        if char == '"':
            return index + 1
        if ord(char) < 0x20:
            raise ContractLifecycleError("unescaped control character in JSON string")
        if char == "\\":
            index += 1
            if index >= len(text) or text[index] not in '"\\/bfnrtu':
                raise ContractLifecycleError("invalid JSON string escape")
            if text[index] == "u":
                digits = text[index + 1 : index + 5]
                if len(digits) != 4 or re.fullmatch(r"[0-9a-fA-F]{4}", digits) is None:
                    raise ContractLifecycleError("invalid JSON unicode escape")
                index += 4
        index += 1
    raise ContractLifecycleError("unterminated JSON string")


def _verify_three_native_trajectories(trace_root: Path, task_id: str) -> None:
    trace_dir = _regular_directory(trace_root, "native trace root")
    parts = task_id.split(":")
    if len(parts) != 3:
        raise ContractLifecycleError(f"invalid AgentDojo task ID: {task_id}")
    suite, user_task, injection_task = parts
    expected = {
        f"local/{suite}/{user_task}/none/none.json",
        f"local/{suite}/{injection_task}/none/none.json",
        f"local/{suite}/{user_task}/direct/{injection_task}.json",
    }
    observed = {
        path.relative_to(trace_dir).as_posix()
        for path in trace_dir.rglob("*")
        if path.is_file()
    }
    if observed != expected:
        raise ContractLifecycleError(
            f"native trajectory set differs for {task_id}: "
            f"missing={sorted(expected - observed)}, extra={sorted(observed - expected)}"
        )


def _verify_artifact_coverage(
    *,
    job_dir: Path,
    staging_root: Path,
    job_inventory_files: Sequence[Mapping[str, Any]],
    artifact_paths: set[Path],
    control_files: set[Path],
) -> None:
    """Reject bytes that are neither control files nor covered by a locked artifact."""

    artifact_files = {path for path in artifact_paths if path.is_file()}
    artifact_directories = tuple(path for path in artifact_paths if path.is_dir())
    uncovered: list[str] = []
    for item in job_inventory_files:
        file_path = staging_root / str(item["relative_path"])
        _require_under(file_path.resolve(), job_dir, "job inventory file")
        if file_path in control_files or file_path in artifact_files:
            continue
        if any(
            _is_relative_to(file_path, directory) for directory in artifact_directories
        ):
            continue
        uncovered.append(file_path.relative_to(job_dir).as_posix())
    if uncovered:
        raise ContractLifecycleError(
            f"job contains files outside the locked artifact graph: {uncovered[:10]}"
        )


def _tree_inventory(root: str | Path) -> TreeInventory:
    resolved = _regular_directory(root, "inventory root")
    files: list[dict[str, Any]] = []
    for path in sorted(resolved.rglob("*")):
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise ContractLifecycleError(f"inventory root contains a symlink: {path}")
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode):
            raise ContractLifecycleError(
                f"inventory root contains a special filesystem node: {path}"
            )
        if info.st_nlink != 1:
            raise ContractLifecycleError(
                f"inventory root contains a hardlinked file: {path}"
            )
        files.append(
            {
                "relative_path": path.relative_to(resolved).as_posix(),
                "sha256": sha256_file(path),
                "size_bytes": info.st_size,
            }
        )
    tree_hash = sha256_object(
        [{"path": item["relative_path"], "sha256": item["sha256"]} for item in files]
    )
    return TreeInventory(root=resolved, files=tuple(files), tree_sha256=tree_hash)


def _inventory_digest_for_path(
    path: Path,
    *,
    staging_root: Path,
    inventory: TreeInventory,
    inventory_by_path: Mapping[str, Mapping[str, Any]] | None = None,
    candidate_files: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[str, int]:
    resolved = path.resolve()
    _require_under(resolved, staging_root, "inventory artifact")
    if path.is_symlink():
        raise ContractLifecycleError(f"artifact path is a symlink: {path}")
    by_path = inventory_by_path or inventory.by_path()
    if resolved.is_file():
        relative = resolved.relative_to(staging_root).as_posix()
        item = by_path.get(relative)
        if item is None:
            raise ContractLifecycleError(
                f"artifact file is absent from inventory: {path}"
            )
        return str(item["sha256"]), int(item["size_bytes"])
    if resolved.is_dir():
        prefix = resolved.relative_to(staging_root).as_posix().rstrip("/") + "/"
        members = [
            item
            for item in (candidate_files or inventory.files)
            if str(item["relative_path"]).startswith(prefix)
        ]
        digest_entries = [
            {
                "path": str(item["relative_path"])[len(prefix) :],
                "sha256": item["sha256"],
            }
            for item in members
        ]
        return sha256_object(digest_entries), sum(
            int(item["size_bytes"]) for item in members
        )
    raise ContractLifecycleError(f"artifact path does not exist: {path}")


def _atomic_promote_tree(
    *, source_inventory: TreeInventory, destination: Path
) -> dict[str, str]:
    candidate = resolve_repo_path(destination)
    if candidate.is_symlink():
        raise ContractLifecycleError(f"formal destination is a symlink: {candidate}")
    destination = candidate.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        existing = _tree_inventory(destination)
        _assert_inventory_equal(source_inventory, existing)
        return {
            str(item["relative_path"]): "existing_verified"
            for item in source_inventory.files
        }

    temp_root = destination.parent / f".{destination.name}.promoting-{uuid.uuid4().hex}"
    temp_root.mkdir(mode=0o700)
    methods: dict[str, str] = {}
    try:
        for item in source_inventory.files:
            relative = Path(str(item["relative_path"]))
            source = source_inventory.root / relative
            target = temp_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            # A formal tree must not share mutable inodes with staging.  Copying
            # followed by full inventory verification is the only permitted
            # first-publication method; hardlinks are rejected below.
            shutil.copyfile(source, target, follow_symlinks=False)
            method = "copy"
            methods[relative.as_posix()] = method
        staged = _tree_inventory(temp_root)
        _assert_inventory_equal(source_inventory, staged)
        _fsync_tree(temp_root)
        _rename_directory_noreplace(temp_root, destination)
        _fsync_directory(destination.parent)
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)
    return methods


def _rename_directory_noreplace(source: Path, destination: Path) -> None:
    """Atomically publish a same-filesystem directory without replacement."""

    if os.path.lexists(destination):
        raise ContractLifecycleError(
            f"atomic promotion destination already exists: {destination}"
        )
    if source.stat().st_dev != destination.parent.stat().st_dev:
        raise ContractLifecycleError(
            "atomic promotion requires a same-filesystem destination"
        )
    source_bytes = os.fsencode(source)
    destination_bytes = os.fsencode(destination)
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin":
        renamex_np = getattr(libc, "renamex_np", None)
        if renamex_np is None:
            raise ContractLifecycleError(
                "renamex_np(RENAME_EXCL) is required for formal promotion"
            )
        renamex_np.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        renamex_np.restype = ctypes.c_int
        result = renamex_np(source_bytes, destination_bytes, 0x00000004)
    else:
        renameat2 = getattr(libc, "renameat2", None)
        if renameat2 is None:
            raise ContractLifecycleError(
                "renameat2(RENAME_NOREPLACE) is required for formal promotion"
            )
        renameat2.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        renameat2.restype = ctypes.c_int
        result = renameat2(-100, source_bytes, -100, destination_bytes, 1)
    if result == 0:
        return
    observed = ctypes.get_errno()
    if observed == errno.EEXIST:
        raise ContractLifecycleError(
            f"atomic promotion destination appeared concurrently: {destination}"
        )
    raise OSError(observed, os.strerror(observed), str(destination))


def _fsync_tree(root: Path) -> None:
    directory = _regular_directory(root, "promotion temporary tree")
    for path in sorted(candidate for candidate in directory.rglob("*") if candidate.is_file()):
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ContractLifecycleError(
                f"promotion temporary tree contains an unsafe file: {path}"
            )
        with path.open("rb") as handle:
            os.fsync(handle.fileno())
    for path in sorted(
        (candidate for candidate in directory.rglob("*") if candidate.is_dir()),
        key=lambda candidate: len(candidate.parts),
        reverse=True,
    ):
        _fsync_directory(path)
    _fsync_directory(directory)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _assert_no_hardlinks(root: Path, label: str) -> None:
    resolved = _regular_directory(root, label)
    hardlinks = [
        path
        for path in resolved.rglob("*")
        if path.is_file() and path.stat().st_nlink != 1
    ]
    if hardlinks:
        raise ContractLifecycleError(
            f"{label} contains hardlinks: {hardlinks[:5]}"
        )


def _score_empty_snapshot(roots: Sequence[str | Path]) -> dict[str, Any]:
    canonical = [resolve_repo_path(path).resolve() for path in roots]
    if len(canonical) < 2 or len(set(canonical)) != len(canonical):
        raise ContractLifecycleError(
            "at least two distinct canonical score namespaces are required"
        )
    snapshots: list[dict[str, Any]] = []
    for root in canonical:
        if root.is_symlink():
            raise ContractLifecycleError(f"score namespace is a symlink: {root}")
        files = [] if not root.exists() else [p for p in root.rglob("*") if p.is_file()]
        symlinks = (
            [] if not root.exists() else [p for p in root.rglob("*") if p.is_symlink()]
        )
        if symlinks:
            raise ContractLifecycleError(
                f"score namespace contains symlinks: {symlinks[:5]}"
            )
        if files:
            raise ContractLifecycleError(
                f"score namespace is not empty: {root} ({len(files)} files)"
            )
        snapshots.append({"path": _display(root), "file_count": 0})
    return {"roots": snapshots, "all_empty": True}


def _verify_formal_execution_receipts(
    *,
    completion_path: str | Path,
    anomaly_path: str | Path,
    execution_lock_path: Path,
    execution_lock_sha256: str,
    execution_policy_sha256: str,
    execution_definition: Mapping[str, Any],
    remote_completion_index_path: str | Path = DEFAULT_FORMAL_REMOTE_COMPLETION_INDEX,
) -> dict[str, dict[str, str]]:
    """Verify the exact v2 blind freeze graph without opening raw evidence."""

    completion_file = _regular_file(
        completion_path, "formal blind execution completion receipt"
    )
    anomaly_file = _regular_file(anomaly_path, "formal blind anomaly receipt")
    completion = load_mapping(completion_file)
    anomaly = load_mapping(anomaly_file)
    completion_fields = {
        "schema_version",
        "status",
        "frozen_at",
        "execution_lock_sha256",
        "execution_policy_sha256",
        "plan_index_sha256",
        "namespace_init_receipt_sha256",
        "completion_journal_relative_path",
        "completion_journal_file_sha256",
        "completion_journal_entry_count",
        "completion_journal_entry_set_sha256",
        "completion_index_relative_path",
        "completion_index_file_sha256",
        "completion_index_semantic_sha256",
        "completion_index_entries_sha256",
        "failed_attempt_journal_relative_path",
        "failed_attempt_journal_file_sha256",
        "failed_attempt_journal_entry_count",
        "failed_attempt_journal_entry_set_sha256",
        "canonical_job_count",
        "native_trajectory_count",
        "unresolved_failure_count",
        "lifecycle_lock_relative_path",
        "blind_only",
        "contains_case_agent_prompt_response_trajectory_evaluator_or_label",
    }
    if set(completion) != completion_fields:
        raise ContractLifecycleError("formal completion v2 field set differs")
    for actual, expected, label in (
        (
            completion.get("schema_version"),
            "agentdojo_formal_execution_completion_receipt/v2",
            "schema",
        ),
        (completion.get("status"), "frozen", "status"),
        (completion.get("execution_lock_sha256"), execution_lock_sha256, "lock"),
        (
            completion.get("execution_policy_sha256"),
            execution_policy_sha256,
            "policy",
        ),
        (
            completion.get("canonical_job_count"),
            EXPECTED_RECORD_SLOT_COUNT,
            "canonical job count",
        ),
        (
            completion.get("native_trajectory_count"),
            EXPECTED_RECORD_SLOT_COUNT * 3,
            "native trajectory count",
        ),
        (completion.get("unresolved_failure_count"), 0, "unresolved failures"),
        (completion.get("blind_only"), True, "blind flag"),
        (
            completion.get(
                "contains_case_agent_prompt_response_trajectory_evaluator_or_label"
            ),
            False,
            "content boundary",
        ),
    ):
        _assert_equal(actual, expected, f"formal completion receipt {label}")
    parse_timestamp(str(completion.get("frozen_at") or ""), "completion frozen_at")

    plan_path = _regular_file(
        EXPERIMENT_ROOT
        / "execution_plan"
        / execution_lock_sha256
        / "plan_index.json",
        "formal execution plan index",
    )
    _assert_equal(
        completion.get("plan_index_sha256"),
        sha256_file(plan_path),
        "formal completion plan index hash",
    )
    namespace_file = _regular_file(
        DEFAULT_FORMAL_NAMESPACE_INIT_RECEIPT,
        "formal namespace-init receipt",
    )
    _assert_equal(
        completion.get("namespace_init_receipt_sha256"),
        sha256_file(namespace_file),
        "formal completion namespace-init hash",
    )

    metadata_root = completion_file.parent
    index_relative = _safe_blind_relative(
        completion.get("completion_index_relative_path"), "completion index"
    )
    remote_index_file = _regular_file(
        metadata_root / index_relative, "formal blind remote completion index"
    )
    canonical_remote_index = _regular_file(
        remote_completion_index_path, "canonical formal blind remote completion index"
    )
    _assert_equal(remote_index_file, canonical_remote_index, "completion index path")
    remote_index = load_mapping(remote_index_file)
    _assert_equal(
        completion.get("completion_index_file_sha256"),
        sha256_file(remote_index_file),
        "completion index file hash",
    )
    _assert_equal(
        completion.get("completion_index_semantic_sha256"),
        sha256_object(remote_index),
        "completion index semantic hash",
    )

    index_fields = {
        "schema_version",
        "status",
        "frozen_at",
        "execution_lock_sha256",
        "execution_policy_sha256",
        "plan_index_sha256",
        "entry_order",
        "entry_count",
        "native_trajectory_count",
        "completion_journal_relative_path",
        "completion_journal_file_sha256",
        "completion_journal_entry_count",
        "completion_journal_entry_set_sha256",
        "entries_sha256",
        "entries",
        "blind_only",
        "contains_case_agent_prompt_response_trajectory_evaluator_or_label",
    }
    if set(remote_index) != index_fields:
        raise ContractLifecycleError("formal remote completion index v2 fields differ")
    for actual, expected, label in (
        (
            remote_index.get("schema_version"),
            "agentdojo_formal_remote_completion_index/v2",
            "schema",
        ),
        (remote_index.get("status"), "frozen", "status"),
        (remote_index.get("execution_lock_sha256"), execution_lock_sha256, "lock"),
        (
            remote_index.get("execution_policy_sha256"),
            execution_policy_sha256,
            "policy",
        ),
        (remote_index.get("plan_index_sha256"), sha256_file(plan_path), "plan"),
        (remote_index.get("entry_order"), "execution_lock_job_plan", "order"),
        (remote_index.get("entry_count"), EXPECTED_RECORD_SLOT_COUNT, "count"),
        (
            remote_index.get("native_trajectory_count"),
            EXPECTED_RECORD_SLOT_COUNT * 3,
            "native count",
        ),
        (remote_index.get("completion_journal_entry_count"), EXPECTED_RECORD_SLOT_COUNT, "journal count"),
        (remote_index.get("blind_only"), True, "blind flag"),
        (
            remote_index.get(
                "contains_case_agent_prompt_response_trajectory_evaluator_or_label"
            ),
            False,
            "content boundary",
        ),
    ):
        _assert_equal(actual, expected, f"formal remote completion index {label}")
    parse_timestamp(str(remote_index.get("frozen_at") or ""), "index frozen_at")

    journal_relative = _safe_blind_relative(
        remote_index.get("completion_journal_relative_path"), "completion journal"
    )
    _assert_equal(
        completion.get("completion_journal_relative_path"),
        journal_relative,
        "completion/index journal path",
    )
    journal_file = _regular_file(
        metadata_root / journal_relative, "formal completion journal"
    )
    journal_rows = _load_jsonl_objects(journal_file, "formal completion journal")
    if len(journal_rows) != EXPECTED_RECORD_SLOT_COUNT:
        raise ContractLifecycleError(
            "formal completion journal must contain exactly 2,847 entries"
        )
    normalized_journal = [
        _normalize_completion_journal_entry(item) for item in journal_rows
    ]
    journal_set_sha = sha256_object(
        sorted(normalized_journal, key=lambda item: str(item["job_binding_sha256"]))
    )
    for actual, expected, label in (
        (remote_index.get("completion_journal_file_sha256"), sha256_file(journal_file), "index journal file hash"),
        (remote_index.get("completion_journal_entry_set_sha256"), journal_set_sha, "index journal set hash"),
        (completion.get("completion_journal_file_sha256"), sha256_file(journal_file), "completion journal file hash"),
        (completion.get("completion_journal_entry_count"), EXPECTED_RECORD_SLOT_COUNT, "completion journal count"),
        (completion.get("completion_journal_entry_set_sha256"), journal_set_sha, "completion journal set hash"),
    ):
        _assert_equal(actual, expected, label)

    remote_entries = list(remote_index.get("entries") or [])
    if len(remote_entries) != EXPECTED_RECORD_SLOT_COUNT:
        raise ContractLifecycleError(
            "formal remote completion index must contain exactly 2,847 entries"
        )
    validated_entries = [
        _validate_remote_completion_entry(
            item,
            execution_lock_sha256=execution_lock_sha256,
            execution_policy_sha256=execution_policy_sha256,
            execution_definition=execution_definition,
        )
        for item in remote_entries
    ]
    _assert_equal(
        remote_index.get("entries_sha256"),
        sha256_object(validated_entries),
        "formal remote completion entries hash",
    )
    _assert_equal(
        completion.get("completion_index_entries_sha256"),
        sha256_object(validated_entries),
        "completion receipt index entries hash",
    )
    _assert_equal(
        sorted(validated_entries, key=lambda item: str(item["job_binding_sha256"])),
        sorted(normalized_journal, key=lambda item: str(item["job_binding_sha256"])),
        "completion journal/index entry set",
    )
    _verify_remote_completion_plan_order(
        entries=validated_entries,
        plan_path=plan_path,
        execution_lock_sha256=execution_lock_sha256,
        execution_policy_sha256=execution_policy_sha256,
    )

    failed_relative = _safe_blind_relative(
        completion.get("failed_attempt_journal_relative_path"),
        "failed-attempt journal",
    )
    failed_file = _regular_file(
        metadata_root / failed_relative, "formal failed-attempt journal"
    )
    failed_rows = _load_jsonl_objects(failed_file, "formal failed-attempt journal")
    _assert_equal(failed_rows, [], "formal failed-attempt journal emptiness")
    for actual, expected, label in (
        (completion.get("failed_attempt_journal_file_sha256"), sha256_file(failed_file), "failed journal file hash"),
        (completion.get("failed_attempt_journal_entry_count"), 0, "failed journal count"),
        (completion.get("failed_attempt_journal_entry_set_sha256"), sha256_object([]), "failed journal set hash"),
    ):
        _assert_equal(actual, expected, label)
    _safe_blind_relative(
        completion.get("lifecycle_lock_relative_path"), "lifecycle lock"
    )

    required_anomaly = {
        "schema_version": "agentdojo_formal_execution_anomaly_receipt/v1",
        "execution_lock_sha256": execution_lock_sha256,
        "execution_policy_sha256": execution_policy_sha256,
        "plan_index_sha256": sha256_file(plan_path),
        "blind_only": True,
        "contains_case_prompt_response_trajectory_evaluator_or_label": False,
    }
    for key, expected in required_anomaly.items():
        _assert_equal(anomaly.get(key), expected, f"formal anomaly receipt {key}")
    return {
        "completion": _path_lock(completion_file),
        "anomaly": _path_lock(anomaly_file),
        "remote_completion_index": _path_lock(remote_index_file),
    }


def _safe_blind_relative(value: Any, label: str) -> str:
    text = str(value or "")
    if not text or "\\" in text:
        raise ContractLifecycleError(f"{label} path is empty or non-POSIX")
    path = Path(text)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ContractLifecycleError(f"{label} path escapes the blind metadata root")
    if path.as_posix() != text:
        raise ContractLifecycleError(f"{label} path is not canonical")
    return text


def _load_jsonl_objects(path: Path, label: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ContractLifecycleError(
                f"{label} line {line_number} is not valid JSON"
            ) from exc
        if not isinstance(value, Mapping):
            raise ContractLifecycleError(f"{label} line {line_number} is not an object")
        rows.append(dict(value))
    return rows


def _normalize_completion_journal_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    expected = (set(COMPLETION_INDEX_ENTRY_FIELDS) - {"schema_version"}) | {
        "schema_version",
        "recorded_at",
    }
    if set(entry) != expected:
        raise ContractLifecycleError("formal completion journal entry fields differ")
    _assert_equal(
        entry.get("schema_version"),
        "agentdojo_formal_remote_completion_journal_entry/v2",
        "formal completion journal schema",
    )
    parse_timestamp(
        str(entry.get("recorded_at") or ""), "completion journal recorded_at"
    )
    normalized = {
        key: value for key, value in entry.items() if key != "recorded_at"
    }
    normalized["schema_version"] = (
        "agentdojo_formal_remote_completion_index_entry/v2"
    )
    return normalized


def _validate_remote_completion_entry(
    value: Any,
    *,
    execution_lock_sha256: str,
    execution_policy_sha256: str,
    execution_definition: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != set(COMPLETION_INDEX_ENTRY_FIELDS):
        raise ContractLifecycleError("formal completion index entry fields differ")
    entry = dict(value)
    for actual, expected, label in (
        (
            entry.get("schema_version"),
            "agentdojo_formal_remote_completion_index_entry/v2",
            "entry schema",
        ),
        (entry.get("execution_lock_sha256"), execution_lock_sha256, "entry lock"),
        (
            entry.get("execution_policy_sha256"),
            execution_policy_sha256,
            "entry policy",
        ),
        (entry.get("native_episode_count"), 3, "entry native count"),
        (entry.get("blind_only"), True, "entry blind flag"),
        (
            entry.get(
                "contains_case_agent_prompt_response_trajectory_evaluator_or_label"
            ),
            False,
            "entry content boundary",
        ),
    ):
        _assert_equal(actual, expected, label)
    for field in (
        "job_binding_sha256",
        "job_identity_sha256",
        "stage_authorization_sha256",
        "formal_execution_context_sha256",
        "completion_marker_file_sha256",
        "completion_marker_semantic_sha256",
        "artifact_tree_sha256",
        "attempt_tree_sha256",
        "supervisor_exit_receipt_sha256",
    ):
        if re.fullmatch(r"[a-f0-9]{64}", str(entry.get(field) or "")) is None:
            raise ContractLifecycleError(f"formal completion entry {field} is invalid")
    for field in (
        "artifact_file_count",
        "artifact_total_bytes",
        "attempt_file_count",
        "attempt_total_bytes",
    ):
        number = entry.get(field)
        if isinstance(number, bool) or not isinstance(number, int) or number < 1:
            raise ContractLifecycleError(f"formal completion entry {field} is invalid")
    binding = str(entry["job_binding_sha256"])
    _assert_equal(
        entry.get("canonical_job_relative_path"), binding, "canonical job path"
    )
    _assert_equal(
        entry.get("completion_marker_relative_path"),
        f"{binding}/adapter/formal_job_completion.json",
        "completion marker path",
    )
    promotion = _mapping(
        _mapping(
            execution_definition.get("concurrency_policy"), "concurrency policy"
        ).get("promotion_policy"),
        "promotion policy",
    )
    if entry.get("formal_stage_id") not in list(
        promotion.get("formal_stage_order") or []
    ):
        raise ContractLifecycleError("formal completion entry stage is not locked")
    if not isinstance(entry.get("formal_stage_session_id"), str) or not entry[
        "formal_stage_session_id"
    ]:
        raise ContractLifecycleError("formal completion entry session is invalid")
    return entry


def _verify_remote_completion_plan_order(
    *,
    entries: Sequence[Mapping[str, Any]],
    plan_path: Path,
    execution_lock_sha256: str,
    execution_policy_sha256: str,
) -> None:
    plan = load_mapping(plan_path)
    plan_entries = list(plan.get("entries") or [])
    if (
        plan.get("schema_version") != "agentdojo_locked_job_plan_index/v2"
        or plan.get("execution_lock_sha256") != execution_lock_sha256
        or plan.get("execution_policy_sha256") != execution_policy_sha256
        or plan.get("job_count") != EXPECTED_RECORD_SLOT_COUNT
        or plan.get("record_slot_count") != EXPECTED_RECORD_SLOT_COUNT
        or len(plan_entries) != EXPECTED_RECORD_SLOT_COUNT
        or plan.get("entries_sha256") != sha256_object(plan_entries)
    ):
        raise ContractLifecycleError("formal plan index denominator/hash differs")
    expected_pairs: list[tuple[str, str]] = []
    for item in plan_entries:
        if not isinstance(item, Mapping):
            raise ContractLifecycleError("formal plan index entry is malformed")
        job_file = _regular_file(item.get("path"), "formal locked job file")
        _assert_equal(item.get("sha256"), sha256_file(job_file), "locked job file hash")
        job = load_mapping(job_file)
        _assert_equal(
            job.get("execution_lock_sha256"), execution_lock_sha256, "job lock"
        )
        _assert_equal(
            job.get("execution_policy_sha256"), execution_policy_sha256, "job policy"
        )
        expected_pairs.append(
            (formal_job_binding_sha256(job), job_identity_sha256(job))
        )
    observed_pairs = [
        (str(item["job_binding_sha256"]), str(item["job_identity_sha256"]))
        for item in entries
    ]
    _assert_equal(observed_pairs, expected_pairs, "remote completion plan order")
    if len(set(observed_pairs)) != EXPECTED_RECORD_SLOT_COUNT:
        raise ContractLifecycleError("remote completion entries are not unique")


def _formal_completion_timestamp(completion: Mapping[str, Any]) -> datetime:
    return parse_timestamp(
        str(completion.get("frozen_at") or ""),
        "formal completion receipt frozen_at",
    )


def _verify_formal_namespace_init_receipt(
    locked_binding: Any,
    *,
    execution: Any,
    _execution_envelope_only: bool = False,
) -> dict[str, Any]:
    """Verify the post-lock empty-namespace receipt and its runtime bindings."""

    from evidence_system.contracts.agentdojo_execution_namespace import (
        verify_formal_namespace_init_receipt,
    )

    binding = _mapping(locked_binding, "sealed retrieval namespace-init binding")
    verifier_kwargs: dict[str, Any] = {
        "execution_lock_path": execution.lock_path,
    }
    if _execution_envelope_only:
        verifier_kwargs["_execution_envelope_only"] = True
    verified = verify_formal_namespace_init_receipt(
        binding.get("path"), **verifier_kwargs
    )
    _assert_equal(
        binding.get("sha256"),
        verified.sha256,
        "formal namespace-init receipt hash",
    )
    return verified.payload

def _validate_sealed_retrieval_payload(payload: Mapping[str, Any]) -> None:
    report = validate_object(
        "agentdojo_sealed_evidence_retrieval_receipt",
        dict(payload),
        raise_on_error=False,
    )
    if not report.ok:
        raise ContractLifecycleError(
            f"sealed evidence retrieval receipt schema failed: {report.to_dict()}"
        )
    definition = _mapping(payload.get("definition"), "sealed retrieval definition")
    _assert_equal(
        payload.get("definition_sha256"),
        sha256_object(definition),
        "sealed retrieval definition hash",
    )
    parse_timestamp(
        str(payload.get("retrieved_at") or ""), "sealed evidence retrieved_at"
    )
    forbidden = {
        "native_label",
        "native_score",
        "trajectory",
        "evaluator_output",
        "prompt",
        "response",
    }
    if _contains_forbidden_key(payload, forbidden):
        raise ContractLifecycleError(
            "sealed evidence retrieval receipt leaked evidence content"
        )


def _verify_score_output_precondition(
    locked: Any,
    roots: Sequence[str | Path],
    *,
    require_empty: bool,
) -> None:
    snapshot = _mapping(locked, "score output precondition")
    locked_roots = list(snapshot.get("roots") or [])
    canonical = [resolve_repo_path(path).resolve() for path in roots]
    if len(canonical) < 2 or len(set(canonical)) != len(canonical):
        raise ContractLifecycleError(
            "at least two distinct canonical score namespaces are required"
        )
    expected = [{"path": _display(path), "file_count": 0} for path in canonical]
    _assert_equal(snapshot.get("all_empty"), True, "locked score-root emptiness")
    _assert_equal(locked_roots, expected, "locked score-root identities")
    if require_empty:
        _assert_equal(
            _score_empty_snapshot(roots),
            {"roots": expected, "all_empty": True},
            "current score-root emptiness",
        )


def _seal_tree_read_only(root: Path) -> None:
    """Remove every write bit from a promoted evidence tree."""

    resolved = _regular_directory(root, "formal evidence root")
    _reject_tree_symlinks(resolved, "formal evidence root")
    for path in resolved.rglob("*"):
        if path.is_file():
            path.chmod(
                path.stat().st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
            )
    directories = sorted(
        (path for path in resolved.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for path in (*directories, resolved):
        path.chmod(path.stat().st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def _assert_tree_read_only(root: Path) -> None:
    resolved = _regular_directory(root, "formal evidence root")
    writable = [
        path
        for path in (resolved, *resolved.rglob("*"))
        if path.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
    ]
    if writable:
        sample = [_display(path) for path in writable[:5]]
        raise ContractLifecycleError(
            f"formal evidence tree is not sealed read-only: {sample}"
        )


def _verify_promoted_namespace_layout(
    *, namespace_root: str | Path, destination: TreeInventory
) -> dict[str, str]:
    """Reject every post-promotion node not bound by the receipt inventory.

    The only permitted regular files are ``NAMESPACE_LOCK.json`` and the exact
    destination inventory.  The only permitted directories are ancestors of
    the formal evidence root and parents required by those exact files.  This
    also rejects empty unbound directories, symlinks, special files, and
    multiply-linked files outside the destination tree.
    """

    root = _regular_directory(namespace_root, "formal result namespace")
    formal_root = destination.root
    _require_under(formal_root, root, "formal evidence root")
    if formal_root == root:
        raise ContractLifecycleError(
            "formal evidence root must be below the reserved namespace root"
        )
    marker_lock = _namespace_reservation_marker(
        namespace_root=root,
        formal_evidence_root=formal_root,
    )
    marker_path = _resolve_locked_path(marker_lock["path"], "namespace reservation")

    allowed_files = {marker_path}
    allowed_directories: set[Path] = {formal_root}
    ancestor = formal_root.parent
    while ancestor != root:
        allowed_directories.add(ancestor)
        ancestor = ancestor.parent
    if ancestor != root:
        raise ContractLifecycleError("formal evidence root escapes namespace root")
    for item in destination.files:
        file_path = formal_root / str(item["relative_path"])
        allowed_files.add(file_path)
        parent = file_path.parent
        while parent != formal_root:
            allowed_directories.add(parent)
            parent = parent.parent

    stack = [root]
    while stack:
        directory = stack.pop()
        with os.scandir(directory) as iterator:
            entries = sorted(iterator, key=lambda item: item.name)
        for entry in entries:
            path = Path(entry.path)
            info = entry.stat(follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode):
                raise ContractLifecycleError(
                    f"formal namespace contains a symlink: {path}"
                )
            if stat.S_ISDIR(info.st_mode):
                if path not in allowed_directories:
                    raise ContractLifecycleError(
                        f"formal namespace contains an unbound directory: {path}"
                    )
                stack.append(path)
                continue
            if not stat.S_ISREG(info.st_mode):
                raise ContractLifecycleError(
                    f"formal namespace contains a special filesystem node: {path}"
                )
            if info.st_nlink != 1:
                raise ContractLifecycleError(
                    f"formal namespace contains a hardlinked file: {path}"
                )
            if path not in allowed_files:
                raise ContractLifecycleError(
                    f"formal namespace contains an unbound file: {path}"
                )
    return marker_lock


def _require_reserved_formal_namespace(
    *, namespace_root: str | Path, formal_evidence_root: str | Path
) -> dict[str, Any]:
    """Require exactly the immutable reservation marker before first promotion."""

    root = _regular_directory(namespace_root, "formal result namespace")
    marker_lock = _namespace_reservation_marker(
        namespace_root=root,
        formal_evidence_root=formal_evidence_root,
    )
    marker_path = _resolve_locked_path(marker_lock["path"], "namespace reservation")
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if files != [marker_path]:
        unexpected = [
            path.relative_to(root).as_posix() for path in files if path != marker_path
        ]
        raise ContractLifecycleError(
            "formal namespace must contain only NAMESPACE_LOCK.json before promotion: "
            f"unexpected={unexpected[:10]}"
        )
    return marker_lock


def _namespace_reservation_marker(
    *, namespace_root: str | Path, formal_evidence_root: str | Path
) -> dict[str, str]:
    root = _regular_directory(namespace_root, "formal result namespace")
    evidence_root = resolve_repo_path(formal_evidence_root).resolve()
    _require_under(evidence_root, root, "formal evidence root")
    marker_path = _regular_file(root / "NAMESPACE_LOCK.json", "namespace reservation")
    marker = load_mapping(marker_path)
    expected = {
        "schema_version": "result_namespace_lock/v1",
        "result_namespace": RESULT_NAMESPACE,
        "experiment_manifest_path": (
            "experiments/agentdojo_full_v1.2.2_direct/experiment_manifest.yaml"
        ),
        "formal_result_root": _display(evidence_root),
        "legacy_result_root": "results/full/agentdojo",
        "legacy_result_root_must_not_be_modified": True,
        "status": "reserved_no_formal_runs_yet",
    }
    _assert_equal(marker, expected, "formal namespace reservation metadata")
    return {"path": _display(marker_path), "sha256": sha256_file(marker_path)}


def _validate_evidence_index_payload(payload: Mapping[str, Any]) -> None:
    report = validate_object(
        "agentdojo_full_evidence_acceptance_index", dict(payload), raise_on_error=False
    )
    if not report.ok:
        raise ContractLifecycleError(
            f"evidence acceptance index schema failed: {report.to_dict()}"
        )
    _validate_definition_hash(payload, "evidence acceptance index")
    definition = _mapping(payload.get("definition"), "evidence definition")
    entries = list(definition.get("entries") or [])
    _assert_equal(
        definition.get("entries_sha256"), sha256_object(entries), "entry index hash"
    )
    identities = [
        (str(item.get("case_unit_id")), str(item.get("agent_id")))
        for item in entries
        if isinstance(item, Mapping)
    ]
    if len(identities) != EXPECTED_RECORD_SLOT_COUNT or len(set(identities)) != len(
        identities
    ):
        raise ContractLifecycleError(
            "evidence index identities are not a 2,847-slot bijection"
        )
    forbidden = {"native_label", "native_score", "trajectory", "evaluator_output"}
    if _contains_forbidden_key(payload, forbidden):
        raise ContractLifecycleError(
            "evidence index leaked outcome or trajectory content"
        )


def _validate_promotion_payload(payload: Mapping[str, Any]) -> None:
    report = validate_object(
        "agentdojo_full_evidence_promotion_receipt", dict(payload), raise_on_error=False
    )
    if not report.ok:
        raise ContractLifecycleError(
            f"promotion receipt schema failed: {report.to_dict()}"
        )
    _validate_definition_hash(payload, "promotion receipt")
    definition = _mapping(payload.get("definition"), "promotion definition")
    files = list(definition.get("files") or [])
    _assert_equal(
        definition.get("inventory_sha256"), sha256_object(files), "promotion inventory"
    )
    relatives = [
        str(item.get("relative_path")) for item in files if isinstance(item, Mapping)
    ]
    if len(relatives) != len(set(relatives)):
        raise ContractLifecycleError("promotion receipt contains duplicate files")
    for item in files:
        if not isinstance(item, Mapping) or item.get("source_sha256") != item.get(
            "destination_sha256"
        ):
            raise ContractLifecycleError("promotion receipt contains a byte mismatch")


def _validate_join_payload(payload: Mapping[str, Any]) -> None:
    report = validate_object(
        "agentdojo_full_prescore_join_lock", dict(payload), raise_on_error=False
    )
    if not report.ok:
        raise ContractLifecycleError(
            f"pre-score join schema failed: {report.to_dict()}"
        )
    _validate_definition_hash(payload, "pre-score join lock")
    definition = _mapping(payload.get("definition"), "pre-score join definition")
    hash_graph = _mapping(definition.get("hash_graph"), "pre-score join hash graph")
    binding_fields = {
        "execution_lock_sha256": "execution_lock",
        "checklist_freeze_sha256": "checklist_freeze_lock",
        "review_quiescence_receipt_sha256": "review_quiescence_receipt",
        "sealed_retrieval_receipt_sha256": "sealed_retrieval_receipt",
        "evidence_acceptance_index_sha256": "evidence_acceptance_index",
        "promotion_receipt_sha256": "promotion_receipt",
        "score_prompt_sha256": "score_prompt",
        "score_schema_sha256": "score_schema",
    }
    for hash_field, binding_field in binding_fields.items():
        binding = _mapping(
            definition.get(binding_field), f"pre-score join {binding_field}"
        )
        _assert_equal(
            hash_graph.get(hash_field),
            binding.get("sha256"),
            f"pre-score join {hash_field}",
        )
    formal = _mapping(definition.get("formal_evidence"), "pre-score formal evidence")
    _assert_equal(
        hash_graph.get("formal_evidence_tree_sha256"),
        formal.get("tree_sha256"),
        "pre-score formal evidence tree hash",
    )
    _assert_equal(
        definition.get("join_inputs_sha256"),
        sha256_object(hash_graph),
        "pre-score join input aggregate hash",
    )


def _validate_definition_hash(payload: Mapping[str, Any], label: str) -> None:
    definition = _mapping(payload.get("definition"), f"{label} definition")
    _assert_equal(
        payload.get("definition_sha256"),
        sha256_object(definition),
        f"{label} definition hash",
    )
    parse_timestamp(str(payload.get("locked_at") or ""), "locked_at")


def _publish_once(
    output_path: str | Path,
    payload: Mapping[str, Any],
    *,
    schema_name: str,
    definition: Mapping[str, Any],
    validate_payload: Callable[[Mapping[str, Any]], None],
) -> LockedArtifactResult:
    candidate = resolve_repo_path(output_path)
    if candidate.is_symlink():
        raise ContractLifecycleError(f"{schema_name} output is a symlink: {candidate}")
    output = candidate.resolve()
    if output.exists():
        existing = load_mapping(output)
        validate_payload(existing)
        if existing.get("definition") != definition:
            raise ContractLifecycleError(
                f"{schema_name} already exists with a different immutable definition"
            )
        return LockedArtifactResult(
            path=output,
            sha256=sha256_file(output),
            definition=dict(definition),
            created=False,
        )
    _atomic_write_json(output, payload)
    if load_mapping(output) != dict(payload):
        raise ContractLifecycleError(f"{schema_name} atomic readback differs")
    return LockedArtifactResult(
        path=output,
        sha256=sha256_file(output),
        definition=dict(definition),
        created=True,
    )


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    temp_path = Path(temporary)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, 0o600)
        try:
            os.link(temp_path, path, follow_symlinks=False)
        except FileExistsError as exc:
            raise ContractLifecycleError(
                f"immutable publication destination appeared concurrently: {path}"
            ) from exc
        _fsync_directory(path.parent)
    finally:
        if temp_path.exists():
            temp_path.unlink()
            _fsync_directory(path.parent)


def _inventory_hash(
    inventory: Mapping[str, Mapping[str, Any]], relative_path: str
) -> str:
    item = inventory.get(relative_path)
    if item is None:
        raise ContractLifecycleError(
            f"file is absent from tree inventory: {relative_path}"
        )
    return str(item["sha256"])


def _assert_inventory_equal(expected: TreeInventory, actual: TreeInventory) -> None:
    expected_projection = [
        (item["relative_path"], item["sha256"], item["size_bytes"])
        for item in expected.files
    ]
    actual_projection = [
        (item["relative_path"], item["sha256"], item["size_bytes"])
        for item in actual.files
    ]
    if expected_projection != actual_projection:
        raise ContractLifecycleError(
            "source/destination file inventories are not byte-identical"
        )


def _path_lock(path: str | Path) -> dict[str, str]:
    file = _regular_file(path, "locked file")
    return {"path": _display(file), "sha256": sha256_file(file)}


def _regular_file(path: str | Path, label: str) -> Path:
    candidate = resolve_repo_path(path)
    if candidate.is_symlink():
        raise ContractLifecycleError(f"{label} is a symlink: {candidate}")
    resolved = candidate.resolve()
    if not resolved.is_file():
        raise ContractLifecycleError(f"{label} is not a regular file: {resolved}")
    return resolved


def _regular_directory(path: str | Path, label: str) -> Path:
    candidate = resolve_repo_path(path)
    if candidate.is_symlink():
        raise ContractLifecycleError(f"{label} is a symlink: {candidate}")
    resolved = candidate.resolve()
    if not resolved.is_dir():
        raise ContractLifecycleError(f"{label} is not a regular directory: {resolved}")
    return resolved


def _reject_tree_symlinks(root: Path, label: str) -> None:
    symlinks = [path for path in root.rglob("*") if path.is_symlink()]
    if symlinks:
        raise ContractLifecycleError(f"{label} contains symlinks: {symlinks[:5]}")


def _resolve_locked_path(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ContractLifecycleError(f"{label} is missing")
    return resolve_repo_path(value).resolve()


def _resolve_declared_under(value: Any, root: Path, label: str) -> Path:
    resolved = _resolve_locked_path(value, label)
    _require_under(resolved, root, label)
    if resolved.is_symlink() or not resolved.exists():
        raise ContractLifecycleError(f"{label} is missing or a symlink: {resolved}")
    return resolved


def _require_under(path: Path, root: Path, label: str) -> None:
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ContractLifecycleError(
            f"{label} escapes its locked root: {path}"
        ) from exc


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _assert_declared_path(value: Any, expected: Path, label: str) -> None:
    actual = _resolve_locked_path(value, label)
    if actual != expected.resolve():
        raise ContractLifecycleError(
            f"{label} differs: expected={expected.resolve()}, actual={actual}"
        )


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractLifecycleError(f"{label} must be an object")
    return dict(value)


def _assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ContractLifecycleError(
            f"{label} differs: expected={expected!r}, actual={actual!r}"
        )


def _display(path: str | Path) -> str:
    resolved = resolve_repo_path(path).resolve()
    try:
        return resolved.relative_to(repo_root()).as_posix()
    except ValueError:
        return str(resolved)


def _timestamp(value: str | None) -> str:
    timestamp = value or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    parse_timestamp(timestamp, "locked_at")
    return timestamp


def _skip_ws(text: str, index: int) -> int:
    while index < len(text) and text[index] in " \t\r\n":
        index += 1
    return index


def _contains_forbidden_key(value: Any, forbidden: set[str]) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key).lower() in forbidden or _contains_forbidden_key(item, forbidden)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_key(item, forbidden) for item in value)
    return False


__all__ = [
    "DEFAULT_ACCEPTANCE_QUIESCENCE_RECEIPT",
    "DEFAULT_EVIDENCE_INDEX",
    "DEFAULT_FORMAL_EXECUTION_COMPLETION_RECEIPT",
    "DEFAULT_FORMAL_EXECUTION_ANOMALY_RECEIPT",
    "DEFAULT_FORMAL_REMOTE_COMPLETION_INDEX",
    "DEFAULT_JOIN_QUIESCENCE_RECEIPT",
    "DEFAULT_PROMOTION_QUIESCENCE_RECEIPT",
    "DEFAULT_PROMOTION_RECEIPT",
    "DEFAULT_PRESCORE_JOIN_LOCK",
    "DEFAULT_RETRIEVAL_QUIESCENCE_RECEIPT",
    "DEFAULT_SEALED_EVIDENCE_RETRIEVAL_RECEIPT",
    "LockedArtifactResult",
    "build_evidence_acceptance_definition",
    "publish_evidence_acceptance_index",
    "verify_evidence_acceptance_index",
    "verify_sealed_evidence_retrieval_receipt",
    "promote_agentdojo_full_evidence",
    "verify_evidence_promotion_receipt",
    "build_prescore_join_definition",
    "publish_prescore_join_lock",
    "verify_prescore_join_lock",
    "verify_prescore_join_inputs_current",
    "load_prescore_join_lock_envelope",
]
