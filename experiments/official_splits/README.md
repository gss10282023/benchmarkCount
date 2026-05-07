# Official case-unit source files

These files are the pre-scoring candidate pools used by
`scripts/select_case_units.py`. They are source inputs, not results.

## Main-study sources

- `agentdojo_v1.2.2_paired_candidates.json`: generated on `other-vps-01` from
  the installed AgentDojo package with `get_suites("v1.2.2")`. Candidate case
  units are official `(suite, user_task_id, injection_task_id)` pairs. The
  selected execution manifest must still fix the AgentDojo attack strategy
  before any scoring run.
- `appworld_test_normal.txt`: copied from
  `<APPWORLD_INSTALL_ROOT>/project/data/datasets/test_normal.txt` on
  `other-vps-01`. The AppWorld project describes the normal and challenge test
  sets separately; this source uses the normal test set as the strong negative
  control pool.
- `webarena_verified_official_812.json`: copied from
  `<WEBARENA_VERIFIED_INSTALL_ROOT>/assets/webarena-verified.json` on
  `webarena-vps-01`.
- `tau3_retail_split_tasks.json`: copied from
  `<TAU2_BENCH_INSTALL_ROOT>/data/tau2/domains/retail/split_tasks.json` on
  `other-vps-01`. The selection command uses the `base` key because `train`
  and `test` are below 100 eligible tasks and `base` is the full official
  retail task pool in that file.

## Contract-draft source details

- `agentdojo_selected_task_sources.json`: generated on `other-vps-01` for the
  selected AgentDojo case units from the installed AgentDojo task classes and
  suite tool metadata.
- `appworld_selected_task_sources.json`: generated on `other-vps-01` for the
  selected AppWorld case units from each official task directory, including
  `specs.json` and ground-truth evaluator files.
- `tau3_retail_tasks.json` and `tau3_retail_policy.md`: copied from the
  official retail domain directory and used for contract-drafting source
  support.

The merged LLM-drafter source bundle is
`../evidence_contracts/source_bundles/main_case_units_source_bundle.json`.

The local full-case packet corpus used by the drafter now lives under
`../case_packets/`. `official_splits/` remains the official selection/source
basis; it is not the materialized per-case packet store.

## Smoke-test exclusions

The explicit exclusion list is `../smoke_test_exclusions.yaml`. It is currently
empty for all four main domains because no prior smoke-test case list was found
in the project or benchmark install directories before selection. This file is
recorded in selection provenance and must remain locked before scoring.
