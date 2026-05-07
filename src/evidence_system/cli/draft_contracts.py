"""Draft evidence contracts from allowed blinded inputs."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from evidence_system.cli._common import BootstrapCommand
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.contracts.draft import draft_contracts
from evidence_system.core.errors import EvidenceSystemError


COMMAND = BootstrapCommand(
    name="draft_contracts",
    responsibility="Draft evidence contracts from allowed blinded inputs.",
    owner_module="evidence_system.contracts.draft",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m evidence_system.cli.draft_contracts", description=COMMAND.responsibility)
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--source-bundle", help="contract_source_bundle.v1 JSON/YAML.")
    parser.add_argument("--agents-config", default="configs/agents.yaml")
    parser.add_argument("--contract-template", default="experiments/evidence_contracts/contract_template.yaml")
    parser.add_argument("--out-dir", default="experiments/evidence_contracts/drafts")
    parser.add_argument("--llm-log-dir", default="results/logs/llm_calls/contract_drafts")
    parser.add_argument("--allow-test-mock", action="store_true", help="Use the Step 4 deterministic mock transport for tests only.")
    parser.add_argument("--locked-manifest", help="Locked/frozen manifest used for formal LLM config consistency checks.")
    parser.add_argument("--formal", action="store_true", help="Fail closed on unresolved config, manifest mismatch, or missing API key.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--request-timestamp")
    parser.add_argument("--response-timestamp")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.bootstrap_check:
        payload = {
            "name": COMMAND.name,
            "responsibility": COMMAND.responsibility,
            "owner_module": COMMAND.owner_module,
            "status": "ok",
            "formal_logic": "implemented_step_6_openrouter_transport_available",
            "side_effects": "none",
        }
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
        return 0
    if not args.source_bundle:
        parser.error("--source-bundle is required unless --bootstrap-check is used")
    try:
        results = draft_contracts(
            source_bundle_path=args.source_bundle,
            agents_config_path=args.agents_config,
            contract_template_path=args.contract_template,
            output_dir=args.out_dir,
            llm_log_dir=args.llm_log_dir,
            allow_test_mock=args.allow_test_mock,
            locked_manifest_path=args.locked_manifest,
            formal=args.formal,
            limit=args.limit,
            request_timestamp=args.request_timestamp,
            response_timestamp=args.response_timestamp,
        )
        payload = {"status": "ok", "draft_count": len(results), "drafts": [item.to_dict() for item in results]}
    except (ContractLifecycleError, EvidenceSystemError) as exc:
        payload = {"status": "blocked", "reason": str(exc)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        else:
            print(f"status: {payload['status']}\nreason: {payload['reason']}", file=sys.stderr)
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
