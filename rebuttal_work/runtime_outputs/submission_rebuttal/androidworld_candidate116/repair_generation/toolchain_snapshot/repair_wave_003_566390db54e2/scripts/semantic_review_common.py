#!/usr/bin/env python3
"""Shared fail-closed helpers for AndroidWorld semantic-review proposals.

The helpers deliberately distinguish a model's review *proposal* from the
human ``androidworld_checklist_review/v1`` record consumed by promotion.  No
function in this module writes the final review directory or authorizes a
contract/draft freeze.
"""

from __future__ import annotations

import copy
import ast
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml
from jsonschema import Draft202012Validator


EXPECTED_CASE_COUNT = 116
EXPECTED_PARALLELISM = 6
PROPOSAL_SCHEMA_VERSION = "androidworld_checklist_semantic_review_proposal/v1"
PRELOCK_SCHEMA_VERSION = "androidworld_semantic_review_prelock/v1"
CONFIG_SCHEMA_VERSION = "androidworld_semantic_review_config/v1"
RECEIPT_SCHEMA_VERSION = "androidworld_semantic_review_receipt/v1"
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
JSON_TOKEN_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_-]*)(?:\[([0-9]+)\])?")
LINE_SPAN_RE = re.compile(r"^(?:lines?\s*)?[Ll]([0-9]+)(?:\s*[-:]\s*[Ll]?([0-9]+))?$", re.I)
FENCED_JSON_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


class SemanticReviewError(RuntimeError):
    """Raised when a semantic-review invariant cannot be established."""


def find_work_root(source: Path | None = None) -> Path:
    """Find the candidate116 root from original or snapshotted scripts."""
    start = (source or Path(__file__)).resolve()
    for candidate in (start, *start.parents):
        if candidate.name == "androidworld_candidate116":
            return candidate
    raise SemanticReviewError(f"cannot locate androidworld_candidate116 above {start}")


WORK_ROOT = find_work_root()
REPO_ROOT = WORK_ROOT.parents[3]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def object_sha256(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def add_self_hash(payload: Mapping[str, Any], field: str) -> dict[str, Any]:
    result = copy.deepcopy(dict(payload))
    result.pop(field, None)
    result[field] = object_sha256(result)
    return result


def verify_self_hash(payload: Mapping[str, Any], field: str, label: str) -> None:
    claimed = payload.get(field)
    core = copy.deepcopy(dict(payload))
    core.pop(field, None)
    if not isinstance(claimed, str) or not HASH_RE.fullmatch(claimed):
        raise SemanticReviewError(f"{label} has no valid {field}")
    observed = object_sha256(core)
    if claimed != observed:
        raise SemanticReviewError(
            f"{label} self hash mismatch: claimed={claimed}, observed={observed}"
        )


def load_json(path: Path, label: str | None = None) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SemanticReviewError(f"cannot load {label or 'JSON'} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SemanticReviewError(f"{label or 'JSON'} must be an object: {path}")
    return value


def load_yaml_mapping(path: Path, label: str | None = None) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SemanticReviewError(f"cannot load {label or 'YAML'} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SemanticReviewError(f"{label or 'YAML'} must be an object: {path}")
    return value


def repo_relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def resolve_repo_path(raw: Any, *, inside_candidate: bool = False) -> Path:
    text = str(raw or "").strip()
    if not text:
        raise SemanticReviewError("empty repository path")
    path = Path(text)
    resolved = (path if path.is_absolute() else REPO_ROOT / path).resolve()
    try:
        resolved.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise SemanticReviewError(f"path escapes repository: {text}") from exc
    if inside_candidate:
        try:
            resolved.relative_to(WORK_ROOT.resolve())
        except ValueError as exc:
            raise SemanticReviewError(f"path is outside candidate116: {text}") from exc
    return resolved


def file_binding(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise SemanticReviewError(f"cannot bind missing file: {resolved}")
    return {
        "path": repo_relative(resolved),
        "sha256": sha256_file(resolved),
        "size_bytes": resolved.stat().st_size,
    }


def verify_file_binding(
    binding: Mapping[str, Any],
    label: str,
    *,
    inside_candidate: bool = True,
) -> Path:
    if not isinstance(binding, Mapping):
        raise SemanticReviewError(f"{label} binding is not an object")
    path = resolve_repo_path(binding.get("path"), inside_candidate=inside_candidate)
    if not path.is_file():
        raise SemanticReviewError(f"{label} is missing: {path}")
    observed_hash = sha256_file(path)
    observed_size = path.stat().st_size
    if binding.get("sha256") != observed_hash or binding.get("size_bytes") != observed_size:
        raise SemanticReviewError(
            f"{label} binding mismatch for {repo_relative(path)}: "
            f"expected {binding.get('sha256')}/{binding.get('size_bytes')}, "
            f"observed {observed_hash}/{observed_size}"
        )
    return path


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temporary)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temporary)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def schema_errors(instance: Any, schema: Mapping[str, Any]) -> list[str]:
    validator = Draft202012Validator(dict(schema))
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.absolute_path))
    return [
        f"{'.'.join(str(token) for token in error.absolute_path) or '<root>'}: {error.message}"
        for error in errors
    ]


def model_body_schema(proposal_schema: Mapping[str, Any]) -> dict[str, Any]:
    """Derive the exact Codex output schema from the proposal schema."""
    all_definitions = copy.deepcopy(dict(proposal_schema).get("$defs") or {})
    review_body = all_definitions.pop("ReviewBody", None)
    if not isinstance(review_body, dict):
        raise SemanticReviewError("proposal schema has no $defs.ReviewBody")

    def referenced_names(value: Any) -> set[str]:
        names: set[str] = set()
        if isinstance(value, Mapping):
            reference = value.get("$ref")
            if isinstance(reference, str) and reference.startswith("#/$defs/"):
                names.add(reference.removeprefix("#/$defs/"))
            for nested in value.values():
                names.update(referenced_names(nested))
        elif isinstance(value, list):
            for nested in value:
                names.update(referenced_names(nested))
        return names

    # Codex receives only ReviewBody.  Excluding unreachable proposal-only defs
    # also excludes their oneOf construct, keeping the enforced model schema in
    # the strict structured-output subset.
    needed = referenced_names(review_body)
    definitions: dict[str, Any] = {}
    while needed:
        name = sorted(needed)[0]
        needed.remove(name)
        if name in definitions:
            continue
        definition = all_definitions.get(name)
        if not isinstance(definition, dict):
            raise SemanticReviewError(f"ReviewBody references missing definition {name}")
        definitions[name] = definition
        needed.update(referenced_names(definition) - set(definitions))
    review_body["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    review_body["$id"] = "androidworld_checklist_semantic_review_body.schema.json"
    review_body["$defs"] = definitions
    Draft202012Validator.check_schema(review_body)
    return review_body


def _parse_embedded_files(packet_text: str) -> dict[str, dict[str, Any]]:
    """Parse full-packet file sections in one linear scan.

    A former all-file regular expression had pathological backtracking on the
    roughly megabyte-sized packets.  The packet builder emits an exact heading,
    a nearby opening fence, and an exact closing fence, so a line scanner is
    both stricter and bounded.
    """
    files: dict[str, dict[str, Any]] = {}
    lines = packet_text.splitlines()
    index = 0
    while index < len(lines):
        heading = re.fullmatch(r"### `([^`]+)`", lines[index].strip())
        if heading is None:
            index += 1
            continue
        path = heading.group(1)
        fence_index = index + 1
        while fence_index < min(index + 10, len(lines)) and not lines[fence_index].startswith("```"):
            if lines[fence_index].startswith("### ") or lines[fence_index].startswith("## "):
                break
            fence_index += 1
        if fence_index >= len(lines) or not lines[fence_index].startswith("```"):
            index += 1
            continue
        language = lines[fence_index][3:].strip()
        next_heading = fence_index + 1
        while next_heading < len(lines) and (
            re.fullmatch(r"### `([^`]+)`", lines[next_heading].strip()) is None
            and lines[next_heading].strip() != "## Raw Source Provenance"
        ):
            next_heading += 1
        # Embedded Python docstrings can themselves contain Markdown ```
        # examples.  The packet section's outer close is therefore the *last*
        # exact fence before the next file heading, not the first.
        closing_candidates = [
            position
            for position in range(fence_index + 1, next_heading)
            if lines[position].strip() == "```"
        ]
        if not closing_candidates:
            raise SemanticReviewError(f"unterminated embedded source fence for {path}")
        close_index = closing_candidates[-1]
        content = "\n".join(lines[fence_index + 1 : close_index]) + "\n"
        record: dict[str, Any] = {"language": language, "text": content}
        if language.casefold() == "json":
            try:
                record["json"] = json.loads(content)
            except json.JSONDecodeError:
                record["json"] = None
        files[path] = record
        index = next_heading
    return files


def _source_inventory(packet_text: str) -> set[str]:
    match = re.search(r"^## Source Inventory\s*$\n(.*?)(?=^## |\Z)", packet_text, re.M | re.S)
    if not match:
        return set()
    return set(re.findall(r"^- `([^`]+)`\s*$", match.group(1), re.M))


def parse_case_packet(packet_text: str) -> dict[str, Any]:
    """Parse either a compact JSON packet or a full embedded-source packet."""
    embedded = _parse_embedded_files(packet_text)
    inventory = _source_inventory(packet_text)
    canonical = embedded.get("derived/canonical_task_semantics.json", {}).get("json")
    packet_kind = "full" if isinstance(canonical, dict) else "compact"
    compact_root: dict[str, Any] | None = None
    if packet_kind == "compact":
        matches = FENCED_JSON_RE.findall(packet_text)
        objects: list[dict[str, Any]] = []
        for raw in matches:
            try:
                value = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                objects.append(value)
        if len(objects) != 1:
            raise SemanticReviewError(
                f"compact packet must contain exactly one JSON object, observed {len(objects)}"
            )
        compact_root = objects[0]
        canonical = compact_root
    assert isinstance(canonical, dict)

    if packet_kind == "full":
        identity = {
            "case_unit_id": canonical.get("case_unit_id"),
            "task_id": canonical.get("task_id") or canonical.get("case_unit_id"),
            "domain": "androidworld",
        }
        conflicts = list(canonical.get("metadata_conflicts") or [])
        canonical_support_path = "derived/canonical_task_semantics.json"
    else:
        identity = dict(canonical.get("identity") or {})
        conflicts = list(((canonical.get("source_context") or {}).get("metadata_conflicts") or []))
        canonical_support_path = "case_packet.md"
    return {
        "kind": packet_kind,
        "identity": identity,
        "canonical": canonical,
        "canonical_support_path": canonical_support_path,
        "metadata_conflicts": conflicts,
        "embedded_files": embedded,
        "source_inventory": inventory,
        "packet_text": packet_text,
    }


def resolve_json_path(root: Any, raw_path: str) -> tuple[bool, Any]:
    path = raw_path.strip()
    if path == "$":
        return True, root
    if not path.startswith("$."):
        return False, None
    current = root
    for raw_token in path[2:].split("."):
        match = JSON_TOKEN_RE.fullmatch(raw_token)
        if not match or not isinstance(current, Mapping) or match.group(1) not in current:
            return False, None
        current = current[match.group(1)]
        if match.group(2) is not None:
            index = int(match.group(2))
            if not isinstance(current, list) or index >= len(current):
                return False, None
            current = current[index]
    return True, current


def _line_span_resolves(text: str, locator: str) -> bool:
    match = LINE_SPAN_RE.fullmatch(locator.strip())
    if not match:
        return False
    start = int(match.group(1))
    end = int(match.group(2) or start)
    return 1 <= start <= end <= len(text.splitlines())


def _python_symbol_resolves(text: str, locator: str) -> bool:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    symbols: set[str] = set()

    def visit(body: list[ast.stmt], prefix: str = "") -> None:
        for node in body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                qualified = f"{prefix}.{node.name}" if prefix else node.name
                symbols.add(qualified)
                visit(node.body, qualified)

    visit(tree.body)
    normalized = locator.strip().removesuffix("()")
    return any(normalized == symbol or normalized.endswith(f".{symbol}") for symbol in symbols)


def resolve_packet_pointer(pointer: str, packet: Mapping[str, Any], *, review_level: bool) -> bool:
    """Resolve review JSON support or a raw checklist source pointer.

    Review-level support is deliberately restricted to canonical JSON.  Raw
    checklist pointers may additionally reference any exact Source Inventory
    path using a symbol or line span, matching the drafting guardrail contract.
    """
    path, separator, locator = str(pointer).strip().replace("\\", "/").partition("::")
    if separator != "::" or not path or not locator:
        return False
    canonical_path = str(packet["canonical_support_path"])
    if review_level:
        if path != canonical_path or not locator.startswith("$"):
            return False
        return resolve_json_path(packet["canonical"], locator)[0]

    if path == "case_packet.md":
        if locator.startswith("$") and packet["kind"] == "compact":
            return resolve_json_path(packet["canonical"], locator)[0]
        return _line_span_resolves(str(packet["packet_text"]), locator)

    embedded = dict(packet.get("embedded_files") or {})
    inventory = set(packet.get("source_inventory") or set())
    if path not in inventory or path not in embedded:
        return False
    record = embedded[path]
    if locator.startswith("$"):
        return isinstance(record.get("json"), (dict, list)) and resolve_json_path(
            record.get("json"), locator
        )[0]
    if _line_span_resolves(str(record.get("text") or ""), locator):
        return True
    text = str(record.get("text") or "")
    language = str(record.get("language") or "").casefold()
    if language in {"python", "py"} or path.endswith(".py"):
        return _python_symbol_resolves(text, locator)
    # Non-Python embedded files have no shared symbol grammar.  Require the
    # exact locator text rather than accepting a basename or fuzzy substring.
    return bool(locator.strip()) and locator.strip() in text


def iter_support_entries(value: Any, json_path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            child_path = f"{json_path}.{key}"
            if key == "support" and isinstance(nested, list):
                for index, pointer in enumerate(nested):
                    yield f"{child_path}[{index}]", str(pointer)
            else:
                yield from iter_support_entries(nested, child_path)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from iter_support_entries(nested, f"{json_path}[{index}]")


def iter_review_packet_support(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if key == "packet_support" and isinstance(nested, list):
                for pointer in nested:
                    yield str(pointer)
            else:
                yield from iter_review_packet_support(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from iter_review_packet_support(nested)


def raw_stronger_ids(checklist: Mapping[str, Any]) -> set[str]:
    rows = ((checklist.get("stronger") or {}).get("additional_conditions") or [])
    return {
        str(row.get("id"))
        for row in rows
        if isinstance(row, Mapping) and str(row.get("id") or "").strip()
    }


def validate_review_body(
    body: Mapping[str, Any],
    *,
    body_schema: Mapping[str, Any],
    checklist: Mapping[str, Any],
    checklist_schema: Mapping[str, Any],
    packet: Mapping[str, Any],
) -> list[str]:
    """Validate structural and deterministic cross-field proposal invariants."""
    problems = [f"body_schema: {item}" for item in schema_errors(body, body_schema)]
    if problems:
        return problems

    expected_identity = dict(packet.get("identity") or {})
    if (
        checklist.get("case_unit_id") != expected_identity.get("case_unit_id")
        or checklist.get("task_id") != expected_identity.get("task_id")
        or checklist.get("domain") != "androidworld"
    ):
        problems.append("raw checklist identity does not match the prelocked packet")

    for pointer in iter_review_packet_support(body):
        if not resolve_packet_pointer(pointer, packet, review_level=True):
            problems.append(f"review packet_support does not resolve canonically: {pointer}")

    checks = dict(body.get("checks") or {})
    check_statuses = [str((checks.get(name) or {}).get("status")) for name in checks]

    metadata = dict(checks.get("metadata_conflict_disposition") or {})
    expected_conflicts = bool(packet.get("metadata_conflicts"))
    if metadata.get("conflicts_present") is not expected_conflicts:
        problems.append(
            "metadata_conflict_disposition.conflicts_present differs from the packet"
        )

    support_entries = list(iter_support_entries(checklist))
    audit = dict(body.get("support_pointer_audit") or {})
    audit_rows = list(audit.get("pointers") or [])
    expected_pairs = Counter(support_entries)
    observed_pairs = Counter(
        (str(row.get("checklist_json_path")), str(row.get("pointer_value")))
        for row in audit_rows
        if isinstance(row, Mapping)
    )
    if observed_pairs != expected_pairs:
        missing = list((expected_pairs - observed_pairs).elements())
        extra = list((observed_pairs - expected_pairs).elements())
        problems.append(f"support audit is not one-for-one; missing={missing}, extra={extra}")

    computed_invalid: set[str] = set()
    computed_unsupported: set[str] = set()
    for row in audit_rows:
        if not isinstance(row, Mapping):
            continue
        pointer = str(row.get("pointer_value") or "")
        resolves = resolve_packet_pointer(pointer, packet, review_level=False)
        if row.get("resolves") is not resolves:
            problems.append(f"support audit resolution claim is wrong: {pointer}")
        if not resolves:
            computed_invalid.add(pointer)
        if row.get("supports_claim") is False:
            computed_unsupported.add(pointer)
    if set(map(str, audit.get("invalid_pointer_values") or [])) != computed_invalid:
        problems.append("support audit invalid_pointer_values is inconsistent with pointer rows")
    if set(map(str, audit.get("unsupported_pointer_values") or [])) != computed_unsupported:
        problems.append("support audit unsupported_pointer_values is inconsistent with pointer rows")
    audit_should_pass = (
        not audit.get("missing_checklist_support_paths")
        and not computed_invalid
        and not computed_unsupported
        and len(audit_rows) == len(support_entries)
        and all(
            row.get("resolves") is True and row.get("supports_claim") is True
            for row in audit_rows
            if isinstance(row, Mapping)
        )
    )
    if (audit.get("status") == "pass") is not audit_should_pass:
        problems.append("support_pointer_audit status disagrees with its exhaustive rows")

    matrix = dict(body.get("goal_evaluator_matrix") or {})
    requirements = list(matrix.get("requirements") or [])
    requirement_ids = [str(row.get("requirement_id")) for row in requirements if isinstance(row, Mapping)]
    if len(requirement_ids) != len(set(requirement_ids)):
        problems.append("goal_evaluator_matrix requirement ids are not unique")
    checklist_stronger_ids = raw_stronger_ids(checklist)
    referenced_stronger: set[str] = set()
    failed_requirement_ids: set[str] = set()
    for row in requirements:
        if not isinstance(row, Mapping):
            continue
        row_id = str(row.get("requirement_id") or "")
        condition_ids = set(map(str, row.get("raw_stronger_condition_ids") or []))
        referenced_stronger.update(condition_ids)
        unknown = condition_ids - checklist_stronger_ids
        if unknown:
            problems.append(f"matrix row {row_id} cites unknown raw stronger ids: {sorted(unknown)}")
        coverage = row.get("native_evaluator_coverage")
        if row.get("requirement_type") == "goal_atom" and coverage in {"partial", "none"}:
            if row.get("stronger_required") is not True:
                problems.append(f"matrix row {row_id} leaves a goal/evaluator gap unmarked")
        if row.get("stronger_required") is True and not condition_ids:
            problems.append(f"matrix row {row_id} requires stronger coverage but cites no raw condition")
        if row.get("status") == "fail":
            failed_requirement_ids.add(row_id)
    unreferenced = checklist_stronger_ids - referenced_stronger
    if unreferenced:
        problems.append(f"raw stronger conditions are absent from the matrix: {sorted(unreferenced)}")
    if set(map(str, matrix.get("uncovered_requirement_ids") or [])) != failed_requirement_ids:
        problems.append("matrix uncovered_requirement_ids must equal its failed row ids")
    matrix_should_pass = not failed_requirement_ids
    if (matrix.get("status") == "pass") is not matrix_should_pass:
        problems.append("goal_evaluator_matrix status disagrees with its requirement rows")

    runner = dict(checks.get("runner_score_semantics") or {})
    raw_score_text = str(runner.get("raw_score_semantics") or "")
    done_text = str(runner.get("done_gate_semantics") or "")
    threshold_text = str(runner.get("display_threshold_semantics") or "")
    if not re.search(r"(?i)(?:is_successful|raw\s*(?:score|result))", raw_score_text):
        problems.append("runner raw-score account does not identify task.is_successful/raw score")
    if not re.search(r"(?i)\bdone\b", done_text) or not re.search(
        r"(?i)(?:0(?:\.0)?|zero|force|gate)", done_text
    ):
        problems.append("runner done-gate account does not state the done/zero gate")
    if not re.search(
        r"(?i)(?:>\s*0?\.5|strictly\s+(?:greater|above)|above\s+0?\.5)", threshold_text
    ):
        problems.append("runner display-threshold account does not state strict > 0.5")

    failure = dict(checks.get("fail_and_undecided") or {})
    if failure.get("status") == "pass" and failure.get(
        "undecided_only_for_missing_or_unusable_evidence"
    ) is not True:
        problems.append("passing fail/undecided check must reserve undecided for unusable evidence")
    artifacts = dict(checks.get("decisive_post_run_artifacts") or {})
    if artifacts.get("status") == "pass":
        if artifacts.get("source_code_not_treated_as_run_evidence") is not True:
            problems.append("passing artifact check treats source material as run evidence")
        if any(
            row.get("post_run_available") is not True
            or row.get("checklist_coverage") != "complete"
            for row in artifacts.get("artifacts") or []
            if isinstance(row, Mapping)
        ):
            problems.append("passing artifact check contains unavailable or incompletely covered evidence")

    corrected = body.get("corrected_checklist")
    correction_summary = list(body.get("correction_summary") or [])
    if corrected is not None:
        if not isinstance(corrected, Mapping):
            problems.append("corrected_checklist is neither null nor an object")
        else:
            problems.extend(
                f"corrected_checklist_schema: {item}"
                for item in schema_errors(corrected, checklist_schema)
            )
            if (
                corrected.get("case_unit_id") != expected_identity.get("case_unit_id")
                or corrected.get("task_id") != expected_identity.get("task_id")
                or corrected.get("domain") != "androidworld"
            ):
                problems.append("corrected_checklist identity differs from the packet")
            for _, pointer in iter_support_entries(corrected):
                if not resolve_packet_pointer(pointer, packet, review_level=False):
                    problems.append(f"corrected checklist support does not resolve: {pointer}")
            if not correction_summary:
                problems.append("a corrected_checklist requires a non-empty correction_summary")
    elif correction_summary:
        problems.append("correction_summary must be empty when corrected_checklist is null")

    all_gate_pass = (
        checks
        and all(status == "pass" for status in check_statuses)
        and matrix.get("status") == "pass"
        and not failed_requirement_ids
        and audit.get("status") == "pass"
        and not audit.get("missing_checklist_support_paths")
        and not computed_invalid
        and not computed_unsupported
        and all(row.get("supports_claim") is True for row in audit_rows if isinstance(row, Mapping))
    )
    issues = list(body.get("issues") or [])
    issue_checks = {
        str(item.get("check")) for item in issues if isinstance(item, Mapping)
    }
    for check_name, finding in checks.items():
        if isinstance(finding, Mapping) and finding.get("status") == "fail" and check_name not in issue_checks:
            problems.append(f"failed check {check_name} has no corresponding issue")
    if matrix.get("status") == "fail" and "goal_evaluator_matrix" not in issue_checks:
        problems.append("failed goal_evaluator_matrix has no corresponding issue")
    if audit.get("status") == "fail" and "support_pointer_audit" not in issue_checks:
        problems.append("failed support_pointer_audit has no corresponding issue")
    status = body.get("proposal_status")
    if status == "accepted":
        if not all_gate_pass:
            problems.append("accepted proposal has a failed or incomplete semantic gate")
        if issues:
            problems.append("accepted proposal must have no issues")
        if corrected is not None or correction_summary:
            problems.append("accepted proposal cannot include a correction")
    elif status == "rejected":
        if all_gate_pass and not issues:
            problems.append("rejected proposal must identify at least one failed gate or issue")
        if not issues:
            problems.append("rejected proposal must contain at least one concrete issue")
        elif not any(
            isinstance(item, Mapping) and item.get("severity") == "error" for item in issues
        ):
            problems.append("rejected proposal must contain at least one error-severity issue")
    return problems


def build_proposal(
    *,
    case_id: str,
    task_id: str,
    input_bindings: Mapping[str, Any],
    review_configuration: Mapping[str, Any],
    review_body: Mapping[str, Any],
) -> dict[str, Any]:
    proposal = {
        "schema_version": PROPOSAL_SCHEMA_VERSION,
        "case_unit_id": case_id,
        "domain": "androidworld",
        "task_id": task_id,
        "review_authority": "independent_model_proposal_only",
        "promotion_authorized": False,
        "input_bindings": copy.deepcopy(dict(input_bindings)),
        "review_configuration": copy.deepcopy(dict(review_configuration)),
        "review": copy.deepcopy(dict(review_body)),
    }
    return add_self_hash(proposal, "proposal_sha256")


def validate_proposal(
    proposal: Mapping[str, Any],
    *,
    proposal_schema: Mapping[str, Any],
    body_schema: Mapping[str, Any],
    checklist: Mapping[str, Any],
    checklist_schema: Mapping[str, Any],
    packet: Mapping[str, Any],
) -> list[str]:
    problems = [f"proposal_schema: {item}" for item in schema_errors(proposal, proposal_schema)]
    if not problems:
        try:
            verify_self_hash(proposal, "proposal_sha256", "semantic-review proposal")
        except SemanticReviewError as exc:
            problems.append(str(exc))
    review = proposal.get("review")
    if isinstance(review, Mapping):
        problems.extend(
            validate_review_body(
                review,
                body_schema=body_schema,
                checklist=checklist,
                checklist_schema=checklist_schema,
                packet=packet,
            )
        )
    else:
        problems.append("proposal review body is missing")
    return problems


def load_jsonl_events(raw: str) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    malformed: list[str] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            malformed.append(line)
            continue
        if isinstance(value, dict):
            events.append(value)
        else:
            malformed.append(line)
    return events, malformed


def reasoning_fragments(events: Iterable[Mapping[str, Any]]) -> list[str]:
    fragments: list[str] = []
    for event in events:
        item = event.get("item")
        if not isinstance(item, Mapping) or item.get("type") != "reasoning":
            continue
        for key in ("text", "summary", "content"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                fragments.append(value.strip())
    return fragments


def codex_usage(events: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    completed: Mapping[str, Any] = {}
    for event in events:
        if event.get("type") == "turn.completed":
            completed = event
    usage = completed.get("usage") if isinstance(completed.get("usage"), Mapping) else {}
    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": int(usage.get("cached_input_tokens", 0) or 0),
        "output_tokens": output_tokens,
        "reasoning_output_tokens": int(usage.get("reasoning_output_tokens", 0) or 0),
        "total_tokens": int(usage.get("total_tokens", input_tokens + output_tokens) or 0),
    }


def event_response_id(events: Iterable[Mapping[str, Any]]) -> str | None:
    for event in events:
        if event.get("type") == "thread.started" and event.get("thread_id"):
            return str(event["thread_id"])
    return None


def require_iso8601(value: Any, label: str) -> str:
    text = str(value or "").strip()
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SemanticReviewError(f"{label} is not ISO-8601: {text}") from exc
    return text
