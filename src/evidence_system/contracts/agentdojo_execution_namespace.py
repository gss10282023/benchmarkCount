"""Pre-lock remote absence and post-lock AgentDojo namespace gates.

The control envelopes in this module are content-blind.  They bind only host,
path, code, lock, and digest metadata; no case, trajectory, evaluator, prompt,
response, or score content is read.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import stat
from typing import Any, Mapping

from evidence_system.adapters.agentdojo_runtime_control import (
    RuntimePolicy,
    execution_runtime_snapshot,
)
from evidence_system.adapters.runtime import (
    formal_job_binding_sha256,
    formal_job_file_sha256,
)
from evidence_system.contracts.common import (
    ContractLifecycleError,
    load_mapping,
    parse_timestamp,
)
from evidence_system.core.hashing import sha256_bytes, sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import validate_object


REMOTE_PRECONDITION_SCHEMA_VERSION = (
    "agentdojo_remote_output_precondition_receipt/v1"
)
NAMESPACE_INIT_SCHEMA_VERSION = (
    "agentdojo_formal_execution_namespace_init_receipt/v2"
)
EXPERIMENT_ROOT = Path("experiments/agentdojo_full_v1.2.2_direct")
DEFAULT_REMOTE_OUTPUT_PRECONDITION_RECEIPT = (
    EXPERIMENT_ROOT / "runtime/preflight/remote_output_precondition_receipt.json"
)
DEFAULT_FINAL_RUNTIME_DEPLOYMENT_RECEIPT = (
    EXPERIMENT_ROOT / "runtime/preflight/final_runtime_deployment_receipt.json"
)
DEFAULT_NAMESPACE_INIT_RECEIPT = Path(
    "results/namespaces/agentdojo_full_v1.2.2_direct_execution_staging/"
    "provenance/formal_execution_namespace_init_receipt.json"
)
PRECONDITION_MAX_AGE = timedelta(minutes=10)
FORMAL_STAGE_ORDER = (
    "canary",
    "ramp-a-8",
    "ramp-a-16",
    "ramp-a-32",
    "remaining-a",
    "ramp-b-8",
    "ramp-b-16",
    "ramp-b-32",
    "remaining-b",
    "ramp-c-8",
    "ramp-c-16",
    "ramp-c-32",
    "remaining-c",
    "recovery-a",
    "recovery-b",
    "recovery-c",
)
FORMAL_STAGE_AUTHORIZATION_FIELDS = frozenset(
    {
        "schema_version",
        "status",
        "created_at",
        "execution_lock_sha256",
        "execution_policy_sha256",
        "plan_index_sha256",
        "namespace_init_receipt",
        "stage_id",
        "session_id",
        "stage_order_index",
        "locked_workers",
        "workers",
        "record_slot_count",
        "record_slot_ids_sha256",
        "allowed_job_binding_sha256",
        "allowed_job_bindings_sha256",
        "allowed_job_file_sha256",
        "allowed_job_files_sha256",
        "allowed_model_config_sha256",
        "allowed_model_configs_sha256",
        "runtime_policy_semantic_sha256",
        "runtime_policy_file_sha256",
        "runtime_infra_file_sha256",
        "runtime_state_root",
        "runtime_snapshot",
        "previous_health_receipt",
        "formal_wall_clock_timeout_seconds",
        "kill_grace_seconds",
        "blind_only",
        "contains_case_agent_prompt_response_trajectory_evaluator_or_label",
    }
)


@dataclass(frozen=True)
class NamespaceReceiptResult:
    path: Path
    sha256: str
    payload: dict[str, Any]
    created: bool


@dataclass(frozen=True)
class FormalStageAuthorization:
    """One immutable, open authorization loaded by a formal VPS worker."""

    path: Path
    file_sha256: str
    payload: dict[str, Any]


def verify_formal_stage_authorization(
    *,
    path: str | Path | None,
    expected_sha256: str,
    job: Mapping[str, Any],
    expected_runtime_policy_semantic_sha256: str,
    expected_runtime_policy_file_sha256: str,
    expected_runtime_state_dir: str | Path | None,
) -> FormalStageAuthorization:
    """Load and fully validate an open stage authorization before worker setup.

    This is deliberately kept in the shared namespace contract rather than in
    the worker.  The controller, worker admission path, and per-request
    currentness check therefore cannot silently diverge.
    """

    if path is None:
        raise RuntimeError("formal execution requires a stage authorization")
    candidate = Path(path)
    if not candidate.is_absolute():
        raise RuntimeError(
            "formal execution requires an absolute stage authorization path"
        )
    expected = _authorization_sha256(
        expected_sha256, field="stage_authorization_sha256"
    )
    payload = _load_and_validate_formal_stage_authorization(
        candidate,
        expected_sha256=expected,
        job=job,
        expected_runtime_policy_semantic_sha256=(
            expected_runtime_policy_semantic_sha256
        ),
        expected_runtime_policy_file_sha256=expected_runtime_policy_file_sha256,
        expected_runtime_state_dir=expected_runtime_state_dir,
    )
    return FormalStageAuthorization(
        path=candidate.resolve(), file_sha256=expected, payload=payload
    )


def assert_formal_stage_authorization_current(
    authorization: FormalStageAuthorization,
    *,
    job: Mapping[str, Any],
    policy: RuntimePolicy,
    model_config_sha256: str,
) -> None:
    """Re-open and revalidate authorization immediately before every request."""

    current = _load_and_validate_formal_stage_authorization(
        authorization.path,
        expected_sha256=authorization.file_sha256,
        job=job,
        expected_runtime_policy_semantic_sha256=policy.semantic_sha256,
        expected_runtime_policy_file_sha256=str(
            authorization.payload["runtime_policy_file_sha256"]
        ),
        expected_runtime_state_dir=str(authorization.payload["runtime_state_root"]),
    )
    if current != authorization.payload:
        raise RuntimeError("formal stage authorization changed after worker start")
    model_digest = _authorization_sha256(
        model_config_sha256, field="model_config_sha256"
    )
    if model_digest not in current["allowed_model_config_sha256"]:
        raise RuntimeError("formal model config is outside the stage authorization")


def _load_and_validate_formal_stage_authorization(
    path: Path,
    *,
    expected_sha256: str,
    job: Mapping[str, Any],
    expected_runtime_policy_semantic_sha256: str,
    expected_runtime_policy_file_sha256: str,
    expected_runtime_state_dir: str | Path | None,
) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("formal stage authorization must be a regular file")
    file_stat = path.stat()
    if (
        file_stat.st_nlink != 1
        or not stat.S_ISREG(file_stat.st_mode)
        or stat.S_IMODE(file_stat.st_mode) & 0o022
    ):
        raise RuntimeError("formal stage authorization is mutable or multiply linked")
    if sha256_file(path) != expected_sha256:
        raise RuntimeError("formal stage authorization SHA-256 mismatch")
    payload = load_mapping(path)
    if set(payload) != FORMAL_STAGE_AUTHORIZATION_FIELDS:
        raise RuntimeError("formal stage authorization has an unexpected field set")
    if (
        payload["schema_version"]
        != "agentdojo_formal_stage_authorization/v1"
        or payload["status"] != "authorized"
        or payload["blind_only"] is not True
        or payload[
            "contains_case_agent_prompt_response_trajectory_evaluator_or_label"
        ]
        is not False
    ):
        raise RuntimeError("formal stage authorization status/schema is invalid")
    created = parse_timestamp(
        str(payload["created_at"]), "formal stage authorization created_at"
    )
    if created > datetime.now(timezone.utc) + timedelta(minutes=5):
        raise RuntimeError("formal stage authorization created_at is in the future")

    lock_sha = _authorization_sha256(
        str(payload["execution_lock_sha256"]),
        field="authorization.execution_lock_sha256",
    )
    policy_sha = _authorization_sha256(
        str(payload["execution_policy_sha256"]),
        field="authorization.execution_policy_sha256",
    )
    if lock_sha != str(job.get("execution_lock_sha256") or "") or policy_sha != str(
        job.get("execution_policy_sha256") or ""
    ):
        raise RuntimeError("formal stage authorization lock/policy binding differs")
    for field in (
        "plan_index_sha256",
        "record_slot_ids_sha256",
        "runtime_policy_semantic_sha256",
        "runtime_policy_file_sha256",
        "runtime_infra_file_sha256",
    ):
        payload[field] = _authorization_sha256(
            str(payload[field]), field=f"authorization.{field}"
        )
    if payload["runtime_policy_semantic_sha256"] != _authorization_sha256(
        expected_runtime_policy_semantic_sha256,
        field="expected_runtime_policy_semantic_sha256",
    ) or payload["runtime_policy_file_sha256"] != _authorization_sha256(
        expected_runtime_policy_file_sha256,
        field="expected_runtime_policy_file_sha256",
    ):
        raise RuntimeError("formal stage authorization runtime-policy binding differs")
    runtime_state_root = Path(str(payload["runtime_state_root"]))
    expected_runtime_state = (
        None
        if expected_runtime_state_dir is None
        else Path(expected_runtime_state_dir)
    )
    if (
        expected_runtime_state is None
        or not runtime_state_root.is_absolute()
        or not expected_runtime_state.is_absolute()
        or runtime_state_root.resolve() != expected_runtime_state.resolve()
    ):
        raise RuntimeError("formal stage authorization runtime-state root differs")
    stage_id = str(payload["stage_id"])
    if not stage_id or len(stage_id) > 64:
        raise RuntimeError("formal stage authorization stage_id is invalid")
    session_id = str(payload["session_id"])
    if (
        not session_id.startswith("session-")
        or len(session_id) > 128
        or any(
            character not in "abcdefghijklmnopqrstuvwxyz0123456789-_"
            for character in session_id
        )
    ):
        raise RuntimeError("formal stage authorization session_id is invalid")
    for field, minimum, maximum in (
        ("stage_order_index", 0, 15),
        ("locked_workers", 1, 32),
        ("workers", 1, 32),
        ("record_slot_count", 1, 2_847),
        ("formal_wall_clock_timeout_seconds", 1, 86_400),
        ("kill_grace_seconds", 1, 300),
    ):
        value = payload[field]
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not minimum <= value <= maximum
        ):
            raise RuntimeError(f"formal stage authorization {field} is invalid")
    if int(payload["workers"]) > int(payload["locked_workers"]):
        raise RuntimeError("formal stage effective workers exceed the locked stage")

    allowed_jobs_raw = payload["allowed_job_binding_sha256"]
    if not isinstance(allowed_jobs_raw, list) or len(allowed_jobs_raw) != int(
        payload["record_slot_count"]
    ):
        raise RuntimeError("formal stage allowed-job denominator differs")
    allowed_jobs = [
        _authorization_sha256(
            str(value), field="authorization.allowed_job_binding"
        )
        for value in allowed_jobs_raw
    ]
    if len(set(allowed_jobs)) != len(allowed_jobs):
        raise RuntimeError("formal stage authorization contains duplicate jobs")
    if payload["allowed_job_bindings_sha256"] != sha256_object(allowed_jobs):
        raise RuntimeError("formal stage allowed-job aggregate SHA-256 differs")
    if formal_job_binding_sha256(job) not in allowed_jobs:
        raise RuntimeError("formal job is not a member of the stage authorization")
    allowed_job_files_raw = payload["allowed_job_file_sha256"]
    if (
        not isinstance(allowed_job_files_raw, list)
        or len(allowed_job_files_raw) != len(allowed_jobs)
    ):
        raise RuntimeError("formal stage allowed-job file denominator differs")
    allowed_job_files = [
        _authorization_sha256(
            str(value), field="authorization.allowed_job_file"
        )
        for value in allowed_job_files_raw
    ]
    if (
        payload["allowed_job_files_sha256"] != sha256_object(allowed_job_files)
        or formal_job_file_sha256(job) not in allowed_job_files
        or allowed_job_files[allowed_jobs.index(formal_job_binding_sha256(job))]
        != formal_job_file_sha256(job)
    ):
        raise RuntimeError("formal job bytes are outside the stage authorization")

    allowed_models_raw = payload["allowed_model_config_sha256"]
    if not isinstance(allowed_models_raw, list) or not 1 <= len(allowed_models_raw) <= 3:
        raise RuntimeError("formal stage allowed-model set is invalid")
    allowed_models = [
        _authorization_sha256(
            str(value), field="authorization.allowed_model_config"
        )
        for value in allowed_models_raw
    ]
    if len(set(allowed_models)) != len(allowed_models) or payload[
        "allowed_model_configs_sha256"
    ] != sha256_object(allowed_models):
        raise RuntimeError("formal stage allowed-model aggregate differs")
    payload["allowed_job_binding_sha256"] = allowed_jobs
    payload["allowed_job_file_sha256"] = allowed_job_files
    payload["allowed_model_config_sha256"] = allowed_models
    if payload["runtime_snapshot"] != execution_runtime_snapshot():
        raise RuntimeError("formal stage authorization runtime snapshot is stale")
    _verify_authorization_file_ref(
        payload["namespace_init_receipt"],
        label="namespace-init receipt",
        expected_execution_lock_sha256=lock_sha,
        expected_execution_policy_sha256=policy_sha,
        expected_plan_index_sha256=str(payload["plan_index_sha256"]),
        expected_runtime_state_root=str(runtime_state_root),
    )
    previous = payload["previous_health_receipt"]
    if previous is not None:
        _verify_authorization_file_ref(previous, label="previous health receipt")
    return dict(payload)


def _verify_authorization_file_ref(
    value: Any,
    *,
    label: str,
    expected_execution_lock_sha256: str | None = None,
    expected_execution_policy_sha256: str | None = None,
    expected_plan_index_sha256: str | None = None,
    expected_runtime_state_root: str | None = None,
) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != {"path", "sha256"}:
        raise RuntimeError(f"formal {label} reference is invalid")
    path = Path(str(value["path"]))
    expected = _authorization_sha256(str(value["sha256"]), field=f"{label}.sha256")
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise RuntimeError(f"formal {label} is not a current absolute regular file")
    if sha256_file(path) != expected:
        raise RuntimeError(f"formal {label} hash is stale")
    if expected_execution_lock_sha256 is not None:
        receipt = load_mapping(path)
        if (
            receipt.get("schema_version")
            != NAMESPACE_INIT_SCHEMA_VERSION
            or receipt.get("status") != "initialized_empty_namespaces"
        ):
            raise RuntimeError(
                "formal namespace-init receipt schema/status is invalid"
            )
        definition = receipt.get("definition")
        if not isinstance(definition, Mapping):
            raise RuntimeError("formal namespace-init receipt definition is missing")
        execution_ref = definition.get("execution_lock")
        plan_ref = definition.get("plan_index")
        if (
            not isinstance(execution_ref, Mapping)
            or execution_ref.get("sha256") != expected_execution_lock_sha256
            or definition.get("execution_policy_sha256")
            != expected_execution_policy_sha256
            or not isinstance(plan_ref, Mapping)
            or plan_ref.get("sha256") != expected_plan_index_sha256
            or definition.get("runtime_sync_after_init_forbidden") is not True
            or definition.get("runtime_state_root") != expected_runtime_state_root
        ):
            raise RuntimeError("formal namespace-init receipt binding is stale")
    return {"path": str(path), "sha256": expected}


def _authorization_sha256(value: str, *, field: str) -> str:
    normalized = str(value).removeprefix("sha256:")
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise RuntimeError(f"{field} must be a lowercase SHA-256 digest")
    return normalized


def publish_remote_output_precondition_receipt(
    *,
    runtime_infra_path: str | Path,
    endpoint: Mapping[str, Any],
    remote_raw_root: str,
    blind_aggregate_root: str,
    runtime_state_root: str,
    failed_attempt_archive_root: str,
    retrieval_snapshot_root: str,
    probe_exit_code: int,
    probe_output: str,
    output_path: str | Path = DEFAULT_REMOTE_OUTPUT_PRECONDITION_RECEIPT,
    checked_at: str | None = None,
) -> NamespaceReceiptResult:
    """Publish one fresh receipt from the fixed-output SSH absence probe."""

    infra_file = _regular_file(runtime_infra_path, "runtime infra overlay")
    timestamp = checked_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    parse_timestamp(timestamp, "remote output precondition checked_at")
    expected_probe = (
        "RAW_ABSENT BLIND_ABSENT RUNTIME_ABSENT FAILED_ABSENT SNAPSHOT_ABSENT"
    )
    if probe_exit_code != 0 or probe_output.strip() != expected_probe:
        raise ContractLifecycleError(
            "one or more remote formal roots already exist; execution lock is forbidden"
        )
    definition = {
        "runtime_infra": _path_lock(infra_file),
        "endpoint": dict(endpoint),
        "remote_raw_root": _absolute(remote_raw_root, "remote raw root"),
        "blind_aggregate_root": _absolute(
            blind_aggregate_root, "blind aggregate root"
        ),
        "runtime_state_root": _absolute(runtime_state_root, "runtime state root"),
        "failed_attempt_archive_root": _absolute(
            failed_attempt_archive_root, "failed-attempt archive root"
        ),
        "retrieval_snapshot_root": _absolute(
            retrieval_snapshot_root, "retrieval snapshot root"
        ),
        "remote_raw_root_absent": True,
        "blind_aggregate_root_absent": True,
        "runtime_state_root_absent": True,
        "failed_attempt_archive_root_absent": True,
        "retrieval_snapshot_root_absent": True,
        "ssh_host_key_checking": "strict_pinned_ed25519",
        "probe_exit_code": 0,
        "probe_output": expected_probe,
        "secret_material_recorded": False,
        "evidence_content_read": False,
    }
    payload = {
        "schema_version": REMOTE_PRECONDITION_SCHEMA_VERSION,
        "status": "verified_absent",
        "checked_at": timestamp,
        "definition": definition,
        "definition_sha256": sha256_object(definition),
    }
    _validate_remote_precondition_payload(payload)
    output = resolve_repo_path(output_path)
    return _publish_immutable(output, payload)


def verify_remote_output_precondition_receipt(
    path: str | Path = DEFAULT_REMOTE_OUTPUT_PRECONDITION_RECEIPT,
    *,
    runtime_infra_path: str | Path | None = None,
    require_fresh: bool = False,
    now: datetime | None = None,
) -> NamespaceReceiptResult:
    receipt_file = _regular_file(path, "remote output precondition receipt")
    payload = load_mapping(receipt_file)
    _validate_remote_precondition_payload(payload)
    definition = dict(payload["definition"])
    infra_ref = dict(definition["runtime_infra"])
    infra_file = _regular_file(
        runtime_infra_path or str(infra_ref["path"]), "runtime infra overlay"
    )
    if infra_ref != _path_lock(infra_file):
        raise ContractLifecycleError(
            "remote output precondition runtime-infra binding is stale"
        )
    infra = load_mapping(infra_file)
    from evidence_system.contracts.agentdojo_full_execution import (
        _strict_agentdojo_infra_snapshot,
    )

    snapshot = _strict_agentdojo_infra_snapshot(infra)
    expected_endpoint = {
        "host": snapshot["ssh_host"],
        "port": snapshot["ssh_port"],
        "user": snapshot["ssh_user"],
        "fingerprint": snapshot["ssh_host_ed25519_fingerprint"],
    }
    if definition.get("endpoint") != expected_endpoint:
        raise ContractLifecycleError(
            "remote output precondition endpoint differs from runtime infra"
        )
    for field, expected in (
        ("remote_raw_root", snapshot["remote_raw_root"]),
        ("blind_aggregate_root", snapshot["blind_aggregate_root"]),
        ("runtime_state_root", snapshot["runtime_state_root"]),
        (
            "failed_attempt_archive_root",
            snapshot["failed_attempt_archive_root"],
        ),
        ("retrieval_snapshot_root", snapshot["retrieval_snapshot_root"]),
    ):
        if definition.get(field) != expected:
            raise ContractLifecycleError(
                f"remote output precondition {field} differs from runtime infra"
            )
    checked = parse_timestamp(
        str(payload["checked_at"]), "remote output precondition checked_at"
    )
    current = now or datetime.now(timezone.utc)
    if require_fresh and not timedelta(0) <= current - checked <= PRECONDITION_MAX_AGE:
        raise ContractLifecycleError(
            "remote output precondition receipt is not fresh enough to publish the lock"
        )
    return NamespaceReceiptResult(
        path=receipt_file,
        sha256=sha256_file(receipt_file),
        payload=dict(payload),
        created=False,
    )


def verify_formal_namespace_init_receipt(
    path: str | Path = DEFAULT_NAMESPACE_INIT_RECEIPT,
    *,
    execution_lock_path: str | Path | None = None,
    plan_index_path: str | Path | None = None,
    _execution_envelope_only: bool = False,
) -> NamespaceReceiptResult:
    """Verify all local/current immutable bindings before any stage may run."""

    receipt_file = _regular_file(path, "formal namespace-init receipt")
    payload = load_mapping(receipt_file)
    _validate_namespace_init_payload(payload)
    definition = dict(payload["definition"])
    from evidence_system.contracts.agentdojo_full_execution import (
        DEFAULT_EXECUTION_LOCK,
        verify_execution_lock,
        verify_execution_lock_envelope,
    )

    execution_verifier = (
        verify_execution_lock_envelope
        if _execution_envelope_only
        else verify_execution_lock
    )
    execution = execution_verifier(
        lock_path=execution_lock_path or DEFAULT_EXECUTION_LOCK
    )
    lock_ref = _path_lock(execution.lock_path)
    if definition.get("execution_lock") != lock_ref:
        raise ContractLifecycleError(
            "formal namespace-init receipt is bound to a different execution lock"
        )
    if definition.get("execution_policy_sha256") != execution.definition.get(
        "execution_policy_sha256"
    ):
        raise ContractLifecycleError(
            "formal namespace-init execution-policy binding is stale"
        )
    plan_ref = dict(definition.get("plan_index") or {})
    plan_file = _regular_file(
        plan_index_path or str(plan_ref.get("path") or ""), "locked job-plan index"
    )
    if plan_ref != _path_lock(plan_file):
        raise ContractLifecycleError("formal namespace-init plan-index binding is stale")
    for field in (
        "remote_output_precondition_receipt",
        "final_runtime_deployment_receipt",
        "runtime_infra",
    ):
        expected = execution.definition.get(
            "runtime_infra_overlay" if field == "runtime_infra" else field
        )
        if definition.get(field) != expected:
            raise ContractLifecycleError(
                f"formal namespace-init {field} differs from execution lock"
            )
        ref = dict(definition[field])
        current = _regular_file(str(ref.get("path") or ""), field)
        if ref != _path_lock(current):
            raise ContractLifecycleError(f"formal namespace-init {field} is stale")

    sealed = dict(execution.definition.get("sealed_remote_evidence") or {})
    for field in (
        "remote_raw_root",
        "blind_aggregate_root",
        "runtime_state_root",
        "failed_attempt_archive_root",
        "retrieval_snapshot_root",
    ):
        if definition.get(field) != sealed.get(field):
            raise ContractLifecycleError(
                f"formal namespace-init {field} differs from execution lock"
            )
    expected_endpoint = {
        "host": sealed.get("ssh_host"),
        "port": sealed.get("ssh_port"),
        "user": sealed.get("execution_user"),
        "fingerprint": sealed.get("ssh_host_ed25519_fingerprint"),
    }
    if definition.get("endpoint") != expected_endpoint:
        raise ContractLifecycleError("formal namespace-init endpoint binding is stale")
    if definition.get("runtime_sync_after_init_forbidden") is not True:
        raise ContractLifecycleError("formal namespace-init does not forbid runtime sync")
    expected_roles = (
        "raw",
        "blind",
        "runtime",
        "failed_attempt_archive",
        "retrieval_snapshot",
    )
    expected_paths = {
        "raw": sealed.get("remote_raw_root"),
        "blind": sealed.get("blind_aggregate_root"),
        "runtime": sealed.get("runtime_state_root"),
        "failed_attempt_archive": sealed.get("failed_attempt_archive_root"),
        "retrieval_snapshot": sealed.get("retrieval_snapshot_root"),
    }
    expected_modes = {
        "raw": sealed.get("remote_raw_mode"),
        "blind": sealed.get("blind_aggregate_dir_mode"),
        "runtime": sealed.get("runtime_state_mode"),
        "failed_attempt_archive": sealed.get("failed_attempt_archive_mode"),
        "retrieval_snapshot": sealed.get("retrieval_snapshot_mode"),
    }
    identities = list(definition.get("remote_root_identities") or [])
    markers = list(definition.get("namespace_markers") or [])
    if [row.get("role") for row in identities if isinstance(row, Mapping)] != list(
        expected_roles
    ) or [row.get("role") for row in markers if isinstance(row, Mapping)] != list(
        expected_roles
    ):
        raise ContractLifecycleError(
            "formal namespace-init root/marker role order differs"
        )
    transaction_id = str(definition.get("namespace_transaction_id") or "")
    if transaction_id != f"ns-{sha256_object({'execution_lock_sha256': execution.lock_sha256, 'plan_index_sha256': sha256_file(plan_file)})}":
        raise ContractLifecycleError(
            "formal namespace-init transaction identity differs"
        )
    for identity, marker in zip(identities, markers, strict=True):
        role = str(identity["role"])
        root = str(expected_paths[role])
        if identity.get("path") != root or identity.get("mode") != expected_modes[role]:
            raise ContractLifecycleError(
                f"formal namespace-init {role} identity path/mode differs"
            )
        expected_marker_path = f"{root.rstrip('/')}/NAMESPACE_INIT.json"
        marker_bytes = namespace_marker_bytes(
            execution_lock_sha256=execution.lock_sha256,
            plan_index_sha256=sha256_file(plan_file),
            namespace_transaction_id=transaction_id,
            initialized_at=str(payload["initialized_at"]),
            role=role,
            root=root,
        )
        if (
            marker.get("path") != expected_marker_path
            or marker.get("sha256") != sha256_bytes(marker_bytes)
            or marker.get("size_bytes") != len(marker_bytes)
            or marker.get("device") != identity.get("device")
        ):
            raise ContractLifecycleError(
                f"formal namespace-init {role} marker binding differs"
            )

    lock_payload = load_mapping(execution.lock_path)
    locked_at = parse_timestamp(
        str(lock_payload.get("locked_at") or ""), "execution lock locked_at"
    )
    initialized_at = parse_timestamp(
        str(payload.get("initialized_at") or ""), "namespace initialized_at"
    )
    deployment_result = verify_final_runtime_deployment_receipt(
        str(dict(definition["final_runtime_deployment_receipt"])["path"]),
        runtime_infra_path=str(dict(definition["runtime_infra"])["path"]),
    )
    deployment = deployment_result.payload
    deployed_at = parse_timestamp(
        str(deployment.get("completed_at") or ""),
        "final runtime deployment completed_at",
    )
    if not deployed_at < locked_at < initialized_at:
        raise ContractLifecycleError(
            "formal namespace-init chronology must be deployment < lock < init"
        )
    return NamespaceReceiptResult(
        path=receipt_file,
        sha256=sha256_file(receipt_file),
        payload=dict(payload),
        created=False,
    )


def verify_final_runtime_deployment_receipt(
    path: str | Path = DEFAULT_FINAL_RUNTIME_DEPLOYMENT_RECEIPT,
    *,
    runtime_infra_path: str | Path,
) -> NamespaceReceiptResult:
    receipt_file = _regular_file(path, "final runtime deployment receipt")
    payload = load_mapping(receipt_file)
    report = validate_object(
        "agentdojo_final_runtime_deployment_receipt",
        dict(payload),
        raise_on_error=False,
    )
    if not report.ok:
        raise ContractLifecycleError(
            f"final runtime deployment schema failed: {report.to_dict()}"
        )
    infra_file = _regular_file(runtime_infra_path, "runtime infra overlay")
    if payload.get("runtime_infra") != _path_lock(infra_file):
        raise ContractLifecycleError("final runtime deployment infra binding is stale")
    from evidence_system.adapters.agentdojo_runtime_control import (
        execution_runtime_snapshot,
    )

    if payload.get("runtime_snapshot") != execution_runtime_snapshot():
        raise ContractLifecycleError(
            "final runtime deployment snapshot differs from current execution runtime"
        )
    if (
        payload.get("remote_runtime_snapshot") != payload.get("runtime_snapshot")
        or payload.get("runtime_snapshots_equal") is not True
    ):
        raise ContractLifecycleError(
            "final runtime deployment remote runtime snapshot differs"
        )
    local = dict(payload.get("local_source") or {})
    remote = dict(payload.get("remote_source") or {})
    if (
        local.get("file_count") != remote.get("file_count")
        or local.get("tree_sha256") != remote.get("tree_sha256")
        or local.get("normalization_method") != remote.get("normalization_method")
        or local.get("excluded_patterns") != remote.get("excluded_patterns")
    ):
        raise ContractLifecycleError(
            "final runtime deployment local/remote source trees differ"
        )
    local_root = resolve_repo_path(str(local.get("root") or ""))
    file_count, tree_sha = normalized_source_tree(local_root)
    if (
        int(local.get("file_count") or 0) != file_count
        or local.get("tree_sha256") != tree_sha
    ):
        raise ContractLifecycleError(
            "final runtime deployment local source tree is stale"
        )
    parse_timestamp(str(payload.get("completed_at") or ""), "deployment completed_at")
    return NamespaceReceiptResult(
        path=receipt_file,
        sha256=sha256_file(receipt_file),
        payload=dict(payload),
        created=False,
    )


def normalized_source_tree(root: str | Path) -> tuple[int, str]:
    resolved = resolve_repo_path(root)
    if resolved.is_symlink() or not resolved.is_dir():
        raise ContractLifecycleError(
            f"runtime deployment source root is missing or symlinked: {resolved}"
        )
    files = sorted(
        path
        for path in resolved.rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    )
    if any(path.is_symlink() for path in resolved.rglob("*")):
        raise ContractLifecycleError("runtime deployment source tree contains symlinks")
    encoded = bytearray()
    for file_path in files:
        encoded.extend(file_path.relative_to(resolved).as_posix().encode("utf-8"))
        encoded.append(0)
        encoded.extend(bytes.fromhex(sha256_file(file_path)))
    return len(files), sha256_bytes(bytes(encoded))


def build_namespace_init_payload(
    *,
    initialized_at: str,
    definition: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "schema_version": NAMESPACE_INIT_SCHEMA_VERSION,
        "status": "initialized_empty_namespaces",
        "initialized_at": initialized_at,
        "definition": dict(definition),
        "definition_sha256": sha256_object(dict(definition)),
    }
    _validate_namespace_init_payload(payload)
    return payload


def namespace_marker_bytes(
    *,
    execution_lock_sha256: str,
    plan_index_sha256: str,
    namespace_transaction_id: str,
    initialized_at: str,
    role: str,
    root: str,
) -> bytes:
    """Canonical bytes created once inside every formal remote root."""

    marker = {
        "schema_version": "agentdojo_formal_namespace_marker/v2",
        "execution_lock_sha256": execution_lock_sha256,
        "plan_index_sha256": plan_index_sha256,
        "namespace_transaction_id": namespace_transaction_id,
        "initialized_at": initialized_at,
        "role": role,
        "root": root,
        "create_once": True,
    }
    return (
        json.dumps(marker, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("ascii")


def publish_namespace_init_payload(
    payload: Mapping[str, Any],
    *,
    output_path: str | Path = DEFAULT_NAMESPACE_INIT_RECEIPT,
) -> NamespaceReceiptResult:
    _validate_namespace_init_payload(payload)
    return _publish_immutable(resolve_repo_path(output_path), dict(payload))


def _validate_remote_precondition_payload(payload: Mapping[str, Any]) -> None:
    report = validate_object(
        "agentdojo_remote_output_precondition_receipt",
        dict(payload),
        raise_on_error=False,
    )
    if not report.ok:
        raise ContractLifecycleError(
            f"remote output precondition schema failed: {report.to_dict()}"
        )
    definition = payload.get("definition")
    if not isinstance(definition, Mapping) or payload.get(
        "definition_sha256"
    ) != sha256_object(definition):
        raise ContractLifecycleError(
            "remote output precondition definition hash mismatch"
        )


def _validate_namespace_init_payload(payload: Mapping[str, Any]) -> None:
    report = validate_object(
        "agentdojo_formal_execution_namespace_init_receipt",
        dict(payload),
        raise_on_error=False,
    )
    if not report.ok:
        raise ContractLifecycleError(
            f"formal namespace-init schema failed: {report.to_dict()}"
        )
    definition = payload.get("definition")
    if not isinstance(definition, Mapping) or payload.get(
        "definition_sha256"
    ) != sha256_object(definition):
        raise ContractLifecycleError("formal namespace-init definition hash mismatch")


def _path_lock(path: Path) -> dict[str, str]:
    return {"path": _portable(path), "sha256": sha256_file(path)}


def _portable(path: Path) -> str:
    resolved = path.resolve()
    root = resolve_repo_path(".").resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return str(resolved)


def _regular_file(path: str | Path, label: str) -> Path:
    resolved = resolve_repo_path(path)
    if resolved.is_symlink() or not resolved.is_file():
        raise ContractLifecycleError(f"{label} is missing or symlinked: {resolved}")
    return resolved.resolve()


def _absolute(value: str, label: str) -> str:
    if not value or "\n" in value or not Path(value).is_absolute():
        raise ContractLifecycleError(f"{label} must be an absolute path")
    return value


def _publish_immutable(path: Path, payload: Mapping[str, Any]) -> NamespaceReceiptResult:
    if path.exists():
        if path.is_symlink() or not path.is_file():
            raise ContractLifecycleError(f"immutable receipt path is unsafe: {path}")
        existing = load_mapping(path)
        if existing != dict(payload):
            raise ContractLifecycleError(
                f"immutable receipt already exists and differs: {path}"
            )
        return NamespaceReceiptResult(
            path=path.resolve(),
            sha256=sha256_file(path),
            payload=dict(existing),
            created=False,
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    parent_info = os.lstat(path.parent)
    if stat.S_ISLNK(parent_info.st_mode) or not stat.S_ISDIR(parent_info.st_mode):
        raise ContractLifecycleError(
            f"immutable receipt parent is unsafe: {path.parent}"
        )
    encoded = (
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    try:
        descriptor = os.open(
            path,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
    except FileExistsError:
        existing = load_mapping(path)
        if existing != dict(payload):
            raise ContractLifecycleError(
                f"immutable receipt appeared concurrently and differs: {path}"
            )
        return NamespaceReceiptResult(
            path=path.resolve(),
            sha256=sha256_file(path),
            payload=dict(existing),
            created=False,
        )
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    parent_descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(parent_descriptor)
    finally:
        os.close(parent_descriptor)
    return NamespaceReceiptResult(
        path=path.resolve(),
        sha256=sha256_file(path),
        payload=dict(payload),
        created=True,
    )
