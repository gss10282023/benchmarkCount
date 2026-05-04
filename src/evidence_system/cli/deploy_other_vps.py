"""Deploy other VPS domains CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="deploy_other_vps",
    responsibility="Deploy the shared VPS role for non-specialized domains.",
    owner_module="evidence_system.orchestrator.remote",
)


if __name__ == "__main__":
    run(COMMAND)
