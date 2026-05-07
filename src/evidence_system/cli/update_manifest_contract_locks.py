"""Update manifests with locked contract hashes."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.contracts.manifest_update import update_manifest_contract_locks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m evidence_system.cli.update_manifest_contract_locks")
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--manifest")
    parser.add_argument("--locked-contract", action="append", default=[], help="Locked contract file or directory. May be repeated.")
    parser.add_argument("--output")
    parser.add_argument("--no-sync-contract-manifest-hash", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.bootstrap_check:
        payload = {"name": "update_manifest_contract_locks", "status": "ok", "formal_logic": "implemented_step_4", "side_effects": "none"}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
        return 0
    if not args.manifest or not args.locked_contract:
        print({"status": "invalid_args", "missing": ["manifest or locked_contract"]}, file=sys.stderr)
        return 2
    try:
        result = update_manifest_contract_locks(
            manifest_path=args.manifest,
            locked_contracts=args.locked_contract,
            output_path=args.output,
            sync_contract_manifest_hash=not args.no_sync_contract_manifest_hash,
        )
        payload = {"status": "ok", **result.to_dict()}
    except ContractLifecycleError as exc:
        payload = {"status": "blocked", "reason": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload, file=sys.stderr)
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
