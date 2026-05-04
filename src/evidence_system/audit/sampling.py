"""Audit sampling placeholder."""

from evidence_system.core.errors import BootstrapOnlyError


def draw_audit_sample() -> None:
    raise BootstrapOnlyError("Audit sampling is not implemented in Step 2.")
