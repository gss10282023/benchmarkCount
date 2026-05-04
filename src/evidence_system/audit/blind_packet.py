"""Blinded audit packet placeholder."""

from evidence_system.core.errors import BootstrapOnlyError


def make_blind_packet() -> None:
    raise BootstrapOnlyError("Blinded audit packets are not implemented in Step 2.")
