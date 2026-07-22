#!/usr/bin/env python3
"""Batch-score benchmark evidence from a benchmark-agnostic task directory.

Each direct child of ``--task-root`` is one independent score task:

  <task_id>/checklist.yaml
  <task_id>/evidence/**
  <task_id>/native_label.json  # optional explicit released label

The runner validates every checklist and released evaluator label before any
model call, seals a hash-bound task plan, and delegates each score to the
canonical ``score_evidence_with_codex.py`` implementation.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
PACKAGE_ROOT = ROOT_DIR.parent
SCORE_SCRIPT = SCRIPT_DIR / "score_evidence_with_codex.py"
CHECKLIST_VALIDATOR = SCRIPT_DIR / "checklist_validator.py"
PROMPT_PATH = ROOT_DIR / "prompts" / "score_evidence_with_codex.prompt.md"
SCHEMA_PATH = ROOT_DIR / "schemas" / "evidence_score.schema.json"
DEFAULT_MODEL = "gpt-5.4"
DEFAULT_REASONING_EFFORT = "xhigh"
DEFAULT_CODEX_TIMEOUT_SECONDS = 1800
TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")

if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from neurips_ed_track_minimal.scripts import score_evidence_with_codex as scorer  # noqa: E402


class ScoreBatchError(RuntimeError):
    """Raised when a generic score job is invalid or cannot complete."""


@dataclass(frozen=True)
class ScoreTask:
    task_index: int
    task_id: str
    task_dir: Path
    checklist_path: Path
    evidence_dir: Path
    native_label_path: Path | None
    case_unit_id: str
    checklist_sha256: str
    evidence_tree_sha256: str
    native_label_sha256: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--reasoning-effort",
        default=DEFAULT_REASONING_EFFORT,
        choices=["minimal", "low", "medium", "high", "xhigh", "max"],
    )
    parser.add_argument(
        "--sandbox",
        default="read-only",
        choices=["read-only"],
        help="The VPS score service is intentionally read-only.",
    )
    parser.add_argument("--service-tier", default="default")
    parser.add_argument("--max-parallel", type=int, default=1)
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument(
        "--codex-timeout-seconds",
        type=int,
        default=DEFAULT_CODEX_TIMEOUT_SECONDS,
    )
    parser.add_argument("--max-run-attempts", type=int, default=2)
    parser.add_argument("--max-input-files", type=int, default=200_000)
    parser.add_argument("--max-input-bytes", type=int, default=100 * 1024**3)
    parser.add_argument("--max-single-file-bytes", type=int, default=5 * 1024**3)
    parser.add_argument("--min-free-bytes", type=int, default=20 * 1024**3)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tree(root: Path) -> str:
    entries: list[dict[str, str]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        entries.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": sha256_file(path),
            }
        )
    encoded = json.dumps(
        entries,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}-{threading.get_ident()}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def append_jsonl(path: Path, value: dict[str, Any], lock: threading.Lock) -> None:
    with lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(value, ensure_ascii=False) + "\n")


def validate_regular_tree(
    root: Path,
    *,
    max_files: int,
    max_bytes: int,
    max_single_file_bytes: int,
) -> dict[str, int]:
    if root.is_symlink() or not root.is_dir():
        raise ScoreBatchError(f"Task root must be a real directory: {root}")

    file_count = 0
    total_bytes = 0
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        parent = Path(dirpath)
        for name in [*dirnames, *filenames]:
            path = parent / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ScoreBatchError(f"Score inputs must not contain symlinks: {path}")
            if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise ScoreBatchError(
                    f"Score inputs may contain only directories and regular files: {path}"
                )
            if not stat.S_ISREG(mode):
                continue
            metadata = path.stat()
            if metadata.st_nlink != 1:
                raise ScoreBatchError(f"Score inputs must not contain hard-linked files: {path}")
            if metadata.st_size > max_single_file_bytes:
                raise ScoreBatchError(
                    f"Score input file exceeds the configured size limit: {path}"
                )
            file_count += 1
            total_bytes += metadata.st_size
            if file_count > max_files:
                raise ScoreBatchError(
                    f"Score input exceeds the configured file-count limit ({max_files})"
                )
            if total_bytes > max_bytes:
                raise ScoreBatchError(
                    f"Score input exceeds the configured byte limit ({max_bytes})"
                )
    return {"file_count": file_count, "total_bytes": total_bytes}


def validate_checklist(checklist_path: Path) -> dict[str, Any]:
    process = subprocess.run(
        [sys.executable, str(CHECKLIST_VALIDATOR), str(checklist_path)],
        cwd=str(PACKAGE_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        detail = (process.stderr or process.stdout or "unknown validation error").strip()
        raise ScoreBatchError(f"Checklist validation failed for {checklist_path}: {detail}")
    checklist = scorer.load_yaml(checklist_path)
    case_unit_id = str(checklist.get("case_unit_id") or "").strip()
    if not case_unit_id:
        raise ScoreBatchError(f"Checklist has no case_unit_id: {checklist_path}")
    return checklist


def discover_tasks(
    task_root: Path,
    *,
    max_files: int,
    max_bytes: int,
    max_single_file_bytes: int,
) -> tuple[list[ScoreTask], dict[str, int]]:
    tree_stats = validate_regular_tree(
        task_root,
        max_files=max_files,
        max_bytes=max_bytes,
        max_single_file_bytes=max_single_file_bytes,
    )
    tasks: list[ScoreTask] = []
    for task_dir in sorted(
        path
        for path in task_root.iterdir()
        if path.is_dir() and not path.name.startswith("_")
    ):
        task_id = task_dir.name
        if not TASK_ID_RE.fullmatch(task_id):
            raise ScoreBatchError(
                f"Invalid task directory name {task_id!r}; expected {TASK_ID_RE.pattern}"
            )
        checklist_path = task_dir / "checklist.yaml"
        evidence_dir = task_dir / "evidence"
        native_label_path = task_dir / "native_label.json"
        if checklist_path.is_symlink() or not checklist_path.is_file():
            raise ScoreBatchError(f"Missing checklist.yaml for task {task_id}")
        if evidence_dir.is_symlink() or not evidence_dir.is_dir():
            raise ScoreBatchError(f"Missing evidence directory for task {task_id}")
        if not any(path.is_file() for path in evidence_dir.rglob("*")):
            raise ScoreBatchError(f"Evidence directory is empty for task {task_id}")
        if native_label_path.exists() and (
            native_label_path.is_symlink() or not native_label_path.is_file()
        ):
            raise ScoreBatchError(
                f"native_label.json must be a regular file for task {task_id}"
            )
        resolved_native_label = native_label_path if native_label_path.exists() else None
        checklist = validate_checklist(checklist_path)
        try:
            scorer.resolve_released_evaluator_label(
                evidence_dir=evidence_dir.resolve(),
                native_label_path=(
                    resolved_native_label.resolve() if resolved_native_label else None
                ),
            )
        except Exception as exc:
            raise ScoreBatchError(
                f"Could not resolve a released evaluator label for task {task_id}: {exc}"
            ) from exc
        tasks.append(
            ScoreTask(
                task_index=len(tasks),
                task_id=task_id,
                task_dir=task_dir.resolve(),
                checklist_path=checklist_path.resolve(),
                evidence_dir=evidence_dir.resolve(),
                native_label_path=(
                    resolved_native_label.resolve() if resolved_native_label else None
                ),
                case_unit_id=str(checklist["case_unit_id"]),
                checklist_sha256=sha256_file(checklist_path),
                evidence_tree_sha256=sha256_tree(evidence_dir),
                native_label_sha256=(
                    sha256_file(resolved_native_label)
                    if resolved_native_label is not None
                    else None
                ),
            )
        )
    if not tasks:
        raise ScoreBatchError(f"No score task directories found under {task_root}")
    return tasks, tree_stats


def task_record(task: ScoreTask, *, output_root: Path) -> dict[str, Any]:
    return {
        "task_index": task.task_index,
        "task_id": task.task_id,
        "case_unit_id": task.case_unit_id,
        "checklist_path": str(task.checklist_path),
        "checklist_sha256": task.checklist_sha256,
        "evidence_dir": str(task.evidence_dir),
        "evidence_tree_sha256": task.evidence_tree_sha256,
        "native_label_path": (
            str(task.native_label_path) if task.native_label_path else None
        ),
        "native_label_sha256": task.native_label_sha256,
        "output_prefix": str((output_root / task.task_id / "score").resolve()),
    }


def resolve_source_codex_home() -> Path:
    raw = os.environ.get("CODEX_HOME")
    if not raw:
        raise ScoreBatchError("CODEX_HOME is not set for the score service")
    source = Path(raw).resolve()
    auth = source / "auth.json"
    if auth.is_symlink() or not auth.is_file():
        raise ScoreBatchError(f"No Codex login auth.json under CODEX_HOME: {source}")
    return source


def task_codex_home(task: ScoreTask, attempt: int) -> Path:
    root = Path(
        os.environ.get(
            "SCORE_CODEX_HOME_ROOT",
            str(Path(tempfile.gettempdir()) / "codex_score_homes"),
        )
    ).resolve()
    unique = f"{task.task_index:06d}_{attempt}_{os.getpid()}_{threading.get_ident()}_{time.time_ns()}"
    return root / unique


def build_score_command(
    task: ScoreTask,
    *,
    output_prefix: Path,
    model: str,
    reasoning_effort: str,
    sandbox: str,
    service_tier: str,
    max_attempts: int,
    codex_timeout_seconds: int,
) -> list[str]:
    command = [
        sys.executable,
        str(SCORE_SCRIPT),
        "--checklist",
        str(task.checklist_path),
        "--evidence-dir",
        str(task.evidence_dir),
        "--out-prefix",
        str(output_prefix),
        "--model",
        model,
        "--reasoning-effort",
        reasoning_effort,
        "--sandbox",
        sandbox,
        "--service-tier",
        service_tier,
        "--max-attempts",
        str(max_attempts),
        "--codex-timeout-seconds",
        str(codex_timeout_seconds),
    ]
    if task.native_label_path is not None:
        command.extend(["--native-label-path", str(task.native_label_path)])
    return command


def run_task(
    task: ScoreTask,
    *,
    output_root: Path,
    source_codex_home: Path,
    model: str,
    reasoning_effort: str,
    sandbox: str,
    service_tier: str,
    max_attempts: int,
    codex_timeout_seconds: int,
    max_run_attempts: int,
) -> dict[str, Any]:
    if sha256_file(task.checklist_path) != task.checklist_sha256:
        raise ScoreBatchError(f"Checklist changed after preflight: {task.task_id}")
    if sha256_tree(task.evidence_dir) != task.evidence_tree_sha256:
        raise ScoreBatchError(f"Evidence changed after preflight: {task.task_id}")
    if task.native_label_path is not None and (
        sha256_file(task.native_label_path) != task.native_label_sha256
    ):
        raise ScoreBatchError(f"Native label changed after preflight: {task.task_id}")

    output_prefix = (output_root / task.task_id / "score").resolve()
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    command = build_score_command(
        task,
        output_prefix=output_prefix,
        model=model,
        reasoning_effort=reasoning_effort,
        sandbox=sandbox,
        service_tier=service_tier,
        max_attempts=max_attempts,
        codex_timeout_seconds=codex_timeout_seconds,
    )
    process_timeout = (codex_timeout_seconds * max_attempts) + 180
    started = time.time()
    last_stdout = ""
    last_stderr = ""
    last_returncode = 1
    timed_out = False

    for run_attempt in range(1, max_run_attempts + 1):
        codex_home = task_codex_home(task, run_attempt)
        try:
            codex_home.mkdir(parents=True, exist_ok=False)
            shutil.copy2(source_codex_home / "auth.json", codex_home / "auth.json")
            os.chmod(codex_home, 0o700)
            os.chmod(codex_home / "auth.json", 0o600)
            env = dict(os.environ)
            env["CODEX_HOME"] = str(codex_home)
            process = subprocess.run(
                command,
                cwd=str(PACKAGE_ROOT),
                env=env,
                capture_output=True,
                text=True,
                check=False,
                timeout=process_timeout,
            )
            last_stdout = process.stdout or ""
            last_stderr = process.stderr or ""
            last_returncode = process.returncode
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            last_stdout = exc.stdout if isinstance(exc.stdout, str) else ""
            last_stderr = exc.stderr if isinstance(exc.stderr, str) else ""
            last_returncode = 124
            timed_out = True
        finally:
            shutil.rmtree(codex_home, ignore_errors=True)

        required_outputs = (
            output_prefix.with_suffix(".json"),
            output_prefix.with_suffix(".yaml"),
            scorer.manifest_output_path(output_prefix),
        )
        if last_returncode == 0 and all(path.is_file() for path in required_outputs):
            return {
                "status": "success",
                "run_attempts": run_attempt,
                "duration_seconds": round(time.time() - started, 3),
                "returncode": 0,
                "timed_out": False,
                "stdout_tail": last_stdout[-2000:],
                "stderr_tail": last_stderr[-2000:],
            }

    return {
        "status": "failed",
        "run_attempts": max_run_attempts,
        "duration_seconds": round(time.time() - started, 3),
        "returncode": last_returncode,
        "timed_out": timed_out,
        "stdout_tail": last_stdout[-2000:],
        "stderr_tail": last_stderr[-2000:],
    }


def build_transfer_manifest(
    *,
    task_root: Path,
    output_root: Path,
    tasks: list[ScoreTask],
    model: str,
    reasoning_effort: str,
) -> dict[str, Any]:
    outputs: list[dict[str, str]] = []
    if output_root.exists():
        for path in sorted(item for item in output_root.rglob("*") if item.is_file()):
            if path.name == "_transfer_manifest.json":
                continue
            outputs.append(
                {
                    "path": path.relative_to(output_root).as_posix(),
                    "sha256": sha256_file(path),
                }
            )
    return {
        "schema_version": "neurips_score_transfer_manifest_v1",
        "generated_at": utc_now_iso(),
        "model": model,
        "reasoning_effort": reasoning_effort,
        "score_prompt_sha256": sha256_file(PROMPT_PATH),
        "score_schema_sha256": sha256_file(SCHEMA_PATH),
        "tasks": [
            {
                "task_id": task.task_id,
                "case_unit_id": task.case_unit_id,
                "checklist": task.checklist_path.relative_to(task_root).as_posix(),
                "checklist_sha256": task.checklist_sha256,
                "evidence": task.evidence_dir.relative_to(task_root).as_posix(),
                "evidence_tree_sha256": task.evidence_tree_sha256,
                "native_label": (
                    task.native_label_path.relative_to(task_root).as_posix()
                    if task.native_label_path is not None
                    else None
                ),
                "native_label_sha256": task.native_label_sha256,
            }
            for task in tasks
        ],
        "outputs": outputs,
    }


def main() -> int:
    args = parse_args()
    positive_values = {
        "--max-parallel": args.max_parallel,
        "--max-attempts": args.max_attempts,
        "--codex-timeout-seconds": args.codex_timeout_seconds,
        "--max-run-attempts": args.max_run_attempts,
        "--max-input-files": args.max_input_files,
        "--max-input-bytes": args.max_input_bytes,
        "--max-single-file-bytes": args.max_single_file_bytes,
        "--min-free-bytes": args.min_free_bytes,
    }
    for option, value in positive_values.items():
        if value < 1:
            raise ScoreBatchError(f"{option} must be at least 1")

    task_root = args.task_root.resolve()
    output_root = args.output_root.resolve()
    state_root = args.state_root.resolve()
    if output_root == task_root or task_root in output_root.parents:
        raise ScoreBatchError("--output-root must be outside --task-root")
    if state_root == task_root or task_root in state_root.parents:
        raise ScoreBatchError("--state-root must be outside --task-root")

    tasks, tree_stats = discover_tasks(
        task_root,
        max_files=args.max_input_files,
        max_bytes=args.max_input_bytes,
        max_single_file_bytes=args.max_single_file_bytes,
    )
    free_bytes = shutil.disk_usage(task_root).free
    if free_bytes < args.min_free_bytes:
        raise ScoreBatchError(
            f"Insufficient free disk space: {free_bytes} < {args.min_free_bytes}"
        )

    plan = {
        "schema_version": "neurips_score_task_plan_v1",
        "generated_at": utc_now_iso(),
        "task_root": str(task_root),
        "output_root": str(output_root),
        "state_root": str(state_root),
        "input_stats": tree_stats,
        "free_bytes_at_preflight": free_bytes,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "service_tier": args.service_tier,
        "sandbox": args.sandbox,
        "max_parallel": args.max_parallel,
        "max_attempts": args.max_attempts,
        "codex_timeout_seconds": args.codex_timeout_seconds,
        "max_run_attempts": args.max_run_attempts,
        "score_prompt_path": str(PROMPT_PATH.resolve()),
        "score_prompt_sha256": sha256_file(PROMPT_PATH),
        "score_schema_path": str(SCHEMA_PATH.resolve()),
        "score_schema_sha256": sha256_file(SCHEMA_PATH),
        "task_count": len(tasks),
        "tasks": [task_record(task, output_root=output_root) for task in tasks],
    }
    if args.dry_run:
        print(json.dumps({"status": "dry_run_ok", **plan}, ensure_ascii=False))
        return 0

    source_codex_home = resolve_source_codex_home()
    for writable_root, option in (
        (output_root, "--output-root"),
        (state_root, "--state-root"),
    ):
        if writable_root.exists():
            if not writable_root.is_dir() or any(writable_root.iterdir()):
                raise ScoreBatchError(f"{option} must be an empty directory")
        else:
            writable_root.mkdir(parents=True, exist_ok=False)
    plan_path = state_root / "_task_plan.json"
    results_path = state_root / "_task_results.jsonl"
    summary_path = state_root / "_batch_summary.json"
    atomic_write_json(plan_path, plan)
    summary: dict[str, Any] = {
        "schema_version": "neurips_score_batch_summary_v1",
        "started_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
        "task_count": len(tasks),
        "completed": 0,
        "success": 0,
        "failed": 0,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "max_parallel": args.max_parallel,
        "plan_path": str(plan_path),
        "results_path": str(results_path),
        "output_root": str(output_root),
    }
    atomic_write_json(summary_path, summary)
    lock = threading.Lock()

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_parallel) as executor:
        futures = {
            executor.submit(
                run_task,
                task,
                output_root=output_root,
                source_codex_home=source_codex_home,
                model=args.model,
                reasoning_effort=args.reasoning_effort,
                sandbox=args.sandbox,
                service_tier=args.service_tier,
                max_attempts=args.max_attempts,
                codex_timeout_seconds=args.codex_timeout_seconds,
                max_run_attempts=args.max_run_attempts,
            ): task
            for task in tasks
        }
        for future in concurrent.futures.as_completed(futures):
            task = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "status": "failed",
                    "run_attempts": 0,
                    "duration_seconds": 0.0,
                    "returncode": None,
                    "timed_out": False,
                    "stdout_tail": "",
                    "stderr_tail": f"{type(exc).__name__}: {exc}",
                }
            row = {
                **task_record(task, output_root=output_root),
                **result,
                "completed_at": utc_now_iso(),
            }
            append_jsonl(results_path, row, lock)
            with lock:
                summary["completed"] += 1
                summary[result["status"]] += 1
                summary["updated_at"] = utc_now_iso()
                atomic_write_json(summary_path, summary)
            print(
                f"[{summary['completed']}/{summary['task_count']}] "
                f"{result['status']} {task.task_id}",
                flush=True,
            )

    transfer_manifest = build_transfer_manifest(
        task_root=task_root,
        output_root=output_root,
        tasks=tasks,
        model=args.model,
        reasoning_effort=args.reasoning_effort,
    )
    atomic_write_json(output_root / "_transfer_manifest.json", transfer_manifest)
    summary["transfer_manifest"] = str(output_root / "_transfer_manifest.json")
    summary["updated_at"] = utc_now_iso()
    atomic_write_json(summary_path, summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ScoreBatchError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
