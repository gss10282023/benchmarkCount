# Paper Mapping

Sources read:

- `计划.md`
- `revised_agent_benchmark_paper.tex`

Scope constraints followed:

- This mapping uses paper labels and appendix names rather than numeric section numbers.
- This mapping does not invent agent model IDs, version pins, seeds, costs, runtimes, machine specs, or appendix case counts.
- Values not explicit in the paper are marked with the Chinese placeholders required by `计划.md`.
- TeX fallback values and `\fillfromdata` macros are treated as placeholders, not empirical results.

## Stable Paper Labels

Main text section labels:

- `sec:evidence-counting`: evidence-supported counting.
- `sec:units`: case units, records, episodes, evidence.
- `sec:evidence-contracts`: native-aligned evidence contracts.
- `sec:envelope`: counted records to evidence envelopes.
- `sec:interval-meaning`: case-resampling interval interpretation.
- `sec:pairwise`: robust pairwise ranking rule.
- `sec:taxonomy`: R1-R7 `UNRESOLVE` taxonomy.
- `sec:worked-example`: qualitative case cards.
- `sec:study-design`: four-domain study design.
- `sec:agents`: fixed agents, manifest, workload.
- `sec:contract-drafting`: contract-drafting and locking.
- `sec:predictions`: pre-registered predictions and falsification clause.
- `sec:audit`: audit and rerun checks.
- `sec:main-results`: main results tables.
- `sec:countability`: envelope width concentration.
- `sec:conditional-score`: counted-only diagnostic interpretation.
- `sec:robust-rankings`: pairwise ranking interpretation.
- `sec:inspectable`: audit and rerun inspectability.
- `sec:discussion`: discussion.
- `sec:related-work`: related work.

Appendix labels and named appendix sections:

- `app:per-agent`: per-agent envelope breakdown.
- `app:cost`: cost of adopting the method.
- `app:contract-drafting-details`: contract-drafting details.
- `app:aux-domains`: AndroidWorld and WorkArena additional negative controls.
- `app:osworld`: OSWorld-Verified higher-noise stress test.
- `app:judge`: judge-only scoring diagnostic.
- `app:update`: benchmark-maintenance study and matched-budget controls.
- `app:release`: responsible release plan.
- Appendix `Formal Definitions`: trajectory, evidence function, oracle, counting/envelope.
- `app:macro-contract`: result macro contract.

## Table Coverage

| Label | Paper object | Required data | Mapping status |
|---|---|---|---|
| `tab:views` | Reporting views | Denominator, undecidable handling, purpose for evidence envelope, counted-only, native benchmark, optimistic, pessimistic, judge-only diagnostic | Static paper table; no scored values required |
| `tab:unresolve-taxonomy` | R1-R7 taxonomy | One dominant blocking reason per `UNRESOLVE` record; upstream-priority rule | Static taxonomy plus scored per-record tags |
| `tab:domains` | Main and appendix domains | Main domain case units, records, episodes, native signals, evidence sources; appendix domain counts | Main counts explicit; appendix counts use `\unresolveplaceholder{}` / `需要从 locked manifest 确认` |
| `tab:main-results-A` | Main measurement report | Total, SUCCESS, FAIL, UNRESOLVE, Coverage, Counted-only score, Lower, Upper, Width | Totals explicit; scored cells are `\fillfromdata` |
| `tab:denominator-audit` | Denominator audit | Attempted, infra/pre-run excluded, completed, agent-caused FAIL, notes | Completed totals explicit; other values are `\fillfromdata` |
| `tab:main-results-B` | Case-resampling intervals | Lower CI, Upper CI, Width CI, Counted-only score CI, native score inside envelope | All empirical interval cells are `\fillfromdata` |
| `tab:prediction-outcomes` | Pre-registered prediction outcomes | P1-P4 observed quantity and three-state outcome | Registered criteria explicit; observed values/outcomes are `\fillfromdata` |
| `tab:main-results-C` | Directional pairwise matrix | A-B, A-C, B-C, non-identified pairs, all-domain diagnostics | Pair cells fallback to `?`; counts/diagnostics are `\fillfromdata` |
| `tab:pairwise-margins` | Pairwise dominance margins | One row per envelope-separated pair with margin and 95% case-cluster bootstrap interval | Row file required; fallback says fill from scored manifest |
| `tab:top-unresolve-reasons` | Dominant `UNRESOLVE` reasons | Top reason by main domain | All values are `\fillfromdata` |
| `tab:audit-rerun` | Stratified audit and rerun checks | Audit strata, agreement, countability kappa, taxonomy kappa, rerun agreement/pattern | Audit item counts explicit; metrics are `\fillfromdata` |
| `tab:per-agent` | Per-agent envelopes | `[LB, UB]`, width, counted-only score for 3 agents x 4 domains | Row file required; fallback rows are `\fillfromdata` |
| `tab:cost` | Human-time cost | Draft/lock min/case, score evidence min/record, tag `UNRESOLVE` min/record, setup notes | Setup notes explicit; time values are `\fillfromdata` |
| `tab:contract-drafting-metadata` | Contract-drafting metadata | Drafter model, temperature, prompt version, visible/hidden inputs, human lock rule, source hierarchy | Metadata values for model/temperature/prompt are `\fillfromdata`; visible/hidden rules explicit |
| `tab:update` | Maintenance micro-update | Proposed, selected, executed, checked, counted, `UNRESOLVE`, top reason | Proposed/selected/executed explicit; checked/counted/UNRESOLVE/top reason are `\fillfromdata` |

## Figure Coverage

| Label | Paper object | Required data | Mapping status |
|---|---|---|---|
| `fig:hero` | Main reporting figures | Panel (a): Coverage, Width, CountedScore for four main domains. Panel (b): pairwise matrix for four main-domain rows only | Plot macros are draft layout fallbacks and must not be used as results |
| `fig:evidence-counting` | Evidence-supported counting process | Record -> episode -> trace/artifacts -> evidence decision -> counted or `UNRESOLVE` | Static process figure; validator must check consistency with denominator/counting rules |
| `fig:case-cards` | Qualitative case cards | Representative tau3/AppWorld records with task, claim, evidence, missing piece, decision, effect on report | P3 qualitative artifact; examples cannot substitute for formal statistics |

## Explicit Study Quantities

Main study quantities stated by the paper:

- Main domains: AgentDojo, AppWorld, WebArena-Verified, tau3-bench retail.
- Main case units: 100 per main domain, 400 total.
- Main agents: Agent A, Agent B, Agent C.
- Main completed-record slots: 300 per main domain, 1200 total.
- Main stored episodes: AgentDojo 600, each other main domain 300, 1500 total.
- AgentDojo has benign and injected paired arms, producing two episodes per record.
- If an official split has fewer than 100 eligible verified cases, use all eligible cases and record the exception before main scoring.

Values deliberately not supplied by the paper:

- Concrete model identifiers for Agent A-C are configured from the provided OpenRouter mapping; exact version pins remain `需要从 locked manifest 确认`.
- Seeds, deterministic hash salt, bootstrap seed, audit seed: `需要从 locked manifest 确认`.
- Contract-drafting model, temperature, prompt version: `需要从 locked manifest 确认`.
- Costs and trained annotator times: `需要从 scored manifest 填充`.
- Runtime and machine specs: `需要从 locked manifest 确认`.
- AndroidWorld, WorkArena, OSWorld-Verified appendix case counts: `需要从 locked manifest 确认`.

## Fill / Placeholder Inventory

TeX macro fallback groups:

- Main measurement totals: `\ADJTotal`, `\APPTotal`, `\WAVTotal`, `\TAUTotal`, `\ALLTotal` are explicit fallback totals: 300, 300, 300, 300, 1200.
- Main measurement values: domain/all `Success`, `Fail`, `Unresolve`, `Coverage`, `CountedScore`, `Lower`, `Upper`, `Width` are `\fillfromdata`.
- Case-resampling intervals: domain/all `LowerCI`, `UpperCI`, `WidthCI`, `CountedScoreCI`, `NativeInside` are `\fillfromdata`.
- Denominator audit: domain/all `Attempted`, `InfraExcluded`, `AgentCausedFail` are `\fillfromdata`; completed uses total macros.
- Contract-drafting metadata: `\ContractDrafterModel`, `\ContractDrafterTemperature`, `\ContractPromptVersion` are `\fillfromdata`.
- Prediction outcomes: `\PoneValue`, `\PoneOutcome`, `\PtwoValue`, `\PtwoOutcome`, `\PthreeValue`, `\PthreeOutcome`, `\PfourValue`, `\PfourOutcome` are `\fillfromdata`.
- Pairwise table cells: A-B/A-C/B-C fallback to `?`; non-identified pair counts and all-domain diagnostics are `\fillfromdata`.
- Pairwise table colors/text: fallback visualization styles only, not results.
- Top `UNRESOLVE` reasons: one macro per main domain, all `\fillfromdata`.
- Audit/rerun metrics: domain/all audit strata, agreement, countability kappa, taxonomy kappa, rerun agreement, rerun pattern are `\fillfromdata`.
- Hero figure plot macros: draft numeric percentages without percent sign; explicitly layout placeholders, not empirical data.

TeX row-file fallbacks:

- `outputs/latex/pairwise_margin_rows.tex`: required for `tab:pairwise-margins`; fallback row says `\textsc{fill from scored manifest}`.
- `outputs/latex/per_agent_rows.tex`: required for `tab:per-agent`; fallback rows contain `\fillfromdata`.
- `outputs/latex/cost_rows.tex`: required for `tab:cost`; fallback time cells contain `\fillfromdata`.
- `outputs/latex/update_rows.tex`: required for `tab:update`; fallback checked/counted/UNRESOLVE/top-reason cells contain `\fillfromdata`.

Final macro contract:

- `outputs/latex/results_macros.tex` must set `\resultdatatrue`.
- Final output must not retain `\fillfromdata`, fallback plot values, or placeholder row values.

## Evidence Contract Gate

The paper and plan require one locked contract per case unit before scoring. Required contract fields:

- `claim_text`
- `native_sources`
- `required_artifacts`
- `success_rule`
- `fail_rule`
- `unresolve_rule`
- `claim_scope`
- `minimality_rationale`
- `source_support`

Required provenance:

- drafter provider/model/version, prompt version/hash, temperature, max tokens, visible input hashes, hidden-input assertion, response metadata, cost if available.
- human reviewer IDs, review actions, source hierarchy application, unsupported-requirement handling, contract version, lock time, contract hash.

Source hierarchy:

1. official evaluator semantics
2. official task text / policy
3. schema constraints needed to interpret evaluator-visible state

Unsupported native-aligned requirements must be removed or labeled `stronger_measurement` and excluded from the native-aligned main envelope.
