"""Validate raw, scored, aggregate, audit, deployment, and release records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from evidence_system.cli._common import BootstrapCommand, bootstrap_main
from evidence_system.core.hashing import sha256_file
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import (
    SchemaValidationError,
    collect_locked_contracts,
    extract_paper_mapping_labels,
    load_json_or_yaml,
    paper_mapping_labels_from_object,
    validate_cross_object_consistency,
    validate_file,
    validate_object,
    validate_paper_mapping_coverage,
)


COMMAND = BootstrapCommand(
    name="validate_results",
    responsibility="Validate formal result artifacts against Step 3 schemas.",
    owner_module="evidence_system.core.schemas",
)

RESULT_OPTIONS: tuple[tuple[str, str], ...] = (
    ("raw_run", "raw_run"),
    ("scored_record", "scored_record"),
    ("infra_exclusion", "infra_exclusion_record"),
    ("failure_record", "failure_record"),
    ("artifact_manifest", "artifact_manifest"),
    ("llm_call", "llm_call"),
    ("human_review", "human_review"),
    ("human_time", "human_time"),
    ("audit_item", "audit_item"),
    ("audit_label", "audit_label"),
    ("rerun_record", "rerun_record"),
    ("aggregate_metrics", "aggregate_metrics"),
    ("prediction_outcome", "prediction_outcome"),
    ("pairwise_matrix", "pairwise_matrix"),
    ("denominator_audit", "denominator_audit"),
    ("paper_output", "paper_output"),
    ("deployment_manifest", "deployment_manifest"),
    ("release_artifact", "release_artifact"),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_system.cli.validate_results",
        description=COMMAND.responsibility,
    )
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--paper-mapping", help="Required when validating paper outputs.")
    parser.add_argument("--manifest", help="Formal experiment_manifest/v1 context.")
    parser.add_argument("--freeze-manifest", help="Formal freeze_manifest/v1 context.")
    parser.add_argument(
        "--evidence-contract",
        action="append",
        default=[],
        metavar="PATH",
        help="Formal locked evidence_contract/v1 context. May be repeated.",
    )
    parser.add_argument("--formal", action="store_true", help="Apply formal fail-closed gates.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    for option, schema_name in RESULT_OPTIONS:
        parser.add_argument(
            f"--{option.replace('_', '-')}",
            action="append",
            default=[],
            metavar="PATH",
            help=f"Validate a {schema_name}/v1 record.",
        )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.bootstrap_check:
        return bootstrap_main(COMMAND, ["--bootstrap-check", *(["--json"] if args.json else [])])

    inputs = _collect_inputs(args)
    if not inputs:
        parser.error("at least one result file option is required unless --bootstrap-check is used")

    issues: list[dict[str, str]] = []
    files: list[dict[str, Any]] = []
    paper_labels: set[str] | None = None
    paper_mapping_context: Mapping[str, Any] | None = None
    if args.paper_mapping:
        try:
            paper_labels, paper_mapping_context = _load_paper_mapping(args.paper_mapping, issues, files, formal=args.formal)
        except SchemaValidationError as exc:
            issues.extend({"file": str(resolve_repo_path(args.paper_mapping)), **issue.to_dict()} for issue in exc.report.issues)

    context_objects: list[tuple[str, Mapping[str, Any]]] = []
    locked_contracts: dict[str, Mapping[str, Any]] | None = None
    if args.formal:
        _formal_context_requirement_issues(args, issues)
        context_objects = _load_formal_context(args, paper_labels, issues, files)
        if paper_mapping_context is not None:
            context_objects.append(("paper_mapping", paper_mapping_context))
        locked_contracts, registry_report = collect_locked_contracts(context_objects, raise_on_error=False)
        if registry_report.issues:
            issues.extend({"file": "<formal-context>", **issue.to_dict()} for issue in registry_report.issues)

    result_objects: list[tuple[str, Mapping[str, Any]]] = []
    for schema_name, path_arg in inputs:
        path = resolve_repo_path(path_arg)
        try:
            report = validate_file(
                schema_name,
                path,
                formal=args.formal,
                paper_mapping_labels=paper_labels,
                locked_contracts=locked_contracts,
                raise_on_error=False,
            )
            payload = load_json_or_yaml(path)
        except SchemaValidationError as exc:
            report = exc.report
            payload = {}
        if schema_name == "paper_output" and paper_labels is None:
            report_issues = list(report.issues)
            report_issues.append(
                report_issue := {
                    "path": "$.paper_mapping",
                    "message": "paper outputs require --paper-mapping coverage validation",
                }
            )
            issues.append({"file": str(path), **report_issue})
            status = "invalid"
        else:
            report_issues = list(report.issues)
            status = report.status
        if report_issues:
            issues.extend({"file": str(path), **issue.to_dict()} for issue in report.issues)
        if isinstance(payload, dict):
            payload_for_cross = dict(payload)
            payload_for_cross["__path"] = _display_path(path)
            payload_for_cross["__abs_path"] = str(path)
            payload_for_cross["__sha256"] = sha256_file(path) if path.exists() else None
            result_objects.append((schema_name, payload_for_cross))
        files.append(
            {
                "path": _display_path(path),
                "schema": schema_name,
                "schema_version": payload.get("schema_version") if isinstance(payload, dict) else None,
                "sha256": sha256_file(path) if path.exists() else None,
                "status": status,
            }
        )

    if args.formal:
        cross_report = validate_cross_object_consistency([*context_objects, *result_objects], raise_on_error=False)
        if cross_report.issues:
            issues.extend({"file": "<cross-object>", **issue.to_dict()} for issue in cross_report.issues)

    response = {
        "status": "ok" if not issues else "invalid",
        "formal": args.formal,
        "files": files,
        "issues": issues,
    }
    if args.json:
        print(json.dumps(response, indent=2, sort_keys=True))
    else:
        print(f"status: {response['status']}")
        for item in files:
            print(f"{item['path']}: {item['schema']} {item['status']}")
        for issue in issues:
            print(f"{issue.get('file', '<unknown>')} {issue['path']}: {issue['message']}", file=sys.stderr)
    return 0 if not issues else 1


def _collect_inputs(args: argparse.Namespace) -> list[tuple[str, str]]:
    inputs: list[tuple[str, str]] = []
    for option, schema_name in RESULT_OPTIONS:
        for path in getattr(args, option):
            inputs.append((schema_name, path))
    return inputs


def _formal_context_requirement_issues(args: argparse.Namespace, issues: list[dict[str, str]]) -> None:
    missing = []
    if not args.paper_mapping:
        missing.append("--paper-mapping")
    if not args.manifest:
        missing.append("--manifest")
    if not args.freeze_manifest:
        missing.append("--freeze-manifest")
    if not args.evidence_contract:
        missing.append("--evidence-contract")
    if missing:
        issues.append(
            {
                "file": "<formal-context>",
                "path": "$",
                "message": "formal validation requires " + ", ".join(missing),
            }
        )


def _load_formal_context(
    args: argparse.Namespace,
    paper_labels: set[str] | None,
    issues: list[dict[str, str]],
    files: list[dict[str, Any]],
) -> list[tuple[str, Mapping[str, Any]]]:
    context: list[tuple[str, Mapping[str, Any]]] = []
    if args.manifest:
        loaded = _load_context_object("experiment_manifest", args.manifest, paper_labels, issues, files)
        if loaded is not None:
            context.append(("manifest", loaded))
    if args.freeze_manifest:
        loaded = _load_context_object("freeze_manifest", args.freeze_manifest, paper_labels, issues, files)
        if loaded is not None:
            with_hash = dict(loaded)
            with_hash["__sha256"] = sha256_file(resolve_repo_path(args.freeze_manifest))
            context.append(("freeze_manifest", with_hash))
    for index, evidence_contract in enumerate(args.evidence_contract):
        loaded = _load_context_object("evidence_contract", evidence_contract, paper_labels, issues, files)
        if loaded is not None:
            context.append((f"evidence_contract[{index}]", loaded))
    return context


def _load_context_object(
    schema_name: str,
    path_arg: str | Path,
    paper_labels: set[str] | None,
    issues: list[dict[str, str]],
    files: list[dict[str, Any]],
) -> Mapping[str, Any] | None:
    path = resolve_repo_path(path_arg)
    try:
        payload = load_json_or_yaml(path)
        report = validate_object(
            schema_name,
            payload,
            formal=True,
            paper_mapping_labels=paper_labels,
            raise_on_error=False,
        )
    except SchemaValidationError as exc:
        payload = None
        report = exc.report
    if report.issues:
        issues.extend({"file": str(path), **issue.to_dict()} for issue in report.issues)
    payload_for_return: Mapping[str, Any] | None = None
    if isinstance(payload, Mapping):
        annotated = dict(payload)
        annotated["__path"] = _display_path(path)
        annotated["__abs_path"] = str(path)
        annotated["__sha256"] = sha256_file(path) if path.exists() else None
        payload_for_return = annotated
    files.append(
        {
            "path": _display_path(path),
            "schema": schema_name,
            "schema_version": payload.get("schema_version") if isinstance(payload, dict) else None,
            "sha256": sha256_file(path) if path.exists() else None,
            "status": report.status,
        }
    )
    return payload_for_return


def _load_paper_mapping(
    path_arg: str | Path,
    issues: list[dict[str, str]],
    files: list[dict[str, Any]],
    *,
    formal: bool,
) -> tuple[set[str], Mapping[str, Any] | None]:
    path = resolve_repo_path(path_arg)
    if path.suffix.lower() == ".md":
        labels = extract_paper_mapping_labels(path)
        report = validate_paper_mapping_coverage(path, raise_on_error=False)
        payload: dict[str, Any] = {"schema_version": "paper_mapping.md"}
        if formal:
            issues.append(
                {
                    "file": str(path),
                    "path": "$.paper_mapping",
                    "message": "formal validation requires structured paper_mapping JSON with per-label source provenance",
                }
            )
    else:
        payload = load_json_or_yaml(path)
        schema_report = validate_object("paper_mapping", payload, formal=formal, raise_on_error=False)
        coverage_report = validate_paper_mapping_coverage(payload, raise_on_error=False)
        report_issues = list(schema_report.issues) + list(coverage_report.issues)
        labels = paper_mapping_labels_from_object(payload) if isinstance(payload, dict) else set()
        report = schema_report if report_issues else coverage_report
        if report_issues:
            issues.extend({"file": str(path), **issue.to_dict()} for issue in report_issues)
        files.append(
            {
                "path": _display_path(path),
                "schema": "paper_mapping",
                "schema_version": payload.get("schema_version") if isinstance(payload, dict) else None,
                "sha256": sha256_file(path) if path.exists() else None,
                "status": "ok" if not report_issues else "invalid",
            }
        )
        context = None
        if isinstance(payload, Mapping):
            annotated = dict(payload)
            annotated["__path"] = _display_path(path)
            annotated["__abs_path"] = str(path)
            annotated["__sha256"] = sha256_file(path) if path.exists() else None
            context = annotated
        return labels, context
    if not report.ok:
        issues.extend({"file": str(path), **issue.to_dict()} for issue in report.issues)
    files.append(
        {
            "path": _display_path(path),
            "schema": "paper_mapping_markdown_coverage",
            "schema_version": payload["schema_version"],
            "sha256": sha256_file(path) if path.exists() else None,
            "status": report.status,
        }
    )
    return labels, None


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(resolve_repo_path(".")))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    sys.exit(main())
