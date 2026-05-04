"""LLM cost accounting placeholder."""

from evidence_system.core.errors import BootstrapOnlyError


def compute_cost() -> None:
    raise BootstrapOnlyError("LLM cost accounting is not implemented in Step 2.")
