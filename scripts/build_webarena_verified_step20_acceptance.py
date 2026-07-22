#!/usr/bin/env python3
"""Build the fail-closed aggregate acceptance receipt for WebArena Step 20.

The historical receipt covered only the frozen environment, official scorer,
and 812 source-rich packets.  This builder keeps those expensive validations,
then aggregates the operational gates needed before either the paid pilot or
the 2,436-slot full run may start.  Missing evidence remains pending/blocked;
machine-generated contracts never stand in for human source-check signoff.  A
separately hash-bound operator waiver can waive that requirement while keeping
``human_signed=0`` and must never be reported as human approval.

The builder never reads ``.env`` and never records credential values.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import re
import sys
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evidence_system.adapters import webarena_official_worker  # noqa: E402
from evidence_system.adapters import webarena_verified_official_scorer  # noqa: E402
from evidence_system.contracts import webarena_native  # noqa: E402
from evidence_system.core.hashing import sha256_object as core_sha256_object  # noqa: E402
from evidence_system.orchestrator import webarena_verified_full  # noqa: E402
from evidence_system.orchestrator import webarena_verified_machine_preview  # noqa: E402
from evidence_system.orchestrator import webarena_verified_run_control  # noqa: E402
from evidence_system.webarena_openrouter_credential import (  # noqa: E402
    CredentialAcceptanceError,
    REQUIRED_MODELS as OPENROUTER_REQUIRED_MODELS,
    validate_openrouter_credential_acceptance_file,
)
from neurips_ed_track_minimal.checklist_guardrails import (  # noqa: E402
    ChecklistGuardrailError,
    case_packet_support_paths,
)
from neurips_ed_track_minimal.scripts.draft_case_checklist import (  # noqa: E402
    DraftChecklistError,
    extract_case_metadata,
)

RECEIPTS_DIR = (
    ROOT / "experiments" / "step20" / "webarena_verified" / "environment_receipts"
)
PACKETS_ROOT = ROOT / "experiments" / "case_packets" / "webarena_verified"
OFFICIAL_INPUTS = (
    ROOT
    / "experiments"
    / "official_splits"
    / "webarena_verified_agent_inputs_full_812.json"
)
OFFICIAL_SOURCE = (
    ROOT / "experiments" / "official_splits" / "webarena_verified_official_812.json"
)
OFFICIAL_SOURCE_SNAPSHOT = (
    ROOT
    / "experiments"
    / "official_splits"
    / "webarena_verified_v1_2_3_source"
)
OFFICIAL_TAG_SOURCE = (
    OFFICIAL_SOURCE_SNAPSHOT / "assets" / "dataset" / "webarena-verified.json"
)
FROZEN_MANIFEST = (
    ROOT / "experiments" / "step19" / "webarena_verified_full_812_manifest.json"
)
DEFAULT_SOURCE_BUNDLE = (
    ROOT
    / "experiments"
    / "evidence_contracts"
    / "source_bundles"
    / "webarena_verified_full_812_source_bundle.json"
)
DEFAULT_OUTPUT = (
    ROOT / "experiments" / "step20" / "webarena_verified" / "acceptance.json"
)
STEP20_ROOT = ROOT / "experiments" / "step20" / "webarena_verified"
INFRA_CONFIG = ROOT / "configs" / "infra.yaml"
NATIVE_CLAIM_ACCEPTANCE = STEP20_ROOT / "native_claims" / "acceptance.json"
NATIVE_CLAIM_ROOT = STEP20_ROOT / "native_claims"
NATIVE_CLAIM_COMPILER_RETIREMENT = (
    STEP20_ROOT / "native_claim_compiler_retirement.json"
)
OPERATOR_WAIVER = STEP20_ROOT / "operator_waiver.json"
MACHINE_PREVIEW_ACCEPTANCE = STEP20_ROOT / "machine_preview_schedule_acceptance.json"
MACHINE_PREVIEW_INDEX = STEP20_ROOT / "machine_preview_schedule_index.json"
FORMAL_SCHEDULER_ACCEPTANCE = STEP20_ROOT / "full_scheduler_dry_run_acceptance.json"
FORMAL_SCHEDULER_JOBS_ROOT = STEP20_ROOT / "jobs" / "full"
FORMAL_RUN_CONTROL_ACCEPTANCE = STEP20_ROOT / "full_run_control_acceptance.json"
GOLDEN_PARITY_ACCEPTANCE = STEP20_ROOT / "golden_parity" / "acceptance.json"
RESET_SMOKE_ACCEPTANCE = (
    STEP20_ROOT / "environment_receipts" / "real_reset_smoke_acceptance.json"
)
EXTENDED_RESET_ACCEPTANCE = (
    STEP20_ROOT / "environment_receipts" / "extended_real_reset_acceptance.json"
)
SITE_DATA_LOCK_ACCEPTANCE = (
    STEP20_ROOT / "environment_receipts" / "site_data_lock_acceptance.json"
)
SITE_DEPLOYMENT_RECEIPTS = STEP20_ROOT / "environment_receipts" / "site_deployment"
BROWSER_ACCEPTANCE_ROOT = (
    STEP20_ROOT / "environment_receipts" / "browser_acceptance"
)
BROWSER_ACCEPTANCE = BROWSER_ACCEPTANCE_ROOT / "acceptance.json"
BROWSER_ARTIFACT_ROOT = ROOT / "output" / "playwright" / "webarena_verified"
HUMAN_REVIEW_ACCEPTANCE = (
    STEP20_ROOT / "native_claims" / "human_review" / "acceptance.json"
)
PILOT_MANIFEST = STEP20_ROOT / "pilot_manifest.json"
PILOT_ACCEPTANCE = STEP20_ROOT / "pilot_acceptance.json"
LOCAL_FAULT_ACCEPTANCE = (
    STEP20_ROOT / "fault_injection" / "local_harness_acceptance.json"
)
FAULT_ACCEPTANCE = (
    STEP20_ROOT / "fault_injection" / "remote_three_host_acceptance.json"
)
FAULT_POSTFLIGHT = (
    STEP20_ROOT / "fault_injection" / "remote_three_host_postflight.json"
)
FAULT_EXECUTION_PLAN = STEP20_ROOT / "fault_injection" / "remote_execution_plan.json"
PILOT_BUDGET_ACCEPTANCE = STEP20_ROOT / "pilot_cost_runtime_storage_acceptance.json"
STORAGE_ACCEPTANCE = STEP20_ROOT / "storage_readiness_acceptance.json"
STORAGE_PROVISIONING_ACCEPTANCE = (
    STEP20_ROOT / "storage_provisioning" / "acceptance.json"
)
STORAGE_READONLY_AUDIT = (
    STEP20_ROOT / "storage_readonly_audit" / "acceptance.json"
)
CREDENTIAL_ACCEPTANCE = STEP20_ROOT / "openrouter_credential_acceptance.json"
PILOT_RESULT_ROOT = (
    ROOT
    / "results"
    / "namespaces"
    / "webarena_verified_v1_2_3_pilot_8x3"
)
LOCAL_DPKG_INVENTORY = (
    ROOT / "experiments" / "step20" / "webarena_verified" / "dpkg-package-inventory.tsv"
)
LOCAL_PYTHON_FREEZE = (
    ROOT / "experiments" / "step20" / "webarena_verified" / "requirements.freeze.txt"
)
LOCAL_RUNNER_FREEZE = (
    ROOT
    / "experiments"
    / "step20"
    / "webarena_verified"
    / "runner-requirements.freeze.txt"
)

EXPECTED_COMMIT = "6473f72db5dcefc97b5725b59e734504edc28a21"
EXPECTED_SOURCE_SHA256 = (
    "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
)
EXPECTED_AGENT_INPUTS_SHA256 = (
    "d125ad7cf9627d9b9151153eaba20ecd85451899a2e4b70ecdd46510d0775a8e"
)
EXPECTED_EVALUATOR_CHECKSUM = (
    "35c3385b1db4b3378657589f95f50defd4234bd36e5b93d44733fd561b01db4e"
)
EXPECTED_DATA_CHECKSUM = (
    "d65275660814663375028e9017e1f929e3c38321041b125795e2713b52243d30"
)
EXPECTED_IMAGE = (
    "ghcr.io/servicenow/webarena-verified@"
    "sha256:d2c3f81b615648a806e0b9c9fd392085a45ca719ea773a51976b59d23f7bd1b9"
)
EXPECTED_TASK_CONTRACT_INDEX_SHA256 = (
    "32b2eb76d2296286fae619f843e985feaf1b3eaf622d90d77133ffb580ab0d49"
)
EXPECTED_AGENT_INPUT_TREE_SHA256 = (
    "98f4f404cae6e794bd2fa1d0c152d43b7fa5d6ee5bffea143a0c9c39ddd4c975"
)
EXPECTED_AGENT_INPUT_TOTAL_BYTES = 235617
EXPECTED_RUNNER_COMMIT = "dce04686a56253aefba7b18a4fa0937cf1dc987b"
EXPECTED_RUNNER_TREE = "8feabebb86b035004a0a242f13c5ee7bd1f8c627"
EXPECTED_RUNNER_REQUIREMENTS_INPUT_SHA256 = (
    "9f3c386d771ae3d556795a15433a30774049ba5b27df006049d3bba4e9e6b2fe"
)
EXPECTED_RUNNER_REQUIREMENTS_LOCK_SHA256 = (
    "b1763680fe08f816345c271dbec467661f0aa9cfa9ade79c3694eea6e2b430b4"
)
EXPECTED_RUNNER_UPSTREAM_REQUIREMENTS_SHA256 = (
    "86db3ff7932398742f9d567a230592b2843704660ed2220748d26b59e4d06bf2"
)
EXPECTED_RUNNER_RAW_TASKS_SHA256 = (
    "7b50386fd69163dbc05d615d834df4c6ed2c35596e97a1b10d17451c02537652"
)
EXPECTED_BUNDLED_PROMPT_SHA256 = (
    "cf344fbc9cf72e5f7c26b203bebe5630b28986d91139e618ebf1ddc4697c77cb"
)
EXPECTED_RUNNER_FREEZE_SHA256 = (
    "8a8c82c9dbb98ceaf98331c890823c4e2c755a653e4aa43aece4d34c80b37055"
)
IDENTITY_FIELDS = {"server_id", "vps_address", "ssh_host_ed25519_fingerprint"}
AGENT_INPUT_FIELDS = {"intent", "intent_template_id", "sites", "start_urls", "task_id"}
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
SECRET_TEXT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "openrouter_api_key",
        re.compile(r"sk-or-v1-[A-Za-z0-9_-]{24,}"),
    ),
    (
        "openai_style_api_key",
        re.compile(r"sk-(?!or-v1-)(?:proj-)?[A-Za-z0-9_-]{32,}"),
    ),
    (
        "authorization_bearer_value",
        re.compile(
            r"(?i)\bauthorization\b\s*[:=]\s*[\"']?bearer\s+[A-Za-z0-9._~+/=-]{20,}"
        ),
    ),
    (
        "http_cookie_header_value",
        re.compile(r"(?im)^\s*(?:cookie|set-cookie)\s*:\s*\S.{7,}$"),
    ),
)
SENSITIVE_VALUE_KEYS = {
    "access_token",
    "api_key",
    "authorization",
    "cookie",
    "cookies",
    "extra_headers",
    "openrouter_api_key",
    "password",
    "passwd",
    "refresh_token",
    "secret",
    "session_token",
    "set-cookie",
    "storage_state",
}
GOLD_FIELD_TOKENS = {
    "answer_key",
    "eval",
    "evaluator",
    "expected",
    "expected_answer",
    "expected_response",
    "gold",
    "gold_answer",
    "golden_answer",
    "private_evaluator_payload",
    "raw_case",
    "reference_answer",
    "reference_response",
}
EXPECTED_INDEX_SCHEMA_VERSION = "webarena_verified_case_packet_index/v2"
EXPECTED_SOURCE_BUNDLE_SCHEMA_VERSION = "contract_source_bundle.v2"
EXPECTED_DERIVED_FILES = {"derived/task.json", "derived/tag_task.json"}
COMMON_OFFICIAL_PACKET_FILES = (
    "src/webarena_verified/api/internal/evaluator.py",
    "src/webarena_verified/core/evaluation/evaluators/base.py",
    "src/webarena_verified/core/evaluation/evaluators/agent_response_evaluator.py",
    "src/webarena_verified/core/evaluation/value_comparator.py",
    "src/webarena_verified/core/evaluation/value_normalizer.py",
    "src/webarena_verified/types/agent_response.py",
    "src/webarena_verified/types/eval.py",
    "src/webarena_verified/types/task.py",
)
NETWORK_EVENT_PACKET_FILES = (
    "src/webarena_verified/core/evaluation/evaluators/network_event_evaluator.py",
    "src/webarena_verified/types/tracing.py",
    "src/webarena_verified/core/utils/jsonpath_utils.py",
)
ALLOWED_EVALUATOR_NAMES = {"AgentResponseEvaluator", "NetworkEventEvaluator"}
OFFICIAL_EVALUATOR_SOURCE_HASHES = {
    "AgentResponseEvaluator": (
        "src/webarena_verified/core/evaluation/evaluators/agent_response_evaluator.py",
        "8ae2caf59c6fafecf4ec259ea67bf79d27f19c7fcbdc33a312cea730c4e54c31",
    ),
    "NetworkEventEvaluator": (
        "src/webarena_verified/core/evaluation/evaluators/network_event_evaluator.py",
        "74bc94874541192d18c6dd221f26599d5279606effc55cf5c059ddce2516c441",
    ),
    "TaskEvalResult": (
        "src/webarena_verified/types/eval.py",
        "f9c2a2aa4fcc839232f3cab88c9618b601c050e2d46b97630f96664257e95140",
    ),
}
EXPECTED_LICENSE_PATH = "official/LICENSE"
EXPECTED_RUNTIME_LIMITS = {
    "action_set": "id_accessibility_tree",
    "action_parse_retry_count_per_browser_step": 2,
    "case_wall_clock_timeout_enforced": False,
    "concurrency_per_server": 1,
    "maximum_model_http_attempts_per_browser_step": 9,
    "max_steps": 30,
    "model_request_timeout_seconds": 120,
    "observation_type": "accessibility_tree",
    "official_evaluator_timeout_seconds": 600,
    "reset_before_each_case_required": True,
    "reset_controller_implementation_status": "pending",
    "transport_retry_count_per_parse_attempt": 2,
    "viewport": {"height": 720, "width": 1280},
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise RuntimeError(f"path is outside the repository: {path}") from exc


def require_sha256(value: Any, label: str) -> str:
    require(
        isinstance(value, str) and SHA256_PATTERN.fullmatch(value) is not None,
        f"{label} must be a lowercase SHA-256 digest",
    )
    return str(value)


def require_safe_relative_path(value: Any, label: str) -> str:
    require(isinstance(value, str) and bool(value), f"{label} must be non-empty")
    require("\\" not in value, f"{label} must use POSIX separators")
    require(
        re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", value) is None,
        f"{label} must not be a URL",
    )
    path = PurePosixPath(value)
    require(not path.is_absolute(), f"{label} must be relative")
    require(
        path.as_posix() == value
        and bool(path.parts)
        and all(part not in {"", ".", ".."} for part in path.parts),
        f"{label} is not a normalized safe relative path: {value!r}",
    )
    return value


def require_string_list(value: Any, label: str) -> list[str]:
    require(isinstance(value, list), f"{label} must be a list")
    require(
        all(isinstance(item, str) and bool(item) for item in value),
        f"{label} must contain non-empty strings",
    )
    result = [str(item) for item in value]
    require(len(result) == len(set(result)), f"{label} contains duplicates")
    return result


def deterministic_json_bytes(value: Any) -> bytes:
    """Match the frozen per-case JSON representation used by the packet builder."""

    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def official_evaluator_snapshot_checksum() -> str:
    root = OFFICIAL_SOURCE_SNAPSHOT / "src" / "webarena_verified"
    files = sorted(root.rglob("*.py"))
    require(files, "official evaluator snapshot contains no Python sources")
    digest = hashlib.sha256()
    for path in files:
        require(path.is_file() and not path.is_symlink(), f"unsafe snapshot file: {path}")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def parse_source_inventory(markdown: str, *, task_id: int) -> list[str]:
    """Parse exactly the Source Inventory grammar consumed by minimal drafter."""

    require(
        markdown.splitlines().count("## Source Inventory") == 1,
        f"task {task_id}: packet must contain exactly one Source Inventory heading",
    )
    result: list[str] = []
    in_inventory = False
    for line in markdown.splitlines():
        if line == "## Source Inventory":
            in_inventory = True
            continue
        if in_inventory and line.startswith("## "):
            break
        if not in_inventory or not line.strip():
            continue
        match = re.fullmatch(r"- `([^`]+)`", line.strip())
        require(
            match is not None,
            f"task {task_id}: Source Inventory has a non-parser-compatible line: {line!r}",
        )
        result.append(
            require_safe_relative_path(
                match.group(1), f"task {task_id}: Source Inventory path"
            )
        )
    require(result, f"task {task_id}: Source Inventory is empty")
    require(
        len(result) == len(set(result)),
        f"task {task_id}: Source Inventory contains duplicate paths",
    )
    return result


def validate_drafter_packet(
    *,
    markdown_path: Path,
    raw_case_dir: Path,
    packet_files: Sequence[str],
    task_id: int,
) -> list[str]:
    markdown = markdown_path.read_text(encoding="utf-8")
    try:
        metadata = extract_case_metadata(markdown)
    except DraftChecklistError as exc:
        raise RuntimeError(
            f"task {task_id}: minimal drafter cannot parse packet metadata: {exc}"
        ) from exc
    require(
        metadata
        == {
            "domain": "webarena_verified",
            "case_unit_id": str(task_id),
            "task_id": str(task_id),
        },
        f"task {task_id}: drafter metadata mismatch",
    )
    for key, value in metadata.items():
        require(
            markdown.splitlines().count(f"- {key}: `{value}`") == 1,
            f"task {task_id}: packet must contain exactly one {key} metadata line",
        )
    inventory = parse_source_inventory(markdown, task_id=task_id)
    try:
        support_paths = case_packet_support_paths(markdown)
    except ChecklistGuardrailError as exc:
        raise RuntimeError(
            f"task {task_id}: minimal checklist guardrail cannot parse Source Inventory: {exc}"
        ) from exc
    require(
        support_paths == {"case_packet.md", *inventory},
        f"task {task_id}: minimal guardrail support-path parse mismatch",
    )
    require(
        inventory == list(packet_files),
        f"task {task_id}: Source Inventory must exactly equal manifest.packet_files",
    )
    require(
        "## Packet Source Files" in markdown,
        f"task {task_id}: packet does not embed its source files",
    )
    require(
        "## Raw Source Provenance" in markdown,
        f"task {task_id}: packet does not embed raw-source provenance",
    )
    for relative in inventory:
        source_path = raw_case_dir / relative
        require(
            markdown.count(f"### `{relative}`") == 1,
            f"task {task_id}: packet must render source {relative} exactly once",
        )
        try:
            source_text = source_path.read_text(encoding="utf-8").rstrip("\n")
        except UnicodeDecodeError as exc:
            raise RuntimeError(
                f"task {task_id}: packet source is not UTF-8 text: {relative}"
            ) from exc
        require(
            source_text and source_text in markdown,
            f"task {task_id}: packet does not embed exact bytes-as-text for {relative}",
        )
    return inventory


def validate_source_bundle(
    *,
    source_bundle_path: Path,
    packet_hashes_by_id: Mapping[int, Mapping[str, str]],
) -> dict[str, Any]:
    require(
        source_bundle_path.is_file() and not source_bundle_path.is_symlink(),
        f"source bundle is missing or symlinked: {source_bundle_path}",
    )
    bundle = load_json(source_bundle_path)
    require(isinstance(bundle, Mapping), "source bundle must be a mapping")
    require(
        bundle.get("schema_version") == EXPECTED_SOURCE_BUNDLE_SCHEMA_VERSION,
        "source bundle schema mismatch",
    )
    require(
        bundle.get("manifest_path") == repo_relative(FROZEN_MANIFEST),
        "source bundle manifest path mismatch",
    )
    if "manifest_sha256" in bundle:
        require(
            bundle.get("manifest_sha256") == sha256_file(FROZEN_MANIFEST),
            "source bundle manifest hash mismatch",
        )
    else:
        require(
            bundle.get("manifest_definition_sha256_scope")
            == "canonical_mapping_without_source_bundle_hash"
            and bundle.get("manifest_definition_excluded_fields")
            == ["source_bundle_hash"],
            "source bundle has no valid manifest provenance binding",
        )
        manifest_definition = load_json(FROZEN_MANIFEST)
        require(isinstance(manifest_definition, Mapping), "frozen manifest is invalid")
        manifest_definition = dict(manifest_definition)
        manifest_definition.pop("source_bundle_hash", None)
        require(
            bundle.get("manifest_definition_sha256")
            == sha256_bytes(canonical_bytes(manifest_definition)),
            "source bundle manifest-definition hash mismatch",
        )

    sources = bundle.get("sources")
    require(isinstance(sources, list), "source bundle requires a sources list")
    require(
        bundle.get("source_count") == 812 == len(sources),
        "source bundle count is not exactly 812",
    )
    require(
        all(isinstance(source, Mapping) for source in sources),
        "source bundle contains a non-object source",
    )
    source_ids = [str(source.get("case_unit_id") or "") for source in sources]
    require(
        source_ids == [str(task_id) for task_id in range(812)],
        "source bundle case order/set is not exactly 0..811",
    )
    contract_ids = [str(source.get("contract_id") or "") for source in sources]
    require(
        all(contract_ids) and len(set(contract_ids)) == 812,
        "source bundle contract IDs are missing or duplicated",
    )

    for task_id, source in enumerate(sources):
        require(
            source.get("domain") == "webarena_verified"
            and str(source.get("case_unit_id")) == str(task_id)
            and str(source.get("task_id")) == str(task_id),
            f"source bundle task {task_id}: identity mismatch",
        )
        draft_input = source.get("draft_input")
        require(
            isinstance(draft_input, Mapping),
            f"source bundle task {task_id}: draft_input is missing",
        )
        expected_paths = {
            "case_packet_path": repo_relative(
                PACKETS_ROOT / str(task_id) / "case_packet.md"
            ),
            "raw_case_manifest_path": repo_relative(
                PACKETS_ROOT / str(task_id) / "raw_case_manifest.json"
            ),
        }
        for field, expected_path in expected_paths.items():
            require_safe_relative_path(
                draft_input.get(field), f"source bundle task {task_id}: {field}"
            )
            require(
                draft_input.get(field) == expected_path,
                f"source bundle task {task_id}: {field} mismatch",
            )
        for field in ("case_packet_sha256", "raw_case_manifest_sha256"):
            require_sha256(
                draft_input.get(field), f"source bundle task {task_id}: {field}"
            )
        expected_hashes = packet_hashes_by_id[task_id]
        require(
            draft_input.get("case_packet_sha256")
            == expected_hashes["case_packet.md"],
            f"source bundle task {task_id}: stale case-packet hash",
        )
        require(
            draft_input.get("raw_case_manifest_sha256")
            == expected_hashes["raw_case_manifest.json"],
            f"source bundle task {task_id}: stale raw-manifest hash",
        )
        serialized_source = json.dumps(source, ensure_ascii=False, sort_keys=True)
        require(
            not Path(str(source.get("contract_id"))).is_absolute()
            and "sk-or-v1-" not in serialized_source.lower(),
            f"source bundle task {task_id}: unsafe absolute/secret content",
        )

    sidecar_path = source_bundle_path.with_name(source_bundle_path.name + ".sha256")
    require(
        sidecar_path.is_file()
        and not sidecar_path.is_symlink()
        and sidecar_path.read_text(encoding="utf-8")
        == f"{sha256_file(source_bundle_path)}  {source_bundle_path.name}\n",
        "source bundle SHA sidecar mismatch",
    )
    return {
        "path": repo_relative(source_bundle_path),
        "sha256": sha256_file(source_bundle_path),
        "source_count": 812,
        "contract_id_count": 812,
        "sidecar_verified": True,
    }


def validate_raw_case(
    *,
    task_id: int,
    case_dir: Path,
    markdown_path: Path,
    manifest: Mapping[str, Any],
    source_task: Mapping[str, Any],
    tag_task: Mapping[str, Any],
    evaluator_names: Sequence[str],
) -> dict[str, Any]:
    raw_case_dir = case_dir / "raw_case"
    require(
        raw_case_dir.is_dir() and not raw_case_dir.is_symlink(),
        f"task {task_id}: raw_case must be a real directory",
    )
    raw_tree = list(raw_case_dir.rglob("*"))
    require(
        not any(path.is_symlink() for path in raw_tree),
        f"task {task_id}: raw_case contains a symlink",
    )
    actual_raw_files = {
        path.relative_to(raw_case_dir).as_posix()
        for path in raw_tree
        if path.is_file()
    }

    require(
        manifest.get("domain") == "webarena_verified"
        and str(manifest.get("case_unit_id")) == str(task_id)
        and str(manifest.get("task_id")) == str(task_id),
        f"task {task_id}: raw manifest identity mismatch",
    )
    require(
        manifest.get("source_sha256") == EXPECTED_SOURCE_SHA256,
        f"task {task_id}: raw manifest normalized-source hash mismatch",
    )
    require(
        manifest.get("source_task_sha256")
        == sha256_bytes(canonical_bytes(source_task)),
        f"task {task_id}: raw manifest source-task hash mismatch",
    )
    source_refs = require_string_list(
        manifest.get("source_refs"), f"task {task_id}: source_refs"
    )
    require(
        all(not Path(ref.split("#", 1)[0]).is_absolute() for ref in source_refs),
        f"task {task_id}: source_refs contain a local absolute path",
    )
    copied_files = require_string_list(
        manifest.get("copied_files"), f"task {task_id}: copied_files"
    )
    official_files = require_string_list(
        manifest.get("official_files"), f"task {task_id}: official_files"
    )
    derived_files = require_string_list(
        manifest.get("derived_files"), f"task {task_id}: derived_files"
    )
    packet_files = require_string_list(
        manifest.get("packet_files"), f"task {task_id}: packet_files"
    )
    for label, values in (
        ("copied_files", copied_files),
        ("official_files", official_files),
        ("derived_files", derived_files),
        ("packet_files", packet_files),
    ):
        for relative in values:
            require_safe_relative_path(relative, f"task {task_id}: {label}")

    require(
        set(evaluator_names).issubset(ALLOWED_EVALUATOR_NAMES)
        and "AgentResponseEvaluator" in evaluator_names,
        f"task {task_id}: unsupported evaluator source selection",
    )
    selected_source_paths = list(COMMON_OFFICIAL_PACKET_FILES)
    if "NetworkEventEvaluator" in evaluator_names:
        selected_source_paths.extend(NETWORK_EVENT_PACKET_FILES)
    expected_evaluator_sources = {
        f"official/{relative}" for relative in selected_source_paths
    }
    expected_official_files = {EXPECTED_LICENSE_PATH, *expected_evaluator_sources}
    expected_raw_files = {*EXPECTED_DERIVED_FILES, *expected_official_files}
    expected_packet_files = {*EXPECTED_DERIVED_FILES, *expected_evaluator_sources}
    require(
        actual_raw_files == expected_raw_files,
        f"task {task_id}: raw_case file set mismatch",
    )
    require(
        copied_files == sorted(expected_raw_files),
        f"task {task_id}: copied_files is not the exact sorted raw_case inventory",
    )
    require(
        official_files == sorted(expected_official_files),
        f"task {task_id}: official_files mismatch",
    )
    require(
        derived_files == ["derived/task.json", "derived/tag_task.json"],
        f"task {task_id}: derived_files mismatch",
    )
    require(
        packet_files
        == [
            "derived/task.json",
            "derived/tag_task.json",
            *(f"official/{relative}" for relative in selected_source_paths),
        ],
        f"task {task_id}: packet_files must be the two task JSONs and selected evaluator sources",
    )
    require(
        EXPECTED_LICENSE_PATH not in packet_files,
        f"task {task_id}: LICENSE must be provenance-only, not drafter packet input",
    )

    hashes = manifest.get("sha256_per_file")
    require(
        isinstance(hashes, Mapping) and set(hashes) == expected_raw_files,
        f"task {task_id}: sha256_per_file must exactly cover raw_case",
    )
    file_sources = manifest.get("file_sources")
    require(
        isinstance(file_sources, Mapping)
        and set(file_sources) == expected_raw_files
        and all(
            isinstance(value, str)
            and bool(value)
            and not Path(value.split("#", 1)[0]).is_absolute()
            for value in file_sources.values()
        ),
        f"task {task_id}: file_sources must bind every raw file without local absolute paths",
    )
    for relative in sorted(expected_raw_files):
        declared_hash = require_sha256(
            hashes.get(relative), f"task {task_id}: sha256_per_file[{relative}]"
        )
        require(
            declared_hash == sha256_file(raw_case_dir / relative),
            f"task {task_id}: stale raw file hash for {relative}",
        )

    require(
        (raw_case_dir / "derived" / "task.json").read_bytes()
        == deterministic_json_bytes(source_task),
        f"task {task_id}: normalized source-rich task is not the exact official task",
    )
    require(
        (raw_case_dir / "derived" / "tag_task.json").read_bytes()
        == deterministic_json_bytes(tag_task),
        f"task {task_id}: tag source-rich task is not the exact v1.2.3 tag task",
    )
    for relative in sorted(expected_official_files):
        snapshot_path = OFFICIAL_SOURCE_SNAPSHOT / relative.removeprefix("official/")
        require(
            snapshot_path.is_file()
            and not snapshot_path.is_symlink()
            and (raw_case_dir / relative).read_bytes() == snapshot_path.read_bytes(),
            f"task {task_id}: official snapshot copy drift for {relative}",
        )

    validate_drafter_packet(
        markdown_path=markdown_path,
        raw_case_dir=raw_case_dir,
        packet_files=packet_files,
        task_id=task_id,
    )
    require(
        manifest.get("schema_version") == "webarena_verified_raw_case_manifest/v2"
        and manifest.get("model_visible_files") == ["agent_input.json"]
        and manifest.get("drafter_reviewer_only_files")
        == ["case_packet.md", "raw_case_manifest.json", "raw_case/**"]
        and manifest.get("controller_runtime_files") == ["case_packet.json"],
        f"task {task_id}: raw manifest visibility boundary mismatch",
    )
    require(
        manifest.get("benchmark_version") == "v1.2.3"
        and manifest.get("official_commit") == EXPECTED_COMMIT
        and manifest.get("normalized_source_sha256") == EXPECTED_SOURCE_SHA256
        and manifest.get("official_tag_dataset_sha256") == EXPECTED_DATA_CHECKSUM
        and manifest.get("official_tag_task_canonical_sha256")
        == sha256_bytes(canonical_bytes(tag_task))
        and manifest.get("official_evaluator_checksum")
        == EXPECTED_EVALUATOR_CHECKSUM,
        f"task {task_id}: raw manifest frozen provenance mismatch",
    )
    require(
        manifest.get("evaluator_names_in_order")
        == [str(item["evaluator"]) for item in source_task.get("eval") or []]
        and manifest.get("task_score_composition")
        == "all_evaluator_scores_must_equal_1.0"
        and manifest.get("required_run_artifacts")
        == ["agent_response.json", "network.har"],
        f"task {task_id}: raw manifest evaluator semantics mismatch",
    )
    require(
        manifest.get("top_level_file_sha256")
        == {
            "agent_input.json": sha256_file(case_dir / "agent_input.json"),
            "case_packet.json": sha256_file(case_dir / "case_packet.json"),
        },
        f"task {task_id}: raw manifest top-level hash binding mismatch",
    )
    raw_tree_digest = hashlib.sha256()
    raw_case_total_bytes = 0
    for relative in sorted(expected_raw_files):
        path = raw_case_dir / relative
        size = path.stat().st_size
        raw_case_total_bytes += size
        raw_tree_digest.update(
            f"{relative}\t{sha256_file(path)}\t{size}\n".encode("utf-8")
        )
    return {
        "raw_case_file_count": len(expected_raw_files),
        "raw_case_total_bytes": raw_case_total_bytes,
        "raw_case_tree_sha256": raw_tree_digest.hexdigest(),
        "packet_source_file_count": len(expected_packet_files),
    }


def expected_servers() -> dict[str, dict[str, Any]]:
    payload = load_json(FROZEN_MANIFEST)
    servers = list(payload.get("servers") or [])
    require(len(servers) == 3, "infra lock must contain exactly three servers")
    result: dict[str, dict[str, Any]] = {}
    for server in servers:
        host = str(server["host"])
        require(host not in result, f"duplicate VPS address in infra lock: {host}")
        result[host] = {
            "server_id": str(server["server_id"]),
            "model": str(server["model"]),
            "ssh_host_ed25519_fingerprint": str(server["ssh_ed25519_fingerprint"]),
        }
    return result


def validate_receipts() -> dict[str, Any]:
    expected = expected_servers()
    # This directory also contains derived acceptance reports (for example the
    # real-reset smoke matrix).  Environment receipts are identity-bound by VPS
    # address, so select the three exact locked filenames instead of treating
    # every JSON report in the directory as an environment receipt.
    receipt_paths = {host: RECEIPTS_DIR / f"{host}.json" for host in expected}
    require(
        all(path.is_file() for path in receipt_paths.values()),
        "environment receipts must match the three locked VPS addresses",
    )
    normalized_hashes: set[str] = set()
    evidence: list[dict[str, Any]] = []
    for host in sorted(expected):
        path = receipt_paths[host]
        receipt = load_json(path)
        identity = expected[host]
        require(
            receipt.get("schema_version")
            == "webarena_verified_step20_environment_receipt/v3",
            f"{host}: receipt schema mismatch",
        )
        require(
            receipt.get("status") == "verified", f"{host}: environment is not verified"
        )
        require(receipt.get("vps_address") == host, f"{host}: receipt address mismatch")
        require(
            receipt.get("server_id") == identity["server_id"],
            f"{host}: server ID mismatch",
        )
        require(
            receipt.get("ssh_host_ed25519_fingerprint")
            == identity["ssh_host_ed25519_fingerprint"],
            f"{host}: SSH host-key fingerprint mismatch",
        )
        for field, value in (
            ("official_commit", EXPECTED_COMMIT),
            ("normalized_dataset_sha256", EXPECTED_SOURCE_SHA256),
            ("official_agent_inputs_sha256", EXPECTED_AGENT_INPUTS_SHA256),
            ("official_evaluator_checksum", EXPECTED_EVALUATOR_CHECKSUM),
            ("raw_dataset_sha256", EXPECTED_DATA_CHECKSUM),
            ("official_evaluator_image", EXPECTED_IMAGE),
            ("webarena_verified_version", "1.2.3"),
            ("playwright_version", "1.56.0"),
            ("chromium_version", "141.0.7390.37"),
            ("docker_version", "29.1.3"),
            ("python_version", "3.12.3"),
            ("official_agent_input_count", 812),
            (
                "task_contract_index_path",
                "/opt/webarena-verified/v1.2.3/runtime/webarena_verified_task_contract_index.json",
            ),
            ("task_contract_index_sha256", EXPECTED_TASK_CONTRACT_INDEX_SHA256),
            (
                "original_webarena_runner_repository",
                "https://github.com/web-arena-x/webarena.git",
            ),
            ("original_webarena_runner_commit", EXPECTED_RUNNER_COMMIT),
            ("original_webarena_runner_tree", EXPECTED_RUNNER_TREE),
            (
                "original_webarena_runner_upstream_requirements_sha256",
                EXPECTED_RUNNER_UPSTREAM_REQUIREMENTS_SHA256,
            ),
            (
                "original_webarena_runner_raw_tasks_sha256",
                EXPECTED_RUNNER_RAW_TASKS_SHA256,
            ),
            (
                "runner_requirements_input_sha256",
                EXPECTED_RUNNER_REQUIREMENTS_INPUT_SHA256,
            ),
            (
                "runner_requirements_lock_sha256",
                EXPECTED_RUNNER_REQUIREMENTS_LOCK_SHA256,
            ),
            ("runner_dependency_freeze_sha256", EXPECTED_RUNNER_FREEZE_SHA256),
            ("runner_python_version", "3.11.13"),
            ("runner_package_version", "0.0.0"),
            ("runner_playwright_version", "1.56.0"),
            ("runner_upstream_generated_prompt_absent", True),
            ("runner_generated_config_count", 812),
            ("runner_chromium_version", "141.0.7390.37"),
        ):
            require(receipt.get(field) == value, f"{host}: unexpected {field}")
        require(
            receipt.get("legacy_evaluator_importable_in_locked_environment") is False,
            f"{host}: legacy evaluator is importable",
        )
        require(
            receipt.get("legacy_evaluator_importable_in_official_evaluator_environment")
            is False,
            f"{host}: legacy evaluator is importable in the official evaluator environment",
        )
        require(
            receipt.get("legacy_evaluator_present_only_as_unused_runner_source")
            is True,
            f"{host}: legacy evaluator source boundary is not explicit",
        )
        validation = dict(receipt.get("validation") or {})
        for field in (
            "dataset_host_docker_identical",
            "native_aggregate_is_binary_not_browsergym_average",
            "playwright_chromium_launch",
            "playwright_full_embedded_har_injection",
            "strict_pinned_scorer_lane",
            "strict_scorer_network_har",
            "original_webarena_runner_imports",
            "script_browser_env_accessibility_tree",
            "script_browser_env_full_embedded_har",
            "runner_and_evaluator_share_chromium_binary",
            "runner_upstream_generated_prompt_absent",
            "task_contract_index_hash_verified",
            "task_contract_index_schema_validated",
        ):
            require(
                validation.get(field) is True, f"{host}: validation gate {field} failed"
            )
        require(
            validation.get("original_webarena_generated_config_count") == 812,
            f"{host}: runner config generation did not cover full-812",
        )
        require(
            validation.get("retrieval_task_108_actual_score") == 1.0,
            f"{host}: retrieval fixture failed",
        )
        require(
            validation.get("navigation_task_44_actual_score") == 1.0,
            f"{host}: dual-evaluator fixture failed",
        )
        require(
            validation.get("negative_control_task_44_actual_score") == 0.0,
            f"{host}: negative control failed",
        )
        normalized = {
            key: value for key, value in receipt.items() if key not in IDENTITY_FIELDS
        }
        normalized_hashes.add(sha256_bytes(canonical_bytes(normalized)))
        evidence.append(
            {
                "server_id": identity["server_id"],
                "vps_address": host,
                "model": identity["model"],
                "ssh_host_ed25519_fingerprint": identity[
                    "ssh_host_ed25519_fingerprint"
                ],
                "receipt_path": str(path.relative_to(ROOT)),
                "receipt_sha256": sha256_file(path),
            }
        )
    require(
        len(normalized_hashes) == 1,
        "the three environment receipts differ outside identity fields",
    )
    first = load_json(receipt_paths[sorted(expected)[0]])
    require(
        LOCAL_DPKG_INVENTORY.is_file(), "canonical dpkg inventory is not frozen locally"
    )
    require(
        LOCAL_PYTHON_FREEZE.is_file(),
        "canonical Python dependency freeze is not frozen locally",
    )
    require(
        LOCAL_RUNNER_FREEZE.is_file(),
        "canonical runner dependency freeze is not frozen locally",
    )
    require(
        sha256_file(LOCAL_DPKG_INVENTORY) == first["dpkg_package_inventory_sha256"],
        "local dpkg inventory differs from the three verified servers",
    )
    require(
        sha256_file(LOCAL_PYTHON_FREEZE) == first["dependency_freeze_sha256"],
        "local Python dependency freeze differs from the three verified servers",
    )
    require(
        len(LOCAL_DPKG_INVENTORY.read_text(encoding="utf-8").splitlines())
        == first["dpkg_package_inventory_count"],
        "local dpkg inventory count mismatch",
    )
    require(
        sha256_file(LOCAL_RUNNER_FREEZE) == first["runner_dependency_freeze_sha256"],
        "local runner dependency freeze differs from the three verified servers",
    )
    require(
        first["runner_chromium_executable_sha256"]
        == first["chromium_executable_sha256"],
        "runner and evaluator environments do not share the frozen Chromium binary",
    )
    return {
        "status": "pass",
        "server_count": 3,
        "identity_bound_receipts": evidence,
        "common_environment_canonical_sha256": next(iter(normalized_hashes)),
        "dpkg_package_count": first["dpkg_package_inventory_count"],
        "dpkg_package_inventory_sha256": first["dpkg_package_inventory_sha256"],
        "dpkg_package_inventory_path": str(LOCAL_DPKG_INVENTORY.relative_to(ROOT)),
        "python_dependency_freeze_sha256": first["dependency_freeze_sha256"],
        "python_dependency_freeze_path": str(LOCAL_PYTHON_FREEZE.relative_to(ROOT)),
        "runner_dependency_freeze_sha256": first["runner_dependency_freeze_sha256"],
        "runner_dependency_freeze_path": str(LOCAL_RUNNER_FREEZE.relative_to(ROOT)),
        "original_webarena_runner_commit": first["original_webarena_runner_commit"],
        "original_webarena_runner_tree": first["original_webarena_runner_tree"],
        "runner_python_version": first["runner_python_version"],
        "runner_playwright_version": first["runner_playwright_version"],
        "chromium_executable_sha256": first["chromium_executable_sha256"],
        "provision_script_sha256": first["provision_script_sha256"],
        "validation_script_sha256": first["validation_script_sha256"],
        "official_scorer_script_sha256": first["official_scorer_script_sha256"],
    }


def validate_official_evaluator_route(environment: Mapping[str, Any]) -> dict[str, Any]:
    scorer_path = (
        ROOT
        / "src"
        / "evidence_system"
        / "adapters"
        / "webarena_verified_official_scorer.py"
    )
    prompt_path = (
        ROOT
        / "src"
        / "evidence_system"
        / "adapters"
        / webarena_official_worker.FALLBACK_PROMPT_TEMPLATE_RELATIVE_PATH
    )
    worker_source = inspect.getsource(webarena_official_worker.run_official_job)
    require(
        "evaluation_harness" not in worker_source,
        "production worker still imports the legacy evaluator",
    )
    require(
        webarena_official_worker.RUNNER_FIXES.get("evaluator")
        == "webarena_verified_v1_2_3_eval_tasks",
        "production worker is not locked to the v1.2.3 evaluator lane",
    )
    require(
        webarena_official_worker.RUNNER_FIXES.get("trace")
        == "playwright_full_embedded_har",
        "production worker is not locked to full embedded HAR",
    )
    require(
        webarena_official_worker.RUNNER_KIND
        == "project_selected_webarena_dce04686_with_verified_v1_2_3_scorer",
        "browser driver provenance is mislabeled",
    )
    require(
        webarena_official_worker.RUNNER_FIXES.get("prompt")
        == "pinned_bundled_p_cot_id_actree_2s",
        "production worker is not locked to the bundled prompt",
    )
    require(
        sha256_file(prompt_path) == EXPECTED_BUNDLED_PROMPT_SHA256,
        "bundled prompt hash mismatch",
    )
    require(
        webarena_verified_official_scorer.OFFICIAL_IMAGE == EXPECTED_IMAGE,
        "scorer image digest mismatch",
    )
    require(
        webarena_verified_official_scorer.EXPECTED_EVALUATOR_CHECKSUM
        == EXPECTED_EVALUATOR_CHECKSUM,
        "scorer evaluator checksum mismatch",
    )
    require(
        webarena_verified_official_scorer.EXPECTED_TASK_CONTRACT_INDEX_SHA256
        == EXPECTED_TASK_CONTRACT_INDEX_SHA256,
        "scorer task-contract hash mismatch",
    )
    require(
        environment["official_scorer_script_sha256"] == sha256_file(scorer_path),
        "deployed scorer script differs from the repository scorer",
    )
    return {
        "status": "pass",
        "formal_backend": "pinned Docker eval-tasks",
        "official_image": EXPECTED_IMAGE,
        "official_commit": EXPECTED_COMMIT,
        "official_evaluator_checksum": EXPECTED_EVALUATOR_CHECKSUM,
        "official_data_checksum": EXPECTED_DATA_CHECKSUM,
        "task_contract_index_sha256": EXPECTED_TASK_CONTRACT_INDEX_SHA256,
        "bundled_prompt_sha256": EXPECTED_BUNDLED_PROMPT_SHA256,
        "required_network_artifact": "Playwright full/embed network.har",
        "legacy_evaluation_harness_allowed": False,
        "official_result_visibility": "controller_only",
    }


def _validate_packets_v1_legacy() -> dict[str, Any]:
    """Historical validator retained only as migration context; never invoked."""
    index_path = PACKETS_ROOT / "index.json"
    index = load_json(index_path)
    index_core = dict(index)
    claimed_core_hash = str(index_core.pop("index_core_sha256", ""))
    require(
        sha256_bytes(canonical_bytes(index_core)) == claimed_core_hash,
        "packet index self-reported core hash does not match its content",
    )
    require(index.get("packet_count") == 812, "packet index count is not 812")
    require(
        index.get("index_core_sha256") == claimed_core_hash,
        "packet index core hash mismatch",
    )
    require(
        index.get("source_sha256") == EXPECTED_SOURCE_SHA256,
        "packet source hash mismatch",
    )
    require(
        index.get("official_agent_inputs_sha256") == EXPECTED_AGENT_INPUTS_SHA256,
        "packet agent-input export hash mismatch",
    )
    require(
        index.get("task_type_counts")
        == {"MUTATE": 374, "NAVIGATE": 113, "RETRIEVE": 325},
        "task type counts mismatch",
    )
    require(
        index.get("task_contract_index_path") == "task_contract_index.json",
        "task contract path mismatch",
    )
    require(
        index.get("task_contract_index_sha256") == EXPECTED_TASK_CONTRACT_INDEX_SHA256,
        "task contract hash mismatch",
    )
    require(
        (PACKETS_ROOT / "index.json.sha256").read_text(encoding="utf-8")
        == f"{sha256_file(index_path)}  index.json\n",
        "packet index SHA sidecar mismatch",
    )

    contract_path = PACKETS_ROOT / "task_contract_index.json"
    contract = load_json(contract_path)
    require(
        sha256_file(contract_path) == EXPECTED_TASK_CONTRACT_INDEX_SHA256,
        "task contract file hash mismatch",
    )
    require(
        (PACKETS_ROOT / "task_contract_index.json.sha256").read_text(encoding="utf-8")
        == f"{EXPECTED_TASK_CONTRACT_INDEX_SHA256}  task_contract_index.json\n",
        "task contract SHA sidecar mismatch",
    )
    require(
        contract.get("schema_version") == "webarena_verified_task_contract_index/v1",
        "task contract schema mismatch",
    )
    require(
        contract.get("visibility") == "controller_only",
        "task contract must be controller-only",
    )
    require(contract.get("task_count") == 812, "task contract count is not 812")
    require(
        contract.get("source_sha256") == EXPECTED_SOURCE_SHA256,
        "task contract source hash mismatch",
    )

    official_inputs = load_json(OFFICIAL_INPUTS)
    require(
        len(official_inputs) == 812
        and sha256_file(OFFICIAL_INPUTS) == EXPECTED_AGENT_INPUTS_SHA256,
        "official agent inputs mismatch",
    )
    by_id = {int(item["task_id"]): item for item in official_inputs}
    require(
        sorted(by_id) == list(range(812)), "official agent input IDs are incomplete"
    )

    official_source = load_json(OFFICIAL_SOURCE)
    require(
        len(official_source) == 812
        and sha256_file(OFFICIAL_SOURCE) == EXPECTED_SOURCE_SHA256,
        "official full source mismatch",
    )
    source_by_id = {int(item["task_id"]): item for item in official_source}
    require(
        sorted(source_by_id) == list(range(812)),
        "official full source IDs are incomplete",
    )
    index_entries = {
        int(item["task_id"]): item for item in list(index.get("entries") or [])
    }
    contract_entries = {
        int(item["task_id"]): item for item in list(contract.get("entries") or [])
    }
    require(
        sorted(index_entries) == list(range(812)), "packet index entries are incomplete"
    )
    require(
        sorted(contract_entries) == list(range(812)),
        "task contract entries are incomplete",
    )

    numeric_directories = sorted(
        (path for path in PACKETS_ROOT.iterdir() if path.is_dir()),
        key=lambda path: int(path.name) if path.name.isdigit() else -1,
    )
    require(
        all(
            path.name.isdigit() and not path.is_symlink()
            for path in numeric_directories
        ),
        "packet root has an unexpected or symlinked directory",
    )
    require(
        [int(path.name) for path in numeric_directories] == list(range(812)),
        "packet directories are not exactly 0..811",
    )

    for task_id in range(812):
        case_dir = PACKETS_ROOT / str(task_id)
        visible_path = case_dir / "agent_input.json"
        packet_path = case_dir / "case_packet.json"
        markdown_path = case_dir / "case_packet.md"
        manifest_path = case_dir / "raw_case_manifest.json"
        expected_names = {
            "agent_input.json",
            "case_packet.json",
            "case_packet.md",
            "raw_case_manifest.json",
        }
        require(
            {path.name for path in case_dir.iterdir()} == expected_names,
            f"task {task_id}: unexpected packet files",
        )
        require(
            all(
                path.is_file() and not path.is_symlink()
                for path in (visible_path, packet_path, markdown_path, manifest_path)
            ),
            f"task {task_id}: packet file missing or symlinked",
        )
        visible = load_json(visible_path)
        packet = load_json(packet_path)
        manifest = load_json(manifest_path)
        source_task = source_by_id[task_id]
        eval_configs = list(source_task.get("eval") or [])
        evaluator_names_in_order = [str(item["evaluator"]) for item in eval_configs]
        unique_evaluator_names = list(dict.fromkeys(evaluator_names_in_order))
        response_types = {
            str(item.get("expected", {}).get("task_type", "")).upper()
            for item in eval_configs
            if item.get("evaluator") == "AgentResponseEvaluator"
        }
        require(
            len(response_types) == 1, f"task {task_id}: official task type is ambiguous"
        )
        expected_task_type = next(iter(response_types))
        require(
            expected_task_type in {"RETRIEVE", "MUTATE", "NAVIGATE"},
            f"task {task_id}: invalid official task type",
        )

        require(
            set(visible) == AGENT_INPUT_FIELDS,
            f"task {task_id}: model-visible field allowlist violation",
        )
        require(
            visible == by_id[task_id],
            f"task {task_id}: model-visible input differs from official agent-input-get",
        )
        serialized = json.dumps(visible, ensure_ascii=False, sort_keys=True).lower()
        require(
            not any(
                token in serialized
                for token in ('"expected"', '"eval"', '"reference_answer"', "sk-or-v1-")
            ),
            f"task {task_id}: private/secret model input",
        )

        task = dict(packet.get("task") or {})
        public_task = {
            "task_id": task_id,
            "intent_template_id": int(source_task["intent_template_id"]),
            "instruction": str(source_task.get("intent") or ""),
            "task_type": expected_task_type,
            "revision": int(source_task["revision"]),
            "sites": list(source_task.get("sites") or []),
            "start_url_templates": list(source_task.get("start_urls") or []),
            "resolved_start_urls": list(visible["start_urls"]),
        }
        require(task == public_task, f"task {task_id}: public task projection mismatch")
        require(
            packet.get("runtime_limits") == EXPECTED_RUNTIME_LIMITS,
            f"task {task_id}: runtime limits mismatch",
        )

        evaluator_reference = dict(packet.get("evaluator_reference") or {})
        expected_evaluator_refs = [
            {
                "index": evaluator_index,
                "name": str(item["evaluator"]),
                "private_dataset_ref": f"official-dataset#task_id={task_id}/eval/{evaluator_index}",
                "private_config_sha256": sha256_bytes(canonical_bytes(item)),
            }
            for evaluator_index, item in enumerate(eval_configs)
        ]
        require(
            evaluator_reference.get("evaluator_names") == unique_evaluator_names,
            f"task {task_id}: evaluator names mismatch",
        )
        require(
            evaluator_reference.get("evaluator_config_names")
            == evaluator_names_in_order,
            f"task {task_id}: evaluator sequence mismatch",
        )
        require(
            evaluator_reference.get("evaluators") == expected_evaluator_refs,
            f"task {task_id}: evaluator references mismatch",
        )
        require(
            evaluator_reference.get("required_run_artifacts")
            == ["agent_response.json", "network.har"],
            f"task {task_id}: required evaluator artifacts mismatch",
        )

        require(
            packet.get("provenance", {}).get("source_sha256") == EXPECTED_SOURCE_SHA256,
            f"task {task_id}: source hash mismatch",
        )
        require(
            packet.get("provenance", {}).get("source_task_sha256")
            == sha256_bytes(canonical_bytes(source_task)),
            f"task {task_id}: source task hash mismatch",
        )
        require(
            packet.get("provenance", {}).get("public_task_sha256")
            == sha256_bytes(canonical_bytes(public_task)),
            f"task {task_id}: public task hash mismatch",
        )

        file_hashes = {
            "agent_input.json": sha256_file(visible_path),
            "case_packet.json": sha256_file(packet_path),
            "case_packet.md": sha256_file(markdown_path),
            "raw_case_manifest.json": sha256_file(manifest_path),
        }
        expected_index_entry = {
            "task_id": task_id,
            "task_type": expected_task_type,
            "revision": int(source_task["revision"]),
            "sites": list(source_task.get("sites") or []),
            "evaluator_names": unique_evaluator_names,
            "agent_input_sha256": file_hashes["agent_input.json"],
            "case_packet_json_sha256": file_hashes["case_packet.json"],
            "case_packet_markdown_sha256": file_hashes["case_packet.md"],
            "raw_case_manifest_sha256": file_hashes["raw_case_manifest.json"],
        }
        require(
            index_entries[task_id] == expected_index_entry,
            f"task {task_id}: packet index entry mismatch",
        )
        require(
            packet.get("model_visible_input", {}).get("sha256")
            == file_hashes["agent_input.json"],
            f"task {task_id}: visible input hash mismatch",
        )
        require(
            manifest.get("model_visible_files") == ["agent_input.json"],
            f"task {task_id}: unsafe visibility manifest",
        )
        require(
            manifest.get("controller_only_files")
            == ["case_packet.json", "case_packet.md", "raw_case_manifest.json"],
            f"task {task_id}: controller-only manifest mismatch",
        )
        require(
            manifest.get("sha256_per_file")
            == {
                name: file_hashes[name]
                for name in ("agent_input.json", "case_packet.json", "case_packet.md")
            },
            f"task {task_id}: raw manifest file hashes mismatch",
        )

        expected_contract_entry = {
            "task_id": task_id,
            "task_revision": int(source_task["revision"]),
            "task_type": expected_task_type,
            "intent_template_id": int(source_task["intent_template_id"]),
            "sites": list(source_task.get("sites") or []),
            "evaluator_names_in_order": evaluator_names_in_order,
            "required_run_artifacts": ["agent_response.json", "network.har"],
            "agent_input_sha256": file_hashes["agent_input.json"],
            "case_packet_sha256": file_hashes["case_packet.json"],
        }
        require(
            contract_entries[task_id] == expected_contract_entry,
            f"task {task_id}: task contract mismatch",
        )

    return {
        "status": "pass",
        "packet_count": 812,
        "task_id_range": [0, 811],
        "model_visible_file_count": 812,
        "private_evaluator_payloads_in_model_inputs": 0,
        "source_sha256": EXPECTED_SOURCE_SHA256,
        "official_agent_inputs_sha256": EXPECTED_AGENT_INPUTS_SHA256,
        "index_core_sha256": claimed_core_hash,
        "index_file_sha256": sha256_file(index_path),
        "task_contract_index_sha256": EXPECTED_TASK_CONTRACT_INDEX_SHA256,
    }


def validate_packets(
    *,
    source_bundle_path: Path = DEFAULT_SOURCE_BUNDLE,
    expected_packet_index_core_sha256: str | None = None,
) -> dict[str, Any]:
    require(
        OFFICIAL_SOURCE_SNAPSHOT.is_dir()
        and not OFFICIAL_SOURCE_SNAPSHOT.is_symlink(),
        "official v1.2.3 source snapshot is missing or symlinked",
    )
    require(
        OFFICIAL_TAG_SOURCE.is_file()
        and not OFFICIAL_TAG_SOURCE.is_symlink()
        and sha256_file(OFFICIAL_TAG_SOURCE) == EXPECTED_DATA_CHECKSUM,
        "official v1.2.3 tag dataset snapshot mismatch",
    )
    require(
        official_evaluator_snapshot_checksum() == EXPECTED_EVALUATOR_CHECKSUM,
        "official evaluator source-snapshot checksum mismatch",
    )
    for label, (relative, expected_hash) in OFFICIAL_EVALUATOR_SOURCE_HASHES.items():
        source_path = OFFICIAL_SOURCE_SNAPSHOT / relative
        require(
            source_path.is_file()
            and not source_path.is_symlink()
            and sha256_file(source_path) == expected_hash,
            f"official evaluator source hash mismatch: {label}",
        )

    index_path = PACKETS_ROOT / "index.json"
    require(
        index_path.is_file() and not index_path.is_symlink(),
        "packet index is missing or symlinked",
    )
    index = load_json(index_path)
    require(isinstance(index, Mapping), "packet index must be a mapping")
    index_core = dict(index)
    claimed_core_hash = str(index_core.pop("index_core_sha256", ""))
    require_sha256(claimed_core_hash, "packet index core hash")
    require(
        sha256_bytes(canonical_bytes(index_core)) == claimed_core_hash,
        "packet index self-reported core hash does not match its content",
    )
    if expected_packet_index_core_sha256 is not None:
        expected_core_hash = require_sha256(
            expected_packet_index_core_sha256,
            "explicit expected packet index core hash",
        )
        require(
            claimed_core_hash == expected_core_hash,
            "packet index core hash differs from explicit expected value",
        )
    index_sidecar = PACKETS_ROOT / "index.json.sha256"
    require(
        index_sidecar.is_file()
        and not index_sidecar.is_symlink()
        and index_sidecar.read_text(encoding="utf-8")
        == f"{sha256_file(index_path)}  index.json\n",
        "packet index SHA sidecar mismatch",
    )

    contract_path = PACKETS_ROOT / "task_contract_index.json"
    contract_sidecar = PACKETS_ROOT / "task_contract_index.json.sha256"
    require(
        contract_path.is_file()
        and not contract_path.is_symlink()
        and sha256_file(contract_path) == EXPECTED_TASK_CONTRACT_INDEX_SHA256,
        "task contract file hash mismatch",
    )
    require(
        contract_sidecar.is_file()
        and not contract_sidecar.is_symlink()
        and contract_sidecar.read_text(encoding="utf-8")
        == f"{EXPECTED_TASK_CONTRACT_INDEX_SHA256}  task_contract_index.json\n",
        "task contract SHA sidecar mismatch",
    )
    contract = load_json(contract_path)
    require(isinstance(contract, Mapping), "task contract index must be a mapping")
    require(
        contract.get("schema_version") == "webarena_verified_task_contract_index/v1"
        and contract.get("visibility") == "controller_only"
        and contract.get("task_count") == 812
        and contract.get("source_sha256") == EXPECTED_SOURCE_SHA256,
        "task contract metadata mismatch",
    )

    official_inputs = load_json(OFFICIAL_INPUTS)
    require(
        isinstance(official_inputs, list)
        and len(official_inputs) == 812
        and sha256_file(OFFICIAL_INPUTS) == EXPECTED_AGENT_INPUTS_SHA256,
        "official agent inputs mismatch",
    )
    by_id = {
        int(item["task_id"]): item
        for item in official_inputs
        if isinstance(item, Mapping)
    }
    require(
        sorted(by_id) == list(range(812)),
        "official agent input IDs are incomplete",
    )

    official_source = load_json(OFFICIAL_SOURCE)
    require(
        isinstance(official_source, list)
        and len(official_source) == 812
        and sha256_file(OFFICIAL_SOURCE) == EXPECTED_SOURCE_SHA256,
        "official normalized full source mismatch",
    )
    source_by_id = {
        int(item["task_id"]): item
        for item in official_source
        if isinstance(item, Mapping)
    }
    require(
        sorted(source_by_id) == list(range(812)),
        "official normalized source IDs are incomplete",
    )
    tag_source = load_json(OFFICIAL_TAG_SOURCE)
    require(
        isinstance(tag_source, list) and len(tag_source) == 812,
        "official tag source must contain exactly 812 tasks",
    )
    tag_source_by_id = {
        int(item["task_id"]): item
        for item in tag_source
        if isinstance(item, Mapping)
    }
    require(
        sorted(tag_source_by_id) == list(range(812)),
        "official tag source IDs are incomplete",
    )

    raw_index_entries = index.get("entries")
    raw_contract_entries = contract.get("entries")
    require(
        isinstance(raw_index_entries, list)
        and len(raw_index_entries) == 812
        and all(isinstance(item, Mapping) for item in raw_index_entries),
        "packet index entries must contain exactly 812 objects",
    )
    require(
        isinstance(raw_contract_entries, list)
        and len(raw_contract_entries) == 812
        and all(isinstance(item, Mapping) for item in raw_contract_entries),
        "task contract entries must contain exactly 812 objects",
    )
    index_entries = {int(item["task_id"]): item for item in raw_index_entries}
    contract_entries = {
        int(item["task_id"]): item for item in raw_contract_entries
    }
    require(
        sorted(index_entries) == list(range(812)),
        "packet index entries are missing or duplicated",
    )
    require(
        sorted(contract_entries) == list(range(812)),
        "task contract entries are missing or duplicated",
    )

    require(
        PACKETS_ROOT.is_dir() and not PACKETS_ROOT.is_symlink(),
        "packet root is missing or symlinked",
    )
    numeric_directories = [path for path in PACKETS_ROOT.iterdir() if path.is_dir()]
    require(
        all(path.name.isdigit() and not path.is_symlink() for path in numeric_directories),
        "packet root has an unexpected or symlinked directory",
    )
    require(
        sorted(int(path.name) for path in numeric_directories) == list(range(812)),
        "packet directories are not exactly 0..811",
    )
    root_files = {path.name for path in PACKETS_ROOT.iterdir() if path.is_file()}
    require(
        root_files
        == {
            "index.json",
            "index.json.sha256",
            "task_contract_index.json",
            "task_contract_index.json.sha256",
        },
        "packet root has unexpected top-level files",
    )
    require(
        not list(PACKETS_ROOT.rglob("draft_case_packet.md")),
        "a parallel draft_case_packet.md set exists; case_packet.md must be the sole drafter packet",
    )

    expected_index_entries: list[dict[str, Any]] = []
    packet_hashes_by_id: dict[int, dict[str, str]] = {}
    agent_input_tree = hashlib.sha256()
    agent_input_total_bytes = 0
    raw_case_file_count = 0
    packet_source_file_count = 0

    for task_id in range(812):
        case_dir = PACKETS_ROOT / str(task_id)
        visible_path = case_dir / "agent_input.json"
        packet_path = case_dir / "case_packet.json"
        markdown_path = case_dir / "case_packet.md"
        manifest_path = case_dir / "raw_case_manifest.json"
        raw_case_dir = case_dir / "raw_case"
        require(
            {path.name for path in case_dir.iterdir()}
            == {
                "agent_input.json",
                "case_packet.json",
                "case_packet.md",
                "raw_case",
                "raw_case_manifest.json",
            },
            f"task {task_id}: unexpected packet files",
        )
        require(
            all(
                path.is_file() and not path.is_symlink()
                for path in (visible_path, packet_path, markdown_path, manifest_path)
            )
            and raw_case_dir.is_dir()
            and not raw_case_dir.is_symlink(),
            f"task {task_id}: packet file missing or symlinked",
        )
        visible = load_json(visible_path)
        packet = load_json(packet_path)
        manifest = load_json(manifest_path)
        require(
            isinstance(visible, Mapping)
            and isinstance(packet, Mapping)
            and isinstance(manifest, Mapping),
            f"task {task_id}: a packet JSON file is not an object",
        )
        source_task = source_by_id[task_id]
        eval_configs = list(source_task.get("eval") or [])
        require(
            eval_configs and all(isinstance(item, Mapping) for item in eval_configs),
            f"task {task_id}: official evaluator configuration is invalid",
        )
        evaluator_names_in_order = [str(item["evaluator"]) for item in eval_configs]
        unique_evaluator_names = list(dict.fromkeys(evaluator_names_in_order))
        require(
            set(unique_evaluator_names).issubset(ALLOWED_EVALUATOR_NAMES)
            and "AgentResponseEvaluator" in unique_evaluator_names,
            f"task {task_id}: unsupported official evaluator",
        )
        response_types = {
            str(item.get("expected", {}).get("task_type", "")).upper()
            for item in eval_configs
            if item.get("evaluator") == "AgentResponseEvaluator"
        }
        require(
            len(response_types) == 1,
            f"task {task_id}: official task type is ambiguous",
        )
        expected_task_type = next(iter(response_types))
        require(
            expected_task_type in {"RETRIEVE", "MUTATE", "NAVIGATE"},
            f"task {task_id}: invalid official task type",
        )

        require(
            set(visible) == AGENT_INPUT_FIELDS,
            f"task {task_id}: model-visible field allowlist violation",
        )
        visible_bytes = visible_path.read_bytes()
        require(
            visible_bytes == deterministic_json_bytes(by_id[task_id]),
            f"task {task_id}: agent_input.json bytes changed from the frozen export projection",
        )
        require(
            dict(visible) == by_id[task_id],
            f"task {task_id}: model-visible input differs from official agent-input-get",
        )
        serialized_visible = json.dumps(
            visible, ensure_ascii=False, sort_keys=True
        ).lower()
        require(
            not any(
                token in serialized_visible
                for token in (
                    '"expected"',
                    '"eval"',
                    '"reference_answer"',
                    "sk-or-v1-",
                )
            ),
            f"task {task_id}: private/secret model input",
        )
        agent_input_hash = sha256_bytes(visible_bytes)
        agent_input_size = len(visible_bytes)
        agent_input_total_bytes += agent_input_size
        agent_input_tree.update(
            f"{task_id}\t{agent_input_hash}\t{agent_input_size}\n".encode("utf-8")
        )

        task = dict(packet.get("task") or {})
        public_task = {
            "task_id": task_id,
            "intent_template_id": int(source_task["intent_template_id"]),
            "instruction": str(source_task.get("intent") or ""),
            "task_type": expected_task_type,
            "revision": int(source_task["revision"]),
            "sites": list(source_task.get("sites") or []),
            "start_url_templates": list(source_task.get("start_urls") or []),
            "resolved_start_urls": list(visible["start_urls"]),
        }
        require(task == public_task, f"task {task_id}: public task projection mismatch")
        require(
            packet.get("runtime_limits") == EXPECTED_RUNTIME_LIMITS,
            f"task {task_id}: runtime limits mismatch",
        )

        evaluator_reference = dict(packet.get("evaluator_reference") or {})
        expected_evaluator_refs = [
            {
                "index": evaluator_index,
                "name": str(item["evaluator"]),
                "private_dataset_ref": (
                    f"official-dataset#task_id={task_id}/eval/{evaluator_index}"
                ),
                "private_config_sha256": sha256_bytes(canonical_bytes(item)),
            }
            for evaluator_index, item in enumerate(eval_configs)
        ]
        require(
            evaluator_reference.get("evaluator_names") == unique_evaluator_names
            and evaluator_reference.get("evaluator_config_names")
            == evaluator_names_in_order
            and evaluator_reference.get("evaluators") == expected_evaluator_refs
            and evaluator_reference.get("required_run_artifacts")
            == ["agent_response.json", "network.har"],
            f"task {task_id}: evaluator reference mismatch",
        )
        provenance = packet.get("provenance")
        require(
            isinstance(provenance, Mapping)
            and provenance.get("source_sha256") == EXPECTED_SOURCE_SHA256
            and provenance.get("source_task_sha256")
            == sha256_bytes(canonical_bytes(source_task))
            and provenance.get("public_task_sha256")
            == sha256_bytes(canonical_bytes(public_task)),
            f"task {task_id}: packet provenance mismatch",
        )
        leakage = packet.get("leakage_control")
        require(
            isinstance(leakage, Mapping)
            and leakage.get("model_receives_only_agent_input_json") is True
            and leakage.get("evaluator_payload_embedded") is False
            and leakage.get("answer_payload_embedded") is False,
            f"task {task_id}: controller-to-agent leakage boundary mismatch",
        )

        raw_counts = validate_raw_case(
            task_id=task_id,
            case_dir=case_dir,
            markdown_path=markdown_path,
            manifest=manifest,
            source_task=source_task,
            tag_task=tag_source_by_id[task_id],
            evaluator_names=unique_evaluator_names,
        )
        raw_case_file_count += raw_counts["raw_case_file_count"]
        packet_source_file_count += raw_counts["packet_source_file_count"]

        file_hashes = {
            "agent_input.json": sha256_file(visible_path),
            "case_packet.json": sha256_file(packet_path),
            "case_packet.md": sha256_file(markdown_path),
            "raw_case_manifest.json": sha256_file(manifest_path),
        }
        packet_hashes_by_id[task_id] = file_hashes
        expected_index_entry = {
            "task_id": task_id,
            "task_type": expected_task_type,
            "revision": int(source_task["revision"]),
            "sites": list(source_task.get("sites") or []),
            "evaluator_names": unique_evaluator_names,
            "agent_input_sha256": file_hashes["agent_input.json"],
            "case_packet_json_sha256": file_hashes["case_packet.json"],
            "case_packet_markdown_sha256": file_hashes["case_packet.md"],
            "raw_case_manifest_sha256": file_hashes["raw_case_manifest.json"],
            "raw_case_tree_sha256": raw_counts["raw_case_tree_sha256"],
            "raw_case_file_count": raw_counts["raw_case_file_count"],
            "raw_case_total_bytes": raw_counts["raw_case_total_bytes"],
        }
        expected_index_entries.append(expected_index_entry)
        require(
            dict(index_entries[task_id]) == expected_index_entry,
            f"task {task_id}: packet index entry mismatch",
        )
        require(
            packet.get("model_visible_input", {}).get("sha256")
            == file_hashes["agent_input.json"],
            f"task {task_id}: visible input hash mismatch",
        )

        expected_contract_entry = {
            "task_id": task_id,
            "task_revision": int(source_task["revision"]),
            "task_type": expected_task_type,
            "intent_template_id": int(source_task["intent_template_id"]),
            "sites": list(source_task.get("sites") or []),
            "evaluator_names_in_order": evaluator_names_in_order,
            "required_run_artifacts": ["agent_response.json", "network.har"],
            "agent_input_sha256": file_hashes["agent_input.json"],
            "case_packet_sha256": file_hashes["case_packet.json"],
        }
        require(
            dict(contract_entries[task_id]) == expected_contract_entry,
            f"task {task_id}: fixed task contract mismatch",
        )

    actual_agent_input_tree_sha256 = agent_input_tree.hexdigest()
    require(
        actual_agent_input_tree_sha256 == EXPECTED_AGENT_INPUT_TREE_SHA256,
        "agent_input.json tree hash changed",
    )
    require(
        agent_input_total_bytes == EXPECTED_AGENT_INPUT_TOTAL_BYTES,
        "agent_input.json total byte count changed",
    )
    source_bundle = validate_source_bundle(
        source_bundle_path=source_bundle_path,
        packet_hashes_by_id=packet_hashes_by_id,
    )

    expected_index_core = {
        "schema_version": EXPECTED_INDEX_SCHEMA_VERSION,
        "status": "frozen",
        "benchmark": "WebArena-Verified",
        "version": "v1.2.3",
        "split": "full",
        "source_path": repo_relative(OFFICIAL_SOURCE),
        "source_sha256": EXPECTED_SOURCE_SHA256,
        "official_agent_inputs_path": repo_relative(OFFICIAL_INPUTS),
        "official_agent_inputs_sha256": EXPECTED_AGENT_INPUTS_SHA256,
        "raw_tag_dataset_sha256": EXPECTED_DATA_CHECKSUM,
        "official_commit": EXPECTED_COMMIT,
        "packet_count": 812,
        "model_visible_file_count": 812,
        "task_type_counts": {"MUTATE": 374, "NAVIGATE": 113, "RETRIEVE": 325},
        "evaluator_task_counts": {
            "AgentResponseEvaluator": 812,
            "NetworkEventEvaluator": 488,
        },
        "evaluator_config_counts": {
            "AgentResponseEvaluator": 812,
            "NetworkEventEvaluator": 663,
        },
        "task_contract_index_path": "task_contract_index.json",
        "task_contract_index_sha256": EXPECTED_TASK_CONTRACT_INDEX_SHA256,
        "source_bundle_path": source_bundle["path"],
        "source_bundle_sha256": source_bundle["sha256"],
        "source_bundle_source_count": 812,
        "official_source_snapshot_path": repo_relative(OFFICIAL_SOURCE_SNAPSHOT),
        "official_evaluator_checksum": EXPECTED_EVALUATOR_CHECKSUM,
        "canonical_packet_filename": "case_packet.md",
        "packet_visibility": "drafter_and_reviewer_only",
        "model_visible_files_per_case": ["agent_input.json"],
        "draft_case_packet_file_count": 0,
        "agent_input_tree_sha256": EXPECTED_AGENT_INPUT_TREE_SHA256,
        "agent_input_total_bytes": EXPECTED_AGENT_INPUT_TOTAL_BYTES,
        "entries": expected_index_entries,
    }
    require(
        index_core == expected_index_core,
        "packet index v2 core differs from the exact source-rich acceptance projection",
    )

    return {
        "status": "pass",
        "packet_count": 812,
        "drafter_ready_packet_count": 812,
        "task_id_range": [0, 811],
        "model_visible_file_count": 812,
        "private_evaluator_payloads_in_model_inputs": 0,
        "agent_input_bytes_preserved": True,
        "agent_inputs_byte_preserved": True,
        "agent_input_tree_sha256": actual_agent_input_tree_sha256,
        "agent_input_total_bytes": agent_input_total_bytes,
        "source_sha256": EXPECTED_SOURCE_SHA256,
        "official_agent_inputs_sha256": EXPECTED_AGENT_INPUTS_SHA256,
        "official_evaluator_checksum": EXPECTED_EVALUATOR_CHECKSUM,
        "official_evaluator_source_snapshot_checksum": EXPECTED_EVALUATOR_CHECKSUM,
        "official_evaluator_sources_verified": True,
        "official_evaluator_source_hashes": {
            label: expected_hash
            for label, (_, expected_hash) in OFFICIAL_EVALUATOR_SOURCE_HASHES.items()
        },
        "official_tag_dataset_sha256": EXPECTED_DATA_CHECKSUM,
        "raw_case_file_count": raw_case_file_count,
        "packet_source_file_count": packet_source_file_count,
        "source_inventory_verified_file_count": packet_source_file_count,
        "minimal_drafter_packet_parse_count": 812,
        "minimal_metadata_parseable_count": 812,
        "source_inventory_parse_count": 812,
        "source_inventory_parseable_count": 812,
        "draft_case_packet_file_count": 0,
        "source_bundle": source_bundle,
        "source_bundle_path": source_bundle["path"],
        "source_bundle_sha256": source_bundle["sha256"],
        "source_bundle_source_count": source_bundle["source_count"],
        "index_core_sha256": claimed_core_hash,
        "index_file_sha256": sha256_file(index_path),
        "task_contract_index_sha256": EXPECTED_TASK_CONTRACT_INDEX_SHA256,
    }


def evidence_ref(path: Path) -> dict[str, Any]:
    """Return value-free evidence metadata for a repository-local file."""

    try:
        label = repo_relative(path)
        repository_local = True
    except RuntimeError:
        # Tests may inject a temporary receipt.  Never serialize its absolute
        # path; production evidence constants are all repository-local.
        label = path.name
        repository_local = False
    return {
        "path": label,
        "repository_local": repository_local,
        "exists": path.is_file(),
        **({"sha256": sha256_file(path)} if path.is_file() else {}),
    }


def _load_optional_receipt(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, None
    try:
        payload = load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"invalid JSON receipt: {type(exc).__name__}"
    if not isinstance(payload, Mapping):
        return None, "receipt root is not an object"
    return dict(payload), None


def _sidecar_valid(path: Path) -> bool:
    sidecar = path.with_name(path.name + ".sha256")
    if not sidecar.is_file():
        return False
    return sidecar.read_text(encoding="utf-8") == (
        f"{sha256_file(path)}  {path.name}\n"
    )


def validate_native_claim_aggregate() -> dict[str, dict[str, Any]]:
    payload, error = _load_optional_receipt(NATIVE_CLAIM_ACCEPTANCE)
    evidence = evidence_ref(NATIVE_CLAIM_ACCEPTANCE)
    if payload is None:
        status = "fail" if error else "pending"
        reason = error or "native claim acceptance receipt is missing"
        return {
            "native_contract_machine_validation": {
                "status": status,
                "reason": reason,
                "evidence": evidence,
            },
            "native_contract_human_signoff": {
                "status": "pending",
                "signed_count": 0,
                "required_count": 812,
                "formal_launch_eligible": False,
                "reason": "hash-bound human source-check evidence is missing",
                "evidence": evidence,
            },
            "native_contract_operator_waiver": {
                "status": "pending",
                "reason": "machine-only operator waiver is missing",
                "human_signoff_claimed": False,
                "human_signed_count": 0,
                "evidence": evidence_ref(OPERATOR_WAIVER),
            },
        }

    package_report = webarena_native.validate_native_claim_package(
        NATIVE_CLAIM_ACCEPTANCE.parent,
        current_source_check=True,
    )
    counts = dict(payload.get("counts") or {})
    gates = dict(payload.get("gates") or {})
    machine_ok = (
        payload.get("schema_version")
        == "webarena_verified_native_claim_acceptance/v1"
        and payload.get("status")
        in {
            "machine_validated_human_signoff_pending",
            "accepted",
            "accepted_machine_only_operator_waiver",
        }
        and isinstance(payload.get("formal_launch_eligible"), bool)
        and counts.get("native_ir") == 812
        and counts.get("draft_contracts") == 812
        and counts.get("draft_checklists") == 812
        and counts.get("machine_validated") == 812
        and dict(payload.get("machine_contract_gate") or {}).get(
            "fallback_contract_count"
        )
        == 0
        and package_report.get("status") == "ok"
        and package_report.get("issue_count") == 0
        and all(
            gates.get(name) is True
            for name in (
                "agent_input_tree_unchanged",
                "checklists_schema_valid",
                "contracts_schema_valid",
                "input_set_exact",
                "machine_validation_complete",
                "native_semantics_complete",
                "source_hashes_valid",
            )
        )
        and _sidecar_valid(NATIVE_CLAIM_ACCEPTANCE)
    )
    signed_count = int(counts.get("human_signed") or 0)
    locked_contracts = int(counts.get("locked_contracts") or 0)
    locked_checklists = int(counts.get("locked_checklists") or 0)
    human_ok = (
        payload.get("status") == "accepted"
        and payload.get("formal_launch_eligible") is True
        and signed_count == 812
        and locked_contracts == 812
        and locked_checklists == 812
        and gates.get("human_signoff_complete") is True
        and gates.get("formal_locks_complete") is True
    )
    operator_descriptor = dict(payload.get("operator_waiver") or {})
    waiver_mode = payload.get("status") == "accepted_machine_only_operator_waiver"
    waiver_ok = (
        waiver_mode
        and payload.get("formal_launch_eligible") is True
        and signed_count == 0
        and locked_contracts == 812
        and locked_checklists == 812
        and gates.get("human_signoff_complete") is False
        and gates.get("human_signoff_requirement_waived") is True
        and gates.get("operator_waiver_valid") is True
        and gates.get("formal_policy_locks_complete") is True
        and gates.get("formal_locks_complete") is True
        and dict(payload.get("human_signoff") or {}).get("status")
        == "waived_not_signed"
        and dict(payload.get("human_signoff") or {}).get("signed_count") == 0
        and dict(payload.get("machine_contract_gate") or {}).get(
            "formal_human_locked"
        )
        is False
        and dict(payload.get("machine_contract_gate") or {}).get(
            "formal_policy_locked"
        )
        is True
        and dict(payload.get("machine_contract_gate") or {}).get(
            "authorizes_formal_launch"
        )
        is True
        and operator_descriptor.get("requirement_waived") is True
        and operator_descriptor.get("input_sha256")
        == (sha256_file(OPERATOR_WAIVER) if OPERATOR_WAIVER.is_file() else None)
        and _sidecar_valid(OPERATOR_WAIVER)
        and package_report.get("status") == "ok"
        and package_report.get("issue_count") == 0
    )
    return {
        "native_contract_machine_validation": {
            "status": "pass" if machine_ok else "fail",
            "machine_validated_count": int(counts.get("machine_validated") or 0),
            "native_contract_count": int(counts.get("draft_contracts") or 0),
            "checklist_count": int(counts.get("draft_checklists") or 0),
            "fallback_contract_count": int(
                dict(payload.get("machine_contract_gate") or {}).get(
                    "fallback_contract_count", -1
                )
            ),
            "scope": "deterministic_machine_validation_not_human_signoff",
            "package_validation_status": package_report.get("status"),
            "package_validation_issue_count": int(
                package_report.get("issue_count") or 0
            ),
            "evidence": evidence,
        },
        "native_contract_human_signoff": {
            "status": "pass" if human_ok else "waived" if waiver_ok else "pending",
            "signed_count": signed_count,
            "locked_contract_count": locked_contracts,
            "locked_checklist_count": locked_checklists,
            "required_count": 812,
            "formal_launch_eligible": human_ok,
            "formal_launch_eligible_via_human_signoff": human_ok,
            "formal_launch_eligible_via_operator_waiver": waiver_ok,
            "requirement_waived": waiver_ok,
            "human_signoff_claimed": human_ok,
            "reason": (
                None
                if human_ok
                else "human review requirement explicitly waived; no human signoff claimed"
                if waiver_ok
                else "812 hash-bound human source-check signoffs are not present"
            ),
            "evidence": evidence,
        },
        "native_contract_operator_waiver": {
            "status": "pass" if waiver_ok else "not_applicable" if human_ok else "pending",
            "basis": (
                "operator_machine_only_waiver" if waiver_ok else None
            ),
            "human_signoff_claimed": False,
            "reviewer_identity_or_signature_claimed": False,
            "human_signed_count": signed_count,
            "machine_validated_count": int(counts.get("machine_validated") or 0),
            "fallback_contract_count": int(
                dict(payload.get("machine_contract_gate") or {}).get(
                    "fallback_contract_count", -1
                )
            ),
            "formal_policy_locked_count": locked_contracts,
            "formal_launch_eligible": waiver_ok,
            "evidence": {
                "operator_waiver": evidence_ref(OPERATOR_WAIVER),
                "native_acceptance": evidence,
            },
        },
    }


def validate_native_human_review_queue(
    operator_waiver_gate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate that the real reviewer has an exact, unsigned 812-item queue.

    This is a machine-readiness gate only.  It deliberately cannot turn the
    separate human-signoff gate green.
    """

    if (
        isinstance(operator_waiver_gate, Mapping)
        and operator_waiver_gate.get("status") == "pass"
    ):
        return {
            "status": "pass",
            "queue_state": "superseded_unsigned_queue_not_human_approval",
            "queue_item_count": 0,
            "pending_human_review_count": 0,
            "human_signed_count": 0,
            "human_review_requirement_waived": True,
            "authorizes_human_signoff": False,
            "scope": "operator-waiver-supersedes-review-work-package-not-human-approval",
            "evidence": operator_waiver_gate.get("evidence"),
        }

    payload, error = _load_optional_receipt(HUMAN_REVIEW_ACCEPTANCE)
    evidence = evidence_ref(HUMAN_REVIEW_ACCEPTANCE)
    if payload is None:
        return {
            "status": "fail" if error else "pending",
            "reason": error or "hash-bound 812-item human review queue is missing",
            "authorizes_human_signoff": False,
            "evidence": evidence,
        }
    counts = dict(payload.get("counts") or {})
    gates = dict(payload.get("gates") or {})
    queue_descriptor = dict(payload.get("review_queue") or {})
    template_descriptor = dict(payload.get("pending_signoff_template") or {})
    index_descriptor = dict(payload.get("index") or {})

    descriptors_ok = True
    for descriptor in (queue_descriptor, template_descriptor, index_descriptor):
        relative = descriptor.get("path")
        if not isinstance(relative, str):
            descriptors_ok = False
            continue
        try:
            relative = require_safe_relative_path(relative, "human review descriptor")
            path = ROOT / relative
        except RuntimeError:
            descriptors_ok = False
            continue
        descriptors_ok = descriptors_ok and (
            path.is_file()
            and not path.is_symlink()
            and descriptor.get("sha256") == sha256_file(path)
            and _sidecar_valid(path)
        )

    ok = (
        payload.get("schema_version")
        == "webarena_verified_native_claim_human_review_acceptance/v1"
        and payload.get("status") == "ready_for_real_human_review"
        and payload.get("formal_launch_eligible") is False
        and payload.get("authorizes_formal_lock") is False
        and payload.get("expected_count") == 812
        and counts
        == {
            "queue_items": 812,
            "pending_human_review": 812,
            "human_signed": 0,
            "approved": 0,
            "formal_locks": 0,
        }
        and all(
            gates.get(name) is True
            for name in (
                "queue_denominator_exact",
                "source_pointers_current",
                "contract_and_checklist_hashes_current",
                "decision_fields_blank",
                "secret_scan_passed",
                "upstream_machine_package_current",
                "upstream_formal_locks_absent",
            )
        )
        and gates.get("human_signoff_complete") is False
        and descriptors_ok
        and _sidecar_valid(HUMAN_REVIEW_ACCEPTANCE)
    )
    return {
        "status": "pass" if ok else "fail",
        "queue_item_count": int(counts.get("queue_items") or 0),
        "pending_human_review_count": int(
            counts.get("pending_human_review") or 0
        ),
        "human_signed_count": int(counts.get("human_signed") or 0),
        "authorizes_human_signoff": False,
        "scope": "reviewer-work-package-readiness-not-human-approval",
        "evidence": evidence,
    }


def validate_scheduler_aggregate() -> dict[str, dict[str, Any]]:
    preview, preview_error = _load_optional_receipt(MACHINE_PREVIEW_ACCEPTANCE)
    preview_ref = evidence_ref(MACHINE_PREVIEW_ACCEPTANCE)
    if preview is None:
        preview_gate = {
            "status": "fail" if preview_error else "pending",
            "reason": preview_error or "machine schedule preview is missing",
            "evidence": preview_ref,
        }
    else:
        counts = dict(preview.get("counts") or {})
        gates = dict(preview.get("gates") or {})
        preview_index, index_error = _load_optional_receipt(MACHINE_PREVIEW_INDEX)
        index_ok = False
        if preview_index is not None and index_error is None:
            try:
                webarena_verified_machine_preview.validate_machine_preview_index(
                    preview_index
                )
                frozen_slots = list(load_json(FROZEN_MANIFEST).get("record_slots") or [])
                preview_slots = list(preview_index.get("record_slots") or [])
                index_ok = (
                    len(frozen_slots) == 2436
                    and len(preview_slots) == 2436
                    and all(
                        {
                            field: slot.get(field)
                            for field in (
                                "record_slot_id",
                                "task_id",
                                "agent_id",
                                "model",
                                "server_id",
                                "revision",
                                "seed",
                            )
                        }
                        == {
                            field: frozen.get(field)
                            for field in (
                                "record_slot_id",
                                "task_id",
                                "agent_id",
                                "model",
                                "server_id",
                                "revision",
                                "seed",
                            )
                        }
                        and slot.get("reset_policy")
                        == "recreate_task_sites_from_digest_v1"
                        and slot.get("reset_receipt_relative_path")
                        == "reset_receipt.json"
                        and slot.get("task_sites")
                        and slot.get("human_signoff_status") == "pending"
                        and slot.get("executable") is False
                        for slot, frozen in zip(preview_slots, frozen_slots, strict=True)
                    )
                    and preview.get("index_path")
                    == repo_relative(MACHINE_PREVIEW_INDEX)
                    and preview.get("index_sha256")
                    == sha256_file(MACHINE_PREVIEW_INDEX)
                    and _sidecar_valid(MACHINE_PREVIEW_INDEX)
                )
            except (RuntimeError, TypeError, ValueError):
                index_ok = False
        preview_ok = (
            preview.get("schema_version")
            == "webarena_verified_machine_preview_acceptance/v1"
            and preview.get("status") == "blocked"
            and preview.get("mode") == "machine_preview_non_launchable"
            and preview.get("executable") is False
            and preview.get("formal_launch_eligible") is False
            and counts.get("preview_cases") == 812
            and counts.get("preview_record_slots") == 2436
            and counts.get("requested_cases") == 812
            and counts.get("requested_record_slots") == 2436
            and counts.get("fallback_contracts") == 0
            and counts.get("per_agent")
            == {"Agent A": 812, "Agent B": 812, "Agent C": 812}
            and counts.get("per_server")
            == {
                "webarena-gpt54-ord": 812,
                "webarena-claude47-ord": 812,
                "webarena-deepseek-v4pro-ord": 812,
            }
            and all(
                gates.get(name) is True
                for name in (
                    "agent_model_server_routes_exact",
                    "exact_2436_slot_product",
                    "exact_812_case_product",
                    "fallback_contracts_zero",
                    "machine_draft_contracts_exact",
                    "paired_seed_policy_exact",
                    "per_slot_reset_declared",
                )
            )
            and index_ok
            and _sidecar_valid(MACHINE_PREVIEW_ACCEPTANCE)
        )
        preview_gate = {
            "status": "pass" if preview_ok else "fail",
            "mode": "proof_only_non_launchable",
            "case_count": int(counts.get("preview_cases") or 0),
            "record_slot_count": int(counts.get("preview_record_slots") or 0),
            "per_agent": dict(counts.get("per_agent") or {}),
            "fallback_contract_count": int(counts.get("fallback_contracts") or 0),
            "all_2436_slots_declare_reset": index_ok,
            "formal_launch_eligible": False,
            "evidence": {
                "acceptance": preview_ref,
                "index": evidence_ref(MACHINE_PREVIEW_INDEX),
            },
        }

    formal, formal_error = _load_optional_receipt(FORMAL_SCHEDULER_ACCEPTANCE)
    formal_ref = evidence_ref(FORMAL_SCHEDULER_ACCEPTANCE)
    if formal is None:
        fail_closed_gate = {
            "status": "fail" if formal_error else "pending",
            "reason": formal_error or "formal scheduler dry-run receipt is missing",
            "evidence": formal_ref,
        }
        formal_jobs_gate = {
            "status": "fail" if formal_error else "pending",
            "planned_record_slot_count": 0,
            "materialized_record_slot_count": 0,
            "fallback_contract_count": None,
            "formal_launch_eligible": False,
            "reason": formal_error or "formal 2,436-job scheduler receipt is missing",
            "evidence": formal_ref,
        }
    else:
        counts = dict(formal.get("counts") or {})
        gates = dict(formal.get("gates") or {})
        blocked_safely = (
            formal.get("schema_version")
            == "webarena_verified_full_812_scheduler_acceptance/v1"
            and formal.get("status") == "blocked"
            and formal.get("formal_launch_eligible") is False
            and formal.get("dry_run") is True
            and counts.get("requested_cases") == 812
            and counts.get("requested_record_slots") == 2436
            and counts.get("planned_record_slots") == 0
            and counts.get("fallback_contracts") == 0
            and gates.get("locked_contract_fallback_disabled") is True
            and gates.get("no_jobs_written_before_all_gates_pass") is True
            and gates.get("remote_dotenv_sync_allowed") is False
            and _sidecar_valid(FORMAL_SCHEDULER_ACCEPTANCE)
        )
        fail_closed_gate = {
            "status": "pass" if blocked_safely else "fail",
            "scheduler_state": "correctly_blocked_pre_human_lock",
            "planned_record_slot_count": int(
                counts.get("planned_record_slots") or 0
            ),
            "fallback_contract_count": int(counts.get("fallback_contracts") or 0),
            "jobs_written": False,
            "formal_launch_eligible": False,
            "evidence": formal_ref,
        }
        formal_jobs_gate = {
            "status": "pending" if blocked_safely else "fail",
            "planned_record_slot_count": int(
                counts.get("planned_record_slots") or 0
            ),
            "materialized_record_slot_count": 0,
            "fallback_contract_count": int(counts.get("fallback_contracts") or 0),
            "formal_launch_eligible": False,
            "reason": (
                "formal 2,436-job materialization correctly awaits all 812 human locks"
                if blocked_safely
                else "formal scheduler receipt is present but neither safely blocked nor accepted"
            ),
            "evidence": formal_ref,
        }

        if formal.get("status") == "pass":
            expected_per_agent = {
                "Agent A": 812,
                "Agent B": 812,
                "Agent C": 812,
            }
            expected_per_server = {
                "webarena-gpt54-ord": 812,
                "webarena-claude47-ord": 812,
                "webarena-deepseek-v4pro-ord": 812,
            }
            formal_inputs = dict(formal.get("inputs") or {})
            launch_authorization = dict(formal.get("launch_authorization") or {})
            waiver_sha256 = (
                sha256_file(OPERATOR_WAIVER) if OPERATOR_WAIVER.is_file() else None
            )
            waiver_binding_ok = (
                waiver_sha256 is not None
                and _sidecar_valid(OPERATOR_WAIVER)
                and launch_authorization.get("basis")
                == "operator_machine_only_waiver"
                and launch_authorization.get("status")
                == "authorized_machine_only_not_human_signoff"
                and launch_authorization.get("human_signoff_claimed") is False
                and launch_authorization.get("human_signed_count") == 0
                and launch_authorization.get("human_review_requirement_waived")
                is True
                and launch_authorization.get("operator_waiver_path")
                == repo_relative(OPERATOR_WAIVER)
                and launch_authorization.get("operator_waiver_sha256")
                == waiver_sha256
                and formal_inputs.get("operator_waiver_path")
                == repo_relative(OPERATOR_WAIVER)
                and formal_inputs.get("operator_waiver_sha256") == waiver_sha256
                and formal_inputs.get("native_claim_acceptance_sha256")
                == (
                    sha256_file(NATIVE_CLAIM_ACCEPTANCE)
                    if NATIVE_CLAIM_ACCEPTANCE.is_file()
                    else None
                )
            )
            formal_plan_ok = (
                formal.get("schema_version")
                == "webarena_verified_full_812_scheduler_acceptance/v1"
                and formal.get("formal_launch_eligible") is True
                and formal.get("result_namespace")
                == "webarena_verified_v1_2_3_full_812"
                and counts.get("requested_cases") == 812
                and counts.get("planned_cases") == 812
                and counts.get("requested_record_slots") == 2436
                and counts.get("planned_record_slots") == 2436
                and counts.get("unique_record_slot_ids") == 2436
                and counts.get("requested_per_agent") == expected_per_agent
                and counts.get("planned_per_agent") == expected_per_agent
                and counts.get("locked_contracts") == 812
                and counts.get("fallback_contracts") == 0
                and dict(formal.get("routing") or {}).get("planned_per_server")
                == expected_per_server
                and all(
                    gates.get(name) is True
                    for name in (
                        "step19_manifest_frozen_and_self_consistent",
                        "source_bundle_exact_812",
                        "native_claim_formal_launch_eligible",
                        "operator_machine_only_waiver_valid",
                        "locked_contract_set_exact_812",
                        "locked_contract_fallback_disabled",
                        "requested_equals_planned_per_agent",
                        "record_slot_ids_exact_and_unique",
                        "paired_seed_policy_exact",
                        "agent_model_server_route_exact",
                        "controller_ssh_public_key_transport_lock_exact",
                    )
                )
                and gates.get("remote_dotenv_sync_allowed") is False
                and waiver_binding_ok
                and not list(formal.get("blocking_reasons") or [])
                and _sidecar_valid(FORMAL_SCHEDULER_ACCEPTANCE)
            )
            materialization = dict(formal.get("materialization") or {})
            jobs_root_value = materialization.get("jobs_root")
            index_value = materialization.get("index_path")
            materialized_ok = False
            job_count = 0
            if (
                formal_plan_ok
                and formal.get("dry_run") is False
                and isinstance(jobs_root_value, str)
                and isinstance(index_value, str)
            ):
                try:
                    jobs_root_relative = require_safe_relative_path(
                        jobs_root_value, "formal jobs root"
                    )
                    index_relative = require_safe_relative_path(
                        index_value, "formal jobs index"
                    )
                    jobs_root = ROOT / jobs_root_relative
                    index_path = ROOT / index_relative
                    index_payload = load_json(index_path)
                    entries = list(index_payload.get("entries") or [])
                    jobs: list[dict[str, Any]] = []
                    descriptors_ok = (
                        jobs_root.resolve() == FORMAL_SCHEDULER_JOBS_ROOT.resolve()
                        and index_path.resolve() == (jobs_root / "index.json").resolve()
                        and index_path.is_file()
                        and not index_path.is_symlink()
                        and _sidecar_valid(index_path)
                        and index_payload.get("schema_version")
                        == "webarena_verified_full_812_schedule_index/v1"
                        and index_payload.get("job_count") == 2436
                        and index_payload.get("result_namespace")
                        == "webarena_verified_v1_2_3_full_812"
                        and index_payload.get("launch_authorization")
                        == launch_authorization
                        and len(entries) == 2436
                        and materialization.get("job_count") == 2436
                        and materialization.get("index_sha256")
                        == sha256_file(index_path)
                    )
                    for position, descriptor in enumerate(entries):
                        if not isinstance(descriptor, Mapping):
                            descriptors_ok = False
                            break
                        relative = descriptor.get("path")
                        if not isinstance(relative, str):
                            descriptors_ok = False
                            break
                        relative = require_safe_relative_path(
                            relative, f"formal job descriptor {position}"
                        )
                        if "/" in relative:
                            descriptors_ok = False
                            break
                        path = jobs_root / relative
                        if (
                            descriptor.get("position") != position
                            or not path.is_file()
                            or path.is_symlink()
                            or descriptor.get("sha256") != sha256_file(path)
                        ):
                            descriptors_ok = False
                            break
                        job = load_json(path)
                        policy_lock = (
                            dict(job.get("formal_policy_lock") or {})
                            if isinstance(job, Mapping)
                            else {}
                        )
                        task_id_value = (
                            str(job.get("task_id"))
                            if isinstance(job, Mapping)
                            else ""
                        )
                        packet_path = PACKETS_ROOT / task_id_value / "case_packet.md"
                        locked_contract_path = (
                            NATIVE_CLAIM_ACCEPTANCE.parent
                            / "locked"
                            / "contracts"
                            / task_id_value
                            / "evidence_contract.json"
                        )
                        if (
                            not isinstance(job, Mapping)
                            or descriptor.get("record_slot_id")
                            != job.get("record_slot_id")
                            or descriptor.get("job_id") != job.get("job_id")
                            or job.get("reset_policy")
                            != "recreate_task_sites_from_digest_v1"
                            or job.get("reset_receipt_relative_path")
                            != "reset_receipt.json"
                            or job.get("result_namespace")
                            != "webarena_verified_v1_2_3_full_812"
                            or policy_lock.get("basis")
                            != "operator_machine_only_waiver"
                            or policy_lock.get("operator_waiver_sha256")
                            != waiver_sha256
                            or policy_lock.get("human_signoff_claimed") is not False
                            or policy_lock.get("human_signed_count") != 0
                            or policy_lock.get("native_claim_acceptance_sha256")
                            != formal_inputs.get("native_claim_acceptance_sha256")
                            or policy_lock.get("native_claim_index_sha256")
                            != formal_inputs.get("native_claim_index_sha256")
                            or policy_lock.get("source_bundle_sha256")
                            != formal_inputs.get("source_bundle_sha256")
                            or policy_lock.get("step19_manifest_sha256")
                            != formal_inputs.get("step19_manifest_sha256")
                            or policy_lock.get("model") != job.get("requested_model")
                            or policy_lock.get("server_id")
                            != dict(job.get("execution_target") or {}).get("server_id")
                            or policy_lock.get("reset_policy")
                            != job.get("reset_policy")
                            or not packet_path.is_file()
                            or packet_path.is_symlink()
                            or policy_lock.get("case_packet_sha256")
                            != sha256_file(packet_path)
                            or not locked_contract_path.is_file()
                            or locked_contract_path.is_symlink()
                            or policy_lock.get("locked_contract_file_sha256")
                            != sha256_file(locked_contract_path)
                        ):
                            descriptors_ok = False
                            break
                        jobs.append(dict(job))
                    if descriptors_ok:
                        frozen_slots = list(
                            load_json(FROZEN_MANIFEST).get("record_slots") or []
                        )
                        webarena_verified_full._validate_planned_jobs(
                            jobs,
                            slots=frozen_slots,
                        )
                        materialized_ok = (
                            len(jobs) == 2436
                            and index_payload.get("jobs_sha256")
                            == core_sha256_object(jobs)
                            and index_payload.get("jobs_sha256")
                            == dict(formal.get("schedule") or {}).get("jobs_sha256")
                        )
                        job_count = len(jobs)
                except (
                    OSError,
                    RuntimeError,
                    TypeError,
                    ValueError,
                    json.JSONDecodeError,
                    webarena_verified_full.WebArenaFullScheduleError,
                ):
                    materialized_ok = False

            formal_jobs_gate = {
                "status": (
                    "pass"
                    if formal_plan_ok and materialized_ok
                    else "pending"
                    if formal_plan_ok
                    else "fail"
                ),
                "planned_record_slot_count": int(
                    counts.get("planned_record_slots") or 0
                ),
                "materialized_record_slot_count": job_count,
                "fallback_contract_count": int(
                    counts.get("fallback_contracts") or 0
                ),
                "formal_launch_eligible": bool(
                    formal_plan_ok and materialized_ok
                ),
                "all_2436_jobs_declare_reset": materialized_ok,
                "all_2436_jobs_bind_operator_waiver": materialized_ok,
                "operator_waiver_sha256": waiver_sha256,
                "human_signoff_claimed": False,
                "human_signed_count": 0,
                "result_namespace": formal.get("result_namespace"),
                "reason": (
                    None
                    if formal_plan_ok and materialized_ok
                    else "accepted formal plan exists but exact 2,436-job materialization is missing"
                    if formal_plan_ok
                    else "formal scheduler acceptance fails exact product/lock/route checks"
                ),
                "evidence": {
                    "acceptance": formal_ref,
                    "jobs_index": (
                        evidence_ref(ROOT / str(index_value))
                        if isinstance(index_value, str)
                        and not Path(index_value).is_absolute()
                        else {"exists": False}
                    ),
                },
            }
            fail_closed_gate = {
                "status": "pass" if formal_plan_ok else "fail",
                "scheduler_state": (
                    "formal_operator_policy_lock_accepted_after_fail_closed_validation"
                    if formal_plan_ok
                    else "formal_scheduler_acceptance_invalid"
                ),
                "planned_record_slot_count": int(
                    counts.get("planned_record_slots") or 0
                ),
                "fallback_contract_count": int(
                    counts.get("fallback_contracts") or 0
                ),
                "jobs_written": bool(formal_plan_ok and materialized_ok),
                "formal_launch_eligible": bool(formal_plan_ok and materialized_ok),
                "evidence": formal_ref,
            }
    return {
        "scheduler_exact_812x3_machine_proof": preview_gate,
        "scheduler_prelock_fail_closed": fail_closed_gate,
        "scheduler_formal_812x3_jobs": formal_jobs_gate,
    }


def validate_golden_parity_aggregate() -> dict[str, Any]:
    payload, error = _load_optional_receipt(GOLDEN_PARITY_ACCEPTANCE)
    evidence = evidence_ref(GOLDEN_PARITY_ACCEPTANCE)
    if payload is None:
        return {
            "status": "fail" if error else "pending",
            "reason": error or "official CLI/adapter parity receipt is missing",
            "evidence": evidence,
        }
    categories = set(payload.get("categories") or [])
    expected_hosts = {item["server_id"] for item in expected_servers().values()}
    host_receipts = [
        item for item in payload.get("host_receipts") or [] if isinstance(item, Mapping)
    ]
    host_receipts_ok = len(host_receipts) == 3
    for item in host_receipts:
        relative = item.get("path")
        if not isinstance(relative, str):
            host_receipts_ok = False
            continue
        try:
            relative = require_safe_relative_path(relative, "golden host receipt")
        except RuntimeError:
            host_receipts_ok = False
            continue
        path = ROOT / relative
        receipt, receipt_error = _load_optional_receipt(path)
        host_receipts_ok = host_receipts_ok and (
            path.is_file()
            and not path.is_symlink()
            and item.get("status") == "pass"
            and item.get("sha256") == sha256_file(path)
            and receipt is not None
            and receipt_error is None
            and receipt.get("schema_version")
            == "webarena_verified_golden_parity/v1"
            and receipt.get("status") == "pass"
            and receipt.get("fixture_count") == 6
            and receipt.get("raw_cli_adapter_exact_match_count") == 6
        )
    fixtures = [
        item for item in payload.get("fixtures") or [] if isinstance(item, Mapping)
    ]
    expected_fixture_ids = {
        "response_only_success",
        "response_only_failure",
        "network_mutation_success",
        "network_mutation_failure",
        "multisite_success",
        "multisite_failure",
    }
    fixtures_ok = (
        len(fixtures) == 6
        and {str(item.get("fixture_id")) for item in fixtures}
        == expected_fixture_ids
        and all(
            item.get("matching_host_count") == 3
            and item.get("expected_status") in {"success", "failure"}
            and SHA256_PATTERN.fullmatch(
                str(item.get("canonical_official_result_sha256") or "")
            )
            is not None
            for item in fixtures
        )
    )
    ok = (
        payload.get("schema_version")
        == "webarena_verified_golden_parity_aggregate/v1"
        and payload.get("status") == "pass"
        and payload.get("host_count") == 3
        and payload.get("fixture_count_per_host") == 6
        and payload.get("total_raw_cli_adapter_comparisons") == 18
        and payload.get("exact_raw_cli_adapter_comparisons") == 18
        and payload.get("cross_host_canonical_result_match_count") == 6
        and set(payload.get("host_ids") or []) == expected_hosts
        and len(payload.get("host_ids") or []) == 3
        and {str(item.get("host_id")) for item in host_receipts}
        == expected_hosts
        and host_receipts_ok
        and fixtures_ok
        and payload.get("official_evaluator_image") == EXPECTED_IMAGE
        and payload.get("official_dataset_sha256") == EXPECTED_DATA_CHECKSUM
        and payload.get("task_contract_index_sha256")
        == EXPECTED_TASK_CONTRACT_INDEX_SHA256
        and payload.get("private_evaluator_payload_in_aggregate") is False
        and categories
        == {
            "agent_response_only_retrieval",
            "multi_site_network_event",
            "network_event_mutation",
        }
        and _sidecar_valid(GOLDEN_PARITY_ACCEPTANCE)
    )
    return {
        "status": "pass" if ok else "fail",
        "host_count": int(payload.get("host_count") or 0),
        "fixture_count_per_host": int(payload.get("fixture_count_per_host") or 0),
        "exact_cli_adapter_comparison_count": int(
            payload.get("exact_raw_cli_adapter_comparisons") or 0
        ),
        "cross_host_canonical_match_count": int(
            payload.get("cross_host_canonical_result_match_count") or 0
        ),
        "evidence": evidence,
    }


def validate_reset_smoke_aggregate() -> dict[str, Any]:
    payload, error = _load_optional_receipt(RESET_SMOKE_ACCEPTANCE)
    evidence = evidence_ref(RESET_SMOKE_ACCEPTANCE)
    if payload is None:
        return {
            "status": "fail" if error else "pending",
            "reason": error or "real reset smoke receipt is missing",
            "evidence": evidence,
        }
    counts = dict(payload.get("counts") or {})
    gates = dict(payload.get("gates") or {})
    sites = {str(item.get("site")) for item in payload.get("entries") or []}
    expected_sites = {"shopping", "shopping_admin", "reddit", "gitlab"}
    ok = (
        payload.get("schema_version")
        == "webarena_verified_real_reset_smoke_acceptance/v1"
        and payload.get("status") == "pass"
        and counts.get("expected_receipts") == 12
        and counts.get("observed_receipts") == 12
        and counts.get("validated_entries") == 12
        and sites == expected_sites
        and all(value is True for value in gates.values())
        and _sidecar_valid(RESET_SMOKE_ACCEPTANCE)
    )
    return {
        "status": "pass" if ok else "fail",
        "validated_slot_reset_count": int(counts.get("validated_entries") or 0),
        "validated_host_count": 3 if ok else 0,
        "covered_sites": sorted(sites),
        "covered_site_count": len(sites),
        "required_site_count": 6,
        "all_six_sites_covered": sites == set(
            ("shopping", "shopping_admin", "reddit", "gitlab", "wikipedia", "map")
        ),
        "scope": "real four-site reset smoke; not full six-site deployment proof",
        "evidence": evidence,
    }


def validate_extended_reset_aggregate() -> dict[str, Any]:
    payload, error = _load_optional_receipt(EXTENDED_RESET_ACCEPTANCE)
    evidence = evidence_ref(EXTENDED_RESET_ACCEPTANCE)
    if payload is None:
        return {
            "status": "fail" if error else "pending",
            "validated_receipt_count": 0,
            "required_receipt_count": 6,
            "covered_sites": [],
            "reason": error or "task 97/759 three-host extended reset receipt is missing",
            "evidence": evidence,
        }
    counts = dict(payload.get("counts") or {})
    gates = dict(payload.get("gates") or {})
    expected = dict(payload.get("expected") or {})
    tasks = [item for item in expected.get("tasks") or [] if isinstance(item, Mapping)]
    task_scopes = {
        int(item.get("task_id", -1)): list(item.get("reset_scope") or [])
        for item in tasks
    }
    entries = [item for item in payload.get("entries") or [] if isinstance(item, Mapping)]
    expected_machine_ids = {
        item["server_id"] for item in expected_servers().values()
    }
    observed_machine_ids = {str(item.get("machine_id")) for item in entries}
    observed_slots = {
        (str(item.get("machine_id")), int(item.get("task_id", -1)))
        for item in entries
    }
    expected_slots = {
        (machine_id, task_id)
        for machine_id in expected_machine_ids
        for task_id in (97, 759)
    }
    covered_sites = sorted(
        {site for scope in task_scopes.values() for site in scope}
    )
    entries_ok = len(entries) == 6 and all(
        item.get("status") == "pass"
        and list(item.get("expected_reset_scope") or [])
        == task_scopes.get(int(item.get("task_id", -1)))
        and len(item.get("sites") or []) == 2
        and [str(site.get("site")) for site in item.get("sites") or []]
        == task_scopes.get(int(item.get("task_id", -1)))
        and all(value is True for value in dict(item.get("flags") or {}).values())
        and len(dict(item.get("flags") or {})) == 7
        for item in entries
    )
    cross_host = [
        item
        for item in payload.get("cross_host_consistency") or []
        if isinstance(item, Mapping)
    ]
    cross_host_ok = len(cross_host) == 4 and all(
        item.get("host_count") == 3
        and item.get("digest_and_sentinels_identical") is True
        and item.get("fresh_container_ids_unique_across_hosts") is True
        for item in cross_host
    )
    structural_ok = (
        payload.get("schema_version")
        == "webarena_verified_extended_real_reset_acceptance/v1"
        and counts.get("expected_receipts") == 6
        and counts.get("observed_receipts") == 6
        and counts.get("validated_receipts") == 6
        and counts.get("expected_site_rows") == 12
        and counts.get("observed_validated_site_rows") == 12
        and counts.get("blocking_reasons") == 0
        and task_scopes
        == {
            97: ["wikipedia", "map"],
            759: ["shopping_admin", "map"],
        }
        and set(expected.get("machine_ids") or []) == expected_machine_ids
        and observed_machine_ids == expected_machine_ids
        and observed_slots == expected_slots
        and entries_ok
        and cross_host_ok
        and all(value is True for value in gates.values())
        and len(gates) == 12
        and not list(payload.get("blocking_reasons") or [])
        and _sidecar_valid(EXTENDED_RESET_ACCEPTANCE)
    )
    if payload.get("status") == "pass" and structural_ok:
        status = "pass"
        reason = None
    elif int(counts.get("observed_receipts") or 0) < 6:
        status = "pending"
        reason = "fewer than six real task 97/759 reset receipts are present"
    else:
        status = "fail"
        reason = "extended reset receipt is present but fails strict validation"
    return {
        "status": status,
        "validated_receipt_count": int(counts.get("validated_receipts") or 0),
        "required_receipt_count": 6,
        "validated_site_row_count": int(
            counts.get("observed_validated_site_rows") or 0
        ),
        "required_site_row_count": 12,
        "task_ids": sorted(task_scopes),
        "validated_host_count": len(observed_machine_ids),
        "covered_sites": covered_sites,
        "reason": reason,
        "evidence": evidence,
    }


def validate_full_six_site_reset_coverage(
    base_reset: Mapping[str, Any],
    extended_reset: Mapping[str, Any],
) -> dict[str, Any]:
    required_sites = {
        "shopping",
        "shopping_admin",
        "reddit",
        "gitlab",
        "wikipedia",
        "map",
    }
    base_sites = set(base_reset.get("covered_sites") or [])
    extended_sites = set(extended_reset.get("covered_sites") or [])
    covered_sites = base_sites | extended_sites
    base_ok = (
        base_reset.get("status") == "pass"
        and base_reset.get("validated_slot_reset_count") == 12
        and base_reset.get("validated_host_count") == 3
        and base_sites
        == {"shopping", "shopping_admin", "reddit", "gitlab"}
    )
    extended_ok = (
        extended_reset.get("status") == "pass"
        and extended_reset.get("validated_receipt_count") == 6
        and extended_reset.get("validated_site_row_count") == 12
        and extended_reset.get("validated_host_count") == 3
        and set(extended_reset.get("task_ids") or []) == {97, 759}
        and extended_sites == {"shopping_admin", "wikipedia", "map"}
    )
    coverage_ok = covered_sites == required_sites
    if base_ok and extended_ok and coverage_ok:
        status = "pass"
        reason = None
    elif base_reset.get("status") == "fail" or extended_reset.get("status") == "fail":
        status = "fail"
        reason = "one reset component has a present but invalid acceptance receipt"
    else:
        status = "pending"
        reason = (
            "requires both the existing four-site 12/12 smoke and the task "
            "97/759 three-host 6/6 extended reset acceptance"
        )
    return {
        "status": status,
        "base_four_site_smoke_status": base_reset.get("status"),
        "base_validated_receipt_count": int(
            base_reset.get("validated_slot_reset_count") or 0
        ),
        "base_required_receipt_count": 12,
        "extended_reset_status": extended_reset.get("status"),
        "extended_validated_receipt_count": int(
            extended_reset.get("validated_receipt_count") or 0
        ),
        "extended_required_receipt_count": 6,
        "covered_sites": sorted(covered_sites),
        "covered_site_count": len(covered_sites),
        "required_sites": sorted(required_sites),
        "required_site_count": 6,
        "all_six_sites_covered": coverage_ok,
        "reason": reason,
        "evidence": {
            "base_four_site": base_reset.get("evidence"),
            "extended_task_97_759": extended_reset.get("evidence"),
        },
    }


def validate_site_data_lock_aggregate() -> dict[str, Any]:
    payload, error = _load_optional_receipt(SITE_DATA_LOCK_ACCEPTANCE)
    evidence = evidence_ref(SITE_DATA_LOCK_ACCEPTANCE)
    if payload is None:
        return {
            "status": "fail" if error else "pending",
            "reason": error or "three-host site data lock acceptance is missing",
            "evidence": evidence,
        }
    gates = dict(payload.get("gates") or {})
    assets = dict(payload.get("assets") or {})
    expected_assets = {
        "nominatim_volumes.tar",
        "osm_tile_server.tar",
        "osrm_routing.tar",
        "wikipedia_en_all_maxi_2022-05.zim",
    }
    host_ids = {
        str(item.get("machine_id"))
        for item in payload.get("hosts") or []
        if isinstance(item, Mapping)
    }
    expected_ids = {item["server_id"] for item in expected_servers().values()}
    ok = (
        payload.get("schema_version")
        == "webarena_verified_site_data_lock_acceptance/v1"
        and payload.get("status") == "pass"
        and payload.get("benchmark_version") == "v1.2.3"
        and payload.get("official_commit") == EXPECTED_COMMIT
        and payload.get("remote_mode") == "0600"
        and payload.get("data_lock_sha256")
        == "ac17f74d63f65461f3264eae87f8131afe42021441efad50cad83ae005344179"
        and set(assets) == expected_assets
        and host_ids == expected_ids
        and all(value is True for value in gates.values())
        and _sidecar_valid(SITE_DATA_LOCK_ACCEPTANCE)
    )
    return {
        "status": "pass" if ok else "fail",
        "host_count": len(host_ids),
        "asset_count": len(assets),
        "data_lock_sha256": payload.get("data_lock_sha256"),
        "all_three_host_locks_byte_identical": bool(
            gates.get("all_three_host_locks_byte_identical")
        ),
        "scope": "site data lock only; does not prove containers or login",
        "evidence": evidence,
    }


def validate_site_deployment_aggregate() -> dict[str, Any]:
    servers_by_host = expected_servers()
    identities = {
        item["server_id"]: {
            "ssh_host": host,
            "ssh_host_fingerprint": item["ssh_host_ed25519_fingerprint"],
        }
        for host, item in servers_by_host.items()
    }
    expected_ids = sorted(identities)
    expected_paths = {
        machine_id: SITE_DEPLOYMENT_RECEIPTS / f"{machine_id}.json"
        for machine_id in expected_ids
    }
    diagnostic_paths = (
        sorted(
            path
            for path in SITE_DEPLOYMENT_RECEIPTS.rglob("*.json")
            if path.is_file() and path.parent != SITE_DEPLOYMENT_RECEIPTS
        )
        if SITE_DEPLOYMENT_RECEIPTS.is_dir()
        else []
    )
    present = [machine_id for machine_id, path in expected_paths.items() if path.is_file()]
    evidence = [evidence_ref(expected_paths[machine_id]) for machine_id in expected_ids]
    if len(present) != 3:
        return {
            "status": "pending",
            "validated_host_count": 0,
            "required_host_count": 3,
            "present_receipt_count": len(present),
            "required_sites": list(
                ("shopping", "shopping_admin", "reddit", "gitlab", "wikipedia", "map")
            ),
            "login_verification_complete": False,
            "reason": "three complete six-site deployment/login receipts are not present",
            "canonical_receipts_only": True,
            "ignored_nonpassing_diagnostic_receipt_count": len(diagnostic_paths),
            "ignored_nonpassing_diagnostic_receipts": [
                evidence_ref(path) for path in diagnostic_paths
            ],
            "evidence": evidence,
        }
    required_sites = {
        "shopping",
        "shopping_admin",
        "reddit",
        "gitlab",
        "wikipedia",
        "map",
    }
    valid = True
    for machine_id, path in expected_paths.items():
        payload, error = _load_optional_receipt(path)
        if payload is None or error:
            valid = False
            continue
        observed_sites = {
            str(item.get("site"))
            for item in payload.get("sites") or []
            if isinstance(item, Mapping)
        }
        login = dict(payload.get("login") or {})
        resets = [
            item for item in payload.get("resets") or [] if isinstance(item, Mapping)
        ]
        site_rows = [
            item for item in payload.get("sites") or [] if isinstance(item, Mapping)
        ]
        identity = identities[machine_id]
        valid = valid and (
            payload.get("schema_version")
            == "webarena_verified_site_deployment_receipt/v1"
            and payload.get("status") == "pass"
            and payload.get("operation") == "deploy_and_accept"
            and payload.get("machine_id") == machine_id
            and payload.get("ssh_host") == identity["ssh_host"]
            and payload.get("ssh_host_fingerprint")
            == identity["ssh_host_fingerprint"]
            and payload.get("site_lock_sha256")
            == "b643c27c0031ce4a1c70c12a70824c77a942795609c6931eb433ec3c2e147ecc"
            and payload.get("error") is None
            and observed_sites == required_sites
            and len(site_rows) == 6
            and all(
                item.get("site") in required_sites
                and item.get("ok") is True
                and dict(item.get("container") or {}).get("running") is True
                and item.get("expected_image_id")
                == dict(item.get("container") or {}).get("image_id")
                and all(
                    sentinel.get("ok") is True
                    for sentinel in item.get("sentinels") or []
                    if isinstance(sentinel, Mapping)
                )
                and bool(item.get("sentinels"))
                for item in site_rows
            )
            and len(resets) == 6
            and {str(item.get("site")) for item in resets} == required_sites
            and all(
                item.get("ok") is True
                and dict(item.get("after") or {}).get("running") is True
                and item.get("expected_image_id")
                == dict(item.get("after") or {}).get("image_id")
                and all(
                    sentinel.get("ok") is True
                    for sentinel in item.get("sentinels") or []
                    if isinstance(sentinel, Mapping)
                )
                and bool(item.get("sentinels"))
                for item in resets
            )
            and login.get("status") == "pass"
            and login.get("sensitive_state_retained") is False
            and set(login.get("required_sites") or [])
            == {"shopping", "shopping_admin", "reddit", "gitlab"}
            and login.get("generated_state_file_count") == 8
            and login.get("validated_authenticated_page_probe_count") == 12
            and int(
                login.get("validated_effective_associated_nonempty_cookie_count")
                or 0
            )
            > 0
        )
    return {
        "status": "pass" if valid else "fail",
        "validated_host_count": 3 if valid else 0,
        "required_host_count": 3,
        "present_receipt_count": 3,
        "required_sites": sorted(required_sites),
        "login_verification_complete": valid,
        "sensitive_login_state_retained": False if valid else None,
        "canonical_receipts_only": True,
        "ignored_nonpassing_diagnostic_receipt_count": len(diagnostic_paths),
        "ignored_nonpassing_diagnostic_receipts": [
            evidence_ref(path) for path in diagnostic_paths
        ],
        "evidence": evidence,
    }


def validate_real_browser_acceptance() -> dict[str, Any]:
    """Validate the real-browser six-site and authenticated-page evidence tree."""

    payload, error = _load_optional_receipt(BROWSER_ACCEPTANCE)
    evidence = evidence_ref(BROWSER_ACCEPTANCE)
    if payload is None:
        return {
            "status": "fail" if error else "pending",
            "reason": error or "real browser acceptance receipt is missing",
            "validated_host_count": 0,
            "required_host_count": 3,
            "evidence": evidence,
        }
    required_sites = {
        "shopping",
        "shopping_admin",
        "reddit",
        "gitlab",
        "wikipedia",
        "map",
    }
    required_auth_sites = {"shopping", "shopping_admin", "reddit", "gitlab"}
    required_combinations = {
        "gitlab+shopping",
        "gitlab+shopping_admin",
        "gitlab+reddit",
        "shopping+shopping_admin",
        "gitlab",
        "shopping",
        "shopping_admin",
        "reddit",
    }
    expected = expected_servers()
    identities = {
        item["server_id"]: {
            "host": host,
            "fingerprint": item["ssh_host_ed25519_fingerprint"],
        }
        for host, item in expected.items()
    }
    counts = dict(payload.get("counts") or {})
    gates = dict(payload.get("gates") or {})
    machine_refs = [
        item for item in payload.get("machines") or [] if isinstance(item, Mapping)
    ]
    expected_gate_values = {
        "all_three_full_deploy_receipts_pass": True,
        "all_eighteen_http_sentinels_pass": True,
        "all_eighteen_real_browser_ui_sentinels_pass": True,
        "all_thirty_six_authenticated_controller_probes_pass": True,
        "ssh_fingerprints_strictly_verified": True,
        "all_tunnels_loopback_only": True,
        "browser_credentials_loaded": False,
        "browser_storage_loaded": False,
        "cookies_read_or_exported": False,
        "public_trace_cookie_headers_absent": True,
    }
    aggregate_ok = (
        payload.get("schema_version") == "webarena_verified_browser_acceptance/v1"
        and payload.get("status") == "pass"
        and payload.get("benchmark_version") == "v1.2.3"
        and dict(payload.get("site_lock") or {}).get("sha256")
        == "b643c27c0031ce4a1c70c12a70824c77a942795609c6931eb433ec3c2e147ecc"
        and dict(payload.get("tool") or {}).get("workflow") == "playwright-cli"
        and dict(payload.get("tool") or {}).get("real_browser") is True
        and counts.get("machines_expected") == 3
        and counts.get("machines_passed") == 3
        and counts.get("sites_per_machine_expected") == 6
        and counts.get("site_browser_probes_passed") == 18
        and counts.get("http_probes_passed") == 18
        and counts.get("authenticated_page_probes_validated") == 36
        and counts.get("authenticated_page_probe_types_referenced") == 12
        and counts.get("login_state_files_validated") == 24
        and int(counts.get("associated_cookies_validated") or 0) > 0
        and counts.get("public_traces") == 3
        and gates == expected_gate_values
        and len(machine_refs) == 3
        and {str(item.get("machine_id")) for item in machine_refs}
        == set(identities)
        and _sidecar_valid(BROWSER_ACCEPTANCE)
    )

    machine_ok = True
    validated_artifact_count = 0
    for reference in machine_refs:
        machine_id = str(reference.get("machine_id"))
        if machine_id not in identities:
            machine_ok = False
            continue
        expected_path = BROWSER_ACCEPTANCE_ROOT / f"{machine_id}.json"
        if (
            reference.get("path") != repo_relative(expected_path)
            or reference.get("sha256") != sha256_file(expected_path)
            if expected_path.is_file()
            else True
        ):
            machine_ok = False
            continue
        receipt, receipt_error = _load_optional_receipt(expected_path)
        if receipt is None or receipt_error:
            machine_ok = False
            continue
        identity = identities[machine_id]
        sites = [
            item for item in receipt.get("sites") or [] if isinstance(item, Mapping)
        ]
        authentication = dict(receipt.get("authentication") or {})
        isolation = dict(receipt.get("browser_isolation") or {})
        trace = dict(receipt.get("trace") or {})
        inventory = dict(receipt.get("artifact_inventory") or {})
        deployment_path = SITE_DEPLOYMENT_RECEIPTS / f"{machine_id}.json"
        try:
            deployment_label = repo_relative(deployment_path)
        except RuntimeError:
            deployment_label = None
        deployment_hash = (
            sha256_file(deployment_path)
            if deployment_path.is_file() and not deployment_path.is_symlink()
            else None
        )
        rows = [
            item for item in inventory.get("files") or [] if isinstance(item, Mapping)
        ]
        artifact_dir = BROWSER_ARTIFACT_ROOT / machine_id
        actual_files = sorted(path for path in artifact_dir.rglob("*") if path.is_file())
        actual_relative = {
            path.relative_to(BROWSER_ARTIFACT_ROOT).as_posix() for path in actual_files
        }
        row_paths = {str(row.get("path")) for row in rows}
        rows_ok = (
            len(rows) == inventory.get("file_count") == len(actual_files)
            and len(row_paths) == len(rows)
            and row_paths == actual_relative
            and all(
                SHA256_PATTERN.fullmatch(str(row.get("sha256") or "")) is not None
                and isinstance(row.get("size_bytes"), int)
                and int(row.get("size_bytes")) >= 0
                and (BROWSER_ARTIFACT_ROOT / str(row.get("path"))).is_file()
                and sha256_file(BROWSER_ARTIFACT_ROOT / str(row.get("path")))
                == row.get("sha256")
                and (BROWSER_ARTIFACT_ROOT / str(row.get("path"))).stat().st_size
                == row.get("size_bytes")
                for row in rows
            )
            and sum(int(row.get("size_bytes") or 0) for row in rows)
            == inventory.get("total_size_bytes")
            and hashlib.sha256(
                json.dumps(rows, sort_keys=True, separators=(",", ":")).encode(
                    "utf-8"
                )
            ).hexdigest()
            == inventory.get("tree_sha256")
        )
        validated_artifact_count += len(rows) if rows_ok else 0
        machine_ok = machine_ok and (
            receipt.get("schema_version")
            == "webarena_verified_browser_machine_acceptance/v1"
            and receipt.get("status") == "pass"
            and receipt.get("machine_id") == machine_id
            and receipt.get("ssh_host") == identity["host"]
            and receipt.get("ssh_host_fingerprint") == identity["fingerprint"]
            and dict(receipt.get("deployment_receipt") or {}).get("status")
            == "pass"
            and dict(receipt.get("deployment_receipt") or {}).get("operation")
            == "deploy_and_accept"
            and dict(receipt.get("deployment_receipt") or {}).get("path")
            == deployment_label
            and dict(receipt.get("deployment_receipt") or {}).get("sha256")
            == deployment_hash
            and len(sites) == 6
            and {str(item.get("site")) for item in sites} == required_sites
            and all(
                item.get("status") == "pass"
                and dict(item.get("http") or {}).get("status_code") == 200
                and dict(item.get("http") or {}).get("sentinel_match") is True
                and dict(item.get("http") or {}).get("loopback_tunnel") is True
                and dict(item.get("browser") or {}).get("ui_sentinel_match") is True
                and dict(item.get("browser") or {}).get("loopback_tunnel") is True
                and dict(item.get("browser") or {}).get("authenticated_state_loaded")
                is False
                for item in sites
            )
            and authentication.get("status") == "pass"
            and set(authentication.get("required_sites") or [])
            == required_auth_sites
            and set(authentication.get("required_state_combinations") or [])
            == required_combinations
            and authentication.get("validated_state_file_count") == 8
            and authentication.get("validated_authenticated_page_probe_count")
            == 12
            and int(
                authentication.get(
                    "validated_effective_associated_nonempty_cookie_count"
                )
                or 0
            )
            > 0
            and authentication.get("sensitive_state_retained") is False
            and isolation
            == {
                "binding": "127.0.0.1",
                "browser_storage_loaded": False,
                "cookies_read_or_exported": False,
                "credentials_loaded": False,
                "fresh_unauthenticated_context": True,
                "transport": "strict-fingerprint SSH local forwarding",
            }
            and trace.get("capture_mode") == "post-load offline action trace"
            and trace.get("authenticated_state_loaded") is False
            and trace.get("cookie_headers_present") is False
            and dict(trace.get("network") or {}).get("size_bytes") == 0
            and dict(trace.get("network") or {}).get("sha256")
            == hashlib.sha256(b"").hexdigest()
            and all(value is True for value in dict(receipt.get("gates") or {}).values())
            and len(dict(receipt.get("gates") or {})) == 6
            and rows_ok
        )

    ok = aggregate_ok and machine_ok
    return {
        "status": "pass" if ok else "fail",
        "validated_host_count": 3 if ok else 0,
        "required_host_count": 3,
        "validated_http_probe_count": int(counts.get("http_probes_passed") or 0),
        "validated_real_browser_probe_count": int(
            counts.get("site_browser_probes_passed") or 0
        ),
        "validated_authenticated_page_probe_count": int(
            counts.get("authenticated_page_probes_validated") or 0
        ),
        "validated_artifact_count": validated_artifact_count,
        "required_sites": sorted(required_sites),
        "real_browser": bool(dict(payload.get("tool") or {}).get("real_browser")),
        "sensitive_browser_state_retained": False if ok else None,
        "evidence": evidence,
    }


def validate_six_site_deployment_and_browser(
    deployment: Mapping[str, Any],
    browser: Mapping[str, Any],
) -> dict[str, Any]:
    if deployment.get("status") == "pass" and browser.get("status") == "pass":
        status = "pass"
        reason = None
    elif deployment.get("status") == "fail" or browser.get("status") == "fail":
        status = "fail"
        reason = "deployment or independent real-browser evidence is invalid"
    else:
        status = "pending"
        reason = "both canonical deployment/login and real-browser acceptance are required"
    return {
        "status": status,
        "deployment_receipt_status": deployment.get("status"),
        "real_browser_acceptance_status": browser.get("status"),
        "validated_host_count": (
            3 if status == "pass" else 0
        ),
        "required_host_count": 3,
        "required_site_count": 6,
        "login_verification_complete": status == "pass",
        "real_browser_verification_complete": status == "pass",
        "reason": reason,
        "evidence": {
            "deployment": deployment.get("evidence"),
            "browser": browser.get("evidence"),
        },
    }


def _value_contains_sensitive_material(value: Any) -> bool:
    if value in (None, False, "", [], {}):
        return False
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return False
        if normalized.lower() in {
            "none",
            "not_set",
            "redacted",
            "removed",
            "false",
            "controller_only",
        }:
            return False
        if re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", normalized):
            return False
    return True


def _json_sensitive_findings(
    value: Any,
    *,
    path: str,
    key_path: tuple[str, ...] = (),
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            normalized = key.lower().replace("-", "_")
            child_path = (*key_path, key)
            if (
                normalized in {item.replace("-", "_") for item in SENSITIVE_VALUE_KEYS}
                and _value_contains_sensitive_material(child)
            ):
                findings.append(
                    {
                        "path": path,
                        "finding_type": "sensitive_json_value",
                        "json_key_path": ".".join(child_path),
                    }
                )
            findings.extend(
                _json_sensitive_findings(child, path=path, key_path=child_path)
            )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(
                _json_sensitive_findings(
                    child,
                    path=path,
                    key_path=(*key_path, f"[{index}]"),
                )
            )
    return findings


def secret_scan_paths(paths: Sequence[Path]) -> list[dict[str, str]]:
    """Return high-confidence metadata without secret values or value hashes."""

    findings: list[dict[str, str]] = []
    seen: set[Path] = set()
    for path in sorted(paths):
        resolved = path.resolve()
        if resolved in seen or not path.is_file() or path.name == ".env":
            continue
        seen.add(resolved)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        label = repo_relative(path) if path.is_relative_to(ROOT) else path.name
        for finding_type, pattern in SECRET_TEXT_PATTERNS:
            if pattern.search(text):
                findings.append({"path": label, "finding_type": finding_type})
        if path.suffix == ".json":
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            findings.extend(_json_sensitive_findings(payload, path=label))
    unique = {
        json.dumps(item, ensure_ascii=False, sort_keys=True): item for item in findings
    }
    return [unique[key] for key in sorted(unique)]


def validate_security_and_gold_isolation() -> dict[str, dict[str, Any]]:
    public_roots = (
        STEP20_ROOT / "environment_receipts",
        STEP20_ROOT / "golden_parity",
    )
    publication_paths = [
        path
        for root in public_roots
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower()
        in {".json", ".jsonl", ".md", ".txt", ".tsv", ".yaml", ".yml"}
    ]
    publication_paths.extend(
        path
        for path in STEP20_ROOT.iterdir()
        if path.is_file()
        and path.suffix.lower()
        in {".json", ".jsonl", ".md", ".txt", ".tsv", ".yaml", ".yml"}
        and path.resolve() != DEFAULT_OUTPUT.resolve()
    )
    publication_paths.extend(
        path
        for path in (
            NATIVE_CLAIM_ACCEPTANCE,
            STEP20_ROOT / "native_claims" / "index.json",
            STEP20_ROOT / "native_claims" / "input_lock.json",
            STEP20_ROOT / "native_claims" / "locks" / "machine_locks.jsonl",
            LOCAL_FAULT_ACCEPTANCE,
            FAULT_ACCEPTANCE,
        )
        if path.is_file()
    )
    publication_paths.extend(
        path
        for path in (
            ROOT / "configs" / "webarena_verified_full_812.yaml",
            ROOT / "configs" / "webarena_verified_sites.lock.json",
        )
        if path.is_file()
    )
    secret_findings = secret_scan_paths(publication_paths)

    agent_inputs = sorted(
        PACKETS_ROOT.glob("*/agent_input.json"),
        key=lambda path: int(path.parent.name),
    )
    gold_findings: list[dict[str, str]] = []
    for path in agent_inputs:
        payload = load_json(path)
        if not isinstance(payload, Mapping):
            gold_findings.append(
                {"path": repo_relative(path), "finding_type": "non_object_model_input"}
            )
            continue
        forbidden = sorted(
            str(key) for key in payload if str(key).lower() in GOLD_FIELD_TOKENS
        )
        for key in forbidden:
            gold_findings.append(
                {
                    "path": repo_relative(path),
                    "finding_type": "gold_or_evaluator_field_in_model_input",
                    "json_key_path": key,
                }
            )
        if set(payload) != AGENT_INPUT_FIELDS:
            gold_findings.append(
                {
                    "path": repo_relative(path),
                    "finding_type": "unexpected_model_input_field_set",
                }
            )

    runtime_present = PILOT_RESULT_ROOT.is_dir()
    runtime_receipt, runtime_error = _load_optional_receipt(PILOT_ACCEPTANCE)
    runtime_scan_ok = bool(
        runtime_present
        and runtime_receipt
        and not runtime_error
        and runtime_receipt.get("status") == "pass"
        and dict(runtime_receipt.get("gates") or {}).get(
            "active_secret_cookie_credential_leakage_zero"
        )
        is True
        and dict(runtime_receipt.get("gates") or {}).get(
            "gold_expected_leakage_zero"
        )
        is True
    )
    runtime_status = "pass" if runtime_scan_ok else "pending"
    if runtime_error or (
        runtime_receipt is not None and runtime_receipt.get("status") == "pass" and not runtime_scan_ok
    ):
        runtime_status = "fail"
    return {
        "static_publication_secret_scan": {
            "status": "pass" if not secret_findings else "fail",
            "scanner_schema": "webarena_verified_high_confidence_secret_scan/v1",
            "scanned_file_count": len({path.resolve() for path in publication_paths}),
            "finding_count": len(secret_findings),
            "findings": secret_findings,
            "credential_values_or_hashes_recorded_in_report": False,
            "dotenv_read": False,
            "excluded_sensitive_input_paths": [".env"],
            "scan_scope": "public acceptance, lock metadata, and deployment receipts",
            "controller_only_private_roots_not_claimed_as_publication_safe": [
                "experiments/step20/webarena_verified/native_claims/drafts",
                "experiments/step20/webarena_verified/native_claims/machine_reviews",
                "results/namespaces/webarena_verified_v1_2_3_pilot_8x3",
            ],
        },
        "static_model_input_gold_isolation": {
            "status": (
                "pass"
                if len(agent_inputs) == 812 and not gold_findings
                else "fail"
            ),
            "model_visible_agent_input_count": len(agent_inputs),
            "expected_model_visible_field_set": sorted(AGENT_INPUT_FIELDS),
            "gold_or_evaluator_field_finding_count": len(gold_findings),
            "findings": gold_findings,
            "drafter_private_sources_are_not_model_visible": True,
        },
        "pilot_runtime_secret_and_gold_scan": {
            "status": runtime_status,
            "pilot_result_namespace_present": runtime_present,
            "required_record_slot_count": 24,
            "credential_values_or_hashes_recorded_in_report": False,
            "reason": (
                None
                if runtime_scan_ok
                else "24-slot pilot runtime security/leakage acceptance is not complete"
            ),
            "evidence": evidence_ref(PILOT_ACCEPTANCE),
        },
    }


def validate_openrouter_credential(
    declared_status: str,
) -> dict[str, Any]:
    allowed = {"invalid_401_user_not_found", "unverified", "valid"}
    if declared_status not in allowed:
        raise RuntimeError(f"unsupported OpenRouter credential status: {declared_status}")
    payload: dict[str, Any] | None = None
    error: str | None = None
    if CREDENTIAL_ACCEPTANCE.is_file():
        try:
            payload = validate_openrouter_credential_acceptance_file(
                CREDENTIAL_ACCEPTANCE
            )
        except (CredentialAcceptanceError, OSError) as exc:
            error = f"invalid credential acceptance: {type(exc).__name__}"
    required_models = list(OPENROUTER_REQUIRED_MODELS)
    receipt_valid = bool(
        payload
        and not error
        and payload.get("schema_version")
        == "webarena_verified_openrouter_credential_acceptance/v1"
        and payload.get("status") == "pass"
        and payload.get("material_retained") is False
        and payload.get("credential_material_retained") is False
        and payload.get("credential_value_hash_retained") is False
        and payload.get("authorization_header_retained") is False
        and payload.get("response_body_retained") is False
        and payload.get("model_content_retained") is False
        and payload.get("model_probe_count") == 3
        and payload.get("successful_model_probe_count") == 3
        and payload.get("paid_model_probe_count") == 3
        and payload.get("fallback_model_probe_count") == 0
        and payload.get("request_attempt_count") == 3
        and payload.get("required_models") == required_models
        and payload.get("secret_scan")
        == {"status": "pass", "finding_count": 0}
        and isinstance(payload.get("gates"), Mapping)
        and all(value is True for value in payload["gates"].values())
        and not secret_scan_paths([CREDENTIAL_ACCEPTANCE])
    )
    if declared_status == "invalid_401_user_not_found":
        status = "fail"
        reason = "latest out-of-band probe returned HTTP 401 User not found"
    elif declared_status == "valid" and receipt_valid:
        status = "pass"
        reason = None
    else:
        status = "pending" if error is None else "fail"
        reason = (
            error
            or "a secret-free, three-model successful credential receipt is not present"
        )
    return {
        "status": status,
        "declared_observation": declared_status,
        "machine_verifiable_from_repository": receipt_valid,
        "required_models": required_models,
        "exact_model_set_verified": bool(
            receipt_valid
            and payload
            and payload.get("required_models") == required_models
        ),
        "model_probe_count": int(payload.get("model_probe_count") or 0)
        if payload
        else 0,
        "successful_model_probe_count": int(
            payload.get("successful_model_probe_count") or 0
        )
        if payload
        else 0,
        "paid_model_probe_count": int(payload.get("paid_model_probe_count") or 0)
        if payload
        else 0,
        "fallback_model_probe_count": int(
            payload.get("fallback_model_probe_count") or 0
        )
        if payload
        else 0,
        "secret_scan_finding_count": int(
            dict(payload.get("secret_scan") or {}).get("finding_count") or 0
        )
        if payload
        else 0,
        "credential_value_read": False,
        "credential_value_retained": False,
        "credential_value_hash_retained": False,
        "blocks_paid_pilot": status != "pass",
        "reason": reason,
        "evidence": evidence_ref(CREDENTIAL_ACCEPTANCE),
    }


def validate_formal_run_control() -> dict[str, Any]:
    payload = load_json(FORMAL_RUN_CONTROL_ACCEPTANCE)
    launch_gates = dict(payload.get("launch_gates") or {})
    canary = dict(launch_gates.get("remote_retention_three_host_canary") or {})
    recovery = dict(launch_gates.get("circuit_recovery_authorization") or {})
    effective_canary_clear = (
        launch_gates.get("effective_remote_retention_canary_clear") is True
    )
    effective_circuit_clear = (
        launch_gates.get("effective_execution_circuit_clear") is True
    )
    recovery_override_ok = bool(
        recovery.get("status") == "pass"
        and recovery.get("raw_circuit_history_preserved") is True
        and effective_canary_clear
        and effective_circuit_clear
    )
    ok = (
        payload.get("schema_version")
        == "webarena_verified_full_run_control_acceptance/v1"
        and payload.get("status") == "pass"
        and payload.get("dry_run") is True
        and payload.get("formal_paid_launch_ready") is True
        and launch_gates.get("formal_jobs_vps_persistent_retention_locked") is True
        and (canary.get("status") == "pass" or recovery_override_ok)
        and launch_gates.get("monitor_circuit_clear") is True
        and effective_circuit_clear
        and _sidecar_valid(FORMAL_RUN_CONTROL_ACCEPTANCE)
    )
    return {
        "status": "pass" if ok else "pending",
        "formal_paid_launch_ready": payload.get("formal_paid_launch_ready") is True,
        "remote_retention_three_host_canary": canary,
        "circuit_recovery_authorization": recovery,
        "raw_monitor_circuit_clear": launch_gates.get(
            "raw_monitor_circuit_clear"
        )
        is True,
        "effective_execution_circuit_clear": effective_circuit_clear,
        "effective_remote_retention_canary_clear": effective_canary_clear,
        "formal_jobs_vps_persistent_retention_locked": launch_gates.get(
            "formal_jobs_vps_persistent_retention_locked"
        )
        is True,
        "remote_file_and_hash_validation_required": True,
        "evidence": evidence_ref(FORMAL_RUN_CONTROL_ACCEPTANCE),
    }


def repository_hygiene_observation(
    *,
    file_count: int | None,
    occurrence_count: int | None,
    active_key_exact_match_count: int | None,
) -> dict[str, Any]:
    values = (file_count, occurrence_count, active_key_exact_match_count)
    if all(value is None for value in values):
        return {
            "status": "not_assessed",
            "scope": "repository history outside the WebArena Step20 publication set",
            "blocks_webarena_step20": False,
            "reason": "no secret-free repository-wide audit counts were supplied",
            "credential_values_or_hashes_recorded": False,
            "dotenv_read_by_builder": False,
        }
    require(all(value is not None for value in values), "hygiene counts must be complete")
    assert file_count is not None
    assert occurrence_count is not None
    assert active_key_exact_match_count is not None
    require(
        file_count >= 0 and occurrence_count >= 0 and active_key_exact_match_count >= 0,
        "hygiene counts cannot be negative",
    )
    return {
        "status": "warning" if occurrence_count else "pass",
        "scope": "repository history outside the WebArena Step20 publication set",
        "blocks_webarena_step20": False,
        "historical_secret_pattern_file_count": file_count,
        "historical_secret_pattern_occurrence_count": occurrence_count,
        "active_key_exact_match_count": active_key_exact_match_count,
        "observation_quality": "out_of_band_secret_free_count_only",
        "action": (
            "retain user-owned historical results; exclude them from release and address "
            "under a separate repository-hygiene workflow"
            if occurrence_count
            else None
        ),
        "credential_values_or_hashes_recorded": False,
        "dotenv_read_by_builder": False,
    }


def _webarena_storage_thresholds() -> dict[str, int]:
    payload = load_json(INFRA_CONFIG)
    machines = [
        item
        for item in payload.get("machines") or []
        if isinstance(item, Mapping)
        and item.get("enabled") is True
        and item.get("role") == "webarena_vps"
    ]
    require(len(machines) == 3, "infra config must contain three enabled WebArena VPSes")
    result = {
        str(item["machine_id"]): int(item["disk_free_gb_min"]) for item in machines
    }
    require(set(result.values()) == {350}, "WebArena disk-free threshold must remain 350 GB")
    return result


def validate_storage_readonly_audit() -> dict[str, Any]:
    payload, error = _load_optional_receipt(STORAGE_READONLY_AUDIT)
    evidence = evidence_ref(STORAGE_READONLY_AUDIT)
    if payload is None:
        return {
            "status": "fail" if error else "pending",
            "reason": error or "read-only three-host storage audit is missing",
            "free_gb_by_machine": {},
            "evidence": evidence,
        }
    expected = expected_servers()
    identities = {
        item["server_id"]: {
            "address": host,
            "fingerprint": item["ssh_host_ed25519_fingerprint"],
        }
        for host, item in expected.items()
    }
    machines = [
        item for item in payload.get("machines") or [] if isinstance(item, Mapping)
    ]
    formal = dict(payload.get("formal_storage_readiness_gate") or {})
    authorization = dict(payload.get("destructive_authorization") or {})
    machine_ok = len(machines) == 3 and {
        str(item.get("machine_id")) for item in machines
    } == set(identities)
    free_gb: dict[str, float] = {}
    for item in machines:
        machine_id = str(item.get("machine_id"))
        identity = identities.get(machine_id, {})
        candidate = dict(item.get("candidate_disk") or {})
        available = int(item.get("root_available_bytes") or 0)
        free_gb[machine_id] = round(available / 1_000_000_000, 6)
        machine_ok = machine_ok and (
            item.get("address") == identity.get("address")
            and item.get("ssh_host_ed25519_fingerprint")
            == identity.get("fingerprint")
            and 0 < available < 350_000_000_000
            and item.get("root_threshold_satisfied") is False
            and candidate.get("size_bytes") == 960_197_124_096
            and candidate.get("metadata_empty_and_unreferenced") is True
            and candidate.get("sfdisk_no_partition_table") is True
            and candidate.get("wipefs_signature_count") == 0
            and candidate.get("partition_or_child_count") == 0
            and candidate.get("mount_reference_count") == 0
            and candidate.get("swap_reference_count") == 0
            and candidate.get("lvm_pv_reference_count") == 0
            and candidate.get("md_reference_count") == 0
            and candidate.get("fstab_reference_count") == 0
            and candidate.get("holder_count") == 0
            and candidate.get("slave_count") == 0
            and candidate.get("open_reference_count") == 0
            and candidate.get("raw_sector_residual_data_ruled_out") is False
        )
    ok = (
        payload.get("schema_version")
        == "webarena_verified_storage_readonly_audit_acceptance/v1"
        and payload.get("status") == "pass"
        and payload.get("audit_mode") == "strictly_read_only_over_pinned_ssh_hosts"
        and payload.get("host_count") == 3
        and payload.get("configured_minimum_free_bytes") == 350_000_000_000
        and payload.get("all_root_filesystems_meet_350gb_gate") is False
        and payload.get("all_candidates_metadata_empty_and_unreferenced") is True
        and payload.get("candidate_capacity_bytes_each") == 960_197_124_096
        and payload.get("destructive_operation_performed") is False
        and payload.get("remote_state_mutated") is False
        and payload.get("secret_material_recorded") is False
        and payload.get("target_paths_absent_on_all_hosts") is True
        and authorization.get("observed") is False
        and formal.get("capacity_gate_current_status") == "fail"
        and formal.get("pilot_storage_measured") is False
        and formal.get("full_2436_storage_projected") is False
        and formal.get("status")
        == "blocked_on_explicit_destructive_confirmation_and_pilot_projection"
        and machine_ok
        and _sidecar_valid(STORAGE_READONLY_AUDIT)
    )
    return {
        "status": "pass" if ok else "fail",
        "audit_is_read_only_and_current": ok,
        "root_capacity_gate_satisfied": False,
        "candidate_disk_count": 3 if ok else 0,
        "candidate_capacity_bytes_each": payload.get("candidate_capacity_bytes_each"),
        "all_candidates_metadata_empty_and_unreferenced": bool(
            payload.get("all_candidates_metadata_empty_and_unreferenced")
        ),
        "raw_sector_history_ruled_out": False,
        "destructive_authorization_observed": bool(authorization.get("observed")),
        "destructive_operation_performed": bool(
            payload.get("destructive_operation_performed")
        ),
        "free_gb_by_machine": free_gb if ok else {},
        "reason": formal.get("reason") if ok else "read-only audit is invalid",
        "evidence": evidence,
    }


def validate_storage_provisioning_acceptance() -> dict[str, Any]:
    payload, error = _load_optional_receipt(STORAGE_PROVISIONING_ACCEPTANCE)
    evidence = evidence_ref(STORAGE_PROVISIONING_ACCEPTANCE)
    if payload is None:
        return {
            "status": "fail" if error else "pending",
            "reason": error or "three-host results-storage provisioning receipt is missing",
            "evidence": evidence,
        }
    expected = expected_servers()
    agent_by_server = {
        "webarena-gpt54-ord": "Agent A",
        "webarena-claude47-ord": "Agent B",
        "webarena-deepseek-v4pro-ord": "Agent C",
    }
    expected_by_id = {
        item["server_id"]: {
            "agent_id": agent_by_server[item["server_id"]],
            "address": host,
            "fingerprint": item["ssh_host_ed25519_fingerprint"],
        }
        for host, item in expected.items()
    }
    machines = [
        item for item in payload.get("machines") or [] if isinstance(item, Mapping)
    ]
    machine_ok = len(machines) == 3 and {
        str(item.get("machine_id")) for item in machines
    } == set(expected_by_id)
    storage_root = STORAGE_PROVISIONING_ACCEPTANCE.parent
    for item in machines:
        machine_id = str(item.get("machine_id"))
        identity = expected_by_id.get(machine_id, {})
        descriptors_ok = True
        for path_field, hash_field in (
            ("preflight_receipt", "preflight_receipt_sha256"),
            ("provision_receipt", "provision_receipt_sha256"),
            ("postflight_receipt", "postflight_receipt_sha256"),
        ):
            name = item.get(path_field)
            if not isinstance(name, str) or "/" in name or "\\" in name:
                descriptors_ok = False
                continue
            path = storage_root / name
            descriptors_ok = descriptors_ok and (
                path.is_file()
                and not path.is_symlink()
                and item.get(hash_field) == sha256_file(path)
                and _sidecar_valid(path)
            )
        machine_ok = machine_ok and descriptors_ok and (
            item.get("agent_id") == identity.get("agent_id")
            and item.get("address") == identity.get("address")
            and item.get("ssh_host_ed25519_fingerprint")
            == identity.get("fingerprint")
            and item.get("candidate_size_bytes") == 960_197_124_096
            and item.get("filesystem_type") == "ext4"
            and item.get("mount_point") == "/opt/webarena-results"
            and item.get("controller_results_projection")
            == "/opt/webarena-controller/current/results"
            and item.get("available_bytes") == 895_944_495_104
            and item.get("minimum_required_bytes") == 350_000_000_000
            and item.get("capacity_threshold_satisfied") is True
            and item.get("mount_a_persistence_tested") is True
            and item.get("status") == "pass"
        )
    authorization = dict(payload.get("authorization") or {})
    preflight = dict(payload.get("preflight") or {})
    capacity = dict(payload.get("capacity_gate") or {})
    safety = dict(payload.get("safety") or {})
    projection = dict(payload.get("storage_budget_projection") or {})
    ok = (
        payload.get("schema_version")
        == "webarena_verified_storage_provisioning_acceptance/v1"
        and payload.get("status") == "pass"
        and payload.get("operation")
        == "authorized_three_host_results_disk_provisioning"
        and payload.get("destructive_operation_performed") is True
        and authorization.get("observed") is True
        and authorization.get("scope_bound_to_readonly_audit") is True
        and authorization.get("readonly_audit_acceptance_sha256")
        == (
            sha256_file(STORAGE_READONLY_AUDIT)
            if STORAGE_READONLY_AUDIT.is_file()
            else None
        )
        and authorization.get("token_or_token_hash_recorded_here") is False
        and preflight.get("status") == "pass"
        and preflight.get("host_count") == 3
        and preflight.get("all_expected_ssh_ed25519_fingerprints_matched") is True
        and preflight.get("all_root_disks_distinct_from_candidates") is True
        and preflight.get("all_candidates_metadata_empty_and_unreferenced") is True
        and capacity.get("status") == "pass"
        and capacity.get("host_count") == 3
        and capacity.get("minimum_available_bytes_across_hosts")
        == 895_944_495_104
        and capacity.get("minimum_required_bytes_per_host") == 350_000_000_000
        and capacity.get("all_hosts_threshold_satisfied") is True
        and safety.get("root_disk_formatted") is False
        and safety.get("all_root_disks_untouched") is True
        and safety.get("remote_results_mount_mode") == "0700"
        and safety.get("remote_controller_results_directory_mode") == "0700"
        and safety.get("secret_material_recorded") is False
        and safety.get("model_credentials_read") is False
        and safety.get("model_calls_made") == 0
        and projection.get("pilot_storage_measured") is False
        and projection.get("full_2436_storage_projected") is False
        and projection.get("formal_storage_readiness_acceptance_satisfied")
        is False
        and machine_ok
        and _sidecar_valid(STORAGE_PROVISIONING_ACCEPTANCE)
    )
    return {
        "status": "pass" if ok else "fail",
        "host_count": len(machines),
        "mounted_results_path": "/opt/webarena-results",
        "controller_results_projection": "/opt/webarena-controller/current/results",
        "available_bytes_per_host": 895_944_495_104 if ok else None,
        "capacity_threshold_satisfied": ok,
        "mount_a_persistence_verified": ok,
        "pilot_storage_measured": False,
        "full_2436_storage_projected": False,
        "secret_material_recorded": False,
        "evidence": evidence,
    }


def validate_storage_readiness(
    observed_free_gb: Mapping[str, float] | None,
) -> dict[str, Any]:
    thresholds = _webarena_storage_thresholds()
    readonly_audit = validate_storage_readonly_audit()
    provisioning = validate_storage_provisioning_acceptance()
    payload, error = _load_optional_receipt(STORAGE_ACCEPTANCE)
    receipt_measurements: dict[str, float] = {}
    receipt_capacity_ok = False
    receipt_full_ok = False
    if payload and not error:
        raw = payload.get("free_gb_by_machine")
        if isinstance(raw, Mapping) and set(raw) == set(thresholds):
            receipt_measurements = {key: float(raw[key]) for key in thresholds}
            receipt_capacity_ok = (
                payload.get("schema_version")
                == "webarena_verified_storage_readiness_acceptance/v1"
                and payload.get("status") == "pass"
                and payload.get("measurement_method") == "df_bytes_hash_bound"
                and payload.get("acceptance_scope")
                == "provisioned_capacity_and_mount_persistence_only"
                and payload.get("provisioning_acceptance")
                == repo_relative(STORAGE_PROVISIONING_ACCEPTANCE)
                and payload.get("provisioning_acceptance_sha256")
                == (
                    sha256_file(STORAGE_PROVISIONING_ACCEPTANCE)
                    if STORAGE_PROVISIONING_ACCEPTANCE.is_file()
                    else None
                )
                and payload.get("all_three_capacity_thresholds_satisfied") is True
                and payload.get("mount_a_persistence_verified_on_all_hosts") is True
                and payload.get("pilot_capacity_gate_satisfied") is True
                and payload.get("blocks_real_pilot_for_capacity") is False
                and provisioning.get("status") == "pass"
                and all(
                    receipt_measurements[key] >= thresholds[key] for key in thresholds
                )
                and _sidecar_valid(STORAGE_ACCEPTANCE)
            )
            receipt_full_ok = (
                receipt_capacity_ok
                and payload.get("pilot_storage_projection_complete") is True
                and payload.get("full_run_storage_projection_complete") is True
                and payload.get("blocks_full_2436_launch") is False
            )
    supplied = dict(observed_free_gb or {})
    if supplied:
        require(
            set(supplied) == set(thresholds),
            "observed storage values must cover exactly the three WebArena VPSes",
        )
        supplied = {key: float(value) for key, value in supplied.items()}
        require(all(value >= 0 for value in supplied.values()), "negative free-space value")
    readonly_measurements = dict(readonly_audit.get("free_gb_by_machine") or {})
    effective = (
        receipt_measurements
        if receipt_measurements
        else supplied
        if supplied
        else readonly_measurements
    )
    threshold_met = bool(effective) and all(
        effective[key] >= thresholds[key] for key in thresholds
    )
    if receipt_full_ok:
        status = "pass"
        measurement_quality = "hash_bound_provisioned_and_projected_remote_receipt"
        reason = None
    elif receipt_capacity_ok:
        status = "pending"
        measurement_quality = "hash_bound_provisioned_capacity_and_mount_persistence"
        reason = (
            "pilot capacity is ready on all three mounted results disks; measured "
            "pilot artifacts are still required for the formal 2,436-slot projection"
        )
    elif (
        readonly_audit.get("status") == "pass"
        and effective == readonly_measurements
        and not threshold_met
    ):
        status = "pending"
        measurement_quality = "hash_bound_readonly_remote_audit"
        reason = (
            "all three root filesystems are below 350 GB; three metadata-empty "
            "960197124096-byte candidates remain unformatted because explicit "
            "destructive authorization is absent; pilot/full storage projections "
            "are also pending"
        )
    elif effective and not threshold_met:
        status = "fail"
        measurement_quality = "operator_supplied_approximation_no_hash_bound_receipt"
        reason = "observed free space is below the configured hard pre-launch minimum"
    elif error:
        status = "fail"
        measurement_quality = "invalid_receipt"
        reason = error
    else:
        status = "pending"
        measurement_quality = (
            "operator_supplied_approximation_no_hash_bound_receipt"
            if effective
            else "unmeasured"
        )
        reason = "hash-bound storage measurement and pilot/full projection are missing"
    per_machine = []
    for machine_id in sorted(thresholds):
        observed = effective.get(machine_id)
        per_machine.append(
            {
                "machine_id": machine_id,
                "configured_min_free_gb": thresholds[machine_id],
                "observed_free_gb": observed,
                "margin_gb": (
                    round(observed - thresholds[machine_id], 3)
                    if observed is not None
                    else None
                ),
                "threshold_satisfied": (
                    observed >= thresholds[machine_id]
                    if observed is not None
                    else False
                ),
            }
        )
    return {
        "status": status,
        "gate_semantics": "hard_pre_launch_minimum_free_space_per_vps",
        "configured_min_free_gb": 350,
        "measurement_quality": measurement_quality,
        "all_three_thresholds_satisfied": threshold_met,
        "pilot_storage_projection_complete": bool(
            payload and payload.get("pilot_storage_projection_complete") is True
        ),
        "full_run_storage_projection_complete": bool(
            payload and payload.get("full_run_storage_projection_complete") is True
        ),
        "pilot_capacity_gate_satisfied": receipt_capacity_ok,
        "blocks_paid_pilot_for_capacity": not receipt_capacity_ok,
        "blocks_full_2436_launch": not receipt_full_ok,
        "blocks_paid_pilot_and_full_launch": not receipt_full_ok,
        "reason": reason,
        "machines": per_machine,
        "evidence": evidence_ref(STORAGE_ACCEPTANCE),
        "readonly_audit": readonly_audit,
        "provisioning": provisioning,
    }


def validate_pilot_storage_capacity_preflight(
    storage: Mapping[str, Any],
) -> dict[str, Any]:
    """Accept capacity discovery for the small pilot without claiming full readiness.

    The pilot does not depend on a post-pilot projection.  A strict read-only
    provisioning receipt proving a mounted ext4 results disk, controller
    projection, persistent mount, and >=350 GB available on each pinned VPS is
    sufficient to authorize the small pilot.  This gate does not make the
    formal 2,436-run projection gate pass.
    """

    provisioning = dict(storage.get("provisioning") or {})
    ok = (
        provisioning.get("status") == "pass"
        and provisioning.get("host_count") == 3
        and provisioning.get("mounted_results_path") == "/opt/webarena-results"
        and provisioning.get("controller_results_projection")
        == "/opt/webarena-controller/current/results"
        and provisioning.get("available_bytes_per_host") == 895_944_495_104
        and provisioning.get("capacity_threshold_satisfied") is True
        and provisioning.get("mount_a_persistence_verified") is True
        and storage.get("pilot_capacity_gate_satisfied") is True
        and storage.get("blocks_paid_pilot_for_capacity") is False
    )
    return {
        "status": "pass" if ok else "pending",
        "scope": "small_pilot_capacity_preflight_only",
        "pilot_launch_capacity_available": ok,
        "formal_2436_storage_ready": storage.get("status") == "pass",
        "destructive_provisioning_completed_under_scoped_authorization": ok,
        "post_pilot_projection_required_for_full_launch": True,
        "mounted_host_count": int(provisioning.get("host_count") or 0),
        "mounted_results_path": provisioning.get("mounted_results_path"),
        "controller_results_projection": provisioning.get(
            "controller_results_projection"
        ),
        "available_bytes_per_host": provisioning.get(
            "available_bytes_per_host"
        ),
        "reason": (
            None
            if ok
            else "three-host hash-bound pilot capacity preflight is incomplete"
        ),
        "evidence": {
            "provisioning_acceptance": provisioning.get("evidence"),
            "storage_readiness_acceptance": storage.get("evidence"),
        },
    }


def _validate_future_acceptance(
    *,
    path: Path,
    schema_version: str,
    required_gates: Sequence[str],
    missing_reason: str,
) -> dict[str, Any]:
    payload, error = _load_optional_receipt(path)
    evidence = evidence_ref(path)
    if payload is None:
        return {
            "status": "fail" if error else "pending",
            "reason": error or missing_reason,
            "evidence": evidence,
        }
    gates = dict(payload.get("gates") or {})
    ok = (
        payload.get("schema_version") == schema_version
        and payload.get("status") == "pass"
        and all(gates.get(name) is True for name in required_gates)
        and _sidecar_valid(path)
    )
    return {
        "status": "pass" if ok else "fail",
        "required_gates": list(required_gates),
        "failed_or_missing_gates": [
            name for name in required_gates if gates.get(name) is not True
        ],
        "evidence": evidence,
    }


def validate_real_pilot_acceptance() -> dict[str, Any]:
    required_gate_names = (
        "all_24_slots_completed",
        "all_reset_receipts_present",
        "all_har_artifacts_present",
        "all_network_sanitization_receipts_present",
        "all_trace_artifacts_present",
        "all_native_evaluator_io_present",
        "all_raw_runs_present",
        "all_artifact_manifests_present",
        "all_model_call_records_present",
        "structured_final_json_valid",
        "paired_seed_exact",
        "counterbalanced_order_exact",
        "schema_hash_pointer_failures_zero",
        "expected_fallback_zero",
        "active_secret_cookie_credential_leakage_zero",
        "gold_expected_leakage_zero",
    )
    base = _validate_future_acceptance(
        path=PILOT_ACCEPTANCE,
        schema_version="webarena_verified_pilot_acceptance/v1",
        required_gates=required_gate_names,
        missing_reason="A/B/C real 8-case x 3-agent pilot acceptance is missing",
    )
    payload, error = _load_optional_receipt(PILOT_ACCEPTANCE)
    if payload is None:
        return base
    manifest, manifest_error = _load_optional_receipt(PILOT_MANIFEST)
    counts = dict(payload.get("counts") or {})
    rows = [
        item for item in payload.get("record_slots") or [] if isinstance(item, Mapping)
    ]
    expected_slots = [
        item
        for item in (manifest or {}).get("record_slots") or []
        if isinstance(item, Mapping)
    ]
    required_artifacts = {
        "structured_final_response",
        "network_har",
        "network_har_sanitization",
        "playwright_trace",
        "native_evaluator_input",
        "native_evaluator_output",
        "raw_run",
        "artifact_manifest",
        "model_calls",
        "reset_receipt",
    }
    artifacts_ok = len(rows) == 24
    validated_artifact_count = 0
    for row, expected in zip(rows, expected_slots, strict=False):
        artifacts = dict(row.get("artifacts") or {})
        row_ok = (
            row.get("record_slot_id") == expected.get("record_slot_id")
            and row.get("task_id") == expected.get("task_id")
            and row.get("agent_id") == expected.get("agent_id")
            and row.get("model") == expected.get("model")
            and row.get("server_id") == expected.get("server_id")
            and row.get("seed") == expected.get("seed")
            and row.get("status") == "completed"
            and set(artifacts) == required_artifacts
        )
        for name in required_artifacts:
            descriptor = dict(artifacts.get(name) or {})
            relative = descriptor.get("path")
            if not isinstance(relative, str):
                row_ok = False
                continue
            try:
                relative = require_safe_relative_path(
                    relative, f"pilot {row.get('record_slot_id')} artifact {name}"
                )
            except RuntimeError:
                row_ok = False
                continue
            path = ROOT / relative
            row_ok = row_ok and (
                path.is_file()
                and not path.is_symlink()
                and path.resolve().is_relative_to(PILOT_RESULT_ROOT.resolve())
                and descriptor.get("sha256") == sha256_file(path)
                and descriptor.get("size_bytes") == path.stat().st_size
                and (path.stat().st_size > 0 or name == "network_har")
            )
        validated_artifact_count += len(required_artifacts) if row_ok else 0
        artifacts_ok = artifacts_ok and row_ok

    structure_ok = (
        error is None
        and manifest is not None
        and manifest_error is None
        and len(expected_slots) == 24
        and len(rows) == 24
        and [row.get("record_slot_id") for row in rows]
        == [slot.get("record_slot_id") for slot in expected_slots]
        and len({row.get("record_slot_id") for row in rows}) == 24
        and counts.get("expected_record_slots") == 24
        and counts.get("completed_record_slots") == 24
        and counts.get("fallback_contracts") == 0
        and counts.get("schema_hash_pointer_failures") == 0
        and counts.get("per_agent")
        == {"Agent A": 8, "Agent B": 8, "Agent C": 8}
        and artifacts_ok
    )
    if base.get("status") == "pass" and structure_ok:
        status = "pass"
        reason = None
    elif base.get("status") == "pending":
        status = "pending"
        reason = base.get("reason")
    else:
        status = "fail"
        reason = "pilot receipt/artifact tree fails exact 24-slot validation"
    return {
        **base,
        "status": status,
        "reason": reason,
        "validated_record_slot_count": len(rows) if structure_ok else 0,
        "required_record_slot_count": 24,
        "validated_artifact_count": validated_artifact_count,
        "required_artifact_count": 24 * len(required_artifacts),
        "exact_agent_counts": counts.get("per_agent")
        == {"Agent A": 8, "Agent B": 8, "Agent C": 8},
        "fallback_contract_count": counts.get("fallback_contracts"),
    }


def validate_local_fault_classification() -> dict[str, Any]:
    payload, error = _load_optional_receipt(LOCAL_FAULT_ACCEPTANCE)
    evidence = evidence_ref(LOCAL_FAULT_ACCEPTANCE)
    if payload is None:
        return {
            "status": "fail" if error else "pending",
            "reason": error or "local four-fault classification receipt is missing",
            "evidence": evidence,
        }
    counts = dict(payload.get("counts") or {})
    gates = dict(payload.get("gates") or {})
    kinds = {
        str(item.get("fault_kind"))
        for item in payload.get("entries") or []
        if isinstance(item, Mapping)
    }
    ok = (
        payload.get("schema_version")
        == "webarena_verified_fault_injection_acceptance/v1"
        and payload.get("status") == "pass"
        and payload.get("scope") == "local_harness"
        and payload.get("real_remote_execution") is False
        and payload.get("local_implementation_gate_satisfied") is True
        and payload.get("formal_step20_fault_gate_satisfied") is False
        and counts.get("expected_receipts") == 4
        and counts.get("validated_receipts") == 4
        and counts.get("score_counted") == 0
        and counts.get("agent_failures_counted") == 0
        and counts.get("fallback_contracts") == 0
        and counts.get("paid_model_calls") == 0
        and kinds
        == {
            "site_outage",
            "login_failure",
            "invalid_placeholder_api_key",
            "evaluator_error",
        }
        and all(value is True for value in gates.values())
        and _sidecar_valid(LOCAL_FAULT_ACCEPTANCE)
    )
    return {
        "status": "pass" if ok else "fail",
        "scope": "local_harness_only",
        "validated_fault_kind_count": len(kinds),
        "validated_receipt_count": int(counts.get("validated_receipts") or 0),
        "execution_status": "INFRA_EXCLUDED",
        "evidence_label": "UNRESOLVE",
        "score_counted": False,
        "agent_failure_counted": False,
        "fallback_contract_count": int(counts.get("fallback_contracts") or 0),
        "formal_step20_fault_gate_satisfied": False,
        "evidence": evidence,
    }


def validate_remote_fault_acceptance() -> dict[str, Any]:
    payload, error = _load_optional_receipt(FAULT_ACCEPTANCE)
    evidence = evidence_ref(FAULT_ACCEPTANCE)
    if payload is None:
        return {
            "status": "fail" if error else "pending",
            "reason": error
            or "three-host x four-kind real fault-injection acceptance is missing",
            "required_remote_receipt_count": 12,
            "evidence": evidence,
        }
    counts = dict(payload.get("counts") or {})
    gates = dict(payload.get("gates") or {})
    entries = [item for item in payload.get("entries") or [] if isinstance(item, Mapping)]
    kinds = {str(item.get("fault_kind")) for item in entries}
    machines = {str(item.get("machine_id")) for item in entries}
    expected_machines = {item["server_id"] for item in expected_servers().values()}
    expected_kinds = {
        "site_outage",
        "login_failure",
        "invalid_placeholder_api_key",
        "evaluator_error",
    }
    exact_matrix = {
        (machine_id, fault_kind)
        for machine_id in expected_machines
        for fault_kind in expected_kinds
    }
    observed_matrix = {
        (str(item.get("machine_id")), str(item.get("fault_kind")))
        for item in entries
    }
    aggregate_core = dict(payload)
    aggregate_core.pop("integrity", None)
    aggregate_integrity_ok = (
        dict(payload.get("integrity") or {}).get("algorithm")
        == "sha256_canonical_json"
        and dict(payload.get("integrity") or {}).get("core_sha256")
        == core_sha256_object(aggregate_core)
    )

    receipt_rows_ok = len(entries) == 12
    for item in entries:
        relative = item.get("receipt_path")
        if not isinstance(relative, str):
            receipt_rows_ok = False
            continue
        try:
            relative = require_safe_relative_path(relative, "fault receipt path")
        except RuntimeError:
            receipt_rows_ok = False
            continue
        receipt_path = FAULT_ACCEPTANCE.parent / "remote_three_host" / relative
        receipt, receipt_error = _load_optional_receipt(receipt_path)
        if receipt is None or receipt_error:
            receipt_rows_ok = False
            continue
        receipt_core = dict(receipt)
        receipt_core.pop("integrity", None)
        receipt_rows_ok = receipt_rows_ok and (
            item.get("status") == "pass"
            and item.get("execution_status") == "INFRA_EXCLUDED"
            and item.get("evidence_label") == "UNRESOLVE"
            and item.get("score_counted") is False
            and item.get("agent_failure_counted") is False
            and item.get("fallback_contract_used") is False
            and item.get("paid_model_calls") == 0
            and item.get("recovery_status") == "pass"
            and item.get("remote_attestation_verified") is True
            and item.get("evidence_hashes_verified") is True
            and item.get("secret_scan_status") == "pass"
            and item.get("receipt_sha256") == sha256_file(receipt_path)
            and item.get("receipt_core_sha256") == core_sha256_object(receipt_core)
            and _sidecar_valid(receipt_path)
            and receipt.get("schema_version")
            == "webarena_verified_fault_injection_receipt/v1"
            and receipt.get("status") == "pass"
            and receipt.get("execution_mode") == "remote_real"
            and receipt.get("machine_id") == item.get("machine_id")
            and receipt.get("fault_kind") == item.get("fault_kind")
            and receipt.get("expected_semantics")
            == receipt.get("observed_semantics")
            and dict(receipt.get("recovery") or {}).get("status") == "pass"
            and all(value is True for value in dict(receipt.get("gates") or {}).values())
            and dict(receipt.get("safety") or {}).get("paid_model_calls") == 0
            and dict(receipt.get("safety") or {}).get("real_dotenv_read") is False
            and dict(receipt.get("safety") or {}).get("real_secret_loaded") is False
            and dict(receipt.get("secret_scan") or {}).get("finding_count") == 0
            and dict(receipt.get("integrity") or {}).get("core_sha256")
            == core_sha256_object(receipt_core)
        )

    postflight, postflight_error = _load_optional_receipt(FAULT_POSTFLIGHT)
    postflight_ok = False
    if postflight is not None and postflight_error is None:
        post_counts = dict(postflight.get("counts") or {})
        results = [
            item
            for item in postflight.get("machine_results") or []
            if isinstance(item, Mapping)
        ]
        post_core = dict(postflight)
        post_core.pop("integrity", None)
        identities = {
            item["server_id"]: item["ssh_host_ed25519_fingerprint"]
            for item in expected_servers().values()
        }
        fault_binding = dict(postflight.get("fault_acceptance") or {})
        plan_binding = dict(postflight.get("execution_plan") or {})
        plan, plan_error = _load_optional_receipt(FAULT_EXECUTION_PLAN)
        plan_core = dict(plan or {})
        plan_core.pop("integrity", None)
        plan_rows = [
            item for item in (plan or {}).get("rows") or [] if isinstance(item, Mapping)
        ]
        plan_ok = bool(
            plan
            and plan_error is None
            and plan.get("schema_version")
            == "webarena_verified_fault_remote_plan/v1"
            and plan.get("status") == "planned"
            and plan.get("machine_count") == 3
            and plan.get("fault_count_per_machine") == 4
            and plan.get("receipt_count") == 12
            and plan.get("paid_model_calls_planned") == 0
            and plan.get("dotenv_loading_supported") is False
            and plan.get("real_credential_input_supported") is False
            and len(plan_rows) == 12
            and {
                (str(item.get("machine_id")), str(item.get("fault_kind")))
                for item in plan_rows
            }
            == exact_matrix
            and len({int(item.get("ordinal", -1)) for item in plan_rows}) == 12
            and dict(plan.get("integrity") or {}).get("core_sha256")
            == core_sha256_object(plan_core)
        )
        postflight_ok = (
            postflight.get("schema_version")
            == "webarena_verified_fault_postflight/v1"
            and postflight.get("status") == "pass"
            and postflight.get("benchmark_version") == "v1.2.3"
            and post_counts.get("machines") == 3
            and post_counts.get("sites_expected") == 18
            and post_counts.get("sites_passed") == 18
            and post_counts.get("receipts") == 12
            and post_counts.get("fault_observations") == 12
            and post_counts.get("recovery_observations") == 12
            and post_counts.get("execution_failures") == 0
            and post_counts.get("score_counted") == 0
            and post_counts.get("agent_failures_counted") == 0
            and post_counts.get("fallback_contracts") == 0
            and post_counts.get("paid_model_calls") == 0
            and len(results) == 3
            and {str(item.get("machine_id")) for item in results}
            == expected_machines
            and all(
                item.get("status") == "pass"
                and item.get("site_status") == "pass"
                and item.get("site_count") == 6
                and set(item.get("sites") or [])
                == {
                    "shopping",
                    "shopping_admin",
                    "reddit",
                    "gitlab",
                    "wikipedia",
                    "map",
                }
                and item.get("all_containers_running") is True
                and item.get("all_port_bindings_loopback_only") is True
                and item.get("all_sentinels_passed") is True
                and item.get("slot_lock_exists") is False
                and item.get("worker_process_count") == 0
                and item.get("login_temp_workspace_count") == 0
                and item.get("evaluator_temp_workspace_count") == 0
                and item.get("provider_key_present") is False
                and item.get("ssh_host_ed25519_fingerprint")
                == identities.get(str(item.get("machine_id")))
                for item in results
            )
            and fault_binding.get("path") == repo_relative(FAULT_ACCEPTANCE)
            and fault_binding.get("file_sha256") == sha256_file(FAULT_ACCEPTANCE)
            and fault_binding.get("core_sha256")
            == dict(payload.get("integrity") or {}).get("core_sha256")
            and fault_binding.get("status") == "pass"
            and fault_binding.get("formal_step20_fault_gate_satisfied") is True
            and plan_ok
            and plan_binding.get("path") == repo_relative(FAULT_EXECUTION_PLAN)
            and plan_binding.get("file_sha256")
            == sha256_file(FAULT_EXECUTION_PLAN)
            and plan_binding.get("core_sha256")
            == dict((plan or {}).get("integrity") or {}).get("core_sha256")
            and dict(postflight.get("integrity") or {}).get("algorithm")
            == "sha256_canonical_json"
            and dict(postflight.get("integrity") or {}).get("core_sha256")
            == core_sha256_object(post_core)
            and _sidecar_valid(FAULT_POSTFLIGHT)
        )
    ok = (
        payload.get("schema_version")
        == "webarena_verified_fault_injection_acceptance/v1"
        and payload.get("status") == "pass"
        and payload.get("scope") == "remote_three_host"
        and payload.get("real_remote_execution") is True
        and payload.get("formal_step20_fault_gate_satisfied") is True
        and counts.get("expected_receipts") == 12
        and counts.get("validated_receipts") == 12
        and counts.get("observed_receipts") == 12
        and counts.get("score_counted") == 0
        and counts.get("agent_failures_counted") == 0
        and counts.get("fallback_contracts") == 0
        and counts.get("paid_model_calls") == 0
        and kinds == expected_kinds
        and machines == expected_machines
        and observed_matrix == exact_matrix
        and len(entries) == len(observed_matrix) == 12
        and receipt_rows_ok
        and aggregate_integrity_ok
        and postflight_ok
        and all(value is True for value in gates.values())
        and _sidecar_valid(FAULT_ACCEPTANCE)
    )
    return {
        "status": "pass" if ok else "fail",
        "real_remote_execution": payload.get("real_remote_execution") is True,
        "validated_host_count": len(machines),
        "validated_fault_kind_count": len(kinds),
        "validated_receipt_count": int(counts.get("validated_receipts") or 0),
        "required_remote_receipt_count": 12,
        "exact_three_by_four_matrix": observed_matrix == exact_matrix,
        "postflight_status": "pass" if postflight_ok else "fail",
        "postflight_six_sites_per_host": postflight_ok,
        "postflight_no_slot_locks_or_workers": postflight_ok,
        "formal_step20_fault_gate_satisfied": payload.get(
            "formal_step20_fault_gate_satisfied"
        )
        is True,
        "evidence": {
            "fault_matrix": evidence,
            "remote_postflight": evidence_ref(FAULT_POSTFLIGHT),
        },
    }


def validate_pilot_fault_and_budget() -> dict[str, dict[str, Any]]:
    pilot_manifest_payload, pilot_manifest_error = _load_optional_receipt(PILOT_MANIFEST)
    pilot_manifest_ok = bool(
        pilot_manifest_payload
        and not pilot_manifest_error
        and pilot_manifest_payload.get("schema_version")
        == "webarena_verified_pilot_8x3_manifest/v1"
        and pilot_manifest_payload.get("status") == "frozen"
        and dict(pilot_manifest_payload.get("counts") or {}).get("cases") == 8
        and dict(pilot_manifest_payload.get("counts") or {}).get("record_slots") == 24
        and dict(pilot_manifest_payload.get("counts") or {}).get("fallback_contracts")
        == 0
        and _sidecar_valid(PILOT_MANIFEST)
    )
    pilot = validate_real_pilot_acceptance()
    pilot["frozen_manifest_status"] = "pass" if pilot_manifest_ok else "fail"
    pilot["frozen_manifest_evidence"] = evidence_ref(PILOT_MANIFEST)
    if not pilot_manifest_ok and pilot["status"] == "pass":
        pilot["status"] = "fail"

    fault = validate_remote_fault_acceptance()
    budget = _validate_future_acceptance(
        path=PILOT_BUDGET_ACCEPTANCE,
        schema_version="webarena_verified_pilot_cost_runtime_storage_acceptance/v1",
        required_gates=(
            "all_24_slots_accounted",
            "actual_cost_within_written_budget",
            "actual_runtime_within_written_budget",
            "pilot_storage_measured",
            "full_2436_storage_projected",
            "retention_policy_written",
            "openrouter_remaining_credit_safety_margin_pass",
        ),
        missing_reason="pilot cost/runtime/storage report is missing",
    )
    return {
        "local_fault_classification": validate_local_fault_classification(),
        "real_abc_pilot_and_artifacts": pilot,
        "fault_injection": fault,
        "pilot_cost_runtime_storage_budget": budget,
    }


def validate_retired_compiler_and_materialized_schedule() -> dict[str, Any]:
    """Validate compiler retirement without reopening its deleted package."""

    receipt, receipt_error = _load_optional_receipt(
        NATIVE_CLAIM_COMPILER_RETIREMENT
    )
    retirement_policy = dict((receipt or {}).get("retirement_policy") or {})
    compiler_package = dict((receipt or {}).get("compiler_package") or {})
    deletion = dict((receipt or {}).get("deletion") or {})
    baseline = dict((receipt or {}).get("full_run_baseline") or {})
    receipt_valid = bool(
        receipt
        and not receipt_error
        and receipt.get("schema_version")
        == "webarena_verified_native_claim_compiler_retirement/v1"
        and receipt.get("status") in {"baseline_recorded", "retired_deleted"}
        and compiler_package.get("path")
        == "experiments/step20/webarena_verified/native_claims"
        and compiler_package.get("file_count") == 5694
        and compiler_package.get("logical_size_bytes") == 30_855_608
        and compiler_package.get("tree_sha256")
        == "8e301160339aeda05fc66bdd3c235dcf0ae6fa15cb1dd53638c190d0d649a6cd"
        and baseline.get("expected_record_slot_count") == 2436
        and baseline.get("canonical_reusable") == 0
        and baseline.get("pending") == 2436
        and baseline.get("jobs_aggregate_sha256")
        == "5c613b729e96ac020b9e2a8d5cdba667371f086be7c5cad4e46292d9a349e704"
        and baseline.get("jobs_index_sha256")
        == "be5188be881e575a13daeb4f334d01a20e50b394b9977e28e2e68bf2ffa7f9ca"
        and retirement_policy.get("unique_formal_score_draft_provider")
        == "neurips_ed_track_minimal"
        and retirement_policy.get(
            "legacy_compiler_outputs_are_formal_score_drafts"
        )
        is False
        and retirement_policy.get("materialized_full_jobs_must_not_change")
        is True
        and _sidecar_valid(NATIVE_CLAIM_COMPILER_RETIREMENT)
    )
    package_absent = not NATIVE_CLAIM_ROOT.exists()
    retired = receipt_valid and package_absent

    jobs: tuple[dict[str, Any], ...] = ()
    index: dict[str, Any] = {}
    plan: Any = None
    materialized_error: str | None = None
    try:
        jobs, index, index_file = webarena_verified_run_control.load_full_jobs()
        plan = webarena_verified_run_control.load_materialized_full_plan(index_file)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        materialized_error = type(exc).__name__
    per_agent = {
        agent_id: sum(job.get("agent_id") == agent_id for job in jobs)
        for agent_id in ("Agent A", "Agent B", "Agent C")
    }
    lineage_values = {
        str(
            dict(job.get("formal_policy_lock") or {}).get(
                "native_claim_index_sha256"
            )
            or ""
        )
        for job in jobs
    }
    materialized = bool(
        plan is not None
        and len(jobs) == 2436
        and index.get("job_count") == 2436
        and index.get("jobs_sha256")
        == "5c613b729e96ac020b9e2a8d5cdba667371f086be7c5cad4e46292d9a349e704"
        and per_agent == {"Agent A": 812, "Agent B": 812, "Agent C": 812}
        and len(lineage_values) == 1
        and len(next(iter(lineage_values), "")) == 64
        and plan.acceptance.get("formal_score_draft_provider")
        == "neurips_ed_track_minimal"
    )

    waiver_sha256 = sha256_file(OPERATOR_WAIVER) if OPERATOR_WAIVER.is_file() else None
    authorization = dict(index.get("launch_authorization") or {})
    waiver_ok = bool(
        waiver_sha256
        and _sidecar_valid(OPERATOR_WAIVER)
        and authorization.get("basis") == "operator_machine_only_waiver"
        and authorization.get("operator_waiver_sha256") == waiver_sha256
        and authorization.get("human_signoff_claimed") is False
        and authorization.get("human_signed_count") == 0
    )
    retirement_evidence = evidence_ref(NATIVE_CLAIM_COMPILER_RETIREMENT)
    retirement_reason = (
        None
        if retired
        else receipt_error
        or "legacy native-claim compiler package is still present in the formal tree"
    )
    native = {
        "native_contract_machine_validation": {
            "status": "pass" if retired and materialized else "fail",
            "machine_validated_count": 812 if materialized else 0,
            "fallback_contract_count": 0 if materialized else None,
            "legacy_compiler_package_present": not package_absent,
            "legacy_compiler_package_retired": retired,
            "unique_formal_score_draft_provider": "neurips_ed_track_minimal",
            "historical_hashes_are_lineage_only": True,
            "retirement_receipt": retirement_evidence,
            "reason": retirement_reason or materialized_error,
        },
        "native_contract_human_signoff": {
            "status": "waived" if retired and waiver_ok else "pending",
            "signed_count": 0,
            "required_count": 812,
            "formal_launch_eligible": bool(retired and waiver_ok and materialized),
            "human_signoff_claimed": False,
            "reason": None if retired and waiver_ok else retirement_reason,
            "evidence": retirement_evidence,
        },
        "native_contract_operator_waiver": {
            "status": "pass" if waiver_ok else "pending",
            "human_signoff_claimed": False,
            "human_signed_count": 0,
            "reviewer_identity_or_signature_claimed": False,
            "operator_waiver_sha256": waiver_sha256,
            "compiler_retirement_does_not_claim_human_review": True,
            "evidence": evidence_ref(OPERATOR_WAIVER),
        },
    }
    human_review_queue = {
        "status": "pass" if retired and waiver_ok else "pending",
        "queue_item_count": 0,
        "human_signed_count": 0,
        "human_review_requirement_waived": waiver_ok,
        "legacy_compiler_review_queue_retired": retired,
        "evidence": retirement_evidence,
    }
    scheduler = {
        "scheduler_exact_812x3_machine_proof": {
            "status": "pass" if materialized else "fail",
            "case_count": 812 if materialized else 0,
            "record_slot_count": len(jobs),
            "per_agent": per_agent,
            "fallback_contract_count": 0 if materialized else None,
            "all_2436_slots_declare_reset": materialized,
            "formal_launch_eligible": False,
            "source": "hash_checked_materialized_full_jobs_index",
        },
        "scheduler_prelock_fail_closed": {
            "status": "pass" if materialized else "fail",
            "jobs_written": materialized,
            "legacy_planner_runtime_dependency": False,
            "materialized_index_sidecar_valid": bool(
                materialized
                and _sidecar_valid(FORMAL_SCHEDULER_JOBS_ROOT / "index.json")
            ),
        },
        "scheduler_formal_812x3_jobs": {
            "status": "pass" if materialized else "fail",
            "planned_record_slot_count": 2436,
            "materialized_record_slot_count": len(jobs),
            "fallback_contract_count": 0 if materialized else None,
            "formal_launch_eligible": materialized,
            "all_2436_jobs_declare_reset": materialized,
            "all_2436_jobs_bind_operator_waiver": materialized and waiver_ok,
            "operator_waiver_sha256": waiver_sha256,
            "human_signoff_claimed": False,
            "human_signed_count": 0,
            "result_namespace": index.get("result_namespace"),
            "jobs_sha256": index.get("jobs_sha256"),
            "legacy_compiler_runtime_dependency": False,
            "reason": materialized_error,
        },
    }
    return {
        "native": native,
        "human_review_queue": human_review_queue,
        "scheduler": scheduler,
        "receipt_valid": receipt_valid,
        "package_absent": package_absent,
        "retired": retired,
        "deletion_state": deletion.get("state"),
    }


def build_acceptance(
    *,
    source_bundle_path: Path = DEFAULT_SOURCE_BUNDLE,
    expected_packet_index_core_sha256: str | None = None,
    openrouter_credential_status: str = "unverified",
    observed_free_gb: Mapping[str, float] | None = None,
    historical_secret_file_count: int | None = None,
    historical_secret_occurrence_count: int | None = None,
    active_key_exact_match_count: int | None = None,
) -> dict[str, Any]:
    environment = validate_receipts()
    evaluator = validate_official_evaluator_route(environment)
    packets = validate_packets(
        source_bundle_path=source_bundle_path,
        expected_packet_index_core_sha256=expected_packet_index_core_sha256,
    )
    retired_compiler = validate_retired_compiler_and_materialized_schedule()
    native = retired_compiler["native"]
    human_review_queue = retired_compiler["human_review_queue"]
    scheduler = retired_compiler["scheduler"]
    golden_parity = validate_golden_parity_aggregate()
    reset_smoke = validate_reset_smoke_aggregate()
    extended_reset = validate_extended_reset_aggregate()
    full_reset_coverage = validate_full_six_site_reset_coverage(
        reset_smoke,
        extended_reset,
    )
    site_data_lock = validate_site_data_lock_aggregate()
    site_deployment = validate_site_deployment_aggregate()
    browser_acceptance = validate_real_browser_acceptance()
    six_site_deployment = validate_six_site_deployment_and_browser(
        site_deployment,
        browser_acceptance,
    )
    security = validate_security_and_gold_isolation()
    credential = validate_openrouter_credential(openrouter_credential_status)
    formal_run_control = validate_formal_run_control()
    hygiene = repository_hygiene_observation(
        file_count=historical_secret_file_count,
        occurrence_count=historical_secret_occurrence_count,
        active_key_exact_match_count=active_key_exact_match_count,
    )
    storage = validate_storage_readiness(observed_free_gb)
    pilot_storage_preflight = validate_pilot_storage_capacity_preflight(storage)
    future = validate_pilot_fault_and_budget()

    machine_gates = {
        "frozen_environment": environment,
        "official_evaluator_route": evaluator,
        "source_rich_812_packets": packets,
        "native_contract_machine_validation": native[
            "native_contract_machine_validation"
        ],
        "native_human_review_queue": human_review_queue,
        "scheduler_exact_812x3_machine_proof": scheduler[
            "scheduler_exact_812x3_machine_proof"
        ],
        "scheduler_prelock_fail_closed": scheduler[
            "scheduler_prelock_fail_closed"
        ],
        "official_cli_adapter_golden_parity": golden_parity,
        "real_four_site_reset_smoke": reset_smoke,
        "three_host_site_data_lock": site_data_lock,
        "local_fault_classification": future["local_fault_classification"],
        "static_publication_secret_scan": security[
            "static_publication_secret_scan"
        ],
        "static_model_input_gold_isolation": security[
            "static_model_input_gold_isolation"
        ],
    }
    machine_validation_status = (
        "pass"
        if all(gate.get("status") == "pass" for gate in machine_gates.values())
        else "fail"
    )
    operational_gates = {
        "native_contract_human_signoff": native[
            "native_contract_human_signoff"
        ],
        "native_contract_operator_waiver": native[
            "native_contract_operator_waiver"
        ],
        "scheduler_formal_812x3_jobs": scheduler[
            "scheduler_formal_812x3_jobs"
        ],
        "six_site_deployment_and_login": six_site_deployment,
        "full_six_site_per_slot_reset_coverage": full_reset_coverage,
        "openrouter_credential": credential,
        "real_abc_pilot_and_artifacts": future["real_abc_pilot_and_artifacts"],
        "fault_injection": future["fault_injection"],
        "pilot_runtime_secret_and_gold_scan": security[
            "pilot_runtime_secret_and_gold_scan"
        ],
        "pilot_cost_runtime_storage_budget": future[
            "pilot_cost_runtime_storage_budget"
        ],
        "storage_readiness": storage,
        "pilot_storage_capacity_preflight": pilot_storage_preflight,
        "formal_remote_retention_run_control": formal_run_control,
    }
    blocker_messages = {
        "native_contract_human_signoff": (
            "812 native contracts/checklists still require hash-bound human source-check signoff"
        ),
        "native_contract_operator_waiver": (
            "the explicit hash-bound machine-only operator waiver is not valid"
        ),
        "scheduler_formal_812x3_jobs": (
            "the exact fallback-free 2,436-job formal schedule has not been materialized"
        ),
        "six_site_deployment_and_login": (
            "six WebArena sites are not yet proven deployed and logged in on all three VPSes"
        ),
        "full_six_site_per_slot_reset_coverage": (
            "per-slot reset proof does not yet cover all six sites"
        ),
        "openrouter_credential": "OpenRouter credential is not currently pilot-ready",
        "real_abc_pilot_and_artifacts": (
            "the real 24-slot A/B/C pilot and HAR/trace/reset/native artifacts are missing"
        ),
        "fault_injection": (
            "login/site/API/evaluator fault-injection acceptance is missing"
        ),
        "pilot_runtime_secret_and_gold_scan": (
            "pilot runtime secret/cookie and gold-leakage scan is missing"
        ),
        "pilot_cost_runtime_storage_budget": (
            "pilot cost/runtime/storage budget report is missing"
        ),
        "storage_readiness": (
            "storage does not satisfy the hash-bound 350 GB free-space launch gate"
        ),
        "pilot_storage_capacity_preflight": (
            "the three-host pilot storage capacity preflight is incomplete"
        ),
        "formal_remote_retention_run_control": (
            "formal run-control has not passed SSH remote-retention canary and launch gates"
        ),
    }
    def operational_gate_satisfied(name: str) -> bool:
        status = operational_gates[name].get("status")
        return status == "pass" or (
            name == "native_contract_human_signoff"
            and status == "waived"
            and operational_gates[
                "native_contract_operator_waiver"
            ].get("status")
            == "pass"
        ) or (
            name == "native_contract_operator_waiver"
            and status == "not_applicable"
            and operational_gates[
                "native_contract_human_signoff"
            ].get("status")
            == "pass"
        )

    blockers = [
        blocker_messages[name]
        for name, gate in operational_gates.items()
        if not operational_gate_satisfied(name)
    ]
    pre_pilot_gate_names = (
        "native_contract_human_signoff",
        "native_contract_operator_waiver",
        "scheduler_formal_812x3_jobs",
        "six_site_deployment_and_login",
        "full_six_site_per_slot_reset_coverage",
        "openrouter_credential",
        "fault_injection",
        "pilot_storage_capacity_preflight",
    )
    pilot_launch_eligible = (
        machine_validation_status == "pass"
        and all(
            operational_gate_satisfied(name)
            for name in pre_pilot_gate_names
        )
    )
    step20_complete = machine_validation_status == "pass" and not blockers
    formal_launch_eligible = step20_complete
    return {
        "schema_version": "webarena_verified_step20_aggregate_acceptance/v2",
        "status": "pass" if step20_complete else "blocked",
        "benchmark": "WebArena-Verified",
        "version": "v1.2.3",
        "split": "full",
        "step20_complete": step20_complete,
        "pilot_launch_eligible": pilot_launch_eligible,
        "formal_2436_launch_eligible": formal_launch_eligible,
        "formal_paid_launch_ready": (
            formal_launch_eligible
            and formal_run_control.get("formal_paid_launch_ready") is True
        ),
        "draft_policy": {
            "unique_formal_score_draft_provider": "neurips_ed_track_minimal",
            "legacy_native_claim_compiler_retired": retired_compiler["retired"],
            "legacy_native_claim_package_absent": retired_compiler[
                "package_absent"
            ],
            "legacy_hashes_in_materialized_jobs_are_lineage_only": True,
            "retirement_receipt": evidence_ref(
                NATIVE_CLAIM_COMPILER_RETIREMENT
            ),
        },
        "machine_validation_status": machine_validation_status,
        "machine_gates": machine_gates,
        "operational_gates": operational_gates,
        "blocking_reasons": blockers,
        "pre_pilot_blocking_reasons": [
            blocker_messages[name]
            for name in pre_pilot_gate_names
            if not operational_gate_satisfied(name)
        ],
        "non_blocking_repository_hygiene": hygiene,
        "requested_scope": {
            "identical_three_vps_environment": environment,
            "official_evaluator_deployed_and_routed": evaluator,
            "full_812_case_packets": packets,
            "six_site_deployment_receipts": site_deployment,
            "independent_real_browser_acceptance": browser_acceptance,
        },
        "scope_boundary": {
            "base_subset_status": "pass",
            "benchmark_websites_deployed": site_deployment.get("status") == "pass",
            "benchmark_websites_real_browser_verified": (
                browser_acceptance.get("status") == "pass"
            ),
            "per_case_reset_controller_completed": (
                operational_gates["full_six_site_per_slot_reset_coverage"].get(
                    "status"
                )
                == "pass"
            ),
            "golden_cli_adapter_parity_completed": golden_parity.get("status")
            == "pass",
            "golden_model_pilot_completed": future[
                "real_abc_pilot_and_artifacts"
            ].get("status")
            == "pass",
            "formal_2436_runs_completed": False,
            "note": (
                "Step 20 authorizes launch only after every operational gate passes. "
                "The formal 2,436 runs remain Step 21 work."
            ),
        },
        "security_attestation": {
            "dotenv_read_by_builder": False,
            "credential_values_recorded": False,
            "credential_value_hashes_recorded": False,
            "machine_pass_does_not_imply_human_signoff": True,
            "machine_preview_does_not_authorize_execution": True,
            "operator_waiver_is_not_human_signoff": True,
            "human_signed_count_under_operator_waiver": 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--source-bundle",
        type=Path,
        default=DEFAULT_SOURCE_BUNDLE,
        help="Canonical WebArena-Verified full-812 contract source bundle.",
    )
    parser.add_argument(
        "--expected-packet-index-core-sha256",
        default=None,
        help=(
            "Optional external pin for index_core_sha256. The index is always "
            "independently self-verified even when this option is omitted."
        ),
    )
    parser.add_argument(
        "--openrouter-credential-status",
        choices=("invalid_401_user_not_found", "unverified", "valid"),
        default="unverified",
        help=(
            "Secret-free operational observation. 'valid' is not accepted as a "
            "pass without the dedicated three-model credential receipt."
        ),
    )
    parser.add_argument(
        "--observed-free-gb",
        action="append",
        default=[],
        metavar="MACHINE_ID=GB",
        help=(
            "Optional approximate free-space observation. Repeat for all three "
            "WebArena machines; it cannot produce a pass without a hash-bound receipt."
        ),
    )
    parser.add_argument("--historical-secret-file-count", type=int, default=None)
    parser.add_argument("--historical-secret-occurrence-count", type=int, default=None)
    parser.add_argument("--active-key-exact-match-count", type=int, default=None)
    args = parser.parse_args()
    observed_free_gb: dict[str, float] = {}
    for raw in args.observed_free_gb:
        machine_id, separator, value = raw.partition("=")
        if not separator or not machine_id or machine_id in observed_free_gb:
            parser.error(f"invalid or duplicate --observed-free-gb value: {raw!r}")
        try:
            observed_free_gb[machine_id] = float(value)
        except ValueError:
            parser.error(f"invalid --observed-free-gb number: {raw!r}")
    acceptance = build_acceptance(
        source_bundle_path=args.source_bundle,
        expected_packet_index_core_sha256=args.expected_packet_index_core_sha256,
        openrouter_credential_status=args.openrouter_credential_status,
        observed_free_gb=observed_free_gb or None,
        historical_secret_file_count=args.historical_secret_file_count,
        historical_secret_occurrence_count=args.historical_secret_occurrence_count,
        active_key_exact_match_count=args.active_key_exact_match_count,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(acceptance, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    digest = sha256_file(args.output)
    args.output.with_name(args.output.name + ".sha256").write_text(
        f"{digest}  {args.output.name}\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "written",
                "acceptance_status": acceptance["status"],
                "formal_2436_launch_eligible": acceptance[
                    "formal_2436_launch_eligible"
                ],
                "output": str(args.output),
                "sha256": digest,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
