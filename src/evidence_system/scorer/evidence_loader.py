"""Evidence loading placeholder."""

from evidence_system.core.errors import BootstrapOnlyError


def load_evidence() -> None:
    raise BootstrapOnlyError("Evidence loading is not implemented in Step 2.")
