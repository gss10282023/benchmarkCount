"""LLM call logging placeholder."""

from evidence_system.core.errors import BootstrapOnlyError


def log_call() -> None:
    raise BootstrapOnlyError("LLM call logging is not implemented in Step 2.")
