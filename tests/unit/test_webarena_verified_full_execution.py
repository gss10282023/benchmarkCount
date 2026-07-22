from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json
import threading

import pytest

from evidence_system.orchestrator.webarena_verified_full import (
    EXPECTED_AGENT_IDS,
    EXPECTED_ROUTES,
    FullSchedulePlan,
    WebArenaFullScheduleError,
    formal_benchmark_config,
)
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.orchestrator.webarena_verified_full_execution import (
    execute_full_schedule,
)


ROOT = Path(__file__).resolve().parents[2]


def _synthetic_accepted_plan() -> FullSchedulePlan:
    manifest = json.loads(
        (ROOT / "experiments/step19/webarena_verified_full_812_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    source_bundle_sha256 = sha256_file(
        ROOT
        / "experiments/evidence_contracts/source_bundles"
        / "webarena_verified_full_812_source_bundle.json"
    )
    site_lock_sha256 = sha256_file(ROOT / "configs/webarena_verified_sites.lock.json")
    native_claim_index_sha256 = "9" * 64
    jobs: list[dict[str, object]] = []
    for task_id in range(812):
        for agent_id in EXPECTED_AGENT_IDS:
            suffix = agent_id[-1].lower()
            slot = f"wv123-task-{task_id:03d}-agent-{suffix}"
            jobs.append(
                {
                    "job_id": f"full-webarena_verified-{task_id:03d}-agent_{suffix}",
                    "record_slot_id": slot,
                    "task_id": str(task_id),
                    "agent_id": agent_id,
                    "seed": 123000 + task_id,
                    "execution_target": EXPECTED_ROUTES[agent_id],
                    "requested_model": EXPECTED_ROUTES[agent_id]["model"],
                    "benchmark_config_hash": sha256_object(
                        formal_benchmark_config(
                            route=EXPECTED_ROUTES[agent_id],
                            common_run_policy=manifest["common_run_policy"],
                            source_bundle_sha256=source_bundle_sha256,
                            native_claim_index_sha256=native_claim_index_sha256,
                            site_lock_sha256=site_lock_sha256,
                        )
                    ),
                    "reset_policy": "recreate_task_sites_from_digest_v1",
                    "reset_receipt_relative_path": "reset_receipt.json",
                    "artifact_retention_mode": "vps_persistent_remote_v1",
                    "task_sites": ["shopping"],
                    "formal_policy_lock": {
                        "native_claim_index_sha256": native_claim_index_sha256,
                    },
                }
            )
    return FullSchedulePlan(
        jobs=tuple(jobs),
        acceptance={
            "status": "pass",
            "formal_launch_eligible": True,
            "inputs": {"native_claim_index_sha256": native_claim_index_sha256},
        },
    )


def test_full_execution_runs_three_sequential_lanes_with_exact_routes(
    tmp_path: Path,
) -> None:
    key = tmp_path / "id_ed25519"
    key.write_text("test-only-not-a-real-private-key\n", encoding="utf-8")
    observed: dict[str, list[int]] = defaultdict(list)
    observed_targets: dict[str, object] = {}
    progress: list[int] = []
    lock = threading.Lock()

    def fake_planner(job: dict[str, object], *, target: object, **_: object) -> dict[str, object]:
        assert getattr(target, "machine_concurrency") == 1
        assert getattr(target, "ssh_host") == job["execution_target"]["ssh_host"]
        assert getattr(target, "ssh_host_ed25519_fingerprint") == job["execution_target"][
            "ssh_host_ed25519_fingerprint"
        ]
        assert getattr(target, "ssh_public_key_fingerprint") == job["execution_target"][
            "controller_ssh_public_key_fingerprint"
        ]
        with lock:
            observed_targets[str(job["agent_id"])] = target
        return {"status": "runnable", "runner_command": "fake"}

    def fake_executor(
        job: dict[str, object], *, target: object, execution_plan: object, context: object
    ) -> dict[str, object]:
        del target, execution_plan, context
        with lock:
            observed[str(job["agent_id"])].append(int(job["task_id"]))
        return {"status": "completed", "raw_run_path": "fake/raw_run.json"}

    executed = execute_full_schedule(
        _synthetic_accepted_plan(),
        ssh_key_path=key,
        manifest_path=ROOT / "experiments/step19/webarena_verified_full_812_manifest.json",
        source_bundle_path=(
            ROOT
            / "experiments/evidence_contracts/source_bundles"
            / "webarena_verified_full_812_source_bundle.json"
        ),
        agents_config_path=ROOT / "configs/agents.yaml",
        site_lock_path=ROOT / "configs/webarena_verified_sites.lock.json",
        adapter_planner=fake_planner,
        adapter_executor=fake_executor,
        progress_callback=lambda _job, _result, count, _total: progress.append(count),
    )

    assert len(executed) == 2436
    assert [item.job["record_slot_id"] for item in executed[:3]] == [
        "wv123-task-000-agent-a",
        "wv123-task-000-agent-b",
        "wv123-task-000-agent-c",
    ]
    assert set(observed_targets) == set(EXPECTED_AGENT_IDS)
    assert observed == {agent: list(range(812)) for agent in EXPECTED_AGENT_IDS}
    assert sorted(progress) == list(range(1, 2437))


def test_full_execution_runs_recovery_prelude_before_any_lane_resume(
    tmp_path: Path,
) -> None:
    key = tmp_path / "id_ed25519"
    key.write_text("test-only-not-a-real-private-key\n", encoding="utf-8")
    observed: list[str] = []
    lock = threading.Lock()
    prelude = tuple(
        f"wv123-task-{task_id:03d}-agent-a" for task_id in range(556, 560)
    )

    def fake_planner(job: dict[str, object], **_: object) -> dict[str, object]:
        return {"status": "runnable", "runner_command": "fake"}

    def fake_executor(job: dict[str, object], **_: object) -> dict[str, object]:
        with lock:
            observed.append(str(job["record_slot_id"]))
        return {"status": "completed", "raw_run_path": "fake/raw_run.json"}

    executed = execute_full_schedule(
        _synthetic_accepted_plan(),
        ssh_key_path=key,
        manifest_path=ROOT / "experiments/step19/webarena_verified_full_812_manifest.json",
        source_bundle_path=(
            ROOT
            / "experiments/evidence_contracts/source_bundles"
            / "webarena_verified_full_812_source_bundle.json"
        ),
        agents_config_path=ROOT / "configs/agents.yaml",
        site_lock_path=ROOT / "configs/webarena_verified_sites.lock.json",
        adapter_planner=fake_planner,
        adapter_executor=fake_executor,
        recovery_prelude_slot_ids=prelude,
    )

    assert observed[:4] == list(prelude)
    assert len(observed) == 2436
    assert len(set(observed)) == 2436
    assert len(executed) == 2436


def test_full_execution_revalidates_route_before_any_worker_call(tmp_path: Path) -> None:
    plan = _synthetic_accepted_plan()
    jobs = [dict(job) for job in plan.jobs]
    jobs[0]["execution_target"] = dict(jobs[0]["execution_target"])
    jobs[0]["execution_target"]["ssh_host"] = "192.0.2.44"
    mutated = FullSchedulePlan(jobs=tuple(jobs), acceptance=plan.acceptance)
    key = tmp_path / "id_ed25519"
    key.write_text("unused\n", encoding="utf-8")

    with pytest.raises(WebArenaFullScheduleError, match="route changed"):
        execute_full_schedule(
            mutated,
            ssh_key_path=key,
            adapter_planner=lambda *_args, **_kwargs: pytest.fail("planner was called"),
            adapter_executor=lambda *_args, **_kwargs: pytest.fail("executor was called"),
        )


def test_full_execution_recomputes_runtime_config_hash_before_ssh(tmp_path: Path) -> None:
    plan = _synthetic_accepted_plan()
    jobs = [dict(job) for job in plan.jobs]
    for job in jobs:
        if job["agent_id"] == "Agent A":
            job["benchmark_config_hash"] = "0" * 64
    mutated = FullSchedulePlan(jobs=tuple(jobs), acceptance=plan.acceptance)
    key = tmp_path / "id_ed25519"
    key.write_text("unused\n", encoding="utf-8")

    with pytest.raises(
        WebArenaFullScheduleError,
        match="does not match the exact runtime config",
    ):
        execute_full_schedule(
            mutated,
            ssh_key_path=key,
            manifest_path=ROOT / "experiments/step19/webarena_verified_full_812_manifest.json",
            source_bundle_path=(
                ROOT
                / "experiments/evidence_contracts/source_bundles"
                / "webarena_verified_full_812_source_bundle.json"
            ),
            agents_config_path=ROOT / "configs/agents.yaml",
            site_lock_path=ROOT / "configs/webarena_verified_sites.lock.json",
            adapter_planner=lambda *_args, **_kwargs: pytest.fail("planner was called"),
            adapter_executor=lambda *_args, **_kwargs: pytest.fail("executor was called"),
        )
