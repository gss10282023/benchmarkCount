#!/usr/bin/env python3
"""Strict AndroidWorld adapter over the frozen NeurIPS checklist guardrails."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from neurips_ed_track_minimal import _base_checklist_guardrails as base


ChecklistGuardrailError = base.ChecklistGuardrailError


def case_packet_support_paths(case_packet_text: str) -> set[str]:
    """Return exact Source Inventory members, never the packet alias itself."""

    allowed = base.case_packet_support_paths(case_packet_text)
    allowed.discard("case_packet.md")
    if not allowed:
        raise ChecklistGuardrailError(
            "Case packet has no exact Source Inventory entries after alias exclusion."
        )
    return allowed


def _required_supported_objects(checklist: dict[str, Any]) -> Iterable[tuple[str, Any]]:
    native = checklist.get("native")
    if not isinstance(native, dict):
        return
    for field in ("user_goal", "benchmark_success", "checked_by"):
        yield f"native.{field}", native.get(field)
    for field in ("success_if", "fail_if", "undecided_if"):
        values = native.get(field)
        if isinstance(values, list):
            for index, value in enumerate(values):
                yield f"native.{field}[{index}]", value


def _strict_support_violations(checklist: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    for field_name, value in _required_supported_objects(checklist):
        if not isinstance(value, dict):
            violations.append(f"{field_name} must be an object with non-empty support")
            continue
        support = value.get("support")
        if (
            not isinstance(support, list)
            or not support
            or any(not isinstance(pointer, str) or not pointer.strip() for pointer in support)
        ):
            violations.append(
                f"{field_name}.support must be a non-empty list; rationale never substitutes"
            )
    return violations


def collect_checklist_guardrail_violations(
    checklist: dict[str, Any],
    *,
    allowed_source_paths: set[str] | None = None,
) -> list[str]:
    if allowed_source_paths is not None and "case_packet.md" in allowed_source_paths:
        allowed_source_paths = set(allowed_source_paths)
        allowed_source_paths.discard("case_packet.md")
    return [
        *base.collect_checklist_guardrail_violations(
            checklist,
            allowed_source_paths=allowed_source_paths,
        ),
        *_strict_support_violations(checklist),
    ]


def validate_checklist_guardrails(
    checklist: dict[str, Any],
    *,
    allowed_source_paths: set[str] | None = None,
) -> None:
    violations = collect_checklist_guardrail_violations(
        checklist,
        allowed_source_paths=allowed_source_paths,
    )
    if violations:
        raise ChecklistGuardrailError(
            "Checklist failed strict AndroidWorld deterministic guardrails:\n- "
            + "\n- ".join(violations)
        )

