"""Utilities for resetting and baseline-checking the WebArena VPS runtime."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
import shlex
import subprocess
import time
from typing import Any, Sequence

from evidence_system.contracts.common import load_mapping, normalize_domain
from evidence_system.orchestrator.jobs import InfraBenchmarkTarget, resolve_infra_target


DEFAULT_SITES = ("shopping", "shopping_admin", "reddit", "gitlab", "wikipedia", "map")
DEFAULT_CONTAINER_NAMES = {
    "shopping": "shopping",
    "shopping_admin": "shopping_admin",
    "reddit": "forum",
    "gitlab": "gitlab",
    "wikipedia": "wikipedia",
    "map": "map",
}
DEFAULT_TIMEOUT_SECONDS = 120
MAP_TIMEOUT_SECONDS = 180
PAGE_NEEDLES = {
    "shopping": "One Stop Market",
    "shopping_admin": "Magento Admin",
    "reddit": "Postmill",
    "gitlab": "Sign in · GitLab",
    "wikipedia": "Wikipedia",
    "map": "OpenStreetMap",
}
SHOPPING_ADMIN_REVIEWS_SQL = (
    "SELECT DISTINCT rd.nickname "
    "FROM review_detail rd "
    "JOIN review r ON r.review_id = rd.review_id "
    "JOIN rating_option_vote rov ON rov.review_id = r.review_id "
    "JOIN catalog_product_entity_varchar cpev "
    "  ON cpev.entity_id = r.entity_pk_value "
    " AND cpev.attribute_id = 73 "
    " AND cpev.store_id = 0 "
    "WHERE cpev.value = 'Circe Hooded Ice Fleece' "
    "  AND rov.value <= 3 "
    "ORDER BY rd.nickname ASC"
)
MAP_ROUTE_URL = (
    "http://127.0.0.1:8080/osrm/routed-car/route/v1/driving/"
    "-79.0567,43.0945;-78.9464,43.1073?overview=false&steps=false"
)
MAP_ROUTE_DISTANCE_METERS = 10289.9
MAP_ROUTE_DISTANCE_TOLERANCE = 5.0


@dataclass(frozen=True)
class WebArenaRuntimeSite:
    site: str
    site_url: str
    container_name: str
    reset_command: str | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_system.cli.webarena_runtime",
        description=__doc__,
    )
    parser.add_argument("--infra-config", default="configs/infra.yaml")
    parser.add_argument("--json", action="store_true")

    subparsers = parser.add_subparsers(dest="command", required=True)

    reset_parser = subparsers.add_parser(
        "reset",
        help="Reset selected WebArena site containers using the configured benchmark reset command.",
    )
    reset_parser.add_argument("--json", action="store_true")
    _add_site_args(reset_parser)
    reset_parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    reset_parser.add_argument("--map-timeout-seconds", type=int, default=MAP_TIMEOUT_SECONDS)

    baseline_parser = subparsers.add_parser(
        "baseline-check",
        help="Run repeatable liveness and sentinel checks against the WebArena VPS runtime.",
    )
    baseline_parser.add_argument("--json", action="store_true")
    _add_site_args(baseline_parser)
    baseline_parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    baseline_parser.add_argument("--map-timeout-seconds", type=int, default=MAP_TIMEOUT_SECONDS)
    baseline_parser.add_argument(
        "--with-reset",
        action="store_true",
        help="Reset each selected site before running baseline checks.",
    )
    return parser


def _add_site_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--site",
        action="append",
        default=[],
        choices=list(DEFAULT_SITES),
        help="Limit the operation to one or more sites. Defaults to all sites.",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    target = _load_webarena_target(args.infra_config)
    sites = _resolve_sites(target)
    selected = [sites[site] for site in (args.site or list(_configured_sites(target)))]

    if args.command == "reset":
        payload = _reset_sites(
            target,
            selected,
            timeout_seconds=int(args.timeout_seconds),
            map_timeout_seconds=int(args.map_timeout_seconds),
        )
    else:
        payload = _baseline_check(
            target,
            selected,
            timeout_seconds=int(args.timeout_seconds),
            map_timeout_seconds=int(args.map_timeout_seconds),
            with_reset=bool(args.with_reset),
        )

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_payload(payload)
    return 0 if payload["status"] == "ok" else 1


def _load_webarena_target(infra_config_path: str | Path) -> InfraBenchmarkTarget:
    infra = load_mapping(infra_config_path)
    return resolve_infra_target("webarena_verified", infra)


def _configured_sites(target: InfraBenchmarkTarget) -> tuple[str, ...]:
    environment = dict(target.benchmark_config.get("environment") or {})
    configured = tuple(str(site) for site in (environment.get("required_sites") or ()) if str(site))
    return configured or DEFAULT_SITES


def _resolve_sites(target: InfraBenchmarkTarget) -> dict[str, WebArenaRuntimeSite]:
    environment = dict(target.benchmark_config.get("environment") or {})
    health_urls = dict(environment.get("health_urls") or {})
    prefix = str(environment.get("container_name_prefix") or "")
    container_names = dict(environment.get("container_names") or {})
    reset_commands = dict(environment.get("reset_commands") or {})
    shared_reset_template = str(environment.get("reset_command") or "").strip()
    sites: dict[str, WebArenaRuntimeSite] = {}
    for site in _configured_sites(target):
        site_url = str(health_urls.get(site) or "")
        if not site_url:
            raise ValueError(f"webarena runtime missing health_urls[{site!r}] in infra config")
        default_container_name = f"{prefix}{site}" if prefix else DEFAULT_CONTAINER_NAMES.get(site, site)
        container_name = str(container_names.get(site) or default_container_name)
        reset_command = str(reset_commands.get(site) or "").strip() or None
        if reset_command is None and shared_reset_template:
            reset_command = shared_reset_template.format(site=site, container_name=container_name)
        sites[site] = WebArenaRuntimeSite(
            site=site,
            site_url=site_url,
            container_name=container_name,
            reset_command=reset_command,
        )
    return sites


def _reset_sites(
    target: InfraBenchmarkTarget,
    sites: Sequence[WebArenaRuntimeSite],
    *,
    timeout_seconds: int,
    map_timeout_seconds: int,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    overall_ok = True
    for site in sites:
        site_timeout = map_timeout_seconds if site.site == "map" else timeout_seconds
        started = time.monotonic()
        if site.reset_command:
            completed = _run_remote_shell(
                target,
                site.reset_command,
                timeout_seconds=site_timeout,
            )
        else:
            completed = _docker_exec(
                target,
                site.container_name,
                ["env-ctrl", "init"],
                timeout_seconds=site_timeout,
            )
        duration_seconds = round(time.monotonic() - started, 3)
        ok = completed.returncode == 0
        overall_ok = overall_ok and ok
        results.append(
            {
                "site": site.site,
                "container_name": site.container_name,
                "ok": ok,
                "duration_seconds": duration_seconds,
                "returncode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        )
    return {
        "status": "ok" if overall_ok else "error",
        "command": "reset",
        "machine_id": target.machine_id,
        "sites": results,
    }


def _baseline_check(
    target: InfraBenchmarkTarget,
    sites: Sequence[WebArenaRuntimeSite],
    *,
    timeout_seconds: int,
    map_timeout_seconds: int,
    with_reset: bool,
) -> dict[str, Any]:
    reset_payload = None
    overall_ok = True
    if with_reset:
        reset_payload = _reset_sites(
            target,
            sites,
            timeout_seconds=timeout_seconds,
            map_timeout_seconds=map_timeout_seconds,
        )
        overall_ok = reset_payload["status"] == "ok"

    checks: list[dict[str, Any]] = []
    for site in sites:
        site_timeout = map_timeout_seconds if site.site == "map" else timeout_seconds
        site_payload = {
            "site": site.site,
            "container_name": site.container_name,
            "container": _check_container_running(target, site, timeout_seconds=site_timeout),
            "homepage": _check_homepage(target, site, timeout_seconds=site_timeout),
            "sentinels": [],
        }
        if site.site == "shopping_admin":
            site_payload["sentinels"].append(
                _check_shopping_admin_reviews_sentinel(target, site, timeout_seconds=site_timeout)
            )
        if site.site == "map":
            site_payload["sentinels"].append(_check_map_route_sentinel(target, site, timeout_seconds=site_timeout))

        site_ok = bool(site_payload["container"]["ok"]) and bool(site_payload["homepage"]["ok"])
        site_ok = site_ok and all(bool(item["ok"]) for item in site_payload["sentinels"])
        site_payload["ok"] = site_ok
        overall_ok = overall_ok and site_ok
        checks.append(site_payload)

    return {
        "status": "ok" if overall_ok else "error",
        "command": "baseline-check",
        "machine_id": target.machine_id,
        "with_reset": with_reset,
        "reset": reset_payload,
        "sites": checks,
    }


def _check_container_running(
    target: InfraBenchmarkTarget,
    site: WebArenaRuntimeSite,
    *,
    timeout_seconds: int,
) -> dict[str, Any]:
    completed = _run_remote(
        target,
        ["docker", "inspect", "-f", "{{json .State}}", site.container_name],
        timeout_seconds=timeout_seconds,
    )
    if completed.returncode != 0:
        return {
            "ok": False,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    try:
        state = json.loads(completed.stdout.strip())
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": f"invalid docker inspect state json: {exc}",
        }
    return {
        "ok": bool(state.get("Running")) and not bool(state.get("Dead")),
        "state": state,
    }


def _check_homepage(
    target: InfraBenchmarkTarget,
    site: WebArenaRuntimeSite,
    *,
    timeout_seconds: int,
) -> dict[str, Any]:
    needle = PAGE_NEEDLES[site.site]
    url = _homepage_url(site)
    code = (
        "import sys, urllib.request\n"
        "url, needle, timeout = sys.argv[1], sys.argv[2], float(sys.argv[3])\n"
        "req = urllib.request.Request(url)\n"
        "with urllib.request.urlopen(req, timeout=timeout) as response:\n"
        "    body = response.read(4096).decode('utf-8', errors='replace')\n"
        "    status = response.status\n"
        "if needle not in body:\n"
        "    raise SystemExit(f'missing sentinel substring: {needle}')\n"
        "print(status)\n"
        "print(body[:400].replace('\\n', ' '))\n"
    )
    completed = _run_remote(
        target,
        ["python3", "-c", code, url, needle, str(timeout_seconds)],
        timeout_seconds=timeout_seconds + 5,
    )
    lines = [line for line in completed.stdout.splitlines() if line]
    return {
        "ok": completed.returncode == 0,
        "url": url,
        "needle": needle,
        "returncode": completed.returncode,
        "status_code": int(lines[0]) if completed.returncode == 0 and lines and lines[0].isdigit() else None,
        "snippet": lines[1] if completed.returncode == 0 and len(lines) > 1 else completed.stdout.strip()[:400],
        "stderr": completed.stderr.strip(),
    }


def _check_shopping_admin_reviews_sentinel(
    target: InfraBenchmarkTarget,
    site: WebArenaRuntimeSite,
    *,
    timeout_seconds: int,
) -> dict[str, Any]:
    completed = _docker_exec(
        target,
        site.container_name,
        [
            "mysql",
            "-N",
            "-B",
            "-umagentouser",
            "-pMyPassword",
            "magentodb",
            "-e",
            SHOPPING_ADMIN_REVIEWS_SQL,
        ],
        timeout_seconds=timeout_seconds,
    )
    rows = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    return {
        "name": "shopping_admin_reviews",
        "ok": completed.returncode == 0 and rows == ["Hannah Lim"],
        "expected_rows": ["Hannah Lim"],
        "actual_rows": rows,
        "returncode": completed.returncode,
        "stderr": completed.stderr.strip(),
    }


def _check_map_route_sentinel(
    target: InfraBenchmarkTarget,
    site: WebArenaRuntimeSite,
    *,
    timeout_seconds: int,
) -> dict[str, Any]:
    code = (
        "import json, sys, urllib.request\n"
        "url = sys.argv[1]\n"
        "timeout = float(sys.argv[2])\n"
        "with urllib.request.urlopen(url, timeout=timeout) as response:\n"
        "    payload = json.loads(response.read().decode())\n"
        "print(payload['routes'][0]['distance'])\n"
    )
    completed = _docker_exec(
        target,
        site.container_name,
        ["python3", "-c", code, MAP_ROUTE_URL, str(timeout_seconds)],
        timeout_seconds=timeout_seconds + 5,
    )
    stdout = completed.stdout.strip()
    try:
        distance = float(stdout)
    except ValueError:
        distance = None
    ok = completed.returncode == 0 and distance is not None and abs(distance - MAP_ROUTE_DISTANCE_METERS) <= MAP_ROUTE_DISTANCE_TOLERANCE
    return {
        "name": "map_osrm_route_distance",
        "ok": ok,
        "expected_distance_meters": MAP_ROUTE_DISTANCE_METERS,
        "tolerance_meters": MAP_ROUTE_DISTANCE_TOLERANCE,
        "actual_distance_meters": distance,
        "returncode": completed.returncode,
        "stderr": completed.stderr.strip(),
    }


def _docker_exec(
    target: InfraBenchmarkTarget,
    container_name: str,
    argv: Sequence[str],
    *,
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    return _run_remote(
        target,
        ["docker", "exec", container_name, *argv],
        timeout_seconds=timeout_seconds,
    )


def _run_remote_shell(
    target: InfraBenchmarkTarget,
    command: str,
    *,
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    return _run_remote(
        target,
        ["bash", "-lc", str(command)],
        timeout_seconds=timeout_seconds,
    )


def _run_remote(
    target: InfraBenchmarkTarget,
    argv: Sequence[str],
    *,
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    remote_command = shlex.join([str(item) for item in argv])
    ssh_command = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=no",
        "-i",
        target.ssh_key_path,
        "-p",
        str(target.ssh_port),
        f"{target.ssh_user}@{target.ssh_host}",
        remote_command,
    ]
    try:
        return subprocess.run(
            ssh_command,
            check=False,
            capture_output=True,
            text=True,
            timeout=max(1, int(timeout_seconds)),
        )
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(
            ssh_command,
            returncode=124,
            stdout=(exc.stdout or ""),
            stderr=((exc.stderr or "") + f"\ncommand timed out after {timeout_seconds}s").strip(),
        )


def _homepage_url(site: WebArenaRuntimeSite) -> str:
    if site.site != "shopping_admin":
        return site.site_url
    stripped = site.site_url.rstrip("/")
    return stripped if stripped.endswith("/admin") else f"{stripped}/admin"


def _print_payload(payload: dict[str, Any]) -> None:
    print(f"status: {payload['status']}")
    print(f"command: {payload['command']}")
    print(f"machine_id: {payload['machine_id']}")
    if payload.get("with_reset") is not None:
        print(f"with_reset: {payload['with_reset']}")
    reset = payload.get("reset")
    if isinstance(reset, dict):
        print(f"reset_status: {reset['status']}")
    for site in payload.get("sites") or []:
        print(f"{site['site']}: {'ok' if site.get('ok', site.get('ok') is not False) else 'error'}")
        if "container" in site:
            print(f"  container_ok: {site['container']['ok']}")
        if "homepage" in site:
            print(f"  homepage_ok: {site['homepage']['ok']}")
        for sentinel in site.get("sentinels") or []:
            print(f"  sentinel {sentinel['name']}: {sentinel['ok']}")
        if "stdout" in site and site["stdout"]:
            print(f"  stdout: {site['stdout']}")
        if "stderr" in site and site["stderr"]:
            print(f"  stderr: {site['stderr']}")


if __name__ == "__main__":
    raise SystemExit(main())
