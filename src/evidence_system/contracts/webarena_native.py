"""Deterministic native-claim compiler for WebArena-Verified v1.2.3.

The canonical case packets contain private evaluator configuration and are never
model-visible.  This module compiles those frozen sources into two pre-run
artifacts:

* an ``evidence_contract/v1`` draft used by the execution scheduler; and
* a ``case_checklist_v1`` draft used by the evidence scorer.

Compilation is deliberately deterministic.  A machine-validation lock proves
that every evaluator configuration is represented and that the official
``TaskEvalResult.create`` all-evaluator conjunction is preserved.  It is not a
human review.  Formal locked artifacts are emitted either after an exact,
hash-bound set of human sign-offs or under a separate, explicit operator
machine-only waiver.  The waiver path never claims a human review, reviewer
identity, signature, or per-case human sign-off.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from evidence_system.contracts.common import contract_content_hash, stamp_contract_hash
from evidence_system.core.schemas import validate_object


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DOMAIN = "webarena_verified"
BENCHMARK_VERSION = "v1.2.3"
EXPECTED_CASES = 812
EXPECTED_TASK_IDS = tuple(str(value) for value in range(EXPECTED_CASES))
COMPILER_ID = "webarena_verified_native_claim_compiler"
COMPILER_VERSION = "1.0.0"
IR_SCHEMA_VERSION = "webarena_verified_native_claim_ir/v1"
MACHINE_REVIEW_SCHEMA_VERSION = "webarena_verified_native_claim_machine_review/v1"
INPUT_LOCK_SCHEMA_VERSION = "webarena_verified_native_claim_input_lock/v1"
INDEX_SCHEMA_VERSION = "webarena_verified_native_claim_index/v1"
ACCEPTANCE_SCHEMA_VERSION = "webarena_verified_native_claim_acceptance/v1"
HUMAN_SIGNOFF_SCHEMA_VERSION = "webarena_verified_native_claim_human_signoff/v1"
MACHINE_LOCK_SCHEMA_VERSION = "webarena_verified_native_claim_machine_lock/v1"
OPERATOR_WAIVER_SCHEMA_VERSION = "webarena_verified_operator_waiver/v1"
OPERATOR_WAIVER_LOCK_SCHEMA_VERSION = "webarena_verified_operator_waiver_lock/v1"
POLICY_LOCK_SCHEMA_VERSION = "webarena_verified_native_claim_policy_lock/v1"
OPERATOR_WAIVER_SCOPE = "webarena_verified_v1.2.3_full_812_machine_only"
OPERATOR_WAIVER_BASIS = "operator_machine_only_waiver"

DEFAULT_SOURCE_BUNDLE = Path(
    "experiments/evidence_contracts/source_bundles/webarena_verified_full_812_source_bundle.json"
)
DEFAULT_STEP19_MANIFEST = Path("experiments/step19/webarena_verified_full_812_manifest.json")
DEFAULT_PACKET_INDEX = Path("experiments/case_packets/webarena_verified/index.json")
DEFAULT_OUTPUT_ROOT = Path("experiments/step20/webarena_verified/native_claims")
CHECKLIST_SCHEMA = Path("neurips_ed_track_minimal/schemas/case_checklist.schema.json")
HUMAN_SIGNOFF_SCHEMA = Path("schemas/webarena_verified_native_claim_human_signoff.schema.json")
OPERATOR_WAIVER_SCHEMA = Path("schemas/webarena_verified_operator_waiver.schema.json")

EXPECTED_EXECUTION_BINDING = {
    "agents": [
        {
            "agent_id": "Agent A",
            "model": "openai/gpt-5.4",
            "server_id": "webarena-gpt54-ord",
            "ssh_host": "45.76.67.186",
            "ssh_user": "root",
            "ssh_host_ed25519_fingerprint": "SHA256:ObgyygktdU2dhYU1CA+rf9PSgmLkv47xxN9FnL1+iYo",
        },
        {
            "agent_id": "Agent B",
            "model": "anthropic/claude-opus-4.7",
            "server_id": "webarena-claude47-ord",
            "ssh_host": "66.42.108.130",
            "ssh_user": "root",
            "ssh_host_ed25519_fingerprint": "SHA256:3hhiish7icTf+jeSmfN6anqb37YhX3qwnhZKloHuPMM",
        },
        {
            "agent_id": "Agent C",
            "model": "deepseek/deepseek-v4-pro",
            "server_id": "webarena-deepseek-v4pro-ord",
            "ssh_host": "149.28.79.226",
            "ssh_user": "root",
            "ssh_host_ed25519_fingerprint": "SHA256:r01stp+Wa+34Y/dxjscF+LpB47u9fuB/3h4MuF/K3AE",
        },
    ],
    "reset_policy": "recreate_task_sites_from_digest_v1",
    "pilot_record_slots": 24,
    "full_record_slots": 2436,
    "launch_order": "pilot_must_pass_before_full",
}

OFFICIAL_COMMIT = "6473f72db5dcefc97b5725b59e734504edc28a21"
OFFICIAL_EVALUATOR_CHECKSUM = "35c3385b1db4b3378657589f95f50defd4234bd36e5b93d44733fd561b01db4e"
OFFICIAL_SOURCE_SHA256 = "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
EXPECTED_SOURCE_BUNDLE_SHA256 = "3009541e335bb309bccbe37f3c54581e5b3024bc2d78e35f16ba9392c3e2bd6b"
EXPECTED_STEP19_MANIFEST_SHA256 = "86671e213ef0149f98240830ef20a2c38585c3c8d0529e6ae77d9d36d6597c35"
EXPECTED_PACKET_INDEX_SHA256 = "493227371de6763f9e5f1b0df0ecfb0eee30e4a1ebcaa9a60725195f2c1a5c21"
EXPECTED_PACKET_INDEX_CORE_SHA256 = "e845176df55bc69381a19804b68ddf5a96427120de841cfb74b6937ab0ba0e2d"
EXPECTED_PACKET_INDEX_AGENT_INPUT_TREE_SHA256 = (
    "98f4f404cae6e794bd2fa1d0c152d43b7fa5d6ee5bffea143a0c9c39ddd4c975"
)
OFFICIAL_SEMANTIC_SOURCE_HASHES = {
    "official/src/webarena_verified/api/internal/evaluator.py":
        "e4d390700985a5921e6a86d1782a4c9803c85728b38a6cfd16ad6e9aebaec714",
    "official/src/webarena_verified/core/evaluation/evaluators/agent_response_evaluator.py":
        "8ae2caf59c6fafecf4ec259ea67bf79d27f19c7fcbdc33a312cea730c4e54c31",
    "official/src/webarena_verified/core/evaluation/evaluators/network_event_evaluator.py":
        "74bc94874541192d18c6dd221f26599d5279606effc55cf5c059ddce2516c441",
    "official/src/webarena_verified/core/evaluation/value_comparator.py":
        "330d6e999e80e45a47ae569cf26c2d32459b17ab93383b6dd1d7676fe2c0257b",
    "official/src/webarena_verified/core/evaluation/value_normalizer.py":
        "3ad6bf5a3f9630714fea69943aede7e616d2fc9926264e590aacbd4498d41b62",
    "official/src/webarena_verified/types/eval.py":
        "f9c2a2aa4fcc839232f3cab88c9618b601c050e2d46b97630f96664257e95140",
}

EVALUATOR_POINTER = (
    "official/src/webarena_verified/api/internal/evaluator.py::"
    "WebArenaVerifiedEvaluator.evaluate_task"
)
TASK_RESULT_POINTER = "official/src/webarena_verified/types/eval.py::TaskEvalResult.create"
AGENT_RESPONSE_POINTER = (
    "official/src/webarena_verified/core/evaluation/evaluators/"
    "agent_response_evaluator.py::AgentResponseEvaluator"
)
NETWORK_EVENT_POINTER = (
    "official/src/webarena_verified/core/evaluation/evaluators/"
    "network_event_evaluator.py::NetworkEventEvaluator"
)


class WebArenaNativeClaimError(RuntimeError):
    """Raised when the native-claim lifecycle must fail closed."""


def canonical_bytes(value: Any, *, ensure_ascii: bool = False) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=ensure_ascii,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def object_sha256(value: Any, *, ensure_ascii: bool = False) -> str:
    return hashlib.sha256(canonical_bytes(value, ensure_ascii=ensure_ascii)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PACKAGE_ROOT / path


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(PACKAGE_ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise WebArenaNativeClaimError(f"path escapes repository root: {path}") from exc


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WebArenaNativeClaimError(f"cannot load JSON {path}: {exc}") from exc


def json_file_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_file_bytes(payload))


def _write_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )


def _write_sha256_sidecar(path: Path) -> None:
    path.with_suffix(path.suffix + ".sha256").write_text(
        f"{file_sha256(path)}  {path.name}\n",
        encoding="utf-8",
    )


def _parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise WebArenaNativeClaimError(f"{field} must be a nonempty ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise WebArenaNativeClaimError(f"{field} is not a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise WebArenaNativeClaimError(f"{field} must include a timezone offset")
    return parsed


def _safe_output_path(output_root: Path, relative: str, *, package_root: str | None = None) -> Path:
    value = Path(relative)
    if value.is_absolute():
        candidate = value.resolve()
    elif package_root is not None:
        prefix = Path(package_root)
        try:
            within = value.relative_to(prefix)
        except ValueError as exc:
            raise WebArenaNativeClaimError(
                f"repository-relative output path is outside declared package root: {relative}"
            ) from exc
        candidate = (output_root / within).resolve()
    else:
        candidate = (PACKAGE_ROOT / value).resolve()
    try:
        candidate.relative_to(output_root.resolve())
    except ValueError as exc:
        raise WebArenaNativeClaimError(f"output path escapes native-claim root: {relative}") from exc
    if candidate.is_symlink():
        raise WebArenaNativeClaimError(f"symlink output is forbidden: {relative}")
    return candidate


def agent_input_tree_sha256(packet_root: Path) -> str:
    entries: list[dict[str, str]] = []
    for task_id in EXPECTED_TASK_IDS:
        path = packet_root / task_id / "agent_input.json"
        if not path.is_file() or path.is_symlink():
            raise WebArenaNativeClaimError(f"missing or symlinked agent_input.json for task {task_id}")
        entries.append({"case_unit_id": task_id, "sha256": file_sha256(path)})
    return object_sha256(entries)


def compiler_identity() -> dict[str, str]:
    path = Path(__file__).resolve()
    return {
        "id": COMPILER_ID,
        "version": COMPILER_VERSION,
        "source_path": _repo_relative(path),
        "source_sha256": file_sha256(path),
    }


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise WebArenaNativeClaimError(f"{label} must be a mapping")
    return dict(value)


def _require_sequence(value: Any, label: str) -> list[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise WebArenaNativeClaimError(f"{label} must be a sequence")
    return list(value)


def _validate_agent_input(
    path: Path,
    task: Mapping[str, Any],
    *,
    resolved_start_urls: Sequence[Any],
    expected_file_sha256: str,
) -> str:
    payload = _require_mapping(_load_json(path), str(path))
    expected_keys = {"intent", "intent_template_id", "sites", "start_urls", "task_id"}
    if set(payload) != expected_keys:
        raise WebArenaNativeClaimError(
            f"{path} model-visible keys drifted: expected={sorted(expected_keys)} actual={sorted(payload)}"
        )
    expected = {
        "intent": task.get("intent"),
        "intent_template_id": task.get("intent_template_id"),
        "sites": task.get("sites") or [],
        "start_urls": list(resolved_start_urls),
        "task_id": task.get("task_id"),
    }
    for field in ("intent", "intent_template_id", "sites", "start_urls", "task_id"):
        if payload.get(field) != expected[field]:
            raise WebArenaNativeClaimError(f"{path} field {field} does not match the official task")
    if len(payload["start_urls"]) != len(task.get("start_urls") or []):
        raise WebArenaNativeClaimError(f"{path} resolved start URL count does not match official templates")
    for url in payload["start_urls"]:
        if not isinstance(url, str) or not url.startswith(("http://", "https://")) or "__" in url:
            raise WebArenaNativeClaimError(f"{path} contains unresolved or invalid start URL: {url!r}")
    forbidden = {"eval", "expected", "gold", "answer", "revision"}
    if forbidden.intersection(payload):
        raise WebArenaNativeClaimError(f"{path} leaks controller-only fields")
    observed = file_sha256(path)
    if observed != expected_file_sha256:
        raise WebArenaNativeClaimError(f"{path} hash differs from the frozen controller packet")
    return observed


def _validate_semantic_sources(raw_root: Path, raw_manifest: Mapping[str, Any], *, has_network: bool) -> None:
    hashes = _require_mapping(raw_manifest.get("sha256_per_file"), "raw manifest sha256_per_file")
    required = [
        key
        for key in OFFICIAL_SEMANTIC_SOURCE_HASHES
        if has_network or "network_event_evaluator.py" not in key
    ]
    for relative in required:
        expected = OFFICIAL_SEMANTIC_SOURCE_HASHES[relative]
        if hashes.get(relative) != expected:
            raise WebArenaNativeClaimError(
                f"official semantic source hash drift for {relative}: {hashes.get(relative)!r}"
            )
        path = raw_root / relative
        if not path.is_file() or path.is_symlink() or file_sha256(path) != expected:
            raise WebArenaNativeClaimError(f"official semantic source file mismatch: {path}")


def _validate_all_raw_files(raw_root: Path, raw_manifest: Mapping[str, Any]) -> None:
    hashes = _require_mapping(raw_manifest.get("sha256_per_file"), "raw manifest sha256_per_file")
    for relative, expected in sorted(hashes.items()):
        path = raw_root / str(relative)
        if not path.is_file() or path.is_symlink():
            raise WebArenaNativeClaimError(f"raw-case source missing or symlinked: {path}")
        if file_sha256(path) != expected:
            raise WebArenaNativeClaimError(f"raw-case source hash mismatch: {path}")


def _evaluator_semantics(entry: Mapping[str, Any], index: int) -> dict[str, Any]:
    name = entry.get("evaluator")
    pointer = f"derived/task.json::eval/{index}"
    if name == "AgentResponseEvaluator":
        expected = _require_mapping(entry.get("expected"), f"eval/{index}/expected")
        required_fields = {"status", "task_type", "error_details", "retrieved_data"}
        if set(expected) != required_fields:
            raise WebArenaNativeClaimError(
                f"AgentResponseEvaluator eval/{index} expected keys drifted: {sorted(expected)}"
            )
        if not isinstance(entry.get("ordered"), bool):
            raise WebArenaNativeClaimError(f"AgentResponseEvaluator eval/{index} requires boolean ordered")
        return {
            "config_pointer": pointer,
            "implementation_pointer": AGENT_RESPONSE_POINTER,
            "comparison": "exact_normalized_agent_response",
            "compared_fields": ["status", "task_type", "error_details", "retrieved_data"],
            "retrieved_data_ordered": entry["ordered"],
            "extra_missing_or_duplicate_retrieved_items_fail": True,
        }
    if name == "NetworkEventEvaluator":
        required = {
            "evaluator",
            "expected",
            "last_event_only",
            "ignored_query_params",
            "ignored_query_params_patterns",
            "decode_base64_query",
            "query_params_schema",
            "post_data_schema",
            "ignored_post_data_params_patterns",
            "should_not_exist",
        }
        if set(entry) != required:
            raise WebArenaNativeClaimError(
                f"NetworkEventEvaluator eval/{index} keys drifted: expected={sorted(required)} actual={sorted(entry)}"
            )
        expected = _require_mapping(entry.get("expected"), f"eval/{index}/expected")
        expected_keys = {
            "url",
            "headers",
            "query_params",
            "post_data",
            "response_content",
            "response_status",
            "http_method",
            "response_cookies",
        }
        if set(expected) != expected_keys:
            raise WebArenaNativeClaimError(
                f"NetworkEventEvaluator eval/{index} expected keys drifted: {sorted(expected)}"
            )
        for field in ("last_event_only", "decode_base64_query", "should_not_exist"):
            if not isinstance(entry.get(field), bool):
                raise WebArenaNativeClaimError(f"NetworkEventEvaluator eval/{index}/{field} must be boolean")
        return {
            "config_pointer": pointer,
            "implementation_pointer": NETWORK_EVENT_POINTER,
            "comparison": "official_normalized_network_event_comparison",
            "last_event_only": entry["last_event_only"],
            "should_not_exist": entry["should_not_exist"],
            "decode_base64_query": entry["decode_base64_query"],
            "compared_expected_fields": sorted(key for key, value in expected.items() if value is not None),
            "ignored_query_params": entry["ignored_query_params"],
            "ignored_query_params_patterns": entry["ignored_query_params_patterns"],
            "query_params_schema": entry["query_params_schema"],
            "post_data_schema": entry["post_data_schema"],
            "ignored_post_data_params_patterns": entry["ignored_post_data_params_patterns"],
        }
    raise WebArenaNativeClaimError(f"unsupported evaluator {name!r} at eval/{index}")


def compile_case_ir(
    *,
    source: Mapping[str, Any],
    manifest_case: Mapping[str, Any],
    official_task: Mapping[str, Any],
    source_bundle_path: Path,
    source_bundle_sha256: str,
    step19_manifest_path: Path,
    step19_manifest_sha256: str,
    packet_index_path: Path,
    packet_index_sha256: str,
    input_lock_sha256: str,
    compiler: Mapping[str, str],
) -> dict[str, Any]:
    case_unit_id = str(source.get("case_unit_id"))
    task_id = str(source.get("task_id"))
    if case_unit_id != task_id or case_unit_id not in EXPECTED_TASK_IDS:
        raise WebArenaNativeClaimError(f"invalid WebArena identity: case={case_unit_id!r} task={task_id!r}")

    draft_input = _require_mapping(source.get("draft_input"), f"source[{case_unit_id}].draft_input")
    packet_path = _repo_path(str(draft_input.get("case_packet_path")))
    raw_manifest_path = _repo_path(str(draft_input.get("raw_case_manifest_path")))
    if packet_path.is_symlink() or raw_manifest_path.is_symlink():
        raise WebArenaNativeClaimError(f"symlinked canonical input for case {case_unit_id}")
    if file_sha256(packet_path) != draft_input.get("case_packet_sha256"):
        raise WebArenaNativeClaimError(f"case packet hash mismatch for case {case_unit_id}")
    if file_sha256(raw_manifest_path) != draft_input.get("raw_case_manifest_sha256"):
        raise WebArenaNativeClaimError(f"raw case manifest hash mismatch for case {case_unit_id}")

    raw_manifest = _require_mapping(_load_json(raw_manifest_path), str(raw_manifest_path))
    raw_root = raw_manifest_path.parent / "raw_case"
    derived_task_path = raw_root / "derived" / "task.json"
    derived_task = _require_mapping(_load_json(derived_task_path), str(derived_task_path))
    if derived_task != dict(official_task):
        raise WebArenaNativeClaimError(f"derived task differs from official source for case {case_unit_id}")
    if str(derived_task.get("task_id")) != task_id:
        raise WebArenaNativeClaimError(f"derived task ID mismatch for case {case_unit_id}")
    revision = int(derived_task.get("revision"))
    if int(manifest_case.get("revision")) != revision:
        raise WebArenaNativeClaimError(f"Step19 revision mismatch for case {case_unit_id}")
    if list(manifest_case.get("sites") or []) != list(derived_task.get("sites") or []):
        raise WebArenaNativeClaimError(f"Step19 site list mismatch for case {case_unit_id}")

    packet_source_task_sha256 = object_sha256(derived_task, ensure_ascii=False)
    manifest_source_task_sha256 = object_sha256(derived_task, ensure_ascii=True)
    if raw_manifest.get("source_task_sha256") != packet_source_task_sha256:
        raise WebArenaNativeClaimError(f"raw manifest task canonical hash mismatch for case {case_unit_id}")
    if manifest_case.get("source_task_sha256") != manifest_source_task_sha256:
        raise WebArenaNativeClaimError(f"Step19 task canonical hash mismatch for case {case_unit_id}")
    if raw_manifest.get("normalized_source_sha256") != OFFICIAL_SOURCE_SHA256:
        raise WebArenaNativeClaimError(f"official source hash mismatch in raw manifest for case {case_unit_id}")
    if raw_manifest.get("official_commit") != OFFICIAL_COMMIT:
        raise WebArenaNativeClaimError(f"official commit mismatch for case {case_unit_id}")
    if raw_manifest.get("official_evaluator_checksum") != OFFICIAL_EVALUATOR_CHECKSUM:
        raise WebArenaNativeClaimError(f"official evaluator checksum mismatch for case {case_unit_id}")
    if raw_manifest.get("task_score_composition") != "all_evaluator_scores_must_equal_1.0":
        raise WebArenaNativeClaimError(f"task score composition drift for case {case_unit_id}")

    eval_entries = [_require_mapping(item, f"task {task_id} evaluator") for item in _require_sequence(derived_task.get("eval"), "task eval")]
    if not eval_entries or eval_entries[0].get("evaluator") != "AgentResponseEvaluator":
        raise WebArenaNativeClaimError(f"task {task_id} must begin with AgentResponseEvaluator")
    if sum(item.get("evaluator") == "AgentResponseEvaluator" for item in eval_entries) != 1:
        raise WebArenaNativeClaimError(f"task {task_id} must contain exactly one AgentResponseEvaluator")
    evaluator_names = [str(item.get("evaluator")) for item in eval_entries]
    if list(raw_manifest.get("evaluator_names_in_order") or []) != evaluator_names:
        raise WebArenaNativeClaimError(f"evaluator order mismatch for case {case_unit_id}")
    has_network = "NetworkEventEvaluator" in evaluator_names
    _validate_semantic_sources(raw_root, raw_manifest, has_network=has_network)
    _validate_all_raw_files(raw_root, raw_manifest)
    controller_packet_path = raw_manifest_path.parent / "case_packet.json"
    controller_packet = _require_mapping(_load_json(controller_packet_path), str(controller_packet_path))
    controller_task = _require_mapping(controller_packet.get("task"), f"controller task {case_unit_id}")
    controller_visible = _require_mapping(
        controller_packet.get("model_visible_input"),
        f"controller model_visible_input {case_unit_id}",
    )
    expected_controller_task = {
        "instruction": derived_task.get("intent"),
        "intent_template_id": derived_task.get("intent_template_id"),
        "revision": revision,
        "sites": list(derived_task.get("sites") or []),
        "start_url_templates": list(derived_task.get("start_urls") or []),
        "task_id": int(task_id),
    }
    for field, expected in expected_controller_task.items():
        if controller_task.get(field) != expected:
            raise WebArenaNativeClaimError(
                f"controller case_packet task field {field} mismatch for case {case_unit_id}"
            )
    top_level_hashes = _require_mapping(
        raw_manifest.get("top_level_file_sha256"),
        f"raw manifest top_level_file_sha256 {case_unit_id}",
    )
    if file_sha256(controller_packet_path) != top_level_hashes.get("case_packet.json"):
        raise WebArenaNativeClaimError(f"controller case_packet.json hash mismatch for case {case_unit_id}")
    if controller_visible.get("path") != "agent_input.json":
        raise WebArenaNativeClaimError(f"controller model-visible path mismatch for case {case_unit_id}")
    expected_agent_hash = str(controller_visible.get("sha256"))
    if top_level_hashes.get("agent_input.json") != expected_agent_hash:
        raise WebArenaNativeClaimError(f"controller/raw-manifest agent-input hash mismatch for case {case_unit_id}")
    agent_input_path = raw_manifest_path.parent / "agent_input.json"
    agent_input_sha256 = _validate_agent_input(
        agent_input_path,
        derived_task,
        resolved_start_urls=_require_sequence(
            controller_task.get("resolved_start_urls"),
            f"controller resolved_start_urls {case_unit_id}",
        ),
        expected_file_sha256=expected_agent_hash,
    )

    evaluator_specs: list[dict[str, Any]] = []
    for index, entry in enumerate(eval_entries):
        evaluator_specs.append(
            {
                "index": index,
                "name": entry["evaluator"],
                "config": entry,
                "config_sha256": object_sha256(entry),
                "semantics": _evaluator_semantics(entry, index),
            }
        )
    response_expected = _require_mapping(eval_entries[0].get("expected"), "AgentResponse expected")
    task_type = str(response_expected.get("task_type"))
    if task_type not in {"RETRIEVE", "MUTATE", "NAVIGATE"}:
        raise WebArenaNativeClaimError(f"unexpected task type for case {case_unit_id}: {task_type!r}")

    return {
        "schema_version": IR_SCHEMA_VERSION,
        "visibility": "controller_drafter_reviewer_only_not_model_visible",
        "compiler": dict(compiler),
        "identity": {
            "domain": DOMAIN,
            "case_unit_id": case_unit_id,
            "task_id": task_id,
            "task_revision": revision,
            "task_type": task_type,
        },
        "task": {
            "intent": derived_task.get("intent"),
            "sites": list(derived_task.get("sites") or []),
            "start_urls": list(derived_task.get("start_urls") or []),
        },
        "source_binding": {
            "input_lock_sha256": input_lock_sha256,
            "source_bundle_path": _repo_relative(source_bundle_path),
            "source_bundle_sha256": source_bundle_sha256,
            "step19_manifest_path": _repo_relative(step19_manifest_path),
            "step19_manifest_sha256": step19_manifest_sha256,
            "packet_index_path": _repo_relative(packet_index_path),
            "packet_index_sha256": packet_index_sha256,
            "case_packet_path": _repo_relative(packet_path),
            "case_packet_sha256": file_sha256(packet_path),
            "raw_case_manifest_path": _repo_relative(raw_manifest_path),
            "raw_case_manifest_sha256": file_sha256(raw_manifest_path),
            "controller_packet_path": _repo_relative(controller_packet_path),
            "controller_packet_sha256": file_sha256(controller_packet_path),
            "derived_task_path": _repo_relative(derived_task_path),
            "derived_task_file_sha256": file_sha256(derived_task_path),
            "packet_source_task_sha256": packet_source_task_sha256,
            "manifest_source_task_sha256": manifest_source_task_sha256,
            "evaluator_config_sha256": object_sha256(eval_entries),
            "agent_input_path": _repo_relative(agent_input_path),
            "agent_input_sha256": agent_input_sha256,
            "official_source_sha256": OFFICIAL_SOURCE_SHA256,
            "official_commit": OFFICIAL_COMMIT,
            "official_evaluator_checksum": OFFICIAL_EVALUATOR_CHECKSUM,
        },
        "native_semantics": {
            "evaluator_count": len(evaluator_specs),
            "evaluator_names_in_order": evaluator_names,
            "evaluators": evaluator_specs,
            "composition": "all_evaluator_scores_must_equal_1.0",
            "composition_pointer": TASK_RESULT_POINTER,
            "orchestration_pointer": EVALUATOR_POINTER,
            "success": "TaskEvalResult.status == SUCCESS and score == 1.0 only when every evaluator score equals 1.0",
            "failure": "TaskEvalResult.status == FAILURE only when evaluation completes without ERROR and at least one evaluator score is not 1.0",
            "unresolve": "TaskEvalResult.status == ERROR or unavailable/corrupt/misbinding decisive evidence is UNRESOLVE, not agent failure",
        },
        "required_artifacts": [
            {
                "artifact_id": "agent-response",
                "artifact_name": "official structured agent response",
                "artifact_source": "agent_response.json",
                "artifact_type": "structured_output",
                "contract_requirement_id": "req-agent-response",
                "native_aligned_source_support": True,
            },
            {
                "artifact_id": "network-har",
                "artifact_name": "full embedded browser network trace",
                "artifact_source": "network.har",
                "artifact_type": "network_trace",
                "contract_requirement_id": "req-network-har",
                "native_aligned_source_support": True,
            },
            {
                "artifact_id": "native-evaluator-input",
                "artifact_name": "official evaluator task-bound input",
                "artifact_source": "official_evaluator",
                "artifact_type": "native_evaluator_input",
                "contract_requirement_id": "req-native-evaluator-input",
                "native_aligned_source_support": True,
            },
            {
                "artifact_id": "native-evaluator-output",
                "artifact_name": "official TaskEvalResult output",
                "artifact_source": "official_evaluator",
                "artifact_type": "native_evaluator_output",
                "contract_requirement_id": "req-native-evaluator-output",
                "native_aligned_source_support": True,
            },
        ],
    }


def validate_native_ir(ir: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    if ir.get("schema_version") != IR_SCHEMA_VERSION:
        issues.append("wrong IR schema_version")
    identity = ir.get("identity")
    if not isinstance(identity, Mapping):
        return issues + ["identity is missing"]
    case_unit_id = str(identity.get("case_unit_id"))
    if identity.get("domain") != DOMAIN or str(identity.get("task_id")) != case_unit_id:
        issues.append("domain/case/task identity mismatch")
    source = ir.get("source_binding")
    if not isinstance(source, Mapping):
        issues.append("source_binding is missing")
    semantics = ir.get("native_semantics")
    if not isinstance(semantics, Mapping):
        return issues + ["native_semantics is missing"]
    evaluators = semantics.get("evaluators")
    if not isinstance(evaluators, list) or not evaluators:
        return issues + ["evaluators must be a nonempty list"]
    names: list[str] = []
    for index, evaluator in enumerate(evaluators):
        if not isinstance(evaluator, Mapping):
            issues.append(f"evaluator {index} is not a mapping")
            continue
        if evaluator.get("index") != index:
            issues.append(f"evaluator {index} index/order mismatch")
        name = str(evaluator.get("name"))
        names.append(name)
        config = evaluator.get("config")
        if not isinstance(config, Mapping) or config.get("evaluator") != name:
            issues.append(f"evaluator {index} config/name mismatch")
        elif evaluator.get("config_sha256") != object_sha256(config):
            issues.append(f"evaluator {index} config hash mismatch")
        semantic = evaluator.get("semantics")
        if not isinstance(semantic, Mapping):
            issues.append(f"evaluator {index} semantics missing")
        elif semantic.get("config_pointer") != f"derived/task.json::eval/{index}":
            issues.append(f"evaluator {index} pointer mismatch")
        if name == "AgentResponseEvaluator":
            if not isinstance(semantic, Mapping) or semantic.get("comparison") != "exact_normalized_agent_response":
                issues.append(f"evaluator {index} lacks exact agent-response semantics")
            if not isinstance(semantic, Mapping) or semantic.get("extra_missing_or_duplicate_retrieved_items_fail") is not True:
                issues.append(f"evaluator {index} does not fail extra/missing/duplicate retrieved items")
        elif name == "NetworkEventEvaluator":
            if not isinstance(semantic, Mapping) or semantic.get("comparison") != "official_normalized_network_event_comparison":
                issues.append(f"evaluator {index} lacks official network-event semantics")
            for flag in ("last_event_only", "should_not_exist", "decode_base64_query"):
                if isinstance(config, Mapping) and isinstance(semantic, Mapping) and semantic.get(flag) != config.get(flag):
                    issues.append(f"evaluator {index} lost NetworkEvent {flag}")
        else:
            issues.append(f"unsupported evaluator {name!r}")
    if names.count("AgentResponseEvaluator") != 1 or not names or names[0] != "AgentResponseEvaluator":
        issues.append("exactly one leading AgentResponseEvaluator is required")
    if semantics.get("evaluator_count") != len(evaluators):
        issues.append("evaluator_count mismatch")
    if semantics.get("evaluator_names_in_order") != names:
        issues.append("evaluator_names_in_order mismatch")
    if semantics.get("composition") != "all_evaluator_scores_must_equal_1.0":
        issues.append("all-evaluator AND composition is missing")
    if semantics.get("composition_pointer") != TASK_RESULT_POINTER:
        issues.append("TaskEvalResult.create pointer is missing")
    if "UNRESOLVE" not in str(semantics.get("unresolve")) or "ERROR" not in str(semantics.get("unresolve")):
        issues.append("evaluator ERROR is not mapped to UNRESOLVE")
    artifacts = ir.get("required_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        issues.append("required_artifacts must be nonempty")
    else:
        artifact_ids = [str(item.get("artifact_id")) for item in artifacts if isinstance(item, Mapping)]
        expected_ids = ["agent-response", "network-har", "native-evaluator-input", "native-evaluator-output"]
        if artifact_ids != expected_ids:
            issues.append("required_artifacts are incomplete or reordered")
        requirement_ids = [
            str(item.get("contract_requirement_id"))
            for item in artifacts
            if isinstance(item, Mapping)
        ]
        if len(requirement_ids) != len(set(requirement_ids)):
            issues.append("required artifact contract_requirement_id values are not unique")
        if any(item.get("native_aligned_source_support") is not True for item in artifacts if isinstance(item, Mapping)):
            issues.append("required artifact lacks native source support")
    return issues


def render_contract(ir: Mapping[str, Any], *, output_path: str, locked: Mapping[str, Any] | None = None) -> dict[str, Any]:
    issues = validate_native_ir(ir)
    if issues:
        raise WebArenaNativeClaimError("invalid IR: " + "; ".join(issues))
    identity = _require_mapping(ir["identity"], "IR identity")
    source = _require_mapping(ir["source_binding"], "IR source binding")
    semantics = _require_mapping(ir["native_semantics"], "IR semantics")
    case_unit_id = str(identity["case_unit_id"])
    evaluator_labels = [
        f"eval[{item['index']}]={item['name']}@{item['config_sha256']}"
        for item in semantics["evaluators"]
    ]
    joined = ", ".join(evaluator_labels)
    contract_id = f"ec_webarena_verified_{case_unit_id}_contract_v1_0_0"
    contract: dict[str, Any] = {
        "schema_version": "evidence_contract/v1",
        "contract_id": contract_id,
        "domain": DOMAIN,
        "case_unit_id": case_unit_id,
        "task_id": str(identity["task_id"]),
        "contract_version": "1.0.0",
        "contract_status": "draft",
        "locked_at": None,
        "locked_by": None,
        "contract_hash": "0" * 64,
        "manifest_hash": source["step19_manifest_sha256"],
        "taxonomy_version": "R1-R7_paper_taxonomy_v0.1.0",
        "claim_text": (
            f"WebArena-Verified task {identity['task_id']} revision {identity['task_revision']} succeeds only "
            f"when the official evaluator completes without ERROR and every configured evaluator scores 1.0: {joined}."
        ),
        "native_sources": [
            f"derived/task.json for task {identity['task_id']} revision {identity['task_revision']}",
            EVALUATOR_POINTER,
            TASK_RESULT_POINTER,
        ],
        "required_artifacts": list(ir["required_artifacts"]),
        "success_rule": (
            f"SUCCESS iff official TaskEvalResult for task {identity['task_id']} revision {identity['task_revision']} "
            "has status SUCCESS and score 1.0, the normalized AgentResponse fields and retrieved_data are exactly "
            "equal to the frozen expected configuration under its ordered flag, and every evaluator in frozen "
            f"order scores 1.0: {joined}."
        ),
        "fail_rule": (
            "FAIL iff the official evaluator completes without ERROR and at least one frozen evaluator returns "
            f"a non-1.0 score, including exact response or network-event mismatch: {joined}."
        ),
        "unresolve_rule": (
            "UNRESOLVE, never agent FAIL, when TaskEvalResult status is ERROR, an infrastructure/evaluator fault "
            "occurs, or a required artifact is missing, corrupt, or not bound to this task/revision so the native "
            "decision cannot be audited. An agent-attributable invalid final response recorded by a completed "
            "non-ERROR evaluator remains FAIL."
        ),
        "claim_scope": "native_aligned",
        "stronger_measurement_mapping": None,
        "minimality_rationale": (
            "The contract preserves only the official per-evaluator comparisons, their all-score-1 conjunction, "
            "and the evaluator inputs/outputs needed to replay or audit that native decision."
        ),
        "source_support": {
            "draft_transport": "deterministic_compiler",
            "formal_draft_eligible": locked is not None,
            "compiler": dict(ir["compiler"]),
            "input_lock_sha256": source["input_lock_sha256"],
            "native_ir_sha256": object_sha256(ir),
            "task_revision": identity["task_revision"],
            "packet_source_task_sha256": source["packet_source_task_sha256"],
            "manifest_source_task_sha256": source["manifest_source_task_sha256"],
            "derived_task_file_sha256": source["derived_task_file_sha256"],
            "evaluator_config_sha256": source["evaluator_config_sha256"],
            "official_commit": source["official_commit"],
            "official_evaluator_checksum": source["official_evaluator_checksum"],
            "case_packet_path": source["case_packet_path"],
            "case_packet_sha256": source["case_packet_sha256"],
            "raw_case_manifest_path": source["raw_case_manifest_path"],
            "raw_case_manifest_sha256": source["raw_case_manifest_sha256"],
            "evaluator": "official WebArena-Verified evaluator sequence and exact config hashes",
            "task_or_policy": "official task instruction and revision",
            "schema": "official TaskEvalResult and evaluator input/output schemas",
        },
        "main_result_eligible": False,
        "contract_drafting_llm_call_id": f"not-applicable-deterministic-compiler-{case_unit_id}",
        "contract_draft_id": f"draft-webarena-verified-{case_unit_id}-v1",
        "review_record_id": f"pending-human-review-webarena-verified-{case_unit_id}",
        "canonicalization_method": "json_canonical_sha256",
        "canonical_hash_source": output_path,
        "canonical_hash": "0" * 64,
        "manifest_contract_lock_ref": f"pending:{contract_id}:1.0.0",
        "supersedes_contract_id": None,
        "supersedes_contract_version": None,
        "supersedes_contract_hash": None,
        "sensitivity_report_id": None,
    }
    if locked is not None:
        lock_basis = str(locked.get("formal_lock_basis") or "human_signoff")
        locked_by = str(locked.get("locked_by") or locked.get("reviewer_id") or "")
        review_record_id = str(
            locked.get("lock_record_id") or locked.get("review_id") or ""
        )
        if not locked_by or not review_record_id:
            raise WebArenaNativeClaimError("formal lock context is missing lock authority/record ID")
        contract["contract_status"] = "locked"
        contract["locked_at"] = locked["locked_at"]
        contract["locked_by"] = locked_by
        contract["main_result_eligible"] = True
        contract["review_record_id"] = review_record_id
        contract["manifest_contract_lock_ref"] = (
            f"webarena-verified-v1.2.3-full-812-three-model:{contract_id}:1.0.0"
        )
        contract["source_support"]["formal_lock_basis"] = lock_basis
        if lock_basis == OPERATOR_WAIVER_BASIS:
            contract["source_support"].update(
                {
                    "human_source_check_complete": False,
                    "human_signoff_claimed": False,
                    "human_signoff_requirement_waived": True,
                    "operator_waiver_lock_sha256": locked["operator_waiver_lock_sha256"],
                }
            )
    stamp_contract_hash(contract)
    report = validate_object("evidence_contract", contract, raise_on_error=False)
    if report.issues:
        raise WebArenaNativeClaimError(
            "rendered evidence contract violates schema: "
            + "; ".join(f"{item.path}: {item.message}" for item in report.issues[:8])
        )
    return contract


def _justified(text: str, *support: str) -> dict[str, Any]:
    return {"text": text, "support": list(support)}


def render_checklist(ir: Mapping[str, Any]) -> dict[str, Any]:
    issues = validate_native_ir(ir)
    if issues:
        raise WebArenaNativeClaimError("invalid IR: " + "; ".join(issues))
    identity = _require_mapping(ir["identity"], "IR identity")
    task = _require_mapping(ir["task"], "IR task")
    semantics = _require_mapping(ir["native_semantics"], "IR semantics")
    evaluators = list(semantics["evaluators"])
    success_if: list[dict[str, Any]] = []
    fail_if: list[dict[str, Any]] = []
    for evaluator in evaluators:
        index = evaluator["index"]
        name = evaluator["name"]
        digest = evaluator["config_sha256"]
        pointer = f"derived/task.json::eval/{index}"
        if name == "AgentResponseEvaluator":
            ordered = evaluator["semantics"]["retrieved_data_ordered"]
            success_text = (
                f"eval[{index}] AgentResponseEvaluator config {digest} scores 1.0: normalized status, task_type, "
                f"error_details and retrieved_data exactly match the frozen expected config; retrieved_data "
                f"ordered={str(ordered).lower()}, with no extra, missing or duplicate mismatch."
            )
            fail_text = (
                f"eval[{index}] completes without ERROR but scores below 1.0 because any exact normalized response "
                f"field or retrieved_data membership/order requirement in config {digest} mismatches."
            )
            implementation = AGENT_RESPONSE_POINTER
        else:
            flags = evaluator["semantics"]
            success_text = (
                f"eval[{index}] NetworkEventEvaluator config {digest} scores 1.0 using the official comparator "
                f"with last_event_only={str(flags['last_event_only']).lower()}, "
                f"should_not_exist={str(flags['should_not_exist']).lower()}, and "
                f"decode_base64_query={str(flags['decode_base64_query']).lower()}, preserving all ignored-field and schema settings."
            )
            fail_text = (
                f"eval[{index}] completes without ERROR but scores below 1.0 because the retained full network "
                f"trace violates NetworkEvent config {digest}, including its event-selection, absence, expected-field, "
                "ignored-field, or schema-normalization rules."
            )
            implementation = NETWORK_EVENT_POINTER
        success_if.append(_justified(success_text, pointer, implementation))
        fail_if.append(_justified(fail_text, pointer, implementation))
    success_if.append(
        _justified(
            f"All {len(evaluators)} evaluator results are present in frozen order and every score equals 1.0, so "
            "TaskEvalResult.create returns status SUCCESS and score 1.0.",
            TASK_RESULT_POINTER,
            EVALUATOR_POINTER,
        )
    )
    fail_if.append(
        _justified(
            "The official task evaluation completes without ERROR and one or more frozen evaluator scores are not 1.0; "
            "TaskEvalResult.create therefore returns FAILURE. Agent-attributable invalid or missing structured final "
            "output recorded by the completed evaluator is included here.",
            TASK_RESULT_POINTER,
        )
    )
    decisive_artifacts = [
        {
            "artifact": "agent_response.json",
            "question": "Is the exact structured response used by AgentResponseEvaluator present and bound to this task/revision?",
            "support": [AGENT_RESPONSE_POINTER, "derived/task.json::eval/0"],
        },
        {
            "artifact": "official TaskEvalResult and ordered EvaluatorResult list",
            "question": "Did the official evaluator complete without ERROR and preserve every configured evaluator result in order?",
            "support": [EVALUATOR_POINTER, TASK_RESULT_POINTER],
        },
    ]
    if any(item["name"] == "NetworkEventEvaluator" for item in evaluators):
        decisive_artifacts.append(
            {
                "artifact": "network.har (full content embedded)",
                "question": "Is the complete task-bound network trace available for every configured NetworkEventEvaluator comparison?",
                "support": [NETWORK_EVENT_POINTER, "derived/task.json::eval"],
            }
        )
    checklist = {
        "schema_version": "case_checklist_v1",
        "case_unit_id": str(identity["case_unit_id"]),
        "domain": DOMAIN,
        "task_id": str(identity["task_id"]),
        "native": {
            "user_goal": _justified(
                f"For official task revision {identity['task_revision']}: {task['intent']}",
                "derived/task.json::intent",
                "derived/task.json::revision",
            ),
            "benchmark_success": _justified(
                f"The official WebArena-Verified TaskEvalResult succeeds only when all {len(evaluators)} configured "
                "evaluator scores equal 1.0; evaluator ERROR is not agent failure.",
                "derived/task.json::eval",
                TASK_RESULT_POINTER,
            ),
            "checked_by": _justified(
                "Run the frozen evaluator sequence in order through WebArenaVerifiedEvaluator.evaluate_task and apply "
                "TaskEvalResult.create's ERROR precedence and all-score-1 conjunction.",
                EVALUATOR_POINTER,
                TASK_RESULT_POINTER,
            ),
            "decisive_artifacts": decisive_artifacts,
            "success_if": success_if,
            "fail_if": fail_if,
            "undecided_if": [
                _justified(
                    "TaskEvalResult or any EvaluatorResult has status ERROR because of evaluator, site, API, login, "
                    "or other infrastructure failure; record UNRESOLVE rather than agent FAIL.",
                    TASK_RESULT_POINTER,
                ),
                _justified(
                    "A decisive artifact is absent, corrupt, truncated, or cannot be hash-bound to this exact task and "
                    "revision, and no completed non-ERROR official evaluator result can decide the claim.",
                    EVALUATOR_POINTER,
                    TASK_RESULT_POINTER,
                ),
            ],
        },
        "stronger": {"additional_conditions": []},
    }
    schema = _load_json(PACKAGE_ROOT / CHECKLIST_SCHEMA)
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(checklist), key=lambda item: list(item.path))
    if errors:
        raise WebArenaNativeClaimError(
            "rendered checklist violates schema: "
            + "; ".join(f"{list(item.path)}: {item.message}" for item in errors[:8])
        )
    return checklist


def _expected_machine_review(
    *,
    ir: Mapping[str, Any],
    ir_path: str,
    ir_sha256: str,
    contract_path: str,
    contract_sha256: str,
    checklist_path: str,
    checklist_sha256: str,
    input_lock_sha256: str,
) -> dict[str, Any]:
    identity = _require_mapping(ir["identity"], "IR identity")
    evaluator_count = int(ir["native_semantics"]["evaluator_count"])
    return {
        "schema_version": MACHINE_REVIEW_SCHEMA_VERSION,
        "status": "accepted",
        "review_type": "deterministic_machine_validation_not_human_review",
        "domain": DOMAIN,
        "case_unit_id": str(identity["case_unit_id"]),
        "task_id": str(identity["task_id"]),
        "task_revision": identity["task_revision"],
        "input_lock_sha256": input_lock_sha256,
        "native_ir_path": ir_path,
        "native_ir_sha256": ir_sha256,
        "draft_contract_path": contract_path,
        "draft_contract_sha256": contract_sha256,
        "draft_checklist_path": checklist_path,
        "draft_checklist_sha256": checklist_sha256,
        "validator": compiler_identity(),
        "checks": {
            "domain_case_task_identity_exact": True,
            "task_revision_and_source_hashes_bound": True,
            "evaluator_count_and_order_exact": True,
            "every_evaluator_config_hash_bound": True,
            "agent_response_exact_semantics_present": True,
            "network_event_semantics_present_when_configured": True,
            "all_evaluator_and_composition_present": True,
            "evaluator_error_maps_to_unresolve": True,
            "required_artifacts_nonempty": True,
            "contract_schema_valid": True,
            "checklist_schema_valid": True,
        },
        "evaluator_count": evaluator_count,
        "network_event_evaluator_count": sum(
            item["name"] == "NetworkEventEvaluator" for item in ir["native_semantics"]["evaluators"]
        ),
        "human_source_check_complete": False,
    }


def _input_lock(
    *,
    source_bundle_path: Path,
    step19_manifest_path: Path,
    packet_index_path: Path,
    source_bundle: Mapping[str, Any],
    manifest: Mapping[str, Any],
    packet_index: Mapping[str, Any],
    agent_input_hash: str,
) -> dict[str, Any]:
    sources = _require_sequence(source_bundle.get("sources"), "source bundle sources")
    cases = _require_sequence(manifest.get("cases"), "Step19 cases")
    if len(sources) != EXPECTED_CASES or len(cases) != EXPECTED_CASES:
        raise WebArenaNativeClaimError("source bundle and Step19 manifest must each contain exactly 812 cases")
    source_ids = [str(item.get("case_unit_id")) for item in sources if isinstance(item, Mapping)]
    manifest_ids = [str(item.get("task_id")) for item in cases if isinstance(item, Mapping)]
    if sorted(source_ids, key=int) != list(EXPECTED_TASK_IDS) or sorted(manifest_ids, key=int) != list(EXPECTED_TASK_IDS):
        raise WebArenaNativeClaimError("source/manifest case IDs must be exactly 0..811 with no duplicates")
    inventory = []
    sources_by_id = {str(item["case_unit_id"]): item for item in sources}
    manifest_by_id = {str(item["task_id"]): item for item in cases}
    for task_id in EXPECTED_TASK_IDS:
        source = sources_by_id[task_id]
        manifest_case = manifest_by_id[task_id]
        draft_input = _require_mapping(source.get("draft_input"), f"source {task_id} draft_input")
        inventory.append(
            {
                "domain": DOMAIN,
                "case_unit_id": task_id,
                "task_id": task_id,
                "task_revision": manifest_case.get("revision"),
                "manifest_source_task_sha256": manifest_case.get("source_task_sha256"),
                "case_packet_path": draft_input.get("case_packet_path"),
                "case_packet_sha256": draft_input.get("case_packet_sha256"),
                "raw_case_manifest_path": draft_input.get("raw_case_manifest_path"),
                "raw_case_manifest_sha256": draft_input.get("raw_case_manifest_sha256"),
            }
        )
    return {
        "schema_version": INPUT_LOCK_SCHEMA_VERSION,
        "domain": DOMAIN,
        "benchmark_version": BENCHMARK_VERSION,
        "expected_count": EXPECTED_CASES,
        "compiler": compiler_identity(),
        "source_bundle_path": _repo_relative(source_bundle_path),
        "source_bundle_sha256": file_sha256(source_bundle_path),
        "step19_manifest_path": _repo_relative(step19_manifest_path),
        "step19_manifest_sha256": file_sha256(step19_manifest_path),
        "packet_index_path": _repo_relative(packet_index_path),
        "packet_index_sha256": file_sha256(packet_index_path),
        "official_source_path": manifest["benchmark"]["source_path"],
        "official_source_sha256": manifest["benchmark"]["source_sha256"],
        "official_commit": manifest["benchmark"]["tag_commit"],
        "packet_index_core_sha256": packet_index.get("index_core_sha256"),
        "packet_index_agent_input_tree_sha256": packet_index.get("agent_input_tree_sha256"),
        "agent_input_tree_sha256_before": agent_input_hash,
        "case_inventory_sha256": object_sha256(inventory),
        "case_inventory": inventory,
    }


def _load_human_signoffs(path: Path | None, entries: Sequence[Mapping[str, Any]], input_lock_sha256: str) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    if not path.is_file() or path.is_symlink():
        raise WebArenaNativeClaimError(f"human signoff file missing or symlinked: {path}")
    expected = {str(item["case_unit_id"]): item for item in entries}
    signoff_schema = _load_json(PACKAGE_ROOT / HUMAN_SIGNOFF_SCHEMA)
    signoff_validator = jsonschema.Draft202012Validator(signoff_schema)
    signoffs: dict[str, dict[str, Any]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise WebArenaNativeClaimError(f"invalid human signoff JSONL line {line_number}") from exc
        item = _require_mapping(item, f"human signoff line {line_number}")
        schema_errors = sorted(signoff_validator.iter_errors(item), key=lambda error: list(error.path))
        if schema_errors:
            raise WebArenaNativeClaimError(
                f"human signoff line {line_number} violates schema: "
                + "; ".join(f"{list(error.path)}: {error.message}" for error in schema_errors[:4])
            )
        case_id = str(item.get("case_unit_id"))
        if case_id in signoffs:
            raise WebArenaNativeClaimError(f"duplicate human signoff for case {case_id}")
        source = expected.get(case_id)
        if source is None:
            raise WebArenaNativeClaimError(f"unexpected human signoff case {case_id}")
        required_exact = {
            "schema_version": HUMAN_SIGNOFF_SCHEMA_VERSION,
            "domain": DOMAIN,
            "case_unit_id": case_id,
            "task_id": source["task_id"],
            "task_revision": source["task_revision"],
            "input_lock_sha256": input_lock_sha256,
            "native_ir_sha256": source["native_ir_sha256"],
            "draft_contract_sha256": source["draft_contract_sha256"],
            "draft_checklist_sha256": source["draft_checklist_sha256"],
            "machine_review_sha256": source["machine_review_sha256"],
            "decision": "approve",
            "source_check_complete": True,
            "evaluator_semantics_complete": True,
            "artifact_requirements_accepted": True,
        }
        for field, value in required_exact.items():
            if item.get(field) != value:
                raise WebArenaNativeClaimError(
                    f"human signoff {case_id} field {field} mismatch: expected={value!r} actual={item.get(field)!r}"
                )
        for field in ("review_id", "reviewer_id", "review_started_at", "review_finished_at", "locked_at", "first_scoring_started_at"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise WebArenaNativeClaimError(f"human signoff {case_id} missing {field}")
        started = _parse_timestamp(item["review_started_at"], "review_started_at")
        finished = _parse_timestamp(item["review_finished_at"], "review_finished_at")
        locked_at = _parse_timestamp(item["locked_at"], "locked_at")
        scoring = _parse_timestamp(item["first_scoring_started_at"], "first_scoring_started_at")
        if not started < finished <= locked_at < scoring:
            raise WebArenaNativeClaimError(
                f"human signoff {case_id} must satisfy review_started < review_finished <= locked_at < first_scoring"
            )
        signoffs[case_id] = item
    if set(signoffs) != set(expected):
        missing = sorted(set(expected) - set(signoffs), key=int)
        raise WebArenaNativeClaimError(
            f"formal lock requires exact human signoff denominator {len(expected)}; missing {len(missing)}"
        )
    return signoffs


def native_case_artifacts_sha256(entries: Sequence[Mapping[str, Any]]) -> str:
    """Hash only the stable machine-generated per-case artifact bindings."""

    fields = (
        "case_unit_id",
        "task_id",
        "task_revision",
        "native_ir_sha256",
        "draft_contract_sha256",
        "draft_checklist_sha256",
        "machine_review_sha256",
    )
    inventory = [
        {field: item.get(field) for field in fields}
        for item in sorted(entries, key=lambda value: int(str(value.get("case_unit_id"))))
    ]
    return object_sha256(inventory)


def expected_operator_waiver_source_binding(
    *,
    input_lock: Mapping[str, Any],
    input_lock_sha256: str,
    machine_lock_sha256: str,
    entries: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    """Return the exact immutable source/machine binding required by a waiver."""

    return {
        "official_source_sha256": str(input_lock["official_source_sha256"]),
        "source_bundle_sha256": str(input_lock["source_bundle_sha256"]),
        "step19_manifest_sha256": str(input_lock["step19_manifest_sha256"]),
        "packet_index_sha256": str(input_lock["packet_index_sha256"]),
        "packet_index_core_sha256": str(input_lock["packet_index_core_sha256"]),
        "packet_index_agent_input_tree_sha256": str(
            input_lock["packet_index_agent_input_tree_sha256"]
        ),
        "native_input_lock_sha256": input_lock_sha256,
        "native_case_inventory_sha256": str(input_lock["case_inventory_sha256"]),
        "native_case_artifacts_sha256": native_case_artifacts_sha256(entries),
        "native_machine_lock_sha256": machine_lock_sha256,
    }


def validate_operator_waiver_receipt(
    path: str | Path,
    *,
    input_lock: Mapping[str, Any],
    input_lock_sha256: str,
    machine_lock_sha256: str,
    entries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate a transparent operator waiver against exact current artifacts.

    This function deliberately does not infer or synthesize human review.  It
    requires the receipt to say that zero human sign-offs and no reviewer
    identity/signature are claimed.
    """

    waiver_path = _repo_path(path)
    if not waiver_path.is_file() or waiver_path.is_symlink():
        raise WebArenaNativeClaimError(
            f"operator waiver file missing or symlinked: {waiver_path}"
        )
    waiver = _require_mapping(_load_json(waiver_path), "operator waiver")
    schema = _load_json(PACKAGE_ROOT / OPERATOR_WAIVER_SCHEMA)
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(waiver), key=lambda error: list(error.path))
    if errors:
        raise WebArenaNativeClaimError(
            "operator waiver violates schema: "
            + "; ".join(
                f"{list(error.path)}: {error.message}" for error in errors[:8]
            )
        )
    statement = str(waiver["authorization_statement"])
    statement_sha256 = hashlib.sha256(statement.encode("utf-8")).hexdigest()
    if waiver.get("authorization_statement_sha256") != statement_sha256:
        raise WebArenaNativeClaimError("operator waiver authorization statement hash mismatch")
    expected_source = expected_operator_waiver_source_binding(
        input_lock=input_lock,
        input_lock_sha256=input_lock_sha256,
        machine_lock_sha256=machine_lock_sha256,
        entries=entries,
    )
    if waiver.get("source_binding") != expected_source:
        raise WebArenaNativeClaimError("operator waiver source/machine binding mismatch")
    if waiver.get("execution_binding") != EXPECTED_EXECUTION_BINDING:
        raise WebArenaNativeClaimError("operator waiver model/route/reset binding mismatch")
    if any(
        (
            waiver.get("human_signoff_claimed") is not False,
            waiver.get("reviewer_identity_or_signature_claimed") is not False,
            waiver.get("human_signed") != 0,
            waiver.get("machine_validated") != EXPECTED_CASES,
            waiver.get("fallback_contracts") != 0,
        )
    ):
        raise WebArenaNativeClaimError(
            "operator waiver must preserve zero human claims, 812 machine validations, and zero fallback contracts"
        )
    return waiver


def _operator_waiver_lock(
    *,
    waiver: Mapping[str, Any],
    waiver_input_path: Path,
    input_lock_sha256: str,
    machine_lock_sha256: str,
    case_artifacts_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": OPERATOR_WAIVER_LOCK_SCHEMA_VERSION,
        "status": "active",
        "scope": OPERATOR_WAIVER_SCOPE,
        "formal_lock_basis": OPERATOR_WAIVER_BASIS,
        "waiver_input_path": _repo_relative(waiver_input_path),
        "waiver_input_sha256": file_sha256(waiver_input_path),
        "authorization_source": waiver["authorization_source"],
        "authorization_statement_sha256": waiver["authorization_statement_sha256"],
        "authorization_date": waiver["authorization_date"],
        "authorization_timezone": waiver["authorization_timezone"],
        "authorized_by_role": waiver["authorized_by_role"],
        "human_signoff_claimed": False,
        "reviewer_identity_or_signature_claimed": False,
        "human_signoff_requirement_waived": True,
        "formal_human_locked": False,
        "formal_policy_locked": True,
        "human_signed": 0,
        "machine_validated": EXPECTED_CASES,
        "fallback_contracts": 0,
        "native_input_lock_sha256": input_lock_sha256,
        "native_machine_lock_sha256": machine_lock_sha256,
        "native_case_artifacts_sha256": case_artifacts_sha256,
        "execution_binding": waiver["execution_binding"],
    }


def _policy_lock_record(
    *,
    entry: Mapping[str, Any],
    waiver_input_sha256: str,
    waiver_lock_sha256: str,
) -> dict[str, Any]:
    case_id = str(entry["case_unit_id"])
    return {
        "schema_version": POLICY_LOCK_SCHEMA_VERSION,
        "status": "formal_policy_locked",
        "lock_record_id": f"policy-lock-webarena-verified-{case_id}-v1",
        "formal_lock_basis": OPERATOR_WAIVER_BASIS,
        "domain": DOMAIN,
        "case_unit_id": case_id,
        "task_id": str(entry["task_id"]),
        "task_revision": entry["task_revision"],
        "input_lock_sha256": entry["input_lock_sha256"],
        "native_ir_sha256": entry["native_ir_sha256"],
        "draft_contract_sha256": entry["draft_contract_sha256"],
        "draft_checklist_sha256": entry["draft_checklist_sha256"],
        "machine_review_sha256": entry["machine_review_sha256"],
        "operator_waiver_input_sha256": waiver_input_sha256,
        "operator_waiver_lock_sha256": waiver_lock_sha256,
        "human_signoff_claimed": False,
        "reviewer_identity_or_signature_claimed": False,
        "human_signoff_requirement_waived": True,
        "human_signed": 0,
        "machine_validation_status": "accepted",
        "formal_human_locked": False,
        "formal_policy_locked": True,
    }


def _contract_review(contract: Mapping[str, Any], signoff: Mapping[str, Any], *, source_bundle_hash: str) -> dict[str, Any]:
    start = _parse_timestamp(signoff["review_started_at"], "review_started_at")
    finish = _parse_timestamp(signoff["review_finished_at"], "review_finished_at")
    review = {
        "schema_version": "contract_review/v1",
        "review_id": signoff["review_id"],
        "contract_id": contract["contract_id"],
        "contract_version": contract["contract_version"],
        "domain": DOMAIN,
        "case_unit_id": contract["case_unit_id"],
        "review_started_at": signoff["review_started_at"],
        "review_finished_at": signoff["review_finished_at"],
        "duration_minutes": (finish - start).total_seconds() / 60.0,
        "reviewer_id": signoff["reviewer_id"],
        "source_bundle_hash": source_bundle_hash,
        "visible_input_hash": contract["source_support"]["native_ir_sha256"],
        "review_actions": [
            "source-checked canonical packet against official task and evaluator files",
            "verified every evaluator config and all-evaluator conjunction",
            "verified decisive artifact requirements and S/F/U mapping",
        ],
        "source_hierarchy_applied": [
            "official evaluator semantics",
            "official task text and revision",
            "official evaluator input/output schemas",
        ],
        "unsupported_requirements_removed": True,
        "requirements_marked_stronger_measurement": [],
        "final_lock_decision": "lock",
        "contract_hash": contract["contract_hash"],
        "manifest_hash": contract["manifest_hash"],
        "contract_drafting_llm_call_id": contract["contract_drafting_llm_call_id"],
        "contract_draft_id": contract["contract_draft_id"],
        "draft_created_at": signoff["review_started_at"],
        "locked_at": signoff["locked_at"],
        "locked_by": signoff["reviewer_id"],
        "first_scoring_started_at": signoff["first_scoring_started_at"],
    }
    report = validate_object("contract_review", review, raise_on_error=False)
    if report.issues:
        raise WebArenaNativeClaimError(
            "rendered contract review violates schema: "
            + "; ".join(f"{item.path}: {item.message}" for item in report.issues[:8])
        )
    return review


def _tree_hash(root: Path) -> str:
    entries = []
    for path in sorted(item for item in root.rglob("*") if item.is_file() and not item.is_symlink()):
        entries.append({"path": path.relative_to(root).as_posix(), "sha256": file_sha256(path)})
    return object_sha256(entries)


def build_native_claim_package(
    *,
    source_bundle_path: str | Path = DEFAULT_SOURCE_BUNDLE,
    step19_manifest_path: str | Path = DEFAULT_STEP19_MANIFEST,
    packet_index_path: str | Path = DEFAULT_PACKET_INDEX,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    human_signoffs_path: str | Path | None = None,
    operator_waiver_path: str | Path | None = None,
    replace: bool = False,
) -> dict[str, Any]:
    source_bundle_path = _repo_path(source_bundle_path)
    step19_manifest_path = _repo_path(step19_manifest_path)
    packet_index_path = _repo_path(packet_index_path)
    output_root = _repo_path(output_root)
    human_path = _repo_path(human_signoffs_path) if human_signoffs_path is not None else None
    waiver_path = _repo_path(operator_waiver_path) if operator_waiver_path is not None else None
    if human_path is not None and waiver_path is not None:
        raise WebArenaNativeClaimError(
            "human signoffs and operator machine-only waiver are mutually exclusive"
        )

    for path in (source_bundle_path, step19_manifest_path, packet_index_path):
        if not path.is_file() or path.is_symlink():
            raise WebArenaNativeClaimError(f"canonical input missing or symlinked: {path}")
    pinned_files = {
        source_bundle_path: EXPECTED_SOURCE_BUNDLE_SHA256,
        step19_manifest_path: EXPECTED_STEP19_MANIFEST_SHA256,
        packet_index_path: EXPECTED_PACKET_INDEX_SHA256,
    }
    for path, expected in pinned_files.items():
        if file_sha256(path) != expected:
            raise WebArenaNativeClaimError(
                f"pinned canonical input hash mismatch for {_repo_relative(path)}: "
                f"expected={expected} actual={file_sha256(path)}"
            )
    source_bundle = _require_mapping(_load_json(source_bundle_path), "source bundle")
    manifest = _require_mapping(_load_json(step19_manifest_path), "Step19 manifest")
    packet_index = _require_mapping(_load_json(packet_index_path), "packet index")
    if source_bundle.get("schema_version") != "contract_source_bundle.v2":
        raise WebArenaNativeClaimError("wrong source bundle schema")
    if source_bundle.get("source_count") != EXPECTED_CASES:
        raise WebArenaNativeClaimError("source bundle source_count must equal 812")
    if manifest.get("schema_version") != "webarena_verified_full_812_manifest/v1" or manifest.get("status") != "frozen":
        raise WebArenaNativeClaimError("Step19 manifest must be the frozen full-812 manifest")
    benchmark = _require_mapping(manifest.get("benchmark"), "Step19 benchmark")
    if benchmark.get("version") != BENCHMARK_VERSION or benchmark.get("source_sha256") != OFFICIAL_SOURCE_SHA256:
        raise WebArenaNativeClaimError("Step19 benchmark version/source hash mismatch")
    if benchmark.get("tag_commit") != OFFICIAL_COMMIT:
        raise WebArenaNativeClaimError("Step19 official commit mismatch")
    if packet_index.get("packet_count") != EXPECTED_CASES or packet_index.get("status") != "frozen":
        raise WebArenaNativeClaimError("packet index must freeze exactly 812 packets")
    if packet_index.get("index_core_sha256") != EXPECTED_PACKET_INDEX_CORE_SHA256:
        raise WebArenaNativeClaimError("packet index core hash mismatch")
    if packet_index.get("source_bundle_sha256") != EXPECTED_SOURCE_BUNDLE_SHA256:
        raise WebArenaNativeClaimError("packet index source-bundle hash linkage mismatch")
    if packet_index.get("agent_input_tree_sha256") != EXPECTED_PACKET_INDEX_AGENT_INPUT_TREE_SHA256:
        raise WebArenaNativeClaimError("packet index canonical agent_input tree hash mismatch")

    packet_root = packet_index_path.parent
    agent_input_before = agent_input_tree_sha256(packet_root)
    input_lock = _input_lock(
        source_bundle_path=source_bundle_path,
        step19_manifest_path=step19_manifest_path,
        packet_index_path=packet_index_path,
        source_bundle=source_bundle,
        manifest=manifest,
        packet_index=packet_index,
        agent_input_hash=agent_input_before,
    )
    input_lock_sha256 = hashlib.sha256(json_file_bytes(input_lock)).hexdigest()
    compiler = compiler_identity()
    sources_by_id = {str(item["case_unit_id"]): item for item in source_bundle["sources"]}
    cases_by_id = {str(item["task_id"]): item for item in manifest["cases"]}
    official_path = _repo_path(str(benchmark["source_path"]))
    if file_sha256(official_path) != OFFICIAL_SOURCE_SHA256:
        raise WebArenaNativeClaimError("official 812 source file hash mismatch")
    official_items = _require_sequence(_load_json(official_path), "official source")
    official_by_id = {str(item["task_id"]): item for item in official_items if isinstance(item, Mapping)}
    if set(official_by_id) != set(EXPECTED_TASK_IDS):
        raise WebArenaNativeClaimError("official task IDs must be exactly 0..811")

    staging_parent = output_root.parent
    staging_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=staging_parent))
    try:
        input_lock_path = staging / "input_lock.json"
        _write_json(input_lock_path, input_lock)
        _write_sha256_sidecar(input_lock_path)
        entries: list[dict[str, Any]] = []
        machine_lock_lines: list[dict[str, Any]] = []
        for task_id in EXPECTED_TASK_IDS:
            ir = compile_case_ir(
                source=sources_by_id[task_id],
                manifest_case=cases_by_id[task_id],
                official_task=official_by_id[task_id],
                source_bundle_path=source_bundle_path,
                source_bundle_sha256=file_sha256(source_bundle_path),
                step19_manifest_path=step19_manifest_path,
                step19_manifest_sha256=file_sha256(step19_manifest_path),
                packet_index_path=packet_index_path,
                packet_index_sha256=file_sha256(packet_index_path),
                input_lock_sha256=input_lock_sha256,
                compiler=compiler,
            )
            ir_issues = validate_native_ir(ir)
            if ir_issues:
                raise WebArenaNativeClaimError(f"case {task_id} IR invalid: {'; '.join(ir_issues)}")
            ir_rel = f"drafts/ir/{task_id}/native_claim_ir.json"
            contract_rel = f"drafts/contracts/{task_id}/evidence_contract.json"
            checklist_rel = f"drafts/checklists/{task_id}/case_checklist.yaml"
            review_rel = f"machine_reviews/{task_id}/review.json"
            ir_path = staging / ir_rel
            contract_path = staging / contract_rel
            checklist_path = staging / checklist_rel
            review_path = staging / review_rel
            _write_json(ir_path, ir)
            contract = render_contract(
                ir,
                output_path=f"{_repo_relative(output_root)}/{contract_rel}",
            )
            checklist = render_checklist(ir)
            _write_json(contract_path, contract)
            _write_yaml(checklist_path, checklist)
            machine_review = _expected_machine_review(
                ir=ir,
                ir_path=f"{_repo_relative(output_root)}/{ir_rel}",
                ir_sha256=file_sha256(ir_path),
                contract_path=f"{_repo_relative(output_root)}/{contract_rel}",
                contract_sha256=file_sha256(contract_path),
                checklist_path=f"{_repo_relative(output_root)}/{checklist_rel}",
                checklist_sha256=file_sha256(checklist_path),
                input_lock_sha256=input_lock_sha256,
            )
            _write_json(review_path, machine_review)
            identity = ir["identity"]
            source_binding = ir["source_binding"]
            entry = {
                "domain": DOMAIN,
                "case_unit_id": task_id,
                "task_id": task_id,
                "task_revision": identity["task_revision"],
                "input_lock_sha256": input_lock_sha256,
                "packet_source_task_sha256": source_binding["packet_source_task_sha256"],
                "manifest_source_task_sha256": source_binding["manifest_source_task_sha256"],
                "evaluator_config_sha256": source_binding["evaluator_config_sha256"],
                "evaluator_count": ir["native_semantics"]["evaluator_count"],
                "native_ir_path": f"{_repo_relative(output_root)}/{ir_rel}",
                "native_ir_sha256": file_sha256(ir_path),
                "draft_contract_path": f"{_repo_relative(output_root)}/{contract_rel}",
                "draft_contract_sha256": file_sha256(contract_path),
                "draft_checklist_path": f"{_repo_relative(output_root)}/{checklist_rel}",
                "draft_checklist_sha256": file_sha256(checklist_path),
                "machine_review_path": f"{_repo_relative(output_root)}/{review_rel}",
                "machine_review_sha256": file_sha256(review_path),
                "human_signoff_status": "pending",
                "formal_lock_basis": None,
                "locked_contract_path": None,
                "locked_contract_sha256": None,
                "locked_checklist_path": None,
                "locked_checklist_sha256": None,
                "contract_review_path": None,
                "contract_review_sha256": None,
                "policy_lock_record_path": None,
                "policy_lock_record_sha256": None,
            }
            entries.append(entry)
            machine_lock_lines.append(
                {
                    "schema_version": MACHINE_LOCK_SCHEMA_VERSION,
                    "status": "machine_locked_not_formal_human_lock",
                    "machine_locked": True,
                    "formal_human_locked": False,
                    "domain": DOMAIN,
                    "case_unit_id": task_id,
                    "task_id": task_id,
                    "task_revision": identity["task_revision"],
                    "input_lock_sha256": input_lock_sha256,
                    "native_ir_sha256": entry["native_ir_sha256"],
                    "draft_contract_sha256": entry["draft_contract_sha256"],
                    "draft_checklist_sha256": entry["draft_checklist_sha256"],
                    "machine_review_sha256": entry["machine_review_sha256"],
                }
            )

        machine_lock_path = staging / "locks" / "machine_locks.jsonl"
        machine_lock_path.parent.mkdir(parents=True, exist_ok=True)
        machine_lock_path.write_text(
            "".join(
                json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n"
                for item in machine_lock_lines
            ),
            encoding="utf-8",
        )
        _write_sha256_sidecar(machine_lock_path)
        machine_lock_sha256 = file_sha256(machine_lock_path)

        signoffs = _load_human_signoffs(human_path, entries, input_lock_sha256)
        human_lock_rel: str | None = None
        human_lock_sha256: str | None = None
        waiver: dict[str, Any] | None = None
        waiver_lock_rel: str | None = None
        waiver_lock_sha256: str | None = None
        if signoffs:
            human_lock_rel = "locked/human_signoffs.jsonl"
            human_lock_path = staging / human_lock_rel
            human_lock_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(human_path, human_lock_path)
            human_lock_sha256 = file_sha256(human_lock_path)
            for entry in entries:
                task_id = entry["case_unit_id"]
                signoff = signoffs[task_id]
                ir = _require_mapping(
                    _load_json(staging / f"drafts/ir/{task_id}/native_claim_ir.json"),
                    f"IR {task_id}",
                )
                locked_contract_rel = f"locked/contracts/{task_id}/evidence_contract.json"
                locked_checklist_rel = f"locked/checklists/{task_id}/case_checklist.yaml"
                contract_review_rel = f"locked/reviews/{task_id}/contract_review.json"
                locked_contract = render_contract(
                    ir,
                    output_path=f"{_repo_relative(output_root)}/{locked_contract_rel}",
                    locked=signoff,
                )
                locked_checklist = render_checklist(ir)
                _write_json(staging / locked_contract_rel, locked_contract)
                _write_yaml(staging / locked_checklist_rel, locked_checklist)
                review = _contract_review(
                    locked_contract,
                    signoff,
                    source_bundle_hash=file_sha256(source_bundle_path),
                )
                _write_json(staging / contract_review_rel, review)
                entry.update(
                    {
                        "human_signoff_status": "approved",
                        "formal_lock_basis": "human_signoff",
                        "locked_contract_path": f"{_repo_relative(output_root)}/{locked_contract_rel}",
                        "locked_contract_sha256": file_sha256(staging / locked_contract_rel),
                        "locked_checklist_path": f"{_repo_relative(output_root)}/{locked_checklist_rel}",
                        "locked_checklist_sha256": file_sha256(staging / locked_checklist_rel),
                        "contract_review_path": f"{_repo_relative(output_root)}/{contract_review_rel}",
                        "contract_review_sha256": file_sha256(staging / contract_review_rel),
                    }
                )
        elif waiver_path is not None:
            waiver = validate_operator_waiver_receipt(
                waiver_path,
                input_lock=input_lock,
                input_lock_sha256=input_lock_sha256,
                machine_lock_sha256=machine_lock_sha256,
                entries=entries,
            )
            waiver_lock_rel = "locked/operator_waiver.json"
            waiver_lock_path = staging / waiver_lock_rel
            waiver_lock = _operator_waiver_lock(
                waiver=waiver,
                waiver_input_path=waiver_path,
                input_lock_sha256=input_lock_sha256,
                machine_lock_sha256=machine_lock_sha256,
                case_artifacts_sha256=native_case_artifacts_sha256(entries),
            )
            _write_json(waiver_lock_path, waiver_lock)
            _write_sha256_sidecar(waiver_lock_path)
            waiver_lock_sha256 = file_sha256(waiver_lock_path)
            waiver_input_sha256 = file_sha256(waiver_path)
            for entry in entries:
                task_id = entry["case_unit_id"]
                ir = _require_mapping(
                    _load_json(staging / f"drafts/ir/{task_id}/native_claim_ir.json"),
                    f"IR {task_id}",
                )
                locked_contract_rel = f"locked/contracts/{task_id}/evidence_contract.json"
                locked_checklist_rel = f"locked/checklists/{task_id}/case_checklist.yaml"
                policy_lock_rel = f"locked/policy_locks/{task_id}/policy_lock.json"
                policy_lock = _policy_lock_record(
                    entry=entry,
                    waiver_input_sha256=waiver_input_sha256,
                    waiver_lock_sha256=waiver_lock_sha256,
                )
                _write_json(staging / policy_lock_rel, policy_lock)
                lock_context = {
                    "locked_at": waiver["authorization_date"],
                    "locked_by": "operator-machine-only-waiver-no-human-review",
                    "lock_record_id": policy_lock["lock_record_id"],
                    "formal_lock_basis": OPERATOR_WAIVER_BASIS,
                    "operator_waiver_lock_sha256": waiver_lock_sha256,
                }
                locked_contract = render_contract(
                    ir,
                    output_path=f"{_repo_relative(output_root)}/{locked_contract_rel}",
                    locked=lock_context,
                )
                locked_checklist = render_checklist(ir)
                _write_json(staging / locked_contract_rel, locked_contract)
                _write_yaml(staging / locked_checklist_rel, locked_checklist)
                entry.update(
                    {
                        "human_signoff_status": "waived_not_signed",
                        "formal_lock_basis": OPERATOR_WAIVER_BASIS,
                        "locked_contract_path": f"{_repo_relative(output_root)}/{locked_contract_rel}",
                        "locked_contract_sha256": file_sha256(staging / locked_contract_rel),
                        "locked_checklist_path": f"{_repo_relative(output_root)}/{locked_checklist_rel}",
                        "locked_checklist_sha256": file_sha256(staging / locked_checklist_rel),
                        "policy_lock_record_path": f"{_repo_relative(output_root)}/{policy_lock_rel}",
                        "policy_lock_record_sha256": file_sha256(staging / policy_lock_rel),
                    }
                )

        policy_locked_count = EXPECTED_CASES if waiver is not None else 0
        locked_count = len(signoffs) + policy_locked_count
        counts = {
            "native_ir": len(entries),
            "draft_contracts": len(entries),
            "draft_checklists": len(entries),
            "machine_validated": len(entries),
            "human_signed": len(signoffs),
            "policy_locked": policy_locked_count,
            "locked_contracts": locked_count,
            "locked_checklists": locked_count,
        }
        index = {
            "schema_version": INDEX_SCHEMA_VERSION,
            "domain": DOMAIN,
            "benchmark_version": BENCHMARK_VERSION,
            "expected_count": EXPECTED_CASES,
            "path_scope": "repository_relative",
            "package_root": _repo_relative(output_root),
            "input_lock_path": f"{_repo_relative(output_root)}/input_lock.json",
            "input_lock_sha256": input_lock_sha256,
            "compiler": compiler,
            "machine_lock_path": f"{_repo_relative(output_root)}/locks/machine_locks.jsonl",
            "machine_lock_sha256": machine_lock_sha256,
            "human_signoff_input_path": _repo_relative(human_path) if human_path else None,
            "human_signoff_input_sha256": file_sha256(human_path) if human_path else None,
            "human_signoff_lock_path": (
                f"{_repo_relative(output_root)}/{human_lock_rel}" if human_lock_rel else None
            ),
            "human_signoff_lock_sha256": human_lock_sha256,
            "operator_waiver_input_path": _repo_relative(waiver_path) if waiver_path else None,
            "operator_waiver_input_sha256": file_sha256(waiver_path) if waiver_path else None,
            "operator_waiver_lock_path": (
                f"{_repo_relative(output_root)}/{waiver_lock_rel}" if waiver_lock_rel else None
            ),
            "operator_waiver_lock_sha256": waiver_lock_sha256,
            "counts": counts,
            "cases": entries,
        }
        index_path = staging / "index.json"
        _write_json(index_path, index)
        _write_sha256_sidecar(index_path)

        agent_input_after = agent_input_tree_sha256(packet_root)
        if agent_input_after != agent_input_before:
            raise WebArenaNativeClaimError("agent_input.json tree changed during native-claim compilation")
        formal_human = len(signoffs) == EXPECTED_CASES
        formal_policy = policy_locked_count == EXPECTED_CASES
        formal = formal_human or formal_policy
        gates = {
            "input_set_exact": len(entries) == EXPECTED_CASES,
            "source_hashes_valid": True,
            "native_semantics_complete": True,
            "contracts_schema_valid": True,
            "checklists_schema_valid": True,
            "machine_validation_complete": counts["machine_validated"] == EXPECTED_CASES,
            "human_signoff_complete": formal_human,
            "human_signoff_requirement_waived": formal_policy,
            "operator_waiver_valid": formal_policy,
            "formal_policy_locks_complete": formal_policy,
            "formal_locks_complete": formal and counts["locked_contracts"] == EXPECTED_CASES,
            "agent_input_tree_unchanged": agent_input_after == agent_input_before,
        }
        core_gate_fields = (
            "input_set_exact",
            "source_hashes_valid",
            "native_semantics_complete",
            "contracts_schema_valid",
            "checklists_schema_valid",
            "machine_validation_complete",
            "formal_locks_complete",
            "agent_input_tree_unchanged",
        )
        formal_launch_eligible = (
            formal
            and all(gates[field] for field in core_gate_fields)
            and (gates["human_signoff_complete"] or gates["operator_waiver_valid"])
        )
        if formal_human:
            acceptance_status = "accepted"
        elif formal_policy:
            acceptance_status = "accepted_machine_only_operator_waiver"
        else:
            acceptance_status = "machine_validated_human_signoff_pending"
        acceptance = {
            "schema_version": ACCEPTANCE_SCHEMA_VERSION,
            "status": acceptance_status,
            "formal_launch_eligible": formal_launch_eligible,
            "domain": DOMAIN,
            "benchmark_version": BENCHMARK_VERSION,
            "expected_count": EXPECTED_CASES,
            "input_lock_sha256": input_lock_sha256,
            "index_path": f"{_repo_relative(output_root)}/index.json",
            "index_sha256": file_sha256(index_path),
            "counts": counts,
            "gates": gates,
            "machine_validation": {
                "status": "accepted",
                "validator": compiler,
                "review_type": "deterministic_machine_validation_not_human_review",
            },
            "machine_contract_gate": {
                "machine_locked": True,
                "machine_locked_count": EXPECTED_CASES,
                "native_contract_count": EXPECTED_CASES,
                "fallback_contract_count": 0,
                "formal_human_locked": formal_human,
                "formal_policy_locked": formal_policy,
                "authorizes_formal_launch": formal_launch_eligible,
            },
            "human_signoff": {
                "status": (
                    "complete" if formal_human else "waived_not_signed" if formal_policy else "pending"
                ),
                "required_count": EXPECTED_CASES,
                "signed_count": len(signoffs),
                "lock_path": (
                    f"{_repo_relative(output_root)}/{human_lock_rel}" if human_lock_rel else None
                ),
                "lock_sha256": human_lock_sha256,
            },
            "operator_waiver": {
                "status": "active" if formal_policy else "absent",
                "requirement_waived": formal_policy,
                "human_signoff_claimed": False,
                "reviewer_identity_or_signature_claimed": False,
                "input_path": _repo_relative(waiver_path) if waiver_path else None,
                "input_sha256": file_sha256(waiver_path) if waiver_path else None,
                "lock_path": (
                    f"{_repo_relative(output_root)}/{waiver_lock_rel}"
                    if waiver_lock_rel
                    else None
                ),
                "lock_sha256": waiver_lock_sha256,
            },
            "agent_input_tree_sha256_before": agent_input_before,
            "agent_input_tree_sha256_after": agent_input_after,
            "packet_index_agent_input_tree_sha256": packet_index.get("agent_input_tree_sha256"),
            "blockers": (
                []
                if formal
                else [
                    "812 hash-bound human source-check signoffs are not present and no operator machine-only waiver is active"
                ]
            ),
        }
        acceptance_path = staging / "acceptance.json"
        _write_json(acceptance_path, acceptance)
        _write_sha256_sidecar(acceptance_path)

        validation = validate_native_claim_package(staging, current_source_check=True)
        if validation["status"] != "ok":
            raise WebArenaNativeClaimError(
                "generated package failed strict validation: " + "; ".join(validation["issues"][:8])
            )
        if output_root.exists():
            if _tree_hash(output_root) == _tree_hash(staging):
                shutil.rmtree(staging)
                return acceptance
            if not replace:
                raise WebArenaNativeClaimError(
                    f"output root exists with different content; pass replace=True after reviewing drift: {output_root}"
                )
            backup = output_root.with_name(f".{output_root.name}.old-{os.getpid()}")
            os.replace(output_root, backup)
            try:
                os.replace(staging, output_root)
            except Exception:
                os.replace(backup, output_root)
                raise
            shutil.rmtree(backup)
        else:
            os.replace(staging, output_root)
        return acceptance
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def validate_native_claim_package(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    *,
    current_source_check: bool = True,
) -> dict[str, Any]:
    root = _repo_path(output_root)
    issues: list[str] = []
    try:
        index_path = root / "index.json"
        acceptance_path = root / "acceptance.json"
        input_lock_path = root / "input_lock.json"
        index = _require_mapping(_load_json(index_path), "native claim index")
        acceptance = _require_mapping(_load_json(acceptance_path), "native claim acceptance")
        input_lock = _require_mapping(_load_json(input_lock_path), "native claim input lock")
        if index.get("schema_version") != INDEX_SCHEMA_VERSION:
            issues.append("wrong index schema_version")
        if acceptance.get("schema_version") != ACCEPTANCE_SCHEMA_VERSION:
            issues.append("wrong acceptance schema_version")
        if input_lock.get("schema_version") != INPUT_LOCK_SCHEMA_VERSION:
            issues.append("wrong input-lock schema_version")
        input_hash = file_sha256(input_lock_path)
        if index.get("input_lock_sha256") != input_hash or acceptance.get("input_lock_sha256") != input_hash:
            issues.append("input lock hash linkage mismatch")
        if acceptance.get("index_sha256") != file_sha256(index_path):
            issues.append("acceptance index_sha256 mismatch")
        for path in (index_path, acceptance_path, input_lock_path, root / "locks" / "machine_locks.jsonl"):
            sidecar = path.with_suffix(path.suffix + ".sha256")
            expected_line = f"{file_sha256(path)}  {path.name}\n" if path.is_file() else None
            if not sidecar.is_file() or sidecar.read_text(encoding="utf-8") != expected_line:
                issues.append(f"missing or invalid SHA-256 sidecar for {path.relative_to(root)}")
        entries = index.get("cases")
        package_root = index.get("package_root")
        if index.get("path_scope") != "repository_relative" or not isinstance(package_root, str):
            issues.append("index must declare repository-relative package_root path scope")
            package_root = _repo_relative(root) if root.is_relative_to(PACKAGE_ROOT) else ""
        if not isinstance(entries, list) or len(entries) != EXPECTED_CASES:
            issues.append("index must contain exactly 812 cases")
            entries = []
        ids = [str(item.get("case_unit_id")) for item in entries if isinstance(item, Mapping)]
        if sorted(ids, key=int) != list(EXPECTED_TASK_IDS) if ids else True:
            issues.append("index case IDs are not exactly unique 0..811")
        machine_lock_path = root / "locks" / "machine_locks.jsonl"
        machine_locks = [json.loads(line) for line in machine_lock_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(machine_locks) != EXPECTED_CASES:
            issues.append("machine lock JSONL must contain exactly 812 entries")
        approved_entries = [
            item
            for item in entries
            if isinstance(item, Mapping) and item.get("human_signoff_status") == "approved"
        ]
        waived_entries = [
            item
            for item in entries
            if isinstance(item, Mapping)
            and item.get("human_signoff_status") == "waived_not_signed"
        ]
        if approved_entries and waived_entries:
            issues.append("human signoff and operator-waiver formal lock modes cannot be mixed")
        signoffs: dict[str, dict[str, Any]] = {}
        if approved_entries:
            human_lock_value = index.get("human_signoff_lock_path")
            if not isinstance(human_lock_value, str):
                issues.append("approved cases require a package-local human signoff lock")
            else:
                human_lock_path = _safe_output_path(root, human_lock_value, package_root=package_root)
                if (
                    not human_lock_path.is_file()
                    or human_lock_path.is_symlink()
                    or file_sha256(human_lock_path) != index.get("human_signoff_lock_sha256")
                ):
                    issues.append("package-local human signoff lock path/hash mismatch")
                else:
                    try:
                        signoffs = _load_human_signoffs(human_lock_path, entries, input_hash)
                    except WebArenaNativeClaimError as exc:
                        issues.append(f"human signoff lock invalid: {exc}")
        waiver: dict[str, Any] | None = None
        waiver_lock: dict[str, Any] | None = None
        waiver_lock_hash: str | None = None
        if waived_entries:
            waiver_input_value = index.get("operator_waiver_input_path")
            waiver_lock_value = index.get("operator_waiver_lock_path")
            if not isinstance(waiver_input_value, str) or not isinstance(
                waiver_lock_value, str
            ):
                issues.append("waived cases require operator waiver input and package-local lock paths")
            else:
                waiver_input_path = _repo_path(waiver_input_value)
                waiver_lock_path = _safe_output_path(
                    root, waiver_lock_value, package_root=package_root
                )
                if (
                    not waiver_lock_path.is_file()
                    or waiver_lock_path.is_symlink()
                    or file_sha256(waiver_lock_path)
                    != index.get("operator_waiver_lock_sha256")
                ):
                    issues.append("package-local operator waiver lock path/hash mismatch")
                else:
                    try:
                        waiver = validate_operator_waiver_receipt(
                            waiver_input_path,
                            input_lock=input_lock,
                            input_lock_sha256=input_hash,
                            machine_lock_sha256=file_sha256(machine_lock_path),
                            entries=entries,
                        )
                    except WebArenaNativeClaimError as exc:
                        issues.append(f"operator waiver invalid: {exc}")
                    else:
                        if file_sha256(waiver_input_path) != index.get(
                            "operator_waiver_input_sha256"
                        ):
                            issues.append("operator waiver input hash mismatch")
                        waiver_lock = _require_mapping(
                            _load_json(waiver_lock_path), "operator waiver lock"
                        )
                        expected_waiver_lock = _operator_waiver_lock(
                            waiver=waiver,
                            waiver_input_path=waiver_input_path,
                            input_lock_sha256=input_hash,
                            machine_lock_sha256=file_sha256(machine_lock_path),
                            case_artifacts_sha256=native_case_artifacts_sha256(entries),
                        )
                        if waiver_lock != expected_waiver_lock:
                            issues.append("operator waiver lock is stale or noncanonical")
                        waiver_lock_hash = file_sha256(waiver_lock_path)
                        sidecar = waiver_lock_path.with_suffix(
                            waiver_lock_path.suffix + ".sha256"
                        )
                        expected_line = (
                            f"{waiver_lock_hash}  {waiver_lock_path.name}\n"
                        )
                        if (
                            not sidecar.is_file()
                            or sidecar.is_symlink()
                            or sidecar.read_text(encoding="utf-8") != expected_line
                        ):
                            issues.append("missing or invalid operator waiver lock SHA-256 sidecar")
        formal_human_count = 0
        formal_policy_count = 0
        for entry in entries:
            if not isinstance(entry, Mapping):
                issues.append("non-mapping index case entry")
                continue
            case_id = str(entry.get("case_unit_id"))
            if entry.get("domain") != DOMAIN or str(entry.get("task_id")) != case_id:
                issues.append(f"case {case_id} domain/case/task mismatch")
                continue
            if entry.get("input_lock_sha256") != input_hash:
                issues.append(f"case {case_id} input lock hash mismatch")
            paths_and_hashes = (
                ("native_ir_path", "native_ir_sha256"),
                ("draft_contract_path", "draft_contract_sha256"),
                ("draft_checklist_path", "draft_checklist_sha256"),
                ("machine_review_path", "machine_review_sha256"),
            )
            loaded_paths: dict[str, Path] = {}
            for path_field, hash_field in paths_and_hashes:
                relative = entry.get(path_field)
                if not isinstance(relative, str):
                    issues.append(f"case {case_id} missing {path_field}")
                    continue
                path = _safe_output_path(root, relative, package_root=package_root)
                loaded_paths[path_field] = path
                if not path.is_file() or path.is_symlink() or file_sha256(path) != entry.get(hash_field):
                    issues.append(f"case {case_id} {path_field} hash/path mismatch")
            if len(loaded_paths) != len(paths_and_hashes):
                continue
            ir = _require_mapping(_load_json(loaded_paths["native_ir_path"]), f"IR {case_id}")
            ir_issues = validate_native_ir(ir)
            issues.extend(f"case {case_id}: {message}" for message in ir_issues)
            contract = _require_mapping(_load_json(loaded_paths["draft_contract_path"]), f"contract {case_id}")
            checklist = _require_mapping(yaml.safe_load(loaded_paths["draft_checklist_path"].read_text(encoding="utf-8")), f"checklist {case_id}")
            expected_contract = render_contract(
                ir,
                output_path=entry["draft_contract_path"],
            )
            expected_checklist = render_checklist(ir)
            if contract != expected_contract:
                issues.append(f"case {case_id} draft contract is not the deterministic rendering of IR")
            if checklist != expected_checklist:
                issues.append(f"case {case_id} draft checklist is not the deterministic rendering of IR")
            if contract.get("contract_status") != "draft" or contract.get("main_result_eligible") is not False:
                issues.append(f"case {case_id} machine draft is incorrectly formal-locked")
            if contract_content_hash(contract) != contract.get("contract_hash"):
                issues.append(f"case {case_id} contract canonical hash mismatch")
            review = _require_mapping(_load_json(loaded_paths["machine_review_path"]), f"machine review {case_id}")
            expected_review = _expected_machine_review(
                ir=ir,
                ir_path=entry["native_ir_path"],
                ir_sha256=entry["native_ir_sha256"],
                contract_path=entry["draft_contract_path"],
                contract_sha256=entry["draft_contract_sha256"],
                checklist_path=entry["draft_checklist_path"],
                checklist_sha256=entry["draft_checklist_sha256"],
                input_lock_sha256=input_hash,
            )
            if review != expected_review or review.get("human_source_check_complete") is not False:
                issues.append(f"case {case_id} machine review mismatch or falsely claims human review")
            if entry.get("human_signoff_status") == "approved":
                formal_human_count += 1
                for path_field, hash_field in (
                    ("locked_contract_path", "locked_contract_sha256"),
                    ("locked_checklist_path", "locked_checklist_sha256"),
                    ("contract_review_path", "contract_review_sha256"),
                ):
                    relative = entry.get(path_field)
                    if not isinstance(relative, str):
                        issues.append(f"case {case_id} approved without {path_field}")
                        continue
                    path = _safe_output_path(root, relative, package_root=package_root)
                    if not path.is_file() or path.is_symlink() or file_sha256(path) != entry.get(hash_field):
                        issues.append(f"case {case_id} formal {path_field} mismatch")
                locked_path_value = entry.get("locked_contract_path")
                if isinstance(locked_path_value, str):
                    locked_contract = _require_mapping(
                        _load_json(_safe_output_path(root, locked_path_value, package_root=package_root)),
                        f"locked contract {case_id}",
                    )
                    if locked_contract.get("contract_status") != "locked" or locked_contract.get("main_result_eligible") is not True:
                        issues.append(f"case {case_id} approved contract is not locked/main-result eligible")
                    if not locked_contract.get("required_artifacts"):
                        issues.append(f"case {case_id} approved contract has empty required artifacts")
                    signoff = signoffs.get(case_id)
                    if signoff is None:
                        issues.append(f"case {case_id} approved without a valid human signoff")
                    else:
                        expected_locked = render_contract(
                            ir,
                            output_path=locked_path_value,
                            locked=signoff,
                        )
                        if locked_contract != expected_locked:
                            issues.append(
                                f"case {case_id} locked contract is not the deterministic human-approved rendering"
                            )
                        if contract_content_hash(locked_contract) != locked_contract.get("contract_hash"):
                            issues.append(f"case {case_id} locked contract canonical hash mismatch")
                        locked_checklist_value = entry.get("locked_checklist_path")
                        if isinstance(locked_checklist_value, str):
                            locked_checklist = _require_mapping(
                                yaml.safe_load(
                                    _safe_output_path(
                                        root,
                                        locked_checklist_value,
                                        package_root=package_root,
                                    ).read_text(encoding="utf-8")
                                ),
                                f"locked checklist {case_id}",
                            )
                            if locked_checklist != expected_checklist:
                                issues.append(f"case {case_id} locked checklist differs from approved draft")
                        review_value = entry.get("contract_review_path")
                        if isinstance(review_value, str):
                            review = _require_mapping(
                                _load_json(
                                    _safe_output_path(root, review_value, package_root=package_root)
                                ),
                                f"contract review {case_id}",
                            )
                            expected_review_record = _contract_review(
                                locked_contract,
                                signoff,
                                source_bundle_hash=input_lock["source_bundle_sha256"],
                            )
                            if review != expected_review_record:
                                issues.append(f"case {case_id} contract review/signoff linkage mismatch")
            elif entry.get("human_signoff_status") == "waived_not_signed":
                formal_policy_count += 1
                if entry.get("formal_lock_basis") != OPERATOR_WAIVER_BASIS:
                    issues.append(f"case {case_id} waiver formal lock basis mismatch")
                if any(
                    entry.get(field) is not None
                    for field in ("contract_review_path", "contract_review_sha256")
                ):
                    issues.append(
                        f"case {case_id} operator waiver must not fabricate a contract review"
                    )
                formal_paths: dict[str, Path] = {}
                for path_field, hash_field in (
                    ("locked_contract_path", "locked_contract_sha256"),
                    ("locked_checklist_path", "locked_checklist_sha256"),
                    ("policy_lock_record_path", "policy_lock_record_sha256"),
                ):
                    relative = entry.get(path_field)
                    if not isinstance(relative, str):
                        issues.append(f"case {case_id} waived without {path_field}")
                        continue
                    path = _safe_output_path(root, relative, package_root=package_root)
                    formal_paths[path_field] = path
                    if (
                        not path.is_file()
                        or path.is_symlink()
                        or file_sha256(path) != entry.get(hash_field)
                    ):
                        issues.append(f"case {case_id} formal {path_field} mismatch")
                if (
                    waiver is None
                    or waiver_lock_hash is None
                    or len(formal_paths) != 3
                ):
                    issues.append(f"case {case_id} waived without a valid operator waiver")
                else:
                    policy_lock = _require_mapping(
                        _load_json(formal_paths["policy_lock_record_path"]),
                        f"policy lock {case_id}",
                    )
                    expected_policy_lock = _policy_lock_record(
                        entry=entry,
                        waiver_input_sha256=str(index["operator_waiver_input_sha256"]),
                        waiver_lock_sha256=waiver_lock_hash,
                    )
                    if policy_lock != expected_policy_lock:
                        issues.append(f"case {case_id} policy lock is stale or noncanonical")
                    lock_context = {
                        "locked_at": waiver["authorization_date"],
                        "locked_by": "operator-machine-only-waiver-no-human-review",
                        "lock_record_id": policy_lock.get("lock_record_id"),
                        "formal_lock_basis": OPERATOR_WAIVER_BASIS,
                        "operator_waiver_lock_sha256": waiver_lock_hash,
                    }
                    locked_contract = _require_mapping(
                        _load_json(formal_paths["locked_contract_path"]),
                        f"locked contract {case_id}",
                    )
                    expected_locked = render_contract(
                        ir,
                        output_path=str(entry["locked_contract_path"]),
                        locked=lock_context,
                    )
                    if locked_contract != expected_locked:
                        issues.append(
                            f"case {case_id} locked contract is not the deterministic operator-waiver rendering"
                        )
                    if (
                        locked_contract.get("contract_status") != "locked"
                        or locked_contract.get("main_result_eligible") is not True
                        or contract_content_hash(locked_contract)
                        != locked_contract.get("contract_hash")
                    ):
                        issues.append(
                            f"case {case_id} waiver contract is not locked/main-result eligible/hash-valid"
                        )
                    support = locked_contract.get("source_support")
                    if not isinstance(support, Mapping) or any(
                        (
                            support.get("formal_lock_basis") != OPERATOR_WAIVER_BASIS,
                            support.get("human_source_check_complete") is not False,
                            support.get("human_signoff_claimed") is not False,
                            support.get("human_signoff_requirement_waived") is not True,
                            support.get("operator_waiver_lock_sha256")
                            != waiver_lock_hash,
                        )
                    ):
                        issues.append(f"case {case_id} waiver contract misstates lock provenance")
                    locked_checklist = _require_mapping(
                        yaml.safe_load(
                            formal_paths["locked_checklist_path"].read_text(
                                encoding="utf-8"
                            )
                        ),
                        f"locked checklist {case_id}",
                    )
                    if locked_checklist != expected_checklist:
                        issues.append(f"case {case_id} locked checklist differs from machine draft")
            elif any(entry.get(field) is not None for field in (
                "locked_contract_path", "locked_contract_sha256", "locked_checklist_path",
                "locked_checklist_sha256", "contract_review_path", "contract_review_sha256",
                "policy_lock_record_path", "policy_lock_record_sha256",
            )):
                issues.append(f"case {case_id} pending signoff has formal lock fields")
        counts = index.get("counts") if isinstance(index.get("counts"), Mapping) else {}
        expected_counts = {
            "native_ir": EXPECTED_CASES,
            "draft_contracts": EXPECTED_CASES,
            "draft_checklists": EXPECTED_CASES,
            "machine_validated": EXPECTED_CASES,
            "human_signed": formal_human_count,
            "policy_locked": formal_policy_count,
            "locked_contracts": formal_human_count + formal_policy_count,
            "locked_checklists": formal_human_count + formal_policy_count,
        }
        if dict(counts) != expected_counts or acceptance.get("counts") != expected_counts:
            issues.append("index/acceptance counts mismatch")
        formal_human = formal_human_count == EXPECTED_CASES
        formal_policy = formal_policy_count == EXPECTED_CASES
        formal = formal_human or formal_policy
        if acceptance.get("formal_launch_eligible") is not formal:
            issues.append("formal_launch_eligible does not match exact human-or-policy lock denominator")
        gates = acceptance.get("gates")
        if not isinstance(gates, Mapping):
            issues.append("acceptance gates block is missing")
        else:
            expected_gate_values = {
                "human_signoff_complete": formal_human,
                "human_signoff_requirement_waived": formal_policy,
                "operator_waiver_valid": formal_policy,
                "formal_policy_locks_complete": formal_policy,
                "formal_locks_complete": formal,
                "machine_validation_complete": True,
            }
            for field, value in expected_gate_values.items():
                if gates.get(field) is not value:
                    issues.append(f"acceptance gate {field} mismatch")
        expected_machine_gate = {
            "machine_locked": True,
            "machine_locked_count": EXPECTED_CASES,
            "native_contract_count": EXPECTED_CASES,
            "fallback_contract_count": 0,
            "formal_human_locked": formal_human,
            "formal_policy_locked": formal_policy,
            "authorizes_formal_launch": formal,
        }
        if acceptance.get("machine_contract_gate") != expected_machine_gate:
            issues.append("machine contract gate does not match exact formal lock basis")
        human_block = acceptance.get("human_signoff")
        expected_human_block = {
            "status": (
                "complete" if formal_human else "waived_not_signed" if formal_policy else "pending"
            ),
            "required_count": EXPECTED_CASES,
            "signed_count": formal_human_count,
            "lock_path": index.get("human_signoff_lock_path"),
            "lock_sha256": index.get("human_signoff_lock_sha256"),
        }
        if human_block != expected_human_block:
            issues.append("human signoff block misstates the actual zero-or-812 denominator")
        waiver_block = acceptance.get("operator_waiver")
        expected_waiver_block = {
            "status": "active" if formal_policy else "absent",
            "requirement_waived": formal_policy,
            "human_signoff_claimed": False,
            "reviewer_identity_or_signature_claimed": False,
            "input_path": index.get("operator_waiver_input_path"),
            "input_sha256": index.get("operator_waiver_input_sha256"),
            "lock_path": index.get("operator_waiver_lock_path"),
            "lock_sha256": index.get("operator_waiver_lock_sha256"),
        }
        if waiver_block != expected_waiver_block:
            issues.append("operator waiver block/path/hash mismatch")
        if formal_human:
            if acceptance.get("status") != "accepted" or acceptance.get("blockers") != []:
                issues.append("human-formal package acceptance state mismatch")
            if index.get("operator_waiver_input_path") is not None:
                issues.append("human-formal package must not also claim an operator waiver")
        elif formal_policy:
            if (
                acceptance.get("status") != "accepted_machine_only_operator_waiver"
                or acceptance.get("blockers") != []
            ):
                issues.append("operator-waiver package acceptance state mismatch")
            if formal_human_count != 0 or any(
                value is not None
                for value in (
                    index.get("human_signoff_input_path"),
                    index.get("human_signoff_input_sha256"),
                    index.get("human_signoff_lock_path"),
                    index.get("human_signoff_lock_sha256"),
                )
            ):
                issues.append("operator waiver must preserve human_signed=0 and no human lock")
        else:
            if acceptance.get("status") != "machine_validated_human_signoff_pending":
                issues.append("pending package acceptance state mismatch")
            if any(
                value is not None
                for value in (
                    index.get("human_signoff_lock_path"),
                    index.get("human_signoff_lock_sha256"),
                    index.get("operator_waiver_input_path"),
                    index.get("operator_waiver_input_sha256"),
                    index.get("operator_waiver_lock_path"),
                    index.get("operator_waiver_lock_sha256"),
                )
            ):
                issues.append("pending package must not claim a human or operator waiver lock")
        if current_source_check:
            pinned_current = {
                "source_bundle_path": EXPECTED_SOURCE_BUNDLE_SHA256,
                "step19_manifest_path": EXPECTED_STEP19_MANIFEST_SHA256,
                "packet_index_path": EXPECTED_PACKET_INDEX_SHA256,
            }
            for field in ("source_bundle_path", "step19_manifest_path", "packet_index_path"):
                path = _repo_path(str(input_lock.get(field)))
                expected = input_lock.get(field.replace("_path", "_sha256"))
                if not path.is_file() or path.is_symlink() or file_sha256(path) != expected:
                    issues.append(f"current frozen input drift: {field}")
                if path.is_file() and file_sha256(path) != pinned_current[field]:
                    issues.append(f"current frozen input differs from hard-pinned acceptance hash: {field}")
            packet_root = _repo_path(str(input_lock["packet_index_path"])).parent
            current_agent_input_hash = agent_input_tree_sha256(packet_root)
            if current_agent_input_hash != input_lock.get("agent_input_tree_sha256_before"):
                issues.append("current agent_input.json tree drift")
            if acceptance.get("agent_input_tree_sha256_before") != current_agent_input_hash or acceptance.get("agent_input_tree_sha256_after") != current_agent_input_hash:
                issues.append("acceptance agent_input tree hash mismatch")
            packet_index_payload = _require_mapping(_load_json(_repo_path(str(input_lock["packet_index_path"]))), "packet index")
            if (
                input_lock.get("packet_index_agent_input_tree_sha256")
                != EXPECTED_PACKET_INDEX_AGENT_INPUT_TREE_SHA256
                or acceptance.get("packet_index_agent_input_tree_sha256")
                != EXPECTED_PACKET_INDEX_AGENT_INPUT_TREE_SHA256
                or packet_index_payload.get("agent_input_tree_sha256")
                != EXPECTED_PACKET_INDEX_AGENT_INPUT_TREE_SHA256
                or packet_index_payload.get("index_core_sha256")
                != EXPECTED_PACKET_INDEX_CORE_SHA256
            ):
                issues.append("canonical packet-index agent_input tree hash linkage mismatch")
    except (WebArenaNativeClaimError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        issues.append(str(exc))
    return {
        "schema_version": "webarena_verified_native_claim_validation_report/v1",
        "status": "ok" if not issues else "invalid",
        "issue_count": len(issues),
        "issues": issues,
    }
