#!/usr/bin/env python3
"""Fail-closed shared primitives for independent candidate116 semantic review v7.

This module is deliberately separate from the historical semantic-review pipeline.
It never calls a model and never writes canonical drafts, contracts, or freeze state.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml
from jsonschema import Draft202012Validator


CASE_COUNT = 116
PARALLELISM = 6
MODEL = "gpt-5.6-sol"
REASONING_EFFORT = "xhigh"
CODEX_VERSION = "codex-cli 0.144.4"
CODEX_BINARY_SHA256 = "3302acbda5f53de1a71ebdb0c0f2aae0d47f9324aa9fb6b4e78a47014fd51c7d"
CODEX_LOGIN_STATUS = "Logged in using ChatGPT"
BODY_SCHEMA = "androidworld_candidate116_semantic_review_v7_body/v1"
PRELOCK_SCHEMA = "androidworld_candidate116_semantic_review_v7_prelock/v1"
CONFIG_SCHEMA = "androidworld_candidate116_semantic_review_v7_config/v1"
RECEIPT_SCHEMA = "androidworld_candidate116_semantic_review_v7_receipt/v1"
VALIDATION_SCHEMA = "androidworld_candidate116_semantic_review_v7_validation/v1"

DIMENSION_IDS = (
    "identity_goal_generator",
    "parameter_schema_generator",
    "initialize_task",
    "success_evaluator",
    "evaluator_helpers",
    "runner_environment_layer",
    "runner_task_layer",
    "runner_evaluation_layer",
    "native_completeness_and_accuracy",
    "support_material_entailment",
    "metadata_runtime_conflicts",
    "stronger_necessity_measurability_retention",
    "fail_undecided_semantics",
    "no_omission_or_hallucination",
)

HASH_RE = re.compile(r"^[0-9a-f]{64}$")
CASE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,127}$")
RAW_PATH_RE = re.compile(r"^official/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$")
FINDING_RE = re.compile(r"^F[0-9]{3}$")
GENERIC_ASSESSMENTS = frozenset(
    {
        "checked and correct",
        "all good",
        "looks correct",
        "verified against source",
        "passes review",
        "no issues found",
    }
)


class SemanticReviewV7Error(RuntimeError):
    """Raised when a v7 semantic-review invariant cannot be proven."""


def find_candidate_root(source: Path | None = None) -> Path:
    start = (source or Path(__file__)).resolve()
    for candidate in (start, *start.parents):
        if candidate.name == "androidworld_candidate116":
            return candidate
    raise SemanticReviewV7Error(
        f"cannot locate androidworld_candidate116 above {start}"
    )


CANDIDATE_ROOT = find_candidate_root()
REPOSITORY_ROOT = CANDIDATE_ROOT.parents[3]


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_exact_int(
    value: Any,
    *,
    expected: int | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
) -> bool:
    """Reject bool-as-int coercion for every persisted numeric invariant."""

    if type(value) is not int:
        return False
    if expected is not None and value != expected:
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def add_self_hash(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    result = copy.deepcopy(dict(value))
    result.pop(field, None)
    result[field] = canonical_sha256(result)
    return result


def verify_self_hash(value: Mapping[str, Any], field: str, label: str) -> None:
    claimed = value.get(field)
    core = copy.deepcopy(dict(value))
    core.pop(field, None)
    if not isinstance(claimed, str) or not HASH_RE.fullmatch(claimed):
        raise SemanticReviewV7Error(f"{label} lacks a valid {field}")
    observed = canonical_sha256(core)
    if claimed != observed:
        raise SemanticReviewV7Error(
            f"{label} self-hash mismatch: claimed={claimed}, observed={observed}"
        )


def verify_actual_frozen_draft_capacity_row(
    row: Mapping[str, Any],
    *,
    label: str,
    max_staged_input_tokens: int,
    max_output_reserve_tokens: int,
    effective_context_limit: int,
    max_checklist_reader_tokens: int,
    max_checklist_reader_bytes: int,
    protocol_reserve_tokens: int,
) -> None:
    """Recompute both context gates from exact persisted integer components."""

    verify_self_hash(row, "capacity_row_sha256", label)
    integer_fields = (
        "actual_frozen_draft_size_bytes",
        "actual_frozen_draft_o200k_tokens",
        "frozen_checklist_yaml_size_bytes",
        "frozen_checklist_yaml_o200k_tokens",
        "prompt_o200k_tokens",
        "packet_reader_output_o200k_tokens",
        "checklist_reader_output_o200k_tokens",
        "checklist_reader_output_size_bytes",
        "max_checklist_reader_output_size_bytes",
        "max_checklist_reader_output_o200k_tokens_hard",
        "base_without_checklist_o200k_tokens",
        "max_checklist_o200k_tokens_by_210000_input_gate",
        "max_checklist_o200k_tokens_by_258400_total_gate",
        "effective_max_checklist_reader_output_o200k_tokens",
        "protocol_reserve_o200k_tokens",
        "staged_input_o200k_tokens",
        "max_staged_input_o200k_tokens_gate",
        "staged_input_gate_headroom_o200k_tokens",
        "reserved_output_o200k_tokens",
        "effective_total_with_output_reserve_o200k_tokens",
        "effective_context_limit_o200k_tokens",
        "remaining_context_margin_o200k_tokens",
    )
    if any(not is_exact_int(row.get(field), minimum=0) for field in integer_fields):
        raise SemanticReviewV7Error(
            f"{label} contains a missing/negative/bool numeric capacity field"
        )
    actual_binding = row.get("actual_frozen_draft")
    if not isinstance(actual_binding, Mapping):
        raise SemanticReviewV7Error(f"{label} lacks actual frozen draft binding")
    actual_path = verify_regular_file_binding(actual_binding, f"{label} frozen draft")
    actual_bytes = actual_path.read_bytes()
    actual_text = actual_bytes.decode("utf-8")
    base = row["base_without_checklist_o200k_tokens"]
    checklist_tokens = row["checklist_reader_output_o200k_tokens"]
    staged = row["staged_input_o200k_tokens"]
    total = row["effective_total_with_output_reserve_o200k_tokens"]
    max_by_input = max_staged_input_tokens - base
    max_by_total = effective_context_limit - max_output_reserve_tokens - base
    effective_checklist_max = min(
        max_checklist_reader_tokens, max_by_input, max_by_total
    )
    if (
        row.get("actual_frozen_draft_sha256") != sha256_bytes(actual_bytes)
        or row["actual_frozen_draft_size_bytes"] != len(actual_bytes)
        or row["frozen_checklist_yaml_size_bytes"] != len(actual_bytes)
        or row["actual_frozen_draft_o200k_tokens"]
        != row["frozen_checklist_yaml_o200k_tokens"]
        or not actual_text
        or row["max_checklist_reader_output_size_bytes"]
        != max_checklist_reader_bytes
        or row["max_checklist_reader_output_o200k_tokens_hard"]
        != max_checklist_reader_tokens
        or row["max_staged_input_o200k_tokens_gate"]
        != max_staged_input_tokens
        or row["reserved_output_o200k_tokens"] != max_output_reserve_tokens
        or row["effective_context_limit_o200k_tokens"] != effective_context_limit
        or row["protocol_reserve_o200k_tokens"] != protocol_reserve_tokens
        or base
        != row["prompt_o200k_tokens"]
        + row["packet_reader_output_o200k_tokens"]
        + protocol_reserve_tokens
        or row["max_checklist_o200k_tokens_by_210000_input_gate"]
        != max_by_input
        or row["max_checklist_o200k_tokens_by_258400_total_gate"]
        != max_by_total
        or row["effective_max_checklist_reader_output_o200k_tokens"]
        != effective_checklist_max
        or staged != base + checklist_tokens
        or row["staged_input_gate_headroom_o200k_tokens"]
        != max_staged_input_tokens - staged
        or total != staged + max_output_reserve_tokens
        or row["remaining_context_margin_o200k_tokens"]
        != effective_context_limit - total
        or row["checklist_reader_output_size_bytes"] > max_checklist_reader_bytes
        or checklist_tokens > effective_checklist_max
        or staged > max_staged_input_tokens
        or total > effective_context_limit
        or row.get("staged_input_gate_passed") is not True
        or row.get("effective_total_gate_passed") is not True
        or row.get("actual_frozen_draft_capacity_gate_passed") is not True
        or row.get("capacity_basis")
        != "actual_frozen_checklist_and_inventory_reader_output_exact_o200k_count"
    ):
        raise SemanticReviewV7Error(f"{label} exact two-gate capacity proof differs")


def require_case_id(value: Any) -> str:
    if not isinstance(value, str) or not CASE_RE.fullmatch(value):
        raise SemanticReviewV7Error(f"unsafe case identity: {value!r}")
    return value


def load_json(path: Path, label: str = "JSON") -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SemanticReviewV7Error(f"cannot load {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SemanticReviewV7Error(f"{label} is not an object: {path}")
    return value


def load_yaml(path: Path, label: str = "YAML") -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SemanticReviewV7Error(f"cannot load {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SemanticReviewV7Error(f"{label} is not an object: {path}")
    return value


def repository_relative(path: Path) -> str:
    resolved = path.resolve(strict=True)
    try:
        return resolved.relative_to(REPOSITORY_ROOT.resolve(strict=True)).as_posix()
    except ValueError:
        return resolved.as_posix()


def regular_file_binding(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise SemanticReviewV7Error(
            f"bound path is not a regular non-symlink file: {path}"
        )
    resolved = path.resolve(strict=True)
    return {
        "path": str(resolved),
        "repository_relative_path": repository_relative(resolved),
        "sha256": sha256_file(resolved),
        "size_bytes": resolved.stat().st_size,
        "mode": stat.S_IMODE(resolved.stat().st_mode),
    }


def verify_regular_file_binding(binding: Mapping[str, Any], label: str) -> Path:
    if not isinstance(binding, Mapping):
        raise SemanticReviewV7Error(f"{label} binding is not an object")
    path = Path(str(binding.get("path") or ""))
    if path.is_symlink() or not path.is_file():
        raise SemanticReviewV7Error(f"{label} path is missing/symlinked: {path}")
    if not is_exact_int(binding.get("size_bytes"), minimum=0) or not is_exact_int(
        binding.get("mode"), minimum=0
    ):
        raise SemanticReviewV7Error(
            f"{label} binding size/mode is not an exact JSON integer"
        )
    observed = regular_file_binding(path)
    for field in ("path", "repository_relative_path", "sha256", "size_bytes", "mode"):
        if observed[field] != binding.get(field):
            raise SemanticReviewV7Error(f"{label} binding changed at {field}")
    return path.resolve(strict=True)


def exact_tree(root: Path) -> dict[str, Any]:
    resolved = root.resolve(strict=True)
    if root.is_symlink() or not resolved.is_dir():
        raise SemanticReviewV7Error(f"tree root is missing/symlinked: {root}")
    rows: list[dict[str, Any]] = []
    for path in sorted(
        resolved.rglob("*"), key=lambda item: item.relative_to(resolved).as_posix()
    ):
        relative = path.relative_to(resolved).as_posix()
        if path.is_symlink():
            raise SemanticReviewV7Error(f"symlink forbidden in exact tree: {relative}")
        if path.is_file():
            rows.append(
                {
                    "relative_path": relative,
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                    "mode": stat.S_IMODE(path.stat().st_mode),
                }
            )
    return {
        "root": str(resolved),
        "file_count": len(rows),
        "files": rows,
        "files_sha256": canonical_sha256(rows),
    }


def verify_exact_tree(binding: Mapping[str, Any], label: str) -> Path:
    root = Path(str(binding.get("root") or ""))
    observed = exact_tree(root)
    if canonical_bytes(observed) != canonical_bytes(dict(binding)):
        raise SemanticReviewV7Error(f"{label} exact tree changed")
    return root.resolve(strict=True)


def write_json_create_once(
    path: Path, value: Mapping[str, Any], *, mode: int = 0o444
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise SemanticReviewV7Error(f"create-once JSON path is symlinked: {path}")
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise SemanticReviewV7Error(f"create-once JSON already exists: {path}") from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(path, mode)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def json_pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def json_pointer(parts: Sequence[str | int]) -> str:
    return "/" + "/".join(json_pointer_escape(str(part)) for part in parts)


def all_json_pointers(value: Any) -> set[str]:
    result: set[str] = set()

    def visit(current: Any, parts: list[str | int]) -> None:
        if parts:
            result.add(json_pointer(parts))
        if isinstance(current, Mapping):
            for key, child in current.items():
                visit(child, [*parts, str(key)])
        elif isinstance(current, list):
            for index, child in enumerate(current):
                visit(child, [*parts, index])

    visit(value, [])
    return result


def _require_text(value: Any, pointer: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SemanticReviewV7Error(f"checklist semantic text is empty at {pointer}")
    return value


def checklist_semantic_inventory(checklist: Mapping[str, Any]) -> dict[str, Any]:
    """Return every semantic claim and every support occurrence in stable order."""

    claims: list[dict[str, Any]] = []
    supports: list[dict[str, Any]] = []

    def add_claim(parts: list[str | int], value: Any, kind: str) -> str:
        pointer = json_pointer(parts)
        text = _require_text(value, pointer)
        claims.append(
            {
                "checklist_pointer": pointer,
                "kind": kind,
                "text_sha256": sha256_text(text),
            }
        )
        return pointer

    def add_supports(
        parts: list[str | int], value: Any, target_claim_pointers: Sequence[str]
    ) -> None:
        if not isinstance(value, list) or not value:
            raise SemanticReviewV7Error(
                f"checklist support is missing/empty at {json_pointer(parts)}"
            )
        for index, source_pointer in enumerate(value):
            if not isinstance(source_pointer, str) or not source_pointer.strip():
                raise SemanticReviewV7Error(
                    f"checklist support pointer is empty at {json_pointer([*parts, index])}"
                )
            supports.append(
                {
                    "support_pointer": json_pointer([*parts, index]),
                    "source_pointer": source_pointer,
                    "target_claim_pointers": list(target_claim_pointers),
                }
            )

    for field in ("case_unit_id", "domain", "task_id"):
        add_claim([field], checklist.get(field), "identity")

    native = checklist.get("native")
    if not isinstance(native, Mapping):
        raise SemanticReviewV7Error("checklist native section is missing")
    for field in ("user_goal", "benchmark_success", "checked_by"):
        item = native.get(field)
        if not isinstance(item, Mapping):
            raise SemanticReviewV7Error(f"native.{field} is not an object")
        target = add_claim(
            ["native", field, "text"], item.get("text"), f"native.{field}"
        )
        add_supports(["native", field, "support"], item.get("support"), [target])

    artifacts = native.get("decisive_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise SemanticReviewV7Error("native.decisive_artifacts is empty")
    for index, item in enumerate(artifacts):
        if not isinstance(item, Mapping):
            raise SemanticReviewV7Error(
                f"native decisive artifact {index} is malformed"
            )
        targets = [
            add_claim(
                ["native", "decisive_artifacts", index, "artifact"],
                item.get("artifact"),
                "native.decisive_artifact",
            ),
            add_claim(
                ["native", "decisive_artifacts", index, "question"],
                item.get("question"),
                "native.decisive_question",
            ),
        ]
        add_supports(
            ["native", "decisive_artifacts", index, "support"],
            item.get("support"),
            targets,
        )

    for field in ("success_if", "fail_if", "undecided_if"):
        items = native.get(field)
        if not isinstance(items, list) or not items:
            raise SemanticReviewV7Error(f"native.{field} is empty")
        for index, item in enumerate(items):
            if not isinstance(item, Mapping):
                raise SemanticReviewV7Error(f"native.{field}[{index}] is malformed")
            target = add_claim(
                ["native", field, index, "text"], item.get("text"), f"native.{field}"
            )
            add_supports(
                ["native", field, index, "support"], item.get("support"), [target]
            )

    stronger = checklist.get("stronger")
    if not isinstance(stronger, Mapping):
        raise SemanticReviewV7Error("checklist stronger section is missing")
    conditions = stronger.get("additional_conditions")
    if not isinstance(conditions, list):
        raise SemanticReviewV7Error("stronger.additional_conditions is not an array")
    for index, condition in enumerate(conditions):
        if not isinstance(condition, Mapping):
            raise SemanticReviewV7Error(f"stronger condition {index} is malformed")
        condition_targets = [
            add_claim(
                ["stronger", "additional_conditions", index, "id"],
                condition.get("id"),
                "stronger.id",
            ),
            add_claim(
                ["stronger", "additional_conditions", index, "text"],
                condition.get("text"),
                "stronger.text",
            ),
            add_claim(
                ["stronger", "additional_conditions", index, "rationale"],
                condition.get("rationale"),
                "stronger.rationale",
            ),
        ]
        add_supports(
            ["stronger", "additional_conditions", index, "support"],
            condition.get("support"),
            condition_targets,
        )
        condition_artifacts = condition.get("decisive_artifacts")
        if not isinstance(condition_artifacts, list) or not condition_artifacts:
            raise SemanticReviewV7Error(
                f"stronger condition {index} has no decisive artifacts"
            )
        for artifact_index, artifact in enumerate(condition_artifacts):
            if not isinstance(artifact, Mapping):
                raise SemanticReviewV7Error(
                    f"stronger condition {index} artifact {artifact_index} is malformed"
                )
            targets = [
                add_claim(
                    [
                        "stronger",
                        "additional_conditions",
                        index,
                        "decisive_artifacts",
                        artifact_index,
                        "artifact",
                    ],
                    artifact.get("artifact"),
                    "stronger.decisive_artifact",
                ),
                add_claim(
                    [
                        "stronger",
                        "additional_conditions",
                        index,
                        "decisive_artifacts",
                        artifact_index,
                        "question",
                    ],
                    artifact.get("question"),
                    "stronger.decisive_question",
                ),
            ]
            add_supports(
                [
                    "stronger",
                    "additional_conditions",
                    index,
                    "decisive_artifacts",
                    artifact_index,
                    "support",
                ],
                artifact.get("support"),
                targets,
            )

    claim_pointers = [row["checklist_pointer"] for row in claims]
    support_pointers = [row["support_pointer"] for row in supports]
    if len(claim_pointers) != len(set(claim_pointers)):
        raise SemanticReviewV7Error("semantic claim inventory contains duplicates")
    if len(support_pointers) != len(set(support_pointers)):
        raise SemanticReviewV7Error("support occurrence inventory contains duplicates")
    payload = {
        "schema_version": "androidworld_candidate116_semantic_review_v7_inventory/v1",
        "claim_count": len(claims),
        "claims": claims,
        "support_occurrence_count": len(supports),
        "support_occurrences": supports,
    }
    payload["inventory_sha256"] = canonical_sha256(payload)
    return payload


def validate_json_schema(
    instance: Mapping[str, Any], schema: Mapping[str, Any], label: str
) -> None:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: (list(error.absolute_path), error.message),
    )
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.absolute_path)
        raise SemanticReviewV7Error(
            f"{label} schema failure at {location}: {first.message}"
        )


def _validate_evidence(
    evidence: Any,
    *,
    raw_sources: Mapping[str, Mapping[str, Any]],
    covered_line_spans: Mapping[str, Sequence[tuple[int, int]]] | None,
    label: str,
) -> None:
    if not isinstance(evidence, list) or not evidence:
        raise SemanticReviewV7Error(f"{label} lacks source evidence")
    for index, row in enumerate(evidence):
        if not isinstance(row, Mapping):
            raise SemanticReviewV7Error(f"{label} evidence {index} is malformed")
        path = row.get("path")
        if (
            not isinstance(path, str)
            or not RAW_PATH_RE.fullmatch(path)
            or path not in raw_sources
        ):
            raise SemanticReviewV7Error(
                f"{label} evidence is not an exact raw official path: {path}"
            )
        start = row.get("line_start")
        end = row.get("line_end")
        line_count = raw_sources[path].get("line_count")
        if not is_exact_int(line_count, minimum=1):
            raise SemanticReviewV7Error(
                f"{label} raw-source line count is not an exact positive integer"
            )
        if (
            not isinstance(start, int)
            or isinstance(start, bool)
            or not isinstance(end, int)
            or isinstance(end, bool)
            or start < 1
            or end < start
            or end > line_count
        ):
            raise SemanticReviewV7Error(
                f"{label} evidence span is outside {path} (1..{line_count}): {start}-{end}"
            )
        if covered_line_spans is not None:
            spans = sorted(covered_line_spans.get(path) or [])
            cursor = start
            for covered_start, covered_end in spans:
                if covered_end < cursor:
                    continue
                if covered_start > cursor:
                    break
                cursor = max(cursor, covered_end + 1)
                if cursor > end:
                    break
            if cursor <= end:
                raise SemanticReviewV7Error(
                    f"{label} evidence span was not completely read by the frozen ledger: "
                    f"{path}:{start}-{end}"
                )
        role = row.get("evidence_role")
        if not isinstance(role, str) or len(role.strip()) < 12:
            raise SemanticReviewV7Error(f"{label} evidence role is not substantive")


def _check_assessment(value: Any, label: str) -> None:
    if not isinstance(value, str) or len(value.strip()) < 24:
        raise SemanticReviewV7Error(
            f"{label} assessment is not case-specific/substantive"
        )
    if " ".join(value.lower().split()) in GENERIC_ASSESSMENTS:
        raise SemanticReviewV7Error(f"{label} uses a generic assessment")


def validate_review_body(
    body: Mapping[str, Any],
    *,
    schema: Mapping[str, Any],
    checklist: Mapping[str, Any],
    inventory: Mapping[str, Any],
    raw_sources: Mapping[str, Mapping[str, Any]],
    require_accept: bool,
    covered_line_spans: Mapping[str, Sequence[tuple[int, int]]] | None = None,
) -> dict[str, Any]:
    """Validate exact review coverage and internally consistent verdict semantics."""

    validate_json_schema(body, schema, "semantic-review body")
    expected_dimensions = list(DIMENSION_IDS)
    dimensions = list(body.get("dimension_audits") or [])
    if [row.get("dimension_id") for row in dimensions] != expected_dimensions:
        raise SemanticReviewV7Error("dimension audit order/set is not exact")

    expected_claims = [
        (row["checklist_pointer"], row["text_sha256"])
        for row in inventory.get("claims") or []
    ]
    claims = list(body.get("claim_audits") or [])
    observed_claims = [
        (row.get("checklist_pointer"), row.get("text_sha256")) for row in claims
    ]
    if observed_claims != expected_claims:
        raise SemanticReviewV7Error(
            "claim audits do not exactly cover the frozen claim inventory"
        )

    expected_supports = [
        (
            row["support_pointer"],
            row["source_pointer"],
            row["target_claim_pointers"],
        )
        for row in inventory.get("support_occurrences") or []
    ]
    supports = list(body.get("support_audits") or [])
    observed_supports = [
        (
            row.get("support_pointer"),
            row.get("source_pointer"),
            row.get("target_claim_pointers"),
        )
        for row in supports
    ]
    if observed_supports != expected_supports:
        raise SemanticReviewV7Error(
            "support audits do not exactly cover the frozen support occurrence inventory"
        )

    findings = list(body.get("blocking_findings") or [])
    finding_ids = [row.get("finding_id") for row in findings]
    if (
        len(finding_ids) != len(set(finding_ids))
        or any(
            not isinstance(item, str) or not FINDING_RE.fullmatch(item)
            for item in finding_ids
        )
        or finding_ids != [f"F{index:03d}" for index in range(1, len(findings) + 1)]
    ):
        raise SemanticReviewV7Error(
            "blocking finding IDs are not unique sequential F001.."
        )
    finding_set = set(finding_ids)

    valid_checklist_pointers = all_json_pointers(checklist)
    failed_count = 0
    for label, rows in (
        ("dimension", dimensions),
        ("claim", claims),
        ("support", supports),
    ):
        for index, row in enumerate(rows):
            status = row.get("status")
            links = list(row.get("finding_ids") or [])
            if len(links) != len(set(links)) or not set(links).issubset(finding_set):
                raise SemanticReviewV7Error(
                    f"{label} audit {index} links an unknown finding"
                )
            if status == "pass" and links:
                raise SemanticReviewV7Error(
                    f"passing {label} audit {index} links a finding"
                )
            if status == "fail":
                failed_count += 1
                if not links:
                    raise SemanticReviewV7Error(
                        f"failed {label} audit {index} lacks a finding"
                    )
            if label == "dimension":
                _check_assessment(row.get("assessment"), f"dimension {index}")
                pointers = list(row.get("checklist_pointers") or [])
            elif label == "claim":
                _check_assessment(row.get("assessment"), f"claim {index}")
                pointers = [row.get("checklist_pointer")]
            else:
                _check_assessment(row.get("entailment"), f"support {index}")
                pointers = [
                    row.get("support_pointer"),
                    *(row.get("target_claim_pointers") or []),
                ]
            if any(pointer not in valid_checklist_pointers for pointer in pointers):
                raise SemanticReviewV7Error(
                    f"{label} audit {index} cites a nonexistent checklist pointer"
                )
            _validate_evidence(
                row.get("source_evidence"),
                raw_sources=raw_sources,
                covered_line_spans=covered_line_spans,
                label=f"{label} audit {index}",
            )

    linked_failures: set[str] = set()
    for index, finding in enumerate(findings):
        pointers = list(finding.get("checklist_pointers") or [])
        if any(pointer not in valid_checklist_pointers for pointer in pointers):
            raise SemanticReviewV7Error(
                f"finding {index} cites a nonexistent checklist pointer"
            )
        _check_assessment(finding.get("blocking_explanation"), f"finding {index}")
        _validate_evidence(
            finding.get("source_evidence"),
            raw_sources=raw_sources,
            covered_line_spans=covered_line_spans,
            label=f"finding {index}",
        )
        linked_failures.add(str(finding.get("finding_id")))

    verdict = body.get("verdict")
    if verdict == "accept":
        if failed_count or findings:
            raise SemanticReviewV7Error(
                "accept verdict contains a failed audit or blocking finding"
            )
    elif verdict == "reject":
        if failed_count == 0 or not findings:
            raise SemanticReviewV7Error(
                "reject verdict lacks a linked failed audit/finding"
            )
        referenced = {
            finding_id
            for rows in (dimensions, claims, supports)
            for row in rows
            for finding_id in row.get("finding_ids") or []
        }
        if referenced != linked_failures:
            raise SemanticReviewV7Error("one blocking finding is orphaned or unlinked")
    else:
        raise SemanticReviewV7Error(f"invalid review verdict: {verdict}")
    if require_accept and verdict != "accept":
        raise SemanticReviewV7Error(
            "independent acceptance gate requires verdict=accept"
        )

    return {
        "verdict": verdict,
        "dimension_count": len(dimensions),
        "claim_count": len(claims),
        "support_occurrence_count": len(supports),
        "blocking_finding_count": len(findings),
        "failed_audit_count": failed_count,
        "body_sha256": canonical_sha256(body),
    }


def covered_line_spans_from_requirements(
    requirements: Mapping[str, Any],
) -> dict[str, list[tuple[int, int]]]:
    """Return the exact raw-file line intervals authorized by frozen reader rows."""

    result: dict[str, list[tuple[int, int]]] = {}
    for index, row in enumerate(requirements.get("required_ranges") or []):
        if row.get("anchor") != "raw_source_closure_chunk":
            continue
        path = row.get("path")
        start = row.get("start_line")
        end = row.get("end_line")
        if (
            not isinstance(path, str)
            or not RAW_PATH_RE.fullmatch(path)
            or not isinstance(start, int)
            or isinstance(start, bool)
            or not isinstance(end, int)
            or isinstance(end, bool)
            or start < 1
            or end < start
        ):
            raise SemanticReviewV7Error(f"malformed frozen reader range {index}")
        result.setdefault(path, []).append((start, end))
    return {path: sorted(spans) for path, spans in result.items()}


def parse_jsonl(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SemanticReviewV7Error(
                f"malformed JSONL at {path}:{line_number}"
            ) from exc
        if not isinstance(value, dict):
            raise SemanticReviewV7Error(
                f"non-object JSONL event at {path}:{line_number}"
            )
        events.append(value)
    if not events:
        raise SemanticReviewV7Error(f"empty Codex JSONL event stream: {path}")
    return events


def ensure_no_sensitive_hash_fields(value: Any, *, path: str = "$.") -> None:
    """Reject persisted fields that claim to hash or expose authentication material."""

    if isinstance(value, Mapping):
        for key, child in value.items():
            lowered = str(key).lower()
            if (
                "auth" in lowered
                and any(
                    token in lowered for token in ("sha", "hash", "content", "bytes")
                )
                and child not in (False, None, "forbidden", "not_persisted")
            ):
                raise SemanticReviewV7Error(
                    f"authentication content/hash field forbidden at {path}{key}"
                )
            ensure_no_sensitive_hash_fields(child, path=f"{path}{key}.")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            ensure_no_sensitive_hash_fields(child, path=f"{path}[{index}].")
