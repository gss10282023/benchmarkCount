"""Bootstrap config loading.

This module only proves that checked-in config files can be read as structured
objects. Formal schema validation is implemented in a later step.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from evidence_system.core.errors import ConfigValidationError
from evidence_system.core.hashing import sha256_file
from evidence_system.core.paths import resolve_repo_path


@dataclass(frozen=True)
class ConfigReadResult:
    path: str
    sha256: str
    schema_version: str
    top_level_keys: list[str]


@dataclass(frozen=True)
class ConfigValidationSummary:
    status: str
    formal_schema_validation: str
    files: list[ConfigReadResult]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["note"] = "Step 2 reads structured configs only; formal validation belongs to Step 3."
        return data


def _load_json_or_yaml(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as json_error:
        try:
            import yaml  # type: ignore[import-not-found]
        except ModuleNotFoundError as exc:
            raise ConfigValidationError(
                f"{path} is not JSON and PyYAML is not installed for YAML parsing"
            ) from exc
        try:
            return yaml.safe_load(text)
        except Exception as yaml_error:  # pragma: no cover - depends on optional parser
            raise ConfigValidationError(f"could not parse {path}: {yaml_error}") from json_error


def read_config_file(path: str | Path) -> ConfigReadResult:
    resolved = resolve_repo_path(path)
    if not resolved.exists():
        raise ConfigValidationError(f"missing config file: {resolved}")
    loaded = _load_json_or_yaml(resolved)
    if not isinstance(loaded, dict):
        raise ConfigValidationError(f"config file must be a mapping: {resolved}")
    schema_version = loaded.get("schema_version")
    if not isinstance(schema_version, str) or not schema_version:
        raise ConfigValidationError(f"missing string schema_version: {resolved}")
    rel_path = str(resolved.relative_to(resolve_repo_path(".")))
    return ConfigReadResult(
        path=rel_path,
        sha256=sha256_file(resolved),
        schema_version=schema_version,
        top_level_keys=sorted(str(key) for key in loaded.keys()),
    )


def validate_config_files(paths: list[str | Path]) -> ConfigValidationSummary:
    files = [read_config_file(path) for path in paths]
    return ConfigValidationSummary(
        status="ok",
        formal_schema_validation="not_implemented_in_step_2",
        files=files,
    )


def add_config_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--infra-config",
        default="configs/infra.yaml",
        help="Path to infra config.",
    )
    parser.add_argument(
        "--agents-config",
        default="configs/agents.yaml",
        help="Path to agent config.",
    )
