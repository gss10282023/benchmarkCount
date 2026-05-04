"""Rerun workflow placeholder."""

from evidence_system.core.errors import BootstrapOnlyError


def run_rerun_subset() -> None:
    raise BootstrapOnlyError("Rerun workflow is not implemented in Step 2.")
