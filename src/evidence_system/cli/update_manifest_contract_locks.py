"""Manifest contract-lock update CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="update_manifest_contract_locks",
    responsibility="Update manifests with locked contract hashes.",
    owner_module="evidence_system.contracts.manifest_update",
)


if __name__ == "__main__":
    run(COMMAND)
