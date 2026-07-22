#!/usr/bin/env bash
set -euo pipefail

job_root=/srv/neurips-score/jobs/aw75_score_gpt54_high_c32_v2_20260720
task_root=$job_root/tasks
output_root=$job_root/results
state_root=$job_root/state

export HOME=/srv/neurips-draft/home
export CODEX_HOME=/srv/neurips-draft/home/.codex
export SCORE_CODEX_HOME_ROOT=/srv/neurips-score/runtime/codex_homes
export TMPDIR=/srv/neurips-score/runtime/tmp
export PYTHONPYCACHEPREFIX=/srv/neurips-score/runtime/pycache
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export PYTHONUNBUFFERED=1

while :; do
  active_codex=$(ps -eo stat=,args= | awk '$1 !~ /^T/ && /vendor.*codex exec/ {count++} END {print count+0}')
  if (( active_codex <= 4 )); then
    break
  fi
  printf 'waiting_for_capacity active_codex=%s\n' "$active_codex"
  sleep 30
done

sandbox_probe=$(mktemp -d "$TMPDIR/aw75_score_sandbox_probe.XXXXXX")
trap 'rm -rf "$sandbox_probe"' EXIT
install -m 0444 /dev/null "$sandbox_probe/readable"
codex sandbox -P :read-only -C "$sandbox_probe" -- /bin/sh -c \
  'test -r readable && ! touch should_not_write 2>/dev/null'
rm -rf "$sandbox_probe"
trap - EXIT

exec /opt/neurips-draft/venv/bin/python \
  /opt/neurips-draft/app/neurips_ed_track_minimal/scripts/run_score_batch.py \
  --task-root "$task_root" \
  --output-root "$output_root" \
  --state-root "$state_root" \
  --model gpt-5.4 \
  --reasoning-effort high \
  --sandbox read-only \
  --service-tier default \
  --max-parallel 32 \
  --codex-timeout-seconds 1800 \
  --max-attempts 2 \
  --max-run-attempts 2 \
  --max-input-files 200000 \
  --max-input-bytes 107374182400 \
  --max-single-file-bytes 5368709120 \
  --min-free-bytes 21474836480
