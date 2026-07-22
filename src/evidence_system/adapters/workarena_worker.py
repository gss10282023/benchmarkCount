"""Thin WorkArena smoke worker using BrowserGym envs and OpenRouter actions."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import signal
import shutil
import time
import traceback
from typing import Any, Mapping
import urllib.error
import urllib.request


OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
DRIVER_OPENROUTER_CHAT = "openrouter_chat"
DRIVER_OFFICIAL_CHEAT = "official_cheat"
DEFAULT_MAX_AXTREE_NODES = 120
_WORKARENA_RUNTIME_PATCHED = False
SYSTEM_PROMPT = """Return exactly one BrowserGym WorkArena action and nothing else.

Rules:
- Output a single action string such as click('a1') or fill('b2', 'value').
- Do not wrap the action in Markdown.
- Use send_msg_to_user("...") only when the task is complete and you need to answer the user.
- If the page is already at the requested destination, you may use noop().
"""


@dataclass(frozen=True)
class WorkArenaSmokeConfig:
    job: dict[str, Any]
    source_entry: dict[str, Any]
    output_dir: Path
    task_id: str
    model: str | None
    temperature: float
    max_tokens: int
    timeout_seconds: int
    retry: int
    openrouter_api_key_env: str
    max_steps: int
    driver: str
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
    parser.add_argument("--openrouter-api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument("--max-steps", type=int, default=6)
    parser.add_argument("--driver", default=DRIVER_OPENROUTER_CHAT, choices=[DRIVER_OPENROUTER_CHAT, DRIVER_OFFICIAL_CHEAT])
    args = parser.parse_args(argv)
    config = WorkArenaSmokeConfig(
        job=_loads_json_object(args.job_json, field_name="job-json"),
        source_entry=_loads_json_object(args.source_entry_json, field_name="source-entry-json"),
        output_dir=Path(args.output_dir),
        task_id=args.task_id,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout_seconds=args.timeout_seconds,
        retry=args.retry,
        openrouter_api_key_env=args.openrouter_api_key_env,
        max_steps=args.max_steps,
        driver=args.driver,
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


def run_smoke_job(config: WorkArenaSmokeConfig) -> dict[str, Any]:
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
    }
    _write_json(config.output_dir / "run_summary.json", summary)

    env = None
    task_state_initial: dict[str, Any] | None = None
    task_state_final: dict[str, Any] | None = None
    final_validation: dict[str, Any] | None = None
    steps: list[dict[str, Any]] = []
    last_task_info: dict[str, Any] = {}
    _apply_workarena_runtime_patches()
    task_kwargs = _task_kwargs_from_source(config.source_entry)
    action_set = _build_action_set()
    action_space_description = action_set.describe(with_long_description=False, with_examples=True)

    error: Exception | None = None
    try:
        env = _make_workarena_env(config=config, task_kwargs=task_kwargs, action_set=action_set)
        obs, reset_info = env.reset(seed=int(config.job.get("seed", 0)))
        raw = env.unwrapped

        task_state_initial = _task_state_payload(raw.task)
        initial_validation = _validation_payload(raw.task.validate(raw.page, raw.chat.messages))
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
                "official_policy": task_context.get("official_policy"),
                "workflow_description": task_context.get("workflow_description"),
                "goal": task_context.get("goal"),
                "goal_object": task_context.get("goal_object"),
                "fixed_config": task_context.get("fixed_config"),
                "source_ref": task_context.get("source_ref"),
            },
        )

        _capture_browser_state(config.output_dir, raw.page, obs, label="step_000_reset")

        latest_obs = obs
        reward = 0.0
        terminated = False
        truncated = False

        if config.driver == DRIVER_OFFICIAL_CHEAT:
            raw.task.cheat(raw.page, raw.chat.messages)
            latest_obs, reward, terminated, truncated, info = raw.post_step({}, validate=True)
            last_task_info = dict(info.get("task_info") or {})
            step_label = "step_001"
            _capture_browser_state(config.output_dir, raw.page, latest_obs, label=step_label)
            steps.append(
                {
                    "step_index": 1,
                    "driver": config.driver,
                    "action": "official_cheat()",
                    "python_code": None,
                    "reward": reward,
                    "terminated": terminated,
                    "truncated": truncated,
                    "task_info": _jsonable(last_task_info),
                    "observation_path": f"trajectory/observations/{step_label}.json",
                    "screenshot_path": f"browser_artifacts/screenshots/{step_label}.png",
                    "html_path": f"browser_artifacts/page_html/{step_label}.html",
                }
            )
        else:
            api_key = os.environ.get(config.openrouter_api_key_env)
            if not api_key:
                raise RuntimeError(f"missing environment variable {config.openrouter_api_key_env}")
            if not config.model:
                raise RuntimeError("model is required for openrouter_chat driver")
            for step_index in range(1, max(1, config.max_steps) + 1):
                step_prompt = build_step_prompt(
                    config=config,
                    observation=latest_obs,
                    step_index=step_index,
                    action_space_description=action_space_description,
                    previous_steps=steps,
                )
                request_timestamp = _utc_now_iso()
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
                try:
                    response_payload = request_openrouter_completion(
                        api_key=api_key,
                        model=config.model,
                        messages=request_messages,
                        temperature=config.temperature,
                        max_tokens=config.max_tokens,
                        timeout_seconds=config.timeout_seconds,
                        retry=config.retry,
                    )
                except Exception as exc:
                    _write_openrouter_call(
                        path=config.output_dir / "openrouter_calls" / f"call-{step_index:04d}.json",
                        call_id=f"call-{step_index:04d}",
                        request_timestamp=request_timestamp,
                        response_timestamp=_utc_now_iso(),
                        request_payload=request_payload,
                        response_payload=None,
                        action_text="",
                        python_code=None,
                        error_type=type(exc).__name__,
                        error_message=str(exc),
                    )
                    raise
                response_timestamp = _utc_now_iso()
                action_text = extract_action_text(extract_response_content(response_payload))
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

        final_validation = _validation_payload(raw.task.validate(raw.page, raw.chat.messages))
        task_state_final = _task_state_payload(raw.task)
        _write_json(config.output_dir / "task_artifacts" / "task_state_final.json", task_state_final)
        _write_json(config.output_dir / "task_artifacts" / "validation_final.json", final_validation)
        _write_json(config.output_dir / "task_artifacts" / "task_info_final.json", last_task_info)
        _write_json(config.output_dir / "task_artifacts" / "chat_messages_final.json", raw.chat.messages)
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
            close_error = _close_env_with_timeout(env, timeout_seconds=20)
        if close_error:
            summary["close_error"] = close_error
        _write_json(config.output_dir / "artifact_manifest.json", _worker_artifact_manifest(config.output_dir))
        summary["artifact_manifest_path"] = str(config.output_dir / "artifact_manifest.json")
        _write_json(config.output_dir / "run_summary.json", summary)

    if error is not None:
        raise error
    return summary


def _apply_workarena_runtime_patches() -> None:
    """Patch known BrowserGym WorkArena/public-instance mismatches at runtime."""
    global _WORKARENA_RUNTIME_PATCHED
    if _WORKARENA_RUNTIME_PATCHED:
        return
    try:
        from browsergym.workarena.tasks.compositional import dash_do_base
    except Exception:
        _WORKARENA_RUNTIME_PATCHED = True
        return

    for class_name in ("DashboardRetrieveCatalogAndDoTask", "DashboardRetrieveCatalogAndDoInfeasibleTask"):
        task_class = getattr(dash_do_base, class_name, None)
        original = getattr(task_class, "get_catalog_item_sysid", None)
        if not callable(original) or getattr(original, "_evidence_system_patched", False):
            continue

        def patched_get_catalog_item_sysid(self, catalog_item: str, *, _original=original) -> str:
            try:
                return _original(self, catalog_item)
            except Exception as exc:
                if catalog_item == "Notebook Computer Loaner" and "Catalog item not found" in str(exc):
                    return _original(self, "Loaner Laptop")
                raise

        patched_get_catalog_item_sysid._evidence_system_patched = True  # type: ignore[attr-defined]
        setattr(task_class, "get_catalog_item_sysid", patched_get_catalog_item_sysid)

    _WORKARENA_RUNTIME_PATCHED = True


def build_step_prompt(
    *,
    config: WorkArenaSmokeConfig,
    observation: Mapping[str, Any],
    step_index: int,
    action_space_description: str,
    previous_steps: list[dict[str, Any]],
) -> str:
    recent_steps = [
        {
            "step_index": item["step_index"],
            "action": item["action"],
            "reward": item["reward"],
            "terminated": item["terminated"],
            "task_info": item.get("task_info"),
        }
        for item in previous_steps[-3:]
    ]
    prompt_payload = {
        "task_id": config.task_id,
        "step_index": step_index,
        "goal": observation.get("goal"),
        "url": observation.get("url"),
        "open_pages_urls": observation.get("open_pages_urls"),
        "open_pages_titles": observation.get("open_pages_titles"),
        "focused_element_bid": observation.get("focused_element_bid"),
        "last_action": observation.get("last_action"),
        "last_action_error": observation.get("last_action_error"),
        "recent_chat_messages": list(observation.get("chat_messages") or [])[-6:],
        "visible_elements": summarize_visible_elements(
            observation.get("axtree_object"),
            observation.get("extra_element_properties"),
            max_nodes=DEFAULT_MAX_AXTREE_NODES,
        ),
        "recent_steps": recent_steps,
        "allowed_actions": action_space_description,
    }
    return json.dumps(_jsonable(prompt_payload), ensure_ascii=True, indent=2, sort_keys=True)


def summarize_visible_elements(
    axtree: Any,
    extra_element_properties: Any,
    *,
    max_nodes: int,
) -> list[str]:
    if not isinstance(axtree, Mapping):
        return []
    extra = dict(extra_element_properties or {}) if isinstance(extra_element_properties, Mapping) else {}
    lines: list[str] = []
    for node in list(axtree.get("nodes") or []):
        if not isinstance(node, Mapping):
            continue
        bid = node.get("browsergym_id")
        if not bid:
            continue
        props = extra.get(str(bid)) or {}
        visibility = props.get("visibility")
        if isinstance(visibility, (int, float)) and visibility <= 0:
            continue
        role = _ax_value(node.get("role"))
        name = _ax_value(node.get("name"))
        description = _ax_value(node.get("description"))
        value = _ax_value(node.get("value"))
        if not any((role, name, description, value)):
            continue
        parts = [f"bid={bid}"]
        if role:
            parts.append(f"role={role}")
        if name:
            parts.append(f"name={name}")
        if value:
            parts.append(f"value={value}")
        if description:
            parts.append(f"description={description}")
        if props:
            parts.append(f"clickable={bool(props.get('clickable'))}")
        lines.append(" | ".join(parts))
        if len(lines) >= max_nodes:
            break
    return lines


def request_openrouter_completion(
    *,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    timeout_seconds: int,
    retry: int,
    provider_routing: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if provider_routing:
        payload["provider"] = dict(provider_routing)
    body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    last_error: Exception | None = None
    for attempt_index in range(retry + 1):
        request = urllib.request.Request(
            OPENROUTER_CHAT_COMPLETIONS_URL,
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                loaded = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:  # pragma: no cover - network path
            error_body = exc.read().decode("utf-8", errors="replace")
            last_error = RuntimeError(f"OpenRouter HTTP {exc.code}: {error_body[:500]}")
        except urllib.error.URLError as exc:  # pragma: no cover - network path
            last_error = RuntimeError(f"OpenRouter transport error: {exc.reason}")
        else:
            if not isinstance(loaded, dict):
                raise RuntimeError("OpenRouter response must be a JSON object")
            return loaded
        if attempt_index < retry:
            time.sleep(min(1.0 + attempt_index, 3.0))
    raise last_error or RuntimeError("OpenRouter request failed")


def extract_response_content(response_payload: Mapping[str, Any]) -> str:
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("OpenRouter response has no choices")
    first_choice = choices[0]
    if not isinstance(first_choice, Mapping):
        raise RuntimeError("OpenRouter first choice must be an object")
    message = first_choice.get("message")
    if not isinstance(message, Mapping):
        raise RuntimeError("OpenRouter response choice has no message object")
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [item.get("text", "") for item in content if isinstance(item, Mapping)]
        return "\n".join(str(part) for part in parts if part)
    raise RuntimeError("OpenRouter response content is missing")


def extract_action_text(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        stripped = "\n".join(stripped.splitlines()[1:-1]).strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            loaded = json.loads(stripped)
        except json.JSONDecodeError:
            return stripped
        if isinstance(loaded, Mapping):
            for key in ("action", "content", "text"):
                value = loaded.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    return stripped


def _artifact_dirs(output_dir: Path) -> None:
    for path in (
        output_dir,
        output_dir / "browser_artifacts" / "recordings",
        output_dir / "browser_artifacts" / "screenshots",
        output_dir / "browser_artifacts" / "page_html",
        output_dir / "trajectory" / "observations",
        output_dir / "task_artifacts",
        output_dir / "openrouter_calls",
    ):
        path.mkdir(parents=True, exist_ok=True)


def _build_action_set() -> Any:
    from browsergym.core.action.highlevel import HighLevelActionSet

    return HighLevelActionSet(subsets="workarena", multiaction=False, strict=False)


def _make_workarena_env(
    *,
    config: WorkArenaSmokeConfig,
    task_kwargs: Mapping[str, Any],
    action_set: Any,
) -> Any:
    import gymnasium as gym
    import browsergym.workarena  # noqa: F401

    return gym.make(
        _resolved_env_id(config.task_id),
        headless=config.headless,
        record_video_dir=str(config.output_dir / "browser_artifacts" / "recordings") if config.record_video else None,
        task_kwargs=dict(task_kwargs),
        action_mapping=action_set.to_python_code,
    )


def _resolved_env_id(task_id: str) -> str:
    task_id = str(task_id).strip()
    if task_id.startswith("browsergym/"):
        return task_id
    return f"browsergym/{task_id}"


def _task_kwargs_from_source(source_entry: Mapping[str, Any]) -> dict[str, Any]:
    visible_inputs = source_entry.get("visible_inputs")
    if not isinstance(visible_inputs, Mapping):
        return {}
    task_kwargs: dict[str, Any] = {}
    task_text = visible_inputs.get("task_text")
    if isinstance(task_text, Mapping):
        fixed_config = task_text.get("fixed_config")
        if isinstance(fixed_config, Mapping):
            task_kwargs["fixed_config"] = dict(fixed_config)
        nested_kwargs = task_text.get("task_kwargs")
        if isinstance(nested_kwargs, Mapping):
            task_kwargs.update(dict(nested_kwargs))
    top_level_kwargs = visible_inputs.get("task_kwargs")
    if isinstance(top_level_kwargs, Mapping):
        task_kwargs.update(dict(top_level_kwargs))
    return task_kwargs


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
    _write_text(output_dir / "browser_artifacts" / "page_html" / f"{label}.html", _safe_page_content(page))
    try:
        page.screenshot(path=str(output_dir / "browser_artifacts" / "screenshots" / f"{label}.png"))
    except Exception as exc:  # pragma: no cover - defensive.
        _write_json(
            output_dir / "browser_artifacts" / "screenshots" / f"{label}.error.json",
            {"error_type": type(exc).__name__, "error_message": str(exc)},
        )


def _task_context_payload(
    *,
    config: WorkArenaSmokeConfig,
    raw_env: Any,
    reset_info: Mapping[str, Any],
    initial_observation: Mapping[str, Any],
    task_kwargs: Mapping[str, Any],
    action_space_description: str,
) -> dict[str, Any]:
    visible_inputs = config.source_entry.get("visible_inputs")
    visible_inputs_mapping = dict(visible_inputs or {}) if isinstance(visible_inputs, Mapping) else {}
    task_text = visible_inputs_mapping.get("task_text")
    workflow_description = None
    if isinstance(task_text, Mapping):
        workflow_description = task_text.get("workflow_description") or task_text.get("instruction")
    if not workflow_description and hasattr(raw_env.task, "get_pretty_printed_description"):
        try:
            workflow_description = raw_env.task.get_pretty_printed_description()
        except Exception:  # pragma: no cover - optional helper.
            workflow_description = None
    return {
        "schema_version": "workarena_task_context/v1",
        "env_id": _resolved_env_id(config.task_id),
        "task_id": config.task_id,
        "task_class": raw_env.task.__class__.__name__,
        "task_module": raw_env.task.__class__.__module__,
        "goal": initial_observation.get("goal"),
        "goal_object": initial_observation.get("goal_object"),
        "task_info_initial": reset_info.get("task_info"),
        "official_policy": visible_inputs_mapping.get("official_policy") or config.source_entry.get("official_policy"),
        "workflow_description": workflow_description,
        "fixed_config": task_kwargs.get("fixed_config"),
        "task_kwargs": task_kwargs,
        "source_ref": _source_ref(config.source_entry),
        "visible_inputs": {
            "native_sources": visible_inputs_mapping.get("native_sources"),
            "evaluator_description": visible_inputs_mapping.get("evaluator_description"),
            "schema": visible_inputs_mapping.get("schema"),
            "trace_schema": visible_inputs_mapping.get("trace_schema"),
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
    config: WorkArenaSmokeConfig,
    task_context: Mapping[str, Any],
    task_kwargs: Mapping[str, Any],
    initial_validation: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "workarena_native_evaluator_input/v1",
        "env_id": task_context["env_id"],
        "task_id": config.task_id,
        "driver": config.driver,
        "source_entry": config.source_entry,
        "task_context": task_context,
        "task_kwargs": task_kwargs,
        "validator_method": "env.task.validate(page, chat_messages)",
        "initial_validation": initial_validation,
    }


def _native_evaluator_output_payload(
    *,
    config: WorkArenaSmokeConfig,
    task_context: Mapping[str, Any],
    final_validation: Mapping[str, Any],
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    reward = float(final_validation.get("reward") or 0.0)
    done = bool(final_validation.get("done"))
    return {
        "schema_version": "workarena_native_evaluator_output/v1",
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
    entries = []
    descriptions = {
        "native_evaluator_input.json": "Official WorkArena validator inputs and task context.",
        "native_evaluator_output.json": "Final env.task.validate(page, chat_messages) output.",
        "task_context.json": "Task policy, workflow description, source metadata, and action-space provenance.",
        "trajectory": "Per-step observations, actions, screenshots, and page HTML snapshots.",
        "browser_artifacts": "Captured screenshots, page HTML, and BrowserGym videos.",
        "task_artifacts": "Enterprise workflow/task state before and after execution plus validator info.",
        "openrouter_calls": "Raw OpenRouter requests and responses used by the smoke agent.",
    }
    for relative in (
        "native_evaluator_input.json",
        "native_evaluator_output.json",
        "task_context.json",
        "trajectory",
        "browser_artifacts",
        "task_artifacts",
        "openrouter_calls",
    ):
        path = output_dir / relative
        if not path.exists():
            continue
        entries.append(
            {
                "path": relative,
                "artifact_type": _worker_artifact_type(relative),
                "description": descriptions.get(relative, relative),
            }
        )
    return {
        "schema_version": "workarena_step8_artifact_manifest/v1",
        "task_id": output_dir.name,
        "artifacts": entries,
    }


def _worker_artifact_type(relative: str) -> str:
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
    return "file"


def _write_openrouter_call(
    *,
    path: Path,
    call_id: str,
    request_timestamp: str,
    response_timestamp: str,
    request_payload: Mapping[str, Any],
    response_payload: Mapping[str, Any] | None,
    action_text: str,
    python_code: str | None,
    error_type: str | None,
    error_message: str | None,
) -> None:
    _write_json(
        path,
        {
            "call_id": call_id,
            "request_timestamp": request_timestamp,
            "response_timestamp": response_timestamp,
            "request_payload": request_payload,
            "response_payload": response_payload,
            "action_text": action_text,
            "python_code": python_code,
            "error_type": error_type,
            "error_message": error_message,
        },
    )


def _source_ref(source_entry: Mapping[str, Any]) -> str | None:
    visible_inputs = source_entry.get("visible_inputs")
    if not isinstance(visible_inputs, Mapping):
        return None
    native_sources = list(visible_inputs.get("native_sources") or [])
    if not native_sources:
        return None
    first = native_sources[0]
    if isinstance(first, Mapping):
        value = first.get("source_ref")
        if value:
            return str(value)
    return None


def _safe_page_title(page: Any) -> str | None:
    try:
        value = page.title()
    except Exception:  # pragma: no cover - defensive.
        return None
    return str(value) if value is not None else None


def _safe_page_content(page: Any) -> str:
    try:
        return str(page.content())
    except Exception as exc:  # pragma: no cover - defensive.
        return f"<!-- failed to capture page content: {type(exc).__name__}: {exc} -->"


def _close_env_with_timeout(env: Any, *, timeout_seconds: int) -> str | None:
    if not hasattr(signal, "SIGALRM"):
        try:
            env.close()
        except Exception as exc:  # pragma: no cover - defensive.
            return f"{type(exc).__name__}: {exc}"
        return None

    def _handler(_signum: int, _frame: Any) -> None:
        raise TimeoutError(f"env.close() exceeded {timeout_seconds}s")

    previous_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _handler)
    signal.alarm(max(1, timeout_seconds))
    try:
        env.close()
    except Exception as exc:  # pragma: no cover - defensive.
        return f"{type(exc).__name__}: {exc}"
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)
    return None


def _ax_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        inner = value.get("value")
        return inner if inner not in {"", None} else None
    return value if value not in {"", None} else None


def _sanitize_sensitive_data(value: Any, *, key_name: str | None = None) -> Any:
    lowered = (key_name or "").lower()
    if any(token in lowered for token in ("password", "secret", "token", "credential", "api_key")):
        return "REDACTED"
    if isinstance(value, Mapping):
        return {
            str(key): _sanitize_sensitive_data(child, key_name=str(key))
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [_sanitize_sensitive_data(child) for child in value]
    if isinstance(value, tuple):
        return [_sanitize_sensitive_data(child) for child in value]
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
        return tolist()
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
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
