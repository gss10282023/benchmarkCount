#!/usr/bin/env python3
"""Build and verify source-pinned OSWorld case packets.

The OSWorld-Verified ``test_nogdrive`` task definitions are public Apache-2.0
sources, so each reviewer packet retains the exact task JSON (including the
controller-only evaluator configuration) at an immutable Git commit.

OSWorld 2.0 task classes are intentionally gated.  This builder never tries to
bypass that gate and never copies a gated task implementation into a packet.
It accepts an already-authorized local snapshot plus the release hash manifest,
verifies both fail-closed, extracts only statically evaluable agent-visible
metadata with ``ast`` (without importing or executing task code), and writes a
non-embedded source pointer for controller review.  Runtime-generated values in
an otherwise agent-visible instruction are represented by explicit, allowlisted
``{{NAME}}`` placeholders.  Without authorized inputs it emits a deterministic
blocked status and exits non-zero.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE_PACKET_ROOT = PROJECT_ROOT / "experiments" / "case_packets"

OSWORLD_VERIFIED_DOMAIN = "osworld_verified"
OSWORLD_VERIFIED_SPLIT = "test_nogdrive"
OSWORLD_VERIFIED_REPOSITORY = "https://github.com/xlang-ai/OSWorld.git"
OSWORLD_VERIFIED_COMMIT = "87df18ff0e906dafdb1ea96b8299f35ec1e67e6b"
OSWORLD_VERIFIED_SPLIT_PATH = "evaluation_examples/test_nogdrive.json"
OSWORLD_VERIFIED_SPLIT_SHA256 = (
    "fcb9497e93a8986407345d3012c872c9c2fed253420730fbea64ccfcace67dbb"
)
OSWORLD_VERIFIED_LICENSE_PATH = "LICENSE"
OSWORLD_VERIFIED_LICENSE_SHA256 = (
    "a8d1d88a0f9cce3cdbff73b03a80dc5e5d69e3ba2443946c268815a550c9e0ec"
)
OSWORLD_VERIFIED_EXPECTED_CASES = 361
OSWORLD_VERIFIED_RUNTIME_PATH = "desktop_env/desktop_env.py"
OSWORLD_VERIFIED_METRIC_MODULES = (
    "__init__",
    "basic_os",
    "chrome",
    "docs",
    "general",
    "gimp",
    "libreoffice",
    "others",
    "pdf",
    "slides",
    "table",
    "thunderbird",
    "utils",
    "vlc",
    "vscode",
)
OSWORLD_VERIFIED_GETTER_MODULES = (
    "__init__",
    "calc",
    "chrome",
    "file",
    "general",
    "gimp",
    "impress",
    "info",
    "misc",
    "replay",
    "vlc",
    "vscode",
)
OSWORLD_VERIFIED_EVALUATOR_PATHS = (
    OSWORLD_VERIFIED_RUNTIME_PATH,
    *(
        f"desktop_env/evaluators/metrics/{module}.py"
        for module in OSWORLD_VERIFIED_METRIC_MODULES
    ),
    *(
        f"desktop_env/evaluators/getters/{module}.py"
        for module in OSWORLD_VERIFIED_GETTER_MODULES
    ),
)

OSWORLD_2_DOMAIN = "osworld_2_0"
OSWORLD_2_RELEASE = "osworld-v2-2026.06.24"
OSWORLD_2_CODE_REPOSITORY = "https://github.com/xlang-ai/OSWorld-V2.git"
OSWORLD_2_CODE_TAG = "v2026.06.24"
OSWORLD_2_CODE_COMMIT = "2b9b7b4eb73243d557bdbf2998fe18d8e18e19c6"
OSWORLD_2_RELEASE_MANIFEST_PATH = (
    "benchmark_releases/osworld-v2-2026.06.24.json"
)
OSWORLD_2_RELEASE_MANIFEST_SHA256 = (
    "d8f9fb126d5f930fffdd6b4f74f7f3da9c81f4118175ccd5c10d1d411d46460e"
)
OSWORLD_2_TASK_REPOSITORY = "xlangai/osworld_v2_tasks"
OSWORLD_2_TASK_TAG = "v2026.06.24"
OSWORLD_2_TASK_COMMIT = "e7996f4cc850be108e510bd8433c63ee7b8303dd"
OSWORLD_2_TASK_HASH_MANIFEST_PATH = "manifests/task_hashes.json"
OSWORLD_2_TASK_HASH_MANIFEST_SHA256 = (
    "3312a7df40dbd004c300804f71c57d5a23a083d6c675082fcc34c60a37f9a76c"
)
OSWORLD_2_EXPECTED_CASES = 108

# A few official instructions interpolate values that only exist when the
# benchmark controller starts (the website hostname and temporary Overleaf
# credentials).  There is no canonical value at packet-build time.  Preserve
# those instructions as explicit templates instead of importing/executing the
# gated module or inventing a concrete runtime value.  This allowlist is kept
# deliberately narrow so a newly introduced dynamic symbol fails closed.
OSWORLD_2_RUNTIME_PLACEHOLDERS = {
    "HOST_SUFFIX": ("WEBSITE_HOST_SUFFIX", "controller website host suffix"),
    "_OVERLEAF_USER_EMAIL": (
        "OVERLEAF_USER_EMAIL",
        "controller-generated temporary Overleaf email",
    ),
    "_OVERLEAF_USER_PASSWORD": (
        "OVERLEAF_USER_PASSWORD",
        "controller-generated temporary Overleaf password",
    ),
    "OVERLEAF_USER_EMAIL": (
        "OVERLEAF_USER_EMAIL",
        "controller-generated temporary Overleaf email",
    ),
    "OVERLEAF_USER_PASSWORD": (
        "OVERLEAF_USER_PASSWORD",
        "controller-generated temporary Overleaf password",
    ),
    "GITLAB_USERNAME": (
        "GITLAB_USERNAME",
        "controller-generated temporary GitLab username",
    ),
    "GITLAB_PASSWORD": (
        "GITLAB_PASSWORD",
        "controller-generated temporary GitLab password",
    ),
}
OSWORLD_2_DYNAMIC_INSTRUCTION_MUTATIONS = {
    "task_026.py": {
        "source_sha256": "249e57f4a07206c1a3690c5744edb4b57ed9cf04130e71bb1c40188903eba7fa",
        "init_ast_sha256": "c944d5721c8e25e1941838fda305cf7f2046e02808b3821565793451d5b18171",
    },
    "task_041.py": {
        "source_sha256": "ba15c9508465d234a1f92159507a8baf6605ae1a118e66f4430df8f61608e982",
        "init_ast_sha256": "c944d5721c8e25e1941838fda305cf7f2046e02808b3821565793451d5b18171",
    },
}
OSWORLD_2_GITLAB_CREDENTIAL_SUFFIX = (
    " My GitLab account is '{{GITLAB_USERNAME}}' and the password is "
    "'{{GITLAB_PASSWORD}}'."
)
OSWORLD_2_MULTIPHASE_CONTRACT = {
    "filename": "task_069.py",
    "source_sha256": "98d43149c4ffac1154ea8178061654d92b37bb95ec5b87c1f9d74c4b61560ed2",
    "get_phases_ast_sha256": "d70a84fd7fc22996113f064f218bebea9218c8ffd165bac0876a0c1753416174",
    "instruction_method_ast_sha256": {
        "phase_1_instruction": "6ede223ecc7b3ebf8d38450374c67b858dfa3a218a2231f0c2a4b0f64c929fcc",
        "phase_2_instruction": "0851215f95bb3ca4a7f2197fc23f613d4c865a279c1741de04e09d4f83dbd59b",
        "phase_3_instruction": "ffcf8b248f94d51af4a8f35693d762265f11e8db026d8d2068d3f5b356dcf1c2",
        "phase_4_instruction": "646e9dfb00046b3720b39a38f509bbbb57c4b2e44bec41ac69c779b8ed2d2c2b",
    },
    "phases": (
        ("Phase 1: Schedule meeting", "PHASE1_INSTRUCTION", 0.35, 0.35),
        (
            "Phase 2: Handle rejection & reschedule",
            "PHASE2_INSTRUCTION",
            0.30,
            0.30,
        ),
        (
            "Phase 3: No-op checkpoint (nothing to do)",
            "PHASE3_INSTRUCTION",
            0.10,
            0.10,
        ),
        ("Phase 4: Post-meeting summary", "PHASE4_INSTRUCTION", 0.25, None),
    ),
}

USER_AGENT = "revised-agent-benchmark-case-packet-builder/1.0"
FORBIDDEN_AGENT_INPUT_KEYS = {
    "config",
    "evaluator",
    "expected",
    "reference_answer",
    "setup",
    "source_sha256",
}


class PacketBuildError(RuntimeError):
    """Raised on any fail-closed packet construction or verification error."""


class GatedSourceUnavailable(PacketBuildError):
    """Raised when authorized OSWorld 2.0 gated sources are unavailable."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--benchmark",
        choices=[OSWORLD_VERIFIED_DOMAIN, OSWORLD_2_DOMAIN, "all"],
        default="all",
        help="Packet family to build or verify (default: all).",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_CASE_PACKET_ROOT,
        help="Parent of the canonical domain packet roots.",
    )
    parser.add_argument(
        "--osworld2-task-root",
        type=Path,
        default=None,
        help=(
            "Authorized local directory containing exactly 108 task_*.py files "
            "from xlangai/osworld_v2_tasks@v2026.06.24."
        ),
    )
    parser.add_argument(
        "--osworld2-hash-manifest",
        type=Path,
        default=None,
        help=(
            "Authorized local manifests/task_hashes.json from the same gated "
            "OSWorld 2.0 task snapshot."
        ),
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify existing packet roots without fetching or writing.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace a differing generated domain root after full validation.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=16,
        help="Concurrent immutable-source downloads for OSWorld-Verified.",
    )
    return parser.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(pretty_json(value), encoding="utf-8")


def write_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def immutable_github_raw(repository: str, revision: str, path: str) -> str:
    owner_repo = repository.removeprefix("https://github.com/").removesuffix(".git")
    return f"https://raw.githubusercontent.com/{owner_repo}/{revision}/{path}"


def fetch_bytes(url: str, *, attempts: int = 4, timeout: int = 60) -> bytes:
    last_error: BaseException | None = None
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if response.status != 200:
                    raise PacketBuildError(f"GET {url} returned HTTP {response.status}")
                return response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(min(2 ** (attempt - 1), 8))
    raise PacketBuildError(f"Unable to fetch immutable source {url}: {last_error}")


def load_json_bytes(data: bytes, label: str) -> Any:
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PacketBuildError(f"Invalid JSON in {label}: {exc}") from exc


def require_sha(data: bytes, expected: str, label: str) -> None:
    actual = sha256_bytes(data)
    if actual != expected:
        raise PacketBuildError(
            f"{label} SHA-256 mismatch: expected {expected}, observed {actual}"
        )


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        data_hash = bytes.fromhex(sha256_file(path))
        digest.update(data_hash)
    return digest.hexdigest()


def install_generated_root(temp_root: Path, target_root: Path, *, replace: bool) -> str:
    generated_hash = tree_sha256(temp_root)
    target_root.parent.mkdir(parents=True, exist_ok=True)
    if target_root.exists():
        existing_hash = tree_sha256(target_root)
        if existing_hash == generated_hash:
            return "unchanged"
        if not replace:
            raise PacketBuildError(
                f"Refusing to replace differing packet root {target_root}; "
                "review the diff and re-run with --replace"
            )
        shutil.rmtree(target_root)
    shutil.move(str(temp_root), str(target_root))
    return "written"


def fetch_verified_evaluator_sources(*, workers: int) -> dict[str, bytes]:
    """Fetch the small, immutable evaluator source set once per build."""

    def download(path: str) -> tuple[str, bytes]:
        url = immutable_github_raw(
            OSWORLD_VERIFIED_REPOSITORY, OSWORLD_VERIFIED_COMMIT, path
        )
        return path, fetch_bytes(url)

    downloaded: dict[str, bytes] = {}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = {
            executor.submit(download, path): path
            for path in OSWORLD_VERIFIED_EVALUATOR_PATHS
        }
        for future in as_completed(futures):
            path, source = future.result()
            try:
                ast.parse(source.decode("utf-8"), filename=path)
            except (UnicodeDecodeError, SyntaxError) as exc:
                raise PacketBuildError(
                    f"invalid official evaluator Python source {path}: {exc}"
                ) from exc
            downloaded[path] = source
    if set(downloaded) != set(OSWORLD_VERIFIED_EVALUATOR_PATHS):
        raise PacketBuildError("not all immutable evaluator sources were downloaded")
    return downloaded


def _assigned_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    targets: list[ast.AST] = []
    if isinstance(node, ast.Assign):
        targets.extend(node.targets)
    elif isinstance(node, ast.AnnAssign):
        targets.append(node.target)
    for target in targets:
        names.update(
            item.id for item in ast.walk(target) if isinstance(item, ast.Name)
        )
    return names


def _local_import_target(
    *, source_path: str, node: ast.ImportFrom, known_paths: set[str]
) -> str | None:
    if node.level:
        package = source_path.removesuffix(".py").split("/")[:-1]
        parents = node.level - 1
        if parents > len(package):
            return None
        if parents:
            package = package[:-parents]
        module_parts = (node.module or "").split(".") if node.module else []
        candidate = "/".join((*package, *module_parts)) + ".py"
    elif node.module:
        candidate = node.module.replace(".", "/") + ".py"
    else:
        return None
    return candidate if candidate in known_paths else None


def make_evaluator_source_catalog(sources: Mapping[str, bytes]) -> dict[str, Any]:
    """Index official definitions/imports without importing evaluator code."""

    known_paths = set(sources)
    trees: dict[str, ast.Module] = {}
    definitions: dict[str, dict[str, ast.AST]] = {}
    local_imports: dict[str, dict[str, tuple[str, str]]] = {}
    import_bindings: dict[str, dict[str, ast.AST]] = {}
    for path, source in sources.items():
        tree = ast.parse(source.decode("utf-8"), filename=path)
        trees[path] = tree
        path_definitions: dict[str, ast.AST] = {}
        path_imports: dict[str, tuple[str, str]] = {}
        path_import_bindings: dict[str, ast.AST] = {}
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                path_definitions[node.name] = node
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                for name in _assigned_names(node):
                    path_definitions[name] = node
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != "*":
                        path_import_bindings[alias.asname or alias.name] = node
                target_path = _local_import_target(
                    source_path=path, node=node, known_paths=known_paths
                )
                if target_path:
                    for alias in node.names:
                        if alias.name != "*":
                            path_imports[alias.asname or alias.name] = (
                                target_path,
                                alias.name,
                            )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    bound_name = alias.asname or alias.name.split(".", 1)[0]
                    path_import_bindings[bound_name] = node
        definitions[path] = path_definitions
        local_imports[path] = path_imports
        import_bindings[path] = path_import_bindings

    def resolve(path: str, symbol: str) -> tuple[str, str]:
        seen: set[tuple[str, str]] = set()
        current = (path, symbol)
        while current not in seen:
            seen.add(current)
            current_path, current_symbol = current
            if current_symbol in definitions[current_path]:
                return current
            imported = local_imports[current_path].get(current_symbol)
            if imported is None:
                break
            current = imported
        raise PacketBuildError(
            f"unable to resolve official evaluator symbol {symbol!r} from {path}"
        )

    def exported_symbols(family: str) -> dict[str, tuple[str, str]]:
        init_path = f"desktop_env/evaluators/{family}/__init__.py"
        exports: dict[str, tuple[str, str]] = {}
        for node in trees[init_path].body:
            if isinstance(node, ast.ImportFrom):
                target_path = _local_import_target(
                    source_path=init_path, node=node, known_paths=known_paths
                )
                if target_path:
                    for alias in node.names:
                        exported = alias.asname or alias.name
                        exports[exported] = resolve(target_path, alias.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                exports[node.name] = (init_path, node.name)
        return exports

    return {
        "sources": dict(sources),
        "trees": trees,
        "definitions": definitions,
        "local_imports": local_imports,
        "import_bindings": import_bindings,
        "metric_symbols": exported_symbols("metrics"),
        "getter_symbols": exported_symbols("getters"),
    }


def _node_line_span(node: ast.AST) -> tuple[int, int]:
    start = int(getattr(node, "lineno"))
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        decorator_lines = [item.lineno for item in node.decorator_list]
        if decorator_lines:
            start = min(start, *decorator_lines)
    return start, int(getattr(node, "end_lineno"))


def _source_excerpt(
    catalog: Mapping[str, Any], *, path: str, symbol: str, node: ast.AST
) -> dict[str, Any]:
    source = catalog["sources"][path]
    start, end = _node_line_span(node)
    lines = source.decode("utf-8").splitlines(keepends=True)
    excerpt = "".join(lines[start - 1 : end])
    return {
        "symbol": symbol,
        "packet_path": f"official/{path}",
        "upstream_path": path,
        "source_ref": immutable_github_raw(
            OSWORLD_VERIFIED_REPOSITORY, OSWORLD_VERIFIED_COMMIT, path
        ),
        "source_sha256": sha256_bytes(source),
        "start_line": start,
        "end_line": end,
        "excerpt_sha256": sha256_bytes(excerpt.encode("utf-8")),
        "source": excerpt,
    }


def collect_symbol_excerpts(
    catalog: Mapping[str, Any], starts: Iterable[tuple[str, str]]
) -> list[dict[str, Any]]:
    """Collect exact target definitions and official in-repo helper closure."""

    definitions = catalog["definitions"]
    local_imports = catalog["local_imports"]
    import_bindings = catalog["import_bindings"]
    pending = list(starts)
    seen_symbols: set[tuple[str, str]] = set()
    excerpts: dict[tuple[str, int, int], dict[str, Any]] = {}
    while pending:
        path, symbol = pending.pop()
        key = (path, symbol)
        if key in seen_symbols:
            continue
        seen_symbols.add(key)
        node = definitions[path].get(symbol)
        if node is None:
            imported = local_imports[path].get(symbol)
            if imported is None:
                raise PacketBuildError(
                    f"official source {path} does not define evaluator symbol {symbol}"
                )
            pending.append(imported)
            continue
        excerpt = _source_excerpt(catalog, path=path, symbol=symbol, node=node)
        excerpt_key = (path, excerpt["start_line"], excerpt["end_line"])
        excerpts.setdefault(excerpt_key, excerpt)
        referenced = {
            child.id
            for child in ast.walk(node)
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)
        }
        for name in sorted(referenced):
            if name in definitions[path]:
                pending.append((path, name))
            elif name in local_imports[path]:
                pending.append(local_imports[path][name])
            elif name in import_bindings[path]:
                import_node = import_bindings[path][name]
                import_excerpt = _source_excerpt(
                    catalog,
                    path=path,
                    symbol=f"import:{name}",
                    node=import_node,
                )
                import_key = (
                    path,
                    import_excerpt["start_line"],
                    import_excerpt["end_line"],
                )
                excerpts.setdefault(import_key, import_excerpt)
    return [excerpts[key] for key in sorted(excerpts)]


def runtime_evaluator_excerpts(catalog: Mapping[str, Any]) -> list[dict[str, Any]]:
    tree = catalog["trees"][OSWORLD_VERIFIED_RUNTIME_PATH]
    desktop_env = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "DesktopEnv"
        ),
        None,
    )
    if desktop_env is None:
        raise PacketBuildError("official desktop_env.py has no DesktopEnv class")
    methods = {
        node.name: node
        for node in desktop_env.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    excerpts = []
    for method_name in ("_set_evaluator_info", "evaluate"):
        node = methods.get(method_name)
        if node is None:
            raise PacketBuildError(
                f"official DesktopEnv has no {method_name} evaluator method"
            )
        excerpts.append(
            _source_excerpt(
                catalog,
                path=OSWORLD_VERIFIED_RUNTIME_PATH,
                symbol=f"DesktopEnv.{method_name}",
                node=node,
            )
        )
    return excerpts


def _evaluator_names(task: Mapping[str, Any]) -> tuple[list[str], bool]:
    evaluator = task.get("evaluator")
    if not isinstance(evaluator, Mapping):
        raise PacketBuildError(f"task {task.get('id')} has no evaluator object")
    raw = evaluator.get("func")
    is_list = isinstance(raw, list)
    names = [str(item) for item in raw] if is_list else [str(raw or "")]
    if not names or any(not name for name in names):
        raise PacketBuildError(f"task {task.get('id')} has invalid evaluator func")
    return names, is_list


def _getter_descriptors(
    *,
    evaluator: Mapping[str, Any],
    key: str,
    catalog: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[tuple[str, str]]]:
    raw = evaluator.get(key)
    values = raw if isinstance(raw, list) else [raw]
    descriptors: list[dict[str, Any]] = []
    starts: list[tuple[str, str]] = []
    for index, config in enumerate(values):
        if not isinstance(config, Mapping):
            continue
        getter_type = str(config.get("type") or "")
        if not getter_type:
            raise PacketBuildError(f"evaluator {key}[{index}] has no getter type")
        symbol = f"get_{getter_type}"
        source = catalog["getter_symbols"].get(symbol)
        if source is None:
            raise PacketBuildError(f"official getter export {symbol!r} is unresolved")
        path, source_symbol = source
        starts.append((path, source_symbol))
        descriptors.append(
            {
                "slot": index,
                "config_path": f"evaluator.{key}"
                + (f"[{index}]" if isinstance(raw, list) else ""),
                "type": getter_type,
                "symbol": symbol,
                "config_sha256": sha256_bytes(canonical_bytes(config)),
                "packet_path": f"official/{path}",
                "source_ref": immutable_github_raw(
                    OSWORLD_VERIFIED_REPOSITORY,
                    OSWORLD_VERIFIED_COMMIT,
                    path,
                ),
                "source_sha256": sha256_bytes(catalog["sources"][path]),
            }
        )
    return descriptors, starts


def build_evaluator_contract(
    task: Mapping[str, Any], catalog: Mapping[str, Any]
) -> tuple[dict[str, Any], list[str], list[dict[str, Any]]]:
    evaluator = task.get("evaluator")
    if not isinstance(evaluator, Mapping):
        raise PacketBuildError(f"task {task.get('id')} has no evaluator object")
    names, list_mode = _evaluator_names(task)
    metric_descriptors: list[dict[str, Any]] = []
    starts: list[tuple[str, str]] = []
    for index, name in enumerate(names):
        source = catalog["metric_symbols"].get(name)
        if source is None:
            raise PacketBuildError(f"official metric export {name!r} is unresolved")
        path, source_symbol = source
        starts.append((path, source_symbol))
        metric_descriptors.append(
            {
                "slot": index,
                "name": name,
                "packet_path": f"official/{path}",
                "source_ref": immutable_github_raw(
                    OSWORLD_VERIFIED_REPOSITORY,
                    OSWORLD_VERIFIED_COMMIT,
                    path,
                ),
                "source_sha256": sha256_bytes(catalog["sources"][path]),
            }
        )
    result_getters, result_starts = _getter_descriptors(
        evaluator=evaluator, key="result", catalog=catalog
    )
    expected_getters, expected_starts = _getter_descriptors(
        evaluator=evaluator, key="expected", catalog=catalog
    )
    starts.extend(result_starts)
    starts.extend(expected_starts)
    symbol_excerpts = collect_symbol_excerpts(catalog, starts)
    runtime_excerpts = runtime_evaluator_excerpts(catalog)
    excerpts = sorted(
        (*runtime_excerpts, *symbol_excerpts),
        key=lambda item: (
            item["upstream_path"],
            item["start_line"],
            item["end_line"],
        ),
    )
    selected_paths = {
        OSWORLD_VERIFIED_RUNTIME_PATH,
        "desktop_env/evaluators/metrics/__init__.py",
        "desktop_env/evaluators/getters/__init__.py",
        *(item["upstream_path"] for item in excerpts),
    }
    official_sources = [
        {
            "packet_path": f"official/{path}",
            "upstream_path": path,
            "source_ref": immutable_github_raw(
                OSWORLD_VERIFIED_REPOSITORY, OSWORLD_VERIFIED_COMMIT, path
            ),
            "sha256": sha256_bytes(catalog["sources"][path]),
        }
        for path in sorted(selected_paths)
    ]
    conjunction = str(evaluator.get("conj", "and"))
    if conjunction not in {"and", "or"}:
        raise PacketBuildError(
            f"task {task.get('id')} has unsupported evaluator conjunction {conjunction}"
        )
    contract = {
        "schema_version": "osworld_verified_evaluator_contract/v1",
        "task_id": str(task.get("id") or ""),
        "extraction": {
            "method": "Python AST and immutable task JSON; no evaluator code executed",
            "official_commit": OSWORLD_VERIFIED_COMMIT,
            "evaluator_config_sha256": sha256_bytes(canonical_bytes(evaluator)),
        },
        "metrics": metric_descriptors,
        "list_mode": list_mode,
        "conjunction": conjunction,
        "result_getters": result_getters,
        "expected_getters": expected_getters,
        "metric_options": evaluator.get("options", None),
        "postconfig_present": bool(evaluator.get("postconfig")),
        "runtime_composition": {
            "binding": (
                "metrics are resolved with getattr(metrics, func); getters are "
                "resolved with getattr(getters, 'get_' + type)"
            ),
            "single_metric": (
                "obtain result state; obtain expected state when configured; call "
                "metric(result, expected, **options) or metric(result, **options); "
                "return the metric value"
            ),
            "multi_metric_and": (
                "evaluate in slot order; return 0 immediately when float(metric) "
                "== 0.0; otherwise return the arithmetic mean"
            ),
            "multi_metric_or": (
                "evaluate in slot order; return 1 immediately when float(metric) "
                "== 1.0; otherwise return the maximum"
            ),
            "infeasible": (
                "when evaluator.func is the string 'infeasible', return 1 only "
                "when the last action is FAIL (string or action_type), else 0"
            ),
            "agent_fail_on_non_infeasible": (
                "a final FAIL action forces score 0 before getters or metrics run"
            ),
            "file_not_found": (
                "single-metric and multi-metric 'and' paths return 0; the official "
                "multi-metric 'or' exception path has no explicit return and must "
                "be interpreted from the embedded exact source"
            ),
            "formal_packet_success": "final evaluator score equals exactly 1.0",
        },
        "official_source_files": official_sources,
        "exact_source_excerpts": [
            {key: value for key, value in excerpt.items() if key != "source"}
            for excerpt in excerpts
        ],
    }
    return contract, sorted(selected_paths), excerpts


def evaluator_shape(contract: Mapping[str, Any]) -> dict[str, Any]:
    metrics = contract.get("metrics")
    if not isinstance(metrics, list):
        raise PacketBuildError("evaluator contract has no metric list")
    result_getters = contract.get("result_getters")
    expected_getters = contract.get("expected_getters")
    return {
        "functions": [str(item["name"]) for item in metrics],
        "conjunction": str(contract.get("conjunction") or "and"),
        "result_types": [
            str(item["type"]) for item in result_getters or []
        ],
        "expected_types": [
            str(item["type"]) for item in expected_getters or []
        ],
        "postconfig_present": bool(contract.get("postconfig_present")),
        "score_range": [0.0, 1.0],
        "native_success_threshold": 1.0,
    }


def render_source_section(
    path: str, source_ref: str, body: Any, *, source_sha256: str | None = None
) -> str:
    rendered = pretty_json(body).rstrip()
    hash_line = f"Source SHA-256: `{source_sha256}`\n\n" if source_sha256 else ""
    return (
        f"### `{path}`\n\n"
        f"Source ref: `{source_ref}`\n\n"
        f"{hash_line}"
        "```json\n"
        f"{rendered}\n"
        "```\n"
    )


def render_python_excerpt(excerpt: Mapping[str, Any]) -> str:
    return (
        f"### `{excerpt['symbol']}` from `{excerpt['packet_path']}`\n\n"
        f"Source ref: `{excerpt['source_ref']}#L{excerpt['start_line']}-"
        f"L{excerpt['end_line']}`\n\n"
        f"Full source SHA-256: `{excerpt['source_sha256']}`\n\n"
        f"Exact excerpt SHA-256: `{excerpt['excerpt_sha256']}`\n\n"
        "```python\n"
        f"{str(excerpt['source']).rstrip()}\n"
        "```\n"
    )


def verified_case_markdown(
    *,
    domain: str,
    task_id: str,
    task: Mapping[str, Any],
    task_source_ref: str,
    task_source_sha256: str,
    evaluator: Mapping[str, Any],
    evaluator_contract: Mapping[str, Any],
    evaluator_contract_sha256: str,
    packet_source_paths: Iterable[str],
    excerpts: Iterable[Mapping[str, Any]],
) -> str:
    related_apps = ", ".join(str(item) for item in task.get("related_apps") or [])
    function_names = ", ".join(str(item) for item in evaluator["functions"])
    result_types = ", ".join(str(item) for item in evaluator["result_types"])
    source_inventory = "\n".join(
        f"- `{path}`" for path in sorted(packet_source_paths)
    )
    excerpt_sections = "\n".join(render_python_excerpt(item) for item in excerpts)
    return (
        "# Case Packet\n\n"
        "## Case Metadata\n\n"
        f"- domain: `{OSWORLD_VERIFIED_DOMAIN}`\n"
        f"- case_unit_id: `{task_id}`\n"
        f"- task_id: `{task_id}`\n\n"
        "## Benchmark Task Summary\n\n"
        "- benchmark: `OSWorld-Verified`\n"
        f"- split: `{OSWORLD_VERIFIED_SPLIT}`\n"
        f"- application domain: `{domain}`\n"
        f"- snapshot: `{task.get('snapshot', '')}`\n"
        f"- related apps: `{related_apps}`\n"
        f"- official instruction: {task.get('instruction', '')}\n"
        f"- evaluator functions: `{function_names}`\n"
        f"- evaluator conjunction: `{evaluator['conjunction']}`\n"
        f"- evaluator result getter types: `{result_types}`\n"
        "- native success: official evaluator score equals `1.0`\n"
        "- required retained run artifacts: `traj.jsonl`, `result.txt`, "
        "`runtime.log`\n\n"
        "## Visibility Boundary\n\n"
        "This canonical source-rich packet is controller/reviewer-only. The tested "
        "agent receives only the instruction in `agent_input.json`; do not place "
        "this packet, `raw_case/`, setup commands, evaluator expectations, or "
        "expected values in the agent prompt.\n\n"
        "## Evaluator Contract\n\n"
        "This contract is mechanically extracted from the immutable task JSON and "
        "the pinned official Python sources without importing or executing them. "
        "The exact evaluator/runtime excerpts below make comparison, threshold, "
        "failure, and multi-metric composition semantics locally reviewable.\n\n"
        "## Source Inventory\n\n"
        f"{source_inventory}\n\n"
        "## Packet Source Files\n\n"
        + render_source_section(
            "official/task.json",
            task_source_ref,
            task,
            source_sha256=task_source_sha256,
        )
        + "\n"
        + render_source_section(
            "derived/evaluator_contract.json",
            "mechanically extracted from the pinned task and evaluator sources",
            evaluator_contract,
            source_sha256=evaluator_contract_sha256,
        )
        + "\n## Exact Official Evaluator Source Excerpts\n\n"
        + excerpt_sections
    )


def build_verified_case(
    *,
    root: Path,
    domain: str,
    task_id: str,
    task_bytes: bytes,
    evaluator_catalog: Mapping[str, Any],
) -> dict[str, Any]:
    task_path = f"evaluation_examples/examples/{domain}/{task_id}.json"
    task_ref = immutable_github_raw(
        OSWORLD_VERIFIED_REPOSITORY, OSWORLD_VERIFIED_COMMIT, task_path
    )
    task = load_json_bytes(task_bytes, task_ref)
    if not isinstance(task, Mapping):
        raise PacketBuildError(f"{task_ref} must contain an object")
    if str(task.get("id")) != task_id:
        raise PacketBuildError(
            f"source ID mismatch for {domain}/{task_id}: {task.get('id')!r}"
        )
    instruction = task.get("instruction")
    if not isinstance(instruction, str) or not instruction.strip():
        raise PacketBuildError(f"task {task_id} has no non-empty instruction")
    evaluator_contract, evaluator_source_paths, excerpts = build_evaluator_contract(
        task, evaluator_catalog
    )
    evaluator = evaluator_shape(evaluator_contract)
    task_sha = sha256_bytes(task_bytes)
    case_dir = root / task_id
    raw_task_path = case_dir / "raw_case" / "official" / "task.json"
    write_bytes(raw_task_path, task_bytes)
    raw_contract_path = case_dir / "raw_case" / "derived" / "evaluator_contract.json"
    write_json(raw_contract_path, evaluator_contract)
    evaluator_contract_sha = sha256_file(raw_contract_path)
    raw_sources: dict[str, Path] = {
        "official/task.json": raw_task_path,
        "derived/evaluator_contract.json": raw_contract_path,
    }
    for source_path in evaluator_source_paths:
        packet_path = f"official/{source_path}"
        destination = case_dir / "raw_case" / packet_path
        write_bytes(destination, evaluator_catalog["sources"][source_path])
        raw_sources[packet_path] = destination

    agent_input = {"instruction": instruction}
    write_json(case_dir / "agent_input.json", agent_input)
    agent_input_sha = sha256_file(case_dir / "agent_input.json")
    packet = {
        "schema_version": "osworld_verified_case_packet/v1",
        "visibility": "controller_and_human_review_only",
        "benchmark": {
            "name": "OSWorld-Verified",
            "split": OSWORLD_VERIFIED_SPLIT,
            "official_repository": OSWORLD_VERIFIED_REPOSITORY,
            "official_commit": OSWORLD_VERIFIED_COMMIT,
        },
        "task": {
            "task_id": task_id,
            "application_domain": domain,
            "instruction": instruction,
            "snapshot": str(task.get("snapshot") or ""),
            "related_apps": [str(item) for item in task.get("related_apps") or []],
            "public_source": str(task.get("source") or ""),
            "proxy": bool(task.get("proxy")),
            "fixed_ip": bool(task.get("fixed_ip")),
        },
        "model_visible_input": {
            "path": "agent_input.json",
            "sha256": agent_input_sha,
            "field_allowlist": ["instruction"],
            "official_runtime_behavior": "agent.predict(instruction, observation)",
        },
        "evaluator_reference": {
            **evaluator,
            "implementation": (
                "xlang-ai/OSWorld immutable task config, exact official evaluator "
                "sources, and mechanically extracted evaluator contract"
            ),
            "task_config_path": "raw_case/official/task.json",
            "task_config_sha256": task_sha,
            "contract_path": "raw_case/derived/evaluator_contract.json",
            "contract_sha256": evaluator_contract_sha,
            "official_source_files": evaluator_contract["official_source_files"],
            "required_run_artifacts": ["traj.jsonl", "result.txt", "runtime.log"],
            "optional_run_artifacts": ["recording.mp4", "step_*.png"],
        },
        "leakage_control": {
            "model_receives_only_agent_input_json": True,
            "answer_payload_embedded_in_agent_input": False,
            "evaluator_payload_embedded_in_agent_input": False,
            "controller_sources_not_model_visible": True,
        },
        "provenance": {
            "source_ref": task_ref,
            "source_sha256": task_sha,
            "split_ref": immutable_github_raw(
                OSWORLD_VERIFIED_REPOSITORY,
                OSWORLD_VERIFIED_COMMIT,
                OSWORLD_VERIFIED_SPLIT_PATH,
            ),
            "split_sha256": OSWORLD_VERIFIED_SPLIT_SHA256,
        },
    }
    write_json(case_dir / "case_packet.json", packet)

    manifest = {
        "schema_version": "osworld_verified_raw_case_manifest/v1",
        "domain": OSWORLD_VERIFIED_DOMAIN,
        "benchmark_split": OSWORLD_VERIFIED_SPLIT,
        "case_unit_id": task_id,
        "task_id": task_id,
        "model_visible_files": ["agent_input.json"],
        "controller_runtime_files": ["case_packet.json"],
        "drafter_reviewer_only_files": [
            "case_packet.md",
            "raw_case_manifest.json",
            "raw_case/**",
        ],
        "copied_files": sorted(raw_sources),
        "official_files": sorted(
            path for path in raw_sources if path.startswith("official/")
        ),
        "derived_files": ["derived/evaluator_contract.json"],
        "packet_files": sorted(raw_sources),
        "file_sources": {
            "official/task.json": task_ref,
            "derived/evaluator_contract.json": (
                "mechanically extracted from official/task.json and pinned "
                "official evaluator sources"
            ),
            **{
                f"official/{path}": immutable_github_raw(
                    OSWORLD_VERIFIED_REPOSITORY,
                    OSWORLD_VERIFIED_COMMIT,
                    path,
                )
                for path in evaluator_source_paths
            },
        },
        "sha256_per_file": {
            name: sha256_file(path) for name, path in sorted(raw_sources.items())
        },
        "source_refs": sorted(
            {
                task_ref,
                *(
                    immutable_github_raw(
                        OSWORLD_VERIFIED_REPOSITORY,
                        OSWORLD_VERIFIED_COMMIT,
                        path,
                    )
                    for path in evaluator_source_paths
                ),
            }
        ),
        "required_run_artifacts": ["traj.jsonl", "result.txt", "runtime.log"],
        "top_level_file_sha256": {
            "agent_input.json": agent_input_sha,
            "case_packet.json": sha256_file(case_dir / "case_packet.json"),
        },
    }
    write_json(case_dir / "raw_case_manifest.json", manifest)
    markdown = verified_case_markdown(
        domain=domain,
        task_id=task_id,
        task=task,
        task_source_ref=task_ref,
        task_source_sha256=task_sha,
        evaluator=evaluator,
        evaluator_contract=evaluator_contract,
        evaluator_contract_sha256=evaluator_contract_sha,
        packet_source_paths=raw_sources,
        excerpts=excerpts,
    )
    (case_dir / "case_packet.md").write_text(markdown, encoding="utf-8")

    return {
        "case_unit_id": task_id,
        "task_id": task_id,
        "application_domain": domain,
        "source_sha256": task_sha,
        "instruction_sha256": sha256_bytes(instruction.encode("utf-8")),
        "files": {
            name: sha256_file(case_dir / name)
            for name in (
                "agent_input.json",
                "case_packet.json",
                "case_packet.md",
                "raw_case_manifest.json",
            )
        },
    }


def build_osworld_verified(output_root: Path, *, workers: int, replace: bool) -> None:
    target_root = output_root / OSWORLD_VERIFIED_DOMAIN
    split_url = immutable_github_raw(
        OSWORLD_VERIFIED_REPOSITORY,
        OSWORLD_VERIFIED_COMMIT,
        OSWORLD_VERIFIED_SPLIT_PATH,
    )
    license_url = immutable_github_raw(
        OSWORLD_VERIFIED_REPOSITORY,
        OSWORLD_VERIFIED_COMMIT,
        OSWORLD_VERIFIED_LICENSE_PATH,
    )
    split_bytes = fetch_bytes(split_url)
    require_sha(split_bytes, OSWORLD_VERIFIED_SPLIT_SHA256, "OSWorld no-GDrive split")
    license_bytes = fetch_bytes(license_url)
    require_sha(license_bytes, OSWORLD_VERIFIED_LICENSE_SHA256, "OSWorld license")
    split = load_json_bytes(split_bytes, split_url)
    if not isinstance(split, Mapping):
        raise PacketBuildError("OSWorld no-GDrive split must be an object")

    memberships: list[tuple[str, str]] = []
    for domain, raw_ids in split.items():
        if not isinstance(domain, str) or not isinstance(raw_ids, list):
            raise PacketBuildError("OSWorld no-GDrive split has invalid domain entries")
        memberships.extend((domain, str(task_id)) for task_id in raw_ids)
    if len(memberships) != OSWORLD_VERIFIED_EXPECTED_CASES:
        raise PacketBuildError(
            f"expected {OSWORLD_VERIFIED_EXPECTED_CASES} no-GDrive tasks, "
            f"observed {len(memberships)}"
        )
    task_ids = [task_id for _, task_id in memberships]
    if len(set(task_ids)) != len(task_ids):
        raise PacketBuildError("OSWorld no-GDrive split contains duplicate task IDs")

    def download(entry: tuple[str, str]) -> tuple[str, str, bytes]:
        domain, task_id = entry
        path = f"evaluation_examples/examples/{domain}/{task_id}.json"
        url = immutable_github_raw(
            OSWORLD_VERIFIED_REPOSITORY, OSWORLD_VERIFIED_COMMIT, path
        )
        return domain, task_id, fetch_bytes(url)

    downloaded: dict[tuple[str, str], bytes] = {}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = {executor.submit(download, entry): entry for entry in memberships}
        for future in as_completed(futures):
            domain, task_id, task_bytes = future.result()
            downloaded[(domain, task_id)] = task_bytes
    if len(downloaded) != OSWORLD_VERIFIED_EXPECTED_CASES:
        raise PacketBuildError("not all immutable OSWorld task sources were downloaded")
    evaluator_sources = fetch_verified_evaluator_sources(workers=workers)
    evaluator_catalog = make_evaluator_source_catalog(evaluator_sources)

    target_root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".osworld-verified-packets-", dir=target_root.parent
    ) as temp_parent:
        temp_root = Path(temp_parent) / OSWORLD_VERIFIED_DOMAIN
        temp_root.mkdir()
        source_lock = {
            "schema_version": "osworld_verified_source_lock/v1",
            "domain": OSWORLD_VERIFIED_DOMAIN,
            "benchmark": "OSWorld-Verified",
            "expected_case_count": OSWORLD_VERIFIED_EXPECTED_CASES,
            "official_repository": OSWORLD_VERIFIED_REPOSITORY,
            "official_commit": OSWORLD_VERIFIED_COMMIT,
            "split": {
                "name": OSWORLD_VERIFIED_SPLIT,
                "path": OSWORLD_VERIFIED_SPLIT_PATH,
                "url": split_url,
                "sha256": OSWORLD_VERIFIED_SPLIT_SHA256,
            },
            "license": {
                "spdx": "Apache-2.0",
                "path": OSWORLD_VERIFIED_LICENSE_PATH,
                "url": license_url,
                "sha256": OSWORLD_VERIFIED_LICENSE_SHA256,
            },
            "runner_sources": {
                "run.py": immutable_github_raw(
                    OSWORLD_VERIFIED_REPOSITORY,
                    OSWORLD_VERIFIED_COMMIT,
                    "run.py",
                ),
                "lib_run_single.py": immutable_github_raw(
                    OSWORLD_VERIFIED_REPOSITORY,
                    OSWORLD_VERIFIED_COMMIT,
                    "lib_run_single.py",
                ),
            },
            "evaluator_sources": {
                path: {
                    "url": immutable_github_raw(
                        OSWORLD_VERIFIED_REPOSITORY,
                        OSWORLD_VERIFIED_COMMIT,
                        path,
                    ),
                    "sha256": sha256_bytes(source),
                }
                for path, source in sorted(evaluator_sources.items())
            },
            "evaluator_contract_policy": {
                "method": "static AST extraction without importing evaluator code",
                "full_selected_sources_embedded_per_case": True,
                "exact_relevant_source_excerpts_embedded_in_case_packet_markdown": True,
            },
            "trajectory_policy": "not_downloaded_not_embedded",
            "environment_policy": "not_downloaded_not_embedded",
        }
        write_json(temp_root / "source_lock.json", source_lock)
        rows = []
        for domain, task_id in sorted(memberships):
            rows.append(
                build_verified_case(
                    root=temp_root,
                    domain=domain,
                    task_id=task_id,
                    task_bytes=downloaded[(domain, task_id)],
                    evaluator_catalog=evaluator_catalog,
                )
            )
        domain_counts: dict[str, int] = {}
        for domain, _ in memberships:
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        index = {
            "schema_version": "osworld_verified_case_packet_index/v1",
            "domain": OSWORLD_VERIFIED_DOMAIN,
            "benchmark": "OSWorld-Verified",
            "split": OSWORLD_VERIFIED_SPLIT,
            "status": "ready",
            "case_count": len(rows),
            "domain_counts": dict(sorted(domain_counts.items())),
            "source_lock_sha256": sha256_file(temp_root / "source_lock.json"),
            "case_rows_sha256": sha256_bytes(canonical_bytes(rows)),
            "cases": rows,
        }
        write_json(temp_root / "index.json", index)
        write_json(
            temp_root / "generation_status.json",
            {
                "schema_version": "osworld_case_packet_generation_status/v1",
                "domain": OSWORLD_VERIFIED_DOMAIN,
                "status": "ready",
                "case_count": len(rows),
                "index_sha256": sha256_file(temp_root / "index.json"),
                "source_lock_sha256": sha256_file(temp_root / "source_lock.json"),
            },
        )
        verify_packet_root(temp_root, expected_domain=OSWORLD_VERIFIED_DOMAIN)
        result = install_generated_root(temp_root, target_root, replace=replace)
    print(
        f"{OSWORLD_VERIFIED_DOMAIN}: {result}; "
        f"cases={OSWORLD_VERIFIED_EXPECTED_CASES}; root={target_root}"
    )


def normalize_hash(value: str) -> str | None:
    value = value.removeprefix("sha256:").lower()
    if len(value) == 64 and all(char in "0123456789abcdef" for char in value):
        return value
    return None


def extract_task_hashes(manifest: Any) -> dict[str, str]:
    """Recover task filename hashes from supported manifest layouts."""

    found: dict[str, str] = {}

    def visit(node: Any) -> None:
        if isinstance(node, Mapping):
            path = node.get("path") or node.get("name") or node.get("filename")
            digest = node.get("sha256") or node.get("hash")
            if isinstance(path, str) and isinstance(digest, str):
                normalized = normalize_hash(digest)
                if Path(path).name.startswith("task_") and path.endswith(".py") and normalized:
                    found[Path(path).name] = normalized
            for key, value in node.items():
                if isinstance(key, str) and key.startswith("task_") and key.endswith(".py"):
                    if isinstance(value, str):
                        normalized = normalize_hash(value)
                    elif isinstance(value, Mapping):
                        raw = value.get("sha256") or value.get("hash")
                        normalized = normalize_hash(raw) if isinstance(raw, str) else None
                    else:
                        normalized = None
                    if normalized:
                        found[Path(key).name] = normalized
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(manifest)
    return found


class StaticFieldError(ValueError):
    """Raised when an AST expression is outside the static extraction subset."""


def static_field_value(
    node: ast.AST,
    environment: Mapping[str, Any],
    runtime_bindings: set[str],
) -> Any:
    """Evaluate a deliberately small, side-effect-free AST expression subset."""

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (str, int, float, bool, bytes, type(None))):
            return node.value
        raise StaticFieldError(f"unsupported constant {type(node.value).__name__}")
    if isinstance(node, ast.Name):
        if node.id not in environment:
            raise StaticFieldError(f"unresolved name {node.id!r}")
        if node.id in OSWORLD_2_RUNTIME_PLACEHOLDERS:
            runtime_bindings.add(OSWORLD_2_RUNTIME_PLACEHOLDERS[node.id][0])
        return environment[node.id]
    if isinstance(node, ast.List):
        return [static_field_value(item, environment, runtime_bindings) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(
            static_field_value(item, environment, runtime_bindings)
            for item in node.elts
        )
    if isinstance(node, ast.Set):
        return {
            static_field_value(item, environment, runtime_bindings)
            for item in node.elts
        }
    if isinstance(node, ast.Dict):
        if any(key is None for key in node.keys):
            raise StaticFieldError("dictionary unpacking is unsupported")
        return {
            static_field_value(key, environment, runtime_bindings): static_field_value(
                value, environment, runtime_bindings
            )
            for key, value in zip(node.keys, node.values)
        }
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = static_field_value(node.operand, environment, runtime_bindings)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise StaticFieldError("unary operator requires a numeric literal")
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = static_field_value(node.left, environment, runtime_bindings)
        right = static_field_value(node.right, environment, runtime_bindings)
        if isinstance(left, str) and isinstance(right, str):
            return left + right
        if isinstance(left, list) and isinstance(right, list):
            return left + right
        if isinstance(left, tuple) and isinstance(right, tuple):
            return left + right
        raise StaticFieldError("addition is limited to strings, lists, and tuples")
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for item in node.values:
            if isinstance(item, ast.Constant) and isinstance(item.value, str):
                parts.append(item.value)
                continue
            if not isinstance(item, ast.FormattedValue):
                raise StaticFieldError("unsupported f-string component")
            if item.conversion != -1 or item.format_spec is not None:
                raise StaticFieldError("f-string conversion/format spec is unsupported")
            value = static_field_value(item.value, environment, runtime_bindings)
            if not isinstance(value, (str, int, float, bool)):
                raise StaticFieldError("f-string value is not a primitive")
            parts.append(str(value))
        return "".join(parts)
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "strip"
        and not node.args
        and not node.keywords
    ):
        value = static_field_value(node.func.value, environment, runtime_bindings)
        if isinstance(value, str):
            return value.strip()
        raise StaticFieldError(".strip() receiver is not a string")
    raise StaticFieldError(f"unsupported AST node {type(node).__name__}")


def _single_assignment(node: ast.AST) -> tuple[str, ast.AST] | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    if (
        isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.value is not None
    ):
        return node.target.id, node.value
    return None


def _self_instruction_writes(task_class: ast.ClassDef) -> list[ast.AST]:
    def is_instruction_target(target: ast.AST) -> bool:
        if (
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
            and target.attr == "instruction"
        ):
            return True
        return (
            isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Attribute)
            and isinstance(target.value.value, ast.Name)
            and target.value.value.id == "self"
            and target.value.attr == "__dict__"
            and isinstance(target.slice, ast.Constant)
            and target.slice.value == "instruction"
        )

    writes: list[ast.AST] = []
    for method in task_class.body:
        if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(method):
            targets: list[ast.AST] = []
            if isinstance(node, ast.Assign):
                targets.extend(node.targets)
            elif isinstance(node, ast.AnnAssign):
                targets.append(node.target)
            elif isinstance(node, ast.AugAssign):
                targets.append(node.target)
            if any(is_instruction_target(target) for target in targets):
                writes.append(node)
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "setattr"
                and len(node.args) >= 2
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == "self"
                and isinstance(node.args[1], ast.Constant)
                and node.args[1].value == "instruction"
            ):
                writes.append(node)
    return writes


def apply_dynamic_instruction_template(
    *,
    source: bytes,
    filename: str,
    task_class: ast.ClassDef,
    fields: dict[str, Any],
) -> None:
    """Apply a hash- and AST-locked template for known controller mutations."""

    writes = _self_instruction_writes(task_class)
    specification = OSWORLD_2_DYNAMIC_INSTRUCTION_MUTATIONS.get(filename)
    if not writes:
        if specification is not None:
            raise PacketBuildError(
                f"{filename} lost its hash-locked runtime instruction mutation"
            )
        return
    if specification is None:
        raise PacketBuildError(
            f"{filename} mutates self.instruction at runtime without an approved "
            "static template rule"
        )
    if sha256_bytes(source) != specification["source_sha256"]:
        raise PacketBuildError(
            f"{filename} source changed under its runtime instruction template rule"
        )
    init_methods = [
        node
        for node in task_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "__init__"
    ]
    if len(init_methods) != 1 or len(writes) != 1:
        raise PacketBuildError(
            f"{filename} runtime instruction mutation shape is not uniquely recognized"
        )
    init_ast_sha256 = sha256_bytes(
        ast.dump(init_methods[0], include_attributes=False).encode("utf-8")
    )
    if init_ast_sha256 != specification["init_ast_sha256"]:
        raise PacketBuildError(
            f"{filename} runtime instruction mutation AST changed; refusing to infer it"
        )
    instruction = fields.get("instruction")
    if not isinstance(instruction, str) or not instruction:
        raise PacketBuildError(
            f"{filename} has no base instruction for its approved runtime template"
        )
    fields["instruction"] = instruction + OSWORLD_2_GITLAB_CREDENTIAL_SUFFIX
    fields["dynamic_instruction_template_rule"] = "gitlab_temporary_credentials/v1"


def apply_multiphase_agent_contract(
    *,
    source: bytes,
    filename: str,
    task_class: ast.ClassDef,
    environment: Mapping[str, Any],
    fields: dict[str, Any],
) -> None:
    """Extract the one frozen multi-phase delivery contract without execution."""

    base_names = {
        base.id if isinstance(base, ast.Name) else base.attr
        for base in task_class.bases
        if isinstance(base, (ast.Name, ast.Attribute))
    }
    is_multiphase = "MultiPhaseTask" in base_names
    specification = OSWORLD_2_MULTIPHASE_CONTRACT
    if not is_multiphase:
        if filename == specification["filename"]:
            raise PacketBuildError(f"{filename} is no longer a MultiPhaseTask")
        return
    if filename != specification["filename"]:
        raise PacketBuildError(
            f"unrecognized MultiPhaseTask {filename}; refusing to infer phase delivery"
        )
    if sha256_bytes(source) != specification["source_sha256"]:
        raise PacketBuildError(f"{filename} changed under its multi-phase contract")
    methods = {
        node.name: node
        for node in task_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    get_phases = methods.get("get_phases")
    if get_phases is None or sha256_bytes(
        ast.dump(get_phases, include_attributes=False).encode("utf-8")
    ) != specification["get_phases_ast_sha256"]:
        raise PacketBuildError(f"{filename} get_phases AST changed")
    for method_name, expected_sha in specification[
        "instruction_method_ast_sha256"
    ].items():
        method = methods.get(method_name)
        if method is None or sha256_bytes(
            ast.dump(method, include_attributes=False).encode("utf-8")
        ) != expected_sha:
            raise PacketBuildError(
                f"{filename} {method_name} AST changed; refusing static extraction"
            )

    phases: list[dict[str, Any]] = []
    for index, (name, field_name, weight, gate_min_score) in enumerate(
        specification["phases"], start=1
    ):
        phase_instruction = environment.get(field_name)
        if not isinstance(phase_instruction, str) or not phase_instruction.strip():
            raise PacketBuildError(
                f"{filename} has no static instruction for phase {index}"
            )
        phases.append(
            {
                "index": index,
                "name": name,
                "instruction": phase_instruction,
                "weight": weight,
                "gate_min_score": gate_min_score,
                "delivery": "sequential_after_controller_setup",
            }
        )
    if abs(sum(float(phase["weight"]) for phase in phases) - 1.0) > 1e-12:
        raise PacketBuildError(f"{filename} phase weights do not sum to 1.0")
    fields["class_meta_instruction"] = fields.get("instruction")
    fields["instruction"] = phases[0]["instruction"]
    fields["phases"] = phases
    fields["multiphase_delivery"] = "sequential_no_future_phase_prefetch"


def literal_class_fields(source: bytes, filename: str) -> dict[str, Any]:
    try:
        tree = ast.parse(source.decode("utf-8"), filename=filename)
    except (UnicodeDecodeError, SyntaxError) as exc:
        raise PacketBuildError(f"unable to parse gated task {filename}: {exc}") from exc
    candidates: list[ast.ClassDef] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        base_names = {
            base.id
            for base in node.bases
            if isinstance(base, ast.Name)
        }
        base_names.update(
            base.attr
            for base in node.bases
            if isinstance(base, ast.Attribute)
        )
        if base_names & {"BaseTask", "MultiPhaseTask"}:
            candidates.append(node)
    if len(candidates) != 1:
        raise PacketBuildError(
            f"{filename} must contain exactly one BaseTask/MultiPhaseTask subclass"
        )
    task_class = candidates[0]
    runtime_bindings: set[str] = set()
    environment: dict[str, Any] = {
        source_name: "{{" + public_name + "}}"
        for source_name, (public_name, _) in OSWORLD_2_RUNTIME_PLACEHOLDERS.items()
    }

    # Resolve only simple module assignments.  Unsupported expressions are
    # ignored unless a selected class field depends on them later.
    for node in tree.body:
        assignment = _single_assignment(node)
        if assignment is None:
            continue
        name, value_node = assignment
        if name in OSWORLD_2_RUNTIME_PLACEHOLDERS:
            continue
        try:
            environment[name] = static_field_value(
                value_node, environment, runtime_bindings
            )
        except StaticFieldError:
            environment.pop(name, None)
            continue

    fields: dict[str, Any] = {"class_name": task_class.name}
    for node in task_class.body:
        assignment = _single_assignment(node)
        if assignment is None:
            continue
        name, value_node = assignment
        try:
            value = static_field_value(value_node, environment, runtime_bindings)
        except StaticFieldError as exc:
            environment.pop(name, None)
            if name in {"id", "instruction", "snapshot", "related_apps", "platform"}:
                raise PacketBuildError(
                    f"{filename} field {name!r} is not statically extractable "
                    f"({exc}); refusing to execute gated task code"
                ) from exc
            continue
        environment[name] = value
        if name in {"id", "instruction", "snapshot", "related_apps", "platform"}:
            fields[name] = value
    fields["evaluator_entrypoints"] = sorted(
        node.name
        for node in task_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in {"evaluate", "get_phases", "setup"}
    )
    apply_dynamic_instruction_template(
        source=source,
        filename=filename,
        task_class=task_class,
        fields=fields,
    )
    apply_multiphase_agent_contract(
        source=source,
        filename=filename,
        task_class=task_class,
        environment=environment,
        fields=fields,
    )
    instruction = fields.get("instruction")
    if not isinstance(instruction, str) or not instruction.strip():
        raise PacketBuildError(f"{filename} has no static non-empty instruction")
    all_agent_visible_instructions = [instruction]
    all_agent_visible_instructions.extend(
        str(phase["instruction"])
        for phase in fields.get("phases", [])
        if isinstance(phase, Mapping)
    )
    binding_text = "\n".join(all_agent_visible_instructions)
    fields["instruction_runtime_bindings"] = sorted(
        {
            public_name
            for public_name, _ in OSWORLD_2_RUNTIME_PLACEHOLDERS.values()
            if "{{" + public_name + "}}" in binding_text
        }
    )
    return fields


def osworld2_source_lock() -> dict[str, Any]:
    release_url = immutable_github_raw(
        OSWORLD_2_CODE_REPOSITORY,
        OSWORLD_2_CODE_TAG,
        OSWORLD_2_RELEASE_MANIFEST_PATH,
    )
    return {
        "schema_version": "osworld_2_0_source_lock/v1",
        "domain": OSWORLD_2_DOMAIN,
        "benchmark": "OSWorld 2.0",
        "release": OSWORLD_2_RELEASE,
        "expected_case_count": OSWORLD_2_EXPECTED_CASES,
        "code": {
            "repository": OSWORLD_2_CODE_REPOSITORY,
            "tag": OSWORLD_2_CODE_TAG,
            "commit": OSWORLD_2_CODE_COMMIT,
        },
        "release_manifest": {
            "path": OSWORLD_2_RELEASE_MANIFEST_PATH,
            "url": release_url,
            "sha256": OSWORLD_2_RELEASE_MANIFEST_SHA256,
        },
        "gated_tasks": {
            "repository": OSWORLD_2_TASK_REPOSITORY,
            "repository_url": (
                "https://huggingface.co/datasets/" + OSWORLD_2_TASK_REPOSITORY
            ),
            "tag": OSWORLD_2_TASK_TAG,
            "commit": OSWORLD_2_TASK_COMMIT,
            "hash_manifest_path": OSWORLD_2_TASK_HASH_MANIFEST_PATH,
            "hash_manifest_sha256": OSWORLD_2_TASK_HASH_MANIFEST_SHA256,
            "access": "auto-gated_user_acceptance_required",
            "embedding_policy": "never_embed_task_or_evaluator_implementation",
            "agent_visible_extraction": {
                "method": "restricted static AST evaluation without import or execution",
                "runtime_value_policy": "explicit allowlisted double-brace placeholders",
                "runtime_placeholders": {
                    public_name: description
                    for public_name, description in sorted(
                        set(OSWORLD_2_RUNTIME_PLACEHOLDERS.values())
                    )
                },
                "runtime_instruction_mutations": {
                    filename: dict(specification)
                    for filename, specification in sorted(
                        OSWORLD_2_DYNAMIC_INSTRUCTION_MUTATIONS.items()
                    )
                },
                "multiphase_contract": {
                    "filename": OSWORLD_2_MULTIPHASE_CONTRACT["filename"],
                    "source_sha256": OSWORLD_2_MULTIPHASE_CONTRACT[
                        "source_sha256"
                    ],
                    "get_phases_ast_sha256": OSWORLD_2_MULTIPHASE_CONTRACT[
                        "get_phases_ast_sha256"
                    ],
                    "delivery": "sequential_no_future_phase_prefetch",
                    "phase_count": len(OSWORLD_2_MULTIPHASE_CONTRACT["phases"]),
                },
            },
        },
        "trajectory_policy": "not_downloaded_not_embedded",
        "environment_policy": "not_downloaded_not_embedded",
    }


def build_osworld2_blocked_root(target_root: Path, *, replace: bool, reason: str) -> None:
    target_root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".osworld-2-packets-blocked-", dir=target_root.parent
    ) as temp_parent:
        temp_root = Path(temp_parent) / OSWORLD_2_DOMAIN
        temp_root.mkdir()
        write_json(temp_root / "source_lock.json", osworld2_source_lock())
        index = {
            "schema_version": "osworld_2_0_case_packet_index/v1",
            "domain": OSWORLD_2_DOMAIN,
            "benchmark": "OSWorld 2.0",
            "release": OSWORLD_2_RELEASE,
            "status": "blocked_gated_source_unavailable",
            "expected_case_count": OSWORLD_2_EXPECTED_CASES,
            "case_count": 0,
            "cases": [],
            "source_lock_sha256": sha256_file(temp_root / "source_lock.json"),
        }
        write_json(temp_root / "index.json", index)
        write_json(
            temp_root / "generation_status.json",
            {
                "schema_version": "osworld_case_packet_generation_status/v1",
                "domain": OSWORLD_2_DOMAIN,
                "status": "blocked_gated_source_unavailable",
                "case_count": 0,
                "expected_case_count": OSWORLD_2_EXPECTED_CASES,
                "reason": reason,
                "required_user_action": [
                    "accept access at https://huggingface.co/datasets/xlangai/osworld_v2_tasks",
                    "obtain task_*.py and manifests/task_hashes.json at v2026.06.24 through the official authenticated downloader",
                    "re-run this builder with --osworld2-task-root and --osworld2-hash-manifest",
                ],
                "source_lock_sha256": sha256_file(temp_root / "source_lock.json"),
                "index_sha256": sha256_file(temp_root / "index.json"),
            },
        )
        result = install_generated_root(temp_root, target_root, replace=replace)
    print(f"{OSWORLD_2_DOMAIN}: {result}; status=blocked; root={target_root}")


def osworld2_case_markdown(
    *, task_id: str, task: Mapping[str, Any], pointer: Mapping[str, Any], release: Any
) -> str:
    runtime_bindings = [str(item) for item in task["instruction_runtime_bindings"]]
    binding_summary = (
        ", ".join(f"`{{{{{name}}}}}`" for name in runtime_bindings)
        if runtime_bindings
        else "none (fully static instruction)"
    )
    phases = task.get("phases")
    phase_section = ""
    if isinstance(phases, list) and phases:
        phase_lines = [
            "## Sequential Agent-Visible Phases",
            "",
            "The official controller delivers these instructions one at a time. "
            "Only phase 1 is present in the initial `agent_input.json`; later "
            "instructions must not be prefetched into the tested agent context.",
            "",
        ]
        for phase in phases:
            gate = phase.get("gate_min_score")
            gate_text = "none" if gate is None else str(gate)
            phase_lines.extend(
                [
                    f"### Phase {phase['index']}: {phase['name']}",
                    "",
                    f"- weight: `{phase['weight']}`",
                    f"- gate_min_score: `{gate_text}`",
                    f"- agent-visible instruction: {phase['instruction']}",
                    "",
                ]
            )
        phase_section = "\n".join(phase_lines) + "\n"
    return (
        "# Case Packet\n\n"
        "## Case Metadata\n\n"
        f"- domain: `{OSWORLD_2_DOMAIN}`\n"
        f"- case_unit_id: `{task_id}`\n"
        f"- task_id: `{task_id}`\n\n"
        "## Benchmark Task Summary\n\n"
        "- benchmark: `OSWorld 2.0`\n"
        f"- release: `{OSWORLD_2_RELEASE}`\n"
        f"- official agent-visible instruction template: {task['instruction']}\n"
        f"- runtime bindings: {binding_summary}\n"
        "- template policy: placeholders are filled by the official controller; "
        "the gated task module was not imported or executed\n"
        "- evaluator implementation: gated official task class, hash-verified and "
        "intentionally not embedded\n"
        "- native score artifacts: `result.json` when emitted and legacy "
        "`result.txt`\n\n"
        + phase_section
        + "## Visibility Boundary\n\n"
        "The tested agent initially receives only `agent_input.json`. The official setup and "
        "evaluator implementation remain gated and are not embedded, reproduced, "
        "or paraphrased here. Formal checklist drafting requires authorized local "
        "controller review of the hash-pinned task class; this packet must not be "
        "treated as exposing hidden evaluator semantics.\n\n"
        "## Source Inventory\n\n"
        "- `derived/agent_visible_task.json`\n"
        "- `controller/gated_source_pointer.json`\n"
        "- `public/release_manifest.json`\n\n"
        "## Packet Source Files\n\n"
        + render_source_section(
            "derived/agent_visible_task.json",
            f"{OSWORLD_2_TASK_REPOSITORY}@{OSWORLD_2_TASK_TAG}#{pointer['path']}",
            task,
        )
        + "\n"
        + render_source_section(
            "controller/gated_source_pointer.json",
            f"{OSWORLD_2_TASK_REPOSITORY}@{OSWORLD_2_TASK_TAG}#{pointer['path']}",
            pointer,
        )
        + "\n"
        + render_source_section(
            "public/release_manifest.json",
            immutable_github_raw(
                OSWORLD_2_CODE_REPOSITORY,
                OSWORLD_2_CODE_TAG,
                OSWORLD_2_RELEASE_MANIFEST_PATH,
            ),
            release,
        )
    )


def build_osworld2_case(
    *,
    root: Path,
    task_path: Path,
    expected_hash: str,
    release_bytes: bytes,
    release: Any,
) -> dict[str, Any]:
    source = task_path.read_bytes()
    actual_hash = sha256_bytes(source)
    if actual_hash != expected_hash:
        raise PacketBuildError(
            f"gated task hash mismatch for {task_path.name}: "
            f"expected {expected_hash}, observed {actual_hash}"
        )
    fields = literal_class_fields(source, task_path.name)
    filename_id = task_path.stem.removeprefix("task_")
    raw_id = fields.get("id")
    task_id = str(raw_id) if raw_id not in (None, "") else filename_id
    if task_id.isdigit():
        task_id = task_id.zfill(3)
    if task_id != filename_id:
        raise PacketBuildError(
            f"task ID mismatch in {task_path.name}: class id {task_id!r}"
        )
    instruction = str(fields["instruction"])
    runtime_bindings = [str(item) for item in fields["instruction_runtime_bindings"]]
    phases = [dict(item) for item in fields.get("phases", [])]
    task = {
        "task_id": task_id,
        "instruction": instruction,
        "snapshot": str(fields.get("snapshot") or ""),
        "related_apps": [str(item) for item in fields.get("related_apps") or []],
        "platform": str(fields.get("platform") or "linux"),
        "instruction_is_runtime_template": bool(runtime_bindings),
        "instruction_runtime_bindings": runtime_bindings,
    }
    if phases:
        task.update(
            {
                "is_multiphase": True,
                "phase_count": len(phases),
                "phases": phases,
                "multiphase_delivery": str(fields["multiphase_delivery"]),
                "runner_class_meta_instruction": str(
                    fields.get("class_meta_instruction") or ""
                ),
            }
        )
    else:
        task.update({"is_multiphase": False, "phase_count": 0})
    pointer = {
        "repository": OSWORLD_2_TASK_REPOSITORY,
        "repository_url": "https://huggingface.co/datasets/" + OSWORLD_2_TASK_REPOSITORY,
        "tag": OSWORLD_2_TASK_TAG,
        "commit": OSWORLD_2_TASK_COMMIT,
        "path": task_path.name,
        "sha256": actual_hash,
        "hash_manifest_path": OSWORLD_2_TASK_HASH_MANIFEST_PATH,
        "hash_manifest_sha256": OSWORLD_2_TASK_HASH_MANIFEST_SHA256,
        "access": "auto-gated_authorized_snapshot",
        "embedded": False,
        "redistribution": "gated_implementation_not_embedded",
        "parsed_without_execution": True,
        "runtime_bindings": runtime_bindings,
        "task_class": str(fields["class_name"]),
        "evaluator_entrypoints": list(fields["evaluator_entrypoints"]),
        "dynamic_instruction_template_rule": fields.get(
            "dynamic_instruction_template_rule"
        ),
        "multiphase_contract": (
            "hash_and_ast_locked_sequential/v1" if phases else None
        ),
    }
    case_dir = root / task_id
    write_json(
        case_dir / "raw_case" / "derived" / "agent_visible_task.json", task
    )
    write_json(
        case_dir / "raw_case" / "controller" / "gated_source_pointer.json",
        pointer,
    )
    write_bytes(
        case_dir / "raw_case" / "public" / "release_manifest.json",
        release_bytes,
    )
    agent_input = {"instruction": instruction}
    write_json(case_dir / "agent_input.json", agent_input)
    packet = {
        "schema_version": "osworld_2_0_case_packet/v1",
        "visibility": "controller_and_human_review_only",
        "benchmark": {
            "name": "OSWorld 2.0",
            "release": OSWORLD_2_RELEASE,
            "official_repository": OSWORLD_2_CODE_REPOSITORY,
            "official_code_tag": OSWORLD_2_CODE_TAG,
            "official_code_commit": OSWORLD_2_CODE_COMMIT,
        },
        "task": task,
        "model_visible_input": {
            "path": "agent_input.json",
            "sha256": sha256_file(case_dir / "agent_input.json"),
            "field_allowlist": ["instruction"],
            "instruction_representation": (
                "official_runtime_template_with_explicit_placeholders"
                if runtime_bindings
                else "official_static_instruction"
            ),
            "runtime_bindings": runtime_bindings,
            "multiphase_boundary": (
                "initial_phase_only_future_phases_sequentially_controller_delivered"
                if phases
                else "single_instruction"
            ),
        },
        "evaluator_reference": {
            "implementation": "official gated BaseTask subclass",
            "source_pointer_path": "raw_case/controller/gated_source_pointer.json",
            "source_sha256": actual_hash,
            "entrypoints": list(fields["evaluator_entrypoints"]),
            "implementation_embedded": False,
            "score_fields": ["result.json.score", "result.txt"],
            "required_run_artifacts": [
                "traj.jsonl",
                "runtime.log",
                "eval.log",
                "result.txt",
            ],
            "optional_run_artifacts": [
                "result.json",
                "checkpoint_results.json",
                "step_*.png",
            ],
        },
        "formal_checklist_drafting_status": (
            "requires_authorized_local_evaluator_review"
        ),
        "leakage_control": {
            "model_receives_only_agent_input_json": True,
            "gated_task_implementation_embedded": False,
            "gated_evaluator_implementation_embedded": False,
            "controller_source_pointer_not_model_visible": True,
        },
        "provenance": {
            "release_manifest_sha256": OSWORLD_2_RELEASE_MANIFEST_SHA256,
            "task_hash_manifest_sha256": OSWORLD_2_TASK_HASH_MANIFEST_SHA256,
            "task_source_sha256": actual_hash,
        },
    }
    write_json(case_dir / "case_packet.json", packet)
    raw_files = {
        "derived/agent_visible_task.json": case_dir
        / "raw_case"
        / "derived"
        / "agent_visible_task.json",
        "controller/gated_source_pointer.json": case_dir
        / "raw_case"
        / "controller"
        / "gated_source_pointer.json",
        "public/release_manifest.json": case_dir
        / "raw_case"
        / "public"
        / "release_manifest.json",
    }
    manifest = {
        "schema_version": "osworld_2_0_raw_case_manifest/v1",
        "domain": OSWORLD_2_DOMAIN,
        "benchmark_release": OSWORLD_2_RELEASE,
        "case_unit_id": task_id,
        "task_id": task_id,
        "model_visible_files": ["agent_input.json"],
        "controller_runtime_files": ["case_packet.json"],
        "drafter_reviewer_only_files": [
            "case_packet.md",
            "raw_case_manifest.json",
            "raw_case/**",
        ],
        "copied_files": sorted(raw_files),
        "derived_files": [
            "derived/agent_visible_task.json",
            "controller/gated_source_pointer.json",
        ],
        "official_public_files": ["public/release_manifest.json"],
        "gated_files_embedded": [],
        "packet_files": sorted(raw_files),
        "file_sources": {
            "derived/agent_visible_task.json": (
                f"{OSWORLD_2_TASK_REPOSITORY}@{OSWORLD_2_TASK_TAG}#{task_path.name}"
            ),
            "controller/gated_source_pointer.json": (
                f"{OSWORLD_2_TASK_REPOSITORY}@{OSWORLD_2_TASK_TAG}#{task_path.name}"
            ),
            "public/release_manifest.json": immutable_github_raw(
                OSWORLD_2_CODE_REPOSITORY,
                OSWORLD_2_CODE_TAG,
                OSWORLD_2_RELEASE_MANIFEST_PATH,
            ),
        },
        "sha256_per_file": {
            name: sha256_file(path) for name, path in sorted(raw_files.items())
        },
        "gated_source_sha256": actual_hash,
        "gated_source_embedded": False,
        "required_run_artifacts": [
            "traj.jsonl",
            "runtime.log",
            "eval.log",
            "result.txt",
        ],
        "top_level_file_sha256": {
            "agent_input.json": sha256_file(case_dir / "agent_input.json"),
            "case_packet.json": sha256_file(case_dir / "case_packet.json"),
        },
    }
    write_json(case_dir / "raw_case_manifest.json", manifest)
    (case_dir / "case_packet.md").write_text(
        osworld2_case_markdown(
            task_id=task_id, task=task, pointer=pointer, release=release
        ),
        encoding="utf-8",
    )
    return {
        "case_unit_id": task_id,
        "task_id": task_id,
        "source_sha256": actual_hash,
        "instruction_sha256": sha256_bytes(instruction.encode("utf-8")),
        "instruction_runtime_bindings": runtime_bindings,
        "phase_count": len(phases),
        "files": {
            name: sha256_file(case_dir / name)
            for name in (
                "agent_input.json",
                "case_packet.json",
                "case_packet.md",
                "raw_case_manifest.json",
            )
        },
    }


def build_osworld2(
    output_root: Path,
    *,
    task_root: Path | None,
    hash_manifest_path: Path | None,
    replace: bool,
) -> None:
    target_root = output_root / OSWORLD_2_DOMAIN
    if task_root is None or hash_manifest_path is None:
        reason = (
            "authorized local task root and hash manifest were not both provided; "
            "network gate bypass is prohibited"
        )
        build_osworld2_blocked_root(target_root, replace=replace, reason=reason)
        raise GatedSourceUnavailable(reason)
    task_root = task_root.resolve()
    hash_manifest_path = hash_manifest_path.resolve()
    if not task_root.is_dir() or not hash_manifest_path.is_file():
        reason = "provided authorized OSWorld 2.0 task inputs do not exist"
        build_osworld2_blocked_root(target_root, replace=replace, reason=reason)
        raise GatedSourceUnavailable(reason)

    manifest_bytes = hash_manifest_path.read_bytes()
    require_sha(
        manifest_bytes,
        OSWORLD_2_TASK_HASH_MANIFEST_SHA256,
        "OSWorld 2.0 gated task hash manifest",
    )
    manifest = load_json_bytes(manifest_bytes, str(hash_manifest_path))
    task_hashes = extract_task_hashes(manifest)
    if len(task_hashes) != OSWORLD_2_EXPECTED_CASES:
        raise PacketBuildError(
            f"expected {OSWORLD_2_EXPECTED_CASES} hashes in gated task manifest, "
            f"observed {len(task_hashes)}"
        )
    task_paths = sorted(task_root.glob("task_*.py"))
    if len(task_paths) != OSWORLD_2_EXPECTED_CASES:
        raise PacketBuildError(
            f"expected {OSWORLD_2_EXPECTED_CASES} gated task files, "
            f"observed {len(task_paths)}"
        )
    if {path.name for path in task_paths} != set(task_hashes):
        raise PacketBuildError("gated task filenames do not match the release hash manifest")

    release_url = immutable_github_raw(
        OSWORLD_2_CODE_REPOSITORY,
        OSWORLD_2_CODE_TAG,
        OSWORLD_2_RELEASE_MANIFEST_PATH,
    )
    release_bytes = fetch_bytes(release_url)
    require_sha(
        release_bytes,
        OSWORLD_2_RELEASE_MANIFEST_SHA256,
        "OSWorld 2.0 public release manifest",
    )
    release = load_json_bytes(release_bytes, release_url)

    target_root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".osworld-2-packets-", dir=target_root.parent
    ) as temp_parent:
        temp_root = Path(temp_parent) / OSWORLD_2_DOMAIN
        temp_root.mkdir()
        write_json(temp_root / "source_lock.json", osworld2_source_lock())
        rows = [
            build_osworld2_case(
                root=temp_root,
                task_path=task_path,
                expected_hash=task_hashes[task_path.name],
                release_bytes=release_bytes,
                release=release,
            )
            for task_path in task_paths
        ]
        rows.sort(key=lambda item: item["case_unit_id"])
        index = {
            "schema_version": "osworld_2_0_case_packet_index/v1",
            "domain": OSWORLD_2_DOMAIN,
            "benchmark": "OSWorld 2.0",
            "release": OSWORLD_2_RELEASE,
            "status": "ready_controller_source_pointer_only",
            "case_count": len(rows),
            "source_lock_sha256": sha256_file(temp_root / "source_lock.json"),
            "case_rows_sha256": sha256_bytes(canonical_bytes(rows)),
            "cases": rows,
        }
        write_json(temp_root / "index.json", index)
        write_json(
            temp_root / "generation_status.json",
            {
                "schema_version": "osworld_case_packet_generation_status/v1",
                "domain": OSWORLD_2_DOMAIN,
                "status": "ready_controller_source_pointer_only",
                "case_count": len(rows),
                "gated_implementation_embedded": False,
                "index_sha256": sha256_file(temp_root / "index.json"),
                "source_lock_sha256": sha256_file(temp_root / "source_lock.json"),
            },
        )
        verify_packet_root(temp_root, expected_domain=OSWORLD_2_DOMAIN)
        result = install_generated_root(temp_root, target_root, replace=replace)
    print(
        f"{OSWORLD_2_DOMAIN}: {result}; cases={OSWORLD_2_EXPECTED_CASES}; "
        f"root={target_root}"
    )


def read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PacketBuildError(f"unable to read JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PacketBuildError(f"{path} must contain a JSON object")
    return value


def verify_packet_root(root: Path, *, expected_domain: str) -> dict[str, Any]:
    if not root.is_dir():
        raise PacketBuildError(f"packet root does not exist: {root}")
    index = read_json_object(root / "index.json")
    source_lock = read_json_object(root / "source_lock.json")
    status = read_json_object(root / "generation_status.json")
    if index.get("domain") != expected_domain or source_lock.get("domain") != expected_domain:
        raise PacketBuildError(f"domain mismatch in {root}")
    if index.get("source_lock_sha256") != sha256_file(root / "source_lock.json"):
        raise PacketBuildError(f"source lock hash mismatch in {root}")
    if status.get("index_sha256") != sha256_file(root / "index.json"):
        raise PacketBuildError(f"index hash mismatch in generation status for {root}")
    rows = index.get("cases")
    if not isinstance(rows, list):
        raise PacketBuildError(f"index cases must be a list in {root}")
    if int(index.get("case_count", -1)) != len(rows):
        raise PacketBuildError(f"case count mismatch in {root}")
    if index.get("status") == "blocked_gated_source_unavailable":
        if rows or expected_domain != OSWORLD_2_DOMAIN:
            raise PacketBuildError("invalid blocked packet index")
        return {
            "domain": expected_domain,
            "status": "blocked_gated_source_unavailable",
            "case_count": 0,
            "tree_sha256": tree_sha256(root),
        }

    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise PacketBuildError(f"non-object case row in {root}")
        case_id = str(row.get("case_unit_id") or "")
        if not case_id or case_id in seen:
            raise PacketBuildError(f"missing or duplicate case ID {case_id!r} in {root}")
        seen.add(case_id)
        case_dir = root / case_id
        required = (
            "agent_input.json",
            "case_packet.json",
            "case_packet.md",
            "raw_case_manifest.json",
        )
        for name in required:
            path = case_dir / name
            if not path.is_file():
                raise PacketBuildError(f"missing {path}")
            expected_hash = row.get("files", {}).get(name)
            if expected_hash != sha256_file(path):
                raise PacketBuildError(f"hash mismatch for {path}")
        packet = read_json_object(case_dir / "case_packet.json")
        agent_input = read_json_object(case_dir / "agent_input.json")
        manifest = read_json_object(case_dir / "raw_case_manifest.json")
        if packet.get("visibility") != "controller_and_human_review_only":
            raise PacketBuildError(f"invalid packet visibility for {case_id}")
        if set(agent_input) != {"instruction"}:
            raise PacketBuildError(f"agent input allowlist violation for {case_id}")
        if FORBIDDEN_AGENT_INPUT_KEYS & set(agent_input):
            raise PacketBuildError(f"forbidden agent input key for {case_id}")
        model_ref = packet.get("model_visible_input")
        if not isinstance(model_ref, Mapping) or model_ref.get("sha256") != sha256_file(
            case_dir / "agent_input.json"
        ):
            raise PacketBuildError(f"agent input pointer mismatch for {case_id}")
        raw_hashes = manifest.get("sha256_per_file")
        if not isinstance(raw_hashes, Mapping):
            raise PacketBuildError(f"missing raw file hashes for {case_id}")
        for relative, expected_hash in raw_hashes.items():
            raw_path = case_dir / "raw_case" / str(relative)
            if not raw_path.is_file() or sha256_file(raw_path) != expected_hash:
                raise PacketBuildError(f"raw source hash mismatch for {raw_path}")
        markdown = (case_dir / "case_packet.md").read_text(encoding="utf-8")
        for key in ("domain", "case_unit_id", "task_id"):
            if f"- {key}: `" not in markdown:
                raise PacketBuildError(f"case metadata line {key} missing for {case_id}")
        if "## Source Inventory" not in markdown:
            raise PacketBuildError(f"source inventory missing for {case_id}")
        if expected_domain == OSWORLD_VERIFIED_DOMAIN:
            task_source = read_json_object(
                case_dir / "raw_case" / "official" / "task.json"
            )
            contract_path = (
                case_dir / "raw_case" / "derived" / "evaluator_contract.json"
            )
            contract = read_json_object(contract_path)
            evaluator_ref = packet.get("evaluator_reference")
            if not isinstance(evaluator_ref, Mapping):
                raise PacketBuildError(f"missing evaluator reference for {case_id}")
            if evaluator_ref.get("contract_sha256") != sha256_file(contract_path):
                raise PacketBuildError(f"evaluator contract hash mismatch for {case_id}")
            evaluator = task_source.get("evaluator")
            if not isinstance(evaluator, Mapping):
                raise PacketBuildError(f"task evaluator missing for {case_id}")
            extraction = contract.get("extraction")
            if not isinstance(extraction, Mapping) or extraction.get(
                "evaluator_config_sha256"
            ) != sha256_bytes(canonical_bytes(evaluator)):
                raise PacketBuildError(
                    f"evaluator contract is not bound to task config for {case_id}"
                )
            functions, list_mode = _evaluator_names(task_source)
            metrics = contract.get("metrics")
            if not isinstance(metrics, list) or [
                item.get("name") for item in metrics if isinstance(item, Mapping)
            ] != functions:
                raise PacketBuildError(f"metric contract mismatch for {case_id}")
            if contract.get("list_mode") is not list_mode:
                raise PacketBuildError(f"metric list-mode mismatch for {case_id}")
            if contract.get("conjunction") != evaluator.get("conj", "and"):
                raise PacketBuildError(f"metric conjunction mismatch for {case_id}")
            official_sources = contract.get("official_source_files")
            if not isinstance(official_sources, list) or not official_sources:
                raise PacketBuildError(f"official evaluator sources missing for {case_id}")
            for source in official_sources:
                if not isinstance(source, Mapping):
                    raise PacketBuildError(f"invalid evaluator source for {case_id}")
                relative = str(source.get("packet_path") or "")
                source_path = case_dir / "raw_case" / relative
                if not source_path.is_file() or source.get("sha256") != sha256_file(
                    source_path
                ):
                    raise PacketBuildError(
                        f"official evaluator source hash mismatch for {case_id}: "
                        f"{relative}"
                    )
                source_ref = str(source.get("source_ref") or "")
                if OSWORLD_VERIFIED_COMMIT not in source_ref:
                    raise PacketBuildError(
                        f"evaluator source is not immutable for {case_id}: {source_ref}"
                    )
                if f"- `{relative}`" not in markdown:
                    raise PacketBuildError(
                        f"evaluator source missing from inventory for {case_id}: "
                        f"{relative}"
                    )
            exact_excerpts = contract.get("exact_source_excerpts")
            if not isinstance(exact_excerpts, list) or not exact_excerpts:
                raise PacketBuildError(f"evaluator excerpts missing for {case_id}")
            excerpt_symbols: set[str] = set()
            for excerpt in exact_excerpts:
                if not isinstance(excerpt, Mapping):
                    raise PacketBuildError(f"invalid evaluator excerpt for {case_id}")
                relative = str(excerpt.get("packet_path") or "")
                source_path = case_dir / "raw_case" / relative
                source_bytes = source_path.read_bytes()
                if excerpt.get("source_sha256") != sha256_bytes(source_bytes):
                    raise PacketBuildError(
                        f"excerpt full-source hash mismatch for {case_id}: {relative}"
                    )
                start = int(excerpt.get("start_line", 0))
                end = int(excerpt.get("end_line", 0))
                lines = source_bytes.decode("utf-8").splitlines(keepends=True)
                if start < 1 or end < start or end > len(lines):
                    raise PacketBuildError(
                        f"invalid evaluator excerpt span for {case_id}: {relative}"
                    )
                excerpt_bytes = "".join(lines[start - 1 : end]).encode("utf-8")
                if excerpt.get("excerpt_sha256") != sha256_bytes(excerpt_bytes):
                    raise PacketBuildError(
                        f"evaluator excerpt hash mismatch for {case_id}: {relative}"
                    )
                excerpt_text = excerpt_bytes.decode("utf-8").rstrip()
                excerpt_hash = str(excerpt.get("excerpt_sha256") or "")
                if (
                    excerpt_text not in markdown
                    or f"Exact excerpt SHA-256: `{excerpt_hash}`" not in markdown
                ):
                    raise PacketBuildError(
                        f"exact evaluator excerpt is not embedded in markdown for "
                        f"{case_id}: {relative}"
                    )
                excerpt_symbols.add(str(excerpt.get("symbol") or ""))
            required_symbols = {
                "DesktopEnv._set_evaluator_info",
                "DesktopEnv.evaluate",
                *functions,
                *(
                    str(item.get("symbol") or "")
                    for getter_key in ("result_getters", "expected_getters")
                    for item in contract.get(getter_key, [])
                    if isinstance(item, Mapping)
                ),
            }
            if not required_symbols <= excerpt_symbols:
                missing = sorted(required_symbols - excerpt_symbols)
                raise PacketBuildError(
                    f"evaluator excerpt closure incomplete for {case_id}: {missing}"
                )
            if (
                "## Evaluator Contract" not in markdown
                or "## Exact Official Evaluator Source Excerpts" not in markdown
            ):
                raise PacketBuildError(
                    f"source-rich evaluator markdown missing for {case_id}"
                )
        elif expected_domain == OSWORLD_2_DOMAIN:
            expected_raw_paths = {
                "derived/agent_visible_task.json",
                "controller/gated_source_pointer.json",
                "public/release_manifest.json",
            }
            if set(str(path) for path in raw_hashes) != expected_raw_paths:
                raise PacketBuildError(
                    f"unexpected OSWorld 2.0 raw packet files for {case_id}"
                )
            if any(path.suffix in {".py", ".pyc"} for path in case_dir.rglob("*")):
                raise PacketBuildError(
                    f"gated Python implementation embedded for {case_id}"
                )
            leakage = packet.get("leakage_control")
            if not isinstance(leakage, Mapping) or any(
                leakage.get(key) is not False
                for key in (
                    "gated_task_implementation_embedded",
                    "gated_evaluator_implementation_embedded",
                )
            ):
                raise PacketBuildError(f"invalid gated-source boundary for {case_id}")
            if manifest.get("gated_files_embedded") != [] or manifest.get(
                "gated_source_embedded"
            ) is not False:
                raise PacketBuildError(f"gated files declared embedded for {case_id}")
            pointer = read_json_object(
                case_dir / "raw_case" / "controller" / "gated_source_pointer.json"
            )
            if pointer.get("embedded") is not False or pointer.get(
                "parsed_without_execution"
            ) is not True:
                raise PacketBuildError(f"invalid gated source pointer for {case_id}")
            if pointer.get("sha256") != row.get("source_sha256") or manifest.get(
                "gated_source_sha256"
            ) != row.get("source_sha256"):
                raise PacketBuildError(f"gated source hash binding mismatch for {case_id}")

            task = packet.get("task")
            if not isinstance(task, Mapping):
                raise PacketBuildError(f"missing OSWorld 2.0 task metadata for {case_id}")
            instruction = agent_input.get("instruction")
            if task.get("instruction") != instruction:
                raise PacketBuildError(f"initial instruction mismatch for {case_id}")
            bindings = task.get("instruction_runtime_bindings")
            if (
                not isinstance(bindings, list)
                or bindings != sorted(set(str(item) for item in bindings))
                or bindings != row.get("instruction_runtime_bindings")
            ):
                raise PacketBuildError(f"runtime binding mismatch for {case_id}")
            public_placeholders = {
                public_name for public_name, _ in OSWORLD_2_RUNTIME_PLACEHOLDERS.values()
            }
            phase_values = task.get("phases", [])
            visible_instruction_texts = [str(instruction)]
            if isinstance(phase_values, list):
                visible_instruction_texts.extend(
                    str(phase.get("instruction") or "")
                    for phase in phase_values
                    if isinstance(phase, Mapping)
                )
            placeholders = set(
                re.findall(
                    r"\{\{([A-Z][A-Z0-9_]*)\}\}",
                    "\n".join(visible_instruction_texts),
                )
            )
            if not placeholders <= public_placeholders or placeholders != set(bindings):
                raise PacketBuildError(f"unbound runtime placeholder for {case_id}")

            is_multiphase = task.get("is_multiphase")
            if case_id == "069":
                if is_multiphase is not True or task.get("phase_count") != 4:
                    raise PacketBuildError("task 069 multi-phase metadata is incomplete")
                if task.get("multiphase_delivery") != (
                    "sequential_no_future_phase_prefetch"
                ):
                    raise PacketBuildError("task 069 delivery boundary is invalid")
                if not isinstance(phase_values, list) or len(phase_values) != 4:
                    raise PacketBuildError("task 069 must expose four controller phases")
                expected_phases = OSWORLD_2_MULTIPHASE_CONTRACT["phases"]
                for phase, expected in zip(phase_values, expected_phases):
                    if not isinstance(phase, Mapping):
                        raise PacketBuildError("task 069 contains an invalid phase")
                    name, _, weight, gate = expected
                    phase_index = expected_phases.index(expected) + 1
                    if (
                        phase.get("index") != phase_index
                        or phase.get("name") != name
                        or phase.get("weight") != weight
                        or phase.get("gate_min_score") != gate
                        or not str(phase.get("instruction") or "").strip()
                    ):
                        raise PacketBuildError(
                            f"task 069 phase {phase_index} contract mismatch"
                        )
                if instruction != phase_values[0].get("instruction"):
                    raise PacketBuildError(
                        "task 069 initial agent input must contain phase 1 only"
                    )
                entrypoints = pointer.get("evaluator_entrypoints")
                if not isinstance(entrypoints, list) or "get_phases" not in entrypoints:
                    raise PacketBuildError("task 069 get_phases pointer is missing")
            elif is_multiphase is not False or task.get("phase_count") != 0:
                raise PacketBuildError(f"unexpected multi-phase metadata for {case_id}")

    if index.get("case_rows_sha256") != sha256_bytes(canonical_bytes(rows)):
        raise PacketBuildError(f"case row aggregate hash mismatch in {root}")
    expected_count = (
        OSWORLD_VERIFIED_EXPECTED_CASES
        if expected_domain == OSWORLD_VERIFIED_DOMAIN
        else OSWORLD_2_EXPECTED_CASES
    )
    if len(rows) != expected_count:
        raise PacketBuildError(
            f"expected {expected_count} cases in {root}, observed {len(rows)}"
        )
    return {
        "domain": expected_domain,
        "status": str(index.get("status")),
        "case_count": len(rows),
        "index_sha256": sha256_file(root / "index.json"),
        "source_lock_sha256": sha256_file(root / "source_lock.json"),
        "tree_sha256": tree_sha256(root),
    }


def selected_domains(value: str) -> Iterable[str]:
    if value == "all":
        return (OSWORLD_VERIFIED_DOMAIN, OSWORLD_2_DOMAIN)
    return (value,)


def main() -> int:
    args = parse_args()
    output_root = args.output_root.resolve()
    domains = tuple(selected_domains(args.benchmark))
    if args.verify_only:
        blocked = False
        for domain in domains:
            report = verify_packet_root(output_root / domain, expected_domain=domain)
            print(json.dumps(report, ensure_ascii=False, sort_keys=True))
            blocked = blocked or report["status"] == "blocked_gated_source_unavailable"
        return 2 if blocked else 0

    gated_error: GatedSourceUnavailable | None = None
    for domain in domains:
        if domain == OSWORLD_VERIFIED_DOMAIN:
            build_osworld_verified(
                output_root, workers=args.workers, replace=args.replace
            )
        else:
            try:
                build_osworld2(
                    output_root,
                    task_root=args.osworld2_task_root,
                    hash_manifest_path=args.osworld2_hash_manifest,
                    replace=args.replace,
                )
            except GatedSourceUnavailable as exc:
                gated_error = exc
    if gated_error is not None:
        raise gated_error
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GatedSourceUnavailable as exc:
        print(f"OSWorld 2.0 packet generation blocked: {exc}", file=sys.stderr)
        raise SystemExit(2)
    except PacketBuildError as exc:
        print(f"OSWorld packet build failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
