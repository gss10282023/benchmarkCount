from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from evidence_system.contracts.draft import draft_contracts
from evidence_system.contracts.lock import lock_contracts
from evidence_system.contracts.manifest_update import update_manifest_contract_locks
from evidence_system.contracts.review import review_contracts
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.core.schemas import validate_cross_object_consistency


ROOT = Path(__file__).resolve().parents[2]
DOMAINS = ("agentdojo", "appworld", "webarena_verified", "tau3_retail")
CASE_UNITS_PER_DOMAIN = 3
DISPLAY = {
    "agentdojo": "AgentDojo",
    "appworld": "AppWorld",
    "webarena_verified": "WebArena-Verified",
    "tau3_retail": "tau3-bench retail",
}


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src if not env.get("PYTHONPATH") else f"{src}{os.pathsep}{env['PYTHONPATH']}"
    return env


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_freeze(tmp_path: Path, manifest_path: Path, source_bundle: Path, *, extra: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    args = [
        sys.executable,
        "-m",
        "evidence_system.cli.freeze_predictions",
        "--check-only",
        "--manifest",
        str(manifest_path),
        "--contracts",
        str(tmp_path / "locked"),
        "--review-record",
        str(tmp_path / "locked_reviews"),
        "--llm-call",
        str(tmp_path / "llm_calls"),
        "--source-bundle",
        str(source_bundle),
        "--paper-mapping",
        str(tmp_path / "paper_mapping.json"),
        "--prediction-registry",
        str(tmp_path / "prediction_registry.json"),
        "--official-splits",
        str(tmp_path / "official_splits"),
        "--bootstrap-plan",
        str(tmp_path / "bootstrap_plan.json"),
        "--audit-sampling-plan",
        str(tmp_path / "audit_sampling_plan.json"),
        "--rerun-subset",
        str(tmp_path / "rerun_subset.json"),
        "--scorer-version",
        "scorer-smoke-step5",
        "--json",
    ]
    if extra:
        args.extend(extra)
    return subprocess.run(args, cwd=ROOT, env=_subprocess_env(), check=False, text=True, capture_output=True)


def test_step5_check_only_accepts_nonformal_3_per_domain_vertical_slice(tmp_path: Path) -> None:
    manifest_path, source_bundle = _build_locked_smoke_slice(tmp_path)

    result = _run_freeze(tmp_path, manifest_path, source_bundle)

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    manifest = _load(manifest_path)
    assert payload["status"] == "ok"
    assert payload["check_only"] is True
    assert payload["formal"] is False
    assert payload["freeze_manifest"]["locked_contracts_hash"] == manifest["contract_locks_hash"]
    assert payload["freeze_manifest"]["manifest_hash"] == sha256_file(manifest_path)
    assert not (ROOT / "results/manifests/pre_scoring_freeze.json").exists()


def test_step5_check_only_fails_missing_case_lock_metadata_and_llm_provenance(tmp_path: Path) -> None:
    manifest_path, source_bundle = _build_locked_smoke_slice(tmp_path)
    manifest = _load(manifest_path)
    del manifest["domains"][0]["case_units"][0]["contract_lock_time"]
    _write_json(manifest_path, manifest)

    missing_lock_time = _run_freeze(tmp_path, manifest_path, source_bundle)

    assert missing_lock_time.returncode == 1
    assert "P0 manifest case unit lacks complete locked contract metadata before freeze" in missing_lock_time.stdout

    manifest_path, source_bundle = _build_locked_smoke_slice(tmp_path / "missing-provenance")
    manifest = _load(manifest_path)
    del manifest["contract_locks"][0]["contract_drafting_llm_call_id"]
    _write_json(manifest_path, manifest)

    missing_provenance = _run_freeze(tmp_path / "missing-provenance", manifest_path, source_bundle)

    assert missing_provenance.returncode == 1
    assert "manifest contract lock entries must be locked" not in missing_provenance.stdout
    assert "contract_drafting_llm_call_id" in missing_provenance.stdout


def test_step5_formal_p0_still_requires_100_per_domain(tmp_path: Path) -> None:
    manifest_path, source_bundle = _build_locked_smoke_slice(tmp_path)

    result = _run_freeze(tmp_path, manifest_path, source_bundle, extra=["--formal"])

    assert result.returncode == 1
    assert "P0 main case_unit_count must match planned eligible case units" in result.stdout
    assert "formal P0 main manifest must plan 1200 record slots" in result.stdout


def test_step5_declared_appendix_requires_locked_contract_or_spec(tmp_path: Path) -> None:
    manifest_path, source_bundle = _build_locked_smoke_slice(tmp_path)
    manifest = _load(manifest_path)
    manifest["declared_appendix_diagnostics"] = [
        {
            "declared": True,
            "domain": "androidworld",
            "experiment_type": "appendix",
            "paper_label": "app:androidworld",
            "priority": "P2",
        }
    ]
    _write_json(manifest_path, manifest)

    result = _run_freeze(tmp_path, manifest_path, source_bundle)

    assert result.returncode == 1
    assert "declared appendix/diagnostic evidence scoring requires explicit locked contract" in result.stdout


def test_step5_prediction_registry_placeholders_block_freeze(tmp_path: Path) -> None:
    manifest_path, source_bundle = _build_locked_smoke_slice(tmp_path)
    registry = _load(tmp_path / "prediction_registry.json")
    registry["predictions"]["P1"]["registered_text"] = "需要从 locked manifest 确认"
    _write_json(tmp_path / "prediction_registry.json", registry)

    result = _run_freeze(tmp_path, manifest_path, source_bundle)

    assert result.returncode == 1
    assert "prediction_registry.predictions.P1.registered_text" in result.stdout
    assert "unresolved placeholder" in result.stdout


def test_step5_non_check_only_refuses_to_create_formal_freeze(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "evidence_system.cli.freeze_predictions", "--json"],
        cwd=ROOT,
        env=_subprocess_env(),
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 2
    assert "supports --check-only only" in result.stderr


def test_step5_formal_scoring_requires_freeze_and_rejects_late_freeze(tmp_path: Path) -> None:
    missing_freeze = subprocess.run(
        [
            sys.executable,
            "-m",
            "evidence_system.cli.validate_results",
            "--formal",
            "--manifest",
            str(ROOT / "tests/fixtures/valid_experiment_manifest.json"),
            "--paper-mapping",
            str(ROOT / "tests/fixtures/valid_paper_mapping.json"),
            "--evidence-contract",
            str(ROOT / "tests/fixtures/valid_evidence_contract.json"),
            "--scored-record",
            str(ROOT / "tests/fixtures/valid_scored_record.json"),
            "--json",
        ],
        cwd=ROOT,
        env=_subprocess_env(),
        check=False,
        text=True,
        capture_output=True,
    )
    assert missing_freeze.returncode == 1
    assert "formal validation requires --freeze-manifest" in missing_freeze.stdout

    manifest = _load(ROOT / "tests/fixtures/valid_experiment_manifest.json")
    freeze = _load(ROOT / "tests/fixtures/valid_freeze_manifest.json")
    scored = _load(ROOT / "tests/fixtures/valid_scored_record.json")
    freeze["frozen_at"] = "2026-05-04T00:01:00+00:00"
    scored["started_at"] = "2026-05-04T00:00:00+00:00"
    report = validate_cross_object_consistency(
        [("manifest", manifest), ("freeze", freeze), ("scored", scored)],
        raise_on_error=False,
    )
    assert not report.ok
    assert "freeze time must be at or before scoring start" in json.dumps(report.to_dict())


def _build_locked_smoke_slice(tmp_path: Path) -> tuple[Path, Path]:
    paper_mapping = _write_json(tmp_path / "paper_mapping.json", {"labels": []})
    _write_json(tmp_path / "bootstrap_plan.json", {"seed": 123, "resample_count": 1000})
    _write_json(tmp_path / "audit_sampling_plan.json", {"seed": 456, "sample": "stratified"})
    _write_json(tmp_path / "rerun_subset.json", {"selection_rule": "predeclared hash order"})
    _write_json(
        tmp_path / "prediction_registry.json",
        {
            "predictions": {
                prediction: {"prediction_id": prediction, "registered_text": f"Locked {prediction}"}
                for prediction in ("P1", "P2", "P3", "P4")
            }
        },
    )
    _write_json(tmp_path / "official_splits" / "splits.json", {"domains": list(DOMAINS)})
    manifest_path = _write_json(tmp_path / "manifest.json", _manifest_payload(paper_mapping))
    source_bundle = _write_json(tmp_path / "source_bundle.json", _source_bundle_payload(tmp_path, manifest_path))
    manifest = _load(manifest_path)
    manifest["source_bundle_hash"] = sha256_file(source_bundle)
    _write_json(manifest_path, manifest)

    drafts = draft_contracts(
        source_bundle_path=source_bundle,
        output_dir=tmp_path / "drafts",
        llm_log_dir=tmp_path / "llm_calls",
        allow_test_mock=True,
        request_timestamp="2026-05-04T00:00:00+00:00",
        response_timestamp="2026-05-04T00:00:01+00:00",
    )
    reviews = review_contracts(
        drafts=[draft.draft_path for draft in drafts],
        reviewed_dir=tmp_path / "reviewed",
        review_log_dir=tmp_path / "review_logs",
        human_time_dir=tmp_path / "human_time",
        reviewer_id="reviewer-001",
        review_started_at="2026-05-04T00:01:00+00:00",
        review_finished_at="2026-05-04T00:05:00+00:00",
        review_actions=["checked source hierarchy"],
        source_bundle_hash=_load(Path(drafts[0].llm_call_path))["source_bundle_hash"],
        unsupported_requirements_removed=True,
    )
    locks = lock_contracts(
        reviewed=[review.reviewed_contract_path for review in reviews],
        review_logs=[review.review_workflow_path for review in reviews],
        locked_dir=tmp_path / "locked",
        contract_review_dir=tmp_path / "locked_reviews",
        manifest_id=_load(manifest_path)["manifest_id"],
        manifest_hash=sha256_file(manifest_path),
        locked_at="2026-05-04T00:06:00+00:00",
        locked_by="reviewer-001",
        first_scoring_started_at="2026-05-04T00:20:00+00:00",
        allow_test_mock=True,
    )
    update_manifest_contract_locks(
        manifest_path=manifest_path,
        locked_contracts=[lock.locked_contract_path for lock in locks],
        output_path=manifest_path,
    )
    return manifest_path, source_bundle


def _manifest_payload(paper_mapping: Path) -> dict[str, Any]:
    return {
        "schema_version": "experiment_manifest/v1",
        "manifest_id": "smoke-step5-3-per-domain",
        "manifest_version": "1.0.0-smoke",
        "created_at": "2026-05-04T00:00:00+00:00",
        "status": "draft",
        "paper_mapping_path": str(paper_mapping),
        "paper_mapping_sha256": sha256_file(paper_mapping),
        "source_bundle_hash": "0" * 64,
        "agents_config_hash": sha256_file(ROOT / "configs/agents.yaml"),
        "infra_config_hash": sha256_file(ROOT / "configs/infra.yaml"),
        "deterministic_selection": {
            "hash_function": "sha256",
            "hash_salt_hash": "1" * 64,
            "eligible_case_unit_set_hash": "2" * 64,
            "excluded_smoke_case_units": [],
            "smoke_exclusion_hash": sha256_object([]),
            "case_selection_order_hash": "3" * 64,
            "bootstrap_seed": 123,
            "bootstrap_resample_count": 1000,
            "audit_sample_seed": 456,
            "rerun_subset_selection_rule": "predeclared hash order",
        },
        "domains": [
            {
                "domain": domain,
                "domain_display_name": DISPLAY[domain],
                "experiment_type": "main",
                "priority": "P0",
                "case_unit_count": CASE_UNITS_PER_DOMAIN,
                "record_slot_count": CASE_UNITS_PER_DOMAIN * 4,
                "planned_record_slot_ids_hash": sha256_object([domain, "slots"]),
                "official_split_eligible_case_units": 100,
                "official_split_hash": sha256_object([domain, "official-split"]),
                "official_split_exception_id": None,
                "contract_lock_status": "locked_required_before_scoring",
                "claim_scope": "native_aligned",
                "stronger_measurement_mapping": None,
                "case_units": [
                    {"case_unit_id": f"{domain}-case-{index:03d}", "task_id": f"{domain}-task-{index:03d}"}
                    for index in range(1, CASE_UNITS_PER_DOMAIN + 1)
                ],
            }
            for domain in DOMAINS
        ],
        "agents": [
            {
                "agent_id": agent,
                "config_hash": sha256_file(ROOT / "configs/agents.yaml"),
                "agent_probe_rationale": {
                    "non_redundant_measurement_probe": True,
                    "spans_source_openness": "locked-smoke",
                    "spans_scale": "locked-smoke",
                    "spans_tool_use_style": "locked-smoke",
                    "leaderboard_interpretation": False,
                },
            }
            for agent in ("Agent A", "Agent B", "Agent C")
        ],
        "official_split_exceptions": [],
        "declared_appendix_diagnostics": [],
        "required_paper_labels": [],
        "contract_locks": [],
    }


def _source_bundle_payload(tmp_path: Path, manifest_path: Path) -> dict[str, Any]:
    sources = []
    for domain in DOMAINS:
        for index in range(1, CASE_UNITS_PER_DOMAIN + 1):
            case_dir = ROOT / "tmp" / f"freeze-case-packet-tests-{tmp_path.name}" / domain / f"{domain}-case-{index:03d}"
            raw_case_dir = case_dir / "raw_case"
            raw_case_dir.mkdir(parents=True, exist_ok=True)
            (raw_case_dir / "task.json").write_text(
                json.dumps({"prompt": f"Complete {domain} official task {index}."}, indent=2) + "\n",
                encoding="utf-8",
            )
            raw_manifest_path = case_dir / "raw_case_manifest.json"
            raw_manifest_path.write_text(
                json.dumps(
                    {
                        "domain": domain,
                        "case_unit_id": f"{domain}-case-{index:03d}",
                        "task_id": f"{domain}-task-{index:03d}",
                        "source_refs": [f"official://{domain}/{index}"],
                        "copied_files": ["task.json"],
                        "official_files": ["task.json"],
                        "derived_files": [],
                        "packet_files": ["task.json"],
                        "sha256_per_file": {"task.json": sha256_file(raw_case_dir / "task.json")},
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            case_packet_path = case_dir / "case_packet.md"
            case_packet_path.write_text(
                f"# Case Packet\n\n## Case Metadata\n\n- domain: `{domain}`\n- case_unit_id: `{domain}-case-{index:03d}`\n- task_id: `{domain}-task-{index:03d}`\n\n## Official Source Files\n\n```json\n{{\"prompt\": \"Complete {domain} official task {index}.\"}}\n```\n",
                encoding="utf-8",
            )
            sources.append(
                {
                    "contract_id": f"contract-{domain}-{index:03d}",
                    "domain": domain,
                    "case_unit_id": f"{domain}-case-{index:03d}",
                    "task_id": f"{domain}-task-{index:03d}",
                    "draft_input": {
                        "case_packet_path": str(case_packet_path.relative_to(ROOT)),
                        "case_packet_sha256": sha256_file(case_packet_path),
                        "raw_case_manifest_path": str(raw_manifest_path.relative_to(ROOT)),
                        "raw_case_manifest_sha256": sha256_file(raw_manifest_path),
                    },
                    "source_context": {
                        "task_text": {"prompt": f"Complete {domain} official task {index}."},
                        "official_policy": "Official task policy.",
                        "evaluator_description": {"semantics": "Official evaluator semantics."},
                        "schema": {"state": "object"},
                        "trace_schema": {"events": ["tool_call", "message"]},
                        "available_post_run_artifact_types": ["native evaluator output"],
                        "contract_template": {"claim_scope": "native_aligned"},
                        "native_sources": [{"source_ref": f"official://{domain}/{index}", "source_sha256": "a" * 64}],
                    },
                }
            )
    return {
        "schema_version": "contract_source_bundle.v2",
        "manifest_path": str(manifest_path),
        "source_count": len(sources),
        "sources": sources,
    }
