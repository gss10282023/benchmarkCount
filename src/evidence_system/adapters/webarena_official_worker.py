"""WebArena browser worker with WebArena-Verified v1.2.3 scoring only."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from typing import Any, Mapping

from evidence_system.adapters.openrouter_chat import (
    extract_response_content,
    request_openrouter_completion,
)
from evidence_system.adapters.webarena_har_sanitization import (
    HarSanitizationError,
    load_and_validate_network_sanitization_receipt,
    sanitize_network_artifacts_before_evaluator,
    sanitize_structured_credential_values,
)


DEFAULT_MAX_STEPS = 30
DEFAULT_OBSERVATION_TYPE = "accessibility_tree"
DEFAULT_ACTION_SET_TAG = "id_accessibility_tree"
DEFAULT_VIEWPORT_WIDTH = 1280
DEFAULT_VIEWPORT_HEIGHT = 720
DEFAULT_SLEEP_AFTER_EXECUTION = 2.0
FALLBACK_PROMPT_TEMPLATE_RELATIVE_PATH = "prompts/webarena_p_cot_id_actree_2s.json"
FALLBACK_PROMPT_TEMPLATE_SHA256 = (
    "cf344fbc9cf72e5f7c26b203bebe5630b28986d91139e618ebf1ddc4697c77cb"
)
PROMPT_TEMPLATE_SOURCE_URL = "https://github.com/web-arena-x/webarena/blob/main/agent/prompts/jsons/p_cot_id_actree_2s.json"
PROMPT_CONSTRUCTOR_SOURCE_URL = "https://github.com/web-arena-x/webarena/blob/main/agent/prompts/prompt_constructor.py"
RUN_PY_SOURCE_URL = "https://github.com/web-arena-x/webarena/blob/main/run.py"
RUNNER_KIND = "project_selected_webarena_dce04686_with_verified_v1_2_3_scorer"
RUNNER_FIXES = {
    "agent_loop": "official_run_py",
    "prompt": "pinned_bundled_p_cot_id_actree_2s",
    "action_set": "id_accessibility_tree",
    "observation_type": "accessibility_tree",
    "task_input": "official_agent_input_get",
    "final_answer_protocol": "strict_structured_json",
    "prompt_contract": "webarena_verified_public_self_classified_four_field_json_v1",
    "evaluator": "webarena_verified_v1_2_3_eval_tasks",
    "trace": "playwright_full_embedded_har",
}

PUBLIC_COMPLETION_CONTRACT_VERSION = (
    "webarena_verified_public_self_classified_four_field_json_v1"
)
PUBLIC_RESPONSE_FIELDS = ("task_type", "status", "retrieved_data", "error_details")
PUBLIC_FAILURE_STATUSES = (
    "ACTION_NOT_ALLOWED_ERROR",
    "PERMISSION_DENIED_ERROR",
    "NOT_FOUND_ERROR",
    "DATA_VALIDATION_ERROR",
    "UNKNOWN_ERROR",
)
AUTHENTICATED_WEBARENA_SITES = frozenset(
    {"gitlab", "shopping", "shopping_admin", "reddit"}
)
_PAGE_CLIENT_BACKING_ATTRIBUTE = "_webarena_verified_cdp_session"


@dataclass(frozen=True)
class WebArenaOfficialConfig:
    job: dict[str, Any]
    source_entry: dict[str, Any]
    output_dir: Path
    task_id: int | None
    model_id: str
    temperature: float
    max_tokens: int
    timeout_seconds: int
    retry: int
    openrouter_api_key_env: str
    shopping_base_url: str
    shopping_admin_base_url: str
    reddit_base_url: str
    gitlab_base_url: str
    wikipedia_base_url: str
    map_base_url: str
    webarena_repo_dir: str
    task_type: str
    task_revision: int
    official_evaluator_config: str
    max_steps: int = DEFAULT_MAX_STEPS
    observation_type: str = DEFAULT_OBSERVATION_TYPE
    action_set_tag: str = DEFAULT_ACTION_SET_TAG
    current_viewport_only: bool = True
    viewport_width: int = DEFAULT_VIEWPORT_WIDTH
    viewport_height: int = DEFAULT_VIEWPORT_HEIGHT
    sleep_after_execution: float = DEFAULT_SLEEP_AFTER_EXECUTION


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-json", required=True)
    parser.add_argument("--source-entry-json", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--task-id")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--retry", type=int, default=0)
    parser.add_argument("--openrouter-api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument("--shopping-base-url", required=True)
    parser.add_argument("--shopping-admin-base-url", required=True)
    parser.add_argument("--reddit-base-url", required=True)
    parser.add_argument("--gitlab-base-url", required=True)
    parser.add_argument("--wikipedia-base-url", required=True)
    parser.add_argument("--map-base-url", required=True)
    parser.add_argument("--webarena-repo-dir", default="<WEBARENA_INSTALL_ROOT>")
    parser.add_argument(
        "--task-type", required=True, choices=("RETRIEVE", "MUTATE", "NAVIGATE")
    )
    parser.add_argument("--task-revision", required=True, type=int)
    parser.add_argument(
        "--official-evaluator-config",
        default="/opt/webarena-verified/v1.2.3/runtime/webarena_verified_runtime_urls.json",
    )
    parser.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS)
    args = parser.parse_args(argv)

    config = WebArenaOfficialConfig(
        job=_loads_json_object(args.job_json, field_name="job-json"),
        source_entry=_loads_json_object(
            args.source_entry_json, field_name="source-entry-json"
        ),
        output_dir=Path(args.output_dir),
        task_id=int(args.task_id) if args.task_id is not None else None,
        model_id=str(args.model_id),
        temperature=float(args.temperature),
        max_tokens=int(args.max_tokens),
        timeout_seconds=int(args.timeout_seconds),
        retry=int(args.retry),
        openrouter_api_key_env=str(args.openrouter_api_key_env),
        shopping_base_url=str(args.shopping_base_url),
        shopping_admin_base_url=str(args.shopping_admin_base_url),
        reddit_base_url=str(args.reddit_base_url),
        gitlab_base_url=str(args.gitlab_base_url),
        wikipedia_base_url=str(args.wikipedia_base_url),
        map_base_url=str(args.map_base_url),
        webarena_repo_dir=str(args.webarena_repo_dir),
        task_type=str(args.task_type),
        task_revision=int(args.task_revision),
        official_evaluator_config=str(args.official_evaluator_config),
        max_steps=int(args.max_steps),
    )
    try:
        summary = run_official_job(config)
    except Exception as exc:  # pragma: no cover - exercised by remote runs.
        summary = _write_error_summary(config, exc)
        print(json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True))
        return 1
    print(json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


def run_official_job(config: WebArenaOfficialConfig) -> dict[str, Any]:
    repo_dir = Path(config.webarena_repo_dir)
    if not repo_dir.exists():
        raise RuntimeError(f"missing original WebArena repo: {repo_dir}")

    output_dir = config.output_dir
    remote_retention = (
        config.job.get("artifact_retention_mode") == "vps_persistent_remote_v1"
    )
    if remote_retention:
        if not output_dir.is_dir() or output_dir.is_symlink():
            raise RuntimeError(
                "remote-retention output directory was not prepared safely"
            )
        existing = {path.name for path in output_dir.iterdir()}
        if existing != {"reset_receipt.json"}:
            raise RuntimeError(
                "remote-retention output directory must contain only the reset receipt"
            )
    else:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    task_id = _resolved_task_id(config)
    task_dir = output_dir / str(task_id)
    task_dir.mkdir(parents=True, exist_ok=True)
    llm_attempts_dir = output_dir / "llm_attempts"
    llm_attempts_dir.mkdir(parents=True, exist_ok=True)
    traces_dir = output_dir / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)
    official_logs_dir = output_dir / "official_run"
    official_logs_dir.mkdir(parents=True, exist_ok=True)

    _write_json(output_dir / "job.json", config.job)
    _write_json(output_dir / "source_bundle_entry.json", config.source_entry)
    _write_json(output_dir / "worker_config.json", _jsonable(asdict(config)))

    official_env = _webarena_env_exports(config)
    _write_json(output_dir / "webarena_env.json", official_env)
    _prepare_repo_assets(config, env_exports=official_env, logs_dir=official_logs_dir)

    runner_kind = RUNNER_KIND
    agent_input = _validated_agent_input(config.source_entry, expected_task_id=task_id)
    trace_path = traces_dir / f"{task_id}.zip"
    har_path = task_dir / "network.har"
    response_path = task_dir / "agent_response.json"
    solver_trace_path = task_dir / "solver_trace.json"
    steps: list[dict[str, Any]] = []
    final_response_source = "missing"
    response_protocol_source = "missing"
    agent = None

    with _temporary_sys_path(repo_dir), _temporary_env(official_env):
        _install_playwright_page_client_compatibility()
        browser_env = importlib.import_module("browser_env")
        actions_mod = importlib.import_module("browser_env.actions")
        helper_mod = importlib.import_module("browser_env.helper_functions")
        auto_login_mod = importlib.import_module("browser_env.auto_login")
        prompt_mod = importlib.import_module("agent.prompts.prompt_constructor")
        lm_config_mod = importlib.import_module("llms.lm_config")

        lm_config = _build_lm_config(lm_config_mod, config)
        prompt_constructor = prompt_mod.CoTPromptConstructor(
            _instruction_path(repo_dir),
            lm_config=lm_config,
            tokenizer=_Cl100kTokenizer(),
        )
        agent = _OpenRouterPromptAgent(
            config=config,
            prompt_constructor=prompt_constructor,
            create_id_based_action=browser_env.create_id_based_action,
            create_none_action=browser_env.create_none_action,
            llm_attempts_dir=llm_attempts_dir,
        )

        render_helper = None
        env = None
        temp_dir: tempfile.TemporaryDirectory[str] | None = None
        try:
            config_file, task_payload, temp_dir = _prepared_task_config(
                repo_dir=repo_dir,
                task_id=task_id,
                auto_login_mod=auto_login_mod,
                timeout_seconds=config.timeout_seconds,
                agent_input=agent_input,
                task_revision=config.task_revision,
            )
            _write_json(task_dir / "official_task_config.json", task_payload)
            _write_text(task_dir / "config_file_path.txt", str(config_file))
            _write_json(
                output_dir / "native_evaluator_input.json",
                {
                    "schema_version": "webarena_verified_native_evaluator_input/v1",
                    "runner_kind": runner_kind,
                    "task_id": task_id,
                    "task_revision": config.task_revision,
                    "agent_response_path": str(response_path),
                    "network_har_path": str(har_path),
                    "evaluator_config_path": config.official_evaluator_config,
                    "evaluator": "ServiceNow/webarena-verified v1.2.3 eval-tasks",
                    "evaluator_image": (
                        "ghcr.io/servicenow/webarena-verified@sha256:"
                        "d2c3f81b615648a806e0b9c9fd392085a45ca719ea773a51976b59d23f7bd1b9"
                    ),
                },
            )

            env = browser_env.ScriptBrowserEnv(
                headless=True,
                slow_mo=0,
                observation_type=config.observation_type,
                current_viewport_only=bool(config.current_viewport_only),
                viewport_size={
                    "width": int(config.viewport_width),
                    "height": int(config.viewport_height),
                },
                save_trace_enabled=True,
                sleep_after_execution=float(config.sleep_after_execution),
            )
            render_helper = helper_mod.RenderHelper(
                str(config_file),
                str(output_dir),
                config.action_set_tag,
            )

            trajectory: list[Any] = []
            meta_data = {"action_history": ["None"]}
            last_stop_action: Mapping[str, Any] | None = None
            final_response_source = "missing"

            with _inject_full_embedded_har(har_path):
                obs, info = env.reset(options={"config_file": str(config_file)})
            state_info = {"observation": obs, "info": info}
            trajectory.append(state_info)

            while True:
                early_stop_flag, stop_info = _early_stop(
                    trajectory,
                    max_steps=int(config.max_steps),
                    thresholds={"parsing_failure": 3, "repeating_action": 3},
                    action_types=actions_mod.ActionTypes,
                    is_equivalent=actions_mod.is_equivalent,
                )
                if early_stop_flag:
                    action = browser_env.create_stop_action(f"Early stop: {stop_info}")
                else:
                    try:
                        action = agent.next_action(
                            trajectory,
                            str(task_payload.get("intent") or ""),
                            meta_data=meta_data,
                        )
                    except ValueError as exc:
                        action = browser_env.create_stop_action(f"ERROR: {exc}")
                trajectory.append(action)

                action_description = helper_mod.get_action_description(
                    action,
                    state_info["info"]["observation_metadata"],
                    action_set_tag=config.action_set_tag,
                    prompt_constructor=prompt_constructor,
                )
                render_helper.render(action, state_info, meta_data, True)
                meta_data["action_history"].append(action_description)

                step_record = {
                    "step": len(steps),
                    "page_url_before": str(state_info["info"]["page"].url),
                    "action": _jsonable(action),
                    "action_description": action_description,
                }

                if action["action_type"] == actions_mod.ActionTypes.STOP:
                    last_stop_action = action
                    final_response_source = "official_stop_action"
                    steps.append(step_record)
                    break

                obs, _, terminated, _, info = env.step(action)
                state_info = {"observation": obs, "info": info}
                trajectory.append(state_info)
                step_record["terminated"] = bool(terminated)
                step_record["page_url_after"] = str(info["page"].url)
                step_record["fail_error"] = str(info.get("fail_error") or "")
                steps.append(step_record)

                if terminated:
                    trajectory.append(browser_env.create_stop_action(""))
                    final_response_source = "environment_terminated"
                    break

            env.save_trace(trace_path)

            agent_response, response_protocol_source = _agent_response_from_stop_action(
                last_stop_action,
                task_type=config.task_type,
                final_response_source=final_response_source,
            )
            _write_json(response_path, agent_response)
            _write_json(
                solver_trace_path,
                {
                    "schema_version": "webarena_verified_solver_trace/v1",
                    "runner_kind": runner_kind,
                    "runner_fixes": dict(RUNNER_FIXES),
                    "task_id": task_id,
                    "task_revision": config.task_revision,
                    "official_task_config_path": str(config_file),
                    "steps": steps,
                    "final_response_source": final_response_source,
                    "response_protocol_source": response_protocol_source,
                    "used_expected_fallback": False,
                    "llm_used": True,
                },
            )
        finally:
            try:
                _close_browser_resources(
                    render_helper=render_helper,
                    env=env,
                )
            finally:
                if temp_dir is not None:
                    temp_dir.cleanup()

    evaluator_summary, har_sanitization = _sanitize_then_evaluate_network_evidence(
        task_id=task_id,
        task_revision=config.task_revision,
        output_dir=output_dir,
        evaluator_config=Path(config.official_evaluator_config),
        har_path=har_path,
        trace_path=trace_path,
    )
    score = float(evaluator_summary["score"])
    native_output = {
        **evaluator_summary,
        "official_render_path": str(output_dir / f"render_{task_id}.html"),
        "official_trace_path": str(trace_path),
        "official_network_har_path": str(har_path),
    }
    _write_json(output_dir / "native_evaluator_output.json", native_output)
    solver_trace = json.loads(solver_trace_path.read_text(encoding="utf-8"))
    solver_trace["official_evaluation_score"] = score
    solver_trace["official_eval_result_path"] = str(task_dir / "eval_result.json")
    _write_json(solver_trace_path, solver_trace)
    summary = {
        "status": "completed",
        "runner_kind": runner_kind,
        "runner_fixes": dict(RUNNER_FIXES),
        "task_id": task_id,
        "task_revision": config.task_revision,
        "success": bool(score >= 1.0),
        "evaluation_status": evaluator_summary["status"],
        "evaluation_score": score,
        "evaluator_version": evaluator_summary["webarena_verified_version"],
        "evaluator_checksum": evaluator_summary["webarena_verified_evaluator_checksum"],
        "data_checksum": evaluator_summary["webarena_verified_data_checksum"],
        "step_count": len(steps),
        "used_expected_fallback": False,
        "llm_used": True,
        "llm_call_count": agent.call_count if agent is not None else 0,
        "official_render_path": str(output_dir / f"render_{task_id}.html"),
        "official_trace_path": str(trace_path),
        "official_network_har_path": str(har_path),
        "official_eval_result_path": str(task_dir / "eval_result.json"),
        "network_har_sanitization": har_sanitization,
    }
    _write_json(output_dir / "run_summary.json", summary)
    return summary


def _install_playwright_page_client_compatibility() -> None:
    """Restore WebArena's legacy ``page.client`` slot on modern Playwright.

    The locked upstream runner assigns a CDP session directly to each sync API
    ``Page`` instance. Playwright 1.56 rejects that dynamic attribute, even
    though the runner still retrieves it through ``get_page_client``. Keep the
    immutable runner tree untouched and attach a property to its wrapper class
    instead; the session lives on the underlying implementation object for the
    lifetime of the single worker process.
    """

    from playwright.sync_api import Page

    _install_page_client_compatibility(Page)


def _install_page_client_compatibility(page_type: type[Any]) -> None:
    """Add the legacy ``client`` property unless the Page class has one."""

    if any("client" in base.__dict__ for base in page_type.__mro__):
        return

    def get_client(page: Any) -> Any:
        try:
            return getattr(page._impl_obj, _PAGE_CLIENT_BACKING_ATTRIBUTE)
        except AttributeError as exc:
            raise AttributeError("WebArena CDP client has not been initialized") from exc

    def set_client(page: Any, client: Any) -> None:
        setattr(page._impl_obj, _PAGE_CLIENT_BACKING_ATTRIBUTE, client)

    setattr(page_type, "client", property(get_client, set_client))


def _close_browser_resources(
    *,
    render_helper: Any,
    env: Any,
) -> None:
    """Close the WebArena Playwright owner on the thread that created it.

    Playwright's synchronous API is greenlet-backed and thread-affine.  Moving
    ``env.close()`` to a helper thread raises ``Cannot switch to a different
    thread`` before the HAR can be sealed.  A bare WebArena ``env.close()``
    exits Playwright but does not reliably flush ``record_har_path``.  Closing
    every page first terminates map/wiki background traffic, after which the
    owning context can seal the HAR without the observed indefinite wait.  The
    complete worker remains bounded by the remote ``timeout(1)`` process
    wrapper and the controller subprocess timeout.
    """

    if render_helper is not None:
        render_helper.close()
    if env is not None:
        try:
            context = getattr(env, "context", None)
            if context is not None:
                for page in list(getattr(context, "pages", ()) or ()):
                    page.close(run_before_unload=False)
                context.close()
        finally:
            env.close()


class _OpenRouterPromptAgent:
    def __init__(
        self,
        *,
        config: WebArenaOfficialConfig,
        prompt_constructor: Any,
        create_id_based_action: Any,
        create_none_action: Any,
        llm_attempts_dir: Path,
    ) -> None:
        self.config = config
        self.prompt_constructor = prompt_constructor
        self.create_id_based_action = create_id_based_action
        self.create_none_action = create_none_action
        self.llm_attempts_dir = llm_attempts_dir
        self.call_count = 0

    def next_action(
        self, trajectory: list[Any], intent: str, meta_data: dict[str, Any]
    ) -> Any:
        prompt = self.prompt_constructor.construct(trajectory, intent, meta_data)
        if not isinstance(prompt, list):
            raise RuntimeError(
                "original WebArena prompt constructor returned non-chat prompt"
            )
        messages = _messages_with_public_completion_contract(
            [_jsonable(item) for item in prompt]
        )
        max_parse_attempts = max(1, int(self.config.retry) + 1)
        force_prefix = str(
            self.prompt_constructor.instruction["meta_data"].get("force_prefix", "")
        )
        last_response_text = ""

        for parse_attempt in range(max_parse_attempts):
            self.call_count += 1
            stem = f"{self.call_count:02d}"
            prompt_payload = {
                "model": self.config.model_id,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "prompt_template_path": str(
                    _instruction_path(Path(self.config.webarena_repo_dir))
                ),
                "prompt_template_source_url": PROMPT_TEMPLATE_SOURCE_URL,
                "prompt_constructor_source_url": PROMPT_CONSTRUCTOR_SOURCE_URL,
                "public_completion_contract_version": PUBLIC_COMPLETION_CONTRACT_VERSION,
                "request_timestamp": _utc_now_iso(),
            }
            _write_json(self.llm_attempts_dir / f"{stem}_prompt.json", prompt_payload)
            response_payload = request_openrouter_completion(
                api_key=_required_env(self.config.openrouter_api_key_env),
                model=self.config.model_id,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout_seconds=self.config.timeout_seconds,
                retry=self.config.retry,
            )
            raw_content = extract_response_content(response_payload)
            response_text = f"{force_prefix}{raw_content}"
            last_response_text = response_text
            response_payload = dict(response_payload)
            response_payload["response_timestamp"] = _utc_now_iso()
            response_payload["raw_content"] = raw_content
            response_payload["response_text"] = response_text
            response_payload["parse_attempt"] = parse_attempt + 1
            try:
                parsed_response = self.prompt_constructor.extract_action(response_text)
                action = self.create_id_based_action(parsed_response)
                action["raw_prediction"] = response_text
                response_payload["parsed_action"] = parsed_response
                response_payload["parse_status"] = "success"
                _write_json(
                    self.llm_attempts_dir / f"{stem}_response.json", response_payload
                )
                return action
            except Exception as exc:
                response_payload["parse_status"] = "failure"
                response_payload["parse_error"] = f"{type(exc).__name__}: {exc}"
                _write_json(
                    self.llm_attempts_dir / f"{stem}_response.json", response_payload
                )
                if parse_attempt + 1 >= max_parse_attempts:
                    action = self.create_none_action()
                    action["raw_prediction"] = last_response_text
                    return action
        action = self.create_none_action()
        action["raw_prediction"] = last_response_text
        return action


def _messages_with_public_completion_contract(
    messages: list[Any],
) -> list[dict[str, Any]]:
    """Append the public contract to the last user turn, after legacy examples."""

    contract = _public_completion_contract()
    normalized: list[dict[str, Any]] = []
    for message in messages:
        if not isinstance(message, Mapping):
            raise RuntimeError(
                "original WebArena prompt contains a non-object chat message"
            )
        normalized.append(dict(message))

    for message in reversed(normalized):
        if str(message.get("role") or "").lower() != "user":
            continue
        content = message.get("content")
        if isinstance(content, str):
            message["content"] = f"{content.rstrip()}\n\n{contract}"
            return normalized
        if isinstance(content, list):
            message["content"] = [*content, {"type": "text", "text": contract}]
            return normalized

    normalized.append({"role": "user", "content": contract})
    return normalized


def _public_completion_contract() -> str:
    retrieve_example = json.dumps(
        {
            "task_type": "RETRIEVE",
            "status": "SUCCESS",
            "retrieved_data": ["<result observed during this run>"],
            "error_details": None,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    mutate_example = json.dumps(
        {
            "task_type": "MUTATE",
            "status": "SUCCESS",
            "retrieved_data": None,
            "error_details": None,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    navigate_example = json.dumps(
        {
            "task_type": "NAVIGATE",
            "status": "SUCCESS",
            "retrieved_data": None,
            "error_details": None,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    failure_statuses = ", ".join(PUBLIC_FAILURE_STATUSES)
    return (
        f"PUBLIC WEBARENA-VERIFIED COMPLETION CONTRACT ({PUBLIC_COMPLETION_CONTRACT_VERSION}):\n"
        "Classify the public objective yourself when you finish: use RETRIEVE when the user asks you to return "
        "information, MUTATE when the user asks you to change website state, or NAVIGATE when the user only asks "
        "you to open or reach a page. No task type is supplied separately.\n"
        "Continue to issue exactly one normal browser action per turn until you are finished. "
        "On the terminal turn, preserve the required action wrapper and put one JSON object inside the stop "
        "brackets. Choose the matching form:\n"
        f"RETRIEVE: In summary, the next action I will perform is ```stop [{retrieve_example}]```\n"
        f"MUTATE: In summary, the next action I will perform is ```stop [{mutate_example}]```\n"
        f"NAVIGATE: In summary, the next action I will perform is ```stop [{navigate_example}]```\n"
        f"The JSON object must contain exactly these four fields: {', '.join(PUBLIC_RESPONSE_FIELDS)}. "
        f"status must be SUCCESS or one of: {failure_statuses}. For RETRIEVE SUCCESS, retrieved_data must be a "
        "JSON array of the result(s) you observed. For MUTATE or NAVIGATE, retrieved_data must be null. "
        "For SUCCESS, error_details must be null. For a failure status, "
        "retrieved_data must be null and error_details must be a non-empty explanation. "
        "Do not use a raw natural-language answer or N/A inside stop. Base the JSON only on the public task "
        "instruction and what you observed or did during this run; do not request or use hidden grading data. "
        "This completion contract overrides earlier stop-action examples that show a plain-text answer."
    )


def _validated_agent_input(
    source_entry: Mapping[str, Any],
    *,
    expected_task_id: int,
) -> dict[str, Any]:
    safe_source_fields = {
        "schema_version",
        "task_id",
        "agent_input",
        "case_packet_sha256",
    }
    if set(source_entry) != safe_source_fields:
        raise RuntimeError(
            "worker source wrapper violates the agent-safe field allowlist"
        )
    if source_entry.get("schema_version") != "webarena_verified_agent_safe_source/v1":
        raise RuntimeError("worker source wrapper has an unsupported schema")
    if int(source_entry.get("task_id", -1)) != expected_task_id:
        raise RuntimeError(
            "worker source wrapper task ID does not match the requested task"
        )
    packet_hash = str(source_entry.get("case_packet_sha256") or "")
    if len(packet_hash) != 64 or any(
        character not in "0123456789abcdef" for character in packet_hash
    ):
        raise RuntimeError("worker source wrapper has an invalid case-packet hash")
    payload = source_entry.get("agent_input")
    if not isinstance(payload, Mapping):
        raise RuntimeError(
            "worker source must contain the official agent-input-get payload"
        )
    value = dict(payload)
    allowed = {"intent", "intent_template_id", "sites", "start_urls", "task_id"}
    if set(value) != allowed:
        raise RuntimeError("official agent input violates the five-field allowlist")
    if int(value["task_id"]) != expected_task_id:
        raise RuntimeError(
            "official agent input task ID does not match the requested task"
        )
    if not isinstance(value["sites"], list) or not value["sites"]:
        raise RuntimeError("official agent input has no sites")
    if not isinstance(value["start_urls"], list) or not value["start_urls"]:
        raise RuntimeError("official agent input has no resolved start URLs")
    if any(
        "__" in str(url) or not str(url).startswith("http://127.0.0.1:")
        for url in value["start_urls"]
    ):
        raise RuntimeError(
            "official agent input contains an unresolved or nonlocal start URL"
        )
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True).lower()
    if any(
        token in serialized
        for token in ('"expected"', '"eval"', '"reference_answer"', "sk-or-v1-")
    ):
        raise RuntimeError(
            "official agent input contains evaluator-private or secret material"
        )
    return value


@contextmanager
def _inject_full_embedded_har(har_path: Path):
    """Inject Playwright HAR options into the legacy environment's new_context call."""

    from playwright.sync_api import Browser

    original = Browser.new_context

    def new_context(browser: Any, *args: Any, **kwargs: Any) -> Any:
        kwargs["record_har_path"] = str(har_path)
        kwargs["record_har_content"] = "embed"
        kwargs["record_har_mode"] = "full"
        return original(browser, *args, **kwargs)

    Browser.new_context = new_context  # type: ignore[method-assign]
    try:
        yield
    finally:
        Browser.new_context = original  # type: ignore[method-assign]


def _validate_har_artifact(path: Path) -> None:
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"missing or empty official evaluator HAR artifact: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid official evaluator HAR artifact: {path}") from exc
    log = payload.get("log") if isinstance(payload, Mapping) else None
    entries = log.get("entries") if isinstance(log, Mapping) else None
    if not isinstance(entries, list) or not entries:
        raise RuntimeError(f"official evaluator HAR has no network entries: {path}")
    if any(
        not isinstance(entry, Mapping) or not isinstance(entry.get("request"), Mapping)
        for entry in entries
    ):
        raise RuntimeError(f"official evaluator HAR has malformed entries: {path}")


def _run_webarena_verified_evaluator(
    *,
    task_id: int,
    task_revision: int,
    output_dir: Path,
    evaluator_config: Path,
) -> dict[str, Any]:
    from evidence_system.adapters.webarena_verified_official_scorer import (
        ScoreRequest,
        score_task,
    )

    request = ScoreRequest(
        task_id=task_id,
        task_revision=task_revision,
        output_root=output_dir,
        runtime_config=evaluator_config,
        summary_output=output_dir / str(task_id) / "eval_summary.json",
    )
    outcome = score_task(request)
    if outcome.exit_code != 0 or outcome.summary.get("scorer_status") != "success":
        raise RuntimeError(
            "official WebArena-Verified evaluator returned an infrastructure/error result"
        )
    if not bool(outcome.summary.get("integrity_verified")):
        raise RuntimeError(
            "official WebArena-Verified evaluator result failed integrity validation"
        )
    return dict(outcome.summary)


def _sanitize_then_evaluate_network_evidence(
    *,
    task_id: int,
    task_revision: int,
    output_dir: Path,
    evaluator_config: Path,
    har_path: Path,
    trace_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Sanitize flushed browser evidence, then score the archived HAR."""

    _validate_har_artifact(har_path)
    sanitization = sanitize_network_artifacts_before_evaluator(
        har_path=har_path,
        trace_path=trace_path,
    )
    _validate_har_artifact(har_path)
    evaluator_summary = _run_webarena_verified_evaluator(
        task_id=task_id,
        task_revision=task_revision,
        output_dir=output_dir,
        evaluator_config=evaluator_config,
    )
    eval_result_path = output_dir / str(task_id) / "eval_result.json"
    eval_result = json.loads(eval_result_path.read_text(encoding="utf-8"))
    if not isinstance(eval_result, dict):
        raise HarSanitizationError("official evaluator result is not a JSON object")
    evaluator_redaction_count = sanitize_structured_credential_values(eval_result)
    if evaluator_redaction_count:
        _write_json(eval_result_path, eval_result)
    evaluator_summary["official_eval_result_sha256"] = hashlib.sha256(
        eval_result_path.read_bytes()
    ).hexdigest()
    evaluator_summary["controller_output_credential_redaction"] = {
        "status": "pass",
        "redacted_value_count": evaluator_redaction_count,
        "original_sensitive_values_retained": False,
        "original_sensitive_value_hashes_retained": False,
    }
    _write_json(output_dir / str(task_id) / "eval_summary.json", evaluator_summary)
    receipt_path = har_path.with_name("network_har_sanitization.json")
    validated = load_and_validate_network_sanitization_receipt(
        receipt_path,
        har_path=har_path,
        trace_path=trace_path,
    )
    if validated != sanitization:
        raise HarSanitizationError(
            "official evaluator changed the network sanitization receipt"
        )
    return evaluator_summary, sanitization


def _prepared_task_config(
    *,
    repo_dir: Path,
    task_id: int,
    auto_login_mod: Any,
    timeout_seconds: int,
    agent_input: Mapping[str, Any],
    task_revision: int,
) -> tuple[Path, dict[str, Any], tempfile.TemporaryDirectory[str] | None]:
    del auto_login_mod  # Authentication is derived from the frozen agent-safe site list.
    config_path = repo_dir / "config_files" / f"{task_id}.json"
    if not config_path.exists():
        raise RuntimeError(f"missing generated WebArena config file: {config_path}")
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise RuntimeError(f"invalid WebArena task config payload: {config_path}")
    task_payload = dict(payload)
    task_payload.pop("eval", None)
    task_payload["task_id"] = task_id
    task_payload["revision"] = int(task_revision)
    task_payload["intent_template_id"] = int(agent_input["intent_template_id"])
    task_payload["intent"] = str(agent_input["intent"])
    task_payload["sites"] = list(agent_input["sites"])
    task_payload["start_url"] = " |AND| ".join(
        str(url) for url in agent_input["start_urls"]
    )
    temp_dir = tempfile.TemporaryDirectory(prefix=f"webarena-task-{task_id}-")
    site_combo = sorted(
        {
            str(site)
            for site in agent_input["sites"]
            if str(site) in AUTHENTICATED_WEBARENA_SITES
        }
    )
    if site_combo:
        # Always create a fresh state after the slot reset.  Reusing the legacy
        # task config's storage_state silently skips authentication for official
        # tasks 759/760 and can carry cookies across slots.
        cookie_file_name = f"{'.'.join(site_combo)}_state.json"
        renew = None
        auto_login_attempts = 0
        for auto_login_attempts in range(1, 3):
            storage_state_path = Path(temp_dir.name) / cookie_file_name
            storage_state_path.unlink(missing_ok=True)
            renew = subprocess.run(
                [
                    sys.executable,
                    "browser_env/auto_login.py",
                    "--auth_folder",
                    temp_dir.name,
                    "--site_list",
                    *site_combo,
                ],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=max(30, int(timeout_seconds)),
                check=False,
            )
            if renew.returncode == 0 and storage_state_path.is_file():
                break
            if auto_login_attempts == 1:
                # A freshly recreated GitLab/Reddit container can satisfy the
                # coarse site sentinel just before its interactive login form
                # becomes ready.  One new-browser retry is deterministic and
                # remains pre-model; never reuse a partial storage state.
                time.sleep(2)
        assert renew is not None
        if renew.returncode != 0:
            raise RuntimeError(
                "official auto_login renewal failed: "
                f"stdout={renew.stdout[-400:]} stderr={renew.stderr[-400:]}"
            )
        if not storage_state_path.is_file() or storage_state_path.stat().st_size <= 0:
            raise RuntimeError(
                "official auto_login did not produce the requested storage state"
            )
        try:
            storage_state_payload = json.loads(
                storage_state_path.read_text(encoding="utf-8")
            )
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("official auto_login produced invalid storage state") from exc
        if not isinstance(storage_state_payload, Mapping) or not any(
            isinstance(storage_state_payload.get(key), list)
            for key in ("cookies", "origins")
        ):
            raise RuntimeError(
                "official auto_login storage state has an invalid Playwright schema"
            )
        task_payload["storage_state"] = str(storage_state_path)
        task_payload["controller_auto_login_attempts"] = auto_login_attempts
    else:
        task_payload.pop("storage_state", None)
    rewritten = Path(temp_dir.name) / config_path.name
    rewritten.write_text(json.dumps(task_payload, indent=2) + "\n", encoding="utf-8")
    return rewritten, task_payload, temp_dir


def _prepare_repo_assets(
    config: WebArenaOfficialConfig,
    *,
    env_exports: Mapping[str, str],
    logs_dir: Path,
) -> None:
    repo_dir = Path(config.webarena_repo_dir)
    _run_repo_command(
        [sys.executable, "scripts/generate_test_data.py"],
        cwd=repo_dir,
        env=env_exports,
        stdout_path=logs_dir / "generate_test_data.stdout.log",
        stderr_path=logs_dir / "generate_test_data.stderr.log",
        timeout_seconds=config.timeout_seconds,
    )


def _run_repo_command(
    argv: list[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    stdout_path: Path,
    stderr_path: Path,
    timeout_seconds: int,
) -> None:
    merged_env = dict(os.environ)
    merged_env.update({key: str(value) for key, value in env.items()})
    completed = subprocess.run(
        argv,
        cwd=cwd,
        env=merged_env,
        capture_output=True,
        text=True,
        timeout=max(30, int(timeout_seconds)),
        check=False,
    )
    _write_text(stdout_path, completed.stdout)
    _write_text(stderr_path, completed.stderr)
    if completed.returncode != 0:
        raise RuntimeError(
            f"official WebArena command failed ({completed.returncode}): {' '.join(argv)}\n"
            f"stdout={completed.stdout[-500:]}\nstderr={completed.stderr[-500:]}"
        )


def _build_lm_config(lm_config_mod: Any, config: WebArenaOfficialConfig) -> Any:
    return lm_config_mod.LMConfig(
        provider="openai",
        model=config.model_id,
        mode="chat",
        gen_config={
            "temperature": config.temperature,
            "top_p": 0.9,
            "context_length": 0,
            "max_tokens": config.max_tokens,
            "stop_token": None,
            "max_obs_length": 1920,
            "max_retry": max(1, int(config.retry) + 1),
        },
    )


class _Cl100kTokenizer:
    def __init__(self) -> None:
        import tiktoken

        self._encoding = tiktoken.get_encoding("cl100k_base")

    def encode(self, text: str) -> list[int]:
        return list(self._encoding.encode(str(text)))

    def decode(self, ids: list[int]) -> str:
        return str(self._encoding.decode(list(ids)))


def _early_stop(
    trajectory: list[Any],
    *,
    max_steps: int,
    thresholds: dict[str, int],
    action_types: Any,
    is_equivalent: Any,
) -> tuple[bool, str]:
    num_steps = (len(trajectory) - 1) / 2
    if num_steps >= max_steps:
        return True, f"Reach max steps {max_steps}"

    k = thresholds["parsing_failure"]
    last_k_actions = trajectory[1::2][-k:]
    if len(last_k_actions) >= k and all(
        action["action_type"] == action_types.NONE for action in last_k_actions
    ):
        return True, f"Failed to parse actions for {k} times"

    k = thresholds["repeating_action"]
    last_k_actions = trajectory[1::2][-k:]
    action_seq = trajectory[1::2]
    if not action_seq:
        return False, ""
    last_action = action_seq[-1]
    if last_action["action_type"] != action_types.TYPE:
        if len(last_k_actions) >= k and all(
            is_equivalent(action, last_action) for action in last_k_actions
        ):
            return True, f"Same action for {k} times"
    else:
        if sum(bool(is_equivalent(action, last_action)) for action in action_seq) >= k:
            return True, f"Same typing action for {k} times"
    return False, ""


def _webarena_env_exports(config: WebArenaOfficialConfig) -> dict[str, str]:
    return {
        "SHOPPING": str(config.shopping_base_url).rstrip("/"),
        "SHOPPING_ADMIN": str(config.shopping_admin_base_url).rstrip("/"),
        "REDDIT": str(config.reddit_base_url).rstrip("/"),
        "GITLAB": str(config.gitlab_base_url).rstrip("/"),
        "MAP": str(config.map_base_url).rstrip("/"),
        "WIKIPEDIA": str(config.wikipedia_base_url).rstrip("/"),
        "HOMEPAGE": "PASS",
    }


def _instruction_path(repo_dir: Path) -> Path:
    del repo_dir  # The mutable/generated upstream JSON is deliberately never selected.
    bundled = Path(__file__).resolve().parent / FALLBACK_PROMPT_TEMPLATE_RELATIVE_PATH
    if not bundled.is_file():
        raise RuntimeError(
            f"missing pinned bundled WebArena prompt template: {bundled}"
        )
    actual_hash = hashlib.sha256(bundled.read_bytes()).hexdigest()
    if actual_hash != FALLBACK_PROMPT_TEMPLATE_SHA256:
        raise RuntimeError(
            "bundled WebArena prompt template hash does not match the frozen source"
        )
    return bundled


def _agent_response_from_stop_action(
    action: Mapping[str, Any] | None,
    *,
    task_type: str,
    final_response_source: str,
) -> tuple[dict[str, Any], str]:
    if not action:
        return (
            _failure_response(
                task_type=task_type,
                error_details=f"missing explicit stop action ({final_response_source})",
            ),
            "missing_stop_action",
        )
    answer = str(action.get("answer") or "")
    return _response_from_stop_answer(answer, task_type=task_type)


def _response_from_stop_answer(
    answer: str, *, task_type: str
) -> tuple[dict[str, Any], str]:
    trimmed = str(answer or "").strip()
    json_payload = _load_json_object_or_none(trimmed)
    if json_payload is None:
        reason = "agent final answer was not valid structured JSON"
        if not trimmed:
            reason = "agent final answer was empty"
        return _failure_response(
            task_type=task_type, error_details=reason
        ), "invalid_structured_json"
    try:
        return _validate_structured_agent_response(
            json_payload, task_type=task_type
        ), "stop_action_json_payload"
    except ValueError as exc:
        return (
            _failure_response(
                task_type=task_type,
                error_details=f"invalid structured final response: {exc}",
            ),
            "invalid_structured_schema",
        )


def _validate_structured_agent_response(
    payload: Mapping[str, Any],
    *,
    task_type: str,
) -> dict[str, Any]:
    required_fields = {"task_type", "status", "retrieved_data", "error_details"}
    if set(payload) != required_fields:
        raise ValueError(
            "fields must be exactly task_type/status/retrieved_data/error_details"
        )
    normalized_task_type = str(payload["task_type"]).upper()
    if normalized_task_type != task_type:
        raise ValueError(f"task_type must be {task_type}")
    status = str(payload["status"]).upper()
    allowed_statuses = {
        "SUCCESS",
        "ACTION_NOT_ALLOWED_ERROR",
        "PERMISSION_DENIED_ERROR",
        "NOT_FOUND_ERROR",
        "DATA_VALIDATION_ERROR",
        "UNKNOWN_ERROR",
    }
    if status not in allowed_statuses:
        raise ValueError("status is not in the public WebArena-Verified schema")
    retrieved_data = payload["retrieved_data"]
    error_details = payload["error_details"]
    if retrieved_data is not None and not isinstance(retrieved_data, list):
        raise ValueError("retrieved_data must be a list or null")
    if normalized_task_type != "RETRIEVE" and retrieved_data is not None:
        raise ValueError("retrieved_data must be null for MUTATE/NAVIGATE")
    if status == "SUCCESS" and error_details is not None:
        raise ValueError("error_details must be null for SUCCESS")
    if status != "SUCCESS" and (
        not isinstance(error_details, str) or not error_details.strip()
    ):
        raise ValueError("error_details must be non-empty for a failure status")
    return {
        "task_type": normalized_task_type,
        "status": status,
        "retrieved_data": _jsonable(retrieved_data),
        "error_details": error_details,
    }


def _load_json_object_or_none(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(loaded, Mapping):
        return None
    return dict(loaded)


def _maybe_json_like_value(raw: str) -> Any:
    text = str(raw or "").strip()
    if not text:
        return ""
    if (text.startswith("{") and text.endswith("}")) or (
        text.startswith("[") and text.endswith("]")
    ):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    if (text.startswith('"') and text.endswith('"')) or (
        text.startswith("'") and text.endswith("'")
    ):
        try:
            return json.loads(text.replace("'", '"'))
        except json.JSONDecodeError:
            return text[1:-1]
    if text in {"true", "false", "null"}:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    if text.replace(".", "", 1).replace("-", "", 1).isdigit():
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    return text


def _failure_response(*, task_type: str, error_details: str) -> dict[str, Any]:
    return {
        "task_type": task_type,
        "status": "UNKNOWN_ERROR",
        "retrieved_data": None,
        "error_details": error_details,
    }


@contextmanager
def _temporary_sys_path(path: Path):
    raw = str(path)
    sys.path.insert(0, raw)
    try:
        yield
    finally:
        try:
            sys.path.remove(raw)
        except ValueError:
            pass


@contextmanager
def _temporary_env(env_exports: Mapping[str, str]):
    previous = {key: os.environ.get(key) for key in env_exports}
    os.environ.update({str(key): str(value) for key, value in env_exports.items()})
    try:
        yield
    finally:
        for key, old_value in previous.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def _resolved_task_id(config: WebArenaOfficialConfig) -> int:
    candidate = config.task_id
    if candidate is None:
        candidate = config.job.get("task_id")
    if candidate is None:
        candidate = config.source_entry.get("task_id")
    if candidate is None:
        raise RuntimeError("unable to determine WebArena task_id")
    return int(candidate)


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"missing environment variable {name}")
    return value


def _loads_json_object(raw: str, *, field_name: str) -> dict[str, Any]:
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must be valid JSON: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"{field_name} must decode to a JSON object")
    return dict(loaded)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonable(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(child) for child in value]
    if isinstance(value, set):
        return sorted(_jsonable(child) for child in value)
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        return _jsonable(tolist())
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        try:
            return _jsonable(model_dump(mode="json"))
        except Exception:
            return _jsonable(model_dump())
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        return str(isoformat())
    if hasattr(value, "__dict__"):
        return {
            key: _jsonable(child)
            for key, child in vars(value).items()
            if not key.startswith("_")
        }
    return str(value)


def _utc_now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_jsonable(payload), ensure_ascii=True, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(content), encoding="utf-8")


def _write_error_summary(
    config: WebArenaOfficialConfig, exc: Exception
) -> dict[str, Any]:
    payload = {
        "status": "error",
        "runner_kind": RUNNER_KIND,
        "runner_fixes": dict(RUNNER_FIXES),
        "task_id": _resolved_task_id(config),
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "traceback": traceback.format_exc(),
    }
    _write_json(config.output_dir / "run_summary.json", payload)
    return payload


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
