#!/usr/bin/env python3
"""Run outcome-blind semantic reviews for all matching packet/checklist pairs."""

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
REPO_ROOT = SCRIPT_DIR.parents[1]
MINIMAL_ROOT = REPO_ROOT / "neurips_ed_track_minimal"
REVIEWER_SCRIPT = MINIMAL_ROOT / "scripts/review_case_checklist_with_codex.py"
REVIEW_SCHEMA = MINIMAL_ROOT / "schemas/case_checklist_review.schema.json"
REVIEW_PROMPT = SCRIPT_DIR / "semantic_review.prompt.md"
REVIEW_ITEM_IDS = (
    "identity_and_scope",
    "native_user_goal",
    "native_evaluator_semantics",
    "decisive_post_run_evidence",
    "decision_rules_sfu",
    "source_support_pointers",
    "stronger_conditions",
    "minimality_and_no_run_leakage",
    "stronger_conflict_separation",
)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

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
    parser.add_argument(
        "--review-prompt",
        type=Path,
        default=REVIEW_PROMPT,
        help="Pinned reviewer prompt; defaults to semantic_review.prompt.md.",
    )
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument(
        "--reasoning-effort",
        default="high",
        choices=["minimal", "low", "medium", "high", "xhigh"],
    )
    parser.add_argument("--max-parallel", type=int, default=32)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--codex-timeout-seconds", type=int, default=1800)
    parser.add_argument("--retry-sleep-seconds", type=float, default=2.0)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def discover_cases(case_packet_root: Path, draft_root: Path) -> list[CaseInputs]:
    packets = {path.parent.name: path for path in case_packet_root.glob("*/case_packet.md")}
    drafts = {path.parent.name: path for path in draft_root.glob("*/checklist.yaml")}
    if not packets or set(packets) != set(drafts):
        raise RuntimeError(
            "packet/draft identity sets differ: "
            f"packets={len(packets)} drafts={len(drafts)} "
            f"missing_drafts={sorted(set(packets) - set(drafts))} "
            f"missing_packets={sorted(set(drafts) - set(packets))}"
        )
    return [
        CaseInputs(case_id, packets[case_id], drafts[case_id])
        for case_id in sorted(packets)
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


def sidecars(output_path: Path) -> dict[str, Path]:
    return reviewer.sidecar_paths_for_output(output_path)


def load_valid_review(path: Path, case_id: str) -> dict[str, Any] | None:
    required = [path, *sidecars(path).values()]
    if not all(item.is_file() for item in required):
        return None
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
        validated = reviewer.validate_model_review_body(
            body,
            REVIEW_SCHEMA,
            review_item_ids=REVIEW_ITEM_IDS,
        )
        llm_call = json.loads(sidecars(path)["llm_call"].read_text(encoding="utf-8"))
        if str(llm_call.get("case_unit_id")) != case_id:
            return None
        return validated
    except (OSError, ValueError, reviewer.ChecklistModelReviewError):
        return None


def promote_attempt(case_dir: Path, attempt_path: Path) -> None:
    promoted = case_dir / "review.json"
    shutil.copy2(attempt_path, promoted)
    attempt_sidecars = sidecars(attempt_path)
    promoted_sidecars = sidecars(promoted)
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

    attempts: list[dict[str, Any]] = []
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
            str(args.review_prompt),
            "--review-schema",
            str(REVIEW_SCHEMA),
            "--review-item-ids",
            ",".join(REVIEW_ITEM_IDS),
            "--experiment-type",
            "tb21_deepswe11_outcome_blind_draft_audit",
            "--reviewer-role",
            "independent_case_checklist_semantic_reviewer",
        ]
        started_at = utc_now_iso()
        start = time.monotonic()
        proc = subprocess.run(
            command,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        duration = round(time.monotonic() - start, 3)
        write_text(case_dir / f"{prefix}.stdout.log", proc.stdout)
        write_text(case_dir / f"{prefix}.stderr.log", proc.stderr)
        validated = (
            load_valid_review(output_path, case.case_id)
            if proc.returncode == 0
            else None
        )
        attempt = {
            "attempt": attempt_index,
            "started_at": started_at,
            "finished_at": utc_now_iso(),
            "duration_seconds": duration,
            "returncode": proc.returncode,
            "valid": validated is not None,
            "stderr_tail": proc.stderr[-2000:],
        }
        attempts.append(attempt)
        write_json_atomic(case_dir / f"{prefix}.status.json", attempt)
        if validated is not None:
            promote_attempt(case_dir, output_path)
            outcome = {
                "case_id": case.case_id,
                "status": "completed",
                "decision": validated["decision"],
                "attempt": attempt_index,
                "duration_seconds": duration,
            }
            write_json_atomic(case_dir / "status.json", {**outcome, "attempts": attempts})
            return outcome
        if attempt_index < args.max_attempts:
            time.sleep(args.retry_sleep_seconds)

    outcome = {
        "case_id": case.case_id,
        "status": "failed",
        "decision": None,
        "attempt": args.max_attempts,
    }
    write_json_atomic(case_dir / "status.json", {**outcome, "attempts": attempts})
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
        "schema_version": "tb21_deepswe11_draft_semantic_review_batch/v1",
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
            "source_boundary": ["case_packet.md", "checklist.yaml", "review_prompt.md"],
            "review_prompt_sha256": sha256_file(args.review_prompt),
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
    required = (args.review_prompt, REVIEW_SCHEMA, REVIEWER_SCRIPT)
    if not all(path.is_file() for path in required):
        raise SystemExit(f"missing pinned reviewer input: {[str(p) for p in required if not p.is_file()]}")

    cases = discover_cases(args.case_packet_root, args.draft_root)
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
            except Exception as exc:
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

    summary = make_summary(cases, outcomes, args, started_at)
    write_json_atomic(summary_path, summary)
    print(
        json.dumps(
            {
                key: summary[key]
                for key in (
                    "input_case_count",
                    "completed_count",
                    "accept_count",
                    "revise_count",
                    "failed_count",
                )
            },
            ensure_ascii=False,
        )
    )
    return 0 if summary["failed_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
