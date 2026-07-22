"""Run strict acceptance gates for the MiniWoB++ remaining-22 extension."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from evidence_system.cli._common import BootstrapCommand
from evidence_system.contracts.miniwob_extension_acceptance import (
    DEFAULT_AGENTS_CONFIG,
    DEFAULT_CASE_PACKETS_ROOT,
    DEFAULT_EXECUTION_INFRA,
    DEFAULT_FIRST50_SELECTED,
    DEFAULT_MANIFEST,
    DEFAULT_REMAINING22_SELECTED,
    DEFAULT_REMAINING_CATALOG,
    DEFAULT_SECOND50_SELECTED,
    DEFAULT_SOURCE_BUNDLE,
    EXPECTED_RESULT_NAMESPACE,
    validate_miniwob_extension,
    write_acceptance_receipt,
)
from evidence_system.core.errors import EvidenceSystemError


COMMAND = BootstrapCommand(
    name="validate_miniwob_extension",
    responsibility="Fail closed unless the MiniWoB++ 50+50+22 definition and every remaining-22 packet byte are exact.",
    owner_module="evidence_system.contracts.miniwob_extension_acceptance",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_system.cli.validate_miniwob_extension",
        description=COMMAND.responsibility,
    )
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--first50-selected", default=str(DEFAULT_FIRST50_SELECTED))
    parser.add_argument("--second50-selected", default=str(DEFAULT_SECOND50_SELECTED))
    parser.add_argument("--remaining22-selected", default=str(DEFAULT_REMAINING22_SELECTED))
    parser.add_argument("--remaining-catalog", default=str(DEFAULT_REMAINING_CATALOG))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--source-bundle", default=str(DEFAULT_SOURCE_BUNDLE))
    parser.add_argument("--case-packets-root", default=str(DEFAULT_CASE_PACKETS_ROOT))
    parser.add_argument("--execution-infra", default=str(DEFAULT_EXECUTION_INFRA))
    parser.add_argument("--agents-config", default=str(DEFAULT_AGENTS_CONFIG))
    parser.add_argument("--expected-result-namespace", default=EXPECTED_RESULT_NAMESPACE)
    parser.add_argument("--output", help="Write a machine-readable receipt only after every hard gate passes.")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.bootstrap_check:
        _emit(
            {
                "name": COMMAND.name,
                "responsibility": COMMAND.responsibility,
                "owner_module": COMMAND.owner_module,
                "status": "ok",
            },
            as_json=args.json,
        )
        return 0
    try:
        receipt = validate_miniwob_extension(
            first50_selected_path=args.first50_selected,
            second50_selected_path=args.second50_selected,
            remaining22_selected_path=args.remaining22_selected,
            remaining_catalog_path=args.remaining_catalog,
            manifest_path=args.manifest,
            source_bundle_path=args.source_bundle,
            case_packets_root=args.case_packets_root,
            execution_infra_path=args.execution_infra,
            agents_config_path=args.agents_config,
            expected_result_namespace=args.expected_result_namespace,
        )
        if args.output:
            output = write_acceptance_receipt(receipt, args.output)
            response = {**receipt, "receipt_path": str(output)}
        else:
            response = receipt
    except (EvidenceSystemError, OSError, ValueError, TypeError) as exc:
        _emit({"status": "blocked", "reason": str(exc)}, as_json=args.json, file=sys.stderr)
        return 2
    _emit(response, as_json=args.json)
    return 0


def _emit(payload: dict[str, object], *, as_json: bool, file: object | None = None) -> None:
    stream = file or sys.stdout
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True), file=stream)
    else:
        for key, value in payload.items():
            print(f"{key}: {value}", file=stream)


if __name__ == "__main__":
    sys.exit(main())
