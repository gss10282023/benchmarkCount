from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from evidence_system.contracts import appworld_draft_acceptance_v56 as runtime


ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = (
    ROOT
    / "neurips_ed_track_minimal"
    / "prompts"
    / "appworld_gpt56_draft_strict_v3.supplement.md"
)
V2_PATH = (
    ROOT
    / "neurips_ed_track_minimal"
    / "prompts"
    / "draft_source_pointer_strict_v2.supplement.md"
)


def _prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def test_v3_is_additive_and_states_testtracker_scoring_semantics() -> None:
    text = _prompt()

    assert V2_PATH.is_file()
    assert "pass_count == num_tests" in text
    assert "with test(...):" in text
    assert "outside every `with test(...):` block" in text
    for forbidden_native_conjunct in (
        "test.task_completed",
        "task.status",
        "active_tasks[0].status",
    ):
        assert forbidden_native_conjunct in text
    assert "any failed registered block belongs in `fail_if`" in text


def test_v3_freezes_resolvable_pointer_forms() -> None:
    text = _prompt()
    compact = " ".join(text.split())

    assert "entire JSON document, the location is exactly `$`" in compact
    assert "`$.outer.items[0].value`" in text
    assert "Every component must resolve" in compact
    assert "`L<n>`" in text
    assert "`L<n>-L<m>`" in text
    assert "exact source-local symbol" in compact
    assert "Never use `root`, `entire_file`" in compact
    assert (
        "Never cite `draft_instructions.md`, `template.yaml`, `output_schema.json`"
        in compact
    )
    assert "URL, absolute path, leading `./`, or `..` traversal" in compact


def test_v3_keeps_official_answer_sources_out_of_post_run_artifacts() -> None:
    text = _prompt()
    compact = " ".join(text.split())

    assert "Official source files and source-only values" in compact
    assert "They are not stored post-run artifacts" in compact
    assert "`native.decisive_artifacts[*].artifact` and `.question`" in compact
    for forbidden in (
        "`ground-truth`",
        "`ground truth`",
        "`ground_truth`",
        "`gold answer`",
        "`answer key`",
        "`reference answer`",
    ):
        assert forbidden in text
    assert (
        "Retained submitted answer and official evaluator comparison result" in compact
    )
    assert (
        "Do not name, reproduce, or call for retaining the official source answer"
        in compact
    )


def test_v3_tool_policy_is_an_explicit_strict_runtime_subset() -> None:
    text = _prompt()
    compact = " ".join(text.split())

    assert "Never call `web_search`" in text
    assert "`python`, `python3`, or any other executable" in text
    assert "sealed direct-input bundle" in text
    assert "requires zero tool events" in compact

    files = {
        "draft_instructions.md": text,
        "template.yaml": "template\n",
        "case_packet.md": "packet\n",
        "output_schema.json": "{}\n",
    }
    stdin_text, _ = runtime.minimal_drafter.build_codex_stdin_bundle(files)
    transport_instruction = json.loads(stdin_text)["instruction"]
    assert "Do not invoke or call any tool of any kind" in transport_instruction
    assert "shell, unified exec, web, network, MCP" in transport_instruction
    assert "file-read, file-write, or patch tools" in transport_instruction
    assert "model-driven file read plan is superseded" in transport_instruction
    assert "exactly one final agent message" in transport_instruction
    assert "Do not emit an intermediate agent message" in transport_instruction


def test_sealed_direct_stdin_bundle_covers_all_four_files_and_is_rebuildable() -> None:
    files = {
        "draft_instructions.md": "instructions\n",
        "template.yaml": "template\n",
        "case_packet.md": "packet one\npacket two\n",
        "output_schema.json": "{}\n",
    }

    stdin_text, manifest = runtime.minimal_drafter.build_codex_stdin_bundle(files)
    payload = json.loads(stdin_text)
    assert payload["schema_version"] == "codex_direct_stdin_bundle.v1"
    assert payload["policy"] == "direct_stdin_sealed_bundle_v1"
    assert [item["name"] for item in payload["components"]] == list(files)
    assert [item["text"] for item in payload["components"]] == list(files.values())
    assert manifest == {
        "schema_version": "codex_direct_stdin_bundle.v1",
        "policy": "direct_stdin_sealed_bundle_v1",
        "total_sha256": hashlib.sha256(stdin_text.encode("utf-8")).hexdigest(),
        "total_size_bytes": len(stdin_text.encode("utf-8")),
        "components": [
            {
                "name": name,
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "size_bytes": len(text.encode("utf-8")),
                "line_count": len(text.splitlines()),
            }
            for name, text in files.items()
        ],
    }
    assert all(
        set(item) == {"name", "sha256", "size_bytes", "line_count"}
        for item in manifest["components"]
    )
    assert "text" not in json.dumps(manifest)
    assert runtime.minimal_drafter.build_codex_stdin_bundle(files) == (
        stdin_text,
        manifest,
    )


def test_direct_stdin_codex_argv_disables_tools_and_workspace_has_only_schema(
    tmp_path: Path, monkeypatch
) -> None:
    drafter = runtime.minimal_drafter
    codex_executable = tmp_path / "codex"
    codex_executable.write_text("placeholder\n", encoding="utf-8")
    observed: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        workspace = Path(command[command.index("--cd") + 1])
        assert {path.name for path in workspace.iterdir()} == {"output_schema.json"}
        stdin_text = str(kwargs["input"])
        payload = json.loads(stdin_text)
        assert [item["name"] for item in payload["components"]] == list(
            drafter.CODEX_WORKSPACE_FILE_ORDER
        )
        observed["stdin_text"] = stdin_text
        output_body = {"native": {}, "stronger": {"additional_conditions": []}}
        Path(command[command.index("-o") + 1]).write_text(
            json.dumps(output_body), encoding="utf-8"
        )
        events = [
            {"type": "thread.started", "thread_id": "sealed-thread"},
            {
                "type": "item.completed",
                "item": {
                    "id": "item_0",
                    "type": "agent_message",
                    "text": json.dumps(output_body),
                },
            },
            {"type": "turn.completed", "usage": {}},
        ]
        return SimpleNamespace(
            returncode=0,
            stdout="".join(json.dumps(event) + "\n" for event in events),
            stderr="",
        )

    monkeypatch.setattr(drafter.shutil, "which", lambda name: str(codex_executable))
    monkeypatch.setattr(drafter.subprocess, "run", fake_run)
    response = drafter.call_codex_cli(
        model="gpt-5.6-sol",
        reasoning_effort="xhigh",
        codex_timeout_seconds=1800,
        sandbox="danger-full-access",
        instructions="instructions\n",
        template_text="template\n",
        case_packet_text="packet\n",
        model_output_schema={"type": "object"},
    )
    command = response["codex_cli"]["command"]
    assert command[:2] == [str(codex_executable.resolve()), "exec"]
    assert command[2:7] == [
        "--strict-config",
        "--disable",
        "shell_tool",
        "--disable",
        "unified_exec",
    ]
    assert "--ignore-user-config" in command
    assert "--ephemeral" in command
    assert command[command.index("--sandbox") + 1] == "danger-full-access"
    assert command[command.index("--model") + 1] == "gpt-5.6-sol"
    assert 'model_reasoning_effort="xhigh"' in command
    assert command[-1] == "-"
    stdin_text = str(observed["stdin_text"])
    manifest = response["codex_cli"]["stdin_bundle"]
    assert (
        manifest["total_sha256"]
        == hashlib.sha256(stdin_text.encode("utf-8")).hexdigest()
    )
    assert manifest["total_size_bytes"] == len(stdin_text.encode("utf-8"))
    assert "text" not in json.dumps(manifest)
