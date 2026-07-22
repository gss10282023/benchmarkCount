#!/usr/bin/env python3
"""Retry the AW75 failed AndroidWorld score tasks in-place on the score VPS."""

from __future__ import annotations

import concurrent.futures
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


JOB_ROOT = Path("/srv/neurips-score/jobs/aw75_score_gpt54_high_c32_v2_20260720")
APP_ROOT = Path("/opt/neurips-draft/app")
PYTHON = Path("/opt/neurips-draft/venv/bin/python")
SCORE_SCRIPT = APP_ROOT / "neurips_ed_track_minimal/scripts/score_evidence_with_codex.py"
SOURCE_CODEX_HOME = Path("/srv/neurips-draft/home/.codex")
CODEX_HOME_ROOT = Path("/srv/neurips-score/runtime/codex_homes")
TMPDIR = Path("/srv/neurips-score/runtime/tmp")

FAILED_TASKS = [
    "full-androidworld-TurnOffWifiAndTurnOnBluetooth-agent_b",
    "full-androidworld-VlcCreatePlaylist-agent_c",
    "full-androidworld-VlcCreateTwoPlaylists-agent_b",
    "full-androidworld-VlcCreateTwoPlaylists-agent_c",
]


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def archive_failed_outputs(stamp: str, task_ids: list[str]) -> Path:
    archive_root = JOB_ROOT / "retry_archives" / f"failed_outputs_{stamp}"
    archive_root.mkdir(parents=True, exist_ok=False)
    for task_id in task_ids:
        source = JOB_ROOT / "results" / task_id
        target = archive_root / task_id
        if source.exists():
            shutil.move(str(source), str(target))
    return archive_root


def task_codex_home(task_id: str) -> Path:
    unique = f"aw75_retry_{task_id}_{os.getpid()}_{time.time_ns()}"
    return CODEX_HOME_ROOT / unique


def retry_task(task_id: str, retry_state: Path) -> dict[str, object]:
    task_dir = JOB_ROOT / "tasks" / task_id
    output_prefix = JOB_ROOT / "results" / task_id / "score"
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    codex_home = task_codex_home(task_id)
    started = time.time()
    command = [
        str(PYTHON),
        str(SCORE_SCRIPT),
        "--checklist",
        str(task_dir / "checklist.yaml"),
        "--evidence-dir",
        str(task_dir / "evidence"),
        "--out-prefix",
        str(output_prefix),
        "--model",
        "gpt-5.4",
        "--reasoning-effort",
        "high",
        "--max-attempts",
        "2",
        "--sandbox",
        "read-only",
        "--service-tier",
        "default",
        "--codex-timeout-seconds",
        "1800",
        "--native-label-path",
        str(task_dir / "native_label.json"),
    ]
    stdout = ""
    stderr = ""
    returncode = 1
    try:
        codex_home.mkdir(parents=True, exist_ok=False)
        shutil.copy2(SOURCE_CODEX_HOME / "auth.json", codex_home / "auth.json")
        os.chmod(codex_home, 0o700)
        os.chmod(codex_home / "auth.json", 0o600)
        env = dict(os.environ)
        env.update(
            {
                "HOME": "/srv/neurips-draft/home",
                "CODEX_HOME": str(codex_home),
                "SCORE_CODEX_HOME_ROOT": str(CODEX_HOME_ROOT),
                "TMPDIR": str(TMPDIR),
                "PYTHONPYCACHEPREFIX": "/srv/neurips-score/runtime/pycache",
                "PYTHONUNBUFFERED": "1",
                "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            }
        )
        process = subprocess.run(
            command,
            cwd=str(APP_ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=3900,
        )
        stdout = process.stdout or ""
        stderr = process.stderr or ""
        returncode = process.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        returncode = 124
    finally:
        shutil.rmtree(codex_home, ignore_errors=True)

    (retry_state / f"{task_id}.runner.stdout.log").write_text(stdout, encoding="utf-8")
    (retry_state / f"{task_id}.runner.stderr.log").write_text(stderr, encoding="utf-8")
    success = (
        returncode == 0
        and output_prefix.with_suffix(".json").is_file()
        and output_prefix.with_suffix(".yaml").is_file()
        and (output_prefix.parent / "score_manifest.json").is_file()
    )
    return {
        "task_id": task_id,
        "status": "success" if success else "failed",
        "returncode": returncode,
        "duration_seconds": round(time.time() - started, 3),
        "score_json": str(output_prefix.with_suffix(".json")),
        "stdout_tail": stdout[-2000:],
        "stderr_tail": stderr[-2000:],
    }


def main() -> int:
    stamp = utc_stamp()
    retry_state = JOB_ROOT / "retry_state" / f"retry_failed7_{stamp}"
    retry_state.mkdir(parents=True, exist_ok=False)
    task_ids = list(FAILED_TASKS)
    archive_root = archive_failed_outputs(stamp, task_ids)
    rows: list[dict[str, object]] = []
    if not task_ids:
        summary = {
            "schema_version": "aw75_failed_retry_v1",
            "started_at_stamp": stamp,
            "archive_root": str(archive_root),
            "retry_state": str(retry_state),
            "retry_selection": "explicit_latest_failed_4",
            "task_count": 0,
            "success": 0,
            "failed": 0,
            "model": "gpt-5.4",
            "reasoning_effort": "high",
            "service_tier": "default",
            "fast_mode": False,
            "max_parallel": 0,
            "rows": [],
        }
        write_json(retry_state / "retry_summary.json", summary)
        print(json.dumps(summary, ensure_ascii=False), flush=True)
        return 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(task_ids)) as executor:
        futures = {executor.submit(retry_task, task_id, retry_state): task_id for task_id in task_ids}
        for future in concurrent.futures.as_completed(futures):
            row = future.result()
            rows.append(row)
            print(f"{row['status']} {row['task_id']}", flush=True)
    rows.sort(key=lambda row: str(row["task_id"]))
    summary = {
        "schema_version": "aw75_failed_retry_v1",
        "started_at_stamp": stamp,
        "archive_root": str(archive_root),
        "retry_state": str(retry_state),
        "retry_selection": "explicit_latest_failed_4",
        "candidate_task_count": len(FAILED_TASKS),
        "task_count": len(rows),
        "success": sum(row["status"] == "success" for row in rows),
        "failed": sum(row["status"] != "success" for row in rows),
        "model": "gpt-5.4",
        "reasoning_effort": "high",
        "service_tier": "default",
        "fast_mode": False,
        "max_parallel": len(task_ids),
        "rows": rows,
    }
    write_json(retry_state / "retry_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
