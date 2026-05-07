from __future__ import annotations

from types import SimpleNamespace

from evidence_system.cli import run_full


def test_run_full_executes_domains_and_agents_in_order(monkeypatch, capsys) -> None:
    planned_order: list[tuple[str, str]] = []
    executed_order: list[tuple[str, str, int | None]] = []

    def fake_plan_smoke_jobs(**kwargs):
        domain = str(kwargs["domain"])
        agent_id = str(kwargs["agent_ids"][0])
        planned_order.append((domain, agent_id))
        job = {
            "job_id": f"full-{domain}-{agent_id.lower().replace(' ', '_')}",
            "domain": domain,
            "agent_id": agent_id,
        }
        return [SimpleNamespace(job=job, official_split_hash="0" * 64, execution_plan={"status": "runnable"})]

    def fake_execute_planned_jobs(planned, **kwargs):
        item = planned[0]
        executed_order.append((str(item.job["domain"]), str(item.job["agent_id"]), kwargs.get("max_workers")))
        return [SimpleNamespace(planned=item, execution_result={"status": "completed"})]

    monkeypatch.setattr(run_full, "plan_smoke_jobs", fake_plan_smoke_jobs)
    monkeypatch.setattr(run_full, "execute_planned_jobs", fake_execute_planned_jobs)

    status = run_full.main(
        [
            "--domain",
            "agentdojo",
            "--domain",
            "appworld",
            "--agent-id",
            "Agent A",
            "--agent-id",
            "Agent B",
            "--case-count",
            "1",
            "--max-workers",
            "2",
        ]
    )

    assert status == 0
    assert planned_order == [
        ("agentdojo", "Agent A"),
        ("agentdojo", "Agent B"),
        ("appworld", "Agent A"),
        ("appworld", "Agent B"),
    ]
    assert executed_order == [
        ("agentdojo", "Agent A", 2),
        ("agentdojo", "Agent B", 2),
        ("appworld", "Agent A", 2),
        ("appworld", "Agent B", 2),
    ]
    stdout = capsys.readouterr().out
    assert "batch 1/4: agentdojo / Agent A / jobs=1" in stdout
    assert "batch 4/4: appworld / Agent B / jobs=1" in stdout


def test_run_full_runs_webarena_preflight_once_before_first_execution(monkeypatch, capsys) -> None:
    events: list[tuple[str, str, str | bool]] = []

    def fake_plan_smoke_jobs(**kwargs):
        domain = str(kwargs["domain"])
        agent_id = str(kwargs["agent_ids"][0])
        events.append(("plan", domain, agent_id))
        job = {
            "job_id": f"full-{domain}-{agent_id.lower().replace(' ', '_')}",
            "domain": domain,
            "agent_id": agent_id,
        }
        return [SimpleNamespace(job=job, official_split_hash="0" * 64, execution_plan={"status": "runnable"})]

    def fake_preflight(infra_config_path: str, *, as_json: bool):
        events.append(("preflight", infra_config_path, as_json))
        return {
            "status": "ok",
            "machine_id": "webarena-vps-01",
            "with_reset": True,
            "sites": [
                {"site": "shopping", "ok": True},
                {"site": "shopping_admin", "ok": True},
            ],
        }

    def fake_execute_planned_jobs(planned, **kwargs):
        item = planned[0]
        events.append(("execute", str(item.job["domain"]), str(item.job["agent_id"])))
        return [SimpleNamespace(planned=item, execution_result={"status": "completed"})]

    monkeypatch.setattr(run_full, "plan_smoke_jobs", fake_plan_smoke_jobs)
    monkeypatch.setattr(run_full, "_run_webarena_preflight", fake_preflight)
    monkeypatch.setattr(run_full, "execute_planned_jobs", fake_execute_planned_jobs)

    status = run_full.main(
        [
            "--domain",
            "webarena_verified",
            "--agent-id",
            "Agent A",
            "--agent-id",
            "Agent B",
            "--case-count",
            "1",
        ]
    )

    assert status == 0
    assert events == [
        ("plan", "webarena_verified", "Agent A"),
        ("preflight", "configs/infra.yaml", False),
        ("execute", "webarena_verified", "Agent A"),
        ("plan", "webarena_verified", "Agent B"),
        ("execute", "webarena_verified", "Agent B"),
    ]
    stdout = capsys.readouterr().out
    assert "preflight: webarena_verified / ok / failing_sites=none" in stdout


def test_run_full_stops_when_webarena_preflight_fails(monkeypatch, capsys) -> None:
    executed = False

    def fake_plan_smoke_jobs(**kwargs):
        domain = str(kwargs["domain"])
        agent_id = str(kwargs["agent_ids"][0])
        job = {
            "job_id": f"full-{domain}-{agent_id.lower().replace(' ', '_')}",
            "domain": domain,
            "agent_id": agent_id,
        }
        return [SimpleNamespace(job=job, official_split_hash="0" * 64, execution_plan={"status": "runnable"})]

    def fake_preflight(infra_config_path: str, *, as_json: bool):
        return {
            "status": "error",
            "machine_id": "webarena-vps-01",
            "with_reset": True,
            "sites": [
                {
                    "site": "shopping_admin",
                    "ok": False,
                    "container": {"ok": True},
                    "homepage": {"ok": False, "stderr": "missing sentinel substring: Magento Admin"},
                    "sentinels": [],
                }
            ],
        }

    def fake_execute_planned_jobs(planned, **kwargs):
        nonlocal executed
        executed = True
        return [SimpleNamespace(planned=planned[0], execution_result={"status": "completed"})]

    monkeypatch.setattr(run_full, "plan_smoke_jobs", fake_plan_smoke_jobs)
    monkeypatch.setattr(run_full, "_run_webarena_preflight", fake_preflight)
    monkeypatch.setattr(run_full, "execute_planned_jobs", fake_execute_planned_jobs)

    status = run_full.main(
        [
            "--domain",
            "webarena_verified",
            "--agent-id",
            "Agent A",
            "--case-count",
            "1",
        ]
    )

    assert status == 1
    assert executed is False
    stderr = capsys.readouterr().err
    assert "WebArena preflight failed after reset+baseline-check" in stderr
    assert "shopping_admin[homepage=missing sentinel substring: Magento Admin]" in stderr
