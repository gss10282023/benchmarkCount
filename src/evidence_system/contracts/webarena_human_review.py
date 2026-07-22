"""Deterministic reviewer queue for WebArena-Verified native claims.

This package makes the remaining human work concrete without asserting that it
has happened.  Every decision field is null and every item is explicitly marked
unsigned.  The builder writes only its review-package output directory; it does
not create formal locks or scheduler jobs.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import jsonschema

from evidence_system.contracts import webarena_native as native


QUEUE_ITEM_SCHEMA_VERSION = (
    "webarena_verified_native_claim_human_review_queue_item/v1"
)
PACKAGE_INDEX_SCHEMA_VERSION = (
    "webarena_verified_native_claim_human_review_package_index/v1"
)
ACCEPTANCE_SCHEMA_VERSION = (
    "webarena_verified_native_claim_human_review_acceptance/v1"
)
DEFAULT_NATIVE_ROOT = native.DEFAULT_OUTPUT_ROOT
DEFAULT_OUTPUT_ROOT = native.DEFAULT_OUTPUT_ROOT / "human_review"
QUEUE_ITEM_SCHEMA = Path(
    "schemas/webarena_verified_native_claim_human_review_queue_item.schema.json"
)
QUEUE_FILENAME = "review_queue.jsonl"
TEMPLATE_FILENAME = "human_signoff.pending.template.jsonl"
README_FILENAME = "README.md"
INDEX_FILENAME = "index.json"
ACCEPTANCE_FILENAME = "acceptance.json"

_SEMANTIC_SOURCES = (
    (
        "official_evaluator_orchestration",
        "official/src/webarena_verified/api/internal/evaluator.py",
        native.EVALUATOR_POINTER,
    ),
    (
        "official_all_evaluator_conjunction",
        "official/src/webarena_verified/types/eval.py",
        native.TASK_RESULT_POINTER,
    ),
    (
        "official_agent_response_semantics",
        (
            "official/src/webarena_verified/core/evaluation/evaluators/"
            "agent_response_evaluator.py"
        ),
        native.AGENT_RESPONSE_POINTER,
    ),
    (
        "official_value_comparison",
        "official/src/webarena_verified/core/evaluation/value_comparator.py",
        (
            "official/src/webarena_verified/core/evaluation/"
            "value_comparator.py::ValueComparator.compare"
        ),
    ),
    (
        "official_value_normalization",
        "official/src/webarena_verified/core/evaluation/value_normalizer.py",
        (
            "official/src/webarena_verified/core/evaluation/"
            "value_normalizer.py::ValueNormalizer.normalize"
        ),
    ),
)
_NETWORK_SOURCE = (
    "official_network_event_semantics",
    (
        "official/src/webarena_verified/core/evaluation/evaluators/"
        "network_event_evaluator.py"
    ),
    native.NETWORK_EVENT_POINTER,
)
_DECISION_FIELDS = {
    "review_id": None,
    "reviewer_id": None,
    "review_started_at": None,
    "review_finished_at": None,
    "locked_at": None,
    "first_scoring_started_at": None,
    "source_check_complete": None,
    "evaluator_semantics_complete": None,
    "artifact_requirements_accepted": None,
    "decision": None,
    "notes": None,
}
_SECRET_MARKERS = (
    b"sk-or-v1-",
    b"OPENROUTER_API_KEY=",
    b"-----BEGIN OPENSSH PRIVATE KEY-----",
    b"-----BEGIN RSA PRIVATE KEY-----",
    b"-----BEGIN PRIVATE KEY-----",
)


class WebArenaHumanReviewError(RuntimeError):
    """Raised when the review queue cannot be trusted or remains incomplete."""


def _repo_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else native.PACKAGE_ROOT / path


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(native.PACKAGE_ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise WebArenaHumanReviewError(
            f"path escapes repository root: {path}"
        ) from exc


def _display_path(path: Path) -> str:
    """Use repository-relative paths in canonical artifacts, absolute paths in tests."""

    try:
        return _repo_relative(path)
    except WebArenaHumanReviewError:
        return path.resolve().as_posix()


def _resolve_repo_file(value: str, *, expected_hash: str | None = None) -> Path:
    path = _repo_path(value).resolve()
    try:
        path.relative_to(native.PACKAGE_ROOT.resolve())
    except ValueError as exc:
        raise WebArenaHumanReviewError(
            f"review source escapes repository root: {value}"
        ) from exc
    if not path.is_file() or path.is_symlink():
        raise WebArenaHumanReviewError(f"review source missing or symlinked: {value}")
    if expected_hash is not None and native.file_sha256(path) != expected_hash:
        raise WebArenaHumanReviewError(f"review source hash mismatch: {value}")
    return path


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WebArenaHumanReviewError(f"cannot load JSON {path}: {exc}") from exc
    if not isinstance(value, Mapping):
        raise WebArenaHumanReviewError(f"JSON document must be an object: {path}")
    return dict(value)


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _jsonl_bytes(values: Sequence[Mapping[str, Any]]) -> bytes:
    return "".join(
        json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n"
        for value in values
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write_sidecar(path: Path) -> None:
    path.with_suffix(path.suffix + ".sha256").write_text(
        f"{native.file_sha256(path)}  {path.name}\n",
        encoding="utf-8",
    )


def _descriptor(path: Path, *, display_path: Path | None = None) -> dict[str, str]:
    return {
        "path": _display_path(display_path or path),
        "sha256": native.file_sha256(path),
    }


def _semantic_pointer(
    *,
    raw_root: Path,
    role: str,
    relative_path: str,
    pointer: str,
) -> dict[str, Any]:
    path = raw_root / relative_path
    expected = native.OFFICIAL_SEMANTIC_SOURCE_HASHES[relative_path]
    if not path.is_file() or path.is_symlink() or native.file_sha256(path) != expected:
        raise WebArenaHumanReviewError(
            f"official semantic source mismatch: {_repo_relative(path)}"
        )
    return {
        "role": role,
        "path": _repo_relative(path),
        "pointer": pointer,
        "file_sha256": expected,
        "object_sha256": None,
    }


def _template_line(
    *, entry: Mapping[str, Any], input_lock_sha256: str
) -> dict[str, Any]:
    return {
        "schema_version": native.HUMAN_SIGNOFF_SCHEMA_VERSION,
        "domain": native.DOMAIN,
        "case_unit_id": entry["case_unit_id"],
        "task_id": entry["task_id"],
        "task_revision": entry["task_revision"],
        "input_lock_sha256": input_lock_sha256,
        "native_ir_sha256": entry["native_ir_sha256"],
        "draft_contract_sha256": entry["draft_contract_sha256"],
        "draft_checklist_sha256": entry["draft_checklist_sha256"],
        "machine_review_sha256": entry["machine_review_sha256"],
        **_DECISION_FIELDS,
    }


def _queue_item(
    *,
    entry: Mapping[str, Any],
    input_lock_sha256: str,
    line_number: int,
    signoff_schema_path: Path,
) -> dict[str, Any]:
    task_id = str(entry["case_unit_id"])
    ir_path = _resolve_repo_file(
        str(entry["native_ir_path"]),
        expected_hash=str(entry["native_ir_sha256"]),
    )
    ir = _load_json(ir_path)
    identity = ir.get("identity")
    task = ir.get("task")
    source = ir.get("source_binding")
    semantics = ir.get("native_semantics")
    if not all(isinstance(value, Mapping) for value in (identity, task, source, semantics)):
        raise WebArenaHumanReviewError(f"case {task_id} IR review sections are missing")
    if str(identity.get("case_unit_id")) != task_id:
        raise WebArenaHumanReviewError(f"case {task_id} IR identity mismatch")

    artifact_fields = (
        ("source_rich_case_packet", "case_packet_path", "case_packet_sha256"),
        (
            "raw_source_manifest",
            "raw_case_manifest_path",
            "raw_case_manifest_sha256",
        ),
        ("native_claim_ir", "native_ir_path", "native_ir_sha256"),
        ("draft_evidence_contract", "draft_contract_path", "draft_contract_sha256"),
        ("draft_case_checklist", "draft_checklist_path", "draft_checklist_sha256"),
        ("machine_validation_record", "machine_review_path", "machine_review_sha256"),
    )
    review_artifacts = []
    for role, path_field, hash_field in artifact_fields:
        owner = source if path_field in source else entry
        path_value = str(owner[path_field])
        hash_value = str(owner[hash_field])
        _resolve_repo_file(path_value, expected_hash=hash_value)
        review_artifacts.append(
            {"role": role, "path": path_value, "sha256": hash_value}
        )

    derived_task_path = _resolve_repo_file(
        str(source["derived_task_path"]),
        expected_hash=str(source["derived_task_file_sha256"]),
    )
    raw_manifest_path = _resolve_repo_file(
        str(source["raw_case_manifest_path"]),
        expected_hash=str(source["raw_case_manifest_sha256"]),
    )
    raw_root = raw_manifest_path.parent / "raw_case"
    case_packet_path = _resolve_repo_file(
        str(source["case_packet_path"]),
        expected_hash=str(source["case_packet_sha256"]),
    )
    pointers: list[dict[str, Any]] = [
        {
            "role": "reviewer_source_inventory",
            "path": _repo_relative(case_packet_path),
            "pointer": "case_packet.md::Source Inventory",
            "file_sha256": native.file_sha256(case_packet_path),
            "object_sha256": None,
        },
        {
            "role": "official_task",
            "path": _repo_relative(derived_task_path),
            "pointer": "derived/task.json::task",
            "file_sha256": native.file_sha256(derived_task_path),
            "object_sha256": str(source["packet_source_task_sha256"]),
        },
    ]
    evaluators = semantics.get("evaluators")
    if not isinstance(evaluators, list) or not evaluators:
        raise WebArenaHumanReviewError(f"case {task_id} has no evaluator semantics")
    for position, evaluator in enumerate(evaluators):
        if not isinstance(evaluator, Mapping):
            raise WebArenaHumanReviewError(
                f"case {task_id} evaluator {position} is not an object"
            )
        pointers.append(
            {
                "role": f"official_evaluator_config_{position}",
                "path": _repo_relative(derived_task_path),
                "pointer": f"derived/task.json::eval/{position}",
                "file_sha256": native.file_sha256(derived_task_path),
                "object_sha256": str(evaluator["config_sha256"]),
            }
        )
    for role, relative_path, pointer in _SEMANTIC_SOURCES:
        pointers.append(
            _semantic_pointer(
                raw_root=raw_root,
                role=role,
                relative_path=relative_path,
                pointer=pointer,
            )
        )
    names = [
        str(item.get("name")) for item in evaluators if isinstance(item, Mapping)
    ]
    if "NetworkEventEvaluator" in names:
        role, relative_path, pointer = _NETWORK_SOURCE
        pointers.append(
            _semantic_pointer(
                raw_root=raw_root,
                role=role,
                relative_path=relative_path,
                pointer=pointer,
            )
        )

    required_exact = {
        "domain": native.DOMAIN,
        "case_unit_id": task_id,
        "task_id": str(entry["task_id"]),
        "task_revision": entry["task_revision"],
        "input_lock_sha256": input_lock_sha256,
        "native_ir_sha256": entry["native_ir_sha256"],
        "draft_contract_sha256": entry["draft_contract_sha256"],
        "draft_checklist_sha256": entry["draft_checklist_sha256"],
        "machine_review_sha256": entry["machine_review_sha256"],
    }
    return {
        "schema_version": QUEUE_ITEM_SCHEMA_VERSION,
        "visibility": "human_reviewer_only_not_model_visible",
        "status": "pending_human_review",
        "human_signed": False,
        "domain": native.DOMAIN,
        "case_unit_id": task_id,
        "task_id": str(entry["task_id"]),
        "task_revision": entry["task_revision"],
        "task": {
            "intent": task["intent"],
            "task_type": identity["task_type"],
            "sites": list(task["sites"]),
            "start_urls": list(task["start_urls"]),
        },
        "hash_binding": {
            "input_lock_sha256": input_lock_sha256,
            "native_ir_sha256": entry["native_ir_sha256"],
            "draft_contract_sha256": entry["draft_contract_sha256"],
            "draft_checklist_sha256": entry["draft_checklist_sha256"],
            "machine_review_sha256": entry["machine_review_sha256"],
            "evaluator_config_sha256": entry["evaluator_config_sha256"],
        },
        "review_artifacts": review_artifacts,
        "source_pointers": pointers,
        "review_requirements": [
            {
                "decision_field": "source_check_complete",
                "instruction": (
                    "Open every listed review artifact and source pointer; verify "
                    "task identity, revision, hashes, and authoritative source support."
                ),
            },
            {
                "decision_field": "evaluator_semantics_complete",
                "instruction": (
                    "Verify evaluator configs in exact order, implementation semantics, "
                    "and TaskEvalResult.create all-evaluator conjunction."
                ),
            },
            {
                "decision_field": "artifact_requirements_accepted",
                "instruction": (
                    "Verify contract and checklist require sufficient task-bound "
                    "AgentResponse, HAR/network, evaluator-input, and evaluator-output evidence."
                ),
            },
        ],
        "decision_fields": dict(_DECISION_FIELDS),
        "signoff_output": {
            "target_schema_version": native.HUMAN_SIGNOFF_SCHEMA_VERSION,
            "schema_path": _repo_relative(signoff_schema_path),
            "schema_sha256": native.file_sha256(signoff_schema_path),
            "template_line_number": line_number,
            "required_exact_fields": required_exact,
        },
    }


def compile_review_materials(
    native_root: str | Path = DEFAULT_NATIVE_ROOT,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    root = _repo_path(native_root)
    report = native.validate_native_claim_package(root, current_source_check=True)
    if report.get("status") != "ok":
        raise WebArenaHumanReviewError(
            "native-claim package is not current: "
            + "; ".join(report.get("issues", [])[:8])
        )
    index_path = root / "index.json"
    acceptance_path = root / "acceptance.json"
    input_lock_path = root / "input_lock.json"
    machine_lock_path = root / "locks" / "machine_locks.jsonl"
    index = _load_json(index_path)
    acceptance = _load_json(acceptance_path)
    entries = index.get("cases")
    if not isinstance(entries, list) or len(entries) != native.EXPECTED_CASES:
        raise WebArenaHumanReviewError("native index must contain exactly 812 cases")
    if [str(item.get("case_unit_id")) for item in entries] != list(
        native.EXPECTED_TASK_IDS
    ):
        raise WebArenaHumanReviewError("native index cases must be ordered exactly 0..811")
    if any(item.get("human_signoff_status") != "pending" for item in entries):
        raise WebArenaHumanReviewError(
            "review queue may only be built from the unsigned machine package"
        )
    counts = acceptance.get("counts")
    if not isinstance(counts, Mapping) or any(
        counts.get(field) != 0
        for field in ("human_signed", "locked_contracts", "locked_checklists")
    ):
        raise WebArenaHumanReviewError(
            "upstream formal/human lock counts must remain zero"
        )
    signoff_schema_path = _resolve_repo_file(str(native.HUMAN_SIGNOFF_SCHEMA))
    input_lock_sha256 = native.file_sha256(input_lock_path)
    queue = [
        _queue_item(
            entry=entry,
            input_lock_sha256=input_lock_sha256,
            line_number=position,
            signoff_schema_path=signoff_schema_path,
        )
        for position, entry in enumerate(entries, start=1)
    ]
    templates = [
        _template_line(entry=entry, input_lock_sha256=input_lock_sha256)
        for entry in entries
    ]
    upstream = {
        "native_claim_index": _descriptor(index_path),
        "native_claim_acceptance": _descriptor(acceptance_path),
        "native_claim_input_lock": _descriptor(input_lock_path),
        "native_claim_machine_locks": _descriptor(machine_lock_path),
        "human_signoff_schema": _descriptor(signoff_schema_path),
        "queue_item_schema": _descriptor(_resolve_repo_file(str(QUEUE_ITEM_SCHEMA))),
    }
    return queue, templates, upstream


def _readme_bytes() -> bytes:
    text = """# WebArena-Verified 812-case human review queue

This directory is reviewer-only and must never be sent to the benchmark agents.
It contains 812 hash-bound review items, one per official task. Every decision
field is intentionally null and `human_signed` is false. Nothing in this package
is a human approval or a formal lock.

For each line in `review_queue.jsonl`, open every `review_artifacts` file and
follow every `source_pointers` entry. Complete all three review requirements
against the cited official task/evaluator sources. Record the real reviewer,
actual timezone-aware timestamps, notes, and decision in a separate copy of
`human_signoff.pending.template.jsonl`; never overwrite the generated template.
If any requirement cannot be affirmed, do not turn that line into a signoff:
record the finding separately, repair the affected upstream draft, and rebuild
the hash-bound queue before review resumes.

The completed JSONL must contain exactly 812 records and conform to
`schemas/webarena_verified_native_claim_human_signoff.schema.json`. Validate it
without creating locks:

```
PYTHONPATH=.:src .venv/bin/python -m evidence_system.cli.webarena_native_human_review \\
  --validate-only --completed-signoffs PATH/TO/human_signoffs.completed.jsonl --json
```

Only after that command reports `ready_for_formal_build` may the completed file
be supplied explicitly to the native-claim builder. The queue itself never
changes machine locks, formal locks, or scheduler outputs.
"""
    return text.encode("utf-8")


def _index_payload(
    *,
    output_root: Path,
    queue_path: Path,
    template_path: Path,
    readme_path: Path,
    queue: Sequence[Mapping[str, Any]],
    upstream: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": PACKAGE_INDEX_SCHEMA_VERSION,
        "status": "ready_for_real_human_review",
        "visibility": "human_reviewer_only_not_model_visible",
        "domain": native.DOMAIN,
        "benchmark_version": native.BENCHMARK_VERSION,
        "expected_count": native.EXPECTED_CASES,
        "package_root": _display_path(output_root),
        "mutation_scope": [_display_path(output_root)],
        "excluded_mutations": [
            "native machine locks",
            "native formal locks",
            "scheduler plans and jobs",
        ],
        "upstream": dict(upstream),
        "review_queue": _descriptor(
            queue_path, display_path=output_root / QUEUE_FILENAME
        ),
        "pending_signoff_template": _descriptor(
            template_path, display_path=output_root / TEMPLATE_FILENAME
        ),
        "instructions": _descriptor(
            readme_path, display_path=output_root / README_FILENAME
        ),
        "queue_content_sha256": native.object_sha256(list(queue)),
        "counts": {
            "queue_items": native.EXPECTED_CASES,
            "pending_human_review": native.EXPECTED_CASES,
            "human_signed": 0,
            "approved": 0,
            "formal_locks": 0,
        },
    }


def _acceptance_payload(
    *,
    output_root: Path,
    index_path: Path,
    queue_path: Path,
    template_path: Path,
) -> dict[str, Any]:
    return {
        "schema_version": ACCEPTANCE_SCHEMA_VERSION,
        "status": "ready_for_real_human_review",
        "formal_launch_eligible": False,
        "authorizes_formal_lock": False,
        "domain": native.DOMAIN,
        "expected_count": native.EXPECTED_CASES,
        "index": _descriptor(
            index_path, display_path=output_root / INDEX_FILENAME
        ),
        "review_queue": _descriptor(
            queue_path, display_path=output_root / QUEUE_FILENAME
        ),
        "pending_signoff_template": _descriptor(
            template_path, display_path=output_root / TEMPLATE_FILENAME
        ),
        "counts": {
            "queue_items": native.EXPECTED_CASES,
            "pending_human_review": native.EXPECTED_CASES,
            "human_signed": 0,
            "approved": 0,
            "formal_locks": 0,
        },
        "gates": {
            "queue_denominator_exact": True,
            "source_pointers_current": True,
            "contract_and_checklist_hashes_current": True,
            "decision_fields_blank": True,
            "secret_scan_passed": True,
            "upstream_machine_package_current": True,
            "upstream_formal_locks_absent": True,
            "human_signoff_complete": False,
        },
        "blockers": ["812 real human source-check decisions remain required"],
    }


def _tree_hash(root: Path) -> str:
    entries = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": native.file_sha256(path),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    ]
    return native.object_sha256(entries)


def _write_package(
    *,
    target: Path,
    declared_output_root: Path,
    queue: Sequence[Mapping[str, Any]],
    templates: Sequence[Mapping[str, Any]],
    upstream: Mapping[str, Any],
) -> None:
    target.mkdir(parents=True, exist_ok=False)
    queue_path = target / QUEUE_FILENAME
    template_path = target / TEMPLATE_FILENAME
    readme_path = target / README_FILENAME
    index_path = target / INDEX_FILENAME
    acceptance_path = target / ACCEPTANCE_FILENAME
    queue_path.write_bytes(_jsonl_bytes(queue))
    template_path.write_bytes(_jsonl_bytes(templates))
    readme_path.write_bytes(_readme_bytes())

    index = _index_payload(
        output_root=declared_output_root,
        queue_path=queue_path,
        template_path=template_path,
        readme_path=readme_path,
        queue=queue,
        upstream=upstream,
    )
    index_path.write_bytes(_json_bytes(index))
    acceptance = _acceptance_payload(
        output_root=declared_output_root,
        index_path=index_path,
        queue_path=queue_path,
        template_path=template_path,
    )
    acceptance_path.write_bytes(_json_bytes(acceptance))
    for path in (queue_path, template_path, readme_path, index_path, acceptance_path):
        _write_sidecar(path)


def build_review_package(
    *,
    native_root: str | Path = DEFAULT_NATIVE_ROOT,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    replace: bool = False,
) -> dict[str, Any]:
    output = _repo_path(output_root)
    queue, templates, upstream = compile_review_materials(native_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent)
    )
    staging.rmdir()
    try:
        _write_package(
            target=staging,
            declared_output_root=output,
            queue=queue,
            templates=templates,
            upstream=upstream,
        )
        if output.exists():
            if _tree_hash(output) == _tree_hash(staging):
                shutil.rmtree(staging)
                return validate_review_package(output, native_root=native_root)
            if not replace:
                raise WebArenaHumanReviewError(
                    "review package differs; pass replace=True only after reviewing drift"
                )
            backup = output.with_name(f".{output.name}.old-{os.getpid()}")
            os.replace(output, backup)
            try:
                os.replace(staging, output)
            except Exception:
                os.replace(backup, output)
                raise
            shutil.rmtree(backup)
        else:
            os.replace(staging, output)
        report = validate_review_package(output, native_root=native_root)
        if report["status"] != "ok":
            raise WebArenaHumanReviewError(
                "generated review package failed validation: "
                + "; ".join(report["issues"][:8])
            )
        return report
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise WebArenaHumanReviewError(f"cannot read JSONL {path}: {exc}") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise WebArenaHumanReviewError(
                f"invalid JSONL line {line_number} in {path}"
            ) from exc
        if not isinstance(item, Mapping):
            raise WebArenaHumanReviewError(
                f"JSONL line {line_number} in {path} is not an object"
            )
        values.append(dict(item))
    return values


def validate_review_package(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    *,
    native_root: str | Path = DEFAULT_NATIVE_ROOT,
    completed_signoffs_path: str | Path | None = None,
) -> dict[str, Any]:
    root = _repo_path(output_root)
    issues: list[str] = []
    completed_status = "not_supplied"
    completed_count = 0
    try:
        expected_queue, expected_templates, upstream = compile_review_materials(
            native_root
        )
        queue_path = root / QUEUE_FILENAME
        template_path = root / TEMPLATE_FILENAME
        readme_path = root / README_FILENAME
        index_path = root / INDEX_FILENAME
        acceptance_path = root / ACCEPTANCE_FILENAME
        required_paths = (
            queue_path,
            template_path,
            readme_path,
            index_path,
            acceptance_path,
        )
        for path in required_paths:
            if not path.is_file() or path.is_symlink():
                issues.append(f"missing or symlinked package file: {path.name}")
        if issues:
            raise WebArenaHumanReviewError("; ".join(issues))

        actual_queue = _read_jsonl(queue_path)
        actual_templates = _read_jsonl(template_path)
        if actual_queue != expected_queue:
            issues.append("review queue differs from current deterministic sources")
        if actual_templates != expected_templates:
            issues.append("pending signoff template differs from current hash bindings")
        if queue_path.read_bytes() != _jsonl_bytes(expected_queue):
            issues.append("review queue serialization is noncanonical")
        if template_path.read_bytes() != _jsonl_bytes(expected_templates):
            issues.append("pending signoff template serialization is noncanonical")
        if readme_path.read_bytes() != _readme_bytes():
            issues.append("review instructions differ from the deterministic template")

        schema = _load_json(_resolve_repo_file(str(QUEUE_ITEM_SCHEMA)))
        validator = jsonschema.Draft202012Validator(schema)
        for line_number, item in enumerate(actual_queue, start=1):
            errors = sorted(
                validator.iter_errors(item), key=lambda error: list(error.path)
            )
            if errors:
                issues.append(
                    f"queue line {line_number} violates schema: "
                    + "; ".join(error.message for error in errors[:3])
                )
                break
            if item.get("human_signed") is not False or any(
                value is not None for value in item.get("decision_fields", {}).values()
            ):
                issues.append(
                    f"queue line {line_number} contains a fabricated human decision"
                )
                break
        if len(actual_queue) != native.EXPECTED_CASES:
            issues.append("review queue denominator is not exactly 812")
        if len(actual_templates) != native.EXPECTED_CASES:
            issues.append("pending signoff template denominator is not exactly 812")

        expected_index = _index_payload(
            output_root=root,
            queue_path=queue_path,
            template_path=template_path,
            readme_path=readme_path,
            queue=expected_queue,
            upstream=upstream,
        )
        actual_index = _load_json(index_path)
        if actual_index != expected_index or index_path.read_bytes() != _json_bytes(
            expected_index
        ):
            issues.append("review package index is stale or noncanonical")
        expected_acceptance = _acceptance_payload(
            output_root=root,
            index_path=index_path,
            queue_path=queue_path,
            template_path=template_path,
        )
        actual_acceptance = _load_json(acceptance_path)
        if actual_acceptance != expected_acceptance or acceptance_path.read_bytes() != (
            _json_bytes(expected_acceptance)
        ):
            issues.append("review package acceptance is stale or noncanonical")

        for path in required_paths:
            sidecar = path.with_suffix(path.suffix + ".sha256")
            expected = f"{native.file_sha256(path)}  {path.name}\n"
            if (
                not sidecar.is_file()
                or sidecar.is_symlink()
                or sidecar.read_text(encoding="utf-8") != expected
            ):
                issues.append(f"missing or invalid SHA-256 sidecar for {path.name}")
        for path in list(required_paths) + [
            path.with_suffix(path.suffix + ".sha256") for path in required_paths
        ]:
            payload = path.read_bytes()
            if any(marker in payload for marker in _SECRET_MARKERS):
                issues.append(f"secret marker detected in review package file {path.name}")

        if completed_signoffs_path is not None:
            completed_path = _repo_path(completed_signoffs_path)
            native_index = _load_json(_repo_path(native_root) / "index.json")
            input_lock_hash = native.file_sha256(
                _repo_path(native_root) / "input_lock.json"
            )
            try:
                completed = native._load_human_signoffs(
                    completed_path,
                    native_index["cases"],
                    input_lock_hash,
                )
            except native.WebArenaNativeClaimError as exc:
                issues.append(f"completed human signoffs invalid: {exc}")
                completed_status = "invalid"
            else:
                completed_count = len(completed)
                completed_status = "ready_for_formal_build"
    except (WebArenaHumanReviewError, OSError, KeyError, TypeError) as exc:
        issues.append(str(exc))

    status = "ok" if not issues else "blocked"
    if completed_signoffs_path is not None and status == "ok":
        status = "ready_for_formal_build"
    return {
        "schema_version": "webarena_verified_native_claim_human_review_validation/v1",
        "status": status,
        "issue_count": len(issues),
        "issues": issues,
        "counts": {
            "expected_queue_items": native.EXPECTED_CASES,
            "human_signed_in_queue": 0,
            "approved_in_queue": 0,
            "completed_signoffs_validated": completed_count,
        },
        "completed_signoffs_status": completed_status,
        "formal_locks_written": 0,
        "scheduler_outputs_written": 0,
    }


def package_hash(output_root: str | Path = DEFAULT_OUTPUT_ROOT) -> str:
    """Return a deterministic hash over all review-package files."""

    return _tree_hash(_repo_path(output_root))
