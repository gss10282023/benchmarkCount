from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
import os
from pathlib import Path

import pytest

from evidence_system.adapters import webarena_verified_official_scorer as scorer


PRIVATE_EXPECTED_VALUE = "PRIVATE_EXPECTED_DO_NOT_EXPOSE"
ROOT = Path(__file__).resolve().parents[2]
TASK_CONTRACT_INDEX = (
    ROOT
    / "experiments"
    / "case_packets"
    / "webarena_verified"
    / "task_contract_index.json"
)


def _evaluator_result(
    evaluator_name: str,
    *,
    status: str = "success",
    score: float | int | bool | None = None,
) -> dict:
    if score is None:
        score = 1.0 if status == "success" else 0.0
    return {
        "evaluator_name": evaluator_name,
        "status": status,
        "score": score,
        "actual": {"retrieved_data": ["public answer"]},
        "actual_normalized": ["public answer"],
        "expected": {"retrieved_data": [PRIVATE_EXPECTED_VALUE]},
        "assertions": [{"assertion_name": "matches", "status": status}],
        "error_msg": "private evaluator diagnostic" if status == "error" else None,
    }


def _official_result(
    *,
    task_id: int = 44,
    task_revision: int = 2,
    status: str = "success",
    score: float | int | bool | None = None,
    evaluators: list[dict] | None = None,
) -> dict:
    if score is None:
        score = 1.0 if status == "success" else 0.0
    if evaluators is None:
        evaluators = (
            []
            if status == "error"
            else [
                _evaluator_result("AgentResponseEvaluator"),
                _evaluator_result("NetworkEventEvaluator"),
            ]
        )
    return {
        "task_id": task_id,
        "intent_template_id": 10,
        "sites": ["gitlab"],
        "task_revision": task_revision,
        "status": status,
        "score": score,
        "evaluators_results": evaluators,
        "error_msg": "private evaluator diagnostic" if status == "error" else None,
        "webarena_verified_version": scorer.EXPECTED_PACKAGE_VERSION,
        "webarena_verified_evaluator_checksum": scorer.EXPECTED_EVALUATOR_CHECKSUM,
        "webarena_verified_data_checksum": scorer.EXPECTED_DATA_CHECKSUM,
    }


def _full_embedded_har() -> dict:
    return {
        "log": {
            "version": "1.2",
            "creator": {"name": "Playwright", "version": "1.56.0"},
            "entries": [
                {
                    "startedDateTime": "2026-07-16T00:00:00.000Z",
                    "time": 1,
                    "request": {
                        "method": "GET",
                        "url": "http://127.0.0.1:8023/dashboard/todos",
                        "httpVersion": "HTTP/1.1",
                        "cookies": [],
                        "headers": [{"name": "accept", "value": "text/html"}],
                        "queryString": [],
                        "headersSize": -1,
                        "bodySize": -1,
                    },
                    "response": {
                        "status": 200,
                        "statusText": "OK",
                        "httpVersion": "HTTP/1.1",
                        "cookies": [],
                        "headers": [],
                        "content": {
                            "size": 13,
                            "mimeType": "text/html",
                            "text": "<html></html>",
                        },
                        "redirectURL": "",
                        "headersSize": -1,
                        "bodySize": 13,
                    },
                    "cache": {},
                    "timings": {"send": 0, "wait": 1, "receive": 0},
                }
            ],
        }
    }


def _cli_args(
    tmp_path: Path,
    *,
    task_id: int = 44,
    task_revision: int = 2,
    task_contract_index: Path = TASK_CONTRACT_INDEX,
) -> tuple[list[str], Path, Path, Path]:
    output_root = tmp_path / "runs"
    task_dir = output_root / str(task_id)
    task_dir.mkdir(parents=True)
    (task_dir / "agent_response.json").write_text(
        json.dumps(
            {
                "task_type": "NAVIGATE",
                "status": "SUCCESS",
                "retrieved_data": None,
                "error_details": None,
            }
        ),
        encoding="utf-8",
    )
    (task_dir / "network.har").write_text(
        json.dumps(_full_embedded_har()), encoding="utf-8"
    )
    config = tmp_path / "runtime.json"
    config.write_bytes(
        (ROOT / "configs" / "webarena_verified_runtime_urls.json").read_bytes()
    )
    summary = tmp_path / "public" / "eval_summary.json"
    args = [
        "--task-id",
        str(task_id),
        "--task-revision",
        str(task_revision),
        "--output-root",
        str(output_root),
        "--config",
        str(config),
        "--task-contract-index",
        str(task_contract_index),
        "--summary-output",
        str(summary),
    ]
    return args, output_root, task_dir, summary


def _install_fake_container(
    monkeypatch: pytest.MonkeyPatch,
    task_dir: Path,
    *,
    result: dict | None = None,
    returncode: int = 0,
) -> list[scorer.ScoreRequest]:
    calls: list[scorer.ScoreRequest] = []

    def fake_run(request: scorer.ScoreRequest) -> scorer.EvaluatorProcessResult:
        calls.append(request)
        if result is not None:
            request.eval_result.write_text(json.dumps(result), encoding="utf-8")
        return scorer.EvaluatorProcessResult(
            command=scorer._docker_command(request),
            returncode=returncode,
            stdout="official stdout\n",
            stderr="official stderr\n" if returncode else "",
        )

    monkeypatch.setattr(scorer, "_run_pinned_evaluator", fake_run)
    return calls


def _contract(task_id: int = 44) -> scorer.TaskContract:
    return scorer._load_task_contract(TASK_CONTRACT_INDEX, task_id=task_id)


def _assert_result_rejected(result: dict, message: str, *, task_id: int = 44) -> None:
    contract = _contract(task_id)
    with pytest.raises(scorer.ScorerIntegrityError, match=message):
        scorer._validate_official_result(
            result,
            task_id=task_id,
            task_revision=contract.task_revision,
            task_contract=contract,
        )


def _write_modified_contract_index(
    path: Path,
    mutator: Callable[[dict], None],
) -> str:
    payload = json.loads(TASK_CONTRACT_INDEX.read_text(encoding="utf-8"))
    mutator(payload)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_cli_runs_pinned_official_result_and_exposes_only_sanitized_summary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args, _, task_dir, summary_path = _cli_args(tmp_path)
    calls = _install_fake_container(monkeypatch, task_dir, result=_official_result())

    assert scorer.main(args) == 0

    full_path = task_dir / "eval_result.json"
    full = json.loads(full_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    stdout = capsys.readouterr().out
    assert full["evaluators_results"][0]["expected"]["retrieved_data"] == [
        PRIVATE_EXPECTED_VALUE
    ]
    assert PRIVATE_EXPECTED_VALUE not in json.dumps(summary)
    assert PRIVATE_EXPECTED_VALUE not in stdout
    assert not scorer._mapping_contains_key(summary, scorer._PRIVATE_RESULT_KEYS)
    assert summary["status"] == "success"
    assert summary["scorer_status"] == "success"
    assert summary["official_evaluator_command_kind"] == "pinned_docker_eval-tasks"
    assert summary["official_evaluator_image"] == scorer.OFFICIAL_IMAGE
    assert (
        summary["task_contract_index_sha256"]
        == scorer.EXPECTED_TASK_CONTRACT_INDEX_SHA256
    )
    assert os.stat(task_dir).st_mode & 0o777 == 0o700
    assert os.stat(full_path).st_mode & 0o777 == 0o600
    assert len(calls) == 1
    assert calls[0].task_contract_index == TASK_CONTRACT_INDEX


def test_frozen_task_contract_index_hash_matches_controller_artifact() -> None:
    assert TASK_CONTRACT_INDEX.is_file()
    assert hashlib.sha256(TASK_CONTRACT_INDEX.read_bytes()).hexdigest() == (
        scorer.EXPECTED_TASK_CONTRACT_INDEX_SHA256
    )
    assert scorer.DEFAULT_TASK_CONTRACT_INDEX == Path(
        "/opt/webarena-verified/v1.2.3/runtime/webarena_verified_task_contract_index.json"
    )


def test_cli_defaults_to_controller_runtime_task_contract_index() -> None:
    args = scorer._build_parser().parse_args(
        [
            "--task-id",
            "44",
            "--task-revision",
            "2",
            "--output-root",
            "/tmp/output",
            "--config",
            "/tmp/runtime.json",
        ]
    )
    assert args.task_contract_index == scorer.DEFAULT_TASK_CONTRACT_INDEX


def test_docker_command_is_digest_pinned_offline_and_uses_fixed_task_files(
    tmp_path: Path,
) -> None:
    _, output_root, _, summary = _cli_args(tmp_path)
    request = scorer.ScoreRequest(
        task_id=44,
        task_revision=2,
        output_root=output_root,
        runtime_config=tmp_path / "runtime.json",
        summary_output=summary,
    )

    command = scorer._docker_command(request)

    assert command[0:3] == ("docker", "run", "--rm")
    assert "--pull=never" in command
    assert "--network=none" in command
    assert scorer.OFFICIAL_IMAGE in command
    assert command[command.index(scorer.OFFICIAL_IMAGE) + 1 :] == (
        "eval-tasks",
        "--task-ids",
        "44",
        "--output-dir",
        "/output",
        "--config",
        "/runtime-config.json",
    )
    assert "agent_response.json" not in command
    assert "network.har" not in command


def test_official_error_result_is_preserved_but_cli_returns_nonzero(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args, _, task_dir, summary_path = _cli_args(tmp_path)
    _install_fake_container(
        monkeypatch, task_dir, result=_official_result(status="error")
    )

    assert scorer.main(args) == 2

    assert (
        json.loads((task_dir / "eval_result.json").read_text(encoding="utf-8"))[
            "status"
        ]
        == "error"
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "error"
    assert summary["scorer_status"] == "error"
    assert "private evaluator diagnostic" not in summary_path.read_text(
        encoding="utf-8"
    )
    assert "private evaluator diagnostic" not in capsys.readouterr().out


def test_valid_failure_semantics_are_preserved_as_completed_evaluation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    args, _, task_dir, summary_path = _cli_args(tmp_path)
    result = _official_result(
        status="failure",
        evaluators=[
            _evaluator_result("AgentResponseEvaluator", status="failure"),
            _evaluator_result("NetworkEventEvaluator"),
        ],
    )
    _install_fake_container(monkeypatch, task_dir, result=result)

    assert scorer.main(args) == 0

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "failure"
    assert summary["score"] == 0.0
    assert summary["scorer_status"] == "success"


def test_accepts_task_error_derived_from_per_evaluator_error() -> None:
    contract = _contract()
    result = _official_result(
        status="error",
        evaluators=[
            _evaluator_result("AgentResponseEvaluator", status="error"),
            _evaluator_result("NetworkEventEvaluator"),
        ],
    )

    scorer._validate_official_result(
        result,
        task_id=44,
        task_revision=contract.task_revision,
        task_contract=contract,
    )


def test_nonzero_container_exit_is_not_accepted_even_with_valid_result(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    args, _, task_dir, summary_path = _cli_args(tmp_path)
    _install_fake_container(
        monkeypatch, task_dir, result=_official_result(), returncode=9
    )

    assert scorer.main(args) == 2

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "success"
    assert summary["scorer_status"] == "error"
    assert summary["integrity_verified"] is False
    assert summary["official_evaluator_exit_code"] == 9


def test_missing_result_is_error_even_when_container_exit_is_zero(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    args, _, task_dir, summary_path = _cli_args(tmp_path)
    _install_fake_container(monkeypatch, task_dir, result=None)

    assert scorer.main(args) == 2

    receipt = json.loads(summary_path.read_text(encoding="utf-8"))
    assert receipt["error_code"] == "integrity_check_failed"
    assert "did not produce" in receipt["public_error_message"]


def test_revision_mismatch_rejects_official_result(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    args, _, task_dir, summary_path = _cli_args(tmp_path)
    result = _official_result()
    result["task_revision"] = 1
    _install_fake_container(monkeypatch, task_dir, result=result)

    assert scorer.main(args) == 2

    receipt = json.loads(summary_path.read_text(encoding="utf-8"))
    assert receipt["error_code"] == "integrity_check_failed"
    assert "task revision mismatch" in receipt["public_error_message"]


@pytest.mark.parametrize(
    ("field", "bad_value", "message"),
    [
        ("webarena_verified_version", "1.2.2", "result package version mismatch"),
        (
            "webarena_verified_evaluator_checksum",
            "0" * 64,
            "result evaluator checksum mismatch",
        ),
        ("webarena_verified_data_checksum", "0" * 64, "result data checksum mismatch"),
    ],
)
def test_rejects_official_provenance_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    field: str,
    bad_value: str,
    message: str,
) -> None:
    args, _, task_dir, summary_path = _cli_args(tmp_path)
    result = _official_result()
    result[field] = bad_value
    _install_fake_container(monkeypatch, task_dir, result=result)

    assert scorer.main(args) == 2

    receipt = json.loads(summary_path.read_text(encoding="utf-8"))
    assert message in receipt["public_error_message"]


def test_rejects_legacy_or_unregistered_evaluator_result(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    args, _, task_dir, summary_path = _cli_args(tmp_path)
    _install_fake_container(
        monkeypatch,
        task_dir,
        result=_official_result(
            evaluators=[
                _evaluator_result("evaluation_harness.StringEvaluator"),
                _evaluator_result("NetworkEventEvaluator"),
            ]
        ),
    )

    assert scorer.main(args) == 2

    receipt = json.loads(summary_path.read_text(encoding="utf-8"))
    assert "non-v1.2.3 evaluator result rejected" in receipt["public_error_message"]


@pytest.mark.parametrize("bad_status", ["partial_match", "SUCCESS", "failed", ""])
def test_rejects_unsupported_task_status(bad_status: str) -> None:
    result = _official_result(status=bad_status, score=0.0)
    _assert_result_rejected(result, "official result has unsupported status")


@pytest.mark.parametrize(
    ("status", "score"),
    [
        ("success", 0.0),
        ("failure", 1.0),
        ("error", 1.0),
    ],
)
def test_rejects_task_status_score_mismatch(status: str, score: float) -> None:
    result = _official_result(status=status, score=score)
    _assert_result_rejected(result, "official task result status/score mismatch")


@pytest.mark.parametrize("score", [0.5, -1.0, 2.0, True, None, "1.0"])
def test_rejects_nonbinary_or_nonnumeric_task_score(score: object) -> None:
    result = _official_result()
    result["score"] = score
    _assert_result_rejected(
        result, "official task result score must use native binary semantics"
    )


@pytest.mark.parametrize("bad_status", ["partial_match", "SUCCESS", "failed", ""])
def test_rejects_unsupported_per_evaluator_status(bad_status: str) -> None:
    result = _official_result(
        evaluators=[
            _evaluator_result("AgentResponseEvaluator", status=bad_status, score=0.0),
            _evaluator_result("NetworkEventEvaluator"),
        ]
    )
    _assert_result_rejected(
        result, "official evaluator result 0 has unsupported status"
    )


@pytest.mark.parametrize(
    ("status", "score"),
    [
        ("success", 0.0),
        ("failure", 1.0),
        ("error", 1.0),
    ],
)
def test_rejects_per_evaluator_status_score_mismatch(status: str, score: float) -> None:
    result = _official_result(
        evaluators=[
            _evaluator_result("AgentResponseEvaluator", status=status, score=score),
            _evaluator_result("NetworkEventEvaluator"),
        ]
    )
    _assert_result_rejected(result, "official evaluator result 0 status/score mismatch")


@pytest.mark.parametrize("score", [0.5, -1.0, 2.0, True, None, "1.0"])
def test_rejects_nonbinary_or_nonnumeric_per_evaluator_score(score: object) -> None:
    evaluator = _evaluator_result("AgentResponseEvaluator")
    evaluator["score"] = score
    result = _official_result(
        evaluators=[
            evaluator,
            _evaluator_result("NetworkEventEvaluator"),
        ]
    )
    _assert_result_rejected(
        result, "official evaluator result 0 score must use native binary semantics"
    )


@pytest.mark.parametrize(
    "result",
    [
        _official_result(
            status="success",
            evaluators=[
                _evaluator_result("AgentResponseEvaluator", status="failure"),
                _evaluator_result("NetworkEventEvaluator"),
            ],
        ),
        _official_result(
            status="failure",
            evaluators=[
                _evaluator_result("AgentResponseEvaluator"),
                _evaluator_result("NetworkEventEvaluator"),
            ],
        ),
        _official_result(
            status="failure",
            evaluators=[
                _evaluator_result("AgentResponseEvaluator", status="error"),
                _evaluator_result("NetworkEventEvaluator"),
            ],
        ),
        _official_result(
            status="error",
            evaluators=[
                _evaluator_result("AgentResponseEvaluator"),
                _evaluator_result("NetworkEventEvaluator"),
            ],
        ),
    ],
)
def test_rejects_task_status_inconsistent_with_per_evaluator_results(
    result: dict,
) -> None:
    _assert_result_rejected(
        result, "task status is inconsistent with per-evaluator statuses"
    )


def test_rejects_evaluator_order_mismatch() -> None:
    result = _official_result(
        evaluators=[
            _evaluator_result("NetworkEventEvaluator"),
            _evaluator_result("AgentResponseEvaluator"),
        ]
    )
    _assert_result_rejected(result, "official evaluator ordered list mismatch")


def test_accepts_exact_ordered_duplicate_evaluator_contract() -> None:
    task_id = 102
    contract = _contract(task_id)
    result = _official_result(
        task_id=task_id,
        task_revision=contract.task_revision,
        evaluators=[
            _evaluator_result("AgentResponseEvaluator"),
            _evaluator_result("NetworkEventEvaluator"),
            _evaluator_result("NetworkEventEvaluator"),
        ],
    )

    scorer._validate_official_result(
        result,
        task_id=task_id,
        task_revision=contract.task_revision,
        task_contract=contract,
    )


def test_rejects_missing_duplicate_evaluator_from_ordered_contract() -> None:
    task_id = 102
    contract = _contract(task_id)
    result = _official_result(
        task_id=task_id,
        task_revision=contract.task_revision,
        evaluators=[
            _evaluator_result("AgentResponseEvaluator"),
            _evaluator_result("NetworkEventEvaluator"),
        ],
    )
    _assert_result_rejected(
        result, "official evaluator ordered list mismatch", task_id=task_id
    )


def test_contract_revision_mismatch_rejects_before_starting_container(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    args, _, task_dir, summary_path = _cli_args(tmp_path, task_revision=3)
    calls = _install_fake_container(monkeypatch, task_dir, result=_official_result())

    assert scorer.main(args) == 2

    receipt = json.loads(summary_path.read_text(encoding="utf-8"))
    assert (
        "request task revision against task contract mismatch"
        in receipt["public_error_message"]
    )
    assert (
        receipt["task_contract_index_sha256"]
        == scorer.EXPECTED_TASK_CONTRACT_INDEX_SHA256
    )
    assert calls == []


def test_contract_index_hash_mismatch_rejects_before_starting_container(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    altered_index = tmp_path / "altered-contract-index.json"
    altered_index.write_bytes(TASK_CONTRACT_INDEX.read_bytes() + b"\n")
    args, _, task_dir, summary_path = _cli_args(
        tmp_path, task_contract_index=altered_index
    )
    calls = _install_fake_container(monkeypatch, task_dir, result=_official_result())

    assert scorer.main(args) == 2

    receipt = json.loads(summary_path.read_text(encoding="utf-8"))
    assert "task contract index SHA-256 mismatch" in receipt["public_error_message"]
    assert (
        receipt["task_contract_index_sha256"]
        == hashlib.sha256(altered_index.read_bytes()).hexdigest()
    )
    assert calls == []


def test_contract_index_duplicate_task_id_rejected_when_injected_hash_is_trusted(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    altered_index = tmp_path / "duplicate-task-contract-index.json"

    def duplicate_task_id(payload: dict) -> None:
        payload["entries"][1]["task_id"] = payload["entries"][0]["task_id"]

    altered_hash = _write_modified_contract_index(altered_index, duplicate_task_id)
    monkeypatch.setattr(scorer, "EXPECTED_TASK_CONTRACT_INDEX_SHA256", altered_hash)
    args, _, task_dir, summary_path = _cli_args(
        tmp_path, task_contract_index=altered_index
    )
    calls = _install_fake_container(monkeypatch, task_dir, result=_official_result())

    assert scorer.main(args) == 2

    receipt = json.loads(summary_path.read_text(encoding="utf-8"))
    assert "duplicate task ID" in receipt["public_error_message"]
    assert calls == []


def test_rejects_attached_or_minimal_har_before_starting_container(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    args, _, task_dir, summary_path = _cli_args(tmp_path)
    har = _full_embedded_har()
    har["log"]["entries"][0]["response"]["content"] = {
        "size": 13,
        "mimeType": "text/html",
        "_file": "body.html",
    }
    (task_dir / "network.har").write_text(json.dumps(har), encoding="utf-8")
    calls = _install_fake_container(monkeypatch, task_dir, result=_official_result())

    assert scorer.main(args) == 2

    receipt = json.loads(summary_path.read_text(encoding="utf-8"))
    assert "content=embed is required" in receipt["public_error_message"]
    assert calls == []


def test_default_summary_path_is_inside_task_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    args, _, task_dir, explicit_summary = _cli_args(tmp_path)
    del args[args.index("--summary-output") :]
    _install_fake_container(monkeypatch, task_dir, result=_official_result())

    assert scorer.main(args) == 0

    assert (task_dir / "eval_summary.json").exists()
    assert not explicit_summary.exists()
