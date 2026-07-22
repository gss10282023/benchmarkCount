from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from jsonschema import Draft202012Validator
import pytest

from evidence_system.contracts import agentdojo_full_experiment as freeze
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_file, sha256_object
from neurips_ed_track_minimal.scripts import update_case_locks_batch as batch


ROOT = Path(__file__).resolve().parents[2]
CANARY_ROOT = ROOT / "experiments/agentdojo_full_v1.2.2_direct/drafts/_canary_drafts"
CANARY_PROVENANCE = (
    ROOT / "experiments/agentdojo_full_v1.2.2_direct/drafts/_canary_provenance"
)
SLACK_DIRECTORY = "v1.2.2_slack_user_task_0_injection_task_1"
CANARY_RUN_ID = "20260716T041300174224Z"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _resolve(value: str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else ROOT / path).resolve()


def _canary_config() -> tuple[dict[str, Any], dict[str, Path], datetime]:
    config = _load_json(CANARY_PROVENANCE / "draft_review_config.json")
    paths = {
        "composed_draft_prompt": _resolve(
            config["generation"]["composed_prompt"]["path"]
        ),
        "checklist_schema": _resolve(config["generation"]["checklist_schema"]["path"]),
        "draft_supplement": _resolve(config["generation"]["prompt_supplement"]["path"]),
        "review_prompt": _resolve(config["review"]["prompt"]["path"]),
        "review_schema": _resolve(config["review"]["schema"]["path"]),
    }
    input_lock = _load_json(CANARY_PROVENANCE / "draft_input_lock.json")
    input_lock_time = freeze._parse_aware_timestamp(input_lock["locked_at"], "lock")
    return config, paths, input_lock_time


def _slack_review_kwargs(lifecycle: dict[str, Any]) -> dict[str, Any]:
    config, config_paths, input_lock_time = _canary_config()
    case_dir = (CANARY_ROOT / SLACK_DIRECTORY).resolve()
    case_unit_id = "v1.2.2:slack:user_task_0:injection_task_1"
    task_id = "slack:user_task_0:injection_task_1"
    packet_path = (
        ROOT
        / "experiments/agentdojo_full_v1.2.2_direct/case_packets/agentdojo"
        / SLACK_DIRECTORY
        / "case_packet.md"
    ).resolve()
    packet = batch.PacketCase(
        batch.ManifestCase("agentdojo", case_unit_id, task_id),
        packet_path,
        packet_path.parent / "raw_case_manifest.json",
    )
    return {
        "case": SimpleNamespace(case_unit_id=case_unit_id, task_id=task_id),
        "packet": packet,
        "case_dir": case_dir,
        "generated_checklist_path": case_dir / "generated_checklist.yaml",
        "final_checklist_path": case_dir / "checklist.yaml",
        "review_receipt": _load_json(case_dir / "review.json"),
        "lifecycle": lifecycle,
        "report_run_id": CANARY_RUN_ID,
        "config": config,
        "config_paths": config_paths,
        "review_schema": _load_json(config_paths["review_schema"]),
        "checklist_validator": Draft202012Validator(
            _load_json(config_paths["checklist_schema"])
        ),
        "input_lock_time": input_lock_time,
        "response_ids": set(),
    }


def test_actual_canary_revision_requires_fresh_second_review() -> None:
    lifecycle = _load_json(CANARY_ROOT / SLACK_DIRECTORY / "review_lifecycle.json")
    component = freeze._validate_review_case_provenance(
        **_slack_review_kwargs(lifecycle)
    )

    assert component["revised"] is True
    assert component["review_rounds"] == 2
    assert (
        component["generated_checklist_sha256"] != component["final_checklist_sha256"]
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda value: value.__setitem__("revised", False), "revised flag"),
        (
            lambda value: value["attempts"][1].__setitem__(
                "input_checklist_sha256", "0" * 64
            ),
            "input checklist hash",
        ),
        (
            lambda value: value["attempts"][0].__setitem__("decision", "accept"),
            "decision",
        ),
        (
            lambda value: value["attempts"][0].__setitem__(
                "model_review_sha256", "0" * 64
            ),
            "model review hash",
        ),
    ],
)
def test_actual_canary_revision_chain_tampering_is_rejected(
    mutation: Any, message: str
) -> None:
    lifecycle = _load_json(CANARY_ROOT / SLACK_DIRECTORY / "review_lifecycle.json")
    mutation(lifecycle)

    with pytest.raises(ContractLifecycleError, match=message):
        freeze._validate_review_case_provenance(**_slack_review_kwargs(lifecycle))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _synthetic_generation(tmp_path: Path) -> dict[str, Any]:
    case_unit_id = "v1.2.2:workspace:user_task_0:injection_task_0"
    task_id = "workspace:user_task_0:injection_task_0"
    case_dir = tmp_path / "case"
    case_dir.mkdir(parents=True)
    packet_path = tmp_path / "packet" / "case_packet.md"
    packet_path.parent.mkdir()
    packet_path.write_text("packet\n", encoding="utf-8")
    raw_manifest = packet_path.parent / "raw_case_manifest.json"
    _write_json(raw_manifest, {})
    checklist = {
        "schema_version": "case_checklist_v1",
        "case_unit_id": case_unit_id,
        "domain": "agentdojo",
        "task_id": task_id,
        "native": {},
        "stronger": {},
    }
    body = {"native": {}, "stronger": {}}
    attempt_prefix = case_dir / "attempt_01"
    attempt_yaml = attempt_prefix.with_suffix(".checklist.yaml")
    attempt_yaml.write_text(
        "schema_version: case_checklist_v1\n"
        f"case_unit_id: {case_unit_id}\n"
        "domain: agentdojo\n"
        f"task_id: {task_id}\n"
        "native: {}\nstronger: {}\n",
        encoding="utf-8",
    )
    attempt_json = attempt_prefix.with_suffix(".checklist.json")
    _write_json(attempt_json, checklist)
    response_id = "fresh-generation-thread"
    workspace = tmp_path / "ephemeral-workspace"
    command = [
        "codex",
        "exec",
        "--cd",
        str(workspace),
        "--skip-git-repo-check",
        "--ephemeral",
        "--ignore-user-config",
        "--sandbox",
        "read-only",
        "--model",
        "gpt-5.6-sol",
        "-c",
        'model_reasoning_effort="xhigh"',
        "-c",
        'model_verbosity="low"',
        "--color",
        "never",
        "--json",
        "--output-schema",
        str(workspace / "output_schema.json"),
        "-o",
        str(workspace / "draft_body.json"),
        "-",
    ]
    usage = {
        "input_tokens": 10,
        "output_tokens": 5,
        "total_tokens": 15,
        "input_tokens_details": {"cached_tokens": 2},
        "output_tokens_details": {"reasoning_tokens": 3},
    }
    api_path = attempt_prefix.with_suffix(".api_response.json")
    reasoning_path = attempt_prefix.with_suffix(".reasoning_summary.txt")
    reasoning_path.write_text("", encoding="utf-8")
    api_response = {
        "id": response_id,
        "status": "completed",
        "model": "gpt-5.6-sol",
        "provider": "codex_cli",
        "output_text": json.dumps(body),
        "output": [
            {"type": "reasoning", "summary": []},
            {
                "type": "message",
                "content": [{"type": "output_text", "text": json.dumps(body)}],
            },
        ],
        "usage": usage,
        "codex_cli": {
            "auth_mode": "codex_login",
            "returncode": 0,
            "timeout_seconds": 1800,
            "sandbox": "read-only",
            "command": command,
            "events": [{"type": "thread.started", "thread_id": response_id}],
            "malformed_event_lines": [],
            "stderr": "",
        },
    }
    _write_json(api_path, api_response)
    llm_path = attempt_prefix.with_suffix(".llm_call.json")
    llm_call = {
        "schema_version": "llm_call/v1",
        "provider": "codex_cli",
        "model": "gpt-5.6-sol",
        "model_version": "gpt-5.6-sol",
        "api_key_env": "CODEX_HOME",
        "domain": "agentdojo",
        "case_unit_id": case_unit_id,
        "task_id": task_id,
        "phase": "draft",
        "experiment_type": "minimal_package",
        "agent_id_or_role": "case_checklist_drafter",
        "request_timestamp": "2026-07-16T00:01:00+00:00",
        "response_timestamp": "2026-07-16T00:02:00+00:00",
        "temperature": 0.0,
        "max_tokens": 12000,
        "timeout_seconds": 1800,
        "retry_index": 0,
        "token_usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "cached_prompt_tokens": 2,
            "reasoning_tokens": 3,
            "total_tokens": 15,
        },
        "response_metadata": {
            "response_id": response_id,
            "response_status": "completed",
            "provider_model": "gpt-5.6-sol",
            "reasoning_effort": "xhigh",
            "raw_api_response_path": str(api_path),
            "reasoning_summary_path": str(reasoning_path),
            "auth_mode": "codex_login",
            "max_output_tokens_enforced": False,
        },
    }
    _write_json(llm_path, llm_call)
    promoted = {
        "generated_checklist": case_dir / "generated_checklist.yaml",
        "generated_checklist_json": case_dir / "generated_checklist.json",
        "api_response": case_dir / "api_response.json",
        "llm_call": case_dir / "llm_call.json",
        "reasoning_summary": case_dir / "reasoning_summary.txt",
    }
    for target, source in (
        (promoted["generated_checklist"], attempt_yaml),
        (promoted["generated_checklist_json"], attempt_json),
        (promoted["api_response"], api_path),
        (promoted["llm_call"], llm_path),
        (promoted["reasoning_summary"], reasoning_path),
    ):
        target.write_bytes(source.read_bytes())
    canonical = case_dir / "checklist.yaml"
    canonical.write_bytes(attempt_yaml.read_bytes())
    prompt = tmp_path / "prompt.md"
    schema = tmp_path / "schema.json"
    supplement = tmp_path / "supplement.md"
    prompt.write_text("prompt\n", encoding="utf-8")
    schema.write_text("{}\n", encoding="utf-8")
    supplement.write_text("supplement\n", encoding="utf-8")
    return {
        "kwargs": {
            "case": SimpleNamespace(case_unit_id=case_unit_id, task_id=task_id),
            "packet": batch.PacketCase(
                batch.ManifestCase("agentdojo", case_unit_id, task_id),
                packet_path.resolve(),
                raw_manifest.resolve(),
            ),
            "case_dir": case_dir.resolve(),
            "paths": {key: path.resolve() for key, path in promoted.items()},
            "batch_result": {
                "case_unit_dir": case_dir.name,
                "case_packet": str(packet_path.resolve()),
                "case_packet_size_bytes": packet_path.stat().st_size,
                "status": "success",
                "attempts": [
                    {
                        "attempt_index": 1,
                        "max_output_tokens": 12000,
                        "codex_timeout_seconds": 1800,
                        "returncode": 0,
                        "validator": f"checklist valid: {attempt_yaml.resolve()}",
                    }
                ],
                "checklist_path": str(canonical.resolve()),
            },
            "config": {
                "generation": {
                    "model": "gpt-5.6-sol",
                    "reasoning_effort": "xhigh",
                    "timeout_seconds": 1800,
                    "token_budgets": [12000, 16000, 20000, 24000],
                }
            },
            "config_paths": {
                "composed_draft_prompt": prompt.resolve(),
                "checklist_schema": schema.resolve(),
                "draft_supplement": supplement.resolve(),
            },
            "input_lock_time": datetime(2026, 7, 16, tzinfo=timezone.utc),
            "response_ids": set(),
        },
        "api_path": api_path,
        "canonical_api_path": promoted["api_response"],
    }


def test_generation_api_body_is_reconstructed_and_bound(tmp_path: Path) -> None:
    fixture = _synthetic_generation(tmp_path)
    component = freeze._validate_generation_case_provenance(**fixture["kwargs"])
    assert component["response_id"] == "fresh-generation-thread"

    tampered = _load_json(fixture["api_path"])
    tampered["output_text"] = json.dumps({"native": {"forged": True}, "stronger": {}})
    _write_json(fixture["api_path"], tampered)
    fixture["canonical_api_path"].write_bytes(fixture["api_path"].read_bytes())
    fixture["kwargs"]["response_ids"] = set()
    with pytest.raises(ContractLifecycleError, match="API body/checklist binding"):
        freeze._validate_generation_case_provenance(**fixture["kwargs"])


def test_production_namespace_roots_are_additive_and_fixed(tmp_path: Path) -> None:
    extra = tmp_path / "extra-score-root"
    normalized = freeze._production_snapshot_overrides({"score_result_roots": (extra,)})
    assert normalized["result_namespace_root"] == (
        freeze.DEFAULT_RESULT_NAMESPACE_LOCK.parent.resolve()
    )
    assert normalized["score_result_roots"] == freeze._deduplicated_resolved_paths(
        (*freeze.DEFAULT_SCORE_NAMESPACE_ROOTS, extra)
    )

    with pytest.raises(ContractLifecycleError, match="cannot be overridden"):
        freeze._production_snapshot_overrides(
            {"result_namespace_root": tmp_path / "shadow-results"}
        )


def test_publish_rechecks_empty_outputs_but_post_freeze_currentness_allows_results(
    tmp_path: Path,
) -> None:
    result_root = tmp_path / "results"
    result_root.mkdir()
    marker = result_root / "NAMESPACE_LOCK.json"
    _write_json(
        marker,
        {
            "result_namespace": freeze.RESULT_NAMESPACE,
            "legacy_result_root_must_not_be_modified": True,
        },
    )
    score_root = tmp_path / "scores"
    result_snapshot = freeze._empty_output_snapshot(
        result_root,
        label="formal result namespace",
        allowed_files=("NAMESPACE_LOCK.json",),
    )
    score_snapshot = freeze._empty_output_snapshot(
        score_root, label="formal scoring namespace[0]"
    )
    precondition = {
        "result_namespace": result_snapshot,
        "score_namespaces": [score_snapshot],
        "formal_results_and_scores_are_empty": True,
    }
    snapshot = {
        "schema_version": freeze.CHECKLIST_FREEZE_SCHEMA_VERSION,
        "expected_count": 1,
        "counts": {
            "case_packets": 1,
            "source_entries": 1,
            "valid_drafts": 1,
            "reviewed": 1,
            "locked": 1,
            "unresolved_drafts": 0,
        },
        "formal_output_precondition": precondition,
    }

    (result_root / "formal.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ContractLifecycleError, match="not empty before freeze"):
        freeze.publish_checklist_freeze_lock(
            snapshot=snapshot,
            base_definition={"result_namespace": freeze.RESULT_NAMESPACE},
            output_path=tmp_path / "experiment_lock.json",
        )

    freeze._validate_frozen_formal_output_precondition(
        precondition,
        result_namespace_root=result_root.resolve(),
        score_result_roots=(score_root,),
    )
    marker.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ContractLifecycleError, match="marker hash"):
        freeze._validate_frozen_formal_output_precondition(
            precondition,
            result_namespace_root=result_root.resolve(),
            score_result_roots=(score_root,),
        )


def test_generation_sidecar_hashes_are_current(tmp_path: Path) -> None:
    fixture = _synthetic_generation(tmp_path)
    component = freeze._validate_generation_case_provenance(**fixture["kwargs"])
    assert component["attempt_api_response_sha256"] == sha256_file(fixture["api_path"])
    fixture["api_path"].write_text("{}\n", encoding="utf-8")
    fixture["kwargs"]["response_ids"] = set()
    with pytest.raises(
        ContractLifecycleError, match="promoted generation api_response"
    ):
        freeze._validate_generation_case_provenance(**fixture["kwargs"])


def test_generation_call_must_be_fresh_and_have_bound_response_id(
    tmp_path: Path,
) -> None:
    fixture = _synthetic_generation(tmp_path)
    llm_path = fixture["api_path"].with_name("attempt_01.llm_call.json")
    canonical_llm = fixture["kwargs"]["paths"]["llm_call"]
    llm_call = _load_json(llm_path)
    llm_call["request_timestamp"] = "2026-07-15T23:59:00+00:00"
    _write_json(llm_path, llm_call)
    canonical_llm.write_bytes(llm_path.read_bytes())
    with pytest.raises(ContractLifecycleError, match="predates or equals"):
        freeze._validate_generation_case_provenance(**fixture["kwargs"])

    fixture = _synthetic_generation(tmp_path / "response-id")
    llm_path = fixture["api_path"].with_name("attempt_01.llm_call.json")
    canonical_llm = fixture["kwargs"]["paths"]["llm_call"]
    llm_call = _load_json(llm_path)
    llm_call["response_metadata"]["response_id"] = "forged-response-id"
    _write_json(llm_path, llm_call)
    canonical_llm.write_bytes(llm_path.read_bytes())
    with pytest.raises(ContractLifecycleError, match="metadata.response_id"):
        freeze._validate_generation_case_provenance(**fixture["kwargs"])


def test_verify_lock_is_post_output_safe_but_still_checks_immutable_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result_root = tmp_path / "results"
    result_root.mkdir()
    marker = result_root / "NAMESPACE_LOCK.json"
    _write_json(
        marker,
        {
            "result_namespace": freeze.RESULT_NAMESPACE,
            "legacy_result_root_must_not_be_modified": True,
        },
    )
    score_root = tmp_path / "scores"
    precondition = {
        "result_namespace": freeze._empty_output_snapshot(
            result_root,
            label="formal result namespace",
            allowed_files=("NAMESPACE_LOCK.json",),
        ),
        "score_namespaces": [
            freeze._empty_output_snapshot(
                score_root, label="formal scoring namespace[0]"
            )
        ],
        "formal_results_and_scores_are_empty": True,
    }
    locked_snapshot = {"formal_output_precondition": precondition}
    base_definition = {"result_namespace": freeze.RESULT_NAMESPACE}
    definition = {
        **base_definition,
        "lock_revision": "checklist-freeze-v1",
        "checklist_freeze": locked_snapshot,
    }
    lock = {
        "schema_version": freeze.CHECKLIST_FREEZE_LOCK_SCHEMA_VERSION,
        "lock_id": freeze.RESULT_NAMESPACE,
        "lock_status": "locked",
        "locked_at": "2026-07-16T00:00:00+00:00",
        **definition,
        "definition_sha256": sha256_object(definition),
    }
    lock_path = tmp_path / "experiment_lock.json"
    _write_json(lock_path, lock)

    monkeypatch.setattr(
        freeze,
        "_production_snapshot_overrides",
        lambda overrides: dict(overrides),
    )
    monkeypatch.setattr(
        freeze, "_build_experiment_definition", lambda **_: base_definition
    )

    def recompute(**kwargs: Any) -> dict[str, Any]:
        assert kwargs["require_empty_formal_outputs"] is False
        freeze._validate_frozen_formal_output_precondition(
            kwargs["frozen_formal_output_precondition"],
            result_namespace_root=result_root.resolve(),
            score_result_roots=(score_root,),
        )
        return locked_snapshot

    monkeypatch.setattr(freeze, "build_checklist_freeze_snapshot", recompute)
    (result_root / "formal.json").write_text("{}\n", encoding="utf-8")
    score_root.mkdir()
    (score_root / "score.json").write_text("{}\n", encoding="utf-8")

    verified = freeze.verify_checklist_freeze_lock(
        lock_path=lock_path,
        result_namespace_root=result_root,
        score_result_roots=(score_root,),
    )
    assert verified.lock_path == lock_path.resolve()

    marker.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ContractLifecycleError, match="marker hash"):
        freeze.verify_checklist_freeze_lock(
            lock_path=lock_path,
            result_namespace_root=result_root,
            score_result_roots=(score_root,),
        )
