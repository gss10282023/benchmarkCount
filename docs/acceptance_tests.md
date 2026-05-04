# Acceptance Tests And Gates

## Step 1 Acceptance

Step 1 is complete when:

- all required docs exist under `docs/`.
- review packet exists at `reviews/packets/step01_spec_freeze_review_packet.md`.
- no formal runner/scorer/adapter/schema/freezer code has been implemented as part of Step 1.
- no formal scored records, formal metrics, formal freeze file, or paper outputs are created.
- docs state P0/P1/P2/P3 full scope and appendix/diagnostic paper-output gate.
- docs state canonical domain identifiers and display-name separation.
- docs state phase, experiment_type, and priority schema.
- docs state record_slot, attempt, final_attempt, completed_record, and infra_exclusion_record semantics.
- docs state adapter/scorer boundary.
- docs state pre-scoring contract lock and prediction freeze.
- docs state native evaluator artifact decisive-evidence rule.
- docs state R1-R7 taxonomy and upstream-priority rule.
- docs state R1-R7 formal semantics, boundaries, examples, and golden fixture requirements.
- docs state INFRA_EXCLUDED, COUNTED_ONLY_SCORE null, and stronger_measurement gates.
- docs state LLM logging and human-time boundaries, including `tab:cost` human-time-only rule.
- docs state paper mapping coverage and paper-output details.

## Paper Mapping Coverage Gate

The gate scans `experiments/paper_mapping.md` and paper labels. Required coverage:

```text
tab:views
tab:unresolve-taxonomy
tab:domains
tab:main-results-A
tab:denominator-audit
tab:main-results-B
tab:prediction-outcomes
tab:main-results-C
tab:pairwise-margins
tab:top-unresolve-reasons
tab:audit-rerun
tab:per-agent
tab:cost
tab:contract-drafting-metadata
tab:update
fig:hero
fig:evidence-counting
fig:case-cards
app:per-agent
app:cost
app:contract-drafting-details
app:aux-domains
app:osworld
app:judge
app:update
app:release
Formal Definitions
app:macro-contract
```

Step 1 check result: all labels above are covered in `experiments/paper_mapping.md`.

## Canonical CLI Gate

The gate requires package CLIs for:

```text
check_infra
deploy_all
deploy_webarena
deploy_osworld
deploy_other_vps
deploy_local_androidworld
monitor
collect_results
resume_failed
make_tables
make_figures
make_appendix
final_report
```

Wrapper scripts can exist only as thin wrappers around `python -m evidence_system.cli.<command>`.

## Schema Gates

Later schema tests must include valid and invalid fixtures for:

- non-canonical domain id fails.
- display name used as id fails.
- missing phase/experiment_type/priority fails.
- `status=COMPLETED` without evidence label fails.
- UNRESOLVE without R1-R7 reason or unresolve_level fails.
- SUCCESS/FAIL with unresolve_reason fails.
- INFRA_EXCLUDED with evidence label fails.
- INFRA_EXCLUDED entering evidence envelope fails.
- COUNTED_ONLY_SCORE not null when SUCCESS+FAIL=0 fails.
- stronger_measurement without sidecar/appendix/manifest mapping fails.
- missing official provenance for decisive native evaluator artifact fails.
- `raw_run.native_label` decisive use without locked artifact mapping fails.
- OSWorld evaluator_failure/evaluator_unstable mapped to evidence UNRESOLVE fails.
- adapter raw output missing `contains_final_evidence_label=false` fails.

## Contract And Freeze Gates

Required tests:

- P0 case unit without locked contract blocks preflight/full/scoring.
- contract lock time after scoring start blocks scoring.
- drafter forbidden inputs block contract use.
- unsupported native-aligned requirement without stronger_measurement mapping blocks lock/freeze.
- prediction registry not frozen before scoring blocks scoring.
- scoring without freeze file blocks scoring.
- manifest/paper_mapping/official_split/contract/schema/scorer/bootstrap/audit/rerun hash drift blocks scoring or paper outputs.
- official split fewer than 100 eligible P0 cases without frozen manifest exception blocks scheduling/scoring.
- pairwise_equality_tolerance or P1-P4 boundary rule missing before scoring blocks aggregation.
- pairwise_equality_tolerance not set to a frozen value or explicit `需要从 locked manifest 确认` placeholder before formal freeze blocks aggregation.
- formal pre_scoring_freeze.json created during Step 5 development blocks formal progression.
- preflight record not declared in the frozen P0 manifest enters formal scored records fails.
- smoke or dry_run output enters formal scored records, metrics, tables, figures, appendix empirical outputs, or final report fails.
- concrete Agent A-D, contract_drafter, or judge_only model id/version pin/temperature/prompt hash/API-key env value hardcoded in code, tests, runner, scorer, paper generation, or review packets fails unless the value is inside an explicitly synthetic config fixture.

## Adapter Gates

Required tests:

- adapter writes raw run record and artifact manifest, not final scored record.
- adapter produces no final SUCCESS/FAIL/UNRESOLVE.
- adapter output must include `contains_final_evidence_label=false`; true, missing, or contradictory final evidence fields fail.
- artifact paths and sha256 values are present.
- official runner/evaluator provenance is present when native evaluator output may be decisive.
- smoke and dry_run outputs cannot enter formal results.
- AgentDojo paired arms are preserved.
- WebArena routes only to WebArena VPS.
- OSWorld-Verified separates infra/pre-run failure, evaluator failure/unstable, and evidence UNRESOLVE.
- judge-only input is blind to native_label, native_score, native evaluator pass/fail scalar, outcome label, evidence label, UNRESOLVE reason, scored values, paper-output values, and agent identity.

## Scorer Gates

Required tests:

- scorer refuses unlocked contract.
- scorer refuses hash mismatch.
- scorer refuses post-lock clarification for native-aligned main result.
- scorer refuses artifact sha mismatch.
- scorer refuses native_label-only decisive evidence.
- scorer refuses outcome_label, prior outcome verdict, previous run outcome, previous scored/evidence label, runner summary verdict, adapter summary verdict, judge-only label, alternate-view verdict, and paper-output value as decisive evidence.
- scorer verdict_engine rejects `agent_id`, agent family, model id, provider, and model version as inputs.
- scorer fixture where only agent identity changes must keep the same verdict_engine output hash.
- scorer implementation with any agent identity condition branch fails static or behavioral validation.
- scorer emits exactly one R1-R7 reason for each UNRESOLVE.
- scorer has positive and negative golden fixtures for R1, R2, R3, R4, R5, R6, and R7.
- scorer has overlap fixtures for R3-over-R1, R4-over-R1, R5-over-arm-specific-missing-evidence, R7-over-R1/R4, and R6-versus-validation-failure.
- scorer applies upstream-priority rule deterministically.
- scorer excludes stronger_measurement from native-aligned main envelope.
- scorer refuses INFRA_EXCLUDED input as completed scored record.

## Stats, Audit, And Paper Gates

Required tests:

- `N = SUCCESS + FAIL + UNRESOLVE`.
- `width = UNRESOLVE / N`.
- bootstrap clusters by case unit.
- prediction outcomes are only supported/falsified/inconclusive.
- interval touching threshold is inconclusive unless inclusive rule was frozen.
- pairwise equality uses frozen tolerance; ordinary overlap is `?`.
- if the paper has not specified `pairwise_equality_tolerance`, the stats plan must carry `需要从 locked manifest 确认` until a formal frozen value is set before scoring.
- rerun subset is Agent A, 10 case units/domain, 40 case units, 50 episodes.
- audit is 100 records, 25/domain, stratified stress sample.
- audit sampler represents counted records, UNRESOLVE records, and native/evidence disagreement records within each domain whenever all three buckets are non-empty.
- audit sampler records `bucket_empty` with source counts when a required bucket is absent and follows the frozen redistribution rule.
- audit sampler omitting any non-empty required bucket fails and blocks `tab:audit-rerun`.
- R1-R7 taxonomy kappa computed only where both auditors mark UNRESOLVE.
- audit and review blind-input fixtures exclude agent identity, native_label, native_score, native evaluator pass/fail scalar, outcome label, scored values, paper-output values, counting decision, UNRESOLVE reason, and alternate view verdicts.
- `tab:views` shares provenance across views.
- `tab:cost` reads only human-time logs.
- `fig:hero` panel (b) includes only four P0 main domains.
- `fig:case-cards` has case-level provenance and artifact ids.
- `app:update` exact funnel is enforced.
- matched-budget controls use same proposal/selection budget.
- judge-only metrics are diagnostic.
- final report cost/latency/failure values require provenance.
- final paper output has no `\fillfromdata` or empirical fallback values.
- required paper_mapping label missing, unmapped, mapped to fallback/manual data, mapped to smoke/dry_run/mock output, or mapped to undeclared non-formal appendix/diagnostic output blocks paper generation unless paper text and manifest are updated together.
