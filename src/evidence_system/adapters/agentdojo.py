"""AgentDojo Step 8 smoke planner and executor."""

from __future__ import annotations

import json
import shlex
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping

from evidence_system.adapters.base import AdapterSkeleton, dotenv_source_prefix, is_smoke_phase, json_arg, runner_plan, smoke_role_config
from evidence_system.adapters.agentdojo_runtime_control import (
    RuntimePolicyError,
    job_identity_sha256,
    load_runtime_policy,
    resource_worker_process_binding_sha256,
)
from evidence_system.adapters.runtime import (
    FORMAL_JOB_COMPLETION_MARKER,
    FORMAL_JOB_LAUNCH_MARKER,
    FORMAL_JOB_STARTED_MARKER,
    build_artifact_manifest,
    build_job_paths,
    build_raw_run,
    default_adapter_artifacts,
    file_descriptor,
    formal_job_binding_sha256,
    remote_job_result_dir,
    rsync_remote_tree,
    run_remote_blind_command,
    run_remote_command,
    reconcile_remote_sealed_command,
    recover_remote_sealed_after_reboot,
    run_remote_sealed_command,
    sync_repo_support_files,
    write_environment_snapshot,
    write_llm_call_logs,
)
from evidence_system.contracts.common import utc_now_iso
from evidence_system.contracts.agentdojo_execution_namespace import (
    FORMAL_STAGE_AUTHORIZATION_FIELDS,
)
from evidence_system.core.hashing import sha256_bytes, sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path

if TYPE_CHECKING:
    from evidence_system.adapters.runtime import SmokeExecutionContext
    from evidence_system.orchestrator.jobs import InfraBenchmarkTarget


ADAPTER = AdapterSkeleton(canonical_domain_id="agentdojo", supports_direct_execution=True)

AGENTDOJO_REQUIRED_PROVIDER = "openrouter"
AGENTDOJO_REQUIRED_MODEL = "openai/gpt-5.4-mini"
AGENTDOJO_PACKAGE_VERSION = "0.1.35"
AGENTDOJO_GIT_COMMIT = "a75aba7631d3ca5fb7ab938965c97ead2f9ff84b"
AGENTDOJO_GIT_TREE = "3c74b60f2bad4ff321d864e0c0483f256cc8f8d2"
AGENTDOJO_BENCHMARK_VERSION = "v1.2.2"
AGENTDOJO_ATTACK = "direct"
AGENTDOJO_DEFENSE = "none"
AGENTDOJO_TOOL_DELIMITER = "tool"
AGENTDOJO_TOOL_OUTPUT_FORMAT = "yaml"
AGENTDOJO_SYSTEM_MESSAGE_SHA256 = "a021a92b114c523250d0e52b18adc0aa7b41db7c7628b579b2b8db1df9361837"
AGENTDOJO_EXPECTED_ARTIFACT_TYPES = (
    "trace",
    "post_state",
    "tool_log",
    "file",
    "message",
    "native_evaluator_output",
)


def plan_smoke_execution(
    job: dict[str, Any],
    *,
    target: "InfraBenchmarkTarget",
    agents_config_path: str,
    dotenv_path: str,
    source_bundle_path: str,
    source_bundle: dict[str, Any],
) -> dict[str, Any]:
    role = smoke_role_config(job, agents_config_path=agents_config_path)
    case_bits = str(job["case_unit_id"]).split(":")
    suite = case_bits[1] if len(case_bits) >= 2 else "banking"
    user_task = case_bits[2] if len(case_bits) >= 3 else str(job["task_id"])
    injection_task = case_bits[3] if len(case_bits) >= 4 else str(job["task_id"])
    output_dir = _remote_output_dir(target, job)
    source_entry = _bundle_source_entry(source_bundle, task_id=str(job["task_id"]))
    source_lock = _agentdojo_install_source_lock(source_entry) if job.get("result_namespace") else {}
    runtime_policy = job.get("openrouter_runtime_policy")
    runtime_policy_sha = str(job.get("openrouter_runtime_policy_sha256") or "")
    runtime_policy_file_sha = str(
        job.get("openrouter_runtime_policy_file_sha256") or ""
    )

    requires_locked_runtime = bool(job.get("result_namespace")) and str(
        job.get("phase") or "smoke"
    ) == "full"
    if requires_locked_runtime and (
        not isinstance(runtime_policy, Mapping)
        or not runtime_policy_sha
        or not runtime_policy_file_sha
        or not job.get("execution_lock_sha256")
        or not job.get("execution_policy_sha256")
    ):
        return runner_plan(
            status="blocked",
            command=None,
            target=target,
            expected_artifact_types=AGENTDOJO_EXPECTED_ARTIFACT_TYPES,
            blocking_reason=(
                "Namespaced AgentDojo execution requires a frozen "
                "execution lock/policy bindings plus a frozen openrouter_runtime_policy "
                "with semantic and file SHA-256 bindings."
            ),
            notes=(f"source_bundle={source_bundle_path}",),
        )

    if role["provider"] != AGENTDOJO_REQUIRED_PROVIDER or (is_smoke_phase(job) and role["model"] != AGENTDOJO_REQUIRED_MODEL):
        return runner_plan(
            status="blocked",
            command=None,
            target=target,
            expected_artifact_types=AGENTDOJO_EXPECTED_ARTIFACT_TYPES,
            blocking_reason=(
                "AgentDojo Step 8 smoke runs are pinned to OpenRouter `openai/gpt-5.4-mini`; "
                f"found provider={role['provider']} model={role['model']}."
            ),
            notes=(f"source_bundle={source_bundle_path}",),
        )

    if requires_locked_runtime:
        secret_env_path = str(
            target.benchmark_config.get("secret_env_path") or ""
        )
        if not secret_env_path.startswith("/"):
            return runner_plan(
                status="blocked",
                command=None,
                target=target,
                expected_artifact_types=AGENTDOJO_EXPECTED_ARTIFACT_TYPES,
                blocking_reason=(
                    "Locked AgentDojo execution requires an absolute, provisioned "
                    "secret_env_path outside the repository."
                ),
                notes=(f"source_bundle={source_bundle_path}",),
            )
        # The formal worker opens and parses this mode-0600 file itself.  It is
        # never shell-sourced, so credential bytes cannot become shell syntax.
        prefix = "true"
        secret_path_arg = (
            f" --secret-env-path {shlex.quote(secret_env_path)}"
        )
    else:
        prefix = dotenv_source_prefix(dotenv_path, repo_root=target.remote_workdir)
        secret_path_arg = ""
    install_dir = str(target.benchmark_config.get("install_dir") or target.runner_workdir)
    benchmark_python = f"{install_dir}/.venv/bin/python"
    repo_src = f"{target.remote_workdir}/src"
    model_id = _openrouter_http_model_id(str(role["model"]))
    runtime_control_args = ""
    runtime_control_note = "openrouter_runtime_policy=legacy-smoke-unlocked"
    if isinstance(runtime_policy, Mapping):
        try:
            parsed_runtime_policy = load_runtime_policy(
                runtime_policy,
                expected_semantic_sha256=runtime_policy_sha,
            )
            _validate_sha256(runtime_policy_file_sha, "openrouter_runtime_policy_file_sha256")
            if parsed_runtime_policy.retry.max_attempts != int(role["retry"]) + 1:
                raise RuntimePolicyError(
                    "runtime retry.max_attempts must equal frozen agent retry + 1"
                )
        except RuntimePolicyError as exc:
            return runner_plan(
                status="blocked",
                command=None,
                target=target,
                expected_artifact_types=AGENTDOJO_EXPECTED_ARTIFACT_TYPES,
                blocking_reason=f"Invalid locked OpenRouter runtime policy: {exc}",
                notes=(f"source_bundle={source_bundle_path}",),
            )
        namespace = str(job.get("result_namespace") or "smoke")
        locked_runtime_state_root = str(
            target.benchmark_config.get("runtime_state_root") or ""
        )
        if requires_locked_runtime:
            if not locked_runtime_state_root.startswith("/"):
                return runner_plan(
                    status="blocked",
                    command=None,
                    target=target,
                    expected_artifact_types=AGENTDOJO_EXPECTED_ARTIFACT_TYPES,
                    blocking_reason=(
                        "Locked AgentDojo execution requires an absolute external "
                        "runtime_state_root from the dedicated infra overlay."
                    ),
                    notes=(f"source_bundle={source_bundle_path}",),
                )
            runtime_state_dir = locked_runtime_state_root
        else:
            runtime_state_dir = (
                f"{target.remote_workdir.rstrip('/')}/results/runtime_state/"
                f"{namespace}/openrouter"
            )
        blind_aggregate_root = str(
            target.benchmark_config.get("blind_aggregate_root") or ""
        )
        if requires_locked_runtime and not blind_aggregate_root.startswith("/"):
            return runner_plan(
                status="blocked",
                command=None,
                target=target,
                expected_artifact_types=AGENTDOJO_EXPECTED_ARTIFACT_TYPES,
                blocking_reason=(
                    "Locked AgentDojo execution requires an absolute "
                    "blind_aggregate_root outside the sealed raw tree."
                ),
                notes=(f"source_bundle={source_bundle_path}",),
            )
        runtime_control_args = (
            f" --openrouter-runtime-policy-json {json_arg(dict(runtime_policy))}"
            f" --openrouter-runtime-policy-sha256 {shlex.quote(runtime_policy_sha)}"
            f" --openrouter-runtime-policy-file-sha256 {shlex.quote(runtime_policy_file_sha)}"
            f" --runtime-state-dir {shlex.quote(runtime_state_dir)}"
            f" --blind-aggregate-root {shlex.quote(blind_aggregate_root)}"
        )
        runtime_control_note = (
            f"openrouter_runtime_policy_sha256={runtime_policy_sha} "
            f"file_sha256={runtime_policy_file_sha}"
        )
    command = (
        f"cd {shlex.quote(target.remote_workdir)} && {prefix} && "
        f"PYTHONHASHSEED={int(job['seed'])} PYTHONPATH={shlex.quote(repo_src)} "
        f"{shlex.quote(benchmark_python)} -m evidence_system.adapters.agentdojo_worker "
        f"--job-json {json_arg(job)} "
        f"--source-entry-json {json_arg(source_entry or {})} "
        f"--output-dir {shlex.quote(output_dir)} "
        f"--suite {shlex.quote(suite)} "
        f"--user-task {shlex.quote(user_task)} "
        f"--injection-task {shlex.quote(injection_task)} "
        f"--agentdojo-package-version {AGENTDOJO_PACKAGE_VERSION} "
        f"--agentdojo-git-commit {AGENTDOJO_GIT_COMMIT} "
        f"--agentdojo-git-tree {AGENTDOJO_GIT_TREE} "
        f"--agentdojo-source-lock-json {json_arg(source_lock)} "
        f"--benchmark-version {AGENTDOJO_BENCHMARK_VERSION} "
        f"--model-id {shlex.quote(model_id)} "
        f"--temperature {shlex.quote(str(role['temperature']))} "
        f"--max-tokens {shlex.quote(str(role['max_tokens']))} "
        f"--timeout-seconds {shlex.quote(str(role['timeout_seconds']))} "
        f"--retry {shlex.quote(str(role['retry']))} "
        f"--openrouter-api-key-env {shlex.quote(str(role['api_key_env']))} "
        f"{secret_path_arg} "
        f"--tool-delimiter {AGENTDOJO_TOOL_DELIMITER} "
        f"--tool-output-format {AGENTDOJO_TOOL_OUTPUT_FORMAT} "
        f"--system-message-sha256 {AGENTDOJO_SYSTEM_MESSAGE_SHA256} "
        f"--defense {AGENTDOJO_DEFENSE} "
        f"--attack {AGENTDOJO_ATTACK}"
        f"{runtime_control_args}"
    )
    return runner_plan(
        status="runnable",
        command=command,
        target=target,
        expected_artifact_types=AGENTDOJO_EXPECTED_ARTIFACT_TYPES,
        notes=(
            f"source_bundle={source_bundle_path}",
            f"requested_model={role['provider']}::{role['model']}",
            (
                f"agentdojo={AGENTDOJO_PACKAGE_VERSION} benchmark={AGENTDOJO_BENCHMARK_VERSION} "
                f"attack={AGENTDOJO_ATTACK} defense={AGENTDOJO_DEFENSE} "
                f"tool_delimiter={AGENTDOJO_TOOL_DELIMITER} tool_output_format={AGENTDOJO_TOOL_OUTPUT_FORMAT}"
            ),
            "worker starts a local OpenAI-compatible proxy on the VPS and routes AgentDojo LOCAL calls to OpenRouter",
            runtime_control_note,
            "blind health ledger excludes prompts, responses, trajectories, case IDs, and evaluator fields",
            "native artifacts expected: native_evaluator_input.json, native_evaluator_output.json, proxy_calls/*.json, trace_logs/**.json",
        ),
    )


def _agentdojo_install_source_lock(source_entry: Mapping[str, Any] | None) -> dict[str, Any]:
    """Extract the compact pinned-source inventory needed by the remote worker."""

    if not source_entry:
        raise ValueError("namespaced AgentDojo jobs require a source-bundle entry")
    draft_input = source_entry.get("draft_input")
    if not isinstance(draft_input, Mapping):
        raise ValueError("namespaced AgentDojo source entry requires draft_input")
    raw_manifest_ref = str(draft_input.get("raw_case_manifest_path") or "")
    raw_manifest_path = resolve_repo_path(raw_manifest_ref)
    raw_manifest = json.loads(raw_manifest_path.read_text(encoding="utf-8"))
    raw_case_dir = raw_manifest_path.parent / "raw_case"
    packet_files = {str(item) for item in raw_manifest.get("packet_files") or []}
    extraction_relative = "derived/extraction_manifest.json"
    if extraction_relative in packet_files:
        extraction_path = raw_case_dir / extraction_relative
        extraction = json.loads(extraction_path.read_text(encoding="utf-8"))
        bundle = extraction.get("shared_source_bundle")
        if not isinstance(bundle, Mapping):
            raise ValueError("AgentDojo extraction has no shared-source binding")
        if (
            bundle.get("package_version") != AGENTDOJO_PACKAGE_VERSION
            or bundle.get("git_commit") != AGENTDOJO_GIT_COMMIT
            or bundle.get("git_tree") != AGENTDOJO_GIT_TREE
        ):
            raise ValueError(
                "AgentDojo extraction release identity does not match runtime pin"
            )
        expected_extraction_sha = str(
            (raw_manifest.get("sha256_per_file") or {}).get(extraction_relative) or ""
        )
        if expected_extraction_sha != sha256_file(extraction_path):
            raise ValueError("AgentDojo extraction manifest hash differs")
        descriptors = {}
        for item in extraction.get("source_files_used") or []:
            if not isinstance(item, Mapping):
                raise ValueError("AgentDojo extracted source-file entry is invalid")
            repo_path = str(item.get("repo_path") or "")
            digest = str(item.get("sha256") or "").removeprefix("sha256:")
            previous = descriptors.setdefault(repo_path, digest)
            if previous != digest:
                raise ValueError(
                    f"conflicting AgentDojo source hashes for {repo_path}"
                )
        if not descriptors:
            raise ValueError("AgentDojo extraction contains no install-file hashes")
        for repo_path, digest in descriptors.items():
            relative = Path(repo_path)
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or not repo_path.startswith("src/agentdojo/")
            ):
                raise ValueError(f"unsafe AgentDojo source path: {repo_path!r}")
            if len(digest) != 64:
                raise ValueError(f"invalid AgentDojo source SHA-256: {repo_path}")
        return {
            "agentdojo_git_commit": AGENTDOJO_GIT_COMMIT,
            "agentdojo_git_tree": AGENTDOJO_GIT_TREE,
            "files": [
                {"repo_path": repo_path, "sha256": digest}
                for repo_path, digest in sorted(descriptors.items())
            ],
        }

    selected_relative = (
        "derived/selected_task_source.json"
        if "derived/selected_task_source.json" in packet_files
        else "selected_task_source.json"
        if "selected_task_source.json" in packet_files
        else None
    )
    if selected_relative is None:
        raise ValueError(
            "namespaced AgentDojo raw case has no selected task source"
        )
    selected_path = raw_case_dir / selected_relative
    selected = json.loads(selected_path.read_text(encoding="utf-8"))
    if selected.get("agentdojo_package_version") != AGENTDOJO_PACKAGE_VERSION:
        raise ValueError("AgentDojo selected source package version does not match runtime pin")
    if selected.get("agentdojo_git_commit") != AGENTDOJO_GIT_COMMIT:
        raise ValueError("AgentDojo selected source commit does not match runtime pin")

    descriptors: dict[str, str] = {}

    def collect(value: Any) -> None:
        if isinstance(value, Mapping):
            repo_path = value.get("repo_path")
            digest = value.get("sha256")
            if isinstance(repo_path, str) and isinstance(digest, str):
                normalized = digest.removeprefix("sha256:")
                previous = descriptors.setdefault(repo_path, normalized)
                if previous != normalized:
                    raise ValueError(f"conflicting AgentDojo source hashes for {repo_path}")
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    closure_relative = "derived/source_closure_manifest.json"
    if closure_relative in packet_files:
        closure_path = raw_case_dir / closure_relative
        closure = json.loads(closure_path.read_text(encoding="utf-8"))
        if (
            closure.get("agentdojo_package_version") != AGENTDOJO_PACKAGE_VERSION
            or closure.get("agentdojo_git_commit") != AGENTDOJO_GIT_COMMIT
        ):
            raise ValueError(
                "AgentDojo source closure release identity does not match runtime pin"
            )
        for item in closure.get("files") or []:
            if not isinstance(item, Mapping):
                raise ValueError("AgentDojo source closure file entry is invalid")
            collect(item)
            repo_path = str(item.get("repo_path") or "")
            archive_path = str(item.get("archive_path") or "")
            digest = str(item.get("sha256") or "").removeprefix("sha256:")
            expected_archive_path = f"official/{repo_path}"
            if archive_path != expected_archive_path:
                raise ValueError(
                    f"AgentDojo source closure archive path differs for {repo_path}"
                )
            copied_hash = str(
                (raw_manifest.get("sha256_per_file") or {}).get(archive_path) or ""
            )
            if copied_hash != digest or sha256_file(raw_case_dir / archive_path) != digest:
                raise ValueError(
                    f"AgentDojo source closure copied hash differs for {repo_path}"
                )
    else:
        collect(selected.get("user_task"))
        collect(selected.get("injection_task"))
        collect(selected.get("source_files"))
    if not descriptors:
        raise ValueError("AgentDojo selected source contains no install-file hashes")
    for repo_path, digest in descriptors.items():
        relative = Path(repo_path)
        if relative.is_absolute() or ".." in relative.parts or not repo_path.startswith("src/agentdojo/"):
            raise ValueError(f"unsafe AgentDojo source path: {repo_path!r}")
        if len(digest) != 64:
            raise ValueError(f"invalid AgentDojo source SHA-256: {repo_path}")
    return {
        "agentdojo_git_commit": AGENTDOJO_GIT_COMMIT,
        "agentdojo_git_tree": AGENTDOJO_GIT_TREE,
        "files": [
            {"repo_path": repo_path, "sha256": digest}
            for repo_path, digest in sorted(descriptors.items())
        ],
    }


def execute_smoke_job(
    job: dict[str, Any],
    *,
    target: "InfraBenchmarkTarget",
    execution_plan: dict[str, Any],
    context: "SmokeExecutionContext",
) -> dict[str, Any]:
    if _is_formal_execution_job(job):
        return _execute_formal_sealed_job(
            job,
            target=target,
            execution_plan=execution_plan,
            context=context,
        )

    paths = build_job_paths(job)
    shutil.rmtree(paths.root, ignore_errors=True)
    paths = build_job_paths(job)
    # AgentDojo credentials are provisioned only in the locked absolute VPS
    # secret path; repository sync must never copy a controller dotenv file.
    sync_repo_support_files(target, include_dotenv=False)
    _, environment_hash = write_environment_snapshot(target=target, job=job, output_path=paths.environment_path)
    shutil.rmtree(paths.native_run_dir, ignore_errors=True)
    paths.native_run_dir.mkdir(parents=True, exist_ok=True)
    remote_output_dir = _remote_output_dir(target, job)
    run_remote_command(
        target,
        f"rm -rf {shlex.quote(remote_output_dir)} && mkdir -p {shlex.quote(remote_output_dir)}",
        stdout_path=paths.logs_dir / "prepare.stdout.log",
        stderr_path=paths.logs_dir / "prepare.stderr.log",
    )
    started_at = utc_now_iso()
    completed = run_remote_command(
        target,
        str(execution_plan["runner_command"]),
        stdout_path=paths.stdout_log,
        stderr_path=paths.stderr_log,
    )
    completed_exit_code = completed.returncode
    ended_at = utc_now_iso()
    rsync_remote_tree(target, remote_output_dir, paths.native_run_dir)

    summary_path = paths.native_run_dir / "run_summary.json"
    if not summary_path.exists():
        raise RuntimeError(f"AgentDojo worker did not produce run_summary.json for {job['job_id']}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if completed_exit_code != 0 or summary.get("status") == "error":
        raise RuntimeError(
            f"AgentDojo worker failed for {job['job_id']} "
            f"exit_code={completed_exit_code}: {summary.get('error_message') or summary.get('status')}"
        )
    llm_path, _ = write_llm_call_logs(
        events=_agentdojo_llm_events(paths.native_run_dir),
        job=job,
        context=context,
        output_dir=paths.llm_dir,
    )
    status = "COMPLETED" if summary.get("status") == "completed" else "INFRA_EXCLUDED"
    native_label = None
    native_score = None
    if status == "COMPLETED":
        benign_utility = bool(summary.get("benign_utility"))
        injected_utility = bool(summary.get("injected_utility"))
        injected_security = bool(summary.get("injected_security"))
        success = benign_utility and injected_utility and not injected_security
        native_label = "success" if success else "fail"
        native_score = 1.0 if success else 0.0
    descriptors = _agentdojo_artifacts(paths.native_run_dir) + default_adapter_artifacts(paths)
    manifest, manifest_path, manifest_sha = build_artifact_manifest(
        job=job,
        context=context,
        target=target,
        descriptors=descriptors,
        producer_command=str(execution_plan["runner_command"]),
        started_at=started_at,
        output_path=paths.artifact_manifest_path,
        environment_hash=environment_hash,
    )
    raw_run, raw_run_path = build_raw_run(
        job=job,
        target=target,
        artifact_manifest_path=manifest_path,
        artifact_manifest_sha256=manifest_sha,
        raw_run_path=paths.raw_run_path,
        started_at=started_at,
        ended_at=ended_at,
        status=status,
        diagnostic_status="completed" if status == "COMPLETED" else "infra_excluded",
        appendix_failure_class="none" if status == "COMPLETED" else "infra_pre_run",
        native_label=native_label,
        native_score=native_score,
        episode_ids=[
            f"agentdojo:benign:{job['task_id']}",
            f"agentdojo:injection_task_as_user_task:{job['task_id']}",
            f"agentdojo:injected:{job['task_id']}",
        ],
        llm_calls_log_path=llm_path,
    )
    return {
        "status": "completed" if status == "COMPLETED" else "infra_excluded",
        "completed_exit_code": completed_exit_code,
        "raw_run_path": str(raw_run_path),
        "artifact_manifest_path": str(manifest_path),
        "raw_run": raw_run,
        "artifact_manifest": manifest,
    }


def _execute_formal_sealed_job(
    job: Mapping[str, Any],
    *,
    target: "InfraBenchmarkTarget",
    execution_plan: Mapping[str, Any],
    context: "SmokeExecutionContext",
) -> dict[str, Any]:
    """Run or reconcile one formal job while keeping all evidence on the VPS."""

    authorized_command, authorization = _prepare_remote_stage_authorization(
        job,
        target=target,
        execution_plan=execution_plan,
    )
    auth_payload = dict(authorization["payload"])
    stage_id = str(auth_payload["stage_id"])
    session_id = str(auth_payload["session_id"])
    authorization_sha = str(authorization["file_sha256"])
    binding = formal_job_binding_sha256(job)
    canonical_root = _remote_output_dir(target, job)
    controls = _formal_remote_evidence_paths(
        target, job=job, session_id=session_id
    )
    worker_command = (
        f"{authorized_command} --output-dir {shlex.quote(controls['attempt_root'])}"
    )
    execution_context = {
        "schema_version": "agentdojo_formal_execution_context/v1",
        "machine_id": target.machine_id,
        "machine_role": target.machine_role,
        "ssh_host": target.ssh_host,
        "ssh_port": int(target.ssh_port),
        "remote_workdir": target.remote_workdir,
        "runner_workdir": target.runner_workdir,
        "benchmark_name": target.benchmark_name,
        "benchmark_config_hash": target.benchmark_config_hash,
        "source_bundle_hash": context.source_bundle_hash,
        "official_split_hash": context.official_split_hash,
        "producer_command_sha256": sha256_bytes(worker_command.encode("utf-8")),
    }
    verified = _run_remote_formal_postprocessor(
        target,
        operation="verify",
        job=job,
        execution_context=execution_context,
        canonical_root=canonical_root,
        controls=controls,
        authorization_sha256=authorization_sha,
        stage_id=stage_id,
        session_id=session_id,
        worker_exit_code=0,
        failure_category="worker_error",
    )
    if verified["status"] == "canonical_reused":
        return _formal_execution_result(verified, reused=True)
    if verified["status"] != "canonical_absent":
        raise RuntimeError("formal canonical verifier returned an invalid state")

    state, marker = _read_remote_formal_job_state(
        target, controls["attempt_root"]
    )
    if state == "absent":
        launch = {
            "schema_version": "agentdojo_formal_job_launch_intent/v1",
            "created_at": utc_now_iso(),
            "stage_authorization_sha256": authorization_sha,
            **_formal_marker_binding(job),
        }
        launched = run_remote_blind_command(
            target,
            _formal_launch_intent_command(
                controls["attempt_root"],
                launch,
                attempt_namespace_root=controls["attempt_namespace_root"],
                python_bin=(
                    f"{str(target.benchmark_config.get('install_dir') or target.runner_workdir).rstrip('/')}"
                    "/.venv/bin/python"
                ),
            ),
            transient_retry_attempts=1,
            maximum_stdout_bytes=0,
            maximum_stderr_bytes=4096,
        )
        state, marker = _read_remote_formal_job_state(
            target, controls["attempt_root"]
        )
        if state != "launch_intent":
            raise RuntimeError(
                "formal attempt launch-intent outcome is unknown and replay is forbidden: "
                f"exit_code={launched.returncode} state={state}"
            )
        if marker != launch:
            raise RuntimeError("formal attempt launch intent differs from this session")
    if state == "launch_intent":
        _validate_formal_marker_binding(
            marker,
            job,
            state="launch_intent",
            expected_stage_authorization_sha256=authorization_sha,
        )
        completed = run_remote_sealed_command(
            target,
            worker_command,
            sealed_job_root=controls["attempt_root"],
            stage_id=stage_id,
            session_id=session_id,
            job_binding_sha256=binding,
            stage_authorization_sha256=authorization_sha,
            formal_timeout_seconds=int(
                auth_payload["formal_wall_clock_timeout_seconds"]
            ),
            kill_grace_seconds=int(auth_payload["kill_grace_seconds"]),
        )
    elif state == "started":
        _validate_formal_marker_binding(
            marker,
            job,
            state="started",
            expected_stage_authorization_sha256=authorization_sha,
        )
        completed = reconcile_remote_sealed_command(
            target,
            sealed_job_root=controls["attempt_root"],
            session_id=session_id,
            maximum_wait_seconds=(
                int(auth_payload["formal_wall_clock_timeout_seconds"])
                + int(auth_payload["kill_grace_seconds"])
                + 300
            ),
        )
    else:
        raise RuntimeError(
            f"formal attempt namespace is not reconcilable: state={state}"
        )
    if completed.boot_changed:
        completed = recover_remote_sealed_after_reboot(
            target,
            sealed_job_root=controls["attempt_root"],
            session_id=session_id,
        )
    if not completed.group_gone:
        raise RuntimeError(
            "formal worker outcome is unresolved because its process group is not gone: "
            f"outcome={completed.outcome}"
        )
    if completed.returncode == 0:
        postprocessed = _run_remote_formal_postprocessor(
            target,
            operation="success",
            job=job,
            execution_context=execution_context,
            canonical_root=canonical_root,
            controls=controls,
            authorization_sha256=authorization_sha,
            stage_id=stage_id,
            session_id=session_id,
            worker_exit_code=0,
            failure_category="worker_error",
        )
        if postprocessed["status"] not in {
            "canonical_published", "canonical_reused",
        }:
            raise RuntimeError("formal success postprocessor did not publish canonical evidence")
        return _formal_execution_result(
            postprocessed,
            reused=postprocessed["status"] == "canonical_reused",
        )
    category = (
        "boot_changed"
        if completed.outcome == "boot_changed"
        else "timeout"
        if completed.timed_out
        else "worker_error"
    )
    archived = _run_remote_formal_postprocessor(
        target,
        operation="failure",
        job=job,
        execution_context=execution_context,
        canonical_root=canonical_root,
        controls=controls,
        authorization_sha256=authorization_sha,
        stage_id=stage_id,
        session_id=session_id,
        worker_exit_code=completed.returncode,
        failure_category=category,
    )
    if archived["status"] != "failed_attempt_archived":
        raise RuntimeError("formal failed attempt could not be archived")
    raise RuntimeError(
        "formal AgentDojo attempt failed and was sealed for post-run diagnosis: "
        f"outcome={completed.outcome} archive_tree_sha256="
        f"{archived['archive_tree_sha256']}"
    )


def _prepare_remote_stage_authorization(
    job: Mapping[str, Any],
    *,
    target: "InfraBenchmarkTarget",
    execution_plan: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Install content-blind stage controls and inject them outside job JSON."""

    payload_raw = execution_plan.get("locked_stage_authorization")
    context_raw = execution_plan.get("locked_stage_authorization_context")
    local_path_raw = execution_plan.get("locked_stage_authorization_path")
    expected_sha = str(
        execution_plan.get("locked_stage_authorization_sha256") or ""
    )
    if not isinstance(payload_raw, Mapping) or set(payload_raw) != (
        FORMAL_STAGE_AUTHORIZATION_FIELDS
    ):
        raise RuntimeError("formal execution plan has no exact stage authorization")
    if not isinstance(context_raw, Mapping) or set(context_raw) != {
        "authorization_remote_path",
        "namespace_init_local_path",
        "previous_health_local_path",
        "plan_index_local_path",
    }:
        raise RuntimeError("formal execution plan has no exact authorization context")
    local_path = resolve_repo_path(str(local_path_raw or ""))
    if (
        local_path.is_symlink()
        or not local_path.is_file()
        or local_path.stat().st_nlink != 1
        or sha256_file(local_path) != expected_sha
    ):
        raise RuntimeError("formal stage authorization local bytes are stale")
    payload = json.loads(local_path.read_text(encoding="utf-8"))
    if payload != dict(payload_raw):
        raise RuntimeError("formal stage authorization payload differs from its file")
    if (
        payload.get("execution_lock_sha256")
        != str(job.get("execution_lock_sha256") or "")
        or payload.get("execution_policy_sha256")
        != str(job.get("execution_policy_sha256") or "")
        or formal_job_binding_sha256(job)
        not in list(payload.get("allowed_job_binding_sha256") or [])
    ):
        raise RuntimeError("formal stage authorization does not admit this job")

    runtime_state_root = str(payload.get("runtime_state_root") or "")
    locked_runtime_state_root = str(
        target.benchmark_config.get("runtime_state_root") or ""
    )
    if (
        not runtime_state_root.startswith("/")
        or runtime_state_root != locked_runtime_state_root
    ):
        raise RuntimeError("formal stage authorization runtime-state root differs")
    authorization_remote_path = str(
        context_raw["authorization_remote_path"]
    )
    expected_authorization_remote = (
        f"{runtime_state_root.rstrip('/')}/formal-control/stage-authorizations/"
        f"{payload['stage_id']}-{payload['session_id']}.json"
    )
    if authorization_remote_path != expected_authorization_remote:
        raise RuntimeError("formal stage authorization remote path is noncanonical")

    controls = [
        (
            resolve_repo_path(str(context_raw["namespace_init_local_path"])),
            str(dict(payload["namespace_init_receipt"])["path"]),
            str(dict(payload["namespace_init_receipt"])["sha256"]),
        ),
        (local_path, authorization_remote_path, expected_sha),
    ]
    previous = payload.get("previous_health_receipt")
    previous_local = context_raw.get("previous_health_local_path")
    if previous is None:
        if previous_local is not None:
            raise RuntimeError("formal stage authorization has unexpected health context")
    else:
        if not isinstance(previous, Mapping) or previous_local is None:
            raise RuntimeError("formal stage authorization health context is missing")
        controls.insert(
            1,
            (
                resolve_repo_path(str(previous_local)),
                str(previous["path"]),
                str(previous["sha256"]),
            ),
        )
    for local_source, remote_destination, digest in controls:
        _install_remote_formal_control_file(
            target,
            local_source=local_source,
            remote_destination=remote_destination,
            expected_sha256=digest,
            runtime_state_root=runtime_state_root,
        )

    blind_group = str(target.benchmark_config.get("blind_group") or "")
    if not blind_group:
        raise RuntimeError("formal stage authorization requires a blind group")
    resource_stage_token = resource_worker_process_binding_sha256(
        execution_scope_sha256=str(payload["execution_lock_sha256"]),
        stage_id=str(payload["stage_id"]),
        session_id=str(payload["session_id"]),
        stage_binding_sha256=expected_sha,
    )
    command = (
        f"{str(execution_plan['runner_command'])}"
        f" --blind-group {shlex.quote(blind_group)}"
        f" --stage-authorization {shlex.quote(authorization_remote_path)}"
        f" --stage-authorization-sha256 {shlex.quote(expected_sha)}"
        f" --resource-stage-token {shlex.quote(resource_stage_token)}"
    )
    return command, {"payload": payload, "file_sha256": expected_sha}


def _formal_remote_evidence_paths(
    target: "InfraBenchmarkTarget",
    *,
    job: Mapping[str, Any],
    session_id: str,
) -> dict[str, str]:
    runtime_root = str(target.benchmark_config.get("runtime_state_root") or "")
    raw_root = str(target.benchmark_config.get("remote_raw_root") or "")
    blind_root = str(target.benchmark_config.get("blind_aggregate_root") or "")
    failed_root = str(
        target.benchmark_config.get("failed_attempt_archive_root") or ""
    )
    for value, label in (
        (runtime_root, "runtime_state_root"),
        (raw_root, "remote_raw_root"),
        (blind_root, "blind_aggregate_root"),
        (failed_root, "failed_attempt_archive_root"),
    ):
        if not value.startswith("/") or "\n" in value:
            raise RuntimeError(f"formal {label} must be a locked absolute path")
    if len({runtime_root, raw_root, blind_root, failed_root}) != 4:
        raise RuntimeError("formal evidence control roots must be distinct")
    binding = formal_job_binding_sha256(job)
    attempt_namespace = f"{runtime_root.rstrip('/')}/sealed-attempts"
    return {
        "attempt_namespace_root": attempt_namespace,
        "attempt_root": f"{attempt_namespace}/{binding}/{session_id}",
        "canonical_root": f"{raw_root.rstrip('/')}/{binding}",
        "completion_journal": (
            f"{blind_root.rstrip('/')}/formal-completion-journal.v2.jsonl"
        ),
        "failed_journal": (
            f"{blind_root.rstrip('/')}/formal-failed-attempt-journal.v1.jsonl"
        ),
        "failed_archive_root": failed_root,
        "lifecycle_lock": f"{blind_root.rstrip('/')}/.canonical-lifecycle.lock",
    }


def _run_remote_formal_postprocessor(
    target: "InfraBenchmarkTarget",
    *,
    operation: str,
    job: Mapping[str, Any],
    execution_context: Mapping[str, Any],
    canonical_root: str,
    controls: Mapping[str, str],
    authorization_sha256: str,
    stage_id: str,
    session_id: str,
    worker_exit_code: int,
    failure_category: str,
) -> dict[str, Any]:
    install_dir = str(
        target.benchmark_config.get("install_dir") or target.runner_workdir
    )
    python_bin = f"{install_dir.rstrip('/')}/.venv/bin/python"
    blind_group = str(target.benchmark_config.get("blind_group") or "")
    if not blind_group:
        raise RuntimeError("formal postprocessor requires the locked blind group")
    command = (
        f"cd {shlex.quote(target.remote_workdir)} && "
        f"PYTHONPATH={shlex.quote(f'{target.remote_workdir}/src')} "
        f"{shlex.quote(python_bin)} -m "
        "evidence_system.adapters.agentdojo_formal_postprocessor "
        f"--operation {shlex.quote(operation)} "
        f"--job-json {json_arg(dict(job))} "
        f"--execution-context-json {json_arg(dict(execution_context))} "
        f"--attempt-root {shlex.quote(controls['attempt_root'])} "
        f"--canonical-root {shlex.quote(canonical_root)} "
        f"--completion-index {shlex.quote(controls['completion_journal'])} "
        f"--failed-attempt-index {shlex.quote(controls['failed_journal'])} "
        f"--failed-archive-root {shlex.quote(controls['failed_archive_root'])} "
        f"--lifecycle-lock {shlex.quote(controls['lifecycle_lock'])} "
        f"--stage-authorization-sha256 {shlex.quote(authorization_sha256)} "
        f"--stage-id {shlex.quote(stage_id)} "
        f"--session-id {shlex.quote(session_id)} "
        f"--blind-group {shlex.quote(blind_group)} "
        f"--worker-exit-code {int(worker_exit_code)} "
        f"--failure-category {shlex.quote(failure_category)}"
    )
    completed = run_remote_blind_command(
        target,
        command,
        timeout_seconds=300,
        transient_retry_attempts=1,
        maximum_stdout_bytes=4096,
        maximum_stderr_bytes=4096,
    )
    if completed.stderr:
        raise RuntimeError("formal postprocessor emitted stderr")
    result = _parse_formal_postprocessor_result(completed.stdout or "")
    if result["status"] == "error":
        raise RuntimeError(
            "formal postprocessor failed closed: "
            f"error_type={result['error_type']} error_sha256={result['error_sha256']}"
        )
    if completed.returncode != 0:
        raise RuntimeError("formal postprocessor exit code differs from its result")
    return result


def _parse_formal_postprocessor_result(value: str) -> dict[str, Any]:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise RuntimeError("formal postprocessor returned invalid blind JSON") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("formal postprocessor result is not an object")
    status = str(payload.get("status") or "")
    expected_by_status = {
        "canonical_absent": {
            "schema_version", "status", "execution_lock_sha256",
            "execution_policy_sha256", "job_binding_sha256",
            "job_identity_sha256", "blind_only",
        },
        "canonical_published": {
            "schema_version", "status", "execution_lock_sha256",
            "execution_policy_sha256", "job_binding_sha256",
            "job_identity_sha256", "artifact_file_count",
            "artifact_tree_sha256", "artifact_total_bytes",
            "native_episode_count", "completion_marker_semantic_sha256",
            "blind_only",
        },
        "canonical_reused": {
            "schema_version", "status", "execution_lock_sha256",
            "execution_policy_sha256", "job_binding_sha256",
            "job_identity_sha256", "artifact_file_count",
            "artifact_tree_sha256", "artifact_total_bytes",
            "native_episode_count", "completion_marker_semantic_sha256",
            "blind_only",
        },
        "failed_attempt_archived": {
            "schema_version", "status", "attempt_identity_sha256",
            "attempt_tree_sha256", "archive_tree_sha256", "blind_only",
        },
        "error": {
            "schema_version", "status", "error_type", "error_sha256",
            "blind_only",
        },
    }
    expected = expected_by_status.get(status)
    if expected is None or set(payload) != expected or payload.get(
        "schema_version"
    ) != "agentdojo_formal_postprocessor_result/v1":
        raise RuntimeError("formal postprocessor blind result fields differ")
    if payload.get("blind_only") is not True:
        raise RuntimeError("formal postprocessor result is not blind-only")
    return payload


def _formal_execution_result(
    result: Mapping[str, Any], *, reused: bool
) -> dict[str, Any]:
    native_episode_count = result.get("native_episode_count")
    if native_episode_count != 3:
        raise RuntimeError(
            "formal postprocessor did not prove exactly three native episodes"
        )
    return {
        "status": "sealed_remote_reused" if reused else "sealed_remote_completed",
        **{
            field: result[field]
            for field in (
                "execution_lock_sha256", "execution_policy_sha256",
                "job_identity_sha256", "job_binding_sha256",
                "artifact_tree_sha256", "artifact_file_count",
                "artifact_total_bytes", "completion_marker_semantic_sha256",
            )
        },
        "native_episode_count": native_episode_count,
        "sealed_remote_evidence": True,
        "raw_evidence_synced_to_controller": False,
        "blind_completion_fields_only": True,
    }


def _install_remote_formal_control_file(
    target: "InfraBenchmarkTarget",
    *,
    local_source: Path,
    remote_destination: str,
    expected_sha256: str,
    runtime_state_root: str,
) -> None:
    """Create-once a mode-0600 remote control file with file+directory fsync."""

    _validate_sha256(expected_sha256, "formal control expected_sha256")
    if (
        local_source.is_symlink()
        or not local_source.is_file()
        or local_source.stat().st_nlink != 1
        or sha256_file(local_source) != expected_sha256
    ):
        raise RuntimeError("formal control source is missing, linked, or stale")
    control_root = f"{runtime_state_root.rstrip('/')}/formal-control"
    if not remote_destination.startswith(f"{control_root}/"):
        raise RuntimeError("formal control destination escapes runtime-state control root")
    install_dir = str(
        target.benchmark_config.get("install_dir") or target.runner_workdir
    )
    python_bin = f"{install_dir.rstrip('/')}/.venv/bin/python"
    script = """
import hashlib, os, pathlib, stat, sys, uuid
root = pathlib.Path(sys.argv[1])
dest = pathlib.Path(sys.argv[2])
expected = sys.argv[3]
data = sys.stdin.buffer.read()
if hashlib.sha256(data).hexdigest() != expected:
    raise SystemExit(41)
if not root.is_absolute() or not dest.is_absolute() or root not in dest.parents:
    raise SystemExit(42)
current = pathlib.Path(root.anchor)
for part in root.parts[1:]:
    current = current / part
    info = os.lstat(current)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise SystemExit(43)
if stat.S_IMODE(os.lstat(root).st_mode) != 0o700:
    raise SystemExit(44)
relative_parent = dest.parent.relative_to(root)
current = root
for part in relative_parent.parts:
    current = current / part
    try:
        os.mkdir(current, 0o700)
    except FileExistsError:
        pass
    info = os.lstat(current)
    if (stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode)
            or stat.S_IMODE(info.st_mode) != 0o700 or info.st_uid != os.geteuid()):
        raise SystemExit(45)
if dest.exists() or dest.is_symlink():
    info = os.lstat(dest)
    if (stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600
            or hashlib.sha256(dest.read_bytes()).hexdigest() != expected):
        raise SystemExit(46)
else:
    temporary = dest.parent / ('.' + dest.name + '.' + uuid.uuid4().hex + '.tmp')
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(temporary, flags, 0o600)
    try:
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    try:
        os.link(temporary, dest, follow_symlinks=False)
    finally:
        os.unlink(temporary)
    descriptor = os.open(dest.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
print('CONTROL_FILE_READY')
""".strip()
    command = (
        f"{shlex.quote(python_bin)} -c {shlex.quote(script)} "
        f"{shlex.quote(runtime_state_root)} "
        f"{shlex.quote(remote_destination)} {shlex.quote(expected_sha256)}"
    )
    result = run_remote_blind_command(
        target,
        command,
        stdin_text=local_source.read_text(encoding="utf-8"),
        transient_retry_attempts=1,
        maximum_stdout_bytes=64,
        maximum_stderr_bytes=0,
    )
    if result.returncode != 0 or result.stdout.strip() != "CONTROL_FILE_READY":
        raise RuntimeError(
            "formal remote control file publication failed: "
            f"exit_code={result.returncode}"
        )


def _is_formal_execution_job(job: Mapping[str, Any]) -> bool:
    return (
        str(job.get("phase") or "") == "full"
        and bool(job.get("result_namespace"))
        and bool(job.get("execution_lock_sha256"))
        and bool(job.get("execution_policy_sha256"))
    )


def _formal_marker_binding(job: Mapping[str, Any]) -> dict[str, str]:
    return {
        "execution_lock_sha256": str(job.get("execution_lock_sha256") or ""),
        "execution_policy_sha256": str(job.get("execution_policy_sha256") or ""),
        "job_binding_sha256": formal_job_binding_sha256(job),
        "job_identity_sha256": job_identity_sha256(job),
    }


def _validate_formal_marker_binding(
    marker: Mapping[str, Any] | None,
    job: Mapping[str, Any],
    *,
    state: str,
    expected_stage_authorization_sha256: str | None = None,
) -> None:
    if not isinstance(marker, Mapping):
        raise RuntimeError(f"formal {state} marker is missing")
    schemas = {
        "launch_intent": "agentdojo_formal_job_launch_intent/v1",
        "started": "agentdojo_formal_job_started/v2",
        "completed": "agentdojo_formal_job_completion/v1",
    }
    if marker.get("schema_version") != schemas[state]:
        raise RuntimeError(f"formal {state} marker schema is invalid")
    for key, value in _formal_marker_binding(job).items():
        if marker.get(key) != value:
            raise RuntimeError(f"formal {state} marker has stale {key}")
    exact_fields = {
        "launch_intent": {
            "schema_version",
            "created_at",
            "stage_authorization_sha256",
            "execution_lock_sha256",
            "execution_policy_sha256",
            "job_binding_sha256",
            "job_identity_sha256",
        },
        "started": {
            "schema_version",
            "started_at",
            "deadline_at",
            "formal_wall_clock_timeout_seconds",
            "pid",
            "linux_starttime_ticks",
            "stage_authorization_sha256",
            "formal_stage_id",
            "formal_stage_session_id",
            "execution_lock_sha256",
            "execution_policy_sha256",
            "job_binding_sha256",
            "job_identity_sha256",
        },
        "completed": {
            "schema_version",
            "completed_at",
            "execution_lock_sha256",
            "execution_policy_sha256",
            "job_binding_sha256",
            "job_identity_sha256",
            "stage_authorization_sha256",
            "artifact_file_count",
            "artifact_tree_sha256",
            "artifact_total_bytes",
            "blind_completion_index_path",
            "blind_completion_index_entry_sha256",
            "worker_status",
        },
    }
    if set(marker) != exact_fields[state]:
        raise RuntimeError(f"formal {state} marker field set is not exact")
    _validate_sha256(
        str(marker.get("stage_authorization_sha256") or ""),
        "stage_authorization_sha256",
    )
    if (
        expected_stage_authorization_sha256 is not None
        and marker.get("stage_authorization_sha256")
        != expected_stage_authorization_sha256
    ):
        raise RuntimeError("formal marker stage authorization is stale")
    if state == "completed":
        if marker.get("worker_status") != "completed":
            raise RuntimeError("formal completion marker is not completed")
        for key in ("artifact_file_count", "artifact_total_bytes"):
            if not isinstance(marker.get(key), int) or int(marker[key]) <= 0:
                raise RuntimeError(f"formal completion marker has invalid {key}")
        _validate_sha256(str(marker.get("artifact_tree_sha256") or ""), "artifact_tree_sha256")
        _validate_sha256(
            str(marker.get("blind_completion_index_entry_sha256") or ""),
            "blind_completion_index_entry_sha256",
        )
        if not str(marker.get("blind_completion_index_path") or "").startswith("/"):
            raise RuntimeError("formal completion marker index path is not absolute")


def _read_remote_formal_job_state(
    target: "InfraBenchmarkTarget",
    remote_output_dir: str,
) -> tuple[str, dict[str, Any] | None]:
    root = shlex.quote(remote_output_dir)
    launch = shlex.quote(f"{remote_output_dir}/{FORMAL_JOB_LAUNCH_MARKER}")
    started = shlex.quote(f"{remote_output_dir}/{FORMAL_JOB_STARTED_MARKER}")
    completed = shlex.quote(f"{remote_output_dir}/{FORMAL_JOB_COMPLETION_MARKER}")
    command = f"""
if [ ! -e {root} ] && [ ! -L {root} ]; then
  printf '%s\\n' absent
elif [ -L {root} ] || [ ! -d {root} ]; then
  printf '%s\\n' invalid_root
elif [ -L {completed} ] || [ -L {started} ] || [ -L {launch} ]; then
  printf '%s\\n' invalid_marker
elif [ -f {completed} ]; then
  printf '%s\\n' completed
  cat {completed}
elif [ -e {completed} ]; then
  printf '%s\\n' invalid_marker
elif [ -f {started} ]; then
  printf '%s\\n' started
  cat {started}
elif [ -e {started} ]; then
  printf '%s\\n' invalid_marker
elif [ -f {launch} ]; then
  printf '%s\\n' launch_intent
  cat {launch}
elif [ -e {launch} ]; then
  printf '%s\\n' invalid_marker
elif [ -n "$(find {root} -mindepth 1 -maxdepth 1 -print -quit)" ]; then
  printf '%s\\n' unmarked_nonempty
else
  printf '%s\\n' empty
fi
""".strip()
    result = run_remote_blind_command(
        target,
        command,
        transient_retry_attempts=4,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "read-only formal remote marker reconciliation failed: "
            f"exit_code={result.returncode}"
        )
    lines = (result.stdout or "").splitlines()
    if not lines:
        raise RuntimeError("read-only formal remote marker reconciliation returned no state")
    state = lines[0].strip()
    marker = None
    if len(lines) > 1:
        try:
            loaded = json.loads("\n".join(lines[1:]))
        except json.JSONDecodeError as exc:
            raise RuntimeError("formal remote lifecycle marker is invalid JSON") from exc
        if not isinstance(loaded, dict):
            raise RuntimeError("formal remote lifecycle marker is not an object")
        marker = loaded
    return state, marker


def _formal_launch_intent_command(
    remote_output_dir: str,
    launch: Mapping[str, Any],
    *,
    attempt_namespace_root: str,
    python_bin: str,
) -> str:
    if not python_bin.startswith("/") or "\n" in python_bin:
        raise RuntimeError("formal launch-intent Python must be a locked absolute path")
    encoded = json.dumps(
        dict(launch), ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ) + "\n"
    script = """
import os, pathlib, stat, sys
namespace = pathlib.Path(sys.argv[1])
root = pathlib.Path(sys.argv[2])
marker = root / 'formal_job_launch_intent.json'
data = sys.argv[3].encode('utf-8')
if (not namespace.is_absolute() or not root.is_absolute()
        or namespace not in root.parents or root.parent.parent != namespace):
    raise SystemExit(21)
current = pathlib.Path(namespace.anchor)
for part in namespace.parts[1:]:
    current = current / part
    info = os.lstat(current)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise SystemExit(22)
namespace_info = os.lstat(namespace)
if (stat.S_IMODE(namespace_info.st_mode) != 0o700
        or namespace_info.st_uid != os.geteuid()):
    raise SystemExit(23)
binding_root = root.parent
try:
    os.mkdir(binding_root, 0o700)
except FileExistsError:
    info = os.lstat(binding_root)
    if (not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode)
            or stat.S_IMODE(info.st_mode) != 0o700 or info.st_uid != os.geteuid()):
        raise SystemExit(24)
try:
    os.mkdir(root, 0o700)
except FileExistsError:
    info = os.lstat(root)
    if (not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode)
            or stat.S_IMODE(info.st_mode) != 0o700 or info.st_uid != os.geteuid()
            or any(root.iterdir())):
        raise SystemExit(25)
flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
if hasattr(os, 'O_NOFOLLOW'):
    flags |= os.O_NOFOLLOW
descriptor = os.open(marker, flags, 0o600)
try:
    view = memoryview(data)
    while view:
        written = os.write(descriptor, view)
        view = view[written:]
    os.fsync(descriptor)
finally:
    os.close(descriptor)
descriptor = os.open(root, os.O_RDONLY)
try:
    os.fsync(descriptor)
finally:
    os.close(descriptor)
descriptor = os.open(binding_root, os.O_RDONLY)
try:
    os.fsync(descriptor)
finally:
    os.close(descriptor)
""".strip()
    return (
        f"{shlex.quote(python_bin)} -c {shlex.quote(script)} "
        f"{shlex.quote(attempt_namespace_root)} "
        f"{shlex.quote(remote_output_dir)} {shlex.quote(encoded)}"
    )


def _bundle_source_entry(source_bundle: Mapping[str, Any], *, task_id: str) -> dict[str, Any] | None:
    for entry in list(source_bundle.get("sources") or []):
        if not isinstance(entry, Mapping):
            continue
        if str(entry.get("task_id")) != task_id:
            continue
        domain = str(entry.get("domain") or "").lower().replace("-", "_")
        if domain != "agentdojo":
            continue
        return dict(entry)
    return None


def _remote_output_dir(target: "InfraBenchmarkTarget", job: Mapping[str, Any]) -> str:
    if _is_formal_execution_job(job):
        root = str(target.benchmark_config.get("remote_raw_root") or "")
        if not root.startswith("/"):
            raise RuntimeError(
                "formal AgentDojo execution requires an absolute sealed remote_raw_root"
            )
        return f"{root.rstrip('/')}/{formal_job_binding_sha256(job)}"
    return remote_job_result_dir(target, job)


def _openrouter_http_model_id(model_id: str) -> str:
    return model_id.removeprefix("openrouter/")


def _validate_sha256(value: str, field: str) -> None:
    normalized = str(value).removeprefix("sha256:")
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise RuntimePolicyError(f"{field} must be a lowercase SHA-256 digest")


def _agentdojo_artifacts(native_run_dir: Any) -> tuple[Any, ...]:
    descriptors: list[Any] = []
    for relative, artifact_type, producer_role, official_evaluator in (
        ("native_evaluator_input.json", "native_evaluator_input", "official_runner", False),
        ("native_evaluator_output.json", "native_evaluator_output", "official_evaluator", True),
        ("run_summary.json", "structured_output", "adapter", False),
        ("job.json", "file", "adapter", False),
        ("source_bundle_entry.json", "file", "adapter", False),
        ("worker_config.json", "file", "adapter", False),
        ("install_verification.json", "file", "adapter", False),
        ("runtime_policy_verification.json", "file", "adapter", False),
        ("blind_health", "file", "adapter", False),
        ("proxy_calls", "file", "adapter", False),
        ("trace_logs", "trace", "official_runner", False),
    ):
        path = native_run_dir / relative
        if not path.exists():
            continue
        descriptors.append(
            file_descriptor(
                path,
                artifact_type=artifact_type,
                producer_role=producer_role,
                producer_name="agentdojo" if producer_role != "adapter" else "agentdojo-worker",
                producer_version="agentdojo" if producer_role != "adapter" else "0.1.0",
                official_runner=producer_role == "official_runner" or official_evaluator,
                official_evaluator=official_evaluator,
                evaluator_name="agentdojo-benchmark" if official_evaluator else None,
                evaluator_version="agentdojo" if official_evaluator else None,
                artifact_contract_requirement_ids=("smoke-native-evaluator-output",) if artifact_type == "native_evaluator_output" else (),
            )
        )
    return tuple(descriptors)


def _agentdojo_llm_events(native_run_dir: Any) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for path in sorted((native_run_dir / "proxy_calls").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        response_payload = payload.get("response_payload")
        usage = dict(response_payload.get("usage") or {}) if isinstance(response_payload, Mapping) else {}
        prompt_tokens = int(usage.get("prompt_tokens", 0))
        completion_tokens = int(usage.get("completion_tokens", 0))
        events.append(
            {
                "call_id": str(payload.get("call_id") or path.stem),
                "request_timestamp": str(payload.get("request_timestamp") or utc_now_iso()),
                "response_timestamp": str(payload.get("response_timestamp") or utc_now_iso()),
                "request_payload": payload.get("request_payload"),
                "response_payload": response_payload,
                "error_message": payload.get("error_message"),
                "token_usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "cached_prompt_tokens": 0,
                    "reasoning_tokens": 0,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
            }
        )
    return events
