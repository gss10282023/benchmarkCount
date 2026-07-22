"""Canonical numeric formatting for rebuttal outputs.

All percentages are rounded half-up to one decimal place.  Callers pass
integer counts whenever possible so the result is independent of binary
floating-point behavior.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


ONE_DECIMAL = Decimal("0.1")


def _as_decimal(value: int | float | str | Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def format_percent(proportion: int | float | str | Decimal) -> str:
    """Format a proportion in [0, 1] as a one-decimal percentage."""

    value = _as_decimal(proportion)
    if not value.is_finite():
        raise ValueError("proportion must be finite")
    if value < 0 or value > 1:
        raise ValueError(f"proportion must be in [0, 1], got {value}")
    if value == 0:
        value = Decimal(0)
    rounded = (value * Decimal(100)).quantize(ONE_DECIMAL, rounding=ROUND_HALF_UP)
    return f"{rounded:.1f}%"


def format_ratio(numerator: int, denominator: int) -> str:
    """Format numerator/denominator as a one-decimal percentage."""

    if denominator <= 0:
        raise ValueError("denominator must be positive")
    if numerator < 0 or numerator > denominator:
        raise ValueError("numerator must be between zero and denominator")
    return format_percent(Decimal(numerator) / Decimal(denominator))


def format_interval(low: int | float | str | Decimal, high: int | float | str | Decimal) -> str:
    """Format a closed proportion interval with the same endpoint rule."""

    low_decimal = _as_decimal(low)
    high_decimal = _as_decimal(high)
    if low_decimal > high_decimal:
        raise ValueError("interval low endpoint exceeds high endpoint")
    return f"[{format_percent(low_decimal)}, {format_percent(high_decimal)}]"


def format_identification_interval(passed: int, unknown: int, total: int) -> str:
    """Format [P/N, (P+U)/N] using the canonical rule."""

    if total <= 0 or min(passed, unknown) < 0 or passed + unknown > total:
        raise ValueError("invalid P/U/N counts")
    low = Decimal(passed) / Decimal(total)
    high = Decimal(passed + unknown) / Decimal(total)
    return format_interval(low, high)
