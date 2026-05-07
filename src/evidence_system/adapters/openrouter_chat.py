"""Shared minimal OpenRouter chat-completion helpers for adapter workers."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Mapping


OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"


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
