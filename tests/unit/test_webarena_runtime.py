from __future__ import annotations

import pytest

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
                "map": "http://127.0.0.1:3000",
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


def test_resolve_sites_defaults_to_original_container_names() -> None:
    sites = webarena_runtime._resolve_sites(
        _target(
            health_urls={
                "shopping": "http://127.0.0.1:7770",
                "shopping_admin": "http://127.0.0.1:7780",
                "reddit": "http://127.0.0.1:9999",
                "gitlab": "http://127.0.0.1:8023",
                "wikipedia": "http://127.0.0.1:8888",
                "map": "http://127.0.0.1:3000",
            }
        )
    )

    assert sites["shopping"].container_name == "shopping"
    assert sites["shopping_admin"].container_name == "shopping_admin"
    assert sites["reddit"].container_name == "forum"


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
