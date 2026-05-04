"""Formal full run CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="run_full",
    responsibility="Run formal full jobs only after required gates pass.",
    owner_module="evidence_system.orchestrator.scheduler",
)


if __name__ == "__main__":
    run(COMMAND)
