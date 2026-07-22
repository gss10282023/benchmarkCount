"""Thin MiniWoB++ smoke worker using BrowserGym envs and OpenRouter actions."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import shutil
import traceback
from typing import Any, Mapping

from evidence_system.adapters.workarena_worker import (
    DRIVER_OPENROUTER_CHAT,
    build_step_prompt,
    extract_action_text,
    extract_response_content,
    request_openrouter_completion,
    _close_env_with_timeout,
    _jsonable,
    _loads_json_object,
    _sanitize_sensitive_data,
    _utc_now_iso,
    _write_json,
    _write_openrouter_call,
)


SYSTEM_PROMPT = """Return exactly one BrowserGym MiniWoB++ action and nothing else.

Rules:
- Output a single action string such as click('12') or fill('7', 'value').
- Do not wrap the action in Markdown.
- Use only valid BrowserGym high-level actions from the provided action list.
- If the task is already solved, you may use noop().
"""


# Chromium may need more than 20 seconds to flush both BrowserGym video
# recorders after a long (30-step) episode.  This timeout affects teardown and
# artifact finalization only; it does not change the task, action budget, or
# released evaluator invocation.
ENV_CLOSE_TIMEOUT_SECONDS = 180


@dataclass(frozen=True)
class MiniWoBSmokeConfig:
    job: dict[str, Any]
    source_entry: dict[str, Any]
    output_dir: Path
    task_id: str
    model: str | None
    temperature: float
    max_tokens: int
    timeout_seconds: int
    retry: int
    openrouter_provider_only: str | None
    openrouter_api_key_env: str
    max_steps: int
    driver: str
    base_url: str
    headless: bool = True
    record_video: bool = True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-json", required=True)
    parser.add_argument("--source-entry-json", default="{}")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--model")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--retry", type=int, default=0)
    parser.add_argument("--openrouter-provider-only")
    parser.add_argument("--openrouter-api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument("--max-steps", type=int, default=6)
    parser.add_argument("--driver", default=DRIVER_OPENROUTER_CHAT)
    parser.add_argument("--base-url", required=True)
    args = parser.parse_args(argv)
    config = MiniWoBSmokeConfig(
        job=_loads_json_object(args.job_json, field_name="job-json"),
        source_entry=_loads_json_object(args.source_entry_json, field_name="source-entry-json"),
        output_dir=Path(args.output_dir),
        task_id=args.task_id,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout_seconds=args.timeout_seconds,
        retry=args.retry,
        openrouter_provider_only=args.openrouter_provider_only,
        openrouter_api_key_env=args.openrouter_api_key_env,
        max_steps=args.max_steps,
        driver=args.driver,
        base_url=args.base_url,
    )
    try:
        summary = run_smoke_job(config)
    except Exception as exc:  # pragma: no cover - exercised in live smoke runs.
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


def run_smoke_job(config: MiniWoBSmokeConfig) -> dict[str, Any]:
    if config.output_dir.exists():
        shutil.rmtree(config.output_dir)
    _artifact_dirs(config.output_dir)

    _write_json(config.output_dir / "job.json", config.job)
    _write_json(config.output_dir / "source_bundle_entry.json", config.source_entry)
    _write_json(config.output_dir / "worker_config.json", _jsonable(asdict(config)))

    summary: dict[str, Any] = {
        "status": "running",
        "job_id": str(config.job.get("job_id") or ""),
        "task_id": config.task_id,
        "driver": config.driver,
        "model": config.model,
        "base_url": config.base_url,
    }
    _write_json(config.output_dir / "run_summary.json", summary)

    env = None
    task_context: dict[str, Any] | None = None
    task_state_initial: dict[str, Any] | None = None
    task_state_final: dict[str, Any] | None = None
    final_validation: dict[str, Any] | None = None
    steps: list[dict[str, Any]] = []
    last_task_info: dict[str, Any] = {}
    truncated = False
    error: Exception | None = None

    try:
        task_kwargs = _task_kwargs_from_source(config.source_entry, base_url=config.base_url)
        action_set = _build_action_set()
        action_space_description = action_set.describe(with_long_description=False, with_examples=True)

        env = _make_miniwob_env(config=config, task_kwargs=task_kwargs, action_set=action_set)
        obs, reset_info = env.reset(seed=int(config.job.get("seed", 0)))
        raw = env.unwrapped
        chat_messages = _chat_messages(raw)

        task_state_initial = _task_state_payload(raw.task)
        initial_validation = _validation_payload(raw.task.validate(raw.page, chat_messages))
        last_task_info = dict(reset_info.get("task_info") or {})
        task_context = _task_context_payload(
            config=config,
            raw_env=raw,
            reset_info=reset_info,
            initial_observation=obs,
            task_kwargs=task_kwargs,
            action_space_description=action_space_description,
        )

        _write_json(config.output_dir / "task_context.json", task_context)
        _write_json(config.output_dir / "task_artifacts" / "reset_info.json", reset_info)
        _write_json(config.output_dir / "task_artifacts" / "task_state_initial.json", task_state_initial)
        _write_json(config.output_dir / "task_artifacts" / "validation_initial.json", initial_validation)
        _write_json(
            config.output_dir / "task_artifacts" / "policy_workflow.json",
            {
                "goal": task_context.get("goal"),
                "base_url": task_context.get("base_url"),
                "source_ref": task_context.get("source_ref"),
                "runtime_goal_note": task_context.get("runtime_goal_note"),
                "task_kwargs": task_kwargs,
            },
        )
        _capture_browser_state(config.output_dir, raw.page, obs, label="step_000_reset")

        latest_obs = obs
        reward = 0.0
        terminated = False

        api_key = os.environ.get(config.openrouter_api_key_env)
        if not api_key:
            raise RuntimeError(f"missing environment variable {config.openrouter_api_key_env}")
        if not config.model:
            raise RuntimeError("model is required for openrouter_chat driver")
        if config.driver != DRIVER_OPENROUTER_CHAT:
            raise RuntimeError(f"unsupported MiniWoB++ driver: {config.driver}")

        for step_index in range(1, max(1, config.max_steps) + 1):
            step_prompt = build_step_prompt(
                config=config,
                observation=latest_obs,
                step_index=step_index,
                action_space_description=action_space_description,
                previous_steps=steps,
            )
            request_messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": step_prompt},
            ]
            request_payload = {
                "model": config.model,
                "messages": request_messages,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
            }
            provider_routing = None
            if config.openrouter_provider_only:
                provider_routing = {
                    "only": [config.openrouter_provider_only],
                    "allow_fallbacks": False,
                }
                request_payload["provider"] = provider_routing

            response_payload = None
            response_content = None
            request_timestamp = _utc_now_iso()
            response_timestamp = request_timestamp
            request_error: Exception | None = None
            for provider_attempt in range(config.retry + 1):
                request_timestamp = _utc_now_iso()
                try:
                    response_payload = request_openrouter_completion(
                        api_key=api_key,
                        model=config.model,
                        messages=request_messages,
                        temperature=config.temperature,
                        max_tokens=config.max_tokens,
                        timeout_seconds=config.timeout_seconds,
                        retry=0,
                        provider_routing=provider_routing,
                    )
                    response_timestamp = _utc_now_iso()
                    response_content = extract_response_content(response_payload)
                    if not response_content.strip():
                        raise RuntimeError("OpenRouter response content is empty")
                except Exception as exc:
                    request_error = exc
                    response_timestamp = _utc_now_iso()
                    _write_openrouter_call(
                        path=(
                            config.output_dir
                            / "openrouter_calls"
                            / "retry_attempts"
                            / f"call-{step_index:04d}-attempt-{provider_attempt + 1:04d}.json"
                        ),
                        call_id=f"call-{step_index:04d}-attempt-{provider_attempt + 1:04d}",
                        request_timestamp=request_timestamp,
                        response_timestamp=response_timestamp,
                        request_payload=request_payload,
                        response_payload=response_payload,
                        action_text="",
                        python_code=None,
                        error_type=type(exc).__name__,
                        error_message=str(exc),
                    )
                    if provider_attempt < config.retry:
                        continue
                else:
                    request_error = None
                break

            if request_error is not None:
                _write_openrouter_call(
                    path=config.output_dir / "openrouter_calls" / f"call-{step_index:04d}.json",
                    call_id=f"call-{step_index:04d}",
                    request_timestamp=request_timestamp,
                    response_timestamp=response_timestamp,
                    request_payload=request_payload,
                    response_payload=response_payload,
                    action_text="",
                    python_code=None,
                    error_type=type(request_error).__name__,
                    error_message=str(request_error),
                )
                raise request_error
            if response_payload is None or response_content is None:
                raise RuntimeError("OpenRouter retry loop ended without a response")
            action_text = extract_action_text(response_content)
            python_code = None
            parse_error = None
            try:
                python_code = action_set.to_python_code(action_text)
            except Exception as exc:
                parse_error = f"{type(exc).__name__}: {exc}"

            _write_openrouter_call(
                path=config.output_dir / "openrouter_calls" / f"call-{step_index:04d}.json",
                call_id=f"call-{step_index:04d}",
                request_timestamp=request_timestamp,
                response_timestamp=response_timestamp,
                request_payload=request_payload,
                response_payload=response_payload,
                action_text=action_text,
                python_code=python_code,
                error_type="ActionParseError" if parse_error else None,
                error_message=parse_error,
            )

            latest_obs, reward, terminated, truncated, info = env.step(action_text)
            last_task_info = dict(info.get("task_info") or {})
            step_label = f"step_{step_index:03d}"
            _capture_browser_state(config.output_dir, raw.page, latest_obs, label=step_label)
            steps.append(
                {
                    "step_index": step_index,
                    "driver": config.driver,
                    "action": action_text,
                    "python_code": python_code,
                    "parse_error": parse_error,
                    "reward": reward,
                    "terminated": terminated,
                    "truncated": truncated,
                    "task_info": _jsonable(last_task_info),
                    "observation_path": f"trajectory/observations/{step_label}.json",
                    "screenshot_path": f"browser_artifacts/screenshots/{step_label}.png",
                    "html_path": f"browser_artifacts/page_html/{step_label}.html",
                }
            )
            if terminated or truncated:
                break

        final_validation = _validation_payload(raw.task.validate(raw.page, _chat_messages(raw)))
        task_state_final = _task_state_payload(raw.task)
        _write_json(config.output_dir / "task_artifacts" / "task_state_final.json", task_state_final)
        _write_json(config.output_dir / "task_artifacts" / "validation_final.json", final_validation)
        _write_json(config.output_dir / "task_artifacts" / "task_info_final.json", last_task_info)
        _write_json(config.output_dir / "task_artifacts" / "chat_messages_final.json", _chat_messages(raw))
        _write_json(config.output_dir / "trajectory" / "steps.json", steps)

        native_evaluator_input = _native_evaluator_input_payload(
            config=config,
            task_context=task_context,
            task_kwargs=task_kwargs,
            initial_validation=initial_validation,
        )
        _write_json(config.output_dir / "native_evaluator_input.json", native_evaluator_input)
        native_evaluator_output = _native_evaluator_output_payload(
            config=config,
            task_context=task_context,
            final_validation=final_validation,
            steps=steps,
        )
        _write_json(config.output_dir / "native_evaluator_output.json", native_evaluator_output)

        success = bool(final_validation.get("done")) and float(final_validation.get("reward") or 0.0) >= 1.0
        summary.update(
            {
                "status": "completed",
                "env_id": task_context["env_id"],
                "goal": task_context["goal"],
                "success": success,
                "task_class": task_context["task_class"],
                "step_count": len(steps),
                "terminated": bool(final_validation.get("done")),
                "truncated": bool(truncated),
                "final_reward": float(final_validation.get("reward") or 0.0),
                "final_validation_message": final_validation.get("message"),
                "recording_file": reset_info.get("recording_file"),
                "chat_recording_file": ((reset_info.get("chat") or {}).get("recording_file") if isinstance(reset_info.get("chat"), Mapping) else None),
            }
        )
    except Exception as exc:
        error = exc
        summary.update(
            {
                "status": "error",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": traceback.format_exc(),
            }
        )
    finally:
        close_error = None
        if env is not None:
            close_error = _close_env_with_timeout(
                env, timeout_seconds=ENV_CLOSE_TIMEOUT_SECONDS
            )
        summary["environment_close_timeout_seconds"] = ENV_CLOSE_TIMEOUT_SECONDS
        if close_error:
            summary["close_error"] = close_error
        _write_json(config.output_dir / "artifact_manifest.json", _worker_artifact_manifest(config.output_dir))
        summary["artifact_manifest_path"] = str(config.output_dir / "artifact_manifest.json")
        _write_json(config.output_dir / "run_summary.json", summary)

    if error is not None:
        raise error
    return summary


def _artifact_dirs(output_dir: Path) -> None:
    for path in (
        output_dir,
        output_dir / "browser_artifacts" / "recordings",
        output_dir / "browser_artifacts" / "screenshots",
        output_dir / "browser_artifacts" / "page_html",
        output_dir / "trajectory" / "observations",
        output_dir / "task_artifacts",
        output_dir / "openrouter_calls",
        output_dir / "openrouter_calls" / "retry_attempts",
    ):
        path.mkdir(parents=True, exist_ok=True)


def _build_action_set() -> Any:
    from browsergym.core.action.highlevel import HighLevelActionSet

    return HighLevelActionSet(multiaction=False, strict=False)


def _make_miniwob_env(
    *,
    config: MiniWoBSmokeConfig,
    task_kwargs: Mapping[str, Any],
    action_set: Any,
) -> Any:
    import gymnasium as gym
    import browsergym.miniwob  # noqa: F401

    return gym.make(
        _resolved_env_id(config.task_id),
        headless=config.headless,
        record_video_dir=str(config.output_dir / "browser_artifacts" / "recordings") if config.record_video else None,
        task_kwargs=dict(task_kwargs),
        action_mapping=action_set.to_python_code,
    )


def _resolved_env_id(task_id: str) -> str:
    normalized = str(task_id).strip()
    if normalized.startswith("browsergym/"):
        return normalized
    if normalized.startswith("miniwob."):
        return f"browsergym/{normalized}"
    return f"browsergym/miniwob.{normalized}"


def _task_kwargs_from_source(source_entry: Mapping[str, Any], *, base_url: str) -> dict[str, Any]:
    visible_inputs = source_entry.get("visible_inputs")
    if not isinstance(visible_inputs, Mapping):
        return {"base_url": base_url}
    task_kwargs: dict[str, Any] = {}
    task_text = visible_inputs.get("task_text")
    if isinstance(task_text, Mapping):
        nested_kwargs = task_text.get("task_kwargs")
        if isinstance(nested_kwargs, Mapping):
            task_kwargs.update(dict(nested_kwargs))
    top_level_kwargs = visible_inputs.get("task_kwargs")
    if isinstance(top_level_kwargs, Mapping):
        task_kwargs.update(dict(top_level_kwargs))
    task_kwargs.setdefault("base_url", base_url)
    return task_kwargs


def _chat_messages(raw_env: Any) -> list[dict[str, Any]]:
    chat = getattr(raw_env, "chat", None)
    messages = getattr(chat, "messages", None)
    if isinstance(messages, list):
        return list(messages)
    return []


def _capture_browser_state(
    output_dir: Path,
    page: Any,
    observation: Mapping[str, Any],
    *,
    label: str,
) -> None:
    observation_payload = dict(observation)
    observation_payload.pop("screenshot", None)
    observation_payload["page_title"] = _safe_page_title(page)
    _write_json(output_dir / "trajectory" / "observations" / f"{label}.json", observation_payload)
    _write_html(output_dir / "browser_artifacts" / "page_html" / f"{label}.html", _safe_page_content(page))
    try:
        page.screenshot(path=str(output_dir / "browser_artifacts" / "screenshots" / f"{label}.png"))
    except Exception as exc:  # pragma: no cover - defensive.
        _write_json(
            output_dir / "browser_artifacts" / "screenshots" / f"{label}.error.json",
            {"error_type": type(exc).__name__, "error_message": str(exc)},
        )


def _task_context_payload(
    *,
    config: MiniWoBSmokeConfig,
    raw_env: Any,
    reset_info: Mapping[str, Any],
    initial_observation: Mapping[str, Any],
    task_kwargs: Mapping[str, Any],
    action_space_description: str,
) -> dict[str, Any]:
    visible_inputs = config.source_entry.get("visible_inputs")
    visible_inputs_mapping = dict(visible_inputs or {}) if isinstance(visible_inputs, Mapping) else {}
    task_text = visible_inputs_mapping.get("task_text")
    return {
        "schema_version": "miniwob_task_context/v1",
        "env_id": _resolved_env_id(config.task_id),
        "task_id": config.task_id,
        "task_class": raw_env.task.__class__.__name__,
        "task_module": raw_env.task.__class__.__module__,
        "goal": initial_observation.get("goal"),
        "goal_object": initial_observation.get("goal_object"),
        "url": initial_observation.get("url"),
        "task_info_initial": reset_info.get("task_info"),
        "base_url": task_kwargs.get("base_url"),
        "task_kwargs": task_kwargs,
        "source_ref": _source_ref(config.source_entry),
        "runtime_goal_note": "Read the exact task instruction from observation.goal at reset; MiniWoB++ episodes can vary per seed.",
        "visible_inputs": {
            "native_sources": visible_inputs_mapping.get("native_sources"),
            "evaluator_description": visible_inputs_mapping.get("evaluator_description"),
            "schema": visible_inputs_mapping.get("schema"),
            "available_post_run_artifact_types": visible_inputs_mapping.get("available_post_run_artifact_types"),
            "task_text": task_text,
        },
        "recording": {
            "task_recording_file": reset_info.get("recording_file"),
            "chat_recording_file": ((reset_info.get("chat") or {}).get("recording_file") if isinstance(reset_info.get("chat"), Mapping) else None),
        },
        "action_space_description": action_space_description,
    }


def _native_evaluator_input_payload(
    *,
    config: MiniWoBSmokeConfig,
    task_context: Mapping[str, Any],
    task_kwargs: Mapping[str, Any],
    initial_validation: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "miniwob_native_evaluator_input/v1",
        "env_id": task_context["env_id"],
        "task_id": config.task_id,
        "driver": config.driver,
        "source_entry": config.source_entry,
        "task_context": task_context,
        "task_kwargs": task_kwargs,
        "validator_method": "env.unwrapped.task.validate(page, chat_messages)",
        "initial_validation": initial_validation,
    }


def _native_evaluator_output_payload(
    *,
    config: MiniWoBSmokeConfig,
    task_context: Mapping[str, Any],
    final_validation: Mapping[str, Any],
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    reward = float(final_validation.get("reward") or 0.0)
    done = bool(final_validation.get("done"))
    return {
        "schema_version": "miniwob_native_evaluator_output/v1",
        "env_id": task_context["env_id"],
        "task_id": config.task_id,
        "driver": config.driver,
        "reward": reward,
        "done": done,
        "success": done and reward >= 1.0,
        "message": final_validation.get("message"),
        "info": final_validation.get("info"),
        "step_count": len(steps),
        "steps": [
            {
                "step_index": item["step_index"],
                "action": item["action"],
                "reward": item["reward"],
                "terminated": item["terminated"],
                "truncated": item["truncated"],
                "parse_error": item.get("parse_error"),
            }
            for item in steps
        ],
    }


def _validation_payload(result: Any) -> dict[str, Any]:
    reward, done, message, info = result
    return {
        "reward": float(reward) if isinstance(reward, (int, float, bool)) else reward,
        "done": bool(done),
        "message": str(message or ""),
        "info": _jsonable(info),
    }


def _task_state_payload(task: Any) -> dict[str, Any]:
    payload = {
        "task_class": task.__class__.__name__,
        "task_module": task.__class__.__module__,
    }
    for key, value in vars(task).items():
        if key.startswith("_") or key in {"page", "random"}:
            continue
        payload[key] = _jsonable(value)
    return _sanitize_sensitive_data(payload)


def _worker_artifact_manifest(output_dir: Path) -> dict[str, Any]:
    descriptions = {
        "native_evaluator_input.json": "Official MiniWoB++ validator inputs and task context.",
        "native_evaluator_output.json": "Final env.unwrapped.task.validate(page, chat_messages) output.",
        "task_context.json": "MiniWoB++ task metadata, runtime goal, source metadata, and action-space provenance.",
        "trajectory": "Per-step observations, actions, screenshots, and page HTML snapshots.",
        "browser_artifacts": "Captured screenshots, page HTML, and BrowserGym videos.",
        "task_artifacts": "Reset info, task state, validation outputs, and final task info.",
        "openrouter_calls": "Per-request OpenRouter request/response payloads and parsed action traces.",
    }
    priority = (
        "native_evaluator_input.json",
        "native_evaluator_output.json",
        "run_summary.json",
        "artifact_manifest.json",
        "job.json",
        "source_bundle_entry.json",
        "worker_config.json",
        "task_context.json",
        "browser_artifacts",
        "task_artifacts",
        "trajectory",
        "openrouter_calls",
    )
    entries = []
    for relative in priority:
        path = output_dir / relative
        if not path.exists():
            continue
        entries.append(
            {
                "path": relative,
                "artifact_type": _artifact_type_for_path(relative),
                "description": descriptions.get(relative),
                "is_dir": path.is_dir(),
            }
        )
    return {
        "schema_version": "miniwob_worker_artifact_manifest/v1",
        "entries": entries,
    }


def _artifact_type_for_path(relative: str) -> str:
    if relative == "native_evaluator_input.json":
        return "native_evaluator_input"
    if relative == "native_evaluator_output.json":
        return "native_evaluator_output"
    if relative == "trajectory":
        return "trace"
    if relative == "browser_artifacts":
        return "browser_artifact"
    if relative == "task_artifacts":
        return "post_state"
    if relative == "run_summary.json":
        return "structured_output"
    return "file"


def _source_ref(source_entry: Mapping[str, Any]) -> str | None:
    visible_inputs = source_entry.get("visible_inputs")
    if not isinstance(visible_inputs, Mapping):
        return None
    native_sources = list(visible_inputs.get("native_sources") or [])
    if not native_sources:
        return None
    first = native_sources[0]
    if isinstance(first, Mapping) and first.get("source_ref"):
        return str(first["source_ref"])
    return None


def _safe_page_title(page: Any) -> str | None:
    try:
        return page.title()
    except Exception:  # pragma: no cover - defensive.
        return None


def _safe_page_content(page: Any) -> str:
    try:
        return page.content()
    except Exception as exc:  # pragma: no cover - defensive.
        return f"<html><body><pre>{type(exc).__name__}: {exc}</pre></body></html>"


def _write_html(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
