"""Thin AppWorld smoke worker using the official Python package APIs."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import shutil
import time
import traceback
from types import ModuleType
from typing import Any, Mapping
import urllib.error
import urllib.request


OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
SYSTEM_PROMPT = """You are writing Python for an AppWorld task.

Return only executable Python. Do not wrap the code in prose or markdown unless the caller explicitly asks.

The execution environment already provides:
- `apis`: application APIs for the task world
- `requester`: lower-level requester if needed
- common stdlib-style imports such as json, datetime, itertools, math, random, re, Counter, defaultdict

Requirements:
- Solve the task using the documented APIs only.
- Inspect the task state before acting when identifiers or records are ambiguous.
- Use supervisor APIs to confirm and complete the task when the work is done.
- Keep the code concise and robust.
- Do not call input(), do not ask for human clarification, and do not emit explanations outside the Python code.
"""

_FENCED_CODE_RE = re.compile(r"```(?:python)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
_MODEL_APP_RE = re.compile(r"['\"]([a-z_]+)\.[A-Za-z][A-Za-z0-9_]*['\"]")


@dataclass(frozen=True)
class AppWorldSmokeConfig:
    job: dict[str, Any]
    source_entry: dict[str, Any]
    output_dir: Path
    experiment_name: str
    model: str
    temperature: float
    max_tokens: int
    timeout_seconds: int
    retry: int
    openrouter_api_key_env: str
    max_agent_attempts: int


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-json", required=True)
    parser.add_argument("--source-entry-json", default="{}")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--retry", type=int, default=0)
    parser.add_argument("--openrouter-api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument("--max-agent-attempts", type=int, default=3)
    args = parser.parse_args(argv)
    config = AppWorldSmokeConfig(
        job=_loads_json_object(args.job_json, field_name="job-json"),
        source_entry=_loads_json_object(args.source_entry_json, field_name="source-entry-json"),
        output_dir=Path(args.output_dir),
        experiment_name=args.experiment_name,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout_seconds=args.timeout_seconds,
        retry=args.retry,
        openrouter_api_key_env=args.openrouter_api_key_env,
        max_agent_attempts=args.max_agent_attempts,
    )
    try:
        summary = run_smoke_job(config)
    except Exception as exc:  # pragma: no cover - exercised through run_smoke_job tests.
        error_payload = {
            "status": "error",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback": traceback.format_exc(),
        }
        print(json.dumps(error_payload, ensure_ascii=True, indent=2))
        return 1
    print(json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True))
    return 0 if summary.get("status") != "error" else 1


def run_smoke_job(config: AppWorldSmokeConfig) -> dict[str, Any]:
    output_dir = config.output_dir
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    attempts_dir = output_dir / "llm_attempts"
    attempts_dir.mkdir(parents=True, exist_ok=True)

    task_id = str(config.job["task_id"])
    api_key = os.environ.get(config.openrouter_api_key_env)
    if not api_key:
        raise RuntimeError(f"missing environment variable {config.openrouter_api_key_env}")

    _write_json(output_dir / "job.json", config.job)
    _write_json(output_dir / "source_bundle_entry.json", config.source_entry)
    _write_json(output_dir / "worker_config.json", _config_payload(config))

    summary: dict[str, Any] = {
        "status": "running",
        "job_id": str(config.job.get("job_id") or ""),
        "task_id": task_id,
        "experiment_name": config.experiment_name,
        "model": config.model,
        "max_agent_attempts": config.max_agent_attempts,
    }
    _write_json(output_dir / "run_summary.json", summary)

    appworld_env_module, appworld_task_module, appworld_evaluator_module = _load_appworld_modules()
    task = appworld_task_module.Task.load(task_id=task_id, load_ground_truth=True)
    relevant_apps = infer_relevant_apps(config.source_entry, available_apps=_task_available_apps(task))
    prompt_context = build_prompt_context(task, config.source_entry, relevant_apps=relevant_apps)
    native_evaluator_input = build_native_evaluator_input(
        task=task,
        source_entry=config.source_entry,
        experiment_name=config.experiment_name,
        relevant_apps=relevant_apps,
    )
    _write_json(output_dir / "task_prompt_context.json", prompt_context)
    _write_json(output_dir / "native_evaluator_input.json", native_evaluator_input)

    messages = build_initial_messages(prompt_context)
    execution_records: list[dict[str, Any]] = []
    tracker_dict: dict[str, Any] | None = None
    appworld_output_root = output_dir / "appworld_task_output"

    try:
        with appworld_env_module.AppWorld(
            task_id=task_id,
            experiment_name=config.experiment_name,
            random_seed=int(config.job.get("seed", 0)),
            timeout_seconds=config.timeout_seconds,
            max_interactions=max(config.max_agent_attempts, 1),
        ) as environment:
            for attempt_index in range(1, config.max_agent_attempts + 1):
                prompt_record = {
                    "attempt": attempt_index,
                    "messages": messages,
                    "model": config.model,
                    "temperature": config.temperature,
                    "max_tokens": config.max_tokens,
                }
                _write_json(attempts_dir / f"{attempt_index:02d}_prompt.json", prompt_record)
                response = request_openrouter_completion(
                    api_key=api_key,
                    model=config.model,
                    messages=messages,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    timeout_seconds=config.timeout_seconds,
                    retry=config.retry,
                )
                response_content = extract_response_content(response)
                code = extract_python_code(response_content)
                _write_json(attempts_dir / f"{attempt_index:02d}_response.json", response)
                _write_text(attempts_dir / f"{attempt_index:02d}_code.py", code)

                execution_output = str(environment.execute(code))
                task_completed = bool(environment.task_completed())
                record = {
                    "attempt": attempt_index,
                    "task_completed": task_completed,
                    "execution_output": execution_output,
                    "assistant_response_preview": response_content[:4000],
                }
                execution_records.append(record)
                _write_json(attempts_dir / f"{attempt_index:02d}_execution.json", record)

                messages = messages + [
                    {"role": "assistant", "content": response_content},
                    {
                        "role": "user",
                        "content": build_feedback_message(
                            execution_output=execution_output,
                            task_completed=task_completed,
                        ),
                    },
                ]
                if task_completed:
                    break

        tracker = appworld_evaluator_module.evaluate_task(
            task_id=task_id,
            experiment_name=config.experiment_name,
            suppress_errors=True,
            save_report=True,
        )
        tracker_dict = tracker.to_dict(stats_only=False) if hasattr(tracker, "to_dict") else _jsonable(tracker)
    except Exception as exc:
        summary.update(
            {
                "status": "error",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": traceback.format_exc(),
                "execution_attempts": execution_records,
            }
        )
        _write_json(output_dir / "run_summary.json", summary)
        copy_appworld_output_tree(
            destination=appworld_output_root,
            appworld_root=os.environ.get("APPWORLD_ROOT"),
            experiment_name=config.experiment_name,
            task_id=task_id,
        )
        raise

    native_output_payload = {
        "schema_version": "appworld_native_evaluator_output/v1",
        "task_id": task_id,
        "experiment_name": config.experiment_name,
        "tracker": tracker_dict,
    }
    _write_json(output_dir / "native_evaluator_output.json", native_output_payload)
    copy_appworld_output_tree(
        destination=appworld_output_root,
        appworld_root=os.environ.get("APPWORLD_ROOT"),
        experiment_name=config.experiment_name,
        task_id=task_id,
    )

    artifact_manifest = build_artifact_manifest(
        output_dir=output_dir,
        task_id=task_id,
        experiment_name=config.experiment_name,
        execution_attempts=execution_records,
        tracker_dict=tracker_dict,
    )
    _write_json(output_dir / "artifact_manifest.json", artifact_manifest)

    summary.update(
        {
            "status": "completed",
            "success": bool(tracker_dict.get("success")) if isinstance(tracker_dict, Mapping) else None,
            "evaluation_pass_count": _tracker_pass_count(tracker_dict),
            "execution_attempts": execution_records,
            "artifact_manifest_path": str(output_dir / "artifact_manifest.json"),
        }
    )
    _write_json(output_dir / "run_summary.json", summary)
    return summary


def _config_payload(config: AppWorldSmokeConfig) -> dict[str, Any]:
    payload = asdict(config)
    payload["output_dir"] = str(config.output_dir)
    return payload


def _loads_json_object(value: str, *, field_name: str) -> dict[str, Any]:
    loaded = json.loads(value)
    if not isinstance(loaded, dict):
        raise ValueError(f"{field_name} must decode to a JSON object")
    return loaded


def _load_appworld_modules() -> tuple[ModuleType, ModuleType, ModuleType]:
    import importlib

    env_module = importlib.import_module("appworld.environment")
    task_module = importlib.import_module("appworld.task")
    evaluator_module = importlib.import_module("appworld.evaluator")
    return env_module, task_module, evaluator_module


def _task_available_apps(task: Any) -> list[str]:
    allowed = getattr(task, "allowed_apps", None)
    if isinstance(allowed, list):
        return [str(item) for item in allowed]
    return list(getattr(getattr(task, "api_docs", {}), "keys", lambda: [])())


def infer_relevant_apps(source_entry: Mapping[str, Any], *, available_apps: list[str]) -> list[str]:
    found: list[str] = []
    visible_inputs = source_entry.get("visible_inputs")
    if isinstance(visible_inputs, Mapping):
        evaluator_code = str(visible_inputs.get("evaluator_code") or "")
        for match in _MODEL_APP_RE.findall(evaluator_code):
            if match not in found:
                found.append(match)
    filtered = [app for app in found if app in available_apps]
    if filtered:
        if "supervisor" in available_apps and "supervisor" not in filtered:
            filtered.insert(0, "supervisor")
        return filtered
    return list(dict.fromkeys(str(app) for app in available_apps if str(app)))


def build_prompt_context(task: Any, source_entry: Mapping[str, Any], *, relevant_apps: list[str]) -> dict[str, Any]:
    api_docs = getattr(task, "api_docs", {})
    if hasattr(api_docs, "compress_parameters"):
        api_docs = api_docs.compress_parameters()
    if hasattr(api_docs, "compress_response_schemas"):
        api_docs = api_docs.compress_response_schemas()
    if relevant_apps and hasattr(api_docs, "keep_apps"):
        api_docs = api_docs.keep_apps(relevant_apps)
    api_docs_payload = _jsonable(api_docs)
    if not relevant_apps and isinstance(api_docs_payload, Mapping):
        relevant_apps = list(api_docs_payload.keys())

    prompt_context = {
        "task_id": str(getattr(task, "id", "")),
        "instruction": str(getattr(task, "instruction", "")),
        "supervisor": _jsonable(getattr(task, "supervisor", {})),
        "datetime": _stringify_datetime(getattr(task, "datetime", None)),
        "relevant_apps": relevant_apps,
        "app_descriptions": {
            name: description
            for name, description in dict(getattr(task, "app_descriptions", {}) or {}).items()
            if not relevant_apps or name in relevant_apps
        },
        "api_docs": api_docs_payload,
        "source_ref": _source_ref(source_entry),
        "source_instruction": _source_instruction(source_entry),
    }
    return prompt_context


def build_initial_messages(prompt_context: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Task context follows as JSON. Write the next Python action block only.\n\n"
                + json.dumps(_jsonable(prompt_context), ensure_ascii=True, indent=2, sort_keys=True)
            ),
        },
    ]


def build_feedback_message(*, execution_output: str, task_completed: bool) -> str:
    return (
        "The previous Python block was executed in the same persistent AppWorld environment.\n"
        "Write the next Python block only.\n\n"
        f"task_completed={str(task_completed).lower()}\n"
        "execution_output:\n"
        f"{execution_output[-4000:]}"
    )


def build_native_evaluator_input(
    *,
    task: Any,
    source_entry: Mapping[str, Any],
    experiment_name: str,
    relevant_apps: list[str],
) -> dict[str, Any]:
    ground_truth = getattr(task, "ground_truth", None)
    payload = {
        "schema_version": "appworld_native_evaluator_input/v1",
        "task_id": str(getattr(task, "id", "")),
        "experiment_name": experiment_name,
        "instruction": str(getattr(task, "instruction", "")),
        "supervisor": _jsonable(getattr(task, "supervisor", {})),
        "datetime": _stringify_datetime(getattr(task, "datetime", None)),
        "relevant_apps": relevant_apps,
        "source_ref": _source_ref(source_entry),
        "source_instruction": _source_instruction(source_entry),
    }
    if ground_truth is not None:
        payload["ground_truth"] = {
            "answer": _jsonable(getattr(ground_truth, "answer", None)),
            "metadata": _jsonable(getattr(ground_truth, "metadata", None)),
            "public_data": _jsonable(getattr(ground_truth, "public_data", None)),
            "private_data": _jsonable(getattr(ground_truth, "private_data", None)),
            "test_data": _jsonable(getattr(ground_truth, "test_data", None)),
        }
    visible_inputs = source_entry.get("visible_inputs")
    if isinstance(visible_inputs, Mapping):
        payload["visible_evaluator_inputs"] = {
            "evaluator_code": visible_inputs.get("evaluator_code"),
            "native_sources": _jsonable(visible_inputs.get("native_sources")),
            "schema": _jsonable(visible_inputs.get("schema")),
            "trace_schema": _jsonable(visible_inputs.get("trace_schema")),
            "available_post_run_artifact_types": _jsonable(visible_inputs.get("available_post_run_artifact_types")),
        }
    return payload


def request_openrouter_completion(
    *,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
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


def extract_response_content(response: Mapping[str, Any]) -> str:
    choices = response.get("choices")
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


def extract_python_code(text: str) -> str:
    match = _FENCED_CODE_RE.search(text)
    if match:
        return match.group(1).strip()
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            loaded = json.loads(stripped)
        except json.JSONDecodeError:
            return stripped
        if isinstance(loaded, Mapping):
            for key in ("code", "python", "content"):
                value = loaded.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    return stripped


def copy_appworld_output_tree(
    *,
    destination: Path,
    appworld_root: str | None,
    experiment_name: str,
    task_id: str,
) -> None:
    if not appworld_root:
        return
    source = Path(appworld_root) / "experiments" / "outputs" / experiment_name / "tasks" / task_id
    if not source.exists():
        return
    shutil.copytree(source, destination, dirs_exist_ok=True)


def build_artifact_manifest(
    *,
    output_dir: Path,
    task_id: str,
    experiment_name: str,
    execution_attempts: list[dict[str, Any]],
    tracker_dict: Mapping[str, Any] | None,
) -> dict[str, Any]:
    artifacts = [
        {
            "artifact_type": "native_evaluator_input",
            "path": "native_evaluator_input.json",
            "description": "Official task evaluator inputs and supporting metadata captured after the run.",
        },
        {
            "artifact_type": "native_evaluator_output",
            "path": "native_evaluator_output.json",
            "description": "Official AppWorld evaluator result serialized from TestTracker.",
        },
        {
            "artifact_type": "trace",
            "path": "appworld_task_output/logs/environment_io.md",
            "description": "Persistent environment interaction transcript written by AppWorld.",
        },
        {
            "artifact_type": "api_log",
            "path": "appworld_task_output/logs/api_calls.jsonl",
            "description": "Official AppWorld API call log.",
        },
        {
            "artifact_type": "database_snapshot",
            "path": "appworld_task_output/dbs",
            "description": "Task output database changes captured by the AppWorld environment.",
        },
        {
            "artifact_type": "file",
            "path": "llm_attempts",
            "description": "Per-attempt prompts, raw OpenRouter responses, generated Python, and execution feedback.",
        },
    ]
    return {
        "schema_version": "appworld_step8_artifact_manifest/v1",
        "task_id": task_id,
        "experiment_name": experiment_name,
        "output_dir": str(output_dir),
        "evaluation_success": bool(tracker_dict.get("success")) if isinstance(tracker_dict, Mapping) else None,
        "execution_attempt_count": len(execution_attempts),
        "artifacts": artifacts,
    }


def _source_ref(source_entry: Mapping[str, Any]) -> str | None:
    visible_inputs = source_entry.get("visible_inputs")
    if not isinstance(visible_inputs, Mapping):
        return None
    native_sources = list(visible_inputs.get("native_sources") or [])
    if not native_sources or not isinstance(native_sources[0], Mapping):
        return None
    value = native_sources[0].get("source_ref") or native_sources[0].get("task_dir")
    return str(value) if value else None


def _source_instruction(source_entry: Mapping[str, Any]) -> str | None:
    visible_inputs = source_entry.get("visible_inputs")
    if not isinstance(visible_inputs, Mapping):
        return None
    task_text = visible_inputs.get("task_text")
    if not isinstance(task_text, Mapping):
        return None
    instruction = task_text.get("instruction")
    return str(instruction) if instruction else None


def _stringify_datetime(value: Any) -> str | None:
    if value is None:
        return None
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        return str(isoformat())
    return str(value)


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
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        return str(isoformat())
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _jsonable(value.to_dict())
    if hasattr(value, "__dict__"):
        return {
            key: _jsonable(child)
            for key, child in vars(value).items()
            if not key.startswith("_")
        }
    return str(value)


def _tracker_pass_count(tracker_dict: Mapping[str, Any] | None) -> int | None:
    if not isinstance(tracker_dict, Mapping):
        return None
    passes = tracker_dict.get("passes")
    if not isinstance(passes, list):
        return None
    return len(passes)


def _write_json(path: Path, payload: Mapping[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(payload), ensure_ascii=True, indent=2, sort_keys=True) + "\n")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
