"""Remote deployment and collection placeholders."""

from evidence_system.core.errors import BootstrapOnlyError


def check_infra() -> None:
    raise BootstrapOnlyError("Infra checks are not implemented in Step 2.")


def deploy() -> None:
    raise BootstrapOnlyError("Deployment is not implemented in Step 2.")


def collect_results() -> None:
    raise BootstrapOnlyError("Result collection is not implemented in Step 2.")
