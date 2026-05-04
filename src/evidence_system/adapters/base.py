"""Adapter interface skeleton.

Adapters will run official benchmarks and save raw evidence only. They do not
produce final evidence labels.
"""

from __future__ import annotations

from dataclasses import dataclass

from evidence_system.core.errors import BootstrapOnlyError


@dataclass(frozen=True)
class AdapterSkeleton:
    canonical_domain_id: str
    contains_formal_runner_logic: bool = False
    can_emit_final_evidence_label: bool = False


def run_adapter() -> None:
    raise BootstrapOnlyError("Formal adapter execution is not implemented in Step 2.")
