from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from evidence_system.contracts import appworld_refreeze_v56 as refreeze
from evidence_system.contracts.common import ContractLifecycleError


class _Clock:
    def __init__(self) -> None:
        self.value = 0.0
        self.epoch = datetime(2026, 7, 16, tzinfo=timezone.utc)

    def monotonic(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.value += seconds

    def now(self) -> datetime:
        return self.epoch + timedelta(seconds=self.value)


def test_canonical_repo_path_rejects_alias_absolute_and_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(refreeze, "repo_root", lambda: tmp_path)
    (tmp_path / "real").mkdir()
    (tmp_path / "link").symlink_to(tmp_path / "real", target_is_directory=True)

    assert refreeze._canonical_repo_relative("real", require_exists=True) == Path(
        "real"
    )
    for value in ("real/../real", "./real", str(tmp_path / "real"), "link"):
        with pytest.raises(ContractLifecycleError):
            refreeze._canonical_repo_relative(value, require_exists=True)


def test_tree_descriptor_rejects_symlink_and_hashes_empty_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(refreeze, "repo_root", lambda: tmp_path)
    root = tmp_path / "tree"
    (root / "empty").mkdir(parents=True)
    (root / "data.txt").write_text("one", encoding="utf-8")
    before = refreeze._tree_descriptor("tree")
    (root / "data.txt").write_text("two", encoding="utf-8")
    after = refreeze._tree_descriptor("tree")
    assert before["inventory_sha256"] == after["inventory_sha256"]
    assert before["tree_sha256"] != after["tree_sha256"]
    (root / "alias").symlink_to(root / "data.txt")
    with pytest.raises(ContractLifecycleError, match="symlink"):
        refreeze._tree_descriptor("tree")


def test_exclusive_writer_never_overwrites(tmp_path: Path) -> None:
    output = tmp_path / "ledger.json"
    refreeze._write_json_exclusive(output, {"version": 1})
    original = output.read_bytes()
    with pytest.raises(ContractLifecycleError, match="overwrite"):
        refreeze._write_json_exclusive(output, {"version": 2})
    assert output.read_bytes() == original


def test_freeze_observes_window_writes_once_and_verifies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(refreeze, "repo_root", lambda: tmp_path)
    root = tmp_path / refreeze.DEFAULT_MATERIALIZATION_ROOT
    (root / "provenance").mkdir(parents=True)
    snapshot = {
        "scope": {
            "extension_case_count": 485,
            "extension_case_count_by_dataset": {
                "test_normal": 68,
                "test_challenge": 417,
            },
        },
        "packet_audit": {
            "lane_counts": {"regular": 1, "oversized": 484},
            "registered_test_count": 3817,
        },
        "input_graph": {
            "protocol_files": {"prompt": {"sha256": "a" * 64}},
            "implementation_files": {"code": {"sha256": "b" * 64}},
        },
    }
    monkeypatch.setattr(refreeze, "_build_snapshot", lambda *_: snapshot)
    monkeypatch.setattr(
        refreeze,
        "_shared_code_probe",
        lambda: {
            "protocol_files": snapshot["input_graph"]["protocol_files"],
            "implementation_files": snapshot["input_graph"]["implementation_files"],
        },
    )
    clock = _Clock()
    frozen = refreeze.freeze_appworld_definition_v56(
        stability_window_seconds=60,
        _minimum_stability_seconds=0,
        _sleep=clock.sleep,
        _monotonic=clock.monotonic,
        _now=clock.now,
    )
    assert frozen["action"] == "frozen"
    assert frozen["case_count"] == 485
    ledger = refreeze._load_mapping(
        root / "provenance" / refreeze.LEDGER_BASENAME, "test ledger"
    )
    assert [
        sample["target_offset_seconds"]
        for sample in ledger["stability_window"]["samples"]
    ] == [0, 10, 20, 30, 40, 50, 60]
    verified = refreeze.verify_appworld_definition_refreeze_v56()
    assert verified["action"] == "verified"
    with pytest.raises(ContractLifecycleError, match="cannot be reused"):
        refreeze.freeze_appworld_definition_v56(
            stability_window_seconds=0,
            _minimum_stability_seconds=0,
            _sleep=clock.sleep,
            _monotonic=clock.monotonic,
            _now=clock.now,
        )


def test_freeze_consumes_no_namespace_when_snapshot_drifts_before_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(refreeze, "repo_root", lambda: tmp_path)
    root = tmp_path / refreeze.DEFAULT_MATERIALIZATION_ROOT
    (root / "provenance").mkdir(parents=True)
    snapshots = iter(({"version": 1}, {"version": 2}))
    monkeypatch.setattr(refreeze, "_build_snapshot", lambda *_: next(snapshots))
    monkeypatch.setattr(refreeze, "_shared_code_probe", lambda: {"stable": True})
    clock = _Clock()
    with pytest.raises(ContractLifecycleError, match="changed during stability window"):
        refreeze.freeze_appworld_definition_v56(
            stability_window_seconds=60,
            _minimum_stability_seconds=0,
            _sleep=clock.sleep,
            _monotonic=clock.monotonic,
            _now=clock.now,
        )
    assert not (root / "provenance" / refreeze.LEDGER_BASENAME).exists()


def test_freeze_detects_transient_shared_code_drift_at_ten_second_sample(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(refreeze, "repo_root", lambda: tmp_path)
    root = tmp_path / refreeze.DEFAULT_MATERIALIZATION_ROOT
    (root / "provenance").mkdir(parents=True)
    monkeypatch.setattr(refreeze, "_build_snapshot", lambda *_: {"stable": True})
    probes = iter(({"code": "v1"}, {"code": "v2"}))
    monkeypatch.setattr(refreeze, "_shared_code_probe", lambda: next(probes))
    clock = _Clock()
    with pytest.raises(ContractLifecycleError, match="shared implementation/protocol"):
        refreeze.freeze_appworld_definition_v56(
            stability_window_seconds=60,
            _minimum_stability_seconds=0,
            _sleep=clock.sleep,
            _monotonic=clock.monotonic,
            _now=clock.now,
        )
    assert clock.value == 10
    assert not (root / "provenance" / refreeze.LEDGER_BASENAME).exists()


def test_materialization_closure_rejects_unlisted_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(refreeze, "repo_root", lambda: tmp_path)
    root_relative = refreeze.DEFAULT_MATERIALIZATION_ROOT
    root = tmp_path / root_relative
    (root / "provenance").mkdir(parents=True)
    (root / "provenance/acceptance_report.json").write_text("{}", encoding="utf-8")
    (root / "unexpected.txt").write_text("drift", encoding="utf-8")
    with pytest.raises(ContractLifecycleError, match="file closure mismatch"):
        refreeze._validate_materialization_closure(
            root_relative=root_relative,
            ledger_relative=root_relative / "provenance" / refreeze.LEDGER_BASENAME,
            case_ids=[],
        )


def test_materialization_closure_excludes_only_canonical_ledger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(refreeze, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(refreeze, "EXPECTED_EXTENSION_COUNT", 1)
    monkeypatch.setattr(refreeze, "EXPECTED_FILES_PER_TASK", 1)
    monkeypatch.setattr(refreeze, "REQUIRED_TASK_FILES", ("specs.json",))
    root_relative = refreeze.DEFAULT_MATERIALIZATION_ROOT
    root = tmp_path / root_relative
    case_id = "abcdef0_1"
    files = set(refreeze._MATERIALIZATION_FIXED_FILES)
    files.update(
        {
            f"case_packets/appworld/{case_id}/case_packet.md",
            f"case_packets/appworld/{case_id}/raw_case_manifest.json",
            f"case_packets/appworld/{case_id}/raw_case/official/specs.json",
        }
    )
    for relative in files:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative, encoding="utf-8")
    ledger_relative = root_relative / "provenance" / refreeze.LEDGER_BASENAME
    before = refreeze._validate_materialization_closure(
        root_relative=root_relative,
        ledger_relative=ledger_relative,
        case_ids=[case_id],
    )
    (tmp_path / ledger_relative).write_text("ledger", encoding="utf-8")
    after = refreeze._validate_materialization_closure(
        root_relative=root_relative,
        ledger_relative=ledger_relative,
        case_ids=[case_id],
    )
    assert before == after
    (root / "unexpected_empty_directory").mkdir()
    with pytest.raises(ContractLifecycleError, match="directory closure mismatch"):
        refreeze._validate_materialization_closure(
            root_relative=root_relative,
            ledger_relative=ledger_relative,
            case_ids=[case_id],
        )
