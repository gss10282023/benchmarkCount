"""Result validation CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="validate_results",
    responsibility="Validate raw, scored, aggregate, audit, and paper-output records.",
    owner_module="evidence_system.core.schemas",
)


if __name__ == "__main__":
    run(COMMAND)
