"""Read checked-in config files for Step 2 bootstrap validation."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from evidence_system.core.config import add_config_args, validate_config_files
from evidence_system.core.errors import ConfigValidationError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_system.cli.validate_config",
        description="Read infra and agent configs without formal schema validation.",
    )
    add_config_args(parser)
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        summary = validate_config_files([args.infra_config, args.agents_config])
    except ConfigValidationError as exc:
        print(f"validate_config: {exc}", file=sys.stderr)
        return 1
    payload = summary.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"status: {payload['status']}")
        for item in payload["files"]:
            print(f"{item['path']}: {item['schema_version']} {item['sha256']}")
        print(payload["note"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
