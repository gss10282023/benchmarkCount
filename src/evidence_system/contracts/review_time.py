"""Human review timing placeholder."""

from evidence_system.core.errors import BootstrapOnlyError


def record_review_time() -> None:
    raise BootstrapOnlyError("Human review timing is not implemented in Step 2.")
