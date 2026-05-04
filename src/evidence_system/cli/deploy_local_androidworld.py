"""Deploy local AndroidWorld CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="deploy_local_androidworld",
    responsibility="Prepare the local AndroidWorld machine role.",
    owner_module="evidence_system.orchestrator.remote",
)


if __name__ == "__main__":
    run(COMMAND)
