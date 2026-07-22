#!/usr/bin/env bash
# Read-only, secret-free audit of one proposed WebArena results disk.
#
# This script deliberately performs no mkdir, mount, filesystem, partition-table,
# fstab, package, or service mutation.  It is safe to stream over SSH with
# `bash -s -- ...`; nothing is installed on the remote host.

set -euo pipefail
export LC_ALL=C

readonly SCHEMA_VERSION="webarena_verified_storage_readonly_host_audit/v1"
readonly MIN_FREE_BYTES=350000000000
readonly RESULTS_MOUNT_POINT="/opt/webarena-results"
readonly CONTROLLER_RESULTS_PATH="/opt/webarena-controller/current/results"

usage() {
  cat >&2 <<'EOF'
usage: audit_webarena_results_storage_readonly.sh \
  --expected-device /dev/DEVICE \
  --expected-size-bytes BYTES \
  --expected-machine-id-sha256 SHA256

The script is read-only.  It emits one JSON receipt to stdout and stores nothing.
EOF
}

die() {
  echo "storage audit refused: $*" >&2
  exit 2
}

sha256_text() {
  printf '%s' "$1" | sha256sum | awk '{print $1}'
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "required command is missing: $1"
}

expected_device=""
expected_size_bytes=""
expected_machine_id_sha256=""
while (($#)); do
  case "$1" in
    --expected-device)
      (($# >= 2)) || die "--expected-device requires a value"
      expected_device=$2
      shift 2
      ;;
    --expected-size-bytes)
      (($# >= 2)) || die "--expected-size-bytes requires a value"
      expected_size_bytes=$2
      shift 2
      ;;
    --expected-machine-id-sha256)
      (($# >= 2)) || die "--expected-machine-id-sha256 requires a value"
      expected_machine_id_sha256=$2
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

[[ $expected_device =~ ^/dev/[[:alnum:]_.-]+$ ]] || die "invalid expected device"
[[ $expected_size_bytes =~ ^[1-9][0-9]+$ ]] || die "invalid expected size"
[[ $expected_machine_id_sha256 =~ ^[0-9a-f]{64}$ ]] || die "invalid machine-id digest"

for command_name in \
  awk basename blkid blockdev date df find findfs findmnt fuser grep head \
  hostname lsblk pvs python3 readlink sed sfdisk sha256sum swapon tail tr \
  wc wipefs; do
  require_command "$command_name"
done

[[ -r /etc/machine-id ]] || die "/etc/machine-id is not readable"
actual_machine_id_sha256=$(sha256sum /etc/machine-id | awk '{print $1}')
[[ $actual_machine_id_sha256 == "$expected_machine_id_sha256" ]] || \
  die "machine-id digest differs from the audited host"

[[ -b $expected_device ]] || die "expected device is not a block device"
device=$(readlink -f -- "$expected_device")
[[ $device == "$expected_device" ]] || die "device must be a canonical /dev path"
[[ $(lsblk -dn -o TYPE -- "$device" | tr -d '[:space:]') == disk ]] || \
  die "expected device is not a whole disk"

actual_size_bytes=$(blockdev --getsize64 "$device")
[[ $actual_size_bytes == "$expected_size_bytes" ]] || \
  die "device size differs from the audited size"

root_source=$(findmnt -n -o SOURCE /)
root_parent=$(lsblk -no PKNAME -- "$root_source" | head -1)
[[ -n $root_parent ]] || die "cannot identify the root disk"
root_disk="/dev/$(basename "$root_parent")"
[[ $device != "$root_disk" ]] || die "candidate is the root disk"
if lsblk -srno PATH -- "$root_source" | grep -Fxq -- "$device"; then
  die "candidate is an ancestor of the root filesystem"
fi

root_df=$(df -B1 --output=source,fstype,size,used,avail,pcent,target /)
lsblk_raw=$(lsblk --bytes --json --paths \
  --output NAME,KNAME,PATH,TYPE,SIZE,FSTYPE,FSVER,LABEL,UUID,PARTUUID,MOUNTPOINTS,PKNAME,RO,RM,MODEL)
findmnt_raw=$(findmnt --bytes --json --output SOURCE,TARGET,FSTYPE,OPTIONS)
pvs_raw=$(pvs --reportformat json --units b --nosuffix \
  -o pv_name,pv_size,pv_free,vg_name)
swap_raw=$(swapon --show --bytes --noheadings --output NAME,TYPE,SIZE,USED,PRIO || true)
mdstat_raw=$(sed -n '1,120p' /proc/mdstat)
fstab_projection=$(sed -E 's/[[:space:]]+#.*$//' /etc/fstab | \
  awk 'NF && $1 !~ /^#/ {print $1, $2, $3, $4}')

wipefs_raw=$(wipefs --no-act --noheadings \
  --output TYPE,UUID,LABEL,OFFSET -- "$device")
set +e
blkid_raw=$(blkid -p -o export -- "$device" 2>/dev/null)
blkid_rc=$?
sfdisk_stdout=$(sfdisk --json -- "$device" 2>/dev/null)
sfdisk_rc=$?
sfdisk_stderr=$(sfdisk --json -- "$device" 2>&1 >/dev/null)
set -e

kname=$(basename "$device")
mount_matches=$(findmnt -rn -S "$device" 2>/dev/null || true)
holder_paths=$(find "/sys/class/block/$kname/holders" -mindepth 1 -maxdepth 1 \
  2>/dev/null || true)
slave_paths=$(find "/sys/class/block/$kname/slaves" -mindepth 1 -maxdepth 1 \
  2>/dev/null || true)
children=$(lsblk -nr -o PATH -- "$device" | tail -n +2)

fstab_reference_count=0
while read -r source _target _rest; do
  [[ -n ${source:-} ]] || continue
  resolved=""
  case "$source" in
    UUID=*|LABEL=*|PARTUUID=*|PARTLABEL=*)
      resolved=$(findfs "$source" 2>/dev/null || true)
      ;;
    /dev/*)
      resolved=$(readlink -f -- "$source" 2>/dev/null || true)
      ;;
  esac
  if [[ $resolved == "$device" ]]; then
    ((fstab_reference_count += 1))
  fi
done <<<"$fstab_projection"

set +e
fuser -s "$device" 2>/dev/null
fuser_rc=$?
set -e
[[ $fuser_rc == 0 || $fuser_rc == 1 ]] || die "fuser probe failed"
open_reference_count=0
[[ $fuser_rc == 1 ]] || open_reference_count=1

read_only=$(blockdev --getro "$device")
removable=$(lsblk -dn -o RM -- "$device" | tr -d '[:space:]')
child_count=$(printf '%s' "$children" | awk 'NF{n++} END{print n+0}')
mount_reference_count=$(printf '%s' "$mount_matches" | awk 'NF{n++} END{print n+0}')
holder_count=$(printf '%s' "$holder_paths" | awk 'NF{n++} END{print n+0}')
slave_count=$(printf '%s' "$slave_paths" | awk 'NF{n++} END{print n+0}')
swap_reference_count=$(printf '%s\n' "$swap_raw" | \
  awk -v d="$device" '$1==d{n++} END{print n+0}')
lvm_pv_reference_count=$(pvs --noheadings -o pv_name 2>/dev/null | \
  awk -v d="$device" '$1==d{n++} END{print n+0}')
md_reference_count=$(printf '%s\n' "$mdstat_raw" | \
  grep -Ewc "(^|[[:space:]])${kname}([[:space:]\[])" || true)
wipefs_signature_count=$(printf '%s' "$wipefs_raw" | awk 'NF{n++} END{print n+0}')
blkid_field_count=$(printf '%s' "$blkid_raw" | awk 'NF{n++} END{print n+0}')
sfdisk_stdout_bytes=$(printf '%s' "$sfdisk_stdout" | wc -c | tr -d '[:space:]')
sfdisk_no_table=false
if [[ $sfdisk_rc == 1 && $sfdisk_stdout_bytes == 0 && \
      $sfdisk_stderr == *"does not contain a recognized partition table"* ]]; then
  sfdisk_no_table=true
fi

results_mount_exists=false
controller_results_exists=false
[[ ! -e $RESULTS_MOUNT_POINT && ! -L $RESULTS_MOUNT_POINT ]] || \
  results_mount_exists=true
[[ ! -e $CONTROLLER_RESULTS_PATH && ! -L $CONTROLLER_RESULTS_PATH ]] || \
  controller_results_exists=true

root_total_bytes=$(df -B1 --output=size / | tail -1 | tr -d '[:space:]')
root_used_bytes=$(df -B1 --output=used / | tail -1 | tr -d '[:space:]')
root_available_bytes=$(df -B1 --output=avail / | tail -1 | tr -d '[:space:]')
root_threshold_satisfied=false
((root_available_bytes >= MIN_FREE_BYTES)) && root_threshold_satisfied=true

metadata_empty=true
for value in \
  "$read_only" "$removable" "$child_count" "$mount_reference_count" \
  "$holder_count" "$slave_count" "$swap_reference_count" \
  "$lvm_pv_reference_count" "$md_reference_count" "$fstab_reference_count" \
  "$open_reference_count" "$wipefs_signature_count" "$blkid_field_count"; do
  [[ $value == 0 ]] || metadata_empty=false
done
[[ $blkid_rc == 2 ]] || metadata_empty=false
[[ $sfdisk_no_table == true ]] || metadata_empty=false
[[ $results_mount_exists == false ]] || metadata_empty=false
[[ $controller_results_exists == false ]] || metadata_empty=false

status=fail
[[ $metadata_empty == true ]] && status=pass
confirmation_token="ERASE_WEBARENA_RESULTS:${actual_machine_id_sha256}:${device}:${actual_size_bytes}"
model_sha256=$(lsblk -dn -o MODEL -- "$device" | \
  sed 's/[[:space:]]*$//' | sha256sum | awk '{print $1}')
hostname_sha256=$(hostname | sha256sum | awk '{print $1}')
major_minor=$(lsblk -dn -o MAJ:MIN -- "$device" | tr -d '[:space:]')
recorded_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)

python3 - \
  "$SCHEMA_VERSION" "$status" "$recorded_at_utc" \
  "$actual_machine_id_sha256" "$hostname_sha256" \
  "$root_source" "$root_disk" "$root_total_bytes" "$root_used_bytes" \
  "$root_available_bytes" "$root_threshold_satisfied" \
  "$(sha256_text "$root_df")" "$(sha256_text "$lsblk_raw")" \
  "$(sha256_text "$findmnt_raw")" "$(sha256_text "$pvs_raw")" \
  "$(sha256_text "$swap_raw")" "$(sha256_text "$mdstat_raw")" \
  "$(sha256_text "$fstab_projection")" \
  "$device" "$major_minor" "$actual_size_bytes" "$model_sha256" \
  "$read_only" "$removable" "$child_count" "$mount_reference_count" \
  "$holder_count" "$slave_count" "$swap_reference_count" \
  "$lvm_pv_reference_count" "$md_reference_count" \
  "$fstab_reference_count" "$open_reference_count" \
  "$wipefs_signature_count" "$(sha256_text "$wipefs_raw")" \
  "$blkid_rc" "$blkid_field_count" "$(sha256_text "$blkid_raw")" \
  "$sfdisk_rc" "$sfdisk_stdout_bytes" "$sfdisk_no_table" \
  "$(sha256_text "$sfdisk_stdout")" "$(sha256_text "$sfdisk_stderr")" \
  "$results_mount_exists" "$controller_results_exists" "$metadata_empty" \
  "$confirmation_token" "$MIN_FREE_BYTES" <<'PY'
import json
import sys

(
    schema,
    status,
    recorded_at,
    machine_id_sha256,
    hostname_sha256,
    root_source,
    root_disk,
    root_total,
    root_used,
    root_available,
    root_gate,
    root_df_sha,
    lsblk_sha,
    findmnt_sha,
    pvs_sha,
    swapon_sha,
    mdstat_sha,
    fstab_sha,
    device,
    major_minor,
    size,
    model_sha,
    read_only,
    removable,
    children,
    mounts,
    holders,
    slaves,
    swaps,
    lvm,
    md,
    fstab_refs,
    open_refs,
    wipefs_count,
    wipefs_sha,
    blkid_rc,
    blkid_count,
    blkid_sha,
    sfdisk_rc,
    sfdisk_bytes,
    sfdisk_no_table,
    sfdisk_stdout_sha,
    sfdisk_stderr_sha,
    mount_exists,
    projection_exists,
    metadata_empty,
    confirmation_token,
    min_free,
) = sys.argv[1:]


def integer(value: str) -> int:
    return int(value)


def boolean(value: str) -> bool:
    if value not in {"true", "false"}:
        raise ValueError(value)
    return value == "true"


payload = {
    "schema_version": schema,
    "status": status,
    "recorded_at_utc": recorded_at,
    "audit_mode": "strictly_read_only",
    "destructive_operation_performed": False,
    "secret_material_recorded": False,
    "host_identity": {
        "machine_id_sha256": machine_id_sha256,
        "hostname_sha256": hostname_sha256,
    },
    "root_filesystem": {
        "source": root_source,
        "root_disk": root_disk,
        "total_bytes": integer(root_total),
        "used_bytes": integer(root_used),
        "available_bytes": integer(root_available),
        "minimum_required_bytes": integer(min_free),
        "threshold_satisfied": boolean(root_gate),
    },
    "candidate_disk": {
        "device": device,
        "major_minor": major_minor,
        "size_bytes": integer(size),
        "model_sha256": model_sha,
        "whole_disk": True,
        "read_only": bool(integer(read_only)),
        "removable": bool(integer(removable)),
        "partition_or_child_count": integer(children),
        "mount_reference_count": integer(mounts),
        "holder_count": integer(holders),
        "slave_count": integer(slaves),
        "swap_reference_count": integer(swaps),
        "lvm_pv_reference_count": integer(lvm),
        "md_reference_count": integer(md),
        "fstab_reference_count": integer(fstab_refs),
        "open_reference_count": integer(open_refs),
        "wipefs_signature_count": integer(wipefs_count),
        "blkid_exit_code": integer(blkid_rc),
        "blkid_field_count": integer(blkid_count),
        "sfdisk_exit_code": integer(sfdisk_rc),
        "sfdisk_stdout_bytes": integer(sfdisk_bytes),
        "sfdisk_no_partition_table": boolean(sfdisk_no_table),
        "metadata_empty_and_unreferenced": boolean(metadata_empty),
        "raw_sector_residual_data_ruled_out": False,
    },
    "target_paths": {
        "mount_point": "/opt/webarena-results",
        "mount_point_preexists": boolean(mount_exists),
        "controller_results_path": "/opt/webarena-controller/current/results",
        "controller_results_path_preexists": boolean(projection_exists),
    },
    "command_output_sha256": {
        "df_root": root_df_sha,
        "lsblk_json": lsblk_sha,
        "findmnt_json": findmnt_sha,
        "pvs_json": pvs_sha,
        "swapon": swapon_sha,
        "proc_mdstat": mdstat_sha,
        "fstab_safe_projection": fstab_sha,
        "candidate_wipefs_no_act": wipefs_sha,
        "candidate_blkid_probe": blkid_sha,
        "candidate_sfdisk_stdout": sfdisk_stdout_sha,
        "candidate_sfdisk_stderr": sfdisk_stderr_sha,
    },
    "destructive_confirmation": {
        "required": True,
        "exact_token": confirmation_token,
        "authorization_observed": False,
    },
    "interpretation": {
        "metadata_empty_means": (
            "no discoverable partition table, filesystem signature, child partition, "
            "mount, swap, LVM, md, fstab, holder, slave, or open-device reference"
        ),
        "does_not_mean": (
            "raw sectors are guaranteed never to have contained data; mkfs.ext4 will "
            "irreversibly overwrite filesystem metadata"
        ),
    },
}
print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
PY

[[ $status == pass ]] || exit 1
