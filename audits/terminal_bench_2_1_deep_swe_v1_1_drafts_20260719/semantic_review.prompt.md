You are independently auditing one pre-run case checklist for Terminal-Bench 2.1
or DeepSWE v1.1.

Read only the supplied `case_packet.md`, `checklist.yaml`, and this prompt. The
packet contains the complete allowed review boundary. Do not use outside
knowledge, browse, or request any run. No concrete agent outcome, trajectory
contents, per-record evaluator result, released reward/label, or prior evidence
score is available or permitted.

Review every item below strictly. Return `accept` only when every item passes. If
any item fails, return `revise`, provide a blocking finding for every failed item,
and return a complete corrected `native` plus `stronger` body. Preserve the case
identity; do not add metadata fields to the revised body.

Review items, in the exact requested order:

1. `identity_and_scope`
   - The checklist is for exactly the packet's case, domain, and task.
   - It is a reusable pre-run evidence rule, not a verdict for a current record.
2. `native_user_goal`
   - `native.user_goal` faithfully states the official instruction/user intent.
   - It does not collapse the goal into a narrower test criterion.
3. `native_evaluator_semantics`
   - `native.benchmark_success`, `checked_by`, `success_if`, and `fail_if`
     reproduce the exact released evaluator/oracle semantics in the packet.
   - Native rules do not silently strengthen the released criterion with prose
     requirements that the evaluator does not operationalize.
   - For DeepSWE v1.1, verify the exact configured fail-to-pass/pass-to-pass
     aggregation, including non-empty fail-to-pass, missing/skipped behavior, and
     duplicate-node worst-status semantics.
   - For Terminal-Bench 2.1, use the exact task-specific verifier/tests rather than
     a benchmark-wide generic predicate.
4. `decisive_post_run_evidence`
   - Every named decisive artifact is a type in the packet's Available Artifact
     Inventory and can independently establish the stated fact.
   - A final reward/result/label record is comparison-only metadata. Never accept
     `result.json`, `verifier/reward.txt`, `verifier/reward.json`, `native_label`,
     `native_score`, or equivalent final success/fail/reward fields as decisive
     artifacts or decision shortcuts.
   - Raw retained traces, logs, CTRF/test reports, patches, and state artifacts may
     be used only for facts their contents actually expose.
5. `decision_rules_sfu`
   - S requires retained non-label evidence establishing native success.
   - F requires retained non-label evidence establishing native failure.
   - U applies only when neither claim can be established. Ordinary
     benchmark-counted failures are not moved to U when evidence establishes them.
6. `source_support_pointers`
   - Every claim has concrete packet-local source support, all pointers resolve to
     the packet or its exact Source Inventory, and evaluator rules are supported by
     evaluator/oracle sources rather than reviewer intuition.
7. `stronger_conditions`
   - Each condition is a concrete, case-specific requirement explicitly supported
     by the official task, user intent, or policy and not operationalized by the
     released native evaluator/oracle.
   - The condition or rationale states that exact measurement gap, and the named
     retained artifacts could assess it in principle. Lack of evidence for a future
     record may yield stronger U; it does not justify deleting an otherwise valid
     condition.
   - Evaluator/oracle code may demonstrate noncoverage but cannot invent a stronger
     requirement absent official task/user/policy support. Exclude stylistic,
     generic-quality, speculative, hidden-state, counterfactual, extra-judge, and
     reviewer-preference conditions.
   - For DeepSWE, explicitly review the instruction to work on a new branch and
     commit everything. Keep the source-supported portion outside the configured
     test-node aggregation as stronger measurement; do not silently add it to
     native success.
8. `minimality_and_no_run_leakage`
   - The checklist is compact and contains no concrete outcome, released label,
     trial/job detail, answer-key action sequence, subjective extra requirement, or
     source material treated as proof that a run succeeded.
9. `stronger_conflict_separation`
   - Stronger results are independent. The checklist never says stronger failure is
     a benchmark error/conflict and never derives conflict from native S plus
     stronger F. Benchmark conflict is outside checklist drafting and requires a
     later record-level review of retained artifacts and source pointers.

Use the output schema exactly. Evidence in each review item/finding should cite
short locations such as `checklist.yaml::native.success_if[0]` and
`case_packet.md::Native Evaluator Semantics`, or exact packet source pointers.
Output JSON only.
