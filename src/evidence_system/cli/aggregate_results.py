"""Aggregate results CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="aggregate_results",
    responsibility="Aggregate scored records into formal metrics.",
    owner_module="evidence_system.stats.envelopes",
)


if __name__ == "__main__":
    run(COMMAND)
