#!/usr/bin/env bash
set -euo pipefail

launch_env=/etc/webarena-controller/launch.env
if [[ ! -f $launch_env || -L $launch_env ]]; then
  echo "WebArena launch authorization is absent or unsafe." >&2
  exit 2
fi
if [[ $(stat -c '%a' "$launch_env") != 600 ]]; then
  echo "WebArena launch authorization permissions must be 0600." >&2
  exit 2
fi

expected_recovery=27266a3f05b7d34c88a5ca884653852ee78c2bd095e0749f955318472e569521
if [[ ${WEBARENA_PAID_CONFIRMATION:-} != RUN-2436-PAID-FULL ]]; then
  echo "Exact paid confirmation is missing." >&2
  exit 2
fi
if [[ ${WEBARENA_RECOVERY_CONFIRMATION:-} != CLEAR-WV-FULL-${expected_recovery} ]]; then
  echo "Exact circuit-recovery confirmation is missing." >&2
  exit 2
fi

exec 9>/run/webarena-controller/controller.lock
if ! flock -n 9; then
  echo "Another WebArena controller already holds the host lock." >&2
  exit 2
fi

cd /opt/webarena-controller/app
export PYTHONPATH=/opt/webarena-controller/app/src
exec /opt/webarena-controller/venv/bin/python \
  scripts/run_webarena_verified_full.py \
  --execute \
  --mode full \
  --ssh-key-path /srv/webarena-controller/secrets/id_ed25519 \
  --confirm-paid-full "$WEBARENA_PAID_CONFIRMATION" \
  --confirm-circuit-recovery "$WEBARENA_RECOVERY_CONFIRMATION" \
  --json
