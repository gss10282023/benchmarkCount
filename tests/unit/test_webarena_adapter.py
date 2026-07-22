from __future__ import annotations

import hashlib
import json
from pathlib import Path
import threading
from types import SimpleNamespace
import zipfile

import pytest

from evidence_system.adapters import webarena_official_worker
from evidence_system.adapters import webarena_verified
from evidence_system.adapters.webarena_verified import _retryable_worker_error
from evidence_system.orchestrator.jobs import (
    InfraBenchmarkTarget,
    _webarena_native_run_is_auditable,
    plan_smoke_jobs,
)


ROOT = Path(__file__).resolve().parents[2]


def test_webarena_plan_injects_secret_by_ssh_stdin_without_remote_dotenv() -> None:
    source_bundle_path = (
        ROOT
        / "experiments/evidence_contracts/source_bundles"
        / "webarena_verified_full_812_source_bundle.json"
    )
    source_bundle = json.loads(source_bundle_path.read_text(encoding="utf-8"))
    target = InfraBenchmarkTarget(
        machine_id="webarena-gpt54-ord",
        machine_role="webarena_vps",
        ssh_host="45.76.67.186",
        ssh_user="root",
        ssh_port=22,
        ssh_key_path="/tmp/test-only-key",
        remote_workdir="/opt/evidence-system/webarena-full-812",
        runner_workdir=(
            "/opt/webarena-runner/dce04686a56253aefba7b18a4fa0937cf1dc987b/source"
        ),
        benchmark_name="WebArena-Verified",
        benchmark_config={
            "install_dir": (
                "/opt/webarena-runner/"
                "dce04686a56253aefba7b18a4fa0937cf1dc987b/source"
            ),
            "python_bin": (
                "/opt/webarena-runner/"
                "dce04686a56253aefba7b18a4fa0937cf1dc987b/source/.venv/bin/python"
            ),
        },
        benchmark_config_hash="0" * 64,
        runner_command="unused",
        machine_concurrency=1,
    )
    plan = webarena_verified.plan_smoke_execution(
        {"job_id": "test-wv-task-0-agent-a", "task_id": "0", "agent_id": "Agent A"},
        target=target,
        agents_config_path=str(ROOT / "configs/agents.yaml"),
        dotenv_path=".env",
        source_bundle_path=str(source_bundle_path),
        source_bundle=source_bundle,
    )

    command = str(plan["runner_command"])
    assert plan["status"] == "runnable"
    assert plan["secret_env_name"] == "OPENROUTER_API_KEY"
    assert plan["secret_transport"] == "ssh_stdin_process_environment_v1"
    assert "IFS= read -r __evidence_api_key" in command
    assert "export OPENROUTER_API_KEY=\"$__evidence_api_key\"" in command
    assert (
        "PLAYWRIGHT_BROWSERS_PATH=/opt/webarena-verified/v1.2.3/ms-playwright"
        in command
    )
    assert "timeout --signal=TERM --kill-after=30s 2700s env" in command
    assert ".env" not in command
    assert "sk-or-v1-" not in command


def test_webarena_approved_dotenv_overrides_stale_inherited_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "OPENROUTER_API_KEY=approved-test-credential\n", encoding="utf-8"
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "stale-inherited-credential")

    loaded = webarena_verified._load_authoritative_api_key(
        dotenv_path=dotenv,
        secret_env_name="OPENROUTER_API_KEY",
    )

    assert loaded == "approved-test-credential"
    assert loaded != "stale-inherited-credential"


def test_remote_control_error_accepts_only_bounded_error_envelope() -> None:
    envelope = json.dumps(
        {
            "schema_version": "webarena_verified_remote_retention_error/v1",
            "status": "blocked",
            "error_code": "credential_or_billing_failure",
        }
    )
    parsed = webarena_verified._remote_control_error(
        envelope,
        fallback_code="fallback",
        remote_runtime_observed=True,
    )
    malformed = webarena_verified._remote_control_error(
        '{"error_code":"unsafe code with spaces"}',
        fallback_code="fallback",
    )

    assert parsed.public_error_code == "credential_or_billing_failure"
    assert parsed.remote_runtime_observed is True
    assert str(malformed) == "fallback"


def _retention_paths_with_stale_raw_dirs(tmp_path: Path) -> SimpleNamespace:
    root = tmp_path / "slot"
    native_run = root / "native_run"
    logs = root / "logs"
    llm_calls = root / "llm_calls"
    for directory in (native_run, logs, llm_calls):
        directory.mkdir(parents=True)
        (directory / "stale.txt").write_text("stale", encoding="utf-8")
    return SimpleNamespace(
        environment_path=root / "environment.json",
        native_run_dir=native_run,
        logs_dir=logs,
        llm_dir=llm_calls,
    )


def test_remote_retention_already_sealed_keeps_artifacts_on_vps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _retention_paths_with_stale_raw_dirs(tmp_path)
    job = {"record_slot_id": "wv123-task-001-agent-a"}
    target = SimpleNamespace(
        benchmark_config={}, runner_workdir="/runner", remote_workdir="/remote"
    )
    verification = {
        "status": "pass",
        "state": "canonical_reusable",
        "record_slot_id": job["record_slot_id"],
        "verified_over_ssh": True,
    }
    calls: list[str] = []

    monkeypatch.setattr(webarena_verified, "build_job_paths", lambda _: paths)
    monkeypatch.setattr(webarena_verified, "sync_repo_support_files", lambda *_, **__: None)
    monkeypatch.setattr(
        webarena_verified, "write_environment_snapshot", lambda **_: ({}, "0" * 64)
    )
    monkeypatch.setattr(webarena_verified, "_remote_adapter_root", lambda *_: "/vps/slot")
    monkeypatch.setattr(
        webarena_verified,
        "run_remote_blind_command",
        lambda _, command, **__: calls.append(command)
        or SimpleNamespace(returncode=0, stderr="", stdout='{"status":"already_sealed"}'),
    )
    monkeypatch.setattr(
        webarena_verified,
        "_verify_remote_slot_is_canonical",
        lambda *_, **__: verification,
    )

    result = webarena_verified._execute_remote_retention_job(
        job,
        target=target,
        execution_plan={
            "artifact_retention_mode": webarena_verified.RETENTION_MODE,
            "remote_adapter_root": "/vps/slot",
        },
        context=SimpleNamespace(),
    )

    assert calls and "webarena_remote_retention prepare" in calls[0]
    assert result["local_runtime_artifacts_downloaded"] is False
    assert result["remote_evidence_retained_on_vps"] is True
    assert "remote_slot_acceptance_path" not in result
    assert not paths.native_run_dir.exists()
    assert not paths.logs_dir.exists()
    assert not paths.llm_dir.exists()


def test_remote_reconciliation_deletes_local_raw_dirs_without_fetching(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _retention_paths_with_stale_raw_dirs(tmp_path)
    job = {"record_slot_id": "wv123-task-002-agent-b"}
    verification = {
        "status": "pass",
        "state": "canonical_reusable",
        "record_slot_id": job["record_slot_id"],
        "verified_over_ssh": True,
    }

    monkeypatch.setattr(webarena_verified, "build_job_paths", lambda _: paths)
    monkeypatch.setattr(webarena_verified, "sync_repo_support_files", lambda *_, **__: None)
    monkeypatch.setattr(webarena_verified, "_remote_adapter_root", lambda *_: "/vps/slot")
    monkeypatch.setattr(
        webarena_verified,
        "_probe_remote_slot",
        lambda *_, **__: {"state": "canonical_reusable"},
    )
    monkeypatch.setattr(
        webarena_verified,
        "_verify_remote_slot_is_canonical",
        lambda *_, **__: verification,
    )

    result = webarena_verified.reconcile_completed_remote_slot(
        job,
        target=SimpleNamespace(),
        execution_plan={
            "artifact_retention_mode": webarena_verified.RETENTION_MODE,
            "remote_adapter_root": "/vps/slot",
        },
        context=SimpleNamespace(),
    )

    assert result["post_run_reconciliation"] == "already_sealed"
    assert result["paid_runtime_replayed"] is False
    assert result["local_runtime_artifacts_downloaded"] is False
    assert not paths.native_run_dir.exists()
    assert not paths.logs_dir.exists()
    assert not paths.llm_dir.exists()


def test_browser_teardown_stays_on_playwright_owner_thread() -> None:
    owner_thread = threading.get_ident()
    calls: list[tuple[str, int]] = []

    class RenderHelper:
        def close(self) -> None:
            calls.append(("render", threading.get_ident()))

    class Page:
        def close(self, *, run_before_unload: bool) -> None:
            assert run_before_unload is False
            calls.append(("page", threading.get_ident()))

    class Context:
        pages = [Page(), Page()]

        def close(self) -> None:
            calls.append(("context", threading.get_ident()))

    class Environment:
        context = Context()

        def close(self) -> None:
            calls.append(("environment", threading.get_ident()))

    webarena_official_worker._close_browser_resources(
        render_helper=RenderHelper(),
        env=Environment(),
    )

    assert calls == [
        ("render", owner_thread),
        ("page", owner_thread),
        ("page", owner_thread),
        ("context", owner_thread),
        ("environment", owner_thread),
    ]


def test_browser_teardown_uses_environment_close_when_context_was_never_created() -> None:
    calls: list[str] = []

    class Environment:
        context = None

        def close(self) -> None:
            calls.append("environment")

    webarena_official_worker._close_browser_resources(
        render_helper=None,
        env=Environment(),
    )
    assert calls == ["environment"]


def test_page_client_compatibility_uses_the_underlying_playwright_object() -> None:
    class ImplPage:
        pass

    class Page:
        def __init__(self) -> None:
            self._impl_obj = ImplPage()

    page = Page()
    client = object()

    webarena_official_worker._install_page_client_compatibility(Page)
    page.client = client

    assert page.client is client
    assert page._impl_obj._webarena_verified_cdp_session is client


def test_page_client_compatibility_preserves_a_native_page_client() -> None:
    class Page:
        client = "native-client"

    webarena_official_worker._install_page_client_compatibility(Page)

    assert Page.client == "native-client"


def _write_fake_auto_login(repo_dir: Path) -> None:
    script = repo_dir / "browser_env" / "auto_login.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(
        """import argparse, json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--auth_folder', required=True)
p.add_argument('--site_list', nargs='+', required=True)
a=p.parse_args()
folder=Path(a.auth_folder)
folder.mkdir(parents=True, exist_ok=True)
(folder / ('.'.join(a.site_list) + '_state.json')).write_text(
    json.dumps({'cookies': [{'name': 'session', 'value': 'controller-only'}], 'origins': []})
)
(folder / 'invocation.json').write_text(json.dumps(a.site_list))
""",
        encoding="utf-8",
    )


def test_prepared_task_config_logs_in_from_agent_safe_sites_even_without_legacy_state(
    tmp_path: Path,
) -> None:
    repo_dir = tmp_path / "repo"
    config_dir = repo_dir / "config_files"
    config_dir.mkdir(parents=True)
    (config_dir / "759.json").write_text(
        json.dumps(
            {
                "task_id": 759,
                "storage_state": None,
                "eval": [{"expected": "controller-only"}],
            }
        ),
        encoding="utf-8",
    )
    _write_fake_auto_login(repo_dir)

    rewritten, payload, temporary = webarena_official_worker._prepared_task_config(
        repo_dir=repo_dir,
        task_id=759,
        auto_login_mod=object(),
        timeout_seconds=30,
        agent_input={
            "task_id": 759,
            "intent_template_id": 1,
            "intent": "public objective",
            "sites": ["map", "shopping_admin"],
            "start_urls": ["http://127.0.0.1:3030", "http://127.0.0.1:7780/admin"],
        },
        task_revision=2,
    )
    try:
        assert rewritten.is_file()
        assert "eval" not in payload
        assert payload["sites"] == ["map", "shopping_admin"]
        assert Path(payload["storage_state"]).is_file()
        assert Path(payload["storage_state"]).name == "shopping_admin_state.json"
        invocation = Path(temporary.name) / "invocation.json"
        assert json.loads(invocation.read_text(encoding="utf-8")) == [
            "shopping_admin"
        ]
    finally:
        temporary.cleanup()


def test_prepared_task_config_retries_one_pre_model_auto_login_failure(
    tmp_path: Path,
) -> None:
    repo_dir = tmp_path / "repo"
    config_dir = repo_dir / "config_files"
    config_dir.mkdir(parents=True)
    (config_dir / "389.json").write_text("{}\n", encoding="utf-8")
    script = repo_dir / "browser_env" / "auto_login.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        """import argparse, json, sys
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--auth_folder', required=True)
p.add_argument('--site_list', nargs='+', required=True)
a=p.parse_args()
counter=Path(__file__).with_name('attempt_count.txt')
attempt=int(counter.read_text()) + 1 if counter.exists() else 1
counter.write_text(str(attempt))
if attempt == 1:
    raise SystemExit(9)
folder=Path(a.auth_folder)
folder.mkdir(parents=True, exist_ok=True)
(folder / ('.'.join(a.site_list) + '_state.json')).write_text(
    json.dumps({'cookies': [], 'origins': []})
)
""",
        encoding="utf-8",
    )

    _, payload, temporary = webarena_official_worker._prepared_task_config(
        repo_dir=repo_dir,
        task_id=389,
        auto_login_mod=object(),
        timeout_seconds=30,
        agent_input={
            "task_id": 389,
            "intent_template_id": 1,
            "intent": "public objective",
            "sites": ["gitlab"],
            "start_urls": ["http://127.0.0.1:8023"],
        },
        task_revision=2,
    )
    try:
        assert payload["controller_auto_login_attempts"] == 2
        assert Path(payload["storage_state"]).is_file()
    finally:
        temporary.cleanup()


def test_prepared_task_config_removes_stale_state_for_public_only_sites(
    tmp_path: Path,
) -> None:
    repo_dir = tmp_path / "repo"
    config_dir = repo_dir / "config_files"
    config_dir.mkdir(parents=True)
    (config_dir / "97.json").write_text(
        json.dumps({"storage_state": "/stale/cross-slot-state.json"}),
        encoding="utf-8",
    )

    _, payload, temporary = webarena_official_worker._prepared_task_config(
        repo_dir=repo_dir,
        task_id=97,
        auto_login_mod=object(),
        timeout_seconds=30,
        agent_input={
            "task_id": 97,
            "intent_template_id": 1,
            "intent": "public objective",
            "sites": ["map", "wikipedia"],
            "start_urls": ["http://127.0.0.1:3030", "http://127.0.0.1:8888"],
        },
        task_revision=2,
    )
    try:
        assert "storage_state" not in payload
    finally:
        temporary.cleanup()


def test_plan_smoke_jobs_webarena_is_unavailable_without_active_manifest_block(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError, match="manifest has no domain block for webarena_verified"
    ):
        plan_smoke_jobs(
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
        map_base_url="http://127.0.0.1:3030",
        webarena_repo_dir="<WEBARENA_INSTALL_ROOT>",
        task_type="RETRIEVE",
        task_revision=1,
        official_evaluator_config=(
            "/opt/webarena-verified/v1.2.3/runtime/webarena_verified_runtime_urls.json"
        ),
    )

    env = webarena_official_worker._webarena_env_exports(config)

    assert env["SHOPPING"] == "http://127.0.0.1:7770"
    assert env["SHOPPING_ADMIN"] == "http://127.0.0.1:7780/admin"
    assert env["WIKIPEDIA"].endswith(
        "/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing"
    )
    assert env["HOMEPAGE"] == "PASS"


class _FakeWebArenaPromptConstructor:
    instruction = {"meta_data": {"force_prefix": ""}}

    def construct(
        self, trajectory: list[object], intent: str, meta_data: dict[str, object]
    ) -> list[dict[str, str]]:
        del trajectory, meta_data
        return [
            {
                "role": "system",
                "content": "Legacy completion example: stop [plain-text answer].",
            },
            {"role": "user", "content": f"OBJECTIVE: {intent}"},
        ]

    def extract_action(self, response: str) -> str:
        return response.split("```")[-2].strip()


def _prompt_test_worker_config(
    tmp_path: Path, *, task_type: str
) -> webarena_official_worker.WebArenaOfficialConfig:
    return webarena_official_worker.WebArenaOfficialConfig(
        job={"job_id": "prompt-contract-test", "task_id": "44", "seed": 7},
        source_entry={
            "agent_input": {
                "task_id": 44,
                "intent_template_id": 303,
                "sites": ["gitlab"],
                "start_urls": ["http://127.0.0.1:8023"],
                "intent": "Open my todos page",
            }
        },
        output_dir=tmp_path / "output",
        task_id=44,
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
        wikipedia_base_url=(
            "http://127.0.0.1:8888/wikipedia_en_all_maxi_2022-05/"
            "A/User:The_other_Kiwix_guy/Landing"
        ),
        map_base_url="http://127.0.0.1:3030",
        webarena_repo_dir="<WEBARENA_INSTALL_ROOT>",
        task_type=task_type,
        task_revision=2,
        official_evaluator_config=(
            "/opt/webarena-verified/v1.2.3/runtime/webarena_verified_runtime_urls.json"
        ),
    )


@pytest.mark.parametrize(
    ("task_type", "retrieved_data"),
    [
        ("RETRIEVE", ["Hannah Lim"]),
        ("MUTATE", None),
        ("NAVIGATE", None),
    ],
)
def test_webarena_prompt_declares_public_contract_and_stop_json_round_trips(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    task_type: str,
    retrieved_data: list[str] | None,
) -> None:
    response_object = {
        "task_type": task_type,
        "status": "SUCCESS",
        "retrieved_data": retrieved_data,
        "error_details": None,
    }
    action_text = f"stop [{json.dumps(response_object, separators=(',', ':'))}]"
    model_text = f"In summary, the next action I will perform is ```{action_text}```"
    captured_request: dict[str, object] = {}

    def fake_request_openrouter_completion(**kwargs: object) -> dict[str, object]:
        captured_request.update(kwargs)
        return {
            "content": model_text,
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

    def create_id_based_action(parsed: str) -> dict[str, str]:
        assert parsed.startswith("stop [") and parsed.endswith("]")
        return {"action_type": "STOP", "answer": parsed[len("stop [") : -1]}

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-only-placeholder")
    monkeypatch.setattr(
        webarena_official_worker,
        "request_openrouter_completion",
        fake_request_openrouter_completion,
    )
    monkeypatch.setattr(
        webarena_official_worker,
        "extract_response_content",
        lambda payload: str(payload["content"]),
    )
    attempts_dir = tmp_path / "attempts"
    attempts_dir.mkdir()
    agent = webarena_official_worker._OpenRouterPromptAgent(
        config=_prompt_test_worker_config(tmp_path, task_type=task_type),
        prompt_constructor=_FakeWebArenaPromptConstructor(),
        create_id_based_action=create_id_based_action,
        create_none_action=lambda: {"action_type": "NONE"},
        llm_attempts_dir=attempts_dir,
    )

    action = agent.next_action([], "Complete the public task", {})
    structured, source = webarena_official_worker._agent_response_from_stop_action(
        action,
        task_type=task_type,
        final_response_source="official_stop_action",
    )

    messages = captured_request["messages"]
    assert isinstance(messages, list)
    prompt_text = json.dumps(messages, ensure_ascii=False)
    assert "The current task_type is" not in prompt_text
    assert "No task type is supplied separately" in prompt_text
    assert (
        "exactly these four fields: task_type, status, retrieved_data, error_details"
        in prompt_text
    )
    assert "overrides earlier stop-action examples" in prompt_text
    assert "In summary, the next action I will perform is ```stop [" in prompt_text
    for public_type in ("RETRIEVE", "MUTATE", "NAVIGATE"):
        assert f'\\"task_type\\":\\"{public_type}\\"' in prompt_text
    for forbidden in ('"expected"', '"eval"', '"reference_answer"', "sk-or-v1-"):
        assert forbidden not in prompt_text.lower()

    logged_prompt = json.loads(
        (attempts_dir / "01_prompt.json").read_text(encoding="utf-8")
    )
    assert logged_prompt["public_completion_contract_version"] == (
        "webarena_verified_public_self_classified_four_field_json_v1"
    )
    assert "task_type" not in logged_prompt
    assert logged_prompt["messages"] == captured_request["messages"]
    assert source == "stop_action_json_payload"
    assert structured == response_object


def test_webarena_public_contract_is_last_user_message_and_does_not_reveal_controller_type() -> (
    None
):
    original = [
        {"role": "system", "content": "Legacy system rule: stop [plain text]."},
        {
            "role": "assistant",
            "content": "Legacy example: ```stop [a plain-text answer]```",
        },
        {"role": "user", "content": "OBJECTIVE: perform the public task"},
    ]

    messages = webarena_official_worker._messages_with_public_completion_contract(
        original
    )

    assert messages[0] == original[0]
    assert messages[1] == original[1]
    assert messages[-1]["role"] == "user"
    assert str(messages[-1]["content"]).startswith("OBJECTIVE: perform the public task")
    assert "PUBLIC WEBARENA-VERIFIED COMPLETION CONTRACT" in str(
        messages[-1]["content"]
    )
    assert all(
        "PUBLIC WEBARENA-VERIFIED COMPLETION CONTRACT"
        not in str(message.get("content"))
        for message in messages[:-1]
    )
    contract = str(messages[-1]["content"])
    assert "Classify the public objective yourself" in contract
    assert "No task type is supplied separately" in contract
    assert "The current task_type is" not in contract
    for public_type in ("RETRIEVE", "MUTATE", "NAVIGATE"):
        assert public_type in contract
    for forbidden in ('"expected"', '"eval"', '"reference_answer"', "sk-or-v1-"):
        assert forbidden not in contract.lower()


def test_webarena_model_request_does_not_leak_controller_task_type(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    controller_only_marker = "CONTROLLER_ONLY_TASK_TYPE_MARKER"
    captured_request: dict[str, object] = {}

    def fake_request_openrouter_completion(**kwargs: object) -> dict[str, object]:
        captured_request.update(kwargs)
        return {
            "content": "In summary, the next action I will perform is ```click [1]```",
            "usage": {},
        }

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-only-placeholder")
    monkeypatch.setattr(
        webarena_official_worker,
        "request_openrouter_completion",
        fake_request_openrouter_completion,
    )
    monkeypatch.setattr(
        webarena_official_worker,
        "extract_response_content",
        lambda payload: str(payload["content"]),
    )
    attempts_dir = tmp_path / "attempts"
    attempts_dir.mkdir()
    agent = webarena_official_worker._OpenRouterPromptAgent(
        config=_prompt_test_worker_config(tmp_path, task_type=controller_only_marker),
        prompt_constructor=_FakeWebArenaPromptConstructor(),
        create_id_based_action=lambda parsed: {
            "action_type": "CLICK",
            "parsed": parsed,
        },
        create_none_action=lambda: {"action_type": "NONE"},
        llm_attempts_dir=attempts_dir,
    )

    action = agent.next_action([], "Complete the public task", {})

    assert action["action_type"] == "CLICK"
    assert controller_only_marker not in json.dumps(
        captured_request, ensure_ascii=False
    )
    logged = (attempts_dir / "01_prompt.json").read_text(encoding="utf-8")
    assert controller_only_marker not in logged


def test_webarena_stop_json_with_wrong_public_task_type_is_explicit_failure() -> None:
    response, source = webarena_official_worker._response_from_stop_answer(
        json.dumps(
            {
                "task_type": "MUTATE",
                "status": "SUCCESS",
                "retrieved_data": None,
                "error_details": None,
            }
        ),
        task_type="NAVIGATE",
    )

    assert source == "invalid_structured_schema"
    assert response == {
        "task_type": "NAVIGATE",
        "status": "UNKNOWN_ERROR",
        "retrieved_data": None,
        "error_details": "invalid structured final response: task_type must be NAVIGATE",
    }


def test_webarena_official_worker_converts_stop_answer_to_structured_response() -> None:
    response, source = webarena_official_worker._response_from_stop_answer(
        json.dumps(
            {
                "task_type": "RETRIEVE",
                "status": "SUCCESS",
                "retrieved_data": ["Hannah Lim"],
                "error_details": None,
            }
        ),
        task_type="RETRIEVE",
    )

    assert source == "stop_action_json_payload"
    assert response["status"] == "SUCCESS"
    assert response["retrieved_data"] == ["Hannah Lim"]


def test_webarena_official_worker_rejects_natural_language_stop_as_unknown_error() -> (
    None
):
    response, source = webarena_official_worker._response_from_stop_answer(
        "Hannah Lim",
        task_type="RETRIEVE",
    )

    assert source == "invalid_structured_json"
    assert response["status"] == "UNKNOWN_ERROR"
    assert response["retrieved_data"] is None


_WEBARENA_AUDIT_TASK_ID = 102
_WEBARENA_AUDIT_TASK_REVISION = 2
_WEBARENA_CASE_ROOT = (
    Path(__file__).resolve().parents[2]
    / "experiments"
    / "case_packets"
    / "webarena_verified"
)
_WEBARENA_TASK_CONTRACT_SHA256 = (
    "32b2eb76d2296286fae619f843e985feaf1b3eaf622d90d77133ffb580ab0d49"
)
_WEBARENA_EVALUATOR_CHECKSUM = (
    "35c3385b1db4b3378657589f95f50defd4234bd36e5b93d44733fd561b01db4e"
)
_WEBARENA_DATA_CHECKSUM = (
    "d65275660814663375028e9017e1f929e3c38321041b125795e2713b52243d30"
)
_WEBARENA_RUNTIME_CONFIG_SHA256 = (
    "0b54e748bfed53d23852cb0d0f2b54b8a405b8e035b560ff86f3632e7c84f673"
)
_WEBARENA_EVALUATOR_IMAGE = (
    "ghcr.io/servicenow/webarena-verified@sha256:"
    "d2c3f81b615648a806e0b9c9fd392085a45ca719ea773a51976b59d23f7bd1b9"
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _full_embedded_webarena_har() -> dict[str, object]:
    return {
        "log": {
            "version": "1.2",
            "creator": {"name": "Playwright", "version": "1.56.0"},
            "entries": [
                {
                    "startedDateTime": "2026-07-16T00:00:00.000Z",
                    "time": 1,
                    "request": {
                        "method": "GET",
                        "url": "http://127.0.0.1:8023/dashboard/issues",
                        "httpVersion": "HTTP/1.1",
                        "cookies": [],
                        "headers": [{"name": "accept", "value": "text/html"}],
                        "queryString": [],
                        "headersSize": -1,
                        "bodySize": -1,
                    },
                    "response": {
                        "status": 200,
                        "statusText": "OK",
                        "httpVersion": "HTTP/1.1",
                        "cookies": [],
                        "headers": [],
                        "content": {
                            "size": 13,
                            "mimeType": "text/html",
                            "text": "<html></html>",
                        },
                        "redirectURL": "",
                        "headersSize": -1,
                        "bodySize": 13,
                    },
                    "cache": {},
                    "timings": {"send": 0, "wait": 1, "receive": 0},
                }
            ],
        }
    }


def _audit_evaluator_result(
    evaluator_name: str,
    *,
    status: str = "success",
    score: float | None = None,
) -> dict[str, object]:
    if score is None:
        score = 1.0 if status == "success" else 0.0
    return {
        "evaluator_name": evaluator_name,
        "status": status,
        "score": score,
        "assertions": [{"assertion_name": "check", "status": status}],
        "expected": {"controller_only": True},
    }


def _reseal_webarena_audit_artifacts(paths: dict[str, Path]) -> None:
    eval_result = json.loads(paths["eval_result"].read_text(encoding="utf-8"))
    har_sanitization = (
        webarena_official_worker.sanitize_network_artifacts_before_evaluator(
            har_path=paths["network_har"],
            trace_path=paths["trace"],
        )
    )
    evaluator_summaries = []
    for item in eval_result["evaluators_results"]:
        assertion_status_counts: dict[str, int] = {}
        assertions = item.get("assertions") or []
        for assertion in assertions:
            if isinstance(assertion, dict):
                status = str(assertion.get("status"))
                assertion_status_counts[status] = (
                    assertion_status_counts.get(status, 0) + 1
                )
        evaluator_summaries.append(
            {
                "evaluator_name": item["evaluator_name"],
                "status": item["status"],
                "score": float(item["score"]),
                "assertion_count": len(assertions),
                "assertion_status_counts": dict(
                    sorted(assertion_status_counts.items())
                ),
            }
        )

    evaluator_summary = {
        "schema_version": "webarena_verified_official_eval_summary/v1",
        "scorer_status": "success",
        "official_evaluation_completed": True,
        "integrity_verified": True,
        "task_id": eval_result["task_id"],
        "task_revision": eval_result["task_revision"],
        "status": eval_result["status"],
        "score": float(eval_result["score"]),
        "sites": eval_result["sites"],
        "evaluators": evaluator_summaries,
        "official_evaluator_image": _WEBARENA_EVALUATOR_IMAGE,
        "official_evaluator_command_kind": "pinned_docker_eval-tasks",
        "official_evaluator_exit_code": 0,
        "webarena_verified_version": "1.2.3",
        "webarena_verified_evaluator_checksum": _WEBARENA_EVALUATOR_CHECKSUM,
        "webarena_verified_data_checksum": _WEBARENA_DATA_CHECKSUM,
        "task_contract_index_sha256": _WEBARENA_TASK_CONTRACT_SHA256,
        "runtime_config_sha256": _WEBARENA_RUNTIME_CONFIG_SHA256,
        "agent_response_sha256": hashlib.sha256(
            paths["agent_response"].read_bytes()
        ).hexdigest(),
        "network_har_sha256": hashlib.sha256(
            paths["network_har"].read_bytes()
        ).hexdigest(),
        "official_eval_result_sha256": hashlib.sha256(
            paths["eval_result"].read_bytes()
        ).hexdigest(),
        "official_evaluator_stdout_sha256": hashlib.sha256(
            paths["stdout"].read_bytes()
        ).hexdigest(),
        "official_evaluator_stderr_sha256": hashlib.sha256(
            paths["stderr"].read_bytes()
        ).hexdigest(),
        "official_eval_result_is_controller_only": True,
        "summary_contains_private_evaluator_payload": False,
    }
    _write_json(paths["eval_summary"], evaluator_summary)
    _write_json(
        paths["native_output"],
        {
            **evaluator_summary,
            "official_render_path": str(paths["render"]),
            "official_trace_path": str(paths["trace"]),
            "official_network_har_path": str(paths["network_har"]),
        },
    )

    run_summary = json.loads(paths["run_summary"].read_text(encoding="utf-8"))
    run_summary.update(
        {
            "evaluation_status": eval_result["status"],
            "evaluation_score": eval_result["score"],
            "success": eval_result["status"] == "success"
            and float(eval_result["score"]) == 1.0,
            "network_har_sanitization": har_sanitization,
        }
    )
    _write_json(paths["run_summary"], run_summary)
    solver_trace = json.loads(paths["solver_trace"].read_text(encoding="utf-8"))
    solver_trace.update(
        {
            "official_evaluation_score": eval_result["score"],
            "official_eval_result_path": str(paths["eval_result"]),
        }
    )
    _write_json(paths["solver_trace"], solver_trace)


def _build_auditable_webarena_run(tmp_path: Path) -> dict[str, Path]:
    task_id = _WEBARENA_AUDIT_TASK_ID
    task_revision = _WEBARENA_AUDIT_TASK_REVISION
    contract_index = json.loads(
        (_WEBARENA_CASE_ROOT / "task_contract_index.json").read_text(encoding="utf-8")
    )
    contract = next(
        entry for entry in contract_index["entries"] if entry["task_id"] == task_id
    )
    agent_input = json.loads(
        (_WEBARENA_CASE_ROOT / str(task_id) / "agent_input.json").read_text(
            encoding="utf-8"
        )
    )
    root = (
        tmp_path
        / "results"
        / "full"
        / "webarena_verified"
        / f"full-webarena-{task_id}-agent_a"
        / "adapter"
    )
    native_root = root / "native_run"
    task_dir = native_root / str(task_id)
    paths = {
        "root": root,
        "native_root": native_root,
        "task_dir": task_dir,
        "eval_result": task_dir / "eval_result.json",
        "eval_summary": task_dir / "eval_summary.json",
        "native_output": native_root / "native_evaluator_output.json",
        "agent_response": task_dir / "agent_response.json",
        "network_har": task_dir / "network.har",
        "network_har_sanitization": task_dir / "network_har_sanitization.json",
        "stdout": task_dir / "official_evaluator.stdout.log",
        "stderr": task_dir / "official_evaluator.stderr.log",
        "run_summary": native_root / "run_summary.json",
        "solver_trace": task_dir / "solver_trace.json",
        "source_entry": native_root / "source_bundle_entry.json",
        "native_job": native_root / "job.json",
        "worker_config": native_root / "worker_config.json",
        "render": native_root / f"render_{task_id}.html",
        "trace": native_root / "traces" / f"{task_id}.zip",
    }
    for directory in (
        task_dir,
        root / "llm_calls",
        native_root / "llm_attempts",
        native_root / "official_run",
        native_root / "traces",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    runner_kind = webarena_official_worker.RUNNER_KIND
    fixes = dict(webarena_official_worker.RUNNER_FIXES)
    job = {
        "schema_version": "job/v1",
        "job_id": f"full-webarena-{task_id}-agent_a",
        "domain": "webarena_verified",
        "case_unit_id": str(task_id),
        "task_id": str(task_id),
        "contract_id": f"full-webarena-{task_id}",
        "contract_version": "1.0.0",
        "contract_hash": "c" * 64,
        "evidence_contract_id": f"full-webarena-{task_id}",
        "evidence_contract_version": "1.0.0",
        "evidence_contract_hash": "c" * 64,
    }
    source_entry = {
        "schema_version": "webarena_verified_agent_safe_source/v1",
        "task_id": task_id,
        "case_packet_sha256": contract["case_packet_sha256"],
        "agent_input": agent_input,
    }
    _write_json(paths["native_job"], job)
    _write_json(paths["source_entry"], source_entry)
    _write_json(
        paths["worker_config"],
        {
            "job": job,
            "source_entry": source_entry,
            "task_id": task_id,
            "task_revision": task_revision,
            "task_type": contract["task_type"],
            "official_evaluator_config": (
                "/opt/webarena-verified/v1.2.3/runtime/"
                "webarena_verified_runtime_urls.json"
            ),
        },
    )
    _write_json(
        native_root / "native_evaluator_input.json",
        {
            "schema_version": "webarena_verified_native_evaluator_input/v1",
            "runner_kind": runner_kind,
            "task_id": task_id,
            "task_revision": task_revision,
            "agent_response_path": str(paths["agent_response"]),
            "network_har_path": str(paths["network_har"]),
            "evaluator_config_path": (
                "/opt/webarena-verified/v1.2.3/runtime/"
                "webarena_verified_runtime_urls.json"
            ),
            "evaluator": "ServiceNow/webarena-verified v1.2.3 eval-tasks",
            "evaluator_image": _WEBARENA_EVALUATOR_IMAGE,
        },
    )
    _write_json(
        task_dir / "official_task_config.json",
        {
            "task_id": task_id,
            "revision": task_revision,
            "intent_template_id": contract["intent_template_id"],
            "intent": agent_input["intent"],
            "sites": agent_input["sites"],
            "start_url": " |AND| ".join(agent_input["start_urls"]),
        },
    )
    _write_json(
        paths["agent_response"],
        {
            "task_type": "NAVIGATE",
            "status": "SUCCESS",
            "retrieved_data": None,
            "error_details": None,
        },
    )
    _write_json(paths["network_har"], _full_embedded_webarena_har())
    _write_json(
        paths["solver_trace"],
        {
            "schema_version": "webarena_verified_solver_trace/v1",
            "runner_kind": runner_kind,
            "runner_fixes": fixes,
            "task_id": task_id,
            "task_revision": task_revision,
            "steps": [{"step": 0}],
            "used_expected_fallback": False,
            "llm_used": True,
        },
    )
    _write_json(
        paths["eval_result"],
        {
            "task_id": task_id,
            "intent_template_id": contract["intent_template_id"],
            "sites": contract["sites"],
            "task_revision": task_revision,
            "status": "success",
            "score": 1.0,
            "evaluators_results": [
                _audit_evaluator_result("AgentResponseEvaluator"),
                _audit_evaluator_result("NetworkEventEvaluator"),
                _audit_evaluator_result("NetworkEventEvaluator"),
            ],
            "webarena_verified_version": "1.2.3",
            "webarena_verified_evaluator_checksum": _WEBARENA_EVALUATOR_CHECKSUM,
            "webarena_verified_data_checksum": _WEBARENA_DATA_CHECKSUM,
        },
    )
    _write_json(
        paths["run_summary"],
        {
            "status": "completed",
            "runner_kind": runner_kind,
            "runner_fixes": fixes,
            "task_id": task_id,
            "task_revision": task_revision,
            "evaluator_version": "1.2.3",
            "evaluator_checksum": _WEBARENA_EVALUATOR_CHECKSUM,
            "data_checksum": _WEBARENA_DATA_CHECKSUM,
            "used_expected_fallback": False,
            "llm_used": True,
            "llm_call_count": 1,
            "official_render_path": str(paths["render"]),
            "official_trace_path": str(paths["trace"]),
            "official_network_har_path": str(paths["network_har"]),
            "official_eval_result_path": str(paths["eval_result"]),
        },
    )
    paths["render"].write_text("<html></html>", encoding="utf-8")
    with zipfile.ZipFile(paths["trace"], "w") as archive:
        archive.writestr("trace.trace", '{"type":"after","callId":"1"}\n')
        archive.writestr(
            "trace.network",
            '{"type":"resource-snapshot","snapshot":{}}\n',
        )
    paths["stdout"].write_text("official evaluator ok\n", encoding="utf-8")
    paths["stderr"].write_text("", encoding="utf-8")
    _write_json(native_root / "webarena_env.json", {"GITLAB": "http://127.0.0.1:8023"})
    (root / "llm_calls" / "calls.jsonl").write_text(
        '{"response_metadata":{"status":"success"}}\n',
        encoding="utf-8",
    )
    _reseal_webarena_audit_artifacts(paths)
    return paths


def test_webarena_native_run_audit_accepts_only_project_selected_runner_with_official_scorer(
    tmp_path: Path,
) -> None:
    paths = _build_auditable_webarena_run(tmp_path)

    assert _webarena_native_run_is_auditable(paths["root"]) is True

    summary = json.loads(paths["run_summary"].read_text(encoding="utf-8"))
    summary["runner_kind"] = "webarena_verified_v1_2_3_official_cli"
    _write_json(paths["run_summary"], summary)
    assert _webarena_native_run_is_auditable(paths["root"]) is False


@pytest.mark.parametrize(
    "mutation",
    [
        "remove_duplicate_evaluator",
        "reorder_evaluators",
        "task_evaluator_aggregate_mismatch",
        "evaluator_status_score_mismatch",
        "task_status_score_mismatch",
        "task_contract_hash",
        "task_revision",
        "case_packet_hash",
        "native_job_task_id",
        "stdout_log",
        "stderr_log",
        "success_false_for_official_success",
        "success_true_for_official_failure",
        "agent_input",
    ],
)
def test_webarena_native_run_audit_rejects_individually_resealed_mutations(
    tmp_path: Path,
    mutation: str,
) -> None:
    paths = _build_auditable_webarena_run(tmp_path)
    eval_result = json.loads(paths["eval_result"].read_text(encoding="utf-8"))

    if mutation == "remove_duplicate_evaluator":
        eval_result["evaluators_results"].pop()
        _write_json(paths["eval_result"], eval_result)
        _reseal_webarena_audit_artifacts(paths)
    elif mutation == "reorder_evaluators":
        evaluators = eval_result["evaluators_results"]
        eval_result["evaluators_results"] = [
            evaluators[1],
            evaluators[0],
            evaluators[2],
        ]
        _write_json(paths["eval_result"], eval_result)
        _reseal_webarena_audit_artifacts(paths)
    elif mutation == "task_evaluator_aggregate_mismatch":
        eval_result["evaluators_results"][1].update({"status": "failure", "score": 0.0})
        _write_json(paths["eval_result"], eval_result)
        _reseal_webarena_audit_artifacts(paths)
    elif mutation == "evaluator_status_score_mismatch":
        eval_result["evaluators_results"][1]["status"] = "failure"
        _write_json(paths["eval_result"], eval_result)
        _reseal_webarena_audit_artifacts(paths)
    elif mutation == "task_status_score_mismatch":
        eval_result["status"] = "failure"
        eval_result["evaluators_results"][0].update({"status": "failure", "score": 0.0})
        _write_json(paths["eval_result"], eval_result)
        _reseal_webarena_audit_artifacts(paths)
    elif mutation == "task_contract_hash":
        eval_summary = json.loads(paths["eval_summary"].read_text(encoding="utf-8"))
        eval_summary["task_contract_index_sha256"] = "0" * 64
        _write_json(paths["eval_summary"], eval_summary)
        native_output = json.loads(paths["native_output"].read_text(encoding="utf-8"))
        native_output["task_contract_index_sha256"] = "0" * 64
        _write_json(paths["native_output"], native_output)
    elif mutation == "task_revision":
        summary = json.loads(paths["run_summary"].read_text(encoding="utf-8"))
        summary["task_revision"] += 1
        _write_json(paths["run_summary"], summary)
    elif mutation == "case_packet_hash":
        source = json.loads(paths["source_entry"].read_text(encoding="utf-8"))
        source["case_packet_sha256"] = "0" * 64
        _write_json(paths["source_entry"], source)
        worker = json.loads(paths["worker_config"].read_text(encoding="utf-8"))
        worker["source_entry"] = source
        _write_json(paths["worker_config"], worker)
    elif mutation == "native_job_task_id":
        job = json.loads(paths["native_job"].read_text(encoding="utf-8"))
        job["task_id"] = "103"
        _write_json(paths["native_job"], job)
        worker = json.loads(paths["worker_config"].read_text(encoding="utf-8"))
        worker["job"] = job
        _write_json(paths["worker_config"], worker)
    elif mutation == "stdout_log":
        paths["stdout"].write_text(
            "tampered after evaluator summary\n", encoding="utf-8"
        )
    elif mutation == "stderr_log":
        paths["stderr"].write_text(
            "tampered after evaluator summary\n", encoding="utf-8"
        )
    elif mutation == "success_false_for_official_success":
        summary = json.loads(paths["run_summary"].read_text(encoding="utf-8"))
        summary["success"] = False
        _write_json(paths["run_summary"], summary)
    elif mutation == "success_true_for_official_failure":
        eval_result["status"] = "failure"
        eval_result["score"] = 0.0
        eval_result["evaluators_results"][0].update({"status": "failure", "score": 0.0})
        _write_json(paths["eval_result"], eval_result)
        _reseal_webarena_audit_artifacts(paths)
        summary = json.loads(paths["run_summary"].read_text(encoding="utf-8"))
        summary["success"] = True
        _write_json(paths["run_summary"], summary)
    elif mutation == "agent_input":
        source = json.loads(paths["source_entry"].read_text(encoding="utf-8"))
        source["agent_input"]["intent"] += " tampered"
        _write_json(paths["source_entry"], source)
        worker = json.loads(paths["worker_config"].read_text(encoding="utf-8"))
        worker["source_entry"] = source
        _write_json(paths["worker_config"], worker)
    else:  # pragma: no cover - protects the test table itself.
        raise AssertionError(f"unknown mutation: {mutation}")

    assert _webarena_native_run_is_auditable(paths["root"]) is False


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
def test_webarena_remote_sync_is_scoped_to_webarena_runtime() -> None:
    paths = set(webarena_verified.WEB_ARENA_SYNC_PATHS)

    assert {
        "src/evidence_system/adapters/webarena_har_sanitization.py",
        "src/evidence_system/adapters/webarena_official_worker.py",
        "src/evidence_system/adapters/webarena_remote_retention.py",
        "src/evidence_system/adapters/webarena_verified.py",
        "experiments/step20/webarena_verified/jobs/full",
    }.issubset(paths)
    assert "src/evidence_system" not in paths
    assert not any("agentdojo" in path or "appworld" in path for path in paths)
