#!/bin/bash
set -euo pipefail

cd <REPO_ROOT>

set -a
[ -f .env ] && . ./.env
set +a

manifest='experiments/appendix/androidworld_remaining80_manifest.json'
source_bundle='experiments/evidence_contracts/source_bundles/androidworld_remaining80_source_bundle.json'
contracts_dir='experiments/evidence_contracts/locked'
infra_config='configs/infra.yaml'
agents_config='configs/agents.yaml'
jobs_dir='results/jobs/full'
start_b="${1:-${START_B:-60}}"
end_b="${2:-${END_B:-79}}"
mode="${3:-${RUN_MODE:-full_chain}}"
start_a="${START_A:-1}"
end_a="${END_A:-1}"
start_c="${START_C:-1}"
end_c="${END_C:-79}"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

case_id_at() {
  jq -r ".domains[0].case_units[$(($1-1))].case_unit_id" "$manifest"
}

case_root() {
  printf 'results/full/androidworld/full-androidworld-%s-%s' "$1" "$2"
}

classify() {
  local root="$1"
  local raw="$root/adapter/raw_run.json"
  local sum="$root/adapter/native_run/run_summary.json"
  local worker_sum="$root/worker_output/run_summary.json"

  if [ ! -f "$raw" ]; then
    echo missing
    return
  fi

  local run_state failure success_flag native_label
  run_state=$(jq -r '.status' "$raw")
  failure=$(jq -r '.appendix_failure_class // "none"' "$raw")
  native_label=$(jq -r '.native_label // "null"' "$raw")
  success_flag="null"
  if [ -f "$worker_sum" ]; then
    success_flag=$(jq -r '.success // "null"' "$worker_sum")
  fi
  if [ "$success_flag" = 'null' ] && [ -f "$sum" ]; then
    success_flag=$(jq -r '.success // "null"' "$sum")
  fi

  if [ "$run_state" = 'COMPLETED' ] && [ "$failure" = 'none' ] && [ "$success_flag" = 'true' ]; then
    echo success
  elif [ "$run_state" = 'COMPLETED' ] && [ "$failure" = 'none' ] && [ "$success_flag" = 'false' ]; then
    echo ordinary_fail
  elif [ "$run_state" = 'COMPLETED' ] && [ "$failure" = 'none' ] && [ "$native_label" = 'success' ]; then
    echo success
  elif [ "$run_state" = 'COMPLETED' ] && [ "$failure" = 'none' ] && [ "$native_label" = 'fail' ]; then
    echo ordinary_fail
  else
    echo unresolved
  fi
}

wait_classify() {
  local root="$1"
  local state=""
  local worker_summary="$root/worker_output/run_summary.json"
  local worker_state=""

  for _ in $(seq 1 180); do
    state=$(classify "$root")
    if [ "$state" = 'success' ] || [ "$state" = 'ordinary_fail' ]; then
      echo "$state"
      return
    fi
    if [ "$state" = 'missing' ] && [ -f "$worker_summary" ]; then
      worker_state=$(jq -r '.status // "unknown"' "$worker_summary" 2>/dev/null || echo unknown)
      if [ "$worker_state" = 'running' ] || [ "$worker_state" = 'started' ]; then
        sleep 2
        continue
      fi
    fi
    if [ "$state" = 'unresolved' ]; then
      sleep 2
      continue
    fi
    sleep 2
  done

  echo "$state"
}

run_one() {
  local agent_id="$1"
  local suffix="$2"
  local idx="$3"
  local cid="$4"
  local root state ts

  root=$(case_root "$cid" "$suffix")
  state=$(classify "$root" || true)

  if [ -d "$root" ] && [ "$state" != 'success' ] && [ "$state" != 'ordinary_fail' ]; then
    ts=$(date '+%Y%m%dT%H%M%S')
    mv "$root" "${root}__retry_archived_${ts}"
    log "ARCHIVE ${suffix} ${idx} ${cid}"
  fi

  log "RUN ${suffix} ${idx} ${cid}"
  PYTHONPATH=src .venv/bin/python -m evidence_system.cli.run_full \
    --domain androidworld \
    --phase full \
    --experiment-type appendix \
    --case-count "$idx" \
    --agent-id "$agent_id" \
    --manifest "$manifest" \
    --source-bundle "$source_bundle" \
    --contracts-dir "$contracts_dir" \
    --infra-config "$infra_config" \
    --agents-config "$agents_config" \
    --jobs-dir "$jobs_dir" \
    --max-workers 1 \
    --json >"/tmp/aw_${suffix}_${idx}.log" 2>&1 || true

  state=$(wait_classify "$root")
  log "RESULT ${suffix} ${idx} ${cid} ${state}"

  if [ "$state" = 'unresolved' ] || [ "$state" = 'missing' ]; then
    log "STOP ${suffix} ${idx} ${cid}"
    exit 0
  fi
}

run_range() {
  local agent_id="$1"
  local suffix="$2"
  local start="$3"
  local end="$4"
  local idx cid root state

  for idx in $(seq "$start" "$end"); do
    cid=$(case_id_at "$idx")
    root=$(case_root "$cid" "$suffix")
    state=$(classify "$root" || true)
    if [ "$state" = 'success' ] || [ "$state" = 'ordinary_fail' ]; then
      log "SKIP ${suffix} ${idx} ${cid} ${state}"
      continue
    fi
    run_one "$agent_id" "$suffix" "$idx" "$cid"
  done

  log "DONE ${suffix} ${start}-${end}"
}

run_range 'Agent B' 'agent_b' "$start_b" "$end_b"
if [ "$mode" != 'b_only' ]; then
  run_range 'Agent A' 'agent_a' "$start_a" "$end_a"
  run_range 'Agent C' 'agent_c' "$start_c" "$end_c"
fi
log 'ALL_DONE'
