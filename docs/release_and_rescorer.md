# Release And Rescorer Specification

## Release Scope

The release package must let a reader trace every reported envelope, table value, figure value, appendix metric, and final report statistic back to:

- manifest entry.
- case unit.
- agent config and locked manifest metadata.
- locked evidence contract.
- scorer/rescorer version.
- raw artifact paths and hashes.
- LLM call logs where applicable.
- human-time or human-review logs where applicable.
- denominator audit and failure records where applicable.

Every reported envelope binds the version tuple:

```text
(rescorer version, manifest version, contract version, taxonomy version)
```

The release also records evidence-contract template version, contract-drafting prompt version, scorer version, result schema version, artifact schema version, bootstrap plan version, audit sampling plan version, rerun subset version, and paper mapping hash.

## Public / Gated / Not Released

Release classification:

- `public`: per-case manifests with task ids, locked claim, evidence contract, claim-scope label, UNRESOLVE taxonomy code, envelope contributions, rescorer source/tests, template/prompt versions, per-domain summaries, robust-ranking matrices, denominator audits, audit instructions, item-level audit labels, stratum counts, and audit disagreement set.
- `access_controlled`: traces or fragments containing prompt-injection content, placeholder credentials, API-like tokens, synthetic personal data, sensitive browser/workspace state, or gated benchmark assets after scrubbing and sandbox re-pinning.
- `not_released`: live-account credentials, real third-party API keys, SSH private keys, private service credentials, and artifacts enabling non-sandbox side effects.

UNRESOLVE records remain visible even when full traces are gated through case identifier, locked claim, evidence contract, taxonomy code, and envelope contribution.

## Rescorer Interface

The public rescorer maps the paper's formal definitions:

```text
trajectory
evidence function
oracle / locked contract
countable rule
envelope aggregation
```

Inputs:

- scored manifest or raw manifest plus locked contracts.
- artifact manifest paths and hashes.
- result schema and artifact schema versions.
- taxonomy version.
- scorer/rescorer version.

Outputs:

- completed scored records.
- denominator audit references.
- aggregate metrics.
- UNRESOLVE reason records.
- paper-output source mapping.

The rescorer must fail closed on missing locked contracts, hash mismatch, missing official provenance for decisive native evaluator artifacts, non-canonical domain ids, forbidden summary-scalar evidence, missing stronger_measurement mapping, or use of post-lock clarification contracts in native-aligned main results.

## Post-Lock Clarification

Locked contracts cannot be changed based on outcomes. Any clarification creates a superseded/clarification contract version containing:

```text
clarification_reason
clarification_requested_at
clarification_locked_at
supersedes_contract_id/version/hash
main_result_eligible: false
sensitivity_report_id
```

Clarified contracts feed sensitivity reports only. They do not enter native-aligned main result, main tables, main figures, or headline report values.

## Paper Output Details

Paper-output system must enforce:

- `tab:views` reports evidence envelope, counted-only, native benchmark, optimistic, and pessimistic views with shared provenance.
- native-score-inside-envelope appears in `tab:main-results-B` and is backed by validated metrics.
- `fig:hero` panel (b) includes only the four P0 main domains: `agentdojo`, `appworld`, `webarena_verified`, `tau3_retail`.
- `fig:case-cards` has case-level provenance and source artifact ids, not hand-authored examples without artifacts.
- `app:update` exact funnel: 6 raw proposals/domain, 3 selected/domain, 24 proposed, 12 selected, 15 executed because AgentDojo is paired.
- matched-budget controls use the same proposal/selection budget and report countable updates plus envelope-width reduction.
- judge-only metrics are diagnostic and include success/fail/inconclusive, disagreement rates, and assignments on evidence-UNRESOLVE records.
- final report cost, latency, and failure statistics have provenance and are not estimated or backfilled.
- `tab:cost` comes only from human-time logs.
- stronger_measurement sidecar data never enters native-aligned main envelope.

Any required paper label missing from `experiments/paper_mapping.md`, mapped to fallback/manual empirical values, mapped to smoke/dry_run/mock outputs, or mapped to undeclared non-formal appendix/diagnostic data blocks paper generation unless the paper text and manifest are updated together.

## Macro Contract

Final paper build must set `\resultdatatrue`. It must not retain `\fillfromdata`, row-file fallback text, figure layout values used as empirical data, or manually entered paper cells. Missing empirical data blocks paper outputs unless the paper and manifest are updated.
