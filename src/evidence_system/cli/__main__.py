"""List available evidence-system CLI entry points."""

from __future__ import annotations

from evidence_system.core.schemas import REQUIRED_SCHEMA_FILES


STEP4_CONTRACT_COMMANDS = (
    "draft_contracts",
    "audit_contract_reviews",
    "review_contracts",
    "lock_contracts",
    "record_contract_clarification",
    "update_manifest_contract_locks",
    "validate_contracts",
)


def main() -> int:
    print("Use python -m evidence_system.cli.<command>.")
    print(f"Step 3 formal schema objects declared: {len(REQUIRED_SCHEMA_FILES)}")
    print(f"Step 4 contract lifecycle commands implemented: {len(STEP4_CONTRACT_COMMANDS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
