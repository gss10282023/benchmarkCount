"""List available CLI skeletons."""

from __future__ import annotations

from evidence_system.core.schemas import REQUIRED_SCHEMA_FILES


def main() -> int:
    print("Use python -m evidence_system.cli.<command>.")
    print(f"Step 2 schema objects declared: {len(REQUIRED_SCHEMA_FILES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
