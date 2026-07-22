"""Run strict AppWorld extension definition, packet, and source-bundle gates."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from evidence_system.cli._common import BootstrapCommand
from evidence_system.contracts.appworld_extension import (
    DEFAULT_OUTPUT_ROOT,
    validate_extension_definition,
    validate_extension_packets,
    validate_extension_source_bundle,
    write_acceptance_report,
)
from evidence_system.contracts.common import ContractLifecycleError


COMMAND = BootstrapCommand(
    name="validate_appworld_extension",
    responsibility="Fail closed unless the frozen AppWorld extension and all requested downstream artifacts are exact.",
    owner_module="evidence_system.contracts.appworld_extension",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_system.cli.validate_appworld_extension",
        description=COMMAND.responsibility,
    )
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--case-packets-root")
    parser.add_argument("--source-bundle")
    parser.add_argument("--definition-only", action="store_true")
    parser.add_argument("--packets-only", action="store_true")
    parser.add_argument("--bundle-only", action="store_true")
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write the acceptance report after all gates pass; default full validation is read-only.",
    )
    parser.add_argument("--acceptance-report")
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
            args.json,
        )
        return 0
    selected_modes = sum(bool(value) for value in (args.definition_only, args.packets_only, args.bundle_only))
    if selected_modes > 1:
        _emit({"status": "blocked", "reason": "choose at most one of --definition-only/--packets-only/--bundle-only"}, args.json, file=sys.stderr)
        return 2
    wants_report = args.write_report or args.acceptance_report is not None
    if wants_report and selected_modes:
        _emit(
            {"status": "blocked", "reason": "report writing cannot be combined with a single-gate mode"},
            args.json,
            file=sys.stderr,
        )
        return 2
    try:
        if args.definition_only:
            audit = validate_extension_definition(output_root=args.output_root)
        elif args.packets_only:
            audit = validate_extension_packets(
                output_root=args.output_root,
                case_packets_root=args.case_packets_root,
            )
        elif args.bundle_only:
            audit = validate_extension_source_bundle(
                output_root=args.output_root,
                case_packets_root=args.case_packets_root,
                source_bundle_path=args.source_bundle,
            )
        elif wants_report:
            audit = write_acceptance_report(
                output_root=args.output_root,
                case_packets_root=args.case_packets_root,
                source_bundle_path=args.source_bundle,
                report_path=args.acceptance_report,
            )
        else:
            audit = {
                "definition": validate_extension_definition(output_root=args.output_root),
                "packets": validate_extension_packets(
                    output_root=args.output_root,
                    case_packets_root=args.case_packets_root,
                ),
                "source_bundle": validate_extension_source_bundle(
                    output_root=args.output_root,
                    case_packets_root=args.case_packets_root,
                    source_bundle_path=args.source_bundle,
                ),
                "all_hard_gates_passed": True,
                "report_written": False,
            }
    except (ContractLifecycleError, OSError, ValueError) as exc:
        _emit({"status": "blocked", "reason": str(exc)}, args.json, file=sys.stderr)
        return 2
    _emit({"status": "ok", **audit}, args.json)
    return 0


def _emit(payload: dict[str, object], as_json: bool, *, file: object = None) -> None:
    stream = file or sys.stdout
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True), file=stream)
    else:
        for key, value in payload.items():
            print(f"{key}: {value}", file=stream)


if __name__ == "__main__":
    sys.exit(main())
