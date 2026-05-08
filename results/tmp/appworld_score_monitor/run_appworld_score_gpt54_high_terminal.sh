#!/bin/zsh
set +e
cd /Users/gss/Downloads/revised_agent_benchmark_paper_package || exit 1

set -a
source .env
set +a

if [[ -z "${super:-}" ]]; then
  echo "missing .env variable: super" >&2
  exit 2
fi

for slot in 1 2 3 4; do
  export SCORE_OPENROUTER_API_KEY_${slot}="$super"
done

export SCORE_OPENAI_BASE_URL="https://openrouter.ai/api/v1"
export SCORE_MODEL="gpt-5.4"
export SCORE_REASONING_EFFORT="high"
export PYTHONUNBUFFERED=1

.venv/bin/python neurips_ed_track_minimal/scripts/run_agentdojo_score_batch.py \
  --draft-root results/full/appworld/drafts \
  --evidence-root results/full/appworld \
  --batch-root results/scores_openrouter/full/appworld/_batch_runs \
  --score-output-root results/scores_openrouter \
  --run-dir-prefix full-appworld- \
  --batch-label appworld_openrouter_super_terminal8_high \
  --tasks-per-key 75 \
  --slot-count 4 \
  --per-key-concurrency 2 \
  --model gpt-5.4 \
  --reasoning-effort high \
  --sandbox read-only \
  --max-attempts 2 \
  --codex-timeout-seconds 600 \
  --max-run-attempts 2

status=$?
echo "EXIT:$status"
exit $status
