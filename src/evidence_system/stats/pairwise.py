"""Pairwise margin placeholder."""

from evidence_system.core.errors import BootstrapOnlyError


def compute_pairwise() -> None:
    raise BootstrapOnlyError("Pairwise statistics are not implemented in Step 2.")
