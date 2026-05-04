"""Manifest validation CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="validate_manifest",
    responsibility="Validate experiment manifests after formal schemas are implemented.",
    owner_module="evidence_system.core.manifest",
)


if __name__ == "__main__":
    run(COMMAND)
