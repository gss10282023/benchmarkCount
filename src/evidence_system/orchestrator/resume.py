"""Resume workflow placeholder."""

from evidence_system.core.errors import BootstrapOnlyError


def resume_failed_attempts() -> None:
    raise BootstrapOnlyError("Resume workflow is not implemented in Step 2.")
