from __future__ import annotations

import sys
import unittest
from decimal import Decimal
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from formatting import format_identification_interval, format_interval, format_percent, format_ratio  # noqa: E402


class FormattingTests(unittest.TestCase):
    def test_percent_and_ratio(self) -> None:
        self.assertEqual(format_percent(0), "0.0%")
        self.assertEqual(format_percent(1), "100.0%")
        self.assertEqual(format_ratio(1, 3), "33.3%")
        self.assertEqual(format_ratio(2, 3), "66.7%")
        self.assertEqual(format_percent(Decimal("0.1255")), "12.6%")

    def test_interval_uses_same_rule(self) -> None:
        self.assertEqual(format_interval(Decimal("0.1255"), Decimal("0.6666")), "[12.6%, 66.7%]")
        self.assertEqual(format_identification_interval(7, 18, 41), "[17.1%, 61.0%]")

    def test_invalid_values_fail_closed(self) -> None:
        for value in (-0.1, 1.1, Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                format_percent(value)
        with self.assertRaises(ValueError):
            format_ratio(0, 0)
        with self.assertRaises(ValueError):
            format_interval(0.8, 0.2)

    def test_negative_zero_is_canonical(self) -> None:
        self.assertEqual(format_percent(Decimal("-0")), "0.0%")


if __name__ == "__main__":
    unittest.main()
