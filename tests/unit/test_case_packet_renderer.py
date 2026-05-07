from __future__ import annotations

from pathlib import Path

from evidence_system.contracts.case_packets import build_case_packets
from evidence_system.core.hashing import sha256_file


ROOT = Path(__file__).resolve().parents[2]


def test_case_packet_renderer_is_deterministic(tmp_path: Path) -> None:
    case_unit_id = "v1.2.2:slack:user_task_19:injection_task_2"
    first = build_case_packets(
        manifest_path=ROOT / "experiments/experiment_manifest.yaml",
        official_splits_path=ROOT / "experiments/official_splits",
        output_root=tmp_path / "case_packets",
        case_unit_ids=[case_unit_id],
    )[0]
    first_path = Path(first.case_packet_path)
    first_text = first_path.read_text(encoding="utf-8")
    first_hash = sha256_file(first_path)

    second = build_case_packets(
        manifest_path=ROOT / "experiments/experiment_manifest.yaml",
        official_splits_path=ROOT / "experiments/official_splits",
        output_root=tmp_path / "case_packets",
        case_unit_ids=[case_unit_id],
    )[0]
    second_path = Path(second.case_packet_path)
    second_text = second_path.read_text(encoding="utf-8")
    second_hash = sha256_file(second_path)

    assert first_text == second_text
    assert first_hash == second_hash


def test_case_packet_excludes_post_run_fields(tmp_path: Path) -> None:
    built = build_case_packets(
        manifest_path=ROOT / "experiments/experiment_manifest.yaml",
        official_splits_path=ROOT / "experiments/official_splits",
        output_root=tmp_path / "case_packets",
        case_unit_ids=["024c982_1"],
    )[0]
    packet = Path(built.case_packet_path).read_text(encoding="utf-8").lower()

    for forbidden in (
        "native score",
        "outcome label",
        "evidence label",
        "final evidence label",
        "unresolve reason",
    ):
        assert forbidden not in packet
