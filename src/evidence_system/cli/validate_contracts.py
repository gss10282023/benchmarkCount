"""Validate evidence contract lifecycle artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.contracts.validate import validate_contracts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m evidence_system.cli.validate_contracts")
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument(
        "--contract",
        "--contracts",
        dest="contract",
        action="append",
        default=[],
        help="Contract file or directory. May be repeated.",
    )
    parser.add_argument("--manifest")
    parser.add_argument("--review-record", action="append", default=[])
    parser.add_argument("--llm-call", action="append", default=[])
    parser.add_argument("--source-bundle")
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--require-p0-complete", action="store_true")
    parser.add_argument("--require-declared-appendix", action="store_true")
    parser.add_argument(
        "--allow-empty-before-lock",
        action="store_true",
        help="Allow an empty contract directory during pre-lock development checks only.",
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.bootstrap_check:
        payload = {"name": "validate_contracts", "status": "ok", "formal_logic": "implemented_step_4", "side_effects": "none"}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
        return 0
    if not args.contract:
        print({"status": "invalid_args", "missing": ["contract"]}, file=sys.stderr)
        return 2
    try:
        report = validate_contracts(
            contracts=args.contract,
            manifest_path=args.manifest,
            review_records=args.review_record,
            llm_calls=args.llm_call,
            source_bundle_path=args.source_bundle,
            formal=args.formal,
            require_p0_complete=args.require_p0_complete,
            require_declared_appendix=args.require_declared_appendix,
            allow_empty_before_lock=args.allow_empty_before_lock,
        )
    except ContractLifecycleError as exc:
        payload = {"status": "blocked", "reason": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload, file=sys.stderr)
        return 2
    payload = report.to_dict()
    print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
