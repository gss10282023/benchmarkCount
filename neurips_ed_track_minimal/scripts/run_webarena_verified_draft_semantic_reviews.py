#!/usr/bin/env python3
"""Review every WebArena-Verified checklist independently with bounded concurrency.

Each model call receives only the matching case packet, checklist, and pinned review
prompt. The runner is resumable: a schema-valid promoted review is never re-run unless
``--force`` is supplied.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
PACKAGE_ROOT = ROOT_DIR.parent
REVIEWER_SCRIPT = SCRIPT_DIR / "review_case_checklist_with_codex.py"
REVIEW_PROMPT = ROOT_DIR / "prompts" / "review_webarena_verified_checklist.prompt.md"
REVIEW_SCHEMA = ROOT_DIR / "schemas" / "case_checklist_review.schema.json"
REVIEW_ITEM_IDS = (
    "identity_and_scope",
    "native_user_goal",
    "official_evaluator_semantics",
    "evaluator_composition",
    "decisive_post_run_evidence",
    "decision_rules",
    "source_support_pointers",
    "stronger_conditions",
    "minimality_and_no_run_leakage",
)

if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from neurips_ed_track_minimal.scripts import (  # noqa: E402
    review_case_checklist_with_codex as reviewer,
)


@dataclass(frozen=True)
class CaseInputs:
    case_id: str
    case_packet: Path
    checklist: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-packet-root", type=Path, required=True)
    parser.add_argument("--draft-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument(
        "--reasoning-effort",
        default="xhigh",
        choices=["minimal", "low", "medium", "high", "xhigh"],
    )
    parser.add_argument("--max-parallel", type=int, default=72)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--codex-timeout-seconds", type=int, default=1800)
    parser.add_argument("--retry-sleep-seconds", type=float, default=3.0)
    parser.add_argument("--case-ids", default=None)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def numeric_case_key(case_id: str) -> tuple[int, int | str]:
    try:
        return (0, int(case_id))
    except ValueError:
        return (1, case_id)


def parse_case_ids(raw: str | None) -> set[str] | None:
    if raw is None:
        return None
    case_ids = [item.strip() for item in raw.split(",") if item.strip()]
    if not case_ids or len(case_ids) != len(set(case_ids)):
        raise SystemExit("--case-ids must be a nonempty duplicate-free comma-separated list")
    return set(case_ids)


def discover_cases(
    case_packet_root: Path,
    draft_root: Path,
    selected: set[str] | None,
) -> list[CaseInputs]:
    packet_paths = {path.parent.name: path for path in case_packet_root.glob("*/case_packet.md")}
    checklist_paths = {path.parent.name: path for path in draft_root.glob("*/checklist.yaml")}
    case_ids = set(packet_paths) & set(checklist_paths)
    if selected is not None:
        missing = selected - case_ids
        if missing:
            raise SystemExit(
                "Selected case inputs are missing: "
                + ", ".join(sorted(missing, key=numeric_case_key))
            )
        case_ids &= selected
    if not case_ids:
        raise SystemExit("No matching case packets and draft checklists found")
    if selected is None and set(packet_paths) != set(checklist_paths):
        missing_drafts = set(packet_paths) - set(checklist_paths)
        missing_packets = set(checklist_paths) - set(packet_paths)
        raise SystemExit(
            f"Input roots differ: missing_drafts={len(missing_drafts)} "
            f"missing_packets={len(missing_packets)}"
        )
    return [
        CaseInputs(
            case_id=case_id,
            case_packet=packet_paths[case_id],
            checklist=checklist_paths[case_id],
        )
        for case_id in sorted(case_ids, key=numeric_case_key)
    ]


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(
        f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp"
    )
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def review_sidecars(output_path: Path) -> dict[str, Path]:
    return reviewer.sidecar_paths_for_output(output_path)


def load_valid_review(path: Path, case_id: str) -> dict[str, Any] | None:
    required = [path, *review_sidecars(path).values()]
    if not all(item.is_file() for item in required):
        return None
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
        validated = reviewer.validate_model_review_body(
            body,
            REVIEW_SCHEMA,
            review_item_ids=REVIEW_ITEM_IDS,
        )
        llm_call = json.loads(
            review_sidecars(path)["llm_call"].read_text(encoding="utf-8")
        )
        if str(llm_call.get("case_unit_id")) != case_id:
            return None
        return validated
    except (OSError, ValueError, reviewer.ChecklistModelReviewError):
        return None


def promote_attempt(case_dir: Path, attempt_path: Path) -> None:
    promoted = case_dir / "review.json"
    shutil.copy2(attempt_path, promoted)
    attempt_sidecars = review_sidecars(attempt_path)
    promoted_sidecars = review_sidecars(promoted)
    for name in ("api_response", "llm_call", "reasoning_summary"):
        shutil.copy2(attempt_sidecars[name], promoted_sidecars[name])


def review_one(case: CaseInputs, args: argparse.Namespace) -> dict[str, Any]:
    case_dir = args.output_root / case.case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    promoted = case_dir / "review.json"
    if not args.force:
        existing = load_valid_review(promoted, case.case_id)
        if existing is not None:
            return {
                "case_id": case.case_id,
                "status": "completed",
                "decision": existing["decision"],
                "attempt": "existing",
            }

    attempt_errors: list[dict[str, Any]] = []
    for attempt_index in range(1, args.max_attempts + 1):
        prefix = f"attempt_{attempt_index:02d}"
        output_path = case_dir / f"{prefix}.review.json"
        command = [
            sys.executable,
            str(REVIEWER_SCRIPT),
            str(case.case_packet),
            str(case.checklist),
            "-o",
            str(output_path),
            "--model",
            args.model,
            "--reasoning-effort",
            args.reasoning_effort,
            "--codex-timeout-seconds",
            str(args.codex_timeout_seconds),
            "--codex-sandbox",
            "read-only",
            "--review-prompt",
            str(REVIEW_PROMPT),
            "--review-schema",
            str(REVIEW_SCHEMA),
            "--review-item-ids",
            ",".join(REVIEW_ITEM_IDS),
            "--experiment-type",
            "webarena_verified_full_812",
            "--reviewer-role",
            "case_checklist_semantic_reviewer",
        ]
        started_at = utc_now_iso()
        start = time.monotonic()
        proc = subprocess.run(
            command,
            cwd=str(PACKAGE_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        duration = time.monotonic() - start
        write_text(case_dir / f"{prefix}.stdout.log", proc.stdout)
        write_text(case_dir / f"{prefix}.stderr.log", proc.stderr)
        validated = (
            load_valid_review(output_path, case.case_id)
            if proc.returncode == 0
            else None
        )
        attempt_record = {
            "attempt": attempt_index,
            "started_at": started_at,
            "finished_at": utc_now_iso(),
            "duration_seconds": round(duration, 3),
            "returncode": proc.returncode,
            "valid": validated is not None,
            "stderr_tail": proc.stderr[-2000:],
        }
        attempt_errors.append(attempt_record)
        write_json_atomic(case_dir / f"{prefix}.status.json", attempt_record)
        if validated is not None:
            promote_attempt(case_dir, output_path)
            outcome = {
                "case_id": case.case_id,
                "status": "completed",
                "decision": validated["decision"],
                "attempt": attempt_index,
                "duration_seconds": round(duration, 3),
            }
            write_json_atomic(
                case_dir / "status.json",
                {**outcome, "attempts": attempt_errors},
            )
            return outcome
        if attempt_index < args.max_attempts:
            time.sleep(args.retry_sleep_seconds)

    outcome = {
        "case_id": case.case_id,
        "status": "failed",
        "decision": None,
        "attempt": args.max_attempts,
    }
    write_json_atomic(
        case_dir / "status.json",
        {**outcome, "attempts": attempt_errors},
    )
    return outcome


def make_summary(
    cases: list[CaseInputs],
    outcomes: dict[str, dict[str, Any]],
    args: argparse.Namespace,
    started_at: str,
) -> dict[str, Any]:
    ordered = [outcomes[case.case_id] for case in cases if case.case_id in outcomes]
    completed = [item for item in ordered if item["status"] == "completed"]
    failed = [item for item in ordered if item["status"] == "failed"]
    return {
        "schema_version": "webarena_verified_draft_semantic_review_batch/v1",
        "started_at": started_at,
        "updated_at": utc_now_iso(),
        "input_case_count": len(cases),
        "processed_count": len(ordered),
        "completed_count": len(completed),
        "accept_count": sum(item["decision"] == "accept" for item in completed),
        "revise_count": sum(item["decision"] == "revise" for item in completed),
        "failed_count": len(failed),
        "pending_count": len(cases) - len(ordered),
        "accept_case_ids": [
            item["case_id"] for item in completed if item["decision"] == "accept"
        ],
        "revise_case_ids": [
            item["case_id"] for item in completed if item["decision"] == "revise"
        ],
        "failed_case_ids": [item["case_id"] for item in failed],
        "config": {
            "model": args.model,
            "reasoning_effort": args.reasoning_effort,
            "max_parallel": args.max_parallel,
            "max_attempts": args.max_attempts,
            "codex_timeout_seconds": args.codex_timeout_seconds,
            "review_item_ids": list(REVIEW_ITEM_IDS),
            "source_boundary": [
                "case_packet.md",
                "checklist.yaml",
                "review_prompt.md",
            ],
            "review_prompt_sha256": sha256_file(REVIEW_PROMPT),
            "review_schema_sha256": sha256_file(REVIEW_SCHEMA),
            "reviewer_script_sha256": sha256_file(REVIEWER_SCRIPT),
        },
        "cases": ordered,
    }


def main() -> int:
    args = parse_args()
    if args.max_parallel <= 0 or args.max_attempts <= 0:
        raise SystemExit("parallelism and attempts must be positive")
    if args.codex_timeout_seconds <= 0 or args.retry_sleep_seconds < 0:
        raise SystemExit("timeout must be positive and retry sleep non-negative")
    if not all(path.is_file() for path in (REVIEW_PROMPT, REVIEW_SCHEMA, REVIEWER_SCRIPT)):
        raise SystemExit("Pinned reviewer inputs are missing")
    cases = discover_cases(
        args.case_packet_root,
        args.draft_root,
        parse_case_ids(args.case_ids),
    )
    args.output_root.mkdir(parents=True, exist_ok=True)
    started_at = utc_now_iso()
    outcomes: dict[str, dict[str, Any]] = {}
    lock = threading.Lock()
    summary_path = args.output_root / "_review_batch_summary.json"
    write_json_atomic(summary_path, make_summary(cases, outcomes, args, started_at))

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_parallel) as executor:
        futures = {executor.submit(review_one, case, args): case for case in cases}
        for future in concurrent.futures.as_completed(futures):
            case = futures[future]
            try:
                outcome = future.result()
            except Exception as exc:  # fail one case closed without losing the ledger
                outcome = {
                    "case_id": case.case_id,
                    "status": "failed",
                    "decision": None,
                    "attempt": 0,
                    "runner_error": f"{type(exc).__name__}: {exc}",
                }
            with lock:
                outcomes[case.case_id] = outcome
                summary = make_summary(cases, outcomes, args, started_at)
                write_json_atomic(summary_path, summary)
                print(
                    f"[{summary['processed_count']}/{summary['input_case_count']}] "
                    f"case={case.case_id} status={outcome['status']} "
                    f"decision={outcome['decision']}",
                    flush=True,
                )

    final_summary = make_summary(cases, outcomes, args, started_at)
    write_json_atomic(summary_path, final_summary)
    final_counts = {
        key: final_summary[key]
        for key in (
            "input_case_count",
            "completed_count",
            "accept_count",
            "revise_count",
            "failed_count",
        )
    }
    print(json.dumps(final_counts, ensure_ascii=False))
    return 0 if final_summary["failed_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
