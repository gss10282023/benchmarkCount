"""Run monitor CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="monitor",
    responsibility="Monitor machine status, run progress, and recoverable failures.",
    owner_module="evidence_system.orchestrator.remote",
)


if __name__ == "__main__":
    run(COMMAND)
