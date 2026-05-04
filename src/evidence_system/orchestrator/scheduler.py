"""Scheduler placeholder."""

from evidence_system.core.errors import BootstrapOnlyError


def schedule_jobs() -> None:
    raise BootstrapOnlyError("Scheduling is not implemented in Step 2.")
