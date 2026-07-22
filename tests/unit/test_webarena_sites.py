from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess

import pytest

from evidence_system import webarena_sites
from evidence_system.webarena_sites import (
    DATA_LOCK_SCHEMA,
    RESET_RECEIPT_SCHEMA,
    SlotIdentity,
    WebArenaSiteController,
    WebArenaSiteError,
    container_run_argv,
    load_data_sha256_lock,
    load_site_lock,
    run_verified_ssh_argv,
    sites_for_agent_input,
    validate_storage_state_payload,
)


ROOT = Path(__file__).resolve().parents[2]
SITE_LOCK_PATH = ROOT / "configs" / "webarena_verified_sites.lock.json"


def _completed(
    argv: list[str] | tuple[str, ...],
    *,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(list(argv), returncode, stdout, stderr)


def _storage_cookie(
    *,
    name: str,
    value: str,
    domain: str = "127.0.0.1",
    expires: float = -1,
) -> dict[str, object]:
    return {
        "name": name,
        "value": value,
        "domain": domain,
        "path": "/",
        "expires": expires,
        "httpOnly": True,
        "secure": False,
        "sameSite": "Lax",
    }


def _controller(run_remote=None) -> WebArenaSiteController:
    return WebArenaSiteController(
        site_lock=load_site_lock(SITE_LOCK_PATH),
        run_remote=run_remote or (lambda argv, _timeout: _completed(argv)),
        machine_id="webarena-gpt54-ord",
        ssh_host="45.76.67.186",
        ssh_host_fingerprint="SHA256:locked",
    )


def test_site_lock_pins_all_images_ports_paths_and_map_reset_scope() -> None:
    lock = load_site_lock(SITE_LOCK_PATH)

    assert lock["official_runtime_python"] == "/opt/webarena-verified/v1.2.3/source/.venv/bin/python"
    assert lock["data_root"] == "/opt/webarena-verified/v1.2.3/data"
    assert set(lock["images"]) == set(webarena_sites.SITE_ORDER)
    assert all("@sha256:" in container_run_argv(lock, site)[-1] for site in webarena_sites.SITE_ORDER)
    assert all(
        any(value.startswith("127.0.0.1:") for value in container_run_argv(lock, site))
        for site in webarena_sites.SITE_ORDER
    )
    map_argv = container_run_argv(lock, "map")
    assert "127.0.0.1:3030:8080" in map_argv
    assert "127.0.0.1:3031:8877" in map_argv
    assert lock["sites"]["map"]["mutable_volumes"] == [
        "webarena_verified_map_website_db",
        "webarena_verified_map_tiles",
        "webarena_verified_map_style",
    ]


def test_infra_routes_three_agents_to_current_vps_without_embedded_secrets() -> None:
    raw = (ROOT / "configs" / "infra.yaml").read_text(encoding="utf-8")
    infra = json.loads(raw)
    machines = [machine for machine in infra["machines"] if machine.get("role") == "webarena_vps"]
    assert [machine["ssh"]["host"] for machine in machines] == [
        "45.76.67.186",
        "66.42.108.130",
        "149.28.79.226",
    ]
    assert [machine["assigned_agent_id"] for machine in machines] == ["Agent A", "Agent B", "Agent C"]
    assert [machine["concurrency"] for machine in machines] == [1, 1, 1]
    assert all(
        machine["benchmarks"]["WebArena-Verified"]["sync_dotenv"] is False
        for machine in machines
    )
    assert all(
        machine["benchmarks"]["WebArena-Verified"]["environment"]["health_urls"]["map"]
        == "http://127.0.0.1:3030"
        for machine in machines
    )
    assert "sk-or-v1-" not in raw


def test_data_sha_lock_is_exact_and_rejects_size_or_digest_drift() -> None:
    lock = load_site_lock(SITE_LOCK_PATH)
    payload = {
        "schema_version": DATA_LOCK_SCHEMA,
        "official_commit": lock["official_commit"],
        "assets": {
            name: {"size_bytes": spec["size_bytes"], "sha256": "a" * 64}
            for name, spec in lock["data_assets"].items()
        },
    }
    assert load_data_sha256_lock(payload, site_lock=lock)["assets"] == payload["assets"]

    payload["assets"]["osrm_routing.tar"]["size_bytes"] += 1
    with pytest.raises(WebArenaSiteError, match="size mismatch"):
        load_data_sha256_lock(payload, site_lock=lock)
    payload["assets"]["osrm_routing.tar"]["size_bytes"] -= 1
    payload["assets"]["osrm_routing.tar"]["sha256"] = "latest"
    with pytest.raises(WebArenaSiteError, match="digest is invalid"):
        load_data_sha256_lock(payload, site_lock=lock)


def test_agent_input_selects_only_declared_task_sites_in_canonical_order() -> None:
    agent_input = {
        "task_id": 759,
        "sites": ["map", "shopping_admin"],
        "intent": "x",
        "intent_template_id": 1,
        "start_urls": [],
    }
    assert sites_for_agent_input(agent_input, expected_task_id=759) == ["shopping_admin", "map"]
    with pytest.raises(WebArenaSiteError, match="task_id"):
        sites_for_agent_input(agent_input, expected_task_id=760)


def test_slot_reset_writes_atomic_mode_600_identity_receipt(monkeypatch, tmp_path: Path) -> None:
    controller = _controller()
    released: list[str] = []
    monkeypatch.setattr(controller, "_acquire_exclusive_lock", lambda **_kwargs: "opaque-token")
    monkeypatch.setattr(controller, "_release_exclusive_lock", lambda token: released.append(token))
    monkeypatch.setattr(
        controller,
        "verify_images",
        lambda sites: {site: {"image_id": f"sha256:{'a' * 64}"} for site in sites},
    )
    monkeypatch.setattr(
        controller,
        "_reset_site",
        lambda site, expected_image_id: {
            "site": site,
            "image_reference": f"locked/{site}@sha256:{'b' * 64}",
            "expected_image_id": expected_image_id,
            "before": {"container_id": "old"},
            "after": {"container_id": "new"},
            "sentinels": [{"name": "homepage", "ok": True}],
            "ok": True,
        },
    )
    receipt_path = tmp_path / "reset_receipt.json"
    receipt = controller.reset_slot(
        identity=SlotIdentity("slot-759-A-0", 759, "Agent A", 0, 123759),
        sites=["map", "shopping_admin"],
        receipt_path=receipt_path,
    )

    on_disk = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt == on_disk
    assert on_disk["schema_version"] == RESET_RECEIPT_SCHEMA
    assert on_disk["status"] == "pass"
    assert on_disk["slot"] == {
        "slot_id": "slot-759-A-0",
        "task_id": 759,
        "agent_id": "Agent A",
        "attempt_id": 0,
        "seed": 123759,
    }
    assert on_disk["reset_scope"] == ["shopping_admin", "map"]
    assert [row["site"] for row in on_disk["sites"]] == ["shopping_admin", "map"]
    assert on_disk["exclusive_lock"]["acquired_at"]
    assert on_disk["exclusive_lock"]["released_at"]
    assert released == ["opaque-token"]
    assert os.stat(receipt_path).st_mode & 0o777 == 0o600


def test_slot_reset_failure_quarantines_and_never_yields_pass(monkeypatch, tmp_path: Path) -> None:
    controller = _controller()
    monkeypatch.setattr(controller, "_acquire_exclusive_lock", lambda **_kwargs: "opaque-token")
    monkeypatch.setattr(controller, "_release_exclusive_lock", lambda _token: None)
    monkeypatch.setattr(
        controller,
        "verify_images",
        lambda sites: {site: {"image_id": f"sha256:{'a' * 64}"} for site in sites},
    )
    monkeypatch.setattr(
        controller,
        "_reset_site",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(WebArenaSiteError("sentinel failed")),
    )
    monkeypatch.setattr(
        controller,
        "_quarantine_sites",
        lambda sites: {"status": "pass", "sites": list(sites)},
    )
    receipt_path = tmp_path / "reset_receipt.json"

    with pytest.raises(WebArenaSiteError, match="slot reset failed"):
        controller.reset_slot(
            identity=SlotIdentity("slot-1-A-0", 1, "Agent A", 0, 123001),
            sites=["shopping"],
            receipt_path=receipt_path,
        )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "fail"
    assert receipt["error"]["message"] == "sentinel failed"
    assert receipt["fail_closed"]["status"] == "pass"


def test_map_reset_recreates_only_mutable_volumes(monkeypatch) -> None:
    calls: list[list[str]] = []

    def run_remote(argv, _timeout):
        calls.append(list(argv))
        return _completed(argv, stdout="ok\n")

    controller = _controller(run_remote)
    before = {
        "container_id": "old",
        "image_id": f"sha256:{'a' * 64}",
        "running": True,
        "started_at": "before",
        "port_bindings": [],
    }
    after = {**before, "container_id": "new", "started_at": "after"}
    inspections = iter([before, after])
    monkeypatch.setattr(controller, "_inspect_container", lambda _name: next(inspections))
    monkeypatch.setattr(
        controller,
        "_wait_for_site",
        lambda _site: [{"name": "map_route_distance", "ok": True}],
    )

    controller._reset_site("map", expected_image_id=f"sha256:{'a' * 64}")
    removed_volumes = [argv[-1] for argv in calls if argv[:4] == ["docker", "volume", "rm", "-f"]]
    assert removed_volumes == [
        "webarena_verified_map_website_db",
        "webarena_verified_map_tiles",
        "webarena_verified_map_style",
    ]
    assert not any("routing_car" in value or "tile_db" in value or "nominatim_db" in value for value in removed_volumes)


def test_stopped_container_can_be_inspected_for_reset_without_active_ports() -> None:
    def run_remote(argv, _timeout):
        command = list(argv)
        if command[:2] == ["docker", "inspect"]:
            return _completed(
                command,
                stdout="old-id|sha256:" + "a" * 64 + "|false|2026-07-16T00:00:00Z\n",
            )
        if command[:2] == ["docker", "port"]:
            return _completed(command, stdout="")
        raise AssertionError(command)

    inspected = _controller(run_remote)._inspect_container("webarena_verified_shopping")

    assert inspected is not None
    assert inspected["running"] is False
    assert inspected["port_bindings"] == []


def test_running_container_without_loopback_ports_remains_fail_closed() -> None:
    def run_remote(argv, _timeout):
        command = list(argv)
        if command[:2] == ["docker", "inspect"]:
            return _completed(
                command,
                stdout="live-id|sha256:" + "a" * 64 + "|true|2026-07-16T00:00:00Z\n",
            )
        if command[:2] == ["docker", "port"]:
            return _completed(command, stdout="80/tcp -> 0.0.0.0:7770\n")
        raise AssertionError(command)

    with pytest.raises(WebArenaSiteError, match="non-loopback"):
        _controller(run_remote)._inspect_container("webarena_verified_shopping")


def test_map_uses_direct_service_sentinels_instead_of_broken_env_ctrl_status() -> None:
    calls: list[list[str]] = []

    def run_remote(argv, _timeout):
        command = list(argv)
        calls.append(command)
        joined = " ".join(command)
        if command[:3] == ["docker", "exec", "webarena_verified_map"] and "process_markers" in joined:
            return _completed(
                command,
                stdout=json.dumps(
                    {
                        "env_ctrl_process": True,
                        "postgres_ports": True,
                        "rails": True,
                        "osrm_profiles": True,
                        "tile_png": True,
                        "nominatim": True,
                    }
                )
                + "\n",
            )
        if command[:3] == ["docker", "exec", "webarena_verified_map"]:
            return _completed(command, stdout="10289.9\n")
        return _completed(command, stdout="200\n")

    checks = _controller(run_remote)._site_checks("map")

    assert [check["name"] for check in checks] == [
        "homepage",
        "map_env_ctrl_process",
        "map_postgres_ports",
        "map_rails",
        "map_osrm_profiles",
        "map_tile_png",
        "map_nominatim",
        "map_route_distance",
    ]
    assert all(check["ok"] is True for check in checks)
    assert not any(command[-2:] == ["env-ctrl", "status"] for command in calls)


def test_verified_ssh_uses_locked_ed25519_known_hosts_and_strict_mode(monkeypatch) -> None:
    webarena_sites._cleanup_known_hosts_files()
    webarena_sites._KNOWN_HOST_FILES.clear()
    commands: list[list[str]] = []
    expected = "SHA256:AbCdEf0123456789+/="

    def fake_run(argv, **kwargs):
        commands.append(list(argv))
        if argv[0] == "ssh-keyscan":
            assert "-H" not in argv
            return _completed(
                argv,
                stdout=(
                    "example.test ssh-ed25519 "
                    "AAAAC3NzaC1lZDI1NTE5AAAAIlocked\n"
                ),
            )
        if argv[0] == "ssh-keygen":
            assert kwargs["input"].startswith("example.test ssh-ed25519")
            return _completed(
                argv, stdout=f"256 {expected} example.test (ED25519)\n"
            )
        assert argv[0] == "ssh"
        return _completed(argv, stdout="remote-ok\n")

    monkeypatch.setattr(webarena_sites.subprocess, "run", fake_run)
    result = run_verified_ssh_argv(
        host="example.test",
        user="root",
        port=22,
        key_path="/secure/key",
        expected_ed25519_fingerprint=expected,
        argv=["docker", "ps"],
        timeout=30,
    )
    assert result.returncode == 0
    ssh = commands[-1]
    assert "StrictHostKeyChecking=yes" in ssh
    assert "HostKeyAlgorithms=ssh-ed25519" in ssh
    assert "ControlMaster=no" in ssh
    assert "ControlPersist=no" in ssh
    assert "ControlMaster=auto" not in ssh
    assert "ControlPersist=300" not in ssh
    assert all("StrictHostKeyChecking=no" not in value for value in ssh)
    known_hosts_option = next(value for value in ssh if value.startswith("UserKnownHostsFile="))
    assert os.stat(known_hosts_option.split("=", 1)[1]).st_mode & 0o777 == 0o600


def test_verified_ssh_fingerprint_mismatch_fails_before_ssh(monkeypatch) -> None:
    webarena_sites._cleanup_known_hosts_files()
    webarena_sites._KNOWN_HOST_FILES.clear()
    commands: list[list[str]] = []

    def fake_run(argv, **_kwargs):
        commands.append(list(argv))
        if argv[0] == "ssh-keyscan":
            return _completed(
                argv,
                stdout=(
                    "example.test ssh-ed25519 "
                    "AAAAC3NzaC1lZDI1NTE5AAAAIother\n"
                ),
            )
        return _completed(
            argv, stdout="256 SHA256:different example.test (ED25519)\n"
        )

    monkeypatch.setattr(webarena_sites.subprocess, "run", fake_run)
    result = run_verified_ssh_argv(
        host="example.test",
        user="root",
        port=22,
        key_path="/secure/key",
        expected_ed25519_fingerprint="SHA256:expected",
        argv=["true"],
        timeout=30,
    )
    assert result.returncode == 255
    assert "fingerprint mismatch" in result.stderr
    assert all(argv[0] != "ssh" for argv in commands)


def test_ssh_retry_classifier_replays_only_pre_execution_connection_failure() -> None:
    assert len(str(webarena_sites._SSH_CONTROL_DIR / ("f" * 40))) < 104
    assert webarena_sites._ssh_failed_before_remote_execution(
        "ssh: connect to host 192.0.2.1 port 22: Operation timed out"
    )
    assert not webarena_sites._ssh_failed_before_remote_execution(
        "client_loop: send disconnect: Broken pipe"
    )


def test_concurrent_known_hosts_cache_is_endpoint_isolated_and_plaintext(
    monkeypatch,
) -> None:
    webarena_sites._cleanup_known_hosts_files()
    hosts = ("192.0.2.10", "192.0.2.11", "192.0.2.12")
    fingerprints = {
        host: f"SHA256:LockedEndpoint{index}+/="
        for index, host in enumerate(hosts, start=1)
    }

    def fake_run(argv, **kwargs):
        if argv[0] == "ssh-keyscan":
            assert "-H" not in argv
            host = str(argv[-1])
            return _completed(
                argv,
                stdout=(
                    f"{host} ssh-ed25519 "
                    f"AAAAC3NzaC1lZDI1NTE5AAAAIendpoint{host[-2:]}\n"
                ),
            )
        assert argv[0] == "ssh-keygen"
        host = str(kwargs["input"]).split()[0]
        return _completed(
            argv,
            stdout=f"256 {fingerprints[host]} {host} (ED25519)\n",
        )

    monkeypatch.setattr(webarena_sites.subprocess, "run", fake_run)
    with ThreadPoolExecutor(max_workers=3) as pool:
        paths = list(
            pool.map(
                lambda host: webarena_sites._verified_known_hosts_file(
                    host=host,
                    port=22,
                    expected_fingerprint=fingerprints[host],
                ),
                hosts,
            )
        )

    assert len(set(paths)) == 3
    for host, raw_path in zip(hosts, paths, strict=True):
        path = Path(raw_path)
        fields = path.read_text(encoding="ascii").split()
        assert fields[0] == host
        assert fields[1] == "ssh-ed25519"
        assert path.stat().st_mode & 0o777 == 0o600
    webarena_sites._cleanup_known_hosts_files()


def test_official_login_probe_sequentially_requires_every_supported_state_combination() -> None:
    calls: list[list[str]] = []

    def run_remote(argv, _timeout):
        calls.append(list(argv))
        return _completed(
            argv,
            stdout=(
                '{"associated_cookie_count":8,"associated_nonempty_cookie_count":8,'
                '"authenticated_page_probe_count":12,"cookie_count":12,'
                '"effective_associated_nonempty_cookie_count":8,'
                '"empty_cookie_count":4,"expired_empty_cookie_count":1,'
                '"file_count":8,"nonempty_cookie_count":8,'
                '"persistent_cookie_count":7,"session_cookie_count":5}\n'
            ),
        )

    receipt = _controller(run_remote).verify_login()
    assert receipt["status"] == "pass"
    assert calls[0][3] == (
        "PLAYWRIGHT_BROWSERS_PATH=/opt/webarena-verified/v1.2.3/ms-playwright"
    )
    injected_script = calls[0][-1]
    compile(injected_script, "<official-login-probe>", "exec")
    assert "login-probe-browser-cache-missing" in injected_script
    assert "'--site_list',*comb,'--auth_folder'" in injected_script
    assert "if files!=required" in injected_script
    assert "login-probe-renewal-failed" in injected_script
    assert "official_login.is_expired" in injected_script
    assert "shutil.rmtree(folder,ignore_errors=True)" in injected_script
    assert "login-state-empty-cookies" in injected_script
    assert "login-state-invalid-cookie-schema" in injected_script
    assert "login-state-expired-nonempty-cookie" in injected_script
    assert "login-state-no-effective-associated-cookie" in injected_script
    assert receipt["generated_state_file_count"] == 8
    assert receipt["validated_authenticated_page_probe_count"] == 12
    assert receipt["validated_cookie_count"] == 12
    assert receipt["validated_associated_cookie_count"] == 8
    assert receipt["validated_associated_nonempty_cookie_count"] == 8
    assert receipt["validated_effective_associated_nonempty_cookie_count"] == 8
    assert receipt["validated_empty_cookie_count"] == 4
    assert receipt["validated_expired_empty_cookie_count"] == 1
    assert receipt["validated_nonempty_cookie_count"] == 8
    assert receipt["playwright_browsers_path"] == (
        "/opt/webarena-verified/v1.2.3/ms-playwright"
    )
    assert receipt["required_state_combinations"] == [
        "gitlab+shopping",
        "gitlab+shopping_admin",
        "gitlab+reddit",
        "shopping+shopping_admin",
        "gitlab",
        "shopping",
        "shopping_admin",
        "reddit",
    ]
    assert len(receipt["authenticated_page_probes"]) == 4
    assert receipt["sensitive_state_retained"] is False


def test_official_login_probe_rejects_summary_without_authenticated_page_count() -> None:
    def run_remote(argv, _timeout):
        return _completed(
            argv,
            stdout=(
                '{"cookie_count":12,"file_count":8,"persistent_cookie_count":7,'
                '"session_cookie_count":5}\n'
            ),
        )

    with pytest.raises(WebArenaSiteError, match="invalid receipt"):
        _controller(run_remote).verify_login()


@pytest.mark.parametrize(
    "field,value",
    [
        ("file_count", 7),
        ("authenticated_page_probe_count", 11),
        ("cookie_count", 0),
        ("associated_cookie_count", 7),
        ("effective_associated_nonempty_cookie_count", 7),
        ("empty_cookie_count", 3),
        ("expired_empty_cookie_count", 5),
        ("session_cookie_count", 4),
    ],
)
def test_official_login_probe_rejects_incomplete_validation_counts(field: str, value: int) -> None:
    summary = {
        "associated_cookie_count": 8,
        "associated_nonempty_cookie_count": 8,
        "authenticated_page_probe_count": 12,
        "cookie_count": 12,
        "effective_associated_nonempty_cookie_count": 8,
        "empty_cookie_count": 4,
        "expired_empty_cookie_count": 1,
        "file_count": 8,
        "nonempty_cookie_count": 8,
        "persistent_cookie_count": 7,
        "session_cookie_count": 5,
    }
    summary[field] = value

    def run_remote(argv, _timeout):
        return _completed(argv, stdout=json.dumps(summary) + "\n")

    with pytest.raises(WebArenaSiteError, match="incomplete validation counts"):
        _controller(run_remote).verify_login()


def test_login_state_validation_rejects_empty_and_expired_cookies() -> None:
    with pytest.raises(WebArenaSiteError, match="no cookies"):
        validate_storage_state_payload(
            {"cookies": [], "origins": []},
            expected_host="127.0.0.1",
            now_epoch=1000,
        )
    with pytest.raises(WebArenaSiteError, match="expired nonempty cookie"):
        validate_storage_state_payload(
            {
                "cookies": [
                    _storage_cookie(name="session", value="opaque", expires=999)
                ],
                "origins": [],
            },
            expected_host="127.0.0.1",
            now_epoch=1000,
        )


def test_login_state_validation_accepts_unexpired_and_session_cookies_without_leaking_values() -> None:
    summary = validate_storage_state_payload(
        {
            "cookies": [
                _storage_cookie(
                    name="persistent",
                    value="must-not-be-returned",
                    domain=".127.0.0.1",
                    expires=2000,
                ),
                _storage_cookie(name="session", value="also-private"),
            ],
            "origins": [],
        },
        expected_host="127.0.0.1",
        now_epoch=1000,
    )
    assert summary == {
        "cookie_count": 2,
        "associated_cookie_count": 2,
        "associated_nonempty_cookie_count": 2,
        "effective_associated_nonempty_cookie_count": 2,
        "empty_cookie_count": 0,
        "expired_empty_cookie_count": 0,
        "nonempty_cookie_count": 2,
        "persistent_cookie_count": 1,
        "session_cookie_count": 1,
    }
    assert "must-not-be-returned" not in json.dumps(summary)


def test_login_state_validation_counts_legal_empty_value_without_treating_it_as_auth() -> None:
    summary = validate_storage_state_payload(
        {
            "cookies": [
                _storage_cookie(name="auth-session", value="opaque-auth", expires=2000),
                _storage_cookie(name="message-queue", value="", expires=2000),
            ],
            "origins": [],
        },
        expected_host="127.0.0.1",
        now_epoch=1000,
    )
    assert summary == {
        "cookie_count": 2,
        "associated_cookie_count": 2,
        "associated_nonempty_cookie_count": 1,
        "effective_associated_nonempty_cookie_count": 1,
        "empty_cookie_count": 1,
        "expired_empty_cookie_count": 0,
        "nonempty_cookie_count": 1,
        "persistent_cookie_count": 2,
        "session_cookie_count": 0,
    }
    serialized = json.dumps(summary)
    assert "opaque-auth" not in serialized
    assert "auth-session" not in serialized
    assert "message-queue" not in serialized


def test_login_state_validation_allows_expired_empty_clear_marker_but_not_as_auth() -> None:
    summary = validate_storage_state_payload(
        {
            "cookies": [
                _storage_cookie(name="auth-session", value="opaque-auth"),
                _storage_cookie(name="clear-marker", value="", expires=999),
            ],
            "origins": [],
        },
        expected_host="127.0.0.1",
        now_epoch=1000,
    )
    assert summary["expired_empty_cookie_count"] == 1
    assert summary["effective_associated_nonempty_cookie_count"] == 1


def test_login_state_validation_rejects_empty_only_state_and_malformed_cookie_schema() -> None:
    with pytest.raises(WebArenaSiteError, match="no effective nonempty cookie"):
        validate_storage_state_payload(
            {
                "cookies": [
                    _storage_cookie(name="message-queue", value="", expires=2000)
                ],
                "origins": [],
            },
            expected_host="127.0.0.1",
            now_epoch=1000,
        )

    malformed = _storage_cookie(name="message-queue", value="", expires=2000)
    malformed.pop("httpOnly")
    with pytest.raises(WebArenaSiteError, match="invalid Playwright cookie schema"):
        validate_storage_state_payload(
            {
                "cookies": [
                    malformed,
                    _storage_cookie(name="auth-session", value="opaque-auth"),
                ],
                "origins": [],
            },
            expected_host="127.0.0.1",
            now_epoch=1000,
        )


@pytest.mark.parametrize(
    ("stderr", "expected_code"),
    [
        (
            ("beartype warning with irrelevant dependency diagnostics " * 100)
            + "login-state-invalid-cookie-schema\n"
            + ("more warning text " * 100),
            "login-state-invalid-cookie-schema",
        ),
        ("unclassified remote warning " * 100, "login-probe-remote-failure"),
    ],
)
def test_login_probe_failure_only_reports_fixed_safe_code(stderr: str, expected_code: str) -> None:
    def run_remote(argv, _timeout):
        return _completed(argv, returncode=1, stderr=stderr)

    with pytest.raises(WebArenaSiteError) as caught:
        _controller(run_remote).verify_login()
    message = str(caught.value)
    assert message == f"official login probe failed (rc=1): {expected_code}"
    assert "beartype" not in message
    assert "dependency" not in message
