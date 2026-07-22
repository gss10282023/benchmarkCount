from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any

import pytest

from evidence_system.adapters.agentdojo_runtime_control import load_runtime_policy
from evidence_system.contracts import agentdojo_remaining_849_execution as remaining
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.paths import resolve_repo_path


FIXED_CREATED_AT = "2026-07-17T05:00:00+00:00"
FIXED_LOCKED_AT = "2026-07-17T05:01:00+00:00"
BASE_KEY_FINGERPRINT = "1" * 64
EXECUTION_KEY_FINGERPRINT = BASE_KEY_FINGERPRINT


def _write_json(path: Path, value: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _case_ids(counts: dict[str, int]) -> list[str]:
    return [
        f"v1.2.2:{suite}:user_task_{ordinal}:injection_task_0"
        for suite in remaining.SUITE_ORDER
        for ordinal in range(counts[suite])
    ]


def _packet(root: Path, case_id: str) -> None:
    directory = root / case_id.replace(":", "_")
    _write_json(
        directory / "raw_case_manifest.json",
        {
            "case_unit_id": case_id,
            "domain": "agentdojo",
            "task_id": case_id.removeprefix("v1.2.2:"),
        },
    )
    (directory / "case_packet.md").write_text(
        f"# {case_id}\n", encoding="utf-8"
    )


def _job_payload(case_id: str, agent_id: str, *, seed: int) -> dict[str, Any]:
    safe_case = case_id.replace(":", "-")
    safe_agent = agent_id.lower().replace(" ", "_")
    return {
        "schema_version": "job/v1",
        "job_id": f"full-agentdojo-{safe_case}-{safe_agent}",
        "domain": "agentdojo",
        "phase": "full",
        "experiment_type": "appendix",
        "result_namespace": "agentdojo_full_v1.2.2_direct",
        "case_unit_id": case_id,
        "task_id": case_id.removeprefix("v1.2.2:"),
        "agent_id": agent_id,
        "record_slot_id": f"slot-agentdojo-{safe_case}-{safe_agent}",
        "run_id": f"run-agentdojo-{safe_case}-{safe_agent}",
        "attempt_id": f"attempt-agentdojo-{safe_case}-{safe_agent}",
        "seed": seed,
    }


def _base_policy(path: Path) -> tuple[Path, dict[str, Any]]:
    source = resolve_repo_path(remaining.DEFAULT_FINALIZED_POLICY)
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["operational_override"][
        "execution_key_fingerprint_sha256"
    ] = BASE_KEY_FINGERPRINT
    load_runtime_policy(payload)
    return _write_json(path, payload), payload


def _infra(path: Path, *, ordinal: int) -> Path:
    prefix = f"/srv/agentdojo-remaining-vps{ordinal}"
    return _write_json(
        path,
        {
            "schema_version": "infra/v1",
            "machines": [
                {
                    "machine_id": f"remaining-vps-{ordinal}",
                    "enabled": True,
                    "connection": "ssh",
                    "ssh": {
                        "host": f"192.0.2.{ordinal}",
                        "user": "benchmark",
                        "port": 22,
                        "ed25519_fingerprint": f"SHA256:host-{ordinal}",
                    },
                    "concurrency": 8,
                    "benchmarks": {
                        "AgentDojo": {
                            "remote_raw_root": f"{prefix}/raw",
                            "blind_aggregate_root": f"{prefix}/blind",
                            "runtime_state_root": f"{prefix}/runtime",
                            "failed_attempt_archive_root": f"{prefix}/failed",
                            "retrieval_snapshot_root": f"{prefix}/snapshots",
                        }
                    },
                }
            ],
        },
    )


def _fixture(tmp_path: Path) -> dict[str, Any]:
    full_root = tmp_path / "full_packets"
    paper_root = tmp_path / "paper_packets"
    jobs_root = tmp_path / "jobs"
    full_ids = _case_ids(remaining.EXPECTED_FULL_SUITE_COUNTS)
    paper_ids = set()
    for suite in remaining.SUITE_ORDER:
        suite_ids = [
            case_id
            for case_id in full_ids
            if f":{suite}:" in case_id
        ]
        paper_ids.update(
            suite_ids[: remaining.EXPECTED_PAPER_SUITE_COUNTS[suite]]
        )
    for case_id in full_ids:
        _packet(full_root, case_id)
        if case_id in paper_ids:
            _packet(paper_root, case_id)
    for case_ordinal, case_id in enumerate(full_ids):
        for agent_id in remaining.EXPECTED_AGENTS:
            payload = _job_payload(case_id, agent_id, seed=7 + case_ordinal)
            _write_json(jobs_root / f"{payload['job_id']}.json", payload)

    source_files = {
        "full_manifest": _write_json(tmp_path / "full_manifest.json", {"v": 1}),
        "full_catalog": _write_json(tmp_path / "full_catalog.json", {"v": 1}),
        "full_source_bundle": _write_json(
            tmp_path / "full_source_bundle.json", {"v": 1}
        ),
        "agents_config": _write_json(tmp_path / "agents_config.json", {"v": 1}),
    }
    base_path, base_payload = _base_policy(
        tmp_path / remaining.FINALIZED_POLICY_BASENAME
    )
    host_paths = [
        tmp_path / f"host_policy_vps{ordinal}.json" for ordinal in (1, 2)
    ]
    host_policy_publication = remaining.publish_host_conservative_policies(
        base_policy_path=base_path,
        output_paths=host_paths,
        execution_key_fingerprint_sha256=EXECUTION_KEY_FINGERPRINT,
    )
    infra_paths = [
        _infra(tmp_path / f"infra_vps{ordinal}.yaml", ordinal=ordinal)
        for ordinal in (1, 2)
    ]
    return {
        "full_root": full_root,
        "paper_root": paper_root,
        "jobs_root": jobs_root,
        "source_files": source_files,
        "base_policy": base_path,
        "base_payload": base_payload,
        "host_policies": host_paths,
        "host_policy_publication": host_policy_publication,
        "infra": infra_paths,
        "remaining_ids": set(full_ids) - paper_ids,
    }


def test_deterministic_two_vps_shards_alternate_with_exact_quotas() -> None:
    cases = _case_ids(remaining.EXPECTED_REMAINING_SUITE_COUNTS)

    assignment = remaining.deterministic_two_vps_shards(cases)

    assert len(assignment) == 849
    for shard_id, expected in remaining.EXPECTED_SHARD_QUOTAS.items():
        observed = Counter(
            case_id.split(":")[1]
            for case_id, assigned in assignment.items()
            if assigned == shard_id
        )
        assert dict(observed) == expected
    for suite in remaining.SUITE_ORDER:
        ordered = sorted(
            (case_id for case_id in cases if f":{suite}:" in case_id),
            key=remaining._case_sort_key,
        )
        expected_first = (
            "vps2"
            if remaining.EXPECTED_SHARD_QUOTAS["vps2"][suite]
            > remaining.EXPECTED_SHARD_QUOTAS["vps1"][suite]
            else "vps1"
        )
        assert assignment[ordered[0]] == expected_first
        assert all(
            assignment[first] != assignment[second]
            for first, second in zip(ordered, ordered[1:], strict=False)
        )


def test_publish_verify_and_detect_bound_job_drift(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    manifest_path = tmp_path / "campaign_manifest.json"
    lock_path = tmp_path / "execution_lock.json"

    assert fixture["host_policy_publication"]["created"] == [True, True]
    assert fixture["host_policy_publication"]["worker_parser_accepted"] is True
    repeated_publication = remaining.publish_host_conservative_policies(
        base_policy_path=fixture["base_policy"],
        output_paths=fixture["host_policies"],
        execution_key_fingerprint_sha256=EXECUTION_KEY_FINGERPRINT,
    )
    assert repeated_publication["created"] == [False, False]
    for path in fixture["host_policies"]:
        parsed = load_runtime_policy(json.loads(path.read_text(encoding="utf-8")))
        assert parsed.max_concurrent_requests == 8
        assert parsed.requests_per_minute == 48
        assert parsed.tokens_per_minute == 957_376
        assert parsed.budget.maximum_run_cost_usd == 325.0

    result = remaining.publish_remaining_849_execution_lock(
        infra_paths=fixture["infra"],
        host_policy_paths=fixture["host_policies"],
        manifest_path=manifest_path,
        lock_path=lock_path,
        full_case_packets_root=fixture["full_root"],
        paper_case_packets_root=fixture["paper_root"],
        jobs_root=fixture["jobs_root"],
        finalized_policy_path=fixture["base_policy"],
        source_files=fixture["source_files"],
        created_at=FIXED_CREATED_AT,
        locked_at=FIXED_LOCKED_AT,
    )
    verified = remaining.verify_remaining_849_execution_lock(lock_path)

    assert result.created is True
    assert verified.lock_sha256 == result.lock_sha256
    definition = verified.manifest["definition"]
    assert definition["selection"]["remaining_case_count"] == 849
    assert definition["selection"]["remaining_suite_counts"] == {
        "workspace": 506,
        "travel": 127,
        "banking": 126,
        "slack": 90,
    }
    assert definition["job_plan"]["job_count"] == 2_547
    assert definition["sharding"]["case_counts"] == {"vps1": 424, "vps2": 425}
    assert definition["sharding"]["job_counts"] == {
        "vps1": 1_272,
        "vps2": 1_275,
    }
    assert (
        definition["monitoring_policy"]["consecutive_problem_case_threshold"]
        == 4
    )
    assert definition["sealed_evidence_policy"] == remaining._sealed_evidence_policy()
    runtime = definition["runtime"]
    assert runtime["base_policy_is_reference_only"] is True
    assert runtime["host_must_not_load_base_policy_directly"] is True
    assert [row["limits"] for row in runtime["host_conservative_policies"]] == [
        remaining.EXPECTED_HOST_LIMITS,
        remaining.EXPECTED_HOST_LIMITS,
    ]
    assert {
        row["execution_key_fingerprint_sha256"]
        for row in runtime["host_conservative_policies"]
    } == {EXECUTION_KEY_FINGERPRINT}
    assert runtime["two_host_static_partition"]["per_host"] == {
        "max_concurrent_requests": 8,
        "requests_per_minute": 48,
        "tokens_per_minute": 957_376,
        "per_model_concurrent_requests_by_agent_lane": {
            "Agent A": 8,
            "Agent B": 4,
            "Agent C": 4,
        },
        "maximum_run_cost_usd": 325.0,
    }

    case_shards: dict[str, set[str]] = defaultdict(set)
    case_agents: dict[str, set[str]] = defaultdict(set)
    for entry in definition["job_plan"]["entries"]:
        case_shards[entry["case_unit_id"]].add(entry["shard_id"])
        case_agents[entry["case_unit_id"]].add(entry["agent_id"])
        assert entry["job_file_sha256"] == entry["job_file_canonical_sha256"]
        assert entry["job_binding_sha256"] == entry["job_payload_sha256"]
    assert len(case_shards) == 849
    assert all(len(shards) == 1 for shards in case_shards.values())
    assert all(agents == set(remaining.EXPECTED_AGENTS) for agents in case_agents.values())

    base_binding = remaining._finalized_policy_binding(fixture["base_policy"])
    with pytest.raises(ContractLifecycleError, match="must not load the complete base"):
        remaining._two_host_policy_bindings(
            [fixture["base_policy"], fixture["host_policies"][1]],
            base_policy_binding=base_binding,
        )

    selected_case = sorted(fixture["remaining_ids"], key=remaining._case_sort_key)[0]
    selected_job = next(
        fixture["jobs_root"].glob(
            f"full-agentdojo-{selected_case.replace(':', '-')}-agent_a.json"
        )
    )
    payload = json.loads(selected_job.read_text(encoding="utf-8"))
    payload["seed"] += 1
    _write_json(selected_job, payload)
    with pytest.raises(ContractLifecycleError, match="bound source job payload/file hash"):
        remaining.verify_remaining_849_execution_lock(lock_path)
