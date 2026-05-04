"""Rerun CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="run_rerun",
    responsibility="Run the frozen rerun subset without changing denominators.",
    owner_module="evidence_system.audit.rerun",
)


if __name__ == "__main__":
    run(COMMAND)
