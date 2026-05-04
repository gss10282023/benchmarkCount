"""Release metadata placeholder."""

from evidence_system.core.errors import BootstrapOnlyError


def make_final_report() -> None:
    raise BootstrapOnlyError("Final report generation is not implemented in Step 2.")
