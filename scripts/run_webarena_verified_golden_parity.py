#!/usr/bin/env python3
"""Run strict raw-CLI versus adapter parity for WebArena-Verified v1.2.3.

The generated fixture inputs and full evaluator outputs are controller-only:
they are derived from the official task evaluator payload and must never be
placed in an agent prompt or a public artifact.  The public receipt contains
only identities, hashes, evaluator names/statuses, and parity decisions.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any, Mapping

from evidence_system.adapters import webarena_verified_official_scorer as scorer


SCHEMA_VERSION = "webarena_verified_golden_parity/v1"
FIXTURE_TASK_IDS = (0, 389, 97)
PRIVATE_KEYS = frozenset(
    {
        "expected",
        "actual",
        "actual_normalized",
        "error_msg",
        "assertion_msgs",
        "agent_response",
        "network_har",
    }
)


class GoldenParityError(RuntimeError):
    """A fixture, official invocation, or parity assertion failed."""


@dataclass(frozen=True)
class Fixture:
    fixture_id: str
    task_id: int
    category: str
    expected_status: str
    network_should_match: bool
    response_should_match: bool


FIXTURES = (
    Fixture("response_only_success", 0, "agent_response_only_retrieval", "success", True, True),
    Fixture("response_only_failure", 0, "agent_response_only_retrieval", "failure", True, False),
    Fixture("network_mutation_success", 389, "network_event_mutation", "success", True, True),
    Fixture("network_mutation_failure", 389, "network_event_mutation", "failure", False, True),
    Fixture("multisite_success", 97, "multi_site_network_event", "success", True, True),
    Fixture("multisite_failure", 97, "multi_site_network_event", "failure", False, True),
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-dataset", type=Path, required=True)
    parser.add_argument("--runtime-config", type=Path, required=True)
    parser.add_argument("--task-contract-index", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _atomic_json(path: Path, payload: Mapping[str, Any], *, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, mode)
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def _atomic_text(path: Path, value: str, *, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, mode)
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def _load_tasks(path: Path) -> dict[int, dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GoldenParityError("official dataset is not readable JSON") from exc
    if not isinstance(payload, list) or len(payload) != 812:
        raise GoldenParityError("official dataset must contain exactly 812 tasks")
    tasks: dict[int, dict[str, Any]] = {}
    for item in payload:
        if not isinstance(item, dict) or isinstance(item.get("task_id"), bool):
            raise GoldenParityError("official dataset contains an invalid task")
        task_id = int(item["task_id"])
        if task_id in tasks:
            raise GoldenParityError(f"duplicate official task ID: {task_id}")
        tasks[task_id] = item
    if set(tasks) != set(range(812)):
        raise GoldenParityError("official dataset task IDs must equal 0..811")
    return tasks


def _response(task: Mapping[str, Any], *, matches: bool) -> dict[str, Any]:
    evaluations = task.get("eval")
    if not isinstance(evaluations, list) or not evaluations:
        raise GoldenParityError("fixture task has no evaluator configuration")
    first = evaluations[0]
    expected = first.get("expected") if isinstance(first, Mapping) else None
    if not isinstance(expected, Mapping):
        raise GoldenParityError("fixture task has no AgentResponse expected object")
    upstream_required = {"task_type", "status", "retrieved_data"}
    if not upstream_required.issubset(expected) or not set(expected).issubset(
        upstream_required | {"error_details"}
    ):
        raise GoldenParityError("fixture AgentResponse fields differ from v1.2.3")
    response = {
        "task_type": str(expected["task_type"]).upper(),
        "status": str(expected["status"]).upper(),
        "retrieved_data": expected["retrieved_data"],
        "error_details": expected.get("error_details"),
    }
    if not matches:
        response["retrieved_data"] = ["__INTENTIONAL_GOLDEN_MISMATCH__"]
    return response


def _har_entry(
    *,
    method: str,
    url: str,
    query: list[tuple[str, str]] | None = None,
    post_json: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    request: dict[str, Any] = {
        "method": method,
        "url": url,
        "httpVersion": "HTTP/1.1",
        "cookies": [],
        "headers": [
            {"name": str(name), "value": str(value)}
            for name, value in sorted((headers or {"accept": "application/json"}).items())
        ],
        "queryString": [
            {"name": str(name), "value": str(value)} for name, value in (query or [])
        ],
        "headersSize": -1,
        "bodySize": -1,
    }
    if post_json is not None:
        text = json.dumps(post_json, separators=(",", ":"), sort_keys=True)
        request["postData"] = {
            "mimeType": "application/json",
            "text": text,
            "params": [],
        }
        request["bodySize"] = len(text.encode("utf-8"))
    return {
        "startedDateTime": "2026-07-16T00:00:00.000Z",
        "time": 1,
        "request": request,
        "response": {
            "status": 200,
            "statusText": "OK",
            "httpVersion": "HTTP/1.1",
            "cookies": [],
            "headers": [{"name": "content-type", "value": "application/json"}],
            "content": {
                "size": 2,
                "mimeType": "application/json",
                "text": "{}",
            },
            "redirectURL": "",
            "headersSize": -1,
            "bodySize": 2,
        },
        "cache": {},
        "timings": {"send": 0, "wait": 1, "receive": 0},
    }


def _network_entry(task_id: int, *, matches: bool) -> dict[str, Any]:
    if not matches:
        return _har_entry(
            method="GET",
            url="http://127.0.0.1:8023/__intentional_golden_network_miss__",
        )
    if task_id == 389:
        query = [("target_id", "139245"), ("target_type", "merge_request")]
        return _har_entry(
            method="POST",
            url=(
                "http://127.0.0.1:8023/primer/design/notes"
                "?target_id=139245&target_type=merge_request"
            ),
            query=query,
            post_json={
                "note": {
                    "noteable_type": "MergeRequest",
                    "note": "Thanks, working on reviews",
                }
            },
        )
    if task_id == 97:
        return _har_entry(
            method="GET",
            url=(
                "http://127.0.0.1:3030/routed-car/route/v1/driving/"
                "-79.9436,40.4433;-71.0936,42.3601?overview=false"
            ),
            query=[("overview", "false")],
        )
    if task_id == 0:
        return _har_entry(
            method="GET",
            url="http://127.0.0.1:7780/admin/dashboard/",
        )
    raise GoldenParityError(f"no golden network fixture for task {task_id}")


def _har(task_id: int, *, matches: bool) -> dict[str, Any]:
    return {
        "log": {
            "version": "1.2",
            "creator": {"name": "Playwright", "version": "1.56.0"},
            "entries": [_network_entry(task_id, matches=matches)],
        }
    }


def _prepare_root(
    root: Path,
    *,
    fixture: Fixture,
    task: Mapping[str, Any],
) -> Path:
    task_dir = root / str(fixture.task_id)
    task_dir.mkdir(parents=True, exist_ok=False)
    os.chmod(root, 0o700)
    os.chmod(task_dir, 0o700)
    _atomic_json(
        task_dir / "agent_response.json",
        _response(task, matches=fixture.response_should_match),
        mode=0o600,
    )
    _atomic_json(
        task_dir / "network.har",
        _har(fixture.task_id, matches=fixture.network_should_match),
        mode=0o600,
    )
    return task_dir


def _raw_command(*, output_root: Path, runtime_config: Path, task_id: int) -> tuple[str, ...]:
    return (
        "docker",
        "run",
        "--rm",
        "--pull=never",
        "--network=none",
        "--read-only",
        "--tmpfs=/tmp:rw,noexec,nosuid,size=64m",
        "--mount",
        f"type=bind,src={output_root.resolve()},dst=/output",
        "--mount",
        f"type=bind,src={runtime_config.resolve()},dst=/runtime-config.json,readonly",
        scorer.OFFICIAL_IMAGE,
        "eval-tasks",
        "--task-ids",
        str(task_id),
        "--output-dir",
        "/output",
        "--config",
        "/runtime-config.json",
    )


def _run_raw(*, root: Path, runtime_config: Path, task_id: int) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            _raw_command(output_root=root, runtime_config=runtime_config, task_id=task_id),
            check=False,
            capture_output=True,
            text=True,
            timeout=scorer.DEFAULT_EVALUATOR_TIMEOUT_SECONDS,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise GoldenParityError("raw official evaluator invocation failed") from exc


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GoldenParityError(f"missing or invalid JSON artifact: {path}") from exc
    if not isinstance(value, dict):
        raise GoldenParityError(f"JSON artifact is not an object: {path}")
    return value


def _private_key_present(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key).lower() in PRIVATE_KEYS or _private_key_present(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_private_key_present(item) for item in value)
    return False


def run(args: argparse.Namespace) -> dict[str, Any]:
    for path, label in (
        (args.official_dataset, "official dataset"),
        (args.runtime_config, "runtime config"),
        (args.task_contract_index, "task contract index"),
    ):
        if not path.is_file():
            raise GoldenParityError(f"{label} is missing: {path}")
    if _sha256(args.runtime_config) != scorer.EXPECTED_RUNTIME_CONFIG_SHA256:
        raise GoldenParityError("runtime config hash does not match scorer lock")
    if _sha256(args.task_contract_index) != scorer.EXPECTED_TASK_CONTRACT_INDEX_SHA256:
        raise GoldenParityError("task contract index hash does not match scorer lock")

    tasks = _load_tasks(args.official_dataset)
    if args.output_root.exists():
        shutil.rmtree(args.output_root)
    controller_root = args.output_root / "controller_only"
    controller_root.mkdir(parents=True)
    os.chmod(args.output_root, 0o700)
    os.chmod(controller_root, 0o700)

    results: list[dict[str, Any]] = []
    for fixture in FIXTURES:
        fixture_root = controller_root / fixture.fixture_id
        raw_root = fixture_root / "raw_cli"
        adapter_root = fixture_root / "adapter"
        raw_task_dir = _prepare_root(raw_root, fixture=fixture, task=tasks[fixture.task_id])
        adapter_task_dir = _prepare_root(
            adapter_root, fixture=fixture, task=tasks[fixture.task_id]
        )

        raw_process = _run_raw(
            root=raw_root,
            runtime_config=args.runtime_config,
            task_id=fixture.task_id,
        )
        _atomic_text(fixture_root / "raw_cli.stdout.log", raw_process.stdout, mode=0o600)
        _atomic_text(fixture_root / "raw_cli.stderr.log", raw_process.stderr, mode=0o600)
        raw_result_path = raw_task_dir / "eval_result.json"
        raw_result = _load_object(raw_result_path)

        adapter_summary_path = fixture_root / "adapter_summary.json"
        outcome = scorer.score_task(
            scorer.ScoreRequest(
                task_id=fixture.task_id,
                task_revision=int(tasks[fixture.task_id]["revision"]),
                output_root=adapter_root,
                runtime_config=args.runtime_config,
                summary_output=adapter_summary_path,
                task_contract_index=args.task_contract_index,
            )
        )
        adapter_result_path = adapter_task_dir / "eval_result.json"
        adapter_result = _load_object(adapter_result_path)
        exact_match = raw_result == adapter_result
        status = str(adapter_result.get("status"))
        if raw_process.returncode != 0:
            raise GoldenParityError(
                f"{fixture.fixture_id}: raw evaluator exited {raw_process.returncode}"
            )
        if outcome.exit_code != 0:
            raise GoldenParityError(
                f"{fixture.fixture_id}: adapter evaluator exited {outcome.exit_code}"
            )
        if not exact_match:
            raise GoldenParityError(f"{fixture.fixture_id}: full evaluator results differ")
        if status != fixture.expected_status:
            raise GoldenParityError(
                f"{fixture.fixture_id}: expected {fixture.expected_status}, got {status}"
            )

        evaluator_results = adapter_result.get("evaluators_results")
        if not isinstance(evaluator_results, list) or not evaluator_results:
            raise GoldenParityError(f"{fixture.fixture_id}: no evaluator results")
        results.append(
            {
                "fixture_id": fixture.fixture_id,
                "category": fixture.category,
                "task_id": fixture.task_id,
                "task_revision": int(tasks[fixture.task_id]["revision"]),
                "sites": list(tasks[fixture.task_id]["sites"]),
                "expected_status": fixture.expected_status,
                "actual_status": status,
                "score": float(adapter_result.get("score", 0.0)),
                "raw_cli_exit_code": raw_process.returncode,
                "adapter_exit_code": outcome.exit_code,
                "full_result_exact_match": exact_match,
                "evaluator_names": [str(item.get("evaluator_name")) for item in evaluator_results],
                "evaluator_statuses": [str(item.get("status")) for item in evaluator_results],
                "raw_result_sha256": _sha256(raw_result_path),
                "adapter_result_sha256": _sha256(adapter_result_path),
                "raw_canonical_result_sha256": _canonical_sha256(raw_result),
                "adapter_canonical_result_sha256": _canonical_sha256(adapter_result),
                "adapter_summary_sha256": _sha256(adapter_summary_path),
                "controller_artifacts_mode": "0700 directories / 0600 files",
            }
        )

    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass",
        "official_evaluator_image": scorer.OFFICIAL_IMAGE,
        "official_dataset_sha256": _sha256(args.official_dataset),
        "runtime_config_sha256": _sha256(args.runtime_config),
        "task_contract_index_sha256": _sha256(args.task_contract_index),
        "fixture_count": len(results),
        "raw_cli_adapter_exact_match_count": sum(
            bool(item["full_result_exact_match"]) for item in results
        ),
        "success_fixture_count": sum(
            item["actual_status"] == "success" for item in results
        ),
        "failure_fixture_count": sum(
            item["actual_status"] == "failure" for item in results
        ),
        "categories": sorted({str(item["category"]) for item in results}),
        "fixtures": results,
        "controller_only_root": "controller_only",
        "public_receipt_contains_private_evaluator_payload": False,
    }
    if _private_key_present(receipt):
        raise GoldenParityError("public receipt contains a controller-only field")
    _atomic_json(args.output_root / "acceptance.json", receipt, mode=0o644)
    return receipt


def main() -> int:
    args = _parser().parse_args()
    try:
        receipt = run(args)
    except Exception as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
