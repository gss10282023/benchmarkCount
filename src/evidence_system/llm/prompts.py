"""Prompt loading and hashing helpers for auditable LLM calls."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evidence_system.core.hashing import sha256_bytes
from evidence_system.core.paths import resolve_repo_path


@dataclass(frozen=True)
class PromptRecord:
    prompt_version: str
    prompt_hash: str
    prompt_hash_method: str
    content: str
    source_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_version": self.prompt_version,
            "prompt_hash": self.prompt_hash,
            "prompt_hash_method": self.prompt_hash_method,
            "content": self.content,
            "source_path": self.source_path,
        }


def load_prompt(path: str | Path, *, prompt_version: str | None = None) -> PromptRecord:
    resolved = resolve_repo_path(path)
    content = resolved.read_text(encoding="utf-8")
    version = prompt_version or resolved.stem
    return PromptRecord(
        prompt_version=version,
        prompt_hash=hash_prompt(content),
        prompt_hash_method="sha256",
        content=content,
        source_path=str(resolved),
    )


def hash_prompt(content: str) -> str:
    return sha256_bytes(content.encode("utf-8"))
