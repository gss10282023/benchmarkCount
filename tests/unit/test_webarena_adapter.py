from __future__ import annotations

import json
from pathlib import Path

from evidence_system.adapters import webarena_official_worker
from evidence_system.adapters.webarena_verified import _retryable_worker_error
from evidence_system.orchestrator.jobs import _webarena_native_run_is_auditable, plan_smoke_jobs


def test_plan_smoke_jobs_webarena_is_runnable_with_official_worker(tmp_path: Path) -> None:
    planned = plan_smoke_jobs(
        domain="webarena_verified",
        phase="full",
        experiment_type="main",
        case_count=1,
        agent_ids=["Agent A"],
        seed=7,
        manifest_path="experiments/experiment_manifest.yaml",
        source_bundle_path="experiments/evidence_contracts/source_bundles/main_case_units_source_bundle.json",
        contracts_dir="experiments/evidence_contracts/locked",
        infra_config_path="configs/infra.yaml",
        agents_config_path="configs/agents.yaml",
        jobs_dir=tmp_path,
    )
    assert len(planned) == 1
    item = planned[0]
    assert item.execution_plan["status"] == "runnable"
    assert "evidence_system.adapters.webarena_official_worker" in item.execution_plan["runner_command"]
    assert "--shopping-admin-base-url http://127.0.0.1:7780/admin" in item.execution_plan["runner_command"]
    assert "--webarena-repo-dir <WEBARENA_INSTALL_ROOT>" in item.execution_plan["runner_command"]
    assert "--gitlab-base-url http://127.0.0.1:8023" in item.execution_plan["runner_command"]
    assert "--max-steps 30" in item.execution_plan["runner_command"]
    assert "no expected-answer fallback" in "\n".join(item.execution_plan["notes"])
    assert "original web-arena-x/webarena repository" in "\n".join(item.execution_plan["notes"])


def test_webarena_official_worker_builds_repo_environment_exports() -> None:
    config = webarena_official_worker.WebArenaOfficialConfig(
        job={"job_id": "full-webarena-10-agent_a", "task_id": "10", "seed": 7},
        source_entry={},
        output_dir=Path("/tmp/unused-webarena-official-worker-output"),
        task_id=10,
        model_id="openai/gpt-5.4-mini",
        temperature=0.0,
        max_tokens=2048,
        timeout_seconds=120,
        retry=0,
        openrouter_api_key_env="OPENROUTER_API_KEY",
        shopping_base_url="http://127.0.0.1:7770",
        shopping_admin_base_url="http://127.0.0.1:7780/admin",
        reddit_base_url="http://127.0.0.1:9999",
        gitlab_base_url="http://127.0.0.1:8023",
        wikipedia_base_url="http://127.0.0.1:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing",
        map_base_url="http://127.0.0.1:3000",
        webarena_repo_dir="<WEBARENA_INSTALL_ROOT>",
    )

    env = webarena_official_worker._webarena_env_exports(config)

    assert env["SHOPPING"] == "http://127.0.0.1:7770"
    assert env["SHOPPING_ADMIN"] == "http://127.0.0.1:7780/admin"
    assert env["WIKIPEDIA"].endswith("/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing")
    assert env["HOMEPAGE"] == "PASS"


def test_webarena_official_worker_converts_stop_answer_to_structured_response() -> None:
    response, source = webarena_official_worker._response_from_stop_answer(
        "Hannah Lim",
        default_task_type="RETRIEVE",
    )

    assert source == "stop_action_answer"
    assert response["status"] == "SUCCESS"
    assert response["retrieved_data"] == ["Hannah Lim"]


def test_webarena_official_worker_marks_stop_na_as_unknown_error() -> None:
    response, source = webarena_official_worker._response_from_stop_answer(
        "N/A",
        default_task_type="RETRIEVE",
    )

    assert source == "stop_action_na"
    assert response["status"] == "UNKNOWN_ERROR"
    assert response["retrieved_data"] is None


def test_webarena_native_run_audit_accepts_official_cli_runner(tmp_path: Path) -> None:
    root = tmp_path / "results" / "smoke" / "webarena_verified" / "smoke-webarena-10-agent_a" / "adapter"
    native_root = root / "native_run"
    task_dir = native_root / "10"
    llm_calls = root / "llm_calls"
    llm_attempts = native_root / "llm_attempts"
    traces = native_root / "traces"
    official_run = native_root / "official_run"

    for path in (task_dir, llm_calls, llm_attempts, traces, official_run):
        path.mkdir(parents=True, exist_ok=True)

    (native_root / "render_10.html").write_text("<html></html>", encoding="utf-8")
    (traces / "10.zip").write_text("zip", encoding="utf-8")
    (task_dir / "agent_response.json").write_text("{}", encoding="utf-8")
    (task_dir / "official_task_config.json").write_text("{}", encoding="utf-8")
    (task_dir / "solver_trace.json").write_text(
        json.dumps(
            {
                "runner_kind": "official_run_py_prompt",
                "runner_fixes": {
                    "agent_loop": "official_run_py",
                    "prompt": "official_p_cot_id_actree_2s",
                    "action_set": "id_accessibility_tree",
                    "observation_type": "accessibility_tree",
                    "evaluator": "official_evaluator_router",
                    "trace": "render_html_and_playwright_trace",
                },
                "used_expected_fallback": False,
            }
        ),
        encoding="utf-8",
    )
    (native_root / "native_evaluator_input.json").write_text("{}", encoding="utf-8")
    (native_root / "native_evaluator_output.json").write_text('{"status":"success","score":1.0}', encoding="utf-8")
    (native_root / "job.json").write_text("{}", encoding="utf-8")
    (native_root / "source_bundle_entry.json").write_text("{}", encoding="utf-8")
    (native_root / "worker_config.json").write_text("{}", encoding="utf-8")
    (native_root / "webarena_env.json").write_text("{}", encoding="utf-8")
    (native_root / "run_summary.json").write_text(
        json.dumps(
            {
                "status": "completed",
                "runner_kind": "official_run_py_prompt",
                "runner_fixes": {
                    "agent_loop": "official_run_py",
                    "prompt": "official_p_cot_id_actree_2s",
                    "action_set": "id_accessibility_tree",
                    "observation_type": "accessibility_tree",
                    "evaluator": "official_evaluator_router",
                    "trace": "render_html_and_playwright_trace",
                },
                "task_id": 10,
                "used_expected_fallback": False,
                "llm_used": True,
                "success": True,
            }
        ),
        encoding="utf-8",
    )
    (llm_calls / "calls.jsonl").write_text('{"response_metadata":{"status":"success"}}\n', encoding="utf-8")

    assert _webarena_native_run_is_auditable(root) is True


def test_webarena_worker_summary_retries_missing_openrouter_content() -> None:
    assert _retryable_worker_error(
        {
            "status": "error",
            "error_message": "OpenRouter response content is missing",
        }
    )
    assert not _retryable_worker_error(
        {
            "status": "error",
            "error_message": "OpenRouter HTTP 402: insufficient credits",
        }
    )
