"""Build and strictly validate a case-packet source bundle.

The command is fail-closed: it writes to a temporary sibling file, validates
the manifest, packet-directory inventory, case identities, and file hashes,
and only then atomically publishes the requested output.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evidence_system.cli._common import BootstrapCommand
from evidence_system.contracts.case_packets import (
    CASE_PACKET_SCHEMA_VERSION,
    build_case_packet_source_bundle,
    case_packet_source_bundle_manifest_provenance,
    validate_case_packet_source,
)
from evidence_system.contracts.common import ContractLifecycleError, normalize_domain
from evidence_system.core.errors import EvidenceSystemError
from evidence_system.core.hashing import sha256_file
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml


DEFAULT_EXPECTED_COUNT = 949
DEFAULT_EXPECTED_DOMAIN = "agentdojo"
DEFAULT_EXPERIMENT_ROOT = "experiments/agentdojo_full_v1.2.2_direct"
DEFAULT_MANIFEST_PATH = f"{DEFAULT_EXPERIMENT_ROOT}/experiment_manifest.yaml"
DEFAULT_CASE_PACKETS_ROOT = f"{DEFAULT_EXPERIMENT_ROOT}/case_packets"
DEFAULT_OUTPUT_PATH = f"{DEFAULT_EXPERIMENT_ROOT}/source_bundles/case_packet_source_bundle.json"
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")

COMMAND = BootstrapCommand(
    name="build_case_packet_source_bundle",
    responsibility="Build a source bundle and fail closed unless its case set and packet hashes are exact.",
    owner_module="evidence_system.contracts.case_packets",
)


@dataclass(frozen=True)
class ManifestCase:
    domain: str
    case_unit_id: str
    task_id: str
    dataset_name: str | None = None
    source_ref: str | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_system.cli.build_case_packet_source_bundle",
        description=COMMAND.responsibility,
    )
    parser.add_argument("--bootstrap-check", action="store_true")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--case-packets-root", default=DEFAULT_CASE_PACKETS_ROOT)
    parser.add_argument(
        "--previous-source-bundle",
        help="Bundle whose contract IDs should be preserved; defaults to --output when it already exists.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_PATH,
    )
    parser.add_argument(
        "--expected-count",
        type=_positive_int,
        default=DEFAULT_EXPECTED_COUNT,
        help=f"Required manifest and bundle count (default: {DEFAULT_EXPECTED_COUNT}).",
    )
    parser.add_argument(
        "--expected-domain",
        action="append",
        help=f"Required domain set; repeat for multiple domains (default: {DEFAULT_EXPECTED_DOMAIN}).",
    )
    parser.add_argument(
        "--allow-generated-contract-ids",
        action="store_true",
        help="Generate deterministic contract IDs for cases absent from the previous bundle.",
    )
    parser.add_argument("--json", action="store_true")
    return parser


def build_and_validate_source_bundle(
    *,
    manifest_path: str | Path,
    case_packets_root: str | Path,
    output_path: str | Path,
    previous_source_bundle_path: str | Path | None,
    expected_count: int,
    expected_domains: Sequence[str],
    allow_generated_contract_ids: bool,
) -> dict[str, Any]:
    """Build, validate, and atomically publish one source bundle."""

    normalized_domains = tuple(sorted({normalize_domain(value) for value in expected_domains}))
    expected_cases = load_manifest_cases_strict(
        manifest_path,
        expected_count=expected_count,
        expected_domains=normalized_domains,
    )
    validate_packet_directory_set(case_packets_root, expected_cases)

    output_resolved = resolve_repo_path(output_path)
    output_resolved.parent.mkdir(parents=True, exist_ok=True)
    previous_path = previous_source_bundle_path
    if previous_path is None and output_resolved.exists():
        previous_path = output_resolved
    if previous_path is None:
        previous_path = output_resolved.with_name(f".{output_resolved.name}.no_previous_bundle")
    manifest_payload = load_json_or_yaml(manifest_path)
    manifest_binds_source_bundle = (
        isinstance(manifest_payload, Mapping) and "source_bundle_hash" in manifest_payload
    )

    with tempfile.NamedTemporaryFile(
        prefix=f".{output_resolved.name}.",
        suffix=".tmp",
        dir=output_resolved.parent,
        delete=False,
    ) as handle:
        temporary_path = Path(handle.name)
    try:
        build_case_packet_source_bundle(
            manifest_path=manifest_path,
            case_packets_root=case_packets_root,
            previous_source_bundle_path=previous_path,
            output_path=temporary_path,
            allow_generated_contract_ids=allow_generated_contract_ids,
            include_manifest_sha256=not manifest_binds_source_bundle,
        )
        audit = validate_source_bundle_strict(
            source_bundle_path=temporary_path,
            manifest_path=manifest_path,
            case_packets_root=case_packets_root,
            expected_cases=expected_cases,
            expected_count=expected_count,
            expected_domains=normalized_domains,
        )
        temporary_path.replace(output_resolved)
        output_resolved.chmod(0o644)
    finally:
        temporary_path.unlink(missing_ok=True)

    return {
        "status": "ok",
        "source_bundle_path": _repo_relative(output_resolved),
        "source_bundle_sha256": sha256_file(output_resolved),
        **audit,
    }


def load_manifest_cases_strict(
    manifest_path: str | Path,
    *,
    expected_count: int,
    expected_domains: Sequence[str],
) -> list[ManifestCase]:
    payload = load_json_or_yaml(manifest_path)
    if not isinstance(payload, Mapping):
        raise ContractLifecycleError("experiment manifest must be a mapping")
    domain_blocks = payload.get("domains")
    if not isinstance(domain_blocks, list) or not domain_blocks:
        raise ContractLifecycleError("experiment manifest requires a non-empty domains list")

    cases: list[ManifestCase] = []
    seen_domain_blocks: set[str] = set()
    for domain_index, block in enumerate(domain_blocks):
        if not isinstance(block, Mapping):
            raise ContractLifecycleError(f"manifest domains[{domain_index}] must be a mapping")
        domain = normalize_domain(block.get("domain"))
        if domain in seen_domain_blocks:
            raise ContractLifecycleError(f"manifest has duplicate domain block: {domain}")
        seen_domain_blocks.add(domain)
        case_units = block.get("case_units")
        if not isinstance(case_units, list):
            raise ContractLifecycleError(f"manifest domain {domain} requires a case_units list")
        declared_count = block.get("case_unit_count")
        if not isinstance(declared_count, int) or isinstance(declared_count, bool):
            raise ContractLifecycleError(f"manifest domain {domain} requires integer case_unit_count")
        if declared_count != len(case_units):
            raise ContractLifecycleError(
                f"manifest domain {domain} case_unit_count mismatch: "
                f"declared={declared_count}, actual={len(case_units)}"
            )
        for case_index, case in enumerate(case_units):
            if not isinstance(case, Mapping):
                raise ContractLifecycleError(f"manifest {domain}.case_units[{case_index}] must be a mapping")
            case_unit_id = _required_string(case, "case_unit_id", f"manifest {domain}.case_units[{case_index}]")
            task_id = _required_string(case, "task_id", f"manifest {domain}.case_units[{case_index}]")
            dataset_name = str(case.get("dataset_name") or case.get("split") or "").strip() or None
            source_ref = str(case.get("source_ref") or "").strip() or None
            cases.append(
                ManifestCase(
                    domain=domain,
                    case_unit_id=case_unit_id,
                    task_id=task_id,
                    dataset_name=dataset_name,
                    source_ref=source_ref,
                )
            )

    if len(cases) != expected_count:
        raise ContractLifecycleError(f"manifest case count mismatch: expected={expected_count}, actual={len(cases)}")
    actual_domains = {case.domain for case in cases}
    required_domains = set(expected_domains)
    if actual_domains != required_domains:
        raise ContractLifecycleError(
            "manifest domain set mismatch: "
            f"expected={sorted(required_domains)}, actual={sorted(actual_domains)}"
        )
    duplicate_ids = sorted(
        case_id
        for case_id, count in Counter(case.case_unit_id for case in cases).items()
        if count > 1
    )
    if duplicate_ids:
        raise ContractLifecycleError(f"manifest contains duplicate case_unit_id values: {duplicate_ids[:10]}")
    duplicate_dirs = sorted(
        directory
        for directory, count in Counter(
            (case.domain, _safe_case_dir_name(case.case_unit_id)) for case in cases
        ).items()
        if count > 1
    )
    if duplicate_dirs:
        raise ContractLifecycleError(f"manifest case IDs collide after directory normalization: {duplicate_dirs[:10]}")
    return cases


def validate_packet_directory_set(case_packets_root: str | Path, expected_cases: Sequence[ManifestCase]) -> None:
    root = resolve_repo_path(case_packets_root)
    if not root.is_dir():
        raise ContractLifecycleError(f"case-packets root is missing or not a directory: {root}")
    expected = {(case.domain, _safe_case_dir_name(case.case_unit_id)) for case in expected_cases}
    actual: set[tuple[str, str]] = set()
    for domain_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        for case_dir in sorted(path for path in domain_dir.iterdir() if path.is_dir()):
            actual.add((domain_dir.name, case_dir.name))
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ContractLifecycleError(
            "case-packet directory set mismatch: "
            f"missing={missing[:10]}, extra={extra[:10]}, expected_count={len(expected)}, actual_count={len(actual)}"
        )


def validate_source_bundle_strict(
    *,
    source_bundle_path: str | Path,
    manifest_path: str | Path,
    case_packets_root: str | Path,
    expected_cases: Sequence[ManifestCase],
    expected_count: int,
    expected_domains: Sequence[str],
) -> dict[str, Any]:
    # Re-check immediately before bundle acceptance so a directory added or
    # removed during hashing cannot pass on the initial preflight alone.
    validate_packet_directory_set(case_packets_root, expected_cases)
    payload = load_json_or_yaml(source_bundle_path)
    if not isinstance(payload, Mapping):
        raise ContractLifecycleError("generated source bundle must be a mapping")
    if payload.get("schema_version") != CASE_PACKET_SCHEMA_VERSION:
        raise ContractLifecycleError(
            f"source bundle schema mismatch: expected={CASE_PACKET_SCHEMA_VERSION}, "
            f"actual={payload.get('schema_version')!r}"
        )
    expected_manifest_ref = _repo_relative(resolve_repo_path(manifest_path))
    if payload.get("manifest_path") != expected_manifest_ref:
        raise ContractLifecycleError(
            f"source bundle manifest_path mismatch: expected={expected_manifest_ref!r}, "
            f"actual={payload.get('manifest_path')!r}"
        )
    if Path(expected_manifest_ref).is_absolute():
        raise ContractLifecycleError("manifest and case packets must be inside the repository")
    manifest_payload = load_json_or_yaml(manifest_path)
    manifest_binds_source_bundle = (
        isinstance(manifest_payload, Mapping) and "source_bundle_hash" in manifest_payload
    )
    expected_manifest_provenance = case_packet_source_bundle_manifest_provenance(
        manifest_path,
        include_manifest_sha256=not manifest_binds_source_bundle,
    )
    for field, expected_value in expected_manifest_provenance.items():
        if payload.get(field) != expected_value:
            raise ContractLifecycleError(
                f"source bundle {field} mismatch: "
                f"expected={expected_value!r}, actual={payload.get(field)!r}"
            )
    if manifest_binds_source_bundle and "manifest_sha256" in payload:
        raise ContractLifecycleError(
            "source bundle must not embed the full manifest SHA-256 when the manifest embeds source_bundle_hash"
        )

    sources = payload.get("sources")
    if not isinstance(sources, list):
        raise ContractLifecycleError("source bundle requires a sources list")
    if payload.get("source_count") != len(sources):
        raise ContractLifecycleError(
            f"source_count mismatch: declared={payload.get('source_count')!r}, actual={len(sources)}"
        )
    if len(sources) != expected_count:
        raise ContractLifecycleError(f"source bundle count mismatch: expected={expected_count}, actual={len(sources)}")

    expected_order = [case.case_unit_id for case in expected_cases]
    source_ids: list[str] = []
    contract_ids: list[str] = []
    source_by_id: dict[str, Mapping[str, Any]] = {}
    for index, source in enumerate(sources):
        if not isinstance(source, Mapping):
            raise ContractLifecycleError(f"source bundle sources[{index}] must be a mapping")
        case_unit_id = _required_string(source, "case_unit_id", f"source bundle sources[{index}]")
        contract_id = _required_string(source, "contract_id", f"source bundle sources[{index}]")
        source_ids.append(case_unit_id)
        contract_ids.append(contract_id)
        source_by_id[case_unit_id] = source
    if len(set(source_ids)) != len(source_ids):
        duplicates = sorted(case_id for case_id, count in Counter(source_ids).items() if count > 1)
        raise ContractLifecycleError(f"source bundle contains duplicate case_unit_id values: {duplicates[:10]}")
    if len(set(contract_ids)) != len(contract_ids):
        duplicates = sorted(contract_id for contract_id, count in Counter(contract_ids).items() if count > 1)
        raise ContractLifecycleError(f"source bundle contains duplicate contract_id values: {duplicates[:10]}")
    if set(source_ids) != set(expected_order):
        missing = sorted(set(expected_order) - set(source_ids))
        extra = sorted(set(source_ids) - set(expected_order))
        raise ContractLifecycleError(f"source bundle case ID set mismatch: missing={missing[:10]}, extra={extra[:10]}")
    if source_ids != expected_order:
        raise ContractLifecycleError("source bundle case order does not exactly match manifest order")

    packet_root = resolve_repo_path(case_packets_root)
    hash_count = 0
    raw_case_hash_count = 0
    issues: list[str] = []
    for index, case in enumerate(expected_cases):
        source = source_by_id[case.case_unit_id]
        if source.get("domain") != case.domain:
            issues.append(f"$.sources[{index}].domain: expected {case.domain!r}, got {source.get('domain')!r}")
        if source.get("task_id") != case.task_id:
            issues.append(f"$.sources[{index}].task_id: expected {case.task_id!r}, got {source.get('task_id')!r}")
        if case.dataset_name is not None and source.get("dataset_name") != case.dataset_name:
            issues.append(
                f"$.sources[{index}].dataset_name: expected {case.dataset_name!r}, "
                f"got {source.get('dataset_name')!r}"
            )
        if case.source_ref is not None and source.get("source_ref") != case.source_ref:
            issues.append(
                f"$.sources[{index}].source_ref: expected {case.source_ref!r}, got {source.get('source_ref')!r}"
            )
        for issue in validate_case_packet_source(source, f"$.sources[{index}]"):
            issues.append(f"{issue.path}: {issue.message}")

        draft_input = source.get("draft_input")
        if not isinstance(draft_input, Mapping):
            continue
        case_dir = packet_root / case.domain / _safe_case_dir_name(case.case_unit_id)
        expected_paths = {
            "case_packet_path": case_dir / "case_packet.md",
            "raw_case_manifest_path": case_dir / "raw_case_manifest.json",
        }
        for path_field, expected_path in expected_paths.items():
            value = draft_input.get(path_field)
            if isinstance(value, str) and resolve_repo_path(value).resolve() != expected_path.resolve():
                issues.append(
                    f"$.sources[{index}].draft_input.{path_field}: "
                    f"expected {_repo_relative(expected_path)!r}, got {value!r}"
                )
        for hash_field in ("case_packet_sha256", "raw_case_manifest_sha256"):
            value = draft_input.get(hash_field)
            if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None:
                issues.append(f"$.sources[{index}].draft_input.{hash_field}: must be a lowercase SHA-256 hex digest")
            else:
                hash_count += 1

        raw_manifest_path = draft_input.get("raw_case_manifest_path")
        if isinstance(raw_manifest_path, str) and resolve_repo_path(raw_manifest_path).is_file():
            raw_manifest = load_json_or_yaml(raw_manifest_path)
            if not isinstance(raw_manifest, Mapping):
                issues.append(f"$.sources[{index}].draft_input.raw_case_manifest_path: must contain a mapping")
            else:
                for field, expected_value in (
                    ("domain", case.domain),
                    ("case_unit_id", case.case_unit_id),
                    ("task_id", case.task_id),
                ):
                    if raw_manifest.get(field) != expected_value:
                        issues.append(
                            f"$.sources[{index}].raw_case_manifest.{field}: "
                            f"expected {expected_value!r}, got {raw_manifest.get(field)!r}"
                        )
                for field, expected_value in (
                    ("dataset_name", case.dataset_name),
                    ("source_ref", case.source_ref),
                ):
                    if expected_value is not None and raw_manifest.get(field) != expected_value:
                        issues.append(
                            f"$.sources[{index}].raw_case_manifest.{field}: "
                            f"expected {expected_value!r}, got {raw_manifest.get(field)!r}"
                        )
                inventory_issues, inventory_hash_count = _validate_raw_case_inventory(
                    raw_manifest,
                    case_dir=case_dir,
                    base=f"$.sources[{index}].raw_case_manifest",
                )
                issues.extend(inventory_issues)
                raw_case_hash_count += inventory_hash_count
    if issues:
        raise ContractLifecycleError("strict source-bundle validation failed: " + "; ".join(issues[:12]))
    if hash_count != expected_count * 2:
        raise ContractLifecycleError(
            f"verified hash field count mismatch: expected={expected_count * 2}, actual={hash_count}"
        )

    actual_domains = sorted({str(source["domain"]) for source in sources})
    if actual_domains != sorted(expected_domains):
        raise ContractLifecycleError(
            f"source bundle domain set mismatch: expected={sorted(expected_domains)}, actual={actual_domains}"
        )
    return {
        "expected_count": expected_count,
        "manifest_case_count": len(expected_cases),
        "source_count": len(sources),
        "domains": actual_domains,
        "exact_case_id_set_verified": True,
        "manifest_order_verified": True,
        "packet_directory_set_verified": True,
        "verified_file_hash_count": hash_count,
        "verified_raw_case_file_hash_count": raw_case_hash_count,
    }


def _validate_raw_case_inventory(
    raw_manifest: Mapping[str, Any],
    *,
    case_dir: Path,
    base: str,
) -> tuple[list[str], int]:
    """Validate the exact raw_case inventory and every declared file hash."""

    issues: list[str] = []
    raw_dir = case_dir / "raw_case"
    if not raw_dir.is_dir() or raw_dir.is_symlink():
        return [f"{base}: raw_case must be a real directory"], 0

    tree_entries = list(raw_dir.rglob("*"))
    symlinks = sorted(str(path.relative_to(raw_dir)) for path in tree_entries if path.is_symlink())
    if symlinks:
        issues.append(f"{base}: raw_case contains symlinks: {symlinks[:5]}")
    actual_files = {
        str(path.relative_to(raw_dir)).replace("\\", "/")
        for path in tree_entries
        if path.is_file() and not path.is_symlink()
    }

    copied_value = raw_manifest.get("copied_files")
    copied_files = copied_value if isinstance(copied_value, list) else []
    if not isinstance(copied_value, list) or any(not isinstance(value, str) for value in copied_files):
        issues.append(f"{base}.copied_files: must be a list of relative paths")
        copied_files = []
    declared_files: set[str] = set()
    for value in copied_files:
        relative = Path(value)
        if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != value:
            issues.append(f"{base}.copied_files: unsafe path {value!r}")
            continue
        declared_files.add(value)
    if len(declared_files) != len(copied_files):
        issues.append(f"{base}.copied_files: duplicate or unsafe entries")
    if declared_files != actual_files:
        issues.append(
            f"{base}.copied_files: inventory mismatch "
            f"missing={sorted(actual_files - declared_files)[:5]}, "
            f"extra={sorted(declared_files - actual_files)[:5]}"
        )

    hashes_value = raw_manifest.get("sha256_per_file")
    hashes = hashes_value if isinstance(hashes_value, Mapping) else {}
    if not isinstance(hashes_value, Mapping):
        issues.append(f"{base}.sha256_per_file: must be a mapping")
    if set(hashes) != declared_files:
        issues.append(f"{base}.sha256_per_file: keys must exactly equal copied_files")
    verified = 0
    for relative in sorted(declared_files & actual_files):
        expected = hashes.get(relative)
        if not isinstance(expected, str) or SHA256_PATTERN.fullmatch(expected) is None:
            issues.append(f"{base}.sha256_per_file.{relative}: invalid SHA-256")
            continue
        actual = sha256_file(raw_dir / relative)
        if actual != expected:
            issues.append(
                f"{base}.sha256_per_file.{relative}: expected={expected}, actual={actual}"
            )
            continue
        verified += 1

    for field in ("official_files", "derived_files", "packet_files"):
        values = raw_manifest.get(field)
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            issues.append(f"{base}.{field}: must be a list of relative paths")
            continue
        extras = sorted(set(values) - declared_files)
        if extras:
            issues.append(f"{base}.{field}: entries not present in copied_files: {extras[:5]}")
    file_sources = raw_manifest.get("file_sources")
    if file_sources is not None:
        if not isinstance(file_sources, Mapping):
            issues.append(f"{base}.file_sources: must be a mapping")
        else:
            extras = sorted(set(file_sources) - declared_files)
            if extras:
                issues.append(f"{base}.file_sources: entries not present in copied_files: {extras[:5]}")
    return issues, verified


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    expected_domains = args.expected_domain or [DEFAULT_EXPECTED_DOMAIN]
    if args.bootstrap_check:
        payload = {
            "name": COMMAND.name,
            "responsibility": COMMAND.responsibility,
            "owner_module": COMMAND.owner_module,
            "status": "ok",
            "default_expected_count": DEFAULT_EXPECTED_COUNT,
            "default_expected_domain": DEFAULT_EXPECTED_DOMAIN,
            "default_manifest_path": DEFAULT_MANIFEST_PATH,
            "default_case_packets_root": DEFAULT_CASE_PACKETS_ROOT,
            "default_output_path": DEFAULT_OUTPUT_PATH,
        }
        _emit(payload, args.json)
        return 0
    try:
        payload = build_and_validate_source_bundle(
            manifest_path=args.manifest,
            case_packets_root=args.case_packets_root,
            output_path=args.output,
            previous_source_bundle_path=args.previous_source_bundle,
            expected_count=args.expected_count,
            expected_domains=expected_domains,
            allow_generated_contract_ids=args.allow_generated_contract_ids,
        )
    except (EvidenceSystemError, OSError) as exc:
        payload = {"status": "blocked", "reason": str(exc)}
        _emit(payload, args.json, file=sys.stderr)
        return 2
    _emit(payload, args.json)
    return 0


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _required_string(payload: Mapping[str, Any], field: str, base: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ContractLifecycleError(f"{base}.{field} must be a non-empty string")
    return value


def _safe_case_dir_name(case_unit_id: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", case_unit_id).strip("_")
    return text or "case"


def _repo_relative(path: str | Path) -> str:
    resolved = resolve_repo_path(path)
    try:
        return str(resolved.relative_to(resolve_repo_path(".")))
    except ValueError:
        return str(resolved)


def _emit(payload: Mapping[str, Any], as_json: bool, *, file: Any = None) -> None:
    stream = file or sys.stdout
    if as_json:
        print(json.dumps(dict(payload), indent=2, sort_keys=True), file=stream)
        return
    for key, value in payload.items():
        print(f"{key}: {value}", file=stream)


if __name__ == "__main__":
    sys.exit(main())
