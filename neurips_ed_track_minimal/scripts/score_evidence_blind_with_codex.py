#!/usr/bin/env python3
"""Outcome-blind AppWorld evidence scoring with independently locked stages.

The released evaluator label is deliberately outside this program's input
contract.  Native registered tests are scored first and SHA-locked.  Stronger
conditions are then scored in a separate Codex invocation with a separate
prompt and no access to the native score.  Both aggregate verdicts are derived
deterministically from their per-condition statuses.
"""

from __future__ import annotations

import argparse
import grp
import hashlib
import json
import os
import pwd
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from jsonschema import Draft202012Validator


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
PACKAGE_ROOT = ROOT_DIR.parent

if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from neurips_ed_track_minimal.scripts import (  # noqa: E402
    score_evidence_with_codex as legacy,
)


NATIVE_PROMPT_PATH = ROOT_DIR / "prompts" / "score_evidence_native_blind.prompt.md"
STRONGER_PROMPT_PATH = (
    ROOT_DIR / "prompts" / "score_evidence_stronger_blind.prompt.md"
)
FINAL_SCHEMA_PATH = SCRIPT_DIR / "blind_evidence_score.schema.json"
DEFAULT_MODEL = "gpt-5.4"
DEFAULT_REASONING_EFFORT = "high"
DEFAULT_SERVICE_TIER = "default"
APPWORLD_TEST_MARKER_RE = re.compile(r"\[(appworld_test_[A-Za-z0-9._-]+)\]")
CHECK_STATUSES = ("supported", "contradicted", "undecided")
FORBIDDEN_BLIND_FILENAMES = frozenset(
    {
        "artifact_manifest.json",
        "component_evaluator_output.json",
        "native_label.json",
        "released_evaluator_label.json",
        "native_evaluator_output.json",
        "evaluator_output.json",
        "evaluator_report.json",
        "evaluator_results.json",
        "component_evaluator_outputs.json",
        "logger.jsonl",
        "logger.log",
        "raw_run.json",
        "report.md",
        "run_summary.json",
        "testtracker.json",
        "test_tracker.json",
        "test_tracker_output.json",
        "test_tracker_results.json",
        "worker_config.json",
    }
)
FORBIDDEN_BLIND_PATH_COMPONENTS = frozenset(
    {
        "released_label_source",
        "released_evaluator_results",
        "component_evaluator_outputs",
    }
)
BANNED_EVIDENCE_POINTER_BASENAMES = frozenset(
    {
        "artifact_manifest.json",
        "component_evaluator_outputs.json",
        "evaluator_output.json",
        "evaluator_results.json",
        "evidence_index.txt",
        "index.json",
        "native_evaluator_output.json",
        "native_label.json",
        "raw_run.json",
        "released_evaluator_label.json",
        "report.md",
        "run_summary.json",
        "test_tracker.json",
        "test_tracker_output.json",
        "test_tracker_results.json",
        "testtracker.json",
    }
)
BANNED_EVIDENCE_POINTER_PARTS = frozenset(
    {
        "component_evaluator_outputs",
        "evaluation",
        "released_evaluator_results",
        "released_label_source",
    }
)
API_CREDENTIAL_ENV_VARS = (
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENROUTER_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "CODEX_API_KEY",
)
BLIND_CODEX_LOGIN_MARKER_ENV = "NEURIPS_BLIND_CODEX_LOGIN_ISOLATED"
BLIND_OS_USER_ENV = "SCORE_BLIND_OS_USER"
BLIND_FORBIDDEN_ROOTS_ENV = "SCORE_BLIND_FORBIDDEN_ROOTS"


class BlindScoreError(RuntimeError):
    """Raised when a blind score input, model output, or lock is invalid."""


@dataclass(frozen=True)
class RegisteredTestSpec:
    test_id: str
    success_index: int
    fail_index: int


@dataclass(frozen=True)
class StrongerConditionSpec:
    condition_id: str
    index: int


@dataclass(frozen=True)
class StageRunArtifacts:
    model_output: Path
    stdout: Path
    stderr: Path
    events: Path
    telemetry: Path
    reasoning: Path
    attempt_files: tuple[Path, ...]


@dataclass(frozen=True)
class FrozenStageArtifacts:
    """Stage files held in memory between isolated model invocations."""

    source_prefix_name: str
    files: tuple[tuple[str, bytes], ...]


@dataclass(frozen=True)
class RestrictedIdentity:
    username: str
    uid: int
    groupname: str
    gid: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checklist", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument(
        "--out-prefix",
        type=Path,
        required=True,
        help="Output prefix; blind mode intentionally requires an explicit destination.",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--reasoning-effort",
        default=DEFAULT_REASONING_EFFORT,
        choices=["minimal", "low", "medium", "high", "xhigh", "max"],
    )
    parser.add_argument(
        "--sandbox",
        default="read-only",
        choices=["read-only"],
    )
    parser.add_argument("--service-tier", default=DEFAULT_SERVICE_TIER)
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument("--codex-timeout-seconds", type=int, default=600)
    parser.add_argument(
        "--keep-workspace",
        type=Path,
        default=None,
        help="Optional root under which native/ and stronger/ staged workspaces are kept.",
    )
    return parser.parse_args()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def sha256_tree(root: Path) -> str:
    entries: list[dict[str, str]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        entries.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": legacy.sha256_file(path),
            }
        )
    return sha256_json(entries)


def artifact_binding(
    path: Path,
    *,
    relative_to: Path | None = None,
) -> dict[str, str]:
    resolved = path.resolve()
    display_path = (
        os.path.relpath(resolved, relative_to.resolve())
        if relative_to is not None
        else str(resolved)
    )
    return {
        "path": Path(display_path).as_posix(),
        "sha256": legacy.sha256_file(resolved),
    }


def blind_lock_output_path(out_prefix: Path) -> Path:
    return out_prefix.parent / f"{out_prefix.name}.blind_lock.json"


def stage_score_output_path(out_prefix: Path, stage: str) -> Path:
    return out_prefix.parent / f"{out_prefix.name}.{stage}.blind.json"


def stage_lock_output_path(out_prefix: Path, stage: str) -> Path:
    return out_prefix.parent / f"{out_prefix.name}.{stage}.lock.json"


def stage_model_output_path(out_prefix: Path, stage: str) -> Path:
    return out_prefix.parent / f"{out_prefix.name}.{stage}.model_output.json"


def stage_schema_output_path(out_prefix: Path, stage: str) -> Path:
    return out_prefix.parent / f"{out_prefix.name}.{stage}.output_schema.json"


def _stage_artifact_path(out_prefix: Path, stage: str, suffix: str) -> Path:
    return out_prefix.parent / f"{out_prefix.name}.{stage}.{suffix}"


def freeze_stage_artifacts(out_prefix: Path) -> FrozenStageArtifacts:
    files = tuple(
        (path.name, path.read_bytes())
        for path in sorted(item for item in out_prefix.parent.iterdir() if item.is_file())
    )
    if not files:
        raise BlindScoreError("Isolated model stage produced no auditable artifacts")
    return FrozenStageArtifacts(source_prefix_name=out_prefix.name, files=files)


def materialize_stage_artifacts(
    frozen: FrozenStageArtifacts,
    *,
    out_prefix: Path,
    stage: str,
) -> StageRunArtifacts:
    written: list[Path] = []
    for source_name, content in frozen.files:
        if not source_name.startswith(frozen.source_prefix_name + "."):
            raise BlindScoreError(
                f"Deferred {stage} artifact escaped its prefix: {source_name}"
            )
        target_name = out_prefix.name + source_name[len(frozen.source_prefix_name) :]
        target = out_prefix.parent / target_name
        target.write_bytes(content)
        written.append(target)

    model_output = stage_model_output_path(out_prefix, stage)
    stdout = _stage_artifact_path(out_prefix, stage, "codex.stdout.log")
    stderr = _stage_artifact_path(out_prefix, stage, "codex.stderr.log")
    events = _stage_artifact_path(out_prefix, stage, "codex.events.jsonl")
    telemetry = _stage_artifact_path(out_prefix, stage, "codex.telemetry.json")
    reasoning = _stage_artifact_path(out_prefix, stage, "codex.reasoning.txt")
    required = (model_output, stdout, stderr, events, telemetry, reasoning)
    missing = [path.name for path in required if not path.is_file()]
    if missing:
        raise BlindScoreError(
            f"Deferred {stage} artifacts were incomplete after publication: {missing}"
        )
    attempts = tuple(
        path
        for path in written
        if f".{stage}.attempt_" in path.name and path.is_file()
    )
    return StageRunArtifacts(
        model_output=model_output,
        stdout=stdout,
        stderr=stderr,
        events=events,
        telemetry=telemetry,
        reasoning=reasoning,
        attempt_files=attempts,
    )


def normalize_staged_permissions(workspace_root: Path) -> None:
    """Make copied benchmark inputs readable to the read-only Codex sandbox."""

    workspace_root.chmod(0o555)
    for path in sorted(workspace_root.rglob("*")):
        if path.is_symlink():
            raise BlindScoreError(f"Staged blind workspace contains a symlink: {path}")
        if path.is_dir():
            path.chmod(0o555)
        elif path.is_file():
            path.chmod(0o444)


def validate_staged_readability_canary(workspace_root: Path) -> None:
    expected_files = (
        workspace_root / "checklist.yaml",
        workspace_root / "evidence_index.txt",
        workspace_root / "output_schema.json",
    )
    for path in expected_files:
        if not path.is_file():
            raise BlindScoreError(f"Blind staged-readability canary is missing: {path}")
    for path in (workspace_root, *workspace_root.rglob("*")):
        if path.is_dir():
            mode = stat.S_IMODE(path.stat().st_mode)
            if mode != 0o555:
                raise BlindScoreError(
                    f"Blind staged directory mode is {mode:o}, expected 555: {path}"
                )
        elif path.is_file():
            mode = stat.S_IMODE(path.stat().st_mode)
            if mode != 0o444:
                raise BlindScoreError(
                    f"Blind staged file mode is {mode:o}, expected 444: {path}"
                )
            try:
                with path.open("rb") as handle:
                    handle.read(1)
            except OSError as exc:
                raise BlindScoreError(
                    f"Blind staged-readability canary could not read {path}: {exc}"
                ) from exc


def restore_workspace_permissions_for_cleanup(workspace_root: Path) -> None:
    if not workspace_root.exists():
        return
    workspace_root.chmod(0o755)
    for path in sorted(
        (item for item in workspace_root.rglob("*") if item.is_dir()),
        key=lambda item: len(item.parts),
    ):
        path.chmod(0o755)


def assert_blind_input_layout(evidence_dir: Path) -> None:
    """Reject result-bearing paths without opening or parsing their contents."""

    root = evidence_dir.resolve()
    if root.is_symlink() or not root.is_dir():
        raise BlindScoreError(f"Blind evidence must be a real directory: {evidence_dir}")

    task_native_label = root.parent / "native_label.json"
    if task_native_label.exists():
        raise BlindScoreError(
            "Blind mode forbids native_label.json at the task root; keep the "
            "released label outside the scorer input tree until the blind score is locked"
        )

    violations: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            violations.append(f"symlink:{path.relative_to(root).as_posix()}")
            continue
        relative = path.relative_to(root).as_posix()
        lowered_parts = tuple(part.lower() for part in path.relative_to(root).parts)
        if any(part in FORBIDDEN_BLIND_PATH_COMPONENTS for part in lowered_parts):
            violations.append(relative)
            continue
        lowered_name = path.name.lower()
        if lowered_name in FORBIDDEN_BLIND_FILENAMES:
            violations.append(relative)
            continue
        if re.fullmatch(
            r"(?:appworld_)?test_?tracker(?:_output|_results)?\.json",
            lowered_name,
        ):
            violations.append(relative)

    if violations:
        raise BlindScoreError(
            "Blind evidence contains released-label or component-evaluator-result "
            "paths that could disclose the saved result:\n- " + "\n- ".join(violations)
        )


def verify_codex_login_environment() -> dict[str, Any]:
    leaked = [name for name in API_CREDENTIAL_ENV_VARS if os.environ.get(name)]
    if leaked:
        raise BlindScoreError(
            "Blind scoring requires Codex login state and forbids API/base-url "
            f"credential overrides; found environment variables: {leaked}"
        )
    if os.environ.get(BLIND_CODEX_LOGIN_MARKER_ENV) != "1":
        raise BlindScoreError(
            "Blind scoring requires the batch-issued isolated Codex-login marker"
        )
    codex_home_raw = os.environ.get("CODEX_HOME")
    if not codex_home_raw:
        raise BlindScoreError("Blind scoring requires CODEX_HOME with Codex login auth.json")
    codex_home = Path(codex_home_raw).resolve()
    auth_path = codex_home / "auth.json"
    if auth_path.is_symlink() or not auth_path.is_file():
        raise BlindScoreError(
            f"Blind scoring requires a regular Codex login auth.json under {codex_home}"
        )
    return {
        "mode": "codex_login",
        "isolated_codex_home": True,
        "auth_json_present": True,
        "api_credential_environment_present": False,
        "batch_login_marker_verified": True,
    }


def resolve_restricted_identity() -> RestrictedIdentity:
    if os.geteuid() != 0:
        raise BlindScoreError("Blind scorer orchestration must run as root")
    username = str(os.environ.get(BLIND_OS_USER_ENV) or "").strip()
    if not username:
        raise BlindScoreError(f"{BLIND_OS_USER_ENV} must name a dedicated blind OS user")
    if username in {"root", "draftsvc"}:
        raise BlindScoreError(
            f"{BLIND_OS_USER_ENV} must not be the privileged or draft service user"
        )
    try:
        entry = pwd.getpwnam(username)
        groupname = grp.getgrgid(entry.pw_gid).gr_name
    except KeyError as exc:
        raise BlindScoreError(f"Unknown blind OS user or primary group: {username}") from exc
    if entry.pw_uid == 0:
        raise BlindScoreError("Dedicated blind OS user must have a non-root uid")
    return RestrictedIdentity(
        username=username,
        uid=entry.pw_uid,
        groupname=groupname,
        gid=entry.pw_gid,
    )


def assert_restricted_user_cannot_read_original_roots(
    identity: RestrictedIdentity,
) -> dict[str, Any]:
    raw = str(os.environ.get(BLIND_FORBIDDEN_ROOTS_ENV) or "").strip()
    roots = [Path(item).resolve() for item in raw.split(os.pathsep) if item.strip()]
    if not roots:
        raise BlindScoreError(
            f"{BLIND_FORBIDDEN_ROOTS_ENV} must bind the original job/results/state roots"
        )
    test_binary = shutil.which("test") or "/usr/bin/test"
    for root in roots:
        for flag in ("-r", "-x"):
            result = subprocess.run(
                [test_binary, flag, str(root)],
                check=False,
                capture_output=True,
                env={"PATH": os.environ.get("PATH", "/usr/bin:/bin")},
                user=identity.uid,
                group=identity.gid,
                extra_groups=(),
            )
            if result.returncode == 0:
                raise BlindScoreError(
                    f"Restricted blind user can access forbidden original root: {root}"
                )
    return {
        "restricted_os_user": identity.username,
        "restricted_uid": identity.uid,
        "restricted_group": identity.groupname,
        "restricted_gid": identity.gid,
        "forbidden_root_canary_count": len(roots),
        "forbidden_root_canary_passed": True,
    }


def prepare_restricted_stage_runtime(
    *,
    workspace_root: Path,
    identity: RestrictedIdentity,
) -> tuple[Path, Path, Path]:
    source_codex_home = Path(str(os.environ["CODEX_HOME"])).resolve()
    source_auth = source_codex_home / "auth.json"
    output_dir = workspace_root / ".model_output"
    stage_codex_home = workspace_root / ".codex_home"
    stage_tmp = workspace_root / ".tmp"
    for directory in (output_dir, stage_codex_home, stage_tmp):
        directory.mkdir(mode=0o700, exist_ok=False)
        os.chown(directory, identity.uid, identity.gid)
        directory.chmod(0o700)
    stage_auth = stage_codex_home / "auth.json"
    shutil.copyfile(source_auth, stage_auth)
    os.chown(stage_auth, identity.uid, identity.gid)
    stage_auth.chmod(0o600)
    return output_dir / "model_output.json", stage_codex_home, stage_tmp


def run_codex_restricted(
    *,
    identity: RestrictedIdentity,
    workspace_root: Path,
    schema_path: Path,
    prompt: str,
    model: str,
    reasoning_effort: str,
    service_tier: str,
    sandbox: str,
    out_json_path: Path,
    stage_codex_home: Path,
    stage_tmp: Path,
    codex_timeout_seconds: int,
) -> legacy.CodexRunResult:
    codex_path = shutil.which("codex")
    if codex_path is None:
        raise BlindScoreError("Could not find codex on PATH")
    command = [
        codex_path,
        "exec",
        "--cd",
        str(workspace_root),
        "--skip-git-repo-check",
        "--ephemeral",
        "--ignore-user-config",
        "--sandbox",
        sandbox,
        "--model",
        model,
        "-c",
        f'model_reasoning_effort="{reasoning_effort}"',
        "-c",
        'model_verbosity="low"',
        "-c",
        f'service_tier="{service_tier}"',
        "--color",
        "never",
        "--json",
        "--output-schema",
        str(schema_path),
        "-o",
        str(out_json_path),
        prompt,
    ]
    child_env = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "HOME": str(stage_codex_home),
        "CODEX_HOME": str(stage_codex_home),
        "TMPDIR": str(stage_tmp),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "TERM": "dumb",
    }
    for name in ("SSL_CERT_FILE", "SSL_CERT_DIR", "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY"):
        if os.environ.get(name):
            child_env[name] = str(os.environ[name])
    try:
        completed = subprocess.run(
            command,
            cwd=str(workspace_root),
            env=child_env,
            capture_output=True,
            text=True,
            check=False,
            timeout=codex_timeout_seconds,
            user=identity.uid,
            group=identity.gid,
            extra_groups=(),
        )
        return legacy.CodexRunResult(
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            timed_out=False,
            timeout_seconds=codex_timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return legacy.CodexRunResult(
            returncode=124,
            stdout=legacy.subprocess_output_text(exc.stdout),
            stderr=legacy.subprocess_output_text(exc.stderr),
            timed_out=True,
            timeout_seconds=codex_timeout_seconds,
        )


def assert_frozen_inputs_unchanged(
    *,
    checklist_path: Path,
    checklist_sha256: str,
    evidence_dir: Path,
    evidence_tree_sha256: str,
) -> None:
    if legacy.sha256_file(checklist_path) != checklist_sha256:
        raise BlindScoreError("Checklist changed during blind scoring")
    if sha256_tree(evidence_dir) != evidence_tree_sha256:
        raise BlindScoreError("Evidence tree changed during blind scoring")


def _one_test_marker(rule: Any, *, field: str) -> str:
    if not isinstance(rule, dict):
        raise BlindScoreError(f"{field} must be an object")
    markers = APPWORLD_TEST_MARKER_RE.findall(str(rule.get("text") or ""))
    if len(markers) != 1:
        raise BlindScoreError(
            f"{field} must contain exactly one [appworld_test_*] marker; found {markers}"
        )
    return markers[0]


def extract_registered_test_specs(checklist: dict[str, Any]) -> list[RegisteredTestSpec]:
    if str(checklist.get("domain") or "").strip().lower() != "appworld":
        raise BlindScoreError("Blind system-design-v3 scoring currently requires domain=appworld")
    native = checklist.get("native")
    if not isinstance(native, dict):
        raise BlindScoreError("Checklist native section is missing")
    success_rules = native.get("success_if")
    fail_rules = native.get("fail_if")
    if not isinstance(success_rules, list) or not success_rules:
        raise BlindScoreError("Checklist native.success_if must be a non-empty list")
    if not isinstance(fail_rules, list) or not fail_rules:
        raise BlindScoreError("Checklist native.fail_if must be a non-empty list")

    success_ids = [
        _one_test_marker(rule, field=f"native.success_if[{index}]")
        for index, rule in enumerate(success_rules)
    ]
    fail_ids = [
        _one_test_marker(rule, field=f"native.fail_if[{index}]")
        for index, rule in enumerate(fail_rules)
    ]
    if success_ids != fail_ids:
        raise BlindScoreError(
            "native.success_if and native.fail_if AppWorld test ids must match "
            f"one-for-one in checklist order: {success_ids} != {fail_ids}"
        )
    if len(success_ids) != len(set(success_ids)):
        raise BlindScoreError("AppWorld registered-test ids must be unique")
    return [
        RegisteredTestSpec(test_id=test_id, success_index=index, fail_index=index)
        for index, test_id in enumerate(success_ids)
    ]


def extract_stronger_condition_specs(
    checklist: dict[str, Any],
) -> list[StrongerConditionSpec]:
    stronger = checklist.get("stronger")
    if not isinstance(stronger, dict):
        raise BlindScoreError("Checklist stronger section is missing")
    conditions = stronger.get("additional_conditions")
    if not isinstance(conditions, list):
        raise BlindScoreError("stronger.additional_conditions must be a list")
    ids: list[str] = []
    for index, condition in enumerate(conditions):
        if not isinstance(condition, dict):
            raise BlindScoreError(
                f"stronger.additional_conditions[{index}] must be an object"
            )
        condition_id = str(condition.get("id") or "").strip()
        if not condition_id:
            raise BlindScoreError(
                f"stronger.additional_conditions[{index}] has no non-empty id"
            )
        ids.append(condition_id)
    if len(ids) != len(set(ids)):
        raise BlindScoreError("stronger.additional_conditions ids must be unique")
    return [
        StrongerConditionSpec(condition_id=condition_id, index=index)
        for index, condition_id in enumerate(ids)
    ]


def _check_item_schema(ids: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "status", "reason", "pointers"],
        "properties": {
            "id": {"type": "string", "enum": ids},
            "status": {"type": "string", "enum": list(CHECK_STATUSES)},
            "reason": {"type": "string", "minLength": 1},
            "pointers": {
                "type": "array",
                "minItems": 2,
                "items": {"type": "string", "minLength": 1},
            },
        },
    }


def build_native_model_schema(
    specs: list[RegisteredTestSpec],
) -> dict[str, Any]:
    ids = [spec.test_id for spec in specs]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["test_checks"],
        "properties": {
            "test_checks": {
                "type": "array",
                "minItems": len(ids),
                "maxItems": len(ids),
                "items": _check_item_schema(ids),
            }
        },
    }


def build_stronger_model_schema(
    specs: list[StrongerConditionSpec],
) -> dict[str, Any]:
    ids = [spec.condition_id for spec in specs]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["condition_checks"],
        "properties": {
            "condition_checks": {
                "type": "array",
                "minItems": len(ids),
                "maxItems": len(ids),
                "items": _check_item_schema(ids),
            }
        },
    }


def _validate_check_pointers(
    *,
    check: dict[str, Any],
    expected_rule: str,
    checklist: dict[str, Any],
    workspace_root: Path,
    field: str,
) -> None:
    pointers = check.get("pointers")
    if not isinstance(pointers, list):
        raise BlindScoreError(f"{field}.pointers must be a list")
    normalized = []
    for pointer in pointers:
        value = str(pointer).strip().replace("\\", "/")
        if value.startswith("checklist.yaml::$."):
            value = "checklist.yaml::" + value.removeprefix("checklist.yaml::$.")
        elif value.startswith("checklist.yaml::$["):
            value = "checklist.yaml::[" + value.removeprefix("checklist.yaml::$[")
        normalized.append(value)
    if expected_rule.endswith("["):
        has_rule = any(pointer.startswith(expected_rule) for pointer in normalized)
    else:
        has_rule = expected_rule in normalized
    if not has_rule:
        raise BlindScoreError(f"{field}.pointers must cite {expected_rule}")

    cache: dict[Path, Any] = {}
    has_evidence_pointer = False
    has_run_evidence_pointer = False
    for pointer in pointers:
        if legacy.pointer_uses_summary_only_native_field(str(pointer)):
            raise BlindScoreError(
                f"{field}.pointers cites a summary-only label/score field: {pointer}"
            )
        pointer_text = str(pointer).strip().replace("\\", "/")
        relative, separator, location = pointer_text.partition("::")
        if separator != "::" or not relative or not location:
            raise BlindScoreError(
                f"{field}.pointers contains an invalid pointer (bad_pointer_format): "
                f"{pointer}"
            )
        relative_path = PurePosixPath(relative)
        relative_parts = relative_path.parts
        if (
            not relative_parts
            or relative_path.is_absolute()
            or relative_path.as_posix() != relative
            or any(part in {"", ".", ".."} for part in relative_parts)
        ):
            raise BlindScoreError(
                f"{field}.pointers contains a non-canonical path: {pointer}"
            )
        if relative_parts[-1].casefold() in BANNED_EVIDENCE_POINTER_BASENAMES or any(
            part.casefold() in BANNED_EVIDENCE_POINTER_PARTS
            for part in relative_parts
        ):
            raise BlindScoreError(
                f"{field}.pointers cites a forbidden result/helper artifact: {pointer}"
            )
        if relative != "checklist.yaml" and not relative.startswith("evidence/"):
            raise BlindScoreError(
                f"{field}.pointers escaped blind scorer inputs: {pointer}"
            )
        if relative.startswith("evidence/"):
            has_evidence_pointer = True
        if relative.startswith("evidence/run/"):
            has_run_evidence_pointer = True
        # Frozen AppWorld source pointers use ordinary JSONPath roots (`$` /
        # `$.field`), L-prefixed line spans (`L21`), and Python symbols
        # (`evaluation.py::evaluate`).  The legacy resolver predates those
        # official pointer spellings, so normalize or validate them here rather
        # than forcing the model to invent a different citation syntax.
        legacy_pointer = pointer_text
        if location == "$" and relative.startswith("evidence/"):
            resolved_path = (workspace_root / relative).resolve()
            workspace = workspace_root.resolve()
            if workspace not in resolved_path.parents or not resolved_path.is_file():
                raise BlindScoreError(
                    f"{field}.pointers contains an invalid pointer (missing_file): "
                    f"{pointer} -> {resolved_path}"
                )
            try:
                if resolved_path.suffix == ".json":
                    json.loads(resolved_path.read_text(encoding="utf-8"))
                elif resolved_path.suffix in {".yaml", ".yml"}:
                    legacy.load_yaml(resolved_path)
                else:
                    raise BlindScoreError(
                        f"{field}.pointers uses JSONPath root on a non-structured "
                        f"file: {pointer}"
                    )
            except (OSError, json.JSONDecodeError, legacy.CodexScoreError) as exc:
                raise BlindScoreError(
                    f"{field}.pointers contains an invalid structured-root pointer: "
                    f"{pointer}: {exc}"
                ) from exc
            continue
        if location.startswith("$."):
            legacy_pointer = f"{relative}::{location[2:]}"
        elif location.startswith("$["):
            legacy_pointer = f"{relative}::{location[1:]}"
        else:
            line_match = re.fullmatch(
                r"L(?P<start>\d+)(?:-L?(?P<end>\d+))?",
                location,
                flags=re.IGNORECASE,
            )
            if line_match is not None:
                start = line_match.group("start")
                end = line_match.group("end") or start
                legacy_pointer = f"{relative}::{start}-{end}"

        if relative.startswith("evidence/") and relative.endswith(".py"):
            symbol = location.split(".")[-1]
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", symbol):
                resolved_path = (workspace_root / relative).resolve()
                workspace = workspace_root.resolve()
                if workspace not in resolved_path.parents or not resolved_path.is_file():
                    raise BlindScoreError(
                        f"{field}.pointers contains an invalid pointer (missing_file): "
                        f"{pointer} -> {resolved_path}"
                    )
                source = resolved_path.read_text(encoding="utf-8", errors="replace")
                declaration = re.compile(
                    rf"(?:^|\n)\s*(?:async\s+def|def|class)\s+{re.escape(symbol)}\b"
                )
                if declaration.search(source) is None:
                    raise BlindScoreError(
                        f"{field}.pointers contains an unresolved Python symbol: "
                        f"{pointer}"
                    )
                continue

        ok, _, status, resolved_path, _ = legacy._resolve_pointer_reference(
            pointer=legacy_pointer,
            checklist=checklist,
            workspace_root=workspace_root,
            doc_cache=cache,
        )
        if not ok:
            detail = f" -> {resolved_path}" if resolved_path is not None else ""
            raise BlindScoreError(
                f"{field}.pointers contains an invalid pointer ({status}): {pointer}{detail}"
            )
    if not has_evidence_pointer:
        raise BlindScoreError(f"{field}.pointers must cite retained evidence")
    if not has_run_evidence_pointer:
        raise BlindScoreError(
            f"{field}.pointers must cite post-run execution evidence under evidence/run/"
        )


def validate_native_model_output(
    payload: dict[str, Any],
    *,
    specs: list[RegisteredTestSpec],
    checklist: dict[str, Any],
    workspace_root: Path,
) -> None:
    checks = payload.get("test_checks")
    if not isinstance(checks, list):
        raise BlindScoreError("Native model output has no test_checks list")
    actual_ids = [check.get("id") if isinstance(check, dict) else None for check in checks]
    expected_ids = [spec.test_id for spec in specs]
    if actual_ids != expected_ids:
        raise BlindScoreError(
            f"native.test_checks ids/order differ from checklist: {actual_ids} != {expected_ids}"
        )
    for index, (spec, check) in enumerate(zip(specs, checks, strict=True)):
        status = str(check["status"])
        if status == "supported":
            expected_rule = f"checklist.yaml::native.success_if[{spec.success_index}]"
        elif status == "contradicted":
            expected_rule = f"checklist.yaml::native.fail_if[{spec.fail_index}]"
        else:
            expected_rule = "checklist.yaml::native.undecided_if["
        _validate_check_pointers(
            check=check,
            expected_rule=expected_rule,
            checklist=checklist,
            workspace_root=workspace_root,
            field=f"native.test_checks[{index}]",
        )


def validate_stronger_model_output(
    payload: dict[str, Any],
    *,
    specs: list[StrongerConditionSpec],
    checklist: dict[str, Any],
    workspace_root: Path,
) -> None:
    checks = payload.get("condition_checks")
    if not isinstance(checks, list):
        raise BlindScoreError("Stronger model output has no condition_checks list")
    actual_ids = [check.get("id") if isinstance(check, dict) else None for check in checks]
    expected_ids = [spec.condition_id for spec in specs]
    if actual_ids != expected_ids:
        raise BlindScoreError(
            "stronger.condition_checks ids/order differ from checklist: "
            f"{actual_ids} != {expected_ids}"
        )
    for index, (spec, check) in enumerate(zip(specs, checks, strict=True)):
        _validate_check_pointers(
            check=check,
            expected_rule=(
                f"checklist.yaml::stronger.additional_conditions[{spec.index}]"
            ),
            checklist=checklist,
            workspace_root=workspace_root,
            field=f"stronger.condition_checks[{index}]",
        )


def _schema_error_message(errors: list[Any]) -> str:
    lines = ["Model output failed the stage schema:"]
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        lines.append(f"- {location}: {error.message}")
    return "\n".join(lines)


def _attempt_artifact_paths(
    out_prefix: Path, stage: str, attempt: int
) -> dict[str, Path]:
    base = f"{out_prefix.name}.{stage}.attempt_{attempt:02d}"
    return {
        "stdout": out_prefix.parent / f"{base}.codex.stdout.log",
        "stderr": out_prefix.parent / f"{base}.codex.stderr.log",
        "events": out_prefix.parent / f"{base}.codex.events.jsonl",
        "telemetry": out_prefix.parent / f"{base}.codex.telemetry.json",
        "reasoning": out_prefix.parent / f"{base}.codex.reasoning.txt",
        "model_output": out_prefix.parent / f"{base}.model_output.json",
    }


def run_model_stage(
    *,
    stage: str,
    prompt_path: Path,
    model_schema: dict[str, Any],
    checklist_path: Path,
    checklist: dict[str, Any],
    evidence_dir: Path,
    out_prefix: Path,
    restricted_identity: RestrictedIdentity,
    model: str,
    reasoning_effort: str,
    service_tier: str,
    sandbox: str,
    max_attempts: int,
    codex_timeout_seconds: int,
    validate_payload: Callable[[dict[str, Any], Path], None],
    keep_workspace: Path | None = None,
) -> tuple[dict[str, Any], StageRunArtifacts]:
    prompt_text = legacy.load_text(prompt_path)
    schema_archive = stage_schema_output_path(out_prefix, stage)
    legacy.write_json(schema_archive, model_schema)
    model_output = stage_model_output_path(out_prefix, stage)
    stdout_path = _stage_artifact_path(out_prefix, stage, "codex.stdout.log")
    stderr_path = _stage_artifact_path(out_prefix, stage, "codex.stderr.log")
    events_path = _stage_artifact_path(out_prefix, stage, "codex.events.jsonl")
    telemetry_path = _stage_artifact_path(out_prefix, stage, "codex.telemetry.json")
    reasoning_path = _stage_artifact_path(out_prefix, stage, "codex.reasoning.txt")
    attempt_files: list[Path] = []

    temp_context: tempfile.TemporaryDirectory[str] | None = None
    if keep_workspace is None:
        temp_context = tempfile.TemporaryDirectory(prefix=f"codex_blind_{stage}_")
        workspace_root = Path(temp_context.name)
    else:
        workspace_root = (keep_workspace / stage).resolve()
        if workspace_root.exists():
            shutil.rmtree(workspace_root)
        workspace_root.mkdir(parents=True, exist_ok=False)

    legacy.stage_workspace(
        checklist_path=checklist_path,
        evidence_dir=evidence_dir,
        workspace_root=workspace_root,
    )
    schema_path = workspace_root / "output_schema.json"
    legacy.write_json(schema_path, model_schema)
    normalize_staged_permissions(workspace_root)
    validate_staged_readability_canary(workspace_root)
    restricted_output_path, stage_codex_home, stage_tmp = (
        prepare_restricted_stage_runtime(
            workspace_root=workspace_root,
            identity=restricted_identity,
        )
    )
    prompt = legacy.build_prompt(prompt_text)
    validator = Draft202012Validator(model_schema)
    retry_note = ""

    try:
        for attempt in range(1, max_attempts + 1):
            if model_output.exists():
                model_output.unlink()
            if restricted_output_path.exists():
                restricted_output_path.unlink()
            attempt_prompt = prompt
            if retry_note:
                attempt_prompt = (
                    prompt.rstrip()
                    + "\n\nRetry correction:\n"
                    + retry_note.rstrip()
                    + "\nReturn a complete corrected JSON object only.\n"
                )
            result = run_codex_restricted(
                identity=restricted_identity,
                workspace_root=workspace_root,
                schema_path=schema_path,
                prompt=attempt_prompt,
                model=model,
                reasoning_effort=reasoning_effort,
                service_tier=service_tier,
                sandbox=sandbox,
                out_json_path=restricted_output_path,
                stage_codex_home=stage_codex_home,
                stage_tmp=stage_tmp,
                codex_timeout_seconds=codex_timeout_seconds,
            )
            if restricted_output_path.is_file():
                shutil.copyfile(restricted_output_path, model_output)

            paths = _attempt_artifact_paths(out_prefix, stage, attempt)
            legacy.write_text(stdout_path, result.stdout)
            legacy.write_text(stderr_path, result.stderr)
            legacy.write_text(events_path, result.stdout)
            legacy.write_text(paths["stdout"], result.stdout)
            legacy.write_text(paths["stderr"], result.stderr)
            legacy.write_text(paths["events"], result.stdout)
            attempt_files.extend(paths.values())

            events, malformed = legacy.load_jsonl_objects(result.stdout)
            telemetry = legacy.build_codex_telemetry(
                events=events,
                malformed_lines=malformed,
            )
            telemetry["stage"] = stage
            telemetry["attempt"] = attempt
            telemetry["codex_exit"] = {
                "returncode": result.returncode,
                "timed_out": result.timed_out,
                "timeout_seconds": result.timeout_seconds,
            }
            legacy.write_json(telemetry_path, telemetry)
            legacy.write_json(paths["telemetry"], telemetry)
            reasoning = (
                str(((telemetry.get("reasoning") or {}).get("summary_text") or "")).rstrip()
                + "\n"
            )
            legacy.write_text(reasoning_path, reasoning)
            legacy.write_text(paths["reasoning"], reasoning)

            if not model_output.exists():
                recovered = legacy.recover_json_output_from_events(events)
                if recovered is not None:
                    legacy.write_json(model_output, recovered)
            if model_output.exists():
                shutil.copy2(model_output, paths["model_output"])

            if result.timed_out:
                retry_note = "The prior attempt timed out; return the required JSON directly."
            elif result.returncode != 0:
                retry_note = (
                    f"The prior attempt exited with status {result.returncode}; "
                    "return the required JSON directly."
                )
            elif not model_output.exists():
                retry_note = "The prior attempt produced no JSON output."
            else:
                try:
                    payload = legacy.load_json(model_output)
                    errors = sorted(
                        validator.iter_errors(payload),
                        key=lambda error: list(error.absolute_path),
                    )
                    if errors:
                        raise BlindScoreError(_schema_error_message(errors))
                    validate_payload(payload, workspace_root)
                    legacy.write_json(model_output, payload)
                    return payload, StageRunArtifacts(
                        model_output=model_output,
                        stdout=stdout_path,
                        stderr=stderr_path,
                        events=events_path,
                        telemetry=telemetry_path,
                        reasoning=reasoning_path,
                        attempt_files=tuple(
                            path for path in attempt_files if path.is_file()
                        ),
                    )
                except (BlindScoreError, legacy.CodexScoreError) as exc:
                    retry_note = str(exc)

            if attempt == max_attempts:
                raise BlindScoreError(
                    f"{stage} blind scoring failed after {max_attempts} attempts: "
                    f"{retry_note}"
                )
    finally:
        restore_workspace_permissions_for_cleanup(workspace_root)
        if temp_context is not None:
            temp_context.cleanup()

    raise BlindScoreError(f"{stage} blind scoring did not produce a valid result")


def _dedupe_pointers(checks: list[dict[str, Any]]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for check in checks:
        for pointer in check["pointers"]:
            value = str(pointer)
            if value not in seen:
                seen.add(value)
                result.append(value)
    return result


def derive_native_result(test_checks: list[dict[str, Any]]) -> dict[str, Any]:
    if not test_checks:
        raise BlindScoreError("Native aggregation requires at least one registered test")
    contradicted = [check for check in test_checks if check["status"] == "contradicted"]
    undecided = [check for check in test_checks if check["status"] == "undecided"]
    if contradicted:
        verdict = "F"
        decisive = contradicted
        reason = (
            "At least one locked AppWorld registered test is contradicted by retained "
            "evidence: " + ", ".join(check["id"] for check in contradicted) + "."
        )
    elif undecided:
        verdict = "U"
        decisive = undecided
        reason = (
            "No registered test is contradicted, but retained evidence leaves these "
            "locked tests undecided: "
            + ", ".join(check["id"] for check in undecided)
            + "."
        )
    else:
        verdict = "S"
        decisive = test_checks
        reason = "Retained evidence supports every locked AppWorld registered test."
    return {
        "verdict": verdict,
        "reason": reason,
        "pointers": _dedupe_pointers(decisive),
        "test_checks": test_checks,
    }


def derive_stronger_result(
    condition_checks: list[dict[str, Any]],
) -> dict[str, Any]:
    if not condition_checks:
        return {
            "verdict": "NA",
            "reason": "The locked checklist has no stronger-measurement conditions.",
            "pointers": ["checklist.yaml::stronger.additional_conditions"],
            "condition_checks": [],
        }
    contradicted = [
        check for check in condition_checks if check["status"] == "contradicted"
    ]
    undecided = [check for check in condition_checks if check["status"] == "undecided"]
    if contradicted:
        verdict = "F"
        decisive = contradicted
        reason = (
            "At least one independent stronger condition is contradicted: "
            + ", ".join(check["id"] for check in contradicted)
            + "."
        )
    elif undecided:
        verdict = "U"
        decisive = undecided
        reason = (
            "No stronger condition is contradicted, but these conditions remain "
            "undecided: "
            + ", ".join(check["id"] for check in undecided)
            + "."
        )
    else:
        verdict = "S"
        decisive = condition_checks
        reason = "Retained evidence supports every independent stronger condition."
    return {
        "verdict": verdict,
        "reason": reason,
        "pointers": _dedupe_pointers(decisive),
        "condition_checks": condition_checks,
    }


def build_stage_lock(
    *,
    stage: str,
    stage_score_path: Path,
    checklist_path: Path,
    evidence_dir: Path,
    evidence_tree_sha256: str,
    prompt_path: Path,
    schema_path: Path,
    model: str,
    reasoning_effort: str,
    service_tier: str,
    restricted_identity: RestrictedIdentity,
) -> dict[str, Any]:
    score_dir = stage_score_path.parent.resolve()
    return {
        "schema_version": "blind_score_stage_lock_v1",
        "stage": stage,
        "locked_at": utc_now_iso(),
        "outcome_blind": True,
        "released_evaluator_label_resolved": False,
        "component_evaluator_outputs_allowed": False,
        "stage_score": artifact_binding(stage_score_path, relative_to=score_dir),
        "checklist": artifact_binding(checklist_path, relative_to=score_dir),
        "evidence": {
            "path": Path(os.path.relpath(evidence_dir.resolve(), score_dir)).as_posix(),
            "tree_sha256": evidence_tree_sha256,
        },
        "prompt": artifact_binding(prompt_path, relative_to=score_dir),
        "model_output_schema": artifact_binding(schema_path, relative_to=score_dir),
        "model": model,
        "reasoning_effort": reasoning_effort,
        "service_tier": service_tier,
        "fast_mode": service_tier.strip().lower() == "fast",
        "auth_mode": "codex_login",
        "restricted_os_user": restricted_identity.username,
        "restricted_uid": restricted_identity.uid,
        "restricted_gid": restricted_identity.gid,
    }


def _stage_artifact_bindings(
    artifacts: StageRunArtifacts | None,
    *,
    score_dir: Path,
) -> dict[str, Any]:
    if artifacts is None:
        return {"model_invoked": False, "attempt_files": []}
    return {
        "model_invoked": True,
        "model_output": artifact_binding(artifacts.model_output, relative_to=score_dir),
        "stdout": artifact_binding(artifacts.stdout, relative_to=score_dir),
        "stderr": artifact_binding(artifacts.stderr, relative_to=score_dir),
        "events": artifact_binding(artifacts.events, relative_to=score_dir),
        "telemetry": artifact_binding(artifacts.telemetry, relative_to=score_dir),
        "reasoning": artifact_binding(artifacts.reasoning, relative_to=score_dir),
        "attempt_files": [
            artifact_binding(path, relative_to=score_dir)
            for path in artifacts.attempt_files
        ],
    }


def infer_agent_id(score_task_id: str) -> str | None:
    match = re.search(r"(?:^|__|-)(agent_[A-Za-z0-9]+)$", score_task_id)
    return match.group(1) if match is not None else None


def build_manifest(
    *,
    out_prefix: Path,
    checklist_path: Path,
    checklist: dict[str, Any],
    evidence_dir: Path,
    evidence_tree_sha256: str,
    model: str,
    reasoning_effort: str,
    service_tier: str,
    auth_receipt: dict[str, Any],
    native_schema_path: Path,
    stronger_schema_path: Path,
    native_score_path: Path,
    stronger_score_path: Path,
    native_lock_path: Path,
    stronger_lock_path: Path,
    blind_lock_path: Path,
    native_artifacts: StageRunArtifacts,
    stronger_artifacts: StageRunArtifacts | None,
) -> dict[str, Any]:
    score_json = out_prefix.with_suffix(".json")
    score_yaml = out_prefix.with_suffix(".yaml")
    score_dir = out_prefix.parent.resolve()
    score_task_id = out_prefix.parent.name
    return {
        "schema_version": "blind_score_manifest_v1",
        "scored_at": utc_now_iso(),
        "case_unit_id": checklist.get("case_unit_id"),
        "task_id": checklist.get("task_id"),
        "score_task_id": score_task_id,
        "agent_id": infer_agent_id(score_task_id),
        "blind_mode": True,
        "released_label_handling": {
            "required_by_scorer": False,
            "resolved_before_or_during_scoring": False,
            "included_in_model_workspaces": False,
            "included_in_score": False,
            "comparison_stage": "external_after_blind_score_lock",
        },
        "model_stage_isolation": {
            "invocation_order": ["stronger", "native"],
            "separate_temporary_workspaces": True,
            "temporary_stage_outputs_deleted_before_next_invocation": True,
            "final_score_directory_empty_during_model_invocations": True,
            "all_stage_artifacts_published_after_all_model_invocations": True,
            "stronger_received_native_output": False,
            "native_received_stronger_output": False,
        },
        "aggregation_rules": {
            "native": "all supported -> S; any contradicted -> F; otherwise U",
            "stronger": (
                "no conditions -> NA; all supported -> S; any contradicted -> F; "
                "otherwise U"
            ),
            "stronger_independent_of_native": True,
        },
        "model": model,
        "reasoning_effort": reasoning_effort,
        "service_tier": service_tier,
        "fast_mode": service_tier.strip().lower() == "fast",
        "auth": auth_receipt,
        "checklist": artifact_binding(checklist_path, relative_to=score_dir),
        "evidence": {
            "path": Path(os.path.relpath(evidence_dir.resolve(), score_dir)).as_posix(),
            "tree_sha256": evidence_tree_sha256,
        },
        "prompts": {
            "native": artifact_binding(NATIVE_PROMPT_PATH, relative_to=score_dir),
            "stronger": artifact_binding(STRONGER_PROMPT_PATH, relative_to=score_dir),
        },
        "schemas": {
            "native_model_output": artifact_binding(
                native_schema_path, relative_to=score_dir
            ),
            "stronger_model_output": artifact_binding(
                stronger_schema_path, relative_to=score_dir
            ),
            "final_blind_score": artifact_binding(
                FINAL_SCHEMA_PATH, relative_to=score_dir
            ),
        },
        "stages": {
            "native": {
                "score": artifact_binding(native_score_path, relative_to=score_dir),
                "lock": artifact_binding(native_lock_path, relative_to=score_dir),
                **_stage_artifact_bindings(native_artifacts, score_dir=score_dir),
            },
            "stronger": {
                "score": artifact_binding(stronger_score_path, relative_to=score_dir),
                "lock": artifact_binding(stronger_lock_path, relative_to=score_dir),
                **_stage_artifact_bindings(stronger_artifacts, score_dir=score_dir),
            },
        },
        "outputs": {
            "json": artifact_binding(score_json, relative_to=score_dir),
            "yaml": artifact_binding(score_yaml, relative_to=score_dir),
            "blind_lock": artifact_binding(blind_lock_path, relative_to=score_dir),
            "manifest": legacy.manifest_output_path(out_prefix).name,
        },
    }


def validate_final_score(
    score: dict[str, Any],
    *,
    checklist: dict[str, Any],
    native_specs: list[RegisteredTestSpec],
    stronger_specs: list[StrongerConditionSpec],
) -> None:
    schema = legacy.load_json(FINAL_SCHEMA_PATH)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(score),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise BlindScoreError(_schema_error_message(errors))
    if score["case_unit_id"] != checklist.get("case_unit_id"):
        raise BlindScoreError("Final blind score case_unit_id differs from checklist")
    native_ids = [check["id"] for check in score["native"]["test_checks"]]
    expected_native_ids = [spec.test_id for spec in native_specs]
    if native_ids != expected_native_ids:
        raise BlindScoreError("Final native test ids/order differ from checklist")
    stronger_ids = [check["id"] for check in score["stronger"]["condition_checks"]]
    expected_stronger_ids = [spec.condition_id for spec in stronger_specs]
    if stronger_ids != expected_stronger_ids:
        raise BlindScoreError("Final stronger condition ids/order differ from checklist")
    if score["native"]["verdict"] != derive_native_result(
        score["native"]["test_checks"]
    )["verdict"]:
        raise BlindScoreError("Final native aggregate is not derived from native.test_checks")
    if score["stronger"]["verdict"] != derive_stronger_result(
        score["stronger"]["condition_checks"]
    )["verdict"]:
        raise BlindScoreError(
            "Final stronger aggregate is not derived from stronger.condition_checks"
        )
    serialized_keys = set()

    def collect_keys(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                serialized_keys.add(str(key).lower())
                collect_keys(child)
        elif isinstance(value, list):
            for child in value:
                collect_keys(child)

    collect_keys(score)
    forbidden_keys = {
        "released_evaluator_label",
        "native_label",
        "released_label",
        "component_evaluator_outputs",
    }
    leaked_keys = sorted(serialized_keys & forbidden_keys)
    if leaked_keys:
        raise BlindScoreError(
            f"Final blind score contains forbidden released-result keys: {leaked_keys}"
        )


def main() -> int:
    args = parse_args()
    if args.max_attempts < 1:
        raise BlindScoreError("--max-attempts must be at least 1")
    if args.codex_timeout_seconds < 1:
        raise BlindScoreError("--codex-timeout-seconds must be at least 1")
    if args.service_tier.strip().lower() == "fast":
        raise BlindScoreError("Blind system-design-v3 scoring forbids fast mode")
    if args.keep_workspace is not None:
        raise BlindScoreError(
            "--keep-workspace is forbidden in blind mode because retained stage "
            "workspaces could leak one model stage to the other"
        )

    checklist_path = args.checklist.resolve()
    evidence_dir = args.evidence_dir.resolve()
    out_prefix = args.out_prefix.resolve()
    for path, label in (
        (checklist_path, "Checklist"),
        (evidence_dir, "Evidence directory"),
        (NATIVE_PROMPT_PATH, "Native blind prompt"),
        (STRONGER_PROMPT_PATH, "Stronger blind prompt"),
        (FINAL_SCHEMA_PATH, "Final blind score schema"),
    ):
        legacy.ensure_exists(path, label)
    assert_blind_input_layout(evidence_dir)

    checklist = legacy.load_yaml(checklist_path)
    native_specs = extract_registered_test_specs(checklist)
    stronger_specs = extract_stronger_condition_specs(checklist)
    auth_receipt = verify_codex_login_environment()
    restricted_identity = resolve_restricted_identity()
    auth_receipt.update(
        assert_restricted_user_cannot_read_original_roots(restricted_identity)
    )
    checklist_sha256 = legacy.sha256_file(checklist_path)
    evidence_tree_sha256 = sha256_tree(evidence_dir)
    if out_prefix.parent.exists():
        if not out_prefix.parent.is_dir() or any(out_prefix.parent.iterdir()):
            raise BlindScoreError(
                "Blind score output directory must be empty before either model stage"
            )
    else:
        out_prefix.parent.mkdir(parents=True, exist_ok=False)

    # Stronger runs first in an isolated result directory.  Its complete audit
    # trail is held in memory and its temporary directory is deleted before the
    # native invocation begins, so neither stage can read the other's output.
    stronger_schema = build_stronger_model_schema(stronger_specs)
    stronger_frozen: FrozenStageArtifacts | None = None
    if stronger_specs:
        with tempfile.TemporaryDirectory(prefix="blind_stronger_result_") as stage_dir:
            isolated_prefix = Path(stage_dir) / "score"
            stronger_payload, _ = run_model_stage(
                stage="stronger",
                prompt_path=STRONGER_PROMPT_PATH,
                model_schema=stronger_schema,
                checklist_path=checklist_path,
                checklist=checklist,
                evidence_dir=evidence_dir,
                out_prefix=isolated_prefix,
                restricted_identity=restricted_identity,
                model=args.model,
                reasoning_effort=args.reasoning_effort,
                service_tier=args.service_tier,
                sandbox=args.sandbox,
                max_attempts=args.max_attempts,
                codex_timeout_seconds=args.codex_timeout_seconds,
                validate_payload=lambda payload, workspace: validate_stronger_model_output(
                    payload,
                    specs=stronger_specs,
                    checklist=checklist,
                    workspace_root=workspace,
                ),
                keep_workspace=None,
            )
            stronger_frozen = freeze_stage_artifacts(isolated_prefix)
        stronger_checks = stronger_payload["condition_checks"]
    else:
        stronger_checks = []
    assert_frozen_inputs_unchanged(
        checklist_path=checklist_path,
        checklist_sha256=checklist_sha256,
        evidence_dir=evidence_dir,
        evidence_tree_sha256=evidence_tree_sha256,
    )

    native_schema = build_native_model_schema(native_specs)
    with tempfile.TemporaryDirectory(prefix="blind_native_result_") as stage_dir:
        isolated_prefix = Path(stage_dir) / "score"
        native_payload, _ = run_model_stage(
            stage="native",
            prompt_path=NATIVE_PROMPT_PATH,
            model_schema=native_schema,
            checklist_path=checklist_path,
            checklist=checklist,
            evidence_dir=evidence_dir,
            out_prefix=isolated_prefix,
            restricted_identity=restricted_identity,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            service_tier=args.service_tier,
            sandbox=args.sandbox,
            max_attempts=args.max_attempts,
            codex_timeout_seconds=args.codex_timeout_seconds,
            validate_payload=lambda payload, workspace: validate_native_model_output(
                payload,
                specs=native_specs,
                checklist=checklist,
                workspace_root=workspace,
            ),
            keep_workspace=None,
        )
        native_frozen = freeze_stage_artifacts(isolated_prefix)
    assert_frozen_inputs_unchanged(
        checklist_path=checklist_path,
        checklist_sha256=checklist_sha256,
        evidence_dir=evidence_dir,
        evidence_tree_sha256=evidence_tree_sha256,
    )
    if any(out_prefix.parent.iterdir()):
        raise BlindScoreError(
            "Final score directory was not empty after isolated model invocations"
        )

    # No more model calls occur below this point; only now publish either
    # stage's model output, logs, schemas, aggregate, and SHA locks.
    native_artifacts = materialize_stage_artifacts(
        native_frozen,
        out_prefix=out_prefix,
        stage="native",
    )
    if stronger_frozen is not None:
        stronger_artifacts: StageRunArtifacts | None = materialize_stage_artifacts(
            stronger_frozen,
            out_prefix=out_prefix,
            stage="stronger",
        )
    else:
        stronger_artifacts = None
        legacy.write_json(
            stage_model_output_path(out_prefix, "stronger"),
            {"condition_checks": []},
        )
        legacy.write_json(
            stage_schema_output_path(out_prefix, "stronger"),
            stronger_schema,
        )

    native_result = derive_native_result(native_payload["test_checks"])
    native_score_path = stage_score_output_path(out_prefix, "native")
    legacy.write_json(native_score_path, {"native": native_result})
    native_schema_path = stage_schema_output_path(out_prefix, "native")
    native_lock_path = stage_lock_output_path(out_prefix, "native")
    legacy.write_json(
        native_lock_path,
        build_stage_lock(
            stage="native",
            stage_score_path=native_score_path,
            checklist_path=checklist_path,
            evidence_dir=evidence_dir,
            evidence_tree_sha256=evidence_tree_sha256,
            prompt_path=NATIVE_PROMPT_PATH,
            schema_path=native_schema_path,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            service_tier=args.service_tier,
            restricted_identity=restricted_identity,
        ),
    )

    stronger_result = derive_stronger_result(stronger_checks)
    stronger_score_path = stage_score_output_path(out_prefix, "stronger")
    legacy.write_json(stronger_score_path, {"stronger": stronger_result})
    stronger_schema_path = stage_schema_output_path(out_prefix, "stronger")
    stronger_lock_path = stage_lock_output_path(out_prefix, "stronger")
    legacy.write_json(
        stronger_lock_path,
        build_stage_lock(
            stage="stronger",
            stage_score_path=stronger_score_path,
            checklist_path=checklist_path,
            evidence_dir=evidence_dir,
            evidence_tree_sha256=evidence_tree_sha256,
            prompt_path=STRONGER_PROMPT_PATH,
            schema_path=stronger_schema_path,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            service_tier=args.service_tier,
            restricted_identity=restricted_identity,
        ),
    )

    score = {
        "schema_version": "blind_evidence_score_v1",
        "case_unit_id": checklist["case_unit_id"],
        "blind_mode": True,
        "native": native_result,
        "stronger": stronger_result,
    }
    validate_final_score(
        score,
        checklist=checklist,
        native_specs=native_specs,
        stronger_specs=stronger_specs,
    )
    json_path = out_prefix.with_suffix(".json")
    yaml_path = out_prefix.with_suffix(".yaml")
    legacy.write_json(json_path, score)
    legacy.write_yaml(yaml_path, score)

    blind_lock_path = blind_lock_output_path(out_prefix)
    score_dir = out_prefix.parent.resolve()
    legacy.write_json(
        blind_lock_path,
        {
            "schema_version": "blind_score_lock_v1",
            "locked_at": utc_now_iso(),
            "case_unit_id": checklist["case_unit_id"],
            "blind_mode": True,
            "released_evaluator_label_resolved": False,
            "model": args.model,
            "reasoning_effort": args.reasoning_effort,
            "service_tier": args.service_tier,
            "fast_mode": False,
            "auth_mode": "codex_login",
            "sandbox": args.sandbox,
            "model_stage_isolation": {
                "invocation_order": ["stronger", "native"],
                "stage_outputs_published_after_all_model_invocations": True,
                "cross_stage_output_visibility": False,
            },
            "score": artifact_binding(json_path, relative_to=score_dir),
            "score_yaml": artifact_binding(yaml_path, relative_to=score_dir),
            "native_stage_lock": artifact_binding(
                native_lock_path, relative_to=score_dir
            ),
            "stronger_stage_lock": artifact_binding(
                stronger_lock_path, relative_to=score_dir
            ),
            "checklist": artifact_binding(checklist_path, relative_to=score_dir),
            "evidence_tree_sha256": evidence_tree_sha256,
            "final_schema": artifact_binding(
                FINAL_SCHEMA_PATH, relative_to=score_dir
            ),
        },
    )

    manifest_path = legacy.manifest_output_path(out_prefix)
    legacy.write_json(
        manifest_path,
        build_manifest(
            out_prefix=out_prefix,
            checklist_path=checklist_path,
            checklist=checklist,
            evidence_dir=evidence_dir,
            evidence_tree_sha256=evidence_tree_sha256,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            service_tier=args.service_tier,
            auth_receipt=auth_receipt,
            native_schema_path=native_schema_path,
            stronger_schema_path=stronger_schema_path,
            native_score_path=native_score_path,
            stronger_score_path=stronger_score_path,
            native_lock_path=native_lock_path,
            stronger_lock_path=stronger_lock_path,
            blind_lock_path=blind_lock_path,
            native_artifacts=native_artifacts,
            stronger_artifacts=stronger_artifacts,
        ),
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (BlindScoreError, legacy.CodexScoreError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
