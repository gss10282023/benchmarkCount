#!/usr/bin/env python3
"""Validate and aggregate three-host WebArena-Verified golden parity receipts."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping


SCHEMA_VERSION = "webarena_verified_golden_parity_aggregate/v1"
HOST_IDS = (
    "webarena-gpt54-ord",
    "webarena-claude47-ord",
    "webarena-deepseek-v4pro-ord",
)
EXPECTED_CATEGORIES = {
    "agent_response_only_retrieval",
    "network_event_mutation",
    "multi_site_network_event",
}


class AcceptanceError(RuntimeError):
    """A host receipt or cross-host parity invariant failed."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hosts-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--golden-script", type=Path, required=True)
    parser.add_argument("--scorer-source", type=Path, required=True)
    return parser


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise AcceptanceError(f"receipt must be a regular non-symlink file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AcceptanceError(f"receipt is not readable JSON: {path}") from exc
    if not isinstance(value, dict):
        raise AcceptanceError(f"receipt is not a JSON object: {path}")
    return value


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, 0o644)
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def _validate_host(host_id: str, path: Path, value: Mapping[str, Any]) -> None:
    if value.get("schema_version") != "webarena_verified_golden_parity/v1":
        raise AcceptanceError(f"{host_id}: wrong receipt schema")
    if value.get("status") != "pass":
        raise AcceptanceError(f"{host_id}: host parity did not pass")
    exact = value.get("raw_cli_adapter_exact_match_count")
    if value.get("fixture_count") != 6 or exact != 6:
        raise AcceptanceError(f"{host_id}: expected six exact parity fixtures")
    if value.get("success_fixture_count") != 3 or value.get("failure_fixture_count") != 3:
        raise AcceptanceError(f"{host_id}: success/failure fixture balance is wrong")
    if set(value.get("categories") or []) != EXPECTED_CATEGORIES:
        raise AcceptanceError(f"{host_id}: required parity categories are incomplete")
    if value.get("public_receipt_contains_private_evaluator_payload") is not False:
        raise AcceptanceError(f"{host_id}: public receipt privacy assertion failed")
    fixtures = value.get("fixtures")
    if not isinstance(fixtures, list) or len(fixtures) != 6:
        raise AcceptanceError(f"{host_id}: fixture list is invalid")
    for fixture in fixtures:
        if not isinstance(fixture, Mapping):
            raise AcceptanceError(f"{host_id}: fixture is not an object")
        if fixture.get("full_result_exact_match") is not True:
            raise AcceptanceError(f"{host_id}: raw/adapter full result mismatch")
        if fixture.get("raw_canonical_result_sha256") != fixture.get(
            "adapter_canonical_result_sha256"
        ):
            raise AcceptanceError(f"{host_id}: canonical result hash mismatch")
        if fixture.get("actual_status") != fixture.get("expected_status"):
            raise AcceptanceError(f"{host_id}: fixture status mismatch")
        if fixture.get("raw_cli_exit_code") != 0 or fixture.get("adapter_exit_code") != 0:
            raise AcceptanceError(f"{host_id}: evaluator invocation failed")
    if path.stat().st_size <= 0:
        raise AcceptanceError(f"{host_id}: empty receipt")


def build(args: argparse.Namespace) -> dict[str, Any]:
    if not args.hosts_root.is_dir():
        raise AcceptanceError("hosts root does not exist")
    actual_host_ids = {path.name for path in args.hosts_root.iterdir() if path.is_dir()}
    if actual_host_ids != set(HOST_IDS):
        raise AcceptanceError(
            f"host receipt directories mismatch: expected {list(HOST_IDS)}, got {sorted(actual_host_ids)}"
        )
    if not args.golden_script.is_file() or not args.scorer_source.is_file():
        raise AcceptanceError("golden script or scorer source is missing")

    host_receipts: list[tuple[str, Path, dict[str, Any]]] = []
    for host_id in HOST_IDS:
        path = args.hosts_root / host_id / "acceptance.json"
        value = _load(path)
        _validate_host(host_id, path, value)
        host_receipts.append((host_id, path, value))

    baseline = host_receipts[0][2]
    common_keys = (
        "official_evaluator_image",
        "official_dataset_sha256",
        "runtime_config_sha256",
        "task_contract_index_sha256",
        "categories",
    )
    for host_id, _, receipt in host_receipts[1:]:
        for key in common_keys:
            if receipt.get(key) != baseline.get(key):
                raise AcceptanceError(f"{host_id}: cross-host {key} mismatch")

    baseline_fixtures = {
        str(item["fixture_id"]): item for item in baseline["fixtures"]
    }
    cross_host_fixture_hashes: list[dict[str, Any]] = []
    for fixture_id in sorted(baseline_fixtures):
        base = baseline_fixtures[fixture_id]
        canonical_hash = base["adapter_canonical_result_sha256"]
        for host_id, _, receipt in host_receipts[1:]:
            fixtures = {str(item["fixture_id"]): item for item in receipt["fixtures"]}
            if set(fixtures) != set(baseline_fixtures):
                raise AcceptanceError(f"{host_id}: fixture identity set mismatch")
            current = fixtures[fixture_id]
            stable_fields = (
                "category",
                "task_id",
                "task_revision",
                "sites",
                "expected_status",
                "actual_status",
                "score",
                "evaluator_names",
                "evaluator_statuses",
                "adapter_canonical_result_sha256",
            )
            for key in stable_fields:
                if current.get(key) != base.get(key):
                    raise AcceptanceError(
                        f"{host_id}: cross-host fixture {fixture_id} field {key} mismatch"
                    )
        cross_host_fixture_hashes.append(
            {
                "fixture_id": fixture_id,
                "category": base["category"],
                "task_id": base["task_id"],
                "expected_status": base["expected_status"],
                "canonical_official_result_sha256": canonical_hash,
                "matching_host_count": len(host_receipts),
            }
        )

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass",
        "host_count": len(host_receipts),
        "host_ids": list(HOST_IDS),
        "fixture_count_per_host": 6,
        "total_raw_cli_adapter_comparisons": 18,
        "exact_raw_cli_adapter_comparisons": 18,
        "cross_host_canonical_result_match_count": 6,
        "categories": sorted(EXPECTED_CATEGORIES),
        "official_evaluator_image": baseline["official_evaluator_image"],
        "official_dataset_sha256": baseline["official_dataset_sha256"],
        "runtime_config_sha256": baseline["runtime_config_sha256"],
        "task_contract_index_sha256": baseline["task_contract_index_sha256"],
        "golden_script_sha256": _sha256(args.golden_script),
        "scorer_source_sha256": _sha256(args.scorer_source),
        "host_receipts": [
            {
                "host_id": host_id,
                "path": str(path),
                "sha256": _sha256(path),
                "status": "pass",
            }
            for host_id, path, _ in host_receipts
        ],
        "fixtures": cross_host_fixture_hashes,
        "private_evaluator_payload_in_aggregate": False,
    }
    _atomic_json(args.output, result)
    return result


def main() -> int:
    args = _parser().parse_args()
    try:
        result = build(args)
    except Exception as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
