"""Retrieve sealed AgentDojo evidence through the v2 freeze-gated snapshot path.

The command is intentionally unavailable as a generic copy utility.  It accepts
only the endpoint, paths, helper hash, 2,847-job plan, and ordered blind
completion index frozen by the current execution lock.  Raw bytes are not sent
until checklist-freeze/v2 and a fresh phase-specific quiescence receipt pass.
"""

from __future__ import annotations

import argparse
import base64
import ctypes
from dataclasses import dataclass
from datetime import datetime, timezone
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from typing import Any, Callable, Mapping, Sequence

from evidence_system.adapters.agentdojo_remote_inventory import (
    COMPLETION_INDEX_ENTRY_FIELDS,
    EXPECTED_RECORD_SLOT_COUNT,
    RECEIPT_SCHEMA_VERSION as REMOTE_SNAPSHOT_RECEIPT_SCHEMA_VERSION,
    REQUEST_SCHEMA_VERSION as REMOTE_SNAPSHOT_REQUEST_SCHEMA_VERSION,
)
from evidence_system.adapters.agentdojo_runtime_control import job_identity_sha256
from evidence_system.adapters.runtime import formal_job_binding_sha256
from evidence_system.contracts.agentdojo_checklist_freeze_v2 import (
    DEFAULT_CHECKLIST_FREEZE_V2,
    DEFAULT_QUIESCENCE_MAX_AGE_SECONDS,
)
from evidence_system.contracts.agentdojo_full_evidence import (
    DEFAULT_FORMAL_EXECUTION_COMPLETION_RECEIPT,
    DEFAULT_FORMAL_NAMESPACE_INIT_RECEIPT,
    DEFAULT_CONTROLLER_REMOTE_SNAPSHOT_RECEIPT,
    DEFAULT_FORMAL_REMOTE_COMPLETION_INDEX,
    DEFAULT_RETRIEVAL_QUIESCENCE_RECEIPT,
    DEFAULT_SEALED_EVIDENCE_RETRIEVAL_RECEIPT,
    SEALED_RETRIEVAL_SCHEMA_VERSION,
    LockedArtifactResult,
    _display,
    _mapping,
    _path_lock,
    _regular_file,
    _score_empty_snapshot,
    _verify_checklist_v2_quiescence_gate,
    _verify_formal_execution_receipts,
    _verify_formal_namespace_init_receipt,
    verify_sealed_evidence_retrieval_receipt,
)
from evidence_system.contracts.agentdojo_full_execution import (
    DEFAULT_EXECUTION_LOCK,
    _strict_agentdojo_infra_snapshot,
    verify_execution_lock,
)
from evidence_system.contracts.agentdojo_full_experiment import (
    DEFAULT_SCORE_NAMESPACE_ROOTS,
    EXPERIMENT_ROOT,
    EXPECTED_CASE_COUNT,
)
from evidence_system.contracts.common import (
    ContractLifecycleError,
    load_mapping,
    parse_timestamp,
)
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path


CONTROLLER_REMOTE_SNAPSHOT_SCHEMA_VERSION = (
    "agentdojo_controller_remote_retrieval_snapshot_receipt/v1"
)
_REMOTE_SAFE_PATH_RE = re.compile(r"/[A-Za-z0-9._/-]+")
_SHA256_RE = re.compile(r"[a-f0-9]{64}")


class RetrievalError(ContractLifecycleError):
    """The sealed evidence snapshot cannot be retrieved safely."""


@dataclass(frozen=True)
class RetrievalInputs:
    execution: Any
    checklist: Any
    quiescence: dict[str, Any]
    sealed: dict[str, Any]
    infra: dict[str, Any]
    completion_file: Path
    completion: dict[str, Any]
    remote_index_file: Path
    remote_index: dict[str, Any]
    ordered_entries: tuple[dict[str, Any], ...]
    binding_to_job_id: dict[str, str]
    local_blind_root: Path
    blind_metadata_entries: tuple[dict[str, Any], ...]
    destination: Path
    score_roots: tuple[str | Path, ...]


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execution-lock", type=Path, default=DEFAULT_EXECUTION_LOCK)
    parser.add_argument(
        "--checklist-freeze-lock", type=Path, default=DEFAULT_CHECKLIST_FREEZE_V2
    )
    parser.add_argument(
        "--review-quiescence-receipt",
        type=Path,
        default=DEFAULT_RETRIEVAL_QUIESCENCE_RECEIPT,
    )
    parser.add_argument(
        "--formal-completion-receipt",
        type=Path,
        default=DEFAULT_FORMAL_EXECUTION_COMPLETION_RECEIPT,
    )
    parser.add_argument(
        "--remote-completion-index",
        type=Path,
        default=DEFAULT_FORMAL_REMOTE_COMPLETION_INDEX,
    )
    parser.add_argument(
        "--remote-snapshot-receipt",
        type=Path,
        default=DEFAULT_CONTROLLER_REMOTE_SNAPSHOT_RECEIPT,
    )
    parser.add_argument(
        "--sealed-retrieval-receipt",
        type=Path,
        default=DEFAULT_SEALED_EVIDENCE_RETRIEVAL_RECEIPT,
    )
    parser.add_argument("--score-result-root", type=Path, action="append", default=None)
    parser.add_argument("--verify-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    score_roots: tuple[str | Path, ...] = tuple(
        args.score_result_root or DEFAULT_SCORE_NAMESPACE_ROOTS
    )
    try:
        if args.verify_only:
            result = verify_sealed_evidence_retrieval_receipt(
                receipt_path=args.sealed_retrieval_receipt,
                execution_lock_path=args.execution_lock,
                checklist_freeze_lock_path=args.checklist_freeze_lock,
                review_quiescence_receipt_path=args.review_quiescence_receipt,
                formal_completion_receipt_path=args.formal_completion_receipt,
                remote_completion_index_path=args.remote_completion_index,
            )
            action = "verified"
        else:
            result = retrieve_agentdojo_full_evidence(
                execution_lock_path=args.execution_lock,
                checklist_freeze_lock_path=args.checklist_freeze_lock,
                review_quiescence_receipt_path=args.review_quiescence_receipt,
                formal_completion_receipt_path=args.formal_completion_receipt,
                remote_completion_index_path=args.remote_completion_index,
                controller_remote_snapshot_receipt_path=args.remote_snapshot_receipt,
                sealed_retrieval_receipt_path=args.sealed_retrieval_receipt,
                score_result_roots=score_roots,
            )
            action = "published" if result.created else "verified_existing"
    except (ContractLifecycleError, OSError, ValueError) as exc:
        print(str(exc))
        return 2
    print(
        json.dumps(
            {
                "action": action,
                "path": str(result.path),
                "sha256": result.sha256,
                "counts": result.definition["counts"],
            },
            sort_keys=True,
        )
    )
    return 0


def retrieve_agentdojo_full_evidence(
    *,
    execution_lock_path: str | Path = DEFAULT_EXECUTION_LOCK,
    checklist_freeze_lock_path: str | Path = DEFAULT_CHECKLIST_FREEZE_V2,
    review_quiescence_receipt_path: str
    | Path = DEFAULT_RETRIEVAL_QUIESCENCE_RECEIPT,
    quiescence_max_age_seconds: int = DEFAULT_QUIESCENCE_MAX_AGE_SECONDS,
    formal_completion_receipt_path: str
    | Path = DEFAULT_FORMAL_EXECUTION_COMPLETION_RECEIPT,
    remote_completion_index_path: str | Path = DEFAULT_FORMAL_REMOTE_COMPLETION_INDEX,
    controller_remote_snapshot_receipt_path: str
    | Path = DEFAULT_CONTROLLER_REMOTE_SNAPSHOT_RECEIPT,
    sealed_retrieval_receipt_path: str
    | Path = DEFAULT_SEALED_EVIDENCE_RETRIEVAL_RECEIPT,
    score_result_roots: Sequence[str | Path] = DEFAULT_SCORE_NAMESPACE_ROOTS,
    command_runner: CommandRunner = subprocess.run,
) -> LockedArtifactResult:
    """Retrieve one immutable tar snapshot and publish local staging once."""

    # This is deliberately the first operation.  No SSH process can start and
    # therefore no raw byte can cross the network before this gate passes.
    inputs = _preflight_inputs(
        execution_lock_path=execution_lock_path,
        checklist_freeze_lock_path=checklist_freeze_lock_path,
        review_quiescence_receipt_path=review_quiescence_receipt_path,
        quiescence_max_age_seconds=quiescence_max_age_seconds,
        formal_completion_receipt_path=formal_completion_receipt_path,
        remote_completion_index_path=remote_completion_index_path,
        score_result_roots=score_result_roots,
    )
    sealed_receipt = resolve_repo_path(sealed_retrieval_receipt_path).absolute()
    if sealed_receipt != resolve_repo_path(
        DEFAULT_SEALED_EVIDENCE_RETRIEVAL_RECEIPT
    ).absolute():
        raise RetrievalError("sealed retrieval receipt path is not canonical")
    if _lexists(sealed_receipt):
        return verify_sealed_evidence_retrieval_receipt(
            receipt_path=sealed_receipt,
            execution_lock_path=execution_lock_path,
            checklist_freeze_lock_path=checklist_freeze_lock_path,
            review_quiescence_receipt_path=review_quiescence_receipt_path,
            formal_completion_receipt_path=formal_completion_receipt_path,
            remote_completion_index_path=remote_completion_index_path,
        )
    if _lexists(inputs.destination):
        raise RetrievalError(
            "local canonical staging destination must be absent before retrieval"
        )

    known_hosts = _verify_known_hosts(inputs)
    ssh_argv = _strict_ssh_argv(inputs, known_hosts=known_hosts)
    request = _remote_snapshot_request(inputs)
    remote_receipt = _prepare_remote_snapshot(
        inputs=inputs,
        request=request,
        ssh_argv=ssh_argv,
        command_runner=command_runner,
    )
    controller_receipt_path = resolve_repo_path(
        controller_remote_snapshot_receipt_path
    ).absolute()
    received_at: str | None = None
    if _lexists(controller_receipt_path):
        existing_controller = load_mapping(
            _single_link_regular_file(
                controller_receipt_path, "controller remote snapshot receipt"
            )
        )
        received_at = str(existing_controller.get("received_at") or "")
        parse_timestamp(received_at, "controller snapshot received_at")
    controller_receipt = _controller_remote_snapshot_receipt(
        inputs=inputs,
        request=request,
        remote_receipt=remote_receipt,
        known_hosts=known_hosts,
        received_at=received_at,
    )
    _publish_identical_or_new(controller_receipt_path, controller_receipt)

    destination_parent = _regular_directory(
        inputs.destination.parent, "local staging parent"
    )
    transfer_root = Path(
        tempfile.mkdtemp(
            prefix=f".{inputs.destination.name}.retrieving-",
            dir=destination_parent,
        )
    )
    published = False
    try:
        archive_path = transfer_root / "remote-snapshot.tar"
        _transfer_snapshot_archive(
            inputs=inputs,
            remote_receipt=remote_receipt,
            archive_path=archive_path,
            ssh_argv=ssh_argv,
            command_runner=command_runner,
        )
        snapshot_root = transfer_root / "snapshot-tree"
        snapshot_root.mkdir(mode=0o700)
        remote_files = list(
            _mapping(
                remote_receipt.get("source_inventory"), "remote source inventory"
            ).get("files")
            or []
        )
        _extract_regular_snapshot(
            archive_path=archive_path,
            output_root=snapshot_root,
            expected_files=remote_files,
        )
        _assert_file_inventory(snapshot_root, remote_files, "downloaded snapshot tree")
        raw_files, blind_files = _split_remote_snapshot_files(
            remote_files,
            expected_bindings=set(inputs.binding_to_job_id),
            expected_blind_entries=inputs.blind_metadata_entries,
        )
        binding_root = _regular_directory(
            snapshot_root / "raw", "downloaded binding tree"
        )
        blind_root = _regular_directory(
            snapshot_root / "blind", "downloaded blind metadata tree"
        )
        _assert_file_inventory(binding_root, raw_files, "downloaded binding tree")
        _assert_file_inventory(blind_root, blind_files, "downloaded blind metadata")

        mapped_root = transfer_root / "mapped-job-tree"
        mapped_root.mkdir(mode=0o700)
        _map_binding_directories(
            binding_root=binding_root,
            mapped_root=mapped_root,
            binding_to_job_id=inputs.binding_to_job_id,
        )
        mapped_files = _mapped_inventory(
            raw_files, binding_to_job_id=inputs.binding_to_job_id
        )
        local_inventory = _assert_file_inventory(
            mapped_root, mapped_files, "mapped local staging tree"
        )
        _fsync_tree(mapped_root)

        # Recheck every non-raw gate immediately before the destination becomes
        # visible.  The phase receipt must still be fresh at publication time.
        _verify_checklist_v2_quiescence_gate(
            checklist_freeze_lock_path=checklist_freeze_lock_path,
            review_quiescence_receipt_path=review_quiescence_receipt_path,
            quiescence_max_age_seconds=quiescence_max_age_seconds,
        )
        _score_empty_snapshot(score_result_roots)
        if _lexists(inputs.destination):
            raise RetrievalError("local staging destination appeared during transfer")
        _rename_directory_noreplace(mapped_root, inputs.destination)
        published = True
        _fsync_directory(destination_parent)
        _assert_file_inventory(
            inputs.destination, mapped_files, "published local staging tree"
        )

        definition = _sealed_retrieval_definition(
            inputs=inputs,
            quiescence_path=review_quiescence_receipt_path,
            controller_receipt_path=controller_receipt_path,
            remote_receipt=remote_receipt,
            local_inventory=local_inventory,
            temporary_root=transfer_root,
            known_hosts=known_hosts,
        )
        retrieved_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        payload = {
            "schema_version": SEALED_RETRIEVAL_SCHEMA_VERSION,
            "status": "retrieved_verified_atomic",
            "retrieved_at": retrieved_at,
            "definition": definition,
            "definition_sha256": sha256_object(definition),
        }
        _exclusive_publish_json(sealed_receipt, payload)
        _score_empty_snapshot(score_result_roots)
        verified = verify_sealed_evidence_retrieval_receipt(
            receipt_path=sealed_receipt,
            execution_lock_path=execution_lock_path,
            checklist_freeze_lock_path=checklist_freeze_lock_path,
            review_quiescence_receipt_path=review_quiescence_receipt_path,
            formal_completion_receipt_path=formal_completion_receipt_path,
            remote_completion_index_path=remote_completion_index_path,
        )
        return LockedArtifactResult(
            path=verified.path,
            sha256=verified.sha256,
            definition=verified.definition,
            created=True,
        )
    finally:
        if transfer_root.exists():
            shutil.rmtree(transfer_root)
        if published and not _lexists(sealed_receipt):
            # Never silently claim rollback: directory publication is atomic and
            # irreversible by design.  A crash/failure in the tiny receipt window
            # leaves a fail-closed destination requiring explicit audit.
            pass


def _preflight_inputs(
    *,
    execution_lock_path: str | Path,
    checklist_freeze_lock_path: str | Path,
    review_quiescence_receipt_path: str | Path,
    quiescence_max_age_seconds: int,
    formal_completion_receipt_path: str | Path,
    remote_completion_index_path: str | Path,
    score_result_roots: Sequence[str | Path],
) -> RetrievalInputs:
    checklist, quiescence = _verify_checklist_v2_quiescence_gate(
        checklist_freeze_lock_path=checklist_freeze_lock_path,
        review_quiescence_receipt_path=review_quiescence_receipt_path,
        quiescence_max_age_seconds=quiescence_max_age_seconds,
    )
    execution = verify_execution_lock(lock_path=execution_lock_path)
    sealed = _mapping(
        execution.definition.get("sealed_remote_evidence"), "sealed remote evidence"
    )
    _require_sealed_retrieval_fields(sealed)
    infra_binding = _mapping(
        execution.definition.get("runtime_infra_overlay"), "runtime infra overlay"
    )
    infra_path = _regular_file(infra_binding.get("path"), "runtime infra overlay")
    if infra_binding != _path_lock(infra_path):
        raise RetrievalError("runtime infra overlay binding is stale")
    infra = _strict_agentdojo_infra_snapshot(load_mapping(infra_path))
    for field, expected in (
        ("ssh_host", infra["ssh_host"]),
        ("ssh_port", infra["ssh_port"]),
        ("execution_user", infra["execution_user"]),
        ("ssh_host_ed25519_fingerprint", infra["ssh_host_ed25519_fingerprint"]),
        ("remote_raw_root", infra["remote_raw_root"]),
        ("blind_aggregate_root", infra["blind_aggregate_root"]),
    ):
        if sealed.get(field) != expected:
            raise RetrievalError(f"sealed remote evidence {field} is stale")

    completion_file = _regular_file(
        formal_completion_receipt_path, "formal execution completion receipt"
    )
    completion = load_mapping(completion_file)
    anomaly_file = _regular_file(
        completion.get("anomaly_receipt_path"), "formal anomaly receipt"
    )
    remote_index_file = _regular_file(
        remote_completion_index_path, "formal remote completion index"
    )
    _verify_formal_execution_receipts(
        completion_path=completion_file,
        anomaly_path=anomaly_file,
        execution_lock_path=execution.lock_path,
        execution_lock_sha256=execution.lock_sha256,
        execution_policy_sha256=str(
            execution.definition.get("execution_policy_sha256") or ""
        ),
        execution_definition=execution.definition,
        remote_completion_index_path=remote_index_file,
    )
    remote_index = load_mapping(remote_index_file)
    ordered_entries, binding_to_job_id = _ordered_job_mapping(
        execution=execution,
        completion=completion,
        remote_index=remote_index,
    )
    local_blind_root, blind_metadata_entries = _locked_blind_metadata(
        completion_file=completion_file,
        completion=completion,
        remote_index_file=remote_index_file,
    )
    output = _mapping(
        execution.definition.get("output_precondition"), "execution output precondition"
    )
    destination = resolve_repo_path(
        str(output.get("staging_raw_result_root") or "")
    ).absolute()
    if destination != resolve_repo_path(
        str(sealed.get("local_canonical_staging_root") or "")
    ).absolute():
        raise RetrievalError("local staging root differs across execution-lock bindings")
    _score_empty_snapshot(score_result_roots)
    return RetrievalInputs(
        execution=execution,
        checklist=checklist,
        quiescence=quiescence,
        sealed=sealed,
        infra=infra,
        completion_file=completion_file,
        completion=completion,
        remote_index_file=remote_index_file,
        remote_index=remote_index,
        ordered_entries=ordered_entries,
        binding_to_job_id=binding_to_job_id,
        local_blind_root=local_blind_root,
        blind_metadata_entries=blind_metadata_entries,
        destination=destination,
        score_roots=tuple(score_result_roots),
    )


def _require_sealed_retrieval_fields(sealed: Mapping[str, Any]) -> None:
    required = {
        "ssh_host",
        "ssh_port",
        "ssh_host_ed25519_fingerprint",
        "execution_user",
        "remote_raw_root",
        "blind_aggregate_root",
        "local_canonical_staging_root",
        "ssh_known_hosts_file",
        "remote_inventory_helper",
        "retrieval_lifecycle_lock",
        "retrieval_snapshot_root",
    }
    missing = sorted(required - set(sealed))
    if missing:
        raise RetrievalError(f"execution lock lacks retrieval fields: {missing}")
    for field in (
        "remote_raw_root",
        "blind_aggregate_root",
        "retrieval_lifecycle_lock",
        "retrieval_snapshot_root",
    ):
        value = str(sealed.get(field) or "")
        if not Path(value).is_absolute() or _REMOTE_SAFE_PATH_RE.fullmatch(value) is None:
            raise RetrievalError(f"locked {field} is not a safe absolute path")
    roots = [
        Path(str(sealed[field]))
        for field in (
            "remote_raw_root",
            "blind_aggregate_root",
            "retrieval_snapshot_root",
        )
    ]
    for position, first in enumerate(roots):
        for second in roots[position + 1 :]:
            if _is_relative_to(first, second) or _is_relative_to(second, first):
                raise RetrievalError("remote raw/blind/snapshot roots overlap")


def _ordered_job_mapping(
    *, execution: Any, completion: Mapping[str, Any], remote_index: Mapping[str, Any]
) -> tuple[tuple[dict[str, Any], ...], dict[str, str]]:
    plan_path = _regular_file(
        EXPERIMENT_ROOT
        / "execution_plan"
        / execution.lock_sha256
        / "plan_index.json",
        "locked plan index",
    )
    if completion.get("plan_index_sha256") != sha256_file(plan_path):
        raise RetrievalError("locked plan index hash is stale")
    plan = load_mapping(plan_path)
    entries = list(plan.get("entries") or [])
    if (
        plan.get("schema_version") != "agentdojo_locked_job_plan_index/v2"
        or plan.get("job_count") != EXPECTED_RECORD_SLOT_COUNT
        or plan.get("record_slot_count") != EXPECTED_RECORD_SLOT_COUNT
        or len(entries) != EXPECTED_RECORD_SLOT_COUNT
        or plan.get("entries_sha256") != sha256_object(entries)
    ):
        raise RetrievalError("locked plan index denominator/hash differs")
    if plan.get("execution_lock_sha256") != execution.lock_sha256:
        raise RetrievalError("locked plan index execution binding is stale")

    remote_entries = list(remote_index.get("entries") or [])
    if len(remote_entries) != EXPECTED_RECORD_SLOT_COUNT:
        raise RetrievalError("remote completion index denominator differs")
    binding_to_job_id: dict[str, str] = {}
    ordered_remote: list[dict[str, Any]] = []
    remote_by_binding: dict[str, dict[str, Any]] = {}
    for raw_remote in remote_entries:
        if not isinstance(raw_remote, Mapping) or set(raw_remote) != set(
            COMPLETION_INDEX_ENTRY_FIELDS
        ):
            raise RetrievalError("remote completion entry field set differs")
        remote = dict(raw_remote)
        binding = _digest(remote.get("job_binding_sha256"), "remote job binding")
        if binding in remote_by_binding:
            raise RetrievalError("remote completion index has duplicate bindings")
        remote_by_binding[binding] = remote

    for position, raw_plan_entry in enumerate(entries):
        if not isinstance(raw_plan_entry, Mapping):
            raise RetrievalError(f"plan index entry {position} is malformed")
        plan_entry = dict(raw_plan_entry)
        job_file = _regular_file(plan_entry.get("path"), "locked job file")
        if plan_entry.get("sha256") != sha256_file(job_file):
            raise RetrievalError("locked job file hash is stale")
        job = load_mapping(job_file)
        job_id = _safe_job_id(job.get("job_id"))
        if (
            plan_entry.get("job_id") != job_id
            or plan_entry.get("record_slot_id") != job.get("record_slot_id")
            or plan_entry.get("agent_id") != job.get("agent_id")
            or job.get("execution_lock_sha256") != execution.lock_sha256
            or job.get("execution_policy_sha256")
            != execution.definition.get("execution_policy_sha256")
        ):
            raise RetrievalError("locked job-plan entry binding differs")
        binding = formal_job_binding_sha256(job)
        identity = job_identity_sha256(job)
        remote = remote_by_binding.get(binding)
        if remote is None or remote.get("job_identity_sha256") != identity:
            raise RetrievalError("remote completion index differs from locked job plan")
        if remote.get("canonical_job_relative_path") != binding:
            raise RetrievalError("remote canonical path differs from job binding")
        binding_to_job_id[binding] = job_id
        ordered_remote.append(remote)
    if list(remote_entries) != ordered_remote:
        raise RetrievalError("remote completion index is not in locked job-plan order")
    if len(set(binding_to_job_id.values())) != EXPECTED_RECORD_SLOT_COUNT:
        raise RetrievalError("locked job IDs are not unique")
    return tuple(ordered_remote), binding_to_job_id


def _locked_blind_metadata(
    *,
    completion_file: Path,
    completion: Mapping[str, Any],
    remote_index_file: Path,
) -> tuple[Path, tuple[dict[str, Any], ...]]:
    """Lock the four content-free files that must share the raw snapshot."""

    root = _regular_directory(completion_file.parent, "local blind metadata root")
    declared = {
        completion_file.name: completion_file,
        str(completion.get("completion_index_relative_path") or ""): remote_index_file,
        str(completion.get("completion_journal_relative_path") or ""): None,
        str(completion.get("failed_attempt_journal_relative_path") or ""): None,
    }
    if len(declared) != 4 or "" in declared:
        raise RetrievalError("completion receipt does not name four unique blind files")
    entries: list[dict[str, Any]] = []
    for relative, supplied in sorted(declared.items()):
        relative = _safe_relative(relative)
        candidate = root.joinpath(*PurePosixPath(relative).parts)
        if supplied is not None and candidate != supplied.absolute():
            raise RetrievalError("blind metadata relative path differs from canonical file")
        file = _single_link_regular_file(candidate, "locked blind metadata file")
        entries.append(
            {
                "relative_path": relative,
                "sha256": sha256_file(file),
                "size_bytes": file.stat().st_size,
            }
        )

    by_path = {entry["relative_path"]: entry for entry in entries}
    for relative_field, hash_field in (
        ("completion_index_relative_path", "completion_index_file_sha256"),
        ("completion_journal_relative_path", "completion_journal_file_sha256"),
        (
            "failed_attempt_journal_relative_path",
            "failed_attempt_journal_file_sha256",
        ),
    ):
        relative = str(completion.get(relative_field) or "")
        if by_path[relative]["sha256"] != completion.get(hash_field):
            raise RetrievalError(f"completion receipt {hash_field} is stale")
    return root, tuple(entries)


def _verify_known_hosts(inputs: RetrievalInputs) -> dict[str, str]:
    binding = _mapping(
        inputs.sealed.get("ssh_known_hosts_file"), "locked known_hosts binding"
    )
    path = _single_link_regular_file(
        binding.get("path"), "pinned ED25519 known_hosts"
    )
    if binding != _path_lock(path):
        raise RetrievalError("known_hosts binding is stale")
    if str(path) != str(Path(inputs.infra["ssh_known_hosts_file"]).expanduser()):
        raise RetrievalError("known_hosts path differs from runtime infra")
    lines = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if len(lines) != 1:
        raise RetrievalError("known_hosts must contain exactly one pinned host entry")
    fields = lines[0].split()
    if len(fields) != 3 or fields[1] != "ssh-ed25519":
        raise RetrievalError("known_hosts is not one plain ED25519 entry")
    expected_host = str(inputs.sealed["ssh_host"])
    expected_token = (
        expected_host
        if int(inputs.sealed["ssh_port"]) == 22
        else f"[{expected_host}]:{int(inputs.sealed['ssh_port'])}"
    )
    if fields[0] != expected_token:
        raise RetrievalError("known_hosts endpoint token differs")
    try:
        public_key = base64.b64decode(fields[2], validate=True)
    except ValueError as exc:
        raise RetrievalError("known_hosts public key is malformed") from exc
    fingerprint = "SHA256:" + base64.b64encode(
        hashlib.sha256(public_key).digest()
    ).decode("ascii").rstrip("=")
    if fingerprint != inputs.sealed["ssh_host_ed25519_fingerprint"]:
        raise RetrievalError("known_hosts ED25519 fingerprint differs")
    return {"path": _display(path), "sha256": sha256_file(path), "fingerprint": fingerprint}


def _strict_ssh_argv(
    inputs: RetrievalInputs, *, known_hosts: Mapping[str, str]
) -> list[str]:
    key = Path(inputs.infra["ssh_key_path"]).expanduser()
    if not key.is_absolute():
        raise RetrievalError("SSH identity key is missing, relative, or symlinked")
    key = _single_link_regular_file(key, "SSH identity key")
    if key.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise RetrievalError("SSH identity key permissions are too broad")
    return [
        "ssh",
        "-F",
        "/dev/null",
        "-o",
        "BatchMode=yes",
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        f"UserKnownHostsFile={resolve_repo_path(known_hosts['path']).absolute()}",
        "-o",
        "GlobalKnownHostsFile=/dev/null",
        "-o",
        "HostKeyAlgorithms=ssh-ed25519",
        "-o",
        "PubkeyAcceptedAlgorithms=ssh-ed25519",
        "-o",
        "UpdateHostKeys=no",
        "-o",
        "VerifyHostKeyDNS=no",
        "-o",
        "PasswordAuthentication=no",
        "-o",
        "KbdInteractiveAuthentication=no",
        "-o",
        "NumberOfPasswordPrompts=0",
        "-o",
        "ForwardAgent=no",
        "-o",
        "ControlMaster=no",
        "-o",
        "ConnectTimeout=20",
        "-p",
        str(inputs.sealed["ssh_port"]),
        "-i",
        str(key),
    ]


def _remote_snapshot_request(inputs: RetrievalInputs) -> dict[str, Any]:
    entries = [dict(entry) for entry in inputs.ordered_entries]
    return {
        "schema_version": REMOTE_SNAPSHOT_REQUEST_SCHEMA_VERSION,
        "execution_lock_sha256": inputs.execution.lock_sha256,
        "execution_policy_sha256": inputs.execution.definition[
            "execution_policy_sha256"
        ],
        "remote_raw_root": inputs.sealed["remote_raw_root"],
        "remote_blind_root": inputs.sealed["blind_aggregate_root"],
        "retrieval_snapshot_root": inputs.sealed["retrieval_snapshot_root"],
        "retrieval_lifecycle_lock": inputs.sealed["retrieval_lifecycle_lock"],
        "entry_count": EXPECTED_RECORD_SLOT_COUNT,
        "entries_sha256": sha256_object(entries),
        "entries": entries,
        "blind_metadata_entry_count": len(inputs.blind_metadata_entries),
        "blind_metadata_entries_sha256": sha256_object(
            list(inputs.blind_metadata_entries)
        ),
        "blind_metadata_entries": list(inputs.blind_metadata_entries),
    }


def _prepare_remote_snapshot(
    *,
    inputs: RetrievalInputs,
    request: Mapping[str, Any],
    ssh_argv: Sequence[str],
    command_runner: CommandRunner,
) -> dict[str, Any]:
    helper = _mapping(
        inputs.sealed.get("remote_inventory_helper"), "remote inventory helper"
    )
    if set(helper) != {"path", "remote_path", "sha256"}:
        raise RetrievalError("remote inventory helper binding is not exact")
    helper_file = _single_link_regular_file(
        helper.get("path"), "local remote inventory helper"
    )
    if helper["sha256"] != sha256_file(helper_file):
        raise RetrievalError("remote inventory helper hash is stale")
    expected_remote = (
        Path(inputs.infra["remote_workdir"])
        / "src/evidence_system/adapters/agentdojo_remote_inventory.py"
    )
    if helper.get("remote_path") != str(expected_remote):
        raise RetrievalError("remote inventory helper path differs from locked deploy path")
    remote_command = shlex.join(
        [
            inputs.infra["python_bin"],
            str(expected_remote),
            "--remote-raw-root",
            inputs.sealed["remote_raw_root"],
            "--remote-blind-root",
            inputs.sealed["blind_aggregate_root"],
            "--snapshot-root",
            inputs.sealed["retrieval_snapshot_root"],
            "--lifecycle-lock",
            inputs.sealed["retrieval_lifecycle_lock"],
            "--self-sha256",
            helper["sha256"],
        ]
    )
    endpoint = f"{inputs.sealed['execution_user']}@{inputs.sealed['ssh_host']}"
    completed = command_runner(
        [*ssh_argv, endpoint, remote_command],
        input=json.dumps(dict(request), separators=(",", ":"), sort_keys=True),
        text=True,
        capture_output=True,
        check=False,
        timeout=7_200,
    )
    if completed.returncode != 0:
        raise RetrievalError(
            "remote snapshot helper failed: "
            f"exit={completed.returncode}, stderr_sha256="
            f"{sha256_object(completed.stderr or '')}"
        )
    try:
        receipt = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RetrievalError("remote snapshot helper output is not JSON") from exc
    if not isinstance(receipt, Mapping):
        raise RetrievalError("remote snapshot helper output is not an object")
    result = dict(receipt)
    _validate_remote_snapshot_receipt(result, inputs=inputs, request=request)
    return result


def _validate_remote_snapshot_receipt(
    receipt: Mapping[str, Any], *, inputs: RetrievalInputs, request: Mapping[str, Any]
) -> None:
    expected_fields = {
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
    if set(receipt) != expected_fields:
        raise RetrievalError("remote snapshot receipt field set differs")
    for actual, expected, label in (
        (receipt.get("schema_version"), REMOTE_SNAPSHOT_RECEIPT_SCHEMA_VERSION, "schema"),
        (receipt.get("status"), "snapshot_verified_content_blind", "status"),
        (receipt.get("execution_lock_sha256"), inputs.execution.lock_sha256, "lock"),
        (
            receipt.get("execution_policy_sha256"),
            inputs.execution.definition["execution_policy_sha256"],
            "policy",
        ),
        (receipt.get("entries_sha256"), request["entries_sha256"], "entries"),
        (receipt.get("entry_count"), EXPECTED_RECORD_SLOT_COUNT, "entry count"),
        (receipt.get("remote_raw_root"), inputs.sealed["remote_raw_root"], "raw root"),
        (
            receipt.get("remote_blind_root"),
            inputs.sealed["blind_aggregate_root"],
            "blind root",
        ),
        (
            receipt.get("retrieval_lifecycle_lock"),
            inputs.sealed["retrieval_lifecycle_lock"],
            "lifecycle lock",
        ),
        (receipt.get("pre_post_inventory_identical"), True, "pre/post inventory"),
        (receipt.get("lifecycle_flock"), "exclusive", "lifecycle flock"),
        (receipt.get("fsync_completed"), True, "fsync"),
        (receipt.get("failed_attempt_archive_included"), False, "failed attempts"),
        (receipt.get("blind_only"), True, "blind only"),
        (
            receipt.get(
                "contains_case_agent_prompt_response_trajectory_evaluator_or_label"
            ),
            False,
            "content boundary",
        ),
    ):
        if actual != expected:
            raise RetrievalError(f"remote snapshot receipt {label} differs")
    snapshot_id = _digest(receipt.get("snapshot_id"), "snapshot id")
    archive = _mapping(receipt.get("archive"), "remote snapshot archive")
    expected_archive_path = f"{inputs.sealed['retrieval_snapshot_root']}/{snapshot_id}.tar"
    if (
        set(archive) != {"path", "sha256", "size_bytes", "format"}
        or archive.get("path") != expected_archive_path
        or _REMOTE_SAFE_PATH_RE.fullmatch(str(archive.get("path") or "")) is None
        or archive.get("format") != "tar_uncompressed_regular_files_only"
    ):
        raise RetrievalError("remote snapshot archive binding differs")
    _digest(archive.get("sha256"), "remote archive hash")
    if not isinstance(archive.get("size_bytes"), int) or archive["size_bytes"] < 1:
        raise RetrievalError("remote snapshot archive size is invalid")
    inventory = _mapping(receipt.get("source_inventory"), "remote source inventory")
    files = list(inventory.get("files") or [])
    if not files:
        raise RetrievalError("remote snapshot inventory is empty")
    raw_files, _ = _split_remote_snapshot_files(
        files,
        expected_bindings=set(inputs.binding_to_job_id),
        expected_blind_entries=inputs.blind_metadata_entries,
    )
    _validate_remote_job_inventories(
        raw_files=raw_files, entries=inputs.ordered_entries
    )
    projection = [{"path": row["path"], "sha256": row["sha256"]} for row in files]
    expected_inventory = {
        "tree_sha256": sha256_object(projection),
        "file_count": len(files),
        "total_bytes": sum(int(row["size_bytes"]) for row in files),
        "files_sha256": sha256_object(files),
        "raw_file_count": sum(
            str(row.get("path") or "").startswith("raw/") for row in files
        ),
        "blind_metadata_file_count": len(inputs.blind_metadata_entries),
        "blind_metadata_entries_sha256": sha256_object(
            list(inputs.blind_metadata_entries)
        ),
        "files": files,
    }
    if inventory != expected_inventory:
        raise RetrievalError("remote snapshot inventory aggregate differs")
    expected_snapshot_id = sha256_object(
        {
            "schema_version": REMOTE_SNAPSHOT_RECEIPT_SCHEMA_VERSION,
            "execution_lock_sha256": inputs.execution.lock_sha256,
            "entries_sha256": request["entries_sha256"],
            "source_tree_sha256": inventory["tree_sha256"],
        }
    )
    if snapshot_id != expected_snapshot_id:
        raise RetrievalError("remote snapshot ID differs from its locked inputs")


def _controller_remote_snapshot_receipt(
    *,
    inputs: RetrievalInputs,
    request: Mapping[str, Any],
    remote_receipt: Mapping[str, Any],
    known_hosts: Mapping[str, str],
    received_at: str | None = None,
) -> dict[str, Any]:
    helper = _mapping(
        inputs.sealed.get("remote_inventory_helper"), "remote inventory helper"
    )
    return {
        "schema_version": CONTROLLER_REMOTE_SNAPSHOT_SCHEMA_VERSION,
        "status": "remote_snapshot_verified_before_transfer",
        "received_at": received_at
        or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "execution_lock": _path_lock(inputs.execution.lock_path),
        "checklist_freeze_lock": _path_lock(inputs.checklist.freeze_path),
        "review_quiescence_receipt": _path_lock(inputs.quiescence["path"]),
        "formal_completion_receipt": _path_lock(inputs.completion_file),
        "remote_completion_index": _path_lock(inputs.remote_index_file),
        "known_hosts": dict(known_hosts),
        "remote_inventory_helper": dict(helper),
        "request_sha256": sha256_object(dict(request)),
        "remote_receipt_sha256": sha256_object(dict(remote_receipt)),
        "remote_receipt": dict(remote_receipt),
        "raw_bytes_transferred": False,
        "blind_only": True,
    }


def _transfer_snapshot_archive(
    *,
    inputs: RetrievalInputs,
    remote_receipt: Mapping[str, Any],
    archive_path: Path,
    ssh_argv: Sequence[str],
    command_runner: CommandRunner,
) -> None:
    archive = _mapping(remote_receipt.get("archive"), "remote archive")
    remote_path = str(archive.get("path") or "")
    if _REMOTE_SAFE_PATH_RE.fullmatch(remote_path) is None:
        raise RetrievalError("remote archive path is unsafe")
    endpoint = f"{inputs.sealed['execution_user']}@{inputs.sealed['ssh_host']}"
    rsync_ssh = shlex.join(ssh_argv)
    argv = [
        "rsync",
        "-rt",
        "--safe-links",
        "--chmod=u=rwX,go=",
        "--timeout=120",
        "-e",
        rsync_ssh,
        "--",
        f"{endpoint}:{remote_path}",
        str(archive_path),
    ]
    if any("--delete" in argument for argument in argv):
        raise RetrievalError("rsync --delete is forbidden")
    completed = command_runner(
        argv,
        text=True,
        capture_output=True,
        check=False,
        timeout=14_400,
    )
    if completed.returncode != 0:
        raise RetrievalError(
            "snapshot archive transfer failed: "
            f"exit={completed.returncode}, stderr_sha256="
            f"{sha256_object(completed.stderr or '')}"
        )
    downloaded = _single_link_regular_file(archive_path, "downloaded snapshot archive")
    if (
        sha256_file(downloaded) != archive.get("sha256")
        or downloaded.stat().st_size != archive.get("size_bytes")
    ):
        raise RetrievalError("downloaded snapshot archive hash/size differs")


def _extract_regular_snapshot(
    *, archive_path: Path, output_root: Path, expected_files: Sequence[Mapping[str, Any]]
) -> None:
    archive = _single_link_regular_file(archive_path, "snapshot archive")
    root = _regular_directory(output_root, "snapshot extraction root")
    expected = {str(row["path"]): dict(row) for row in expected_files}
    observed: set[str] = set()
    with tarfile.open(archive, mode="r:") as tar:
        members = tar.getmembers()
        if len(members) != len(expected):
            raise RetrievalError("snapshot tar member denominator differs")
        for member in members:
            relative = _safe_relative(member.name)
            if (
                relative in observed
                or relative not in expected
                or not member.isfile()
                or member.issym()
                or member.islnk()
                or member.isdev()
                or member.isfifo()
            ):
                raise RetrievalError("snapshot tar contains unsafe/extra/duplicate member")
            row = expected[relative]
            if member.size != row["size_bytes"]:
                raise RetrievalError("snapshot tar member size differs")
            destination = root.joinpath(*PurePosixPath(relative).parts)
            _mkdir_parents_nosymlink(destination.parent, stop=root)
            source = tar.extractfile(member)
            if source is None:
                raise RetrievalError("snapshot tar member is unreadable")
            digest = hashlib.sha256()
            total = 0
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(destination, flags, 0o600)
            try:
                while True:
                    block = source.read(1 << 20)
                    if not block:
                        break
                    digest.update(block)
                    total += len(block)
                    view = memoryview(block)
                    while view:
                        written = os.write(descriptor, view)
                        if written <= 0:
                            raise RetrievalError("snapshot extraction made no progress")
                        view = view[written:]
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            if digest.hexdigest() != row["sha256"] or total != row["size_bytes"]:
                raise RetrievalError("snapshot extracted member hash/size differs")
            observed.add(relative)
    if observed != set(expected):
        raise RetrievalError("snapshot tar is missing expected members")


def _map_binding_directories(
    *, binding_root: Path, mapped_root: Path, binding_to_job_id: Mapping[str, str]
) -> None:
    observed = sorted(path.name for path in binding_root.iterdir())
    if observed != sorted(binding_to_job_id):
        raise RetrievalError("extracted binding directory set differs")
    for binding, job_id in binding_to_job_id.items():
        source = _regular_directory(binding_root / binding, "extracted binding root")
        destination = mapped_root / _safe_job_id(job_id)
        if _lexists(destination):
            raise RetrievalError("mapped job destination collides")
        os.rename(source, destination)
    if any(binding_root.iterdir()):
        raise RetrievalError("binding tree contains unmapped entries")


def _mapped_inventory(
    files: Sequence[Mapping[str, Any]], *, binding_to_job_id: Mapping[str, str]
) -> list[dict[str, Any]]:
    mapped: list[dict[str, Any]] = []
    for raw in files:
        row = dict(raw)
        path = PurePosixPath(_safe_relative(str(row["path"])))
        binding = path.parts[0]
        job_id = binding_to_job_id.get(binding)
        if job_id is None:
            raise RetrievalError("remote inventory contains an unknown binding")
        mapped.append(
            {
                "path": PurePosixPath(job_id, *path.parts[1:]).as_posix(),
                "sha256": row["sha256"],
                "size_bytes": row["size_bytes"],
            }
        )
    mapped.sort(key=lambda row: str(row["path"]))
    return mapped


def _assert_file_inventory(
    root: Path, expected_files: Sequence[Mapping[str, Any]], label: str
) -> dict[str, Any]:
    directory = _regular_directory(root, label)
    expected = [dict(row) for row in expected_files]
    observed: list[dict[str, Any]] = []

    def visit(current_path: Path) -> None:
        _regular_directory(current_path, label)
        with os.scandir(current_path) as iterator:
            entries = sorted(iterator, key=lambda item: item.name)
        for entry in entries:
            path = current_path / entry.name
            info = entry.stat(follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode):
                visit(path)
                continue
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise RetrievalError(f"{label} contains a link or special node")
            path = _single_link_regular_file(path, label)
            observed.append(
                {
                    "path": path.relative_to(directory).as_posix(),
                    "sha256": sha256_file(path),
                    "size_bytes": info.st_size,
                }
            )

    visit(directory)
    observed.sort(key=lambda row: str(row["path"]))
    expected.sort(key=lambda row: str(row["path"]))
    if observed != expected:
        raise RetrievalError(f"{label} inventory differs")
    projection = [{"path": row["path"], "sha256": row["sha256"]} for row in observed]
    return {
        "tree_sha256": sha256_object(projection),
        "file_count": len(observed),
        "total_bytes": sum(int(row["size_bytes"]) for row in observed),
    }


def _sealed_retrieval_definition(
    *,
    inputs: RetrievalInputs,
    quiescence_path: str | Path,
    controller_receipt_path: Path,
    remote_receipt: Mapping[str, Any],
    local_inventory: Mapping[str, Any],
    temporary_root: Path,
    known_hosts: Mapping[str, str],
) -> dict[str, Any]:
    remote_entries = list(inputs.remote_index.get("entries") or [])
    namespace_binding = _path_lock(
        _single_link_regular_file(
            DEFAULT_FORMAL_NAMESPACE_INIT_RECEIPT,
            "formal execution namespace-init receipt",
        )
    )
    _verify_formal_namespace_init_receipt(
        namespace_binding,
        execution=inputs.execution,
    )
    controller_code = _single_link_regular_file(__file__, "retrieval controller code")
    return {
        "execution_lock": _path_lock(inputs.execution.lock_path),
        "namespace_init_receipt": namespace_binding,
        "checklist_freeze_lock": _path_lock(inputs.checklist.freeze_path),
        "review_quiescence_receipt": _path_lock(quiescence_path),
        "formal_completion_receipt": _path_lock(inputs.completion_file),
        "remote_completion_index": {
            **_path_lock(inputs.remote_index_file),
            "entry_count": EXPECTED_RECORD_SLOT_COUNT,
            "entries_sha256": sha256_object(remote_entries),
        },
        "controller_remote_snapshot_receipt": _path_lock(controller_receipt_path),
        "remote_snapshot": {
            "receipt_sha256": sha256_object(dict(remote_receipt)),
            "snapshot_id": remote_receipt["snapshot_id"],
            "archive_sha256": remote_receipt["archive"]["sha256"],
            "archive_size_bytes": remote_receipt["archive"]["size_bytes"],
            "source_tree_sha256": remote_receipt["source_inventory"]["tree_sha256"],
            "source_file_count": remote_receipt["source_inventory"]["file_count"],
            "source_total_bytes": remote_receipt["source_inventory"]["total_bytes"],
            "source_raw_file_count": remote_receipt["source_inventory"][
                "raw_file_count"
            ],
            "source_blind_metadata_file_count": remote_receipt[
                "source_inventory"
            ]["blind_metadata_file_count"],
            "blind_metadata_entries_sha256": remote_receipt[
                "source_inventory"
            ]["blind_metadata_entries_sha256"],
        },
        "ssh_transport": {
            "host": inputs.sealed["ssh_host"],
            "port": inputs.sealed["ssh_port"],
            "user": inputs.sealed["execution_user"],
            "host_key_algorithm": "ssh-ed25519",
            "host_fingerprint": known_hosts["fingerprint"],
            "known_hosts": {"path": known_hosts["path"], "sha256": known_hosts["sha256"]},
            "strict_host_key_checking": True,
            "password_authentication": False,
            "agent_forwarding": False,
        },
        "retrieval_controller": _path_lock(controller_code),
        "remote_raw_root": inputs.sealed["remote_raw_root"],
        "remote_blind_root": inputs.sealed["blind_aggregate_root"],
        "local_staging_root": _display(inputs.destination),
        "local_inventory": dict(local_inventory),
        "counts": {
            "cases": EXPECTED_CASE_COUNT,
            "record_slots": EXPECTED_RECORD_SLOT_COUNT,
            "native_trajectories": EXPECTED_RECORD_SLOT_COUNT * 3,
            "missing": 0,
            "duplicate": 0,
            "extra": 0,
            "hash_mismatch": 0,
        },
        "transfer": {
            "temporary_root": _display(temporary_root),
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
            "binding_to_job_id_mapping_sha256": sha256_object(
                inputs.binding_to_job_id
            ),
            "failed_attempt_archive_included": False,
        },
    }


def _split_remote_snapshot_files(
    files: Sequence[Any],
    *,
    expected_bindings: set[str],
    expected_blind_entries: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    paths: list[str] = []
    raw_files: list[dict[str, Any]] = []
    blind_files: list[dict[str, Any]] = []
    expected_blind = {
        str(entry["relative_path"]): {
            "path": str(entry["relative_path"]),
            "sha256": entry["sha256"],
            "size_bytes": entry["size_bytes"],
        }
        for entry in expected_blind_entries
    }
    for raw in files:
        if not isinstance(raw, Mapping) or set(raw) != {"path", "sha256", "size_bytes"}:
            raise RetrievalError("remote inventory file entry is malformed")
        path = _safe_relative(str(raw.get("path") or ""))
        parts = PurePosixPath(path).parts
        if len(parts) < 2 or parts[0] not in {"raw", "blind"}:
            raise RetrievalError("remote inventory path lacks a snapshot partition")
        _digest(raw.get("sha256"), "remote inventory file hash")
        size = raw.get("size_bytes")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise RetrievalError("remote inventory file size is invalid")
        stripped = PurePosixPath(*parts[1:]).as_posix()
        projected = {
            "path": stripped,
            "sha256": raw["sha256"],
            "size_bytes": size,
        }
        if parts[0] == "raw":
            if len(parts) < 3:
                raise RetrievalError("remote raw inventory path lacks a job/file")
            binding = parts[1]
            if binding not in expected_bindings:
                raise RetrievalError("remote inventory path has an unknown job binding")
            raw_files.append(projected)
        else:
            if stripped not in expected_blind or projected != expected_blind[stripped]:
                raise RetrievalError("remote blind metadata inventory differs")
            blind_files.append(projected)
        paths.append(path)
    if len(paths) != len(set(paths)):
        raise RetrievalError("remote inventory contains duplicate paths")
    if paths != sorted(paths):
        raise RetrievalError("remote inventory paths are not sorted")
    if {row["path"] for row in blind_files} != set(expected_blind):
        raise RetrievalError("remote snapshot is missing locked blind metadata")
    if not raw_files:
        raise RetrievalError("remote snapshot raw inventory is empty")
    raw_files.sort(key=lambda row: str(row["path"]))
    blind_files.sort(key=lambda row: str(row["path"]))
    return raw_files, blind_files


def _validate_remote_job_inventories(
    *, raw_files: Sequence[Mapping[str, Any]], entries: Sequence[Mapping[str, Any]]
) -> None:
    entry_by_binding = {
        str(item["job_binding_sha256"]): dict(item) for item in entries
    }
    by_binding: dict[str, list[dict[str, Any]]] = {}
    for raw in raw_files:
        row = dict(raw)
        path = PurePosixPath(_safe_relative(str(row["path"])))
        binding = path.parts[0]
        if binding not in entry_by_binding:
            raise RetrievalError("raw snapshot inventory has an unknown binding")
        by_binding.setdefault(binding, []).append(row)
    if set(by_binding) != set(entry_by_binding):
        raise RetrievalError("raw snapshot job directory set differs")
    for binding, entry in entry_by_binding.items():
        rows = by_binding[binding]
        marker_relative = f"{binding}/adapter/formal_job_completion.json"
        marker_rows = [row for row in rows if row["path"] == marker_relative]
        if len(marker_rows) != 1:
            raise RetrievalError("raw snapshot completion marker is missing")
        if marker_rows[0]["sha256"] != entry["completion_marker_file_sha256"]:
            raise RetrievalError("raw snapshot completion marker hash differs")
        artifacts = [row for row in rows if row["path"] != marker_relative]
        projection = [
            {
                "path": PurePosixPath(str(row["path"])).relative_to(
                    PurePosixPath(binding)
                ).as_posix(),
                "sha256": row["sha256"],
            }
            for row in artifacts
        ]
        if (
            len(artifacts) != entry["artifact_file_count"]
            or sha256_object(projection) != entry["artifact_tree_sha256"]
            or sum(int(row["size_bytes"]) for row in artifacts)
            != entry["artifact_total_bytes"]
        ):
            raise RetrievalError("raw snapshot artifact inventory differs")


def _publish_identical_or_new(path: Path, payload: Mapping[str, Any]) -> None:
    if _lexists(path):
        if load_mapping(_regular_file(path, "controller remote snapshot receipt")) != dict(
            payload
        ):
            raise RetrievalError("controller remote snapshot receipt already differs")
        return
    _exclusive_publish_json(path, payload)


def _exclusive_publish_json(path: Path, payload: Mapping[str, Any]) -> None:
    path = Path(path).absolute()
    _reject_symlink_ancestors(path.parent, "immutable output parent")
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(dict(payload), indent=2, sort_keys=True) + "\n").encode()
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        try:
            os.link(temporary, path, follow_symlinks=False)
        except FileExistsError as exc:
            raise RetrievalError(f"immutable output destination already exists: {path}") from exc
        _fsync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def _rename_directory_noreplace(source: Path, destination: Path) -> None:
    if _lexists(destination):
        raise RetrievalError("atomic publication destination already exists")
    if source.stat().st_dev != destination.parent.stat().st_dev:
        raise RetrievalError("atomic publication source/destination are not same-filesystem")
    source_bytes = os.fsencode(source)
    destination_bytes = os.fsencode(destination)
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin":
        renamex_np = getattr(libc, "renamex_np", None)
        if renamex_np is None:
            raise RetrievalError("renamex_np(RENAME_EXCL) is unavailable")
        renamex_np.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        renamex_np.restype = ctypes.c_int
        result = renamex_np(source_bytes, destination_bytes, 0x00000004)
    else:
        renameat2 = getattr(libc, "renameat2", None)
        if renameat2 is None:
            raise RetrievalError("renameat2(RENAME_NOREPLACE) is unavailable")
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
        raise RetrievalError("atomic publication destination already exists")
    raise OSError(observed, os.strerror(observed), str(destination))


def _fsync_tree(root: Path) -> None:
    directory = _regular_directory(root, "fsync tree")
    for path in sorted(candidate for candidate in directory.rglob("*") if candidate.is_file()):
        with _single_link_regular_file(path, "fsync file").open("rb") as handle:
            os.fsync(handle.fileno())
    for path in sorted(
        (candidate for candidate in directory.rglob("*") if candidate.is_dir()),
        key=lambda value: len(value.parts),
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


def _mkdir_parents_nosymlink(path: Path, *, stop: Path) -> None:
    try:
        relative = path.relative_to(stop)
    except ValueError as exc:
        raise RetrievalError("extraction parent escapes destination") from exc
    current = stop
    for part in relative.parts:
        current = current / part
        if _lexists(current):
            _regular_directory(current, "extraction directory")
        else:
            current.mkdir(mode=0o700)


def _regular_directory(path: str | Path, label: str) -> Path:
    candidate = Path(path).expanduser().absolute()
    _reject_symlink_ancestors(candidate, label)
    try:
        info = candidate.lstat()
    except FileNotFoundError as exc:
        raise RetrievalError(f"{label} is missing") from exc
    if not stat.S_ISDIR(info.st_mode):
        raise RetrievalError(f"{label} is not a directory")
    return candidate


def _single_link_regular_file(path: str | Path, label: str) -> Path:
    candidate = Path(path).expanduser().absolute()
    _reject_symlink_ancestors(candidate.parent, label)
    try:
        info = candidate.lstat()
    except FileNotFoundError as exc:
        raise RetrievalError(f"{label} is missing") from exc
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise RetrievalError(f"{label} is not a single-link regular file")
    return candidate


def _reject_symlink_ancestors(path: Path, label: str) -> None:
    for candidate in (path, *path.parents):
        if candidate.is_symlink():
            raise RetrievalError(f"{label} has a symlinked ancestor")


def _safe_relative(value: str) -> str:
    if not value or "\\" in value:
        raise RetrievalError("snapshot member path is empty or non-POSIX")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise RetrievalError("snapshot member path escapes extraction root")
    normalized = path.as_posix()
    if normalized != value:
        raise RetrievalError("snapshot member path is not canonical")
    return normalized


def _safe_job_id(value: Any) -> str:
    text = str(value or "")
    if (
        not text
        or text in {".", ".."}
        or "/" in text
        or "\\" in text
        or "\x00" in text
    ):
        raise RetrievalError("locked job ID is not a safe path component")
    return text


def _digest(value: Any, label: str) -> str:
    text = str(value or "")
    if _SHA256_RE.fullmatch(text) is None:
        raise RetrievalError(f"{label} is not a lowercase SHA-256 digest")
    return text


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _lexists(path: Path) -> bool:
    return os.path.lexists(os.fspath(path))


if __name__ == "__main__":
    raise SystemExit(main())
