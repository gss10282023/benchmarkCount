from __future__ import annotations

import pytest

from evidence_system.adapters import runtime
from evidence_system.cli import webarena_runtime
from evidence_system.orchestrator.jobs import InfraBenchmarkTarget


def _target(*, health_urls: dict[str, str], prefix: str = "") -> InfraBenchmarkTarget:
    return InfraBenchmarkTarget(
        machine_id="webarena-vps-01",
        machine_role="webarena_vps",
        ssh_host="example.com",
        ssh_user="root",
        ssh_port=22,
        ssh_key_path="<SSH_PRIVATE_KEY_PATH>",
        remote_workdir="<REMOTE_REPO_ROOT>",
        runner_workdir="<REMOTE_REPO_ROOT>",
        benchmark_name="WebArena",
        benchmark_config={
            "environment": {
                "container_name_prefix": prefix,
                "health_urls": health_urls,
            }
        },
        benchmark_config_hash="x" * 64,
        runner_command="/root/miniconda3/envs/webarena/bin/python",
        machine_concurrency=1,
    )


def test_resolve_sites_uses_health_urls_and_container_prefix() -> None:
    sites = webarena_runtime._resolve_sites(
        _target(
            health_urls={
                "shopping": "http://127.0.0.1:7770",
                "shopping_admin": "http://127.0.0.1:7780",
                "reddit": "http://127.0.0.1:9999",
                "gitlab": "http://127.0.0.1:8023",
                "wikipedia": "http://127.0.0.1:8888",
                "map": "http://127.0.0.1:3030",
            },
            prefix="custom_prefix_",
        )
    )

    assert tuple(sites) == webarena_runtime.DEFAULT_SITES
    assert sites["shopping"].site_url == "http://127.0.0.1:7770"
    assert sites["shopping"].container_name == "custom_prefix_shopping"
    assert sites["map"].container_name == "custom_prefix_map"


def test_resolve_sites_requires_all_declared_health_urls() -> None:
    with pytest.raises(ValueError, match="health_urls\\['map'\\]"):
        webarena_runtime._resolve_sites(
            _target(
                health_urls={
                    "shopping": "http://127.0.0.1:7770",
                    "shopping_admin": "http://127.0.0.1:7780",
                    "reddit": "http://127.0.0.1:9999",
                    "gitlab": "http://127.0.0.1:8023",
                    "wikipedia": "http://127.0.0.1:8888",
                }
            )
        )


def test_resolve_sites_defaults_to_verified_canonical_container_names() -> None:
    sites = webarena_runtime._resolve_sites(
        _target(
            health_urls={
                "shopping": "http://127.0.0.1:7770",
                "shopping_admin": "http://127.0.0.1:7780",
                "reddit": "http://127.0.0.1:9999",
                "gitlab": "http://127.0.0.1:8023",
                "wikipedia": "http://127.0.0.1:8888",
                "map": "http://127.0.0.1:3030",
            }
        )
    )

    assert sites["shopping"].container_name == "webarena_verified_shopping"
    assert sites["shopping_admin"].container_name == "webarena_verified_shopping_admin"
    assert sites["reddit"].container_name == "webarena_verified_reddit"


def test_homepage_url_uses_admin_entrypoint_for_shopping_admin() -> None:
    site = webarena_runtime.WebArenaRuntimeSite(
        site="shopping_admin",
        site_url="http://127.0.0.1:7780",
        container_name="shopping_admin",
    )

    assert webarena_runtime._homepage_url(site) == "http://127.0.0.1:7780/admin"


def test_homepage_url_keeps_other_sites_unchanged() -> None:
    site = webarena_runtime.WebArenaRuntimeSite(
        site="shopping",
        site_url="http://127.0.0.1:7770",
        container_name="shopping",
    )

    assert webarena_runtime._homepage_url(site) == "http://127.0.0.1:7770"


def test_global_json_flag_is_not_overwritten_by_slot_subparser() -> None:
    args = webarena_runtime.build_parser().parse_args(
        [
            "--json",
            "slot-reset",
            "--slot-id",
            "slot-0-a",
            "--task-id",
            "0",
            "--agent-id",
            "Agent A",
            "--attempt-id",
            "0",
            "--seed",
            "123000",
            "--agent-input",
            "agent_input.json",
            "--receipt",
            "reset_receipt.json",
        ]
    )
    assert args.json is True


def test_remote_transport_disables_ssh_multiplexing() -> None:
    options = runtime._ssh_host_key_options(
        _target(
            health_urls={
                "shopping": "http://127.0.0.1:7770",
                "shopping_admin": "http://127.0.0.1:7780",
                "reddit": "http://127.0.0.1:9999",
                "gitlab": "http://127.0.0.1:8023",
                "wikipedia": "http://127.0.0.1:8888",
                "map": "http://127.0.0.1:3030",
            }
        )
    )

    assert "ControlMaster=no" in options
    assert "ControlPersist=no" in options
    assert "ControlMaster=auto" not in options
    assert "ControlPersist=300" not in options
    assert not any(option.startswith("ControlPath=") for option in options)


def test_subcommand_json_flag_remains_supported() -> None:
    args = webarena_runtime.build_parser().parse_args(["site-status", "--json"])
    assert args.json is True


def test_print_payload_reads_machine_id_from_reset_receipt(capsys) -> None:
    webarena_runtime._print_payload(
        {
            "status": "pass",
            "command": "slot-reset",
            "machine": {"machine_id": "webarena-gpt54-ord"},
            "sites": [],
        }
    )
    assert "machine_id: webarena-gpt54-ord" in capsys.readouterr().out
