"""Final report CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="final_report",
    responsibility="Create the final release report after all validation gates pass.",
    owner_module="evidence_system.release.metadata",
)


if __name__ == "__main__":
    run(COMMAND)
