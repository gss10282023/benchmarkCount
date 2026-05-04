"""Scoring engine placeholder.

The formal scorer is intentionally absent in Step 2.
"""

from evidence_system.core.errors import BootstrapOnlyError


def score_records() -> None:
    raise BootstrapOnlyError("Formal scoring is not implemented in Step 2.")
