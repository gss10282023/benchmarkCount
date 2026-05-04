"""Domain run CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="run_domain",
    responsibility="Run one canonical domain through its adapter.",
    owner_module="evidence_system.orchestrator.scheduler",
)


if __name__ == "__main__":
    run(COMMAND)
