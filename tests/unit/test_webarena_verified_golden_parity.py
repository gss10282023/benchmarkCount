from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

import pytest

from evidence_system.adapters import webarena_verified_official_scorer as scorer
from scripts import build_webarena_verified_golden_parity_acceptance as aggregate
from scripts import run_webarena_verified_golden_parity as parity


ROOT = Path(__file__).resolve().parents[2]
RAW_DATASET = (
    ROOT
    / "experiments"
    / "official_splits"
    / "webarena_verified_v1_2_3_source"
    / "assets"
    / "dataset"
    / "webarena-verified.json"
)
HOSTS_ROOT = (
    ROOT
    / "experiments"
    / "step20"
    / "webarena_verified"
    / "golden_parity"
    / "hosts"
)


def test_golden_fixtures_cover_required_success_failure_and_categories(
    tmp_path: Path,
) -> None:
    assert len(parity.FIXTURES) == 6
    assert {fixture.category for fixture in parity.FIXTURES} == aggregate.EXPECTED_CATEGORIES
    assert sum(fixture.expected_status == "success" for fixture in parity.FIXTURES) == 3
    assert sum(fixture.expected_status == "failure" for fixture in parity.FIXTURES) == 3

    tasks = parity._load_tasks(RAW_DATASET)
    for fixture in parity.FIXTURES:
        response = parity._response(
            tasks[fixture.task_id], matches=fixture.response_should_match
        )
        assert set(response) == {
            "task_type",
            "status",
            "retrieved_data",
            "error_details",
        }
        assert response["task_type"] in {"RETRIEVE", "MUTATE", "NAVIGATE"}
        har_path = tmp_path / f"{fixture.fixture_id}.har"
        har_path.write_text(
            json.dumps(
                parity._har(
                    fixture.task_id, matches=fixture.network_should_match
                )
            ),
            encoding="utf-8",
        )
        scorer._validate_full_embedded_har(har_path)


def _aggregate_args(hosts_root: Path, output: Path) -> argparse.Namespace:
    return argparse.Namespace(
        hosts_root=hosts_root,
        output=output,
        golden_script=ROOT / "scripts" / "run_webarena_verified_golden_parity.py",
        scorer_source=(
            ROOT
            / "src"
            / "evidence_system"
            / "adapters"
            / "webarena_verified_official_scorer.py"
        ),
    )


def test_three_host_golden_parity_acceptance_is_strict_and_private_free(
    tmp_path: Path,
) -> None:
    result = aggregate.build(_aggregate_args(HOSTS_ROOT, tmp_path / "acceptance.json"))

    assert result["status"] == "pass"
    assert result["host_count"] == 3
    assert result["exact_raw_cli_adapter_comparisons"] == 18
    assert result["cross_host_canonical_result_match_count"] == 6
    assert result["private_evaluator_payload_in_aggregate"] is False
    assert not parity._private_key_present(result)


def test_aggregate_rejects_cross_host_canonical_result_drift(tmp_path: Path) -> None:
    copied = tmp_path / "hosts"
    shutil.copytree(HOSTS_ROOT, copied)
    path = copied / aggregate.HOST_IDS[-1] / "acceptance.json"
    receipt = json.loads(path.read_text(encoding="utf-8"))
    receipt["fixtures"][0]["raw_canonical_result_sha256"] = "0" * 64
    path.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(aggregate.AcceptanceError, match="canonical result hash mismatch"):
        aggregate.build(_aggregate_args(copied, tmp_path / "rejected.json"))
