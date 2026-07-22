"""Machine-driven pre-lock and post-lock AgentDojo VPS namespace control.

The public commands never accept hand-authored probe output.  Every receipt is
derived from one strict-ED25519 SSH observation of the pinned runtime overlay.
The hidden ``remote-*`` commands are executed with the overlay's absolute,
locked virtualenv Python and emit only fixed content-blind envelopes.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import grp
import json
import os
from pathlib import Path
import pwd
import shlex
import stat
import sys
from typing import Any, Mapping, Sequence

from evidence_system.adapters.runtime import run_remote_blind_command
from evidence_system.contracts.agentdojo_execution_namespace import (
    DEFAULT_NAMESPACE_INIT_RECEIPT,
    DEFAULT_REMOTE_OUTPUT_PRECONDITION_RECEIPT,
    build_namespace_init_payload,
    namespace_marker_bytes,
    publish_namespace_init_payload,
    publish_remote_output_precondition_receipt,
    verify_formal_namespace_init_receipt,
    verify_remote_output_precondition_receipt,
)
from evidence_system.contracts.agentdojo_full_execution import (
    DEFAULT_EXECUTION_LOCK,
    DEFAULT_LOCAL_BLIND_METADATA_ROOT,
    DEFAULT_RUNTIME_INFRA_OVERLAY,
    DEFAULT_STAGING_RAW_RESULT_ROOT,
    _strict_agentdojo_infra_snapshot,
    verify_execution_lock,
)
from evidence_system.contracts.agentdojo_full_experiment import (
    DEFAULT_AGENTS_CONFIG,
    DEFAULT_MANIFEST,
    DEFAULT_SCORE_NAMESPACE_ROOTS,
    DEFAULT_SOURCE_BUNDLE,
)
from evidence_system.contracts.common import (
    ContractLifecycleError,
    load_mapping,
    utc_now_iso,
)
from evidence_system.core.hashing import sha256_bytes, sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path
from evidence_system.orchestrator.jobs import resolve_infra_target


ROOT_ROLES = (
    "raw",
    "blind",
    "runtime",
    "failed_attempt_archive",
    "retrieval_snapshot",
)
REMOTE_RESULT_FIELDS = frozenset(
    {
        "schema_version",
        "status",
        "action",
        "namespace_transaction_id",
        "root_identities",
        "namespace_markers",
        "blind_only",
    }
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("precondition", "init", "verify-current"):
        item = sub.add_parser(name)
        item.add_argument("--runtime-infra", default=str(DEFAULT_RUNTIME_INFRA_OVERLAY))
    precondition = sub.choices["precondition"]
    precondition.add_argument(
        "--output", default=str(DEFAULT_REMOTE_OUTPUT_PRECONDITION_RECEIPT)
    )
    init = sub.choices["init"]
    init.add_argument("--execution-lock", default=str(DEFAULT_EXECUTION_LOCK))
    init.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    init.add_argument("--source-bundle", default=str(DEFAULT_SOURCE_BUNDLE))
    init.add_argument("--agents-config", default=str(DEFAULT_AGENTS_CONFIG))
    init.add_argument("--output", default=str(DEFAULT_NAMESPACE_INIT_RECEIPT))
    verify = sub.choices["verify-current"]
    verify.add_argument("--execution-lock", default=str(DEFAULT_EXECUTION_LOCK))
    verify.add_argument("--plan-index", required=True)
    verify.add_argument("--receipt", default=str(DEFAULT_NAMESPACE_INIT_RECEIPT))

    # Not a controller-facing interface.  These modes are intentionally omitted
    # from help and are called only through the exact virtualenv Python below.
    remote = sub.add_parser("remote-control", help=argparse.SUPPRESS)
    remote.add_argument("--action", choices=("precondition", "init", "verify"), required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "remote-control":
            request = json.load(sys.stdin)
            result = _remote_control(request, action=args.action)
            if isinstance(result, str):
                print(result)
                return 0
        elif args.command == "precondition":
            result = precondition_remote_namespaces(
                runtime_infra_path=args.runtime_infra,
                output_path=args.output,
            )
        elif args.command == "init":
            result = initialize_formal_namespaces(
                runtime_infra_path=args.runtime_infra,
                execution_lock_path=args.execution_lock,
                manifest_path=args.manifest,
                source_bundle_path=args.source_bundle,
                agents_config_path=args.agents_config,
                output_path=args.output,
            )
        else:
            result = verify_current_formal_namespaces(
                runtime_infra_path=args.runtime_infra,
                execution_lock_path=args.execution_lock,
                plan_index_path=args.plan_index,
                receipt_path=args.receipt,
            )
    except (ContractLifecycleError, OSError, RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


def precondition_remote_namespaces(
    *,
    runtime_infra_path: str | Path = DEFAULT_RUNTIME_INFRA_OVERLAY,
    output_path: str | Path = DEFAULT_REMOTE_OUTPUT_PRECONDITION_RECEIPT,
) -> dict[str, Any]:
    infra_file, snapshot, target = _infra_context(runtime_infra_path)
    roots = _root_specs(snapshot)
    request = {"schema_version": "agentdojo_namespace_control_request/v2", "roots": roots}
    completed = _run_remote(target, snapshot, action="precondition", request=request)
    expected = "RAW_ABSENT BLIND_ABSENT RUNTIME_ABSENT FAILED_ABSENT SNAPSHOT_ABSENT"
    receipt = publish_remote_output_precondition_receipt(
        runtime_infra_path=infra_file,
        endpoint=_endpoint(snapshot, user=snapshot["ssh_user"]),
        remote_raw_root=snapshot["remote_raw_root"],
        blind_aggregate_root=snapshot["blind_aggregate_root"],
        runtime_state_root=snapshot["runtime_state_root"],
        failed_attempt_archive_root=snapshot["failed_attempt_archive_root"],
        retrieval_snapshot_root=snapshot["retrieval_snapshot_root"],
        probe_exit_code=completed.returncode,
        probe_output=completed.stdout,
        output_path=output_path,
    )
    if completed.stdout.strip() != expected:
        raise ContractLifecycleError("remote precondition fixed output differs")
    verified = verify_remote_output_precondition_receipt(
        receipt.path, runtime_infra_path=infra_file, require_fresh=True
    )
    return {"status": "verified_absent", "receipt": _path_lock(verified.path)}


def initialize_formal_namespaces(
    *,
    runtime_infra_path: str | Path,
    execution_lock_path: str | Path,
    manifest_path: str | Path,
    source_bundle_path: str | Path,
    agents_config_path: str | Path,
    output_path: str | Path = DEFAULT_NAMESPACE_INIT_RECEIPT,
) -> dict[str, Any]:
    infra_file, snapshot, target = _infra_context(runtime_infra_path)
    execution = verify_execution_lock(
        lock_path=execution_lock_path,
        manifest_path=manifest_path,
        source_bundle_path=source_bundle_path,
        agents_config_path=agents_config_path,
        runtime_infra_path=infra_file,
    )
    from evidence_system.orchestrator.agentdojo_locked_runner import (
        build_and_verify_locked_plan,
    )

    plan = build_and_verify_locked_plan(
        execution_lock_path=execution.lock_path,
        manifest_path=manifest_path,
        source_bundle_path=source_bundle_path,
        infra_config_path=infra_file,
        agents_config_path=agents_config_path,
    )
    if plan.execution.lock_sha256 != execution.lock_sha256:
        raise ContractLifecycleError("namespace init plan execution-lock binding differs")
    _require_empty_local_outputs()
    initialized_at = utc_now_iso()
    transaction_id = "ns-" + sha256_object(
        {
            "execution_lock_sha256": execution.lock_sha256,
            "plan_index_sha256": plan.plan_index_sha256,
        }
    )
    roots = _root_specs(snapshot)
    request = {
        "schema_version": "agentdojo_namespace_control_request/v2",
        "action": "init",
        "execution_lock_sha256": execution.lock_sha256,
        "plan_index_sha256": plan.plan_index_sha256,
        "namespace_transaction_id": transaction_id,
        "initialized_at": initialized_at,
        "execution_user": snapshot["execution_user"],
        "blind_group": snapshot["blind_group"],
        "control_lock_path": (
            f"{Path(snapshot['runtime_state_root']).parent.as_posix()}"
            "/.agentdojo-full-namespace-init.lock"
        ),
        "roots": roots,
    }
    completed = _run_remote(target, snapshot, action="init", request=request)
    remote = _parse_remote_result(completed, expected_action="init", transaction_id=transaction_id)
    definition = {
        "execution_lock": _path_lock(execution.lock_path),
        "execution_policy_sha256": execution.definition["execution_policy_sha256"],
        "plan_index": _path_lock(plan.plan_index_path),
        "remote_output_precondition_receipt": execution.definition[
            "remote_output_precondition_receipt"
        ],
        "final_runtime_deployment_receipt": execution.definition[
            "final_runtime_deployment_receipt"
        ],
        "runtime_infra": execution.definition["runtime_infra_overlay"],
        "endpoint": _endpoint(snapshot, user=snapshot["execution_user"]),
        "remote_raw_root": snapshot["remote_raw_root"],
        "blind_aggregate_root": snapshot["blind_aggregate_root"],
        "runtime_state_root": snapshot["runtime_state_root"],
        "failed_attempt_archive_root": snapshot["failed_attempt_archive_root"],
        "retrieval_snapshot_root": snapshot["retrieval_snapshot_root"],
        "roots_previously_absent": True,
        "remote_root_identities": remote["root_identities"],
        "namespace_markers": remote["namespace_markers"],
        "namespace_transaction_id": transaction_id,
        "remote_create_once": True,
        "runtime_sync_after_init_forbidden": True,
        "local_staging_root": _display(resolve_repo_path(DEFAULT_STAGING_RAW_RESULT_ROOT)),
        "local_staging_file_count": 0,
        "local_blind_metadata_root": _display(resolve_repo_path(DEFAULT_LOCAL_BLIND_METADATA_ROOT)),
        "local_blind_metadata_file_count_before_receipt": 0,
        "score_result_roots": [
            _display(resolve_repo_path(value)) for value in DEFAULT_SCORE_NAMESPACE_ROOTS
        ],
        "score_result_file_count": 0,
        "secret_material_recorded": False,
    }
    payload = build_namespace_init_payload(
        initialized_at=initialized_at, definition=definition
    )
    published = publish_namespace_init_payload(payload, output_path=output_path)
    verify_formal_namespace_init_receipt(
        published.path,
        execution_lock_path=execution.lock_path,
        plan_index_path=plan.plan_index_path,
    )
    return {"status": "initialized", "receipt": _path_lock(published.path)}


def verify_current_formal_namespaces(
    *,
    runtime_infra_path: str | Path,
    execution_lock_path: str | Path,
    plan_index_path: str | Path,
    receipt_path: str | Path = DEFAULT_NAMESPACE_INIT_RECEIPT,
) -> dict[str, Any]:
    infra_file, snapshot, target = _infra_context(runtime_infra_path)
    receipt = verify_formal_namespace_init_receipt(
        receipt_path,
        execution_lock_path=execution_lock_path,
        plan_index_path=plan_index_path,
    )
    definition = receipt.payload["definition"]
    request = {
        "schema_version": "agentdojo_namespace_control_request/v2",
        "action": "verify",
        "execution_lock_sha256": sha256_file(resolve_repo_path(execution_lock_path)),
        "plan_index_sha256": sha256_file(resolve_repo_path(plan_index_path)),
        "namespace_transaction_id": definition["namespace_transaction_id"],
        "initialized_at": receipt.payload["initialized_at"],
        "execution_user": snapshot["execution_user"],
        "blind_group": snapshot["blind_group"],
        "control_lock_path": (
            f"{Path(snapshot['runtime_state_root']).parent.as_posix()}"
            "/.agentdojo-full-namespace-init.lock"
        ),
        "roots": _root_specs(snapshot),
    }
    completed = _run_remote(target, snapshot, action="verify", request=request)
    remote = _parse_remote_result(
        completed,
        expected_action="verify",
        transaction_id=str(definition["namespace_transaction_id"]),
    )
    _compare_current_remote_identity(definition, remote)
    return {"status": "current", "receipt": _path_lock(receipt.path)}


def _run_remote(target: Any, snapshot: Mapping[str, Any], *, action: str, request: Mapping[str, Any]) -> Any:
    python_bin = str(snapshot["python_bin"])
    if not python_bin.startswith("/"):
        raise ContractLifecycleError("namespace control Python must be absolute")
    command = (
        f"cd {shlex.quote(str(snapshot['remote_workdir']))} && "
        f"PYTHONPATH={shlex.quote(str(snapshot['remote_workdir']) + '/src')} "
        f"{shlex.quote(python_bin)} -m "
        "evidence_system.cli.agentdojo_namespace_control remote-control "
        f"--action {shlex.quote(action)}"
    )
    result = run_remote_blind_command(
        target,
        command,
        stdin_text=json.dumps(request, ensure_ascii=True, sort_keys=True),
        timeout_seconds=60,
        transient_retry_attempts=1,
        maximum_stdout_bytes=32_768,
        maximum_stderr_bytes=0,
    )
    if result.returncode != 0:
        raise ContractLifecycleError(
            f"remote namespace {action} failed closed: exit_code={result.returncode}"
        )
    return result


def _remote_control(request: Mapping[str, Any], *, action: str) -> Any:
    if not isinstance(request, Mapping) or request.get("schema_version") != (
        "agentdojo_namespace_control_request/v2"
    ):
        raise ContractLifecycleError("remote namespace request schema differs")
    roots = list(request.get("roots") or [])
    if [row.get("role") for row in roots if isinstance(row, Mapping)] != list(ROOT_ROLES):
        raise ContractLifecycleError("remote namespace root order differs")
    if action == "precondition":
        if any(_lexists(Path(str(row["path"]))) for row in roots):
            raise ContractLifecycleError("one or more formal roots already exist")
        return "RAW_ABSENT BLIND_ABSENT RUNTIME_ABSENT FAILED_ABSENT SNAPSHOT_ABSENT"
    required = {
        "action",
        "execution_lock_sha256",
        "plan_index_sha256",
        "namespace_transaction_id",
        "initialized_at",
        "execution_user",
        "blind_group",
        "control_lock_path",
    }
    if any(key not in request for key in required) or request.get("action") != action:
        raise ContractLifecycleError("remote namespace request fields differ")
    lock_path = Path(str(request["control_lock_path"]))
    _assert_absolute_safe(lock_path)
    lock_parent_info = os.lstat(lock_path.parent)
    if stat.S_ISLNK(lock_parent_info.st_mode) or not stat.S_ISDIR(
        lock_parent_info.st_mode
    ):
        raise ContractLifecycleError("namespace control-lock parent is unsafe")
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        identities, markers = _remote_initialize_or_verify(
            request, roots=roots, create=(action == "init")
        )
    finally:
        os.close(descriptor)
    return {
        "schema_version": "agentdojo_namespace_control_result/v2",
        "status": "initialized" if action == "init" else "current",
        "action": action,
        "namespace_transaction_id": request["namespace_transaction_id"],
        "root_identities": identities,
        "namespace_markers": markers,
        "blind_only": True,
    }


def _remote_initialize_or_verify(
    request: Mapping[str, Any], *, roots: Sequence[Mapping[str, Any]], create: bool
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    identities: list[dict[str, Any]] = []
    markers: list[dict[str, Any]] = []
    execution_user = str(request["execution_user"])
    user_info = pwd.getpwnam(execution_user)
    primary_group = grp.getgrgid(user_info.pw_gid).gr_name
    for row in roots:
        role = str(row["role"])
        root = Path(str(row["path"]))
        _assert_absolute_safe(root)
        parent = root.parent
        parent_info = os.lstat(parent)
        if stat.S_ISLNK(parent_info.st_mode) or not stat.S_ISDIR(parent_info.st_mode):
            raise ContractLifecycleError("formal root parent is unsafe")
        expected_parent_mode = int(str(row["parent_mode"]), 8)
        if stat.S_IMODE(parent_info.st_mode) != expected_parent_mode:
            raise ContractLifecycleError("formal root parent mode differs")
        group_name = str(request["blind_group"]) if role == "blind" else primary_group
        group_info = grp.getgrnam(group_name)
        marker_bytes = namespace_marker_bytes(
            execution_lock_sha256=str(request["execution_lock_sha256"]),
            plan_index_sha256=str(request["plan_index_sha256"]),
            namespace_transaction_id=str(request["namespace_transaction_id"]),
            initialized_at=str(request["initialized_at"]),
            role=role,
            root=str(root),
        )
        if not _lexists(root):
            if not create:
                raise ContractLifecycleError("formal root disappeared")
            temporary = parent / (
                f".{root.name}.{request['namespace_transaction_id']}.init"
            )
            if not _lexists(temporary):
                os.mkdir(temporary, int(str(row["mode"]), 8))
            _verify_or_prepare_temporary(
                temporary,
                owner_uid=user_info.pw_uid,
                group_gid=group_info.gr_gid,
                mode=int(str(row["mode"]), 8),
                marker_bytes=marker_bytes,
                marker_mode=int(str(row["marker_mode"]), 8),
            )
            if _lexists(root):
                raise ContractLifecycleError("formal root appeared during create-once")
            os.rename(temporary, root)
            _fsync_dir(parent)
        identity, marker = _inspect_remote_root(
            role=role,
            root=root,
            expected_bytes=marker_bytes,
            expected_uid=user_info.pw_uid,
            expected_gid=group_info.gr_gid,
            expected_mode=int(str(row["mode"]), 8),
            expected_marker_mode=int(str(row["marker_mode"]), 8),
            require_empty=create,
        )
        identities.append(identity)
        markers.append(marker)
    return identities, markers


def _verify_or_prepare_temporary(
    temporary: Path,
    *,
    owner_uid: int,
    group_gid: int,
    mode: int,
    marker_bytes: bytes,
    marker_mode: int,
) -> None:
    info = os.lstat(temporary)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise ContractLifecycleError("namespace transaction temporary root is unsafe")
    os.chown(temporary, owner_uid, group_gid)
    os.chmod(temporary, mode)
    marker = temporary / "NAMESPACE_INIT.json"
    if not _lexists(marker):
        descriptor = os.open(
            marker,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0),
            marker_mode,
        )
        try:
            os.write(descriptor, marker_bytes)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.chown(marker, owner_uid, group_gid)
        os.chmod(marker, marker_mode)
    elif marker.read_bytes() != marker_bytes:
        raise ContractLifecycleError("namespace transaction marker differs")
    if {entry.name for entry in os.scandir(temporary)} != {"NAMESPACE_INIT.json"}:
        raise ContractLifecycleError("namespace transaction temporary root has extra entries")
    _fsync_dir(temporary)


def _inspect_remote_root(
    *,
    role: str,
    root: Path,
    expected_bytes: bytes,
    expected_uid: int,
    expected_gid: int,
    expected_mode: int,
    expected_marker_mode: int,
    require_empty: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    info = os.lstat(root)
    if (
        stat.S_ISLNK(info.st_mode)
        or not stat.S_ISDIR(info.st_mode)
        or info.st_uid != expected_uid
        or info.st_gid != expected_gid
        or stat.S_IMODE(info.st_mode) != expected_mode
    ):
        raise ContractLifecycleError(f"formal {role} root identity differs")
    marker_path = root / "NAMESPACE_INIT.json"
    marker_info = os.lstat(marker_path)
    if (
        stat.S_ISLNK(marker_info.st_mode)
        or not stat.S_ISREG(marker_info.st_mode)
        or marker_info.st_nlink != 1
        or marker_info.st_uid != expected_uid
        or marker_info.st_gid != expected_gid
        or stat.S_IMODE(marker_info.st_mode) != expected_marker_mode
        or marker_path.read_bytes() != expected_bytes
    ):
        raise ContractLifecycleError(f"formal {role} namespace marker differs")
    if require_empty and {entry.name for entry in os.scandir(root)} != {"NAMESPACE_INIT.json"}:
        raise ContractLifecycleError(f"formal {role} root is not empty at initialization")
    owner_user = pwd.getpwuid(info.st_uid).pw_name
    group_name = grp.getgrgid(info.st_gid).gr_name
    return (
        {
            "role": role,
            "path": str(root),
            "owner_user": owner_user,
            "owner_uid": info.st_uid,
            "group_name": group_name,
            "group_gid": info.st_gid,
            "mode": f"{stat.S_IMODE(info.st_mode):04o}",
            "device": info.st_dev,
            "inode": info.st_ino,
            "nlink": info.st_nlink,
        },
        {
            "role": role,
            "path": str(marker_path),
            "sha256": sha256_bytes(expected_bytes),
            "size_bytes": marker_info.st_size,
            "owner_user": pwd.getpwuid(marker_info.st_uid).pw_name,
            "owner_uid": marker_info.st_uid,
            "group_name": grp.getgrgid(marker_info.st_gid).gr_name,
            "group_gid": marker_info.st_gid,
            "mode": f"{stat.S_IMODE(marker_info.st_mode):04o}",
            "device": marker_info.st_dev,
            "inode": marker_info.st_ino,
            "nlink": marker_info.st_nlink,
        },
    )


def _parse_remote_result(completed: Any, *, expected_action: str, transaction_id: str) -> dict[str, Any]:
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ContractLifecycleError("remote namespace result is not JSON") from exc
    if (
        not isinstance(payload, dict)
        or set(payload) != REMOTE_RESULT_FIELDS
        or payload.get("schema_version") != "agentdojo_namespace_control_result/v2"
        or payload.get("action") != expected_action
        or payload.get("status")
        != ("initialized" if expected_action == "init" else "current")
        or payload.get("namespace_transaction_id") != transaction_id
        or payload.get("blind_only") is not True
        or len(list(payload.get("root_identities") or [])) != 5
        or len(list(payload.get("namespace_markers") or [])) != 5
    ):
        raise ContractLifecycleError("remote namespace result envelope differs")
    return payload


def _compare_current_remote_identity(definition: Mapping[str, Any], remote: Mapping[str, Any]) -> None:
    locked_identities = list(definition["remote_root_identities"])
    current_identities = list(remote["root_identities"])
    for locked, current in zip(locked_identities, current_identities, strict=True):
        for field in (
            "role", "path", "owner_user", "owner_uid", "group_name", "group_gid",
            "mode", "device", "inode",
        ):
            if current.get(field) != locked.get(field):
                raise ContractLifecycleError(f"remote root current {field} differs")
    if remote["namespace_markers"] != definition["namespace_markers"]:
        raise ContractLifecycleError("remote namespace marker identities drifted")


def _root_specs(snapshot: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {"role": "raw", "path": snapshot["remote_raw_root"], "parent_mode": snapshot["remote_raw_parent_mode"], "mode": snapshot["remote_raw_mode"], "marker_mode": "0600"},
        {"role": "blind", "path": snapshot["blind_aggregate_root"], "parent_mode": snapshot["blind_aggregate_dir_mode"], "mode": snapshot["blind_aggregate_dir_mode"], "marker_mode": snapshot["blind_aggregate_file_mode"]},
        {"role": "runtime", "path": snapshot["runtime_state_root"], "parent_mode": snapshot["runtime_state_parent_mode"], "mode": snapshot["runtime_state_mode"], "marker_mode": "0600"},
        {"role": "failed_attempt_archive", "path": snapshot["failed_attempt_archive_root"], "parent_mode": snapshot["failed_attempt_archive_parent_mode"], "mode": snapshot["failed_attempt_archive_mode"], "marker_mode": "0600"},
        {"role": "retrieval_snapshot", "path": snapshot["retrieval_snapshot_root"], "parent_mode": snapshot["retrieval_snapshot_parent_mode"], "mode": snapshot["retrieval_snapshot_mode"], "marker_mode": "0600"},
    ]


def _infra_context(path: str | Path) -> tuple[Path, dict[str, Any], Any]:
    infra = resolve_repo_path(path)
    if infra.is_symlink() or not infra.is_file():
        raise ContractLifecycleError("runtime infra overlay is missing or symlinked")
    payload = load_mapping(infra)
    snapshot = _strict_agentdojo_infra_snapshot(payload)
    target = resolve_infra_target("agentdojo", payload)
    return infra.resolve(), snapshot, target


def _endpoint(snapshot: Mapping[str, Any], *, user: str) -> dict[str, Any]:
    return {"host": snapshot["ssh_host"], "port": snapshot["ssh_port"], "user": user, "fingerprint": snapshot["ssh_host_ed25519_fingerprint"]}


def _require_empty_local_outputs() -> None:
    roots = [
        resolve_repo_path(DEFAULT_STAGING_RAW_RESULT_ROOT),
        resolve_repo_path(DEFAULT_LOCAL_BLIND_METADATA_ROOT),
        *(resolve_repo_path(value) for value in DEFAULT_SCORE_NAMESPACE_ROOTS),
    ]
    counts = [_tree_file_count(value) for value in roots]
    if any(counts):
        raise ContractLifecycleError(
            "namespace init requires empty local staging, blind metadata, and score roots"
        )


def _tree_file_count(root: Path) -> int:
    if not _lexists(root):
        return 0
    info = os.lstat(root)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise ContractLifecycleError(f"local output root is unsafe: {root}")
    count = 0
    for value in root.rglob("*"):
        entry = os.lstat(value)
        if stat.S_ISLNK(entry.st_mode) or (
            not stat.S_ISDIR(entry.st_mode) and not stat.S_ISREG(entry.st_mode)
        ):
            raise ContractLifecycleError(f"local output tree is unsafe: {value}")
        if stat.S_ISREG(entry.st_mode):
            if entry.st_nlink != 1:
                raise ContractLifecycleError(f"local output file is hard-linked: {value}")
            count += 1
    return count


def _assert_absolute_safe(path: Path) -> None:
    if not path.is_absolute() or ".." in path.parts or "\n" in str(path):
        raise ContractLifecycleError("remote namespace path is unsafe")


def _lexists(path: Path) -> bool:
    try:
        os.lstat(path)
    except FileNotFoundError:
        return False
    return True


def _fsync_dir(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _path_lock(path: Path) -> dict[str, str]:
    return {"path": _display(path), "sha256": sha256_file(path)}


def _display(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(resolve_repo_path(".").resolve()).as_posix()
    except ValueError:
        return str(resolved)


if __name__ == "__main__":
    raise SystemExit(main())
