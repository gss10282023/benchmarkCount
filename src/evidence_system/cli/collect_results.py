"""Collect results CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="collect_results",
    responsibility="Collect raw logs, artifact manifests, and failure records repeatably.",
    owner_module="evidence_system.orchestrator.remote",
)


if __name__ == "__main__":
    run(COMMAND)
