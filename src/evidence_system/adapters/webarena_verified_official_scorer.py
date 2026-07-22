"""Strict pinned-container scorer for WebArena-Verified v1.2.3.

The formal scoring lane runs only the official ``eval-tasks`` CLI from the
locked ServiceNow image digest.  It does not import or call the legacy
original-WebArena scorer.

For task ``N``, ``--output-root`` must already contain:

* ``N/agent_response.json``
* ``N/network.har`` (Playwright HAR recorded with ``mode=full`` and
  ``content=embed``)

The official CLI writes ``N/eval_result.json``.  That file is a protected,
controller-only artifact because it contains evaluator ``expected`` payloads.
The optional summary file and stdout contain only a sanitized result.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any


OFFICIAL_IMAGE = (
    "ghcr.io/servicenow/webarena-verified@"
    "sha256:d2c3f81b615648a806e0b9c9fd392085a45ca719ea773a51976b59d23f7bd1b9"
)
EXPECTED_PACKAGE_VERSION = "1.2.3"
EXPECTED_EVALUATOR_CHECKSUM = (
    "35c3385b1db4b3378657589f95f50defd4234bd36e5b93d44733fd561b01db4e"
)
EXPECTED_DATA_CHECKSUM = (
    "d65275660814663375028e9017e1f929e3c38321041b125795e2713b52243d30"
)
EXPECTED_RUNTIME_CONFIG_SHA256 = (
    "0b54e748bfed53d23852cb0d0f2b54b8a405b8e035b560ff86f3632e7c84f673"
)
EXPECTED_TASK_CONTRACT_INDEX_SHA256 = (
    "32b2eb76d2296286fae619f843e985feaf1b3eaf622d90d77133ffb580ab0d49"
)
EXPECTED_TASK_IDS = frozenset(range(812))
ALLOWED_EVALUATORS = frozenset({"AgentResponseEvaluator", "NetworkEventEvaluator"})
ALLOWED_RESULT_STATUSES = frozenset({"success", "failure", "error"})
TASK_CONTRACT_INDEX_SCHEMA_VERSION = "webarena_verified_task_contract_index/v1"
SUMMARY_SCHEMA_VERSION = "webarena_verified_official_eval_summary/v1"
DEFAULT_EVALUATOR_TIMEOUT_SECONDS = 600
DEFAULT_TASK_CONTRACT_INDEX = Path(
    "/opt/webarena-verified/v1.2.3/runtime/webarena_verified_task_contract_index.json"
)

_FULL_HAR_ENTRY_FIELDS = frozenset(
    {"startedDateTime", "time", "request", "response", "cache", "timings"}
)
_FULL_HAR_REQUEST_FIELDS = frozenset(
    {
        "method",
        "url",
        "httpVersion",
        "cookies",
        "headers",
        "queryString",
        "headersSize",
        "bodySize",
    }
)
_FULL_HAR_RESPONSE_FIELDS = frozenset(
    {
        "status",
        "statusText",
        "httpVersion",
        "cookies",
        "headers",
        "content",
        "redirectURL",
        "headersSize",
        "bodySize",
    }
)
_PRIVATE_RESULT_KEYS = frozenset(
    {"expected", "actual", "actual_normalized", "error_msg", "assertion_msgs"}
)


class ScorerIntegrityError(RuntimeError):
    """A locked artifact, official result, or required input failed validation."""


@dataclass(frozen=True)
class ScoreRequest:
    task_id: int
    task_revision: int
    output_root: Path
    runtime_config: Path
    summary_output: Path
    task_contract_index: Path = DEFAULT_TASK_CONTRACT_INDEX

    @property
    def task_dir(self) -> Path:
        return self.output_root / str(self.task_id)

    @property
    def agent_response(self) -> Path:
        return self.task_dir / "agent_response.json"

    @property
    def network_har(self) -> Path:
        return self.task_dir / "network.har"

    @property
    def eval_result(self) -> Path:
        return self.task_dir / "eval_result.json"

    @property
    def stdout_log(self) -> Path:
        return self.task_dir / "official_evaluator.stdout.log"

    @property
    def stderr_log(self) -> Path:
        return self.task_dir / "official_evaluator.stderr.log"


@dataclass(frozen=True)
class EvaluatorProcessResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class TaskContract:
    task_id: int
    task_revision: int
    evaluator_names_in_order: tuple[str, ...]
    index_sha256: str


@dataclass(frozen=True)
class ScoreOutcome:
    summary: dict[str, Any]
    exit_code: int


def score_task(request: ScoreRequest) -> ScoreOutcome:
    """Execute the pinned official CLI, validate its file, and sanitize metadata."""

    task_contract = _validate_request(request)
    # The image creates eval_result.json itself.  Protect the containing
    # directory before launch so the private file is never briefly world-readable.
    os.chmod(request.task_dir, 0o700)
    request.eval_result.unlink(
        missing_ok=True
    )  # A stale result must never satisfy this invocation.

    process = _run_pinned_evaluator(request)
    _atomic_write_text(request.stdout_log, process.stdout, mode=0o600)
    _atomic_write_text(request.stderr_log, process.stderr, mode=0o600)

    # Do not trust the process exit code.  A result is accepted only after the
    # official JSON itself passes all provenance and identity checks.
    if not request.eval_result.is_file():
        raise ScorerIntegrityError(
            "pinned official evaluator did not produce task eval_result.json"
        )
    os.chmod(request.eval_result, 0o600)
    full_result = _load_json_object(request.eval_result, label="official eval_result")
    _validate_official_result(
        full_result,
        task_id=request.task_id,
        task_revision=request.task_revision,
        task_contract=task_contract,
    )

    official_status = str(full_result["status"])
    wrapper_error = process.returncode != 0 or official_status == "error"
    summary = _sanitized_summary(
        full_result,
        request=request,
        process=process,
        wrapper_error=wrapper_error,
        task_contract=task_contract,
    )
    _assert_summary_is_sanitized(summary)
    _atomic_write_json(request.summary_output, summary, mode=0o644)
    return ScoreOutcome(summary=summary, exit_code=2 if wrapper_error else 0)


def _run_pinned_evaluator(request: ScoreRequest) -> EvaluatorProcessResult:
    command = _docker_command(request)
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=DEFAULT_EVALUATOR_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise ScorerIntegrityError("Docker executable is not available") from exc
    except subprocess.TimeoutExpired as exc:
        raise ScorerIntegrityError(
            "pinned official evaluator exceeded its timeout"
        ) from exc
    return EvaluatorProcessResult(
        command=command,
        returncode=int(completed.returncode),
        stdout=str(completed.stdout or ""),
        stderr=str(completed.stderr or ""),
    )


def _docker_command(request: ScoreRequest) -> tuple[str, ...]:
    output_root = request.output_root.resolve()
    runtime_config = request.runtime_config.resolve()
    return (
        "docker",
        "run",
        "--rm",
        "--pull=never",
        "--network=none",
        "--read-only",
        "--tmpfs=/tmp:rw,noexec,nosuid,size=64m",
        "--mount",
        f"type=bind,src={output_root},dst=/output",
        "--mount",
        f"type=bind,src={runtime_config},dst=/runtime-config.json,readonly",
        OFFICIAL_IMAGE,
        "eval-tasks",
        "--task-ids",
        str(request.task_id),
        "--output-dir",
        "/output",
        "--config",
        "/runtime-config.json",
    )


def _validate_request(request: ScoreRequest) -> TaskContract:
    if request.task_id not in EXPECTED_TASK_IDS:
        raise ScorerIntegrityError(
            "task ID must be in the official full-812 namespace 0..811"
        )
    if request.task_revision < 1:
        raise ScorerIntegrityError("task revision must be a positive integer")
    if not request.output_root.is_dir():
        raise ScorerIntegrityError("output root does not exist or is not a directory")
    if not request.task_dir.is_dir():
        raise ScorerIntegrityError("task directory does not exist")
    if not request.runtime_config.is_file():
        raise ScorerIntegrityError(
            "runtime config does not exist or is not a regular file"
        )
    if not request.task_contract_index.is_file():
        raise ScorerIntegrityError(
            "task contract index does not exist or is not a regular file"
        )
    if not request.agent_response.is_file():
        raise ScorerIntegrityError("task directory is missing agent_response.json")
    if not request.network_har.is_file():
        raise ScorerIntegrityError("task directory is missing network.har")
    if request.summary_output.resolve() in {
        request.agent_response.resolve(),
        request.network_har.resolve(),
        request.runtime_config.resolve(),
        request.task_contract_index.resolve(),
        request.eval_result.resolve(),
    }:
        raise ScorerIntegrityError(
            "summary output must not overwrite an evaluator input or official result"
        )

    task_contract = _load_task_contract(
        request.task_contract_index, task_id=request.task_id
    )
    _require_equal(
        "request task revision against task contract",
        request.task_revision,
        task_contract.task_revision,
    )

    config = _load_json_object(request.runtime_config, label="runtime config")
    if (
        not isinstance(config.get("environments"), Mapping)
        or not config["environments"]
    ):
        raise ScorerIntegrityError("runtime config must define non-empty environments")
    if _sha256_file(request.runtime_config) != EXPECTED_RUNTIME_CONFIG_SHA256:
        raise ScorerIntegrityError(
            "runtime config does not match the frozen full-812 URL mapping"
        )

    agent_response = _load_json_object(request.agent_response, label="agent response")
    required_response_fields = {
        "task_type",
        "status",
        "retrieved_data",
        "error_details",
    }
    if set(agent_response) != required_response_fields:
        raise ScorerIntegrityError(
            "agent_response.json must contain exactly the official response fields"
        )
    if _mapping_contains_key(agent_response, frozenset({"expected", "eval"})):
        raise ScorerIntegrityError(
            "agent_response.json contains evaluator-private fields"
        )

    _validate_full_embedded_har(request.network_har)
    return task_contract


def _load_task_contract(path: Path, *, task_id: int) -> TaskContract:
    try:
        raw_payload = path.read_bytes()
    except OSError as exc:
        raise ScorerIntegrityError(
            "task contract index is not a readable JSON file"
        ) from exc

    actual_sha256 = hashlib.sha256(raw_payload).hexdigest()
    _require_equal(
        "task contract index SHA-256",
        actual_sha256,
        EXPECTED_TASK_CONTRACT_INDEX_SHA256,
    )
    try:
        payload = json.loads(raw_payload.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ScorerIntegrityError(
            "task contract index is not a readable JSON file"
        ) from exc
    if not isinstance(payload, dict):
        raise ScorerIntegrityError("task contract index must contain a JSON object")

    _require_equal(
        "task contract index schema version",
        payload.get("schema_version"),
        TASK_CONTRACT_INDEX_SCHEMA_VERSION,
    )
    _require_equal(
        "task contract benchmark", payload.get("benchmark"), "WebArena-Verified"
    )
    _require_equal("task contract version", payload.get("version"), "v1.2.3")
    _require_equal("task contract split", payload.get("split"), "full")
    _require_equal(
        "task contract visibility", payload.get("visibility"), "controller_only"
    )
    _require_equal(
        "task contract task count", _required_contract_int(payload, "task_count"), 812
    )
    _require_equal(
        "task contract raw dataset SHA-256",
        payload.get("raw_tag_dataset_sha256"),
        EXPECTED_DATA_CHECKSUM,
    )

    entries = payload.get("entries")
    if not isinstance(entries, list) or len(entries) != len(EXPECTED_TASK_IDS):
        raise ScorerIntegrityError(
            "task contract index must contain exactly 812 entries"
        )

    by_task_id: dict[int, Mapping[str, Any]] = {}
    for position, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            raise ScorerIntegrityError(
                f"task contract entry {position} is not an object"
            )
        entry_task_id = _required_contract_int(entry, "task_id")
        if entry_task_id not in EXPECTED_TASK_IDS:
            raise ScorerIntegrityError(
                f"task contract entry has out-of-range task ID: {entry_task_id}"
            )
        if entry_task_id in by_task_id:
            raise ScorerIntegrityError(
                f"task contract index has duplicate task ID: {entry_task_id}"
            )
        by_task_id[entry_task_id] = entry

    if frozenset(by_task_id) != EXPECTED_TASK_IDS:
        raise ScorerIntegrityError(
            "task contract index does not cover the official task IDs 0..811 exactly"
        )

    entry = by_task_id[task_id]
    task_revision = _required_contract_int(entry, "task_revision")
    if task_revision < 1:
        raise ScorerIntegrityError("task contract revision must be a positive integer")
    evaluator_names = entry.get("evaluator_names_in_order")
    if not isinstance(evaluator_names, list) or not evaluator_names:
        raise ScorerIntegrityError(
            "task contract evaluator_names_in_order must be a non-empty array"
        )
    if any(
        not isinstance(name, str) or name not in ALLOWED_EVALUATORS
        for name in evaluator_names
    ):
        raise ScorerIntegrityError("task contract contains a non-v1.2.3 evaluator name")
    if evaluator_names[0] != "AgentResponseEvaluator":
        raise ScorerIntegrityError(
            "task contract evaluator list must start with AgentResponseEvaluator"
        )

    return TaskContract(
        task_id=task_id,
        task_revision=task_revision,
        evaluator_names_in_order=tuple(evaluator_names),
        index_sha256=actual_sha256,
    )


def _validate_full_embedded_har(path: Path) -> None:
    har = _load_json_object(path, label="network HAR")
    log = har.get("log")
    if not isinstance(log, Mapping) or str(log.get("version")) != "1.2":
        raise ScorerIntegrityError("network.har must contain a HAR 1.2 log")
    creator = log.get("creator")
    if (
        not isinstance(creator, Mapping)
        or "playwright" not in str(creator.get("name", "")).lower()
    ):
        raise ScorerIntegrityError("network.har must be recorded by Playwright")
    entries = log.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ScorerIntegrityError("network.har must contain at least one entry")

    embedded_body_count = 0
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping) or not _FULL_HAR_ENTRY_FIELDS.issubset(entry):
            raise ScorerIntegrityError(
                f"network.har entry {index} is not Playwright full-mode HAR"
            )
        request = entry.get("request")
        response = entry.get("response")
        if not isinstance(request, Mapping) or not _FULL_HAR_REQUEST_FIELDS.issubset(
            request
        ):
            raise ScorerIntegrityError(
                f"network.har request {index} is not Playwright full-mode HAR"
            )
        if not isinstance(response, Mapping) or not _FULL_HAR_RESPONSE_FIELDS.issubset(
            response
        ):
            raise ScorerIntegrityError(
                f"network.har response {index} is not Playwright full-mode HAR"
            )
        content = response.get("content")
        if not isinstance(content, Mapping):
            raise ScorerIntegrityError(
                f"network.har response {index} has invalid content metadata"
            )
        if "_file" in content or "_sha1" in content:
            raise ScorerIntegrityError(
                "network.har references detached response bodies; content=embed is required"
            )
        if "text" in content:
            embedded_body_count += 1

    if embedded_body_count == 0:
        raise ScorerIntegrityError(
            "network.har has no embedded response body; content=embed is required"
        )


def _validate_official_result(
    result: Mapping[str, Any],
    *,
    task_id: int,
    task_revision: int,
    task_contract: TaskContract,
) -> None:
    _require_equal("task contract task ID", task_contract.task_id, task_id)
    _require_equal(
        "task contract task revision", task_contract.task_revision, task_revision
    )
    _require_equal("result task ID", _required_int(result, "task_id"), task_id)
    _require_equal(
        "result task revision", _required_int(result, "task_revision"), task_revision
    )
    _require_equal(
        "result package version",
        str(result.get("webarena_verified_version")),
        EXPECTED_PACKAGE_VERSION,
    )
    _require_equal(
        "result evaluator checksum",
        str(result.get("webarena_verified_evaluator_checksum")),
        EXPECTED_EVALUATOR_CHECKSUM,
    )
    _require_equal(
        "result data checksum",
        str(result.get("webarena_verified_data_checksum")),
        EXPECTED_DATA_CHECKSUM,
    )

    status = str(result.get("status"))
    if status not in ALLOWED_RESULT_STATUSES:
        raise ScorerIntegrityError(
            f"official result has unsupported status: {status!r}"
        )
    score = _validate_status_and_binary_score(
        status=status,
        score=result.get("score"),
        label="official task result",
    )

    evaluator_results = result.get("evaluators_results")
    if not isinstance(evaluator_results, list):
        raise ScorerIntegrityError(
            "official result evaluators_results must be an array"
        )
    if status != "error" and not evaluator_results:
        raise ScorerIntegrityError("non-error official result has no evaluator results")

    evaluator_names: list[str] = []
    evaluator_statuses: list[str] = []
    for position, evaluator_result in enumerate(evaluator_results):
        if not isinstance(evaluator_result, Mapping):
            raise ScorerIntegrityError(
                "official evaluator result entry is not an object"
            )
        evaluator_name = str(evaluator_result.get("evaluator_name"))
        if evaluator_name not in ALLOWED_EVALUATORS:
            raise ScorerIntegrityError(
                f"non-v1.2.3 evaluator result rejected: {evaluator_name!r}"
            )
        evaluator_names.append(evaluator_name)
        evaluator_status = str(evaluator_result.get("status"))
        if evaluator_status not in ALLOWED_RESULT_STATUSES:
            raise ScorerIntegrityError(
                f"official evaluator result {position} has unsupported status: {evaluator_status!r}"
            )
        _validate_status_and_binary_score(
            status=evaluator_status,
            score=evaluator_result.get("score"),
            label=f"official evaluator result {position}",
        )
        evaluator_statuses.append(evaluator_status)

    # A task-level evaluator exception can legitimately yield no individual
    # results.  Once any evaluator result exists, however, its ordered list
    # (including duplicate NetworkEventEvaluator entries) is contractual.
    if evaluator_results or status != "error":
        expected_names = list(task_contract.evaluator_names_in_order)
        if evaluator_names != expected_names:
            raise ScorerIntegrityError(
                "official evaluator ordered list mismatch: "
                f"expected {expected_names!r}, got {evaluator_names!r}"
            )

    if evaluator_statuses:
        derived_status = (
            "error"
            if "error" in evaluator_statuses
            else "success"
            if all(item_status == "success" for item_status in evaluator_statuses)
            else "failure"
        )
        if status != derived_status:
            raise ScorerIntegrityError(
                "official task status is inconsistent with per-evaluator statuses: "
                f"expected {derived_status!r}, got {status!r}"
            )

    # Keep the explicit local variable so binary task semantics are checked
    # before evaluator composition and cannot be weakened accidentally.
    del score


def _validate_status_and_binary_score(*, status: str, score: Any, label: str) -> float:
    if (
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or float(score) not in {0.0, 1.0}
    ):
        raise ScorerIntegrityError(f"{label} score must use native binary semantics")
    binary_score = float(score)
    expected_score = 1.0 if status == "success" else 0.0
    if binary_score != expected_score:
        raise ScorerIntegrityError(
            f"{label} status/score mismatch: status {status!r} requires score {expected_score:.1f}"
        )
    return binary_score


def _sanitized_summary(
    result: Mapping[str, Any],
    *,
    request: ScoreRequest,
    process: EvaluatorProcessResult,
    wrapper_error: bool,
    task_contract: TaskContract,
) -> dict[str, Any]:
    evaluator_summaries: list[dict[str, Any]] = []
    for item in list(result.get("evaluators_results") or []):
        assertions = item.get("assertions") if isinstance(item, Mapping) else None
        assertion_statuses = Counter(
            str(assertion.get("status"))
            for assertion in (assertions or [])
            if isinstance(assertion, Mapping)
        )
        evaluator_summaries.append(
            {
                "evaluator_name": str(item.get("evaluator_name")),
                "status": str(item.get("status")),
                "score": float(item.get("score", 0.0)),
                "assertion_count": len(assertions or []),
                "assertion_status_counts": dict(sorted(assertion_statuses.items())),
            }
        )

    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "scorer_status": "error" if wrapper_error else "success",
        "official_evaluation_completed": True,
        "integrity_verified": process.returncode == 0,
        "task_id": request.task_id,
        "task_revision": request.task_revision,
        "status": str(result["status"]),
        "score": float(result["score"]),
        "sites": [str(site) for site in list(result.get("sites") or [])],
        "evaluators": evaluator_summaries,
        "official_evaluator_image": OFFICIAL_IMAGE,
        "official_evaluator_command_kind": "pinned_docker_eval-tasks",
        "official_evaluator_exit_code": process.returncode,
        "webarena_verified_version": EXPECTED_PACKAGE_VERSION,
        "webarena_verified_evaluator_checksum": EXPECTED_EVALUATOR_CHECKSUM,
        "webarena_verified_data_checksum": EXPECTED_DATA_CHECKSUM,
        "task_contract_index_sha256": task_contract.index_sha256,
        "runtime_config_sha256": _sha256_file(request.runtime_config),
        "agent_response_sha256": _sha256_file(request.agent_response),
        "network_har_sha256": _sha256_file(request.network_har),
        "official_eval_result_sha256": _sha256_file(request.eval_result),
        "official_evaluator_stdout_sha256": _sha256_file(request.stdout_log),
        "official_evaluator_stderr_sha256": _sha256_file(request.stderr_log),
        "official_eval_result_is_controller_only": True,
        "summary_contains_private_evaluator_payload": False,
    }


def _error_summary(request: ScoreRequest, exc: Exception) -> dict[str, Any]:
    if isinstance(exc, ScorerIntegrityError):
        error_code = "integrity_check_failed"
        public_message = str(exc)
    else:
        error_code = "official_scorer_failed"
        public_message = (
            "official scoring failed before a validated result was produced"
        )
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "scorer_status": "error",
        "official_evaluation_completed": False,
        "integrity_verified": False,
        "task_id": request.task_id,
        "task_revision": request.task_revision,
        "status": "error",
        "score": 0.0,
        "evaluators": [],
        "official_evaluator_image": OFFICIAL_IMAGE,
        "task_contract_index_sha256": _optional_sha256_file(
            request.task_contract_index
        ),
        "error_code": error_code,
        "public_error_message": public_message,
        "summary_contains_private_evaluator_payload": False,
    }


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ScorerIntegrityError(f"{label} is not a readable JSON file") from exc
    if not isinstance(payload, dict):
        raise ScorerIntegrityError(f"{label} must contain a JSON object")
    return payload


def _assert_summary_is_sanitized(summary: Mapping[str, Any]) -> None:
    if _mapping_contains_key(summary, _PRIVATE_RESULT_KEYS):
        raise ScorerIntegrityError(
            "sanitized summary contains a private evaluator field"
        )


def _mapping_contains_key(value: Any, forbidden: frozenset[str]) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key).lower() in forbidden or _mapping_contains_key(item, forbidden)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_mapping_contains_key(item, forbidden) for item in value)
    return False


def _required_int(payload: Mapping[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScorerIntegrityError(f"official result {key} must be an integer")
    return value


def _required_contract_int(payload: Mapping[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScorerIntegrityError(f"task contract {key} must be an integer")
    return value


def _require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise ScorerIntegrityError(
            f"{label} mismatch: expected {expected!r}, got {actual!r}"
        )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _optional_sha256_file(path: Path) -> str | None:
    try:
        return _sha256_file(path) if path.is_file() else None
    except OSError:
        return None


def _atomic_write_json(path: Path, payload: Mapping[str, Any], *, mode: int) -> None:
    _atomic_write_text(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        mode=mode,
    )


def _atomic_write_text(path: Path, text: str, *, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, mode)
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def _default_summary_path(request_output_root: Path, task_id: int) -> Path:
    return request_output_root / str(task_id) / "eval_summary.json"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True, type=int)
    parser.add_argument("--task-revision", required=True, type=int)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path, dest="runtime_config")
    parser.add_argument(
        "--task-contract-index",
        type=Path,
        default=DEFAULT_TASK_CONTRACT_INDEX,
        help=(
            "controller-only full-812 task contract index "
            f"(default: {DEFAULT_TASK_CONTRACT_INDEX})"
        ),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        help="sanitized summary JSON (default: <output-root>/<task-id>/eval_summary.json)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    output_root = Path(args.output_root)
    request = ScoreRequest(
        task_id=int(args.task_id),
        task_revision=int(args.task_revision),
        output_root=output_root,
        runtime_config=Path(args.runtime_config),
        task_contract_index=Path(args.task_contract_index),
        summary_output=(
            Path(args.summary_output)
            if args.summary_output
            else _default_summary_path(output_root, int(args.task_id))
        ),
    )

    try:
        outcome = score_task(request)
    except Exception as exc:  # Always emit a sanitized, non-zero controller receipt.
        summary = _error_summary(request, exc)
        try:
            _assert_summary_is_sanitized(summary)
            _atomic_write_json(request.summary_output, summary, mode=0o644)
        except Exception:
            pass
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    print(json.dumps(outcome.summary, ensure_ascii=False, indent=2, sort_keys=True))
    return outcome.exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
