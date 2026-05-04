"""Audit CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="run_audit",
    responsibility="Run blinded audit sampling and agreement workflows.",
    owner_module="evidence_system.audit.sampling",
)


if __name__ == "__main__":
    run(COMMAND)
