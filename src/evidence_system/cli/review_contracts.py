"""Evidence contract review CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="review_contracts",
    responsibility="Record human evidence-contract review actions and timing.",
    owner_module="evidence_system.contracts.review",
)


if __name__ == "__main__":
    run(COMMAND)
