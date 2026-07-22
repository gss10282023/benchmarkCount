from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from evidence_system.adapters import agentdojo_disposable_controller as controller
from evidence_system.adapters.agentdojo_runtime_control import (
    REQUIRED_AGENT_IDS,
    REQUIRED_MODELS,
)


def test_fake_transport_executes_exact_192_slots_in_13_model_serial_stages(
    tmp_path: Path, monkeypatch,
) -> None:
    plan_path = tmp_path / "round-plan.json"
    plan_path.write_text("{}\n", encoding="utf-8")
    policy_path = tmp_path / "policy.json"
    policy_path.write_text("{}\n", encoding="utf-8")
    stages = [
        {
            "ordinal": 0,
            "locked_workers": 4,
            "effective_workers": 4,
            "model_ordinal": None,
            "receipt_scope": "exploratory_measurement",
            "planned_jobs": 12,
            "workload": {"marker": 0},
            "workload_sha256": "a" * 64,
        }
    ]
    ordinal = 1
    for workers in (4, 8, 16, 32):
        for model_ordinal in range(3):
            stages.append(
                {
                    "ordinal": ordinal,
                    "locked_workers": workers,
                    "effective_workers": None,
                    "model_ordinal": model_ordinal,
                    "receipt_scope": "exploratory_measurement",
                    "planned_jobs": workers,
                    "workload": {"marker": ordinal},
                    "workload_sha256": f"{ordinal:x}" * 64,
                }
            )
            ordinal += 1
    plan = {
        "definition_sha256": "d" * 64,
        "definition": {
            "round_kind": "exploratory_measurement",
            "runtime_policy": {
                "path": str(policy_path),
                "semantic_sha256": "e" * 64,
            },
            "runtime_infra": {"sha256": "f" * 64},
            "stages": stages,
        },
        "artifact_namespace": {
            "stages": [
                {
                    "ordinal": row["ordinal"],
                    "stage_receipt": str(tmp_path / f"stage-{row['ordinal']}.json"),
                }
                for row in stages
            ]
        },
    }

    def materialize(workload: dict[str, int]) -> list[dict[str, object]]:
        stage = stages[int(workload["marker"])]
        if stage["model_ordinal"] is None:
            model_ordinals = [0] * 4 + [1] * 4 + [2] * 4
        else:
            model_ordinals = [int(stage["model_ordinal"])] * int(
                stage["planned_jobs"]
            )
        return [
            {
                "job": {
                    "job_id": f"job-{stage['ordinal']}-{job_ordinal}",
                    "agent_id": REQUIRED_AGENT_IDS[model_ordinal],
                },
                "source_entry": {"opaque": True},
            }
            for job_ordinal, model_ordinal in enumerate(model_ordinals)
        ]

    monkeypatch.setattr(controller, "load_disposable_round_plan", lambda _: plan)
    monkeypatch.setattr(
        controller,
        "load_runtime_policy",
        lambda *_args, **_kwargs: SimpleNamespace(semantic_sha256="e" * 64),
    )
    monkeypatch.setattr(controller, "materialize_disposable_stage_jobs", materialize)
    fake = controller.CountingFakeDisposableTransport()
    receipt = controller.execute_disposable_round(
        round_plan_path=plan_path,
        transport=fake,
        receipt_path=tmp_path / "controller-receipt.json",
        created_at="2026-07-17T00:00:00+00:00",
    )

    assert receipt["publishable"] is False
    assert receipt["stage_count"] == 13
    assert receipt["record_slot_count"] == 192
    assert receipt["record_slots_per_agent"] == {
        "Agent A": 64,
        "Agent B": 64,
        "Agent C": 64,
    }
    assert receipt["transport_batch_count"] == 15
    assert len(fake.batches) == 15
    assert [batch.model_ordinal for batch in fake.batches[:3]] == [0, 1, 2]
    assert [len(batch.jobs) for batch in fake.batches[:3]] == [4, 4, 4]
    assert all(
        {str(job["agent_id"]) for job in batch.jobs} == {batch.agent_id}
        and batch.model_id == REQUIRED_MODELS[batch.model_ordinal]
        for batch in fake.batches
    )
    assert all(
        row["opaque_completed_job_count"] == row["planned_jobs"]
        and row["opaque_worker_failure_count"] == 0
        and row["opaque_incident_count"] == 0
        for row in receipt["stages"]
    )

    class ThresholdFake(controller.CountingFakeDisposableTransport):
        def execute_batch(
            self, batch: controller.DisposableBatch
        ) -> controller.DisposableBatchResult:
            self.batches.append(batch)
            if batch.stage_ordinal == 9:
                return controller.DisposableBatchResult(
                    status="completed_with_failures",
                    completed_jobs=len(batch.jobs) - 1,
                    failed_jobs=1,
                    incident_count=1,
                )
            return controller.DisposableBatchResult(
                status="completed",
                completed_jobs=len(batch.jobs),
                failed_jobs=0,
                incident_count=0,
            )

        def seal_stage(self, **kwargs) -> controller.DisposableStageResult:
            failed = sum(
                row.failed_jobs for row in kwargs["batch_results"]
            )
            effective = int(kwargs["effective_workers"])
            locked = int(kwargs["stage"]["locked_workers"])
            prior = int(kwargs["prior_safe_workers"])
            if failed:
                return controller.DisposableStageResult(
                    status="measured_with_threshold_breach",
                    thresholds_passed=False,
                    resulting_safe_workers=prior,
                    stage_receipt_path=None,
                )
            return controller.DisposableStageResult(
                status=(
                    "passed"
                    if effective == locked
                    else "held_at_prior_safe"
                ),
                thresholds_passed=True,
                resulting_safe_workers=(
                    locked if effective == locked else prior
                ),
                stage_receipt_path=None,
            )

    threshold_receipt = controller.execute_disposable_round(
        round_plan_path=plan_path,
        transport=ThresholdFake(),
        created_at="2026-07-17T00:00:00+00:00",
    )
    assert threshold_receipt["stages"][9][
        "status"
    ] == "measured_with_threshold_breach"
    assert threshold_receipt["stages"][9][
        "opaque_worker_failure_count"
    ] == 1
    assert threshold_receipt["stages"][9]["resulting_safe_workers"] == 8
    assert threshold_receipt["stages"][12]["effective_workers"] == 8
    assert threshold_receipt["stages"][12][
        "status"
    ] == "held_at_prior_safe"


def _unit_batch(*, round_kind: str) -> controller.DisposableBatch:
    return controller.DisposableBatch(
        round_definition_sha256="a" * 64,
        round_kind=round_kind,
        stage_ordinal=9,
        batch_ordinal=0,
        workload_sha256="b" * 64,
        locked_workers=16,
        effective_workers=8,
        model_ordinal=2,
        agent_id="Agent C",
        model_id=REQUIRED_MODELS[2],
        jobs=({"job_id": "ok"}, {"job_id": "failed"}),
        source_entries=({"opaque": True}, {"opaque": True}),
        artifact_namespace={"opaque": True},
    )


def _unit_transport(monkeypatch, *, worker) -> controller.VPSDisposableTransport:
    transport = object.__new__(controller.VPSDisposableTransport)
    transport._stage = SimpleNamespace(
        stage_ordinal=9,
        locked_workers=16,
        effective_workers=8,
    )
    monkeypatch.setattr(transport, "_run_job", worker)
    monkeypatch.setattr(
        transport,
        "_stop_sampler",
        lambda _context, *, allow_receipt: None,
    )
    return transport


def test_exploratory_worker_failure_is_opaque_and_sealable(monkeypatch) -> None:
    def worker(**kwargs):
        return {
            "status": (
                "completed"
                if kwargs["job"]["job_id"] == "ok"
                else "failed"
            )
        }

    transport = _unit_transport(monkeypatch, worker=worker)
    result = transport.execute_batch(
        _unit_batch(round_kind="exploratory_measurement")
    )

    assert result == controller.DisposableBatchResult(
        status="completed_with_failures",
        completed_jobs=1,
        failed_jobs=1,
        incident_count=1,
    )
    controller._validate_batch_result(
        result, expected_jobs=2, allow_worker_failures=True
    )


def test_finalized_worker_failure_remains_fail_closed(monkeypatch) -> None:
    transport = _unit_transport(
        monkeypatch, worker=lambda **_kwargs: {"status": "failed"}
    )
    with pytest.raises(
        controller.RuntimePolicyError,
        match="finalized disposable VPS batch has 2 real worker failure",
    ):
        transport.execute_batch(
            _unit_batch(round_kind="finalized_validation")
        )


def test_exploratory_unknown_transport_outcome_remains_fail_closed(
    monkeypatch,
) -> None:
    def worker(**_kwargs):
        raise ConnectionError("opaque transport loss")

    transport = _unit_transport(monkeypatch, worker=worker)
    with pytest.raises(
        controller.RuntimePolicyError,
        match="unknown transport outcome",
    ):
        transport.execute_batch(
            _unit_batch(round_kind="exploratory_measurement")
        )


def test_vps_transport_rejects_any_formal_root_overlap() -> None:
    transport = object.__new__(controller.VPSDisposableTransport)
    transport.remote_root = (
        "/srv/agentdojo-full/disposable/namespaces/unit/rounds/" + "a" * 64
    )
    transport.target = SimpleNamespace(
        benchmark_config={
            "runtime_state_root": "/srv/agentdojo-full/runtime-state/formal",
            "remote_raw_root": "/srv/agentdojo-full/sealed/raw/formal",
            "blind_aggregate_root": "/srv/agentdojo-full/blind-monitor/formal",
            "failed_attempt_archive_root": "/srv/agentdojo-full/sealed/failed/formal",
            "retrieval_snapshot_root": "/srv/agentdojo-full/sealed/retrieval/formal",
        }
    )
    transport._assert_isolated_remote_root()

    transport.target.benchmark_config["remote_raw_root"] = (
        "/srv/agentdojo-full/disposable"
    )
    with pytest.raises(
        controller.RuntimePolicyError, match="overlaps a formal evidence root"
    ):
        transport._assert_isolated_remote_root()


def test_real_run_cli_is_explicit_and_never_uses_local_key_argument() -> None:
    from evidence_system.cli.agentdojo_disposable_controller import parse_args

    parsed = parse_args(
        [
            "real-run",
            "--round-plan",
            "round.json",
            "--output",
            "controller.json",
        ]
    )
    assert parsed.command == "real-run"
    assert parsed.round_plan == "round.json"
    assert parsed.output == "controller.json"
    assert not hasattr(parsed, "api_key")
