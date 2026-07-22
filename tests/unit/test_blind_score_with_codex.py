from __future__ import annotations

import json
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from neurips_ed_track_minimal.scripts import (
    score_evidence_blind_with_codex as subject,
)


def checklist(*, stronger_ids: tuple[str, ...] = ()) -> dict:
    return {
        "schema_version": "case_checklist_v1",
        "case_unit_id": "case_1",
        "domain": "appworld",
        "task_id": "case_1",
        "native": {
            "success_if": [
                {"text": "[appworld_test_001_aaaa] passes"},
                {"text": "[appworld_test_002_bbbb] passes"},
            ],
            "fail_if": [
                {"text": "[appworld_test_001_aaaa] fails"},
                {"text": "[appworld_test_002_bbbb] fails"},
            ],
            "undecided_if": [{"text": "missing decisive evidence"}],
        },
        "stronger": {
            "additional_conditions": [
                {"id": condition_id, "text": condition_id}
                for condition_id in stronger_ids
            ]
        },
    }


def check(check_id: str, status: str, pointer: str) -> dict:
    return {
        "id": check_id,
        "status": status,
        "reason": "decided from retained evidence",
        "pointers": [pointer],
    }


def test_registered_test_specs_require_exact_matched_markers() -> None:
    specs = subject.extract_registered_test_specs(checklist())
    assert [spec.test_id for spec in specs] == [
        "appworld_test_001_aaaa",
        "appworld_test_002_bbbb",
    ]

    malformed = checklist()
    malformed["native"]["fail_if"][1]["text"] = "no marker"
    with pytest.raises(subject.BlindScoreError, match="exactly one"):
        subject.extract_registered_test_specs(malformed)


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        (("supported", "supported"), "S"),
        (("supported", "undecided"), "U"),
        (("undecided", "contradicted"), "F"),
    ],
)
def test_native_aggregate_is_strictly_derived(
    statuses: tuple[str, str], expected: str
) -> None:
    checks = [
        check("appworld_test_001_aaaa", statuses[0], "evidence/state.json::a"),
        check("appworld_test_002_bbbb", statuses[1], "evidence/state.json::b"),
    ]
    assert subject.derive_native_result(checks)["verdict"] == expected


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        ((), "NA"),
        (("supported", "supported"), "S"),
        (("supported", "undecided"), "U"),
        (("undecided", "contradicted"), "F"),
    ],
)
def test_stronger_aggregate_is_independent_and_strictly_derived(
    statuses: tuple[str, ...], expected: str
) -> None:
    checks = [
        check(f"condition_{index}", status, f"evidence/state.json::c{index}")
        for index, status in enumerate(statuses)
    ]
    assert subject.derive_stronger_result(checks)["verdict"] == expected


def test_blind_layout_rejects_task_label_and_component_outputs(tmp_path: Path) -> None:
    task = tmp_path / "task"
    evidence = task / "evidence"
    evidence.mkdir(parents=True)
    (evidence / "state.json").write_text("{}\n", encoding="utf-8")
    (task / "native_label.json").write_text('{"value":"success"}\n')
    with pytest.raises(subject.BlindScoreError, match="task root"):
        subject.assert_blind_input_layout(evidence)

    (task / "native_label.json").unlink()
    (evidence / "native_evaluator_output.json").write_text("{}\n")
    with pytest.raises(subject.BlindScoreError, match="component-evaluator-result"):
        subject.assert_blind_input_layout(evidence)


def test_staged_permissions_canary_normalizes_copy2_modes(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    evidence = workspace / "evidence"
    evidence.mkdir(parents=True)
    for path in (
        workspace / "checklist.yaml",
        workspace / "evidence_index.txt",
        workspace / "output_schema.json",
        evidence / "state.json",
    ):
        path.write_text("{}\n", encoding="utf-8")
        path.chmod(0o600)

    subject.normalize_staged_permissions(workspace)
    subject.validate_staged_readability_canary(workspace)
    assert stat.S_IMODE(workspace.stat().st_mode) == 0o555
    assert stat.S_IMODE((evidence / "state.json").stat().st_mode) == 0o444

    subject.restore_workspace_permissions_for_cleanup(workspace)
    assert stat.S_IMODE(workspace.stat().st_mode) == 0o755


def test_frozen_stage_is_published_only_when_explicitly_materialized(
    tmp_path: Path,
) -> None:
    isolated = tmp_path / "isolated"
    isolated.mkdir()
    source_prefix = isolated / "score"
    required_names = (
        "score.native.model_output.json",
        "score.native.codex.stdout.log",
        "score.native.codex.stderr.log",
        "score.native.codex.events.jsonl",
        "score.native.codex.telemetry.json",
        "score.native.codex.reasoning.txt",
    )
    for name in required_names:
        (isolated / name).write_text("{}\n", encoding="utf-8")
    frozen = subject.freeze_stage_artifacts(source_prefix)

    final_prefix = tmp_path / "final" / "score"
    final_prefix.parent.mkdir()
    assert not any(final_prefix.parent.iterdir())
    artifacts = subject.materialize_stage_artifacts(
        frozen,
        out_prefix=final_prefix,
        stage="native",
    )
    assert artifacts.model_output.is_file()
    assert json.loads(artifacts.model_output.read_text()) == {}


def test_stage_lock_paths_are_portable_relative_to_score_dir(tmp_path: Path) -> None:
    score_dir = tmp_path / "outputs" / "task"
    score_dir.mkdir(parents=True)
    stage_score = score_dir / "score.native.blind.json"
    stage_score.write_text("{}\n")
    checklist_path = tmp_path / "tasks" / "task" / "checklist.yaml"
    evidence = checklist_path.parent / "evidence"
    evidence.mkdir(parents=True)
    checklist_path.write_text("{}\n")
    prompt = tmp_path / "prompt.md"
    schema = score_dir / "score.native.output_schema.json"
    prompt.write_text("prompt\n")
    schema.write_text("{}\n")

    lock = subject.build_stage_lock(
        stage="native",
        stage_score_path=stage_score,
        checklist_path=checklist_path,
        evidence_dir=evidence,
        evidence_tree_sha256="a" * 64,
        prompt_path=prompt,
        schema_path=schema,
        model="gpt-5.4",
        reasoning_effort="high",
        service_tier="default",
        restricted_identity=subject.RestrictedIdentity(
            username="score-blind",
            uid=1234,
            groupname="score-blind",
            gid=1234,
        ),
    )
    assert lock["stage_score"]["path"] == "score.native.blind.json"
    assert not Path(lock["checklist"]["path"]).is_absolute()
    assert not Path(lock["evidence"]["path"]).is_absolute()


def test_pointer_validator_accepts_frozen_appworld_pointer_spellings(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    evidence = workspace / "evidence"
    run_evidence = evidence / "run"
    run_evidence.mkdir(parents=True)
    (run_evidence / "data.json").write_text(
        json.dumps({"items": [{"value": 1}]}) + "\n", encoding="utf-8"
    )
    (run_evidence / "trace.jsonl").write_text(
        '{"event": 1}\n{"event": 2}\n', encoding="utf-8"
    )
    (run_evidence / "evaluation.py").write_text(
        "def evaluate():\n    return True\n", encoding="utf-8"
    )
    frozen = checklist(stronger_ids=("condition_0",))
    frozen["stronger"]["additional_conditions"][0]["support"] = []
    subject._validate_check_pointers(
        check={
            "pointers": [
                "checklist.yaml::stronger.additional_conditions[0]",
                "evidence/run/data.json::$",
                "evidence/run/data.json::$.items[0].value",
                "evidence/run/trace.jsonl::L2",
                "evidence/run/evaluation.py::evaluate",
            ]
        },
        expected_rule="checklist.yaml::stronger.additional_conditions[0]",
        checklist=frozen,
        workspace_root=workspace,
        field="stronger.condition_checks[0]",
    )


def test_pointer_validator_accepts_checklist_jsonpath_rule_spelling(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    run = workspace / "evidence" / "run"
    run.mkdir(parents=True)
    (run / "state.json").write_text('{"ok":true}\n', encoding="utf-8")
    subject._validate_check_pointers(
        check={
            "pointers": [
                "checklist.yaml::$.native.success_if[0]",
                "evidence/run/state.json::$.ok",
            ]
        },
        expected_rule="checklist.yaml::native.success_if[0]",
        checklist=checklist(),
        workspace_root=workspace,
        field="native.test_checks[0]",
    )


def test_pointer_validator_rejects_criterion_sources_without_postrun_evidence(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    official = workspace / "evidence" / "official"
    official.mkdir(parents=True)
    (official / "criterion.json").write_text('{"rule":true}\n', encoding="utf-8")
    with pytest.raises(subject.BlindScoreError, match="post-run execution evidence"):
        subject._validate_check_pointers(
            check={
                "pointers": [
                    "checklist.yaml::stronger.additional_conditions[0]",
                    "evidence/official/criterion.json::$.rule",
                ]
            },
            expected_rule="checklist.yaml::stronger.additional_conditions[0]",
            checklist=checklist(stronger_ids=("condition_0",)),
            workspace_root=workspace,
            field="stronger.condition_checks[0]",
        )


@pytest.mark.parametrize(
    "index_pointer",
    (
        "evidence/index.json::$",
        "evidence/index.json::$.files[0]",
        "evidence/evidence_index.txt::L1",
        "evidence_index.txt::L1",
        "evidence/./index.json::$",
        "evidence//index.json::$",
        "evidence/run/../index.json::$",
        "evidence/raw_run.json::$.native_label",
    ),
)
def test_pointer_validator_rejects_navigation_only_indexes(
    tmp_path: Path,
    index_pointer: str,
) -> None:
    workspace = tmp_path / "workspace"
    evidence = workspace / "evidence"
    evidence.mkdir(parents=True)
    (evidence / "index.json").write_text("{}\n", encoding="utf-8")
    (evidence / "evidence_index.txt").write_text("index\n", encoding="utf-8")
    (workspace / "evidence_index.txt").write_text("index\n", encoding="utf-8")

    with pytest.raises(
        subject.BlindScoreError,
        match="(?:forbidden result/helper artifact|non-canonical path)",
    ):
        subject._validate_check_pointers(
            check={
                "pointers": [
                    "checklist.yaml::stronger.additional_conditions[0]",
                    index_pointer,
                ]
            },
            expected_rule="checklist.yaml::stronger.additional_conditions[0]",
            checklist=checklist(stronger_ids=("condition_0",)),
            workspace_root=workspace,
            field="stronger.condition_checks[0]",
        )


def test_agent_id_supports_double_underscore_task_names() -> None:
    assert subject.infer_agent_id("7847649_1__agent_a") == "agent_a"
    assert subject.infer_agent_id("full-appworld-7847649_1-agent_b") == "agent_b"


def test_restricted_codex_command_contains_exactly_one_exec(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(subject.shutil, "which", lambda _: "/usr/local/bin/codex")

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subject.subprocess, "run", fake_run)
    workspace = tmp_path / "workspace"
    codex_home = workspace / ".codex_home"
    stage_tmp = workspace / ".tmp"
    for directory in (workspace, codex_home, stage_tmp):
        directory.mkdir(exist_ok=True)
    schema = workspace / "schema.json"
    schema.write_text("{}\n")
    subject.run_codex_restricted(
        identity=subject.RestrictedIdentity("score-blind", 1234, "score-blind", 1234),
        workspace_root=workspace,
        schema_path=schema,
        prompt="score",
        model="gpt-5.4",
        reasoning_effort="high",
        service_tier="default",
        sandbox="read-only",
        out_json_path=workspace / "model_output.json",
        stage_codex_home=codex_home,
        stage_tmp=stage_tmp,
        codex_timeout_seconds=600,
    )
    command = captured["command"]
    assert isinstance(command, list)
    assert command[:2] == ["/usr/local/bin/codex", "exec"]
    assert command.count("exec") == 1
