from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from scripts import run_webarena_verified_browser_acceptance as browser_acceptance


ROOT = Path(__file__).resolve().parents[2]
SITE_LOCK = browser_acceptance.load_json(ROOT / "configs" / "webarena_verified_sites.lock.json")


def _machine() -> browser_acceptance.Machine:
    return browser_acceptance.load_machines(ROOT / "configs" / "infra.yaml")[0]


def _full_deploy_receipt() -> dict:
    machine = _machine()
    return {
        "schema_version": browser_acceptance.DEPLOY_SCHEMA,
        "operation": "deploy_and_accept",
        "status": "pass",
        "machine_id": machine.machine_id,
        "ssh_host": machine.host,
        "ssh_host_fingerprint": machine.fingerprint,
        "site_lock_sha256": browser_acceptance._site_lock_sha256(SITE_LOCK),
        "exclusive_lock": {"acquired_at": "before", "released_at": "after"},
        "runtime_sources": {
            "installed_version": "1.2.3",
            "official_commit": SITE_LOCK["official_commit"],
            "runner_commit": SITE_LOCK["runner_commit"],
        },
        "images": {
            site: {
                "reference": (
                    f"{SITE_LOCK['images'][site]['reference']}@{SITE_LOCK['images'][site]['digest']}"
                ),
                "image_id": f"sha256:{'a' * 64}",
            }
            for site in browser_acceptance.SITE_ORDER
        },
        "data_assets": {
            name: {"size_bytes": spec["size_bytes"], "sha256": "b" * 64}
            for name, spec in SITE_LOCK["data_assets"].items()
        },
        "resets": [
            {"site": site, "ok": True} for site in browser_acceptance.SITE_ORDER
        ],
        "sites": [
            {
                "site": site,
                "ok": True,
                "container": {"port_bindings": [f"80/tcp -> 127.0.0.1:{10000 + index}"]},
                "sentinels": [{"name": "homepage", "ok": True}],
            }
            for index, site in enumerate(browser_acceptance.SITE_ORDER)
        ],
        "login": {
            "status": "pass",
            "required_sites": list(browser_acceptance.AUTH_SITES),
            "required_state_combinations": list(browser_acceptance.AUTH_STATE_COMBINATIONS),
            "authenticated_page_probes": [
                "shopping:/wishlist/ exact URL",
                "shopping_admin:/dashboard with Dashboard marker",
                "reddit:/user/<locked-account>/account with Delete marker",
                "gitlab:/-/profile exact URL",
            ],
            "generated_state_file_count": 8,
            "validated_authenticated_page_probe_count": 12,
            "validated_cookie_count": 12,
            "validated_associated_cookie_count": 9,
            "validated_associated_nonempty_cookie_count": 8,
            "validated_effective_associated_nonempty_cookie_count": 8,
            "validated_empty_cookie_count": 4,
            "validated_expired_empty_cookie_count": 0,
            "validated_nonempty_cookie_count": 8,
            "validated_persistent_cookie_count": 7,
            "validated_session_cookie_count": 5,
            "sensitive_state_retained": False,
        },
    }


def test_strict_full_deploy_receipt_is_required_and_secret_free_summary_is_returned() -> None:
    machine = _machine()
    summary = browser_acceptance.validate_deploy_receipt(
        _full_deploy_receipt(), machine=machine, site_lock=SITE_LOCK
    )
    assert summary == {
        "status": "pass",
        "source": "controller_full_deployment_receipt",
        "required_sites": list(browser_acceptance.AUTH_SITES),
        "required_state_combinations": list(browser_acceptance.AUTH_STATE_COMBINATIONS),
        "authenticated_page_probes": [
            "shopping:/wishlist/ exact URL",
            "shopping_admin:/dashboard with Dashboard marker",
            "reddit:/user/<locked-account>/account with Delete marker",
            "gitlab:/-/profile exact URL",
        ],
        "validated_state_file_count": 8,
        "validated_authenticated_page_probe_count": 12,
        "validated_cookie_count": 12,
        "validated_associated_cookie_count": 9,
        "validated_associated_nonempty_cookie_count": 8,
        "validated_effective_associated_nonempty_cookie_count": 8,
        "validated_empty_cookie_count": 4,
        "validated_expired_empty_cookie_count": 0,
        "validated_nonempty_cookie_count": 8,
        "validated_persistent_cookie_count": 7,
        "validated_session_cookie_count": 5,
        "sensitive_state_retained": False,
    }
    serialized = json.dumps(summary)
    assert "value" not in serialized
    assert "storage_state" not in serialized


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda row: row.update(status="verified"), "full deployment did not pass"),
        (lambda row: row["data_assets"]["osrm_routing.tar"].pop("sha256"), "full SHA is absent"),
        (lambda row: row["sites"].pop(), "six-site deployment status did not pass"),
        (
            lambda row: row["login"].update(generated_state_file_count=7),
            "state file count is not exactly 8",
        ),
        (
            lambda row: row["login"].update(validated_authenticated_page_probe_count=11),
            "page probe count is not exactly 12",
        ),
        (
            lambda row: row["login"].update(validated_associated_cookie_count=7),
            "associated cookie count is below 8",
        ),
        (
            lambda row: row["login"].update(
                validated_effective_associated_nonempty_cookie_count=7
            ),
            "effective associated nonempty cookie count is below 8",
        ),
        (
            lambda row: row["login"].update(validated_empty_cookie_count=3),
            "cookie validation counts do not close",
        ),
        (
            lambda row: row["login"].pop("validated_empty_cookie_count"),
            "validation counts are missing or invalid",
        ),
        (lambda row: row["login"].update(sensitive_state_retained=True), "may have been retained"),
    ],
)
def test_deploy_receipt_drift_fails_closed(mutation, message: str) -> None:
    receipt = _full_deploy_receipt()
    mutation(receipt)
    with pytest.raises(browser_acceptance.BrowserAcceptanceError, match=message):
        browser_acceptance.validate_deploy_receipt(
            receipt, machine=_machine(), site_lock=SITE_LOCK
        )


def test_missing_three_machine_receipts_stop_before_any_browser_work(tmp_path: Path) -> None:
    args = argparse.Namespace(
        infra=str(ROOT / "configs" / "infra.yaml"),
        site_lock=str(ROOT / "configs" / "webarena_verified_sites.lock.json"),
        deploy_receipts=str(tmp_path / "missing"),
        artifact_root=str(tmp_path / "artifacts"),
        output=str(tmp_path / "receipts"),
        pwcli=str(browser_acceptance.DEFAULT_PWCLI),
        replace=False,
    )
    with pytest.raises(browser_acceptance.BrowserAcceptanceError, match="receipt is absent"):
        browser_acceptance.run_acceptance(args)
    assert not (tmp_path / "artifacts").exists()
    assert not (tmp_path / "receipts").exists()


def test_trace_cookie_header_guard_deletes_trace_before_failing(tmp_path: Path) -> None:
    trace = tmp_path / "trace.trace"
    network = tmp_path / "trace.network"
    trace.write_bytes(b"safe trace")
    network.write_bytes(b'{"headers":[{"name":"Cookie","value":"must-not-remain"}]}')
    with pytest.raises(browser_acceptance.BrowserAcceptanceError, match="cookie header"):
        browser_acceptance._assert_trace_has_no_cookie_headers([trace, network])
    assert not trace.exists()
    assert not network.exists()


def test_infra_is_exactly_three_locked_vps_and_never_syncs_dotenv() -> None:
    machines = browser_acceptance.load_machines(ROOT / "configs" / "infra.yaml")
    assert [machine.machine_id for machine in machines] == [
        "webarena-gpt54-ord",
        "webarena-claude47-ord",
        "webarena-deepseek-v4pro-ord",
    ]
    assert [machine.host for machine in machines] == [
        "45.76.67.186",
        "66.42.108.130",
        "149.28.79.226",
    ]
    source = (ROOT / "scripts" / "run_webarena_verified_browser_acceptance.py").read_text(
        encoding="utf-8"
    )
    assert 'read_text(encoding="utf-8")' in source
    assert "state-load" not in source
    assert "cookie-list" not in source
    assert "cookie-get" not in source
    assert '"all_thirty_six_authenticated_controller_probes_pass": True' in source
    assert '"all_twelve_authenticated_controller_probes_pass": True' not in source
