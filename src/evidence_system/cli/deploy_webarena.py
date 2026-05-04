"""Deploy WebArena-Verified CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="deploy_webarena",
    responsibility="Deploy the WebArena-Verified machine role.",
    owner_module="evidence_system.orchestrator.remote",
)


if __name__ == "__main__":
    run(COMMAND)
