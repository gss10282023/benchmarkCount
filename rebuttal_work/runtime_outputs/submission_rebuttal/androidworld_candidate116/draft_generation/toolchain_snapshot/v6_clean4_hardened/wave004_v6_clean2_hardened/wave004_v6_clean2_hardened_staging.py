#!/usr/bin/env python3
"""Deterministic, read-only case staging for the clean2 hardened candidate.

The full canonical packet remains byte-for-byte present, but large embedded source
files are also materialized under ``packet_sources/<exact Source Inventory path>``.
Every distinct raw ``official/...`` Source Inventory payload is materialized and
must be read completely through a small read-only reader.  Byte-identical logical
aliases are bound explicitly and read once physically.  Semantic/AST closure is a
cross-audit only; it can never exclude a raw inventory member.  Codex JSONL events
are then converted into a fail-closed coverage receipt before an answer is accepted.

This module is stdlib-only and performs no model call.
"""

from __future__ import annotations

import ast
import contextlib
import hashlib
import json
import os
import re
import shutil
import stat
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable, Mapping, Sequence


ANCHORS = (
    "definition",
    "goal",
    "schema",
    "initialize_task",
    "is_successful",
    "evaluator",
)
INVENTORY_LINE_RE = re.compile(r"^- `([^`]+)`$")
SECTION_RE = re.compile(
    r"^### `(?P<path>[^`\n]+)`\n\n"
    r"Source ref: (?P<source_ref>[^\n]+)\n\n"
    r"```(?P<language>[A-Za-z0-9_.+-]+)\n"
    r"(?P<body>.*?)^```\n",
    re.MULTILINE | re.DOTALL,
)
SAFE_PATH_RE = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$")
SAFE_CASE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,127}$")
MAX_COVERAGE_CHUNK_BYTES = 10_000
MAX_READER_ENVELOPE_BYTES = 24_000
MAX_READER_ENVELOPE_TOKENS = 7_500
REQUIREMENTS_HASH_TOKEN_VARIATION_RESERVE = 256
MAX_COVERAGE_PLAN_ROW_BYTES = 4_096
MAX_COVERAGE_PLAN_PAGE_OUTPUT_BYTES = 10_000
MAX_COVERAGE_PLAN_PAGE_TOKENS = 4_000
FROZEN_TIKTOKEN_ENCODING = "o200k_base"
FROZEN_TIKTOKEN_VERSION = "0.12.0"
FROZEN_TIKTOKEN_BPE_SHA256 = (
    "446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d"
)
PERMISSION_PROFILE_NAME = "candidate_draft_isolated"
PRODUCTION_NAMESPACE = "wave_004_v6_clean4_hardened"
DISABLED_CODEX_FEATURES = (
    "apps",
    "plugins",
    "remote_plugin",
    "enable_mcp_apps",
    "skill_mcp_dependency_install",
    "browser_use",
    "browser_use_external",
    "browser_use_full_cdp_access",
    "computer_use",
    "in_app_browser",
    "image_generation",
    "artifact",
    "workspace_dependencies",
    "multi_agent",
    "tool_suggest",
    "plugin_sharing",
    "auth_elicitation",
    "tool_call_mcp_elicitation",
    "request_permissions_tool",
    "hooks",
    "shell_snapshot",
    "goals",
    "guardian_approval",
    "exec_permission_approvals",
    "code_mode_host",
    "remote_compaction_v2",
    "fast_mode",
)
IGNORED_GENERIC_CALL_NAMES = frozenset(
    {
        "add",
        "append",
        "bool",
        "clear",
        "copy",
        "dict",
        "encode",
        "endswith",
        "enumerate",
        "extend",
        "float",
        "format",
        "get",
        "int",
        "isinstance",
        "items",
        "join",
        "len",
        "list",
        "lower",
        "max",
        "min",
        "next",
        "open",
        "pop",
        "print",
        "range",
        "read",
        "replace",
        "set",
        "sleep",
        "sorted",
        "split",
        "startswith",
        "str",
        "strip",
        "sum",
        "super",
        "tuple",
        "type",
        "update",
        "values",
        "zip",
    }
)


class StagingError(RuntimeError):
    """Raised when a packet, staged workspace, or coverage trace is not exact."""


@contextlib.contextmanager
def exact_case_workspace(tmp_root: Path, case_unit_id: str) -> Iterable[str]:
    """Create exactly ``TMP/<case_id>`` once and remove it on every exit."""

    if not SAFE_CASE_ID_RE.fullmatch(case_unit_id):
        raise StagingError(f"unsafe exact case workspace id: {case_unit_id!r}")
    root = tmp_root.resolve(strict=True)
    workspace = root / case_unit_id
    if workspace.exists() or workspace.is_symlink():
        raise StagingError(f"exact case workspace already exists: {workspace}")
    os.mkdir(workspace, 0o700)
    os.chmod(workspace, 0o700)
    try:
        yield str(workspace)
    finally:
        if workspace.is_symlink():
            workspace.unlink()
        elif workspace.exists():
            for path in sorted(
                workspace.rglob("*"), key=lambda item: len(item.parts), reverse=True
            ):
                try:
                    os.chmod(path, 0o700 if path.is_dir() else 0o600)
                except OSError:
                    pass
            os.chmod(workspace, 0o700)
            shutil.rmtree(workspace)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def load_frozen_o200k_token_counter(
    *, tokenizer_root: Path, merge_table_path: Path
) -> tuple[Callable[[str], int], dict[str, Any]]:
    """Load the byte-bound tokenizer used for both planning and 116-case audit.

    The caller binds the tokenizer tree separately.  This helper still verifies the
    decisive merge table before import so a different cache cannot silently change
    range boundaries.
    """

    root = tokenizer_root.resolve(strict=True)
    merge_table = merge_table_path.resolve(strict=True)
    if not root.is_dir() or not merge_table.is_file() or merge_table.is_symlink():
        raise StagingError("frozen o200k tokenizer root/cache is not a regular closure")
    if sha256_bytes(merge_table.read_bytes()) != FROZEN_TIKTOKEN_BPE_SHA256:
        raise StagingError("frozen o200k merge-table hash changed")
    prior_cache = os.environ.get("TIKTOKEN_CACHE_DIR")
    prior_path = list(os.sys.path)
    os.environ["TIKTOKEN_CACHE_DIR"] = str(merge_table.parent)
    os.sys.path.insert(0, str(root))
    try:
        import tiktoken  # type: ignore[import-not-found]

        version = str(getattr(tiktoken, "__version__", ""))
        module_path = Path(str(getattr(tiktoken, "__file__", ""))).resolve(strict=True)
        if root not in module_path.parents:
            raise StagingError("tiktoken import did not resolve inside the frozen tokenizer root")
        if version != FROZEN_TIKTOKEN_VERSION:
            raise StagingError(
                f"frozen tiktoken version changed: {version!r}"
            )
        encoding = tiktoken.get_encoding(FROZEN_TIKTOKEN_ENCODING)
    except StagingError:
        raise
    except BaseException as exc:
        raise StagingError(f"cannot load frozen o200k tokenizer: {exc}") from exc
    finally:
        os.sys.path[:] = prior_path
        if prior_cache is None:
            os.environ.pop("TIKTOKEN_CACHE_DIR", None)
        else:
            os.environ["TIKTOKEN_CACHE_DIR"] = prior_cache

    def count(value: str) -> int:
        return len(encoding.encode(value))

    binding = {
        "encoding": FROZEN_TIKTOKEN_ENCODING,
        "tiktoken_version": FROZEN_TIKTOKEN_VERSION,
        "merge_table_sha256": FROZEN_TIKTOKEN_BPE_SHA256,
    }
    binding["binding_sha256"] = canonical_sha256(binding)
    return count, binding


def safe_source_path(value: Any) -> str:
    if not isinstance(value, str) or not SAFE_PATH_RE.fullmatch(value):
        raise StagingError(f"unsafe Source Inventory path: {value!r}")
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise StagingError(f"unsafe Source Inventory path: {value!r}")
    return value


def _toml_key(value: Path | str) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def build_permission_profile_override(
    *,
    workspace_root: Path,
    repository_root: Path,
    wave_tmp_root: Path,
    auth_home: Path,
    original_codex_home: Path,
    isolated_home: Path,
    real_home: Path,
    require_existing_paths: bool = True,
) -> str:
    """Build the exact deny-by-default filesystem/network permission profile.

    The broad temp roots, dedicated wave temp root, both auth roots, and repository
    are denied.  Only the current per-case workspace is reopened read-only.
    """

    workspace = workspace_root.resolve(strict=require_existing_paths)
    repository = repository_root.resolve(strict=require_existing_paths)
    tmp_root = wave_tmp_root.resolve(strict=require_existing_paths)
    auth = auth_home.resolve(strict=require_existing_paths)
    original_auth = original_codex_home.resolve(strict=require_existing_paths)
    child_home = isolated_home.resolve(strict=require_existing_paths)
    host_home = real_home.resolve(strict=require_existing_paths)
    if workspace.parent != tmp_root:
        raise StagingError("per-case workspace is not an immediate child of the bound wave TMP root")
    if repository == workspace or repository in workspace.parents:
        raise StagingError("per-case workspace unexpectedly resides inside the repository")
    if auth == workspace or auth in workspace.parents:
        raise StagingError("per-case workspace unexpectedly resides inside isolated auth home")
    if child_home == auth or child_home == tmp_root or child_home == workspace:
        raise StagingError("isolated HOME/CODEX_HOME/TMP roots are not distinct")
    if host_home not in original_auth.parents and host_home != original_auth:
        raise StagingError("original Codex home is not inside the bound real HOME")
    filesystem = (
        '{":minimal"="read",":workspace_roots"={"."="read"},'
        '":tmpdir"="deny",":slash_tmp"="deny",'
        + _toml_key(tmp_root)
        + '="deny",'
        + _toml_key(auth)
        + '="deny",'
        + _toml_key(original_auth)
        + '="deny",'
        + _toml_key(child_home)
        + '="deny",'
        + _toml_key(host_home)
        + '="deny",'
        + _toml_key(repository)
        + '="deny",'
        + _toml_key(workspace)
        + '="read"}'
    )
    return (
        "permissions."
        + PERMISSION_PROFILE_NAME
        + '={description="Canonical packet staged workspace read only",filesystem='
        + filesystem
        + ",network={enabled=false}}"
    )


def build_codex_exec_argv(
    *,
    codex_executable: Path,
    workspace_root: Path,
    schema_path: Path,
    output_path: Path,
    model: str,
    reasoning_effort: str,
    repository_root: Path,
    wave_tmp_root: Path,
    auth_home: Path,
    original_codex_home: Path,
    isolated_home: Path,
    real_home: Path,
    require_existing_paths: bool = True,
) -> list[str]:
    """Return the one exact production Codex argv; it contains no sandbox/add-dir/search."""

    workspace = workspace_root.resolve(strict=require_existing_paths)
    schema = schema_path.resolve(strict=require_existing_paths)
    output = output_path.resolve(strict=require_existing_paths)
    if schema != workspace / "output_schema.json" or output != workspace / "draft_body.json":
        raise StagingError("Codex schema/output paths are not the exact case-workspace paths")
    profile = build_permission_profile_override(
        workspace_root=workspace,
        repository_root=repository_root,
        wave_tmp_root=wave_tmp_root,
        auth_home=auth_home,
        original_codex_home=original_codex_home,
        isolated_home=isolated_home,
        real_home=real_home,
        require_existing_paths=require_existing_paths,
    )
    command = [
        str(codex_executable.resolve(strict=True)),
        "-a",
        "never",
        "--strict-config",
        "exec",
        "--cd",
        str(workspace),
        "--skip-git-repo-check",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--model",
        model,
        "-c",
        f'default_permissions="{PERMISSION_PROFILE_NAME}"',
        "-c",
        profile,
        "-c",
        f'model_reasoning_effort="{reasoning_effort}"',
        "-c",
        'model_verbosity="low"',
        "-c",
        'web_search="disabled"',
        "-c",
        "mcp_servers={}",
        "-c",
        'shell_environment_policy.inherit="none"',
    ]
    for feature in DISABLED_CODEX_FEATURES:
        command.extend(("--disable", feature))
    command.extend(
        (
            "--color",
            "never",
            "--json",
            "--output-schema",
            str(schema),
            "-o",
            str(output),
            "-",
        )
    )
    forbidden = {"--sandbox", "-s", "--add-dir", "--search"}
    if forbidden.intersection(command):
        raise StagingError("forbidden Codex privilege/search flag entered exact argv")
    if command[:5] != [
        str(codex_executable.resolve(strict=True)),
        "-a",
        "never",
        "--strict-config",
        "exec",
    ]:
        raise StagingError("Codex global approval/strict-config flags are not before exec")
    return command


def _between(text: str, start: str, end: str, label: str) -> str:
    if text.count(start) != 1 or text.count(end) != 1:
        raise StagingError(f"packet has non-exact {label} headings")
    before, remainder = text.split(start, 1)
    body, _after = remainder.split(end, 1)
    if not before and start != "# Case Packet\n":
        raise StagingError(f"packet {label} ordering is invalid")
    return body


def parse_packet_sources(case_packet_text: str) -> dict[str, Any]:
    """Parse and cross-check the packet inventory and every embedded source body."""

    inventory_body = _between(
        case_packet_text,
        "## Source Inventory\n\n",
        "## Packet Source Files\n",
        "Source Inventory",
    )
    inventory: list[str] = []
    for line in inventory_body.splitlines():
        if not line.strip():
            continue
        match = INVENTORY_LINE_RE.fullmatch(line)
        if match is None:
            raise StagingError(f"unexpected Source Inventory line: {line!r}")
        inventory.append(safe_source_path(match.group(1)))
    if not inventory or len(inventory) != len(set(inventory)):
        raise StagingError("Source Inventory is empty or contains duplicates")

    source_region = _between(
        case_packet_text,
        "## Packet Source Files\n\n",
        "## Raw Source Provenance\n",
        "Packet Source Files",
    )
    sources: dict[str, dict[str, Any]] = {}
    cursor = 0
    section_order: list[str] = []
    for match in SECTION_RE.finditer(source_region):
        if source_region[cursor : match.start()].strip():
            raise StagingError("unparsed bytes exist between embedded packet sources")
        path = safe_source_path(match.group("path"))
        if path in sources:
            raise StagingError(f"duplicate embedded packet source: {path}")
        body = match.group("body")
        sources[path] = {
            "path": path,
            "source_ref": match.group("source_ref"),
            "language": match.group("language"),
            "text": body,
            "sha256": sha256_text(body),
            "size_bytes": len(body.encode("utf-8")),
            "line_count": len(body.splitlines()),
        }
        section_order.append(path)
        cursor = match.end()
    if source_region[cursor:].strip():
        raise StagingError("unparsed bytes follow the final embedded packet source")
    if section_order != inventory:
        raise StagingError("embedded packet source order/set differs from Source Inventory")

    raw_region = case_packet_text.split("## Raw Source Provenance\n\n", 1)[1]
    raw_match = re.fullmatch(r"```json\n(?P<body>.*?)\n```\n?", raw_region, re.DOTALL)
    if raw_match is None:
        raise StagingError("Raw Source Provenance block is not exact JSON fencing")
    try:
        raw_provenance = json.loads(raw_match.group("body"))
    except json.JSONDecodeError as exc:
        raise StagingError(f"Raw Source Provenance is invalid JSON: {exc}") from exc
    if raw_provenance.get("packet_files") != inventory:
        raise StagingError("Raw Source Provenance packet_files differs from Source Inventory")
    if sorted(raw_provenance.get("copied_files") or []) != sorted(inventory):
        raise StagingError("Raw Source Provenance copied_files differs from Source Inventory")

    try:
        semantics = json.loads(sources["derived/canonical_task_semantics.json"]["text"])
    except (KeyError, json.JSONDecodeError) as exc:
        raise StagingError("canonical_task_semantics is missing or invalid") from exc
    try:
        selected_task_source = json.loads(
            sources["derived/selected_task_source.json"]["text"]
        )
    except (KeyError, json.JSONDecodeError) as exc:
        raise StagingError("selected_task_source is missing or invalid") from exc
    return {
        "inventory": inventory,
        "sources": sources,
        "raw_provenance": raw_provenance,
        "canonical_task_semantics": semantics,
        "selected_task_source": selected_task_source,
    }


def _walk_source_bindings(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, dict):
        bindings = value.get("source_bindings")
        if isinstance(bindings, list):
            for binding in bindings:
                if isinstance(binding, dict):
                    yield binding
        for child in value.values():
            yield from _walk_source_bindings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_source_bindings(child)


def _walk_source_refs(value: Any, pointer: str = "") -> Iterable[tuple[str, Mapping[str, Any]]]:
    if isinstance(value, dict):
        source_ref = value.get("source_ref")
        if isinstance(source_ref, dict) and source_ref.get("path"):
            yield pointer + "/source_ref", source_ref
        for key, child in value.items():
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            yield from _walk_source_refs(child, pointer + "/" + escaped)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_source_refs(child, pointer + f"/{index}")


def _binding_source_path(
    binding: Mapping[str, Any], sources: Mapping[str, Mapping[str, Any]]
) -> str:
    artifact_path = str(binding.get("artifact_path") or "")
    marker = "shared_source/source_tree/"
    expected = ""
    if marker in artifact_path:
        expected = "official/install/" + artifact_path.split(marker, 1)[1]
    claimed_sha = str(binding.get("sha256") or "")
    if expected in sources and sources[expected]["sha256"] == claimed_sha:
        return expected
    candidates = [
        path
        for path, row in sources.items()
        if path.startswith("official/") and row["sha256"] == claimed_sha
    ]
    preferred = [path for path in candidates if "/.venv" not in path]
    if len(preferred) == 1:
        return preferred[0]
    if len(candidates) == 1:
        return candidates[0]
    raise StagingError(
        f"cannot map source binding to one raw official inventory path: {artifact_path!r}"
    )


def _source_ref_path(
    source_ref: Mapping[str, Any], sources: Mapping[str, Mapping[str, Any]]
) -> str:
    relative = safe_source_path(str(source_ref.get("path") or ""))
    expected = "official/install/" + relative
    claimed_sha = str(source_ref.get("file_sha256") or source_ref.get("sha256") or "")
    if expected in sources and (not claimed_sha or sources[expected]["sha256"] == claimed_sha):
        return expected
    candidates = [
        path
        for path, row in sources.items()
        if path.startswith("official/")
        and path.endswith("/" + relative)
        and (not claimed_sha or row["sha256"] == claimed_sha)
    ]
    preferred = [path for path in candidates if "/.venv" not in path]
    if len(preferred) == 1:
        return preferred[0]
    if len(candidates) == 1:
        return candidates[0]
    raise StagingError(f"cannot map source_ref to one raw official inventory path: {source_ref}")


READER_COMPLETION_PREFIX = "WAVE004_READER_COMPLETE "
READER_BODY_PREFIX = "WAVE004_READER_BODY "
READER_OPERATION_EXPECTATIONS_SCHEMA = (
    "androidworld_candidate116_reader_operation_expectations/v1"
)
CODEX_EVENT_HOST_SHELL = "/bin/zsh"
CODEX_EVENT_HOST_SHELL_FLAG = "-lc"
SAFE_READER_INNER_COMMAND_RE = re.compile(r"^[A-Za-z0-9_./:= -]+$")


def codex_event_shell_carrier_binding() -> dict[str, Any]:
    """Return the frozen Codex 0.144.4 command-event carrier calibration."""

    payload = {
        "schema_version": "codex_command_event_shell_carrier/v1",
        "codex_cli_version": "0.144.4",
        "shell_path": CODEX_EVENT_HOST_SHELL,
        "shell_flag": CODEX_EVENT_HOST_SHELL_FLAG,
        "inner_command_policy": "single_ascii_spaces_and_safe_reader_tokens_only",
        "event_serialization": "shell -lc single-quoted-inner-command",
        "bare_semantic_argv_event_allowed": False,
        "double_wrapper_allowed": False,
        "shell_operators_or_substitution_allowed": False,
        "calibration_basis": (
            "existing local Codex 0.144.4 item.started/item.completed "
            "command_execution events with safe inner payloads"
        ),
    }
    payload["carrier_binding_sha256"] = canonical_sha256(payload)
    return payload


def render_codex_event_command(argv: Sequence[str]) -> str:
    """Render the sole accepted host-carried event command for one reader argv."""

    if not argv or not all(isinstance(token, str) and token for token in argv):
        raise StagingError("reader semantic argv is not a non-empty string sequence")
    inner = " ".join(argv)
    if (
        not SAFE_READER_INNER_COMMAND_RE.fullmatch(inner)
        or any(token in inner for token in ("'", '"', "`", "$", ";", "&", "|", "\\", "\n", "\r"))
        or "  " in inner
    ):
        raise StagingError("reader semantic argv cannot use the frozen host shell carrier")
    return (
        CODEX_EVENT_HOST_SHELL
        + " "
        + CODEX_EVENT_HOST_SHELL_FLAG
        + " '"
        + inner
        + "'"
    )


def _reader_envelope(
    *, kind: str, argv: Sequence[str], requirements_sha256: str, body: str
) -> str:
    """Render one exact reader stdout envelope with its completion proof last."""

    if not body.endswith("\n"):
        raise StagingError("reader envelope body must end in one newline")
    completion = {
        "argv_sha256": canonical_sha256(list(argv)),
        "body_sha256": sha256_text(body),
        "body_size_bytes": len(body.encode("utf-8")),
        "kind": kind,
        "requirements_sha256": requirements_sha256,
    }
    return body + READER_COMPLETION_PREFIX + json.dumps(
        completion, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ) + "\n"


def _read_argv(row: Mapping[str, Any], requirements_sha256: str) -> list[str]:
    return [
        "/usr/bin/python3",
        "packet_reader.py",
        "read",
        "--anchor",
        str(row["anchor"]),
        "--path",
        str(row["path"]),
        "--start",
        str(row["start_line"]),
        "--end",
        str(row["end_line"]),
        "--manifest-sha256",
        requirements_sha256,
    ]


def _page_argv(page: int, requirements_sha256: str) -> list[str]:
    return [
        "/usr/bin/python3",
        "packet_reader.py",
        "plan-page",
        "--page",
        str(page),
        "--manifest-sha256",
        requirements_sha256,
    ]


def _render_read_output(
    *, row: Mapping[str, Any], source_text: str, requirements_sha256: str
) -> str:
    lines = source_text.splitlines(keepends=True)
    start = int(row["start_line"])
    end = int(row["end_line"])
    snippet_lines = lines[start - 1 : end]
    identity = {
        key: row[key]
        for key in (
            "anchor",
            "path",
            "start_line",
            "end_line",
            "file_sha256",
            "snippet_sha256",
            "chunk_size_bytes",
            "snippet_ends_with_newline",
            "chunk_index",
            "chunk_count",
        )
    }
    body = READER_BODY_PREFIX + json.dumps(
        {"kind": "read", "identity": identity},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
    snippet = "".join(snippet_lines)
    if sha256_text(snippet) != row["snippet_sha256"]:
        raise StagingError("reader render snippet hash differs from the frozen range")
    body += snippet
    if not snippet.endswith("\n"):
        body += "\n"
    return _reader_envelope(
        kind="read",
        argv=_read_argv(row, requirements_sha256),
        requirements_sha256=requirements_sha256,
        body=body,
    )


def _render_page_output(
    *,
    page_index: int,
    page_count: int,
    rows: Sequence[Mapping[str, Any]],
    requirements_sha256: str,
) -> str:
    payload = {
        "page_index": page_index,
        "page_count": page_count,
        "requirements_sha256": requirements_sha256,
        "rows": list(rows),
    }
    body = READER_BODY_PREFIX + json.dumps(
        {"kind": "plan-page", "page_index": page_index, "page_count": page_count},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
    body += json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return _reader_envelope(
        kind="plan-page",
        argv=_page_argv(page_index, requirements_sha256),
        requirements_sha256=requirements_sha256,
        body=body,
    )


def render_overview_output_for_audit(requirements: Mapping[str, Any]) -> str:
    summary = {
        key: requirements[key]
        for key in (
            "schema_version",
            "production_namespace",
            "case_unit_id",
            "task_id",
            "policy",
            "requirements_sha256",
            "required_range_count",
            "coverage_page_count",
            "raw_official_source_closure_count",
            "raw_official_inventory_member_count",
            "raw_official_distinct_sha_count",
            "raw_official_omitted_count",
            "derived_navigation",
            "anchors",
        )
    }
    argv = ["/usr/bin/python3", "packet_reader.py", "overview"]
    body = READER_BODY_PREFIX + json.dumps(
        {"kind": "overview"},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
    body += json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return _reader_envelope(
        kind="overview",
        argv=argv,
        requirements_sha256=str(requirements["requirements_sha256"]),
        body=body,
    )


def render_header_output_for_audit(
    *, header_text: str, case_packet_sha256: str, requirements_sha256: str
) -> str:
    argv = ["/usr/bin/python3", "packet_reader.py", "header"]
    body = READER_BODY_PREFIX + json.dumps(
        {"case_packet_sha256": case_packet_sha256, "kind": "header"},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
    body += header_text if header_text.endswith("\n") else header_text + "\n"
    return _reader_envelope(
        kind="header",
        argv=argv,
        requirements_sha256=requirements_sha256,
        body=body,
    )


def render_plan_page_output_for_audit(
    *, page_index: int, requirements: Mapping[str, Any]
) -> str:
    page = requirements["coverage_pages"][page_index]
    start = int(page["start_range_index"])
    end = int(page["end_range_index_exclusive"])
    return _render_page_output(
        page_index=page_index,
        page_count=int(requirements["coverage_page_count"]),
        rows=requirements["required_ranges"][start:end],
        requirements_sha256=str(requirements["requirements_sha256"]),
    )


def render_read_output_for_audit(
    *, row: Mapping[str, Any], source_text: str, requirements_sha256: str
) -> str:
    return _render_read_output(
        row=row,
        source_text=source_text,
        requirements_sha256=requirements_sha256,
    )


def _reader_output_body_and_completion(output: str) -> tuple[str, dict[str, Any]]:
    """Split one deterministic reader output without trusting a marker search."""

    if not output.endswith("\n"):
        raise StagingError("reader output lacks its terminal newline")
    marker_start = output.rfind("\n" + READER_COMPLETION_PREFIX)
    if marker_start < 0:
        raise StagingError("reader output lacks its terminal completion record")
    body = output[: marker_start + 1]
    marker_line = output[marker_start + 1 : -1]
    if READER_COMPLETION_PREFIX in body or not marker_line.startswith(
        READER_COMPLETION_PREFIX
    ):
        raise StagingError("reader output completion record is non-unique/non-terminal")
    try:
        completion = json.loads(marker_line[len(READER_COMPLETION_PREFIX) :])
    except json.JSONDecodeError as exc:
        raise StagingError("reader output completion record is invalid JSON") from exc
    if not isinstance(completion, dict):
        raise StagingError("reader output completion record is not an object")
    return body, completion


def _reader_operation_record(
    *,
    operation_index: int,
    kind: str,
    argv: Sequence[str],
    output: str,
    semantic_identity: Mapping[str, Any],
    token_counter: Callable[[str], int],
) -> dict[str, Any]:
    """Bind one exact command, complete body, and terminal output envelope."""

    body, completion = _reader_output_body_and_completion(output)
    expected_completion = {
        "argv_sha256": canonical_sha256(list(argv)),
        "body_sha256": sha256_text(body),
        "body_size_bytes": len(body.encode("utf-8")),
        "kind": kind,
        "requirements_sha256": completion.get("requirements_sha256"),
    }
    if completion != expected_completion:
        raise StagingError("planned reader completion record is internally inconsistent")
    max_bytes = (
        MAX_COVERAGE_PLAN_PAGE_OUTPUT_BYTES
        if kind == "plan-page"
        else MAX_READER_ENVELOPE_BYTES
    )
    max_tokens = (
        MAX_COVERAGE_PLAN_PAGE_TOKENS
        if kind == "plan-page"
        else MAX_READER_ENVELOPE_TOKENS
    )
    output_bytes = len(output.encode("utf-8"))
    output_tokens = token_counter(output)
    if output_bytes > max_bytes or output_tokens > max_tokens:
        raise StagingError(
            f"planned {kind} operation exceeds its exact byte/token envelope"
        )
    semantic_command = " ".join(argv)
    event_command = render_codex_event_command(argv)
    record = {
        "operation_index": operation_index,
        "kind": kind,
        "argv": list(argv),
        "argv_sha256": canonical_sha256(list(argv)),
        "semantic_command": semantic_command,
        "exact_command": event_command,
        "event_command_sha256": sha256_text(event_command),
        "semantic_identity": dict(semantic_identity),
        "body_sha256": sha256_text(body),
        "body_size_bytes": len(body.encode("utf-8")),
        "body_line_count": body.count("\n"),
        "body_ends_with_newline": True,
        "terminal_completion": completion,
        "expected_full_output_sha256": sha256_text(output),
        "expected_full_output_size_bytes": output_bytes,
        "expected_full_output_o200k_tokens": output_tokens,
        "max_full_output_size_bytes": max_bytes,
        "max_full_output_o200k_tokens": max_tokens,
        "aggregated_output_must_equal_exact_bytes": True,
    }
    record["operation_sha256"] = canonical_sha256(record)
    return record


def build_reader_operation_expectations(
    *,
    case_packet_text: str,
    parsed: Mapping[str, Any],
    requirements: Mapping[str, Any],
    token_counter: Callable[[str], int],
) -> dict[str, Any]:
    """Build layer B after layer A is frozen, avoiding a self-hash cycle.

    Layer A (``coverage_requirements``) owns the requirements SHA used by every
    reader command and terminal marker.  This independent layer B binds A and
    then freezes the exact ordered commands plus complete-output identities.
    """

    requirements_core = dict(requirements)
    claimed_requirements_sha = requirements_core.pop("requirements_sha256", None)
    if (
        not isinstance(claimed_requirements_sha, str)
        or canonical_sha256(requirements_core) != claimed_requirements_sha
    ):
        raise StagingError("reader expectations received an unsealed layer-A manifest")
    if requirements.get("case_packet_sha256") != sha256_text(case_packet_text):
        raise StagingError("reader expectations packet hash differs from layer A")
    sources = parsed.get("sources")
    if not isinstance(sources, Mapping):
        raise StagingError("reader expectations lack parsed packet sources")
    marker = "## Packet Source Files\n"
    if case_packet_text.count(marker) != 1:
        raise StagingError("reader expectations packet header boundary is non-exact")
    header_text = case_packet_text.split(marker, 1)[0]

    operations: list[dict[str, Any]] = []

    def append(
        kind: str,
        argv: Sequence[str],
        output: str,
        semantic_identity: Mapping[str, Any],
    ) -> None:
        operations.append(
            _reader_operation_record(
                operation_index=len(operations),
                kind=kind,
                argv=argv,
                output=output,
                semantic_identity=semantic_identity,
                token_counter=token_counter,
            )
        )

    overview_argv = ["/usr/bin/python3", "packet_reader.py", "overview"]
    append(
        "overview",
        overview_argv,
        render_overview_output_for_audit(requirements),
        {
            "case_unit_id": requirements["case_unit_id"],
            "required_range_count": requirements["required_range_count"],
            "coverage_page_count": requirements["coverage_page_count"],
        },
    )
    header_argv = ["/usr/bin/python3", "packet_reader.py", "header"]
    append(
        "header",
        header_argv,
        render_header_output_for_audit(
            header_text=header_text,
            case_packet_sha256=str(requirements["case_packet_sha256"]),
            requirements_sha256=claimed_requirements_sha,
        ),
        {
            "case_packet_sha256": requirements["case_packet_sha256"],
            "header_sha256": sha256_text(header_text),
            "header_size_bytes": len(header_text.encode("utf-8")),
        },
    )
    for page_index, page in enumerate(requirements.get("coverage_pages") or []):
        append(
            "plan-page",
            _page_argv(page_index, claimed_requirements_sha),
            render_plan_page_output_for_audit(
                page_index=page_index,
                requirements=requirements,
            ),
            {
                "page_index": page_index,
                "start_range_index": page["start_range_index"],
                "end_range_index_exclusive": page["end_range_index_exclusive"],
                "rows_sha256": canonical_sha256(
                    requirements["required_ranges"][
                        page["start_range_index"] : page["end_range_index_exclusive"]
                    ]
                ),
            },
        )
    for range_index, row in enumerate(requirements.get("required_ranges") or []):
        source = sources.get(row["path"])
        if not isinstance(source, Mapping) or not isinstance(source.get("text"), str):
            raise StagingError(f"reader expectation source is absent: {row['path']}")
        append(
            "read",
            _read_argv(row, claimed_requirements_sha),
            _render_read_output(
                row=row,
                source_text=str(source["text"]),
                requirements_sha256=claimed_requirements_sha,
            ),
            {
                "range_index": range_index,
                "range_sha256": canonical_sha256(row),
                "path": row["path"],
                "logical_aliases": row["logical_aliases"],
                "start_line": row["start_line"],
                "end_line": row["end_line"],
                "file_sha256": row["file_sha256"],
                "snippet_sha256": row["snippet_sha256"],
                "chunk_size_bytes": row["chunk_size_bytes"],
            },
        )

    expected_kinds = [
        "overview",
        "header",
        *(["plan-page"] * int(requirements["coverage_page_count"])),
        *(["read"] * int(requirements["required_range_count"])),
    ]
    if [row["kind"] for row in operations] != expected_kinds:
        raise StagingError("reader operation plan does not have the exact global order")
    payload = {
        "schema_version": READER_OPERATION_EXPECTATIONS_SCHEMA,
        "production_namespace": PRODUCTION_NAMESPACE,
        "case_unit_id": requirements["case_unit_id"],
        "task_id": requirements["task_id"],
        "coverage_requirements_sha256": claimed_requirements_sha,
        "case_packet_sha256": requirements["case_packet_sha256"],
        "tokenizer_binding": requirements["tokenizer_binding"],
        "event_trust_policy": {
            "accepted_event_type": "item.completed",
            "accepted_output_field": "aggregated_output",
            "same_id_started_completed_pair_required": True,
            "completed_status_required": "completed",
            "completed_exit_code_required": 0,
            "shell_wrapper_pipeline_or_chain_allowed": False,
            "additional_command_count_allowed": 0,
            "terminal_completion_must_be_unique_and_last": True,
            "full_body_and_output_identity_required": True,
        },
        "event_shell_carrier": codex_event_shell_carrier_binding(),
        "global_order": "overview_then_header_then_all_pages_then_all_ranges",
        "operation_count": len(operations),
        "overview_operation_count": 1,
        "header_operation_count": 1,
        "plan_page_operation_count": requirements["coverage_page_count"],
        "read_operation_count": requirements["required_range_count"],
        "operations": operations,
        "operations_sha256": canonical_sha256(operations),
    }
    payload["reader_operation_expectations_sha256"] = canonical_sha256(payload)
    return payload


def verify_reader_operation_expectations_binding(
    requirements: Mapping[str, Any], expectations: Mapping[str, Any]
) -> None:
    """Fail closed if layer B or its exact layer-A binding is altered."""

    requirements_core = dict(requirements)
    requirements_sha = requirements_core.pop("requirements_sha256", None)
    if canonical_sha256(requirements_core) != requirements_sha:
        raise StagingError("coverage requirements self-hash mismatch")
    expectations_core = dict(expectations)
    expectations_sha = expectations_core.pop(
        "reader_operation_expectations_sha256", None
    )
    operations = expectations.get("operations")
    if (
        expectations.get("schema_version") != READER_OPERATION_EXPECTATIONS_SCHEMA
        or expectations.get("production_namespace") != PRODUCTION_NAMESPACE
        or requirements.get("production_namespace") != PRODUCTION_NAMESPACE
        or canonical_sha256(expectations_core) != expectations_sha
        or expectations.get("coverage_requirements_sha256") != requirements_sha
        or expectations.get("case_unit_id") != requirements.get("case_unit_id")
        or expectations.get("task_id") != requirements.get("task_id")
        or expectations.get("case_packet_sha256")
        != requirements.get("case_packet_sha256")
        or expectations.get("event_shell_carrier")
        != codex_event_shell_carrier_binding()
        or not isinstance(operations, list)
        or expectations.get("operation_count") != len(operations)
        or expectations.get("operations_sha256") != canonical_sha256(operations)
    ):
        raise StagingError("reader operation expectations binding/self-hash is invalid")
    for index, operation in enumerate(operations):
        if not isinstance(operation, Mapping):
            raise StagingError("reader operation expectation is not an object")
        argv = operation.get("argv")
        if not isinstance(argv, list) or not all(
            isinstance(token, str) and token for token in argv
        ):
            raise StagingError(f"reader operation expectation {index} argv is invalid")
        operation_core = dict(operation)
        operation_sha = operation_core.pop("operation_sha256", None)
        if (
            operation.get("operation_index") != index
            or canonical_sha256(operation_core) != operation_sha
            or operation.get("argv_sha256")
            != canonical_sha256(argv)
            or operation.get("semantic_command") != " ".join(argv)
            or operation.get("exact_command") != render_codex_event_command(argv)
            or operation.get("event_command_sha256")
            != sha256_text(render_codex_event_command(argv))
        ):
            raise StagingError(f"reader operation expectation {index} is invalid")


def _provisional_chunk_row(
    *,
    path: str,
    logical_aliases: Sequence[str],
    file_sha256: str,
    start_line: int,
    end_line: int,
    snippet: str,
) -> dict[str, Any]:
    return {
        "anchor": "raw_source_closure_chunk",
        "raw_authority": "official_source",
        "path": path,
        "logical_aliases": list(logical_aliases),
        "start_line": start_line,
        "end_line": end_line,
        "file_sha256": file_sha256,
        "snippet_sha256": sha256_text(snippet),
        "snippet_ends_with_newline": snippet.endswith("\n"),
        # Six-digit sentinels make the planning measurement conservative for the
        # actual 116-case range count while keeping the exact production format.
        "chunk_index": 999_999,
        "chunk_count": 999_999,
        "chunk_size_bytes": len(snippet.encode("utf-8")),
        "owner_module": None,
        "owner_qualname": "complete_file_chunk",
    }


def _complete_file_chunks(
    *,
    path: str,
    source: Mapping[str, Any],
    logical_aliases: Sequence[str],
    token_counter: Callable[[str], int],
) -> list[dict[str, Any]]:
    """Token-adapt one full file to bounded, tail-proven reader envelopes."""

    text = str(source["text"])
    lines = text.splitlines(keepends=True)
    if not lines:
        raise StagingError("raw closure source file is unexpectedly empty")
    encoded_sizes = [len(line.encode("utf-8")) for line in lines]
    for index, size in enumerate(encoded_sizes, 1):
        if size > MAX_COVERAGE_CHUNK_BYTES:
            raise StagingError(
                f"one source line exceeds 10KB raw chunk ceiling at {path}:{index}: {size}"
            )

    chunks: list[dict[str, Any]] = []
    cursor = 0
    placeholder_sha = "0" * 64
    while cursor < len(lines):
        raw_bytes = 0
        byte_end = cursor
        while byte_end < len(lines):
            candidate_size = raw_bytes + encoded_sizes[byte_end]
            if candidate_size > MAX_COVERAGE_CHUNK_BYTES:
                break
            raw_bytes = candidate_size
            byte_end += 1
        if byte_end == cursor:
            raise StagingError(f"cannot place one raw source line in a bounded chunk: {path}")

        low = cursor + 1
        high = byte_end
        best: tuple[int, dict[str, Any], int, int] | None = None
        while low <= high:
            candidate_end = (low + high) // 2
            snippet = "".join(lines[cursor:candidate_end])
            row = _provisional_chunk_row(
                path=path,
                logical_aliases=logical_aliases,
                file_sha256=str(source["sha256"]),
                start_line=cursor + 1,
                end_line=candidate_end,
                snippet=snippet,
            )
            rendered = _render_read_output(
                row=row,
                source_text=text,
                requirements_sha256=placeholder_sha,
            )
            output_bytes = len(rendered.encode("utf-8"))
            output_tokens = token_counter(rendered)
            if (
                output_bytes <= MAX_READER_ENVELOPE_BYTES
                and output_tokens + REQUIREMENTS_HASH_TOKEN_VARIATION_RESERVE
                <= MAX_READER_ENVELOPE_TOKENS
            ):
                best = (
                    candidate_end,
                    row,
                    output_bytes,
                    output_tokens + REQUIREMENTS_HASH_TOKEN_VARIATION_RESERVE,
                )
                low = candidate_end + 1
            else:
                high = candidate_end - 1
        if best is None:
            raise StagingError(
                f"one line cannot fit the frozen reader byte/token envelope: {path}:{cursor + 1}"
            )
        candidate_end, row, output_bytes, output_tokens = best
        chunks.append(
            {
                "start_line": row["start_line"],
                "end_line": row["end_line"],
                "size_bytes": row["chunk_size_bytes"],
                "snippet_sha256": row["snippet_sha256"],
                "snippet_ends_with_newline": row[
                    "snippet_ends_with_newline"
                ],
                "planned_reader_envelope_max_bytes": output_bytes,
                "planned_reader_envelope_max_o200k_tokens": output_tokens,
            }
        )
        cursor = candidate_end

    if (
        chunks[0]["start_line"] != 1
        or chunks[-1]["end_line"] != len(lines)
        or any(
            left["end_line"] + 1 != right["start_line"]
            for left, right in zip(chunks, chunks[1:])
        )
        or sum(chunk["size_bytes"] for chunk in chunks) != len(text.encode("utf-8"))
        or any(chunk["size_bytes"] > MAX_COVERAGE_CHUNK_BYTES for chunk in chunks)
        or any(
            chunk["planned_reader_envelope_max_bytes"] > MAX_READER_ENVELOPE_BYTES
            or chunk["planned_reader_envelope_max_o200k_tokens"]
            > MAX_READER_ENVELOPE_TOKENS
            for chunk in chunks
        )
    ):
        raise StagingError("complete-file coverage chunks are not contiguous/exhaustive/bounded")
    return chunks


def _pack_coverage_pages(
    required_ranges: Sequence[Mapping[str, Any]],
    *,
    token_counter: Callable[[str], int],
) -> list[dict[str, Any]]:
    """Greedily page by exact serialized byte/token envelope, never row count."""

    if not required_ranges:
        raise StagingError("cannot page an empty raw-source read plan")
    for index, row in enumerate(required_ranges):
        row_bytes = len(canonical_bytes(row))
        if row_bytes > MAX_COVERAGE_PLAN_ROW_BYTES:
            raise StagingError(
                f"coverage plan row {index} exceeds serialized hard limit: {row_bytes}"
            )
    placeholder_sha = "0" * 64
    boundaries: list[tuple[int, int]] = []
    start = 0
    while start < len(required_ranges):
        best_end: int | None = None
        end = start + 1
        while end <= len(required_ranges):
            # Six-digit page sentinels are conservative for the final page indexes.
            output = _render_page_output(
                page_index=999_999,
                page_count=999_999,
                rows=required_ranges[start:end],
                requirements_sha256=placeholder_sha,
            )
            if (
                len(output.encode("utf-8")) > MAX_COVERAGE_PLAN_PAGE_OUTPUT_BYTES
                or token_counter(output) + REQUIREMENTS_HASH_TOKEN_VARIATION_RESERVE
                > MAX_COVERAGE_PLAN_PAGE_TOKENS
            ):
                break
            best_end = end
            end += 1
        if best_end is None:
            raise StagingError(f"one coverage row cannot fit page envelope at index {start}")
        boundaries.append((start, best_end))
        start = best_end
    page_count = len(boundaries)
    pages: list[dict[str, Any]] = []
    for page_index, (start, end) in enumerate(boundaries):
        rows = required_ranges[start:end]
        output = _render_page_output(
            page_index=page_index,
            page_count=page_count,
            rows=rows,
            requirements_sha256=placeholder_sha,
        )
        output_bytes = len(output.encode("utf-8"))
        output_tokens = token_counter(output) + REQUIREMENTS_HASH_TOKEN_VARIATION_RESERVE
        if (
            output_bytes > MAX_COVERAGE_PLAN_PAGE_OUTPUT_BYTES
            or output_tokens > MAX_COVERAGE_PLAN_PAGE_TOKENS
        ):
            raise StagingError("final coverage page exceeds byte/token envelope")
        pages.append(
            {
                "page_index": page_index,
                "start_range_index": start,
                "end_range_index_exclusive": end,
                "row_count": end - start,
                "max_row_serialized_bytes": max(len(canonical_bytes(row)) for row in rows),
                "planned_output_size_bytes": output_bytes,
                "planned_output_o200k_tokens": output_tokens,
            }
        )
    return pages


def _walk_direct_calls(value: Any, pointer: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        calls = value.get("direct_calls")
        if isinstance(calls, list):
            for index, call in enumerate(calls):
                if isinstance(call, str) and call.strip():
                    yield pointer + f"/direct_calls/{index}", call.strip()
        for key, child in value.items():
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            yield from _walk_direct_calls(child, pointer + "/" + escaped)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_direct_calls(child, pointer + f"/{index}")


def _call_leaf(node: ast.Call) -> tuple[str | None, str | None]:
    function = node.func
    if isinstance(function, ast.Name):
        return None, function.id
    if isinstance(function, ast.Attribute):
        name = function.attr
        value = function.value
        if isinstance(value, ast.Name):
            return value.id, name
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
            return value.func.id, name
        return None, name
    return None, None


def _semantic_call_leaf(value: str) -> tuple[str | None, str]:
    cleaned = value.replace("()", "").strip()
    parts = [part for part in cleaned.split(".") if part]
    if not parts:
        raise StagingError(f"empty semantic direct call: {value!r}")
    return (parts[-2] if len(parts) > 1 else None), parts[-1]


def _build_python_definition_index(
    sources: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], dict[str, ast.AST]]:
    by_name: dict[str, list[dict[str, Any]]] = {}
    definitions: list[dict[str, Any]] = []
    trees: dict[str, ast.AST] = {}
    for path, source in sources.items():
        if not path.startswith("official/") or not path.endswith(".py") or "/.venv" in path:
            continue
        try:
            tree = ast.parse(source["text"], filename=path)
        except SyntaxError as exc:
            raise StagingError(f"raw official Python source cannot be parsed: {path}: {exc}") from exc
        trees[path] = tree
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            end = getattr(node, "end_lineno", None)
            if not isinstance(end, int):
                raise StagingError(f"definition lacks end_lineno: {path}:{node.lineno}")
            row = {
                "path": path,
                "name": node.name,
                "start_line": node.lineno,
                "end_line": end,
                "kind": type(node).__name__,
                "node": node,
            }
            definitions.append(row)
            by_name.setdefault(node.name, []).append(row)
    for rows in by_name.values():
        rows.sort(
            key=lambda row: (
                row["path"],
                row["start_line"],
                row["end_line"],
            )
        )
    return by_name, definitions, trees


def _packet_module_paths(
    module_hint: str, sources: Mapping[str, Mapping[str, Any]]
) -> list[str]:
    if module_hint in {"self", "cls", "super"}:
        return []
    suffix = "/" + module_hint.replace(".", "/") + ".py"
    init_suffix = "/" + module_hint.replace(".", "/") + "/__init__.py"
    candidates = [
        path
        for path in sources
        if path.startswith("official/")
        and "/.venv" not in path
        and (path.endswith(suffix) or path.endswith(init_suffix) or Path(path).stem == module_hint)
    ]
    return sorted(set(candidates))


def expand_decisive_call_closure(
    *,
    parsed: Mapping[str, Any],
    closure_reasons: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Expand canonical anchors through packet-local AST calls to a fixed point."""

    sources = parsed["sources"]
    semantics = parsed["canonical_task_semantics"]
    selected = parsed["selected_task_source"]
    by_name, definitions, _trees = _build_python_definition_index(sources)
    pending_definitions: list[tuple[dict[str, Any], str]] = []
    pending_calls: list[tuple[str | None, str, str | None, str, bool]] = []
    seen_definitions: set[tuple[str, int, int]] = set()
    edges: list[dict[str, Any]] = []
    unresolved_external: list[dict[str, Any]] = []

    def seed_range(path: str, start: Any, end: Any, reason: str) -> None:
        if not isinstance(start, int) or not isinstance(end, int):
            return
        matches = [
            row
            for row in definitions
            if row["path"] == path
            and row["start_line"] <= end
            and row["end_line"] >= start
        ]
        # Prefer the narrowest overlapping semantic owner; class bindings are kept
        # only when no method/function is the more exact owner.
        non_classes = [row for row in matches if row["kind"] != "ClassDef"]
        if non_classes:
            smallest = min(row["end_line"] - row["start_line"] for row in non_classes)
            matches = [
                row
                for row in non_classes
                if row["end_line"] - row["start_line"] == smallest
            ]
        for row in matches:
            pending_definitions.append((row, reason))

    for document_name, document in (
        ("canonical_task_semantics", semantics),
        ("selected_task_source", selected),
    ):
        for pointer, source_ref in _walk_source_refs(document):
            path = _source_ref_path(source_ref, sources)
            seed_range(
                path,
                source_ref.get("start_line"),
                source_ref.get("end_line"),
                f"derived/{document_name}.json#{pointer}",
            )
        for pointer, direct_call in _walk_direct_calls(document):
            module_hint, name = _semantic_call_leaf(direct_call)
            pending_calls.append(
                (
                    module_hint,
                    name,
                    None,
                    f"derived/{document_name}.json#{pointer}",
                    True,
                )
            )
    for binding in _walk_source_bindings(semantics):
        path = _binding_source_path(binding, sources)
        seed_range(
            path,
            binding.get("start_line"),
            binding.get("end_line"),
            f"source_binding:{binding.get('owner_qualname')}",
        )

    while pending_definitions or pending_calls:
        while pending_definitions:
            definition, reason = pending_definitions.pop(0)
            key = (
                str(definition["path"]),
                int(definition["start_line"]),
                int(definition["end_line"]),
            )
            if key in seen_definitions:
                continue
            seen_definitions.add(key)
            path = str(definition["path"])
            closure_reasons.setdefault(path, []).append(
                {
                    "navigation_document": "packet_local_ast_call_graph",
                    "json_pointer": reason,
                    "symbol": definition["name"],
                    "bound_start_line": definition["start_line"],
                    "bound_end_line": definition["end_line"],
                }
            )
            if definition["kind"] == "ClassDef":
                continue
            for call in ast.walk(definition["node"]):
                if not isinstance(call, ast.Call):
                    continue
                module_hint, name = _call_leaf(call)
                if not name:
                    continue
                if module_hint == "super":
                    # Explicit MRO/method-chain anchors already seed inherited paths;
                    # expanding every super method name across the packet is ambiguous.
                    continue
                pending_calls.append(
                    (
                        module_hint,
                        name,
                        path,
                        f"{path}:{definition['name']}:{getattr(call, 'lineno', 0)}",
                        False,
                    )
                )

        if not pending_calls:
            continue
        module_hint, name, context_path, reason, semantic_direct = pending_calls.pop(0)
        if not semantic_direct and name in IGNORED_GENERIC_CALL_NAMES:
            continue
        candidates = list(by_name.get(name) or [])
        module_paths: list[str] = []
        if module_hint and module_hint not in {"self", "cls"}:
            module_paths = _packet_module_paths(module_hint, sources)
            if module_paths:
                narrowed = [row for row in candidates if row["path"] in module_paths]
                if narrowed:
                    candidates = narrowed
                for module_path in module_paths:
                    closure_reasons.setdefault(module_path, []).append(
                        {
                            "navigation_document": "packet_local_ast_call_graph",
                            "json_pointer": reason,
                            "symbol": f"{module_hint}.{name}",
                            "bound_start_line": None,
                            "bound_end_line": None,
                        }
                    )
        elif context_path:
            local = [row for row in candidates if row["path"] == context_path]
            if local:
                candidates = local
            elif module_hint in {"self", "cls"}:
                # A base-class dispatch not represented by the semantic method chain
                # remains ambiguous; include every same-name packet definition.
                candidates = candidates
        if candidates:
            for target in candidates:
                edges.append(
                    {
                        "from": reason,
                        "call": f"{module_hint + '.' if module_hint else ''}{name}",
                        "to_path": target["path"],
                        "to_symbol": target["name"],
                        "to_start_line": target["start_line"],
                        "to_end_line": target["end_line"],
                        "semantic_direct": semantic_direct,
                    }
                )
                pending_definitions.append((target, reason))
        elif module_paths:
            # Whole-file closure is still complete for dynamic/module-level callables.
            edges.append(
                {
                    "from": reason,
                    "call": f"{module_hint}.{name}",
                    "to_paths": module_paths,
                    "to_symbol": None,
                    "semantic_direct": semantic_direct,
                    "resolution": "whole_module_file",
                }
            )
        elif semantic_direct:
            unresolved_external.append(
                {
                    "from": reason,
                    "call": f"{module_hint + '.' if module_hint else ''}{name}",
                    "classification": "no_packet_local_module_or_definition",
                }
            )

    edges.sort(
        key=lambda row: (
            str(row["from"]),
            str(row["call"]),
            str(row.get("to_path") or row.get("to_paths")),
            str(row.get("to_symbol")),
        )
    )
    unresolved_external.sort(key=lambda row: (row["from"], row["call"]))
    return {
        "algorithm": "packet_local_ast_fixed_point_v1",
        "fixed_point_reached": True,
        "selected_definition_count": len(seen_definitions),
        "resolved_edges": edges,
        "resolved_edges_sha256": canonical_sha256(edges),
        "unresolved_external_semantic_direct_calls": unresolved_external,
        "packet_local_unresolved_count": 0,
    }


def build_coverage_requirements(
    parsed: Mapping[str, Any],
    *,
    token_counter: Callable[[str], int],
    tokenizer_binding: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind every raw-official inventory payload plus semantic cross-audits."""

    sources = parsed["sources"]
    semantics = parsed["canonical_task_semantics"]
    case_id = semantics.get("case_unit_id")
    task_id = semantics.get("task_id")
    if not isinstance(case_id, str) or not isinstance(task_id, str):
        raise StagingError("canonical semantics lacks case/task identity")
    expected_tokenizer = {
        "encoding": FROZEN_TIKTOKEN_ENCODING,
        "tiktoken_version": FROZEN_TIKTOKEN_VERSION,
        "merge_table_sha256": FROZEN_TIKTOKEN_BPE_SHA256,
    }
    if any(tokenizer_binding.get(key) != value for key, value in expected_tokenizer.items()):
        raise StagingError("coverage planner tokenizer binding is not the frozen o200k identity")
    expected_tokenizer_sha = canonical_sha256(expected_tokenizer)
    if tokenizer_binding.get("binding_sha256") != expected_tokenizer_sha:
        raise StagingError("coverage planner tokenizer self-binding is not exact")

    anchors: list[dict[str, Any]] = []
    anchor_ranges: list[dict[str, Any]] = []
    for anchor in ANCHORS:
        if anchor not in semantics:
            raise StagingError(f"canonical semantics lacks required anchor: {anchor}")
        rows: list[dict[str, Any]] = []
        seen: set[tuple[str, int, int, str]] = set()
        for binding in _walk_source_bindings(semantics[anchor]):
            path = _binding_source_path(binding, sources)
            start = binding.get("start_line")
            end = binding.get("end_line")
            snippet_sha = str(binding.get("snippet_sha256") or "")
            if not isinstance(start, int) or not isinstance(end, int) or not (1 <= start <= end):
                raise StagingError(f"invalid {anchor} source range: {binding}")
            source = sources[path]
            lines = source["text"].splitlines(keepends=True)
            if end > len(lines):
                raise StagingError(f"{anchor} source range exceeds {path}")
            observed_snippet_sha = sha256_text("".join(lines[start - 1 : end]))
            if source["sha256"] != binding.get("sha256") or observed_snippet_sha != snippet_sha:
                raise StagingError(f"{anchor} source binding hashes do not match {path}")
            key = (path, start, end, snippet_sha)
            if key in seen:
                continue
            seen.add(key)
            row = {
                "anchor": anchor,
                "raw_authority": "official_source",
                "path": path,
                "start_line": start,
                "end_line": end,
                "file_sha256": source["sha256"],
                "snippet_sha256": snippet_sha,
                "owner_module": binding.get("owner_module"),
                "owner_qualname": binding.get("owner_qualname"),
            }
            rows.append(row)
            anchor_ranges.append(row)
        rows.sort(key=lambda row: (row["path"], row["start_line"], row["end_line"]))
        if not rows:
            raise StagingError(f"required semantic anchor has no raw official source binding: {anchor}")
        anchors.append({"anchor": anchor, "required_raw_official_ranges": rows})

    metadata_path = "official/install/android_world/task_metadata.json"
    if metadata_path not in sources:
        raise StagingError("task metadata raw source is not in Source Inventory")
    metadata_source = sources[metadata_path]
    metadata_row = {
        "anchor": "metadata_task_description",
        "raw_authority": "official_source",
        "path": metadata_path,
        "start_line": 1,
        "end_line": metadata_source["line_count"],
        "file_sha256": metadata_source["sha256"],
        "snippet_sha256": metadata_source["sha256"],
        "owner_module": None,
        "owner_qualname": task_id,
    }
    anchors.insert(
        0,
        {
            "anchor": "metadata_task_description",
            "required_raw_official_ranges": [metadata_row],
        },
    )
    anchor_ranges.append(metadata_row)
    anchor_ranges.sort(
        key=lambda row: (row["anchor"], row["path"], row["start_line"], row["end_line"])
    )

    closure_reasons: dict[str, list[dict[str, Any]]] = {}
    for document_name, document in (
        ("canonical_task_semantics", semantics),
        ("selected_task_source", parsed["selected_task_source"]),
    ):
        for pointer, source_ref in _walk_source_refs(document):
            path = _source_ref_path(source_ref, sources)
            closure_reasons.setdefault(path, []).append(
                {
                    "navigation_document": f"derived/{document_name}.json",
                    "json_pointer": pointer,
                    "symbol": source_ref.get("symbol"),
                    "bound_start_line": source_ref.get("start_line"),
                    "bound_end_line": source_ref.get("end_line"),
                }
            )
    closure_reasons.setdefault(metadata_path, []).append(
        {
            "navigation_document": "derived/canonical_task_semantics.json",
            "json_pointer": "/raw_metadata/source_ref",
            "symbol": task_id,
            "bound_start_line": None,
            "bound_end_line": None,
        }
    )
    registry_path = "official/install/android_world/registry.py"
    if registry_path not in sources:
        raise StagingError("runtime task registry raw source is not in Source Inventory")
    closure_reasons.setdefault(registry_path, []).append(
        {
            "navigation_document": "runtime_dispatch_requirement",
            "json_pointer": "/registry",
            "symbol": case_id,
            "bound_start_line": None,
            "bound_end_line": None,
        }
    )
    # Source-binding extraction is independently mapped as a second completeness
    # route.  This catches a source_ref projection regression before generation.
    for anchor in anchors:
        for row in anchor["required_raw_official_ranges"]:
            closure_reasons.setdefault(row["path"], []).append(
                {
                    "navigation_document": "derived/canonical_task_semantics.json",
                    "json_pointer": f"/anchors/{anchor['anchor']}",
                    "symbol": row.get("owner_qualname"),
                    "bound_start_line": row["start_line"],
                    "bound_end_line": row["end_line"],
                }
            )
    call_graph = expand_decisive_call_closure(
        parsed=parsed,
        closure_reasons=closure_reasons,
    )
    if (
        call_graph.get("fixed_point_reached") is not True
        or call_graph.get("packet_local_unresolved_count") != 0
    ):
        raise StagingError("packet-local decisive call closure did not reach an exact fixed point")
    # Full-safe trust boundary: semantic/AST navigation may add reasons, but it is
    # never allowed to select or exclude raw sources.  Every raw official Inventory
    # member belongs to exactly one SHA group.  A byte-identical group is read once
    # physically only after every logical alias has been explicitly bound.
    raw_inventory_paths = [
        path for path in parsed["inventory"] if str(path).startswith("official/")
    ]
    if not raw_inventory_paths:
        raise StagingError("Source Inventory contains no raw official member")
    grouped_paths: dict[str, list[str]] = {}
    for path in raw_inventory_paths:
        grouped_paths.setdefault(str(sources[path]["sha256"]), []).append(path)
    if set(closure_reasons) - set(raw_inventory_paths):
        raise StagingError("semantic/AST closure named a path outside raw official Inventory")

    physical_groups: list[tuple[str, str, list[str]]] = []
    for content_sha, aliases in grouped_paths.items():
        ordered_aliases = sorted(aliases)
        representative = min(
            ordered_aliases,
            key=lambda value: ("/.venv" in value, value),
        )
        if any(sources[path]["sha256"] != content_sha for path in ordered_aliases):
            raise StagingError("logical alias group does not share one exact content hash")
        physical_groups.append((representative, content_sha, ordered_aliases))
    physical_groups.sort(key=lambda row: row[0])

    required_ranges: list[dict[str, Any]] = []
    raw_closure: list[dict[str, Any]] = []
    bound_aliases: list[str] = []
    for path, content_sha, logical_aliases in physical_groups:
        source = sources[path]
        chunks = _complete_file_chunks(
            path=path,
            source=source,
            logical_aliases=logical_aliases,
            token_counter=token_counter,
        )
        for index, chunk in enumerate(chunks):
            chunk["chunk_index"] = index
            chunk["chunk_count"] = len(chunks)
        navigation_rows = [
            row
            for alias in logical_aliases
            for row in closure_reasons.get(alias, [])
        ]
        unique_reasons = {canonical_sha256(row): row for row in navigation_rows}
        reasons = sorted(
            unique_reasons.values(),
            key=lambda row: (
                str(row["navigation_document"]),
                str(row["json_pointer"]),
                str(row.get("symbol")),
                int(row.get("bound_start_line") or 0),
            ),
        )
        closure_row = {
            "path": path,
            "physical_read_path": path,
            "file_sha256": content_sha,
            "size_bytes": source["size_bytes"],
            "line_count": source["line_count"],
            "logical_aliases": logical_aliases,
            "logical_alias_count": len(logical_aliases),
            "logical_alias_bindings": [
                {
                    "path": alias,
                    "file_sha256": sources[alias]["sha256"],
                    "size_bytes": sources[alias]["size_bytes"],
                    "line_count": sources[alias]["line_count"],
                    "source_ref": sources[alias]["source_ref"],
                }
                for alias in logical_aliases
            ],
            "chunks": chunks,
            "navigation_reasons": reasons,
        }
        raw_closure.append(closure_row)
        bound_aliases.extend(logical_aliases)
        for chunk in chunks:
            required_ranges.append(
                {
                    "anchor": "raw_source_closure_chunk",
                    "raw_authority": "official_source",
                    "path": path,
                    "logical_aliases": logical_aliases,
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                    "file_sha256": content_sha,
                    "snippet_sha256": chunk["snippet_sha256"],
                    "snippet_ends_with_newline": chunk[
                        "snippet_ends_with_newline"
                    ],
                    "chunk_index": chunk["chunk_index"],
                    "chunk_count": chunk["chunk_count"],
                    "chunk_size_bytes": chunk["size_bytes"],
                    "owner_module": None,
                    "owner_qualname": "complete_file_chunk",
                }
            )
    if (
        sorted(bound_aliases) != sorted(raw_inventory_paths)
        or len(bound_aliases) != len(set(bound_aliases))
        or any(path not in bound_aliases for path in raw_inventory_paths)
    ):
        raise StagingError("raw official Inventory aliases are omitted or multiply bound")
    if not raw_closure or len(raw_closure) != len(grouped_paths):
        raise StagingError("full-safe raw official physical closure is not exact")

    coverage_pages = _pack_coverage_pages(
        required_ranges,
        token_counter=token_counter,
    )

    navigation = {
        "canonical_module": semantics.get("canonical_module"),
        "canonical_source_file": semantics.get("canonical_source_file"),
        "runtime_reported_class": semantics.get("runtime_reported_class"),
        "runtime_reported_module": semantics.get("runtime_reported_module"),
        "readiness": semantics.get("readiness"),
        "metadata_conflicts": semantics.get("metadata_conflicts"),
        "metadata_comparison_status": (semantics.get("metadata_comparison") or {}).get(
            "status"
        ),
        "record_sha256": semantics.get("record_sha256"),
    }
    payload = {
        "schema_version": "androidworld_candidate116_staged_source_coverage_requirements/v1",
        "production_namespace": PRODUCTION_NAMESPACE,
        "case_unit_id": case_id,
        "task_id": task_id,
        "policy": {
            "derived_role": "navigation_identity_closure_and_conflict_only",
            "runtime_semantics_authority": "raw_official_source_ranges",
            "required_anchors": ["metadata_task_description", *ANCHORS],
            "every_distinct_raw_official_inventory_payload_must_be_read_completely": True,
            "raw_inventory_members_may_never_be_excluded_by_navigation_or_ast": True,
            "byte_identical_aliases_share_one_physical_read_only_when_hash_bound": True,
            "max_coverage_chunk_bytes": MAX_COVERAGE_CHUNK_BYTES,
            "max_reader_envelope_bytes": MAX_READER_ENVELOPE_BYTES,
            "max_reader_envelope_o200k_tokens": MAX_READER_ENVELOPE_TOKENS,
            "max_plan_row_serialized_bytes": MAX_COVERAGE_PLAN_ROW_BYTES,
            "max_plan_page_output_bytes": MAX_COVERAGE_PLAN_PAGE_OUTPUT_BYTES,
            "max_plan_page_o200k_tokens": MAX_COVERAGE_PLAN_PAGE_TOKENS,
            "chunks_must_be_read_separately_in_listed_order": True,
            "recursive_source_ref_mapping_missing_count": 0,
            "source_binding_mapping_missing_count": 0,
            "case_packet_one_shot_read_forbidden": True,
        },
        "derived_navigation": navigation,
        "tokenizer_binding": dict(tokenizer_binding),
        "anchors": anchors,
        "anchor_raw_official_ranges": anchor_ranges,
        "raw_official_source_closure": raw_closure,
        "raw_official_source_closure_count": len(raw_closure),
        "raw_official_inventory_member_count": len(raw_inventory_paths),
        "raw_official_distinct_sha_count": len(grouped_paths),
        "raw_official_omitted_count": 0,
        "raw_official_inventory_aliases_sha256": canonical_sha256(raw_inventory_paths),
        "decisive_call_closure": call_graph,
        "source_closure_audit": {
            "method": "all_raw_official_inventory_members_exhaustively_bound_before_ast_audit",
            "unresolved_internal_imports": [],
            "unresolved_internal_import_count": 0,
            "plan_member_count": len(raw_inventory_paths),
            "plan_distinct_content_count": len(grouped_paths),
        },
        "required_ranges": required_ranges,
        "required_range_count": len(required_ranges),
        "coverage_pagination": "serialized_byte_and_o200k_token_envelope_v1",
        "coverage_pages": coverage_pages,
        "coverage_page_count": len(coverage_pages),
    }
    payload["requirements_sha256"] = canonical_sha256(payload)
    return payload


def _reader_source() -> str:
    """Return the frozen reader program materialized into each case workspace."""

    return r'''#!/usr/bin/env python3
import argparse, hashlib, json, pathlib, sys

BODY_PREFIX = "WAVE004_READER_BODY "
COMPLETION_PREFIX = "WAVE004_READER_COMPLETE "
root = pathlib.Path(__file__).resolve().parent
requirements_path = root / "model_input_coverage.json"
requirements = json.loads(requirements_path.read_text(encoding="utf-8"))

def canonical_sha256(value):
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()

def enveloped(kind, argv, body):
    if not body.endswith("\n"):
        raise SystemExit("reader body lacks terminal newline")
    completion = {
        "argv_sha256": canonical_sha256(argv),
        "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "body_size_bytes": len(body.encode("utf-8")),
        "kind": kind,
        "requirements_sha256": requirements["requirements_sha256"],
    }
    return body + COMPLETION_PREFIX + json.dumps(
        completion, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ) + "\n"

parser = argparse.ArgumentParser()
sub = parser.add_subparsers(dest="command", required=True)
sub.add_parser("overview")
sub.add_parser("header")
page = sub.add_parser("plan-page")
page.add_argument("--page", required=True, type=int)
page.add_argument("--manifest-sha256", required=True)
read = sub.add_parser("read")
read.add_argument("--anchor", required=True)
read.add_argument("--path", required=True)
read.add_argument("--start", required=True, type=int)
read.add_argument("--end", required=True, type=int)
read.add_argument("--manifest-sha256", required=True)
args = parser.parse_args()

if args.command == "overview":
    summary = {key: requirements[key] for key in (
        "schema_version", "production_namespace", "case_unit_id", "task_id", "policy",
        "requirements_sha256", "required_range_count", "coverage_page_count",
        "raw_official_source_closure_count", "raw_official_inventory_member_count",
        "raw_official_distinct_sha_count", "raw_official_omitted_count",
        "derived_navigation", "anchors")}
    argv = ["/usr/bin/python3", "packet_reader.py", "overview"]
    body = BODY_PREFIX + json.dumps(
        {"kind": "overview"}, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")) + "\n"
    body += json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    sys.stdout.write(enveloped("overview", argv, body))
    raise SystemExit(0)

if args.command == "header":
    packet = (root / "case_packet.md").read_bytes()
    if hashlib.sha256(packet).hexdigest() != requirements["case_packet_sha256"]:
        raise SystemExit("case packet hash mismatch")
    text = packet.decode("utf-8")
    marker = "## Packet Source Files\n"
    if text.count(marker) != 1:
        raise SystemExit("case packet header boundary is not exact")
    header = text.split(marker, 1)[0]
    argv = ["/usr/bin/python3", "packet_reader.py", "header"]
    body = BODY_PREFIX + json.dumps(
        {"case_packet_sha256": requirements["case_packet_sha256"], "kind": "header"},
        ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    body += header if header.endswith("\n") else header + "\n"
    sys.stdout.write(enveloped("header", argv, body))
    raise SystemExit(0)

if args.manifest_sha256 != requirements["requirements_sha256"]:
    raise SystemExit("requirements hash mismatch")
if args.command == "plan-page":
    if not 0 <= args.page < requirements["coverage_page_count"]:
        raise SystemExit("coverage page index is out of range")
    page_record = requirements["coverage_pages"][args.page]
    if page_record["page_index"] != args.page:
        raise SystemExit("coverage page record order changed")
    start = page_record["start_range_index"]
    end = page_record["end_range_index_exclusive"]
    rows = requirements["required_ranges"][start:end]
    if len(rows) != page_record["row_count"]:
        raise SystemExit("coverage page boundary changed")
    page_payload = {"page_index": args.page,
                    "page_count": requirements["coverage_page_count"],
                    "requirements_sha256": requirements["requirements_sha256"],
                    "rows": rows}
    argv = ["/usr/bin/python3", "packet_reader.py", "plan-page", "--page",
            str(args.page), "--manifest-sha256", requirements["requirements_sha256"]]
    body = BODY_PREFIX + json.dumps(
        {"kind": "plan-page", "page_index": args.page,
         "page_count": requirements["coverage_page_count"]},
        ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    body += json.dumps(page_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    output = enveloped("plan-page", argv, body)
    if len(output.encode("utf-8")) > requirements["policy"]["max_plan_page_output_bytes"]:
        raise SystemExit("coverage plan page exceeds frozen output byte limit")
    sys.stdout.write(output)
    raise SystemExit(0)
matches = [row for row in requirements["required_ranges"] if
           row["anchor"] == args.anchor and row["path"] == args.path and
           row["start_line"] == args.start and row["end_line"] == args.end]
if len(matches) != 1:
    raise SystemExit("requested range is not one exact coverage requirement")
row = matches[0]
source = root / "packet_sources" / pathlib.PurePosixPath(args.path)
if source.is_symlink() or not source.is_file():
    raise SystemExit("materialized source missing or symlinked")
data = source.read_bytes()
if hashlib.sha256(data).hexdigest() != row["file_sha256"]:
    raise SystemExit("materialized source hash mismatch")
text = data.decode("utf-8")
lines = text.splitlines(keepends=True)
snippet = "".join(lines[args.start - 1:args.end])
if hashlib.sha256(snippet.encode("utf-8")).hexdigest() != row["snippet_sha256"]:
    raise SystemExit("materialized source range hash mismatch")
identity = {key: row[key] for key in (
    "anchor", "path", "start_line", "end_line", "file_sha256",
    "snippet_sha256", "chunk_size_bytes", "snippet_ends_with_newline",
    "chunk_index", "chunk_count")}
argv = ["/usr/bin/python3", "packet_reader.py", "read", "--anchor", args.anchor,
        "--path", args.path, "--start", str(args.start), "--end", str(args.end),
        "--manifest-sha256", requirements["requirements_sha256"]]
body = BODY_PREFIX + json.dumps(
    {"kind": "read", "identity": identity}, ensure_ascii=False, sort_keys=True,
    separators=(",", ":")) + "\n"
body += snippet
if not snippet.endswith("\n"):
    body += "\n"
output = enveloped("read", argv, body)
if len(output.encode("utf-8")) > requirements["policy"]["max_reader_envelope_bytes"]:
    raise SystemExit("raw-source reader envelope exceeds frozen output byte limit")
sys.stdout.write(output)
'''


def _write_new(path: Path, data: bytes, mode: int) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise StagingError(f"create-once staged path already exists: {path}")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            path.unlink()
        except OSError:
            pass
        raise
    os.chmod(path, mode)
    return {
        "relative_path": path.name,
        "sha256": sha256_bytes(data),
        "size_bytes": len(data),
        "mode": mode,
    }


def materialize_case_workspace(
    workspace_root: Path,
    *,
    case_packet_text: str,
    model_output_schema: Mapping[str, Any],
    token_counter: Callable[[str], int],
    tokenizer_binding: Mapping[str, Any],
) -> dict[str, Any]:
    """Create the exact per-case namespace and seal all model inputs read-only."""

    if workspace_root.is_symlink() or not workspace_root.is_dir() or any(workspace_root.iterdir()):
        raise StagingError("case workspace must be a new empty non-symlink directory")
    parsed = parse_packet_sources(case_packet_text)
    requirements = build_coverage_requirements(
        parsed,
        token_counter=token_counter,
        tokenizer_binding=tokenizer_binding,
    )
    requirements["case_packet_sha256"] = sha256_text(case_packet_text)
    requirements["source_inventory"] = [
        {
            key: parsed["sources"][path][key]
            for key in ("path", "sha256", "size_bytes", "line_count")
        }
        for path in parsed["inventory"]
    ]
    requirements.pop("requirements_sha256", None)
    requirements["requirements_sha256"] = canonical_sha256(requirements)
    operation_expectations = build_reader_operation_expectations(
        case_packet_text=case_packet_text,
        parsed=parsed,
        requirements=requirements,
        token_counter=token_counter,
    )
    verify_reader_operation_expectations_binding(requirements, operation_expectations)
    files: list[dict[str, Any]] = []

    def write(relative: str, data: bytes, mode: int = 0o444) -> None:
        path = workspace_root / PurePosixPath(safe_source_path(relative))
        row = _write_new(path, data, mode)
        row["relative_path"] = relative
        files.append(row)

    write("case_packet.md", case_packet_text.encode("utf-8"))
    for source_path in parsed["inventory"]:
        write(
            f"packet_sources/{source_path}",
            parsed["sources"][source_path]["text"].encode("utf-8"),
        )
    inventory_manifest = {
        "schema_version": "androidworld_candidate116_materialized_source_inventory/v1",
        "case_unit_id": requirements["case_unit_id"],
        "packet_sha256": sha256_text(case_packet_text),
        "source_count": len(parsed["inventory"]),
        "source_order": parsed["inventory"],
        "sources": [
            {
                key: parsed["sources"][path][key]
                for key in ("path", "source_ref", "language", "sha256", "size_bytes", "line_count")
            }
            for path in parsed["inventory"]
        ],
    }
    inventory_manifest["inventory_sha256"] = canonical_sha256(inventory_manifest)
    write(
        "source_inventory_manifest.json",
        json.dumps(inventory_manifest, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        + b"\n",
    )
    write(
        "model_input_coverage.json",
        json.dumps(requirements, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        + b"\n",
    )
    write(
        "reader_operation_expectations.json",
        json.dumps(
            operation_expectations, ensure_ascii=False, indent=2, sort_keys=True
        ).encode("utf-8")
        + b"\n",
    )
    write("packet_reader.py", _reader_source().encode("utf-8"))
    schema_bytes = (
        json.dumps(model_output_schema, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        + b"\n"
    )
    write("output_schema.json", schema_bytes)
    write("draft_body.json", b"", 0o600)
    files.sort(key=lambda row: row["relative_path"])
    manifest = {
        "schema_version": "androidworld_candidate116_case_workspace_materialization/v1",
        "production_namespace": PRODUCTION_NAMESPACE,
        "case_unit_id": requirements["case_unit_id"],
        "task_id": requirements["task_id"],
        "packet_sha256": sha256_text(case_packet_text),
        "requirements_sha256": requirements["requirements_sha256"],
        "reader_operation_expectations_sha256": operation_expectations[
            "reader_operation_expectations_sha256"
        ],
        "inventory_sha256": inventory_manifest["inventory_sha256"],
        "input_files": [row for row in files if row["relative_path"] != "draft_body.json"],
        "output_file": next(row for row in files if row["relative_path"] == "draft_body.json"),
        "allowed_namespace": [row["relative_path"] for row in files],
        "full_packet_present": True,
        "full_packet_in_stdin": False,
        "materialized_source_count": len(parsed["inventory"]),
    }
    manifest["materialization_sha256"] = canonical_sha256(manifest)
    write(
        "workspace_materialization.json",
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        + b"\n",
    )
    manifest["allowed_namespace"] = sorted(
        [*manifest["allowed_namespace"], "workspace_materialization.json"]
    )
    manifest["workspace_manifest_file_sha256"] = sha256_text(
        (workspace_root / "workspace_materialization.json").read_text(encoding="utf-8")
    )
    # The self-hash covers the semantic materialization payload written above; the
    # two readback-only fields deliberately bind the physical manifest file without
    # introducing a recursive file/self-hash definition.
    seal_case_workspace(workspace_root, manifest)
    return manifest | {
        "coverage_requirements": requirements,
        "reader_operation_expectations": operation_expectations,
    }


def seal_case_workspace(workspace_root: Path, manifest: Mapping[str, Any]) -> None:
    for row in manifest["input_files"]:
        os.chmod(workspace_root / row["relative_path"], 0o444)
    os.chmod(workspace_root / "workspace_materialization.json", 0o444)
    os.chmod(workspace_root / "draft_body.json", 0o600)
    for path in sorted(
        (item for item in workspace_root.rglob("*") if item.is_dir()),
        key=lambda item: len(item.parts),
        reverse=True,
    ):
        os.chmod(path, 0o555)
    os.chmod(workspace_root, 0o555)


def verify_case_workspace(
    workspace_root: Path, manifest: Mapping[str, Any], *, require_output: bool
) -> None:
    allowed = set(manifest["allowed_namespace"])
    observed: set[str] = set()
    for path in workspace_root.rglob("*"):
        if path.is_symlink():
            raise StagingError(f"symlink appeared in case workspace: {path}")
        if path.is_file():
            observed.add(path.relative_to(workspace_root).as_posix())
    if observed != allowed:
        raise StagingError(f"case workspace namespace changed: {sorted(observed ^ allowed)}")
    for row in manifest["input_files"]:
        path = workspace_root / row["relative_path"]
        if (
            sha256_bytes(path.read_bytes()) != row["sha256"]
            or path.stat().st_size != row["size_bytes"]
            or stat.S_IMODE(path.stat().st_mode) != 0o444
        ):
            raise StagingError(f"immutable staged input changed: {row['relative_path']}")
    manifest_path = workspace_root / "workspace_materialization.json"
    if (
        sha256_text(manifest_path.read_text(encoding="utf-8"))
        != manifest["workspace_manifest_file_sha256"]
        or stat.S_IMODE(manifest_path.stat().st_mode) != 0o444
    ):
        raise StagingError("workspace materialization manifest changed")
    output = workspace_root / "draft_body.json"
    if require_output and output.stat().st_size == 0:
        raise StagingError("Codex did not write draft_body.json")


def verify_workspace_against_frozen_reader_coverage(
    workspace_root: Path,
    frozen_case_root: Path,
    materialization: Mapping[str, Any],
) -> dict[str, Any]:
    """Require runtime A/B bytes to equal the independently frozen clean4 pair."""

    case_id = str(materialization.get("case_unit_id") or "")
    if not SAFE_CASE_ID_RE.fullmatch(case_id) or frozen_case_root.name != case_id:
        raise StagingError("frozen A/B case identity/path is invalid")
    if (
        frozen_case_root.is_symlink()
        or not frozen_case_root.is_dir()
        or stat.S_IMODE(frozen_case_root.stat().st_mode) != 0o555
    ):
        raise StagingError("frozen A/B case root is not a sealed 0555 directory")
    expected_names = [
        "model_input_coverage.json",
        "reader_operation_expectations.json",
    ]
    if sorted(path.name for path in frozen_case_root.iterdir()) != expected_names:
        raise StagingError("frozen A/B case namespace is not exact")
    workspace_paths = [workspace_root / name for name in expected_names]
    frozen_paths = [frozen_case_root / name for name in expected_names]
    for label, workspace_path, frozen_path in zip(
        expected_names, workspace_paths, frozen_paths, strict=True
    ):
        if (
            workspace_path.is_symlink()
            or frozen_path.is_symlink()
            or not workspace_path.is_file()
            or not frozen_path.is_file()
            or stat.S_IMODE(workspace_path.stat().st_mode) != 0o444
            or stat.S_IMODE(frozen_path.stat().st_mode) != 0o444
            or workspace_path.read_bytes() != frozen_path.read_bytes()
        ):
            raise StagingError(f"runtime/frozen A/B bytes or modes differ: {label}")
    try:
        requirements = json.loads(workspace_paths[0].read_text(encoding="utf-8"))
        operations = json.loads(workspace_paths[1].read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StagingError("runtime/frozen A/B JSON cannot be read exactly") from exc
    if not isinstance(requirements, dict) or not isinstance(operations, dict):
        raise StagingError("runtime/frozen A/B JSON is not object-shaped")
    verify_reader_operation_expectations_binding(requirements, operations)
    if (
        requirements.get("requirements_sha256")
        != materialization.get("requirements_sha256")
        or operations.get("reader_operation_expectations_sha256")
        != materialization.get("reader_operation_expectations_sha256")
        or requirements != materialization.get("coverage_requirements")
        or operations != materialization.get("reader_operation_expectations")
    ):
        raise StagingError("runtime/frozen A/B objects differ from materialization")
    return {
        "schema_version": (
            "androidworld_candidate116_runtime_frozen_reader_coverage_readback/"
            "v6_clean4_hardened"
        ),
        "production_namespace": PRODUCTION_NAMESPACE,
        "case_unit_id": case_id,
        "frozen_case_root": str(frozen_case_root.resolve(strict=True)),
        "requirements_sha256": requirements["requirements_sha256"],
        "reader_operation_expectations_sha256": operations[
            "reader_operation_expectations_sha256"
        ],
        "workspace_A_B_byte_equal_to_frozen": True,
        "workspace_and_frozen_modes": "0444_files_under_0555_frozen_case_root",
        "A_B_gate_passed_before_model_call": True,
    }


def unseal_case_workspace_for_cleanup(workspace_root: Path) -> None:
    for path in sorted(
        (item for item in workspace_root.rglob("*") if item.is_dir()),
        key=lambda item: len(item.parts),
    ):
        os.chmod(path, 0o700)
    os.chmod(workspace_root, 0o700)
    for path in workspace_root.rglob("*"):
        if path.is_file():
            os.chmod(path, 0o600)


def staged_prompt(
    *, instructions: str, template_text: str, manifest: Mapping[str, Any]
) -> str:
    requirements = manifest["coverage_requirements"]
    operation_expectations = manifest.get("reader_operation_expectations")
    if not isinstance(operation_expectations, Mapping):
        raise StagingError("staged prompt lacks frozen reader operation expectations")
    verify_reader_operation_expectations_binding(
        requirements, operation_expectations
    )
    return (
        "Draft exactly one AndroidWorld checklist body as JSON. The full canonical packet is "
        "present unchanged as case_packet.md but may exceed one-shot context: NEVER cat, print, "
        "or read that whole file at once, and do not treat derived/* as runtime authority.\n\n"
        "Use only the read-only packet_reader.py protocol. First run `/usr/bin/python3 "
        "packet_reader.py overview`, then `/usr/bin/python3 packet_reader.py header`. "
        "The overview includes the exact semantic anchor line ranges; the header reads only "
        "the packet Case Metadata and Source Inventory, never the bulk embedded sources. Do "
        "not cat/print model_input_coverage.json. Read every bounded plan "
        "page in increasing order with `/usr/bin/python3 packet_reader.py plan-page --page N "
        "--manifest-sha256 "
        + requirements["requirements_sha256"]
        + "`. Then, for EVERY row on those pages, in listed order, run exactly:\n"
        "`/usr/bin/python3 packet_reader.py read --anchor <anchor> --path <path> --start "
        "<start_line> --end <end_line> --manifest-sha256 "
        + requirements["requirements_sha256"]
        + "`\n"
        "Read each returned raw official source range completely. Its body is the byte-exact "
        "raw source slice without per-line decoration; use the plan/overview start and end "
        "lines for citations. The frozen plan exhaustively "
        "covers every distinct raw official/... Source Inventory payload and binds every logical "
        "alias sharing its content hash. There is no inspect command or dynamic exception. If an "
        "internal decisive dependency is outside the Inventory/plan, the wrapper must reject the "
        "attempt; do not guess or work around it. derived/* may navigate identity, closure, or "
        "recorded conflicts only. Goal, parameters/schema, initialize_task, "
        "is_successful/evaluator, helpers, and runner semantics must be supported by exact "
        "official/... Source Inventory paths. A rationale is never a substitute for support. "
        "Do not write or modify files; the CLI alone writes draft_body.json. Return JSON only.\n\n"
        "<<<BEGIN FROZEN BASE PLUS CLEAN STAGED INSTRUCTIONS>>>\n"
        + instructions.rstrip()
        + "\n<<<END FROZEN BASE PLUS CLEAN STAGED INSTRUCTIONS>>>\n\n"
        "<<<BEGIN FROZEN TEMPLATE>>>\n"
        + template_text.rstrip()
        + "\n<<<END FROZEN TEMPLATE>>>\n\n"
        "Case identity: "
        + requirements["case_unit_id"]
        + " / "
        + requirements["task_id"]
        + "\nCoverage requirements SHA-256: "
        + requirements["requirements_sha256"]
        + "\nReader operation expectations SHA-256: "
        + operation_expectations["reader_operation_expectations_sha256"]
        + "\nExact required reader operation count: "
        + str(operation_expectations["operation_count"])
        + "\n"
    )


def _required_reader_argv(row: Mapping[str, Any], requirements_sha256: str) -> list[str]:
    return _read_argv(row, requirements_sha256)


def _required_page_argv(page: int, requirements_sha256: str) -> list[str]:
    return _page_argv(page, requirements_sha256)


def _ordered_completed_command_records(
    events: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    """Trust only ordered item.completed command records and their own stdout."""

    seen_ids: set[str] = set()
    active: tuple[str, str] | None = None
    completed: list[dict[str, str]] = []
    for event in events:
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") != "command_execution":
            continue
        item_id = item.get("id")
        command = item.get("command")
        if not isinstance(item_id, str) or not item_id or not isinstance(command, str) or not command:
            raise StagingError("command execution event lacks one stable id/exact command")
        if event.get("type") == "item.started":
            if active is not None:
                raise StagingError("packet-reader command executions overlap")
            if item_id in seen_ids:
                raise StagingError("one command id is reused after start/completion")
            seen_ids.add(item_id)
            active = (item_id, command)
            continue
        if event.get("type") != "item.completed":
            raise StagingError("command execution event is neither started nor completed")
        if active != (item_id, command):
            raise StagingError("command completion lacks its exact active same-id start")
        if item.get("status") != "completed" or item.get("exit_code") != 0:
            raise StagingError("packet-reader item.completed is not status=completed/exit_code=0")
        output = item.get("aggregated_output")
        if not isinstance(output, str):
            raise StagingError("packet-reader item.completed lacks its own aggregated_output")
        completed.append({"id": item_id, "command": command, "output": output})
        active = None
    if not completed or active is not None or len(seen_ids) != len(completed):
        raise StagingError(
            "a command execution id lacks exactly one start and successful completion"
        )
    return completed


def _verify_completed_envelope(
    *, output: str, kind: str, argv: Sequence[str], requirements_sha256: str
) -> tuple[str, dict[str, Any]]:
    """Verify an untruncated body and the unique terminal completion hash."""

    if not output.endswith("\n"):
        raise StagingError("reader aggregated_output lacks its terminal newline")
    prefix = READER_COMPLETION_PREFIX
    marker_start = output.rfind("\n" + prefix)
    if marker_start < 0:
        raise StagingError("reader aggregated_output lacks a terminal completion marker")
    body = output[: marker_start + 1]
    marker_line = output[marker_start + 1 : -1]
    if prefix in body or "\n" in marker_line or not marker_line.startswith(prefix):
        raise StagingError("reader completion marker is missing, duplicated, or not terminal")
    try:
        completion = json.loads(marker_line[len(prefix) :])
    except json.JSONDecodeError as exc:
        raise StagingError("reader terminal completion marker is invalid JSON") from exc
    expected = {
        "argv_sha256": canonical_sha256(list(argv)),
        "body_sha256": sha256_text(body),
        "body_size_bytes": len(body.encode("utf-8")),
        "kind": kind,
        "requirements_sha256": requirements_sha256,
    }
    if completion != expected:
        raise StagingError("reader terminal completion proof does not bind its exact body/argv")
    return body, completion


def _expected_body_prefix(kind: str, **values: Any) -> str:
    return READER_BODY_PREFIX + json.dumps(
        {"kind": kind, **values},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def coverage_receipt_from_events(
    events: list[dict[str, Any]],
    requirements: Mapping[str, Any],
    operation_expectations: Mapping[str, Any],
) -> dict[str, Any]:
    """Replay the exact layer-B ledger using only same-ID completed outputs."""

    verify_reader_operation_expectations_binding(requirements, operation_expectations)
    required = list(requirements.get("required_ranges") or [])
    requirements_sha = str(requirements.get("requirements_sha256") or "")
    expected_operations = list(operation_expectations.get("operations") or [])
    if len(requirements_sha) != 64 or not required or not expected_operations:
        raise StagingError("coverage requirements/reader operations are empty or unbound")
    records = _ordered_completed_command_records(events)
    if len(records) != len(expected_operations):
        raise StagingError("completed command count differs from the frozen layer-B ledger")

    completed_operations: list[dict[str, Any]] = []
    covered_ranges: list[dict[str, Any]] = []
    command_event_ids: list[str] = []
    for record, operation in zip(records, expected_operations, strict=True):
        kind = str(operation.get("kind") or "")
        expected_argv = operation.get("argv")
        if not isinstance(expected_argv, list) or not all(
            isinstance(token, str) for token in expected_argv
        ):
            raise StagingError("layer-B reader argv is not an exact string list")
        if record["command"] != operation.get("exact_command"):
            raise StagingError(
                "reader command differs from layer B (wrappers/chains/pipelines forbidden)"
            )
        body, completion = _verify_completed_envelope(
            output=record["output"],
            kind=kind,
            argv=expected_argv,
            requirements_sha256=requirements_sha,
        )
        output_bytes = len(record["output"].encode("utf-8"))
        if (
            sha256_text(record["output"])
            != operation.get("expected_full_output_sha256")
            or output_bytes != operation.get("expected_full_output_size_bytes")
            or output_bytes > int(operation.get("max_full_output_size_bytes") or 0)
            or sha256_text(body) != operation.get("body_sha256")
            or len(body.encode("utf-8")) != operation.get("body_size_bytes")
            or body.count("\n") != operation.get("body_line_count")
            or completion != operation.get("terminal_completion")
        ):
            raise StagingError("completed aggregated_output differs from exact layer-B identity")
        command_event_ids.append(record["id"])
        completed_operations.append(
            {
                "operation_index": operation["operation_index"],
                "kind": kind,
                "operation_sha256": operation["operation_sha256"],
                "completed_event_id": record["id"],
                "argv_sha256": operation["argv_sha256"],
                "event_command_sha256": operation["event_command_sha256"],
                "expected_output_sha256": operation["expected_full_output_sha256"],
                "observed_output_sha256": sha256_text(record["output"]),
                "observed_output_size_bytes": output_bytes,
                "completion_proof": completion,
            }
        )
        if kind != "read":
            continue
        identity = operation.get("semantic_identity")
        if not isinstance(identity, Mapping):
            raise StagingError("read operation lacks its frozen semantic identity")
        range_index = identity.get("range_index")
        if not isinstance(range_index, int) or not 0 <= range_index < len(required):
            raise StagingError("read operation range index is invalid")
        row = required[range_index]
        if identity.get("range_sha256") != canonical_sha256(row):
            raise StagingError("read operation does not bind its exact layer-A range")
        reader_identity = {
            key: row[key]
            for key in (
                "anchor",
                "path",
                "start_line",
                "end_line",
                "file_sha256",
                "snippet_sha256",
                "chunk_size_bytes",
                "snippet_ends_with_newline",
                "chunk_index",
                "chunk_count",
            )
        }
        if not body.startswith(_expected_body_prefix("read", identity=reader_identity)):
            raise StagingError("read output body identity differs from layer A/B")
        raw_snippet = body.split("\n", 1)[1]
        if row["snippet_ends_with_newline"] is not True:
            if not raw_snippet.endswith("\n"):
                raise StagingError("non-newline source range lacks envelope terminator")
            raw_snippet = raw_snippet[:-1]
        if (
            len(raw_snippet.encode("utf-8")) != int(row["chunk_size_bytes"])
            or sha256_text(raw_snippet) != row["snippet_sha256"]
        ):
            raise StagingError("read body is truncated or differs from layer-A raw bytes")
        covered_ranges.append(
            {
                "range_index": range_index,
                "anchor": row["anchor"],
                "path": row["path"],
                "logical_aliases": row["logical_aliases"],
                "start_line": row["start_line"],
                "end_line": row["end_line"],
                "file_sha256": row["file_sha256"],
                "snippet_sha256": row["snippet_sha256"],
                "reader_argv_sha256": operation["argv_sha256"],
                "completed_event_id": record["id"],
                "completed_output_sha256": sha256_text(record["output"]),
                "completion_proof": completion,
            }
        )

    expected_range_indexes = list(range(len(required)))
    if [row["range_index"] for row in covered_ranges] != expected_range_indexes:
        raise StagingError("covered read ranges are not the exact ordered layer-A sequence")
    if len(command_event_ids) != len(set(command_event_ids)):
        raise StagingError("reader command ledger reused a completed event id")
    payload = {
        "schema_version": "androidworld_candidate116_staged_source_coverage_receipt/v2",
        "production_namespace": PRODUCTION_NAMESPACE,
        "status": "all_required_reader_operations_completed",
        "case_unit_id": requirements.get("case_unit_id"),
        "requirements_sha256": requirements_sha,
        "reader_operation_expectations_sha256": operation_expectations[
            "reader_operation_expectations_sha256"
        ],
        "operations_sha256": operation_expectations["operations_sha256"],
        "required_operation_count": len(expected_operations),
        "completed_operation_count": len(completed_operations),
        "completed_operations": completed_operations,
        "completed_operations_sha256": canonical_sha256(completed_operations),
        "completed_command_event_ids": command_event_ids,
        "completed_command_event_ids_sha256": canonical_sha256(command_event_ids),
        "required_range_count": len(required),
        "covered_range_count": len(covered_ranges),
        "covered_ranges": covered_ranges,
        "coverage_page_count": requirements.get("coverage_page_count"),
        "coverage_pages_read": list(range(int(requirements.get("coverage_page_count") or 0))),
        "additional_command_count": 0,
        "global_order": "overview_then_header_then_all_pages_then_all_ranges",
    }
    payload["coverage_receipt_sha256"] = canonical_sha256(payload)
    return payload


def verify_coverage_receipt_against_events(
    receipt: Mapping[str, Any],
    events: list[dict[str, Any]],
    requirements: Mapping[str, Any],
    operation_expectations: Mapping[str, Any],
) -> None:
    """Independently replay A/B and require exact identity with a signed receipt."""

    receipt_core = dict(receipt)
    claimed_sha = receipt_core.pop("coverage_receipt_sha256", None)
    if not isinstance(claimed_sha, str) or canonical_sha256(receipt_core) != claimed_sha:
        raise StagingError("coverage receipt self-hash is invalid")
    replayed = coverage_receipt_from_events(
        events, requirements, operation_expectations
    )
    if dict(receipt) != replayed:
        raise StagingError("coverage receipt differs from independent A/B event replay")
