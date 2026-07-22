from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from evidence_system.contracts.common import normalize_domain
from evidence_system.core.schemas import load_json_or_yaml


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "experiments/experiment_manifest.yaml"
SOURCE_BUNDLE_PATH = ROOT / "experiments/evidence_contracts/source_bundles/main_case_units_source_bundle.json"


def test_case_packet_migration_preserves_selected_case_units() -> None:
    manifest = load_json_or_yaml(MANIFEST_PATH)
    source_bundle = json.loads(SOURCE_BUNDLE_PATH.read_text(encoding="utf-8"))

    assert isinstance(manifest, dict)
    assert isinstance(source_bundle, dict)

    manifest_by_domain: dict[str, set[str]] = defaultdict(set)
    for block in manifest.get("domains", []):
        if not isinstance(block, dict):
            continue
        domain = normalize_domain(block.get("domain"))
        for case_unit in block.get("case_units", []):
            if isinstance(case_unit, dict) and case_unit.get("case_unit_id"):
                manifest_by_domain[domain].add(str(case_unit["case_unit_id"]))

    bundle_by_domain: dict[str, set[str]] = defaultdict(set)
    for source in source_bundle.get("sources", []):
        if not isinstance(source, dict):
            continue
        domain = normalize_domain(source.get("domain"))
        case_unit_id = source.get("case_unit_id")
        if case_unit_id:
            bundle_by_domain[domain].add(str(case_unit_id))

    assert Counter({domain: len(case_units) for domain, case_units in manifest_by_domain.items()}) == {
        "agentdojo": 100,
        "appworld": 100,
        "tau3_retail": 100,
    }
    assert Counter({domain: len(case_units) for domain, case_units in bundle_by_domain.items()}) == {
        "agentdojo": 100,
        "appworld": 100,
        "tau3_retail": 100,
    }
    assert dict(manifest_by_domain) == dict(bundle_by_domain)
