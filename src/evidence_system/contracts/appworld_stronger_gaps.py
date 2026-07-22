"""Frozen AppWorld task-intent/evaluator gap registry.

The registry is reviewed before draft generation and is copied into every
AppWorld packet.  A drafter may not infer, omit, add, or rewrite a stronger
condition: ``stronger.additional_conditions`` must exactly equal the packet's
approved projection.  This turns task/evaluator-gap handling into a frozen
input instead of a post-hoc model judgement.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path


REGISTRY_SCHEMA = "appworld_stronger_gap_registry.v2"
PACKET_REGISTRY_SCHEMA = "appworld_packet_stronger_gap_registry.v2"
APPWORLD_GIT_COMMIT = "a072b7a86e7c1d5b1d7175659d750ebb9b79f10a"
APPWORLD_DATA_VERSION = "0.1.0"
EXPECTED_CASE_COUNT = 485
REGISTRY_PATH = Path(
    "experiments/appworld_full_test_extension_v1/official_splits/"
    "appworld_stronger_gap_registry.gpt56.v2.json"
)
REVIEW_POLICY_PATH = Path(
    "experiments/appworld_full_test_extension_v1/official_splits/"
    "appworld_stronger_gap_review_policy.gpt56.v1.json"
)
EXTENSION_MANIFEST_PATH = Path(
    "experiments/appworld_full_test_extension_v1/experiment_manifest.json"
)
SOURCE_CATALOG_PATH = Path(
    "experiments/appworld_full_test_extension_v1/official_splits/"
    "appworld_selected_task_sources.json"
)
REVIEW_POLICY_SCHEMA = "appworld_stronger_gap_review_policy.v1"
REVIEW_RECEIPT_SCHEMA = "appworld_stronger_gap_review_receipt.v1"
REVIEW_RECEIPT_PATH = Path(
    "experiments/appworld_full_test_extension_v1/official_splits/"
    "appworld_stronger_gap_review_receipt.gpt56.v1.json"
)
REVIEW_RECEIPT_SHA256 = "b4cf32d62078e827c8ee32c1ae18595e1de3dc7134c7609695b85460f0f9dcc7"
REVIEW_RULE = (
    "Record every concrete explicit task-intent obligation not fully enforced by the "
    "registered with-test evaluator blocks; never derive a condition from "
    "test.task_completed or another non-scoring convenience assignment."
)
REGISTRY_SHA256 = "cf942eca4bd1a84d05031aaf4bc5a93977c491492b84fd5b4b5d8e34c8536cb0"

_GAP_MARKER_RE = re.compile(r"\[appworld_stronger_gap_[0-9]{3}_[0-9a-f]{12}\]")
_MARKER_SHAPED_RE = re.compile(r"\[\s*appworld_stronger_gap_[^\]\r\n]*\]", re.I)
_FORBIDDEN_DYNAMIC_PATTERNS = (
    re.compile(r"\btest task completed\b"),
    re.compile(r"\btask completed\b"),
    re.compile(r"\btask(?: [0-9]+)? status\b"),
    re.compile(r"\bactive tasks?(?: [0-9]+)? status\b"),
    re.compile(r"\bsupervisor tasks?(?: [0-9]+)? status\b"),
)


class AppWorldStrongerGapError(ContractLifecycleError):
    """Raised when a frozen stronger-gap binding cannot be accepted."""


def _fail(message: str) -> None:
    raise AppWorldStrongerGapError(message)


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f"{label} must be a mapping")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(f"{label} must be a non-empty string")
    return value


def appworld_stronger_gap_marker(index: int, condition_without_marker: Mapping[str, Any]) -> str:
    """Return the stable marker for one approved condition."""

    digest = sha256_object(dict(condition_without_marker))[:12]
    return f"[appworld_stronger_gap_{index:03d}_{digest}]"


def _condition_without_marker(condition: Mapping[str, Any], marker: str) -> dict[str, Any]:
    text = _string(condition.get("text"), "required_condition.text")
    prefix = marker + " "
    if not text.startswith(prefix):
        _fail("required_condition.text must start with its exact stronger-gap marker")
    projected = dict(condition)
    projected["text"] = text[len(prefix) :]
    return projected


def _string_leaves(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        return [leaf for child in value.values() for leaf in _string_leaves(child)]
    if isinstance(value, list):
        return [leaf for child in value for leaf in _string_leaves(child)]
    return []


def _semantic_text_leaves(condition: Mapping[str, Any]) -> list[str]:
    leaves = [
        _string(condition.get("id"), "required_condition.id"),
        _string(condition.get("text"), "required_condition.text"),
        _string(condition.get("rationale"), "required_condition.rationale"),
    ]
    artifacts = condition.get("decisive_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        _fail("required_condition.decisive_artifacts must be a non-empty array")
    for index, raw in enumerate(artifacts):
        artifact = _mapping(raw, f"required_condition.decisive_artifacts[{index}]")
        if set(artifact) != {"artifact", "question", "support"}:
            _fail(f"artifact[{index}] has an unexpected field set")
        leaves.extend(
            [
                _string(artifact.get("artifact"), f"artifact[{index}].artifact"),
                _string(artifact.get("question"), f"artifact[{index}].question"),
            ]
        )
        artifact_support = artifact.get("support")
        if (
            not isinstance(artifact_support, list)
            or not artifact_support
            or not all(isinstance(pointer, str) and pointer for pointer in artifact_support)
            or len(artifact_support) != len(set(artifact_support))
        ):
            _fail(f"artifact[{index}].support must be a non-empty unique string array")
    support = condition.get("support")
    if (
        not isinstance(support, list)
        or not support
        or not all(isinstance(pointer, str) and pointer for pointer in support)
        or len(support) != len(set(support))
    ):
        _fail("required_condition.support must be a non-empty unique string array")
    return leaves


def _normalized_alias_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = "".join(
        " " if unicodedata.category(character) == "Cf" else character
        for character in normalized
    )
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def validate_condition_without_marker(raw: Any, *, index: int) -> dict[str, Any]:
    """Validate a reviewed policy condition before a marker is generated."""

    condition = dict(_mapping(raw, f"gap[{index}].required_condition"))
    marker = appworld_stronger_gap_marker(index, condition)
    marked = dict(condition)
    marked["text"] = (
        f"{marker} {_string(condition.get('text'), 'required_condition.text')}"
    )
    _validate_required_condition(marked, index=index, marker=marker)
    return condition


def appworld_gap_basis(
    condition_without_marker: Mapping[str, Any],
    *,
    registered_test_registry_sha256: str,
    non_scoring_assignment_registry_sha256: str,
) -> dict[str, Any]:
    """Build the structural task/evaluator/non-scoring exclusion basis for one gap."""

    condition = validate_condition_without_marker(condition_without_marker, index=1)
    support = list(condition["support"])
    evaluator_pointer = "official/ground_truth/evaluation.py::evaluate"
    instruction_support = [pointer for pointer in support if pointer != evaluator_pointer]
    if "official/specs.json::$.instruction" not in instruction_support:
        _fail("stronger-gap basis must cite the exact official instruction")
    claim = {
        "id": condition["id"],
        "text": condition["text"],
        "rationale": condition["rationale"],
        "instruction_support": instruction_support,
    }
    basis: dict[str, Any] = {
        "disposition": "explicit_task_intent_not_fully_enforced_by_registered_tests",
        "instruction_support": instruction_support,
        "instruction_claim_sha256": sha256_object(claim),
        "native_evaluator_support": [evaluator_pointer],
        "native_registered_test_registry_sha256": registered_test_registry_sha256,
        "excluded_non_scoring_assignment_registry_sha256": (
            non_scoring_assignment_registry_sha256
        ),
    }
    basis["basis_semantic_sha256"] = sha256_object(basis)
    return basis


def validate_review_basis(value: Any) -> dict[str, Any]:
    """Validate the exact exhaustive-review identity and its immutable receipt."""

    basis = dict(_mapping(value, "stronger-gap review basis"))
    expected = {
        "status": "source_only_exhaustive_review",
        "scope": "485 extension cases",
        "rule": REVIEW_RULE,
        "normal_reviewed_case_count": 68,
        "challenge_reviewed_case_count": 417,
        "review_receipt_path": REVIEW_RECEIPT_PATH.as_posix(),
        "review_receipt_schema": REVIEW_RECEIPT_SCHEMA,
        "review_receipt_sha256": REVIEW_RECEIPT_SHA256,
    }
    if basis != expected:
        _fail("stronger-gap review basis identity/counts/receipt drifted")
    receipt_path = resolve_repo_path(REVIEW_RECEIPT_PATH)
    if (
        not receipt_path.is_file()
        or receipt_path.is_symlink()
        or sha256_file(receipt_path) != REVIEW_RECEIPT_SHA256
    ):
        _fail("stronger-gap exhaustive-review receipt bytes drifted")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AppWorldStrongerGapError("stronger-gap review receipt is malformed") from exc
    receipt_mapping = dict(_mapping(receipt, "stronger-gap review receipt"))
    observed_semantic_sha = receipt_mapping.pop("receipt_semantic_sha256", None)
    if (
        receipt.get("schema_version") != REVIEW_RECEIPT_SCHEMA
        or receipt.get("status") != "passed_source_only_exhaustive_review"
        or observed_semantic_sha != sha256_object(receipt_mapping)
    ):
        _fail("stronger-gap review receipt semantic binding drifted")
    return basis


def validate_review_receipt_inputs(
    *, manifest_path: Path, catalog_path: Path, policy: Mapping[str, Any]
) -> dict[str, Any]:
    """Bind the receipt to the exact reviewed inputs and policy projection."""

    receipt_path = resolve_repo_path(REVIEW_RECEIPT_PATH)
    try:
        receipt = dict(
            _mapping(
                json.loads(receipt_path.read_text(encoding="utf-8")),
                "stronger-gap review receipt",
            )
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise AppWorldStrongerGapError(
            "stronger-gap review receipt cannot be loaded"
        ) from exc
    reviewed_inputs = _mapping(receipt.get("reviewed_inputs"), "receipt reviewed inputs")
    projection = {
        "groups": policy.get("groups"),
        "reviewed_no_gap_case_ids": policy.get("reviewed_no_gap_case_ids"),
    }
    expected_inputs = {
        "manifest_path": EXTENSION_MANIFEST_PATH.as_posix(),
        "manifest_sha256": sha256_file(manifest_path),
        "source_catalog_path": SOURCE_CATALOG_PATH.as_posix(),
        "source_catalog_sha256": sha256_file(catalog_path),
        "policy_path": REVIEW_POLICY_PATH.as_posix(),
        "policy_file_sha256_before_receipt_binding": (
            "217bb406f80fa8abfa2d263ad241cab5d469eece56626ee21c9bf4b9101ace28"
        ),
        "policy_projection_sha256": sha256_object(projection),
    }
    if dict(reviewed_inputs) != expected_inputs:
        _fail("stronger-gap receipt does not bind the current reviewed inputs/projection")
    scope = _mapping(receipt.get("scope"), "receipt scope")
    expected_scope = {
        "appworld_commit": APPWORLD_GIT_COMMIT,
        "data_version": APPWORLD_DATA_VERSION,
        "case_count": 485,
        "normal_case_count": 68,
        "challenge_case_count": 417,
        "gap_case_count": 135,
        "explicit_no_gap_case_count": 350,
        "required_condition_count": 137,
        "normal_gap_case_count": 33,
        "normal_no_gap_case_count": 35,
        "normal_condition_count": 35,
        "challenge_gap_case_count": 102,
        "challenge_no_gap_case_count": 315,
        "challenge_condition_count": 102,
    }
    if dict(scope) != expected_scope:
        _fail("stronger-gap receipt scope/counts drifted")
    acceptance = _mapping(receipt.get("acceptance"), "receipt acceptance")
    if (
        acceptance.get("unresolved_p0_count") != 0
        or acceptance.get("unresolved_p1_count") != 0
        or acceptance.get("source_hash_mismatch_count") != 0
        or acceptance.get("registered_test_registry_mismatch_count") != 0
        or acceptance.get("support_pointer_failure_count") != 0
        or acceptance.get("dynamic_non_scoring_alias_finding_count") != 0
        or acceptance.get("source_only_artifact_boundary_finding_count") != 0
        or acceptance.get("manifest_gap_no_gap_union_exact") is not True
        or acceptance.get("gap_no_gap_disjoint") is not True
        or acceptance.get("explicit_no_gap_ordered_complement_exact") is not True
    ):
        _fail("stronger-gap receipt acceptance is not a zero-finding pass")
    return receipt


def _validate_required_condition(raw: Any, *, index: int, marker: str) -> dict[str, Any]:
    condition = dict(_mapping(raw, f"gap[{index}].required_condition"))
    if set(condition) != {"id", "text", "rationale", "decisive_artifacts", "support"}:
        _fail(f"gap[{index}].required_condition has an unexpected field set")
    if _GAP_MARKER_RE.fullmatch(marker) is None:
        _fail(f"gap[{index}] marker is malformed")
    without_marker = _condition_without_marker(condition, marker)
    if appworld_stronger_gap_marker(index, without_marker) != marker:
        _fail(f"gap[{index}] marker/hash binding is invalid")
    marker_hits = [
        hit.group(0)
        for leaf in _string_leaves(condition)
        for hit in _MARKER_SHAPED_RE.finditer(leaf)
    ]
    for leaf in _string_leaves(condition):
        without_closed_markers = _MARKER_SHAPED_RE.sub("", leaf)
        if re.search(r"\[\s*appworld_", without_closed_markers, flags=re.I):
            _fail(f"gap[{index}] contains an unclosed or malformed AppWorld marker prefix")
    if marker_hits != [marker]:
        _fail(f"gap[{index}] marker must occur exactly once, only in condition text")
    normalized_semantic_text = "\n".join(
        _normalized_alias_text(value) for value in _semantic_text_leaves(condition)
    )
    for pattern in _FORBIDDEN_DYNAMIC_PATTERNS:
        if pattern.search(normalized_semantic_text):
            _fail(
                f"gap[{index}] condition derives from a non-scoring TestTracker convenience field"
            )
    return condition


def _validate_case_entry(raw: Any, *, expected_index: int | None = None) -> dict[str, Any]:
    entry = dict(_mapping(raw, "stronger-gap case entry"))
    expected_keys = {
        "case_unit_id",
        "split",
        "source_ref",
        "source_basis_sha256",
        "registered_test_registry_sha256",
        "non_scoring_assignment_registry",
        "non_scoring_assignment_registry_sha256",
        "non_scoring_assignment_exclusion_status",
        "review_status",
        "gaps",
        "entry_semantic_sha256",
    }
    if set(entry) != expected_keys:
        _fail("stronger-gap case entry has an unexpected field set")
    case_id = _string(entry.get("case_unit_id"), "case_unit_id")
    if not re.fullmatch(r"[0-9a-f]{7}_[123]", case_id):
        _fail(f"invalid AppWorld case ID in stronger-gap registry: {case_id!r}")
    if entry.get("split") not in {"test_normal", "test_challenge"}:
        _fail(f"{case_id}: invalid split")
    if entry.get("source_ref") != f"appworld://{entry['split']}/{case_id}":
        _fail(f"{case_id}: source_ref does not match split/case identity")
    for field in ("source_basis_sha256", "registered_test_registry_sha256"):
        if re.fullmatch(r"[0-9a-f]{64}", str(entry.get(field) or "")) is None:
            _fail(f"{case_id}: {field} is not a SHA-256")
    non_scoring = entry.get("non_scoring_assignment_registry")
    if not isinstance(non_scoring, list) or len(non_scoring) != 1:
        _fail(f"{case_id}: expected exactly one frozen non-scoring assignment")
    assignment = _mapping(non_scoring[0], f"{case_id}.non_scoring_assignment_registry[0]")
    if set(assignment) != {
        "attribute",
        "line",
        "source_expression",
        "semantic_atoms",
    }:
        _fail(f"{case_id}: non-scoring assignment has an unexpected field set")
    atoms = _mapping(assignment.get("semantic_atoms"), f"{case_id}.non-scoring semantic atoms")
    if (
        assignment.get("attribute") != "task_completed"
        or not isinstance(assignment.get("line"), int)
        or assignment["line"] <= 0
        or not isinstance(assignment.get("source_expression"), str)
        or not assignment["source_expression"]
        or set(atoms) != {"attributes", "names", "constants"}
        or any(
            not isinstance(atoms.get(field), list)
            or not all(isinstance(value, str) for value in atoms[field])
            or atoms[field] != sorted(set(atoms[field]))
            for field in ("attributes", "names", "constants")
        )
    ):
        _fail(f"{case_id}: non-scoring assignment registry is malformed")
    if (
        entry.get("non_scoring_assignment_registry_sha256")
        != sha256_object(non_scoring)
        or entry.get("non_scoring_assignment_exclusion_status")
        != "excluded_from_native_and_stronger_scoring"
    ):
        _fail(f"{case_id}: non-scoring assignment exclusion binding drifted")
    gaps = entry.get("gaps")
    if not isinstance(gaps, list):
        _fail(f"{case_id}: gaps must be an array")
    if entry.get("review_status") != ("reviewed_gap" if gaps else "reviewed_no_gap"):
        _fail(f"{case_id}: review_status/gaps mismatch")
    markers: list[str] = []
    for index, raw_gap in enumerate(gaps, start=1):
        gap = _mapping(raw_gap, f"{case_id}.gaps[{index - 1}]")
        if set(gap) != {
            "index",
            "marker",
            "condition_sha256",
            "required_condition",
            "gap_basis",
        }:
            _fail(f"{case_id}: gap[{index}] has an unexpected field set")
        if gap.get("index") != index:
            _fail(f"{case_id}: gap indexes must be consecutive and ordered")
        marker = _string(gap.get("marker"), f"{case_id}.gap[{index}].marker")
        condition = _validate_required_condition(
            gap.get("required_condition"), index=index, marker=marker
        )
        expected_condition_sha256 = sha256_object(_condition_without_marker(condition, marker))
        if gap.get("condition_sha256") != expected_condition_sha256:
            _fail(f"{case_id}: gap[{index}] condition hash mismatch")
        expected_basis = appworld_gap_basis(
            _condition_without_marker(condition, marker),
            registered_test_registry_sha256=entry["registered_test_registry_sha256"],
            non_scoring_assignment_registry_sha256=entry[
                "non_scoring_assignment_registry_sha256"
            ],
        )
        if gap.get("gap_basis") != expected_basis:
            _fail(f"{case_id}: gap[{index}] structural basis/exclusion mismatch")
        markers.append(marker)
    if len(markers) != len(set(markers)):
        _fail(f"{case_id}: duplicate stronger-gap marker")
    semantic = dict(entry)
    observed_entry_sha = semantic.pop("entry_semantic_sha256")
    if observed_entry_sha != sha256_object(semantic):
        _fail(f"{case_id}: entry semantic hash mismatch")
    return entry


def validate_registry_case_entry(raw: Any) -> dict[str, Any]:
    """Validate one complete generated registry entry before publication."""

    return _validate_case_entry(raw)


def load_frozen_appworld_stronger_gap_registry() -> dict[str, Any]:
    """Load and fully validate the immutable 485-case registry."""

    path = resolve_repo_path(REGISTRY_PATH)
    if not path.is_file() or path.is_symlink():
        _fail(f"frozen stronger-gap registry is missing or symlinked: {path}")
    observed_sha = sha256_file(path)
    if observed_sha != REGISTRY_SHA256:
        _fail(
            "frozen stronger-gap registry hash mismatch: "
            f"expected={REGISTRY_SHA256}, actual={observed_sha}"
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AppWorldStrongerGapError("frozen stronger-gap registry is malformed") from exc
    registry = dict(_mapping(payload, "frozen stronger-gap registry"))
    if set(registry) != {
        "schema_version",
        "appworld_commit",
        "data_version",
        "case_count",
        "case_ids_semantic_sha256",
        "review_policy",
        "cases",
        "registry_semantic_sha256",
    }:
        _fail("frozen stronger-gap registry has an unexpected field set")
    if (
        registry.get("schema_version") != REGISTRY_SCHEMA
        or registry.get("appworld_commit") != APPWORLD_GIT_COMMIT
        or registry.get("data_version") != APPWORLD_DATA_VERSION
        or registry.get("case_count") != EXPECTED_CASE_COUNT
    ):
        _fail("frozen stronger-gap registry identity drift")
    review = _mapping(registry.get("review_policy"), "frozen review policy binding")
    if set(review) != {
        "path",
        "sha256",
        "schema_version",
        "review_basis",
        "reviewed_gap_case_count",
        "reviewed_no_gap_case_count",
        "reviewed_no_gap_case_ids_sha256",
        "required_condition_count",
    }:
        _fail("frozen stronger-gap review-policy binding has an unexpected field set")
    policy_path = resolve_repo_path(REVIEW_POLICY_PATH)
    if (
        review.get("path") != REVIEW_POLICY_PATH.as_posix()
        or review.get("schema_version") != REVIEW_POLICY_SCHEMA
        or not policy_path.is_file()
        or policy_path.is_symlink()
        or review.get("sha256") != sha256_file(policy_path)
    ):
        _fail("frozen stronger-gap registry is stale against the reviewed policy bytes")
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AppWorldStrongerGapError(
            "frozen stronger-gap review policy is malformed"
        ) from exc
    policy_mapping = _mapping(policy, "frozen stronger-gap review policy")
    if set(policy_mapping) != {
        "schema_version",
        "review_basis",
        "reviewed_no_gap_case_ids",
        "groups",
    }:
        _fail("frozen stronger-gap review policy has an unexpected field set")
    if (
        policy_mapping.get("schema_version") != REVIEW_POLICY_SCHEMA
        or validate_review_basis(policy_mapping.get("review_basis"))
        != review.get("review_basis")
    ):
        _fail("frozen stronger-gap review policy identity/basis drifted")
    validate_review_receipt_inputs(
        manifest_path=resolve_repo_path(EXTENSION_MANIFEST_PATH),
        catalog_path=resolve_repo_path(SOURCE_CATALOG_PATH),
        policy=policy_mapping,
    )
    cases = registry.get("cases")
    if not isinstance(cases, list) or len(cases) != EXPECTED_CASE_COUNT:
        _fail("frozen stronger-gap registry must contain exactly 485 cases")
    validated = [_validate_case_entry(raw) for raw in cases]
    case_ids = [record["case_unit_id"] for record in validated]
    if len(case_ids) != len(set(case_ids)):
        _fail("frozen stronger-gap registry contains duplicate case IDs")
    if registry.get("case_ids_semantic_sha256") != sha256_object(case_ids):
        _fail("frozen stronger-gap registry case-order hash mismatch")
    groups = policy_mapping.get("groups")
    if not isinstance(groups, list):
        _fail("frozen stronger-gap review policy groups must be an array")
    policy_conditions_by_case: dict[str, list[dict[str, Any]]] = {}
    for group_index, raw_group in enumerate(groups):
        group = _mapping(raw_group, f"review policy group[{group_index}]")
        if set(group) != {"case_ids", "conditions"}:
            _fail(f"review policy group[{group_index}] has an unexpected field set")
        group_case_ids = group.get("case_ids")
        conditions = group.get("conditions")
        if (
            not isinstance(group_case_ids, list)
            or not group_case_ids
            or len(group_case_ids) != len(set(group_case_ids))
            or not isinstance(conditions, list)
            or not conditions
        ):
            _fail(f"review policy group[{group_index}] is empty or duplicated")
        projected_conditions: list[dict[str, Any]] = []
        condition_ids: list[str] = []
        for index, raw_condition in enumerate(conditions, start=1):
            condition = validate_condition_without_marker(raw_condition, index=index)
            condition_ids.append(condition["id"])
            projected_conditions.append(condition)
        if len(condition_ids) != len(set(condition_ids)):
            _fail(f"review policy group[{group_index}] contains duplicate condition IDs")
        for raw_case_id in group_case_ids:
            case_id = _string(raw_case_id, f"review policy group[{group_index}] case ID")
            if case_id not in case_ids or case_id in policy_conditions_by_case:
                _fail(f"review policy case is off-scope or duplicated: {case_id}")
            policy_conditions_by_case[case_id] = projected_conditions
    for record in validated:
        expected_gaps: list[dict[str, Any]] = []
        for index, condition in enumerate(
            policy_conditions_by_case.get(record["case_unit_id"], []), start=1
        ):
            marker = appworld_stronger_gap_marker(index, condition)
            marked = dict(condition)
            marked["text"] = f"{marker} {condition['text']}"
            expected_gaps.append(
                {
                    "index": index,
                    "marker": marker,
                    "condition_sha256": sha256_object(condition),
                    "required_condition": marked,
                    "gap_basis": appworld_gap_basis(
                        condition,
                        registered_test_registry_sha256=record[
                            "registered_test_registry_sha256"
                        ],
                        non_scoring_assignment_registry_sha256=record[
                            "non_scoring_assignment_registry_sha256"
                        ],
                    ),
                }
            )
        if record["gaps"] != expected_gaps:
            _fail(
                f"{record['case_unit_id']}: frozen registry gaps differ from review-policy projection"
            )
    gap_case_count = sum(bool(record["gaps"]) for record in validated)
    condition_count = sum(len(record["gaps"]) for record in validated)
    no_gap_case_ids = [
        record["case_unit_id"] for record in validated if not record["gaps"]
    ]
    if (
        policy_mapping.get("reviewed_no_gap_case_ids") != no_gap_case_ids
        or review.get("reviewed_no_gap_case_ids_sha256")
        != sha256_object(no_gap_case_ids)
    ):
        _fail("frozen stronger-gap explicit no-gap disposition drifted")
    if (
        review.get("reviewed_gap_case_count") != gap_case_count
        or review.get("reviewed_no_gap_case_count") != EXPECTED_CASE_COUNT - gap_case_count
        or review.get("required_condition_count") != condition_count
    ):
        _fail("frozen stronger-gap review-policy aggregate counts drifted")
    semantic = dict(registry)
    observed_registry_sha = semantic.pop("registry_semantic_sha256")
    if observed_registry_sha != sha256_object(semantic):
        _fail("frozen stronger-gap registry semantic hash mismatch")
    return registry


def stronger_gap_case_entry(
    *,
    case_unit_id: str,
    split: str,
    source_ref: str,
    source_basis_sha256: str,
    registered_test_registry_sha256: str,
) -> dict[str, Any]:
    """Select one frozen entry and bind it to the packet's raw sources."""

    registry = load_frozen_appworld_stronger_gap_registry()
    matches = [raw for raw in registry["cases"] if raw["case_unit_id"] == case_unit_id]
    if len(matches) != 1:
        _fail(f"{case_unit_id}: stronger-gap registry identity is absent or duplicated")
    entry = dict(_validate_case_entry(matches[0]))
    expected = {
        "split": split,
        "source_ref": source_ref,
        "source_basis_sha256": source_basis_sha256,
        "registered_test_registry_sha256": registered_test_registry_sha256,
    }
    for field, value in expected.items():
        if entry.get(field) != value:
            _fail(f"{case_unit_id}: frozen stronger-gap {field} differs from packet source")
    return entry


def packet_stronger_gap_payload(entry: Mapping[str, Any]) -> dict[str, Any]:
    """Build the exact self-contained packet projection."""

    validated = _validate_case_entry(entry)
    return {
        "schema_version": PACKET_REGISTRY_SCHEMA,
        "registry_source": REGISTRY_PATH.as_posix(),
        "registry_sha256": REGISTRY_SHA256,
        "case": validated,
    }


def frozen_stronger_gap_case_entry(case_unit_id: str) -> dict[str, Any]:
    """Return exactly one canonical case entry from the frozen global registry."""

    registry = load_frozen_appworld_stronger_gap_registry()
    matches = [
        raw for raw in registry["cases"] if raw.get("case_unit_id") == case_unit_id
    ]
    if len(matches) != 1:
        _fail(f"{case_unit_id}: global stronger-gap registry entry is absent or duplicated")
    return dict(_validate_case_entry(matches[0]))


def parse_packet_stronger_gap_registry(packet_text: str) -> dict[str, Any]:
    """Parse and validate the packet's sole stronger-gap JSON fence."""

    heading = "### Machine-verifiable stronger-gap registry"
    heading_matches = re.findall(
        r"^[ ]{0,3}#{1,6}[ \t]+Machine-verifiable[ \t]+stronger-gap[ \t]+registry"
        r"(?:[ \t]+#+)?[ \t]*$",
        packet_text,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    if heading_matches != [heading]:
        _fail("case packet must contain one exact, unambiguous stronger-gap registry heading")
    sections = re.findall(
        r"^### Machine-verifiable stronger-gap registry\s*$\n(?P<body>.*?)(?=^### |^## |\Z)",
        packet_text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if len(sections) != 1:
        _fail(
            "case packet must contain exactly one machine-verifiable stronger-gap registry"
        )
    fences = re.findall(
        r"^```json\s*$\n(?P<json>.*?)^```\s*$",
        sections[0],
        flags=re.MULTILINE | re.DOTALL,
    )
    if len(fences) != 1:
        _fail("packet stronger-gap registry must contain exactly one JSON fence")
    try:
        raw = json.loads(fences[0])
    except json.JSONDecodeError as exc:
        raise AppWorldStrongerGapError("packet stronger-gap registry is malformed") from exc
    payload = dict(_mapping(raw, "packet stronger-gap registry"))
    if set(payload) != {"schema_version", "registry_source", "registry_sha256", "case"}:
        _fail("packet stronger-gap registry has an unexpected field set")
    if (
        payload.get("schema_version") != PACKET_REGISTRY_SCHEMA
        or payload.get("registry_source") != REGISTRY_PATH.as_posix()
        or payload.get("registry_sha256") != REGISTRY_SHA256
    ):
        _fail("packet stronger-gap registry provenance drift")
    payload["case"] = _validate_case_entry(payload.get("case"))
    canonical = frozen_stronger_gap_case_entry(payload["case"]["case_unit_id"])
    if payload["case"] != canonical:
        _fail(
            f"{payload['case']['case_unit_id']}: packet stronger-gap entry differs from "
            "the frozen global registry"
        )
    return payload


def validate_stronger_gap_composition(
    *, packet_payload: Mapping[str, Any], checklist: Mapping[str, Any]
) -> dict[str, Any]:
    """Require the checklist stronger surface to equal the frozen projection."""

    entry = _validate_case_entry(_mapping(packet_payload.get("case"), "packet case entry"))
    stronger = _mapping(checklist.get("stronger"), "checklist.stronger")
    if set(stronger) != {"additional_conditions"}:
        _fail("checklist.stronger has an unexpected field set")
    observed = stronger.get("additional_conditions")
    if not isinstance(observed, list):
        _fail("checklist.stronger.additional_conditions must be an array")
    expected = [dict(gap["required_condition"]) for gap in entry["gaps"]]
    if observed != expected:
        _fail(
            f"{entry['case_unit_id']}: stronger.additional_conditions must exactly equal "
            "the frozen packet stronger-gap projection"
        )
    markers = [gap["marker"] for gap in entry["gaps"]]
    return {
        "registry_file_sha256": REGISTRY_SHA256,
        "entry_semantic_sha256": entry["entry_semantic_sha256"],
        "source_basis_sha256": entry["source_basis_sha256"],
        "registered_test_registry_sha256": entry[
            "registered_test_registry_sha256"
        ],
        "gap_count": len(markers),
        "markers": markers,
        "required_conditions_sha256": sha256_object(expected),
        "stronger_exact_match": True,
        "non_scoring_alias_count": 0,
    }


__all__ = [
    "APPWORLD_DATA_VERSION",
    "APPWORLD_GIT_COMMIT",
    "AppWorldStrongerGapError",
    "PACKET_REGISTRY_SCHEMA",
    "REGISTRY_PATH",
    "REGISTRY_SCHEMA",
    "REGISTRY_SHA256",
    "REVIEW_POLICY_PATH",
    "appworld_gap_basis",
    "appworld_stronger_gap_marker",
    "frozen_stronger_gap_case_entry",
    "load_frozen_appworld_stronger_gap_registry",
    "packet_stronger_gap_payload",
    "parse_packet_stronger_gap_registry",
    "stronger_gap_case_entry",
    "validate_condition_without_marker",
    "validate_registry_case_entry",
    "validate_review_basis",
    "validate_review_receipt_inputs",
    "validate_stronger_gap_composition",
]
