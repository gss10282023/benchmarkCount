#!/usr/bin/env python3
"""Audit draft-checklist outputs for the four source-rich benchmark packets.

The audit is intentionally read-only.  It separates deterministic acceptance
failures (coverage, bytes, schema, provenance and sealed-input/runtime policy)
from conservative semantic findings that need reviewer attention.  The latter
never rewrite or silently "repair" a draft.

Examples:

  python scripts/audit_four_benchmark_drafts.py \
    --target osworld_verified experiments/case_packets/osworld_verified /tmp/drafts \
    --json-report /tmp/audit.json --markdown-report /tmp/audit.md

  python scripts/audit_four_benchmark_drafts.py \
    --target osworld_verified PACKETS_1 DRAFTS_1 \
    --target osworld_2_0 PACKETS_2 DRAFTS_2 \
    --target terminal_bench_2_1 PACKETS_3 DRAFTS_3 \
    --target swe_bench_pro PACKETS_4 DRAFTS_4 \
    --json-report audit.json --markdown-report audit.md

Draft directories may be named either ``CASE_ID`` or
``BENCHMARK__CASE_ID``.  This permits all four benchmarks to share a flattened
batch output root while preserving exact per-benchmark coverage checks.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from neurips_ed_track_minimal.checklist_guardrails import (  # noqa: E402
    ChecklistGuardrailError,
    case_packet_support_paths,
    validate_checklist_guardrails,
)
from neurips_ed_track_minimal.scripts import checklist_validator  # noqa: E402
from neurips_ed_track_minimal.scripts import draft_case_checklist as drafter  # noqa: E402


REPORT_SCHEMA = "four_benchmark_draft_audit.v1"
SUPPORTED_BENCHMARKS = (
    "osworld_verified",
    "osworld_2_0",
    "terminal_bench_2_1",
    "swe_bench_pro",
)
CANONICAL_SUFFIXES = (
    "checklist.yaml",
    "checklist.json",
    "api_response.json",
    "llm_call.json",
    "reasoning_summary.txt",
    "stderr.log",
    "stdout.log",
)
ROOT_BATCH_FILES = frozenset({"_batch_results.jsonl", "_batch_summary.json"})
EXPECTED_STDIN_COMPONENTS = (
    "draft_instructions.md",
    "template.yaml",
    "case_packet.md",
    "output_schema.json",
)
EXPECTED_LLM_FIELDS = frozenset(
    {
        "schema_version",
        "provider",
        "model",
        "model_version",
        "api_key_env",
        "domain",
        "case_unit_id",
        "task_id",
        "phase",
        "experiment_type",
        "agent_id_or_role",
        "request_timestamp",
        "response_timestamp",
        "temperature",
        "max_tokens",
        "timeout_seconds",
        "retry_index",
        "token_usage",
        "cost",
        "response_metadata",
    }
)
EXPECTED_API_FIELDS = frozenset(
    {"id", "status", "model", "provider", "output_text", "output", "usage", "codex_cli"}
)
EXPECTED_CODEX_FIELDS = frozenset(
    {
        "auth_mode",
        "returncode",
        "timeout_seconds",
        "sandbox",
        "command",
        "stdin_bundle",
        "events",
        "malformed_event_lines",
        "stderr",
    }
)

FORBIDDEN_ITEM_TYPES = frozenset(
    {
        "command_execution",
        "shell",
        "shell_command",
        "tool",
        "tool_call",
        "function_call",
        "file_change",
        "file_read",
        "file_write",
        "apply_patch",
        "web_search",
        "web_fetch",
        "browser",
        "computer",
        "mcp_tool_call",
        "image_generation",
    }
)
TRANSPORT_ERROR_TERMS = (
    "websocket",
    "websockets",
    "https transport",
    "reconnecting",
    "connection reset",
    "connection closed",
    "stream disconnected",
    "transport error",
)

PRIOR_PUBLIC_RUN_REFERENCE_RE = re.compile(
    r"(?ix)\b(?:public|prior|previous|published|leaderboard)\s+"
    r"(?:agent\s+)?(?:run|trajectory|submission|patch|output|artifact|result|score)s?\b"
)
GENERIC_RESULT_ASSERTION_RE = re.compile(
    r"(?ix)(?:"
    r"\b(?:the|this|a)\s+(?:agent|run|trajectory|submission|patch|output|artifact|result)\s+"
    r"(?:has\s+|was\s+|is\s+)?(?:passed|failed|succeeded|completed|produced|generated|"
    r"achieved|obtained|returned|scored|demonstrates?|shows?|proves?|contains?)\b"
    r"|\b(?:achieved|obtained|received|scored)\s+(?:a\s+)?"
    r"(?:score\s+of\s+)?[0-9]+(?:\.[0-9]+)?\b"
    r")"
)
CONDITIONAL_OR_BOUNDARY_RE = re.compile(
    r"(?ix)\b(?:if|when|unless|would|should|must|unknown|not\s+known|"
    r"do\s+not\s+(?:assume|use)|must\s+not\s+(?:assume|use)|"
    r"without\s+(?:assuming|using)|"
    r"no\s+(?:prior|public|previous)\s+run|future\s+run|post[- ]run)\b"
)
EVIDENCE_INSUFFICIENCY_RE = re.compile(
    r"(?ix)(?:"
    r"\bneither\b.{0,220}\b(?:establish(?:es)?|determine(?:s)?|resolve(?:s)?|"
    r"reconstruct(?:s)?|verify|attribute)\b"
    r"|\bno\s+(?:valid|trustworthy|readable|completed|complete|attributable|"
    r"unambiguous|reliable|final|official|evaluator[- ]time|case[- ]linked|run[- ]matched|"
    r"parseable\s+)*?(?:official\s+|evaluator\s+|final\s+)?"
    r"(?:score|outcome|result|record|evidence|trace)\s+(?:is\s+)?"
    r"(?:retained|available|recoverable|readable|parseable|attributable|trustworthy)\b"
    r"|\b(?:retained|stored|remaining|review)\s+"
    r"(?:evidence|records?|artifacts?|results?|scores?|outcomes?|logs?|traces?|"
    r"trajector(?:y|ies)|(?:evaluator|verifier)\s+outputs?|outputs?|files?)"
    r"(?:\s*/\s*(?:records?|artifacts?|logs?))?"
    r".{0,140}\b(?:missing|absent|unavailable|unreadable|unparseable|malformed|"
    r"corrupt(?:ed)?|truncated|incomplete|insufficient|ambiguous|untrustworthy|"
    r"invalid|conflict(?:s|ing)?|contradict(?:s|ory)?|inconsistent|irreconcilable|"
    r"misassociated|not\s+attributable|cannot\s+be\s+(?:tied|linked|associated|resolved))\b"
    r"|\b(?:missing|absent|unavailable|unreadable|unparseable|malformed|corrupt(?:ed)?|"
    r"truncated|incomplete|insufficient|ambiguous|conflicting|contradictory|"
    r"inconsistent|irreconcilable)\s+(?:retained\s+|stored\s+)?"
    r"(?:evidence|records?|artifacts?|results?|scores?|outcomes?|logs?|traces?|"
    r"trajector(?:y|ies)|(?:evaluator|verifier)\s+outputs?|outputs?|files?)\b"
    r"|\b(?:remaining|retained|stored)\s+(?:artifacts?|records?|evidence).{0,100}"
    r"(?:do|does)\s+not\s+(?:establish|determine|preserve|suffice|resolve|verify)\b"
    r"|\b(?:attribution|association|integrity|provenance|run\s+identity|task\s+identity)"
    r".{0,80}\b(?:cannot\s+be|is\s+not|are\s+not)\s+"
    r"(?:resolved|established|verified|determined|tied|linked|attributed)\b"
    r"|\b(?:cannot|can\s+not|unable\s+to|fails?\s+to)\s+"
    r"(?:determine|establish|reconstruct|resolve|verify|attribute|parse|recover)\b"
    r"|\b(?:insufficient|incomplete|contradictory|conflicting|ambiguous)\s+"
    r"(?:retained\s+|stored\s+|review\s+)?evidence\b"
    r"|\bevidence[- ]retention\s+gap\b"
    r")"
)
ORDINARY_FAILURE_RE = re.compile(
    r"(?ix)\b(?:test(?:s)?\s+(?:fail|fails|failed)|evaluator\s+(?:fails|returns?\s+0)|"
    r"verifier\s+(?:fails|exits?\s+non[- ]?zero)|score\s+(?:is\s+)?(?:0|below|less)|"
    r"wrong|incorrect|does\s+not\s+satisfy|required\s+(?:task\s+)?output\s+is\s+absent)\b"
)
EVIDENCE_OBJECT_RE = re.compile(
    r"(?ix)(?:\bparsed_test_output(?:\.json)?\b|\b(?:score|reward(?:\.txt)?|ctrf(?:\.json)?|reports?|"
    r"result(?:\.txt|\.json)?|evidence|artifacts?|records?|logs?|"
    r"runtime\.log|traces?|trajector(?:y|ies)|outputs?|files?|outcomes?|evaluation|"
    r"evaluator|verifier|getter|metric|final[- ]action|workbooks?|documents?|presentations?|"
    r"images?|urls?|tabs?|state|attribution|association|integrity|provenance|"
    r"run\s+identity|task\s+identity)\b)"
)
EVIDENCE_GAP_RE = re.compile(
    r"(?ix)(?:\b(?:missing|absent|unavailable|unreadable|unparseable|malformed|"
    r"corrupt(?:ed)?|truncated|incomplete|insufficient|ambiguous|untrustworthy|loss|"
    r"unreliable|invalid|conflict(?:s|ing)?|contradict(?:s|ory)?|inconsistent|"
    r"irreconcilable|misassociated|unattributable|not\s+attributable|not\s+tied|"
    r"cannot|can\s+not|unable|neither|lacks?|lack\s+of|failed\s+attribution|"
    r"inconsisten(?:cy|t)|does\s+not\s+(?:establish|determine|preserve|identify|"
    r"suffice|resolve|verify|include|contain)|do\s+not\s+(?:establish|determine|"
    r"preserve|identify|suffice|resolve|verify|include|contain)|not\s+enough|"
    r"no\s+retained|"
    r"no\s+(?:valid|trustworthy|readable|completed|complete|attributable|reliable|"
    r"official|final|parseable|usable))\b|\bdisagree\b|\bdifferent\s+runs\b)"
)

# A source task can require backward compatibility with an earlier API/output
# shape.  That is not an assertion that a prior benchmark trajectory or score
# was available to the drafter.
TASK_BACKWARD_COMPATIBILITY_RE = re.compile(
    r"(?ix)\b(?:preserv(?:e|es|ed|ing)|maintain(?:s|ed|ing)?|keep(?:s|ing)?|"
    r"remain(?:s|ed|ing)?|backward[- ]compatib(?:le|ility))\b.{0,100}"
    r"\b(?:prior|previous|existing|legacy)\b.{0,80}"
    r"\b(?:output|behavior|behaviour|format|structure|schema|api|semantics?)\b"
)


@dataclass(frozen=True)
class TargetSpec:
    benchmark: str
    packet_root: Path
    draft_root: Path


@dataclass(frozen=True)
class PacketInfo:
    case_unit_id: str
    task_id: str
    domain: str
    directory_name: str
    path: Path
    text: str
    sha256: str


class CaseAudit:
    """Mutable recorder for one case; serialized as a plain JSON object."""

    def __init__(self, benchmark: str, packet: PacketInfo, draft_dir: Path | None) -> None:
        self.data: dict[str, Any] = {
            "benchmark": benchmark,
            "case_unit_id": packet.case_unit_id,
            "task_id": packet.task_id,
            "packet_path": str(packet.path),
            "packet_sha256": packet.sha256,
            "draft_directory": str(draft_dir) if draft_dir else None,
            "status": "failed",
            "checks": {},
            "errors": [],
            "findings": [],
        }

    def passed(self, name: str, **details: Any) -> None:
        self.data["checks"][name] = {"status": "passed", **details}

    def failed(self, name: str, code: str, message: str, **details: Any) -> None:
        self.data["checks"][name] = {"status": "failed", **details}
        self.data["errors"].append({"code": code, "check": name, "message": message})

    def finding(
        self,
        code: str,
        message: str,
        *,
        severity: str = "medium",
        location: str | None = None,
        excerpt: str | None = None,
    ) -> None:
        item = {"severity": severity, "code": code, "message": message}
        if location is not None:
            item["location"] = location
        if excerpt is not None:
            item["excerpt"] = excerpt[:500]
        self.data["findings"].append(item)

    def finish(self) -> dict[str, Any]:
        if self.data["errors"]:
            self.data["status"] = "failed"
        elif self.data["findings"]:
            self.data["status"] = "passed_with_findings"
        else:
            self.data["status"] = "passed"
        return self.data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        nargs=3,
        action="append",
        metavar=("BENCHMARK", "CASE_PACKET_ROOT", "DRAFT_OUTPUT_ROOT"),
        help="Repeatable benchmark/packet-root/draft-root triple",
    )
    parser.add_argument("--benchmark", choices=SUPPORTED_BENCHMARKS)
    parser.add_argument("--case-packet-root", type=Path)
    parser.add_argument("--draft-output-root", type=Path)
    parser.add_argument(
        "--runtime-root",
        type=Path,
        default=REPO_ROOT / "neurips_ed_track_minimal",
        help="Local neurips_ed_track_minimal tree used to reconstruct sealed stdin",
    )
    parser.add_argument(
        "--prompt-supplement",
        type=Path,
        default=None,
        help="Optional supplement used for every audited draft run",
    )
    parser.add_argument(
        "--case-prompt-supplement",
        nargs=3,
        action="append",
        metavar=("BENCHMARK", "CASE_ID", "PATH"),
        help=(
            "Case-specific supplement override; repeat for repaired cases whose "
            "sealed prompt differs from the base batch"
        ),
    )
    parser.add_argument("--expected-provider", default="codex_cli")
    parser.add_argument("--expected-model", default="gpt-5.6-sol")
    parser.add_argument("--expected-reasoning-effort", default="max")
    parser.add_argument("--json-report", type=Path, required=True)
    parser.add_argument("--markdown-report", type=Path, required=True)
    parser.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="Return nonzero for conservative semantic findings as well as hard failures",
    )
    return parser.parse_args()


def _targets_from_args(args: argparse.Namespace) -> list[TargetSpec]:
    triples = list(args.target or [])
    singular = (args.benchmark, args.case_packet_root, args.draft_output_root)
    if any(value is not None for value in singular):
        if not all(value is not None for value in singular):
            raise SystemExit(
                "--benchmark, --case-packet-root and --draft-output-root must be supplied together"
            )
        triples.append([str(args.benchmark), str(args.case_packet_root), str(args.draft_output_root)])
    if not triples:
        raise SystemExit("At least one --target or one complete singular target is required")

    targets: list[TargetSpec] = []
    seen: set[tuple[str, Path, Path]] = set()
    for raw_benchmark, raw_packet_root, raw_draft_root in triples:
        if raw_benchmark not in SUPPORTED_BENCHMARKS:
            raise SystemExit(
                f"Unsupported benchmark {raw_benchmark!r}; choose from {SUPPORTED_BENCHMARKS}"
            )
        target = TargetSpec(
            benchmark=raw_benchmark,
            packet_root=Path(raw_packet_root).expanduser().resolve(),
            draft_root=Path(raw_draft_root).expanduser().resolve(),
        )
        identity = (target.benchmark, target.packet_root, target.draft_root)
        if identity in seen:
            raise SystemExit(f"Duplicate target: {identity}")
        seen.add(identity)
        targets.append(target)
    return targets


def _case_prompt_supplements_from_args(
    args: argparse.Namespace,
) -> dict[tuple[str, str], Path]:
    supplements: dict[tuple[str, str], Path] = {}
    for raw_benchmark, case_id, raw_path in args.case_prompt_supplement or []:
        if raw_benchmark not in SUPPORTED_BENCHMARKS:
            raise SystemExit(
                f"Unsupported case-supplement benchmark {raw_benchmark!r}; "
                f"choose from {SUPPORTED_BENCHMARKS}"
            )
        if (
            not case_id
            or case_id in {".", ".."}
            or "/" in case_id
            or "\\" in case_id
            or "\x00" in case_id
        ):
            raise SystemExit(
                f"Case-supplement CASE_ID must be one safe path component: {case_id!r}"
            )
        key = (raw_benchmark, case_id)
        if key in supplements:
            raise SystemExit(f"Duplicate case-prompt supplement: {key}")
        supplements[key] = Path(raw_path).expanduser().resolve()
    return supplements


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a YAML object, got {type(value).__name__}")
    return value


def _is_safe_regular(path: Path) -> bool:
    return path.is_file() and not path.is_symlink()


def _read_packets(target: TargetSpec) -> tuple[dict[str, PacketInfo], list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    packets: dict[str, PacketInfo] = {}
    if not target.packet_root.is_dir() or target.packet_root.is_symlink():
        return {}, [
            {
                "code": "packet_root_missing_or_unsafe",
                "message": f"Packet root is missing, not a directory, or a symlink: {target.packet_root}",
            }
        ]
    paths = sorted(target.packet_root.glob("*/case_packet.md"))
    if not paths:
        return {}, [
            {
                "code": "packet_coverage_empty",
                "message": f"No */case_packet.md files found under {target.packet_root}",
            }
        ]
    for path in paths:
        try:
            if not _is_safe_regular(path) or path.parent.is_symlink():
                raise ValueError("packet or case directory is a symlink/unsafe")
            text = path.read_text(encoding="utf-8")
            metadata = drafter.extract_case_metadata(text)
            case_id = metadata["case_unit_id"]
            if metadata["domain"] != target.benchmark:
                raise ValueError(
                    f"domain {metadata['domain']!r} does not equal target {target.benchmark!r}"
                )
            if path.parent.name != case_id:
                raise ValueError(
                    f"directory {path.parent.name!r} differs from case_unit_id {case_id!r}"
                )
            if case_id in packets:
                raise ValueError(f"duplicate case_unit_id {case_id!r}")
            packets[case_id] = PacketInfo(
                case_unit_id=case_id,
                task_id=metadata["task_id"],
                domain=metadata["domain"],
                directory_name=path.parent.name,
                path=path.resolve(),
                text=text,
                sha256=_sha256_bytes(text.encode("utf-8")),
            )
        except Exception as exc:
            errors.append(
                {
                    "code": "invalid_case_packet_identity",
                    "message": f"{path}: {type(exc).__name__}: {exc}",
                }
            )
    return packets, errors


def _candidate_output_names(benchmark: str, case_id: str) -> tuple[str, str]:
    return case_id, f"{benchmark}__{case_id}"


def _discover_draft_dirs(
    target: TargetSpec, packets: Mapping[str, PacketInfo]
) -> tuple[dict[str, Path], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    mapping: dict[str, Path] = {}
    if not target.draft_root.is_dir() or target.draft_root.is_symlink():
        return {}, [
            {
                "code": "draft_root_missing_or_unsafe",
                "message": f"Draft root is missing, not a directory, or a symlink: {target.draft_root}",
            }
        ]
    used_names: set[str] = set()
    for case_id in sorted(packets):
        candidates = [
            target.draft_root / name
            for name in _candidate_output_names(target.benchmark, case_id)
            if (target.draft_root / name).exists()
        ]
        if len(candidates) > 1:
            errors.append(
                {
                    "code": "duplicate_draft_case_directory",
                    "case_unit_id": case_id,
                    "message": f"Both exact and namespaced draft directories exist: {candidates}",
                }
            )
            continue
        if not candidates:
            continue
        candidate = candidates[0]
        if not candidate.is_dir() or candidate.is_symlink():
            errors.append(
                {
                    "code": "unsafe_draft_case_directory",
                    "case_unit_id": case_id,
                    "message": f"Draft case path is not a safe directory: {candidate}",
                }
            )
            continue
        mapping[case_id] = candidate
        used_names.add(candidate.name)

    for entry in sorted(target.draft_root.iterdir(), key=lambda item: item.name):
        if entry.name in used_names or entry.name in ROOT_BATCH_FILES:
            continue
        if entry.name.startswith(tuple(f"{name}__" for name in SUPPORTED_BENCHMARKS if name != target.benchmark)):
            # A different target sharing the flattened root.
            continue
        if entry.is_dir() and not entry.is_symlink():
            checklist_path = entry / "checklist.yaml"
            if _is_safe_regular(checklist_path):
                try:
                    metadata = _load_yaml_mapping(checklist_path)
                except Exception:
                    metadata = {}
                if metadata.get("domain") in SUPPORTED_BENCHMARKS and metadata.get("domain") != target.benchmark:
                    continue
            errors.append(
                {
                    "code": "extra_draft_case_directory",
                    "message": f"Unexpected directory for {target.benchmark}: {entry}",
                }
            )
        elif entry.is_file() and entry.name.startswith("_"):
            errors.append(
                {
                    "code": "extra_draft_root_file",
                    "message": f"Unexpected batch metadata file: {entry}",
                }
            )

    missing = sorted(set(packets) - set(mapping))
    if missing:
        errors.append(
            {
                "code": "missing_draft_cases",
                "message": f"Missing {len(missing)} draft case directories",
                "case_unit_ids": missing,
            }
        )
    return mapping, errors


def _load_batch_metadata(root: Path) -> tuple[dict[str, Any] | None, dict[str, dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    summary_path = root / "_batch_summary.json"
    results_path = root / "_batch_results.jsonl"
    summary: dict[str, Any] | None = None
    rows: dict[str, dict[str, Any]] = {}
    if not _is_safe_regular(summary_path):
        errors.append(
            {"code": "batch_summary_missing", "message": f"Missing safe file: {summary_path}"}
        )
    else:
        try:
            value = _load_json(summary_path)
            if not isinstance(value, dict):
                raise ValueError("summary is not an object")
            summary = value
            for field in ("total_cases", "completed_cases", "success_cases", "failed_cases"):
                if not isinstance(summary.get(field), int):
                    raise ValueError(f"{field} is not an integer")
            if summary.get("completed_cases") != summary.get("total_cases"):
                errors.append(
                    {
                        "code": "batch_incomplete",
                        "message": f"Batch completed {summary.get('completed_cases')} of {summary.get('total_cases')} cases",
                    }
                )
            if summary.get("failed_cases") != 0 or summary.get("not_run_case_count", 0) != 0:
                errors.append(
                    {
                        "code": "batch_has_failed_or_not_run_cases",
                        "message": (
                            f"failed_cases={summary.get('failed_cases')}, "
                            f"not_run_case_count={summary.get('not_run_case_count', 0)}"
                        ),
                    }
                )
        except Exception as exc:
            errors.append(
                {
                    "code": "invalid_batch_summary",
                    "message": f"{summary_path}: {type(exc).__name__}: {exc}",
                }
            )
    if not _is_safe_regular(results_path):
        errors.append(
            {"code": "batch_results_missing", "message": f"Missing safe file: {results_path}"}
        )
    else:
        try:
            for line_number, line in enumerate(results_path.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip():
                    raise ValueError(f"blank line {line_number}")
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"line {line_number} is not an object")
                case_dir = str(value.get("case_unit_dir") or "")
                if not case_dir:
                    raise ValueError(f"line {line_number} lacks case_unit_dir")
                if case_dir in rows:
                    raise ValueError(f"duplicate case_unit_dir {case_dir!r}")
                rows[case_dir] = value
            if summary is not None and len(rows) != summary.get("completed_cases"):
                errors.append(
                    {
                        "code": "batch_result_count_mismatch",
                        "message": f"Results rows={len(rows)} but completed_cases={summary.get('completed_cases')}",
                    }
                )
        except Exception as exc:
            errors.append(
                {
                    "code": "invalid_batch_results",
                    "message": f"{results_path}: {type(exc).__name__}: {exc}",
                }
            )
    return summary, rows, errors


def _iter_text(node: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(node, Mapping):
        for key, value in node.items():
            yield from _iter_text(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _iter_text(value, f"{path}[{index}]")
    elif isinstance(node, str):
        yield path, node


def _iter_support_pointers(node: Any) -> Iterable[str]:
    if isinstance(node, Mapping):
        for key, value in node.items():
            if key == "support" and isinstance(value, list):
                yield from (str(item) for item in value)
            else:
                yield from _iter_support_pointers(value)
    elif isinstance(node, list):
        for value in node:
            yield from _iter_support_pointers(value)


def prior_run_findings(checklist: Mapping[str, Any], reasoning_summary: str = "") -> list[dict[str, str]]:
    """Return only explicit assertions that a prior/public run result is known."""

    findings: list[dict[str, str]] = []
    sources = [(*item, False) for item in _iter_text(checklist)]
    if reasoning_summary.strip():
        sources.append(("reasoning_summary.txt", reasoning_summary, True))
    for location, text, is_reasoning in sources:
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
            asserted = PRIOR_PUBLIC_RUN_REFERENCE_RE.search(sentence) is not None
            # Checklist fields are themselves conditional scoring rules and evidence
            # questions.  Generic "this run"/"reported score" wording in those
            # fields is not proof that a prior output was supplied to the drafter.
            # In free-form reasoning, however, an unconditional claim that a run
            # already achieved a result is still worth surfacing.
            if is_reasoning:
                asserted = asserted or GENERIC_RESULT_ASSERTION_RE.search(sentence) is not None
            if not asserted:
                continue
            if CONDITIONAL_OR_BOUNDARY_RE.search(sentence):
                continue
            if TASK_BACKWARD_COMPATIBILITY_RE.search(sentence):
                continue
            findings.append(
                {
                    "code": "prior_or_public_run_treated_as_known",
                    "location": location,
                    "message": "Draft appears to assert a prior/public benchmark run result as a known fact",
                    "excerpt": sentence.strip()[:500],
                }
            )
    return findings


def undecided_findings(checklist: Mapping[str, Any]) -> list[dict[str, str]]:
    """Flag undecided rules that look like ordinary task failure conditions."""

    findings: list[dict[str, str]] = []
    native = checklist.get("native") if isinstance(checklist, Mapping) else None
    undecided = native.get("undecided_if") if isinstance(native, Mapping) else None
    if not isinstance(undecided, list):
        return findings
    for index, item in enumerate(undecided):
        if not isinstance(item, Mapping):
            continue
        combined = " ".join(str(item.get(key) or "") for key in ("text", "rationale"))
        location = f"$.native.undecided_if[{index}]"
        evidence_like = EVIDENCE_INSUFFICIENCY_RE.search(combined) is not None or (
            EVIDENCE_OBJECT_RE.search(combined) is not None
            and EVIDENCE_GAP_RE.search(combined) is not None
        )
        if not evidence_like:
            findings.append(
                {
                    "code": "undecided_not_evidence_insufficiency",
                    "location": location,
                    "message": "Undecided rule does not clearly describe retained-evidence insufficiency/integrity",
                    "excerpt": combined[:500],
                }
            )
        # A well-formed evidence-gap rule often states the contrasting native
        # failure boundary (for example, "score below 1 is failure, not
        # undecided").  Once the rule independently establishes a retention,
        # attribution, integrity, or conflict gap, that contrast is not an
        # ordinary failure misclassified as U.
        if ORDINARY_FAILURE_RE.search(combined) and not evidence_like:
            findings.append(
                {
                    "code": "ordinary_failure_misclassified_as_undecided",
                    "location": location,
                    "message": "Undecided rule contains a normal benchmark failure condition",
                    "excerpt": combined[:500],
                }
            )
    return findings


def _native_text(checklist: Mapping[str, Any], field: str | None = None) -> str:
    native = checklist.get("native") if isinstance(checklist, Mapping) else {}
    value: Any = native.get(field) if isinstance(native, Mapping) and field else native
    return " ".join(text for _, text in _iter_text(value)).lower().replace("`", "")


def _semantic_finding(code: str, message: str, location: str = "$.native") -> dict[str, str]:
    return {"code": code, "message": message, "location": location}


def _field_support_pointers(checklist: Mapping[str, Any], field: str) -> tuple[str, ...]:
    native = checklist.get("native") if isinstance(checklist, Mapping) else None
    value = native.get(field) if isinstance(native, Mapping) else None
    return tuple(_iter_support_pointers(value))


def _field_support_paths(checklist: Mapping[str, Any], field: str) -> set[str]:
    """Return source paths cited by one native field, without selectors."""

    return {
        pointer.split("::", 1)[0]
        for pointer in _field_support_pointers(checklist, field)
        if "::" in pointer
    }


def _has_terminal_bench_test_support(pointers: Iterable[str]) -> bool:
    return any(
        pointer.split("::", 1)[0]
        in {"official/tests/test.sh", "official/tests/test_outputs.py"}
        for pointer in pointers
        if "::" in pointer
    )


def _terminal_bench_test_composition_findings(
    checklist: Mapping[str, Any], packet_path: Path | None
) -> list[dict[str, str]]:
    """Check that benchmark_success cites every released pytest test.

    Terminal-Bench's wrapper is a conjunction over the released pytest
    composition.  Individual success/failure rules may reconstruct that
    decision from final workspace artifacts, so requiring every rule to repeat
    ``reward.txt`` is overly strict.  Coverage of the actual test composition,
    however, is independently checkable from the packet and should remain a
    hard semantic review signal.
    """

    if packet_path is None:
        return []
    source_path = packet_path.parent / "raw_case" / "official" / "tests" / "test_outputs.py"
    if not source_path.is_file():
        return []
    try:
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeError):
        return []
    tests = sorted(
        (node.name, node.lineno)
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )
    if not tests:
        return []

    pointers = _field_support_pointers(checklist, "benchmark_success")

    def covers(pointer: str, test_name: str, line_number: int) -> bool:
        if "::" not in pointer:
            return False
        path, selector = pointer.split("::", 1)
        if path != "official/tests/test_outputs.py":
            return False
        selector = selector.strip()
        if selector == test_name or selector.endswith(f".{test_name}"):
            return True
        line_match = re.fullmatch(
            r"(?:lines?\s*)?(\d+)(?:\s*-\s*(\d+))?", selector, flags=re.IGNORECASE
        )
        if not line_match:
            return False
        first = int(line_match.group(1))
        last = int(line_match.group(2) or line_match.group(1))
        return first <= line_number <= last

    omitted = [
        test_name
        for test_name, line_number in tests
        if not any(covers(pointer, test_name, line_number) for pointer in pointers)
    ]
    if not omitted:
        return []
    return [
        _semantic_finding(
            "terminal_bench_test_composition_incomplete",
            "benchmark_success does not cite every released pytest test: "
            + ", ".join(omitted),
            "$.native.benchmark_success.support",
        )
    ]


def domain_semantic_findings(
    benchmark: str,
    checklist: Mapping[str, Any],
    packet_path: Path | None = None,
) -> list[dict[str, str]]:
    """Conservative benchmark-level checks; findings are never auto-repairs."""

    findings: list[dict[str, str]] = []
    all_text = _native_text(checklist)
    success = _native_text(checklist, "success_if")
    fail = _native_text(checklist, "fail_if")
    artifacts = _native_text(checklist, "decisive_artifacts")
    if benchmark == "osworld_verified":
        if "evaluator" not in all_text or not re.search(r"\b1(?:\.0)?\b", all_text):
            findings.append(
                _semantic_finding(
                    "osworld_verified_native_rule_unclear",
                    "Native claim should make official evaluator score 1.0 the success boundary",
                )
            )
        if not re.search(
            r"(?:official\s+)?(?:evaluator\s+)?"
            r"(?:score|result|outcome|evaluation).{0,100}"
            r"(?:exactly\s+|equals?\s+|returns?\s+|records?\s+|is\s+)?1(?:\.0)?|"
            r"evaluator.{0,100}(?:returns?|equals?|reports?|records?).{0,30}1(?:\.0)?|"
            r"(?:desktopenv\.)?evaluate.{0,100}"
            r"(?:returns?|returned|equals?|reports?|records?).{0,30}1(?:\.0)?|"
            r"(?:all|every).{0,50}(?:pass|satisf)",
            success,
        ):
            findings.append(
                _semantic_finding(
                    "osworld_verified_success_rule_unclear",
                    "Success rules do not clearly require the full official evaluator decision",
                    "$.native.success_if",
                )
            )
        if not re.search(r"(?:below|less|not|non[- ]?1|fail|zero|0(?:\.0)?)", fail):
            findings.append(
                _semantic_finding(
                    "osworld_verified_failure_rule_unclear",
                    "Failure rules do not clearly cover a non-full official evaluator result",
                    "$.native.fail_if",
                )
            )
        if "result" not in artifacts and "evaluator" not in artifacts:
            findings.append(
                _semantic_finding(
                    "osworld_verified_decisive_result_missing",
                    "Decisive artifacts do not name retained evaluator/result evidence",
                    "$.native.decisive_artifacts",
                )
            )

    elif benchmark == "osworld_2_0":
        # OSWorld 2.0 private packets expose two different source roles to the
        # drafter: the agent-visible task representation and the authorized
        # official task/evaluator source.  The checklist should ground the goal
        # in either equivalent task representation, while every decisive native
        # evaluator field remains grounded in the authorized implementation.
        # The controller pointer is packet-level provenance, not evidence that
        # every claim has to cite redundantly.
        goal_paths = _field_support_paths(checklist, "user_goal")
        goal_sources = {
            "derived/agent_visible_task.json",
            "authorized/official_task.py",
        }
        if not goal_paths.intersection(goal_sources):
            findings.append(
                _semantic_finding(
                    "osworld_2_user_goal_source_role_missing",
                    "User goal is not grounded in the visible-task representation or authorized official instruction",
                    "$.native.user_goal.support",
                )
            )

        decisive_fields = (
            "benchmark_success",
            "checked_by",
            "decisive_artifacts",
            "success_if",
            "fail_if",
        )
        missing_authorized_support = [
            field
            for field in decisive_fields
            if "authorized/official_task.py" not in _field_support_paths(checklist, field)
        ]
        if missing_authorized_support:
            findings.append(
                _semantic_finding(
                    "osworld_2_required_source_roles_missing",
                    "Decisive native evaluator fields lack authorized official-task support: "
                    + ", ".join(missing_authorized_support),
                    "$.native",
                )
            )

        packet_sources: set[str] = set()
        if packet_path is not None and packet_path.is_file():
            try:
                packet_sources = case_packet_support_paths(
                    packet_path.read_text(encoding="utf-8")
                )
            except (OSError, UnicodeError, ChecklistGuardrailError):
                packet_sources = set()
        packet_boundary_sources = {
            "controller/gated_source_pointer.json",
            "authorized/official_task.py",
        }
        missing_packet_boundary = sorted(packet_boundary_sources - packet_sources)
        if missing_packet_boundary:
            findings.append(
                _semantic_finding(
                    "osworld_2_gated_evaluator_boundary_missing",
                    "Packet provenance does not expose the complete gated authorized-evaluator boundary; missing "
                    + ", ".join(missing_packet_boundary),
                    "case_packet.md",
                )
            )
        if not re.search(r"result\.json|result\.txt|evaluator\s+(?:result|output)|score\s+(?:record|artifact)", artifacts):
            findings.append(
                _semantic_finding(
                    "osworld_2_decisive_result_missing",
                    "Decisive artifacts do not identify retained authorized evaluator output",
                    "$.native.decisive_artifacts",
                )
            )
        if re.search(r"(?ix)exact\s+(?:hidden|gated)\s+evaluator\s+(?:requires|checks|expects)", all_text):
            findings.append(
                _semantic_finding(
                    "osworld_2_hidden_evaluator_semantics_invented",
                    "Draft appears to state exact hidden/gated evaluator semantics not embedded in the packet",
                )
            )

    elif benchmark == "terminal_bench_2_1":
        benchmark_success = _native_text(checklist, "benchmark_success")
        checked_by = _native_text(checklist, "checked_by")
        wrapper_boundary = f"{benchmark_success} {checked_by}"
        if not re.search(r"pytest|verifier|test", wrapper_boundary):
            findings.append(
                _semantic_finding(
                    "terminal_bench_verifier_missing",
                    "Native claim does not identify the official verifier/test decision",
                )
            )
        if "reward" not in wrapper_boundary or not re.search(r"\b1\b", wrapper_boundary):
            findings.append(
                _semantic_finding(
                    "terminal_bench_native_success_boundary_missing",
                    "benchmark_success/checked_by should preserve the official passing-test to reward-1 wrapper boundary",
                    "$.native.benchmark_success",
                )
            )
        if not _has_terminal_bench_test_support(
            _field_support_pointers(checklist, "benchmark_success")
            + _field_support_pointers(checklist, "checked_by")
        ):
            findings.append(
                _semantic_finding(
                    "terminal_bench_native_wrapper_support_missing",
                    "benchmark_success/checked_by should be grounded in the released test wrapper or test suite",
                    "$.native.benchmark_success.support",
                )
            )
        if not _has_terminal_bench_test_support(_field_support_pointers(checklist, "success_if")):
            findings.append(
                _semantic_finding(
                    "terminal_bench_success_basis_missing",
                    "Success rules should be grounded in the released wrapper/tests, whether through native logs or deterministic final-artifact reconstruction",
                    "$.native.success_if.support",
                )
            )
        if not _has_terminal_bench_test_support(_field_support_pointers(checklist, "fail_if")):
            findings.append(
                _semantic_finding(
                    "terminal_bench_failure_basis_missing",
                    "Failure rules should be grounded in the released wrapper/tests",
                    "$.native.fail_if.support",
                )
            )
        if not artifacts.strip() or not _has_terminal_bench_test_support(
            _field_support_pointers(checklist, "decisive_artifacts")
        ):
            findings.append(
                _semantic_finding(
                    "terminal_bench_decisive_basis_missing",
                    "Decisive evidence should be grounded in released tests; reward/CTRF logs or sufficient deterministic final workspace artifacts are both valid",
                    "$.native.decisive_artifacts",
                )
            )
        findings.extend(_terminal_bench_test_composition_findings(checklist, packet_path))

    elif benchmark == "swe_bench_pro":
        normalized = all_text.replace("-", "_").replace(" ", "_")
        success_normalized = success.replace("-", "_").replace(" ", "_")
        for group in ("fail_to_pass", "pass_to_pass"):
            if group not in normalized:
                findings.append(
                    _semantic_finding(
                        "swe_bench_pro_test_group_missing",
                        f"Native claim omits the named {group.upper()} group",
                    )
                )
        success_composition = all(
            group in success_normalized for group in ("fail_to_pass", "pass_to_pass")
        ) or re.search(
            r"passed_test_names|"
            r"(?:all|every|both|each|complete).{0,80}"
            r"(?:required|named|exact|official|listed|contracted|test)|"
            r"(?:required|named|exact|official|listed|contracted).{0,80}"
            r"(?:test|name|list|set).{0,100}(?:pass|passed)|"
            r"(?:union|subset|set\s*\()|"
            r"(?:include|contain|record|list|place)s?.{0,180}"
            r"\btest[a-z0-9_./:\[\]-]*\b.{0,120}\bpassed\b|"
            r"\bpassed\b.{0,80}(?:entries|results?|names?).{0,160}"
            r"\btest[a-z0-9_./:\[\]-]*\b",
            success,
        )
        if not success_composition or not re.search(r"pass|passed", success):
            findings.append(
                _semantic_finding(
                    "swe_bench_pro_success_rule_incomplete",
                    "Success rules should require every named FAIL_TO_PASS and PASS_TO_PASS test to pass",
                    "$.native.success_if",
                )
            )
        if not re.search(
            r"\b(?:fails?|failed|missing|absent|unparsed|omit(?:s|ted)?|lacks?)\b|"
            r"\bnon[- ]?passed\b|\bstatus\s+other\s+than\s+passed\b|"
            r"\bnot\s+(?:appear|present|included|listed|reported|recorded|marked)"
            r"(?:.{0,40})\bpassed\b|"
            r"\bdoes\s+not\s+(?:appear|include|contain|list|record|report|mark|place)\b|"
            r"\boutside\b.{0,60}\bpassed|\bnot\s+in\s+passed|"
            r"\bno\s+passed\s+(?:entry|record|result)",
            fail,
        ):
            findings.append(
                _semantic_finding(
                    "swe_bench_pro_failure_rule_incomplete",
                    "Failure rules should cover any named test not appearing as PASSED",
                    "$.native.fail_if",
                )
            )
        if "evaluator" not in artifacts or "test" not in artifacts:
            findings.append(
                _semantic_finding(
                    "swe_bench_pro_decisive_artifacts_incomplete",
                    "Decisive artifacts should identify parsed official evaluator/test output",
                    "$.native.decisive_artifacts",
                )
            )
        benchmark_success = _native_text(checklist, "benchmark_success")
        solution_patch_is_excluded = re.search(
            r"not\s+(?:part|used)|irrelevant|"
            r"not\s+(?:compared|checked|evaluated)\s+(?:against|with)|"
            r"does\s+not\s+(?:compare|check|evaluate)",
            benchmark_success,
        )
        if "solution patch" in benchmark_success and not solution_patch_is_excluded:
            findings.append(
                _semantic_finding(
                    "swe_bench_pro_solution_patch_used_as_native_decider",
                    "Official solution patch must not be a native success condition",
                    "$.native.benchmark_success",
                )
            )
    return findings


def _runtime_workspace_files(
    runtime_root: Path, packet: PacketInfo, prompt_supplement: Path | None
) -> dict[str, str]:
    prompt_path = runtime_root / "prompts/draft_case_checklist.prompt.md"
    template_path = runtime_root / "templates/case_checklist.template.yaml"
    schema_path = runtime_root / "schemas/case_checklist.schema.json"
    for path in (prompt_path, template_path, schema_path):
        if not _is_safe_regular(path):
            raise ValueError(f"missing or unsafe runtime file: {path}")
    supplement_text: str | None = None
    if prompt_supplement is not None:
        if not _is_safe_regular(prompt_supplement):
            raise ValueError(f"missing or unsafe prompt supplement: {prompt_supplement}")
        supplement_text = prompt_supplement.read_text(encoding="utf-8")
    schema = _load_json(schema_path)
    if not isinstance(schema, dict):
        raise ValueError("checklist schema is not an object")
    return drafter.build_codex_workspace_files(
        instructions=drafter.compose_prompt(
            prompt_path.read_text(encoding="utf-8"), supplement_text
        ),
        template_text=template_path.read_text(encoding="utf-8"),
        case_packet_text=packet.text,
        model_output_schema=drafter.build_model_output_schema(schema),
    )


def _audit_validator(
    audit: CaseAudit,
    checklist: dict[str, Any],
    packet: PacketInfo,
    runtime_root: Path,
) -> None:
    try:
        schema = _load_json(runtime_root / "schemas/case_checklist.schema.json")
        errors = sorted(
            Draft202012Validator(schema).iter_errors(checklist),
            key=lambda item: list(item.absolute_path),
        )
        if errors:
            rendered = "; ".join(
                f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
                for error in errors[:20]
            )
            audit.failed("checklist_schema", "checklist_schema_invalid", rendered)
        else:
            audit.passed("checklist_schema")
    except Exception as exc:
        audit.failed(
            "checklist_schema",
            "checklist_schema_audit_error",
            f"{type(exc).__name__}: {exc}",
        )

    try:
        allowed = case_packet_support_paths(packet.text)
        validate_checklist_guardrails(checklist, allowed_source_paths=allowed)
    except (ChecklistGuardrailError, Exception) as exc:
        audit.failed(
            "checklist_guardrails",
            "checklist_guardrail_failure",
            f"{type(exc).__name__}: {exc}",
        )
    else:
        audit.passed("checklist_guardrails")

    try:
        checklist_validator.validate_support_pointers(checklist, packet.path)
    except Exception as exc:
        audit.failed(
            "support_pointer_resolution",
            "support_pointer_unresolvable",
            f"{type(exc).__name__}: {exc}",
        )
    else:
        audit.passed(
            "support_pointer_resolution",
            pointer_count=len(list(_iter_support_pointers(checklist))),
        )


def _audit_attempt_promotion(audit: CaseAudit, case_dir: Path) -> int | None:
    canonical = case_dir / "checklist.yaml"
    if not _is_safe_regular(canonical):
        return None
    matching: list[int] = []
    for attempt_path in sorted(case_dir.glob("attempt_*.checklist.yaml")):
        match = re.fullmatch(r"attempt_([0-9]+)\.checklist\.yaml", attempt_path.name)
        if match and _is_safe_regular(attempt_path) and attempt_path.read_bytes() == canonical.read_bytes():
            matching.append(int(match.group(1)))
    if not matching:
        audit.failed(
            "attempt_promotion_bytes",
            "canonical_checklist_has_no_source_attempt",
            "Canonical checklist.yaml is not byte-identical to any attempt_N.checklist.yaml",
        )
        return None
    index = matching[0]
    prefix = f"attempt_{index:02d}"
    mismatches: list[str] = []
    for suffix in CANONICAL_SUFFIXES:
        canonical_path = case_dir / suffix
        attempt_path = case_dir / f"{prefix}.{suffix}"
        if not _is_safe_regular(attempt_path):
            mismatches.append(f"missing {attempt_path.name}")
        elif canonical_path.read_bytes() != attempt_path.read_bytes():
            mismatches.append(f"byte mismatch for {suffix}")
    if mismatches:
        audit.failed(
            "attempt_promotion_bytes",
            "canonical_attempt_sidecar_mismatch",
            "; ".join(mismatches),
            attempt_index=index,
        )
        return index
    audit.passed("attempt_promotion_bytes", attempt_index=index)
    return index


def _audit_batch_row(
    audit: CaseAudit,
    case_dir: Path,
    batch_rows: Mapping[str, Mapping[str, Any]],
    attempt_index: int | None,
) -> None:
    row = batch_rows.get(case_dir.name)
    if row is None:
        audit.failed(
            "batch_result_row",
            "batch_result_row_missing",
            f"No _batch_results.jsonl row for output directory {case_dir.name!r}",
        )
        return
    status = row.get("status")
    if status not in {"success", "skipped_existing"}:
        audit.failed(
            "batch_result_row",
            "batch_result_not_successful",
            f"Batch row status is {status!r}",
        )
        return
    if attempt_index is not None and status == "success":
        indices = {
            item.get("attempt_index")
            for item in row.get("attempts", [])
            if isinstance(item, Mapping) and item.get("returncode") == 0
        }
        if attempt_index not in indices:
            audit.failed(
                "batch_result_row",
                "promoted_attempt_not_successful_in_batch_row",
                f"Promoted attempt {attempt_index} is not a successful batch attempt: {sorted(indices)}",
            )
            return
    audit.passed("batch_result_row", status=status)


def _audit_codex_command(
    audit: CaseAudit,
    codex: Mapping[str, Any],
    expected_model: str,
    expected_reasoning: str,
) -> None:
    command = codex.get("command")
    errors: list[str] = []
    if not isinstance(command, list) or not all(isinstance(value, str) for value in command):
        errors.append("command is not a string argv list")
    else:
        def has_pair(left: str, right: str) -> bool:
            return any(command[index : index + 2] == [left, right] for index in range(len(command) - 1))

        if not has_pair("--disable", "shell_tool"):
            errors.append("shell_tool is not disabled")
        if not has_pair("--disable", "unified_exec"):
            errors.append("unified_exec is not disabled")
        if not has_pair("--sandbox", "read-only"):
            errors.append("sandbox argv is not read-only")
        if not has_pair("--model", expected_model):
            errors.append(f"model argv is not {expected_model}")
        if f'model_reasoning_effort="{expected_reasoning}"' not in command:
            errors.append(f"reasoning effort argv is not {expected_reasoning}")
        if not command or command[-1] != "-":
            errors.append("Codex input is not direct stdin ('-')")
    if codex.get("sandbox") != "read-only":
        errors.append("recorded sandbox is not read-only")
    if errors:
        audit.failed("codex_tool_policy", "codex_tool_policy_violation", "; ".join(errors))
    else:
        audit.passed("codex_tool_policy")


def _is_transport_error(message: Any) -> bool:
    if not isinstance(message, str):
        return False
    lowered = message.lower()
    return any(term in lowered for term in TRANSPORT_ERROR_TERMS)


def _audit_events(
    audit: CaseAudit,
    api_response: Mapping[str, Any],
    codex: Mapping[str, Any],
    checklist: Mapping[str, Any],
    reasoning_summary: str,
) -> None:
    errors: list[str] = []
    if codex.get("malformed_event_lines") != []:
        errors.append("malformed_event_lines is nonempty")
    events = codex.get("events")
    messages: list[str] = []
    item_types: Counter[str] = Counter()
    if not isinstance(events, list) or not events or not all(isinstance(item, Mapping) for item in events):
        errors.append("events is empty or not an object list")
        events = []
    for index, event in enumerate(events):
        event_type = str(event.get("type") or "")
        if event_type == "error":
            if not _is_transport_error(event.get("message")):
                errors.append(f"event[{index}] contains a non-transport error")
            continue
        item = event.get("item")
        if not isinstance(item, Mapping):
            continue
        item_type = str(item.get("type") or "").lower()
        item_types[item_type] += 1
        if item_type in FORBIDDEN_ITEM_TYPES or item_type not in {"reasoning", "agent_message", "error"}:
            errors.append(f"event[{index}] contains forbidden item type {item_type!r}")
            continue
        if item_type == "error":
            if not _is_transport_error(item.get("message")):
                errors.append(f"event[{index}] contains a non-transport error item")
        elif item_type == "agent_message":
            text = item.get("text")
            if isinstance(text, str):
                messages.append(text)
            else:
                errors.append(f"event[{index}] agent_message has no text")
    if len(messages) != 1:
        errors.append(f"expected exactly one agent_message, found {len(messages)}")
    expected_body = drafter.strip_null_fields(
        {
            key: value
            for key, value in checklist.items()
            if key not in {"schema_version", "case_unit_id", "domain", "task_id"}
        }
    )
    message_body: Any | None = None
    if len(messages) == 1:
        try:
            message_body = drafter.strip_null_fields(json.loads(messages[0]))
        except json.JSONDecodeError as exc:
            errors.append(f"agent_message is malformed JSON: {exc}")
        else:
            if message_body != expected_body:
                errors.append("agent_message body differs from canonical checklist")
    output_text = api_response.get("output_text")
    output_body: Any | None = None
    if not isinstance(output_text, str):
        errors.append("api_response.output_text is not text")
    else:
        try:
            output_body = drafter.strip_null_fields(json.loads(output_text))
        except json.JSONDecodeError as exc:
            errors.append(f"output_text is malformed JSON: {exc}")
        else:
            if output_body != expected_body:
                errors.append("output_text body differs from canonical checklist")
    if message_body is not None and output_body is not None and message_body != output_body:
        errors.append("agent_message and api_response.output_text differ semantically")
    expected_reasoning = drafter.extract_reasoning_summary_text(dict(api_response))
    expected_reasoning += "\n" if expected_reasoning else ""
    if reasoning_summary != expected_reasoning:
        errors.append("reasoning_summary.txt differs from API reasoning projection")
    if errors:
        audit.failed(
            "codex_event_stream",
            "codex_event_stream_invalid",
            "; ".join(errors[:30]),
            item_types=dict(item_types),
        )
    else:
        audit.passed(
            "codex_event_stream",
            event_count=len(events),
            item_types=dict(item_types),
            forbidden_tool_item_count=0,
        )


def _audit_provenance(
    audit: CaseAudit,
    packet: PacketInfo,
    checklist: Mapping[str, Any],
    llm_call: Mapping[str, Any],
    api_response: Mapping[str, Any],
    reasoning_summary: str,
    runtime_root: Path,
    prompt_supplement: Path | None,
    expected_provider: str,
    expected_model: str,
    expected_reasoning: str,
) -> None:
    identity_errors: list[str] = []
    if set(llm_call) != EXPECTED_LLM_FIELDS:
        identity_errors.append(
            f"llm_call field set drift: missing={sorted(EXPECTED_LLM_FIELDS - set(llm_call))}, "
            f"extra={sorted(set(llm_call) - EXPECTED_LLM_FIELDS)}"
        )
    expected_identity = {
        "schema_version": "llm_call/v1",
        "provider": expected_provider,
        "model": expected_model,
        "model_version": expected_model,
        "api_key_env": "CODEX_HOME",
        "domain": packet.domain,
        "case_unit_id": packet.case_unit_id,
        "task_id": packet.task_id,
        "phase": "draft",
        "experiment_type": "minimal_package",
        "agent_id_or_role": "case_checklist_drafter",
        "retry_index": 0,
    }
    for key, expected in expected_identity.items():
        if llm_call.get(key) != expected:
            identity_errors.append(f"llm_call.{key}={llm_call.get(key)!r}, expected {expected!r}")
    metadata = llm_call.get("response_metadata")
    if not isinstance(metadata, Mapping):
        identity_errors.append("llm_call.response_metadata is not an object")
        metadata = {}
    else:
        expected_metadata = {
            "reasoning_effort": expected_reasoning,
            "model_verbosity": drafter.DEFAULT_DRAFT_VERBOSITY,
            "auth_mode": "codex_login",
            "max_output_tokens_enforced": False,
            "response_status": "completed",
            "provider_model": expected_model,
        }
        for key, expected in expected_metadata.items():
            if metadata.get(key) != expected:
                identity_errors.append(
                    f"response_metadata.{key}={metadata.get(key)!r}, expected {expected!r}"
                )
    if set(api_response) != EXPECTED_API_FIELDS:
        identity_errors.append("api_response field set drift")
    for key, expected in {
        "status": "completed",
        "model": expected_model,
        "provider": expected_provider,
    }.items():
        if api_response.get(key) != expected:
            identity_errors.append(f"api_response.{key}={api_response.get(key)!r}, expected {expected!r}")
    codex = api_response.get("codex_cli")
    if not isinstance(codex, Mapping):
        identity_errors.append("api_response.codex_cli is not an object")
        codex = {}
    else:
        if set(codex) != EXPECTED_CODEX_FIELDS:
            identity_errors.append("codex_cli field set drift")
        if codex.get("auth_mode") != "codex_login" or codex.get("returncode") != 0:
            identity_errors.append("Codex auth_mode/returncode mismatch")
    if identity_errors:
        audit.failed(
            "llm_provenance",
            "llm_provenance_mismatch",
            "; ".join(identity_errors[:30]),
        )
    else:
        audit.passed(
            "llm_provenance",
            provider=expected_provider,
            model=expected_model,
            reasoning_effort=expected_reasoning,
        )

    if codex:
        _audit_codex_command(audit, codex, expected_model, expected_reasoning)
        bundle_errors: list[str] = []
        try:
            workspace_files = _runtime_workspace_files(runtime_root, packet, prompt_supplement)
            _, expected_manifest = drafter.build_codex_stdin_bundle(workspace_files)
            actual_manifest = codex.get("stdin_bundle")
            if actual_manifest != expected_manifest:
                bundle_errors.append("stored stdin manifest differs from exact local reconstruction")
            if not isinstance(actual_manifest, Mapping):
                bundle_errors.append("stdin_bundle is not an object")
            else:
                components = actual_manifest.get("components")
                if not isinstance(components, list):
                    bundle_errors.append("stdin_bundle.components is not a list")
                else:
                    names = tuple(
                        str(item.get("name")) if isinstance(item, Mapping) else ""
                        for item in components
                    )
                    if names != EXPECTED_STDIN_COMPONENTS:
                        bundle_errors.append(f"stdin component inventory/order drift: {names}")
                    packet_components = [
                        item
                        for item in components
                        if isinstance(item, Mapping) and item.get("name") == "case_packet.md"
                    ]
                    if len(packet_components) != 1:
                        bundle_errors.append("stdin has no unique case_packet.md component")
                    elif packet_components[0].get("sha256") != packet.sha256:
                        bundle_errors.append(
                            f"stdin case_packet hash {packet_components[0].get('sha256')} != local {packet.sha256}"
                        )
        except Exception as exc:
            bundle_errors.append(f"could not reconstruct sealed stdin: {type(exc).__name__}: {exc}")
        if bundle_errors:
            audit.failed(
                "sealed_stdin_bundle",
                "sealed_stdin_bundle_mismatch",
                "; ".join(bundle_errors),
            )
        else:
            audit.passed(
                "sealed_stdin_bundle",
                policy="direct_stdin_sealed_bundle_v1",
                case_packet_sha256=packet.sha256,
                component_count=4,
            )
        _audit_events(audit, api_response, codex, checklist, reasoning_summary)


def _audit_case(
    *,
    target: TargetSpec,
    packet: PacketInfo,
    case_dir: Path | None,
    batch_rows: Mapping[str, Mapping[str, Any]],
    runtime_root: Path,
    prompt_supplement: Path | None,
    expected_provider: str,
    expected_model: str,
    expected_reasoning: str,
) -> dict[str, Any]:
    audit = CaseAudit(target.benchmark, packet, case_dir)
    if case_dir is None:
        audit.failed(
            "case_coverage",
            "draft_case_missing",
            "No matching exact or benchmark-namespaced draft directory",
        )
        return audit.finish()
    audit.passed("case_coverage", output_directory_name=case_dir.name)

    missing_sidecars = [
        suffix for suffix in CANONICAL_SUFFIXES if not _is_safe_regular(case_dir / suffix)
    ]
    if missing_sidecars:
        audit.failed(
            "canonical_sidecars",
            "canonical_sidecars_missing_or_unsafe",
            f"Missing/unsafe canonical sidecars: {missing_sidecars}",
        )
    else:
        audit.passed(
            "canonical_sidecars",
            files={suffix: _sha256_file(case_dir / suffix) for suffix in CANONICAL_SUFFIXES},
        )

    checklist: dict[str, Any] | None = None
    checklist_json: Any = None
    try:
        checklist = _load_yaml_mapping(case_dir / "checklist.yaml")
        checklist_json = _load_json(case_dir / "checklist.json")
        if checklist_json != checklist:
            raise ValueError("checklist.json differs semantically from checklist.yaml")
    except Exception as exc:
        audit.failed(
            "checklist_yaml_json",
            "checklist_yaml_json_mismatch",
            f"{type(exc).__name__}: {exc}",
        )
    else:
        audit.passed("checklist_yaml_json")
        expected_identity = {
            "schema_version": "case_checklist_v1",
            "case_unit_id": packet.case_unit_id,
            "domain": packet.domain,
            "task_id": packet.task_id,
        }
        mismatches = {
            key: {"actual": checklist.get(key), "expected": expected}
            for key, expected in expected_identity.items()
            if checklist.get(key) != expected
        }
        if mismatches:
            audit.failed(
                "checklist_identity",
                "checklist_identity_mismatch",
                f"Checklist identity mismatch: {mismatches}",
            )
        else:
            audit.passed("checklist_identity")
        _audit_validator(audit, checklist, packet, runtime_root)

    attempt_index = _audit_attempt_promotion(audit, case_dir)
    _audit_batch_row(audit, case_dir, batch_rows, attempt_index)

    if checklist is not None and not missing_sidecars:
        try:
            llm_call = _load_json(case_dir / "llm_call.json")
            api_response = _load_json(case_dir / "api_response.json")
            reasoning_summary = (case_dir / "reasoning_summary.txt").read_text(encoding="utf-8")
            if not isinstance(llm_call, Mapping) or not isinstance(api_response, Mapping):
                raise ValueError("llm_call/api_response must both be objects")
        except Exception as exc:
            audit.failed(
                "llm_sidecar_parse",
                "llm_sidecar_parse_failure",
                f"{type(exc).__name__}: {exc}",
            )
        else:
            audit.passed("llm_sidecar_parse")
            _audit_provenance(
                audit,
                packet,
                checklist,
                llm_call,
                api_response,
                reasoning_summary,
                runtime_root,
                prompt_supplement,
                expected_provider,
                expected_model,
                expected_reasoning,
            )
            for finding in prior_run_findings(checklist, reasoning_summary):
                audit.finding(
                    finding["code"],
                    finding["message"],
                    severity="high",
                    location=finding.get("location"),
                    excerpt=finding.get("excerpt"),
                )

    if checklist is not None:
        for finding in undecided_findings(checklist):
            audit.finding(
                finding["code"],
                finding["message"],
                severity="high",
                location=finding.get("location"),
                excerpt=finding.get("excerpt"),
            )
        for finding in domain_semantic_findings(
            target.benchmark, checklist, packet.path
        ):
            audit.finding(
                finding["code"],
                finding["message"],
                severity="medium",
                location=finding.get("location"),
                excerpt=finding.get("excerpt"),
            )
    return audit.finish()


def _audit_target(
    target: TargetSpec,
    *,
    runtime_root: Path,
    prompt_supplement: Path | None,
    expected_provider: str,
    expected_model: str,
    expected_reasoning: str,
    batch_cache: dict[Path, tuple[dict[str, Any] | None, dict[str, dict[str, Any]], list[dict[str, Any]]]],
    case_prompt_supplements: Mapping[tuple[str, str], Path] | None = None,
) -> dict[str, Any]:
    packets, packet_errors = _read_packets(target)
    draft_dirs, coverage_errors = _discover_draft_dirs(target, packets)
    per_case_supplements = case_prompt_supplements or {}
    supplement_errors = [
        {
            "code": "case_prompt_supplement_case_missing",
            "message": (
                f"Case-specific prompt supplement names no packet in target: "
                f"{target.benchmark}/{case_id}"
            ),
        }
        for benchmark, case_id in sorted(per_case_supplements)
        if benchmark == target.benchmark and case_id not in packets
    ]
    if target.draft_root not in batch_cache:
        batch_cache[target.draft_root] = _load_batch_metadata(target.draft_root)
    batch_summary, batch_rows, batch_errors = batch_cache[target.draft_root]
    cases = [
        _audit_case(
            target=target,
            packet=packets[case_id],
            case_dir=draft_dirs.get(case_id),
            batch_rows=batch_rows,
            runtime_root=runtime_root,
            prompt_supplement=per_case_supplements.get(
                (target.benchmark, case_id), prompt_supplement
            ),
            expected_provider=expected_provider,
            expected_model=expected_model,
            expected_reasoning=expected_reasoning,
        )
        for case_id in sorted(packets)
    ]
    status_counts = Counter(case["status"] for case in cases)
    finding_counts = Counter(
        finding["code"] for case in cases for finding in case.get("findings", [])
    )
    error_counts = Counter(error["code"] for case in cases for error in case.get("errors", []))
    global_errors = [
        *packet_errors,
        *coverage_errors,
        *batch_errors,
        *supplement_errors,
    ]
    if global_errors or status_counts.get("failed", 0):
        status = "failed"
    elif status_counts.get("passed_with_findings", 0):
        status = "passed_with_findings"
    else:
        status = "passed"
    return {
        "benchmark": target.benchmark,
        "packet_root": str(target.packet_root),
        "draft_root": str(target.draft_root),
        "status": status,
        "expected_case_count": len(packets),
        "mapped_draft_case_count": len(draft_dirs),
        "case_status_counts": dict(sorted(status_counts.items())),
        "error_code_counts": dict(sorted(error_counts.items())),
        "finding_code_counts": dict(sorted(finding_counts.items())),
        "global_errors": global_errors,
        "batch_summary": batch_summary,
        "cases": cases,
    }


def _markdown_report(report: Mapping[str, Any]) -> str:
    lines = [
        "# Four-benchmark draft audit",
        "",
        f"- verdict: **{report['verdict']}**",
        f"- generated: `{report['generated_at']}`",
        f"- cases audited: `{report['summary']['case_count']}`",
        f"- deterministic failures: `{report['summary']['failed_case_count']}` cases, "
        f"`{report['summary']['global_error_count']}` target/root errors",
        f"- semantic findings: `{report['summary']['finding_count']}` across "
        f"`{report['summary']['finding_case_count']}` cases",
        "",
        "Deterministic failures reject an output. Semantic findings are conservative review flags; "
        "they do not mutate a checklist and do not by themselves prove it is wrong.",
        "",
        "## Benchmark summary",
        "",
        "| Benchmark | Expected | Mapped | Passed | With findings | Failed | Target status |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for target in report["targets"]:
        counts = target["case_status_counts"]
        lines.append(
            f"| `{target['benchmark']}` | {target['expected_case_count']} | "
            f"{target['mapped_draft_case_count']} | {counts.get('passed', 0)} | "
            f"{counts.get('passed_with_findings', 0)} | {counts.get('failed', 0)} | "
            f"**{target['status']}** |"
        )

    global_errors = [
        (target["benchmark"], error)
        for target in report["targets"]
        for error in target.get("global_errors", [])
    ]
    lines.extend(["", "## Coverage and batch-root errors", ""])
    if not global_errors:
        lines.append("None.")
    else:
        lines.extend(["| Benchmark | Code | Message |", "|---|---|---|"])
        for benchmark, error in global_errors:
            message = str(error.get("message", "")).replace("|", "\\|").replace("\n", " ")
            lines.append(f"| `{benchmark}` | `{error.get('code')}` | {message} |")

    failed_cases = [
        case
        for target in report["targets"]
        for case in target["cases"]
        if case["status"] == "failed"
    ]
    lines.extend(["", "## Deterministic case failures", ""])
    if not failed_cases:
        lines.append("None.")
    else:
        lines.extend(["| Benchmark | Case | Codes |", "|---|---|---|"])
        for case in failed_cases[:500]:
            codes = ", ".join(sorted({error["code"] for error in case["errors"]}))
            lines.append(f"| `{case['benchmark']}` | `{case['case_unit_id']}` | `{codes}` |")
        if len(failed_cases) > 500:
            lines.append(f"\nOnly the first 500 of {len(failed_cases)} failed cases are shown; see JSON.")

    finding_counts = Counter(
        finding["code"]
        for target in report["targets"]
        for case in target["cases"]
        for finding in case.get("findings", [])
    )
    lines.extend(["", "## Semantic finding counts", ""])
    if not finding_counts:
        lines.append("None.")
    else:
        lines.extend(["| Finding code | Count |", "|---|---:|"])
        for code, count in sorted(finding_counts.items()):
            lines.append(f"| `{code}` | {count} |")

        lines.extend(["", "## Semantic finding examples", ""])
        examples: dict[str, list[tuple[str, str, Mapping[str, Any]]]] = defaultdict(list)
        for target in report["targets"]:
            for case in target["cases"]:
                for finding in case.get("findings", []):
                    if len(examples[finding["code"]]) < 10:
                        examples[finding["code"]].append(
                            (target["benchmark"], case["case_unit_id"], finding)
                        )
        for code in sorted(examples):
            lines.extend([f"### `{code}`", ""])
            for benchmark, case_id, finding in examples[code]:
                excerpt = str(finding.get("excerpt") or finding.get("message") or "")
                excerpt = excerpt.replace("\n", " ").strip()
                lines.append(
                    f"- `{benchmark}/{case_id}` ({finding.get('severity', 'medium')}): {excerpt}"
                )
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    targets = _targets_from_args(args)
    case_prompt_supplements = _case_prompt_supplements_from_args(args)
    target_benchmarks = {target.benchmark for target in targets}
    unused_benchmarks = sorted(
        {
            benchmark
            for benchmark, _case_id in case_prompt_supplements
            if benchmark not in target_benchmarks
        }
    )
    if unused_benchmarks:
        raise SystemExit(
            "Case-prompt supplements were supplied for benchmarks with no target: "
            f"{unused_benchmarks}"
        )
    runtime_root = args.runtime_root.expanduser().resolve()
    prompt_supplement = (
        args.prompt_supplement.expanduser().resolve() if args.prompt_supplement else None
    )
    batch_cache: dict[
        Path,
        tuple[dict[str, Any] | None, dict[str, dict[str, Any]], list[dict[str, Any]]],
    ] = {}
    target_reports = [
        _audit_target(
            target,
            runtime_root=runtime_root,
            prompt_supplement=prompt_supplement,
            expected_provider=args.expected_provider,
            expected_model=args.expected_model,
            expected_reasoning=args.expected_reasoning_effort,
            batch_cache=batch_cache,
            case_prompt_supplements=case_prompt_supplements,
        )
        for target in targets
    ]
    all_cases = [case for target in target_reports for case in target["cases"]]
    failed_case_count = sum(case["status"] == "failed" for case in all_cases)
    finding_case_count = sum(bool(case.get("findings")) for case in all_cases)
    finding_count = sum(len(case.get("findings", [])) for case in all_cases)
    global_error_count = sum(len(target["global_errors"]) for target in target_reports)
    if failed_case_count or global_error_count:
        verdict = "failed"
    elif finding_count:
        verdict = "passed_with_findings"
    else:
        verdict = "passed"
    report = {
        "schema_version": REPORT_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "configuration": {
            "runtime_root": str(runtime_root),
            "prompt_supplement": str(prompt_supplement) if prompt_supplement else None,
            "case_prompt_supplements": [
                {
                    "benchmark": benchmark,
                    "case_unit_id": case_id,
                    "path": str(path),
                }
                for (benchmark, case_id), path in sorted(case_prompt_supplements.items())
            ],
            "expected_provider": args.expected_provider,
            "expected_model": args.expected_model,
            "expected_reasoning_effort": args.expected_reasoning_effort,
            "fail_on_findings": args.fail_on_findings,
        },
        "summary": {
            "target_count": len(target_reports),
            "case_count": len(all_cases),
            "passed_case_count": sum(case["status"] == "passed" for case in all_cases),
            "finding_case_count": finding_case_count,
            "failed_case_count": failed_case_count,
            "finding_count": finding_count,
            "global_error_count": global_error_count,
        },
        "targets": target_reports,
    }
    args.json_report.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_report.parent.mkdir(parents=True, exist_ok=True)
    args.json_report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    args.markdown_report.write_text(_markdown_report(report), encoding="utf-8")
    print(
        f"draft audit verdict={verdict} cases={len(all_cases)} failed_cases={failed_case_count} "
        f"global_errors={global_error_count} findings={finding_count}"
    )
    print(f"json_report={args.json_report.resolve()}")
    print(f"markdown_report={args.markdown_report.resolve()}")
    if verdict == "failed" or (args.fail_on_findings and finding_count):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
