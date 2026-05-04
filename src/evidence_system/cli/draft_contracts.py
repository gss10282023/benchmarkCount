"""Evidence contract draft CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="draft_contracts",
    responsibility="Draft evidence contracts from allowed blinded inputs.",
    owner_module="evidence_system.contracts.draft",
)


if __name__ == "__main__":
    run(COMMAND)
