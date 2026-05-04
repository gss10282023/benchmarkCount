"""Shared exceptions for fail-closed bootstrap behavior."""


class EvidenceSystemError(RuntimeError):
    """Base error for evidence system failures."""


class BootstrapOnlyError(EvidenceSystemError):
    """Raised when a formal-only action is requested from a bootstrap stub."""


class ConfigValidationError(EvidenceSystemError):
    """Raised when a bootstrap config read fails."""
