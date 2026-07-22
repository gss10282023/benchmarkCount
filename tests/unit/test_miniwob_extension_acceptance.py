from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from evidence_system.cli import validate_miniwob_extension as acceptance_cli
from evidence_system.contracts import case_packets
from evidence_system.contracts import miniwob_extension_acceptance as acceptance
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_file, sha256_object


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_CATALOG = ROOT / "experiments/official_splits/miniwob_remaining22/miniwob_official_task_catalog_122.json"


def test_strict_acceptance_validates_50_50_22_and_every_packet_byte(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fixture = _build_fixture(monkeypatch, tmp_path)

    receipt = acceptance.validate_miniwob_extension(**fixture["kwargs"])

    assert receipt["status"] == "ok"
    assert receipt["all_hard_gates_passed"] is True
    assert receipt["cohort_union_count"] == 122
    assert receipt["cohorts_pairwise_disjoint"] is True
    assert receipt["manifest"]["record_slot_count"] == 66
    assert receipt["packets"]["packet_count"] == 22
    assert receipt["packets"]["verified_raw_file_count"] == 154
    assert receipt["packets"]["stronger_condition_case_count"] == 7
    assert receipt["packets"]["stronger_condition_count"] == 7
    assert receipt["packets"]["max_compact_packet_bytes"] <= acceptance.MAX_COMPACT_PACKET_BYTES
    assert receipt["privacy"]["violations"] == 0


def test_strict_acceptance_rejects_raw_file_hash_drift(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fixture = _build_fixture(monkeypatch, tmp_path)
    raw_file = tmp_path / fixture["first_raw_file"]
    raw_file.write_text(raw_file.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")

    with pytest.raises(ContractLifecycleError, match="raw file hash mismatch"):
        acceptance.validate_miniwob_extension(**fixture["kwargs"])


def test_cli_rejects_public_host_path_and_writes_no_receipt(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture = _build_fixture(monkeypatch, tmp_path)
    catalog_path = tmp_path / "catalog.json"
    catalog = _load_json(catalog_path)
    catalog["private_note"] = "/Users/alice/private/miniwob"
    _write_json(catalog_path, catalog)
    _refresh_manifest_bundle_hashes(tmp_path)
    output = tmp_path / "receipt.json"

    code = acceptance_cli.main([*fixture["cli_args"], "--output", str(output), "--json"])

    captured = capsys.readouterr()
    assert code == 2
    assert not output.exists()
    assert "public_artifact_path_anonymization" in captured.err


def test_cli_writes_machine_readable_receipt_after_success(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fixture = _build_fixture(monkeypatch, tmp_path)
    output = tmp_path / "receipt.json"

    code = acceptance_cli.main([*fixture["cli_args"], "--output", str(output), "--json"])

    assert code == 0
    receipt = _load_json(output)
    assert receipt["schema_version"] == "miniwob_extension_acceptance_receipt/v1"
    assert receipt["all_hard_gates_passed"] is True


def _build_fixture(monkeypatch: pytest.MonkeyPatch, root: Path) -> dict[str, Any]:
    original_resolve = acceptance.resolve_repo_path

    def resolve_fixture_path(path: str | Path) -> Path:
        candidate = Path(path)
        return candidate if candidate.is_absolute() else root / candidate

    monkeypatch.setattr(acceptance, "resolve_repo_path", resolve_fixture_path)
    # Keep a reference solely to make the intended isolation explicit and to
    # avoid a future refactor accidentally patching the shared path helper.
    assert original_resolve is not resolve_fixture_path

    catalog = _load_json(REFERENCE_CATALOG)
    _write_json(root / "catalog.json", catalog)
    ordered_catalog = sorted(catalog["items"], key=lambda item: item["selection_rank"])

    selected_payloads: dict[str, dict[str, Any]] = {}
    cohort_specs = {"first.json": (0, 50), "second.json": (50, 100), "remaining.json": (100, 122)}
    for filename, (start, end) in cohort_specs.items():
        items: list[dict[str, Any]] = []
        for catalog_item in ordered_catalog[start:end]:
            item = dict(catalog_item)
            class_name = str(item["class_name"])
            subdomain = str(item["subdomain"])
            official_payloads = {
                "official/python/browsergym/miniwob/all.py": f"class {class_name}:\n    pass\n",
                "official/python/browsergym/miniwob/base.py": (
                    "class AbstractMiniwobTask:\n"
                    "    def _get_goal(self):\n        return self.page.evaluate('core.getUtterance()')\n"
                    "    def _get_info(self):\n        return {'RAW_REWARD_GLOBAL': 0, 'DONE_GLOBAL': False}\n"
                    "    def validate(self, page, chat_messages):\n        return 0, False, '', self._get_info()\n"
                ),
                "official/install/miniwob/html/core/core.js": (
                    "var WOB_REWARD_GLOBAL = 0;\nvar WOB_RAW_REWARD_GLOBAL = 0;\n"
                    "var WOB_REWARD_REASON = null;\nvar WOB_DONE_GLOBAL = false;\n"
                    "var WOB_EPISODE_ID = 0;\nvar WOB_TASK_READY = true;\n"
                    "core.endEpisode = function(reward, time_proportional, reason) {\n"
                    "  WOB_RAW_REWARD_GLOBAL = reward;\n  WOB_DONE_GLOBAL = true;\n};\n"
                ),
                f"official/install/miniwob/html/miniwob/{subdomain}.html": (
                    "<!DOCTYPE html><html><script>function genProblem() { "
                    "core.endEpisode(1, true); }</script></html>\n"
                ),
            }
            item["official_files"] = [
                {
                    "source_path": f"<MINIWOB_TEST_ROOT>/{archive_path}",
                    "archive_path": archive_path,
                    "sha256": sha256_object({"raw": content}),
                }
                for archive_path, content in official_payloads.items()
            ]
            task_html_archive = f"official/install/miniwob/html/miniwob/{subdomain}.html"
            item["packet_files"] = [
                *case_packets.MINIWOB_COMPACT_DERIVED_FILES,
                task_html_archive,
            ]
            item["source_ref"] = f"miniwob://{item['task_id']}"
            item["source_sha256"] = sha256_object({"task_id": item["task_id"]})
            item["_test_official_payloads"] = official_payloads
            items.append(item)
        payload = {
            "benchmark": "MiniWoB++",
            "schema_version": "official_case_source.miniwob_selected_tasks.v1",
            "selected_count": len(items),
            "selection_hash_function": "sha256",
            "selection_salt_hash": acceptance.EXPECTED_SELECTION_SALT_HASH,
            "candidate_pool_path": "catalog.json",
            "source_mode": "local",
            "items": items,
        }
        selected_payloads[filename] = payload

    packet_root = root / "packets/miniwob"
    sources: list[dict[str, Any]] = []
    remaining_items = selected_payloads["remaining.json"]["items"]
    first_raw_file = ""
    for index, item in enumerate(remaining_items):
        case_id = item["case_unit_id"]
        case_dir = packet_root / case_id
        raw_root = case_dir / "raw_case"
        official_payloads = item.pop("_test_official_payloads")
        for descriptor in item["official_files"]:
            archive_path = descriptor["archive_path"]
            official_file = raw_root / archive_path
            official_file.parent.mkdir(parents=True, exist_ok=True)
            official_file.write_text(official_payloads[archive_path], encoding="utf-8")
            descriptor["sha256"] = sha256_file(official_file)
        task_html = item["packet_files"][-1]
        excerpts = case_packets._miniwob_source_excerpts(
            raw_case_dir=raw_root,
            case_unit_id=case_id,
            task_id=item["task_id"],
            class_name=item["class_name"],
            task_class_source="official/python/browsergym/miniwob/all.py",
            base_source="official/python/browsergym/miniwob/base.py",
            core_source="official/install/miniwob/html/core/core.js",
            task_html=task_html,
        )
        excerpts_file = raw_root / "derived/official_source_excerpts.json"
        _write_json(excerpts_file, excerpts)
        context = case_packets._miniwob_drafting_context(
            case_unit_id=case_id,
            task_id=item["task_id"],
            payload=item,
            task_html=task_html,
            excerpts_rel="derived/official_source_excerpts.json",
        )
        context_file = raw_root / "derived/drafting_context.json"
        _write_json(context_file, context)
        derived_file = raw_root / "derived/selected_task_source.json"
        _write_json(derived_file, item)
        copied_files = sorted(
            [descriptor["archive_path"] for descriptor in item["official_files"]]
            + list(case_packets.MINIWOB_COMPACT_DERIVED_FILES)
        )
        file_sources = {
            descriptor["archive_path"]: descriptor["source_path"]
            for descriptor in item["official_files"]
        }
        file_sources.update(
            {
                "derived/drafting_context.json": "derived://miniwob-pre-run-drafting-context/v1",
                "derived/official_source_excerpts.json": "derived://miniwob-official-source-excerpts/v1",
                "derived/selected_task_source.json": item["source_ref"],
            }
        )
        raw_manifest = {
            "domain": "miniwob",
            "case_unit_id": case_id,
            "task_id": item["task_id"],
            "source_refs": [
                *[descriptor["source_path"] for descriptor in item["official_files"]],
                item["source_ref"],
            ],
            "copied_files": copied_files,
            "official_files": sorted(
                descriptor["archive_path"] for descriptor in item["official_files"]
            ),
            "derived_files": sorted(case_packets.MINIWOB_COMPACT_DERIVED_FILES),
            "packet_files": item["packet_files"],
            "sha256_per_file": {
                relative: sha256_file(raw_root / relative) for relative in copied_files
            },
            "file_sources": file_sources,
        }
        raw_manifest_path = case_dir / "raw_case_manifest.json"
        _write_json(raw_manifest_path, raw_manifest)
        packet_path = case_dir / "case_packet.md"
        packet_path.write_text(
            case_packets.render_case_packet(
                domain="miniwob",
                case_unit_id=case_id,
                task_id=item["task_id"],
                raw_case_dir=raw_root,
                raw_case_manifest=raw_manifest,
            ),
            encoding="utf-8",
        )
        sources.append(
            {
                "domain": "miniwob",
                "case_unit_id": case_id,
                "task_id": item["task_id"],
                "contract_id": f"ec_miniwob_{case_id}_contract_v1_0_0",
                "draft_input": {
                    "case_packet_path": f"packets/miniwob/{case_id}/case_packet.md",
                    "case_packet_sha256": sha256_file(packet_path),
                    "raw_case_manifest_path": f"packets/miniwob/{case_id}/raw_case_manifest.json",
                    "raw_case_manifest_sha256": sha256_file(raw_manifest_path),
                },
            }
        )
        if index == 0:
            first_raw_file = (
                f"packets/miniwob/{case_id}/raw_case/"
                "official/python/browsergym/miniwob/all.py"
            )

    for payload in selected_payloads.values():
        for item in payload["items"]:
            item.pop("_test_official_payloads", None)

    for filename, payload in selected_payloads.items():
        _write_json(root / filename, payload)

    infra = {"schema_version": "infra/v1", "machines": [{"enabled": True}]}
    _write_json(root / "infra.json", infra)
    roles = {
        agent_id: {"provider": "test", "model": f"model-{agent_id[-1]}", "temperature": 0}
        for agent_id in acceptance.EXPECTED_AGENTS
    }
    agents = {
        "schema_version": "agents/v1",
        "experimental_agents": roles,
        "main_domain_agent_map": {"miniwob": list(acceptance.EXPECTED_AGENTS)},
    }
    _write_json(root / "agents.json", agents)
    case_refs = [{"case_unit_id": item["case_unit_id"], "task_id": item["task_id"]} for item in remaining_items]
    manifest = {
        "schema_version": "experiment_manifest/v1",
        "manifest_id": "test-remaining22",
        "result_namespace": acceptance.EXPECTED_RESULT_NAMESPACE,
        "infra_config_hash": sha256_file(root / "infra.json"),
        "agents_config_hash": sha256_file(root / "agents.json"),
        "source_bundle_hash": "0" * 64,
        "agents": [
            {"agent_id": agent_id, "config_hash": sha256_object(roles[agent_id])}
            for agent_id in acceptance.EXPECTED_AGENTS
        ],
        "deterministic_selection": {
            "hash_salt_hash": acceptance.EXPECTED_SELECTION_SALT_HASH,
            "eligible_case_unit_set_hash": acceptance.EXPECTED_ELIGIBLE_SET_HASH,
            "case_selection_order_hash": acceptance.EXPECTED_SELECTION_ORDER_HASH,
            "smoke_exclusion_hash": acceptance.EXPECTED_SMOKE_EXCLUSION_HASH,
            "excluded_smoke_case_units": list(acceptance.EXPECTED_SMOKE_CASES),
        },
        "domains": [
            {
                "domain": "miniwob",
                "case_unit_count": 22,
                "record_slot_count": 66,
                "official_split_eligible_case_units": 122,
                "official_split_hash": sha256_file(root / "catalog.json"),
                "planned_record_slot_ids_hash": sha256_object(
                    [
                        {"case_unit_id": item["case_unit_id"], "agent_id": agent_id}
                        for item in remaining_items
                        for agent_id in acceptance.EXPECTED_AGENTS
                    ]
                ),
                "case_units": case_refs,
            }
        ],
    }
    _write_json(root / "manifest.json", manifest)
    bundle = {
        "schema_version": "contract_source_bundle.v2",
        "manifest_path": "manifest.json",
        "manifest_definition_sha256": sha256_object({key: value for key, value in manifest.items() if key != "source_bundle_hash"}),
        "manifest_definition_sha256_scope": "canonical_mapping_without_source_bundle_hash",
        "manifest_definition_excluded_fields": ["source_bundle_hash"],
        "source_count": 22,
        "sources": sources,
    }
    _write_json(root / "bundle.json", bundle)
    manifest["source_bundle_hash"] = sha256_file(root / "bundle.json")
    _write_json(root / "manifest.json", manifest)

    kwargs = {
        "first50_selected_path": "first.json",
        "second50_selected_path": "second.json",
        "remaining22_selected_path": "remaining.json",
        "remaining_catalog_path": "catalog.json",
        "manifest_path": "manifest.json",
        "source_bundle_path": "bundle.json",
        "case_packets_root": "packets",
        "execution_infra_path": "infra.json",
        "agents_config_path": "agents.json",
    }
    cli_args = [
        "--first50-selected", "first.json",
        "--second50-selected", "second.json",
        "--remaining22-selected", "remaining.json",
        "--remaining-catalog", "catalog.json",
        "--manifest", "manifest.json",
        "--source-bundle", "bundle.json",
        "--case-packets-root", "packets",
        "--execution-infra", "infra.json",
        "--agents-config", "agents.json",
    ]
    return {"kwargs": kwargs, "cli_args": cli_args, "first_raw_file": first_raw_file}


def _refresh_manifest_bundle_hashes(root: Path) -> None:
    manifest_path = root / "manifest.json"
    bundle_path = root / "bundle.json"
    manifest = _load_json(manifest_path)
    manifest["domains"][0]["official_split_hash"] = sha256_file(root / "catalog.json")
    bundle = _load_json(bundle_path)
    bundle["manifest_definition_sha256"] = sha256_object(
        {key: value for key, value in manifest.items() if key != "source_bundle_hash"}
    )
    _write_json(bundle_path, bundle)
    manifest["source_bundle_hash"] = sha256_file(bundle_path)
    _write_json(manifest_path, manifest)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
