"""Run strict acceptance checks for the isolated AgentDojo full experiment."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from evidence_system.contracts.agentdojo_full_experiment import (
    DEFAULT_ACCEPTANCE,
    DEFAULT_LOCK,
    verify_full_experiment,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", default=str(DEFAULT_LOCK))
    parser.add_argument("--output", default=str(DEFAULT_ACCEPTANCE))
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = verify_full_experiment(lock_path=args.lock, acceptance_output_path=args.output)
    except (ContractLifecycleError, ValueError, KeyError) as exc:
        payload = {"status": "blocked", "reason": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload, file=sys.stderr)
        return 2
    payload = {"status": "accepted", "report_path": str(report), "report_sha256": sha256_file(report)}
    print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
