#!/usr/bin/env python3
"""Fail-closed freeze publisher for the 22 MiniWoB case checklists.

This publisher keeps raw model drafts immutable, accepts one explicitly audited
reviewed-candidate layer, emits canonical checklist and file locks, and advances
the remaining-22 manifest/source-bundle pair to a hash-consistent frozen state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml
from jsonschema import Draft202012Validator


SCRIPT_DIR = Path(__file__).resolve().parent
MINIMAL_ROOT = SCRIPT_DIR.parent
PACKAGE_ROOT = MINIMAL_ROOT.parent
for import_root in (PACKAGE_ROOT, PACKAGE_ROOT / "src"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from evidence_system.core.hashing import canonical_json_bytes, sha256_file, sha256_object, sha256_path  # noqa: E402
from neurips_ed_track_minimal.scripts import update_case_locks as case_locks  # noqa: E402
from neurips_ed_track_minimal.scripts.checklist_validator import (  # noqa: E402
    ChecklistValidationError,
    _iter_supports,
    load_checklist,
    validate_packet_required_stronger_conditions,
    validate_support_pointers,
)
from neurips_ed_track_minimal.checklist_guardrails import (  # noqa: E402
    ChecklistGuardrailError,
    case_packet_support_paths,
    validate_checklist_guardrails,
)


DEFAULT_MANIFEST = PACKAGE_ROOT / "experiments/appendix/miniwob_remaining22_manifest.yaml"
DEFAULT_SOURCE_BUNDLE = (
    PACKAGE_ROOT
    / "experiments/evidence_contracts/source_bundles/miniwob_remaining22_case_units_source_bundle.json"
)
DEFAULT_PACKET_ROOT = (
    PACKAGE_ROOT / "experiments/case_packets_extensions/miniwob_remaining22/miniwob"
)
DEFAULT_DRAFT_PROMPT = MINIMAL_ROOT / "prompts/draft_case_checklist.prompt.md"
DEFAULT_SCORE_PROMPT = MINIMAL_ROOT / "prompts/score_evidence_with_codex.prompt.md"
DEFAULT_CHECKLIST_SCHEMA = MINIMAL_ROOT / "schemas/case_checklist.schema.json"
DEFAULT_SCORE_SCHEMA = MINIMAL_ROOT / "schemas/evidence_score.schema.json"
DEFAULT_MANIFEST_SCHEMA = PACKAGE_ROOT / "schemas/experiment_manifest.schema.json"
DEFAULT_RESULTS_ROOT = PACKAGE_ROOT / "results/namespaces/miniwob_remaining22_bg0143_v1"

EXPECTED_COUNT = 22
EXPECTED_DOMAIN = "miniwob"
EXPECTED_TAXONOMY = "R1-R7_paper_taxonomy_v0.1.0"
EXPECTED_FINAL_CHECKLIST_SHA256 = {
    "miniwob.click-checkboxes": "15e78b1f11e48a185007cc393fafd9db69f7b177ed2b273f6ed25e88acf55960",
    "miniwob.click-dialog": "989570fa63849ae58b656bee01c6f5b96267e75c705cd6dc2fc7302d889cd7f9",
    "miniwob.click-option": "cd39fe362553c8569eb5470a78e0c57e6c190da19e92be6aef7e79bd829251bb",
    "miniwob.click-pie-nodelay": "209b91afa0adb8d97a9e43a092c895ea1fdf0919c403cf7a5eb7027edc77cca6",
    "miniwob.click-shades": "5c3d14d12964c0165e5c8f83b69c6ac5444810247cb653a7918e49d619119a97",
    "miniwob.click-shape": "2bf15d97ecee1d0b8a9296838133b6d7aff45bc2ab621271faecef7c0204d292",
    "miniwob.click-test-2": "748c16b78d70ae5652d7dbb1f859da083f024d607affd5ad432cde6c61db69c4",
    "miniwob.count-shape": "c7bb91fdcf06a1a233988f1c330401dc8376f546a92673c4c6ba7b60cf901aa0",
    "miniwob.drag-items": "e8dd4a8fb86d9100ab4d8d76268e0690b3ed36b130b47f8954ff26b182094ece",
    "miniwob.draw-circle": "1a47186817b7ed9674d43559d414d095f6e04aca9ec5d55962be96116682758f",
    "miniwob.email-inbox-forward": "2cef230aa44676e4185b64a050d10978e60328b8fee4a6d78c3a5620bfe172f3",
    "miniwob.email-inbox-forward-nl-turk": "ce69d9266f0a6edf2c45db155a9702995d3bddaaf3e65704ee5c286263d9770b",
    "miniwob.email-inbox-star-reply": "518b91fe69a87a3b46f1b69c0ecf6963aef4f15dfe0403b4e2128953d49863c2",
    "miniwob.enter-text-2": "0d7acaff08d841ff4967d8454a7f305a7823fcb862e5709e8108dfe6fe6af7cc",
    "miniwob.enter-time": "14cf0e7ff583b579b3e0f9d5a3deb40025dc84d856ecd1350aed609c85374095",
    "miniwob.focus-text-2": "e47349310ae51f398b88d91acf0b7ee7892c83c544e31953e893fc378de54c99",
    "miniwob.generate-number": "38ed9631e5524a5c770250707a25d4e0a3e23d8ad971fff4ae9822e7fdc94f52",
    "miniwob.odd-or-even": "a2c999d9be30b2b076c62107644895480d157ff9be3879637a753893a765192f",
    "miniwob.terminal": "a05a94fbdaaafbfd7183f970d10f9d81253c75313a951af7a5b367d91a6393a5",
    "miniwob.use-autocomplete": "ba34febfc426239278693007c92a78b397eb127a8a010ad96385a6e30f12935f",
    "miniwob.use-colorwheel-2": "3ba95b0e7dbb3236dc632909c26017a431997d9480c2092cc6420cb43b9ee564",
    "miniwob.use-slider": "8f7e19c4e95d2f8f4e4c3efd15e0af50c42c7d5e6b651f3a8e433b608b835443",
}
UNCHANGED_CASES = {
    "miniwob.click-checkboxes",
    "miniwob.use-autocomplete",
}
CORRECTION_REASONS = {
    "miniwob.focus-text-2": (
        "Identify the released validator in checked_by and bind Unknown to evaluator output, not input."
    ),
    "miniwob.email-inbox-forward": (
        "State the native oracle exactly, remove task context as standalone success evidence, cover other "
        "benchmark-counted failures, and add the source-supported sender-identity stronger condition."
    ),
    "miniwob.email-inbox-forward-nl-turk": (
        "Add the source-supported sender-identity stronger condition omitted from the generated draft."
    ),
    "miniwob.use-colorwheel-2": (
        "Cover other benchmark-counted failures and allow equivalent final task-state evidence before Unknown."
    ),
}
FORBIDDEN_OUTCOME_MARKERS = (
    "Agent A",
    "Agent B",
    "Agent C",
    '"native_score"',
    '"outcome_label"',
    '"evidence_label"',
    '"response_id"',
    '"api_response"',
)


class MiniwobChecklistFreezeError(RuntimeError):
    """Raised when any precondition for publishing the freeze fails."""


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source-bundle", type=Path, default=DEFAULT_SOURCE_BUNDLE)
    parser.add_argument("--case-packet-root", type=Path, default=DEFAULT_PACKET_ROOT)
    parser.add_argument("--raw-draft-root", type=Path, required=True)
    parser.add_argument("--reviewed-root", type=Path, required=True)
    parser.add_argument("--generation-manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--draft-prompt", type=Path, default=DEFAULT_DRAFT_PROMPT)
    parser.add_argument("--score-prompt", type=Path, default=DEFAULT_SCORE_PROMPT)
    parser.add_argument("--checklist-schema", type=Path, default=DEFAULT_CHECKLIST_SCHEMA)
    parser.add_argument("--score-schema", type=Path, default=DEFAULT_SCORE_SCHEMA)
    parser.add_argument("--manifest-schema", type=Path, default=DEFAULT_MANIFEST_SCHEMA)
    parser.add_argument("--locked-at", default=None)
    parser.add_argument("--manifest-version", default="1.0.0")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def _require_file(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.resolve().is_file():
        raise MiniwobChecklistFreezeError(f"{label} is missing, not regular, or a symlink: {path}")
    return path.resolve()


def _require_dir(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.resolve().is_dir():
        raise MiniwobChecklistFreezeError(f"{label} is missing, not a directory, or a symlink: {path}")
    return path.resolve()


def _load_mapping(path: Path, label: str) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        value = json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise MiniwobChecklistFreezeError(f"failed to parse {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MiniwobChecklistFreezeError(f"{label} must be a mapping: {path}")
    return value


def _display(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(PACKAGE_ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _diff_paths(left: Any, right: Any, path: str = "$") -> set[str]:
    if type(left) is not type(right):
        return {path}
    if isinstance(left, dict):
        paths: set[str] = set()
        for key in sorted(set(left) | set(right)):
            child = f"{path}.{key}"
            if key not in left or key not in right:
                paths.add(child)
            else:
                paths.update(_diff_paths(left[key], right[key], child))
        return paths
    if isinstance(left, list):
        paths = set()
        for index in range(max(len(left), len(right))):
            child = f"{path}[{index}]"
            if index >= len(left) or index >= len(right):
                paths.add(child)
            else:
                paths.update(_diff_paths(left[index], right[index], child))
        return paths
    return set() if left == right else {path}


def _validate_checklist(
    *,
    checklist: dict[str, Any],
    packet_path: Path,
    schema_validator: Draft202012Validator,
    case_id: str,
) -> int:
    errors = sorted(
        schema_validator.iter_errors(checklist),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if errors:
        rendered = "; ".join(
            f"{'.'.join(str(item) for item in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors
        )
        raise MiniwobChecklistFreezeError(f"checklist schema failed for {case_id}: {rendered}")
    if checklist.get("domain") != EXPECTED_DOMAIN or checklist.get("case_unit_id") != case_id:
        raise MiniwobChecklistFreezeError(f"checklist identity mismatch for {case_id}")
    if checklist.get("task_id") != case_id:
        raise MiniwobChecklistFreezeError(f"MiniWoB task identity mismatch for {case_id}")
    try:
        allowed = case_packet_support_paths(packet_path.read_text(encoding="utf-8"))
        validate_checklist_guardrails(checklist, allowed_source_paths=allowed)
        validate_support_pointers(checklist, packet_path)
        validate_packet_required_stronger_conditions(checklist, packet_path)
    except (ChecklistGuardrailError, ChecklistValidationError) as exc:
        raise MiniwobChecklistFreezeError(f"checklist guardrail failed for {case_id}: {exc}") from exc
    serialized = json.dumps(checklist, ensure_ascii=False, sort_keys=True)
    present = [marker for marker in FORBIDDEN_OUTCOME_MARKERS if marker in serialized]
    if present:
        raise MiniwobChecklistFreezeError(
            f"outcome/agent leakage markers in pre-run checklist {case_id}: {present}"
        )
    return sum(1 for _ in _iter_supports(checklist))


def _validate_prelock_bundle(
    *, manifest: Mapping[str, Any], bundle: Mapping[str, Any], bundle_path: Path, manifest_path: Path
) -> None:
    if manifest.get("source_bundle_hash") != sha256_file(bundle_path):
        raise MiniwobChecklistFreezeError("pre-lock manifest source_bundle_hash is stale")
    if bundle.get("schema_version") != "contract_source_bundle.v2":
        raise MiniwobChecklistFreezeError("unexpected source bundle schema_version")
    declared = Path(str(bundle.get("manifest_path") or ""))
    declared = (declared if declared.is_absolute() else PACKAGE_ROOT / declared).resolve()
    if declared != manifest_path:
        raise MiniwobChecklistFreezeError("source bundle does not bind the supplied manifest")
    definition = dict(manifest)
    definition.pop("source_bundle_hash", None)
    if bundle.get("manifest_definition_sha256") != sha256_object(definition):
        raise MiniwobChecklistFreezeError("pre-lock source bundle manifest definition hash is stale")


def _validated_locked_at(value: str | None) -> str:
    candidate = value or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    try:
        parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MiniwobChecklistFreezeError(f"locked-at is not an ISO timestamp: {candidate}") from exc
    if parsed.tzinfo is None:
        raise MiniwobChecklistFreezeError("locked-at must include a timezone")
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def build_and_publish(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = _require_file(args.manifest, "manifest")
    bundle_path = _require_file(args.source_bundle, "source bundle")
    packet_root = _require_dir(args.case_packet_root, "case packet root")
    raw_root = _require_dir(args.raw_draft_root, "raw draft root")
    reviewed_root = _require_dir(args.reviewed_root, "reviewed root")
    results_root = _require_dir(args.results_root, "results root")
    generation_manifest = _require_file(args.generation_manifest, "generation manifest")
    draft_prompt = _require_file(args.draft_prompt, "draft prompt")
    score_prompt = _require_file(args.score_prompt, "score prompt")
    checklist_schema_path = _require_file(args.checklist_schema, "checklist schema")
    score_schema = _require_file(args.score_schema, "score schema")
    manifest_schema_path = _require_file(args.manifest_schema, "manifest schema")
    output_root = args.output_root.resolve()
    if output_root.exists():
        raise MiniwobChecklistFreezeError(f"output root already exists: {output_root}")
    scoring_files = [
        path
        for path in results_root.rglob("*")
        if path.is_file()
        and (not path.relative_to(results_root).parts or path.relative_to(results_root).parts[0] != "drafts")
    ]
    if scoring_files:
        raise MiniwobChecklistFreezeError(
            "cannot freeze after scoring artifacts exist: "
            + ", ".join(_display(path) for path in sorted(scoring_files)[:10])
        )

    manifest = _load_mapping(manifest_path, "manifest")
    bundle = _load_mapping(bundle_path, "source bundle")
    _validate_prelock_bundle(
        manifest=manifest,
        bundle=bundle,
        bundle_path=bundle_path,
        manifest_path=manifest_path,
    )
    domains = manifest.get("domains")
    if not isinstance(domains, list) or len(domains) != 1 or domains[0].get("domain") != EXPECTED_DOMAIN:
        raise MiniwobChecklistFreezeError("manifest must contain exactly one MiniWoB domain")
    manifest_cases = domains[0].get("case_units")
    sources = bundle.get("sources")
    if not isinstance(manifest_cases, list) or not isinstance(sources, list):
        raise MiniwobChecklistFreezeError("manifest cases and source bundle sources must be lists")
    if len(manifest_cases) != EXPECTED_COUNT or len(sources) != EXPECTED_COUNT:
        raise MiniwobChecklistFreezeError("freeze requires exactly 22 manifest cases and sources")
    case_ids = [str(case.get("case_unit_id") or "") for case in manifest_cases]
    source_ids = [str(source.get("case_unit_id") or "") for source in sources]
    if case_ids != source_ids or len(set(case_ids)) != EXPECTED_COUNT:
        raise MiniwobChecklistFreezeError("manifest/source identity or order mismatch")
    expected_dirs = set(case_ids)
    if set(EXPECTED_FINAL_CHECKLIST_SHA256) != expected_dirs:
        raise MiniwobChecklistFreezeError("final checklist hash allowlist does not match the 22-case manifest")
    if not UNCHANGED_CASES < expected_dirs:
        raise MiniwobChecklistFreezeError("unchanged-case allowlist is not a strict subset of the manifest")
    for root, label in ((packet_root, "packet"), (raw_root, "raw draft"), (reviewed_root, "reviewed")):
        observed = {path.name for path in root.iterdir() if path.is_dir() and not path.is_symlink()}
        if observed != expected_dirs:
            raise MiniwobChecklistFreezeError(
                f"{label} case directory set mismatch: missing={sorted(expected_dirs-observed)}, "
                f"extra={sorted(observed-expected_dirs)}"
            )

    checklist_schema = _load_mapping(checklist_schema_path, "checklist schema")
    schema_validator = Draft202012Validator(checklist_schema)
    locked_at = _validated_locked_at(args.locked_at)
    output_root.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.stage-", dir=output_root.parent))
    original_manifest_bytes = manifest_path.read_bytes()
    original_bundle_bytes = bundle_path.read_bytes()
    published = False
    try:
        accepted_cases: list[dict[str, Any]] = []
        corrections: list[dict[str, Any]] = []
        file_lock_entries: list[dict[str, str]] = []
        contract_locks: list[dict[str, Any]] = []
        model_configs: set[tuple[str, str, str, str]] = set()
        support_pointer_count = 0
        stronger_case_count = 0
        stronger_condition_count = 0

        for case_id, source in zip(case_ids, sources, strict=True):
            packet_path = _require_file(packet_root / case_id / "case_packet.md", f"packet {case_id}")
            raw_yaml_path = _require_file(raw_root / case_id / "checklist.yaml", f"raw checklist {case_id}")
            raw_json_path = _require_file(raw_root / case_id / "checklist.json", f"raw checklist JSON {case_id}")
            reviewed_yaml_path = _require_file(
                reviewed_root / case_id / "checklist.yaml", f"reviewed checklist {case_id}"
            )
            reviewed_json_path = _require_file(
                reviewed_root / case_id / "checklist.json", f"reviewed checklist JSON {case_id}"
            )
            llm_call_path = _require_file(reviewed_root / case_id / "llm_call.json", f"LLM call {case_id}")
            raw_yaml = load_checklist(raw_yaml_path)
            raw_json = load_checklist(raw_json_path)
            reviewed_yaml = load_checklist(reviewed_yaml_path)
            reviewed_json = load_checklist(reviewed_json_path)
            if raw_yaml != raw_json:
                raise MiniwobChecklistFreezeError(f"raw YAML/JSON mismatch for {case_id}")
            if reviewed_yaml != reviewed_json:
                raise MiniwobChecklistFreezeError(f"reviewed YAML/JSON mismatch for {case_id}")
            differences = _diff_paths(raw_yaml, reviewed_yaml)
            final_contract_sha256 = sha256_object(reviewed_yaml)
            if final_contract_sha256 != EXPECTED_FINAL_CHECKLIST_SHA256[case_id]:
                raise MiniwobChecklistFreezeError(
                    f"reviewed checklist hash differs from the audited final candidate for {case_id}"
                )
            if case_id in UNCHANGED_CASES:
                if differences:
                    raise MiniwobChecklistFreezeError(
                        f"unexpected reviewed drift for unchanged case {case_id}: {sorted(differences)}"
                    )
            else:
                if not differences:
                    raise MiniwobChecklistFreezeError(
                        f"required audited correction is missing for {case_id}"
                    )
                corrections.append(
                    {
                        "case_unit_id": case_id,
                        "changed_paths": sorted(differences),
                        "reason": CORRECTION_REASONS.get(
                            case_id,
                            "Complete native S/F/U coverage and decisive-artifact fallback under the "
                            "released evaluator semantics.",
                        ),
                        "raw_contract_sha256": sha256_object(raw_yaml),
                        "final_contract_sha256": final_contract_sha256,
                    }
                )

            support_pointer_count += _validate_checklist(
                checklist=reviewed_yaml,
                packet_path=packet_path,
                schema_validator=schema_validator,
                case_id=case_id,
            )
            stronger_count = len(reviewed_yaml["stronger"]["additional_conditions"])
            stronger_case_count += int(stronger_count > 0)
            stronger_condition_count += stronger_count

            llm_call = _load_mapping(llm_call_path, f"LLM call {case_id}")
            response_metadata = llm_call.get("response_metadata")
            if not isinstance(response_metadata, dict):
                raise MiniwobChecklistFreezeError(f"LLM response metadata missing for {case_id}")
            response_id = str(response_metadata.get("response_id") or "")
            config = (
                str(llm_call.get("provider") or ""),
                str(llm_call.get("model") or ""),
                str(response_metadata.get("reasoning_effort") or ""),
                str(response_metadata.get("auth_mode") or ""),
            )
            if not response_id or not all(config):
                raise MiniwobChecklistFreezeError(f"incomplete draft provenance for {case_id}")
            model_configs.add(config)

            frozen_case_dir = stage / "checklists" / case_id
            frozen_case_dir.mkdir(parents=True)
            shutil.copyfile(reviewed_yaml_path, frozen_case_dir / "checklist.yaml")
            canonical_bytes = canonical_json_bytes(reviewed_yaml)
            (frozen_case_dir / "checklist.canonical.json").write_bytes(canonical_bytes)
            contract_hash = _sha256_bytes(canonical_bytes)
            contract_id = str(source.get("contract_id") or "")
            if not contract_id:
                raise MiniwobChecklistFreezeError(f"source contract_id missing for {case_id}")
            review_record_id = f"miniwob22-system-design-review-v1::{case_id}"
            draft_id = f"miniwob22-codex-gpt54-medium-20260719::{case_id}"
            canonical_path = output_root / "checklists" / case_id / "checklist.canonical.json"
            contract_locks.append(
                {
                    "contract_id": contract_id,
                    "contract_version": "1.0.0",
                    "contract_hash": contract_hash,
                    "lock_status": "locked",
                    "locked_at": locked_at,
                    "review_record_id": review_record_id,
                    "contract_drafting_llm_call_id": response_id,
                    "contract_draft_id": draft_id,
                    "canonicalization_method": "json_canonical_sha256",
                    "canonical_hash_source": _display(canonical_path),
                    "main_result_eligible": True,
                }
            )
            try:
                file_lock_entry = case_locks.build_lock_entry(
                    case_packet_path=packet_path,
                    checklist_path=frozen_case_dir / "checklist.yaml",
                    draft_prompt_path=draft_prompt,
                    score_prompt_path=score_prompt,
                    checklist_schema_path=checklist_schema_path,
                    score_schema_path=score_schema,
                )
            except case_locks.CaseLockError as exc:
                raise MiniwobChecklistFreezeError(str(exc)) from exc
            file_lock_entries.append(file_lock_entry)
            accepted_cases.append(
                {
                    "case_unit_id": case_id,
                    "contract_id": contract_id,
                    "contract_sha256": contract_hash,
                    "checklist_yaml_sha256": sha256_file(frozen_case_dir / "checklist.yaml"),
                    "case_packet_sha256": sha256_file(packet_path),
                    "draft_llm_response_id": response_id,
                    "review_record_id": review_record_id,
                    "correction_applied": case_id not in UNCHANGED_CASES,
                    "decision": "accept",
                    "unresolved_findings": [],
                }
            )

        if model_configs != {("codex_cli", "gpt-5.4", "medium", "codex_login")}:
            raise MiniwobChecklistFreezeError(f"unexpected or non-uniform draft model config: {model_configs}")
        if len(corrections) != EXPECTED_COUNT - len(UNCHANGED_CASES):
            raise MiniwobChecklistFreezeError("freeze requires the complete audited correction set")
        if (stronger_case_count, stronger_condition_count) != (7, 7):
            raise MiniwobChecklistFreezeError(
                "stronger freeze basis drifted; expected seven conditions across seven cases"
            )

        review_receipt = {
            "schema_version": "miniwob_case_checklist_system_design_review/v1",
            "status": "accepted",
            "reviewed_at": locked_at,
            "historical_threads_used": False,
            "review_basis": {
                "phase": "pre_run_before_evidence_scoring",
                "native_priority": "released_evaluator_or_oracle_formal_semantics",
                "stronger_rule": "official_case_specific_support_beyond_native_only",
                "unsupported_reviewer_requirements_allowed": False,
                "released_label_preserved_separately": True,
                "native_labels": {"S": "Evidence Pass", "F": "Evidence Fail", "U": "Unknown"},
                "paper_counts": {"S": "P", "F": "F", "U": "U"},
                "stronger_reported_separately": True,
                "stronger_failure_implies_conflict": False,
                "benchmark_conflict_requires_separate_record_level_audit": True,
            },
            "draft_provenance": {
                "provider": "codex_cli",
                "model": "gpt-5.4",
                "reasoning_effort": "medium",
                "auth_mode": "codex_login",
                "generation_manifest_path": _display(generation_manifest),
                "generation_manifest_sha256": sha256_file(generation_manifest),
            },
            "counts": {
                "reviewed": len(accepted_cases),
                "accepted": len(accepted_cases),
                "rejected": 0,
                "unresolved": 0,
                "corrected_cases": len(corrections),
                "support_pointers_resolved": support_pointer_count,
                "stronger_cases": stronger_case_count,
                "stronger_conditions": stronger_condition_count,
            },
            "corrections": corrections,
            "cases": accepted_cases,
        }
        provenance = stage / "provenance"
        provenance.mkdir()
        review_path = provenance / "review_receipt.json"
        review_path.write_bytes(_json_bytes(review_receipt))
        file_lock_path = provenance / "case_checklist_file_locks.jsonl"
        file_lock_bytes = b"".join(
            (json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            for entry in file_lock_entries
        )
        file_lock_path.write_bytes(file_lock_bytes)

        locked_manifest = deepcopy(manifest)
        locked_manifest["manifest_version"] = args.manifest_version
        locked_manifest["status"] = "frozen"
        locked_manifest["experiment_lock_path"] = _display(output_root / "provenance/freeze_receipt.json")
        locked_manifest["contract_locks"] = contract_locks
        locked_manifest["contract_locks_hash"] = sha256_object(contract_locks)
        locked_domain = locked_manifest["domains"][0]
        locked_domain["contract_lock_status"] = "locked"
        for case, lock in zip(locked_domain["case_units"], contract_locks, strict=True):
            case["contract_lock_status"] = "locked"
            case["contract_lock_time"] = locked_at
            case["evidence_contract_id"] = lock["contract_id"]
            case["evidence_contract_version"] = lock["contract_version"]
            case["evidence_contract_hash"] = lock["contract_hash"]
            case["taxonomy_version"] = EXPECTED_TAXONOMY

        updated_bundle = deepcopy(bundle)
        manifest_definition = dict(locked_manifest)
        manifest_definition.pop("source_bundle_hash", None)
        updated_bundle["manifest_definition_sha256"] = sha256_object(manifest_definition)
        bundle_bytes = _json_bytes(updated_bundle)
        locked_manifest["source_bundle_hash"] = _sha256_bytes(bundle_bytes)
        manifest_bytes = _json_bytes(locked_manifest)

        manifest_schema = _load_mapping(manifest_schema_path, "manifest schema")
        schema_errors = sorted(
            Draft202012Validator(manifest_schema).iter_errors(locked_manifest),
            key=lambda error: tuple(str(item) for item in error.absolute_path),
        )
        if schema_errors:
            rendered = "; ".join(
                f"{'.'.join(str(item) for item in error.absolute_path) or '<root>'}: {error.message}"
                for error in schema_errors
            )
            raise MiniwobChecklistFreezeError(f"locked manifest schema failed: {rendered}")

        freeze_receipt = {
            "schema_version": "miniwob_case_checklist_freeze/v1",
            "status": "frozen",
            "locked_at": locked_at,
            "domain": EXPECTED_DOMAIN,
            "case_count": len(accepted_cases),
            "pre_run_assertion": {
                "scoring_started": False,
                "checklists_outcome_isolated": True,
                "historical_threads_used": False,
            },
            "inputs": {
                "raw_draft_root": _display(raw_root),
                "raw_draft_tree_sha256": sha256_path(raw_root),
                "reviewed_root": _display(reviewed_root),
                "reviewed_tree_sha256": sha256_path(reviewed_root),
                "generation_manifest_path": _display(generation_manifest),
                "generation_manifest_sha256": sha256_file(generation_manifest),
                "case_packet_root": _display(packet_root),
                "case_packet_tree_sha256": sha256_path(packet_root),
                "results_root": _display(results_root),
                "pre_freeze_scoring_file_count": len(scoring_files),
                "draft_prompt_path": _display(draft_prompt),
                "draft_prompt_sha256": sha256_file(draft_prompt),
                "score_prompt_path": _display(score_prompt),
                "score_prompt_sha256": sha256_file(score_prompt),
                "checklist_schema_path": _display(checklist_schema_path),
                "checklist_schema_sha256": sha256_file(checklist_schema_path),
                "score_schema_path": _display(score_schema),
                "score_schema_sha256": sha256_file(score_schema),
                "prelock_manifest_sha256": _sha256_bytes(original_manifest_bytes),
                "prelock_source_bundle_sha256": _sha256_bytes(original_bundle_bytes),
            },
            "outputs": {
                "freeze_root": _display(output_root),
                "checklists_tree_sha256": sha256_path(stage / "checklists"),
                "review_receipt_path": _display(output_root / "provenance/review_receipt.json"),
                "review_receipt_sha256": sha256_file(review_path),
                "file_lock_path": _display(output_root / "provenance/case_checklist_file_locks.jsonl"),
                "file_lock_sha256": _sha256_bytes(file_lock_bytes),
                "contract_locks_sha256": sha256_object(contract_locks),
                "manifest_path": _display(manifest_path),
                "manifest_sha256": _sha256_bytes(manifest_bytes),
                "source_bundle_path": _display(bundle_path),
                "source_bundle_sha256": _sha256_bytes(bundle_bytes),
            },
            "counts": review_receipt["counts"],
            "accepted_cases_sha256": sha256_object(accepted_cases),
            "corrections": corrections,
        }
        freeze_path = provenance / "freeze_receipt.json"
        freeze_path.write_bytes(_json_bytes(freeze_receipt))

        os.replace(stage, output_root)
        published = True
        try:
            _atomic_write(bundle_path, bundle_bytes)
            _atomic_write(manifest_path, manifest_bytes)
        except Exception:
            _atomic_write(bundle_path, original_bundle_bytes)
            _atomic_write(manifest_path, original_manifest_bytes)
            shutil.rmtree(output_root, ignore_errors=True)
            published = False
            raise
        return freeze_receipt
    finally:
        if not published:
            shutil.rmtree(stage, ignore_errors=True)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        receipt = build_and_publish(args)
    except (MiniwobChecklistFreezeError, OSError, ValueError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    else:
        print(
            f"frozen {receipt['case_count']} MiniWoB checklists: "
            f"{receipt['outputs']['freeze_root']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
