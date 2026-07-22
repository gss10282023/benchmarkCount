"""Real, recovery-first three-host fault executor for WebArena-Verified.

Importing this module is inert.  Remote mutation is available only through the
explicitly armed CLI in :mod:`evidence_system.cli.webarena_fault_injection_remote`.
The executor never loads a dotenv file and has no parameter for a real model
credential.  Its sole provider probe uses a compile-time, known-invalid
placeholder against OpenRouter's non-billable key-auth endpoint.

Each fault is a transaction:

* observe a healthy baseline where applicable;
* inject one bounded fault while using the SSH ED25519 fingerprint frozen in
  ``configs/infra.yaml``;
* prove the locked pre-model / evaluator fail-closed boundary;
* recover before publishing a receipt;
* write two mode-0600 controller-only evidence files and a secret-free public
  receipt.

No passing receipt is produced unless recovery succeeds.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from typing import Any

from evidence_system.adapters import webarena_verified_official_scorer as scorer
from evidence_system.contracts.common import load_mapping
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.orchestrator.jobs import InfraBenchmarkTarget, resolve_infra_target
from evidence_system.webarena_fault_injection import (
    FAULT_KINDS,
    build_fault_acceptance,
    build_fault_receipt,
    classify_fault_observation,
    classify_recovery_observation,
    scan_sensitive_material,
    write_fault_acceptance,
    write_fault_receipt,
)
from evidence_system.webarena_sites import (
    SlotIdentity,
    WebArenaSiteController,
    atomic_write_json,
    load_site_lock,
    run_verified_ssh_argv,
)


REMOTE_RAW_EVIDENCE_SCHEMA = "webarena_verified_fault_raw_evidence/v1"
REMOTE_FAILURE_SCHEMA = "webarena_verified_fault_execution_failure/v1"
REMOTE_PLAN_SCHEMA = "webarena_verified_fault_remote_plan/v1"
REMOTE_EXECUTION_CONFIRMATION = (
    "EXECUTE_WEBARENA_VERIFIED_3X4_FAULTS_WITH_NO_PAID_MODEL"
)
EXPECTED_AGENT_BINDINGS = {
    "webarena-gpt54-ord": "Agent A",
    "webarena-claude47-ord": "Agent B",
    "webarena-deepseek-v4pro-ord": "Agent C",
}
SITE_FAULT_SITE = "shopping"
SITE_FAULT_TASK_ID = 21
SITE_FAULT_SEED = 123021
OPENROUTER_AUTH_URL = "https://openrouter.ai/api/v1/key"
OPENROUTER_AUTH_DOC_URL = (
    "https://openrouter.ai/docs/api/api-reference/api-keys/get-current-key"
)

# This value is deliberately not key-shaped and is not configurable.  It can
# never select or bill a model.  The value itself is never written to evidence.
_INVALID_PLACEHOLDER = "evidence-system-known-invalid-auth-probe-v1"
INVALID_PLACEHOLDER_SHA256 = hashlib.sha256(
    _INVALID_PLACEHOLDER.encode("utf-8")
).hexdigest()

REMOTE_GOLDEN_ADAPTER_ROOT = (
    "/opt/webarena-verified/v1.2.3/evidence/golden-parity-v1/"
    "controller_only/response_only_success/adapter"
)
REMOTE_RUNTIME_CONFIG = (
    "/opt/webarena-verified/v1.2.3/runtime/webarena_verified_runtime_urls.json"
)
REMOTE_TASK_CONTRACT_INDEX = (
    "/opt/webarena-verified/v1.2.3/runtime/"
    "webarena_verified_task_contract_index.json"
)
REMOTE_CONTROLLER_ROOT = "/opt/webarena-controller/current"

RemoteRunner = Callable[[Sequence[str], int], subprocess.CompletedProcess[str]]


class RemoteFaultExecutionError(RuntimeError):
    """A remote fault was not observed or could not be safely recovered."""


@dataclass(frozen=True)
class RemoteFaultBinding:
    target: InfraBenchmarkTarget
    agent_id: str
    ssh_host_fingerprint: str


@dataclass(frozen=True)
class RemoteMatrixResult:
    acceptance: dict[str, Any]
    acceptance_path: Path
    receipt_paths: tuple[Path, ...]
    failures: tuple[dict[str, str], ...]


def load_remote_fault_bindings(
    infra_config_path: str | Path,
) -> tuple[RemoteFaultBinding, RemoteFaultBinding, RemoteFaultBinding]:
    """Resolve the exact three enabled one-agent VPS routes from the infra lock."""

    infra = load_mapping(infra_config_path)
    raw_machines = [
        dict(machine)
        for machine in list(infra.get("machines") or [])
        if isinstance(machine, Mapping) and machine.get("role") == "webarena_vps"
    ]
    if len(raw_machines) != 3:
        raise RemoteFaultExecutionError(
            "infra must define exactly three WebArena VPS machines"
        )
    observed_ids = [str(machine.get("machine_id") or "") for machine in raw_machines]
    if observed_ids != list(EXPECTED_AGENT_BINDINGS):
        raise RemoteFaultExecutionError(
            "WebArena VPS machine order or identity differs from the frozen route"
        )

    bindings: list[RemoteFaultBinding] = []
    for raw_machine in raw_machines:
        machine_id = str(raw_machine["machine_id"])
        agent_id = str(raw_machine.get("assigned_agent_id") or "")
        if agent_id != EXPECTED_AGENT_BINDINGS[machine_id]:
            raise RemoteFaultExecutionError(
                f"{machine_id} agent assignment differs from the frozen route"
            )
        if raw_machine.get("enabled") is not True or raw_machine.get("concurrency") != 1:
            raise RemoteFaultExecutionError(
                f"{machine_id} must be enabled with concurrency exactly one"
            )
        benchmark_config = dict(
            dict(raw_machine.get("benchmarks") or {}).get("WebArena-Verified") or {}
        )
        controller_config = dict(benchmark_config.get("site_controller") or {})
        fingerprint = str(controller_config.get("ssh_host_fingerprint") or "")
        if re.fullmatch(r"SHA256:[A-Za-z0-9+/=]+", fingerprint) is None:
            raise RemoteFaultExecutionError(
                f"{machine_id} has no locked SSH ED25519 fingerprint"
            )
        scoped = dict(infra)
        scoped["machines"] = [raw_machine]
        target = resolve_infra_target("webarena_verified", scoped)
        target_fingerprint = str(
            dict(target.benchmark_config.get("site_controller") or {}).get(
                "ssh_host_fingerprint"
            )
            or ""
        )
        if target.machine_id != machine_id or target_fingerprint != fingerprint:
            raise RemoteFaultExecutionError(
                f"{machine_id} target resolution changed its SSH identity"
            )
        if target.benchmark_config.get("sync_dotenv") is not False:
            raise RemoteFaultExecutionError(
                f"{machine_id} must explicitly disable dotenv synchronization"
            )
        bindings.append(RemoteFaultBinding(target, agent_id, fingerprint))
    return tuple(bindings)  # type: ignore[return-value]


def build_remote_fault_plan(
    *,
    infra_config_path: str | Path,
    receipts_root: str | Path,
) -> dict[str, Any]:
    """Build a read-only exact-12 plan without opening an SSH connection."""

    bindings = load_remote_fault_bindings(infra_config_path)
    root = Path(receipts_root)
    rows = [
        {
            "ordinal": ordinal,
            "machine_id": binding.target.machine_id,
            "agent_id": binding.agent_id,
            "fault_kind": kind,
            "ssh_host_ed25519_fingerprint": binding.ssh_host_fingerprint,
            "receipt_path": str(
                root / binding.target.machine_id / kind / "receipt.json"
            ),
            "fault_evidence_path": str(
                root
                / "private"
                / binding.target.machine_id
                / kind
                / "fault_observation.json"
            ),
            "recovery_evidence_path": str(
                root
                / "private"
                / binding.target.machine_id
                / kind
                / "recovery_observation.json"
            ),
        }
        for ordinal, (binding, kind) in enumerate(
            (
                (binding, kind)
                for binding in bindings
                for kind in FAULT_KINDS
            ),
            start=1,
        )
    ]
    plan: dict[str, Any] = {
        "schema_version": REMOTE_PLAN_SCHEMA,
        "status": "planned",
        "remote_execution_performed": False,
        "benchmark": "WebArena-Verified",
        "benchmark_version": "v1.2.3",
        "machine_count": 3,
        "fault_count_per_machine": 4,
        "receipt_count": 12,
        "paid_model_calls_planned": 0,
        "provider_probe_endpoint_kind": "non_billable_key_auth",
        "provider_probe_spec_source": OPENROUTER_AUTH_DOC_URL,
        "invalid_placeholder_sha256": INVALID_PLACEHOLDER_SHA256,
        "real_credential_input_supported": False,
        "dotenv_loading_supported": False,
        "scheduler_quiescence_required": True,
        "concurrent_pilot_or_full_run_allowed": False,
        "infra_config_sha256": sha256_file(infra_config_path),
        "executor_source_sha256": sha256_file(Path(__file__).resolve()),
        "official_scorer_source_sha256": sha256_file(Path(scorer.__file__).resolve()),
        "official_evaluator_image": scorer.OFFICIAL_IMAGE,
        "rows": rows,
        "rows_sha256": sha256_object(rows),
    }
    plan["integrity"] = {
        "algorithm": "sha256_canonical_json",
        "core_sha256": sha256_object(plan),
    }
    return plan


def write_remote_fault_plan(path: str | Path, payload: Mapping[str, Any]) -> None:
    plan = dict(payload)
    integrity = plan.pop("integrity", None)
    if (
        plan.get("schema_version") != REMOTE_PLAN_SCHEMA
        or plan.get("remote_execution_performed") is not False
        or plan.get("receipt_count") != 12
        or plan.get("paid_model_calls_planned") != 0
        or not isinstance(integrity, Mapping)
        or integrity.get("core_sha256") != sha256_object(plan)
    ):
        raise RemoteFaultExecutionError("remote fault plan failed its integrity gate")
    atomic_write_json(path, payload)


class RemoteFaultExecutor:
    """Execute four recovery-first faults on one fingerprint-bound host."""

    def __init__(
        self,
        *,
        binding: RemoteFaultBinding,
        site_lock: Mapping[str, Any],
        receipts_root: str | Path,
        runner: RemoteRunner | None = None,
        controller: WebArenaSiteController | None = None,
    ) -> None:
        self.binding = binding
        self.site_lock = dict(site_lock)
        self.receipts_root = Path(receipts_root)
        self.runner = runner or self._verified_remote
        self.controller = controller or WebArenaSiteController(
            site_lock=self.site_lock,
            run_remote=self.runner,
            machine_id=binding.target.machine_id,
            ssh_host=binding.target.ssh_host,
            ssh_host_fingerprint=binding.ssh_host_fingerprint,
        )
        self._provider_env_probe: dict[str, Any] | None = None

    @property
    def machine_id(self) -> str:
        return self.binding.target.machine_id

    def run_fault(self, kind: str) -> Path:
        receipt_path = self._receipt_path(kind)
        if receipt_path.exists():
            raise RemoteFaultExecutionError(
                f"refusing to overwrite existing fault receipt: {receipt_path}"
            )
        self._assert_provider_environment_absent()
        if kind == "site_outage":
            observation, recovery = self._site_outage()
        elif kind == "login_failure":
            observation, recovery = self._login_failure()
        elif kind == "invalid_placeholder_api_key":
            observation, recovery = self._invalid_placeholder_api_key()
        elif kind == "evaluator_error":
            observation, recovery = self._evaluator_error()
        else:
            raise RemoteFaultExecutionError(f"unsupported fault kind: {kind!r}")
        return self._publish(kind, observation=observation, recovery=recovery)

    def _verified_remote(
        self, argv: Sequence[str], timeout: int
    ) -> subprocess.CompletedProcess[str]:
        target = self.binding.target
        return run_verified_ssh_argv(
            host=target.ssh_host,
            user=target.ssh_user,
            port=target.ssh_port,
            key_path=target.ssh_key_path,
            expected_ed25519_fingerprint=self.binding.ssh_host_fingerprint,
            argv=argv,
            timeout=timeout,
        )

    def _site_outage(self) -> tuple[dict[str, Any], dict[str, Any]]:
        site = SITE_FAULT_SITE
        container_name = str(self.site_lock["sites"][site]["container_name"])
        baseline = self.controller.status([site])
        _require_status_identity(baseline, machine_id=self.machine_id, status="pass")
        baseline_row = _one_site_row(baseline, site=site)
        before_id = str(dict(baseline_row.get("container") or {}).get("container_id") or "")
        if not before_id:
            raise RemoteFaultExecutionError("site baseline has no container identity")
        token: str | None = None
        stop_result: subprocess.CompletedProcess[str] | None = None
        outage: dict[str, Any] | None = None
        workers_after: int | None = None
        workers_before: int | None = None
        injection_error: Exception | None = None
        lock_released = False
        try:
            token = self.controller._acquire_exclusive_lock(  # noqa: SLF001
                owner={
                    "operation": "fault_injection",
                    "fault_kind": "site_outage",
                    "machine_id": self.machine_id,
                }
            )
            workers_before = self._worker_process_count()
            stop_result = self.runner(
                ["docker", "stop", "--time", "10", container_name], 60
            )
            if stop_result.returncode != 0:
                raise RemoteFaultExecutionError("injected docker stop did not succeed")
            outage = self.controller.status([site])
            _require_status_identity(outage, machine_id=self.machine_id, status="fail")
            if _one_site_row(outage, site=site).get("ok") is not False:
                raise RemoteFaultExecutionError("stopped site did not fail its sentinel gate")
            workers_after = self._worker_process_count()
        except Exception as exc:  # Recovery is mandatory even after observation failure.
            injection_error = exc
        finally:
            if token is not None:
                try:
                    self.controller._release_exclusive_lock(token)  # noqa: SLF001
                    lock_released = True
                except Exception as exc:
                    if injection_error is None:
                        injection_error = exc

        reset_path = self._private_dir("site_outage") / "slot_reset_receipt.json"
        reset_receipt: dict[str, Any] | None = None
        recovery_status: dict[str, Any] | None = None
        recovery_error: Exception | None = None
        try:
            reset_receipt = self.controller.reset_slot(
                identity=SlotIdentity(
                    slot_id=f"wv123-fi-{self.machine_id}-site-outage",
                    task_id=SITE_FAULT_TASK_ID,
                    agent_id=self.binding.agent_id,
                    attempt_id="fault-injection-001",
                    seed=SITE_FAULT_SEED,
                ),
                sites=[site],
                receipt_path=reset_path,
            )
            recovery_status = self.controller.status([site])
            _require_status_identity(
                recovery_status, machine_id=self.machine_id, status="pass"
            )
        except Exception as exc:
            recovery_error = exc
        if recovery_error is not None:
            raise RemoteFaultExecutionError(
                "site-outage recovery failed; no passing receipt was published"
            ) from recovery_error
        if injection_error is not None:
            raise RemoteFaultExecutionError(
                "site-outage observation failed after successful recovery"
            ) from injection_error
        assert stop_result is not None
        assert outage is not None
        assert workers_after is not None
        assert workers_before is not None
        assert reset_receipt is not None
        assert recovery_status is not None
        after_row = _one_site_row(recovery_status, site=site)
        after_id = str(dict(after_row.get("container") or {}).get("container_id") or "")
        reset_row = _one_reset_row(reset_receipt, site=site)
        reset_after_id = str(dict(reset_row.get("after") or {}).get("container_id") or "")
        if not after_id or after_id == before_id or reset_after_id != after_id:
            raise RemoteFaultExecutionError(
                "slot reset did not restore the site with a fresh container"
            )
        facts = {
            "probe_kind": "site_status",
            "site_container_stopped": True,
            "sentinel_passed": False,
            "model_worker_started": workers_before != 0 or workers_after != 0,
        }
        recovery_facts = {
            "site_recreated_from_pins": reset_receipt.get("status") == "pass",
            "all_sentinels_passed": recovery_status.get("status") == "pass",
        }
        classify_fault_observation("site_outage", facts)
        classify_recovery_observation("site_outage", recovery_facts)
        observation = self._raw_payload(
            kind="site_outage",
            phase="fault_observation",
            facts=facts,
            measurements={
                "site": site,
                "baseline_status": baseline["status"],
                "baseline_payload_sha256": sha256_object(baseline),
                "baseline_container_id_sha256": _sha256_text(before_id),
                "outage_status": outage["status"],
                "outage_payload_sha256": sha256_object(outage),
                "stop_command": _command_metadata(stop_result),
                "worker_process_count_before": workers_before,
                "worker_process_count_after": workers_after,
                "exclusive_lock_released": lock_released,
            },
        )
        recovery = self._raw_payload(
            kind="site_outage",
            phase="recovery_observation",
            facts=recovery_facts,
            measurements={
                "recovery_method": "slot_reset",
                "slot_reset_receipt": reset_receipt,
                "post_reset_status": recovery_status,
                "before_container_id_sha256": _sha256_text(before_id),
                "after_container_id_sha256": _sha256_text(after_id),
            },
        )
        return observation, recovery

    def _login_failure(self) -> tuple[dict[str, Any], dict[str, Any]]:
        workers_before = self._worker_process_count()
        runner_root = str(self.site_lock["runner_root"])
        runner_python = f"{runner_root}/.venv/bin/python"
        result, remote = self._run_json(
            ["python3", "-c", _LOGIN_FAILURE_SCRIPT, runner_root, runner_python],
            timeout=180,
            label="login-failure",
        )
        workers_after = self._worker_process_count()
        expected_keys = {
            "probe_kind",
            "wrong_target_kind",
            "auto_login_exit_nonzero",
            "auto_login_returncode",
            "storage_state_created",
            "state_file_count",
            "auth_folder_removed",
            "stdout_sha256",
            "stderr_sha256",
            "stdout_bytes",
            "stderr_bytes",
        }
        if set(remote) != expected_keys:
            raise RemoteFaultExecutionError("login probe returned an unsafe schema")
        if remote.get("wrong_target_kind") != "closed_loopback_port":
            raise RemoteFaultExecutionError("login failure did not use the locked bad target")
        if remote.get("auth_folder_removed") is not True:
            raise RemoteFaultExecutionError("failed login retained its auth folder")
        facts = {
            "probe_kind": remote.get("probe_kind"),
            "auto_login_exit_nonzero": remote.get("auto_login_exit_nonzero"),
            "storage_state_created": remote.get("storage_state_created"),
            "model_worker_started": workers_before != 0 or workers_after != 0,
        }
        classify_fault_observation("login_failure", facts)

        login = self.controller.verify_login()
        if login.get("status") != "pass" or login.get("sensitive_state_retained") is not False:
            raise RemoteFaultExecutionError("normal official login recovery did not pass")
        recovery_facts = {
            "fresh_state_regenerated": int(login.get("generated_state_file_count") or 0)
            >= 5,
            "fresh_state_validated": int(login.get("validated_cookie_count") or 0) > 0,
            "sensitive_state_deleted": login.get("sensitive_state_retained") is False,
        }
        classify_recovery_observation("login_failure", recovery_facts)
        observation = self._raw_payload(
            kind="login_failure",
            phase="fault_observation",
            facts=facts,
            measurements={
                "remote_probe": remote,
                "remote_command": _command_metadata(result),
                "worker_process_count_before": workers_before,
                "worker_process_count_after": workers_after,
            },
        )
        recovery = self._raw_payload(
            kind="login_failure",
            phase="recovery_observation",
            facts=recovery_facts,
            measurements={"official_login_receipt": login},
        )
        return observation, recovery

    def _invalid_placeholder_api_key(
        self,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        result, remote = self._run_json(
            ["python3", "-c", _INVALID_API_SCRIPT],
            timeout=60,
            label="invalid-placeholder-api-key",
        )
        expected_keys = {
            "probe_kind",
            "endpoint_kind",
            "worker_exit_nonzero",
            "child_returncode",
            "provider_http_status",
            "model_completion_received",
            "credential_scope",
            "response_body_sha256",
            "response_body_bytes",
            "parent_key_present_before",
            "parent_key_present_after",
            "placeholder_child_destroyed",
            "parent_environment_unchanged",
        }
        if set(remote) != expected_keys:
            raise RemoteFaultExecutionError("invalid-key probe returned an unsafe schema")
        if remote.get("endpoint_kind") != "non_billable_key_auth":
            raise RemoteFaultExecutionError("invalid-key probe attempted a billable endpoint")
        if remote.get("parent_key_present_before") is not False or remote.get(
            "parent_key_present_after"
        ) is not False:
            raise RemoteFaultExecutionError(
                "remote parent environment unexpectedly contains a provider key"
            )
        facts = {
            "probe_kind": remote.get("probe_kind"),
            "worker_exit_nonzero": remote.get("worker_exit_nonzero"),
            "provider_http_status": remote.get("provider_http_status"),
            "model_completion_received": remote.get("model_completion_received"),
            "credential_scope": remote.get("credential_scope"),
        }
        recovery_facts = {
            "placeholder_child_destroyed": remote.get("placeholder_child_destroyed"),
            "parent_environment_unchanged": remote.get(
                "parent_environment_unchanged"
            ),
        }
        classify_fault_observation("invalid_placeholder_api_key", facts)
        classify_recovery_observation(
            "invalid_placeholder_api_key", recovery_facts
        )
        observation = self._raw_payload(
            kind="invalid_placeholder_api_key",
            phase="fault_observation",
            facts=facts,
            measurements={
                "remote_probe": remote,
                "remote_command": _command_metadata(result),
                "invalid_placeholder_sha256": INVALID_PLACEHOLDER_SHA256,
                "paid_model_endpoint_invocations": 0,
            },
        )
        recovery = self._raw_payload(
            kind="invalid_placeholder_api_key",
            phase="recovery_observation",
            facts=recovery_facts,
            measurements={
                "child_process_exit_observed": True,
                "provider_environment_value_read": False,
            },
        )
        return observation, recovery

    def _evaluator_error(self) -> tuple[dict[str, Any], dict[str, Any]]:
        controller_python = str(self.site_lock["official_runtime_python"])
        result, remote = self._run_json(
            [
                "python3",
                "-c",
                _EVALUATOR_ERROR_SCRIPT,
                REMOTE_CONTROLLER_ROOT,
                controller_python,
                REMOTE_GOLDEN_ADAPTER_ROOT,
                REMOTE_RUNTIME_CONFIG,
                REMOTE_TASK_CONTRACT_INDEX,
            ],
            timeout=900,
            label="evaluator-error",
        )
        expected_keys = {
            "probe_kind",
            "scorer_exit_code",
            "scorer_status",
            "official_evaluation_completed",
            "integrity_verified",
            "mutated_input_is_copy",
            "fault_stdout_sha256",
            "fault_stderr_sha256",
            "golden_recovery_exit_code",
            "golden_recovery_scorer_status",
            "golden_recovery_official_evaluation_completed",
            "golden_recovery_integrity_verified",
            "recovery_stdout_sha256",
            "recovery_stderr_sha256",
            "baseline_hash_before",
            "baseline_hash_after",
            "baseline_artifact_hash_unchanged",
            "corrupt_copy_quarantined",
            "temporary_workspace_deleted",
            "remote_scorer_source_sha256",
        }
        if set(remote) != expected_keys:
            raise RemoteFaultExecutionError("evaluator probe returned an unsafe schema")
        local_scorer_sha = sha256_file(Path(scorer.__file__).resolve())
        if remote.get("remote_scorer_source_sha256") != local_scorer_sha:
            raise RemoteFaultExecutionError(
                "remote official scorer adapter source differs from the controller"
            )
        facts = {
            "probe_kind": remote.get("probe_kind"),
            "scorer_exit_code": remote.get("scorer_exit_code"),
            "scorer_status": remote.get("scorer_status"),
            "official_evaluation_completed": remote.get(
                "official_evaluation_completed"
            ),
            "integrity_verified": remote.get("integrity_verified"),
            "mutated_input_is_copy": remote.get("mutated_input_is_copy"),
        }
        recovery_facts = {
            "corrupt_copy_quarantined": remote.get("corrupt_copy_quarantined"),
            "baseline_artifact_hash_unchanged": remote.get(
                "baseline_artifact_hash_unchanged"
            ),
        }
        classify_fault_observation("evaluator_error", facts)
        classify_recovery_observation("evaluator_error", recovery_facts)
        if (
            remote.get("golden_recovery_exit_code") != 0
            or remote.get("golden_recovery_scorer_status") != "success"
            or remote.get("golden_recovery_official_evaluation_completed") is not True
            or remote.get("golden_recovery_integrity_verified") is not True
            or remote.get("temporary_workspace_deleted") is not True
        ):
            raise RemoteFaultExecutionError("golden evaluator recovery did not pass")
        observation = self._raw_payload(
            kind="evaluator_error",
            phase="fault_observation",
            facts=facts,
            measurements={
                "remote_probe": {
                    key: value
                    for key, value in remote.items()
                    if not key.startswith("golden_recovery_")
                    and not key.startswith("recovery_")
                },
                "remote_command": _command_metadata(result),
                "official_image": scorer.OFFICIAL_IMAGE,
            },
        )
        recovery = self._raw_payload(
            kind="evaluator_error",
            phase="recovery_observation",
            facts=recovery_facts,
            measurements={
                "golden_recovery_exit_code": remote["golden_recovery_exit_code"],
                "golden_recovery_scorer_status": remote[
                    "golden_recovery_scorer_status"
                ],
                "golden_recovery_official_evaluation_completed": remote[
                    "golden_recovery_official_evaluation_completed"
                ],
                "golden_recovery_integrity_verified": remote[
                    "golden_recovery_integrity_verified"
                ],
                "recovery_stdout_sha256": remote["recovery_stdout_sha256"],
                "recovery_stderr_sha256": remote["recovery_stderr_sha256"],
                "baseline_hash_before": remote["baseline_hash_before"],
                "baseline_hash_after": remote["baseline_hash_after"],
                "temporary_workspace_deleted": remote[
                    "temporary_workspace_deleted"
                ],
            },
        )
        return observation, recovery

    def _worker_process_count(self) -> int:
        _, payload = self._run_json(
            ["python3", "-c", _WORKER_COUNT_SCRIPT],
            timeout=30,
            label="worker-process-count",
        )
        if set(payload) != {"worker_process_count"}:
            raise RemoteFaultExecutionError("worker-count probe schema mismatch")
        count = payload.get("worker_process_count")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise RemoteFaultExecutionError("worker-count probe value is invalid")
        return count

    def _assert_provider_environment_absent(self) -> None:
        result, payload = self._run_json(
            ["python3", "-c", _PROVIDER_ENV_ABSENCE_SCRIPT],
            timeout=30,
            label="provider-environment-absence",
        )
        if payload != {"provider_key_present": False}:
            raise RemoteFaultExecutionError(
                "remote process environment contains a provider key; refusing fault test"
            )
        self._provider_env_probe = _command_metadata(result)

    def _run_json(
        self,
        argv: Sequence[str],
        *,
        timeout: int,
        label: str,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        result = self.runner(argv, timeout)
        if result.returncode != 0:
            raise RemoteFaultExecutionError(
                f"{label} wrapper failed before producing a measured receipt"
            )
        try:
            payload = json.loads(result.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError) as exc:
            raise RemoteFaultExecutionError(
                f"{label} wrapper returned invalid JSON"
            ) from exc
        if not isinstance(payload, dict):
            raise RemoteFaultExecutionError(f"{label} wrapper returned a non-object")
        if scan_sensitive_material(payload):
            raise RemoteFaultExecutionError(
                f"{label} wrapper output contains prohibited sensitive material"
            )
        return result, payload

    def _raw_payload(
        self,
        *,
        kind: str,
        phase: str,
        facts: Mapping[str, Any],
        measurements: Mapping[str, Any],
    ) -> dict[str, Any]:
        if self._provider_env_probe is None:
            raise RemoteFaultExecutionError(
                "provider environment absence was not verified before remote execution"
            )
        payload = {
            "schema_version": REMOTE_RAW_EVIDENCE_SCHEMA,
            "benchmark": "WebArena-Verified",
            "benchmark_version": "v1.2.3",
            "execution_mode": "remote_real",
            "machine_id": self.machine_id,
            "agent_id": self.binding.agent_id,
            "fault_kind": kind,
            "phase": phase,
            "measured_at": _utc_now_iso(),
            "ssh_host_ed25519_fingerprint": self.binding.ssh_host_fingerprint,
            "executor_source_sha256": sha256_file(Path(__file__).resolve()),
            "site_lock_core_sha256": sha256_object(self.site_lock),
            "facts": dict(facts),
            "measurements": dict(measurements),
            "raw_stdout_or_stderr_persisted": False,
            "provider_environment_absence_verified": True,
            "provider_environment_probe": dict(self._provider_env_probe),
            "real_credential_loaded": False,
            "paid_model_calls": 0,
        }
        if scan_sensitive_material(payload):
            raise RemoteFaultExecutionError(
                "controller evidence normalization retained sensitive material"
            )
        payload["integrity"] = {
            "algorithm": "sha256_canonical_json",
            "core_sha256": sha256_object(payload),
        }
        return payload

    def _publish(
        self,
        kind: str,
        *,
        observation: Mapping[str, Any],
        recovery: Mapping[str, Any],
    ) -> Path:
        observation_facts = dict(observation.get("facts") or {})
        recovery_facts = dict(recovery.get("facts") or {})
        observed_semantics = classify_fault_observation(kind, observation_facts)
        recovery_semantics = classify_recovery_observation(kind, recovery_facts)
        private_dir = self._private_dir(kind)
        observation_path = private_dir / "fault_observation.json"
        recovery_path = private_dir / "recovery_observation.json"
        atomic_write_json(observation_path, observation)
        atomic_write_json(recovery_path, recovery)
        _assert_private_file(observation_path)
        _assert_private_file(recovery_path)
        evidence = [
            {
                "artifact_kind": "fault_observation",
                "sha256": sha256_file(observation_path),
                "controller_only": True,
                "relative_reference": observation_path.relative_to(
                    self.receipts_root
                ).as_posix(),
            },
            {
                "artifact_kind": "recovery_observation",
                "sha256": sha256_file(recovery_path),
                "controller_only": True,
                "relative_reference": recovery_path.relative_to(
                    self.receipts_root
                ).as_posix(),
            },
        ]
        completed_at = max(
            str(observation["measured_at"]), str(recovery["measured_at"])
        )
        receipt = build_fault_receipt(
            machine_id=self.machine_id,
            kind=kind,
            execution_mode="remote_real",
            observed_semantics=observed_semantics,
            recovery=recovery_semantics,
            remote_attestation={
                "ssh_host_ed25519_fingerprint": self.binding.ssh_host_fingerprint,
                "verified_ssh_host_key": True,
                "controller_machine_id_match": True,
                "remote_command_executed": True,
            },
            evidence=evidence,
            completed_at=completed_at,
            real_dotenv_read=False,
            real_secret_loaded=False,
            paid_model_calls=0,
        )
        receipt_path = self._receipt_path(kind)
        write_fault_receipt(receipt_path, receipt)
        return receipt_path

    def _private_dir(self, kind: str) -> Path:
        private_root = self.receipts_root / "private"
        machine_root = private_root / self.machine_id
        destination = machine_root / kind
        for path in (private_root, machine_root, destination):
            path.mkdir(parents=True, exist_ok=True)
            os.chmod(path, 0o700)
        return destination

    def _receipt_path(self, kind: str) -> Path:
        return self.receipts_root / self.machine_id / kind / "receipt.json"


def execute_remote_fault_matrix(
    *,
    infra_config_path: str | Path,
    site_lock_path: str | Path,
    receipts_root: str | Path,
    acceptance_output: str | Path,
    confirmation: str,
    runner_factory: Callable[[RemoteFaultBinding], RemoteRunner] | None = None,
    controller_factory: Callable[
        [RemoteFaultBinding, Mapping[str, Any], RemoteRunner], WebArenaSiteController
    ]
    | None = None,
) -> RemoteMatrixResult:
    """Execute exact 3×4 faults; the confirmation is intentionally non-default."""

    if confirmation != REMOTE_EXECUTION_CONFIRMATION:
        raise RemoteFaultExecutionError("remote fault execution is not explicitly armed")
    bindings = load_remote_fault_bindings(infra_config_path)
    site_lock = load_site_lock(site_lock_path)
    root = Path(receipts_root)
    acceptance_path = Path(acceptance_output)
    if acceptance_path.exists() or any(root.rglob("receipt.json")):
        raise RemoteFaultExecutionError(
            "refusing to overwrite an existing fault matrix or acceptance"
        )
    for binding in bindings:
        if runner_factory is None and not Path(binding.target.ssh_key_path).is_file():
            raise RemoteFaultExecutionError(
                f"SSH private key is missing for {binding.target.machine_id}"
            )

    receipt_paths: list[Path] = []
    failures: list[dict[str, str]] = []

    def run_host(binding: RemoteFaultBinding) -> tuple[list[Path], list[dict[str, str]]]:
        runner = (
            runner_factory(binding)
            if runner_factory is not None
            else _binding_runner(binding)
        )
        controller = (
            controller_factory(binding, site_lock, runner)
            if controller_factory is not None
            else WebArenaSiteController(
                site_lock=site_lock,
                run_remote=runner,
                machine_id=binding.target.machine_id,
                ssh_host=binding.target.ssh_host,
                ssh_host_fingerprint=binding.ssh_host_fingerprint,
            )
        )
        executor = RemoteFaultExecutor(
            binding=binding,
            site_lock=site_lock,
            receipts_root=root,
            runner=runner,
            controller=controller,
        )
        host_receipts: list[Path] = []
        host_failures: list[dict[str, str]] = []
        for kind in FAULT_KINDS:
            try:
                host_receipts.append(executor.run_fault(kind))
            except Exception as exc:
                failure = {
                    "machine_id": binding.target.machine_id,
                    "fault_kind": kind,
                    "error_type": type(exc).__name__,
                }
                host_failures.append(failure)
                failure_path = (
                    executor._private_dir(kind) / "execution_failure.json"  # noqa: SLF001
                )
                failure_payload = {
                    "schema_version": REMOTE_FAILURE_SCHEMA,
                    **failure,
                    "failed_at": _utc_now_iso(),
                    "exception_message_persisted": False,
                    "real_credential_loaded": False,
                    "paid_model_calls": 0,
                }
                atomic_write_json(failure_path, failure_payload)
                # A fault whose recovery cannot be proved may have changed site
                # state.  Stop this host lane; the missing receipts make the
                # aggregate fail closed.
                break
        return host_receipts, host_failures

    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="wv-fault") as pool:
        futures = {pool.submit(run_host, binding): binding for binding in bindings}
        for future in as_completed(futures):
            host_receipts, host_failures = future.result()
            receipt_paths.extend(host_receipts)
            failures.extend(host_failures)

    fingerprints = {
        binding.target.machine_id: binding.ssh_host_fingerprint for binding in bindings
    }
    acceptance = build_fault_acceptance(
        receipts_root=root,
        scope="remote_three_host",
        machine_ids=tuple(binding.target.machine_id for binding in bindings),
        ssh_host_fingerprints=fingerprints,
    )
    write_fault_acceptance(acceptance_path, acceptance)
    return RemoteMatrixResult(
        acceptance=acceptance,
        acceptance_path=acceptance_path,
        receipt_paths=tuple(sorted(receipt_paths)),
        failures=tuple(failures),
    )


def _binding_runner(binding: RemoteFaultBinding) -> RemoteRunner:
    def run(argv: Sequence[str], timeout: int) -> subprocess.CompletedProcess[str]:
        target = binding.target
        return run_verified_ssh_argv(
            host=target.ssh_host,
            user=target.ssh_user,
            port=target.ssh_port,
            key_path=target.ssh_key_path,
            expected_ed25519_fingerprint=binding.ssh_host_fingerprint,
            argv=argv,
            timeout=timeout,
        )

    return run


def _require_status_identity(
    payload: Mapping[str, Any], *, machine_id: str, status: str
) -> None:
    if payload.get("machine_id") != machine_id or payload.get("status") != status:
        raise RemoteFaultExecutionError(
            f"site status identity/result mismatch; expected {machine_id}/{status}"
        )


def _one_site_row(payload: Mapping[str, Any], *, site: str) -> dict[str, Any]:
    rows = payload.get("sites")
    if not isinstance(rows, list):
        raise RemoteFaultExecutionError("site status has no rows")
    selected = [dict(row) for row in rows if isinstance(row, Mapping) and row.get("site") == site]
    if len(selected) != 1:
        raise RemoteFaultExecutionError("site status does not contain exactly one target row")
    return selected[0]


def _one_reset_row(payload: Mapping[str, Any], *, site: str) -> dict[str, Any]:
    rows = payload.get("sites")
    if not isinstance(rows, list):
        raise RemoteFaultExecutionError("slot reset has no site rows")
    selected = [dict(row) for row in rows if isinstance(row, Mapping) and row.get("site") == site]
    if len(selected) != 1 or selected[0].get("ok") is not True:
        raise RemoteFaultExecutionError("slot reset target row is absent or failed")
    return selected[0]


def _command_metadata(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    stdout = str(result.stdout or "")
    stderr = str(result.stderr or "")
    return {
        "returncode": int(result.returncode),
        "stdout_sha256": _sha256_text(stdout),
        "stderr_sha256": _sha256_text(stderr),
        "stdout_bytes": len(stdout.encode("utf-8")),
        "stderr_bytes": len(stderr.encode("utf-8")),
        "raw_output_persisted": False,
    }


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _assert_private_file(path: Path) -> None:
    if not path.is_file() or stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise RemoteFaultExecutionError(
            f"controller-only evidence is absent or not mode-0600: {path}"
        )


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


_WORKER_COUNT_SCRIPT = r'''
import json, subprocess, time
# Split the marker so the probe's own parent shell command line does not
# contain the exact worker module name and cannot count itself.
marker = "evidence_system.adapters." + "webarena_official_worker"
counts = []
for sample in range(3):
    processes = subprocess.run(
        ["ps", "-eo", "args="], capture_output=True, text=True, timeout=10, check=False
    )
    if processes.returncode:
        raise SystemExit("worker process census failed")
    counts.append(sum(marker in line for line in processes.stdout.splitlines()))
    if sample < 2:
        time.sleep(1)
print(json.dumps({"worker_process_count": max(counts)}, sort_keys=True))
'''.strip()


_PROVIDER_ENV_ABSENCE_SCRIPT = r'''
import json, os
print(json.dumps({"provider_key_present": "OPENROUTER_API_KEY" in os.environ}, sort_keys=True))
'''.strip()


_LOGIN_FAILURE_SCRIPT = r'''
import hashlib, json, os, pathlib, shutil, socket, subprocess, sys, tempfile
runner = pathlib.Path(sys.argv[1])
python = sys.argv[2]
probe = socket.socket()
probe.settimeout(1)
if probe.connect_ex(("127.0.0.1", 1)) == 0:
    raise SystemExit("locked bad-login target unexpectedly accepts connections")
probe.close()
folder = pathlib.Path(tempfile.mkdtemp(prefix="wv-login-fault-", dir="/tmp"))
os.chmod(folder, 0o700)
stdout = ""
stderr = ""
returncode = 124
state_count = 0
try:
    env = os.environ.copy()
    env.update({
        "SHOPPING": "http://127.0.0.1:1/__intentional_login_fault__",
        "SHOPPING_ADMIN": "http://127.0.0.1:7780/admin",
        "REDDIT": "http://127.0.0.1:9999",
        "GITLAB": "http://127.0.0.1:8023",
        "WIKIPEDIA": "http://127.0.0.1:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing",
        "MAP": "http://127.0.0.1:3030",
        "HOMEPAGE": "PASS",
    })
    try:
        completed = subprocess.run(
            [python, "browser_env/auto_login.py", "--site_list", "shopping", "--auth_folder", str(folder)],
            cwd=runner,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        stdout, stderr, returncode = completed.stdout or "", completed.stderr or "", completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = str(exc.stdout or "")
        stderr = str(exc.stderr or "")
        returncode = 124
    state_count = len(list(folder.glob("*_state.json")))
finally:
    shutil.rmtree(folder, ignore_errors=True)
payload = {
    "probe_kind": "official_auto_login",
    "wrong_target_kind": "closed_loopback_port",
    "auto_login_exit_nonzero": returncode != 0,
    "auto_login_returncode": int(returncode),
    "storage_state_created": state_count != 0,
    "state_file_count": state_count,
    "auth_folder_removed": not folder.exists(),
    "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
    "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(),
    "stdout_bytes": len(stdout.encode()),
    "stderr_bytes": len(stderr.encode()),
}
print(json.dumps(payload, sort_keys=True))
'''.strip()


_INVALID_API_SCRIPT = rf'''
import hashlib, json, os, subprocess, sys
parent_before = "OPENROUTER_API_KEY" in os.environ
child = r"""
import hashlib, json, sys, urllib.error, urllib.request
key = sys.stdin.read()
request = urllib.request.Request(
    {OPENROUTER_AUTH_URL!r},
    headers={{"Authorization": "Bearer " + key}},
    method="GET",
)
status = None
body = b""
try:
    with urllib.request.urlopen(request, timeout=30) as response:
        status = int(response.status)
        body = response.read()
        exit_code = 0
except urllib.error.HTTPError as exc:
    status = int(exc.code)
    body = exc.read()
    exit_code = 17
except Exception:
    status = None
    body = b""
    exit_code = 18
print(json.dumps({{
    "http_status": status,
    "body_sha256": hashlib.sha256(body).hexdigest(),
    "body_bytes": len(body),
}}, sort_keys=True))
raise SystemExit(exit_code)
"""
env = {{key: value for key, value in os.environ.items() if key != "OPENROUTER_API_KEY"}}
completed = subprocess.run(
    [sys.executable, "-c", child],
    input={_INVALID_PLACEHOLDER!r},
    capture_output=True,
    text=True,
    env=env,
    timeout=45,
    check=False,
)
try:
    child_payload = json.loads(completed.stdout.strip().splitlines()[-1])
except Exception:
    child_payload = {{"http_status": None, "body_sha256": "0" * 64, "body_bytes": 0}}
parent_after = "OPENROUTER_API_KEY" in os.environ
payload = {{
    "probe_kind": "openrouter_transport",
    "endpoint_kind": "non_billable_key_auth",
    "worker_exit_nonzero": completed.returncode != 0,
    "child_returncode": int(completed.returncode),
    "provider_http_status": child_payload.get("http_status"),
    "model_completion_received": False,
    "credential_scope": "injected_placeholder_child_only",
    "response_body_sha256": child_payload.get("body_sha256"),
    "response_body_bytes": child_payload.get("body_bytes"),
    "parent_key_present_before": parent_before,
    "parent_key_present_after": parent_after,
    "placeholder_child_destroyed": completed.returncode is not None,
    "parent_environment_unchanged": parent_before == parent_after == False,
}}
print(json.dumps(payload, sort_keys=True))
'''.strip()


_EVALUATOR_ERROR_SCRIPT = r'''
import hashlib, json, os, pathlib, shutil, subprocess, sys, tempfile
controller_root = pathlib.Path(sys.argv[1])
python = sys.argv[2]
golden_source = pathlib.Path(sys.argv[3])
runtime_config = pathlib.Path(sys.argv[4])
contract_index = pathlib.Path(sys.argv[5])
scorer_source = controller_root / "src/evidence_system/adapters/webarena_verified_official_scorer.py"
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def tree_hash(root):
    rows=[]
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rows.append({"path": path.relative_to(root).as_posix(), "sha256": sha(path)})
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
def protect(root):
    for path in [root, *root.rglob("*")]:
        os.chmod(path, 0o700 if path.is_dir() else 0o600)
def run_score(root, summary):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(controller_root / "src")
    command = [
        python, "-m", "evidence_system.adapters.webarena_verified_official_scorer",
        "--task-id", "0", "--task-revision", str(revision),
        "--output-root", str(root), "--config", str(runtime_config),
        "--task-contract-index", str(contract_index), "--summary-output", str(summary),
    ]
    completed = subprocess.run(command, env=env, capture_output=True, text=True, timeout=700, check=False)
    try:
        value = json.loads(summary.read_text())
    except Exception:
        value = {}
    return completed, value
if not golden_source.is_dir() or not scorer_source.is_file():
    raise SystemExit("golden evaluator source is missing")
contracts = json.loads(contract_index.read_text())
entry = next(item for item in contracts["entries"] if int(item["task_id"]) == 0)
revision = int(entry["task_revision"])
baseline_before = tree_hash(golden_source)
workspace = pathlib.Path(tempfile.mkdtemp(prefix="wv-evaluator-fault-", dir="/tmp"))
os.chmod(workspace, 0o700)
payload = None
try:
    fault_root = workspace / "fault-copy"
    recovery_root = workspace / "recovery-copy"
    shutil.copytree(golden_source, fault_root)
    shutil.copytree(golden_source, recovery_root)
    protect(fault_root)
    protect(recovery_root)
    invalid_har = fault_root / "0/network.har"
    invalid_har.write_text("{}\n")
    os.chmod(invalid_har, 0o600)
    fault_summary = fault_root / "0/fault_summary.json"
    fault, fault_value = run_score(fault_root, fault_summary)
    recovery_summary = recovery_root / "0/recovery_summary.json"
    recovery, recovery_value = run_score(recovery_root, recovery_summary)
    baseline_after = tree_hash(golden_source)
    payload = {
        "probe_kind": "pinned_official_scorer",
        "scorer_exit_code": int(fault.returncode),
        "scorer_status": fault_value.get("scorer_status"),
        "official_evaluation_completed": fault_value.get("official_evaluation_completed"),
        "integrity_verified": fault_value.get("integrity_verified"),
        "mutated_input_is_copy": True,
        "fault_stdout_sha256": hashlib.sha256((fault.stdout or "").encode()).hexdigest(),
        "fault_stderr_sha256": hashlib.sha256((fault.stderr or "").encode()).hexdigest(),
        "golden_recovery_exit_code": int(recovery.returncode),
        "golden_recovery_scorer_status": recovery_value.get("scorer_status"),
        "golden_recovery_official_evaluation_completed": recovery_value.get("official_evaluation_completed"),
        "golden_recovery_integrity_verified": recovery_value.get("integrity_verified"),
        "recovery_stdout_sha256": hashlib.sha256((recovery.stdout or "").encode()).hexdigest(),
        "recovery_stderr_sha256": hashlib.sha256((recovery.stderr or "").encode()).hexdigest(),
        "baseline_hash_before": baseline_before,
        "baseline_hash_after": baseline_after,
        "baseline_artifact_hash_unchanged": baseline_before == baseline_after,
        "corrupt_copy_quarantined": fault_root.is_dir() and fault_root != golden_source,
        "temporary_workspace_deleted": False,
        "remote_scorer_source_sha256": sha(scorer_source),
    }
finally:
    shutil.rmtree(workspace, ignore_errors=True)
if payload is None:
    raise SystemExit("evaluator probe did not complete")
payload["temporary_workspace_deleted"] = not workspace.exists()
print(json.dumps(payload, sort_keys=True))
'''.strip()


__all__ = [
    "EXPECTED_AGENT_BINDINGS",
    "INVALID_PLACEHOLDER_SHA256",
    "REMOTE_EXECUTION_CONFIRMATION",
    "REMOTE_PLAN_SCHEMA",
    "RemoteFaultBinding",
    "RemoteFaultExecutionError",
    "RemoteFaultExecutor",
    "RemoteMatrixResult",
    "build_remote_fault_plan",
    "execute_remote_fault_matrix",
    "load_remote_fault_bindings",
    "write_remote_fault_plan",
]
