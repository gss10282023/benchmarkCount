#!/usr/bin/env python3
"""Batch-generate outcome-blind v2 replacements for rejected case checklists.

Each model call sees exactly one case packet and a case-specific repair supplement
containing the frozen original checklist and prior outcome-blind review findings.
The runner never reads outcomes, retained execution artifact contents, labels,
scores, or conflict records.  It keeps every attempt and promotes only a locally
schema/guardrail/pointer-valid checklist into the v2 candidate directory.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
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
DRAFTER = REPO_ROOT / "neurips_ed_track_minimal/scripts/draft_case_checklist.py"
VALIDATOR = REPO_ROOT / "neurips_ed_track_minimal/scripts/checklist_validator.py"


@dataclass(frozen=True)
class CaseInput:
    case_id: str
    packet: Path
    context: Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{threading.get_ident()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-packet-root", type=Path, required=True)
    parser.add_argument("--repair-context-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--model", default="gpt-5.4")
    parser.add_argument(
        "--reasoning-effort",
        default="high",
        choices=["minimal", "low", "medium", "high", "xhigh", "max"],
    )
    parser.add_argument("--max-parallel", type=int, default=12)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--max-output-tokens", type=int, default=16000)
    parser.add_argument("--codex-timeout-seconds", type=int, default=1800)
    parser.add_argument("--retry-sleep-seconds", type=float, default=2.0)
    parser.add_argument("--case-ids", default=None, help="Optional comma-separated exact case IDs")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def parse_case_ids(raw: str | None) -> set[str] | None:
    if raw is None:
        return None
    values = [value.strip() for value in raw.split(",")]
    if not values or any(not value for value in values) or len(values) != len(set(values)):
        raise SystemExit("--case-ids must be a duplicate-free nonempty comma-separated list")
    return set(values)


def discover_cases(packet_root: Path, context_root: Path, selected: set[str] | None) -> list[CaseInput]:
    packets = {path.parent.name: path for path in packet_root.glob("*/case_packet.md")}
    contexts = {path.parent.name: path for path in context_root.glob("*/repair_context.md")}
    if selected is not None:
        packets = {case_id: path for case_id, path in packets.items() if case_id in selected}
        contexts = {case_id: path for case_id, path in contexts.items() if case_id in selected}
        unknown = selected - set(packets)
        if unknown:
            raise SystemExit(f"selected IDs not in packet root: {sorted(unknown)}")
        if not packets or set(packets) != set(contexts):
            raise SystemExit(
                "packet/context identity mismatch: "
                f"packets={len(packets)} contexts={len(contexts)} "
                f"missing_context={sorted(set(packets) - set(contexts))} "
                f"missing_packet={sorted(set(contexts) - set(packets))}"
            )
    else:
        missing_context = set(packets) - set(contexts)
        if missing_context:
            raise SystemExit(f"packet cases missing repair context: {sorted(missing_context)}")
        # The context root spans both benchmarks.  Do not duplicate packet trees
        # just to schedule each benchmark family independently.
        packets = {case_id: path for case_id, path in packets.items() if case_id in contexts}
    if not packets:
        raise SystemExit("no matching packet/context cases discovered")
    return [CaseInput(case_id, packets[case_id], contexts[case_id]) for case_id in sorted(packets)]


def validate(checklist: Path, packet: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), str(checklist), "--case-packet", str(packet)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    message = "\n".join(part for part in (proc.stdout.strip(), proc.stderr.strip()) if part).strip()
    return proc.returncode == 0, message


def attempt_sidecars(case_dir: Path, prefix: str) -> list[str]:
    return [
        f"{prefix}.checklist.yaml",
        f"{prefix}.checklist.json",
        f"{prefix}.api_response.json",
        f"{prefix}.llm_call.json",
        f"{prefix}.reasoning_summary.txt",
        f"{prefix}.stdout.log",
        f"{prefix}.stderr.log",
    ]


def promote(case_dir: Path, prefix: str) -> None:
    names = attempt_sidecars(case_dir, prefix)
    canonical = {
        f"{prefix}.checklist.yaml": "checklist.yaml",
        f"{prefix}.checklist.json": "checklist.json",
        f"{prefix}.api_response.json": "api_response.json",
        f"{prefix}.llm_call.json": "llm_call.json",
        f"{prefix}.reasoning_summary.txt": "reasoning_summary.txt",
        f"{prefix}.stdout.log": "stdout.log",
        f"{prefix}.stderr.log": "stderr.log",
    }
    for name in names:
        source = case_dir / name
        if source.is_file():
            shutil.copy2(source, case_dir / canonical[name])


def existing_valid(case_dir: Path, packet: Path) -> bool:
    needed = [
        case_dir / "checklist.yaml",
        case_dir / "checklist.json",
        case_dir / "llm_call.json",
        case_dir / "api_response.json",
    ]
    if not all(path.is_file() for path in needed):
        return False
    valid, _ = validate(case_dir / "checklist.yaml", packet)
    return valid


def run_one(case: CaseInput, args: argparse.Namespace) -> dict[str, Any]:
    case_dir = args.output_root / case.case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    if not args.force and existing_valid(case_dir, case.packet):
        return {
            "case_unit_id": case.case_id,
            "status": "skipped_existing",
            "attempts": [],
            "checklist_sha256": sha256_file(case_dir / "checklist.yaml"),
            "repair_context_sha256": sha256_file(case.context),
        }

    attempts: list[dict[str, Any]] = []
    for index in range(1, args.max_attempts + 1):
        prefix = f"attempt_{index:02d}"
        output = case_dir / f"{prefix}.checklist.yaml"
        raw_json = case_dir / f"{prefix}.checklist.json"
        raw_api = case_dir / f"{prefix}.api_response.json"
        command = [
            sys.executable,
            str(DRAFTER),
            str(case.packet),
            "-o",
            str(output),
            "--raw-json-output",
            str(raw_json),
            "--raw-api-response",
            str(raw_api),
            "--provider",
            "codex",
            "--model",
            args.model,
            "--reasoning-effort",
            args.reasoning_effort,
            "--max-output-tokens",
            str(args.max_output_tokens),
            "--codex-timeout-seconds",
            str(args.codex_timeout_seconds),
            "--codex-sandbox",
            "read-only",
            "--prompt-supplement",
            str(case.context),
        ]
        started_at = utc_now()
        started = time.monotonic()
        proc = subprocess.run(command, cwd=str(REPO_ROOT), capture_output=True, text=True, check=False)
        elapsed = round(time.monotonic() - started, 3)
        write_text(case_dir / f"{prefix}.stdout.log", proc.stdout)
        write_text(case_dir / f"{prefix}.stderr.log", proc.stderr)
        valid = False
        validation = "drafter did not produce a candidate"
        if proc.returncode == 0 and output.is_file():
            valid, validation = validate(output, case.packet)
        attempt = {
            "attempt_index": index,
            "started_at": started_at,
            "finished_at": utc_now(),
            "duration_seconds": elapsed,
            "returncode": proc.returncode,
            "validator_passed": valid,
            "validator_output": validation,
            "stderr_tail": proc.stderr[-2000:],
        }
        attempts.append(attempt)
        write_json_atomic(case_dir / f"{prefix}.status.json", attempt)
        if valid:
            promote(case_dir, prefix)
            result = {
                "case_unit_id": case.case_id,
                "status": "completed",
                "attempt": index,
                "attempts": attempts,
                "checklist_sha256": sha256_file(case_dir / "checklist.yaml"),
                "repair_context_sha256": sha256_file(case.context),
            }
            write_json_atomic(case_dir / "status.json", result)
            return result
        if index < args.max_attempts:
            time.sleep(args.retry_sleep_seconds)
    result = {
        "case_unit_id": case.case_id,
        "status": "failed",
        "attempt": args.max_attempts,
        "attempts": attempts,
        "repair_context_sha256": sha256_file(case.context),
    }
    write_json_atomic(case_dir / "status.json", result)
    return result


def summary(cases: list[CaseInput], outcomes: dict[str, dict[str, Any]], args: argparse.Namespace, started_at: str) -> dict[str, Any]:
    rows = [outcomes[case.case_id] for case in cases if case.case_id in outcomes]
    return {
        "schema_version": "tb21_deepswe11_outcome_blind_repair_v2_batch/v1",
        "started_at": started_at,
        "updated_at": utc_now(),
        "input_case_count": len(cases),
        "processed_count": len(rows),
        "completed_count": sum(row["status"] in {"completed", "skipped_existing"} for row in rows),
        "failed_count": sum(row["status"] == "failed" for row in rows),
        "pending_count": len(cases) - len(rows),
        "source_boundary": ["case_packet.md", "repair_context.md", "frozen base draft prompt/schema/template"],
        "excluded_inputs": [
            "agent outcomes",
            "agent trajectory contents",
            "concrete retained execution-artifact contents",
            "per-record evaluator reward/result/label values",
            "evidence-scoring outputs",
            "benchmark-conflict records",
        ],
        "config": {
            "provider": "codex_cli",
            "model": args.model,
            "reasoning_effort": args.reasoning_effort,
            "sandbox": "read-only",
            "max_parallel": args.max_parallel,
            "max_attempts": args.max_attempts,
            "max_output_tokens": args.max_output_tokens,
            "codex_timeout_seconds": args.codex_timeout_seconds,
        },
        "cases": rows,
    }


def main() -> int:
    args = parse_args()
    if args.max_parallel < 1 or args.max_attempts < 1 or args.codex_timeout_seconds < 1:
        raise SystemExit("parallelism, attempt count, and timeout must be positive")
    if args.retry_sleep_seconds < 0:
        raise SystemExit("retry sleep must be non-negative")
    if not DRAFTER.is_file() or not VALIDATOR.is_file():
        raise SystemExit("missing frozen drafter or validator")
    cases = discover_cases(
        args.case_packet_root.resolve(), args.repair_context_root.resolve(), parse_case_ids(args.case_ids)
    )
    args.output_root = args.output_root.resolve()
    args.output_root.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()
    outcomes: dict[str, dict[str, Any]] = {}
    lock = threading.Lock()
    summary_path = args.output_root / "_repair_batch_summary.json"
    write_json_atomic(summary_path, summary(cases, outcomes, args, started_at))
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_parallel) as executor:
        futures = {executor.submit(run_one, case, args): case for case in cases}
        for future in concurrent.futures.as_completed(futures):
            case = futures[future]
            try:
                result = future.result()
            except Exception as exc:  # preserve case-level failure rather than discarding the batch
                result = {
                    "case_unit_id": case.case_id,
                    "status": "failed",
                    "attempt": 0,
                    "attempts": [],
                    "runner_error": f"{type(exc).__name__}: {exc}",
                }
            with lock:
                outcomes[case.case_id] = result
                current = summary(cases, outcomes, args, started_at)
                write_json_atomic(summary_path, current)
                print(
                    f"[{current['processed_count']}/{current['input_case_count']}] "
                    f"case={case.case_id} status={result['status']}",
                    flush=True,
                )
    final = summary(cases, outcomes, args, started_at)
    write_json_atomic(summary_path, final)
    print(json.dumps({key: final[key] for key in ("input_case_count", "completed_count", "failed_count")}, ensure_ascii=False))
    return 0 if final["failed_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
