"""Deterministic MiniWoB++ case selection and case-packet materialization."""

from __future__ import annotations

import json
import re
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


@dataclass(frozen=True)
class CandidateCase:
    domain: str
    case_unit_id: str
    task_id: str
    payload: dict[str, Any]


def build_miniwob_case_selection(
    *,
    infra_config_path: str | Path = "configs/infra.yaml",
    main_manifest_path: str | Path = "experiments/experiment_manifest.yaml",
    official_splits_root: str | Path = "experiments/official_splits",
    manifest_path: str | Path = MINIWOB_MANIFEST_PATH,
    selected_sources_path: str | Path = MINIWOB_SELECTED_SOURCES_PATH,
    source_bundle_path: str | Path = MINIWOB_SOURCE_BUNDLE_PATH,
    case_packets_root: str | Path = "experiments/case_packets",
    selected_count: int = MINIWOB_SELECTED_COUNT,
    selection_offset: int = MINIWOB_SELECTION_OFFSET,
    manifest_id: str | None = None,
) -> dict[str, Any]:
    main_manifest = _load_manifest(main_manifest_path)
    remote = RemoteCaseSources(infra_config_path)
    created_at = utc_now_iso()

    official_root = resolve_repo_path(official_splits_root)
    official_root.mkdir(parents=True, exist_ok=True)

    candidate_pool = _miniwob_candidate_pool(remote)
    candidate_pool_path = official_root / f"miniwob_official_task_catalog_{int(candidate_pool['candidate_count'])}.json"
    write_json(candidate_pool_path, candidate_pool)

    selected = _select_cases(candidate_pool, selected_count=selected_count, selection_offset=selection_offset)
    selected_payload = _selected_payload(
        candidate_pool=candidate_pool,
        candidate_pool_path=_repo_relative(candidate_pool_path),
        selected=selected,
        remote=remote,
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
        ),
    )

    built_packets = build_case_packets(
        manifest_path=manifest_resolved,
        official_splits_path=official_root,
        output_root=case_packets_root,
        source_mode="remote",
        infra_config_path=infra_config_path,
    )

    build_case_packet_source_bundle(
        manifest_path=manifest_resolved,
        case_packets_root=case_packets_root,
        previous_source_bundle_path=source_bundle_resolved,
        output_path=source_bundle_resolved,
        allow_generated_contract_ids=True,
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
        "built_count": len(built_packets),
        "built": [item.to_dict() for item in built_packets],
    }


def _load_manifest(path: str | Path) -> dict[str, Any]:
    payload = load_json_or_yaml(path)
    if not isinstance(payload, dict):
        raise ContractLifecycleError("main manifest must be a mapping")
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


def _miniwob_candidate_pool(remote: RemoteCaseSources) -> dict[str, Any]:
    config = _miniwob_config()
    machine = remote.miniwob_machine
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
    script = script.replace("__PYTHON_BIN__", python_bin)
    script = script.replace("__INSTALL_DIR__", json.dumps(install_dir))
    script = script.replace("__HTML_ROOT__", json.dumps(html_root))
    payload = json.loads(remote.run(machine, script))
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
    payload["selection_hash_function"] = "sha256"
    payload["selection_salt_hash"] = sha256_object(MINIWOB_SELECTION_SALT)
    payload["excluded_smoke_case_units"] = excluded_smoke
    payload["smoke_exclusion_hash"] = sha256_object(excluded_smoke)
    payload["eligible_case_unit_set_hash"] = sha256_object(_case_unit_records(eligible))
    payload["case_selection_order_hash"] = sha256_object(_selection_order_records(eligible))
    payload["eligibility_policy"] = "official BrowserGym MiniWoB++ task registry minus MiniWoB++ smoke tasks declared in experiments/smoke/miniwob_manifest.yaml"
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
    remote: RemoteCaseSources,
) -> dict[str, Any]:
    install_dir = str(candidate_pool.get("install_dir") or "")
    machine = remote.miniwob_machine
    unique_paths: list[str] = []
    seen: set[str] = set()
    for case in selected:
        for path in _miniwob_official_paths(candidate_pool, case.payload):
            if path in seen:
                continue
            seen.add(path)
            unique_paths.append(path)
    hash_lookup = remote.remote_file_hashes(machine, unique_paths)
    items = []
    for case in selected:
        item = dict(case.payload)
        official_files = []
        for source_path in _miniwob_official_paths(candidate_pool, item):
            official_files.append(
                {
                    "source_path": source_path,
                    "archive_path": _archive_path_for_miniwob(source_path, install_dir=install_dir),
                    "sha256": hash_lookup[source_path],
                }
            )
        item["source_ref"] = f"miniwob://{case.task_id}"
        item["official_files"] = official_files
        item["packet_files"] = [entry["archive_path"] for entry in official_files] + ["derived/selected_task_source.json"]
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
) -> dict[str, Any]:
    agents = list(main_manifest.get("agents") or [])
    selection_cfg = dict(main_manifest.get("deterministic_selection") or {})
    domain_cases = [
        {
            "case_unit_id": case.case_unit_id,
            "task_id": case.task_id,
            "contract_lock_status": "draft_required",
        }
        for case in selected
    ]
    return {
        "schema_version": "experiment_manifest/v1",
        "manifest_id": manifest_id,
        "manifest_version": "0.1.0-prelock",
        "created_at": created_at,
        "status": "draft",
        "paper_mapping_path": "experiments/paper_mapping.md",
        "paper_mapping_sha256": hash_path_if_exists("experiments/paper_mapping.md"),
        "source_bundle_hash": source_bundle_hash,
        "agents_config_hash": hash_path_if_exists("configs/agents.yaml"),
        "infra_config_hash": hash_path_if_exists("configs/infra.yaml"),
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


def _default_manifest_id(*, selected_count: int, selection_offset: int) -> str:
    start_rank = selection_offset + 1
    end_rank = selection_offset + selected_count
    if selection_offset == 0 and selected_count == MINIWOB_SELECTED_COUNT:
        return "miniwob-diagnostic-50-manifest"
    return f"miniwob-diagnostic-window-{start_rank:03d}-{end_rank:03d}-manifest"


def _miniwob_config() -> dict[str, str]:
    infra = load_json_or_yaml("configs/infra.yaml")
    if not isinstance(infra, dict):
        raise ContractLifecycleError("infra config must be a mapping")
    for machine in list(infra.get("machines") or []):
        if not isinstance(machine, dict) or machine.get("enabled") is False:
            continue
        benchmarks = dict(machine.get("benchmarks") or {})
        benchmark = dict(benchmarks.get("MiniWoB++") or {})
        if not benchmark:
            continue
        return {
            "python_bin": str(benchmark.get("python_bin") or ""),
            "install_dir": str(benchmark.get("install_dir") or ""),
            "html_root": str(benchmark.get("assets_path") or ""),
        }
    raise ContractLifecycleError("MiniWoB++ benchmark config missing from infra config")


def _repo_relative(path: str | Path) -> str:
    resolved = resolve_repo_path(path)
    try:
        return str(resolved.relative_to(resolve_repo_path(".")))
    except ValueError:
        return str(resolved)
