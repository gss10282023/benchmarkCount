"""Scoring CLI placeholder."""

from evidence_system.cli._common import BootstrapCommand, run


COMMAND = BootstrapCommand(
    name="score_records",
    responsibility="Produce locked-contract scored records from verified artifacts.",
    owner_module="evidence_system.scorer.engine",
)


if __name__ == "__main__":
    run(COMMAND)
