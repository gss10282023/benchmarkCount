from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "scripts/audit_webarena_results_storage_readonly.sh"
PROVISION = ROOT / "scripts/provision_webarena_results_storage.sh"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_storage_scripts_are_valid_bash() -> None:
    for path in (AUDIT, PROVISION):
        subprocess.run(["bash", "-n", str(path)], check=True)


def test_readonly_audit_contains_no_mutating_storage_commands() -> None:
    text = _text(AUDIT)
    forbidden = (
        "wipefs --all",
        "wipefs -a",
        "\nmount ",
        "\numount ",
        "\nparted ",
        "\nfdisk ",
        "dd if=",
        ">>/etc/fstab",
        ">/etc/fstab",
    )
    assert all(token not in text for token in forbidden)
    assert "\nmkfs.ext4 " not in text
    assert "destructive_operation_performed\": False" in text
    assert "raw_sector_residual_data_ruled_out\": False" in text


def test_provisioning_requires_identity_bound_exact_confirmation_before_mkfs() -> None:
    text = _text(PROVISION)
    token_check = '[[ $confirmation_token == "$expected_token" ]]'
    mkfs = 'mkfs.ext4 -F -L webarena-results -- "$device"'
    assert token_check in text
    assert mkfs in text
    assert text.index("[[ $execute == true ]]") < text.index(token_check)
    assert text.index(token_check) < text.index(mkfs)
    assert text.count('\nmkfs.ext4 -F -L webarena-results -- "$device"') == 1


def test_every_destructive_precondition_precedes_mkfs_boundary() -> None:
    text = _text(PROVISION)
    mkfs_index = text.index('mkfs.ext4 -F -L webarena-results -- "$device"')
    required_preconditions = (
        '[[ $device != "$root_disk" ]]',
        "device has partitions or child block devices",
        "device is mounted",
        "device has block holders",
        "device has block slaves",
        "device is active swap",
        "device is an LVM physical volume",
        "device is referenced by md",
        "device is open or fuser could not prove it unused",
        "device is referenced by fstab",
        "device contains a filesystem or partition signature",
        "blkid found a signature",
        "absence of a partition table",
        "$MOUNT_POINT already exists",
        "$CONTROLLER_RESULTS_PATH already exists",
    )
    for precondition in required_preconditions:
        assert precondition in text
        assert text.index(precondition) < mkfs_index


def test_provisioning_uses_uuid_fstab_projection_and_hard_capacity_gate() -> None:
    text = _text(PROVISION)
    assert 'fstab_line="UUID=${filesystem_uuid} ${MOUNT_POINT} ext4' in text
    assert 'ln -s "$MOUNT_POINT/$RESULTS_SUBDIRECTORY" "$CONTROLLER_RESULTS_PATH"' in text
    assert "readonly MIN_FREE_BYTES=350000000000" in text
    assert "mounted results disk is below the 350 GB gate" in text
    assert 'printf \'%s  %s\\n\'' in text
    assert 'chmod 0600 "${receipt_path}.sha256"' in text


def test_missing_execute_flag_fails_without_reaching_machine_or_disk_checks() -> None:
    completed = subprocess.run(
        [
            "bash",
            str(PROVISION),
            "--device",
            "/dev/definitely-not-a-device",
            "--expected-size-bytes",
            "960197124096",
            "--expected-machine-id-sha256",
            "0" * 64,
            "--confirmation-token",
            "wrong",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    assert "--execute is required" in completed.stderr
    assert "mkfs" not in completed.stdout
