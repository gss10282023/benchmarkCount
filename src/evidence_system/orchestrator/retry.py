"""Retry policy placeholder."""

from evidence_system.core.errors import BootstrapOnlyError


def apply_retry_policy() -> None:
    raise BootstrapOnlyError("Retry policy is not implemented in Step 2.")
