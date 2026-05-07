from __future__ import annotations

import json
from pathlib import Path

import pytest

from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.contracts.draft import build_drafter_prompt, load_source_bundle
from evidence_system.core.hashing import sha256_file


ROOT = Path(__file__).resolve().parents[2]


def test_draft_prompt_uses_case_packet_md_only(tmp_path: Path) -> None:
    source_bundle = _source_bundle(tmp_path)
    payload = load_source_bundle(source_bundle)
    source = payload["sources"][0]

    prompt = build_drafter_prompt(source)

    assert '"case_packet_markdown"' in prompt
    assert '"visible_inputs"' not in prompt
    assert "Use only the case_packet_markdown" in prompt
    assert "Complete the official task." in prompt


def test_draft_prompt_rejects_missing_packet_hash(tmp_path: Path) -> None:
    source_bundle = _source_bundle(tmp_path)
    payload = json.loads(source_bundle.read_text(encoding="utf-8"))
    del payload["sources"][0]["draft_input"]["case_packet_sha256"]
    source_bundle.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(ContractLifecycleError, match="required draft_input field is missing"):
        load_source_bundle(source_bundle)


def _source_bundle(tmp_path: Path) -> Path:
    case_dir = ROOT / "tmp" / f"case-packet-prompt-tests-{tmp_path.name}" / "agentdojo" / "case-001"
    raw_case_dir = case_dir / "raw_case"
    raw_case_dir.mkdir(parents=True, exist_ok=True)
    (raw_case_dir / "task.json").write_text(json.dumps({"prompt": "Complete the official task."}, indent=2) + "\n", encoding="utf-8")
    raw_manifest = {
        "domain": "agentdojo",
        "case_unit_id": "case-001",
        "task_id": "task-001",
        "source_refs": ["official://task-001"],
        "copied_files": ["task.json"],
        "official_files": ["task.json"],
        "derived_files": [],
        "packet_files": ["task.json"],
        "sha256_per_file": {"task.json": sha256_file(raw_case_dir / "task.json")},
        "file_sources": {"task.json": "official://task-001"},
    }
    raw_manifest_path = case_dir / "raw_case_manifest.json"
    raw_manifest_path.write_text(json.dumps(raw_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    case_packet_path = case_dir / "case_packet.md"
    case_packet_path.write_text(
        "# Case Packet\n\n## Case Metadata\n\n- domain: `agentdojo`\n- case_unit_id: `case-001`\n- task_id: `task-001`\n\n## Official Source Files\n\n```json\n{\"prompt\": \"Complete the official task.\"}\n```\n",
        encoding="utf-8",
    )
    payload = {
        "schema_version": "contract_source_bundle.v2",
        "manifest_path": "tests/fixtures/valid_experiment_manifest.json",
        "source_count": 1,
        "sources": [
            {
                "contract_id": "contract-001",
                "domain": "AgentDojo",
                "case_unit_id": "case-001",
                "task_id": "task-001",
                "draft_input": {
                    "case_packet_path": str(case_packet_path.relative_to(ROOT)),
                    "case_packet_sha256": sha256_file(case_packet_path),
                    "raw_case_manifest_path": str(raw_manifest_path.relative_to(ROOT)),
                    "raw_case_manifest_sha256": sha256_file(raw_manifest_path),
                },
            }
        ],
    }
    source_bundle = tmp_path / "source_bundle.json"
    source_bundle.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return source_bundle
