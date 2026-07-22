from __future__ import annotations

from pathlib import Path
import copy
import json

import pytest

from evidence_system.orchestrator.webarena_verified_full import (
    EXPECTED_AGENT_IDS,
    EXPECTED_ROUTES,
    FullSchedulePlan,
    WebArenaFullScheduleError,
)
from evidence_system.orchestrator.webarena_verified_pilot_execution import (
    EXPECTED_FULL_SOURCE_JOBS_SHA256,
    EXPECTED_PILOT_JOBS_SHA256,
    PILOT_ATTEMPT_ORDINAL,
    PILOT_ATTEMPT_POLICY,
    build_pilot_schedule,
    materialize_canonical_pilot_schedule,
    validate_canonical_pilot_schedule,
)
from evidence_system.orchestrator.webarena_verified_run_control import (
    load_materialized_full_plan,
)


def test_pilot_schedule_refuses_machine_preview_without_formal_locks() -> None:
    preview = FullSchedulePlan(
        jobs=(),
        acceptance={"status": "blocked", "formal_launch_eligible": False},
    )

    with pytest.raises(WebArenaFullScheduleError, match="formally locked"):
        build_pilot_schedule(preview)


def test_pilot_schedule_materializes_exact_24_locked_jobs() -> None:
    root = Path(__file__).resolve().parents[2]
    base = json.loads((root / "tests/fixtures/valid_job.json").read_text(encoding="utf-8"))
    manifest = json.loads(
        (root / "experiments/step19/webarena_verified_full_812_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    cases = {int(case["task_id"]): case for case in manifest["cases"]}
    jobs = []
    for task_id in range(812):
        for agent_id in EXPECTED_AGENT_IDS:
            suffix = agent_id[-1].lower()
            slot = f"wv123-task-{task_id:03d}-agent-{suffix}"
            job = copy.deepcopy(base)
            job.update(
                {
                    "job_id": f"full-webarena_verified-{task_id:03d}-agent_{suffix}",
                    "domain": "webarena_verified",
                    "domain_display_name": "WebArena-Verified",
                    "benchmark_name": "WebArena-Verified",
                    "case_unit_id": str(task_id),
                    "task_id": str(task_id),
                    "task_revision": int(cases[task_id]["revision"]),
                    "task_sites": list(cases[task_id]["sites"]),
                    "record_slot_id": slot,
                    "run_id": f"run-{slot}",
                    "attempt_id": f"attempt-{slot}-001",
                    "seed": 123000 + task_id,
                    "agent_id": agent_id,
                    "requested_model": EXPECTED_ROUTES[agent_id]["model"],
                    "execution_target": EXPECTED_ROUTES[agent_id],
                    "reset_policy": "recreate_task_sites_from_digest_v1",
                        "reset_receipt_relative_path": "reset_receipt.json",
                        "artifact_retention_mode": "vps_persistent_remote_v1",
                        "adapter_module": "evidence_system.adapters.webarena_verified",
                    "benchmark_config_hash": suffix * 64,
                }
            )
            jobs.append(job)
    full = FullSchedulePlan(
        jobs=tuple(jobs),
        acceptance={
            "status": "pass",
            "formal_launch_eligible": True,
            "inputs": {"native_claim_index_sha256": "9" * 64},
        },
    )

    pilot = build_pilot_schedule(full)

    assert len(pilot.jobs) == 24
    assert pilot.acceptance["pilot_launch_eligible"] is True
    assert pilot.acceptance["formal_launch_eligible"] is False
    assert pilot.acceptance["counts"]["fallback_contracts"] == 0
    assert pilot.jobs[0]["record_slot_id"] == "wv123-pilot-task-000-agent-a"
    assert pilot.jobs[-1]["record_slot_id"] == "wv123-pilot-task-681-agent-a"
    assert all(job["phase"] == "preflight" for job in pilot.jobs)


def test_production_canonical_pilot_schedule_is_exact_and_hash_locked() -> None:
    pilot = build_pilot_schedule(load_materialized_full_plan())

    receipt = validate_canonical_pilot_schedule(pilot)

    assert receipt["status"] == "pass"
    assert receipt["job_count"] == 24
    assert receipt["jobs_sha256"] == EXPECTED_PILOT_JOBS_SHA256
    assert pilot.acceptance["attempt_policy"] == PILOT_ATTEMPT_POLICY
    assert {
        job["attempt_id"].rsplit("-", 1)[-1] for job in pilot.jobs
    } == {f"{PILOT_ATTEMPT_ORDINAL:03d}"}
    assert (
        receipt["source_full_jobs_sha256"]
        == EXPECTED_FULL_SOURCE_JOBS_SHA256
    )


def test_canonical_pilot_schedule_rejects_tampered_job(tmp_path: Path) -> None:
    pilot = build_pilot_schedule(load_materialized_full_plan())
    output = tmp_path / "pilot"
    acceptance = tmp_path / "pilot_schedule_acceptance.json"
    materialize_canonical_pilot_schedule(
        pilot,
        output_root=output,
        acceptance_path=acceptance,
        replace=True,
    )
    index = json.loads((output / "index.json").read_text(encoding="utf-8"))
    first = output / index["entries"][0]["path"]
    job = json.loads(first.read_text(encoding="utf-8"))
    job["seed"] = int(job["seed"]) + 1
    first.write_text(json.dumps(job, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(WebArenaFullScheduleError, match="job/index mismatch"):
        validate_canonical_pilot_schedule(
            pilot,
            jobs_index_path=output / "index.json",
            acceptance_path=acceptance,
        )
