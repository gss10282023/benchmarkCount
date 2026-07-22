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
EXPECTED_MODEL = "gpt-5.6-sol"
EXPECTED_REASONING_EFFORT = "xhigh"
EXACT_CODEX_LOGIN_STATUS = "Logged in using ChatGPT"
PROPOSAL_SCHEMA_VERSION = "androidworld_checklist_semantic_review_proposal/v1"
PRELOCK_SCHEMA_VERSION = "androidworld_semantic_review_prelock/v1"
CONFIG_SCHEMA_VERSION = "androidworld_semantic_review_config/v1"
RECEIPT_SCHEMA_VERSION = "androidworld_semantic_review_receipt/v1"
ISSUE_HISTORY_SCHEMA_VERSION = "androidworld_effective_checklist_issue_history/v1"
CONCURRENCY_EVENT_SCHEMA_VERSION = "androidworld_semantic_review_concurrency_event/v1"
CONCURRENCY_AUDIT_SCHEMA_VERSION = "androidworld_semantic_review_concurrency_audit/v1"
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


def canonical_runtime_tree(
    root: Path, *, excluded_directory_names: frozenset[str] = frozenset()
) -> dict[str, Any]:
    """Return the complete non-following byte tree used by runtime gates."""
    root = Path(os.path.abspath(root))
    if not root.is_dir():
        raise SemanticReviewError(f"runtime tree root is missing: {root}")
    rows: list[dict[str, Any]] = []

    def visit(directory: Path, relative_directory: Path) -> None:
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as exc:
            raise SemanticReviewError(f"cannot enumerate runtime tree {directory}: {exc}") from exc
        for entry in entries:
            relative = relative_directory / entry.name
            absolute = Path(entry.path)
            if entry.name in excluded_directory_names and entry.is_dir(follow_symlinks=False):
                continue
            metadata = absolute.lstat()
            portable = relative.as_posix()
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
                raise SemanticReviewError(f"unsupported runtime special file: {absolute}")

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


def verify_python_runtime_trees(runtime: Mapping[str, Any]) -> None:
    for root, tree in (runtime.get("site_packages_trees") or {}).items():
        if canonical_runtime_tree(Path(root)) != tree:
            raise SemanticReviewError(f"site-packages runtime tree changed: {root}")
    for root, record in (runtime.get("stdlib_platstdlib_trees") or {}).items():
        if canonical_runtime_tree(
            Path(root), excluded_directory_names=frozenset({"site-packages", "dist-packages"})
        ) != (record or {}).get("tree"):
            raise SemanticReviewError(f"stdlib runtime tree changed: {root}")
    for item in runtime.get("extra_sys_path_entries") or []:
        if not isinstance(item, Mapping):
            raise SemanticReviewError("runtime extra sys.path row is malformed")
        path = Path(str(item.get("path") or ""))
        kind = item.get("kind")
        if kind == "regular_file":
            if (
                not path.is_file()
                or path.stat().st_size != item.get("size_bytes")
                or sha256_file(path) != item.get("sha256")
            ):
                raise SemanticReviewError(f"runtime sys.path file changed: {path}")
        elif kind == "directory_tree" and canonical_runtime_tree(path) != item.get("tree"):
            raise SemanticReviewError(f"runtime sys.path directory changed: {path}")
        elif kind == "expected_absent" and (path.exists() or path.is_symlink()):
            raise SemanticReviewError(f"runtime expected-absent path appeared: {path}")


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


def validate_issue_history_audit(
    audit: Mapping[str, Any],
    *,
    issue_history: Mapping[str, Any],
    checklist: Mapping[str, Any],
) -> tuple[list[str], bool]:
    """Validate one-for-one disposition of every frozen historical issue."""
    problems: list[str] = []
    historical_issues = list(issue_history.get("issues") or [])
    expected_pairs: Counter[tuple[str, str]] = Counter()
    for item in historical_issues:
        if not isinstance(item, Mapping):
            problems.append("issue history contains a non-object issue")
            continue
        issue_id = str(item.get("issue_id") or "")
        issue_sha = str(item.get("issue_sha256") or "")
        if not issue_id or not HASH_RE.fullmatch(issue_sha):
            problems.append("issue history contains an invalid issue id/hash")
            continue
        expected_pairs[(issue_id, issue_sha)] += 1
    rows = list(audit.get("resolutions") or [])
    observed_pairs = Counter(
        (str(item.get("issue_id") or ""), str(item.get("issue_sha256") or ""))
        for item in rows
        if isinstance(item, Mapping)
    )
    if observed_pairs != expected_pairs:
        missing = list((expected_pairs - observed_pairs).elements())
        extra = list((observed_pairs - expected_pairs).elements())
        problems.append(f"issue history audit is not one-for-one; missing={missing}, extra={extra}")
    if audit.get("historical_issue_count") != len(historical_issues):
        problems.append("issue history audit count differs from frozen issue history")
    unresolved_ids: set[str] = set()
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        issue_id = str(item.get("issue_id") or "")
        for pointer in item.get("checklist_support") or []:
            if not resolve_json_path(checklist, str(pointer))[0]:
                problems.append(
                    f"issue history checklist support does not resolve for {issue_id}: {pointer}"
                )
        if item.get("status") == "unresolved":
            unresolved_ids.add(issue_id)
    if set(map(str, audit.get("unresolved_issue_ids") or [])) != unresolved_ids:
        problems.append("issue history unresolved ids differ from resolution rows")
    should_pass = (
        observed_pairs == expected_pairs
        and audit.get("historical_issue_count") == len(historical_issues)
        and not unresolved_ids
        and all(
            isinstance(item, Mapping) and item.get("status") == "resolved" for item in rows
        )
    )
    if (audit.get("status") == "pass") is not should_pass:
        problems.append("issue_history_audit status disagrees with its exhaustive rows")
    return problems, should_pass


def validate_review_body(
    body: Mapping[str, Any],
    *,
    body_schema: Mapping[str, Any],
    checklist: Mapping[str, Any],
    checklist_schema: Mapping[str, Any],
    packet: Mapping[str, Any],
    issue_history: Mapping[str, Any],
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

    history_audit = dict(body.get("issue_history_audit") or {})
    history_problems, history_should_pass = validate_issue_history_audit(
        history_audit,
        issue_history=issue_history,
        checklist=checklist,
    )
    problems.extend(history_problems)

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
        and history_audit.get("status") == "pass"
        and history_should_pass
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
    if history_audit.get("status") == "fail" and "issue_history_audit" not in issue_checks:
        problems.append("failed issue_history_audit has no corresponding issue")
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
    issue_history: Mapping[str, Any],
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
                issue_history=issue_history,
            )
        )
    else:
        problems.append("proposal review body is missing")
    return problems


def verify_issue_history(value: Mapping[str, Any], *, case_id: str, rank: int) -> None:
    """Verify one normalized, self-hashed historical-issue input."""
    if (
        value.get("schema_version") != ISSUE_HISTORY_SCHEMA_VERSION
        or value.get("case_unit_id") != case_id
        or value.get("task_id") != case_id
        or value.get("selection_rank") != rank
        or value.get("disposition") not in {"repair", "retain"}
    ):
        raise SemanticReviewError(f"{case_id} issue-history identity/disposition is invalid")
    verify_self_hash(value, "issue_history_sha256", f"{case_id} issue history")
    issues = list(value.get("issues") or [])
    if value.get("issue_count") != len(issues) or value.get("issues_sha256") != object_sha256(issues):
        raise SemanticReviewError(f"{case_id} issue-history count/hash differs")
    ids: list[str] = []
    for index, issue in enumerate(issues):
        if not isinstance(issue, Mapping):
            raise SemanticReviewError(f"{case_id} issue-history row {index} is not an object")
        core = dict(issue)
        claimed = core.pop("issue_sha256", None)
        issue_id = str(issue.get("issue_id") or "")
        if not issue_id or claimed != object_sha256(core):
            raise SemanticReviewError(f"{case_id} issue-history row {index} hash differs")
        ids.append(issue_id)
    if len(ids) != len(set(ids)):
        raise SemanticReviewError(f"{case_id} issue-history issue ids are duplicated")
    if (value.get("disposition") == "retain") is not (len(issues) == 0):
        raise SemanticReviewError(f"{case_id} issue-history disposition/count is inconsistent")
    sources = value.get("source_bindings")
    if not isinstance(sources, Mapping) or not sources:
        raise SemanticReviewError(f"{case_id} issue-history source bindings are missing")
    for name, binding in sources.items():
        verify_file_binding(binding, f"{case_id} issue-history source {name}", inside_candidate=True)


def verify_semantic_concurrency_evidence(
    *,
    events_path: Path,
    audit_path: Path,
    expected_case_order: list[str],
    expected_prelock_sha256: str,
) -> dict[str, Any]:
    """Recompute exact-six process-lifecycle evidence from chained JSONL rows."""
    try:
        raw_lines = events_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SemanticReviewError(f"cannot read concurrency events: {exc}") from exc
    if not raw_lines:
        raise SemanticReviewError("semantic-review concurrency event stream is empty")
    active: dict[tuple[str, int], int] = {}
    started_cases: set[str] = set()
    previous_hash: str | None = None
    peak = 0
    start_count = 0
    stop_count = 0
    for sequence, raw in enumerate(raw_lines):
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SemanticReviewError(f"concurrency event {sequence} is malformed: {exc}") from exc
        if not isinstance(event, dict):
            raise SemanticReviewError(f"concurrency event {sequence} is not an object")
        verify_self_hash(event, "event_sha256", f"concurrency event {sequence}")
        if (
            event.get("schema_version") != CONCURRENCY_EVENT_SCHEMA_VERSION
            or event.get("sequence") != sequence
            or event.get("previous_event_sha256") != previous_hash
            or event.get("prelock_sha256") != expected_prelock_sha256
        ):
            raise SemanticReviewError(f"concurrency event {sequence} chain/identity differs")
        case_id = str(event.get("case_unit_id") or "")
        attempt_index = event.get("attempt_index")
        pid = event.get("pid")
        if (
            case_id not in set(expected_case_order)
            or not isinstance(attempt_index, int)
            or attempt_index <= 0
            or not isinstance(pid, int)
            or pid <= 0
        ):
            raise SemanticReviewError(f"concurrency event {sequence} process identity is invalid")
        key = (case_id, attempt_index)
        kind = event.get("event")
        if kind == "start":
            if key in active:
                raise SemanticReviewError(f"duplicate concurrency start for {key}")
            active[key] = pid
            started_cases.add(case_id)
            start_count += 1
        elif kind == "stop":
            if active.get(key) != pid:
                raise SemanticReviewError(f"unmatched concurrency stop for {key}")
            del active[key]
            stop_count += 1
        else:
            raise SemanticReviewError(f"concurrency event {sequence} has invalid kind")
        observed_active = [
            {"case_unit_id": item[0], "attempt_index": item[1], "pid": active[item]}
            for item in sorted(active)
        ]
        if (
            event.get("active") != observed_active
            or event.get("active_count") != len(observed_active)
            or len(observed_active) > EXPECTED_PARALLELISM
        ):
            raise SemanticReviewError(f"concurrency event {sequence} active state differs")
        observation = event.get("process_observation")
        if kind == "start":
            expected_observed_pids = (
                sorted(item["pid"] for item in observed_active)
                if len(observed_active) == EXPECTED_PARALLELISM
                else []
            )
            if not isinstance(observation, list) or [
                row.get("pid") for row in observation if isinstance(row, Mapping)
            ] != expected_observed_pids or any(
                not isinstance(row, Mapping)
                or row.get("pgid") != row.get("pid")
                or row.get("command_is_codex_exec") is not True
                or not HASH_RE.fullmatch(str(row.get("command_sha256") or ""))
                for row in observation
            ):
                raise SemanticReviewError(
                    f"concurrency event {sequence} lacks live /bin/ps Codex-exec proof"
                )
        elif observation != []:
            raise SemanticReviewError(
                f"concurrency stop event {sequence} must not claim a live-process sample"
            )
        peak = max(peak, len(observed_active))
        previous_hash = event["event_sha256"]
    if active:
        raise SemanticReviewError("semantic-review concurrency stream ends with active processes")
    if started_cases != set(expected_case_order):
        raise SemanticReviewError("concurrency evidence does not cover exact 116-case universe")
    if peak != EXPECTED_PARALLELISM or start_count != stop_count:
        raise SemanticReviewError("concurrency evidence does not prove an exact six-way peak")
    audit = load_json(audit_path, "semantic-review concurrency audit")
    verify_self_hash(audit, "audit_sha256", "semantic-review concurrency audit")
    expected = {
        "schema_version": CONCURRENCY_AUDIT_SCHEMA_VERSION,
        "status": "pass",
        "configured_workers": EXPECTED_PARALLELISM,
        "observed_peak_active_processes": EXPECTED_PARALLELISM,
        "event_count": len(raw_lines),
        "process_start_count": start_count,
        "process_stop_count": stop_count,
        "covered_case_count": EXPECTED_CASE_COUNT,
        "covered_cases": expected_case_order,
        "final_event_sha256": previous_hash,
        "prelock_sha256": expected_prelock_sha256,
    }
    for key, wanted in expected.items():
        if audit.get(key) != wanted:
            raise SemanticReviewError(
                f"semantic-review concurrency audit {key}={audit.get(key)!r}, expected {wanted!r}"
            )
    observer = audit.get("process_observer")
    if not isinstance(observer, Mapping):
        raise SemanticReviewError("semantic-review process observer binding is missing")
    observer_path = Path(str(observer.get("invocation_path") or ""))
    observer_resolved = Path(str(observer.get("resolved_path") or ""))
    if (
        not observer_path.is_file()
        or observer_path.resolve(strict=True) != observer_resolved
        or sha256_file(observer_resolved) != observer.get("sha256")
    ):
        raise SemanticReviewError("semantic-review process observer bytes differ")
    bound_events = verify_file_binding(
        audit.get("events"), "semantic-review concurrency events", inside_candidate=True
    )
    if bound_events != events_path.resolve():
        raise SemanticReviewError("semantic-review concurrency audit binds other events")
    return {
        "schema_version": "androidworld_semantic_review_concurrency_evidence/v1",
        "events": file_binding(events_path),
        "audit": file_binding(audit_path) | {"audit_sha256": audit["audit_sha256"]},
        "configured_workers": EXPECTED_PARALLELISM,
        "observed_peak_active_processes": peak,
        "covered_case_count": len(started_cases),
        "final_event_sha256": previous_hash,
    }


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
