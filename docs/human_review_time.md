# Human Review Time

## Contract Review And Lock

Human adapter authors review contract drafts before scoring. The review record must show:

```text
review_started_at
review_finished_at
duration_minutes
reviewer_id
source_bundle_hash
visible_input_hash
review_actions
source hierarchy applied
unsupported requirements removed
requirements marked stronger_measurement
final lock decision
locked_at
locked_by
contract_version
contract_hash
manifest_hash
contract_drafting_llm_call_id
contract_draft_id
```

Required ordering:

```text
draft created_at <= review_started_at < review_finished_at <= locked_at < first_scoring_started_at
```

If lock time is missing or later than scoring, the record cannot enter formal scoring. If the locked contract cannot be linked back to the exact `contract_drafting_llm_call_id` and `contract_draft_id` that produced the reviewed draft, contract metadata validation fails and `tab:contract-drafting-metadata` is blocked.

## Review Input Restrictions

Human contract review uses official task/evaluator/policy/schema sources and the draft contract. The review log records `source_bundle_hash` and `visible_input_hash` for the exact materials shown to the reviewer. Contract reviewers must not use agent identity, agent trace, native_label, native_score, native evaluator pass/fail scalar, outcome label, prior outcome verdict, scored values, paper-output values, judge-only labels, alternate view verdicts, adapter/runner summary verdicts, or any other agent outcome to alter native-aligned contracts. After locking, any clarification creates a superseded/clarification contract version and sensitivity report mapping only.

## Human Audit Time

Blinded human audit records must capture:

- auditor id.
- assignment id.
- start/finish/duration.
- domain, stratum, record id.
- inputs shown to auditor.
- forbidden-input assertion.
- auditor label over counted-SUCCESS / counted-FAIL / UNRESOLVE.
- auditor R1-R7 taxonomy label when UNRESOLVE.
- disagreement notes.

Auditor inputs include task, trace, available evidence, and locked contract. They exclude agent identity, native_label, native_score, native evaluator pass/fail scalar, outcome label, prior outcome verdict, scored values, paper-output values, counting decision, UNRESOLVE reason, alternate view verdicts, judge-only labels, and adapter/runner summary verdicts.

## Review Logs And Release

Review logs are used for auditability and `tab:cost` human-time values. Public release may include reviewer ids only if they are approved for release; otherwise stable pseudonymous ids are used. The raw review timing and actions remain auditable in the gated package.
