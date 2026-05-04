"""Native evaluator mapping placeholder."""

from evidence_system.core.errors import BootstrapOnlyError


def resolve_native_mapping() -> None:
    raise BootstrapOnlyError("Native evaluator mapping is not implemented in Step 2.")
