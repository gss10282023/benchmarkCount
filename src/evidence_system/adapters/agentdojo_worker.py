"""Thin AgentDojo smoke worker with a local OpenAI-compatible OpenRouter proxy."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import socket
import threading
import time
import traceback
from typing import Any, Mapping
import urllib.error
import urllib.request


OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"


@dataclass(frozen=True)
class AgentDojoSmokeConfig:
    job: dict[str, Any]
    source_entry: dict[str, Any]
    output_dir: Path
    suite: str
    user_task: str
    injection_task: str
    benchmark_version: str
    model_id: str
    temperature: float
    max_tokens: int
    timeout_seconds: int
    retry: int
    openrouter_api_key_env: str
    tool_delimiter: str
    attack: str


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-json", required=True)
    parser.add_argument("--source-entry-json", default="{}")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--suite", required=True)
    parser.add_argument("--user-task", required=True)
    parser.add_argument("--injection-task", required=True)
    parser.add_argument("--benchmark-version", default="v1.2.2")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--retry", type=int, default=0)
    parser.add_argument("--openrouter-api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument("--tool-delimiter", default="tool")
    parser.add_argument("--attack", default="direct")
    args = parser.parse_args(argv)
    config = AgentDojoSmokeConfig(
        job=_loads_json_object(args.job_json),
        source_entry=_loads_json_object(args.source_entry_json),
        output_dir=Path(args.output_dir),
        suite=args.suite,
        user_task=args.user_task,
        injection_task=args.injection_task,
        benchmark_version=args.benchmark_version,
        model_id=args.model_id,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout_seconds=args.timeout_seconds,
        retry=args.retry,
        openrouter_api_key_env=args.openrouter_api_key_env,
        tool_delimiter=args.tool_delimiter,
        attack=args.attack,
    )
    try:
        summary = run_smoke_job(config)
    except Exception as exc:  # pragma: no cover - exercised by remote runs.
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


def run_smoke_job(config: AgentDojoSmokeConfig) -> dict[str, Any]:
    config = _normalize_config(config)
    if config.output_dir.exists():
        shutil.rmtree(config.output_dir)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    proxy_calls_dir = config.output_dir / "proxy_calls"
    proxy_calls_dir.mkdir(parents=True, exist_ok=True)
    _write_json(config.output_dir / "job.json", config.job)
    _write_json(config.output_dir / "source_bundle_entry.json", config.source_entry)
    _write_json(config.output_dir / "worker_config.json", _jsonable(asdict(config)))

    api_key = os.environ.get(config.openrouter_api_key_env)
    if not api_key:
        raise RuntimeError(f"missing environment variable {config.openrouter_api_key_env}")

    port = _available_port()
    os.environ["LOCAL_LLM_PORT"] = str(port)
    proxy = OpenRouterProxyServer(
        host="127.0.0.1",
        port=port,
        api_key=api_key,
        model_id=config.model_id,
        timeout_seconds=config.timeout_seconds,
        retry=config.retry,
        log_dir=proxy_calls_dir,
    )
    proxy.start()
    try:
        try:
            summary = _run_agentdojo_benchmark(config)
            error_calls = _proxy_error_calls(proxy_calls_dir)
            if error_calls:
                first = error_calls[0]
                raise RuntimeError(
                    f"OpenRouter proxy recorded {len(error_calls)} failed LLM call(s); "
                    f"first={first['path']}: {first['error_message']}"
                )
        except Exception as exc:
            summary = {
                "status": "error",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": traceback.format_exc(),
            }
            _write_json(config.output_dir / "run_summary.json", summary)
            raise
    finally:
        proxy.stop()
    _write_json(config.output_dir / "run_summary.json", summary)
    return summary


def _run_agentdojo_benchmark(config: AgentDojoSmokeConfig) -> dict[str, Any]:
    from agentdojo.agent_pipeline.agent_pipeline import AgentPipeline, PipelineConfig
    from agentdojo.attacks.attack_registry import load_attack
    from agentdojo.benchmark import run_task_with_injection_tasks, run_task_without_injection_tasks
    from agentdojo.logging import OutputLogger
    from agentdojo.models import ModelsEnum
    from agentdojo.task_suite.load_suites import get_suite

    suite = get_suite(config.benchmark_version, config.suite)
    pipeline = AgentPipeline.from_config(
        PipelineConfig(
            llm=ModelsEnum.LOCAL,
            model_id=config.model_id,
            defense=None,
            tool_delimiter=config.tool_delimiter,
            system_message_name=None,
            system_message=None,
        )
    )
    attack = load_attack(config.attack, suite, pipeline)
    logdir = config.output_dir / "trace_logs"

    user_task = suite.get_user_task_by_id(config.user_task)
    injection_task = suite.get_injection_task_by_id(config.injection_task)
    with OutputLogger(logdir=str(logdir)):
        benign_utility, benign_security = run_task_without_injection_tasks(
            suite,
            pipeline,
            user_task,
            logdir=logdir,
            force_rerun=True,
            benchmark_version=config.benchmark_version,
        )
        injection_task_utility, injection_task_security = run_task_without_injection_tasks(
            suite,
            pipeline,
            injection_task,
            logdir=logdir,
            force_rerun=True,
            benchmark_version=config.benchmark_version,
        )
        utility_results, security_results = run_task_with_injection_tasks(
            suite,
            pipeline,
            user_task,
            attack,
            logdir=logdir,
            force_rerun=True,
            injection_tasks=[config.injection_task],
            benchmark_version=config.benchmark_version,
        )
    injected_key = (config.user_task, config.injection_task)
    injected_utility = bool(utility_results[injected_key])
    injected_security = bool(security_results[injected_key])

    native_output = {
        "schema_version": "agentdojo_native_evaluator_output/v1",
        "suite_name": config.suite,
        "user_task_id": config.user_task,
        "injection_task_id": config.injection_task,
        "attack_name": config.attack,
        "benchmark_version": config.benchmark_version,
        "benign": {
            "utility": bool(benign_utility),
            "security": bool(benign_security),
        },
        "injection_task_as_user_task": {
            "utility": bool(injection_task_utility),
            "security": bool(injection_task_security),
        },
        "injected": {
            "utility": injected_utility,
            "security": injected_security,
        },
    }
    _write_json(config.output_dir / "native_evaluator_output.json", native_output)
    _write_json(
        config.output_dir / "native_evaluator_input.json",
        {
            "schema_version": "agentdojo_native_evaluator_input/v1",
            "suite_name": config.suite,
            "user_task_id": config.user_task,
            "injection_task_id": config.injection_task,
            "source_entry": config.source_entry,
        },
    )
    return {
        "status": "completed",
        "suite_name": config.suite,
        "user_task_id": config.user_task,
        "injection_task_id": config.injection_task,
        "attack_name": config.attack,
        "benign_utility": bool(benign_utility),
        "injection_task_utility": bool(injection_task_utility),
        "injected_utility": injected_utility,
        "injected_security": injected_security,
    }


class OpenRouterProxyServer:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        api_key: str,
        model_id: str,
        timeout_seconds: int,
        retry: int,
        log_dir: Path,
    ) -> None:
        self.host = host
        self.port = port
        self.api_key = api_key
        self.model_id = model_id
        self.timeout_seconds = timeout_seconds
        self.retry = retry
        self.log_dir = log_dir
        self._counter = 0
        handler = self._build_handler()
        self.server = ThreadingHTTPServer((host, port), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def _build_handler(self):
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:  # pragma: no cover - noisy stdlib hook
                return

            def do_GET(self) -> None:
                if self.path.rstrip("/") != "/v1/models":
                    self.send_error(404)
                    return
                payload = {
                    "object": "list",
                    "data": [
                        {
                            "id": outer.model_id,
                            "object": "model",
                            "created": int(time.time()),
                            "owned_by": "openrouter-proxy",
                        }
                    ],
                }
                self._send_json(200, payload)

            def do_POST(self) -> None:
                if self.path.rstrip("/") != "/v1/chat/completions":
                    self.send_error(404)
                    return
                length = int(self.headers.get("Content-Length") or 0)
                raw_body = self.rfile.read(length)
                request_payload = json.loads(raw_body.decode("utf-8"))
                forwarded = {
                    "model": outer.model_id,
                    "messages": _normalize_chat_messages(request_payload.get("messages", [])),
                    "temperature": request_payload.get("temperature", 0.0),
                }
                if request_payload.get("max_tokens") is not None:
                    forwarded["max_tokens"] = request_payload["max_tokens"]
                request_at = _utc_now_iso()
                response_payload = None
                error_message = None
                try:
                    response_payload = _request_openrouter(
                        api_key=outer.api_key,
                        payload=forwarded,
                        timeout_seconds=outer.timeout_seconds,
                        retry=outer.retry,
                    )
                except Exception as exc:  # pragma: no cover - remote-only path
                    error_message = str(exc)
                    self._send_json(500, {"error": {"message": error_message}})
                else:
                    self._send_json(200, response_payload)
                finally:
                    outer._counter += 1
                    response_at = _utc_now_iso()
                    _write_json(
                        outer.log_dir / f"{outer._counter:04d}.json",
                        {
                            "call_id": f"agentdojo-proxy-{outer._counter:04d}",
                            "request_timestamp": request_at,
                            "response_timestamp": response_at,
                            "request_payload": request_payload,
                            "forwarded_payload": forwarded,
                            "response_payload": response_payload,
                            "error_message": error_message,
                        },
                    )

            def _send_json(self, status_code: int, payload: Mapping[str, Any]) -> None:
                encoded = json.dumps(payload, ensure_ascii=True).encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

        return Handler


def _request_openrouter(
    *,
    api_key: str,
    payload: Mapping[str, Any],
    timeout_seconds: int,
    retry: int,
) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    last_error: Exception | None = None
    for attempt in range(retry + 1):
        request = urllib.request.Request(
            OPENROUTER_CHAT_COMPLETIONS_URL,
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                loaded = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            last_error = RuntimeError(f"OpenRouter HTTP {exc.code}: {error_body[:500]}")
        except urllib.error.URLError as exc:
            last_error = RuntimeError(f"OpenRouter transport error: {exc.reason}")
        else:
            if not isinstance(loaded, dict):
                raise RuntimeError("OpenRouter response must be a JSON object")
            return loaded
        if attempt < retry:
            time.sleep(min(1.0 + attempt, 3.0))
    raise last_error or RuntimeError("OpenRouter request failed")


def _loads_json_object(value: str) -> dict[str, Any]:
    loaded = json.loads(value)
    if not isinstance(loaded, dict):
        raise ValueError("expected a JSON object")
    return loaded


def _normalize_chat_messages(messages: Any) -> list[dict[str, str]]:
    if not isinstance(messages, list):
        return [{"role": "user", "content": _message_content_to_text(messages)}]

    normalized: list[dict[str, str]] = []
    for item in messages:
        if not isinstance(item, Mapping):
            role = "user"
            content = _message_content_to_text(item)
            prefix = ""
        else:
            source_role = str(item.get("role") or "user")
            content = _message_content_to_text(item.get("content"))
            prefix = ""
            if source_role in {"tool", "function"}:
                role = "user"
                name = item.get("name")
                label = "Tool result" if source_role == "tool" else "Function result"
                prefix = f"{label} ({name}):\n" if name else f"{label}:\n"
            elif source_role in {"system", "user", "assistant"}:
                role = source_role
                if not content and item.get("tool_calls"):
                    content = _message_content_to_text(item.get("tool_calls"))
            else:
                role = "user"
                prefix = f"{source_role} message:\n"

        content = f"{prefix}{content}".strip()
        if not content:
            continue
        if normalized and normalized[-1]["role"] == role:
            normalized[-1]["content"] = f"{normalized[-1]['content']}\n\n{content}"
        else:
            normalized.append({"role": role, "content": content})
    return normalized or [{"role": "user", "content": ""}]


def _message_content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, Mapping):
                if isinstance(item.get("text"), str):
                    parts.append(str(item["text"]))
                elif isinstance(item.get("content"), str):
                    parts.append(str(item["content"]))
                else:
                    parts.append(json.dumps(_jsonable(item), ensure_ascii=True, sort_keys=True))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part)
    return json.dumps(_jsonable(content), ensure_ascii=True, sort_keys=True)


def _normalize_config(config: AgentDojoSmokeConfig) -> AgentDojoSmokeConfig:
    model_id = config.model_id.removeprefix("openrouter/")
    if model_id == config.model_id:
        return config
    payload = asdict(config)
    payload["model_id"] = model_id
    return AgentDojoSmokeConfig(**payload)


def _proxy_error_calls(proxy_calls_dir: Path) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for path in sorted(proxy_calls_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append({"path": str(path), "error_message": f"invalid proxy call JSON: {exc}"})
            continue
        error_message = payload.get("error_message") if isinstance(payload, Mapping) else None
        if error_message:
            errors.append({"path": str(path), "error_message": str(error_message)})
    return errors


def _available_port() -> int:
    with socket.socket() as handle:
        handle.bind(("127.0.0.1", 0))
        return int(handle.getsockname()[1])


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonable(child) for key, child in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(child) for child in value]
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return _jsonable(value.model_dump())
    if hasattr(value, "__dict__"):
        return {key: _jsonable(child) for key, child in vars(value).items() if not key.startswith("_")}
    return str(value)


def _write_json(path: Path, payload: Mapping[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(payload), ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
