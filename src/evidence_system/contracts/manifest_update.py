"""Manifest contract-lock update placeholder."""

from evidence_system.core.errors import BootstrapOnlyError


def update_manifest_contract_locks() -> None:
    raise BootstrapOnlyError("Manifest contract-lock updates are not implemented in Step 2.")
