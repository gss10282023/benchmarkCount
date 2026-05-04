"""Evidence contract validation CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="validate_contracts",
    responsibility="Validate evidence contracts once contract schemas exist.",
    owner_module="evidence_system.contracts.validate",
)


if __name__ == "__main__":
    run(COMMAND)
