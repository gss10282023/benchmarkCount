#!/usr/bin/env python3
"""Build and validate the pinned SWE-bench Pro public case-packet corpus.

The builder intentionally materializes only compact task/evaluator metadata. It
does not download repositories, Docker images, or public agent trajectories.
The Hugging Face rows endpoint is accepted only while the repository head and
the canonical 731-row digest match the constants below; a moved ``main`` fails
closed instead of silently changing the packet corpus.
"""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import hashlib
import json
import shutil
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "experiments" / "case_packets" / "swe_bench_pro"

HF_DATASET_ID = "ScaleAI/SWE-bench_Pro"
HF_CONFIG = "default"
HF_SPLIT = "test"
HF_CURRENT_REVISION = "7ab5114912baf22bb098818e604c02fe7ad2c11f"
HF_CURRENT_DATA_COMMIT = "2dd05cab1572ce1d59fdc699b386692ff8e0bd29"
HF_CURRENT_PARQUET_PATH = "data/test-00000-of-00001.parquet"
HF_CURRENT_PARQUET_SHA256 = "c8cd7115496ad4e9a8b21d088cef576a65bf821bb542b24336f13f714cef13f8"
HF_CURRENT_PARQUET_SIZE = 7_816_820
HF_CURRENT_ROWS_CANONICAL_SHA256 = "6085a1fc78185e252a5919bcedfa18571d6a7906f14500cc6328c3af45982e91"
HF_HISTORICAL_REVISION = "9c13b199fe2d3195214e2f0c6bf3c7d6f81e3877"

OFFICIAL_REPOSITORY = "https://github.com/scaleapi/SWE-bench_Pro-os"
CURRENT_EVALUATOR_COMMIT = "ca10a60a5fcae51e6948ffe1485d4153d421e6c5"
HISTORICAL_REPOSITORY_COMMIT_BY_DATE = "21ced48139be967dd3729701bb3b8a9d07cde01f"

EXPECTED_CURRENT_TASK_COUNT = 731
EXPECTED_HISTORICAL_TRAJECTORY_COUNT = 730
HISTORICAL_REFERENCE_RUN = "claude-45sonnet-10132025"
HISTORICAL_MISSING_INSTANCE_ID = (
    "instance_element-hq__element-web-ec0f940ef0e8e3b61078f145f34dc40d1938e6c5-vnan"
)

S3_ROOT = "s3://scaleapi-results/swe-bench-pro/"
S3_HTTPS_ROOT = "https://scaleapi-results.s3.amazonaws.com/swe-bench-pro/"
DOCENT_URL = "https://docent.transluce.org/dashboard/032fb63d-4992-4bfc-911d-3b7dafcb931f"

CASE_FILES = (
    "agent_input.json",
    "case_packet.json",
    "case_packet.md",
    "raw_case_manifest.json",
)

RAW_CASE_FILES = (
    "official/huggingface/task_visible.json",
    "official/evaluator/test_contract.json",
    "official/evaluator/test.patch",
    "official/evaluator/solution_patch_metadata.json",
    "official/environment/runtime.json",
)

# The drafter-visible packet is a pre-run claim specification. Public reference
# runs remain documented only in the root source lock and the repository-level
# acquisition guide; no per-case model/run/trajectory pointer may enter the
# drafter input. Keep these markers explicit so generation and validate-only
# both fail closed if the boundary regresses.
FORBIDDEN_DRAFTER_PRIOR_RUN_MARKERS = (
    "official/provenance/contracts.json",
    "historical_public_artifacts",
    "historical_public_trajectory",
    "historical_public_trajectory_contract_id",
    "available_in_reference_run",
    "reference_run_prefix",
    "trajectory_s3_uri",
    "trajectory_https_url",
    "patch_s3_uri",
    "parsed_test_output_s3_uri",
    "downloaded_or_embedded",
    HISTORICAL_REFERENCE_RUN.lower(),
    S3_ROOT.lower(),
    S3_HTTPS_ROOT.lower(),
    "scaleapi-results",
    "/traj/",
    "/_patch.diff",
    "/_output.json",
)


class BuildError(RuntimeError):
    """Raised when a source or generated-artifact invariant is violated."""


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json_text(value))


def fetch_json(url: str, *, attempts: int = 3) -> Any:
    error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "swe-bench-pro-case-packet-builder/1"},
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.load(response)
        except Exception as exc:  # pragma: no cover - exercised only on network failure
            error = exc
            if attempt < attempts:
                time.sleep(attempt)
    raise BuildError(f"Failed to fetch {url}: {error}")


def assert_hf_head_is_pinned() -> None:
    metadata = fetch_json(f"https://huggingface.co/api/datasets/{HF_DATASET_ID}")
    observed = metadata.get("sha") if isinstance(metadata, Mapping) else None
    if observed != HF_CURRENT_REVISION:
        raise BuildError(
            "Hugging Face dataset head moved; refusing the floating rows endpoint: "
            f"expected {HF_CURRENT_REVISION}, observed {observed!r}. Supply a saved "
            "pinned-row JSONL with --source-jsonl instead."
        )


def fetch_row_chunk(offset: int, length: int) -> list[Mapping[str, Any]]:
    query = urllib.parse.urlencode(
        {
            "dataset": HF_DATASET_ID,
            "config": HF_CONFIG,
            "split": HF_SPLIT,
            "offset": offset,
            "length": length,
        }
    )
    payload = fetch_json(f"https://datasets-server.huggingface.co/rows?{query}")
    rows = payload.get("rows") if isinstance(payload, Mapping) else None
    if not isinstance(rows, list):
        raise BuildError(f"Rows response at offset {offset} has no rows list")
    return rows


def fetch_pinned_rows(max_workers: int) -> list[tuple[int, Mapping[str, Any]]]:
    assert_hf_head_is_pinned()
    offsets = list(range(0, EXPECTED_CURRENT_TASK_COUNT, 100))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        chunks = list(executor.map(lambda offset: fetch_row_chunk(offset, 100), offsets))
    assert_hf_head_is_pinned()

    items: list[tuple[int, Mapping[str, Any]]] = []
    for chunk in chunks:
        for item in chunk:
            if not isinstance(item, Mapping) or not isinstance(item.get("row"), Mapping):
                raise BuildError("Malformed item returned by the Hugging Face rows endpoint")
            row_idx = item.get("row_idx")
            if not isinstance(row_idx, int):
                raise BuildError("Hugging Face row item is missing integer row_idx")
            items.append((row_idx, item["row"]))
    items.sort(key=lambda item: item[0])
    return items


def load_source_jsonl(path: Path) -> list[tuple[int, Mapping[str, Any]]]:
    items: list[tuple[int, Mapping[str, Any]]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if isinstance(value, Mapping) and isinstance(value.get("row"), Mapping):
                row = value["row"]
                row_idx = value.get("row_idx", len(items))
            else:
                row = value
                row_idx = len(items)
            if not isinstance(row, Mapping) or not isinstance(row_idx, int):
                raise BuildError(f"Malformed row at {path}:{line_number}")
            items.append((row_idx, row))
    items.sort(key=lambda item: item[0])
    return items


def validate_source_rows(items: Sequence[tuple[int, Mapping[str, Any]]]) -> None:
    if len(items) != EXPECTED_CURRENT_TASK_COUNT:
        raise BuildError(
            f"Expected {EXPECTED_CURRENT_TASK_COUNT} source rows, found {len(items)}"
        )
    expected_positions = list(range(EXPECTED_CURRENT_TASK_COUNT))
    observed_positions = [position for position, _ in items]
    if observed_positions != expected_positions:
        raise BuildError("Source row_idx sequence is not the exact 0..730 sequence")

    instance_ids = [row.get("instance_id") for _, row in items]
    if not all(isinstance(instance_id, str) and instance_id for instance_id in instance_ids):
        raise BuildError("Every source row must have a non-empty string instance_id")
    if len(set(instance_ids)) != EXPECTED_CURRENT_TASK_COUNT:
        raise BuildError("Source instance_id values are not unique")

    digest = hashlib.sha256()
    for _, row in items:
        digest.update(canonical_json_bytes(row))
        digest.update(b"\n")
    observed_digest = digest.hexdigest()
    if observed_digest != HF_CURRENT_ROWS_CANONICAL_SHA256:
        raise BuildError(
            "Pinned source-row digest mismatch: "
            f"expected {HF_CURRENT_ROWS_CANONICAL_SHA256}, observed {observed_digest}"
        )


def decode_serialized_text(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        return str(value)
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == '"' and stripped[-1] == '"':
        try:
            decoded = json.loads(stripped)
        except json.JSONDecodeError:
            return value
        if isinstance(decoded, str):
            return decoded
    return value


def parse_string_list(value: Any, *, field: str, instance_id: str) -> list[str]:
    if isinstance(value, list):
        parsed = value
    elif isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            parsed = []
        else:
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                try:
                    parsed = ast.literal_eval(stripped)
                except (SyntaxError, ValueError) as exc:
                    raise BuildError(
                        f"{instance_id}: cannot parse {field} as a list: {exc}"
                    ) from exc
    else:
        raise BuildError(f"{instance_id}: {field} has unsupported type {type(value).__name__}")
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise BuildError(f"{instance_id}: {field} is not a list of strings")
    return parsed


def parse_optional_string_list(value: Any) -> tuple[list[str], str]:
    raw = "" if value is None else str(value)
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value), raw
    if not isinstance(value, str) or not value.strip():
        return [], raw
    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(value)
        except (json.JSONDecodeError, SyntaxError, ValueError):
            continue
        if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
            return parsed, raw
    return [], raw


def text_fence(text: str, language: str = "text") -> str:
    longest = 0
    run = 0
    for character in text:
        if character == "`":
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    fence = "`" * max(3, longest + 1)
    return f"{fence}{language}\n{text.rstrip()}\n{fence}"


def validate_drafter_prior_run_boundary(markdown: str, *, instance_id: str) -> None:
    """Reject public-run/model metadata from the per-case drafter input."""

    normalized = markdown.lower()
    found = [
        marker
        for marker in FORBIDDEN_DRAFTER_PRIOR_RUN_MARKERS
        if marker in normalized
    ]
    if found:
        raise BuildError(
            f"{instance_id}: case_packet.md contains forbidden prior-run metadata: "
            + ", ".join(found)
        )


def source_lock() -> dict[str, Any]:
    current_parquet_url = (
        f"https://huggingface.co/datasets/{HF_DATASET_ID}/resolve/"
        f"{HF_CURRENT_REVISION}/{HF_CURRENT_PARQUET_PATH}"
    )
    return {
        "schema_version": "swe_bench_pro_source_lock/v1",
        "benchmark": {
            "name": "SWE-bench Pro",
            "public_split_name": HF_SPLIT,
            "current_task_count": EXPECTED_CURRENT_TASK_COUNT,
        },
        "current_regrade_contract": {
            "contract_id": "swe_bench_pro_current_regrade_2026_02_23",
            "dataset": {
                "repository": HF_DATASET_ID,
                "revision": HF_CURRENT_REVISION,
                "data_commit": HF_CURRENT_DATA_COMMIT,
                "config": HF_CONFIG,
                "split": HF_SPLIT,
                "task_count": EXPECTED_CURRENT_TASK_COUNT,
                "parquet_path": HF_CURRENT_PARQUET_PATH,
                "parquet_url": current_parquet_url,
                "parquet_sha256": HF_CURRENT_PARQUET_SHA256,
                "parquet_size_bytes": HF_CURRENT_PARQUET_SIZE,
                "canonical_rows_sha256": HF_CURRENT_ROWS_CANONICAL_SHA256,
                "canonical_rows_rule": "sha256(concat(canonical_json(row), LF) in row_idx order)",
            },
            "evaluator": {
                "repository": OFFICIAL_REPOSITORY,
                "commit": CURRENT_EVALUATOR_COMMIT,
                "entrypoint": "swe_bench_pro_eval.py",
                "score_rule": (
                    "resolved iff every named FAIL_TO_PASS and PASS_TO_PASS test is present "
                    "with status PASSED in parsed evaluator output"
                ),
                "cli_template": (
                    "python swe_bench_pro_eval.py --raw_sample_path <pinned-lowercase-field.jsonl> "
                    "--patch_path <predictions.json> --output_dir <output-dir> "
                    "--scripts_dir run_scripts --dockerhub_username jefzda "
                    "--num_workers <n> [--use_local_docker] [--block_network]"
                ),
            },
            "task_count": EXPECTED_CURRENT_TASK_COUNT,
        },
        "historical_public_trajectory_contract": {
            "contract_id": "swe_bench_pro_public_trajectory_2025_10_13",
            "dataset_revision_nearest_before_run": HF_HISTORICAL_REVISION,
            "repository_commit_nearest_before_run": HISTORICAL_REPOSITORY_COMMIT_BY_DATE,
            "repository_commit_status": "date-bounded provenance; the S3 objects do not declare an exact harness commit",
            "reference_run_prefix": HISTORICAL_REFERENCE_RUN,
            "reference_run_configuration": {
                "scaffold": "SWE-Agent",
                "turn_limit": 250,
                "cost_cap": None,
                "configuration_source": f"{OFFICIAL_REPOSITORY}/tree/{CURRENT_EVALUATOR_COMMIT}/traj/README.md",
            },
            "dataset_task_count": EXPECTED_CURRENT_TASK_COUNT,
            "trajectory_task_count": EXPECTED_HISTORICAL_TRAJECTORY_COUNT,
            "missing_instance_ids": [HISTORICAL_MISSING_INSTANCE_ID],
            "s3_root": S3_ROOT,
            "s3_https_root": S3_HTTPS_ROOT,
            "s3_listing_cli": f"aws s3 ls {S3_ROOT} --no-sign-request",
            "s3_download_cli": (
                f"aws s3 cp {S3_ROOT}{HISTORICAL_REFERENCE_RUN}/ <local-dir> "
                "--recursive --no-sign-request"
            ),
            "docent_url": DOCENT_URL,
            "external_store_mutability": (
                "S3 keys are public but not release-tagged; record object key, size, ETag, "
                "LastModified, and a local SHA-256 when acquiring an artifact"
            ),
        },
        "cross_contract_policy": {
            "same_contract": False,
            "reason": (
                "The public trajectories predate the 2026-02-09 dataset/test update. "
                "Historical official rewards must not be treated as labels under the current "
                "regrade contract without rerunning the pinned evaluator."
            ),
            "required_label_fields": [
                "historical_official_reward",
                "recomputed_reward",
                "recomputed_reward_contract_id",
            ],
        },
        "materialization_policy": {
            "included": [
                "task-visible fields",
                "test patch",
                "FAIL_TO_PASS/PASS_TO_PASS names",
                "environment and evaluator references",
                "solution-patch presence/hash/pointer",
            ],
            "excluded": [
                "repository checkout",
                "Docker image or layer",
                "public trajectory",
                "historical evaluator output",
                "official solution patch body",
            ],
        },
    }


def row_components(row: Mapping[str, Any]) -> dict[str, Any]:
    instance_id = row.get("instance_id")
    if not isinstance(instance_id, str) or not instance_id:
        raise BuildError("Source row has no non-empty instance_id")
    required_strings = ("repo", "base_commit", "patch", "test_patch", "dockerhub_tag")
    for field in required_strings:
        if not isinstance(row.get(field), str):
            raise BuildError(f"{instance_id}: {field} must be a string")

    fail_to_pass = parse_string_list(
        row.get("fail_to_pass"), field="fail_to_pass", instance_id=instance_id
    )
    pass_to_pass = parse_string_list(
        row.get("pass_to_pass"), field="pass_to_pass", instance_id=instance_id
    )
    selected_tests = parse_string_list(
        row.get("selected_test_files_to_run"),
        field="selected_test_files_to_run",
        instance_id=instance_id,
    )
    issue_specificity, issue_specificity_raw = parse_optional_string_list(
        row.get("issue_specificity")
    )
    issue_categories, issue_categories_raw = parse_optional_string_list(
        row.get("issue_categories")
    )

    task = {
        "instance_id": instance_id,
        "repo": row["repo"],
        "base_commit": row["base_commit"],
        "repo_language": row.get("repo_language", ""),
        "problem_statement": decode_serialized_text(row.get("problem_statement")),
        "requirements": decode_serialized_text(row.get("requirements")),
        "interface": decode_serialized_text(row.get("interface")),
        "issue_specificity": issue_specificity,
        "issue_categories": issue_categories,
        "source_serialization": {
            "issue_specificity": issue_specificity_raw,
            "issue_categories": issue_categories_raw,
        },
    }
    evaluation = {
        "FAIL_TO_PASS": fail_to_pass,
        "PASS_TO_PASS": pass_to_pass,
        "selected_test_files_to_run": selected_tests,
        "test_patch": row["test_patch"],
        "test_patch_sha256": sha256_bytes(row["test_patch"].encode("utf-8")),
        "test_patch_size_bytes": len(row["test_patch"].encode("utf-8")),
    }
    solution = {
        "present_in_pinned_dataset": bool(row["patch"]),
        "embedded_in_packet": False,
        "sha256": sha256_bytes(row["patch"].encode("utf-8")),
        "size_bytes": len(row["patch"].encode("utf-8")),
        "source_pointer": (
            f"hf://datasets/{HF_DATASET_ID}@{HF_CURRENT_REVISION}/"
            f"{HF_SPLIT}#instance_id={instance_id}/patch"
        ),
        "native_verifier_dependency": False,
    }
    environment = {
        "container_registry": "docker.io",
        "container_repository": "jefzda/sweap-images",
        "dockerhub_tag": row["dockerhub_tag"],
        "image_reference": f"docker.io/jefzda/sweap-images:{row['dockerhub_tag']}",
        "image_digest": None,
        "image_reference_status": "tag supplied by pinned dataset; resolve and record digest before execution",
        "working_directory": "/app",
        "before_repo_set_cmd": row.get("before_repo_set_cmd", ""),
        "selected_test_files_to_run": selected_tests,
        "run_script_ref": (
            f"{OFFICIAL_REPOSITORY}/blob/{CURRENT_EVALUATOR_COMMIT}/run_scripts/"
            f"{instance_id}/run_script.sh"
        ),
        "parser_ref": (
            f"{OFFICIAL_REPOSITORY}/blob/{CURRENT_EVALUATOR_COMMIT}/run_scripts/"
            f"{instance_id}/parser.py"
        ),
        "instance_info_ref": (
            f"{OFFICIAL_REPOSITORY}/blob/{CURRENT_EVALUATOR_COMMIT}/run_scripts/"
            f"{instance_id}/instance_info.txt"
        ),
    }
    return {
        "instance_id": instance_id,
        "task": task,
        "evaluation": evaluation,
        "solution": solution,
        "environment": environment,
    }


def build_agent_input(task: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "swe_bench_pro_agent_input/v1",
        "benchmark": {
            "name": "SWE-bench Pro",
            "split": HF_SPLIT,
            "dataset_revision": HF_CURRENT_REVISION,
        },
        "instance_id": task["instance_id"],
        "repo": task["repo"],
        "base_commit": task["base_commit"],
        "repo_language": task["repo_language"],
        "problem_statement": task["problem_statement"],
        "requirements": task["requirements"],
        "interface": task["interface"],
    }


def build_case_packet(
    *,
    components: Mapping[str, Any],
    source_row_sha256: str,
    agent_input_sha256: str,
) -> dict[str, Any]:
    task = components["task"]
    evaluation = components["evaluation"]
    return {
        "schema_version": "swe_bench_pro_case_packet/v2",
        "visibility": "controller_and_human_review_only",
        "benchmark": {
            "name": "SWE-bench Pro",
            "split": HF_SPLIT,
            "dataset_revision": HF_CURRENT_REVISION,
            "dataset_data_commit": HF_CURRENT_DATA_COMMIT,
            "evaluator_repository": OFFICIAL_REPOSITORY,
            "evaluator_commit": CURRENT_EVALUATOR_COMMIT,
        },
        "task": task,
        "model_visible_input": {
            "path": "agent_input.json",
            "sha256": agent_input_sha256,
            "field_allowlist": [
                "instance_id",
                "repo",
                "base_commit",
                "repo_language",
                "problem_statement",
                "requirements",
                "interface",
            ],
        },
        "evaluator_reference": {
            "implementation": "scaleapi/SWE-bench_Pro-os",
            "commit": CURRENT_EVALUATOR_COMMIT,
            "entrypoint": "swe_bench_pro_eval.py",
            "native_success": (
                "Every named FAIL_TO_PASS and PASS_TO_PASS test appears with status "
                "PASSED in the parsed evaluator output."
            ),
            "score_composition": "set(FAIL_TO_PASS + PASS_TO_PASS) <= passed_test_names",
            "FAIL_TO_PASS": evaluation["FAIL_TO_PASS"],
            "PASS_TO_PASS": evaluation["PASS_TO_PASS"],
            "selected_test_files_to_run": evaluation["selected_test_files_to_run"],
            "test_patch": evaluation["test_patch"],
            "test_patch_sha256": evaluation["test_patch_sha256"],
            "required_regrade_artifacts": [
                "submitted_patch.diff",
                "parsed_test_output.json",
                "stdout.log",
                "stderr.log",
                "environment_manifest.json",
            ],
        },
        "official_solution_reference": components["solution"],
        "environment_reference": components["environment"],
        "provenance": {
            "source_row_canonical_sha256": source_row_sha256,
            "source_lock_path": "../source_lock.json",
            "current_regrade_contract_id": "swe_bench_pro_current_regrade_2026_02_23",
        },
        "leakage_control": {
            "model_receives_only_agent_input_json": True,
            "official_solution_patch_body_embedded": False,
            "test_patch_embedded_for_drafter_and_reviewer": True,
            "evaluator_payload_embedded_in_agent_input": False,
            "prior_run_metadata_embedded_in_drafter_packet": False,
        },
    }


def task_visible_view(packet: Mapping[str, Any]) -> dict[str, Any]:
    task = packet["task"]
    return {
        key: task[key]
        for key in (
            "instance_id",
            "repo",
            "base_commit",
            "repo_language",
            "problem_statement",
            "requirements",
            "interface",
        )
    }


def test_contract_view(packet: Mapping[str, Any]) -> dict[str, Any]:
    evaluator = packet["evaluator_reference"]
    return {
        "native_success": evaluator["native_success"],
        "score_composition": evaluator["score_composition"],
        "FAIL_TO_PASS": evaluator["FAIL_TO_PASS"],
        "PASS_TO_PASS": evaluator["PASS_TO_PASS"],
        "selected_test_files_to_run": evaluator["selected_test_files_to_run"],
        "required_regrade_artifacts": evaluator["required_regrade_artifacts"],
    }


def solution_metadata_view(packet: Mapping[str, Any]) -> dict[str, Any]:
    solution = packet["official_solution_reference"]
    return {
        "present_in_pinned_dataset": solution["present_in_pinned_dataset"],
        "embedded_in_packet": solution["embedded_in_packet"],
        "sha256": solution["sha256"],
        "size_bytes": solution["size_bytes"],
        "source_pointer": solution["source_pointer"],
        "native_verifier_dependency": solution["native_verifier_dependency"],
    }


def raw_case_file_sources(packet: Mapping[str, Any]) -> dict[str, str]:
    instance_id = packet["task"]["instance_id"]
    hf_row_ref = (
        f"hf://datasets/{HF_DATASET_ID}@{HF_CURRENT_REVISION}/"
        f"{HF_SPLIT}#instance_id={instance_id}"
    )
    return {
        "official/huggingface/task_visible.json": hf_row_ref,
        "official/evaluator/test_contract.json": (
            f"{OFFICIAL_REPOSITORY}/blob/{CURRENT_EVALUATOR_COMMIT}/"
            "swe_bench_pro_eval.py"
        ),
        "official/evaluator/test.patch": f"{hf_row_ref}/test_patch",
        "official/evaluator/solution_patch_metadata.json": f"{hf_row_ref}/patch",
        "official/environment/runtime.json": (
            f"{hf_row_ref}/runtime_fields; evaluator_scripts="
            f"{OFFICIAL_REPOSITORY}/tree/{CURRENT_EVALUATOR_COMMIT}/"
            f"run_scripts/{instance_id}"
        ),
    }


def raw_case_tree_digest(raw_case_dir: Path) -> tuple[str, int, int]:
    files = sorted(path for path in raw_case_dir.rglob("*") if path.is_file())
    lines: list[str] = []
    total_bytes = 0
    for path in files:
        relative = path.relative_to(raw_case_dir).as_posix()
        size = path.stat().st_size
        total_bytes += size
        lines.append(f"{relative}\t{sha256_file(path)}\t{size}\n")
    return sha256_bytes("".join(lines).encode("utf-8")), len(files), total_bytes


def materialize_raw_case(case_dir: Path, packet: Mapping[str, Any]) -> dict[str, Any]:
    """Write the five compact source snapshots consumed by the packet drafter."""

    raw_case_dir = case_dir / "raw_case"
    if raw_case_dir.exists():
        if raw_case_dir.is_symlink() or not raw_case_dir.is_dir():
            raise BuildError(f"Refusing unsafe raw_case path: {raw_case_dir}")
        shutil.rmtree(raw_case_dir)
    raw_case_dir.mkdir(parents=True)

    write_json(
        raw_case_dir / "official/huggingface/task_visible.json",
        task_visible_view(packet),
    )
    write_json(
        raw_case_dir / "official/evaluator/test_contract.json",
        test_contract_view(packet),
    )
    # Preserve the dataset test-patch bytes exactly. In particular, do not add
    # a newline that was not present in the pinned source row.
    write_text(
        raw_case_dir / "official/evaluator/test.patch",
        packet["evaluator_reference"]["test_patch"],
    )
    write_json(
        raw_case_dir / "official/evaluator/solution_patch_metadata.json",
        solution_metadata_view(packet),
    )
    write_json(
        raw_case_dir / "official/environment/runtime.json",
        packet["environment_reference"],
    )
    observed_files = sorted(
        path.relative_to(raw_case_dir).as_posix()
        for path in raw_case_dir.rglob("*")
        if path.is_file()
    )
    if observed_files != sorted(RAW_CASE_FILES):
        raise BuildError(f"Unexpected raw_case inventory: {observed_files}")
    file_sources = raw_case_file_sources(packet)
    file_hashes = {
        relative: sha256_file(raw_case_dir / relative)
        for relative in observed_files
    }
    file_sizes = {
        relative: (raw_case_dir / relative).stat().st_size
        for relative in observed_files
    }
    tree_sha256, file_count, total_bytes = raw_case_tree_digest(raw_case_dir)
    return {
        "packet_files": list(RAW_CASE_FILES),
        "file_sources": file_sources,
        "sha256_per_file": file_hashes,
        "size_bytes_per_file": file_sizes,
        "tree_sha256": tree_sha256,
        "file_count": file_count,
        "total_bytes": total_bytes,
    }


def build_case_markdown(
    packet: Mapping[str, Any],
    *,
    raw_case_dir: Path,
    raw_bundle: Mapping[str, Any],
) -> str:
    task = packet["task"]
    evaluator = packet["evaluator_reference"]
    sections = [
        "# Case Packet",
        "",
        "## Case Metadata",
        "",
        "- domain: `swe_bench_pro`",
        f"- case_unit_id: `{task['instance_id']}`",
        f"- task_id: `{task['instance_id']}`",
        f"- repository: `{task['repo']}`",
        f"- base_commit: `{task['base_commit']}`",
        f"- current dataset revision: `{HF_CURRENT_REVISION}`",
        f"- current evaluator commit: `{CURRENT_EVALUATOR_COMMIT}`",
        "",
        "## Native Benchmark Claim",
        "",
        evaluator["native_success"],
        "The official solution patch is not part of this native decision rule and its body is not embedded.",
        "",
        "## Visibility Boundary",
        "",
        "This source-rich packet is for checklist drafting and human review only. The tested agent",
        "receives only `agent_input.json`. Do not place this packet, the test patch, named verifier",
        "tests, environment setup commands, benchmark-run artifacts, or solution metadata in the agent prompt.",
        "",
        "## Source Inventory",
        "",
    ]
    packet_files = [str(value) for value in raw_bundle["packet_files"]]
    for relative in packet_files:
        sections.append(f"- `{relative}`")
    sections.extend(["", "## Packet Source Files", ""])
    file_sources = raw_bundle["file_sources"]
    for relative in packet_files:
        path = raw_case_dir / relative
        language = "diff" if path.suffix == ".patch" else "json"
        sections.extend(
            [
                f"### `{relative}`",
                "",
                f"Source ref: `{file_sources[relative]}`",
                "",
            ]
        )
        if relative == "official/evaluator/solution_patch_metadata.json":
            sections.extend(
                [
                    "The solution body is deliberately excluded; only integrity metadata and an external pointer are retained.",
                    "",
                ]
            )
        sections.extend(
            [
                text_fence(path.read_text(encoding="utf-8"), language),
                "",
            ]
        )
    return "\n".join(sections)


def build_raw_manifest(
    *,
    components: Mapping[str, Any],
    row_position: int,
    source_row_sha256: str,
    hashes: Mapping[str, str],
    raw_bundle: Mapping[str, Any],
) -> dict[str, Any]:
    instance_id = components["instance_id"]
    return {
        "schema_version": "swe_bench_pro_raw_case_manifest/v3",
        "domain": "swe_bench_pro",
        "case_unit_id": instance_id,
        "task_id": instance_id,
        "source_dataset": {
            "repository": HF_DATASET_ID,
            "revision": HF_CURRENT_REVISION,
            "data_commit": HF_CURRENT_DATA_COMMIT,
            "config": HF_CONFIG,
            "split": HF_SPLIT,
            "row_idx": row_position,
            "row_canonical_sha256": source_row_sha256,
            "corpus_canonical_sha256": HF_CURRENT_ROWS_CANONICAL_SHA256,
            "parquet_sha256": HF_CURRENT_PARQUET_SHA256,
        },
        "official_evaluator": {
            "repository": OFFICIAL_REPOSITORY,
            "commit": CURRENT_EVALUATOR_COMMIT,
            "entrypoint": "swe_bench_pro_eval.py",
        },
        "official_solution_patch": components["solution"],
        "test_patch": {
            "embedded_in_case_packet": True,
            "sha256": components["evaluation"]["test_patch_sha256"],
            "size_bytes": components["evaluation"]["test_patch_size_bytes"],
        },
        "current_regrade_contract_id": "swe_bench_pro_current_regrade_2026_02_23",
        "model_visible_files": ["agent_input.json"],
        "controller_runtime_files": ["case_packet.json"],
        "drafter_reviewer_only_files": [
            "case_packet.md",
            "raw_case_manifest.json",
            "raw_case/**",
        ],
        "source_refs": list(dict.fromkeys(raw_bundle["file_sources"].values())),
        "copied_files": sorted(RAW_CASE_FILES),
        "official_files": sorted(RAW_CASE_FILES),
        "derived_files": [],
        "packet_files": list(raw_bundle["packet_files"]),
        "sha256_per_file": dict(sorted(raw_bundle["sha256_per_file"].items())),
        "file_sources": dict(sorted(raw_bundle["file_sources"].items())),
        "materialized_files": [
            *CASE_FILES,
            *(f"raw_case/{relative}" for relative in RAW_CASE_FILES),
        ],
        "excluded_external_artifacts": [
            "repository checkout",
            "Docker image or layer",
            "third-party benchmark-run artifacts",
            "official solution patch body",
        ],
        "top_level_file_sha256": dict(hashes),
    }


def make_case(
    *,
    output_root: Path,
    row_position: int,
    row: Mapping[str, Any],
) -> dict[str, Any]:
    components = row_components(row)
    instance_id = components["instance_id"]
    case_dir = output_root / instance_id
    case_dir.mkdir(parents=True, exist_ok=True)

    source_row_sha256 = sha256_bytes(canonical_json_bytes(row))
    agent_input = build_agent_input(components["task"])
    write_json(case_dir / "agent_input.json", agent_input)
    agent_input_sha256 = sha256_file(case_dir / "agent_input.json")

    packet = build_case_packet(
        components=components,
        source_row_sha256=source_row_sha256,
        agent_input_sha256=agent_input_sha256,
    )
    write_json(case_dir / "case_packet.json", packet)
    raw_bundle = materialize_raw_case(case_dir, packet)
    markdown = build_case_markdown(
        packet,
        raw_case_dir=case_dir / "raw_case",
        raw_bundle=raw_bundle,
    )
    validate_drafter_prior_run_boundary(markdown, instance_id=instance_id)
    write_text(case_dir / "case_packet.md", markdown)

    preliminary_hashes = {
        "agent_input.json": agent_input_sha256,
        "case_packet.json": sha256_file(case_dir / "case_packet.json"),
        "case_packet.md": sha256_file(case_dir / "case_packet.md"),
    }
    manifest = build_raw_manifest(
        components=components,
        row_position=row_position,
        source_row_sha256=source_row_sha256,
        hashes=preliminary_hashes,
        raw_bundle=raw_bundle,
    )
    write_json(case_dir / "raw_case_manifest.json", manifest)

    file_hashes = {
        name: sha256_file(case_dir / name)
        for name in CASE_FILES
    }
    file_sizes = {
        name: (case_dir / name).stat().st_size
        for name in CASE_FILES
    }
    return {
        "row_idx": row_position,
        "instance_id": instance_id,
        "case_dir": instance_id,
        "repo": components["task"]["repo"],
        "base_commit": components["task"]["base_commit"],
        "dockerhub_tag": components["environment"]["dockerhub_tag"],
        "source_row_canonical_sha256": source_row_sha256,
        "file_sha256": file_hashes,
        "file_size_bytes": file_sizes,
        "raw_case_file_sha256": raw_bundle["sha256_per_file"],
        "raw_case_file_size_bytes": raw_bundle["size_bytes_per_file"],
        "raw_case_tree_sha256": raw_bundle["tree_sha256"],
        "raw_case_file_count": raw_bundle["file_count"],
        "raw_case_total_bytes": raw_bundle["total_bytes"],
    }


def write_root_artifacts(output_root: Path, entries: Sequence[Mapping[str, Any]]) -> None:
    lock = source_lock()
    write_json(output_root / "source_lock.json", lock)
    lock_hash = sha256_file(output_root / "source_lock.json")
    write_text(output_root / "source_lock.json.sha256", f"{lock_hash}  source_lock.json\n")

    entry_digest = hashlib.sha256()
    for entry in entries:
        entry_digest.update(canonical_json_bytes(entry))
        entry_digest.update(b"\n")
    top_level_case_bytes = sum(
        sum(entry["file_size_bytes"].values())
        for entry in entries
    )
    raw_case_bytes = sum(entry["raw_case_total_bytes"] for entry in entries)
    index = {
        "schema_version": "swe_bench_pro_case_packet_index/v2",
        "status": "ready",
        "domain": "swe_bench_pro",
        "benchmark": "SWE-bench Pro",
        "split": HF_SPLIT,
        "dataset_revision": HF_CURRENT_REVISION,
        "evaluator_commit": CURRENT_EVALUATOR_COMMIT,
        "case_count": len(entries),
        "files_per_case": list(CASE_FILES),
        "top_level_files_per_case": list(CASE_FILES),
        "raw_case_files_per_case": list(RAW_CASE_FILES),
        "generated_top_level_case_file_count": len(entries) * len(CASE_FILES),
        "generated_raw_case_file_count": len(entries) * len(RAW_CASE_FILES),
        "generated_case_file_count": len(entries) * (len(CASE_FILES) + len(RAW_CASE_FILES)),
        "generated_top_level_case_bytes": top_level_case_bytes,
        "generated_raw_case_bytes": raw_case_bytes,
        "generated_case_bytes": top_level_case_bytes + raw_case_bytes,
        "source_rows_canonical_sha256": HF_CURRENT_ROWS_CANONICAL_SHA256,
        "entry_sequence_sha256": entry_digest.hexdigest(),
        "source_lock_sha256": lock_hash,
        "entries": list(entries),
    }
    write_json(output_root / "index.json", index)
    index_hash = sha256_file(output_root / "index.json")
    write_text(output_root / "index.json.sha256", f"{index_hash}  index.json\n")
    status = {
        "schema_version": "swe_bench_pro_case_packet_generation_status/v1",
        "status": "ready",
        "domain": "swe_bench_pro",
        "case_count": len(entries),
        "dataset_revision": HF_CURRENT_REVISION,
        "dataset_data_commit": HF_CURRENT_DATA_COMMIT,
        "source_rows_canonical_sha256": HF_CURRENT_ROWS_CANONICAL_SHA256,
        "evaluator_commit": CURRENT_EVALUATOR_COMMIT,
        "source_lock_sha256": lock_hash,
        "index_sha256": index_hash,
    }
    write_json(output_root / "generation_status.json", status)


def validate_generated(output_root: Path) -> dict[str, Any]:
    lock_path = output_root / "source_lock.json"
    index_path = output_root / "index.json"
    status_path = output_root / "generation_status.json"
    for path in (
        lock_path,
        index_path,
        status_path,
        output_root / "source_lock.json.sha256",
        output_root / "index.json.sha256",
    ):
        if not path.is_file():
            raise BuildError(f"Missing root artifact: {path}")

    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    index = json.loads(index_path.read_text(encoding="utf-8"))
    status = json.loads(status_path.read_text(encoding="utf-8"))
    if lock.get("current_regrade_contract", {}).get("dataset", {}).get("revision") != HF_CURRENT_REVISION:
        raise BuildError("source_lock.json does not carry the pinned current revision")
    historical_contract = lock.get("historical_public_trajectory_contract", {})
    if (
        historical_contract.get("reference_run_prefix") != HISTORICAL_REFERENCE_RUN
        or historical_contract.get("trajectory_task_count")
        != EXPECTED_HISTORICAL_TRAJECTORY_COUNT
        or historical_contract.get("missing_instance_ids")
        != [HISTORICAL_MISSING_INSTANCE_ID]
        or historical_contract.get("s3_root") != S3_ROOT
        or historical_contract.get("s3_https_root") != S3_HTTPS_ROOT
    ):
        raise BuildError("source_lock.json lost root-only public-run acquisition metadata")
    if index.get("case_count") != EXPECTED_CURRENT_TASK_COUNT:
        raise BuildError("index.json case_count mismatch")
    if (
        index.get("schema_version") != "swe_bench_pro_case_packet_index/v2"
        or index.get("status") != "ready"
        or index.get("domain") != "swe_bench_pro"
        or index.get("dataset_revision") != HF_CURRENT_REVISION
        or index.get("evaluator_commit") != CURRENT_EVALUATOR_COMMIT
    ):
        raise BuildError("index.json readiness/revision metadata mismatch")
    entries = index.get("entries")
    if not isinstance(entries, list) or len(entries) != EXPECTED_CURRENT_TASK_COUNT:
        raise BuildError("index.json entries mismatch")

    expected_lock_line = f"{sha256_file(lock_path)}  source_lock.json\n"
    if (output_root / "source_lock.json.sha256").read_text(encoding="utf-8") != expected_lock_line:
        raise BuildError("source_lock.json.sha256 mismatch")
    expected_index_line = f"{sha256_file(index_path)}  index.json\n"
    if (output_root / "index.json.sha256").read_text(encoding="utf-8") != expected_index_line:
        raise BuildError("index.json.sha256 mismatch")
    if (
        status.get("status") != "ready"
        or status.get("domain") != "swe_bench_pro"
        or status.get("case_count") != EXPECTED_CURRENT_TASK_COUNT
        or status.get("dataset_revision") != HF_CURRENT_REVISION
        or status.get("dataset_data_commit") != HF_CURRENT_DATA_COMMIT
        or status.get("source_rows_canonical_sha256")
        != HF_CURRENT_ROWS_CANONICAL_SHA256
        or status.get("evaluator_commit") != CURRENT_EVALUATOR_COMMIT
        or status.get("source_lock_sha256") != sha256_file(lock_path)
        or status.get("index_sha256") != sha256_file(index_path)
    ):
        raise BuildError("generation_status.json mismatch")

    seen: set[str] = set()
    total_bytes = 0
    for entry in entries:
        instance_id = entry.get("instance_id")
        if not isinstance(instance_id, str) or instance_id in seen:
            raise BuildError(f"Invalid or duplicate index instance_id: {instance_id!r}")
        seen.add(instance_id)
        case_dir = output_root / instance_id
        if case_dir.is_symlink() or not case_dir.is_dir():
            raise BuildError(f"{instance_id}: case path is not a real directory")
        observed_files = sorted(path.name for path in case_dir.iterdir() if path.is_file())
        if observed_files != sorted(CASE_FILES):
            raise BuildError(f"{instance_id}: unexpected case files {observed_files}")
        observed_dirs = sorted(path.name for path in case_dir.iterdir() if path.is_dir())
        if observed_dirs != ["raw_case"]:
            raise BuildError(f"{instance_id}: unexpected case directories {observed_dirs}")
        markdown = (case_dir / "case_packet.md").read_text(encoding="utf-8")
        # Run the semantic leakage boundary before hash comparisons so a
        # reintroduced prior-run pointer receives an explicit fail-closed error
        # even when the corpus index has not yet been regenerated.
        validate_drafter_prior_run_boundary(markdown, instance_id=instance_id)
        for name in CASE_FILES:
            path = case_dir / name
            expected_hash = entry["file_sha256"].get(name)
            observed_hash = sha256_file(path)
            if observed_hash != expected_hash:
                raise BuildError(f"{instance_id}/{name}: SHA-256 mismatch")
            expected_size = entry["file_size_bytes"].get(name)
            if path.stat().st_size != expected_size:
                raise BuildError(f"{instance_id}/{name}: size mismatch")
            total_bytes += path.stat().st_size

        raw_case_dir = case_dir / "raw_case"
        raw_tree = list(raw_case_dir.rglob("*"))
        if raw_case_dir.is_symlink() or any(path.is_symlink() for path in raw_tree):
            raise BuildError(f"{instance_id}: raw_case contains a symlink")
        observed_raw_files = sorted(
            path.relative_to(raw_case_dir).as_posix()
            for path in raw_tree
            if path.is_file()
        )
        if observed_raw_files != sorted(RAW_CASE_FILES):
            raise BuildError(
                f"{instance_id}: unexpected raw_case files {observed_raw_files}"
            )
        for relative in RAW_CASE_FILES:
            path = raw_case_dir / relative
            expected_hash = entry["raw_case_file_sha256"].get(relative)
            expected_size = entry["raw_case_file_size_bytes"].get(relative)
            if sha256_file(path) != expected_hash:
                raise BuildError(f"{instance_id}/raw_case/{relative}: SHA-256 mismatch")
            if path.stat().st_size != expected_size:
                raise BuildError(f"{instance_id}/raw_case/{relative}: size mismatch")
            total_bytes += path.stat().st_size
        raw_tree_hash, raw_file_count, raw_total_bytes = raw_case_tree_digest(raw_case_dir)
        if (
            raw_tree_hash != entry.get("raw_case_tree_sha256")
            or raw_file_count != entry.get("raw_case_file_count")
            or raw_total_bytes != entry.get("raw_case_total_bytes")
        ):
            raise BuildError(f"{instance_id}: raw_case tree metadata mismatch")

        agent_input = json.loads((case_dir / "agent_input.json").read_text(encoding="utf-8"))
        if set(agent_input) != {
            "schema_version",
            "benchmark",
            "instance_id",
            "repo",
            "base_commit",
            "repo_language",
            "problem_statement",
            "requirements",
            "interface",
        }:
            raise BuildError(f"{instance_id}: agent_input.json field boundary changed")
        packet = json.loads((case_dir / "case_packet.json").read_text(encoding="utf-8"))
        if packet.get("schema_version") != "swe_bench_pro_case_packet/v2":
            raise BuildError(f"{instance_id}: case packet schema version mismatch")
        if packet.get("official_solution_reference", {}).get("embedded_in_packet") is not False:
            raise BuildError(f"{instance_id}: solution body leakage boundary changed")
        if "patch" in packet.get("official_solution_reference", {}):
            raise BuildError(f"{instance_id}: solution patch body is embedded")
        if set(packet.get("provenance", {})) != {
            "source_row_canonical_sha256",
            "source_lock_path",
            "current_regrade_contract_id",
        }:
            raise BuildError(f"{instance_id}: per-case provenance boundary changed")
        if (
            packet.get("leakage_control", {}).get(
                "prior_run_metadata_embedded_in_drafter_packet"
            )
            is not False
        ):
            raise BuildError(f"{instance_id}: prior-run leakage assertion changed")
        manifest = json.loads((case_dir / "raw_case_manifest.json").read_text(encoding="utf-8"))
        if manifest.get("schema_version") != "swe_bench_pro_raw_case_manifest/v3":
            raise BuildError(f"{instance_id}: raw manifest schema version mismatch")
        if any(
            key in manifest
            for key in (
                "historical_public_trajectory",
                "historical_public_trajectory_contract_id",
            )
        ):
            raise BuildError(f"{instance_id}: raw manifest contains prior-run metadata")
        required_manifest_fields = {
            "source_refs",
            "copied_files",
            "official_files",
            "derived_files",
            "packet_files",
            "sha256_per_file",
        }
        if not required_manifest_fields <= set(manifest):
            raise BuildError(f"{instance_id}: raw manifest compatibility fields missing")
        if (
            manifest.get("copied_files") != sorted(RAW_CASE_FILES)
            or manifest.get("official_files") != sorted(RAW_CASE_FILES)
            or manifest.get("derived_files") != []
            or manifest.get("packet_files") != list(RAW_CASE_FILES)
            or set(manifest.get("sha256_per_file", {})) != set(RAW_CASE_FILES)
            or set(manifest.get("file_sources", {})) != set(RAW_CASE_FILES)
        ):
            raise BuildError(f"{instance_id}: raw manifest inventory mismatch")
        if not all(
            isinstance(ref, str) and ref and not Path(ref.split("#", 1)[0]).is_absolute()
            for ref in manifest.get("source_refs", [])
        ):
            raise BuildError(f"{instance_id}: invalid raw manifest source_refs")
        for relative in RAW_CASE_FILES:
            if manifest["sha256_per_file"].get(relative) != sha256_file(
                raw_case_dir / relative
            ):
                raise BuildError(
                    f"{instance_id}: raw manifest hash mismatch for {relative}"
                )
        for name in ("agent_input.json", "case_packet.json", "case_packet.md"):
            expected_hash = manifest["top_level_file_sha256"].get(name)
            if expected_hash != sha256_file(case_dir / name):
                raise BuildError(f"{instance_id}: manifest hash mismatch for {name}")
        if json.loads(
            (raw_case_dir / "official/huggingface/task_visible.json").read_text(
                encoding="utf-8"
            )
        ) != task_visible_view(packet):
            raise BuildError(f"{instance_id}: task-visible raw source drift")
        if json.loads(
            (raw_case_dir / "official/evaluator/test_contract.json").read_text(
                encoding="utf-8"
            )
        ) != test_contract_view(packet):
            raise BuildError(f"{instance_id}: test-contract raw source drift")
        if (raw_case_dir / "official/evaluator/test.patch").read_text(
            encoding="utf-8"
        ) != packet["evaluator_reference"]["test_patch"]:
            raise BuildError(f"{instance_id}: test-patch raw source drift")
        solution_metadata = json.loads(
            (raw_case_dir / "official/evaluator/solution_patch_metadata.json").read_text(
                encoding="utf-8"
            )
        )
        if solution_metadata != solution_metadata_view(packet) or "patch" in solution_metadata:
            raise BuildError(f"{instance_id}: solution metadata boundary drift")
        if json.loads(
            (raw_case_dir / "official/environment/runtime.json").read_text(
                encoding="utf-8"
            )
        ) != packet["environment_reference"]:
            raise BuildError(f"{instance_id}: runtime raw source drift")
        inventory_block = markdown.split("## Source Inventory\n\n", 1)[1].split(
            "\n\n## Packet Source Files", 1
        )[0]
        expected_inventory = "\n".join(f"- `{relative}`" for relative in RAW_CASE_FILES)
        if inventory_block != expected_inventory:
            raise BuildError(f"{instance_id}: markdown Source Inventory mismatch")

    case_dirs = [path for path in output_root.iterdir() if path.is_dir()]
    if len(case_dirs) != EXPECTED_CURRENT_TASK_COUNT:
        raise BuildError(
            f"Expected {EXPECTED_CURRENT_TASK_COUNT} case directories, found {len(case_dirs)}"
        )
    if total_bytes != index.get("generated_case_bytes"):
        raise BuildError("Generated byte total differs from index.json")
    return {
        "case_count": len(entries),
        "top_level_case_file_count": len(entries) * len(CASE_FILES),
        "raw_case_file_count": len(entries) * len(RAW_CASE_FILES),
        "case_file_count": len(entries) * (len(CASE_FILES) + len(RAW_CASE_FILES)),
        "case_bytes": total_bytes,
        "source_lock_sha256": sha256_file(lock_path),
        "index_sha256": sha256_file(index_path),
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help=f"Packet root (default: {DEFAULT_OUTPUT_ROOT})",
    )
    parser.add_argument(
        "--source-jsonl",
        type=Path,
        default=None,
        help=(
            "Optional saved pinned rows, one raw row or datasets-server row wrapper per line. "
            "Its canonical digest must match the locked 731-row digest."
        ),
    )
    parser.add_argument(
        "--max-fetch-workers",
        type=int,
        default=4,
        help="Concurrent Hugging Face rows requests (default: 4)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate an existing generated corpus without network access",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    output_root = args.output_root.resolve()
    if args.validate_only:
        summary = validate_generated(output_root)
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.max_fetch_workers < 1 or args.max_fetch_workers > 8:
        raise BuildError("--max-fetch-workers must be between 1 and 8")

    if args.source_jsonl is None:
        items = fetch_pinned_rows(args.max_fetch_workers)
    else:
        items = load_source_jsonl(args.source_jsonl.resolve())
    validate_source_rows(items)

    output_root.mkdir(parents=True, exist_ok=True)
    entries = [
        make_case(output_root=output_root, row_position=row_idx, row=row)
        for row_idx, row in items
    ]
    entries.sort(key=lambda entry: entry["row_idx"])
    write_root_artifacts(output_root, entries)
    summary = validate_generated(output_root)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BuildError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
