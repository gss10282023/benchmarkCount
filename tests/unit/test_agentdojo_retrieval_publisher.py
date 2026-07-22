from __future__ import annotations

import base64
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
import tarfile
from typing import Any

import pytest

from evidence_system.adapters import agentdojo_remote_inventory as remote
from evidence_system.cli import retrieve_agentdojo_full_evidence as controller
from evidence_system.contracts.common import ContractLifecycleError
from evidence_system.core.hashing import sha256_file, sha256_object


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _remote_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    monkeypatch.setattr(remote, "EXPECTED_RECORD_SLOT_COUNT", 1)
    raw_root = tmp_path / "raw"
    blind_root = tmp_path / "blind"
    snapshot_root = tmp_path / "snapshots"
    for path in (raw_root, blind_root, snapshot_root):
        path.mkdir()
    lifecycle_lock = blind_root / ".canonical-lifecycle.lock"
    lifecycle_lock.write_bytes(b"")

    binding = "1" * 64
    identity = "2" * 64
    adapter = raw_root / binding / "adapter"
    adapter.mkdir(parents=True)
    artifact = adapter / "payload.bin"
    artifact.write_bytes(b"opaque-native-evidence\n")
    artifact_projection = [
        {"path": "adapter/payload.bin", "sha256": sha256_file(artifact)}
    ]
    marker = {
        "schema_version": "agentdojo_formal_job_completion/v2",
        "completed_at": "2026-07-16T10:00:00+00:00",
        "execution_lock_sha256": "3" * 64,
        "execution_policy_sha256": "4" * 64,
        "job_binding_sha256": binding,
        "job_identity_sha256": identity,
        "stage_authorization_sha256": "5" * 64,
        "formal_stage_id": "recovery-a",
        "formal_stage_session_id": "session-a",
        "formal_execution_context_sha256": "6" * 64,
        "artifact_file_count": 1,
        "artifact_tree_sha256": sha256_object(artifact_projection),
        "artifact_total_bytes": artifact.stat().st_size,
        "native_episode_count": 3,
        "attempt_tree_sha256": "7" * 64,
        "attempt_file_count": 7,
        "attempt_total_bytes": 4096,
        "supervisor_exit_receipt_sha256": "8" * 64,
        "worker_status": "completed",
        "postprocessor": "agentdojo_formal_postprocessor/v1",
    }
    marker_path = adapter / remote.COMPLETION_MARKER.removeprefix("adapter/")
    _write_json(marker_path, marker)
    entry = {
        "schema_version": "agentdojo_formal_remote_completion_index_entry/v2",
        **{
            field: marker[field]
            for field in (
                "execution_lock_sha256",
                "execution_policy_sha256",
                "job_binding_sha256",
                "job_identity_sha256",
                "stage_authorization_sha256",
                "formal_stage_id",
                "formal_stage_session_id",
                "formal_execution_context_sha256",
                "artifact_file_count",
                "artifact_tree_sha256",
                "artifact_total_bytes",
                "native_episode_count",
                "attempt_tree_sha256",
                "attempt_file_count",
                "attempt_total_bytes",
                "supervisor_exit_receipt_sha256",
            )
        },
        "canonical_job_relative_path": binding,
        "completion_marker_relative_path": f"{binding}/{remote.COMPLETION_MARKER}",
        "completion_marker_file_sha256": sha256_file(marker_path),
        "completion_marker_semantic_sha256": sha256_object(marker),
        "blind_only": True,
        "contains_case_agent_prompt_response_trajectory_evaluator_or_label": False,
    }
    blind_names = (
        "formal-completion-journal.v2.jsonl",
        "formal-failed-attempt-journal.v2.jsonl",
        "formal_execution_completion_receipt.json",
        "formal_remote_completion_index.json",
    )
    for index, name in enumerate(blind_names):
        (blind_root / name).write_bytes(b"" if index == 1 else f"blind-{index}\n".encode())
    blind_entries = [
        {
            "relative_path": name,
            "sha256": sha256_file(blind_root / name),
            "size_bytes": (blind_root / name).stat().st_size,
        }
        for name in sorted(blind_names)
    ]
    request = {
        "schema_version": remote.REQUEST_SCHEMA_VERSION,
        "execution_lock_sha256": marker["execution_lock_sha256"],
        "execution_policy_sha256": marker["execution_policy_sha256"],
        "remote_raw_root": str(raw_root),
        "remote_blind_root": str(blind_root),
        "retrieval_snapshot_root": str(snapshot_root),
        "retrieval_lifecycle_lock": str(lifecycle_lock),
        "entry_count": 1,
        "entries_sha256": sha256_object([entry]),
        "entries": [entry],
        "blind_metadata_entry_count": 4,
        "blind_metadata_entries_sha256": sha256_object(blind_entries),
        "blind_metadata_entries": blind_entries,
    }
    return {
        "request": request,
        "raw_root": raw_root,
        "blind_root": blind_root,
        "snapshot_root": snapshot_root,
        "lifecycle_lock": lifecycle_lock,
        "artifact": artifact,
    }


def _prepare(fixture: dict[str, Any]) -> dict[str, Any]:
    return remote.prepare_retrieval_snapshot(
        request=fixture["request"],
        remote_raw_root=fixture["raw_root"],
        remote_blind_root=fixture["blind_root"],
        snapshot_root=fixture["snapshot_root"],
        lifecycle_lock=fixture["lifecycle_lock"],
    )


def test_remote_snapshot_is_one_locked_raw_plus_blind_tar_and_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _remote_fixture(tmp_path, monkeypatch)
    receipt = _prepare(fixture)
    assert receipt["pre_post_inventory_identical"] is True
    assert receipt["lifecycle_flock"] == "exclusive"
    assert receipt["source_inventory"]["raw_file_count"] == 2
    assert receipt["source_inventory"]["blind_metadata_file_count"] == 4
    archive = Path(receipt["archive"]["path"])
    assert sha256_file(archive) == receipt["archive"]["sha256"]
    with tarfile.open(archive, "r:") as tar:
        names = sorted(member.name for member in tar.getmembers())
        assert names == [row["path"] for row in receipt["source_inventory"]["files"]]
        assert all(member.isfile() and not member.islnk() for member in tar.getmembers())
    assert _prepare(fixture) == receipt


def test_remote_snapshot_pre_post_mismatch_publishes_no_archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _remote_fixture(tmp_path, monkeypatch)
    original = remote._create_archive_temporary

    def mutate_after_archive(**kwargs: Any) -> Path:
        temporary = original(**kwargs)
        fixture["artifact"].write_bytes(b"mutated-after-pre-inventory\n")
        return temporary

    monkeypatch.setattr(remote, "_create_archive_temporary", mutate_after_archive)
    with pytest.raises(remote.RemoteInventoryError, match="differs"):
        _prepare(fixture)
    assert not list(fixture["snapshot_root"].glob("*.tar"))
    assert not list(fixture["snapshot_root"].glob("*.receipt.json"))
    assert not list(fixture["snapshot_root"].glob(".*.tmp"))


@pytest.mark.parametrize("kind", ["fifo", "hardlink"])
def test_remote_inventory_rejects_special_nodes_and_hardlinks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    fixture = _remote_fixture(tmp_path, monkeypatch)
    adapter = fixture["artifact"].parent
    if kind == "fifo":
        os.mkfifo(adapter / "forbidden.fifo")
    else:
        os.link(fixture["artifact"], adapter / "forbidden-hardlink.bin")
    with pytest.raises(remote.RemoteInventoryError, match="link or special"):
        _prepare(fixture)


@pytest.mark.parametrize(
    ("member_type", "name"),
    [
        (tarfile.SYMTYPE, "raw/a/link"),
        (tarfile.LNKTYPE, "raw/a/hardlink"),
        (tarfile.FIFOTYPE, "raw/a/fifo"),
        (tarfile.CHRTYPE, "raw/a/device"),
        (tarfile.REGTYPE, "../escape"),
    ],
)
def test_controller_safe_extraction_rejects_unsafe_tar_members(
    tmp_path: Path, member_type: bytes, name: str
) -> None:
    archive = tmp_path / "snapshot.tar"
    with tarfile.open(archive, "w:") as tar:
        info = tarfile.TarInfo(name)
        info.type = member_type
        if member_type == tarfile.REGTYPE:
            info.size = 1
            tar.addfile(info, io.BytesIO(b"x"))
        else:
            info.linkname = "target"
            tar.addfile(info)
    output = tmp_path / "output"
    output.mkdir()
    expected = [{"path": name, "sha256": hashlib.sha256(b"x").hexdigest(), "size_bytes": 1}]
    with pytest.raises(controller.RetrievalError):
        controller._extract_regular_snapshot(
            archive_path=archive,
            output_root=output,
            expected_files=expected,
        )
    assert not (tmp_path / "escape").exists()


def test_controller_atomic_publication_is_destination_absent_noreplace(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    (source / "evidence.bin").write_bytes(b"opaque\n")
    controller._rename_directory_noreplace(source, destination)
    assert (destination / "evidence.bin").read_bytes() == b"opaque\n"

    another = tmp_path / "another"
    another.mkdir()
    with pytest.raises(controller.RetrievalError, match="already exists"):
        controller._rename_directory_noreplace(another, destination)


def test_known_hosts_is_exact_single_ed25519_pin(tmp_path: Path) -> None:
    key_blob = base64.b64decode(
        "AAAAC3NzaC1lZDI1NTE5AAAAIFOIGFEp1pDVQ1lanOoszsKWVYQ9gWJwvqn2XEX07ovl"
    )
    fingerprint = "SHA256:" + base64.b64encode(
        hashlib.sha256(key_blob).digest()
    ).decode().rstrip("=")
    known_hosts = tmp_path / "known_hosts"
    known_hosts.write_text(
        "64.177.120.135 ssh-ed25519 "
        "AAAAC3NzaC1lZDI1NTE5AAAAIFOIGFEp1pDVQ1lanOoszsKWVYQ9gWJwvqn2XEX07ovl\n",
        encoding="utf-8",
    )
    inputs = SimpleNamespace(
        sealed={
            "ssh_known_hosts_file": {
                "path": str(known_hosts),
                "sha256": sha256_file(known_hosts),
            },
            "ssh_host": "64.177.120.135",
            "ssh_port": 22,
            "ssh_host_ed25519_fingerprint": fingerprint,
        },
        infra={"ssh_known_hosts_file": str(known_hosts)},
    )
    assert controller._verify_known_hosts(inputs)["fingerprint"] == fingerprint
    known_hosts.write_text(known_hosts.read_text() + "# second line\n", encoding="utf-8")
    inputs.sealed["ssh_known_hosts_file"]["sha256"] = sha256_file(known_hosts)
    # Comments do not add a second pin; a second key does.
    known_hosts.write_text(
        known_hosts.read_text()
        + "64.177.120.135 ssh-ed25519 "
        + base64.b64encode(b"different-key").decode()
        + "\n",
        encoding="utf-8",
    )
    inputs.sealed["ssh_known_hosts_file"]["sha256"] = sha256_file(known_hosts)
    with pytest.raises(controller.RetrievalError, match="exactly one"):
        controller._verify_known_hosts(inputs)


def test_retrieval_v2_gate_fails_before_ssh_or_transfer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        controller,
        "_preflight_inputs",
        lambda **_: (_ for _ in ()).throw(
            ContractLifecycleError("v2 freeze/quiescence absent")
        ),
    )

    def forbidden_runner(*_args: Any, **_kwargs: Any) -> Any:
        pytest.fail("no SSH/rsync process may start before the v2 gate")

    with pytest.raises(ContractLifecycleError, match="v2 freeze/quiescence absent"):
        controller.retrieve_agentdojo_full_evidence(command_runner=forbidden_runner)


def test_single_tar_transfer_never_uses_rsync_delete(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.tar"
    source.write_bytes(b"hash-locked-tar\n")
    destination = tmp_path / "downloaded.tar"
    captured: list[str] = []

    def runner(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        captured.extend(argv)
        shutil.copyfile(source, destination)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    inputs = SimpleNamespace(
        sealed={"execution_user": "benchmark", "ssh_host": "64.177.120.135"}
    )
    controller._transfer_snapshot_archive(
        inputs=inputs,
        remote_receipt={
            "archive": {
                "path": "/srv/snapshot.tar",
                "sha256": sha256_file(source),
                "size_bytes": source.stat().st_size,
            }
        },
        archive_path=destination,
        ssh_argv=["ssh", "-o", "StrictHostKeyChecking=yes"],
        command_runner=runner,
    )
    assert not any("--delete" in argument for argument in captured)
    assert captured.count("--") == 1
    assert captured[-1] == str(destination)
