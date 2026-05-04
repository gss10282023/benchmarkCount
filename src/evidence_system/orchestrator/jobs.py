"""Job object placeholder."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JobSkeleton:
    phase: str
    experiment_type: str
    priority: str
