from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from evidence_system.adapters import webarena_verified
from evidence_system.adapters.runtime import JobPaths
from evidence_system.orchestrator.jobs import InfraBenchmarkTarget
from evidence_system.webarena_sites import RESET_RECEIPT_SCHEMA, load_site_lock, pinned_image_reference


ROOT = Path(__file__).resolve().parents[2]


def _target() -> InfraBenchmarkTarget:
    return InfraBenchmarkTarget(
        machine_id="webarena-gpt54-ord",
        machine_role="webarena_vps",
        ssh_host="45.76.67.186",
        ssh_user="root",
        ssh_port=22,
        ssh_key_path="/tmp/test-key",
        remote_workdir="/opt/webarena-controller/current",
        runner_workdir="/opt/webarena-runner/pinned/source",
        benchmark_name="WebArena-Verified",
        benchmark_config={
            "site_controller": {
                "ssh_host_fingerprint": "SHA256:locked-fingerprint",
            }
        },
        benchmark_config_hash="0" * 64,
        runner_command="unused",
        machine_concurrency=1,
    )


def _job() -> dict[str, object]:
    return {
        "schema_version": "job/v1",
        "job_id": "full-webarena_verified-000-agent_a",
        "domain": "webarena_verified",
        "phase": "full",
        "task_id": "0",
        "record_slot_id": "wv-000-agent-a",
        "attempt_id": "attempt-wv-000-agent-a-001",
        "agent_id": "Agent A",
        "seed": 123000,
        "reset_policy": "recreate_task_sites_from_digest_v1",
        "reset_receipt_relative_path": "reset_receipt.json",
        "task_sites": ["shopping_admin"],
    }


def _paths(tmp_path: Path) -> JobPaths:
    root = tmp_path / "adapter"
    native = root / "native_run"
    logs = root / "logs"
    llm = root / "llm_calls"
    for path in (native, logs, llm):
        path.mkdir(parents=True, exist_ok=True)
    return JobPaths(
        root=root,
        native_run_dir=native,
        logs_dir=logs,
        stdout_log=logs / "stdout.log",
        stderr_log=logs / "stderr.log",
        llm_dir=llm,
        llm_jsonl=llm / "calls.jsonl",
        raw_run_path=root / "raw_run.json",
        artifact_manifest_path=root / "artifact_manifest.json",
        environment_path=root / "environment.json",
        failure_record_path=root / "failure_record.json",
    )


def test_execute_refuses_to_start_worker_when_slot_reset_fails(monkeypatch, tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    remote_commands: list[str] = []

    monkeypatch.setattr(webarena_verified, "build_job_paths", lambda _job: paths)
    monkeypatch.setattr(webarena_verified, "sync_repo_support_files", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        webarena_verified,
        "write_environment_snapshot",
        lambda **_kwargs: ({}, "e" * 64),
    )

    def fake_remote(_target, command, **_kwargs):
        remote_commands.append(str(command))
        return subprocess.CompletedProcess(["ssh"], 0, "", "")

    monkeypatch.setattr(webarena_verified, "run_remote_command", fake_remote)
    monkeypatch.setattr(
        webarena_verified,
        "_perform_slot_reset",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("reset sentinel failed")),
    )

    with pytest.raises(RuntimeError, match="reset sentinel failed"):
        webarena_verified.execute_smoke_job(
            _job(),
            target=_target(),
            execution_plan={
                "runner_command": "WORKER_MUST_NOT_RUN",
                "secret_env_name": "OPENROUTER_API_KEY",
            },
            context=SimpleNamespace(dotenv_path=tmp_path / ".env"),
        )

    assert len(remote_commands) == 1  # output-directory preparation is non-agent work
    assert all("WORKER_MUST_NOT_RUN" not in command for command in remote_commands)
    assert not (paths.native_run_dir / "reset_receipt.json").exists()


def test_adapter_accepts_only_fully_bound_pinned_reset_receipt() -> None:
    job = _job()
    target = _target()
    lock = load_site_lock(ROOT / "configs/webarena_verified_sites.lock.json")
    lock_hash = hashlib.sha256(
        json.dumps(lock, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    image_id = f"sha256:{'a' * 64}"
    receipt = {
        "schema_version": RESET_RECEIPT_SCHEMA,
        "status": "pass",
        "slot": {
            "slot_id": job["record_slot_id"],
            "task_id": 0,
            "agent_id": job["agent_id"],
            "attempt_id": job["attempt_id"],
            "seed": job["seed"],
        },
        "machine": {
            "machine_id": target.machine_id,
            "ssh_host": target.ssh_host,
            "ssh_host_fingerprint": "SHA256:locked-fingerprint",
        },
        "site_lock_sha256": lock_hash,
        "reset_scope": ["shopping_admin"],
        "exclusive_lock": {"acquired_at": "2026-07-16T00:00:00Z", "released_at": "2026-07-16T00:01:00Z"},
        "error": None,
        "fail_closed": None,
        "sites": [
            {
                "site": "shopping_admin",
                "ok": True,
                "image_reference": pinned_image_reference(lock, "shopping_admin"),
                "expected_image_id": image_id,
                "before": {"container_id": "old"},
                "after": {"container_id": "new", "running": True, "image_id": image_id},
                "sentinels": [{"name": "homepage", "ok": True}],
            }
        ],
    }

    webarena_verified._validate_slot_reset_receipt(
        receipt,
        job=job,
        target=target,
        expected_sites=["shopping_admin"],
        site_lock=lock,
    )
    receipt["sites"][0]["after"]["container_id"] = "old"
    with pytest.raises(RuntimeError, match="did not replace"):
        webarena_verified._validate_slot_reset_receipt(
            receipt,
            job=job,
            target=target,
            expected_sites=["shopping_admin"],
            site_lock=lock,
        )


def test_reset_receipt_is_packaged_as_an_adapter_artifact(tmp_path: Path) -> None:
    native = tmp_path / "native_run"
    native.mkdir()
    (native / "reset_receipt.json").write_text('{"status":"pass"}\n', encoding="utf-8")

    descriptors = webarena_verified._webarena_artifacts(native)
    reset = next(item for item in descriptors if item.local_path.name == "reset_receipt.json")
    assert reset.artifact_type == "structured_output"
    assert reset.producer_name == "webarena-verified-site-controller"


def test_official_evaluator_artifacts_use_locked_contract_requirement(
    tmp_path: Path,
) -> None:
    native = tmp_path / "native_run"
    task = native / "7"
    task.mkdir(parents=True)
    (native / "native_evaluator_output.json").write_text(
        '{"success":true}\n', encoding="utf-8"
    )
    (task / "eval_result.json").write_text(
        '{"status":"success"}\n', encoding="utf-8"
    )
    (task / "eval_summary.json").write_text(
        '{"status":"success"}\n', encoding="utf-8"
    )
    job = {
        "artifact_contract": {
            "required_artifacts": [
                {
                    "artifact_type": "native_evaluator_output",
                    "contract_requirement_id": "req-native-evaluator-output",
                }
            ]
        }
    }

    official = [
        item
        for item in webarena_verified._webarena_artifacts(native, job=job)
        if item.official_evaluator
    ]

    assert len(official) == 3
    assert all(item.official_runner for item in official)
    assert all(
        item.producer_role == "official_evaluator" for item in official
    )
    assert all(
        item.artifact_contract_requirement_ids
        == ("req-native-evaluator-output",)
        for item in official
    )
