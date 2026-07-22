from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from evidence_system.adapters.runtime import job_result_relative_dir
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.orchestrator import jobs
from evidence_system.orchestrator.jobs import PlannedJob


SOURCE_BUNDLE_HASH = "e" * 64
OFFICIAL_SPLIT_HASH = "f" * 64


def test_completed_result_is_reused_only_when_all_provenance_matches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    item, context = _write_completed_result(tmp_path, monkeypatch)

    result = jobs._existing_completed_result(item, context=context)

    assert result is not None
    assert result["status"] == "skipped_completed"


@pytest.mark.parametrize(
    "drift",
    [
        "manifest",
        "agent_config",
        "benchmark_config",
        "contract",
        "source_bundle",
        "official_split",
    ],
)
def test_completed_result_reuse_fails_closed_on_provenance_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    drift: str,
) -> None:
    item, context = _write_completed_result(tmp_path, monkeypatch)

    if drift == "manifest":
        item.job["manifest_hash"] = "1" * 64
    elif drift == "agent_config":
        item.job["agent_config_hash"] = "2" * 64
    elif drift == "benchmark_config":
        item.job["benchmark_config_hash"] = "3" * 64
    elif drift == "contract":
        item.job["contract_hash"] = "4" * 64
        item.job["evidence_contract_hash"] = "4" * 64
    elif drift == "source_bundle":
        context.source_bundle_hash = "5" * 64
    elif drift == "official_split":
        item = replace(item, official_split_hash="6" * 64)

    assert jobs._existing_completed_result(item, context=context) is None


def test_completed_result_reuse_rejects_missing_or_unverifiable_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    item, context = _write_completed_result(tmp_path, monkeypatch)
    root = _result_root(tmp_path, item.job)
    artifact_path = root / "artifact_manifest.json"
    raw_path = root / "raw_run.json"
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact.pop("source_bundle_hash")
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    raw["artifact_manifest_sha256"] = sha256_file(artifact_path)
    raw_path.write_text(json.dumps(raw), encoding="utf-8")

    assert jobs._existing_completed_result(item, context=context) is None


def _write_completed_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[PlannedJob, SimpleNamespace]:
    def resolve(path: str | Path) -> Path:
        candidate = Path(path)
        return candidate if candidate.is_absolute() else tmp_path / candidate

    monkeypatch.setattr(jobs, "resolve_repo_path", resolve)
    job = _job()
    item = PlannedJob(
        job=job,
        job_path=tmp_path / "job.json",
        official_split_hash=OFFICIAL_SPLIT_HASH,
        execution_plan={},
    )
    context = SimpleNamespace(source_bundle_hash=SOURCE_BUNDLE_HASH)
    root = _result_root(tmp_path, job)
    root.mkdir(parents=True)
    artifact_path = root / "artifact_manifest.json"
    raw_path = root / "raw_run.json"
    environment_path = root / "environment.json"
    common = {
        "domain": job["domain"],
        "domain_display_name": job["domain_display_name"],
        "benchmark_name": job["benchmark_name"],
        "case_unit_id": job["case_unit_id"],
        "task_id": job["task_id"],
        "record_slot_id": job["record_slot_id"],
        "run_id": job["run_id"],
        "attempt_id": job["attempt_id"],
        "final_attempt": job["final_attempt"],
        "seed": job["seed"],
        "agent_id": job["agent_id"],
        "phase": job["phase"],
        "experiment_type": job["experiment_type"],
        "priority": job["priority"],
    }
    artifact = {
        "schema_version": "artifact_manifest/v1",
        **common,
        "evidence_contract_id": job["evidence_contract_id"],
        "evidence_contract_version": job["evidence_contract_version"],
        "evidence_contract_hash": job["evidence_contract_hash"],
        "source_bundle_hash": SOURCE_BUNDLE_HASH,
        "official_splits_hash": OFFICIAL_SPLIT_HASH,
        "artifacts": [],
    }
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
    relative_root = job_result_relative_dir(job) / "adapter"
    raw = {
        "schema_version": "raw_run/v1",
        **common,
        "status": "COMPLETED",
        "diagnostic_status": "completed",
        "manifest_hash": job["manifest_hash"],
        "contract_id": job["contract_id"],
        "contract_version": job["contract_version"],
        "contract_hash": job["contract_hash"],
        "taxonomy_version": job["taxonomy_version"],
        "evidence_contract_id": job["evidence_contract_id"],
        "evidence_contract_version": job["evidence_contract_version"],
        "evidence_contract_hash": job["evidence_contract_hash"],
        "config_hash": sha256_object(
            {
                "agent_config_hash": job["agent_config_hash"],
                "benchmark_config_hash": job["benchmark_config_hash"],
            }
        ),
        "artifact_manifest_path": str(relative_root / "artifact_manifest.json"),
        "artifact_manifest_sha256": sha256_file(artifact_path),
        "raw_source_path": str(relative_root / "raw_run.json"),
    }
    raw_path.write_text(json.dumps(raw), encoding="utf-8")
    environment_path.write_text(
        json.dumps(
            {
                "benchmark_name": job["benchmark_name"],
                "benchmark_config_hash": job["benchmark_config_hash"],
                "job_id": job["job_id"],
                "run_id": job["run_id"],
            }
        ),
        encoding="utf-8",
    )
    return item, context


def _result_root(tmp_path: Path, job: dict[str, object]) -> Path:
    return tmp_path / job_result_relative_dir(job) / "adapter"


def _job() -> dict[str, object]:
    return {
        "schema_version": "job/v1",
        "job_id": "full-miniwob-use-slider-agent_a",
        "domain": "miniwob",
        "domain_display_name": "MiniWoB++",
        "benchmark_name": "MiniWoB++",
        "case_unit_id": "miniwob.use-slider",
        "task_id": "miniwob.use-slider",
        "record_slot_id": "slot-miniwob-use-slider-agent_a",
        "run_id": "run-miniwob-use-slider-agent_a",
        "attempt_id": "attempt-miniwob-use-slider-agent_a",
        "final_attempt": True,
        "seed": 7,
        "agent_id": "Agent A",
        "phase": "full",
        "experiment_type": "diagnostic",
        "priority": "P3",
        "adapter_module": "evidence_system.adapters.miniwob",
        "agent_config_hash": "a" * 64,
        "benchmark_config_hash": "b" * 64,
        "manifest_hash": "c" * 64,
        "evidence_contract_id": "contract-miniwob-use-slider",
        "evidence_contract_version": "1.0.0",
        "evidence_contract_hash": "d" * 64,
        "contract_id": "contract-miniwob-use-slider",
        "contract_version": "1.0.0",
        "contract_hash": "d" * 64,
        "taxonomy_version": "1.0.0",
    }
