from __future__ import annotations

from argparse import Namespace
import copy
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts/audit_four_benchmark_drafts.py"
SPEC = importlib.util.spec_from_file_location("audit_four_benchmark_drafts", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit
SPEC.loader.exec_module(audit)


def test_case_prompt_supplements_are_keyed_and_resolved(tmp_path: Path) -> None:
    supplement = tmp_path / "repair.md"
    args = Namespace(
        case_prompt_supplement=[
            ["terminal_bench_2_1", "case-1", str(supplement)],
        ]
    )
    assert audit._case_prompt_supplements_from_args(args) == {
        ("terminal_bench_2_1", "case-1"): supplement.resolve()
    }


def test_case_prompt_supplements_reject_duplicate_case(tmp_path: Path) -> None:
    args = Namespace(
        case_prompt_supplement=[
            ["terminal_bench_2_1", "case-1", str(tmp_path / "one.md")],
            ["terminal_bench_2_1", "case-1", str(tmp_path / "two.md")],
        ]
    )
    try:
        audit._case_prompt_supplements_from_args(args)
    except SystemExit as exc:
        assert "Duplicate" in str(exc)
    else:
        raise AssertionError("duplicate case supplement was accepted")


def _checklist(*, undecided_text: str, native_overrides: dict | None = None) -> dict:
    native = {
        "user_goal": {"text": "Do the task", "rationale": "Task", "support": ["case_packet.md::Case Metadata"]},
        "benchmark_success": {
            "text": "The verifier tests pass and reward.txt equals 1",
            "rationale": "Native rule",
            "support": ["official/tests/test.sh::L1-L2"],
        },
        "checked_by": {
            "text": "Official verifier",
            "rationale": "Checker",
            "support": ["official/tests/test.sh::L1-L2"],
        },
        "decisive_artifacts": [
            {
                "artifact": "reward.txt and ctrf.json verifier test report",
                "question": "Do all tests pass and is reward 1?",
                "support": ["official/tests/test.sh::L1-L2"],
            }
        ],
        "success_if": [
            {
                "text": "All verifier tests pass and reward.txt is 1",
                "rationale": "Success",
                "support": ["official/tests/test.sh::L1-L2"],
            }
        ],
        "fail_if": [
            {
                "text": "A verifier test fails and reward.txt is 0",
                "rationale": "Failure",
                "support": ["official/tests/test.sh::L1-L2"],
            }
        ],
        "undecided_if": [
            {
                "text": undecided_text,
                "rationale": "Evidence rule",
                "support": ["case_packet.md::Visibility Boundary"],
            }
        ],
    }
    native.update(native_overrides or {})
    return {
        "schema_version": "case_checklist_v1",
        "case_unit_id": "case-1",
        "domain": "terminal_bench_2_1",
        "task_id": "terminal-bench/case-1",
        "native": native,
        "stronger": {"additional_conditions": []},
    }


def test_prior_run_assertion_is_flagged_but_boundary_statement_is_not() -> None:
    asserted = _checklist(undecided_text="The retained evaluator output is missing")
    asserted["native"]["benchmark_success"]["text"] = (
        "The public run achieved a score of 1.0."
    )
    assert audit.prior_run_findings(asserted)

    boundary = _checklist(undecided_text="The retained evaluator output is missing")
    boundary["native"]["benchmark_success"]["text"] = (
        "Do not assume that a prior run passed; score only future retained evidence."
    )
    assert audit.prior_run_findings(boundary) == []

    evidence_question = _checklist(
        undecided_text="The retained evaluator output is missing"
    )
    evidence_question["native"]["decisive_artifacts"][0]["question"] = (
        "Does the trajectory show a completed measurement and its observed output?"
    )
    evidence_question["native"]["success_if"][0]["text"] = (
        "A consistent retained evaluator result reports exactly 1.0."
    )
    assert audit.prior_run_findings(evidence_question) == []


def test_prior_output_backward_compatibility_is_not_a_prior_run_result() -> None:
    checklist = _checklist(
        undecided_text="The retained evaluator output is missing"
    )
    checklist["stronger"]["additional_conditions"] = [
        {
            "id": "compatibility",
            "text": "Valid packets preserve the prior output structure and error format.",
            "rationale": "The official task requires backward compatibility.",
            "support": ["official/huggingface/task_visible.json::requirements"],
            "decisive_artifacts": [],
        }
    ]
    assert audit.prior_run_findings(checklist) == []


def test_undecided_requires_evidence_insufficiency() -> None:
    ordinary_failure = _checklist(undecided_text="A verifier test fails")
    codes = {item["code"] for item in audit.undecided_findings(ordinary_failure)}
    assert "undecided_not_evidence_insufficiency" in codes
    assert "ordinary_failure_misclassified_as_undecided" in codes

    evidence_gap = _checklist(
        undecided_text="The retained verifier output is missing or corrupt, so the result cannot be determined"
    )
    assert audit.undecided_findings(evidence_gap) == []


def test_undecided_accepts_conflict_attribution_and_no_score_phrasings() -> None:
    accepted = [
        "Neither result.txt nor runtime.log unambiguously establishes the final official evaluator score.",
        "The retained records and artifacts conflict about the run outcome.",
        "No valid evaluator score is retained and the remaining artifacts do not establish a final outcome.",
        "The artifacts conflict and their attribution or integrity cannot be resolved.",
        "Neither success nor failure can be established because the reward or CTRF report is missing, incomplete, not attributable to the same completed run, or mutually inconsistent.",
        "No complete, readable parsed_test_output.json from the run is retained, so the required set-inclusion relation cannot be determined.",
    ]
    for text in accepted:
        checklist = _checklist(undecided_text=text)
        assert audit.undecided_findings(checklist) == [], text


def test_swe_bench_pro_accepts_equivalent_set_rule_wording_and_solution_exclusion() -> None:
    checklist = _checklist(
        undecided_text=(
            "No complete, readable parsed_test_output.json is retained, so the "
            "required set-inclusion relation cannot be determined."
        )
    )
    checklist["domain"] = "swe_bench_pro"
    checklist["native"]["benchmark_success"]["text"] = (
        "Every named FAIL_TO_PASS and PASS_TO_PASS test appears PASSED in parsed "
        "evaluator output. The submission is not compared with the official solution patch."
    )
    checklist["native"]["success_if"][0]["text"] = (
        "Every exact test in both official lists appears PASSED in parsed output."
    )
    checklist["native"]["fail_if"][0]["text"] = (
        "A complete parsed output omits a required test or records a status other than PASSED."
    )
    checklist["native"]["decisive_artifacts"][0]["artifact"] = (
        "parsed official evaluator test output"
    )
    codes = {
        finding["code"]
        for finding in audit.domain_semantic_findings("swe_bench_pro", checklist)
    }
    assert codes == set()


def test_terminal_bench_baseline_accepts_reward_and_verifier_contract() -> None:
    checklist = _checklist(
        undecided_text="The retained verifier output is missing or corrupt, so the result cannot be determined"
    )
    assert audit.domain_semantic_findings("terminal_bench_2_1", checklist) == []


def test_terminal_bench_accepts_complete_final_artifact_reconstruction() -> None:
    checklist = _checklist(
        undecided_text="The retained final result is missing or unreadable",
        native_overrides={
            "benchmark_success": {
                "text": (
                    "Every released pytest check passes, after which test.sh writes "
                    "reward.txt = 1."
                ),
                "support": [
                    "official/tests/test.sh::lines 1-8",
                    "official/tests/test_outputs.py::test_result",
                ],
            },
            "checked_by": {
                "text": "The official pytest verifier and reward wrapper.",
                "support": ["official/tests/test.sh::lines 1-8"],
            },
            "decisive_artifacts": [
                {
                    "artifact": "/app/result.json full final contents",
                    "question": "Does the parsed value equal the released expected value?",
                    "support": ["official/tests/test_outputs.py::test_result"],
                }
            ],
            "success_if": [
                {
                    "text": "/app/result.json exists and its parsed value is exactly 7.",
                    "support": ["official/tests/test_outputs.py::test_result"],
                }
            ],
            "fail_if": [
                {
                    "text": "The final file is absent, invalid JSON, or its value differs from 7.",
                    "support": ["official/tests/test_outputs.py::test_result"],
                }
            ],
        },
    )
    assert audit.domain_semantic_findings("terminal_bench_2_1", checklist) == []


def test_terminal_bench_final_artifact_reconstruction_still_requires_test_grounding() -> None:
    checklist = _checklist(
        undecided_text="The retained final result is missing or unreadable"
    )
    checklist["native"]["success_if"][0]["support"] = [
        "official/instruction.md::lines 1-2"
    ]
    checklist["native"]["fail_if"][0]["support"] = [
        "official/instruction.md::lines 1-2"
    ]
    checklist["native"]["decisive_artifacts"][0]["support"] = [
        "official/instruction.md::lines 1-2"
    ]
    codes = {
        item["code"]
        for item in audit.domain_semantic_findings("terminal_bench_2_1", checklist)
    }
    assert codes == {
        "terminal_bench_success_basis_missing",
        "terminal_bench_failure_basis_missing",
        "terminal_bench_decisive_basis_missing",
    }


def test_terminal_bench_test_composition_uses_function_or_line_span_support(
    tmp_path: Path,
) -> None:
    packet_path = tmp_path / "case_packet.md"
    packet_path.write_text("# packet\n", encoding="utf-8")
    tests_path = tmp_path / "raw_case" / "official" / "tests" / "test_outputs.py"
    tests_path.parent.mkdir(parents=True)
    tests_path.write_text(
        "def test_first():\n    assert True\n\n"
        "def test_second():\n    assert True\n",
        encoding="utf-8",
    )
    checklist = _checklist(
        undecided_text="The retained verifier output is missing or corrupt"
    )
    checklist["native"]["benchmark_success"]["support"] = [
        "official/tests/test.sh::lines 1-8",
        "official/tests/test_outputs.py::test_first",
    ]
    findings = audit.domain_semantic_findings(
        "terminal_bench_2_1", checklist, packet_path
    )
    composition = [
        item for item in findings if item["code"] == "terminal_bench_test_composition_incomplete"
    ]
    assert len(composition) == 1
    assert "test_second" in composition[0]["message"]
    assert "test_first" not in composition[0]["message"]

    checklist["native"]["benchmark_success"]["support"] = [
        "official/tests/test.sh::lines 1-8",
        "official/tests/test_outputs.py::lines 1-5",
    ]
    codes = {
        item["code"]
        for item in audit.domain_semantic_findings(
            "terminal_bench_2_1", checklist, packet_path
        )
    }
    assert "terminal_bench_test_composition_incomplete" not in codes


def test_osworld_success_rule_accepts_official_outcome_wording() -> None:
    checklist = _checklist(
        undecided_text="No valid evaluator score is retained and the artifacts conflict"
    )
    checklist["native"]["benchmark_success"]["text"] = (
        "The official evaluator returns exactly 1.0 when every configured rule passes."
    )
    checklist["native"]["success_if"][0]["text"] = (
        "The retained official evaluator outcome is exactly 1.0, corroborated by both configured rules."
    )
    checklist["native"]["fail_if"][0]["text"] = (
        "The official evaluator returns a non-1.0 score or any configured rule fails."
    )
    checklist["native"]["decisive_artifacts"][0]["artifact"] = (
        "result.txt official evaluator result"
    )
    codes = {
        finding["code"]
        for finding in audit.domain_semantic_findings("osworld_verified", checklist)
    }
    assert "osworld_verified_success_rule_unclear" not in codes


def _osworld2_checklist() -> dict:
    checklist = _checklist(
        undecided_text="The retained authorized evaluator result is missing or corrupt"
    )
    checklist["domain"] = "osworld_2_0"
    checklist["native"]["user_goal"]["support"] = [
        "derived/agent_visible_task.json::$.instruction"
    ]
    for field in (
        "benchmark_success",
        "checked_by",
        "decisive_artifacts",
        "success_if",
        "fail_if",
    ):
        value = checklist["native"][field]
        items = value if isinstance(value, list) else [value]
        for item in items:
            item["support"] = ["authorized/official_task.py::Task.evaluate"]
    checklist["native"]["benchmark_success"]["text"] = (
        "The authorized official evaluator returns its native successful result."
    )
    checklist["native"]["decisive_artifacts"][0]["artifact"] = (
        "result.json authorized evaluator result"
    )
    return checklist


def _osworld2_packet(tmp_path: Path, *, include_controller: bool = True) -> Path:
    sources = [
        "derived/agent_visible_task.json",
        "authorized/official_task.py",
    ]
    if include_controller:
        sources.append("controller/gated_source_pointer.json")
    packet_path = tmp_path / "case_packet.md"
    inventory = "\n".join(f"- `{source}`" for source in sources)
    sections = "\n\n".join(f"### `{source}`\n\nsource" for source in sources)
    packet_path.write_text(
        f"# Case Packet\n\n## Source Inventory\n\n{inventory}"
        f"\n\n## Packet Source Files\n\n{sections}\n",
        encoding="utf-8",
    )
    return packet_path


def test_osworld2_source_roles_accept_equivalent_goal_source_and_authorized_native_support(
    tmp_path: Path,
) -> None:
    packet_path = _osworld2_packet(tmp_path)
    checklist = _osworld2_checklist()
    role_codes = {
        finding["code"]
        for finding in audit.domain_semantic_findings(
            "osworld_2_0", checklist, packet_path
        )
        if finding["code"].startswith("osworld_2_")
    }
    assert role_codes == set()

    checklist["native"]["user_goal"]["support"] = [
        "authorized/official_task.py::Task.instruction"
    ]
    role_codes = {
        finding["code"]
        for finding in audit.domain_semantic_findings(
            "osworld_2_0", checklist, packet_path
        )
        if finding["code"].startswith("osworld_2_")
    }
    assert role_codes == set()


def test_osworld2_source_roles_reject_missing_authorized_native_support(
    tmp_path: Path,
) -> None:
    checklist = _osworld2_checklist()
    checklist["native"]["fail_if"][0]["support"] = [
        "derived/agent_visible_task.json::$.instruction"
    ]
    findings = audit.domain_semantic_findings(
        "osworld_2_0", checklist, _osworld2_packet(tmp_path)
    )
    matching = [
        finding
        for finding in findings
        if finding["code"] == "osworld_2_required_source_roles_missing"
    ]
    assert len(matching) == 1
    assert "fail_if" in matching[0]["message"]


def test_osworld2_gated_boundary_is_verified_from_packet_provenance(
    tmp_path: Path,
) -> None:
    checklist = _osworld2_checklist()
    checklist["native"]["checked_by"]["text"] = (
        "The gated authorized controller-side official evaluator."
    )
    codes = {
        finding["code"]
        for finding in audit.domain_semantic_findings(
            "osworld_2_0",
            checklist,
            _osworld2_packet(tmp_path, include_controller=False),
        )
    }
    assert "osworld_2_gated_evaluator_boundary_missing" in codes

    checklist["native"]["success_if"][0]["text"] = (
        "Run-matched evidence shows that `DesktopEnv.evaluate` returned exactly `1.0`."
    )
    codes = {
        finding["code"]
        for finding in audit.domain_semantic_findings("osworld_verified", checklist)
    }
    assert "osworld_verified_success_rule_unclear" not in codes


def test_namespaced_and_exact_output_names_are_supported() -> None:
    assert audit._candidate_output_names("swe_bench_pro", "instance-1") == (
        "instance-1",
        "swe_bench_pro__instance-1",
    )


def test_codex_event_stream_still_rejects_tool_items(tmp_path: Path) -> None:
    checklist = _checklist(
        undecided_text="No valid evaluator score is retained and the artifacts conflict"
    )
    packet = audit.PacketInfo(
        case_unit_id="case-1",
        task_id="terminal-bench/case-1",
        domain="terminal_bench_2_1",
        directory_name="case-1",
        path=tmp_path / "case_packet.md",
        text="# packet\n",
        sha256="0" * 64,
    )
    recorder = audit.CaseAudit("terminal_bench_2_1", packet, tmp_path)
    body = {"native": checklist["native"], "stronger": checklist["stronger"]}
    output_text = json.dumps(body)
    events = [
        {
            "type": "item.completed",
            "item": {"id": "item_0", "type": "command_execution", "command": "pwd"},
        },
        {
            "type": "item.completed",
            "item": {"id": "item_1", "type": "agent_message", "text": output_text},
        },
    ]
    api_response = {
        "output_text": output_text,
        "output": [
            {"type": "reasoning", "summary": []},
            {"type": "message", "content": [{"type": "output_text", "text": output_text}]},
        ],
    }
    audit._audit_events(
        recorder,
        api_response,
        {"events": events, "malformed_event_lines": []},
        checklist,
        "",
    )
    assert recorder.data["checks"]["codex_event_stream"]["status"] == "failed"
    assert recorder.data["errors"][0]["code"] == "codex_event_stream_invalid"


def test_end_to_end_valid_namespaced_codex_draft_passes(tmp_path: Path) -> None:
    benchmark = "terminal_bench_2_1"
    case_id = "adaptive-rejection-sampler"
    source_case = REPO_ROOT / "experiments/case_packets" / benchmark / case_id
    packet_root = tmp_path / "packets"
    shutil.copytree(source_case, packet_root / case_id)
    packet_path = packet_root / case_id / "case_packet.md"
    packet_text = packet_path.read_text(encoding="utf-8")
    metadata = audit.drafter.extract_case_metadata(packet_text)

    checklist = _checklist(
        undecided_text=(
            "The retained verifier output is missing or corrupt, so the result cannot be determined"
        )
    )
    checklist["native"]["user_goal"].pop("rationale")
    checklist["native"]["benchmark_success"]["support"].append(
        "official/tests/test_outputs.py::lines 1-307"
    )
    checklist["case_unit_id"] = case_id
    checklist["task_id"] = metadata["task_id"]
    case_dir = tmp_path / "drafts" / f"{benchmark}__{case_id}"
    case_dir.mkdir(parents=True)

    checklist_yaml = yaml.safe_dump(
        checklist, sort_keys=False, allow_unicode=True, width=1000
    )
    checklist_json = json.dumps(checklist, indent=2, ensure_ascii=False) + "\n"
    body = {"native": checklist["native"], "stronger": checklist["stronger"]}
    output_text = "\n" + json.dumps(body, ensure_ascii=False, separators=(",", ":")) + "\n"
    event_body = copy.deepcopy(body)
    event_body["native"]["user_goal"]["rationale"] = None
    event_text = json.dumps(event_body, indent=2, ensure_ascii=False)
    events = [
        {"type": "thread.started", "thread_id": "thread-1"},
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {"id": "item_0", "type": "agent_message", "text": event_text},
        },
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 100,
                "cached_input_tokens": 0,
                "output_tokens": 50,
                "reasoning_output_tokens": 0,
                "total_tokens": 150,
            },
        },
    ]
    runtime_root = REPO_ROOT / "neurips_ed_track_minimal"
    packet_info = audit.PacketInfo(
        case_unit_id=case_id,
        task_id=metadata["task_id"],
        domain=benchmark,
        directory_name=case_id,
        path=packet_path,
        text=packet_text,
        sha256=audit._sha256_bytes(packet_text.encode("utf-8")),
    )
    workspace_files = audit._runtime_workspace_files(runtime_root, packet_info, None)
    _, stdin_manifest = audit.drafter.build_codex_stdin_bundle(workspace_files)
    command = [
        "/usr/local/bin/codex",
        "exec",
        "--disable",
        "shell_tool",
        "--disable",
        "unified_exec",
        "--sandbox",
        "read-only",
        "--model",
        "gpt-5.6-sol",
        "-c",
        'model_reasoning_effort="max"',
        "--json",
        "-",
    ]
    api_response = {
        "id": "thread-1",
        "status": "completed",
        "model": "gpt-5.6-sol",
        "provider": "codex_cli",
        "output_text": output_text,
        "output": [
            {"type": "reasoning", "summary": []},
            {"type": "message", "content": [{"type": "output_text", "text": output_text}]},
        ],
        "usage": audit.drafter.normalize_codex_usage(events),
        "codex_cli": {
            "auth_mode": "codex_login",
            "returncode": 0,
            "timeout_seconds": 1800,
            "sandbox": "read-only",
            "command": command,
            "stdin_bundle": stdin_manifest,
            "events": events,
            "malformed_event_lines": [],
            "stderr": "",
        },
    }
    llm_call = audit.drafter.build_llm_call_record(
        provider="codex_cli",
        api_response=api_response,
        api_key_env="CODEX_HOME",
        case_metadata=metadata,
        model="gpt-5.6-sol",
        reasoning_effort="max",
        max_output_tokens=12000,
        temperature=0.0,
        timeout_seconds=1800,
        request_timestamp="2026-07-18T00:00:00+00:00",
        response_timestamp="2026-07-18T00:01:00+00:00",
        raw_api_response_path=case_dir / "attempt_01.api_response.json",
        reasoning_summary_path=case_dir / "attempt_01.reasoning_summary.txt",
    )

    payloads = {
        "checklist.yaml": checklist_yaml,
        "checklist.json": checklist_json,
        "api_response.json": json.dumps(api_response, indent=2) + "\n",
        "llm_call.json": json.dumps(llm_call, indent=2) + "\n",
        "reasoning_summary.txt": "",
        "stderr.log": "",
        "stdout.log": "drafted\n",
    }
    for suffix, text in payloads.items():
        (case_dir / suffix).write_text(text, encoding="utf-8")
        (case_dir / f"attempt_01.{suffix}").write_text(text, encoding="utf-8")

    batch_row = {
        "case_unit_dir": case_dir.name,
        "status": "success",
        "attempts": [{"attempt_index": 1, "returncode": 0}],
    }
    (case_dir.parent / "_batch_results.jsonl").write_text(
        json.dumps(batch_row) + "\n", encoding="utf-8"
    )
    (case_dir.parent / "_batch_summary.json").write_text(
        json.dumps(
            {
                "total_cases": 1,
                "completed_cases": 1,
                "success_cases": 1,
                "failed_cases": 0,
                "not_run_case_count": 0,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    target = audit.TargetSpec(benchmark, packet_root, case_dir.parent)
    report = audit._audit_target(
        target,
        runtime_root=runtime_root,
        prompt_supplement=None,
        expected_provider="codex_cli",
        expected_model="gpt-5.6-sol",
        expected_reasoning="max",
        batch_cache={},
    )
    assert report["status"] == "passed", report
    assert report["case_status_counts"] == {"passed": 1}
