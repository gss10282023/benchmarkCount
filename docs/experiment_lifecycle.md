# Experiment Lifecycle

## Formal Ordering

The formal lifecycle is:

```text
bootstrap repo
-> validate config, manifest, official splits, source bundle, and paper mapping
-> draft evidence contracts
-> human review with timing
-> lock contracts
-> update manifest with contract hash, lock time, and version
-> validate locked contracts
-> freeze prediction registry and all code/config/hash inputs
-> deploy and check infrastructure
-> adapter smoke
-> preflight 10 case units per main domain
-> validate preflight
-> full run
-> scoring from locked contracts and raw artifacts
-> validate scored results
-> audit and rerun diagnostics
-> aggregation, bootstrap, pairwise margins, and P1-P4 outcomes
-> appendix diagnostics and release metadata
-> paper tables, figures, appendix, result macros, and final report
-> release audit package
```

No formal scorer output, aggregate metric, freeze file, or paper output may be produced before the required upstream gates pass. Step 8 vertical-slice scoring or aggregation is provisional integration testing only; it cannot create formal scored records, formal metrics, formal `pre_scoring_freeze.json`, or paper outputs.

## Contract Lifecycle

Evidence contract draft/review/lock is a P0 blocker. For every case unit that can produce evidence-scored records or update-countability results:

1. A contract-drafting LLM drafts requirements using only task text, official policy, evaluator code or description, database/API/browser/file/tool schema, trace schema, available post-run artifact types, and the native-aligned vs stronger_measurement template.
2. The drafter must be blind to agent identity, agent trace, native score, native evaluator pass/fail scalar, outcome label, alternate view verdicts, evidence label, UNRESOLVE reason, and scored/paper-output values.
3. Human adapter authors audit and edit each proposed requirement against the source hierarchy: official evaluator semantics, official task text / policy, then schema constraints needed to interpret evaluator-visible state.
4. Unsupported native-aligned requirements are removed or marked `stronger_measurement`.
5. Every stronger_measurement claim gets a sidecar report, appendix mapping, or manifest mapping and stays out of native-aligned main results.
6. The locked contract records version, hash, lock time, reviewer, drafter metadata, prompt version/hash, visible input hashes, hidden-input assertion, source-support audit, and claim scope.
7. The manifest records the locked contract id/version/hash before scoring.

If a locked contract needs clarification after outcomes are available, the change creates a superseded/clarification contract version and a sensitivity report mapping only. It is never folded into the native-aligned main result.

## Prediction And Pre-Scoring Freeze

Prediction freeze must occur before scoring. The formal pre-scoring freeze must include all inputs that can affect scoring, aggregation, or paper outputs:

```text
manifest_hash
paper_mapping_hash
official_splits_hash
eligible_case_unit_set_hash
excluded_smoke_case_units
smoke_exclusion_hash
case_selection_order_hash
hash_function
hash_salt_hash
source_bundle_hash
agents_config_hash
infra_config_hash
locked_contracts_hash
evidence_contract_template_version/hash
contract_drafting_prompt_version/hash
prediction_registry_hash
taxonomy_version
result_schema_hash
artifact_schema_hash
scorer_version
scorer_code_hash
code_git_commit
bootstrap_plan_hash
bootstrap_seed
bootstrap_resample_count
audit_sampling_plan_hash
audit_sample_seed
rerun_subset_hash
rerun_subset_selection_rule
P1-P4 predictions
pairwise_equality_tolerance
P1-P4 threshold boundary rule
```

Step 5 may implement freeze CLI and tests, but it must not create a formal `results/manifests/pre_scoring_freeze.json`. Formal freeze creation waits until Step 1-12 are approved and formal experiment flow begins.

## Deterministic Selection

Main-domain default selection is 100 case units per domain: 10 preflight and 90 full. Selection must freeze:

```text
hash_function
hash_salt_hash
eligible_case_unit_set_hash
excluded_smoke_case_units
smoke_exclusion_hash
case_selection_order_hash
case selection order
seeds
rerun subset rule
```

If an official verified split has fewer than 100 eligible case units, the exception must be recorded in the frozen manifest before scoring. Otherwise the system fails closed. It cannot backfill with non-official, duplicated, smoke-test, appendix, or synthetic cases.

Preflight status is formal only for frozen manifest slots. The 10 P0 preflight case units per main domain may enter formal scored records only when they were predeclared in the frozen P0 manifest, passed preflight validation, and are carried forward as final selected attempts under the same contract/config/taxonomy hashes. `phase=smoke` and `phase=dry_run` outputs can never enter formal scored records, metrics, tables, figures, appendix empirical outputs, or final report values.

Failed formal preflight validation blocks the full run. Recovery is limited to retry/resume under the same frozen manifest, record_slot, case_unit_id, contract version/hash, config hash, taxonomy version, and deterministic selection order. Failed or inconvenient preflight slots cannot be replaced, cherry-picked, moved to appendix, or silently dropped from P0 accounting.

## P0 Run Semantics

The P0 planned record-slot count is 1600:

```text
4 main domains x 100 case units x 4 agents
```

AgentDojo stores two episodes per record, benign and injected, for 800 AgentDojo episodes. The other three main domains store 400 episodes each. The main study stores 2000 episodes total.

Before final result gate, every P0 record_slot has exactly one final state:

```text
completed_record
infra_exclusion_record
formally_documented_missing_or_blocked
```

Formal envelopes use completed scored records only. Denominator audit still reports all attempted P0 record slots and all infra exclusions.

## Execution And Retry

Adapters create raw artifacts and raw run records only. They cannot produce final SUCCESS/FAIL/UNRESOLVE labels.

Retries apply only to recoverable infra/pre-run failures or recoverable logging/collection failures. Each retry writes a new attempt and preserves earlier attempts. A retry never changes case unit, agent id, contract version, taxonomy version, or deterministic selection order. UNRESOLVE is not an execution failure and must not be retried as a failure. Agent-caused invalid actions, tool misuse, malformed answers, or timeouts after benchmark execution begins are not infra exclusions.

## Formal Scoring

Scoring occurs after completed raw runs are collected, locked contracts exist, prediction freeze is earlier than scoring, and hash inputs match. The scorer reads only locked contracts, manifest/case metadata, raw trace/post-state/artifacts, artifact manifest, freeze metadata, and native evaluator artifacts permitted by locked contract mapping.

The scorer must not use `raw_run.native_label`, native score, or normalized summary scalar as decisive evidence unless the locked contract maps a native evaluator artifact as allowed/required evidence and the artifact has path, sha256, official runner/evaluator provenance, and direct verified object read.

## Aggregation And Paper Outputs

Aggregation runs only on validated scored records and validated denominator-audit inputs. Bootstrap plan, pairwise_equality_tolerance, audit sampling plan, rerun subset, P1-P4 threshold boundary rule, and inclusive/exclusive threshold behavior must be frozen before formal scoring.

Paper outputs are generated only after all declared P0/P1/P2/P3 outputs either exist with provenance or have been removed from both paper text and manifest. `tab:cost` reads only human-time logs, not LLM token/cost logs or VPS runtime. `fig:hero` panel (b) includes only four P0 main-domain rows. `app:update` uses the exact paper funnel: 6 raw proposals/domain, 3 selected/domain, 24 proposed, 12 selected, and 15 executed because AgentDojo is paired.
