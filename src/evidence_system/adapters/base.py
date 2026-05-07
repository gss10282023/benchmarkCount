"""Shared Step 8 adapter planning/runtime primitives."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shlex
from typing import TYPE_CHECKING, Any

from evidence_system.llm.openrouter_client import load_role_config

if TYPE_CHECKING:
    from evidence_system.orchestrator.jobs import InfraBenchmarkTarget


@dataclass(frozen=True)
class AdapterSkeleton:
    canonical_domain_id: str
    supports_direct_execution: bool = False


def runner_plan(
    *,
    status: str,
    command: str | None,
    target: "InfraBenchmarkTarget",
    expected_artifact_types: tuple[str, ...],
    blocking_reason: str | None = None,
    notes: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "status": status,
        "machine_id": target.machine_id,
        "machine_role": target.machine_role,
        "benchmark_name": target.benchmark_name,
        "remote_workdir": target.remote_workdir,
        "runner_workdir": target.runner_workdir,
        "runner_command": command,
        "expected_artifact_types": list(expected_artifact_types),
        "blocking_reason": blocking_reason,
        "notes": list(notes),
    }


def smoke_agent_role(job: dict[str, Any]) -> str:
    return str(job["agent_id"])


def smoke_role_config(job: dict[str, Any], *, agents_config_path: str | Path) -> dict[str, Any]:
    config = load_role_config(smoke_agent_role(job), agents_config_path=agents_config_path, formal=False)
    return {
        "provider": config.provider,
        "model": config.model,
        "model_version": config.model_version,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "timeout_seconds": config.timeout_seconds,
        "retry": config.retry,
        "api_key_env": config.api_key_env,
    }


def is_smoke_phase(job: dict[str, Any] | Any) -> bool:
    return str(getattr(job, "get", lambda *_args, **_kwargs: None)("phase") or "smoke") == "smoke"


def dotenv_source_prefix(dotenv_path: str | Path, *, repo_root: str) -> str:
    candidate = str(Path(repo_root) / dotenv_path)
    quoted = shlex.quote(candidate)
    return f"set -a && . {quoted} && set +a"


def json_arg(value: Any) -> str:
    return shlex.quote(json.dumps(value, ensure_ascii=True, sort_keys=True))
