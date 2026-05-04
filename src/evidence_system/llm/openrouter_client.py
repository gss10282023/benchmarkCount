"""OpenRouter client placeholder.

No network calls or model configuration are implemented in Step 2.
"""

from evidence_system.core.errors import BootstrapOnlyError


def create_client() -> None:
    raise BootstrapOnlyError("OpenRouter client logic is not implemented in Step 2.")
