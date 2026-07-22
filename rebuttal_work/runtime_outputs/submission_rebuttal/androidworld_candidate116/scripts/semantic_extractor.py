#!/usr/bin/env python3
"""Deterministic canonical-semantic extraction for AndroidWorld candidate-116.

The public :func:`extract_canonical_semantic_records` interface is intentionally
side-effect free.  It launches this file as an isolated worker under the
AndroidWorld virtualenv, imports ``android_world`` only from the frozen shared
source tree, and returns JSON-safe data without writing any artifact.

The extractor keeps raw ``task_metadata.json`` text as descriptive metadata,
while treating the runtime goal implementation and native evaluator source as
canonical.  In particular, dynamically generated information-retrieval tasks
are attributed to their textproto definition and registry factory, never to
the incidental runtime module ``abc``.
"""

from __future__ import annotations

import argparse
import ast
import base64
import dataclasses
import datetime as datetime_lib
import enum
import hashlib
import inspect
import json
import os
import random
import re
import string
import subprocess
import sys
import tempfile
import textwrap
import types
import uuid
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = "androidworld_canonical_semantic_bundle/v1"
RECORD_SCHEMA_VERSION = "androidworld_canonical_semantic_record/v1"
DEFAULT_SAMPLE_SEEDS = (0, 1, 2, 3, 4, 5, 7, 11)
EXPECTED_MECHANISM_COUNTS = {
    "format_template": 57,
    "computed_goal": 33,
    "branch_template": 1,
    "ir_proto_prompt": 25,
}
FIXED_WALL_CLOCK = datetime_lib.datetime(2023, 10, 15, 12, 0, 0)

# These are source-reviewed, material metadata/runtime-goal disagreements in
# the pinned 116-task source snapshot.  Everything else that differs remains
# visible in metadata_comparison and is conservatively labelled unresolved or
# non-material rather than silently accepted.
KNOWN_MATERIAL_METADATA_CONFLICTS: dict[str, tuple[str, str]] = {
    "MarkorAddNoteHeader": (
        "missing_required_subgoal",
        "metadata omits the required rename and names a non-runtime file_name placeholder",
    ),
    "MarkorChangeNoteContent": (
        "missing_required_subgoal",
        "metadata omits the required rename and does not identify original_name/new_name",
    ),
    "MarkorEditNote": (
        "missing_reachable_variants",
        "metadata describes only header while runtime also reaches footer and replace",
    ),
    "OsmAndTrack": (
        "fixed_example_replaces_parameterized_goal",
        "metadata fixes two waypoints while the runtime goal uses generated two-to-four waypoints",
    ),
    "VlcCreateTwoPlaylists": (
        "parameter_binding_and_location_mismatch",
        "metadata reuses files1 for playlist two and swaps the runtime location wording",
    ),
    "SportsTrackerTotalDistanceForCategoryOverInterval": (
        "answer_rounding_mismatch",
        "runtime prompt requires rounding meters to the nearest integer",
    ),
    "SportsTrackerTotalDurationForCategoryThisWeek": (
        "time_boundary_omission",
        "runtime prompt specifies Monday as the first day of the week",
    ),
    "SimpleCalendarEventsInNextWeek": (
        "time_boundary_omission",
        "runtime prompt specifies Monday as the first day of the week",
    ),
    "SportsTrackerActivitiesCountForWeek": (
        "time_boundary_omission",
        "runtime prompt specifies Monday as the first day of the week",
    ),
    "SportsTrackerActivitiesOnDate": (
        "answer_field_terminology_mismatch",
        "metadata requests category while runtime prompt requests activity type",
    ),
    "TasksDueNextWeek": (
        "time_boundary_omission",
        "runtime prompt specifies Monday as the first day of the week",
    ),
    "SportsTrackerLongestDistanceActivity": (
        "time_boundary_and_rounding_omission",
        "runtime prompt specifies Monday week boundaries and nearest-integer rounding",
    ),
    "NotesRecipeIngredientCount": (
        "answer_format_conflict",
        "metadata says no abbreviations while runtime requires exact amount/unit formatting from the recipe",
    ),
}

KNOWN_NON_MATERIAL_METADATA_CONFLICTS: dict[str, tuple[str, str]] = {
    "ExpenseDeleteDuplicates": (
        "app_display_name_alias",
        "metadata says 'arduia pro expense' while the runtime goal uses the shorter installed-app label 'pro expense'; the duplicate-deletion requirement is unchanged",
    ),
    "ExpenseAddSingle": (
        "app_display_name_alias_and_runtime_rendering",
        "metadata uses the older 'arduia pro expense' label and a generic expense placeholder; runtime uses 'pro expense' and renders the generated row fields without changing the required transaction",
    ),
    "ExpenseDeleteMultiple": (
        "app_display_name_alias_and_runtime_rendering",
        "metadata uses the older 'arduia pro expense' label and an expenses placeholder; runtime uses 'pro expense' and renders the same selected expense names",
    ),
    "ExpenseAddMultiple": (
        "app_display_name_alias_and_runtime_rendering",
        "metadata uses the older 'arduia pro expense' label and an expenses placeholder; runtime uses 'pro expense' and renders the generated transaction rows without changing their required values",
    ),
    "ExpenseDeleteSingle": (
        "app_display_name_alias_and_runtime_rendering",
        "metadata uses the older 'arduia pro expense' label and a singular placeholder; runtime uses 'pro expense' and renders the same selected expense name",
    ),
    "ExpenseDeleteMultiple2": (
        "app_display_name_alias_and_runtime_rendering",
        "metadata uses the older 'arduia pro expense' label and an expenses placeholder; runtime uses 'pro expense' and renders the same selected expense names",
    ),
    "ExpenseAddMultipleFromMarkor": (
        "app_display_name_alias",
        "metadata says 'arduia pro expense' while the runtime goal uses the shorter installed-app label 'pro expense'; the reimbursable-transaction requirement is unchanged",
    ),
    "ExpenseDeleteDuplicates2": (
        "app_display_name_alias",
        "metadata says 'arduia pro expense' while the runtime goal uses the shorter installed-app label 'pro expense'; the duplicate-deletion requirement is unchanged",
    ),
    "SaveCopyOfReceiptTaskEval": (
        "runtime_app_name_clarification",
        "runtime prepends 'In Simple Gallery Pro' to the same DCIM-to-Download copy task described by metadata; this clarifies the target app without changing the required state",
    ),
    "MarkorTranscribeVideo": (
        "grammar_only",
        "metadata says 'should contains'; runtime template corrects this to 'should contain'",
    ),
}


class SemanticExtractionError(RuntimeError):
    """Raised when strict semantic extraction cannot close its invariants."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _object_sha256(value: Any) -> str:
    return _sha256_bytes(_canonical_json_bytes(value))


def _json_safe(value: Any) -> Any:
    """Converts known AndroidWorld parameter objects to stable JSON values."""

    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise SemanticExtractionError(f"non-finite float is not canonical JSON: {value!r}")
        return value
    if isinstance(value, enum.Enum):
        return {
            "$type": f"{value.__class__.__module__}.{value.__class__.__qualname__}",
            "$enum": value.name,
            "value": _json_safe(value.value),
        }
    if isinstance(value, (datetime_lib.datetime, datetime_lib.date, datetime_lib.time)):
        return {
            "$type": f"{value.__class__.__module__}.{value.__class__.__qualname__}",
            "$iso8601": value.isoformat(),
        }
    if isinstance(value, datetime_lib.timedelta):
        return {"$type": "datetime.timedelta", "total_seconds": value.total_seconds()}
    if isinstance(value, Path):
        return {"$type": "pathlib.Path", "value": value.as_posix()}
    if isinstance(value, bytes):
        return {"$type": "bytes", "base64": base64.b64encode(value).decode("ascii")}
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            "$type": f"{value.__class__.__module__}.{value.__class__.__qualname__}",
            "fields": {
                field.name: _json_safe(getattr(value, field.name))
                for field in dataclasses.fields(value)
            },
        }
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (set, frozenset)):
        converted = [_json_safe(item) for item in value]
        return sorted(converted, key=lambda item: _canonical_json_bytes(item))

    # NumPy is intentionally not imported by the parent process.  Array/scalar
    # support is detected structurally inside the venv worker.
    if value.__class__.__module__.startswith("numpy"):
        if hasattr(value, "tolist"):
            return _json_safe(value.tolist())
        if hasattr(value, "item"):
            return _json_safe(value.item())

    if value.__class__.__module__.startswith("PIL.") and hasattr(value, "tobytes"):
        pixels = value.tobytes()
        return {
            "$type": f"{value.__class__.__module__}.{value.__class__.__qualname__}",
            "mode": getattr(value, "mode", None),
            "size": _json_safe(getattr(value, "size", None)),
            "pixel_bytes_sha256": _sha256_bytes(pixels),
            "pixel_byte_count": len(pixels),
        }

    # Protobuf values expose deterministic serialization.  MessageToDict is
    # imported lazily so the public parent interface has no protobuf dependency.
    if hasattr(value, "DESCRIPTOR") and hasattr(value, "SerializeToString"):
        from google.protobuf import json_format  # type: ignore

        return {
            "$type": value.DESCRIPTOR.full_name,
            "$protobuf": json_format.MessageToDict(
                value,
                preserving_proto_field_name=True,
                use_integers_for_enums=False,
            ),
            "$protobuf_sha256": _sha256_bytes(value.SerializeToString(deterministic=True)),
        }

    if hasattr(value, "_asdict"):
        return {
            "$type": f"{value.__class__.__module__}.{value.__class__.__qualname__}",
            "fields": _json_safe(value._asdict()),
        }
    if hasattr(value, "__dict__"):
        return {
            "$type": f"{value.__class__.__module__}.{value.__class__.__qualname__}",
            "attributes": _json_safe(vars(value)),
        }
    raise SemanticExtractionError(
        "unsupported non-deterministic parameter value: "
        f"{value.__class__.__module__}.{value.__class__.__qualname__}"
    )


def _relative_source_path(path: Path, source_root: Path) -> str:
    try:
        return path.resolve().relative_to(source_root.resolve()).as_posix()
    except ValueError as exc:
        raise SemanticExtractionError(f"AndroidWorld source escaped frozen tree: {path}") from exc


def _unwrap_source_object(value: Any) -> Any:
    if isinstance(value, property):
        return value.fget
    if isinstance(value, (classmethod, staticmethod)):
        return value.__func__
    if inspect.ismethod(value):
        return value.__func__
    return value


def _source_ref(value: Any, source_root: Path, *, symbol: str | None = None) -> dict[str, Any]:
    target = _unwrap_source_object(value)
    if target is None:
        raise SemanticExtractionError(f"cannot resolve source for {symbol or value!r}")
    source_file = inspect.getsourcefile(target) or inspect.getfile(target)
    path = Path(source_file).resolve()
    relative = _relative_source_path(path, source_root)
    lines, start_line = inspect.getsourcelines(target)
    snippet = "".join(lines)
    try:
        parsed = ast.parse(textwrap.dedent(snippet))
        ast_hash = _sha256_bytes(ast.dump(parsed, annotate_fields=True, include_attributes=False).encode("utf-8"))
    except SyntaxError:
        ast_hash = None
    return {
        "path": relative,
        "symbol": symbol or getattr(target, "__qualname__", getattr(target, "__name__", None)),
        "start_line": start_line,
        "end_line": start_line + len(lines) - 1,
        "file_sha256": _sha256_file(path),
        "snippet_sha256": _sha256_bytes(snippet.encode("utf-8")),
        "ast_sha256": ast_hash,
    }


def _owner(cls: type[Any], attribute: str) -> type[Any]:
    for base in cls.__mro__:
        if attribute in base.__dict__:
            return base
    raise SemanticExtractionError(f"{cls.__name__} has no MRO owner for {attribute}")


def _member_ref(cls: type[Any], attribute: str, source_root: Path) -> dict[str, Any]:
    owner = _owner(cls, attribute)
    descriptor = owner.__dict__[attribute]
    if isinstance(descriptor, (property, classmethod, staticmethod)) or inspect.isroutine(descriptor):
        ref = _source_ref(descriptor, source_root, symbol=f"{owner.__qualname__}.{attribute}")
    else:
        # Class constants such as ``template`` and ``schema`` do not have an
        # inspectable source object of their own.  The frozen owning class span
        # is the narrowest reliable source reference.
        ref = _source_ref(owner, source_root, symbol=f"{owner.__qualname__}.{attribute}")
    ref["owner_module"] = owner.__module__
    ref["owner_class"] = owner.__qualname__
    return ref


def _method_chain(cls: type[Any], attribute: str, source_root: Path) -> list[dict[str, Any]]:
    chain: list[dict[str, Any]] = []
    for base in cls.__mro__:
        if attribute not in base.__dict__:
            continue
        if not base.__module__.startswith("android_world"):
            continue
        descriptor = base.__dict__[attribute]
        ref = _source_ref(descriptor, source_root, symbol=f"{base.__qualname__}.{attribute}")
        semantics = _source_semantics(descriptor)
        chain.append(
            {
                "owner_module": base.__module__,
                "owner_class": base.__qualname__,
                "source_ref": ref,
                **semantics,
            }
        )
    if not chain:
        raise SemanticExtractionError(f"no frozen AndroidWorld {attribute} chain for {cls.__name__}")
    return chain


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Call):
        return _call_name(node.func)
    return None


def _slice_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _source_semantics(value: Any) -> dict[str, Any]:
    target = _unwrap_source_object(value)
    if target is None:
        return {"direct_parameter_reads": [], "direct_calls": [], "branch_node_count": 0}
    try:
        snippet = textwrap.dedent(inspect.getsource(target))
        tree = ast.parse(snippet)
    except (OSError, TypeError, SyntaxError):
        return {"direct_parameter_reads": [], "direct_calls": [], "branch_node_count": 0}

    param_reads: set[str] = set()
    calls: set[str] = set()
    branches = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.IfExp, ast.Match)):
            branches += 1
        if isinstance(node, ast.Subscript):
            value_name = _call_name(node.value)
            if value_name in {"self.params", "self._params"}:
                key = _slice_string(node.slice)
                if key:
                    param_reads.add(key)
        if isinstance(node, ast.Call):
            call = _call_name(node.func)
            if call:
                calls.add(call)
            if call in {"self.params.get", "self._params.get"} and node.args:
                key = _slice_string(node.args[0])
                if key:
                    param_reads.add(key)
    return {
        "direct_parameter_reads": sorted(param_reads),
        "direct_calls": sorted(calls),
        "branch_node_count": branches,
    }


def _template_fields(template: str) -> list[str]:
    fields: set[str] = set()
    for _, field, _, _ in string.Formatter().parse(template):
        if field:
            fields.add(field.split(".", 1)[0].split("[", 1)[0])
    return sorted(fields)


def _metadata_ref(metadata_path: Path, index: int, item: Mapping[str, Any], source_root: Path) -> dict[str, Any]:
    text = metadata_path.read_text(encoding="utf-8")
    needle = f'"task_name": "{item["task_name"]}"'
    offset = text.find(needle)
    line = text.count("\n", 0, offset) + 1 if offset >= 0 else None
    return {
        "path": _relative_source_path(metadata_path, source_root),
        "json_pointer": f"/{index}",
        "line_hint": line,
        "file_sha256": _sha256_file(metadata_path),
        "value_sha256": _object_sha256(_json_safe(dict(item))),
    }


def _brace_delta_without_strings(line: str) -> int:
    delta = 0
    quoted = False
    escaped = False
    for character in line:
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
            continue
        if character == "#":
            break
        if character == '"':
            quoted = True
        elif character == "{":
            delta += 1
        elif character == "}":
            delta -= 1
    return delta


def _textproto_task_ref(source_root: Path, task_name: str) -> dict[str, Any]:
    path = source_root / "android_world/task_evals/information_retrieval/proto/tasks.textproto"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    blocks: list[tuple[int, int, str]] = []
    index = 0
    while index < len(lines):
        if not re.match(r"^\s*tasks\s*\{", lines[index]):
            index += 1
            continue
        start = index
        depth = 0
        while index < len(lines):
            depth += _brace_delta_without_strings(lines[index])
            index += 1
            if depth == 0:
                break
        block = "".join(lines[start:index])
        blocks.append((start + 1, index, block))
    name_pattern = re.compile(rf'^\s*name:\s*"{re.escape(task_name)}"\s*$', re.MULTILINE)
    matches = [row for row in blocks if name_pattern.search(row[2])]
    if len(matches) != 1:
        raise SemanticExtractionError(
            f"expected one tasks.textproto block for {task_name}, found {len(matches)}"
        )
    start_line, end_line, snippet = matches[0]
    return {
        "path": _relative_source_path(path, source_root),
        "selector": f'tasks[name="{task_name}"]',
        "start_line": start_line,
        "end_line": end_line,
        "file_sha256": _sha256_file(path),
        "snippet_sha256": _sha256_bytes(snippet.encode("utf-8")),
    }


def _verify_snapshot(source_root: Path) -> dict[str, Any]:
    manifest_path = source_root.parent / "androidworld_source_snapshot_manifest.json"
    if not manifest_path.is_file():
        raise SemanticExtractionError(f"shared-source manifest is missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = manifest.get("files")
    if not isinstance(rows, list) or int(manifest.get("file_count", -1)) != len(rows):
        raise SemanticExtractionError("shared-source manifest inventory is malformed")
    expected_paths: list[str] = []
    for row in rows:
        relative = str(row["path"])
        path = source_root / relative
        expected_paths.append(relative)
        if not path.is_file() or _sha256_file(path) != row.get("sha256"):
            raise SemanticExtractionError(f"shared-source hash mismatch: {relative}")
    actual_paths = sorted(
        path.relative_to(source_root).as_posix()
        for path in source_root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )
    if sorted(expected_paths) != actual_paths:
        raise SemanticExtractionError("shared-source file set differs from its frozen manifest")
    return {
        "schema_version": manifest.get("schema_version"),
        "source_commit": manifest.get("source_commit"),
        "tree_sha256": manifest.get("tree_sha256"),
        "file_count": len(rows),
        "manifest_sha256": _sha256_file(manifest_path),
        "source_root_role": "shared_source/source_tree",
    }


class _FrozenDateTime(datetime_lib.datetime):
    @classmethod
    def now(cls, tz: datetime_lib.tzinfo | None = None) -> "_FrozenDateTime":
        value = FIXED_WALL_CLOCK
        if tz is not None:
            value = value.replace(tzinfo=datetime_lib.timezone.utc).astimezone(tz)
        return cls.fromtimestamp(value.timestamp(), tz=value.tzinfo)

    @classmethod
    def today(cls) -> "_FrozenDateTime":
        return cls.fromtimestamp(FIXED_WALL_CLOCK.timestamp())


def _install_frozen_time_for_markor() -> None:
    from android_world.task_evals.single import markor

    markor.datetime = types.SimpleNamespace(  # type: ignore[assignment]
        datetime=_FrozenDateTime,
        timedelta=datetime_lib.timedelta,
        date=datetime_lib.date,
        time=datetime_lib.time,
    )


def _generate_params(task_cls: type[Any], seed: int) -> dict[str, Any]:
    random.seed(seed)
    try:
        import numpy as np  # type: ignore

        np.random.seed(seed)
    except ImportError:
        pass

    original_uuid4 = uuid.uuid4
    counter = 0

    def deterministic_uuid4() -> uuid.UUID:
        nonlocal counter
        value = uuid.uuid5(uuid.NAMESPACE_URL, f"androidworld-semantic:{seed}:{counter}")
        counter += 1
        return value

    uuid.uuid4 = deterministic_uuid4  # type: ignore[assignment]
    try:
        params = dict(task_cls.generate_random_params())
    finally:
        uuid.uuid4 = original_uuid4  # type: ignore[assignment]
    # This mirrors suite_utils._instantiate_task.
    params["seed"] = seed
    return params


def _realize_goal_sample(
    task_cls: type[Any],
    seed: int,
    *,
    is_ir: bool,
    sample_kind: str = "fixed_seed",
) -> tuple[dict[str, Any], Any]:
    params = _generate_params(task_cls, seed)
    task = task_cls(params)
    before_params = _json_safe(dict(task.params))
    construction_goal = str(task.goal)

    transforms: list[str] = []
    if is_ir:
        # These are the pure semantic mutations performed by
        # InformationRetrieval.initialize_task after the base device setup and
        # before the goal is dispatched to the agent.
        from android_world.task_evals.information_retrieval import information_retrieval
        from android_world.task_evals.information_retrieval import proto_utils

        proto_utils.initialize_proto(task.task, task.params)
        information_retrieval._maybe_replace_date(task.params)  # pylint: disable=protected-access
        transforms = [
            "proto_utils.initialize_proto(task.task, task.params)",
            "information_retrieval._maybe_replace_date(task.params)",
        ]
    dispatch_goal = str(task.goal)
    repeated_goal = str(task.goal)
    if dispatch_goal != repeated_goal:
        raise SemanticExtractionError(f"non-repeatable goal property for {task_cls.__name__}, seed {seed}")
    after_params = _json_safe(dict(task.params))
    sample = {
        "sample_kind": sample_kind,
        "suite_seed": seed,
        "params_before_goal": before_params,
        "params_at_dispatch_model": after_params,
        "construction_goal": construction_goal,
        "dispatch_goal_model": dispatch_goal,
        "dispatch_goal_sha256": _sha256_bytes(dispatch_goal.encode("utf-8")),
        "pure_pre_dispatch_transforms": transforms,
        "device_initialization_executed": False,
        "reproducible_from_frozen_source_and_seed": True,
    }
    return sample, task


def _branch_samples(task_cls: type[Any], is_ir: bool) -> list[tuple[dict[str, Any], Any]]:
    if task_cls.__name__ != "MarkorEditNote":
        return []
    found: dict[str, tuple[dict[str, Any], Any]] = {}
    for seed in range(256):
        sample, task = _realize_goal_sample(
            task_cls,
            seed,
            is_ir=is_ir,
            sample_kind="branch_coverage",
        )
        branch = str(task.params.get("edit_type"))
        if branch not in found:
            sample["branch_selector"] = {"edit_type": branch}
            found[branch] = (sample, task)
        if set(found) == {"header", "footer", "replace"}:
            break
    if set(found) != {"header", "footer", "replace"}:
        raise SemanticExtractionError(f"MarkorEditNote branch coverage incomplete: {sorted(found)}")
    return [found[name] for name in ("header", "footer", "replace")]


def _normalize_text(value: str) -> str:
    return " ".join(value.split()).strip()


def _metadata_shape_pattern(template: str) -> re.Pattern[str]:
    pieces: list[str] = []
    for literal, field, _, _ in string.Formatter().parse(template):
        pieces.append(re.escape(_normalize_text(literal)))
        if field:
            pieces.append(r".+?")
    return re.compile(r"^" + "".join(pieces) + r"$", re.DOTALL)


def _metadata_comparison(
    task_id: str,
    metadata_template: str,
    mechanism: str,
    canonical_templates: Sequence[str],
    samples: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    normalized_metadata = _normalize_text(metadata_template)
    normalized_templates = [_normalize_text(value) for value in canonical_templates]
    sample_goals = [str(sample["dispatch_goal_model"]) for sample in samples]
    pattern = _metadata_shape_pattern(metadata_template)
    sample_shape_matches = [bool(pattern.fullmatch(_normalize_text(goal))) for goal in sample_goals]

    if canonical_templates and all(metadata_template == value for value in canonical_templates):
        status = "exact"
    elif canonical_templates and all(normalized_metadata == value for value in normalized_templates):
        status = "whitespace_normalized_equal"
    elif mechanism == "branch_template" and normalized_metadata in normalized_templates:
        status = "partial_variant_coverage"
    elif sample_shape_matches and all(sample_shape_matches):
        status = "fixed_seed_goal_shape_match"
    else:
        status = "mismatch"

    comparison = {
        "status": status,
        "metadata_template": metadata_template,
        "metadata_placeholders": _template_fields(metadata_template),
        "canonical_templates": list(canonical_templates),
        "fixed_seed_sample_shape_matches": sample_shape_matches,
        "comparison_is_semantic_proof": status in {"exact", "whitespace_normalized_equal"},
    }
    conflicts: list[dict[str, Any]] = []
    if task_id in KNOWN_MATERIAL_METADATA_CONFLICTS:
        conflict_type, reason = KNOWN_MATERIAL_METADATA_CONFLICTS[task_id]
        conflicts.append(
            {
                "scope": "metadata_vs_runtime_goal",
                "conflict_type": conflict_type,
                "materiality": "material",
                "status": "open",
                "reason": reason,
                "resolution_rule": "runtime_goal_and_evaluator_sources_are_canonical",
            }
        )
    elif task_id in KNOWN_NON_MATERIAL_METADATA_CONFLICTS:
        conflict_type, reason = KNOWN_NON_MATERIAL_METADATA_CONFLICTS[task_id]
        conflicts.append(
            {
                "scope": "metadata_vs_runtime_goal",
                "conflict_type": conflict_type,
                "materiality": "non_material",
                "status": "resolved",
                "reason": reason,
                "resolution_rule": "runtime_goal_text_is_canonical",
            }
        )
    elif status not in {"exact", "whitespace_normalized_equal", "fixed_seed_goal_shape_match"}:
        conflicts.append(
            {
                "scope": "metadata_vs_runtime_goal",
                "conflict_type": "unclassified_text_or_binding_difference",
                "materiality": "unresolved",
                "status": "open",
                "reason": "metadata differs from the canonical runtime goal representation",
                "resolution_rule": "manual semantic review required; runtime source remains canonical",
            }
        )
    return comparison, conflicts


def _mro_identity(cls: type[Any], source_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for base in cls.__mro__:
        row: dict[str, Any] = {
            "module": base.__module__,
            "qualname": base.__qualname__,
            "canonical_androidworld_source": base.__module__.startswith("android_world"),
        }
        if row["canonical_androidworld_source"]:
            try:
                row["source_ref"] = _source_ref(base, source_root, symbol=base.__qualname__)
            except (OSError, TypeError, SemanticExtractionError):
                # Only the generated IR subclass itself lacks a class source.
                row["source_ref"] = None
        else:
            row["source_ref"] = None
        rows.append(row)
    return rows


def _schema_contract(task_cls: type[Any], representative: Any, source_root: Path) -> dict[str, Any]:
    owner = _owner(task_cls, "schema")
    declared = representative.schema
    return {
        "declared_schema": _json_safe(declared),
        "schema_completeness": "empty" if not declared else "declared_not_assumed_complete",
        "source_ref": _source_ref(owner, source_root, symbol=f"{owner.__qualname__}.schema"),
    }


def _ir_contract(task_cls: type[Any], representative: Any, source_root: Path) -> dict[str, Any]:
    from android_world.task_evals.information_retrieval import information_retrieval
    from android_world.task_evals.information_retrieval import information_retrieval_registry
    from google.protobuf import json_format  # type: ignore

    proto = representative.task_template
    return {
        "prompt": proto.prompt,
        "task_params": [
            json_format.MessageToDict(
                value,
                preserving_proto_field_name=True,
                use_integers_for_enums=False,
            )
            for value in proto.task_params
        ],
        "success_criteria": json_format.MessageToDict(
            proto.success_criteria,
            preserving_proto_field_name=True,
            use_integers_for_enums=False,
        ),
        "relevant_state": json_format.MessageToDict(
            proto.relevant_state,
            preserving_proto_field_name=True,
            use_integers_for_enums=False,
        ),
        "task_proto_sha256": _sha256_bytes(proto.SerializeToString(deterministic=True)),
        "task_proto_source_ref": _textproto_task_ref(source_root, task_cls.__name__),
        "dynamic_property_ref": _member_ref(task_cls, "task_template", source_root),
        "factory_ref": _source_ref(
            information_retrieval_registry.InformationRetrievalRegistry._build_task_class,
            source_root,
            symbol="InformationRetrievalRegistry._build_task_class",
        ),
        "base_class_ref": _source_ref(
            information_retrieval.InformationRetrieval,
            source_root,
            symbol="InformationRetrieval",
        ),
        "runtime_module_abc_is_not_definition_provenance": task_cls.__module__ == "abc",
    }


def _extract_record(
    task_id: str,
    task_cls: type[Any],
    metadata: Mapping[str, Any],
    metadata_index: int,
    metadata_path: Path,
    source_root: Path,
    sample_seeds: Sequence[int],
    *,
    task_eval_cls: type[Any],
    information_retrieval_cls: type[Any],
    registry_ref: Mapping[str, Any],
) -> dict[str, Any]:
    is_ir = issubclass(task_cls, information_retrieval_cls)
    goal_owner = _owner(task_cls, "goal")
    template_owner = _owner(task_cls, "template")
    template_descriptor = template_owner.__dict__["template"]
    if is_ir:
        mechanism = "ir_proto_prompt"
    elif goal_owner is not task_eval_cls:
        mechanism = "computed_goal"
    elif isinstance(template_descriptor, property):
        mechanism = "branch_template"
    else:
        mechanism = "format_template"

    realized: list[tuple[dict[str, Any], Any]] = [
        _realize_goal_sample(task_cls, seed, is_ir=is_ir) for seed in sample_seeds
    ]
    realized.extend(_branch_samples(task_cls, is_ir))
    samples = [row[0] for row in realized]
    representative = realized[0][1]

    canonical_templates: list[str] = []
    goal_contract: dict[str, Any] = {
        "authority": "runtime_goal_dispatched_by_android_world.suite_utils",
        "dispatch_phase": "after_initialize_task",
        "representation_kind": mechanism,
        "effective_goal_ref": _member_ref(task_cls, "goal", source_root),
        "runtime_samples": samples,
        "sample_count": len(samples),
        "samples_are_examples_not_generic_templates": True,
    }
    if mechanism == "format_template":
        template = str(representative.template)
        canonical_templates = [template]
        goal_contract.update(
            {
                "effective_template_ref": _member_ref(task_cls, "template", source_root),
                "templates": [{"variant_id": "default", "template": template, "placeholders": _template_fields(template)}],
            }
        )
    elif mechanism == "branch_template":
        branch_templates: list[dict[str, Any]] = []
        for sample, task in _branch_samples(task_cls, is_ir):
            branch = str(task.params["edit_type"])
            template = str(task.template)
            canonical_templates.append(template)
            branch_templates.append(
                {
                    "variant_id": branch,
                    "when": {"edit_type": branch},
                    "template": template,
                    "placeholders": _template_fields(template),
                    "sample_seed": sample["suite_seed"],
                }
            )
        goal_contract.update(
            {
                "effective_template_ref": _member_ref(task_cls, "template", source_root),
                "templates": branch_templates,
                "branch_coverage": {
                    "expected": ["header", "footer", "replace"],
                    "covered": [row["variant_id"] for row in branch_templates],
                    "complete": len(branch_templates) == 3,
                },
            }
        )
    elif mechanism == "computed_goal":
        descriptor = goal_owner.__dict__["goal"]
        goal_contract["computed_goal_semantics"] = _source_semantics(descriptor)
        goal_contract["templates"] = []
    else:
        ir = _ir_contract(task_cls, representative, source_root)
        canonical_templates = [ir["prompt"]]
        goal_contract["templates"] = [
            {
                "variant_id": "textproto_prompt",
                "template": ir["prompt"],
                "placeholders": _template_fields(ir["prompt"]),
            }
        ]
        goal_contract["ir_proto"] = ir

    metadata_template = str(metadata.get("task_template") or "")
    metadata_comparison, conflicts = _metadata_comparison(
        task_id,
        metadata_template,
        mechanism,
        canonical_templates,
        samples,
    )

    parameter_keys = sorted(
        {
            key
            for sample in samples
            for key in sample["params_at_dispatch_model"].keys()
        }
    )
    parameter_type_observations: dict[str, list[str]] = {}
    for key in parameter_keys:
        observed: set[str] = set()
        for _, task in realized:
            if key in task.params:
                value = task.params[key]
                observed.add(f"{value.__class__.__module__}.{value.__class__.__qualname__}")
        parameter_type_observations[key] = sorted(observed)

    initialize_chain = _method_chain(task_cls, "initialize_task", source_root)
    evaluator_chain = _method_chain(task_cls, "is_successful", source_root)
    generator_ref = _member_ref(task_cls, "generate_random_params", source_root)
    schema = _schema_contract(task_cls, representative, source_root)

    definition: dict[str, Any] = {
        "definition_kind": "dynamic_ir_proto" if is_ir else "python_class",
        "registration_ref": dict(registry_ref),
        "runtime_class_module": task_cls.__module__,
        "runtime_class_qualname": task_cls.__qualname__,
        "mro": _mro_identity(task_cls, source_root),
    }
    if is_ir:
        definition.update(
            {
                "class_ref": None,
                "canonical_definition_refs": [
                    goal_contract["ir_proto"]["task_proto_source_ref"],
                    goal_contract["ir_proto"]["factory_ref"],
                    goal_contract["ir_proto"]["base_class_ref"],
                ],
                "incidental_runtime_module_excluded": "abc" if task_cls.__module__ == "abc" else None,
            }
        )
    else:
        class_ref = _source_ref(task_cls, source_root, symbol=task_cls.__qualname__)
        definition.update({"class_ref": class_ref, "canonical_definition_refs": [class_ref]})

    raw_metadata = {
        "semantic_role": "descriptive_non_authoritative",
        "value": _json_safe(dict(metadata)),
        "source_ref": _metadata_ref(metadata_path, metadata_index, metadata, source_root),
        "template_placeholders": _template_fields(metadata_template),
    }
    open_material = any(
        row["status"] == "open" and row["materiality"] == "material" for row in conflicts
    )
    open_unresolved = any(
        row["status"] == "open" and row["materiality"] == "unresolved" for row in conflicts
    )
    record: dict[str, Any] = {
        "schema_version": RECORD_SCHEMA_VERSION,
        "identity": {
            "task_id": task_id,
            "case_unit_id": task_id,
            "registry_family": "android_world",
            "registry_key": task_id,
            "runtime_class_name": task_cls.__name__,
        },
        "definition": definition,
        "raw_metadata": raw_metadata,
        "parameters": {
            **schema,
            "generator_ref": generator_ref,
            "runner_injected_parameters": ["seed"],
            "observed_parameter_keys": parameter_keys,
            "observed_parameter_types": parameter_type_observations,
            "observation_seed_set": list(sample_seeds),
            "observations_are_not_a_proof_of_parameter_domain": True,
        },
        "goal": goal_contract,
        "initialization": {
            "effective_entrypoint_ref": initialize_chain[0]["source_ref"],
            "mro_source_chain": initialize_chain,
            "device_execution_performed_during_extraction": False,
        },
        "evaluator": {
            "effective_entrypoint_ref": evaluator_chain[0]["source_ref"],
            "mro_source_chain": evaluator_chain,
            "runner_semantics": {
                "task_raw_score": "task.is_successful(env)",
                "done_gate": "task_successful if interaction_results.done else 0.0",
                "display_success_threshold": "agent_successful > 0.5",
                "source_ref": _suite_runner_ref(source_root),
            },
            "live_evaluator_execution_performed": False,
        },
        "metadata_comparison": metadata_comparison,
        "conflicts": conflicts,
        "readiness": {
            "canonical_source_complete": True,
            "goal_samples_reproducible": True,
            "static_semantic_record_complete": True,
            "canonical_runtime_resolution_applied": True,
            "metadata_is_excluded_from_canonical_goal_when_conflicting": True,
            "metadata_has_open_material_conflict": open_material,
            "metadata_has_open_unresolved_conflict": open_unresolved,
            "static_draft_ready": True,
            "draft_blockers": [],
            "live_runtime_verified": False,
            "live_run_ready": False,
            "live_run_blockers": ["device/emulator execution is outside this static extractor"],
        },
    }
    record["record_sha256"] = _object_sha256(record)
    return record


def _suite_runner_ref(source_root: Path) -> dict[str, Any]:
    from android_world import suite_utils

    return _source_ref(suite_utils._run_task, source_root, symbol="suite_utils._run_task")  # pylint: disable=protected-access


def _validate_loaded_androidworld_modules(source_root: Path) -> list[str]:
    loaded: list[str] = []
    for module_name, module in sorted(sys.modules.items()):
        if not module_name.startswith("android_world"):
            continue
        module_file = getattr(module, "__file__", None)
        if module_file is None:
            continue
        _relative_source_path(Path(module_file), source_root)
        loaded.append(module_name)
    return loaded


def _worker_extract(config: Mapping[str, Any]) -> dict[str, Any]:
    source_root = Path(str(config["shared_source_root"])).resolve()
    if not (source_root / "android_world/registry.py").is_file():
        raise SemanticExtractionError(f"invalid frozen shared source root: {source_root}")
    snapshot = _verify_snapshot(source_root)
    if sys.path[0] != str(source_root):
        sys.path.insert(0, str(source_root))

    from android_world.registry import TaskRegistry
    from android_world.task_evals.information_retrieval.information_retrieval import InformationRetrieval
    from android_world.task_evals.task_eval import TaskEval

    _install_frozen_time_for_markor()
    registry = TaskRegistry().get_registry(TaskRegistry.ANDROID_WORLD_FAMILY)
    task_ids = sorted(str(value) for value in registry)
    expected_task_ids = config.get("expected_task_ids")
    if expected_task_ids is not None and task_ids != sorted(str(value) for value in expected_task_ids):
        raise SemanticExtractionError("frozen registry task IDs differ from expected candidate IDs")
    if len(task_ids) != 116:
        raise SemanticExtractionError(f"expected 116 AndroidWorld registry tasks, found {len(task_ids)}")

    metadata_path = source_root / "android_world/task_metadata.json"
    metadata_rows = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(metadata_rows, list):
        raise SemanticExtractionError("task_metadata.json must be a list")
    metadata_by_name: dict[str, tuple[int, Mapping[str, Any]]] = {}
    for index, row in enumerate(metadata_rows):
        if not isinstance(row, Mapping) or not row.get("task_name"):
            raise SemanticExtractionError(f"malformed metadata row {index}")
        name = str(row["task_name"])
        if name in metadata_by_name:
            raise SemanticExtractionError(f"duplicate task metadata: {name}")
        metadata_by_name[name] = (index, row)
    if set(metadata_by_name) != set(task_ids):
        raise SemanticExtractionError("task metadata and frozen registry task sets differ")

    sample_seeds = tuple(int(value) for value in config.get("sample_seeds", DEFAULT_SAMPLE_SEEDS))
    if not sample_seeds or len(sample_seeds) != len(set(sample_seeds)):
        raise SemanticExtractionError("sample seeds must be a non-empty unique sequence")
    registry_ref = _source_ref(TaskRegistry, source_root, symbol="TaskRegistry")
    records: list[dict[str, Any]] = []
    for task_id in task_ids:
        metadata_index, metadata = metadata_by_name[task_id]
        records.append(
            _extract_record(
                task_id,
                registry[task_id],
                metadata,
                metadata_index,
                metadata_path,
                source_root,
                sample_seeds,
                task_eval_cls=TaskEval,
                information_retrieval_cls=InformationRetrieval,
                registry_ref=registry_ref,
            )
        )

    mechanism_counts = dict(
        sorted(Counter(record["goal"]["representation_kind"] for record in records).items())
    )
    if mechanism_counts != EXPECTED_MECHANISM_COUNTS:
        raise SemanticExtractionError(
            f"goal mechanism count mismatch: {mechanism_counts} != {EXPECTED_MECHANISM_COUNTS}"
        )
    loaded_modules = _validate_loaded_androidworld_modules(source_root)
    bundle: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "source_snapshot": snapshot,
        "extraction_config": {
            "sample_seeds": list(sample_seeds),
            "fixed_wall_clock": FIXED_WALL_CLOCK.isoformat(),
            "python_hash_seed": os.environ.get("PYTHONHASHSEED"),
            "device_execution_performed": False,
        },
        "task_count": len(records),
        "task_ids": task_ids,
        "task_set_sha256": _object_sha256(task_ids),
        "mechanism_counts": mechanism_counts,
        "loaded_androidworld_module_count": len(loaded_modules),
        "all_loaded_androidworld_modules_from_frozen_tree": True,
        "records": records,
    }
    bundle["bundle_sha256"] = _object_sha256(bundle)
    return bundle


def extract_canonical_semantic_records(
    *,
    shared_source_root: str | Path,
    venv_python: str | Path,
    expected_task_ids: Iterable[str] | None = None,
    sample_seeds: Sequence[int] = DEFAULT_SAMPLE_SEEDS,
    timeout_seconds: int = 300,
) -> dict[str, Any]:
    """Returns deterministic canonical semantic records for all 116 tasks.

    Args:
      shared_source_root: Frozen ``shared_source/source_tree`` directory.
      venv_python: AndroidWorld virtualenv Python executable.
      expected_task_ids: Optional candidate-manifest task IDs to assert against.
      sample_seeds: Unique deterministic seeds used for reproducible goal probes.
      timeout_seconds: Worker timeout.  The worker performs no device operation.

    No files are created or modified.  Any diagnostic text from AndroidWorld is
    retained on worker stderr; stdout is reserved for the returned JSON object.
    """

    source_root = Path(shared_source_root).resolve()
    # Do not resolve this symlink on macOS: ``.venv/bin/python`` commonly
    # points at the base interpreter, and resolving it discards pyvenv.cfg and
    # therefore the venv's site-packages (including absl).
    python = Path(venv_python).expanduser()
    if not python.is_absolute():
        python = Path.cwd() / python
    python = python.absolute()
    if not python.is_file():
        raise SemanticExtractionError(f"AndroidWorld venv Python is missing: {python}")
    config = {
        "shared_source_root": str(source_root),
        "expected_task_ids": sorted(str(value) for value in expected_task_ids)
        if expected_task_ids is not None
        else None,
        "sample_seeds": [int(value) for value in sample_seeds],
    }
    env = dict(os.environ)
    env["PYTHONPATH"] = str(source_root)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONHASHSEED"] = "0"
    # This local venv intentionally resolves several AndroidWorld third-party
    # dependencies from its configured user-site path.  We still enforce that
    # every loaded ``android_world.*`` module itself comes from source_root.
    env.pop("PYTHONNOUSERSITE", None)
    completed = subprocess.run(
        [str(python), str(Path(__file__).resolve()), "--worker"],
        input=json.dumps(config, sort_keys=True),
        cwd=Path(tempfile.gettempdir()),
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    if completed.returncode != 0:
        raise SemanticExtractionError(
            f"semantic worker failed ({completed.returncode})\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SemanticExtractionError(
            f"semantic worker returned invalid JSON\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        ) from exc
    if payload.get("task_count") != 116 or payload.get("mechanism_counts") != EXPECTED_MECHANISM_COUNTS:
        raise SemanticExtractionError("semantic worker returned an incomplete bundle")
    expected_hash = payload.get("bundle_sha256")
    unhashed = dict(payload)
    unhashed.pop("bundle_sha256", None)
    if expected_hash != _object_sha256(unhashed):
        raise SemanticExtractionError("semantic bundle hash does not verify")
    return payload


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if not args.worker:
        parser.error("this module is imported by the builder; direct execution requires --worker and JSON stdin")
    config = json.loads(sys.stdin.read())
    payload = _worker_extract(config)
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
