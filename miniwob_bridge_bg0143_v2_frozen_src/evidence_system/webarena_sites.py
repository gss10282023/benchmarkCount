"""Pinned WebArena-Verified v1.2.3 site lifecycle and slot-reset controller.

The evaluator and browser runner are not the benchmark environment.  This
module controls the six stateful WebArena site containers, verifies their
locked images/data, and emits an atomic reset receipt before a task attempt.
It deliberately does not read or copy ``.env``.
"""

from __future__ import annotations

import atexit
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import subprocess
import tempfile
import time
from typing import Any


SITE_ORDER = ("shopping", "shopping_admin", "reddit", "gitlab", "wikipedia", "map")
SITE_LOCK_SCHEMA = "webarena_verified_site_lock/v1"
DATA_LOCK_SCHEMA = "webarena_verified_site_data_sha256/v1"
RESET_RECEIPT_SCHEMA = "webarena_verified_slot_reset_receipt/v1"
DEPLOYMENT_RECEIPT_SCHEMA = "webarena_verified_site_deployment_receipt/v1"
HEX_SHA256 = re.compile(r"[0-9a-f]{64}")

_SAFE_LOGIN_PROBE_ERRORS = frozenset(
    {
        "login-probe-browser-cache-missing",
        "login-probe-renewal-failed:gitlab+shopping",
        "login-probe-renewal-failed:gitlab+shopping_admin",
        "login-probe-renewal-failed:gitlab+reddit",
        "login-probe-renewal-failed:shopping+shopping_admin",
        "login-probe-renewal-failed:gitlab",
        "login-probe-renewal-failed:shopping",
        "login-probe-renewal-failed:shopping_admin",
        "login-probe-renewal-failed:reddit",
        "login-probe-state-set-mismatch",
        "login-state-authenticated-page-failed:gitlab",
        "login-state-authenticated-page-failed:shopping",
        "login-state-authenticated-page-failed:shopping_admin",
        "login-state-authenticated-page-failed:reddit",
        "login-state-invalid-json",
        "login-state-empty-cookies",
        "login-state-invalid-cookie-schema",
        "login-state-invalid-expiry",
        "login-state-expired-nonempty-cookie",
        "login-state-no-effective-associated-cookie",
        "login-state-invalid-origins",
    }
)

RemoteRunner = Callable[[Sequence[str], int], subprocess.CompletedProcess[str]]
_KNOWN_HOST_FILES: dict[tuple[str, int, str], str] = {}


class WebArenaSiteError(RuntimeError):
    """A fail-closed site lock, deployment, health, or reset error."""


@dataclass(frozen=True)
class SlotIdentity:
    slot_id: str
    task_id: int
    agent_id: str
    attempt_id: int | str
    seed: int


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_site_lock(path: str | Path) -> dict[str, Any]:
    resolved = Path(path)
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WebArenaSiteError(f"cannot load WebArena site lock {resolved}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise WebArenaSiteError("WebArena site lock must be a JSON object")
    lock = dict(payload)
    _validate_site_lock(lock)
    return lock


def _validate_site_lock(lock: Mapping[str, Any]) -> None:
    if lock.get("schema_version") != SITE_LOCK_SCHEMA:
        raise WebArenaSiteError("unsupported WebArena site lock schema")
    if lock.get("benchmark_version") != "v1.2.3":
        raise WebArenaSiteError("site lock must target WebArena-Verified v1.2.3")
    if lock.get("official_commit") != "6473f72db5dcefc97b5725b59e734504edc28a21":
        raise WebArenaSiteError("site lock official commit mismatch")
    if lock.get("runner_commit") != "dce04686a56253aefba7b18a4fa0937cf1dc987b":
        raise WebArenaSiteError("site lock original-runner commit mismatch")
    for key in (
        "official_source_root",
        "official_runtime_python",
        "runner_root",
        "data_root",
        "data_sha256_lock",
        "slot_lock_file",
    ):
        value = str(lock.get(key) or "")
        if not value.startswith("/") or "<" in value or ">" in value:
            raise WebArenaSiteError(f"site lock has an invalid absolute path: {key}")
    if lock.get("network_binding") != "127.0.0.1":
        raise WebArenaSiteError("site containers must bind only to 127.0.0.1")

    images = lock.get("images")
    sites = lock.get("sites")
    assets = lock.get("data_assets")
    if not isinstance(images, Mapping) or set(images) != set(SITE_ORDER):
        raise WebArenaSiteError("site lock image set must be exactly the six official sites")
    if not isinstance(sites, Mapping) or set(sites) != set(SITE_ORDER):
        raise WebArenaSiteError("site lock site set must be exactly the six official sites")
    if not isinstance(assets, Mapping):
        raise WebArenaSiteError("site lock data_assets must be an object")

    used_host_ports: set[int] = set()
    for site in SITE_ORDER:
        image = images[site]
        spec = sites[site]
        if not isinstance(image, Mapping) or not isinstance(spec, Mapping):
            raise WebArenaSiteError(f"invalid site/image specification: {site}")
        digest = str(image.get("digest") or "")
        if not digest.startswith("sha256:") or not HEX_SHA256.fullmatch(digest.removeprefix("sha256:")):
            raise WebArenaSiteError(f"site image is not digest pinned: {site}")
        if not str(image.get("reference") or "").startswith("docker.io/am1n3e/webarena-verified-"):
            raise WebArenaSiteError(f"unexpected official image reference: {site}")
        if int(image.get("compressed_bytes") or 0) <= 0:
            raise WebArenaSiteError(f"missing image size lock: {site}")
        if str(spec.get("container_name") or "") != f"webarena_verified_{site}":
            raise WebArenaSiteError(f"non-canonical container name: {site}")
        for key in ("host_port", "env_ctrl_host_port", "container_port", "env_ctrl_container_port"):
            if int(spec.get(key) or 0) <= 0:
                raise WebArenaSiteError(f"invalid {key} for {site}")
        for host_port_key in ("host_port", "env_ctrl_host_port"):
            port = int(spec[host_port_key])
            if port in used_host_ports:
                raise WebArenaSiteError(f"duplicate locked host port: {port}")
            used_host_ports.add(port)
        health_url = str(spec.get("health_url") or "")
        if not health_url.startswith("http://127.0.0.1:"):
            raise WebArenaSiteError(f"non-loopback health URL: {site}")
        if not str(spec.get("health_needle") or ""):
            raise WebArenaSiteError(f"missing health sentinel: {site}")

    for filename, raw in assets.items():
        if not isinstance(raw, Mapping):
            raise WebArenaSiteError(f"invalid data asset lock: {filename}")
        if Path(str(filename)).name != str(filename):
            raise WebArenaSiteError(f"unsafe data asset filename: {filename}")
        if int(raw.get("size_bytes") or 0) <= 0:
            raise WebArenaSiteError(f"missing byte-size lock: {filename}")
        if raw.get("sha256_source") != "data_sha256_lock":
            raise WebArenaSiteError(f"data asset lacks mandatory SHA256 lock binding: {filename}")
        raw_sites = raw.get("sites")
        if not isinstance(raw_sites, list) or not raw_sites or not set(raw_sites) <= set(SITE_ORDER):
            raise WebArenaSiteError(f"invalid data asset site binding: {filename}")


def load_data_sha256_lock(payload: Mapping[str, Any], *, site_lock: Mapping[str, Any]) -> dict[str, Any]:
    data_lock = dict(payload)
    if data_lock.get("schema_version") != DATA_LOCK_SCHEMA:
        raise WebArenaSiteError("unsupported WebArena site data SHA256 lock schema")
    if data_lock.get("official_commit") != site_lock.get("official_commit"):
        raise WebArenaSiteError("data SHA256 lock official commit mismatch")
    assets = data_lock.get("assets")
    expected = site_lock["data_assets"]
    if not isinstance(assets, Mapping) or set(assets) != set(expected):
        raise WebArenaSiteError("data SHA256 lock asset set mismatch")
    for filename, expected_entry in expected.items():
        actual = assets[filename]
        if not isinstance(actual, Mapping):
            raise WebArenaSiteError(f"invalid data SHA256 lock entry: {filename}")
        if int(actual.get("size_bytes") or -1) != int(expected_entry["size_bytes"]):
            raise WebArenaSiteError(f"data SHA256 lock size mismatch: {filename}")
        digest = str(actual.get("sha256") or "")
        if not HEX_SHA256.fullmatch(digest):
            raise WebArenaSiteError(f"data SHA256 lock digest is invalid: {filename}")
    return data_lock


def pinned_image_reference(site_lock: Mapping[str, Any], site: str) -> str:
    _require_site(site)
    image = site_lock["images"][site]
    return f"{image['reference']}@{image['digest']}"


def container_run_argv(site_lock: Mapping[str, Any], site: str) -> list[str]:
    """Build the exact digest-pinned, loopback-only Docker invocation."""

    _require_site(site)
    spec = site_lock["sites"][site]
    binding = str(site_lock["network_binding"])
    argv = [
        "docker",
        "run",
        "-d",
        "--pull",
        "never",
        "--name",
        str(spec["container_name"]),
        "--label",
        f"org.openai.webarena.official_commit={site_lock['official_commit']}",
        "--label",
        f"org.openai.webarena.site={site}",
        "-p",
        f"{binding}:{int(spec['host_port'])}:{int(spec['container_port'])}",
        "-p",
        f"{binding}:{int(spec['env_ctrl_host_port'])}:{int(spec['env_ctrl_container_port'])}",
        "-e",
        f"WA_ENV_CTRL_EXTERNAL_SITE_URL={_site_base_url(spec)}",
    ]
    for volume in spec.get("volumes") or []:
        if not isinstance(volume, Mapping):
            raise WebArenaSiteError(f"invalid volume lock for {site}")
        suffix = ":ro" if bool(volume.get("read_only")) else ""
        argv.extend(["-v", f"{volume['source']}:{volume['target']}{suffix}"])
    argv.append(pinned_image_reference(site_lock, site))
    return argv


def _site_base_url(spec: Mapping[str, Any]) -> str:
    return f"http://127.0.0.1:{int(spec['host_port'])}"


def sites_for_agent_input(agent_input: Mapping[str, Any], *, expected_task_id: int) -> list[str]:
    if int(agent_input.get("task_id", -1)) != int(expected_task_id):
        raise WebArenaSiteError("agent input task_id does not match slot task_id")
    sites = agent_input.get("sites")
    if not isinstance(sites, list) or not sites:
        raise WebArenaSiteError("agent input must declare one or more sites")
    normalized = [str(site) for site in sites]
    if len(normalized) != len(set(normalized)) or not set(normalized) <= set(SITE_ORDER):
        raise WebArenaSiteError("agent input has duplicate or unsupported sites")
    return [site for site in SITE_ORDER if site in set(normalized)]


def validate_storage_state_payload(
    payload: Mapping[str, Any],
    *,
    expected_host: str,
    now_epoch: float,
) -> dict[str, int]:
    """Validate a Playwright state without returning any cookie material."""

    if not isinstance(payload, Mapping):
        raise WebArenaSiteError("login state must be a JSON object")
    cookies = payload.get("cookies")
    if not isinstance(cookies, list) or not cookies:
        raise WebArenaSiteError("login state has no cookies")
    associated = 0
    associated_nonempty = 0
    effective_associated_nonempty = 0
    empty = 0
    expired_empty = 0
    nonempty = 0
    persistent = 0
    session = 0
    for cookie in cookies:
        if not isinstance(cookie, Mapping):
            raise WebArenaSiteError("login state has an invalid cookie record")
        name = cookie.get("name")
        value = cookie.get("value")
        raw_domain = cookie.get("domain")
        path = cookie.get("path")
        http_only = cookie.get("httpOnly")
        secure = cookie.get("secure")
        same_site = cookie.get("sameSite")
        if (
            not isinstance(name, str)
            or not name
            or not isinstance(value, str)
            or not isinstance(raw_domain, str)
            or not raw_domain
            or not isinstance(path, str)
            or not path.startswith("/")
            or type(http_only) is not bool
            or type(secure) is not bool
            or same_site not in {"Lax", "None", "Strict"}
        ):
            raise WebArenaSiteError("login state has an invalid Playwright cookie schema")
        raw_expires = cookie.get("expires")
        if (
            isinstance(raw_expires, bool)
            or not isinstance(raw_expires, (int, float))
            or not math.isfinite(float(raw_expires))
        ):
            raise WebArenaSiteError("login state has an invalid cookie expiry")
        expires = float(raw_expires)
        domain = raw_domain.lstrip(".").lower()
        host = expected_host.lower()
        is_associated = domain == host or host.endswith(f".{domain}")
        if is_associated:
            associated += 1
        is_nonempty = bool(value)
        if is_nonempty:
            nonempty += 1
            if is_associated:
                associated_nonempty += 1
        else:
            empty += 1
        if expires > 0:
            persistent += 1
            if expires <= float(now_epoch):
                if is_nonempty:
                    raise WebArenaSiteError("login state contains an expired nonempty cookie")
                expired_empty += 1
        else:
            session += 1
        if is_associated and is_nonempty and (expires <= 0 or expires > float(now_epoch)):
            effective_associated_nonempty += 1
    if effective_associated_nonempty == 0:
        raise WebArenaSiteError(
            "login state has no effective nonempty cookie associated with the target host"
        )
    origins = payload.get("origins", [])
    if not isinstance(origins, list):
        raise WebArenaSiteError("login state origins must be a list")
    return {
        "cookie_count": len(cookies),
        "associated_cookie_count": associated,
        "associated_nonempty_cookie_count": associated_nonempty,
        "effective_associated_nonempty_cookie_count": effective_associated_nonempty,
        "empty_cookie_count": empty,
        "expired_empty_cookie_count": expired_empty,
        "nonempty_cookie_count": nonempty,
        "persistent_cookie_count": persistent,
        "session_cookie_count": session,
    }


def atomic_write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    fd, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_name, 0o600)
        os.replace(temporary_name, destination)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def run_verified_ssh_argv(
    *,
    host: str,
    user: str,
    port: int,
    key_path: str,
    expected_ed25519_fingerprint: str,
    argv: Sequence[str],
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    """Run one argv-only SSH command after an exact ED25519 host-key check."""

    try:
        known_hosts = _verified_known_hosts_file(
            host=host,
            port=int(port),
            expected_fingerprint=expected_ed25519_fingerprint,
        )
    except WebArenaSiteError as exc:
        return subprocess.CompletedProcess(
            ["ssh"],
            returncode=255,
            stdout="",
            stderr=str(exc),
        )
    remote_command = _shell_join(argv)
    command = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        f"UserKnownHostsFile={known_hosts}",
        "-o",
        "GlobalKnownHostsFile=/dev/null",
        "-o",
        "HostKeyAlgorithms=ssh-ed25519",
        "-i",
        key_path,
        "-p",
        str(int(port)),
        f"{user}@{host}",
        remote_command,
    ]
    try:
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=max(1, int(timeout)),
        )
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(
            command,
            returncode=124,
            stdout=str(exc.stdout or ""),
            stderr=(str(exc.stderr or "") + f"\ncommand timed out after {timeout}s").strip(),
        )


def _verified_known_hosts_file(*, host: str, port: int, expected_fingerprint: str) -> str:
    if not host or not expected_fingerprint.startswith("SHA256:"):
        raise WebArenaSiteError("SSH host and locked ED25519 fingerprint are required")
    cache_key = (host, int(port), expected_fingerprint)
    cached = _KNOWN_HOST_FILES.get(cache_key)
    if cached and Path(cached).is_file():
        return cached

    try:
        scan = subprocess.run(
            ["ssh-keyscan", "-T", "10", "-H", "-p", str(int(port)), "-t", "ed25519", host],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WebArenaSiteError(f"cannot scan SSH ED25519 host key for {host}: {exc}") from exc
    key_lines = [line for line in scan.stdout.splitlines() if " ssh-ed25519 " in line]
    if scan.returncode != 0 or not key_lines:
        raise WebArenaSiteError(f"SSH ED25519 host-key scan failed for {host}")
    key_text = "\n".join(key_lines) + "\n"
    try:
        fingerprint = subprocess.run(
            ["ssh-keygen", "-E", "sha256", "-lf", "-"],
            input=key_text,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WebArenaSiteError(f"cannot fingerprint SSH host key for {host}: {exc}") from exc
    fingerprints = {
        match.group(0)
        for line in fingerprint.stdout.splitlines()
        for match in [re.search(r"SHA256:[A-Za-z0-9+/=]+", line)]
        if match is not None
    }
    if fingerprint.returncode != 0 or fingerprints != {expected_fingerprint}:
        raise WebArenaSiteError(
            f"SSH ED25519 fingerprint mismatch for {host}; expected {expected_fingerprint}"
        )

    fd, path = tempfile.mkstemp(prefix="webarena-known-hosts-")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(key_text)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(path, 0o600)
    _KNOWN_HOST_FILES[cache_key] = path
    return path


def _shell_join(argv: Sequence[str]) -> str:
    import shlex

    return shlex.join([str(value) for value in argv])


def _cleanup_known_hosts_files() -> None:
    for path in set(_KNOWN_HOST_FILES.values()):
        try:
            Path(path).unlink(missing_ok=True)
        except OSError:
            pass


atexit.register(_cleanup_known_hosts_files)


class WebArenaSiteController:
    """Remote site controller with digest, data, health, and receipt gates."""

    def __init__(
        self,
        *,
        site_lock: Mapping[str, Any],
        run_remote: RemoteRunner,
        machine_id: str,
        ssh_host: str,
        ssh_host_fingerprint: str | None = None,
    ) -> None:
        _validate_site_lock(site_lock)
        self.site_lock = dict(site_lock)
        self.run_remote = run_remote
        self.machine_id = machine_id
        self.ssh_host = ssh_host
        self.ssh_host_fingerprint = ssh_host_fingerprint

    def verify_images(self, sites: Sequence[str] = SITE_ORDER) -> dict[str, dict[str, Any]]:
        verified: dict[str, dict[str, Any]] = {}
        for site in _ordered_sites(sites):
            ref = pinned_image_reference(self.site_lock, site)
            result = self._run(
                ["docker", "image", "inspect", "--format", "{{.Id}}", ref],
                timeout=60,
                label=f"inspect pinned image {site}",
            )
            image_id = result.stdout.strip()
            if not image_id.startswith("sha256:") or not HEX_SHA256.fullmatch(image_id.removeprefix("sha256:")):
                raise WebArenaSiteError(f"invalid local image ID for {site}")
            verified[site] = {"reference": ref, "image_id": image_id}
        return verified

    def verify_runtime_sources(self) -> dict[str, Any]:
        """Verify both independently pinned codebases and the installed WV version."""

        official_root = str(self.site_lock["official_source_root"])
        runner_root = str(self.site_lock["runner_root"])
        official_commit = self._run(
            ["git", "-C", official_root, "rev-parse", "HEAD"],
            timeout=30,
            label="verify official WebArena-Verified source commit",
        ).stdout.strip()
        runner_commit = self._run(
            ["git", "-C", runner_root, "rev-parse", "HEAD"],
            timeout=30,
            label="verify original runner source commit",
        ).stdout.strip()
        if official_commit != self.site_lock["official_commit"]:
            raise WebArenaSiteError("remote WebArena-Verified source commit is not pinned v1.2.3")
        if runner_commit != self.site_lock["runner_commit"]:
            raise WebArenaSiteError("remote original WebArena runner source commit mismatch")

        python = str(self.site_lock["official_runtime_python"])
        version_script = (
            "import importlib.metadata as m; "
            "print(m.version('webarena-verified'))"
        )
        version = self._run(
            [python, "-c", version_script],
            timeout=30,
            label="verify installed WebArena-Verified version",
        ).stdout.strip()
        if version != "1.2.3":
            raise WebArenaSiteError(f"installed WebArena-Verified version is {version!r}, expected '1.2.3'")
        return {
            "official_source_root": official_root,
            "official_commit": official_commit,
            "installed_version": version,
            "runner_root": runner_root,
            "runner_commit": runner_commit,
        }

    def verify_map_seed_volumes(self) -> dict[str, dict[str, Any]]:
        """Require every preserved map seed volume to exist and be non-empty.

        These volumes are populated once from the hash-locked archives.  They
        are deliberately preserved across slots; only the map website DB,
        generated tiles, and style volumes are recreated for each map slot.
        """

        spec = self.site_lock["sites"]["map"]
        mutable = set(str(value) for value in (spec.get("mutable_volumes") or []))
        preserved = [
            str(volume["source"])
            for volume in spec.get("volumes") or []
            if volume.get("kind") == "volume" and str(volume["source"]) not in mutable
        ]
        verified: dict[str, dict[str, Any]] = {}
        check_script = (
            "import os,pathlib,sys\n"
            "p=pathlib.Path(sys.argv[1])\n"
            "if not p.is_dir(): raise SystemExit('mountpoint-missing')\n"
            "try: first=next(os.scandir(p))\n"
            "except StopIteration: raise SystemExit('volume-empty')\n"
            "print(first.name)\n"
        )
        for name in preserved:
            mountpoint = self._run(
                ["docker", "volume", "inspect", "--format", "{{.Mountpoint}}", name],
                timeout=30,
                label=f"inspect preserved map volume {name}",
            ).stdout.strip()
            if not mountpoint.startswith("/"):
                raise WebArenaSiteError(f"invalid Docker volume mountpoint: {name}")
            first_entry = self._run(
                ["python3", "-c", check_script, mountpoint],
                timeout=30,
                label=f"verify preserved map volume is populated: {name}",
            ).stdout.strip()
            verified[name] = {
                "mountpoint": mountpoint,
                "non_empty": True,
                "first_entry_name_sha256": hashlib.sha256(first_entry.encode("utf-8")).hexdigest(),
                "reset_policy": "preserve_seed_data",
            }
        return verified

    def read_data_lock(self) -> dict[str, Any]:
        path = str(self.site_lock["data_sha256_lock"])
        code = "import pathlib,sys; print(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))"
        result = self._run(["python3", "-c", code, path], timeout=30, label="read data SHA256 lock")
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise WebArenaSiteError("remote data SHA256 lock is not valid JSON") from exc
        if not isinstance(payload, Mapping):
            raise WebArenaSiteError("remote data SHA256 lock must be an object")
        return load_data_sha256_lock(payload, site_lock=self.site_lock)

    def verify_data_assets(
        self,
        sites: Sequence[str] = ("wikipedia", "map"),
        *,
        full_sha256: bool = True,
    ) -> dict[str, dict[str, Any]]:
        selected = set(_ordered_sites(sites))
        required = {
            filename: entry
            for filename, entry in self.site_lock["data_assets"].items()
            if selected.intersection(entry["sites"])
        }
        if not required:
            return {}
        data_lock = self.read_data_lock()
        root = str(self.site_lock["data_root"])
        script = (
            "import hashlib,json,pathlib,sys\n"
            "root=pathlib.Path(sys.argv[1]); specs=json.loads(sys.argv[2]); do_hash=sys.argv[3]=='1'\n"
            "out={}\n"
            "for name,spec in specs.items():\n"
            " p=root/name\n"
            " if not p.is_file() or p.is_symlink(): raise SystemExit('missing-or-symlink:'+name)\n"
            " size=p.stat().st_size\n"
            " if size != int(spec['size_bytes']): raise SystemExit('size-mismatch:'+name)\n"
            " row={'size_bytes':size}\n"
            " if do_hash:\n"
            "  h=hashlib.sha256()\n"
            "  with p.open('rb') as f:\n"
            "   for chunk in iter(lambda:f.read(8*1024*1024),b''): h.update(chunk)\n"
            "  row['sha256']=h.hexdigest()\n"
            " out[name]=row\n"
            "print(json.dumps(out,sort_keys=True))\n"
        )
        expected = {
            name: {
                "size_bytes": int(spec["size_bytes"]),
                "sha256": str(data_lock["assets"][name]["sha256"]),
            }
            for name, spec in required.items()
        }
        timeout = 7200 if full_sha256 else 120
        result = self._run(
            ["python3", "-c", script, root, json.dumps(expected, sort_keys=True), "1" if full_sha256 else "0"],
            timeout=timeout,
            label="verify locked site data",
        )
        try:
            actual = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise WebArenaSiteError("site data verification returned invalid JSON") from exc
        for name, expected_entry in expected.items():
            row = actual.get(name)
            if not isinstance(row, Mapping) or int(row.get("size_bytes") or -1) != expected_entry["size_bytes"]:
                raise WebArenaSiteError(f"verified data size mismatch: {name}")
            if full_sha256 and row.get("sha256") != expected_entry["sha256"]:
                raise WebArenaSiteError(f"verified data SHA256 mismatch: {name}")
        return dict(actual)

    def status(self, sites: Sequence[str] = SITE_ORDER) -> dict[str, Any]:
        selected = _ordered_sites(sites)
        images = self.verify_images(selected)
        rows = [self._container_status(site, images[site]["image_id"]) for site in selected]
        ok = all(bool(row["ok"]) for row in rows)
        return {
            "schema_version": "webarena_verified_site_status/v1",
            "status": "pass" if ok else "fail",
            "checked_at": utc_now(),
            "machine_id": self.machine_id,
            "ssh_host": self.ssh_host,
            "site_lock_sha256": _sha256_json(self.site_lock),
            "sites": rows,
        }

    def reset_slot(
        self,
        *,
        identity: SlotIdentity,
        sites: Sequence[str],
        receipt_path: str | Path,
    ) -> dict[str, Any]:
        selected = _ordered_sites(sites)
        if not selected:
            raise WebArenaSiteError("slot reset requires at least one site")
        started = utc_now()
        started_monotonic = time.monotonic()
        receipt: dict[str, Any] = {
            "schema_version": RESET_RECEIPT_SCHEMA,
            "status": "in_progress",
            "slot": {
                "slot_id": identity.slot_id,
                "task_id": int(identity.task_id),
                "agent_id": identity.agent_id,
                "attempt_id": identity.attempt_id,
                "seed": int(identity.seed),
            },
            "machine": {
                "machine_id": self.machine_id,
                "ssh_host": self.ssh_host,
                "ssh_host_fingerprint": self.ssh_host_fingerprint,
            },
            "site_lock_sha256": _sha256_json(self.site_lock),
            "reset_scope": selected,
            "started_at": started,
            "completed_at": None,
            "duration_seconds": None,
            "exclusive_lock": {
                "path": self.site_lock["slot_lock_file"],
                "acquired_at": None,
                "released_at": None,
            },
            "sites": [],
            "fail_closed": None,
            "error": None,
        }
        lock_token: str | None = None
        try:
            lock_token = self._acquire_exclusive_lock(
                owner={
                    "operation": "slot_reset",
                    "slot_id": identity.slot_id,
                    "task_id": int(identity.task_id),
                    "agent_id": identity.agent_id,
                }
            )
            receipt["exclusive_lock"]["acquired_at"] = utc_now()
            image_rows = self.verify_images(selected)
            for site in selected:
                receipt["sites"].append(self._reset_site(site, expected_image_id=image_rows[site]["image_id"]))
            receipt["status"] = "pass"
        except Exception as exc:
            receipt["status"] = "fail"
            receipt["error"] = {"type": type(exc).__name__, "message": _safe_error(str(exc))}
        if receipt["status"] != "pass" and lock_token is not None:
            receipt["fail_closed"] = self._quarantine_sites(selected)
        if lock_token is not None:
            try:
                self._release_exclusive_lock(lock_token)
                receipt["exclusive_lock"]["released_at"] = utc_now()
            except Exception as exc:
                if receipt["status"] == "pass":
                    receipt["status"] = "fail"
                    receipt["error"] = {"type": type(exc).__name__, "message": _safe_error(str(exc))}
                    receipt["fail_closed"] = self._quarantine_sites(selected)
        receipt["completed_at"] = utc_now()
        receipt["duration_seconds"] = round(time.monotonic() - started_monotonic, 3)
        atomic_write_json(receipt_path, receipt)
        if receipt["status"] != "pass":
            raise WebArenaSiteError(f"slot reset failed; receipt={receipt_path}: {receipt['error']['message']}")
        return receipt

    def deployment_receipt(
        self,
        *,
        receipt_path: str | Path,
        verify_full_data_sha256: bool = True,
    ) -> dict[str, Any]:
        started = utc_now()
        receipt: dict[str, Any] = {
            "schema_version": DEPLOYMENT_RECEIPT_SCHEMA,
            "status": "in_progress",
            "machine_id": self.machine_id,
            "ssh_host": self.ssh_host,
            "ssh_host_fingerprint": self.ssh_host_fingerprint,
            "site_lock_sha256": _sha256_json(self.site_lock),
            "started_at": started,
            "completed_at": None,
            "runtime_sources": None,
            "images": {},
            "data_assets": {},
            "map_seed_volumes": {},
            "sites": [],
            "login": None,
            "error": None,
        }
        try:
            receipt["runtime_sources"] = self.verify_runtime_sources()
            receipt["images"] = self.verify_images()
            receipt["data_assets"] = self.verify_data_assets(full_sha256=verify_full_data_sha256)
            receipt["map_seed_volumes"] = self.verify_map_seed_volumes()
            status = self.status()
            if status["status"] != "pass":
                raise WebArenaSiteError("one or more deployed sites failed status checks")
            receipt["sites"] = status["sites"]
            receipt["login"] = self.verify_login()
            receipt["status"] = "pass"
        except Exception as exc:
            receipt["status"] = "fail"
            receipt["error"] = {"type": type(exc).__name__, "message": _safe_error(str(exc))}
        receipt["completed_at"] = utc_now()
        atomic_write_json(receipt_path, receipt)
        if receipt["status"] != "pass":
            raise WebArenaSiteError(f"site deployment acceptance failed; receipt={receipt_path}")
        return receipt

    def deploy_and_accept(
        self,
        *,
        receipt_path: str | Path,
        verify_full_data_sha256: bool = True,
    ) -> dict[str, Any]:
        """Start all six pinned sites from clean state and run acceptance.

        Image pulls, large-file downloads, and map seed-volume extraction are
        intentionally separate provisioning operations.  This gate accepts
        only assets already present under their locks, then recreates every
        site container before login/sentinel verification.
        """

        started_monotonic = time.monotonic()
        receipt: dict[str, Any] = {
            "schema_version": DEPLOYMENT_RECEIPT_SCHEMA,
            "operation": "deploy_and_accept",
            "status": "in_progress",
            "machine_id": self.machine_id,
            "ssh_host": self.ssh_host,
            "ssh_host_fingerprint": self.ssh_host_fingerprint,
            "site_lock_sha256": _sha256_json(self.site_lock),
            "started_at": utc_now(),
            "completed_at": None,
            "duration_seconds": None,
            "exclusive_lock": {
                "path": self.site_lock["slot_lock_file"],
                "acquired_at": None,
                "released_at": None,
            },
            "runtime_sources": None,
            "images": {},
            "data_assets": {},
            "map_seed_volumes": {},
            "resets": [],
            "sites": [],
            "login": None,
            "fail_closed": None,
            "error": None,
        }
        lock_token: str | None = None
        try:
            lock_token = self._acquire_exclusive_lock(
                owner={"operation": "deploy_and_accept", "machine_id": self.machine_id}
            )
            receipt["exclusive_lock"]["acquired_at"] = utc_now()
            receipt["runtime_sources"] = self.verify_runtime_sources()
            receipt["images"] = self.verify_images()
            receipt["data_assets"] = self.verify_data_assets(full_sha256=verify_full_data_sha256)
            receipt["map_seed_volumes"] = self.verify_map_seed_volumes()
            for site in SITE_ORDER:
                receipt["resets"].append(
                    self._reset_site(site, expected_image_id=receipt["images"][site]["image_id"])
                )
            status = self.status()
            if status["status"] != "pass":
                raise WebArenaSiteError("one or more freshly deployed sites failed status checks")
            receipt["sites"] = status["sites"]
            receipt["login"] = self.verify_login()
            receipt["status"] = "pass"
        except Exception as exc:
            receipt["status"] = "fail"
            receipt["error"] = {"type": type(exc).__name__, "message": _safe_error(str(exc))}

        if receipt["status"] != "pass" and lock_token is not None:
            receipt["fail_closed"] = self._quarantine_sites(SITE_ORDER)
        if lock_token is not None:
            try:
                self._release_exclusive_lock(lock_token)
                receipt["exclusive_lock"]["released_at"] = utc_now()
            except Exception as exc:
                if receipt["status"] == "pass":
                    receipt["status"] = "fail"
                    receipt["error"] = {"type": type(exc).__name__, "message": _safe_error(str(exc))}
                    receipt["fail_closed"] = self._quarantine_sites(SITE_ORDER)
        receipt["completed_at"] = utc_now()
        receipt["duration_seconds"] = round(time.monotonic() - started_monotonic, 3)
        atomic_write_json(receipt_path, receipt)
        if receipt["status"] != "pass":
            raise WebArenaSiteError(f"site deployment failed closed; receipt={receipt_path}")
        return receipt

    def verify_login(self) -> dict[str, Any]:
        """Run the pinned original runner's self-checking login utility.

        Cookie files remain in a mode-0700 temporary directory and are removed
        before the command exits.  No cookie values or credentials enter the
        receipt.

        The upstream ``--site_list all`` implementation submits renewals to a
        thread pool but never observes those futures.  A failed renewal can
        therefore be silently omitted while the CLI still exits zero.  Drive
        the exact eight combinations supported by that implementation one at
        a time so every renewal failure is observable, then reuse its
        authenticated-page predicate for every site in every generated state.

        The runner venv's Playwright otherwise falls back to root's empty
        user cache.  The environment acceptance installs the pinned browser
        payload beside the official source tree, so bind that deterministic
        cache explicitly for both renewal subprocesses and page probes.
        """

        runner = str(self.site_lock["runner_root"])
        python = f"{runner}/.venv/bin/python"
        playwright_browsers_path = str(
            Path(str(self.site_lock["official_source_root"])).parent / "ms-playwright"
        )
        script = (
            "import json,math,os,pathlib,shutil,subprocess,tempfile,time\n"
            "runner=pathlib.Path(os.environ['WA_RUNNER'])\n"
            "browser_cache=pathlib.Path(os.environ['PLAYWRIGHT_BROWSERS_PATH'])\n"
            "if not browser_cache.is_dir(): raise SystemExit('login-probe-browser-cache-missing')\n"
            "folder=pathlib.Path(tempfile.mkdtemp(prefix='webarena-login-',dir='/tmp'))\n"
            "os.chmod(folder,0o700)\n"
            "try:\n"
            " combinations=(('gitlab','shopping'),('gitlab','shopping_admin'),('gitlab','reddit'),('shopping','shopping_admin'),('gitlab',),('shopping',),('shopping_admin',),('reddit',))\n"
            " required={'.'.join(comb)+'_state.json' for comb in combinations}\n"
            " for comb in combinations:\n"
            "  p=subprocess.run([os.environ['WA_PYTHON'],'browser_env/auto_login.py','--site_list',*comb,'--auth_folder',str(folder)],cwd=runner,env=os.environ,capture_output=True,text=True,timeout=180)\n"
            "  if p.returncode: raise SystemExit('login-probe-renewal-failed:'+('+'.join(comb)))\n"
            " files={x.name for x in folder.glob('*_state.json')}\n"
            " if files!=required: raise SystemExit('login-probe-state-set-mismatch')\n"
            " from browser_env import auto_login as official_login\n"
            " authenticated_page_probe_count=0\n"
            " for comb in combinations:\n"
            "  state_path=folder/('.'.join(comb)+'_state.json')\n"
            "  for site in comb:\n"
            "   index=official_login.SITES.index(site)\n"
            "   if official_login.is_expired(state_path,official_login.URLS[index],official_login.KEYWORDS[index],official_login.EXACT_MATCH[index]): raise SystemExit('login-state-authenticated-page-failed:'+site)\n"
            "   authenticated_page_probe_count+=1\n"
            " validation_now=time.time()\n"
            " totals={'cookie_count':0,'associated_cookie_count':0,'associated_nonempty_cookie_count':0,'effective_associated_nonempty_cookie_count':0,'empty_cookie_count':0,'expired_empty_cookie_count':0,'nonempty_cookie_count':0,'persistent_cookie_count':0,'session_cookie_count':0}\n"
            " for name in sorted(required):\n"
            "  try: state=json.loads((folder/name).read_text())\n"
            "  except Exception: raise SystemExit('login-state-invalid-json')\n"
            "  if not isinstance(state,dict) or not isinstance(state.get('cookies'),list) or not state['cookies']: raise SystemExit('login-state-empty-cookies')\n"
            "  effective_associated_nonempty=0\n"
            "  for cookie in state['cookies']:\n"
            "   if not isinstance(cookie,dict): raise SystemExit('login-state-invalid-cookie-schema')\n"
            "   cookie_name=cookie.get('name'); value=cookie.get('value'); raw_domain=cookie.get('domain'); path=cookie.get('path'); http_only=cookie.get('httpOnly'); secure=cookie.get('secure'); same_site=cookie.get('sameSite')\n"
            "   if not isinstance(cookie_name,str) or not cookie_name or not isinstance(value,str) or not isinstance(raw_domain,str) or not raw_domain or not isinstance(path,str) or not path.startswith('/') or type(http_only) is not bool or type(secure) is not bool or same_site not in {'Lax','None','Strict'}: raise SystemExit('login-state-invalid-cookie-schema')\n"
            "   raw_expires=cookie.get('expires')\n"
            "   if isinstance(raw_expires,bool) or not isinstance(raw_expires,(int,float)) or not math.isfinite(float(raw_expires)): raise SystemExit('login-state-invalid-expiry')\n"
            "   expires=float(raw_expires); domain=raw_domain.lstrip('.').lower(); associated=(domain=='127.0.0.1' or '127.0.0.1'.endswith('.'+domain)); nonempty=bool(value)\n"
            "   if associated: totals['associated_cookie_count']+=1\n"
            "   if nonempty:\n"
            "    totals['nonempty_cookie_count']+=1\n"
            "    if associated: totals['associated_nonempty_cookie_count']+=1\n"
            "   else: totals['empty_cookie_count']+=1\n"
            "   if expires>0:\n"
            "    totals['persistent_cookie_count']+=1\n"
            "    if expires<=validation_now:\n"
            "     if nonempty: raise SystemExit('login-state-expired-nonempty-cookie')\n"
            "     totals['expired_empty_cookie_count']+=1\n"
            "   else: totals['session_cookie_count']+=1\n"
            "   if associated and nonempty and (expires<=0 or expires>validation_now):\n"
            "    effective_associated_nonempty+=1\n"
            "    totals['effective_associated_nonempty_cookie_count']+=1\n"
            "  if effective_associated_nonempty<1: raise SystemExit('login-state-no-effective-associated-cookie')\n"
            "  if not isinstance(state.get('origins',[]),list): raise SystemExit('login-state-invalid-origins')\n"
            "  totals['cookie_count']+=len(state['cookies'])\n"
            " totals['file_count']=len(files)\n"
            " totals['authenticated_page_probe_count']=authenticated_page_probe_count\n"
            " print(json.dumps(totals,sort_keys=True))\n"
            "finally:\n"
            " shutil.rmtree(folder,ignore_errors=True)\n"
        )
        env_prefix = [
            "env",
            f"WA_RUNNER={runner}",
            f"WA_PYTHON={python}",
            f"PLAYWRIGHT_BROWSERS_PATH={playwright_browsers_path}",
            "SHOPPING=http://127.0.0.1:7770",
            "SHOPPING_ADMIN=http://127.0.0.1:7780/admin",
            "REDDIT=http://127.0.0.1:9999",
            "GITLAB=http://127.0.0.1:8023",
            "WIKIPEDIA=http://127.0.0.1:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing",
            "MAP=http://127.0.0.1:3030",
            "HOMEPAGE=PASS",
        ]
        result = self.run_remote([*env_prefix, python, "-c", script], 1800)
        if result.returncode != 0:
            error_code = _safe_login_probe_error_code(result.stdout, result.stderr)
            raise WebArenaSiteError(
                f"official login probe failed (rc={result.returncode}): {error_code}"
            )
        try:
            summary = json.loads(result.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError) as exc:
            raise WebArenaSiteError("official login probe returned invalid receipt") from exc
        count_keys = (
            "file_count",
            "authenticated_page_probe_count",
            "cookie_count",
            "associated_cookie_count",
            "associated_nonempty_cookie_count",
            "effective_associated_nonempty_cookie_count",
            "empty_cookie_count",
            "expired_empty_cookie_count",
            "nonempty_cookie_count",
            "persistent_cookie_count",
            "session_cookie_count",
        )
        if not isinstance(summary, Mapping) or any(
            type(summary.get(key)) is not int or summary[key] < 0 for key in count_keys
        ):
            raise WebArenaSiteError("official login probe returned invalid receipt")
        file_count = summary["file_count"]
        authenticated_page_probe_count = summary["authenticated_page_probe_count"]
        cookie_count = summary["cookie_count"]
        associated_cookie_count = summary["associated_cookie_count"]
        associated_nonempty_cookie_count = summary["associated_nonempty_cookie_count"]
        effective_associated_nonempty_cookie_count = summary[
            "effective_associated_nonempty_cookie_count"
        ]
        empty_cookie_count = summary["empty_cookie_count"]
        expired_empty_cookie_count = summary["expired_empty_cookie_count"]
        nonempty_cookie_count = summary["nonempty_cookie_count"]
        persistent_count = summary["persistent_cookie_count"]
        session_count = summary["session_cookie_count"]
        if (
            file_count != 8
            or authenticated_page_probe_count != 12
            or cookie_count <= 0
            or effective_associated_nonempty_cookie_count < file_count
            or associated_nonempty_cookie_count != effective_associated_nonempty_cookie_count
            or associated_cookie_count < associated_nonempty_cookie_count
            or empty_cookie_count + nonempty_cookie_count != cookie_count
            or expired_empty_cookie_count > empty_cookie_count
            or persistent_count + session_count != cookie_count
        ):
            raise WebArenaSiteError("official login probe returned incomplete validation counts")
        return {
            "status": "pass",
            "playwright_browsers_path": playwright_browsers_path,
            "method": (
                "sequential pinned original-runner auto_login renewal for every upstream-supported "
                "state combination, its authenticated-page assertions for every state/site, plus "
                "Playwright cookie schema/domain/expiry validation with legal zero-length cookies counted "
                "but excluded from the effective authentication-cookie gate"
            ),
            "required_sites": ["shopping", "shopping_admin", "reddit", "gitlab"],
            "required_state_combinations": [
                "gitlab+shopping",
                "gitlab+shopping_admin",
                "gitlab+reddit",
                "shopping+shopping_admin",
                "gitlab",
                "shopping",
                "shopping_admin",
                "reddit",
            ],
            "generated_state_file_count": file_count,
            "validated_authenticated_page_probe_count": authenticated_page_probe_count,
            "validated_cookie_count": cookie_count,
            "validated_associated_cookie_count": associated_cookie_count,
            "validated_associated_nonempty_cookie_count": associated_nonempty_cookie_count,
            "validated_effective_associated_nonempty_cookie_count": (
                effective_associated_nonempty_cookie_count
            ),
            "validated_empty_cookie_count": empty_cookie_count,
            "validated_expired_empty_cookie_count": expired_empty_cookie_count,
            "validated_nonempty_cookie_count": nonempty_cookie_count,
            "validated_persistent_cookie_count": persistent_count,
            "validated_session_cookie_count": session_count,
            "authenticated_page_probes": [
                "shopping:/wishlist/ exact URL",
                "shopping_admin:/dashboard with Dashboard marker",
                "reddit:/user/<locked-account>/account with Delete marker",
                "gitlab:/-/profile exact URL",
            ],
            "sensitive_state_retained": False,
        }

    def _acquire_exclusive_lock(self, *, owner: Mapping[str, Any]) -> str:
        path = str(self.site_lock["slot_lock_file"])
        token = secrets.token_hex(32)
        owner_payload = {
            "schema_version": "webarena_verified_remote_lock/v1",
            "token": token,
            "machine_id": self.machine_id,
            "ssh_host": self.ssh_host,
            "acquired_at": utc_now(),
            "owner": dict(owner),
        }
        script = (
            "import json,os,pathlib,sys\n"
            "p=pathlib.Path(sys.argv[1]); payload=sys.argv[2]\n"
            "p.parent.mkdir(parents=True,exist_ok=True)\n"
            "try: fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)\n"
            "except FileExistsError: raise SystemExit('exclusive-slot-lock-busy')\n"
            "try:\n"
            " os.write(fd,(payload+'\\n').encode())\n"
            " os.fsync(fd)\n"
            "finally: os.close(fd)\n"
            "print('acquired')\n"
        )
        self._run(
            ["python3", "-c", script, path, json.dumps(owner_payload, sort_keys=True)],
            timeout=30,
            label="acquire exclusive WebArena slot lock",
        )
        return token

    def _release_exclusive_lock(self, token: str) -> None:
        path = str(self.site_lock["slot_lock_file"])
        script = (
            "import json,pathlib,sys\n"
            "p=pathlib.Path(sys.argv[1])\n"
            "try: payload=json.loads(p.read_text())\n"
            "except Exception: raise SystemExit('exclusive-slot-lock-unreadable')\n"
            "if payload.get('token') != sys.argv[2]: raise SystemExit('exclusive-slot-lock-owner-mismatch')\n"
            "p.unlink()\n"
            "print('released')\n"
        )
        self._run(
            ["python3", "-c", script, path, token],
            timeout=30,
            label="release exclusive WebArena slot lock",
        )

    def _quarantine_sites(self, sites: Sequence[str]) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        all_removed = True
        for site in _ordered_sites(sites):
            name = str(self.site_lock["sites"][site]["container_name"])
            result = self.run_remote(["docker", "rm", "-f", name], 180)
            missing = "no such" in (result.stderr or "").lower() or "not found" in (result.stderr or "").lower()
            ok = result.returncode == 0 or missing
            all_removed = all_removed and ok
            rows.append(
                {
                    "site": site,
                    "container_name": name,
                    "removed_or_absent": ok,
                    "returncode": int(result.returncode),
                }
            )
        return {
            "status": "pass" if all_removed else "fail",
            "policy": "all selected containers removed; agent execution prohibited",
            "completed_at": utc_now(),
            "sites": rows,
        }

    def _reset_site(self, site: str, *, expected_image_id: str) -> dict[str, Any]:
        spec = self.site_lock["sites"][site]
        name = str(spec["container_name"])
        before = self._inspect_container(name)
        reset_started = utc_now()
        reset_monotonic = time.monotonic()

        self._run(["docker", "rm", "-f", name], timeout=180, label=f"remove {site} container", allow_missing=True)
        restored_volumes: list[str] = []
        for volume in spec.get("mutable_volumes") or []:
            self._run(["docker", "volume", "rm", "-f", str(volume)], timeout=180, label=f"remove {site} mutable volume")
            self._run(["docker", "volume", "create", str(volume)], timeout=60, label=f"create {site} mutable volume")
            restored_volumes.append(str(volume))

        self._run(
            container_run_argv(self.site_lock, site),
            timeout=180,
            label=f"start pinned {site} container",
        )
        checks = self._wait_for_site(site)
        after = self._inspect_container(name)
        if after is None or not after["running"]:
            raise WebArenaSiteError(f"{site} container is not running after reset")
        if after["image_id"] != expected_image_id:
            raise WebArenaSiteError(f"{site} container image ID differs from pinned image")
        if before is not None and before["container_id"] == after["container_id"]:
            raise WebArenaSiteError(f"{site} reset did not replace the container")
        return {
            "site": site,
            "image_reference": pinned_image_reference(self.site_lock, site),
            "expected_image_id": expected_image_id,
            "before": before,
            "after": after,
            "mutable_volumes_restored": restored_volumes,
            "sentinels": checks,
            "started_at": reset_started,
            "completed_at": utc_now(),
            "duration_seconds": round(time.monotonic() - reset_monotonic, 3),
            "ok": True,
        }

    def _container_status(self, site: str, expected_image_id: str) -> dict[str, Any]:
        spec = self.site_lock["sites"][site]
        try:
            inspected = self._inspect_container(str(spec["container_name"]))
        except WebArenaSiteError as exc:
            return {"site": site, "ok": False, "reason": _safe_error(str(exc))}
        if inspected is None:
            return {"site": site, "ok": False, "reason": "container_missing"}
        try:
            checks = self._wait_for_site(site, attempts=1)
        except WebArenaSiteError as exc:
            return {
                "site": site,
                "ok": False,
                "reason": _safe_error(str(exc)),
                "expected_image_reference": pinned_image_reference(self.site_lock, site),
                "expected_image_id": expected_image_id,
                "container": inspected,
                "sentinels": [],
            }
        ok = bool(inspected["running"]) and inspected["image_id"] == expected_image_id and all(
            bool(check["ok"]) for check in checks
        )
        return {
            "site": site,
            "ok": ok,
            "expected_image_reference": pinned_image_reference(self.site_lock, site),
            "expected_image_id": expected_image_id,
            "container": inspected,
            "sentinels": checks,
        }

    def _inspect_container(self, name: str) -> dict[str, Any] | None:
        result = self.run_remote(
            [
                "docker",
                "inspect",
                "--format",
                "{{.Id}}|{{.Image}}|{{.State.Running}}|{{.State.StartedAt}}",
                name,
            ],
            30,
        )
        if result.returncode != 0:
            stderr = (result.stderr or "").lower()
            if "no such" in stderr or "not found" in stderr:
                return None
            raise WebArenaSiteError(f"docker inspect failed for {name}: {_safe_error(result.stderr)}")
        fields = result.stdout.strip().split("|", 3)
        if len(fields) != 4:
            raise WebArenaSiteError(f"invalid docker inspect output for {name}")
        ports = self._run(["docker", "port", name], timeout=30, label=f"inspect {name} ports").stdout.splitlines()
        if not ports or any("127.0.0.1:" not in line for line in ports):
            raise WebArenaSiteError(f"{name} has a non-loopback or missing port binding")
        return {
            "container_id": fields[0],
            "image_id": fields[1],
            "running": fields[2].lower() == "true",
            "started_at": fields[3],
            "port_bindings": sorted(line.strip() for line in ports if line.strip()),
        }

    def _wait_for_site(self, site: str, *, attempts: int | None = None) -> list[dict[str, Any]]:
        spec = self.site_lock["sites"][site]
        timeout = int(spec["startup_timeout_seconds"])
        deadline = time.monotonic() + timeout
        maximum_attempts = attempts
        attempt = 0
        last_error = "not checked"
        while True:
            attempt += 1
            try:
                checks = self._site_checks(site)
                if all(bool(check["ok"]) for check in checks):
                    return checks
                last_error = ", ".join(check["name"] for check in checks if not check["ok"])
            except WebArenaSiteError as exc:
                last_error = str(exc)
            if maximum_attempts is not None and attempt >= maximum_attempts:
                break
            if time.monotonic() >= deadline:
                break
            time.sleep(min(5.0, max(0.1, deadline - time.monotonic())))
        raise WebArenaSiteError(f"{site} failed readiness checks: {_safe_error(last_error)}")

    def _site_checks(self, site: str) -> list[dict[str, Any]]:
        spec = self.site_lock["sites"][site]
        name = str(spec["container_name"])
        # The pinned map image's env-ctrl status implementation waits for
        # /run/supervisord.sock, but that image does not configure a
        # supervisor control socket.  Calling it can therefore block for
        # several internal retry windows even when every map service is
        # healthy.  For map we verify the underlying services directly below;
        # the other five images retain the official env-ctrl status gate.
        env_ctrl = None
        if site != "map":
            env_ctrl = self._run(
                ["docker", "exec", name, "env-ctrl", "status"],
                timeout=60,
                label=f"{site} env-ctrl status",
            )
        code = (
            "import sys,urllib.request\n"
            "with urllib.request.urlopen(sys.argv[1],timeout=float(sys.argv[3])) as r:\n"
            " body=r.read(1048576).decode('utf-8','replace'); status=r.status\n"
            "if sys.argv[2] not in body: raise SystemExit('missing-sentinel')\n"
            "print(status)\n"
        )
        homepage = self._run(
            ["python3", "-c", code, str(spec["health_url"]), str(spec["health_needle"]), "30"],
            timeout=40,
            label=f"{site} homepage sentinel",
        )
        checks: list[dict[str, Any]] = []
        if env_ctrl is not None:
            checks.append({"name": "env_ctrl_status", "ok": env_ctrl.returncode == 0})
        checks.append(
            {"name": "homepage", "ok": homepage.stdout.strip().splitlines()[-1:] == ["200"]}
        )
        if site == "shopping_admin":
            query = (
                "SELECT DISTINCT rd.nickname FROM review_detail rd JOIN review r ON r.review_id=rd.review_id "
                "JOIN rating_option_vote rov ON rov.review_id=r.review_id "
                "JOIN catalog_product_entity_varchar cpev ON cpev.entity_id=r.entity_pk_value "
                "AND cpev.attribute_id=73 AND cpev.store_id=0 "
                "WHERE cpev.value='Circe Hooded Ice Fleece' AND rov.value<=3 ORDER BY rd.nickname ASC"
            )
            sentinel = self._run(
                [
                    "docker",
                    "exec",
                    name,
                    "mysql",
                    "-N",
                    "-B",
                    "-umagentouser",
                    "-pMyPassword",
                    "magentodb",
                    "-e",
                    query,
                ],
                timeout=90,
                label="shopping_admin database sentinel",
            )
            checks.append(
                {
                    "name": "shopping_admin_reviews",
                    "ok": [line.strip() for line in sentinel.stdout.splitlines() if line.strip()] == ["Hannah Lim"],
                }
            )
        if site == "map":
            service_probe = (
                "import json,os,socket,sys,urllib.request\n"
                "def fetch(url,timeout=30):\n"
                " with urllib.request.urlopen(url,timeout=timeout) as r:\n"
                "  return r.status,dict(r.headers),r.read(1048576)\n"
                "cmdlines=[]\n"
                "for entry in os.scandir('/proc'):\n"
                " if not entry.name.isdigit(): continue\n"
                " try: cmdlines.append(open(entry.path+'/cmdline','rb').read().replace(b'\\0',b' ').decode('utf-8','replace'))\n"
                " except OSError: pass\n"
                "joined='\\n'.join(cmdlines)\n"
                "process_markers=['environment_control.cli serve','puma 5.6.5','osrm-routed','renderd -f']\n"
                "processes=all(marker in joined for marker in process_markers)\n"
                "ports=[]\n"
                "for port in (5432,5433,5434):\n"
                " try:\n"
                "  with socket.create_connection(('127.0.0.1',port),timeout=5): pass\n"
                "  ports.append(True)\n"
                " except OSError: ports.append(False)\n"
                "rails_status,_,rails_body=fetch('http://127.0.0.1:3000/',30)\n"
                "osrm=[]\n"
                "for profile,port in [('car',5000),('bike',5001),('foot',5002)]:\n"
                " status,_,body=fetch(f'http://127.0.0.1:{port}/route/v1/{profile}/-74.006,40.7128;-73.95,40.72',30)\n"
                " try: payload=json.loads(body)\n"
                " except Exception: payload={}\n"
                " osrm.append(status==200 and payload.get('code')=='Ok' and bool(payload.get('routes')))\n"
                "tile_status,tile_headers,tile_body=fetch('http://127.0.0.1:8080/tile/12/1205/1539.png',180)\n"
                "tile_type=str(tile_headers.get('Content-Type','')).lower()\n"
                "nom_status,_,nom_body=fetch('http://127.0.0.1:8080/nominatim/search?q=New+York&format=json&limit=1',30)\n"
                "try: nom_payload=json.loads(nom_body)\n"
                "except Exception: nom_payload=[]\n"
                "print(json.dumps({'env_ctrl_process':processes,'postgres_ports':all(ports),'rails':rails_status==200 and b'OpenStreetMap' in rails_body,'osrm_profiles':all(osrm),'tile_png':tile_status==200 and 'image/png' in tile_type and tile_body.startswith(b'\\x89PNG\\r\\n\\x1a\\n'),'nominatim':nom_status==200 and isinstance(nom_payload,list) and bool(nom_payload)},sort_keys=True))\n"
            )
            service_result = self._run(
                ["docker", "exec", name, "python3", "-c", service_probe],
                timeout=240,
                label="map direct service sentinels",
            )
            try:
                service_payload = json.loads(service_result.stdout)
            except json.JSONDecodeError as exc:
                raise WebArenaSiteError("map direct service sentinels returned invalid JSON") from exc
            for sentinel_name, field in (
                ("map_env_ctrl_process", "env_ctrl_process"),
                ("map_postgres_ports", "postgres_ports"),
                ("map_rails", "rails"),
                ("map_osrm_profiles", "osrm_profiles"),
                ("map_tile_png", "tile_png"),
                ("map_nominatim", "nominatim"),
            ):
                checks.append(
                    {
                        "name": sentinel_name,
                        "ok": service_payload.get(field) is True,
                    }
                )
            route_url = (
                "http://127.0.0.1:8080/osrm/routed-car/route/v1/driving/"
                "-79.0567,43.0945;-78.9464,43.1073?overview=false&steps=false"
            )
            route_code = (
                "import json,sys,urllib.request\n"
                "with urllib.request.urlopen(sys.argv[1],timeout=30) as r: p=json.load(r)\n"
                "print(p['routes'][0]['distance'])\n"
            )
            route = self._run(
                ["docker", "exec", name, "python3", "-c", route_code, route_url],
                timeout=60,
                label="map route sentinel",
            )
            try:
                distance = float(route.stdout.strip())
            except ValueError:
                distance = None
            checks.append(
                {
                    "name": "map_route_distance",
                    "ok": distance is not None and abs(distance - 10289.9) <= 5.0,
                    "actual_distance_meters": distance,
                }
            )
        return checks

    def _run(
        self,
        argv: Sequence[str],
        *,
        timeout: int,
        label: str,
        allow_missing: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        result = self.run_remote([str(item) for item in argv], timeout)
        if result.returncode != 0:
            stderr = (result.stderr or "").lower()
            missing = "no such" in stderr or "not found" in stderr
            if not (allow_missing and missing):
                detail = _safe_error((result.stderr or result.stdout or "").strip())
                raise WebArenaSiteError(f"{label} failed (rc={result.returncode}): {detail}")
        return result


def _ordered_sites(sites: Sequence[str]) -> list[str]:
    values = [str(site) for site in sites]
    if len(values) != len(set(values)) or not set(values) <= set(SITE_ORDER):
        raise WebArenaSiteError("duplicate or unsupported site in reset scope")
    return [site for site in SITE_ORDER if site in set(values)]


def _require_site(site: str) -> None:
    if site not in SITE_ORDER:
        raise WebArenaSiteError(f"unsupported WebArena site: {site}")


def _sha256_json(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _safe_error(value: str | None) -> str:
    text = str(value or "").replace("\n", " ").strip()
    text = re.sub(r"(?i)(password|token|secret|api[_-]?key)\s*[=:]\s*\S+", r"\1=<redacted>", text)
    return text[-600:]


def _safe_login_probe_error_code(stdout: str | None, stderr: str | None) -> str:
    """Return only a fixed, non-sensitive login failure code.

    Playwright imports can emit long dependency warnings before the probe's
    final error.  Never copy that arbitrary diagnostic text into a deployment
    receipt; retain only a code emitted by this controller's injected script.
    """

    combined = f"{stdout or ''}\n{stderr or ''}"
    for code in sorted(_SAFE_LOGIN_PROBE_ERRORS, key=len, reverse=True):
        if code in combined:
            return code
    return "login-probe-remote-failure"


__all__ = [
    "DATA_LOCK_SCHEMA",
    "DEPLOYMENT_RECEIPT_SCHEMA",
    "RESET_RECEIPT_SCHEMA",
    "SITE_LOCK_SCHEMA",
    "SITE_ORDER",
    "SlotIdentity",
    "WebArenaSiteController",
    "WebArenaSiteError",
    "atomic_write_json",
    "container_run_argv",
    "load_data_sha256_lock",
    "load_site_lock",
    "pinned_image_reference",
    "run_verified_ssh_argv",
    "sites_for_agent_input",
    "validate_storage_state_payload",
]
