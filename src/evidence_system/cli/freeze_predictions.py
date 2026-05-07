"""Check Step 5 pre-scoring freeze inputs without creating formal artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from evidence_system.cli._common import BootstrapCommand
from evidence_system.core.freeze import check_freeze_predictions


COMMAND = BootstrapCommand(
    name="freeze_predictions",
    responsibility="Check pre-scoring freeze inputs without writing the formal freeze file.",
    owner_module="evidence_system.core.freeze",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_system.cli.freeze_predictions",
        description=COMMAND.responsibility,
    )
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--check-only", action="store_true", help="Validate freeze inputs and print the would-be freeze manifest.")
    parser.add_argument("--manifest", help="experiment_manifest/v1 JSON/YAML.")
    parser.add_argument("--contract", "--contracts", dest="contract", action="append", default=[], help="Locked contract file or directory. May be repeated.")
    parser.add_argument("--review-record", action="append", default=[], help="contract_review/v1 file or directory. May be repeated.")
    parser.add_argument("--llm-call", action="append", default=[], help="llm_call/v1 file or directory. May be repeated.")
    parser.add_argument("--source-bundle", help="contract_source_bundle.v1 JSON/YAML.")
    parser.add_argument("--paper-mapping", help="Paper mapping markdown or schema file.")
    parser.add_argument("--agents-config", default="configs/agents.yaml")
    parser.add_argument("--infra-config", default="configs/infra.yaml")
    parser.add_argument("--prediction-registry", default="experiments/prediction_registry/registry.yaml")
    parser.add_argument("--official-splits", default="experiments/official_splits")
    parser.add_argument("--contract-template", default="experiments/evidence_contracts/contract_template.yaml")
    parser.add_argument("--bootstrap-plan")
    parser.add_argument("--audit-sampling-plan", default="experiments/audit_sampling_plan/plan.yaml")
    parser.add_argument("--rerun-subset")
    parser.add_argument("--result-schema", default="schemas/scored_record.schema.json")
    parser.add_argument("--artifact-schema", default="schemas/artifact_manifest.schema.json")
    parser.add_argument("--scorer-code", action="append", default=["src/evidence_system/scorer"])
    parser.add_argument("--scorer-version")
    parser.add_argument("--code-git-commit")
    parser.add_argument("--frozen-at")
    parser.add_argument("--evidence-contract-template-version", default="contract_template/v1")
    parser.add_argument("--contract-drafting-prompt-version", default="contract_draft_prompt/v1")
    parser.add_argument("--contract-drafting-prompt-hash")
    parser.add_argument("--freeze-manifest", help="Optional proposed freeze_manifest/v1 to compare against current inputs.")
    parser.add_argument("--formal", action="store_true", help="Apply formal P0 fail-closed gates.")
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
            "formal_logic": "implemented_step_5_check_only",
            "side_effects": "none",
        }
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
        return 0
    if not args.check_only:
        payload = {
            "status": "blocked",
            "reason": "Step 5 development supports --check-only only; it must not create results/manifests/pre_scoring_freeze.json.",
        }
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload, file=sys.stderr)
        return 2
    missing = []
    if not args.manifest:
        missing.append("--manifest")
    if not args.contract:
        missing.append("--contract/--contracts")
    if not args.source_bundle:
        missing.append("--source-bundle")
    if not args.bootstrap_plan:
        missing.append("--bootstrap-plan")
    if not args.rerun_subset:
        missing.append("--rerun-subset")
    if not args.scorer_version:
        missing.append("--scorer-version")
    if missing:
        payload = {"status": "invalid_args", "missing": missing}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload, file=sys.stderr)
        return 2

    report = check_freeze_predictions(
        manifest_path=args.manifest,
        contracts=args.contract,
        review_records=args.review_record,
        llm_calls=args.llm_call,
        source_bundle_path=args.source_bundle,
        paper_mapping_path=args.paper_mapping,
        agents_config_path=args.agents_config,
        infra_config_path=args.infra_config,
        prediction_registry_path=args.prediction_registry,
        official_splits_path=args.official_splits,
        contract_template_path=args.contract_template,
        bootstrap_plan_path=args.bootstrap_plan,
        audit_sampling_plan_path=args.audit_sampling_plan,
        rerun_subset_path=args.rerun_subset,
        result_schema_path=args.result_schema,
        artifact_schema_path=args.artifact_schema,
        scorer_code_paths=tuple(args.scorer_code),
        scorer_version=args.scorer_version,
        code_git_commit=args.code_git_commit,
        frozen_at=args.frozen_at,
        evidence_contract_template_version=args.evidence_contract_template_version,
        contract_drafting_prompt_version=args.contract_drafting_prompt_version,
        contract_drafting_prompt_hash=args.contract_drafting_prompt_hash,
        proposed_freeze_manifest_path=args.freeze_manifest,
        formal=args.formal,
    )
    payload = report.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"status: {payload['status']}")
        for issue in payload["issues"]:
            print(f"{issue['path']}: {issue['message']}", file=sys.stderr)
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
