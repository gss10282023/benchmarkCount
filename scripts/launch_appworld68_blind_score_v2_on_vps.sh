#!/usr/bin/env bash
set -euo pipefail

JOB=/srv/neurips-score/jobs/appworld68_tn_score_gpt54_high_default_c34_20260720_v2_runtime_semantics
APP="$JOB/app/neurips_ed_track_minimal"
TASKS="$JOB/input_package/public_score_job/tasks"
RESULTS="$JOB/results"
STATE="$JOB/state"
AUTH="$JOB/runtime/auth_source"
PROVENANCE="$JOB/provenance"

# The user explicitly requested that the other scoring work be paused.  Launch
# only when its processes are frozen/stopped and no external Codex process is
# runnable.  Paused processes are preserved for later continuation.
if [[ $(systemctl show neurips-score-aw75-score-gpt54-high-c32-v2-20260720.service -p FreezerState --value) != frozen ]]; then
  echo "AndroidWorld score service is not frozen" >&2
  exit 2
fi
if [[ $(ps -p 2914154 -o stat= | tr -d ' ' | cut -c1) != T ]]; then
  echo "AgentDojo audit controller is not paused" >&2
  exit 2
fi

if [[ -e "$RESULTS" ]] || [[ -e "$STATE" ]]; then
  echo "formal results/state already exist; refusing to mix runs" >&2
  exit 2
fi
if [[ $(find "$TASKS" -mindepth 1 -maxdepth 1 -type d | wc -l) -ne 204 ]]; then
  echo "formal task denominator differs from 204" >&2
  exit 2
fi
RUNNABLE_EXTERNAL_CODEX=$(ps -eo stat,args | awk '$1 !~ /^T/ && /[c]odex exec/ {count++} END {print count+0}')
PAUSED_EXTERNAL_CODEX=$(ps -eo stat,args | awk '$1 ~ /^T/ && /[c]odex exec/ {count++} END {print count+0}')
if [[ "$RUNNABLE_EXTERNAL_CODEX" -ne 0 ]]; then
  echo "runnable external Codex process appeared during prelaunch" >&2
  exit 2
fi

export CODEX_HOME="$AUTH"
export SCORE_BLIND_OS_USER=appworld68-score-blind
codex login status 2>&1 | grep -F 'Logged in using ChatGPT' >/dev/null
sudo -u appworld68-score-blind test ! -r "$AUTH/auth.json"

{
  echo "started_preflight_at=$(date -u +%FT%TZ)"
  echo "hostname=$(hostname)"
  echo "runnable_external_codex_exec=$RUNNABLE_EXTERNAL_CODEX"
  echo "paused_external_codex_exec=$PAUSED_EXTERNAL_CODEX"
  echo "agentdojo_controller_state=paused"
  echo "androidworld_service_freezer_state=frozen"
  echo "task_count=204"
  echo "results_present=false"
  echo "state_present=false"
  echo "scorer_sha256=$(sha256sum "$APP/scripts/score_evidence_blind_with_codex.py" | awk '{print $1}')"
  echo "native_prompt_sha256=$(sha256sum "$APP/prompts/score_evidence_native_blind.prompt.md" | awk '{print $1}')"
  echo "stronger_prompt_sha256=$(sha256sum "$APP/prompts/score_evidence_stronger_blind.prompt.md" | awk '{print $1}')"
  echo "package_manifest_sha256=$(sha256sum "$JOB/input_package/public_score_job/package_manifest.json" | awk '{print $1}')"
  echo "dry_run_plan_sha256=$(sha256sum "$PROVENANCE/full_dry_run_plan.json" | awk '{print $1}')"
  echo "model=gpt-5.4"
  echo "reasoning_effort=high"
  echo "service_tier=default"
  echo "fast_mode=false"
  echo "max_parallel=34"
  echo "auth_mode=codex_login"
} > "$PROVENANCE/prelaunch_snapshot.txt"

exec python3 "$APP/scripts/run_score_batch.py" \
  --task-root "$TASKS" \
  --output-root "$RESULTS" \
  --state-root "$STATE" \
  --blind-mode \
  --scorer codex \
  --model gpt-5.4 \
  --reasoning-effort high \
  --sandbox read-only \
  --service-tier default \
  --max-parallel 34 \
  --max-attempts 3 \
  --codex-timeout-seconds 1800 \
  --max-run-attempts 1 \
  --max-input-files 20000 \
  --max-input-bytes 200000000 \
  --max-single-file-bytes 20000000 \
  --min-free-bytes 1000000000
