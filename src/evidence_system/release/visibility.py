"""Release visibility placeholder."""

from evidence_system.core.errors import BootstrapOnlyError


def compute_visibility() -> None:
    raise BootstrapOnlyError("Release visibility logic is not implemented in Step 2.")
