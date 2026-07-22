from __future__ import annotations

import pytest

from scripts import build_terminal_bench_2_1_case_packets as builder


def _locked_fixture(**overrides: object) -> builder.SourceFile:
    values: dict[str, object] = {
        "task_slug": "reshard-c4-data",
        "relative_path": "tests/files_hashes.json",
        "sha256": "8a6b0c533db960d5534d3ab28ff4c683d6b5bca0a486e9a1921509a14db0e2fb",
        "size_bytes": 1_029_394,
        "text": "{}",
    }
    values.update(overrides)
    return builder.SourceFile(**values)  # type: ignore[arg-type]


def test_exact_oversized_fixture_is_metadata_only() -> None:
    policy = builder._metadata_only_text_policy(_locked_fixture())

    assert policy is not None
    assert policy["size_bytes"] == 1_029_394
    assert "not decision logic" in policy["reason"]


@pytest.mark.parametrize(
    ("field", "value"),
    (("size_bytes", 1_029_393), ("sha256", "0" * 64), ("text", None)),
)
def test_oversized_fixture_policy_fails_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError, match="metadata-only text source"):
        builder._metadata_only_text_policy(_locked_fixture(**{field: value}))


def test_unlisted_large_text_remains_materializable() -> None:
    source = builder.SourceFile(
        task_slug="some-other-task",
        relative_path="tests/large.json",
        sha256="1" * 64,
        size_bytes=10_000_000,
        text="{}",
    )

    assert builder._metadata_only_text_policy(source) is None
