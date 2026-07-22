"""Thin AndroidWorld smoke worker with OpenRouter-backed T3A execution."""

from __future__ import annotations

import argparse
import base64
from dataclasses import asdict, dataclass
import dataclasses
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import traceback
from typing import Any, Mapping
import urllib.error
import urllib.request

import numpy as np
from PIL import Image


OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
_PREFLIGHT_APP_NAMES = frozenset(
    {
        "broccoli app",
        "clipper",
        "markor",
        "pro expense",
        "simple calendar pro",
        "simple sms messenger",
    }
)
_REQUIRED_DEVICE_PATHS: dict[str, tuple[str, ...]] = {
    "broccoli app": ("/data/data/com.flauschcode.broccoli/databases/broccoli",),
    "simple calendar pro": ("/data/data/com.simplemobiletools.calendar.pro/databases/events.db",),
    "pro expense": ("/data/data/com.arduia.expense/databases/accounting.db",),
}
_SOFT_REQUIRED_DEVICE_PATH_APPS = frozenset({"broccoli app", "simple calendar pro"})


@dataclass(frozen=True)
class AndroidWorldSmokeConfig:
    job: dict[str, Any]
    source_entry: dict[str, Any]
    output_dir: Path
    install_dir: Path
    task_name: str
    model: str
    temperature: float
    max_tokens: int
    timeout_seconds: int
    retry: int
    openrouter_api_key_env: str
    console_port: int
    grpc_port: int
    adb_path: str | None = None


@dataclass(frozen=True)
class AndroidWorldModules:
    registry: Any
    suite_utils: Any
    checkpointer_lib: Any
    env_launcher: Any
    t3a: Any
    adb_utils: Any
    setup_device_setup: Any
    app_snapshot: Any


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-json", required=True)
    parser.add_argument("--source-entry-json", default="{}")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--install-dir", required=True)
    parser.add_argument("--task-name", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--retry", type=int, default=0)
    parser.add_argument("--openrouter-api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument("--console-port", type=int, default=5554)
    parser.add_argument("--grpc-port", type=int, default=8554)
    parser.add_argument("--adb-path")
    args = parser.parse_args(argv)
    config = AndroidWorldSmokeConfig(
        job=_loads_json_object(args.job_json, field_name="job-json"),
        source_entry=_loads_json_object(args.source_entry_json, field_name="source-entry-json"),
        output_dir=Path(args.output_dir),
        install_dir=Path(args.install_dir),
        task_name=args.task_name,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout_seconds=args.timeout_seconds,
        retry=args.retry,
        openrouter_api_key_env=args.openrouter_api_key_env,
        console_port=args.console_port,
        grpc_port=args.grpc_port,
        adb_path=args.adb_path,
    )
    try:
        summary = run_smoke_job(config)
    except Exception as exc:  # pragma: no cover - exercised via live smoke runs.
        payload = {
            "status": "error",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback": traceback.format_exc(),
        }
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 1
    print(json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True))
    return 0 if summary.get("status") != "error" else 1


def run_smoke_job(config: AndroidWorldSmokeConfig) -> dict[str, Any]:
    if config.output_dir.exists():
        shutil.rmtree(config.output_dir)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    (config.output_dir / "device_state").mkdir(parents=True, exist_ok=True)
    (config.output_dir / "system_state").mkdir(parents=True, exist_ok=True)
    (config.output_dir / "evaluator_artifacts").mkdir(parents=True, exist_ok=True)
    (config.output_dir / "trajectories").mkdir(parents=True, exist_ok=True)
    (config.output_dir / "observations").mkdir(parents=True, exist_ok=True)
    (config.output_dir / "actions").mkdir(parents=True, exist_ok=True)
    (config.output_dir / "messages").mkdir(parents=True, exist_ok=True)
    (config.output_dir / "post_run_artifacts").mkdir(parents=True, exist_ok=True)
    (config.output_dir / "openrouter_calls").mkdir(parents=True, exist_ok=True)

    _write_json(config.output_dir / "job.json", config.job)
    _write_json(config.output_dir / "source_bundle_entry.json", config.source_entry)
    _write_json(config.output_dir / "worker_config.json", _jsonable(asdict(config)))

    summary: dict[str, Any] = {
        "status": "running",
        "job_id": str(config.job.get("job_id") or ""),
        "task_name": config.task_name,
        "model": config.model,
        "console_port": config.console_port,
        "grpc_port": config.grpc_port,
    }
    _write_json(config.output_dir / "run_summary.json", summary)

    try:
        _safe_capture_state(lambda: _capture_system_state(config, stage="pre_run"))
        _safe_capture_state(lambda: _capture_device_state(config, stage="pre_run"))
        _assert_emulator_ready(config)
        run_result = _run_androidworld_task(config)
    except Exception as exc:
        summary.update(
            {
                "status": "error",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": traceback.format_exc(),
            }
        )
        _write_json(config.output_dir / "run_summary.json", summary)
        _safe_capture_state(lambda: _capture_device_state(config, stage="error"))
        _safe_capture_state(lambda: _capture_system_state(config, stage="error"))
        raise

    _safe_capture_state(lambda: _capture_device_state(config, stage="post_run"))
    _safe_capture_state(lambda: _capture_system_state(config, stage="post_run"))

    episode = dict(run_result["episode"])
    exception_info = episode.get(run_result["constants"].EpisodeConstants.EXCEPTION_INFO)
    native_score = (
        episode.get(run_result["constants"].EpisodeConstants.IS_SUCCESSFUL)
        if exception_info is None
        else None
    )
    success = bool(native_score) if native_score is not None else None

    _write_json(config.output_dir / "task_context.json", _task_context_payload(config, run_result))
    _write_json(config.output_dir / "native_evaluator_input.json", _native_evaluator_input_payload(config, run_result))
    _write_json(config.output_dir / "native_evaluator_output.json", _native_evaluator_output_payload(config, run_result))
    _write_json(config.output_dir / "evaluator_artifacts" / "episodes_full.json", _episodes_payload(run_result))
    _write_json(config.output_dir / "post_run_artifacts" / "episode_metadata.json", _episode_metadata_payload(run_result))
    _write_json(config.output_dir / "post_run_artifacts" / "aux_data.json", _jsonable(episode.get(run_result["constants"].EpisodeConstants.AUX_DATA)))

    checkpoint_dir = Path(run_result["checkpoint_dir"])
    if checkpoint_dir.exists():
        shutil.copytree(checkpoint_dir, config.output_dir / "evaluator_artifacts" / "checkpoint_dir", dirs_exist_ok=True)

    _write_step_artifacts(config, run_result)
    _write_json(config.output_dir / "artifact_manifest.json", _worker_artifact_manifest(config.output_dir))

    summary.update(
        {
            "status": "completed" if exception_info is None else "error",
            "task_name": run_result["task_name"],
            "goal": run_result["goal"],
            "success": success,
            "native_score": _jsonable(native_score),
            "instance_id": episode.get(run_result["constants"].EpisodeConstants.INSTANCE_ID),
            "episode_length": episode.get(run_result["constants"].EpisodeConstants.EPISODE_LENGTH),
            "checkpoint_dir": str(config.output_dir / "evaluator_artifacts" / "checkpoint_dir"),
            "exception_info": _jsonable(exception_info),
            "artifact_manifest_path": str(config.output_dir / "artifact_manifest.json"),
        }
    )
    _write_json(config.output_dir / "run_summary.json", summary)
    return summary


class OpenRouterTextWrapper:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        temperature: float,
        max_tokens: int,
        timeout_seconds: int,
        retry: int,
        calls_dir: Path,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.retry = max(0, retry)
        self.calls_dir = calls_dir
        self._call_index = 0

    def predict(self, text_prompt: str) -> tuple[str, bool | None, Any]:
        request_payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": text_prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        return self._request(request_payload)

    def predict_mm(self, text_prompt: str, _images: list[np.ndarray]) -> tuple[str, bool | None, Any]:
        return self.predict(text_prompt)

    def _request(self, request_payload: dict[str, Any]) -> tuple[str, bool | None, Any]:
        last_error: Exception | None = None
        error_message = None
        for attempt in range(self.retry + 1):
            call_id = f"call-{self._call_index + 1:04d}"
            request_timestamp = _utc_now_iso()
            try:
                response_payload = request_openrouter_completion(
                    api_key=self.api_key,
                    model=self.model,
                    messages=list(request_payload["messages"]),
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    timeout_seconds=self.timeout_seconds,
                    retry=0,
                )
            except Exception as exc:  # pragma: no cover - exercised in live runs.
                last_error = exc
                error_message = str(exc)
                self._call_index += 1
                self._write_call(
                    call_id=call_id,
                    request_timestamp=request_timestamp,
                    request_payload=request_payload,
                    response_payload=None,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
                if attempt >= self.retry:
                    break
                time.sleep(min(2**attempt, 8))
                continue
            response_timestamp = _utc_now_iso()
            self._call_index += 1
            self._write_call(
                call_id=call_id,
                request_timestamp=request_timestamp,
                request_payload=request_payload,
                response_payload=response_payload,
                response_timestamp=response_timestamp,
            )
            return extract_response_content(response_payload), None, response_payload
        if last_error is not None:
            print(error_message or str(last_error))
        return "Error calling LLM", None, None

    def _write_call(
        self,
        *,
        call_id: str,
        request_timestamp: str,
        request_payload: Mapping[str, Any],
        response_payload: Mapping[str, Any] | None,
        response_timestamp: str | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> None:
        payload = {
            "call_id": call_id,
            "request_timestamp": request_timestamp,
            "response_timestamp": response_timestamp,
            "request_payload": _jsonable(request_payload),
            "response_payload": _jsonable(response_payload),
            "error_type": error_type,
            "error_message": error_message,
        }
        _write_json(self.calls_dir / f"{call_id}.json", payload)


def _run_androidworld_task(config: AndroidWorldSmokeConfig) -> dict[str, Any]:
    modules = _load_androidworld_modules(config.install_dir)
    adb_path = _resolve_adb_path(config.adb_path)
    api_key = os.environ.get(config.openrouter_api_key_env)
    if not api_key:
        raise RuntimeError(f"missing environment variable {config.openrouter_api_key_env}")

    env = modules.env_launcher.load_and_setup_env(
        console_port=config.console_port,
        emulator_setup=False,
        adb_path=adb_path,
    )
    try:
        task_registry = modules.registry.TaskRegistry()
        suite_family = task_registry.ANDROID_WORLD_FAMILY
        registry_block = task_registry.get_registry(family=suite_family)
        if config.task_name not in registry_block:
            raise ValueError(f"task {config.task_name} not found in AndroidWorld registry")
        suite = modules.suite_utils.create_suite(
            registry_block,
            n_task_combinations=1,
            seed=int(config.job.get("seed", 0)),
            tasks=[config.task_name],
            use_identical_params=True,
            env=env,
        )
        suite.suite_family = suite_family
        task_instance = list(suite[config.task_name])[0]
        _prepare_task_environment(config, modules, env, task_instance)
        llm = OpenRouterTextWrapper(
            api_key=api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout_seconds=config.timeout_seconds,
            retry=config.retry,
            calls_dir=config.output_dir / "openrouter_calls",
        )
        agent = modules.t3a.T3A(env, llm, name="t3a_openrouter")
        checkpoint_dir = config.output_dir / "checkpoint_dir"
        checkpointer = modules.checkpointer_lib.IncrementalCheckpointer(str(checkpoint_dir))
        episodes = modules.suite_utils.run(
            suite,
            agent,
            checkpointer=checkpointer,
            return_full_episode_data=True,
        )
    finally:
        env.close()

    if not episodes:
        raise RuntimeError("AndroidWorld suite run returned no episodes")

    episode = dict(episodes[0])
    return {
        "modules": modules,
        "constants": __import__("android_world.constants", fromlist=["constants"]),
        "suite_family": suite_family,
        "task_name": task_instance.name,
        "goal": str(task_instance.goal),
        "params": _jsonable(task_instance.params),
        "episodes": episodes,
        "episode": episode,
        "agent_name": agent.name,
        "checkpoint_dir": checkpoint_dir,
        "adb_path": adb_path,
    }


def _load_androidworld_modules(install_dir: Path) -> AndroidWorldModules:
    install_dir = install_dir.resolve()
    if str(install_dir) not in sys.path:
        sys.path.insert(0, str(install_dir))
    from android_world import checkpointer as checkpointer_lib
    from android_world import registry
    from android_world import suite_utils
    from android_world.agents import t3a
    from android_world.env import adb_utils
    from android_world.env import env_launcher
    from android_world.env.setup_device import setup as setup_device_setup
    from android_world.utils import app_snapshot

    return AndroidWorldModules(
        registry=registry,
        suite_utils=suite_utils,
        checkpointer_lib=checkpointer_lib,
        env_launcher=env_launcher,
        t3a=t3a,
        adb_utils=adb_utils,
        setup_device_setup=setup_device_setup,
        app_snapshot=app_snapshot,
    )


def _prepare_task_environment(
    config: AndroidWorldSmokeConfig,
    modules: AndroidWorldModules,
    env: Any,
    task_instance: Any,
) -> None:
    app_names = tuple(str(app) for app in (getattr(task_instance, "app_names", ()) or ()) if app)
    if not app_names:
        return
    modules.adb_utils.set_root_if_needed(env.controller)
    if "markor" in app_names:
        _ensure_device_directory(modules, env, "/storage/emulated/0/Documents/Markor")
    for app_name in app_names:
        if app_name not in _PREFLIGHT_APP_NAMES:
            continue
        if app_name not in _REQUIRED_DEVICE_PATHS:
            continue
        _verify_required_device_paths(config, modules, env, app_name)
    if "clipper" in app_names:
        _verify_clipper_access(modules, env)


def _verify_required_device_paths(
    config: AndroidWorldSmokeConfig,
    modules: AndroidWorldModules,
    env: Any,
    app_name: str,
) -> None:
    for device_path in _REQUIRED_DEVICE_PATHS.get(app_name, ()):
        if _device_path_exists(config, modules, env, device_path):
            continue
        _materialize_required_device_path(config, modules, env, app_name, device_path)
        if _device_path_exists(config, modules, env, device_path):
            continue
        if app_name in _SOFT_REQUIRED_DEVICE_PATH_APPS:
            print(
                f"AndroidWorld preflight warning: {app_name} path still missing after warm-up: {device_path}",
                file=sys.stderr,
                flush=True,
            )
            continue
        raise RuntimeError(f"AndroidWorld task preflight could not materialize {device_path}")


def _materialize_required_device_path(
    config: AndroidWorldSmokeConfig,
    modules: AndroidWorldModules,
    env: Any,
    app_name: str,
    device_path: str,
) -> None:
    if _device_path_exists(config, modules, env, device_path):
        return

    try:
        modules.app_snapshot.restore_snapshot(app_name, env.controller)
    except Exception:
        pass
    if _warm_materialize_device_path(config, modules, env, app_name, device_path):
        return

    app_setup = modules.setup_device_setup.get_app_mapping(app_name)
    if app_setup is not None:
        try:
            modules.setup_device_setup.setup_app(app_setup, env)
        except Exception:
            pass
    _warm_materialize_device_path(config, modules, env, app_name, device_path)


def _warm_materialize_device_path(
    config: AndroidWorldSmokeConfig,
    modules: AndroidWorldModules,
    env: Any,
    app_name: str,
    device_path: str,
) -> bool:
    if _device_path_exists(config, modules, env, device_path):
        return True
    for wait_seconds in (2.0, 4.0, 6.0):
        try:
            modules.adb_utils.launch_app(app_name, env.controller)
        except Exception:
            continue
        time.sleep(wait_seconds)
        if _device_path_exists(config, modules, env, device_path):
            return True
        try:
            modules.adb_utils.close_app(app_name, env.controller)
        except Exception:
            pass
        time.sleep(0.5)
    return _device_path_exists(config, modules, env, device_path)


def _verify_clipper_access(modules: AndroidWorldModules, env: Any) -> None:
    probe_value = "androidworld-preflight"
    modules.adb_utils.launch_app("clipper", env.controller)
    time.sleep(1.0)
    modules.adb_utils.set_clipboard_contents(probe_value, env.controller)
    observed = modules.adb_utils.get_clipboard_contents(env.controller)
    if probe_value not in str(observed):
        raise RuntimeError("AndroidWorld task preflight could not verify Clipper clipboard access")


def _device_path_exists(
    config: AndroidWorldSmokeConfig,
    modules: AndroidWorldModules,
    env: Any,
    device_path: str,
) -> bool:
    adb_path = _resolve_adb_path(config.adb_path)
    device_serial = f"emulator-{config.console_port}"
    completed = subprocess.run(
        [adb_path, "-s", device_serial, "shell", "ls", device_path],
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode == 0:
        return True

    # AndroidEnv's gRPC-backed shell semantics can misreport `test -e` for
    # real files on this emulator, so fall back to a direct controller `ls`
    # probe only when the host-side adb check was inconclusive.
    try:
        modules.adb_utils.issue_generic_request(["shell", "ls", device_path], env.controller)
        return True
    except Exception:
        return False


def _ensure_device_directory(modules: AndroidWorldModules, env: Any, device_path: str) -> None:
    modules.adb_utils.issue_generic_request(
        ["shell", "mkdir", "-p", device_path],
        env.controller,
    )
    modules.adb_utils.issue_generic_request(
        ["shell", "touch", f"{device_path}/androidworld_keep.txt"],
        env.controller,
    )


def _task_context_payload(config: AndroidWorldSmokeConfig, run_result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "androidworld_task_context/v1",
        "task_name": run_result["task_name"],
        "goal": run_result["goal"],
        "params": run_result["params"],
        "suite_family": run_result["suite_family"],
        "seed": int(config.job.get("seed", 0)),
        "agent_name": run_result["agent_name"],
        "model": config.model,
    }


def _native_evaluator_input_payload(config: AndroidWorldSmokeConfig, run_result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "androidworld_native_evaluator_input/v1",
        "task_name": run_result["task_name"],
        "suite_family": run_result["suite_family"],
        "seed": int(config.job.get("seed", 0)),
        "agent_name": run_result["agent_name"],
        "model": config.model,
        "console_port": config.console_port,
        "grpc_port": config.grpc_port,
        "source_entry": _jsonable(config.source_entry),
        "task_params": run_result["params"],
    }


def _native_evaluator_output_payload(config: AndroidWorldSmokeConfig, run_result: Mapping[str, Any]) -> dict[str, Any]:
    constants = run_result["constants"]
    episode = run_result["episode"]
    return {
        "schema_version": "androidworld_native_evaluator_output/v1",
        "task_name": run_result["task_name"],
        "goal": run_result["goal"],
        "success": episode.get(constants.EpisodeConstants.IS_SUCCESSFUL),
        "episode_length": episode.get(constants.EpisodeConstants.EPISODE_LENGTH),
        "run_time_seconds": episode.get(constants.EpisodeConstants.RUN_TIME),
        "instance_id": episode.get(constants.EpisodeConstants.INSTANCE_ID),
        "finish_dtime": _jsonable(episode.get(constants.EpisodeConstants.FINISH_DTIME)),
        "aux_data": _jsonable(episode.get(constants.EpisodeConstants.AUX_DATA)),
        "exception_info": _jsonable(episode.get(constants.EpisodeConstants.EXCEPTION_INFO)),
        "checkpoint_dir": str(config.output_dir / "evaluator_artifacts" / "checkpoint_dir"),
    }


def _episodes_payload(run_result: Mapping[str, Any]) -> dict[str, Any]:
    constants = run_result["constants"]
    episode = dict(run_result["episode"])
    step_records = _episode_steps(episode, constants)
    return {
        "schema_version": "androidworld_episode_bundle/v1",
        "task_name": run_result["task_name"],
        "goal": run_result["goal"],
        "episodes": [
            {
                "goal": _jsonable(episode.get(constants.EpisodeConstants.GOAL)),
                "task_template": _jsonable(episode.get(constants.EpisodeConstants.TASK_TEMPLATE)),
                "instance_id": _jsonable(episode.get(constants.EpisodeConstants.INSTANCE_ID)),
                "is_successful": _jsonable(episode.get(constants.EpisodeConstants.IS_SUCCESSFUL)),
                "episode_length": _jsonable(episode.get(constants.EpisodeConstants.EPISODE_LENGTH)),
                "run_time": _jsonable(episode.get(constants.EpisodeConstants.RUN_TIME)),
                "finish_dtime": _jsonable(episode.get(constants.EpisodeConstants.FINISH_DTIME)),
                "aux_data": _jsonable(episode.get(constants.EpisodeConstants.AUX_DATA)),
                "exception_info": _jsonable(episode.get(constants.EpisodeConstants.EXCEPTION_INFO)),
                "step_count": len(step_records),
            }
        ],
    }


def _episode_metadata_payload(run_result: Mapping[str, Any]) -> dict[str, Any]:
    constants = run_result["constants"]
    episode = dict(run_result["episode"])
    return {
        "schema_version": "androidworld_episode_metadata/v1",
        "goal": _jsonable(episode.get(constants.EpisodeConstants.GOAL)),
        "task_template": _jsonable(episode.get(constants.EpisodeConstants.TASK_TEMPLATE)),
        "instance_id": _jsonable(episode.get(constants.EpisodeConstants.INSTANCE_ID)),
        "is_successful": _jsonable(episode.get(constants.EpisodeConstants.IS_SUCCESSFUL)),
        "episode_length": _jsonable(episode.get(constants.EpisodeConstants.EPISODE_LENGTH)),
        "run_time": _jsonable(episode.get(constants.EpisodeConstants.RUN_TIME)),
        "finish_dtime": _jsonable(episode.get(constants.EpisodeConstants.FINISH_DTIME)),
        "screen_config": _jsonable(episode.get(constants.EpisodeConstants.SCREEN_CONFIG)),
        "seed": _jsonable(episode.get(constants.EpisodeConstants.SEED)),
        "aux_data": _jsonable(episode.get(constants.EpisodeConstants.AUX_DATA)),
        "exception_info": _jsonable(episode.get(constants.EpisodeConstants.EXCEPTION_INFO)),
    }


def _write_step_artifacts(config: AndroidWorldSmokeConfig, run_result: Mapping[str, Any]) -> None:
    constants = run_result["constants"]
    episode = dict(run_result["episode"])
    steps = _episode_steps(episode, constants)
    trajectory_records: list[dict[str, Any]] = []
    action_records: list[dict[str, Any]] = []
    message_records: list[dict[str, Any]] = []

    for index, step in enumerate(steps, start=1):
        before_path = _write_observation_image(
            config.output_dir / "observations",
            index=index,
            suffix="before",
            image_value=step.get("before_screenshot"),
        )
        after_path = _write_observation_image(
            config.output_dir / "observations",
            index=index,
            suffix="after",
            image_value=step.get("after_screenshot"),
        )
        observation_payload = {
            "step_number": index,
            "before_screenshot_path": str(before_path) if before_path else None,
            "after_screenshot_path": str(after_path) if after_path else None,
            "before_element_list": _jsonable(step.get("before_element_list")),
            "after_element_list": _jsonable(step.get("after_element_list")),
        }
        _write_json(config.output_dir / "observations" / f"step_{index:03d}.json", observation_payload)

        action_record = {
            "step_number": index,
            "action_prompt": _jsonable(step.get("action_prompt")),
            "action_output": _jsonable(step.get("action_output")),
            "action_raw_response": _jsonable(step.get("action_raw_response")),
            "summary": _jsonable(step.get("summary")),
        }
        action_records.append(action_record)
        message_records.append(
            {
                "step_number": index,
                "action_prompt": _jsonable(step.get("action_prompt")),
                "summary_prompt": _jsonable(step.get("summary_prompt")),
                "action_output": _jsonable(step.get("action_output")),
                "summary": _jsonable(step.get("summary")),
            }
        )
        trajectory_records.append(
            {
                "step_number": index,
                "action_prompt": _jsonable(step.get("action_prompt")),
                "action_output": _jsonable(step.get("action_output")),
                "summary_prompt": _jsonable(step.get("summary_prompt")),
                "summary": _jsonable(step.get("summary")),
                "before_screenshot_path": str(before_path) if before_path else None,
                "after_screenshot_path": str(after_path) if after_path else None,
                "before_element_list": _jsonable(step.get("before_element_list")),
                "after_element_list": _jsonable(step.get("after_element_list")),
            }
        )

    _write_json(config.output_dir / "trajectories" / "steps.json", trajectory_records)
    _write_json(config.output_dir / "actions" / "actions.json", action_records)
    _write_json(config.output_dir / "messages" / "messages.json", message_records)


def _episode_steps(episode: Mapping[str, Any], constants: Any) -> list[dict[str, Any]]:
    step_data = episode.get(constants.EpisodeConstants.EPISODE_DATA) or {}
    if not isinstance(step_data, Mapping):
        return []
    lengths = [len(value) for value in step_data.values() if isinstance(value, list)]
    step_count = max(lengths, default=0)
    records: list[dict[str, Any]] = []
    for index in range(step_count):
        record: dict[str, Any] = {}
        for key, values in step_data.items():
            if isinstance(values, list):
                record[str(key)] = values[index] if index < len(values) else None
            else:
                record[str(key)] = values
        records.append(record)
    return records


def _write_observation_image(directory: Path, *, index: int, suffix: str, image_value: Any) -> Path | None:
    if image_value is None:
        return None
    if not isinstance(image_value, np.ndarray):
        return None
    array = image_value
    if array.dtype != np.uint8:
        array = np.clip(array, 0, 255).astype(np.uint8)
    path = directory / f"step_{index:03d}_{suffix}.png"
    Image.fromarray(array).save(path)
    return path


def _worker_artifact_manifest(output_dir: Path) -> dict[str, Any]:
    files = []
    for path in sorted(candidate for candidate in output_dir.rglob("*") if candidate.is_file()):
        files.append(
            {
                "path": str(path.relative_to(output_dir)),
                "size_bytes": path.stat().st_size,
            }
        )
    return {
        "schema_version": "androidworld_worker_artifact_manifest/v1",
        "root": str(output_dir),
        "files": files,
    }


def _capture_system_state(config: AndroidWorldSmokeConfig, *, stage: str) -> None:
    system_dir = config.output_dir / "system_state"
    payload = {
        "stage": stage,
        "python_executable": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "install_dir": str(config.install_dir),
        "task_name": config.task_name,
        "model": config.model,
    }
    _write_json(system_dir / f"{stage}.json", payload)
    install_manifest = config.install_dir / "install_manifest.json"
    if install_manifest.exists():
        shutil.copyfile(install_manifest, system_dir / f"{stage}_install_manifest.json")


def _capture_device_state(config: AndroidWorldSmokeConfig, *, stage: str) -> None:
    device_dir = config.output_dir / "device_state"
    adb_path = _resolve_adb_path(config.adb_path)
    device_serial = f"emulator-{config.console_port}"
    commands = {
        "adb_devices.txt": [adb_path, "devices", "-l"],
        "getprop.txt": [adb_path, "-s", device_serial, "shell", "getprop"],
        "window.txt": [adb_path, "-s", device_serial, "shell", "dumpsys", "window", "windows"],
        "activity.txt": [adb_path, "-s", device_serial, "shell", "dumpsys", "activity", "top"],
    }
    for filename, command in commands.items():
        completed = subprocess.run(command, check=False, text=True, capture_output=True)
        content = {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
        _write_json(device_dir / f"{stage}_{filename}.json", content)
    grpc_probe = subprocess.run(
        ["bash", "-lc", f"lsof -n -iTCP:{config.grpc_port} -sTCP:LISTEN || true"],
        check=False,
        text=True,
        capture_output=True,
    )
    _write_json(
        device_dir / f"{stage}_grpc_probe.json",
        {
            "command": f"lsof -n -iTCP:{config.grpc_port} -sTCP:LISTEN",
            "returncode": grpc_probe.returncode,
            "stdout": grpc_probe.stdout,
            "stderr": grpc_probe.stderr,
        },
    )


def _resolve_adb_path(explicit_path: str | None) -> str:
    candidates = []
    if explicit_path:
        candidates.append(explicit_path)
    candidates.extend(
        [
            os.path.expanduser("~/Library/Android/sdk/platform-tools/adb"),
            os.path.expanduser("~/Android/Sdk/platform-tools/adb"),
            shutil.which("adb"),
        ]
    )
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    raise RuntimeError("adb not found in common Android SDK paths and not present on PATH")


def _assert_emulator_ready(config: AndroidWorldSmokeConfig) -> None:
    adb_path = _resolve_adb_path(config.adb_path)
    device_serial = f"emulator-{config.console_port}"
    devices = subprocess.run(
        [adb_path, "devices"],
        check=False,
        text=True,
        capture_output=True,
    )
    grpc_probe = subprocess.run(
        ["bash", "-lc", f"lsof -n -iTCP:{config.grpc_port} -sTCP:LISTEN || true"],
        check=False,
        text=True,
        capture_output=True,
    )
    device_ready = device_serial in (devices.stdout or "")
    grpc_ready = bool((grpc_probe.stdout or "").strip())
    if device_ready and grpc_ready:
        return
    reasons = []
    if not device_ready:
        reasons.append(f"{device_serial} missing from `adb devices`")
    if not grpc_ready:
        reasons.append(f"no listener on gRPC port {config.grpc_port}")
    reason_text = "; ".join(reasons)
    raise RuntimeError(
        "AndroidWorld local smoke prerequisites not satisfied: "
        f"{reason_text}. Start the AVD with `-grpc {config.grpc_port}` before running the benchmark."
    )


def _safe_capture_state(callback) -> None:
    try:
        callback()
    except Exception:
        pass


def request_openrouter_completion(
    *,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float,
    max_tokens: int,
    timeout_seconds: int,
    retry: int,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    attempt = 0
    while True:
        request = urllib.request.Request(
            OPENROUTER_CHAT_COMPLETIONS_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if attempt >= retry:
                raise RuntimeError(f"OpenRouter HTTP {exc.code}: {body}") from exc
        except Exception:
            if attempt >= retry:
                raise
        attempt += 1
        time.sleep(min(2**attempt, 8))


def extract_response_content(response_payload: Mapping[str, Any]) -> str:
    choices = list(response_payload.get("choices") or [])
    if not choices:
        raise ValueError("OpenRouter response did not contain any choices")
    first = choices[0]
    if not isinstance(first, Mapping):
        raise ValueError("OpenRouter choice payload must be a mapping")
    message = first.get("message")
    if not isinstance(message, Mapping):
        raise ValueError("OpenRouter choice did not contain a message payload")
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, Mapping):
        text = _coerce_openrouter_text(content)
        if text:
            return text
    if isinstance(content, list):
        text = "".join(_coerce_openrouter_text(item) for item in content)
        if text:
            return text
    for key in ("reasoning", "reasoning_content", "output_text", "text"):
        text = _coerce_openrouter_text(message.get(key))
        if text:
            return text
    raise ValueError("OpenRouter message content is not text")


def _coerce_openrouter_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        for key in ("text", "content", "value", "output_text"):
            text = _coerce_openrouter_text(value.get(key))
            if text:
                return text
        return "".join(_coerce_openrouter_text(child) for child in value.values())
    if isinstance(value, list):
        return "".join(_coerce_openrouter_text(item) for item in value)
    return ""


def _loads_json_object(raw: str, *, field_name: str) -> dict[str, Any]:
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise TypeError(f"{field_name} must decode to a JSON object")
    return payload


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return {"base64": base64.b64encode(value).decode("ascii")}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return {"shape": list(value.shape), "dtype": str(value.dtype)}
    if dataclasses.is_dataclass(value):
        return {str(key): _jsonable(child) for key, child in dataclasses.asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(child) for key, child in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(child) for child in value]
    if hasattr(value, "__dict__"):
        return {
            str(key): _jsonable(child)
            for key, child in vars(value).items()
            if not str(key).startswith("_")
        }
    return repr(value)


def _utc_now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover - exercised by smoke execution.
    raise SystemExit(main())
