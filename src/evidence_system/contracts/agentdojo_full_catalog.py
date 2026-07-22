"""Build the pinned AgentDojo v1.2.2 full paired-case source catalog.

The catalog is intentionally narrower than a generic AgentDojo exporter.  It
locks the exact upstream release used by this experiment and fails closed when
the installed package, checkout, task counts, or paired-candidate IDs differ
from that release.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import inspect
import json
import subprocess
import tomllib
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml


AGENTDOJO_PACKAGE_NAME = "agentdojo"
AGENTDOJO_PACKAGE_VERSION = "0.1.35"
AGENTDOJO_GIT_TAG = "v0.1.35"
AGENTDOJO_GIT_COMMIT = "a75aba7631d3ca5fb7ab938965c97ead2f9ff84b"
AGENTDOJO_REPOSITORY_URL = "https://github.com/ethz-spylab/agentdojo"
AGENTDOJO_BENCHMARK_VERSION = "v1.2.2"
AGENTDOJO_ATTACK_STRATEGY = "direct"
AGENTDOJO_DEFENSE: None = None
AGENTDOJO_EXPECTED_CASE_COUNT = 949
AGENTDOJO_SELECTED_SOURCE_SCHEMA = "official_case_source.agentdojo_selected_tasks.v1"
AGENTDOJO_PAIRED_CANDIDATE_SCHEMA = (
    "official_case_source.agentdojo_paired_candidates.v1"
)

AGENTDOJO_SUITE_ORDER = ("workspace", "travel", "banking", "slack")
AGENTDOJO_EXPECTED_SUITE_COUNTS: dict[str, dict[str, int]] = {
    "workspace": {"user_tasks": 40, "injection_tasks": 14, "case_units": 560},
    "travel": {"user_tasks": 20, "injection_tasks": 7, "case_units": 140},
    "banking": {"user_tasks": 16, "injection_tasks": 9, "case_units": 144},
    "slack": {"user_tasks": 21, "injection_tasks": 5, "case_units": 105},
}

DEFAULT_PAIRED_CANDIDATES_PATH = (
    "experiments/official_splits/agentdojo_v1.2.2_paired_candidates.json"
)
DEFAULT_SELECTED_SOURCES_PATH = "experiments/agentdojo_full_v1.2.2_direct/official_splits/agentdojo_selected_task_sources.json"

EVALUATOR_SEMANTICS = (
    "Utility is evaluated by the selected user task utility method on the benign/injected run. "
    "Security is evaluated by the selected injection task security method on the injected run. "
    "The official runner records results keyed by user_task_id and injection_task_id."
)


def build_agentdojo_full_catalog(
    *,
    paired_candidates_path: str | Path = DEFAULT_PAIRED_CANDIDATES_PATH,
    output_path: str | Path = DEFAULT_SELECTED_SOURCES_PATH,
    agentdojo_repo_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build and write the deterministic 949-item selected-source catalog.

    The official AgentDojo package must be importable in the current Python
    environment.  ``agentdojo_repo_path`` may point at its clean official git
    checkout; for editable installs the checkout is inferred from the imported
    package file when omitted.
    """

    agentdojo_module, get_suites = _load_agentdojo()
    source_pin = _validate_source_pin(agentdojo_module, agentdojo_repo_path)
    repo_root = Path(source_pin["repo_root"])
    package_root = Path(inspect.getfile(agentdojo_module)).resolve().parent

    paired_path = resolve_repo_path(paired_candidates_path)
    candidates = _load_paired_candidates(paired_path)
    suites = get_suites(AGENTDOJO_BENCHMARK_VERSION)
    items, suite_counts = _enumerate_source_items(
        suites,
        source_repo_root=repo_root,
        package_root=package_root,
    )
    generated_ids = [str(item["case_unit_id"]) for item in items]
    candidate_ids = _candidate_ids(candidates)
    _validate_catalog_identity(generated_ids, candidate_ids, suite_counts)

    case_unit_ids_sha256 = sha256_object(generated_ids)
    candidate_file_sha256 = sha256_file(paired_path)
    payload: dict[str, Any] = {
        "benchmark": "AgentDojo",
        "benchmark_version": AGENTDOJO_BENCHMARK_VERSION,
        "items": items,
        "schema_version": AGENTDOJO_SELECTED_SOURCE_SCHEMA,
        "selected_count": len(items),
        "suite_case_counts": {
            name: suite_counts[name]["case_units"] for name in AGENTDOJO_SUITE_ORDER
        },
        "provenance": {
            "agentdojo_package_name": AGENTDOJO_PACKAGE_NAME,
            "agentdojo_package_version": AGENTDOJO_PACKAGE_VERSION,
            "agentdojo_git_tag": AGENTDOJO_GIT_TAG,
            "agentdojo_git_commit": AGENTDOJO_GIT_COMMIT,
            "agentdojo_repository_url": AGENTDOJO_REPOSITORY_URL,
            "source_tree_state": "clean",
            "benchmark_version": AGENTDOJO_BENCHMARK_VERSION,
            "attack_strategy": AGENTDOJO_ATTACK_STRATEGY,
            "defense": AGENTDOJO_DEFENSE,
            "pairing_rule": "cartesian product of each official suite's user_tasks and injection_tasks",
            "paired_candidates_path": _repo_display_path(paired_path),
            "paired_candidates_sha256": f"sha256:{candidate_file_sha256}",
            "case_unit_ids_sha256": f"sha256:{case_unit_ids_sha256}",
            "source_extraction": (
                "inspect.getsource on task classes plus repo-relative SHA-256 inventory of task/evaluator, "
                "suite, tool implementation, core evaluator, and environment data files"
            ),
        },
    }

    output = resolve_repo_path(output_path)
    _write_json_atomic(output, payload)
    output_sha256 = sha256_file(output)
    return {
        "status": "ok",
        "output_path": _repo_display_path(output),
        "selected_count": len(items),
        "suite_case_counts": payload["suite_case_counts"],
        "case_unit_ids_sha256": case_unit_ids_sha256,
        "output_sha256": output_sha256,
        "package_version": AGENTDOJO_PACKAGE_VERSION,
        "git_commit": AGENTDOJO_GIT_COMMIT,
    }


def _load_agentdojo() -> tuple[Any, Callable[[str], Mapping[str, Any]]]:
    try:
        module = importlib.import_module(AGENTDOJO_PACKAGE_NAME)
        task_suite_module = importlib.import_module("agentdojo.task_suite")
    except (ImportError, ModuleNotFoundError) as exc:
        raise ContractLifecycleError(
            "AgentDojo 0.1.35 is not importable; install the pinned official checkout in this Python environment"
        ) from exc
    get_suites = getattr(task_suite_module, "get_suites", None)
    if not callable(get_suites):
        raise ContractLifecycleError("AgentDojo task_suite.get_suites is unavailable")
    return module, get_suites


def _validate_source_pin(
    agentdojo_module: Any, repo_path: str | Path | None
) -> dict[str, str]:
    try:
        installed_version = importlib.metadata.version(AGENTDOJO_PACKAGE_NAME)
    except importlib.metadata.PackageNotFoundError as exc:
        raise ContractLifecycleError(
            "AgentDojo package metadata is unavailable"
        ) from exc
    if installed_version != AGENTDOJO_PACKAGE_VERSION:
        raise ContractLifecycleError(
            f"AgentDojo package version mismatch: expected {AGENTDOJO_PACKAGE_VERSION}, found {installed_version}"
        )

    module_file = Path(inspect.getfile(agentdojo_module)).resolve()
    source_repo = (
        resolve_repo_path(repo_path)
        if repo_path is not None
        else _infer_git_root(module_file)
    )
    if not source_repo.is_dir():
        raise ContractLifecycleError(
            f"AgentDojo source checkout is missing: {source_repo}"
        )
    try:
        module_file.relative_to(source_repo.resolve())
    except ValueError as exc:
        raise ContractLifecycleError(
            f"imported AgentDojo module {module_file} is not inside the supplied checkout {source_repo}"
        ) from exc

    commit = _git(source_repo, "rev-parse", "HEAD")
    if commit != AGENTDOJO_GIT_COMMIT:
        raise ContractLifecycleError(
            f"AgentDojo git commit mismatch: expected {AGENTDOJO_GIT_COMMIT}, found {commit}"
        )
    tag_commit = _git(
        source_repo, "rev-parse", f"refs/tags/{AGENTDOJO_GIT_TAG}^{{commit}}"
    )
    if tag_commit != AGENTDOJO_GIT_COMMIT:
        raise ContractLifecycleError(
            f"AgentDojo tag {AGENTDOJO_GIT_TAG} does not resolve to pinned commit {AGENTDOJO_GIT_COMMIT}"
        )
    tags = set(_git(source_repo, "tag", "--points-at", "HEAD").splitlines())
    if AGENTDOJO_GIT_TAG not in tags:
        raise ContractLifecycleError(
            f"AgentDojo HEAD is not exactly tagged {AGENTDOJO_GIT_TAG}"
        )
    dirty = _git(source_repo, "status", "--porcelain", "--untracked-files=all")
    if dirty:
        raise ContractLifecycleError(
            "AgentDojo source checkout is dirty; provenance requires a clean pinned checkout"
        )

    pyproject_path = source_repo / "pyproject.toml"
    if not pyproject_path.is_file():
        raise ContractLifecycleError(
            f"AgentDojo checkout has no pyproject.toml: {source_repo}"
        )
    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = pyproject.get("project")
    if not isinstance(project, Mapping):
        raise ContractLifecycleError(
            "AgentDojo pyproject.toml has no [project] mapping"
        )
    if (
        project.get("name") != AGENTDOJO_PACKAGE_NAME
        or project.get("version") != AGENTDOJO_PACKAGE_VERSION
    ):
        raise ContractLifecycleError(
            "AgentDojo pyproject name/version does not match the pinned source definition"
        )
    repository = str((project.get("urls") or {}).get("repository") or "").rstrip("/")
    if repository != AGENTDOJO_REPOSITORY_URL:
        raise ContractLifecycleError(
            f"AgentDojo pyproject repository mismatch: expected {AGENTDOJO_REPOSITORY_URL}, found {repository or '<missing>'}"
        )
    origin = _git(source_repo, "remote", "get-url", "origin")
    if not _is_official_origin(origin):
        raise ContractLifecycleError(
            f"AgentDojo checkout origin is not the official repository: {origin}"
        )
    return {
        "repo_root": str(source_repo.resolve()),
        "commit": commit,
        "version": installed_version,
    }


def _infer_git_root(module_file: Path) -> Path:
    for parent in (module_file.parent, *module_file.parents):
        if (parent / ".git").exists() and (parent / "pyproject.toml").is_file():
            return parent.resolve()
    raise ContractLifecycleError(
        "unable to infer the official AgentDojo git checkout; pass --agentdojo-repo explicitly"
    )


def _is_official_origin(origin: str) -> bool:
    normalized = origin.strip().lower().removesuffix(".git").rstrip("/")
    return normalized in {
        AGENTDOJO_REPOSITORY_URL.lower(),
        "git@github.com:ethz-spylab/agentdojo",
        "ssh://git@github.com/ethz-spylab/agentdojo",
    }


def _git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        stderr = (
            completed.stderr.strip() or completed.stdout.strip() or "unknown git error"
        )
        raise ContractLifecycleError(
            f"unable to verify AgentDojo checkout with git {' '.join(args)}: {stderr}"
        )
    return completed.stdout.strip()


def _load_paired_candidates(path: Path) -> Mapping[str, Any]:
    if not path.is_file():
        raise ContractLifecycleError(
            f"AgentDojo paired-candidate file is missing: {path}"
        )
    payload = load_json_or_yaml(path)
    if not isinstance(payload, Mapping):
        raise ContractLifecycleError(
            "AgentDojo paired-candidate file must be a mapping"
        )
    if payload.get("schema_version") != AGENTDOJO_PAIRED_CANDIDATE_SCHEMA:
        raise ContractLifecycleError(
            f"paired-candidate schema mismatch: expected {AGENTDOJO_PAIRED_CANDIDATE_SCHEMA}"
        )
    if (
        payload.get("benchmark") != "AgentDojo"
        or payload.get("benchmark_version") != AGENTDOJO_BENCHMARK_VERSION
    ):
        raise ContractLifecycleError(
            "paired-candidate benchmark/version does not match pinned AgentDojo v1.2.2"
        )
    if payload.get("candidate_count") != AGENTDOJO_EXPECTED_CASE_COUNT:
        raise ContractLifecycleError(
            f"paired-candidate count must be {AGENTDOJO_EXPECTED_CASE_COUNT}, found {payload.get('candidate_count')!r}"
        )
    items = payload.get("items")
    if not isinstance(items, list) or len(items) != AGENTDOJO_EXPECTED_CASE_COUNT:
        raise ContractLifecycleError(
            f"paired-candidate items must contain exactly {AGENTDOJO_EXPECTED_CASE_COUNT} entries"
        )
    return payload


def _candidate_ids(payload: Mapping[str, Any]) -> list[str]:
    ids: list[str] = []
    for index, raw in enumerate(payload.get("items") or []):
        if not isinstance(raw, Mapping):
            raise ContractLifecycleError(
                f"paired-candidate item {index} must be a mapping"
            )
        case_unit_id = str(raw.get("case_unit_id") or "")
        version, suite_name, user_task_id, injection_task_id = _parse_case_unit_id(
            case_unit_id
        )
        expected_task_id = f"{suite_name}:{user_task_id}:{injection_task_id}"
        expected_source_ref = (
            f"agentdojo://{version}/{suite_name}/{user_task_id}/{injection_task_id}"
        )
        if (
            raw.get("task_id") != expected_task_id
            or raw.get("source_ref") != expected_source_ref
        ):
            raise ContractLifecycleError(
                f"paired-candidate identity fields disagree for {case_unit_id}"
            )
        ids.append(case_unit_id)
    duplicates = sorted(
        case_id for case_id, count in Counter(ids).items() if count != 1
    )
    if duplicates:
        raise ContractLifecycleError(
            f"paired-candidate IDs are not unique: {', '.join(duplicates[:5])}"
        )
    return ids


def _enumerate_source_items(
    suites: Mapping[str, Any],
    *,
    source_repo_root: Path,
    package_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    if tuple(suites) != AGENTDOJO_SUITE_ORDER:
        raise ContractLifecycleError(
            f"AgentDojo suite order mismatch: expected {AGENTDOJO_SUITE_ORDER}, found {tuple(suites)}"
        )

    descriptor_cache: dict[Path, dict[str, str]] = {}

    def descriptor(path: str | Path) -> dict[str, str]:
        resolved = Path(path).resolve()
        cached = descriptor_cache.get(resolved)
        if cached is None:
            cached = _source_file_descriptor(resolved, source_repo_root)
            descriptor_cache[resolved] = cached
        return dict(cached)

    items: list[dict[str, Any]] = []
    suite_counts: dict[str, dict[str, int]] = {}
    for suite_name in AGENTDOJO_SUITE_ORDER:
        suite = suites[suite_name]
        user_tasks = getattr(suite, "user_tasks", None)
        injection_tasks = getattr(suite, "injection_tasks", None)
        tools = getattr(suite, "tools", None)
        if (
            not isinstance(user_tasks, Mapping)
            or not isinstance(injection_tasks, Mapping)
            or not isinstance(tools, list)
        ):
            raise ContractLifecycleError(
                f"AgentDojo suite {suite_name} has an unexpected API shape"
            )
        if len(set(user_tasks)) != len(user_tasks) or len(set(injection_tasks)) != len(
            injection_tasks
        ):
            raise ContractLifecycleError(
                f"AgentDojo suite {suite_name} task IDs are not unique"
            )
        expected = AGENTDOJO_EXPECTED_SUITE_COUNTS[suite_name]
        actual = {
            "user_tasks": len(user_tasks),
            "injection_tasks": len(injection_tasks),
            "case_units": len(user_tasks) * len(injection_tasks),
        }
        if actual != expected:
            raise ContractLifecycleError(
                f"AgentDojo {suite_name} count mismatch: expected {expected}, found {actual}"
            )
        suite_counts[suite_name] = actual

        suite_tools = _suite_tool_metadata(tools)
        shared_sources = _suite_source_inventory(
            suite_name,
            suite,
            tools,
            package_root=package_root,
            descriptor=descriptor,
        )
        user_metadata = {
            task_id: _user_task_metadata(task_id, task, descriptor=descriptor)
            for task_id, task in user_tasks.items()
        }
        injection_metadata = {
            task_id: _injection_task_metadata(task_id, task, descriptor=descriptor)
            for task_id, task in injection_tasks.items()
        }
        for user_task_id in user_tasks:
            for injection_task_id in injection_tasks:
                case_unit_id = f"{AGENTDOJO_BENCHMARK_VERSION}:{suite_name}:{user_task_id}:{injection_task_id}"
                item: dict[str, Any] = {
                    "agentdojo_package_version": AGENTDOJO_PACKAGE_VERSION,
                    "agentdojo_git_commit": AGENTDOJO_GIT_COMMIT,
                    "benchmark_version": AGENTDOJO_BENCHMARK_VERSION,
                    "case_unit_id": case_unit_id,
                    "evaluator_semantics": EVALUATOR_SEMANTICS,
                    "injection_task": injection_metadata[injection_task_id],
                    "source_files": shared_sources,
                    "source_ref": (
                        f"agentdojo://{AGENTDOJO_BENCHMARK_VERSION}/{suite_name}/"
                        f"{user_task_id}/{injection_task_id}"
                    ),
                    "suite": suite_name,
                    "suite_tools": suite_tools,
                    "task_id": f"{suite_name}:{user_task_id}:{injection_task_id}",
                    "user_task": user_metadata[user_task_id],
                }
                item["source_sha256"] = f"sha256:{_legacy_item_hash(item)}"
                items.append(item)
    return items, suite_counts


def _user_task_metadata(
    task_id: str,
    task: Any,
    *,
    descriptor: Callable[[str | Path], dict[str, str]],
) -> dict[str, Any]:
    _validate_task_identity(task_id, task, "user")
    prompt = getattr(task, "PROMPT", None)
    ground_truth_output = getattr(task, "GROUND_TRUTH_OUTPUT", None)
    if not isinstance(prompt, str) or not isinstance(ground_truth_output, str):
        raise ContractLifecycleError(
            f"AgentDojo user task {task_id} prompt/output fields must be strings"
        )
    task_type = type(task)
    return {
        "class": task_type.__name__,
        "class_source": _class_source(task_type, task_id),
        "evaluator_source_files": _task_evaluator_source_files(
            task,
            method_names=("ground_truth", "utility", "utility_from_traces"),
            descriptor=descriptor,
        ),
        "ground_truth_output": ground_truth_output,
        "id": task_id,
        "prompt": prompt,
        "source_file": descriptor(inspect.getfile(task_type)),
    }


def _injection_task_metadata(
    task_id: str,
    task: Any,
    *,
    descriptor: Callable[[str | Path], dict[str, str]],
) -> dict[str, Any]:
    _validate_task_identity(task_id, task, "injection")
    goal = getattr(task, "GOAL", None)
    ground_truth_output = getattr(task, "GROUND_TRUTH_OUTPUT", None)
    if not isinstance(goal, str) or not isinstance(ground_truth_output, str):
        raise ContractLifecycleError(
            f"AgentDojo injection task {task_id} goal/output fields must be strings"
        )
    task_type = type(task)
    return {
        "class": task_type.__name__,
        "class_source": _class_source(task_type, task_id),
        "evaluator_source_files": _task_evaluator_source_files(
            task,
            method_names=("ground_truth", "security", "security_from_traces"),
            descriptor=descriptor,
        ),
        "goal": goal,
        "ground_truth_output": ground_truth_output,
        "id": task_id,
        "source_file": descriptor(inspect.getfile(task_type)),
    }


def _validate_task_identity(task_id: str, task: Any, kind: str) -> None:
    if not task_id.startswith(f"{kind}_task_"):
        raise ContractLifecycleError(f"invalid AgentDojo {kind} task ID: {task_id}")
    if getattr(task, "ID", None) != task_id:
        raise ContractLifecycleError(
            f"AgentDojo {kind} task mapping key {task_id} disagrees with task.ID {getattr(task, 'ID', None)!r}"
        )


def _class_source(task_type: type[Any], task_id: str) -> str:
    try:
        return inspect.getsource(task_type)
    except (OSError, TypeError) as exc:
        raise ContractLifecycleError(
            f"unable to inspect official AgentDojo class source for {task_id}"
        ) from exc


def _task_evaluator_source_files(
    task: Any,
    *,
    method_names: Sequence[str],
    descriptor: Callable[[str | Path], dict[str, str]],
) -> list[dict[str, str]]:
    paths: set[Path] = set()
    visited: set[int] = set()

    def visit(current: Any) -> None:
        identity = id(current)
        if identity in visited:
            return
        visited.add(identity)
        task_type = type(current)
        paths.add(Path(inspect.getfile(task_type)).resolve())
        for method_name in method_names:
            method = getattr(task_type, method_name, None)
            if method is None:
                continue
            try:
                paths.add(Path(inspect.getfile(method)).resolve())
            except (OSError, TypeError):
                continue
            try:
                nonlocals = inspect.getclosurevars(method).nonlocals.values()
            except (TypeError, ValueError):
                continue
            for value in nonlocals:
                if _looks_like_task(value):
                    visit(value)

    visit(task)
    return [
        descriptor(path) for path in sorted(paths, key=lambda item: item.as_posix())
    ]


def _looks_like_task(value: Any) -> bool:
    task_type = type(value)
    return (
        hasattr(value, "ID")
        and hasattr(task_type, "ground_truth")
        and (hasattr(task_type, "utility") or hasattr(task_type, "security"))
    )


def _suite_tool_metadata(tools: Sequence[Any]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    names: set[str] = set()
    for tool in tools:
        name = getattr(tool, "name", None)
        description = getattr(tool, "description", None)
        if not isinstance(name, str) or not name or not isinstance(description, str):
            raise ContractLifecycleError(
                "AgentDojo suite tool name/description must be non-empty strings"
            )
        if name in names:
            raise ContractLifecycleError(
                f"AgentDojo suite contains duplicate tool name {name}"
            )
        names.add(name)
        result.append({"description": description, "name": name})
    return result


def _suite_source_inventory(
    suite_name: str,
    suite: Any,
    tools: Sequence[Any],
    *,
    package_root: Path,
    descriptor: Callable[[str | Path], dict[str, str]],
) -> dict[str, Any]:
    suite_module = importlib.import_module(
        f"agentdojo.default_suites.v1.{suite_name}.task_suite"
    )
    suite_definition_file = descriptor(inspect.getfile(suite_module))

    tool_paths: dict[Path, list[str]] = defaultdict(list)
    for tool in tools:
        try:
            path = Path(inspect.getfile(tool.run)).resolve()
        except (OSError, TypeError) as exc:
            raise ContractLifecycleError(
                f"unable to inspect implementation source for AgentDojo tool {getattr(tool, 'name', '<unknown>')}"
            ) from exc
        tool_paths[path].append(str(tool.name))
    tool_files: list[dict[str, Any]] = []
    for path in sorted(tool_paths, key=lambda item: item.as_posix()):
        item: dict[str, Any] = descriptor(path)
        item["tool_names"] = sorted(tool_paths[path])
        tool_files.append(item)

    data_path_value = getattr(suite, "data_path", None)
    data_root = (
        Path(data_path_value).resolve()
        if data_path_value is not None
        else package_root / "data" / "suites" / suite_name
    )
    if not data_root.is_dir():
        raise ContractLifecycleError(
            f"AgentDojo environment data directory is missing for {suite_name}: {data_root}"
        )
    environment_files = [
        descriptor(path)
        for path in sorted(
            (item for item in data_root.rglob("*") if item.is_file()),
            key=lambda item: item.as_posix(),
        )
    ]
    if not environment_files:
        raise ContractLifecycleError(
            f"AgentDojo environment data inventory is empty for {suite_name}"
        )

    base_tasks_module = importlib.import_module("agentdojo.base_tasks")
    task_suite_runtime_module = importlib.import_module(
        "agentdojo.task_suite.task_suite"
    )
    core_files = [
        descriptor(inspect.getfile(base_tasks_module)),
        descriptor(inspect.getfile(task_suite_runtime_module)),
    ]
    inventory: dict[str, Any] = {
        "core_evaluator_files": sorted(core_files, key=lambda item: item["repo_path"]),
        "environment_data_files": environment_files,
        "suite_definition_file": suite_definition_file,
        "tool_implementation_files": tool_files,
    }
    inventory["inventory_sha256"] = f"sha256:{sha256_object(inventory)}"
    return inventory


def _source_file_descriptor(path: Path, source_repo_root: Path) -> dict[str, str]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise ContractLifecycleError(f"AgentDojo source file is missing: {resolved}")
    try:
        relative = resolved.relative_to(source_repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise ContractLifecycleError(
            f"AgentDojo source file is outside the pinned official checkout: {resolved}"
        ) from exc
    return {"repo_path": relative, "sha256": f"sha256:{sha256_file(resolved)}"}


def _validate_catalog_identity(
    generated_ids: Sequence[str],
    candidate_ids: Sequence[str],
    suite_counts: Mapping[str, Mapping[str, int]],
) -> None:
    if len(generated_ids) != AGENTDOJO_EXPECTED_CASE_COUNT:
        raise ContractLifecycleError(
            f"AgentDojo API enumeration produced {len(generated_ids)} cases; expected {AGENTDOJO_EXPECTED_CASE_COUNT}"
        )
    if len(set(generated_ids)) != len(generated_ids):
        raise ContractLifecycleError(
            "AgentDojo API enumeration produced duplicate case-unit IDs"
        )
    generated_set = set(generated_ids)
    candidate_set = set(candidate_ids)
    if generated_set != candidate_set:
        missing = sorted(candidate_set - generated_set)
        unexpected = sorted(generated_set - candidate_set)
        raise ContractLifecycleError(
            "AgentDojo API IDs do not equal paired-candidate IDs: "
            f"missing={missing[:5]}, unexpected={unexpected[:5]}"
        )
    if list(generated_ids) != list(candidate_ids):
        first = next(
            index
            for index, pair in enumerate(zip(generated_ids, candidate_ids, strict=True))
            if pair[0] != pair[1]
        )
        raise ContractLifecycleError(
            "AgentDojo API ID order does not equal the locked paired-candidate order: "
            f"first mismatch at {first}: generated={generated_ids[first]}, candidate={candidate_ids[first]}"
        )
    if dict(suite_counts) != AGENTDOJO_EXPECTED_SUITE_COUNTS:
        raise ContractLifecycleError(
            "AgentDojo suite counts do not match the pinned v1.2.2 definition"
        )


def _parse_case_unit_id(case_unit_id: str) -> tuple[str, str, str, str]:
    parts = case_unit_id.split(":")
    if len(parts) != 4:
        raise ContractLifecycleError(
            f"invalid AgentDojo case_unit_id: {case_unit_id!r}"
        )
    version, suite_name, user_task_id, injection_task_id = parts
    if (
        version != AGENTDOJO_BENCHMARK_VERSION
        or suite_name not in AGENTDOJO_SUITE_ORDER
    ):
        raise ContractLifecycleError(
            f"AgentDojo case_unit_id is outside the pinned catalog: {case_unit_id}"
        )
    if not user_task_id.startswith("user_task_") or not injection_task_id.startswith(
        "injection_task_"
    ):
        raise ContractLifecycleError(
            f"invalid AgentDojo task IDs in case_unit_id: {case_unit_id}"
        )
    try:
        int(user_task_id.removeprefix("user_task_"))
        int(injection_task_id.removeprefix("injection_task_"))
    except ValueError as exc:
        raise ContractLifecycleError(
            f"non-numeric AgentDojo task ID in case_unit_id: {case_unit_id}"
        ) from exc
    return version, suite_name, user_task_id, injection_task_id


def _legacy_item_hash(item_without_hash: Mapping[str, Any]) -> str:
    """Match the hash convention used by the existing 100-case source file."""

    serialized = json.dumps(item_without_hash, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _repo_display_path(path: Path) -> str:
    resolved = path.resolve()
    repo_root = resolve_repo_path(".").resolve()
    try:
        return resolved.relative_to(repo_root).as_posix()
    except ValueError:
        return resolved.as_posix()


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)
