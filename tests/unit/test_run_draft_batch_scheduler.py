from __future__ import annotations

import argparse
import json
import threading
from pathlib import Path
from typing import Any

import pytest

from neurips_ed_track_minimal.scripts import run_draft_batch as subject


def _case(index: int) -> subject.CasePacketInfo:
    return subject.CasePacketInfo(
        path=Path(f"case_{index}/case_packet.md"),
        size_bytes=index + 1,
    )


def _result(case_info: subject.CasePacketInfo, status: str) -> dict[str, Any]:
    return {
        "case_unit_dir": case_info.path.parent.name,
        "case_packet": case_info.path.as_posix(),
        "case_packet_size_bytes": case_info.size_bytes,
        "lane": "regular",
        "status": status,
        "attempts": [],
        "quality_warnings": [],
    }


def test_bounded_scheduler_stops_submitting_but_drains_running_cases() -> None:
    cases = [_case(index) for index in range(5)]
    initial_window = threading.Barrier(2)
    release_running_success = threading.Event()
    started: list[str] = []
    recorded: list[tuple[str, str]] = []
    lock = threading.Lock()

    def worker(case_info: subject.CasePacketInfo) -> dict[str, Any]:
        with lock:
            started.append(case_info.path.parent.name)
        initial_window.wait(timeout=5)
        if case_info.path.parent.name == "case_0":
            return _result(case_info, "failed")
        assert release_running_success.wait(timeout=5)
        return _result(case_info, "success")

    def record(
        case_info: subject.CasePacketInfo,
        outcome: dict[str, Any] | Exception,
    ) -> bool:
        assert isinstance(outcome, dict)
        status = str(outcome["status"])
        recorded.append((case_info.path.parent.name, status))
        if status == "failed":
            release_running_success.set()
            return True
        return False

    not_submitted = subject.run_lane_bounded(
        lane_cases=cases,
        max_parallel=2,
        worker=worker,
        record_result=record,
        fail_fast=True,
    )

    assert set(started) == {"case_0", "case_1"}
    assert set(recorded) == {("case_0", "failed"), ("case_1", "success")}
    assert [info.path.parent.name for info in not_submitted] == [
        "case_2",
        "case_3",
        "case_4",
    ]


def test_bounded_scheduler_success_path_completes_every_case() -> None:
    cases = [_case(index) for index in range(7)]
    recorded: list[str] = []
    active = 0
    max_active = 0
    lock = threading.Lock()
    initial_window = threading.Barrier(3)

    def worker(case_info: subject.CasePacketInfo) -> dict[str, Any]:
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        if case_info.path.parent.name in {"case_0", "case_1", "case_2"}:
            initial_window.wait(timeout=5)
        with lock:
            active -= 1
        return _result(case_info, "success")

    def record(
        case_info: subject.CasePacketInfo,
        outcome: dict[str, Any] | Exception,
    ) -> bool:
        assert isinstance(outcome, dict)
        recorded.append(case_info.path.parent.name)
        return False

    not_submitted = subject.run_lane_bounded(
        lane_cases=cases,
        max_parallel=3,
        worker=worker,
        record_result=record,
        fail_fast=True,
    )

    assert not not_submitted
    assert set(recorded) == {f"case_{index}" for index in range(7)}
    assert max_active == 3


def test_main_fail_fast_summary_lists_unsubmitted_cases(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    packet_root = tmp_path / "packets"
    output_root = tmp_path / "outputs"
    for index in range(5):
        case_dir = packet_root / f"case_{index}"
        case_dir.mkdir(parents=True)
        (case_dir / "case_packet.md").write_text(f"case {index}\n", encoding="utf-8")

    args = argparse.Namespace(
        case_packet_root=packet_root,
        output_root=output_root,
        model="test-model",
        provider="openai",
        reasoning_effort="high",
        token_budgets="12000,16000,20000",
        max_parallel=2,
        large_max_parallel=2,
        large_case_threshold_bytes=100_000,
        http_timeout_seconds=180,
        large_http_timeout_seconds=480,
        codex_timeout_seconds=1800,
        large_codex_timeout_seconds=3600,
        codex_sandbox="danger-full-access",
        prompt_supplement=None,
        sort_by="name",
        sleep_seconds=0.0,
        quality_check="none",
        appworld_v56_runtime_gate=False,
        limit=None,
        case_ids=None,
        appworld_v56_canary_round=None,
        force=True,
        fail_fast=True,
        dry_run=False,
    )
    monkeypatch.setattr(subject, "parse_args", lambda: args)
    monkeypatch.setattr(
        subject.drafter,
        "resolve_provider_credentials",
        lambda provider, model: ("test-key", "TEST_KEY", provider, model),
    )

    initial_window = threading.Barrier(2)
    release_running_success = threading.Event()
    started: list[str] = []
    started_lock = threading.Lock()

    def fake_process_case(
        *,
        case_info: subject.CasePacketInfo,
        lane: str,
        **_: Any,
    ) -> dict[str, Any]:
        with started_lock:
            started.append(case_info.path.parent.name)
        initial_window.wait(timeout=5)
        if case_info.path.parent.name == "case_0":
            return {**_result(case_info, "failed"), "lane": lane}
        assert release_running_success.wait(timeout=5)
        return {**_result(case_info, "success"), "lane": lane}

    original_append = subject.append_jsonl

    def append_and_release(
        path: Path,
        payload: dict[str, Any],
        lock: threading.Lock,
    ) -> None:
        original_append(path, payload, lock)
        if payload["status"] == "failed":
            release_running_success.set()

    monkeypatch.setattr(subject, "process_case", fake_process_case)
    monkeypatch.setattr(subject, "append_jsonl", append_and_release)

    assert subject.main() == 1

    summary = json.loads((output_root / "_batch_summary.json").read_text())
    rows = [
        json.loads(line)
        for line in (output_root / "_batch_results.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert set(started) == {"case_0", "case_1"}
    assert {row["case_unit_dir"] for row in rows} == {"case_0", "case_1"}
    assert summary["completed_cases"] == 2
    assert summary["success_cases"] == 1
    assert summary["failed_cases"] == 1
    assert summary["not_run_case_count"] == 3
    assert summary["not_run_case_ids"] == ["case_2", "case_3", "case_4"]
    assert summary["completed_cases"] + summary["not_run_case_count"] == 5
