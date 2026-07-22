"""Build or validate the deterministic WebArena-Verified native-claim package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evidence_system.contracts.webarena_native import (
    DEFAULT_OUTPUT_ROOT,
    DEFAULT_PACKET_INDEX,
    DEFAULT_SOURCE_BUNDLE,
    DEFAULT_STEP19_MANIFEST,
    WebArenaNativeClaimError,
    build_native_claim_package,
    validate_native_claim_package,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-bundle", type=Path, default=DEFAULT_SOURCE_BUNDLE)
    parser.add_argument("--step19-manifest", type=Path, default=DEFAULT_STEP19_MANIFEST)
    parser.add_argument("--packet-index", type=Path, default=DEFAULT_PACKET_INDEX)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--human-signoffs",
        type=Path,
        help="Exact 812-entry reviewer JSONL. Omit to emit machine-locked drafts with a formal-launch blocker.",
    )
    parser.add_argument(
        "--operator-waiver",
        type=Path,
        help=(
            "Strict machine-only operator waiver receipt. This path keeps human_signed=0 "
            "and never claims reviewer identity/signature or per-case human review."
        ),
    )
    parser.add_argument("--replace", action="store_true", help="Atomically replace a different generated package")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--no-current-source-check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.validate_only:
            result = validate_native_claim_package(
                args.output_root,
                current_source_check=not args.no_current_source_check,
            )
        else:
            result = build_native_claim_package(
                source_bundle_path=args.source_bundle,
                step19_manifest_path=args.step19_manifest,
                packet_index_path=args.packet_index,
                output_root=args.output_root,
                human_signoffs_path=args.human_signoffs,
                operator_waiver_path=args.operator_waiver,
                replace=args.replace,
            )
    except WebArenaNativeClaimError as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.validate_only and result.get("status") != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
