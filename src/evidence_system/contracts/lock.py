"""Contract lock placeholder."""

from evidence_system.core.errors import BootstrapOnlyError


def lock_contracts() -> None:
    raise BootstrapOnlyError("Contract locking is not implemented in Step 2.")
