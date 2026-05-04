"""Validate checked-in agent and infra configuration files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from evidence_system.core.config import add_config_args
from evidence_system.core.hashing import sha256_file
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import SchemaValidationError, load_json_or_yaml, validate_object


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_system.cli.validate_config",
        description="Validate infra and agent configs against Step 3 schemas.",
    )
    add_config_args(parser)
    parser.add_argument(
        "--formal",
        action="store_true",
        help="Fail closed on unresolved locked-manifest placeholders and non-canonical formal domain ids.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    files = [
        ("agent_config", args.agents_config),
        ("infra_config", args.infra_config),
    ]
    results: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    for schema_name, path in files:
        resolved = resolve_repo_path(path)
        try:
            payload = load_json_or_yaml(resolved)
            report = validate_object(schema_name, payload, formal=args.formal, raise_on_error=False)
        except SchemaValidationError as exc:
            report = exc.report
            payload = {}
        if not report.ok:
            issues.extend(
                {"file": str(resolved), **issue.to_dict()}
                for issue in report.issues
            )
        schema_version = payload.get("schema_version") if isinstance(payload, dict) else None
        results.append(
            {
                "path": _display_path(resolved),
                "schema": schema_name,
                "schema_version": schema_version,
                "sha256": sha256_file(resolved) if resolved.exists() else None,
                "status": report.status,
            }
        )
    payload = {
        "status": "ok" if not issues else "invalid",
        "formal": args.formal,
        "formal_schema_validation": "step3_fail_closed",
        "files": results,
        "issues": issues,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"status: {payload['status']}")
        for item in results:
            print(f"{item['path']}: {item['schema_version']} {item['sha256']} {item['status']}")
        for issue in issues:
            print(f"{issue['file']} {issue['path']}: {issue['message']}", file=sys.stderr)
    return 0 if not issues else 1


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(resolve_repo_path(".")))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    sys.exit(main())
