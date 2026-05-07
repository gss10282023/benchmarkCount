"""Run one ToolSandbox scenario with OpenRouter-backed roles."""

from __future__ import annotations

import argparse
import json
import os
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from evidence_system.contracts.common import utc_now_iso, write_json
from evidence_system.core.hashing import sha256_object


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-json", required=True)
    parser.add_argument("--source-entry-json", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--user-model", required=True)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--retry", type=int, default=0)
    parser.add_argument("--openrouter-api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument("--preferred-tool-backend", default="DEFAULT")
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    started_at = utc_now_iso()
    job = json.loads(args.job_json)
    source_entry = json.loads(args.source_entry_json)
    write_json(output_dir / "job.json", job)
    write_json(output_dir / "source_bundle_entry.json", source_entry)
    write_json(
        output_dir / "worker_config.json",
        {
            "runner_kind": "toolsandbox_direct_api",
            "toolsandbox_version": "0.0.1",
            "openrouter_base_url": OPENROUTER_BASE_URL,
            "agent_model": args.model,
            "user_model": args.user_model,
            "temperature": args.temperature,
            "max_tokens": args.max_tokens,
            "timeout_seconds": args.timeout_seconds,
            "retry": args.retry,
            "api_key_env": args.openrouter_api_key_env,
            "preferred_tool_backend": args.preferred_tool_backend,
            "scenario": args.scenario,
        },
    )

    try:
        api_key = os.environ.get(args.openrouter_api_key_env)
        if not api_key:
            raise RuntimeError(f"missing required environment variable {args.openrouter_api_key_env}")
        result_payload = _run_toolsandbox(
            output_dir=output_dir,
            scenario_name=args.scenario,
            preferred_tool_backend=args.preferred_tool_backend,
            agent_model=args.model,
            user_model=args.user_model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            timeout_seconds=args.timeout_seconds,
            retry=args.retry,
            api_key=api_key,
            job=job,
            source_entry=source_entry,
        )
        ended_at = utc_now_iso()
        summary = {
            "status": "completed",
            "runner_kind": "toolsandbox_direct_api",
            "scenario": args.scenario,
            "success": bool(float(result_payload.get("similarity") or 0.0) >= 0.999),
            "similarity": float(result_payload.get("similarity") or 0.0),
            "milestone_similarity": float(result_payload.get("milestone_similarity") or 0.0),
            "minefield_similarity": float(result_payload.get("minefield_similarity") or 0.0),
            "turn_count": int(result_payload.get("turn_count") or 0),
            "exception_type": result_payload.get("exception_type"),
            "started_at": started_at,
            "ended_at": ended_at,
        }
        write_json(output_dir / "run_summary.json", summary)
        return 0
    except Exception as exc:
        ended_at = utc_now_iso()
        write_json(
            output_dir / "run_summary.json",
            {
                "status": "error",
                "runner_kind": "toolsandbox_direct_api",
                "scenario": args.scenario,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": traceback.format_exc(),
                "started_at": started_at,
                "ended_at": ended_at,
            },
        )
        return 1


def _run_toolsandbox(
    *,
    output_dir: Path,
    scenario_name: str,
    preferred_tool_backend: str,
    agent_model: str,
    user_model: str,
    temperature: float,
    max_tokens: int,
    timeout_seconds: int,
    retry: int,
    api_key: str,
    job: Mapping[str, Any],
    source_entry: Mapping[str, Any],
) -> dict[str, Any]:
    from openai import NOT_GIVEN, OpenAI
    from tool_sandbox.cli.utils import resolve_scenarios
    from tool_sandbox.common.execution_context import RoleType
    from tool_sandbox.common.tool_discovery import ToolBackend
    from tool_sandbox.roles.execution_environment import ExecutionEnvironment
    from tool_sandbox.roles.openai_api_agent import OpenAIAPIAgent
    from tool_sandbox.roles.openai_api_user import OpenAIAPIUser

    call_dir = output_dir / "openrouter_calls"
    call_dir.mkdir(parents=True, exist_ok=True)
    recorder = _OpenRouterCallRecorder(call_dir)

    class OpenRouterAgent(OpenAIAPIAgent):
        model_name = agent_model

        def __init__(self) -> None:
            self.openai_client = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL, timeout=timeout_seconds)

        def model_inference(self, openai_messages: list[dict[str, Any]], openai_tools: Any) -> Any:
            return _chat_completion_with_capture(
                client=self.openai_client,
                recorder=recorder,
                role_name="agent",
                model=self.model_name,
                messages=openai_messages,
                tools=openai_tools,
                not_given=NOT_GIVEN,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_seconds=timeout_seconds,
                retry=retry,
            )

    class OpenRouterUser(OpenAIAPIUser):
        model_name = user_model

        def __init__(self) -> None:
            self.openai_client = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL, timeout=timeout_seconds)

        def model_inference(self, openai_messages: list[dict[str, Any]], openai_tools: Any) -> Any:
            return _chat_completion_with_capture(
                client=self.openai_client,
                recorder=recorder,
                role_name="user",
                model=self.model_name,
                messages=openai_messages,
                tools=openai_tools,
                not_given=NOT_GIVEN,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_seconds=timeout_seconds,
                retry=retry,
            )

    backend = ToolBackend(preferred_tool_backend)
    scenarios = resolve_scenarios(
        desired_scenario_names=[scenario_name],
        preferred_tool_backend=backend,
    )
    scenario = scenarios[scenario_name]
    scenario_context = {
        "scenario": scenario_name,
        "categories": [str(category) for category in scenario.categories],
        "max_messages": scenario.max_messages,
        "source_entry_hash": sha256_object(source_entry),
    }
    write_json(output_dir / "scenario_context.json", scenario_context)
    write_json(
        output_dir / "native_evaluator_input.json",
        {
            "scenario": scenario_name,
            "categories": scenario_context["categories"],
            "job": {
                "job_id": job.get("job_id"),
                "case_unit_id": job.get("case_unit_id"),
                "task_id": job.get("task_id"),
                "agent_id": job.get("agent_id"),
                "seed": job.get("seed"),
            },
            "evaluation_source": "ToolSandbox scenario.evaluation.evaluate(execution_context, max_turn_count)",
        },
    )

    roles = {
        RoleType.USER: OpenRouterUser(),
        RoleType.EXECUTION_ENVIRONMENT: ExecutionEnvironment(),
        RoleType.AGENT: OpenRouterAgent(),
    }
    try:
        result = scenario.play_and_evaluate(
            roles=roles,
            output_directory=output_dir,
            scenario_name=scenario_name,
        )
        result_payload = {
            "name": scenario_name,
            "categories": scenario_context["categories"],
            "traceback": None,
            "exception_type": None,
            "milestone_similarity": result.evaluation_result.milestone_similarity,
            "minefield_similarity": result.evaluation_result.minefield_similarity,
            "similarity": result.evaluation_result.similarity,
            "turn_count": result.evaluation_result.turn_count,
            "milestone_mapping": result.evaluation_result.milestone_mapping,
            "minefield_mapping": result.evaluation_result.minefield_mapping,
        }
    except Exception as exc:
        result_payload = {
            "name": scenario_name,
            "categories": scenario_context["categories"],
            "traceback": traceback.format_exc(),
            "exception_type": type(exc).__name__,
            "milestone_similarity": 0.0,
            "minefield_similarity": 0.0,
            "similarity": 0.0,
            "turn_count": scenario.max_messages,
            "milestone_mapping": {},
            "minefield_mapping": {},
        }
    finally:
        for role in roles.values():
            role.teardown()

    result_payload = _jsonable(result_payload)
    native_output = {
        "scenario": scenario_name,
        "score": float(result_payload.get("similarity") or 0.0),
        "status": "success" if float(result_payload.get("similarity") or 0.0) >= 0.999 else "fail",
        "per_scenario_result": result_payload,
    }
    write_json(output_dir / "native_evaluator_output.json", native_output)
    write_json(
        output_dir / "result_summary.json",
        {
            "per_scenario_results": [result_payload],
            "category_aggregated_results": _category_summary(result_payload),
            "git_sha": None,
        },
    )
    _write_derived_artifacts(output_dir=output_dir, scenario_name=scenario_name)
    return result_payload


def _chat_completion_with_capture(
    *,
    client: Any,
    recorder: "_OpenRouterCallRecorder",
    role_name: str,
    model: str,
    messages: list[dict[str, Any]],
    tools: Any,
    not_given: Any,
    temperature: float,
    max_tokens: int,
    timeout_seconds: int,
    retry: int,
) -> Any:
    request_payload: dict[str, Any] = {
        "model": model,
        "messages": _jsonable(messages),
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools is not not_given:
        request_payload["tools"] = _jsonable(tools)
        kwargs["tools"] = tools

    last_error: Exception | None = None
    for attempt in range(retry + 1):
        request_timestamp = utc_now_iso()
        try:
            response = client.chat.completions.create(**kwargs)
            response_timestamp = _response_timestamp_after(request_timestamp)
            recorder.record(
                role_name=role_name,
                attempt=attempt,
                request_timestamp=request_timestamp,
                response_timestamp=response_timestamp,
                request_payload=request_payload,
                response_payload=_jsonable(response),
                error_type=None,
                error_message=None,
                timeout_seconds=timeout_seconds,
            )
            return response
        except Exception as exc:
            last_error = exc
            response_timestamp = _response_timestamp_after(request_timestamp)
            recorder.record(
                role_name=role_name,
                attempt=attempt,
                request_timestamp=request_timestamp,
                response_timestamp=response_timestamp,
                request_payload=request_payload,
                response_payload=None,
                error_type=type(exc).__name__,
                error_message=str(exc),
                timeout_seconds=timeout_seconds,
            )
    raise RuntimeError(f"OpenRouter ToolSandbox {role_name} call failed after {retry + 1} attempts: {last_error}")


class _OpenRouterCallRecorder:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.index = 0

    def record(
        self,
        *,
        role_name: str,
        attempt: int,
        request_timestamp: str,
        response_timestamp: str,
        request_payload: Mapping[str, Any],
        response_payload: Any,
        error_type: str | None,
        error_message: str | None,
        timeout_seconds: int,
    ) -> None:
        self.index += 1
        call_id = f"toolsandbox-{role_name}-{self.index:04d}"
        write_json(
            self.output_dir / f"{call_id}.json",
            {
                "call_id": call_id,
                "toolsandbox_role": role_name,
                "attempt": attempt,
                "request_timestamp": request_timestamp,
                "response_timestamp": response_timestamp,
                "request_payload": dict(request_payload),
                "response_payload": response_payload,
                "error_type": error_type,
                "error_message": error_message,
                "transport": "openrouter",
                "timeout_seconds": timeout_seconds,
            },
        )


def _category_summary(result_payload: Mapping[str, Any]) -> dict[str, dict[str, float]]:
    score = float(result_payload.get("similarity") or 0.0)
    turns = float(result_payload.get("turn_count") or 0.0)
    summary: dict[str, dict[str, float]] = {
        "ALL_CATEGORIES": {"similarity": score, "turn_count": turns}
    }
    for category in list(result_payload.get("categories") or []):
        summary[str(category)] = {"similarity": score, "turn_count": turns}
    return summary


def _write_derived_artifacts(*, output_dir: Path, scenario_name: str) -> None:
    scenario_dir = output_dir / "trajectories" / scenario_name
    conversation_path = scenario_dir / "conversation.json"
    messages_path = output_dir / "messages.jsonl"
    tool_calls_path = output_dir / "tool_calls.jsonl"
    if conversation_path.exists():
        conversation = json.loads(conversation_path.read_text(encoding="utf-8"))
        if isinstance(conversation, list):
            with messages_path.open("w", encoding="utf-8") as f:
                for index, message in enumerate(conversation):
                    f.write(json.dumps({"index": index, "message": message}, ensure_ascii=False) + "\n")
            with tool_calls_path.open("w", encoding="utf-8") as f:
                for index, message in enumerate(conversation):
                    if not isinstance(message, Mapping):
                        continue
                    if message.get("tool_calls"):
                        f.write(
                            json.dumps(
                                {
                                    "index": index,
                                    "role": message.get("role"),
                                    "tool_calls": message.get("tool_calls"),
                                },
                                ensure_ascii=False,
                            )
                            + "\n"
                        )
                    if message.get("role") == "tool":
                        f.write(json.dumps({"index": index, "tool_result": message}, ensure_ascii=False) + "\n")
    execution_context_path = scenario_dir / "execution_context.json"
    if execution_context_path.exists():
        write_json(
            output_dir / "post_state.json",
            {
                "scenario": scenario_name,
                "execution_context_path": str(execution_context_path),
                "execution_context_sha256": sha256_object(
                    json.loads(execution_context_path.read_text(encoding="utf-8"))
                ),
            },
        )


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return {str(key): _jsonable(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_jsonable(child) for child in value]
    if isinstance(value, tuple):
        return [_jsonable(child) for child in value]
    if isinstance(value, set):
        return sorted(_jsonable(child) for child in value)
    if hasattr(value, "to_dict"):
        return _jsonable(value.to_dict())
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _response_timestamp_after(request_timestamp: str) -> str:
    try:
        request_dt = datetime.fromisoformat(request_timestamp.replace("Z", "+00:00"))
    except ValueError:
        return utc_now_iso()
    response_dt = datetime.now(timezone.utc).replace(microsecond=0)
    if response_dt > request_dt:
        return response_dt.isoformat()
    return (request_dt + timedelta(microseconds=1)).isoformat()


if __name__ == "__main__":  # pragma: no cover - exercised by smoke execution.
    raise SystemExit(main())
