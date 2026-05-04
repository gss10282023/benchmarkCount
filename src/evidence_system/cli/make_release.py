"""Release package CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="make_release",
    responsibility="Package release artifacts and rescorer metadata.",
    owner_module="evidence_system.release.rescorer_package",
)


if __name__ == "__main__":
    run(COMMAND)
