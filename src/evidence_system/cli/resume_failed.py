"""Resume failed attempts CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="resume_failed",
    responsibility="Resume recoverable infra or pre-run failures under frozen policy.",
    owner_module="evidence_system.orchestrator.resume",
)


if __name__ == "__main__":
    run(COMMAND)
