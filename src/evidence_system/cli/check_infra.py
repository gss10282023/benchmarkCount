"""Infrastructure check CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="check_infra",
    responsibility="Check infrastructure readiness without running formal experiments.",
    owner_module="evidence_system.orchestrator.remote",
)


if __name__ == "__main__":
    run(COMMAND)
