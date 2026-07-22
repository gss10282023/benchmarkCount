"""Build and validate the frozen AppWorld full-test extension.

The extension is deliberately disjoint from the submitted 100-case AppWorld
cohort.  It contains the remaining 68 ``test_normal`` tasks followed by all
417 ``test_challenge`` tasks.  The module is fail-closed: source identities,
task-directory inventories, protected-data files, packet contents, and bundle
hashes must all agree before an acceptance report can be published.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from evidence_system.contracts.case_packets import (
    CASE_PACKET_SCHEMA_VERSION,
    render_case_packet,
    validate_case_packet_source,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_bytes, sha256_file, sha256_object, sha256_path
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml


EXPERIMENT_ID = "appworld_full_test_extension_v1"
EXPERIMENT_SCHEMA = "experiment_manifest.appworld_full_test_extension.v1"
CATALOG_SCHEMA = "official_case_source.appworld_extension.v1"
SCOPE_SCHEMA = "appworld_extension_scope_lock.v1"
ACCEPTANCE_SCHEMA = "appworld_extension_acceptance.v1"
FROZEN_ON = "2026-07-16"

APPWORLD_REPOSITORY_URL = "https://github.com/StonyBrookNLP/appworld"
APPWORLD_GIT_COMMIT = "a072b7a86e7c1d5b1d7175659d750ebb9b79f10a"
APPWORLD_PACKAGE_VERSION = "0.1.3.post1"
APPWORLD_DATA_VERSION = "0.1.0"
CANONICAL_NORMAL_SPLIT_SHA256 = "c3af41497b6f2f0860a2ff8c09b335dca527e2cf48e59b4aabdb301b6b68db8f"
CANONICAL_CHALLENGE_SPLIT_SHA256 = "3c32b481042ac97f7d3477d53f5d196245c885c438d652944edc8a9a28e0f028"
CANONICAL_SELECTED_100_CATALOG_SHA256 = "d5e0be1b5c10b7d7d956292b435b59f57c5748bf3929e2c0664f97b7a5842e04"

EXPECTED_NORMAL_POOL_COUNT = 168
EXPECTED_CURRENT_COUNT = 100
EXPECTED_NORMAL_EXTENSION_COUNT = 68
EXPECTED_CHALLENGE_COUNT = 417
EXPECTED_EXTENSION_COUNT = 485
EXPECTED_FULL_TEST_COUNT = 585
EXPECTED_AGENT_COUNT = 3
EXPECTED_RECORD_SLOT_COUNT = EXPECTED_EXTENSION_COUNT * EXPECTED_AGENT_COUNT
EXPECTED_FILES_PER_TASK = 19

AGENT_IDS = ("Agent A", "Agent B", "Agent C")
DATASET_ORDER = ("test_normal", "test_challenge")
TASK_ID_PATTERN = re.compile(r"[0-9a-f]{7}_[123]")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")

REQUIRED_TASK_FILES = (
    "specs.json",
    "ground_truth/answer.json",
    "ground_truth/evaluation.py",
    "ground_truth/metadata.json",
    "ground_truth/private_data.json",
    "ground_truth/public_data.json",
    "ground_truth/test_data.json",
    "dbs/admin.jsonl",
    "dbs/amazon.jsonl",
    "dbs/api_docs.jsonl",
    "dbs/file_system.jsonl",
    "dbs/gmail.jsonl",
    "dbs/phone.jsonl",
    "dbs/simple_note.jsonl",
    "dbs/splitwise.jsonl",
    "dbs/spotify.jsonl",
    "dbs/supervisor.jsonl",
    "dbs/todoist.jsonl",
    "dbs/venmo.jsonl",
)

DEFAULT_OUTPUT_ROOT = Path("experiments") / EXPERIMENT_ID
DEFAULT_NORMAL_SPLIT = Path("experiments/official_splits/appworld_test_normal.txt")
DEFAULT_CHALLENGE_SPLIT = Path("experiments/official_splits/appworld_test_challenge.not_selected.txt")
DEFAULT_CURRENT_CATALOG = Path("experiments/official_splits/appworld_selected_task_sources.json")
DEFAULT_TASKS_ROOT = Path("vps_snapshots/other-vps-01/data/tasks")
DEFAULT_DATA_VERSION_PATH = Path("vps_snapshots/other-vps-01/data/version.txt")
DEFAULT_BASE_DBS_ROOT = Path("vps_snapshots/other-vps-01/data/base_dbs")
DEFAULT_SNAPSHOT_README = Path("vps_snapshots/other-vps-01/README.md")
DEFAULT_INSTALL_LOG = Path("vps_snapshots/other-vps-01/project/results/logs/install_other_benchmarks.log")
DEFAULT_AGENTS_CONFIG = Path("configs/agents.yaml")
DEFAULT_SCORE_PROMPT = Path("neurips_ed_track_minimal/prompts/score_evidence_with_codex.prompt.md")
DEFAULT_SCORE_SCHEMA = Path("neurips_ed_track_minimal/schemas/evidence_score.schema.json")
DEFAULT_DRAFT_PROMPT = Path("neurips_ed_track_minimal/prompts/draft_case_checklist.prompt.md")
DEFAULT_DRAFT_SCHEMA = Path("neurips_ed_track_minimal/schemas/case_checklist.schema.json")
DEFAULT_DRAFT_SCRIPT = Path("neurips_ed_track_minimal/scripts/draft_case_checklist.py")
DEFAULT_DRAFT_BATCH_SCRIPT = Path("neurips_ed_track_minimal/scripts/run_draft_batch.py")
DEFAULT_DRAFT_TEMPLATE = Path("neurips_ed_track_minimal/templates/case_checklist.template.yaml")
DEFAULT_DRAFT_GUARDRAILS = Path("neurips_ed_track_minimal/checklist_guardrails.py")
DEFAULT_EXISTING_SCORE_ROOT = Path("paper_result_packages/appworld_case_bundle_openrouter")
DEFAULT_EXISTING_DRAFT_ROOT = DEFAULT_EXISTING_SCORE_ROOT / "cases"
DEFAULT_EXISTING_PACKETS = Path("experiments/case_packets/appworld")
DEFAULT_EXISTING_SOURCE_BUNDLE = Path(
    "experiments/evidence_contracts/source_bundles/main_case_units_source_bundle.json"
)
DEFAULT_EXISTING_MANIFEST = Path("experiments/experiment_manifest.yaml")


def build_appworld_extension(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    normal_split_path: str | Path = DEFAULT_NORMAL_SPLIT,
    challenge_split_path: str | Path = DEFAULT_CHALLENGE_SPLIT,
    current_catalog_path: str | Path = DEFAULT_CURRENT_CATALOG,
    tasks_root: str | Path = DEFAULT_TASKS_ROOT,
    data_version_path: str | Path = DEFAULT_DATA_VERSION_PATH,
    base_dbs_root: str | Path = DEFAULT_BASE_DBS_ROOT,
    agents_config_path: str | Path = DEFAULT_AGENTS_CONFIG,
) -> dict[str, Any]:
    """Materialize the frozen catalog, scope lock, and extension manifest."""

    _validate_build_path_isolation(
        output_root=output_root,
        normal_split_path=normal_split_path,
        challenge_split_path=challenge_split_path,
        current_catalog_path=current_catalog_path,
        tasks_root=tasks_root,
        data_version_path=data_version_path,
        base_dbs_root=base_dbs_root,
        agents_config_path=agents_config_path,
    )
    paths = _output_paths(output_root)
    payloads = _expected_artifacts(
        output_root=output_root,
        normal_split_path=normal_split_path,
        challenge_split_path=challenge_split_path,
        current_catalog_path=current_catalog_path,
        tasks_root=tasks_root,
        data_version_path=data_version_path,
        base_dbs_root=base_dbs_root,
        agents_config_path=agents_config_path,
    )
    text_keys = ("normal_extension_ids", "challenge_ids", "extension_ids")
    json_keys = ("catalog", "scope", "manifest")
    definition_paths = [paths[key] for key in (*text_keys, *json_keys)]
    existing_count = sum(path.exists() for path in definition_paths)
    if existing_count:
        _require(
            existing_count == len(definition_paths),
            "extension definition is partially materialized; refusing to overwrite a frozen namespace",
        )
        for key in text_keys:
            _require(
                paths[key].read_text(encoding="utf-8") == payloads[key],
                f"frozen extension definition differs at {paths[key]}; use a new experiment ID",
            )
        for key in json_keys:
            _require(
                paths[key].read_bytes() == _json_bytes(payloads[key]),
                f"frozen extension definition differs at {paths[key]}; use a new experiment ID",
            )
    else:
        for key in text_keys:
            _write_text_atomic(paths[key], payloads[key])
        for key in json_keys:
            _write_json_atomic(paths[key], payloads[key])

    audit = validate_extension_definition(
        output_root=output_root,
        normal_split_path=normal_split_path,
        challenge_split_path=challenge_split_path,
        current_catalog_path=current_catalog_path,
        tasks_root=tasks_root,
        data_version_path=data_version_path,
        base_dbs_root=base_dbs_root,
        agents_config_path=agents_config_path,
    )
    return {
        "status": "ok",
        "experiment_id": EXPERIMENT_ID,
        "catalog_path": _repo_relative(paths["catalog"]),
        "catalog_sha256": sha256_file(paths["catalog"]),
        "scope_lock_path": _repo_relative(paths["scope"]),
        "scope_lock_sha256": sha256_file(paths["scope"]),
        "manifest_path": _repo_relative(paths["manifest"]),
        "manifest_sha256": sha256_file(paths["manifest"]),
        **audit,
    }


def validate_extension_definition(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    normal_split_path: str | Path = DEFAULT_NORMAL_SPLIT,
    challenge_split_path: str | Path = DEFAULT_CHALLENGE_SPLIT,
    current_catalog_path: str | Path = DEFAULT_CURRENT_CATALOG,
    tasks_root: str | Path = DEFAULT_TASKS_ROOT,
    data_version_path: str | Path = DEFAULT_DATA_VERSION_PATH,
    base_dbs_root: str | Path = DEFAULT_BASE_DBS_ROOT,
    agents_config_path: str | Path = DEFAULT_AGENTS_CONFIG,
) -> dict[str, Any]:
    """Recompute all pre-packet artifacts and require byte-for-byte equality."""

    paths = _output_paths(output_root)
    expected = _expected_artifacts(
        output_root=output_root,
        normal_split_path=normal_split_path,
        challenge_split_path=challenge_split_path,
        current_catalog_path=current_catalog_path,
        tasks_root=tasks_root,
        data_version_path=data_version_path,
        base_dbs_root=base_dbs_root,
        agents_config_path=agents_config_path,
    )
    for key in ("normal_extension_ids", "challenge_ids", "extension_ids"):
        _require(paths[key].is_file(), f"extension ID file is missing: {paths[key]}")
        _require(paths[key].read_text(encoding="utf-8") == expected[key], f"extension ID file drift: {paths[key]}")
    for key in ("catalog", "scope", "manifest"):
        _require(paths[key].is_file(), f"extension artifact is missing: {paths[key]}")
        actual_bytes = paths[key].read_bytes()
        expected_bytes = _json_bytes(expected[key])
        _require(actual_bytes == expected_bytes, f"extension artifact drift: {paths[key]}")

    catalog = expected["catalog"]
    manifest = expected["manifest"]
    _require(catalog["selected_count"] == EXPECTED_EXTENSION_COUNT, "catalog selected_count mismatch")
    _require(manifest["domains"][0]["case_unit_count"] == EXPECTED_EXTENSION_COUNT, "manifest case count mismatch")
    _require(manifest["domains"][0]["record_slot_count"] == EXPECTED_RECORD_SLOT_COUNT, "manifest slot count mismatch")
    return {
        "definition_verified": True,
        "normal_pool_count": EXPECTED_NORMAL_POOL_COUNT,
        "completed_case_count": EXPECTED_CURRENT_COUNT,
        "normal_extension_count": EXPECTED_NORMAL_EXTENSION_COUNT,
        "challenge_count": EXPECTED_CHALLENGE_COUNT,
        "extension_case_count": EXPECTED_EXTENSION_COUNT,
        "full_test_case_count": EXPECTED_FULL_TEST_COUNT,
        "record_slot_count": EXPECTED_RECORD_SLOT_COUNT,
        "source_file_count": catalog["source_file_count"],
        "source_byte_count": catalog["source_byte_count"],
        "source_tree_sha256": catalog["source_tree_sha256"].removeprefix("sha256:"),
    }


def validate_extension_packets(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    case_packets_root: str | Path | None = None,
) -> dict[str, Any]:
    """Strictly validate all 485 AppWorld packets against the frozen catalog."""

    paths = _output_paths(output_root)
    catalog = _load_mapping(paths["catalog"], "extension source catalog")
    manifest = _load_mapping(paths["manifest"], "extension manifest")
    items = _catalog_items(catalog)
    cases = _manifest_cases(manifest)
    _require([case["case_unit_id"] for case in cases] == list(items), "manifest/catalog case order mismatch")

    packet_root = resolve_repo_path(case_packets_root or (resolve_repo_path(output_root) / "case_packets"))
    domain_root = packet_root / "appworld"
    _require(packet_root.is_dir() and not packet_root.is_symlink(), f"packet root is missing or symlinked: {packet_root}")
    _require(not domain_root.is_symlink(), f"AppWorld packet directory must not be a symlink: {domain_root}")
    _require(domain_root.is_dir(), f"AppWorld packet directory is missing: {domain_root}")
    actual_dirs = {path.name for path in domain_root.iterdir() if path.is_dir()}
    expected_dirs = set(items)
    _require(
        actual_dirs == expected_dirs,
        f"packet directory set mismatch: missing={sorted(expected_dirs-actual_dirs)[:10]}, extra={sorted(actual_dirs-expected_dirs)[:10]}",
    )
    non_directories = sorted(path.name for path in domain_root.iterdir() if not path.is_dir())
    _require(not non_directories, f"unexpected non-directory entries in packet root: {non_directories[:10]}")

    split_counts: Counter[str] = Counter()
    packet_hashes: list[dict[str, str]] = []
    tree_lines: list[str] = []
    verified_file_count = 0
    verified_byte_count = 0
    json_file_count = 0
    jsonl_file_count = 0
    python_file_count = 0
    for case in cases:
        task_id = case["task_id"]
        item = items[task_id]
        dataset_name = str(item["dataset_name"])
        source_ref = str(item["source_ref"])
        split_counts[dataset_name] += 1
        case_dir = domain_root / task_id
        packet_path = case_dir / "case_packet.md"
        raw_manifest_path = case_dir / "raw_case_manifest.json"
        raw_case_dir = case_dir / "raw_case"
        _require(packet_path.is_file(), f"missing case_packet.md for {task_id}")
        _require(raw_manifest_path.is_file(), f"missing raw_case_manifest.json for {task_id}")
        _require(raw_case_dir.is_dir(), f"missing raw_case directory for {task_id}")
        expected_descriptors = item["files"]
        expected_archives = sorted(str(value["archive_path"]) for value in expected_descriptors.values())
        expected_hashes = {
            str(descriptor["archive_path"]): str(descriptor["sha256"]).removeprefix("sha256:")
            for _, descriptor in sorted(expected_descriptors.items())
        }
        expected_file_sources = {
            str(descriptor["archive_path"]): f"{source_ref}#{relative}"
            for relative, descriptor in sorted(expected_descriptors.items())
        }
        expected_raw_manifest = {
            "case_unit_id": task_id,
            "catalog_item_sha256": item["source_item_sha256"],
            "copied_files": expected_archives,
            "dataset_name": dataset_name,
            "derived_files": [],
            "domain": "appworld",
            "file_sources": expected_file_sources,
            "official_files": expected_archives,
            "packet_files": expected_archives,
            "sha256_per_file": expected_hashes,
            "source_ref": source_ref,
            "source_refs": [source_ref, str(item["task_dir"])],
            "split": dataset_name,
            "task_dir": item["task_dir"],
            "task_id": task_id,
            "task_tree_sha256": item["task_tree_sha256"],
        }
        raw_manifest = _load_mapping(raw_manifest_path, f"raw manifest {task_id}")
        _require(
            dict(raw_manifest) == expected_raw_manifest,
            f"{task_id} raw manifest is not the exact catalog-derived manifest",
        )

        expected_case_entries = {"case_packet.md", "raw_case_manifest.json", "raw_case"}
        actual_case_entries = {path.name for path in case_dir.iterdir()}
        _require(actual_case_entries == expected_case_entries, f"{task_id} case directory layout mismatch")
        _require(not case_dir.is_symlink(), f"{task_id} case directory must not be a symlink")
        _require(not packet_path.is_symlink(), f"{task_id} case_packet.md must not be a symlink")
        _require(not raw_manifest_path.is_symlink(), f"{task_id} raw_case_manifest.json must not be a symlink")
        _require(not raw_case_dir.is_symlink(), f"{task_id} raw_case directory must not be a symlink")
        expected_raw_dirs = {
            parent.as_posix()
            for path in expected_archives
            for parent in Path(path).parents
            if parent != Path(".")
        }
        actual_raw_dirs = {
            path.relative_to(raw_case_dir).as_posix()
            for path in raw_case_dir.rglob("*")
            if path.is_dir()
        }
        _require(actual_raw_dirs == expected_raw_dirs, f"{task_id} raw directory layout mismatch")
        _require(
            not any(path.is_symlink() for path in raw_case_dir.rglob("*")),
            f"{task_id} raw tree contains a symlink",
        )
        actual_raw_files = sorted(
            path.relative_to(raw_case_dir).as_posix() for path in raw_case_dir.rglob("*") if path.is_file()
        )
        for field in ("copied_files", "official_files", "packet_files"):
            _require(sorted(raw_manifest.get(field) or []) == expected_archives, f"{task_id} {field} inventory mismatch")
        _require(list(raw_manifest.get("derived_files") or []) == [], f"{task_id} has unexpected derived files")
        _require(actual_raw_files == expected_archives, f"{task_id} raw directory inventory mismatch")
        hashes = raw_manifest["sha256_per_file"]
        file_sources = raw_manifest["file_sources"]

        for relative, descriptor in sorted(expected_descriptors.items()):
            archive_path = str(descriptor["archive_path"])
            raw_path = raw_case_dir / archive_path
            _require(raw_path.is_file() and not raw_path.is_symlink(), f"{task_id}/{archive_path} missing or symlinked")
            digest = sha256_file(raw_path)
            expected_digest = str(descriptor["sha256"]).removeprefix("sha256:")
            _require(digest == expected_digest, f"{task_id}/{archive_path} catalog hash mismatch")
            _require(hashes[archive_path] == digest, f"{task_id}/{archive_path} raw-manifest hash mismatch")
            _require(file_sources[archive_path] == f"{source_ref}#{relative}", f"{task_id}/{archive_path} source pointer mismatch")
            size = raw_path.stat().st_size
            _require(size == descriptor["size_bytes"], f"{task_id}/{archive_path} size mismatch")
            _validate_structured_file(raw_path, relative)
            if relative.endswith(".json"):
                json_file_count += 1
            elif relative.endswith(".jsonl"):
                jsonl_file_count += 1
            elif relative.endswith(".py"):
                python_file_count += 1
            tree_lines.append(f"{task_id}\t{relative}\t{digest}\n")
            verified_file_count += 1
            verified_byte_count += size

        expected_packet = render_case_packet(
            domain="appworld",
            case_unit_id=task_id,
            task_id=task_id,
            raw_case_dir=raw_case_dir,
            raw_case_manifest=raw_manifest,
        )
        actual_packet = packet_path.read_text(encoding="utf-8")
        _require(actual_packet == expected_packet, f"{task_id} case_packet.md is not an exact renderer output")
        packet_hashes.append(
            {
                "task_id": task_id,
                "case_packet_sha256": sha256_file(packet_path),
                "raw_case_manifest_sha256": sha256_file(raw_manifest_path),
            }
        )

    tree_digest = hashlib.sha256("".join(sorted(tree_lines)).encode("utf-8")).hexdigest()
    _require(tree_digest == str(catalog["source_tree_sha256"]).removeprefix("sha256:"), "packet/source tree digest mismatch")
    _require(verified_file_count == EXPECTED_EXTENSION_COUNT * EXPECTED_FILES_PER_TASK, "verified file count mismatch")
    _require(verified_byte_count == catalog["source_byte_count"], "verified byte count mismatch")
    _require(dict(split_counts) == {"test_normal": 68, "test_challenge": 417}, "packet split counts mismatch")
    return {
        "packets_verified": True,
        "packet_count": EXPECTED_EXTENSION_COUNT,
        "packet_count_by_dataset": dict(sorted(split_counts.items())),
        "verified_official_file_count": verified_file_count,
        "verified_official_byte_count": verified_byte_count,
        "verified_json_file_count": json_file_count,
        "verified_jsonl_file_count": jsonl_file_count,
        "verified_python_file_count": python_file_count,
        "packet_source_tree_sha256": tree_digest,
        "packet_index_sha256": sha256_object(packet_hashes),
    }


def validate_extension_source_bundle(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    case_packets_root: str | Path | None = None,
    source_bundle_path: str | Path | None = None,
) -> dict[str, Any]:
    """Validate exact bundle membership, routing metadata, pointers, and hashes."""

    paths = _output_paths(output_root)
    manifest = _load_mapping(paths["manifest"], "extension manifest")
    cases = _manifest_cases(manifest)
    packet_root = resolve_repo_path(case_packets_root or (resolve_repo_path(output_root) / "case_packets"))
    bundle_path = resolve_repo_path(source_bundle_path or (resolve_repo_path(output_root) / "source_bundles/case_packet_source_bundle.json"))
    _require(packet_root.is_dir() and not packet_root.is_symlink(), f"packet root is missing or symlinked: {packet_root}")
    _require(bundle_path.is_file() and not bundle_path.is_symlink(), f"source bundle is missing or symlinked: {bundle_path}")
    bundle = _load_mapping(bundle_path, "extension source bundle")
    sources = bundle.get("sources")
    _require(isinstance(sources, list), "source bundle requires sources list")
    _require(
        set(bundle) == {"manifest_path", "manifest_sha256", "schema_version", "source_count", "sources"},
        "source bundle top-level field set mismatch",
    )
    _require(bundle.get("schema_version") == CASE_PACKET_SCHEMA_VERSION, "source bundle schema version mismatch")
    _require(bundle.get("source_count") == EXPECTED_EXTENSION_COUNT == len(sources), "source bundle count mismatch")
    _require(bundle.get("manifest_path") == _repo_relative(paths["manifest"]), "source bundle manifest pointer mismatch")
    _require(bundle.get("manifest_sha256") == sha256_file(paths["manifest"]), "source bundle manifest hash mismatch")
    expected_ids = [case["case_unit_id"] for case in cases]
    actual_ids = [str(source.get("case_unit_id") or "") for source in sources if isinstance(source, Mapping)]
    _require(actual_ids == expected_ids, "source bundle case set/order mismatch")
    contract_ids = [str(source.get("contract_id") or "") for source in sources if isinstance(source, Mapping)]
    _require(all(contract_ids) and len(set(contract_ids)) == EXPECTED_EXTENSION_COUNT, "source bundle contract IDs are missing or duplicated")

    verified_hashes = 0
    for index, (case, raw_source) in enumerate(zip(cases, sources, strict=True)):
        _require(isinstance(raw_source, Mapping), f"source bundle item {index} must be a mapping")
        source = dict(raw_source)
        task_id = case["task_id"]
        _require(
            set(source) == {"case_unit_id", "contract_id", "dataset_name", "domain", "draft_input", "source_ref", "task_id"},
            f"bundle {task_id} field set mismatch",
        )
        _require(
            source.get("contract_id") == f"ec_appworld_{task_id}_contract_v1_0_0",
            f"bundle {task_id} contract_id is not the deterministic extension ID",
        )
        for field, expected_value in (
            ("domain", "appworld"),
            ("case_unit_id", case["case_unit_id"]),
            ("task_id", case["task_id"]),
            ("dataset_name", case["dataset_name"]),
            ("source_ref", case["source_ref"]),
        ):
            _require(source.get(field) == expected_value, f"bundle {task_id} {field} mismatch")
        issues = validate_case_packet_source(source, f"$.sources[{index}]")
        _require(not issues, f"bundle {task_id} packet-source validation failed: {issues[:3]}")
        draft = source.get("draft_input")
        _require(isinstance(draft, Mapping), f"bundle {task_id} draft_input missing")
        _require(
            set(draft)
            == {"case_packet_path", "case_packet_sha256", "raw_case_manifest_path", "raw_case_manifest_sha256"},
            f"bundle {task_id} draft_input field set mismatch",
        )
        case_dir = packet_root / "appworld" / task_id
        expected_paths = {
            "case_packet_path": case_dir / "case_packet.md",
            "raw_case_manifest_path": case_dir / "raw_case_manifest.json",
        }
        for field, expected_path in expected_paths.items():
            _require(resolve_repo_path(str(draft.get(field) or "")).resolve() == expected_path.resolve(), f"bundle {task_id} {field} mismatch")
        for path_field, hash_field in (
            ("case_packet_path", "case_packet_sha256"),
            ("raw_case_manifest_path", "raw_case_manifest_sha256"),
        ):
            digest = str(draft.get(hash_field) or "")
            _require(SHA256_PATTERN.fullmatch(digest) is not None, f"bundle {task_id} {hash_field} invalid")
            _require(digest == sha256_file(resolve_repo_path(str(draft[path_field]))), f"bundle {task_id} {hash_field} mismatch")
            verified_hashes += 1
    return {
        "source_bundle_verified": True,
        "source_bundle_path": _repo_relative(bundle_path),
        "source_bundle_sha256": sha256_file(bundle_path),
        "source_count": EXPECTED_EXTENSION_COUNT,
        "verified_bundle_file_hash_count": verified_hashes,
        "routing_metadata_verified": True,
    }


def write_acceptance_report(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    case_packets_root: str | Path | None = None,
    source_bundle_path: str | Path | None = None,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    """Publish a non-sensitive report only after every gate passes."""

    provenance_root = (resolve_repo_path(output_root) / "provenance").resolve()
    destination = resolve_repo_path(report_path or (provenance_root / "acceptance_report.json")).resolve()
    _require(
        provenance_root in destination.parents and destination.suffix == ".json",
        f"acceptance report must be a JSON file inside {provenance_root}",
    )
    definition = validate_extension_definition(output_root=output_root)
    packets = validate_extension_packets(output_root=output_root, case_packets_root=case_packets_root)
    bundle = validate_extension_source_bundle(
        output_root=output_root,
        case_packets_root=case_packets_root,
        source_bundle_path=source_bundle_path,
    )
    paths = _output_paths(output_root)
    payload = {
        "schema_version": ACCEPTANCE_SCHEMA,
        "status": "accepted",
        "experiment_id": EXPERIMENT_ID,
        "protected_data_notice": (
            "AppWorld protected source and derived packets must remain access-controlled or be redistributed only encrypted."
        ),
        "definition": definition,
        "packets": packets,
        "source_bundle": bundle,
        "artifact_hashes": {
            "catalog_sha256": sha256_file(paths["catalog"]),
            "scope_lock_sha256": sha256_file(paths["scope"]),
            "manifest_sha256": sha256_file(paths["manifest"]),
        },
        "all_hard_gates_passed": True,
    }
    _write_json_atomic(destination, payload)
    payload["acceptance_report_path"] = _repo_relative(destination)
    payload["acceptance_report_sha256"] = sha256_file(destination)
    return payload


def _expected_artifacts(
    *,
    output_root: str | Path,
    normal_split_path: str | Path,
    challenge_split_path: str | Path,
    current_catalog_path: str | Path,
    tasks_root: str | Path,
    data_version_path: str | Path,
    base_dbs_root: str | Path,
    agents_config_path: str | Path,
) -> dict[str, Any]:
    output = resolve_repo_path(output_root)
    paths = _output_paths(output)
    normal_path = resolve_repo_path(normal_split_path)
    challenge_path = resolve_repo_path(challenge_split_path)
    current_path = resolve_repo_path(current_catalog_path)
    task_root = resolve_repo_path(tasks_root)
    data_version = resolve_repo_path(data_version_path)
    base_dbs = resolve_repo_path(base_dbs_root)
    agent_path = resolve_repo_path(agents_config_path)

    normal_ids = _read_split_ids(
        normal_path,
        "test_normal",
        EXPECTED_NORMAL_POOL_COUNT,
        CANONICAL_NORMAL_SPLIT_SHA256,
    )
    challenge_ids = _read_split_ids(
        challenge_path,
        "test_challenge",
        EXPECTED_CHALLENGE_COUNT,
        CANONICAL_CHALLENGE_SPLIT_SHA256,
    )
    _require(set(normal_ids).isdisjoint(challenge_ids), "AppWorld normal/challenge pools overlap")
    current_ids = _read_current_selected_ids(current_path)
    _require(set(current_ids).issubset(normal_ids), "current selected-100 is not a subset of test_normal")
    normal_extension = [task_id for task_id in normal_ids if task_id not in set(current_ids)]
    _require(len(normal_extension) == EXPECTED_NORMAL_EXTENSION_COUNT, "normal extension count mismatch")
    extension_ids = normal_extension + challenge_ids
    _require(len(extension_ids) == len(set(extension_ids)) == EXPECTED_EXTENSION_COUNT, "extension IDs are not exactly 485 unique cases")
    _require(set(current_ids) | set(extension_ids) == set(normal_ids) | set(challenge_ids), "full-test set algebra mismatch")

    source_items: list[dict[str, Any]] = []
    tree_lines: list[str] = []
    split_tree_lines: dict[str, list[str]] = {name: [] for name in DATASET_ORDER}
    source_byte_count = 0
    split_bytes: Counter[str] = Counter()
    for dataset_name, task_ids in (("test_normal", normal_extension), ("test_challenge", challenge_ids)):
        for task_id in task_ids:
            item, lines, byte_count = _source_item(task_root, dataset_name, task_id)
            source_items.append(item)
            tree_lines.extend(lines)
            split_tree_lines[dataset_name].extend(lines)
            source_byte_count += byte_count
            split_bytes[dataset_name] += byte_count
    items_by_id = {str(item["task_id"]): item for item in source_items}

    extension_text = _id_text(extension_ids)
    normal_extension_text = _id_text(normal_extension)
    challenge_text = _id_text(challenge_ids)
    selection_rule = (
        "test_normal official order with existing selected-100 removed, followed by test_challenge official order"
    )
    exclusion_rule = "exclude exactly the existing selected-100 test_normal IDs"
    source_tree_sha = _tree_line_digest(tree_lines)
    split_tree_sha = {key: _tree_line_digest(value) for key, value in split_tree_lines.items()}
    catalog = {
        "schema_version": CATALOG_SCHEMA,
        "benchmark": "AppWorld",
        "selection_id": EXPERIMENT_ID,
        "dataset_names": list(DATASET_ORDER),
        "source_root": _repo_relative(task_root),
        "materialization": "copy_local_task_directory",
        "selected_count": EXPECTED_EXTENSION_COUNT,
        "selected_count_by_dataset": {"test_normal": 68, "test_challenge": 417},
        "source_file_count": EXPECTED_EXTENSION_COUNT * EXPECTED_FILES_PER_TASK,
        "source_byte_count": source_byte_count,
        "source_tree_sha256": f"sha256:{source_tree_sha}",
        "source_tree_sha256_by_dataset": {key: f"sha256:{value}" for key, value in split_tree_sha.items()},
        "source_byte_count_by_dataset": dict(sorted(split_bytes.items())),
        "candidate_pools": [
            {
                "dataset_name": "test_normal",
                "path": _repo_relative(normal_path),
                "sha256": f"sha256:{sha256_file(normal_path)}",
                "canonical_data_version": APPWORLD_DATA_VERSION,
                "canonical_sha256": f"sha256:{CANONICAL_NORMAL_SPLIT_SHA256}",
                "provenance": "exported from the pinned AppWorld protected data bundle datasets/test_normal.txt",
                "eligible_count": EXPECTED_NORMAL_POOL_COUNT,
                "selected_for_extension": EXPECTED_NORMAL_EXTENSION_COUNT,
            },
            {
                "dataset_name": "test_challenge",
                "path": _repo_relative(challenge_path),
                "sha256": f"sha256:{sha256_file(challenge_path)}",
                "canonical_data_version": APPWORLD_DATA_VERSION,
                "canonical_sha256": f"sha256:{CANONICAL_CHALLENGE_SPLIT_SHA256}",
                "provenance": "exported from the pinned AppWorld protected data bundle datasets/test_challenge.txt",
                "eligible_count": EXPECTED_CHALLENGE_COUNT,
                "selected_for_extension": EXPECTED_CHALLENGE_COUNT,
            },
        ],
        "completed_cohort": {
            "catalog_path": _repo_relative(current_path),
            "catalog_sha256": f"sha256:{sha256_file(current_path)}",
            "case_count": EXPECTED_CURRENT_COUNT,
            "case_ids_sha256": f"sha256:{sha256_object(current_ids)}",
            "exclusion_rule": exclusion_rule,
            "exclusion_rule_sha256": f"sha256:{sha256_object(exclusion_rule)}",
        },
        "selection_order_rule": selection_rule,
        "selection_rule_sha256": f"sha256:{sha256_object(selection_rule)}",
        "selection_order_sha256": f"sha256:{sha256_object(extension_ids)}",
        "derived_id_files": {
            "normal_extension": {
                "path": _repo_relative(paths["normal_extension_ids"]),
                "sha256": f"sha256:{sha256_bytes(normal_extension_text.encode('utf-8'))}",
                "count": 68,
            },
            "challenge": {
                "path": _repo_relative(paths["challenge_ids"]),
                "sha256": f"sha256:{sha256_bytes(challenge_text.encode('utf-8'))}",
                "count": 417,
            },
            "extension": {
                "path": _repo_relative(paths["extension_ids"]),
                "sha256": f"sha256:{sha256_bytes(extension_text.encode('utf-8'))}",
                "count": 485,
            },
        },
        "provenance": _appworld_provenance(data_version, base_dbs),
        "items": source_items,
    }
    catalog_sha = sha256_bytes(_json_bytes(catalog))

    agents_lock = _agents_lock(agent_path)
    drafter_lock = _drafter_lock(agent_path, current_ids)
    scorer_lock = _scorer_lock(current_ids)
    legacy_lock = _legacy_lock(current_path)
    scope = {
        "schema_version": SCOPE_SCHEMA,
        "experiment_id": EXPERIMENT_ID,
        "frozen_on": FROZEN_ON,
        "status": "frozen_pre_run",
        "scope": {
            "full_test_case_count": EXPECTED_FULL_TEST_COUNT,
            "full_test_case_count_by_dataset": {"test_normal": 168, "test_challenge": 417},
            "completed_case_count": EXPECTED_CURRENT_COUNT,
            "extension_case_count": EXPECTED_EXTENSION_COUNT,
            "extension_case_count_by_dataset": {"test_normal": 68, "test_challenge": 417},
            "extension_record_slot_count": EXPECTED_RECORD_SLOT_COUNT,
        },
        "set_hashes": {
            "normal_pool_order_sha256": f"sha256:{sha256_object(normal_ids)}",
            "challenge_pool_order_sha256": f"sha256:{sha256_object(challenge_ids)}",
            "completed_100_order_sha256": f"sha256:{sha256_object(current_ids)}",
            "normal_extension_order_sha256": f"sha256:{sha256_object(normal_extension)}",
            "extension_order_sha256": f"sha256:{sha256_object(extension_ids)}",
            "full_test_set_sha256": f"sha256:{sha256_object(sorted(set(normal_ids) | set(challenge_ids)))}",
        },
        "appworld": _appworld_provenance(data_version, base_dbs),
        "source_catalog": {
            "path": _repo_relative(paths["catalog"]),
            "sha256": f"sha256:{catalog_sha}",
            "source_tree_sha256": f"sha256:{source_tree_sha}",
        },
        "agents": agents_lock,
        "contract_drafter": drafter_lock,
        "scorer": scorer_lock,
        "retry_policy": {
            "max_retries_per_record": 2,
            "retryable": ["recoverable infrastructure failure", "pre-run failure", "recoverable logging/collection failure"],
            "non_retryable": [
                "agent-caused invalid action",
                "tool misuse",
                "malformed final answer",
                "timeout after benchmark execution begins",
                "FAIL",
                "UNRESOLVE",
            ],
            "attempt_rule": "preserve every attempt and select exactly one canonical final attempt",
            "identity_invariance": ["case_unit_id", "agent_id", "contract_version", "taxonomy_version", "config_hash"],
        },
        "denominator_policy": {
            "planned_record_slots": EXPECTED_RECORD_SLOT_COUNT,
            "cartesian_product": "485 frozen cases x Agent A/B/C",
            "completed_denominator": "completed scored records",
            "excluded_from_evidence_denominator_only": "proven infrastructure or pre-run failures",
            "included_as_agent_outcomes": [
                "agent-caused invalid action",
                "tool misuse",
                "malformed final answer",
                "timeout after benchmark execution begins",
                "benchmark-facing abort",
            ],
            "audit_identity": "TOTAL = SUCCESS + FAIL + UNRESOLVE for completed scored records; attempted slots are reported separately",
        },
        "legacy_100_isolation": legacy_lock,
        "protected_data_policy": {
            "source": _repo_relative(resolve_repo_path("vps_snapshots/other-vps-01/data/README_BEFORE_SHARING.md")),
            "rule": "raw tasks and derived packets remain access-controlled; any public redistribution must be encrypted",
            "prompt_boundary": "raw packets are pre-run drafting/review inputs and must not be exposed to benchmark agents or scorers",
        },
    }
    scope_sha = sha256_bytes(_json_bytes(scope))
    agent_names = list(AGENT_IDS)
    slot_ids = [f"{task_id}::{agent_id}" for task_id in extension_ids for agent_id in agent_names]
    manifest = {
        "schema_version": EXPERIMENT_SCHEMA,
        "manifest_id": EXPERIMENT_ID,
        "manifest_version": "1.0.0-frozen",
        "status": "frozen_pre_run",
        "result_namespace": EXPERIMENT_ID,
        "scope_lock_path": _repo_relative(paths["scope"]),
        "scope_lock_sha256": f"sha256:{scope_sha}",
        "source_catalog_path": _repo_relative(paths["catalog"]),
        "source_catalog_sha256": f"sha256:{catalog_sha}",
        "full_pool": {
            "case_unit_count": EXPECTED_FULL_TEST_COUNT,
            "test_normal_count": EXPECTED_NORMAL_POOL_COUNT,
            "test_challenge_count": EXPECTED_CHALLENGE_COUNT,
        },
        "completed_cohort": {
            "case_unit_count": EXPECTED_CURRENT_COUNT,
            "dataset_name": "test_normal",
            "case_ids_sha256": f"sha256:{sha256_object(current_ids)}",
            "rule": exclusion_rule,
            "rule_sha256": f"sha256:{sha256_object(exclusion_rule)}",
        },
        "selection": {
            "rule": catalog["selection_order_rule"],
            "rule_sha256": f"sha256:{sha256_object(catalog['selection_order_rule'])}",
            "extension_case_ids_sha256": f"sha256:{sha256_object(extension_ids)}",
            "excluded_case_ids_sha256": f"sha256:{sha256_object(current_ids)}",
            "source_tree_sha256": f"sha256:{source_tree_sha}",
        },
        "agents_config_path": _repo_relative(agent_path),
        "agents_config_sha256": agents_lock["agents_config_sha256"],
        "contract_drafter_config_sha256": drafter_lock["config_sha256"],
        "scorer_config_sha256": scorer_lock["config_sha256"],
        "retry_policy_sha256": f"sha256:{sha256_object(scope['retry_policy'])}",
        "denominator_policy_sha256": f"sha256:{sha256_object(scope['denominator_policy'])}",
        "domains": [
            {
                "domain": "appworld",
                "domain_display_name": "AppWorld",
                "experiment_type": "appendix_extension",
                "priority": "P1",
                "claim_scope": "native_aligned",
                "official_full_test_pool_case_units": EXPECTED_FULL_TEST_COUNT,
                "completed_case_unit_count": EXPECTED_CURRENT_COUNT,
                "case_unit_count": EXPECTED_EXTENSION_COUNT,
                "case_unit_count_by_dataset": {"test_normal": 68, "test_challenge": 417},
                "record_slot_count": EXPECTED_RECORD_SLOT_COUNT,
                "planned_record_slot_ids_sha256": f"sha256:{sha256_object(slot_ids)}",
                "contract_lock_status": "draft_required",
                "case_units": [
                    {
                        "case_unit_id": task_id,
                        "task_id": task_id,
                        "dataset_name": str(items_by_id[task_id]["dataset_name"]),
                        "split": str(items_by_id[task_id]["dataset_name"]),
                        "source_ref": str(items_by_id[task_id]["source_ref"]),
                        "contract_lock_status": "draft_required",
                    }
                    for task_id in extension_ids
                ],
            }
        ],
        "agents": [
            {
                "agent_id": agent_id,
                "config_sha256": agents_lock["per_agent"][agent_id]["config_sha256"],
                "provider": agents_lock["per_agent"][agent_id]["config"]["provider"],
                "model": agents_lock["per_agent"][agent_id]["config"]["model"],
                "model_version": agents_lock["per_agent"][agent_id]["config"]["model_version"],
            }
            for agent_id in AGENT_IDS
        ],
    }
    return {
        "normal_extension_ids": normal_extension_text,
        "challenge_ids": challenge_text,
        "extension_ids": extension_text,
        "catalog": catalog,
        "scope": scope,
        "manifest": manifest,
    }


def _source_item(tasks_root: Path, dataset_name: str, task_id: str) -> tuple[dict[str, Any], list[str], int]:
    task_dir = tasks_root / task_id
    _require(task_dir.is_dir(), f"AppWorld task directory is missing: {task_dir}")
    _require(not task_dir.is_symlink(), f"AppWorld task directory must not be a symlink: {task_dir}")
    actual_files = sorted(path.relative_to(task_dir).as_posix() for path in task_dir.rglob("*") if path.is_file())
    _require(
        len(actual_files) == len(REQUIRED_TASK_FILES) and set(actual_files) == set(REQUIRED_TASK_FILES),
        f"AppWorld task {task_id} does not have the exact 19-file inventory",
    )
    symlinks = sorted(path.relative_to(task_dir).as_posix() for path in task_dir.rglob("*") if path.is_symlink())
    _require(not symlinks, f"AppWorld task {task_id} contains symlinks: {symlinks[:5]}")
    source_ref = f"appworld://{dataset_name}/{task_id}"
    files: dict[str, dict[str, Any]] = {}
    tree_lines: list[str] = []
    byte_count = 0
    tree_inventory: list[dict[str, Any]] = []
    for relative in actual_files:
        path = task_dir / relative
        _validate_structured_file(path, relative)
        digest = sha256_file(path)
        size = path.stat().st_size
        files[relative] = {
            "source_path": _repo_relative(path),
            "archive_path": f"official/{relative}",
            "sha256": f"sha256:{digest}",
            "size_bytes": size,
        }
        tree_lines.append(f"{task_id}\t{relative}\t{digest}\n")
        tree_inventory.append({"path": relative, "sha256": digest, "size_bytes": size})
        byte_count += size
    item: dict[str, Any] = {
        "case_unit_id": task_id,
        "task_id": task_id,
        "dataset_name": dataset_name,
        "split": dataset_name,
        "source_ref": source_ref,
        "task_dir": _repo_relative(task_dir),
        "materialization": "copy_local_task_directory",
        "file_count": len(files),
        "byte_count": byte_count,
        "task_tree_sha256": f"sha256:{sha256_object(tree_inventory)}",
        "files": files,
    }
    item["source_item_sha256"] = f"sha256:{sha256_object(item)}"
    return item, tree_lines, byte_count


def _read_split_ids(
    path: Path,
    dataset_name: str,
    expected_count: int,
    expected_sha256: str,
) -> list[str]:
    _require(path.is_file(), f"AppWorld split file missing: {path}")
    actual_sha256 = sha256_file(path)
    _require(
        actual_sha256 == expected_sha256,
        f"{dataset_name} canonical AppWorld {APPWORLD_DATA_VERSION} split hash mismatch: "
        f"expected={expected_sha256}, actual={actual_sha256}",
    )
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    _require(all(line.strip() for line in raw_lines), f"{dataset_name} split contains blank lines")
    ids = [line.strip() for line in raw_lines]
    _require(len(ids) == expected_count, f"{dataset_name} count mismatch: expected={expected_count}, actual={len(ids)}")
    _require(len(set(ids)) == len(ids), f"{dataset_name} contains duplicate task IDs")
    invalid = [task_id for task_id in ids if TASK_ID_PATTERN.fullmatch(task_id) is None]
    _require(not invalid, f"{dataset_name} contains invalid task IDs: {invalid[:5]}")
    return ids


def _read_current_selected_ids(path: Path) -> list[str]:
    actual_sha256 = sha256_file(path)
    _require(
        actual_sha256 == CANONICAL_SELECTED_100_CATALOG_SHA256,
        "selected-100 catalog hash does not match the frozen main-study cohort",
    )
    payload = _load_mapping(path, "current AppWorld selected catalog")
    items = payload.get("items")
    _require(isinstance(items, list) and len(items) == EXPECTED_CURRENT_COUNT, "current AppWorld catalog must contain 100 items")
    _require(payload.get("selected_count") == EXPECTED_CURRENT_COUNT, "current AppWorld selected_count mismatch")
    ids: list[str] = []
    for index, item in enumerate(items):
        _require(isinstance(item, Mapping), f"current AppWorld catalog item {index} must be a mapping")
        task_id = str(item.get("task_id") or "")
        _require(item.get("source_ref") == f"appworld://test_normal/{task_id}", f"current AppWorld source_ref mismatch for {task_id}")
        ids.append(task_id)
    _require(len(ids) == len(set(ids)) == EXPECTED_CURRENT_COUNT, "current AppWorld IDs are duplicated")
    return ids


def _appworld_provenance(data_version_path: Path, base_dbs_root: Path) -> dict[str, Any]:
    _require(data_version_path.is_file(), f"AppWorld data version file missing: {data_version_path}")
    actual_version = data_version_path.read_text(encoding="utf-8").strip()
    _require(actual_version == APPWORLD_DATA_VERSION, f"AppWorld data version mismatch: {actual_version!r}")
    snapshot_readme = resolve_repo_path(DEFAULT_SNAPSHOT_README)
    _require(snapshot_readme.is_file(), f"AppWorld snapshot README missing: {snapshot_readme}")
    _require(APPWORLD_GIT_COMMIT in snapshot_readme.read_text(encoding="utf-8"), "snapshot README does not record pinned AppWorld commit")
    install_log = resolve_repo_path(DEFAULT_INSTALL_LOG)
    _require(install_log.is_file(), f"AppWorld install log missing: {install_log}")
    _require(f'"package_version": "{APPWORLD_PACKAGE_VERSION}"' in install_log.read_text(encoding="utf-8"), "install log does not record pinned AppWorld package version")
    _require(base_dbs_root.is_dir(), f"AppWorld base DB directory missing: {base_dbs_root}")
    return {
        "repository_url": APPWORLD_REPOSITORY_URL,
        "git_commit": APPWORLD_GIT_COMMIT,
        "git_commit_evidence_path": _repo_relative(snapshot_readme),
        "git_commit_evidence_sha256": f"sha256:{sha256_file(snapshot_readme)}",
        "package_version": APPWORLD_PACKAGE_VERSION,
        "package_version_evidence_path": _repo_relative(install_log),
        "package_version_evidence_sha256": f"sha256:{sha256_file(install_log)}",
        "data_version": APPWORLD_DATA_VERSION,
        "data_version_path": _repo_relative(data_version_path),
        "data_version_sha256": f"sha256:{sha256_file(data_version_path)}",
        "base_dbs_root": _repo_relative(base_dbs_root),
        "base_dbs_tree_sha256": f"sha256:{sha256_path(base_dbs_root)}",
    }


def _agents_lock(path: Path) -> dict[str, Any]:
    payload = _load_mapping(path, "agents config")
    agents = payload.get("experimental_agents")
    _require(isinstance(agents, Mapping), "agents config requires experimental_agents mapping")
    agent_map = payload.get("main_domain_agent_map")
    _require(isinstance(agent_map, Mapping) and list(agent_map.get("appworld") or []) == list(AGENT_IDS), "AppWorld agent map must be Agent A/B/C")
    per_agent: dict[str, Any] = {}
    for agent_id in AGENT_IDS:
        config = agents.get(agent_id)
        _require(isinstance(config, Mapping), f"agents config is missing {agent_id}")
        _require(config.get("retry") == 2, f"{agent_id} retry must remain 2")
        per_agent[agent_id] = {
            "config": dict(config),
            "config_sha256": f"sha256:{sha256_object(config)}",
        }
    return {
        "agents_config_path": _repo_relative(path),
        "agents_config_sha256": f"sha256:{sha256_file(path)}",
        "agent_ids": list(AGENT_IDS),
        "per_agent": per_agent,
    }


def _drafter_lock(agents_path: Path, current_ids: Sequence[str]) -> dict[str, Any]:
    """Resolve and verify the drafting protocol without treating placeholders as locks."""

    payload = _load_mapping(agents_path, "agents config")
    source_config = payload.get("contract_drafter")
    _require(isinstance(source_config, Mapping), "agents config requires contract_drafter mapping")
    for field, expected in (
        ("provider", "openrouter"),
        ("model", "openai/gpt-5.4"),
        ("model_version", "openai/gpt-5.4-20260305"),
        ("temperature", 0),
        ("retry", 2),
    ):
        _require(source_config.get(field) == expected, f"contract drafter source config {field} drift")
    input_policy = source_config.get("input_policy")
    _require(isinstance(input_policy, Mapping), "contract drafter source config requires input_policy")
    prompt = resolve_repo_path(DEFAULT_DRAFT_PROMPT)
    schema = resolve_repo_path(DEFAULT_DRAFT_SCHEMA)
    draft_script = resolve_repo_path(DEFAULT_DRAFT_SCRIPT)
    batch_script = resolve_repo_path(DEFAULT_DRAFT_BATCH_SCRIPT)
    template = resolve_repo_path(DEFAULT_DRAFT_TEMPLATE)
    guardrails = resolve_repo_path(DEFAULT_DRAFT_GUARDRAILS)
    for label, path in (
        ("draft prompt", prompt),
        ("draft schema", schema),
        ("draft script", draft_script),
        ("draft batch script", batch_script),
        ("draft template", template),
        ("draft guardrails", guardrails),
    ):
        _require(path.is_file(), f"{label} is missing: {path}")

    protocol = {
        "provider": "openrouter",
        "credential_env_preference": ["OPENROUTER_DRAFT_API_KEY", "OPENROUTER_API_KEY"],
        "model": "openai/gpt-5.4",
        "model_version": "openai/gpt-5.4-20260305",
        "reasoning_effort": "high",
        "service_tier": "default",
        "temperature": 0.0,
        "max_output_token_budgets": [12_000, 16_000, 20_000],
        "retry_rule": "advance to the next token budget only after a failed or schema-invalid attempt",
        "regular_http_timeout_seconds": 180,
        "oversized_http_timeout_seconds": 480,
        "oversized_threshold_bytes": 100_000,
        "regular_max_parallel": 8,
        "oversized_max_parallel": 2,
        "prompt_path": _repo_relative(prompt),
        "prompt_sha256": f"sha256:{sha256_file(prompt)}",
        "schema_path": _repo_relative(schema),
        "schema_sha256": f"sha256:{sha256_file(schema)}",
        "output_schema_version": "contract/v1",
        "input_policy": dict(input_policy),
        "draft_script_path": _repo_relative(draft_script),
        "draft_script_sha256": f"sha256:{sha256_file(draft_script)}",
        "batch_script_path": _repo_relative(batch_script),
        "batch_script_sha256": f"sha256:{sha256_file(batch_script)}",
        "template_path": _repo_relative(template),
        "template_sha256": f"sha256:{sha256_file(template)}",
        "guardrails_path": _repo_relative(guardrails),
        "guardrails_sha256": f"sha256:{sha256_file(guardrails)}",
    }

    existing_root = resolve_repo_path(DEFAULT_EXISTING_DRAFT_ROOT)
    _require(existing_root.is_dir(), f"existing AppWorld draft package is missing: {existing_root}")
    calls = {path.parents[1].name: path for path in existing_root.glob("*/draft/llm_call.json")}
    responses = {path.parents[1].name: path for path in existing_root.glob("*/draft/api_response.json")}
    expected_id_set = set(current_ids)
    _require(
        set(calls) == set(responses) == expected_id_set and len(calls) == EXPECTED_CURRENT_COUNT,
        "existing AppWorld final draft evidence must cover exactly the selected 100 cases",
    )
    evidence_index: list[dict[str, Any]] = []
    for task_id in current_ids:
        call_path = calls[task_id]
        response_path = responses[task_id]
        call = _load_mapping(call_path, "existing AppWorld draft llm_call")
        response = _load_mapping(response_path, "existing AppWorld draft API response")
        metadata = call.get("response_metadata")
        _require(isinstance(metadata, Mapping), f"existing AppWorld draft {task_id} lacks response_metadata")
        for field, expected in (
            ("provider", protocol["provider"]),
            ("model", protocol["model"]),
            ("model_version", protocol["model_version"]),
            ("domain", "appworld"),
            ("case_unit_id", task_id),
            ("task_id", task_id),
            ("phase", "draft"),
            ("agent_id_or_role", "case_checklist_drafter"),
            ("temperature", protocol["temperature"]),
        ):
            _require(call.get(field) == expected, f"existing AppWorld draft {task_id} {field} drift")
        _require(
            metadata.get("reasoning_effort") == protocol["reasoning_effort"]
            and metadata.get("service_tier") == protocol["service_tier"],
            f"existing AppWorld draft {task_id} reasoning/service-tier drift",
        )
        max_tokens = call.get("max_tokens")
        timeout_seconds = call.get("timeout_seconds")
        _require(max_tokens in protocol["max_output_token_budgets"], f"existing AppWorld draft {task_id} token budget drift")
        _require(
            timeout_seconds in {
                protocol["regular_http_timeout_seconds"],
                protocol["oversized_http_timeout_seconds"],
            },
            f"existing AppWorld draft {task_id} timeout drift",
        )
        response_reasoning = response.get("reasoning")
        _require(isinstance(response_reasoning, Mapping), f"existing AppWorld response {task_id} lacks reasoning config")
        for field, expected in (
            ("model", protocol["model_version"]),
            ("status", "completed"),
            ("max_output_tokens", max_tokens),
            ("temperature", protocol["temperature"]),
            ("service_tier", protocol["service_tier"]),
        ):
            _require(response.get(field) == expected, f"existing AppWorld response {task_id} {field} drift")
        _require(
            response_reasoning.get("effort") == protocol["reasoning_effort"],
            f"existing AppWorld response {task_id} reasoning effort drift",
        )
        evidence_index.append(
            {
                "task_id": task_id,
                "llm_call_path": _repo_relative(call_path),
                "llm_call_sha256": sha256_file(call_path),
                "api_response_path": _repo_relative(response_path),
                "api_response_sha256": sha256_file(response_path),
                "final_max_output_tokens": max_tokens,
                "final_timeout_seconds": timeout_seconds,
            }
        )

    return {
        "resolution_rule": (
            "the explicit resolved_config is authoritative; source prompt placeholders and the generic max_tokens field are not"
        ),
        "source_agents_config_path": _repo_relative(agents_path),
        "source_agents_config_sha256": f"sha256:{sha256_file(agents_path)}",
        "source_contract_drafter_config_sha256": f"sha256:{sha256_object(source_config)}",
        "non_effective_source_fields": ["prompt_hash", "prompt_version", "max_tokens", "timeout_seconds"],
        "resolved_config": protocol,
        "config_sha256": f"sha256:{sha256_object(protocol)}",
        "existing_selected_100_evidence_root": _repo_relative(existing_root),
        "existing_selected_100_evidence_count": len(evidence_index),
        "existing_selected_100_evidence_index_sha256": f"sha256:{sha256_object(evidence_index)}",
    }


def _scorer_lock(current_ids: Sequence[str]) -> dict[str, Any]:
    prompt = resolve_repo_path(DEFAULT_SCORE_PROMPT)
    schema = resolve_repo_path(DEFAULT_SCORE_SCHEMA)
    prompt_sha = sha256_file(prompt)
    schema_sha = sha256_file(schema)
    score_root = resolve_repo_path(DEFAULT_EXISTING_SCORE_ROOT)
    _require(score_root.is_dir(), f"existing AppWorld score package is missing: {score_root}")
    score_manifests = sorted(
        path for path in score_root.rglob("score_manifest.json") if path.parent.name == "codex-gpt-5.4-high"
    )
    _require(
        len(score_manifests) == EXPECTED_CURRENT_COUNT * EXPECTED_AGENT_COUNT,
        "existing AppWorld canonical gpt-5.4/high score manifest count must be 300",
    )
    score_manifest_index: list[dict[str, str]] = []
    seen_case_agents: set[tuple[str, str]] = set()
    expected_case_agents = {(task_id, agent_id) for task_id in current_ids for agent_id in AGENT_IDS}
    for path in score_manifests:
        relative_parts = path.relative_to(score_root).parts
        _require(
            len(relative_parts) == 7
            and relative_parts[0] == "cases"
            and relative_parts[2] == "score_runs"
            and relative_parts[5] == "codex-gpt-5.4-high"
            and relative_parts[6] == "score_manifest.json",
            f"unexpected score manifest location: {path}",
        )
        path_task_id = relative_parts[1]
        path_run_dir = relative_parts[3]
        checklist_bucket = relative_parts[4]
        payload = _load_mapping(path, "existing AppWorld score manifest")
        for field, expected in (
            ("schema_version", "score_manifest_v1"),
            ("case_unit_id", path_task_id),
            ("phase", "full"),
            ("domain", "appworld"),
            ("run_dir_name", path_run_dir),
            ("contract_id", f"full-appworld-{path_task_id}"),
            ("model", "gpt-5.4"),
            ("reasoning_effort", "high"),
            ("service_tier", "fast"),
            ("score_prompt_sha256", prompt_sha),
            ("score_schema_sha256", schema_sha),
        ):
            _require(payload.get(field) == expected, f"existing AppWorld score manifest {path} has {field} drift")
        agent_id = str(payload.get("agent_id") or "")
        agent_slug = agent_id.lower().replace(" ", "_")
        expected_run_dir = f"full-appworld-{path_task_id}-{agent_slug}"
        _require(agent_id in AGENT_IDS, f"existing AppWorld score manifest {path} has invalid agent_id")
        _require(path_run_dir == expected_run_dir, f"existing AppWorld score manifest {path} run directory drift")
        _require(
            payload.get("run_id") == f"run-appworld-{path_task_id}-{agent_slug}",
            f"existing AppWorld score manifest {path} run_id drift",
        )
        checklist_sha = str(payload.get("checklist_sha256") or "")
        _require(
            SHA256_PATTERN.fullmatch(checklist_sha) is not None
            and checklist_bucket == f"{path_task_id}__chk_{checklist_sha[:8]}",
            f"existing AppWorld score manifest {path} checklist bucket drift",
        )
        case_agent = (path_task_id, agent_id)
        _require(case_agent not in seen_case_agents, f"duplicate AppWorld score case-agent pair: {case_agent}")
        seen_case_agents.add(case_agent)
        score_path = path.with_name("score.json")
        _require(score_path.is_file() and not score_path.is_symlink(), f"existing AppWorld score output missing: {score_path}")
        score = _load_mapping(score_path, "existing AppWorld score output")
        _require(
            score.get("schema_version") == "evidence_score_v1" and score.get("case_unit_id") == path_task_id,
            f"existing AppWorld score output identity drift: {score_path}",
        )
        score_manifest_index.append(
            {
                "case_unit_id": path_task_id,
                "agent_id": agent_id,
                "manifest_path": _repo_relative(path),
                "manifest_sha256": sha256_file(path),
                "score_path": _repo_relative(score_path),
                "score_sha256": sha256_file(score_path),
            }
        )
    _require(seen_case_agents == expected_case_agents, "existing AppWorld scores are not the exact selected-100 x Agent A/B/C cartesian set")
    protocol = {
        "executor": "codex",
        "model": "gpt-5.4",
        "reasoning_effort": "high",
        "service_tier": "fast",
        "score_prompt_path": _repo_relative(prompt),
        "score_prompt_sha256": f"sha256:{prompt_sha}",
        "score_schema_path": _repo_relative(schema),
        "score_schema_sha256": f"sha256:{schema_sha}",
        "existing_score_manifest_root": _repo_relative(score_root),
        "existing_score_manifest_selection": "*/codex-gpt-5.4-high/score_manifest.json",
        "existing_score_manifest_count": len(score_manifests),
        "existing_score_case_agent_count": len(seen_case_agents),
        "existing_score_output_count": len(score_manifest_index),
        "existing_score_manifest_index_sha256": f"sha256:{sha256_object(score_manifest_index)}",
    }
    return {**protocol, "config_sha256": f"sha256:{sha256_object(protocol)}"}


def _legacy_lock(current_catalog: Path) -> dict[str, Any]:
    paths = {
        "selected_catalog": current_catalog,
        "main_manifest": resolve_repo_path(DEFAULT_EXISTING_MANIFEST),
        "main_source_bundle": resolve_repo_path(DEFAULT_EXISTING_SOURCE_BUNDLE),
    }
    lock: dict[str, Any] = {
        name: {"path": _repo_relative(path), "sha256": f"sha256:{sha256_file(path)}"}
        for name, path in paths.items()
    }
    packets = resolve_repo_path(DEFAULT_EXISTING_PACKETS)
    _require(packets.is_dir(), f"existing AppWorld packet root missing: {packets}")
    packet_dirs = [path for path in packets.iterdir() if path.is_dir()]
    _require(len(packet_dirs) == EXPECTED_CURRENT_COUNT, "existing AppWorld packet root is not exactly 100 cases")
    lock["case_packets"] = {
        "path": _repo_relative(packets),
        "case_count": EXPECTED_CURRENT_COUNT,
        "tree_sha256": f"sha256:{sha256_path(packets)}",
    }
    lock["rule"] = "all listed legacy artifacts are read-only inputs and must retain these hashes"
    return lock


def _catalog_items(catalog: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    raw_items = catalog.get("items")
    _require(isinstance(raw_items, list) and len(raw_items) == EXPECTED_EXTENSION_COUNT, "extension catalog item count mismatch")
    items: dict[str, Mapping[str, Any]] = {}
    for index, item in enumerate(raw_items):
        _require(isinstance(item, Mapping), f"catalog item {index} must be a mapping")
        task_id = str(item.get("task_id") or "")
        _require(task_id and task_id not in items, f"catalog has missing/duplicate task ID: {task_id!r}")
        items[task_id] = item
    return items


def _manifest_cases(manifest: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    domains = manifest.get("domains")
    _require(isinstance(domains, list) and len(domains) == 1 and isinstance(domains[0], Mapping), "extension manifest must have one domain")
    block = domains[0]
    _require(block.get("domain") == "appworld", "extension manifest domain must be appworld")
    cases = block.get("case_units")
    _require(isinstance(cases, list) and len(cases) == EXPECTED_EXTENSION_COUNT, "extension manifest case list mismatch")
    return cases


def _validate_structured_file(path: Path, relative: str) -> None:
    try:
        if relative.endswith(".json"):
            json.loads(path.read_text(encoding="utf-8"))
        elif relative.endswith(".jsonl"):
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if line.strip():
                    try:
                        json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ContractLifecycleError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
        elif relative == "ground_truth/evaluation.py":
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, SyntaxError) as exc:
        raise ContractLifecycleError(f"invalid AppWorld source file {path}: {exc}") from exc


def _output_paths(output_root: str | Path) -> dict[str, Path]:
    root = resolve_repo_path(output_root)
    return {
        "catalog": root / "official_splits/appworld_selected_task_sources.json",
        "normal_extension_ids": root / "official_splits/appworld_test_normal_extension.txt",
        "challenge_ids": root / "official_splits/appworld_test_challenge.txt",
        "extension_ids": root / "official_splits/appworld_extension_all.txt",
        "scope": root / "frozen_scope.json",
        "manifest": root / "experiment_manifest.json",
    }


def _validate_build_path_isolation(
    *,
    output_root: str | Path,
    normal_split_path: str | Path,
    challenge_split_path: str | Path,
    current_catalog_path: str | Path,
    tasks_root: str | Path,
    data_version_path: str | Path,
    base_dbs_root: str | Path,
    agents_config_path: str | Path,
) -> None:
    """Reject every input/output overlap before the first extension write."""

    output = resolve_repo_path(output_root).resolve()
    protected_inputs = {
        "normal split": normal_split_path,
        "challenge split": challenge_split_path,
        "selected-100 catalog": current_catalog_path,
        "AppWorld tasks root": tasks_root,
        "AppWorld data-version file": data_version_path,
        "AppWorld base DB root": base_dbs_root,
        "agents config": agents_config_path,
        "snapshot README": DEFAULT_SNAPSHOT_README,
        "install log": DEFAULT_INSTALL_LOG,
        "draft prompt": DEFAULT_DRAFT_PROMPT,
        "draft schema": DEFAULT_DRAFT_SCHEMA,
        "draft script": DEFAULT_DRAFT_SCRIPT,
        "draft batch script": DEFAULT_DRAFT_BATCH_SCRIPT,
        "draft template": DEFAULT_DRAFT_TEMPLATE,
        "draft guardrails": DEFAULT_DRAFT_GUARDRAILS,
        "score prompt": DEFAULT_SCORE_PROMPT,
        "score schema": DEFAULT_SCORE_SCHEMA,
        "selected-100 score/draft package": DEFAULT_EXISTING_SCORE_ROOT,
        "selected-100 packet root": DEFAULT_EXISTING_PACKETS,
        "selected-100 source bundle": DEFAULT_EXISTING_SOURCE_BUNDLE,
        "main experiment manifest": DEFAULT_EXISTING_MANIFEST,
    }
    for label, raw_path in protected_inputs.items():
        protected = resolve_repo_path(raw_path).resolve()
        if _paths_overlap(output, protected):
            raise ContractLifecycleError(
                f"extension output root must be disjoint from {label}: output={output}, protected={protected}"
            )


def _paths_overlap(first: Path, second: Path) -> bool:
    return first == second or first in second.parents or second in first.parents


def _tree_line_digest(lines: Sequence[str]) -> str:
    return hashlib.sha256("".join(sorted(lines)).encode("utf-8")).hexdigest()


def _id_text(ids: Sequence[str]) -> str:
    return "".join(f"{task_id}\n" for task_id in ids)


def _load_mapping(path: str | Path, label: str) -> dict[str, Any]:
    resolved = resolve_repo_path(path)
    _require(resolved.is_file(), f"{label} is missing: {resolved}")
    payload = load_json_or_yaml(resolved)
    _require(isinstance(payload, Mapping), f"{label} must be a mapping")
    return dict(payload)


def _json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_json_atomic(path: Path, payload: Any) -> None:
    _write_bytes_atomic(path, _json_bytes(payload))


def _write_text_atomic(path: Path, text: str) -> None:
    _write_bytes_atomic(path, text.encode("utf-8"))


def _write_bytes_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(data)
    try:
        temporary.replace(path)
        path.chmod(0o644)
    finally:
        temporary.unlink(missing_ok=True)


def _repo_relative(path: str | Path) -> str:
    resolved = resolve_repo_path(path).resolve()
    root = resolve_repo_path(".").resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise ContractLifecycleError(f"AppWorld extension artifacts must stay inside the repository: {resolved}") from exc


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractLifecycleError(message)
