from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from scripts import consolidate_draft_batches as subject


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _write_case(
    root: Path,
    case_id: str,
    *,
    attempt_index: int = 1,
    missing_suffix: str | None = None,
    mismatched_attempt_suffix: str | None = None,
) -> None:
    case_dir = root / case_id
    case_dir.mkdir(parents=True)
    prefix = f"attempt_{attempt_index:02d}"
    for suffix in subject.CANONICAL_SUFFIXES:
        if suffix == missing_suffix:
            continue
        canonical = f"{case_id}:{suffix}\n".encode()
        (case_dir / suffix).write_bytes(canonical)
        attempt = canonical
        if suffix == mismatched_attempt_suffix:
            attempt = b"not-the-promoted-bytes\n"
        (case_dir / f"{prefix}.{suffix}").write_bytes(attempt)
    (case_dir / "nested").mkdir()
    (case_dir / "nested" / "provenance.txt").write_text(
        f"source={root.name}\n", encoding="utf-8"
    )


def _row(case_id: str, status: str, *, attempt_index: int = 1) -> dict[str, Any]:
    return {
        "case_unit_dir": case_id,
        "case_packet": f"packets/{case_id}/case_packet.md",
        "status": status,
        "attempts": (
            [{"attempt_index": attempt_index, "returncode": 0, "validator": "ok"}]
            if status == "success"
            else []
        ),
        "quality_warnings": [],
    }


def _write_batch(
    root: Path,
    rows: list[dict[str, Any]],
    *,
    not_run: list[str] | None = None,
    create_accepted_cases: bool = True,
) -> None:
    root.mkdir(parents=True)
    not_run = not_run or []
    (root / subject.RESULTS_NAME).write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    status_counts = {
        status: sum(row["status"] == status for row in rows)
        for status in subject.KNOWN_STATUSES
    }
    summary = {
        "total_cases": len(rows) + len(not_run),
        "completed_cases": len(rows),
        "success_cases": status_counts["success"],
        "skipped_cases": status_counts["skipped_existing"],
        "failed_cases": status_counts["failed"],
        "not_run_case_count": len(not_run),
        "not_run_case_ids": not_run,
    }
    (root / subject.SUMMARY_NAME).write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    if create_accepted_cases:
        for row in rows:
            if row["status"] in subject.ACCEPTED_STATUSES:
                attempt_index = 1
                attempts = row.get("attempts")
                if attempts:
                    attempt_index = attempts[-1]["attempt_index"]
                _write_case(root, row["case_unit_dir"], attempt_index=attempt_index)


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_consolidates_base_success_and_repairs_in_stable_case_order(tmp_path: Path) -> None:
    base = tmp_path / "base"
    repair_one = tmp_path / "repair-one"
    repair_two = tmp_path / "repair-two"
    output = tmp_path / "output"
    manifest_path = tmp_path / "manifest.json"

    _write_batch(
        base,
        [_row("z_base_success", "success"), _row("a_failed", "failed")],
        not_run=["m_not_run"],
    )
    _write_batch(repair_one, [_row("a_failed", "success")])
    _write_batch(repair_two, [_row("m_not_run", "skipped_existing")])
    base_before = _tree_bytes(base)
    repair_one_before = _tree_bytes(repair_one)
    repair_two_before = _tree_bytes(repair_two)

    # A pre-existing output is accepted only when it is still empty.
    output.mkdir()
    manifest = subject.consolidate(
        base_root=base,
        repair_roots=[repair_one, repair_two],
        output_root=output,
        json_manifest=manifest_path,
    )

    rows = [
        json.loads(line)
        for line in (output / subject.RESULTS_NAME).read_text(encoding="utf-8").splitlines()
    ]
    assert [row["case_unit_dir"] for row in rows] == [
        "a_failed",
        "m_not_run",
        "z_base_success",
    ]
    assert [row["status"] for row in rows] == [
        "success",
        "skipped_existing",
        "success",
    ]
    expected_result_bytes = b"".join(_canonical_json(row) + b"\n" for row in rows)
    assert (output / subject.RESULTS_NAME).read_bytes() == expected_result_bytes

    summary = json.loads((output / subject.SUMMARY_NAME).read_text(encoding="utf-8"))
    assert summary["total_cases"] == 3
    assert summary["completed_cases"] == 3
    assert summary["success_cases"] == 2
    assert summary["skipped_cases"] == 1
    assert summary["failed_cases"] == 0
    assert summary["not_run_case_count"] == 0
    assert summary["consolidation"]["source_status_counts"] == {
        "skipped_existing": 1,
        "success": 2,
    }
    assert summary["source_roots"] == [
        str(base.resolve()),
        str(repair_one.resolve()),
        str(repair_two.resolve()),
    ]

    written_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert written_manifest == manifest
    assert [case["case_unit_dir"] for case in manifest["cases"]] == [
        "a_failed",
        "m_not_run",
        "z_base_success",
    ]
    assert [case["source_kind"] for case in manifest["cases"]] == [
        "repair",
        "repair",
        "base",
    ]
    assert all(len(case["row_sha256"]) == 64 for case in manifest["cases"])
    assert all(len(case["case_tree_sha256"]) == 64 for case in manifest["cases"])
    assert manifest["batch_results_sha256"] == hashlib.sha256(expected_result_bytes).hexdigest()

    for case_id in ("a_failed", "m_not_run", "z_base_success"):
        for suffix in subject.CANONICAL_SUFFIXES:
            assert (output / case_id / suffix).is_file()
    assert _tree_bytes(base) == base_before
    assert _tree_bytes(repair_one) == repair_one_before
    assert _tree_bytes(repair_two) == repair_two_before


def test_freezes_complete_base_without_repair_roots(tmp_path: Path) -> None:
    base = tmp_path / "base"
    output = tmp_path / "accepted"
    manifest_path = tmp_path / "accepted.manifest.json"
    _write_batch(base, [_row("case_b", "success"), _row("case_a", "success")])

    manifest = subject.consolidate(
        base_root=base,
        repair_roots=[],
        output_root=output,
        json_manifest=manifest_path,
    )

    assert manifest["case_count"] == 2
    assert manifest["repair_roots"] == []
    assert [case["case_unit_dir"] for case in manifest["cases"]] == ["case_a", "case_b"]
    summary = json.loads((output / subject.SUMMARY_NAME).read_text(encoding="utf-8"))
    assert summary["success_cases"] == 2
    assert summary["failed_cases"] == 0


def test_rejects_repair_row_for_successful_base_case(tmp_path: Path) -> None:
    base = tmp_path / "base"
    repair = tmp_path / "repair"
    output = tmp_path / "output"
    _write_batch(base, [_row("case_a", "success")])
    _write_batch(repair, [_row("case_a", "success")])

    with pytest.raises(subject.ConsolidationError, match="overwrite successful base"):
        subject.consolidate(
            base_root=base,
            repair_roots=[repair],
            output_root=output,
            json_manifest=tmp_path / "manifest.json",
        )

    assert not output.exists()


def test_rejects_multiple_successful_repairs_for_one_base_failure(tmp_path: Path) -> None:
    base = tmp_path / "base"
    repair_one = tmp_path / "repair-one"
    repair_two = tmp_path / "repair-two"
    _write_batch(base, [_row("case_a", "failed")])
    _write_batch(repair_one, [_row("case_a", "success")])
    _write_batch(repair_two, [_row("case_a", "skipped_existing")])

    with pytest.raises(subject.ConsolidationError, match="multiple successful repair rows"):
        subject.consolidate(
            base_root=base,
            repair_roots=[repair_one, repair_two],
            output_root=tmp_path / "output",
            json_manifest=tmp_path / "manifest.json",
        )


def test_rejects_duplicate_rows_and_unclosed_base_coverage(tmp_path: Path) -> None:
    duplicate_base = tmp_path / "duplicate-base"
    repair = tmp_path / "repair"
    row = _row("case_a", "failed")
    _write_batch(duplicate_base, [row])
    with (duplicate_base / subject.RESULTS_NAME).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")
    _write_batch(repair, [_row("case_a", "success")])

    with pytest.raises(subject.ConsolidationError, match="duplicate case_unit_dir"):
        subject.consolidate(
            base_root=duplicate_base,
            repair_roots=[repair],
            output_root=tmp_path / "duplicate-output",
            json_manifest=tmp_path / "duplicate-manifest.json",
        )

    coverage_base = tmp_path / "coverage-base"
    _write_batch(coverage_base, [_row("case_a", "failed")])
    summary_path = coverage_base / subject.SUMMARY_NAME
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["total_cases"] = 2
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    with pytest.raises(subject.ConsolidationError, match="coverage does not close"):
        subject.consolidate(
            base_root=coverage_base,
            repair_roots=[repair],
            output_root=tmp_path / "coverage-output",
            json_manifest=tmp_path / "coverage-manifest.json",
        )


@pytest.mark.parametrize(
    ("missing_suffix", "mismatched_attempt_suffix", "message"),
    [
        ("reasoning_summary.txt", None, "lacks complete canonical sidecars"),
        (None, "llm_call.json", "not byte-identical"),
    ],
)
def test_rejects_incomplete_or_unpromoted_canonical_artifacts(
    tmp_path: Path,
    missing_suffix: str | None,
    mismatched_attempt_suffix: str | None,
    message: str,
) -> None:
    base = tmp_path / "base"
    repair = tmp_path / "repair"
    _write_batch(base, [_row("case_a", "success")], create_accepted_cases=False)
    _write_case(
        base,
        "case_a",
        missing_suffix=missing_suffix,
        mismatched_attempt_suffix=mismatched_attempt_suffix,
    )
    _write_batch(repair, [], not_run=[])

    with pytest.raises(subject.ConsolidationError, match=message):
        subject.consolidate(
            base_root=base,
            repair_roots=[repair],
            output_root=tmp_path / "output",
            json_manifest=tmp_path / "manifest.json",
        )


def test_success_promotion_must_match_final_attempt_not_earlier_returncode_zero(
    tmp_path: Path,
) -> None:
    base = tmp_path / "base"
    repair = tmp_path / "repair"
    row = _row("case_a", "success")
    row["attempts"] = [
        {"attempt_index": 1, "returncode": 0, "validator": "failed"},
        {"attempt_index": 2, "returncode": 0, "validator": "passed"},
    ]
    _write_batch(base, [row])
    case_dir = base / "case_a"
    for suffix in subject.CANONICAL_SUFFIXES:
        earlier_bytes = f"earlier:{suffix}\n".encode()
        (case_dir / f"attempt_01.{suffix}").write_bytes(earlier_bytes)
        (case_dir / suffix).write_bytes(earlier_bytes)
    _write_batch(repair, [])

    with pytest.raises(subject.ConsolidationError, match="final successful attempt"):
        subject.consolidate(
            base_root=base,
            repair_roots=[repair],
            output_root=tmp_path / "output",
            json_manifest=tmp_path / "manifest.json",
        )


def test_rejects_nonempty_or_symlink_output_without_changing_sources(tmp_path: Path) -> None:
    base = tmp_path / "base"
    repair = tmp_path / "repair"
    _write_batch(base, [_row("case_a", "failed")])
    _write_batch(repair, [_row("case_a", "success")])
    before = _tree_bytes(base) | {
        f"repair/{name}": value for name, value in _tree_bytes(repair).items()
    }

    nonempty = tmp_path / "nonempty"
    nonempty.mkdir()
    (nonempty / "keep.txt").write_text("do not replace\n", encoding="utf-8")
    with pytest.raises(subject.ConsolidationError, match="must not exist or must be empty"):
        subject.consolidate(
            base_root=base,
            repair_roots=[repair],
            output_root=nonempty,
            json_manifest=tmp_path / "manifest-one.json",
        )
    assert (nonempty / "keep.txt").read_text(encoding="utf-8") == "do not replace\n"

    target = tmp_path / "target"
    target.mkdir()
    symlink_output = tmp_path / "output-link"
    symlink_output.symlink_to(target, target_is_directory=True)
    with pytest.raises(subject.ConsolidationError, match="must not be a symlink"):
        subject.consolidate(
            base_root=base,
            repair_roots=[repair],
            output_root=symlink_output,
            json_manifest=tmp_path / "manifest-two.json",
        )

    after = _tree_bytes(base) | {
        f"repair/{name}": value for name, value in _tree_bytes(repair).items()
    }
    assert after == before


def test_rejects_external_manifest_that_is_output_ancestor(tmp_path: Path) -> None:
    base = tmp_path / "base"
    repair = tmp_path / "repair"
    manifest_as_directory = tmp_path / "future-container"
    _write_batch(base, [_row("case_a", "failed")])
    _write_batch(repair, [_row("case_a", "success")])

    with pytest.raises(subject.ConsolidationError, match="cannot be an ancestor"):
        subject.consolidate(
            base_root=base,
            repair_roots=[repair],
            output_root=manifest_as_directory / "output",
            json_manifest=manifest_as_directory,
        )

    assert not manifest_as_directory.exists()


def test_external_manifest_commit_is_no_clobber_and_precedes_output_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = tmp_path / "base"
    repair = tmp_path / "repair"
    output = tmp_path / "output"
    manifest = tmp_path / "manifest.json"
    _write_batch(base, [_row("case_a", "failed")])
    _write_batch(repair, [_row("case_a", "success")])

    def racing_link(_: Path, destination: Path) -> None:
        Path(destination).write_text("racer-won\n", encoding="utf-8")
        raise FileExistsError(destination)

    monkeypatch.setattr(subject.os, "link", racing_link)
    with pytest.raises(subject.ConsolidationError, match="appeared before commit"):
        subject.consolidate(
            base_root=base,
            repair_roots=[repair],
            output_root=output,
            json_manifest=manifest,
        )

    assert not output.exists()
    assert manifest.read_text(encoding="utf-8") == "racer-won\n"


def test_manifest_can_commit_inside_output_root(tmp_path: Path) -> None:
    base = tmp_path / "base"
    repair = tmp_path / "repair"
    output = tmp_path / "output"
    _write_batch(base, [_row("case_a", "failed")])
    _write_batch(repair, [_row("case_a", "success")])

    result = subject.consolidate(
        base_root=base,
        repair_roots=[repair],
        output_root=output,
        json_manifest=output / "consolidation_manifest.json",
    )

    assert json.loads((output / "consolidation_manifest.json").read_text()) == result
