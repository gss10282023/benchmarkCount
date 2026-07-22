#!/usr/bin/env bash
set -euo pipefail

# Start the two independent blind-only monitors for one remaining-849 VPS.
# This script is intentionally limited to control-plane and blind-journal paths.
# It never traverses the sealed raw-result or failed-attempt trees.

usage() {
  printf 'usage: %s {vps1|vps2} [start|health-loop|integrity-loop]\n' "$0" >&2
  exit 2
}

vps_id=${1:-}
mode=${2:-start}
case "${vps_id}" in
  vps1|vps2) ;;
  *) usage ;;
esac
case "${mode}" in
  start|health-loop|integrity-loop) ;;
  *) usage ;;
esac

base=/srv/agentdojo-full
repo=${base}/repo
python_bin=${repo}/.venv/bin/python
plan=${repo}/experiments/agentdojo_full_v1.2.2_direct/remaining_849/remote/${vps_id}/plan_index.json
runtime_root=${base}/runtime-state/agentdojo_remaining_849_v1.2.2_direct_${vps_id}
blind_root=${base}/blind-monitor/agentdojo_remaining_849_v1.2.2_direct_${vps_id}
watch_root=/home/benchmark/agentdojo-remaining-849-watchers/${vps_id}
state_root=${watch_root}/state
log_root=${watch_root}/logs
issue_ledger=${watch_root}/remaining-849-monitor-issues.v1.jsonl
pause_request=${runtime_root}/remaining-849-pause-request.v1.json
controller_identity=${runtime_root}/remaining-849-controller-identity.v1.json
script_path=$(readlink -f "$0")

if [[ "${mode}" == start ]]; then
  if [[ "$(id -un)" != benchmark ]]; then
    printf 'blind watchers must be started as benchmark\n' >&2
    exit 3
  fi
  test -x "${python_bin}"
  test -f "${repo}/src/evidence_system/cli/agentdojo_remaining_849_monitor.py"
  install -d -m 0700 "${watch_root}" "${state_root}" "${log_root}"

  health_session=remaining849-${vps_id}-health
  integrity_session=remaining849-${vps_id}-integrity
  if ! tmux has-session -t "${health_session}" 2>/dev/null; then
    tmux new-session -d -s "${health_session}" \
      "${script_path} ${vps_id} health-loop"
  fi
  if ! tmux has-session -t "${integrity_session}" 2>/dev/null; then
    tmux new-session -d -s "${integrity_session}" \
      "${script_path} ${vps_id} integrity-loop"
  fi
  tmux display-message -p -t "${health_session}" \
    '#{session_name} #{session_attached} #{session_windows}'
  tmux display-message -p -t "${integrity_session}" \
    '#{session_name} #{session_attached} #{session_windows}'
  exit 0
fi

# Starting the tmux sessions before namespace publication is safe: each child
# remains in this metadata-only readiness loop and does not invoke the monitor
# until its required immutable/control paths exist.
while [[ ! -r "${plan}" || ! -d "${runtime_root}" || ! -d "${blind_root}" ]]; do
  sleep 2
done

common=(
  --campaign-plan-index "${plan}"
  --blind-root "${blind_root}"
  --runtime-root "${runtime_root}"
  --issue-ledger "${issue_ledger}"
  --pause-request "${pause_request}"
  --vps-id "${vps_id}"
  --poll-interval 5
)

if [[ "${mode}" == health-loop ]]; then
  while [[ ! -r "${controller_identity}" ]]; do
    sleep 2
  done
  exec env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="${repo}/src" \
    "${python_bin}" \
    -m evidence_system.cli.agentdojo_remaining_849_monitor health-watch \
    "${common[@]}" \
    --controller-identity "${controller_identity}" \
    --state-output "${state_root}/health-state.v1.json" \
    >>"${log_root}/health-snapshots.v1.jsonl" 2>&1
fi

exec env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="${repo}/src" \
  "${python_bin}" \
  -m evidence_system.cli.agentdojo_remaining_849_monitor integrity-watch \
  "${common[@]}" \
  --state-output "${state_root}/integrity-state.v1.json" \
  >>"${log_root}/integrity-snapshots.v1.jsonl" 2>&1
