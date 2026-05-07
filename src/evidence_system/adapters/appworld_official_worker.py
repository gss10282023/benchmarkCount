"""Run a single AppWorld task through the official simplified ReAct code agent."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import shutil
import traceback
from typing import Any, Mapping


_SOURCE_REF_RE = re.compile(r"^appworld://(?P<dataset>[^/]+)/(?P<task_id>[^/]+)$")
_ZERO_COST = {
    "input_cache_miss": 0.0,
    "input_cache_hit": 0.0,
    "input_cache_write": 0.0,
    "output": 0.0,
}


@dataclass(frozen=True)
class AppWorldOfficialConfig:
    job: dict[str, Any]
    source_entry: dict[str, Any]
    output_dir: Path
    experiment_name: str
    provider: str
    model: str
    temperature: float
    max_tokens: int
    openrouter_api_key_env: str
    max_steps: int
    lm_retry_after_seconds: int
    lm_max_retries: int


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-json", required=True)
    parser.add_argument("--source-entry-json", default="{}")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--openrouter-api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument("--max-steps", type=int, default=50)
    parser.add_argument("--lm-retry-after-seconds", type=int, default=15)
    parser.add_argument("--lm-max-retries", type=int, default=100)
    args = parser.parse_args(argv)
    config = AppWorldOfficialConfig(
        job=_loads_json_object(args.job_json, field_name="job-json"),
        source_entry=_loads_json_object(args.source_entry_json, field_name="source-entry-json"),
        output_dir=Path(args.output_dir),
        experiment_name=args.experiment_name,
        provider=args.provider,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        openrouter_api_key_env=args.openrouter_api_key_env,
        max_steps=args.max_steps,
        lm_retry_after_seconds=args.lm_retry_after_seconds,
        lm_max_retries=args.lm_max_retries,
    )
    try:
        summary = run_official_job(config)
    except Exception as exc:  # pragma: no cover - integration path
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


def run_official_job(config: AppWorldOfficialConfig) -> dict[str, Any]:
    output_dir = config.output_dir
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    task_id = str(config.job["task_id"])
    dataset_name = resolve_dataset_name(task_id=task_id, source_entry=config.source_entry)
    model_id = resolve_model_id(provider=config.provider, model=config.model)

    _write_json(output_dir / "job.json", config.job)
    _write_json(output_dir / "source_bundle_entry.json", config.source_entry)
    _write_json(output_dir / "worker_config.json", _config_payload(config))

    summary: dict[str, Any] = {
        "status": "running",
        "job_id": str(config.job.get("job_id") or ""),
        "task_id": task_id,
        "dataset_name": dataset_name,
        "experiment_name": config.experiment_name,
        "provider": config.provider,
        "model": config.model,
        "official_agent_name": "simplified_react_code_agent",
        "official_prompt_path": "react_code_agent/instructions.txt",
        "max_steps": config.max_steps,
        "compatibility_mode": "locked_data_runtime_patch",
    }
    _write_json(output_dir / "run_summary.json", summary)

    appworld_root = os.environ.get("APPWORLD_ROOT")
    if not appworld_root:
        raise RuntimeError("APPWORLD_ROOT must be set")
    os.environ.setdefault("OPENAI_API_KEY", "unused-for-litellm")

    from appworld.common.path_store import path_store
    from appworld.evaluator import evaluate_task
    from appworld_agents.code.simplified.run import run_experiment

    data_version = apply_locked_data_compatibility_patch(appworld_root)
    summary["data_version"] = data_version
    _write_json(output_dir / "run_summary.json", summary)

    prompt_file_path = os.path.join(path_store.experiment_prompts, "react_code_agent", "instructions.txt")
    runner_config = build_runner_config(
        dataset_name=dataset_name,
        prompt_file_path=prompt_file_path,
        model_id=model_id,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        api_key_env_name=config.openrouter_api_key_env,
        max_steps=config.max_steps,
        lm_retry_after_seconds=config.lm_retry_after_seconds,
        lm_max_retries=config.lm_max_retries,
        random_seed=int(config.job.get("seed", 100) or 100),
    )
    _write_json(output_dir / "official_runner_config.json", runner_config)
    native_input = build_native_evaluator_input(
        task_id=task_id,
        dataset_name=dataset_name,
        experiment_name=config.experiment_name,
        source_entry=config.source_entry,
        model_id=model_id,
        runner_config=runner_config,
    )
    _write_json(output_dir / "native_evaluator_input.json", native_input)

    task_output_root = Path(appworld_root) / "experiments" / "outputs" / config.experiment_name / "tasks" / task_id
    try:
        run_experiment(
            experiment_name=config.experiment_name,
            runner_config=runner_config,
            task_id=task_id,
            num_processes=1,
            process_index=0,
        )
        tracker = evaluate_task(
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
            }
        )
        _write_json(output_dir / "run_summary.json", summary)
        copy_tree(task_output_root, output_dir / "appworld_task_output")
        raise

    copy_tree(task_output_root, output_dir / "appworld_task_output")
    native_output = {
        "schema_version": "appworld_native_evaluator_output/v1",
        "task_id": task_id,
        "dataset_name": dataset_name,
        "experiment_name": config.experiment_name,
        "tracker": tracker_dict,
    }
    _write_json(output_dir / "native_evaluator_output.json", native_output)
    artifact_manifest = build_artifact_manifest(
        output_dir=output_dir,
        task_id=task_id,
        dataset_name=dataset_name,
        experiment_name=config.experiment_name,
        tracker_dict=tracker_dict,
    )
    _write_json(output_dir / "artifact_manifest.json", artifact_manifest)

    summary.update(
        {
            "status": "completed",
            "success": bool(tracker_dict.get("success")) if isinstance(tracker_dict, Mapping) else None,
            "evaluation_pass_count": _tracker_pass_count(tracker_dict),
            "data_version": data_version,
        }
    )
    _write_json(output_dir / "run_summary.json", summary)
    return summary


def build_runner_config(
    *,
    dataset_name: str,
    prompt_file_path: str,
    model_id: str,
    temperature: float,
    max_tokens: int,
    api_key_env_name: str,
    max_steps: int,
    lm_retry_after_seconds: int,
    lm_max_retries: int,
    random_seed: int,
) -> dict[str, Any]:
    return {
        "agent": {
            "type": "simplified_react_code_agent",
            "model_config": {
                "name": model_id,
                "client_name": "litellm",
                "api_type": "chat_completions",
                "temperature": temperature,
                "max_tokens": max_tokens,
                "seed": random_seed,
                "tool_parser_name": None,
                "drop_reasoning_content": False,
                "retry_after_n_seconds": lm_retry_after_seconds,
                "max_retries": lm_max_retries,
                "use_cache": False,
                "api_key_env_name": api_key_env_name,
                "cost_per_token": _ZERO_COST,
            },
            "appworld_config": {
                "random_seed": random_seed,
                "raise_on_extra_parameters": True,
            },
            "logger_config": {
                "color": True,
                "verbose": True,
            },
            "usage_tracker_config": {
                "max_cost_overall": 1000,
                "max_cost_per_task": 10,
                "max_output_tokens_per_task": 100000,
            },
            "prompt_file_path": prompt_file_path,
            "ignore_multiple_calls": True,
            "max_prompt_length": None,
            "max_output_length": None,
            "max_steps": max_steps,
            "log_lm_calls": True,
            "skip_if_finished": True,
        },
        "dataset": dataset_name,
    }


def build_native_evaluator_input(
    *,
    task_id: str,
    dataset_name: str,
    experiment_name: str,
    source_entry: Mapping[str, Any],
    model_id: str,
    runner_config: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "appworld_native_evaluator_input/v1",
        "task_id": task_id,
        "dataset_name": dataset_name,
        "experiment_name": experiment_name,
        "source_ref": resolve_source_ref(task_id=task_id, source_entry=source_entry),
        "official_agent_name": "simplified_react_code_agent",
        "official_prompt_path": "react_code_agent/instructions.txt",
        "model_id": model_id,
        "runner_config": _jsonable(runner_config),
    }


def build_artifact_manifest(
    *,
    output_dir: Path,
    task_id: str,
    dataset_name: str,
    experiment_name: str,
    tracker_dict: Mapping[str, Any] | None,
) -> dict[str, Any]:
    artifacts = [
        {
            "artifact_type": "native_evaluator_input",
            "path": "native_evaluator_input.json",
            "description": "Official simplified_react_code_agent runner configuration for this AppWorld task.",
        },
        {
            "artifact_type": "native_evaluator_output",
            "path": "native_evaluator_output.json",
            "description": "Official AppWorld evaluator result serialized from TestTracker.",
        },
        {
            "artifact_type": "file",
            "path": "official_runner_config.json",
            "description": "Exact official simplified_react_code_agent runner config passed to run_experiment().",
        },
        {
            "artifact_type": "api_log",
            "path": "appworld_task_output/logs/api_calls.jsonl",
            "description": "Official AppWorld API call log.",
        },
        {
            "artifact_type": "trace",
            "path": "appworld_task_output/logs/environment_io.md",
            "description": "Official AppWorld environment interaction transcript.",
        },
        {
            "artifact_type": "file",
            "path": "appworld_task_output/logs/lm_calls.jsonl",
            "description": "Official simplified agent LM call log.",
        },
        {
            "artifact_type": "database_snapshot",
            "path": "appworld_task_output/dbs",
            "description": "Task output database state captured by the official AppWorld environment.",
        },
        {
            "artifact_type": "file",
            "path": "appworld_task_output/evaluation",
            "description": "Official task-level evaluation report.",
        },
        {
            "artifact_type": "file",
            "path": "appworld_task_output/misc",
            "description": "Official simplified agent auxiliary outputs, including usage.json and finished marker.",
        },
    ]
    return {
        "schema_version": "appworld_step8_artifact_manifest/v1",
        "task_id": task_id,
        "dataset_name": dataset_name,
        "experiment_name": experiment_name,
        "output_dir": str(output_dir),
        "evaluation_success": bool(tracker_dict.get("success")) if isinstance(tracker_dict, Mapping) else None,
        "artifacts": artifacts,
    }


def resolve_model_id(*, provider: str, model: str) -> str:
    if provider == "openrouter":
        return f"openrouter/{model}"
    return model


def resolve_dataset_name(*, task_id: str, source_entry: Mapping[str, Any]) -> str:
    source_ref = resolve_source_ref(task_id=task_id, source_entry=source_entry)
    match = _SOURCE_REF_RE.match(source_ref or "")
    if match:
        return str(match.group("dataset"))
    raise RuntimeError(f"could not resolve AppWorld dataset name for task_id={task_id}")


def resolve_source_ref(*, task_id: str, source_entry: Mapping[str, Any]) -> str | None:
    explicit = source_entry.get("source_ref")
    if isinstance(explicit, str) and explicit:
        return explicit
    visible_inputs = source_entry.get("visible_inputs")
    if isinstance(visible_inputs, Mapping):
        native_sources = list(visible_inputs.get("native_sources") or [])
        if native_sources and isinstance(native_sources[0], Mapping):
            value = native_sources[0].get("source_ref") or native_sources[0].get("task_dir")
            if value:
                return str(value)
    selected_split_path = Path("experiments/official_splits/appworld_selected_task_sources.json")
    if selected_split_path.exists():
        loaded = json.loads(selected_split_path.read_text(encoding="utf-8"))
        for item in list(loaded.get("items") or []):
            if isinstance(item, Mapping) and str(item.get("task_id")) == task_id:
                value = item.get("source_ref")
                if value:
                    return str(value)
    return None


def apply_locked_data_compatibility_patch(appworld_root: str) -> str | None:
    version_path = Path(appworld_root) / "data" / "version.txt"
    if not version_path.exists():
        return None
    data_version = version_path.read_text(encoding="utf-8").strip()
    if not data_version:
        return None

    import appworld.common.constants as constants
    import appworld.environment as environment_module
    import appworld.evaluator as evaluator_module
    import appworld.task as task_module

    if data_version not in constants.COMPATIBLE_DATA_VERSIONS:
        constants.COMPATIBLE_DATA_VERSIONS.append(data_version)
    if data_version not in constants.COMPATIBLE_DB_VERSIONS:
        constants.COMPATIBLE_DB_VERSIONS.append(data_version)
    if data_version not in task_module.COMPATIBLE_DB_VERSIONS:
        task_module.COMPATIBLE_DB_VERSIONS.append(data_version)
    constants.DB_VERSION = data_version
    environment_module.DB_VERSION = data_version
    evaluator_module.DB_VERSION = data_version
    return data_version


def copy_tree(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    shutil.copytree(source, destination, dirs_exist_ok=True)


def _config_payload(config: AppWorldOfficialConfig) -> dict[str, Any]:
    payload = asdict(config)
    payload["output_dir"] = str(config.output_dir)
    return payload


def _loads_json_object(value: str, *, field_name: str) -> dict[str, Any]:
    loaded = json.loads(value)
    if not isinstance(loaded, dict):
        raise ValueError(f"{field_name} must decode to a JSON object")
    return loaded


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


if __name__ == "__main__":
    raise SystemExit(main())
