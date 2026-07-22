"""VPS-resident sealing and read-only verification for WebArena-Verified.

The module is intentionally runnable on a benchmark VPS.  Full browser/model
evidence never crosses the SSH boundary: ``seal`` inventories and scans it in
place, while ``verify`` emits only a bounded, secret-free control envelope.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import sys
from typing import Any, Mapping, Sequence

from evidence_system.adapters.runtime import job_result_relative_dir
from evidence_system.adapters.webarena_har_sanitization import (
    load_and_validate_network_sanitization_receipt,
)
from evidence_system.core.hashing import sha256_file, sha256_object
RETENTION_MODE = "vps_persistent_remote_v1"
PERSISTENT_RESULTS_ROOT = Path("/opt/webarena-results/controller-results")
MANIFEST_SCHEMA = "webarena_verified_remote_artifact_manifest/v1"
SECURITY_SCHEMA = "webarena_verified_remote_security_acceptance/v1"
EVALUATOR_SCHEMA = "webarena_verified_remote_evaluator_receipt/v1"
SLOT_SCHEMA = "webarena_verified_remote_slot_acceptance/v1"
VERIFY_SCHEMA = "webarena_verified_remote_slot_verification/v1"
HOST_SCHEMA = "webarena_verified_remote_host_finalization/v1"

PUBLIC_RECEIPT_NAMES = (
    "remote_artifact_manifest.json",
    "remote_security_acceptance.json",
    "remote_evaluator_receipt.json",
    "remote_slot_acceptance.json",
)


class RemoteRetentionError(RuntimeError):
    """Raised when remote evidence cannot be sealed or verified exactly."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise RemoteRetentionError(f"{label} is missing or unsafe")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RemoteRetentionError(f"{label} is not valid JSON") from exc
    if not isinstance(value, dict):
        raise RemoteRetentionError(f"{label} is not a JSON object")
    return value


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    encoded = (
        json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    sidecar = path.with_suffix(f"{path.suffix}.sha256")
    sidecar.write_text(f"{sha256_file(path)}  {path.name}\n", encoding="ascii")


def _parse_job(value: str) -> dict[str, Any]:
    try:
        job = json.loads(value)
    except json.JSONDecodeError as exc:
        raise RemoteRetentionError("job JSON is invalid") from exc
    if not isinstance(job, dict):
        raise RemoteRetentionError("job JSON is not an object")
    if job.get("artifact_retention_mode") != RETENTION_MODE:
        raise RemoteRetentionError("job is not locked to VPS persistent retention")
    if not job.get("result_namespace"):
        raise RemoteRetentionError("remote-retention job has no result namespace")
    return job


def _expected_adapter_root(job: Mapping[str, Any]) -> Path:
    relative = job_result_relative_dir(job)
    if not relative.parts or relative.parts[0] != "results":
        raise RemoteRetentionError("job result path is outside the results root")
    return PERSISTENT_RESULTS_ROOT.joinpath(*relative.parts[1:], "adapter")


def validate_adapter_root(adapter_root: str | Path, job: Mapping[str, Any]) -> Path:
    raw = Path(adapter_root)
    if not raw.is_absolute():
        raise RemoteRetentionError("remote adapter root must be absolute")
    resolved = raw.resolve(strict=False)
    expected = _expected_adapter_root(job)
    if resolved != expected:
        raise RemoteRetentionError(
            "remote adapter root does not resolve to the locked persistent namespace"
        )
    if PERSISTENT_RESULTS_ROOT not in resolved.parents:
        raise RemoteRetentionError("remote adapter root escapes persistent storage")
    return resolved


def _partial_tree_receipt(root: Path) -> dict[str, Any]:
    """Return a content-free, deterministic binding for a partial slot tree."""

    entries: list[dict[str, Any]] = []
    total_size_bytes = 0
    for path in sorted(root.rglob("*")):
        info = os.lstat(path)
        if stat.S_ISDIR(info.st_mode):
            continue
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise RemoteRetentionError(
                "partial remote artifact tree contains a non-regular file"
            )
        relative = path.relative_to(root).as_posix()
        entries.append(
            {
                "path": relative,
                "sha256": sha256_file(path),
                "size_bytes": info.st_size,
            }
        )
        total_size_bytes += info.st_size
    return {
        "tree_sha256": sha256_object(entries),
        "file_count": len(entries),
        "total_size_bytes": total_size_bytes,
    }


def prepare_slot(*, job: Mapping[str, Any], adapter_root: str | Path) -> dict[str, Any]:
    """Prepare a new slot without deleting any previous remote evidence."""

    root = validate_adapter_root(adapter_root, job)
    action = "created"
    preservation: dict[str, Any] | None = None
    if root.exists():
        if root.is_symlink() or not root.is_dir():
            raise RemoteRetentionError("existing remote adapter root is unsafe")
        if any(root.iterdir()):
            existing = root / "remote_slot_acceptance.json"
            if existing.is_file():
                try:
                    verified = verify_slot(job=job, adapter_root=root)
                except RemoteRetentionError:
                    verified = None
                if verified is not None and verified.get("status") == "pass":
                    return {
                        "schema_version": "webarena_verified_remote_slot_prepare/v1",
                        "status": "already_sealed",
                        "job_binding_sha256": sha256_object(dict(job)),
                        "remote_directory_deleted": False,
                    }
            before = _partial_tree_receipt(root)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            preserved = root.with_name(f"{root.name}.preserved-{stamp}")
            if preserved.exists():
                raise RemoteRetentionError("remote preservation target already exists")
            root.rename(preserved)
            after = _partial_tree_receipt(preserved)
            if before != after:
                raise RemoteRetentionError(
                    "partial remote artifact tree changed during preservation"
                )
            preservation = {
                "schema_version": "webarena_verified_partial_preservation/v1",
                "status": "pass",
                "job_binding_sha256": sha256_object(dict(job)),
                "preserved_directory_name": preserved.name,
                **after,
                "remote_directory_deleted": False,
                "secret_material_recorded": False,
            }
            action = "preserved_partial_then_created"
    root.mkdir(parents=True, exist_ok=False if action != "created" else True)
    (root / "native_run").mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(parents=True, exist_ok=True)
    if preservation is not None:
        _write_json(root / "logs" / "partial_preservation_receipt.json", preservation)
    receipt = {
        "schema_version": "webarena_verified_remote_slot_prepare/v1",
        "status": "prepared",
        "action": action,
        "job_binding_sha256": sha256_object(dict(job)),
        "remote_directory_deleted": False,
    }
    if preservation is not None:
        receipt["partial_preservation"] = preservation
    return receipt


def _inventory(adapter_root: Path) -> list[dict[str, Any]]:
    roots = [adapter_root / "native_run", adapter_root / "logs"]
    entries: list[dict[str, Any]] = []
    seen_inodes: set[tuple[int, int]] = set()
    for root in roots:
        if not root.is_dir() or root.is_symlink():
            raise RemoteRetentionError(f"remote artifact root is missing or unsafe: {root.name}")
        for path in sorted(root.rglob("*")):
            info = os.lstat(path)
            if stat.S_ISDIR(info.st_mode):
                continue
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                raise RemoteRetentionError("remote artifact tree contains a non-regular file")
            inode = (info.st_dev, info.st_ino)
            if info.st_nlink != 1 or inode in seen_inodes:
                raise RemoteRetentionError("remote artifact tree contains a hard-linked file")
            seen_inodes.add(inode)
            relative = path.relative_to(adapter_root).as_posix()
            if relative.startswith("native_run/llm_attempts/"):
                artifact_class = "full_llm_record"
            elif relative.endswith("network.har"):
                artifact_class = "har"
            elif "/traces/" in f"/{relative}":
                artifact_class = "playwright_trace"
            elif "screenshot" in relative.lower() or relative.endswith(".png"):
                artifact_class = "screenshot"
            elif relative.startswith("logs/"):
                artifact_class = "runtime_log"
            else:
                artifact_class = "native_evidence"
            entries.append(
                {
                    "relative_path": relative,
                    "sha256": sha256_file(path),
                    "size_bytes": info.st_size,
                    "artifact_class": artifact_class,
                    "retention": "vps_only",
                }
            )
    return entries


def _required_paths(native: Path, task_id: int) -> dict[str, Path]:
    task = native / str(task_id)
    return {
        "reset_receipt": native / "reset_receipt.json",
        "run_summary": native / "run_summary.json",
        "native_evaluator_input": native / "native_evaluator_input.json",
        "native_evaluator_output": native / "native_evaluator_output.json",
        "job": native / "job.json",
        "source_bundle_entry": native / "source_bundle_entry.json",
        "worker_config": native / "worker_config.json",
        "webarena_env": native / "webarena_env.json",
        "render": native / f"render_{task_id}.html",
        "trace": native / "traces" / f"{task_id}.zip",
        "official_task": task / "official_task_config.json",
        "agent_response": task / "agent_response.json",
        "solver_trace": task / "solver_trace.json",
        "har": task / "network.har",
        "har_receipt": task / "network_har_sanitization.json",
        "eval_result": task / "eval_result.json",
        "eval_summary": task / "eval_summary.json",
        "evaluator_stdout": task / "official_evaluator.stdout.log",
        "evaluator_stderr": task / "official_evaluator.stderr.log",
    }


def _validate_native(job: Mapping[str, Any], native: Path) -> tuple[dict[str, Path], dict[str, Any], dict[str, Any]]:
    task_id = int(job["task_id"])
    required = _required_paths(native, task_id)
    missing = sorted(label for label, path in required.items() if not path.is_file())
    if missing:
        raise RemoteRetentionError(f"remote native evidence is incomplete: {','.join(missing)}")
    for directory in (native / "llm_attempts", native / "official_run"):
        if not directory.is_dir() or directory.is_symlink():
            raise RemoteRetentionError("remote native evidence directory is incomplete")
    summary = _load_object(required["run_summary"], "run summary")
    eval_summary = _load_object(required["eval_summary"], "official evaluator summary")
    native_job = _load_object(required["job"], "worker job binding")
    reset = _load_object(required["reset_receipt"], "reset receipt")
    if sha256_object(native_job) != sha256_object(dict(job)):
        raise RemoteRetentionError("worker job binding differs from the scheduled job")
    if (
        summary.get("status") != "completed"
        or summary.get("llm_used") is not True
        or summary.get("used_expected_fallback") is not False
        or int(summary.get("task_id", -1)) != task_id
        or int(summary.get("task_revision", -1)) != int(job["task_revision"])
    ):
        raise RemoteRetentionError("run summary failed the formal native contract")
    if (
        eval_summary.get("schema_version")
        != "webarena_verified_official_eval_summary/v1"
        or eval_summary.get("official_evaluation_completed") is not True
        or eval_summary.get("integrity_verified") is not True
        or eval_summary.get("summary_contains_private_evaluator_payload") is not False
        or eval_summary.get("official_evaluator_exit_code") != 0
        or int(eval_summary.get("task_id", -1)) != task_id
        or int(eval_summary.get("task_revision", -1)) != int(job["task_revision"])
    ):
        raise RemoteRetentionError("official evaluator summary failed the formal contract")
    if float(eval_summary.get("score", -1.0)) not in (0.0, 1.0):
        raise RemoteRetentionError("official evaluator score is outside the binary contract")
    expected_slot = {
        "slot_id": str(job["record_slot_id"]),
        "task_id": task_id,
        "agent_id": str(job["agent_id"]),
        "attempt_id": str(job["attempt_id"]),
        "seed": int(job["seed"]),
    }
    if reset.get("status") != "pass" or dict(reset.get("slot") or {}) != expected_slot:
        raise RemoteRetentionError("reset receipt is not bound to the scheduled slot")
    receipt = load_and_validate_network_sanitization_receipt(
        required["har_receipt"],
        har_path=required["har"],
        trace_path=required["trace"],
    )
    if receipt.get("status") != "pass":
        raise RemoteRetentionError("HAR/trace sanitization receipt is not pass")
    return required, summary, eval_summary


def _llm_metrics(native: Path) -> dict[str, Any]:
    responses = sorted((native / "llm_attempts").glob("*_response.json"))
    if not responses:
        raise RemoteRetentionError("remote evidence has no complete LLM response record")
    total_cost = 0.0
    for path in responses:
        payload = _load_object(path, "LLM response record")
        usage = payload.get("usage")
        if isinstance(usage, Mapping):
            total_cost += float(usage.get("cost") or 0.0)
    return {
        "complete_record_count": len(responses),
        "observed_cost_usd": round(total_cost, 12),
        "full_records_retained_on_vps": True,
    }


def _materialize_model_visible_agent_input(
    native: Path, requested_path: str | Path
) -> Path:
    source = _load_object(native / "source_bundle_entry.json", "safe source entry")
    agent_input = source.get("agent_input")
    expected_fields = {
        "task_id",
        "intent_template_id",
        "intent",
        "sites",
        "start_urls",
    }
    if not isinstance(agent_input, Mapping) or set(agent_input) != expected_fields:
        raise RemoteRetentionError("safe source entry agent input is invalid")
    requested = Path(requested_path)
    if requested.is_file():
        locked = _load_object(requested, "agent input")
        if locked != dict(agent_input):
            raise RemoteRetentionError("agent input differs from the safe source entry")
    output = native / "model_visible_agent_input.json"
    _write_json(output, dict(agent_input))
    return output


def seal_slot(
    *,
    job: Mapping[str, Any],
    adapter_root: str | Path,
    active_secret_env: str,
    agent_input_path: str | Path,
) -> dict[str, Any]:
    # Imported lazily to keep the adapter import graph acyclic; the finalizer
    # also imports run-control for pilot monitoring.
    from evidence_system.orchestrator.webarena_verified_pilot_finalization import (
        _scan_runtime_security,
    )

    root = validate_adapter_root(adapter_root, job)
    native = root / "native_run"
    required, summary, eval_summary = _validate_native(job, native)
    model_visible_agent_input = _materialize_model_visible_agent_input(
        native, agent_input_path
    )
    active_secret = os.environ.get(active_secret_env)
    if not active_secret:
        raise RemoteRetentionError("active secret is unavailable for the exact-match scan")
    inventory = _inventory(root)
    if not inventory:
        raise RemoteRetentionError("remote artifact inventory is empty")
    scan_paths = [root / item["relative_path"] for item in inventory]
    security_scan = _scan_runtime_security(
        scan_paths=scan_paths,
        agent_inputs=[model_visible_agent_input],
        active_secret=active_secret,
    )
    if security_scan.get("status") != "pass":
        raise RemoteRetentionError("remote runtime security scan found sensitive material")
    job_binding = sha256_object(dict(job))
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "status": "pass",
        "job_binding_sha256": job_binding,
        "record_slot_id": str(job["record_slot_id"]),
        "artifact_retention_mode": RETENTION_MODE,
        "persistent_adapter_root": str(root),
        "file_count": len(inventory),
        "total_size_bytes": sum(int(item["size_bytes"]) for item in inventory),
        "inventory_sha256": sha256_object(inventory),
        "files": inventory,
        "remote_directory_cleanup_performed": False,
        "full_evidence_synced_to_controller": False,
    }
    manifest_path = root / "remote_artifact_manifest.json"
    _write_json(manifest_path, manifest)
    security = {
        "schema_version": SECURITY_SCHEMA,
        "status": "pass",
        "job_binding_sha256": job_binding,
        "record_slot_id": str(job["record_slot_id"]),
        "scan": security_scan,
        "gates": {
            "active_secret_exact_match_zero": security_scan.get("active_secret_exact_match_count") == 0,
            "credential_cookie_authorization_findings_zero": security_scan.get("finding_count") == 0,
            "model_visible_gold_findings_zero": security_scan.get("gold_finding_count") == 0,
        },
        "secret_values_or_hashes_recorded": False,
    }
    security_path = root / "remote_security_acceptance.json"
    _write_json(security_path, security)
    evaluator = {
        "schema_version": EVALUATOR_SCHEMA,
        "status": "pass",
        "job_binding_sha256": job_binding,
        "record_slot_id": str(job["record_slot_id"]),
        "task_id": int(job["task_id"]),
        "task_revision": int(job["task_revision"]),
        "official_evaluator_completed": True,
        "official_evaluator_exit_code": 0,
        "score": float(eval_summary["score"]),
        "evaluation_status": str(eval_summary["status"]),
        "eval_summary_sha256": sha256_file(required["eval_summary"]),
        "eval_result_sha256": sha256_file(required["eval_result"]),
        "network_har_sha256": sha256_file(required["har"]),
        "playwright_trace_sha256": sha256_file(required["trace"]),
        "private_evaluator_payload_in_receipt": False,
    }
    evaluator_path = root / "remote_evaluator_receipt.json"
    _write_json(evaluator_path, evaluator)
    slot = {
        "schema_version": SLOT_SCHEMA,
        "status": "pass",
        "sealed_at": _now(),
        "job_binding_sha256": job_binding,
        "record_slot_id": str(job["record_slot_id"]),
        "agent_id": str(job["agent_id"]),
        "server_id": str(dict(job.get("execution_target") or {}).get("server_id") or ""),
        "artifact_retention_mode": RETENTION_MODE,
        "persistent_adapter_root": str(root),
        "remote_artifact_manifest_sha256": sha256_file(manifest_path),
        "remote_security_acceptance_sha256": sha256_file(security_path),
        "remote_evaluator_receipt_sha256": sha256_file(evaluator_path),
        "reset_receipt_sha256": sha256_file(required["reset_receipt"]),
        "run_summary_sha256": sha256_file(required["run_summary"]),
        "network_sanitization_receipt_sha256": sha256_file(required["har_receipt"]),
        "score": float(eval_summary["score"]),
        "success": bool(summary["success"]),
        "artifact_file_count": manifest["file_count"],
        "artifact_total_size_bytes": manifest["total_size_bytes"],
        "llm": _llm_metrics(native),
        "security_scan_executed_on_vps": True,
        "remote_directory_cleanup_performed": False,
        "full_evidence_synced_to_controller": False,
        "secret_values_or_hashes_recorded": False,
    }
    _write_json(root / "remote_slot_acceptance.json", slot)
    return slot


def _verify_manifest(
    root: Path, manifest: Mapping[str, Any], *, verify_files: bool = True
) -> None:
    files = manifest.get("files")
    if not isinstance(files, list) or len(files) != int(manifest.get("file_count", -1)):
        raise RemoteRetentionError("remote artifact manifest inventory is invalid")
    if sha256_object(files) != manifest.get("inventory_sha256"):
        raise RemoteRetentionError("remote artifact manifest inventory hash changed")
    declared_total = sum(
        int(entry.get("size_bytes", -1))
        for entry in files
        if isinstance(entry, Mapping)
    )
    if declared_total != int(manifest.get("total_size_bytes", -1)):
        raise RemoteRetentionError("remote artifact manifest declared size changed")
    if not verify_files:
        return
    total = 0
    for entry in files:
        if not isinstance(entry, Mapping):
            raise RemoteRetentionError("remote artifact manifest entry is invalid")
        relative = str(entry.get("relative_path") or "")
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise RemoteRetentionError("remote artifact manifest path is unsafe")
        path = root / relative_path
        if not path.is_file() or path.is_symlink():
            raise RemoteRetentionError("remote artifact is missing or unsafe")
        if sha256_file(path) != entry.get("sha256") or path.stat().st_size != entry.get("size_bytes"):
            raise RemoteRetentionError("remote artifact hash or size changed")
        total += path.stat().st_size
    if total != int(manifest.get("total_size_bytes", -1)):
        raise RemoteRetentionError("remote artifact total size changed")


def verify_slot(
    *,
    job: Mapping[str, Any],
    adapter_root: str | Path,
    verify_files: bool = True,
) -> dict[str, Any]:
    root = validate_adapter_root(adapter_root, job)
    if not root.exists():
        return {
            "schema_version": VERIFY_SCHEMA,
            "status": "pass",
            "state": "pending",
            "record_slot_id": str(job["record_slot_id"]),
            "job_binding_sha256": sha256_object(dict(job)),
            "persistent_adapter_root": str(root),
            "verified_over_ssh": True,
            "secret_material_recorded": False,
        }
    if not (root / "remote_slot_acceptance.json").is_file():
        result = {
            "schema_version": VERIFY_SCHEMA,
            "status": "pass",
            "state": "in_progress",
            "record_slot_id": str(job["record_slot_id"]),
            "job_binding_sha256": sha256_object(dict(job)),
            "persistent_adapter_root": str(root),
            "verified_over_ssh": True,
            "secret_material_recorded": False,
        }
        # A controller can disappear after the remote worker has already
        # written its bounded public run summary.  Preserve the resumable slot
        # state, but expose a content-free failure observation so the next
        # monitor can add the issue to its immutable ledger instead of calling
        # the slot indefinitely in-progress.
        summary_path = root / "native_run" / "run_summary.json"
        if summary_path.is_file() and not summary_path.is_symlink():
            summary = _load_object(summary_path, "run summary")
            if summary.get("status") == "error":
                diagnostic = " ".join(
                    str(summary.get(key) or "")
                    for key in ("error_type", "error_message")
                )
                result.update(
                    {
                        "terminal_failure_observed": True,
                        "terminal_failure_code": _public_error_code(
                            RuntimeError(diagnostic)
                        ),
                        "run_summary_sha256": sha256_file(summary_path),
                    }
                )
            elif summary.get("status") == "completed":
                # The paid browser/evaluator work is already complete.  A
                # missing seal at this point is post-run reconciliation work,
                # not permission to repeat the paid case during a full sweep.
                result.update(
                    {
                        "runtime_completed_unsealed": True,
                        "run_summary_sha256": sha256_file(summary_path),
                    }
                )
        return result
    slot = _load_object(root / "remote_slot_acceptance.json", "remote slot acceptance")
    manifest_path = root / "remote_artifact_manifest.json"
    security_path = root / "remote_security_acceptance.json"
    evaluator_path = root / "remote_evaluator_receipt.json"
    manifest = _load_object(manifest_path, "remote artifact manifest")
    security = _load_object(security_path, "remote security acceptance")
    evaluator = _load_object(evaluator_path, "remote evaluator receipt")
    binding = sha256_object(dict(job))
    if (
        slot.get("schema_version") != SLOT_SCHEMA
        or manifest.get("schema_version") != MANIFEST_SCHEMA
        or security.get("schema_version") != SECURITY_SCHEMA
        or evaluator.get("schema_version") != EVALUATOR_SCHEMA
        or any(item.get("status") != "pass" for item in (slot, manifest, security, evaluator))
        or any(item.get("job_binding_sha256") != binding for item in (slot, manifest, security, evaluator))
        or slot.get("persistent_adapter_root") != str(root)
        or slot.get("artifact_retention_mode") != RETENTION_MODE
        or slot.get("remote_artifact_manifest_sha256") != sha256_file(manifest_path)
        or slot.get("remote_security_acceptance_sha256") != sha256_file(security_path)
        or slot.get("remote_evaluator_receipt_sha256") != sha256_file(evaluator_path)
        or dict(security.get("scan") or {}).get("finding_count") != 0
        or dict(security.get("scan") or {}).get("gold_finding_count") != 0
    ):
        raise RemoteRetentionError("remote slot receipt binding or security status changed")
    _verify_manifest(root, manifest, verify_files=verify_files)
    return {
        "schema_version": VERIFY_SCHEMA,
        "status": "pass",
        "state": "canonical_reusable",
        "record_slot_id": str(job["record_slot_id"]),
        "job_binding_sha256": binding,
        "server_id": slot.get("server_id"),
        "persistent_adapter_root": str(root),
        "remote_slot_acceptance_sha256": sha256_file(root / "remote_slot_acceptance.json"),
        "remote_artifact_manifest_sha256": sha256_file(manifest_path),
        "remote_security_acceptance_sha256": sha256_file(security_path),
        "remote_evaluator_receipt_sha256": sha256_file(evaluator_path),
        "reset_receipt_sha256": slot.get("reset_receipt_sha256"),
        "run_summary_sha256": slot.get("run_summary_sha256"),
        "network_sanitization_receipt_sha256": slot.get("network_sanitization_receipt_sha256"),
        "score": slot.get("score"),
        "paid_model_call_count": dict(slot.get("llm") or {}).get(
            "complete_record_count"
        ),
        "observed_model_cost_usd": dict(slot.get("llm") or {}).get(
            "observed_cost_usd"
        ),
        "artifact_file_count": manifest.get("file_count"),
        "artifact_total_size_bytes": manifest.get("total_size_bytes"),
        "security_finding_count": 0,
        "gold_finding_count": 0,
        "verified_over_ssh": True,
        "artifact_files_rehashed": verify_files,
        "remote_directory_cleanup_performed": False,
        "full_evidence_synced_to_controller": False,
        "secret_material_recorded": False,
    }


def finalize_namespace(*, namespace_root: str | Path, server_id: str) -> dict[str, Any]:
    raw = Path(namespace_root)
    if not raw.is_absolute():
        raise RemoteRetentionError("namespace root must be absolute")
    root = raw.resolve(strict=False)
    if PERSISTENT_RESULTS_ROOT not in root.parents or root.parent != PERSISTENT_RESULTS_ROOT / "namespaces":
        raise RemoteRetentionError("namespace root escapes persistent storage")
    slots: list[dict[str, Any]] = []
    for path in sorted(root.glob("*/*/*/adapter/remote_slot_acceptance.json")):
        adapter = path.parent
        slot = _load_object(path, "remote slot acceptance")
        manifest = _load_object(adapter / "remote_artifact_manifest.json", "remote artifact manifest")
        security = _load_object(adapter / "remote_security_acceptance.json", "remote security acceptance")
        evaluator = _load_object(adapter / "remote_evaluator_receipt.json", "remote evaluator receipt")
        if (
            slot.get("status") != "pass"
            or slot.get("server_id") != server_id
            or security.get("status") != "pass"
            or evaluator.get("status") != "pass"
            or dict(security.get("scan") or {}).get("finding_count") != 0
            or dict(security.get("scan") or {}).get("gold_finding_count") != 0
            or slot.get("remote_artifact_manifest_sha256") != sha256_file(adapter / "remote_artifact_manifest.json")
        ):
            raise RemoteRetentionError("host namespace contains a failed or mismatched slot")
        _verify_manifest(adapter, manifest)
        slots.append(
            {
                "record_slot_id": slot.get("record_slot_id"),
                "job_binding_sha256": slot.get("job_binding_sha256"),
                "remote_slot_acceptance_sha256": sha256_file(path),
                "remote_artifact_manifest_sha256": sha256_file(adapter / "remote_artifact_manifest.json"),
                "remote_security_acceptance_sha256": sha256_file(adapter / "remote_security_acceptance.json"),
                "remote_evaluator_receipt_sha256": sha256_file(adapter / "remote_evaluator_receipt.json"),
                "artifact_file_count": manifest.get("file_count"),
                "artifact_total_size_bytes": manifest.get("total_size_bytes"),
                "score": slot.get("score"),
            }
        )
    if not slots:
        raise RemoteRetentionError("host namespace has no sealed slots")
    receipt = {
        "schema_version": HOST_SCHEMA,
        "status": "pass",
        "finalized_at": _now(),
        "server_id": server_id,
        "persistent_namespace_root": str(root),
        "slot_count": len(slots),
        "artifact_file_count": sum(int(item["artifact_file_count"]) for item in slots),
        "artifact_total_size_bytes": sum(int(item["artifact_total_size_bytes"]) for item in slots),
        "slots_sha256": sha256_object(slots),
        "slots": slots,
        "security_scan_executed_on_vps": True,
        "security_finding_count": 0,
        "gold_finding_count": 0,
        "remote_directory_cleanup_performed": False,
        "full_evidence_synced_to_controller": False,
        "secret_material_recorded": False,
    }
    _write_json(root / f"host_finalization_{server_id}.json", receipt)
    return receipt


def verify_schedule(
    *, jobs_index: str | Path, server_id: str, verify_files: bool = True
) -> dict[str, Any]:
    """Verify one server lane from a locally synced immutable full index."""

    index_path = Path(jobs_index)
    index = _load_object(index_path, "full jobs index")
    entries = index.get("entries")
    if not isinstance(entries, list) or index.get("job_count") != len(entries):
        raise RemoteRetentionError("full jobs index is incomplete")
    audits: list[dict[str, Any]] = []
    selected_jobs: list[dict[str, Any]] = []
    for position, entry in enumerate(entries):
        if not isinstance(entry, Mapping) or entry.get("position") != position:
            raise RemoteRetentionError("full jobs index position changed")
        relative = str(entry.get("path") or "")
        if Path(relative).name != relative:
            raise RemoteRetentionError("full jobs index has an unsafe path")
        job_path = index_path.parent / relative
        if sha256_file(job_path) != entry.get("sha256"):
            raise RemoteRetentionError("full job file hash changed")
        job = _load_object(job_path, "full job")
        if str(dict(job.get("execution_target") or {}).get("server_id") or "") != server_id:
            continue
        if job.get("artifact_retention_mode") != RETENTION_MODE:
            raise RemoteRetentionError("full job retention policy changed")
        selected_jobs.append(job)
        audits.append(
            verify_slot(
                job=job,
                adapter_root=_expected_adapter_root(job),
                verify_files=verify_files,
            )
        )
    if len(selected_jobs) != 812:
        raise RemoteRetentionError("full server lane does not contain exactly 812 jobs")
    return {
        "schema_version": "webarena_verified_remote_schedule_verification/v1",
        "status": "pass",
        "server_id": server_id,
        "jobs_index_sha256": sha256_file(index_path),
        "lane_jobs_sha256": sha256_object(selected_jobs),
        "slot_count": len(audits),
        "canonical_reusable_count": sum(
            item.get("state") == "canonical_reusable" for item in audits
        ),
        "audits": audits,
        "verified_over_ssh": True,
        "artifact_files_rehashed": verify_files,
        "secret_material_recorded": False,
    }


def _emit(payload: Mapping[str, Any]) -> None:
    encoded = json.dumps(dict(payload), ensure_ascii=True, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > 4_194_304:
        raise RemoteRetentionError("public control envelope exceeds its size bound")
    print(encoded)


def _public_error_code(exc: Exception) -> str:
    """Map internal diagnostics to a content-free control-plane code."""

    message = str(exc).lower()
    categories = (
        ("openrouter http 401", "credential_or_billing_failure"),
        ("openrouter http 402", "credential_or_billing_failure"),
        ("insufficient credit", "credential_or_billing_failure"),
        ("openrouter http 429", "openrouter_rate_limited"),
        ("rate limit", "openrouter_rate_limited"),
        ("response content missing", "openrouter_empty_response"),
        ("auto_login", "official_auto_login_failed"),
        ("auto login", "official_auto_login_failed"),
        ("renewal failed", "official_auto_login_failed"),
        ("'page' object has no attribute 'client'", "playwright_page_client_incompatible"),
        ("evaluator infrastructure", "official_evaluator_infrastructure_failure"),
        ("evaluator error", "official_evaluator_infrastructure_failure"),
        ("playwright trace zip", "playwright_trace_security_scan_failed"),
        ("trace zip", "playwright_trace_security_scan_failed"),
        ("agent input", "agent_input_security_scan_failed"),
        ("runtime security scan", "runtime_security_scan_failed"),
        ("active secret", "active_secret_scan_unavailable"),
        ("llm response", "llm_record_validation_failed"),
        ("har/trace", "network_sanitization_validation_failed"),
        ("evaluator", "official_evaluator_validation_failed"),
        ("reset receipt", "reset_receipt_validation_failed"),
        ("run summary", "run_summary_validation_failed"),
        ("worker job binding", "worker_job_binding_failed"),
        ("native evidence", "native_evidence_incomplete"),
        ("artifact inventory", "artifact_inventory_validation_failed"),
        ("artifact hash", "artifact_hash_validation_failed"),
        ("adapter root", "persistent_path_validation_failed"),
        ("namespace root", "persistent_namespace_validation_failed"),
    )
    for marker, code in categories:
        if marker in message:
            return code
    return "remote_retention_validation_failed"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--job-json", required=True)
    prepare.add_argument("--adapter-root", required=True)
    seal = sub.add_parser("seal")
    seal.add_argument("--job-json", required=True)
    seal.add_argument("--adapter-root", required=True)
    seal.add_argument("--active-secret-env", required=True)
    seal.add_argument("--agent-input-path", required=True)
    seal.add_argument("--quiet", action="store_true")
    verify = sub.add_parser("verify")
    verify.add_argument("--job-json", required=True)
    verify.add_argument("--adapter-root", required=True)
    finalize = sub.add_parser("finalize-namespace")
    finalize.add_argument("--namespace-root", required=True)
    finalize.add_argument("--server-id", required=True)
    schedule = sub.add_parser("verify-schedule")
    schedule.add_argument("--jobs-index", required=True)
    schedule.add_argument("--server-id", required=True)
    schedule.add_argument("--receipt-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare_slot(
                job=_parse_job(args.job_json), adapter_root=args.adapter_root
            )
        elif args.command == "seal":
            result = seal_slot(
                job=_parse_job(args.job_json),
                adapter_root=args.adapter_root,
                active_secret_env=args.active_secret_env,
                agent_input_path=args.agent_input_path,
            )
        elif args.command == "verify":
            result = verify_slot(
                job=_parse_job(args.job_json), adapter_root=args.adapter_root
            )
        elif args.command == "finalize-namespace":
            result = finalize_namespace(
                namespace_root=args.namespace_root, server_id=args.server_id
            )
        else:
            result = verify_schedule(
                jobs_index=args.jobs_index,
                server_id=args.server_id,
                verify_files=not args.receipt_only,
            )
        if not (args.command == "seal" and args.quiet):
            _emit(result)
        return 0
    except Exception as exc:
        error = {
            "schema_version": "webarena_verified_remote_retention_error/v1",
            "status": "blocked",
            "error_type": type(exc).__name__,
            "error_code": _public_error_code(exc),
            "secret_material_recorded": False,
        }
        print(json.dumps(error, separators=(",", ":")), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
