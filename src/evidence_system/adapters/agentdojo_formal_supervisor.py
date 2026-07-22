"""Detached, content-blind process-group supervisor for formal AgentDojo jobs.

The controller may retry read-only ``status`` calls, but a session-specific
supervisor claim makes worker launch create-once.  Worker stdout/stderr never
cross SSH and every signal is guarded by boot, PID start-time, PGID, and SID.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence


LAUNCH_INTENT = "formal_job_launch_intent.json"
SPEC = "formal_supervisor_spec.json"
CLAIM = "formal_supervisor_claim.json"
STATE = "formal_supervisor_state.json"
EXIT = "formal_supervisor_exit.json"
STDOUT = "sealed_worker.stdout.log"
STDERR = "sealed_worker.stderr.log"
MODULE_NAME = "evidence_system.adapters.agentdojo_formal_supervisor"
_DIGEST_FIELDS = ("job_binding_sha256", "stage_authorization_sha256")
BOOTSTRAP_TIMEOUT_SECONDS = 30


class SupervisorError(RuntimeError):
    pass


class BootChanged(SupervisorError):
    pass


class ProcessIdentityConflict(SupervisorError):
    pass


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    launch = commands.add_parser("launch")
    launch.add_argument("--attempt-root", type=Path, required=True)
    launch.add_argument("--stage-id", required=True)
    launch.add_argument("--session-id", required=True)
    launch.add_argument("--job-binding-sha256", required=True)
    launch.add_argument("--stage-authorization-sha256", required=True)
    launch.add_argument("--timeout-seconds", type=int, required=True)
    launch.add_argument("--kill-grace-seconds", type=int, required=True)
    status = commands.add_parser("status")
    status.add_argument("--attempt-root", type=Path, required=True)
    status.add_argument("--session-id", required=True)
    recover = commands.add_parser("recover-reboot")
    recover.add_argument("--attempt-root", type=Path, required=True)
    recover.add_argument("--session-id", required=True)
    supervise = commands.add_parser("supervise")
    supervise.add_argument("--spec", type=Path, required=True)
    worker_guard = commands.add_parser("worker-guard")
    worker_guard.add_argument("--spec", type=Path, required=True)
    worker_guard.add_argument("--claim", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.mode == "launch":
            result = launch_once(
                attempt_root=args.attempt_root,
                stage_id=args.stage_id,
                session_id=args.session_id,
                job_binding_sha256=args.job_binding_sha256,
                authorization_sha256=args.stage_authorization_sha256,
                timeout_seconds=args.timeout_seconds,
                kill_grace_seconds=args.kill_grace_seconds,
                command=sys.stdin.read(),
            )
        elif args.mode == "status":
            result = status_only(args.attempt_root, session_id=args.session_id)
        elif args.mode == "recover-reboot":
            result = recover_after_reboot(
                args.attempt_root, session_id=args.session_id
            )
        elif args.mode == "supervise":
            return supervise_once(args.spec)
        else:
            return worker_guard_once(args.spec, args.claim)
    except Exception as exc:
        result = {
            "schema_version": "agentdojo_formal_supervisor_result/v1",
            "status": "error",
            "error_type": type(exc).__name__,
            "error_sha256": _sha256_json(
                {"type": type(exc).__name__, "message": str(exc)}
            ),
            "blind_only": True,
        }
        print(json.dumps(result, separators=(",", ":"), sort_keys=True))
        return 1
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


def launch_once(
    *,
    attempt_root: Path,
    stage_id: str,
    session_id: str,
    job_binding_sha256: str,
    authorization_sha256: str,
    timeout_seconds: int,
    kill_grace_seconds: int,
    command: str,
) -> dict[str, Any]:
    root = _regular_directory(attempt_root, "formal attempt root")
    if not stage_id or not session_id.startswith("session-"):
        raise SupervisorError("formal supervisor stage/session identity is invalid")
    _digest(job_binding_sha256, "job binding")
    _digest(authorization_sha256, "stage authorization")
    if not 1 <= timeout_seconds <= 86_400 or not 1 <= kill_grace_seconds <= 300:
        raise SupervisorError("formal supervisor timeout policy is invalid")
    if not command or "\x00" in command:
        raise SupervisorError("formal supervisor worker command is invalid")
    names = {path.name for path in root.iterdir()}
    allowed = {LAUNCH_INTENT, SPEC, CLAIM, STATE, EXIT, STDOUT, STDERR}
    if LAUNCH_INTENT not in names or not names <= allowed:
        raise SupervisorError("formal attempt pre-launch field set differs")
    _regular_file(root / LAUNCH_INTENT, "formal launch intent")
    spec = {
        "schema_version": "agentdojo_formal_supervisor_spec/v1",
        "stage_id": stage_id,
        "session_id": session_id,
        "job_binding_sha256": job_binding_sha256,
        "stage_authorization_sha256": authorization_sha256,
        "formal_wall_clock_timeout_seconds": timeout_seconds,
        "kill_grace_seconds": kill_grace_seconds,
        "command_sha256": hashlib.sha256(command.encode("utf-8")).hexdigest(),
        "command": command,
    }
    spec_path = root / SPEC
    _write_identical_or_new(spec_path, spec)
    claim_path = root / CLAIM
    if not claim_path.exists() and not claim_path.is_symlink():
        subprocess.Popen(
            [sys.executable, "-m", MODULE_NAME, "supervise", "--spec", str(spec_path)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
    deadline = time.monotonic() + 10.0
    while time.monotonic() < deadline:
        if (root / STATE).is_file() or (root / EXIT).is_file():
            return status_only(root, session_id=session_id)
        if claim_path.exists() or claim_path.is_symlink():
            time.sleep(0.05)
        else:
            time.sleep(0.01)
    if claim_path.exists() or claim_path.is_symlink():
        return status_only(root, session_id=session_id)
    raise SupervisorError("formal supervisor did not establish a create-once claim")


def supervise_once(spec_path: Path) -> int:
    spec = _verify_spec(spec_path)
    root = spec_path.parent
    session_id = str(spec["session_id"])
    boot_id = _boot_id()
    supervisor_pid = os.getpid()
    supervisor_start, supervisor_pgid, supervisor_sid = _proc_identity(supervisor_pid)
    claimed_boottime = _boottime()
    claim = {
        "schema_version": "agentdojo_formal_supervisor_claim/v2",
        "stage_id": spec["stage_id"],
        "session_id": session_id,
        "job_binding_sha256": spec["job_binding_sha256"],
        "stage_authorization_sha256": spec["stage_authorization_sha256"],
        "supervisor_pid": supervisor_pid,
        "supervisor_pgid": supervisor_pgid,
        "supervisor_session_id": supervisor_sid,
        "supervisor_starttime_ticks": supervisor_start,
        "host_boot_id": boot_id,
        "spec_sha256": _sha256_file(spec_path),
        "claimed_boottime_seconds": claimed_boottime,
        "bootstrap_deadline_boottime_seconds": (
            claimed_boottime + BOOTSTRAP_TIMEOUT_SECONDS
        ),
    }
    try:
        _write_exclusive_json(root / CLAIM, claim)
    except FileExistsError:
        return 73
    stdout_fd = _open_exclusive_stream(root / STDOUT)
    try:
        stderr_fd = _open_exclusive_stream(root / STDERR)
    except Exception:
        os.close(stdout_fd)
        raise
    state_path = root / STATE
    worker: subprocess.Popen[bytes] | None = None
    state: dict[str, Any] | None = None
    try:
        worker = subprocess.Popen(
            [
                sys.executable,
                "-m",
                MODULE_NAME,
                "worker-guard",
                "--spec",
                str(spec_path),
                "--claim",
                str(root / CLAIM),
            ],
            stdin=subprocess.DEVNULL,
            stdout=stdout_fd,
            stderr=stderr_fd,
            start_new_session=True,
            close_fds=True,
        )
        bootstrap_deadline = float(claim["bootstrap_deadline_boottime_seconds"])
        while _boottime() < bootstrap_deadline and not state_path.exists():
            if worker.poll() is not None:
                break
            time.sleep(0.01)
        if not state_path.exists():
            if worker.poll() is None:
                worker.kill()
                worker.wait(timeout=10)
            _write_bootstrap_terminal_exit(
                root,
                claim=claim,
                spec=spec,
                outcome="worker_guard_failed",
                exit_code=int(worker.returncode or 125),
            )
            return 0
        state = _verify_state(state_path, expected_session_id=session_id)
        if int(state["worker_pid"]) != int(worker.pid):
            raise SupervisorError("formal worker guard PID differs from state")
        return _watch_worker(worker, root=root, state=state)
    except BaseException:
        if worker is not None and state is not None:
            try:
                if _safe_group_alive(state):
                    _signal_group(state, signal.SIGKILL)
            except Exception:
                pass
        raise
    finally:
        os.close(stdout_fd)
        os.close(stderr_fd)


def worker_guard_once(spec_path: Path, claim_path: Path) -> int:
    """Durably publish worker identity before executing any benchmark command."""

    spec = _verify_spec(spec_path)
    claim = _verify_claim(
        claim_path,
        expected_session_id=str(spec["session_id"]),
        spec_path=spec_path,
    )
    pid = os.getpid()
    worker_start, worker_pgid, worker_sid = _proc_identity(pid)
    if worker_pgid != pid or worker_sid != pid:
        raise SupervisorError("formal worker guard lacks a dedicated session/PGID")
    launched_boottime = _boottime()
    state = {
        "schema_version": "agentdojo_formal_supervisor_state/v2",
        "stage_id": spec["stage_id"],
        "session_id": spec["session_id"],
        "job_binding_sha256": spec["job_binding_sha256"],
        "stage_authorization_sha256": spec["stage_authorization_sha256"],
        "spec_sha256": _sha256_file(spec_path),
        "claim_sha256": _sha256_file(claim_path),
        "supervisor_pid": claim["supervisor_pid"],
        "supervisor_pgid": claim["supervisor_pgid"],
        "supervisor_session_id": claim["supervisor_session_id"],
        "supervisor_starttime_ticks": claim["supervisor_starttime_ticks"],
        "worker_pid": pid,
        "worker_pgid": worker_pgid,
        "worker_session_id": worker_sid,
        "worker_starttime_ticks": worker_start,
        "launched_host_boot_id": claim["host_boot_id"],
        "launched_boottime_seconds": launched_boottime,
        "deadline_boottime_seconds": (
            launched_boottime + int(spec["formal_wall_clock_timeout_seconds"])
        ),
        "formal_wall_clock_timeout_seconds": int(
            spec["formal_wall_clock_timeout_seconds"]
        ),
        "kill_grace_seconds": int(spec["kill_grace_seconds"]),
    }
    _write_exclusive_json(spec_path.parent / STATE, state)
    os.execv("/bin/bash", ["/bin/bash", "-lc", str(spec["command"])])
    raise AssertionError("unreachable worker exec")


def _watch_worker(
    worker: subprocess.Popen[bytes], *, root: Path, state: Mapping[str, Any]
) -> int:
    deadline = float(state["deadline_boottime_seconds"])
    grace = int(state["kill_grace_seconds"])
    timed_out = False
    term_sent = False
    kill_sent = False
    outcome = "worker_exited"
    returncode: int | None = None
    while True:
        returncode = worker.poll()
        alive = _safe_group_alive(state)
        if returncode is not None and not alive:
            break
        if returncode is not None and alive:
            outcome = "orphaned_process_group"
            term_sent, kill_sent = _terminate_group(state, grace_seconds=grace)
            break
        if _boottime() >= deadline:
            timed_out = True
            outcome = "timeout"
            term_sent, kill_sent = _terminate_group(state, grace_seconds=grace)
            returncode = worker.poll()
            break
        time.sleep(0.2)
    group_gone = not _safe_group_alive(state)
    if not group_gone:
        outcome = "process_group_not_gone"
    if returncode is None:
        try:
            returncode = worker.wait(timeout=5)
        except subprocess.TimeoutExpired:
            returncode = 124 if timed_out else 125
    exit_code = int(returncode)
    if timed_out and exit_code == 0:
        exit_code = 124
    receipt = {
        "schema_version": "agentdojo_formal_supervisor_exit/v2",
        "stage_id": state["stage_id"],
        "session_id": state["session_id"],
        "job_binding_sha256": state["job_binding_sha256"],
        "stage_authorization_sha256": state["stage_authorization_sha256"],
        "spec_sha256": state["spec_sha256"],
        "claim_sha256": state["claim_sha256"],
        "state_sha256": _sha256_json(dict(state)),
        "supervisor_pid": state["supervisor_pid"],
        "supervisor_pgid": state["supervisor_pgid"],
        "supervisor_session_id": state["supervisor_session_id"],
        "supervisor_starttime_ticks": state["supervisor_starttime_ticks"],
        "worker_pid": state["worker_pid"],
        "worker_pgid": state["worker_pgid"],
        "worker_session_id": state["worker_session_id"],
        "worker_starttime_ticks": state["worker_starttime_ticks"],
        "launched_host_boot_id": state["launched_host_boot_id"],
        "finished_host_boot_id": _boot_id(),
        "finished_boottime_seconds": _boottime(),
        "exit_code": exit_code,
        "outcome": outcome,
        "timed_out": timed_out,
        "term_sent": term_sent,
        "kill_sent": kill_sent,
        "group_gone": group_gone,
        "bootstrap_terminal": False,
    }
    _write_exclusive_json(root / EXIT, receipt)
    return 0


def _terminate_group(
    state: Mapping[str, Any], *, grace_seconds: int
) -> tuple[bool, bool]:
    if not _safe_group_alive(state):
        return False, False
    _signal_group(state, signal.SIGTERM)
    term_sent = True
    grace_deadline = _boottime() + grace_seconds
    while _boottime() < grace_deadline:
        if not _safe_group_alive(state):
            return term_sent, False
        time.sleep(0.1)
    if _safe_group_alive(state):
        _signal_group(state, signal.SIGKILL)
        kill_deadline = _boottime() + 10.0
        while _boottime() < kill_deadline and _safe_group_alive(state):
            time.sleep(0.05)
        return term_sent, True
    return term_sent, False


def status_only(attempt_root: Path, *, session_id: str) -> dict[str, Any]:
    root = _regular_directory(attempt_root, "formal attempt root")
    exit_path = root / EXIT
    state_path = root / STATE
    claim_path = root / CLAIM
    if exit_path.exists() or exit_path.is_symlink():
        receipt = _verify_exit(exit_path, expected_session_id=session_id)
        return {
            **_result("exited", session_id=session_id),
            "exit_code": receipt["exit_code"],
            "outcome": receipt["outcome"],
            "timed_out": receipt["timed_out"],
            "group_gone": receipt["group_gone"],
        }
    if state_path.exists() or state_path.is_symlink():
        state = _verify_state(state_path, expected_session_id=session_id)
        if state["launched_host_boot_id"] != _boot_id():
            return _result("boot_changed", session_id=session_id)
        try:
            alive = _safe_group_alive(state)
        except ProcessIdentityConflict:
            return _result("identity_conflict", session_id=session_id)
        return {
            **_result("running" if alive else "exit_receipt_missing", session_id=session_id),
            "deadline_boottime_seconds": state["deadline_boottime_seconds"],
        }
    if claim_path.exists() or claim_path.is_symlink():
        return _reconcile_bootstrap_claim(
            root, session_id=session_id, state_path=state_path
        )
    if (root / SPEC).is_file():
        return _result("launch_pending", session_id=session_id)
    return _result("absent", session_id=session_id)


def recover_after_reboot(
    attempt_root: Path, *, session_id: str
) -> dict[str, Any]:
    root = _regular_directory(attempt_root, "formal attempt root")
    if (root / EXIT).exists() or (root / EXIT).is_symlink():
        return status_only(root, session_id=session_id)
    if not (root / STATE).exists() and not (root / STATE).is_symlink():
        claim = _verify_claim(
            root / CLAIM,
            expected_session_id=session_id,
            spec_path=root / SPEC,
        )
        if claim["host_boot_id"] == _boot_id():
            raise SupervisorError("reboot recovery requires a different host boot ID")
        _write_bootstrap_terminal_exit(
            root,
            claim=claim,
            spec=_verify_spec(root / SPEC),
            outcome="boot_changed_before_state",
            exit_code=125,
        )
        return status_only(root, session_id=session_id)
    state = _verify_state(root / STATE, expected_session_id=session_id)
    if state["launched_host_boot_id"] == _boot_id():
        raise SupervisorError("reboot recovery requires a different host boot ID")
    receipt = {
        "schema_version": "agentdojo_formal_supervisor_exit/v2",
        "stage_id": state["stage_id"],
        "session_id": state["session_id"],
        "job_binding_sha256": state["job_binding_sha256"],
        "stage_authorization_sha256": state["stage_authorization_sha256"],
        "spec_sha256": state["spec_sha256"],
        "claim_sha256": state["claim_sha256"],
        "state_sha256": _sha256_json(dict(state)),
        "supervisor_pid": state["supervisor_pid"],
        "supervisor_pgid": state["supervisor_pgid"],
        "supervisor_session_id": state["supervisor_session_id"],
        "supervisor_starttime_ticks": state["supervisor_starttime_ticks"],
        "worker_pid": state["worker_pid"],
        "worker_pgid": state["worker_pgid"],
        "worker_session_id": state["worker_session_id"],
        "worker_starttime_ticks": state["worker_starttime_ticks"],
        "launched_host_boot_id": state["launched_host_boot_id"],
        "finished_host_boot_id": _boot_id(),
        "finished_boottime_seconds": _boottime(),
        "exit_code": 125,
        "outcome": "boot_changed",
        "timed_out": False,
        "term_sent": False,
        "kill_sent": False,
        "group_gone": True,
        "bootstrap_terminal": False,
    }
    _write_exclusive_json(root / EXIT, receipt)
    return status_only(root, session_id=session_id)


def _safe_group_alive(state: Mapping[str, Any]) -> bool:
    if state["launched_host_boot_id"] != _boot_id():
        raise BootChanged("formal worker host boot ID changed")
    pid = int(state["worker_pid"])
    pgid = int(state["worker_pgid"])
    sid = int(state["worker_session_id"])
    expected_start = int(state["worker_starttime_ticks"])
    leader_path = Path(f"/proc/{pid}/stat")
    if leader_path.exists():
        start, observed_pgid, observed_sid = _proc_identity(pid)
        if (
            start != expected_start
            or observed_pgid != pgid
            or observed_sid != sid
        ):
            raise ProcessIdentityConflict("formal worker PID/PGID/SID was reused")
    members = _group_members(pgid=pgid, sid=sid)
    if not members:
        return False
    if leader_path.exists():
        return True
    if any(member_start < expected_start for _member_pid, member_start in members):
        raise ProcessIdentityConflict("formal worker group has an older process member")
    return True


def _signal_group(state: Mapping[str, Any], signal_number: int) -> None:
    if not _safe_group_alive(state):
        return
    os.killpg(int(state["worker_pgid"]), signal_number)


def _group_members(*, pgid: int, sid: int) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    proc_root = Path("/proc")
    if not proc_root.is_dir():
        raise SupervisorError("formal supervisor requires Linux /proc")
    for candidate in proc_root.iterdir():
        if not candidate.name.isdigit():
            continue
        try:
            start, observed_pgid, observed_sid = _proc_identity(int(candidate.name))
        except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError):
            continue
        if observed_pgid == pgid and observed_sid == sid:
            result.append((int(candidate.name), start))
    return result


def _verify_claim(
    path: Path, *, expected_session_id: str, spec_path: Path
) -> dict[str, Any]:
    payload = _load_object(_regular_file(path, "supervisor claim"))
    expected = {
        "schema_version", "stage_id", "session_id", "job_binding_sha256",
        "stage_authorization_sha256", "supervisor_pid", "supervisor_pgid",
        "supervisor_session_id", "supervisor_starttime_ticks", "host_boot_id",
        "spec_sha256", "claimed_boottime_seconds",
        "bootstrap_deadline_boottime_seconds",
    }
    if set(payload) != expected or payload.get("schema_version") != (
        "agentdojo_formal_supervisor_claim/v2"
    ):
        raise SupervisorError("formal supervisor claim fields differ")
    spec = _verify_spec(spec_path)
    if payload.get("session_id") != expected_session_id:
        raise SupervisorError("formal supervisor claim session differs")
    for field in _DIGEST_FIELDS:
        _digest(str(payload.get(field) or ""), f"claim {field}")
    _digest(str(payload.get("spec_sha256") or ""), "claim spec_sha256")
    for field in ("stage_id", "session_id", *_DIGEST_FIELDS):
        if payload.get(field) != spec.get(field):
            raise SupervisorError(f"formal supervisor claim {field} differs from spec")
    if payload.get("spec_sha256") != _sha256_file(spec_path):
        raise SupervisorError("formal supervisor claim spec hash is stale")
    integers = (
        "supervisor_pid", "supervisor_pgid", "supervisor_session_id",
        "supervisor_starttime_ticks",
    )
    if any(
        not isinstance(payload.get(field), int)
        or isinstance(payload.get(field), bool)
        or int(payload[field]) <= 0
        for field in integers
    ):
        raise SupervisorError("formal supervisor claim process identity is invalid")
    if not (
        payload["supervisor_pid"] == payload["supervisor_pgid"]
        == payload["supervisor_session_id"]
    ):
        raise SupervisorError("formal supervisor claim lacks a dedicated session/PGID")
    claimed = payload.get("claimed_boottime_seconds")
    deadline = payload.get("bootstrap_deadline_boottime_seconds")
    if (
        not isinstance(claimed, (int, float))
        or isinstance(claimed, bool)
        or not isinstance(deadline, (int, float))
        or isinstance(deadline, bool)
        or float(claimed) < 0
        or float(deadline) != float(claimed) + BOOTSTRAP_TIMEOUT_SECONDS
    ):
        raise SupervisorError("formal supervisor claim bootstrap deadline is invalid")
    if not isinstance(payload.get("host_boot_id"), str) or len(
        str(payload["host_boot_id"])
    ) != 36:
        raise SupervisorError("formal supervisor claim host boot ID is invalid")
    return payload


def _claim_supervisor_alive(claim: Mapping[str, Any]) -> bool:
    if claim["host_boot_id"] != _boot_id():
        raise BootChanged("formal supervisor claim host boot ID changed")
    pid = int(claim["supervisor_pid"])
    if not Path(f"/proc/{pid}/stat").exists():
        return False
    try:
        start, pgid, sid = _proc_identity(pid)
    except (FileNotFoundError, ProcessLookupError):
        return False
    if (
        start != int(claim["supervisor_starttime_ticks"])
        or pgid != int(claim["supervisor_pgid"])
        or sid != int(claim["supervisor_session_id"])
    ):
        raise ProcessIdentityConflict("formal supervisor claim PID/PGID/SID was reused")
    return True


def _reconcile_bootstrap_claim(
    root: Path, *, session_id: str, state_path: Path
) -> dict[str, Any]:
    spec_path = root / SPEC
    claim = _verify_claim(
        root / CLAIM,
        expected_session_id=session_id,
        spec_path=spec_path,
    )
    if claim["host_boot_id"] != _boot_id():
        _write_bootstrap_terminal_exit(
            root,
            claim=claim,
            spec=_verify_spec(spec_path),
            outcome="boot_changed_before_state",
            exit_code=125,
        )
        return status_only(root, session_id=session_id)
    alive = False
    identity_conflict = False
    try:
        alive = _claim_supervisor_alive(claim)
    except ProcessIdentityConflict:
        identity_conflict = True
    if _boottime() < float(claim["bootstrap_deadline_boottime_seconds"]):
        return {
            **_result("bootstrapping", session_id=session_id),
            "deadline_boottime_seconds": claim[
                "bootstrap_deadline_boottime_seconds"
            ],
        }
    # This session is never relaunched.  Give a concurrently starting guard
    # one final chance to publish its durable state before terminalization.
    time.sleep(0.05)
    if state_path.exists() or state_path.is_symlink():
        return status_only(root, session_id=session_id)
    term_sent = False
    kill_sent = False
    if alive and not identity_conflict:
        os.killpg(int(claim["supervisor_pgid"]), signal.SIGTERM)
        term_sent = True
        deadline = _boottime() + 2.0
        while _boottime() < deadline and _claim_supervisor_alive(claim):
            time.sleep(0.05)
        if _claim_supervisor_alive(claim):
            os.killpg(int(claim["supervisor_pgid"]), signal.SIGKILL)
            kill_sent = True
            deadline = _boottime() + 5.0
            while _boottime() < deadline and _claim_supervisor_alive(claim):
                time.sleep(0.05)
    if state_path.exists() or state_path.is_symlink():
        return status_only(root, session_id=session_id)
    try:
        still_alive = _claim_supervisor_alive(claim)
    except ProcessIdentityConflict:
        still_alive = False
        identity_conflict = True
    if still_alive:
        raise SupervisorError("stale bootstrap supervisor could not be terminated")
    _write_bootstrap_terminal_exit(
        root,
        claim=claim,
        spec=_verify_spec(spec_path),
        outcome=(
            "supervisor_identity_conflict_before_state"
            if identity_conflict
            else "bootstrap_deadline_expired"
        ),
        exit_code=125,
        term_sent=term_sent,
        kill_sent=kill_sent,
    )
    return status_only(root, session_id=session_id)


def _write_bootstrap_terminal_exit(
    root: Path,
    *,
    claim: Mapping[str, Any],
    spec: Mapping[str, Any],
    outcome: str,
    exit_code: int,
    term_sent: bool = False,
    kill_sent: bool = False,
) -> None:
    if (root / STATE).exists() or (root / STATE).is_symlink():
        raise SupervisorError("bootstrap terminal exit cannot replace a durable state")
    if claim["host_boot_id"] == _boot_id():
        try:
            if _claim_supervisor_alive(claim) and int(
                claim["supervisor_pid"]
            ) != os.getpid():
                raise SupervisorError(
                    "bootstrap terminal exit requires the claimed supervisor to be gone"
                )
        except ProcessIdentityConflict:
            pass
    receipt = {
        "schema_version": "agentdojo_formal_supervisor_exit/v2",
        "stage_id": spec["stage_id"],
        "session_id": spec["session_id"],
        "job_binding_sha256": spec["job_binding_sha256"],
        "stage_authorization_sha256": spec["stage_authorization_sha256"],
        "spec_sha256": _sha256_file(root / SPEC),
        "claim_sha256": _sha256_file(root / CLAIM),
        "state_sha256": None,
        "supervisor_pid": claim["supervisor_pid"],
        "supervisor_pgid": claim["supervisor_pgid"],
        "supervisor_session_id": claim["supervisor_session_id"],
        "supervisor_starttime_ticks": claim["supervisor_starttime_ticks"],
        "worker_pid": None,
        "worker_pgid": None,
        "worker_session_id": None,
        "worker_starttime_ticks": None,
        "launched_host_boot_id": claim["host_boot_id"],
        "finished_host_boot_id": _boot_id(),
        "finished_boottime_seconds": _boottime(),
        "exit_code": int(exit_code),
        "outcome": outcome,
        "timed_out": outcome == "bootstrap_deadline_expired",
        "term_sent": bool(term_sent),
        "kill_sent": bool(kill_sent),
        "group_gone": True,
        "bootstrap_terminal": True,
    }
    _write_exclusive_json(root / EXIT, receipt)


def _verify_spec(path: Path) -> dict[str, Any]:
    payload = _load_object(_regular_file(path, "supervisor spec"))
    expected = {
        "schema_version", "stage_id", "session_id", "job_binding_sha256",
        "stage_authorization_sha256", "formal_wall_clock_timeout_seconds",
        "kill_grace_seconds", "command_sha256", "command",
    }
    if set(payload) != expected or payload.get("schema_version") != (
        "agentdojo_formal_supervisor_spec/v1"
    ):
        raise SupervisorError("formal supervisor spec fields differ")
    for field in _DIGEST_FIELDS:
        _digest(str(payload[field]), field)
    command = str(payload["command"])
    _digest(str(payload.get("command_sha256") or ""), "command_sha256")
    if (
        not payload.get("stage_id")
        or not str(payload.get("session_id") or "").startswith("session-")
        or not command
        or "\x00" in command
        or hashlib.sha256(command.encode()).hexdigest() != payload["command_sha256"]
    ):
        raise SupervisorError("formal supervisor command hash differs")
    if (
        not isinstance(payload.get("formal_wall_clock_timeout_seconds"), int)
        or isinstance(payload.get("formal_wall_clock_timeout_seconds"), bool)
        or not 1 <= int(payload["formal_wall_clock_timeout_seconds"]) <= 86_400
        or not isinstance(payload.get("kill_grace_seconds"), int)
        or isinstance(payload.get("kill_grace_seconds"), bool)
        or not 1 <= int(payload["kill_grace_seconds"]) <= 300
    ):
        raise SupervisorError("formal supervisor spec timeout policy is invalid")
    return payload


def _verify_state(path: Path, *, expected_session_id: str) -> dict[str, Any]:
    payload = _load_object(_regular_file(path, "supervisor state"))
    expected = {
        "schema_version", "stage_id", "session_id", "job_binding_sha256",
        "stage_authorization_sha256", "spec_sha256", "claim_sha256",
        "supervisor_pid", "supervisor_pgid", "supervisor_session_id",
        "supervisor_starttime_ticks", "worker_pid",
        "worker_pgid", "worker_session_id", "worker_starttime_ticks",
        "launched_host_boot_id", "launched_boottime_seconds",
        "deadline_boottime_seconds", "formal_wall_clock_timeout_seconds",
        "kill_grace_seconds",
    }
    if set(payload) != expected or payload.get("schema_version") != (
        "agentdojo_formal_supervisor_state/v2"
    ):
        raise SupervisorError("formal supervisor state fields differ")
    root = path.parent
    spec = _verify_spec(root / SPEC)
    claim = _verify_claim(
        root / CLAIM,
        expected_session_id=expected_session_id,
        spec_path=root / SPEC,
    )
    for field in ("stage_id", "session_id", *_DIGEST_FIELDS):
        if payload.get(field) != spec.get(field) or payload.get(field) != claim.get(field):
            raise SupervisorError(f"formal supervisor state {field} binding differs")
    for field in ("spec_sha256", "claim_sha256", *_DIGEST_FIELDS):
        _digest(str(payload.get(field) or ""), f"state {field}")
    if payload.get("spec_sha256") != _sha256_file(root / SPEC) or payload.get(
        "claim_sha256"
    ) != _sha256_file(root / CLAIM):
        raise SupervisorError("formal supervisor state control hash is stale")
    supervisor_fields = (
        "supervisor_pid", "supervisor_pgid", "supervisor_session_id",
        "supervisor_starttime_ticks",
    )
    if any(payload.get(field) != claim.get(field) for field in supervisor_fields):
        raise SupervisorError("formal supervisor state supervisor identity differs")
    process_fields = (*supervisor_fields, "worker_pid", "worker_pgid", "worker_session_id", "worker_starttime_ticks")
    if any(
        not isinstance(payload.get(field), int)
        or isinstance(payload.get(field), bool)
        or int(payload[field]) <= 0
        for field in process_fields
    ):
        raise SupervisorError("formal supervisor state process identity is invalid")
    if payload["worker_pid"] != payload["worker_pgid"] or payload["worker_pid"] != payload["worker_session_id"]:
        raise SupervisorError("formal supervisor state worker session/PGID differs")
    if payload.get("launched_host_boot_id") != claim.get("host_boot_id"):
        raise SupervisorError("formal supervisor state boot binding differs")
    launched = payload.get("launched_boottime_seconds")
    deadline = payload.get("deadline_boottime_seconds")
    timeout = payload.get("formal_wall_clock_timeout_seconds")
    grace = payload.get("kill_grace_seconds")
    if (
        not isinstance(launched, (int, float)) or isinstance(launched, bool)
        or not isinstance(deadline, (int, float)) or isinstance(deadline, bool)
        or not isinstance(timeout, int) or isinstance(timeout, bool)
        or not isinstance(grace, int) or isinstance(grace, bool)
        or float(launched) < 0
        or float(deadline) != float(launched) + int(timeout)
        or timeout != spec["formal_wall_clock_timeout_seconds"]
        or grace != spec["kill_grace_seconds"]
    ):
        raise SupervisorError("formal supervisor state watchdog policy is invalid")
    return payload


def _verify_exit(path: Path, *, expected_session_id: str) -> dict[str, Any]:
    payload = _load_object(_regular_file(path, "supervisor exit receipt"))
    expected = {
        "schema_version", "stage_id", "session_id", "job_binding_sha256",
        "stage_authorization_sha256", "spec_sha256", "claim_sha256",
        "state_sha256", "supervisor_pid", "supervisor_pgid",
        "supervisor_session_id", "supervisor_starttime_ticks", "worker_pid",
        "worker_pgid", "worker_session_id", "worker_starttime_ticks",
        "launched_host_boot_id", "finished_host_boot_id",
        "finished_boottime_seconds", "exit_code", "outcome", "timed_out",
        "term_sent", "kill_sent", "group_gone", "bootstrap_terminal",
    }
    if set(payload) != expected or payload.get("schema_version") != (
        "agentdojo_formal_supervisor_exit/v2"
    ):
        raise SupervisorError("formal supervisor exit fields differ")
    root = path.parent
    spec = _verify_spec(root / SPEC)
    claim = _verify_claim(
        root / CLAIM,
        expected_session_id=expected_session_id,
        spec_path=root / SPEC,
    )
    for field in ("stage_id", "session_id", *_DIGEST_FIELDS):
        if payload.get(field) != spec.get(field) or payload.get(field) != claim.get(field):
            raise SupervisorError(f"formal supervisor exit {field} binding differs")
    for field in ("spec_sha256", "claim_sha256", *_DIGEST_FIELDS):
        _digest(str(payload.get(field) or ""), f"exit {field}")
    if payload.get("spec_sha256") != _sha256_file(root / SPEC) or payload.get(
        "claim_sha256"
    ) != _sha256_file(root / CLAIM):
        raise SupervisorError("formal supervisor exit control hash is stale")
    if not isinstance(payload.get("exit_code"), int) or isinstance(
        payload.get("exit_code"), bool
    ):
        raise SupervisorError("formal supervisor exit code is invalid")
    for field in (
        "timed_out", "term_sent", "kill_sent", "group_gone", "bootstrap_terminal"
    ):
        if not isinstance(payload.get(field), bool):
            raise SupervisorError(f"formal supervisor exit {field} is invalid")
    if payload.get("group_gone") is not True:
        raise SupervisorError("formal supervisor exit does not prove the process group gone")
    if not isinstance(payload.get("finished_boottime_seconds"), (int, float)) or isinstance(
        payload.get("finished_boottime_seconds"), bool
    ):
        raise SupervisorError("formal supervisor exit boottime is invalid")
    supervisor_fields = (
        "supervisor_pid", "supervisor_pgid", "supervisor_session_id",
        "supervisor_starttime_ticks",
    )
    if any(payload.get(field) != claim.get(field) for field in supervisor_fields):
        raise SupervisorError("formal supervisor exit supervisor identity differs")
    if payload.get("launched_host_boot_id") != claim.get("host_boot_id"):
        raise SupervisorError("formal supervisor exit launch boot binding differs")
    if payload["bootstrap_terminal"]:
        if (root / STATE).exists() or (root / STATE).is_symlink() or any(
            payload.get(field) is not None
            for field in (
                "state_sha256", "worker_pid", "worker_pgid",
                "worker_session_id", "worker_starttime_ticks",
            )
        ):
            raise SupervisorError("bootstrap terminal exit unexpectedly binds worker state")
        if payload.get("outcome") not in {
            "worker_guard_failed", "bootstrap_deadline_expired",
            "supervisor_identity_conflict_before_state", "boot_changed_before_state",
        }:
            raise SupervisorError("bootstrap terminal exit outcome is invalid")
    else:
        state = _verify_state(root / STATE, expected_session_id=expected_session_id)
        _digest(str(payload.get("state_sha256") or ""), "exit state_sha256")
        if payload.get("state_sha256") != _sha256_json(state):
            raise SupervisorError("formal supervisor exit state hash is stale")
        for field in (
            "worker_pid", "worker_pgid", "worker_session_id",
            "worker_starttime_ticks",
        ):
            if payload.get(field) != state.get(field):
                raise SupervisorError(f"formal supervisor exit {field} differs from state")
    if payload.get("exit_code") == 0 and (
        payload.get("outcome") != "worker_exited" or payload.get("timed_out") is not False
    ):
        raise SupervisorError("successful supervisor exit outcome is inconsistent")
    if payload.get("outcome") == "timeout" and payload.get("timed_out") is not True:
        raise SupervisorError("timed-out supervisor exit receipt is inconsistent")
    return payload


def _proc_identity(pid: int) -> tuple[int, int, int]:
    raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    command_end = raw.rfind(")")
    if command_end < 0:
        raise SupervisorError("Linux process stat framing is invalid")
    fields = raw[command_end + 1 :].strip().split()
    if len(fields) <= 19:
        raise SupervisorError("Linux process stat is truncated")
    return int(fields[19]), int(fields[2]), int(fields[3])


def _boot_id() -> str:
    path = _regular_file(Path("/proc/sys/kernel/random/boot_id"), "host boot ID")
    value = path.read_text(encoding="ascii").strip().lower()
    if len(value) != 36:
        raise SupervisorError("host boot ID is invalid")
    return value


def _boottime() -> float:
    clock = getattr(time, "CLOCK_BOOTTIME", None)
    if clock is None:
        raise SupervisorError("formal supervisor requires CLOCK_BOOTTIME")
    return float(time.clock_gettime(clock))


def _open_exclusive_stream(path: Path) -> int:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    os.fchmod(descriptor, 0o600)
    _fsync_directory(path.parent)
    return descriptor


def _write_identical_or_new(path: Path, payload: Mapping[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        if _load_object(_regular_file(path, str(path))) != dict(payload):
            raise SupervisorError("immutable formal supervisor spec differs")
        return
    _write_exclusive_json(path, payload)


def _write_exclusive_json(path: Path, payload: Mapping[str, Any]) -> None:
    encoded = (json.dumps(dict(payload), separators=(",", ":"), sort_keys=True) + "\n").encode()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        view = memoryview(encoded)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise SupervisorError("formal supervisor receipt write stalled")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _fsync_directory(path.parent)


def _regular_directory(path: Path, label: str) -> Path:
    _assert_no_symlink_ancestors(path)
    info = os.lstat(path)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise SupervisorError(f"{label} is not a regular directory")
    return path


def _regular_file(path: Path, label: str) -> Path:
    _assert_no_symlink_ancestors(path)
    info = os.lstat(path)
    if (
        stat.S_ISLNK(info.st_mode)
        or not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
    ):
        raise SupervisorError(f"{label} is not a regular nlink-1 file")
    return path


def _assert_no_symlink_ancestors(path: Path) -> None:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:-1]:
        current = current / part
        info = os.lstat(current)
        if stat.S_ISLNK(info.st_mode):
            raise SupervisorError(f"formal supervisor path has symlink ancestor: {current}")


def _load_object(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise SupervisorError("formal supervisor JSON is not an object")
    return loaded


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _digest(value: str, label: str) -> str:
    normalized = value.removeprefix("sha256:")
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise SupervisorError(f"{label} is not a lowercase SHA-256")
    return normalized


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_json(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(dict(payload), separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _result(status: str, *, session_id: str) -> dict[str, Any]:
    return {
        "schema_version": "agentdojo_formal_supervisor_result/v1",
        "status": status,
        "session_id": session_id,
        "blind_only": True,
    }


if __name__ == "__main__":
    raise SystemExit(main())
