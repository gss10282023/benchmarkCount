"""Build or validate the unsigned WebArena-Verified human review queue."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evidence_system.contracts.webarena_human_review import (
    DEFAULT_NATIVE_ROOT,
    DEFAULT_OUTPUT_ROOT,
    WebArenaHumanReviewError,
    build_review_package,
    package_hash,
    validate_review_package,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-root", type=Path, default=DEFAULT_NATIVE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument(
        "--completed-signoffs",
        type=Path,
        help=(
            "Read-only validation of an exact 812-line completed human signoff "
            "JSONL; no formal locks or scheduler outputs are written."
        ),
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.validate_only:
            result = validate_review_package(
                args.output_root,
                native_root=args.native_root,
                completed_signoffs_path=args.completed_signoffs,
            )
        else:
            if args.completed_signoffs is not None:
                raise WebArenaHumanReviewError(
                    "--completed-signoffs is read-only and requires --validate-only"
                )
            result = build_review_package(
                native_root=args.native_root,
                output_root=args.output_root,
                replace=args.replace,
            )
        result["package_sha256"] = package_hash(args.output_root)
    except WebArenaHumanReviewError as exc:
        result = {"status": "blocked", "error": str(exc)}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"status: {result['status']}")
        if "package_sha256" in result:
            print(f"package_sha256: {result['package_sha256']}")
        for issue in result.get("issues", []):
            print(f"blocking: {issue}")
        if "error" in result:
            print(f"blocking: {result['error']}")
    return 0 if result.get("status") in {"ok", "ready_for_formal_build"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

