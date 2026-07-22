#!/usr/bin/env python3
"""Stdlib-only admission gate for the frozen semantic-review toolchain.

This file is never trusted by path alone.  The prelock prints a ``python -I
-S -B -c`` launcher which hashes these bytes before executing them.  The gate
then revalidates the prelock, the complete Python runtime trees, and the exact
toolchain snapshot before importing any project or third-party module.
"""

from __future__ import annotations

import hashlib
import json
import os
import runpy
import sys
from pathlib import Path
from typing import Any


def fail(message: str) -> None:
    raise SystemExit(f"SEMANTIC_REVIEW_BOOTSTRAP_ERROR: {message}")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def object_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot load {label}: {exc}")
    if not isinstance(value, dict):
        fail(f"{label} is not an object")
    return value


def verify_self_hash(value: dict[str, Any], field: str, label: str) -> None:
    core = dict(value)
    claimed = core.pop(field, None)
    if not isinstance(claimed, str) or claimed != object_sha256(core):
        fail(f"{label} {field} differs")


def canonical_tree(
    root: Path, *, excluded_directory_names: frozenset[str] = frozenset()
) -> dict[str, Any]:
    root = Path(os.path.abspath(root))
    if not root.is_dir():
        fail(f"runtime tree root is missing: {root}")
    rows: list[dict[str, Any]] = []

    def visit(directory: Path, relative_directory: Path) -> None:
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as exc:
            fail(f"cannot enumerate runtime tree {directory}: {exc}")
        for entry in entries:
            relative = relative_directory / entry.name
            absolute = Path(entry.path)
            if entry.name in excluded_directory_names and entry.is_dir(follow_symlinks=False):
                continue
            portable = relative.as_posix()
            metadata = absolute.lstat()
            if absolute.is_symlink():
                rows.append(
                    {"path": portable, "kind": "symlink", "target": os.readlink(absolute)}
                )
            elif absolute.is_dir():
                rows.append({"path": portable, "kind": "directory"})
                visit(absolute, relative)
            elif absolute.is_file():
                rows.append(
                    {
                        "path": portable,
                        "kind": "regular_file",
                        "size_bytes": metadata.st_size,
                        "sha256": sha256_file(absolute),
                    }
                )
            else:
                fail(f"unsupported special file in runtime tree: {absolute}")

    visit(root, Path())
    return {
        "root": str(root),
        "entry_count": len(rows),
        "regular_file_count": sum(row["kind"] == "regular_file" for row in rows),
        "directory_count": sum(row["kind"] == "directory" for row in rows),
        "symlink_count": sum(row["kind"] == "symlink" for row in rows),
        "total_regular_file_bytes": sum(
            int(row.get("size_bytes") or 0)
            for row in rows
            if row["kind"] == "regular_file"
        ),
        "tree_sha256": object_sha256(rows),
        "entries": rows,
    }


def verify_tree(
    expected: Any, label: str, *, exclude_site_directories: bool = False
) -> None:
    if not isinstance(expected, dict):
        fail(f"{label} descriptor is missing")
    observed = canonical_tree(
        Path(str(expected.get("root") or "")),
        excluded_directory_names=(
            frozenset({"site-packages", "dist-packages"})
            if exclude_site_directories
            else frozenset()
        ),
    )
    if observed != expected:
        fail(f"{label} changed")


def verify_runtime(runtime: Any) -> None:
    if not isinstance(runtime, dict):
        fail("Python runtime binding is missing")
    flags = {
        "isolated": int(sys.flags.isolated),
        "no_site": int(sys.flags.no_site),
        "ignore_environment": int(sys.flags.ignore_environment),
        "safe_path": bool(getattr(sys.flags, "safe_path", False)),
    }
    required_flags = {"isolated": 1, "no_site": 1, "ignore_environment": 1, "safe_path": True}
    if flags != required_flags or runtime.get("required_execution_flags") != required_flags:
        fail(f"interpreter flags differ: {flags}")
    if not sys.dont_write_bytecode or runtime.get("required_execution_state") != {
        "dont_write_bytecode": True
    }:
        fail("bytecode writes are not disabled")
    if os.environ.get("PYTHONSAFEPATH") is not None:
        fail("PYTHONSAFEPATH must be absent; -I supplies safe-path semantics")
    invocation = os.path.abspath(sys.executable)
    resolved = str(Path(invocation).resolve(strict=True))
    if invocation != runtime.get("invocation_path"):
        fail("Python invocation path differs")
    if (
        resolved != runtime.get("resolved_binary_path")
        or sha256_file(Path(resolved)) != runtime.get("resolved_binary_sha256")
    ):
        fail("Python executable bytes differ")
    site_trees = runtime.get("site_packages_trees")
    if not isinstance(site_trees, dict) or object_sha256(site_trees) != runtime.get(
        "site_packages_trees_sha256"
    ):
        fail("site-packages tree index differs")
    for root, tree in site_trees.items():
        if not isinstance(tree, dict) or tree.get("root") != root:
            fail("site-packages root/descriptor differs")
        verify_tree(tree, f"site-packages {root}")
    library_trees = runtime.get("stdlib_platstdlib_trees")
    if not isinstance(library_trees, dict) or object_sha256(library_trees) != runtime.get(
        "stdlib_platstdlib_trees_sha256"
    ):
        fail("stdlib tree index differs")
    for root, record in library_trees.items():
        if not isinstance(record, dict) or not isinstance(record.get("tree"), dict):
            fail("stdlib tree record is malformed")
        if record["tree"].get("root") != root:
            fail("stdlib root/descriptor differs")
        verify_tree(record["tree"], f"stdlib {root}", exclude_site_directories=True)
    extras = runtime.get("extra_sys_path_entries")
    if not isinstance(extras, list) or object_sha256(extras) != runtime.get(
        "extra_sys_path_entries_sha256"
    ):
        fail("extra sys.path index differs")
    expected_sys_path = runtime.get("expected_runner_sys_path")
    if not isinstance(expected_sys_path, list) or not expected_sys_path:
        fail("expected sys.path is missing")
    for item in extras:
        if not isinstance(item, dict):
            fail("extra sys.path row is malformed")
        index = item.get("index")
        path = Path(str(item.get("path") or ""))
        if not isinstance(index, int) or index <= 0 or index >= len(expected_sys_path):
            fail("extra sys.path index is invalid")
        if os.path.abspath(str(path)) != os.path.abspath(str(expected_sys_path[index])):
            fail("extra sys.path path/index differs")
        kind = item.get("kind")
        if kind == "covered_by_runtime_tree":
            root = str(item.get("root") or "")
            if root not in site_trees and root not in library_trees:
                fail("extra sys.path covered root is unknown")
        elif kind == "regular_file":
            if (
                not path.is_file()
                or path.stat().st_size != item.get("size_bytes")
                or sha256_file(path) != item.get("sha256")
            ):
                fail(f"extra sys.path file changed: {path}")
        elif kind == "directory_tree":
            verify_tree(item.get("tree"), f"extra sys.path directory {path}")
        elif kind == "expected_absent":
            if path.exists() or path.is_symlink():
                fail(f"expected-absent sys.path entry appeared: {path}")
        else:
            fail(f"unknown extra sys.path kind: {kind}")
    if runtime.get("live_repository_source_excluded") is not True:
        fail("runtime does not attest exclusion of live repository source")
    live_source = os.path.abspath(str(runtime.get("live_repository_source_path") or ""))
    if not live_source or any(os.path.abspath(str(item)) == live_source for item in expected_sys_path):
        fail("live repository source remains on frozen sys.path")
    forbidden = runtime.get("forbidden_child_python_environment")
    required_environment = runtime.get("required_environment")
    if not isinstance(forbidden, list) or not isinstance(required_environment, dict):
        fail("child environment policy is missing")
    for variable in forbidden:
        os.environ.pop(str(variable), None)
    os.environ.update({str(key): str(value) for key, value in required_environment.items()})
    if any(str(variable) in os.environ for variable in forbidden):
        fail("forbidden Python environment survived sanitization")
    sys.prefix = str(runtime.get("sys_prefix"))
    sys.base_prefix = str(runtime.get("sys_base_prefix"))
    sys.exec_prefix = str(runtime.get("sys_exec_prefix"))
    sys.base_exec_prefix = str(runtime.get("sys_base_exec_prefix"))
    sys.path[:] = [str(item) for item in expected_sys_path]


def parse_args(argv: list[str]) -> tuple[dict[str, str], list[str]]:
    names = (
        "--prelock",
        "--prelock-file-sha256",
        "--prelock-internal-sha256",
        "--snapshot-tree-sha256",
        "--target-role",
    )
    values: dict[str, str] = {}
    position = 0
    while position < len(argv):
        token = argv[position]
        if token == "--":
            return values, argv[position + 1 :]
        if token not in names or position + 1 >= len(argv) or token in values:
            fail(f"invalid bootstrap argument sequence near {token!r}")
        values[token] = argv[position + 1]
        position += 2
    return values, []


def main() -> int:
    values, target_args = parse_args(sys.argv[1:])
    required = {
        "--prelock",
        "--prelock-file-sha256",
        "--prelock-internal-sha256",
        "--snapshot-tree-sha256",
        "--target-role",
    }
    if set(values) != required:
        fail("bootstrap arguments are incomplete")
    prelock_path = Path(values["--prelock"]).resolve(strict=True)
    if sha256_file(prelock_path) != values["--prelock-file-sha256"]:
        fail("prelock physical hash differs from launch command")
    prelock = load_json(prelock_path, "semantic-review prelock")
    verify_self_hash(prelock, "prelock_sha256", "semantic-review prelock")
    if prelock.get("prelock_sha256") != values["--prelock-internal-sha256"]:
        fail("prelock internal hash differs from launch command")
    bootstrap = prelock.get("isolated_bootstrap")
    if not isinstance(bootstrap, dict):
        fail("prelock has no isolated-bootstrap binding")
    if (
        bootstrap.get("schema_version")
        != "androidworld_semantic_review_isolated_bootstrap/v1"
        or bootstrap.get("entrypoint_sha256") != sha256_file(Path(__file__).resolve())
        or hashlib.sha256(str(bootstrap.get("launcher_source") or "").encode("utf-8")).hexdigest()
        != bootstrap.get("launcher_sha256")
        or bootstrap.get("required_python_flags") != ["-I", "-S", "-B"]
    ):
        fail("executed bootstrap bytes differ from prelock")
    runtime_binding = prelock.get("python_runtime")
    if not isinstance(runtime_binding, dict):
        fail("prelock has no Python runtime file binding")
    runtime_path = Path(str(runtime_binding.get("path") or ""))
    if not runtime_path.is_absolute():
        runtime_path = Path(str(prelock.get("repository_root") or "")) / runtime_path
    runtime_path = runtime_path.resolve(strict=True)
    if (
        runtime_path.stat().st_size != runtime_binding.get("size_bytes")
        or sha256_file(runtime_path) != runtime_binding.get("sha256")
    ):
        fail("Python runtime file binding differs")
    runtime = load_json(runtime_path, "Python runtime binding")
    verify_self_hash(runtime, "runtime_sha256", "Python runtime binding")
    if runtime.get("runtime_sha256") != runtime_binding.get("runtime_sha256"):
        fail("Python runtime internal hash differs from prelock")
    verify_runtime(runtime)
    snapshot_tree = prelock.get("toolchain_exact_tree")
    if (
        not isinstance(snapshot_tree, dict)
        or snapshot_tree.get("tree_sha256") != values["--snapshot-tree-sha256"]
    ):
        fail("toolchain snapshot launch binding differs")
    verify_tree(snapshot_tree, "semantic-review toolchain snapshot")
    snapshot_binding = prelock.get("toolchain_snapshot")
    if not isinstance(snapshot_binding, dict):
        fail("toolchain snapshot manifest binding is missing")
    snapshot_path = Path(str(snapshot_binding.get("path") or ""))
    if not snapshot_path.is_absolute():
        snapshot_path = Path(str(prelock.get("repository_root") or "")) / snapshot_path
    snapshot_path = snapshot_path.resolve(strict=True)
    if (
        snapshot_path.stat().st_size != snapshot_binding.get("size_bytes")
        or sha256_file(snapshot_path) != snapshot_binding.get("sha256")
    ):
        fail("toolchain snapshot manifest bytes differ")
    snapshot = load_json(snapshot_path, "toolchain snapshot manifest")
    verify_self_hash(snapshot, "snapshot_sha256", "toolchain snapshot manifest")
    if snapshot.get("snapshot_sha256") != snapshot_binding.get("snapshot_sha256"):
        fail("toolchain snapshot internal hash differs")
    security_payload = prelock.get("security_content_payload")
    execution_payload = prelock.get("execution_security_payload")
    if (
        not isinstance(security_payload, dict)
        or object_sha256(security_payload) != prelock.get("security_content_address")
        or not isinstance(execution_payload, dict)
        or object_sha256(execution_payload) != prelock.get("execution_security_address")
    ):
        fail("semantic-review security content address differs")
    expected_execution = {
        "security_content_address": prelock.get("security_content_address"),
        "case_inputs_sha256": prelock.get("case_inputs_sha256"),
        "config_sha256": (prelock.get("review_config") or {}).get("config_sha256"),
        "python_runtime_sha256": runtime.get("runtime_sha256"),
        "toolchain_snapshot_sha256": snapshot.get("snapshot_sha256"),
        "toolchain_exact_tree_sha256": snapshot_tree.get("tree_sha256"),
        "bootstrap_launcher_sha256": bootstrap.get("launcher_sha256"),
        "bootstrap_entrypoint_sha256": bootstrap.get("entrypoint_sha256"),
    }
    if execution_payload != expected_execution:
        fail("semantic-review execution security payload differs")
    role = values["--target-role"]
    if role not in {"batch_runner", "independent_validator"}:
        fail(f"target role is forbidden: {role}")
    tools = prelock.get("tool_bindings")
    binding = tools.get(role) if isinstance(tools, dict) else None
    if not isinstance(binding, dict):
        fail(f"target role is unbound: {role}")
    target = Path(str(binding.get("path") or ""))
    if not target.is_absolute():
        target = Path(str(prelock.get("repository_root") or "")) / target
    target = target.resolve(strict=True)
    if target.stat().st_size != binding.get("size_bytes") or sha256_file(target) != binding.get(
        "sha256"
    ):
        fail(f"target role bytes differ: {role}")
    snapshot_root = Path(str(prelock.get("toolchain_snapshot_root_absolute") or "")).resolve(
        strict=True
    )
    try:
        target.relative_to(snapshot_root)
    except ValueError:
        fail("target role escapes the frozen toolchain")
    sys._androidworld_semantic_review_bootstrap = prelock["prelock_sha256"]
    sys._androidworld_semantic_review_prelock_file_sha256 = values[
        "--prelock-file-sha256"
    ]
    sys.argv = [str(target), *target_args]
    runpy.run_path(str(target), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
