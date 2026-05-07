from __future__ import annotations

from pathlib import Path

from evidence_system.adapters.agentdojo import _agentdojo_artifacts
from evidence_system.adapters.appworld import _appworld_artifacts
from evidence_system.adapters.runtime import JobPaths, default_adapter_artifacts


def test_default_adapter_artifacts_include_environment_and_llm_directory(tmp_path: Path) -> None:
    root = tmp_path / "adapter"
    logs_dir = root / "logs"
    llm_dir = root / "llm_calls"
    native_run_dir = root / "native_run"
    logs_dir.mkdir(parents=True)
    llm_dir.mkdir(parents=True)
    native_run_dir.mkdir(parents=True)

    (root / "environment.json").write_text("{}\n", encoding="utf-8")
    (logs_dir / "stdout.log").write_text("stdout\n", encoding="utf-8")
    (logs_dir / "stderr.log").write_text("stderr\n", encoding="utf-8")
    (llm_dir / "calls.jsonl").write_text('{"call_id":"c1"}\n', encoding="utf-8")
    (llm_dir / "c1.json").write_text("{}\n", encoding="utf-8")

    paths = JobPaths(
        root=root,
        native_run_dir=native_run_dir,
        logs_dir=logs_dir,
        stdout_log=logs_dir / "stdout.log",
        stderr_log=logs_dir / "stderr.log",
        llm_dir=llm_dir,
        llm_jsonl=llm_dir / "calls.jsonl",
        raw_run_path=root / "raw_run.json",
        artifact_manifest_path=root / "artifact_manifest.json",
        environment_path=root / "environment.json",
        failure_record_path=root / "failure_record.json",
    )

    descriptors = default_adapter_artifacts(paths)
    indexed = {descriptor.local_path.relative_to(root).as_posix() for descriptor in descriptors}
    assert "environment.json" in indexed
    assert "llm_calls" in indexed
    assert "llm_calls/calls.jsonl" in indexed
    assert "logs/stdout.log" in indexed
    assert "logs/stderr.log" in indexed


def test_appworld_artifacts_include_high_and_medium_importance_files(tmp_path: Path) -> None:
    native_run_dir = tmp_path / "native_run"
    (native_run_dir / "appworld_task_output" / "logs").mkdir(parents=True)
    (native_run_dir / "appworld_task_output" / "dbs").mkdir(parents=True)
    (native_run_dir / "appworld_task_output" / "evaluation").mkdir(parents=True)
    (native_run_dir / "appworld_task_output" / "version").mkdir(parents=True)
    (native_run_dir / "llm_attempts").mkdir(parents=True)

    for relative in (
        "native_evaluator_input.json",
        "native_evaluator_output.json",
        "task_prompt_context.json",
        "artifact_manifest.json",
        "run_summary.json",
        "job.json",
        "source_bundle_entry.json",
        "worker_config.json",
        "appworld_task_output/logs/api_calls.jsonl",
        "appworld_task_output/logs/environment_io.md",
        "appworld_task_output/dbs/snapshot.txt",
        "appworld_task_output/evaluation/report.md",
        "appworld_task_output/version/code.txt",
        "llm_attempts/01_prompt.json",
    ):
        path = native_run_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")

    descriptors = _appworld_artifacts(native_run_dir)
    indexed = {descriptor.local_path.relative_to(native_run_dir).as_posix() for descriptor in descriptors}
    assert "job.json" in indexed
    assert "source_bundle_entry.json" in indexed
    assert "worker_config.json" in indexed
    assert "appworld_task_output/evaluation" in indexed
    assert "appworld_task_output/version" in indexed


def test_agentdojo_artifacts_include_high_importance_files(tmp_path: Path) -> None:
    native_run_dir = tmp_path / "native_run"
    (native_run_dir / "proxy_calls").mkdir(parents=True)
    (native_run_dir / "trace_logs").mkdir(parents=True)

    for relative in (
        "native_evaluator_input.json",
        "native_evaluator_output.json",
        "run_summary.json",
        "job.json",
        "source_bundle_entry.json",
        "worker_config.json",
        "proxy_calls/0001.json",
        "trace_logs/trace.json",
    ):
        path = native_run_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")

    descriptors = _agentdojo_artifacts(native_run_dir)
    indexed = {descriptor.local_path.relative_to(native_run_dir).as_posix() for descriptor in descriptors}
    assert "job.json" in indexed
    assert "source_bundle_entry.json" in indexed
    assert "worker_config.json" in indexed
