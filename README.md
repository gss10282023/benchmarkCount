# Reviewer Entry Point

This repository contains the code and frozen result artifacts for the NeurIPS
Evaluations and Datasets track submission.

## What to Treat as the Paper Snapshot

`paper_result_packages/` is the frozen data snapshot used for the paper. Treat
this directory as the canonical source for the reported benchmark results. The
other `results/` directories are working outputs from local runs and may contain
newer or intermediate files that are not the paper snapshot.

The frozen snapshot contains five benchmark bundles:

| Benchmark | Bundle directory | Cases | Agents | Main per-case layout |
| --- | --- | ---: | --- | --- |
| AgentDojo | `paper_result_packages/agentdojo_case_bundle_openrouter_gpt54_high/` | 100 | `agent_a`, `agent_b`, `agent_c` | `cases/<case>/case_packet/`, `draft/`, `full_runs/`, `score_runs/` |
| AndroidWorld | `paper_result_packages/androidworld_both_agents_scored_cases_official_full100/` | 41 | `agent_a`, `agent_b` | `cases/<case>/draft/`, `source/`, `full/agent_*`, `score/agent_*` |
| AppWorld | `paper_result_packages/appworld_case_bundle_openrouter/` | 100 | `agent_a`, `agent_b`, `agent_c` | `cases/<case>/case_packet/`, `draft/`, `full_runs/`, `score_runs/` |
| MiniWoB | `paper_result_packages/miniwob_case_bundle/` | 100 | `agent_a`, `agent_b`, `agent_c` | `cases/<case>/case_packet/`, `drafts/`, `full_runs/`, `score_runs/` |
| tau3-retail | `paper_result_packages/tau3_retail_case_bundle/` | 100 | `agent_a`, `agent_b`, `agent_c` | `cases/<case>/case_packet/`, `draft/`, `full_runs/`, `score_runs/` |

Each case bundle includes the checklist draft artifacts, the retained benchmark
run artifacts, and the final evidence-scoring outputs. The final score outputs
are under `score_runs/` for AgentDojo, AppWorld, MiniWoB, and tau3-retail, and
under `score/agent_*` for AndroidWorld. Global flat score tables and official
split metadata are under each bundle's `global/` directory when present.

## Artifact Map

Use the following paths to inspect the frozen paper artifacts:

| Benchmark | Case packet/source | Draft/checklist artifacts | Benchmark run artifacts | Evidence-score artifacts |
| --- | --- | --- | --- | --- |
| AgentDojo | `agentdojo_case_bundle_openrouter_gpt54_high/cases/<case>/case_packet/` | `agentdojo_case_bundle_openrouter_gpt54_high/cases/<case>/draft/` | `agentdojo_case_bundle_openrouter_gpt54_high/cases/<case>/full_runs/full-agentdojo-*-agent_*` | `agentdojo_case_bundle_openrouter_gpt54_high/cases/<case>/score_runs/full-agentdojo-*-agent_*` |
| AndroidWorld | `androidworld_both_agents_scored_cases_official_full100/cases/<case>/source/` | `androidworld_both_agents_scored_cases_official_full100/cases/<case>/draft/` | `androidworld_both_agents_scored_cases_official_full100/cases/<case>/full/agent_a` and `full/agent_b` | `androidworld_both_agents_scored_cases_official_full100/cases/<case>/score/agent_a` and `score/agent_b` |
| AppWorld | `appworld_case_bundle_openrouter/cases/<case>/case_packet/` | `appworld_case_bundle_openrouter/cases/<case>/draft/` | `appworld_case_bundle_openrouter/cases/<case>/full_runs/full-appworld-*-agent_*` | `appworld_case_bundle_openrouter/cases/<case>/score_runs/full-appworld-*-agent_*` |
| MiniWoB | `miniwob_case_bundle/cases/<case>/case_packet/` | `miniwob_case_bundle/cases/<case>/drafts/` | `miniwob_case_bundle/cases/<case>/full_runs/full-miniwob-*-agent_*` | `miniwob_case_bundle/cases/<case>/score_runs/full-miniwob-*-agent_*` |
| tau3-retail | `tau3_retail_case_bundle/cases/<case>/case_packet/` | `tau3_retail_case_bundle/cases/<case>/draft/` | `tau3_retail_case_bundle/cases/<case>/full_runs/full-tau3_retail-*-agent_*` | `tau3_retail_case_bundle/cases/<case>/score_runs/full-tau3_retail-*-agent_*` |

All paths in this table are relative to `paper_result_packages/`.

## Minimal Reproduction Package

`neurips_ed_track_minimal/` is the reviewer-facing minimal code package. It
contains the code path used to transform original case content into draft
checklists, pair those drafts with benchmark case run artifacts, and run the
evidence-scoring comparison that produces score outputs.

This package is intentionally smaller than the full development tree. Reviewers
should start here when checking that the submitted code can run.

## Original Case Content

`experiments/case_packets/` stores the original case content used as input to
the draft/checklist pipeline. These case packets are the source-side artifacts
that feed into `neurips_ed_track_minimal/` before draft generation, benchmark
run artifact collection, and evidence scoring.

## Experiment Reproduction Flow

To reproduce the paper pipeline at the artifact level, start from the case
packets in `paper_result_packages/`. A case packet is a Markdown file that
consolidates the benchmark-specific files for one selected benchmark case into
one reviewer-readable input.

The reproduction flow is:

1. Feed a case packet into `neurips_ed_track_minimal/`.
2. Use the LLM drafting path in `neurips_ed_track_minimal/` to generate the
   draft checklist for that case.
3. Take the generated draft checklist and pair it with the saved benchmark run
   artifacts already included in `paper_result_packages/`.
4. Run the scorer in `neurips_ed_track_minimal/` to compare the draft checklist
   against the retained benchmark evidence and produce the score outputs.

In other words, `paper_result_packages/` provides both the paper snapshot and
the frozen benchmark run artifacts needed for scoring, while
`neurips_ed_track_minimal/` provides the minimal code path for draft generation
and score comparison. Re-running the live benchmark environments themselves is
separate from this artifact-level reproduction and requires benchmark-specific
installations and credentials.

## Path Placeholders

Text metadata and logs use anonymized path roots instead of machine-specific
absolute paths. The main placeholders are:

- `<REPO_ROOT>`: this repository root.
- `<REMOTE_REPO_ROOT>`: remote/VPS checkout root used for benchmark runs.
- `<ANDROIDWORLD_INSTALL_ROOT>`, `<ANDROID_SDK_ROOT>`: AndroidWorld and Android
  SDK installation roots.
- `<AGENTDOJO_INSTALL_ROOT>`, `<APPWORLD_INSTALL_ROOT>`,
  `<APPWORLD_OFFICIAL_ROOT>`, `<MINIWOB_INSTALL_ROOT>`,
  `<MINIWOB_VENV_ROOT>`, `<WORKARENA_INSTALL_ROOT>`,
  `<TAU2_BENCH_INSTALL_ROOT>`, `<WEBARENA_INSTALL_ROOT>`,
  `<WEBARENA_VERIFIED_INSTALL_ROOT>`: benchmark-specific installation roots.
- `<PYTHON_RUNTIME>`, `<UV_DATA_ROOT>`, `<UV_BINARY>`: local Python/uv runtime
  locations.
- `<CODEX_HOME>`, `<SSH_PRIVATE_KEY_PATH>`, `<LOCAL_USER>`, `<LOCAL_TMPDIR>`:
  local user, authentication, and temporary-directory placeholders.
- `<LOCAL_PATH>`, `<USER_HOME>`, `<REPO_ROOT_TRUNCATED>`: generic local path
  placeholders used in anonymized logs or guardrail examples.
- `<BENCHMARK_INSTALL_ROOT>`: generic benchmark installation placeholder used in
  guardrail examples when a benchmark-specific root is not needed.
- `<APPWORLD_TASK_HOME>`: AppWorld task-internal home directory used inside
  benchmark task text and derived flat score tables.

## Smoke Test

The offline smoke test verifies that the minimal checklist/scoring package can
load its schemas, run deterministic guardrails, and execute without external
model calls.

Install the minimal Python dependencies:

```bash
python3 -m pip install -r neurips_ed_track_minimal/requirements.txt
```

Run the smoke test from the repository root. If `.venv/bin/python` exists, the
root `Makefile` uses it automatically; otherwise it uses `python3`.

```bash
make smoke
```

Equivalent command:

```bash
make -C neurips_ed_track_minimal smoke PYTHON=python3
```

Full benchmark reruns require benchmark-specific environments and model/API
credentials. The frozen artifacts in `paper_result_packages/` are provided so
reviewers can inspect the paper data without rerunning the full collection
pipeline.

## Repository Layout

- `paper_result_packages/`: frozen paper result snapshot.
- `neurips_ed_track_minimal/`: minimal reviewer-facing code path for draft
  generation, benchmark artifact pairing, evidence scoring, and smoke tests.
- `experiments/case_packets/`: original case content used as input to the
  draft/checklist pipeline.
- `experiments/`: case packets, split metadata, and experiment inputs used by
  the local pipeline.
- `results/`: local working outputs from draft/full/score runs. These are not
  the canonical paper snapshot unless explicitly copied into
  `paper_result_packages/`.
- `src/evidence_system/`: broader experiment-system code used during
  development and local runs.

## Secrets

Do not put real API keys, SSH private keys, credentials, or private prompt logs in repository files. Use environment variable names and local paths only.
