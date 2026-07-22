# Minimal case-checklist pipeline for NeurIPS ED track

This package keeps the method surface small on purpose.

What stays **inside** the checklist YAML:
- the native benchmark claim,
- the official checker/oracle that defines it,
- the minimal decisive post-run artifacts,
- the native S/F/U decision rules,
- optional stronger-measurement conditions.

What stays **outside** the checklist YAML:
- prompt hashes,
- model billing/costs,
- reviewer bookkeeping,
- manifest locks/hashes,
- run metadata that is not needed to interpret evidence.

That split is deliberate: the checklist should read like a compact, source-grounded statement of what evidence would decide the benchmark's own claim.

## Files

- `templates/case_checklist.template.yaml` — final YAML shape
- `schemas/case_checklist.schema.json` — schema for the final checklist YAML/JSON
- `checklist_guardrails.py` — deterministic fail-closed lint for drafted checklists
- `prompts/draft_case_checklist.prompt.md` — drafter prompt
- `scripts/draft_case_checklist.py` — drafts through Codex CLI, OpenAI, or OpenRouter and writes YAML
- `scripts/checklist_validator.py` — validates a checklist with schema checks plus deterministic lint
- `locks/cases.jsonl` — external case locks for case packet/checklist/prompt/schema drift
- `scripts/update_case_locks.py` — upserts a minimal external lock entry for a case
- `schemas/evidence_score.schema.json` — schema for scorer output
- `prompts/score_evidence_with_codex.prompt.md` — Codex scorer prompt
- `scripts/score_evidence_with_codex.py` — calls Codex CLI in read-only mode
- `scripts/score_evidence_with_claude.py` — opt-in Claude Code CLI scorer using login auth
- `examples/*.yaml` — illustrative filled checklist from the uploaded case packet

## Usage

Install the minimal Python dependencies:

```bash
python -m pip install -r requirements.txt
```

Reviewer-friendly entry points:

```bash
make validate
make smoke
```

`make smoke` is offline. It does not call OpenRouter or Codex.
If you want to run against a specific interpreter or virtualenv, use `make ... PYTHON=/path/to/python`.

Draft a checklist from a case packet:

Using an existing Codex CLI login (no API key required):

```bash
codex login
make draft-codex \
  CASE_PACKET=/path/to/case_packet.md \
  OUTPUT=/path/to/case_checklist.yaml
```

The Codex path defaults to `gpt-5.4`, `reasoning-effort=xhigh`, output verbosity
`medium`, a read-only ephemeral session, and a 30-minute subprocess timeout. It uses
the existing Codex login under `CODEX_HOME`; `--ignore-user-config` keeps unrelated
local defaults from changing the experiment while preserving login authentication.

Using OpenRouter instead:

```bash
export OPENROUTER_DRAFT_API_KEY=...
make draft \
  CASE_PACKET=/path/to/case_packet.md \
  OUTPUT=/path/to/case_checklist.yaml
```

For OpenRouter, `draft` prefers `OPENROUTER_DRAFT_API_KEY` when it is set, and
otherwise falls back to `OPENROUTER_API_KEY`. This lets you rotate the drafter key
without changing other flows.

API providers default to `openai/gpt-5.4`, `reasoning-effort=xhigh`, output verbosity
`medium`, and `max_output_tokens=12000`. You can override them from `make`, for
example:

```bash
make draft \
  CASE_PACKET=/path/to/case_packet.md \
  OUTPUT=/path/to/case_checklist.yaml \
  MAX_OUTPUT_TOKENS=16000
```

Each draft now also saves sidecar files next to the YAML:
- `api_response.json` — full raw provider response
- `llm_call.json` — normalized call metadata, token usage, and provider-reported cost
- `reasoning_summary.txt` — provider-exposed reasoning summary text when available

For larger benchmark families such as AppWorld, use the generic batch runner. It can
split oversized case packets into a lower-concurrency lane while keeping smaller cases
highly parallel:

```bash
python scripts/run_draft_batch.py \
  --case-packet-root experiments/case_packets/appworld \
  --output-root results/full/appworld/drafts \
  --provider codex \
  --model gpt-5.4 \
  --reasoning-effort xhigh \
  --max-parallel 8 \
  --large-max-parallel 2 \
  --large-case-threshold-bytes 100000 \
  --codex-timeout-seconds 1800 \
  --large-codex-timeout-seconds 3600 \
  --quality-check none
```

Each worker launches one independent `codex exec` process using the same Codex login.
`--max-parallel` controls normal cases; `--large-max-parallel` separately limits oversized
packets. Set these to values allowed by the authenticated account/service. For Codex,
`--token-budgets` determines the retry count but is not an output-token cap, because
`codex exec` does not expose the Responses API `max_output_tokens` flag.

The public minimal package uses the shared `draft_case_checklist.prompt.md` directly.
Benchmark-specific prompt supplements are not part of the public prompt directory and
must not be supplied by the benchmark workflows in this package.

`draft_case_checklist.py` now fails closed if the drafted checklist passes schema validation
but still violates deterministic guardrails, for example by depending on hidden internal state,
extra judges/model calls, or answer-key-style ordered action sequences that are not grounded in
retained post-run artifacts.

You can also validate any saved checklist offline:

```bash
python scripts/checklist_validator.py /path/to/case_checklist.yaml
```

Freeze a drafted case externally without adding hashes back into the checklist YAML:

```bash
python scripts/update_case_locks.py \
  --case-packet /path/to/case_packet.md \
  --checklist /path/to/case_checklist.yaml
```

This updates `locks/cases.jsonl` with:
- the case packet hash,
- the locked checklist hash,
- the draft and score prompt paths plus hashes,
- the checklist and score schema paths plus hashes.

Score stored run artifacts against the locked checklist:

```bash
# Codex CLI must already be installed and authenticated.
make score \
  CHECKLIST=/path/to/case_checklist.yaml \
  EVIDENCE_DIR=/path/to/run_artifacts \
  OUT_PREFIX=/path/to/results/case_score
```

The Codex scorer defaults to `gpt-5.4`, `reasoning-effort=xhigh`, the default
service tier (fast mode is not enabled), and a read-only sandbox. It runs with
`--ephemeral --ignore-user-config`, so
the active `CODEX_HOME` login is preserved while personal Codex configuration,
plugins, and MCP settings do not change the experiment.

An opt-in secondary scorer is available through an existing Claude Code login:

```bash
claude login
make score-claude \
  CHECKLIST=/path/to/case_checklist.yaml \
  EVIDENCE_DIR=/path/to/run_artifacts \
  OUT_PREFIX=/path/to/results/case_score
```

This secondary scorer defaults to Claude Code's `sonnet` alias (the current
Sonnet 5 family) with `effort=high`. It uses `--safe-mode`, does not persist a
session, and exposes only `Read`, `Glob`, and `Grep`; therefore it retains the
Claude Code login state without loading personal/project customizations or
allowing score-time writes. API-key and third-party-provider auth environment
variables are removed from the scorer subprocess so it uses the Claude Code
login rather than metered API credentials. It is never selected implicitly: `make score`
continues to use Codex, and the generic batch runner requires the explicit
flag `--scorer claude-code`. Without that flag, its defaults remain Codex
`gpt-5.4` plus `xhigh`.

For an explicitly requested Claude batch:

```bash
python scripts/run_score_batch.py \
  --scorer claude-code \
  --task-root /path/to/tasks \
  --output-root /path/to/outputs \
  --state-root /path/to/state
```

`OUT_PREFIX` is optional. If omitted, the scorer writes a standardized bundle under:

```text
results/scores/<phase>/<domain>/<run_dir_name>/<checklist_key>/<scorer_tag>/
```

with `score.json`, `score.yaml`, `score_manifest.json`, canonical Codex logs, and
per-attempt files such as `score.attempt_01.codex.stdout.log` and
`score.attempt_01.model_output.json`.
It stages a copied evidence workspace, writes `evidence_index.txt` for file discovery,
resolves the released evaluator label locally from saved native artifacts (or from `--native-label-path`),
preserves AgentDojo paired released-evaluator arm fields under
`released_evaluator_label.agentdojo_arms` when available, and fails closed if Codex
tries to use `native_label` / `native_score` summary scalars as decisive evidence for
the native or stronger verdict.

The formal batch scorer inherits `SCORE_MODEL` and `SCORE_REASONING_EFFORT` from
`.env`; the supplied defaults are `gpt-5.4` and `xhigh`. A pending-only resume
inherits the model and reasoning effort recorded in its source `task_plan.json` unless
explicitly overridden, preventing accidental mixed-model batches.

If you want to keep the same scorer pipeline but route GPT-5.4 calls through OpenRouter
instead of Codex auth, use the OpenRouter wrapper:

```bash
export OPENROUTER_SCORE_API_KEY=...
python scripts/run_openrouter_score_batch.py \
  --draft-root results/full/agentdojo/drafts \
  --evidence-root results/full/agentdojo \
  --batch-root results/scores/full/agentdojo/_batch_runs \
  --run-dir-prefix full-agentdojo- \
  --batch-label agentdojo-openrouter \
  --tasks-per-key 100 \
  --per-key-concurrency 4
```

By default this wrapper:
- fans one shared OpenRouter key out to `SCORE_OPENROUTER_API_KEY_{1,2,3}`,
- sets `SCORE_OPENAI_BASE_URL=https://openrouter.ai/api/v1`,
- defaults the score model to `openai/gpt-5.4` with `reasoning-effort=xhigh`,
- writes final score bundles under `results/scores_openrouter/...`,
- keeps the same checklist/evidence pairing, validators, and output format.

If you want different keys per slot, set all three of `SCORE_OPENROUTER_API_KEY_1`,
`SCORE_OPENROUTER_API_KEY_2`, and `SCORE_OPENROUTER_API_KEY_3` yourself before launching.
If you want a different output tree, pass `--score-output-root /your/path`.
