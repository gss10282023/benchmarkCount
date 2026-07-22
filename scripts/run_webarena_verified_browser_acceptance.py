#!/usr/bin/env python3
"""Independently accept six-site WebArena-Verified deployments in a real browser.

This gate is intentionally downstream of the controller's full deployment
receipt.  It never reads model credentials, never loads browser storage state,
and never enumerates or exports cookies.  Authentication evidence for the four
stateful sites is referenced only from the controller's secret-free login
summary; the independent browser context checks public HTTP/UI visibility.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import time
from typing import Any, Iterator, Mapping, Sequence
import urllib.error
import urllib.parse
import urllib.request
import uuid


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INFRA = ROOT / "configs" / "infra.yaml"
DEFAULT_SITE_LOCK = ROOT / "configs" / "webarena_verified_sites.lock.json"
DEFAULT_DEPLOY_RECEIPTS = (
    ROOT / "experiments" / "step20" / "webarena_verified" / "environment_receipts" / "site_deployment"
)
DEFAULT_RECEIPT_OUTPUT = (
    ROOT
    / "experiments"
    / "step20"
    / "webarena_verified"
    / "environment_receipts"
    / "browser_acceptance"
)
DEFAULT_ARTIFACT_ROOT = ROOT / "output" / "playwright" / "webarena_verified"
DEFAULT_PWCLI = Path("/Users/gss/.codex/skills/playwright/scripts/playwright_cli.sh")

SCHEMA = "webarena_verified_browser_acceptance/v1"
MACHINE_SCHEMA = "webarena_verified_browser_machine_acceptance/v1"
DEPLOY_SCHEMA = "webarena_verified_site_deployment_receipt/v1"
SITE_ORDER = ("shopping", "shopping_admin", "reddit", "gitlab", "wikipedia", "map")
AUTH_SITES = ("shopping", "shopping_admin", "reddit", "gitlab")
AUTH_STATE_COMBINATIONS = (
    "gitlab+shopping",
    "gitlab+shopping_admin",
    "gitlab+reddit",
    "shopping+shopping_admin",
    "gitlab",
    "shopping",
    "shopping_admin",
    "reddit",
)
TRACE_SITES = ("wikipedia", "map")
HEX_SHA256 = re.compile(r"[0-9a-f]{64}")
COOKIE_HEADER_MARKERS = (
    b'"name":"cookie"',
    b'"name": "cookie"',
    b'"name":"set-cookie"',
    b'"name": "set-cookie"',
    b"\ncookie:",
    b"\nset-cookie:",
)


class BrowserAcceptanceError(RuntimeError):
    """Raised when any prerequisite or independent browser check fails."""


@dataclass(frozen=True)
class Machine:
    machine_id: str
    host: str
    user: str
    port: int
    key_path: Path
    fingerprint: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, payload: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_bytes(payload)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        temporary.unlink(missing_ok=True)
    return sha256_bytes(data)


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BrowserAcceptanceError(f"cannot read valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise BrowserAcceptanceError(f"JSON root must be an object: {path}")
    return payload


def _site_lock_sha256(site_lock: Mapping[str, Any]) -> str:
    encoded = json.dumps(site_lock, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_machines(infra_path: Path) -> list[Machine]:
    infra = load_json(infra_path)
    selected: list[Machine] = []
    for row in infra.get("machines") or []:
        if row.get("role") != "webarena_vps" or not bool(row.get("enabled")):
            continue
        benchmark = (row.get("benchmarks") or {}).get("WebArena-Verified") or {}
        controller = benchmark.get("site_controller") or {}
        ssh = row.get("ssh") or {}
        machine = Machine(
            machine_id=str(row.get("machine_id") or ""),
            host=str(ssh.get("host") or ""),
            user=str(ssh.get("user") or ""),
            port=int(ssh.get("port") or 0),
            key_path=Path(str(ssh.get("key_path") or "")),
            fingerprint=str(controller.get("ssh_host_fingerprint") or ""),
        )
        if (
            not machine.machine_id
            or not machine.host
            or not machine.user
            or machine.port <= 0
            or not machine.key_path.is_file()
            or not machine.fingerprint.startswith("SHA256:")
        ):
            raise BrowserAcceptanceError(f"incomplete locked SSH route: {machine.machine_id!r}")
        if bool(benchmark.get("sync_dotenv", True)):
            raise BrowserAcceptanceError(f"dotenv synchronization is not disabled: {machine.machine_id}")
        selected.append(machine)
    if len(selected) != 3 or len({machine.machine_id for machine in selected}) != 3:
        raise BrowserAcceptanceError("exactly three unique enabled WebArena VPS routes are required")
    return selected


def validate_deploy_receipt(
    receipt: Mapping[str, Any],
    *,
    machine: Machine,
    site_lock: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate that a receipt is the strict, full-SHA deploy-and-accept gate."""

    if receipt.get("schema_version") != DEPLOY_SCHEMA:
        raise BrowserAcceptanceError(f"wrong deployment receipt schema: {machine.machine_id}")
    if receipt.get("operation") != "deploy_and_accept" or receipt.get("status") != "pass":
        raise BrowserAcceptanceError(f"full deployment did not pass: {machine.machine_id}")
    if receipt.get("machine_id") != machine.machine_id or receipt.get("ssh_host") != machine.host:
        raise BrowserAcceptanceError(f"deployment receipt identity mismatch: {machine.machine_id}")
    if receipt.get("ssh_host_fingerprint") != machine.fingerprint:
        raise BrowserAcceptanceError(f"deployment receipt fingerprint mismatch: {machine.machine_id}")
    if receipt.get("site_lock_sha256") != _site_lock_sha256(site_lock):
        raise BrowserAcceptanceError(f"deployment receipt site-lock hash mismatch: {machine.machine_id}")
    lock = receipt.get("exclusive_lock") or {}
    if not lock.get("acquired_at") or not lock.get("released_at"):
        raise BrowserAcceptanceError(f"deployment exclusive lock was not proven: {machine.machine_id}")

    sources = receipt.get("runtime_sources") or {}
    if (
        sources.get("installed_version") != "1.2.3"
        or sources.get("official_commit") != site_lock.get("official_commit")
        or sources.get("runner_commit") != site_lock.get("runner_commit")
    ):
        raise BrowserAcceptanceError(f"deployment runtime source lock mismatch: {machine.machine_id}")

    images = receipt.get("images") or {}
    if set(images) != set(SITE_ORDER):
        raise BrowserAcceptanceError(f"deployment image set is not six sites: {machine.machine_id}")
    for site in SITE_ORDER:
        expected = site_lock["images"][site]
        if images[site].get("reference") != f"{expected['reference']}@{expected['digest']}":
            raise BrowserAcceptanceError(f"deployment image digest mismatch: {machine.machine_id}/{site}")
        image_id = str(images[site].get("image_id") or "")
        if not image_id.startswith("sha256:") or not HEX_SHA256.fullmatch(image_id[7:]):
            raise BrowserAcceptanceError(f"invalid local image ID: {machine.machine_id}/{site}")

    expected_assets = set(site_lock.get("data_assets") or {})
    assets = receipt.get("data_assets") or {}
    if set(assets) != expected_assets:
        raise BrowserAcceptanceError(f"full deployment data asset set mismatch: {machine.machine_id}")
    for name, expected in site_lock["data_assets"].items():
        row = assets[name]
        if int(row.get("size_bytes") or -1) != int(expected["size_bytes"]):
            raise BrowserAcceptanceError(f"deployment data size mismatch: {machine.machine_id}/{name}")
        if not HEX_SHA256.fullmatch(str(row.get("sha256") or "")):
            raise BrowserAcceptanceError(
                f"full SHA is absent from deployment receipt: {machine.machine_id}/{name}"
            )

    reset_rows = receipt.get("resets") or []
    site_rows = receipt.get("sites") or []
    if [row.get("site") for row in reset_rows] != list(SITE_ORDER) or not all(
        row.get("ok") is True for row in reset_rows
    ):
        raise BrowserAcceptanceError(f"six-site clean deployment reset did not pass: {machine.machine_id}")
    if [row.get("site") for row in site_rows] != list(SITE_ORDER) or not all(
        row.get("ok") is True for row in site_rows
    ):
        raise BrowserAcceptanceError(f"six-site deployment status did not pass: {machine.machine_id}")
    for row in site_rows:
        bindings = ((row.get("container") or {}).get("port_bindings") or [])
        if not bindings or any("127.0.0.1:" not in str(binding) for binding in bindings):
            raise BrowserAcceptanceError(
                f"site is not proven loopback-only: {machine.machine_id}/{row.get('site')}"
            )
        sentinels = row.get("sentinels") or []
        if not sentinels or not all(check.get("ok") is True for check in sentinels):
            raise BrowserAcceptanceError(
                f"controller sentinel did not pass: {machine.machine_id}/{row.get('site')}"
            )

    login = receipt.get("login") or {}
    if login.get("status") != "pass" or login.get("required_sites") != list(AUTH_SITES):
        raise BrowserAcceptanceError(f"four-site login probe did not pass: {machine.machine_id}")
    if login.get("required_state_combinations") != list(AUTH_STATE_COMBINATIONS):
        raise BrowserAcceptanceError(
            f"eight required login state combinations are incomplete: {machine.machine_id}"
        )
    count_keys = (
        "generated_state_file_count",
        "validated_authenticated_page_probe_count",
        "validated_cookie_count",
        "validated_associated_cookie_count",
        "validated_associated_nonempty_cookie_count",
        "validated_effective_associated_nonempty_cookie_count",
        "validated_empty_cookie_count",
        "validated_expired_empty_cookie_count",
        "validated_nonempty_cookie_count",
        "validated_persistent_cookie_count",
        "validated_session_cookie_count",
    )
    if any(type(login.get(key)) is not int or int(login[key]) < 0 for key in count_keys):
        raise BrowserAcceptanceError(
            f"login validation counts are missing or invalid: {machine.machine_id}"
        )
    counts = {key: int(login[key]) for key in count_keys}
    if counts["generated_state_file_count"] != 8:
        raise BrowserAcceptanceError(f"login state file count is not exactly 8: {machine.machine_id}")
    if counts["validated_authenticated_page_probe_count"] != 12:
        raise BrowserAcceptanceError(
            f"authenticated page probe count is not exactly 12: {machine.machine_id}"
        )
    if counts["validated_associated_cookie_count"] < 8:
        raise BrowserAcceptanceError(
            f"associated cookie count is below 8: {machine.machine_id}"
        )
    if counts["validated_effective_associated_nonempty_cookie_count"] < 8:
        raise BrowserAcceptanceError(
            f"effective associated nonempty cookie count is below 8: {machine.machine_id}"
        )
    if (
        counts["validated_associated_nonempty_cookie_count"]
        != counts["validated_effective_associated_nonempty_cookie_count"]
        or counts["validated_associated_cookie_count"]
        < counts["validated_associated_nonempty_cookie_count"]
        or counts["validated_empty_cookie_count"] + counts["validated_nonempty_cookie_count"]
        != counts["validated_cookie_count"]
        or counts["validated_expired_empty_cookie_count"]
        > counts["validated_empty_cookie_count"]
        or counts["validated_persistent_cookie_count"]
        + counts["validated_session_cookie_count"]
        != counts["validated_cookie_count"]
    ):
        raise BrowserAcceptanceError(
            f"login cookie validation counts do not close: {machine.machine_id}"
        )
    if len(login.get("authenticated_page_probes") or []) != 4:
        raise BrowserAcceptanceError(f"authenticated page probes are incomplete: {machine.machine_id}")
    if login.get("sensitive_state_retained") is not False:
        raise BrowserAcceptanceError(f"sensitive login state may have been retained: {machine.machine_id}")
    if counts["validated_cookie_count"] <= 0:
        raise BrowserAcceptanceError(f"login storage validation is empty: {machine.machine_id}")

    return {
        "status": "pass",
        "source": "controller_full_deployment_receipt",
        "required_sites": list(AUTH_SITES),
        "required_state_combinations": list(AUTH_STATE_COMBINATIONS),
        "authenticated_page_probes": list(login["authenticated_page_probes"]),
        "validated_state_file_count": 8,
        "validated_authenticated_page_probe_count": 12,
        "validated_cookie_count": counts["validated_cookie_count"],
        "validated_associated_cookie_count": counts["validated_associated_cookie_count"],
        "validated_associated_nonempty_cookie_count": counts[
            "validated_associated_nonempty_cookie_count"
        ],
        "validated_effective_associated_nonempty_cookie_count": counts[
            "validated_effective_associated_nonempty_cookie_count"
        ],
        "validated_empty_cookie_count": counts["validated_empty_cookie_count"],
        "validated_expired_empty_cookie_count": counts[
            "validated_expired_empty_cookie_count"
        ],
        "validated_nonempty_cookie_count": counts["validated_nonempty_cookie_count"],
        "validated_persistent_cookie_count": counts["validated_persistent_cookie_count"],
        "validated_session_cookie_count": counts["validated_session_cookie_count"],
        "sensitive_state_retained": False,
    }


def _verified_known_hosts(machine: Machine) -> Path:
    try:
        scan = subprocess.run(
            [
                "ssh-keyscan",
                "-T",
                "10",
                "-H",
                "-p",
                str(machine.port),
                "-t",
                "ed25519",
                machine.host,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BrowserAcceptanceError(f"cannot scan SSH key: {machine.machine_id}") from exc
    lines = [line for line in scan.stdout.splitlines() if " ssh-ed25519 " in line]
    if scan.returncode != 0 or not lines:
        raise BrowserAcceptanceError(f"SSH ED25519 scan failed: {machine.machine_id}")
    key_text = "\n".join(lines) + "\n"
    fingerprint = subprocess.run(
        ["ssh-keygen", "-E", "sha256", "-lf", "-"],
        input=key_text,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    actual = {
        match.group(0)
        for line in fingerprint.stdout.splitlines()
        for match in [re.search(r"SHA256:[A-Za-z0-9+/=]+", line)]
        if match is not None
    }
    if fingerprint.returncode != 0 or actual != {machine.fingerprint}:
        raise BrowserAcceptanceError(f"SSH fingerprint mismatch: {machine.machine_id}")
    fd, raw_path = tempfile.mkstemp(prefix="webarena-browser-known-hosts-")
    path = Path(raw_path)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(key_text)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(path, 0o600)
    return path


def _wait_for_tunnel(process: subprocess.Popen[str], ports: Sequence[int], timeout: float = 20) -> None:
    deadline = time.monotonic() + timeout
    pending = set(ports)
    while pending and time.monotonic() < deadline:
        if process.poll() is not None:
            stderr = (process.stderr.read() if process.stderr else "").strip()
            raise BrowserAcceptanceError(f"SSH tunnel exited early: {stderr[:300]}")
        for port in tuple(pending):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.3):
                    pending.remove(port)
            except OSError:
                pass
        if pending:
            time.sleep(0.2)
    if pending:
        raise BrowserAcceptanceError(f"SSH tunnel ports did not open: {sorted(pending)}")


@contextmanager
def ssh_tunnel(machine: Machine, site_lock: Mapping[str, Any]) -> Iterator[None]:
    ports = [int(site_lock["sites"][site]["host_port"]) for site in SITE_ORDER]
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("127.0.0.1", port))
            except OSError as exc:
                raise BrowserAcceptanceError(f"local tunnel port is already occupied: {port}") from exc

    known_hosts = _verified_known_hosts(machine)
    argv = [
        "ssh",
        "-N",
        "-T",
        "-i",
        str(machine.key_path),
        "-p",
        str(machine.port),
        "-o",
        "BatchMode=yes",
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        f"UserKnownHostsFile={known_hosts}",
        "-o",
        "HostKeyAlgorithms=ssh-ed25519",
        "-o",
        "ExitOnForwardFailure=yes",
        "-o",
        "ServerAliveInterval=15",
        "-o",
        "ServerAliveCountMax=3",
    ]
    for port in ports:
        argv.extend(["-L", f"127.0.0.1:{port}:127.0.0.1:{port}"])
    argv.append(f"{machine.user}@{machine.host}")
    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        _wait_for_tunnel(process, ports)
        yield
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        known_hosts.unlink(missing_ok=True)


def http_probe(url: str, needle: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "webarena-browser-acceptance/1"})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read(4 * 1024 * 1024).decode("utf-8", "replace")
            status = int(response.status)
            final_url = str(response.url)
    except (OSError, urllib.error.URLError) as exc:
        raise BrowserAcceptanceError(f"HTTP probe failed for {url}: {type(exc).__name__}") from exc
    parsed = urllib.parse.urlsplit(final_url)
    expected = urllib.parse.urlsplit(url)
    if parsed.hostname != "127.0.0.1" or parsed.port != expected.port:
        raise BrowserAcceptanceError(f"HTTP probe escaped its loopback tunnel: {url}")
    if status != 200 or needle not in body:
        raise BrowserAcceptanceError(f"HTTP/UI sentinel failed for {url}")
    return {
        "status_code": status,
        "sentinel_match": True,
        "final_path": parsed.path or "/",
        "loopback_tunnel": True,
    }


def _pwcli(
    pwcli: Path,
    session: str,
    args: Sequence[str],
    *,
    output_dir: Path | None = None,
    timeout: int = 180,
) -> dict[str, Any]:
    env = os.environ.copy()
    if output_dir is not None:
        env["PLAYWRIGHT_MCP_OUTPUT_DIR"] = str(output_dir)
    command = [str(pwcli), "--json", f"-s={session}", *[str(value) for value in args]]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd=ROOT,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BrowserAcceptanceError(f"playwright-cli command failed: {args[0]}") from exc
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise BrowserAcceptanceError(f"playwright-cli returned invalid JSON: {args[0]}") from exc
    if result.returncode != 0 or payload.get("isError"):
        message = str(payload.get("error") or result.stderr or "unknown error")
        raise BrowserAcceptanceError(f"playwright-cli {args[0]} failed: {message[:300]}")
    return payload


def _close_session(pwcli: Path, session: str) -> None:
    try:
        _pwcli(pwcli, session, ["close"], timeout=30)
    except BrowserAcceptanceError:
        pass


def _artifact_row(path: Path, *, root: Path, allow_empty: bool = False) -> dict[str, Any]:
    if not path.is_file() or (path.stat().st_size <= 0 and not allow_empty):
        raise BrowserAcceptanceError(f"browser artifact is empty or absent: {path}")
    os.chmod(path, 0o600)
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def _assert_trace_has_no_cookie_headers(paths: Sequence[Path]) -> None:
    for path in paths:
        raw = path.read_bytes().lower()
        if any(marker in raw for marker in COOKIE_HEADER_MARKERS):
            for candidate in paths:
                candidate.unlink(missing_ok=True)
            raise BrowserAcceptanceError("public trace unexpectedly contained a cookie header")


def _remove_playwright_auxiliary_files(folder: Path) -> None:
    """Delete CLI auto-reports that are superseded by explicitly named evidence."""

    for pattern in ("page-*.yml", "console-*.log"):
        for path in folder.glob(pattern):
            path.unlink(missing_ok=True)


def _artifact_inventory(folder: Path, *, root: Path) -> dict[str, Any]:
    for directory in sorted(candidate for candidate in folder.rglob("*") if candidate.is_dir()):
        os.chmod(directory, 0o700)
    rows = [
        _artifact_row(path, root=root, allow_empty=path.suffix == ".network")
        for path in sorted(candidate for candidate in folder.rglob("*") if candidate.is_file())
    ]
    if not rows:
        raise BrowserAcceptanceError(f"artifact inventory is empty: {folder}")
    tree_payload = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "file_count": len(rows),
        "total_size_bytes": sum(int(row["size_bytes"]) for row in rows),
        "tree_sha256": hashlib.sha256(tree_payload).hexdigest(),
        "files": rows,
    }


def collect_machine(
    *,
    machine: Machine,
    deploy_receipt: Mapping[str, Any],
    deploy_receipt_path: Path,
    login_summary: Mapping[str, Any],
    site_lock: Mapping[str, Any],
    pwcli: Path,
    staging_dir: Path,
) -> dict[str, Any]:
    machine_dir = staging_dir / machine.machine_id
    machine_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
    session = f"wa-{machine.machine_id}-ui-{uuid.uuid4().hex[:8]}"
    site_results: list[dict[str, Any]] = []
    first = True
    try:
        with ssh_tunnel(machine, site_lock):
            for site in SITE_ORDER:
                spec = site_lock["sites"][site]
                url = str(spec["health_url"])
                needle = str(spec["health_needle"])
                http = http_probe(url, needle)
                if first:
                    _pwcli(pwcli, session, ["open", url], output_dir=machine_dir, timeout=180)
                    first = False
                else:
                    _pwcli(pwcli, session, ["goto", url], timeout=180)
                snapshot_path = machine_dir / f"{site}.snapshot.yml"
                screenshot_path = machine_dir / f"{site}.png"
                _pwcli(
                    pwcli,
                    session,
                    ["snapshot", "--filename", str(snapshot_path), "--depth", "8"],
                    timeout=120,
                )
                expression = (
                    "() => ({title: document.title.slice(0,160), "
                    "url: location.href, sentinel: "
                    "(document.title + '\\n' + (document.body?.innerText || '')).includes("
                    + json.dumps(needle)
                    + ")})"
                )
                evaluated = _pwcli(pwcli, session, ["eval", expression], timeout=90)
                try:
                    browser = json.loads(str(evaluated["result"]))
                except (KeyError, TypeError, json.JSONDecodeError) as exc:
                    raise BrowserAcceptanceError(
                        f"invalid browser evaluation result: {machine.machine_id}/{site}"
                    ) from exc
                browser_url = urllib.parse.urlsplit(str(browser.get("url") or ""))
                if (
                    browser.get("sentinel") is not True
                    or not str(browser.get("title") or "").strip()
                    or browser_url.hostname != "127.0.0.1"
                    or browser_url.port != int(spec["host_port"])
                ):
                    raise BrowserAcceptanceError(
                        f"real-browser UI sentinel failed: {machine.machine_id}/{site}"
                    )
                _pwcli(
                    pwcli,
                    session,
                    ["screenshot", "--filename", str(screenshot_path), "--full-page"],
                    timeout=180,
                )
                screenshot = _artifact_row(screenshot_path, root=staging_dir)
                snapshot = _artifact_row(snapshot_path, root=staging_dir)
                site_results.append(
                    {
                        "site": site,
                        "status": "pass",
                        "http": http,
                        "browser": {
                            "title": str(browser["title"]),
                            "final_path": browser_url.path or "/",
                            "loopback_tunnel": True,
                            "ui_sentinel_match": True,
                            "authenticated_state_loaded": False,
                        },
                        "artifacts": {"screenshot": screenshot, "snapshot": snapshot},
                    }
                )
            _close_session(pwcli, session)

            _remove_playwright_auxiliary_files(machine_dir)

            trace_session = f"wa-{machine.machine_id}-trace-{uuid.uuid4().hex[:8]}"
            trace_dir = machine_dir / "public_trace"
            trace_dir.mkdir(mode=0o700)
            try:
                _pwcli(
                    pwcli,
                    trace_session,
                    ["open", str(site_lock["sites"]["wikipedia"]["health_url"])],
                    output_dir=trace_dir,
                    timeout=180,
                )
                _pwcli(pwcli, trace_session, ["snapshot", "--depth", "5"], timeout=90)
                _pwcli(pwcli, trace_session, ["network-state-set", "offline"], timeout=60)
                _pwcli(pwcli, trace_session, ["tracing-start"], timeout=60)
                offline_snapshot = trace_dir / "wikipedia.offline.snapshot.yml"
                offline_screenshot = trace_dir / "wikipedia.offline.png"
                _pwcli(
                    pwcli,
                    trace_session,
                    ["snapshot", "--filename", str(offline_snapshot), "--depth", "8"],
                    timeout=90,
                )
                evaluated = _pwcli(
                    pwcli,
                    trace_session,
                    [
                        "eval",
                        "() => ({title: document.title, sentinel: "
                        "(document.title + '\\n' + (document.body?.innerText || '')).includes('Wikipedia')})",
                    ],
                    timeout=90,
                )
                try:
                    offline_result = json.loads(str(evaluated["result"]))
                except (KeyError, TypeError, json.JSONDecodeError) as exc:
                    raise BrowserAcceptanceError(
                        f"invalid offline trace evaluation: {machine.machine_id}"
                    ) from exc
                if offline_result.get("sentinel") is not True:
                    raise BrowserAcceptanceError(
                        f"offline trace UI sentinel failed: {machine.machine_id}/wikipedia"
                    )
                _pwcli(
                    pwcli,
                    trace_session,
                    ["screenshot", "--filename", str(offline_screenshot), "--full-page"],
                    timeout=120,
                )
                _pwcli(pwcli, trace_session, ["tracing-stop"], timeout=120)
            finally:
                _close_session(pwcli, trace_session)
            _remove_playwright_auxiliary_files(trace_dir)
            trace_files = sorted((trace_dir / "traces").glob("trace-*.trace"))
            network_files = sorted((trace_dir / "traces").glob("trace-*.network"))
            stack_files = sorted((trace_dir / "traces").glob("trace-*.stacks"))
            if len(trace_files) != 1 or len(network_files) != 1 or len(stack_files) != 1:
                raise BrowserAcceptanceError(f"public trace was not captured: {machine.machine_id}")
            _assert_trace_has_no_cookie_headers([*trace_files, *network_files, *stack_files])
            trace_artifacts = {
                "trace": _artifact_row(trace_files[0], root=staging_dir),
                "network": _artifact_row(network_files[0], root=staging_dir, allow_empty=True),
                "stacks": _artifact_row(stack_files[0], root=staging_dir),
                "offline_snapshot": _artifact_row(offline_snapshot, root=staging_dir),
                "offline_screenshot": _artifact_row(offline_screenshot, root=staging_dir),
                "scope": ["wikipedia"],
                "capture_mode": "post-load offline action trace",
                "authenticated_state_loaded": False,
                "cookie_headers_present": False,
            }
    finally:
        _close_session(pwcli, session)

    if len(site_results) != 6 or any(row["status"] != "pass" for row in site_results):
        raise BrowserAcceptanceError(f"six-site browser coverage incomplete: {machine.machine_id}")
    artifact_inventory = _artifact_inventory(machine_dir, root=staging_dir)
    deploy_hash = sha256_file(deploy_receipt_path)
    return {
        "schema_version": MACHINE_SCHEMA,
        "status": "pass",
        "machine_id": machine.machine_id,
        "ssh_host": machine.host,
        "ssh_host_fingerprint": machine.fingerprint,
        "checked_at": utc_now(),
        "deployment_receipt": {
            "path": deploy_receipt_path.relative_to(ROOT).as_posix(),
            "sha256": deploy_hash,
            "status": deploy_receipt["status"],
            "operation": deploy_receipt["operation"],
        },
        "authentication": dict(login_summary),
        "browser_isolation": {
            "binding": "127.0.0.1",
            "transport": "strict-fingerprint SSH local forwarding",
            "fresh_unauthenticated_context": True,
            "credentials_loaded": False,
            "browser_storage_loaded": False,
            "cookies_read_or_exported": False,
        },
        "sites": site_results,
        "trace": trace_artifacts,
        "artifact_inventory": artifact_inventory,
        "gates": {
            "full_deploy_receipt_pass": True,
            "six_http_sentinels_pass": True,
            "six_real_browser_ui_sentinels_pass": True,
            "twelve_authenticated_controller_probes_pass": True,
            "no_sensitive_browser_state_retained": True,
            "trace_cookie_headers_absent": True,
        },
    }


def _rewrite_artifact_paths(machine_receipt: dict[str, Any], staging_dir: Path) -> None:
    """Remove the staging prefix after the artifacts have been atomically promoted."""

    prefix = staging_dir.name + "/"
    for site in machine_receipt["sites"]:
        for artifact in site["artifacts"].values():
            if str(artifact["path"]).startswith(prefix):
                artifact["path"] = str(artifact["path"])[len(prefix) :]
    for key in ("trace", "network", "stacks", "offline_snapshot", "offline_screenshot"):
        artifact = machine_receipt["trace"][key]
        if str(artifact["path"]).startswith(prefix):
            artifact["path"] = str(artifact["path"])[len(prefix) :]
    for artifact in machine_receipt["artifact_inventory"]["files"]:
        if str(artifact["path"]).startswith(prefix):
            artifact["path"] = str(artifact["path"])[len(prefix) :]


def run_acceptance(args: argparse.Namespace) -> dict[str, Any]:
    if shutil.which("npx") is None:
        raise BrowserAcceptanceError("npx is required by the Playwright CLI wrapper")
    pwcli = Path(args.pwcli).resolve()
    if not pwcli.is_file() or not os.access(pwcli, os.X_OK):
        raise BrowserAcceptanceError(f"Playwright CLI wrapper is unavailable: {pwcli}")
    site_lock_path = Path(args.site_lock).resolve()
    site_lock = load_json(site_lock_path)
    if tuple(site_lock.get("sites") or {}) != SITE_ORDER:
        raise BrowserAcceptanceError("site lock must contain exactly six canonical sites in order")
    machines = load_machines(Path(args.infra).resolve())
    deploy_dir = Path(args.deploy_receipts).resolve()
    output_dir = Path(args.output).resolve()
    artifact_root = Path(args.artifact_root).resolve()

    prerequisites: list[tuple[Machine, Path, dict[str, Any], dict[str, Any]]] = []
    for machine in machines:
        receipt_path = deploy_dir / f"{machine.machine_id}.json"
        if not receipt_path.is_file():
            raise BrowserAcceptanceError(f"full deployment receipt is absent: {machine.machine_id}")
        receipt = load_json(receipt_path)
        login_summary = validate_deploy_receipt(receipt, machine=machine, site_lock=site_lock)
        prerequisites.append((machine, receipt_path, receipt, login_summary))

    existing = [artifact_root / machine.machine_id for machine in machines]
    existing.extend([output_dir / f"{machine.machine_id}.json" for machine in machines])
    existing.extend([output_dir / "acceptance.json", output_dir / "acceptance.json.sha256"])
    if any(path.exists() for path in existing) and not bool(args.replace):
        raise BrowserAcceptanceError("browser acceptance output already exists; use --replace explicitly")
    if args.replace:
        for path in existing:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink(missing_ok=True)

    artifact_root.mkdir(parents=True, exist_ok=True)
    os.chmod(artifact_root, 0o700)
    output_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(output_dir, 0o700)
    staging_dir = artifact_root / f".staging-{uuid.uuid4().hex}"
    staging_dir.mkdir(mode=0o700)
    machine_receipts: list[dict[str, Any]] = []
    try:
        for machine, receipt_path, receipt, login_summary in prerequisites:
            machine_receipts.append(
                collect_machine(
                    machine=machine,
                    deploy_receipt=receipt,
                    deploy_receipt_path=receipt_path,
                    login_summary=login_summary,
                    site_lock=site_lock,
                    pwcli=pwcli,
                    staging_dir=staging_dir,
                )
            )
        for machine in machines:
            os.replace(staging_dir / machine.machine_id, artifact_root / machine.machine_id)
        for receipt in machine_receipts:
            _rewrite_artifact_paths(receipt, staging_dir)
    except Exception:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise
    finally:
        if staging_dir.exists() and not any(staging_dir.iterdir()):
            staging_dir.rmdir()

    machine_index: list[dict[str, Any]] = []
    for receipt in machine_receipts:
        path = output_dir / f"{receipt['machine_id']}.json"
        digest = atomic_json(path, receipt)
        machine_index.append(
            {
                "machine_id": receipt["machine_id"],
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": digest,
                "status": receipt["status"],
                "site_count": len(receipt["sites"]),
            }
        )

    version = subprocess.run(
        [str(pwcli), "--version"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=ROOT,
    )
    if version.returncode != 0:
        raise BrowserAcceptanceError("cannot identify playwright-cli version")
    aggregate: dict[str, Any] = {
        "schema_version": SCHEMA,
        "status": "pass",
        "generated_at": utc_now(),
        "benchmark": "WebArena-Verified",
        "benchmark_version": "v1.2.3",
        "site_lock": {
            "path": site_lock_path.relative_to(ROOT).as_posix(),
            "sha256": _site_lock_sha256(site_lock),
        },
        "tool": {
            "workflow": "playwright-cli",
            "version": version.stdout.strip(),
            "real_browser": True,
        },
        "counts": {
            "machines_expected": 3,
            "machines_passed": 3,
            "sites_per_machine_expected": 6,
            "site_browser_probes_passed": 18,
            "http_probes_passed": 18,
            "authenticated_page_probes_validated": sum(
                int(receipt["authentication"]["validated_authenticated_page_probe_count"])
                for receipt in machine_receipts
            ),
            "authenticated_page_probe_types_referenced": sum(
                len(receipt["authentication"]["authenticated_page_probes"])
                for receipt in machine_receipts
            ),
            "login_state_files_validated": sum(
                int(receipt["authentication"]["validated_state_file_count"])
                for receipt in machine_receipts
            ),
            "associated_cookies_validated": sum(
                int(receipt["authentication"]["validated_associated_cookie_count"])
                for receipt in machine_receipts
            ),
            "public_traces": 3,
        },
        "machines": machine_index,
        "gates": {
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
        },
    }
    aggregate_path = output_dir / "acceptance.json"
    digest = atomic_json(aggregate_path, aggregate)
    sidecar = output_dir / "acceptance.json.sha256"
    sidecar.write_text(f"{digest}  acceptance.json\n", encoding="ascii")
    os.chmod(sidecar, 0o600)
    return aggregate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--infra", default=str(DEFAULT_INFRA))
    parser.add_argument("--site-lock", default=str(DEFAULT_SITE_LOCK))
    parser.add_argument("--deploy-receipts", default=str(DEFAULT_DEPLOY_RECEIPTS))
    parser.add_argument("--artifact-root", default=str(DEFAULT_ARTIFACT_ROOT))
    parser.add_argument("--output", default=str(DEFAULT_RECEIPT_OUTPUT))
    parser.add_argument("--pwcli", default=str(DEFAULT_PWCLI))
    parser.add_argument("--replace", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = run_acceptance(args)
    except BrowserAcceptanceError as exc:
        print(json.dumps({"schema_version": SCHEMA, "status": "fail", "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
