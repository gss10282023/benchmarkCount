from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

from neurips_ed_track_minimal import checklist_guardrails
from neurips_ed_track_minimal.scripts import draft_case_checklist


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "build_webarena_verified_full_812_case_packets.py"
SOURCE_PATH = (
    ROOT / "experiments" / "official_splits" / "webarena_verified_official_812.json"
)
AGENT_INPUTS_PATH = (
    ROOT
    / "experiments"
    / "official_splits"
    / "webarena_verified_agent_inputs_full_812.json"
)
STEP19_MANIFEST_PATH = (
    ROOT / "experiments" / "step19" / "webarena_verified_full_812_manifest.json"
)
SOURCE_BUNDLE_NAME = "webarena_verified_full_812_source_bundle.json"
EXPECTED_TASK_CONTRACT_INDEX_SHA256 = (
    "32b2eb76d2296286fae619f843e985feaf1b3eaf622d90d77133ffb580ab0d49"
)
EXPECTED_AGENT_INPUT_TREE_SHA256 = (
    "98f4f404cae6e794bd2fa1d0c152d43b7fa5d6ee5bffea143a0c9c39ddd4c975"
)
EXPECTED_AGENT_INPUT_TOTAL_BYTES = 235_617
EXPECTED_OFFICIAL_SOURCE_HASHES = {
    "agent_response_evaluator.py": (
        "8ae2caf59c6fafecf4ec259ea67bf79d27f19c7fcbdc33a312cea730c4e54c31"
    ),
    "network_event_evaluator.py": (
        "74bc94874541192d18c6dd221f26599d5279606effc55cf5c059ddce2516c441"
    ),
    "types/eval.py": (
        "f9c2a2aa4fcc839232f3cab88c9618b601c050e2d46b97630f96664257e95140"
    ),
}
EXPECTED_CASE_TOP_LEVEL = {
    "agent_input.json",
    "case_packet.json",
    "case_packet.md",
    "raw_case",
    "raw_case_manifest.json",
}
FORBIDDEN_MODEL_INPUT_TOKENS = (
    b'"expected":',
    b'"retrieved_data":',
    b'"error_details":',
    b'"reference_answer":',
    b'"password":',
    b'"cookie":',
    b'"session":',
    b'"authorization":',
    b"sk-or-v1-",
)

SPEC = importlib.util.spec_from_file_location("wv_packet_builder", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _tree_snapshot(root: Path) -> dict[str, tuple[str, int]]:
    return {
        path.relative_to(root).as_posix(): (_sha256_file(path), path.stat().st_size)
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def _agent_input_tree_digest(packet_root: Path) -> tuple[str, int]:
    lines: list[str] = []
    total_bytes = 0
    for task_id in range(812):
        payload = (packet_root / str(task_id) / "agent_input.json").read_bytes()
        total_bytes += len(payload)
        lines.append(
            f"{task_id}\t{hashlib.sha256(payload).hexdigest()}\t{len(payload)}\n"
        )
    digest = hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()
    return digest, total_bytes


def _bundle_sidecar(bundle_path: Path) -> Path:
    return bundle_path.with_name(f"{bundle_path.name}.sha256")


def _resolve_bundle_input_path(
    raw_path: str,
    *,
    expected: Path,
    packet_root: Path,
    bundle_path: Path,
) -> Path:
    value = Path(raw_path)
    candidates = [value] if value.is_absolute() else [
        ROOT / value,
        packet_root / value,
        bundle_path.parent / value,
    ]
    matches = [candidate.resolve() for candidate in candidates if candidate.is_file()]
    assert expected.resolve() in matches, (
        f"bundle path {raw_path!r} does not resolve to canonical file {expected}"
    )
    return expected


@pytest.fixture(scope="module")
def built_corpus(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    root = tmp_path_factory.mktemp("webarena-source-rich-packets")
    packet_root = root / "packets"
    bundle_path = root / SOURCE_BUNDLE_NAME

    first_index = MODULE.build_packets(
        SOURCE_PATH,
        AGENT_INPUTS_PATH,
        packet_root,
        source_bundle_path=bundle_path,
    )
    first_tree = _tree_snapshot(packet_root)
    first_bundle = bundle_path.read_bytes()
    first_bundle_sidecar = _bundle_sidecar(bundle_path).read_bytes()

    second_index = MODULE.build_packets(
        SOURCE_PATH,
        AGENT_INPUTS_PATH,
        packet_root,
        source_bundle_path=bundle_path,
    )
    second_tree = _tree_snapshot(packet_root)

    return {
        "packet_root": packet_root,
        "bundle_path": bundle_path,
        "first_index": first_index,
        "second_index": second_index,
        "first_tree": first_tree,
        "second_tree": second_tree,
        "first_bundle": first_bundle,
        "second_bundle": bundle_path.read_bytes(),
        "first_bundle_sidecar": first_bundle_sidecar,
        "second_bundle_sidecar": _bundle_sidecar(bundle_path).read_bytes(),
    }


def test_builds_exactly_812_source_rich_packets_deterministically(
    built_corpus: dict[str, Any],
) -> None:
    first = built_corpus["first_index"]
    second = built_corpus["second_index"]
    packet_root: Path = built_corpus["packet_root"]

    assert first["packet_count"] == 812
    assert first["task_type_counts"] == {
        "MUTATE": 374,
        "NAVIGATE": 113,
        "RETRIEVE": 325,
    }
    assert first["evaluator_task_counts"] == {
        "AgentResponseEvaluator": 812,
        "NetworkEventEvaluator": 488,
    }
    assert first["evaluator_config_counts"] == {
        "AgentResponseEvaluator": 812,
        "NetworkEventEvaluator": 663,
    }
    assert first == second
    assert built_corpus["first_tree"] == built_corpus["second_tree"]
    assert built_corpus["first_bundle"] == built_corpus["second_bundle"]
    assert (
        built_corpus["first_bundle_sidecar"]
        == built_corpus["second_bundle_sidecar"]
    )
    assert not list(packet_root.rglob("draft_case_packet*"))

    numeric_dirs = sorted(
        (path for path in packet_root.iterdir() if path.is_dir()),
        key=lambda path: int(path.name),
    )
    assert [int(path.name) for path in numeric_dirs] == list(range(812))
    for case_dir in numeric_dirs:
        assert {path.name for path in case_dir.iterdir()} == EXPECTED_CASE_TOP_LEVEL
        assert (case_dir / "raw_case").is_dir()
        assert not (case_dir / "raw_case").is_symlink()

    task_contract_path = packet_root / "task_contract_index.json"
    assert _sha256_file(task_contract_path) == EXPECTED_TASK_CONTRACT_INDEX_SHA256
    assert first["task_contract_index_sha256"] == EXPECTED_TASK_CONTRACT_INDEX_SHA256
    assert (packet_root / "task_contract_index.json.sha256").read_text(
        encoding="utf-8"
    ) == (
        f"{EXPECTED_TASK_CONTRACT_INDEX_SHA256}  task_contract_index.json\n"
    )

    index_path = packet_root / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index_core = dict(index)
    claimed_core_hash = index_core.pop("index_core_sha256")
    assert hashlib.sha256(MODULE.canonical_bytes(index_core)).hexdigest() == claimed_core_hash
    assert (packet_root / "index.json.sha256").read_text(encoding="utf-8") == (
        f"{_sha256_file(index_path)}  index.json\n"
    )

    bundle_path: Path = built_corpus["bundle_path"]
    assert first["source_bundle_sha256"] == _sha256_file(bundle_path)
    assert Path(first["source_bundle_path"]).name == SOURCE_BUNDLE_NAME
    assert _bundle_sidecar(bundle_path).read_text(encoding="utf-8") == (
        f"{_sha256_file(bundle_path)}  {SOURCE_BUNDLE_NAME}\n"
    )


def test_rebuild_refuses_a_partial_preexisting_agent_input_tree(
    tmp_path: Path,
) -> None:
    packet_root = tmp_path / "partial-packets"
    partial_case = packet_root / "0"
    partial_case.mkdir(parents=True)
    (partial_case / "agent_input.json").write_bytes(
        (ROOT / "experiments/case_packets/webarena_verified/0/agent_input.json").read_bytes()
    )

    with pytest.raises(
        ValueError,
        match="partial pre-existing agent-input tree",
    ):
        MODULE.build_packets(SOURCE_PATH, AGENT_INPUTS_PATH, packet_root)

    # Fail closed before replacing the only pre-existing model-visible byte.
    assert (partial_case / "agent_input.json").is_file()


def test_packets_are_minimal_compatible_source_complete_and_agent_safe(
    built_corpus: dict[str, Any],
) -> None:
    packet_root: Path = built_corpus["packet_root"]
    bundle_path: Path = built_corpus["bundle_path"]
    official_tasks = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    official_inputs = json.loads(AGENT_INPUTS_PATH.read_text(encoding="utf-8"))
    task_by_id = {int(task["task_id"]): task for task in official_tasks}
    input_by_id = {int(value["task_id"]): value for value in official_inputs}
    task_contract = json.loads(
        (packet_root / "task_contract_index.json").read_text(encoding="utf-8")
    )
    contract_by_id = {
        int(entry["task_id"]): entry for entry in task_contract["entries"]
    }

    assert set(task_by_id) == set(input_by_id) == set(contract_by_id) == set(range(812))
    assert _sha256_file(packet_root / "task_contract_index.json") == (
        EXPECTED_TASK_CONTRACT_INDEX_SHA256
    )

    for task_id in range(812):
        case_dir = packet_root / str(task_id)
        raw_dir = case_dir / "raw_case"
        agent_input_path = case_dir / "agent_input.json"
        packet_json_path = case_dir / "case_packet.json"
        packet_markdown_path = case_dir / "case_packet.md"
        raw_manifest_path = case_dir / "raw_case_manifest.json"

        agent_bytes = agent_input_path.read_bytes()
        agent_input = json.loads(agent_bytes)
        packet = json.loads(packet_json_path.read_text(encoding="utf-8"))
        manifest = json.loads(raw_manifest_path.read_text(encoding="utf-8"))
        markdown = packet_markdown_path.read_text(encoding="utf-8")
        source_task = task_by_id[task_id]

        # The model projection is byte-for-byte frozen and is the only place to
        # apply the private-evaluator/secret denylist.  The canonical drafter
        # packet intentionally contains the official evaluator configuration.
        assert agent_bytes == _json_bytes(input_by_id[task_id])
        assert set(agent_input) == MODULE.AGENT_INPUT_FIELDS
        assert _sha256_file(agent_input_path) == contract_by_id[task_id][
            "agent_input_sha256"
        ]
        agent_bytes_lower = agent_bytes.lower()
        for token in FORBIDDEN_MODEL_INPUT_TOKENS:
            assert token.lower() not in agent_bytes_lower

        assert packet["task"]["task_type"] in MODULE.ALLOWED_TASK_TYPES
        assert packet["task"]["revision"] == int(source_task["revision"])
        assert packet["task"]["sites"] == list(source_task["sites"])
        assert packet["task"]["resolved_start_urls"] == agent_input["start_urls"]
        assert packet["evaluator_reference"]["evaluator_names"]
        assert packet["evaluator_reference"]["required_run_artifacts"] == [
            "agent_response.json",
            "network.har",
        ]
        assert _sha256_file(packet_json_path) == contract_by_id[task_id][
            "case_packet_sha256"
        ]

        assert manifest["domain"] == "webarena_verified"
        assert manifest["case_unit_id"] == str(task_id)
        assert manifest["task_id"] == str(task_id)
        assert manifest["source_sha256"] == MODULE.SOURCE_SHA256
        assert manifest["source_task_sha256"] == hashlib.sha256(
            MODULE.canonical_bytes(source_task)
        ).hexdigest()
        assert manifest["model_visible_files"] == ["agent_input.json"]
        for required_field in (
            "source_refs",
            "copied_files",
            "official_files",
            "derived_files",
            "packet_files",
            "file_sources",
            "sha256_per_file",
        ):
            assert required_field in manifest

        copied_files = list(manifest["copied_files"])
        packet_files = list(manifest["packet_files"])
        actual_raw_files = {
            path.relative_to(raw_dir).as_posix()
            for path in raw_dir.rglob("*")
            if path.is_file() and not path.is_symlink()
        }
        assert copied_files
        assert set(copied_files) == actual_raw_files
        assert set(manifest["sha256_per_file"]) == actual_raw_files
        assert set(packet_files) <= actual_raw_files
        assert set(manifest["official_files"]) <= actual_raw_files
        assert set(manifest["derived_files"]) <= actual_raw_files
        assert set(manifest["file_sources"]) >= set(packet_files)
        assert not any(path.is_symlink() for path in raw_dir.rglob("*"))
        for relative in copied_files:
            assert Path(relative).as_posix() == relative
            assert not Path(relative).is_absolute()
            assert ".." not in Path(relative).parts
            assert manifest["sha256_per_file"][relative] == _sha256_file(
                raw_dir / relative
            )

        metadata = draft_case_checklist.extract_case_metadata(markdown)
        assert metadata == {
            "domain": "webarena_verified",
            "case_unit_id": str(task_id),
            "task_id": str(task_id),
        }
        allowed_support_paths = checklist_guardrails.case_packet_support_paths(markdown)
        assert allowed_support_paths == {"case_packet.md", *packet_files}
        for relative in packet_files:
            assert markdown.count(f"### `{relative}`") == 1

        # The packet must contain the exact per-task official specification,
        # not merely a public/controller summary.
        assert "derived/task.json" in packet_files
        assert json.loads((raw_dir / "derived/task.json").read_text(encoding="utf-8")) == (
            source_task
        )
        assert '"eval":' in markdown
        assert '"expected":' in markdown
        assert "agent_response.json" in markdown
        assert "network.har" in markdown
        assert "TaskEvalResult.score" in markdown

        agent_response_sources = [
            relative
            for relative in packet_files
            if relative.endswith("/agent_response_evaluator.py")
        ]
        task_eval_sources = [
            relative for relative in packet_files if relative.endswith("/types/eval.py")
        ]
        assert len(agent_response_sources) == 1
        assert len(task_eval_sources) == 1
        assert _sha256_file(raw_dir / agent_response_sources[0]) == (
            EXPECTED_OFFICIAL_SOURCE_HASHES["agent_response_evaluator.py"]
        )
        assert _sha256_file(raw_dir / task_eval_sources[0]) == (
            EXPECTED_OFFICIAL_SOURCE_HASHES["types/eval.py"]
        )

        uses_network_evaluator = any(
            config.get("evaluator") == "NetworkEventEvaluator"
            for config in source_task["eval"]
        )
        network_sources = [
            relative
            for relative in packet_files
            if relative.endswith("/network_event_evaluator.py")
        ]
        if uses_network_evaluator:
            assert len(network_sources) == 1
            assert _sha256_file(raw_dir / network_sources[0]) == (
                EXPECTED_OFFICIAL_SOURCE_HASHES["network_event_evaluator.py"]
            )

    tree_digest, total_bytes = _agent_input_tree_digest(packet_root)
    assert tree_digest == EXPECTED_AGENT_INPUT_TREE_SHA256
    assert total_bytes == EXPECTED_AGENT_INPUT_TOTAL_BYTES

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert bundle["schema_version"] == "contract_source_bundle.v2"
    assert bundle["source_count"] == 812 == len(bundle["sources"])
    assert bundle["manifest_path"].endswith(
        "experiments/step19/webarena_verified_full_812_manifest.json"
    )
    assert bundle["manifest_sha256"] == _sha256_file(STEP19_MANIFEST_PATH)
    assert [entry["case_unit_id"] for entry in bundle["sources"]] == [
        str(task_id) for task_id in range(812)
    ]
    assert len({entry["contract_id"] for entry in bundle["sources"]}) == 812
    for task_id, entry in enumerate(bundle["sources"]):
        assert entry["domain"] == "webarena_verified"
        assert entry["task_id"] == str(task_id)
        assert entry["source_ref"].endswith(f"#task_id={task_id}")
        draft_input = entry["draft_input"]
        assert "draft_case_packet" not in draft_input["case_packet_path"]
        for path_field in ("case_packet_path", "raw_case_manifest_path"):
            declared_path = Path(draft_input[path_field])
            assert not declared_path.is_absolute()
            assert ".." not in declared_path.parts
        packet_path = packet_root / str(task_id) / "case_packet.md"
        manifest_path = packet_root / str(task_id) / "raw_case_manifest.json"
        _resolve_bundle_input_path(
            draft_input["case_packet_path"],
            expected=packet_path,
            packet_root=packet_root,
            bundle_path=bundle_path,
        )
        _resolve_bundle_input_path(
            draft_input["raw_case_manifest_path"],
            expected=manifest_path,
            packet_root=packet_root,
            bundle_path=bundle_path,
        )
        assert draft_input["case_packet_sha256"] == _sha256_file(packet_path)
        assert draft_input["raw_case_manifest_sha256"] == _sha256_file(manifest_path)
