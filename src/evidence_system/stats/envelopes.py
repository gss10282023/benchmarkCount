"""Evidence envelope aggregation placeholder."""

from evidence_system.core.errors import BootstrapOnlyError


def aggregate_envelopes() -> None:
    raise BootstrapOnlyError("Envelope aggregation is not implemented in Step 2.")
