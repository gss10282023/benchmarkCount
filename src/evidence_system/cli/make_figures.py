"""Make paper figures CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="make_figures",
    responsibility="Create paper figure artifacts from validated metrics.",
    owner_module="evidence_system.paper.figures",
)


if __name__ == "__main__":
    run(COMMAND)
