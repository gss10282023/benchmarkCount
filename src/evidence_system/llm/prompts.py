"""Prompt registry placeholder."""

from evidence_system.core.errors import BootstrapOnlyError


def load_prompt() -> None:
    raise BootstrapOnlyError("Prompt loading is not implemented in Step 2.")
