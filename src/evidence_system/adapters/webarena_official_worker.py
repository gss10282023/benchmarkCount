"""WebArena runner aligned to the original `web-arena-x/webarena` baseline."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict, dataclass
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


DEFAULT_MAX_STEPS = 30
DEFAULT_OBSERVATION_TYPE = "accessibility_tree"
DEFAULT_ACTION_SET_TAG = "id_accessibility_tree"
DEFAULT_VIEWPORT_WIDTH = 1280
DEFAULT_VIEWPORT_HEIGHT = 720
DEFAULT_SLEEP_AFTER_EXECUTION = 2.0
PROMPT_TEMPLATE_RELATIVE_PATH = "agent/prompts/jsons/p_cot_id_actree_2s.json"
FALLBACK_PROMPT_TEMPLATE_RELATIVE_PATH = "prompts/webarena_p_cot_id_actree_2s.json"
PROMPT_TEMPLATE_SOURCE_URL = "https://github.com/web-arena-x/webarena/blob/main/agent/prompts/jsons/p_cot_id_actree_2s.json"
PROMPT_CONSTRUCTOR_SOURCE_URL = "https://github.com/web-arena-x/webarena/blob/main/agent/prompts/prompt_constructor.py"
RUN_PY_SOURCE_URL = "https://github.com/web-arena-x/webarena/blob/main/run.py"
RUNNER_FIXES = {
    "agent_loop": "official_run_py",
    "prompt": "official_p_cot_id_actree_2s",
    "action_set": "id_accessibility_tree",
    "observation_type": "accessibility_tree",
    "evaluator": "official_evaluator_router",
    "trace": "render_html_and_playwright_trace",
}


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
    parser.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS)
    args = parser.parse_args(argv)

    config = WebArenaOfficialConfig(
        job=_loads_json_object(args.job_json, field_name="job-json"),
        source_entry=_loads_json_object(args.source_entry_json, field_name="source-entry-json"),
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

    with _temporary_sys_path(repo_dir), _temporary_env(official_env):
        browser_env = importlib.import_module("browser_env")
        actions_mod = importlib.import_module("browser_env.actions")
        helper_mod = importlib.import_module("browser_env.helper_functions")
        auto_login_mod = importlib.import_module("browser_env.auto_login")
        prompt_mod = importlib.import_module("agent.prompts.prompt_constructor")
        lm_config_mod = importlib.import_module("llms.lm_config")
        evaluator_mod = importlib.import_module("evaluation_harness")

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
            )
            _write_json(task_dir / "official_task_config.json", task_payload)
            _write_text(task_dir / "config_file_path.txt", str(config_file))
            _write_json(
                output_dir / "native_evaluator_input.json",
                {
                    "schema_version": "webarena_native_evaluator_input/v4",
                    "runner_kind": "official_run_py_prompt",
                    "task_id": task_id,
                    "official_repo_dir": str(repo_dir),
                    "official_prompt_path": str(_instruction_path(repo_dir)),
                    "official_task_config_path": str(config_file),
                    "official_task_config": task_payload,
                    "webarena_env": official_env,
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
            steps: list[dict[str, Any]] = []
            meta_data = {"action_history": ["None"]}
            last_stop_action: Mapping[str, Any] | None = None
            final_response_source = "missing"

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
                        action = agent.next_action(trajectory, str(task_payload.get("intent") or ""), meta_data=meta_data)
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

            score = float(
                evaluator_mod.evaluator_router(str(config_file))(
                    trajectory=trajectory,
                    config_file=str(config_file),
                    page=env.page,
                    client=env.get_page_client(env.page),
                )
            )
            env.save_trace(traces_dir / f"{task_id}.zip")

            agent_response = _agent_response_from_stop_action(
                last_stop_action,
                default_task_type=_default_task_type(config.source_entry),
                final_response_source=final_response_source,
            )
            native_output = {
                "status": "success" if score >= 1.0 else "fail",
                "score": score,
                "task_id": task_id,
                "official_render_path": str(output_dir / f"render_{task_id}.html"),
                "official_trace_path": str(traces_dir / f"{task_id}.zip"),
            }
            _write_json(task_dir / "agent_response.json", agent_response)
            _write_json(
                task_dir / "solver_trace.json",
                {
                    "schema_version": "webarena_original_trace/v1",
                    "runner_kind": "official_run_py_prompt",
                    "runner_fixes": dict(RUNNER_FIXES),
                    "task_id": task_id,
                    "official_task_config_path": str(config_file),
                    "steps": steps,
                    "final_response_source": final_response_source,
                    "used_expected_fallback": False,
                    "llm_used": True,
                    "score": score,
                },
            )
            _write_json(output_dir / "native_evaluator_output.json", native_output)
            summary = {
                "status": "completed",
                "runner_kind": "official_run_py_prompt",
                "runner_fixes": dict(RUNNER_FIXES),
                "task_id": task_id,
                "success": bool(score >= 1.0),
                "evaluation_status": native_output["status"],
                "evaluation_score": score,
                "step_count": len(steps),
                "used_expected_fallback": False,
                "llm_used": True,
                "llm_call_count": agent.call_count,
                "official_render_path": str(output_dir / f"render_{task_id}.html"),
                "official_trace_path": str(traces_dir / f"{task_id}.zip"),
            }
            _write_json(output_dir / "run_summary.json", summary)
            return summary
        finally:
            if render_helper is not None:
                render_helper.close()
            if env is not None:
                env.close()
            if temp_dir is not None:
                temp_dir.cleanup()


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

    def next_action(self, trajectory: list[Any], intent: str, meta_data: dict[str, Any]) -> Any:
        prompt = self.prompt_constructor.construct(trajectory, intent, meta_data)
        if not isinstance(prompt, list):
            raise RuntimeError("original WebArena prompt constructor returned non-chat prompt")
        messages = [_jsonable(item) for item in prompt]
        max_parse_attempts = max(1, int(self.config.retry) + 1)
        force_prefix = str(self.prompt_constructor.instruction["meta_data"].get("force_prefix", ""))
        last_response_text = ""

        for parse_attempt in range(max_parse_attempts):
            self.call_count += 1
            stem = f"{self.call_count:02d}"
            prompt_payload = {
                "model": self.config.model_id,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "prompt_template_path": str(_instruction_path(Path(self.config.webarena_repo_dir))),
                "prompt_template_source_url": PROMPT_TEMPLATE_SOURCE_URL,
                "prompt_constructor_source_url": PROMPT_CONSTRUCTOR_SOURCE_URL,
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
                _write_json(self.llm_attempts_dir / f"{stem}_response.json", response_payload)
                return action
            except Exception as exc:
                response_payload["parse_status"] = "failure"
                response_payload["parse_error"] = f"{type(exc).__name__}: {exc}"
                _write_json(self.llm_attempts_dir / f"{stem}_response.json", response_payload)
                if parse_attempt + 1 >= max_parse_attempts:
                    action = self.create_none_action()
                    action["raw_prediction"] = last_response_text
                    return action
        action = self.create_none_action()
        action["raw_prediction"] = last_response_text
        return action


def _prepared_task_config(
    *,
    repo_dir: Path,
    task_id: int,
    auto_login_mod: Any,
    timeout_seconds: int,
) -> tuple[Path, dict[str, Any], tempfile.TemporaryDirectory[str] | None]:
    config_path = repo_dir / "config_files" / f"{task_id}.json"
    if not config_path.exists():
        raise RuntimeError(f"missing generated WebArena config file: {config_path}")
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise RuntimeError(f"invalid WebArena task config payload: {config_path}")
    task_payload = dict(payload)
    storage_state = str(task_payload.get("storage_state") or "")
    if not storage_state:
        return config_path, task_payload, None

    cookie_file_name = os.path.basename(storage_state)
    site_combo = list(auto_login_mod.get_site_comb_from_filepath(cookie_file_name))
    temp_dir = tempfile.TemporaryDirectory(prefix=f"webarena-task-{task_id}-")
    renew = subprocess.run(
        [sys.executable, "browser_env/auto_login.py", "--auth_folder", temp_dir.name, "--site_list", *site_combo],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=max(30, int(timeout_seconds)),
        check=False,
    )
    if renew.returncode != 0:
        raise RuntimeError(
            "official auto_login renewal failed: "
            f"stdout={renew.stdout[-400:]} stderr={renew.stderr[-400:]}"
        )
    task_payload["storage_state"] = f"{temp_dir.name}/{cookie_file_name}"
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
    if len(last_k_actions) >= k and all(action["action_type"] == action_types.NONE for action in last_k_actions):
        return True, f"Failed to parse actions for {k} times"

    k = thresholds["repeating_action"]
    last_k_actions = trajectory[1::2][-k:]
    action_seq = trajectory[1::2]
    if not action_seq:
        return False, ""
    last_action = action_seq[-1]
    if last_action["action_type"] != action_types.TYPE:
        if len(last_k_actions) >= k and all(is_equivalent(action, last_action) for action in last_k_actions):
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
    official_json = repo_dir / PROMPT_TEMPLATE_RELATIVE_PATH
    if official_json.exists():
        return official_json
    bundled = Path(__file__).resolve().parent / FALLBACK_PROMPT_TEMPLATE_RELATIVE_PATH
    if bundled.exists():
        return bundled
    raise RuntimeError(
        "missing WebArena prompt template: neither "
        f"{official_json} nor {bundled} exists"
    )


def _agent_response_from_stop_action(
    action: Mapping[str, Any] | None,
    *,
    default_task_type: str,
    final_response_source: str,
) -> dict[str, Any]:
    if not action:
        return _failure_response(task_type=default_task_type, error_details=f"missing explicit stop action ({final_response_source})")
    answer = str(action.get("answer") or "")
    response, source = _response_from_stop_answer(answer, default_task_type=default_task_type)
    response["final_response_source"] = source
    response["raw_prediction"] = str(action.get("raw_prediction") or "")
    return response


def _response_from_stop_answer(answer: str, *, default_task_type: str) -> tuple[dict[str, Any], str]:
    trimmed = str(answer or "").strip()
    json_payload = _load_json_object_or_none(trimmed)
    if isinstance(json_payload, Mapping) and "task_type" in json_payload and "status" in json_payload:
        return dict(json_payload), "stop_action_json_payload"
    if not trimmed:
        return (
            {
                "task_type": default_task_type,
                "status": "SUCCESS",
                "retrieved_data": [],
                "error_details": None,
            },
            "stop_action_empty_answer",
        )
    if trimmed.upper() == "N/A":
        return (
            {
                "task_type": default_task_type,
                "status": "UNKNOWN_ERROR",
                "retrieved_data": None,
                "error_details": "agent stopped with N/A",
            },
            "stop_action_na",
        )
    return (
        {
            "task_type": default_task_type,
            "status": "SUCCESS",
            "retrieved_data": _retrieved_data_from_stop_answer(trimmed),
            "error_details": None,
        },
        "stop_action_answer",
    )


def _retrieved_data_from_stop_answer(answer: str) -> list[Any]:
    parsed = _maybe_json_like_value(answer)
    if isinstance(parsed, list):
        return _jsonable(parsed)
    if parsed is None:
        return []
    return [_jsonable(parsed)]


def _default_task_type(source_entry: Mapping[str, Any]) -> str:
    visible_inputs = dict(source_entry.get("visible_inputs") or {})
    task_text = dict(visible_inputs.get("task_text") or {})
    for item in list(task_text.get("eval") or visible_inputs.get("evaluator_description") or []):
        if not isinstance(item, Mapping):
            continue
        expected = item.get("expected")
        if isinstance(expected, Mapping) and expected.get("task_type"):
            return str(expected["task_type"])
    return "RETRIEVE"


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
    if (text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]")):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
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
    path.write_text(json.dumps(_jsonable(payload), ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(content), encoding="utf-8")


def _write_error_summary(config: WebArenaOfficialConfig, exc: Exception) -> dict[str, Any]:
    payload = {
        "status": "error",
        "runner_kind": "official_run_py_prompt",
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
