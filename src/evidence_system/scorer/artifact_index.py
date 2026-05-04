"""Artifact index placeholder."""

from evidence_system.core.errors import BootstrapOnlyError


def build_artifact_index() -> None:
    raise BootstrapOnlyError("Artifact indexing is not implemented in Step 2.")
