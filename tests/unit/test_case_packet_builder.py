from __future__ import annotations

import importlib.metadata
import json
from collections import Counter
from pathlib import Path

import pytest

from evidence_system.contracts.case_packets import build_case_packet_source_bundle, build_case_packets, derive_source_context
from evidence_system.contracts.agentdojo_packet_extraction import (
    SHARED_SOURCE_BUNDLE_DIRECTORY,
    validate_materialized_agentdojo_case_packet,
    validate_official_source_bundle,
)
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_file


ROOT = Path(__file__).resolve().parents[2]


def test_full_agentdojo_packet_materializes_pinned_evidence_basis(
    tmp_path: Path,
) -> None:
    try:
        installed_version = importlib.metadata.version("agentdojo")
    except importlib.metadata.PackageNotFoundError:
        pytest.skip("pinned AgentDojo package is not installed")
    if installed_version != "0.1.35":
        pytest.skip("pinned AgentDojo package is not installed")

    case_unit_id = "v1.2.2:workspace:user_task_0:injection_task_0"
    built = build_case_packets(
        manifest_path=(
            ROOT
            / "experiments/agentdojo_full_v1.2.2_direct/experiment_manifest.yaml"
        ),
        official_splits_path=(
            ROOT / "experiments/agentdojo_full_v1.2.2_direct/official_splits"
        ),
        output_root=tmp_path / "case_packets",
        case_unit_ids=[case_unit_id],
    )

    assert len(built) == 1
    case_dir = Path(built[0].case_dir)
    raw_case = case_dir / "raw_case"
    manifest = json.loads(
        (case_dir / "raw_case_manifest.json").read_text(encoding="utf-8")
    )
    assert "derived/checklist_basis.json" in manifest["packet_files"]
    assert "derived/native_decision_rules.json" in manifest["packet_files"]
    assert "derived/stronger_measurement_basis.json" in manifest["packet_files"]
    assert "official/state_schema_excerpts.json" in manifest["packet_files"]
    assert "derived/artifact_inventory.json" in manifest["packet_files"]
    assert "official/case_definition.json" in manifest["official_files"]
    assert "official/evaluator_oracle_excerpts.json" in manifest["official_files"]
    assert not any(path.startswith("official/src/agentdojo/") for path in manifest["copied_files"])
    assert len(manifest["copied_files"]) == 8
    for relative in manifest["copied_files"]:
        assert manifest["sha256_per_file"][relative] == sha256_file(
            raw_case / relative
        )

    wiring = json.loads(
        (raw_case / "derived/native_decision_rules.json").read_text(
            encoding="utf-8"
        )
    )
    assert [
        item["component_id"]
        for item in wiring["released_components"]
    ] == [
        "benign_user_utility",
        "injected_user_utility",
        "injected_security_breach",
    ]
    assert (
        wiring["local_evidence_system_aggregation"]["classification"]
        .lower()
        .startswith("local paired-case aggregation")
    )
    assert wiring["goal_role_mapping"]["native_user_goal"]["source"] == (
        "official/case_definition.json::user_goal.text"
    )
    assert wiring["goal_role_mapping"]["injected_attack_goal"]["source"] == (
        "official/case_definition.json::injection_goal.text"
    )
    aggregation = wiring["local_evidence_system_aggregation"]
    assert len(aggregation["decision_precedence"]) == 3
    assert aggregation[
        "mutually_exclusive_and_exhaustive_over_three_valued_inputs"
    ]
    assert aggregation["local_label_mapping"] == {
        "success_expression_true": "success",
        "failure_expression_true": "fail",
        "otherwise": "unknown",
    }

    stronger = json.loads(
        (raw_case / "derived/stronger_measurement_basis.json").read_text(
            encoding="utf-8"
        )
    )
    assert "locked_stronger_conditions" not in stronger
    assert stronger["pre_draft_lock_status"] == "candidate_review_required"
    assert stronger["lock_destination"] == "checklist.stronger.additional_conditions"

    artifacts = json.loads(
        (raw_case / "derived/artifact_inventory.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(artifacts["episodes"]) == 3
    assert not artifacts["post_run_state"]["standalone_full_snapshot_retained"]
    assert "equal one single entry" in artifacts["artifact_name_rule"]

    bundle_root = tmp_path / "source_bundles" / SHARED_SOURCE_BUNDLE_DIRECTORY
    bundle = validate_official_source_bundle(bundle_root)
    assert bundle["file_count"] == 112
    assert bundle["git_commit"] == "a75aba7631d3ca5fb7ab938965c97ead2f9ff84b"
    assert not (bundle_root / "source/src/agentdojo/__pycache__").exists()
    validation = validate_materialized_agentdojo_case_packet(
        raw_case,
        case_unit_id=case_unit_id,
        bundle_root=bundle_root,
    )
    assert validation["deterministic_reextraction"]
    assert validation["semantic_contract"]
    assert "official/src/agentdojo/benchmark.py" not in (
        case_dir / "case_packet.md"
    ).read_text(encoding="utf-8")
    excerpt_file = raw_case / "official/evaluator_oracle_excerpts.json"
    excerpt_file.write_bytes(excerpt_file.read_bytes() + b"\n")
    with pytest.raises(
        ContractLifecycleError, match="deterministic packet re-extraction differs"
    ):
        validate_materialized_agentdojo_case_packet(
            raw_case,
            case_unit_id=case_unit_id,
            bundle_root=bundle_root,
        )


def test_build_case_packets_materializes_sample_cases(tmp_path: Path) -> None:
    built = build_case_packets(
        manifest_path=ROOT / "experiments/experiment_manifest.yaml",
        official_splits_path=ROOT / "experiments/official_splits",
        output_root=tmp_path / "case_packets",
        per_domain_limit=1,
    )

    assert len(built) == 4
    assert Counter(item.domain for item in built) == {
        "agentdojo": 1,
        "appworld": 1,
        "webarena_verified": 1,
        "tau3_retail": 1,
    }
    for item in built:
        case_dir = Path(item.case_dir)
        assert (case_dir / "raw_case").is_dir()
        assert (case_dir / "raw_case_manifest.json").is_file()
        assert (case_dir / "case_packet.md").is_file()


def test_raw_case_manifest_has_sha256_for_all_files(tmp_path: Path) -> None:
    built = build_case_packets(
        manifest_path=ROOT / "experiments/experiment_manifest.yaml",
        official_splits_path=ROOT / "experiments/official_splits",
        output_root=tmp_path / "case_packets",
        per_domain_limit=1,
    )

    for item in built:
        manifest_path = Path(item.raw_case_manifest_path)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        raw_case_dir = manifest_path.parent / "raw_case"
        copied_files = list(manifest["copied_files"])
        assert copied_files
        assert set(copied_files) == set(manifest["sha256_per_file"])
        for relative in copied_files:
            file_path = raw_case_dir / relative
            assert file_path.is_file()
            assert manifest["sha256_per_file"][relative] == sha256_file(file_path)


def test_build_case_packets_materializes_miniwob_case_from_local_sources(tmp_path: Path) -> None:
    source_root = tmp_path / "official_src"
    python_root = source_root / "site-packages" / "browsergym" / "miniwob"
    install_root = source_root / "miniwob-plusplus"
    html_root = install_root / "miniwob" / "html" / "miniwob"
    core_root = install_root / "miniwob" / "html" / "core"
    common_root = install_root / "miniwob" / "html" / "common"

    (python_root / "__init__.py").parent.mkdir(parents=True, exist_ok=True)
    (python_root / "__init__.py").write_text("ALL_MINIWOB_TASKS = []\n", encoding="utf-8")
    (python_root / "all.py").write_text("class ClickTestTask: ...\n", encoding="utf-8")
    (python_root / "base.py").write_text("class AbstractMiniwobTask: ...\n", encoding="utf-8")
    html_root.mkdir(parents=True, exist_ok=True)
    core_root.mkdir(parents=True, exist_ok=True)
    common_root.mkdir(parents=True, exist_ok=True)
    (core_root / "core.js").write_text("window.core = {};\n", encoding="utf-8")
    (common_root / "ui_utils.js").write_text("window.ui = {};\n", encoding="utf-8")
    (html_root / "click-test.html").write_text(
        """<!DOCTYPE html>
<html>
<head>
<title>Click Test Task</title>
<script src="../core/core.js"></script>
<script src="../common/ui_utils.js"></script>
</head>
<body>
  <div id="query">Click the button.</div>
</body>
</html>
""",
        encoding="utf-8",
    )

    official_splits = tmp_path / "official_splits"
    official_splits.mkdir(parents=True, exist_ok=True)
    selected_sources = {
        "benchmark": "MiniWoB++",
        "schema_version": "official_case_source.miniwob_selected_tasks.v1",
        "selected_count": 1,
        "items": [
            {
                "case_unit_id": "miniwob.click-test",
                "task_id": "miniwob.click-test",
                "class_name": "ClickTestTask",
                "module": "browsergym.miniwob.all",
                "base_class_name": "AbstractMiniwobTask",
                "base_module": "browsergym.miniwob.base",
                "subdomain": "click-test",
                "nondeterministic": False,
                "html_title": "Click Test Task",
                "static_query_text": "Click the button.",
                "html_asset_files": [
                    str(core_root / "core.js"),
                    str(common_root / "ui_utils.js"),
                ],
                "source_ref": "miniwob://miniwob.click-test",
                "source_sha256": "abc123",
                "official_files": [
                    {
                        "source_path": str(python_root / "__init__.py"),
                        "archive_path": "official/python/browsergym/miniwob/__init__.py",
                    },
                    {
                        "source_path": str(python_root / "all.py"),
                        "archive_path": "official/python/browsergym/miniwob/all.py",
                    },
                    {
                        "source_path": str(python_root / "base.py"),
                        "archive_path": "official/python/browsergym/miniwob/base.py",
                    },
                    {
                        "source_path": str(html_root / "click-test.html"),
                        "archive_path": "official/install/miniwob/html/miniwob/click-test.html",
                    },
                    {
                        "source_path": str(core_root / "core.js"),
                        "archive_path": "official/install/miniwob/html/core/core.js",
                    },
                    {
                        "source_path": str(common_root / "ui_utils.js"),
                        "archive_path": "official/install/miniwob/html/common/ui_utils.js",
                    },
                ],
                "packet_files": [
                    "official/python/browsergym/miniwob/__init__.py",
                    "official/python/browsergym/miniwob/all.py",
                    "official/python/browsergym/miniwob/base.py",
                    "official/install/miniwob/html/miniwob/click-test.html",
                    "official/install/miniwob/html/core/core.js",
                    "official/install/miniwob/html/common/ui_utils.js",
                    "derived/selected_task_source.json",
                ],
            }
        ],
    }
    (official_splits / "miniwob_selected_task_sources.json").write_text(
        json.dumps(selected_sources, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    manifest = {
        "schema_version": "experiment_manifest/v1",
        "manifest_id": "miniwob-test",
        "manifest_version": "0.1.0",
        "created_at": "2026-05-06T00:00:00+00:00",
        "status": "draft",
        "paper_mapping_path": "experiments/paper_mapping.md",
        "paper_mapping_sha256": "0" * 64,
        "source_bundle_hash": "0" * 64,
        "agents_config_hash": "0" * 64,
        "infra_config_hash": "0" * 64,
        "deterministic_selection": {
            "hash_function": "sha256",
            "hash_salt_hash": "0" * 64,
            "eligible_case_unit_set_hash": "0" * 64,
            "excluded_smoke_case_units": [],
            "smoke_exclusion_hash": "0" * 64,
            "case_selection_order_hash": "0" * 64,
            "bootstrap_seed": 123,
            "bootstrap_resample_count": 1000,
            "audit_sample_seed": 456,
            "rerun_subset_selection_rule": "test",
        },
        "domains": [
            {
                "domain": "miniwob",
                "domain_display_name": "MiniWoB++",
                "experiment_type": "diagnostic",
                "priority": "P3",
                "case_unit_count": 1,
                "record_slot_count": 1,
                "planned_record_slot_ids_hash": "0" * 64,
                "official_split_eligible_case_units": 1,
                "official_split_hash": "0" * 64,
                "official_split_exception_id": None,
                "contract_lock_status": "draft_required",
                "claim_scope": "native_aligned",
                "stronger_measurement_mapping": None,
                "case_units": [
                    {
                        "case_unit_id": "miniwob.click-test",
                        "task_id": "miniwob.click-test",
                        "contract_lock_status": "draft_required",
                    }
                ],
            }
        ],
        "agents": [],
        "official_split_exceptions": [],
        "declared_appendix_diagnostics": [],
        "required_paper_labels": [],
        "contract_locks": [],
    }
    manifest_path = tmp_path / "miniwob_manifest.yaml"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output_root = tmp_path / "case_packets"
    built = build_case_packets(
        manifest_path=manifest_path,
        official_splits_path=official_splits,
        output_root=output_root,
    )

    assert len(built) == 1
    case_dir = Path(built[0].case_dir)
    packet = Path(built[0].case_packet_path).read_text(encoding="utf-8")
    assert "miniwob.click-test" in packet
    assert "official/install/miniwob/html/miniwob/click-test.html" in packet
    manifest_payload = json.loads(
        (case_dir / "raw_case_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest_payload["packet_files"] == [
        "derived/drafting_context.json",
        "derived/official_source_excerpts.json",
        "derived/selected_task_source.json",
        "official/install/miniwob/html/miniwob/click-test.html",
    ]
    assert "official/python/browsergym/miniwob/all.py" in manifest_payload["official_files"]
    assert "### `official/python/browsergym/miniwob/all.py`" not in packet
    assert "### `official/python/browsergym/miniwob/base.py`" not in packet
    context_payload = json.loads(
        (case_dir / "raw_case/derived/drafting_context.json").read_text(
            encoding="utf-8"
        )
    )
    assert context_payload["locked_before_outcomes"] is True
    assert context_payload["contains_agent_outcomes"] is False
    assert context_payload["official_policy"]["applicability"] == "N/A"
    assert context_payload["artifact_inventory"]["artifact_types"] == [
        "browser_artifact",
        "post_state",
        "trace",
        "native_evaluator_input",
        "native_evaluator_output",
        "structured_output",
        "file",
    ]

    source_bundle_path = build_case_packet_source_bundle(
        manifest_path=manifest_path,
        case_packets_root=output_root,
        previous_source_bundle_path=tmp_path / "missing_source_bundle.json",
        output_path=tmp_path / "miniwob_source_bundle.json",
        allow_generated_contract_ids=True,
    )
    source_bundle = json.loads(source_bundle_path.read_text(encoding="utf-8"))
    assert source_bundle["manifest_sha256"] == sha256_file(manifest_path)
    context = derive_source_context(source_bundle["sources"][0])
    assert context["task_text"]["task_id"] == "miniwob.click-test"
    assert context["task_text"]["static_query_text"] == "Click the button."


def test_source_bundle_can_omit_manifest_hash_to_avoid_hash_cycle(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    packet_root = tmp_path / "case_packets"
    case_dir = packet_root / "miniwob" / "miniwob.click-test"
    case_dir.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "domains": [
                    {
                        "domain": "miniwob",
                        "case_units": [
                            {
                                "case_unit_id": "miniwob.click-test",
                                "task_id": "miniwob.click-test",
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (case_dir / "case_packet.md").write_text("locked packet\n", encoding="utf-8")
    (case_dir / "raw_case_manifest.json").write_text("{}\n", encoding="utf-8")

    bundle_path = build_case_packet_source_bundle(
        manifest_path=manifest_path,
        case_packets_root=packet_root,
        previous_source_bundle_path=tmp_path / "missing.json",
        output_path=tmp_path / "bundle.json",
        allow_generated_contract_ids=True,
        include_manifest_sha256=False,
    )

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert bundle["manifest_path"]
    assert "manifest_sha256" not in bundle
