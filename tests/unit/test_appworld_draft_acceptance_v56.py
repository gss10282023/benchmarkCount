from __future__ import annotations

import json
from pathlib import Path

import pytest

from evidence_system.contracts import appworld_draft_acceptance_v56 as subject
from evidence_system.contracts.appworld_support_pointers import (
    support_location_resolves,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_bytes
from neurips_ed_track_minimal.scripts import run_draft_batch as runner


def _approved_env() -> dict[str, str]:
    return dict(subject._APPROVED_ENV_VALUES)


def _workspace_files() -> dict[str, str]:
    return {
        "draft_instructions.md": "instructions\n",
        "template.yaml": "template\n",
        "case_packet.md": "packet line 1\npacket line 2\n",
        "output_schema.json": "{}\n",
    }


def _command_event_pair(
    raw: str,
    *,
    output: str = "",
    terminal_status: str = "completed",
    exit_code: int = 0,
) -> list[dict[str, object]]:
    return [
        {"type": "item.started", "item": {"id": "item_0", "type": "command_execution", "command": raw, "aggregated_output": "", "status": "in_progress", "exit_code": None}},
        {"type": "item.completed", "item": {"id": "item_0", "type": "command_execution", "command": raw, "aggregated_output": output, "status": terminal_status, "exit_code": exit_code}},
    ]


def _read_plan_events(files: dict[str, str] | None = None) -> list[dict[str, object]]:
    selected = files or _workspace_files()
    events: list[dict[str, object]] = []
    for index, item in enumerate(subject.minimal_drafter.build_codex_read_plan(selected)):
        raw = f"/bin/zsh -lc {json.dumps(item['command'])}"
        pair = _command_event_pair(raw, output=str(item["expected_output"]))
        for event in pair:
            event["item"]["id"] = f"item_{index}"
        events.extend(pair)
    return events


def test_freeze_environment_accepts_only_known_macos_injection(monkeypatch: pytest.MonkeyPatch) -> None:
    environment = _approved_env()
    environment["__CF_USER_TEXT_ENCODING"] = "0x1F5:0x19:0x34"
    monkeypatch.setattr(subject.os, "environ", environment)
    # Avoid depending on host directories in this focused value-policy test.
    monkeypatch.setattr(subject.Path, "is_absolute", lambda self: True)
    monkeypatch.setattr(subject.Path, "is_dir", lambda self: True)
    monkeypatch.setattr(subject.Path, "is_symlink", lambda self: False)
    monkeypatch.setattr(subject.Path, "iterdir", lambda self: iter(()))

    frozen = subject._freeze_environment()

    assert frozen["explicit_variable_names"] == sorted(subject._ENV_ALLOWLIST)
    assert set(frozen["value_sha256_by_name"]) == set(subject._ENV_ALLOWLIST)
    assert "__CF_USER_TEXT_ENCODING" not in frozen["value_sha256_by_name"]
    assert frozen["platform_injected_variable"] == {
        "name": "__CF_USER_TEXT_ENCODING",
        "value_sha256": sha256_bytes(b"0x1F5:0x19:0x34"),
    }


@pytest.mark.parametrize(
    "mutation",
    [
        {"USER": "gss"},
        {"PATH": "/tmp/unapproved"},
        {"OPENAI_API_KEY": "sk-not-allowed"},
        {"__CF_USER_TEXT_ENCODING": "not-the-macos-format"},
    ],
)
def test_freeze_environment_rejects_extra_or_unapproved_values(
    monkeypatch: pytest.MonkeyPatch,
    mutation: dict[str, str],
) -> None:
    environment = _approved_env()
    environment.update(mutation)
    monkeypatch.setattr(subject.os, "environ", environment)
    with pytest.raises(ContractLifecycleError):
        subject._freeze_environment()


def test_builder_is_exclusive_and_freezes_8_by_8(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    materialization = tmp_path / "materialization"
    materialization.mkdir()
    draft_root = materialization / "draft_runs" / "draft"
    lock_path = draft_root / "provenance" / "draft_run_lock.json"
    cases_root = draft_root / "cases"
    packet_root = tmp_path / "packets"
    packet_root.mkdir()
    preflight = tmp_path / "preflight"

    monkeypatch.setattr(subject, "DEFAULT_DRAFT_ROOT", draft_root)
    monkeypatch.setattr(subject, "DEFAULT_CASES_ROOT", cases_root)
    monkeypatch.setattr(subject, "DEFAULT_ACCEPTED_CASES_ROOT", draft_root / "accepted_cases")
    monkeypatch.setattr(subject, "DEFAULT_CANARY_ACCEPTANCE_PATH", draft_root / "provenance" / "canary_acceptance.json")
    monkeypatch.setattr(subject, "DEFAULT_PREFLIGHT_ROOT", preflight)
    monkeypatch.setattr(subject, "_freeze_inputs", lambda root: ({"case_packet_root": str(root)}, [{"case_unit_id": str(index)} for index in range(485)]))
    monkeypatch.setattr(subject, "_failed_v2_snapshot_audit", lambda: {"status": "diagnostics_only", "reuse_prohibited": True})
    monkeypatch.setattr(
        subject,
        "_locked_canary_plan",
        lambda **kwargs: {
            "schema_version": "appworld_draft_canary_plan.v1",
            "round_ids": list(subject.EXPECTED_PREFLIGHT_ROUNDS),
        },
    )
    monkeypatch.setattr(subject, "_freeze_prompt", lambda: {"effective_composed_prompt_sha256": "a" * 64})
    monkeypatch.setattr(subject, "_live_runtime", lambda: {"codex_executable": "/tmp/codex", "codex_executable_sha256": "b" * 64})
    monkeypatch.setattr(subject, "_codex_login_status", lambda *args: "Logged in using ChatGPT")
    monkeypatch.setattr(subject, "_freeze_environment", lambda: {"policy": subject.ENVIRONMENT_POLICY})
    monkeypatch.setattr(subject, "_git_commit", lambda: "c" * 40)
    monkeypatch.setattr(subject, "_expected_batch_argv", lambda **kwargs: ["run", "--max-parallel", "8", "--large-max-parallel", "8"])

    result = subject.prepare_appworld_draft_run_lock_v56(
        lock_path=lock_path, cases_root=cases_root, case_packet_root=packet_root
    )
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    assert result["schema_version"] == "appworld_draft_run_lock.v5"
    assert lock["drafter"]["regular_max_parallel"] == 8
    assert lock["drafter"]["oversized_max_parallel"] == 8
    assert lock["drafter"]["requested_model_alias"] == "gpt-5.6-sol"
    assert lock["drafter"]["reasoning_effort"] == "xhigh"
    assert draft_root.parent.is_dir()
    with pytest.raises(ContractLifecycleError, match="already exists"):
        subject.prepare_appworld_draft_run_lock_v56(
            lock_path=lock_path, cases_root=cases_root, case_packet_root=packet_root
        )


def test_event_command_policy_rejects_environment_enumeration() -> None:
    events = _command_event_pair('/bin/zsh -lc "printenv"')
    with pytest.raises(ContractLifecycleError, match="read-only allowlist"):
        subject._validate_event_commands(
            events=events,
            workspace=Path("/private/tmp/case-checklist-codex-test"),
            case_id="case",
            expected_workspace_files=_workspace_files(),
        )


def test_event_command_policy_allows_temp_relative_reads() -> None:
    files = _workspace_files()
    audit = subject._validate_event_commands(
        events=_read_plan_events(files),
        workspace=Path("/private/tmp/case-checklist-codex-test"),
        case_id="case",
        expected_workspace_files=files,
    )
    assert audit["command_event_count"] == 8
    assert audit["command_invocation_count"] == 4
    assert set(audit["workspace_files"]) == set(files)


def test_event_command_policy_rejects_failed_only_command_pair() -> None:
    raw = '/bin/zsh -lc "sed -n \'1,1p\' case_packet.md"'
    with pytest.raises(ContractLifecycleError, match="pairing invalid"):
        subject._validate_event_commands(
            events=_command_event_pair(
                raw,
                terminal_status="failed",
                exit_code=1,
            ),
            workspace=Path("/private/tmp/case-checklist-codex-test"),
            case_id="case",
            expected_workspace_files=_workspace_files(),
        )


def test_event_command_policy_rejects_incomplete_or_drifted_full_read() -> None:
    files = _workspace_files()
    events = _read_plan_events(files)
    with pytest.raises(ContractLifecycleError, match="read-plan length"):
        subject._validate_event_commands(
            events=events[:-2],
            workspace=Path("/private/tmp/case-checklist-codex-test"),
            case_id="case",
            expected_workspace_files=files,
        )
    drifted = _read_plan_events(files)
    drifted[-1]["item"]["aggregated_output"] = "tampered\n"
    with pytest.raises(ContractLifecycleError, match="differs from frozen workspace bytes"):
        subject._validate_event_commands(
            events=drifted,
            workspace=Path("/private/tmp/case-checklist-codex-test"),
            case_id="case",
            expected_workspace_files=files,
        )


def test_event_command_policy_rejects_non_plan_read_command() -> None:
    files = _workspace_files()
    events = _read_plan_events(files)
    events[0]["item"]["command"] = '/bin/zsh -lc "wc -l draft_instructions.md"'
    events[1]["item"]["command"] = '/bin/zsh -lc "wc -l draft_instructions.md"'
    with pytest.raises(ContractLifecycleError, match="exact mandatory read plan"):
        subject._validate_event_commands(
            events=events,
            workspace=Path("/private/tmp/case-checklist-codex-test"),
            case_id="case",
            expected_workspace_files=files,
        )


def _agent_message_event(item_id: str = "message_0") -> dict[str, object]:
    return {
        "type": "item.completed",
        "item": {"id": item_id, "type": "agent_message", "text": "{}"},
    }


def test_agent_message_must_be_unique_and_after_all_reads() -> None:
    files = _workspace_files()
    valid_events = [*_read_plan_events(files), _agent_message_event()]
    audit = subject._validate_event_commands(
        events=valid_events,
        workspace=Path("/private/tmp/case-checklist-codex-test"),
        case_id="case",
        expected_workspace_files=files,
    )
    subject._validate_single_agent_message_after_reads(
        events=valid_events,
        read_audit=audit,
        case_id="case",
    )

    early_events = [_agent_message_event(), *_read_plan_events(files)]
    early_audit = subject._validate_event_commands(
        events=early_events,
        workspace=Path("/private/tmp/case-checklist-codex-test"),
        case_id="case",
        expected_workspace_files=files,
    )
    with pytest.raises(ContractLifecycleError, match="before mandatory reads"):
        subject._validate_single_agent_message_after_reads(
            events=early_events,
            read_audit=early_audit,
            case_id="case",
        )

    duplicate_events = [
        *_read_plan_events(files),
        _agent_message_event("message_0"),
        _agent_message_event("message_1"),
    ]
    duplicate_audit = subject._validate_event_commands(
        events=duplicate_events,
        workspace=Path("/private/tmp/case-checklist-codex-test"),
        case_id="case",
        expected_workspace_files=files,
    )
    with pytest.raises(ContractLifecycleError, match="exactly one"):
        subject._validate_single_agent_message_after_reads(
            events=duplicate_events,
            read_audit=duplicate_audit,
            case_id="case",
        )


def test_event_command_policy_rejects_quoted_newline() -> None:
    raw = "/bin/zsh -lc \"rg 'foo" + "\n" + "bar' case_packet.md\""
    with pytest.raises(ContractLifecycleError, match="forbidden expansion"):
        subject._validate_event_commands(
            events=_command_event_pair(raw),
            workspace=Path("/private/tmp/case-checklist-codex-test"),
            case_id="case",
            expected_workspace_files=_workspace_files(),
        )


def test_event_command_policy_rejects_duplicate_started_event() -> None:
    raw = '/bin/zsh -lc "wc -l case_packet.md"'
    events = [
        {"type": "item.started", "item": {"id": "item_0", "type": "command_execution", "command": raw, "aggregated_output": "", "status": "in_progress", "exit_code": None}},
        {"type": "item.started", "item": {"id": "item_0", "type": "command_execution", "command": raw, "aggregated_output": "", "status": "in_progress", "exit_code": None}},
        {"type": "item.completed", "item": {"id": "item_0", "type": "command_execution", "command": raw, "aggregated_output": "", "status": "completed", "exit_code": 0}},
    ]
    with pytest.raises(ContractLifecycleError, match="exactly one start"):
        subject._validate_event_commands(
            events=events,
            workspace=Path("/private/tmp/case-checklist-codex-test"),
            case_id="case",
            expected_workspace_files=_workspace_files(),
        )


def test_event_command_policy_rejects_terminal_before_start() -> None:
    raw = '/bin/zsh -lc "wc -l case_packet.md"'
    events = list(reversed(_command_event_pair(raw)))
    with pytest.raises(ContractLifecycleError, match="precedes"):
        subject._validate_event_commands(
            events=events,
            workspace=Path("/private/tmp/case-checklist-codex-test"),
            case_id="case",
            expected_workspace_files=_workspace_files(),
        )


def test_codex_event_lifecycle_requires_turn_start_before_items() -> None:
    events = [
        {"type": "thread.started", "thread_id": "thread"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "{}"}},
        {"type": "turn.completed", "usage": {}},
    ]
    with pytest.raises(ContractLifecycleError, match="turn.started"):
        subject._validate_codex_event_lifecycle(
            events=events, response_id="thread", case_id="case"
        )


@pytest.mark.parametrize(
    "payload",
    [
        "rm case_packet.md",
        "tee stolen.txt",
        "sed -i 's/a/b/' case_packet.md",
        "python -c 'print(1)'",
        "sort -o output.txt case_packet.md",
        "wc -l case_packet.md > count.txt",
        "awk 'BEGIN{for(k in ENVIRON) print ENVIRON[k]}' case_packet.md",
        "jq 'env' case_packet.md",
        "rg --file=/etc/passwd pattern case_packet.md",
        'wc -l "$CODEX_HOME/auth.json"',
    ],
)
def test_event_command_policy_rejects_mutation_environment_and_external_reads(payload: str) -> None:
    raw = f"/bin/zsh -lc {json.dumps(payload)}"
    events = _command_event_pair(raw)
    with pytest.raises(ContractLifecycleError):
        subject._validate_event_commands(
            events=events,
            workspace=Path("/private/tmp/case-checklist-codex-test"),
            case_id="case",
            expected_workspace_files=_workspace_files(),
        )


def test_quote_aware_expansion_allows_literal_backtick_and_awk_field_in_separate_calls() -> None:
    for payload in ("rg -n '^### `|^## ' case_packet.md", "awk '{print $0}' case_packet.md"):
        assert not subject._has_forbidden_shell_expansion(payload)
        tokens = subject._shell_tokens(payload, case_id="case")
        subject._validate_read_only_shell_tokens(tokens, case_id="case")


@pytest.mark.parametrize(
    "payload",
    [
        "wc -l case_packet.md && sed -n '1,10p' case_packet.md",
        "rg -n test case_packet.md | sort",
        "sed -n '1,10p' case_packet.md; wc -l case_packet.md",
        "sort",
        "sed '1,10p' case_packet.md",
        "sed -n -n '1,10p' case_packet.md",
        "wc case_packet.md -l",
        "wc -l --lines case_packet.md",
        "rg test -n case_packet.md",
    ],
)
def test_v3_command_policy_rejects_control_operators_and_implicit_stdin(payload: str) -> None:
    tokens = subject._shell_tokens(payload, case_id="case")
    with pytest.raises(ContractLifecycleError):
        subject._validate_read_only_shell_tokens(tokens, case_id="case")


def test_codex_argv_rejects_model_or_effort_drift() -> None:
    workspace = Path("/private/tmp/case-checklist-codex-test")
    command = [
        "codex", "exec", "--cd", str(workspace), "--skip-git-repo-check", "--ephemeral",
        "--ignore-user-config", "--sandbox", subject.EXPECTED_CODEX_SANDBOX, "--model", "gpt-5.6-sol",
        "-c", 'model_reasoning_effort="high"', "-c", 'model_verbosity="low"',
        "--color", "never", "--json", "--output-schema", str(workspace / "output_schema.json"),
        "-o", str(workspace / "draft_body.json"), "-",
    ]
    with pytest.raises(ContractLifecycleError, match="argv flags drift"):
        subject._validate_codex_argv(command, case_id="case")


def test_source_location_is_source_local(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    source.write_text('{"outer":{"items":[{"value":3}]}}\n', encoding="utf-8")
    assert support_location_resolves(source, "$")
    assert support_location_resolves(source, "$.outer.items[0].value")
    assert not support_location_resolves(source, "root")
    assert not support_location_resolves(source, "entire_file")
    assert not support_location_resolves(source, "line 1")
    assert not support_location_resolves(source, "999")

    text = tmp_path / "source.py"
    text.write_text("def evaluate():\n    return True\n", encoding="utf-8")
    assert support_location_resolves(text, "L1")
    assert support_location_resolves(text, "L1-L2")
    assert support_location_resolves(text, "evaluate")
    assert not support_location_resolves(text, "1")
    assert not support_location_resolves(text, "line 1")


def test_no_symlink_gate_executes_and_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    (root / "regular.txt").write_text("ok\n", encoding="utf-8")
    subject._validate_no_symlinks(root)
    (root / "link.txt").symlink_to(root / "regular.txt")
    with pytest.raises(ContractLifecycleError, match="symlink"):
        subject._validate_no_symlinks(root)
    with pytest.raises(ContractLifecycleError, match="symlink"):
        subject._input_file(root / "link.txt", "linked input")


def test_consecutive_canary_parent_inventory_is_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preflight = tmp_path / "preflight"
    monkeypatch.setattr(subject, "DEFAULT_PREFLIGHT_ROOT", preflight)

    subject._validate_preflight_parent_inventory(completed_rounds=())
    (preflight / "round_01/cases").mkdir(parents=True)
    subject._validate_preflight_parent_inventory(completed_rounds=("round_01",))

    (preflight / "stray").mkdir()
    with pytest.raises(ContractLifecycleError, match="parent inventory"):
        subject._validate_preflight_parent_inventory(completed_rounds=("round_01",))


def test_completed_provenance_inventory_rejects_parallel_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    draft_root = tmp_path / "draft"
    provenance = draft_root / "provenance"
    provenance.mkdir(parents=True)
    preflight = tmp_path / "preflight"
    for round_id in subject.EXPECTED_PREFLIGHT_ROUNDS:
        (preflight / round_id / "cases").mkdir(parents=True)
    monkeypatch.setattr(subject, "DEFAULT_DRAFT_ROOT", draft_root)
    monkeypatch.setattr(subject, "DEFAULT_PREFLIGHT_ROOT", preflight)

    for name in subject._completed_phase_provenance_names():
        (provenance / name).write_text("{}\n", encoding="utf-8")
    subject._validate_completed_provenance_inventory(final=False)

    for path in (
        subject.DEFAULT_CORRECTIONS_PATH,
        subject.DEFAULT_HASH_INDEX_PATH,
        subject.DEFAULT_ACCEPTANCE_PATH,
        subject.DEFAULT_FINAL_LOCK_PATH,
    ):
        (provenance / path.name).write_text("{}\n", encoding="utf-8")
    subject._validate_completed_provenance_inventory(final=True)

    (provenance / "parallel_authority.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ContractLifecycleError, match="provenance inventory"):
        subject._validate_completed_provenance_inventory(final=True)


def test_draft_namespace_top_level_inventory_is_stage_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    draft_root = tmp_path / "draft"
    (draft_root / "provenance").mkdir(parents=True)
    monkeypatch.setattr(subject, "DEFAULT_DRAFT_ROOT", draft_root)

    subject._validate_draft_root_inventory(stage="phase_start")
    (draft_root / "cases").mkdir()
    subject._validate_draft_root_inventory(stage="pre_acceptance")
    (draft_root / "accepted_cases").mkdir()
    subject._validate_draft_root_inventory(stage="final")

    (draft_root / "junk").mkdir()
    with pytest.raises(ContractLifecycleError, match="top-level inventory"):
        subject._validate_draft_root_inventory(stage="final")


@pytest.mark.parametrize(
    "payload",
    [
        "wc -l {/etc/hosts,case_packet.md}",
        "awk 'BEGIN { ARGV[1]=\"/etc/hosts\"; ARGC=2 } { print }' case_packet.md",
        "wc --files0-from=case_packet.md",
        "sort --compress-program=sh case_packet.md",
        "wc -l case_packet.md |& env",
        "wc -l case_packet.md &| env",
        "wc -l case_packet.md ;& env",
        "wc -l case_packet.md ;; env",
        "wc -l case_packet.md ;| env",
        "wc -l =env",
    ],
)
def test_event_policy_rejects_indirect_read_and_execution_bypasses(payload: str) -> None:
    raw = f"/bin/zsh -lc {json.dumps(payload)}"
    events = _command_event_pair(raw)
    with pytest.raises(ContractLifecycleError):
        subject._validate_event_commands(
            events=events,
            workspace=Path("/private/tmp/case-checklist-codex-test"),
            case_id="case",
            expected_workspace_files=_workspace_files(),
        )


def test_event_policy_rejects_unquoted_real_newline_injection() -> None:
    raw = "/bin/zsh -lc 'wc -l case_packet.md\nenv'"
    with pytest.raises(ContractLifecycleError, match="forbidden expansion"):
        subject._validate_event_commands(
            events=_command_event_pair(raw),
            workspace=Path("/private/tmp/case-checklist-codex-test"),
            case_id="case",
            expected_workspace_files=_workspace_files(),
        )


@pytest.mark.parametrize("item_type", ["web_search", "mcp_tool_call", "file_change", "reasoning"])
def test_event_type_policy_rejects_tool_like_or_unknown_items(item_type: str) -> None:
    with pytest.raises(ContractLifecycleError, match="forbidden"):
        subject._validate_codex_event_type_policy(
            events=[{"type": "item.completed", "item": {"type": item_type}}],
            case_id="case",
        )


def _fake_attempt_files(case_dir: Path, attempt_prefix: str) -> None:
    for suffix in runner.CANONICAL_SUFFIXES if hasattr(runner, "CANONICAL_SUFFIXES") else (
        "api_response.json", "checklist.json", "checklist.yaml", "llm_call.json",
        "reasoning_summary.txt", "stderr.log", "stdout.log",
    ):
        (case_dir / f"{attempt_prefix}.{suffix}").write_text(
            f"{attempt_prefix}:{suffix}\n", encoding="utf-8"
        )


def test_runner_runtime_gate_failure_is_quarantined_and_not_retried(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    packet_dir = tmp_path / "packets" / "case_1"
    packet_dir.mkdir(parents=True)
    packet = packet_dir / "case_packet.md"
    packet.write_text("packet\n", encoding="utf-8")
    output_root = tmp_path / "formal" / "cases"
    gate_calls = 0

    def fake_run_attempt(**kwargs: object) -> runner.AttemptResult:
        index = int(kwargs["attempt_index"])
        prefix = f"attempt_{index:02d}"
        case_dir = Path(kwargs["case_dir"])
        _fake_attempt_files(case_dir, prefix)
        return runner.AttemptResult(index, int(kwargs["max_output_tokens"]), 180, 1800, 0, 0.1, "", "", prefix)

    def fake_gate(**kwargs: object) -> dict[str, object]:
        nonlocal gate_calls
        gate_calls += 1
        if gate_calls == 1:
            raise ContractLifecycleError("forbidden event command: case_1")
        return {"schema_version": subject.RUNTIME_GATE_SCHEMA, "status": "passed", "policy": subject.EVENT_COMMAND_POLICY}

    monkeypatch.setattr(runner, "run_attempt", fake_run_attempt)
    monkeypatch.setattr(runner, "run_validator", lambda *args: (True, "checklist valid: case_1"))
    monkeypatch.setattr(runner, "run_appworld_v56_runtime_gate", fake_gate)
    monkeypatch.setattr(runner.time, "sleep", lambda _: None)

    result = runner.process_case(
        case_info=runner.CasePacketInfo(packet, packet.stat().st_size),
        lane="regular", output_root=output_root, provider="codex",
        model="gpt-5.6-sol", reasoning_effort="xhigh",
        token_budgets=[12000, 16000, 20000], http_timeout_seconds=180,
        codex_timeout_seconds=1800, codex_sandbox="read-only",
        prompt_supplement=None, sleep_seconds=0.0, force=True,
        warning_fn=lambda _: [], appworld_v56_runtime_gate=True,
    )

    assert result["status"] == "failed"
    assert [attempt["runtime_policy_gate"]["status"] for attempt in result["attempts"]] == ["failed"]
    assert "quarantine" in result["attempts"][0]
    case_dir = output_root / "case_1"
    assert not list(case_dir.glob("attempt_01.*"))
    assert not list(case_dir.glob("attempt_02.*"))
    quarantine_dir = output_root.parent / "quarantine" / "case_1"
    assert len(list(quarantine_dir.glob("attempt_01.*"))) == 8
    assert not (case_dir / "checklist.yaml").exists()


def test_runner_retries_only_an_audited_infrastructure_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    packet_dir = tmp_path / "packets" / "case_1"
    packet_dir.mkdir(parents=True)
    packet = packet_dir / "case_packet.md"
    packet.write_text("packet\n", encoding="utf-8")
    output_root = tmp_path / "formal" / "cases"

    def fake_run_attempt(**kwargs: object) -> runner.AttemptResult:
        index = int(kwargs["attempt_index"])
        prefix = f"attempt_{index:02d}"
        case_dir = Path(kwargs["case_dir"])
        _fake_attempt_files(case_dir, prefix)
        return runner.AttemptResult(
            index,
            int(kwargs["max_output_tokens"]),
            180,
            1800,
            1 if index == 1 else 0,
            0.1,
            "rate limited" if index == 1 else "",
            "",
            prefix,
        )

    monkeypatch.setattr(runner, "run_attempt", fake_run_attempt)
    monkeypatch.setattr(runner, "run_validator", lambda *args: (True, "checklist valid: case_1"))
    monkeypatch.setattr(
        runner,
        "classify_appworld_v56_infra_retry",
        lambda **kwargs: {"retryable": True},
    )
    monkeypatch.setattr(
        runner,
        "run_appworld_v56_runtime_gate",
        lambda **kwargs: {
            "schema_version": subject.RUNTIME_GATE_SCHEMA,
            "status": "passed",
            "policy": subject.EVENT_COMMAND_POLICY,
        },
    )
    monkeypatch.setattr(runner.time, "sleep", lambda _: None)

    result = runner.process_case(
        case_info=runner.CasePacketInfo(packet, packet.stat().st_size),
        lane="regular",
        output_root=output_root,
        provider="codex",
        model="gpt-5.6-sol",
        reasoning_effort="xhigh",
        token_budgets=[12000, 16000, 20000],
        http_timeout_seconds=180,
        codex_timeout_seconds=1800,
        codex_sandbox="danger-full-access",
        prompt_supplement=None,
        sleep_seconds=0.0,
        force=True,
        warning_fn=lambda _: [],
        appworld_v56_runtime_gate=True,
    )

    assert result["status"] == "success"
    assert [attempt["returncode"] for attempt in result["attempts"]] == [1, 0]
    assert result["attempts"][0]["runtime_policy_gate"]["status"] == "not_run"
    assert result["attempts"][1]["runtime_policy_gate"]["status"] == "passed"
    assert (output_root.parent / "quarantine/case_1/attempt_01.quarantine.json").is_file()


def _infra_retry_fixture(*, returncode: int = 124, stderr: str = "") -> tuple[dict[str, object], dict[str, object], frozenset[str]]:
    attempt = {
        "attempt_index": 1,
        "returncode": 1,
        "runtime_policy_gate": subject.appworld_v56_runtime_gate_rejection(
            status="not_run", reason="drafter_nonzero_or_checklist_missing"
        ),
    }
    api = {
        "status": "failed",
        "output_text": "{}",
        "codex_cli": {
            "returncode": returncode,
            "stderr": stderr,
            "events": [
                {"type": "thread.started", "thread_id": "thread-1"},
                {"type": "turn.started"},
            ],
        },
    }
    suffixes = frozenset(
        {
            "api_response.json",
            "llm_call.json",
            "reasoning_summary.txt",
            "stderr.log",
            "stdout.log",
        }
    )
    return api, attempt, suffixes


def test_infra_retry_classifier_accepts_only_pre_result_timeout_or_allowlist() -> None:
    api, attempt, suffixes = _infra_retry_fixture()
    timeout = subject._classify_audited_infra_retry(
        api_response=api,
        attempt_record=attempt,
        suffixes=suffixes,
        case_id="case_1",
        attempt_prefix="attempt_01",
    )
    assert timeout["retryable"] is True
    assert timeout["reason"] == "codex_subprocess_timeout"

    api, attempt, suffixes = _infra_retry_fixture(
        returncode=1, stderr="HTTP 429: please try again in 2.5s"
    )
    rate_limit = subject._classify_audited_infra_retry(
        api_response=api,
        attempt_record=attempt,
        suffixes=suffixes,
        case_id="case_1",
        attempt_prefix="attempt_01",
    )
    assert rate_limit["retryable"] is True
    assert rate_limit["reason"] == "provider_rate_limit"


@pytest.mark.parametrize(
    "mutation",
    [
        "completed_response",
        "agent_message",
        "unallowlisted_failure",
        "checklist_artifact",
    ],
)
def test_infra_retry_classifier_rejects_model_or_unclassified_failures(
    mutation: str,
) -> None:
    api, attempt, suffixes = _infra_retry_fixture(returncode=1, stderr="unknown failure")
    if mutation == "completed_response":
        api["status"] = "completed"
    elif mutation == "agent_message":
        api["codex_cli"]["events"].append(  # type: ignore[index,union-attr]
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": "draft"},
            }
        )
    elif mutation == "checklist_artifact":
        suffixes = frozenset({*suffixes, "checklist.yaml"})
    result = subject._classify_audited_infra_retry(
        api_response=api,
        attempt_record=attempt,
        suffixes=suffixes,
        case_id="case_1",
        attempt_prefix="attempt_01",
    )
    assert result["retryable"] is False


def test_generic_runner_does_not_invoke_v56_gate_or_quarantine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    packet_dir = tmp_path / "packets" / "case_1"
    packet_dir.mkdir(parents=True)
    packet = packet_dir / "case_packet.md"
    packet.write_text("packet\n", encoding="utf-8")
    output_root = tmp_path / "formal" / "cases"

    def fake_run_attempt(**kwargs: object) -> runner.AttemptResult:
        case_dir = Path(kwargs["case_dir"])
        _fake_attempt_files(case_dir, "attempt_01")
        return runner.AttemptResult(1, 12000, 180, 1800, 0, 0.1, "", "", "attempt_01")

    monkeypatch.setattr(runner, "run_attempt", fake_run_attempt)
    monkeypatch.setattr(runner, "run_validator", lambda *args: (True, "checklist valid: case_1"))
    monkeypatch.setattr(
        runner,
        "run_appworld_v56_runtime_gate",
        lambda **kwargs: pytest.fail("generic runner called the AppWorld v56 gate"),
    )
    result = runner.process_case(
        case_info=runner.CasePacketInfo(packet, packet.stat().st_size),
        lane="regular", output_root=output_root, provider="codex", model="any",
        reasoning_effort="high", token_budgets=[12000], http_timeout_seconds=180,
        codex_timeout_seconds=1800, codex_sandbox="read-only",
        prompt_supplement=None, sleep_seconds=0.0, force=True,
        warning_fn=lambda _: [], appworld_v56_runtime_gate=False,
    )
    assert result["status"] == "success"
    assert "runtime_policy_gate" not in result["attempts"][0]
    assert not (output_root.parent / "quarantine").exists()


def test_runner_does_not_misclassify_runtime_bug_as_policy_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    packet_dir = tmp_path / "packets" / "case_1"
    packet_dir.mkdir(parents=True)
    packet = packet_dir / "case_packet.md"
    packet.write_text("packet\n", encoding="utf-8")
    output_root = tmp_path / "formal" / "cases"

    def fake_run_attempt(**kwargs: object) -> runner.AttemptResult:
        case_dir = Path(kwargs["case_dir"])
        _fake_attempt_files(case_dir, "attempt_01")
        return runner.AttemptResult(1, 12000, 180, 1800, 0, 0.1, "", "", "attempt_01")

    monkeypatch.setattr(runner, "run_attempt", fake_run_attempt)
    monkeypatch.setattr(runner, "run_validator", lambda *args: (True, "checklist valid: case_1"))
    monkeypatch.setattr(
        runner,
        "run_appworld_v56_runtime_gate",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("implementation defect")),
    )
    with pytest.raises(RuntimeError, match="implementation defect"):
        runner.process_case(
            case_info=runner.CasePacketInfo(packet, packet.stat().st_size),
            lane="regular", output_root=output_root, provider="codex",
            model="gpt-5.6-sol", reasoning_effort="xhigh",
            token_budgets=[12000, 16000], http_timeout_seconds=180,
            codex_timeout_seconds=1800, codex_sandbox="read-only",
            prompt_supplement=None, sleep_seconds=0.0, force=True,
            warning_fn=lambda _: [], appworld_v56_runtime_gate=True,
        )
    assert not (output_root.parent / "quarantine").exists()


def test_formal_batch_argv_freezes_runtime_gate_and_8_by_8() -> None:
    argv = subject._expected_batch_argv(
        packet_root=subject.resolve_repo_path(subject._PACKET_ROOT).resolve(),
        cases_root=subject.resolve_repo_path(subject.DEFAULT_CASES_ROOT).resolve(),
    )
    assert "--appworld-v56-runtime-gate" in argv
    assert argv[argv.index("--max-parallel") + 1] == "8"
    assert argv[argv.index("--large-max-parallel") + 1] == "8"
    assert argv[argv.index("--codex-sandbox") + 1] == "danger-full-access"
    assert "--fail-fast" in argv


def _parsed_config_fixture(*, run_kind: str, round_id: str | None = None) -> tuple[dict[str, object], dict[str, object]]:
    packet_root = subject._repo_relative(subject.resolve_repo_path(subject._PACKET_ROOT).resolve())
    formal_root = subject._repo_relative(subject.resolve_repo_path(subject.DEFAULT_CASES_ROOT).resolve())
    rounds = [
        {
            "round_id": value,
            "output_root": subject._repo_relative(
                subject.resolve_repo_path(subject.DEFAULT_PREFLIGHT_ROOT / value / "cases").resolve()
            ),
        }
        for value in subject.EXPECTED_PREFLIGHT_ROUNDS
    ]
    lock: dict[str, object] = {
        "inputs": {"case_packet_root": packet_root},
        "execution": {"output_root": formal_root},
        "preflight": {"rounds": rounds},
    }
    is_canary = run_kind == "canary"
    config: dict[str, object] = {
        "case_packet_root": packet_root,
        "output_root": (
            next(item["output_root"] for item in rounds if item["round_id"] == round_id)
            if is_canary
            else formal_root
        ),
        "provider": "codex",
        "model": subject.EXPECTED_MODEL,
        "reasoning_effort": subject.EXPECTED_REASONING_EFFORT,
        "token_budgets": list(subject.EXPECTED_TOKEN_BUDGETS),
        "max_parallel": 8,
        "large_max_parallel": 8,
        "large_case_threshold_bytes": subject.EXPECTED_LARGE_THRESHOLD_BYTES,
        "http_timeout_seconds": 180,
        "large_http_timeout_seconds": 480,
        "codex_timeout_seconds": 1800,
        "large_codex_timeout_seconds": 3600,
        "codex_sandbox": subject.EXPECTED_CODEX_SANDBOX,
        "prompt_supplement": subject._repo_relative(
            subject.resolve_repo_path(
                subject._IMPLEMENTATION_PATHS["appworld_gpt56_draft_strict_v3.supplement.md"]
            ).resolve()
        ),
        "sort_by": "size",
        "sleep_seconds": 2.0,
        "quality_check": "none",
        "limit": None,
        "case_ids": list(subject.EXPECTED_PREFLIGHT_CASE_IDS) if is_canary else None,
        "canary_round": round_id if is_canary else None,
        "run_kind": run_kind,
        "force": False,
        "fail_fast": True,
        "dry_run": False,
        "total_case_count": (
            len(subject.EXPECTED_PREFLIGHT_CASE_IDS) if is_canary else 485
        ),
        "regular_case_count": (
            subject.EXPECTED_PREFLIGHT_LANE_COUNTS["regular"]
            if is_canary
            else subject.EXPECTED_LANE_COUNTS["regular"]
        ),
        "oversized_case_count": (
            subject.EXPECTED_PREFLIGHT_LANE_COUNTS["oversized"]
            if is_canary
            else subject.EXPECTED_LANE_COUNTS["oversized"]
        ),
    }
    return config, lock


def test_formal_and_canary_configs_are_explicit_disjoint_complete_maps() -> None:
    formal, formal_lock = _parsed_config_fixture(run_kind="formal")
    canary, canary_lock = _parsed_config_fixture(run_kind="canary", round_id="round_02")

    assert subject._validate_v56_parsed_config(
        formal, lock=formal_lock, require_clean_roots=False
    )["run_kind"] == "formal"
    assert subject._validate_v56_parsed_config(
        canary, lock=canary_lock, require_clean_roots=False
    )["canary_round"] == "round_02"

    canary["case_ids"] = list(reversed(subject.EXPECTED_PREFLIGHT_CASE_IDS))
    with pytest.raises(ContractLifecycleError, match="complete canonical map"):
        subject._validate_v56_parsed_config(
            canary, lock=canary_lock, require_clean_roots=False
        )


def test_runner_case_id_parser_is_exact_and_duplicate_free() -> None:
    assert runner.parse_case_ids("a,b,c") == ["a", "b", "c"]
    assert runner.parse_case_ids(None) is None
    with pytest.raises(SystemExit, match="duplicate"):
        runner.parse_case_ids("a,b,a")
    with pytest.raises(SystemExit, match="empty"):
        runner.parse_case_ids("a,,b")


def test_runner_utc_timestamp_has_subsecond_utc_precision() -> None:
    value = runner.utc_now_iso()
    assert value.endswith("Z")
    assert "." in value
    parsed = subject._parse_timestamp(value, "runner timestamp")
    assert parsed.utcoffset() is not None
    assert parsed.utcoffset().total_seconds() == 0


@pytest.mark.parametrize(
    ("filename", "label", "content_sha256"),
    [
        (subject.DEFAULT_CORRECTIONS_PATH.name, "zero-correction manifest", None),
        (subject.DEFAULT_HASH_INDEX_PATH.name, "draft hash index", "c" * 64),
        (subject.DEFAULT_ACCEPTANCE_PATH.name, "acceptance report", None),
    ],
)
def test_final_artifact_refs_require_exact_fields_and_canonical_paths(
    tmp_path: Path,
    filename: str,
    label: str,
    content_sha256: str | None,
) -> None:
    canonical = tmp_path / filename
    canonical.write_text('{"canonical":true}\n', encoding="utf-8")
    expected = {
        "path": str(canonical.resolve()),
        "sha256": subject.sha256_file(canonical),
    }
    if content_sha256 is not None:
        expected["content_sha256"] = content_sha256

    assert subject._validate_canonical_final_artifact_ref(
        expected,
        canonical_file=canonical,
        label=label,
        content_sha256=content_sha256,
    ) == canonical.resolve()

    with pytest.raises(ContractLifecycleError, match="field/value drift"):
        subject._validate_canonical_final_artifact_ref(
            {**expected, "unbound_extra": True},
            canonical_file=canonical,
            label=label,
            content_sha256=content_sha256,
        )

    sibling = tmp_path / f"copy-{filename}"
    sibling.write_bytes(canonical.read_bytes())
    sibling_ref = {**expected, "path": str(sibling.resolve()), "sha256": subject.sha256_file(sibling)}
    with pytest.raises(ContractLifecycleError, match="path is noncanonical"):
        subject._validate_canonical_final_artifact_ref(
            sibling_ref,
            canonical_file=canonical,
            label=label,
            content_sha256=content_sha256,
        )


def test_api_less_rejected_attempt_invalidates_namespace(tmp_path: Path) -> None:
    """A rejected call without its API/event stream is never an auditable retry."""

    with pytest.raises(ContractLifecycleError, match="no auditable Codex API/event sidecar"):
        subject._validate_rejected_codex_transport(
            expected_dir=tmp_path,
            sidecar_origin_dir=tmp_path,
            case_id="case_1",
            attempt_prefix="attempt_01",
            attempt_record={},
            suffixes=frozenset({"stderr.log", "stdout.log"}),
            case_packet_path=tmp_path / "case_packet.md",
        )


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _phase_receipt_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    run_kind: str = "canary",
    round_id: str | None = "round_01",
    started_at: str = "2026-01-01T00:02:00Z",
    predecessor_validated_at: str = "2026-01-01T00:01:00Z",
    acceptance_validated_at: str = "2026-01-01T00:01:00Z",
) -> dict[str, object]:
    draft_root = tmp_path / "draft"
    provenance = draft_root / "provenance"
    provenance.mkdir(parents=True)
    lock_path = provenance / "draft_run_lock.json"
    acceptance_path = provenance / "canary_acceptance.json"
    output_root = tmp_path / ("formal" if run_kind == "formal" else str(round_id)) / "cases"
    expected_argv = [f"run-{run_kind}-{round_id or 'all'}"]
    environment_sha = "e" * 64
    python_sha = "p" * 64
    codex_sha = "c" * 64
    predecessor_sha = "d" * 64
    acceptance_sha = "a" * 64

    lock: dict[str, object] = {
        "locked_at": "2026-01-01T00:00:00Z",
        "execution": {
            "output_root": subject._repo_relative(output_root),
            "command_argv": expected_argv if run_kind == "formal" else ["unused-formal"],
        },
        "preflight": {
            "rounds": [
                {
                    "round_id": value,
                    "output_root": subject._repo_relative(tmp_path / value / "cases"),
                    "command_argv": expected_argv if value == round_id else [f"run-{value}"],
                }
                for value in subject.EXPECTED_PREFLIGHT_ROUNDS
            ]
        },
        "environment": {"environment_semantic_sha256": environment_sha},
        "runtime": {
            "python_executable_sha256": python_sha,
            "codex_executable_sha256": codex_sha,
        },
    }
    _write_json(lock_path, lock)
    if run_kind == "formal":
        _write_json(acceptance_path, {"validated_at": acceptance_validated_at})

    monkeypatch.setattr(subject, "DEFAULT_DRAFT_ROOT", draft_root)
    monkeypatch.setattr(subject, "DEFAULT_LOCK_PATH", lock_path)
    monkeypatch.setattr(subject, "DEFAULT_CANARY_ACCEPTANCE_PATH", acceptance_path)
    monkeypatch.setattr(
        subject,
        "_validate_v56_parsed_config",
        lambda config, **_kwargs: dict(config),
    )
    monkeypatch.setattr(
        subject,
        "validate_appworld_v56_canary_round_receipt",
        lambda **_kwargs: {
            "receipt_sha256": predecessor_sha,
            "validated_at": predecessor_validated_at,
        },
    )
    monkeypatch.setattr(
        subject,
        "validate_appworld_v56_canary_acceptance",
        lambda **_kwargs: {"receipt_sha256": acceptance_sha},
    )

    canonical_output = subject._repo_relative(output_root)
    config = {"output_root": canonical_output}
    core: dict[str, object] = {
        "schema_version": "appworld_v56_batch_start_validation.v2",
        "status": "passed",
        "run_kind": run_kind,
        "canary_round": round_id,
        "pre_run_lock_sha256": subject.sha256_file(lock_path),
        "prior_round_receipt_sha256": (
            predecessor_sha
            if run_kind == "canary" and round_id != subject.EXPECTED_PREFLIGHT_ROUNDS[0]
            else None
        ),
        "canary_acceptance_sha256": acceptance_sha if run_kind == "formal" else None,
        "parsed_config_semantic_sha256": subject.sha256_object(config),
        "parsed_config": config,
        "login_status_at_batch_start": "Logged in using ChatGPT",
        "environment_semantic_sha256": environment_sha,
        "python_executable_sha256": python_sha,
        "codex_executable_sha256": codex_sha,
    }
    start_payload: dict[str, object] = {
        "schema_version": subject.PHASE_START_SCHEMA,
        "status": "started_locked",
        "started_at": started_at,
        "draft_run_id": subject.EXPECTED_DRAFT_RUN_ID,
        "run_kind": run_kind,
        "canary_round": round_id,
        "pre_run_lock": {
            "path": subject._repo_relative(lock_path),
            "sha256": subject.sha256_file(lock_path),
        },
        "output_root": canonical_output,
        "quarantine_root": subject._repo_relative(output_root.parent / "quarantine"),
        "invocation_argv": expected_argv,
        "invocation_argv_semantic_sha256": subject.sha256_object(expected_argv),
        "batch_start_validation": core,
        "batch_start_validation_semantic_sha256": subject.sha256_object(core),
    }
    start_path, terminal_path = subject._phase_receipt_paths(
        run_kind=run_kind,
        round_id=round_id,
    )
    _write_json(start_path, start_payload)
    return {
        "start_path": start_path,
        "terminal_path": terminal_path,
        "start_payload": start_payload,
        "output_root": output_root,
        "lock_path": lock_path,
        "acceptance_path": acceptance_path,
        "predecessor_sha": predecessor_sha,
        "acceptance_sha": acceptance_sha,
    }


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("extra_field", "field set drift"),
        ("lock_path", "lock binding drift"),
        ("lock_hash", "lock binding drift"),
        ("before_lock", "started before the pre-run lock"),
        ("argv_hash", "invocation binding drift"),
        ("core_hash", "core hash drift"),
    ],
)
def test_phase_start_receipt_rejects_field_hash_time_and_canonical_path_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    message: str,
) -> None:
    fixture = _phase_receipt_fixture(tmp_path, monkeypatch)
    start_path = Path(fixture["start_path"])
    payload = dict(fixture["start_payload"])
    if mutation == "extra_field":
        payload["parallel_authority"] = True
    elif mutation == "lock_path":
        sibling = tmp_path / "copied_lock.json"
        sibling.write_bytes(Path(fixture["lock_path"]).read_bytes())
        payload["pre_run_lock"] = {
            **dict(payload["pre_run_lock"]),
            "path": subject._repo_relative(sibling),
        }
    elif mutation == "lock_hash":
        payload["pre_run_lock"] = {
            **dict(payload["pre_run_lock"]),
            "sha256": "0" * 64,
        }
    elif mutation == "before_lock":
        payload["started_at"] = "2025-12-31T23:59:59Z"
    elif mutation == "argv_hash":
        payload["invocation_argv_semantic_sha256"] = "0" * 64
    else:
        payload["batch_start_validation_semantic_sha256"] = "0" * 64
    _write_json(start_path, payload)

    with pytest.raises(ContractLifecycleError, match=message):
        subject._validate_phase_start_receipt(run_kind="canary", round_id="round_01")


def test_canary_phase_start_strictly_binds_and_follows_predecessor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _phase_receipt_fixture(
        tmp_path,
        monkeypatch,
        round_id="round_02",
    )
    assert subject._validate_phase_start_receipt(
        run_kind="canary", round_id="round_02"
    )["started_at"] == "2026-01-01T00:02:00Z"

    payload = dict(fixture["start_payload"])
    core = dict(payload["batch_start_validation"])
    core["prior_round_receipt_sha256"] = "0" * 64
    payload["batch_start_validation"] = core
    payload["batch_start_validation_semantic_sha256"] = subject.sha256_object(core)
    _write_json(Path(fixture["start_path"]), payload)
    with pytest.raises(ContractLifecycleError, match="predecessor binding drift"):
        subject._validate_phase_start_receipt(run_kind="canary", round_id="round_02")


def test_canary_phase_start_must_be_strictly_after_predecessor_time(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _phase_receipt_fixture(
        tmp_path,
        monkeypatch,
        round_id="round_02",
        predecessor_validated_at="2026-01-01T00:02:00Z",
    )
    with pytest.raises(ContractLifecycleError, match="did not start after its predecessor"):
        subject._validate_phase_start_receipt(run_kind="canary", round_id="round_02")


def test_formal_phase_start_binds_accepted_canary_and_is_strictly_later(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _phase_receipt_fixture(
        tmp_path,
        monkeypatch,
        run_kind="formal",
        round_id=None,
    )
    assert subject._validate_phase_start_receipt(
        run_kind="formal", round_id=None
    )["started_at"] == "2026-01-01T00:02:00Z"

    payload = dict(fixture["start_payload"])
    core = dict(payload["batch_start_validation"])
    core["canary_acceptance_sha256"] = "0" * 64
    payload["batch_start_validation"] = core
    payload["batch_start_validation_semantic_sha256"] = subject.sha256_object(core)
    _write_json(Path(fixture["start_path"]), payload)
    with pytest.raises(ContractLifecycleError, match="canary-acceptance binding drift"):
        subject._validate_phase_start_receipt(run_kind="formal", round_id=None)


def test_formal_phase_start_equal_to_canary_acceptance_time_is_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _phase_receipt_fixture(
        tmp_path,
        monkeypatch,
        run_kind="formal",
        round_id=None,
        acceptance_validated_at="2026-01-01T00:02:00Z",
    )
    with pytest.raises(ContractLifecycleError, match="did not start after canary acceptance"):
        subject._validate_phase_start_receipt(run_kind="formal", round_id=None)


def _terminal_receipt_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, object]:
    fixture = _phase_receipt_fixture(tmp_path, monkeypatch)
    start_path = Path(fixture["start_path"])
    terminal_path = Path(fixture["terminal_path"])
    output_root = Path(fixture["output_root"])
    output_root.mkdir(parents=True)
    summary_path = output_root / "_batch_summary.json"
    results_path = output_root / "_batch_results.jsonl"
    _write_json(summary_path, {"updated_at": "2026-01-01T00:02:30Z"})
    results_path.write_text('{"status":"success"}\n', encoding="utf-8")
    terminal_payload: dict[str, object] = {
        "schema_version": subject.PHASE_TERMINAL_SCHEMA,
        "status": "passed_complete",
        "completed_at": "2026-01-01T00:03:00Z",
        "draft_run_id": subject.EXPECTED_DRAFT_RUN_ID,
        "run_kind": "canary",
        "canary_round": "round_01",
        "exit_code": 0,
        "phase_start_receipt": {
            "path": subject._repo_relative(start_path),
            "sha256": subject.sha256_file(start_path),
        },
        "output_root": subject._repo_relative(output_root),
        "output_tree_sha256": subject.sha256_path(output_root),
        "quarantine": {
            "root": subject._repo_relative(output_root.parent / "quarantine"),
            "exists": False,
            "tree_sha256": None,
        },
        "batch_summary": {
            "path": subject._repo_relative(summary_path),
            "sha256": subject.sha256_file(summary_path),
        },
        "batch_results": {
            "path": subject._repo_relative(results_path),
            "sha256": subject.sha256_file(results_path),
            "row_count": 1,
        },
    }
    _write_json(terminal_path, terminal_payload)
    return {
        **fixture,
        "terminal_payload": terminal_payload,
        "summary_path": summary_path,
        "results_path": results_path,
    }


def test_missing_phase_terminal_receipt_is_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _phase_receipt_fixture(tmp_path, monkeypatch)
    assert not Path(fixture["terminal_path"]).exists()
    with pytest.raises(ContractLifecycleError, match="phase-terminal receipt is missing"):
        subject._validate_phase_terminal_receipt(
            run_kind="canary",
            round_id="round_01",
            require_passed=True,
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("extra_field", "field set drift"),
        ("start_path", "start/output binding drift"),
        ("start_hash", "start/output binding drift"),
        ("before_start", "terminal predates start"),
        ("output_hash", "output changed after terminal receipt"),
        ("summary_path", "batch-file binding drift"),
        ("summary_hash", "batch-file binding drift"),
    ],
)
def test_phase_terminal_receipt_rejects_field_hash_time_and_canonical_path_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    message: str,
) -> None:
    fixture = _terminal_receipt_fixture(tmp_path, monkeypatch)
    terminal_path = Path(fixture["terminal_path"])
    payload = dict(fixture["terminal_payload"])
    if mutation == "extra_field":
        payload["parallel_terminal"] = True
    elif mutation == "start_path":
        sibling = tmp_path / "copied_start.json"
        sibling.write_bytes(Path(fixture["start_path"]).read_bytes())
        payload["phase_start_receipt"] = {
            **dict(payload["phase_start_receipt"]),
            "path": subject._repo_relative(sibling),
        }
    elif mutation == "start_hash":
        payload["phase_start_receipt"] = {
            **dict(payload["phase_start_receipt"]),
            "sha256": "0" * 64,
        }
    elif mutation == "before_start":
        payload["completed_at"] = "2026-01-01T00:01:59Z"
    elif mutation == "output_hash":
        payload["output_tree_sha256"] = "0" * 64
    elif mutation == "summary_path":
        sibling = tmp_path / "copied_summary.json"
        sibling.write_bytes(Path(fixture["summary_path"]).read_bytes())
        payload["batch_summary"] = {
            **dict(payload["batch_summary"]),
            "path": subject._repo_relative(sibling),
        }
    else:
        payload["batch_summary"] = {
            **dict(payload["batch_summary"]),
            "sha256": "0" * 64,
        }
    _write_json(terminal_path, payload)

    with pytest.raises(ContractLifecycleError, match=message):
        subject._validate_phase_terminal_receipt(
            run_kind="canary",
            round_id="round_01",
            require_passed=True,
        )


def test_phase_terminal_receipt_detects_post_seal_start_and_output_tampering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _terminal_receipt_fixture(tmp_path, monkeypatch)
    assert subject._validate_phase_terminal_receipt(
        run_kind="canary", round_id="round_01", require_passed=True
    )["status"] == "passed_complete"

    start_path = Path(fixture["start_path"])
    start_path.write_text(start_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ContractLifecycleError, match="start/output binding drift"):
        subject._validate_phase_terminal_receipt(
            run_kind="canary", round_id="round_01", require_passed=True
        )

    _write_json(start_path, dict(fixture["start_payload"]))
    (Path(fixture["output_root"]) / "post_terminal_tamper.txt").write_text(
        "tampered\n", encoding="utf-8"
    )
    with pytest.raises(ContractLifecycleError, match="output changed after terminal receipt"):
        subject._validate_phase_terminal_receipt(
            run_kind="canary", round_id="round_01", require_passed=True
        )


def test_formal_batch_start_refuses_missing_or_rejected_canary_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    draft_root = tmp_path / "draft"
    provenance = draft_root / "provenance"
    provenance.mkdir(parents=True)
    lock_path = provenance / "draft_run_lock.json"
    config, lock = _parsed_config_fixture(run_kind="formal")
    lock["execution"]["command_argv"] = ["run-formal"]
    _write_json(lock_path, lock)
    monkeypatch.setattr(subject, "DEFAULT_DRAFT_ROOT", draft_root)
    monkeypatch.setattr(subject, "DEFAULT_LOCK_PATH", lock_path)
    monkeypatch.setattr(
        subject,
        "validate_appworld_draft_pre_run_lock_v56",
        lambda **_kwargs: {"lock_sha256": subject.sha256_file(lock_path)},
    )
    monkeypatch.setattr(
        subject,
        "_validate_v56_parsed_config",
        lambda value, **_kwargs: dict(value),
    )
    monkeypatch.setattr(
        subject,
        "_validate_phase_start_provenance_inventory",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        subject,
        "validate_appworld_v56_canary_acceptance",
        lambda **_kwargs: (_ for _ in ()).throw(
            ContractLifecycleError("canary acceptance missing or invalid")
        ),
    )

    start_path, _ = subject._phase_receipt_paths(run_kind="formal", round_id=None)
    with pytest.raises(ContractLifecycleError, match="canary acceptance missing or invalid"):
        subject.validate_appworld_v56_batch_start(
            config,
            invocation_argv=["run-formal"],
        )
    assert not start_path.exists()
