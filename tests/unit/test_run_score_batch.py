from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from neurips_ed_track_minimal.scripts import run_score_batch as subject
from neurips_ed_track_minimal.scripts import score_evidence_blind_with_codex as blind_scorer


REPO_ROOT = Path(__file__).resolve().parents[2]
VALID_CHECKLIST = (
    REPO_ROOT
    / "neurips_ed_track_minimal"
    / "examples"
    / "agentdojo_banking_user_task_0_injection_task_2.checklist.yaml"
)


def write_task(task_root: Path, task_id: str = "case_1_agent_a") -> Path:
    task_dir = task_root / task_id
    evidence_dir = task_dir / "evidence"
    evidence_dir.mkdir(parents=True)
    shutil.copy2(VALID_CHECKLIST, task_dir / "checklist.yaml")
    (evidence_dir / "released_evaluator_label.json").write_text(
        json.dumps({"value": "success"}),
        encoding="utf-8",
    )
    (evidence_dir / "post_state.json").write_text(
        json.dumps({"status": "completed"}),
        encoding="utf-8",
    )
    return task_dir


def blind_checklist() -> dict:
    return {
        "case_unit_id": "case_1",
        "domain": "appworld",
        "task_id": "case_1",
        "native": {
            "success_if": [{"text": "[appworld_test_001_aaaa] passes"}],
            "fail_if": [{"text": "[appworld_test_001_aaaa] fails"}],
            "undecided_if": [{"text": "missing evidence"}],
        },
        "stronger": {"additional_conditions": []},
    }


def write_blind_task(task_root: Path, task_id: str = "case_1__agent_a") -> Path:
    task_dir = task_root / task_id
    evidence_dir = task_dir / "evidence"
    evidence_dir.mkdir(parents=True)
    (task_dir / "checklist.yaml").write_text("placeholder: true\n", encoding="utf-8")
    (evidence_dir / "post_state.json").write_text(
        json.dumps({"status": "completed"}), encoding="utf-8"
    )
    return task_dir


def test_discover_tasks_validates_generic_layout(tmp_path: Path) -> None:
    task_root = tmp_path / "tasks"
    write_task(task_root)

    tasks, stats = subject.discover_tasks(
        task_root,
        max_files=100,
        max_bytes=1_000_000,
        max_single_file_bytes=1_000_000,
    )

    assert len(tasks) == 1
    assert tasks[0].task_id == "case_1_agent_a"
    assert tasks[0].checklist_sha256
    assert tasks[0].evidence_tree_sha256
    assert stats["file_count"] == 3


def test_discover_tasks_rejects_symlinks(tmp_path: Path) -> None:
    task_root = tmp_path / "tasks"
    task_dir = write_task(task_root)
    (task_dir / "evidence" / "linked.json").symlink_to(
        task_dir / "evidence" / "post_state.json"
    )

    with pytest.raises(subject.ScoreBatchError, match="symlinks"):
        subject.discover_tasks(
            task_root,
            max_files=100,
            max_bytes=1_000_000,
            max_single_file_bytes=1_000_000,
        )


def test_blind_discovery_never_resolves_released_label(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_root = tmp_path / "tasks"
    write_blind_task(task_root)
    monkeypatch.setattr(subject, "validate_checklist", lambda _: blind_checklist())

    def unexpected_label_resolution(**_: object) -> None:
        raise AssertionError("blind discovery touched the released-label resolver")

    monkeypatch.setattr(
        subject.scorer,
        "resolve_released_evaluator_label",
        unexpected_label_resolution,
    )
    tasks, _ = subject.discover_tasks(
        task_root,
        max_files=100,
        max_bytes=1_000_000,
        max_single_file_bytes=1_000_000,
        blind_mode=True,
    )
    assert len(tasks) == 1
    assert tasks[0].native_label_path is None


def test_blind_discovery_fails_on_task_root_native_label(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_root = tmp_path / "tasks"
    task_dir = write_blind_task(task_root)
    (task_dir / "native_label.json").write_text('{"value":"success"}\n')
    monkeypatch.setattr(subject, "validate_checklist", lambda _: blind_checklist())
    with pytest.raises(subject.ScoreBatchError, match="forbids native_label"):
        subject.discover_tasks(
            task_root,
            max_files=100,
            max_bytes=1_000_000,
            max_single_file_bytes=1_000_000,
            blind_mode=True,
        )


def test_run_task_uses_isolated_codex_home_and_fixed_score_settings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_root = tmp_path / "tasks"
    write_task(task_root)
    tasks, _ = subject.discover_tasks(
        task_root,
        max_files=100,
        max_bytes=1_000_000,
        max_single_file_bytes=1_000_000,
    )
    task = tasks[0]
    source_codex_home = tmp_path / "source_codex_home"
    source_codex_home.mkdir()
    (source_codex_home / "auth.json").write_text("{}\n", encoding="utf-8")
    isolated_root = tmp_path / "isolated_codex_homes"
    monkeypatch.setenv("SCORE_CODEX_HOME_ROOT", str(isolated_root))
    captured: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        captured["command"] = command
        captured["env"] = kwargs["env"]
        out_prefix = Path(command[command.index("--out-prefix") + 1])
        out_prefix.parent.mkdir(parents=True, exist_ok=True)
        out_prefix.with_suffix(".json").write_text("{}\n", encoding="utf-8")
        out_prefix.with_suffix(".yaml").write_text("{}\n", encoding="utf-8")
        subject.scorer.manifest_output_path(out_prefix).write_text(
            "{}\n", encoding="utf-8"
        )
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subject.subprocess, "run", fake_run)
    result = subject.run_task(
        task,
        output_root=tmp_path / "outputs",
        source_codex_home=source_codex_home,
        model="gpt-5.6-sol",
        reasoning_effort="max",
        sandbox="read-only",
        service_tier="default",
        max_attempts=2,
        codex_timeout_seconds=1800,
        max_run_attempts=2,
    )

    command = captured["command"]
    assert isinstance(command, list)
    assert result["status"] == "success"
    assert command[command.index("--model") + 1] == "gpt-5.6-sol"
    assert command[command.index("--reasoning-effort") + 1] == "max"
    assert command[command.index("--sandbox") + 1] == "read-only"
    child_env = captured["env"]
    assert isinstance(child_env, dict)
    assert Path(child_env["CODEX_HOME"]).parent == isolated_root
    assert not any(isolated_root.iterdir())


def test_blind_run_task_uses_login_only_env_and_two_stage_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_root = tmp_path / "tasks"
    write_blind_task(task_root)
    monkeypatch.setattr(subject, "validate_checklist", lambda _: blind_checklist())
    tasks, _ = subject.discover_tasks(
        task_root,
        max_files=100,
        max_bytes=1_000_000,
        max_single_file_bytes=1_000_000,
        blind_mode=True,
    )
    source_codex_home = tmp_path / "source_codex_home"
    source_codex_home.mkdir()
    (source_codex_home / "auth.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-reach-child")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://must-not-reach-child")
    captured: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        captured["command"] = command
        captured["env"] = kwargs["env"]
        captured["timeout"] = kwargs["timeout"]
        out_prefix = Path(command[command.index("--out-prefix") + 1])
        out_prefix.parent.mkdir(parents=True, exist_ok=True)
        out_prefix.with_suffix(".json").write_text("{}\n")
        out_prefix.with_suffix(".yaml").write_text("{}\n")
        subject.scorer.manifest_output_path(out_prefix).write_text("{}\n")
        blind_scorer.blind_lock_output_path(out_prefix).write_text("{}\n")
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subject.subprocess, "run", fake_run)
    forbidden = (task_root, tmp_path / "outputs", tmp_path / "state")
    result = subject.run_task(
        tasks[0],
        output_root=forbidden[1],
        source_codex_home=source_codex_home,
        model="gpt-5.4",
        reasoning_effort="high",
        sandbox="read-only",
        service_tier="default",
        max_attempts=2,
        codex_timeout_seconds=1800,
        max_run_attempts=1,
        blind_mode=True,
        blind_forbidden_roots=forbidden,
    )
    assert result["status"] == "success"
    command = captured["command"]
    assert isinstance(command, list)
    assert command[1].endswith("score_evidence_blind_with_codex.py")
    assert "--native-label-path" not in command
    child_env = captured["env"]
    assert isinstance(child_env, dict)
    assert "OPENAI_API_KEY" not in child_env
    assert "OPENAI_BASE_URL" not in child_env
    assert child_env[blind_scorer.BLIND_CODEX_LOGIN_MARKER_ENV] == "1"
    assert child_env[blind_scorer.BLIND_FORBIDDEN_ROOTS_ENV]
    assert captured["timeout"] == (1800 * 2 * 2) + 300


def test_main_dry_run_preflights_without_codex_auth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    task_root = tmp_path / "tasks"
    write_task(task_root)
    output_root = tmp_path / "outputs"
    state_root = tmp_path / "state"
    monkeypatch.delenv("CODEX_HOME", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_score_batch.py",
            "--task-root",
            str(task_root),
            "--output-root",
            str(output_root),
            "--state-root",
            str(state_root),
            "--dry-run",
            "--min-free-bytes",
            "1",
        ],
    )

    assert subject.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "dry_run_ok"
    assert payload["task_count"] == 1
    assert payload["model"] == "gpt-5.4"
    assert payload["reasoning_effort"] == "xhigh"
    assert not output_root.exists()
    assert not state_root.exists()


def test_claude_batch_is_explicit_and_defaults_to_sonnet_high(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    task_root = tmp_path / "tasks"
    write_task(task_root)
    output_root = tmp_path / "outputs"
    state_root = tmp_path / "state"
    monkeypatch.delenv("CODEX_HOME", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_score_batch.py",
            "--task-root",
            str(task_root),
            "--output-root",
            str(output_root),
            "--state-root",
            str(state_root),
            "--scorer",
            "claude-code",
            "--dry-run",
            "--min-free-bytes",
            "1",
        ],
    )

    assert subject.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["scorer"] == "claude-code"
    assert payload["model"] == "sonnet"
    assert payload["reasoning_effort"] == "high"
    assert not output_root.exists()
    assert not state_root.exists()


def test_run_task_uses_claude_login_environment_without_codex_home_copy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_root = tmp_path / "tasks"
    write_task(task_root)
    tasks, _ = subject.discover_tasks(
        task_root,
        max_files=100,
        max_bytes=1_000_000,
        max_single_file_bytes=1_000_000,
    )
    captured: dict[str, object] = {}
    monkeypatch.setenv("CODEX_HOME", "/unchanged/codex/home")

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        captured["command"] = command
        captured["env"] = kwargs["env"]
        out_prefix = Path(command[command.index("--out-prefix") + 1])
        out_prefix.parent.mkdir(parents=True, exist_ok=True)
        out_prefix.with_suffix(".json").write_text("{}\n", encoding="utf-8")
        out_prefix.with_suffix(".yaml").write_text("{}\n", encoding="utf-8")
        subject.scorer.manifest_output_path(out_prefix).write_text(
            "{}\n", encoding="utf-8"
        )
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subject.subprocess, "run", fake_run)
    result = subject.run_task(
        tasks[0],
        output_root=tmp_path / "outputs",
        source_codex_home=None,
        model="sonnet",
        reasoning_effort="high",
        sandbox="read-only",
        service_tier="default",
        max_attempts=2,
        codex_timeout_seconds=1800,
        max_run_attempts=2,
        scorer_name="claude-code",
        claude_timeout_seconds=900,
    )

    command = captured["command"]
    assert isinstance(command, list)
    assert result["status"] == "success"
    assert command[1].endswith("score_evidence_with_claude.py")
    assert command[command.index("--model") + 1] == "sonnet"
    assert command[command.index("--reasoning-effort") + 1] == "high"
    assert command[command.index("--claude-timeout-seconds") + 1] == "900"
    assert "--sandbox" not in command
    child_env = captured["env"]
    assert isinstance(child_env, dict)
    assert child_env["CODEX_HOME"] == "/unchanged/codex/home"
