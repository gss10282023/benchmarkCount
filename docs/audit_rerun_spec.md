# Audit And Rerun Specification

## Frozen Plans

Audit sampling plan, audit sample seed, rerun subset, rerun subset selection rule, bootstrap seed/resample count, pairwise_equality_tolerance, and P1-P4 threshold boundary behavior must be frozen before formal scoring. Until a formal value is set in the frozen stats plan, `pairwise_equality_tolerance` is `需要从 locked manifest 确认`; missing tolerance blocks aggregation and paper outputs.

Default boundary rule:

```text
supported: full 95% interval strictly lies on predicted side
falsified: full 95% interval strictly lies on opposite side
inconclusive: interval touches or crosses threshold
```

An inclusive threshold rule is allowed only if frozen before results are seen.

## Case-Cluster Bootstrap

Bootstrap resamples case units within domain with replacement and keeps all agent records attached to a resampled case unit. It does not resample records independently. Intervals are secondary descriptive views over a deterministic manifest; they condition on stored traces, fixed agent versions, and fixed environments. They do not include repeated-execution randomness, API drift, tool-call nondeterminism, or environment volatility.

## P1-P4 Outcomes

Prediction outcomes are `supported`, `falsified`, or `inconclusive`.

- P1: AppWorld and WebArena-Verified width intervals each strictly below 15% support; either lower bound strictly above 15% falsifies; interval touching 15% is inconclusive unless an inclusive rule was frozen.
- P2: AgentDojo width minus max(AppWorld, WebArena-Verified) contrast interval strictly above 20 percentage points supports; upper bound strictly below 20 pp falsifies; touching is inconclusive unless frozen otherwise.
- P3: tau3_retail width must be strictly above both negative controls and strictly below AgentDojo by contrast intervals; opposite-direction intervals falsify; overlap/touch is inconclusive.
- P4: fraction of non-identified pairs on AgentDojo or tau3_retail supports only when the lower interval bound satisfies the frozen 75% rule; upper bound below 75% falsifies. Exact zero-width equality is reported separately and is not evidence-induced non-identification.

## Pairwise Ranking

For agents i and j in domain d:

```text
i > j if LB_i,d > UB_j,d
j > i if LB_j,d > UB_i,d
? otherwise
= only if both evidence envelopes are exactly equal under frozen pairwise_equality_tolerance
```

`pairwise_equality_tolerance` must be frozen before scoring. If the paper does not specify it, the stats plan must choose a value before results are seen and freeze it. Ordinary interval overlap is `?`, not equality.

Pairwise margins are generated only for observed separated pairs. For `i > j`:

```text
M_i>j = LB_i,d - UB_j,d
```

An asterisk is added only when the observed envelope is separated and the lower 2.5th percentile of the case-cluster bootstrap distribution of `M_i>j` remains positive. It is descriptive, unadjusted, and post-selection, not a formal significance test.

## Rerun Subset

Rerun subset:

```text
Agent A
10 case units per main domain
40 total rerun case units
50 total rerun episodes because AgentDojo reruns paired arms
```

Rerun reports original counting decision agreement, envelope category agreement, exact Clopper-Pearson intervals, and changes in lower endpoint, upper endpoint, and width. Rerun is a stability check of evidence labels, not a performance confidence interval.

## Blinded Human Audit

Audit sample:

```text
100 main-study records
25 records per main domain
stratified stress sample with required within-domain buckets
```

Within each main domain, the audit sampler must form the required strata from the formal scored-record source set:

```text
counted records: evidence_label in SUCCESS | FAIL
UNRESOLVE records: evidence_label == UNRESOLVE
native/evidence disagreement records: native reporting and evidence reporting disagree
```

When all three buckets exist in a domain, all three must be represented in that domain's 25-record audit sample. If a bucket is empty, the audit sampling manifest must record `bucket_empty` with the source count and redistribute the remaining quota according to the frozen audit_sampling_plan. If a non-empty required bucket is omitted, audit validation fails and paper outputs depending on `tab:audit-rerun` are blocked. This is a stratified stress sample, not a simple random sample. Agreement and kappa are descriptive unless design weights are applied.

Auditors see task, trace, available evidence, and locked evidence contract. They do not see agent identity, native label, counting decision, UNRESOLVE reason, or alternate view verdicts.

The blinded audit forbidden-input list is: agent identity, native_label, native_score, native evaluator pass/fail scalar, outcome label, prior outcome verdict, scored values, paper-output values, counting decision, UNRESOLVE reason, alternate view verdicts, judge-only labels, and adapter/runner summary verdicts.

Metrics:

- auditor-vs-scorer agreement over counted-SUCCESS, counted-FAIL, UNRESOLVE.
- inter-rater kappa over counted vs UNRESOLVE.
- R1-R7 taxonomy kappa only where both auditors mark UNRESOLVE.

Release metadata includes item-level audit labels, stratum counts, and audit disagreement set.
