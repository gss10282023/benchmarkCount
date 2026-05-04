"""Evidence contract lock CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="lock_contracts",
    responsibility="Lock reviewed evidence contracts before scoring.",
    owner_module="evidence_system.contracts.lock",
)


if __name__ == "__main__":
    run(COMMAND)
