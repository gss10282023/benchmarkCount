#!/usr/bin/env python3
"""Build the frozen WebArena-Verified v1.2.3 full-812 Step 19 manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "experiments/official_splits/webarena_verified_official_812.json"
INFRA_PATH = ROOT / "configs/webarena_verified_full_812.yaml"
OUTPUT_PATH = ROOT / "experiments/step19/webarena_verified_full_812_manifest.json"
SHA_PATH = OUTPUT_PATH.with_suffix(OUTPUT_PATH.suffix + ".sha256")
EXPECTED_SOURCE_SHA256 = "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f"
EXPECTED_TAG_COMMIT = "6473f72db5dcefc97b5725b59e734504edc28a21"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")


def object_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_source() -> list[dict[str, Any]]:
    observed_sha = file_sha256(SOURCE_PATH)
    if observed_sha != EXPECTED_SOURCE_SHA256:
        raise SystemExit(f"official source SHA-256 mismatch: {observed_sha}")
    payload = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or len(payload) != 812:
        raise SystemExit(f"expected 812 official tasks, found {len(payload) if isinstance(payload, list) else 'non-list'}")
    tasks = [dict(task) for task in payload]
    task_ids = [int(task["task_id"]) for task in tasks]
    if len(set(task_ids)) != 812:
        raise SystemExit("official task_id values are not unique")
    if set(task_ids) != set(range(812)):
        raise SystemExit("official task_id values must be exactly 0..811")
    for task in tasks:
        if "revision" not in task:
            raise SystemExit(f"task {task['task_id']} is missing revision")
    return sorted(tasks, key=lambda task: int(task["task_id"]))


def load_infra() -> dict[str, Any]:
    payload = yaml.safe_load(INFRA_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("Step 19 infrastructure config must be a mapping")
    servers = payload.get("servers")
    if not isinstance(servers, list) or len(servers) != 3:
        raise SystemExit("Step 19 infrastructure config must contain exactly three servers")
    if len({server["host"] for server in servers}) != 3:
        raise SystemExit("Step 19 server hosts must be unique")
    if len({server["agent_id"] for server in servers}) != 3:
        raise SystemExit("Step 19 agent IDs must be unique")
    for server in servers:
        probe = server.get("openrouter_probe") or {}
        if probe.get("http_status") != 200 or probe.get("exact_response") != "OK":
            raise SystemExit(f"server {server.get('server_id')} lacks a successful OpenRouter probe")
        if probe.get("response_model") != server.get("model"):
            raise SystemExit(f"server {server.get('server_id')} returned the wrong model")
    return payload


def build_manifest(tasks: list[dict[str, Any]], infra: dict[str, Any]) -> dict[str, Any]:
    cases = [
        {
            "ordinal": ordinal,
            "task_id": int(task["task_id"]),
            "revision": int(task["revision"]),
            "sites": list(task.get("sites") or []),
            "source_task_sha256": object_sha256(task),
        }
        for ordinal, task in enumerate(tasks, start=1)
    ]
    servers = list(infra["servers"])
    base_seed = int(infra["common_run_policy"]["base_seed"])
    record_slots: list[dict[str, Any]] = []
    for case in cases:
        for server in servers:
            agent_slug = str(server["agent_id"]).lower().replace(" ", "-")
            record_slots.append(
                {
                    "record_slot_id": f"wv123-task-{case['task_id']:03d}-{agent_slug}",
                    "task_id": case["task_id"],
                    "revision": case["revision"],
                    "seed": base_seed + case["task_id"],
                    "agent_id": server["agent_id"],
                    "model": server["model"],
                    "server_id": server["server_id"],
                }
            )
    if len(record_slots) != 2436:
        raise SystemExit(f"expected 2436 record slots, found {len(record_slots)}")
    if len({slot["record_slot_id"] for slot in record_slots}) != 2436:
        raise SystemExit("record_slot_id values are not unique")

    manifest: dict[str, Any] = {
        "schema_version": "webarena_verified_full_812_manifest/v1",
        "manifest_id": "webarena-verified-v1.2.3-full-812-three-model",
        "manifest_version": "1.0.0",
        "status": "frozen",
        "created_at": infra["verified_at"],
        "benchmark": {
            "name": "WebArena-Verified",
            "version": "v1.2.3",
            "tag_commit": EXPECTED_TAG_COMMIT,
            "split": "full",
            "case_count": 812,
            "source_path": SOURCE_PATH.relative_to(ROOT).as_posix(),
            "source_sha256": EXPECTED_SOURCE_SHA256,
            "task_id_range": [0, 811],
            "task_ids_unique": True,
        },
        "study_design": {
            "models_per_case": 3,
            "record_slot_count": 2436,
            "case_order": infra["common_run_policy"]["case_order"],
            "case_packets_required_for_step19": False,
            "case_packet_phase": "step20",
        },
        "infrastructure_config_path": INFRA_PATH.relative_to(ROOT).as_posix(),
        "infrastructure_config_sha256": file_sha256(INFRA_PATH),
        "servers": servers,
        "common_run_policy": infra["common_run_policy"],
        "cases_sha256": object_sha256(cases),
        "record_slots_sha256": object_sha256(record_slots),
        "cases": cases,
        "record_slots": record_slots,
    }
    core_sha = object_sha256(manifest)
    manifest["integrity"] = {
        "algorithm": "sha256",
        "canonicalization": "sorted-key compact JSON with ensure_ascii=true",
        "scope": "entire manifest excluding integrity",
        "core_sha256": core_sha,
    }
    return manifest


def main() -> None:
    tasks = load_source()
    infra = load_infra()
    manifest = build_manifest(tasks, infra)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_sha = file_sha256(OUTPUT_PATH)
    SHA_PATH.write_text(f"{output_sha}  {OUTPUT_PATH.name}\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "output": OUTPUT_PATH.relative_to(ROOT).as_posix(),
                "file_sha256": output_sha,
                "case_count": len(manifest["cases"]),
                "record_slot_count": len(manifest["record_slots"]),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
