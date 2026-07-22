from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from evidence_system.contracts.common import stamp_contract_hash
from evidence_system.core.hashing import sha256_file, sha256_object
from evidence_system.orchestrator import webarena_verified_full as scheduler
from evidence_system.orchestrator.webarena_verified_run_control import (
    load_materialized_full_plan,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "experiments/step19/webarena_verified_full_812_manifest.json"
SOURCE_BUNDLE = (
    ROOT
    / "experiments/evidence_contracts/source_bundles"
    / "webarena_verified_full_812_source_bundle.json"
)
TASK_CONTRACT_INDEX = (
    ROOT / "experiments/case_packets/webarena_verified/task_contract_index.json"
)
AGENTS_CONFIG = ROOT / "configs/agents.yaml"
BASE_CONTRACT = ROOT / "tests/fixtures/valid_evidence_contract.json"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_sidecar(path: Path) -> None:
    path.with_name(path.name + ".sha256").write_text(
        f"{sha256_file(path)}  {path.name}\n",
        encoding="utf-8",
    )


def _formal_counts() -> dict[str, int]:
    return {field: scheduler.EXPECTED_CASE_COUNT for field in scheduler._LOCKED_COUNT_FIELDS}


def _build_formal_claim_tree(root: Path) -> dict[str, Path]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    base = json.loads(BASE_CONTRACT.read_text(encoding="utf-8"))
    manifest_hash = sha256_file(MANIFEST)
    cases: list[dict[str, object]] = []

    for case in manifest["cases"]:
        task_id = int(case["task_id"])
        upstream_root = root / "upstream" / str(task_id)
        upstream_specs = {
            "ir": (upstream_root / "native_ir.json", {"task_id": task_id, "kind": "native_ir"}),
            "draft_contract": (
                upstream_root / "draft_contract.json",
                {"task_id": task_id, "kind": "draft_contract"},
            ),
            "draft_checklist": (
                upstream_root / "draft_checklist.md",
                f"# Task {task_id} draft checklist\n",
            ),
            "machine_review": (
                upstream_root / "machine_review.json",
                {"task_id": task_id, "status": "pass"},
            ),
            "contract_review": (
                upstream_root / "contract_review.json",
                {"task_id": task_id, "status": "approved"},
            ),
        }
        upstream_paths: dict[str, Path] = {}
        for name, (path, payload) in upstream_specs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(payload, str):
                path.write_text(payload, encoding="utf-8")
            else:
                _write_json(path, payload)
            upstream_paths[name] = path

        contract_path = root / "locked/contracts" / str(task_id) / "evidence_contract.json"
        contract = copy.deepcopy(base)
        contract_id = f"ec_webarena_verified_{task_id}_contract_v1_0_0"
        contract.update(
            {
                "canonical_hash_source": str(contract_path),
                "case_unit_id": str(task_id),
                "claim_text": f"Native-aligned WebArena-Verified claim for task {task_id}",
                "contract_draft_id": f"wv-draft-{task_id}",
                "contract_drafting_llm_call_id": f"wv-draft-call-{task_id}",
                "contract_id": contract_id,
                "domain": "webarena_verified",
                "locked_by": "formal-reviewer",
                "manifest_contract_lock_ref": f"{manifest_hash}:{contract_id}:1.0.0",
                "manifest_hash": manifest_hash,
                "native_sources": ["WebArena-Verified v1.2.3 official evaluator semantics"],
                "review_record_id": f"wv-review-{task_id}",
                "source_support": {
                    "evaluator": "WebArena-Verified v1.2.3 official evaluator",
                    "schema": "evidence_contract/v1",
                    "task_or_policy": f"official task {task_id} revision {case['revision']}",
                },
                "task_id": str(task_id),
            }
        )
        contract["required_artifacts"][0].update(
            {
                "artifact_id": f"wv-native-output-{task_id}",
                "contract_requirement_id": f"wv-req-native-output-{task_id}",
            }
        )
        stamp_contract_hash(contract)
        _write_json(contract_path, contract)

        checklist_path = root / "locked/checklists" / str(task_id) / "checklist.md"
        checklist_path.parent.mkdir(parents=True, exist_ok=True)
        checklist_path.write_text(
            f"# Locked checklist for WebArena-Verified task {task_id}\n",
            encoding="utf-8",
        )
        cases.append(
            {
                "domain": "webarena_verified",
                "case_unit_id": str(task_id),
                "task_id": task_id,
                "task_revision": int(case["revision"]),
                "manifest_source_task_sha256": case["source_task_sha256"],
                "packet_source_task_sha256": hashlib.sha256(
                    json.dumps(
                        json.loads(
                            (
                                ROOT
                                / f"experiments/case_packets/webarena_verified/{task_id}/"
                                "raw_case/derived/task.json"
                            ).read_text(encoding="utf-8")
                        ),
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    ).encode("utf-8")
                ).hexdigest(),
                "evaluator_config_sha256": sha256_object(
                    {"task_id": task_id, "evaluator": "official-v1.2.3"}
                ),
                "native_ir_path": str(upstream_paths["ir"]),
                "native_ir_sha256": sha256_file(upstream_paths["ir"]),
                "draft_contract_path": str(upstream_paths["draft_contract"]),
                "draft_contract_sha256": sha256_file(upstream_paths["draft_contract"]),
                "draft_checklist_path": str(upstream_paths["draft_checklist"]),
                "draft_checklist_sha256": sha256_file(upstream_paths["draft_checklist"]),
                "machine_review_path": str(upstream_paths["machine_review"]),
                "machine_review_sha256": sha256_file(upstream_paths["machine_review"]),
                "contract_review_path": str(upstream_paths["contract_review"]),
                "contract_review_sha256": sha256_file(upstream_paths["contract_review"]),
                "human_signoff_status": "approved",
                "locked_contract_path": str(contract_path),
                "locked_contract_sha256": sha256_file(contract_path),
                "locked_checklist_path": str(checklist_path),
                "locked_checklist_sha256": sha256_file(checklist_path),
            }
        )

    index_path = root / "index.json"
    index = {
        "schema_version": scheduler.NATIVE_CLAIM_INDEX_SCHEMA_VERSION,
        "domain": "webarena_verified",
        "benchmark_version": "v1.2.3",
        "expected_count": scheduler.EXPECTED_CASE_COUNT,
        "path_scope": "repository_relative",
        "input_lock_sha256": sha256_object(
            {"manifest": manifest_hash, "case_count": scheduler.EXPECTED_CASE_COUNT}
        ),
        "compiler": {
            "id": "neurips_ed_track_minimal",
            "version": "test-locked-v1",
            "source_path": "neurips_ed_track_minimal",
            "source_sha256": sha256_object("test compiler source"),
        },
        "counts": _formal_counts(),
        "cases": cases,
    }
    _write_json(index_path, index)
    _write_sidecar(index_path)

    acceptance_path = root / "acceptance.json"
    acceptance = {
        "schema_version": scheduler.NATIVE_CLAIM_ACCEPTANCE_SCHEMA_VERSION,
        "status": "accepted",
        "formal_launch_eligible": True,
        "expected_count": scheduler.EXPECTED_CASE_COUNT,
        "input_lock_sha256": index["input_lock_sha256"],
        "index_path": str(index_path),
        "index_sha256": sha256_file(index_path),
        "counts": _formal_counts(),
        "gates": {field: True for field in scheduler._FORMAL_GATE_FIELDS},
        "human_signoff": {
            "required_count": scheduler.EXPECTED_CASE_COUNT,
            "signed_count": scheduler.EXPECTED_CASE_COUNT,
            "status": "complete",
        },
        "machine_contract_gate": {
            "machine_locked": True,
            "machine_locked_count": scheduler.EXPECTED_CASE_COUNT,
            "native_contract_count": scheduler.EXPECTED_CASE_COUNT,
            "fallback_contract_count": 0,
            "formal_human_locked": True,
            "authorizes_formal_launch": True,
        },
        "blockers": [],
    }
    _write_json(acceptance_path, acceptance)
    _write_sidecar(acceptance_path)
    return {
        "root": root,
        "index": index_path,
        "acceptance": acceptance_path,
        "contracts": root / "locked/contracts",
    }


@pytest.fixture(scope="module")
def formal_claim_tree(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    return _build_formal_claim_tree(tmp_path_factory.mktemp("wv-formal-claims"))


def _plan(tree: dict[str, Path]) -> scheduler.FullSchedulePlan:
    return scheduler.plan_full_schedule(
        manifest_path=MANIFEST,
        source_bundle_path=SOURCE_BUNDLE,
        task_contract_index_path=TASK_CONTRACT_INDEX,
        agents_config_path=AGENTS_CONFIG,
        native_claim_index_path=tree["index"],
        native_claim_acceptance_path=tree["acceptance"],
        locked_contracts_root=tree["contracts"],
    )


def _clone_tree(source: dict[str, Path], destination: Path) -> dict[str, Path]:
    shutil.copytree(source["root"], destination)
    index_path = destination / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    old_prefix = str(source["root"])
    new_prefix = str(destination)
    for case in index["cases"]:
        for field in (
            "native_ir_path",
            "draft_contract_path",
            "draft_checklist_path",
            "machine_review_path",
            "contract_review_path",
            "locked_contract_path",
            "locked_checklist_path",
        ):
            case[field] = str(case[field]).replace(old_prefix, new_prefix, 1)
    _write_json(index_path, index)
    _write_sidecar(index_path)
    acceptance_path = destination / "acceptance.json"
    acceptance = json.loads(acceptance_path.read_text(encoding="utf-8"))
    acceptance["index_path"] = str(index_path)
    acceptance["index_sha256"] = sha256_file(index_path)
    _write_json(acceptance_path, acceptance)
    _write_sidecar(acceptance_path)
    return {
        "root": destination,
        "index": index_path,
        "acceptance": acceptance_path,
        "contracts": destination / "locked/contracts",
    }


def _reseal_contract_mutation(tree: dict[str, Path], task_id: int) -> None:
    contract_path = tree["contracts"] / str(task_id) / "evidence_contract.json"
    index = json.loads(tree["index"].read_text(encoding="utf-8"))
    index["cases"][task_id]["locked_contract_sha256"] = sha256_file(contract_path)
    _write_json(tree["index"], index)
    _write_sidecar(tree["index"])
    acceptance = json.loads(tree["acceptance"].read_text(encoding="utf-8"))
    acceptance["index_sha256"] = sha256_file(tree["index"])
    _write_json(tree["acceptance"], acceptance)
    _write_sidecar(tree["acceptance"])


def test_full_scheduler_plans_exact_frozen_product(
    formal_claim_tree: dict[str, Path],
) -> None:
    plan = _plan(formal_claim_tree)

    assert len(plan.jobs) == 2436
    assert plan.acceptance["status"] == "pass"
    assert plan.acceptance["formal_launch_eligible"] is True
    assert plan.acceptance["counts"]["planned_per_agent"] == {
        "Agent A": 812,
        "Agent B": 812,
        "Agent C": 812,
    }
    assert plan.acceptance["counts"]["fallback_contracts"] == 0
    assert plan.jobs[0]["record_slot_id"] == "wv123-task-000-agent-a"
    assert plan.jobs[-1]["record_slot_id"] == "wv123-task-811-agent-c"
    assert [job["seed"] for job in plan.jobs[:3]] == [123000, 123000, 123000]
    assert [job["execution_target"] for job in plan.jobs[:3]] == [
        scheduler.EXPECTED_ROUTES[agent] for agent in scheduler.EXPECTED_AGENT_IDS
    ]
    assert {
        job["execution_target"]["controller_ssh_public_key_fingerprint"]
        for job in plan.jobs
    } == {scheduler.EXPECTED_CONTROLLER_SSH_PUBLIC_KEY_FINGERPRINT}
    assert plan.acceptance["transport_identity"] == {
        "boundary": "execution_transport_independent_of_case_source_chain",
        "controller_key_algorithm": "ssh-ed25519",
        "controller_ssh_public_key_fingerprint": (
            scheduler.EXPECTED_CONTROLLER_SSH_PUBLIC_KEY_FINGERPRINT
        ),
        "route_count": 3,
        "planned_job_count": 2436,
        "all_routes_explicitly_bound": True,
        "all_jobs_explicitly_bound": True,
        "step19_source_manifest_unchanged": True,
    }
    assert all(job["reset_policy"] == "recreate_task_sites_from_digest_v1" for job in plan.jobs)
    assert all(job["reset_receipt_relative_path"] == "reset_receipt.json" for job in plan.jobs)
    assert all(job["task_sites"] for job in plan.jobs)


def test_full_scheduler_rejects_missing_contract(
    formal_claim_tree: dict[str, Path], tmp_path: Path
) -> None:
    tree = _clone_tree(formal_claim_tree, tmp_path / "claims")
    (tree["contracts"] / "0/evidence_contract.json").unlink()

    with pytest.raises(scheduler.WebArenaFullScheduleError):
        _plan(tree)


def test_full_scheduler_rejects_extra_contract_json(
    formal_claim_tree: dict[str, Path], tmp_path: Path
) -> None:
    tree = _clone_tree(formal_claim_tree, tmp_path / "claims")
    _write_json(tree["contracts"] / "extra.json", {"not": "a locked contract"})

    with pytest.raises(scheduler.WebArenaFullScheduleError, match="exactly 812 canonical"):
        _plan(tree)


@pytest.mark.parametrize("mutation", ["unlocked", "empty_artifacts"])
def test_full_scheduler_rejects_invalid_locked_contract(
    formal_claim_tree: dict[str, Path],
    tmp_path: Path,
    mutation: str,
) -> None:
    tree = _clone_tree(formal_claim_tree, tmp_path / "claims")
    path = tree["contracts"] / "0/evidence_contract.json"
    contract = json.loads(path.read_text(encoding="utf-8"))
    if mutation == "unlocked":
        contract["contract_status"] = "draft"
        contract["main_result_eligible"] = False
        contract["locked_at"] = None
        contract["locked_by"] = None
    else:
        contract["required_artifacts"] = []
    stamp_contract_hash(contract)
    _write_json(path, contract)
    _reseal_contract_mutation(tree, 0)

    with pytest.raises(scheduler.WebArenaFullScheduleError):
        _plan(tree)


def test_full_scheduler_rejects_pending_formal_gate(
    formal_claim_tree: dict[str, Path], tmp_path: Path
) -> None:
    tree = _clone_tree(formal_claim_tree, tmp_path / "claims")
    acceptance = json.loads(tree["acceptance"].read_text(encoding="utf-8"))
    acceptance["status"] = "pending"
    acceptance["formal_launch_eligible"] = False
    acceptance["gates"]["human_signoff_complete"] = False
    acceptance["human_signoff"].update({"signed_count": 0, "status": "pending"})
    acceptance["machine_contract_gate"].update(
        {"formal_human_locked": False, "authorizes_formal_launch": False}
    )
    acceptance["blockers"] = ["human signoff pending"]
    _write_json(tree["acceptance"], acceptance)
    _write_sidecar(tree["acceptance"])

    with pytest.raises(
        scheduler.WebArenaFullScheduleError,
        match="native claim acceptance status mismatch",
    ):
        _plan(tree)


def test_full_scheduler_rejects_route_and_paired_seed_mutations(
    formal_claim_tree: dict[str, Path],
) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["servers"][1]["host"] = "192.0.2.99"
    with pytest.raises(scheduler.WebArenaFullScheduleError, match="route for Agent B"):
        scheduler._validate_routes(manifest)

    plan = _plan(formal_claim_tree)
    jobs = [dict(job) for job in plan.jobs]
    jobs[1]["seed"] = 999999
    slots = json.loads(MANIFEST.read_text(encoding="utf-8"))["record_slots"]
    with pytest.raises(scheduler.WebArenaFullScheduleError, match="paired seed"):
        scheduler._validate_planned_jobs(jobs, slots=slots)

    jobs = [copy.deepcopy(job) for job in plan.jobs]
    jobs[0]["execution_target"].pop("controller_ssh_public_key_fingerprint")
    with pytest.raises(scheduler.WebArenaFullScheduleError, match="route"):
        scheduler._validate_planned_jobs(jobs, slots=slots)


def test_blocked_receipt_never_claims_jobs_or_fallbacks(tmp_path: Path) -> None:
    receipt = scheduler.blocked_dry_run_acceptance(
        "locked contract set is incomplete",
        native_claim_index_path=tmp_path / "missing-index.json",
        native_claim_acceptance_path=tmp_path / "missing-acceptance.json",
        locked_contracts_root=tmp_path / "missing-contracts",
    )

    assert receipt["status"] == "blocked"
    assert receipt["formal_launch_eligible"] is False
    assert receipt["counts"]["planned_record_slots"] == 0
    assert receipt["counts"]["fallback_contracts"] == 0


def test_production_operator_waiver_plan_binds_all_formal_jobs() -> None:
    plan = load_materialized_full_plan()

    assert len(plan.jobs) == 2436
    assert plan.acceptance["plan_source"] == (
        "hash_checked_materialized_full_jobs_index"
    )
    assert plan.acceptance["legacy_native_claim_compiler_runtime_dependency"] is False
    assert plan.acceptance["formal_score_draft_provider"] == (
        "neurips_ed_track_minimal"
    )
    assert plan.acceptance["launch_authorization"]["basis"] == (
        "operator_machine_only_waiver"
    )
    assert plan.acceptance["launch_authorization"]["human_signed_count"] == 0
    assert plan.acceptance["formal_launch_eligible"] is True
    waiver_hashes = {
        job["formal_policy_lock"]["operator_waiver_sha256"] for job in plan.jobs
    }
    assert waiver_hashes == {
        "02d389bf8da5895c1281a5f3f97468ae1c195220052cfa1840214f1003c53641"
    }
    assert all(
        job["result_namespace"] == scheduler.RESULT_NAMESPACE
        and job["formal_policy_lock"]["human_signoff_claimed"] is False
        and job["formal_policy_lock"]["human_signed_count"] == 0
        and job["formal_policy_lock"]["model"] == job["requested_model"]
        and job["formal_policy_lock"]["server_id"]
        == job["execution_target"]["server_id"]
        and job["formal_policy_lock"]["reset_policy"] == job["reset_policy"]
        for job in plan.jobs
    )

    tampered = [dict(job) for job in plan.jobs]
    tampered[0] = copy.deepcopy(tampered[0])
    tampered[0]["formal_policy_lock"]["human_signed_count"] = 1
    slots = json.loads(MANIFEST.read_text(encoding="utf-8"))["record_slots"]
    with pytest.raises(scheduler.WebArenaFullScheduleError, match="human_signed_count"):
        scheduler._validate_planned_jobs(tampered, slots=slots)
