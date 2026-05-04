"""Make paper tables CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="make_tables",
    responsibility="Create paper table artifacts from validated metrics.",
    owner_module="evidence_system.paper.tables",
)


if __name__ == "__main__":
    run(COMMAND)
