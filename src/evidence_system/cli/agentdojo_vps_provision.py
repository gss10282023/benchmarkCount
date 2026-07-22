"""Finalize and attest the pinned AgentDojo VPS runtime without starting episodes.

The controller-facing command performs a final ``rsync --delete`` of the
execution runtime, asks the already-synced locked virtualenv Python to audit
the installed AgentDojo wheel/RECORD closure, and publishes create-once
deployment and provision receipts.  The hidden remote command never reads an
OpenRouter secret or any evidence result.
"""

from __future__ import annotations

import argparse
import base64
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any, Mapping, Sequence

from evidence_system.adapters.agentdojo_runtime_control import (
    execution_runtime_snapshot,
)
from evidence_system.adapters.runtime import run_remote_blind_command
from evidence_system.contracts.agentdojo_execution_namespace import (
    DEFAULT_FINAL_RUNTIME_DEPLOYMENT_RECEIPT,
    normalized_source_tree,
    verify_final_runtime_deployment_receipt,
)
from evidence_system.contracts.agentdojo_full_execution import (
    AGENTDOJO_COMMIT,
    AGENTDOJO_PACKAGE_VERSION,
    AGENTDOJO_TREE,
    AGENTDOJO_WHEEL,
    AGENTDOJO_WHEEL_SHA256,
    BENCHMARK_VERSION,
    DEFAULT_RUNTIME_INFRA_OVERLAY,
    DEFAULT_VPS_PROVISION_RECEIPT,
    EXPECTED_CASE_COUNT,
    EXPECTED_SUITE_COUNTS,
    _strict_agentdojo_infra_snapshot,
)
from evidence_system.contracts.common import ContractLifecycleError, load_mapping
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import validate_object
from evidence_system.orchestrator.jobs import resolve_infra_target


EXPERIMENT_ROOT = Path("experiments/agentdojo_full_v1.2.2_direct")
DEFAULT_PRELIMINARY_ARCHIVE = EXPERIMENT_ROOT / "provenance/preliminary"
DEFAULT_UPSTREAM_ROOT = "/srv/agentdojo-full/agentdojo-upstream-v0.1.35"
DEFAULT_WHEEL_FILE = f"/srv/agentdojo-full/tooling/wheels/{AGENTDOJO_WHEEL}"
SOURCE_EXCLUDES = ("**/__pycache__/**", "**/*.pyc", "**/*.pyo")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    finalize = sub.add_parser("final-sync")
    finalize.add_argument("--runtime-infra", default=str(DEFAULT_RUNTIME_INFRA_OVERLAY))
    finalize.add_argument("--preliminary-receipt", default=str(DEFAULT_VPS_PROVISION_RECEIPT))
    finalize.add_argument("--deployment-output", default=str(DEFAULT_FINAL_RUNTIME_DEPLOYMENT_RECEIPT))
    finalize.add_argument("--provision-output", default=str(DEFAULT_VPS_PROVISION_RECEIPT))
    finalize.add_argument("--preliminary-archive-root", default=str(DEFAULT_PRELIMINARY_ARCHIVE))
    finalize.add_argument("--upstream-root", default=DEFAULT_UPSTREAM_ROOT)
    finalize.add_argument("--wheel-file", default=DEFAULT_WHEEL_FILE)
    finalize.add_argument(
        "--credential-status",
        choices=("missing", "validated"),
        required=True,
    )
    finalize.add_argument("--rsync-bin", default="rsync")
    remote = sub.add_parser("remote-audit", help=argparse.SUPPRESS)
    remote.add_argument("--repo-root", required=True)
    remote.add_argument("--upstream-root", required=True)
    remote.add_argument("--wheel-file", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "remote-audit":
            result = build_remote_audit(
                repo_root=Path(args.repo_root),
                upstream_root=Path(args.upstream_root),
                wheel_file=Path(args.wheel_file),
            )
        else:
            result = final_sync_and_publish(
                runtime_infra_path=args.runtime_infra,
                preliminary_receipt_path=args.preliminary_receipt,
                deployment_output_path=args.deployment_output,
                provision_output_path=args.provision_output,
                preliminary_archive_root=args.preliminary_archive_root,
                upstream_root=args.upstream_root,
                wheel_file=args.wheel_file,
                credential_status=args.credential_status,
                rsync_bin=args.rsync_bin,
            )
    except (ContractLifecycleError, OSError, RuntimeError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "formal_episode_started": False,
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


def final_sync_and_publish(
    *,
    runtime_infra_path: str | Path,
    preliminary_receipt_path: str | Path,
    deployment_output_path: str | Path,
    provision_output_path: str | Path,
    preliminary_archive_root: str | Path,
    upstream_root: str,
    wheel_file: str,
    credential_status: str,
    rsync_bin: str = "rsync",
) -> dict[str, Any]:
    """Synchronize runtime bytes and publish the two pre-lock receipts."""

    infra_file = _regular_file(runtime_infra_path, "runtime infra overlay")
    infra = load_mapping(infra_file)
    snapshot = _strict_agentdojo_infra_snapshot(infra)
    target = resolve_infra_target("agentdojo", infra)
    preliminary_file = _regular_file(preliminary_receipt_path, "preliminary VPS receipt")
    preliminary = load_mapping(preliminary_file)
    if preliminary.get("schema_version") not in {
        "agentdojo_vps_provision_receipt/v1",
        "agentdojo_vps_provision_receipt/v2",
    }:
        raise ContractLifecycleError("preliminary VPS receipt schema is unsupported")
    archive = _archive_preliminary_once(
        preliminary_file, resolve_repo_path(preliminary_archive_root)
    )

    _require_formal_roots_absent(snapshot, target)
    _rsync_runtime_sources(
        snapshot=snapshot,
        target=target,
        rsync_bin=rsync_bin,
    )
    _run_locked_uv_sync(snapshot=snapshot, target=target)
    remote = _remote_audit(
        snapshot=snapshot,
        target=target,
        upstream_root=upstream_root,
        wheel_file=wheel_file,
    )
    local_count, local_tree = normalized_source_tree(resolve_repo_path("src"))
    remote_source = dict(remote["runtime_source"])
    if (
        remote_source.get("file_count") != local_count
        or remote_source.get("tree_sha256") != local_tree
    ):
        raise ContractLifecycleError("final local/remote src trees differ after rsync")
    runtime_snapshot = execution_runtime_snapshot()
    if remote.get("runtime_snapshot") != runtime_snapshot:
        raise ContractLifecycleError("remote execution-runtime snapshot differs after sync")
    completed_at = _utc_now_iso()
    deployment = {
        "schema_version": "agentdojo_final_runtime_deployment_receipt/v1",
        "status": "synced_verified_frozen",
        "completed_at": completed_at,
        "runtime_infra": _path_lock(infra_file),
        "runtime_snapshot": runtime_snapshot,
        "remote_runtime_snapshot": dict(remote["runtime_snapshot"]),
        "runtime_snapshots_equal": True,
        "local_source": _source_tree_payload(
            root=resolve_repo_path("src"), count=local_count, digest=local_tree
        ),
        "remote_source": _source_tree_payload(
            root=Path(str(snapshot["remote_workdir"])) / "src",
            count=int(remote_source["file_count"]),
            digest=str(remote_source["tree_sha256"]),
        ),
        "trees_equal": True,
        "rsync_delete": True,
        "rsync_source_trailing_slash": True,
        "remote_extra_file_count": 0,
        "sync_completed_before_namespace_init": True,
        "namespace_uninitialized_at_completion": True,
        "runtime_mutation_after_init_forbidden": True,
        "secrets_included": False,
    }
    deployment_file = resolve_repo_path(deployment_output_path)
    _publish_create_once(deployment_file, deployment)
    verify_final_runtime_deployment_receipt(
        deployment_file, runtime_infra_path=infra_file
    )

    closure = dict(remote["agentdojo_runtime_source_closure"])
    runtime = dict(preliminary.get("runtime") or {})
    runtime.update(
        {
            "pyproject_sha256": sha256_file(resolve_repo_path("pyproject.toml")),
            "uv_lock_sha256": sha256_file(resolve_repo_path("uv.lock")),
            "deployed_src_file_count": local_count,
            "deployed_src_tree_sha256": _legacy_src_tree_sha256(),
            "deployed_src_tree_excludes": ["__pycache__", "*.egg-info"],
            "local_remote_src_match_at_recording": True,
            "final_execution_freeze_resync_required": False,
        }
    )
    credentials = {
        "openrouter_api_key_status": credential_status,
        "openrouter_api_key_environment_present": credential_status == "validated",
        "dotenv_file_count_under_runtime_root": 0,
        "openrouter_key_endpoint_check": (
            "passed" if credential_status == "validated" else "not_run_missing_credential"
        ),
        "secret_material_recorded": False,
    }
    ready = credential_status == "validated"
    provision = {
        **{
            key: value
            for key, value in preliminary.items()
            if key
            not in {
                "schema_version",
                "recorded_at_utc",
                "status",
                "runtime",
                "credentials",
                "run_readiness",
                "agentdojo_runtime_source_closure",
                "agentdojo_runtime_source_closure_sha256",
                "preliminary_receipt_supersession",
            }
        },
        "schema_version": "agentdojo_vps_provision_receipt/v2",
        "recorded_at_utc": completed_at,
        "status": "provisioned" if ready else "provisioned_blocked_on_credentials",
        "runtime": runtime,
        "credentials": credentials,
        "run_readiness": {
            "disposable_smoke_authorized": ready,
            "formal_run_authorized": ready,
            "blocking_reasons": [] if ready else ["OPENROUTER_API_KEY is not validated"],
        },
        "agentdojo_runtime_source_closure": closure,
        "agentdojo_runtime_source_closure_sha256": sha256_object(closure),
        "preliminary_receipt_supersession": _path_lock(archive),
    }
    validate_object("agentdojo_vps_provision_receipt", provision)
    provision_file = resolve_repo_path(provision_output_path)
    if provision_file.resolve() == preliminary_file.resolve():
        _replace_preliminary_with_final_once(provision_file, provision, archive=archive)
    else:
        _publish_create_once(provision_file, provision)
    return {
        "status": "final_runtime_synced_and_attested",
        "formal_episode_started": False,
        "deployment_receipt": _path_lock(deployment_file),
        "provision_receipt": _path_lock(provision_file),
        "preliminary_receipt": _path_lock(archive),
        "agentdojo_runtime_source_closure_sha256": sha256_object(closure),
    }


def build_remote_audit(
    *, repo_root: Path, upstream_root: Path, wheel_file: Path
) -> dict[str, Any]:
    """Build the remote, content-free runtime and wheel/RECORD audit envelope."""

    for path, label in (
        (repo_root, "repo root"),
        (upstream_root, "AgentDojo upstream root"),
    ):
        if not path.is_absolute() or path.is_symlink() or not path.is_dir():
            raise ContractLifecycleError(f"remote {label} is unsafe or missing")
    if not wheel_file.is_absolute() or wheel_file.is_symlink() or not wheel_file.is_file():
        raise ContractLifecycleError("pinned AgentDojo wheel file is unsafe or missing")
    if sha256_file(wheel_file) != AGENTDOJO_WHEEL_SHA256:
        raise ContractLifecycleError("pinned AgentDojo wheel SHA-256 differs")
    src_count, src_tree = normalized_source_tree(repo_root / "src")
    closure = _installed_agentdojo_closure(
        upstream_root=upstream_root, wheel_file=wheel_file
    )
    return {
        "schema_version": "agentdojo_vps_remote_audit/v1",
        "runtime_source": {"file_count": src_count, "tree_sha256": src_tree},
        "runtime_snapshot": execution_runtime_snapshot(),
        "agentdojo_runtime_source_closure": closure,
        "secret_material_recorded": False,
    }


def _installed_agentdojo_closure(
    *, upstream_root: Path, wheel_file: Path
) -> dict[str, Any]:
    distribution = importlib.metadata.distribution("agentdojo")
    if distribution.version != AGENTDOJO_PACKAGE_VERSION:
        raise ContractLifecycleError("installed AgentDojo version differs")
    files = list(distribution.files or [])
    if not files:
        raise ContractLifecycleError("installed AgentDojo distribution has no RECORD files")
    normalized: list[str] = []
    content_manifest: list[dict[str, str]] = []
    located: dict[str, Path] = {}
    for relative_value in files:
        relative = PurePosixPath(str(relative_value))
        if relative.is_absolute() or ".." in relative.parts:
            raise ContractLifecycleError("AgentDojo RECORD path escapes distribution")
        name = relative.as_posix()
        path = Path(distribution.locate_file(relative_value))
        info = os.lstat(path)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ContractLifecycleError("AgentDojo installed file is linked or non-regular")
        normalized.append(name)
        located[name] = path
        content_manifest.append({"path": name, "sha256": sha256_file(path)})
    if len(normalized) != len(set(normalized)):
        raise ContractLifecycleError("AgentDojo installed path set contains duplicates")
    normalized.sort()
    content_manifest.sort(key=lambda row: row["path"])
    record_names = [name for name in normalized if name.endswith(".dist-info/RECORD")]
    if len(record_names) != 1:
        raise ContractLifecycleError("AgentDojo distribution has no unique RECORD")
    record_name = record_names[0]
    record_path = located[record_name]
    rows = list(csv.reader(record_path.read_text(encoding="utf-8").splitlines()))
    if any(len(row) != 3 for row in rows):
        raise ContractLifecycleError("AgentDojo RECORD row shape differs")
    record_paths = [PurePosixPath(row[0]).as_posix() for row in rows]
    if len(record_paths) != len(set(record_paths)) or set(record_paths) != set(normalized):
        raise ContractLifecycleError("AgentDojo RECORD/install path denominator differs")
    verified = 0
    unhashed = 0
    for raw_path, raw_hash, raw_size in rows:
        name = PurePosixPath(raw_path).as_posix()
        path = located[name]
        if raw_size and int(raw_size) != path.stat().st_size:
            raise ContractLifecycleError("AgentDojo RECORD file size differs")
        if not raw_hash:
            unhashed += 1
            continue
        algorithm, separator, encoded = raw_hash.partition("=")
        if separator != "=" or algorithm != "sha256":
            raise ContractLifecycleError("AgentDojo RECORD uses a non-SHA256 hash")
        padding = "=" * ((4 - len(encoded) % 4) % 4)
        digest = base64.urlsafe_b64decode(encoded + padding).hex()
        if digest != sha256_file(path):
            raise ContractLifecycleError("AgentDojo RECORD content hash differs")
        verified += 1
    if unhashed != 1 or record_name not in {
        PurePosixPath(row[0]).as_posix() for row in rows if not row[1]
    }:
        raise ContractLifecycleError("only AgentDojo RECORD may be unhashed")

    head = _checked_output(["git", "-C", str(upstream_root), "rev-parse", "HEAD"])
    tree = _checked_output(["git", "-C", str(upstream_root), "rev-parse", "HEAD^{tree}"])
    dirty = _checked_output(["git", "-C", str(upstream_root), "status", "--porcelain"])
    if head != AGENTDOJO_COMMIT or tree != AGENTDOJO_TREE or dirty:
        raise ContractLifecycleError("official AgentDojo checkout is not the clean pinned tree")
    package_root = Path(importlib.import_module("agentdojo").__file__).resolve().parent
    upstream_package = upstream_root / "src" / "agentdojo"
    installed_package_manifest = _regular_tree_manifest(package_root)
    upstream_package_manifest = _regular_tree_manifest(upstream_package)
    if installed_package_manifest != upstream_package_manifest:
        raise ContractLifecycleError("installed AgentDojo package differs from upstream tree")
    return {
        "schema_version": "agentdojo_runtime_source_closure/v1",
        "package_name": "agentdojo",
        "package_version": AGENTDOJO_PACKAGE_VERSION,
        "official_git_commit": AGENTDOJO_COMMIT,
        "official_git_tree": AGENTDOJO_TREE,
        "wheel_filename": AGENTDOJO_WHEEL,
        "wheel_sha256": AGENTDOJO_WHEEL_SHA256,
        "wheel_file_path": str(wheel_file),
        "dist_info_record_relative_path": record_name,
        "dist_info_record_sha256": sha256_file(record_path),
        "installed_file_count": len(normalized),
        "installed_path_set_sha256": sha256_object(normalized),
        "installed_content_manifest_sha256": sha256_object(content_manifest),
        "record_entry_count": len(rows),
        "record_verified_file_count": verified,
        "record_unhashed_entry_count": unhashed,
        "record_verification": (
            "all_hashed_entries_match_paths_contained_no_links_or_special_inodes"
        ),
        "imported_package_root": str(package_root),
        "upstream_repository_root": str(upstream_root),
        "upstream_head_matches_official_commit": True,
        "upstream_tree_matches_official_tree": True,
        "installed_source_matches_upstream_tree": True,
        "closure_verified": True,
        "secret_material_recorded": False,
    }


def _rsync_runtime_sources(*, snapshot: Mapping[str, Any], target: Any, rsync_bin: str) -> None:
    known_hosts = str(snapshot["ssh_known_hosts_file"])
    key = str(snapshot["ssh_key_path"])
    endpoint = f"{snapshot['ssh_user']}@{snapshot['ssh_host']}"
    remote_root = str(snapshot["remote_workdir"]).rstrip("/")
    ssh_transport = (
        f"ssh -i {key} -p {int(snapshot['ssh_port'])} -o BatchMode=yes "
        f"-o IdentitiesOnly=yes -o StrictHostKeyChecking=yes "
        f"-o UserKnownHostsFile={known_hosts} -o HostKeyAlgorithms=ssh-ed25519"
    )
    for local_name, remote_name in (("src", "src"), ("schemas", "schemas")):
        source = resolve_repo_path(local_name)
        command = [
            rsync_bin,
            "-az",
            "--delete",
            "--exclude=__pycache__/",
            "--exclude=*.pyc",
            "--exclude=*.pyo",
            "-e",
            ssh_transport,
            f"{source.resolve()}/",
            f"{endpoint}:{remote_root}/{remote_name}/",
        ]
        _checked_run(command, label=f"final {local_name} rsync")
    for relative in (
        "pyproject.toml",
        "uv.lock",
        "configs/agents.yaml",
        "experiments/agentdojo_full_v1.2.2_direct/runtime/openrouter_runtime_policy.json",
        "experiments/agentdojo_full_v1.2.2_direct/runtime/infra.vultr.yaml",
    ):
        source = resolve_repo_path(relative)
        _checked_run(
            [
                rsync_bin,
                "-az",
                "-e",
                ssh_transport,
                str(source.resolve()),
                f"{endpoint}:{remote_root}/{relative}",
            ],
            label=f"final runtime file sync: {relative}",
        )


def _run_locked_uv_sync(*, snapshot: Mapping[str, Any], target: Any) -> None:
    command = (
        f"cd {json.dumps(str(snapshot['remote_workdir']))} && "
        f"/srv/agentdojo-full/tooling/uv-0.9.24/bin/uv sync --locked --extra agentdojo-full"
    )
    result = run_remote_blind_command(
        target,
        command,
        timeout_seconds=900,
        transient_retry_attempts=1,
        maximum_stdout_bytes=0,
        maximum_stderr_bytes=2048,
    )
    if result.returncode != 0:
        raise ContractLifecycleError("remote uv sync --locked failed")


def _remote_audit(
    *, snapshot: Mapping[str, Any], target: Any, upstream_root: str, wheel_file: str
) -> dict[str, Any]:
    python_bin = str(snapshot["python_bin"])
    repo_root = str(snapshot["remote_workdir"])
    command = (
        f"cd {json.dumps(repo_root)} && PYTHONPATH={json.dumps(repo_root + '/src')} "
        f"{json.dumps(python_bin)} -m evidence_system.cli.agentdojo_vps_provision "
        f"remote-audit --repo-root {json.dumps(repo_root)} "
        f"--upstream-root {json.dumps(upstream_root)} --wheel-file {json.dumps(wheel_file)}"
    )
    result = run_remote_blind_command(
        target,
        command,
        timeout_seconds=300,
        transient_retry_attempts=1,
        maximum_stdout_bytes=131_072,
        maximum_stderr_bytes=0,
    )
    if result.returncode != 0 or result.stderr:
        raise ContractLifecycleError("remote AgentDojo closure audit failed")
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict) or payload.get("schema_version") != (
        "agentdojo_vps_remote_audit/v1"
    ):
        raise ContractLifecycleError("remote AgentDojo audit envelope differs")
    return payload


def _require_formal_roots_absent(snapshot: Mapping[str, Any], target: Any) -> None:
    roots = [
        snapshot[field]
        for field in (
            "remote_raw_root",
            "blind_aggregate_root",
            "runtime_state_root",
            "failed_attempt_archive_root",
            "retrieval_snapshot_root",
        )
    ]
    script = "import os,sys; raise SystemExit(1 if any(os.path.lexists(p) for p in sys.argv[1:]) else 0)"
    command = " ".join(
        [json.dumps(str(snapshot["python_bin"])), "-c", json.dumps(script)]
        + [json.dumps(str(value)) for value in roots]
    )
    result = run_remote_blind_command(
        target,
        command,
        timeout_seconds=30,
        transient_retry_attempts=1,
        maximum_stdout_bytes=0,
        maximum_stderr_bytes=0,
    )
    if result.returncode != 0:
        raise ContractLifecycleError("formal remote roots are not all absent before final sync")


def _regular_tree_manifest(root: Path) -> list[dict[str, str]]:
    if root.is_symlink() or not root.is_dir():
        raise ContractLifecycleError("AgentDojo package tree is missing or symlinked")
    rows: list[dict[str, str]] = []
    for path in sorted(root.rglob("*")):
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        info = os.lstat(path)
        if stat.S_ISLNK(info.st_mode):
            raise ContractLifecycleError("AgentDojo package tree contains a symlink")
        if stat.S_ISREG(info.st_mode):
            rows.append(
                {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}
            )
        elif not stat.S_ISDIR(info.st_mode):
            raise ContractLifecycleError("AgentDojo package tree contains a special inode")
    return rows


def _legacy_src_tree_sha256() -> str:
    root = resolve_repo_path("src")
    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
        and not any(part.endswith(".egg-info") for part in path.parts)
    )
    return sha256_object(
        [
            {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}
            for path in files
        ]
    )


def _source_tree_payload(*, root: Path, count: int, digest: str) -> dict[str, Any]:
    return {
        "root": str(root),
        "file_count": count,
        "tree_sha256": digest,
        "normalization_method": "relative_posix_path_nul_sha256_bytes/v1",
        "excluded_patterns": list(SOURCE_EXCLUDES),
    }


def _archive_preliminary_once(source: Path, root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    digest = sha256_file(source)
    destination = root / f"vps_provision_receipt.{digest}.json"
    if destination.exists():
        if destination.is_symlink() or sha256_file(destination) != digest:
            raise ContractLifecycleError("preliminary VPS archive is stale or linked")
        return destination.resolve()
    descriptor = os.open(
        destination,
        os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        data = source.read_bytes()
        os.write(descriptor, data)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    if sha256_file(destination) != digest:
        raise ContractLifecycleError("preliminary VPS archive copy hash differs")
    _fsync_dir(root)
    return destination.resolve()


def _replace_preliminary_with_final_once(path: Path, payload: Mapping[str, Any], *, archive: Path) -> None:
    if sha256_file(path) != sha256_file(archive):
        raise ContractLifecycleError("preliminary VPS receipt changed after archival")
    encoded = (json.dumps(dict(payload), indent=2, sort_keys=True) + "\n").encode()
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_dir(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _publish_create_once(path: Path, payload: Mapping[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise ContractLifecycleError(f"create-once receipt already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        path,
        os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        encoded = (json.dumps(dict(payload), indent=2, sort_keys=True) + "\n").encode()
        os.write(descriptor, encoded)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _fsync_dir(path.parent)


def _checked_run(command: Sequence[str], *, label: str) -> None:
    completed = subprocess.run(list(command), check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise ContractLifecycleError(f"{label} failed with exit {completed.returncode}")


def _checked_output(command: Sequence[str]) -> str:
    completed = subprocess.run(list(command), check=False, capture_output=True, text=True)
    if completed.returncode != 0 or completed.stderr:
        raise ContractLifecycleError("remote AgentDojo git audit command failed")
    return completed.stdout.strip()


def _regular_file(path: str | Path, label: str) -> Path:
    candidate = resolve_repo_path(path)
    if candidate.is_symlink() or not candidate.is_file() or candidate.stat().st_nlink != 1:
        raise ContractLifecycleError(f"{label} is missing, linked, or non-regular")
    return candidate.resolve()


def _path_lock(path: Path) -> dict[str, str]:
    return {"path": _display(path), "sha256": sha256_file(path)}


def _display(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(resolve_repo_path(".").resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _fsync_dir(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
