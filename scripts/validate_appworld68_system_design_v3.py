#!/usr/bin/env python3
"""Fail-closed validator for the AppWorld test_normal-68 system-design-v3 bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO_ROOT / (
    "experiments/appworld_test_normal_68_system_design_v3_gpt54_high_v1"
)
PRIOR_STANDARD_ROOT = REPO_ROOT / (
    "experiments/appworld_test_normal_68_system_design_v2_gpt54_high_v1"
)
SOURCE_ROOT = REPO_ROOT / (
    "experiments/appworld_full_test_extension_v1_gpt56_strict_v3_lockfix_v6"
    "/case_packets/appworld"
)
SOURCE_DRAFT_ROOT = REPO_ROOT / (
    "experiments/appworld_full_test_extension_v1_gpt56_strict_v3_lockfix_v6"
    "/remote_draft_runs/appworld68_tn_gpt54_high_c34_v2_20260719/results"
)
MARKER_RE = re.compile(r"^(\[appworld_stronger_gap_[0-9]{3}_([0-9a-f]{12})\])\s+")
LINE_RE = re.compile(r"^L([1-9][0-9]*)(?:-L([1-9][0-9]*))?$")
JSON_TOKEN_RE = re.compile(r"\.([A-Za-z_][A-Za-z0-9_]*)|\[([0-9]+)\]")
EXPECTED_CONFLICT_GATE = {
    "review_scope": (
        "A separate record-level audit, independent of native and stronger "
        "evidence scoring."
    ),
    "mismatch_role": (
        "A released-label/native-verdict mismatch may be used as a review routing "
        "signal but is neither necessary nor sufficient for benchmark conflict."
    ),
    "confirmation_rule": (
        "Mark confirmed benchmark conflict only when retained artifacts and explicit "
        "source pointers establish that the original benchmark task, target "
        "construction, evaluator/oracle, or reward wiring/aggregation actually "
        "checked a different outcome from the benchmark's apparent claim."
    ),
}
EXPECTED_STRONGER_SEPARATION = (
    "Stronger results are scored and reported independently. Stronger F does not "
    "change native S/F/U. Neither stronger F alone nor native S together with "
    "stronger F is sufficient to establish benchmark conflict; only the independent "
    "benchmark-conflict audit gate may do so."
)
EXPECTED_NATIVE_SFU_RULE = (
    "Let each frozen registered test have an evidence status in {S, F, U}. Native "
    "S iff every registered test is S. Native F iff at least one registered test "
    "is F, regardless of unresolved remaining tests. Native U iff no registered "
    "test is F and at least one registered test is U."
)
EXPECTED_STRONGER_RULE = {
    "condition": {
        "S": (
            "All conjuncts in condition.text are established by the condition's "
            "scorer-visible retained evidence."
        ),
        "F": "At least one conjunct is established false by retained evidence.",
        "U": (
            "No conjunct is established false, but at least one necessary conjunct "
            "is unresolved because evidence is missing, incomplete, or non-decisive."
        ),
    },
    "aggregate": {
        "S": "Every stronger condition is S.",
        "F": "At least one stronger condition is F.",
        "U": "No stronger condition is F and at least one is U.",
    },
    "action_absence_boundary": (
        "For a condition about whether an action occurred, absence is F only when "
        "the retained action/API trace is established complete; otherwise it is U."
    ),
    "separation": EXPECTED_STRONGER_SEPARATION,
}
EXPECTED_VISIBILITY_CONTRACT = {
    "schema_version": "appworld_evidence_visibility_contract.v2",
    "known_before_run": True,
    "full_retained_record": {
        "rule": (
            "Preserve the benchmark execution artifacts, released evaluator label, "
            "complete TestTracker output, and evaluator report verbatim and immutably."
        ),
        "scorer_access": False,
    },
    "scorer_visible_non_verdict_evidence": {
        "projection_rule": (
            "Build an immutable scorer view with a fixed allowlist from the full "
            "retained record and frozen pre-run case sources."
        ),
        "criterion_and_target_basis": [
            "frozen_semantics/appworld_evaluator_semantics.a072b7a8.json",
            "official/specs.json",
            "official/ground_truth/evaluation.py",
            "official/ground_truth/test_data.json",
            "official/ground_truth/answer.json",
            "official/ground_truth/public_data.json",
            "official/ground_truth/private_data.json",
            "official/ground_truth/metadata.json",
            "official/dbs/**",
            "case-specific initial-state SQL column lists and evaluator model-field "
            "accesses in the official 19-file packet",
        ],
        "execution_evidence": [
            "retained submitted answer",
            "post-run database state or lossless start/end database diff",
            "API/action log",
            "environment/conversation trace",
            "LM/tool-call log",
            "verdict-free execution-status and termination evidence",
        ],
        "forbidden": [
            "released evaluator label or score",
            "TestTracker success, passes, failures, or num_tests output values",
            "evaluator report or component-evaluator output",
            "any summary, manifest, log field, reward, or aggregate that "
            "deterministically reveals a released result",
        ],
    },
    "non_scorer_released_results": {
        "rule": (
            "Only a non-scorer process may read these results after the native S/F/U "
            "verdict bytes and hash have been locked; they may never flow back to the "
            "scorer."
        ),
        "contents": [
            "released evaluator label",
            "complete TestTracker and evaluator outputs",
        ],
    },
    "native_verdict_rule": EXPECTED_NATIVE_SFU_RULE,
    "benchmark_conflict_gate": EXPECTED_CONFLICT_GATE,
    "formal_semantics_binding": {
        "descriptor": "frozen_semantics/appworld_evaluator_semantics.a072b7a8.json",
        "descriptor_sha256": (
            "f92952e8a35001848126397fc43f4b612ea607030c53deb783af57d93e624d9f"
        ),
        "scope_note": (
            "The descriptor pins the released AppWorld commit and evaluator.py source "
            "hash. The case packet additionally freezes each case evaluator, "
            "test_data, targets, and initial-state SQL column inventory."
        ),
    },
    "stronger_rule": EXPECTED_STRONGER_RULE,
}
EXPECTED_BASE_DRAFT_GENERATION = {
    "model": "gpt-5.4",
    "reasoning_effort": "high",
    "fast_mode": False,
    "requested_parallelism": 34,
    "source_results_root": (
        "experiments/appworld_full_test_extension_v1_gpt56_strict_v3_lockfix_v6/"
        "remote_draft_runs/appworld68_tn_gpt54_high_c34_v2_20260719/results"
    ),
}
EXPECTED_PIPELINE_INTEGRATION = {
    "status": "required_gates_not_implemented_by_this_asset_repair",
    "safe_to_score_with_unfiltered_reference_workspace_copy": False,
    "safe_to_score_with_current_reference_prompt": False,
    "known_reference_runner_gaps": [
        {
            "gate": "post_lock_released_result_join",
            "source": "neurips_ed_track_minimal/scripts/score_evidence_with_codex.py",
            "issue": (
                "The current runner resolves the released evaluator label before "
                "invoking the scorer instead of joining it only after the native "
                "verdict bytes and hash are locked."
            ),
        },
        {
            "gate": "allowlist_scorer_view",
            "source": "neurips_ed_track_minimal/scripts/score_evidence_with_codex.py",
            "issue": (
                "The current runner copies the complete evidence directory instead "
                "of constructing the contract's non-verdict allowlist."
            ),
        },
        {
            "gate": "independent_stronger_scoring",
            "source": (
                "neurips_ed_track_minimal/prompts/"
                "score_evidence_with_codex.prompt.md"
            ),
            "issue": (
                "The current prompt derives stronger F from native F and stronger U "
                "from native U instead of independently applying each locked stronger "
                "condition to retained evidence."
            ),
        },
        {
            "gate": "independent_benchmark_conflict_audit",
            "source": "neurips_ed_track_minimal/",
            "issue": (
                "No AppWorld record-level confirmed-conflict audit implements the "
                "retained-artifact plus explicit-source-pointer gate independently "
                "of mismatch and native/stronger verdict routing."
            ),
        },
    ],
    "required_next_gates": [
        "Move released-result resolution and comparison after the native verdict "
        "bytes and hash are locked.",
        "Implement and validate an allowlist-built non-verdict scorer view.",
        "Replace native-conditioned stronger verdict propagation with independent "
        "per-condition stronger S/F/U scoring.",
        "Implement an AppWorld record-level benchmark-conflict audit in which "
        "mismatch is neither necessary nor sufficient and confirmation requires "
        "retained-artifact and explicit source-pointer proof of a different checked "
        "outcome.",
    ],
}
EXPECTED_YAML_DERIVATION = {
    "authoritative_format": "checklist.json",
    "derived_format": "checklist.yaml",
    "renderer": "yq (https://github.com/mikefarah/yq/) version v4.50.1",
    "renderer_command": "yq -P -o=yaml . -",
    "renderer_binary_sha256": (
        "b431c4c63fe098ac2e856704178990697796438e4d2599dabb7dc5623bee873f"
    ),
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_object(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def parse_json_block(section: str, label: str) -> dict[str, Any]:
    match = re.search(r"```json\n(.*?)\n```", section, flags=re.DOTALL)
    if match is None:
        fail(f"{label}: JSON block missing")
    value = json.loads(match.group(1))
    if not isinstance(value, dict):
        fail(f"{label}: JSON block must be an object")
    return value


def parse_packet(
    packet: str, case_id: str
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    visibility_start = packet.index("### Artifact visibility and phase separation")
    semantics_start = packet.index("### Released evaluator semantic binding")
    native_start = packet.index("### Machine-verifiable native registry")
    stronger_start = packet.index("### Machine-verifiable stronger registry")
    source_start = packet.index("## Source Inventory")
    visibility = parse_json_block(
        packet[visibility_start:semantics_start], f"{case_id}: visibility"
    )
    semantics = parse_json_block(
        packet[semantics_start:native_start], f"{case_id}: evaluator semantics"
    )
    native = parse_json_block(packet[native_start:stronger_start], f"{case_id}: native")
    stronger = parse_json_block(packet[stronger_start:source_start], f"{case_id}: stronger")
    return visibility, semantics, native, stronger


def yaml_as_json(path: Path) -> Any:
    completed = subprocess.run(
        ["yq", "-o=json", ".", str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        fail(f"YAML parse failed for {path}: {completed.stderr.decode(errors='replace')}")
    return json.loads(completed.stdout)


def string_supports(checklist: dict[str, Any]) -> Iterable[str]:
    native = checklist["native"]
    for key in ("user_goal", "benchmark_success", "checked_by"):
        yield from native[key]["support"]
    for key in ("decisive_artifacts", "success_if", "fail_if", "undecided_if"):
        for item in native[key]:
            yield from item["support"]
    for condition in checklist["stronger"]["additional_conditions"]:
        yield from condition["support"]
        for artifact in condition["decisive_artifacts"]:
            yield from artifact["support"]


def validate_json_locator(path: Path, locator: str, case_id: str) -> None:
    if path.suffix == ".jsonl":
        fail(f"{case_id}: JSONL support must use an exact line range: {path}::{locator}")
    value: Any = json.loads(path.read_text(encoding="utf-8"))
    if not locator.startswith("$"):
        fail(f"{case_id}: malformed JSON locator: {path}::{locator}")
    position = 1
    for match in JSON_TOKEN_RE.finditer(locator, position):
        if match.start() != position:
            fail(f"{case_id}: unsupported JSON locator syntax: {path}::{locator}")
        key, index = match.groups()
        if key is not None:
            if not isinstance(value, dict) or key not in value:
                fail(f"{case_id}: JSON support field missing: {path}::{locator}")
            value = value[key]
        else:
            offset = int(index)
            if not isinstance(value, list) or offset >= len(value):
                fail(f"{case_id}: JSON support index missing: {path}::{locator}")
            value = value[offset]
        position = match.end()
    if position != len(locator):
        fail(f"{case_id}: unsupported JSON locator tail: {path}::{locator}")


def validate_support(raw_case: Path, pointer: str, case_id: str) -> None:
    if "::" not in pointer:
        fail(f"{case_id}: support pointer lacks locator: {pointer}")
    relative, locator = pointer.split("::", 1)
    if "*" in relative or "?" in relative or "[" in relative:
        fail(f"{case_id}: support path must be an exact inventory path: {pointer}")
    if relative == "official/ground_truth/answer.json":
        fail(f"{case_id}: answer target is not an admissible checklist support pointer")
    candidates = [raw_case / relative]
    if not candidates or any(not path.is_file() for path in candidates):
        fail(f"{case_id}: support path missing: {pointer}")
    for path in candidates:
        line_match = LINE_RE.fullmatch(locator)
        if line_match:
            start = int(line_match.group(1))
            end = int(line_match.group(2) or start)
            line_count = len(path.read_text(encoding="utf-8").splitlines())
            if start > end or end > line_count:
                fail(
                    f"{case_id}: support line range {locator} exceeds {relative} "
                    f"({line_count} lines)"
                )
        elif locator == "evaluate":
            if "def evaluate(" not in path.read_text(encoding="utf-8"):
                fail(f"{case_id}: evaluator support target missing: {pointer}")
        elif locator.startswith("$"):
            validate_json_locator(path, locator, case_id)
        else:
            fail(f"{case_id}: unsupported support locator: {pointer}")


def validate_marker(condition: dict[str, Any], index: int, case_id: str) -> None:
    text = condition["text"]
    match = MARKER_RE.match(text)
    if match is None:
        fail(f"{case_id}: condition {index} marker missing")
    marker, observed_digest = match.groups()
    expected_prefix = f"[appworld_stronger_gap_{index:03d}_"
    if not marker.startswith(expected_prefix):
        fail(f"{case_id}: condition {index} marker index drift")
    markerless = dict(condition)
    markerless["text"] = text[match.end():]
    expected_digest = sha256_object(markerless)[:12]
    if observed_digest != expected_digest:
        fail(f"{case_id}: condition {index} marker digest drift")


def validate_manifest(root: Path) -> dict[str, Any]:
    manifest_path = root / "repair_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual_paths = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path != manifest_path
    )
    records = manifest["files"]
    if [item["path"] for item in records] != actual_paths:
        fail("repair manifest file inventory differs from output tree")
    for record in records:
        path = root / record["path"]
        if record["size_bytes"] != path.stat().st_size or record["sha256"] != sha256_file(path):
            fail(f"repair manifest hash/size mismatch: {record['path']}")
    if manifest["files_sha256"] != sha256_object(records):
        fail("repair manifest aggregate file hash mismatch")
    if manifest["file_count_excluding_this_manifest"] != len(records):
        fail("repair manifest file count mismatch")
    return manifest


def validate(root: Path) -> dict[str, Any]:
    source_module_root = str(REPO_ROOT / "src")
    if source_module_root not in sys.path:
        sys.path.insert(0, source_module_root)
    from evidence_system.contracts.appworld_support_pointers import (  # noqa: PLC0415
        official_pointer_resolves,
    )

    if not root.is_dir():
        fail(f"bundle root missing: {root}")
    symlinks = [path for path in root.rglob("*") if path.is_symlink()]
    if symlinks:
        fail(f"bundle contains symlinks: {symlinks[:3]}")
    manifest = validate_manifest(root)
    expected_repair_validation = {
        "source_only_outcome_blind": True,
        "old_namespace_untouched": True,
        "packet_draft_exact_projection": True,
        "prior_standard_draft_bytes_preserved_case_count": 68,
        "updated_packet_contract_case_count": 68,
        "native_artifact_contract_case_count": 68,
        "native_explicit_sfu_case_count": 68,
        "stronger_counts": {
            "gap_cases": 34,
            "no_gap_cases": 34,
            "conditions": 44,
        },
    }
    if (
        set(manifest)
        != {
            "schema_version",
            "created_date",
            "case_count",
            "file_count_excluding_this_manifest",
            "files",
            "files_sha256",
            "validation",
        }
        or manifest.get("created_date") != "2026-07-19"
        or manifest.get("case_count") != 68
        or manifest.get("schema_version")
        != "appworld_test_normal_68_repair_manifest.v2_standard_update"
        or manifest.get("validation") != expected_repair_validation
    ):
        fail("updated-standard repair manifest metadata differs")
    visibility_file = json.loads(
        (root / "artifact_visibility_contract.json").read_text(encoding="utf-8")
    )
    if visibility_file != EXPECTED_VISIBILITY_CONTRACT:
        fail("artifact visibility contract differs from the updated standard")
    if visibility_file.get("schema_version") != "appworld_evidence_visibility_contract.v2":
        fail("updated visibility schema missing")
    if "post_score_comparison_rule" in visibility_file:
        fail("stale mismatch-triggered post-score comparison rule remains")
    if "comparison_only_released_results" in visibility_file:
        fail("stale comparison-only released-results field remains")
    if visibility_file.get("benchmark_conflict_gate") != EXPECTED_CONFLICT_GATE:
        fail("independent benchmark-conflict gate differs from updated standard")
    if (
        visibility_file.get("stronger_rule", {}).get("separation")
        != EXPECTED_STRONGER_SEPARATION
    ):
        fail("updated independent stronger/conflict rule differs")
    forbidden = visibility_file.get("scorer_visible_non_verdict_evidence", {}).get(
        "forbidden", []
    )
    if not all(
        any(term in item for item in forbidden)
        for term in ("released evaluator label", "TestTracker", "component-evaluator")
    ):
        fail("scorer non-verdict projection omits a required result-leakage ban")
    semantics_path = root / "frozen_semantics/appworld_evaluator_semantics.a072b7a8.json"
    semantics_file_sha = sha256_file(semantics_path)
    if semantics_file_sha != "f92952e8a35001848126397fc43f4b612ea607030c53deb783af57d93e624d9f":
        fail("frozen evaluator-semantics descriptor hash drift")
    evaluator_semantics = json.loads(semantics_path.read_text(encoding="utf-8"))
    registry_path = root / "stronger_registry.json"
    stronger_registry = json.loads(registry_path.read_text())
    if (
        set(stronger_registry)
        != {
            "schema_version",
            "review_date",
            "review_mode",
            "scope",
            "review_rule",
            "condition_verdict_rule",
            "cases",
        }
        or stronger_registry.get("schema_version")
        != "appworld_stronger_gap_registry.v4_system_design_v3"
        or stronger_registry.get("review_date") != "2026-07-19"
        or stronger_registry.get("review_mode") != "source_only_outcome_blind"
        or stronger_registry.get("scope")
        != {
            "dataset_name": "test_normal",
            "case_count": 68,
            "action_case_count": 27,
            "explicitly_deleted_unsupported_case_count": 5,
        }
        or stronger_registry.get("review_rule")
        != (
            "Record only concrete case-specific official task, user-intent, or "
            "policy obligations not fully operationalized by the released evaluator/"
            "oracle. Exclude reviewer preferences and all agent outcomes or released "
            "results."
        )
        or stronger_registry.get("condition_verdict_rule")
        != visibility_file.get("stronger_rule")
    ):
        fail("updated stronger registry schema/separation rule differs")
    registry_canonical_sha = sha256_object(stronger_registry)
    registry_file_sha = sha256_file(registry_path)
    registry_by_id = {item["case_unit_id"]: item for item in stronger_registry["cases"]}

    results = sorted((root / "results").glob("*/checklist.json"))
    packets = sorted((root / "case_packets/appworld").glob("*/case_packet.md"))
    freezes = sorted((root / "claim_freeze/checklists").glob("*/checklist.json"))
    if not (len(results) == len(packets) == len(freezes) == 68):
        fail("expected exactly 68 results, packets, and frozen checklists")
    case_ids = [path.parent.name for path in results]
    if len(set(case_ids)) != 68 or set(registry_by_id) != set(case_ids):
        fail("case ID closure mismatch")

    condition_count = 0
    gap_count = 0
    registered_test_count = 0
    support_pointer_count = 0
    support_pointer_occurrence_count = 0
    raw_file_count = 0
    for result_path in results:
        case_id = result_path.parent.name
        checklist = json.loads(result_path.read_text(encoding="utf-8"))
        repair_record = json.loads(
            (result_path.parent / "repair_record.json").read_text(encoding="utf-8")
        )
        if (
            repair_record.get("schema_version")
            != "appworld_checklist_repair_record.v2_standard_update"
            or repair_record.get("repair_mode")
            != "source_only_outcome_blind_updated_standard_refreeze"
            or repair_record.get("case_unit_id") != case_id
            or repair_record.get("dataset_name") != "test_normal"
            or set(repair_record)
            != {
                "schema_version",
                "case_unit_id",
                "dataset_name",
                "repair_mode",
                "source",
                "prior_standard",
                "output",
                "outcome_or_released_result_inputs_read",
            }
        ):
            fail(f"{case_id}: updated-standard repair record schema/mode differs")
        if repair_record["outcome_or_released_result_inputs_read"] != []:
            fail(f"{case_id}: repair record declares outcome/result inputs")
        prior_result_dir = PRIOR_STANDARD_ROOT / "results" / case_id
        prior = repair_record.get("prior_standard", {})
        if (
            set(prior)
            != {
                "bundle_relative_path",
                "checklist_json_sha256",
                "checklist_yaml_sha256",
                "case_specific_content_changed",
            }
            or prior.get("bundle_relative_path")
            != PRIOR_STANDARD_ROOT.relative_to(REPO_ROOT).as_posix()
            or prior.get("case_specific_content_changed") is not False
            or prior.get("checklist_json_sha256")
            != sha256_file(prior_result_dir / "checklist.json")
            or prior.get("checklist_yaml_sha256")
            != sha256_file(prior_result_dir / "checklist.yaml")
            or result_path.read_bytes()
            != (prior_result_dir / "checklist.json").read_bytes()
            or result_path.with_suffix(".yaml").read_bytes()
            != (prior_result_dir / "checklist.yaml").read_bytes()
        ):
            fail(f"{case_id}: case-specific draft bytes differ from prior standard")
        source = repair_record.get("source", {})
        expected_source_paths = {
            "source_checklist_path": SOURCE_DRAFT_ROOT / case_id / "checklist.json",
            "source_packet_path": SOURCE_ROOT / case_id / "case_packet.md",
        }
        if set(source) != {
            "source_checklist_path",
            "source_checklist_sha256",
            "source_packet_path",
            "source_packet_sha256",
            "official_source_manifest_sha256",
        }:
            fail(f"{case_id}: source freeze fields differ")
        for path_key, source_path in expected_source_paths.items():
            recorded_path = source.get(path_key)
            if (
                recorded_path != source_path.relative_to(REPO_ROOT).as_posix()
                or Path(recorded_path).is_absolute()
                or ".." in Path(recorded_path).parts
                or not source_path.is_file()
                or source.get(path_key.replace("_path", "_sha256"))
                != sha256_file(source_path)
            ):
                fail(f"{case_id}: source freeze binding drift: {path_key}")
        if source.get("official_source_manifest_sha256") != sha256_file(
            SOURCE_ROOT / case_id / "raw_case_manifest.json"
        ):
            fail(f"{case_id}: official source-manifest hash differs")
        output = repair_record.get("output", {})
        if set(output) != {
            "checklist_json_sha256",
            "checklist_yaml_sha256",
            "case_packet_sha256",
            "native_registry_canonical_json_sha256",
            "stronger_condition_ids",
        }:
            fail(f"{case_id}: repair-record output fields differ")
        if output["checklist_json_sha256"] != sha256_file(result_path):
            fail(f"{case_id}: repair-record JSON hash differs")
        if output["checklist_yaml_sha256"] != sha256_file(
            result_path.with_suffix(".yaml")
        ):
            fail(f"{case_id}: repair-record YAML hash differs")
        if output["stronger_condition_ids"] != [
            item["id"] for item in checklist["stronger"]["additional_conditions"]
        ]:
            fail(f"{case_id}: repair-record stronger condition IDs differ")
        if yaml_as_json(result_path.with_suffix(".yaml")) != checklist:
            fail(f"{case_id}: YAML and JSON checklist values differ")
        if (root / "claim_freeze/checklists" / case_id / "checklist.json").read_bytes() != result_path.read_bytes():
            fail(f"{case_id}: frozen JSON differs from result JSON")
        if (
            root / "claim_freeze/checklists" / case_id / "checklist.yaml"
        ).read_bytes() != result_path.with_suffix(".yaml").read_bytes():
            fail(f"{case_id}: frozen YAML differs from result YAML")

        packet_path = root / "case_packets/appworld" / case_id / "case_packet.md"
        packet = packet_path.read_text(encoding="utf-8")
        if output["case_packet_sha256"] != sha256_file(packet_path):
            fail(f"{case_id}: repair-record packet hash differs")
        packet_visibility, packet_semantics, packet_native, packet_stronger = parse_packet(
            packet, case_id
        )
        for stale in (
            "Any released-label/native-verdict mismatch enters separate record-level review",
            "Stronger F does not change native S/F/U and never establishes benchmark conflict",
            "Stronger results are scored and reported separately and never imply benchmark conflict",
        ):
            if stale in packet:
                fail(f"{case_id}: stale global policy remains in packet: {stale}")
        if packet_visibility != visibility_file:
            fail(f"{case_id}: embedded visibility contract differs")
        if packet_semantics != evaluator_semantics:
            fail(f"{case_id}: embedded evaluator-semantics descriptor differs")
        if packet_native["required_native"] != checklist["native"]:
            fail(f"{case_id}: packet native registry differs from checklist")
        if output["native_registry_canonical_json_sha256"] != sha256_object(
            packet_native
        ):
            fail(f"{case_id}: repair-record native registry hash differs")
        expected_conditions = [
            item["required_condition"] for item in packet_stronger["case"]["gaps"]
        ]
        if expected_conditions != checklist["stronger"]["additional_conditions"]:
            fail(f"{case_id}: packet stronger registry differs from checklist")
        if (
            packet_stronger["registry_canonical_json_sha256"] != registry_canonical_sha
            or packet_stronger["registry_file_sha256"] != registry_file_sha
        ):
            fail(f"{case_id}: packet stronger registry hash differs")
        if packet_stronger["case"] != registry_by_id[case_id]:
            fail(f"{case_id}: packet stronger case entry differs from registry")
        registry_case = packet_stronger["case"]
        if (
            set(registry_case)
            != {
                "case_unit_id",
                "dataset_name",
                "review_disposition",
                "native_registry_canonical_json_sha256",
                "gaps",
            }
            or registry_case.get("case_unit_id") != case_id
            or registry_case.get("dataset_name") != "test_normal"
            or registry_case.get("review_disposition")
            not in {
                "reviewed_unchanged_source_supported",
                "reviewed_repaired_source_supported",
                "reviewed_no_gap",
            }
            or registry_case.get("native_registry_canonical_json_sha256")
            != sha256_object(packet_native)
            or any(
                set(gap) != {"index", "marker", "required_condition"}
                or gap.get("index") != index
                or gap.get("marker")
                != MARKER_RE.match(gap["required_condition"]["text"]).group(1)
                for index, gap in enumerate(registry_case["gaps"], start=1)
            )
        ):
            fail(f"{case_id}: stronger registry case provenance differs")
        if (
            packet_stronger.get("schema_version")
            != "appworld_packet_stronger_gap_registry.v4_system_design_v3"
            or packet_stronger.get("condition_verdict_rule", {}).get("separation")
            != EXPECTED_STRONGER_SEPARATION
            or packet_native.get("schema_version")
            != "appworld_packet_native_registry.v4_system_design_v3"
        ):
            fail(f"{case_id}: packet updated-standard schema/rules differ")

        conditions = checklist["stronger"]["additional_conditions"]
        condition_count += len(conditions)
        gap_count += bool(conditions)
        registered_test_count += len(checklist["native"]["success_if"])
        if len(checklist["native"]["success_if"]) != len(checklist["native"]["fail_if"]):
            fail(f"{case_id}: native pass/fail registry length differs")
        if "official TestTracker results" in json.dumps(checklist, ensure_ascii=False):
            fail(f"{case_id}: old decisive TestTracker dependency remains")
        if "Native S iff every registered test is S" not in json.dumps(checklist["native"]):
            fail(f"{case_id}: explicit native S/F/U formula missing")
        for index, item in enumerate(conditions, start=1):
            validate_marker(item, index, case_id)

        raw_case = root / "case_packets/appworld" / case_id / "raw_case"
        raw_manifest = json.loads(
            (
                root
                / "case_packets/appworld"
                / case_id
                / "raw_case_manifest.json"
            ).read_text(encoding="utf-8")
        )
        official_inventory = set(raw_manifest["packet_files"])
        source_raw = SOURCE_ROOT / case_id / "raw_case"
        new_raw_paths = sorted(path.relative_to(raw_case) for path in raw_case.rglob("*") if path.is_file())
        old_raw_paths = sorted(path.relative_to(source_raw) for path in source_raw.rglob("*") if path.is_file())
        if new_raw_paths != old_raw_paths or len(new_raw_paths) != 19:
            fail(f"{case_id}: official raw source inventory differs or is not 19 files")
        for relative in new_raw_paths:
            if (raw_case / relative).read_bytes() != (source_raw / relative).read_bytes():
                fail(f"{case_id}: raw source bytes differ: {relative}")
        raw_file_count += len(new_raw_paths)

        source_packet = (SOURCE_ROOT / case_id / "case_packet.md").read_text(encoding="utf-8")
        if packet[packet.index("## Source Inventory"):] != source_packet[
            source_packet.index("## Source Inventory"):
        ]:
            fail(f"{case_id}: packet official source tail differs from source packet")

        seen_supports = set(string_supports(checklist))
        for pointer in sorted(seen_supports):
            validate_support(raw_case, pointer, case_id)
        all_supports = list(string_supports(checklist))
        for pointer in all_supports:
            if not official_pointer_resolves(
                task_dir=raw_case / "official",
                pointer=pointer,
                inventory_paths=official_inventory,
            ):
                fail(f"{case_id}: repository-native support resolver rejected {pointer}")
        support_pointer_count += len(seen_supports)
        support_pointer_occurrence_count += len(all_supports)

    if (gap_count, 68 - gap_count, condition_count, registered_test_count) != (34, 34, 44, 469):
        fail("cohort semantic counts drift")
    freeze_manifest = json.loads(
        (root / "claim_freeze/freeze_manifest.json").read_text(encoding="utf-8")
    )
    freeze_records = freeze_manifest["records"]
    if (
        set(freeze_manifest)
        != {
            "schema_version",
            "created_date",
            "case_count",
            "lock_boundary",
            "records",
            "records_sha256",
        }
        or freeze_manifest.get("schema_version")
        != "appworld_pre_outcome_checklist_freeze.v2_standard_update"
        or freeze_manifest.get("created_date") != "2026-07-19"
        or freeze_manifest.get("lock_boundary")
        != (
            "Before access to agent outcomes, per-record released evaluator labels, "
            "or component evaluator results."
        )
        or freeze_manifest["case_count"] != 68
        or len(freeze_records) != 68
        or [item.get("case_unit_id") for item in freeze_records] != case_ids
        or any(
            set(item)
            != {
                "case_unit_id",
                "checklist_json_sha256",
                "checklist_yaml_sha256",
                "case_packet_sha256",
            }
            for item in freeze_records
        )
        or freeze_manifest["records_sha256"] != sha256_object(freeze_records)
    ):
        fail("freeze manifest record hash mismatch")
    for record in freeze_records:
        case_id = record["case_unit_id"]
        expected = {
            "checklist_json_sha256": sha256_file(
                root / "claim_freeze/checklists" / case_id / "checklist.json"
            ),
            "checklist_yaml_sha256": sha256_file(
                root / "claim_freeze/checklists" / case_id / "checklist.yaml"
            ),
            "case_packet_sha256": sha256_file(
                root / "case_packets/appworld" / case_id / "case_packet.md"
            ),
        }
        if any(record[key] != value for key, value in expected.items()):
            fail(f"{case_id}: freeze record points to different bytes")

    experiment_manifest = json.loads(
        (root / "experiment_manifest.json").read_text(encoding="utf-8")
    )
    expected_scope = {
        "benchmark": "AppWorld",
        "dataset_name": "test_normal",
        "case_count": 68,
        "case_ids": case_ids,
        "case_ids_sha256": sha256_object(case_ids),
        "registered_test_count": registered_test_count,
    }
    expected_repair = {
        "mode": "deterministic_source_only_outcome_blind_standard_update",
        "prior_standard_bundle": PRIOR_STANDARD_ROOT.relative_to(REPO_ROOT).as_posix(),
        "case_specific_draft_content_revalidated_case_count": 68,
        "case_specific_draft_content_changed_case_count": 0,
        "packet_global_contract_changed_case_count": 68,
        "native_artifact_contract_preserved_case_count": 68,
        "native_explicit_sfu_rule_preserved_case_count": 68,
        "stronger_condition_content_changed_case_count": 0,
        "stronger_reviewed_prior_action_case_count": 27,
        "stronger_gap_case_count": gap_count,
        "stronger_no_gap_case_count": 68 - gap_count,
        "stronger_condition_count": condition_count,
        "old_frozen_namespace_mutated": False,
        "outcome_or_released_result_inputs_read": [],
    }
    if (
        set(experiment_manifest)
        != {
            "schema_version",
            "status",
            "created_date",
            "scope",
            "base_draft_generation",
            "repair",
            "pipeline_integration",
            "hash_canonicalization",
            "artifact_visibility_contract_canonical_json_sha256",
            "artifact_visibility_contract_file_sha256",
            "stronger_registry_canonical_json_sha256",
            "stronger_registry_file_sha256",
            "frozen_evaluator_semantics_file_sha256",
            "yaml_derivation",
        }
        or experiment_manifest.get("status")
        != "source_only_updated_standard_refrozen"
        or experiment_manifest.get("schema_version")
        != "appworld_test_normal_68_system_design_v3.v1"
        or experiment_manifest.get("created_date") != "2026-07-19"
        or experiment_manifest.get("scope") != expected_scope
        or experiment_manifest.get("base_draft_generation")
        != EXPECTED_BASE_DRAFT_GENERATION
        or experiment_manifest.get("repair") != expected_repair
        or experiment_manifest.get("pipeline_integration")
        != EXPECTED_PIPELINE_INTEGRATION
        or experiment_manifest.get("hash_canonicalization")
        != "UTF-8 JSON, ensure_ascii=true, sort_keys=true, separators=(',', ':')"
        or experiment_manifest["scope"]["case_ids_sha256"]
        != "2b54ce295ac44589ff9ceb689ea52daf69c64dfb0c76118db34af2b3e1da7c96"
        or experiment_manifest["artifact_visibility_contract_canonical_json_sha256"]
        != sha256_object(visibility_file)
        or experiment_manifest["artifact_visibility_contract_file_sha256"]
        != sha256_file(root / "artifact_visibility_contract.json")
        or experiment_manifest["stronger_registry_canonical_json_sha256"]
        != registry_canonical_sha
        or experiment_manifest["stronger_registry_file_sha256"] != registry_file_sha
        or experiment_manifest["frozen_evaluator_semantics_file_sha256"]
        != semantics_file_sha
        or experiment_manifest.get("yaml_derivation") != EXPECTED_YAML_DERIVATION
    ):
        fail("experiment manifest semantic/hash binding drift")

    return {
        "status": "ok",
        "root": str(root),
        "case_count": 68,
        "prior_standard_draft_byte_identical_case_count": 68,
        "updated_packet_contract_case_count": 68,
        "registered_test_count": registered_test_count,
        "stronger_gap_case_count": gap_count,
        "stronger_no_gap_case_count": 68 - gap_count,
        "stronger_condition_count": condition_count,
        "unique_support_pointer_occurrence_count": support_pointer_count,
        "repository_resolved_support_pointer_occurrence_count": (
            support_pointer_occurrence_count
        ),
        "byte_identical_official_raw_file_count": raw_file_count,
        "manifest_files_sha256": manifest["files_sha256"],
        "stronger_registry_canonical_json_sha256": registry_canonical_sha,
        "stronger_registry_file_sha256": registry_file_sha,
        "frozen_evaluator_semantics_file_sha256": semantics_file_sha,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    report = validate(args.root.expanduser().resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
