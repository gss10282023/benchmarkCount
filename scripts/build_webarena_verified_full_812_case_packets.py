#!/usr/bin/env python3
"""Build the canonical source-rich WebArena-Verified v1.2.3 full-812 packets.

``agent_input.json`` remains the only model-visible file.  The canonical
``case_packet.md`` and its ``raw_case/`` sources are drafter/reviewer inputs and
intentionally contain the private official evaluator semantics needed to draft
an auditable checklist.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = "webarena_verified_case_packet/v1"
INDEX_SCHEMA_VERSION = "webarena_verified_case_packet_index/v2"
RAW_CASE_MANIFEST_SCHEMA_VERSION = "webarena_verified_raw_case_manifest/v2"
TASK_CONTRACT_INDEX_SCHEMA_VERSION = "webarena_verified_task_contract_index/v1"
BENCHMARK_VERSION = "v1.2.3"
OFFICIAL_REPOSITORY = "https://github.com/ServiceNow/webarena-verified.git"
OFFICIAL_COMMIT = "6473f72db5dcefc97b5725b59e734504edc28a21"
OFFICIAL_EVALUATOR_IMAGE = (
    "ghcr.io/servicenow/webarena-verified@"
    "sha256:d2c3f81b615648a806e0b9c9fd392085a45ca719ea773a51976b59d23f7bd1b9"
)
SOURCE_SHA256 = "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
RAW_TAG_DATASET_SHA256 = (
    "d65275660814663375028e9017e1f929e3c38321041b125795e2713b52243d30"
)
OFFICIAL_EVALUATOR_CHECKSUM = (
    "35c3385b1db4b3378657589f95f50defd4234bd36e5b93d44733fd561b01db4e"
)
OFFICIAL_LICENSE_SHA256 = (
    "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4"
)
OFFICIAL_AGENT_INPUTS_SHA256 = (
    "d125ad7cf9627d9b9151153eaba20ecd85451899a2e4b70ecdd46510d0775a8e"
)
AGENT_INPUT_TREE_SHA256 = (
    "98f4f404cae6e794bd2fa1d0c152d43b7fa5d6ee5bffea143a0c9c39ddd4c975"
)
AGENT_INPUT_TOTAL_BYTES = 235617
TASK_CONTRACT_INDEX_SHA256 = (
    "32b2eb76d2296286fae619f843e985feaf1b3eaf622d90d77133ffb580ab0d49"
)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKET_ROOT = PROJECT_ROOT / "experiments/case_packets/webarena_verified"
DEFAULT_OFFICIAL_SOURCE_ROOT = (
    PROJECT_ROOT
    / "experiments/official_splits/webarena_verified_v1_2_3_source"
)
DEFAULT_SOURCE_BUNDLE_PATH = (
    PROJECT_ROOT
    / "experiments/evidence_contracts/source_bundles/"
    "webarena_verified_full_812_source_bundle.json"
)
STEP19_MANIFEST_PATH = (
    "experiments/step19/webarena_verified_full_812_manifest.json"
)

# These are the exact v1.2.3 sources needed to recover task-level aggregation,
# response matching, normalization and (where applicable) HAR matching.  The
# complete official package is frozen once under DEFAULT_OFFICIAL_SOURCE_ROOT;
# the relevant slice is copied into each case so every packet is standalone.
COMMON_OFFICIAL_PACKET_FILES = (
    "src/webarena_verified/api/internal/evaluator.py",
    "src/webarena_verified/core/evaluation/evaluators/base.py",
    "src/webarena_verified/core/evaluation/evaluators/agent_response_evaluator.py",
    "src/webarena_verified/core/evaluation/value_comparator.py",
    "src/webarena_verified/core/evaluation/value_normalizer.py",
    "src/webarena_verified/types/agent_response.py",
    "src/webarena_verified/types/eval.py",
    "src/webarena_verified/types/task.py",
)
NETWORK_EVENT_PACKET_FILES = (
    "src/webarena_verified/core/evaluation/evaluators/network_event_evaluator.py",
    "src/webarena_verified/types/tracing.py",
    "src/webarena_verified/core/utils/jsonpath_utils.py",
)
ALLOWED_TASK_TYPES = {"RETRIEVE", "MUTATE", "NAVIGATE"}
ALLOWED_EVALUATORS = {"AgentResponseEvaluator", "NetworkEventEvaluator"}
AGENT_INPUT_FIELDS = {"sites", "task_id", "intent_template_id", "start_urls", "intent"}
FORBIDDEN_MODEL_VISIBLE_PATTERNS = (
    re.compile(r'"expected"\s*:', re.IGNORECASE),
    re.compile(r'"retrieved_data"\s*:', re.IGNORECASE),
    re.compile(r'"error_details"\s*:', re.IGNORECASE),
    re.compile(r'"reference_answer"\s*:', re.IGNORECASE),
    re.compile(r'"gold(?:en)?(?:_answer|_value|_output)?"\s*:', re.IGNORECASE),
    re.compile(r"sk-or-v1-[A-Za-z0-9_-]+"),
    re.compile(r'"(?:password|cookie|session|authorization)"\s*:', re.IGNORECASE),
)

RUNTIME_LIMITS = {
    "max_steps": 30,
    "model_request_timeout_seconds": 120,
    "transport_retry_count_per_parse_attempt": 2,
    "action_parse_retry_count_per_browser_step": 2,
    "maximum_model_http_attempts_per_browser_step": 9,
    "official_evaluator_timeout_seconds": 600,
    "case_wall_clock_timeout_enforced": False,
    "observation_type": "accessibility_tree",
    "action_set": "id_accessibility_tree",
    "viewport": {"width": 1280, "height": 720},
    "concurrency_per_server": 1,
    "reset_before_each_case_required": True,
    "reset_controller_implementation_status": "pending",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def evaluator_names(task: Mapping[str, Any]) -> list[str]:
    names: list[str] = []
    for item in task.get("eval") or []:
        if not isinstance(item, Mapping):
            raise ValueError(f"task {task.get('task_id')} has a non-object evaluator")
        name = str(item.get("evaluator") or "")
        if name not in ALLOWED_EVALUATORS:
            raise ValueError(
                f"task {task.get('task_id')} has unsupported evaluator {name!r}"
            )
        if name not in names:
            names.append(name)
    if "AgentResponseEvaluator" not in names:
        raise ValueError(f"task {task.get('task_id')} lacks AgentResponseEvaluator")
    return names


def task_type(task: Mapping[str, Any]) -> str:
    values: set[str] = set()
    for item in task.get("eval") or []:
        if (
            not isinstance(item, Mapping)
            or item.get("evaluator") != "AgentResponseEvaluator"
        ):
            continue
        private_payload = item.get("expected")
        if not isinstance(private_payload, Mapping):
            raise ValueError(
                f"task {task.get('task_id')} has no typed agent-response specification"
            )
        values.add(str(private_payload.get("task_type") or "").upper())
    if len(values) != 1 or next(iter(values)) not in ALLOWED_TASK_TYPES:
        raise ValueError(
            f"task {task.get('task_id')} has invalid task type set {sorted(values)}"
        )
    return next(iter(values))


def required_artifacts() -> list[str]:
    # The official v1.2.3 CLI validates both run outputs before dispatching
    # evaluators, including tasks that only use AgentResponseEvaluator.
    return ["agent_response.json", "network.har"]


def validate_agent_input(
    task: Mapping[str, Any], value: Mapping[str, Any]
) -> dict[str, Any]:
    value = dict(value)
    if set(value) != AGENT_INPUT_FIELDS:
        raise ValueError(
            f"task {task.get('task_id')} official agent input violates the field allowlist"
        )
    if int(value["task_id"]) != int(task["task_id"]):
        raise ValueError(
            f"task {task.get('task_id')} official agent input has mismatched task ID"
        )
    if int(value["intent_template_id"]) != int(task["intent_template_id"]):
        raise ValueError(
            f"task {task.get('task_id')} official agent input has mismatched template ID"
        )
    if list(value["sites"]) != list(task.get("sites") or []):
        raise ValueError(
            f"task {task.get('task_id')} official agent input has mismatched sites"
        )
    if str(value["intent"]) != str(task.get("intent") or ""):
        raise ValueError(
            f"task {task.get('task_id')} official agent input has mismatched instruction"
        )
    if len(list(value["start_urls"])) != len(list(task.get("start_urls") or [])):
        raise ValueError(
            f"task {task.get('task_id')} official agent input has mismatched start URL count"
        )
    if any(
        "__" in str(url) or not str(url).startswith("http://127.0.0.1:")
        for url in value["start_urls"]
    ):
        raise ValueError(
            f"task {task.get('task_id')} official agent input has unresolved or nonlocal start URL"
        )
    return value


def controller_packet(
    task: Mapping[str, Any],
    model_input: Mapping[str, Any],
    *,
    model_input_file_sha256: str,
) -> dict[str, Any]:
    names = evaluator_names(task)
    evaluator_config_names = [str(item["evaluator"]) for item in task.get("eval") or []]
    evaluator_refs = []
    for index, item in enumerate(task.get("eval") or []):
        evaluator_refs.append(
            {
                "index": index,
                "name": str(item["evaluator"]),
                "private_dataset_ref": f"official-dataset#task_id={int(task['task_id'])}/eval/{index}",
                "private_config_sha256": sha256_bytes(canonical_bytes(item)),
            }
        )
    source_task_sha256 = sha256_bytes(canonical_bytes(task))
    public_task = {
        "task_id": int(task["task_id"]),
        "intent_template_id": int(task["intent_template_id"]),
        "instruction": str(task.get("intent") or ""),
        "task_type": task_type(task),
        "revision": int(task["revision"]),
        "sites": list(task.get("sites") or []),
        "start_url_templates": [str(url) for url in task.get("start_urls") or []],
        "resolved_start_urls": list(model_input["start_urls"]),
    }
    public_task_sha256 = sha256_bytes(canonical_bytes(public_task))
    return {
        "schema_version": SCHEMA_VERSION,
        "visibility": "controller_and_human_review_only",
        "model_visible_input": {
            "path": "agent_input.json",
            "sha256": model_input_file_sha256,
            "field_allowlist": sorted(AGENT_INPUT_FIELDS),
        },
        "benchmark": {
            "name": "WebArena-Verified",
            "version": BENCHMARK_VERSION,
            "split": "full",
            "official_repository": OFFICIAL_REPOSITORY,
            "official_commit": OFFICIAL_COMMIT,
        },
        "task": public_task,
        "runtime_limits": dict(RUNTIME_LIMITS),
        "evaluator_reference": {
            "implementation": "ServiceNow/webarena-verified",
            "version": BENCHMARK_VERSION,
            "commit": OFFICIAL_COMMIT,
            "docker_image": OFFICIAL_EVALUATOR_IMAGE,
            "cli": "webarena-verified eval-tasks",
            "python_api": "webarena_verified.api.WebArenaVerified.evaluate_task",
            "evaluator_names": names,
            "evaluator_config_names": evaluator_config_names,
            "evaluators": evaluator_refs,
            "required_run_artifacts": required_artifacts(),
            "score_field": "TaskEvalResult.score",
        },
        "provenance": {
            "source_path": "experiments/official_splits/webarena_verified_official_812.json",
            "source_sha256": SOURCE_SHA256,
            "tag_raw_dataset_sha256": RAW_TAG_DATASET_SHA256,
            "source_task_sha256": source_task_sha256,
            "public_task_sha256": public_task_sha256,
        },
        "leakage_control": {
            "policy": "allowlist_only_v1",
            "model_receives_only_agent_input_json": True,
            "evaluator_payload_embedded": False,
            "answer_payload_embedded": False,
        },
    }


def _repo_relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        # Isolated test builds can live outside the repository. Canonical builds
        # always take the repository-relative branch.
        return resolved.as_posix()


def _markdown_fence(path: Path) -> str:
    return {
        ".json": "json",
        ".py": "python",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
    }.get(path.suffix.lower(), "text")


def _raw_case_tree_digest(raw_case_dir: Path) -> tuple[str, int, int]:
    files = sorted(path for path in raw_case_dir.rglob("*") if path.is_file())
    lines: list[str] = []
    total_bytes = 0
    for path in files:
        rel = path.relative_to(raw_case_dir).as_posix()
        size = path.stat().st_size
        total_bytes += size
        lines.append(f"{rel}\t{sha256_file(path)}\t{size}\n")
    return sha256_bytes("".join(lines).encode("utf-8")), len(files), total_bytes


def _agent_input_tree_digest(output_root: Path) -> tuple[str, int]:
    lines: list[str] = []
    total_bytes = 0
    for task_id in range(812):
        path = output_root / str(task_id) / "agent_input.json"
        size = path.stat().st_size
        total_bytes += size
        lines.append(f"{task_id}\t{sha256_file(path)}\t{size}\n")
    return sha256_bytes("".join(lines).encode("utf-8")), total_bytes


def _official_evaluator_checksum(source_root: Path) -> str:
    package_root = source_root / "src/webarena_verified"
    files = sorted(package_root.rglob("*.py"))
    if len(files) != 74:
        raise ValueError(
            f"official source snapshot must contain 74 evaluator Python files, got {len(files)}"
        )
    digest = hashlib.sha256()
    for path in files:
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"official source snapshot contains an unsafe file: {path}")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def load_and_validate_official_snapshot(
    source_root: Path,
) -> dict[int, Mapping[str, Any]]:
    dataset_path = source_root / "assets/dataset/webarena-verified.json"
    license_path = source_root / "LICENSE"
    if sha256_file(dataset_path) != RAW_TAG_DATASET_SHA256:
        raise ValueError(f"official tag dataset hash mismatch for {dataset_path}")
    if sha256_file(license_path) != OFFICIAL_LICENSE_SHA256:
        raise ValueError(f"official license hash mismatch for {license_path}")
    checksum = _official_evaluator_checksum(source_root)
    if checksum != OFFICIAL_EVALUATOR_CHECKSUM:
        raise ValueError(
            "official evaluator snapshot checksum mismatch: "
            f"expected {OFFICIAL_EVALUATOR_CHECKSUM}, got {checksum}"
        )
    for rel in (*COMMON_OFFICIAL_PACKET_FILES, *NETWORK_EVENT_PACKET_FILES):
        path = source_root / rel
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"required official source file is missing or unsafe: {path}")
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or len(payload) != 812:
        raise ValueError("official v1.2.3 tag dataset must contain exactly 812 tasks")
    by_id = {
        int(item["task_id"]): item
        for item in payload
        if isinstance(item, Mapping)
    }
    if sorted(by_id) != list(range(812)):
        raise ValueError("official v1.2.3 tag dataset IDs must be 0..811")
    return by_id


def _validate_tag_task_identity(
    normalized_task: Mapping[str, Any], tag_task: Mapping[str, Any]
) -> None:
    task_id = int(normalized_task["task_id"])
    for key in (
        "task_id",
        "intent_template_id",
        "intent",
        "intent_template",
        "instantiation_dict",
        "revision",
        "sites",
        "start_urls",
    ):
        if normalized_task.get(key) != tag_task.get(key):
            raise ValueError(f"task {task_id} normalized/tag identity mismatch for {key}")
    normalized_names = [str(item["evaluator"]) for item in normalized_task["eval"]]
    tag_names = [str(item["evaluator"]) for item in tag_task["eval"]]
    if normalized_names != tag_names:
        raise ValueError(f"task {task_id} normalized/tag evaluator order mismatch")


def build_raw_case(
    *,
    case_dir: Path,
    task: Mapping[str, Any],
    tag_task: Mapping[str, Any],
    packet: Mapping[str, Any],
    official_source_root: Path,
) -> dict[str, Any]:
    case_id = int(task["task_id"])
    raw_case_dir = case_dir / "raw_case"
    raw_case_dir.mkdir()
    _validate_tag_task_identity(task, tag_task)

    normalized_task_rel = "derived/task.json"
    tag_task_rel = "derived/tag_task.json"
    write_json(raw_case_dir / normalized_task_rel, task)
    write_json(raw_case_dir / tag_task_rel, tag_task)

    names = evaluator_names(task)
    selected_sources = list(COMMON_OFFICIAL_PACKET_FILES)
    if "NetworkEventEvaluator" in names:
        selected_sources.extend(NETWORK_EVENT_PACKET_FILES)

    official_files = ["official/LICENSE"]
    license_destination = raw_case_dir / "official/LICENSE"
    license_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(official_source_root / "LICENSE", license_destination)
    packet_files = [normalized_task_rel, tag_task_rel]
    for rel in selected_sources:
        destination_rel = f"official/{rel}"
        destination = raw_case_dir / destination_rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(official_source_root / rel, destination)
        official_files.append(destination_rel)
        packet_files.append(destination_rel)

    files = sorted(path for path in raw_case_dir.rglob("*") if path.is_file())
    copied_files = [path.relative_to(raw_case_dir).as_posix() for path in files]
    sha256_per_file = {
        path.relative_to(raw_case_dir).as_posix(): sha256_file(path) for path in files
    }
    raw_dataset_ref = (
        "experiments/official_splits/webarena_verified_v1_2_3_source/"
        f"assets/dataset/webarena-verified.json#task_id={case_id}"
    )
    normalized_dataset_ref = (
        "experiments/official_splits/webarena_verified_official_812.json"
        f"#task_id={case_id}"
    )
    file_sources = {
        normalized_task_rel: normalized_dataset_ref,
        tag_task_rel: raw_dataset_ref,
        "official/LICENSE": f"{OFFICIAL_REPOSITORY}@{OFFICIAL_COMMIT}/LICENSE",
    }
    for rel in selected_sources:
        file_sources[f"official/{rel}"] = (
            f"{OFFICIAL_REPOSITORY}/blob/{OFFICIAL_COMMIT}/{rel}"
        )

    return {
        "schema_version": RAW_CASE_MANIFEST_SCHEMA_VERSION,
        "domain": "webarena_verified",
        "case_unit_id": str(case_id),
        "task_id": str(case_id),
        "benchmark_version": BENCHMARK_VERSION,
        "official_commit": OFFICIAL_COMMIT,
        "source_refs": [normalized_dataset_ref, raw_dataset_ref],
        "copied_files": copied_files,
        "official_files": sorted(official_files),
        "derived_files": [normalized_task_rel, tag_task_rel],
        "packet_files": packet_files,
        "sha256_per_file": sha256_per_file,
        "file_sources": dict(sorted(file_sources.items())),
        "model_visible_files": ["agent_input.json"],
        "drafter_reviewer_only_files": [
            "case_packet.md",
            "raw_case_manifest.json",
            "raw_case/**",
        ],
        "controller_runtime_files": ["case_packet.json"],
        "top_level_file_sha256": {
            "agent_input.json": sha256_file(case_dir / "agent_input.json"),
            "case_packet.json": sha256_file(case_dir / "case_packet.json"),
        },
        "normalized_source_path": (
            "experiments/official_splits/webarena_verified_official_812.json"
        ),
        # Backward-compatible aliases retained for existing readers.  The two
        # explicitly named fields below are authoritative and disambiguate the
        # normalized export from the raw tag dataset.
        "source_sha256": SOURCE_SHA256,
        "source_task_sha256": packet["provenance"]["source_task_sha256"],
        "normalized_source_sha256": SOURCE_SHA256,
        "normalized_source_task_canonical_sha256": packet["provenance"][
            "source_task_sha256"
        ],
        "official_tag_dataset_path": (
            "experiments/official_splits/webarena_verified_v1_2_3_source/"
            "assets/dataset/webarena-verified.json"
        ),
        "official_tag_dataset_sha256": RAW_TAG_DATASET_SHA256,
        "official_tag_task_canonical_sha256": sha256_bytes(canonical_bytes(tag_task)),
        "official_evaluator_checksum": OFFICIAL_EVALUATOR_CHECKSUM,
        "evaluator_names_in_order": [
            str(item["evaluator"]) for item in task.get("eval") or []
        ],
        "task_score_composition": "all_evaluator_scores_must_equal_1.0",
        "required_run_artifacts": required_artifacts(),
    }


def render_source_rich_packet(
    *,
    packet: Mapping[str, Any],
    raw_case_dir: Path,
    raw_case_manifest: Mapping[str, Any],
) -> str:
    task = packet["task"]
    evaluator = packet["evaluator_reference"]
    runtime = packet["runtime_limits"]
    sites = ", ".join(f"`{site}`" for site in task["sites"])
    names = ", ".join(f"`{name}`" for name in evaluator["evaluator_names"])
    artifacts = ", ".join(
        f"`{name}`" for name in evaluator["required_run_artifacts"]
    )
    lines = [
        "# Case Packet",
        "",
        "## Case Metadata",
        "",
        "- domain: `webarena_verified`",
        f"- case_unit_id: `{task['task_id']}`",
        f"- task_id: `{task['task_id']}`",
        "",
        "## Benchmark Task Summary",
        "",
        f"- benchmark: `WebArena-Verified {BENCHMARK_VERSION} full`",
        f"- task type: `{task['task_type']}`",
        f"- task revision: `{task['revision']}`",
        f"- sites: {sites}",
        f"- official instruction: {task['instruction'].rstrip()}",
        f"- official evaluator commit: `{OFFICIAL_COMMIT}`",
        f"- evaluator sequence: {names}",
        "- task score composition: `all evaluator scores must equal 1.0`",
        "- official score field: `TaskEvalResult.score`",
        f"- required run artifacts: {artifacts}",
        f"- maximum browser steps: `{runtime['max_steps']}`",
        f"- observation/action set: `{runtime['observation_type']}` / `{runtime['action_set']}`",
        f"- reset before each case: `{str(runtime['reset_before_each_case_required']).lower()}`",
        "",
        "## Visibility Boundary",
        "",
        "This canonical source-rich packet is only for checklist drafting and human review.",
        "The tested agent receives only `agent_input.json`; do not place this packet,",
        "`raw_case/`, evaluator expectations, or gold values in the agent prompt.",
        "",
        "## Source Inventory",
        "",
    ]
    packet_files = [str(item) for item in raw_case_manifest["packet_files"]]
    for rel in packet_files:
        lines.append(f"- `{rel}`")
    lines.extend(["", "## Packet Source Files", ""])
    file_sources = raw_case_manifest["file_sources"]
    for rel in packet_files:
        path = raw_case_dir / rel
        lines.extend(
            [
                f"### `{rel}`",
                "",
                f"Source ref: `{file_sources[rel]}`",
                "",
                f"```{_markdown_fence(path)}",
                path.read_text(encoding="utf-8").rstrip("\n"),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Raw Source Provenance",
            "",
            "```json",
            json.dumps(raw_case_manifest, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def assert_model_visible_safe(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_MODEL_VISIBLE_PATTERNS:
        if pattern.search(text):
            raise ValueError(
                f"forbidden model-visible content pattern in {path}: {pattern.pattern}"
            )


def write_source_bundle(
    *,
    output_root: Path,
    source_bundle_path: Path,
    manifest_path: str = STEP19_MANIFEST_PATH,
) -> dict[str, Any]:
    def bundle_reference(path: Path) -> str:
        resolved = path.resolve()
        try:
            return resolved.relative_to(PROJECT_ROOT).as_posix()
        except ValueError:
            try:
                return resolved.relative_to(source_bundle_path.parent.resolve()).as_posix()
            except ValueError as exc:
                raise ValueError(
                    f"source-bundle input must be under the repository or bundle directory: {path}"
                ) from exc

    sources: list[dict[str, Any]] = []
    for task_id in range(812):
        case_dir = output_root / str(task_id)
        packet_path = case_dir / "case_packet.md"
        manifest_file = case_dir / "raw_case_manifest.json"
        sources.append(
            {
                "contract_id": f"ec_webarena_verified_{task_id}_contract_v1_0_0",
                "domain": "webarena_verified",
                "case_unit_id": str(task_id),
                "task_id": str(task_id),
                "source_ref": (
                    "experiments/official_splits/"
                    "webarena_verified_official_812.json"
                    f"#task_id={task_id}"
                ),
                "draft_input": {
                    "case_packet_path": bundle_reference(packet_path),
                    "case_packet_sha256": sha256_file(packet_path),
                    "raw_case_manifest_path": bundle_reference(manifest_file),
                    "raw_case_manifest_sha256": sha256_file(manifest_file),
                },
            }
        )
    bundle = {
        "schema_version": "contract_source_bundle.v2",
        "manifest_path": manifest_path,
        "manifest_sha256": sha256_file(PROJECT_ROOT / manifest_path),
        "source_count": len(sources),
        "sources": sources,
    }
    write_json(source_bundle_path, bundle)
    bundle_sha256 = sha256_file(source_bundle_path)
    source_bundle_path.with_suffix(source_bundle_path.suffix + ".sha256").write_text(
        f"{bundle_sha256}  {source_bundle_path.name}\n", encoding="utf-8"
    )
    return bundle


def build_packets(
    source_path: Path,
    agent_inputs_path: Path,
    output_root: Path,
    *,
    official_source_root: Path = DEFAULT_OFFICIAL_SOURCE_ROOT,
    source_bundle_path: Path | None = None,
) -> dict[str, Any]:
    if sha256_file(source_path) != SOURCE_SHA256:
        raise ValueError(f"source hash mismatch for {source_path}")
    if sha256_file(agent_inputs_path) != OFFICIAL_AGENT_INPUTS_SHA256:
        raise ValueError(f"official agent-input export hash mismatch for {agent_inputs_path}")
    tag_tasks_by_id = load_and_validate_official_snapshot(official_source_root)
    source = json.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(source, list) or len(source) != 812:
        raise ValueError("WebArena-Verified source must contain exactly 812 tasks")
    task_ids = [int(task["task_id"]) for task in source if isinstance(task, Mapping)]
    if (
        len(task_ids) != 812
        or sorted(task_ids) != list(range(812))
        or len(set(task_ids)) != 812
    ):
        raise ValueError("task IDs must be the unique complete range 0..811")
    agent_inputs_source = json.loads(agent_inputs_path.read_text(encoding="utf-8"))
    if not isinstance(agent_inputs_source, list) or len(agent_inputs_source) != 812:
        raise ValueError(
            "official agent-input-get export must contain exactly 812 tasks"
        )
    agent_inputs_by_id = {
        int(value["task_id"]): value
        for value in agent_inputs_source
        if isinstance(value, Mapping)
    }
    if sorted(agent_inputs_by_id) != list(range(812)):
        raise ValueError(
            "official agent-input-get export IDs must be the unique complete range 0..811"
        )

    # If rebuilding an existing canonical tree, freeze every model-visible byte
    # before replacing generated artifacts and compare it immediately afterward.
    previous_agent_inputs: dict[int, bytes] = {}
    if output_root.exists():
        previous_agent_inputs = {
            task_id: (output_root / str(task_id) / "agent_input.json").read_bytes()
            for task_id in range(812)
            if (output_root / str(task_id) / "agent_input.json").is_file()
        }
        if previous_agent_inputs and len(previous_agent_inputs) != 812:
            raise ValueError(
                "refusing to replace a partial pre-existing agent-input tree"
            )
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    if source_bundle_path is None and output_root.resolve() == DEFAULT_PACKET_ROOT.resolve():
        source_bundle_path = DEFAULT_SOURCE_BUNDLE_PATH

    entries: list[dict[str, Any]] = []
    task_contract_entries: list[dict[str, Any]] = []
    type_counts: Counter[str] = Counter()
    evaluator_task_counts: Counter[str] = Counter()
    evaluator_config_counts: Counter[str] = Counter()
    for task in sorted(source, key=lambda item: int(item["task_id"])):
        case_id = int(task["task_id"])
        case_dir = output_root / str(case_id)
        case_dir.mkdir()
        visible = validate_agent_input(task, agent_inputs_by_id[case_id])
        write_json(case_dir / "agent_input.json", visible)
        if previous_agent_inputs and (
            (case_dir / "agent_input.json").read_bytes()
            != previous_agent_inputs[case_id]
        ):
            raise ValueError(f"task {case_id} agent_input.json changed byte-for-byte")
        packet = controller_packet(
            task,
            visible,
            model_input_file_sha256=sha256_file(case_dir / "agent_input.json"),
        )
        write_json(case_dir / "case_packet.json", packet)
        raw_manifest = build_raw_case(
            case_dir=case_dir,
            task=task,
            tag_task=tag_tasks_by_id[case_id],
            packet=packet,
            official_source_root=official_source_root,
        )
        write_json(case_dir / "raw_case_manifest.json", raw_manifest)
        (case_dir / "case_packet.md").write_text(
            render_source_rich_packet(
                packet=packet,
                raw_case_dir=case_dir / "raw_case",
                raw_case_manifest=raw_manifest,
            ),
            encoding="utf-8",
        )
        assert_model_visible_safe(case_dir / "agent_input.json")
        # The controller JSON remains intentionally evaluator-payload-free so
        # the already deployed task contract stays byte-identical.
        assert_model_visible_safe(case_dir / "case_packet.json")

        packet_type = str(packet["task"]["task_type"])
        names = list(packet["evaluator_reference"]["evaluator_names"])
        type_counts[packet_type] += 1
        evaluator_task_counts.update(names)
        evaluator_config_counts.update(
            str(item["evaluator"]) for item in task.get("eval") or []
        )
        raw_tree_sha256, raw_file_count, raw_total_bytes = _raw_case_tree_digest(
            case_dir / "raw_case"
        )
        entries.append(
            {
                "task_id": case_id,
                "task_type": packet_type,
                "revision": int(packet["task"]["revision"]),
                "sites": list(packet["task"]["sites"]),
                "evaluator_names": names,
                "agent_input_sha256": sha256_file(case_dir / "agent_input.json"),
                "case_packet_json_sha256": sha256_file(case_dir / "case_packet.json"),
                "case_packet_markdown_sha256": sha256_file(case_dir / "case_packet.md"),
                "raw_case_manifest_sha256": sha256_file(
                    case_dir / "raw_case_manifest.json"
                ),
                "raw_case_tree_sha256": raw_tree_sha256,
                "raw_case_file_count": raw_file_count,
                "raw_case_total_bytes": raw_total_bytes,
            }
        )
        task_contract_entries.append(
            {
                "task_id": case_id,
                "task_revision": int(packet["task"]["revision"]),
                "task_type": packet_type,
                "intent_template_id": int(packet["task"]["intent_template_id"]),
                "sites": list(packet["task"]["sites"]),
                "evaluator_names_in_order": [
                    str(item["name"])
                    for item in packet["evaluator_reference"]["evaluators"]
                ],
                "required_run_artifacts": required_artifacts(),
                "agent_input_sha256": sha256_file(case_dir / "agent_input.json"),
                "case_packet_sha256": sha256_file(case_dir / "case_packet.json"),
            }
        )

    if list(output_root.rglob("draft_case_packet*")):
        raise ValueError("a second draft_case_packet artifact is forbidden")
    agent_input_tree_sha256, agent_input_total_bytes = _agent_input_tree_digest(
        output_root
    )
    if (
        agent_input_tree_sha256 != AGENT_INPUT_TREE_SHA256
        or agent_input_total_bytes != AGENT_INPUT_TOTAL_BYTES
    ):
        raise ValueError(
            "agent-input byte freeze mismatch: "
            f"sha256={agent_input_tree_sha256}, bytes={agent_input_total_bytes}"
        )

    task_contract_index = {
        "schema_version": TASK_CONTRACT_INDEX_SCHEMA_VERSION,
        "visibility": "controller_only",
        "benchmark": "WebArena-Verified",
        "version": BENCHMARK_VERSION,
        "split": "full",
        "official_commit": OFFICIAL_COMMIT,
        "source_sha256": SOURCE_SHA256,
        "raw_tag_dataset_sha256": RAW_TAG_DATASET_SHA256,
        "task_count": len(task_contract_entries),
        "entries": task_contract_entries,
    }
    task_contract_index_path = output_root / "task_contract_index.json"
    write_json(task_contract_index_path, task_contract_index)
    task_contract_index_sha256 = sha256_file(task_contract_index_path)
    if task_contract_index_sha256 != TASK_CONTRACT_INDEX_SHA256:
        raise ValueError(
            "task contract changed while normalizing drafter packets: "
            f"expected {TASK_CONTRACT_INDEX_SHA256}, got {task_contract_index_sha256}"
        )
    (output_root / "task_contract_index.json.sha256").write_text(
        f"{task_contract_index_sha256}  task_contract_index.json\n",
        encoding="utf-8",
    )

    source_bundle_sha256: str | None = None
    source_bundle_source_count = 0
    if source_bundle_path is not None:
        bundle = write_source_bundle(
            output_root=output_root,
            source_bundle_path=source_bundle_path,
        )
        source_bundle_sha256 = sha256_file(source_bundle_path)
        source_bundle_source_count = int(bundle["source_count"])

    index_core = {
        "schema_version": INDEX_SCHEMA_VERSION,
        "status": "frozen",
        "benchmark": "WebArena-Verified",
        "version": BENCHMARK_VERSION,
        "split": "full",
        "source_path": str(source_path),
        "source_sha256": SOURCE_SHA256,
        "official_agent_inputs_path": str(agent_inputs_path),
        "official_agent_inputs_sha256": sha256_file(agent_inputs_path),
        "agent_input_tree_sha256": agent_input_tree_sha256,
        "agent_input_total_bytes": agent_input_total_bytes,
        "raw_tag_dataset_sha256": RAW_TAG_DATASET_SHA256,
        "official_commit": OFFICIAL_COMMIT,
        "official_source_snapshot_path": _repo_relative(official_source_root),
        "official_evaluator_checksum": OFFICIAL_EVALUATOR_CHECKSUM,
        "canonical_packet_filename": "case_packet.md",
        "packet_visibility": "drafter_and_reviewer_only",
        "model_visible_files_per_case": ["agent_input.json"],
        "draft_case_packet_file_count": 0,
        "packet_count": len(entries),
        "model_visible_file_count": len(entries),
        "task_type_counts": dict(sorted(type_counts.items())),
        "evaluator_task_counts": dict(sorted(evaluator_task_counts.items())),
        "evaluator_config_counts": dict(sorted(evaluator_config_counts.items())),
        "task_contract_index_path": "task_contract_index.json",
        "task_contract_index_sha256": task_contract_index_sha256,
        "entries": entries,
    }
    if source_bundle_path is not None:
        index_core.update(
            {
                "source_bundle_path": _repo_relative(source_bundle_path),
                "source_bundle_sha256": source_bundle_sha256,
                "source_bundle_source_count": source_bundle_source_count,
            }
        )
    index = dict(index_core)
    index["index_core_sha256"] = sha256_bytes(canonical_bytes(index_core))
    write_json(output_root / "index.json", index)
    index_file_sha256 = sha256_file(output_root / "index.json")
    (output_root / "index.json.sha256").write_text(
        f"{index_file_sha256}  index.json\n", encoding="utf-8"
    )
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("experiments/official_splits/webarena_verified_official_812.json"),
    )
    parser.add_argument(
        "--agent-inputs",
        type=Path,
        default=Path(
            "experiments/official_splits/webarena_verified_agent_inputs_full_812.json"
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("experiments/case_packets/webarena_verified"),
    )
    parser.add_argument(
        "--official-source-root",
        type=Path,
        default=Path(
            "experiments/official_splits/webarena_verified_v1_2_3_source"
        ),
    )
    parser.add_argument(
        "--source-bundle",
        type=Path,
        default=Path(
            "experiments/evidence_contracts/source_bundles/"
            "webarena_verified_full_812_source_bundle.json"
        ),
    )
    args = parser.parse_args()
    index = build_packets(
        args.source,
        args.agent_inputs,
        args.output_root,
        official_source_root=args.official_source_root,
        source_bundle_path=args.source_bundle,
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "packet_count": index["packet_count"],
                "task_type_counts": index["task_type_counts"],
                "evaluator_task_counts": index["evaluator_task_counts"],
                "evaluator_config_counts": index["evaluator_config_counts"],
                "agent_input_tree_sha256": index["agent_input_tree_sha256"],
                "source_bundle_sha256": index["source_bundle_sha256"],
                "index_core_sha256": index["index_core_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
