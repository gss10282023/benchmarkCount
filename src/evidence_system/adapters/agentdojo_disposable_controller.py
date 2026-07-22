"""Exact 192-slot/13-stage disposable AgentDojo round controller.

The controller owns ordering and concurrency semantics, while a transport owns
how one batch is executed on the VPS.  This separation gives us a fully
deterministic fake-transport end-to-end test without adding a second network
implementation.  Production transports must return a real stage receipt; fake
transports are explicitly marked non-publishable.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import tempfile
import threading
from typing import Any, Mapping, Protocol, Sequence
import uuid

from evidence_system.adapters.agentdojo import (
    AGENTDOJO_ATTACK,
    AGENTDOJO_BENCHMARK_VERSION,
    AGENTDOJO_DEFENSE,
    AGENTDOJO_GIT_COMMIT,
    AGENTDOJO_GIT_TREE,
    AGENTDOJO_PACKAGE_VERSION,
    AGENTDOJO_SYSTEM_MESSAGE_SHA256,
    AGENTDOJO_TOOL_DELIMITER,
    AGENTDOJO_TOOL_OUTPUT_FORMAT,
    _agentdojo_install_source_lock,
)
from evidence_system.adapters.base import json_arg, smoke_role_config
from evidence_system.adapters.agentdojo_runtime_control import (
    REQUIRED_AGENT_IDS,
    REQUIRED_MODELS,
    RuntimePolicyError,
    build_ramp_stage_receipt,
    load_credential_probe_receipt,
    load_ramp_stage_receipt,
    load_runtime_policy,
    materialize_disposable_stage_jobs,
    resource_worker_process_binding_sha256,
)
from evidence_system.adapters.runtime import (
    rsync_remote_tree,
    run_remote_blind_command,
)
from evidence_system.contracts.agentdojo_rate_lifecycle import (
    load_disposable_round_plan,
)
from evidence_system.contracts.common import load_mapping
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path
from evidence_system.orchestrator.jobs import resolve_infra_target


CONTROLLER_RECEIPT_SCHEMA_VERSION = "agentdojo_disposable_controller_receipt/v1"


@dataclass(frozen=True)
class DisposableBatch:
    round_definition_sha256: str
    round_kind: str
    stage_ordinal: int
    batch_ordinal: int
    workload_sha256: str
    locked_workers: int
    effective_workers: int
    model_ordinal: int
    agent_id: str
    model_id: str
    jobs: tuple[Mapping[str, Any], ...]
    source_entries: tuple[Mapping[str, Any], ...]
    artifact_namespace: Mapping[str, Any]


@dataclass(frozen=True)
class DisposableBatchResult:
    status: str
    completed_jobs: int
    failed_jobs: int
    incident_count: int


@dataclass(frozen=True)
class DisposableStageResult:
    status: str
    thresholds_passed: bool
    resulting_safe_workers: int
    stage_receipt_path: str | None


class DisposableTransport(Protocol):
    """Production boundary used by the deterministic controller."""

    publishable: bool

    def execute_batch(self, batch: DisposableBatch) -> DisposableBatchResult:
        """Execute exactly the supplied batch, appending blind stage ledgers."""

    def seal_stage(
        self,
        *,
        round_plan: Mapping[str, Any],
        stage: Mapping[str, Any],
        effective_workers: int,
        prior_safe_workers: int,
        batch_results: Sequence[DisposableBatchResult],
    ) -> DisposableStageResult:
        """Stop sampling and publish the stage receipt after all batches finish."""


class CountingFakeDisposableTransport:
    """Offline-only transport proving exact controller scheduling."""

    publishable = False

    def __init__(self) -> None:
        self.batches: list[DisposableBatch] = []

    def execute_batch(self, batch: DisposableBatch) -> DisposableBatchResult:
        self.batches.append(batch)
        return DisposableBatchResult(
            status="completed",
            completed_jobs=len(batch.jobs),
            failed_jobs=0,
            incident_count=0,
        )

    def seal_stage(
        self,
        *,
        round_plan: Mapping[str, Any],
        stage: Mapping[str, Any],
        effective_workers: int,
        prior_safe_workers: int,
        batch_results: Sequence[DisposableBatchResult],
    ) -> DisposableStageResult:
        del round_plan, batch_results
        return DisposableStageResult(
            status="passed",
            thresholds_passed=True,
            resulting_safe_workers=(
                int(stage["locked_workers"])
                if effective_workers == int(stage["locked_workers"])
                else prior_safe_workers
            ),
            stage_receipt_path=None,
        )


@dataclass
class _RemoteStageContext:
    stage_ordinal: int
    stage_id: str
    locked_workers: int
    effective_workers: int
    session_id: str
    host_boot_id: str
    minimum_worker_starttime_ticks: int
    expected_worker_uid: int
    worker_process_binding_sha256: str
    runtime_database_path: str
    remote_stage_root: str
    remote_blind_health_path: str
    remote_resource_ledger_path: str
    sampler_stop: threading.Event
    sampler_thread: threading.Thread | None = None
    sampler_count: int = 0
    sampler_error: BaseException | None = None


class VPSDisposableTransport:
    """Real SSH transport for one immutable disposable round.

    Raw worker output stays under a round-derived VPS-only disposable root.
    Only the two evidence-blind stage ledgers are retrieved to the controller.
    The five formal evidence roots from the infra overlay are rejected as both
    destinations and ancestors of the disposable root.
    """

    publishable = True
    _REMOTE_BASE = "/srv/agentdojo-full/disposable/namespaces"
    _SECRET_PATH = "/srv/agentdojo-full/secrets/openrouter.env"

    def __init__(self, *, round_plan_path: str | Path) -> None:
        self.round_plan_path = _regular_file(
            round_plan_path, "disposable round plan"
        )
        self.plan = load_disposable_round_plan(self.round_plan_path)
        definition = dict(self.plan["definition"])
        self.round_definition_sha256 = str(self.plan["definition_sha256"])
        self.result_namespace = str(definition["result_namespace"])
        self.policy_path = _regular_file(
            str(definition["runtime_policy"]["path"]),
            "disposable runtime policy",
        )
        self.policy = load_runtime_policy(
            json.loads(self.policy_path.read_text(encoding="utf-8")),
            expected_semantic_sha256=str(
                definition["runtime_policy"]["semantic_sha256"]
            ),
        )
        self.infra_path = _regular_file(
            str(definition["runtime_infra"]["path"]),
            "disposable runtime infra",
        )
        self.agents_path = _regular_file(
            str(definition["agents_config"]["path"]),
            "disposable agents config",
        )
        self.target = resolve_infra_target(
            "agentdojo", load_mapping(self.infra_path)
        )
        secret_path = str(
            self.target.benchmark_config.get("secret_env_path") or ""
        )
        if secret_path != self._SECRET_PATH:
            raise RuntimePolicyError(
                "disposable transport requires the locked OpenRouter secret path"
            )
        remote_workdir = str(self.target.remote_workdir).rstrip("/")
        if not remote_workdir.startswith("/"):
            raise RuntimePolicyError(
                "disposable transport requires an absolute remote workdir"
            )
        self.remote_workdir = remote_workdir
        install_dir = str(
            self.target.benchmark_config.get("install_dir")
            or self.target.runner_workdir
        ).rstrip("/")
        self.remote_python = f"{install_dir}/.venv/bin/python"
        if not self.remote_python.startswith("/"):
            raise RuntimePolicyError(
                "disposable transport requires an absolute remote Python"
            )
        self.remote_policy_path = self._remote_repo_path(
            str(definition["runtime_policy"]["path"])
        )
        self.remote_root = (
            f"{self._REMOTE_BASE}/{self.result_namespace}/rounds/"
            f"{self.round_definition_sha256}"
        )
        self.remote_runtime_state = f"{self.remote_root}/runtime"
        self._assert_isolated_remote_root()
        self._verify_pre_credential_receipt()
        self._stage: _RemoteStageContext | None = None
        self._initialize_remote_round()

    def execute_batch(self, batch: DisposableBatch) -> DisposableBatchResult:
        if self._stage is None:
            self._stage = self._start_stage(batch)
        context = self._stage
        if (
            context.stage_ordinal != batch.stage_ordinal
            or context.locked_workers != batch.locked_workers
            or context.effective_workers != batch.effective_workers
        ):
            raise RuntimePolicyError(
                "disposable transport crossed a stage boundary without sealing"
            )
        completed = 0
        worker_failures = 0
        unknown_transport_outcomes = 0
        with ThreadPoolExecutor(max_workers=batch.effective_workers) as pool:
            futures = [
                pool.submit(
                    self._run_job,
                    batch=batch,
                    job=dict(job),
                    source_entry=dict(source_entry),
                    context=context,
                )
                for job, source_entry in zip(
                    batch.jobs, batch.source_entries, strict=True
                )
            ]
            for future in as_completed(futures):
                try:
                    result = future.result()
                except BaseException:
                    unknown_transport_outcomes += 1
                else:
                    if result["status"] == "completed":
                        completed += 1
                    else:
                        worker_failures += 1
        if unknown_transport_outcomes:
            self._stop_sampler(context, allow_receipt=False)
            raise RuntimePolicyError(
                "disposable VPS batch has an unknown transport outcome; "
                "refusing replay or threshold sealing"
            )
        if worker_failures and batch.round_kind != "exploratory_measurement":
            self._stop_sampler(context, allow_receipt=False)
            raise RuntimePolicyError(
                f"finalized disposable VPS batch has {worker_failures} "
                "real worker failure(s)"
            )
        return DisposableBatchResult(
            status=(
                "completed_with_failures"
                if worker_failures
                else "completed"
            ),
            completed_jobs=completed,
            failed_jobs=worker_failures,
            incident_count=worker_failures,
        )

    def seal_stage(
        self,
        *,
        round_plan: Mapping[str, Any],
        stage: Mapping[str, Any],
        effective_workers: int,
        prior_safe_workers: int,
        batch_results: Sequence[DisposableBatchResult],
    ) -> DisposableStageResult:
        del batch_results
        context = self._stage
        if (
            context is None
            or context.stage_ordinal != int(stage["ordinal"])
            or context.effective_workers != effective_workers
            or str(round_plan["definition_sha256"])
            != self.round_definition_sha256
        ):
            raise RuntimePolicyError(
                "disposable stage seal does not match the active remote session"
            )
        self._stop_sampler(context, allow_receipt=True)
        artifact = dict(
            round_plan["artifact_namespace"]["stages"][context.stage_ordinal]
        )
        health_path = self._retrieve_blind_file(
            context=context,
            remote_name="blind_health.jsonl",
            destination=str(artifact["blind_health_ledger"]),
        )
        resource_path = self._retrieve_blind_file(
            context=context,
            remote_name="resource_health.jsonl",
            destination=str(artifact["resource_ledger"]),
        )
        receipt = build_ramp_stage_receipt(
            self.policy,
            scope=str(stage["receipt_scope"]),
            worker_concurrency=int(stage["locked_workers"]),
            effective_worker_concurrency=effective_workers,
            prior_safe_workers=prior_safe_workers,
            runtime_infra_file_sha256=sha256_file(self.infra_path),
            blind_health_ledger_path=health_path,
            resource_ledger_path=resource_path,
            stage_workload=dict(stage["workload"]),
        )
        receipt_path = _write_once_json(
            str(artifact["stage_receipt"]), receipt
        )
        self._stage = None
        return DisposableStageResult(
            status=str(receipt["status"]),
            thresholds_passed=bool(receipt["observed"]["thresholds_passed"]),
            resulting_safe_workers=int(receipt["resulting_safe_workers"]),
            stage_receipt_path=str(receipt_path),
        )

    def _verify_pre_credential_receipt(self) -> None:
        phase = (
            "pre_ramp"
            if self.plan["definition"]["round_kind"]
            == "exploratory_measurement"
            else "pre_final_validation"
        )
        path = _regular_file(
            str(self.plan["artifact_namespace"]["pre_credential_receipt"]),
            "disposable pre-credential receipt",
        )
        load_credential_probe_receipt(
            path,
            expected_policy_sha256=self.policy.semantic_sha256,
            expected_runtime_infra_file_sha256=sha256_file(self.infra_path),
            expected_probe_phase=phase,
        )

    def _assert_isolated_remote_root(self) -> None:
        formal = [
            str(self.target.benchmark_config.get(field) or "")
            for field in (
                "runtime_state_root",
                "remote_raw_root",
                "blind_aggregate_root",
                "failed_attempt_archive_root",
                "retrieval_snapshot_root",
            )
        ]
        if any(not value.startswith("/") for value in formal):
            raise RuntimePolicyError("formal overlay roots are not fully absolute")
        for value in formal:
            try:
                common = os.path.commonpath((self.remote_root, value))
            except ValueError as exc:
                raise RuntimePolicyError("remote root path comparison failed") from exc
            if common in {self.remote_root, value}:
                raise RuntimePolicyError(
                    "disposable root overlaps a formal evidence root"
                )

    def _initialize_remote_round(self) -> None:
        definition = dict(self.plan["definition"])
        files = dict(definition["runtime_snapshot"]["files"])
        for ref_name in (
            "runtime_policy",
            "runtime_infra",
            "agents_config",
            "manifest",
            "source_bundle",
        ):
            ref = dict(definition[ref_name])
            path = str(ref["path"])
            if Path(path).is_absolute() or ".." in Path(path).parts:
                raise RuntimePolicyError(
                    f"round {ref_name} path is not remotely portable"
                )
            files[path] = str(ref["sha256"])
        metadata = {
            "schema_version": "agentdojo_disposable_remote_round/v1",
            "round_definition_sha256": self.round_definition_sha256,
            "result_namespace": self.result_namespace,
            "remote_workdir": self.remote_workdir,
            "formal_roots_touched": False,
        }
        script = """
import hashlib, json, os, pathlib, stat, sys
root=pathlib.Path(sys.argv[1]); repo=pathlib.Path(sys.argv[2]); secret=pathlib.Path(sys.argv[3])
files=json.loads(sys.argv[4]); expected=json.loads(sys.argv[5]); formal=json.loads(sys.argv[6])
if not root.is_absolute() or not str(root).startswith('/srv/agentdojo-full/disposable/namespaces/'):
    raise SystemExit(70)
for value in formal:
    common=os.path.commonpath((str(root), value))
    if common in {str(root), value}: raise SystemExit(71)
secret_info=os.lstat(secret)
if stat.S_ISLNK(secret_info.st_mode) or not stat.S_ISREG(secret_info.st_mode) or stat.S_IMODE(secret_info.st_mode)!=0o600 or secret_info.st_nlink!=1 or secret_info.st_uid!=os.geteuid():
    raise SystemExit(72)
for rel,digest in files.items():
    path=repo/pathlib.Path(rel); info=os.lstat(path)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
        raise SystemExit(73)
root.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
meta=root/'round_binding.json'
encoded=(json.dumps(expected,sort_keys=True,indent=2)+'\\n').encode()
if root.exists():
    if root.is_symlink() or not root.is_dir() or not meta.is_file() or meta.is_symlink() or meta.read_bytes()!=encoded: raise SystemExit(74)
else:
    root.mkdir(mode=0o700)
    fd=os.open(meta,os.O_CREAT|os.O_EXCL|os.O_WRONLY|getattr(os,'O_NOFOLLOW',0),0o600)
    try: os.write(fd,encoded); os.fsync(fd)
    finally: os.close(fd)
print(json.dumps({'schema_version':'agentdojo_disposable_remote_init/v1','status':'ready','verified_file_count':len(files),'blind_only':True},sort_keys=True))
""".strip()
        _validate_remote_python_script(script, label="round initialization")
        formal = [
            str(self.target.benchmark_config[field])
            for field in (
                "runtime_state_root",
                "remote_raw_root",
                "blind_aggregate_root",
                "failed_attempt_archive_root",
                "retrieval_snapshot_root",
            )
        ]
        command = (
            f"{shlex.quote(self.remote_python)} -c {shlex.quote(script)} "
            f"{shlex.quote(self.remote_root)} {shlex.quote(self.remote_workdir)} "
            f"{shlex.quote(self._SECRET_PATH)} {json_arg(files)} "
            f"{json_arg(metadata)} {json_arg(formal)}"
        )
        completed = run_remote_blind_command(
            self.target,
            command,
            timeout_seconds=120,
            transient_retry_attempts=1,
            maximum_stdout_bytes=2048,
            maximum_stderr_bytes=0,
        )
        if completed.returncode != 0 or completed.stderr:
            raise RuntimePolicyError(
                "disposable remote round initialization/hash audit failed"
            )
        payload = json.loads(completed.stdout)
        if payload != {
            "schema_version": "agentdojo_disposable_remote_init/v1",
            "status": "ready",
            "verified_file_count": len(files),
            "blind_only": True,
        }:
            raise RuntimePolicyError(
                "disposable remote initialization envelope differs"
            )

    def _start_stage(self, batch: DisposableBatch) -> _RemoteStageContext:
        artifact = dict(batch.artifact_namespace)
        for field in (
            "blind_health_ledger",
            "resource_ledger",
            "stage_receipt",
        ):
            path = Path(str(artifact[field]))
            if not path.is_absolute():
                path = resolve_repo_path(path)
            if path.exists() or path.is_symlink():
                raise RuntimePolicyError(
                    f"disposable stage artifact already exists: {field}"
                )
        stage_id = f"disposable-stage-{batch.stage_ordinal:02d}"
        session_id = f"session-{uuid.uuid4().hex}"
        binding = resource_worker_process_binding_sha256(
            execution_scope_sha256=self.round_definition_sha256,
            stage_id=stage_id,
            session_id=session_id,
            stage_binding_sha256=batch.workload_sha256,
        )
        remote_stage = f"{self.remote_root}/stages/{batch.stage_ordinal:02d}"
        remote_health = f"{remote_stage}/blind/blind_health.jsonl"
        remote_resource = f"{remote_stage}/blind/resource_health.jsonl"
        script = """
import json, os, pathlib, sys
from evidence_system.adapters.agentdojo_runtime_control import GlobalRateLimiter, load_runtime_policy, linux_host_boot_id
stage=pathlib.Path(sys.argv[1]); runtime=pathlib.Path(sys.argv[2]); policy_path=pathlib.Path(sys.argv[3]); binding=json.loads(sys.argv[4])
stage.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
stage.mkdir(mode=0o700)
for name in ('blind','raw','control'): (stage/name).mkdir(mode=0o700)
policy=load_runtime_policy(json.loads(policy_path.read_text()))
limiter=GlobalRateLimiter(policy,state_dir=runtime,budget_scope='disposable_preflight')
ticks=int(float(pathlib.Path('/proc/uptime').read_text().split()[0])*os.sysconf('SC_CLK_TCK'))
(stage/'stage_binding.json').write_text(json.dumps(binding,sort_keys=True,indent=2)+'\\n')
print(json.dumps({'schema_version':'agentdojo_disposable_remote_stage_init/v1','status':'ready','host_boot_id':linux_host_boot_id(),'expected_worker_uid':os.geteuid(),'minimum_worker_starttime_ticks':max(1,ticks),'runtime_database_path':str(limiter.database_path.resolve()),'blind_only':True},sort_keys=True))
""".strip()
        _validate_remote_python_script(script, label="stage initialization")
        stage_binding = {
            "round_definition_sha256": self.round_definition_sha256,
            "stage_ordinal": batch.stage_ordinal,
            "stage_id": stage_id,
            "session_id": session_id,
            "workload_sha256": batch.workload_sha256,
            "locked_workers": batch.locked_workers,
            "effective_workers": batch.effective_workers,
        }
        command = (
            f"cd {shlex.quote(self.remote_workdir)} && "
            f"PYTHONPATH={shlex.quote(self.remote_workdir + '/src')} "
            f"{shlex.quote(self.remote_python)} -c {shlex.quote(script)} "
            f"{shlex.quote(remote_stage)} {shlex.quote(self.remote_runtime_state)} "
            f"{shlex.quote(self.remote_policy_path)} {json_arg(stage_binding)}"
        )
        completed = run_remote_blind_command(
            self.target,
            command,
            timeout_seconds=120,
            transient_retry_attempts=1,
            maximum_stdout_bytes=4096,
            maximum_stderr_bytes=0,
        )
        if completed.returncode != 0 or completed.stderr:
            raise RuntimePolicyError("disposable remote stage initialization failed")
        payload = json.loads(completed.stdout)
        required = {
            "schema_version",
            "status",
            "host_boot_id",
            "expected_worker_uid",
            "minimum_worker_starttime_ticks",
            "runtime_database_path",
            "blind_only",
        }
        if (
            set(payload) != required
            or payload["schema_version"]
            != "agentdojo_disposable_remote_stage_init/v1"
            or payload["status"] != "ready"
            or payload["blind_only"] is not True
            or not str(payload["runtime_database_path"]).startswith(
                self.remote_runtime_state.rstrip("/") + "/"
            )
        ):
            raise RuntimePolicyError(
                "disposable remote stage initialization envelope differs"
            )
        context = _RemoteStageContext(
            stage_ordinal=batch.stage_ordinal,
            stage_id=stage_id,
            locked_workers=batch.locked_workers,
            effective_workers=batch.effective_workers,
            session_id=session_id,
            host_boot_id=str(payload["host_boot_id"]),
            minimum_worker_starttime_ticks=int(
                payload["minimum_worker_starttime_ticks"]
            ),
            expected_worker_uid=int(payload["expected_worker_uid"]),
            worker_process_binding_sha256=binding,
            runtime_database_path=str(payload["runtime_database_path"]),
            remote_stage_root=remote_stage,
            remote_blind_health_path=remote_health,
            remote_resource_ledger_path=remote_resource,
            sampler_stop=threading.Event(),
        )
        context.sampler_thread = threading.Thread(
            target=self._sample_resources,
            args=(context,),
            name=f"disposable-resource-{batch.stage_ordinal:02d}",
            daemon=True,
        )
        context.sampler_thread.start()
        return context

    def _sample_resources(self, context: _RemoteStageContext) -> None:
        command = (
            f"cd {shlex.quote(self.remote_workdir)} && "
            f"PYTHONPATH={shlex.quote(self.remote_workdir + '/src')} "
            f"{shlex.quote(self.remote_python)} -m "
            "evidence_system.cli.agentdojo_runtime_health sample-resource "
            f"--ledger {shlex.quote(context.remote_resource_ledger_path)} "
            f"--worker-concurrency {context.effective_workers} "
            "--sample-seconds 0.25 "
            f"--policy {shlex.quote(self.remote_policy_path)} "
            f"--runtime-state-dir {shlex.quote(self.remote_runtime_state)} "
            "--budget-scope disposable_preflight "
            f"--expected-database-path {shlex.quote(context.runtime_database_path)} "
            f"--session-id {shlex.quote(context.session_id)} "
            f"--host-boot-id {shlex.quote(context.host_boot_id)} "
            f"--stage-binding-sha256 {shlex.quote(self.plan['definition']['stages'][context.stage_ordinal]['workload_sha256'])} "
            f"--worker-process-binding-sha256 {shlex.quote(context.worker_process_binding_sha256)} "
            f"--expected-worker-uid {context.expected_worker_uid} "
            f"--minimum-worker-starttime-ticks {context.minimum_worker_starttime_ticks}"
        )
        while not context.sampler_stop.is_set():
            try:
                completed = run_remote_blind_command(
                    self.target,
                    command,
                    timeout_seconds=30,
                    transient_retry_attempts=1,
                    maximum_stdout_bytes=4096,
                    maximum_stderr_bytes=0,
                )
                if completed.returncode != 0 or completed.stderr:
                    raise RuntimePolicyError(
                        "remote disposable resource sample failed"
                    )
                payload = json.loads(completed.stdout)
                if (
                    payload.get("schema_version")
                    != "agentdojo_openrouter_ramp_resource_sample/v2"
                    or payload.get("session_id") != context.session_id
                ):
                    raise RuntimePolicyError(
                        "remote disposable resource sample envelope differs"
                    )
                context.sampler_count += 1
            except BaseException as exc:
                context.sampler_error = exc
                context.sampler_stop.set()
                return
            context.sampler_stop.wait(0.1)

    def _stop_sampler(
        self, context: _RemoteStageContext, *, allow_receipt: bool
    ) -> None:
        context.sampler_stop.set()
        if context.sampler_thread is not None:
            context.sampler_thread.join(timeout=60)
            if context.sampler_thread.is_alive():
                raise RuntimePolicyError(
                    "disposable resource sampler did not stop"
                )
        if context.sampler_error is not None:
            raise RuntimePolicyError(
                "disposable resource sampler failed during the stage"
            ) from context.sampler_error
        if allow_receipt and context.sampler_count < self.policy.ramp_minimum_resource_samples:
            raise RuntimePolicyError(
                "disposable stage produced too few real resource samples"
            )

    def _run_job(
        self,
        *,
        batch: DisposableBatch,
        job: dict[str, Any],
        source_entry: dict[str, Any],
        context: _RemoteStageContext,
    ) -> dict[str, Any]:
        role = smoke_role_config(job, agents_config_path=self.agents_path)
        if (
            str(role["provider"]) != "openrouter"
            or str(role["model"]) != batch.model_id
            or str(role["api_key_env"]) != "OPENROUTER_API_KEY"
        ):
            raise RuntimePolicyError(
                "disposable worker model/credential binding differs"
            )
        job["runtime_session_id"] = context.session_id
        source_lock = _agentdojo_install_source_lock(source_entry)
        case_bits = str(job["case_unit_id"]).split(":")
        if len(case_bits) != 4:
            raise RuntimePolicyError("disposable job case identity is invalid")
        suite, user_task, injection_task = case_bits[1:]
        identity = sha256_object(
            {
                key: str(job[key])
                for key in ("job_id", "case_unit_id", "record_slot_id")
            }
        )
        output_dir = f"{context.remote_stage_root}/raw/{identity}"
        control_dir = f"{context.remote_stage_root}/control/{identity}"
        claim = f"{control_dir}/claim.json"
        preclaim_script = """
import json, os, pathlib, sys
p=pathlib.Path(sys.argv[1]); p.parent.mkdir(mode=0o700); value={'job_identity_sha256':sys.argv[2],'status':'claimed'}
fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY|getattr(os,'O_NOFOLLOW',0),0o600)
try: os.write(fd,(json.dumps(value,sort_keys=True)+'\\n').encode()); os.fsync(fd)
finally: os.close(fd)
""".strip()
        _validate_remote_python_script(preclaim_script, label="job preclaim")
        worker = (
            f"PYTHONHASHSEED={int(job['seed'])} "
            f"PYTHONPATH={shlex.quote(self.remote_workdir + '/src')} "
            f"{shlex.quote(self.remote_python)} -m "
            "evidence_system.adapters.agentdojo_worker "
            f"--job-json {json_arg(job)} "
            f"--source-entry-json {json_arg(source_entry)} "
            f"--output-dir {shlex.quote(output_dir)} "
            f"--suite {shlex.quote(suite)} "
            f"--user-task {shlex.quote(user_task)} "
            f"--injection-task {shlex.quote(injection_task)} "
            f"--agentdojo-package-version {AGENTDOJO_PACKAGE_VERSION} "
            f"--agentdojo-git-commit {AGENTDOJO_GIT_COMMIT} "
            f"--agentdojo-git-tree {AGENTDOJO_GIT_TREE} "
            f"--agentdojo-source-lock-json {json_arg(source_lock)} "
            f"--benchmark-version {AGENTDOJO_BENCHMARK_VERSION} "
            f"--model-id {shlex.quote(batch.model_id)} "
            f"--temperature {shlex.quote(str(role['temperature']))} "
            f"--max-tokens {int(role['max_tokens'])} "
            f"--timeout-seconds {int(role['timeout_seconds'])} "
            f"--retry {int(role['retry'])} "
            "--openrouter-api-key-env OPENROUTER_API_KEY "
            f"--secret-env-path {shlex.quote(self._SECRET_PATH)} "
            f"--tool-delimiter {AGENTDOJO_TOOL_DELIMITER} "
            f"--tool-output-format {AGENTDOJO_TOOL_OUTPUT_FORMAT} "
            f"--system-message-sha256 {AGENTDOJO_SYSTEM_MESSAGE_SHA256} "
            f"--defense {AGENTDOJO_DEFENSE} --attack {AGENTDOJO_ATTACK} "
            f"--openrouter-runtime-policy-json {json_arg(dict(self.policy.raw))} "
            f"--openrouter-runtime-policy-sha256 {self.policy.semantic_sha256} "
            f"--openrouter-runtime-policy-file-sha256 {sha256_file(self.policy_path)} "
            f"--runtime-state-dir {shlex.quote(self.remote_runtime_state)} "
            f"--disposable-blind-health-path {shlex.quote(context.remote_blind_health_path)} "
            f"--resource-stage-token {context.worker_process_binding_sha256}"
        )
        result_script = """
import json, pathlib, stat, sys
root=pathlib.Path(sys.argv[1]); rc=int(sys.argv[2]); identity=sys.argv[3]; status='failed'
try:
    path=root/'run_summary.json'; info=path.lstat()
    if stat.S_ISREG(info.st_mode) and info.st_nlink==1:
        value=json.loads(path.read_text())
        if rc==0 and value.get('status')=='completed': status='completed'
except Exception: pass
print(json.dumps({'schema_version':'agentdojo_disposable_worker_result/v1','status':status,'job_identity_sha256':identity,'worker_exit_code':rc,'blind_only':True},sort_keys=True))
""".strip()
        _validate_remote_python_script(result_script, label="job result audit")
        command = (
            f"cd {shlex.quote(self.remote_workdir)} && "
            f"{shlex.quote(self.remote_python)} -c {shlex.quote(preclaim_script)} "
            f"{shlex.quote(claim)} {identity} && rc=0 && "
            f"{worker} > {shlex.quote(control_dir + '/worker.stdout.log')} "
            f"2> {shlex.quote(control_dir + '/worker.stderr.log')} || rc=$?; "
            f"{shlex.quote(self.remote_python)} -c {shlex.quote(result_script)} "
            f"{shlex.quote(output_dir)} \"$rc\" {identity}"
        )
        completed = run_remote_blind_command(
            self.target,
            command,
            timeout_seconds=None,
            transient_retry_attempts=1,
            maximum_stdout_bytes=2048,
            maximum_stderr_bytes=0,
        )
        if completed.returncode != 0 or completed.stderr:
            raise RuntimePolicyError(
                "disposable SSH worker outcome is unknown; refusing replay"
            )
        payload = json.loads(completed.stdout)
        if (
            set(payload)
            != {
                "schema_version",
                "status",
                "job_identity_sha256",
                "worker_exit_code",
                "blind_only",
            }
            or payload["schema_version"]
            != "agentdojo_disposable_worker_result/v1"
            or payload["job_identity_sha256"] != identity
            or payload["status"] not in {"completed", "failed"}
            or payload["blind_only"] is not True
        ):
            raise RuntimePolicyError(
                "disposable worker returned a non-blind or stale envelope"
            )
        return payload

    def _retrieve_blind_file(
        self,
        *,
        context: _RemoteStageContext,
        remote_name: str,
        destination: str,
    ) -> Path:
        temporary = Path(tempfile.mkdtemp(prefix="agentdojo-disposable-blind-"))
        try:
            rsync_remote_tree(
                self.target,
                f"{context.remote_stage_root}/blind",
                temporary,
                timeout_seconds=120,
                transient_retry_attempts=1,
            )
            entries = sorted(
                path.name for path in temporary.iterdir() if path.is_file()
            )
            if entries != ["blind_health.jsonl", "resource_health.jsonl"]:
                raise RuntimePolicyError(
                    "remote disposable blind directory contains unexpected files"
                )
            source = temporary / remote_name
            if source.is_symlink() or not source.is_file():
                raise RuntimePolicyError(
                    "remote disposable blind ledger retrieval is unsafe"
                )
            return _write_once_bytes(destination, source.read_bytes())
        finally:
            shutil.rmtree(temporary, ignore_errors=True)

    def _remote_repo_path(self, portable: str) -> str:
        path = Path(portable)
        if path.is_absolute() or ".." in path.parts:
            raise RuntimePolicyError("round source path is not remotely portable")
        return f"{self.remote_workdir}/{path.as_posix()}"


def execute_disposable_round(
    *,
    round_plan_path: str | Path,
    transport: DisposableTransport,
    receipt_path: str | Path | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Execute one immutable round without ever scheduling cross-model overlap."""

    plan_file = _regular_file(round_plan_path, "disposable round plan")
    plan = load_disposable_round_plan(plan_file)
    definition = dict(plan["definition"])
    stages = list(definition["stages"])
    if len(stages) != 13:
        raise RuntimePolicyError("disposable controller requires exactly 13 stages")
    policy_ref = dict(definition["runtime_policy"])
    policy_file = _regular_file(policy_ref["path"], "disposable runtime policy")
    policy = load_runtime_policy(
        json.loads(policy_file.read_text(encoding="utf-8")),
        expected_semantic_sha256=str(policy_ref["semantic_sha256"]),
    )
    infra_sha = str(definition["runtime_infra"]["sha256"])
    prior_safe = {ordinal: 4 for ordinal in range(len(REQUIRED_MODELS))}
    promotion_open = {ordinal: True for ordinal in range(len(REQUIRED_MODELS))}
    stage_rows: list[dict[str, Any]] = []
    scheduled_jobs = 0
    transport_batch_count = 0

    for stage in stages:
        ordinal = int(stage["ordinal"])
        materialized = materialize_disposable_stage_jobs(stage["workload"])
        locked_workers = int(stage["locked_workers"])
        model_ordinal_raw = stage["model_ordinal"]
        if model_ordinal_raw is None:
            effective_workers = 4
            batches = _split_mixed_canary(materialized, workers=4)
            stage_prior_safe = 4
        else:
            model_ordinal = int(model_ordinal_raw)
            stage_prior_safe = prior_safe[model_ordinal]
            if definition["round_kind"] == "exploratory_measurement":
                effective_workers = (
                    locked_workers
                    if promotion_open[model_ordinal]
                    else stage_prior_safe
                )
            else:
                expected_effective = stage.get("effective_workers")
                if not isinstance(expected_effective, int):
                    raise RuntimePolicyError(
                        "validation stage lacks finalized effective workers"
                    )
                effective_workers = expected_effective
            batches = [(model_ordinal, materialized)]

        existing = (
            _existing_publishable_stage(
                plan=plan,
                stage=stage,
                policy_sha256=policy.semantic_sha256,
                infra_sha256=infra_sha,
                effective_workers=effective_workers,
                prior_safe_workers=stage_prior_safe,
            )
            if transport.publishable
            else None
        )
        batch_results: list[DisposableBatchResult] = []
        if existing is None:
            for batch_ordinal, (model_ordinal, rows) in enumerate(batches):
                batch = _build_batch(
                    plan=plan,
                    stage=stage,
                    batch_ordinal=batch_ordinal,
                    model_ordinal=model_ordinal,
                    effective_workers=effective_workers,
                    materialized=rows,
                )
                result = transport.execute_batch(batch)
                _validate_batch_result(
                    result,
                    expected_jobs=len(rows),
                    allow_worker_failures=(
                        definition["round_kind"]
                        == "exploratory_measurement"
                    ),
                )
                batch_results.append(result)
            sealed = transport.seal_stage(
                round_plan=plan,
                stage=stage,
                effective_workers=effective_workers,
                prior_safe_workers=stage_prior_safe,
                batch_results=batch_results,
            )
        else:
            sealed = existing
        completed_jobs, failed_jobs, incident_count = _stage_batch_counters(
            batch_results=batch_results,
            sealed=sealed,
            planned_jobs=len(materialized),
        )
        scheduled_jobs += len(materialized)
        transport_batch_count += len(batches)
        _validate_stage_result(
            sealed,
            publishable=bool(transport.publishable),
            policy_sha256=policy.semantic_sha256,
            infra_sha256=infra_sha,
            scope=str(stage["receipt_scope"]),
            expected_stage=stage,
            expected_effective_workers=effective_workers,
            expected_prior_safe_workers=stage_prior_safe,
        )
        if model_ordinal_raw is not None and definition[
            "round_kind"
        ] == "exploratory_measurement":
            model_ordinal = int(model_ordinal_raw)
            if sealed.thresholds_passed and effective_workers == locked_workers:
                prior_safe[model_ordinal] = locked_workers
            else:
                promotion_open[model_ordinal] = False
            if sealed.resulting_safe_workers != prior_safe[model_ordinal]:
                raise RuntimePolicyError(
                    "transport stage result broke the adaptive safe-worker chain"
                )
        stage_rows.append(
            {
                "ordinal": ordinal,
                "locked_workers": locked_workers,
                "effective_workers": effective_workers,
                "model_ordinal": model_ordinal_raw,
                "planned_jobs": len(materialized),
                "transport_batch_count": len(batches),
                "opaque_completed_job_count": completed_jobs,
                "opaque_worker_failure_count": failed_jobs,
                "opaque_incident_count": incident_count,
                "status": sealed.status,
                "thresholds_passed": sealed.thresholds_passed,
                "resulting_safe_workers": sealed.resulting_safe_workers,
                "stage_receipt": (
                    None
                    if sealed.stage_receipt_path is None
                    else {
                        "path": sealed.stage_receipt_path,
                        "sha256": sha256_file(sealed.stage_receipt_path),
                    }
                ),
            }
        )

    if scheduled_jobs != 192 or len(stage_rows) != 13:
        raise RuntimePolicyError(
            "disposable controller denominator differs from 192 slots/13 stages"
        )
    if transport_batch_count != 15:
        raise RuntimePolicyError(
            "model-serial mixed canary requires 15 transport batches across 13 stages"
        )
    model_counts = {agent: 0 for agent in REQUIRED_AGENT_IDS}
    for stage in stages:
        for row in materialize_disposable_stage_jobs(stage["workload"]):
            model_counts[str(row["job"]["agent_id"])] += 1
    if list(model_counts.values()) != [64, 64, 64]:
        raise RuntimePolicyError("disposable controller model denominators differ")

    payload = {
        "schema_version": CONTROLLER_RECEIPT_SCHEMA_VERSION,
        "status": (
            "test_only_completed"
            if not transport.publishable
            else (
                "completed"
                if all(row["status"] == "passed" for row in stage_rows)
                else "completed_with_threshold_holds"
            )
        ),
        "created_at": _timestamp(created_at),
        "publishable": bool(transport.publishable),
        "round_plan": {
            "path": _portable_path(plan_file),
            "sha256": sha256_file(plan_file),
            "definition_sha256": str(plan["definition_sha256"]),
        },
        "round_kind": str(definition["round_kind"]),
        "stage_count": 13,
        "record_slot_count": 192,
        "record_slots_per_agent": model_counts,
        "transport_batch_count": 15,
        "mixed_canary_schedule": "three_serial_four_slot_single_model_subbatches",
        "cross_model_overlap_allowed": False,
        "stages": stage_rows,
        "contains_prompt_response_trajectory_evaluator_or_label": False,
    }
    payload["receipt_sha256"] = sha256_object(payload)
    if receipt_path is not None:
        _write_once_json(receipt_path, payload)
    return payload


def _split_mixed_canary(
    rows: Sequence[Mapping[str, Any]], *, workers: int
) -> list[tuple[int, list[Mapping[str, Any]]]]:
    if len(rows) != workers * len(REQUIRED_MODELS):
        raise RuntimePolicyError("mixed canary does not contain 12 jobs")
    batches: list[tuple[int, list[Mapping[str, Any]]]] = []
    for model_ordinal, agent_id in enumerate(REQUIRED_AGENT_IDS):
        start = model_ordinal * workers
        batch = list(rows[start : start + workers])
        if len(batch) != workers or {
            str(row["job"]["agent_id"]) for row in batch
        } != {agent_id}:
            raise RuntimePolicyError(
                "mixed canary model-serial batch identity differs"
            )
        batches.append((model_ordinal, batch))
    return batches


def _build_batch(
    *,
    plan: Mapping[str, Any],
    stage: Mapping[str, Any],
    batch_ordinal: int,
    model_ordinal: int,
    effective_workers: int,
    materialized: Sequence[Mapping[str, Any]],
) -> DisposableBatch:
    if not materialized:
        raise RuntimePolicyError("disposable transport batch is empty")
    expected_agent = REQUIRED_AGENT_IDS[model_ordinal]
    if {str(row["job"]["agent_id"]) for row in materialized} != {
        expected_agent
    }:
        raise RuntimePolicyError("disposable batch contains cross-model jobs")
    artifact = plan["artifact_namespace"]["stages"][int(stage["ordinal"])]
    return DisposableBatch(
        round_definition_sha256=str(plan["definition_sha256"]),
        round_kind=str(plan["definition"]["round_kind"]),
        stage_ordinal=int(stage["ordinal"]),
        batch_ordinal=batch_ordinal,
        workload_sha256=str(stage["workload_sha256"]),
        locked_workers=int(stage["locked_workers"]),
        effective_workers=effective_workers,
        model_ordinal=model_ordinal,
        agent_id=expected_agent,
        model_id=REQUIRED_MODELS[model_ordinal],
        jobs=tuple(dict(row["job"]) for row in materialized),
        source_entries=tuple(dict(row["source_entry"]) for row in materialized),
        artifact_namespace=dict(artifact),
    )


def _validate_batch_result(
    result: DisposableBatchResult,
    *,
    expected_jobs: int,
    allow_worker_failures: bool,
) -> None:
    exact_denominator = (
        result.completed_jobs >= 0
        and result.failed_jobs >= 0
        and result.completed_jobs + result.failed_jobs == expected_jobs
    )
    incidents_are_opaque_counts = (
        result.incident_count >= result.failed_jobs
    )
    expected_status = (
        "completed_with_failures"
        if result.failed_jobs
        else "completed"
    )
    if allow_worker_failures:
        valid = (
            exact_denominator
            and incidents_are_opaque_counts
            and result.status == expected_status
        )
    else:
        valid = (
            result.status == "completed"
            and result.completed_jobs == expected_jobs
            and result.failed_jobs == 0
            and result.incident_count >= 0
        )
    if not valid:
        raise RuntimePolicyError("disposable transport batch did not complete exactly")


def _stage_batch_counters(
    *,
    batch_results: Sequence[DisposableBatchResult],
    sealed: DisposableStageResult,
    planned_jobs: int,
) -> tuple[int, int, int]:
    if batch_results:
        completed = sum(row.completed_jobs for row in batch_results)
        failed = sum(row.failed_jobs for row in batch_results)
        incidents = sum(row.incident_count for row in batch_results)
    elif sealed.stage_receipt_path is not None:
        receipt = json.loads(
            Path(sealed.stage_receipt_path).read_text(encoding="utf-8")
        )
        observed = dict(receipt.get("observed") or {})
        failed = int(observed.get("missing_successful_jobs") or 0)
        completed = planned_jobs - failed
        incidents = int(observed.get("worker_failures") or 0)
    else:
        completed = planned_jobs
        failed = 0
        incidents = 0
    if (
        completed < 0
        or failed < 0
        or incidents < 0
        or completed + failed != planned_jobs
    ):
        raise RuntimePolicyError(
            "disposable stage opaque batch counters break the denominator"
        )
    return completed, failed, incidents


def _validate_stage_result(
    result: DisposableStageResult,
    *,
    publishable: bool,
    policy_sha256: str,
    infra_sha256: str,
    scope: str,
    expected_stage: Mapping[str, Any],
    expected_effective_workers: int,
    expected_prior_safe_workers: int,
) -> None:
    if result.status not in {
        "passed",
        "held_at_prior_safe",
        "measured_with_threshold_breach",
    }:
        raise RuntimePolicyError("disposable transport returned an invalid stage status")
    if result.resulting_safe_workers not in (4, 8, 16, 32):
        raise RuntimePolicyError("disposable transport safe-worker result is invalid")
    if not publishable:
        if result.stage_receipt_path is not None:
            raise RuntimePolicyError("fake transport must not publish a real stage receipt")
        return
    if not result.stage_receipt_path:
        raise RuntimePolicyError("publishable transport did not return a stage receipt")
    receipt = load_ramp_stage_receipt(
        result.stage_receipt_path,
        expected_policy_sha256=policy_sha256,
        expected_runtime_infra_file_sha256=infra_sha256,
        expected_scope=scope,
    )
    if (
        receipt["stage_workload_sha256"] != expected_stage["workload_sha256"]
        or int(receipt["effective_workers"]) != expected_effective_workers
        or int(receipt["prior_safe_workers"]) != expected_prior_safe_workers
        or receipt["status"] != result.status
        or bool(receipt["observed"]["thresholds_passed"])
        != result.thresholds_passed
        or int(receipt["resulting_safe_workers"])
        != result.resulting_safe_workers
    ):
        raise RuntimePolicyError("transport stage result differs from its sealed receipt")


def _existing_publishable_stage(
    *,
    plan: Mapping[str, Any],
    stage: Mapping[str, Any],
    policy_sha256: str,
    infra_sha256: str,
    effective_workers: int,
    prior_safe_workers: int,
) -> DisposableStageResult | None:
    artifact = dict(
        plan["artifact_namespace"]["stages"][int(stage["ordinal"])]
    )
    receipt_path = Path(str(artifact["stage_receipt"]))
    if not receipt_path.is_absolute():
        receipt_path = resolve_repo_path(receipt_path)
    if not receipt_path.exists() and not receipt_path.is_symlink():
        return None
    receipt = load_ramp_stage_receipt(
        receipt_path,
        expected_policy_sha256=policy_sha256,
        expected_runtime_infra_file_sha256=infra_sha256,
        expected_scope=str(stage["receipt_scope"]),
    )
    if (
        receipt["stage_workload_sha256"] != stage["workload_sha256"]
        or int(receipt["effective_workers"]) != effective_workers
        or int(receipt["prior_safe_workers"]) != prior_safe_workers
    ):
        raise RuntimePolicyError(
            "existing disposable stage receipt breaks controller recovery"
        )
    return DisposableStageResult(
        status=str(receipt["status"]),
        thresholds_passed=bool(receipt["observed"]["thresholds_passed"]),
        resulting_safe_workers=int(receipt["resulting_safe_workers"]),
        stage_receipt_path=str(receipt_path),
    )


def _validate_remote_python_script(script: str, *, label: str) -> None:
    """Fail locally before SSH if an embedded remote program is malformed."""

    try:
        compile(script, f"<agentdojo-disposable-{label}>", "exec")
    except SyntaxError as exc:
        raise RuntimePolicyError(
            f"disposable remote {label} script does not compile"
        ) from exc


def _regular_file(path: str | Path, label: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = resolve_repo_path(candidate)
    info = os.lstat(candidate)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise RuntimePolicyError(f"{label} must be a single-link regular file")
    return candidate


def _portable_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(resolve_repo_path(".").resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _timestamp(value: str | None) -> str:
    text = value or datetime.now(timezone.utc).isoformat()
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise RuntimePolicyError("controller receipt timestamp must have a timezone")
    return text


def _write_once_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    output = Path(path)
    if not output.is_absolute():
        output = resolve_repo_path(output)
    if output.exists() or output.is_symlink():
        raise RuntimePolicyError("controller receipt output must be absent")
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            os.fchmod(handle.fileno(), 0o600)
            json.dump(payload, handle, ensure_ascii=True, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return output


def _write_once_bytes(path: str | Path, payload: bytes) -> Path:
    output = Path(path)
    if not output.is_absolute():
        output = resolve_repo_path(output)
    if output.exists() or output.is_symlink():
        raise RuntimePolicyError("disposable artifact output must be absent")
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        output,
        os.O_CREAT
        | os.O_EXCL
        | os.O_WRONLY
        | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        os.fchmod(descriptor, 0o600)
        os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return output
