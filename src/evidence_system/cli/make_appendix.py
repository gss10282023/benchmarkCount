"""Make appendix outputs CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="make_appendix",
    responsibility="Create appendix artifacts from declared validated inputs.",
    owner_module="evidence_system.paper.appendix",
)


if __name__ == "__main__":
    run(COMMAND)
