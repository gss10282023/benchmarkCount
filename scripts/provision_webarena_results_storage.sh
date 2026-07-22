#!/usr/bin/env bash
# Destructive, fail-closed provisioning of a metadata-empty whole disk for
# WebArena result artifacts.  Never run this script without the disk owner's
# explicit approval of the exact confirmation token printed by the read-only
# audit script.

set -euo pipefail
export LC_ALL=C
umask 077

readonly SCHEMA_VERSION="webarena_verified_results_storage_provision/v1"
readonly MIN_FREE_BYTES=350000000000
readonly MOUNT_POINT="/opt/webarena-results"
readonly CONTROLLER_RESULTS_PATH="/opt/webarena-controller/current/results"
readonly RESULTS_SUBDIRECTORY="controller-results"
readonly DEFAULT_RECEIPT_PATH="/opt/webarena-verified/v1.2.3/receipts/storage_provisioning.json"

usage() {
  cat >&2 <<'EOF'
usage: provision_webarena_results_storage.sh --execute \
  --device /dev/DEVICE \
  --expected-size-bytes BYTES \
  --expected-machine-id-sha256 SHA256 \
  --confirmation-token 'ERASE_WEBARENA_RESULTS:SHA256:/dev/DEVICE:BYTES' \
  [--receipt-path /absolute/path/to/receipt.json]

WARNING: this command runs mkfs.ext4 on the entire named disk.  It is
irreversible.  The token must exactly bind the audited machine, device and size.
The command refuses any disk with a signature, partition, mount, swap, LVM, md,
fstab, holder, slave, or open-device reference.
EOF
}

die() {
  echo "storage provisioning refused: $*" >&2
  exit 2
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "required command is missing: $1"
}

execute=false
device_arg=""
expected_size_bytes=""
expected_machine_id_sha256=""
confirmation_token=""
receipt_path=$DEFAULT_RECEIPT_PATH
while (($#)); do
  case "$1" in
    --execute)
      execute=true
      shift
      ;;
    --device)
      (($# >= 2)) || die "--device requires a value"
      device_arg=$2
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
    --confirmation-token)
      (($# >= 2)) || die "--confirmation-token requires a value"
      confirmation_token=$2
      shift 2
      ;;
    --receipt-path)
      (($# >= 2)) || die "--receipt-path requires a value"
      receipt_path=$2
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

[[ $execute == true ]] || die "--execute is required"
((EUID == 0)) || die "must run as root"
[[ $device_arg =~ ^/dev/[[:alnum:]_.-]+$ ]] || die "invalid device"
[[ $expected_size_bytes =~ ^[1-9][0-9]+$ ]] || die "invalid expected size"
[[ $expected_machine_id_sha256 =~ ^[0-9a-f]{64}$ ]] || die "invalid machine-id digest"
[[ $receipt_path == /* && $receipt_path == *.json ]] || die "receipt path must be absolute JSON"

for command_name in \
  awk basename blkid blockdev chmod chown date df dirname find findmnt findfs \
  flock fuser grep head install ln lsblk mkfs.ext4 mktemp mount mountpoint \
  mv pvs python3 readlink rm sed sfdisk sha256sum swapon tail tr wipefs; do
  require_command "$command_name"
done

exec 9>/run/lock/webarena-results-storage-provision.lock
flock -n 9 || die "another storage provisioning process holds the lock"

actual_machine_id_sha256=$(sha256sum /etc/machine-id | awk '{print $1}')
[[ $actual_machine_id_sha256 == "$expected_machine_id_sha256" ]] || \
  die "machine-id digest differs from the audited host"
expected_token="ERASE_WEBARENA_RESULTS:${actual_machine_id_sha256}:${device_arg}:${expected_size_bytes}"
[[ $confirmation_token == "$expected_token" ]] || die "exact confirmation token mismatch"

[[ -b $device_arg ]] || die "device is not a block device"
device=$(readlink -f -- "$device_arg")
[[ $device == "$device_arg" ]] || die "device must be a canonical /dev path"
[[ $(lsblk -dn -o TYPE -- "$device" | tr -d '[:space:]') == disk ]] || \
  die "device is not a whole disk"
[[ $(blockdev --getsize64 "$device") == "$expected_size_bytes" ]] || \
  die "device size differs from the audited size"
[[ $(blockdev --getro "$device") == 0 ]] || die "device is read-only"
[[ $(lsblk -dn -o RM -- "$device" | tr -d '[:space:]') == 0 ]] || \
  die "device is removable"

root_source=$(findmnt -n -o SOURCE /)
root_parent=$(lsblk -no PKNAME -- "$root_source" | head -1)
[[ -n $root_parent ]] || die "cannot identify the root disk"
root_disk="/dev/$(basename "$root_parent")"
[[ $device != "$root_disk" ]] || die "refusing the root disk"
if lsblk -srno PATH -- "$root_source" | grep -Fxq -- "$device"; then
  die "refusing an ancestor of the root filesystem"
fi

children=$(lsblk -nr -o PATH -- "$device" | tail -n +2)
[[ -z $children ]] || die "device has partitions or child block devices"
mount_matches=$(findmnt -rn -S "$device" 2>/dev/null || true)
[[ -z $mount_matches ]] || die "device is mounted"
kname=$(basename "$device")
[[ -z $(find "/sys/class/block/$kname/holders" -mindepth 1 -maxdepth 1 \
  2>/dev/null || true) ]] || die "device has block holders"
[[ -z $(find "/sys/class/block/$kname/slaves" -mindepth 1 -maxdepth 1 \
  2>/dev/null || true) ]] || die "device has block slaves"
if swapon --show --noheadings --output NAME | grep -Fxq -- "$device"; then
  die "device is active swap"
fi
if pvs --noheadings -o pv_name 2>/dev/null | awk '{$1=$1; print}' | \
  grep -Fxq -- "$device"; then
  die "device is an LVM physical volume"
fi
if grep -Eq "(^|[[:space:]])${kname}([[:space:]\[])" /proc/mdstat; then
  die "device is referenced by md"
fi
set +e
fuser -s "$device" 2>/dev/null
fuser_rc=$?
set -e
[[ $fuser_rc == 1 ]] || die "device is open or fuser could not prove it unused"

while read -r source target _rest; do
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
  [[ $resolved != "$device" ]] || die "device is referenced by fstab"
  [[ $target != "$MOUNT_POINT" ]] || die "target mount point already exists in fstab"
done < <(sed -E 's/[[:space:]]+#.*$//' /etc/fstab | \
  awk 'NF && $1 !~ /^#/ {print $1, $2, $3, $4}')

wipefs_raw=$(wipefs --no-act --noheadings \
  --output TYPE,UUID,LABEL,OFFSET -- "$device")
[[ -z $wipefs_raw ]] || die "device contains a filesystem or partition signature"
set +e
blkid_raw=$(blkid -p -o export -- "$device" 2>/dev/null)
blkid_rc=$?
sfdisk_stdout=$(sfdisk --json -- "$device" 2>/dev/null)
sfdisk_rc=$?
sfdisk_stderr=$(sfdisk --json -- "$device" 2>&1 >/dev/null)
set -e
[[ $blkid_rc == 2 && -z $blkid_raw ]] || die "blkid found a signature"
[[ $sfdisk_rc == 1 && -z $sfdisk_stdout && \
   $sfdisk_stderr == *"does not contain a recognized partition table"* ]] || \
  die "sfdisk did not prove the absence of a partition table"

[[ ! -e $MOUNT_POINT && ! -L $MOUNT_POINT ]] || die "$MOUNT_POINT already exists"
[[ -d $(dirname "$MOUNT_POINT") ]] || die "mount-point parent is absent"
[[ ! -e $CONTROLLER_RESULTS_PATH && ! -L $CONTROLLER_RESULTS_PATH ]] || \
  die "$CONTROLLER_RESULTS_PATH already exists"
[[ -d $(dirname "$CONTROLLER_RESULTS_PATH") ]] || \
  die "controller results parent is absent"
receipt_parent=$(dirname "$receipt_path")
[[ -d $(dirname "$receipt_parent") ]] || die "receipt grandparent is absent"

# Destructive boundary: every check above must pass before this line.
mkfs.ext4 -F -L webarena-results -- "$device"
filesystem_uuid=$(blkid -s UUID -o value -- "$device")
[[ $filesystem_uuid =~ ^[0-9a-fA-F-]{36}$ ]] || die "mkfs did not produce an ext4 UUID"
[[ $(blkid -s TYPE -o value -- "$device") == ext4 ]] || die "filesystem is not ext4"

install -d -m 0700 "$MOUNT_POINT"
fstab_line="UUID=${filesystem_uuid} ${MOUNT_POINT} ext4 defaults,nodev,nosuid 0 2"
fstab_tmp=$(mktemp /etc/fstab.webarena-results.XXXXXX)
install -m 0600 /etc/fstab "$fstab_tmp"
printf '%s\n' "$fstab_line" >>"$fstab_tmp"
findmnt --verify --tab-file "$fstab_tmp" >/dev/null
chmod 0644 "$fstab_tmp"
chown root:root "$fstab_tmp"
mv "$fstab_tmp" /etc/fstab
mount "$MOUNT_POINT"
mountpoint -q "$MOUNT_POINT" || die "results filesystem is not mounted"
[[ $(findmnt -n -o FSTYPE -T "$MOUNT_POINT") == ext4 ]] || die "mounted filesystem is not ext4"
chmod 0700 "$MOUNT_POINT"
install -d -m 0700 "$MOUNT_POINT/$RESULTS_SUBDIRECTORY"
ln -s "$MOUNT_POINT/$RESULTS_SUBDIRECTORY" "$CONTROLLER_RESULTS_PATH"
[[ $(readlink -f -- "$CONTROLLER_RESULTS_PATH") == \
   "$MOUNT_POINT/$RESULTS_SUBDIRECTORY" ]] || die "results projection is incorrect"

available_bytes=$(df -B1 --output=avail "$CONTROLLER_RESULTS_PATH" | \
  tail -1 | tr -d '[:space:]')
((available_bytes >= MIN_FREE_BYTES)) || die "mounted results disk is below the 350 GB gate"
mount_source=$(findmnt -n -o SOURCE -T "$CONTROLLER_RESULTS_PATH")
fstab_sha256=$(sha256sum /etc/fstab | awk '{print $1}')
script_sha256=$(sha256sum "$(readlink -f -- "$0")" | awk '{print $1}')
recorded_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)

install -d -m 0700 "$receipt_parent"
receipt_tmp=$(mktemp "${receipt_path}.tmp.XXXXXX")
python3 - "$receipt_tmp" "$SCHEMA_VERSION" "$recorded_at_utc" \
  "$actual_machine_id_sha256" "$device" "$expected_size_bytes" \
  "$filesystem_uuid" "$mount_source" "$available_bytes" "$MIN_FREE_BYTES" \
  "$fstab_sha256" "$script_sha256" <<'PY'
import json
import os
import sys

(
    output,
    schema,
    recorded_at,
    machine_id_sha256,
    device,
    size_bytes,
    filesystem_uuid,
    mount_source,
    available_bytes,
    minimum_bytes,
    fstab_sha256,
    script_sha256,
) = sys.argv[1:]
payload = {
    "schema_version": schema,
    "status": "pass",
    "recorded_at_utc": recorded_at,
    "host_identity": {"machine_id_sha256": machine_id_sha256},
    "destructive_confirmation": {
        "required": True,
        "exact_token_validated": True,
        "token_or_token_hash_recorded": False,
    },
    "filesystem": {
        "device": device,
        "device_size_bytes": int(size_bytes),
        "type": "ext4",
        "uuid": filesystem_uuid,
        "mount_source": mount_source,
        "mount_point": "/opt/webarena-results",
        "mount_point_mode": "0700",
        "fstab_uses_uuid": True,
        "fstab_sha256": fstab_sha256,
    },
    "results_path_projection": {
        "controller_path": "/opt/webarena-controller/current/results",
        "storage_path": "/opt/webarena-results/controller-results",
        "status": "pass",
    },
    "capacity_gate": {
        "measurement_method": "df_B1_available_bytes_after_mount",
        "available_bytes": int(available_bytes),
        "minimum_required_bytes": int(minimum_bytes),
        "threshold_satisfied": int(available_bytes) >= int(minimum_bytes),
    },
    "budget_projection_scope": {
        "pilot_storage_measured": False,
        "full_2436_storage_projected": False,
        "formal_storage_readiness_acceptance_satisfied": False,
        "reason": "requires measured pilot artifacts and full-run byte projection",
    },
    "provision_script_sha256": script_sha256,
    "secret_material_recorded": False,
}
with open(output, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
    handle.write("\n")
os.chmod(output, 0o600)
PY
install -m 0600 "$receipt_tmp" "$receipt_path"
rm -f "$receipt_tmp"
receipt_sha256=$(sha256sum "$receipt_path" | awk '{print $1}')
printf '%s  %s\n' "$receipt_sha256" "$(basename "$receipt_path")" \
  >"${receipt_path}.sha256"
chmod 0600 "${receipt_path}.sha256"

echo "storage-provisioning-status=pass"
echo "receipt=$receipt_path"
echo "receipt-sha256=$receipt_sha256"
