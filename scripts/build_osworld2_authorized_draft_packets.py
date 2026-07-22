#!/usr/bin/env python3
"""Build private, source-complete OSWorld 2.0 packets for checklist drafting.

The public OSWorld 2.0 packets intentionally retain only a hash-pinned pointer
to the gated task class.  That is the correct publication boundary, but it is
not enough input for ``draft_case_checklist.py``: the drafter reads only
``case_packet.md`` and therefore cannot follow a gated source pointer.

This script creates a separate, ignored packet overlay for an authorized user.
For each of the 108 cases it verifies the official gated task against the
release hash manifest, embeds the exact task class in ``case_packet.md``, and
adds the directly referenced public OSWorld evaluator/helper sources from the
pinned Git commit.  It never imports or executes a task module.  It also never
adds a trajectory, generated artifact, result, or observed score.

The output is private controller/drafter material.  Do not commit, publish, or
place it in the tested agent's prompt.  The tested agent still receives only
``agent_input.json`` at benchmark runtime.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import shutil
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from build_osworld_case_packets import (
    OSWORLD_2_CODE_COMMIT,
    OSWORLD_2_CODE_REPOSITORY,
    OSWORLD_2_EXPECTED_CASES,
    OSWORLD_2_RELEASE,
    OSWORLD_2_TASK_COMMIT,
    OSWORLD_2_TASK_HASH_MANIFEST_SHA256,
    OSWORLD_2_TASK_REPOSITORY,
    canonical_bytes,
    extract_task_hashes,
    normalize_hash,
    sha256_bytes,
    sha256_file,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PUBLIC_PACKET_ROOT = (
    PROJECT_ROOT / "experiments" / "case_packets" / "osworld_2_0"
)
DEFAULT_PRIVATE_PACKET_ROOT = (
    PROJECT_ROOT / "experiments" / "private_case_packets" / "osworld_2_0"
)
OFFICIAL_PUBLIC_PREFIXES = ("desktop_env", "evaluation_examples")
PRIVATE_STATUS = "ready_authorized_evaluator_source_embedded"
TASK_LOGICAL_PATH = "authorized/official_task.py"
PUBLIC_LOGICAL_PREFIX = "official_public/"
FORBIDDEN_RUN_FILENAMES = {
    "traj.jsonl",
    "runtime.log",
    "eval.log",
    "result.txt",
    "result.json",
    "checkpoint_results.json",
}


class AuthorizedPacketBuildError(RuntimeError):
    """Raised when private packet construction cannot remain fail-closed."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--public-packet-root",
        type=Path,
        default=DEFAULT_PUBLIC_PACKET_ROOT,
        help="Existing 108-case public pointer-only OSWorld 2.0 packet root.",
    )
    parser.add_argument(
        "--authorized-task-root",
        type=Path,
        required=True,
        help="Authorized xlangai/osworld_v2_tasks task_*.py directory.",
    )
    parser.add_argument(
        "--hash-manifest",
        type=Path,
        required=True,
        help="Authorized manifests/task_hashes.json from the same revision.",
    )
    parser.add_argument(
        "--official-code-root",
        type=Path,
        required=True,
        help="OSWorld-V2 Git checkout at the pinned public code commit.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_PRIVATE_PACKET_ROOT,
        help="Private domain packet root to create.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace an existing private output root after building and validating a new one.",
    )
    return parser.parse_args()


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(pretty_json(value), encoding="utf-8")


def read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuthorizedPacketBuildError(f"unable to read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AuthorizedPacketBuildError(f"expected a JSON object in {path}")
    return value


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def require_git_commit(code_root: Path) -> None:
    result = subprocess.run(
        ["git", "-C", str(code_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AuthorizedPacketBuildError(
            f"official code root is not a readable Git checkout: {code_root}"
        )
    observed = result.stdout.strip()
    if observed != OSWORLD_2_CODE_COMMIT:
        raise AuthorizedPacketBuildError(
            "OSWorld-V2 code commit mismatch: "
            f"expected {OSWORLD_2_CODE_COMMIT}, observed {observed}"
        )


def require_authorized_inputs(
    task_root: Path, hash_manifest_path: Path
) -> dict[str, str]:
    manifest_bytes = hash_manifest_path.read_bytes()
    observed_manifest_sha = sha256_bytes(manifest_bytes)
    if observed_manifest_sha != OSWORLD_2_TASK_HASH_MANIFEST_SHA256:
        raise AuthorizedPacketBuildError(
            "OSWorld 2.0 task hash manifest mismatch: "
            f"expected {OSWORLD_2_TASK_HASH_MANIFEST_SHA256}, "
            f"observed {observed_manifest_sha}"
        )
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuthorizedPacketBuildError(f"invalid task hash manifest: {exc}") from exc
    hashes = extract_task_hashes(manifest)
    if len(hashes) != OSWORLD_2_EXPECTED_CASES:
        raise AuthorizedPacketBuildError(
            f"expected {OSWORLD_2_EXPECTED_CASES} task hashes, observed {len(hashes)}"
        )
    task_paths = sorted(task_root.glob("task_*.py"))
    if len(task_paths) != OSWORLD_2_EXPECTED_CASES:
        raise AuthorizedPacketBuildError(
            f"expected {OSWORLD_2_EXPECTED_CASES} task files, observed {len(task_paths)}"
        )
    if {path.name for path in task_paths} != set(hashes):
        raise AuthorizedPacketBuildError(
            "authorized task filenames do not match the official hash manifest"
        )
    for path in task_paths:
        if sha256_file(path) != hashes[path.name]:
            raise AuthorizedPacketBuildError(
                f"authorized task hash mismatch for {path.name}"
            )
    return hashes


def module_name(code_root: Path, path: Path) -> str:
    parts = list(path.relative_to(code_root).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def module_level_definitions(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeDecodeError, SyntaxError) as exc:
        raise AuthorizedPacketBuildError(
            f"unable to parse official public source {path}: {exc}"
        ) from exc
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
    return names


def public_source_catalog(
    code_root: Path,
) -> tuple[dict[str, Path], dict[str, set[str]]]:
    module_paths: dict[str, Path] = {}
    definitions: dict[str, set[str]] = {}
    for prefix in OFFICIAL_PUBLIC_PREFIXES:
        prefix_root = code_root / prefix
        if not prefix_root.is_dir():
            raise AuthorizedPacketBuildError(
                f"pinned public code root lacks required package {prefix}"
            )
        for path in sorted(prefix_root.rglob("*.py")):
            name = module_name(code_root, path)
            if name in module_paths:
                raise AuthorizedPacketBuildError(f"duplicate public module {name}")
            module_paths[name] = path
            definitions[name] = module_level_definitions(path)
    return module_paths, definitions


def is_official_public_module(name: str | None) -> bool:
    return bool(
        name
        and any(name == prefix or name.startswith(prefix + ".") for prefix in OFFICIAL_PUBLIC_PREFIXES)
    )


def public_support_sources(
    task_path: Path,
    module_paths: Mapping[str, Path],
    definitions: Mapping[str, set[str]],
) -> list[Path]:
    """Select exact public modules directly needed to interpret one task source."""

    try:
        tree = ast.parse(task_path.read_text(encoding="utf-8"), filename=str(task_path))
    except (OSError, UnicodeDecodeError, SyntaxError) as exc:
        raise AuthorizedPacketBuildError(f"unable to parse {task_path}: {exc}") from exc

    selected: set[Path] = set()
    aliases: dict[str, tuple[str, str | None]] = {}
    type_only_import_ids: set[int] = set()
    for candidate in ast.walk(tree):
        if not isinstance(candidate, ast.If):
            continue
        is_type_checking = (
            isinstance(candidate.test, ast.Name)
            and candidate.test.id == "TYPE_CHECKING"
        ) or (
            isinstance(candidate.test, ast.Attribute)
            and candidate.test.attr == "TYPE_CHECKING"
        )
        if not is_type_checking:
            continue
        for statement in candidate.body:
            for nested in ast.walk(statement):
                if isinstance(nested, (ast.Import, ast.ImportFrom)):
                    type_only_import_ids.add(id(nested))

    def add_module(name: str) -> None:
        path = module_paths.get(name)
        if path is not None:
            selected.add(path)

    def add_symbol(module: str, symbol: str) -> None:
        # Keep the importing module/package for exact export semantics.
        add_module(module)
        submodule = f"{module}.{symbol}"
        add_module(submodule)
        candidates = [
            module_paths[name]
            for name in sorted(module_paths)
            if (name == module or name.startswith(module + "."))
            and symbol in definitions.get(name, set())
        ]
        selected.update(candidates)

    # Official tasks sometimes guard OSWorld imports with ``try/except`` so
    # evaluator-only local tooling can parse the file without the full runtime.
    # Walk the full AST to retain those imports as well as method-local helper
    # imports; this still performs no import or execution.
    for node in ast.walk(tree):
        if id(node) in type_only_import_ids:
            continue
        if isinstance(node, ast.ImportFrom) and is_official_public_module(node.module):
            assert node.module is not None
            add_module(node.module)
            for alias in node.names:
                if alias.name == "*":
                    raise AuthorizedPacketBuildError(
                        f"unsupported wildcard official import in {task_path.name}: {node.module}"
                    )
                aliases[alias.asname or alias.name] = (node.module, alias.name)
                add_symbol(node.module, alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if is_official_public_module(alias.name):
                    add_module(alias.name)
                    aliases[alias.asname or alias.name.split(".", 1)[0]] = (
                        alias.name,
                        None,
                    )

    # ``from desktop_env.evaluators import getters, metrics`` is a common
    # package import.  Resolve every attribute the task actually uses to the
    # public module that defines it, without importing benchmark code.
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute) or not isinstance(node.value, ast.Name):
            continue
        binding = aliases.get(node.value.id)
        if binding is None:
            continue
        imported_module, imported_symbol = binding
        if imported_symbol is None:
            base_module = imported_module
        else:
            possible_submodule = f"{imported_module}.{imported_symbol}"
            if possible_submodule not in module_paths:
                continue
            base_module = possible_submodule
        add_symbol(base_module, node.attr)

    if not selected:
        raise AuthorizedPacketBuildError(
            f"no official public support source selected for {task_path.name}"
        )
    return sorted(selected)


def fenced_python(source: str) -> str:
    # Four backticks remain valid even if an upstream comment contains a
    # conventional three-backtick Markdown fence.
    return "````python\n" + source.rstrip() + "\n````\n"


def render_authorized_sources(
    *,
    task_path: Path,
    support_paths: Iterable[Path],
    code_root: Path,
) -> tuple[str, list[str], dict[str, dict[str, str]]]:
    task_source = task_path.read_text(encoding="utf-8")
    logical_paths = [TASK_LOGICAL_PATH]
    metadata: dict[str, dict[str, str]] = {
        TASK_LOGICAL_PATH: {
            "source_ref": (
                f"https://huggingface.co/datasets/{OSWORLD_2_TASK_REPOSITORY}/"
                f"resolve/{OSWORLD_2_TASK_COMMIT}/{task_path.name}"
            ),
            "sha256": sha256_file(task_path),
        }
    }
    sections = [
        "## Authorized Controller-Only Official Evaluator Sources",
        "",
        "This private drafting overlay contains the exact hash-verified official task "
        "class and the directly referenced public helper/evaluator sources. It is "
        "provided to the checklist drafter only. It contains no benchmark run, "
        "trajectory, generated artifact, result, or observed score, and it must never "
        "be shown to the tested agent. The inherited gated source pointer below records "
        "the publication-safe packet (`embedded: false`); that field does not negate "
        "the private authorized source section in this overlay.",
        "",
        f"### `{TASK_LOGICAL_PATH}`",
        "",
        f"Source ref: `{metadata[TASK_LOGICAL_PATH]['source_ref']}`",
        "",
        f"Source SHA-256: `{metadata[TASK_LOGICAL_PATH]['sha256']}`",
        "",
        fenced_python(task_source).rstrip(),
        "",
    ]
    for path in support_paths:
        relative = path.relative_to(code_root).as_posix()
        logical = PUBLIC_LOGICAL_PREFIX + relative
        logical_paths.append(logical)
        metadata[logical] = {
            "source_ref": (
                OSWORLD_2_CODE_REPOSITORY.removesuffix(".git")
                + f"/blob/{OSWORLD_2_CODE_COMMIT}/{relative}"
            ),
            "sha256": sha256_file(path),
        }
        sections.extend(
            [
                f"### `{logical}`",
                "",
                f"Source ref: `{metadata[logical]['source_ref']}`",
                "",
                f"Source SHA-256: `{metadata[logical]['sha256']}`",
                "",
                fenced_python(path.read_text(encoding="utf-8")).rstrip(),
                "",
            ]
        )
    return "\n".join(sections).rstrip() + "\n", logical_paths, metadata


def private_markdown(
    *,
    base_markdown: str,
    source_section: str,
    source_paths: Iterable[str],
) -> str:
    old_summary = (
        "- evaluator implementation: gated official task class, hash-verified and "
        "intentionally not embedded"
    )
    new_summary = (
        "- evaluator implementation: exact hash-verified official gated task class "
        "embedded only in this authorized private drafting overlay"
    )
    if old_summary not in base_markdown:
        raise AuthorizedPacketBuildError(
            "public packet summary no longer has the expected gated-source boundary"
        )
    rendered = base_markdown.replace(old_summary, new_summary, 1)
    old_boundary = (
        "The tested agent initially receives only `agent_input.json`. The official setup and "
        "evaluator implementation remain gated and are not embedded, reproduced, "
        "or paraphrased here. Formal checklist drafting requires authorized local "
        "controller review of the hash-pinned task class; this packet must not be "
        "treated as exposing hidden evaluator semantics."
    )
    new_boundary = (
        "The tested agent still receives only `agent_input.json`. This separate private "
        "drafting overlay embeds the authorized, hash-pinned official task/evaluator "
        "source solely so a controller-side checklist can state the native scoring "
        "contract. It contains no observed run output and must not be committed, "
        "published, or placed in the tested agent's context."
    )
    if old_boundary not in rendered:
        raise AuthorizedPacketBuildError(
            "public packet visibility boundary no longer matches the expected text"
        )
    rendered = rendered.replace(old_boundary, new_boundary, 1)
    inventory_end = "\n## Packet Source Files\n"
    if inventory_end not in rendered:
        raise AuthorizedPacketBuildError("packet lacks a parseable Source Inventory boundary")
    extra_inventory = "".join(f"- `{path}`\n" for path in source_paths)
    rendered = rendered.replace(
        inventory_end,
        extra_inventory + inventory_end,
        1,
    )
    return rendered.rstrip() + "\n\n" + source_section


def copy_authorized_sources(
    *,
    case_dir: Path,
    task_path: Path,
    support_paths: Iterable[Path],
    code_root: Path,
) -> dict[str, Path]:
    copied: dict[str, Path] = {}
    task_destination = case_dir / "raw_case" / TASK_LOGICAL_PATH
    task_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(task_path, task_destination)
    copied[TASK_LOGICAL_PATH] = task_destination
    for path in support_paths:
        logical = PUBLIC_LOGICAL_PREFIX + path.relative_to(code_root).as_posix()
        destination = case_dir / "raw_case" / logical
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        copied[logical] = destination
    return copied


def update_case_metadata(
    *,
    case_dir: Path,
    copied: Mapping[str, Path],
    source_metadata: Mapping[str, Mapping[str, str]],
) -> None:
    packet_path = case_dir / "case_packet.json"
    packet = read_object(packet_path)
    evaluator = packet.get("evaluator_reference")
    leakage = packet.get("leakage_control")
    if not isinstance(evaluator, dict) or not isinstance(leakage, dict):
        raise AuthorizedPacketBuildError(f"invalid public packet metadata in {case_dir}")
    evaluator.update(
        {
            "implementation_embedded": True,
            "authorized_source_path": f"raw_case/{TASK_LOGICAL_PATH}",
            "authorized_public_support_paths": [
                f"raw_case/{path}"
                for path in sorted(copied)
                if path != TASK_LOGICAL_PATH
            ],
            "draft_input_contains_observed_run_output": False,
        }
    )
    packet["formal_checklist_drafting_status"] = PRIVATE_STATUS
    leakage.update(
        {
            "gated_task_implementation_embedded": True,
            "gated_evaluator_implementation_embedded": True,
            "tested_agent_receives_authorized_sources": False,
            "drafter_receives_authorized_sources": True,
            "generated_run_output_embedded": False,
        }
    )
    packet["authorized_private_overlay"] = {
        "schema_version": "osworld_2_0_authorized_draft_overlay/v1",
        "official_task_revision": OSWORLD_2_TASK_COMMIT,
        "official_code_revision": OSWORLD_2_CODE_COMMIT,
        "publication_allowed": False,
        "tested_agent_visibility": "agent_input.json only",
        "drafter_visibility": "official case claim and evaluator source; no run output",
        "source_files": {
            path: dict(source_metadata[path]) for path in sorted(source_metadata)
        },
    }
    write_json(packet_path, packet)

    manifest_path = case_dir / "raw_case_manifest.json"
    manifest = read_object(manifest_path)
    for key in ("copied_files", "packet_files"):
        values = [str(item) for item in manifest.get(key, [])]
        manifest[key] = sorted(set(values) | set(copied))
    file_sources = manifest.setdefault("file_sources", {})
    hashes = manifest.setdefault("sha256_per_file", {})
    if not isinstance(file_sources, dict) or not isinstance(hashes, dict):
        raise AuthorizedPacketBuildError(f"invalid raw manifest maps in {case_dir}")
    for logical, path in copied.items():
        file_sources[logical] = source_metadata[logical]["source_ref"]
        hashes[logical] = sha256_file(path)
    manifest["gated_files_embedded"] = [TASK_LOGICAL_PATH]
    manifest["gated_source_embedded"] = True
    manifest["authorized_private_overlay"] = True
    manifest["contains_generated_run_output"] = False
    top_hashes = manifest.setdefault("top_level_file_sha256", {})
    if not isinstance(top_hashes, dict):
        raise AuthorizedPacketBuildError(f"invalid top-level hash map in {case_dir}")
    top_hashes["agent_input.json"] = sha256_file(case_dir / "agent_input.json")
    top_hashes["case_packet.json"] = sha256_file(packet_path)
    write_json(manifest_path, manifest)


def validate_private_root(root: Path, task_hashes: Mapping[str, str]) -> dict[str, int]:
    case_dirs = sorted(
        path for path in root.iterdir() if path.is_dir() and path.name.isdigit()
    )
    if len(case_dirs) != OSWORLD_2_EXPECTED_CASES:
        raise AuthorizedPacketBuildError(
            f"private root has {len(case_dirs)} cases, expected {OSWORLD_2_EXPECTED_CASES}"
        )
    sizes: list[int] = []
    support_counts: list[int] = []
    for case_dir in case_dirs:
        filename = f"task_{case_dir.name}.py"
        expected = normalize_hash(task_hashes.get(filename, ""))
        task_copy = case_dir / "raw_case" / TASK_LOGICAL_PATH
        if expected is None or not task_copy.is_file() or sha256_file(task_copy) != expected:
            raise AuthorizedPacketBuildError(
                f"private task source binding failed for {case_dir.name}"
            )
        try:
            task_tree = ast.parse(
                task_copy.read_text(encoding="utf-8"), filename=str(task_copy)
            )
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            raise AuthorizedPacketBuildError(
                f"private official source is not parseable for {case_dir.name}: {exc}"
            ) from exc
        official_classes = []
        for node in task_tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            base_names = {
                base.id if isinstance(base, ast.Name) else base.attr
                for base in node.bases
                if isinstance(base, (ast.Name, ast.Attribute))
            }
            if base_names & {"BaseTask", "MultiPhaseTask"}:
                official_classes.append(node)
        if len(official_classes) != 1 or not any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "evaluate"
            for node in official_classes[0].body
        ):
            raise AuthorizedPacketBuildError(
                f"exactly one official task class with evaluate() is required for {case_dir.name}"
            )
        packet = read_object(case_dir / "case_packet.json")
        if packet.get("formal_checklist_drafting_status") != PRIVATE_STATUS:
            raise AuthorizedPacketBuildError(
                f"private drafting status missing for {case_dir.name}"
            )
        overlay = packet.get("authorized_private_overlay")
        if not isinstance(overlay, dict) or overlay.get("publication_allowed") is not False:
            raise AuthorizedPacketBuildError(
                f"private publication boundary missing for {case_dir.name}"
            )
        markdown = (case_dir / "case_packet.md").read_text(encoding="utf-8")
        if (
            f"- `{TASK_LOGICAL_PATH}`" not in markdown
            or "contains no observed run output" not in markdown
            or task_copy.read_text(encoding="utf-8").rstrip() not in markdown
        ):
            raise AuthorizedPacketBuildError(
                f"authorized source is not fully rendered for {case_dir.name}"
            )
        sizes.append((case_dir / "case_packet.md").stat().st_size)
        source_files = overlay.get("source_files")
        if not isinstance(source_files, dict):
            raise AuthorizedPacketBuildError(
                f"private source inventory missing for {case_dir.name}"
            )
        support_counts.append(len(source_files) - 1)
        forbidden = [
            path
            for path in case_dir.rglob("*")
            if path.is_file() and path.name in FORBIDDEN_RUN_FILENAMES
        ]
        if forbidden:
            raise AuthorizedPacketBuildError(
                f"run output unexpectedly present in draft packet {case_dir.name}: {forbidden}"
            )
    return {
        "case_count": len(case_dirs),
        "min_case_packet_bytes": min(sizes),
        "max_case_packet_bytes": max(sizes),
        "total_case_packet_bytes": sum(sizes),
        "min_public_support_files": min(support_counts),
        "max_public_support_files": max(support_counts),
    }


def build(args: argparse.Namespace) -> None:
    public_root = args.public_packet_root.resolve()
    task_root = args.authorized_task_root.resolve()
    manifest_path = args.hash_manifest.resolve()
    code_root = args.official_code_root.resolve()
    output_root = args.output_root.resolve()
    if not public_root.is_dir() or not task_root.is_dir() or not manifest_path.is_file():
        raise AuthorizedPacketBuildError("one or more required input paths do not exist")
    require_git_commit(code_root)
    task_hashes = require_authorized_inputs(task_root, manifest_path)
    public_index = read_object(public_root / "index.json")
    if (
        public_index.get("case_count") != OSWORLD_2_EXPECTED_CASES
        or public_index.get("status") != "ready_controller_source_pointer_only"
    ):
        raise AuthorizedPacketBuildError(
            "public packet root is not the expected ready pointer-only 108-case build"
        )
    module_paths, definitions = public_source_catalog(code_root)

    output_root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".osworld2-authorized-draft-", dir=output_root.parent
    ) as temp_parent:
        temp_root = Path(temp_parent) / "osworld_2_0"
        shutil.copytree(public_root, temp_root)
        rows_by_id = {
            str(row["case_unit_id"]): dict(row)
            for row in public_index.get("cases", [])
            if isinstance(row, dict) and "case_unit_id" in row
        }
        if len(rows_by_id) != OSWORLD_2_EXPECTED_CASES:
            raise AuthorizedPacketBuildError("public index case rows are incomplete")

        for task_path in sorted(task_root.glob("task_*.py")):
            case_id = task_path.stem.removeprefix("task_").zfill(3)
            case_dir = temp_root / case_id
            if not case_dir.is_dir():
                raise AuthorizedPacketBuildError(f"public packet lacks case {case_id}")
            support_paths = public_support_sources(
                task_path, module_paths, definitions
            )
            section, logical_paths, source_metadata = render_authorized_sources(
                task_path=task_path,
                support_paths=support_paths,
                code_root=code_root,
            )
            copied = copy_authorized_sources(
                case_dir=case_dir,
                task_path=task_path,
                support_paths=support_paths,
                code_root=code_root,
            )
            update_case_metadata(
                case_dir=case_dir,
                copied=copied,
                source_metadata=source_metadata,
            )
            base_markdown = (case_dir / "case_packet.md").read_text(encoding="utf-8")
            (case_dir / "case_packet.md").write_text(
                private_markdown(
                    base_markdown=base_markdown,
                    source_section=section,
                    source_paths=logical_paths,
                ),
                encoding="utf-8",
            )
            # The manifest is written before the Markdown by design; refresh
            # its top-level hashes now that both controller inputs are final.
            manifest = read_object(case_dir / "raw_case_manifest.json")
            top_hashes = manifest.setdefault("top_level_file_sha256", {})
            assert isinstance(top_hashes, dict)
            for name in ("agent_input.json", "case_packet.json", "case_packet.md"):
                top_hashes[name] = sha256_file(case_dir / name)
            write_json(case_dir / "raw_case_manifest.json", manifest)

            row = rows_by_id[case_id]
            row["authorized_private_overlay"] = True
            row["source_sha256"] = sha256_file(task_path)
            row["case_packet_size_bytes"] = (case_dir / "case_packet.md").stat().st_size
            row["public_support_file_count"] = len(support_paths)
            row["files"] = {
                name: sha256_file(case_dir / name)
                for name in (
                    "agent_input.json",
                    "case_packet.json",
                    "case_packet.md",
                    "raw_case_manifest.json",
                )
            }

        validation = validate_private_root(temp_root, task_hashes)
        rows = [rows_by_id[key] for key in sorted(rows_by_id)]
        private_index = dict(public_index)
        private_index.update(
            {
                "schema_version": "osworld_2_0_authorized_draft_packet_index/v1",
                "status": PRIVATE_STATUS,
                "visibility": "private_authorized_controller_and_drafter_only",
                "cases": rows,
                "case_rows_sha256": sha256_bytes(canonical_bytes(rows)),
                "official_task_commit": OSWORLD_2_TASK_COMMIT,
                "official_code_commit": OSWORLD_2_CODE_COMMIT,
                "contains_generated_run_output": False,
                "validation": validation,
            }
        )
        write_json(temp_root / "index.json", private_index)
        generation_status = {
            "schema_version": "osworld_2_0_authorized_draft_generation_status/v1",
            "domain": "osworld_2_0",
            "benchmark": "OSWorld 2.0",
            "release": OSWORLD_2_RELEASE,
            "status": PRIVATE_STATUS,
            "visibility": "private_authorized_controller_and_drafter_only",
            "publication_allowed": False,
            "tested_agent_receives_only_agent_input_json": True,
            "drafter_receives_official_evaluator_source": True,
            "contains_generated_run_output": False,
            "hash_manifest_sha256": OSWORLD_2_TASK_HASH_MANIFEST_SHA256,
            "index_sha256": sha256_file(temp_root / "index.json"),
            "validation": validation,
        }
        write_json(temp_root / "generation_status.json", generation_status)
        notice = (
            "# Private authorized OSWorld 2.0 draft packets\n\n"
            "This directory contains official gated task/evaluator source obtained "
            "through the authenticated Hugging Face gate. It exists only so the "
            "controller-side checklist drafter can read the benchmark claim and native "
            "scoring contract. It contains no run outputs. Do not commit, publish, or "
            "show it to a tested agent.\n"
        )
        (temp_root / "AUTHORIZED_PRIVATE_NOTICE.md").write_text(notice, encoding="utf-8")
        # Revalidate after root metadata is finalized; this also proves no run
        # artifact appeared during index construction.
        validate_private_root(temp_root, task_hashes)
        generated_hash = tree_sha256(temp_root)

        if output_root.exists():
            if not args.replace:
                raise AuthorizedPacketBuildError(
                    f"refusing to replace existing private root {output_root}; use --replace"
                )
            shutil.rmtree(output_root)
        shutil.move(str(temp_root), str(output_root))

    print(
        pretty_json(
            {
                "status": PRIVATE_STATUS,
                "output_root": str(output_root),
                "tree_sha256": generated_hash,
                **validation,
            }
        ).rstrip()
    )


def main() -> int:
    args = parse_args()
    try:
        build(args)
    except (AuthorizedPacketBuildError, OSError) as exc:
        print(f"error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
