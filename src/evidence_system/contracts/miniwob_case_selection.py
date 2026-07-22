"""Deterministic MiniWoB++ case selection and case-packet materialization."""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evidence_system.contracts.case_packets import (
    RemoteCaseSources,
    build_case_packet_source_bundle,
    build_case_packets,
)
from evidence_system.contracts.common import ContractLifecycleError, hash_path_if_exists, normalize_domain, utc_now_iso, write_json
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml


MINIWOB_SELECTION_SALT = "miniwob-deterministic-selection-v1"
MINIWOB_SELECTED_COUNT = 50
MINIWOB_SELECTION_OFFSET = 0
MINIWOB_SELECTED_SOURCES_PATH = "experiments/official_splits/miniwob_selected_task_sources.json"
MINIWOB_MANIFEST_PATH = "experiments/appendix/miniwob_manifest.yaml"
MINIWOB_SOURCE_BUNDLE_PATH = "experiments/evidence_contracts/source_bundles/miniwob_case_units_source_bundle.json"
MINIWOB_SMOKE_MANIFEST_PATH = "experiments/smoke/miniwob_manifest.yaml"
MINIWOB_INSTALL_ROOT_TOKEN = "<MINIWOB_INSTALL_ROOT>"
MINIWOB_VENV_ROOT_TOKEN = "<MINIWOB_VENV_ROOT>"
MINIWOB_COMPACT_PACKET_DERIVED_FILES = (
    "derived/drafting_context.json",
    "derived/official_source_excerpts.json",
    "derived/selected_task_source.json",
)
_MINIWOB_PRIVATE_ROOTS_KEY = "_materialization_roots"
_MATERIALIZATION_PATH_KEY = "materialization_path"


@dataclass(frozen=True)
class CandidateCase:
    domain: str
    case_unit_id: str
    task_id: str
    payload: dict[str, Any]


def build_miniwob_case_selection(
    *,
    infra_config_path: str | Path = "configs/infra.yaml",
    source_infra_config_path: str | Path | None = None,
    agents_config_path: str | Path = "configs/agents.yaml",
    source_mode: str = "remote",
    main_manifest_path: str | Path = "experiments/experiment_manifest.yaml",
    official_splits_root: str | Path = "experiments/official_splits",
    manifest_path: str | Path = MINIWOB_MANIFEST_PATH,
    selected_sources_path: str | Path = MINIWOB_SELECTED_SOURCES_PATH,
    source_bundle_path: str | Path = MINIWOB_SOURCE_BUNDLE_PATH,
    case_packets_root: str | Path = "experiments/case_packets",
    selected_count: int = MINIWOB_SELECTED_COUNT,
    selection_offset: int = MINIWOB_SELECTION_OFFSET,
    manifest_id: str | None = None,
    result_namespace: str | None = None,
) -> dict[str, Any]:
    main_manifest = _load_manifest(main_manifest_path)
    agents_config = _load_agents_config(agents_config_path)
    result_namespace = _validate_result_namespace(result_namespace)
    source_mode = _normalize_source_mode(source_mode)
    source_infra_config_path = source_infra_config_path or infra_config_path
    remote = RemoteCaseSources(source_infra_config_path) if source_mode == "remote" else None
    created_at = utc_now_iso()

    official_root = resolve_repo_path(official_splits_root)
    official_root.mkdir(parents=True, exist_ok=True)

    candidate_pool = _miniwob_candidate_pool(
        remote,
        infra_config_path=source_infra_config_path,
        source_mode=source_mode,
    )
    candidate_pool_path = official_root / f"miniwob_official_task_catalog_{int(candidate_pool['candidate_count'])}.json"
    public_candidate_pool = _public_miniwob_payload(candidate_pool) if source_mode == "local" else candidate_pool
    write_json(candidate_pool_path, public_candidate_pool)

    selected = _select_cases(candidate_pool, selected_count=selected_count, selection_offset=selection_offset)
    selected_payload = _selected_payload(
        candidate_pool=candidate_pool,
        candidate_pool_path=_repo_relative(candidate_pool_path),
        selected=selected,
        remote=remote,
        source_mode=source_mode,
    )
    selected_sources_resolved = resolve_repo_path(selected_sources_path)
    write_json(selected_sources_resolved, selected_payload)

    manifest_resolved = resolve_repo_path(manifest_path)
    manifest_resolved.parent.mkdir(parents=True, exist_ok=True)
    source_bundle_resolved = resolve_repo_path(source_bundle_path)
    source_bundle_resolved.parent.mkdir(parents=True, exist_ok=True)

    write_json(
        manifest_resolved,
        _manifest_payload(
            main_manifest=main_manifest,
            candidate_pool_path=candidate_pool_path,
            candidate_pool=candidate_pool,
            selected=selected,
            source_bundle_hash="0" * 64,
            created_at=created_at,
            manifest_id=manifest_id or _default_manifest_id(selected_count=selected_count, selection_offset=selection_offset),
            infra_config_path=infra_config_path,
            agents_config_path=agents_config_path,
            agents_config=agents_config,
            result_namespace=result_namespace,
        ),
    )

    try:
        built_packets = build_case_packets(
            manifest_path=manifest_resolved,
            official_splits_path=official_root,
            output_root=case_packets_root,
            source_mode=source_mode,
            infra_config_path=source_infra_config_path,
        )
    finally:
        # Local materialization paths are transient capabilities, not public
        # provenance.  Scrub them even when packet construction fails so a
        # rerun never leaves host-specific paths behind.
        if source_mode == "local":
            write_json(selected_sources_resolved, _public_miniwob_payload(selected_payload))

    build_case_packet_source_bundle(
        manifest_path=manifest_resolved,
        case_packets_root=case_packets_root,
        previous_source_bundle_path=source_bundle_resolved,
        output_path=source_bundle_resolved,
        allow_generated_contract_ids=True,
        include_manifest_sha256=False,
    )

    write_json(
        manifest_resolved,
        _manifest_payload(
            main_manifest=main_manifest,
            candidate_pool_path=candidate_pool_path,
            candidate_pool=candidate_pool,
            selected=selected,
            source_bundle_hash=sha256_file(source_bundle_resolved),
            created_at=created_at,
            manifest_id=manifest_id or _default_manifest_id(selected_count=selected_count, selection_offset=selection_offset),
            infra_config_path=infra_config_path,
            agents_config_path=agents_config_path,
            agents_config=agents_config,
            result_namespace=result_namespace,
        ),
    )

    return {
        "status": "ok",
        "candidate_pool_path": _repo_relative(candidate_pool_path),
        "selected_sources_path": _repo_relative(selected_sources_resolved),
        "manifest_path": _repo_relative(manifest_resolved),
        "source_bundle_path": _repo_relative(source_bundle_resolved),
        "selected_count": len(selected),
        "selection_offset": selection_offset,
        "source_mode": source_mode,
        "source_infra_config_path": _repo_relative(source_infra_config_path),
        "source_infra_config_hash": sha256_file(resolve_repo_path(source_infra_config_path)),
        "result_namespace": result_namespace,
        "built_count": len(built_packets),
        "built": [item.to_dict() for item in built_packets],
    }


def _load_manifest(path: str | Path) -> dict[str, Any]:
    payload = load_json_or_yaml(path)
    if not isinstance(payload, dict):
        raise ContractLifecycleError("main manifest must be a mapping")
    return dict(payload)


def _load_agents_config(path: str | Path) -> dict[str, Any]:
    payload = load_json_or_yaml(path)
    if not isinstance(payload, dict):
        raise ContractLifecycleError("agents config must be a mapping")
    if not isinstance(payload.get("experimental_agents"), dict):
        raise ContractLifecycleError("agents config must contain experimental_agents mapping")
    return dict(payload)


def _smoke_task_ids(smoke_manifest_path: str | Path = MINIWOB_SMOKE_MANIFEST_PATH) -> list[str]:
    payload = load_json_or_yaml(smoke_manifest_path)
    if not isinstance(payload, dict):
        raise ContractLifecycleError("MiniWoB++ smoke manifest must be a mapping")
    selected: set[str] = set()
    for domain_block in list(payload.get("domains") or []):
        if not isinstance(domain_block, dict):
            continue
        if normalize_domain(domain_block.get("domain")) != "miniwob":
            continue
        for case in list(domain_block.get("case_units") or []):
            if not isinstance(case, dict):
                continue
            task_id = str(case.get("task_id") or "").strip()
            if task_id:
                selected.add(task_id)
    return sorted(selected)


def _miniwob_candidate_pool(
    remote: RemoteCaseSources | None,
    *,
    infra_config_path: str | Path = "configs/infra.yaml",
    source_mode: str = "remote",
) -> dict[str, Any]:
    source_mode = _normalize_source_mode(source_mode)
    config = _miniwob_config(infra_config_path)
    if source_mode == "local":
        config = _validated_local_miniwob_config(config)
    python_bin = str(config["python_bin"])
    install_dir = str(config["install_dir"])
    html_root = str(config["html_root"])
    script = """
__PYTHON_BIN__ - <<'PY'
import inspect
import json
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

import browsergym.miniwob as mw


class LocalRefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs = []

    def handle_starttag(self, _tag, attrs) -> None:
        lookup = dict(attrs)
        for key in ("src", "href"):
            value = lookup.get(key)
            if value:
                self.refs.append(value)


def collapse_ws(text: str | None) -> str | None:
    if text is None:
        return None
    collapsed = re.sub(r"\\s+", " ", text).strip()
    return collapsed or None


def strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


html_root = Path(__HTML_ROOT__)
module_file = Path(inspect.getfile(mw)).resolve()
package_root = module_file.parent
registry_file = package_root / "__init__.py"
rows = []
for task_cls in sorted(mw.ALL_MINIWOB_TASKS, key=lambda cls: cls.get_task_id()):
    html_file = html_root / f"{task_cls.subdomain}.html"
    html_text = html_file.read_text(encoding="utf-8")
    parser = LocalRefParser()
    parser.feed(html_text)
    asset_paths = []
    for ref in parser.refs:
        if ref.startswith(("http://", "https://", "data:", "javascript:", "#")):
            continue
        asset_path = (html_file.parent / ref).resolve()
        if asset_path.is_file():
            asset_paths.append(str(asset_path))
    title_match = re.search(r"<title>(.*?)</title>", html_text, flags=re.IGNORECASE | re.DOTALL)
    query_match = re.search(r'id=["\\\']query["\\\'][^>]*>(.*?)</', html_text, flags=re.IGNORECASE | re.DOTALL)
    base_cls = task_cls.__mro__[1] if len(task_cls.__mro__) > 1 else None
    rows.append(
        {
            "case_unit_id": task_cls.get_task_id(),
            "task_id": task_cls.get_task_id(),
            "class_name": task_cls.__name__,
            "module": task_cls.__module__,
            "source_file": inspect.getfile(task_cls),
            "base_class_name": base_cls.__name__ if base_cls is not None else None,
            "base_module": base_cls.__module__ if base_cls is not None else None,
            "base_source_file": inspect.getfile(base_cls) if base_cls is not None else None,
            "subdomain": task_cls.subdomain,
            "nondeterministic": bool(getattr(task_cls, "nondeterministic", False)),
            "html_file": str(html_file),
            "html_asset_files": sorted(set(asset_paths)),
            "html_title": collapse_ws(unescape(strip_tags(title_match.group(1)))) if title_match else None,
            "static_query_text": collapse_ws(unescape(strip_tags(query_match.group(1)))) if query_match else None,
        }
    )
print(
    json.dumps(
        {
            "schema_version": "official_case_source.miniwob_candidates.v1",
            "benchmark": "MiniWoB++",
            "install_dir": __INSTALL_DIR__,
            "package_root": str(package_root),
            "html_root": str(html_root),
            "registry_file": str(registry_file),
            "catalog_count": len(rows),
            "items": rows,
        },
        indent=2,
        sort_keys=True,
    )
)
PY
"""
    script = script.replace("__PYTHON_BIN__", shlex.quote(python_bin))
    script = script.replace("__INSTALL_DIR__", json.dumps(install_dir))
    script = script.replace("__HTML_ROOT__", json.dumps(html_root))
    if source_mode == "remote":
        if remote is None:
            raise ContractLifecycleError("remote source mode requires remote case sources")
        raw_payload = remote.run(remote.miniwob_machine, script)
    else:
        raw_payload = _run_local_candidate_helper(script)
    payload = json.loads(raw_payload)
    if not isinstance(payload, dict):
        raise ContractLifecycleError("MiniWoB++ candidate helper payload must be a mapping")
    items = [dict(item) for item in list(payload.get("items") or []) if isinstance(item, dict)]
    excluded_smoke = _smoke_task_ids()
    eligible = [
        item
        for item in items
        if str(item.get("task_id") or item.get("case_unit_id") or "").strip() not in set(excluded_smoke)
    ]
    _augment_selection_order(eligible, domain="miniwob")
    payload["catalog_count"] = len(items)
    payload["candidate_count"] = len(eligible)
    payload["items"] = eligible
    payload["source_mode"] = source_mode
    payload["selection_hash_function"] = "sha256"
    payload["selection_salt_hash"] = sha256_object(MINIWOB_SELECTION_SALT)
    payload["excluded_smoke_case_units"] = excluded_smoke
    payload["smoke_exclusion_hash"] = sha256_object(excluded_smoke)
    payload["eligible_case_unit_set_hash"] = sha256_object(_case_unit_records(eligible))
    payload["case_selection_order_hash"] = sha256_object(_selection_order_records(eligible))
    payload["eligibility_policy"] = "official BrowserGym MiniWoB++ task registry minus MiniWoB++ smoke tasks declared in experiments/smoke/miniwob_manifest.yaml"
    if source_mode == "local":
        payload[_MINIWOB_PRIVATE_ROOTS_KEY] = {
            "install_root": install_dir,
            "venv_root": str(Path(python_bin).parent.parent),
        }
    return payload


def _augment_selection_order(items: list[dict[str, Any]], *, domain: str) -> None:
    decorated: list[tuple[str, str, dict[str, Any]]] = []
    for item in items:
        task_id = str(item.get("task_id") or item.get("case_unit_id") or "")
        case_unit_id = str(item.get("case_unit_id") or task_id)
        if not task_id or not case_unit_id:
            raise ContractLifecycleError(f"{domain} candidate item missing task_id/case_unit_id")
        order_key = sha256_object(
            {
                "salt": MINIWOB_SELECTION_SALT,
                "domain": domain,
                "case_unit_id": case_unit_id,
                "task_id": task_id,
            }
        )
        item["selection_order_key"] = order_key
        decorated.append((order_key, case_unit_id, item))
    decorated.sort(key=lambda row: (row[0], row[1]))
    for index, (_key, _case_unit_id, item) in enumerate(decorated):
        item["selection_rank"] = index


def _select_cases(candidate_pool: dict[str, Any], *, selected_count: int, selection_offset: int = 0) -> list[CandidateCase]:
    if selected_count <= 0:
        raise ContractLifecycleError("MiniWoB++ selected_count must be positive")
    if selection_offset < 0:
        raise ContractLifecycleError("MiniWoB++ selection_offset must be non-negative")
    items = [dict(item) for item in list(candidate_pool.get("items") or []) if isinstance(item, dict)]
    items.sort(key=lambda item: (str(item.get("selection_order_key") or ""), str(item.get("case_unit_id") or "")))
    window_end = selection_offset + selected_count
    if len(items) < window_end:
        raise ContractLifecycleError(
            "MiniWoB++ candidate pool too small for requested window "
            f"offset={selection_offset} selected_count={selected_count}: only {len(items)} eligible cases"
        )
    selected: list[CandidateCase] = []
    for item in items[selection_offset:window_end]:
        case_unit_id = str(item.get("case_unit_id") or item.get("task_id") or "")
        task_id = str(item.get("task_id") or case_unit_id)
        selected.append(CandidateCase(domain="miniwob", case_unit_id=case_unit_id, task_id=task_id, payload=item))
    return selected


def _selected_payload(
    *,
    candidate_pool: dict[str, Any],
    candidate_pool_path: str,
    selected: list[CandidateCase],
    remote: RemoteCaseSources | None,
    source_mode: str = "remote",
) -> dict[str, Any]:
    source_mode = _normalize_source_mode(source_mode)
    install_dir = str(candidate_pool.get("install_dir") or "")
    public_roots = _miniwob_path_roots(candidate_pool) if source_mode == "local" else None
    unique_paths: list[str] = []
    seen: set[str] = set()
    for case in selected:
        for path in _miniwob_official_paths(candidate_pool, case.payload):
            if path in seen:
                continue
            seen.add(path)
            unique_paths.append(path)
    if source_mode == "remote":
        if remote is None:
            raise ContractLifecycleError("remote source mode requires remote case sources")
        hash_lookup = remote.remote_file_hashes(remote.miniwob_machine, unique_paths)
    else:
        hash_lookup = _local_file_hashes(unique_paths)
    items = []
    for case in selected:
        actual_item = dict(case.payload)
        item = (
            _public_miniwob_payload(actual_item, roots=public_roots)
            if source_mode == "local"
            else actual_item
        )
        official_files = []
        for source_path in _miniwob_official_paths(candidate_pool, actual_item):
            descriptor = {
                "source_path": (
                    _public_miniwob_path(source_path, public_roots)
                    if public_roots is not None
                    else source_path
                ),
                "archive_path": _archive_path_for_miniwob(source_path, install_dir=install_dir),
                "sha256": hash_lookup[source_path],
            }
            if source_mode == "local":
                descriptor[_MATERIALIZATION_PATH_KEY] = source_path
            official_files.append(descriptor)
        item["source_ref"] = f"miniwob://{case.task_id}"
        item["official_files"] = official_files
        task_html_archive = next(
            (
                str(entry["archive_path"])
                for entry in official_files
                if str(entry["archive_path"]).startswith(
                    "official/install/miniwob/html/miniwob/"
                )
                and str(entry["archive_path"]).endswith(".html")
            ),
            "",
        )
        if not task_html_archive:
            raise ContractLifecycleError(
                f"MiniWoB++ selected task has no task HTML source: {case.task_id}"
            )
        item["packet_files"] = [
            *MINIWOB_COMPACT_PACKET_DERIVED_FILES,
            task_html_archive,
        ]
        item["source_sha256"] = sha256_object(
            {
                "task_id": case.task_id,
                "source_files": [entry["sha256"] for entry in official_files],
            }
        )
        items.append(item)
    return {
        "benchmark": "MiniWoB++",
        "schema_version": "official_case_source.miniwob_selected_tasks.v1",
        "selected_count": len(items),
        "selection_hash_function": "sha256",
        "selection_salt_hash": sha256_object(MINIWOB_SELECTION_SALT),
        "candidate_pool_path": candidate_pool_path,
        "source_mode": source_mode,
        "items": items,
    }


def _miniwob_official_paths(candidate_pool: dict[str, Any], item: dict[str, Any]) -> list[str]:
    files = [
        str(candidate_pool.get("registry_file") or "").strip(),
        str(item.get("source_file") or "").strip(),
        str(item.get("base_source_file") or "").strip(),
        str(item.get("html_file") or "").strip(),
        *[str(path).strip() for path in list(item.get("html_asset_files") or [])],
    ]
    deduped: list[str] = []
    seen: set[str] = set()
    for path in files:
        if not path or path in seen:
            continue
        seen.add(path)
        deduped.append(path)
    return deduped


def _archive_path_for_miniwob(source_path: str, *, install_dir: str) -> str:
    path = Path(source_path)
    install = Path(install_dir)
    try:
        return f"official/install/{path.relative_to(install)}"
    except ValueError:
        marker = "site-packages/"
        text = str(path)
        if marker in text:
            return f"official/python/{text.split(marker, 1)[1]}"
        return f"official/files/{path.name}"


def _case_unit_records(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "case_unit_id": str(item.get("case_unit_id") or ""),
            "task_id": str(item.get("task_id") or ""),
        }
        for item in sorted(items, key=lambda row: str(row.get("case_unit_id") or ""))
    ]


def _selection_order_records(items: list[dict[str, Any]]) -> list[dict[str, str | int]]:
    ordered = sorted(items, key=lambda row: int(row.get("selection_rank") or 0))
    return [
        {
            "case_unit_id": str(item.get("case_unit_id") or ""),
            "task_id": str(item.get("task_id") or ""),
            "selection_order_key": str(item.get("selection_order_key") or ""),
            "selection_rank": int(item.get("selection_rank") or 0),
        }
        for item in ordered
    ]


def _manifest_payload(
    *,
    main_manifest: dict[str, Any],
    candidate_pool_path: Path,
    candidate_pool: dict[str, Any],
    selected: list[CandidateCase],
    source_bundle_hash: str,
    created_at: str,
    manifest_id: str,
    infra_config_path: str | Path = "configs/infra.yaml",
    agents_config_path: str | Path = "configs/agents.yaml",
    agents_config: dict[str, Any] | None = None,
    result_namespace: str | None = None,
) -> dict[str, Any]:
    agents_config = agents_config or _load_agents_config(agents_config_path)
    agents = _manifest_agent_entries(main_manifest=main_manifest, agents_config=agents_config)
    selection_cfg = dict(main_manifest.get("deterministic_selection") or {})
    domain_cases = [
        {
            "case_unit_id": case.case_unit_id,
            "task_id": case.task_id,
            "contract_lock_status": "draft_required",
        }
        for case in selected
    ]
    payload = {
        "schema_version": "experiment_manifest/v1",
        "manifest_id": manifest_id,
        "manifest_version": "0.1.0-prelock",
        "created_at": created_at,
        "status": "draft",
        "paper_mapping_path": "experiments/paper_mapping.md",
        "paper_mapping_sha256": hash_path_if_exists("experiments/paper_mapping.md"),
        "source_bundle_hash": source_bundle_hash,
        "agents_config_hash": sha256_file(resolve_repo_path(agents_config_path)),
        "infra_config_hash": sha256_file(resolve_repo_path(infra_config_path)),
        "deterministic_selection": {
            "hash_function": "sha256",
            "hash_salt_hash": sha256_object(MINIWOB_SELECTION_SALT),
            "eligible_case_unit_set_hash": str(candidate_pool.get("eligible_case_unit_set_hash") or ""),
            "excluded_smoke_case_units": list(candidate_pool.get("excluded_smoke_case_units") or []),
            "smoke_exclusion_hash": str(candidate_pool.get("smoke_exclusion_hash") or ""),
            "case_selection_order_hash": str(candidate_pool.get("case_selection_order_hash") or ""),
            "bootstrap_seed": int(selection_cfg.get("bootstrap_seed") or 123),
            "bootstrap_resample_count": int(selection_cfg.get("bootstrap_resample_count") or 1000),
            "audit_sample_seed": int(selection_cfg.get("audit_sample_seed") or 456),
            "rerun_subset_selection_rule": "predeclared hash order over MiniWoB++ eligible case units after smoke exclusion",
        },
        "domains": [
            {
                "domain": "miniwob",
                "domain_display_name": "MiniWoB++",
                "experiment_type": "diagnostic",
                "priority": "P3",
                "case_unit_count": len(selected),
                "record_slot_count": len(selected) * len(agents),
                "planned_record_slot_ids_hash": sha256_object(
                    [
                        {
                            "case_unit_id": case.case_unit_id,
                            "agent_id": str((agent or {}).get("agent_id") or ""),
                        }
                        for case in selected
                        for agent in agents
                    ]
                ),
                "official_split_eligible_case_units": int(candidate_pool.get("candidate_count") or len(selected)),
                "official_split_hash": sha256_file(candidate_pool_path),
                "official_split_exception_id": None,
                "contract_lock_status": "draft_required",
                "claim_scope": "native_aligned",
                "stronger_measurement_mapping": None,
                "case_units": domain_cases,
            }
        ],
        "agents": agents,
        "official_split_exceptions": [],
        "declared_appendix_diagnostics": [],
        "required_paper_labels": [],
        "contract_locks": [],
    }
    if result_namespace is not None:
        payload["result_namespace"] = _validate_result_namespace(result_namespace)
    return payload


def _default_manifest_id(*, selected_count: int, selection_offset: int) -> str:
    start_rank = selection_offset + 1
    end_rank = selection_offset + selected_count
    if selection_offset == 0 and selected_count == MINIWOB_SELECTED_COUNT:
        return "miniwob-diagnostic-50-manifest"
    return f"miniwob-diagnostic-window-{start_rank:03d}-{end_rank:03d}-manifest"


def _miniwob_config(infra_config_path: str | Path = "configs/infra.yaml") -> dict[str, str]:
    infra = load_json_or_yaml(infra_config_path)
    if not isinstance(infra, dict):
        raise ContractLifecycleError("infra config must be a mapping")
    for machine in list(infra.get("machines") or []):
        if not isinstance(machine, dict) or machine.get("enabled") is False:
            continue
        benchmarks = dict(machine.get("benchmarks") or {})
        benchmark = dict(benchmarks.get("MiniWoB++") or {})
        if not benchmark:
            continue
        config = {
            "python_bin": str(benchmark.get("python_bin") or ""),
            "install_dir": str(benchmark.get("install_dir") or ""),
            "html_root": str(benchmark.get("assets_path") or ""),
        }
        missing = [key for key, value in config.items() if not value]
        if missing:
            raise ContractLifecycleError(
                "MiniWoB++ benchmark config missing required values: " + ", ".join(missing)
            )
        return config
    raise ContractLifecycleError("MiniWoB++ benchmark config missing from infra config")


def _validated_local_miniwob_config(config: dict[str, str]) -> dict[str, str]:
    # Keep the venv interpreter entrypoint itself: resolving its symlink would
    # execute the base interpreter without the venv's site-packages.
    python_path = resolve_repo_path(config["python_bin"]).absolute()
    install_path = resolve_repo_path(config["install_dir"]).resolve()
    html_path = resolve_repo_path(config["html_root"]).resolve()
    if not python_path.is_file() or not os.access(python_path, os.X_OK):
        raise ContractLifecycleError(
            f"local MiniWoB++ python_bin must be an executable file: {python_path}"
        )
    if not install_path.is_dir():
        raise ContractLifecycleError(
            f"local MiniWoB++ install_dir must be a directory: {install_path}"
        )
    if not html_path.is_dir():
        raise ContractLifecycleError(
            f"local MiniWoB++ assets_path must be a directory: {html_path}"
        )
    return {
        "python_bin": str(python_path),
        "install_dir": str(install_path),
        "html_root": str(html_path),
    }


def _run_local_candidate_helper(script: str) -> str:
    try:
        completed = subprocess.run(
            ["/bin/bash", "-lc", "set -euo pipefail\n" + script],
            cwd=resolve_repo_path("."),
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ContractLifecycleError(f"local MiniWoB++ candidate helper failed: {exc}") from exc
    if completed.returncode != 0:
        raise ContractLifecycleError(
            "local MiniWoB++ candidate helper failed "
            f"with exit code {completed.returncode}: {completed.stderr.strip()}"
        )
    return completed.stdout


def _local_file_hashes(paths: list[str]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for source_path in paths:
        resolved = resolve_repo_path(source_path).resolve()
        if not resolved.is_file():
            raise ContractLifecycleError(
                f"local MiniWoB++ official source file is missing: {resolved}"
            )
        hashes[source_path] = sha256_file(resolved)
    return hashes


def _miniwob_path_roots(payload: dict[str, Any]) -> tuple[tuple[Path, str], ...]:
    raw_roots = payload.get(_MINIWOB_PRIVATE_ROOTS_KEY)
    if not isinstance(raw_roots, dict):
        raise ContractLifecycleError("local MiniWoB++ payload missing private materialization roots")
    install_root = Path(str(raw_roots.get("install_root") or ""))
    venv_root = Path(str(raw_roots.get("venv_root") or ""))
    if not install_root.is_absolute() or not venv_root.is_absolute():
        raise ContractLifecycleError("local MiniWoB++ materialization roots must be absolute")
    roots = (
        (install_root, MINIWOB_INSTALL_ROOT_TOKEN),
        (venv_root, MINIWOB_VENV_ROOT_TOKEN),
    )
    return tuple(sorted(roots, key=lambda item: len(str(item[0])), reverse=True))


def _public_miniwob_path(value: str, roots: tuple[tuple[Path, str], ...]) -> str:
    candidate = Path(value)
    if not candidate.is_absolute():
        return value
    for root, token in roots:
        try:
            relative = candidate.relative_to(root)
        except ValueError:
            continue
        return token if not relative.parts else f"{token}/{relative.as_posix()}"
    raise ContractLifecycleError(
        f"local MiniWoB++ path is outside locked install/venv roots: {candidate}"
    )


def _public_miniwob_payload(
    value: Any,
    *,
    roots: tuple[tuple[Path, str], ...] | None = None,
) -> Any:
    if roots is None and isinstance(value, dict) and _MINIWOB_PRIVATE_ROOTS_KEY in value:
        roots = _miniwob_path_roots(value)
    roots = roots or ()
    if isinstance(value, dict):
        return {
            str(key): _public_miniwob_payload(item, roots=roots)
            for key, item in value.items()
            if key not in {_MINIWOB_PRIVATE_ROOTS_KEY, _MATERIALIZATION_PATH_KEY}
        }
    if isinstance(value, list):
        return [_public_miniwob_payload(item, roots=roots) for item in value]
    if isinstance(value, tuple):
        return tuple(_public_miniwob_payload(item, roots=roots) for item in value)
    if isinstance(value, str):
        return _public_miniwob_path(value, roots) if roots else value
    return value


def _normalize_source_mode(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized not in {"remote", "local"}:
        raise ContractLifecycleError("source_mode must be 'remote' or 'local'")
    return normalized


def _manifest_agent_entries(
    *,
    main_manifest: dict[str, Any],
    agents_config: dict[str, Any],
) -> list[dict[str, Any]]:
    roles = agents_config.get("experimental_agents")
    if not isinstance(roles, dict):
        raise ContractLifecycleError("agents config must contain experimental_agents mapping")
    entries: list[dict[str, Any]] = []
    for original in list(main_manifest.get("agents") or []):
        if not isinstance(original, dict):
            raise ContractLifecycleError("main manifest agents entries must be mappings")
        agent_id = str(original.get("agent_id") or "").strip()
        if not agent_id:
            raise ContractLifecycleError("main manifest agent entry missing agent_id")
        role = roles.get(agent_id)
        if not isinstance(role, dict):
            raise ContractLifecycleError(f"agents config missing experimental agent {agent_id}")
        entries.append(
            {
                "agent_id": agent_id,
                "config_hash": sha256_object(role),
                "agent_probe_rationale": _validated_agent_probe_rationale(agent_id, role),
            }
        )
    if not entries:
        raise ContractLifecycleError("main manifest must declare at least one agent")
    return entries


def _validated_agent_probe_rationale(
    agent_id: str,
    role: dict[str, Any],
) -> dict[str, Any]:
    rationale = role.get("agent_probe_rationale")
    if not isinstance(rationale, dict):
        raise ContractLifecycleError(
            f"agents config {agent_id} missing agent_probe_rationale mapping"
        )
    if not isinstance(rationale.get("non_redundant_measurement_probe"), bool):
        raise ContractLifecycleError(
            f"agents config {agent_id} rationale requires boolean non_redundant_measurement_probe"
        )
    if rationale.get("leaderboard_interpretation") is not False:
        raise ContractLifecycleError(
            f"agents config {agent_id} rationale leaderboard_interpretation must be false"
        )
    result: dict[str, Any] = {
        "non_redundant_measurement_probe": rationale["non_redundant_measurement_probe"],
    }
    placeholder_markers = (
        "需要从",
        "placeholder",
        "pending",
        "tbd",
        "todo",
        "fillfrom",
        "not_implemented",
    )
    for field in (
        "spans_source_openness",
        "spans_scale",
        "spans_tool_use_style",
    ):
        value = rationale.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ContractLifecycleError(
                f"agents config {agent_id} rationale requires non-empty {field}"
            )
        lowered = value.lower()
        if any(marker in lowered for marker in placeholder_markers) or re.search(r"<[^>]+>", value):
            raise ContractLifecycleError(
                f"agents config {agent_id} rationale {field} contains a placeholder"
            )
        result[field] = value
    result["leaderboard_interpretation"] = False
    return result


def _validate_result_namespace(value: str | None) -> str | None:
    if value is None:
        return None
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value):
        raise ContractLifecycleError(
            "result_namespace must match ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"
        )
    return value


def _repo_relative(path: str | Path) -> str:
    resolved = resolve_repo_path(path)
    try:
        return str(resolved.relative_to(resolve_repo_path(".")))
    except ValueError:
        return str(resolved)
