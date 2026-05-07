"""Deterministic appendix case selection for AndroidWorld and WorkArena."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evidence_system.contracts.case_packets import (
    RemoteCaseSources,
    build_case_packet_source_bundle,
    build_case_packets,
)
from evidence_system.contracts.common import ContractLifecycleError, normalize_domain
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.paths import resolve_repo_path
from evidence_system.core.schemas import load_json_or_yaml


APPENDIX_SELECTION_SALT = "appendix-androidworld-workarena-selection-v1"
APPENDIX_DOMAIN_SPECS: tuple[tuple[str, str, int, str], ...] = (
    ("androidworld", "AndroidWorld", 20, "P2"),
    ("workarena", "WorkArena", 20, "P2"),
)
APPENDIX_SOURCE_BUNDLE_PATH = "experiments/evidence_contracts/source_bundles/appendix_androidworld_workarena_source_bundle.json"
APPENDIX_MANIFEST_PATH = "experiments/appendix/androidworld_workarena_manifest.yaml"
ANDROIDWORLD_CANDIDATE_POOL_PATH = "experiments/official_splits/androidworld_official_task_metadata_116.json"
ANDROIDWORLD_SELECTED_SOURCES_PATH = "experiments/official_splits/androidworld_selected_task_sources.json"
WORKARENA_CANDIDATE_POOL_PATH = "experiments/official_splits/workarena_official_task_catalog_716.json"
WORKARENA_SELECTED_SOURCES_PATH = "experiments/official_splits/workarena_selected_task_sources.json"


@dataclass(frozen=True)
class CandidateCase:
    domain: str
    case_unit_id: str
    task_id: str
    payload: dict[str, Any]


def build_auxiliary_case_selection(
    *,
    infra_config_path: str | Path = "configs/infra.yaml",
    main_manifest_path: str | Path = "experiments/experiment_manifest.yaml",
    official_splits_root: str | Path = "experiments/official_splits",
    appendix_manifest_path: str | Path = APPENDIX_MANIFEST_PATH,
    appendix_source_bundle_path: str | Path = APPENDIX_SOURCE_BUNDLE_PATH,
    case_packets_root: str | Path = "experiments/case_packets",
) -> dict[str, Any]:
    official_root = resolve_repo_path(official_splits_root)
    official_root.mkdir(parents=True, exist_ok=True)
    appendix_manifest = resolve_repo_path(appendix_manifest_path)
    appendix_manifest.parent.mkdir(parents=True, exist_ok=True)
    appendix_source_bundle = resolve_repo_path(appendix_source_bundle_path)
    appendix_source_bundle.parent.mkdir(parents=True, exist_ok=True)

    main_manifest = _load_manifest(main_manifest_path)
    remote = RemoteCaseSources(infra_config_path)

    android_candidates = _androidworld_candidate_pool(main_manifest)
    workarena_candidates = _workarena_candidate_pool(main_manifest, remote)
    candidate_pools = {
        "androidworld": android_candidates,
        "workarena": workarena_candidates,
    }

    _write_json(resolve_repo_path(ANDROIDWORLD_CANDIDATE_POOL_PATH), android_candidates)
    _write_json(resolve_repo_path(WORKARENA_CANDIDATE_POOL_PATH), workarena_candidates)

    selected = {
        "androidworld": _select_cases(android_candidates, selected_count=20),
        "workarena": _select_cases(workarena_candidates, selected_count=20),
    }

    _write_json(
        resolve_repo_path(ANDROIDWORLD_SELECTED_SOURCES_PATH),
        _selected_payload(
            benchmark="AndroidWorld",
            schema_version="official_case_source.androidworld_selected_tasks.v1",
            candidate_pool_path=ANDROIDWORLD_CANDIDATE_POOL_PATH,
            selected=selected["androidworld"],
            selection_salt_hash=sha256_object(APPENDIX_SELECTION_SALT),
        ),
    )
    _write_json(
        resolve_repo_path(WORKARENA_SELECTED_SOURCES_PATH),
        _selected_payload(
            benchmark="WorkArena",
            schema_version="official_case_source.workarena_selected_tasks.v1",
            candidate_pool_path=WORKARENA_CANDIDATE_POOL_PATH,
            selected=selected["workarena"],
            selection_salt_hash=sha256_object(APPENDIX_SELECTION_SALT),
        ),
    )

    manifest_payload = _appendix_manifest_payload(
        main_manifest=main_manifest,
        selected=selected,
        source_bundle_hash="",
        candidate_pools=candidate_pools,
    )
    _write_json(appendix_manifest, manifest_payload)

    build_case_packets(
        manifest_path=appendix_manifest,
        official_splits_path=official_root,
        output_root=case_packets_root,
        source_mode="remote",
        infra_config_path=infra_config_path,
    )

    build_case_packet_source_bundle(
        manifest_path=appendix_manifest,
        case_packets_root=case_packets_root,
        previous_source_bundle_path=appendix_source_bundle,
        output_path=appendix_source_bundle,
        allow_generated_contract_ids=True,
    )

    manifest_payload = _appendix_manifest_payload(
        main_manifest=main_manifest,
        selected=selected,
        source_bundle_hash=sha256_file(appendix_source_bundle),
        candidate_pools=candidate_pools,
    )
    _write_json(appendix_manifest, manifest_payload)

    built_packets = build_case_packets(
        manifest_path=appendix_manifest,
        official_splits_path=official_root,
        output_root=case_packets_root,
        source_mode="remote",
        infra_config_path=infra_config_path,
    )
    return {
        "status": "ok",
        "appendix_manifest_path": str(appendix_manifest.relative_to(resolve_repo_path("."))),
        "appendix_source_bundle_path": str(appendix_source_bundle.relative_to(resolve_repo_path("."))),
        "built_count": len(built_packets),
        "built": [item.to_dict() for item in built_packets],
        "selected_counts": {domain: len(items) for domain, items in selected.items()},
    }


def _load_manifest(path: str | Path) -> dict[str, Any]:
    payload = load_json_or_yaml(path)
    if not isinstance(payload, dict):
        raise ContractLifecycleError("main manifest must be a mapping")
    return dict(payload)


def _androidworld_candidate_pool(main_manifest: dict[str, Any]) -> dict[str, Any]:
    android_cfg = _androidworld_config()
    python_bin = str(android_cfg["python_bin"])
    install_dir = str(android_cfg["install_dir"])
    script = """
import inspect
import json
from pathlib import Path
from android_world.registry import TaskRegistry

install_dir = Path(__INSTALL_DIR__)
metadata_path = install_dir / "android_world" / "task_metadata.json"
registry_path = install_dir / "android_world" / "registry.py"
task_eval_path = install_dir / "android_world" / "task_evals" / "task_eval.py"
metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
metadata_by_name = dict((item["task_name"], item) for item in metadata)
registry = TaskRegistry().get_registry(TaskRegistry.ANDROID_WORLD_FAMILY)
rows = []
for task_name, task_cls in sorted(registry.items()):
    row = dict(metadata_by_name[task_name])
    row.update(
        {
            "task_name": task_name,
            "task_id": task_name,
            "case_unit_id": task_name,
            "class_name": task_cls.__name__,
            "module": task_cls.__module__,
            "source_file": inspect.getfile(task_cls),
            "base_class_name": task_cls.__mro__[1].__name__ if len(task_cls.__mro__) > 1 else None,
            "base_module": task_cls.__mro__[1].__module__ if len(task_cls.__mro__) > 1 else None,
            "base_source_file": inspect.getfile(task_cls.__mro__[1]) if len(task_cls.__mro__) > 1 else None,
        }
    )
    rows.append(row)
print(json.dumps({
    "schema_version": "official_case_source.androidworld_candidates.v1",
    "benchmark": "AndroidWorld",
    "install_dir": str(install_dir),
    "candidate_count": len(rows),
    "registry_file": str(registry_path),
    "task_metadata_file": str(metadata_path),
    "task_eval_base_file": str(task_eval_path),
    "selection_hash_function": "sha256",
    "selection_salt_hash": __SELECTION_SALT_HASH__,
    "items": rows,
}, indent=2, sort_keys=True))
"""
    script = script.replace("__INSTALL_DIR__", repr(install_dir)).replace(
        "__SELECTION_SALT_HASH__", json.dumps(sha256_object(APPENDIX_SELECTION_SALT))
    )
    payload = _run_local_python(python_bin, script)
    items = list(payload.get("items") or [])
    _augment_selection_order(items, domain="androidworld")
    payload["eligible_case_unit_set_hash"] = sha256_object(_case_unit_records(items))
    payload["case_selection_order_hash"] = sha256_object(_selection_order_records(items))
    payload["smoke_exclusion_hash"] = sha256_object([])
    payload["excluded_smoke_case_units"] = []
    payload["paper_label"] = _declared_paper_label(main_manifest, "androidworld")
    return payload


def _workarena_candidate_pool(main_manifest: dict[str, Any], remote: RemoteCaseSources) -> dict[str, Any]:
    machine = remote._machine_for_benchmark("WorkArena")  # noqa: SLF001
    script = """
<WORKARENA_INSTALL_ROOT>/.venv/bin/python - <<'PY'
import inspect
import json
import re
from pathlib import Path
import browsergym.workarena as wa

def referenced_task_configs(paths):
    refs = []
    pattern = re.compile(r"data_files/task_configs/([A-Za-z0-9_.-]+\\.json)")
    for source_path in paths:
        text = Path(source_path).read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            refs.append(match.group(1))
    return sorted(set(refs))

rows = []
for task_cls in wa.ALL_WORKARENA_TASKS:
    task_id = task_cls.get_task_id()
    source_file = inspect.getfile(task_cls)
    mro = [cls for cls in task_cls.__mro__[1:] if cls.__name__ not in {"object"}]
    parent = mro[0] if mro else None
    parent_source = inspect.getfile(parent) if parent is not None else None
    files_to_scan = [source_file]
    if parent_source and parent_source not in files_to_scan:
        files_to_scan.append(parent_source)
    config_files = referenced_task_configs(files_to_scan)
    rows.append({
        "task_id": task_id,
        "case_unit_id": task_id,
        "class_name": task_cls.__name__,
        "module": task_cls.__module__,
        "source_file": source_file,
        "base_class_name": parent.__name__ if parent is not None else None,
        "base_module": parent.__module__ if parent is not None else None,
        "base_source_file": parent_source,
        "task_category": wa.TASK_CATEGORY_MAP.get(task_id),
        "config_files": config_files,
    })
rows = sorted(rows, key=lambda item: item["task_id"])
package_root = Path(inspect.getfile(wa)).resolve().parent
print(json.dumps({
    "schema_version": "official_case_source.workarena_candidates.v1",
    "benchmark": "WorkArena",
    "package_root": str(package_root),
    "candidate_count": len(rows),
    "registry_file": str(package_root / "__init__.py"),
    "items": rows,
}, indent=2, sort_keys=True))
PY
"""
    payload = json.loads(remote.run(machine, script))
    items = list(payload.get("items") or [])
    _augment_selection_order(items, domain="workarena")
    payload["selection_hash_function"] = "sha256"
    payload["selection_salt_hash"] = sha256_object(APPENDIX_SELECTION_SALT)
    payload["eligible_case_unit_set_hash"] = sha256_object(_case_unit_records(items))
    payload["case_selection_order_hash"] = sha256_object(_selection_order_records(items))
    payload["smoke_exclusion_hash"] = sha256_object([])
    payload["excluded_smoke_case_units"] = []
    payload["paper_label"] = _declared_paper_label(main_manifest, "workarena")
    return payload


def _declared_paper_label(main_manifest: dict[str, Any], domain: str) -> str | None:
    for item in list(main_manifest.get("declared_appendix_diagnostics") or []):
        if not isinstance(item, dict):
            continue
        if normalize_domain(item.get("domain")) == domain:
            label = item.get("paper_label")
            return str(label) if label else None
    return None


def _augment_selection_order(items: list[dict[str, Any]], *, domain: str) -> None:
    decorated = []
    for item in items:
        task_id = str(item.get("task_id") or item.get("case_unit_id") or "")
        if not task_id:
            raise ContractLifecycleError(f"{domain} candidate item missing task_id/case_unit_id")
        case_unit_id = str(item.get("case_unit_id") or task_id)
        order_key = sha256_object(
            {
                "salt": APPENDIX_SELECTION_SALT,
                "domain": domain,
                "case_unit_id": case_unit_id,
                "task_id": task_id,
            }
        )
        item["selection_order_key"] = order_key
        decorated.append((order_key, case_unit_id, item))
    decorated.sort(key=lambda row: (row[0], row[1]))
    for index, (_, _, item) in enumerate(decorated):
        item["selection_rank"] = index


def _select_cases(candidate_pool: dict[str, Any], *, selected_count: int) -> list[CandidateCase]:
    items = [dict(item) for item in list(candidate_pool.get("items") or []) if isinstance(item, dict)]
    items.sort(key=lambda item: (str(item.get("selection_order_key") or ""), str(item.get("case_unit_id") or "")))
    selected: list[CandidateCase] = []
    for item in items[:selected_count]:
        domain = normalize_domain(candidate_pool.get("benchmark"))
        case_unit_id = str(item.get("case_unit_id") or item.get("task_id") or "")
        task_id = str(item.get("task_id") or case_unit_id)
        selected.append(CandidateCase(domain=domain, case_unit_id=case_unit_id, task_id=task_id, payload=item))
    return selected


def _selected_payload(
    *,
    benchmark: str,
    schema_version: str,
    candidate_pool_path: str,
    selected: list[CandidateCase],
    selection_salt_hash: str,
) -> dict[str, Any]:
    items = []
    for case in selected:
        item = dict(case.payload)
        if case.domain == "androidworld":
            install_dir = _androidworld_config()["install_dir"]
            item["source_ref"] = f"androidworld://{case.task_id}"
            item["official_files"] = _androidworld_official_files(item, install_dir=str(install_dir))
            item["packet_files"] = [entry["archive_path"] for entry in item["official_files"]] + ["derived/selected_task_source.json"]
            item["source_sha256"] = sha256_object(
                {
                    "task_name": case.task_id,
                    "source_files": [entry["sha256"] for entry in item["official_files"]],
                }
            )
        elif case.domain == "workarena":
            item["source_ref"] = f"workarena://{case.task_id}"
            item["official_files"] = _workarena_official_files(item)
            item["packet_files"] = [entry["archive_path"] for entry in item["official_files"]] + ["derived/selected_task_source.json"]
            item["source_sha256"] = sha256_object(
                {
                    "task_id": case.task_id,
                    "source_files": [entry["sha256"] for entry in item["official_files"]],
                }
            )
        items.append(item)
    return {
        "benchmark": benchmark,
        "schema_version": schema_version,
        "selected_count": len(items),
        "selection_hash_function": "sha256",
        "selection_salt_hash": selection_salt_hash,
        "candidate_pool_path": candidate_pool_path,
        "items": items,
    }


def _androidworld_official_files(item: dict[str, Any], *, install_dir: str) -> list[dict[str, str]]:
    install = Path(install_dir)
    files = [
        install / "android_world" / "task_metadata.json",
        install / "android_world" / "registry.py",
        install / "android_world" / "task_evals" / "task_eval.py",
    ]
    for key in ("source_file", "base_source_file"):
        value = str(item.get(key) or "").strip()
        if value:
            files.append(Path(value))
    deduped = []
    seen: set[Path] = set()
    for path in files:
        if path in seen or not path.exists():
            continue
        seen.add(path)
        if path.is_relative_to(install):
            archive_path = f"official/install/{path.relative_to(install)}"
        else:
            marker = "site-packages/"
            text = str(path)
            archive_path = f"official/python/{text.split(marker, 1)[1]}" if marker in text else f"official/files/{path.name}"
        deduped.append(
            {
                "source_path": str(path),
                "archive_path": archive_path,
                "sha256": sha256_file(path),
            }
        )
    return deduped


def _workarena_official_files(item: dict[str, Any]) -> list[dict[str, str]]:
    files = [
        "<WORKARENA_INSTALL_ROOT>/.venv/lib/python3.12/site-packages/browsergym/workarena/__init__.py",
        str(item.get("source_file") or ""),
        str(item.get("base_source_file") or ""),
    ]
    package_root = "<WORKARENA_INSTALL_ROOT>/.venv/lib/python3.12/site-packages/browsergym/workarena"
    for name in list(item.get("config_files") or []):
        files.append(f"{package_root}/data_files/task_configs/{name}")
    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    remote = RemoteCaseSources("configs/infra.yaml")
    machine = remote._machine_for_benchmark("WorkArena")  # noqa: SLF001
    paths: list[str] = []
    for path in files:
        if not path or path in seen:
            continue
        seen.add(path)
        paths.append(path)
    hashes = remote.remote_file_hashes(machine, paths)
    for path in paths:
        marker = "site-packages/"
        archive_path = f"official/python/{path.split(marker, 1)[1]}" if marker in path else f"official/files/{Path(path).name}"
        deduped.append(
            {
                "source_path": path,
                "archive_path": archive_path,
                "sha256": hashes[path],
            }
        )
    return deduped


def _androidworld_config() -> dict[str, Any]:
    infra = load_json_or_yaml("configs/infra.yaml")
    if not isinstance(infra, dict):
        raise ContractLifecycleError("infra config must be a mapping")
    for machine in list(infra.get("machines") or []):
        if not isinstance(machine, dict):
            continue
        if machine.get("role") != "local_androidworld":
            continue
        python_cfg = dict(machine.get("python") or {})
        benchmark_cfg = dict((machine.get("benchmarks") or {}).get("AndroidWorld") or {})
        return {
            "python_bin": python_cfg.get("python_bin"),
            "install_dir": benchmark_cfg.get("install_dir"),
        }
    raise ContractLifecycleError("local_androidworld machine missing from infra config")


def _run_local_python(python_bin: str, script: str) -> dict[str, Any]:
    completed = subprocess.run(
        [python_bin, "-c", script],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ContractLifecycleError(
            f"local helper failed with {python_bin}:\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    payload = json.loads(completed.stdout)
    if not isinstance(payload, dict):
        raise ContractLifecycleError("helper payload must be a mapping")
    return payload


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


def _appendix_manifest_payload(
    *,
    main_manifest: dict[str, Any],
    selected: dict[str, list[CandidateCase]],
    source_bundle_hash: str,
    candidate_pools: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    agents = list(main_manifest.get("agents") or [])
    domains = []
    for domain_key, display_name, _count, priority in APPENDIX_DOMAIN_SPECS:
        cases = selected[domain_key]
        domains.append(
            {
                "domain": domain_key,
                "domain_display_name": display_name,
                "experiment_type": "appendix",
                "priority": priority,
                "case_unit_count": len(cases),
                "record_slot_count": len(cases) * len(agents),
                "planned_record_slot_ids_hash": sha256_object(
                    [
                        {
                            "case_unit_id": case.case_unit_id,
                            "agent_id": str((agent or {}).get("agent_id") or ""),
                        }
                        for case in cases
                        for agent in agents
                    ]
                ),
                "official_split_eligible_case_units": int(candidate_pools[domain_key].get("candidate_count") or len(cases)),
                "official_split_hash": sha256_file(_candidate_pool_path_for_domain(domain_key)),
                "official_split_exception_id": None,
                "contract_lock_status": "locked_required_before_scoring",
                "claim_scope": "native_aligned",
                "stronger_measurement_mapping": None,
                "case_units": [
                    {
                        "case_unit_id": case.case_unit_id,
                        "task_id": case.task_id,
                        "contract_lock_status": "locked_required_before_scoring",
                    }
                    for case in cases
                ],
            }
        )
    combined_selection_records = [
        {
            "domain": domain_key,
            "case_unit_id": case.case_unit_id,
            "task_id": case.task_id,
            "selection_order_key": str(case.payload.get("selection_order_key") or ""),
            "selection_rank": int(case.payload.get("selection_rank") or 0),
        }
        for domain_key, cases in selected.items()
        for case in sorted(cases, key=lambda row: int(row.payload.get("selection_rank") or 0))
    ]
    declared = [
        item
        for item in list(main_manifest.get("declared_appendix_diagnostics") or [])
        if isinstance(item, dict) and normalize_domain(item.get("domain")) in {"androidworld", "workarena"}
    ]
    required_labels = [
        label
        for label in list(main_manifest.get("required_paper_labels") or [])
        if label == "app:aux-domains"
    ]
    return {
        "schema_version": "experiment_manifest/v1",
        "manifest_id": "androidworld_workarena_appendix_manifest",
        "manifest_version": "0.1.0-prelock",
        "created_at": str(main_manifest.get("created_at") or ""),
        "status": "draft",
        "paper_mapping_path": main_manifest.get("paper_mapping_path"),
        "paper_mapping_sha256": main_manifest.get("paper_mapping_sha256"),
        "source_bundle_hash": source_bundle_hash,
        "agents_config_hash": main_manifest.get("agents_config_hash"),
        "infra_config_hash": main_manifest.get("infra_config_hash"),
        "deterministic_selection": {
            "hash_function": "sha256",
            "hash_salt_hash": sha256_object(APPENDIX_SELECTION_SALT),
            "eligible_case_unit_set_hash": sha256_object(
                {
                    domain: _case_unit_records([case.payload for case in cases])
                    for domain, cases in selected.items()
                }
            ),
            "excluded_smoke_case_units": [],
            "smoke_exclusion_hash": sha256_object([]),
            "case_selection_order_hash": sha256_object(combined_selection_records),
            "bootstrap_seed": int((main_manifest.get("deterministic_selection") or {}).get("bootstrap_seed") or 123),
            "bootstrap_resample_count": int((main_manifest.get("deterministic_selection") or {}).get("bootstrap_resample_count") or 1000),
            "audit_sample_seed": int((main_manifest.get("deterministic_selection") or {}).get("audit_sample_seed") or 456),
            "rerun_subset_selection_rule": "predeclared hash order over locked appendix case units",
        },
        "domains": domains,
        "agents": agents,
        "official_split_exceptions": [],
        "declared_appendix_diagnostics": declared,
        "required_paper_labels": required_labels,
        "contract_locks": [],
    }


def _candidate_pool_path_for_domain(domain: str) -> Path:
    if domain == "androidworld":
        return resolve_repo_path(ANDROIDWORLD_CANDIDATE_POOL_PATH)
    if domain == "workarena":
        return resolve_repo_path(WORKARENA_CANDIDATE_POOL_PATH)
    raise ContractLifecycleError(f"unsupported appendix domain: {domain}")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
