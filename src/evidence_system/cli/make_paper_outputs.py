"""Paper outputs CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="make_paper_outputs",
    responsibility="Create all paper output artifacts from validated metrics.",
    owner_module="evidence_system.paper",
)


if __name__ == "__main__":
    run(COMMAND)
