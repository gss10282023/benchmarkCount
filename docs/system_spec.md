# System Specification

## Status And Scope

This is the Step 1 Spec Freeze draft for the evidence-envelope experiment system. It is a specification only. It does not implement formal runner, adapter, scorer, schema validator, freeze file, metrics, or paper-output code.

The complete system scope is P0/P1/P2/P3:

- P0: four main domains, locked native-aligned evidence contracts, prediction freeze, evidence-envelope scoring, main tables, and main figures.
- P1: denominator audit, case-cluster bootstrap, pairwise ranking and margins, top UNRESOLVE reasons, rerun subset, blinded audit, and per-agent envelopes.
- P2: AndroidWorld, WorkArena, OSWorld-Verified appendix stress test, contract metadata, human-time cost, release metadata, formal definitions / rescorer interface, and result macro contract.
- P3: judge-only diagnostic, maintenance update, matched-budget controls, and qualitative case cards.

If any declared appendix or diagnostic is missing, paper outputs must be blocked unless the paper text and `experiments/experiment_manifest.yaml` are updated together. Appendix or diagnostic omissions cannot be explained only in a final report.

Old scaffold, `mock_result`, and dry-run output are not formal experiment logic. They may be used only for engineering self-checks and synthetic fixtures. Formal logic must live under `src/evidence_system/`. Any `scripts/*.py` files are thin wrappers around package CLIs and cannot contain unique formal logic.

## Canonical Domains

All manifest IDs, job IDs, raw/scored result directories, adapter module names, aggregation keys, hash inputs, release metadata, and paper mappings use canonical domain identifiers. Display names are presentation fields only.

| canonical id | display name |
|---|---|
| `agentdojo` | AgentDojo |
| `appworld` | AppWorld |
| `webarena_verified` | WebArena-Verified |
| `tau3_retail` | tau3-bench retail |
| `androidworld` | AndroidWorld |
| `workarena` | WorkArena |
| `osworld_verified` | OSWorld-Verified |
| `judge_only` | judge-only |
| `maintenance_update` | maintenance update |
| `matched_budget_controls` | matched-budget controls |

Legacy spellings such as `AgentDojo`, `AppWorld`, `WebArena-Verified`, `tau3-bench retail`, `tau3 retail`, `webarena`, `osworld`, `judge-only`, and `matched-budget controls` must be normalized before hashing, scheduling, aggregation, scoring, release, or paper-output generation. If a formal artifact still uses a display name as an ID, the gate fails closed.

## Phases, Experiment Types, And Priorities

Every job, raw run record, scored record, failure record, metric artifact, and paper-output source record must distinguish:

```text
phase: smoke | dry_run | preflight | full | rerun
experiment_type: main | appendix | diagnostic | audit | maintenance_update | matched_budget_control
priority: P0 | P1 | P2 | P3
```

`phase=smoke` and `phase=dry_run` are engineering-only phases and cannot enter the formal evidence envelope. P2/P3 appendix and diagnostic work uses `experiment_type`, not a new phase value.

## Record Terms

The system uses these terms consistently:

- `record_slot`: manifest-declared domain x case_unit x agent slot.
- `attempt`: one execution attempt for a record_slot.
- `final_attempt`: selected attempt after retry/resume.
- `completed_record`: final_attempt where benchmark execution began and is eligible for SUCCESS/FAIL/UNRESOLVE.
- `infra_exclusion_record`: benchmark/pre-run failure excluded from evidence-envelope denominator but included in denominator audit.

Evidence-envelope denominators use only completed scored records. Denominator audit covers attempted record slots, infra exclusions, completed records, agent-caused failures, and formally blocked slots. Retry attempts do not create additional samples.

P0 planned record slots are fixed at 1600: 4 main domains x 100 case units x 4 agents. If the frozen paper or manifest requires 1600 completed_records strictly, recoverable infra exclusions must be retried until completed, or the run is `P0-incomplete`. If infra exclusions remain after the allowed retry policy, the main envelope `N` uses completed scored records only, while the denominator audit reports `attempted=1600`, `completed`, `infra_excluded`, `agent_caused_failures`, and formally blocked slots.

## Formal Entry Points

Package CLI is the canonical formal entry. Wrapper scripts, if retained, call these commands.

| Required responsibility | Canonical package CLI |
|---|---|
| check infra | `python -m evidence_system.cli.check_infra` |
| deploy all machines | `python -m evidence_system.cli.deploy_all` |
| deploy WebArena-Verified | `python -m evidence_system.cli.deploy_webarena` |
| deploy OSWorld-Verified | `python -m evidence_system.cli.deploy_osworld` |
| deploy other VPS domains | `python -m evidence_system.cli.deploy_other_vps` |
| deploy local AndroidWorld | `python -m evidence_system.cli.deploy_local_androidworld` |
| monitor runs | `python -m evidence_system.cli.monitor` |
| collect results | `python -m evidence_system.cli.collect_results` |
| resume failed attempts | `python -m evidence_system.cli.resume_failed` |
| make tables | `python -m evidence_system.cli.make_tables` |
| make figures | `python -m evidence_system.cli.make_figures` |
| make appendix | `python -m evidence_system.cli.make_appendix` |
| final report | `python -m evidence_system.cli.final_report` |

Additional package CLIs required by the lifecycle include `validate_config`, `draft_contracts`, `lock_contracts`, `validate_contracts`, `freeze_predictions --check-only`, `run_domain`, `run_preflight`, `run_full`, `score_records`, `validate_results`, `aggregate`, `run_audit`, `run_rerun`, and `make_release`.

## Configuration And Model Rules

Agent A-D, `contract_drafter`, and `judge_only` model IDs, version pins, temperatures, prompt versions, prompt hashes, provider fields, retry settings, and API-key environment variable names must not be hardcoded in code, tests, docs-as-data, runner logic, scorer logic, or paper generation. Formal code reads them from `configs/agents.yaml` and the locked manifest. If the two disagree or a value is missing for a formal run, the system fails closed.

Agent A-D are fixed measurement probes, not leaderboard entries. Each Agent A-D entry must include `agent_probe_rationale` with:

```text
non_redundant_measurement_probe
spans_source_openness
spans_scale
spans_tool_use_style
leaderboard_interpretation=false
```

Unresolved rationale fields remain `需要从 locked manifest 确认` during specification and draft manifest work, but formal runs fail until resolved.

The paper interpretation is frozen: Agent A-D are non-redundant measurement probes used to test whether evidence uncertainty is structured by domain, not leaderboard entries and not a factorial model comparison. Concrete model identifiers, version pins, temperatures, provider settings, prompt versions, and prompt hashes are config/locked-manifest data only.

Static gates must scan code, tests, runner logic, scorer logic, paper generation, and review packets for hardcoded Agent A-D, `contract_drafter`, or `judge_only` concrete model ids, version pins, temperatures, prompt hashes, prompt versions, and API-key environment variable values. Such values fail unless they appear inside an explicitly synthetic config fixture that cannot be used by formal runs.

API key values, SSH private keys, and other secrets must never be written to repository files, logs, review packets, manifests, or paper outputs. Only environment variable names and redacted/hashed references may be recorded.

## Required Schemas As First-Class Objects

Formal artifacts are validated schema objects, not untyped dictionaries. Step 3 must create first-class schemas for at least:

```text
experiment_manifest.schema.json
paper_mapping.schema.json
job.schema.json
agent_config.schema.json
infra_config.schema.json
stats_plan.schema.json
bootstrap_plan.schema.json
audit_sampling_plan.schema.json
rerun_subset.schema.json
aggregate_metrics.schema.json
prediction_outcome.schema.json
pairwise_matrix.schema.json
paper_output.schema.json
denominator_audit.schema.json
failure_record.schema.json
deployment_manifest.schema.json
result_schema.schema.json
artifact_manifest.schema.json
llm_call.schema.json
human_time.schema.json
human_review.schema.json
release_manifest.schema.json
```

Schemas must cover experiment id, canonical domain id, phase, experiment_type, priority, paper labels, case counts, official splits, deterministic selection metadata, agents, Agent A-D rationale, contract metadata, raw logs, artifact provenance, metrics, tables, figures, machine role, failure status, human time, LLM logging, deployment provenance, paper-output source mapping, audit/rerun plans, and release metadata.

## Paper Mapping Coverage

Step 1 checked `experiments/paper_mapping.md` against the required label list. The mapping covers:

`tab:views`, `tab:unresolve-taxonomy`, `tab:domains`, `tab:main-results-A`, `tab:denominator-audit`, `tab:main-results-B`, `tab:prediction-outcomes`, `tab:main-results-C`, `tab:pairwise-margins`, `tab:top-unresolve-reasons`, `tab:audit-rerun`, `tab:per-agent`, `tab:cost`, `tab:contract-drafting-metadata`, `tab:update`, `fig:hero`, `fig:evidence-counting`, `fig:case-cards`, `app:per-agent`, `app:cost`, `app:contract-drafting-details`, `app:aux-domains`, `app:osworld`, `app:judge`, `app:update`, `app:release`, `Formal Definitions`, and `app:macro-contract`.

Future paper-output gates must also scan for `\fillfromdata`, row-file fallbacks, result macro fallbacks, and figure layout values. Final paper outputs must set `\resultdatatrue` and must not contain empirical fallback values.

Paper generation fails closed if any required `paper_mapping` label is missing, unmapped, mapped to fallback or manual empirical data, mapped to smoke/dry_run/mock output, or mapped to an undeclared non-formal appendix/diagnostic output. The only allowed exception is a synchronized update to paper text and manifest that removes or changes the declared output.

## Strict Gates

Any gate failure blocks the next formal stage. Critical gates include:

- no spec freeze or missing Step 1 GPT Pro review packet blocks formal progression.
- non-canonical domain IDs block hashing, scheduling, aggregation, and paper outputs.
- missing contract lock blocks preflight scoring, full scoring, and formal freeze.
- prediction freeze later than scoring blocks scoring.
- formal scoring with smoke, dry-run, mock, or old scaffold data blocks results.
- declared appendix/diagnostic missing blocks paper outputs unless paper and manifest are updated.
- schema drift, scorer drift, manifest drift, contract hash drift, official split drift, paper mapping drift, bootstrap/audit/rerun plan drift, or prompt/template drift blocks scoring or paper outputs.
- missing, unmapped, fallback/manual, or non-formal `paper_mapping` source blocks paper outputs unless paper and manifest are updated together.
- use of `raw_run.native_label` as decisive evidence without locked artifact mapping blocks scoring.
- use of `outcome_label`, prior outcome verdict, previous scored/evidence label, adapter summary verdict, runner summary verdict, judge-only label, alternate-view verdict, paper-output value, or agent identity as decisive scorer evidence blocks scoring.
- `INFRA_EXCLUDED` with evidence label blocks result validation.
- `COUNTED_ONLY_SCORE` fallback when SUCCESS+FAIL is zero blocks paper outputs.
- missing stronger_measurement sidecar/appendix/manifest mapping blocks formal run.
- post-lock clarification used in native-aligned main result blocks paper outputs.

## Confirmation Items

The following are not formal values in this Step 1 draft:

- Agent A-D concrete model version pins: `需要从 locked manifest 确认`.
- Agent A-D full probe rationale fields: `需要从 locked manifest 确认`.
- Contract drafter model/version/temperature/prompt version/prompt hash: `需要从 locked manifest 确认`.
- Judge-only model/version/temperature/prompt version/prompt hash: `需要从 locked manifest 确认`.
- Appendix case counts for AndroidWorld, WorkArena, OSWorld-Verified, judge-only, maintenance update, and matched-budget controls: `需要从 locked manifest 确认`.
- Official split eligible set counts and exceptions: `需要从 benchmark 官方 split 确认`.
- `pairwise_equality_tolerance` until set in the frozen stats plan: `需要从 locked manifest 确认`.
- Formal metrics, costs, human times, latency, failure rates, and paper cell values: `需要从 scored manifest 填充`.
