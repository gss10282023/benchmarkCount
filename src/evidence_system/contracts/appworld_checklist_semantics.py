"""Fail-closed AppWorld evaluator-composition checks for case checklists.

AppWorld's released task evaluators sometimes assign convenient dynamic
attributes to ``TestTracker`` (in the frozen data, ``test.task_completed``).
Those assignments are not tests.  A native test is created only by a
``with test(...):`` block containing ``test.answer``, ``test.case``, or
``test.subcases`` calls, and ``TestTracker.success`` is the conjunction
``pass_count == num_tests``.  This module derives that composition from the
official evaluator AST and rejects checklists that promote an unscored dynamic
attribute (or its source predicate) into a native necessary condition.

The validator deliberately consumes both the rendered packet and its raw
official files.  It binds the two byte-for-byte before inspecting semantics so
that a caller cannot validate a checklist against a different evaluator than
the one shown to the drafter.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import unicodedata
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.contracts.appworld_stronger_gaps import (
    parse_packet_stronger_gap_registry,
    validate_stronger_gap_composition,
)
from evidence_system.core.hashing import sha256_file, sha256_object


SEMANTIC_REPORT_SCHEMA = "appworld_checklist_evaluator_semantics.v2"
PACKET_EVALUATOR_REPORT_SCHEMA = "appworld_packet_evaluator_semantics.v2"
TEST_TRACKER_SUCCESS_EXPRESSION = "pass_count == num_tests"
APPWORLD_ALL_TESTS_MARKER = "[appworld_all_registered_tests]"
APPWORLD_UNDECIDED_TEXT = (
    "Undecided only if retained evidence cannot determine one or more frozen "
    "registered-test outcomes."
)
APPWORLD_UNDECIDED_RATIONALE = (
    "A registered-test outcome must not be inferred when its decisive retained "
    "evidence is missing or non-decisive."
)
SCORING_METHODS = frozenset({"answer", "case", "subcases"})
_EVALUATION_RELATIVE_PATH = Path("official/ground_truth/evaluation.py")
_TEST_DATA_RELATIVE_PATH = Path("official/ground_truth/test_data.json")
_SPECS_RELATIVE_PATH = Path("official/specs.json")


class AppWorldChecklistSemanticError(ContractLifecycleError):
    """Raised when AppWorld checklist semantics cannot be accepted."""


def appworld_registered_test_marker(index: int, requirement: str) -> str:
    """Return the packet/checklist marker bound to one ordered test-data requirement."""

    normalized = " ".join(requirement.split())
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
    return f"[appworld_test_{index:03d}_{digest}]"


def appworld_registered_test_success_text(marker: str, requirement: str) -> str:
    normalized = " ".join(requirement.split())
    return (
        f"{marker} passes exactly when this official requirement is satisfied: "
        f"{normalized}"
    )


def appworld_registered_test_fail_text(marker: str, requirement: str) -> str:
    normalized = " ".join(requirement.split())
    return (
        f"{marker} fails exactly when this official requirement is not satisfied: "
        f"{normalized}"
    )


def appworld_benchmark_success_text(markers: Sequence[str]) -> str:
    return (
        f"{APPWORLD_ALL_TESTS_MARKER} all registered tests pass: "
        f"{', '.join(markers)}"
    )


def appworld_required_native_surface(
    *, instruction: str, registered_tests: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Return the exact AppWorld native checklist surface; no free scoring prose remains."""

    markers = [str(record["marker"]) for record in registered_tests]
    evaluator_support = "official/ground_truth/evaluation.py::evaluate"
    test_data_root = "official/ground_truth/test_data.json::$"
    return {
        "user_goal": {
            "text": instruction,
            "support": ["official/specs.json::$.instruction"],
            "rationale": "This is the exact frozen official AppWorld instruction.",
        },
        "benchmark_success": {
            "text": appworld_benchmark_success_text(markers),
            "support": [evaluator_support, test_data_root],
            "rationale": (
                "AppWorld TestTracker success is exactly pass_count == num_tests, so every "
                "frozen registered test must pass."
            ),
        },
        "checked_by": {
            "text": (
                "The official AppWorld evaluate function registers scoring outcomes only "
                "inside with test(requirement) blocks."
            ),
            "support": [evaluator_support, test_data_root],
            "rationale": (
                "Assignments to other TestTracker attributes are excluded from native and "
                "stronger scoring."
            ),
        },
        "decisive_artifacts": [
            {
                "artifact": (
                    "Retained submitted answer, start/end database diff, API log, "
                    "environment trace, and official TestTracker results"
                ),
                "question": (
                    "Do the retained artifacts and TestTracker results establish the outcome "
                    "of every frozen registered test?"
                ),
                "support": [evaluator_support, test_data_root],
            }
        ],
        "success_if": [
            {
                "text": str(record["required_success_if_text"]),
                "support": [
                    evaluator_support,
                    f"official/ground_truth/test_data.json::$[{index}].requirement",
                ],
                "rationale": (
                    "The retained official evidence determines this registered-test pass outcome."
                ),
            }
            for index, record in enumerate(registered_tests)
        ],
        "fail_if": [
            {
                "text": str(record["required_fail_if_text"]),
                "support": [
                    evaluator_support,
                    f"official/ground_truth/test_data.json::$[{index}].requirement",
                ],
                "rationale": (
                    "The retained official evidence determines this registered-test fail outcome."
                ),
            }
            for index, record in enumerate(registered_tests)
        ],
        "undecided_if": [
            {
                "text": APPWORLD_UNDECIDED_TEXT,
                "support": [evaluator_support, test_data_root],
                "rationale": APPWORLD_UNDECIDED_RATIONALE,
            }
        ],
    }


@dataclass(frozen=True)
class _AssignmentSource:
    name: str
    line: int
    expression: str
    value: ast.expr


def _fail(message: str) -> None:
    raise AppWorldChecklistSemanticError(message)


def _read_text(path: str | Path, label: str) -> tuple[Path, str]:
    value = Path(path).expanduser().resolve()
    if not value.is_file():
        _fail(f"{label} is missing or not a file: {value}")
    try:
        return value, value.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise AppWorldChecklistSemanticError(f"{label} is not UTF-8: {value}") from exc


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f"{label} must be a mapping")
    return value


def _require_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(f"{label} must be a non-empty string")
    return value.strip()


def _ast_text(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception as exc:  # pragma: no cover - ast.unparse supports parsed Python 3.11 trees.
        raise AppWorldChecklistSemanticError("could not render official evaluator AST") from exc


def _target_names(target: ast.expr) -> tuple[str, ...]:
    if isinstance(target, ast.Name):
        return (target.id,)
    if isinstance(target, (ast.Tuple, ast.List)):
        return tuple(
            name for child in target.elts for name in _target_names(child)
        )
    return ()


def _assignment_index(function: ast.FunctionDef) -> dict[str, list[_AssignmentSource]]:
    by_name: dict[str, list[_AssignmentSource]] = {}
    for node in ast.walk(function):
        targets: Sequence[ast.expr]
        value: ast.expr | None
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = (node.target,)
            value = node.value
        elif isinstance(node, ast.NamedExpr):
            targets = (node.target,)
            value = node.value
        else:
            continue
        if value is None:
            continue
        for target in targets:
            for name in _target_names(target):
                by_name.setdefault(name, []).append(
                    _AssignmentSource(
                        name=name,
                        line=int(getattr(node, "lineno", 0)),
                        expression=_ast_text(value),
                        value=value,
                    )
                )
    for entries in by_name.values():
        entries.sort(key=lambda item: item.line)
    return by_name


def _related_sources(
    call: ast.Call,
    assignments: Mapping[str, Sequence[_AssignmentSource]],
) -> list[dict[str, Any]]:
    """Conservatively expose local RHS provenance used by a scoring call.

    This is intentionally an audit aid, not a claim of path-sensitive Python
    dataflow.  For each referenced local, it follows the latest preceding
    assignment and recursively follows locals in that RHS.  Branch-heavy
    evaluators therefore remain fail-closed for composition while retaining a
    readable account of the source expressions that informed each check.
    """

    found: dict[tuple[str, int, str], dict[str, Any]] = {}
    pending = [
        node.id
        for argument in (*call.args, *(keyword.value for keyword in call.keywords))
        for node in ast.walk(argument)
        if isinstance(node, ast.Name)
    ]
    seen_names: set[str] = set()
    while pending:
        name = pending.pop()
        if name in seen_names:
            continue
        seen_names.add(name)
        candidates = [item for item in assignments.get(name, ()) if item.line < call.lineno]
        if not candidates:
            continue
        source = candidates[-1]
        key = (source.name, source.line, source.expression)
        found[key] = {
            "name": source.name,
            "line": source.line,
            "expression": source.expression,
            "semantic_atoms": _semantic_atoms(source.value),
        }
        pending.extend(
            node.id for node in ast.walk(source.value) if isinstance(node, ast.Name)
        )
    return [found[key] for key in sorted(found, key=lambda item: (item[1], item[0], item[2]))]


def _nearest_scoring_block(
    node: ast.AST,
    parents: Mapping[ast.AST, ast.AST],
    scoring_blocks: set[ast.With],
) -> ast.With | None:
    current = parents.get(node)
    while current is not None:
        if isinstance(current, ast.With) and current in scoring_blocks:
            return current
        current = parents.get(current)
    return None


def _literal_requirement(context: ast.Call, line: int) -> str:
    if len(context.args) != 1 or context.keywords:
        _fail(f"evaluation.py:{line}: with test(...) must have exactly one positional argument")
    try:
        value = ast.literal_eval(context.args[0])
    except (TypeError, ValueError) as exc:
        raise AppWorldChecklistSemanticError(
            f"evaluation.py:{line}: with test(...) requirement must be a literal string"
        ) from exc
    return _require_nonempty_string(value, f"evaluation.py:{line} test requirement")


def _semantic_atoms(node: ast.AST) -> dict[str, list[str]]:
    attributes = sorted(
        {child.attr.casefold() for child in ast.walk(node) if isinstance(child, ast.Attribute)}
    )
    names = sorted(
        {child.id.casefold() for child in ast.walk(node) if isinstance(child, ast.Name)}
    )
    constants = sorted(
        {
            str(child.value).casefold()
            for child in ast.walk(node)
            if isinstance(child, ast.Constant)
            and isinstance(child.value, (str, int, float, bool))
        }
    )
    return {"attributes": attributes, "names": names, "constants": constants}


def _extract_evaluator_semantics(
    evaluation_source: str,
    test_data: Any,
) -> dict[str, Any]:
    try:
        module = ast.parse(evaluation_source, filename="evaluation.py")
    except SyntaxError as exc:
        raise AppWorldChecklistSemanticError(
            f"official evaluation.py is not valid Python: line {exc.lineno}: {exc.msg}"
        ) from exc

    functions = [
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "evaluate"
    ]
    if len(functions) != 1:
        _fail("official evaluation.py must contain exactly one top-level evaluate function")
    function = functions[0]
    if not function.args.args or function.args.args[0].arg != "test":
        _fail("official evaluate function must receive TestTracker as its first parameter `test`")
    annotation = function.args.args[0].annotation
    if not isinstance(annotation, ast.Name) or annotation.id != "TestTracker":
        _fail("official evaluate(test) parameter must be annotated as TestTracker")

    parents = {
        child: parent
        for parent in ast.walk(function)
        for child in ast.iter_child_nodes(parent)
    }
    scoring_blocks: list[ast.With] = []
    block_contexts: dict[ast.With, ast.Call] = {}
    for node in ast.walk(function):
        if not isinstance(node, ast.With):
            continue
        if len(node.items) != 1:
            _fail(f"evaluation.py:{node.lineno}: multi-context with statement is unsupported")
        item = node.items[0]
        context = item.context_expr
        if not (
            isinstance(context, ast.Call)
            and isinstance(context.func, ast.Name)
            and context.func.id == "test"
        ):
            _fail(
                f"evaluation.py:{node.lineno}: only official with test(...) contexts are supported"
            )
        if item.optional_vars is not None:
            _fail(f"evaluation.py:{node.lineno}: with test(...) cannot bind an `as` target")
        _literal_requirement(context, node.lineno)
        scoring_blocks.append(node)
        block_contexts[node] = context
    scoring_blocks.sort(key=lambda node: (node.lineno, node.col_offset))
    if not scoring_blocks:
        _fail("official evaluate function contains no with test(...) scoring blocks")
    scoring_block_set = set(scoring_blocks)

    assignments = _assignment_index(function)
    scoring_calls_by_block: dict[ast.With, list[ast.Call]] = {
        block: [] for block in scoring_blocks
    }
    scoring_calls: list[dict[str, Any]] = []
    test_attribute_call_nodes: set[ast.Attribute] = set()
    context_call_nodes = set(block_contexts.values())
    for node in ast.walk(function):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "test":
            if node not in context_call_nodes:
                _fail(f"evaluation.py:{node.lineno}: test(...) may only be used as a with context")
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "test"
        ):
            continue
        method = node.func.attr
        if method not in SCORING_METHODS:
            _fail(f"evaluation.py:{node.lineno}: unsupported TestTracker call test.{method}(...)")
        block = _nearest_scoring_block(node, parents, scoring_block_set)
        if block is None:
            _fail(
                f"evaluation.py:{node.lineno}: test.{method}(...) is outside with test(...)"
            )
        scoring_calls_by_block[block].append(node)
        test_attribute_call_nodes.add(node.func)
        argument_node = ast.Tuple(
            elts=[*node.args, *(keyword.value for keyword in node.keywords)],
            ctx=ast.Load(),
        )
        scoring_calls.append(
            {
                "method": method,
                "line": int(node.lineno),
                "expression": _ast_text(node),
                "argument_expressions": [_ast_text(argument) for argument in node.args],
                "semantic_atoms": _semantic_atoms(argument_node),
                "source_expressions": _related_sources(node, assignments),
            }
        )
    scoring_calls.sort(key=lambda item: (item["line"], item["method"], item["expression"]))
    for block, calls in scoring_calls_by_block.items():
        if not calls:
            _fail(
                f"evaluation.py:{block.lineno}: with test(...) has no test.answer/case/subcases call"
            )

    non_scoring_assignments: list[dict[str, Any]] = []
    test_assignment_attributes: set[ast.Attribute] = set()
    for node in ast.walk(function):
        targets: Sequence[ast.expr]
        value: ast.expr | None
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = (node.target,)
            value = node.value
        elif isinstance(node, ast.AugAssign):
            targets = (node.target,)
            value = node.value
        else:
            continue
        for target in targets:
            if not (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "test"
            ):
                continue
            test_assignment_attributes.add(target)
            if value is None:
                _fail(f"evaluation.py:{node.lineno}: TestTracker assignment has no value")
            if _nearest_scoring_block(node, parents, scoring_block_set) is not None:
                _fail(
                    f"evaluation.py:{node.lineno}: assigning test.{target.attr} inside a scoring block "
                    "has unsupported dataflow"
                )
            non_scoring_assignments.append(
                {
                    "attribute": target.attr,
                    "line": int(node.lineno),
                    "source_expression": _ast_text(value),
                    "semantic_atoms": _semantic_atoms(value),
                }
            )
    non_scoring_assignments.sort(
        key=lambda item: (item["line"], item["attribute"], item["source_expression"])
    )

    # Any other direct read/mutation of the tracker would make the deliberately
    # narrow composition model incomplete, so reject it instead of guessing.
    for node in ast.walk(function):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {
            "getattr",
            "setattr",
            "delattr",
        }:
            if node.args and isinstance(node.args[0], ast.Name) and node.args[0].id == "test":
                _fail(
                    f"evaluation.py:{node.lineno}: reflective TestTracker access is unsupported"
                )
        if not (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "test"
        ):
            continue
        if node in test_attribute_call_nodes or node in test_assignment_attributes:
            continue
        _fail(f"evaluation.py:{node.lineno}: unsupported direct access to test.{node.attr}")

    if not isinstance(test_data, list) or not test_data:
        _fail("official test_data.json must be a non-empty array")
    test_requirements: list[str] = []
    for index, item in enumerate(test_data):
        record = _require_mapping(item, f"test_data.json[{index}]")
        test_requirements.append(
            _require_nonempty_string(
                record.get("requirement"), f"test_data.json[{index}].requirement"
            )
        )
        _require_nonempty_string(record.get("label"), f"test_data.json[{index}].label")

    registered_test_registry = []
    for index, requirement in enumerate(test_requirements, start=1):
        marker = appworld_registered_test_marker(index, requirement)
        registered_test_registry.append(
            {
                "index": index,
                "marker": marker,
                "requirement": requirement,
                "requirement_sha256": hashlib.sha256(
                    " ".join(requirement.split()).encode("utf-8")
                ).hexdigest(),
                "required_success_if_text": appworld_registered_test_success_text(
                    marker, requirement
                ),
                "required_fail_if_text": appworld_registered_test_fail_text(
                    marker, requirement
                ),
            }
        )

    def normalize_requirement(value: str) -> str:
        return " ".join(value.split())

    block_requirements = [
        _literal_requirement(block_contexts[block], block.lineno) for block in scoring_blocks
    ]
    normalized_blocks = Counter(normalize_requirement(value) for value in block_requirements)
    normalized_data = Counter(normalize_requirement(value) for value in test_requirements)
    if normalized_blocks != normalized_data:
        _fail(
            "official evaluation.py with-test requirements do not match test_data.json "
            "as a multiset"
        )

    for block, requirement in zip(scoring_blocks, block_requirements, strict=True):
        for call in scoring_calls:
            if any(node.lineno == call["line"] for node in scoring_calls_by_block[block]):
                # Lines are unique for the frozen evaluators; keep the report
                # compact while binding each call to its enclosing requirement.
                call["requirement"] = requirement

    scored_attributes = sorted(
        {
            attribute
            for call in scoring_calls
            for attribute in (
                *call["semantic_atoms"]["attributes"],
                *(
                    attribute
                    for source in call["source_expressions"]
                    for attribute in source["semantic_atoms"]["attributes"]
                ),
            )
        }
    )
    return {
        "test_tracker_success": {
            "expression": TEST_TRACKER_SUCCESS_EXPRESSION,
            "composition": "all_with_test_blocks_must_pass",
        },
        "scoring_block_count": len(scoring_blocks),
        "scoring_call_count": len(scoring_calls),
        "scoring_methods": sorted({call["method"] for call in scoring_calls}),
        "scored_source_attributes": scored_attributes,
        "scoring_calls": scoring_calls,
        "non_scoring_test_assignments": non_scoring_assignments,
        "test_data_requirement_count": len(test_requirements),
        "registered_test_registry": registered_test_registry,
    }


def derive_appworld_evaluator_semantics(
    evaluation_source: str, test_data: Any
) -> dict[str, Any]:
    """Derive the canonical scoring/non-scoring AST registry from official sources."""

    return _extract_evaluator_semantics(evaluation_source, test_data)


def _packet_case_id(packet_text: str) -> str:
    values: dict[str, str] = {}
    for field in ("domain", "case_unit_id", "task_id"):
        matches = re.findall(
            rf"^- {re.escape(field)}:\s*`([^`]+)`\s*$", packet_text, flags=re.MULTILINE
        )
        if len(matches) != 1:
            _fail(f"case packet must contain exactly one `{field}` metadata row")
        values[field] = matches[0]
    if values["domain"].casefold() != "appworld":
        _fail("case packet domain must be appworld")
    if values["case_unit_id"] != values["task_id"]:
        _fail("case packet case_unit_id/task_id mismatch")
    return values["case_unit_id"]


def _embedded_source(packet_text: str, relative_path: Path) -> str:
    relative = relative_path.as_posix()
    section = re.search(
        rf"^### `{re.escape(relative)}`\s*$\n(?P<body>.*?)(?=^### `|\Z)",
        packet_text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if section is None:
        _fail(f"case packet is missing rendered source section {relative}")
    fenced = re.search(
        r"^```[^\n]*\n(?P<source>.*?)^```\s*$",
        section.group("body"),
        flags=re.MULTILINE | re.DOTALL,
    )
    if fenced is None:
        _fail(f"case packet source section {relative} has no single rendered code fence")
    return fenced.group("source")


def _bind_packet_source(
    *,
    packet_path: Path,
    packet_text: str,
    raw_path: Path,
    relative_path: Path,
) -> None:
    expected = (packet_path.parent / "raw_case" / relative_path).resolve()
    if raw_path != expected:
        _fail(
            f"{relative_path.as_posix()} must be the packet-local raw official file: "
            f"expected {expected}, got {raw_path}"
        )
    raw_text = raw_path.read_text(encoding="utf-8")
    embedded = _embedded_source(packet_text, relative_path)
    # The packet renderer terminates a Markdown code fence on a fresh line, so
    # it adds one newline only when the raw source did not already end in one.
    expected_embedded = raw_text if raw_text.endswith("\n") else raw_text + "\n"
    if embedded != expected_embedded:
        _fail(f"case packet rendered {relative_path.as_posix()} differs from raw official bytes")


def _packet_registered_test_registry(packet_text: str) -> Mapping[str, Any]:
    heading = "### Machine-verifiable registered-test registry"
    heading_matches = re.findall(
        r"^[ ]{0,3}#{1,6}[ \t]+Machine-verifiable[ \t]+registered-test[ \t]+registry"
        r"(?:[ \t]+#+)?[ \t]*$",
        packet_text,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    if heading_matches != [heading]:
        _fail(
            "case packet must contain one exact, unambiguous registered-test registry heading"
        )
    sections = re.findall(
        r"^### Machine-verifiable registered-test registry\s*$\n(?P<body>.*?)(?=^### |^## |\Z)",
        packet_text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if len(sections) != 1:
        _fail(
            "case packet must contain exactly one machine-verifiable registered-test registry"
        )
    fenced = re.findall(
        r"^```json\s*$\n(?P<json>.*?)^```\s*$",
        sections[0],
        flags=re.MULTILINE | re.DOTALL,
    )
    if len(fenced) != 1:
        _fail("case packet registered-test registry must contain exactly one JSON fence")
    try:
        payload = json.loads(fenced[0])
    except json.JSONDecodeError as exc:
        raise AppWorldChecklistSemanticError(
            "case packet registered-test registry JSON is malformed"
        ) from exc
    return _require_mapping(payload, "case packet registered-test registry")


def appworld_packet_registered_test_registry(packet_text: str) -> dict[str, Any]:
    """Parse the single packet registry for deterministic pre-run audits."""

    return dict(_packet_registered_test_registry(packet_text))


def _native_required_texts(checklist: Mapping[str, Any]) -> list[tuple[str, str]]:
    native = _require_mapping(checklist.get("native"), "checklist.native")
    values: list[tuple[str, str]] = []
    benchmark = _require_mapping(
        native.get("benchmark_success"), "checklist.native.benchmark_success"
    )
    values.append(
        (
            "native.benchmark_success.text",
            _require_nonempty_string(
                benchmark.get("text"), "checklist.native.benchmark_success.text"
            ),
        )
    )
    for field in ("success_if", "fail_if", "undecided_if"):
        items = native.get(field)
        if not isinstance(items, list) or not items:
            _fail(f"checklist.native.{field} must be a non-empty array")
        for index, item in enumerate(items):
            record = _require_mapping(item, f"checklist.native.{field}[{index}]")
            values.append(
                (
                    f"native.{field}[{index}].text",
                    _require_nonempty_string(
                        record.get("text"), f"checklist.native.{field}[{index}].text"
                    ),
                )
            )
    artifacts = native.get("decisive_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        _fail("checklist.native.decisive_artifacts must be a non-empty array")
    for index, item in enumerate(artifacts):
        record = _require_mapping(item, f"checklist.native.decisive_artifacts[{index}]")
        artifact = _require_nonempty_string(
            record.get("artifact"),
            f"checklist.native.decisive_artifacts[{index}].artifact",
        )
        question = _require_nonempty_string(
            record.get("question"),
            f"checklist.native.decisive_artifacts[{index}].question",
        )
        values.append(
            (f"native.decisive_artifacts[{index}]", f"{artifact}. {question}")
        )
    return values


_REGISTERED_TEST_MARKER_RE = re.compile(r"\[appworld_test_[0-9]{3}_[0-9a-f]{12}\]")
_STRONGER_GAP_MARKER_RE = re.compile(
    r"\[appworld_stronger_gap_[0-9]{3}_[0-9a-f]{12}\]"
)
_APPWORLD_MARKER_SHAPED_RE = re.compile(
    r"\[\s*appworld_[^\]\r\n]*\]",
    flags=re.IGNORECASE,
)


def _string_leaves(value: Any, *, path: str = "checklist") -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, Mapping):
        leaves: list[tuple[str, str]] = []
        for key, child in value.items():
            leaves.extend(_string_leaves(child, path=f"{path}.{key}"))
        return leaves
    if isinstance(value, list):
        leaves = []
        for index, child in enumerate(value):
            leaves.extend(_string_leaves(child, path=f"{path}[{index}]"))
        return leaves
    return []


def _validate_registered_test_composition(
    *, checklist: Mapping[str, Any], semantics: Mapping[str, Any]
) -> dict[str, Any]:
    native = _require_mapping(checklist.get("native"), "checklist.native")
    registry_raw = semantics.get("registered_test_registry")
    if not isinstance(registry_raw, list) or not registry_raw:
        _fail("derived registered-test registry is empty")
    expected_markers = [
        _require_nonempty_string(
            _require_mapping(item, "registered-test record").get("marker"),
            "registered-test marker",
        )
        for item in registry_raw
    ]
    expected_requirements = [
        _require_nonempty_string(
            _require_mapping(item, "registered-test record").get("requirement"),
            "registered-test requirement",
        )
        for item in registry_raw
    ]
    invalid_marker_set = (
        len(expected_markers) != len(set(expected_markers))
        or any(_REGISTERED_TEST_MARKER_RE.fullmatch(marker) is None for marker in expected_markers)
    )
    if invalid_marker_set:
        _fail("derived registered-test markers are invalid or duplicated")

    benchmark = _require_mapping(
        native.get("benchmark_success"), "checklist.native.benchmark_success"
    )
    benchmark_text = _require_nonempty_string(
        benchmark.get("text"), "checklist.native.benchmark_success.text"
    )
    stronger = _require_mapping(checklist.get("stronger"), "checklist.stronger")
    stronger_conditions = stronger.get("additional_conditions")
    if not isinstance(stronger_conditions, list):
        _fail("checklist.stronger.additional_conditions must be an array")
    stronger_markers: list[str] = []
    stronger_marker_locations: dict[str, str] = {}
    for index, raw_condition in enumerate(stronger_conditions):
        condition = _require_mapping(
            raw_condition, f"checklist.stronger.additional_conditions[{index}]"
        )
        text = _require_nonempty_string(
            condition.get("text"),
            f"checklist.stronger.additional_conditions[{index}].text",
        )
        markers = _STRONGER_GAP_MARKER_RE.findall(text)
        if len(markers) > 1:
            _fail(
                "a stronger condition may not contain multiple canonical stronger-gap markers"
            )
        if not markers:
            continue
        marker = markers[0]
        if marker in stronger_marker_locations:
            _fail("stronger conditions may not duplicate a stronger-gap marker")
        stronger_markers.append(marker)
        stronger_marker_locations[marker] = (
            f"checklist.stronger.additional_conditions[{index}].text"
        )
    allowed_markers = {
        APPWORLD_ALL_TESTS_MARKER,
        *expected_markers,
        *stronger_markers,
    }
    global_marker_counts: Counter[str] = Counter()
    global_marker_locations: dict[str, list[str]] = {}
    for path, text in _string_leaves(checklist):
        without_closed_markers = _APPWORLD_MARKER_SHAPED_RE.sub("", text)
        if re.search(r"\[\s*appworld_", without_closed_markers, flags=re.I):
            _fail(f"{path} contains an unclosed or malformed AppWorld marker prefix")
        for match in _APPWORLD_MARKER_SHAPED_RE.finditer(text):
            marker = match.group(0)
            if marker not in allowed_markers:
                _fail(f"{path} contains an unknown or malformed AppWorld marker: {marker}")
            global_marker_counts[marker] += 1
            global_marker_locations.setdefault(marker, []).append(path)
    if (
        global_marker_counts[APPWORLD_ALL_TESTS_MARKER] != 1
        or global_marker_locations.get(APPWORLD_ALL_TESTS_MARKER)
        != ["checklist.native.benchmark_success.text"]
    ):
        _fail(
            f"{APPWORLD_ALL_TESTS_MARKER} must occur exactly once globally and only in "
            "checklist.native.benchmark_success.text"
        )
    for marker in expected_markers:
        if global_marker_counts[marker] != 3:
            _fail(
                f"{marker} must occur exactly once in benchmark_success, success_if, and "
                "fail_if, with no occurrence elsewhere"
            )
    for marker in stronger_markers:
        if (
            global_marker_counts[marker] != 1
            or global_marker_locations.get(marker)
            != [stronger_marker_locations[marker]]
        ):
            _fail(
                f"{marker} must occur exactly once globally and only in its canonical "
                "stronger condition text"
            )
    benchmark_markers = _REGISTERED_TEST_MARKER_RE.findall(benchmark_text)
    required_benchmark_text = appworld_benchmark_success_text(expected_markers)
    if benchmark_text != required_benchmark_text:
        _fail(
            "native.benchmark_success.text must exactly equal the frozen registered-test "
            "conjunction from the packet registry"
        )

    surface_audits: dict[str, Any] = {}
    for field, polarity in (("success_if", "pass"), ("fail_if", "fail")):
        items = native.get(field)
        if not isinstance(items, list) or len(items) != len(expected_markers):
            _fail(
                f"checklist.native.{field} must contain exactly one item per frozen "
                "AppWorld registered test"
            )
        marker_counts: Counter[str] = Counter()
        marker_sequence: list[str] = []
        for index, (item, marker, requirement) in enumerate(
            zip(items, expected_markers, expected_requirements, strict=True)
        ):
            record = _require_mapping(item, f"checklist.native.{field}[{index}]")
            text = _require_nonempty_string(
                record.get("text"), f"checklist.native.{field}[{index}].text"
            )
            markers = _REGISTERED_TEST_MARKER_RE.findall(text)
            marker_counts.update(markers)
            marker_sequence.extend(markers)
            required_text = (
                appworld_registered_test_success_text(marker, requirement)
                if polarity == "pass"
                else appworld_registered_test_fail_text(marker, requirement)
            )
            if markers != [marker] or text != required_text:
                _fail(
                    f"checklist.native.{field}[{index}].text must be exactly "
                    f"{required_text!r} so requirement and polarity are bound to one marker"
                )
        if marker_counts != Counter(expected_markers):
            _fail(
                f"checklist.native.{field} must cover every frozen AppWorld test marker "
                "exactly once and contain no unknown marker"
            )
        surface_audits[field] = {
            "marker_count": sum(marker_counts.values()),
            "markers_semantic_order": marker_sequence,
        }
    undecided_items = native.get("undecided_if")
    if not isinstance(undecided_items, list) or len(undecided_items) != 1:
        _fail("checklist.native.undecided_if must contain exactly one frozen rule")
    undecided = _require_mapping(
        undecided_items[0], "checklist.native.undecided_if[0]"
    )
    if (
        undecided.get("text") != APPWORLD_UNDECIDED_TEXT
        or undecided.get("rationale") != APPWORLD_UNDECIDED_RATIONALE
    ):
        _fail(
            "checklist.native.undecided_if[0] must exactly equal the frozen "
            "registered-test evidence rule and rationale"
        )
    return {
        "all_tests_marker": APPWORLD_ALL_TESTS_MARKER,
        "registered_test_count": len(expected_markers),
        "registered_test_markers": expected_markers,
        "required_benchmark_success_text": required_benchmark_text,
        "required_undecided_if_text": APPWORLD_UNDECIDED_TEXT,
        "required_undecided_if_rationale": APPWORLD_UNDECIDED_RATIONALE,
        "benchmark_marker_count": len(benchmark_markers),
        "surfaces": surface_audits,
    }


def _normalized_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = "".join(
        " " if unicodedata.category(character) == "Cf" else character
        for character in value
    )
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


_EXCLUSION_PATTERNS = (
    re.compile(r"\bregardless of (?:the )?(?:supervisor )?task(?:'s)? status\b"),
    re.compile(r"\b(?:task )?status (?:is |remains )?(?:not scored|unscored|ignored|irrelevant)\b"),
    re.compile(r"\b(?:does not|doesn't) (?:depend on|require|include)\b.{0,50}\btask status\b"),
    re.compile(r"\btask status\b.{0,50}\b(?:does not|doesn't) (?:affect|contribute|count)\b"),
    re.compile(r"\btask completed\b.{0,50}\b(?:not scored|unscored|ignored|irrelevant)\b"),
)

_TASK_COMPLETION_PREDICATE_PATTERNS = (
    re.compile(
        r"\b(?:supervisor )?task\s+"
        r"(?:is|was|must be|should be|needs? to be|has been)\s+"
        r"(?:successful|complete|completed|done|finished)\b"
    ),
    re.compile(
        r"\b(?:supervisor )?task\s+(?:must|should|needs? to)\s+"
        r"(?:succeed|be successful|be complete|be completed|finish)\b"
    ),
    re.compile(
        r"\b(?:complete|completed|finish|finished|succeed|succeeded)\s+"
        r"(?:the\s+)?(?:supervisor\s+)?task\b"
    ),
)


def _sentence_explicitly_excludes_predicate(sentence: str) -> bool:
    return any(pattern.search(sentence) for pattern in _EXCLUSION_PATTERNS)


def _assignment_aliases(assignment: Mapping[str, Any]) -> tuple[str, ...]:
    attribute = str(assignment["attribute"])
    words = _normalized_text(attribute)
    aliases = {words}
    if words.endswith(" completed"):
        aliases.add(words[: -len(" completed")] + " completion")
    return tuple(sorted(alias for alias in aliases if alias))


def _text_requires_non_scoring_assignment(
    text: str,
    assignment: Mapping[str, Any],
    *,
    scored_attributes: set[str],
) -> bool:
    normalized = _normalized_text(text)
    exact_sentences = [
        clause.strip(" ,:")
        for sentence in re.split(r"(?<=[.!?;])\s+", normalized)
        for clause in re.split(
            r"\s+\b(?:but|however|yet)\b\s+|,\s*(?=(?:native\s+)?(?:success|failure)\b)",
            sentence,
        )
        if clause.strip(" ,:")
    ]
    atoms = _require_mapping(assignment.get("semantic_atoms"), "assignment semantic atoms")
    attributes = {
        str(value).casefold() for value in atoms.get("attributes", []) if isinstance(value, str)
    }
    constants = {
        str(value).casefold() for value in atoms.get("constants", []) if isinstance(value, str)
    }
    aliases = _assignment_aliases(assignment)
    status_is_exclusively_non_scoring = "status" in attributes and "status" not in scored_attributes
    success_predicate = "success" in constants

    for sentence in exact_sentences:
        explicitly_excludes = _sentence_explicitly_excludes_predicate(sentence)
        if (
            any(re.search(rf"\b{re.escape(alias)}\b", sentence) for alias in aliases)
            and not explicitly_excludes
        ):
            return True

    # Keep exact snake_case aliases visible above (so ``task_completed`` is
    # rejected), but remove all snake_case identifiers from the broader prose
    # heuristic.  Otherwise an independently scored field such as
    # ``is_completed`` contributes the word ``completed`` and can be falsely
    # conflated with the unscored ``test.task_completed`` assignment merely
    # because the same requirement also mentions a task.
    prose_only = re.sub(r"\b[a-zA-Z][a-zA-Z0-9]*(?:_[a-zA-Z0-9]+)+\b", " ", text)
    heuristic_sentences = [
        clause.strip(" ,:")
        for sentence in re.split(r"(?<=[.!?;])\s+", _normalized_text(prose_only))
        for clause in re.split(
            r"\s+\b(?:but|however|yet)\b\s+|,\s*(?=(?:native\s+)?(?:success|failure)\b)",
            sentence,
        )
        if clause.strip(" ,:")
    ]
    for sentence in heuristic_sentences:
        explicitly_excludes = _sentence_explicitly_excludes_predicate(sentence)
        words = set(re.findall(r"[a-z0-9]+", sentence))
        task_context = bool(words & {"task", "tasks", "supervisor"})
        if explicitly_excludes:
            continue
        if status_is_exclusively_non_scoring and task_context and "status" in words:
            return True
        if (
            status_is_exclusively_non_scoring
            and success_predicate
            and task_context
            and (
                bool(
                    words
                    & {
                        "status",
                        "success",
                        "successful",
                        "successfully",
                        "succeed",
                        "succeeds",
                        "succeeded",
                        "outcome",
                    }
                )
                or any(
                    pattern.search(sentence)
                    for pattern in _TASK_COMPLETION_PREDICATE_PATTERNS
                )
            )
        ):
            return True
        if (
            success_predicate
            and bool(words & {"complete", "completed", "completion"})
            and bool(words & {"assign", "assigned", "evaluate", "evaluator", "flag", "test", "tracker"})
            and bool(words & {"success", "successful", "true"})
        ):
            return True
    return False


def validate_appworld_checklist_semantics(
    *,
    case_packet_path: str | Path,
    evaluation_path: str | Path,
    test_data_path: str | Path,
    checklist: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate one checklist against packet-bound official AppWorld semantics.

    The returned report is deterministic and suitable for inclusion in a
    runtime-gate or final-acceptance receipt.  Any ambiguity, unsupported AST
    construct, packet/raw mismatch, or native use of an unscored predicate
    raises :class:`AppWorldChecklistSemanticError`.
    """

    packet_file, packet_text = _read_text(case_packet_path, "case packet")
    evaluation_file, evaluation_source = _read_text(evaluation_path, "official evaluation.py")
    test_data_file, test_data_source = _read_text(test_data_path, "official test_data.json")
    specs_file, specs_source = _read_text(
        packet_file.parent / "raw_case" / _SPECS_RELATIVE_PATH,
        "official specs.json",
    )
    _bind_packet_source(
        packet_path=packet_file,
        packet_text=packet_text,
        raw_path=evaluation_file,
        relative_path=_EVALUATION_RELATIVE_PATH,
    )
    _bind_packet_source(
        packet_path=packet_file,
        packet_text=packet_text,
        raw_path=test_data_file,
        relative_path=_TEST_DATA_RELATIVE_PATH,
    )
    _bind_packet_source(
        packet_path=packet_file,
        packet_text=packet_text,
        raw_path=specs_file,
        relative_path=_SPECS_RELATIVE_PATH,
    )
    case_id = _packet_case_id(packet_text)
    checklist_mapping = _require_mapping(checklist, "checklist")
    checklist_case_id = _require_nonempty_string(
        checklist_mapping.get("case_unit_id"), "checklist.case_unit_id"
    )
    checklist_task_id = _require_nonempty_string(
        checklist_mapping.get("task_id"), "checklist.task_id"
    )
    if checklist_mapping.get("domain") != "appworld":
        _fail(f"{case_id}: checklist.domain must be appworld")
    if checklist_case_id != case_id or checklist_task_id != case_id:
        _fail(
            f"{case_id}: checklist case_unit_id/task_id must both match the packet identity"
        )
    try:
        test_data = json.loads(test_data_source)
    except json.JSONDecodeError as exc:
        raise AppWorldChecklistSemanticError(
            f"{case_id}: official test_data.json is malformed: {exc}"
        ) from exc
    try:
        specs = json.loads(specs_source)
    except json.JSONDecodeError as exc:
        raise AppWorldChecklistSemanticError(
            f"{case_id}: official specs.json is malformed: {exc}"
        ) from exc
    if not isinstance(specs, Mapping) or not isinstance(specs.get("instruction"), str):
        _fail(f"{case_id}: official specs instruction is invalid")

    semantics = _extract_evaluator_semantics(evaluation_source, test_data)
    packet_registry = _packet_registered_test_registry(packet_text)
    registry_markers = [
        _require_nonempty_string(record.get("marker"), "registered-test marker")
        for record in semantics["registered_test_registry"]
    ]
    expected_packet_registry = {
        "all_tests_marker": APPWORLD_ALL_TESTS_MARKER,
        "required_benchmark_success_text": appworld_benchmark_success_text(
            registry_markers
        ),
        "required_undecided_if_text": APPWORLD_UNDECIDED_TEXT,
        "required_undecided_if_rationale": APPWORLD_UNDECIDED_RATIONALE,
        "registered_tests": semantics["registered_test_registry"],
        "required_native": appworld_required_native_surface(
            instruction=specs["instruction"],
            registered_tests=semantics["registered_test_registry"],
        ),
    }
    if dict(packet_registry) != expected_packet_registry:
        _fail(f"{case_id}: packet registered-test registry differs from official test_data.json")
    gap_payload = parse_packet_stronger_gap_registry(packet_text)
    gap_entry = _require_mapping(gap_payload.get("case"), "packet stronger-gap case")
    if gap_entry.get("case_unit_id") != case_id:
        _fail(f"{case_id}: packet stronger-gap case identity mismatch")
    if gap_entry.get("registered_test_registry_sha256") != sha256_object(
        expected_packet_registry
    ):
        _fail(f"{case_id}: packet stronger-gap/native-test registry hash mismatch")
    if (
        gap_entry.get("non_scoring_assignment_registry")
        != semantics["non_scoring_test_assignments"]
        or gap_entry.get("non_scoring_assignment_registry_sha256")
        != sha256_object(semantics["non_scoring_test_assignments"])
        or gap_entry.get("non_scoring_assignment_exclusion_status")
        != "excluded_from_native_and_stronger_scoring"
    ):
        _fail(f"{case_id}: packet non-scoring assignment registry differs from evaluator AST")
    composition_audit = _validate_registered_test_composition(
        checklist=checklist_mapping,
        semantics=semantics,
    )
    if checklist_mapping.get("native") != expected_packet_registry["required_native"]:
        _fail(
            f"{case_id}: checklist.native must exactly equal the frozen packet required_native"
        )
    stronger_audit = validate_stronger_gap_composition(
        packet_payload=gap_payload,
        checklist=checklist_mapping,
    )
    required_texts = _native_required_texts(checklist_mapping)
    stronger_required_texts = _string_leaves(
        _require_mapping(checklist_mapping.get("stronger"), "checklist.stronger"),
        path="checklist.stronger",
    )
    scored_attributes = set(semantics["scored_source_attributes"])
    findings: list[dict[str, Any]] = []
    for assignment in semantics["non_scoring_test_assignments"]:
        for field_path, text in [*required_texts, *stronger_required_texts]:
            if _text_requires_non_scoring_assignment(
                text, assignment, scored_attributes=scored_attributes
            ):
                findings.append(
                    {
                        "code": "native_requires_non_scoring_test_attribute",
                        "field": field_path,
                        "test_attribute": assignment["attribute"],
                        "assignment_line": assignment["line"],
                        "source_expression": assignment["source_expression"],
                    }
                )
    if findings:
        details = "; ".join(
            f"{item['field']} requires unscored test.{item['test_attribute']} "
            f"from evaluation.py:{item['assignment_line']}"
            for item in findings[:8]
        )
        suffix = "" if len(findings) <= 8 else f"; plus {len(findings) - 8} more"
        _fail(f"{case_id}: AppWorld evaluator-composition gate rejected checklist: {details}{suffix}")

    return {
        "schema_version": SEMANTIC_REPORT_SCHEMA,
        "status": "passed",
        "case_id": case_id,
        "case_packet_sha256": sha256_file(packet_file),
        "evaluation_sha256": sha256_file(evaluation_file),
        "test_data_sha256": sha256_file(test_data_file),
        "specs_sha256": sha256_file(specs_file),
        **semantics,
        "registered_test_composition": composition_audit,
        "stronger_gap_composition": stronger_audit,
        "native_required_field_count": len(required_texts),
        "non_scoring_native_requirement_count": 0,
        "stronger_required_field_count": len(stronger_required_texts),
        "non_scoring_stronger_requirement_count": 0,
        "non_scoring_assignment_registry_sha256": sha256_object(
            semantics["non_scoring_test_assignments"]
        ),
    }


def validate_appworld_packet_evaluator_semantics(
    *, case_packet_root: str | Path
) -> dict[str, Any]:
    """Validate packet bytes, evaluator AST, test_data, and frozen registry pre-draft."""

    root = Path(case_packet_root).expanduser().resolve()
    if not root.is_dir() or root.is_symlink():
        _fail(f"case packet root is missing, symlinked, or not a directory: {root}")
    packet_file, packet_text = _read_text(root / "case_packet.md", "case packet")
    evaluation_file, evaluation_source = _read_text(
        root / "raw_case" / _EVALUATION_RELATIVE_PATH,
        "official evaluation.py",
    )
    test_data_file, test_data_source = _read_text(
        root / "raw_case" / _TEST_DATA_RELATIVE_PATH,
        "official test_data.json",
    )
    specs_file, specs_source = _read_text(
        root / "raw_case" / _SPECS_RELATIVE_PATH,
        "official specs.json",
    )
    _bind_packet_source(
        packet_path=packet_file,
        packet_text=packet_text,
        raw_path=evaluation_file,
        relative_path=_EVALUATION_RELATIVE_PATH,
    )
    _bind_packet_source(
        packet_path=packet_file,
        packet_text=packet_text,
        raw_path=test_data_file,
        relative_path=_TEST_DATA_RELATIVE_PATH,
    )
    _bind_packet_source(
        packet_path=packet_file,
        packet_text=packet_text,
        raw_path=specs_file,
        relative_path=_SPECS_RELATIVE_PATH,
    )
    case_id = _packet_case_id(packet_text)
    if root.name != case_id:
        _fail(f"packet directory/case identity mismatch: {root.name} != {case_id}")
    try:
        test_data = json.loads(test_data_source)
    except json.JSONDecodeError as exc:
        raise AppWorldChecklistSemanticError(
            f"{case_id}: official test_data.json is malformed: {exc}"
        ) from exc
    try:
        specs = json.loads(specs_source)
    except json.JSONDecodeError as exc:
        raise AppWorldChecklistSemanticError(
            f"{case_id}: official specs.json is malformed: {exc}"
        ) from exc
    if not isinstance(specs, Mapping) or not isinstance(specs.get("instruction"), str):
        _fail(f"{case_id}: official specs instruction is invalid")
    semantics = _extract_evaluator_semantics(evaluation_source, test_data)
    registry_markers = [
        _require_nonempty_string(record.get("marker"), "registered-test marker")
        for record in semantics["registered_test_registry"]
    ]
    expected_registry = {
        "all_tests_marker": APPWORLD_ALL_TESTS_MARKER,
        "required_benchmark_success_text": appworld_benchmark_success_text(
            registry_markers
        ),
        "required_undecided_if_text": APPWORLD_UNDECIDED_TEXT,
        "required_undecided_if_rationale": APPWORLD_UNDECIDED_RATIONALE,
        "registered_tests": semantics["registered_test_registry"],
        "required_native": appworld_required_native_surface(
            instruction=specs["instruction"],
            registered_tests=semantics["registered_test_registry"],
        ),
    }
    if dict(_packet_registered_test_registry(packet_text)) != expected_registry:
        _fail(f"{case_id}: packet registered-test registry differs from evaluator/test_data")
    gap_payload = parse_packet_stronger_gap_registry(packet_text)
    gap_entry = _require_mapping(gap_payload.get("case"), "packet stronger-gap case")
    if gap_entry.get("case_unit_id") != case_id:
        _fail(f"{case_id}: packet stronger-gap case identity mismatch")
    if gap_entry.get("registered_test_registry_sha256") != sha256_object(expected_registry):
        _fail(f"{case_id}: packet stronger-gap/native-test registry hash mismatch")
    if (
        gap_entry.get("non_scoring_assignment_registry")
        != semantics["non_scoring_test_assignments"]
        or gap_entry.get("non_scoring_assignment_registry_sha256")
        != sha256_object(semantics["non_scoring_test_assignments"])
        or gap_entry.get("non_scoring_assignment_exclusion_status")
        != "excluded_from_native_and_stronger_scoring"
    ):
        _fail(f"{case_id}: packet non-scoring assignment registry differs from evaluator AST")
    payload = {
        "schema_version": PACKET_EVALUATOR_REPORT_SCHEMA,
        "status": "passed",
        "case_id": case_id,
        "case_packet_sha256": sha256_file(packet_file),
        "evaluation_sha256": sha256_file(evaluation_file),
        "test_data_sha256": sha256_file(test_data_file),
        "specs_sha256": sha256_file(specs_file),
        "stronger_gap_registry": {
            "registry_file_sha256": gap_payload["registry_sha256"],
            "entry_semantic_sha256": gap_entry["entry_semantic_sha256"],
            "source_basis_sha256": gap_entry["source_basis_sha256"],
            "registered_test_registry_sha256": gap_entry[
                "registered_test_registry_sha256"
            ],
            "non_scoring_assignment_registry_sha256": gap_entry[
                "non_scoring_assignment_registry_sha256"
            ],
            "non_scoring_assignment_exclusion_status": gap_entry[
                "non_scoring_assignment_exclusion_status"
            ],
            "gap_count": len(gap_entry["gaps"]),
            "markers": [gap["marker"] for gap in gap_entry["gaps"]],
        },
        **semantics,
    }
    return {**payload, "audit_semantic_sha256": sha256_object(payload)}


def validate_appworld_packet_checklist_semantics(
    *,
    case_packet_root: str | Path,
    checklist: Mapping[str, Any],
) -> dict[str, Any]:
    """Convenience wrapper using the canonical raw paths under a packet root."""

    root = Path(case_packet_root).expanduser().resolve()
    return validate_appworld_checklist_semantics(
        case_packet_path=root / "case_packet.md",
        evaluation_path=root / "raw_case" / _EVALUATION_RELATIVE_PATH,
        test_data_path=root / "raw_case" / _TEST_DATA_RELATIVE_PATH,
        checklist=checklist,
    )


__all__ = [
    "APPWORLD_ALL_TESTS_MARKER",
    "AppWorldChecklistSemanticError",
    "SCORING_METHODS",
    "SEMANTIC_REPORT_SCHEMA",
    "TEST_TRACKER_SUCCESS_EXPRESSION",
    "appworld_registered_test_marker",
    "derive_appworld_evaluator_semantics",
    "validate_appworld_checklist_semantics",
    "validate_appworld_packet_checklist_semantics",
]
