"""Validate experiment manifests and paper-mapping coverage."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from evidence_system.cli._common import BootstrapCommand, bootstrap_main
from evidence_system.core.hashing import sha256_file
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import (
    REQUIRED_PAPER_LABELS,
    SchemaValidationError,
    extract_paper_mapping_labels,
    load_json_or_yaml,
    paper_mapping_labels_from_object,
    validate_object,
    validate_paper_mapping_coverage,
)


COMMAND = BootstrapCommand(
    name="validate_manifest",
    responsibility="Validate experiment manifests and paper mapping coverage.",
    owner_module="evidence_system.core.schemas",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_system.cli.validate_manifest",
        description=COMMAND.responsibility,
    )
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--manifest", help="experiment_manifest/v1 JSON or YAML file.")
    parser.add_argument(
        "--paper-mapping",
        default="experiments/paper_mapping.md",
        help="paper_mapping/v1 JSON file or the frozen paper_mapping.md.",
    )
    parser.add_argument("--formal", action="store_true", help="Apply formal fail-closed gates.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.bootstrap_check:
        return bootstrap_main(COMMAND, ["--bootstrap-check", *(["--json"] if args.json else [])])
    if not args.manifest:
        parser.error("--manifest is required unless --bootstrap-check is used")

    issues: list[dict[str, str]] = []
    files: list[dict[str, Any]] = []
    paper_labels: set[str] | None = None
    paper_mapping_context: dict[str, Any] | None = None

    try:
        paper_labels, paper_mapping_context = _load_and_validate_paper_mapping(args.paper_mapping, issues, files, formal=args.formal)
    except SchemaValidationError as exc:
        issues.extend(issue.to_dict() for issue in exc.report.issues)

    manifest_path = resolve_repo_path(args.manifest)
    try:
        manifest = load_json_or_yaml(manifest_path)
        report = validate_object(
            "experiment_manifest",
            manifest,
            formal=args.formal,
            paper_mapping_labels=paper_labels,
            raise_on_error=False,
        )
    except SchemaValidationError as exc:
        report = exc.report
        manifest = {}
    if not report.ok:
        issues.extend({"file": str(manifest_path), **issue.to_dict()} for issue in report.issues)
    if args.formal and isinstance(manifest, dict) and paper_mapping_context is not None:
        paper_sha = paper_mapping_context.get("__sha256")
        if paper_sha is not None and manifest.get("paper_mapping_sha256") != paper_sha:
            issues.append(
                {
                    "file": str(manifest_path),
                    "path": "$.paper_mapping_sha256",
                    "message": "manifest paper_mapping_sha256 must match loaded paper_mapping sha256",
                }
            )
    files.append(
        {
            "path": _display_path(manifest_path),
            "schema": "experiment_manifest",
            "schema_version": manifest.get("schema_version") if isinstance(manifest, dict) else None,
            "sha256": sha256_file(manifest_path) if manifest_path.exists() else None,
            "status": report.status,
        }
    )

    payload = {
        "status": "ok" if not issues else "invalid",
        "formal": args.formal,
        "required_paper_label_count": len(REQUIRED_PAPER_LABELS),
        "files": files,
        "issues": issues,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"status: {payload['status']}")
        for item in files:
            print(f"{item['path']}: {item['schema']} {item['status']}")
        for issue in issues:
            print(f"{issue.get('file', args.manifest)} {issue['path']}: {issue['message']}", file=sys.stderr)
    return 0 if not issues else 1


def _load_and_validate_paper_mapping(
    path_arg: str | Path,
    issues: list[dict[str, str]],
    files: list[dict[str, Any]],
    *,
    formal: bool,
) -> tuple[set[str], dict[str, Any] | None]:
    path = resolve_repo_path(path_arg)
    if path.suffix.lower() == ".md":
        labels = extract_paper_mapping_labels(path)
        report = validate_paper_mapping_coverage(path, raise_on_error=False)
        if formal:
            issues.append(
                {
                    "file": str(path),
                    "path": "$.paper_mapping",
                    "message": "formal validation requires structured paper_mapping JSON with per-label source provenance",
                }
            )
        if not report.ok:
            issues.extend({"file": str(path), **issue.to_dict()} for issue in report.issues)
        files.append(
            {
                "path": _display_path(path),
                "schema": "paper_mapping_markdown_coverage",
                "schema_version": "paper_mapping.md",
                "sha256": sha256_file(path) if path.exists() else None,
                "status": report.status,
            }
        )
        return labels, None

    payload = load_json_or_yaml(path)
    schema_report = validate_object("paper_mapping", payload, formal=formal, raise_on_error=False)
    coverage_report = validate_paper_mapping_coverage(payload, raise_on_error=False)
    labels = paper_mapping_labels_from_object(payload) if isinstance(payload, dict) else set()
    for report in (schema_report, coverage_report):
        if not report.ok:
            issues.extend({"file": str(path), **issue.to_dict()} for issue in report.issues)
    files.append(
        {
            "path": _display_path(path),
            "schema": "paper_mapping",
            "schema_version": payload.get("schema_version") if isinstance(payload, dict) else None,
            "sha256": sha256_file(path) if path.exists() else None,
            "status": "ok" if schema_report.ok and coverage_report.ok else "invalid",
        }
    )
    context = None
    if isinstance(payload, dict):
        context = dict(payload)
        context["__path"] = _display_path(path)
        context["__abs_path"] = str(path)
        context["__sha256"] = sha256_file(path) if path.exists() else None
    return labels, context


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(resolve_repo_path(".")))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    sys.exit(main())
