# Reproduction Setup Tables (compiled from the current repository)

This document is compiled from your current setup and the repository state:

- Raw input to `draft`: `<REPO_ROOT>/neurips_ed_track_minimal`
- Evidence collection: benchmark-specific adapters running on VPS machines or local machines
- `score`: `<REPO_ROOT>/neurips_ed_track_minimal`

If the final paper reports only the benchmarks you actually ran, remove the unused machine-role rows.

## 1. End-to-end reproduction pipeline

| Stage | Purpose | Package / code | Entry command | Main inputs | Main outputs | Default configuration / model | Runtime requirements |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Raw input -> `draft` | Generate a checklist draft from `case_packet.md` | `neurips_ed_track_minimal` | `make draft CASE_PACKET=... OUTPUT=...` | `case_packet.md` | `checklist.yaml`, `api_response.json`, `llm_call.json`, `reasoning_summary.txt` | `openai/gpt-5.4`, `reasoning-effort=high`, `max_output_tokens=12000`, `temperature=0`, `http_timeout_seconds=180` | Any networked CPU machine; requires Python 3, `requests`, `PyYAML`, `jsonschema`; requires `OPENROUTER_DRAFT_API_KEY` or `OPENROUTER_API_KEY` |
| `draft` validation / locking | Validate schema and guardrails, then freeze the case/checklist mapping | `neurips_ed_track_minimal` | `python scripts/checklist_validator.py ...`; `python scripts/update_case_locks.py --case-packet ... --checklist ...` | `case_packet.md`, `checklist.yaml` | Validated checklist; lock record in `locks/cases.jsonl` | Offline validation; no additional model call | Local CPU machine is sufficient |
| Evidence collection (adapter) | Run the official benchmark or diagnostic runner and save raw evidence without making final S/F/U decisions | `src/evidence_system/adapters/` and `python -m evidence_system.cli.run_domain` | `python -m evidence_system.adapters.<canonical_domain> ...` or wrapped CLI | `job.json`, benchmark installation, `configs/agents.yaml`, `configs/infra.yaml` | `raw_run_record/v1`, `artifact_manifest/v1`, raw artifacts, native evaluator outputs, stdout/stderr, LLM call logs | Agent configuration comes from `configs/agents.yaml`; the adapter itself must not output the final evidence verdict | Routed to the corresponding VPS or local machine by domain; may depend on docker, benchmark assets, network access, and local services |
| `score` | Perform final evidence scoring over saved run artifacts using the locked checklist | `neurips_ed_track_minimal` | `make score CHECKLIST=... EVIDENCE_DIR=... OUT_PREFIX=...` | `checklist.yaml`, `run_artifacts/` | `score.json`, `score.yaml`, `score_manifest.json`, `score.codex.stdout.log`, `score.codex.stderr.log`, `score.codex.events.jsonl`, `score.codex.telemetry.json`, `score.codex.reasoning.txt` | `gpt-5.4`, `reasoning-effort=xhigh`, `sandbox=read-only`, `max_attempts=2` | Any local CPU machine; requires Codex CLI installed and authenticated |
| Batch scoring / export (optional) | Score evidence directories in batch and export a flat table | `neurips_ed_track_minimal` | `make score-agentdojo-batch`; `python scripts/export_agentdojo_scores_csv.py` | Draft root, evidence root | Standardized score bundles; flat CSV | Batch scoring defaults: `openai/gpt-5.4`, `reasoning-effort=xhigh`, `per-key-concurrency=4`, `tasks-per-key=100` | Suitable for large-scale runs; requires preconfigured score-only API keys |

## 2. Machine configuration table (extracted from `configs/infra.yaml`)

| Machine role | Typical use | Connection | CPU limit | Memory | GPU | Concurrency | Docker | Applicable domains |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `other_vps` | Runs most general-purpose adapters | SSH VPS | 8 | 32 GB | No | 10 | Yes | `agentdojo`, `appworld`, `tau3_retail`, `workarena`, `judge_only`, `maintenance_update`, `matched_budget_controls` |
| `webarena_vps` | Runs WebArena / MiniWoB++ related adapters | SSH VPS | 4 | 16 GB | No | 3 | Yes | `webarena_verified`, `MiniWoB++` |
| `osworld_vps` | Runs the OSWorld-Verified appendix adapter | SSH VPS | 8 | 32 GB | No | 3 | Yes | `osworld_verified` |
| `local_androidworld` | Runs the AndroidWorld appendix adapter | Local machine | 4 | 16 GB | No | 1 | No | `androidworld` |

Notes:

- `draft` and `score` are not pinned to a specific machine role; the table above mainly constrains the adapter stage.
- The repository also contains a `local_toolsandbox` role, but it is primarily for smoke or diagnostic use and is not a necessary part of the current `draft -> adapter evidence -> score` pipeline.
- In the current config, `osworld_vps` still contains placeholder host/user/path values; a formal reproduction should follow the locked manifest.

## 3. Paper-ready fill-in table

You can copy the table below directly into the experimental setup section and replace the bracketed placeholders.

| Stage | Execution location | Machine configuration | Key software / model | Key inputs | Key outputs | Fields that should be explicitly reported in the paper |
| --- | --- | --- | --- | --- | --- | --- |
| Raw input -> `draft` | Local machine | `[CPU model]`; `[memory]`; no GPU required | `neurips_ed_track_minimal`; OpenRouter; `openai/gpt-5.4`; `reasoning-effort=high`; `max_output_tokens=12000` | `case_packet.md` | `checklist.yaml` and sidecar logs | OS version, Python version, package path, prompt path, schema path, API provider, model name, temperature, timeout settings |
| Evidence collection (adapter) | VPS or local, depending on benchmark routing | `other_vps: 8 CPU / 32 GB`; `webarena_vps: 4 CPU / 16 GB`; `osworld_vps: 8 CPU / 32 GB`; `local_androidworld: 4 CPU / 16 GB` | `src/evidence_system/adapters/*`; official benchmark runner; Agent A/B/C config from `configs/agents.yaml` | `job.json`, benchmark environment, official data/assets, agent config | `raw_run_record`, `artifact_manifest`, native evaluator artifacts, traces/logs | VPS provider and region, OS, CPU model, docker/conda/venv setup, benchmark commit/version, adapter commit, domain-to-machine-role mapping |
| `score` | Local machine | `[CPU model]`; `[memory]`; no GPU required | `neurips_ed_track_minimal`; Codex CLI; `gpt-5.4`; `reasoning-effort=xhigh`; `sandbox=read-only` | Locked checklist and saved evidence directory | `score.json/yaml`, manifest, Codex telemetry/reasoning log | Codex CLI version, model name, reasoning effort, sandbox mode, scoring prompt path, score schema path, whether `native_label` override was used |

## 4. Agent configuration that should usually be reported alongside machine configuration

If you are reproducing the full main experiment, reporting machine configuration alone is not enough. The agent configuration should also be listed.

| Role | Provider | Model | Temperature | Max tokens | Timeout | Retry |
| --- | --- | --- | --- | --- | --- | --- |
| Agent A | OpenRouter | `openai/gpt-5.4` | 0 | 4096 | 120 s | 2 |
| Agent B | OpenRouter | `anthropic/claude-opus-4.7` | 0 | 4096 | 120 s | 2 |
| Agent C | OpenRouter | `deepseek/deepseek-v4-pro` | 0 | 4096 | 120 s | 2 |
| Contract drafter | OpenRouter | `openai/gpt-5.4` | 0 | 8192 | 180 s | 2 |

## 5. One-sentence version

If you want a one-sentence description for the main paper text, you can use:

> Checklist drafting and final evidence scoring were both run with the minimal package at `<REPO_ROOT>/neurips_ed_track_minimal`, while raw evidence collection was executed through benchmark-specific adapters on benchmark-routed VPS or local machines as specified by `configs/infra.yaml`.
